/**
 * Tests for the page-QA sweep.
 *
 * The sweep is the substitute for a baseline that could not be captured, so
 * what these pin down is that each detector fires on the real defect shape and
 * stays quiet on the thing that looks like it. A checker that reports nothing
 * because it checks nothing would be indistinguishable from a clean site.
 *
 * Run from `site/`:
 *
 *     npm test
 *     node --test "scripts/*.test.mjs"
 */

import test from 'node:test';
import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { copyFile, mkdtemp, mkdir, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { promisify } from 'node:util';

import {
  QaError,
  emptyTableColumns,
  isAdvisory,
  isExternal,
  literalMarkupInText,
  pageFindings,
  parseArgs,
  residualGitbookMarkup,
} from './qa_pages.mjs';

const checks = (findings) => findings.map((finding) => finding.check);
const details = (findings) => findings.map((finding) => finding.detail);

// --------------------------------------------------------------------------
// residualGitbookMarkup
// --------------------------------------------------------------------------

test('the card-table widget is reported', () => {
  const source = '<table data-view="cards"><td data-card-cover></td></table>';
  assert.deepEqual(new Set(checks(residualGitbookMarkup(source))), new Set(['gitbook-card-table']));
});

test('a hidden column is reported', () => {
  assert.deepEqual(checks(residualGitbookMarkup('<th data-hidden></th>')), [
    'gitbook-hidden-column',
  ]);
});

test('data-full-width and data-search are reported', () => {
  assert.deepEqual(
    details(residualGitbookMarkup('<table data-full-width="true"></table>\n<table data-search="false"></table>')),
    ['data-full-width="true"', 'data-search="false"'],
  );
});

test('a private app.gitbook.com URL is reported', () => {
  const findings = residualGitbookMarkup('See our [library](https://app.gitbook.com/u/abc123).');
  assert.deepEqual(checks(findings), ['gitbook-private-url']);
  assert.deepEqual(details(findings), ['https://app.gitbook.com/u/abc123']);
});

test('a .gitbook/assets path is reported', () => {
  assert.deepEqual(checks(residualGitbookMarkup('![](../.gitbook/assets/x.png)')), [
    'gitbook-asset-path',
  ]);
});

test('a clean page produces no findings', () => {
  const source = [
    '---',
    'title: "Prompts"',
    '---',
    '',
    'A table with a real header:',
    '',
    '<table><thead><tr><th>Feature</th></tr></thead></table>',
    '',
    '![](../../assets/shot.png)',
  ].join('\n');
  assert.deepEqual(residualGitbookMarkup(source), []);
});

test('GitBook markup inside a fenced code block is an example, not a defect', () => {
  const source = ['Before it looked like this:', '', '```html', '<table data-view="cards"></table>', '```'].join('\n');
  assert.deepEqual(residualGitbookMarkup(source), []);
});

test('an unclosed fence swallows the rest of the page', () => {
  const source = ['```', '<th data-hidden></th>'].join('\n');
  assert.deepEqual(residualGitbookMarkup(source), []);
});

test('the same attribute twice is reported once', () => {
  const source = '<th data-hidden></th><th data-hidden></th>';
  assert.equal(residualGitbookMarkup(source).length, 1);
});

// --------------------------------------------------------------------------
// literalMarkupInText
// --------------------------------------------------------------------------

test('an HTML tag shown as text is reported', () => {
  const findings = literalMarkupInText('Step 3\n<figure style="max-width:375px">\nStep 4');
  assert.deepEqual(checks(findings), ['unrendered-html']);
});

test('a closing tag shown as text is reported', () => {
  assert.deepEqual(checks(literalMarkupInText('</figure>')), ['unrendered-html']);
});

test('an unrendered markdown image is reported', () => {
  // The raw-space destination: not an image as far as CommonMark is concerned,
  // so it renders as text with no error anywhere in the build.
  const findings = literalMarkupInText('![](../../assets/my shot.png)');
  assert.deepEqual(checks(findings), ['unrendered-image']);
});

test('an unrendered markdown link is reported', () => {
  const findings = literalMarkupInText(
    "5. Generate data using Kiln's [synthetic data gen](/docs/synthetic-data-generation/) tool.",
  );
  assert.deepEqual(checks(findings), ['unrendered-link']);
});

test('an image is not also reported as a link', () => {
  assert.deepEqual(checks(literalMarkupInText('![alt](/assets/x.png)')), ['unrendered-image']);
});

test('an unconverted GitBook directive is reported', () => {
  assert.deepEqual(checks(literalMarkupInText('{% embed url="https://vimeo.com/1" %}')), [
    'gitbook-directive',
  ]);
});

test('prose that merely names a tag is not reported', () => {
  // Code spans are stripped before this runs, so what is left is prose. A
  // detector that fires on ordinary sentences is a detector people switch off.
  assert.deepEqual(literalMarkupInText('Wrap screenshots in a figure element, not a div.'), []);
});

test('comparisons and arrows in prose are not reported', () => {
  assert.deepEqual(literalMarkupInText('Typically <50 documents, and a -> b > c.'), []);
});

test('bracketed prose that is not a link is not reported', () => {
  assert.deepEqual(literalMarkupInText('Step 6 [Optional] (see below) for details.'), []);
});

// --------------------------------------------------------------------------
// emptyTableColumns
// --------------------------------------------------------------------------

const cell = (text = '', media = false) => ({ text, media });

test('a column that is empty in every row is reported', () => {
  const rows = [
    [cell('Feature'), cell('Manual'), cell()],
    [cell('Effort'), cell('~15 min'), cell()],
  ];
  assert.deepEqual(emptyTableColumns(rows), [2]);
});

test('a column with an empty header but full cells is kept', () => {
  // The label column of every comparison table in this corpus. A header-only
  // check would delete them all.
  const rows = [
    [cell(), cell('Manual'), cell('Kiln Pro')],
    [cell('Effort'), cell('~15 min'), cell('~5 min')],
  ];
  assert.deepEqual(emptyTableColumns(rows), []);
});

test('a column holding only an image is kept', () => {
  const rows = [[cell(), cell('Title')], [cell('', true), cell('Fine Tuning')]];
  assert.deepEqual(emptyTableColumns(rows), []);
});

test('whitespace-only cells count as empty', () => {
  assert.deepEqual(emptyTableColumns([[cell('A'), cell('  \n ')]]), [1]);
});

test('a ragged table does not report its missing cells', () => {
  const rows = [[cell('A'), cell('B'), cell('C')], [cell('1')]];
  assert.deepEqual(emptyTableColumns(rows), []);
});

test('an empty table reports nothing', () => {
  assert.deepEqual(emptyTableColumns([]), []);
});

// --------------------------------------------------------------------------
// pageFindings
// --------------------------------------------------------------------------

/** A page with nothing wrong with it, for one field at a time to be broken. */
function observation(overrides = {}) {
  return {
    scrollWidth: 1280,
    clientWidth: 1280,
    wideElements: [],
    images: [],
    proseText: 'Ordinary prose.',
    tables: [],
    title: 'Agents',
    description: 'Build multi-action agentic systems.',
    consoleErrors: [],
    pageErrors: [],
    ...overrides,
  };
}

test('a clean observation produces no findings', () => {
  assert.deepEqual(pageFindings(observation()), []);
});

test('horizontal overflow is reported, naming the element that causes it', () => {
  const findings = pageFindings(
    observation({
      scrollWidth: 542,
      clientWidth: 375,
      wideElements: [{ selector: 'a.next', right: 542, left: 305, clipped: false }],
    }),
  );
  assert.deepEqual(checks(findings), ['horizontal-overflow']);
  assert.match(findings[0].message, /542px of content in 375px/);
  assert.match(findings[0].detail, /a\.next \(right edge 542px\)/);
});

test('an element clipped by a scrolling ancestor is not named', () => {
  // Code blocks and wide tables scroll inside their own box on every page that
  // has one. Naming them buries the finding that actually moved the page.
  const findings = pageFindings(
    observation({
      scrollWidth: 408,
      clientWidth: 375,
      wideElements: [
        { selector: 'code', right: 831, left: 35, clipped: true },
        { selector: 'a.next', right: 408, left: 286, clipped: false },
      ],
    }),
  );
  assert.equal(findings.length, 1);
  assert.equal(findings[0].detail, 'a.next (right edge 408px)');
});

test('a page that does not scroll is not reported, however wide its contents', () => {
  const findings = pageFindings(
    observation({
      wideElements: [{ selector: 'pre', right: 3000, left: 35, clipped: true }],
    }),
  );
  assert.deepEqual(findings, []);
});

test('a broken same-origin image is a failure', () => {
  const findings = pageFindings(
    observation({ images: [{ src: '/assets/gone.png', loaded: false, external: false }] }),
  );
  assert.deepEqual(checks(findings), ['broken-image']);
  assert.equal(isAdvisory(findings[0]), false);
});

test('an unreachable external image is a note, not a failure', () => {
  // This environment has no egress. Reporting a shields.io badge as broken
  // would make every run red and teach people to ignore the output.
  const findings = pageFindings(
    observation({
      images: [{ src: 'https://img.shields.io/pypi/v/kiln-ai.svg', loaded: false, external: true }],
    }),
  );
  assert.deepEqual(checks(findings), ['external-image-unverified']);
  assert.equal(isAdvisory(findings[0]), true);
});

test('a loaded image is not reported', () => {
  assert.deepEqual(
    pageFindings(observation({ images: [{ src: '/_astro/x.webp', loaded: true, external: false }] })),
    [],
  );
});

test('a missing title is reported', () => {
  assert.deepEqual(checks(pageFindings(observation({ title: '' }))), ['missing-title']);
});

test('a missing description is reported', () => {
  assert.deepEqual(checks(pageFindings(observation({ description: '' }))), ['missing-description']);
});

test('literal markup in the rendered prose is reported', () => {
  const findings = pageFindings(observation({ proseText: 'Step 3\n<figure>\nStep 4' }));
  assert.deepEqual(checks(findings), ['unrendered-html']);
});

test('an empty table column is reported with its index', () => {
  const findings = pageFindings(
    observation({ tables: [[[cell('A'), cell()], [cell('1'), cell()]]] }),
  );
  assert.deepEqual(checks(findings), ['empty-table-column']);
  assert.match(findings[0].message, /column 1/);
});

test('a same-origin console error is reported and an external one is not', () => {
  const findings = pageFindings(
    observation({
      consoleErrors: [
        { text: '404', url: 'http://localhost/assets/gone.png', external: false },
        { text: 'ERR_TUNNEL', url: 'https://img.shields.io/x.svg', external: true },
      ],
    }),
  );
  assert.deepEqual(checks(findings), ['console-error']);
});

test('an uncaught page error is reported', () => {
  assert.deepEqual(checks(pageFindings(observation({ pageErrors: ['x is not defined'] }))), [
    'page-error',
  ]);
});

// --------------------------------------------------------------------------
// isExternal and parseArgs
// --------------------------------------------------------------------------

test('isExternal separates the site under test from everything else', () => {
  const origin = 'http://127.0.0.1:4321';
  assert.equal(isExternal('/assets/x.png', origin), false);
  assert.equal(isExternal('#top', origin), false);
  assert.equal(isExternal(`${origin}/_astro/x.webp`, origin), false);
  assert.equal(isExternal('https://img.shields.io/x.svg', origin), true);
  assert.equal(isExternal('', origin), false);
});

test('parseArgs defaults to the static sweep over dist', () => {
  assert.deepEqual(parseArgs([]), {
    dist: 'dist',
    content: 'src/content/docs',
    browser: false,
    baseUrl: null,
  });
});

test('parseArgs accepts both spellings and strips a trailing slash', () => {
  assert.deepEqual(parseArgs(['--browser', '--base-url', 'https://x.pages.dev/']), {
    dist: 'dist',
    content: 'src/content/docs',
    browser: true,
    baseUrl: 'https://x.pages.dev',
  });
  assert.equal(parseArgs(['--dist=out']).dist, 'out');
});

test('parseArgs rejects an unknown argument rather than ignoring it', () => {
  assert.throws(() => parseArgs(['--browserr']), QaError);
  assert.throws(() => parseArgs(['--dist']), QaError);
});

// The cutover runbook points --base-url at production. Silently ignoring it
// there would print "no findings" for a site nothing had requested.
test('parseArgs refuses --base-url without --browser rather than ignoring it', () => {
  assert.throws(
    () => parseArgs(['--base-url', 'https://docs.kiln.tech']),
    (error) => error instanceof QaError && /--browser/.test(error.message),
  );
  assert.equal(parseArgs(['--browser', '--base-url', 'https://x']).baseUrl, 'https://x');
});

// The guard above tests for null, not truthiness. An unset shell variable —
// `URL=` on one line, `--base-url "$URL"` on another — arrives as '', and a
// truthiness test would wave it through to the same false green.
test('parseArgs rejects an empty value rather than reading it as absent', () => {
  for (const flag of ['--base-url', '--dist', '--content']) {
    assert.throws(
      () => parseArgs([flag, '']),
      (error) => error instanceof QaError && /empty value/.test(error.message),
      `${flag} accepted an empty value`,
    );
  }
  // Still refused with --browser present: empty is invalid, not merely unpaired.
  assert.throws(() => parseArgs(['--browser', '--base-url', '']), QaError);
});

// --------------------------------------------------------------------------
// The CLI
// --------------------------------------------------------------------------

const SCRIPT = fileURLToPath(new URL('./qa_pages.mjs', import.meta.url));
const run = promisify(execFile);

/** A content directory holding one page with two pieces of residual GitBook markup. */
async function fixtureSite() {
  const root = await mkdtemp(path.join(tmpdir(), 'qa-pages-'));
  await mkdir(path.join(root, 'content'));
  await mkdir(path.join(root, 'dist'));
  await writeFile(
    path.join(root, 'content', 'fixture.md'),
    '---\ntitle: Fixture\n---\n<table data-view="cards"><tr><th data-hidden></th></tr></table>\n',
  );
  return root;
}

async function runScript(script, args) {
  return run(process.execPath, [script, ...args], { env: process.env }).catch((error) => error);
}

async function runCli(args) {
  return runScript(SCRIPT, args);
}

/**
 * A copy of the sweep whose only resolvable `playwright` has a failing
 * `launch()`.
 *
 * Stands in for the common half-installed case — the package is there, the
 * Chromium binary is not — which fails *after* the module has loaded, and so
 * is not a `QaError`.
 *
 * The stub has to be found by ordinary `node_modules` resolution, not
 * `NODE_PATH`: `NODE_PATH` is consulted only after the directory walk, so a
 * real `site/node_modules/playwright` would win and the stub would never
 * load. The README tells a reader to install exactly that before a
 * `--browser` sweep, so the test cannot assume it is absent. Copying the
 * script into a scratch tree moves the walk somewhere the test owns: the
 * sweep imports nothing but node builtins, and it resolves `playwright`
 * relative to its own location.
 */
async function stubbedSweepPath(root) {
  const stub = path.join(root, 'stub', 'node_modules', 'playwright');
  await mkdir(stub, { recursive: true });
  await writeFile(
    path.join(stub, 'package.json'),
    '{ "name": "playwright", "version": "0.0.0-stub", "main": "index.js" }',
  );
  await writeFile(
    path.join(stub, 'index.js'),
    "module.exports = { chromium: { launch: async () => { throw new Error('stub: Executable does not exist'); } } };",
  );
  const scripts = path.join(root, 'stub', 'scripts');
  await mkdir(scripts, { recursive: true });
  await copyFile(SCRIPT, path.join(scripts, 'qa_pages.mjs'));
  return path.join(scripts, 'qa_pages.mjs');
}

test('the static report is printed and exits non-zero', async () => {
  const root = await fixtureSite();
  const result = await runCli(['--content', `${root}/content`, '--dist', `${root}/dist`]);
  assert.equal(result.code, 1);
  assert.match(result.stdout, /gitbook-card-table/);
  assert.match(result.stdout, /gitbook-hidden-column/);
});

test('--browser never swallows the static findings, however it ends', async () => {
  // The half that cannot run must not take the half that did with it: without
  // this, a page full of residual markup reports nothing when Playwright is
  // missing, which is indistinguishable from a clean page.
  const root = await fixtureSite();
  const result = await runCli(['--browser', '--content', `${root}/content`, '--dist', `${root}/dist`]);
  assert.notEqual(result.code, 0);
  assert.match(result.stdout, /gitbook-card-table/);
  assert.match(result.stdout, /gitbook-hidden-column/);
});

// `dist` supplies the page list even when the pages are fetched from a
// deployment, so an unbuilt dist sweeps nothing. Reporting that as a pass is
// the defect the --base-url guard exists to prevent, arriving by another door.
test('--browser refuses to report on a dist with no built pages', async () => {
  const root = await fixtureSite();
  const result = await runScript(await stubbedSweepPath(root), [
    '--browser',
    '--base-url',
    'https://example.invalid',
    '--content',
    `${root}/content`,
    '--dist',
    `${root}/dist`,
  ]);
  assert.equal(result.code, 2);
  assert.match(result.stderr, /no built pages/);
  // and the static findings still survive it
  assert.match(result.stdout, /gitbook-card-table/);
});

test('a browser that fails after it loads does not swallow them either', async () => {
  // The failure that is not a QaError: Playwright resolves, its browser binary
  // does not exist. Catching only QaError would print nothing but a stack.
  const root = await fixtureSite();
  // A built page, so the sweep gets as far as launching. Without it the
  // no-built-pages guard stops it earlier and this stops testing the launch.
  await writeFile(path.join(root, 'dist', 'index.html'), '<html><body>fixture</body></html>');
  const result = await runScript(await stubbedSweepPath(root), [
    '--browser',
    '--content',
    `${root}/content`,
    '--dist',
    `${root}/dist`,
  ]);
  assert.equal(result.code, 2);
  assert.match(result.stdout, /gitbook-card-table/);
  assert.match(result.stdout, /gitbook-hidden-column/);
  assert.match(result.stderr, /could not finish/);
});
