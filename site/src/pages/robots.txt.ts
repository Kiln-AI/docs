import type { APIRoute } from 'astro';

/**
 * GitBook served a `robots.txt`; nothing in the Astro build does. Generated
 * rather than dropped in `public/` so the origin comes from `site` in
 * `astro.config.mjs` instead of being spelled out a second time.
 *
 * `@astrojs/sitemap` always emits an index plus numbered children, so the
 * sitemap advertised here is `sitemap-index.xml`. `/sitemap.xml`, which is
 * what Search Console has on file from GitBook, 301s to it via `_redirects`.
 */
export const GET: APIRoute = ({ site }) => {
	if (!site) throw new Error('`site` must be set in astro.config.mjs to build robots.txt');
	const body = ['User-agent: *', 'Allow: /', '', `Sitemap: ${new URL('/sitemap-index.xml', site).href}`, ''];
	return new Response(body.join('\n'), {
		headers: { 'Content-Type': 'text/plain; charset=utf-8' },
	});
};
