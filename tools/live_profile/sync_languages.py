"""Recompute data/languages.json from every repository the authenticated account owns, private ones included.

Usage (on the owner's machine, with a token that can read private repositories):
    GITHUB_TOKEN="$(gh auth token)" python -m live_profile.sync_languages        (run from the tools directory)

Forks are skipped (their code is not the owner's); archived repositories count. Nothing but language names is stored.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

from . import config
from .github_data import _get
from .language_stats import rank_languages, save_languages

PAGE_SIZE = 100


def fetch_language_sizes() -> list[dict[str, int]]:
    """Bytes per language for each owned original repository, public and private."""
    listing = _get(f"/user/repos?affiliation=owner&per_page={PAGE_SIZE}") or []
    if len(listing) == PAGE_SIZE:
        raise RuntimeError("more than one page of repositories: add pagination before trusting this list")
    return [_get(f"/repos/{item['full_name']}/languages") or {} for item in listing if not item["fork"]]


def main() -> int:
    if not os.environ.get("GITHUB_TOKEN"):
        print("error: set GITHUB_TOKEN to a token that can read private repositories", file=sys.stderr)
        return 2
    sizes = fetch_language_sizes()
    languages = rank_languages(sizes)
    changed = save_languages(config.LANGUAGES_FILE, languages, datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    print("changed" if changed else "unchanged", f"({len(sizes)} repositories, {len(languages)} languages: {', '.join(languages)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
