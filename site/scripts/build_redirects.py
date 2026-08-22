#!/usr/bin/env python3
"""Build the Cloudflare Pages `_redirects` file from `redirects.csv`.

`redirects.csv` is the committed, human-reviewable record of every URL the old
GitBook site served. `public/_redirects` is derived from it and committed too,
so that deploying needs nothing but `astro build`.

    python3 scripts/build_redirects.py                # csv -> public/_redirects
    python3 scripts/build_redirects.py --check        # is the committed file stale?
    python3 scripts/build_redirects.py --refresh-csv  # regenerate the machine rows

See `specs/projects/gitbook-to-starlight-migration/phase_plans/phase_4.md` for
the data model and the reconciliation procedure.
"""

from __future__ import annotations

import argparse
import csv
import difflib
import io
import re
import sys
from pathlib import Path
from typing import NamedTuple
from urllib.parse import urlsplit
from xml.etree import ElementTree

SITE_DIR = Path(__file__).resolve().parent.parent

CSV_PATH = SITE_DIR / "redirects.csv"
REDIRECTS_PATH = SITE_DIR / "public" / "_redirects"
SITEMAP_PATH = SITE_DIR / "ref" / "legacy_sitemap.xml"
EXCLUSIONS_PATH = SITE_DIR / "ref" / "alias_exclusions.txt"
CONTENT_DIR = SITE_DIR / "src" / "content" / "docs"

LEGACY_ORIGIN = "docs.kiln.tech"

CSV_HEADER = ["old_path", "new_path", "status", "source"]

# Sources this script derives from files in `ref/`. `--refresh-csv` rewrites
# every row carrying one of these and leaves everything else alone.
GENERATED_SOURCES = ("sitemap", "alias-generated", "structural")

# Sources only a human can supply. `alias` means a flat alias that phase 1's
# probe confirmed returns 200 — deliberately a different value from
# `alias-generated`, which is a guess from a pattern and has never been
# requested against the live site.
HUMAN_SOURCES = ("alias", "crawl", "gsc", "manual")

VALID_SOURCES = GENERATED_SOURCES + HUMAN_SOURCES

SOURCE_BLURBS = {
    "sitemap": "verbatim from ref/legacy_sitemap.xml",
    "alias-generated": "inferred from the flat-alias pattern, NOT probe-confirmed",
    "structural": "paths we chose to catch, not ones we observed",
    "alias": "flat alias confirmed live by the phase 1 probe",
    "crawl": "found by the phase 1 link crawl",
    "gsc": "from the Search Console indexed-pages export",
    "manual": "added by hand",
}

# 301 is the rule. 302 exists in the schema only for the launch-week rollback
# window the functional spec allows; nothing uses it today.
VALID_STATUSES = (301, 302)

# Section roots the nav points into. Neither is built as a page and neither is
# in the legacy sitemap, but both are trivially hand-typeable.
STRUCTURAL_REDIRECTS = (
    ("/docs", "/docs/quickstart/"),
    ("/docs/", "/docs/quickstart/"),
    ("/developers", "/developers/python-library-quickstart/"),
    ("/developers/", "/developers/python-library-quickstart/"),
)

# Cloudflare Pages caps static redirect rules. The architecture records ~2,000
# and asks for it to be confirmed against current Cloudflare docs before
# cutover. We are two orders of magnitude below it; this exists so the script
# errors instead of silently shipping a truncated rule set.
MAX_RULES = 2000

PAGE_SUFFIXES = (".md", ".mdx")


class RedirectError(Exception):
    """Any problem that should stop the build with a readable message."""


class Row(NamedTuple):
    old_path: str
    new_path: str
    status: int
    source: str


class Annotations(NamedTuple):
    """`#` comments in `redirects.csv`, keyed by the row they sit above."""

    header: list[str]
    by_old_path: dict[str, list[str]]
    trailing: list[str]


# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------


def canonical_path(url_or_path: str) -> str:
    """Reduce a sitemap URL or a bare path to the path we match on.

    Absolute URLs are accepted only for the legacy origin — anything else is a
    typo or a link off-site, and neither belongs in a redirect rule.
    """
    value = " ".join(url_or_path.split())
    if not value:
        raise RedirectError("empty path")

    if "://" in value:
        parts = urlsplit(value)
        if parts.hostname != LEGACY_ORIGIN:
            raise RedirectError(
                f"{value!r} is not on {LEGACY_ORIGIN}; redirect rules are path-only"
            )
        path = parts.path or "/"
        if parts.query or parts.fragment:
            raise RedirectError(f"{value!r} carries a query or fragment; use the path alone")
    else:
        path = value
        if "?" in path or "#" in path:
            raise RedirectError(f"{value!r} carries a query or fragment; use the path alone")

    if not path.startswith("/"):
        raise RedirectError(f"{value!r} must start with '/'")

    # `//evil.com/x` starts with a slash but is protocol-relative, and `.`/`..`
    # segments mean the rule does not match the string it appears to match.
    # A trailing slash is the one legitimate empty segment.
    segments = path.split("/")[1:]
    if segments and segments[-1] == "":
        segments = segments[:-1]
    if any(segment in ("", ".", "..") for segment in segments):
        raise RedirectError(
            f"{value!r} is not a normalised path; "
            "no empty, '.' or '..' segments, and nothing protocol-relative"
        )
    return path


def with_trailing_slash(path: str) -> str:
    return path if path.endswith("/") else path + "/"


def flat_alias_paths(nested_path: str) -> list[str]:
    """The flat aliases GitBook serves for a nested page, both slash forms.

    GitBook also serves `/docs/a/b/c` at `/docs/c` — first segment kept,
    everything between it and the leaf dropped. Confirmed for
    `/docs/fine-tuning/fine-tuning-guide` -> `/docs/fine-tuning-guide`.
    """
    segments = [segment for segment in nested_path.split("/") if segment]
    if len(segments) < 3:
        return []
    flat = f"/{segments[0]}/{segments[-1]}"
    return [flat, flat + "/"]


def page_exists(path: str, content_dir: Path) -> bool:
    """Does `path` correspond to a page in the content collection?"""
    relative = path.strip("/")
    stems = [relative or "index"]
    if relative:
        stems.append(f"{relative}/index")
    return any(
        (content_dir / f"{stem}{suffix}").is_file()
        for stem in stems
        for suffix in PAGE_SUFFIXES
    )


# --------------------------------------------------------------------------
# Inventory sources
# --------------------------------------------------------------------------


def parse_sitemap(xml_text: str) -> list[str]:
    """`<loc>` values from a sitemap, in document order, deduped.

    `ref/legacy_sitemap.xml` was saved from a browser's XML view, so it opens
    with the browser's prose banner and wraps some `<loc>` values across
    newlines. Both are handled here rather than at every call site.
    """
    start = re.search(r"<(?:\?xml|urlset|sitemapindex)\b", xml_text)
    if start is None:
        raise RedirectError("no <urlset> or <sitemapindex> element found in the sitemap")

    try:
        root = ElementTree.fromstring(xml_text[start.start():])
    except ElementTree.ParseError as error:
        raise RedirectError(f"sitemap is not well-formed XML: {error}") from error

    if _local_name(root.tag) == "sitemapindex":
        raise RedirectError(
            "this is a sitemap index, not a sitemap; its child sitemaps have to be "
            "fetched and saved into ref/ individually"
        )

    urls: list[str] = []
    seen: set[str] = set()
    for element in root.iter():
        if _local_name(element.tag) != "loc":
            continue
        url = " ".join((element.text or "").split())
        if url and url not in seen:
            seen.add(url)
            urls.append(url)
    return urls


def _local_name(tag: str) -> str:
    return tag.rpartition("}")[2]


def read_exclusions(text: str) -> set[str]:
    """Flat-alias paths the phase 1 probe proved do not exist.

    One entry covers both slash forms — an alias that 404s does not 404 only in
    the spelling the author happened to write down.
    """
    paths = set()
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            path = canonical_path(line)
            paths.add(path)
            paths.add(with_trailing_slash(path))
            paths.add(path.rstrip("/") or "/")
    return paths


# --------------------------------------------------------------------------
# CSV
# --------------------------------------------------------------------------


def read_rows(csv_text: str) -> list[Row]:
    numbered = _significant_lines(csv_text)
    if not numbered:
        raise RedirectError("redirects.csv is empty")

    header = _parse_line(numbered[0][1])
    if [field.strip() for field in header] != CSV_HEADER:
        raise RedirectError(f"redirects.csv header must be {','.join(CSV_HEADER)}")

    return [
        _parse_record(_parse_line(line), line_number)
        for line_number, line in numbered[1:]
    ]


def read_annotations(csv_text: str) -> Annotations:
    """The `#` comments in a CSV, tied to the row each one sits above.

    Rows get rewritten and reordered by `--refresh-csv`; a human's note about
    a row should travel with it rather than being silently dropped.
    """
    header_comments: list[str] = []
    by_old_path: dict[str, list[str]] = {}

    pending: list[str] = []
    seen_header = False
    last_old_path: str | None = None

    for line in csv_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            pending.append(stripped)
            continue
        if not seen_header:
            seen_header = True
            header_comments = pending
        else:
            last_old_path = canonical_path(_parse_line(line)[0].strip())
            by_old_path[last_old_path] = pending
        pending = []

    return Annotations(header_comments, by_old_path, pending)


def _parse_line(line: str) -> list[str]:
    return next(csv.reader([line]))


def _significant_lines(csv_text: str) -> list[tuple[int, str]]:
    """Data lines paired with their real line number in the file."""
    return [
        (number, line)
        for number, line in enumerate(csv_text.splitlines(), start=1)
        if line.strip() and not line.lstrip().startswith("#")
    ]


def _parse_record(record: list[str], line_number: int) -> Row:
    if len(record) != len(CSV_HEADER):
        raise RedirectError(
            f"line {line_number}: expected {len(CSV_HEADER)} columns, got {len(record)}"
        )

    old_raw, new_raw, status_raw, source = (field.strip() for field in record)

    try:
        old_path = canonical_path(old_raw)
        new_path = canonical_path(new_raw)
    except RedirectError as error:
        raise RedirectError(f"line {line_number}: {error}") from None

    try:
        status = int(status_raw)
    except ValueError:
        raise RedirectError(f"line {line_number}: status {status_raw!r} is not a number") from None
    if status not in VALID_STATUSES:
        raise RedirectError(
            f"line {line_number}: status {status} is not one of {VALID_STATUSES}"
        )

    if source not in VALID_SOURCES:
        raise RedirectError(
            f"line {line_number}: source {source!r} is not one of {', '.join(VALID_SOURCES)}"
        )

    return Row(old_path, new_path, status, source)


def write_rows(rows: list[Row], annotations: Annotations | None = None) -> str:
    annotations = annotations or Annotations([], {}, [])

    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    for comment in annotations.header:
        buffer.write(comment + "\n")
    writer.writerow(CSV_HEADER)
    for row in rows:
        for comment in annotations.by_old_path.get(row.old_path, ()):
            buffer.write(comment + "\n")
        writer.writerow([row.old_path, row.new_path, row.status, row.source])
    for comment in annotations.trailing:
        buffer.write(comment + "\n")
    return buffer.getvalue()


# --------------------------------------------------------------------------
# Rule set
# --------------------------------------------------------------------------


def dedupe(rows: list[Row]) -> list[Row]:
    """Collapse identical rows; refuse to guess between conflicting ones."""
    kept: list[Row] = []
    by_old: dict[str, Row] = {}
    for row in rows:
        existing = by_old.get(row.old_path)
        if existing is None:
            by_old[row.old_path] = row
            kept.append(row)
        elif (existing.new_path, existing.status) != (row.new_path, row.status):
            raise RedirectError(
                f"{row.old_path} is redirected twice with different results: "
                f"-> {existing.new_path} ({existing.status}, {existing.source}) and "
                f"-> {row.new_path} ({row.status}, {row.source})"
            )
    return kept


def flatten_chains(rows: list[Row]) -> list[Row]:
    """Resolve A->B->C into A->C, so no visitor ever takes two hops.

    Detecting a cycle is what guarantees this terminates: every step either
    reaches a path nothing redirects, or revisits one already on the trail.
    """
    targets = {row.old_path: row.new_path for row in rows}

    flattened = []
    for row in rows:
        destination = row.new_path
        seen = [row.old_path]
        while destination in targets:
            if destination in seen:
                raise RedirectError("redirect cycle: " + " -> ".join(seen + [destination]))
            seen.append(destination)
            destination = targets[destination]
        flattened.append(row._replace(new_path=destination))
    return flattened


def check_slash_variants(rows: list[Row]) -> None:
    """`/a` and `/a/` are different keys to Cloudflare but the same URL to a
    reader. Emitting both is deliberate; sending them to *different* places is
    always a mistake, and nothing else would catch it."""
    by_old = {row.old_path: row for row in rows}
    for row in rows:
        sibling_path = (
            row.old_path.rstrip("/") if row.old_path.endswith("/") else row.old_path + "/"
        )
        if not sibling_path or sibling_path == row.old_path:
            continue
        sibling = by_old.get(sibling_path)
        if sibling is not None and sibling.new_path != row.new_path:
            raise RedirectError(
                f"{row.old_path} and {sibling.old_path} are the same URL but go to "
                f"different places: {row.new_path} and {sibling.new_path}"
            )


def validate_targets(rows: list[Row], content_dir: Path) -> None:
    missing = sorted(
        {row.new_path for row in rows if not page_exists(row.new_path, content_dir)}
    )
    if missing:
        raise RedirectError(
            "redirect targets with no page in "
            f"{content_dir}: {', '.join(missing)}"
        )


def build_rules(rows: list[Row], content_dir: Path | None = CONTENT_DIR) -> list[Row]:
    """CSV rows -> the rules that actually get written out."""
    rules = [row for row in rows if row.old_path != row.new_path]
    rules = dedupe(rules)
    check_slash_variants(rules)
    rules = flatten_chains(rules)
    if content_dir is not None:
        validate_targets(rules, content_dir)
    if len(rules) > MAX_RULES:
        raise RedirectError(
            f"{len(rules)} rules exceeds the Cloudflare Pages cap of {MAX_RULES}"
        )
    return rules


def render_redirects(rules: list[Row], row_count: int) -> str:
    lines = [
        "# Generated by scripts/build_redirects.py from redirects.csv - do not edit.",
        "# Run `npm run redirects` after changing redirects.csv.",
        f"# {len(rules)} rules from {row_count} inventory rows.",
    ]
    for source in VALID_SOURCES:
        grouped = [rule for rule in rules if rule.source == source]
        if not grouped:
            continue
        lines.append("")
        lines.append(f"# {source}: {len(grouped)} rules - {SOURCE_BLURBS[source]}")
        lines.extend(
            f"{rule.old_path} {rule.new_path} {rule.status}" for rule in grouped
        )
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# Refresh
# --------------------------------------------------------------------------


class Refresh(NamedTuple):
    rows: list[Row]
    dropped_ambiguous: list[str]
    dropped_colliding: list[str]
    dropped_excluded: list[str]


def refresh_rows(
    existing: list[Row],
    sitemap_urls: list[str],
    exclusions: set[str],
    content_dir: Path,
) -> Refresh:
    """Regenerate the machine rows; keep every human row exactly as it is.

    A generated row never overwrites a human one: if a human has already
    claimed an `old_path` — typically by promoting an `alias-generated` row to
    `alias` once the probe confirmed it — the generator skips that path.
    """
    preserved = [row for row in existing if row.source not in GENERATED_SOURCES]
    claimed = {row.old_path for row in preserved}

    sitemap_paths = [canonical_path(url) for url in sitemap_urls]

    sitemap_rows = [
        Row(path, with_trailing_slash(path), 301, "sitemap")
        for path in sitemap_paths
        if path not in claimed
    ]

    alias_rows, dropped = _alias_rows(sitemap_paths, claimed, exclusions, content_dir)

    structural_rows = [
        Row(old, new, 301, "structural")
        for old, new in STRUCTURAL_REDIRECTS
        if old not in claimed
    ]

    return Refresh(
        rows=sitemap_rows + alias_rows + structural_rows + preserved,
        **dropped,
    )


def _alias_rows(
    sitemap_paths: list[str],
    claimed: set[str],
    exclusions: set[str],
    content_dir: Path,
) -> tuple[list[Row], dict[str, list[str]]]:
    # Two nested pages sharing a leaf name would flatten to the same alias.
    # There is no way to pick between them, so neither gets a rule.
    owners: dict[str, list[str]] = {}
    for path in sitemap_paths:
        for alias in flat_alias_paths(path):
            owners.setdefault(alias, []).append(path)

    rows = []
    ambiguous, colliding, excluded = [], [], []
    for path in sitemap_paths:
        for alias in flat_alias_paths(path):
            if alias in claimed:
                continue
            if len(owners[alias]) > 1:
                if alias not in ambiguous:
                    ambiguous.append(alias)
                continue
            if alias in exclusions:
                excluded.append(alias)
                continue
            if page_exists(alias, content_dir):
                colliding.append(alias)
                continue
            rows.append(Row(alias, with_trailing_slash(path), 301, "alias-generated"))

    return rows, {
        "dropped_ambiguous": ambiguous,
        "dropped_colliding": colliding,
        "dropped_excluded": excluded,
    }


# --------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------


def _load_rows(csv_path: Path) -> list[Row]:
    if not csv_path.is_file():
        raise RedirectError(f"{csv_path} does not exist")
    return read_rows(csv_path.read_text(encoding="utf-8"))


def _render_from_csv(csv_path: Path, content_dir: Path) -> str:
    rows = _load_rows(csv_path)
    if not rows:
        raise RedirectError(
            f"{csv_path} holds no rows; refusing to write an empty rule set. "
            "Run --refresh-csv to rebuild it from ref/."
        )
    return render_redirects(build_rules(rows, content_dir), len(rows))


def command_build(csv_path: Path, out_path: Path, content_dir: Path) -> int:
    rendered = _render_from_csv(csv_path, content_dir)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(rendered, encoding="utf-8")
    rule_count = sum(1 for line in rendered.splitlines() if line and not line.startswith("#"))
    print(f"wrote {rule_count} rules to {out_path}")
    return 0


def command_check(csv_path: Path, out_path: Path, content_dir: Path) -> int:
    rendered = _render_from_csv(csv_path, content_dir)
    current = out_path.read_text(encoding="utf-8") if out_path.is_file() else ""
    if current == rendered:
        print(f"{out_path} is up to date")
        return 0

    diff = difflib.unified_diff(
        current.splitlines(keepends=True),
        rendered.splitlines(keepends=True),
        fromfile=f"{out_path} (committed)",
        tofile=f"{out_path} (from redirects.csv)",
    )
    sys.stdout.writelines(diff)
    print(f"\n{out_path} is stale - run `npm run redirects`", file=sys.stderr)
    return 1


def command_refresh(
    csv_path: Path,
    out_path: Path,
    content_dir: Path,
    sitemap_path: Path,
    exclusions_path: Path,
) -> int:
    csv_text = csv_path.read_text(encoding="utf-8") if csv_path.is_file() else ""
    existing = read_rows(csv_text) if csv_text.strip() else []
    annotations = read_annotations(csv_text) if csv_text.strip() else None
    sitemap_urls = parse_sitemap(sitemap_path.read_text(encoding="utf-8"))
    exclusions = (
        read_exclusions(exclusions_path.read_text(encoding="utf-8"))
        if exclusions_path.is_file()
        else set()
    )

    refresh = refresh_rows(existing, sitemap_urls, exclusions, content_dir)
    csv_path.write_text(write_rows(refresh.rows, annotations), encoding="utf-8")

    _report_refresh(existing, refresh)
    return command_build(csv_path, out_path, content_dir)


def _report_refresh(existing: list[Row], refresh: Refresh) -> None:
    counts = {source: 0 for source in VALID_SOURCES}
    for row in refresh.rows:
        counts[row.source] += 1
    summary = ", ".join(f"{counts[s]} {s}" for s in VALID_SOURCES if counts[s])
    print(f"refreshed redirects.csv: {len(refresh.rows)} rows ({summary})")

    before = {row.old_path: row for row in existing}
    after = {row.old_path: row for row in refresh.rows}
    for label, paths in (
        ("added", after.keys() - before.keys()),
        ("removed", before.keys() - after.keys()),
    ):
        if paths:
            print(f"  {label} {len(paths)}: {', '.join(sorted(paths))}")

    # Keying the diff on old_path alone would hide an edited target being
    # regenerated away, which is the likeliest way to lose a hand-made change.
    changed = sorted(
        old_path
        for old_path, row in after.items()
        if old_path in before and before[old_path] != row
    )
    for old_path in changed:
        was, now = before[old_path], after[old_path]
        print(
            f"  changed {old_path}: was -> {was.new_path} ({was.status}, {was.source}), "
            f"now -> {now.new_path} ({now.status}, {now.source})"
        )

    for label, paths in (
        ("ambiguous, two nested pages share the leaf name", refresh.dropped_ambiguous),
        ("collides with a real page", refresh.dropped_colliding),
        ("listed in alias_exclusions.txt", refresh.dropped_excluded),
    ):
        if paths:
            print(f"  alias dropped ({label}): {', '.join(sorted(paths))}")


def main_with_paths(
    argv: list[str] | None,
    csv_path: Path,
    out_path: Path,
    content_dir: Path,
    sitemap_path: Path,
    exclusions_path: Path,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check",
        action="store_true",
        help="fail if public/_redirects does not match redirects.csv",
    )
    mode.add_argument(
        "--refresh-csv",
        action="store_true",
        help="regenerate the sitemap, alias and structural rows from ref/",
    )
    args = parser.parse_args(argv)

    try:
        if args.check:
            return command_check(csv_path, out_path, content_dir)
        if args.refresh_csv:
            return command_refresh(
                csv_path, out_path, content_dir, sitemap_path, exclusions_path
            )
        return command_build(csv_path, out_path, content_dir)
    except RedirectError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    return main_with_paths(
        argv, CSV_PATH, REDIRECTS_PATH, CONTENT_DIR, SITEMAP_PATH, EXCLUSIONS_PATH
    )


if __name__ == "__main__":
    raise SystemExit(main())
