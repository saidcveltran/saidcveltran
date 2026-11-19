"""Glowing motes that rise through the banner's light, drawn as native SVG animation.

They used to be painted into the animated WebP, but a lossy animated image re-encodes the whole area they cross
in every frame, and the soft light around the cat's head then shimmered. As SVG circles with a radial-gradient
glow they cost no raster at all, and the artwork stays static except for the lenses and the cursor.
Each mote rises linearly and loops by itself; a negative delay starts it part of the way up, so the whole field
is already in motion when the page opens. Positions and speeds come from a fixed seed, so the output is stable.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

REGION = (900, 0, 1500, 500)  # x0, y0, x1, y1: where the motes drift (the light around the cat)
MOTE_COUNT = 16
LAP_SECONDS = 3.0  # time for a mote with laps=1 to rise through the whole region; laps=2 is twice as fast
SWAY = 6  # sideways drift in pixels, each way
GLOW_COLOR = "#5fe296"
GLOW_RADIUS_FACTOR = 2.2  # the glow reaches this many times the mote's core radius
OPACITY_FACTOR = 0.55
CSS = f"""
.mote-rise {{ animation: mote-rise linear infinite; }}
.mote-sway {{ animation: mote-sway ease-in-out infinite alternate; }}
@keyframes mote-rise {{ from {{ transform: translateY(0); }} to {{ transform: translateY(var(--travel)); }} }}
@keyframes mote-sway {{ from {{ transform: translateX(-{SWAY}px); }} to {{ transform: translateX({SWAY}px); }} }}
"""


@dataclass(frozen=True)
class Mote:
    x: float
    start_y: float  # where the mote is at time zero
    radius: float
    laps: int  # 1 = LAP_SECONDS for the full height, 2 = twice as fast
    strength: float


def make_motes(seed: int = 11) -> list[Mote]:
    rng = random.Random(seed)
    x0, y0, x1, y1 = REGION
    return [Mote(rng.uniform(x0, x1 - 30), rng.uniform(y0, y1), rng.uniform(2.0, 5.0), rng.choice((1, 1, 2)), rng.uniform(0.35, 0.8))
            for _ in range(MOTE_COUNT)]


def _mote(mote: Mote) -> str:
    _, top, _, bottom = REGION
    margin = mote.radius * GLOW_RADIUS_FACTOR
    entry_y = bottom + margin  # every mote enters below the region and leaves above it
    travel = entry_y - (top - margin)
    duration = LAP_SECONDS / mote.laps * travel / (bottom - top)
    delay = -duration * (entry_y - mote.start_y) / travel  # start the loop already part of the way up
    sway_duration = duration / 2
    sway_delay = -(mote.x % sway_duration)
    return (f'<g class="mote-rise" style="--travel:-{travel:.0f}px;animation-duration:{duration:.2f}s;animation-delay:{delay:.2f}s">'
            f'<g class="mote-sway" style="animation-duration:{sway_duration:.2f}s;animation-delay:{sway_delay:.2f}s">'
            f'<circle cx="{mote.x:.0f}" cy="{entry_y:.0f}" r="{margin:.1f}" fill="url(#mote-glow)" fill-opacity="{mote.strength * OPACITY_FACTOR:.2f}"/>'
            '</g></g>')


def render_motes(motes: list[Mote] | None = None) -> str:
    """SVG fragment: the glow gradient and the animated circles. The document's style must include CSS."""
    motes = make_motes() if motes is None else motes
    gradient = (f'<defs><radialGradient id="mote-glow"><stop offset="0" stop-color="{GLOW_COLOR}"/>'
                f'<stop offset=".45" stop-color="{GLOW_COLOR}" stop-opacity=".55"/><stop offset="1" stop-color="{GLOW_COLOR}" stop-opacity="0"/></radialGradient></defs>')
    return gradient + "".join(_mote(mote) for mote in motes)
