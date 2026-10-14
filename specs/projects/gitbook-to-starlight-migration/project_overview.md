---
status: complete
---

# GitBook → Astro Starlight Migration

## What we're building

Move the Kiln docs site off GitBook and onto the Astro Starlight prototype
already built in `site/`, and take it to production on Cloudflare Pages.

GitBook works but costs a lot, and we want to own the stack: markdown in git,
a static build, self-hosted. A proof of concept already exists on this branch
(PR #16) and is accepted — it is pretty, fast, and functional. This project
takes it from prototype to production.

## Why

- **Cost.** GitBook is expensive for what we get.
- **Control.** Modern OSS stack, styles we can change, no vendor lock-in.
- **Speed.** The static build is 47 pages in ~12 seconds including search
  indexing, with no external search service.

## Current state

The prototype at `site/` runs Astro 7 + Starlight 0.41 with the
`starlight-theme-black` theme. A Python transformer,
`site/scripts/gitbook_to_starlight.py`, reads the GitBook markdown at the repo
root and generates the Starlight site. Everything it writes is gitignored and
regenerated on every build, so GitBook markdown is still the source of truth.

Content was frozen by merging `main` into this branch at commit `1dde281`,
which brought in four pages added upstream during the prototype work
(`code-tools`, `code-judges`, `judge-types`, `llm-judges`). 45 source pages,
47 built.

## What "done" looks like

- `docs.kiln.tech` serves the Starlight site from Cloudflare Pages
- Every URL that works today still works, or 301s to its new home
- The repo is Astro-native: no transformer in the build path, no generated
  content gitignored
- GitBook is decommissioned and the subscription cancelled

## Constraints and decisions already made

- **Preserve all existing public URLs**, including ones that moved in the past.
  SEO and inbound links must keep working. Use **301** (permanent), not 302.
- **Theme is settled**: `starlight-theme-black`, with collapsible sidebar
  dropdowns. No further theme evaluation.
- **No CMS / WYSIWYG editor.** Originally on the wishlist, explicitly cut. We
  prefer editing markdown in git.
- **`llms.txt` must be preserved** — GitBook publishes one today and we want to
  keep it, plus add a visible link to it from the site. GitBook also serves a
  markdown version of every page.
- **One static OG image** for all docs pages is sufficient.
- **The transformer stays until the very end.** Even with content frozen, late
  pages could sneak in. Deleting it is the final step, after cutover.
- Work happens on branch `claude/gitbook-alternatives-pjubsj`.

## Known findings from the audit so far

- GitBook serves some pages at **two URLs** — a flat alias and a nested path
  (e.g. `/docs/fine-tuning-guide` and `/docs/fine-tuning/fine-tuning-guide`).
  Both are indexed. Only the nested form is reproduced by the prototype.
- 119 cross-page links contain `#anchors`, and search engines have indexed
  anchor URLs. Anchor slugs must be checked for drift between GitBook and
  Starlight (priority 2 — worth checking, not a launch blocker).
- Of 159 files in `.gitbook/assets`, only 86 are referenced. The two videos
  that exceed Cloudflare Pages' 25 MiB per-file limit are referenced by
  nothing, so they can be deleted rather than rehosted.
- The hand-written landing page drifts from the GitBook card table whenever
  upstream changes it. This already happened once.
