"""Offline tests for the social icon buttons and the two-group Find me block."""
from __future__ import annotations

import re
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest import mock

from live_profile import render_socials
from live_profile.render_socials import (BUTTON, GROUPS, LABEL_FONT, LABEL_WIDTH, Link, button_name, group_label_name, load_glyph, render_button,
                                         render_group_label, render_social_links)
from live_profile.svg_common import DISPLAY_ADVANCE
from tests.fixtures import drawn_text

README_COLUMN, CELL_PADDING = 665, 26  # measured on GitHub: content width of the README, and the left and right padding of a table cell


class SocialButtons(unittest.TestCase):
    LINKS = [link for _, _, links in GROUPS for link in links]

    def test_every_button_is_a_small_square_with_a_glyph_and_nothing_external(self):
        for link in self.LINKS:
            with self.subTest(link=link.label):
                svg = render_button(link)
                root = ET.fromstring(svg)
                self.assertEqual((root.get("width"), root.get("height")), (str(BUTTON), str(BUTTON)))
                self.assertTrue('class="glyph"' in svg or 'class="globe"' in svg)
                self.assertIn("prefers-color-scheme: light", svg)
                self.assertNotRegex(svg, r'(href|src)="https?:')
                self.assertNotIn("<script", svg)
                self.assertLess(len(svg), 8_000)  # no fonts: they draw no text

    def test_buttons_draw_no_text_but_keep_name_and_handle_accessible(self):
        for link in self.LINKS:
            with self.subTest(link=link.label):
                svg = render_button(link)
                self.assertEqual(drawn_text(svg), "")
                self.assertIn(f"{link.label}: {link.handle}", svg)
        html = render_social_links("assets")
        self.assertIn('alt="X, @aiskaron"', html)
        self.assertIn(f'width="{BUTTON}" height="{BUTTON}"', html)

    def test_urls_are_https_and_file_names_are_unique(self):
        self.assertTrue(all(link.url.startswith("https://") for link in self.LINKS))
        names = [button_name(link) for link in self.LINKS]
        self.assertEqual(len(names), len(set(names)))

    def test_both_groups_are_rendered_with_their_links(self):
        html = render_social_links("assets")
        self.assertIn('alt="AIskaron (the projects)"', html)
        self.assertIn('alt="saidcveltran.dev (me)"', html)
        self.assertEqual(html.count("<td"), 2)  # side by side, one cell per group
        self.assertEqual(html.count("<tr>"), 1)
        for link in self.LINKS:
            self.assertIn(f'href="{link.url}"', html)

    def test_group_headings_are_fixed_width_so_two_of_them_fill_the_column(self):
        self.assertLessEqual(2 * (LABEL_WIDTH + CELL_PADDING) + 1, README_COLUMN)  # two padded cells and a border fit GitHub's README column
        self.assertGreater(2 * (LABEL_WIDTH + CELL_PADDING), 0.9 * README_COLUMN)  # and use most of it (GitHub ignores a table's width attribute)
        names = set()
        for title, note, _ in GROUPS:
            with self.subTest(group=title):
                svg = render_group_label(title, note)
                root = ET.fromstring(svg)
                self.assertEqual(root.get("width"), str(LABEL_WIDTH))
                self.assertIn(f">{title}<", svg)
                self.assertIn(f">{note}<", svg)
                names.add(group_label_name(title))
        self.assertEqual(len(names), len(GROUPS))

    def test_group_heading_text_stays_inside_its_width(self):
        for title, note, _ in GROUPS:
            end = len(title) * LABEL_FONT * DISPLAY_ADVANCE + 10 + len(note) * 12 * 0.62
            self.assertLess(end, LABEL_WIDTH, title)

    def test_group_heading_escapes_markup(self):
        svg = render_group_label("a<b>", "&x")
        ET.fromstring(svg)
        self.assertNotIn("a<b>", svg)

    def test_names_with_markup_characters_are_escaped(self):
        svg = render_button(Link("a<b>", "&x", "https://example.test", "globe"))
        ET.fromstring(svg)
        self.assertNotIn("a<b>", svg)

    def test_every_vendored_icon_has_a_viewbox_and_path_data(self):
        for link in self.LINKS:
            if link.icon == "globe":
                continue
            with self.subTest(icon=link.icon):
                view_box, paths = load_glyph(link.icon)
                self.assertEqual(len(view_box.split()), 4)
                self.assertTrue(all(d.strip() for d in paths))

    def test_missing_icon_fails_loudly(self):
        with self.assertRaises(FileNotFoundError):
            render_button(Link("Ghost", "@ghost", "https://example.test", "no-such-icon"))

    def test_icon_file_without_a_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, "empty.svg").write_text('<svg viewBox="0 0 24 24"></svg>', encoding="utf-8")
            with mock.patch.object(render_socials, "ICON_DIR", Path(folder)):
                with self.assertRaises(ValueError):
                    load_glyph("empty")


if __name__ == "__main__":
    unittest.main()
