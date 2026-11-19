"""The embedded fonts are small subsets: every drawn character must be inside them."""
from __future__ import annotations

import importlib.util
import unittest

from live_profile.glyph_ranges import RANGES, supported, unicodes, unsupported
from live_profile.render_repo_card import render_repo_card
from live_profile.render_title import render_title
from live_profile.svg_common import DISPLAY_FONT, FONT
from tests.fixtures import FIXTURE, NOW, drawn_text, make_repo

SIZE_BUDGET = 25_000  # bytes per embedded font


class GlyphRanges(unittest.TestCase):
    def test_helpers_agree(self):
        self.assertTrue(supported("a") and supported("é") and supported("…"))
        self.assertEqual(unsupported("a★b中"), {"★", "中"})
        self.assertEqual(len(unicodes()), sum(high - low + 1 for low, high in RANGES))

    def test_cards_with_real_looking_data_draw_only_supported_characters(self):
        accented = make_repo("herramientas-pdf", created_days=9, pushed_days=1, description="Herramientas PDF gratuitas en el navegador: unir PDF y JPG a PDF.")
        cards = {"title": render_title("Find me"), "title-symbols": render_title("C++ & Rust"), "accented": render_repo_card(accented, NOW)}
        cards.update({repo.name: render_repo_card(repo, NOW) for repo in FIXTURE})
        for name, svg in cards.items():
            with self.subTest(card=name):
                self.assertEqual(unsupported(drawn_text(svg)), set())

    def test_the_check_can_fail(self):
        self.assertEqual(unsupported(drawn_text('<svg xmlns="http://www.w3.org/2000/svg"><text>ok ★</text></svg>')), {"★"})

    def test_font_files_stay_small(self):
        for path in (FONT, DISPLAY_FONT):
            with self.subTest(font=path.name):
                self.assertLess(path.stat().st_size, SIZE_BUDGET)


@unittest.skipUnless(importlib.util.find_spec("fontTools"), "fontTools is only needed to build and verify the subsets")
class SubsetContents(unittest.TestCase):
    def test_subsets_contain_every_supported_character(self):
        from fontTools.ttLib import TTFont
        for path in (FONT, DISPLAY_FONT):
            with self.subTest(font=path.name):
                cmap = TTFont(str(path)).getBestCmap()
                self.assertEqual([hex(c) for c in unicodes() if c not in cmap], [])

    def test_display_font_is_monospaced_at_six_tenths(self):
        from fontTools.ttLib import TTFont
        font = TTFont(str(DISPLAY_FONT))
        advances = {font["hmtx"][name][0] / font["head"].unitsPerEm for name in font.getBestCmap().values() if name != ".notdef"}
        self.assertEqual({round(a, 3) for a in advances}, {0.6})


if __name__ == "__main__":
    unittest.main()
