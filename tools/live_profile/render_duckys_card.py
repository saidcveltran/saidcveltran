"""Duckys feature card: the name large, the public figures, a call to action, and the mascot over a pastel panel.

The figures (servers and tracks played) are real. The faint bars dancing behind the text are decoration with
a fixed, hash-derived rhythm, so the card changes only when a figure changes. The mascot is a small transparent
WebP embedded in the SVG; see feature_card for how it fades in from the middle. Borderless, square corners.
"""
from __future__ import annotations

import base64
import hashlib
import math
from pathlib import Path

from .duckys_figures import Figures
from .feature_card import HEIGHT, MARK_BOX, MARK_X, MARK_Y, call_to_action, faded_mark, panel
from .svg_common import DISPLAY_ADVANCE, document, stamp

BARS, BAR_WIDTH, BAR_GAP = 41, 12, 8
BASELINE, MAX_HEIGHT = 204, 150
NAME_SIZE, FIGURE_SIZE = 66, 32
FIGURE_ADVANCE = FIGURE_SIZE * DISPLAY_ADVANCE
PANEL_COLOR = "#f7dcae"  # pastel amber: the Duckys site's accent (#ffb454 in its dark theme, #d87c03 in the light one), lightened
CSS = """
.bar { transform-box: fill-box; transform-origin: bottom; animation: dance ease-in-out infinite alternate; }
@keyframes dance { from { transform: scaleY(.16); } to { transform: scaleY(1); } }
.bar-a { fill: #3fb950; opacity: .20; } .bar-b { fill: #3fb950; opacity: .10; }
.cta-line { animation: cta 2.4s ease-in-out infinite alternate; }
@keyframes cta { from { opacity: .35; } to { opacity: 1; } }
@media (prefers-color-scheme: light) { .bar-a, .bar-b { fill: #1a7f37; } }
"""


def _unit(index: int, salt: str) -> float:
    return int(hashlib.sha256(f"{salt}{index}".encode()).hexdigest()[:6], 16) / 0x1000000


def bar_heights() -> list[float]:
    """A smooth envelope (two slow waves) so the resting shape already looks like a spectrum."""
    return [MAX_HEIGHT * (0.40 + 0.60 * abs(math.sin(i * 0.31) * math.cos(i * 0.11 + 0.8))) for i in range(BARS)]


def _bars() -> list[str]:
    bars = []
    for index, height in enumerate(bar_heights()):
        duration = 0.6 + _unit(index, "d") * 1.0
        delay = -_unit(index, "p") * duration
        bars.append(f'<rect class="bar {"bar-a" if index % 4 else "bar-b"}" style="animation-duration:{duration:.2f}s;animation-delay:{delay:.2f}s" '
                    f'x="{index * (BAR_WIDTH + BAR_GAP)}" y="{BASELINE - height:.1f}" width="{BAR_WIDTH}" height="{height:.1f}"/>')
    return bars


def _mascot(mark: Path) -> str:
    data = base64.b64encode(mark.read_bytes()).decode("ascii")
    return faded_mark(f'<image href="data:image/webp;base64,{data}" x="{MARK_X}" y="{MARK_Y}" width="{MARK_BOX}" height="{MARK_BOX}"/>')


def render_duckys_card(figures: Figures, now, mark: Path) -> str:
    servers, tracks = f"{figures.servers:,}+", f"{figures.tracks:,}+"
    servers_label_x = len(servers) * FIGURE_ADVANCE + 10
    tracks_x = servers_label_x + 62
    tracks_label_x = tracks_x + len(tracks) * FIGURE_ADVANCE + 10
    body = [
        *_bars(),  # drawn first: the panel, the mascot and the text sit on top of the bars
        panel(PANEL_COLOR),
        _mascot(mark),
        f'<text class="ink display" x="0" y="72" font-size="{NAME_SIZE}">DUCKYS</text>',
        '<text class="muted" x="2" y="98" font-size="12" letter-spacing="2.4">MUSIC BOT FOR DISCORD</text>',
        f'<text class="ink display" x="0" y="146" font-size="{FIGURE_SIZE}">{servers}</text>',
        f'<text class="muted" x="{servers_label_x:.0f}" y="146" font-size="14">servers</text>',
        f'<text class="ink display" x="{tracks_x:.0f}" y="146" font-size="{FIGURE_SIZE}">{tracks}</text>',
        f'<text class="muted" x="{tracks_label_x:.0f}" y="146" font-size="14">tracks played</text>',
        call_to_action("Duckys"),
        f'<text class="muted" x="0" y="{HEIGHT - 2}" font-size="9.5">Figures from the Duckys home page; the bars are only decoration · {stamp(now)}</text>',
    ]
    return document(HEIGHT, f"Duckys, a music bot for Discord: in {figures.servers:,}+ servers, {figures.tracks:,}+ tracks played", "\n".join(body), CSS, framed=False)
