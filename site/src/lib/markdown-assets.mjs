/**
 * Rewrite asset references in a page's raw markdown to absolute URLs.
 *
 * Pages reference images with paths that only mean something relative to the
 * file they live in (`../../../assets/foo.png`) or relative to the site root
 * (`/assets/bar.mp4`). That is correct for the build, but the same markdown is
 * also handed to machines — the theme's "Copy page" blob and the per-page
 * `.md` endpoints — where neither form resolves. This module turns both into
 * absolute URLs.
 *
 * Plain `.mjs` rather than `.ts` so `node --test` can import it directly
 * alongside Astro.
 */

/** Schemes and prefixes that are already resolvable and must not be touched. */
const ABSOLUTE_REFERENCE = /^(?:[a-z][a-z0-9+.-]*:|\/\/|#)/i;

/** `../assets/NAME`, at any nesting depth. Nothing else reaches src/assets. */
const SRC_ASSET_REFERENCE = /^(?:\.\.\/)+assets\/([^/]+)$/;

/** `/assets/NAME` — files served verbatim out of public/. */
const PUBLIC_ASSET_REFERENCE = /^\/assets\/[^/]+$/;

/** Markdown image destinations: the `…` in `![alt](…)`. */
const MARKDOWN_IMAGE = /(!\[[^\]]*\]\()([^)\s]*)(\))/g;

/**
 * `src="…"` and `href="…"` in the raw HTML blocks pages still use.
 *
 * The lookbehind keeps it off attributes that merely end in those letters —
 * `data-src`, `xlink:href`, `poster-src` — whose values are not necessarily
 * URLs we own. No page uses one today; this is here so that stays true by
 * construction rather than by luck.
 */
const HTML_ATTRIBUTE = /(?<![\w:-])((?:src|href)=")([^"]*)(")/g;

/**
 * The filename an `../…/assets/NAME` reference points at.
 *
 * @param {string} reference
 * @returns {string | null} the filename, or null if this is not such a reference
 */
export function srcAssetName(reference) {
	const match = SRC_ASSET_REFERENCE.exec(reference);
	return match ? match[1] : null;
}

/**
 * Is this a reference to a file served verbatim from `public/assets/`?
 *
 * @param {string} reference
 * @returns {boolean}
 */
export function isPublicAssetPath(reference) {
	return PUBLIC_ASSET_REFERENCE.test(reference);
}

/**
 * Every `src/assets/` filename `markdown` refers to.
 *
 * Callers resolve built URLs for exactly these and no more: asking the image
 * service about an unreferenced image would emit a variant of it that nothing
 * on the site uses.
 *
 * @param {string} markdown
 * @returns {Set<string>}
 */
export function srcAssetNames(markdown) {
	const names = new Set();
	for (const pattern of [MARKDOWN_IMAGE, HTML_ATTRIBUTE]) {
		for (const match of markdown.matchAll(pattern)) {
			const name = srcAssetName(match[2]);
			if (name !== null) names.add(name);
		}
	}
	return names;
}

export class UnresolvedAssetError extends Error {}

/**
 * Rewrite every asset reference in `markdown` to an absolute URL.
 *
 * References that are already absolute, and paths that point at neither asset
 * tree, are left exactly as they are. Re-running on already-rewritten markdown
 * is a no-op, which is what makes it safe to call from route middleware.
 *
 * @param {string} markdown raw page body
 * @param {(name: string) => string | undefined} resolveSrcAsset
 *   filename in `src/assets/` -> the URL path the build emits for it
 * @param {string} origin e.g. `https://docs.kiln.tech`, no trailing slash
 * @returns {string}
 */
export function absolutizeAssetReferences(markdown, resolveSrcAsset, origin) {
	const base = origin.replace(/\/$/, '');

	const rewrite = (reference) => {
		if (!reference || ABSOLUTE_REFERENCE.test(reference)) return reference;

		if (isPublicAssetPath(reference)) return base + reference;

		const name = srcAssetName(reference);
		if (name === null) return reference;

		// Percent-encoding is how a filename with spaces survives a markdown
		// destination, so look the file up under its real name.
		const resolved = resolveSrcAsset(name) ?? resolveSrcAsset(decodeAssetName(name));
		if (resolved === undefined) {
			throw new UnresolvedAssetError(
				`no built URL for src/assets/${name} (referenced as ${reference})`,
			);
		}
		return base + resolved;
	};

	return markdown
		.replace(MARKDOWN_IMAGE, (_match, open, reference, close) => open + rewrite(reference) + close)
		.replace(HTML_ATTRIBUTE, (_match, open, reference, close) => open + rewrite(reference) + close);
}

/**
 * Percent-decode a filename, tolerating names that contain a bare `%`.
 *
 * A markdown destination cannot hold a raw space, so a file such as
 * `rag icon 2-2.png` is referenced encoded and has to be looked up decoded.
 *
 * @param {string} name
 * @returns {string}
 */
export function decodeAssetName(name) {
	try {
		return decodeURIComponent(name);
	} catch {
		return name;
	}
}
