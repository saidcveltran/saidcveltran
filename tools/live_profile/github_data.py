"""Read-only access to the public GitHub API: repositories and their releases.

Only public data of one account is read, and only versions and dates: commit messages are never
fetched, so nothing internal can reach the profile. Forks, archived repositories and a configurable
exclusion list are skipped. Standard library only; set GITHUB_TOKEN to raise the API rate limit.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

API = "https://api.github.com"
NEW_WINDOW = timedelta(days=7)
ACTIVE_WINDOW = timedelta(days=7)
STEADY_WINDOW = timedelta(days=60)


@dataclass(frozen=True)
class Release:
    tag: str
    published: datetime


@dataclass(frozen=True)
class Repo:
    name: str
    language: str
    created: datetime
    pushed: datetime
    releases: tuple[Release, ...]  # newest first
    description: str = ""

    @property
    def latest(self) -> Release | None:
        return self.releases[0] if self.releases else None

    def is_new(self, now: datetime) -> bool:
        return now - self.created < NEW_WINDOW

    def state(self, now: datetime) -> str:
        """ACTIVE when pushed in the last week, STEADY within two months, otherwise QUIET."""
        age = now - self.pushed
        return "ACTIVE" if age <= ACTIVE_WINDOW else "STEADY" if age <= STEADY_WINDOW else "QUIET"


def _get(path: str) -> object | None:
    """GET a path and parse the JSON body; a 404 or 409 (no release, empty repository) returns None."""
    request = urllib.request.Request(API + path, headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-live-data"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        if error.code in (404, 409):
            return None
        raise


def _time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def fetch_total_public(user: str) -> int:
    profile = _get(f"/users/{user}") or {}
    return int(profile.get("public_repos", 0))


def fetch_repos(user: str, *, limit: int, exclude: frozenset[str]) -> list[Repo]:
    """The `limit` most recently pushed original public repositories with their release history."""
    listing = _get(f"/users/{user}/repos?type=owner&sort=pushed&per_page=100") or []
    repos: list[Repo] = []
    for item in listing:
        if item["fork"] or item["archived"] or item["name"] in exclude:
            continue
        published = _get(f"/repos/{user}/{item['name']}/releases?per_page=12") or []
        releases = tuple(Release(r["tag_name"], _time(r["published_at"])) for r in published if not r["draft"] and r["published_at"])
        repos.append(Repo(
            name=item["name"],
            language=item.get("language") or "",
            created=_time(item["created_at"]),
            pushed=_time(item["pushed_at"]),
            releases=releases,
            description=(item.get("description") or "").strip(),
        ))
        if len(repos) == limit:
            break
    return repos


def utc_now() -> datetime:
    return datetime.now(timezone.utc)

