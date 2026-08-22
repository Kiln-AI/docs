---
status: draft
---

# Phase 3: Go Astro-Native

## Overview

Until now the Starlight site has been a *view* of the GitBook tree: every build
re-ran `gitbook_to_starlight.py`, which deleted and regenerated
`site/src/content/docs/`, `site/src/assets/`, `site/public/assets/` and
`site/sidebar.json`, all four of them gitignored. This phase flips the source of
truth. After it, `site/src/content/docs/**` is committed, hand-maintained
content; the GitBook tree is gone; and an ordinary `npm run build` is nothing
but `astro build`.

Four things have to happen in one commit, because each one breaks the others if
it lands alone:

1. The transformer runs a final time and its output is committed.
2. `npm run convert` is unwired from `build` and `dev`.
3. Referenced images move into `site/src/assets/` and go through Astro's image
   pipeline; referenced videos move into `site/public/assets/`; the 75
   unreferenced assets are dropped.
4. The GitBook source tree is deleted.

The transformer itself stays (phase 9 deletes it), and it stays *correct*: the
new output shape is produced by the converter, not by hand-editing its output,
so the phase 9 reconciliation converts new pages into the same shape the corpus
already uses.

## Findings that change the plan

### Astro's image pipeline cannot resolve filenames containing spaces

The architecture says referenced images move to `src/assets/` and are referenced
with relative markdown links so Astro optimizes them. Verified by spike: that is
true, and the optimizer produces `<img>` with WebP `src` and intrinsic
`width`/`height`. But **most of the referenced images have spaces, parentheses
or U+202F in their filenames** (GitBook stored macOS screenshots verbatim), and
Astro cannot resolve those:

```
[ImageNotFound] Could not find requested image `../../assets/two words.png`. Does it exist?
```

Reproduced with a plain space, with the path percent-encoded (`two%20words.png`)
and with an angle-bracket destination (`![](<../../assets/two words.png>)`).
`remark-collect-images` `decodeURI`s the destination and hands the literal
string to Vite's importer, which does not find it. This is not something
encoding can work around.

**Decision:** sanitize filenames on the way into `src/assets/`.
`safe_asset_name()` maps every run of characters outside `[A-Za-z0-9._-]` to a
single `-`, collapses repeats, strips leading/trailing `-`/`.`, and lowercases
the extension. Over the 68 images that land in `src/assets/`: 22 unchanged, 46
renamed, **zero collisions**, and no collision with `hero.png`. The converter
raises on a collision rather than trusting that.

Videos keep their original names — they live in `public/`, are referenced by
absolute URL, and percent-encoding works there.

### `<figure>` conversion: width goes on the figure, not the image

The architecture's constraint holds exactly: `rehype-images` only rewrites
`<img>` nodes whose `src` was collected by `remark-collect-images`, and that
plugin only visits mdast `image`/`imageReference` nodes. Raw HTML `<img>` is
never optimized.

All 68 image-bearing `<figure>` blocks are mechanically uniform — attributes are
only `src`, `alt` and optional `width`; no attributes on `<figure>` itself; all
35 non-empty captions are a bare `<figcaption><p>text</p></figcaption>`. So they
convert to:

```markdown
<figure style="max-width:375px">

![alt](../../../assets/screenshot-2025-01-08-at-12.38.31-pm.png)

<figcaption><p>Kiln's Visual Schema Editor</p></figcaption>
</figure>
```

The blank lines matter: a CommonMark HTML block ends at a blank line, so the
image is parsed as markdown (and optimized) while still nesting inside the
`<figure>` in the output HTML. Spike-verified against a real build:

```html
<figure style="max-width:375px">
<p><img alt="" loading="lazy" decoding="async" width="1522" height="412"
        src="/_astro/json.Crh_6yZY_1JCSy9.webp"></p>
<figcaption><p>Kiln's Visual Schema Editor</p></figcaption>
</figure>
```

The architecture says "re-express width constraints in CSS rather than per-image
attributes", and its fallback is "keep it as HTML and accept it skipping the
optimizer". **Neither is needed.** Moving `width="375"` to
`style="max-width:375px"` on the wrapping `<figure>` is CSS, keeps the image in
markdown syntax so it *is* optimized, and preserves each image's own width
exactly. A single shared CSS class would be worse: the 44 widths span 179–375px
across 12 distinct values, so one rule would visibly resize a dozen narrow
screenshots. Zero figures fall back to raw HTML.

### Ten images stay in `public/`, all for the same reason

Astro only rewrites markdown image nodes, so an asset referenced any other way
has to keep an absolute `/assets/…` URL out of `public/`. Ten do:

- **Nine GitBook card-table covers.** In `docs/optimizers.md` and
  `docs/fine-tuning/README.md`, `<table data-view="cards">` names its cover
  images as `<a href="../.gitbook/assets/tuning2.png">tuning2.png</a>` — link
  targets, not images. Phase 2 already recorded these tables as a phase 7
  rendering job (they currently render as plain 4-column tables with raw
  filenames as link text). When phase 7 turns them into real card grids the
  covers become images and can move to `src/assets/`; forcing it now would mean
  a relative path in an `href`, which resolves against the page URL and 404s.
- **One centered, link-wrapped screenshot**, the corpus's only `<img>` outside
  a `<figure>`:

  ```html
  <p align="center"><a href="end-to-end-project-demo.md"><img src="../.gitbook/assets/Screenshot 2025-07-28 at 11.26.08 AM.png" alt="Download button"></a></p>
  ```

  Centering plus a link wrapper is not expressible in markdown. This is the
  architecture's escape hatch, and inventing a transformer rule for a single
  occurrence is not worth it.

So 68 of the 78 page-referenced images are optimized, and the remaining ten are
tracked against phase 7 rather than worked around.

### The landing page moves out of `src/landing/`

`src/landing/index.mdx` existed only because the converter deleted and rebuilt
`src/content/docs/` on every run, so the hand-written landing page had to be
staged somewhere else and copied in. With the content committed, that staging
directory is a footgun: two files, one of which is silently authoritative.

`src/landing/index.mdx` becomes `src/content/docs/index.mdx` — an ordinary
page — and the converter's landing-page copy step goes away with it. Nothing
else in the converter referenced `src/landing/`.

### `editLink` is wrong today for a different reason than expected

Starlight builds the edit URL as `baseUrl + entry.filePath`, and `filePath` is
relative to the **Astro project root**, not the repo root. The built site
currently emits
`https://github.com/Kiln-AI/docs/edit/main/src/content/docs/docs/agents.md`,
which 404s — the path is missing the `site/` segment. Fixing the base URL to
`.../edit/main/site/` makes it correct both before and after this phase.

## Asset inventory — showing the working

Counted with the converter's own `MD_LINK` and `HTML_ATTR` patterns (a looser
regex mis-splits `Eval (1).png` at the space and picks up
`github.com/user-attachments/...`), destinations percent-decoded, over:

- every file in `site/src/content/docs/**` (the converted output),
- the hand-written landing page,
- `site/astro.config.mjs`, `site/src/styles/custom.css`, `site/sidebar.json`,
- `README.md` and `SUMMARY.md` (the two GitBook files that are not pages),

plus `App3.png`, which nothing references by name but which the converter copies
to `src/assets/hero.png` for the landing page hero.

| | Count |
| --- | --- |
| Files in `.gitbook/assets` | 159 |
| Referenced | 84 |
| — markdown images → `site/src/assets/` (sanitized names, optimized) | 68 |
| — hero `App3.png` → `site/src/assets/hero.png` | 1 |
| — videos → `site/public/assets/` (original names) | 5 |
| — card covers and the centered screenshot → `site/public/assets/` | 10 |
| Unreferenced, deleted | **75** |
| Referenced but missing on disk | 0 |

75 rather than the architecture's estimated ~73: that estimate counted
references in the *GitBook source*, and the source's `README.md` — GitBook's
landing page, replaced by the hand-written `index.mdx` — carries four card
covers (`Video-2.png`, `providers3.png`, `python3.png`, `synth.png`) that
nothing on the new site uses.

The delete list includes both oversized videos — `final_1080.mp4` (38 MB) and
`final_1080p_web_fast_start.mp4` (27 MB) — which is what clears Cloudflare
Pages' 25 MiB per-file limit. The largest surviving file is `Datagen720.mp4` at
4.8 MB. The full 75-name list is printed by the converter (step 6) and is
recoverable from git history at any time.

`prune_assets.py` from the architecture is **not written**. It was specified to
delete orphans out of `.gitbook/assets`, and this phase deletes that entire
directory — a standalone script whose only job is to remove files that are about
to be removed anyway would be dead on arrival. Its two required behaviours are
kept where they belong: the converter already fails the run on a referenced
asset that does not exist on disk (phase 2, defect 3), and it now *reports* the
orphan list rather than silently dropping it.

## Steps

### 1. `site/scripts/gitbook_to_starlight.py` — asset destinations

Split the single `asset_url()` into the two destinations an asset can now have,
and record which assets are actually used so the copy step can be selective.

```python
def safe_asset_name(name):
    """Asset filename -> a name Astro's image pipeline can resolve.

    Vite resolves a markdown image destination as a literal path, so a space
    anywhere in the filename fails the build no matter how it is encoded.
    """

def public_asset_url(name):        # unchanged behaviour: "/assets/" + quote(name)

def src_asset_path(name, relpath):
    """Relative path from a converted page to site/src/assets/<safe name>."""
    return "../" * (out_for(relpath).count("/") + 2) + "assets/" + safe_asset_name(name)
```

`Conversion` gains `image_assets` and `public_assets` (sets of real on-disk
filenames) and two methods that resolve, record and format in one step:

```python
def image_asset(self, relpath, name):   # -> src_asset_path, records in image_assets
def public_asset(self, relpath, name):  # -> public_asset_url, records in public_assets
```

Both go through the existing `resolve_asset`, so a missing file is still a fatal
error and the U+202F normalisation still applies.

### 2. `rewrite_target` learns whether it is rewriting an image

A markdown *image* destination gets the relative `src/assets` path; every other
reference to an asset (raw HTML `src`/`href`, a markdown link whose target is an
asset) gets the `public/assets` URL, because Astro only rewrites markdown image
nodes.

`rewrite_target(target, relpath, ctx, page_url, is_image=False)`; the
`.gitbook/assets/` branch picks `ctx.image_asset` or `ctx.public_asset`.

`MD_LINK` is left exactly as it is. Whether a given `](…)` belongs to an image
is decided by walking backwards from the `]` to its matching `[`:

```python
def is_image_destination(text, close):
    """Is the `]` at index `close` the end of an image's alt text?"""
```

Rewriting `MD_LINK` to capture a leading `!` instead would look simpler but
silently stops matching the outer destination of a nested `[![alt](a)](b)` —
the corpus has one, in `docs/quickstart.md`, and both of its targets happen to
be external, which is exactly the kind of near-miss that becomes a broken link
the next time someone writes one.

`embed_html(url, relpath, ctx)` routes its `files.gitbook.com` video fallback
through `ctx.public_asset` instead of formatting the URL itself. That registers
the five videos for the copy step and, incidentally, gives them the
missing-asset check they never had.

### 3. `<figure>` blocks become markdown images

A new pass in `convert`'s `prose()`, running **before** `rewrite_references` so
that all asset resolution stays in one place — the pass is a pure structural
transform on GitBook's own HTML:

```python
FIGURE_IMAGE = re.compile(
    r'<figure><img src="(?P<src>[^"]*)" alt="(?P<alt>[^"]*)"'
    r'(?: width="(?P<width>\d+)")?>'
    r'(?:<figcaption>(?P<caption>.*?)</figcaption>)?</figure>')
```

emits

```
<figure[ style="max-width:Npx"]>

![alt](<src>)

[<figcaption>caption</figcaption>]
</figure>
```

with the destination always angle-bracketed, since the source filenames contain
spaces. `rewrite_references` then turns that destination into the relative
`src/assets` path. Runs inside `outside_code`, like everything else in `prose`.

Captioned `{% embed %}` figures are built by `convert_embeds` and are *not*
matched (no `<img>`), so the 8 video figures keep their current HTML.

### 4. `main()` copies only what is referenced

Replace `shutil.copytree(GITBOOK_ASSETS, ASSETS_OUT)` with a selective copy:

- `site/src/assets/<safe name>` for each name in `ctx.image_assets`
- `site/public/assets/<name>` for each name in `ctx.public_assets`
- `site/src/assets/hero.png` from `HERO_SOURCE`, as today

`safe_asset_name` collisions raise `SystemExit` rather than letting one image
silently overwrite another. Both output directories are cleared first, so a
re-run cannot leave a stale file behind. Afterwards the run prints the count and
the full list of unreferenced assets it did not copy.

The landing-page copy step goes away in the same place (see findings): the
landing page is now an ordinary committed page, not something staged elsewhere
and copied in. The module docstring and `path_within`'s scope note are updated
to match — the latter matters, because phase 9 reads it to know which paths the
`--out` write-time containment check covers.

### 5. `site/src/styles/custom.css`

The optimized image now sits inside a `<p>` that CommonMark generates inside the
`<figure>`. Zero the margins so the figure keeps its current spacing:

```css
.sl-markdown-content figure p { margin: 0; }
```

The existing `figure`/`figcaption`/`img` rules are unchanged.

### 6. Run the converter for the last time

`npm run convert`, while `site/src/content/docs/` is still untracked — the phase
2 git backstop refuses the default run the moment it is committed, so this has
to happen before step 8. Then `npx astro build` to confirm 47 pages and no
`ImageNotFound`.

Snapshot the generated tree to a scratch directory outside the repo, so step 9
can `git mv` the GitBook sources onto those paths and then restore the converted
content.

### 7. Unwire `convert` from the build — `site/package.json`

```json
"dev": "astro dev",
"build": "astro build",
```

`convert` stays as a standalone script for phase 9. This is the actual fix the
phase 2 backstop was standing in for.

### 8. Un-gitignore the generated paths — `site/.gitignore`

Delete the four entries under "Everything below is generated by `npm run
convert`": `src/content/docs/`, `src/assets/`, `public/assets/`, `sidebar.json`.
`node_modules/`, `dist/` and `.astro/` stay.

### 9. Move the content, delete the GitBook tree

`git mv` for every path that maps cleanly, then restore the converted content
from the step 6 snapshot over the moved file:

| From | To |
| --- | --- |
| `docs/<name>.md` | `site/src/content/docs/docs/<name>.md` |
| `docs/<dir>/README.md` | `site/src/content/docs/docs/<dir>/index.md` |
| `developers/<name>.md` | `site/src/content/docs/developers/<name>.md` |
| `.gitbook/assets/<image>` | `site/src/assets/<safe name>` |
| `.gitbook/assets/<video or HTML-referenced image>` | `site/public/assets/<name>` |
| `site/src/landing/index.mdx` | `site/src/content/docs/index.mdx` |

`git rm` for the rest: `README.md` (GitBook's landing page, replaced by the
hand-written `index.mdx`), `SUMMARY.md` (replaced by `sidebar.json`), and the
75 unreferenced assets. `.gitbook/` is then empty and disappears.

Git stores no rename records — `git log --follow` recovers them by content
similarity — so `git mv` and `rm`+`add` produce byte-identical commits here.
Using `git mv` anyway keeps the deletion and the addition staged together, which
is what makes the diff readable.

### 10. `site/astro.config.mjs`

- `editLink.baseUrl` → `https://github.com/Kiln-AI/docs/edit/main/site/` (see
  findings).
- The `sidebar.json` comment and its failure message both say the file is
  generated and tell the reader to run `npm run convert`. It is now committed
  content; say so.

### 11. Rewrite `site/README.md`

It currently opens "A working proof-of-concept port … The GitBook content in
this repo is untouched", documents `npm run dev` as running the converter first,
and carries a "What is not done yet" section whose first three entries this
phase closes. Rewrite it around the site as it now is:

- `src/content/docs/**` is the content, edited directly; `npm run dev` /
  `npm run build` are plain Astro commands.
- Images live in `src/assets/` and go through Astro's optimizer; the figure
  markup convention and why the blank lines are load-bearing; videos and the one
  centered image live in `public/assets/`.
- `sidebar.json` is committed and hand-edited.
- The transformer section shrinks to what it is now: a one-shot migration tool
  kept only for the phase 9 reconciliation, run with `--out DIR`, refusing the
  default run over committed content. The `--out` safety notes stay — phase 9
  depends on them.
- Keep the theme, sidebar-workaround, tests, troubleshooting and Cloudflare
  sections. Drop the resolved items from "What is not done yet" and keep
  redirects and the CMS note.

## Tests

28 new cases in `site/scripts/test_gitbook_to_starlight.py`, taking the suite
from 93 to 121. Fixtures only — nothing here reads the live corpus or `.git`.

**Asset names** (`AssetNameTest`) — Astro resolves a markdown image path
literally, so the naming rule is load-bearing:

- `test_unsafe_runs_become_single_hyphens`,
  `test_narrow_no_break_space_is_folded_too` — the two real shapes, spaces plus
  parentheses and the U+202F screenshots.
- `test_a_clean_name_is_left_alone` — the 22 already-safe names must not churn.
- `test_extension_is_lowercased`.
- `test_near_collisions_stay_distinct` — `synth_data-2 (1).png` vs
  `synth_data-2 (2).png`.
- `test_src_asset_path_counts_the_page_depth` and
  `test_src_asset_path_follows_readme_to_index` — the `../` count for a
  top-level page, a one-deep page, a two-deep page, and a `README.md` that is
  written as `index.md`.

**Image vs. link destinations** (`AssetTest`) — which of the two asset trees a
reference lands in:

- `test_markdown_image_points_into_src_assets`,
  `test_html_img_src_stays_in_public_assets`,
  `test_markdown_link_to_an_asset_stays_in_public_assets` — each asserting both
  the emitted path and which set the asset was registered in.
- `test_nested_image_link_rewrites_both_destinations` — `[![alt](a)](b.md)`:
  the inner target is an image, the outer is not, and both are still rewritten.
  This is the case that rules out folding the `!` into `MD_LINK`.
- `test_missing_asset_is_still_fatal_for_a_markdown_image` — the phase 2
  guarantee holds on the new path.
- `test_angle_bracket_asset_link` and
  `test_asset_filename_containing_parentheses` updated to the new destinations.

**Figures** (`FigureTest`)

- `test_figure_becomes_a_markdown_image` — blank lines present, no `<img>` left.
- `test_width_moves_onto_the_figure_as_css`.
- `test_caption_is_preserved`, `test_empty_caption_leaves_no_figcaption`,
  `test_alt_text_is_preserved`.
- `test_a_filename_with_spaces_survives_the_handoff` — the figure pass hands a
  destination to `rewrite_references`, and a space has to survive the handoff,
  which is why it emits `<angle brackets>`.
- `test_embed_figure_keeps_its_html` — the 8 captioned video figures are not
  touched.
- `test_a_figure_inside_a_code_fence_is_untouched`.

**Videos** (`EmbedTest`)

- `test_gitbook_cdn_video_points_at_the_local_copy` extended: the video
  registers as a public asset, which is what gets it copied at all.
- `test_a_cdn_video_with_no_local_copy_is_reported` — new coverage. The video
  path never had an existence check.

**Copying** (`CopyAssetsTest`) — runs `main()` against a `fake_repo()` extended
with a plain image, an image whose name needs sanitizing, a video and an orphan:

- `test_referenced_assets_land_in_the_right_tree` — image in `src/assets` under
  its safe name, video in `public/assets` verbatim.
- `test_unreferenced_assets_are_not_copied_but_are_reported`.
- `test_the_original_assets_are_left_alone` — the copy never mutates
  `.gitbook/assets`.
- `test_the_hero_image_is_still_copied`.
- `test_a_stale_copy_does_not_survive_a_rerun`.
- `test_colliding_safe_names_fail_the_run`.
- `test_out_runs_copy_nothing` — `--out` still writes pages and nothing else.

## Verification

Whole-corpus checks, run against the committed state:

- `npm test` — 121 tests, green.
- `npm run build`, which is now plain `astro build` — 47 pages, 68 images
  optimized to WebP, no `ImageNotFound`.
- **Rendered figure nesting**, read out of `site/dist`:
  `<figure style="max-width:375px"><p><img … src="/_astro/….webp"></p><figcaption><p>…</p></figcaption></figure>`.
- **Every `<img src>` in `site/dist` resolves.** 68 point at `/_astro/*.webp`;
  the rest are the 5 external badge/attachment URLs and the one centered
  screenshot. No dangling file.
- **The two asset trees hold exactly what is referenced and nothing more.**
  `src/assets` — 69 files, all referenced (68 pages + `hero.png` from the
  landing page's frontmatter). `public/assets` — 15 files, all referenced. No
  dangling reference in either direction.
- **Link check over `site/dist`**: 46 pages, zero broken internal paths except
  `/favicon.svg`, which phase 2 recorded for phase 5. The converter still
  reports the same 24 stale source anchors — unchanged, as expected.
- **The backstop fires.** `npm run convert` now refuses with the `--out DIR`
  instruction, since `site/src/content/docs` is tracked. It is only reachable
  deliberately: `build` and `dev` no longer call it.
- Nothing in `site/` or the build output references `.gitbook/`, `docs/*.md`,
  `SUMMARY.md` or `src/landing/`.

## Carried forward

New findings, on top of the phase 2 list that phases 5 and 7 already inherit:

- **The "Copy page" markdown blob now carries relative image paths.** The
  theme embeds each page's raw markdown for its copy-to-clipboard and
  open-in-ChatGPT actions, so an external consumer sees
  `![](../../../assets/foo.png)` instead of a resolvable URL. It was
  `/assets/foo.png` before, which at least resolved against the origin. This is
  inherent to putting images through the optimizer — Starlight has no hook for
  rewriting paths in that blob — and belongs with the `llms.txt` work in phase
  5, which has the same problem to solve.
- **Nine card-cover images sit in `public/assets` waiting on phase 7.** When
  `<table data-view="cards">` becomes a real card grid, those covers become
  images and should move to `src/assets/` to pick up the optimizer. They are
  the only images on the site that skip it for a reason that is going to
  disappear.
