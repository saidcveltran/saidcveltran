"""Resma feature card: the name, what the tool does, a call to action, and the paper sheets over a pastel panel.

Resma has no public counter, so the card states only what the product does and nothing live; it never changes.
The mark is the two sheets of Resma's own icon, drawn as vector paths without the app icon's rounded square, so
the card keeps square corners. The back sheet drifts up and down, like pages being merged.
"""
from __future__ import annotations

from .feature_card import HEIGHT, MARK_X, MARK_Y, call_to_action, faded_mark, panel
from .svg_common import document

URL = "https://resma.aiskaron.com"
PANEL_COLOR = "#c9e9e4"  # pastel teal: the Resma site's #0f766e, lightened (a little lighter than its icon's pale sheet, so the dark sheets read)
SHEETS_SCALE = 0.25  # the icon's sheets span 660 x 800 units; at this scale they fill the card's height
SHEETS_ORIGIN = (170, 100)  # top-left corner of the sheets inside the icon's 1000-unit drawing
SHEET_FRONT, SHEET_BACK, SHEET_FOLD = "#0f766e", "#4fa398", "#0a5550"  # the site's teal and two shades of it: dark enough to stand out on the pastel panel
CSS = """
.sheet-back { animation: drift 3.2s ease-in-out infinite alternate; }
@keyframes drift { from { transform: translateY(0); } to { transform: translateY(56px); } }
.cta-line { animation: cta 2.4s ease-in-out infinite alternate; }
@keyframes cta { from { opacity: .35; } to { opacity: 1; } }
"""
BACK_SHEET = "M386 100 H774 A56 56 0 0 1 830 156 V684 A56 56 0 0 1 774 740 H386 A56 56 0 0 1 330 684 V156 A56 56 0 0 1 386 100 Z"
FRONT_SHEET = "M226 260 H500 L670 430 V844 A56 56 0 0 1 614 900 H226 A56 56 0 0 1 170 844 V316 A56 56 0 0 1 226 260 Z"
FOLD = "500,260 670,430 500,430"


def _sheets() -> str:
    """The icon's two sheets: the front one hides the part of the back one it overlaps, so the drift reads as sliding behind it."""
    x = MARK_X + 20 - SHEETS_ORIGIN[0] * SHEETS_SCALE
    y = MARK_Y + 4 - SHEETS_ORIGIN[1] * SHEETS_SCALE
    return (f'<g transform="translate({x:g} {y:g}) scale({SHEETS_SCALE})">'
            f'<defs><mask id="behind-front" maskUnits="userSpaceOnUse" x="0" y="-100" width="1000" height="1200">'
            f'<rect x="0" y="-100" width="1000" height="1200" fill="#fff"/>'
            f'<path d="{FRONT_SHEET}" fill="#000" stroke="#000" stroke-width="112" stroke-linejoin="round"/></mask></defs>'
            f'<g mask="url(#behind-front)"><path class="sheet-back" d="{BACK_SHEET}" fill="{SHEET_BACK}"/></g>'
            f'<path d="{FRONT_SHEET}" fill="{SHEET_FRONT}"/><polygon points="{FOLD}" fill="{SHEET_FOLD}"/></g>')


def render_resma_card() -> str:
    body = [
        panel(PANEL_COLOR),
        faded_mark(_sheets()),
        '<text class="ink display" x="0" y="72" font-size="66">RESMA</text>',
        '<text class="muted" x="2" y="98" font-size="12" letter-spacing="2.4">PDF TOOLS IN YOUR BROWSER</text>',
        '<text class="ink display" x="0" y="142" font-size="32">Merge PDF · JPG to PDF</text>',
        '<text class="muted" x="0" y="164" font-size="14">Free, no sign-up, nothing leaves your device</text>',
        call_to_action("Resma", 192),
    ]
    return document(HEIGHT, "Resma: free PDF tools in your browser, merge PDF and JPG to PDF, no sign-up, nothing uploaded", "\n".join(body), CSS, framed=False)
