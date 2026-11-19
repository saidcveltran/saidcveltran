"""Code rain made of real data: falling columns spell out the repository names and versions.

Same idea as the classic terminal rain, but the characters are not random: they are read, column by
column, from the public releases. Columns fall at different speeds and fade towards the top and the
bottom. The layout is fixed by the text, so the rain changes only when the data does.
`rain_fragment` returns SVG content to be placed inside a card; render_banner.py uses it as the banner background.
"""
from __future__ import annotations

from dataclasses import dataclass
from html import escape

from .github_data import Repo
from .svg_common import short_date

FALLBACK = "NO_PUBLIC_RELEASES_YET"


@dataclass(frozen=True)
class RainGrid:
    """Geometry of one rain field. Every length is in SVG user units (pixels of the card)."""
    width: int
    height: int
    pitch: int  # distance between columns
    rows: int  # characters per column
    row_step: int  # distance between characters
    font_size: int
    strength: float = 1.0  # overall opacity, 0..1

    @property
    def columns(self) -> int:
        return self.width // self.pitch

    @property
    def css(self) -> str:
        return (f".drop {{ animation: fall linear infinite; }}\n"
                f"@keyframes fall {{ from {{ transform: translateY(-{self.rows * self.row_step}px); }} to {{ transform: translateY({self.height}px); }} }}\n"
                ".rain-glyph { fill: #3fb950; } .rain-lead { fill: #e6edf3; }")


def source_text(repos: list[Repo], *, with_dates: bool = False) -> str:
    """One long string of the real facts: name and latest version of each repository, optionally the last push date.

    Dates change with every push, names and versions only with a release; the banner uses the stable form.
    """
    parts = []
    for repo in repos:
        parts += [repo.name, repo.latest.tag if repo.latest else "-"]
        if with_dates:
            parts.append(short_date(repo.pushed))
    return "_".join(parts).replace(" ", "_") or FALLBACK


def column_text(source: str, index: int, rows: int) -> str:
    """The characters of one column: a window of the source, shifted per column, wrapping around."""
    start = (index * 7) % len(source)
    doubled = source * (rows // len(source) + 2)
    return doubled[start:start + rows]


def rain_fragment(source: str, grid: RainGrid, uid: str = "rain") -> str:
    """SVG content (defs, mask and the falling columns) for one rain field; needs grid.css and the display font."""
    mask = (f'<defs><linearGradient id="{uid}-fade" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
            f'<stop offset=".25" stop-color="#fff"/><stop offset=".75" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
            f'<mask id="{uid}-mask"><rect width="{grid.width}" height="{grid.height}" fill="url(#{uid}-fade)"/></mask></defs>')
    drops = []
    for index in range(grid.columns):
        duration = 7 + (index * 37 % 9)  # 7..15 s, fixed per column
        delay = -((index * 53) % (duration * 10)) / 10
        chars = column_text(source, index, grid.rows)
        tspans = []
        for row, char in enumerate(chars):
            lead = row == len(chars) - 1  # the lead glyph is the brightest and sits at the bottom of the falling column
            opacity = grid.strength * (0.18 + 0.82 * row / max(len(chars) - 1, 1))
            tspans.append(f'<tspan class="{"rain-lead" if lead else "rain-glyph"}" x="0" dy="{grid.row_step}" fill-opacity="{opacity:.2f}">{escape(char)}</tspan>')
        # The column position sits on an outer group: a CSS animation on `transform` would replace it.
        drops.append(f'<g transform="translate({index * grid.pitch + 4} 0)"><g class="drop" style="animation-duration:{duration}s;animation-delay:{delay:.1f}s">'
                     f'<text class="display" y="0" font-size="{grid.font_size}">{"".join(tspans)}</text></g></g>')
    return mask + f'<g mask="url(#{uid}-mask)">' + "".join(drops) + "</g>"
