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

## Audit results

Run against all 45 pages plus a real `npm run build`. Prose is not being lost:
a word-level diff of source vs output shows the only removals are the H1 (lifted
into frontmatter, correct), the `embed url="…"` directive text, and `:desktop:`.
Structural counts (fences, headings, list items, table rows, `<details>`,
`<figure>`, `<img>`) match exactly on all 45 pages, and all 96 hints become 96
asides. The losses are concentrated in links, assets, and titles.

### Defects to fix (transformer)

1. **HTML `<a href="…">` links are never rewritten.** `rewrite_links` only
   matches markdown `](…)`. 15 relative `href`s across 9 pages — `.md` targets
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

2. **Anchor index.** Add `build_anchor_index(sources)` returning, per page URL,
   the set of real Starlight slugs plus a `legacy -> starlight` alias map, built
   from the source headings with fenced code skipped.

3. **Asset index.** Add `build_asset_index()` mapping a whitespace-normalised
   filename (U+00A0/U+202F/U+2009 → space) to the real filename on disk, and
   `resolve_asset(name)` returning the real name or `None`.

4. **Leave code blocks alone.** Add `outside_code(text, transform)`, which
   splits the body on fences and applies the directive and link pipeline only
   to the prose between them (defect 6).

5. **One link-rewriting path.** Replace `rewrite_assets` and `rewrite_links`
   with `rewrite_target(target, srcdir, ctx)` plus two callers:

   ```python
   def rewrite_target(target, srcdir, ctx):
       """Link destination -> rewritten URL, or None to leave it untouched."""
   ```

   - `rewrite_html_attrs(text, …)` over `(src|href)="([^"]*)"`, so HTML links
     get the same treatment as markdown links (fixes defect 1).
   - `rewrite_markdown_links(text, …)` over a destination pattern that accepts
     `<…>` and balanced parens (fixes defect 2).

   `rewrite_target` resolves `.gitbook/assets/…` through the asset index (defect
   3), leaves external/absolute targets alone, maps `.md` and directory targets
   through `url_for`, and remaps an anchor **only when it does not match a real
   slug on the target page and does match a legacy alias** (defect 9) — so a
   working anchor can never be rewritten into a broken one. Same-page `#anchor`
   links go through the same remap against the current page.

6. **Unescape the title** in `convert` using the same `heading_text` helper
   (defect 4). `build_sidebar` reuses it in place of its own
   `label.replace("\\", "")`.

7. **Frontmatter scalars.** Replace the line-splitting parser with
   `parse_frontmatter(text)` handling the YAML subset GitBook writes: plain
   scalars, single- and double-quoted scalars, and `>`/`|` block scalars with
   their chomping indicators (defects 7 and 8). There is no `yaml` module in
   the standard library and adding a dependency to a script that gets deleted
   in phase 9 is not worth it.

8. **Embed blocks.** Convert `{% embed url="…" %}…{% endembed %}` as a whole. A
   non-empty body becomes `<figure>…<figcaption>caption</figcaption></figure>`
   around the iframe/video, matching the `<figure>` convention already used by
   the GitBook image blocks (defect 5). A bodyless embed is unchanged.

9. **Unresolved-reference reporting.** Convert every page in memory first, then
   report. Unresolved assets print with their page and exit non-zero (spec:
   blocker). Unresolved anchors print as warnings and do not fail — they are the
   stale-source class, and the functional spec ranks anchor work priority 2.

10. **`--out DIR` flag.** Add `parse_args(argv)` returning `(mode, out_dir)`.
   With `--out`, write the converted tree under `DIR`, never `rmtree` anything,
   and skip the landing page copy, the hero image, the `public/assets` copy and
   `sidebar.json`. Without it, behaviour is unchanged. Document it in the module
   docstring and in `site/README.md`.

11. **`site/package.json`** gains `"test": "python3 -m unittest discover -s
   scripts -p 'test_*.py' -t scripts"`.

## Tests

New `site/scripts/test_gitbook_to_starlight.py` (stdlib `unittest`, no new
dependencies). One case per defect plus the invariants that keep the fixes
honest:

- `test_starlight_slug_matches_github_slugger` — the punctuation, `&`, hyphen,
  escaped-bracket and HTML-entity heading forms taken from the real docs slug to
  the ids Starlight actually emitted.
- `test_heading_text_strips_inline_markup` — code spans, links, emphasis,
  trailing GitBook `<a id>` anchor overrides, `&#x20;`.
- `test_legacy_slug_alias_for_ampersand_heading` — `State & Memory` yields the
  legacy `state-and-memory` alias alongside `state--memory`.
- `test_anchor_remapped_only_when_broken` — a link to `#state-and-memory` is
  rewritten to `#state--memory`; a link to an anchor that already matches a real
  slug is left untouched; an anchor matching nothing is left untouched.
- `test_html_anchor_href_to_md_is_rewritten` — `<a href="prompts.md">` becomes
  `<a href="/docs/prompts/">`.
- `test_html_anchor_href_to_directory_is_rewritten` — `<a href="fine-tuning/">`
  becomes `<a href="/docs/fine-tuning/">`.
- `test_external_and_absolute_targets_untouched` — `https:`, `mailto:`, `/…`.
- `test_angle_bracket_asset_link` — `](<../.gitbook/assets/filter 2.png>)`
  produces `/assets/filter%202.png` with no stray `>`.
- `test_asset_link_with_parens_in_filename` — `Screenshot … (1).png` survives.
- `test_asset_name_whitespace_normalised` — a reference written with a plain
  space resolves to the U+202F filename on disk.
- `test_unresolved_asset_is_reported` — a reference to a nonexistent file is
  collected rather than silently emitted.
- `test_title_unescapes_markdown` — `# … Q\&A Evals` yields `Q&A` in the title.
- `test_links_inside_code_fences_are_untouched` — the `docs/skills.md` example
  link survives verbatim.
- `test_folded_block_description_is_joined`,
  `test_literal_block_description_keeps_line_breaks`,
  `test_single_quoted_description_keeps_inner_quotes`,
  `test_plain_description_is_passed_through`,
  `test_page_without_description_omits_the_field`.
- `test_embed_with_caption_becomes_figure` — vimeo, youtube and the GitBook CDN
  `.mp4` forms each produce a `<figure>` with the caption in `<figcaption>`.
- `test_embed_without_caption_has_no_figcaption`.
- `test_hint_styles_map_to_asides` — all four styles, and that an unknown style
  falls back to `note`.
- `test_parse_args_out_dir` — `--out` sets the output directory and clears the
  asset/sidebar/landing-page side effects; absence restores the defaults.

Whole-corpus checks re-run after the change (the substituted baseline diff):

- `npm run build` succeeds and still emits 47 pages.
- Every `/assets/...` reference in the converted output resolves to a real file
  in `.gitbook/assets` (87 references, currently 4 broken → 0).
- Walking `site/dist`, no internal link points at a missing page (currently 15
  broken → 0, `/favicon.svg` excepted and recorded above).
- Broken anchors drop from 27 to the 24 stale-source ones, which are listed.
- Word-level source-vs-output diff still shows no prose loss on any page.
