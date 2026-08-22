// @ts-check
import { readFileSync } from 'node:fs';
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

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
      sidebar,
    }),
  ],
});
