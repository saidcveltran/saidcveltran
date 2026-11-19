"""Section title: large display type, a square accent block, a blinking terminal cursor and a light that travels along the rule.

Borderless and square-cornered, so it sits on the page like a heading. The text is the only input; the
cursor position is exact because the display font is monospaced (every glyph advances 0.6 em).
"""
from __future__ import annotations

from html import escape

from .svg_common import DISPLAY_ADVANCE, document

HEIGHT = 72
FONT_SIZE = 44
LEFT = 34
WIDTH = 820
CSS = f"""
.cursor {{ animation: blink 1.1s steps(1, end) infinite; }}
@keyframes blink {{ 50% {{ opacity: 0; }} }}
.light {{ animation: travel 5.5s cubic-bezier(.6, 0, .4, 1) infinite; }}
@keyframes travel {{ from {{ transform: translateX(-160px); }} to {{ transform: translateX({WIDTH}px); }} }}
.rule-fill {{ fill: #30363d; }}
@media (prefers-color-scheme: light) {{ .rule-fill {{ fill: #d1d9e0; }} }}
"""


def render_title(text: str) -> str:
    """One title card. Texts longer than the card allows are rejected instead of being cut."""
    advance = FONT_SIZE * DISPLAY_ADVANCE
    if not text.strip():
        raise ValueError("a title needs text")
    if LEFT + len(text) * advance + advance > WIDTH:
        raise ValueError(f"title too long for the card: {text!r}")
    cursor_x = LEFT + len(text) * advance + 4
    body = [
        '<rect class="accent" x="0" y="20" width="16" height="16"/>',
        f'<text class="ink display" x="{LEFT}" y="42" font-size="{FONT_SIZE}">{escape(text)}</text>',
        f'<rect class="accent cursor" x="{cursor_x:.1f}" y="36" width="{advance * 0.55:.1f}" height="6"/>',
        f'<rect class="rule-fill" x="0" y="58" width="{WIDTH}" height="1"/>',
        '<rect class="accent light" x="0" y="57" width="160" height="3"/>',
    ]
    return document(HEIGHT, text, "\n".join(body), CSS, framed=False)
