"""Build the subset fonts embedded in the SVG cards.

Usage (needs fonttools and brotli, which the renderers themselves do not):
    python build_fonts.py

Reads the full fonts from fonts/source and writes the WOFF2 subsets next to them. Run it again only when
glyph_ranges.RANGES or a source font changes; the generated files are committed.
"""
from __future__ import annotations

import sys
from pathlib import Path

from fontTools import subset

from live_profile.glyph_ranges import unicodes

FONTS = Path(__file__).resolve().parent / "fonts"
JOBS = (
    ("source/inter-600-latin.woff2", "inter-600-subset.woff2"),
    ("source/jetbrains-mono-800-latin.woff2", "jetbrains-mono-800-subset.woff2"),
)


def build(source: Path, target: Path) -> int:
    options = subset.Options()
    options.flavor = "woff2"
    options.layout_features = ["kern", "tnum"]
    options.hinting = False
    options.notdef_outline = True
    font = subset.load_font(str(source), options)
    subsetter = subset.Subsetter(options)
    subsetter.populate(unicodes=unicodes())
    subsetter.subset(font)
    subset.save_font(font, str(target), options)
    return target.stat().st_size


def main() -> int:
    for source_name, target_name in JOBS:
        size = build(FONTS / source_name, FONTS / target_name)
        print(f"{target_name}: {size} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
