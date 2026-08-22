/**
 * Tests for the known-stale anchor allowlist and its rot audit.
 *
 * The allowlist is the one place in CI where a check is deliberately switched
 * off, so what these pin down is mostly the *limits* of that: an entry
 * excuses one link on one page and nothing else, and it stops excusing
 * anything the moment it stops being true.
 *
 * Run from `site/`:
 *
 *     npm test
 *     node --test "scripts/*.test.mjs"
 */

import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  builtPagePath,
  parseStaleAnchors,
  retiredStaleAnchors,
  splitHash,
  staleAnchorExclusion,
  STALE_ANCHORS_FILE,
} from './stale_anchors.mjs';

const SITE_DIR = fileURLToPath(new URL('..', import.meta.url));
const CONTENT_DIR = path.join(SITE_DIR, 'src', 'content', 'docs');

/** Absolute path of a content page, the way the validator hands it to us. */
function contentFile(page) {
  return path.join(CONTENT_DIR, ...page.split('/'));
}

test('parses a page and a link, ignoring comments and blank lines', () => {
  assert.deepEqual(
    parseStaleAnchors('# a comment\n\ndocs/prompts.md  /docs/prompts/#prompt-generators\n'),
    [{ page: 'docs/prompts.md', link: '/docs/prompts/#prompt-generators', line: 3 }],
  );
});

test('accepts an .mdx page', () => {
  const [entry] = parseStaleAnchors('docs/index.mdx /docs/prompts/#gone');
  assert.equal(entry.page, 'docs/index.mdx');
});

test('reports the real line number, counting comments', () => {
  const text = '# one\n# two\n\ndocs/prompts.md\n';
  assert.throws(() => parseStaleAnchors(text), /line 4: expected "<page> <link>", got 1 field/);
});

test('rejects a line with a third field', () => {
  assert.throws(
    () => parseStaleAnchors('docs/prompts.md /docs/prompts/#gone invalid hash'),
    /line 1: expected "<page> <link>", got 4 field/,
  );
});

test('rejects a page path that is not under src/content/docs', () => {
  assert.throws(
    () => parseStaleAnchors('/docs/prompts.md /docs/prompts/#gone'),
    /is not a page path under src\/content\/docs/,
  );
});

test('rejects a page path that is not markdown', () => {
  assert.throws(
    () => parseStaleAnchors('docs/prompts /docs/prompts/#gone'),
    /is not a page path under src\/content\/docs/,
  );
});

test('rejects a link that is not root-relative', () => {
  assert.throws(
    () => parseStaleAnchors('docs/prompts.md ../prompts/#gone'),
    /is not a root-relative link with a hash/,
  );
});

test('rejects a link with no hash, because a broken page link is a real error', () => {
  assert.throws(
    () => parseStaleAnchors('docs/prompts.md /docs/prompts/'),
    /is not a root-relative link with a hash/,
  );
});

test('rejects a link whose hash is empty', () => {
  assert.throws(
    () => parseStaleAnchors('docs/prompts.md /docs/prompts/#'),
    /is not a root-relative link with a hash/,
  );
});

test('rejects a duplicate entry and names the line it repeats', () => {
  const text = 'docs/prompts.md /docs/prompts/#gone\ndocs/prompts.md /docs/prompts/#gone\n';
  assert.throws(() => parseStaleAnchors(text), /line 2: duplicate of line 1/);
});

test('the committed allowlist parses and still holds the 24 anchors phase 2 found', () => {
  // A regression guard on the file itself, in the spirit of RepoStateTest in
  // test_build_redirects.py. The count is not sacred — it should *fall* as
  // phase 7 repairs anchors — but it must never rise without a decision.
  const entries = parseStaleAnchors(readFileSync(path.join(SITE_DIR, STALE_ANCHORS_FILE), 'utf8'));
  assert.ok(entries.length <= 24, `${entries.length} excused anchors; phase 2 recorded 24`);
  for (const { page, link } of entries) {
    assert.ok(readFileSync(contentFile(page), 'utf8').includes(link), `${page} does not link ${link}`);
  }
});

test('excuses the exact page and link it names', () => {
  const exclude = staleAnchorExclusion(
    parseStaleAnchors('docs/prompts.md /docs/prompts/#prompt-generators'),
    CONTENT_DIR,
  );
  assert.equal(
    exclude({
      file: contentFile('docs/prompts.md'),
      link: '/docs/prompts/#prompt-generators',
      slug: 'docs/prompts',
    }),
    true,
  );
});

test('does not excuse the same dead anchor on a page that is not listed', () => {
  // The property that keeps the list from becoming a blanket amnesty: three
  // pages link `/docs/prompts/#prompt-generators` and all three are listed,
  // so a fourth must still fail.
  const exclude = staleAnchorExclusion(
    parseStaleAnchors('docs/prompts.md /docs/prompts/#prompt-generators'),
    CONTENT_DIR,
  );
  assert.equal(
    exclude({
      file: contentFile('docs/agents.md'),
      link: '/docs/prompts/#prompt-generators',
      slug: 'docs/agents',
    }),
    false,
  );
});

test('does not excuse a different link on a listed page', () => {
  const exclude = staleAnchorExclusion(
    parseStaleAnchors('docs/prompts.md /docs/prompts/#prompt-generators'),
    CONTENT_DIR,
  );
  assert.equal(
    exclude({
      file: contentFile('docs/prompts.md'),
      link: '/docs/prompts/#something-else',
      slug: 'docs/prompts',
    }),
    false,
  );
});

test('matches a page nested several directories deep', () => {
  const page = 'docs/fine-tuning/guide-train-a-reasoning-model.md';
  const exclude = staleAnchorExclusion(
    parseStaleAnchors(`${page} /docs/prompts/#custom-prompts-saved-prompts`),
    CONTENT_DIR,
  );
  assert.equal(
    exclude({
      file: contentFile(page),
      link: '/docs/prompts/#custom-prompts-saved-prompts',
      slug: 'docs/fine-tuning/guide-train-a-reasoning-model',
    }),
    true,
  );
});

const ENTRY = parseStaleAnchors('docs/prompts.md /docs/prompts/#prompt-generators');
const LIVE_SOURCE = () => 'see [generators](/docs/prompts/#prompt-generators)';
const LIVE_PAGE = () => '<h2 id="using-prompts">Using prompts</h2>';

test('retires nothing while the anchor is still stale', () => {
  assert.deepEqual(retiredStaleAnchors(ENTRY, LIVE_SOURCE, LIVE_PAGE), []);
});

test('retires an entry whose page is gone', () => {
  const [retired] = retiredStaleAnchors(ENTRY, () => null, LIVE_PAGE);
  assert.match(retired.reason, /docs\/prompts\.md no longer exists/);
  assert.equal(retired.entry.line, 1);
});

test('retires an entry whose page no longer carries the link', () => {
  const [retired] = retiredStaleAnchors(ENTRY, () => 'the link was rewritten', LIVE_PAGE);
  assert.match(retired.reason, /no longer links to \/docs\/prompts\/#prompt-generators/);
});

test('retires an entry whose target page no longer builds', () => {
  // The hole this closes: `exclude` exempts a link from *all* validation, so
  // without this the deleted page would take five excused links down quietly.
  const [retired] = retiredStaleAnchors(ENTRY, LIVE_SOURCE, () => null);
  assert.match(retired.reason, /\/docs\/prompts\/ no longer builds/);
  assert.match(retired.reason, /broken page link rather than a stale anchor/);
});

test('retires an entry whose anchor has come back', () => {
  const withHeading = () => '<h2 id="prompt-generators">Prompt Generators</h2>';
  const [retired] = retiredStaleAnchors(ENTRY, LIVE_SOURCE, withHeading);
  assert.match(retired.reason, /now has an element with id="prompt-generators"/);
});

test('sees a single-quoted id too', () => {
  const withHeading = () => "<h2 id='prompt-generators'>Prompt Generators</h2>";
  assert.equal(retiredStaleAnchors(ENTRY, LIVE_SOURCE, withHeading).length, 1);
});

test('does not mistake the hash appearing in prose for an element id', () => {
  const prose = () => '<p>The old link was /docs/prompts/#prompt-generators</p>';
  assert.deepEqual(retiredStaleAnchors(ENTRY, LIVE_SOURCE, prose), []);
});

test('reports every retired entry, in the order they are listed', () => {
  const entries = parseStaleAnchors(
    ['docs/a.md /docs/x/#one', 'docs/b.md /docs/x/#two', 'docs/c.md /docs/x/#three'].join('\n'),
  );
  const source = (page) => (page === 'docs/b.md' ? 'nothing here' : `link /docs/x/#${page}`);
  const retired = retiredStaleAnchors(
    entries,
    (page) => (page === 'docs/a.md' ? null : source(page)),
    LIVE_PAGE,
  );
  assert.deepEqual(
    retired.map(({ entry }) => entry.page),
    ['docs/a.md', 'docs/b.md', 'docs/c.md'],
  );
});

test('splits a link into its path and its hash', () => {
  assert.deepEqual(splitHash('/docs/prompts/#prompt-generators'), [
    '/docs/prompts/',
    'prompt-generators',
  ]);
});

test('maps a URL path to the file the directory-format build emits', () => {
  assert.equal(builtPagePath('/docs/prompts/'), 'docs/prompts/index.html');
  assert.equal(builtPagePath('/'), 'index.html');
});
