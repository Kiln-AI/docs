import { defineRouteMiddleware } from '@astrojs/starlight/route-data';

import { absolutizePageBody } from './lib/page-markdown';

/**
 * Make the theme's "Copy page" blob usable outside this site.
 *
 * `starlight-theme-black` builds that blob from `entry.body`, which carries the
 * repo-relative image paths the build needs (`../../../assets/foo.png`) and
 * nobody else can resolve. Rewriting `body` here fixes the blob and the
 * "Open in ChatGPT/Claude/v0" payloads without copying 130 lines of the theme's
 * `PageTitle` markup into this repo, where it would silently diverge on the
 * next theme upgrade.
 *
 * Safe because rendering does not read `body`: `render(entry)` uses the
 * precompiled `entry.rendered`. The rewrite is also idempotent, so it does not
 * matter if an entry is seen more than once.
 */
export const onRequest = defineRouteMiddleware(async (context) => {
	const route = context.locals.starlightRoute;
	const entry = route?.entry;
	if (!entry?.body || !context.site) return;

	route.entry = { ...entry, body: await absolutizePageBody(entry.body, context.site.origin) };
});
