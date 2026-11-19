"""Languages used across all of the owner's projects, public and private, kept as an anonymous ordered list.

The scheduled refresh cannot read private repositories (its token covers only this repository), so the list is
computed on the owner's machine by sync_languages.py and committed as data/languages.json. The file holds only
language names, most used first: no repository names, counts or sizes, so it reveals nothing about private work
beyond the languages themselves.
"""
from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable, Mapping
from pathlib import Path

SHARE_THRESHOLD = 0.01  # a language counts for a repository only when it is at least this share of the repository's code


def rank_languages(per_repository: Iterable[Mapping[str, int]], threshold: float = SHARE_THRESHOLD) -> list[str]:
    """Languages that reach `threshold` of at least one repository, ordered by how many repositories they reach,
    then by total code size, then by name. Build files and a few stray bytes (a 400-byte batch file) do not count."""
    repositories: Counter[str] = Counter()
    sizes: Counter[str] = Counter()
    for languages in per_repository:
        total = sum(languages.values())
        if total <= 0:
            continue
        for name, size in languages.items():
            if size / total >= threshold:
                repositories[name] += 1
                sizes[name] += size
    return sorted(repositories, key=lambda name: (-repositories[name], -sizes[name], name))


def save_languages(path: Path, languages: list[str], generated: str) -> bool:
    """Write the list; returns False and leaves the file untouched when the languages did not change."""
    if load_languages(path) == languages:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"generated": generated, "languages": languages}, indent=2) + "\n", encoding="utf-8")
    return True


def load_languages(path: Path) -> list[str]:
    """The stored list, or an empty one when the file does not exist yet."""
    if not path.exists():
        return []
    languages = json.loads(path.read_text(encoding="utf-8")).get("languages", [])
    if not isinstance(languages, list) or not all(isinstance(name, str) for name in languages):
        raise ValueError(f"{path}: 'languages' must be a list of names")
    return languages
