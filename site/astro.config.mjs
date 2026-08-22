// @ts-check
import { readFileSync } from 'node:fs';
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import starlightThemeBlack from 'starlight-theme-black';

// Committed content, kept out of this file so the config stays readable.
// Originally generated from GitBook's SUMMARY.md; edited by hand since.
let sidebar;
try {
  sidebar = JSON.parse(readFileSync(new URL('./sidebar.json', import.meta.url), 'utf8'));
} catch (cause) {
  throw new Error('site/sidebar.json could not be read.', { cause });
}

export default defineConfig({
  site: 'https://docs.kiln.tech',
  integrations: [
    starlight({
      title: 'Kiln AI',
      description: 'Rapid AI Prototyping and Dataset Collaboration Tool',
      customCss: ['./src/styles/custom.css'],
      social: [
        { icon: 'github', label: 'GitHub', href: 'https://github.com/Kiln-AI/Kiln' },
      ],
      // Starlight appends the page's path relative to this Astro project, not
      // the repo, so the base URL has to carry the `site/` segment itself.
      editLink: { baseUrl: 'https://github.com/Kiln-AI/docs/edit/main/site/' },
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
      ],
      sidebar,
    }),
  ],
});
