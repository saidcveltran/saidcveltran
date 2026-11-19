"""Public figures of the Duckys home page: servers and tracks played.

The page has no JSON endpoint, so the two numbers are read from the server-rendered "home-figures" list.
Nothing else is read. When the markup changes the parser returns None and the caller keeps the last card,
instead of publishing a wrong number.
"""
from __future__ import annotations

import re
import urllib.request
from dataclasses import dataclass

HOME_URL = "https://duckys.aiskaron.com/"
_FIGURE = re.compile(r"<dt>\s*(Servers|Tracks played)\s*</dt>\s*<dd[^>]*>\s*([\d.,]+)\s*</dd>", re.I)


@dataclass(frozen=True)
class Figures:
    servers: int
    tracks: int

    def rounded(self) -> "Figures":
        """Round down (servers to tens, tracks to five thousands) so the card changes a few times a day, not every run."""
        return Figures(self.servers // 10 * 10, self.tracks // 5000 * 5000)


def parse_figures(html: str) -> Figures | None:
    found = {label.lower(): int(re.sub(r"\D", "", value)) for label, value in _FIGURE.findall(html)}
    if set(found) != {"servers", "tracks played"}:
        return None
    return Figures(found["servers"], found["tracks played"])


def fetch_figures(url: str = HOME_URL) -> Figures | None:
    """GET the home page; None on any network error or unrecognised markup."""
    request = urllib.request.Request(url, headers={"User-Agent": "profile-live-data", "Accept": "text/html"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return parse_figures(response.read().decode("utf-8", "replace"))
    except OSError:
        return None
