---
status: draft
---

# Phase 9: Reconcile late content, then remove the transformer

## Overview

Phase 9 has two halves. The first is reconciliation: pick up any GitBook page
that landed on `origin/main` after the content freeze at `1dde281` and bring it
into the hand-maintained Starlight content. The second is demolition: delete
`gitbook_to_starlight.py`, the `npm run convert` wiring, and any remaining
migration-only scripts.

**The first half turns out to be already done, and the second half should not
happen yet.** Both conclusions are evidenced below.

### Why reconciliation is already complete

The implementation plan was written before `origin/main` was merged into this
branch at `3e16f5a` ("Merge main into the Starlight branch before phase 3"),
which happened *before* phase 3 committed the converted output. That merge was
deliberate: it put main's then-current content — the evals/judges edits from
PR #15, 8 files — through the audited transformer in a clean full conversion,
rather than leaving it for this phase's copy-in-individually procedure.

Nothing has landed on main since. Three independent checks agree:

1. **Commit graph.** `git log HEAD..origin/main` is empty and
   `git merge-base --is-ancestor origin/main HEAD` succeeds. `origin/main`'s
   HEAD (`722d4cd`) is literally the second parent of `3e16f5a`.

2. **Source trees.** Every GitBook input object is bit-identical between
   `3e16f5a` and `origin/main`:

   | Path | Tree/blob SHA (both refs) |
   | --- | --- |
   | `docs` | `b5cc0b9012560d160a09e208dd1cf04b19d06018` |
   | `developers` | `260166e5790abbf628c6d836bc62c37c3d820565` |
   | `.gitbook` | `cfd79765e9bdedccbd943207e8ac52ea2874e689` |
   | `SUMMARY.md` | `b7f47d8bd0445a7bab07535783f50982c27f9df6` |
   | `README.md` | `13f8bccc0c92e53447a76a35357bf547992673a4` |

   `git diff 3e16f5a origin/main -- docs developers .gitbook SUMMARY.md README.md`
   is empty. There is no post-freeze page to convert.

3. **A real conversion run.** Following the recovery procedure in
   `require_gitbook_sources()` exactly — worktree at `GITBOOK_TREE_COMMIT`,
   *today's* transformer copied in, `--out` to a scratch directory — reproduces
   the shipped content page for page: 45 pages, 27 byte-identical to
   `src/content/docs`, 18 differing only in the phase 5/7 hand edits, and the
   two pages phase 7 promoted to `.mdx`. No converted page carries content that
   the shipped tree is missing.

Of the 8 files PR #15 touched, 7 are byte-identical to a fresh conversion of
main's sources. The eighth, `evals-and-specs/evaluations.md`, differs in exactly
four lines, all of them phase 7 link/anchor repairs that improve on the
converter's output rather than losing anything.

Spot checks confirm the same thing from the content side. Every distinctive
string PR #15 *added* is present in `src/content/docs` (the Jinja2 template
guidance, the 300-second timeout maximum, "Unlisted Tool Calls", the
`test_`/`golden_` tag naming, "Advanced: Judge Prompt", session-scoped trust),
and every string it *removed* is absent (the `scorer.py` filename hint, the
"Python Library Usage \[optional]" block under judge types, "returns mapped
float scores", the old "Advanced: Customize …" headings).

**Nothing is outstanding. There is no page to copy in, so the `.mdx` collision
hazard that phase 7 and `site/README.md` warn about is never reached.**

### Why the transformer should not be deleted yet

The plan orders phase 9 last because it "removes our ability to convert
anything else". That rationale assumes everything ahead of it is finished. It
is not: **phase 8, the cutover, is deliberately unperformed and its checkbox
stays unticked.** GitBook is still live and still editable. Any edit made there
between now and decommissioning arrives on `main` as a further `GITBOOK-nnn`
commit and needs precisely this tool.

The second reason is sharper, and it is a trap the project has already
documented twice. The recovery procedure tells a future reader to check out
`GITBOOK_TREE_COMMIT` — and the transformer sitting *inside* that commit is the
phase-2 vintage, which produces materially different output: 29 of 45 pages
differ, and it writes `<img src="/assets/NAME">` for images that now live in
`src/assets/`, a 404 nothing validates. The procedure works only because the
correct, audited transformer is at `HEAD` where `cp scripts/gitbook_to_starlight.py`
can reach it. Delete it, and the only correct copy is buried at commit `3f91b7e`
in a branch's history, while the *wrong* copy is sitting in plain sight at the
commit the instructions name. That converts a well-signposted procedure into a
silent-failure trap.

Recommendation: **defer the deletion of `gitbook_to_starlight.py` and its tests
until after phase 8's cutover completes and GitBook is decommissioned.** At that
point no new GitBook content can exist, the tool is genuinely dead, and removing
it costs nothing.

### What this phase does remove

`npm run convert` goes now. It is the "wiring" the plan names, it is
undocumented, and it cannot do anything useful:

- **The script cannot run from this checkout at all, in any mode.** `main()`
  calls `require_gitbook_sources()` before anything else, and `.gitbook/`,
  `docs/`, `developers/` and `SUMMARY.md` were deleted in phase 3 — so the run
  exits 1 with the recovery procedure. Both `npm run convert` and
  `npm run convert -- --out DIR` die there. Note the ordering: the source-tree
  guard fires *first*, so `refuse_to_rebuild_committed_output()` is never
  reached from here. It is not what stops `npm run convert`; it is a second
  guard, for a checkout that still has the sources.
- The documented reconciliation path never uses it, and could not. It is
  `python3 scripts/gitbook_to_starlight.py --out DIR` run from *the worktree's*
  copy of the script — a different working directory, and a different
  `site/package.json`. An npm script here cannot be the vehicle for a run that
  by definition happens somewhere else.

So the entry is a footgun with no upside: it names a capability this checkout
does not have. The one thing it could plausibly teach a reader — that
`npm run convert` is how you convert — is exactly the thing that is false, and
the failure it produces is a wall of recovery text rather than an obvious
"wrong command". Removing it costs no capability, because the capability lives
in `--out`, invoked directly from a worktree.

### What is not migration scaffolding

Judged individually, and kept:

| Script | Why it stays |
| --- | --- |
| `build_redirects.py` (+ tests) | Generates and gates `public/_redirects`; `npm run redirects:check` is a CI gate. |
| `verify_redirects.mjs` (+ tests) | Verifies redirects against `dist` and against preview/production URLs; used by both workflows. |
| `qa_pages.mjs` (+ tests) | The page-QA sweep, static and real-browser. |
| `build_integrations.mjs` | Imported directly by `astro.config.mjs`; the build fails without it. |
| `stale_anchors.mjs` (+ tests) | Imported directly by `astro.config.mjs`. |
| `build_og_image.mjs` | Regenerates the committed `public/og.png` when branding changes. A generator for live content, not migration scaffolding. |
| `frontmatter.test.mjs`, `markdown_assets.test.mjs` | Cover `src/lib/frontmatter.mjs` and `src/lib/markdown-assets.mjs`, which power the per-page `.md` endpoints and the theme's "Copy page". Live code. |

The only migration-only artifacts in the repo are
`scripts/gitbook_to_starlight.py`, `scripts/test_gitbook_to_starlight.py`, and
the `convert` entry in `package.json`.

## Steps

1. **Establish what is outstanding.** Fetch `origin/main`; compare it to the
   branch by commit graph, by GitBook source tree object SHA against
   `3e16f5a`, and by a real `--out` conversion run diffed against
   `src/content/docs`. Result recorded above: nothing outstanding.

2. **Remove the `convert` entry** from `site/package.json`. No other script
   depends on it; it appears in no workflow and no README.

3. **Rewrite the "The GitBook converter" section of `site/README.md`** so it
   states the tool's actual remaining purpose. It currently says the converter
   "is kept only for the final reconciliation step, which picks up any GitBook
   page that landed after the content freeze" — that step is now done, so the
   sentence would leave the next reader hunting for work that does not exist.
   Replace it with: reconciliation is complete as of `origin/main` `722d4cd`;
   the tool is retained only against further GitBook edits before cutover; and
   it is scheduled for deletion once phase 8 decommissions GitBook. Keep the
   worktree procedure, the "do not skip the `cp`" warning, and the `.mdx`
   warning intact — they are what make the tool safe to use if it is needed.

4. **Record the deferral in `implementation_plan.md`** under phase 9, so the
   split between the done half and the deferred half is visible from the plan
   and not only from this file. Leave the phase 9 checkbox unticked, as phase 8's
   is, because the phase is deliberately only half performed.

5. **Leave `gitbook_to_starlight.py` and `test_gitbook_to_starlight.py` in
   place**, per the reasoning above.

## Tests

No new tests. This phase removes an undocumented npm script entry and edits
prose; it adds no code paths to cover. The existing suite is what guards the
change:

- `npm test` — 236 Python tests (135 transformer, 101 redirects) and 151 JS
  tests must still pass, unchanged. The transformer's 135 tests staying green
  is the check that step 5 actually left it intact and importable.
- `npm run build` — must still succeed, including `starlight-links-validator`
  and the post-build assertions, proving nothing removed was load-bearing.
- `npm run redirects:check`, `npm run verify:redirects -- --dist dist`,
  `npm run qa` — must stay green.
- Manually: `npm run convert` must be gone from `npm run` output, and no
  workflow, README, or script references it.
