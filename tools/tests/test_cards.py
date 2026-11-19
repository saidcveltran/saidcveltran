"""Offline tests for the borderless cards: titles, repository cards, the Duckys card, the rain and the banner."""
from __future__ import annotations

import re
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from live_profile.duckys_figures import Figures
from live_profile.render_banner import GRID as BANNER_GRID
from live_profile.render_banner import render_banner
from live_profile.feature_card import FADE_FROM, FADE_TO, MARK_BOX, MARK_X, MARK_Y, PANEL_FROM, PANEL_FULL, PANEL_OPACITY, WIDTH as FEATURE_WIDTH
from live_profile.feature_card import HEIGHT as FEATURE_HEIGHT
from live_profile.render_duckys_card import BARS, render_duckys_card
from live_profile.render_languages import render_language_icon
from live_profile.render_resma_card import PANEL_COLOR, SHEET_BACK, SHEET_FOLD, SHEET_FRONT, render_resma_card
from live_profile.render_rain import FALLBACK, RainGrid, column_text, rain_fragment, source_text
from live_profile.render_repo_card import (DESCRIPTION_LINES, GUTTER, HEIGHT, NAME_LIMIT, TILE_WIDTH, WIDTH, card_name, render_repo_card,
                                           render_repo_cards_html, wrap)
from live_profile.render_socials import Link, render_button
from live_profile.render_title import render_title
from live_profile.svg_common import DISPLAY_ADVANCE, document
from tests.fixtures import FIXTURE, NOW, make_repo

FIGURES = Figures(1340, 395000)
MARK_BYTES = b"RIFF\x00\x00\x00\x00WEBPVP8 "  # stands in for an image: the renderers only embed the bytes
GRID = RainGrid(width=200, height=100, pitch=20, rows=6, row_step=10, font_size=9)


class WithAssets(unittest.TestCase):
    """Base class: a temporary folder with a fake mascot and a fake banner foreground."""

    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.mark = Path(folder.name, "mark.webp")
        self.mark.write_bytes(MARK_BYTES)
        self.foreground = Path(folder.name, "foreground.webp")
        self.foreground.write_bytes(MARK_BYTES * 3)
        self.cards = {
            "title": render_title("Projects"),
            "duckys-card": render_duckys_card(FIGURES, NOW, self.mark),
            "repo-card": render_repo_card(FIXTURE[1], NOW),
            "language-icon": render_language_icon("Rust"),
            "social-button": render_button(Link("X", "@aiskaron", "https://x.com/aiskaron", "x")),
            "banner": render_banner(FIXTURE, self.foreground),
            "resma-card": render_resma_card(),
        }


class Borderless(WithAssets):
    def test_cards_have_no_surface_no_frame_and_no_rounded_corner(self):
        for name, svg in self.cards.items():
            with self.subTest(card=name):
                for forbidden in ('class="surface"', 'class="frame"', "border-radius"):
                    self.assertNotIn(forbidden, svg)
                self.assertNotRegex(svg, r"<rect\b[^>]*\brx=")  # an ellipse's rx is a radius, not a rounded corner

    def test_framed_documents_keep_their_rounded_card(self):
        framed = document(40, "x", "", framed=True)
        self.assertIn('class="surface"', framed)
        self.assertIn('rx="10"', framed)
        self.assertRegex(framed, r"<rect\b[^>]*\brx=")  # negative control: the borderless check above can fail

    def test_cards_are_well_formed_self_contained_and_scriptless(self):
        for name, svg in self.cards.items():
            with self.subTest(card=name):
                self.assertTrue(ET.fromstring(svg).tag.endswith("svg"))
                self.assertNotIn("https://", svg)
                self.assertNotIn("<script", svg)
                self.assertNotRegex(svg, r'(href|src)="(?!data:)[^"#]')
                self.assertIn("prefers-reduced-motion", svg)

    def test_font_embedding_is_optional(self):
        self.assertEqual(document(10, "x", "", fonts=False).count("data:font/woff2"), 0)
        self.assertEqual(document(10, "x", "", fonts=True).count("data:font/woff2"), 2)


class Title(unittest.TestCase):
    def test_text_is_set_in_the_display_font_and_escaped(self):
        svg = render_title("A<b>&")
        ET.fromstring(svg)
        self.assertIn('class="ink display"', svg)
        self.assertNotIn("A<b>", svg)

    def test_there_is_no_small_text_above_the_title(self):
        svg = render_title("Projects")
        self.assertEqual(svg.count("<text"), 1)

    def test_empty_and_overlong_titles_are_rejected_not_cut(self):
        with self.assertRaises(ValueError):
            render_title("   ")
        with self.assertRaises(ValueError):
            render_title("x" * 40)

    def test_cursor_follows_the_text(self):
        position = lambda text: float(re.search(r'class="accent cursor" x="([\d.]+)"', render_title(text)).group(1))
        self.assertLess(position("Ask"), position("Languages"))


class Wrap(unittest.TestCase):
    def test_short_text_stays_on_one_line(self):
        self.assertEqual(wrap("Static documentation engine", 31, 2), ["Static documentation engine"])

    def test_long_text_wraps_at_word_boundaries_within_the_width(self):
        rows = wrap("one two three four five six seven eight nine ten", 14, 5)
        self.assertTrue(all(len(row) <= 14 for row in rows))
        self.assertEqual(" ".join(rows), "one two three four five six seven eight nine ten")

    def test_overflow_ends_with_an_ellipsis_and_respects_the_line_limit(self):
        rows = wrap("word " * 60, 20, 2)
        self.assertEqual(len(rows), 2)
        self.assertTrue(rows[-1].endswith("…"))
        self.assertTrue(all(len(row) <= 20 for row in rows))

    def test_a_single_huge_word_is_clipped_and_empty_text_gives_no_lines(self):
        self.assertEqual(wrap("x" * 100, 10, 2), ["x" * 9 + "…"])
        self.assertEqual(wrap("", 10, 2), [])
        self.assertEqual(wrap("   ", 10, 2), [])


class RepoCard(unittest.TestCase):
    def test_tile_leaves_a_transparent_gutter_so_cards_read_as_separate(self):
        svg = render_repo_card(FIXTURE[0], NOW)
        self.assertEqual((WIDTH, GUTTER), (TILE_WIDTH + GUTTER, 20))
        self.assertIn(f'width="{WIDTH}" height="{HEIGHT}"', svg)
        self.assertIn(f'<rect class="tile" x="0" y="0" width="{TILE_WIDTH}"', svg)

    def test_shows_version_release_date_language_and_last_push(self):
        svg = render_repo_card(FIXTURE[1], NOW)  # steady: v1.9.0 released 20 days ago, pushed 14 days ago
        for fact in (">v1.9.0<", "released 30 Oct", ">Rust<", "pushed 5 Nov", ">steady<"):
            self.assertIn(fact, svg)

    def test_repository_without_a_release_says_so(self):
        svg = render_repo_card(FIXTURE[2], NOW)
        self.assertIn("no release yet", svg)
        self.assertNotIn("released ", svg)

    def test_state_label_follows_the_data(self):
        self.assertIn(">NEW<", render_repo_card(FIXTURE[0], NOW))
        self.assertIn(">STEADY<", render_repo_card(FIXTURE[1], NOW))
        self.assertIn(">QUIET<", render_repo_card(FIXTURE[2], NOW))

    def test_description_is_shortened_to_the_line_limit_and_escaped(self):
        repo = make_repo("tool", created_days=60, pushed_days=3, description="A <b>tool</b> & more " * 20)
        svg = render_repo_card(repo, NOW)
        ET.fromstring(svg)
        self.assertNotIn("<b>", svg)
        self.assertEqual(len(re.findall(r'<text class="muted" x="18" y="(?:122|138|154)"', svg)), DESCRIPTION_LINES)

    def test_long_names_are_clipped_to_the_tile(self):
        self.assertIn("n" * (NAME_LIMIT - 1) + "…", render_repo_card(make_repo("n" * 60, created_days=60, pushed_days=3), NOW))

    def test_missing_language_hides_the_language_mark(self):
        repo = make_repo("plain", created_days=60, pushed_days=3, language="")
        self.assertNotIn('<rect class="accent" x="18" y="150"', render_repo_card(repo, NOW))

    def test_row_has_one_link_per_repository_with_alt_text(self):
        html = render_repo_cards_html(FIXTURE, "someone", "assets")
        self.assertEqual(html.count("<a href="), len(FIXTURE))
        self.assertIn('href="https://github.com/someone/steady"', html)
        self.assertIn(f'src="assets/{card_name(FIXTURE[1])}"', html)
        self.assertIn('alt="steady: v1.9.0"', html)
        self.assertIn('alt="quiet: no release yet"', html)

    def test_no_repositories_gives_no_markup_and_hostile_names_are_escaped(self):
        self.assertEqual(render_repo_cards_html([], "someone", "assets"), "")
        self.assertNotIn("<b>", render_repo_cards_html([make_repo("a<b>", created_days=9, pushed_days=1)], "someone", "assets"))


class DuckysCard(WithAssets):
    def test_name_figures_and_call_to_action_are_drawn(self):
        svg = self.cards["duckys-card"]
        for text in (">DUCKYS<", ">1,340+<", ">395,000+<", ">servers<", ">tracks played<", "Click to see the Duckys project"):
            self.assertIn(text, svg)

    def test_the_name_is_the_largest_text(self):
        sizes = [float(size) for size in re.findall(r'font-size="([\d.]+)"', self.cards["duckys-card"])]
        name_size = float(re.search(r'font-size="([\d.]+)">DUCKYS<', self.cards["duckys-card"]).group(1))
        self.assertEqual(name_size, max(sizes))

    def test_the_mascot_is_embedded(self):
        self.assertIn("data:image/webp;base64,", self.cards["duckys-card"])

    def test_layers_bars_then_panel_then_mascot_then_text(self):
        svg = self.cards["duckys-card"]
        self.assertLess(svg.rindex('class="bar '), svg.index("fill=\"url(#panel-gradient)\""))
        self.assertLess(svg.index("fill=\"url(#panel-gradient)\""), svg.index("<image"))
        self.assertLess(svg.index("<image"), svg.index(">DUCKYS<"))

    def test_bar_count_and_faintness(self):
        svg = self.cards["duckys-card"]
        self.assertEqual(svg.count('class="bar '), BARS)
        self.assertRegex(svg, r"\.bar-a \{[^}]*opacity: \.[1-3]\d?;")

    def test_footnote_says_the_bars_are_decoration(self):
        self.assertIn("the bars are only decoration", self.cards["duckys-card"])

    def test_labels_stay_clear_of_larger_numbers(self):
        big = render_duckys_card(Figures(1340000, 39500000), NOW, self.mark)
        positions = lambda text: [float(v) for v in re.findall(r'<text class="muted" x="(\d+)" y="146"', text)]
        self.assertGreater(positions(big)[1], positions(self.cards["duckys-card"])[1])

    def test_card_height_and_determinism(self):
        self.assertIn(f'height="{FEATURE_HEIGHT}"', self.cards["duckys-card"])
        self.assertEqual(self.cards["duckys-card"], render_duckys_card(FIGURES, NOW, self.mark))

    def test_missing_mascot_fails_loudly(self):
        with self.assertRaises(FileNotFoundError):
            render_duckys_card(FIGURES, NOW, self.mark.with_name("absent.webp"))


class FeatureCards(WithAssets):
    """What the Duckys and Resma cards share: a mark that fades in over a pastel panel that appears from the middle."""

    def setUp(self):
        super().setUp()
        self.featured = {"duckys": self.cards["duckys-card"], "resma": render_resma_card()}

    def test_the_mark_appears_from_the_middle_and_sinks_at_the_bottom(self):
        for name, svg in self.featured.items():
            with self.subTest(card=name):
                self.assertIn('mask="url(#mark-fade-x)"', svg)
                self.assertIn('mask="url(#mark-fade-y)"', svg)
                self.assertIn(f'x1="{FADE_FROM}" x2="{FADE_TO}"', svg)
                self.assertRegex(svg, r'<stop offset="0" stop-color="#fff" stop-opacity="0"/>')  # fully transparent at the start
                self.assertRegex(svg, r'<stop offset="1" stop-color="#fff" stop-opacity="0"/>')  # and at the bottom

    def test_geometry_keeps_every_edge_transparent_and_the_mark_whole(self):
        self.assertTrue(FEATURE_WIDTH // 2 <= FADE_FROM < FADE_TO <= MARK_X + 50)  # fully shown before the artwork's tail
        self.assertEqual((MARK_Y, MARK_Y + MARK_BOX), (0, FEATURE_HEIGHT))  # the artwork fits the card exactly: not cropped at the top
        self.assertEqual(PANEL_FROM, FEATURE_WIDTH // 2)  # the background starts exactly at the middle of the card
        self.assertLess(PANEL_FROM, PANEL_FULL)
        self.assertLessEqual(PANEL_FULL, MARK_X + 110)  # and is solid by the time the mark is fully shown

    def test_the_panel_is_a_pastel_that_appears_from_the_middle(self):
        for name, svg in self.featured.items():
            with self.subTest(card=name):
                stops = re.findall(r'<linearGradient id="panel-gradient"[^>]*>(.*?)</linearGradient>', svg)[0]
                self.assertRegex(stops, r'offset="0" stop-color="#[0-9a-f]{6}" stop-opacity="0"')  # nothing at the middle
                self.assertRegex(stops, rf'offset="1" stop-color="#[0-9a-f]{{6}}" stop-opacity="{PANEL_OPACITY}"')
                red, green, blue = (int(stops[stops.index("#") + 1:][i:i + 2], 16) for i in (0, 2, 4))
                self.assertGreaterEqual((red + green + blue) / 3, 200)  # pastel: light overall...
                self.assertGreaterEqual(min(red, green, blue), 0xa0)  # ...and no channel dark
                self.assertRegex(svg, rf'<rect x="{PANEL_FROM}" width="{FEATURE_WIDTH - PANEL_FROM}" height="{FEATURE_HEIGHT}" fill="url\(#panel-gradient\)"/>')

    def test_each_card_takes_the_colour_of_its_own_site(self):
        """Duckys: warm amber from its accent; Resma: the teal of its icon. Different, never the same pastel."""
        colour = lambda svg: re.search(r'id="panel-gradient".*?stop-color="(#[0-9a-f]{6})"', svg).group(1)
        self.assertEqual(colour(self.featured["duckys"]), "#f7dcae")
        self.assertEqual(colour(self.featured["resma"]), "#c9e9e4")

    def test_call_to_action_names_the_project(self):
        self.assertIn("Click to see the Duckys project", self.featured["duckys"])
        self.assertIn("Click to see the Resma project", self.featured["resma"])


class ResmaCard(unittest.TestCase):
    def setUp(self):
        self.svg = render_resma_card()

    def test_says_what_the_product_does_and_nothing_live(self):
        for text in (">RESMA<", "PDF TOOLS IN YOUR BROWSER", "Merge PDF · JPG to PDF", "nothing leaves your device"):
            self.assertIn(text, self.svg)
        self.assertNotRegex(self.svg, r">[\d,]+\+<")  # no figures: Resma has no public counter
        self.assertNotIn("updated", self.svg)

    def test_is_static_so_a_scheduled_run_never_commits_it(self):
        self.assertEqual(self.svg, render_resma_card())

    def test_text_stays_clear_of_the_mark(self):
        widest = max(len("Merge PDF · JPG to PDF") * 32 * DISPLAY_ADVANCE, len("Click to see the Resma project") * 7.4,
                     len("Free, no sign-up, nothing leaves your device") * 7.8)
        self.assertLess(widest, FADE_FROM)

    def test_sheets_are_vector_so_the_card_stays_small_and_square(self):
        self.assertNotIn("<image", self.svg)
        self.assertNotRegex(self.svg, r"<rect\b[^>]*\brx=")
        self.assertEqual(self.svg.count('class="sheet-back"'), 1)
        self.assertLess(len(self.svg), 40_000)

    def test_the_back_sheet_moves_inside_the_masked_group(self):
        """The mask sits on a static parent: the animated sheet must not carry the mask that hides its overlap."""
        match = re.search(r'<g mask="url\(#behind-front\)"><path class="sheet-back"', self.svg)
        self.assertIsNotNone(match)
        self.assertIn("@keyframes drift", self.svg)

    def test_the_logo_stands_out_from_the_panel(self):
        """The pale first version (white and pale teal sheets on a pale teal panel) was hard to see: require real contrast."""
        def luminance(colour: str) -> float:
            channels = [int(colour[i:i + 2], 16) / 255 for i in (1, 3, 5)]
            red, green, blue = (c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels)
            return 0.2126 * red + 0.7152 * green + 0.0722 * blue

        def contrast(first: str, second: str) -> float:
            light, dark = sorted((luminance(first), luminance(second)), reverse=True)
            return (light + 0.05) / (dark + 0.05)

        self.assertGreaterEqual(contrast(SHEET_FRONT, PANEL_COLOR), 4.0)  # the main sheet reads clearly
        self.assertGreaterEqual(contrast(SHEET_BACK, PANEL_COLOR), 2.0)  # the sheet behind is secondary but visible
        self.assertGreater(contrast(SHEET_FRONT, SHEET_BACK), 1.5)  # and the two sheets are distinguishable
        self.assertLess(contrast("#ffffff", PANEL_COLOR), 2.0)  # negative control: the old white sheet would fail the main check
        for colour in (SHEET_FRONT, SHEET_BACK, SHEET_FOLD):
            self.assertIn(f'fill="{colour}"', self.svg)

    def test_layers_panel_then_mark_then_text(self):
        self.assertLess(self.svg.index("fill=\"url(#panel-gradient)\""), self.svg.index('class="sheet-back"'))
        self.assertLess(self.svg.index('class="sheet-back"'), self.svg.index(">RESMA<"))


class Rain(unittest.TestCase):
    def test_source_text_is_made_of_the_real_facts_without_dates_by_default(self):
        text = source_text(FIXTURE)
        for fact in ("fresh", "v0.1.1", "steady", "v1.9.0", "quiet"):
            self.assertIn(fact, text)
        self.assertNotIn(" ", text)
        self.assertNotIn("Nov", text)
        self.assertIn("Nov", source_text(FIXTURE, with_dates=True))

    def test_source_text_ignores_pushes_when_no_dates_are_wanted(self):
        pushed_again = [make_repo("steady", created_days=30, pushed_days=1, tags=(("v1.9.0", 20),))]
        self.assertEqual(source_text(FIXTURE[1:2]), source_text(pushed_again))

    def test_empty_input_uses_the_fallback(self):
        self.assertEqual(source_text([]), FALLBACK)
        ET.fromstring(document(10, "x", rain_fragment(FALLBACK, GRID), GRID.css, framed=False))

    def test_columns_are_windows_of_the_source_and_wrap(self):
        self.assertEqual(len(column_text("ab", 3, 6)), 6)
        self.assertTrue(set(column_text("ab", 3, 6)) <= set("ab"))
        self.assertNotEqual(column_text("abcdefghijklmnop", 0, 6), column_text("abcdefghijklmnop", 1, 6))

    def test_one_drop_per_column_and_only_source_characters_fall(self):
        source = source_text(FIXTURE)
        svg = document(100, "x", rain_fragment(source, GRID), GRID.css, width=200, framed=False)
        ET.fromstring(svg)
        self.assertEqual(svg.count('class="drop"'), GRID.columns)
        fallen = {char for text in ET.fromstring(svg).iter("{http://www.w3.org/2000/svg}tspan") for char in "".join(text.itertext())}
        self.assertTrue(fallen <= set(source))

    def test_hostile_characters_cannot_inject_markup(self):
        svg = document(100, "x", rain_fragment("<b>&\"'", GRID), GRID.css, width=200, framed=False)
        ET.fromstring(svg)
        self.assertNotIn("<b>", svg)

    def test_opacity_scales_with_strength_and_the_lead_glyph_is_brightest(self):
        faint = rain_fragment("abcdefghij", RainGrid(200, 100, 20, 6, 10, 9, strength=0.5))
        strong = rain_fragment("abcdefghij", RainGrid(200, 100, 20, 6, 10, 9, strength=1.0))
        top = lambda text: max(float(v) for v in re.findall(r'fill-opacity="([\d.]+)"', text))
        self.assertLess(top(faint), top(strong))
        self.assertIn('class="rain-lead"', strong)

    def test_is_deterministic(self):
        self.assertEqual(rain_fragment("abcdef", GRID), rain_fragment("abcdef", GRID))


class Banner(WithAssets):
    def test_embeds_the_foreground_over_a_gradient_and_the_rain(self):
        svg = self.cards["banner"]
        self.assertIn("data:image/webp;base64,", svg)
        self.assertLess(svg.index('fill="url(#sky)"'), svg.index('class="drop"'))
        self.assertLess(svg.rindex('class="drop"'), svg.index("<image"))
        self.assertIn('width="1500" height="500"', svg)

    def test_rain_spells_the_repositories(self):
        text = "".join("".join(t.itertext()) for t in ET.fromstring(self.cards["banner"]).iter("{http://www.w3.org/2000/svg}tspan"))
        self.assertTrue(set(text) <= set(source_text(FIXTURE)))

    def test_rain_is_faint_so_the_wordmark_stays_readable(self):
        self.assertLessEqual(BANNER_GRID.strength, 0.6)
        self.assertLessEqual(max(float(v) for v in re.findall(r'fill-opacity="([\d.]+)"', self.cards["banner"])), 0.6)

    def test_pushes_do_not_change_the_banner_but_a_release_does(self):
        pushed = [make_repo("steady", created_days=30, pushed_days=1, tags=(("v1.9.0", 20),))]
        released = [make_repo("steady", created_days=30, pushed_days=14, tags=(("v2.0.0", 1), ("v1.9.0", 20)))]
        base = render_banner(FIXTURE[1:2], self.foreground)
        self.assertEqual(base, render_banner(pushed, self.foreground))
        self.assertNotEqual(base, render_banner(released, self.foreground))

    def test_all_four_edges_fade_to_transparent_so_there_is_no_border(self):
        svg = self.cards["banner"]
        for mask in ("fade-x", "fade-y"):
            self.assertIn(f'<mask id="{mask}"', svg)
            self.assertIn(f'mask="url(#{mask})"', svg)
            gradient = re.search(rf'<linearGradient id="{mask}-gradient"[^>]*>(.*?)</linearGradient>', svg).group(1)
            stops = re.findall(r'<stop offset="([\d.]+)" stop-color="#fff"(?: stop-opacity="([\d.]+)")?/>', gradient)
            self.assertEqual([(float(o), float(a or 1)) for o, a in stops][0], (0.0, 0.0))   # transparent at the start edge
            self.assertEqual([(float(o), float(a or 1)) for o, a in stops][-1], (1.0, 0.0))  # transparent at the end edge
            self.assertTrue(any(float(a or 1) == 1.0 for _, a in stops))                      # opaque in the middle
        self.assertLess(svg.index('mask="url(#fade-x)"'), svg.index('fill="url(#sky)"'))   # the fade wraps the whole picture

    def test_missing_foreground_fails_loudly(self):
        with self.assertRaises(FileNotFoundError):
            render_banner(FIXTURE, self.foreground.with_name("absent.webp"))


if __name__ == "__main__":
    unittest.main()
