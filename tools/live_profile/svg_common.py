"""Shared pieces of the live SVG cards: the embedded font, the dark and light palettes and the document frame.

GitHub serves README images through a proxy that runs no script and loads nothing external, so each
card carries its own font (as a data URI), its own CSS and its own animation, and switches between
dark and light with a prefers-color-scheme media query inside the SVG.
"""
from __future__ import annotations

import base64
import re
from html import escape
from pathlib import Path

FONT = Path(__file__).resolve().parent.parent / "fonts" / "inter-600-subset.woff2"
DISPLAY_FONT = Path(__file__).resolve().parent.parent / "fonts" / "jetbrains-mono-800-subset.woff2"
DISPLAY_ADVANCE = 0.6  # JetBrains Mono: every glyph advances 0.6 em, so text width is exact
WIDTH = 820


def slug(text: str) -> str:
    """File-name safe form of a name: lower case, letters and digits, single hyphens."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
MONO = 'ui-monospace, "Cascadia Mono", Consolas, "SF Mono", Menlo, monospace'

PALETTE_CSS = """
.surface { fill: #0d1117; } .surface-alt { fill: #161b22; } .frame { fill: none; stroke: #30363d; }
.ink { fill: #e6edf3; } .muted { fill: #8b949e; } .accent { fill: #3fb950; } .on-accent { fill: #0d1117; }
.rule { stroke: #30363d; } .accent-line { stroke: #3fb950; fill: none; } .accent-ring { stroke: #3fb950; fill: none; }
@media (prefers-color-scheme: light) {
  .surface { fill: #ffffff; } .surface-alt { fill: #f6f8fa; } .frame { stroke: #d1d9e0; }
  .ink { fill: #1f2328; } .muted { fill: #59636e; } .accent { fill: #1a7f37; } .on-accent { fill: #ffffff; }
  .rule { stroke: #d1d9e0; } .accent-line, .accent-ring { stroke: #1a7f37; }
}
"""


def clip(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def document(height: int, title: str, body: str, css: str = "", *, width: int = WIDTH, framed: bool = True, fonts: bool = True) -> str:
    """Wrap card content in an <svg> with the embedded fonts, the palette and a reduced-motion guard.

    framed=True draws the rounded card (surface and border). framed=False leaves the background transparent
    and the corners square, so the card sits directly on the page like any other piece of the README.
    Titles and figures use `<text class="display">`, set in the embedded display font. fonts=False leaves both
    fonts out, for cards that draw no text (icon buttons), which keeps them a few hundred bytes.
    """
    font_rules = _font_rules() if fonts else ""
    frame = (f'<rect class="surface" x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="10"/>\n'
             f'<rect class="frame" x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="10"/>\n') if framed else ""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">
<title>{escape(title)}</title>
<style>
{font_rules}{PALETTE_CSS}{css}
@media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
</style>
{frame}{body}
</svg>
"""


def short_date(moment) -> str:
    """Calendar date in UTC, e.g. '19 Nov'."""
    return f"{moment.day} {MONTHS[moment.month - 1]}"


def ago(moment, now) -> str:
    """Compact relative age: '12 min', '3 h', '5 d'."""
    seconds = max(0, int((now - moment).total_seconds()))
    if seconds < 3600:
        return f"{max(1, seconds // 60)} min"
    if seconds < 86400:
        return f"{seconds // 3600} h"
    return f"{seconds // 86400} d"


def stamp(now) -> str:
    return f"updated {now.day} {MONTHS[now.month - 1]} {now:%H:%M} UTC"


def _font_rules() -> str:
    """CSS for the two embedded fonts: body text (Inter) and `.display` titles and figures (JetBrains Mono)."""
    body = base64.b64encode(FONT.read_bytes()).decode("ascii")
    display = base64.b64encode(DISPLAY_FONT.read_bytes()).decode("ascii")
    return (f'@font-face {{ font-family: "Inter Embedded"; font-weight: 600; src: url(data:font/woff2;base64,{body}) format("woff2"); }}\n'
            f'@font-face {{ font-family: "JetBrains Embedded"; font-weight: 800; src: url(data:font/woff2;base64,{display}) format("woff2"); }}\n'
            'text { font-family: "Inter Embedded", "Segoe UI", Helvetica, Arial, sans-serif; font-weight: 600; font-variant-numeric: tabular-nums; }\n'
            f'text.display {{ font-family: "JetBrains Embedded", {MONO}; font-weight: 800; letter-spacing: -.01em; }}\n')
