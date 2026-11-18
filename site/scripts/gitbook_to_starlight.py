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
"""

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


def asset_url(name):
    return "/assets/" + urllib.parse.quote(name)


def rewrite_assets(text):
    """Point .gitbook/assets references at the copies under public/assets."""

    def repl(m):
        pre, path, post = m.group(1), m.group(2), m.group(3)
        name = urllib.parse.unquote(path.split(".gitbook/assets/")[-1])
        return pre + asset_url(name) + post

    text = re.sub(r'(src=")([^"]*\.gitbook/assets/[^"]*)(")', repl, text)
    text = re.sub(r'(href=")([^"]*\.gitbook/assets/[^"]*)(")', repl, text)
    text = re.sub(r"(\]\()([^)]*\.gitbook/assets/[^)]*)(\))", repl, text)
    return text


def rewrite_links(text, srcdir):
    """Turn relative .md links into absolute Starlight URLs."""

    def repl(m):
        target = m.group(1)
        if re.match(r"^(https?:|mailto:|#|/)", target) or ".gitbook/assets/" in target:
            return m.group(0)
        anchor = ""
        if "#" in target:
            target, anchor = target.split("#", 1)
            anchor = "#" + anchor
        if not target:
            return m.group(0)
        resolved = os.path.normpath(os.path.join(srcdir, target))
        if resolved.endswith(".md"):
            return "](" + url_for(resolved) + anchor + ")"
        if os.path.isdir(os.path.join(REPO, resolved)):
            return "](/" + resolved.strip("/") + "/" + anchor + ")"
        return m.group(0)

    return re.sub(r"\]\(([^)\s]*)\)", repl, text)


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


def convert(text, relpath):
    srcdir = os.path.dirname(relpath)

    frontmatter = {}
    body = text
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if m:
        for line in m.group(1).split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                frontmatter[key.strip()] = value.strip()
        body = text[m.end() :]

    # Starlight renders the title itself, so lift the H1 out of the body.
    title = None
    m = re.search(r"^#\s+(.+?)\s*$", body, re.M)
    if m:
        title = m.group(1)
        body = body[: m.start()] + body[m.end() :]
    if not title:
        title = os.path.basename(relpath)[:-3].replace("-", " ").title()

    body = re.sub(
        r'\{%\s*hint style="(\w+)"\s*%\}',
        lambda m: ":::" + HINTS.get(m.group(1), "note"),
        body,
    )
    body = re.sub(r"\{%\s*endhint\s*%\}", ":::", body)
    # {% code %} only carried display options; Expressive Code handles those.
    body = re.sub(r"\{%\s*code[^%]*%\}\n?", "", body)
    body = re.sub(r"\{%\s*endcode\s*%\}\n?", "", body)
    body = re.sub(r'\{%\s*embed url="([^"]+)"\s*%\}', lambda m: embed_html(m.group(1)), body)
    body = re.sub(r"\{%\s*endembed\s*%\}\n?", "", body)
    body = re.sub(r"\{%[^%]*%\}", "", body)

    body = rewrite_assets(body)
    body = rewrite_links(body, srcdir)
    body = body.replace(":desktop:", "\U0001f5a5️")

    body = re.sub(r"\n:::(note|tip|caution|danger)\n\n", r"\n:::\1\n", body)
    body = re.sub(r"\n\n:::\n", "\n:::\n", body)

    out = ["---", "title: " + json.dumps(title)]
    description = frontmatter.get("description")
    if description:
        out.append("description: " + json.dumps(description.strip("\"'")))
    out.append("---")
    return "\n".join(out) + "\n" + body.lstrip("\n")


def build_sidebar():
    """Build the Starlight sidebar from SUMMARY.md."""
    lines = open(os.path.join(REPO, "SUMMARY.md")).read().split("\n")
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
        label = label.replace("\\", "")
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


def main():
    # `--list` prints what would be converted, without writing anything. Use it
    # when the page count looks wrong to see exactly which files are picked up.
    if "--list" in sys.argv:
        sources = find_sources()
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

    if os.path.isdir(DOCS_OUT):
        shutil.rmtree(DOCS_OUT)
    os.makedirs(DOCS_OUT)

    sources = find_sources()

    for rel in sources:
        text = open(os.path.join(REPO, rel)).read()
        out_path = os.path.join(DOCS_OUT, out_for(rel))
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        open(out_path, "w").write(convert(text, rel))

    # Hand-written landing page (the GitBook card table doesn't convert).
    shutil.copy(os.path.join(SITE, "src/landing/index.mdx"), os.path.join(DOCS_OUT, "index.mdx"))

    os.makedirs(SRC_ASSETS, exist_ok=True)
    shutil.copy(os.path.join(GITBOOK_ASSETS, HERO_SOURCE), os.path.join(SRC_ASSETS, "hero.png"))

    if os.path.isdir(ASSETS_OUT):
        shutil.rmtree(ASSETS_OUT)
    shutil.copytree(GITBOOK_ASSETS, ASSETS_OUT)

    sidebar = build_sidebar()
    with open(os.path.join(SITE, "sidebar.json"), "w") as f:
        json.dump(sidebar, f, indent=2)

    pages = sum(len(g["items"]) for g in sidebar)
    print("Converted %d pages, %d sidebar entries across %d groups."
          % (len(sources), pages, len(sidebar)))


if __name__ == "__main__":
    main()
