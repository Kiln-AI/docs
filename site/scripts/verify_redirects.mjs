#!/usr/bin/env node
/**
 * Prove that every URL in `redirects.csv` still resolves.
 *
 * Every `old_path` and every distinct `new_path` must end at a real page:
 * checking the targets as well as the sources is what catches a redirect
 * pointing at nothing.
 *
 *   node scripts/verify_redirects.mjs --dist dist
 *       Offline. Rules come from `dist/_redirects`, and the destination is
 *       checked against the built files. No server needed.
 *
 *   node scripts/verify_redirects.mjs --base-url https://x.pages.dev
 *       Over HTTP, with the *server* doing the redirecting. This is the real
 *       gate, run against a Cloudflare preview and later production.
 *
 *   node scripts/verify_redirects.mjs --base-url http://localhost:4321 --dist dist
 *       Over HTTP against a server that does not implement `_redirects` — i.e.
 *       `astro preview`. Rules are applied locally first and only the resolved
 *       destination is fetched.
 */

import { readFile, stat } from 'node:fs/promises';
import { argv, exit } from 'node:process';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const SITE_DIR = path.resolve(SCRIPT_DIR, '..');

const PERMANENT_STATUSES = new Set([301, 308]);
const TEMPORARY_STATUSES = new Set([302, 303, 307]);
const MAX_HOPS = 5;
const DEFAULT_CONCURRENCY = 6;

export class VerifyError extends Error {}

// --------------------------------------------------------------------------
// Inventory
// --------------------------------------------------------------------------

const CSV_HEADER = 'old_path,new_path,status,source';

/** Paths to check: every source and every distinct destination, deduped. */
export function parseInventory(csvText) {
  const lines = csvText
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith('#'));

  if (lines.shift() !== CSV_HEADER) {
    throw new VerifyError(`redirects.csv header must be ${CSV_HEADER}`);
  }

  const checks = new Map();
  for (const [index, line] of lines.entries()) {
    const fields = line.split(',').map((field) => field.trim());
    if (fields.length !== 4) {
      throw new VerifyError(`redirects.csv line ${index + 2}: expected 4 columns`);
    }
    const [oldPath, newPath, , source] = fields;
    // `expect` is what this path must actually end up at. Without it a source
    // path passes merely by resolving to *something* that exists — and 45 of
    // ours resolve to `x/index.html` whether or not their rule is present, so
    // deleting a rule would go unnoticed.
    if (!checks.has(oldPath)) {
      checks.set(oldPath, { source, expect: oldPath === newPath ? null : newPath });
    }
    if (!checks.has(newPath)) checks.set(newPath, { source: 'target', expect: null });
  }
  return [...checks].map(([urlPath, check]) => ({ path: urlPath, ...check }));
}

// --------------------------------------------------------------------------
// Local rule resolution
// --------------------------------------------------------------------------

/** Parse a Cloudflare Pages `_redirects` file into exact-match rules. */
export function parseRules(text) {
  const rules = new Map();
  for (const raw of text.split('\n')) {
    const line = raw.split('#')[0].trim();
    if (!line) continue;

    const [from, to, statusText] = line.split(/\s+/);
    if (!from || !to) {
      throw new VerifyError(`malformed redirect rule: ${raw.trim()}`);
    }
    // We emit only exact paths. A splat or placeholder appearing later should
    // stop this tool rather than let it quietly report a miss as a pass.
    if (/[*:]/.test(from)) {
      throw new VerifyError(
        `rule ${from} uses wildcard matching, which this verifier does not implement`,
      );
    }
    // Cloudflare defaults to 302 when a rule omits the status.
    rules.set(from, { to, status: statusText ? Number(statusText) : 302 });
  }
  return rules;
}

/** Follow local rules to the path that should actually be served. */
export function resolvePath(startPath, rules) {
  const hops = [];
  let current = startPath;
  const seen = new Set([current]);

  while (rules.has(current)) {
    const { to, status } = rules.get(current);
    hops.push({ from: current, to, status });
    if (seen.has(to)) {
      throw new VerifyError(`redirect loop: ${[...seen, to].join(' -> ')}`);
    }
    if (hops.length > MAX_HOPS) {
      throw new VerifyError(`more than ${MAX_HOPS} redirect hops from ${startPath}`);
    }
    seen.add(to);
    current = to;
  }
  return { path: current, hops };
}

// --------------------------------------------------------------------------
// Oracles
// --------------------------------------------------------------------------

function distCandidates(urlPath) {
  const relative = urlPath.replace(/^\//, '');
  if (urlPath.endsWith('/')) return [`${relative}index.html`];
  return [`${relative}/index.html`, `${relative}.html`, relative];
}

// A directory is not a served file. `dist/docs/` exists as a directory but
// nothing is served at `/docs`, so testing for mere existence would pass a
// path that 404s in production.
async function servedFileExists(distDir, urlPath) {
  for (const candidate of distCandidates(urlPath)) {
    try {
      if ((await stat(path.join(distDir, candidate))).isFile()) return true;
    } catch {
      /* try the next spelling */
    }
  }
  return false;
}

/** Walk the server's own redirects to a final status. */
async function fetchChain(baseUrl, urlPath, fetchImpl) {
  const hops = [];
  let current = urlPath;

  for (let hop = 0; hop <= MAX_HOPS; hop += 1) {
    const response = await fetchImpl(new URL(current, baseUrl), { redirect: 'manual' });
    if (response.status < 300 || response.status >= 400) {
      return { status: response.status, hops };
    }
    const location = response.headers.get('location');
    if (!location) {
      throw new VerifyError(`${current} returned ${response.status} with no Location`);
    }
    const next = new URL(location, new URL(current, baseUrl));
    hops.push({ from: current, to: next.pathname, status: response.status });
    current = next.pathname + next.search;
  }
  throw new VerifyError(`more than ${MAX_HOPS} redirect hops from ${urlPath}`);
}

// --------------------------------------------------------------------------
// Checking
// --------------------------------------------------------------------------

export function describeFailure({ hops, status }, { allowTemporary }) {
  const temporary = hops.filter(
    (hop) => !PERMANENT_STATUSES.has(hop.status) && TEMPORARY_STATUSES.has(hop.status),
  );
  if (temporary.length && !allowTemporary) {
    const shown = temporary.map((hop) => `${hop.from} -> ${hop.to} (${hop.status})`);
    return `temporary redirect, expected 301: ${shown.join(', ')}`;
  }
  const unexpected = hops.find(
    (hop) => !PERMANENT_STATUSES.has(hop.status) && !TEMPORARY_STATUSES.has(hop.status),
  );
  if (unexpected) {
    return `unexpected redirect status ${unexpected.status} on ${unexpected.from}`;
  }
  if (status !== undefined && status !== 200) {
    return `final response was ${status}`;
  }
  return null;
}

async function checkOne(check, options) {
  const { rules, distDir, baseUrl, allowTemporary, fetchImpl } = options;

  let start = check.path;
  let hops = [];
  if (rules) {
    const resolved = resolvePath(check.path, rules);
    start = resolved.path;
    hops = resolved.hops;
  }

  if (baseUrl) {
    const result = await fetchChain(baseUrl, start, fetchImpl);
    const allHops = [...hops, ...result.hops];
    const landedOn = allHops.length ? allHops[allHops.length - 1].to : start;
    const failure = describeFailure(
      { hops: allHops, status: result.status },
      { allowTemporary },
    ) ?? wrongDestination(check, landedOn);
    return { ...check, resolvedTo: landedOn, hops: allHops, failure };
  }

  const failure = describeFailure({ hops }, { allowTemporary })
    ?? wrongDestination(check, start)
    ?? ((await servedFileExists(distDir, start))
      ? null
      : `no file in ${describeDir(distDir)} for ${start}`);
  return { ...check, resolvedTo: start, hops, failure };
}

function wrongDestination(check, landedOn) {
  if (!check.expect || landedOn === check.expect) return null;
  return landedOn === check.path
    ? `nothing redirects it; redirects.csv says it should reach ${check.expect}`
    : `reached ${landedOn}, but redirects.csv says ${check.expect}`;
}

function describeDir(directory) {
  const relative = path.relative(SITE_DIR, directory);
  return relative && !relative.startsWith('..') ? relative : directory;
}

async function mapWithConcurrency(items, limit, worker) {
  const results = new Array(items.length);
  let next = 0;
  let completed = 0;

  const runners = Array.from({ length: Math.min(limit, items.length) }, async () => {
    while (next < items.length) {
      const index = next;
      next += 1;
      results[index] = await worker(items[index]);
      completed += 1;
    }
  });
  await Promise.all(runners);

  // Counting completions rather than inspecting `results`: a sparse array's
  // holes are skipped by every array method, `filter` included, so a run that
  // spawned no runners at all would otherwise look like a run with no
  // failures. This is the property, not a guard against one bad flag value.
  if (completed !== items.length) {
    throw new VerifyError(
      `only ${completed} of ${items.length} paths were checked - `
      + `the run did not complete, so its result means nothing`,
    );
  }
  return results;
}

export async function verify(options) {
  const csvText = await readFile(options.csvPath, 'utf8');
  const checks = parseInventory(csvText);

  // Phase 8 runs this against production as the last gate before DNS cutover.
  // An inventory that has been truncated to nothing would otherwise sail
  // through as "all paths resolve".
  const floor = options.minPaths ?? 1;
  if (!Number.isInteger(floor) || floor < 1) {
    throw new VerifyError(`--min-paths must be a positive integer, got ${options.minPaths}`);
  }
  if (checks.length < floor) {
    throw new VerifyError(
      `only ${checks.length} paths to check, expected at least ${floor} - `
      + `is ${path.basename(options.csvPath)} truncated? If instead the inventory `
      + `legitimately shrank - the alias probe disproved a row, say - lower the floor `
      + `in the verify:redirects script in package.json to ${checks.length} and commit `
      + `that with the inventory change. Passing --min-paths on the command line to get `
      + `a green run leaves the floor wrong for everyone else.`,
    );
  }

  const rules = options.distDir
    ? parseRules(await readFile(path.join(options.distDir, '_redirects'), 'utf8'))
    : null;

  const results = await mapWithConcurrency(
    checks,
    options.concurrency ?? DEFAULT_CONCURRENCY,
    (check) => checkOne(check, { ...options, rules, fetchImpl: options.fetchImpl ?? fetch }),
  );

  return {
    results,
    failures: results.filter((result) => result.failure),
    locallyResolved: results.filter((result) => result.hops.length && rules).length,
  };
}

// --------------------------------------------------------------------------
// CLI
// --------------------------------------------------------------------------

export function parseArgs(args) {
  const options = {
    csvPath: path.join(SITE_DIR, 'redirects.csv'),
    distDir: null,
    baseUrl: null,
    allowTemporary: false,
    concurrency: DEFAULT_CONCURRENCY,
    minPaths: 1,
  };

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    const value = () => {
      const next = args[index + 1];
      if (next === undefined) throw new VerifyError(`${arg} needs a value`);
      index += 1;
      return next;
    };
    // Numeric flags are validated for the same reason unknown flags throw: a
    // mistyped one must stop the run, never quietly weaken what it checks.
    const count = () => {
      const raw = value();
      const parsed = Number(raw);
      if (!Number.isInteger(parsed) || parsed < 1) {
        throw new VerifyError(`${arg} must be a positive integer, got ${raw}`);
      }
      return parsed;
    };
    switch (arg) {
      case '--dist': options.distDir = path.resolve(value()); break;
      case '--base-url': options.baseUrl = value(); break;
      case '--csv': options.csvPath = path.resolve(value()); break;
      case '--concurrency': options.concurrency = count(); break;
      case '--min-paths': options.minPaths = count(); break;
      case '--allow-temporary': options.allowTemporary = true; break;
      default: throw new VerifyError(`unknown argument: ${arg}`);
    }
  }

  if (!options.distDir && !options.baseUrl) {
    throw new VerifyError('pass --dist DIR, --base-url URL, or both');
  }
  return options;
}

async function main(args) {
  let options;
  try {
    options = parseArgs(args);
  } catch (error) {
    console.error(`error: ${error.message}`);
    return 2;
  }

  let report;
  try {
    report = await verify(options);
  } catch (error) {
    console.error(`error: ${error.message}`);
    return 2;
  }

  const mode = options.baseUrl
    ? `${options.baseUrl}${options.distDir ? ' (rules applied locally)' : ' (server-side redirects)'}`
    : `${options.distDir} (offline)`;
  console.log(`checked ${report.results.length} paths against ${mode}`);
  if (options.distDir) {
    console.log(`  ${report.locallyResolved} resolved through local _redirects rules`);
  }

  if (report.failures.length === 0) {
    console.log('all paths resolve');
    return 0;
  }

  console.error(`\n${report.failures.length} failing paths:`);
  for (const failure of report.failures) {
    console.error(`  ${failure.path} [${failure.source}] - ${failure.failure}`);
  }
  return 1;
}

if (import.meta.url === pathToFileURL(argv[1] ?? '').href) {
  exit(await main(argv.slice(2)));
}
