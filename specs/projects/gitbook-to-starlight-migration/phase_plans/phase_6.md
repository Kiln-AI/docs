---
status: complete
---

# Phase 6: CI and Deployment

## Overview

Phases 2–5 made the site correct. This phase makes it *stay* correct without
anyone remembering to check, and writes down the parts a machine cannot do.

Three gates the functional spec names — build succeeds, no broken internal
link, every inventoried URL resolves — become a GitHub Actions workflow on
pull requests. A second workflow covers the questions that only a real
Cloudflare deployment can answer. And `site/README.md` gains the deploy and
cutover procedure, with the human-only steps added to the checklist phase 5
started rather than a competing one.

### What this environment could not do, and what was done instead

| Cannot | Substitute |
| --- | --- |
| Create the Cloudflare Pages project | Every setting it needs is written down in `README.md` > Project settings, and pinned in-repo where it can be: `.nvmrc` is the Node version Cloudflare reads. |
| Run a real preview deployment | The preview workflow's commands were rehearsed against a local server built to serve `dist` the way Pages documents it — rules, `_headers`, 308 normalisation, `404.html` — in both the passing and the failing direction. |
| Run GitHub Actions | Both workflows pass `actionlint` (first shown to catch a bad event name, a malformed expression, a `needs:` on a missing job and a mistyped step id, so the pass is not vacuous), and **every command in them was run locally, in order, on a clean checkout**. |
| Reach `docs.kiln.tech` or `developers.cloudflare.com` | Action versions were resolved through the git proxy (`git ls-remote`), which does work — `actions/checkout` and `actions/setup-node` are both on **v7**, not the v4/v5 that memory suggested. |

The Cloudflare-shaped rehearsal server is deliberately **not committed**. It
proves the workflow's commands, not Cloudflare, and phase 4's `--dist` mode
already covers the rule logic offline; a mock host in the repo would look like
a third oracle while adding nothing.

## Findings that shape the plan

### `starlight-links-validator` reports exactly the 24 anchors phase 2 predicted

Wired up with no configuration, the build fails with **25 invalid links in 12
files** — 24 distinct (page, link) pairs, one of which appears twice in
`docs/evals-and-specs/evaluations.md`. Every one is `invalid hash`, and the set
matches phase 2's table exactly once `README.md` is read as `index.md`. No
conversion damage has appeared since; nothing else in the corpus is broken.

That is the decision this phase has to make, and the options are not equal:

| Option | Why not |
| --- | --- |
| Fix the 24 | Content edits. The functional spec puts copy changes out of scope and phase 7 owns them. |
| `errorOnInvalidHashes: false` | Switches off anchor checking for the whole site — and anchors are the half most likely to break, since the converter re-derived every heading slug (phase 2 built a github-slugger port for exactly this). It would disable the check that the conversion most needed. |
| `failOnError: false` + compare the JSON report | Exact, but prints a 25-error report on every local build. Phase 2 already warned that printing 24 known problems on every build trains people to ignore the channel. |
| **`exclude`, page by page, audited** | Chosen. |

**Decision: excuse the 24 individually in `ref/stale_anchors.txt`, and audit
the list on every build.**

### The trade `exclude` makes, and what closes it

`exclude` is consulted at the *top* of `validateLink`, before any check. So an
excused link is exempt from **all** validation, not just its hash — delete
`/docs/prompts/` and five excused links would vanish from the report along
with it. An allowlist also outlives the problem it describes: phase 7 will fix
these anchors, and nothing about a suppressed check notices when it starts
suppressing nothing.

So the allowlist is not trusted; it is **re-derived from reality on every
build** by `staleAnchorsStillStale()`. Each line claims four things, and the
build fails naming the line if any of them stops being true:

1. the page still exists,
2. it still carries that link,
3. the link's target page still builds — this is the hole above,
4. the target still has no element with that `id`.

Check 4 is a substring test on the built HTML, which means the audit answers
"is this anchor still broken?" directly rather than by asking the validator,
and needs neither a slug port nor a second build.

Scoping to (page, link) rather than to the link alone is what keeps the list
from becoming an amnesty: three pages link `/docs/prompts/#prompt-generators`
and all three are listed individually, so a fourth page still fails.

### The verifier already catches the asset-versus-rule question phase 4 left open

`phase_4.md` > Carried forward says a Pages deployment preferring the static
asset would serve `/docs/quickstart` as a 200, and that "the verifier passes
either way by design; this needs an eye, not a test."

**That line is stale.** Phase 4's own step 4 later strengthened the verifier to
hold every source path to the destination `redirects.csv` names for it.
Verified against a server built to prefer assets: the run fails with `nothing
redirects it; redirects.csv says it should reach /docs/quickstart/` on all 45
slashless sitemap paths. So the bad outcome is already gated.

What is still unknown is *which* redirect a healthy deployment issues — 301
(our rule) or 308 (Cloudflare's own trailing-slash normalisation). Both are
correct. The preview workflow therefore keeps a step for it, reframed as
**recording the answer**, with the failure case documented as a second, clearer
signal rather than the only one.

### Node has to be pinned in one place, and that place is the repo root

The architecture fixes the build command as `cd site && npm run build` with
output `site/dist`, which means Cloudflare's project root is the repo root —
so that is where it looks for `.nvmrc`. CI reads the same file via
`node-version-file`. One pin, and CI cannot pass on a Node the deploy will not
use. `NODE_VERSION` stays in the checklist as a fallback, because some Pages
projects default to a Node far below Astro 7's floor.

## Steps

### 1. `site/ref/stale_anchors.txt` — the allowlist

24 lines of `<page> <link>`, generated from the validator's own JSON report so
the file cannot disagree with what the validator sees. Its header explains the
provenance, the four ways a line stops being true, and that repairing an
anchor means deleting its line.

### 2. `site/scripts/stale_anchors.mjs` — the parser, the predicate, the audit

```js
export function parseStaleAnchors(text)                          // -> {page, link, line}[]
export function staleAnchorExclusion(entries, contentDir)        // -> exclude predicate
export function retiredStaleAnchors(entries, readSource, readBuiltPage)
export function splitHash(link)
export function builtPagePath(urlPath)
```

`parseStaleAnchors` is strict — two fields, a markdown page path, a
root-relative link with a non-empty hash, no duplicates — because every field
is load-bearing and a typo in either one fails silently by *not* excusing
anything while looking like it does.

`retiredStaleAnchors` takes its two readers as arguments so the audit is
testable without a `dist` on disk.

### 3. `site/scripts/build_integrations.mjs` — a third post-build assertion

`staleAnchorsStillStale({ entries, contentDir })`, alongside the two phase 5
added. Registered before `starlight()` in the integrations array so a rotted
exclusion is reported even on a build the validator is about to fail for its
own reasons. (Both orderings work — an integration listed after `starlight()`
does get its `astro:build:done` after the validator's, measured with a probe
integration rather than assumed — but this order is the useful one.)

### 4. `site/astro.config.mjs`

`starlightLinksValidator({ exclude, sameSitePolicy: 'error' })` in `plugins`,
and the audit integration in `integrations`. `failOnError` stays at its
default `true`: the build itself fails on a broken link, so Cloudflare's build
is gated too, not only CI.

`sameSitePolicy: 'error'` is not the default. An internal link written as
`https://docs.kiln.tech/…` would send a reader of a *preview* deployment back
to production; there are none in the corpus today and this keeps it that way.

### 5. `.nvmrc` at the repo root

`22.22.2` — the version everything here was built and tested on.

### 6. `.github/workflows/ci.yml`

`pull_request` and pushes to `main`, `concurrency` cancelling superseded runs,
`permissions: contents: read`, `working-directory: site`:

```sh
npm ci
npm test
npm run redirects:check
npm run build
npm run verify:redirects -- --dist dist
```

`npm test`, never `test:py` or the bare discovery line — phase 4 recorded that
calling either suite directly silently skips the other.

`--min-paths` is **not** written in either workflow. It lives once, in the
`verify:redirects` script in `site/package.json`, and the callers pass only
their oracle (`-- --dist dist`, `-- --base-url "$BASE_URL"`). The floor has to
move in step with the inventory — the cutover procedure explicitly anticipates
adding `gsc` rows — and a floor that only some callers pass has stopped being a
floor. Verified by raising the script's floor to 9999 and watching the npm
invocation fail, so the flag demonstrably reaches the tool through `--`.

Most of the gating is inside `npm run build`, deliberately, because that is
what Cloudflare runs too: link validation, the stale-anchor audit, the
`dist/_headers` writer, and `optimizedImagesOnly()`.

### 7. `.github/workflows/verify-preview.yml`

The three checks that need a real host, on two triggers:

- `deployment_status` — automatic. It fires for *every* GitHub Deployment in
  the repo, so the job condition narrows twice: to a successful deployment, and
  to one whose environment name looks like Cloudflare's. Without the second
  clause any future integration that creates a Deployment would send this job
  at an unrelated `environment_url` and fail 176 requests for reasons nobody
  would connect to this file. **Never exercised here**, so the checklist asks a
  human to confirm it ran on the first preview. It also has to be on `main`
  before GitHub will fire it at all.

  The narrowing is spelled `endsWith(…, 'Preview')` rather than `== 'Preview'`,
  and the difference is the whole point. Cloudflare names the environment
  `<project-name> (Preview)`; the bare `Preview`/`Production` form is
  **Vercel's** convention, and an equality test against it would most likely
  have matched nothing — converting a narrowing into an off switch, which is
  the failure this workflow can least afford. `endsWith` covers both spellings
  and is case-insensitive, as all GitHub string comparison is.

  `timeout-minutes: 15` is not there because the run is slow — the verifier
  works six-wide and the 176 checks take under a second locally. It is there
  because Node's `fetch` has no default timeout, so an unresponsive host would
  otherwise hold a runner for the default 360 minutes.
- `workflow_dispatch` with a `deployment_url` input — manual, certain, and
  what the cutover procedure points at.

Steps: the redirect verifier **without `--dist`**, so the server has to do the
redirecting; the `Content-Type` on `/docs/quickstart.md`; and the status a
slashless path answers with. The URL is read through the environment rather
than interpolated into the shell, since it arrives in a webhook payload, and
`checkout` takes `ref: github.event.deployment.sha` so the inventory comes
from the commit that was actually deployed.

`concurrency` is keyed on the deployed *branch* rather than the environment: a
new push should supersede the verification of the preview it replaces, while
different PRs stay independent — and every preview shares one environment name,
so grouping on that would make every open PR cancel every other.

### 8. `site/README.md`

- **Link validation** — the two non-default settings, the 24 anchors, the
  options that were rejected and why, and the table of ways a line stops being
  true.
- **Continuous integration** — what runs, and that Node comes from one file.
- **Deploying to Cloudflare Pages** — rewritten: project settings as a table,
  how to verify a deployment (workflow and by hand), and a seven-step cutover
  order.
- Three new checklist items in the existing *Before cutover* list, plus the
  ones phase 5 wrote: create the project, confirm the preview workflow fired,
  confirm the static-rule cap.
- Layout table, *Still to do*, *Tests*, and *Working on it* updated.

### 9. `site/package.json`, `site/.gitignore`

`starlight-links-validator` as a devDependency; `.starlight-links-validator/`
ignored, since the JSON reporter writes there when someone turns it on to
debug.

## Tests

`site/scripts/stale_anchors.test.mjs` — 25 tests under `node:test`. They pin
down the *limits* of the one place a check is deliberately switched off:

**Parsing** — a page and a link with comments and blanks ignored; `.mdx`; the
real line number with comments counted; a third field; a page path that is
absolute, escapes the content directory via `..`, or is not markdown; a link
that is not root-relative, has no hash, or has an empty hash; a duplicate
naming the line it repeats.

**The committed file** — parses, holds no more than the 24 phase 2 recorded,
and every entry's link still appears in the page it names. A regression guard
in the spirit of `RepoStateTest`; the count must fall as phase 7 works, never
rise without a decision.

**The predicate** — excuses the exact pair; **does not excuse the same dead
anchor on an unlisted page**; does not excuse a different link on a listed
page; matches a deeply nested page.

**The audit** — retires nothing while the anchor is still stale, then one case
per way a line dies: page gone, link gone, **target page gone** (the
`exclude`-hides-everything hole), anchor back, anchor back with a
single-quoted id. Plus: the hash appearing in prose is not an element id, and
several retirements are reported in listed order.

**Link matching is by whole link, not substring** — `/docs/prompts/#custom-prompts`
is a strict prefix of `/docs/prompts/#custom-prompts-saved-prompts` and both are
on the allowlist, so a bare `includes()` would keep the shorter line alive
forever after it was repaired. Three tests: the prefix case retires, the exact
link does not, and a `.` in a link is matched literally rather than as a regex
wildcard.

**Path helpers** — `splitHash`, and `builtPagePath` for a page and for the root.

Totals: **340 tests**, up from 311 — 236 Python unchanged, 104 JavaScript.

## Verification

Everything below was run, not reasoned about.

### The gates fire

Each of these was produced by breaking the property and watching the build fail
with exit 1, then restoring and watching it pass:

| Broken | Result |
| --- | --- |
| A new `/docs/prompts/#prompt-generators` link added to `docs/agents.md` — *the same link that is excused on three other pages* | `Found 1 invalid link in 1 file`, exit 1 |
| An absolute `https://docs.kiln.tech/docs/quickstart/` link in content | `https://docs.kiln.tech can be omitted`, exit 1 |
| A stale anchor's link rewritten in the content, line left behind | `line 46: docs/prompts.md no longer links to /docs/prompts/#prompt-generators` |
| `## Prompt Generators` added back to `docs/prompts.md` | All **three** entries pointing at that anchor retired, by line number |
| `src/content/docs/docs/prompts.md` deleted | 8 entries retired, 3 of them `/docs/prompts/ no longer builds, so this line is excusing a broken page link rather than a stale anchor` |
| `plainMetadata` patched to `return image`, cold cache | `dist/_astro holds 68 unoptimized images, expected at most 4` — the phase 5 `image.clone` guard, confirmed to fire under CI's exact conditions |

### The CI workflow

Every step run in order on a **clean checkout** — no `node_modules`, no `dist`,
no `.astro`, no image cache — which is the condition CI actually runs in and
the one phase 5 warned changes the image measurement:

```
npm ci             403 packages
npm test           236 Python + 104 JavaScript, all pass
redirects:check    public/_redirects is up to date
npm run build      All internal links are valid. 47 pages. 45 .md endpoints.
verify:redirects   176 paths, 84 through local rules, all resolve
```

Cold-cache `dist/_astro`: **1 original, 2.0 MB** — matching phase 5's healthy
figure, so the image guard passes for the right reason rather than by luck.

`ruff check scripts/` clean. (`ruff format --check` still fails on all four
Python files, as phase 5 recorded; no formatter has ever been applied here and
adopting one belongs in its own commit.)

### The preview workflow

`actionlint` passes on both files — and was first shown to catch a misspelled
webhook event, an unparseable `if:` expression, a `needs:` on a missing job and
a mistyped `steps.<id>.outputs` reference, so the pass means something.

**What it does not check: webhook payload field names.** Mutating
`github.event.deployment_status.environment` to `.environmentt`, and
`github.event.deployment.ref` to `.deploymentt.ref`, both still lint clean —
`github.event` is an open object to it. So the environment clause in the
preview workflow has no automated check at all, in this session or in CI, and
the first-preview checklist item in `site/README.md` is the only thing that
verifies it. That item is written to say so.

The commands were then run against a local server that serves `dist` the way
Pages documents it, in both directions:

| Check | Healthy server | Broken server |
| --- | --- | --- |
| `verify_redirects --base-url … --min-paths 176` | 176 paths, server-side redirects, exit 0 | rules stripped → every source path fails |
| `.md` `Content-Type` | `text/markdown; charset=utf-8` | `_headers` removed → `application/octet-stream`, exit 1 |
| slashless path | `GET /docs/quickstart -> 301` | asset-preferring mode → `200`, exit 1 |

The asset-preferring run is also what showed phase 4's "the verifier passes
either way" note to be out of date: the verifier fails there too.

## Carried forward

New findings, on top of the phase 2–5 lists later phases inherit.

- **Nobody has seen a Cloudflare Pages deployment of this site.** Everything
  here is rehearsed against a local stand-in. The first real preview is the
  first time `_redirects`, `_headers` and the trailing-slash behaviour meet the
  actual host, and the checklist in `site/README.md` is written on that
  assumption. Phase 8's deadline.
- **`deployment_status` has never fired, and nothing here can check its
  condition.** The automatic half of the preview workflow is the one piece of
  this phase that could not be exercised even indirectly: it depends on the
  Pages GitHub integration creating deployments, and GitHub only runs
  `deployment_status` workflows from the default branch. `actionlint` does not
  validate webhook payload fields, so the two environment names the job
  condition tests for (`Preview`, `Production`) are unverified by any tool.

  A job that silently never runs is worse than no job, and this one has a
  second trap: `deployment_status` fires on every state transition, so a
  *healthy* deploy produces several runs whose job is **Skipped** — and a
  skipped job reports success. "The job is present and green" therefore looks
  identical in the working and the broken case. The checklist item is written
  to say what to look for instead: a run whose job **executed its steps**, with
  the redirect step showing 176 paths — and it separates "no runs at all"
  (re-authorize the Pages GitHub App) from "runs exist, job always skipped"
  (the condition does not match; read the payload's real environment name).
  `workflow_dispatch` is the certain path until that is confirmed.

  Review round 2 caught this condition mid-flight and it is worth recording
  why: the first spelling tested `environment == 'Preview'`, which is
  **Vercel's** naming. Cloudflare uses `<project-name> (Preview)`, so the
  equality would probably never have matched and the narrowing added in round 1
  would have silently disabled the job. `endsWith` fixes it, but the general
  lesson is that this condition is the one part of the phase with no oracle at
  all — not the build, not the tests, not actionlint — and it has now been
  wrong once.
- **`phase_4.md`'s asset-versus-rule note is stale and has been superseded
  here.** The verifier does catch a 200 at a slashless path; phase 4's own
  step 4 closed it and the Carried-forward note was written before that. Left
  in place in `phase_4.md` rather than edited, since this plan is the newer
  record.
- **The 24 excused anchors are phase 7's to repair, and the build will ask.**
  Fixing one is: fix the link or add the heading, then delete its line from
  `ref/stale_anchors.txt`. Leaving the line behind fails the build with the
  line number, so the list cannot silently outlive the problem — but it does
  mean a phase 7 agent editing these pages will hit build failures that are
  instructions rather than defects.
- **`sameSitePolicy: 'error'` forbids absolute self-links in content.** There
  are none today. If someone deliberately wants one — quoting the site's own
  URL in prose, say — the build will refuse it and the fix is either the
  root-relative form or an `exclude` entry. Worth knowing before it surprises
  someone in phase 7.
- **`sharp` carries a high-severity `npm audit` advisory** (libvips CVEs, fixed
  in 0.35 which is a breaking change). Pre-existing — `sharp` came in with
  phase 5's OG generator — and untouched here, because a major bump of the
  image toolchain in a CI phase is the wrong place for it. `npm audit` is
  deliberately **not** a CI gate for the same reason: it would fail every run
  today. Worth a small dedicated change.
- **The manual trigger checks out the dispatcher's ref, not the deployment's.**
  `workflow_dispatch` verifies whatever URL is pasted against the
  `redirects.csv` of whatever branch it was dispatched from, so dispatching
  from `main` against a PR's preview compares one commit's inventory with
  another commit's site and reports the disagreement as redirect failures. The
  `deployment_status` path has no such trap — it checks out
  `github.event.deployment.sha`. Documented in *Verifying a deployment* rather
  than fixed, because "verify this URL against this ref" is the useful shape
  for a cutover check against production.
- **`ruff check` is not in CI.** It passes, and adding it would mean a Python
  setup step and a lint gate the architecture does not ask for, which a future
  ruff release could break unrelatedly. Recorded as a deliberate omission
  rather than an oversight; `npm test` already runs the Python suites.
- **The link validator clears the content-layer cache on every build.** That is
  `clearContentLayerCache` inside the plugin, not something configured here. It
  costs a couple of seconds locally and nothing in CI, which starts cold
  anyway — but it means `npm run build` is now always a cold content build.
- **`_headers` is verified on the wire only by the preview workflow.** Phase 5
  left this open and it is now automated rather than closed: the check exists
  and has been rehearsed, but it has never been run against Cloudflare. Same
  status as everything else in this list — built, not observed.
