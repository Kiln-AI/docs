---
status: complete
---

# Implementation Plan: GitBook → Astro Starlight Migration

Ordered by dependency. Phases 1 and 2 come first because they must happen
while GitBook is still live; phase 9 must be last because it removes our
ability to convert anything else.

## Where this stands

Phases 2-7 are done. **Three checkboxes are open, and none of them is open
because the work was forgotten.** Each is blocked on something this environment
cannot provide, and each has a different closing condition:

| Phase | Why it is open | What closes it |
| --- | --- | --- |
| **1. Capture the baseline** | Needs real Chrome and public internet; egress to `docs.kiln.tech` is blocked here. Never performed. | Nothing, now. It had to happen while GitBook was live and before phase 7 needed it, and neither is still true. Phase 7 was completed against a mechanical sweep instead — see `phase_plans/phase_7.md`. **It expires entirely at cutover step 8**; the parts still worth capturing are collected as group 1 of the pre-cutover checklist in `site/README.md`. |
| **8. Cutover** | Every action needs credentials on an account nobody in this session holds — Cloudflare, the `kiln.tech` DNS zone, Search Console, GitBook billing — and each is irreversible. Deliberately not attempted; see `phase_plans/phase_8.md`. | A human following the cutover runbook in `site/README.md`. The phase's deliverable is that runbook, and it is finished. |
| **9. Reconcile, then remove the transformer** | Reconciliation is **done and proven** (nothing landed on `main` after the freeze that is not already here). The deletion half is deliberately deferred, because phase 8 has not run and GitBook is still editable. | Cutover step 8. Once GitBook is decommissioned, delete `site/scripts/gitbook_to_starlight.py` and `site/scripts/test_gitbook_to_starlight.py`. Step 8 and the `Still to do` list in `site/README.md` both say so, so it is not reachable only from here. |

Read together: **the project is complete up to the point where it needs
credentials.** What is left is one human-operated cutover, plus a two-file
deletion that the cutover's own final step triggers.

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
  9 reconciliation (and was removed in phase 9, once that reconciliation proved
  to be already complete). (Phase 2 added a backstop: the default run refuses when
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

  **Deliberately unperformed.** Every action here needs credentials nobody in
  this session holds, and each is irreversible; egress to `docs.kiln.tech` is
  blocked besides. The phase instead produced the cutover runbook in
  `site/README.md` and verified locally everything that could be verified
  locally. A human runs it from there. The checkbox stays unticked until
  someone does. See `phase_plans/phase_8.md`.

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
