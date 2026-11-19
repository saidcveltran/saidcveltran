"""Offline tests for the Duckys figures parser and its rounding policy."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from live_profile.duckys_figures import Figures, parse_figures
from live_profile.render_duckys_card import render_duckys_card
from tests.fixtures import NOW

PAGE = """<dl class="home-figures">
<div class="home-figures__item"><dt>Servers</dt><dd class="home-figures__value">1,340</dd></div>
<div class="home-figures__item">
  <dt>Tracks played</dt>
  <dd class="home-figures__value">394,271</dd>
</div></dl>"""


class ParseFigures(unittest.TestCase):
    def test_reads_both_numbers(self):
        self.assertEqual(parse_figures(PAGE), Figures(1340, 394271))

    def test_changed_markup_returns_none(self):
        self.assertIsNone(parse_figures("<div>Servers 1,340</div>"))
        self.assertIsNone(parse_figures(""))

    def test_a_single_figure_is_not_enough(self):
        self.assertIsNone(parse_figures('<dt>Servers</dt><dd class="x">1,340</dd>'))

    def test_a_non_numeric_value_is_not_a_figure(self):
        self.assertIsNone(parse_figures("<dt>Servers</dt><dd>many</dd><dt>Tracks played</dt><dd>lots</dd>"))


class Rounding(unittest.TestCase):
    def test_rounding_goes_down_and_never_overstates(self):
        real = Figures(1349, 394999)
        rounded = real.rounded()
        self.assertEqual(rounded, Figures(1340, 390000))
        self.assertTrue(rounded.servers <= real.servers and rounded.tracks <= real.tracks)

    def test_rounding_is_idempotent_so_small_changes_do_not_redraw_the_card(self):
        self.assertEqual(Figures(1349, 394999).rounded().rounded(), Figures(1349, 394999).rounded())
        self.assertEqual(Figures(1341, 390001).rounded(), Figures(1349, 394999).rounded())

    def test_the_card_shows_the_rounded_numbers_it_is_given(self):
        with tempfile.TemporaryDirectory() as folder:
            mark = Path(folder, "mark.webp")
            mark.write_bytes(b"RIFF")
            svg = render_duckys_card(Figures(1349, 394999).rounded(), NOW, mark)
        self.assertIn(">1,340+<", svg)
        self.assertIn(">390,000+<", svg)
        self.assertNotIn("394,999", svg)


if __name__ == "__main__":
    unittest.main()
