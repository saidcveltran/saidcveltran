"""Shared fixtures for the offline tests: a fixed clock and three repositories in different states."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

from live_profile.github_data import Release, Repo

NOW = datetime(2026, 11, 19, 0, 0, tzinfo=timezone.utc)
SVG_NS = "{http://www.w3.org/2000/svg}"


def make_repo(name: str, *, created_days: int, pushed_days: float, tags: tuple[tuple[str, int], ...] = (), description: str = "", language: str = "Rust") -> Repo:
    """A repository created and pushed the given number of days before NOW, with releases tagged (tag, age in days)."""
    releases = tuple(Release(tag, NOW - timedelta(days=age)) for tag, age in tags)
    return Repo(name, language, NOW - timedelta(days=created_days), NOW - timedelta(days=pushed_days), releases, description)


FIXTURE = [
    make_repo("fresh", created_days=2, pushed_days=0.1, tags=(("v0.1.1", 1), ("v0.1.0", 1)), description="Fresh <tool> & more"),
    make_repo("steady", created_days=30, pushed_days=14, tags=(("v1.9.0", 20),)),
    make_repo("quiet", created_days=200, pushed_days=120),
]


def drawn_text(svg: str) -> str:
    """Everything a card actually draws: the content of its <text> elements."""
    return "".join("".join(node.itertext()) for node in ET.fromstring(svg).iter(f"{SVG_NS}text"))
