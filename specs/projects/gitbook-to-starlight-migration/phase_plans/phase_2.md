---
status: draft
---

# Phase 2: Audit the Transformer and Its Output

## Overview

`site/scripts/gitbook_to_starlight.py` is about to stop being a build step and
start being the origin of hand-maintained content (phase 3). Anything it drops
or mangles now becomes a hand-editing chore later, page by page. This phase
audits its output across all 45 source pages, fixes the systematic losses, and
adds the `--out DIR` flag the architecture requires so the phase 9
reconciliation can run without clobbering hand-edited files.

### Environment substitution: no baseline to diff against

The implementation plan says "diff converted text against `baseline/pages/`".
**Phase 1 could not run** — outbound network to `docs.kiln.tech` is blocked by
policy in this environment, so there is no `baseline/` directory and no
rendered-text capture of the live GitBook site.

Substituted check, which tests the same property from the other side: diff the
**converted output against the GitBook source markdown** in `docs/`,
`developers/`, and `README.md`. A baseline diff would catch "the new page says
less than the old page"; a source diff catches "the converter dropped something
that was in the markdown". Since GitBook renders from that same markdown, the
overlap is nearly total — what it cannot catch is content GitBook synthesised
that has no markdown representation (the landing-page card table, page chrome,
auto-generated `llms.txt`), all of which is already tracked elsewhere in the
spec. The baseline diff itself remains outstanding for phase 7.

The source-side diff is mechanical and covers: word-level prose loss, code
fences, headings, list items, markdown and HTML tables, `<details>` blocks,
`<figure>`/`<img>` counts, hint→aside counts, embeds, frontmatter fields,
asset references resolving to real files, and every internal link and anchor
resolving in the built site.

**Its blind spot:** a source diff proves nothing was *dropped*; it says nothing
about whether Starlight *renders* what survived. Markup GitBook interpreted and
Starlight passes through as a plain HTML table counts as intact by every check
here while looking wrong on the page. The card tables below are exactly that
case, and they are why the visual half of phase 7 still needs the baseline
screenshots.

## Audit results

Run against all 45 pages plus a real `npm run build`. Prose is not being lost:
a word-level diff of source vs output shows the only removals are the H1 (lifted
into frontmatter, correct), the `embed url="…"` directive text, and `:desktop:`.
Structural counts (fences, headings, list items, table rows, `<details>`,
`<figure>`, `<img>`) match exactly on all 45 pages, and all 96 hints become 96
asides. Matching counts mean nothing was dropped, not that everything renders —
see the card tables under recorded findings. The losses fixed here are
concentrated in links, assets, titles, and frontmatter.

### Defects to fix (transformer)

1. **HTML `<a href="…">` links are never rewritten.** `rewrite_links` only
   matches markdown `](…)`. 15 relative `href`s across 8 pages — `.md` targets
   and directory targets — ship verbatim into the output and 404 on the built
   site (verified by walking `site/dist`). Affects `docs/optimizers.md`,
   `docs/quickstart.md`, `docs/skills.md`, `docs/evals-and-specs/README.md`,
   `docs/evals-and-specs/evaluations.md`,
   `docs/evals-and-specs/evaluate-rag-accuracy-q-and-a-evals.md`,
   `docs/fine-tuning/README.md`, `docs/fine-tuning/fine-tuning-for-tool-use.md`.

2. **Angle-bracket link destinations corrupt asset URLs.** GitBook writes
   `](<../.gitbook/assets/filter 2.png>)` when a filename contains spaces. The
   `[^)]*` destination pattern keeps the `>` and stops at the first `)`, so
   `filter 2.png>` and `Screenshot 2025-01-05 at 12.18.52 PM (1` are emitted as
   asset names. Three broken images in `docs/organizing-datasets.md`,
   `docs/keyboard-shortcuts.md`, `docs/reviewing-and-rating.md`.

3. **Asset filenames are used verbatim and one does not exist.**
   `.gitbook/assets/Screenshot 2025-11-14 at 1.33.24␟PM.png` is stored with a
   narrow no-break space (U+202F) but referenced with a plain space from
   `docs/evals-and-specs/evaluate-appropriate-tool-use.md`. GitBook's CDN
   normalised this; a static host will not. The transformer must resolve
   references against the real directory listing and fail loudly on a genuine
   miss (functional spec: "an asset is referenced but missing … treat as a
   blocker").

4. **Markdown escapes leak into the page title.** `# Evaluate RAG Accuracy: Q\&A
   Evals` yields `<title>Evaluate RAG Accuracy: Q\&A Evals</title>` and an `<h1>`
   with a literal backslash. `build_sidebar` already strips escapes; `convert`
   does not.

5. **Embed captions lose their caption semantics.** The text between
   `{% embed %}` and `{% endembed %}` is GitBook's video caption. Today only the
   opening and closing tags are removed, so the caption lands as a bare text node
   glued to the end of the iframe/video HTML block. Six captions across
   `docs/fine-tuning/fine-tuning-guide.md`,
   `docs/evals-and-specs/evaluations.md`, and
   `docs/synthetic-data-generation/generating-synthetic-data.md`.

6. **Link rewriting runs inside fenced code blocks.** `docs/skills.md`
   documents a skill whose example content contains
   `[style guide](references/STYLE_GUIDE.md)`. The converter rewrites it to
   `/docs/references/STYLE_GUIDE/`, silently editing a code sample into
   something wrong. Any future code block containing a markdown link or an
   `href` has the same problem.

7. **Folded YAML descriptions are read as the literal string `">-"`.** Six
   pages wrap a long `description` into a block scalar. The line-splitting
   frontmatter parser emits `description: ">-"`, which Starlight puts straight
   into `<meta name="description">` and Pagefind indexes. The functional spec
   requires every page to have a description.

8. **A quoted description loses its leading quote.**
   `docs/repairing-responses.md` has
   `description: '"Teach the model, you will" - ML Yoda'`; `strip("\"'")`
   removes the outer single quotes *and* the inner opening double quote.

9. **Cross-page anchors drift on `&` headings.** GitBook slugifies `&` to `and`;
   `github-slugger` deletes it and leaves the surrounding double space, producing
   `--`. Four in-repo links break as a result: `#state-and-memory`,
   `#goal-directed-autonomy-and-reasoning` (`docs/agents.md`) and
   `#search-tool-name-and-description`
   (`docs/documents-and-search-rag.md`). These are also indexed anchor URLs, so
   the drift matters beyond the repo.

### Findings recorded, not fixed here

- **24 anchors are already stale in the GitBook source** — headings were renamed
  upstream and the links were not updated. These are broken on GitBook today;
  fixing them is a content edit, and the functional spec puts copy changes out of
  scope. They will fail `starlight-links-validator` in phase 6, so the full list
  is below for phase 7 to resolve.

  | Page | Dead anchor |
  | --- | --- |
  | `developers/kiln-datamodel.md` | `/docs/collaboration/#technical-collaboration-architecture` |
  | `docs/collaboration/README.md` | `/docs/collaboration/#option-1-use-git` |
  | `docs/collaboration/README.md` | `/docs/collaboration/#option-2-use-shared-drives-for-non-technical-team-members` |
  | `docs/collaboration/README.md` | `/docs/collaboration/#option-3-combining-git-and-shared-drives` |
  | `docs/evals-and-specs/evaluations.md` | `/docs/evals-and-specs/evaluations/#iterate-and-expand` |
  | `docs/evals-and-specs/evaluations.md` | `/docs/prompts/#custom-prompts-saved-prompts` |
  | `docs/evals-and-specs/evaluations.md` | `/docs/prompts/#prompt-generators` |
  | `docs/evals-and-specs/evaluations.md` | `/docs/synthetic-data-generation/#templates-and-custom-guidance` |
  | `docs/fine-tuning/fine-tuning-guide.md` | `/docs/fine-tuning/fine-tuning-guide/#step-1-define-your-task-and-goals` |
  | `docs/fine-tuning/fine-tuning-guide.md` | `/docs/models-and-ai-providers/#additional-fine-tuneable-models` |
  | `docs/fine-tuning/fine-tuning-guide.md` | `/docs/synthetic-data-generation/#templates-and-custom-guidance` |
  | `docs/fine-tuning/guide-train-a-reasoning-model.md` | `/docs/models-and-ai-providers/#included-models-recommended` |
  | `docs/fine-tuning/guide-train-a-reasoning-model.md` | `/docs/prompts/#custom-prompts-saved-prompts` |
  | `docs/fine-tuning/guide-train-a-reasoning-model.md` | `/docs/reasoning-and-chain-of-thought/#what-are-reasoning-models-and-chain-of-thought` |
  | `docs/models-and-ai-providers.md` | `/docs/models-and-ai-providers/#included-models-recommended` |
  | `docs/models-and-ai-providers.md` | `/docs/models-and-ai-providers/#litellm` |
  | `docs/prompts.md` | `/docs/prompts/#custom-prompts` |
  | `docs/prompts.md` | `/docs/prompts/#prompt-generators` |
  | `docs/reasoning-and-chain-of-thought.md` | `/docs/models-and-ai-providers/#included-models-recommended` |
  | `docs/repairing-responses.md` | `/docs/prompts/#prompt-builders-prompt-styles` |
  | `docs/reviewing-and-rating.md` | `/docs/prompts/#prompt-generators` |
  | `docs/structured-data-json.md` | `/docs/models-and-ai-providers/#included-models-recommended` |
  | `docs/structured-data-json.md` | `/docs/prompts/#custom-prompts-saved-prompts` |
  | `docs/synthetic-data-generation/generating-synthetic-data.md` | `/docs/synthetic-data-generation/generating-synthetic-data/#set-up-a-data-guide` |

  Three of these point at `/docs/prompts/#prompt-generators` and
  `#custom-prompts-saved-prompts`, which look like they were meant for the
  separate `docs/prompts/prompt-generators.md` page — worth checking rather than
  inventing a heading.
- **GitBook's card tables render as plain 4-column tables.**
  `<table data-view="cards">` was a GitBook grid widget; Starlight passes the
  HTML through unchanged, so `docs/fine-tuning/README.md` and
  `docs/optimizers.md` now show an ordinary table with a visible `Cover image`
  header column and raw filenames (`tuning2.png`, `fine-tuning-guide.md`) as the
  link text. Confirmed in `site/dist/docs/fine-tuning/index.html`. The same
  inertness affects 10 `data-hidden` columns across 5 pages (they render as
  visible empty columns), `data-full-width` on two tables in `docs/skills.md`,
  and `data-search="false"` in `docs/evals-and-specs/README.md`. Nothing is
  lost — it is a rendering job, and it is the one class of problem the
  substituted source diff structurally cannot see. Phase 7, alongside the
  hand-written landing page that replaced the third card table.

- **Two pages have no `description` at all.** `docs/structured-data-json.md`
  and `docs/keyboard-shortcuts.md` have none in the GitBook source, so the
  converted pages have none either and fall back to the site description. The
  functional spec's fidelity bar requires one per page — the same requirement
  that motivated defect 7 — so these two need copy written for them in phase 5
  or 7. The transformer cannot invent them.

- **`/favicon.svg` 404s on all 47 pages.** There is no `site/public/favicon.svg`.
  Needs a real asset decision; belongs with the OG image work in phase 5.
- **`docs/tools-and-mcp/README.md` links to `https://app.gitbook.com/u/…`**, a
  private GitBook URL that will die with the space. Content fix, phase 7.
- **`icon:` frontmatter on 30 source pages is dropped.** Starlight has no
  equivalent frontmatter field; the sidebar is icon-free by design. Accepted.

## Steps

1. **`site/scripts/gitbook_to_starlight.py` — heading slugs.** Add
   `heading_text(raw)` (strip inline HTML, code spans, links, emphasis, decode
   HTML entities, unescape `\x`), `starlight_slug(text)` (a faithful
   `github-slugger` port: lowercase, drop `[^\w\s-]`, spaces to hyphens, no
   trim), and `legacy_slugs(text)` returning the GitBook-style alternates
   (`&` → `and`, collapsed whitespace). Verified against the built HTML: the
   port reproduces all 307 heading ids across the 45 pages.

2. **One fence scanner.** Add `code_regions(text)`, returning the character
   ranges of fenced code blocks. It tracks the *opening* fence rather than
   toggling on any fence-looking line, so a ```` ``` ````-fence nested inside a
   ```` ```` ````-block does not close it — the corpus has two such blocks
   (`docs/structured-data-json.md`, `docs/documents-and-search-rag.md`).
   `heading_matches`, `headings`, `lift_title` and `outside_code` all build on
   it, so there is one definition of "this is code, leave it alone" (defect 6).

3. **Anchor index.** `Conversion` holds, per page URL, the set of real Starlight
   slugs plus a `legacy -> starlight` alias map. It indexes the body **after**
   `lift_title` has removed the H1, matching what `convert` writes: Starlight
   renders the H1 from frontmatter with `id="_top"`, so indexing it would mint
   one anchor per page that does not exist and shift the duplicate-slug
   numbering off by one (`docs/prompts/prompt-generators.md` has both
   `# Prompt Generators` and `### Prompt Generators`).

4. **Asset index.** Add `build_asset_index()` mapping a whitespace-normalised
   filename (U+00A0/U+202F/U+2009 → space) to the real filename on disk, and
   `Conversion.resolve_asset`, which checks the exact name against a set first
   and falls back to the normalised lookup.

5. **One link-rewriting path.** Replace `rewrite_assets` and `rewrite_links`
   with `rewrite_target(target, relpath, ctx, page_url)` plus two callers inside
   `rewrite_references`:

   ```python
   def rewrite_target(target, relpath, ctx, page_url):
       """Link destination -> rewritten URL, or None to leave it untouched."""
   ```

   - an `(src|href)="([^"]*)"` pass, so HTML links get the same treatment as
     markdown links (fixes defect 1);
   - a markdown-destination pass whose pattern accepts `<…>` and one level of
     balanced parens (fixes defect 2).

   `rewrite_target` resolves `.gitbook/assets/…` through the asset index (defect
   3), leaves external/absolute targets alone, maps `.md` and directory targets
   through `url_for`, and remaps an anchor **only when it does not match a real
   slug on the target page and does match a legacy alias** (defect 9) — so a
   working anchor can never be rewritten into a broken one. Same-page `#anchor`
   links go through the same remap against the current page.

6. **Unescape the title.** `lift_title` runs the H1 through `heading_text`, and
   `build_sidebar` reuses it in place of `label.replace("\\", "")` (defect 4).
   Frontmatter is written with `ensure_ascii=False` so curly quotes and dashes
   survive as themselves.

7. **Frontmatter scalars.** Replace the line-splitting parser with
   `parse_frontmatter(text)` handling the YAML subset GitBook writes: plain
   scalars, single- and double-quoted scalars, and `>`/`|` block scalars with
   their chomping indicators (defects 7 and 8). There is no `yaml` module in
   the standard library and adding a dependency to a script that gets deleted
   in phase 9 is not worth it.

8. **Embed blocks.** Convert `{% embed url="…" %}…{% endembed %}` as a whole.
   The caption pattern requires **one or more** non-blank lines, so a caption
   becomes `<figure>…<figcaption>caption</figcaption></figure>` around the
   iframe/video (defect 5) while `{% embed %}{% endembed %}` — GitBook's shape
   for an uncaptioned video — stays a bare embed rather than growing an empty
   `<figcaption>`.

9. **Unresolved-reference reporting.** Convert every page in memory first, then
   report; each distinct problem is recorded once. Unresolved assets print with
   their page and exit non-zero (spec: blocker). Unresolved anchors get one
   summary line, with the full list behind `--anchors` — they are the
   stale-source class the functional spec ranks priority 2, and printing 24 of
   them on every build would train people to ignore the channel the fatal error
   uses.

10. **`--out DIR` flag, via `argparse`.** With `--out`, write the converted tree
   under `DIR`, never `rmtree` anything, and skip the landing page copy, the
   hero image, the `public/assets` copy and `sidebar.json`. Without it,
   behaviour is unchanged. `argparse` rather than hand-rolled matching because
   the failure mode is the point: an unrecognised argument — `--out=DIR` against
   a bare `--out` check, or a typo like `--outt` — must be an error, never a
   fall-through to the default run, which begins by deleting
   `src/content/docs/`. The functional spec forbids that once content is
   hand-edited. Documented in the module docstring and in `site/README.md`.

11. **`site/package.json`** gains `"test": "python3 -m unittest discover -s
   scripts -p 'test_*.py' -t scripts"`.

## Tests

New `site/scripts/test_gitbook_to_starlight.py` (stdlib `unittest`, no new
dependencies). One case per defect plus the invariants that keep the fixes
honest:

**Slugs and headings**

- `test_starlight_slug_matches_github_slugger` — the punctuation, `&`, hyphen,
  escaped-bracket, HTML-entity and trailing-anchor-tag heading forms taken from
  the real docs slug to the ids Starlight actually emitted.
- `test_heading_text_strips_inline_markup` — code spans, links, emphasis, and
  `kiln_ai` surviving with its underscore.
- `test_legacy_slugs_spell_ampersand_as_and`.
- `test_repeated_heading_gets_numeric_suffix`.
- `test_hand_written_anchor_ids_count_as_anchors`.
- `test_lift_title_removes_the_h1_and_leaves_the_rest`,
  `test_lift_title_ignores_a_hash_inside_a_code_fence`.
- `test_h1_is_not_indexed_as_an_anchor` — the
  `docs/prompts/prompt-generators.md` shape: the H3 keeps the bare slug instead
  of being pushed to `prompt-generators-1`.

**Fences**

- `test_headings_inside_code_fences_are_not_anchors`.
- `test_nested_fence_does_not_close_a_longer_block` and
  `test_links_inside_a_nested_fence_are_untouched` — a ```` ``` ````-fence
  inside a ```` ```` ````-block leaves neither a phantom anchor nor a rewritten
  link.
- `test_closing_fence_must_match_the_opening_character`.
- `test_unclosed_fence_swallows_the_rest_of_the_page`.
- `test_links_inside_code_fences_are_untouched` — the `docs/skills.md` example
  link survives verbatim.

**Anchors**

- `test_legacy_anchor_is_remapped`, `test_current_anchor_is_left_alone`,
  `test_unknown_anchor_is_reported_but_not_rewritten` (and recorded once for two
  identical links), `test_same_page_anchor_is_remapped`.

**Links and assets**

- `test_html_anchor_href_to_md_is_rewritten`,
  `test_html_anchor_href_to_directory_is_rewritten`,
  `test_html_anchor_href_with_parent_segments_is_rewritten`,
  `test_markdown_link_to_md_is_rewritten`.
- `test_external_and_absolute_targets_are_untouched`,
  `test_link_to_missing_page_is_untouched`.
- `test_angle_bracket_asset_link` — `](<../.gitbook/assets/filter 2.png>)`
  produces `/assets/filter%202.png` with no stray `>`.
- `test_asset_filename_containing_parentheses`.
- `test_asset_name_whitespace_is_normalised_to_the_real_file` — a reference
  written with a plain space resolves to the U+202F filename on disk.
- `test_missing_asset_is_reported`, `test_the_same_missing_asset_is_recorded_once`,
  `test_report_raises_on_missing_asset`.
- `test_report_tolerates_unresolved_anchors` (summary line only) and
  `test_anchors_flag_lists_each_unresolved_anchor`.

**Frontmatter and titles**

- `test_folded_block_description_is_joined`,
  `test_literal_block_description_keeps_line_breaks`,
  `test_single_quoted_description_keeps_inner_quotes`,
  `test_plain_description_is_passed_through`,
  `test_page_without_description_omits_the_field`.
- `test_title_unescapes_markdown` — `# … Q\&A Evals` yields `Q&A` in the title.
- `test_h1_is_lifted_out_of_the_body`, `test_title_falls_back_to_the_filename`.

**Hints and embeds**

- `test_every_hint_style_maps_to_an_aside`,
  `test_unknown_hint_style_falls_back_to_note`,
  `test_code_directive_is_dropped_and_the_fence_survives`.
- `test_captioned_embed_becomes_a_figure` (vimeo),
  `test_captioned_youtube_embed_becomes_a_figure`,
  `test_gitbook_cdn_video_points_at_the_local_copy` — all three forms.
- `test_embed_caption_is_html_escaped`.
- `test_bodyless_embed_has_no_empty_figcaption` and
  `test_embed_without_endembed_has_no_figure` — the two uncaptioned shapes,
  tested separately because they take different paths.

**Arguments and the `--out` safety property**

- `test_default_mode_writes_the_site`, `test_list_mode`,
  `test_out_returns_an_absolute_directory`,
  `test_out_accepts_the_equals_spelling`,
  `test_out_without_a_directory_is_an_error`.
- `test_unknown_arguments_are_rejected` — `--outt DIR`, bare `garbage`, and a
  trailing unknown flag all raise rather than falling through to the run that
  deletes `src/content/docs/`.
- `test_out_writes_pages_only_and_touches_nothing_else` — runs `main()` for
  real against a temp directory with `shutil.rmtree`/`copy`/`copytree` patched,
  asserting none is called, a sentinel file survives, `sidebar.json`'s mtime is
  unchanged, one `.md` lands per source page, and no `.mdx` landing page is
  copied. This is the single most safety-critical behaviour in the change, so
  it gets an end-to-end test rather than an assertion about `parse_args`.

**Sidebar** — built from a fixture `SUMMARY.md` rather than the live one, so a
content rename cannot break it: `test_group_heading_becomes_a_sidebar_group`,
`test_readme_is_not_a_sidebar_entry`, `test_labels_are_unescaped`,
`test_a_parent_page_becomes_an_overview_entry_in_its_own_group`, plus
`test_url_for` and `test_out_for`.

Whole-corpus checks re-run after the change (the substituted baseline diff):

- `npm run build` succeeds and still emits 47 pages.
- Every `/assets/...` reference in the converted output resolves to a real file
  in `.gitbook/assets` (87 references, currently 4 broken → 0).
- Walking `site/dist`, no internal link points at a missing page (currently 15
  broken → 0, `/favicon.svg` excepted and recorded above).
- Broken anchors drop from 27 to the 24 stale-source ones, which are listed.
- The slug port reproduces all 307 heading ids in `site/dist` exactly, and the
  anchor index contains no slug the built page lacks.
- Word-level source-vs-output diff still shows no prose loss on any page.
