/**
 * The known-stale anchor allowlist, and the audit that stops it rotting.
 *
 * 24 links in the corpus point at headings that no longer exist. They were
 * already broken in the GitBook source — renamed upstream, links never
 * updated — so they are conversion damage from nobody, and repairing them is
 * a content edit the functional spec puts outside this migration. Phase 7
 * owns them. Meanwhile CI has to fail on a *new* broken link without failing
 * on these, so `ref/stale_anchors.txt` lists them and
 * `starlight-links-validator` is handed an `exclude` predicate built from it.
 *
 * An allowlist that only ever grows is worse than no gate at all, so the
 * entries are audited against reality on every build — see
 * `retiredStaleAnchors` for the four ways a line stops being true, and
 * `staleAnchorsStillStale()` in `build_integrations.mjs` for the wiring.
 *
 * Note what `exclude` costs: the validator consults it before any check, so
 * an excluded link is exempt from *all* validation, not just its hash. That
 * is why the audit asserts the target page still exists rather than only that
 * the anchor is still missing — otherwise deleting `/docs/prompts/` would
 * silently take five excused links down with it.
 */

import path from 'node:path';

/**
 * @typedef {object} StaleAnchor
 * @property {string} page  Page path under `src/content/docs/`, e.g. `docs/prompts.md`.
 * @property {string} link  The link exactly as authored, e.g. `/docs/prompts/#prompt-generators`.
 * @property {number} line  1-based line number in the allowlist, for error messages.
 */

/**
 * Parse `ref/stale_anchors.txt`.
 *
 * Strict about shape because every field is load-bearing: a typo in a page
 * name would silently stop excusing the link it names, and a typo in a link
 * would silently excuse nothing while looking like it did. Both would surface
 * as a confusing build failure rather than as the real mistake, so they are
 * rejected here with a line number instead.
 *
 * @param {string} text
 * @returns {StaleAnchor[]}
 */
export function parseStaleAnchors(text) {
	const entries = [];
	const seen = new Map();

	text.split('\n').forEach((raw, index) => {
		const line = index + 1;
		const content = raw.trim();
		if (content === '' || content.startsWith('#')) return;

		const fields = content.split(/\s+/);
		if (fields.length !== 2) {
			throw new Error(
				`${STALE_ANCHORS_FILE} line ${line}: expected "<page> <link>", got ${fields.length} ` +
					`field(s): ${content}`,
			);
		}

		const [page, link] = /** @type {[string, string]} */ (fields);
		if (page.startsWith('/') || page.includes('..') || !/\.mdx?$/.test(page)) {
			throw new Error(
				`${STALE_ANCHORS_FILE} line ${line}: "${page}" is not a page path under ` +
					'src/content/docs/, e.g. docs/prompts.md. Absolute paths and `..` are ' +
					'rejected: the audit joins this onto the content directory, and a path ' +
					'that escapes it would excuse nothing while reporting itself still stale.',
			);
		}
		if (!link.startsWith('/') || !link.includes('#') || link.endsWith('#')) {
			throw new Error(
				`${STALE_ANCHORS_FILE} line ${line}: "${link}" is not a root-relative link with a ` +
					'hash. This file excuses stale anchors only; a broken page link is a real error.',
			);
		}

		const key = `${page} ${link}`;
		const earlier = seen.get(key);
		if (earlier !== undefined) {
			throw new Error(
				`${STALE_ANCHORS_FILE} line ${line}: duplicate of line ${earlier}. One line excuses ` +
					'every occurrence of that link on that page.',
			);
		}
		seen.set(key, line);
		entries.push({ page, link, line });
	});

	return entries;
}

/** Where the allowlist lives, relative to `site/`. Named for error messages. */
export const STALE_ANCHORS_FILE = 'ref/stale_anchors.txt';

/**
 * An `exclude` predicate for `starlight-links-validator`.
 *
 * Scoped to the (page, link) pair rather than to the link alone: the same
 * dead anchor appearing on a page that is not listed is still a build
 * failure, which is what keeps the list from turning into a blanket amnesty
 * for `/docs/prompts/#prompt-generators` everywhere.
 *
 * @param {StaleAnchor[]} entries
 * @param {string} contentDir  Absolute path of `src/content/docs`.
 * @returns {(context: { file: string; link: string; slug: string }) => boolean}
 */
export function staleAnchorExclusion(entries, contentDir) {
	const excused = new Set(entries.map(({ page, link }) => `${page} ${link}`));
	return ({ file, link }) => excused.has(`${docsPathOf(file, contentDir)} ${link}`);
}

/**
 * The page path the validator would report for `file`, e.g. `docs/prompts.md`.
 *
 * @param {string} file  Absolute path of a content file.
 * @param {string} contentDir  Absolute path of `src/content/docs`.
 */
function docsPathOf(file, contentDir) {
	return path.relative(contentDir, file).split(path.sep).join('/');
}

/**
 * Entries that no longer describe a stale anchor, with the reason for each.
 *
 * This is the whole safety story for the allowlist, so it checks the entire
 * claim a line makes — that this page still carries this link, that the link
 * still lands on a real page, and that the anchor is still missing from it —
 * rather than only the last part. Anything else is reported, because an
 * exclusion that has stopped being true is suppressing something nobody
 * decided to suppress.
 *
 * Readers are injected so the audit is testable without a `dist` on disk.
 *
 * @param {StaleAnchor[]} entries
 * @param {(page: string) => string | null} readSource
 *   Text of a page under `src/content/docs/`, or null if it is gone.
 * @param {(urlPath: string) => string | null} readBuiltPage
 *   HTML of a built page given its URL path, or null if it is gone.
 * @returns {{ entry: StaleAnchor; reason: string }[]}
 */
export function retiredStaleAnchors(entries, readSource, readBuiltPage) {
	const retired = [];

	for (const entry of entries) {
		const source = readSource(entry.page);
		if (source === null) {
			retired.push({ entry, reason: `${entry.page} no longer exists` });
			continue;
		}
		if (!linksTo(source, entry.link)) {
			retired.push({ entry, reason: `${entry.page} no longer links to ${entry.link}` });
			continue;
		}

		const [urlPath, hash] = splitHash(entry.link);
		const html = readBuiltPage(urlPath);
		if (html === null) {
			retired.push({
				entry,
				reason:
					`${urlPath} no longer builds, so this line is excusing a broken page link ` +
					'rather than a stale anchor',
			});
			continue;
		}
		if (hasElementId(html, hash)) {
			retired.push({ entry, reason: `${urlPath} now has an element with id="${hash}"` });
		}
	}

	return retired;
}

/**
 * Whether `source` still carries `link` as a whole link.
 *
 * A bare substring test would keep a repaired entry alive whenever one link is
 * a strict prefix of another on the same page — `/docs/prompts/#custom-prompts`
 * is a prefix of `/docs/prompts/#custom-prompts-saved-prompts`, and both are on
 * the allowlist today, just not on the same page. So require the match to end
 * where a slug can end: anything a heading id could continue with disqualifies
 * it.
 */
function linksTo(source, link) {
	const escaped = link.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
	return new RegExp(`${escaped}(?![\\w-])`).test(source);
}

/** `/docs/prompts/#prompt-generators` -> `['/docs/prompts/', 'prompt-generators']`. */
export function splitHash(link) {
	const index = link.indexOf('#');
	return [link.slice(0, index), link.slice(index + 1)];
}

/**
 * Built-page path, relative to `dist`, for a URL path.
 *
 * `trailingSlash: 'always'` with `build.format: 'directory'` puts every page
 * at `<path>/index.html`, including the root — see astro.config.mjs.
 */
export function builtPagePath(urlPath) {
	return path.posix.join(urlPath.replace(/^\/+/, ''), 'index.html');
}

/**
 * Whether `html` has an element carrying `id`.
 *
 * A substring test rather than a parse: the question is only whether the
 * fragment resolves, and an `id` written in prose would have to be spelled as
 * a real attribute to match.
 */
function hasElementId(html, id) {
	return html.includes(`id="${id}"`) || html.includes(`id='${id}'`);
}
