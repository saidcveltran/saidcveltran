"""Social links as own-hosted SVG icon buttons, in the brand palette.

The logo shapes are vendored in tools/icons (see the README there for sources and licences) and drawn in the
palette's green, so the buttons stay one family while the glyph is the network's real mark. A button is only
the icon, large; the network name and the account handle live in its accessible title and alt text.
Handles come from the account registry of the project. Nothing is loaded from outside.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from html import escape
from pathlib import Path

from .svg_common import DISPLAY_ADVANCE, document, slug

ICON_DIR = Path(__file__).resolve().parent.parent / "icons"
BUTTON = 52  # the button is a square this many pixels wide and tall
ICON_SIZE = 32
LABEL_WIDTH, LABEL_HEIGHT, LABEL_FONT = 300, 30, 15  # two groups of this width fill the README column
CSS = """
.glyph path { fill: #7ee2a8; } .globe { fill: none; stroke: #7ee2a8; stroke-width: 1.7; }
@media (prefers-color-scheme: light) { .glyph path { fill: #1a7f37; } .globe { stroke: #1a7f37; } }
"""
# The own-drawn globe for the project website (there is no third-party mark for it).
GLOBE = ('<g class="globe" transform="translate({x} {y}) scale({s})"><circle cx="12" cy="12" r="10"/>'
         '<ellipse cx="12" cy="12" rx="4.4" ry="10"/><path d="M2 12h20"/></g>')


@dataclass(frozen=True)
class Link:
    label: str
    handle: str
    url: str
    icon: str  # file stem in tools/icons, or "globe"


AISKARON = (
    Link("X", "@aiskaron", "https://x.com/aiskaron", "x"),
    Link("TikTok", "@aiskaron", "https://www.tiktok.com/@aiskaron", "tiktok"),
    Link("Instagram", "@aiskaron", "https://www.instagram.com/aiskaron", "instagram"),
    Link("Discord", "discord.aiskaron.com", "https://discord.aiskaron.com", "discord"),
    Link("Web", "aiskaron.com", "https://aiskaron.com", "globe"),
)
PERSONAL = (
    Link("GitHub", "saidcveltran", "https://github.com/saidcveltran", "github"),
    Link("Apify", "saidcveltran", "https://apify.com/saidcveltran", "apify"),
    Link("dev.to", "saidcveltran", "https://dev.to/saidcveltran", "devdotto"),
    Link("Product Hunt", "@saidcveltran", "https://www.producthunt.com/@saidcveltran", "producthunt"),
    Link("itch.io", "saidcveltran", "https://saidcveltran.itch.io", "itchdotio"),
)
GROUPS = (("AIskaron", "the projects", AISKARON), ("saidcveltran.dev", "me", PERSONAL))


def load_glyph(name: str) -> tuple[str, list[str]]:
    """(viewBox, path data) of a vendored icon; fills and clip groups of the source are dropped on purpose."""
    text = (ICON_DIR / f"{name}.svg").read_text(encoding="utf-8")
    box = re.search(r'viewBox="([^"]+)"', text)
    paths = re.findall(r'<path[^>]*?\sd="([^"]+)"', text)
    if not box or not paths:
        raise ValueError(f"icon {name} has no viewBox or path")
    return box.group(1), paths


def icon_fragment(name: str, x: int, y: int) -> str:
    if name == "globe":
        return GLOBE.format(x=x, y=y, s=round(ICON_SIZE / 24, 3))
    view_box, paths = load_glyph(name)
    drawn = "".join(f'<path d="{d}"/>' for d in paths)
    return f'<svg class="glyph" x="{x}" y="{y}" width="{ICON_SIZE}" height="{ICON_SIZE}" viewBox="{view_box}">{drawn}</svg>'


def render_button(link: Link) -> str:
    """Square button with the network's logo only; name and handle are in the accessible title."""
    offset = (BUTTON - ICON_SIZE) // 2
    body = (f'<rect class="accent" opacity=".5" x="0" y="{BUTTON - 2}" width="{BUTTON}" height="2"/>'
            f'{icon_fragment(link.icon, offset, offset - 2)}')
    return document(BUTTON, f"{link.label}: {link.handle}", body, CSS, width=BUTTON, framed=False, fonts=False)


def button_name(link: Link) -> str:
    return f"social-{slug(link.label)}.svg"


def group_label_name(title: str) -> str:
    return f"group-{slug(title)}.svg"


def render_group_label(title: str, note: str) -> str:
    """The heading of one group: its name, a short note and a faint rule, as a fixed-width image.

    The fixed width is what makes the two groups share the page's width: GitHub ignores a table's width attribute,
    so each cell is as wide as the widest thing in it.
    """
    note_x = len(title) * LABEL_FONT * DISPLAY_ADVANCE + 10
    body = (f'<text class="ink display" x="0" y="20" font-size="{LABEL_FONT}">{escape(title)}</text>'
            f'<text class="muted" x="{note_x:.0f}" y="20" font-size="12">{escape(note)}</text>'
            f'<rect class="accent" opacity=".35" x="0" y="{LABEL_HEIGHT - 2}" width="{LABEL_WIDTH}" height="2"/>')
    return document(LABEL_HEIGHT, f"{title} ({note})", body, width=LABEL_WIDTH, framed=False)


def render_social_links(assets_url: str) -> str:
    """HTML for both groups, side by side in one two-cell table: the cell border is the divider between the groups.

    Every button links to the account. Each cell starts with its group's heading image (the name is its alt text).
    """
    cells = []
    for title, note, links in GROUPS:
        label = f'<img src="{assets_url}/{group_label_name(title)}" alt="{escape(title)} ({escape(note)})" width="{LABEL_WIDTH}" height="{LABEL_HEIGHT}">'
        buttons = "\n".join(f'<a href="{escape(l.url)}"><img src="{assets_url}/{button_name(l)}" alt="{escape(l.label)}, {escape(l.handle)}" width="{BUTTON}" height="{BUTTON}"></a>' for l in links)
        cells.append(f'<td valign="top">\n{label}<br>\n{buttons}\n</td>')
    return "<table>\n<tr>\n" + "\n".join(cells) + "\n</tr>\n</table>"
