#!/usr/bin/env python3
"""Convert the GitBook docs in this repo into Astro Starlight content.

Everything this writes is generated and gitignored. Re-run it any time the
GitBook markdown changes:

    cd site && npm run convert

Outputs:
    site/src/content/docs/**   pages (converted markdown + the landing page)
    site/src/assets/hero.png   landing page hero
    site/public/assets/**      images and video copied from .gitbook/assets
    site/sidebar.json          sidebar built from SUMMARY.md

Flags:
    --list          print the source pages that would be converted, write nothing
    --out DIR       write the converted pages to DIR instead, and skip every
                    other output. Nothing is deleted, so this is the safe way to
                    convert late content once site/src/content/docs is
                    hand-maintained: convert into a scratch directory and copy
                    in only the pages that are actually new.
"""

import html
import json
import os
import re
import shutil
import sys
import urllib.parse

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(SITE)

DOCS_OUT = os.path.join(SITE, "src/content/docs")
ASSETS_OUT = os.path.join(SITE, "public/assets")
SRC_ASSETS = os.path.join(SITE, "src/assets")
GITBOOK_ASSETS = os.path.join(REPO, ".gitbook/assets")

# GitBook hint styles -> Starlight aside types
HINTS = {"info": "note", "success": "tip", "warning": "caution", "danger": "danger"}

# Directory names never scanned for source markdown, at any depth. Dot
# directories are skipped separately.
SKIP_DIRS = {"site", "specs", "node_modules", "dist", "__pycache__", "venv", "env"}

# Image used for the landing page hero
HERO_SOURCE = "App3.png"

# Link targets that are already final and must be left exactly as written.
EXTERNAL_TARGET = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|//|/)", re.I)

FENCE = re.compile(r"^[ \t]*(?:```+|~~~+).*$", re.M)


def url_for(relpath):
    """Repo-relative markdown path -> Starlight URL."""
    p = relpath.replace("\\", "/")
    if p == "README.md":
        return "/"
    p = re.sub(r"/README\.md$", "/", p)
    p = re.sub(r"\.md$", "/", p)
    if not p.startswith("/"):
        p = "/" + p
    if not p.endswith("/"):
        p += "/"
    return p


def out_for(relpath):
    """Repo-relative markdown path -> output path under src/content/docs."""
    return re.sub(r"/README\.md$", "/index.md", relpath)


# --- headings and anchors ---------------------------------------------------


def heading_text(raw):
    """Heading source -> the plain text a markdown renderer would produce.

    Whitespace is deliberately *not* trimmed: github-slugger does not trim
    either, so a heading ending in an inline anchor tag or a `&#x20;` entity
    really does get a trailing hyphen in its id.
    """
    text = html.unescape(raw)
    text = re.sub(r"<[^>]*>", "", text)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\*\*(.*?)\*\*|__(.*?)__", lambda m: m.group(1) or m.group(2) or "", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    # Only underscores acting as delimiters -- kiln_ai is one word, not emphasis.
    text = re.sub(r"(?<![\w\\])_(.+?)_(?!\w)", r"\1", text)
    return re.sub(r"\\(.)", r"\1", text)


def starlight_slug(text):
    """Heading text -> the id Starlight emits (a github-slugger port).

    github-slugger lowercases, deletes punctuation without collapsing the gap it
    leaves, then turns each remaining space into a hyphen -- which is why
    "State & Memory" becomes "state--memory" and not "state-memory".
    """
    return re.sub(r"[^\w\s-]", "", text.lower(), flags=re.U).replace(" ", "-")


def legacy_slugs(text):
    """Heading text -> the slugs GitBook would have published for it.

    GitBook spells "&" as "and" and collapses runs of whitespace; github-slugger
    does neither. Anchor URLs minted under GitBook are indexed, and 119 in-repo
    links use them, so these are what a broken anchor gets looked up against.
    """
    collapsed = re.sub(r"\s+", " ", text).strip()
    ampersand = re.sub(r"\s+", " ", text.replace("&", " and ")).strip()
    return {starlight_slug(collapsed), starlight_slug(ampersand)}


def page_anchors(body):
    """Page body -> (slugs Starlight will emit, {legacy slug: current slug})."""
    slugs, aliases, seen = set(), {}, {}

    for raw in headings(body):
        text = heading_text(raw)
        slug = starlight_slug(text)
        # github-slugger disambiguates a repeated slug with a numeric suffix.
        if slug in seen:
            seen[slug] += 1
            slug = "%s-%d" % (slug, seen[slug])
        else:
            seen[slug] = 0
        slugs.add(slug)
        for legacy in legacy_slugs(text):
            aliases.setdefault(legacy, slug)

    # GitBook pins some headings to a hand-written id with an inline anchor tag.
    slugs.update(re.findall(r'\bid="([^"]+)"', body))

    return slugs, {legacy: slug for legacy, slug in aliases.items() if legacy not in slugs}


def headings(body):
    """Every ATX heading in a body, skipping fenced code blocks."""
    found, in_fence = [], False
    for line in body.split("\n"):
        if re.match(r"^[ \t]*(?:```|~~~)", line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = re.match(r"^#{1,6}\s+(.*?)\s*$", line)
        if m:
            found.append(m.group(1))
    return found


# --- assets -----------------------------------------------------------------


def normalize_asset_name(name):
    """Fold the unicode spaces macOS screenshots carry down to a plain space."""
    return re.sub(r"\s+", " ", name).strip()


def build_asset_index(directory=GITBOOK_ASSETS):
    """Real filename, keyed by its normalized form.

    Screenshot filenames from macOS contain U+202F (narrow no-break space) where
    the markdown that references them was written with a plain space. GitBook's
    CDN papered over the difference; a static host will not.
    """
    index = {}
    for name in sorted(os.listdir(directory)):
        index.setdefault(normalize_asset_name(name), name)
    return index


def asset_url(name):
    return "/assets/" + urllib.parse.quote(name)


# --- frontmatter ------------------------------------------------------------


FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n", re.S)


def read(path):
    with open(path) as f:
        return f.read()


def strip_frontmatter(text):
    m = FRONTMATTER.match(text)
    return text[m.end():] if m else text


def parse_frontmatter(text):
    """(fields, body). Handles the YAML subset GitBook actually writes.

    Descriptions that ran long got wrapped into a folded block scalar
    (`description: >-`), and ones containing quotes got single-quoted. A
    line-splitting parser reads the first as the literal string ">-" and drops a
    leading quote from the second, so both need real scalar handling. There is
    no yaml module in the standard library and this is the whole grammar in use.
    """
    m = FRONTMATTER.match(text)
    if not m:
        return {}, text

    fields, lines, i = {}, m.group(1).split("\n"), 0
    while i < len(lines):
        entry = re.match(r"^(\w[\w.-]*):[ \t]*(.*)$", lines[i])
        i += 1
        if not entry:
            continue
        key, value = entry.group(1), entry.group(2).strip()

        block = re.match(r"^([|>])([+-]?)$", value)
        if block:
            folded, body = block.group(1) == ">", []
            while i < len(lines) and (not lines[i].strip() or lines[i][:1] in " \t"):
                body.append(lines[i].strip())
                i += 1
            fields[key] = (" " if folded else "\n").join(body).strip()
            continue

        fields[key] = unquote_scalar(value)

    return fields, text[m.end():]


def unquote_scalar(value):
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return value[1:-1].replace("''", "'")
    if len(value) >= 2 and value[0] == value[-1] == '"':
        return re.sub(r"\\(.)", r"\1", value[1:-1])
    return value


# --- link rewriting ---------------------------------------------------------


class Conversion:
    """Everything a page conversion needs to resolve references site-wide."""

    def __init__(self, sources=(), assets=None):
        self.assets = build_asset_index() if assets is None else assets
        self.anchors = {}
        for rel in sources:
            body = strip_frontmatter(read(os.path.join(REPO, rel)))
            self.anchors[url_for(rel)] = page_anchors(body)
        self.missing_assets = []
        self.unresolved_anchors = []

    def resolve_asset(self, relpath, name):
        if name in self.assets.values():
            return name
        real = self.assets.get(normalize_asset_name(name))
        if real is None:
            self.missing_assets.append((relpath, name))
            return name
        return real

    def resolve_anchor(self, relpath, url, anchor):
        """Map a GitBook anchor onto the current Starlight one where they differ.

        Only anchors that do not already match a real id are touched, so a
        working anchor can never be rewritten into a broken one.
        """
        if not anchor:
            return anchor
        known = self.anchors.get(url)
        if known is None:
            return anchor
        slugs, aliases = known
        if anchor in slugs:
            return anchor
        if anchor in aliases:
            return aliases[anchor]
        self.unresolved_anchors.append((relpath, url + "#" + anchor))
        return anchor


def rewrite_target(target, relpath, ctx, page_url):
    """Link destination -> rewritten URL, or None to leave it as written."""
    if ".gitbook/assets/" in target:
        name = urllib.parse.unquote(target.split(".gitbook/assets/")[-1])
        return asset_url(ctx.resolve_asset(relpath, name))

    if target.startswith("#"):
        return "#" + ctx.resolve_anchor(relpath, page_url, target[1:])

    if not target or EXTERNAL_TARGET.match(target):
        return None

    path, _, anchor = target.partition("#")
    if not path:
        return None

    resolved = os.path.normpath(os.path.join(os.path.dirname(relpath), path))
    if resolved.endswith(".md"):
        url = url_for(resolved)
    elif os.path.isdir(os.path.join(REPO, resolved)):
        url = "/" + resolved.strip("/") + "/"
    else:
        return None

    anchor = ctx.resolve_anchor(relpath, url, anchor)
    return url + ("#" + anchor if anchor else "")


# A markdown link destination: either <angle bracketed>, which is how GitBook
# writes filenames containing spaces, or a bare target that may contain one
# level of balanced parentheses ("Screenshot ... (1).png").
MD_LINK = re.compile(r"\]\((<[^<>\n]*>|[^()\s]*(?:\([^()\s]*\)[^()\s]*)*)\)")

HTML_ATTR = re.compile(r'\b(src|href)="([^"]*)"')


def rewrite_references(text, relpath, ctx, page_url):
    """Point every asset, page and anchor reference at its Starlight home."""

    def markdown(m):
        raw = m.group(1)
        target = raw[1:-1] if raw.startswith("<") else raw
        rewritten = rewrite_target(target, relpath, ctx, page_url)
        return m.group(0) if rewritten is None else "](" + rewritten + ")"

    def attribute(m):
        rewritten = rewrite_target(m.group(2), relpath, ctx, page_url)
        return m.group(0) if rewritten is None else '%s="%s"' % (m.group(1), rewritten)

    return HTML_ATTR.sub(attribute, MD_LINK.sub(markdown, text))


def outside_code(text, transform):
    """Apply `transform` to the prose, leaving fenced code blocks untouched.

    Without this, a markdown link inside a code sample gets rewritten as though
    it were a real link -- which silently edits documented example content.
    """
    parts, last, in_fence = [], 0, False
    for m in FENCE.finditer(text):
        if not in_fence:
            parts.append(transform(text[last:m.start()]))
        else:
            parts.append(text[last:m.start()])
        parts.append(m.group(0))
        last, in_fence = m.end(), not in_fence
    parts.append(text[last:] if in_fence else transform(text[last:]))
    return "".join(parts)


# --- embeds -----------------------------------------------------------------


def embed_html(url):
    """GitBook {% embed %} -> a real embed."""
    url = url.strip()
    frame = (
        '<div style="position:relative;padding-bottom:56.25%;height:0;margin:1.5rem 0;">'
        '<iframe src="{src}" style="position:absolute;top:0;left:0;width:100%;height:100%;'
        'border:0;border-radius:8px" allow="{allow}" allowfullscreen title="Video"></iframe></div>'
    )

    m = re.search(r"vimeo\.com/(\d+)(?:/([0-9a-f]+))?", url)
    if m:
        q = "?h=" + m.group(2) if m.group(2) else ""
        return frame.format(
            src="https://player.vimeo.com/video/%s%s" % (m.group(1), q),
            allow="autoplay; fullscreen; picture-in-picture",
        )

    m = re.search(r"(?:youtube\.com/watch\?v=|youtu\.be/)([\w-]+)", url)
    if m:
        return frame.format(
            src="https://www.youtube.com/embed/%s" % m.group(1),
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; picture-in-picture",
        )

    # Videos still served from GitBook's CDN. We have local copies of these in
    # .gitbook/assets, so point at those instead -- the CDN URLs die when the
    # GitBook space goes away.
    m = re.search(r"files\.gitbook\.com/.*?%2F([^%?]+\.mp4)", url)
    if m:
        name = urllib.parse.unquote(m.group(1))
        return (
            '<video controls playsinline style="width:100%;border-radius:8px;'
            'margin:1.5rem 0" src="' + asset_url(name) + '"></video>'
        )

    return '<p><a href="%s">%s</a></p>' % (url, url)


# A captioned embed. The caption body may not contain a blank line, which is
# what separates it from an uncaptioned embed followed by ordinary prose.
CAPTIONED_EMBED = re.compile(
    r'\{%\s*embed url="([^"]+)"\s*%\}[ \t]*\n((?:[^\n]+\n)*?)\{%\s*endembed\s*%\}[ \t]*\n?'
)


def convert_embeds(body):
    """GitBook embeds -> a figure, so the caption stays a caption."""

    def captioned(m):
        caption = html.escape(m.group(2).strip(), quote=False)
        return "<figure>%s<figcaption><p>%s</p></figcaption></figure>\n" % (
            embed_html(m.group(1)),
            caption,
        )

    body = CAPTIONED_EMBED.sub(captioned, body)
    body = re.sub(r'\{%\s*embed url="([^"]+)"\s*%\}', lambda m: embed_html(m.group(1)), body)
    return re.sub(r"\{%\s*endembed\s*%\}\n?", "", body)


# --- page conversion --------------------------------------------------------


def convert(text, relpath, ctx=None):
    ctx = Conversion() if ctx is None else ctx
    page_url = url_for(relpath)

    frontmatter, body = parse_frontmatter(text)

    # Starlight renders the title itself, so lift the H1 out of the body.
    title = None
    m = re.search(r"^#\s+(.+?)\s*$", body, re.M)
    if m:
        title = heading_text(m.group(1)).strip()
        body = body[: m.start()] + body[m.end():]
    if not title:
        title = os.path.basename(relpath)[:-3].replace("-", " ").title()

    def prose(chunk):
        chunk = re.sub(
            r'\{%\s*hint style="(\w+)"\s*%\}',
            lambda m: ":::" + HINTS.get(m.group(1), "note"),
            chunk,
        )
        chunk = re.sub(r"\{%\s*endhint\s*%\}", ":::", chunk)
        # {% code %} only carried display options; Expressive Code handles those.
        chunk = re.sub(r"\{%\s*code[^%]*%\}\n?", "", chunk)
        chunk = re.sub(r"\{%\s*endcode\s*%\}\n?", "", chunk)
        chunk = convert_embeds(chunk)
        chunk = re.sub(r"\{%[^%]*%\}", "", chunk)
        chunk = rewrite_references(chunk, relpath, ctx, page_url)
        return chunk.replace(":desktop:", "\U0001f5a5️")

    body = outside_code(body, prose)

    body = re.sub(r"\n:::(note|tip|caution|danger)\n\n", r"\n:::\1\n", body)
    body = re.sub(r"\n\n:::\n", "\n:::\n", body)

    out = ["---", "title: " + json.dumps(title)]
    description = frontmatter.get("description")
    if description:
        out.append("description: " + json.dumps(description))
    out.append("---")
    return "\n".join(out) + "\n" + body.lstrip("\n")


def build_sidebar():
    """Build the Starlight sidebar from SUMMARY.md."""
    lines = read(os.path.join(REPO, "SUMMARY.md")).split("\n")
    groups, current = [], None

    for line in lines:
        heading = re.match(r"^##\s+(.+)$", line)
        if heading:
            current = {"label": heading.group(1).strip(), "items": []}
            groups.append(current)
            continue

        item = re.match(r"^(\s*)\*\s+\[(.+?)\]\((.+?)\)\s*$", line)
        if not item or current is None:
            continue

        indent, label, target = len(item.group(1)), item.group(2), item.group(3)
        label = heading_text(label).strip()
        if target == "README.md":
            continue

        entry = {"label": label, "link": url_for(target)}
        if indent >= 2 and current["items"]:
            current["items"][-1].setdefault("items", []).append(entry)
        else:
            current["items"].append(entry)

    # A SUMMARY.md parent has both a page and children. Starlight groups don't,
    # so the parent page becomes an "Overview" entry inside its own group.
    for group in groups:
        items = []
        for item in group["items"]:
            if "items" in item:
                children = [{"label": "Overview", "link": item["link"]}] + item["items"]
                items.append({"label": item["label"], "items": children, "collapsed": True})
            else:
                items.append(item)
        group["items"] = items

    return groups


def find_sources():
    """Every GitBook markdown file that becomes a page."""
    sources = []
    for root, dirs, files in os.walk(REPO):
        # Prune in place so os.walk does not descend into these at all. Matching
        # on directory names rather than path substrings means a stray
        # node_modules anywhere (including the repo root) stays out.
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for name in files:
            if not name.endswith(".md"):
                continue
            rel = os.path.relpath(os.path.join(root, name), REPO)
            # SUMMARY.md becomes the sidebar; README.md becomes the landing page.
            if rel in ("SUMMARY.md", "README.md"):
                continue
            sources.append(rel)
    return sorted(sources)


# --- entry point ------------------------------------------------------------


def parse_args(argv):
    """(mode, out_dir). mode is "list" or "convert"; out_dir is None by default.

    An explicit --out means "pages only, delete nothing": the caller wants a
    scratch copy to cherry-pick from, not a rebuild of the site.
    """
    if "--list" in argv:
        return "list", None
    if "--out" in argv:
        i = argv.index("--out")
        if i + 1 >= len(argv):
            raise SystemExit("--out needs a directory")
        return "convert", os.path.abspath(argv[i + 1])
    return "convert", None


def report(ctx):
    """Print unresolved references. Missing assets are fatal, anchors are not."""
    for relpath, anchor in ctx.unresolved_anchors:
        print("warning: %s links to %s, which no heading provides" % (relpath, anchor),
              file=sys.stderr)
    if ctx.unresolved_anchors:
        print("%d unresolved anchor(s). These are stale in the GitBook source too."
              % len(ctx.unresolved_anchors), file=sys.stderr)

    if ctx.missing_assets:
        for relpath, name in ctx.missing_assets:
            print("error: %s references missing asset %r" % (relpath, name), file=sys.stderr)
        raise SystemExit("%d referenced asset(s) do not exist in .gitbook/assets"
                         % len(ctx.missing_assets))


def main(argv=None):
    mode, out_dir = parse_args(sys.argv[1:] if argv is None else argv)

    sources = find_sources()

    # `--list` prints what would be converted, without writing anything. Use it
    # when the page count looks wrong to see exactly which files are picked up.
    if mode == "list":
        try:
            print("Repo root: %s" % REPO)
            print("%d source pages:" % len(sources))
            for rel in sources:
                print("  " + rel)
            sys.stdout.flush()
        except BrokenPipeError:
            # Piping into `head` and friends closes stdout early.
            os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        return

    # Convert everything before writing anything, so a missing asset stops the
    # run instead of leaving a half-written tree behind.
    ctx = Conversion(sources)
    pages = {rel: convert(read(os.path.join(REPO, rel)), rel, ctx) for rel in sources}
    report(ctx)

    scratch = out_dir is not None
    docs_out = out_dir or DOCS_OUT
    if not scratch and os.path.isdir(docs_out):
        shutil.rmtree(docs_out)
    os.makedirs(docs_out, exist_ok=True)

    for rel, converted in pages.items():
        out_path = os.path.join(docs_out, out_for(rel))
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w") as f:
            f.write(converted)

    if scratch:
        print("Converted %d pages into %s. Nothing else was written or deleted."
              % (len(pages), docs_out))
        return

    # Hand-written landing page (the GitBook card table doesn't convert).
    shutil.copy(os.path.join(SITE, "src/landing/index.mdx"), os.path.join(docs_out, "index.mdx"))

    os.makedirs(SRC_ASSETS, exist_ok=True)
    shutil.copy(os.path.join(GITBOOK_ASSETS, HERO_SOURCE), os.path.join(SRC_ASSETS, "hero.png"))

    if os.path.isdir(ASSETS_OUT):
        shutil.rmtree(ASSETS_OUT)
    shutil.copytree(GITBOOK_ASSETS, ASSETS_OUT)

    sidebar = build_sidebar()
    with open(os.path.join(SITE, "sidebar.json"), "w") as f:
        json.dump(sidebar, f, indent=2)

    entries = sum(len(g["items"]) for g in sidebar)
    print("Converted %d pages, %d sidebar entries across %d groups."
          % (len(pages), entries, len(sidebar)))


if __name__ == "__main__":
    main()
