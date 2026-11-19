"""Offline tests for the repository model and for writing generated content without noise."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from live_profile.page_blocks import replace_block, write_if_changed
from tests.fixtures import FIXTURE, NOW


class RepositoryRules(unittest.TestCase):
    def test_states_follow_the_windows(self):
        self.assertEqual([repo.state(NOW) for repo in FIXTURE], ["ACTIVE", "STEADY", "QUIET"])

    def test_only_a_young_repository_is_new(self):
        self.assertEqual([repo.is_new(NOW) for repo in FIXTURE], [True, False, False])

    def test_latest_release_is_the_first_and_missing_releases_give_none(self):
        self.assertEqual(FIXTURE[0].latest.tag, "v0.1.1")
        self.assertIsNone(FIXTURE[2].latest)


class FileUpdates(unittest.TestCase):
    def test_write_if_changed_ignores_only_the_timestamp(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "card.svg"
            self.assertTrue(write_if_changed(path, "<t>updated 19 Nov 10:00 UTC</t>"))
            self.assertFalse(write_if_changed(path, "<t>updated 19 Nov 10:15 UTC</t>"))
            self.assertTrue(write_if_changed(path, "<t>updated 19 Nov 10:15 UTC v2</t>"))

    def test_replace_block_is_idempotent_and_rejects_missing_markers(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "page.md"
            path.write_text("top\n<!-- live:x:start -->\n<!-- live:x:end -->\nbottom\n", encoding="utf-8")
            self.assertTrue(replace_block(path, "x", "body"))
            self.assertFalse(replace_block(path, "x", "body"))
            self.assertIn("top", path.read_text(encoding="utf-8"))
            with self.assertRaises(ValueError):
                replace_block(path, "missing", "body")

    def test_block_names_are_matched_literally(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "p.md"
            path.write_text("<!-- live:a.b:start -->\n<!-- live:a.b:end -->\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                replace_block(path, "aXb", "x")
            self.assertTrue(replace_block(path, "a.b", "x"))
            self.assertFalse(replace_block(path, "a.b", "x"))


if __name__ == "__main__":
    unittest.main()
