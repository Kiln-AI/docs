---
status: complete
---

# Phase 4: Redirects

## Overview

Preserve every GitBook URL on the new site. This phase builds the redirect data
model (`site/redirects.csv`), the generator that turns it into a Cloudflare
Pages `_redirects` file, the verifier that proves the rules actually work, and
pins the trailing-slash behaviour that decides what the redirect targets even
look like.

The phase is unusual in one respect and the whole design turns on it: **the URL
inventory is real but incomplete.**

### What we have, and what we do not

Phase 1 — the live-site baseline capture — has not run in this environment and
cannot: egress to `docs.kiln.tech` is blocked by policy. A separate task is
doing it. So there is no crawl, no alias probe, and no Google Search Console
export.

What we do have is `site/ref/legacy_sitemap.xml`, the real GitBook sitemap,
saved by hand from a browser's XML view. It carries **46 URLs** and two
handling quirks:

1. The first line is the browser's prose banner (`This XML file does not appear
   to have any style information…`), so it is not well-formed XML at the top.
2. Some `<loc>` values are wrapped across newlines, so a naive parse yields
   URLs with embedded whitespace. Whitespace inside `<loc>` must be collapsed
   before the value is used.

It also contains **only nested paths**. It has no flat aliases, and the flat
alias is the exact class of URL that the repo cannot know about — the reason
phase 1's alias probe exists.

### The design consequence

Every row in `redirects.csv` carries a `source` that says where it came from
and, by implication, whether the URL is **known to exist** or **inferred from a
pattern**:

| `source` | Meaning | URL confirmed to exist? |
| --- | --- | --- |
| `sitemap` | Verbatim from `site/ref/legacy_sitemap.xml` | Yes |
| `alias-generated` | Produced by applying the documented flat-alias pattern | **No — inferred** |
| `structural` | A path we chose to catch, not one we observed | No — deliberate |
| `alias` | Flat alias confirmed 200 by phase 1's probe | Yes |
| `crawl` | Found by phase 1's link crawl | Yes |
| `gsc` | From the Search Console indexed-pages export | Yes (historically) |
| `manual` | Added by a human for a reason of their own | Human's call |

`alias-generated` is a new value, added on top of the architecture's enum
specifically so a generated guess is never filed under the same label as a
probe-confirmed URL. The architecture's `alias` keeps its meaning: confirmed.

The first three sources are **machine-generated** from files in `site/ref/`.
The last four are **human-supplied** and live only in the CSV. That split is
what makes reconciliation cheap: `build_redirects.py --refresh-csv`
regenerates the machine rows and preserves the human rows verbatim, so merging
phase 1's data later is *add rows, re-run, review the diff* — not a rebuild.

## Findings that shape the plan

### The sitemap and the committed content match exactly, 46 for 46

Cross-checking the 46 normalised sitemap paths against the 46 files under
`site/src/content/docs/` (45 doc pages plus the hand-written landing page)
gives an exact bijection: **no sitemap URL lacks a page, and no page lacks a
sitemap URL.** The constraint asked for any mismatch to be recorded as a
finding; the finding is that there is none. This also means every `new_path`
this phase emits points at a page that demonstrably exists.

### `/docs/` and `/developers/` 404 on the new site

There is no `src/content/docs/docs/index.md` and no
`src/content/docs/developers/index.md`, so neither section root is built.
Confirmed against a running `astro preview`: both return 404. Neither appears
in the GitBook sitemap either, but they are the two most obviously
hand-typeable paths on the site and the header nav points into both sections.
They get `structural` rows aimed at the same targets the nav uses.

### Starlight's canonical form is already trailing-slash

Before any change, the built output stamps
`<link rel="canonical" href="https://docs.kiln.tech/docs/quickstart/"/>`, emits
every internal link with a trailing slash, and generates `dist/sitemap-0.xml`
with 46 trailing-slash URLs — a set matching the legacy sitemap one-for-one.

So the choice is already made in practice, and setting `trailingSlash: 'always'`
plus `build.format: 'directory'` **records** it rather than changing it. Both
were verified to leave the build byte-identical (207 files, identical
checksums). The alternative — `trailingSlash: 'never'` with
`build.format: 'file'`, which would preserve GitBook's slashless URLs exactly
and need no redirects for the 46 — was rejected: it fights Starlight's own link
generation (`createPathFormatter`, `canonical.ts`, and the Pagefind
`data-strip-trailing-slash` hook all key off this setting), and the functional
spec already anticipates the trailing-slash difference and names a redirect as
the answer.

### `astro preview` 404s on slashless paths, so the verifier needs local rules

With `trailingSlash: 'always'`, `astro preview` serves `/docs/quickstart/` as
200 and `/docs/quickstart` as **404** (under the previous implicit `'ignore'`
it served both). `astro preview` does not read `_redirects` — that file means
nothing outside Cloudflare Pages.

So a naive `verify_redirects.mjs --base-url http://localhost:4321` would report
83 failures against a perfectly good build — one for every rule. The verifier
therefore takes an
optional rule set to apply **client-side** before it requests anything, which
is what makes it runnable against `astro preview` — and which is deliberately
*not* used in phase 6 against the Cloudflare preview, where the server itself
must do the redirecting.

## Data model

`site/redirects.csv`, committed and human-reviewable:

```csv
old_path,new_path,status,source
/docs/quickstart,/docs/quickstart/,301,sitemap
/docs/fine-tuning-guide,/docs/fine-tuning/fine-tuning-guide/,301,alias-generated
/docs,/docs/quickstart/,301,structural
```

- `old_path` — path only, no origin, leading slash required
- `new_path` — path on the new site
- `status` — `301`; `302` is accepted by the schema for a deliberate rollback
  window but nothing uses it today
- `source` — the enum above

Row inventory, 84 rows total:

| Source | Rows | Rules emitted | Derivation |
| --- | --- | --- | --- |
| `sitemap` | 46 | 45 | Each sitemap path → its trailing-slash form. `/` → `/` is a no-op and is dropped at build time. |
| `alias-generated` | 34 | 34 | The 17 three-segment sitemap paths, flattened by dropping the middle segment, in both slashless and slashed form. |
| `structural` | 4 | 4 | `/docs`, `/docs/`, `/developers`, `/developers/` |

The 17 nested paths that produce aliases are the children of `fine-tuning` (3),
`evals-and-specs` (7), `tools-and-mcp` (2), `prompts` (2),
`synthetic-data-generation` (2) and `collaboration` (1).

Both slash forms are generated for aliases because Cloudflare's implicit
trailing-slash normalisation cannot help here: there is no asset at
`/docs/fine-tuning-guide/` for it to normalise towards. The slashless form is
what GitBook serves and what Google will have indexed; the slashed form is
free insurance.

The 46th sitemap row (`/` → `/`) is kept in the CSV on purpose. The CSV is the
record of the inventory; `_redirects` is the derived rule set. Dropping the
no-op belongs to the generator, not to the record.

## Steps

### 1. `site/astro.config.mjs` — pin the URL form (done first, everything targets it)

```js
export default defineConfig({
  site: 'https://docs.kiln.tech',
  trailingSlash: 'always',
  build: { format: 'directory' },
  // …
});
```

With a comment saying why it is explicit rather than inherited.

### 2. `site/ref/alias_exclusions.txt`

A commented, initially-empty file listing flat-alias paths that phase 1's probe
proved do not exist. `--refresh-csv` skips them, so deleting a disproved row
from the CSV makes it stay deleted. Its header comment is where the
reconciliation instructions live in-place.

### 3. `site/scripts/build_redirects.py`

One script, three modes, sharing one set of path helpers.

Core functions, all pure and unit-testable:

```python
def parse_sitemap(xml_text: str) -> list[str]:
    """<loc> values with internal whitespace collapsed, deduped, in document
    order. Tolerates the browser prose banner ahead of the XML."""

def canonical_path(url_or_path: str) -> str:
    """'https://docs.kiln.tech/docs/x' -> '/docs/x'. Rejects other origins,
    and any path that is not normalised: protocol-relative '//host/x',
    doubled slashes, '.' and '..' segments."""

def flat_alias_paths(nested_path: str) -> list[str]:
    """'/docs/a/b' -> ['/docs/b', '/docs/b/']. Fewer than 3 segments -> []."""

def read_rows(csv_text: str) -> list[Row]:
    """Parse and validate. Raises RedirectError on a bad status, an unknown
    source, a path without a leading slash, or a missing column, quoting the
    row's real line number in the file, comments counted."""

def read_annotations(csv_text: str) -> Annotations:
    """The '#' comments in the CSV, tied to the row each sits above, so a
    human's note travels with its row through a refresh."""

def flatten_chains(rows: list[Row]) -> list[Row]:
    """A->B, B->C  =>  A->C and B->C. Raises on a cycle."""

def dedupe(rows: list[Row]) -> list[Row]:
    """Identical duplicates collapse; a repeated old_path with a different
    new_path raises RedirectError naming the path and both targets."""

def check_slash_variants(rows: list[Row]) -> None:
    """'/a' and '/a/' are one URL to a reader and two keys to Cloudflare.
    Sharing a target is fine and deliberate; disagreeing on one raises."""

def render_redirects(rows: list[Row]) -> str:
    """'/old /new 301' per line, with a generated-by header and one comment
    line per source group."""
```

Order of operations in the build: read → validate → drop `old_path ==
new_path` → dedupe → check slash variants → flatten → validate targets exist →
cap check → render. Flattening after deduping means a conflict is reported
against what the human wrote, not against a synthesised intermediate.

An inventory with no rows is an error, not an empty rule set: a truncated CSV
should stop the build rather than quietly ship zero redirects. `--refresh-csv`
is exempt, since a header-only CSV is how the file gets bootstrapped.

Target validation resolves each final `new_path` against
`site/src/content/docs/`, mapping `/a/b/` to `a/b.md`, `a/b.mdx`, `a/b/index.md`
or `a/b/index.mdx`, and `/` to `index.*`. A target with no page is an error —
"a redirect target does not exist" is a named failure mode in the functional
spec and this is the cheapest place to catch it.

Rule cap: `MAX_RULES = 2000`, the figure the architecture records for
Cloudflare Pages with a note that it wants confirming against current docs.
Exceeding it errors rather than truncating. We are at 83.

Modes:

| Invocation | Behaviour |
| --- | --- |
| `build_redirects.py` | CSV → `site/public/_redirects` |
| `build_redirects.py --check` | Renders and compares against the committed `_redirects`; non-zero and a diff if stale. This is the CI gate. |
| `build_redirects.py --refresh-csv` | Regenerates the machine-generated rows from `site/ref/`, merges them with the preserved human rows, rewrites the CSV, prints an added/removed/changed summary, then rebuilds `_redirects`. |

`--refresh-csv` merge rules:

- **Preserved** = every existing row whose source is not `sitemap`,
  `alias-generated` or `structural`.
- **Generated** = sitemap rows, then alias rows, then structural rows — each
  skipped if its `old_path` already appears in a preserved row, and alias rows
  additionally skipped if listed in `alias_exclusions.txt` or if the flattened
  path collides with a real page.
- Output order: sitemap (sitemap order), aliases (sitemap order of their
  parent), structural, then preserved rows in their original file order.
  `#` comments are re-emitted above the row they were written above.

The summary diffs **whole rows**, not just the set of `old_path`s. Keying it on
paths alone would let a hand-edited target on a generated row be reverted in
silence, which is the likeliest way to lose a deliberate change.

The "skip if a preserved row already claims this `old_path`" rule is what lets
a human promote a confirmed alias: change its `source` from `alias-generated`
to `alias` and refresh will leave it alone instead of regenerating a duplicate.

### 4. `site/scripts/verify_redirects.mjs`

Reads `redirects.csv`, checks **every `old_path` and every distinct
`new_path`**, and exits non-zero with a list on any failure. Checking targets
as well as sources is what catches a redirect that points at nothing.

```
node scripts/verify_redirects.mjs --dist dist
node scripts/verify_redirects.mjs --base-url https://<preview>.pages.dev
node scripts/verify_redirects.mjs --base-url http://localhost:4321 --dist dist
```

Every source path is held to the destination `redirects.csv` names for it, not
merely to landing somewhere that exists. Without that, `--dist` would prove
only 38 of the 83 rules: the 45 slashless `sitemap` paths resolve to
`x/index.html` whether or not their rule is present, so deleting one would go
unnoticed. With it, removing any single rule fails the run.

`--dist DIR` does two jobs: it supplies the rule set (`DIR/_redirects`) and, on
its own, it is the offline oracle — resolve the path through the rules, then
assert the destination is **a file** in `DIR`. It has to be a file, not merely
something that exists: `dist/docs/` is a directory and nothing is served at
`/docs`, so an existence test would pass a path that 404s in production and let
a dropped rule sail through CI. That is the offline check the architecture asks
for, and it needs no server.

A run that checks nothing is a failure, not a pass. Three things enforce that,
because "the gate reported success without checking anything" is this phase's
characteristic failure mode:

- an empty inventory is an error, and `--min-paths N` pins the floor higher for
  the production run before cutover;
- `--concurrency` and `--min-paths` must parse as positive integers, the same
  strictness `parseArgs` already applied to unknown and valueless flags — a
  mistyped floor must not silently switch the floor off;
- the worker pool counts completions and refuses to report a run where any path
  went unchecked. That is the structural half: a sparse results array's holes
  are skipped by `filter`, so an incomplete run would otherwise be
  indistinguishable from a clean one, whatever the cause.

`--base-url URL` is the HTTP oracle. Alone, the *server* must do the
redirecting — that is phase 6 and phase 8 against Cloudflare. Combined with
`--dist`, rules are applied locally first and only the resolved target is
fetched, which is how it runs against `astro preview`. Rows resolved locally
are reported as such so the two runs can never be confused for each other.

Acceptance: 200, or a chain of permanent redirects (301, 308) ending in 200.
Cloudflare Pages issues **308** for its own trailing-slash normalisation, so
restricting to 301 would fail a correct deployment. 302/307 fail unless
`--allow-temporary` is passed, which is there for the spec's optional
launch-week rollback window. Max 5 hops.

Rule matching is exact-path only. A rule containing `*` or `:` raises rather
than silently failing to match — we emit none today, and a splat appearing
later should stop the verifier rather than let it lie.

### 5. `site/package.json`

```json
"redirects": "python3 scripts/build_redirects.py",
"redirects:check": "python3 scripts/build_redirects.py --check",
"verify:redirects": "node scripts/verify_redirects.mjs",
"test": "npm run test:py && npm run test:js",
"test:py": "python3 -m unittest discover -s scripts -p 'test_*.py' -t scripts",
"test:js": "node --test \"scripts/*.test.mjs\""
```

`npm run build` stays plain `astro build`. Phase 3 deliberately unwired Python
from the build, and `_redirects` is committed rather than generated at deploy
time, so Cloudflare Pages needs no Python. `redirects:check` is what keeps the
committed file honest.

### 6. `site/README.md`

A "Redirects" section: the data model, the three commands, how to verify
locally against `astro preview`, and the reconciliation procedure for when
phase 1's data arrives.

## Tests

`site/scripts/test_build_redirects.py` — 91 tests, stdlib `unittest`, grouped
by the function under test:

| Class | Tests | What it pins down |
| --- | --- | --- |
| `SitemapTest` | 8 | The two real-file quirks — a `<loc>` wrapped across newlines, and the browser prose banner ahead of the XML — plus dedupe-in-document-order, a rejected sitemap *index*, malformed XML, and a regression guard asserting the committed file still holds 46 URLs with no embedded whitespace. |
| `CanonicalPathTest` | 13 | Origin stripping, bare origin to `/`, and the rejections: a foreign origin, a missing leading slash, a query string, a fragment, an empty value, the unnormalised forms — protocol-relative `//host/x`, `/a//b`, `/a/../b` — and internal whitespace, which would render as extra tokens in a rule line. |
| `FlatAliasTest` | 5 | Three segments give both slash forms; two segments and `/` give none; four segments drop every middle; a trailing slash on the nested path is ignored. |
| `ExclusionsTest` | 3 | One entry covers both slash forms; comments and blanks ignored. |
| `ReadRowsTest` | 11 | Header, column count, status, source and path validation, each reporting its **real** line number with comment lines counted; round-trip through `write_rows`. |
| `DedupeTest` | 4 | Identical duplicates collapse; conflicting targets raise an error naming the path and *both* targets; conflicting statuses raise; order is preserved. |
| `FlattenTest` | 5 | Two- and three-hop chains collapse to one hop, unrelated rows are untouched, and both a direct and a three-node cycle raise. |
| `BuildRulesTest` | 6 | Self-redirects dropped; a target with no page raises; targets resolve through both `a/b.md` and `a/b/index.mdx`; the rule cap is enforced. |
| `RenderTest` | 4 | One rule per line, a comment per source group, counts in the header, and no empty groups. |
| `RefreshTest` | 10 | The merge semantics: human rows preserved verbatim, stale generated rows dropped, no regeneration over a preserved `old_path`, exclusions honoured, aliases dropped when they collide with a real page or when two nested pages would both claim them, and idempotence. |
| `CommandTest` | 12 | The three CLI modes end to end against a scratch directory: refresh writes both files, check passes fresh and fails stale or missing, a missing CSV is an error not a traceback, a CSV that yields no rules is refused by build — rows are not rules, so a file of only self-redirects counts — but repopulated by refresh, a comment stays attached to its preserved row, and the summary names what was added, dropped and silently reverted. |
| `AnnotationTest` | 3 | `#` comments are tied to the row below them and follow it when rows are reordered; an un-annotated write is unchanged. |
| `SlashVariantTest` | 3 | Both slash forms may share a target; disagreeing on one raises; `/` has no sibling. |
| `RepoStateTest` | 4 | The committed artifacts as they will deploy: `_redirects` matches `redirects.csv`, every sitemap URL has a row, every content page is some row's target, and the `NOT probe-confirmed` disclaimer is still in the generated file — skipped, not failed, once no `alias-generated` row is left to disclaim. |

`site/scripts/verify_redirects.test.mjs` — 46 tests under `node:test`:

- `parseInventory`: checks sources *and* targets, dedupes a target that is also
  a source, keeps the first source seen, rejects a bad header or a short row
- `parseRules`: explicit status, Cloudflare's 302 default for a status-less
  rule, comments and blanks, a rejected wildcard rule, a rejected rule with no
  destination
- `resolvePath`: no match, one hop, a chain, and a loop
- `describeFailure`: 200 passes; 301 and 308 chains pass; 302 fails by default
  and passes under `--allow-temporary`; a non-200 final response and an
  unexpected 3xx are both reported
- `parseArgs`: an oracle is required, both are accepted, `--min-paths` is read,
  and unknown flags, valueless flags, `--concurrency 0`, `--concurrency abc`
  and `--min-paths abc` are all rejected
- `verify`, against a fake server and a scratch `dist`: offline pass, offline
  failure on an unbuilt target, **a directory refused as a served file**, **a
  missing rule caught even where the destination file exists**, **a rule that
  lands on the wrong page**, a server held to the named destination, an empty
  inventory refused, an explicit `--min-paths` floor, a non-numeric floor
  refused, **a run that checked nothing refused** (concurrency 0 and NaN,
  reached by bypassing `parseArgs`), server-side redirects, a server that 404s
  instead of redirecting, local rules applied first so only the destination is
  ever requested, a redirect with no `Location`, and a server-side loop

## Verification

Run against the real artifacts, not fixtures:

- **The config change moves nothing.** `dist` checksummed across all 207 files
  before and after adding `trailingSlash` and `build.format`: identical. 47
  pages both times.
- **`--refresh-csv` is idempotent on real data.** Seeded from a header-only
  CSV it produced 84 rows (46 `sitemap`, 34 `alias-generated`, 4
  `structural`); a second run reproduced the file byte-for-byte.
- `npm run redirects` writes 83 rules; `npm run redirects:check` then reports
  the file up to date.
- **Offline verification is green.** `verify_redirects.mjs --dist dist`
  checked **129 paths** — the 84 `old_path`s plus the 46 distinct `new_path`s,
  less `/` counted once — with 83 resolved through the local rules, and found
  every destination in the built output.
- **HTTP verification against `astro preview` is green**, same 129 paths, same
  83 locally resolved.
- **The verifier fails when it should.** The same run without `--dist`, so
  `astro preview` has to redirect for itself, reports exactly 83 failures —
  every path that has a rule, since `astro preview` implements none of them.
  That is the shape of a deployment whose `_redirects` was never applied,
  which is what phase 6 needs this to catch.
- `npm test` — 272 tests green: 226 Python (135 inherited plus 91 new) and 46
  under `node:test`.
- `ruff check scripts/` clean.
- **The offline gate catches a dropped rule.** With the `/docs` and
  `/developers` rules removed from a copy of `dist/_redirects`, the run reports
  exactly those two failures and exits 1. Before the file-not-directory fix
  both passed, because `dist/docs/` and `dist/developers/` exist as
  directories — a green CI over a production 404.
- **`--dist` now proves all 83 rules, not 38.** Dropping the single
  `/docs/quickstart` rule — one of the 45 whose destination file exists either
  way, and which the previous version passed — fails the run with
  `nothing redirects it; redirects.csv says it should reach /docs/quickstart/`.
  Stripping every rule fails all 83 sources and no targets.
- **The vacuous-pass class is closed twice over.** `--concurrency 0`,
  `--concurrency abc` and `--min-paths abc` are each rejected by `parseArgs`
  with exit 2; calling `verify()` directly with `concurrency: 0` or `NaN`,
  bypassing that validation entirely, is refused by the completion count with
  `only 0 of 129 paths were checked`.
- **Reconciliation exercised on the real file**: a hand-edited `sitemap` target
  is reported as `changed /docs/agents: was -> /docs/skills/ … now ->
  /docs/agents/`, and a `#` comment written above a `gsc` row is still directly
  above that row after a refresh. `redirects.csv` and `public/_redirects`
  restored to identical checksums afterwards.

## Residual risk in the alias pattern

Recorded because it is the phase's central judgement call and it stays open
until phase 1's probe runs.

The pattern is applied exactly as `phase_1.md` specifies — keep the first
segment, drop everything between it and the leaf. All 17 candidates in the
sitemap are three-segment, so the "drop *every* middle segment" generalisation
is implemented and unit-tested but has never met real data. Nothing in the
generated set looks implausible, every two-segment sitemap path is already
flat, and no generated alias collides with a real page or is claimed by two
nested pages.

The open question the pattern cannot answer is whether GitBook also aliases at
the site root — `/fine-tuning-guide` rather than `/docs/fine-tuning-guide`.
Only the probe can settle that. If it does, the fix is one more generated form
in `_alias_rows` and a refresh.

## Carried forward

New findings, on top of the phase 2 and phase 3 lists that later phases already
inherit.

- **`/sitemap.xml`, `/robots.txt` and `/llms.txt` all 404 on the new site.**
  GitBook served all three — phase 1's brief captures each of them as a
  separate artifact. The build emits `sitemap-index.xml` and `sitemap-0.xml`
  and nothing else at the root. `llms.txt` is already phase 5's job, and
  `robots.txt` naturally belongs beside it. `/sitemap.xml` is the one with no
  owner yet: either add a `public/robots.txt` and a `sitemap.xml` endpoint, or
  redirect it. Deliberately not decided here — phase 5 is choosing how these
  files get produced, and the right answer depends on that. Phase 8 has the
  deadline, since it submits the new sitemap to Search Console.
- **`validate_targets` only knows about pages.** It resolves each `new_path`
  against `src/content/docs/`, so a rule pointing at a static file — the
  `/sitemap.xml` case above, for instance — would be rejected as a missing
  target. Widening it to look in `public/` as well is a few lines, and should
  happen at the moment the first such rule is actually wanted rather than
  speculatively.
- **The 34 `alias-generated` rows are inferences, not observations.** They are
  the phase's one soft spot and they are labelled everywhere they appear: in
  the CSV's `source` column, in a `NOT probe-confirmed` comment in
  `public/_redirects`, and in `site/README.md`. `ref/alias_exclusions.txt`
  carries the settle-up instructions for when phase 1's probe runs. A test
  (`test_generated_aliases_are_marked_unverified`) fails if the disclaimer ever
  drops out of the generated file.
- **Two Cloudflare behaviours are assumed and need confirming on the phase 6
  preview URL.** Neither can be checked from here.
  1. *Static assets versus redirect rules.* Every rule we emit has no asset at
     its exact path, so the rule should apply either way — but a Pages
     deployment that prefers the asset would serve `/docs/quickstart` as a
     200 rather than a 301, leaving the served URL and the canonical tag
     disagreeing. The verifier passes either way by design; this needs an eye,
     not a test.
  2. *The static-rule cap.* `MAX_RULES` is set to the 2,000 the architecture
     records with a note to confirm it. We are at 83, so the margin is large,
     but the constant should be checked against current Cloudflare docs when
     the account is set up.
- **`/a` and `/a/` are still two keys.** `check_slash_variants` now refuses a
  pair that disagrees on a target, which closes the trap for hand-added rows.
  It does not merge them: emitting both forms is deliberate, since Cloudflare
  matches the path exactly.
- **`npm test` now runs two suites.** `test:py` and `test:js`, wrapped by
  `test`. Phase 6's CI workflow should call `npm test`, not the Python
  discovery line directly, or it will silently skip the verifier's tests.
- **The `redirects:check` gate belongs in CI.** `public/_redirects` is
  committed, so nothing regenerates it at deploy time and a hand-edited
  `redirects.csv` would ship stale rules. Both gates are offline and fast, and
  phase 6 should add them alongside the link validator, spelled with the floor:

  ```sh
  npm run redirects:check
  node scripts/verify_redirects.mjs --dist dist --min-paths 176
  ```

  `--min-paths` is what stops a truncated `redirects.csv` passing as "all paths
  resolve". It was 129 when this phase landed — 84 `old_path`s plus 46 distinct
  `new_path`s, less `/` counted once. **Phase 5 raised it to 176** by adding
  `/sitemap.xml`, `/sitemap-index.xml` and 45 `.md` endpoint rows; the line
  above is updated so a phase 6 agent copying it gets the current floor. Raise
  it again when the inventory grows; it is a floor, not an equality.
