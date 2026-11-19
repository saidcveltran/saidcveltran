"""Offline tests for the rising motes: native SVG animation, deterministic, and kept out of the animated WebP."""
from __future__ import annotations

import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from live_profile.render_banner import render_banner
from live_profile.render_motes import CSS, GLOW_RADIUS_FACTOR, LAP_SECONDS, MOTE_COUNT, REGION, make_motes, render_motes
from live_profile.svg_common import document
from tests.fixtures import FIXTURE

FOREGROUND_BUILDER = Path(__file__).resolve().parents[1] / "banner" / "build_banner_foreground.py"


class Motes(unittest.TestCase):
    def test_the_field_is_deterministic_and_complete(self):
        self.assertEqual(make_motes(), make_motes())
        self.assertEqual(len(make_motes()), MOTE_COUNT)
        self.assertEqual(render_motes(), render_motes())
        self.assertNotEqual(make_motes(seed=1), make_motes(seed=2))

    def test_every_mote_starts_inside_the_region_and_is_a_soft_glow_not_a_hard_disc(self):
        x0, y0, x1, y1 = REGION
        for mote in make_motes():
            self.assertTrue(x0 <= mote.x <= x1 and y0 <= mote.start_y <= y1)
            self.assertTrue(0.3 <= mote.strength <= 0.9)
        svg = render_motes()
        self.assertEqual(svg.count("<circle"), MOTE_COUNT)
        self.assertEqual(svg.count('fill="url(#mote-glow)"'), MOTE_COUNT)
        self.assertRegex(svg, r'<stop offset="1" stop-color="#[0-9a-f]{6}" stop-opacity="0"/>')  # the glow fades to nothing

    def test_each_mote_loops_by_itself_and_starts_part_of_the_way_up(self):
        delays = [float(v) for v in re.findall(r"animation-delay:(-?[\d.]+)s;?\"><g class=\"mote-sway\"", render_motes())]
        self.assertEqual(len(delays), MOTE_COUNT)
        self.assertTrue(all(delay <= 0 for delay in delays))  # negative: the field is already moving when the page opens
        durations = [float(v) for v in re.findall(r"mote-rise\" style=\"--travel:-\d+px;animation-duration:([\d.]+)s", render_motes())]
        self.assertTrue(all(0.5 * LAP_SECONDS <= d <= 1.5 * LAP_SECONDS * (1 + 2 * GLOW_RADIUS_FACTOR * 5 / 500) for d in durations))
        self.assertIn("infinite", CSS)

    def test_the_banner_carries_the_motes_in_front_of_the_artwork(self):
        banner = render_banner(FIXTURE, Path(__file__).with_name("__init__.py"))
        ET.fromstring(banner)
        self.assertEqual(banner.count("<circle"), MOTE_COUNT)
        self.assertIn("@keyframes mote-rise", banner)
        self.assertLess(banner.index("<image"), banner.index('class="mote-rise"'))

    def test_motes_are_well_formed_inside_a_document_and_respect_reduced_motion(self):
        svg = document(500, "x", render_motes(), CSS, width=1500, framed=False)
        ET.fromstring(svg)
        self.assertIn("prefers-reduced-motion", svg)

    def test_regression_guard_the_animated_webp_must_not_contain_motes(self):
        """Motes inside a lossy animated WebP made the light around the cat's head shimmer (alpha std 3-5 per pixel)."""
        source = FOREGROUND_BUILDER.read_text(encoding="utf-8")
        self.assertNotIn("def draw_motes", source)
        self.assertNotIn("mote_specs", source)


if __name__ == "__main__":
    unittest.main()
