---
status: draft
---

# Phase 5: Feature Parity

## Overview

Phases 2–4 moved the content and preserved the URLs. What is still missing is
everything GitBook gave us that is *not* a page: `llms.txt`, per-page markdown,
social preview images, analytics, a favicon, `robots.txt`, and a `/sitemap.xml`
that answers. This phase closes that list, and clears the recorded findings
from phases 2–4 that were explicitly assigned here.

The work splits into five groups:

1. **Machine-readable content** — `starlight-llms-txt`, per-page `.md`
   endpoints, and one shared asset-URL rewriter so all three of them (plus the
   theme's "Copy page" blob) emit URLs an external consumer can actually
   fetch.
2. **Site chrome** — favicon, static OG image, Cloudflare Web Analytics, a
   visible link to `llms.txt`.
3. **Root files** — `robots.txt`, and a `/sitemap.xml` that resolves.
4. **Inherited content fixes** — descriptions for the two pages that have
   none.
5. **Redirect machinery** — the `validate_targets` widening phase 4 asked for,
   and the new inventory rows.

### What needs a human, and exactly what they must do

Two things cannot be finished in this session. Both are wired so that
finishing them is a one-line change, and both are listed in
`site/README.md` under "Still to do" as well as here.

| Item | What is done | What a human must do |
| --- | --- | --- |
| Cloudflare Web Analytics | The beacon `<script>` is built from `CLOUDFLARE_ANALYTICS_TOKEN` and injected through Starlight's `head` config. With no token the tag is not emitted, so nothing ships broken. | Create a Web Analytics site for `docs.kiln.tech` in the Cloudflare dashboard, copy its token, and set `CLOUDFLARE_ANALYTICS_TOKEN` as a Pages build environment variable (or paste it into the fallback constant at the top of `astro.config.mjs`). |
| Brand assets | `public/favicon.svg` and `public/og.png` exist, are wired up, and are visually consistent with the theme. They are typographic placeholders built from the site's own palette, not the Kiln brand mark — there is no Kiln logo anywhere in this repo or its history to derive one from. | Drop in the real logo. `favicon.svg` is a hand-editable file; `og.png` is regenerated with `npm run og`. |

The favicon is the one place where "do nothing" was not an option: Starlight
emits `<link rel="shortcut icon" href="/favicon.svg">` on every page whether
or not the file exists, so the choice was between a placeholder and a 404 on
all 47 pages.

## Findings that shape the plan

### GitBook's `.md` URLs: emit them, do not redirect them

The scope item is "check whether GitBook's per-page `.md` URLs need redirect
rules". Egress to `docs.kiln.tech` is blocked, so this is settled from
evidence already in the repo. Separating what is known from what is inferred:

**Fact.** `project_overview.md` records, as an audit finding, that "GitBook
also serves a markdown version of every page". The `.md` URL family exists.

**Fact.** `ref/legacy_sitemap.xml` has 46 `<loc>` entries and **zero** contain
`.md`. GitBook does not advertise these URLs to search engines, so the
inbound-link and indexed-URL risk that drives the rest of phase 4 is low here.

**Fact.** Nothing in the converted corpus links to a `.md` URL, and nothing on
the new site needs one: `starlight-theme-black` passes `Astro.url.href` — the
HTML page URL — to its "Open in ChatGPT/Claude/v0" actions, not a markdown
URL.

**Inference.** The consumers of `.md` URLs are LLM agents and scripts, not
browsers or crawlers.

That last point is what decides it. Functional-spec requirement 1 ("every URL
reachable today must continue to resolve") would be *technically* satisfied by
`/docs/quickstart.md → /docs/quickstart/ 301`. But an agent that follows that
redirect gets HTML, which is precisely the thing it asked not to get. A
redirect would preserve the URL and destroy the feature, and the functional
spec lists per-page markdown under **feature** parity, not just URL
preservation.

**Decision: emit real static `.md` endpoints**, the second of the two options
the architecture allows. One Astro route covers all 45 non-landing pages, and it costs
~230 KB in `dist`. No `_redirects` rules are added for `.md` paths.

The landing page is the one exception: `index.mdx` is a `template: splash`
page whose body is JSX (`<CardGrid>`, `<LinkCard>`), so raw markdown for it
would be neither valid markdown nor useful. `/index.md` is not emitted, and
`/.md` — which is what the mechanical rule would produce — is not a URL
GitBook could have served either.

### Relative image paths: one rewriter, three consumers

Phase 3 recorded that the theme's "Copy page" blob emits
`![](../../../assets/foo.png)`, unresolvable outside the repo, and put the fix
here because `llms.txt` "has the same problem to solve". Both the `.md`
endpoints and the copy blob read `entry.body`, so they share one fix.

The corpus uses exactly two asset reference shapes, confirmed by scanning all
46 pages:

| Shape | Count | Lives in | Rewrites to |
| --- | --- | --- | --- |
| `![alt](../../[../]assets/NAME)` | 71 | `src/assets/` | `https://docs.kiln.tech/_astro/NAME.<hash>_<hash>.webp` |
| `src="/assets/NAME"` / `href="/assets/NAME"` (raw HTML, videos + card covers) | 16 | `public/assets/` | `https://docs.kiln.tech/assets/NAME` |

No angle-bracket or percent-encoded markdown image references exist (phase 3
normalised the filenames), so the rewriter does not have to reimplement
CommonMark link-destination parsing.

**Spike result (verified, not assumed).** The first shape needs the *optimized*
URL, which is only knowable at build time. `import.meta.glob('../assets/*',
{ eager: true })` + `getImage({ src, format: 'webp' })` returns
`/_astro/Collab2.Csp7EcGO_Z89dcf.webp` — **byte-identical to the URL the
markdown pipeline emits** for the same image in
`dist/docs/collaboration/index.html`.

**Correction, found while implementing.** An earlier draft of this section
claimed the eager glob was free. It is not, and the first clean build proved
it: `dist/_astro` came back with **68 unoptimized PNGs alongside the 68 WebPs**
and `dist` grew from 2.0 MB of images to 9.2 MB. The measurement that said
otherwise had been taken from a build that reused a warm image cache.

Isolating it took two controlled clean builds — glob present with `getImage`
never called (1 PNG, 2.0 MB) and glob present with `getImage` called (68 PNGs,
9.2 MB) — which points at `getImage`, not the glob. The mechanism is in
`astro/dist/assets/utils/proxy.js`: Astro exports each `src/` image as a
`Proxy` whose `get` trap adds the file to `globalThis.astroAsset.referencedImages`
**on any property read**, and `assets/build/generate.js` deletes the original
only for images not in that set. Reading `.src` to hand it to `getImage` is
enough to pin the original in the output.

The trap answers exactly one property without recording anything —
`if (name === 'clone') return structuredClone(target)`, checked before the
`referencedImages.add` line — and the clone carries `fsPath`, which is all
`getImage` needs. So `src/lib/page-markdown.ts` reads `image.clone` and never
touches the proxy otherwise, including for its lookup keys. Clean build back to
**1 PNG + 68 WebP, 2.0 MB**, matching the pre-phase state exactly.

Two smaller consequences of the same finding:

- Images are resolved **only for the page being rendered**, in two passes
  (`srcAssetNames` then `getImage`). Resolving all 69 up front generated a
  second WebP variant of `hero.png`, whose only real use is the splash hero
  and whose transform options differ — a dead 2 KB file in `dist`.
- `getImage` is memoised per filename, so 45 endpoints plus 47 middleware
  passes do the work once.

`starlight-llms-txt` needs no rewriting: it renders each page to HTML through
an Astro container and converts back to markdown, so its images are already
the resolved `/_astro/…` paths.

**Spike result.** A route at `src/pages/[...slug].md.ts` builds to
`dist/<slug>.md` verbatim under `trailingSlash: 'always'` — Astro does not
append a slash to a route carrying a file extension.

### The copy-page blob is fixed with route middleware, not a component copy

The blob is built inside `starlight-theme-black/overrides/PageTitle.astro`
from `Astro.locals.starlightRoute.entry.body`. Overriding `PageTitle`
ourselves would mean copying 130 lines of the theme's markup and scoped CSS
into this repo, which would silently diverge on the next theme upgrade.

Starlight's `routeMiddleware` hook mutates the same route data before any
component renders, in ~20 lines, with no theme markup copied. `render(entry)`
uses `entry.rendered`, not `entry.body`, so replacing `body` changes the copy
blob and the `.md` endpoints without touching the rendered HTML. **This is
verified by diffing `dist/**/*.html` before and after** — see Verification.

### `/sitemap.xml` cannot be produced directly, so it is a redirect

`@astrojs/sitemap` always emits an index plus numbered children
(`sitemap-index.xml`, `sitemap-0.xml`); its `filenameBase` option changes the
stem, not the shape, so there is no configuration that yields a single
`sitemap.xml`. Starlight adds the integration itself and only skips doing so
if `@astrojs/sitemap` is already in `integrations`, so taking it over buys
nothing.

**Decision:** `/sitemap.xml → /sitemap-index.xml 301`, as a `structural` row
in `redirects.csv`. Google follows redirects when fetching a sitemap. Phase 8
should submit `https://docs.kiln.tech/sitemap-index.xml` — the redirect exists
for the URL Search Console already has on file, not as the address we hand it.

This is the rule that finally needs phase 4's `validate_targets` widening:
`/sitemap-index.xml` is neither a content page nor a file in `public/`.

### `robots.txt` is generated, not static

A static `public/robots.txt` would hardcode the origin a second time. A
`src/pages/robots.txt.ts` endpoint reads `Astro.site`, so `astro.config.mjs`
stays the single source of truth for the origin.

### The 404 page is already useful — verified, not assumed

Checked against `dist/404.html` rather than merely confirming the file exists:

| Requirement | Present |
| --- | --- |
| Link home | `<a href="/" class="site-title">` |
| Section navigation | Header nav: Docs, Developers, Download |
| Full page list | In the mobile menu, which carries all 21 doc entries plus the Developers group |
| Working search | Same `Search.astro…js` bundle as every docs page |
| A human message | "Page not found. Check the URL or try using the search bar." |

**Checked in a browser, not only in the markup.** Rendering `dist/404.html`
from a static server at 1280px and driving it with Playwright: the desktop
*sidebar* is not rendered (an earlier draft of this table claimed it was —
that markup is the mobile menu), and opening the search dialog and typing
"fine tuning" returns real Pagefind hits
(`/docs/fine-tuning/fine-tuning-guide/` and four more) with no console errors.
So search genuinely works from the 404 page rather than merely being present.

`astro preview` shows Astro's own dev 404 instead, which is a preview-server
artifact — Cloudflare Pages serves `dist/404.html`.

No change needed. Recorded here so phase 7 does not re-litigate it.

### `twitter:card` is already correct

Starlight emits `<meta name="twitter:card" content="summary_large_image">` on
every page by default. The architecture asks for that value; it is already
there, so the config does not restate it. Only `og:image` (plus dimensions and
alt) and `twitter:image` are added.

## Steps

### 1. `site/src/lib/markdown-assets.mjs` — the pure rewriter

Plain `.mjs` with JSDoc types so both Astro and `node --test` can import it
(`npm run test:js` globs `scripts/*.test.mjs`, which can import across).

```js
/** Filename an `../../assets/NAME` reference points at, or null. */
export function srcAssetName(reference)

/** True for a `/assets/NAME` reference into public/. */
export function isPublicAssetPath(reference)

/** Every src/assets filename `markdown` refers to, so the caller can resolve
 *  exactly those and no more. */
export function srcAssetNames(markdown)

/**
 * Rewrite every asset reference in `markdown` to an absolute URL.
 * @param {string} markdown
 * @param {(name: string) => string | undefined} resolveSrcAsset
 *   filename in src/assets -> built URL (path, not absolute)
 * @param {string} origin  e.g. "https://docs.kiln.tech"
 */
export function absolutizeAssetReferences(markdown, resolveSrcAsset, origin)
```

Handles markdown image destinations `![alt](…)` and HTML `src=`/`href=`
attributes. Leaves anything already absolute (`http:`, `https:`, `//`,
`data:`, `#`) untouched, which is also what makes it idempotent. Throws on a
`src/assets` reference the resolver cannot place — a silently unrewritten path
is the failure mode worth being loud about.

### 2. `site/src/lib/page-markdown.ts` — the Astro-side binding

```ts
/** A page body with every asset reference made absolute. */
export async function absolutizePageBody(body: string, origin: string): Promise<string>

/** `---\ntitle…description…---\n\n` + that body. */
export async function pageMarkdown(entry, origin): Promise<string>
```

Two passes per page: `srcAssetNames` to find what this body needs, then
`getImage` on those alone, memoised per filename. Both halves of that matter —
see the correction above for why resolving everything up front is wrong and
why the metadata is read through `image.clone`.

The frontmatter header matches the shape the theme already uses for its copy
blob (`title`, `description`), so the copy blob and the `.md` endpoint return
the same bytes for the same page.

### 3. `site/src/pages/[...slug].md.ts` — per-page markdown endpoints

`getStaticPaths` over `getCollection('docs')`, skipping the `index` entry (see
the landing-page note above). `GET` returns `pageMarkdown(entry, site)` as
`text/markdown; charset=utf-8`.

### 4. `site/src/starlightRouteData.ts` — the copy-page fix

`defineRouteMiddleware` that replaces `starlightRoute.entry` with a shallow
copy whose `body` has been run through `absolutizeAssetReferences`. Registered
as `routeMiddleware: ['./src/starlightRouteData.ts']` in the Starlight config.

### 5. `site/src/components/Footer.astro` — the visible `llms.txt` link

Wraps Starlight's own `Footer` so edit-link, last-updated and pagination are
untouched, then appends one line:

```
For LLMs: llms.txt · llms-full.txt
```

Registered via `components: { Footer: './src/components/Footer.astro' }`.
Safe: `starlight-theme-black` overrides `Head`, `Hero`, `MobileMenuToggle`,
`PageTitle`, `Pagination`, `Sidebar`, `SiteTitle` and `ThemeSelect` — not
`Footer` — so there is no override collision and no theme warning.

### 6. `site/src/pages/robots.txt.ts`

`User-agent: * / Allow: /` plus `Sitemap: <site>/sitemap-index.xml`, both
built from `Astro.site`.

### 7. `site/public/favicon.svg`

Hand-written SVG: a rounded-square tile in the theme's accent (`#6d5ef8`) with
a white "K". Renders at 16 px. Flagged as a placeholder in the README.

### 8. `site/scripts/build_og_image.mjs` → `site/public/og.png`

1200×630, generated with `sharp` (already a dependency) from an SVG: the
theme's dark background, "Kiln AI" in white, the site description beneath it
in muted grey, an accent rule, and `docs.kiln.tech` in the corner. Wired as
`npm run og`. The PNG is **committed** — the architecture calls for one static
image, and the generator exists so it can be regenerated deliberately rather
than on every build. Font availability differs between machines, so the script
is a tool, not a build step.

### 9. `site/astro.config.mjs`

- `import starlightLlmsTxt from 'starlight-llms-txt'` and add it to `plugins`,
  configured with `details` pointing at the site and `promote: ['index*']`.
- `head`: `og:image`, `og:image:width`, `og:image:height`, `og:image:alt`,
  `twitter:image` — all absolute, built from the configured `site`.
- `head`: the Cloudflare beacon, emitted only when
  `CLOUDFLARE_ANALYTICS_TOKEN` is set.
- `components: { Footer }`, `routeMiddleware`.

### 10. `site/scripts/build_redirects.py`

- New `PUBLIC_DIR` constant and `BUILD_EMITTED_TARGETS` frozenset naming the
  root paths the build produces that are neither pages nor `public/` files
  (`/sitemap-index.xml`, `/sitemap-0.xml`, `/llms.txt`, `/llms-full.txt`,
  `/llms-small.txt`, `/robots.txt`), each with the integration that emits it
  named in a comment.
- `target_exists(path, content_dir, public_dir)` replaces the bare
  `page_exists` call in `validate_targets`; `page_exists` itself is unchanged
  and still used by the alias generator.
- `build_rules(rows, content_dir=CONTENT_DIR, public_dir=PUBLIC_DIR)`.
  `content_dir=None` still skips validation entirely, as today.
- `STRUCTURAL_REDIRECTS` gains `("/sitemap.xml", "/sitemap-index.xml")`.
- New generated source `md-endpoint`, with `refresh_rows` emitting one
  identity row (`old_path == new_path`) per non-root sitemap page. Identity
  rows produce no `_redirects` rule — `build_rules` drops them first — but
  `verify_redirects.mjs` checks every path in the CSV, so this is what proves
  all 45 `.md` endpoints actually built.

### 11. `site/redirects.csv` and `site/public/_redirects`

Regenerated with `npm run redirects -- --refresh-csv`. Actual: 83 → 84 rules
(the one new one is `/sitemap.xml`), and 130 rows, of which 45 are new
`md-endpoint` identity rows.

### 12. Descriptions for the two pages phase 2 flagged

- `docs/structured-data-json.md`:
  `"Define JSON schemas for task inputs and outputs, with automatic validation"`
- `docs/keyboard-shortcuts.md`:
  `"Shortcuts for navigating the dataset, rating runs, and invoking runs"`

Both match the corpus's existing style: quoted, sentence case, no trailing
period, under a dozen words.

### 13. `site/package.json`

`"og": "node scripts/build_og_image.mjs"`.

### 14. `site/README.md`

New "Machine-readable output" section (`llms.txt`, `.md` endpoints, how the
asset rewriting works and why), a "Social preview and favicon" section, and an
"Analytics" section with the exact Cloudflare steps. Update the layout table
and "Still to do".

## Tests

Ten new Python tests and eighteen new JavaScript ones; 272 → 300 in total.

Python (`scripts/test_build_redirects.py`), all in existing test classes:

- `test_target_may_be_a_file_in_public` — a rule pointing at a file that
  exists only in `public/` validates.
- `test_target_may_be_a_file_the_build_emits` — `/sitemap-index.xml`
  validates though it is in neither tree.
- `test_a_directory_in_public_is_not_a_target` — `/assets/` must not pass just
  because `public/assets/` exists; the same trap `page_exists` already avoids.
- `test_unknown_target_still_raises_and_names_where_it_looked` — the widening
  did not turn validation off.
- `test_generates_the_sitemap_redirect` — `refresh_rows` emits
  `/sitemap.xml → /sitemap-index.xml`.
- `test_md_endpoint_rows_cover_every_page_but_the_root`
- `test_md_endpoint_rows_are_identity_rows`
- `test_md_endpoint_rows_never_become_rules` — they do not reach `_redirects`.
- `test_no_md_endpoint_row_for_the_site_root` — neither `/.md` nor `/index.md`.
- `test_a_human_row_still_wins_over_a_generated_md_row` — the existing
  provenance rule holds for the new source.

JavaScript (`scripts/markdown_assets.test.mjs`), covering every reference
shape the corpus actually contains plus the properties the callers rely on:

- The two nesting depths in the corpus (`../../../` and `../../../../`), an
  HTML `src`, an `href`, and an `svg` that must not be assumed to be WebP.
- `preserves percent-encoding in a public asset name` — `rag%20icon%202-2.png`
  is served under that spelling.
- `resolves a percent-encoded src/assets name against its real filename` —
  the opposite direction, where the file on disk has the space.
- `leaves remote images alone`, `leaves data URIs, protocol-relative URLs and
  fragments alone`, `leaves internal page links alone`.
- `does not rewrite prose that merely looks like a path` — the
  `{task}/.../eval_configs/{id}` line in `code-judges.md` is the real case.
- `is idempotent, which is what makes the route middleware safe`.
- `throws when a src/assets reference has no built URL`.
- `srcAssetNames` collects each name once, ignores remote images, and is empty
  for a page with none — this is what keeps `getImage` off unreferenced files.

## Verification

Beyond the two suites, all offline:

1. `npm run build` clean, then assert against `dist`:
   - `dist/llms.txt`, `dist/llms-full.txt`, `dist/llms-small.txt`,
     `dist/robots.txt`, `dist/favicon.svg`, `dist/og.png` all exist.
   - 45 `.md` files at the expected paths, and `dist/index.md` absent.
   - No `../` sequence survives in any `.md` endpoint or in any page's
     `data-content` copy blob.
   - Every `https://docs.kiln.tech/_astro/…` URL in the `.md` output has a
     matching file in `dist/_astro/`.
   - `og:image`, `twitter:image` and the existing `twitter:card` present on a
     docs page and on the landing page.
   - No Cloudflare beacon tag when the token is unset; one when it is set.
2. **HTML equality check for the route middleware.** Hash every
   `dist/**/*.html` before and after adding the middleware and confirm the
   only bytes that move are inside `data-content`.
3. `npm run redirects:check` clean, and
   `node scripts/verify_redirects.mjs --dist dist --min-paths 176` — 176 is
   today's count (129 before this phase, plus 45 `.md` paths, plus
   `/sitemap.xml` and `/sitemap-index.xml`).
4. `/favicon.svg` no longer 404s: re-run the phase 2 dangling-reference sweep
   over `dist` and confirm zero.

### Results

All of the above ran and passed on a clean build:

- 300 tests green (236 Python, 64 JavaScript).
- 45 `.md` endpoints, no `/index.md`. Every `_astro` and `/assets` URL they
  emit resolves to a file in `dist`. The only surviving `../` anywhere in the
  `.md` output or the copy blobs is the literal `{task}/.../eval_configs/{id}`
  in `code-judges.md`, which is prose.
- The middleware moves **nothing** outside `data-content`: 47 of 47 pages
  byte-identical once that attribute is blanked.
- `verify_redirects.mjs --dist dist --min-paths 176`: 176 paths, all resolve,
  84 through local rules.
- Dangling-reference sweep over `dist`: 220 local references, **0 dangling**.
  This is the phase 2 `/favicon.svg` finding closed.
- With `CLOUDFLARE_ANALYTICS_TOKEN` set, `beacon.min.js` appears on 47/47
  pages; with it unset, on 0.
- Served from `dist` over HTTP: `/docs/quickstart.md` returns 200
  `text/markdown`, `/llms.txt` and `/robots.txt` 200 `text/plain`,
  `/favicon.svg` 200 `image/svg+xml`, `/og.png` 200 `image/png`.
  (`/sitemap.xml` 404s under `astro preview`, which does not implement
  `_redirects` — the same known gap phase 4 documented.)

## Carried forward

New findings, on top of the phase 2, 3 and 4 lists later phases inherit.

- **The favicon and the OG image are placeholders, and a human has to replace
  them.** Both are wired up and look deliberate rather than broken, but
  neither is the Kiln brand mark — there is none in this repo or its history.
  Phase 8's deadline, since that is when the site becomes the public one.
- **Cloudflare Web Analytics has no token.** Phase 6 sets up the Pages
  project; `CLOUDFLARE_ANALYTICS_TOKEN` should be set there at the same time,
  and phase 8 should confirm data is arriving before GitBook is cancelled.
- **`/sitemap.xml` is a redirect, not a file.** Phase 8 should submit
  `https://docs.kiln.tech/sitemap-index.xml` to Search Console. The redirect
  exists for the URL Search Console already holds from GitBook.
- **The `.md` endpoints reproduce a URL family nobody has probed.** The
  decision to serve them is argued from the sitemap and the phase 1 brief, not
  from an observation of the live site. If phase 1's crawl ever runs, it costs
  nothing to confirm — and if GitBook turns out to use a different spelling
  (`/docs/quickstart/index.md`, say), the fix is one line in
  `src/pages/[...slug].md.ts` plus a `redirects.csv` refresh.
- **`llms.txt` is an index of the two full-text files, not of the 45 pages.**
  GitBook's was a page list. The plugin follows the llmstxt.org convention
  instead, and `llms-full.txt` carries everything a page list would have
  pointed at, so this is a difference in shape rather than in content. The
  `details` text names the `.md` URL pattern so an agent can still address a
  single page. Recorded, not treated as a gap.
- **The asset rewriter does not know about fenced code blocks.** It is regex
  over the raw body, so an `<img src="/assets/…">` *inside* a code sample
  would be rewritten as if it were real markup. No page does that today
  (checked across all 46), and the failure is cosmetic — the rewritten URL is
  still correct, just unwanted in a code listing. Worth remembering before
  someone documents this repo's own markup.
- **Internal page links in the `.md` output stay root-relative.** They resolve
  against the origin the file was fetched from, so unlike the `../../` asset
  paths they are not broken. Making them absolute would help anything that
  pastes the copy blob into a chat window with no base URL; it was left alone
  as a change with a wider blast radius than this phase needed.
- **Two pages now have descriptions that nobody at Kiln wrote.**
  `structured-data-json.md` and `keyboard-shortcuts.md` had none in GitBook.
  The new copy is faithful to the pages and matches the corpus's house style,
  but it is ours, not theirs — worth 30 seconds of a human's attention during
  phase 7.
- **`--min-paths` is now 176.** Phase 4 left it at 129; the README, this plan
  and phase 4's CI note all need to agree. Phase 6 should spell the CI gate
  `node scripts/verify_redirects.mjs --dist dist --min-paths 176`. It is a
  floor, not an equality — raise it when the inventory grows.
- **`ruff format --check` fails on all four Python files**, including the two
  this phase did not touch. There is no ruff config in the repo and the
  project has never been ruff-formatted, so this is not a regression and was
  left alone; `ruff check` passes. If a formatter is ever adopted it should be
  one commit of its own.
