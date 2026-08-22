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
import shutil
import tempfile
import textwrap
import unittest
from unittest import mock

import gitbook_to_starlight as G


def context(assets=None, pages=None):
    """A Conversion wired to fixtures instead of the repo."""
    ctx = G.Conversion((), assets or {})
    for url, body in (pages or {}).items():
        ctx.anchors[url] = G.page_anchors(body)
    return ctx


@contextlib.contextmanager
def fake_repo():
    """A miniature GitBook repo, with the module pointed at it.

    The safety tests run `main()` for real, so they must not depend on the live
    corpus or on `.git` being present -- the second is the very condition that
    disables the guard some of them cover.
    """
    with tempfile.TemporaryDirectory() as root:
        repo = pathlib.Path(root, "repo")
        (repo / "docs" / "fine-tuning").mkdir(parents=True)
        (repo / ".gitbook" / "assets").mkdir(parents=True)
        for name in ("shot.png", "wide shot.png", "clip.mp4", "orphan.png"):
            (repo / ".gitbook" / "assets" / name).write_bytes(b"bytes")
        (repo / "docs" / "one.md").write_text(
            "---\ndescription: First\n---\n\n# One\n\n"
            "![](../.gitbook/assets/shot.png)\n\n"
            "![](<../.gitbook/assets/wide shot.png>)\n\n"
            '<video src="../.gitbook/assets/clip.mp4"></video>\n\n'
            "[two](fine-tuning/two.md)\n")
        (repo / "docs" / "fine-tuning" / "two.md").write_text("# Two\n\nBody\n")
        (repo / "SUMMARY.md").write_text(
            "## Docs\n\n* [One](docs/one.md)\n* [Two](docs/fine-tuning/two.md)\n")
        site = repo / "site"
        (site / "src").mkdir(parents=True)

        with mock.patch.multiple(
            G,
            REPO=str(repo),
            SITE=str(site),
            DOCS_OUT=str(site / "src" / "content" / "docs"),
            ASSETS_OUT=str(site / "public" / "assets"),
            SRC_ASSETS=str(site / "src" / "assets"),
            GITBOOK_ASSETS=str(repo / ".gitbook" / "assets"),
            HERO_SOURCE="shot.png",
        ):
            yield repo


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

    def test_ids_inside_code_fences_are_not_anchors(self):
        # The corpus documents HTML in fences; an id in a sample is not an anchor.
        slugs, _ = G.page_anchors('## Real\n\n```html\n<a id="sample"></a>\n```\n')
        self.assertEqual(slugs, {"real"})

    def test_derived_duplicate_slug_is_itself_registered(self):
        # github-slugger records the suffixed slug too, so a literal "Overview 1"
        # cannot collide with the overview-1 minted for a second "Overview".
        slugs, _ = G.page_anchors("## Overview\n\n## Overview\n\n## Overview 1\n")
        self.assertEqual(slugs, {"overview", "overview-1", "overview-1-1"})

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
        # Directory targets resolve against the repo on disk, so this one needs a
        # repo -- a fixture one, not whatever happens to exist in the checkout.
        with fake_repo():
            out = convert('# P\n\n<a href="fine-tuning/">Fine Tuning</a>\n')
        self.assertIn('<a href="/docs/fine-tuning/">', out)

    def test_html_anchor_href_to_a_missing_directory_is_untouched(self):
        with fake_repo():
            out = convert('# P\n\n<a href="no-such-section/">Nope</a>\n')
        self.assertIn('<a href="no-such-section/">', out)

    def test_external_url_containing_the_asset_path_is_not_localised(self):
        # An absolute URL that happens to contain ".gitbook/assets/" belongs to
        # someone else's site; localising it would raise a fatal missing asset.
        ctx = context()
        out = convert('# P\n\n[x](https://other.example/.gitbook/assets/a.png)\n', ctx=ctx)
        self.assertIn("https://other.example/.gitbook/assets/a.png", out)
        self.assertEqual(ctx.missing_assets, [])

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
        self.assertIn("![](../../../assets/filter-2.png)", out)
        self.assertNotIn(">", out.split("---\n")[-1])

    def test_asset_filename_containing_parentheses(self):
        out = convert("# P\n\n![](<../.gitbook/assets/"
                      "Screenshot 2025-01-05 at 12.18.52 PM (1).png>)\n",
                      ctx=context(self.ASSETS))
        self.assertIn("../../../assets/Screenshot-2025-01-05-at-12.18.52-PM-1.png", out)
        self.assertNotIn("%3E", out)

    def test_markdown_image_points_into_src_assets(self):
        ctx = context(self.ASSETS)
        convert("# P\n\n![](<../.gitbook/assets/filter 2.png>)\n", ctx=ctx)
        self.assertEqual(ctx.image_assets, {"filter 2.png"})
        self.assertEqual(ctx.public_assets, set())

    def test_html_img_src_stays_in_public_assets(self):
        # Astro rewrites markdown image nodes and nothing else, so a raw <img>
        # cannot use a relative src/assets path.
        ctx = context(self.ASSETS)
        out = convert('# P\n\n<img src="../.gitbook/assets/filter 2.png">\n', ctx=ctx)
        self.assertIn('src="/assets/filter%202.png"', out)
        self.assertEqual(ctx.public_assets, {"filter 2.png"})
        self.assertEqual(ctx.image_assets, set())

    def test_markdown_link_to_an_asset_stays_in_public_assets(self):
        ctx = context(self.ASSETS)
        out = convert("# P\n\n[the shot](<../.gitbook/assets/filter 2.png>)\n", ctx=ctx)
        self.assertIn("](/assets/filter%202.png)", out)
        self.assertEqual(ctx.public_assets, {"filter 2.png"})

    def test_nested_image_link_rewrites_both_destinations(self):
        # [![alt](image)](page.md): the inner target is an image, the outer is
        # not, and folding the "!" into MD_LINK would stop matching the outer.
        ctx = context(self.ASSETS, {"/docs/two/": "# Two\n"})
        out = convert("# P\n\n[![shot](<../.gitbook/assets/filter 2.png>)](two.md)\n",
                      ctx=ctx)
        self.assertIn("[![shot](../../../assets/filter-2.png)](/docs/two/)", out)
        self.assertEqual(ctx.image_assets, {"filter 2.png"})
        self.assertEqual(ctx.public_assets, set())

    def test_missing_asset_is_still_fatal_for_a_markdown_image(self):
        ctx = context(self.ASSETS)
        convert("# P\n\n![](../.gitbook/assets/nope.png)\n", ctx=ctx)
        self.assertEqual(ctx.missing_assets, [("docs/page.md", "nope.png")])

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


class AssetNameTest(unittest.TestCase):
    """Astro resolves a markdown image path literally, so spaces are fatal."""

    def test_unsafe_runs_become_single_hyphens(self):
        self.assertEqual(
            G.safe_asset_name("Screenshot 2025-01-05 at 12.18.52 PM (1).png"),
            "Screenshot-2025-01-05-at-12.18.52-PM-1.png")

    def test_narrow_no_break_space_is_folded_too(self):
        self.assertEqual(
            G.safe_asset_name("Screenshot 2025-11-14 at 1.33.24 PM.png"),
            "Screenshot-2025-11-14-at-1.33.24-PM.png")

    def test_a_clean_name_is_left_alone(self):
        # 22 of the 68 images in src/assets are already safe; they must not churn.
        for name in ("Agents-2.png", "synth_data-2.png", "eval_header.png"):
            self.assertEqual(G.safe_asset_name(name), name)

    def test_extension_is_lowercased(self):
        self.assertEqual(G.safe_asset_name("CreateTask720.MP4"), "CreateTask720.mp4")

    def test_near_collisions_stay_distinct(self):
        self.assertNotEqual(G.safe_asset_name("synth_data-2 (1).png"),
                            G.safe_asset_name("synth_data-2 (2).png"))

    def test_src_asset_path_counts_the_page_depth(self):
        # site/src/content/docs/<page> -> site/src/assets/<name>
        self.assertEqual(G.src_asset_path("a.png", "top.md"), "../../assets/a.png")
        self.assertEqual(G.src_asset_path("a.png", "docs/page.md"),
                         "../../../assets/a.png")
        self.assertEqual(G.src_asset_path("a.png", "docs/group/deep.md"),
                         "../../../../assets/a.png")

    def test_src_asset_path_follows_readme_to_index(self):
        # docs/group/README.md is written as docs/group/index.md, one level in.
        self.assertEqual(G.src_asset_path("a.png", "docs/group/README.md"),
                         "../../../../assets/a.png")


class FigureTest(unittest.TestCase):
    ASSETS = {"shot.png": "shot.png", "wide shot.png": "wide shot.png"}

    def figure(self, source, ctx=None):
        return convert("# P\n\n" + source + "\n", ctx=ctx or context(self.ASSETS))

    def test_figure_becomes_a_markdown_image(self):
        out = self.figure('<figure><img src="../.gitbook/assets/shot.png" alt="">'
                          "<figcaption></figcaption></figure>")
        self.assertIn("<figure>\n\n![](../../../assets/shot.png)\n\n</figure>", out)
        self.assertNotIn("<img", out)

    def test_width_moves_onto_the_figure_as_css(self):
        out = self.figure('<figure><img src="../.gitbook/assets/shot.png" alt="" '
                          'width="375"><figcaption></figcaption></figure>')
        self.assertIn('<figure style="max-width:375px">', out)
        self.assertNotIn("width=", out)

    def test_caption_is_preserved(self):
        out = self.figure('<figure><img src="../.gitbook/assets/shot.png" alt="">'
                          "<figcaption><p>Rating UI</p></figcaption></figure>")
        self.assertIn("<figcaption><p>Rating UI</p></figcaption>\n</figure>", out)

    def test_empty_caption_leaves_no_figcaption(self):
        out = self.figure('<figure><img src="../.gitbook/assets/shot.png" alt="">'
                          "</figure>")
        self.assertNotIn("<figcaption>", out)

    def test_alt_text_is_preserved(self):
        out = self.figure('<figure><img src="../.gitbook/assets/shot.png" '
                          'alt="Kiln Model Library"></figure>')
        self.assertIn("![Kiln Model Library](../../../assets/shot.png)", out)

    def test_a_filename_with_spaces_survives_the_handoff(self):
        # The figure pass emits an angle-bracketed destination so the space
        # reaches rewrite_references intact.
        out = self.figure('<figure><img src="../.gitbook/assets/wide shot.png" '
                          'alt=""></figure>')
        self.assertIn("![](../../../assets/wide-shot.png)", out)

    def test_embed_figure_keeps_its_html(self):
        out = convert('# P\n\n{% embed url="https://vimeo.com/1" %}\nCap\n{% endembed %}\n')
        self.assertIn("<figure><div", out)
        self.assertIn("<figcaption><p>Cap</p></figcaption></figure>", out)

    def test_a_figure_inside_a_code_fence_is_untouched(self):
        source = ('# P\n\n```html\n<figure><img src="../.gitbook/assets/shot.png" '
                  'alt=""></figure>\n```\n')
        out = G.convert(source, "docs/page.md", context(self.ASSETS))
        self.assertIn('<figure><img src="../.gitbook/assets/shot.png" alt=""></figure>', out)


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

    def test_folded_block_treats_a_blank_line_as_a_line_break(self):
        fields, _ = G.parse_frontmatter("---\ndescription: >\n  one\n  two\n\n  three\n---\n")
        self.assertEqual(fields["description"], "one two\nthree")

    def test_double_quoted_escapes_are_decoded(self):
        fields, _ = G.parse_frontmatter('---\ndescription: "a\\nb \\"c\\""\n---\n')
        self.assertEqual(fields["description"], 'a\nb "c"')

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

    CDN_VIDEO = ("https://files.gitbook.com/v0/b/gitbook-x-prod.appspot.com/o/"
                 "spaces%2FA%2Fuploads%2FB%2FCreateTask720.mp4?alt=media&token=x")

    def test_gitbook_cdn_video_points_at_the_local_copy(self):
        ctx = context({"CreateTask720.mp4": "CreateTask720.mp4"})
        out = convert('# P\n\n{%% embed url="%s" %%}\nCreate a task\n{%% endembed %%}\n'
                      % self.CDN_VIDEO, ctx=ctx)
        self.assertIn('<video controls playsinline', out)
        self.assertIn('src="/assets/CreateTask720.mp4"', out)
        self.assertIn("<figcaption><p>Create a task</p></figcaption>", out)
        # Videos are not optimizable, so they belong in public/assets -- and
        # registering them there is what gets them copied at all.
        self.assertEqual(ctx.public_assets, {"CreateTask720.mp4"})
        self.assertEqual(ctx.missing_assets, [])

    def test_a_cdn_video_with_no_local_copy_is_reported(self):
        ctx = context()
        convert('# P\n\n{%% embed url="%s" %%}\n' % self.CDN_VIDEO, ctx=ctx)
        self.assertEqual(ctx.missing_assets, [("docs/page.md", "CreateTask720.mp4")])


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
        with tempfile.TemporaryDirectory() as scratch:
            relative = os.path.relpath(os.path.join(scratch, "out"))
            self.assertEqual(self.parse(["--out", relative]).out,
                             os.path.join(scratch, "out"))

    def test_out_accepts_the_equals_spelling(self):
        with tempfile.TemporaryDirectory() as scratch:
            target = os.path.join(scratch, "out")
            self.assertEqual(self.parse(["--out=%s" % target]).out, target)

    def test_out_without_a_directory_is_an_error(self):
        with self.assertRaises(SystemExit):
            self.parse(["--out"])

    def test_empty_out_is_rejected(self):
        # An empty --out is an unset shell variable. Truthiness checks downstream
        # would read it as "no --out given" and rebuild the site in place.
        for argv in (["--out", ""], ["--out", "   "], ["--out="]):
            with self.subTest(argv=argv), self.assertRaises(SystemExit):
                self.parse(argv)

    def test_unknown_arguments_are_rejected(self):
        # Never fall through to the default run: that one starts by deleting
        # src/content/docs, which is forbidden once content is hand-edited.
        for argv in (["--outt", "/tmp/x"], ["garbage"], ["--out", "/tmp/x", "--nope"]):
            with self.subTest(argv=argv), self.assertRaises(SystemExit):
                self.parse(argv)


class GitGuardTest(unittest.TestCase):
    """From phase 3 on, src/content/docs is committed and must not be rebuilt."""

    def git_says(self, returncode=0, stdout="", stderr=""):
        result = mock.Mock(returncode=returncode, stdout=stdout, stderr=stderr)
        return mock.patch.object(G.subprocess, "run", return_value=result)

    def test_git_status_reads_the_ls_files_output(self):
        with self.git_says(stdout="site/src/content/docs/index.md\n"):
            self.assertEqual(G.git_status_of("x"), (G.TRACKED, ""))
        with self.git_says(stdout="  \n"):
            self.assertEqual(G.git_status_of("x"), (G.UNTRACKED, ""))

    def test_git_failure_is_unknown_not_untracked(self):
        # dubious ownership, a held index.lock, a damaged index: git answered,
        # but not with "no".
        with self.git_says(returncode=128, stderr="fatal: detected dubious ownership"):
            state, detail = G.git_status_of("x")
        self.assertEqual(state, G.UNKNOWN)
        self.assertIn("dubious ownership", detail)

    def test_missing_git_is_unknown(self):
        with mock.patch.object(G.subprocess, "run", side_effect=OSError("no git")):
            self.assertEqual(G.git_status_of("x")[0], G.UNKNOWN)

    def test_default_run_refuses_when_the_output_is_committed(self):
        with fake_repo():
            with mock.patch.object(G, "git_status_of", return_value=(G.TRACKED, "")), \
                    mock.patch.object(G.shutil, "rmtree") as rmtree:
                with self.assertRaises(SystemExit) as raised:
                    silenced(lambda: G.main([]))
            rmtree.assert_not_called()
            self.assertIn("--out DIR", str(raised.exception))

    def test_default_run_refuses_when_a_checkout_cannot_be_queried(self):
        with fake_repo() as repo:
            (repo / ".git").mkdir()
            with mock.patch.object(G, "git_status_of", return_value=(G.UNKNOWN, "boom")), \
                    mock.patch.object(G.shutil, "rmtree") as rmtree:
                with self.assertRaises(SystemExit) as raised:
                    silenced(lambda: G.main([]))
            rmtree.assert_not_called()
            self.assertIn("boom", str(raised.exception))

    def test_default_run_refuses_when_dot_git_is_a_worktree_file(self):
        # A worktree or submodule checkout has .git as a file holding a gitdir:
        # pointer -- and those are the container setups where git fails to answer.
        with fake_repo() as repo:
            (repo / ".git").write_text("gitdir: /elsewhere/.git/worktrees/wt\n")
            with mock.patch.object(G, "git_status_of", return_value=(G.UNKNOWN, "boom")), \
                    mock.patch.object(G.shutil, "rmtree") as rmtree:
                with self.assertRaises(SystemExit) as raised:
                    silenced(lambda: G.main([]))
            rmtree.assert_not_called()
            self.assertIn("boom", str(raised.exception))

    def test_default_run_proceeds_when_there_is_no_checkout(self):
        with fake_repo() as repo:
            with mock.patch.object(G, "git_status_of", return_value=(G.UNKNOWN, "no git")):
                silenced(lambda: G.main([]))
            self.assertTrue((repo / "site/src/content/docs/docs/one.md").exists())

    def test_out_run_skips_the_check_entirely(self):
        with fake_repo(), tempfile.TemporaryDirectory() as scratch:
            with mock.patch.object(G, "git_status_of") as asked:
                silenced(lambda: G.main(["--out", os.path.join(scratch, "out")]))
            asked.assert_not_called()


class OutTargetTest(unittest.TestCase):
    """--out must not be able to clobber anything. It has failed open three ways."""

    def reject(self, target):
        with fake_repo():
            with self.assertRaises(SystemExit):
                silenced(lambda: G.parse_args(["--out", target]))

    def test_the_repo_itself_is_rejected(self):
        # This one really happened: it rewrote 40 tracked source pages in place.
        with fake_repo() as repo:
            with self.assertRaises(SystemExit):
                silenced(lambda: G.parse_args(["--out", str(repo)]))
            self.assertIn("# One", (repo / "docs" / "one.md").read_text())

    def test_a_directory_inside_the_repo_is_rejected(self):
        with fake_repo() as repo:
            for target in ("scratch", "docs", "site/src/content/docs"):
                with self.subTest(target=target), self.assertRaises(SystemExit):
                    silenced(lambda: G.parse_args(["--out", str(repo / target)]))

    def test_an_ancestor_of_the_repo_is_rejected(self):
        with fake_repo() as repo:
            with self.assertRaises(SystemExit):
                silenced(lambda: G.parse_args(["--out", str(repo.parent)]))
            with self.assertRaises(SystemExit):
                silenced(lambda: G.parse_args(["--out", "/"]))

    def test_a_directory_holding_foreign_markdown_is_rejected(self):
        with fake_repo(), tempfile.TemporaryDirectory() as scratch:
            notes = pathlib.Path(scratch, "notes")
            notes.mkdir()
            (notes / "keep.md").write_text("# mine\n")
            with self.assertRaises(SystemExit):
                silenced(lambda: G.parse_args(["--out", scratch]))
            self.assertEqual((notes / "keep.md").read_text(), "# mine\n")

    def test_an_existing_file_is_rejected(self):
        with fake_repo(), tempfile.TemporaryDirectory() as scratch:
            target = pathlib.Path(scratch, "afile")
            target.write_text("")
            with self.assertRaises(SystemExit):
                silenced(lambda: G.parse_args(["--out", str(target)]))

    def test_padding_is_stripped_before_the_path_is_resolved(self):
        with fake_repo(), tempfile.TemporaryDirectory() as scratch:
            target = os.path.join(scratch, "out")
            self.assertEqual(silenced(lambda: G.parse_args(["--out", " %s " % target])).out,
                             target)

    def test_a_fresh_directory_is_accepted(self):
        with fake_repo(), tempfile.TemporaryDirectory() as scratch:
            target = os.path.join(scratch, "out")
            self.assertEqual(silenced(lambda: G.parse_args(["--out", target])).out, target)

    def test_a_symlinked_subdirectory_cannot_be_written_through(self):
        # The write-time assertion, isolated: the symlink points at an in-repo
        # directory holding no markdown, so the parse-time stray-markdown check
        # finds nothing and the run is accepted. Nothing may still be written.
        with fake_repo() as repo, tempfile.TemporaryDirectory() as scratch:
            wrapper = pathlib.Path(scratch, "wrapper")
            wrapper.mkdir()
            (wrapper / "docs").symlink_to(repo / ".gitbook" / "assets")
            self.assertIsNone(G.stray_markdown(str(wrapper)))

            with self.assertRaises(SystemExit) as raised:
                silenced(lambda: G.main(["--out", str(wrapper)]))

            self.assertIn("outside the output directory", str(raised.exception))
            self.assertEqual(sorted(os.listdir(repo / ".gitbook" / "assets")),
                             ["clip.mp4", "orphan.png", "shot.png", "wide shot.png"])

    def test_a_symlink_swapped_in_after_stamping_is_still_refused(self):
        # The stamp short-circuits stray_markdown, so on a re-run the write-time
        # assertion is the only thing left. It has to be enough on its own.
        with fake_repo() as repo, tempfile.TemporaryDirectory() as scratch:
            target = pathlib.Path(scratch, "out")
            silenced(lambda: G.main(["--out", str(target)]))
            source = (repo / "docs" / "one.md").read_text()

            shutil.rmtree(target / "docs")
            (target / "docs").symlink_to(repo / "docs")
            self.assertIsNone(G.stray_markdown(str(target)))

            with self.assertRaises(SystemExit) as raised:
                silenced(lambda: G.main(["--out", str(target)]))
            self.assertIn("outside the output directory", str(raised.exception))
            self.assertEqual((repo / "docs" / "one.md").read_text(), source)

    def test_a_symlinked_subdirectory_holding_markdown_is_rejected_at_parse_time(self):
        # The secondary check: os.walk has to follow the link to see what a
        # write would reach.
        with fake_repo() as repo, tempfile.TemporaryDirectory() as scratch:
            wrapper = pathlib.Path(scratch, "wrapper")
            wrapper.mkdir()
            (wrapper / "docs").symlink_to(repo / "docs")
            source = (repo / "docs" / "one.md").read_text()

            with self.assertRaises(SystemExit):
                silenced(lambda: G.parse_args(["--out", str(wrapper)]))
            self.assertEqual((repo / "docs" / "one.md").read_text(), source)

    def test_stray_markdown_survives_a_symlink_cycle(self):
        with tempfile.TemporaryDirectory() as scratch:
            (pathlib.Path(scratch, "loop")).symlink_to(scratch)
            self.assertIsNone(G.stray_markdown(scratch))

    def test_a_dangling_symlink_is_a_parser_error_not_a_traceback(self):
        # Broken at the target itself, and one and two levels above it: all three
        # used to die in os.makedirs instead of reporting like every other bad
        # target.
        with fake_repo(), tempfile.TemporaryDirectory() as scratch:
            broken = pathlib.Path(scratch, "dangling")
            broken.symlink_to(pathlib.Path(scratch, "nowhere"))
            for target in (broken, broken / "sub", broken / "a" / "b"):
                with self.subTest(target=str(target)):
                    with self.assertRaises(SystemExit) as raised:
                        silenced(lambda: G.parse_args(["--out", str(target)]))
                    self.assertEqual(raised.exception.code, 2)

    def test_a_hardlinked_destination_is_replaced_not_written_through(self):
        # os.replace unlinks the destination name, so a page hardlinked to a
        # GitBook source cannot truncate the inode they share. Needs a deliberate
        # `ln` into a stamped target, but it is the round-1 damage signature.
        with fake_repo() as repo, tempfile.TemporaryDirectory() as scratch:
            target = pathlib.Path(scratch, "out")
            silenced(lambda: G.main(["--out", str(target)]))
            source = repo / "docs" / "one.md"
            original = source.read_text()

            written = target / "docs" / "one.md"
            written.unlink()
            os.link(source, written)
            self.assertEqual(source.stat().st_nlink, 2)

            silenced(lambda: G.main(["--out", str(target)]))

            self.assertEqual(source.read_text(), original)
            self.assertIn('title: "One"', written.read_text())
            self.assertEqual(source.stat().st_nlink, 1)

    def test_no_partial_files_are_left_behind(self):
        with fake_repo(), tempfile.TemporaryDirectory() as scratch:
            target = pathlib.Path(scratch, "out")
            silenced(lambda: G.main(["--out", str(target)]))
            self.assertEqual(list(target.rglob("*.part")), [])

    def test_rerunning_into_our_own_output_is_accepted(self):
        # The stamp is what tells our markdown apart from somebody else's.
        with fake_repo(), tempfile.TemporaryDirectory() as scratch:
            target = os.path.join(scratch, "out")
            silenced(lambda: G.main(["--out", target]))
            self.assertTrue(os.path.exists(os.path.join(target, G.OUT_STAMP)))
            silenced(lambda: G.main(["--out", target]))


class OutFlagTest(unittest.TestCase):
    """The safety property --out exists for: it must never delete or clobber."""

    def test_out_writes_pages_only_and_touches_nothing_else(self):
        with fake_repo() as repo, tempfile.TemporaryDirectory() as scratch:
            sidebar = pathlib.Path(G.SITE, "sidebar.json")
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
            self.assertEqual(len(list(pathlib.Path(scratch).rglob("*.md"))), 2)
            self.assertEqual(list(pathlib.Path(scratch).rglob("*.mdx")), [])
            self.assertFalse(sidebar.exists())
            self.assertFalse(pathlib.Path(G.DOCS_OUT).exists())
            self.assertIn("# One", (repo / "docs" / "one.md").read_text())

    def test_the_completion_message_does_not_overclaim(self):
        with fake_repo(), tempfile.TemporaryDirectory() as scratch:
            out = io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                G.main(["--out", os.path.join(scratch, "out")])
        message = out.getvalue()
        self.assertNotIn("Nothing else was written", message)
        self.assertIn("Left untouched:", message)


class CopyAssetsTest(unittest.TestCase):
    """The default run decides which of the 159 GitBook assets survive."""

    def run_default(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            G.main([])
        return out.getvalue()

    def test_referenced_assets_land_in_the_right_tree(self):
        with fake_repo():
            self.run_default()
            src = pathlib.Path(G.SRC_ASSETS)
            public = pathlib.Path(G.ASSETS_OUT)
            # Markdown images are optimizable, so they go to src/assets under a
            # name Astro can resolve.
            self.assertTrue((src / "shot.png").exists())
            self.assertTrue((src / "wide-shot.png").exists())
            self.assertFalse((src / "wide shot.png").exists())
            # Everything Astro will not process is served verbatim.
            self.assertEqual(sorted(p.name for p in public.iterdir()), ["clip.mp4"])

    def test_unreferenced_assets_are_not_copied_but_are_reported(self):
        with fake_repo():
            printed = self.run_default()
            self.assertFalse(pathlib.Path(G.SRC_ASSETS, "orphan.png").exists())
            self.assertFalse(pathlib.Path(G.ASSETS_OUT, "orphan.png").exists())
            self.assertIn("1 unreferenced asset(s)", printed)
            self.assertIn("orphan.png", printed)

    def test_the_original_assets_are_left_alone(self):
        with fake_repo() as repo:
            self.run_default()
            self.assertEqual(
                sorted(p.name for p in (repo / ".gitbook" / "assets").iterdir()),
                ["clip.mp4", "orphan.png", "shot.png", "wide shot.png"])

    def test_the_hero_image_is_still_copied(self):
        with fake_repo():
            self.run_default()
            self.assertTrue(pathlib.Path(G.SRC_ASSETS, "hero.png").exists())

    def test_a_stale_copy_does_not_survive_a_rerun(self):
        with fake_repo():
            self.run_default()
            stale = pathlib.Path(G.SRC_ASSETS, "gone.png")
            stale.write_bytes(b"stale")
            self.run_default()
            self.assertFalse(stale.exists())

    def test_colliding_safe_names_fail_the_run(self):
        with fake_repo() as repo:
            assets = repo / ".gitbook" / "assets"
            (assets / "wide-shot.png").write_bytes(b"bytes")
            (repo / "docs" / "one.md").write_text(
                "# One\n\n![](<../.gitbook/assets/wide shot.png>)\n\n"
                "![](../.gitbook/assets/wide-shot.png)\n")
            with self.assertRaises(SystemExit) as raised:
                self.run_default()
            self.assertIn("wide-shot.png", str(raised.exception))

    def test_out_runs_copy_nothing(self):
        with fake_repo(), tempfile.TemporaryDirectory() as scratch:
            silenced(lambda: G.main(["--out", os.path.join(scratch, "out")]))
            self.assertFalse(pathlib.Path(G.SRC_ASSETS).exists())
            self.assertFalse(pathlib.Path(G.ASSETS_OUT).exists())


class SidebarTest(unittest.TestCase):
    SUMMARY = textwrap.dedent("""
        # Table of contents

        * [Welcome](README.md)

        ## Docs

        * [Quickstart](docs/quickstart.md)
        * [Fine Tuning](docs/fine-tuning/README.md)
          * [Fine Tuning Guide](docs/fine-tuning/fine-tuning-guide.md)
        * [Evaluate RAG Accuracy: Q\\&A Evals](docs/evals-and-specs/rag.md)
        * [Using `kiln_ai` **now**](developers/library.md)
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

    def test_labels_are_rendered_as_text(self):
        # Escapes, code spans and emphasis all have to go: the sidebar shows the
        # label verbatim, it does not render markdown.
        labels = [i["label"] for i in self.groups[0]["items"]]
        self.assertIn("Evaluate RAG Accuracy: Q&A Evals", labels)
        self.assertIn("Using kiln_ai now", labels)

    def test_a_parent_page_becomes_an_overview_entry_in_its_own_group(self):
        parent = next(i for i in self.groups[0]["items"] if i["label"] == "Fine Tuning")
        self.assertTrue(parent["collapsed"])
        self.assertEqual(parent["items"][0], {"label": "Overview", "link": "/docs/fine-tuning/"})
        self.assertEqual(parent["items"][1]["link"], "/docs/fine-tuning/fine-tuning-guide/")


if __name__ == "__main__":
    unittest.main()
