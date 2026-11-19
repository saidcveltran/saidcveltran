"""Characters the embedded fonts are guaranteed to contain.

The fonts inside the SVG cards are subsets (see build_fonts.py) so each card stays small. Every text a card
draws must stay inside these ranges; tests check the rendered cards against `unsupported`.
"""
from __future__ import annotations

RANGES = (
    (0x0020, 0x007E),  # printable ASCII
    (0x00A1, 0x00A1),  # inverted exclamation
    (0x00B7, 0x00B7),  # middle dot
    (0x00BF, 0x00FF),  # inverted question mark and accented Latin letters
    (0x2013, 0x2014),  # en and em dash
    (0x2018, 0x2019),  # single curly quotes
    (0x201C, 0x201D),  # double curly quotes
    (0x2022, 0x2022),  # bullet
    (0x2026, 0x2026),  # ellipsis
)


def supported(char: str) -> bool:
    return any(low <= ord(char) <= high for low, high in RANGES)


def unsupported(text: str) -> set[str]:
    """The characters of `text` that the embedded fonts do not contain."""
    return {char for char in text if not supported(char)}


def unicodes() -> list[int]:
    """Every code point of RANGES, for the subsetter."""
    return [code for low, high in RANGES for code in range(low, high + 1)]
