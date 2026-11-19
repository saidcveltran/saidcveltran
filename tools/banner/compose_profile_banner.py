"""Compose the GitHub profile banner: wordmark and handle line on the left, cat head only on the right.

Inputs are the saidcveltran brand kit files; the output is a flat 1500x500 PNG with no metadata.
The handle line is lifted from the kit's X banner by keying its green pixels, because the brand
typeface (Anonymous Pro) is not installed on this machine.
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

WIDTH, HEIGHT = 1500, 500
BASE_TOP, BASE_BOTTOM = (5, 8, 12), (13, 18, 22)
GLOW_CENTER, GLOW_RADIUS = (1235, 225), 330
GLOW_COLOR = (20, 58, 36)
GREEN = (63, 185, 80)


def vertical_gradient() -> Image.Image:
    """Dark base from near-black to a slightly lifted slate."""
    strip = Image.new("RGB", (1, HEIGHT))
    for y in range(HEIGHT):
        t = y / (HEIGHT - 1)
        strip.putpixel((0, y), tuple(round(a + (b - a) * t) for a, b in zip(BASE_TOP, BASE_BOTTOM)))
    return strip.resize((WIDTH, HEIGHT))


def radial_glow() -> Image.Image:
    """Soft green glow behind the head, built as a blurred mask over a flat colour."""
    mask = Image.new("L", (WIDTH, HEIGHT), 0)
    cx, cy = GLOW_CENTER
    ImageDraw.Draw(mask).ellipse((cx - GLOW_RADIUS, cy - GLOW_RADIUS * 0.78, cx + GLOW_RADIUS, cy + GLOW_RADIUS * 0.78), fill=215)
    mask = mask.filter(ImageFilter.GaussianBlur(120))
    return Image.composite(Image.new("RGB", (WIDTH, HEIGHT), GLOW_COLOR), Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0)), mask)


def bokeh(seed: int = 7) -> Image.Image:
    """A few out-of-focus green discs, mostly around the glow."""
    rng = random.Random(seed)
    layer = Image.new("L", (WIDTH, HEIGHT), 0)
    draw = ImageDraw.Draw(layer)
    for _ in range(16):
        x = rng.randint(760, WIDTH - 20) if rng.random() < 0.75 else rng.randint(40, 740)
        y = rng.randint(20, HEIGHT - 20)
        r = rng.randint(10, 34)
        draw.ellipse((x - r, y - r, x + r, y + r), fill=rng.randint(14, 36))
    layer = layer.filter(ImageFilter.GaussianBlur(7))
    return Image.composite(Image.new("RGB", (WIDTH, HEIGHT), (46, 125, 66)), Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0)), layer)


def grain(strength: int = 9) -> Image.Image:
    """Fine monochrome noise, centred on mid grey so that it adds and removes light evenly."""
    return Image.effect_noise((WIDTH, HEIGHT), strength).convert("RGB")


def build_background() -> Image.Image:
    canvas = vertical_gradient()
    canvas = ImageChops.add(canvas, radial_glow())
    canvas = ImageChops.add(canvas, bokeh())
    noise = ImageChops.subtract(grain(), Image.new("RGB", (WIDTH, HEIGHT), (128, 128, 128)))
    return ImageChops.add(canvas, noise)


def place_wordmark(canvas: Image.Image, kit: Path) -> tuple[Image.Image, tuple[int, int]]:
    """Wordmark with its green cursor, scaled to the width used by the kit's X banner."""
    mark = Image.open(kit / "04-logo/wordmark-fondo-oscuro.png").convert("RGBA")
    mark = mark.crop(mark.getchannel("A").getbbox())
    target_width = 642
    mark = mark.resize((target_width, round(mark.height * target_width / mark.width)), Image.LANCZOS)
    canvas.paste(mark, (120, 186), mark)
    return mark, (120, 186)


def place_handle_line(canvas: Image.Image, kit: Path) -> None:
    """Re-use the kit's '</> github.com/...' line: green pixels become alpha on a clean green fill."""
    source = Image.open(kit / "05-banners/banner-x-1500x500.png").convert("RGB")
    box = (118, 286, 640, 334)
    crop = source.crop(box)
    alpha = crop.getchannel("G").point(lambda v: max(0, min(255, round((v - 24) * 255 / 160))))
    fill = Image.new("RGB", crop.size, GREEN)
    canvas.paste(fill, box[:2], alpha)


def place_head(canvas: Image.Image, kit: Path) -> tuple[Image.Image, int, int]:
    """Head only (transparent kit asset), centred on the glow."""
    head = Image.open(kit / "02-sin-fondo/gato-solo-1024.png").convert("RGBA")
    head = head.crop(head.getchannel("A").getbbox())
    target_height = 410
    head = head.resize((round(head.width * target_height / head.height), target_height), Image.LANCZOS)
    x = GLOW_CENTER[0] - head.width // 2
    y = GLOW_CENTER[1] - head.height // 2 + 8
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow.paste((0, 0, 0, 150), (x, y + 14), head.getchannel("A"))
    shadow = shadow.filter(ImageFilter.GaussianBlur(22))
    canvas.paste(shadow, (0, 0), shadow)
    canvas.paste(head, (x, y), head)
    return head, x, y


def main(kit: Path, out: Path) -> None:
    canvas = build_background().convert("RGB")
    place_wordmark(canvas, kit)
    place_handle_line(canvas, kit)
    place_head(canvas, kit)
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out, format="PNG", optimize=True)  # no exif, no text chunks, no icc
    print("written", out, canvas.size)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
