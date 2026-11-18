// @ts-check
import { readFileSync } from 'node:fs';
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import starlightThemeBlack from 'starlight-theme-black';

// Generated from SUMMARY.md by scripts/gitbook_to_starlight.py.
let sidebar;
try {
  sidebar = JSON.parse(readFileSync(new URL('./sidebar.json', import.meta.url), 'utf8'));
} catch {
  throw new Error('sidebar.json is missing. Run `npm run convert` first.');
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
      editLink: { baseUrl: 'https://github.com/Kiln-AI/docs/edit/main/' },
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
