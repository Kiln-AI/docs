# Kiln docs on Astro Starlight (WIP prototype)

A working proof-of-concept port of these docs off GitBook and onto
[Astro Starlight](https://starlight.astro.build/), building to a static site
that can be hosted on Cloudflare Pages.

The GitBook content in this repo is untouched. This directory reads it and
generates a Starlight site from it.

## Try it locally

Requires **Node 22.12 or newer** (Astro 7's floor — older Node fails with
confusing module errors) and Python 3.

```sh
cd site
npm install
npm run dev
```

Then open <http://localhost:4321>.

`npm run dev` runs the converter first, so a plain `npm install && npm run dev`
is all you need. To build the static site instead:

```sh
npm run build     # output in site/dist
npm run preview   # serve site/dist locally
```

## Theme

The site uses [starlight-theme-black](https://github.com/adrian-ub/starlight-theme-black),
a shadcn-inspired Starlight theme. On top of stock Starlight it adds a top nav
bar and a per-page "Copy page" menu with open-in-ChatGPT/Claude actions.

Starlight themes are plugins, so it is configured in one place — the `plugins`
array in `astro.config.mjs` — and swapping it is an npm install plus editing
that array.

### Sidebar

By default the theme renders a flat sidebar: every group becomes a static
header with all its children always visible, and `collapsed` in the sidebar
config is ignored. Our `SUMMARY.md` has six nested groups that need to expand
and collapse, so the theme is configured with `sidebar: { useDropdowns: true }`
in `astro.config.mjs`, which renders groups as collapsible dropdowns with a
caret in the theme's own styling.

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

## How it works

`scripts/gitbook_to_starlight.py` reads the GitBook markdown at the repo root
and generates Starlight content. Everything it writes is gitignored, so the
site is always regenerated from the GitBook files as the source of truth:

| Generated | From |
| --- | --- |
| `src/content/docs/**` | `docs/`, `developers/` |
| `sidebar.json` | `SUMMARY.md` |
| `public/assets/**`, `src/assets/hero.png` | `.gitbook/assets/` |

Re-run it on its own with `npm run convert`.

What it converts automatically:

- 81 `{% hint style="…" %}` blocks into Starlight asides (`:::note`, `:::tip`,
  `:::caution`, `:::danger`)
- 14 `{% embed %}` blocks into Vimeo/YouTube iframes and local `<video>` tags
- `{% code %}` wrappers stripped (Expressive Code handles those options)
- `SUMMARY.md` into the sidebar, including nested groups
- Relative `.md` links into absolute site URLs, resolved per file
- The leading `# Heading` into Starlight's `title` frontmatter

The ~90 `<figure>` blocks are left as raw HTML and render as-is, `width`
attributes included.

## What is not done yet

This is a preview, not a migration.

- **The landing page** (`src/landing/index.mdx`) is hand-written, because
  GitBook's `<table data-view="cards">` has no automatic equivalent. It is the
  one page maintained by hand rather than generated.
- **Images skip Astro's optimizer.** They are copied to `public/assets/` and
  referenced absolutely, which works but forgoes automatic WebP and responsive
  sizing. Moving them into `src/assets/` with relative markdown links would
  turn that on — the hero image alone goes 63 kB → 2 kB through the pipeline.
- **Two videos exceed Cloudflare Pages' 25 MiB per-file limit**
  (`final_1080.mp4` at 38 MB, `final_1080p_web_fast_start.mp4` at 27 MB). They need to move
  to Cloudflare Stream, R2, or Vimeo before this can deploy.
- **Five `{% embed %}` blocks pointed at `files.gitbook.com` CDN URLs**, which
  stop working once the GitBook space goes away. The converter already
  repoints them at the local copies in `.gitbook/assets/`.
- **No redirects.** If any URLs change relative to the current GitBook site,
  they need redirect rules.
- **No WYSIWYG editor yet.** Starlight pairs with git-backed CMSes such as
  [Keystatic](https://keystatic.com/) or [TinaCMS](https://tina.io/); neither
  is wired up here.

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

If it recurs, exclude the generated directories from syncing. On macOS
Dropbox:

```sh
xattr -w com.dropbox.ignored 1 site/node_modules
xattr -w com.dropbox.ignored 1 site/dist
xattr -w com.dropbox.ignored 1 site/.astro
```

Moving the checkout outside the synced folder entirely also works, and is the
more reliable option.

Meanwhile, `npm run serve` builds and serves the static output in one step and
does not depend on the dev server:

```sh
npm run serve    # build + preview
```

**Converted far more pages than expected** (the count printed by
`npm run convert` should match the number of docs, currently 41) means the
converter picked up markdown it should have skipped, such as a stray
`node_modules` at the repo root. `SKIP_DIRS` in the converter controls this.

## Deploying to Cloudflare Pages

`npm run build` emits a fully static `site/dist`. Point Cloudflare Pages at
this repo with build command `cd site && npm run build` and output directory
`site/dist`. Search (Pagefind) is built at build time, so there is no Algolia
account or other external service to set up.
