"""The README header: a dark gradient, live falling code made of the repositories' names and versions,
and in front the animated artwork (glow, wordmark, cat head) as a transparent WebP embedded in the SVG,
with a few glowing motes drifting up through the light as native SVG animation.

The artwork is built once by tools/banner/build_banner_foreground.py and committed; only the rain is live.
An animated WebP inside an SVG shown as an image keeps animating in Chromium (checked on GitHub); a browser
that does not animate it shows the first frame. All four edges fade to transparent, so the header has no
visible border and melts into the page.
"""
from __future__ import annotations

import base64
from pathlib import Path

from .github_data import Repo
from .render_motes import CSS as MOTES_CSS
from .render_motes import render_motes
from .render_rain import RainGrid, rain_fragment, source_text
from .svg_common import document

WIDTH, HEIGHT = 1500, 500
FADE_X, FADE_Y = 140, 90  # width of the fade at the left and right edges, and at the top and bottom edges
GRID = RainGrid(width=WIDTH, height=HEIGHT, pitch=30, rows=16, row_step=20, font_size=15, strength=0.5)
SKY_TOP, SKY_BOTTOM = "#05080c", "#0d1216"


def _edge_mask(uid: str, horizontal: bool, fade: int) -> str:
    """A mask that is opaque in the middle and fades to transparent over `fade` pixels at both ends."""
    length = WIDTH if horizontal else HEIGHT
    inner = fade / length
    axis = 'x1="0" x2="1" y1="0" y2="0"' if horizontal else 'x1="0" x2="0" y1="0" y2="1"'
    return (f'<linearGradient id="{uid}-gradient" {axis}><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
            f'<stop offset="{inner:.4f}" stop-color="#fff"/><stop offset="{1 - inner:.4f}" stop-color="#fff"/>'
            '<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
            f'<mask id="{uid}" maskUnits="userSpaceOnUse" x="0" y="0" width="{WIDTH}" height="{HEIGHT}">'
            f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#{uid}-gradient)"/></mask>')


def render_banner(repos: list[Repo], foreground: Path) -> str:
    """Header SVG for the given repositories; `foreground` is the transparent animated WebP."""
    artwork = base64.b64encode(foreground.read_bytes()).decode("ascii")
    body = [
        f'<defs><linearGradient id="sky" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="{SKY_TOP}"/><stop offset="1" stop-color="{SKY_BOTTOM}"/></linearGradient>'
        f'{_edge_mask("fade-x", True, FADE_X)}{_edge_mask("fade-y", False, FADE_Y)}</defs>',
        '<g mask="url(#fade-x)"><g mask="url(#fade-y)">',
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#sky)"/>',
        rain_fragment(source_text(repos), GRID, uid="banner-rain"),
        f'<image href="data:image/webp;base64,{artwork}" x="0" y="0" width="{WIDTH}" height="{HEIGHT}"/>',
        render_motes(),  # native SVG, in front of the artwork: a lossy animated image would shimmer where they cross it
        "</g></g>",
    ]
    return document(HEIGHT, "saidcveltran.dev", "\n".join(body), GRID.css + MOTES_CSS, width=WIDTH, framed=False)
