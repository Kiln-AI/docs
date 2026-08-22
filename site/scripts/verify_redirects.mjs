#!/usr/bin/env node
/**
 * Prove that every URL in `redirects.csv` still resolves.
 *
 * Every `old_path` and every distinct `new_path` must end at a real page:
 * checking the targets as well as the sources is what catches a redirect
 * pointing at nothing.
 *
 *   node scripts/verify_redirects.mjs --dist dist
 *       Offline. Rules come from `dist/_redirects`, and the destination is
 *       checked against the built files. No server needed.
 *
 *   node scripts/verify_redirects.mjs --base-url https://x.pages.dev
 *       Over HTTP, with the *server* doing the redirecting. This is the real
 *       gate, run against a Cloudflare preview and later production.
 *
 *   node scripts/verify_redirects.mjs --base-url http://localhost:4321 --dist dist
 *       Over HTTP against a server that does not implement `_redirects` — i.e.
 *       `astro preview`. Rules are applied locally first and only the resolved
 *       destination is fetched.
 */

import { readFile, access } from 'node:fs/promises';
import { argv, exit } from 'node:process';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const SITE_DIR = path.resolve(SCRIPT_DIR, '..');

const PERMANENT_STATUSES = new Set([301, 308]);
const TEMPORARY_STATUSES = new Set([302, 303, 307]);
const MAX_HOPS = 5;
const DEFAULT_CONCURRENCY = 6;

export class VerifyError extends Error {}

// --------------------------------------------------------------------------
// Inventory
// --------------------------------------------------------------------------

const CSV_HEADER = 'old_path,new_path,status,source';

/** Paths to check: every source and every distinct destination, deduped. */
export function parseInventory(csvText) {
  const lines = csvText
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith('#'));

  if (lines.shift() !== CSV_HEADER) {
    throw new VerifyError(`redirects.csv header must be ${CSV_HEADER}`);
  }

  const checks = new Map();
  for (const [index, line] of lines.entries()) {
    const fields = line.split(',').map((field) => field.trim());
    if (fields.length !== 4) {
      throw new VerifyError(`redirects.csv line ${index + 2}: expected 4 columns`);
    }
    const [oldPath, newPath, , source] = fields;
    if (!checks.has(oldPath)) checks.set(oldPath, source);
    if (!checks.has(newPath)) checks.set(newPath, 'target');
  }
  return [...checks].map(([urlPath, source]) => ({ path: urlPath, source }));
}

// --------------------------------------------------------------------------
// Local rule resolution
// --------------------------------------------------------------------------

/** Parse a Cloudflare Pages `_redirects` file into exact-match rules. */
export function parseRules(text) {
  const rules = new Map();
  for (const raw of text.split('\n')) {
    const line = raw.split('#')[0].trim();
    if (!line) continue;

    const [from, to, statusText] = line.split(/\s+/);
    if (!from || !to) {
      throw new VerifyError(`malformed redirect rule: ${raw.trim()}`);
    }
    // We emit only exact paths. A splat or placeholder appearing later should
    // stop this tool rather than let it quietly report a miss as a pass.
    if (/[*:]/.test(from)) {
      throw new VerifyError(
        `rule ${from} uses wildcard matching, which this verifier does not implement`,
      );
    }
    // Cloudflare defaults to 302 when a rule omits the status.
    rules.set(from, { to, status: statusText ? Number(statusText) : 302 });
  }
  return rules;
}

/** Follow local rules to the path that should actually be served. */
export function resolvePath(startPath, rules) {
  const hops = [];
  let current = startPath;
  const seen = new Set([current]);

  while (rules.has(current)) {
    const { to, status } = rules.get(current);
    hops.push({ from: current, to, status });
    if (seen.has(to)) {
      throw new VerifyError(`redirect loop: ${[...seen, to].join(' -> ')}`);
    }
    if (hops.length > MAX_HOPS) {
      throw new VerifyError(`more than ${MAX_HOPS} redirect hops from ${startPath}`);
    }
    seen.add(to);
    current = to;
  }
  return { path: current, hops };
}

// --------------------------------------------------------------------------
// Oracles
// --------------------------------------------------------------------------

function distCandidates(urlPath) {
  const relative = urlPath.replace(/^\//, '');
  if (urlPath.endsWith('/')) return [`${relative}index.html`];
  return [`${relative}/index.html`, `${relative}.html`, relative];
}

async function existsInDist(distDir, urlPath) {
  for (const candidate of distCandidates(urlPath)) {
    try {
      await access(path.join(distDir, candidate));
      return true;
    } catch {
      /* try the next spelling */
    }
  }
  return false;
}

/** Walk the server's own redirects to a final status. */
async function fetchChain(baseUrl, urlPath, fetchImpl) {
  const hops = [];
  let current = urlPath;

  for (let hop = 0; hop <= MAX_HOPS; hop += 1) {
    const response = await fetchImpl(new URL(current, baseUrl), { redirect: 'manual' });
    if (response.status < 300 || response.status >= 400) {
      return { status: response.status, hops };
    }
    const location = response.headers.get('location');
    if (!location) {
      throw new VerifyError(`${current} returned ${response.status} with no Location`);
    }
    const next = new URL(location, new URL(current, baseUrl));
    hops.push({ from: current, to: next.pathname, status: response.status });
    current = next.pathname + next.search;
  }
  throw new VerifyError(`more than ${MAX_HOPS} redirect hops from ${urlPath}`);
}

// --------------------------------------------------------------------------
// Checking
// --------------------------------------------------------------------------

export function describeFailure({ hops, status }, { allowTemporary }) {
  const temporary = hops.filter(
    (hop) => !PERMANENT_STATUSES.has(hop.status) && TEMPORARY_STATUSES.has(hop.status),
  );
  if (temporary.length && !allowTemporary) {
    const shown = temporary.map((hop) => `${hop.from} -> ${hop.to} (${hop.status})`);
    return `temporary redirect, expected 301: ${shown.join(', ')}`;
  }
  const unexpected = hops.find(
    (hop) => !PERMANENT_STATUSES.has(hop.status) && !TEMPORARY_STATUSES.has(hop.status),
  );
  if (unexpected) {
    return `unexpected redirect status ${unexpected.status} on ${unexpected.from}`;
  }
  if (status !== undefined && status !== 200) {
    return `final response was ${status}`;
  }
  return null;
}

async function checkOne(check, options) {
  const { rules, distDir, baseUrl, allowTemporary, fetchImpl } = options;

  let start = check.path;
  let hops = [];
  if (rules) {
    const resolved = resolvePath(check.path, rules);
    start = resolved.path;
    hops = resolved.hops;
  }

  if (baseUrl) {
    const result = await fetchChain(baseUrl, start, fetchImpl);
    const allHops = [...hops, ...result.hops];
    const failure = describeFailure(
      { hops: allHops, status: result.status },
      { allowTemporary },
    );
    return { ...check, resolvedTo: start, hops: allHops, failure };
  }

  const failure = describeFailure({ hops }, { allowTemporary })
    ?? ((await existsInDist(distDir, start))
      ? null
      : `no file in ${path.relative(SITE_DIR, distDir) || distDir} for ${start}`);
  return { ...check, resolvedTo: start, hops, failure };
}

async function mapWithConcurrency(items, limit, worker) {
  const results = new Array(items.length);
  let next = 0;
  const runners = Array.from({ length: Math.min(limit, items.length) }, async () => {
    while (next < items.length) {
      const index = next;
      next += 1;
      results[index] = await worker(items[index]);
    }
  });
  await Promise.all(runners);
  return results;
}

export async function verify(options) {
  const csvText = await readFile(options.csvPath, 'utf8');
  const checks = parseInventory(csvText);

  const rules = options.distDir
    ? parseRules(await readFile(path.join(options.distDir, '_redirects'), 'utf8'))
    : null;

  const results = await mapWithConcurrency(
    checks,
    options.concurrency ?? DEFAULT_CONCURRENCY,
    (check) => checkOne(check, { ...options, rules, fetchImpl: options.fetchImpl ?? fetch }),
  );

  return {
    results,
    failures: results.filter((result) => result.failure),
    locallyResolved: results.filter((result) => result.hops.length && rules).length,
  };
}

// --------------------------------------------------------------------------
// CLI
// --------------------------------------------------------------------------

export function parseArgs(args) {
  const options = {
    csvPath: path.join(SITE_DIR, 'redirects.csv'),
    distDir: null,
    baseUrl: null,
    allowTemporary: false,
    concurrency: DEFAULT_CONCURRENCY,
  };

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    const value = () => {
      const next = args[index + 1];
      if (next === undefined) throw new VerifyError(`${arg} needs a value`);
      index += 1;
      return next;
    };
    switch (arg) {
      case '--dist': options.distDir = path.resolve(value()); break;
      case '--base-url': options.baseUrl = value(); break;
      case '--csv': options.csvPath = path.resolve(value()); break;
      case '--concurrency': options.concurrency = Number(value()); break;
      case '--allow-temporary': options.allowTemporary = true; break;
      default: throw new VerifyError(`unknown argument: ${arg}`);
    }
  }

  if (!options.distDir && !options.baseUrl) {
    throw new VerifyError('pass --dist DIR, --base-url URL, or both');
  }
  return options;
}

async function main(args) {
  let options;
  try {
    options = parseArgs(args);
  } catch (error) {
    console.error(`error: ${error.message}`);
    return 2;
  }

  let report;
  try {
    report = await verify(options);
  } catch (error) {
    console.error(`error: ${error.message}`);
    return 2;
  }

  const mode = options.baseUrl
    ? `${options.baseUrl}${options.distDir ? ' (rules applied locally)' : ' (server-side redirects)'}`
    : `${options.distDir} (offline)`;
  console.log(`checked ${report.results.length} paths against ${mode}`);
  if (options.distDir) {
    console.log(`  ${report.locallyResolved} resolved through local _redirects rules`);
  }

  if (report.failures.length === 0) {
    console.log('all paths resolve');
    return 0;
  }

  console.error(`\n${report.failures.length} failing paths:`);
  for (const failure of report.failures) {
    console.error(`  ${failure.path} [${failure.source}] - ${failure.failure}`);
  }
  return 1;
}

if (import.meta.url === pathToFileURL(argv[1] ?? '').href) {
  exit(await main(argv.slice(2)));
}
