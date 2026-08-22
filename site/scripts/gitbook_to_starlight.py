#!/usr/bin/env python3
"""Convert the GitBook docs in this repo into Astro Starlight content.

This produced the content now committed under site/src/content/docs, and it is
no longer part of the build -- `npm run dev` and `npm run build` are plain Astro
commands. It is kept only to reconcile GitBook pages that landed after the
content freeze, which is what --out DIR is for. The default run rebuilds
site/src/content/docs from scratch and refuses to start once that directory is
committed, because it would delete hand-maintained content.

Outputs:
    site/src/content/docs/**   converted pages
    site/src/assets/**         referenced images, renamed so Astro can optimize
                               them, plus hero.png for the landing page
    site/public/assets/**      referenced videos and anything else Astro will
                               not process, copied verbatim
    site/sidebar.json          sidebar built from SUMMARY.md

Unreferenced files in .gitbook/assets are reported and left alone.

Run with --help for the flags. --out DIR is the safe one: it writes the
converted pages to DIR and nothing else, deleting nothing, which is how late
content gets reconciled once site/src/content/docs is hand-maintained.
"""

import argparse
import html
import json
import os
import re
import shutil
import subprocess
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

# An opening or closing code fence. A fence closes only on a run of the same
# character at least as long as the one that opened it, so a ```-fence nested
# inside a ````-block does not end it.
FENCE = re.compile(r"^[ \t]*(?P<fence>`{3,}|~{3,})(?P<info>.*)$")

LINE = re.compile(r"^.*$", re.M)

ATX_HEADING = re.compile(r"^(#{1,6})[ \t]+(.*?)[ \t]*$", re.M)


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
    regions = code_regions(body)

    for raw in headings(body, regions):
        text = heading_text(raw)
        # github-slugger disambiguates a repeated slug with a numeric suffix, and
        # records the suffixed result too -- so a literal "Overview 1" heading
        # cannot collide with the "overview-1" minted for a second "Overview".
        base = slug = starlight_slug(text)
        while slug in seen:
            seen[base] += 1
            slug = "%s-%d" % (base, seen[base])
        seen[slug] = 0
        slugs.add(slug)
        for legacy in legacy_slugs(text):
            aliases.setdefault(legacy, slug)

    # GitBook pins some headings to a hand-written id with an inline anchor tag.
    # Scanned over the prose only: an id in a documented HTML sample is not an
    # anchor, and a phantom slug here would bless a dead link.
    slugs.update(re.findall(r'\bid="([^"]+)"', without_code(body, regions)))

    return slugs, {legacy: slug for legacy, slug in aliases.items() if legacy not in slugs}


def code_regions(text):
    """Character ranges covered by fenced code blocks.

    Tracking the opening fence rather than toggling on any fence-looking line
    keeps a ```-fence nested inside a ````-block from closing the outer block --
    the corpus contains such blocks, and treating their contents as prose would
    rewrite links inside documented examples.
    """
    regions, opener, start = [], None, 0
    for line in LINE.finditer(text):
        m = FENCE.match(line.group(0))
        if opener is None:
            if m:
                opener, start = m.group("fence"), line.start()
        elif m and m.group("fence")[0] == opener[0] and len(m.group("fence")) >= len(opener) \
                and not m.group("info").strip():
            regions.append((start, line.end()))
            opener = None
    if opener is not None:
        regions.append((start, len(text)))
    return regions


def without_code(text, regions=None):
    """The text with every fenced code block removed."""
    parts, last = [], 0
    for start, end in code_regions(text) if regions is None else regions:
        parts.append(text[last:start])
        last = end
    parts.append(text[last:])
    return "".join(parts)


def heading_matches(text, regions=None):
    """Every ATX heading match outside a fenced code block."""
    regions = code_regions(text) if regions is None else regions
    return [m for m in ATX_HEADING.finditer(text)
            if not any(start <= m.start() < end for start, end in regions)]


def headings(text, regions=None):
    return [m.group(2) for m in heading_matches(text, regions)]


def lift_title(body):
    """(title or None, body without its H1). Starlight renders the H1 itself.

    The anchor index has to see the same body the page does: Starlight gives the
    H1 `id="_top"`, not a slug, so leaving it in would mint one anchor per page
    that does not exist and shift the duplicate-slug numbering off by one.
    """
    for m in heading_matches(body):
        if len(m.group(1)) == 1:
            return heading_text(m.group(2)).strip(), body[: m.start()] + body[m.end():]
    return None, body


# --- assets -----------------------------------------------------------------


def normalize_asset_name(name):
    """Fold the unicode spaces macOS screenshots carry down to a plain space."""
    return re.sub(r"\s+", " ", name).strip()


def build_asset_index(directory=None):
    """Real filename, keyed by its normalized form.

    Screenshot filenames from macOS contain U+202F (narrow no-break space) where
    the markdown that references them was written with a plain space. GitBook's
    CDN papered over the difference; a static host will not.
    """
    # Resolved at call time, not bound as a default: the module constant is what
    # callers (and tests) repoint, and a default argument would freeze the value
    # this module happened to have at import.
    directory = GITBOOK_ASSETS if directory is None else directory
    index = {}
    for name in sorted(os.listdir(directory)):
        index.setdefault(normalize_asset_name(name), name)
    return index


def public_asset_url(name):
    """URL of an asset served verbatim out of site/public/assets."""
    return "/assets/" + urllib.parse.quote(name)


# Everything outside this set is folded to a hyphen by safe_asset_name.
UNSAFE_IN_ASSET_NAME = re.compile(r"[^A-Za-z0-9._-]+")


def safe_asset_name(name):
    """Asset filename -> a name that is safe to write as a markdown image.

    Astro resolves an encoded destination fine: `%20` and `<angle brackets>`
    both optimize, U+202F included. The hazard is the unencoded form -- a raw
    space makes the line stop being an image as far as CommonMark is concerned,
    so it renders as literal `![alt](path)` text with no error and nothing in
    CI to catch it. Most of the referenced files are macOS screenshots full of
    spaces, parentheses and U+202F, so the names change on the way into
    src/assets and neither that nor a `%20` in the built URL can happen.
    """
    stem, ext = os.path.splitext(name)
    stem = UNSAFE_IN_ASSET_NAME.sub("-", stem)
    stem = re.sub(r"-{2,}", "-", stem).strip("-.")
    return stem + ext.lower()


def src_asset_path(name, relpath):
    """Relative path from a converted page to its image in site/src/assets.

    Two levels out of src/content/docs, plus one per directory the page sits in.
    """
    return "../" * (out_for(relpath).count("/") + 2) + "assets/" + safe_asset_name(name)


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
    leading quote from the second, so both need real scalar handling, and there
    is no yaml module in the standard library.

    Supported: `key: value` at the top level, with plain, single-quoted,
    double-quoted, folded (`>`) and literal (`|`) scalars, including the escapes
    a double-quoted scalar can carry. Not supported, because GitBook emits none
    of it: nested mappings, sequences, anchors and aliases, and explicit tags --
    all of which are skipped rather than parsed, so a page that grows one would
    silently lose the field rather than mis-set it.

    Two deliberate approximations, verified against PyYAML to make no difference
    over the current 46 files: chomping indicators are accepted and ignored
    (every value is stripped, so a trailing newline would be dropped anyway), and
    a more-indented continuation line inside a folded block is folded rather than
    kept as a literal break.
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

        block = re.match(r"^([|>])[+-]?$", value)
        if block:
            body = []
            while i < len(lines) and (not lines[i].strip() or lines[i][:1] in " \t"):
                body.append(lines[i].strip())
                i += 1
            fields[key] = (fold(body) if block.group(1) == ">" else "\n".join(body)).strip()
            continue

        fields[key] = unquote_scalar(value)

    return fields, text[m.end():]


def fold(lines):
    """Join a YAML folded (`>`) block: a space between lines, but a blank line
    is a real line break rather than a wider gap."""
    folded = ""
    for line in lines:
        if not line:
            folded += "\n"
        elif folded and not folded.endswith("\n"):
            folded += " " + line
        else:
            folded += line
    return folded


# The escapes a double-quoted YAML scalar can carry. Anything else after a
# backslash is passed through as the character itself.
DOUBLE_QUOTED_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "0": "\0"}

UNICODE_ESCAPE = re.compile(r"\\(?:x([0-9a-fA-F]{2})|u([0-9a-fA-F]{4})|U([0-9a-fA-F]{8}))")


def unquote_scalar(value):
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return value[1:-1].replace("''", "'")
    if len(value) >= 2 and value[0] == value[-1] == '"':
        inner = UNICODE_ESCAPE.sub(
            lambda m: chr(int(next(g for g in m.groups() if g), 16)), value[1:-1])
        return re.sub(r"\\(.)",
                      lambda m: DOUBLE_QUOTED_ESCAPES.get(m.group(1), m.group(1)),
                      inner)
    return value


# --- link rewriting ---------------------------------------------------------


class Conversion:
    """Everything a page conversion needs to resolve references site-wide."""

    def __init__(self, sources, assets):
        self.assets = assets
        self.asset_names = set(self.assets.values())
        self.anchors = {}
        for rel in sources:
            _, body = lift_title(strip_frontmatter(read(os.path.join(REPO, rel))))
            self.anchors[url_for(rel)] = page_anchors(body)
        self.missing_assets = []
        self.unresolved_anchors = []
        # Real on-disk filenames, split by where the reference needs them to
        # live: src/assets goes through Astro's optimizer, public/assets does
        # not. Only what lands in one of these is copied out of .gitbook.
        self.image_assets = set()
        self.public_assets = set()
        self.unconverted_figures = []

    def image_asset(self, relpath, name):
        """An asset referenced as a markdown image -> its src/assets path."""
        name = self.resolve_asset(relpath, name)
        self.image_assets.add(name)
        return src_asset_path(name, relpath)

    def public_asset(self, relpath, name):
        """An asset Astro cannot optimize -> its public/assets URL."""
        name = self.resolve_asset(relpath, name)
        self.public_assets.add(name)
        return public_asset_url(name)

    def resolve_asset(self, relpath, name):
        if name in self.asset_names:
            return name
        real = self.assets.get(normalize_asset_name(name))
        if real is None:
            self.record(self.missing_assets, (relpath, name))
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
        self.record(self.unresolved_anchors, (relpath, url + "#" + anchor))
        return anchor

    @staticmethod
    def record(collected, item):
        """Collect a diagnostic once. The same dead link often appears twice."""
        if item not in collected:
            collected.append(item)


def rewrite_target(target, relpath, ctx, page_url, is_image=False):
    """Link destination -> rewritten URL, or None to leave it as written.

    `is_image` decides where an asset reference points. Astro rewrites markdown
    image nodes and nothing else, so only those can use the relative src/assets
    path that puts the file through the optimizer.
    """
    if target.startswith("#"):
        return "#" + ctx.resolve_anchor(relpath, page_url, target[1:])

    # Before the asset check: an absolute URL that happens to contain
    # ".gitbook/assets/" belongs to somebody else's site, and rewriting it to a
    # local path would turn a working link into a fatal missing-asset error.
    if not target or EXTERNAL_TARGET.match(target):
        return None

    if ".gitbook/assets/" in target:
        name = urllib.parse.unquote(target.split(".gitbook/assets/")[-1])
        place = ctx.image_asset if is_image else ctx.public_asset
        return place(relpath, name)

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


def is_image_destination(text, close):
    """Is the `]` at index `close` the end of an image's alt text?

    Walks back to the matching `[` rather than folding the `!` into MD_LINK,
    which would stop matching the outer destination of a nested
    `[![alt](a)](b)` -- a shape the corpus already contains.
    """
    depth = 0
    for i in range(close, -1, -1):
        if text[i] == "]" and not text[i - 1: i] == "\\":
            depth += 1
        elif text[i] == "[" and not text[i - 1: i] == "\\":
            depth -= 1
            if depth == 0:
                return text[i - 1: i] == "!"
    return False


def rewrite_references(text, relpath, ctx, page_url):
    """Point every asset, page and anchor reference at its Starlight home."""

    def markdown(m):
        raw = m.group(1)
        target = raw[1:-1] if raw.startswith("<") else raw
        rewritten = rewrite_target(target, relpath, ctx, page_url,
                                   is_image=is_image_destination(text, m.start()))
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
    parts, last = [], 0
    for start, end in code_regions(text):
        parts.append(transform(text[last:start]))
        parts.append(text[start:end])
        last = end
    parts.append(transform(text[last:]))
    return "".join(parts)


# --- embeds -----------------------------------------------------------------


def embed_html(url, relpath, ctx):
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
            'margin:1.5rem 0" src="' + ctx.public_asset(relpath, name) + '"></video>'
        )

    return '<p><a href="%s">%s</a></p>' % (url, url)


# A captioned embed. The caption is one or more non-blank lines: a blank line
# separates an uncaptioned embed from the prose that follows it, and requiring
# at least one line keeps `{% embed %}{% endembed %}` -- GitBook's shape for an
# uncaptioned video -- from producing an empty <figcaption>.
CAPTIONED_EMBED = re.compile(
    r'\{%\s*embed url="([^"]+)"\s*%\}[ \t]*\n((?:[^\n]+\n)+?)\{%\s*endembed\s*%\}[ \t]*\n?'
)


def convert_embeds(body, relpath, ctx):
    """GitBook embeds -> a figure, so the caption stays a caption."""

    def captioned(m):
        caption = html.escape(m.group(2).strip(), quote=False)
        return "<figure>%s<figcaption><p>%s</p></figcaption></figure>\n" % (
            embed_html(m.group(1), relpath, ctx),
            caption,
        )

    body = CAPTIONED_EMBED.sub(captioned, body)
    body = re.sub(r'\{%\s*embed url="([^"]+)"\s*%\}',
                  lambda m: embed_html(m.group(1), relpath, ctx), body)
    return re.sub(r"\{%\s*endembed\s*%\}\n?", "", body)


# --- figures ----------------------------------------------------------------


# GitBook exported every screenshot as this one shape. Across the 45 pages the
# only attributes that ever appear are src, alt and an optional width, and every
# caption is a bare <figcaption><p>text</p></figcaption>.
FIGURE_IMAGE = re.compile(
    r'<figure><img src="(?P<src>[^"]*)" alt="(?P<alt>[^"]*)"'
    r'(?: width="(?P<width>\d+)")?>'
    r"(?:<figcaption>(?P<caption>.*?)</figcaption>)?</figure>",
    re.S,
)


def convert_figures(body):
    """<figure><img> -> a figure wrapped around a *markdown* image.

    Astro only optimizes images written as markdown, so the <img> has to go.
    The blank lines are load-bearing: a CommonMark HTML block ends at a blank
    line, which is what lets the image parse as markdown while still nesting
    inside the surrounding <figure>.

    The width moves onto the figure as CSS. Keeping it as an <img width> would
    force the image back to raw HTML and out of the optimizer, and a shared
    stylesheet rule cannot stand in for it -- the 44 widths span 179-375px
    across 12 distinct values, so one rule would visibly resize the narrow
    screenshots.
    """

    def figure(m):
        style = ' style="max-width:%spx"' % m.group("width") if m.group("width") else ""
        caption = m.group("caption")
        return "<figure%s>\n\n![%s](<%s>)\n\n%s</figure>" % (
            style,
            m.group("alt"),
            m.group("src"),
            "<figcaption>%s</figcaption>\n" % caption if caption else "",
        )

    return FIGURE_IMAGE.sub(figure, body)


# A <figure> that still contains an <img> after convert_figures ran: a shape the
# pattern above does not cover. Nothing breaks -- the reference falls through to
# the HTML-attribute path and the image is served unoptimized out of
# public/assets -- which is exactly why it needs saying out loud.
UNCONVERTED_FIGURE = re.compile(r"<figure[^>]*>(?:(?!</figure>).)*<img", re.S)


# --- page conversion --------------------------------------------------------


def convert(text, relpath, ctx):
    page_url = url_for(relpath)

    frontmatter, body = parse_frontmatter(text)

    title, body = lift_title(body)
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
        chunk = convert_embeds(chunk, relpath, ctx)
        chunk = re.sub(r"\{%[^%]*%\}", "", chunk)
        # Before rewrite_references, so the markdown image it produces is the
        # thing that gets resolved -- asset resolution stays in one place, and
        # the figure pass stays a pure structural transform.
        chunk = convert_figures(chunk)
        if UNCONVERTED_FIGURE.search(chunk):
            ctx.record(ctx.unconverted_figures, relpath)
        chunk = rewrite_references(chunk, relpath, ctx, page_url)
        return chunk.replace(":desktop:", "\U0001f5a5️")

    body = outside_code(body, prose)

    body = re.sub(r"\n:::(note|tip|caution|danger)\n\n", r"\n:::\1\n", body)
    body = re.sub(r"\n\n:::\n", "\n:::\n", body)

    out = ["---", "title: " + json.dumps(title, ensure_ascii=False)]
    description = frontmatter.get("description")
    if description:
        out.append("description: " + json.dumps(description, ensure_ascii=False))
    out.append("---")
    return "\n".join(out) + "\n" + body.lstrip("\n")


def build_sidebar(summary):
    """Build the Starlight sidebar from the text of SUMMARY.md."""
    lines = summary.split("\n")
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


# Written into an --out directory so a re-run can tell its own output apart from
# markdown that was already there.
OUT_STAMP = ".gitbook-to-starlight-out"


def is_within(parent, child):
    """Is `child` at or below `parent`? Both must be absolute."""
    try:
        return os.path.commonpath([parent, child]) == parent
    except ValueError:
        return False


def stray_markdown(directory):
    """The first .md file under `directory` that this converter did not write.

    Follows symlinks: a symlinked subdirectory is markdown that a write would
    reach, so it is markdown this check has to see. Directories already visited
    are skipped by real path, which is what stops a symlink cycle from looping
    forever. Two links to the same subtree in one directory are still both
    walked; the check only needs the first .md it finds, so that costs nothing.
    """
    if not os.path.isdir(directory) or os.path.exists(os.path.join(directory, OUT_STAMP)):
        return None
    seen = set()
    for root, dirs, files in os.walk(directory, followlinks=True):
        dirs[:] = sorted(d for d in dirs if not d.startswith(".")
                         and os.path.realpath(os.path.join(root, d)) not in seen)
        seen.update(os.path.realpath(os.path.join(root, d)) for d in dirs)
        for name in sorted(files):
            if name.endswith(".md"):
                return os.path.join(root, name)
    return None


def path_within(root, relative):
    """Absolute path for `root/relative`, refusing anything that escapes `root`.

    `--out` is validated once, at parse time, on the target root. But the write
    happens later, on paths derived from it, and `open()` follows symlinks -- so
    a symlinked subdirectory under an accepted target was enough to lay converted
    pages on top of the GitBook sources while the run reported it had left them
    alone. Enumerating bad targets cannot close that: the gap is the distance
    between validating a path and acting on it.

    So containment is asserted again here, immediately before the write.
    `realpath` resolves every existing component, and a component that does not
    exist yet cannot be a symlink, so symlink escapes are closed by construction
    rather than by having listed the ways in.

    Scope, precisely. This gates everything written into the output directory --
    the 45 pages and the stamp -- which is the only destination a caller
    supplies. `sidebar.json` and the copies into `src/assets` and
    `public/assets` do *not* go through it: their destinations are module
    constants derived from `__file__`, never user input, and they are written
    only on the default run, never under `--out`.

    It remains a check-then-use assertion, not an atomic one. Nothing stops a
    concurrent writer with access to the output directory from swapping a
    component between the check and the write. That is fine for a local
    development script and is not a claim this makes.
    """
    resolved = os.path.realpath(os.path.join(root, relative))
    if not is_within(os.path.realpath(root), resolved):
        raise SystemExit(
            "Refusing to write %s: it resolves to\n    %s\nwhich is outside the "
            "output directory\n    %s\nA symlinked directory under the output "
            "target would put converted pages on top of real files."
            % (relative, resolved, os.path.realpath(root)))
    return os.path.join(root, relative)


def write_within(root, relative, text):
    """Write `text` to `root/relative`, refusing anything that escapes `root`.

    Written to a sibling temp file and moved into place. `os.replace` unlinks the
    destination name rather than writing through it, so a destination that is a
    hardlink to a GitBook source keeps its own inode and the source is left
    alone; a page also appears whole or not at all. `O_NOFOLLOW` covers the temp
    name itself, which `path_within` validated as a path but which could still be
    a pre-existing symlink at its final component.
    """
    path = path_within(root, relative)
    partial = path_within(root, relative + ".part")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        fd = os.open(partial, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o644)
        with os.fdopen(fd, "w") as f:
            f.write(text)
        os.replace(partial, path)
    except BaseException:
        if os.path.lexists(partial):
            os.remove(partial)
        raise


def dangling_component(path):
    """The first component of `path` that is a symlink pointing nowhere.

    Checked so a broken link anywhere in the target -- not just at its last
    component -- reports as a one-line error rather than a traceback out of
    os.makedirs.
    """
    components, current = [], os.path.abspath(path)
    while True:
        components.append(current)
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    for component in reversed(components):
        if os.path.islink(component) and not os.path.exists(component):
            return component
    return None


def unusable_out_dir(target):
    """Why `target` is unsafe to write converted pages into, or None if it is fine.

    Every check lives here rather than at the call sites. --out has now failed
    open three ways -- a missing value, an empty value, and a target that
    overwrites real files -- and the third one rewrote 40 tracked GitBook source
    pages in place while the run reported that nothing had been written. The
    common shape is a caller reading a value it never validated, so validation
    happens once, before anything can act on it.
    """
    repo = os.path.realpath(REPO)
    resolved = os.path.realpath(target)

    if is_within(repo, resolved):
        # `--out .`, `--out $PWD`, `--out docs`, `--out src/content/docs`.
        # Writing here overwrites the converter's own input or its hand-edited
        # output, and the tree becomes the next run's input too: find_sources()
        # walks everything outside SKIP_DIRS, so a scratch directory at the repo
        # root silently doubles the page set.
        return ("%s is inside the repo. The converter reads the repo for source "
                "markdown, so it would overwrite its own input and then read the "
                "output back as source. Use a directory outside %s." % (resolved, repo))

    if is_within(resolved, repo):
        # `--out /`, `--out ~`.
        return ("%s contains the repo, so writing the converted tree into it "
                "would overwrite the source markdown. Use a directory outside %s."
                % (resolved, repo))

    broken = dangling_component(target)
    if broken:
        return "%s is unusable: %s is a symlink that points nowhere." % (target, broken)

    if os.path.islink(target) and not os.path.isdir(target):
        return "%s is a symlink that does not point at a directory." % target

    if os.path.exists(resolved) and not os.path.isdir(resolved):
        return "%s exists and is not a directory." % resolved

    stray = stray_markdown(resolved)
    if stray:
        return ("%s already contains markdown this converter did not write (%s). "
                "Use an empty or new directory so nothing is overwritten."
                % (resolved, stray))

    return None


def parse_args(argv):
    """Parse and validate the command line.

    argparse rather than hand-rolled matching because the failure mode matters:
    an unrecognised argument -- `--out=DIR` under a hand-rolled `--out` check, or
    a typo like `--outt` -- used to fall through to the default run, which starts
    by deleting src/content/docs. The functional spec forbids that once content
    is hand-edited, so an argument this parser does not understand is an error,
    never a silent full rebuild. --out's target is validated here too, for the
    same reason: one place says no, and it says no before anything writes.
    """
    parser = argparse.ArgumentParser(
        prog="gitbook_to_starlight.py",
        description="Convert the GitBook docs at the repo root into Starlight content.",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="print the source pages that would be converted, then exit")
    parser.add_argument(
        "--out", metavar="DIR",
        help="write the converted pages to DIR and nothing else. DIR must be "
             "outside the repo and must not already hold markdown.")
    parser.add_argument(
        "--anchors", action="store_true",
        help="list every link pointing at an anchor no heading provides")
    args = parser.parse_args(argv)

    if args.out is not None:
        # Strip before resolving: an unset shell variable arrives as "" or "  ",
        # and abspath of a padded value silently lands somewhere else entirely.
        target = args.out.strip()
        if not target:
            parser.error("--out needs a directory")
        args.out = os.path.abspath(target)
        unusable = unusable_out_dir(args.out)
        if unusable:
            parser.error("--out %s" % unusable)

    return args


def report(ctx, list_anchors=False):
    """Print unresolved references. Missing assets are fatal, anchors are not.

    The anchors are stale in the GitBook source and there is a known backlog of
    them, so they get one summary line by default. Printing all of them on every
    build would train people to ignore the channel the fatal error uses too.
    """
    if ctx.unresolved_anchors:
        if list_anchors:
            for relpath, anchor in ctx.unresolved_anchors:
                print("warning: %s links to %s, which no heading provides"
                      % (relpath, anchor), file=sys.stderr)
        print("warning: %d link(s) point at anchors no heading provides; these are "
              "stale in the GitBook source too. Re-run with --anchors to list them."
              % len(ctx.unresolved_anchors), file=sys.stderr)

    for relpath in ctx.unconverted_figures:
        print("warning: %s has a <figure> the image pass did not match, so its "
              "image skips Astro's optimizer" % relpath, file=sys.stderr)

    if ctx.missing_assets:
        for relpath, name in ctx.missing_assets:
            print("error: %s references missing asset %r" % (relpath, name), file=sys.stderr)
        raise SystemExit("%d referenced asset(s) do not exist in .gitbook/assets"
                         % len(ctx.missing_assets))


TRACKED, UNTRACKED, UNKNOWN = "tracked", "untracked", "unknown"


def git_status_of(path):
    """(state, detail) for whether git has committed files under `path`.

    UNKNOWN means git could not answer, which is not the same as "no": it covers
    git missing entirely, and also a real checkout where git failed -- dubious
    ownership when a container runs as a different uid than the checkout owner, a
    held index.lock, a damaged index. The caller decides what to do with each,
    because reading UNKNOWN as UNTRACKED is how committed content gets deleted.
    """
    try:
        found = subprocess.run(
            ["git", "ls-files", "--", path],
            cwd=REPO, capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as error:
        return UNKNOWN, str(error)
    if found.returncode != 0:
        return UNKNOWN, found.stderr.strip() or "git exited %d" % found.returncode
    return (TRACKED if found.stdout.strip() else UNTRACKED), ""


def refuse_to_rebuild_committed_output():
    """Stop the destructive run when src/content/docs is hand-maintained content.

    It is committed now, and the functional spec forbids a full re-run over it.
    Unwiring this script from `npm run build` and `npm run dev` -- which is what
    used to make the refusal urgent -- means nothing reaches it by accident any
    more. It stays because the cost of being wrong is asymmetric: refusing costs
    a re-run, guessing wrong costs the content.
    """
    relative = os.path.relpath(DOCS_OUT, REPO)
    advice = ("Convert into a scratch directory instead:\n"
              "    python3 scripts/gitbook_to_starlight.py --out DIR\n"
              "and copy in only the pages you actually need.")

    state, detail = git_status_of(DOCS_OUT)
    if state == TRACKED:
        raise SystemExit(
            "%s is committed to git, so it is hand-maintained content and a full\n"
            "re-run would delete it. %s" % (relative, advice))

    # exists, not isdir: in a worktree or submodule checkout .git is a *file*
    # holding a gitdir: pointer, and those are exactly the container setups the
    # dubious-ownership failure shows up in.
    if state == UNKNOWN and os.path.exists(os.path.join(REPO, ".git")):
        # A checkout whose git we cannot query. Refusing costs a build; guessing
        # "not committed" costs the content this guard exists to protect.
        raise SystemExit(
            "This is a git checkout, but git could not say whether %s is\n"
            "committed: %s\n"
            "Refusing to delete and rebuild it on a guess. Fix git (a dubious-ownership\n"
            "checkout needs `git config --global --add safe.directory %s`), or:\n%s"
            % (relative, detail, REPO, advice))


def report_assets_to_copy(ctx):
    """Name the assets an --out run's pages reference but did not copy.

    --out deliberately writes pages and nothing else, so a reconciled page
    arrives referencing ../../../assets/some-safe-name.png with no such file. The
    mapping is right here in the Conversion and is otherwise thrown away, which
    would leave the operator to rediscover safe_asset_name() by hand.
    """
    if not ctx.image_assets and not ctx.public_assets:
        return
    print("\nAssets these pages reference. Copy any the site does not already have:")
    for name in sorted(ctx.image_assets):
        print("  %-52s -> site/src/assets/%s"
              % (".gitbook/assets/" + name, safe_asset_name(name)))
    for name in sorted(ctx.public_assets):
        print("  %-52s -> site/public/assets/%s" % (".gitbook/assets/" + name, name))


def copy_assets(ctx):
    """Copy the referenced assets out of .gitbook, and report what was left.

    Images go to src/assets under a sanitized name so Astro's optimizer can
    resolve them; videos and anything else Astro will not process go to
    public/assets verbatim. Everything unreferenced stays behind -- it is
    reported rather than quietly dropped, because this is the run that decides
    which of the 159 files survive the migration.
    """
    for directory in (SRC_ASSETS, ASSETS_OUT):
        if os.path.isdir(directory):
            shutil.rmtree(directory)
        os.makedirs(directory)

    # Keyed casefolded: on a case-insensitive filesystem -- APFS, which is where
    # a corpus of macOS screenshots comes from -- Foo.png and foo.png are two
    # keys but one file, so the second copy would silently win.
    # Seeded with the hero, which is copied unconditionally below and would
    # otherwise be the one destination no collision check covers.
    safe_names = {"hero.png".casefold(): HERO_SOURCE}
    for name in sorted(ctx.image_assets):
        safe = safe_asset_name(name)
        clash = safe_names.get(safe.casefold())
        if clash is not None:
            raise SystemExit(
                "%r would be written to site/src/assets/%s, which %r already "
                "claims. Rename one in .gitbook/assets." % (name, safe, clash))
        safe_names[safe.casefold()] = name
        shutil.copy(os.path.join(GITBOOK_ASSETS, name), os.path.join(SRC_ASSETS, safe))

    for name in sorted(ctx.public_assets):
        shutil.copy(os.path.join(GITBOOK_ASSETS, name), os.path.join(ASSETS_OUT, name))

    shutil.copy(os.path.join(GITBOOK_ASSETS, HERO_SOURCE),
                os.path.join(SRC_ASSETS, "hero.png"))

    referenced = ctx.image_assets | ctx.public_assets | {HERO_SOURCE}
    unreferenced = sorted(set(os.listdir(GITBOOK_ASSETS)) - referenced)
    print("Copied %d image(s) plus the hero to %s, and %d file(s) to %s."
          % (len(ctx.image_assets), os.path.relpath(SRC_ASSETS, REPO),
             len(ctx.public_assets), os.path.relpath(ASSETS_OUT, REPO)))
    print("%d unreferenced asset(s) in %s were not copied:"
          % (len(unreferenced), os.path.relpath(GITBOOK_ASSETS, REPO)))
    for name in unreferenced:
        print("  " + name)


# The last commit that still carries the GitBook tree. Phase 3 deleted it, so
# any later run has to restore it first, and the error below has to say so.
# Spelled in full: the whole recovery path depends on it resolving.
GITBOOK_TREE_COMMIT = "3e16f5af77fc0e0e27a6785ec78a5f6c1761a889"


def require_gitbook_sources():
    """Fail with the recovery procedure, not a traceback, once the inputs are gone.

    Phase 3 deleted `.gitbook/`, `docs/`, `developers/` and `SUMMARY.md` from
    the working tree. Without this the first thing a reconciliation run hits is
    a bare FileNotFoundError out of build_asset_index().
    """
    # Every input the run reads. `developers` earns its place as much as the
    # rest: it holds three pages, and without it the run converts 42 of 45 and
    # exits 0, which is worse than the traceback this function replaced.
    missing = [rel for rel in (".gitbook/assets", "docs", "developers", "SUMMARY.md")
               if not os.path.exists(os.path.join(REPO, rel))]
    if not missing:
        return
    raise SystemExit(
        "The GitBook source tree is not in this checkout (missing: %s).\n"
        "It was deleted once its content moved into site/src/content/docs.\n"
        "Restore it into a worktree and convert from there:\n"
        "    git worktree add /tmp/gitbook %s\n"
        "    cp %s /tmp/gitbook/site/scripts/\n"
        "    cd /tmp/gitbook/site && python3 scripts/gitbook_to_starlight.py --out /tmp/converted\n"
        "\n"
        "The copy is not optional. The worktree is checked out at a commit that predates\n"
        "this script, so without it you would run that older converter, which writes\n"
        "<img src=\"/assets/NAME\"> for images that now live in site/src/assets -- a 404\n"
        "nothing validates. This script cannot simply be run in place, either: it locates\n"
        "the repo from its own path, so it would look right back here and fail again.\n"
        "\n"
        "Use a worktree rather than checking the old paths out into this one: a\n"
        "worktree cannot be committed back here by accident, and it cannot leave\n"
        "half the GitBook tree behind for the next run to trip over."
        % (", ".join(missing), GITBOOK_TREE_COMMIT, os.path.abspath(__file__)))


def list_sources(sources):
    """Print what would be converted. Diagnostic for a surprising page count."""
    try:
        print("Repo root: %s" % REPO)
        print("%d source pages:" % len(sources))
        for rel in sources:
            print("  " + rel)
        sys.stdout.flush()
    except BrokenPipeError:
        # Piping into `head` and friends closes stdout early.
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)

    require_gitbook_sources()
    sources = find_sources()
    if args.list:
        list_sources(sources)
        return

    if args.out is None:
        refuse_to_rebuild_committed_output()

    # Convert everything before writing anything, so a missing asset stops the
    # run instead of leaving a half-written tree behind.
    ctx = Conversion(sources, build_asset_index())
    pages = {rel: convert(read(os.path.join(REPO, rel)), rel, ctx) for rel in sources}
    report(ctx, args.anchors)

    docs_out = DOCS_OUT if args.out is None else args.out
    if args.out is None and os.path.isdir(docs_out):
        shutil.rmtree(docs_out)
    os.makedirs(docs_out, exist_ok=True)

    for rel, converted in pages.items():
        write_within(docs_out, out_for(rel), converted)

    if args.out is not None:
        write_within(docs_out, OUT_STAMP,
                     "Converted pages written by site/scripts/gitbook_to_starlight.py"
                     " --out. Safe to delete.\n")
        print("Converted %d pages into %s.\nLeft untouched: %s, %s, %s."
              % (len(pages), docs_out,
                 os.path.relpath(DOCS_OUT, REPO),
                 os.path.relpath(ASSETS_OUT, REPO),
                 os.path.relpath(os.path.join(SITE, "sidebar.json"), REPO)))
        report_assets_to_copy(ctx)
        return

    copy_assets(ctx)

    sidebar = build_sidebar(read(os.path.join(REPO, "SUMMARY.md")))
    with open(os.path.join(SITE, "sidebar.json"), "w") as f:
        json.dump(sidebar, f, indent=2, ensure_ascii=False)

    entries = sum(len(g["items"]) for g in sidebar)
    print("Converted %d pages, %d sidebar entries across %d groups."
          % (len(pages), entries, len(sidebar)))


if __name__ == "__main__":
    main()
