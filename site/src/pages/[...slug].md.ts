import type { APIRoute, GetStaticPaths } from 'astro';
import { getCollection } from 'astro:content';

import { pageMarkdown } from '../lib/page-markdown';

/**
 * Per-page markdown, at the URLs GitBook served them from: `/docs/quickstart.md`
 * alongside `/docs/quickstart/`.
 *
 * These are the machine-readable half of the docs — an agent that asks for the
 * `.md` URL wants markdown, so this serves markdown rather than redirecting to
 * the HTML page. See `specs/.../phase_plans/phase_5.md` for the reasoning.
 */

/**
 * The landing page is a `template: splash` MDX page whose body is JSX, not
 * prose. There is no useful markdown to serve, and the mechanical slug for it
 * is the empty string, which would produce `/.md`.
 */
const LANDING_PAGE_ID = 'index';

export const getStaticPaths: GetStaticPaths = async () => {
	const entries = await getCollection('docs');
	return entries
		.filter((entry) => entry.id !== LANDING_PAGE_ID)
		.map((entry) => ({ params: { slug: entry.id }, props: { entry } }));
};

export const GET: APIRoute = async ({ props, site }) => {
	if (!site) throw new Error('`site` must be set in astro.config.mjs to build .md endpoints');
	const markdown = await pageMarkdown(props.entry, site.origin);
	return new Response(markdown, {
		headers: { 'Content-Type': 'text/markdown; charset=utf-8' },
	});
};
