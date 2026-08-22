// @ts-check
import { readFileSync } from 'node:fs';
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import starlightThemeBlack from 'starlight-theme-black';
import starlightThemeNova from 'starlight-theme-nova';

// Generated from SUMMARY.md by scripts/gitbook_to_starlight.py.
let sidebar;
try {
  sidebar = JSON.parse(readFileSync(new URL('./sidebar.json', import.meta.url), 'utf8'));
} catch {
  throw new Error('sidebar.json is missing. Run `npm run convert` first.');
}

/**
 * Pick the visual theme with the DOCS_THEME env var, e.g.
 *
 *   DOCS_THEME=nova npm run dev
 *   DOCS_THEME=none npm run build
 *
 * Defaults to `black`. Each entry lists the Starlight plugins and any extra CSS
 * that theme needs.
 */
const THEMES = {
  // shadcn-inspired: top nav bar, "Copy page" / open-in-LLM actions.
  black: {
    plugins: [
      starlightThemeBlack({
        navLinks: [
          { label: 'Docs', link: '/docs/quickstart/' },
          { label: 'Developers', link: '/developers/python-library-quickstart/' },
          { label: 'Download', link: 'https://kiln.tech' },
        ],
      }),
    ],
    css: ['./src/styles/theme-black-fixes.css'],
  },
  // A more polished take on stock Starlight; keeps collapsible sidebar groups.
  nova: { plugins: [starlightThemeNova()], css: [] },
  // Stock Starlight.
  none: { plugins: [], css: [] },
};

const name = process.env.DOCS_THEME ?? 'black';
const theme = THEMES[name];
if (!theme) {
  throw new Error(
    `Unknown DOCS_THEME "${name}". Valid values: ${Object.keys(THEMES).join(', ')}.`
  );
}

export default defineConfig({
  site: 'https://docs.kiln.tech',
  integrations: [
    starlight({
      title: 'Kiln AI',
      description: 'Rapid AI Prototyping and Dataset Collaboration Tool',
      customCss: ['./src/styles/custom.css', ...theme.css],
      social: [
        { icon: 'github', label: 'GitHub', href: 'https://github.com/Kiln-AI/Kiln' },
      ],
      editLink: { baseUrl: 'https://github.com/Kiln-AI/docs/edit/main/' },
      plugins: theme.plugins,
      sidebar,
    }),
  ],
});
