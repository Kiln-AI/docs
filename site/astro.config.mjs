// @ts-check
import { readFileSync } from 'node:fs';
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import starlightThemeBlack from 'starlight-theme-black';
import starlightLlmsTxt from 'starlight-llms-txt';
import { markdownContentType, optimizedImagesOnly } from './scripts/build_integrations.mjs';

const SITE = 'https://docs.kiln.tech';

/**
 * Cloudflare Web Analytics site token.
 *
 * Account-specific, so it is not in the repo. Set `CLOUDFLARE_ANALYTICS_TOKEN`
 * as a build environment variable in the Cloudflare Pages project, or paste the
 * token into the fallback below. Until one of those happens, no beacon tag is
 * emitted and the site simply has no analytics — see "Analytics" in README.md.
 */
const CLOUDFLARE_ANALYTICS_TOKEN = process.env.CLOUDFLARE_ANALYTICS_TOKEN ?? '';

// One static image for every page, per the architecture; no per-page
// generation. Rebuild it with `npm run og`. Dimensions must match
// scripts/build_og_image.mjs.
const OG_IMAGE = new URL('/og.png', SITE).href;
const OG_IMAGE_WIDTH = '1200';
const OG_IMAGE_HEIGHT = '630';

// Committed content, kept out of this file so the config stays readable.
// Originally generated from GitBook's SUMMARY.md; edited by hand since.
let sidebar;
try {
  sidebar = JSON.parse(readFileSync(new URL('./sidebar.json', import.meta.url), 'utf8'));
} catch (cause) {
  throw new Error('site/sidebar.json could not be read.', { cause });
}

/** @type {NonNullable<Parameters<typeof starlight>[0]['head']>} */
const head = [
  // Starlight already emits og:title/type/url/description/site_name and
  // twitter:card=summary_large_image. Only the image tags are missing.
  { tag: 'meta', attrs: { property: 'og:image', content: OG_IMAGE } },
  { tag: 'meta', attrs: { property: 'og:image:width', content: OG_IMAGE_WIDTH } },
  { tag: 'meta', attrs: { property: 'og:image:height', content: OG_IMAGE_HEIGHT } },
  { tag: 'meta', attrs: { property: 'og:image:alt', content: 'Kiln AI documentation' } },
  { tag: 'meta', attrs: { name: 'twitter:image', content: OG_IMAGE } },
];

if (CLOUDFLARE_ANALYTICS_TOKEN) {
  head.push({
    tag: 'script',
    attrs: {
      defer: true,
      src: 'https://static.cloudflareinsights.com/beacon.min.js',
      'data-cf-beacon': JSON.stringify({ token: CLOUDFLARE_ANALYTICS_TOKEN }),
    },
  });
}

export default defineConfig({
  site: SITE,
  // Set explicitly rather than inherited from Astro's defaults: the canonical
  // URL form is what `redirects.csv` targets and what Starlight stamps into
  // <link rel="canonical"> and sitemap-0.xml. See specs phase_plans/phase_4.md.
  trailingSlash: 'always',
  build: { format: 'directory' },
  integrations: [
    // Both are post-build assertions about `dist` rather than build steps; see
    // scripts/build_integrations.mjs for what each one is defending against.
    markdownContentType(),
    optimizedImagesOnly(),
    starlight({
      title: 'Kiln AI',
      description: 'Rapid AI Prototyping and Dataset Collaboration Tool',
      customCss: ['./src/styles/custom.css'],
      head,
      social: [
        { icon: 'github', label: 'GitHub', href: 'https://github.com/Kiln-AI/Kiln' },
      ],
      // Starlight appends the page's path relative to this Astro project, not
      // the repo, so the base URL has to carry the `site/` segment itself.
      editLink: { baseUrl: 'https://github.com/Kiln-AI/docs/edit/main/site/' },
      components: {
        // Adds the visible llms.txt link. starlight-theme-black overrides Head,
        // Hero, MobileMenuToggle, PageTitle, Pagination, Sidebar, SiteTitle and
        // ThemeSelect, so Footer is free to take.
        Footer: './src/components/Footer.astro',
      },
      // Rewrites each page's raw markdown so the theme's "Copy page" blob
      // carries absolute image URLs. See the file for why this is not a
      // component override.
      routeMiddleware: './src/starlightRouteData.ts',
      plugins: [
        starlightThemeBlack({
          // Render sidebar groups as collapsible dropdowns rather than flat,
          // always-expanded sections. SUMMARY.md relies on expanding groups.
          sidebar: { useDropdowns: true },
          docs: {
            // The "Copy page" menu offers ChatGPT, v0, Claude and Scira by
            // default. Listed agents override the defaults, so this drops
            // Scira and leaves the other three.
            showMarkdownActions: { agents: { scira: false } },
          },
          navLinks: [
            { label: 'Docs', link: '/docs/quickstart/' },
            { label: 'Developers', link: '/developers/python-library-quickstart/' },
            { label: 'Download', link: 'https://kiln.tech' },
          ],
        }),
        // Replaces the llms.txt GitBook generated for us. Emits /llms.txt (an
        // index), /llms-full.txt and /llms-small.txt.
        starlightLlmsTxt({
          details: [
            'Kiln is a desktop app and Python library for fine-tuning, evals, synthetic data',
            'generation, and shipping AI systems. These docs cover both the app and the library.',
            '\n\nEvery page is also available as markdown at its own URL with a `.md` suffix,',
            'for example <https://docs.kiln.tech/docs/quickstart.md>.',
          ].join(' '),
          optionalLinks: [
            {
              label: 'Kiln on GitHub',
              url: 'https://github.com/Kiln-AI/Kiln',
              description: 'Source for the app and the Python library.',
            },
          ],
        }),
      ],
      sidebar,
    }),
  ],
});
