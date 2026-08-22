/**
 * Tests for the redirect verifier.
 *
 * Run from `site/`:
 *
 *     npm test
 *     node --test "scripts/*.test.mjs"
 */

import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';

import {
  VerifyError,
  parseInventory,
  parseRules,
  resolvePath,
  describeFailure,
  parseArgs,
  verify,
} from './verify_redirects.mjs';

const HEADER = 'old_path,new_path,status,source\n';

function response(status, location) {
  return {
    status,
    headers: { get: (name) => (name.toLowerCase() === 'location' ? location ?? null : null) },
  };
}

/** A server described as a path -> response map, as `verify` would call it. */
function fakeServer(routes) {
  return async (url) => routes[url.pathname] ?? response(404);
}

async function scratch(files) {
  const root = await mkdtemp(path.join(tmpdir(), 'verify-redirects-'));
  for (const [relative, contents] of Object.entries(files)) {
    const target = path.join(root, relative);
    await mkdir(path.dirname(target), { recursive: true });
    await writeFile(target, contents, 'utf8');
  }
  return root;
}

// --------------------------------------------------------------------------

test('parseInventory checks both sources and targets', () => {
  const checks = parseInventory(`${HEADER}/a,/a/,301,sitemap\n`);
  assert.deepEqual(checks, [
    { path: '/a', source: 'sitemap', expect: '/a/' },
    { path: '/a/', source: 'target', expect: null },
  ]);
});

test('parseInventory dedupes a target that is also a source', () => {
  const checks = parseInventory(`${HEADER}/a,/b,301,gsc\n/b,/b/,301,sitemap\n`);
  assert.deepEqual(checks.map((check) => check.path), ['/a', '/b', '/b/']);
});

test('parseInventory keeps the first source seen for a path', () => {
  const checks = parseInventory(`${HEADER}/a,/b/,301,sitemap\n/a,/b/,301,manual\n`);
  assert.equal(checks.find((check) => check.path === '/a').source, 'sitemap');
});

test('parseInventory expects no destination for a self-redirect', () => {
  const checks = parseInventory(`${HEADER}/,/,301,sitemap\n`);
  assert.deepEqual(checks, [{ path: '/', source: 'sitemap', expect: null }]);
});

test('parseInventory rejects a wrong header', () => {
  assert.throws(() => parseInventory('from,to\n'), VerifyError);
});

test('parseInventory rejects a short row', () => {
  assert.throws(() => parseInventory(`${HEADER}/a,/a/,301\n`), /line 2/);
});

test('parseInventory ignores comments and blank lines', () => {
  assert.equal(parseInventory(`${HEADER}# note\n\n/a,/a/,301,sitemap\n`).length, 2);
});

// --------------------------------------------------------------------------

test('parseRules reads a rule with an explicit status', () => {
  assert.deepEqual(parseRules('/a /a/ 301\n').get('/a'), { to: '/a/', status: 301 });
});

test('parseRules defaults a status-less rule to 302, as Cloudflare does', () => {
  assert.equal(parseRules('/a /a/\n').get('/a').status, 302);
});

test('parseRules ignores comments and blank lines', () => {
  const rules = parseRules('# header\n\n/a /a/ 301  # trailing\n');
  assert.equal(rules.size, 1);
  assert.equal(rules.get('/a').to, '/a/');
});

test('parseRules refuses wildcard rules rather than mis-reporting them', () => {
  assert.throws(() => parseRules('/docs/* /docs/:splat/ 301\n'), /wildcard/);
});

test('parseRules rejects a rule with no destination', () => {
  assert.throws(() => parseRules('/a\n'), /malformed/);
});

// --------------------------------------------------------------------------

test('resolvePath returns the path unchanged when no rule matches', () => {
  const resolved = resolvePath('/a/', parseRules('/b /b/ 301\n'));
  assert.deepEqual(resolved, { path: '/a/', hops: [] });
});

test('resolvePath follows a single hop', () => {
  const resolved = resolvePath('/a', parseRules('/a /a/ 301\n'));
  assert.equal(resolved.path, '/a/');
  assert.deepEqual(resolved.hops, [{ from: '/a', to: '/a/', status: 301 }]);
});

test('resolvePath follows a chain to its end', () => {
  const resolved = resolvePath('/a', parseRules('/a /b 301\n/b /c/ 301\n'));
  assert.equal(resolved.path, '/c/');
  assert.equal(resolved.hops.length, 2);
});

test('resolvePath raises on a loop', () => {
  assert.throws(() => resolvePath('/a', parseRules('/a /b 301\n/b /a 301\n')), /loop/);
});

// --------------------------------------------------------------------------

test('describeFailure passes a plain 200', () => {
  assert.equal(describeFailure({ hops: [], status: 200 }, {}), null);
});

test('describeFailure passes a 301 that lands on a 200', () => {
  const outcome = { hops: [{ from: '/a', to: '/a/', status: 301 }], status: 200 };
  assert.equal(describeFailure(outcome, {}), null);
});

test('describeFailure passes a 308, which is what Cloudflare normalises with', () => {
  const outcome = { hops: [{ from: '/a', to: '/a/', status: 308 }], status: 200 };
  assert.equal(describeFailure(outcome, {}), null);
});

test('describeFailure rejects a temporary redirect by default', () => {
  const outcome = { hops: [{ from: '/a', to: '/a/', status: 302 }], status: 200 };
  assert.match(describeFailure(outcome, {}), /temporary redirect/);
});

test('describeFailure accepts a temporary redirect with --allow-temporary', () => {
  const outcome = { hops: [{ from: '/a', to: '/a/', status: 302 }], status: 200 };
  assert.equal(describeFailure(outcome, { allowTemporary: true }), null);
});

test('describeFailure reports a non-200 final response', () => {
  assert.match(describeFailure({ hops: [], status: 404 }, {}), /final response was 404/);
});

test('describeFailure reports an unexpected 3xx status', () => {
  const outcome = { hops: [{ from: '/a', to: '/a/', status: 305 }], status: 200 };
  assert.match(describeFailure(outcome, {}), /unexpected redirect status 305/);
});

// --------------------------------------------------------------------------

test('parseArgs requires an oracle', () => {
  assert.throws(() => parseArgs([]), /--dist DIR, --base-url URL, or both/);
});

test('parseArgs reads both oracles and the flags', () => {
  const options = parseArgs(['--base-url', 'http://x', '--dist', 'dist', '--allow-temporary']);
  assert.equal(options.baseUrl, 'http://x');
  assert.equal(options.distDir, path.resolve('dist'));
  assert.equal(options.allowTemporary, true);
});

test('parseArgs reads --min-paths', () => {
  assert.equal(parseArgs(['--dist', 'dist', '--min-paths', '120']).minPaths, 120);
});

test('parseArgs rejects a zero concurrency, which would spawn no runners', () => {
  assert.throws(() => parseArgs(['--dist', 'dist', '--concurrency', '0']), /positive integer/);
});

test('parseArgs rejects a non-numeric concurrency', () => {
  assert.throws(() => parseArgs(['--dist', 'dist', '--concurrency', 'abc']), /positive integer/);
});

test('parseArgs rejects a non-numeric --min-paths', () => {
  // The flag that raises the floor must not disable it when mistyped.
  assert.throws(() => parseArgs(['--dist', 'dist', '--min-paths', 'abc']), /positive integer/);
});

test('parseArgs rejects an unknown argument', () => {
  assert.throws(() => parseArgs(['--nope']), /unknown argument/);
});

test('parseArgs rejects a flag with no value', () => {
  assert.throws(() => parseArgs(['--dist']), /needs a value/);
});

// --------------------------------------------------------------------------

test('verify passes offline when the built files exist', async () => {
  const root = await scratch({
    'redirects.csv': `${HEADER}/a,/a/,301,sitemap\n`,
    'dist/_redirects': '/a /a/ 301\n',
    'dist/a/index.html': '<html></html>',
  });
  const report = await verify({
    csvPath: path.join(root, 'redirects.csv'),
    distDir: path.join(root, 'dist'),
  });
  assert.deepEqual(report.failures, []);
  assert.equal(report.locallyResolved, 1);
});

test('verify refuses to pass a directory off as a served file', async () => {
  // `dist/docs/` exists as a directory but nothing is served at `/docs`.
  // Accepting it would let a dropped rule sail through CI while production 404s.
  const root = await scratch({
    'redirects.csv': `${HEADER}/docs,/docs/quickstart/,301,structural\n`,
    'dist/_redirects': '# every rule dropped\n',
    'dist/docs/quickstart/index.html': '<html></html>',
  });
  const report = await verify({
    csvPath: path.join(root, 'redirects.csv'),
    distDir: path.join(root, 'dist'),
  });
  assert.equal(report.failures.length, 1);
  assert.equal(report.failures[0].path, '/docs');
});

test('verify refuses to report a run that checked nothing', async () => {
  // The structural property, reached by bypassing parseArgs: a sparse results
  // array has holes, and `filter` skips holes, so an incomplete run would
  // otherwise look exactly like a run with no failures.
  const root = await scratch({
    'redirects.csv': `${HEADER}/a,/a/,301,sitemap\n`,
    'dist/_redirects': '/a /a/ 301\n',
    'dist/a/index.html': '<html></html>',
  });
  const options = { csvPath: path.join(root, 'redirects.csv'), distDir: path.join(root, 'dist') };
  for (const concurrency of [0, NaN]) {
    await assert.rejects(verify({ ...options, concurrency }), /did not complete/);
  }
});

test('verify refuses a --min-paths floor that is not a number', async () => {
  const root = await scratch({
    'redirects.csv': `${HEADER}/a,/a/,301,sitemap\n`,
    'dist/_redirects': '/a /a/ 301\n',
    'dist/a/index.html': '<html></html>',
  });
  await assert.rejects(
    verify({
      csvPath: path.join(root, 'redirects.csv'),
      distDir: path.join(root, 'dist'),
      minPaths: NaN,
    }),
    /--min-paths must be a positive integer/,
  );
});

test('verify catches a missing rule even where the destination file exists', async () => {
  // `/a` resolves to `a/index.html` with or without its rule, so testing only
  // that something exists would prove nothing about the 45 rules of this shape.
  const root = await scratch({
    'redirects.csv': `${HEADER}/a,/a/,301,sitemap\n`,
    'dist/_redirects': '# rule dropped\n',
    'dist/a/index.html': '<html></html>',
  });
  const report = await verify({
    csvPath: path.join(root, 'redirects.csv'),
    distDir: path.join(root, 'dist'),
  });
  assert.equal(report.failures.length, 1);
  assert.match(report.failures[0].failure, /nothing redirects it/);
});

test('verify catches a rule that lands on the wrong page', async () => {
  const root = await scratch({
    'redirects.csv': `${HEADER}/a,/a/,301,sitemap\n`,
    'dist/_redirects': '/a /elsewhere/ 301\n',
    'dist/a/index.html': '<html></html>',
    'dist/elsewhere/index.html': '<html></html>',
  });
  const report = await verify({
    csvPath: path.join(root, 'redirects.csv'),
    distDir: path.join(root, 'dist'),
  });
  assert.equal(report.failures.length, 1);
  assert.match(report.failures[0].failure, /reached \/elsewhere\/, but redirects.csv says \/a\//);
});

test('verify holds a server to the destination redirects.csv names', async () => {
  const root = await scratch({ 'redirects.csv': `${HEADER}/a,/a/,301,sitemap\n` });
  const report = await verify({
    csvPath: path.join(root, 'redirects.csv'),
    baseUrl: 'http://localhost:9999',
    fetchImpl: fakeServer({
      '/a': response(301, '/elsewhere/'),
      '/elsewhere/': response(200),
      '/a/': response(200),
    }),
  });
  assert.equal(report.failures.length, 1);
  assert.match(report.failures[0].failure, /reached \/elsewhere\//);
});

test('verify refuses an inventory with nothing in it', async () => {
  const root = await scratch({ 'redirects.csv': `${HEADER}# everything gone\n` });
  await assert.rejects(
    verify({ csvPath: path.join(root, 'redirects.csv'), distDir: path.join(root, 'dist') }),
    /expected at least 1/,
  );
});

test('verify enforces an explicit --min-paths floor', async () => {
  const root = await scratch({
    'redirects.csv': `${HEADER}/a,/a/,301,sitemap\n`,
    'dist/_redirects': '/a /a/ 301\n',
    'dist/a/index.html': '<html></html>',
  });
  const options = { csvPath: path.join(root, 'redirects.csv'), distDir: path.join(root, 'dist') };
  assert.deepEqual((await verify({ ...options, minPaths: 2 })).failures, []);
  await assert.rejects(verify({ ...options, minPaths: 3 }), /only 2 paths to check/);
});

test('verify fails offline when a redirect target was never built', async () => {
  const root = await scratch({
    'redirects.csv': `${HEADER}/a,/ghost/,301,manual\n`,
    'dist/_redirects': '/a /ghost/ 301\n',
  });
  const report = await verify({
    csvPath: path.join(root, 'redirects.csv'),
    distDir: path.join(root, 'dist'),
  });
  assert.equal(report.failures.length, 2);
  assert.match(report.failures[0].failure, /no file in/);
});

test('verify holds a server to doing its own redirecting when --dist is absent', async () => {
  const root = await scratch({ 'redirects.csv': `${HEADER}/a,/a/,301,sitemap\n` });
  const report = await verify({
    csvPath: path.join(root, 'redirects.csv'),
    baseUrl: 'http://localhost:9999',
    fetchImpl: fakeServer({ '/a': response(301, '/a/'), '/a/': response(200) }),
  });
  assert.deepEqual(report.failures, []);
  assert.equal(report.locallyResolved, 0);
});

test('verify reports a server that 404s instead of redirecting', async () => {
  const root = await scratch({ 'redirects.csv': `${HEADER}/a,/a/,301,alias-generated\n` });
  const report = await verify({
    csvPath: path.join(root, 'redirects.csv'),
    baseUrl: 'http://localhost:9999',
    fetchImpl: fakeServer({ '/a/': response(200) }),
  });
  assert.equal(report.failures.length, 1);
  assert.equal(report.failures[0].path, '/a');
  assert.equal(report.failures[0].source, 'alias-generated');
});

test('verify applies local rules first when both oracles are given', async () => {
  const root = await scratch({
    'redirects.csv': `${HEADER}/a,/a/,301,sitemap\n`,
    'dist/_redirects': '/a /a/ 301\n',
  });
  const report = await verify({
    csvPath: path.join(root, 'redirects.csv'),
    distDir: path.join(root, 'dist'),
    baseUrl: 'http://localhost:9999',
    // Only the resolved destination is ever requested: `/a` is not served.
    fetchImpl: fakeServer({ '/a/': response(200) }),
  });
  assert.deepEqual(report.failures, []);
  assert.equal(report.locallyResolved, 1);
});

test('verify rejects a redirect with no Location header', async () => {
  const root = await scratch({ 'redirects.csv': `${HEADER}/a,/a/,301,sitemap\n` });
  await assert.rejects(
    verify({
      csvPath: path.join(root, 'redirects.csv'),
      baseUrl: 'http://localhost:9999',
      fetchImpl: fakeServer({ '/a': response(301), '/a/': response(200) }),
    }),
    /no Location/,
  );
});

test('verify gives up on a server redirect loop', async () => {
  const root = await scratch({ 'redirects.csv': `${HEADER}/a,/b/,301,manual\n` });
  await assert.rejects(
    verify({
      csvPath: path.join(root, 'redirects.csv'),
      baseUrl: 'http://localhost:9999',
      fetchImpl: fakeServer({ '/a': response(301, '/b/'), '/b/': response(301, '/a') }),
    }),
    /more than 5 redirect hops/,
  );
});
