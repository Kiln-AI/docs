#!/usr/bin/env node
/**
 * Build the one static social-preview image, `public/og.png`.
 *
 * The architecture calls for a single OG image shared by every page rather than
 * per-page generation, so this is a tool you run deliberately, not a build
 * step: the PNG is committed and `astro build` never touches it. Text is
 * rasterised through whatever fonts the machine has, so regenerating elsewhere
 * will not be byte-identical — rerun it only when the wording or design
 * changes.
 *
 *   npm run og
 *
 * Like `public/favicon.svg`, the typography here stands in for a real brand
 * asset. There is no Kiln logo in this repo to use.
 */

import { writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import sharp from 'sharp';

const SITE_DIR = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const OUTPUT = path.join(SITE_DIR, 'public', 'og.png');

// The canonical Open Graph card size. Also declared in `astro.config.mjs` as
// og:image:width / og:image:height, so change both together.
export const WIDTH = 1200;
export const HEIGHT = 630;

const TITLE = 'Kiln AI';
const TAGLINE = 'Rapid AI Prototyping and Dataset Collaboration Tool';
const DOMAIN = 'docs.kiln.tech';

// Matches the theme: neutral-950 ground, neutral-50 text, gray-4 for secondary
// text, and the accent from src/styles/custom.css.
const BACKGROUND = '#0a0a0a';
const FOREGROUND = '#fafafa';
const MUTED = '#a1a1aa';
const ACCENT = '#6d5ef8';

const SANS = 'Inter, Liberation Sans, DejaVu Sans, Helvetica, Arial, sans-serif';

export function ogImageSvg() {
	return `<svg xmlns="http://www.w3.org/2000/svg" width="${WIDTH}" height="${HEIGHT}" viewBox="0 0 ${WIDTH} ${HEIGHT}">
  <rect width="${WIDTH}" height="${HEIGHT}" fill="${BACKGROUND}"/>
  <rect x="0" y="0" width="${WIDTH}" height="8" fill="${ACCENT}"/>
  <rect x="96" y="150" width="96" height="96" rx="22" fill="${ACCENT}"/>
  <path d="M123 172h12v20l18-20h15l-22 24 23 26h-16l-18-20v20h-12z" fill="#ffffff"/>
  <text x="96" y="360" font-family="${SANS}" font-size="104" font-weight="700" fill="${FOREGROUND}">${TITLE}</text>
  <text x="96" y="434" font-family="${SANS}" font-size="38" font-weight="400" fill="${MUTED}">${TAGLINE}</text>
  <rect x="96" y="486" width="88" height="4" rx="2" fill="${ACCENT}"/>
  <text x="96" y="546" font-family="${SANS}" font-size="30" font-weight="500" fill="${MUTED}">${DOMAIN}</text>
</svg>`;
}

export async function renderOgImage() {
	return sharp(Buffer.from(ogImageSvg())).png({ compressionLevel: 9 }).toBuffer();
}

if (import.meta.url === `file://${process.argv[1]}`) {
	const png = await renderOgImage();
	await writeFile(OUTPUT, png);
	console.log(`wrote ${path.relative(SITE_DIR, OUTPUT)} (${WIDTH}x${HEIGHT}, ${png.length} bytes)`);
}
