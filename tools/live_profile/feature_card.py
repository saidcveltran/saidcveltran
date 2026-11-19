"""Building blocks shared by the project feature cards (Duckys, Resma).

A feature card is a borderless 820 x 208 banner: the project name and text on the left, and on the right a mark
that fades in from the middle of the card over a pastel panel that also appears from the middle. The left half is
transparent and the corners are square, so the card has no visible border on the page. The mark is any SVG fragment drawn inside the
square MARK_X, MARK_Y, MARK_BOX; the helpers here only light it and fade it.
"""
from __future__ import annotations

WIDTH, HEIGHT = 820, 208
MARK_X, MARK_Y, MARK_BOX = 530, 0, 208  # the square that holds the mark; it ends exactly on the card's bottom edge
FADE_FROM, FADE_TO = 470, 580  # the mark is invisible at FADE_FROM (a little right of the middle) and fully shown at FADE_TO
FADE_BOTTOM = 36  # height of the fade at the bottom edge, where the artwork is cut flat
PANEL_FROM, PANEL_FULL, PANEL_OPACITY = WIDTH // 2, 640, 0.9  # the pastel background: invisible at the middle, nearly solid from PANEL_FULL
CTA_TEXT = "Click to see the {name} project"
CTA_RULE_PER_CHARACTER = 7.4  # width of the underline per character of the 14 px call to action


def call_to_action(name: str, baseline: int = 180) -> str:
    """The call to action and its pulsing underline; the page CSS must define `.cta-line`."""
    text = CTA_TEXT.format(name=name)
    return (f'<text class="accent" x="0" y="{baseline}" font-size="14">{text}</text>'
            f'<rect class="accent cta-line" x="0" y="{baseline + 7}" width="{len(text) * CTA_RULE_PER_CHARACTER:.0f}" height="2"/>')


def panel(color: str) -> str:
    """A pastel background that starts transparent at the middle of the card and is solid from PANEL_FULL to the right edge.

    The corners stay square and nothing is drawn on the left half, so the card still melts into the page.
    """
    return (f'<defs><linearGradient id="panel-gradient" gradientUnits="userSpaceOnUse" x1="{PANEL_FROM}" x2="{PANEL_FULL}" y1="0" y2="0">'
            f'<stop offset="0" stop-color="{color}" stop-opacity="0"/><stop offset="1" stop-color="{color}" stop-opacity="{PANEL_OPACITY}"/></linearGradient></defs>'
            f'<rect x="{PANEL_FROM}" width="{WIDTH - PANEL_FROM}" height="{HEIGHT}" fill="url(#panel-gradient)"/>')


def faded_mark(artwork: str) -> str:
    """Wrap `artwork` in two masks: it appears from FADE_FROM to FADE_TO and fades out over its last FADE_BOTTOM pixels."""
    rise_from = HEIGHT - FADE_BOTTOM
    return ('<defs>'
            f'<linearGradient id="mark-appear" gradientUnits="userSpaceOnUse" x1="{FADE_FROM}" x2="{FADE_TO}" y1="0" y2="0">'
            '<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff"/></linearGradient>'
            f'<mask id="mark-fade-x" maskUnits="userSpaceOnUse" x="0" y="0" width="{WIDTH}" height="{HEIGHT}">'
            f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#mark-appear)"/></mask>'
            f'<linearGradient id="mark-sink" gradientUnits="userSpaceOnUse" x1="0" x2="0" y1="{rise_from}" y2="{HEIGHT}">'
            '<stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
            f'<mask id="mark-fade-y" maskUnits="userSpaceOnUse" x="0" y="0" width="{WIDTH}" height="{HEIGHT}">'
            f'<rect width="{WIDTH}" height="{rise_from}" fill="#fff"/>'
            f'<rect y="{rise_from}" width="{WIDTH}" height="{FADE_BOTTOM}" fill="url(#mark-sink)"/></mask>'
            '</defs>'
            f'<g mask="url(#mark-fade-x)"><g mask="url(#mark-fade-y)">{artwork}</g></g>')
