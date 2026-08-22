---
status: draft
---

# Phase 8: Cutover

## Overview

The implementation plan's scope for this phase is four outward-facing actions:
point `docs.kiln.tech` at Cloudflare Pages, verify redirects against
production, submit the sitemap to Search Console and watch for 404 spikes, then
decommission GitBook and cancel the subscription.

**None of them can be performed from this environment, and none of them should
be attempted from it.** Each needs credentials on an account nobody in this
session holds — Cloudflare, the DNS zone for `kiln.tech`, Google Search
Console, GitBook billing — and each is irreversible or close to it. Egress to
`docs.kiln.tech` is blocked, so the live site cannot be reached either.

So this phase does not execute the cutover. It does the two things that can be
done from here:

1. **Make the cutover executable by a human without rediscovery.** The runbook
   in `site/README.md` is the deliverable; this plan points at it and does not
   duplicate it. Everything a person needs while the old site is still live and
   the clock is running belongs in one document they can follow top to bottom.
2. **Verify locally everything the runbook claims that can be verified
   locally**, and record honestly what cannot.

### Why the runbook is the deliverable and not this plan

Whoever performs the cutover will not be reading `specs/`. They will be in the
repo, under time pressure, with the old site still serving traffic. A procedure
that lives in a phase plan is a procedure that gets rediscovered. The runbook
lives next to the commands it tells you to run.

This plan records what changed in it and why, and what remains unverifiable.

## The state this phase inherited

The runbook already had a *Deploying to Cloudflare Pages* section from phase 6:
an intro, a human checklist, project settings, deployment verification and a
cutover procedure. It was sound in structure. What it was missing was
everything about the situation going wrong, and half of what expires.

Read as "the document someone follows under time pressure with the old site
still live", the gaps were:

- **Two of the three expiring probes were not in it at all.** The `.md` URL
  spelling probe was there, correctly placed first and correctly labelled as
  expiring. The **flat-alias probe** and the **Search Console indexed-pages
  export** — the two things that would turn phase 4's 34 inferred
  `alias-generated` rows and the missing historical URLs into fact — appeared
  only in *Still to do* and *Adding to the inventory*, as background rather
  than as dated work. The **page baseline** (phase 1, never run) was in *Still
  to do* with no mention that decommission ends it.
- **No rollback.** The procedure described going forward only. The two things
  rollback actually depends on — knowing the DNS record you are replacing, and
  having lowered its TTL beforehand — are both *pre*-cutover actions, so their
  absence from the checklist made rollback not merely undocumented but
  materially harder.
- **"Watch for 404 spikes" was one clause.** No instrument, no threshold, no
  reading of what a spike would mean given that 34 rows are inferred, and no
  link to the fix path that already exists.
- **No single pre-cutover verification.** Five green commands existed, spread
  across four sections of the README.
- **Commands did not say where to stand.** The *Deploying* section is the one a
  reader jumps straight to, and its commands are all `site/`-relative with no
  `cd`. This project has already shipped this exact bug twice.

## Steps

### 1. Audit and rewrite `site/README.md` > Deploying to Cloudflare Pages

Rewrite in place. Structure, in the order a reader meets it:

| Section | Purpose |
| --- | --- |
| Intro | Adds **"every command in this section runs from `site/`"** with `cd site && npm ci`, and points at the checklist before the procedure. |
| Before cutover | Regrouped into three numbered groups, below. |
| Project settings | Unchanged — it was correct. |
| **The pre-cutover check** | New. Step 3. |
| Verifying a deployment | Kept; commands given a `URL=` variable so they are copy-pasteable, `curl -sI` replaced with an explicit `-w` form, and the browser sweep added. |
| Cutover | Reworked. Step 5. |
| **If it goes wrong: rolling back** | New. Step 6. |
| **Watching for 404s** | New. Step 7. |

### 2. Regroup the human checklist by what expires

The old checklist was one list with the expiring item flagged in bold. Replace
with three explicitly named groups, because "ordered so each step is possible
when you reach it" is a weaker property than "these three stop being possible
forever, and the rest do not".

- **Group 1 — while GitBook is still live.** The `.md` spelling probe, the flat
  alias probe, the Search Console export, the page baseline. Prefaced with the
  reason the group exists and an instruction to save raw output rather than
  conclusions. Each item carries a runnable command where one exists.
- **Group 2 — set up the deployment.** Pages project, analytics token, confirm
  `deployment_status` actually fired. Carried over from phase 6 unchanged; it
  was already right.
- **Group 3 — before the site becomes the public one.** Favicon and OG image,
  the two descriptions nobody at Kiln wrote, the rule cap, **plus the two new
  rollback prerequisites**: write down the current DNS record verbatim, and
  lower its TTL to 60s a day ahead.

Group 1's commands are the ones this phase cannot run. Write them so they can
be pasted:

```sh
# the .md spelling: which candidate answers as markdown?
for path in /docs/quickstart.md /docs/quickstart/index.md /docs/quickstart/; do
  curl -sS -o /dev/null -w "%{http_code} %{content_type} <- $path\n" \
    "https://docs.kiln.tech$path"
done

# all 17 slashless alias-generated paths, with where GitBook sent each one
awk -F, '$4=="alias-generated" && $1 !~ /\/$/ {print $1}' redirects.csv \
| while read -r path; do
    printf '%s %s\n' "$path" \
      "$(curl -sS -o /dev/null -w '%{http_code} %{redirect_url}' \
           "https://docs.kiln.tech$path")"
  done | tee ref/alias_probe.txt
```

`%{redirect_url}` is not optional: a `301` proves the alias existed but not
where GitBook sent it, and the promotion step freezes our *inferred*
destination as fact. See step 13.

State what the alias probe is *for*, because it is counter-intuitive: a
generated row for a URL GitBook never served is dead weight, not a defect —
`_alias_rows` already refuses to generate an alias that would shadow a real
page, so an unused one costs nothing. The inferred rows can only be wrong by
being **too few**. The probe's value is discovering aliases the pattern failed
to generate, including the site-root form (`/fine-tuning-guide` rather than
`/docs/fine-tuning-guide`) that phase 4 flagged and could not settle. Step 14
has the full reasoning and its caveat.

### 3. Assemble the pre-cutover verification

One `&&` chain, from `site/`, reusing what exists and adding nothing:

```sh
cd site && npm ci \
  && npm test \
  && npm run redirects:check \
  && npm run build \
  && npm run verify:redirects -- --dist dist \
  && npm run qa \
  && echo "PRE-CUTOVER CHECKS PASSED"
```

`&&` so the first failure stops the chain and the closing line is the only
green signal. Follow it with a table of what each link proves, so a reader can
tell which property they lost when one fails. Then the browser half, which CI
cannot run, as a separate two-command step.

Deliberately **not** a new npm script. The honest reason is not that it
mirrors CI — it does not: it is the CI set *plus* `npm run qa`, which CI runs
in neither half. It is that a `verify:precutover` script would be a second
place for the list to live, drifting from `ci.yml` on one side and from the
runbook prose that explains each link on the other. A chain the reader can see
is a chain they can shorten when one link is inapplicable.

### 4. Verify every claim in the section that can be checked locally

Run every command as written, from the directory the reader is standing in.
Findings become steps 8–10 below.

### 5. Rework the cutover procedure

Keep the ordering, fix what it assumed:

- Front it with the two gates: finish group 1, then run the pre-cutover check.
- Merge the old steps 2 and 3 (add custom domain / point DNS). On a zone
  already at Cloudflare they are one action, and describing them as two invites
  a reader to look for a second thing to do. Cover both zone cases.
- Add the certificate-issuance window explicitly: **give it fifteen minutes
  before concluding anything**. A TLS error immediately after adding a custom
  domain is normal, and rolling back on it burns the window.
- Mark step 8 (decommission) as the project's one irreversible act, and state
  what it destroys: the rollback option and every group 1 answer.

### 6. Write the rollback plan

Short and concrete. Restore the recorded record, remove the custom domain, wait
out the TTL you lowered, confirm from a resolver you have not used. Then the
part that is not obvious:

- **Rollback does not undo the 301s already served.** Browsers cache them,
  often until the cache is cleared. Blast radius is whoever visited during the
  window, so a short window is the mitigation.
- The functional spec's **302 launch-week option** is the way to remove that
  risk rather than bound it. Give the mechanics, including
  **`--allow-temporary`** on the verifier — which exists in
  `scripts/verify_redirects.mjs` but appears nowhere in the README. Without it
  a deliberate 302 window fails the verifier, which is the correct default and
  exactly wrong during that window.
- **When to roll back and when not to**, as two lists. Roll back for: not
  serving at all past the certificate window; `verify:redirects` failing
  *broadly* against production, which means `_redirects` is not being applied.
  Do not roll back for: a handful of unpredicted 404s, a missing analytics
  beacon, one page rendering badly.

### 7. Make the 404 watch actionable

Search Console → Indexing → Pages → *Not found (404)*, with the report's two-
to three-day lag stated so day one silence is not read as success.

**Threshold is distinct paths, not hits** — 45 pages, and any volume-based
threshold is noise. Then a table separating the two failure shapes, because
they need opposite responses:

| Seen | Means | Do |
| --- | --- | --- |
| 404s on paths **not** in `redirects.csv` | Inventory gap — an alias the pattern missed, or a historical URL only the Search Console export had | Add `gsc` rows, refresh, ship forward |
| A 404 on a path that **is** in `redirects.csv` | The rules are not being applied at all | Verify against production; this is a rollback case |
| Nothing new for a full reporting cycle | Quiet | Decommission GitBook |

The fix path is phase 4's existing `--refresh-csv` reconciliation, linked
rather than restated, plus the floor move from step 9.

### 8. Fix `qa_pages.mjs`: `--base-url` without `--browser` was a silent no-op

`--base-url` is parsed unconditionally but consumed only inside
`sweepInBrowser`, which runs only under `--browser`. So:

```
$ npm run qa -- --base-url https://not-a-real-host.invalid
scanned 46 content files for residual GitBook markup
no findings          # exit 0, nothing contacted
```

This is the runbook's production check reporting success having tested nothing.
Reject the combination in `parseArgs` with a message naming the fix, and add a
test. Update the *Page QA* section, which said only "It takes `--base-url`".

### 9. Make the `--min-paths` floor bidirectional

The README said "raise it in `package.json` when the inventory grows". The
inventory also **shrinks**, on one expected path: the alias probe disproving a
row, whose documented settle-up deletes both of its rows. Confirmed by
simulation — see Verification. The verifier then stops with `is redirects.csv
truncated?`, which is the wrong diagnosis at the worst moment, and the README's
own escape hatch (`--min-paths N` on the command line) is the thing it warns
against.

- Extend the verifier's floor error to name the legitimate cause and the number
  to put in `package.json`.
- Rewrite *The floor* to say the floor moves both ways, and that a failure
  right after a disproved-alias refresh is the gate working.
- Add the floor move as a numbered step in *Adding to the inventory*.

### 10. Make `qa_pages.test.mjs` hermetic

The stub-Playwright test resolves its stub through `NODE_PATH`, which node
consults **after** the `node_modules` walk. It therefore passes only while
Playwright is *not* installed — and the README instructs installing it into
`site/` for the browser sweep, which the pre-cutover check now points at. A
reader who follows the runbook in order gets a red `npm test`.

Fix by copying the sweep into a scratch tree with the stub in *its*
`node_modules`, so ordinary resolution finds it. The sweep imports nothing but
node builtins, which is what makes this safe.

### 11. Fix the fourth broken command: the 404 fix path verified a stale `dist`

Found in review, in the worst possible place — the post-cutover incident path.
*Watching for 404s* > *The fix* was `add row → --refresh-csv → move the floor →
npm run verify:redirects -- --dist dist`. `--refresh-csv` writes
`public/_redirects`; only `npm run build` copies it into `dist/_redirects`,
which is what the verifier reads. There was no build in the list.

Reproduced: adding one `gsc` row and following the four steps verbatim gives
`nothing redirects it; redirects.csv says it should reach /docs/quickstart/`
against the row just added correctly. On a fresh clone there is no `dist` and
it is `ENOENT`. Same wrong-diagnosis-under-pressure shape as step 9, landing on
someone responding to a live 404 spike.

Step 4 becomes `npm run build && npm run verify:redirects -- --dist dist`, with
a note saying why the build is load-bearing. The other two copies of the terse
command (*Verifying*, *Continuous integration*) both already have `npm run
build` immediately above; *Adding to the inventory* escapes by delegating.
Checked all four.

### 12. Close two more zero-work-reports-success holes in `qa_pages.mjs`

Step 8's guard was right in intent and too narrow in both directions.

- **`options.baseUrl && !options.browser` tests truthiness**, so
  `--base-url ""` is falsy and slips through to the same silent no-op, exit 0.
  Reachable straight from this runbook's own `URL=…` idiom when the variable
  never got set. Test `!== null`, and reject an empty value at parse time for
  `--base-url`, `--dist` and `--content` alike.
- **A zero-page sweep reported success.** `--browser --base-url <prod>` against
  an unbuilt `dist` printed `rendered 0 pages` / `no findings`, exit 0, without
  resolving the host — the page list comes from `dist` even when the pages are
  fetched. Throw when `pages.length === 0`.

Both are the defect class step 8 was written to kill, arriving by other doors.

### 13. Keep the alias probe's `Location`

The probe recorded `%{http_code}` only. A `301` proves the alias existed; it
does not say where GitBook sent it — and *Adding to the inventory* step 2 then
promotes the row to `alias`, freezing our *inferred* destination as confirmed
fact on evidence that never mentioned it. Add `%{redirect_url}`. Group 1's
whole framing is "save raw output, this is unrepeatable", and this is the field
you cannot go back for.

### 14. Correct the "can only be too few" claim's reasoning

The conclusion holds — verified independently: no `alias-generated` `old_path`
collides with a built page, another row's `old_path`, or any row's `new_path`.
But the reason given was wrong. It is not "nothing links to it, so the rule
never fires"; it is that `_alias_rows` in `build_redirects.py` skips an alias
`page_exists()` matches and one two nested pages both claim.

That distinction has teeth, because the guard runs at **generation** time. A
page added later at a path an existing alias row claims is shadowed silently —
neither `redirects:check` nor the link validator compares the two. Record the
real reason and the caveat.

### 15. Note that `--refresh-csv` ends a 302 window

If the launch-week 302 option is taken, the refresh rebuilds every generated
row at its default `301`. Verified: 130 rows at `302` come out of a refresh as
130 at `301` — including `md-endpoint`, so it is every row, not the three
sources first assumed. That means following *The fix* during a 302 window
reverts the whole map. Loud, but easy to scroll past. One paragraph in *If it
goes wrong*.

## Tests

- `parseArgs refuses --base-url without --browser rather than ignoring it` —
  asserts a `QaError` naming `--browser`, and that the pair together still
  parses. The regression is a false green on the production check.
- `a browser that fails after it loads does not swallow them either` — existing
  test, made hermetic. Must pass **both** with Playwright installed in
  `site/node_modules` and without it; run both ways.
- `parseArgs rejects an empty value rather than reading it as absent` — all
  three value-taking flags, and `--base-url ""` still refused when `--browser`
  is present. Empty is invalid, not merely unpaired.
- `--browser refuses to report on a dist with no built pages` — exits 2, says
  `no built pages`, and still prints the static findings it did have.
- The full suite (`npm test`) run with Playwright present, since that is the
  state the runbook puts the reader's tree in — and again with it absent, since
  that is CI's state.

Note that the zero-page guard preempts the launch-failure path, so the stub
test now writes a `dist/index.html` to get as far as `launch()`. Without it
that test silently stops testing what it names.

## Verification performed in this phase

Everything below was run locally. What could not be is in *Not verifiable from
here*.

| Claim | How checked | Result |
| --- | --- | --- |
| The whole pre-cutover chain runs as written from the repo root | Ran it verbatim | Passes, ends `PRE-CUTOVER CHECKS PASSED` |
| `npm run verify:redirects -- --dist dist` checks 176 paths | Ran | `checked 176 paths`, 84 rules, all resolve |
| 84 rules, 130 rows, 34 `alias-generated` | Counted in `redirects.csv` / `public/_redirects` | Confirmed; 17 slashless aliases |
| `npm run qa -- --browser` is green | Ran, 46 pages × 2 viewports | No findings; only unreachable-external-image notes |
| Both Playwright install commands work as written from `site/` | Ran both | Work; `--no-save` leaves `package-lock.json` byte-identical |
| `npm run qa -- --base-url X` without `--browser` | Ran | **Silent no-op, exit 0** — fixed, step 8 |
| `npm test` with Playwright installed | Ran | **Failed 1 of 44 in `qa_pages.test.mjs`** — fixed, step 10 |
| `--refresh-csv` is idempotent today | Ran in a scratch copy | No change to `redirects.csv` |
| The disproved-alias settle-up works as documented | Simulated in a scratch copy: deleted both rows, added the exclusion, refreshed | Rows dropped correctly, 130 → 128 |
| …and what it does to the verifier | Ran the verifier after | **Fails the 176 floor** — fixed, step 9 |
| `--allow-temporary` exists for the 302 window | Read `verify_redirects.mjs` | Exists, undocumented; now documented |
| The `.md` and alias probe command shapes are correct | Ran both against a local `astro preview` | Correct output shape |
| Every internal anchor in `README.md` resolves | `github-slugger` over headings and `](#…)` links | 57 anchors, all resolve |
| The sitemap URL to submit | `dist/` contents and `redirects.csv` | `sitemap-index.xml` is real; `/sitemap.xml` is a redirect row |
| The 404 fix path, step 4 | Added a `gsc` row, refreshed, ran it verbatim | **Failed on a stale `dist`**; `ENOENT` with no `dist` — fixed, step 11 |
| …and with `npm run build` first | Same scratch copy | 177 paths, 85 rules, all resolve |
| `--base-url ""` | Ran | **`no findings`, exit 0** — fixed, step 12 |
| `--browser` against an unbuilt `dist` | Ran | **`rendered 0 pages`, exit 0** — fixed, step 12 |
| No `alias-generated` row shadows anything | Compared all 34 against built pages, other `old_path`s and all `new_path`s | No collisions; guard is in `_alias_rows` |
| `%{redirect_url}` captures the destination | Ran the probe against a local 301/404/200 server | Records the `Location`; empty on 404 and 200 |
| `--refresh-csv` reverts a 302 window | Set all 130 rows to `302` in a scratch copy, refreshed | All 130 back to `301` — documented, step 15 |

## Not verifiable from here — a human must confirm

Recorded so nobody re-derives the list under pressure. Everything in group 1 of
the checklist is on it by definition.

- **Every group 1 answer.** The `.md` URL spelling, whether each of the 34
  inferred alias rows is real, whether GitBook aliases at the site root, the
  Search Console historical URLs, and the page baseline. Egress is blocked;
  these are unanswerable here and unanswerable anywhere after decommission.
- **Every Cloudflare behaviour.** That Pages applies `_redirects`, that it
  honours `dist/_headers` so the `.md` endpoints keep `text/markdown`, and
  whether a slashless path answers 301 (our rule) or 308 (Cloudflare's
  normalisation). `.github/workflows/verify-preview.yml` runs all three against
  a real deployment; nothing here can.
- **That `deployment_status` fires and the job condition matches.** Phase 6's
  finding, unchanged: the environment-name guess
  (`<project-name> (Preview)`) has no oracle short of a real payload, and a
  wrong guess looks exactly like a healthy skip.
- **The current DNS record for `docs.kiln.tech`**, and whether `kiln.tech` is
  on Cloudflare. The runbook covers both cases; which one applies is unknown
  here, and the record's current value is the rollback anchor.
- **Whether the custom domain must be detached before or after DNS is
  restored, on rollback.** The runbook says detach first, reasoning that an
  attached domain may let Cloudflare re-assert its record, and a rollback that
  appears not to take is the worst thing to debug in the moment. That is
  reasoning, not observation, and it is flagged as such in place.
- **The Cloudflare static-redirect rule cap.** `MAX_RULES` is 2,000 from the
  architecture, unconfirmed. We emit 84, so this is bookkeeping.
- **Whether analytics receives data.** Needs the token, the project and real
  page views.

## Carried forward

For phase 9, and for whoever performs the cutover.

- **This phase did not perform the cutover. The implementation-plan checkbox
  for phase 8 stays UNTICKED, and this plan stays at `status: draft`, until a
  human has actually completed the cutover.** That is not bookkeeping
  pedantry: a ticked box is what a later agent reads as "`docs.kiln.tech`
  serves Starlight and GitBook is gone", and acting on that while GitBook is
  still live would skip group 1 and destroy evidence that cannot be recovered.

  What is complete is the runbook and everything verifiable without an account.
  What closes the box: group 1 run and its output saved, DNS moved,
  `verify:redirects` green against production, the sitemap submitted, the 404
  watch quiet for a full reporting cycle, and GitBook decommissioned. Its
  evidence is a live site, not a commit.
- **Phase 9 must not run before group 1.** The reconciliation diffs
  `origin/main` against the freeze commit `1dde281`. If group 1's probes add
  `gsc` or `alias` rows, they land in `redirects.csv` alongside that work, and
  the `--min-paths` floor moves with them.
- **If the `.md` probe disproves the spelling**, the fix is one line in
  `src/pages/[...slug].md.ts` plus a refresh — but the 45 `md-endpoint` rows
  and the `176` floor both move, and the *Machine-readable output* section's
  rationale needs rereading rather than editing around.
- **The 302 launch-week option is a live decision, not a default.** If it is
  taken, flipping back to 301 is a tracked follow-up the functional spec
  requires, and the verifier's `--allow-temporary` must come back off with it.
- **The alias probe's `Location` output has no consumer yet.**
  `ref/alias_probe.txt` is written by hand and read by a human against
  *Adding to the inventory*. If the probe ever runs, a row whose recorded
  `Location` disagrees with its `new_path` is a *wrong* row, not a confirmed
  one, and nothing automates that comparison.
- **`npm ci` removes an `--no-save` Playwright install.** The pre-cutover chain
  starts with `npm ci`, so the browser sweep's two install commands belong
  after it, which is how the runbook orders them. Worth knowing before someone
  reorders that block.
