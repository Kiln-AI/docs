"""Tests for the redirect builder.

Run from `site/`:

    npm test
    python3 -m unittest discover -s scripts -p 'test_*.py' -t scripts

The sitemap fixtures reproduce the two quirks of the real
`ref/legacy_sitemap.xml`: a browser's prose banner ahead of the XML, and `<loc>`
values wrapped across newlines.
"""

import contextlib
import io
import pathlib
import tempfile
import unittest

import build_redirects as B


HEADER = "old_path,new_path,status,source\n"


def csv_text(*rows):
    return HEADER + "".join(f"{','.join(str(field) for field in row)}\n" for row in rows)


def sitemap(*urls, banner=True):
    entries = "".join(f"<url><loc>{url}</loc></url>" for url in urls)
    prose = "This XML file does not appear to have any style information.\n" if banner else ""
    return (
        prose
        + '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + entries
        + "</urlset>"
    )


@contextlib.contextmanager
def content_tree(*page_paths):
    """A stand-in for `src/content/docs` holding just the named files."""
    with tempfile.TemporaryDirectory() as root:
        directory = pathlib.Path(root)
        for page_path in page_paths:
            target = directory / page_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("---\ntitle: x\n---\n", encoding="utf-8")
        yield directory


def rows_from(*specs):
    return [B.Row(*spec) for spec in specs]


class SitemapTest(unittest.TestCase):
    def test_collapses_loc_wrapped_across_newlines(self):
        text = sitemap("\nhttps://docs.kiln.tech/docs/a/b\n")
        self.assertEqual(B.parse_sitemap(text), ["https://docs.kiln.tech/docs/a/b"])

    def test_tolerates_browser_prose_banner(self):
        self.assertEqual(
            B.parse_sitemap(sitemap("https://docs.kiln.tech/docs/a")),
            ["https://docs.kiln.tech/docs/a"],
        )

    def test_parses_without_a_banner_too(self):
        self.assertEqual(
            B.parse_sitemap(sitemap("https://docs.kiln.tech/docs/a", banner=False)),
            ["https://docs.kiln.tech/docs/a"],
        )

    def test_dedupes_preserving_document_order(self):
        text = sitemap(
            "https://docs.kiln.tech/b",
            "https://docs.kiln.tech/a",
            "https://docs.kiln.tech/b",
        )
        self.assertEqual(
            B.parse_sitemap(text),
            ["https://docs.kiln.tech/b", "https://docs.kiln.tech/a"],
        )

    def test_rejects_a_sitemap_index(self):
        text = (
            '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            "<sitemap><loc>https://docs.kiln.tech/s1.xml</loc></sitemap></sitemapindex>"
        )
        with self.assertRaisesRegex(B.RedirectError, "sitemap index"):
            B.parse_sitemap(text)

    def test_rejects_text_with_no_sitemap_element(self):
        with self.assertRaisesRegex(B.RedirectError, "no <urlset>"):
            B.parse_sitemap("nothing to see here")

    def test_rejects_malformed_xml(self):
        with self.assertRaisesRegex(B.RedirectError, "well-formed"):
            B.parse_sitemap("<urlset><url><loc>x</loc>")

    def test_committed_sitemap_still_holds_46_urls(self):
        urls = B.parse_sitemap(B.SITEMAP_PATH.read_text(encoding="utf-8"))
        self.assertEqual(len(urls), 46)
        self.assertIn("https://docs.kiln.tech/docs/fine-tuning/fine-tuning-guide", urls)
        self.assertTrue(all(" " not in url for url in urls))


class CanonicalPathTest(unittest.TestCase):
    def test_strips_the_legacy_origin(self):
        self.assertEqual(
            B.canonical_path("https://docs.kiln.tech/docs/a"), "/docs/a"
        )

    def test_bare_origin_becomes_root(self):
        self.assertEqual(B.canonical_path("https://docs.kiln.tech"), "/")

    def test_collapses_wrapping_whitespace(self):
        self.assertEqual(
            B.canonical_path("\n https://docs.kiln.tech/docs/a \n"), "/docs/a"
        )

    def test_passes_a_bare_path_through(self):
        self.assertEqual(B.canonical_path("/docs/a/"), "/docs/a/")

    def test_rejects_a_foreign_origin(self):
        with self.assertRaisesRegex(B.RedirectError, "not on docs.kiln.tech"):
            B.canonical_path("https://example.com/docs/a")

    def test_rejects_a_path_without_a_leading_slash(self):
        with self.assertRaisesRegex(B.RedirectError, "must start with"):
            B.canonical_path("docs/a")

    def test_rejects_a_query_string(self):
        with self.assertRaisesRegex(B.RedirectError, "query or fragment"):
            B.canonical_path("/docs/a?utm_source=x")

    def test_rejects_a_fragment_on_an_absolute_url(self):
        with self.assertRaisesRegex(B.RedirectError, "query or fragment"):
            B.canonical_path("https://docs.kiln.tech/docs/a#heading")

    def test_rejects_a_protocol_relative_path(self):
        with self.assertRaisesRegex(B.RedirectError, "not a normalised path"):
            B.canonical_path("//evil.com/x")

    def test_rejects_a_doubled_slash(self):
        with self.assertRaisesRegex(B.RedirectError, "not a normalised path"):
            B.canonical_path("/a//b")

    def test_rejects_dot_segments(self):
        with self.assertRaisesRegex(B.RedirectError, "not a normalised path"):
            B.canonical_path("/a/../b")

    def test_rejects_an_empty_value(self):
        with self.assertRaisesRegex(B.RedirectError, "empty path"):
            B.canonical_path("   ")


class FlatAliasTest(unittest.TestCase):
    def test_three_segment_path_yields_both_slash_forms(self):
        self.assertEqual(
            B.flat_alias_paths("/docs/fine-tuning/fine-tuning-guide"),
            ["/docs/fine-tuning-guide", "/docs/fine-tuning-guide/"],
        )

    def test_two_segment_path_has_no_alias(self):
        self.assertEqual(B.flat_alias_paths("/docs/quickstart"), [])

    def test_root_has_no_alias(self):
        self.assertEqual(B.flat_alias_paths("/"), [])

    def test_four_segment_path_drops_every_middle_segment(self):
        self.assertEqual(
            B.flat_alias_paths("/docs/a/b/c"), ["/docs/c", "/docs/c/"]
        )

    def test_trailing_slash_on_the_nested_path_is_ignored(self):
        self.assertEqual(
            B.flat_alias_paths("/docs/a/b/"), ["/docs/b", "/docs/b/"]
        )


class ExclusionsTest(unittest.TestCase):
    def test_one_entry_covers_both_slash_forms(self):
        excluded = B.read_exclusions("/docs/a\n")
        self.assertIn("/docs/a", excluded)
        self.assertIn("/docs/a/", excluded)

    def test_ignores_comments_and_blank_lines(self):
        self.assertEqual(B.read_exclusions("# note\n\n   \n"), set())

    def test_strips_a_trailing_comment(self):
        self.assertIn("/docs/a", B.read_exclusions("/docs/a  # probe says 404\n"))


class ReadRowsTest(unittest.TestCase):
    def test_parses_a_row(self):
        rows = B.read_rows(csv_text(("/a", "/a/", 301, "sitemap")))
        self.assertEqual(rows, [B.Row("/a", "/a/", 301, "sitemap")])

    def test_skips_comment_and_blank_lines(self):
        text = HEADER + "# a note\n\n/a,/a/,301,sitemap\n"
        self.assertEqual(len(B.read_rows(text)), 1)

    def test_rejects_a_wrong_header(self):
        with self.assertRaisesRegex(B.RedirectError, "header must be"):
            B.read_rows("from,to\n/a,/b\n")

    def test_rejects_an_empty_file(self):
        with self.assertRaisesRegex(B.RedirectError, "empty"):
            B.read_rows("")

    def test_rejects_a_missing_column(self):
        with self.assertRaisesRegex(B.RedirectError, "line 2: expected 4 columns"):
            B.read_rows(HEADER + "/a,/a/,301\n")

    def test_rejects_a_non_numeric_status(self):
        with self.assertRaisesRegex(B.RedirectError, "not a number"):
            B.read_rows(csv_text(("/a", "/a/", "perm", "sitemap")))

    def test_rejects_an_unsupported_status(self):
        with self.assertRaisesRegex(B.RedirectError, "status 307"):
            B.read_rows(csv_text(("/a", "/a/", 307, "sitemap")))

    def test_rejects_an_unknown_source(self):
        with self.assertRaisesRegex(B.RedirectError, "source 'guess'"):
            B.read_rows(csv_text(("/a", "/a/", 301, "guess")))

    def test_line_numbers_count_comment_lines(self):
        text = HEADER + "# a note\n# another\n/a,/a/,301,bogus\n"
        with self.assertRaisesRegex(B.RedirectError, "line 4"):
            B.read_rows(text)

    def test_reports_the_line_number_of_a_bad_path(self):
        text = csv_text(("/a", "/a/", 301, "sitemap"), ("b", "/b/", 301, "sitemap"))
        with self.assertRaisesRegex(B.RedirectError, "line 3"):
            B.read_rows(text)

    def test_round_trips_through_write_rows(self):
        rows = rows_from(("/a", "/a/", 301, "sitemap"), ("/b", "/b/", 301, "manual"))
        self.assertEqual(B.read_rows(B.write_rows(rows)), rows)


class AnnotationTest(unittest.TestCase):
    ANNOTATED = (
        "# what this file is\n"
        + HEADER
        + "# why this row exists\n"
        + "/a,/a/,301,manual\n"
        + "/b,/b/,301,manual\n"
        + "# a parting thought\n"
    )

    def test_ties_each_comment_to_the_row_below_it(self):
        annotations = B.read_annotations(self.ANNOTATED)
        self.assertEqual(annotations.header, ["# what this file is"])
        self.assertEqual(annotations.by_old_path["/a"], ["# why this row exists"])
        self.assertEqual(annotations.by_old_path["/b"], [])
        self.assertEqual(annotations.trailing, ["# a parting thought"])

    def test_comments_follow_their_row_when_rows_are_reordered(self):
        annotations = B.read_annotations(self.ANNOTATED)
        rows = list(reversed(B.read_rows(self.ANNOTATED)))
        rewritten = B.write_rows(rows, annotations).splitlines()
        self.assertEqual(rewritten.index("# why this row exists") + 1,
                         rewritten.index("/a,/a/,301,manual"))

    def test_write_rows_without_annotations_is_unchanged(self):
        rows = rows_from(("/a", "/a/", 301, "manual"))
        self.assertEqual(B.write_rows(rows), HEADER + "/a,/a/,301,manual\n")


class SlashVariantTest(unittest.TestCase):
    def test_both_slash_forms_may_share_a_target(self):
        rows = rows_from(("/a", "/x/", 301, "manual"), ("/a/", "/x/", 301, "manual"))
        B.check_slash_variants(rows)

    def test_slash_forms_pointing_at_different_places_raise(self):
        rows = rows_from(("/a", "/x/", 301, "manual"), ("/a/", "/y/", 301, "manual"))
        with self.assertRaisesRegex(B.RedirectError, "same URL but go to different"):
            B.check_slash_variants(rows)

    def test_root_has_no_sibling_to_conflict_with(self):
        B.check_slash_variants(rows_from(("/", "/x/", 301, "manual")))


class DedupeTest(unittest.TestCase):
    def test_identical_duplicates_collapse(self):
        rows = rows_from(("/a", "/b/", 301, "sitemap"), ("/a", "/b/", 301, "gsc"))
        self.assertEqual(B.dedupe(rows), [B.Row("/a", "/b/", 301, "sitemap")])

    def test_conflicting_targets_raise_and_name_both(self):
        rows = rows_from(("/a", "/b/", 301, "sitemap"), ("/a", "/c/", 301, "gsc"))
        with self.assertRaises(B.RedirectError) as caught:
            B.dedupe(rows)
        message = str(caught.exception)
        self.assertIn("/a", message)
        self.assertIn("/b/", message)
        self.assertIn("/c/", message)

    def test_conflicting_statuses_raise(self):
        rows = rows_from(("/a", "/b/", 301, "sitemap"), ("/a", "/b/", 302, "manual"))
        with self.assertRaises(B.RedirectError):
            B.dedupe(rows)

    def test_unrelated_rows_keep_their_order(self):
        rows = rows_from(("/b", "/b/", 301, "sitemap"), ("/a", "/a/", 301, "sitemap"))
        self.assertEqual([row.old_path for row in B.dedupe(rows)], ["/b", "/a"])


class FlattenTest(unittest.TestCase):
    def test_two_hop_chain_collapses(self):
        rows = rows_from(("/a", "/b", 301, "gsc"), ("/b", "/c/", 301, "sitemap"))
        self.assertEqual(
            B.flatten_chains(rows),
            rows_from(("/a", "/c/", 301, "gsc"), ("/b", "/c/", 301, "sitemap")),
        )

    def test_three_hop_chain_collapses(self):
        rows = rows_from(
            ("/a", "/b", 301, "gsc"),
            ("/b", "/c", 301, "gsc"),
            ("/c", "/d/", 301, "sitemap"),
        )
        self.assertEqual([row.new_path for row in B.flatten_chains(rows)], ["/d/"] * 3)

    def test_leaves_unrelated_rows_alone(self):
        rows = rows_from(("/a", "/x/", 301, "sitemap"), ("/b", "/y/", 301, "sitemap"))
        self.assertEqual(B.flatten_chains(rows), rows)

    def test_direct_cycle_raises(self):
        rows = rows_from(("/a", "/b", 301, "manual"), ("/b", "/a", 301, "manual"))
        with self.assertRaisesRegex(B.RedirectError, "cycle"):
            B.flatten_chains(rows)

    def test_longer_cycle_raises(self):
        rows = rows_from(
            ("/a", "/b", 301, "manual"),
            ("/b", "/c", 301, "manual"),
            ("/c", "/a", 301, "manual"),
        )
        with self.assertRaisesRegex(B.RedirectError, "cycle"):
            B.flatten_chains(rows)


class BuildRulesTest(unittest.TestCase):
    def test_self_redirect_is_dropped(self):
        rows = rows_from(("/", "/", 301, "sitemap"), ("/a", "/a/", 301, "sitemap"))
        with content_tree("index.md", "a.md") as tree:
            rules = B.build_rules(rows, tree)
        self.assertEqual([rule.old_path for rule in rules], ["/a"])

    def test_target_must_exist_in_the_content_tree(self):
        rows = rows_from(("/a", "/ghost/", 301, "manual"))
        with content_tree("index.md") as tree:
            with self.assertRaisesRegex(B.RedirectError, "/ghost/"):
                B.build_rules(rows, tree)

    def test_target_resolves_through_an_index_file(self):
        rows = rows_from(("/docs/a", "/docs/a/", 301, "sitemap"))
        with content_tree("docs/a/index.mdx") as tree:
            self.assertEqual(len(B.build_rules(rows, tree)), 1)

    def test_target_resolves_through_a_flat_file(self):
        rows = rows_from(("/docs/a", "/docs/a/", 301, "sitemap"))
        with content_tree("docs/a.md") as tree:
            self.assertEqual(len(B.build_rules(rows, tree)), 1)

    def test_rule_cap_is_enforced(self):
        rows = rows_from(*(
            (f"/p{index}", "/a/", 301, "sitemap") for index in range(B.MAX_RULES + 1)
        ))
        with content_tree("a.md") as tree:
            with self.assertRaisesRegex(B.RedirectError, "exceeds the Cloudflare"):
                B.build_rules(rows, tree)

    def test_target_validation_can_be_skipped(self):
        rows = rows_from(("/a", "/ghost/", 301, "manual"))
        self.assertEqual(len(B.build_rules(rows, content_dir=None)), 1)


class RenderTest(unittest.TestCase):
    def test_emits_one_rule_per_line(self):
        rendered = B.render_redirects(rows_from(("/a", "/a/", 301, "sitemap")), 1)
        self.assertIn("/a /a/ 301", rendered.splitlines())

    def test_groups_by_source_with_a_comment_per_group(self):
        rules = rows_from(
            ("/a", "/a/", 301, "sitemap"),
            ("/b", "/x/", 301, "alias-generated"),
        )
        rendered = B.render_redirects(rules, 2)
        self.assertIn("# sitemap: 1 rules - verbatim from ref/legacy_sitemap.xml", rendered)
        self.assertIn("NOT probe-confirmed", rendered)

    def test_header_records_rule_and_row_counts(self):
        rendered = B.render_redirects(rows_from(("/a", "/a/", 301, "sitemap")), 4)
        self.assertIn("# 1 rules from 4 inventory rows.", rendered)

    def test_omits_groups_with_no_rules(self):
        rendered = B.render_redirects(rows_from(("/a", "/a/", 301, "sitemap")), 1)
        self.assertNotIn("# manual:", rendered)


class RefreshTest(unittest.TestCase):
    SITEMAP = [
        "https://docs.kiln.tech",
        "https://docs.kiln.tech/docs/quickstart",
        "https://docs.kiln.tech/docs/fine-tuning/fine-tuning-guide",
    ]
    PAGES = ("index.md", "docs/quickstart.md", "docs/fine-tuning/fine-tuning-guide.md")

    def refresh(self, existing=(), exclusions=frozenset(), pages=None, sitemap_urls=None):
        with content_tree(*(pages or self.PAGES)) as tree:
            return B.refresh_rows(
                list(existing),
                list(sitemap_urls or self.SITEMAP),
                set(exclusions),
                tree,
            )

    def test_generates_sitemap_alias_and_structural_rows(self):
        result = self.refresh()
        by_source = {}
        for row in result.rows:
            by_source.setdefault(row.source, []).append(row)
        self.assertEqual(len(by_source["sitemap"]), 3)
        self.assertEqual(len(by_source["alias-generated"]), 2)
        self.assertEqual(len(by_source["structural"]), len(B.STRUCTURAL_REDIRECTS))

    def test_root_keeps_its_no_op_row(self):
        self.assertIn(B.Row("/", "/", 301, "sitemap"), self.refresh().rows)

    def test_alias_points_at_the_nested_page(self):
        self.assertIn(
            B.Row("/docs/fine-tuning-guide", "/docs/fine-tuning/fine-tuning-guide/", 301,
                  "alias-generated"),
            self.refresh().rows,
        )

    def test_preserves_human_rows_verbatim(self):
        human = B.Row("/docs/old-name", "/docs/quickstart/", 301, "gsc")
        self.assertIn(human, self.refresh(existing=[human]).rows)

    def test_drops_stale_generated_rows(self):
        stale = B.Row("/docs/gone", "/docs/quickstart/", 301, "sitemap")
        self.assertNotIn(stale, self.refresh(existing=[stale]).rows)

    def test_does_not_regenerate_over_a_preserved_old_path(self):
        promoted = B.Row(
            "/docs/fine-tuning-guide", "/docs/fine-tuning/fine-tuning-guide/", 301, "alias"
        )
        rows = self.refresh(existing=[promoted]).rows
        claiming = [row for row in rows if row.old_path == "/docs/fine-tuning-guide"]
        self.assertEqual(claiming, [promoted])

    def test_honours_alias_exclusions(self):
        result = self.refresh(exclusions=B.read_exclusions("/docs/fine-tuning-guide"))
        self.assertEqual([row for row in result.rows if row.source == "alias-generated"], [])
        self.assertIn("/docs/fine-tuning-guide", result.dropped_excluded)

    def test_drops_an_alias_that_collides_with_a_real_page(self):
        result = self.refresh(pages=self.PAGES + ("docs/fine-tuning-guide.md",))
        self.assertEqual([row for row in result.rows if row.source == "alias-generated"], [])
        self.assertIn("/docs/fine-tuning-guide", result.dropped_colliding)

    def test_drops_an_alias_two_nested_pages_would_both_claim(self):
        result = self.refresh(
            sitemap_urls=self.SITEMAP + ["https://docs.kiln.tech/docs/other/fine-tuning-guide"],
            pages=self.PAGES + ("docs/other/fine-tuning-guide.md",),
        )
        self.assertEqual([row for row in result.rows if row.source == "alias-generated"], [])
        self.assertIn("/docs/fine-tuning-guide", result.dropped_ambiguous)

    def test_is_idempotent(self):
        first = self.refresh().rows
        self.assertEqual(self.refresh(existing=first).rows, first)


class CommandTest(unittest.TestCase):
    """The three CLI modes, wired to a scratch directory instead of the repo."""

    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        root = pathlib.Path(self.scratch.name)
        self.csv_path = root / "redirects.csv"
        self.out_path = root / "public" / "_redirects"
        self.content = root / "content"
        pages = RefreshTest.PAGES + ("developers/python-library-quickstart.md",)
        for page in pages:
            target = self.content / page
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("---\ntitle: x\n---\n", encoding="utf-8")
        self.sitemap_path = root / "legacy_sitemap.xml"
        self.sitemap_path.write_text(sitemap(*RefreshTest.SITEMAP), encoding="utf-8")
        self.exclusions_path = root / "alias_exclusions.txt"

    def run_quietly(self, call):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = call()
        return code, stdout.getvalue(), stderr.getvalue()

    def refresh(self):
        return self.run_quietly(lambda: B.command_refresh(
            self.csv_path, self.out_path, self.content,
            self.sitemap_path, self.exclusions_path,
        ))

    def test_refresh_writes_both_files(self):
        code, out, _ = self.refresh()
        self.assertEqual(code, 0)
        self.assertIn("refreshed redirects.csv", out)
        self.assertTrue(self.csv_path.is_file())
        self.assertIn("/docs/quickstart /docs/quickstart/ 301", self.out_path.read_text())

    def test_check_passes_on_fresh_output(self):
        self.refresh()
        code, out, _ = self.run_quietly(
            lambda: B.command_check(self.csv_path, self.out_path, self.content)
        )
        self.assertEqual(code, 0)
        self.assertIn("up to date", out)

    def test_check_detects_stale_output(self):
        self.refresh()
        self.out_path.write_text("# hand-edited\n", encoding="utf-8")
        code, out, err = self.run_quietly(
            lambda: B.command_check(self.csv_path, self.out_path, self.content)
        )
        self.assertEqual(code, 1)
        self.assertIn("stale", err)
        self.assertIn("/docs/quickstart", out)

    def test_check_detects_a_missing_output_file(self):
        self.refresh()
        self.out_path.unlink()
        code, _, _ = self.run_quietly(
            lambda: B.command_check(self.csv_path, self.out_path, self.content)
        )
        self.assertEqual(code, 1)

    def test_build_refuses_an_inventory_with_no_rows(self):
        self.csv_path.write_text(HEADER, encoding="utf-8")
        code, _, err = self.run_quietly(
            lambda: B.main_with_paths(
                [], self.csv_path, self.out_path, self.content,
                self.sitemap_path, self.exclusions_path,
            )
        )
        self.assertEqual(code, 1)
        self.assertIn("refusing to write an empty rule set", err)

    def test_refresh_repopulates_an_empty_inventory(self):
        self.csv_path.write_text(HEADER, encoding="utf-8")
        code, _, _ = self.refresh()
        self.assertEqual(code, 0)
        self.assertTrue(B.read_rows(self.csv_path.read_text(encoding="utf-8")))

    def test_refresh_keeps_a_comment_attached_to_a_preserved_row(self):
        self.refresh()
        annotated = self.csv_path.read_text(encoding="utf-8").rstrip("\n")
        annotated += "\n# found in Search Console\n/docs/old,/docs/quickstart/,301,gsc\n"
        self.csv_path.write_text(annotated, encoding="utf-8")
        self.refresh()
        lines = self.csv_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines.index("# found in Search Console") + 1,
                         lines.index("/docs/old,/docs/quickstart/,301,gsc"))

    def test_refresh_reports_a_reverted_target(self):
        self.refresh()
        rows = B.read_rows(self.csv_path.read_text(encoding="utf-8"))
        edited = [
            row._replace(new_path="/docs/fine-tuning/fine-tuning-guide/")
            if row.old_path == "/docs/quickstart" else row
            for row in rows
        ]
        self.csv_path.write_text(B.write_rows(edited), encoding="utf-8")
        _, out, _ = self.refresh()
        self.assertIn("changed /docs/quickstart", out)

    def test_build_reports_a_missing_csv(self):
        code, _, err = self.run_quietly(
            lambda: B.main_with_paths(
                [], self.csv_path, self.out_path, self.content,
                self.sitemap_path, self.exclusions_path,
            )
        )
        self.assertEqual(code, 1)
        self.assertIn("does not exist", err)

    def test_refresh_reports_dropped_aliases(self):
        self.exclusions_path.write_text("/docs/fine-tuning-guide\n", encoding="utf-8")
        _, out, _ = self.refresh()
        self.assertIn("alias_exclusions.txt", out)

    def test_refresh_reports_added_and_removed_paths(self):
        self.refresh()
        rows = B.read_rows(self.csv_path.read_text(encoding="utf-8"))
        kept = [row for row in rows if row.old_path != "/docs/quickstart"]
        kept.append(B.Row("/docs/handmade", "/docs/quickstart/", 301, "manual"))
        self.csv_path.write_text(B.write_rows(kept), encoding="utf-8")
        _, out, _ = self.refresh()
        self.assertIn("added 1: /docs/quickstart", out)
        self.assertNotIn("removed", out)


class RepoStateTest(unittest.TestCase):
    """The committed artifacts, checked as they will actually be deployed."""

    def test_committed_redirects_match_the_committed_csv(self):
        rows = B.read_rows(B.CSV_PATH.read_text(encoding="utf-8"))
        rendered = B.render_redirects(B.build_rules(rows, B.CONTENT_DIR), len(rows))
        self.assertEqual(B.REDIRECTS_PATH.read_text(encoding="utf-8"), rendered)

    def test_every_sitemap_url_has_a_row(self):
        rows = B.read_rows(B.CSV_PATH.read_text(encoding="utf-8"))
        covered = {row.old_path for row in rows}
        missing = [
            path
            for path in (
                B.canonical_path(url)
                for url in B.parse_sitemap(B.SITEMAP_PATH.read_text(encoding="utf-8"))
            )
            if path not in covered
        ]
        self.assertEqual(missing, [])

    def test_every_content_page_is_a_redirect_target(self):
        """No page is reachable only at a URL nothing redirects to."""
        rows = B.read_rows(B.CSV_PATH.read_text(encoding="utf-8"))
        targets = {row.new_path for row in rows}
        for page in sorted(B.CONTENT_DIR.rglob("*.md*")):
            stem = page.relative_to(B.CONTENT_DIR).with_suffix("").as_posix()
            stem = "" if stem == "index" else stem.removesuffix("/index")
            self.assertIn(B.with_trailing_slash(f"/{stem}"), targets, page)

    def test_generated_aliases_are_marked_unverified(self):
        """While any inferred alias ships, the deployed file must say so.

        Once the phase 1 probe settles all 34 — each promoted to `alias` or
        excluded — the group disappears and there is nothing left to disclaim.
        """
        rows = B.read_rows(B.CSV_PATH.read_text(encoding="utf-8"))
        if not any(row.source == "alias-generated" for row in rows):
            self.skipTest("no alias-generated rows left; the probe has settled them")
        self.assertIn("NOT probe-confirmed", B.REDIRECTS_PATH.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
