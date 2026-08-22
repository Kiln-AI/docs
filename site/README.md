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
confusing module errors).

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
| `src/assets/**` | Images. Referenced from pages with relative markdown links, which is what puts them through Astro's image pipeline. |
| `public/assets/**` | Videos, and the handful of images referenced from raw HTML. Served verbatim. |
| `sidebar.json` | The sidebar, read by `astro.config.mjs`. |
| `astro.config.mjs` | Site config, theme, nav. |
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

```sh
# last commit carrying the GitBook tree
git worktree add /tmp/gitbook 3e16f5af77fc0e0e27a6785ec78a5f6c1761a889
# today's converter, not the one the worktree checked out
cp site/scripts/gitbook_to_starlight.py /tmp/gitbook/site/scripts/
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

### Tests

```sh
npm test
```

Unit tests for the converter live in `scripts/test_gitbook_to_starlight.py`
(stdlib `unittest`, no extra dependencies). They cover the parts that are easy
to get subtly wrong and hard to eyeball: the github-slugger port, anchor
remapping, link and asset rewriting, figure conversion, asset naming, and YAML
frontmatter scalars.

## Still to do

- **No redirects yet.** GitBook URLs that change need rules in
  `public/_redirects`.
- **No WYSIWYG editor.** Starlight pairs with git-backed CMSes such as
  [Keystatic](https://keystatic.com/) or [TinaCMS](https://tina.io/); neither
  is wired up.

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

`npm run build` emits a fully static `site/dist`. Point Cloudflare Pages at
this repo with build command `cd site && npm run build` and output directory
`site/dist`. Search (Pagefind) is built at build time, so there is no Algolia
account or other external service to set up.
