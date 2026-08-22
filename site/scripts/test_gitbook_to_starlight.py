"""Tests for the GitBook -> Starlight transformer.

Run from `site/`:

    npm test
    python3 -m unittest discover -s scripts -p 'test_*.py' -t scripts

The expectations here are taken from the real docs: every slug case is a heading
that exists in the corpus, checked against the id Starlight actually emitted for
it, and every link case is a reference shape that appears in the GitBook source.
"""

import contextlib
import io
import os
import pathlib
import tempfile
import textwrap
import unittest
from unittest import mock

import gitbook_to_starlight as G


def context(assets=None, pages=None):
    """A Conversion wired to fixtures instead of the repo."""
    ctx = G.Conversion(assets=assets or {})
    for url, body in (pages or {}).items():
        ctx.anchors[url] = G.page_anchors(body)
    return ctx


def silenced(call):
    """Run `call`, swallowing its console output. Returns what it returned."""
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return call()


def convert(source, relpath="docs/page.md", ctx=None):
    return G.convert(textwrap.dedent(source).lstrip("\n"), relpath, ctx or context())


class SlugTest(unittest.TestCase):
    def test_starlight_slug_matches_github_slugger(self):
        # Left: the heading as written. Right: the id in site/dist today.
        cases = {
            "Tool Use": "tool-use",
            "State & Memory": "state--memory",
            "Goal Directed, Autonomy, & Reasoning": "goal-directed-autonomy--reasoning",
            "Included Models from the Model Library - Recommended":
                "included-models-from-the-model-library---recommended",
            "Azure AI Foundry (formerly Azure AI Studio, Microsoft AI for Enterprise 360 Elite)":
                "azure-ai-foundry-formerly-azure-ai-studio-microsoft-ai-for-enterprise-360-elite",
            "Step 6 \\[Optional]: Training on your own Infrastructure":
                "step-6-optional-training-on-your-own-infrastructure",
            "What is the Kiln Eval Builder?&#x20;": "what-is-the-kiln-eval-builder-",
            "Philosophy: AI Product Evals work Best with Many Small Evals"
            ' <a href="#setup-team-evals" id="setup-team-evals"></a>':
                "philosophy-ai-product-evals-work-best-with-many-small-evals-",
        }
        for heading, expected in cases.items():
            with self.subTest(heading=heading):
                self.assertEqual(G.starlight_slug(G.heading_text(heading)), expected)

    def test_heading_text_strips_inline_markup(self):
        self.assertEqual(G.heading_text("**Kiln UI: For Personal Use**"),
                         "Kiln UI: For Personal Use")
        self.assertEqual(G.heading_text("Use `kiln_ai` in [code](developers/x.md)"),
                         "Use kiln_ai in code")

    def test_legacy_slugs_spell_ampersand_as_and(self):
        self.assertEqual(G.legacy_slugs("State & Memory"),
                         {"state--memory", "state-and-memory"})

    def test_repeated_heading_gets_numeric_suffix(self):
        slugs, _ = G.page_anchors("## Overview\n\n## Overview\n")
        self.assertEqual(slugs, {"overview", "overview-1"})

    def test_headings_inside_code_fences_are_not_anchors(self):
        slugs, _ = G.page_anchors("## Real\n\n```sh\n# Not a heading\n```\n")
        self.assertEqual(slugs, {"real"})

    def test_nested_fence_does_not_close_a_longer_block(self):
        body = "````md\n```sh\nls\n```\n\n## Fake\n````\n\n## Real\n"
        slugs, _ = G.page_anchors(body)
        self.assertEqual(slugs, {"real"})

    def test_closing_fence_must_match_the_opening_character(self):
        slugs, _ = G.page_anchors("~~~\n## Fake\n```\n## Still Fake\n~~~\n\n## Real\n")
        self.assertEqual(slugs, {"real"})

    def test_unclosed_fence_swallows_the_rest_of_the_page(self):
        text = "prose\n```sh\nls\n"
        self.assertEqual(G.code_regions(text), [(6, len(text))])

    def test_hand_written_anchor_ids_count_as_anchors(self):
        slugs, _ = G.page_anchors('### Philosophy <a id="setup-team-evals"></a>\n')
        self.assertIn("setup-team-evals", slugs)

    def test_lift_title_removes_the_h1_and_leaves_the_rest(self):
        title, body = G.lift_title("Intro\n\n# Prompt Generators\n\n### Prompt Generators\n")
        self.assertEqual(title, "Prompt Generators")
        self.assertEqual(G.headings(body), ["Prompt Generators"])
        self.assertIn("### Prompt Generators", body)
        self.assertIn("Intro", body)

    def test_lift_title_ignores_a_hash_inside_a_code_fence(self):
        title, _ = G.lift_title("```sh\n# install kiln\n```\n\n# Real Title\n")
        self.assertEqual(title, "Real Title")

    def test_h1_is_not_indexed_as_an_anchor(self):
        # Starlight gives the H1 id="_top", and the H3 below keeps the bare slug
        # rather than being pushed to prompt-generators-1.
        _, body = G.lift_title("# Prompt Generators\n\n### Prompt Generators\n")
        slugs, _ = G.page_anchors(body)
        self.assertEqual(slugs, {"prompt-generators"})


class AnchorRewriteTest(unittest.TestCase):
    AGENTS = "### Tool Use\n\n### State & Memory\n"

    def ctx(self):
        return context(pages={"/docs/agents/": self.AGENTS})

    def test_legacy_anchor_is_remapped(self):
        ctx = self.ctx()
        out = convert("# P\n\nSee [memory](agents.md#state-and-memory).\n", ctx=ctx)
        self.assertIn("(/docs/agents/#state--memory)", out)
        self.assertEqual(ctx.unresolved_anchors, [])

    def test_current_anchor_is_left_alone(self):
        out = convert("# P\n\nSee [memory](agents.md#state--memory).\n", ctx=self.ctx())
        self.assertIn("(/docs/agents/#state--memory)", out)

    def test_unknown_anchor_is_reported_but_not_rewritten(self):
        ctx = self.ctx()
        out = convert("# P\n\nSee [gone](agents.md#removed-heading) and\n"
                      "[gone again](agents.md#removed-heading).\n", ctx=ctx)
        self.assertIn("(/docs/agents/#removed-heading)", out)
        self.assertEqual(ctx.unresolved_anchors,
                         [("docs/page.md", "/docs/agents/#removed-heading")])

    def test_same_page_anchor_is_remapped(self):
        ctx = context(pages={"/docs/agents/": self.AGENTS})
        out = convert("# Agents\n\n" + self.AGENTS + "\n[jump](#state-and-memory)\n",
                      relpath="docs/agents.md", ctx=ctx)
        self.assertIn("(#state--memory)", out)


class LinkRewriteTest(unittest.TestCase):
    def test_html_anchor_href_to_md_is_rewritten(self):
        out = convert('# P\n\n<a href="prompts.md">Prompts</a>\n')
        self.assertIn('<a href="/docs/prompts/">', out)

    def test_html_anchor_href_to_directory_is_rewritten(self):
        out = convert('# P\n\n<a href="fine-tuning/">Fine Tuning</a>\n')
        self.assertIn('<a href="/docs/fine-tuning/">', out)

    def test_html_anchor_href_with_parent_segments_is_rewritten(self):
        out = convert('# P\n\n<a href="../../developers/rest-api.md">API</a>\n',
                      relpath="docs/evals-and-specs/page.md")
        self.assertIn('<a href="/developers/rest-api/">', out)

    def test_markdown_link_to_md_is_rewritten(self):
        self.assertIn("(/docs/prompts/)", convert("# P\n\n[Prompts](prompts.md)\n"))

    def test_external_and_absolute_targets_are_untouched(self):
        source = ("# P\n\n[a](https://kiln.tech) [b](mailto:x@y.z) [c](/docs/x/)\n"
                  '<a href="https://kiln.tech">d</a>\n')
        out = convert(source)
        for target in ("https://kiln.tech", "mailto:x@y.z", "/docs/x/"):
            self.assertIn(target, out)

    def test_link_to_missing_page_is_untouched(self):
        self.assertIn("(nowhere/)", convert("# P\n\n[x](nowhere/)\n"))

    def test_links_inside_code_fences_are_untouched(self):
        out = convert("# P\n\n```md\nSee our [style guide](references/STYLE_GUIDE.md).\n```\n")
        self.assertIn("[style guide](references/STYLE_GUIDE.md)", out)

    def test_links_inside_a_nested_fence_are_untouched(self):
        out = convert("# P\n\n````md\n```sh\nls\n```\n"
                      "See our [style guide](references/STYLE_GUIDE.md).\n````\n")
        self.assertIn("[style guide](references/STYLE_GUIDE.md)", out)


class AssetTest(unittest.TestCase):
    ASSETS = {
        "filter 2.png": "filter 2.png",
        "Screenshot 2025-01-05 at 12.18.52 PM (1).png":
            "Screenshot 2025-01-05 at 12.18.52 PM (1).png",
        # Stored with U+202F, referenced from markdown with a plain space.
        "Screenshot 2025-11-14 at 1.33.24 PM.png":
            "Screenshot 2025-11-14 at 1.33.24 PM.png",
    }

    def test_angle_bracket_asset_link(self):
        out = convert("# P\n\n![](<../.gitbook/assets/filter 2.png>)\n",
                      ctx=context(self.ASSETS))
        self.assertIn("![](/assets/filter%202.png)", out)

    def test_asset_filename_containing_parentheses(self):
        out = convert("# P\n\n![](<../.gitbook/assets/"
                      "Screenshot 2025-01-05 at 12.18.52 PM (1).png>)\n",
                      ctx=context(self.ASSETS))
        self.assertIn("Screenshot%202025-01-05%20at%2012.18.52%20PM%20%281%29.png", out)
        self.assertNotIn("%3E", out)

    def test_asset_name_whitespace_is_normalised_to_the_real_file(self):
        ctx = context(self.ASSETS)
        out = convert('# P\n\n<img src="../.gitbook/assets/'
                      'Screenshot 2025-11-14 at 1.33.24 PM.png">\n', ctx=ctx)
        self.assertIn("1.33.24%E2%80%AFPM.png", out)
        self.assertEqual(ctx.missing_assets, [])

    def test_missing_asset_is_reported(self):
        ctx = context(self.ASSETS)
        convert('# P\n\n<img src="../.gitbook/assets/nope.png">\n', ctx=ctx)
        self.assertEqual(ctx.missing_assets, [("docs/page.md", "nope.png")])

    def test_the_same_missing_asset_is_recorded_once(self):
        ctx = context(self.ASSETS)
        convert('# P\n\n<img src="../.gitbook/assets/nope.png">\n'
                '<img src="../.gitbook/assets/nope.png">\n', ctx=ctx)
        self.assertEqual(ctx.missing_assets, [("docs/page.md", "nope.png")])

    def test_report_raises_on_missing_asset(self):
        ctx = context()
        ctx.missing_assets.append(("docs/page.md", "nope.png"))
        with self.assertRaises(SystemExit):
            silenced(lambda: G.report(ctx))

    def test_report_tolerates_unresolved_anchors(self):
        ctx = context()
        ctx.unresolved_anchors.append(("docs/page.md", "/docs/x/#gone"))
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            G.report(ctx)
        self.assertIn("1 link(s) point at anchors", stderr.getvalue())
        self.assertNotIn("/docs/x/#gone", stderr.getvalue())

    def test_anchors_flag_lists_each_unresolved_anchor(self):
        ctx = context()
        ctx.unresolved_anchors.append(("docs/page.md", "/docs/x/#gone"))
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            G.report(ctx, list_anchors=True)
        self.assertIn("/docs/x/#gone", stderr.getvalue())


class FrontmatterTest(unittest.TestCase):
    def test_folded_block_description_is_joined(self):
        out = convert("""
            ---
            description: >-
              Know your Kiln Search tools find the right answer with RAG evals and
              synthetic Q&A data
            icon: list-check
            ---

            # Page
            """)
        self.assertIn('description: "Know your Kiln Search tools find the right answer '
                      'with RAG evals and synthetic Q&A data"', out)

    def test_literal_block_description_keeps_line_breaks(self):
        fields, _ = G.parse_frontmatter("---\ndescription: |\n  one\n  two\n---\n")
        self.assertEqual(fields["description"], "one\ntwo")

    def test_single_quoted_description_keeps_inner_quotes(self):
        out = convert("---\ndescription: '\"Teach the model, you will\" - ML Yoda'\n"
                      "---\n\n# Page\n")
        self.assertIn(r'description: "\"Teach the model, you will\" - ML Yoda"', out)

    def test_plain_description_is_passed_through(self):
        fields, body = G.parse_frontmatter("---\ndescription: Call Kiln over HTTP\n---\nbody\n")
        self.assertEqual(fields["description"], "Call Kiln over HTTP")
        self.assertEqual(body, "body\n")

    def test_page_without_description_omits_the_field(self):
        self.assertNotIn("description:", convert("# Keyboard Shortcuts\n\nBody\n"))


class TitleTest(unittest.TestCase):
    def test_title_unescapes_markdown(self):
        out = convert("# Evaluate RAG Accuracy: Q\\&A Evals\n\nBody\n")
        self.assertIn('title: "Evaluate RAG Accuracy: Q&A Evals"', out)

    def test_h1_is_lifted_out_of_the_body(self):
        out = convert("# Agents\n\nBody\n")
        self.assertNotIn("\n# Agents", out)
        self.assertIn("Body", out)

    def test_title_falls_back_to_the_filename(self):
        out = convert("Body with no heading\n", relpath="docs/keyboard-shortcuts.md")
        self.assertIn('title: "Keyboard Shortcuts"', out)


class HintTest(unittest.TestCase):
    def test_every_hint_style_maps_to_an_aside(self):
        for style, aside in G.HINTS.items():
            with self.subTest(style=style):
                out = convert('# P\n\n{%% hint style="%s" %%}\nText\n{%% endhint %%}\n' % style)
                self.assertIn(":::%s\nText\n:::" % aside, out)

    def test_unknown_hint_style_falls_back_to_note(self):
        out = convert('# P\n\n{% hint style="quote" %}\nText\n{% endhint %}\n')
        self.assertIn(":::note\nText\n:::", out)

    def test_code_directive_is_dropped_and_the_fence_survives(self):
        out = convert('# P\n\n{% code overflow="wrap" %}\n```sh\nls\n```\n{% endcode %}\n')
        self.assertNotIn("{%", out)
        self.assertIn("```sh\nls\n```", out)


class EmbedTest(unittest.TestCase):
    def test_captioned_embed_becomes_a_figure(self):
        out = convert('# P\n\n{% embed url="https://vimeo.com/1067948856" %}\n'
                      "Video walkthrough\n{% endembed %}\n")
        self.assertIn("<figure>", out)
        self.assertIn("<figcaption><p>Video walkthrough</p></figcaption></figure>", out)
        self.assertIn("player.vimeo.com/video/1067948856", out)

    def test_embed_caption_is_html_escaped(self):
        out = convert('# P\n\n{% embed url="https://vimeo.com/1" %}\n'
                      "Llama 3.2 1b & GPT 4o-mini\n{% endembed %}\n")
        self.assertIn("Llama 3.2 1b &amp; GPT 4o-mini", out)

    def test_captioned_youtube_embed_becomes_a_figure(self):
        out = convert('# P\n\n{% embed url="https://www.youtube.com/watch?v=qh0FIrLMrII" %}\n'
                      "Tools walkthrough\n{% endembed %}\n")
        self.assertIn("youtube.com/embed/qh0FIrLMrII", out)
        self.assertIn("<figcaption><p>Tools walkthrough</p></figcaption></figure>", out)

    def test_embed_without_endembed_has_no_figure(self):
        out = convert('# P\n\n{% embed url="https://www.youtube.com/watch?v=qh0FIrLMrII" %}\n'
                      "\nOrdinary prose that is not a caption.\n")
        self.assertNotIn("<figure>", out)
        self.assertIn("youtube.com/embed/qh0FIrLMrII", out)
        self.assertIn("Ordinary prose that is not a caption.", out)

    def test_bodyless_embed_has_no_empty_figcaption(self):
        # GitBook's shape for an uncaptioned video. It must not grow a caption.
        out = convert('# P\n\n{% embed url="https://vimeo.com/1" %}\n{% endembed %}\n')
        self.assertNotIn("<figcaption>", out)
        self.assertNotIn("<figure>", out)
        self.assertIn("player.vimeo.com/video/1", out)

    def test_gitbook_cdn_video_points_at_the_local_copy(self):
        url = ("https://files.gitbook.com/v0/b/gitbook-x-prod.appspot.com/o/"
               "spaces%2FA%2Fuploads%2FB%2FCreateTask720.mp4?alt=media&token=x")
        out = convert('# P\n\n{%% embed url="%s" %%}\nCreate a task\n{%% endembed %%}\n' % url)
        self.assertIn('<video controls playsinline', out)
        self.assertIn('src="/assets/CreateTask720.mp4"', out)
        self.assertIn("<figcaption><p>Create a task</p></figcaption>", out)


class ArgsTest(unittest.TestCase):
    def parse(self, argv):
        return silenced(lambda: G.parse_args(argv))

    def test_default_mode_writes_the_site(self):
        args = self.parse([])
        self.assertFalse(args.list)
        self.assertIsNone(args.out)
        self.assertFalse(args.anchors)

    def test_list_mode(self):
        self.assertTrue(self.parse(["--list"]).list)

    def test_out_returns_an_absolute_directory(self):
        self.assertEqual(self.parse(["--out", "scratch"]).out,
                         os.path.abspath("scratch"))

    def test_out_accepts_the_equals_spelling(self):
        self.assertEqual(self.parse(["--out=scratch"]).out, os.path.abspath("scratch"))

    def test_out_without_a_directory_is_an_error(self):
        with self.assertRaises(SystemExit):
            self.parse(["--out"])

    def test_unknown_arguments_are_rejected(self):
        # Never fall through to the default run: that one starts by deleting
        # src/content/docs, which is forbidden once content is hand-edited.
        for argv in (["--outt", "scratch"], ["garbage"], ["--out", "scratch", "--nope"]):
            with self.subTest(argv=argv), self.assertRaises(SystemExit):
                self.parse(argv)


class OutFlagTest(unittest.TestCase):
    """The safety property --out exists for: it must never delete anything."""

    def test_out_writes_pages_only_and_touches_nothing_else(self):
        sidebar = pathlib.Path(G.SITE, "sidebar.json")
        before = sidebar.stat().st_mtime_ns if sidebar.exists() else None

        with tempfile.TemporaryDirectory() as scratch:
            sentinel = pathlib.Path(scratch, "sentinel.txt")
            sentinel.write_text("keep me")
            with mock.patch.object(G.shutil, "rmtree") as rmtree, \
                    mock.patch.object(G.shutil, "copy") as copy, \
                    mock.patch.object(G.shutil, "copytree") as copytree:
                silenced(lambda: G.main(["--out", scratch]))

            rmtree.assert_not_called()
            copy.assert_not_called()
            copytree.assert_not_called()
            self.assertEqual(sentinel.read_text(), "keep me")
            self.assertEqual(len(list(pathlib.Path(scratch).rglob("*.md"))),
                             len(G.find_sources()))
            self.assertEqual(list(pathlib.Path(scratch).rglob("*.mdx")), [])

        after = sidebar.stat().st_mtime_ns if sidebar.exists() else None
        self.assertEqual(before, after)


class SidebarTest(unittest.TestCase):
    SUMMARY = textwrap.dedent("""
        # Table of contents

        * [Welcome](README.md)

        ## Docs

        * [Quickstart](docs/quickstart.md)
        * [Fine Tuning](docs/fine-tuning/README.md)
          * [Fine Tuning Guide](docs/fine-tuning/fine-tuning-guide.md)
        * [Evaluate RAG Accuracy: Q\\&A Evals](docs/evals-and-specs/rag.md)
        """).lstrip("\n")

    def setUp(self):
        self.groups = G.build_sidebar(self.SUMMARY)

    def test_url_for(self):
        self.assertEqual(G.url_for("README.md"), "/")
        self.assertEqual(G.url_for("docs/fine-tuning/README.md"), "/docs/fine-tuning/")
        self.assertEqual(G.url_for("docs/quickstart.md"), "/docs/quickstart/")

    def test_out_for(self):
        self.assertEqual(G.out_for("docs/fine-tuning/README.md"), "docs/fine-tuning/index.md")
        self.assertEqual(G.out_for("docs/quickstart.md"), "docs/quickstart.md")

    def test_group_heading_becomes_a_sidebar_group(self):
        self.assertEqual([g["label"] for g in self.groups], ["Docs"])

    def test_readme_is_not_a_sidebar_entry(self):
        self.assertNotIn("Welcome", [i["label"] for i in self.groups[0]["items"]])

    def test_labels_are_unescaped(self):
        labels = [i["label"] for i in self.groups[0]["items"]]
        self.assertIn("Evaluate RAG Accuracy: Q&A Evals", labels)

    def test_a_parent_page_becomes_an_overview_entry_in_its_own_group(self):
        parent = next(i for i in self.groups[0]["items"] if i["label"] == "Fine Tuning")
        self.assertTrue(parent["collapsed"])
        self.assertEqual(parent["items"][0], {"label": "Overview", "link": "/docs/fine-tuning/"})
        self.assertEqual(parent["items"][1]["link"], "/docs/fine-tuning/fine-tuning-guide/")


if __name__ == "__main__":
    unittest.main()
