# Phase 1: Capture the GitBook Baseline

**Run this in a session with a real browser and public internet access.** It
cannot run in a network-restricted environment. It must run **while
`docs.kiln.tech` is still served by GitBook** — every output here becomes
impossible to obtain once GitBook is decommissioned.

This brief is self-contained. You do not need context from the session that
wrote it.

## Why this exists

We are migrating these docs from GitBook to an Astro Starlight site (see
`../project_overview.md`). Two later phases depend entirely on data that only
exists while the old site is live:

1. **Redirects.** We must preserve every publicly reachable URL. The repo
   cannot tell us what those are — GitBook's routing invents URLs that have no
   representation in `SUMMARY.md`. The only way to learn them is to ask the
   live site.
2. **Per-page QA.** The bar is "every page renders at least as well as the
   GitBook version." That is unverifiable without a record of what the GitBook
   version looked like.

## Outputs

Everything goes in `baseline/` at the repo root.

```
baseline/
  urls.txt            one URL per line, the full inventory
  manifest.json       per-URL metadata (see schema below)
  sitemap.xml         raw copy as fetched
  llms.txt            raw copy as fetched
  robots.txt          raw copy as fetched
  pages/<slug>.txt    rendered main-content text, one file per page
  shots/<slug>.png    full-page screenshot, one file per page
```

`<slug>` is the URL path with `/` replaced by `_`, e.g.
`docs_fine-tuning_fine-tuning-guide`. Use `index` for `/`.

### `manifest.json` schema

One entry per URL requested, including ones that redirect or 404:

```json
{
  "captured_at": "2026-08-22T00:00:00Z",
  "origin": "https://docs.kiln.tech",
  "entries": [
    {
      "url": "/docs/fine-tuning-guide",
      "status": 200,
      "final_url": "/docs/fine-tuning-guide",
      "redirect_chain": [],
      "title": "Fine Tuning Guide | Kiln AI Docs",
      "description": "Fine tuning 9 Models in 18 minutes",
      "anchors": ["overview", "step-1-define-your-task", "cost-breakdown"],
      "slug": "docs_fine-tuning-guide",
      "source": "alias-probe",
      "text_file": "pages/docs_fine-tuning-guide.txt",
      "shot_file": "shots/docs_fine-tuning-guide.png"
    }
  ]
}
```

`redirect_chain` and `final_url` matter as much as `status` — they tell us
which URLs *already* redirect on GitBook, which we need in order to flatten
redirect chains rather than daisy-chaining them on the new site.

`anchors` feeds a later check for heading-slug drift between GitBook and
Starlight (priority 2, not a launch blocker).

## Step 1: Assemble the URL inventory

Use four independent sources. Redundancy is the point — each finds URLs the
others miss. Tag every URL with which source produced it.

1. **`https://docs.kiln.tech/sitemap.xml`** — may be a sitemap index pointing
   at child sitemaps; follow them if so.
2. **`https://docs.kiln.tech/llms.txt`** — GitBook publishes this as a complete
   documentation index. It is likely the cleanest full page list, and we are
   recreating it later, so capture the file itself too.
3. **A crawl.** Breadth-first from `/`, following same-origin links only, no
   depth limit. Stay on `docs.kiln.tech`; do not follow out to `kiln.tech`,
   GitHub, or Vimeo.
4. **Google Search Console → Pages → indexed pages, exported.** *This is a
   human step — ask the user to export it.* It is the only source for
   historical URLs that have dropped out of the sitemap but still have inbound
   links. Merge the export into `urls.txt` with `source: "gsc"`.

### Step 1b: Probe for flat aliases (do not skip)

GitBook serves some nested pages at a flattened path as well, and **both are
indexed by Google**. Confirmed example:

| URL | Serves |
| --- | --- |
| `https://docs.kiln.tech/docs/fine-tuning/fine-tuning-guide` | the page |
| `https://docs.kiln.tech/docs/fine-tuning-guide` | the same page |

These aliases do not appear in `SUMMARY.md` and may not appear in the sitemap.
For every nested URL discovered (paths with 3+ segments), probe the flattened
variant — drop the intermediate segment(s) — and record the result in
`manifest.json` with `source: "alias-probe"`. Any that return 200 are real
URLs we must redirect.

If you find aliases following a different pattern than the one above,
generalise the probe and note the pattern in your summary.

## Step 2: Capture each page

For every URL that returns 200:

- **Text.** Extract the **main content only** — exclude the sidebar, header,
  footer, and "Last updated" chrome. Diffs should reflect content changes, not
  navigation. Inspect the DOM to find GitBook's main content container and use
  a stable selector. Normalise whitespace so later diffs are not noise.
- **Screenshot.** Full page, viewport width **1440**, `deviceScaleFactor: 2`.
  Wait for network idle and for images to load — GitBook lazy-loads images, so
  scroll to the bottom first or disable lazy loading, otherwise screenshots
  will be full of blank boxes.
- **Metadata.** Title, meta description, and the `id` of every `h2`/`h3`.

Keep concurrency low (2–3) with a small delay between requests. This is our
own site, but there is no reason to hammer it. ~45 pages plus alias probes is
on the order of 150 requests.

Do not log in. Capture only what an anonymous visitor sees — that is what
search engines indexed.

## Step 3: Sanity-check before finishing

- The page count should be **at least 45**. The repo has 45 source pages as of
  the content freeze (commit `1dde281`). Materially fewer means the crawl
  missed something; materially more is expected and interesting — those are
  the aliases.
- Every entry in `manifest.json` with `status: 200` has both a `text_file` and
  a `shot_file` that exist and are non-empty.
- Spot-check three screenshots by eye for blank image placeholders.

## Step 4: Commit

Add to the repo's `.gitignore`:

```
baseline/shots/
```

Commit `urls.txt`, `manifest.json`, `sitemap.xml`, `llms.txt`, `robots.txt`,
and `pages/`. These are small, and they are the permanent record of what the
old site contained.

**Do not commit the screenshots.** 45+ full-page PNGs at 2x is tens of
megabytes, permanently in git history — and we are separately pruning ~73
unreferenced assets from this repo to keep it lean. Keep `shots/` locally for
the phase 7 QA diff. If they need to be shared between machines, zip them and
attach to PR #16 rather than committing.

If the user would rather have them in git despite the size, that is their
call — just make it deliberate.

## Report back

Summarise:

- Total URLs found, broken down by source
- How many flat aliases were discovered, and the pattern
- Any URL that 404s or redirects unexpectedly
- Pages where text extraction or screenshots looked wrong
- Whether the Search Console export was obtained (and if not, that it is still
  outstanding — it is the only source for historical URLs)

Then the next phase is `/spec continue` in the main working session.
