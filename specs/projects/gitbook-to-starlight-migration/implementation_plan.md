---
status: complete
---

# Implementation Plan: GitBook → Astro Starlight Migration

Ordered by dependency. Phases 1 and 2 come first because they must happen
while GitBook is still live; phase 9 must be last because it removes our
ability to convert anything else.

## Phases

- [ ] **Phase 1: Capture the baseline.** Crawl the live GitBook site for the
  URL inventory, per-page rendered text, and full-page screenshots into
  `baseline/`. Add Search Console's indexed-page export for historical URLs.
  **Requires a session with real Chrome and public internet access** — cannot
  run in a network-restricted environment. Everything downstream depends on
  this, and it is impossible once GitBook is gone.

- [x] **Phase 2: Audit the transformer and its output.** Review
  `gitbook_to_starlight.py` against all 45 pages and fix conversion gaps before
  the output becomes hand-maintained. Add the `--out DIR` flag so later runs
  are non-destructive. Diff converted text against `baseline/pages/` to find
  systematic losses.

- [x] **Phase 3: Go Astro-native.** Run the transformer a final time, commit
  its output, and remove the gitignore rules for generated paths. **Unwire
  `npm run convert` from `npm run build` and `npm run dev`** — both call it
  today, so once `src/content/docs/` is committed the ordinary build would
  delete the hand-maintained content and regenerate it from `docs/`, which the
  functional spec forbids. `convert` stays as a standalone script for the phase
  9 reconciliation. (Phase 2 added a backstop: the default run refuses when
  `src/content/docs/` is tracked in git. Unwiring is still the actual fix — the
  backstop only stops the build rather than letting it work.) Move referenced
  images into `src/assets/` and convert `<figure>` blocks per the architecture.
  Prune the ~73 unreferenced assets, including the two oversized videos. Delete
  the GitBook source tree (`docs/`, `developers/`, `README.md`, `SUMMARY.md`,
  `.gitbook/`) using `git mv` where paths map cleanly. Update `editLink` and
  rewrite `site/README.md` so it no longer describes a transform pipeline.
  **Keep the transformer itself.**

- [x] **Phase 4: Redirects.** Build `redirects.csv` from the phase 1 inventory
  plus the known flat-alias pattern. Implement `build_redirects.py` (with unit
  tests for chain-flattening and duplicate detection) and
  `verify_redirects.mjs`. Set `trailingSlash`/`build.format` explicitly.

- [x] **Phase 5: Feature parity.** `starlight-llms-txt` plus a visible link to
  it. Static OG image wired through `head`. Cloudflare Web Analytics. Confirm
  the 404 page is useful. Check whether GitBook's per-page `.md` URLs need
  redirect rules.

- [x] **Phase 6: CI and deployment.** GitHub Actions running build and
  `starlight-links-validator` on PRs. Cloudflare Pages project, building from
  `site/`, with preview deployments. Run `verify_redirects.mjs` against the
  preview URL. Document the deploy and cutover process.

- [x] **Phase 7: Page-by-page QA.** Work through all 45 pages against the
  baseline text and screenshot diffs. Fix rendering and styling issues; every
  page must meet or exceed the GitBook version. Prioritise by what the diffs
  flag rather than reviewing all 45 by eye. Interactive polish of sidebar,
  header, and other chrome lands here.

- [ ] **Phase 8: Cutover.** Point `docs.kiln.tech` at Cloudflare Pages. Verify
  redirects against production. Submit the new sitemap to Search Console and
  watch for 404 spikes. Keep GitBook running until the new site is confirmed
  good, then decommission it and cancel the subscription.

- [ ] **Phase 9: Reconcile late content, then remove the transformer.** Diff
  `origin/main` against the freeze commit `1dde281` for anything that landed
  after the freeze. Convert those pages with `--out` into a scratch directory
  and copy them in individually — never a destructive full re-run. Once
  reconciled, delete `gitbook_to_starlight.py`, the `npm run convert` wiring,
  and the remaining migration scripts.

  **Half done, deliberately.** *Reconciliation is complete:* nothing landed on
  `origin/main` after the freeze that is not already here. Main was merged into
  this branch at `3e16f5a` before phase 3 converted, so PR #15's 8 files went
  through the audited transformer in the ordinary full conversion; `origin/main`
  `722d4cd` is that merge's own second parent and its GitBook sources are
  bit-identical to the ones this content was built from. No page needed copying
  in, so the `.mdx` merge hazard was never reached. *The transformer is not
  deleted*, because phase 8 is unperformed: GitBook is still live and still
  editable, and this is the only tool that can convert a further edit. Deleting
  it would also strand the recovery procedure, which needs today's copy at
  `HEAD` — the copy at `GITBOOK_TREE_COMMIT` is an older version whose output is
  wrong in ways nothing validates. The `npm run convert` wiring *was* removed:
  it could only invoke the destructive mode the backstop refuses. Delete
  `gitbook_to_starlight.py` and `test_gitbook_to_starlight.py` once phase 8
  decommissions GitBook; the checkbox stays unticked until then. See
  `phase_plans/phase_9.md`.
