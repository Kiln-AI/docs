/**
 * Tests for the asset-reference rewriter behind the per-page `.md` endpoints
 * and the theme's "Copy page" blob.
 *
 * Run from `site/`:
 *
 *     npm test
 *     node --test "scripts/*.test.mjs"
 */

import test from 'node:test';
import assert from 'node:assert/strict';

import {
  UnresolvedAssetError,
  absolutizeAssetReferences,
  isPublicAssetPath,
  srcAssetName,
  srcAssetNames,
} from '../src/lib/markdown-assets.mjs';

const ORIGIN = 'https://docs.kiln.tech';

/** Stands in for the build's `src/assets` filename -> emitted URL map. */
const BUILT = new Map([
  ['json.png', '/_astro/json.CI3NTPX4_Z187LTJ.webp'],
  ['KBD.png', '/_astro/KBD.BdSoTKlp_1Mo8nt.webp'],
  ['diagram.svg', '/_astro/diagram.DRbvD29F.svg'],
]);

const resolve = (name) => BUILT.get(name);

const rewrite = (markdown) => absolutizeAssetReferences(markdown, resolve, ORIGIN);

test('srcAssetName recognises a src/assets reference at any depth', () => {
  assert.equal(srcAssetName('../../assets/json.png'), 'json.png');
  assert.equal(srcAssetName('../../../../assets/json.png'), 'json.png');
  assert.equal(srcAssetName('/assets/json.png'), null);
  assert.equal(srcAssetName('https://example.com/assets/json.png'), null);
});

test('isPublicAssetPath recognises a public/assets reference', () => {
  assert.equal(isPublicAssetPath('/assets/clip.mp4'), true);
  assert.equal(isPublicAssetPath('/assets/nested/clip.mp4'), false);
  assert.equal(isPublicAssetPath('../../assets/clip.mp4'), false);
});

test('rewrites a three-segment markdown image to an absolute optimized URL', () => {
  assert.equal(
    rewrite('![](../../../assets/json.png)'),
    `![](${ORIGIN}/_astro/json.CI3NTPX4_Z187LTJ.webp)`,
  );
});

test('rewrites a four-segment markdown image, the other depth in the corpus', () => {
  assert.equal(
    rewrite('![A caption](../../../../assets/KBD.png)'),
    `![A caption](${ORIGIN}/_astro/KBD.BdSoTKlp_1Mo8nt.webp)`,
  );
});

test('rewrites a public asset in an HTML src attribute', () => {
  assert.equal(
    rewrite('<video controls src="/assets/Run720.mp4"></video>'),
    `<video controls src="${ORIGIN}/assets/Run720.mp4"></video>`,
  );
});

test('rewrites a public asset in an href attribute', () => {
  assert.equal(
    rewrite('<a href="/assets/tuning2.png">cover</a>'),
    `<a href="${ORIGIN}/assets/tuning2.png">cover</a>`,
  );
});

test('preserves percent-encoding in a public asset name', () => {
  const encoded = '/assets/rag%20icon%202-2.png';
  assert.equal(rewrite(`<img src="${encoded}">`), `<img src="${ORIGIN}${encoded}">`);
});

test('resolves a percent-encoded src/assets name against its real filename', () => {
  const urls = new Map([['a b.png', '/_astro/a-b.hash.webp']]);
  assert.equal(
    absolutizeAssetReferences('![](../assets/a%20b.png)', (n) => urls.get(n), ORIGIN),
    `![](${ORIGIN}/_astro/a-b.hash.webp)`,
  );
});

test('leaves remote images alone', () => {
  const badge = '![PyPI](https://img.shields.io/pypi/v/kiln-ai.svg)';
  assert.equal(rewrite(badge), badge);
});

test('leaves data URIs, protocol-relative URLs and fragments alone', () => {
  const markdown = [
    '![](data:image/png;base64,AAAA)',
    '<a href="//example.com/x.png">x</a>',
    '<a href="#anchor">a</a>',
  ].join('\n');
  assert.equal(rewrite(markdown), markdown);
});

test('leaves internal page links alone — they already resolve against the origin', () => {
  const markdown = '[Git](/docs/collaboration/#option-1-use-git)';
  assert.equal(rewrite(markdown), markdown);
});

test('does not rewrite prose that merely looks like a path', () => {
  const markdown = 'Runs live at `{task}/.../eval_configs/{id}` on disk.';
  assert.equal(rewrite(markdown), markdown);
});

test('is idempotent, which is what makes the route middleware safe', () => {
  const once = rewrite('![](../../assets/json.png) <img src="/assets/skills.png">');
  assert.equal(rewrite(once), once);
});

test('throws when a src/assets reference has no built URL', () => {
  assert.throws(
    () => rewrite('![](../../assets/missing.png)'),
    (error) => error instanceof UnresolvedAssetError && /missing\.png/.test(error.message),
  );
});

test('an SVG keeps its own extension rather than being assumed to be WebP', () => {
  assert.equal(
    rewrite('![](../../assets/diagram.svg)'),
    `![](${ORIGIN}/_astro/diagram.DRbvD29F.svg)`,
  );
});

test('trims a trailing slash off the origin', () => {
  assert.equal(
    absolutizeAssetReferences('<img src="/assets/x.png">', resolve, `${ORIGIN}/`),
    `<img src="${ORIGIN}/assets/x.png">`,
  );
});

test('srcAssetNames collects each referenced image once and ignores the rest', () => {
  const markdown = [
    '![](../../assets/json.png)',
    '![](../../../assets/json.png)',
    '![](../../assets/KBD.png)',
    '<img src="/assets/skills.png">',
    '![](https://img.shields.io/badge/docs-pdoc-blue)',
  ].join('\n');
  assert.deepEqual([...srcAssetNames(markdown)].sort(), ['KBD.png', 'json.png']);
});

test('srcAssetNames is empty for a page with no local images', () => {
  assert.deepEqual([...srcAssetNames('# Title\n\nJust prose.')], []);
});
