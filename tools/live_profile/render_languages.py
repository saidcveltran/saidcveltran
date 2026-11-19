"""The Languages row: one icon per language used across all projects, with no text on the page.

Icons are the languages' own logos, vendored in tools/icons and drawn in the palette's green like the social
buttons. A language without a vendored logo is reported by `split_by_icon` and left out of the row instead of
being drawn as text or with an invented mark. The name is in the image's alt text and tooltip.
"""
from __future__ import annotations

from html import escape

from .render_socials import BUTTON, Link, render_button
from .svg_common import slug

NOTE = "used in my projects"
ICONS = {  # language name as GitHub reports it -> file stem in tools/icons
    "Python": "python", "Rust": "rust", "JavaScript": "javascript", "TypeScript": "typescript",
    "HTML": "html5", "CSS": "css", "Shell": "gnubash", "Astro": "astro",
    "PowerShell": "powershell", "Go Template": "go-template",  # drawn here: no official logo is available for them
}


def split_by_icon(languages: list[str]) -> tuple[list[str], list[str]]:
    """(languages that have a logo, languages without one), each in the given order."""
    return [name for name in languages if name in ICONS], [name for name in languages if name not in ICONS]


def icon_name(language: str) -> str:
    return f"language-{slug(language)}.svg"


def render_language_icon(language: str) -> str:
    return render_button(Link(language, NOTE, "", ICONS[language]))


def render_language_row(languages: list[str], assets_url: str) -> str:
    """HTML for the row; the icons are not links (the list includes private projects), they show the name on hover."""
    shown, _ = split_by_icon(languages)
    images = [f'<img src="{assets_url}/{icon_name(name)}" alt="{escape(name)}" title="{escape(name)}" width="{BUTTON}" height="{BUTTON}">' for name in shown]
    return "<p>\n" + "\n".join(images) + "\n</p>" if images else ""
