# Kiln docs on Astro Starlight (WIP prototype)

A working proof-of-concept port of these docs off GitBook and onto
[Astro Starlight](https://starlight.astro.build/), building to a static site
that can be hosted on Cloudflare Pages.

The GitBook content in this repo is untouched. This directory reads it and
generates a Starlight site from it.

## Try it locally

Requires Node 20+ and Python 3.

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

## Switching themes

Starlight themes are plugins, so the visual design is one env var. Set
`DOCS_THEME` on either `dev` or `build`:

```sh
npm run dev                    # black (the default)
DOCS_THEME=nova npm run dev    # nova
DOCS_THEME=none npm run dev    # stock Starlight, no theme
```

| Value | Theme | Notes |
| --- | --- | --- |
| `black` (default) | [starlight-theme-black](https://github.com/adrian-ub/starlight-theme-black) | shadcn-inspired. Adds a top nav bar and a per-page "Copy page" menu with open-in-ChatGPT/Claude actions. |
| `nova` | [starlight-theme-nova](https://github.com/dinesh-b-mahato/starlight-theme-nova) | A more polished take on stock Starlight; keeps collapsible sidebar groups. |
| `none` | — | Stock Starlight. |

Themes are configured in `astro.config.mjs`. Adding another is an npm install
plus one entry in the `THEMES` map.

`src/styles/theme-black-fixes.css` loads only under `DOCS_THEME=black`. It
fixes a real bug in that theme: sidebar links are given a fixed `30px` height
against a `22.4px` line-height, so any label wrapping to two lines overflows
its box and collides with the next entry. Three of our sidebar labels hit it
("Evaluate RAG Accuracy: Q&A Evals", "Evaluate Appropriate Tool Use", "Input
Templates & Feature Engineering"). The override lets the box grow.

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

## Deploying to Cloudflare Pages

`npm run build` emits a fully static `site/dist`. Point Cloudflare Pages at
this repo with build command `cd site && npm run build` and output directory
`site/dist`. Search (Pagefind) is built at build time, so there is no Algolia
account or other external service to set up.
