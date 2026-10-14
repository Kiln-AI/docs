---
status: complete
---

# Functional Spec: GitBook → Astro Starlight Migration

## Scope

### In scope

- Converting the GitBook markdown in this repo into hand-maintained Astro
  Starlight content, permanently
- Preserving every publicly reachable URL, including historical ones
- Production deployment on Cloudflare Pages at `docs.kiln.tech`
- Parity for features GitBook gives us today: search, `llms.txt`, per-page
  markdown, social preview images, analytics
- Per-page visual QA against a baseline captured from the live GitBook site
- Decommissioning GitBook

### Out of scope

- A CMS or WYSIWYG editor. Editing is markdown in git, via GitHub's web editor
  or a local editor.
- Restructuring the information architecture. Page set and hierarchy stay as
  they are; this is a platform migration, not a docs rewrite.
- Rewriting page copy. Content changes are limited to what rendering fidelity
  requires.
- Versioned docs, i18n, and dark/light logo variants.

## URL preservation

This is the highest-risk area and the one that is expensive to fix after
launch.

### Requirements

1. **Every URL reachable on the live GitBook site today must continue to
   resolve**, either by serving the same page at the same path or by
   redirecting to its new location.
2. Redirects use **HTTP 301** (permanent). 302 is acceptable only as a
   temporary launch-week setting if we want the option to roll back; if used,
   flipping to 301 is a tracked follow-up.
3. Historical URLs that already redirect on GitBook must keep working. Chained
   redirects (old → intermediate → new) should be flattened to a single hop
   where we can determine the final destination.
4. Redirect coverage is **verified, not assumed**: every URL in the inventory
   is requested against the built site and must return 200 or a 301 that
   itself terminates in a 200.

### Sources of truth for the URL inventory

The repo cannot tell us what URLs exist — GitBook's routing invents aliases
that have no representation in `SUMMARY.md`. The inventory must come from:

- GitBook's `sitemap.xml`
- A crawl of the live site following internal links
- Google Search Console's indexed-pages export, which surfaces historical URLs
  that no longer appear in the sitemap

### Known alias pattern

GitBook serves nested pages at a flat path as well:

| Live today | Prototype produces |
| --- | --- |
| `/docs/fine-tuning/fine-tuning-guide` | `/docs/fine-tuning/fine-tuning-guide/` |
| `/docs/fine-tuning-guide` | *(404)* |

Both forms are indexed. The flat form must be redirected.

### Trailing slashes

Starlight generates directory-style URLs with a trailing slash. GitBook serves
without one. Cloudflare Pages normalises this, but the behaviour must be
confirmed against the real deployment rather than assumed, and whichever form
is canonical must be reflected consistently in `sitemap.xml` and canonical
tags.

### Anchors (priority 2)

119 cross-page links use `#anchors`, and anchor URLs are indexed. Anchors are
resolved client-side, so a redirect only preserves them if the heading slug is
unchanged. GitBook and Starlight (github-slugger) may disagree on headings
containing punctuation — `Step 6 [Optional]: …`, `Evaluate RAG Accuracy: Q&A
Evals`, curly quotes in `Our "Ladder" Data Strategy`.

Required: generate both slug sets and diff them, then either adjust headings or
accept the drift with the list recorded. Not a launch blocker.

## Content fidelity

### Baseline

Before GitBook is torn down, capture a baseline of the live site:

- The full URL inventory
- Rendered text of every page
- A full-page screenshot of every page

**This must run in a session with real Chrome access to the public internet.**
The current session's egress is blocked, so it cannot produce the baseline.

The baseline is what makes "meets or exceeds the old site" checkable rather
than a matter of opinion, and it is what per-page QA diffs against.

### Fidelity bar

Each page must:

- Contain the same information as the GitBook version — no dropped sections,
  images, videos, tables, or callouts
- Render at least as well as the GitBook version; where the prototype already
  renders better, keep the improvement
- Have working internal links and images
- Have a `title` and a `description`

## Late content reconciliation

Content was frozen at `1dde281`, but pages can still land in GitBook after a
freeze in practice. Before the transformer is deleted:

1. Diff `origin/main` against the freeze commit
2. For anything new or changed, run the transformer into a **scratch
   directory** and copy the converted pages in individually
3. A destructive full re-run is forbidden once content is hand-edited — it
   would overwrite the visual QA work

The transformer is deleted only after this reconciliation, as the final step of
the project.

## Feature parity

| Feature | GitBook today | Plan |
| --- | --- | --- |
| Search | Built in | Pagefind, already working, no external service |
| `llms.txt` | Auto-generated | `starlight-llms-txt` plugin, **plus a visible link** in the site so people can find it |
| Per-page markdown | Auto-generated | Theme's "Copy page" menu provides copy-as-markdown; verify whether a stable `.md` URL is also needed for parity |
| Social/OG images | Auto-generated per page | One static OG image for all docs pages |
| Analytics | Built in | Cloudflare Web Analytics |
| Edit this page | — | Already configured; `editLink` base URL must be corrected once content moves |
| 404 page | Custom | Theme ships one; confirm it is useful and links somewhere sensible |

### Search keywords

Considered and dropped. Pagefind indexes body text automatically and Starlight
has no generic keywords frontmatter field, so a keywords step would produce
frontmatter nothing reads. Instead: ensure every page carries a good
`description`, which is already inherited from GitBook frontmatter.

## Repository outcome

After the conversion the repo is Astro-native:

- Converted markdown lives in `site/src/content/docs/` and is **committed**,
  not gitignored
- Assets live under the site, pruned to only what is referenced
- The GitBook source files (`docs/`, `developers/`, `README.md`, `SUMMARY.md`,
  `.gitbook/`) are removed once their content has moved
- `site/README.md` no longer describes a transform pipeline
- The transformer is gone (final step)

## Quality gates

These run in CI on pull requests and must pass before cutover:

1. **Build succeeds**
2. **No broken internal links** — `starlight-links-validator`. This matters
   because the conversion rewrites relative links across 45 pages.
3. **Redirect coverage** — every URL in the inventory resolves

## Edge cases and failure modes

- **An asset is referenced but missing.** Build should surface it; treat as a
  blocker for that page.
- **A redirect target does not exist.** Caught by redirect verification.
- **Cloudflare Pages file-size limit (25 MiB).** The two oversized videos are
  unreferenced and get deleted with the rest of the unreferenced assets. If any
  referenced asset ever exceeds the limit, it must move to Cloudflare Stream,
  R2, or Vimeo — flag to a human, do not silently drop it.
- **The landing page drifts.** It is hand-written because GitBook's card table
  has no automatic equivalent. Once the repo is Astro-native this stops being a
  sync problem, since there is no longer a second source.
- **DNS cutover goes wrong.** Deploy to a Cloudflare preview URL and validate
  fully before pointing `docs.kiln.tech` at it. Keep GitBook running until the
  new site is confirmed good.
- **Post-cutover 404 spike.** Watch Search Console; any spike means the
  redirect map has a gap.

## Success criteria

- `docs.kiln.tech` serves the Starlight site
- Every inventoried URL returns 200, or 301s to a 200
- CI enforces build + link checks
- `llms.txt` published and linked
- Search, OG images, and analytics working
- Search Console shows no sustained 404 increase after cutover
- GitBook subscription cancelled
