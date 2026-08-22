/**
 * Tests for the frontmatter block on the per-page `.md` endpoints.
 *
 * These parse what the code emits with a real YAML parser rather than
 * eyeballing the string. The defect that motivated them —
 * `title: Evaluate RAG Accuracy: Q&A Evals` — looked perfectly fine by eye and
 * failed on the first parse.
 *
 * Run from `site/`:
 *
 *     npm test
 *     node --test "scripts/*.test.mjs"
 */

import test from 'node:test';
import assert from 'node:assert/strict';
import { parse } from 'yaml';

import { pageFrontmatter, yamlScalar } from '../src/lib/frontmatter.mjs';

/** Parse a frontmatter block back into the data it claims to carry. */
function parseBlock(block) {
  const match = /^---\n([\s\S]*?)\n---\n$/.exec(block);
  assert.ok(match, `not a frontmatter block: ${JSON.stringify(block)}`);
  return parse(match[1]);
}

function roundTrip(data) {
  return parseBlock(pageFrontmatter(data));
}

test('round-trips an ordinary page', () => {
  assert.deepEqual(roundTrip({ title: 'Quickstart', description: 'Download our app' }), {
    title: 'Quickstart',
    description: 'Download our app',
  });
});

test('round-trips the corpus title that broke bare YAML', () => {
  // docs/evals-and-specs/evaluate-rag-accuracy-q-and-a-evals
  const title = 'Evaluate RAG Accuracy: Q&A Evals';
  assert.equal(roundTrip({ title }).title, title);
});

test('round-trips every other punctuated title in the corpus', () => {
  for (const title of [
    'Structured Data / JSON',
    'Tools & MCP',
    'Documents & Search (RAG)',
    'Reasoning & Chain of Thought',
    'Input Templates & Feature Engineering',
  ]) {
    assert.equal(roundTrip({ title }).title, title);
  }
});

test('round-trips a description containing a colon', () => {
  const description = 'Score your evals with LLM judges: fast, cheap, deterministic';
  assert.equal(roundTrip({ title: 'x', description }).description, description);
});

test('round-trips the YAML metacharacters that break unquoted scalars', () => {
  for (const title of [
    'a: b',
    '# not a comment',
    '- not a list item',
    '[not a flow sequence]',
    '{not a flow mapping}',
    '*not an alias',
    '&not an anchor',
    '"already quoted"',
    "it's got an apostrophe",
    'trailing space ',
    'yes',
    '3.14',
    'null',
    'back\\slash',
  ]) {
    assert.equal(roundTrip({ title }).title, title, `failed on ${JSON.stringify(title)}`);
  }
});

test('omits description entirely when the page has none', () => {
  const block = pageFrontmatter({ title: 'Keyboard Shortcuts' });
  assert.ok(!block.includes('description'));
  assert.deepEqual(parseBlock(block), { title: 'Keyboard Shortcuts' });
});

test('omits an empty description rather than emitting a blank one', () => {
  assert.deepEqual(parseBlock(pageFrontmatter({ title: 'x', description: '' })), { title: 'x' });
});

test('ends with a delimiter line and a newline, so a body can follow', () => {
  assert.ok(pageFrontmatter({ title: 'x' }).endsWith('---\n'));
});

test('yamlScalar emits a double-quoted flow scalar', () => {
  assert.equal(yamlScalar('a: b'), '"a: b"');
  assert.equal(parse(yamlScalar('a: b')), 'a: b');
});
