"""Where the live profile lives. Switching from the test bench to the real profile changes only this file."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
USER = "saidcveltran"
REPO = "saidcveltran"  # the profile repository: github.com/<USER>/<USER>
PAGE = ROOT / "README.md"  # the real profile README
ASSETS_URL = "assets"  # relative to PAGE
LANGUAGES_FILE = ROOT / "data" / "languages.json"  # written by sync_languages on the owner's machine, read by the refresh
EXCLUDED_REPOS = frozenset({USER, REPO})
