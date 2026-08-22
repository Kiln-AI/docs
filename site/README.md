# Kiln docs

The Kiln documentation site, built with [Astro
Starlight](https://starlight.astro.build/) and deployed as a static site on
Cloudflare Pages.

The content lives in `src/content/docs/` and is edited directly. It was
migrated out of GitBook — see `specs/projects/gitbook-to-starlight-migration/`
for the plan and the record of what changed — but there is no longer a
generation step between the markdown and the site. What you edit is what ships.

## Working on it

Requires **Node 22.12 or newer** (Astro 7's floor — older Node fails with
confusing module errors). The exact version CI and Cloudflare Pages use is in
`.nvmrc` at the repo root, so `nvm use` from anywhere in the checkout picks it
up.

```sh
cd site
npm install
npm run dev
```

Then open <http://localhost:4321>.

```sh
npm run build     # static output in site/dist
npm run preview   # serve site/dist locally
npm run serve     # build + preview in one step
```

## Layout

| Path | What it is |
| --- | --- |
| `src/content/docs/**` | Every page. Directory structure is the URL structure. |
| `src/content/docs/index.mdx` | The landing page — an MDX splash page using Starlight's `Card`/`LinkCard` components. |
| `src/content/docs/docs/fine-tuning/index.mdx`, `src/content/docs/docs/optimizers.mdx` | The two content pages that are MDX rather than markdown, because they render card grids with a component. See [Card grids](#card-grids) — and read [The GitBook converter](#the-gitbook-converter) before reconciling either of them. |
| `src/assets/**` | Images. Referenced from pages with relative markdown links, which is what puts them through Astro's image pipeline. |
| `public/assets/**` | Videos, and the handful of images referenced from raw HTML. Served verbatim. |
| `sidebar.json` | The sidebar, read by `astro.config.mjs`. |
| `redirects.csv` | Every URL the old GitBook site served, and where it goes now. See [Redirects](#redirects). |
| `public/_redirects` | Generated from `redirects.csv`. Read by Cloudflare Pages. |
| `ref/**` | Evidence the gates are built from: GitBook's sitemap, the alias exclusion list, and the anchors GitBook had already broken. See [Link validation](#link-validation). |
| `src/pages/[...slug].md.ts` | Serves every page's markdown at `<url>.md`. See [Machine-readable output](#machine-readable-output). |
| `src/pages/robots.txt.ts` | `robots.txt`, generated so the origin comes from `site`. |
| `src/lib/**` | The asset-URL rewriter shared by the `.md` endpoints and the "Copy page" blob, and the frontmatter builder. |
| `scripts/build_integrations.mjs` | Three post-build assertions: the `.md` `Content-Type`, that no unoptimized originals leaked into `dist/_astro`, and that the stale-anchor list is still true. |
| `scripts/stale_anchors.mjs` | Reads `ref/stale_anchors.txt`, and re-derives on every build whether each line still describes a broken anchor. |
| `scripts/qa_pages.mjs` | The page-QA sweep: residual GitBook markup in the sources, plus an optional real-browser render of every built page. `npm run qa`, and see [Page QA](#page-qa). |
| `src/components/Footer.astro` | Starlight's footer plus the visible `llms.txt` link. |
| `src/components/CoverCard.astro` | A `LinkCard` with a cover image above the title. What GitBook's card-table widget became. See [Card grids](#card-grids). |
| `src/starlightRouteData.ts` | Route middleware that rewrites each page's raw markdown before the theme reads it. |
| `public/og.png` | The one social preview image, shared by every page. Rebuild with `npm run og`. |
| `public/favicon.svg` | Placeholder favicon — see [Social preview and favicon](#social-preview-and-favicon). |
| `astro.config.mjs` | Site config, theme, nav, `head` tags, analytics. |
| `src/styles/custom.css` | Accent colours and a few content-level rules. |

## Images

Write images as **markdown images with a relative path into `src/assets/`**:

```markdown
![Alt text](../../assets/model-library.png)
```

Astro then optimizes them: automatic WebP, intrinsic `width`/`height`, and lazy
loading. Nothing else gets that treatment — a raw `<img src="/assets/…">`
served out of `public/` is passed through untouched, and Astro's own image
handling only ever sees markdown image syntax.

Two things to get right:

- **Count the `../` from the page, not the site root.** A page at
  `src/content/docs/docs/agents.md` reaches `src/assets/` with
  `../../../assets/`. Too few or too many segments fails the build with
  `Could not find requested image` — loud, and the usual cause of it.
- **Keep filenames free of spaces.** Astro itself copes fine with a space, as
  long as the reference is percent-encoded (`my%20shot.png`) or wrapped in
  `<angle brackets>`. The hazard is the third form: a **raw, unwrapped space is
  not an image at all** as far as CommonMark is concerned, so the line renders
  as literal `![alt](../../assets/my shot.png)` text — no error, no warning,
  and the link checker will not catch it, because it is not a link. Spaces also
  survive into the built URL as `%20`. Use `lowercase-with-hyphens.png` and
  neither can happen; the assets migrated out of GitBook were renamed on that
  basis.

### Screenshots with a caption

Screenshots are wrapped in a `<figure>`:

```markdown
<figure style="max-width:375px">

![](../../../assets/schema-editor.png)

<figcaption><p>Kiln's Visual Schema Editor</p></figcaption>
</figure>
```

**The blank lines are load-bearing.** A CommonMark HTML block ends at a blank
line, so they are what lets the image parse as markdown — and therefore be
optimized — while still nesting inside the `<figure>` in the rendered HTML.
Without them the image stays a literal string inside an HTML block.

Width goes on the `<figure>` as `max-width`, never on the image as a `width`
attribute: an `<img>` with attributes has to be raw HTML, which drops it out of
the optimizer. `src/styles/custom.css` zeroes the margin on the paragraph
CommonMark generates around the image, so the figure controls its own spacing.

#### Inside a numbered or bulleted list

The blank lines are necessary there too, and **not sufficient**. Indent the
whole block — opening tag, image, caption and closing tag — to the list item's
content column, four spaces in from the item's text:

```markdown
3.  Select the set of tools that the model should learn to call.

    <figure style="max-width:375px">

    ![](../../../../assets/selecting-tools.png)

    <figcaption><p>Selecting tools available to the fine-tuned model</p></figcaption>
    </figure>

4.  The next step, still a list item.
```

Get it wrong — the opening tag indented but the image and the closing tag left
at the margin — and the damage runs past the figure: the list **closes early**,
every following item renders as literal text (`4.  The next step…`, markdown
links included), and a four-space-indented `<figure>` in what is no longer a
list is read as an **indented code block**, so the raw tag is displayed in a
code frame.

None of that raises anything. The build is green, the page count matches, and
`starlight-links-validator` is silent precisely *because* the link stopped
being a link — the same silent-degradation failure as the raw-space image
above. `npm run qa -- --browser` is what catches it — see [Page QA](#page-qa).

### Card grids

`src/components/CoverCard.astro` renders a link card with a cover image above
the title; `docs/fine-tuning/index.mdx` and `docs/optimizers.mdx` lay a set of
them out in Starlight's `<CardGrid>`. It is what GitBook's
`<table data-view="cards">` widget became — Starlight rendered that as a plain
four-column table, with raw filenames as the link text.

The cover is passed as an `ImageMetadata`, imported by the page:

```mdx
import { CardGrid } from '@astrojs/starlight/components';
import CoverCard from '../../../../components/CoverCard.astro';
import fineTuningGuideCover from '../../../../assets/tuning2.png';

<CardGrid>
  <CoverCard
    title="Fine Tuning Guide"
    description="Our end-to-end walkthrough of fine-tuning a model in Kiln."
    href="/docs/fine-tuning/fine-tuning-guide/"
    cover={fineTuningGuideCover}
  />
</CardGrid>
```

Count the `../` from the page just as you would for a markdown image — the
example above is from `src/content/docs/docs/fine-tuning/index.mdx`.

Passing the import rather than a filename is the point: the covers then take
the same optimized path through `astro:assets` that a markdown image takes,
which is why they live in `src/assets/` like everything else. **Using a
component means the page has to be `.mdx`** — which has consequences for the
converter, so read [The GitBook converter](#the-gitbook-converter) before
reconciling either page.

### Videos

Videos go in `public/assets/` and are referenced absolutely
(`<video src="/assets/name.mp4">`). Astro's optimizer does not process video,
so there is nothing to gain from `src/assets/`. Cloudflare Pages rejects any
single file over 25 MiB — the largest video here is 4.8 MB, but a longer
screen recording will need Cloudflare Stream, R2 or Vimeo instead.

## Theme

The site uses [starlight-theme-black](https://github.com/adrian-ub/starlight-theme-black),
a shadcn-inspired Starlight theme. On top of stock Starlight it adds a top nav
bar and a per-page "Copy page" menu with open-in-ChatGPT/Claude actions.

Starlight themes are plugins, so it is configured in one place — the `plugins`
array in `astro.config.mjs` — and swapping it is an npm install plus editing
that array.

### Sidebar

The sidebar is `sidebar.json`, read by `astro.config.mjs` at build time. Add a
page by adding an entry; the file is ordinary committed content.

By default the theme renders a flat sidebar: every group becomes a static
header with all its children always visible, and `collapsed` in the sidebar
config is ignored. The docs have six nested groups that need to expand and
collapse, so the theme is configured with `sidebar: { useDropdowns: true }`,
which renders groups as collapsible dropdowns with a caret in the theme's own
styling.

A group starts open if it contains the current page or is not marked
`collapsed`, so the section you are reading is always expanded.

`src/styles/custom.css` carries one workaround for that sidebar. The theme
gives links a fixed `30px` height against a `22.4px` line-height, so labels
wrapping to two lines overflow their box and collide with the next entry —
three of our labels are long enough to wrap. Letting the box grow fixes it,
but the theme's `8px` block padding then makes every row `38px`, so the
padding is traded down to keep the intended `30px` rhythm: single-line rows
stay at `30px` and wrapped ones grow to `53px`.

The build also logs `No data found for font family Geist Mono`, from the
theme's font configuration. It is harmless — the monospace stack falls back —
and unrelated to the sidebar.

## Machine-readable output

GitBook published an `llms.txt` and a markdown copy of every page. Both are
reproduced here.

| URL | What it is |
| --- | --- |
| `/llms.txt` | Index, in the [llmstxt.org](https://llmstxt.org/) shape: what this project is, plus links to the two full-text files. |
| `/llms-full.txt` | Every page, concatenated. |
| `/llms-small.txt` | The same with notes, tips and `<details>` blocks stripped. |
| `/docs/quickstart.md` | One page's markdown, at its own URL plus `.md`. One route, `src/pages/[...slug].md.ts`, covers all 45. |
| `/robots.txt` | Points crawlers at `sitemap-index.xml`. |

**`Content-Type` comes from `dist/_headers`, not from the endpoint.** Astro's
static build throws away the headers an endpoint returns — it keeps them only
for adapters that declare `staticHeaders`, and this is a plain static build —
so the `Content-Type` in `src/pages/[...slug].md.ts` never reaches Cloudflare.
`scripts/build_integrations.mjs` writes a `_headers` file at the end of every
build instead, naming each `.md` path explicitly. Confirm it survives the
first real deployment: `curl -sI https://<preview>/docs/quickstart.md` should
report `text/markdown`.

Enumerating costs one of Cloudflare's **100** `_headers` rules per page, so
the build fails at 90 with instructions to switch to the single documented
rule `/*.md` (Cloudflare's `_headers` uses `_redirects`' matching, allows one
splat, and documents `/*.jpg` as an example). Enumeration is the default only
because it is generated from the files actually emitted, which proves the
rules match the output instead of asserting a pattern. A hand-added
`public/_headers` also fails the build rather than silently replacing all 45
rules; the error says how to merge them.

The first three come from the
[`starlight-llms-txt`](https://github.com/delucis/starlight-llms-txt) plugin,
configured in `astro.config.mjs`. All of it is linked from the site footer,
because an unlinked `llms.txt` is one nobody finds — which is how we nearly
missed that GitBook had one.

### Why `.md` endpoints rather than redirects

GitBook served a `.md` variant of every page. Redirecting those URLs to the
HTML page would satisfy "the URL still resolves" while handing an agent
exactly the thing it asked not to get, so they are served for real. They are
not in `sitemap.xml` — GitBook did not advertise them either — but they are in
`redirects.csv` as identity rows, which is what makes `verify_redirects.mjs`
check that all 45 were actually built.

The landing page has no `.md` form. It is a splash page whose body is JSX
rather than prose, and the mechanical spelling would be `/.md`.

### Absolute asset URLs

Pages reference images the way the build needs them —
`![](../../../assets/foo.png)` for `src/assets`, `/assets/foo.mp4` for
`public/assets` — and neither form means anything to something that fetched
the markdown over HTTP. `src/lib/markdown-assets.mjs` rewrites both to
absolute URLs, and `src/lib/page-markdown.ts` looks up what the image pipeline
actually emitted for each one, so a `.md` endpoint points at the same
optimized WebP the HTML page uses.

The same rewrite feeds the theme's "Copy page" blob, through the route
middleware in `src/starlightRouteData.ts`. That is why the middleware exists:
the blob is built inside the theme's `PageTitle` component, and rewriting the
route data avoids copying 130 lines of theme markup into this repo.

The blob and the endpoint therefore carry the same **body text** — identical
`absolutizePageBody` output, plus a trailing newline on the endpoint that the
blob does not have, so the two files differ by that one byte. Their
frontmatter differs by more: `src/lib/frontmatter.mjs` quotes every scalar
(`title: "Evaluate RAG Accuracy: Q&A Evals"`), matching what
`gitbook_to_starlight.py` writes into the content files, while the theme
interpolates the title raw. Two of the 45 titles and descriptions contain YAML
metacharacters, so the theme's blob is not parseable frontmatter for those
pages. That is the theme's to fix; the endpoints are correct.

Internal *page* links are left as root-relative paths. They resolve against
the origin the file was fetched from, which the `../../` asset paths did not.

## Social preview and favicon

`public/og.png` is one static 1200x630 image shared by every page, wired up as
`og:image` and `twitter:image` in the `head` array in `astro.config.mjs`.
Starlight already emits `twitter:card: summary_large_image`, so that is not
restated. Regenerate the image with:

```sh
npm run og
```

`scripts/build_og_image.mjs` renders it from an inline SVG through `sharp`. It
is a tool, not a build step — the PNG is committed, and text rasterises with
whatever fonts the machine has, so reruns are not byte-identical.

**Both `og.png` and `favicon.svg` are placeholders.** They are typography and
a "K" tile in the site's own palette, because there is no Kiln logo anywhere
in this repo or its history. Dropping in the real brand assets is a file swap:
`favicon.svg` is hand-editable, and the OG image's wording and colours are
constants at the top of the generator. Starlight links `/favicon.svg` from
every page whether or not it exists, so the placeholder is what stops 47 pages
404ing on it.

## Analytics

Cloudflare Web Analytics, injected as a `<script>` through the `head` array in
`astro.config.mjs`. **It needs a site token, which is account-specific and not
in this repo.** Until one is supplied no beacon tag is emitted at all, so the
site ships without analytics rather than with a broken tag.

To turn it on:

1. Cloudflare dashboard, Web Analytics, add a site for `docs.kiln.tech`.
2. Copy the site token out of the snippet it shows you.
3. In the Pages project, set `CLOUDFLARE_ANALYTICS_TOKEN` as a build
   environment variable (production and preview).

Alternatively paste the token into the `CLOUDFLARE_ANALYTICS_TOKEN` fallback
at the top of `astro.config.mjs`. Confirm afterwards that `beacon.min.js`
appears in the built HTML — `grep -l cloudflareinsights dist/index.html`.

## Redirects

Every URL GitBook served has to keep working. `redirects.csv` is the record of
what those URLs are; `public/_redirects` is generated from it and read by
Cloudflare Pages.

```csv
old_path,new_path,status,source
/docs/quickstart,/docs/quickstart/,301,sitemap
/docs/fine-tuning-guide,/docs/fine-tuning/fine-tuning-guide/,301,alias-generated
/docs,/docs/quickstart/,301,structural
```

`source` says where the row came from, and therefore how much to trust it:

| `source` | Where it came from | URL known to exist? |
| --- | --- | --- |
| `sitemap` | `ref/legacy_sitemap.xml`, GitBook's own sitemap | Yes |
| `alias-generated` | The flat-alias pattern, applied to nested pages | **No — inferred** |
| `structural` | Paths we chose to catch, e.g. `/docs`, `/sitemap.xml` | No — deliberate |
| `md-endpoint` | A page's `.md` URL, served rather than redirected | **No — the spelling is inferred** |
| `alias` | A flat alias a probe confirmed returns 200 | Yes |
| `crawl` | A crawl of the live site | Yes |
| `gsc` | Search Console's indexed-pages export | Yes, historically |
| `manual` | Added by hand | Your call |

The first four are generated from files in `ref/`. The rest are human-supplied
and live only in the CSV.

`md-endpoint` rows are identity rows — `old_path` equals `new_path` — so they
never become redirect rules. They are in the inventory so the verifier proves
the `.md` endpoints were built. Note what that does and does not establish:
GitBook is *recorded* as serving a markdown copy of every page, but nobody has
fetched one, so `/docs/quickstart.md` is our reading of the spelling rather
than an observed URL. These rows assert our build output, not GitBook's URL
inventory — which is why the verifier's "176 paths" is 131 inventory paths
plus 45 build-output assertions, not 176 old URLs.

`/sitemap.xml` is a `structural` row because `@astrojs/sitemap` can only emit
`sitemap-index.xml`; that is the URL to give Search Console, and the redirect
covers the one it already has on file.

**GitBook serves some nested pages at a flat path too** —
`/docs/fine-tuning/fine-tuning-guide` is also served at
`/docs/fine-tuning-guide`, and both are indexed by Google. Which pages have an
alias can only be learned by asking the live site. That probe has not run, so
every `alias-generated` row is an inference from the pattern rather than an
observed URL. They are marked as such rather than quietly mixed in with the
real ones.

```sh
npm run redirects          # redirects.csv -> public/_redirects
npm run redirects:check    # fail if public/_redirects is stale (CI gate)
```

`public/_redirects` is committed, so deploying needs nothing but `astro build`
and Cloudflare Pages needs no Python.

### Verifying

**Always go through `npm run verify:redirects`, never
`node scripts/verify_redirects.mjs` directly.** The npm script carries
`--min-paths`, and the raw command defaults that floor to 1 — see
[The floor](#the-floor) below for why that matters. Pass your oracle after
`--`:

```sh
npm run build
npm run verify:redirects -- --dist dist
```

That is the offline check: it applies the rules in `dist/_redirects` itself and
confirms every source path and every destination path lands on a file that was
actually built. No server required.

Against a running site:

```sh
npm run preview   # in another shell
npm run verify:redirects -- --base-url http://localhost:4321 --dist dist
```

`astro preview` does not implement `_redirects` — that file means nothing
outside Cloudflare Pages — so `--dist` is needed to apply the rules locally
before each request. **Drop `--dist` when checking a real deployment:**

```sh
npm run verify:redirects -- --base-url https://<preview>.pages.dev
```

Without it the server has to do the redirecting itself, which is the thing
actually being tested. A path passes if it returns 200, or redirects
permanently (301 or 308 — Cloudflare's own trailing-slash normalisation uses
308) to something that returns 200.

Every source path is held to the destination `redirects.csv` names for it, so a
rule that is missing, or that points at the wrong page, fails even when the
page it lands on exists.

#### The floor

A verifier that checks nothing must not report success. So an empty inventory
is an error rather than a pass, `--concurrency` and `--min-paths` must be
positive integers, and the run refuses to report on a pass where any path went
unchecked.

`--min-paths` is the last of those, and it is the one that catches a truncated
`redirects.csv` — the failure you least want to sail through on the pre-cutover
run against production. **It lives in one place: the `verify:redirects` script
in `package.json`.** Callers pass only their oracle, because the floor has to
move in step with the inventory and a floor only some callers pass has stopped
being a floor.

It is **176** today: 131 URLs from the inventory, plus 45 `md-endpoint`
identity rows that assert our own build output rather than GitBook's. Raise it
in `package.json` when the inventory grows.

Appending `--min-paths N` still works and wins, since the last flag is the one
read. That is an escape hatch for a one-off, not a way to make a failing run
pass — lowering the floor to get a green run is how a truncated inventory ships.

### Adding to the inventory

Rows added by hand are never touched by the generator, so a new redirect is
just a new line in `redirects.csv` with `source` set to `manual`, followed by
`npm run redirects`. `#` comments are allowed and travel with the row they sit
above, so annotating a hand-added row survives a refresh.

When the live-site crawl, alias probe and Search Console export land, merge
them like this rather than rebuilding:

1. Add each newly discovered URL as a row with `source` set to `gsc`, `crawl`
   or `alias`.
2. For a flat alias the probe **confirmed**, change that row's `source` from
   `alias-generated` to `alias`. Refresh then leaves it alone instead of
   regenerating it. Each alias has two rows, one per slash form, and they are
   settled separately — promote the sibling only if the probe requested it too.
3. For a flat alias the probe **disproved**, delete both of its rows and add
   the slashless path to `ref/alias_exclusions.txt`. One entry covers both
   forms; a row deleted without an entry comes back on the next refresh.
4. Run `python3 scripts/build_redirects.py --refresh-csv`. It regenerates the
   `sitemap`, `alias-generated` and `structural` rows from `ref/`, keeps every
   other row verbatim, prints what changed, and rewrites `public/_redirects`.
5. Review the diff and re-run the verification above.

### Trailing slashes

`astro.config.mjs` sets `trailingSlash: 'always'` and `build.format:
'directory'` explicitly. Starlight already generated trailing-slash URLs — its
canonical tags, its internal links and `dist/sitemap-0.xml` all use them — so
this records the choice rather than changing it, and gives the redirect targets
something stable to point at. GitBook served the same paths without a trailing
slash, which is what the 45 `sitemap` rows redirect.

## The GitBook converter

`scripts/gitbook_to_starlight.py` is the one-shot tool that produced this
content out of the GitBook tree. **It is not part of the build.** `npm run dev`
and `npm run build` are plain Astro commands; the converter is kept only for
the final reconciliation step, which picks up any GitBook page that landed
after the content freeze.

**Its inputs are not in this checkout.** `.gitbook/`, `docs/`, `developers/`
and `SUMMARY.md` were deleted once their content moved here, so a run has to
restore them first. Use a worktree, not `git checkout … -- <paths>`, so the
restored tree cannot be committed back by accident:

From `site/`, where the rest of this README leaves you:

```sh
# last commit carrying the GitBook tree
git worktree add /tmp/gitbook 3e16f5af77fc0e0e27a6785ec78a5f6c1761a889
# today's converter, not the one the worktree checked out
cp scripts/gitbook_to_starlight.py /tmp/gitbook/site/scripts/
cd /tmp/gitbook/site
python3 scripts/gitbook_to_starlight.py --out /tmp/converted
```

**Do not skip the `cp`.** The worktree is checked out at a commit that predates
this script, so the copy inside it is the older converter — it writes
`<img src="/assets/NAME">` for images that now live in `src/assets/`, which is
a 404 nothing validates, and it skips the image optimizer. The script cannot be
run in place from this checkout either: it finds the repo from its own path, so
it would look right back here and fail again.

The script prints this whole procedure if you forget it.

`--out` writes the converted pages to a scratch directory and nothing else — no
assets, no `sidebar.json`, no deletions — so pages can be copied in one at a
time. Because it copies no assets, it finishes by printing every asset its
pages reference and the `src/assets`/`public/assets` name to copy it to; bring
those across by hand from the worktree.

**Two pages are the exception and must not be copied over** — `fine-tuning/index.mdx`
and `optimizers.mdx`. See
[Two pages are `.mdx`: merge, never copy over](#two-pages-are-mdx-merge-never-copy-over)
below, *before* you copy anything in.

Its default run rebuilds `src/content/docs/` from scratch, which would delete
hand-maintained content, so it refuses to start once that directory is
committed to git. `--out` is the only mode to use.

| Flag | Effect |
| --- | --- |
| `--out DIR` | Write converted pages to `DIR` and nothing else. `--out=DIR` works too. `DIR` must be outside the repo and must not already hold markdown; see below. |
| `--list` | Print the source pages that would be converted; write nothing. |
| `--anchors` | List every link pointing at an anchor no heading provides. Without it they are summarised in one line. |

An argument the script does not recognise is an error, not a default run — and
so is an empty `--out`, which is what an unset shell variable looks like.

`--out`'s target is validated at parse time, because the flag exists to make
conversion safe and a bad target makes it the opposite. It is refused when it

- **is inside the repo** (`--out .`, `--out $PWD`, `--out src/content/docs`).
  The converter reads the repo for source markdown, so it would overwrite its
  own input;
- **contains the repo** — `/`, or any parent of the checkout;
- **already holds markdown this converter did not write**, which would be
  clobbered. The walk follows symlinks, so a symlinked subdirectory counts. A
  directory it wrote before carries a `.gitbook-to-starlight-out` stamp, so
  re-running into the same scratch directory is fine;
- **exists and is not a directory**, including a symlink that does not point at
  one.

Beyond that, each page is re-checked at the moment it is written: if the path
resolves outside the target — through a symlinked subdirectory, say — the run
stops rather than writing. Target validation happens once, but the writes happen
later, and that gap is where `--out` has gone wrong before. Pages are written to
a sibling temp file and moved into place with `os.replace`, so a destination
that is a hardlink to a source file keeps its own inode rather than being
truncated, and a page appears whole or not at all.

What is *not* checked is whether the target holds unrelated non-markdown
content, so `--out ~` will happily scatter 45 pages across a home directory
that does not contain the checkout. Use a fresh directory outside the checkout —
`mktemp -d` is the obvious choice.

### Two pages are `.mdx`: merge, never copy over

**`src/content/docs/docs/fine-tuning/index.mdx` and
`src/content/docs/docs/optimizers.mdx` are the exception to "copy the page in".**

Both carried GitBook's `<table data-view="cards">` widget, which Starlight
renders as an ordinary four-column table with a `Cover image` header and raw
filenames (`tuning2.png`) as the link text. They now use a component instead —
see [Card grids](#card-grids) — and a component means the page must be MDX.

The converter knows nothing about that. It writes `.md`, one file per page, so
for these two its output is a *different file* from the one in the tree:

- Copying `index.md` in beside `index.mdx` gives Astro **two pages for one
  URL**, and the build fails on the collision.
- Deleting the `.mdx` to resolve that collision **restores the card table** —
  the exact defect the migration removed, and it comes back looking like
  ordinary converter output, so nothing flags it. The link validator is happy;
  the table is a valid table.

So: **diff the converter's `.md` against the `.mdx` and merge the prose changes
into the MDX by hand.** The frontmatter and the body text transfer normally;
the card table in the converted output is the part that has already been
replaced and must be dropped. Keep the file `.mdx`, and keep its
`import`/`<CardGrid>` block.

`npm run qa` is the backstop if this goes wrong anyway: its
`gitbook-card-table` check fails on `data-view="cards"` in any content file.

### Tests

```sh
npm test
```

`npm test` runs both suites, neither of which needs anything beyond the
standard library:

- `scripts/test_gitbook_to_starlight.py` and `scripts/test_build_redirects.py`
  (stdlib `unittest`) — `npm run test:py`
- `scripts/verify_redirects.test.mjs`, `scripts/markdown_assets.test.mjs`,
  `scripts/frontmatter.test.mjs`, `scripts/stale_anchors.test.mjs` and
  `scripts/qa_pages.test.mjs` (`node:test`) — `npm run test:js`

They cover the parts that are easy to get subtly wrong and hard to eyeball: for
the converter, the github-slugger port, anchor remapping, link and asset
rewriting, figure conversion, asset naming and YAML frontmatter scalars; for
the redirects, chain flattening, duplicate detection, the alias pattern, and
the sitemap's whitespace-wrapped `<loc>` values; for the machine-readable
output, every asset-reference shape the corpus uses, the idempotence the route
middleware relies on, and every frontmatter scalar parsed back with a real
YAML parser rather than eyeballed; for the stale-anchor allowlist, that an
entry excuses exactly one link on one page and stops excusing it the moment it
stops being true; and for the QA sweep, that each detector fires on the real
defect shape and stays quiet on the thing that resembles it — a checker that
reports nothing because it checks nothing looks exactly like a clean site.

## Link validation

Every build runs
[starlight-links-validator](https://github.com/HiDeoo/starlight-links-validator)
over the corpus and fails on a broken internal link or a `#anchor` that no
heading answers. This is the gate the conversion needed most: it rewrote
relative links across 45 pages, and a link that lands nowhere looks exactly
like one that works until someone clicks it.

Two settings are not the defaults:

- **`sameSitePolicy: 'error'`.** An internal link written as
  `https://docs.kiln.tech/docs/quickstart/` would send a reader of a *preview*
  deployment back to production, so absolute self-links are rejected in favour
  of the root-relative form. Stock behaviour is to ignore them.
- **`exclude`**, built from `ref/stale_anchors.txt`.

### The two anchors that are still broken

24 links pointed at headings that no longer exist. They were broken in the
GitBook source before this migration started — headings renamed upstream,
links never updated — so they are broken on the live site today too.

Phase 7 repaired **22** of them, two ways: where the section was renamed but
stayed on the page, its old id was put back on the heading that replaced it
(`<a id="…"></a>`), which is the only repair that also rescues the indexed
anchor URL, since no redirect can reach a fragment; where the section moved to
another page, the link was repointed.

**Two are left**, and both need someone who knows what the page meant, because
repairing either means writing a section that does not exist:

- `/docs/collaboration/#option-3-combining-git-and-shared-drives` — the page
  has no Option 3 any more and nothing on it describes combining the two. The
  link text is "mix".
- `/docs/synthetic-data-generation/generating-synthetic-data/#set-up-a-data-guide`
  — the Data Guide is mentioned twice in prose and has no section of its own.

They are listed in `ref/stale_anchors.txt`, one line per link, and excused from
validation. The alternative was `errorOnInvalidHashes: false`, which would have
switched off anchor checking for the whole site — and the anchors are the half
most likely to break, since the converter had to re-derive every heading slug.

The trade is that any allowlist can outlive the problem it describes and start
hiding new ones. So each line is **re-derived from reality on every build** by
`staleAnchorsStillStale()` in `scripts/build_integrations.mjs`, and the build
fails, naming the line, if it has stopped being true:

| What changed | Why it fails |
| --- | --- |
| The page is gone, or no longer carries that link | The link was fixed or removed; the line is dead |
| The target page no longer builds | The line is hiding a broken *page* link, not a stale anchor |
| The target page now has an element with that `id` | The heading came back |

Each entry excuses one link on one page, so the same dead anchor appearing on a
page that is not listed still fails — when three pages linked
`/docs/prompts/#prompt-generators`, all three needed their own line.

**Repairing one is: fix the link or add the heading, then delete its line.** The
build tells you to.

## Page QA

```sh
npm run qa                                   # static: the content sources
npm run qa -- --browser                      # + a real Chromium render of every built page
npm run qa -- --browser --base-url https://<preview>.pages.dev
```

`scripts/qa_pages.mjs` is the migration's substitute for a baseline. Phase 1 was
meant to capture the live GitBook site — its rendered text and a screenshot of
every page — so that per-page QA could be a diff; that capture never ran,
because egress to `docs.kiln.tech` is blocked from the build environment. This
asks a weaker but mechanical question instead: not "does this page still say
what GitBook said", but **"is anything on this page detectably wrong"**.

What it checks:

| Check | What it catches | Needs a browser |
| --- | --- | --- |
| Residual GitBook markup | `data-view="cards"`, `data-hidden`, `data-card-*`, `data-full-width`, `data-search`, `app.gitbook.com` links, `.gitbook/assets` paths — attributes that meant something to GitBook and nothing here. Fenced code blocks are skipped, so a page *documenting* the markup is not a defect. | no |
| Literal markup in rendered text | Markdown or HTML being *displayed* instead of interpreted: a visible `<figure …>`, an unrendered `![alt](path)` or `[text](url)`, a leftover `{% … %}`. This is the class nothing else catches — see [figures inside a list](#inside-a-numbered-or-bulleted-list). | yes |
| Page-level horizontal overflow | Anything that makes the page scroll sideways, naming the element responsible. An element clipped by a scrolling ancestor is not a finding, so a code block or a wide table that scrolls *inside its own box* is left alone. | yes |
| Images that did not load | Broken `src`, wrong path, missing file. Lazy images are forced eager and awaited first, so "below the fold" is not mistaken for "broken". | yes |
| Empty table columns | A column whose header and every cell are empty — what GitBook's hidden columns become. | yes |
| Console and page errors | Script errors and failed same-origin requests. | yes |
| Missing `title` / `description` | Asserted per page. | yes |

Every page is rendered at 1280px and at 375px, because the defects this found
were mostly mobile ones.

Findings print as failures; things it cannot verify print as **notes** and do
not fail — external images (`img.shields.io`, `github.com/user-attachments`)
are unreachable from this environment, and a check that cries wolf about them
gets ignored. Exit codes: `1` means it found something, `2` means it could not
finish, and in that case whatever it *did* find is still printed first.

**Playwright is not a dependency of this project** and `--browser` is opt-in.
It is a large package with a browser download attached, this is a docs site,
and CI already gates what must never regress. `--browser` resolves Playwright
from wherever it is installed and says so plainly when it is not there, rather
than failing with a stack trace — and it still prints the static findings it
already has. Install it with:

```sh
npx playwright install chromium
```

`--base-url` points the same checks at a deployment instead of a local `dist`
— **worth re-running against the Cloudflare preview and against production**,
the same way [`verify_redirects.mjs`](#verifying-a-deployment) is. The page list
still comes from `dist`, so build first.

**It is deliberately not a CI gate.** CI has no browser, so the half worth
gating is the half that could not run there; the gates that must never regress
(build, link validation, the stale-anchor audit, the redirect verifier) are
already in CI, and the static half's job is to stop GitBook markup coming back
rather than to block a merge. Run it before a release, and after any change to
layout, images or CSS.

**What it cannot answer**, stated because it is the whole reason the phase plan
exists: content GitBook rendered that the markdown never contained, and whether
a page that is free of detectable defects is nonetheless a visual regression
against a design nobody here has seen. Only the baseline answers those, and it
is still outstanding — see [Still to do](#still-to-do).

`npm test` covers the detectors themselves; the sweep is not part of it.

## Continuous integration

`.github/workflows/ci.yml` runs on every pull request and on pushes to `main`:

```sh
npm ci
npm test                  # both suites
npm run redirects:check   # public/_redirects still matches redirects.csv
npm run build             # + link validation and the three post-build assertions
npm run verify:redirects -- --dist dist
```

Node comes from `.nvmrc` **at the repo root**, which is also the file
Cloudflare Pages reads — one pin, so CI cannot pass on a Node the deploy will
not use.

`npm run qa` is deliberately absent: the half of it worth gating needs a
browser, and CI has none — see [Page QA](#page-qa).

Most of the gating happens inside `npm run build`, because that is what
Cloudflare runs too: link validation, the stale-anchor audit, the `dist/_headers`
writer, and the assertion that no unoptimized image originals leaked into
`dist/_astro`. CI adds the unit suites and the two redirect gates around it.

`.github/workflows/verify-preview.yml` covers what only a real deployment can
answer — see [Verifying a deployment](#verifying-a-deployment).

## Still to do

- **The redirect inventory is incomplete.** It is built from GitBook's sitemap
  plus an inferred alias pattern. The live-site crawl, alias probe and Search
  Console export have not landed — see
  [Adding to the inventory](#adding-to-the-inventory).
- **No WYSIWYG editor.** Starlight pairs with git-backed CMSes such as
  [Keystatic](https://keystatic.com/) or [TinaCMS](https://tina.io/); neither
  is wired up.
- **Analytics is wired but off.** It needs a Cloudflare Web Analytics site
  token — see [Analytics](#analytics).
- **There is no Cloudflare Pages project yet.** Everything the deployment needs
  is committed and CI is green, but nobody has created the project or seen a
  real preview — see
  [Deploying to Cloudflare Pages](#deploying-to-cloudflare-pages).
- **The live-site baseline was never captured.** Egress to `docs.kiln.tech` is
  blocked from this environment, so no page has been diffed — in text or in a
  screenshot — against the GitBook original. The mechanical sweep in
  [Page QA](#page-qa) reduces what such a diff has to find; it does not replace
  it, and it cannot see content GitBook rendered that the markdown never
  contained.
- **2 anchors are still broken**, inherited from GitBook and excused from link
  validation until someone writes the missing sections —
  `#option-3-combining-git-and-shared-drives` in `docs/collaboration/index.md`
  and `#set-up-a-data-guide` in
  `docs/synthetic-data-generation/generating-synthetic-data.md`. See
  [Link validation](#link-validation). The other 22 were repaired.
- **The favicon and OG image are placeholders.** There is no Kiln logo in this
  repo to build them from — see
  [Social preview and favicon](#social-preview-and-favicon).

## Troubleshooting

**`npm run dev` fails intermittently** with
`Class extends value undefined is not a constructor or null`, or similar
module errors pointing inside `node_modules/astro/`, while `npm run build`
works. The code is fine; the install is being modified underneath the dev
server.

The usual cause is a file-syncing client (Dropbox, iCloud Drive, OneDrive,
Google Drive) rewriting files under `node_modules` while Vite reads them. The
dev server imports modules lazily, one request at a time, so it sees whatever
half-synced state exists at that moment — which is why it fails sometimes and
not others. `astro build` reads everything in a single pass up front and
usually survives.

First reinstall from the lockfile:

```sh
cd site
rm -rf node_modules
npm ci
```

If it recurs, exclude the build directories from syncing. On macOS Dropbox:

```sh
xattr -w com.dropbox.ignored 1 site/node_modules
xattr -w com.dropbox.ignored 1 site/dist
xattr -w com.dropbox.ignored 1 site/.astro
```

Moving the checkout outside the synced folder entirely also works, and is the
more reliable option.

Meanwhile, `npm run serve` builds and serves the static output in one step and
does not depend on the dev server.

**`Could not find requested image`** at build time means a markdown image path
does not resolve. Check the number of `../` segments and check the filename for
spaces — see [Images](#images).

## Deploying to Cloudflare Pages

`npm run build` emits a fully static `site/dist`. There is no server, no
database and no external search service — Pagefind is built at build time — so
deployment is "upload a directory", plus three text files Cloudflare reads out
of it: `_redirects`, `_headers` and `404.html`.

### Before cutover: things only a human can do

None of these can be done from a sandbox. They are ordered so that each one is
possible when you reach it: the expiring one first, then the Pages project, then
everything that needs the project to exist.

**Do this one first — it expires.**

- [ ] **Fetch one `.md` URL from the live GitBook site**, e.g.
      `curl -sI https://docs.kiln.tech/docs/quickstart.md`, to confirm the
      spelling the `.md` endpoints reproduce. The endpoints reproduce a URL
      family nobody has ever probed; the decision was argued from the sitemap,
      not from an observation. If the spelling differs the fix is one line in
      `src/pages/[...slug].md.ts` plus a `redirects.csv` refresh. **This is the
      last moment it is physically possible** — once GitBook is decommissioned
      the evidence is gone permanently, and it does not depend on anything else
      here.

**Then set up the deployment.**

- [ ] **Create the Cloudflare Pages project** and connect it to this repo, with
      the settings in [Project settings](#project-settings). Nothing below can
      be checked until this exists.
- [ ] **Set the Cloudflare Web Analytics token** while you are in the
      dashboard. Create a Web Analytics site for `docs.kiln.tech`, then set
      `CLOUDFLARE_ANALYTICS_TOKEN` as a Pages build environment variable, on
      **both** production and preview. Without it the site deploys with no
      analytics at all — see [Analytics](#analytics).
- [ ] **Confirm the deployment checks actually ran on the first preview.**
      `.github/workflows/verify-preview.yml` is triggered by
      `deployment_status`, which has never fired here because there was no
      Pages project when it was written.

      **Present and green is not the same as run.** `deployment_status` fires
      on every state transition, and the job's condition lets only a
      *successful* deployment, in an environment named for Cloudflare, through.
      So a perfectly healthy deploy produces several workflow runs whose
      "Verify a deployment" job is **Skipped** — and a skipped job reports
      success. A broken setup looks identical at a glance.

      What to look for: a run in which "Verify a deployment" **executed its
      steps**, with "Every inventoried URL resolves on the deployment" showing
      `176 paths` and green. Two ways it can be missing, with different fixes:

      - **No "Verify deployment" runs exist at all.** Cloudflare's GitHub App
        is not creating Deployments — re-authorize the Pages integration, and
        check the workflow is on `main`. Nothing about this repo will fix it.
      - **Runs exist but the job is Skipped in every one.** The job condition
        is not matching. The deployment's `environment` is the first thing to
        check: the workflow expects a name ending in `Preview` or
        `Production`. Cloudflare spells it `<project-name> (Preview)`, but that
        was never verified against a real payload and no linter checks it.
        Open the run's `deployment_status` payload, read the actual name, and
        adjust the condition.

      Until either is settled, run the workflow by hand — see
      [Verifying a deployment](#verifying-a-deployment).

**Then, before the site becomes the public one.**

- [ ] **Replace `public/favicon.svg` and `public/og.png`.** Both are
      placeholders built from type and the site's palette, because **there is
      no Kiln logo anywhere in this repo or its git history**. They are what
      every share card and browser tab will show — see
      [Social preview and favicon](#social-preview-and-favicon).
- [ ] **Read the two descriptions nobody at Kiln wrote.**
      `docs/structured-data-json.md` and `docs/keyboard-shortcuts.md` had none
      in GitBook, so the copy in them is ours. Thirty seconds each.
- [ ] **Check the static-redirect rule cap against current Cloudflare docs.**
      `MAX_RULES` in `scripts/build_redirects.py` is 2,000, taken from the
      architecture with a note to confirm it. We emit 84, so the margin is
      large and this is bookkeeping rather than risk.

Then work through [Cutover](#cutover), which is the ordered procedure rather
than a checklist. One thing to know before you start it: the sitemap to submit
to Search Console is **`https://docs.kiln.tech/sitemap-index.xml`**, not
`/sitemap.xml` — that one is a redirect kept for the URL Search Console already
has on file.

### Project settings

| Setting | Value |
| --- | --- |
| Build command | `cd site && npm run build` |
| Build output directory | `site/dist` |
| Root directory | *(repo root — leave unset)* |
| Node version | From `.nvmrc` at the repo root. Set `NODE_VERSION` to the same value as a belt-and-braces fallback: some Pages projects default to a Node far older than Astro 7's floor of 22.12. |
| Environment variables | `CLOUDFLARE_ANALYTICS_TOKEN`, on **both** production and preview — see [Analytics](#analytics). |

`.nvmrc` lives at the repo root rather than in `site/` precisely because the
build command starts from the repo root, so that is where Cloudflare looks. CI
reads the same file.

Preview deployments are on by default for pull requests once the repo is
connected; production builds from `main`.

The build needs **no Python**. `public/_redirects` is committed rather than
generated at deploy time, so the rules that ship are the rules reviewable in
git, and `npm run redirects:check` in CI is what keeps the two in step.

### Verifying a deployment

Everything CI can prove offline, it already has. What is left needs the real
host: whether Cloudflare applies `_redirects`, whether it honours `_headers`,
and which of a static asset and a redirect rule wins.

`.github/workflows/verify-preview.yml` runs those three checks — the redirect
verifier without `--dist`, so the *server* has to do the redirecting; the
`Content-Type` on a `.md` endpoint; and the status a slashless path answers
with. Trigger it by hand from the Actions tab against any deployment URL:

> Actions → **Verify deployment** → Run workflow → paste the URL

**Run it from the branch that produced the deployment.** The URL is checked
against the `redirects.csv` in whatever ref you dispatch from — dispatching
from `main` against a PR's preview compares one commit's inventory with another
commit's site, and any disagreement is reported as a redirect failure. The
automatic trigger has no such trap: it checks out
`github.event.deployment.sha`, the commit that was actually deployed.

Or run the same checks locally:

```sh
npm run verify:redirects -- --base-url https://<preview>.pages.dev
curl -sI https://<preview>.pages.dev/docs/quickstart.md   # want: text/markdown
curl -sI https://<preview>.pages.dev/docs/quickstart      # want: 301, or 308
```

That last one is the open question from the migration: a **301** means our
`_redirects` rule ran, a **308** means Cloudflare's own trailing-slash
normalisation got there first. Both are fine. A **200** is not — it would mean
Cloudflare serves the page at a URL that disagrees with its own canonical tag,
and the verifier above fails on it too.

Also worth an eye on the first preview, none of which is automated:

- the 404 page, by requesting a path that does not exist
- search, which is a separate Pagefind bundle
- the OG image, via any card-preview debugger

### Cutover

The order matters, and every step before the last is reversible.

1. **Deploy to preview and verify it**, as above. Do not skip the manual look
   at the 404 page and search.
2. **Add `docs.kiln.tech` as a custom domain** on the Pages project. Cloudflare
   walks through the DNS record; if the zone is already on Cloudflare it is one
   click.
3. **Point DNS at the Pages project.** This is the only irreversible-feeling
   step, and it is not really — the record can be pointed back at GitBook.
4. **Re-run the verification against production**, without `--dist`, before
   telling anyone. A rule that worked on `*.pages.dev` and not on the custom
   domain would be a surprise, but this is a two-minute check.
5. **Submit `https://docs.kiln.tech/sitemap-index.xml`** to Search Console and
   watch the coverage report. A 404 spike means the redirect map has a gap —
   the inventory is built from GitBook's sitemap plus an inferred alias
   pattern, so gaps are expected rather than surprising. Add the missing URLs
   as `gsc` rows and re-run; see
   [Adding to the inventory](#adding-to-the-inventory).
6. **Confirm analytics is receiving data** before assuming the token is right.
7. **Keep GitBook running** until all of the above is settled. Only then
   decommission the space and cancel the subscription — at which point the
   `.md` URL evidence and the live-site baseline are gone permanently.
