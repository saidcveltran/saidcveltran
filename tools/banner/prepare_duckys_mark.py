"""Shrink the Duckys mascot master to the size the profile card needs, as a transparent WebP.

Usage: python prepare_duckys_mark.py <duck-master.png> <output.webp>
The master is DUCKYS/assets/brand/duck-master.png (transparent, 1178 px). Pass the result through img-scrub.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

SIZE = 400
QUALITY = 88


def main(master: Path, out: Path) -> None:
    mark = Image.open(master).convert("RGBA")
    mark = mark.crop(mark.getchannel("A").getbbox())
    side = max(mark.size)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.paste(mark, ((side - mark.width) // 2, (side - mark.height) // 2), mark)
    square = square.resize((SIZE, SIZE), Image.LANCZOS)
    out.parent.mkdir(parents=True, exist_ok=True)
    square.save(out, format="WEBP", quality=QUALITY, alpha_quality=90, method=6)
    print("written", out, f"{out.stat().st_size / 1024:.0f} KiB", square.size)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
