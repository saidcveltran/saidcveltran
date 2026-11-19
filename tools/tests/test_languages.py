"""Offline tests for the language ranking, its anonymous storage and the icon-only Languages row."""
from __future__ import annotations

import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from live_profile.language_stats import SHARE_THRESHOLD, load_languages, rank_languages, save_languages
from live_profile.render_languages import ICONS, NOTE, icon_name, render_language_icon, render_language_row, split_by_icon
from live_profile.render_socials import BUTTON, ICON_DIR
from tests.fixtures import drawn_text

REPOSITORIES = [  # bytes per language, shaped like the GitHub API answer
    {"Rust": 836960, "Python": 34745, "JavaScript": 19667, "CSS": 17444, "HTML": 6823},
    {"Python": 16864401, "JavaScript": 642389, "HTML": 572865, "CSS": 423586, "Batchfile": 386, "Just": 13107},
    {"JavaScript": 55309, "CSS": 22371},
    {},  # an empty repository contributes nothing and must not divide by zero
]


class RankLanguages(unittest.TestCase):
    def test_orders_by_repositories_reached_then_size(self):
        self.assertEqual(rank_languages(REPOSITORIES)[:4], ["JavaScript", "CSS", "Python", "Rust"])

    def test_stray_bytes_do_not_count(self):
        ranked = rank_languages(REPOSITORIES)
        self.assertNotIn("Batchfile", ranked)  # 386 bytes next to 19 MB
        self.assertNotIn("Just", ranked)  # 0.07 % of its repository

    def test_a_language_reaching_the_threshold_in_one_repository_is_kept(self):
        self.assertIn("Shell", rank_languages([{"Python": 97_000, "Shell": 3_000}, {"Python": 1_000}]))
        self.assertNotIn("Shell", rank_languages([{"Python": 99_500, "Shell": 500}]))

    def test_threshold_is_inclusive_and_configurable(self):
        self.assertIn("B", rank_languages([{"A": 99, "B": 1}], threshold=0.01))
        self.assertNotIn("B", rank_languages([{"A": 99, "B": 1}], threshold=0.02))
        self.assertEqual(SHARE_THRESHOLD, 0.01)

    def test_ties_resolve_by_name_so_the_file_never_flaps(self):
        self.assertEqual(rank_languages([{"B": 10}, {"A": 10}]), ["A", "B"])
        self.assertEqual(rank_languages([{"A": 10, "B": 10}]), rank_languages([{"B": 10, "A": 10}]))

    def test_no_repositories_means_no_languages(self):
        self.assertEqual(rank_languages([]), [])
        self.assertEqual(rank_languages([{}]), [])


class Storage(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name, "data", "languages.json")

    def test_round_trip_and_no_rewrite_when_unchanged(self):
        self.assertTrue(save_languages(self.path, ["Python", "Rust"], "2026-11-19"))
        self.assertEqual(load_languages(self.path), ["Python", "Rust"])
        self.assertFalse(save_languages(self.path, ["Python", "Rust"], "2026-11-20"))  # the date alone is not a change
        self.assertIn("2026-11-19", self.path.read_text(encoding="utf-8"))

    def test_the_file_holds_only_language_names(self):
        save_languages(self.path, rank_languages(REPOSITORIES), "2026-11-19")
        stored = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(set(stored), {"generated", "languages"})
        self.assertTrue(all(isinstance(name, str) for name in stored["languages"]))

    def test_missing_file_is_empty_and_malformed_data_is_rejected(self):
        self.assertEqual(load_languages(self.path), [])
        self.path.parent.mkdir(parents=True)
        self.path.write_text(json.dumps({"languages": [1, 2]}), encoding="utf-8")
        with self.assertRaises(ValueError):
            load_languages(self.path)


class LanguageRow(unittest.TestCase):
    def test_every_mapped_language_has_a_vendored_logo(self):
        for language, stem in ICONS.items():
            with self.subTest(language=language):
                self.assertTrue((ICON_DIR / f"{stem}.svg").exists())

    def test_icon_is_a_text_free_square_that_keeps_the_name_accessible(self):
        for language in ICONS:
            with self.subTest(language=language):
                svg = render_language_icon(language)
                root = ET.fromstring(svg)
                self.assertEqual((root.get("width"), root.get("height")), (str(BUTTON), str(BUTTON)))
                self.assertEqual(drawn_text(svg), "")
                self.assertIn(f"{language}: {NOTE}", svg)

    def test_row_has_images_only_no_links_and_no_visible_text(self):
        html = render_language_row(["Python", "Rust"], "assets")
        self.assertEqual(html.count("<img"), 2)
        self.assertNotIn("<a ", html)
        self.assertIn('alt="Python" title="Python"', html)
        self.assertIn('src="assets/language-python.svg"', html)
        self.assertEqual(render_language_row([], "assets"), "")

    def test_languages_without_a_logo_are_split_out_not_invented(self):
        shown, missing = split_by_icon(["Python", "Brainfuck", "Rust", "Whitespace"])
        self.assertEqual(shown, ["Python", "Rust"])
        self.assertEqual(missing, ["Brainfuck", "Whitespace"])
        self.assertNotIn("Brainfuck", render_language_row(["Python", "Brainfuck"], "assets"))

    def test_file_names_are_unique_and_safe(self):
        names = [icon_name(language) for language in ICONS]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(icon_name("Go Template"), "language-go-template.svg")

    def test_a_hostile_language_name_from_the_data_file_never_reaches_the_page(self):
        """Only names with a vendored logo are drawn, so markup in the data file cannot be injected."""
        self.assertEqual(render_language_row(['x"><script>alert(1)</script>'], "assets"), "")
        self.assertEqual(split_by_icon(['x"><script>'])[0], [])


if __name__ == "__main__":
    unittest.main()
