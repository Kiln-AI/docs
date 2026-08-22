---
status: complete
---

# Architecture: GitBook → Astro Starlight Migration

A single architecture doc — the project is broad but each piece is small, and
no component has enough internal complexity to justify its own design file.

No separate UI design doc: the theme (`starlight-theme-black` with dropdown
sidebar), layout, and landing page are already built and accepted in PR #16.
Visual acceptance criteria live in the functional spec.

## Repository layout

### Today

```
/                            GitBook source, still the source of truth
  README.md, SUMMARY.md
  docs/**, developers/**
  .gitbook/assets/**         159 files, 86 referenced
/site                        Astro site
  scripts/gitbook_to_starlight.py
  src/landing/index.mdx      hand-written landing page
  src/content/docs/**        GENERATED, gitignored
  public/assets/**           GENERATED, gitignored
  sidebar.json               GENERATED, gitignored
```

### After conversion

```
/site
  src/content/docs/**        COMMITTED, hand-maintained
  src/assets/**              COMMITTED, referenced images only
  src/content.config.ts, astro.config.mjs
  public/og.png, public/_redirects
  scripts/gitbook_to_starlight.py   kept until the final step
  scripts/                   migration tooling (below)
/specs/**                    these documents
```

The GitBook source directories are deleted once content has moved. Use
`git mv` where paths map cleanly so history follows the files.

## Transformer changes

`gitbook_to_starlight.py` currently writes into fixed locations and calls
`shutil.rmtree(DOCS_OUT)` first. Once content is hand-edited and committed,
that is destructive.

**Add an `--out DIR` flag.** When passed, the script writes the converted tree
to `DIR` instead of `site/src/content/docs`, and skips the asset copy and
`sidebar.json` write. This makes the late-content reconciliation safe: convert
into a scratch directory, then copy in only the pages that are actually new.

The existing `--list` flag stays; it is the diagnostic for "did the walk pick
up files it shouldn't".

After the final reconciliation, the script and its `npm run convert` wiring are
deleted, along with the gitignore entries for the generated paths.

## Asset handling

### Pruning

A script (`scripts/prune_assets.py`) computes:

- **referenced** = every `.gitbook/assets/NAME` appearing in any source
  markdown, URL-decoded to match real filenames
- **orphans** = files on disk minus referenced

Orphans are reported and deleted. Expected: 159 on disk, 86 referenced, ~73
removed, including both oversized videos.

The script must **report** the delete list rather than silently removing, and
must fail loudly if a referenced file does not exist on disk.

### Move into the image pipeline

Referenced images move to `site/src/assets/` and pages reference them with
relative markdown links, which puts them through Astro's optimizer (automatic
WebP, responsive sizing). The prototype's absolute `/assets/...` paths in
`public/` skip this.

Constraint: Astro only optimizes images referenced from markdown image syntax,
not from raw `<img>` inside the ~90 `<figure>` blocks. Converting figures to
markdown images loses the `width` attributes some of them carry. **Decision:**
convert `<figure>` blocks to markdown images plus a caption where the
`figcaption` is non-empty, and re-express width constraints in CSS rather than
per-image attributes. Where a figure genuinely needs a fixed width, keep it as
HTML and accept it skipping the optimizer.

Videos stay in `public/` — Astro's optimizer does not process them.

## URL preservation

### Data model

One CSV, `site/redirects.csv`, committed and human-reviewable:

```csv
old_path,new_path,status,source
/docs/fine-tuning-guide,/docs/fine-tuning/fine-tuning-guide/,301,alias
/docs/old-name,/docs/new-name/,301,gsc
```

- `old_path` — path only, no origin
- `new_path` — path on the new site
- `status` — 301 (302 only if we deliberately choose a rollback window)
- `source` — `sitemap` | `crawl` | `gsc` | `alias` | `manual`, so every row's
  provenance is auditable

### Generation

`scripts/build_redirects.py` reads `redirects.csv` and emits
`site/public/_redirects`, which Astro copies to `dist/` and Cloudflare Pages
reads. Format is one rule per line: `/old /new 301`.

Rules:
- Skip rows where `old_path` equals `new_path`
- Flatten chains: if A→B and B→C, emit A→C and B→C
- Fail on duplicate `old_path` with conflicting targets
- Cloudflare Pages caps static redirect rules (documented around 2,000 —
  confirm against current docs). Our inventory is well under 200, so headroom
  is large, but the script should error rather than silently truncate.

### Inventory capture

`scripts/capture_baseline.mjs` (Playwright) crawls the live GitBook site and
writes to `baseline/`:

- `urls.txt` — every URL found, from `sitemap.xml` plus link-following
- `pages/<slug>.txt` — rendered text per page, for content diffing
- `shots/<slug>.png` — full-page screenshot per page

**This requires real outbound internet access.** It cannot run in a
network-restricted session. Google Search Console's indexed-pages export is
added to `urls.txt` by hand — it is the only source for historical URLs that
have dropped out of the sitemap.

### Verification

`scripts/verify_redirects.mjs` takes a base URL (a Cloudflare preview
deployment, later production) and, for every `old_path` in the inventory,
asserts the response is 200, or a 301 whose target itself returns 200. It
reports failures as a list and exits non-zero. This is what turns "we wrote
redirects" into "redirects work".

### Trailing slashes

Set `trailingSlash` and `build.format` explicitly in `astro.config.mjs` rather
than relying on defaults, and confirm the deployed behaviour on the preview URL
before cutover. Whatever is canonical must match `sitemap.xml` and the
canonical tags Starlight emits.

## Feature parity implementation

| Feature | Implementation |
| --- | --- |
| `llms.txt` | `starlight-llms-txt` plugin. Visible link added to the site footer or landing page — GitBook surfaces it in page chrome today and we did not know it existed, so discoverability matters. |
| OG image | One static `public/og.png`. Injected via Starlight's `head` config as `og:image` and `twitter:image`, with `twitter:card = summary_large_image`. Absolute URL, built from the configured `site`. |
| Analytics | Cloudflare Web Analytics beacon, injected via the same `head` config. |
| Search | Pagefind, already working. No change. |
| Per-page markdown | The theme's "Copy page" menu already covers copy-to-clipboard. Check whether GitBook's `.md` URLs are linked externally; if so, add rules to `_redirects` or emit static `.md` endpoints. |
| `editLink` | Base URL must change once content lives in `site/src/content/docs/`. |

## CI

A GitHub Actions workflow on pull requests:

1. `npm ci`
2. `npm run build`
3. Link validation via `starlight-links-validator`, configured to fail the
   build on broken internal links
4. `verify_redirects.mjs` against the built output where it can run offline
   (relative checks), full verification against the preview deployment

Node is pinned to the `engines` floor already declared (>= 22.12).

## Deployment

Cloudflare Pages, connected to the repo:

- Build command: `cd site && npm run build`
- Output directory: `site/dist`
- Node version pinned via environment variable
- Preview deployments on PRs, production on the branch we cut over from

`site/README.md` gains a deployment section covering project setup, custom
domain, DNS, and the cutover order: deploy to preview → verify → point DNS →
watch Search Console → decommission GitBook.

## Testing strategy

This is a content project, so "tests" are checks rather than unit tests:

| Check | Tool | Gate |
| --- | --- | --- |
| Site builds | `astro build` | CI, blocking |
| No broken internal links | `starlight-links-validator` | CI, blocking |
| Every old URL resolves | `verify_redirects.mjs` | Pre-cutover, blocking |
| Page count sanity | transformer `--list` | Manual, during conversion |
| Content fidelity | text diff vs `baseline/pages/` | Per-page QA |
| Visual fidelity | screenshot vs `baseline/shots/` | Per-page QA |
| Asset integrity | `prune_assets.py` fails on missing referenced file | During pruning |

The Python scripts are small and procedural; a couple of unit tests around
`build_redirects.py` chain-flattening and duplicate detection are worth having,
since that logic is easy to get subtly wrong and hard to eyeball.

## Risks

- **The URL inventory is incomplete.** The main risk to SEO. Mitigated by using
  three independent sources (sitemap, crawl, Search Console) and by watching
  Search Console after cutover.
- **Baseline cannot be captured.** Blocks meaningful per-page QA and must
  happen before GitBook is torn down. Sequenced early for this reason.
- **Anchor drift.** Accepted as priority 2; recorded rather than necessarily
  fixed.
- **Late content.** Handled by the reconciliation step and by keeping the
  transformer until the end.
