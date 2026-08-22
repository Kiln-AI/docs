#!/usr/bin/env node
/**
 * Audit every built page for defects that can be detected without a baseline.
 *
 * Phase 1 of the migration was meant to capture the live GitBook site — its
 * rendered text and a screenshot of every page — so that per-page QA could be
 * a diff. That capture never ran here: egress to `docs.kiln.tech` is blocked.
 * This is the substitute, and it answers a different question. A diff asks
 * "does this page still say and show what GitBook did"; this asks "is anything
 * on this page detectably wrong". The second is weaker, and it is mechanical,
 * repeatable and honest about its limits — see `specs/.../phase_plans/phase_7.md`.
 *
 * Two halves:
 *
 *   node scripts/qa_pages.mjs
 *       Static. Scans the content sources for GitBook markup that survived the
 *       conversion and now means nothing. No browser, no server.
 *
 *   node scripts/qa_pages.mjs --browser
 *       The above, plus a real Chromium render of every page in `dist` at a
 *       desktop and a mobile viewport: horizontal overflow, images that did
 *       not load, markup being displayed instead of interpreted, empty table
 *       columns, console errors, missing title/description.
 *
 *   node scripts/qa_pages.mjs --browser --base-url https://x.pages.dev
 *       Same checks against a deployment rather than a local `dist`. The page
 *       list still comes from `dist`, so build first.
 *
 * Playwright is deliberately not a dependency of this project: it is large, it
 * carries a browser download, and CI already gates the things that must never
 * regress (build, links, anchors, redirects). `--browser` resolves it from
 * wherever it is installed and says so plainly when it is not there.
 *
 * What this cannot catch, stated because it is the whole reason the phase plan
 * exists: content GitBook rendered that the markdown never contained, and
 * whether a defect-free page is nonetheless a visual regression. Only the
 * baseline answers those.
 */

import { createRequire } from 'node:module';
import { createServer } from 'node:http';
import { readdir, readFile, stat } from 'node:fs/promises';
import path from 'node:path';
import { argv, exit } from 'node:process';
import { fileURLToPath } from 'node:url';

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const SITE_DIR = path.resolve(SCRIPT_DIR, '..');

const VIEWPORTS = [
	{ name: 'desktop', width: 1280, height: 900 },
	{ name: 'mobile', width: 375, height: 780 },
];

export class QaError extends Error {}

// --------------------------------------------------------------------------
// Static: GitBook markup that outlived GitBook
// --------------------------------------------------------------------------

/**
 * Attributes and URLs that meant something to GitBook and nothing to Starlight.
 *
 * An inert attribute that looks like a feature is worse than no attribute: it
 * reads as intent and invites the next person to implement it. Each of these
 * was either honoured by a real component or deleted in phase 7, and this is
 * what stops them coming back.
 */
const RESIDUAL_MARKUP = [
	{
		check: 'gitbook-card-table',
		pattern: /data-view="cards"|data-card-cover|data-card-target/g,
		message: "GitBook's card-table widget. Starlight renders it as a plain table — use src/components/CoverCard.astro.",
	},
	{
		check: 'gitbook-hidden-column',
		pattern: /\bdata-hidden\b/g,
		message: 'GitBook hid this column; Starlight shows it as an empty one. Delete the column.',
	},
	{
		check: 'gitbook-inert-attribute',
		pattern: /data-full-width="[^"]*"|data-search="[^"]*"/g,
		message: 'Inert GitBook rendering hint. Starlight has no equivalent; delete it rather than leaving it to look like a feature.',
	},
	{
		check: 'gitbook-private-url',
		pattern: /https?:\/\/app\.gitbook\.com\/[^\s)"'<]*/g,
		message: 'A private GitBook URL. It dies with the subscription.',
	},
	{
		check: 'gitbook-asset-path',
		pattern: /\.gitbook\/assets\//g,
		message: 'The GitBook asset tree was deleted in phase 3. Images live in src/assets/, videos in public/assets/.',
	},
];

/** Character ranges of fenced code blocks, so examples are not scanned. */
function codeRegions(source) {
	const regions = [];
	let open = null;
	let offset = 0;
	for (const line of source.split('\n')) {
		const fence = /^\s{0,3}(`{3,}|~{3,})/.exec(line);
		if (fence && open === null) {
			open = { char: fence[1][0], length: fence[1].length, start: offset };
		} else if (fence && open !== null && fence[1][0] === open.char && fence[1].length >= open.length) {
			regions.push([open.start, offset + line.length]);
			open = null;
		}
		offset += line.length + 1;
	}
	if (open !== null) regions.push([open.start, source.length]);
	return regions;
}

function insideCode(regions, index) {
	return regions.some(([start, end]) => index >= start && index < end);
}

/**
 * GitBook markup left in one page's source.
 *
 * @param {string} source raw markdown or MDX
 * @returns {{check: string, message: string, detail: string}[]}
 */
export function residualGitbookMarkup(source) {
	const regions = codeRegions(source);
	const findings = [];
	for (const { check, pattern, message } of RESIDUAL_MARKUP) {
		const seen = new Set();
		for (const match of source.matchAll(new RegExp(pattern.source, pattern.flags))) {
			// A page documenting GitBook markup in an example is not a defect —
			// the same rule the converter learned about link rewriting.
			if (insideCode(regions, match.index)) continue;
			if (seen.has(match[0])) continue;
			seen.add(match[0]);
			findings.push({ check, message, detail: match[0] });
		}
	}
	return findings;
}

// --------------------------------------------------------------------------
// Rendered: markup being displayed instead of interpreted
// --------------------------------------------------------------------------

/**
 * The failure mode nothing else on this site catches.
 *
 * Markdown that degrades to text raises no error anywhere: the build stays
 * green, the counts match, and `starlight-links-validator` is silent precisely
 * *because* the link stopped being a link. Phase 3 documented it for
 * raw-space image references; phase 7 found it again as a `<figure>` indented
 * inside a list item, which took two list items and a link down with it.
 *
 * Scanned text has already had code blocks and code spans removed by the
 * caller, so anything matching here is being shown to a reader as prose.
 */
const LITERAL_MARKUP = [
	{
		check: 'unrendered-html',
		// Only the block-level tags this corpus uses as real markup. Deliberately
		// not a generic `<\w+>`: prose says "a > b" and "N<50" often enough.
		pattern: /<\/?(?:figure|figcaption|table|thead|tbody|tr|td|th|details|summary|img|iframe|video)\b[^>]*>/gi,
		message: 'HTML tag shown as text. It is inside something CommonMark read as a paragraph or a code block.',
	},
	{
		check: 'unrendered-image',
		pattern: /!\[[^\]\n]*\]\([^)\n]+\)/g,
		message: 'Markdown image shown as text — usually a raw space in the destination, which CommonMark does not accept.',
	},
	{
		check: 'unrendered-link',
		pattern: /(?<!!)\[[^\]\n]+\]\((?:\/|\.{1,2}\/|https?:|#)[^)\n]*\)/g,
		message: 'Markdown link shown as text.',
	},
	{
		check: 'gitbook-directive',
		pattern: /\{%[^%]*%\}/g,
		message: 'An unconverted GitBook directive.',
	},
];

/**
 * Markup that a reader can see as text.
 *
 * @param {string} text rendered prose, with code blocks and code spans removed
 * @returns {{check: string, message: string, detail: string}[]}
 */
export function literalMarkupInText(text) {
	const findings = [];
	for (const { check, pattern, message } of LITERAL_MARKUP) {
		const seen = new Set();
		for (const match of text.matchAll(new RegExp(pattern.source, pattern.flags))) {
			if (seen.has(match[0])) continue;
			seen.add(match[0]);
			findings.push({ check, message, detail: match[0].slice(0, 120) });
		}
	}
	return findings;
}

// --------------------------------------------------------------------------
// Rendered: table columns with nothing in them
// --------------------------------------------------------------------------

/**
 * Indices of columns where every cell — header included — is empty.
 *
 * GitBook's `data-hidden` columns look like this once Starlight stops honouring
 * the attribute. Emptiness is text *and* media, and a column whose header is
 * blank but whose cells are full is the label column of every comparison table
 * in this corpus, so both halves matter.
 *
 * @param {{text: string, media: boolean}[][]} rows every row, header row first
 * @returns {number[]}
 */
export function emptyTableColumns(rows) {
	const width = Math.max(0, ...rows.map((row) => row.length));
	const empty = [];
	for (let column = 0; column < width; column++) {
		const cells = rows.map((row) => row[column]).filter((cell) => cell !== undefined);
		// A ragged table's missing cells are absent, not empty; a column that
		// exists nowhere is not a finding.
		if (cells.length === 0) continue;
		if (cells.every((cell) => !cell.text.trim() && !cell.media)) empty.push(column);
	}
	return empty;
}

// --------------------------------------------------------------------------
// Judgement over one page's observation
// --------------------------------------------------------------------------

/** Is this URL served by somewhere other than the site under test? */
export function isExternal(url, origin) {
	if (!url) return false;
	if (url.startsWith('/') || url.startsWith('#')) return false;
	return !url.startsWith(origin);
}

/**
 * Everything wrong with one page.
 *
 * Takes a plain object rather than a `Page` so that every judgement is
 * testable without a browser, and so the `page.evaluate` payload stays a dumb
 * collector of facts.
 *
 * @param {object} observation see `observePage`
 * @returns {{check: string, message: string, detail?: string}[]}
 */
export function pageFindings(observation) {
	const findings = [];
	const add = (check, message, detail) => findings.push({ check, message, detail });

	if (!observation.title) add('missing-title', 'Page has no <title>.');
	if (!observation.description) {
		add('missing-description', 'Page has no <meta name="description">.');
	}

	if (observation.scrollWidth > observation.clientWidth + 1) {
		// Only elements nothing clips: a code block or a wide table that scrolls
		// inside its own box is correct behaviour, and reporting those buries
		// the real finding under every page that contains one.
		const offenders = observation.wideElements.filter((element) => !element.clipped);
		add(
			'horizontal-overflow',
			`Page scrolls sideways: ${observation.scrollWidth}px of content in ` +
				`${observation.clientWidth}px of viewport.`,
			offenders.map((element) => `${element.selector} (right edge ${element.right}px)`).join(', ') ||
				'no unclipped element found',
		);
	}

	for (const image of observation.images) {
		if (image.loaded) continue;
		if (image.external) {
			// This environment has no egress. An unreachable badge is not
			// evidence of a defect, and a check that cries wolf gets ignored.
			add('external-image-unverified', 'External image could not be loaded from here.', image.src);
		} else {
			add('broken-image', 'Image did not load.', image.src);
		}
	}

	for (const finding of literalMarkupInText(observation.proseText)) findings.push(finding);

	for (const table of observation.tables) {
		for (const column of emptyTableColumns(table)) {
			add('empty-table-column', `Table column ${column} is empty in every row.`);
		}
	}

	for (const error of observation.consoleErrors) {
		if (error.external) continue;
		add('console-error', error.text, error.url);
	}
	for (const error of observation.pageErrors) add('page-error', error);

	return findings;
}

/** Findings that are notes rather than failures. */
const ADVISORY_CHECKS = new Set(['external-image-unverified']);

export function isAdvisory(finding) {
	return ADVISORY_CHECKS.has(finding.check);
}

// --------------------------------------------------------------------------
// Collecting the facts
// --------------------------------------------------------------------------

/**
 * Read one rendered page.
 *
 * Runs inside the browser, so it may only return structured-cloneable data.
 * Every judgement about what it returns lives in `pageFindings`.
 */
/* c8 ignore start -- runs in the browser, covered by the corpus run */
function observeInPage() {
	const root = document.documentElement;
	const clientWidth = root.clientWidth;

	const describe = (element) => {
		const id = element.id ? `#${element.id}` : '';
		const cls = typeof element.className === 'string' && element.className
			? `.${element.className.trim().split(/\s+/).slice(0, 2).join('.')}`
			: '';
		return `${element.tagName.toLowerCase()}${id}${cls}`;
	};

	const wideElements = [];
	for (const element of document.querySelectorAll('body *')) {
		const box = element.getBoundingClientRect();
		if (box.width === 0 || (box.right <= clientWidth + 1 && box.left >= -1)) continue;
		let clipped = false;
		for (let parent = element.parentElement; parent; parent = parent.parentElement) {
			const overflowX = getComputedStyle(parent).overflowX;
			if (overflowX === 'auto' || overflowX === 'scroll' || overflowX === 'hidden') {
				clipped = true;
				break;
			}
		}
		wideElements.push({
			selector: describe(element),
			right: Math.round(box.right),
			left: Math.round(box.left),
			clipped,
		});
	}

	const images = [...document.images].map((image) => ({
		src: image.currentSrc || image.src,
		loaded: image.complete && image.naturalWidth > 0,
	}));

	// Code is excluded before the text is scanned: a page documenting markdown
	// is not a page displaying broken markdown.
	const prose = document.querySelector('.sl-markdown-content');
	let proseText = '';
	if (prose) {
		const copy = prose.cloneNode(true);
		for (const node of copy.querySelectorAll('pre, code, kbd, samp, script, style, button')) {
			node.remove();
		}
		proseText = copy.textContent ?? '';
	}

	const tables = [...document.querySelectorAll('.sl-markdown-content table')].map((table) =>
		[...table.rows].map((row) =>
			[...row.cells].map((cell) => ({
				text: cell.textContent ?? '',
				media: cell.querySelector('img, svg, video, picture') !== null,
			})),
		),
	);

	return {
		scrollWidth: root.scrollWidth,
		clientWidth,
		wideElements,
		images,
		proseText,
		tables,
		title: document.title,
		description: document.querySelector('meta[name="description"]')?.content ?? '',
	};
}
/* c8 ignore stop */

/** Load one page and return everything `pageFindings` needs to judge it. */
async function observePage(page, url, origin) {
	const consoleErrors = [];
	const pageErrors = [];
	page.on('console', (message) => {
		if (message.type() !== 'error') return;
		const location = message.location()?.url ?? '';
		consoleErrors.push({
			text: message.text(),
			url: location,
			external: isExternal(location, origin),
		});
	});
	page.on('pageerror', (error) => pageErrors.push(error.message));

	await page.goto(url, { waitUntil: 'load' });

	// Every screenshot on this site is lazy-loaded, so without this the first
	// pass reports every image below the fold as broken. Force them eager and
	// wait, rather than scrolling and hoping.
	await page.evaluate(() => {
		for (const image of document.images) image.loading = 'eager';
	});
	await page.evaluate(
		() =>
			Promise.all(
				[...document.images].map((image) =>
					image.complete
						? null
						: new Promise((resolve) => {
								image.addEventListener('load', resolve, { once: true });
								image.addEventListener('error', resolve, { once: true });
							}),
				),
			),
	);

	const observation = await page.evaluate(observeInPage);
	return {
		...observation,
		images: observation.images.map((image) => ({
			...image,
			external: isExternal(image.src, origin),
		})),
		consoleErrors,
		pageErrors,
	};
}

// --------------------------------------------------------------------------
// Walking the build
// --------------------------------------------------------------------------

/** Every page path in a built site, as a URL path. */
async function builtPages(distDir, prefix = '/') {
	const found = [];
	for (const entry of await readdir(path.join(distDir, prefix), { withFileTypes: true })) {
		if (entry.name.startsWith('_') || entry.name === 'pagefind') continue;
		if (entry.isDirectory()) found.push(...(await builtPages(distDir, `${prefix}${entry.name}/`)));
		else if (entry.name === 'index.html') found.push(prefix);
	}
	return found.sort();
}

/** Every content source file, as a path relative to the content directory. */
async function contentFiles(contentDir, prefix = '') {
	const found = [];
	for (const entry of await readdir(path.join(contentDir, prefix), { withFileTypes: true })) {
		if (entry.isDirectory()) found.push(...(await contentFiles(contentDir, `${prefix}${entry.name}/`)));
		else if (/\.mdx?$/.test(entry.name)) found.push(`${prefix}${entry.name}`);
	}
	return found.sort();
}

const CONTENT_TYPES = {
	'.html': 'text/html; charset=utf-8',
	'.css': 'text/css',
	'.js': 'text/javascript',
	'.json': 'application/json',
	'.svg': 'image/svg+xml',
	'.png': 'image/png',
	'.webp': 'image/webp',
	'.jpg': 'image/jpeg',
	'.mp4': 'video/mp4',
	'.woff2': 'font/woff2',
	'.txt': 'text/plain; charset=utf-8',
	'.xml': 'application/xml',
	'.md': 'text/markdown; charset=utf-8',
};

/**
 * Serve `dist` well enough to render it.
 *
 * Range requests are answered because `<video>` asks for one, and a video that
 * cannot start looks exactly like a video that is missing.
 */
async function serveDist(distDir) {
	const server = createServer((request, response) => {
		void (async () => {
			const urlPath = decodeURIComponent((request.url ?? '/').split('?')[0]);
			let file = path.join(distDir, urlPath);
			const info = await stat(file).catch(() => null);
			if (info?.isDirectory()) file = path.join(file, 'index.html');
			const body = await readFile(file).catch(() => null);
			if (body === null) {
				response.writeHead(404, { 'Content-Type': 'text/html' });
				response.end('<h1>404</h1>');
				return;
			}
			const type = CONTENT_TYPES[path.extname(file)] ?? 'application/octet-stream';
			const range = /^bytes=(\d*)-(\d*)$/.exec(request.headers.range ?? '');
			if (range) {
				const start = range[1] ? Number(range[1]) : 0;
				const end = range[2] ? Number(range[2]) : body.length - 1;
				response.writeHead(206, {
					'Content-Type': type,
					'Content-Range': `bytes ${start}-${end}/${body.length}`,
					'Accept-Ranges': 'bytes',
				});
				response.end(body.subarray(start, end + 1));
				return;
			}
			response.writeHead(200, { 'Content-Type': type, 'Accept-Ranges': 'bytes' });
			response.end(body);
		})();
	});
	await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
	const { port } = /** @type {import('node:net').AddressInfo} */ (server.address());
	return { server, origin: `http://127.0.0.1:${port}` };
}

/**
 * Playwright, from wherever it happens to be installed.
 *
 * Not a dependency of this project on purpose — see the module docstring — so
 * the absence of it is a message, not a stack trace.
 */
function loadPlaywright() {
	try {
		return createRequire(path.join(SITE_DIR, 'noop.cjs'))('playwright');
	} catch (cause) {
		throw new QaError(
			'--browser needs Playwright, which is not installed. The static checks ran; the ' +
				'layout checks did not. Install it from `site/` with `npm install --no-save ' +
				'playwright && npx playwright install chromium` — the first command is the one ' +
				'this resolves, the second downloads the browser it drives — or drop --browser.',
			{ cause },
		);
	}
}

// --------------------------------------------------------------------------
// CLI
// --------------------------------------------------------------------------

export function parseArgs(args) {
	const options = { dist: 'dist', content: 'src/content/docs', browser: false, baseUrl: null };
	for (let index = 0; index < args.length; index++) {
		const arg = args[index];
		const value = () => {
			const next = args[++index];
			if (next === undefined) throw new QaError(`${arg} needs a value`);
			return next;
		};
		if (arg === '--browser') options.browser = true;
		else if (arg === '--dist') options.dist = value();
		else if (arg === '--content') options.content = value();
		else if (arg === '--base-url') options.baseUrl = value().replace(/\/$/, '');
		else if (arg.startsWith('--') && arg.includes('=')) {
			const split = arg.indexOf('=');
			args.splice(index--, 1, arg.slice(0, split), arg.slice(split + 1));
		} else throw new QaError(`unknown argument: ${arg}`);
	}
	return options;
}

/**
 * The browser half: render every built page at each viewport and judge it.
 *
 * Separate from `main` so that the one thing that can stop it before it starts
 * — Playwright not being installed — is catchable without also swallowing the
 * static findings.
 */
async function sweepInBrowser(options, distDir, record) {
	const { chromium } = loadPlaywright();
	const local = options.baseUrl ? null : await serveDist(distDir);
	try {
		const origin = options.baseUrl ?? local.origin;
		const pages = await builtPages(distDir);
		const browser = await chromium.launch();
		try {
			for (const viewport of VIEWPORTS) {
				const context = await browser.newContext({
					viewport: { width: viewport.width, height: viewport.height },
				});
				for (const urlPath of pages) {
					const page = await context.newPage();
					const observation = await observePage(page, origin + urlPath, origin);
					for (const finding of pageFindings(observation)) {
						record(`${viewport.name} ${urlPath}`, finding);
					}
					await page.close();
				}
				await context.close();
			}
		} finally {
			await browser.close();
		}
		console.log(`rendered ${pages.length} pages at ${VIEWPORTS.map((v) => `${v.width}px`).join(' and ')}`);
	} finally {
		local?.server.close();
	}
}

async function main(args) {
	const options = parseArgs(args);
	const contentDir = path.resolve(SITE_DIR, options.content);
	const distDir = path.resolve(SITE_DIR, options.dist);

	/** @type {{where: string, check: string, message: string, detail?: string}[]} */
	const failures = [];
	const notes = [];
	const record = (where, finding) => {
		(isAdvisory(finding) ? notes : failures).push({ where, ...finding });
	};

	let pageCount = 0;
	for (const file of await contentFiles(contentDir)) {
		pageCount++;
		const source = await readFile(path.join(contentDir, file), 'utf8');
		for (const finding of residualGitbookMarkup(source)) record(file, finding);
	}
	console.log(`scanned ${pageCount} content files for residual GitBook markup`);

	/**
	 * Why the browser half stopped, if it did.
	 *
	 * Held rather than thrown, and held for *any* failure — Playwright missing,
	 * its Chromium binary missing, `dist` unservable, a page that will not load.
	 * Throwing would discard the static findings already collected, and for a
	 * tool whose whole thesis is that markup which degrades quietly raises no
	 * error anywhere, silently dropping its own results is the one failure mode
	 * it cannot have. Narrowing this to `QaError` would leave the common case —
	 * an installed Playwright with no browser downloaded — swallowing them again.
	 */
	let incomplete = null;
	if (options.browser) {
		try {
			await sweepInBrowser(options, distDir, record);
		} catch (error) {
			incomplete = error;
		}
	}

	const print = (label, items) => {
		if (items.length === 0) return;
		console.log(`\n${label}`);
		for (const item of items) {
			console.log(`  ${item.where}\n    [${item.check}] ${item.message}`);
			if (item.detail) console.log(`      ${item.detail}`);
		}
	};

	print(`${notes.length} note(s), not failures:`, notes);
	print(`${failures.length} finding(s):`, failures);

	// 1: the sweep ran and found something. 2: the sweep could not finish, so a
	// clean report means nothing — anything it did find is printed above first.
	if (incomplete) {
		// A QaError is a message written for this situation; anything else is a
		// surprise, and a surprise needs its stack.
		console.error(`\n${incomplete instanceof QaError ? incomplete.message : `--browser could not finish: ${incomplete?.stack ?? incomplete}`}`);
		return 2;
	}
	if (failures.length > 0) return 1;
	console.log('\nno findings');
	return 0;
}

/* c8 ignore start */
if (import.meta.url === `file://${process.argv[1]}`) {
	main(argv.slice(2))
		.then(exit)
		.catch((error) => {
			console.error(error instanceof QaError ? error.message : error);
			exit(2);
		});
}
/* c8 ignore stop */
