import { getImage } from 'astro:assets';
import type { CollectionEntry } from 'astro:content';

import {
	absolutizeAssetReferences,
	decodeAssetName,
	srcAssetNames,
} from './markdown-assets.mjs';

/**
 * Images under `src/assets/` are served from a content-hashed,
 * format-converted path that only the build knows, so the only way to write an
 * absolute URL for one is to ask the image service for the same variant the
 * markdown pipeline asks for.
 */
const sourceImages = import.meta.glob<{ default: ImageMetadata }>(
	'../assets/*.{png,jpg,jpeg,gif,webp,avif,svg}',
	{ eager: true },
);

/**
 * Deliberately holds the modules' default exports without reading a single
 * property off them — see `plainMetadata`.
 */
const imagesByName = new Map(
	Object.entries(sourceImages).map(([path, module]) => [
		path.slice(path.lastIndexOf('/') + 1),
		module.default,
	]),
);

/**
 * Astro exports each `src/` image as a `Proxy` that records the image as
 * "referenced" the moment any property is read, which stops the build deleting
 * the unoptimized original from `dist/_astro` once the WebP exists. Reading
 * every image here would have added 7.5 MB of originals nothing serves.
 *
 * `clone` is the one property the proxy answers without recording anything: it
 * returns a structured clone of the same metadata, `fsPath` included, which is
 * all `getImage` needs. Modules loaded outside a server environment are plain
 * objects with no `clone`, so fall back to the object itself.
 */
function plainMetadata(image: ImageMetadata): ImageMetadata {
	return (image as ImageMetadata & { clone?: ImageMetadata }).clone ?? image;
}

/** Resolved on demand: `getImage` on an unreferenced image emits a dead variant. */
const builtUrls = new Map<string, Promise<string>>();

function builtAssetUrl(name: string): Promise<string> | undefined {
	const image = imagesByName.get(name) ?? imagesByName.get(decodeAssetName(name));
	if (!image) return undefined;

	let url = builtUrls.get(name);
	if (!url) {
		const metadata = plainMetadata(image);
		// SVGs pass through the image service untouched; everything else is
		// converted, and a markdown image with no width constraint gets WebP.
		url = metadata.format === 'svg'
			? Promise.resolve(metadata.src)
			: getImage({ src: metadata, format: 'webp' }).then((optimized) => optimized.src);
		builtUrls.set(name, url);
	}
	return url;
}

/** Built URLs for every `src/assets/` image `markdown` refers to. */
async function resolveReferencedAssets(markdown: string): Promise<Map<string, string>> {
	const resolved = new Map<string, string>();
	for (const name of srcAssetNames(markdown)) {
		const url = builtAssetUrl(name);
		// A name with no image behind it is left unresolved on purpose, so that
		// `absolutizeAssetReferences` is the one place that reports it.
		if (url) resolved.set(name, await url);
	}
	return resolved;
}

/**
 * Rewrite a page body's asset references to absolute URLs.
 *
 * Shared by the per-page `.md` endpoints and the route middleware that feeds
 * the theme's "Copy page" blob, so the two cannot drift.
 */
export async function absolutizePageBody(body: string, origin: string): Promise<string> {
	const urls = await resolveReferencedAssets(body);
	return absolutizeAssetReferences(body, (name) => urls.get(name), origin);
}

/**
 * The markdown for one page, as machines should see it: a small frontmatter
 * header and the page body with every asset reference made absolute.
 */
export async function pageMarkdown(
	entry: CollectionEntry<'docs'>,
	origin: string,
): Promise<string> {
	const body = await absolutizePageBody(entry.body ?? '', origin);
	const { title, description } = entry.data;
	const header = ['---', `title: ${title}`];
	if (description) header.push(`description: ${description}`);
	header.push('---', '');
	return `${header.join('\n')}\n${body}`.trim() + '\n';
}
