---
status: draft
---

# Phase 7: Page-by-Page QA

## Overview

The implementation plan's bar for this phase is "every page must meet or exceed
the GitBook version", and its method is "work through all 45 pages against the
baseline text and screenshot diffs … prioritise by what the diffs flag".

**There are no diffs.** Phase 1 never ran in this environment — egress to
`docs.kiln.tech` is blocked by policy, a separate task is capturing the
baseline elsewhere — so `baseline/pages/*.txt` and `baseline/shots/*.png` do
not exist. The prioritisation mechanism this phase was designed around is
unavailable, and the live site must not be fetched.

So this phase substitutes a method, and states plainly what the substitute
does and does not prove.

### The substituted method

Three legs, in priority order.

**1. The recorded findings from phases 2–6.** These are specific,
evidence-backed and already triaged. They are the closest thing to a diff we
have, because each one was found by comparing converted output against the
GitBook source it came from. They are worked first.

**2. A mechanical defect sweep over the built site, in a real browser.** This
is the substitute for the screenshot diff. It cannot ask "does this look like
GitBook did", but it can ask "is anything on this page detectably wrong", and
that question catches most of what a screenshot diff would have flagged as a
red block. `scripts/qa_pages.mjs` renders all 46 built pages at a desktop and
a mobile viewport and reports:

| Check | What it catches |
| --- | --- |
| Page-level horizontal overflow | Anything that makes the page scroll sideways, with the offending element named. Ignores elements clipped by a scrolling ancestor, so a code block or table that scrolls *inside its own box* is not a finding. |
| Images that did not load | Broken `src`, wrong path, missing file. Lazy images are forced eager first, so "below the fold" is not mistaken for "broken". |
| Literal markup in rendered text | Markdown or HTML that survived conversion and is being *displayed* rather than *interpreted* — `<figure …>` as text, an unrendered `![alt](path)`, a `{% … %}` directive, a visible `[text](url)`. This is the class the phase 2 source diff structurally could not see. |
| Empty table columns | A column whose header and every cell are empty — GitBook's `data-hidden` columns, which Starlight has no reason to hide. |
| Console and page errors | Script errors, failed same-origin requests. |
| Missing `title` / `description` | The functional spec's fidelity bar, asserted per page. |
| Residual GitBook attributes in source | `data-view="cards"`, `data-hidden`, `data-card-*`, `data-full-width`, `data-search`, `app.gitbook.com` links, `.gitbook/assets` paths. Static, no browser needed. |

**3. Targeted reading of what legs 1 and 2 flag**, plus the pages adjacent to
each fix, rather than reviewing all 45 by eye. That is the plan's own
instruction, applied to a different signal.

### What this method cannot catch, and who inherits it

Stated explicitly because it is the honest limit of the substitution, and
because phase 8 is the deadline for closing it:

- **Content GitBook rendered that the markdown never contained.** GitBook
  synthesised page chrome, and its card-table widget rendered images that
  appear in the markdown only as `<a href>` link targets. If GitBook ever
  displayed something with no representation in the source at all, nothing in
  this phase can know it existed. Phase 2 recorded the same blind spot for its
  source diff.
- **"Renders at least as well as GitBook."** A page that is detectably free of
  defects may still be a visual regression against a design nobody here has
  seen. Every "meets or exceeds" claim in this phase is therefore a claim about
  *detectable defects only*, and is written that way.
- **Anything only a human eye ranks** — typography, image cropping, whether a
  screenshot is still current.
- **External images and embeds.** `img.shields.io`, `github.com/user-attachments`,
  Vimeo and YouTube are unreachable from this environment, so the sweep can
  only confirm the markup is correct, never that the resource is alive. The
  script classifies them separately rather than reporting them as broken.

When the baseline lands, the diff should still be run. This phase reduces what
it has to find; it does not replace it.

## Findings from the sweep

Run against the phase 6 build, before any fix in this phase. Every item below
was found by the method above, not assumed.

### A. `<table data-view="cards">` renders as a plain 4-column table

Inherited from phase 2, and the most visible defect on the site.
`docs/fine-tuning/index.md` and `docs/optimizers.md` carry GitBook's card-grid
widget as a raw `<table>`. Starlight passes it through, so both pages show an
ordinary table with a visible `Cover image` header and raw filenames
(`tuning2.png`, `fine-tuning-guide.md`) as the link text. Ten cards across two
pages. On mobile both tables overflow their column and have to be scrolled
sideways to read.

### B. Two figures inside a numbered list destroy the rest of the list

**Found by the sweep, not inherited — the highest-severity new finding.**

`docs/fine-tuning/fine-tuning-for-tool-use.md` lines 31 and 39 indent a
`<figure>` block by four spaces inside an ordered list item. The blank-line
convention that makes a figure work at the top level (README, "Screenshots with
a caption") does not survive there. In `dist` today:

- the list closes after item 3, mid-figure, leaving `<figure …>` orphaned and
  the image outside the list;
- **item 4 renders as literal text** `4.  Click "Add Fine-Tuning Data"…`;
- the second `<figure style="max-width:375px">` is four-space-indented in a
  context that is no longer a list, so CommonMark reads it as an **indented
  code block** and the page displays the raw HTML tag in a code frame with a
  copy button;
- **item 5 renders as literal text**, its markdown link included:
  `5. Generate synthetic training data using Kiln's [synthetic data gen](/docs/synthetic-data-generation/) tool.`

Nothing caught this. The build is green, every count matches, and
`starlight-links-validator` is silent precisely *because* the link stopped
being a link. It is the exact failure mode phase 3 documented for raw-space
image references, in a different disguise: **markdown that degrades to text
raises no error anywhere.** That is why the sweep scans rendered text.

### C. Pagination links overflow the viewport on mobile

`starlight-theme-black`'s `Pagination.astro` sets `white-space: nowrap` on both
links and lays them out in a non-wrapping flex row. Any long page title pushes
past the viewport and makes **the whole page** scroll sideways — the worst kind
of mobile defect, because it moves the body text off-screen too.

Measured at 375px, `document.scrollWidth` vs a 375px viewport:

| Page | scrollWidth | Label |
| --- | --- | --- |
| `/docs/issues/` | 542 | Reasoning & Chain of Thought |
| `/docs/synthetic-data-generation/generating-synthetic-data/` | 490 | — |
| `/docs/prompts/prompt-generators/` | 459 | — |
| `/docs/prompts/` | 450 | — |
| `/docs/evals-and-specs/code-judges/` | 408 | Evaluate RAG Accuracy: Q&A Evals |
| `/docs/evals-and-specs/evaluate-appropriate-tool-use/` | 390 | — |
| `/docs/evals-and-specs/evaluate-rag-accuracy-q-and-a-evals/` | 379 | — |

Seven pages. This is the "interactive polish of sidebar, header, and other
chrome" the phase scope names.

### D. The landing page hero overflows on mobile

`/` at 375px has `scrollWidth` 380. The theme constrains the hero image with
`.hero > img { width: min(70%, 20rem) }`, but in the `media-top` layout the
image is wrapped in a `.hero-image` div, so the child combinator misses it and
the image renders at its intrinsic 400px inside a 328px column.

### E. Ten `data-hidden` columns render as visible empty columns

Inherited from phase 2, confirmed by the sweep's empty-column check on
`/docs/evals-and-specs/`, `/docs/synthetic-data-generation/generating-synthetic-data/`
and `/docs/synthetic-data-generation/synthetic-data-guides/`. Seven `<th
data-hidden>` in five pages; four of the seven are in the two card tables and
disappear with them. Every hidden column's body cells are empty, so removal is
purely a rendering fix with no content to preserve.

On mobile these empty columns are not merely ugly: `/docs/evals-and-specs/`
measures 381px of table for 375px of viewport, and the whole excess is the
empty column.

### F. Card covers sit in `public/assets/`, unoptimized

Inherited from phase 3. Nine images, in `public/` only because they are
`<a href>` targets rather than images. They are the only images on the site
that skip Astro's optimizer, for a reason that disappears with finding A.
`rag icon 2-2.png` carries spaces and is referenced as
`/assets/rag%20icon%202-2.png`.

### G. `docs/tools-and-mcp/index.md` links a private GitBook URL

Line 138 links "model library" at
`https://app.gitbook.com/u/lbKlVk0pqscWejhogcdq9NRaUtP2` — a GitBook user
profile, which dies when phase 8 cancels the subscription. The intended target
is unambiguous: the same phrase is linked twice in
`docs/models-and-ai-providers.md` as `https://kiln.tech/model_library`, and
`docs/optimizers.md` uses the same URL for its "Compare Models" card.

### H. `data-full-width` and `data-search="false"` are inert

Two tables in `docs/skills.md` carry `data-full-width="true"`;
`docs/evals-and-specs/index.md` carries `data-search="false"`. Both were
GitBook rendering hints with no Starlight equivalent. Neither table is a
defect at either viewport — measured, not assumed — so this is a decision, not
a repair. See step 8.

### I. The 24 stale source anchors

Inherited from phase 2, allowlisted in `ref/stale_anchors.txt` by phase 6,
which recorded them as phase 7's to repair. 22 of the 24 have an unambiguous
correct target; two do not. See step 9.

### Checked and clean

Recorded so the next reader knows these were looked at rather than skipped:

- **No page is missing a `title` or a `description`** — including the two
  pages phase 5 wrote copy for.
- **Every same-origin image on every page loads**, at both viewports, once
  lazy loading is forced eager. The only images that do not load are the five
  external badges and the one `github.com/user-attachments` screenshot, which
  this environment cannot reach.
- **No console errors or page errors** on any page from same-origin code.
- **Code blocks and wide tables scroll inside their own boxes** at 375px
  rather than pushing the page sideways — checked by ignoring elements clipped
  by a scrolling ancestor, which is what separates C and D from the ten pages
  that merely contain something wider than the viewport.
- **The 404 page** was confirmed useful in phase 5; not re-litigated.
- **The favicon and OG image are typographic placeholders** and stay that way.
  There is no Kiln logo in this repo or its history, and inventing branding is
  worse than a placeholder. The README's "Still to do" entry stays.

## Steps

### 1. `site/scripts/qa_pages.mjs` — the sweep, as a committed tool

The substituted method has to be re-runnable, or it is an anecdote. One script,
two modes, no new npm dependencies:

```sh
node scripts/qa_pages.mjs                 # static checks over dist/ and src/content/docs
node scripts/qa_pages.mjs --browser       # the above, plus a real Chromium render of every page
node scripts/qa_pages.mjs --browser --base-url https://x.pages.dev
```

Shape follows `verify_redirects.mjs`, which is the closest existing tool: pure
exported functions that decide, a thin CLI that gathers and prints, and a
non-zero exit on findings.

```js
/** GitBook markup that survived conversion and now means nothing. @returns {Finding[]} */
export function residualGitbookMarkup(source)

/** Rendered text that should have been interpreted as markup. @returns {Finding[]} */
export function literalMarkupInText(text)

/** Columns where the header and every cell are empty. @returns {number[]} */
export function emptyTableColumns(rows)

/** Everything wrong with one page, from a plain observation object. @returns {Finding[]} */
export function pageFindings(observation)
```

The browser half collects facts (`observePage`) and the pure half judges them
(`pageFindings`), so every judgement is unit-testable without a browser and the
`page.evaluate` payload stays dumb.

Two details that decide whether the tool is honest:

- **Lazy images are forced eager and awaited** before they are judged. Without
  it the first pass reported 20 perfectly good screenshots as broken on 8
  pages, purely because they were below the fold.
- **An element wider than the viewport is only a finding if nothing clips it.**
  The check walks ancestors for `overflow-x: auto|scroll|hidden`. Without it
  every code block and every wide table is a false positive, which would have
  buried C and D under ten pages of noise.

Playwright is **not** added to `package.json`. It is a large dependency with a
browser download attached, this is a docs site, and CI already has the gates
that must never regress (build, links, anchors, redirects). The script resolves
it through `createRequire` so a global or `npx` install works, and says so
plainly when it is absent instead of failing:

```
--browser needs Playwright, which is not installed. Static checks ran; layout
checks did not. Install it with `npx playwright install chromium`, or drop
--browser.
```

`npm run qa` runs the static half. `npm test` gains the unit tests, not the
sweep.

### 2. Card grids — a real component, not a table

`src/components/CoverCard.astro`, modelled on Starlight's own `LinkCard` (same
`sl-link-card` idiom, same full-card `::before` click target, same hover
treatment) with a cover image above the title:

```astro
interface Props { title: string; href: string; cover: ImageMetadata; }
```

`cover` is an `ImageMetadata`, imported by the page and rendered through
`astro:assets`'s `<Image>`. Taking the metadata rather than a filename is what
keeps the covers on the ordinary optimized path — the same path markdown images
take — instead of the `import.meta.glob` + `getImage` route `page-markdown.ts`
had to invent, which pins unoptimized originals in `dist/_astro` and is guarded
by `optimizedImagesOnly()` for exactly that reason.

Layout reuses Starlight's `<CardGrid>`, already used by the landing page.

`docs/fine-tuning/index.md` and `docs/optimizers.md` become `.mdx`. That is
required — components need MDX — and it is what the landing page already does.
Consequences, checked rather than assumed:

- URLs are unchanged: `index.md` → `index.mdx` still builds `/docs/fine-tuning/`.
- The `.md` endpoints and the "Copy page" blob serve `entry.body`, which for
  MDX is the JSX source. For these two pages that is a strict improvement on
  today's single-line HTML table: a machine reading it sees a title, a
  description and an href per card instead of `<td><a href="…">tuning2.png</a></td>`.
- Phase 9's reconciliation converts to `.md`. If either page is ever
  reconciled, the converter's output must be merged into the `.mdx` by hand
  rather than copied over it. Recorded in "Carried forward" and in the README.

The seventh card in `optimizers.md` (`Skills`) has an empty target cell in the
GitBook source — no `<a>` at all. Its cover is `skills.png` and the page it
obviously wants is `/docs/skills/`, which exists and is in the sidebar. A card
that is not a link is worse than the table it replaces, so it gets that href;
recorded as a judgement call.

### 3. Covers into `src/assets/`

Move all nine from `public/assets/` to `src/assets/` with `git mv`, renaming
`rag icon 2-2.png` to `rag-icon-2-2.png` — `safe_asset_name()`'s output for it,
so the corpus keeps one naming rule. The other eight are already safe and keep
their names.

### 4. `data-hidden` columns

Delete each `<th data-hidden…>` and the matching trailing `<td></td>` from
every row, in the three tables that survive step 2. The cells are empty in the
source, so nothing is lost. `data-view`, `data-card-cover`, `data-card-target`
and `data-type` leave with the tables they annotate.

### 5. The list-item figures (finding B)

Indent the whole figure block — image and closing tag included — to the list
item's content column so it stays inside the item:

```markdown
3.  Select the set of tools that the model should learn to call.

    <figure style="max-width:375px">

    ![](../../../../assets/Screenshot-2026-01-08-at-8.07.16-PM.png)

    <figcaption><p>Selecting tools available to the fine-tuned model</p></figcaption>
    </figure>
```

At the content column the image is a paragraph rather than an indented code
block, so it parses as markdown and is optimized; the HTML block still ends at
the blank line; and the list is never closed early, so items 4 and 5 stay list
items and item 5's link stays a link.

The README's "Screenshots with a caption" section gains this case, because the
blank-line rule it already documents is necessary but not sufficient inside a
list.

### 6. Pagination overflow (finding C) — `src/styles/custom.css`

Let the links wrap instead of forcing them onto one line:

```css
.pagination-links { flex-wrap: wrap; gap: 0.5rem; }
.pagination-links a { white-space: normal; height: auto; min-height: 2rem; }
```

`white-space: nowrap` and a fixed `2rem` height are the pair that has to go
together: unsetting only the first would let the text wrap out of a box that
cannot grow. Same shape as the existing `a.entry-link` fix in this file, which
is the sidebar's version of the same mistake.

### 7. Hero overflow (finding D) — `src/styles/custom.css`

```css
.hero .hero-image img { max-width: min(70%, 20rem); height: auto; }
```

Restates the theme's own intent for the wrapper it does not reach, rather than
inventing a size.

### 8. `data-full-width` and `data-search` (finding H)

**Decision: delete both attributes, change no layout.**

`data-search="false"` asked GitBook not to index one table. Pagefind indexes
body text and has no per-element opt-out, and the table is a useful thing to
find. There is nothing to implement.

`data-full-width="true"` asked GitBook to break two tables out of the content
column. Both were measured at 1280px and 375px: neither overflows, neither
scrolls, both are readable. Building a full-bleed escape from Starlight's
content column — negative margins that have to dodge the right-hand table of
contents — to solve a problem that does not measurably exist is not worth the
regression surface. Recorded rather than done, so a human with the baseline
screenshots can overrule it with evidence.

Both attributes are removed because an inert attribute that looks like a
feature is worse than no attribute: it invites the next reader to implement it.
The QA script's residual-markup check then keeps them from coming back.

### 9. Stale anchors (finding I)

22 of the 24 have a target that the corpus itself identifies. Two do not, and
stay in the allowlist. Every repair deletes its line from
`ref/stale_anchors.txt`, which the build requires.

Two repair shapes, chosen by what actually happened to the section:

**(a) The heading was renamed on the same page → restore the old id.** The old
anchor URL is indexed, and a redirect cannot fix a fragment, so putting the
legacy id back is the only repair that helps a reader arriving from Google.
The corpus already uses this idiom — `evaluations.md`'s
`### Philosophy: … <a href="#setup-team-evals" id="setup-team-evals"></a>` is
GitBook's own output. The stub is written **flush against the heading text with
no space before it**: `github-slugger` does not trim, so a trailing space turns
the heading's own slug into `…-evals-`, which is how the existing one acquired
its trailing hyphen. Verified against the built ids.

| Page | Legacy id restored on |
| --- | --- |
| `docs/collaboration/index.md` | `### **Recommended: Use Git!**` ← `#option-1-use-git` |
| `docs/collaboration/index.md` | `### Option 2: Use Shared Drives` ← `#option-2-use-shared-drives-for-non-technical-team-members` |
| `docs/models-and-ai-providers.md` | `### Included Models from the Model Library - Recommended` ← `#included-models-recommended` (4 links) |
| `docs/models-and-ai-providers.md` | `### Fine-Tuneable Models` ← `#additional-fine-tuneable-models` |
| `docs/models-and-ai-providers.md` | `### Custom OpenAI Compatible Servers` ← `#litellm` |
| `docs/prompts.md` | `## Viewing, Managing & Sharing Prompts` ← `#custom-prompts`, `#custom-prompts-saved-prompts` (4 links) |
| `docs/evals-and-specs/evaluations.md` | `### Next Steps: Iterate and Expand` ← `#iterate-and-expand` |
| `docs/fine-tuning/fine-tuning-guide.md` | `### Step 1: Define your Task` ← `#step-1-define-your-task-and-goals` |
| `docs/reasoning-and-chain-of-thought.md` | `<details><summary>What are reasoning models and chain of thought?</summary>` ← `#what-are-reasoning-models-and-chain-of-thought` |

The last is the interesting one: the section was not renamed, it became a
collapsible. The id goes on the `<details>` element, so the link lands on it.

**(b) The section moved to another page → repoint the link.** Restoring an id
on the old page would send the reader to the wrong content.

| Link | New target | Evidence |
| --- | --- | --- |
| `/docs/prompts/#prompt-generators` (3 links) | `/docs/prompts/prompt-generators/#prompt-generators` | That page exists, is in the sidebar, and its `### Prompt Generators` is the list of generator styles the links describe. |
| `/docs/prompts/#prompt-builders-prompt-styles` | `/docs/prompts/prompt-generators/#prompt-generators` | "Prompt builders / prompt styles" is the old name; the link text is "repair prompts" and **Repair Multi Shot** is an entry in that list. |
| `/docs/synthetic-data-generation/#templates-and-custom-guidance` (2 links) | `/docs/synthetic-data-generation/generating-synthetic-data/#templates-and-custom-guidance` | The heading exists verbatim on that page. |

**Not repaired, and why.** Both need a person who knows what the page meant:

- `docs/collaboration/index.md` → `#option-3-combining-git-and-shared-drives`.
  There is no Option 3 on the page any more, and no section describes combining
  the two. The link text is "mix". Guessing at Automatic Git Sync would be
  inventing intent.
- `docs/synthetic-data-generation/generating-synthetic-data.md` →
  `#set-up-a-data-guide`. The Data Guide is mentioned in prose twice and has no
  section of its own. The repair is to write one, which is content.

### 10. The GitBook link (finding G)

`docs/tools-and-mcp/index.md:138` → `https://kiln.tech/model_library`.

### 11. Wiring and docs

- `package.json`: `"qa": "node scripts/qa_pages.mjs"`, and the new test file in
  `test:js` (the existing glob already covers `scripts/*.test.mjs`).
- `README.md`: a "Page QA" section covering what the sweep checks and what it
  cannot; the list-item figure case under "Screenshots with a caption"; the
  card-grid component under "Images"; the anchor count in "Still to do" moved
  from 24 to 2, with the two survivors named; the `.mdx` pages noted where the
  converter is described.
- `ref/stale_anchors.txt`: 22 lines deleted, header updated so it no longer
  says phase 7 owns them.

## Tests

New `site/scripts/qa_pages.test.mjs` (`node:test`, no new dependencies).
Fixture strings and plain observation objects — nothing reads the live corpus,
matching the convention phases 2 and 6 settled on.

**`residualGitbookMarkup`**

- `test_card_table_attribute_is_reported`, `test_data_hidden_is_reported`,
  `test_data_full_width_is_reported`, `test_data_search_is_reported`.
- `test_app_gitbook_link_is_reported` — the URL class phase 8 kills.
- `test_gitbook_asset_path_is_reported` — nothing should reference
  `.gitbook/assets` after phase 3.
- `test_clean_source_is_silent` — no finding on a page with none of them.
- `test_a_fenced_code_block_is_not_scanned` — a page documenting GitBook
  markup in an example is not a defect. Same "leave code alone" rule the
  converter learned in phase 2.

**`literalMarkupInText`** — the finding B class, which is the one nothing else
catches:

- `test_a_visible_figure_tag_is_reported` and
  `test_a_visible_closing_tag_is_reported`.
- `test_an_unrendered_markdown_image_is_reported` — the raw-space failure
  phase 3 documented, seen from the rendered side.
- `test_an_unrendered_markdown_link_is_reported` — item 5 of finding B.
- `test_a_gitbook_directive_is_reported` — `{% embed %}` and friends.
- `test_prose_that_merely_mentions_a_tag_is_not_reported` — "use the `<figure>`
  element" in a code span or inline code must not fire, or the check gets
  switched off.
- `test_an_arrow_in_prose_is_not_reported` — `a -> b` and `x < y > z`.

**`emptyTableColumns`**

- `test_a_column_that_is_empty_everywhere_is_reported` — header and all cells.
- `test_a_column_with_an_empty_header_but_full_cells_is_kept` — the label
  column of every comparison table in the corpus. A naive header-only check
  would delete them.
- `test_a_column_holding_only_an_image_is_kept` — emptiness is text *and*
  media.
- `test_a_ragged_table_does_not_report_the_missing_cells`.

**`pageFindings`** — judgement over an observation:

- `test_page_level_overflow_is_reported_with_its_offender`.
- `test_an_element_clipped_by_a_scrolling_ancestor_is_not_reported` — the code
  block and wide table case; without this the report is unusable.
- `test_a_broken_same_origin_image_is_reported`.
- `test_an_unreachable_external_image_is_classified_not_failed` — this
  environment cannot reach `img.shields.io`, and a check that cries wolf about
  it will be ignored.
- `test_a_missing_description_is_reported` and
  `test_a_missing_title_is_reported`.
- `test_console_errors_are_reported`.
- `test_a_clean_observation_produces_no_findings`.

**Whole-corpus checks re-run after the change** — the phase's own acceptance,
in the absence of a baseline:

- `npm run build` green: 47 pages, links valid, `staleAnchorsStillStale()`
  satisfied by a 2-line allowlist, `optimizedImagesOnly()` still under its
  cap with the nine covers added.
- `npm test` green, including the existing 104 JS and 135 Python cases.
- `node scripts/qa_pages.mjs --browser` reports **zero** findings across all 46
  pages at 1280px and 375px, other than the external resources this
  environment cannot reach.
- `npm run verify:redirects` still passes its `--min-paths 176` floor — the two
  pages that became `.mdx` must keep their URLs.
- The card grids read correctly at 1280px and 375px, in both light and dark
  themes, with the cover images loading from `/_astro/*.webp`.
- `public/assets/` holds only the five videos and the one centered screenshot;
  every remaining file is referenced.

## Carried forward

For phase 8, and for whoever holds the baseline:

- **The baseline diff is still outstanding.** This phase reduced what it has to
  find and cannot replace it. Both the text diff and the screenshot diff should
  be run against `baseline/` when it exists, and anything they surface is
  phase 8's.
- **Two stale anchors remain**, both needing a decision about what the page
  meant: `#option-3-combining-git-and-shared-drives` in
  `docs/collaboration/index.md` and `#set-up-a-data-guide` in
  `docs/synthetic-data-generation/generating-synthetic-data.md`. Both are
  broken on GitBook today, so neither is a regression.
- **`data-full-width` was dropped rather than implemented** (step 8), on
  measurements taken without the baseline. If the screenshots show GitBook's
  full-bleed comparison tables reading materially better, this is the decision
  to revisit.
- **The favicon and OG image are still typographic placeholders.** No Kiln logo
  exists in this repo or its history. The README "Still to do" entry stays.
- **Two pages are now `.mdx`** — `docs/fine-tuning/index.mdx` and
  `docs/optimizers.mdx`. The phase 9 reconciliation converts to `.md`; if
  either page has changed upstream, merge the converter's output into the MDX
  by hand. Copying over it would restore the card table.
- **Phase 5's written descriptions for `structured-data-json` and
  `keyboard-shortcuts` are still ours, not upstream's** — worth 30 seconds of a
  human's attention, as phase 5 asked.
- **`scripts/qa_pages.mjs --browser` is worth re-running against the
  Cloudflare preview and against production**, the same way
  `verify_redirects.mjs` is. It takes `--base-url`. It is deliberately not a CI
  gate: CI has no browser, and the checks that must never regress are already
  gated there.
