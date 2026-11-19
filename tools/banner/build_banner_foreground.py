"""Foreground of the profile banner: a transparent animated WebP with everything except the rain and the base colour.

The README header is an SVG (render_banner.py) with a dark gradient and live falling code behind this image.
Everything painted here is semi-transparent or has transparent surroundings so the rain shows through:
the green glow, a few bokeh discs, the wordmark, the handle line, the cat head, and two motions
  1. the dot matrices inside the cat's glasses scroll as a travelling wave,
  2. the wordmark's cursor blinks once per second.
The rising motes are not here: a lossy animated image re-encodes everything they cross in every frame, which made
the light around the head shimmer. They are native SVG animation (live_profile/render_motes.py).

Usage: python build_banner_foreground.py <brand-kit-dir> <output.webp>
Needs Pillow and numpy and the brand kit; the output is committed, so the scheduled refresh does not need either.
Pass the result through img-scrub before committing it.
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import compose_profile_banner as compose

WIDTH, HEIGHT = compose.WIDTH, compose.HEIGHT
FPS, SECONDS = 12, 3
FRAMES = FPS * SECONDS
BLINK_FRAMES = FPS // 2
LENS_BOXES = ((170, 470, 460, 665), (540, 480, 870, 665))  # in the 1024 px source art: (left, top, right, bottom)
WAVE_CYCLES, WAVE_RANGE = 1.5, 1.3
GLOW_TINT, GLOW_ALPHA = (36, 120, 70), 0.45
BOKEH_TINT = (46, 125, 66)
WEBP_QUALITY, WEBP_ALPHA_QUALITY = 80, 100  # lossless alpha: a lossy alpha channel makes the soft glow shimmer between frames


def glow_layer() -> Image.Image:
    """Soft green light behind the head: a flat tint whose alpha is a blurred ellipse."""
    mask = Image.new("L", (WIDTH, HEIGHT), 0)
    cx, cy = compose.GLOW_CENTER
    r = compose.GLOW_RADIUS
    ImageDraw.Draw(mask).ellipse((cx - r, cy - r * 0.78, cx + r, cy + r * 0.78), fill=215)
    mask = mask.filter(ImageFilter.GaussianBlur(120)).point(lambda v: round(v * GLOW_ALPHA))
    layer = Image.new("RGBA", (WIDTH, HEIGHT), GLOW_TINT + (0,))
    layer.putalpha(mask)
    return layer


def bokeh_layer(seed: int = 7) -> Image.Image:
    """Out-of-focus green discs as an alpha-only layer (same discs as the flat banner)."""
    rng = random.Random(seed)
    mask = Image.new("L", (WIDTH, HEIGHT), 0)
    draw = ImageDraw.Draw(mask)
    for _ in range(16):
        x = rng.randint(760, WIDTH - 20) if rng.random() < 0.75 else rng.randint(40, 740)
        y = rng.randint(20, HEIGHT - 20)
        r = rng.randint(10, 34)
        draw.ellipse((x - r, y - r, x + r, y + r), fill=rng.randint(14, 36))
    layer = Image.new("RGBA", (WIDTH, HEIGHT), BOKEH_TINT + (0,))
    layer.putalpha(mask.filter(ImageFilter.GaussianBlur(7)))
    return layer


def wordmark_layer(kit: Path) -> tuple[Image.Image, tuple[int, int], Image.Image]:
    """The wordmark on a transparent canvas, its origin, and the wordmark image itself."""
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    mark = Image.open(kit / "04-logo/wordmark-fondo-oscuro.png").convert("RGBA")
    mark = mark.crop(mark.getchannel("A").getbbox())
    mark = mark.resize((642, round(mark.height * 642 / mark.width)), Image.LANCZOS)
    layer.paste(mark, (120, 186), mark)
    return layer, (120, 186), mark


def handle_layer(kit: Path) -> Image.Image:
    """The '</> github.com/...' line: the kit's green pixels become the alpha of a flat green."""
    source = Image.open(kit / "05-banners/banner-x-1500x500.png").convert("RGB")
    box = (118, 286, 640, 334)
    crop = source.crop(box)
    alpha = crop.getchannel("G").point(lambda v: max(0, min(255, round((v - 24) * 255 / 160))))
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    layer.paste(Image.new("RGBA", crop.size, compose.GREEN + (255,)), box[:2], alpha)
    return layer


def head_layer(kit: Path) -> tuple[Image.Image, Image.Image, int, int]:
    """Cat head with its soft shadow on a transparent canvas, the head image and its position."""
    head = Image.open(kit / "02-sin-fondo/gato-solo-1024.png").convert("RGBA")
    head = head.crop(head.getchannel("A").getbbox())
    head = head.resize((round(head.width * 410 / head.height), 410), Image.LANCZOS)
    x = compose.GLOW_CENTER[0] - head.width // 2
    y = compose.GLOW_CENTER[1] - head.height // 2 + 8
    shadow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    shadow.paste((0, 0, 0, 150), (x, y + 14), head.getchannel("A"))
    layer = shadow.filter(ImageFilter.GaussianBlur(22))
    layer.alpha_composite(head, (x, y))
    return layer, head, x, y


def lens_dot_mask(source: Image.Image, head: Image.Image) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    """Float mask (0..1) of the green dots in the resized head's pixel grid, plus the lens bounding box."""
    crop_box = source.getchannel("A").getbbox()
    scale = head.height / (crop_box[3] - crop_box[1])
    rgba = np.asarray(head).astype(np.int16)
    greenness = rgba[..., 1] - np.maximum(rgba[..., 0], rgba[..., 2])
    mask = np.zeros(greenness.shape, dtype=np.float32)
    boxes = []
    for left, top, right, bottom in LENS_BOXES:
        x0, x1 = round((left - crop_box[0]) * scale), round((right - crop_box[0]) * scale)
        y0, y1 = round((top - crop_box[1]) * scale), round((bottom - crop_box[1]) * scale)
        region = np.clip((greenness[y0:y1, x0:x1] - 10) / 60.0, 0, 1)
        region[rgba[y0:y1, x0:x1, 3] < 200] = 0
        mask[y0:y1, x0:x1] = region
        boxes.append((x0, y0, x1, y1))
    return mask, (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))


def cursor_box(mark: Image.Image, origin: tuple[int, int]) -> tuple[int, int, int, int]:
    """Bounding box of the wordmark's green cursor in canvas coordinates; the text itself is white."""
    arr = np.asarray(mark).astype(np.int16)
    green = (arr[..., 1] > 140) & (arr[..., 0] < 130) & (arr[..., 3] > 128)
    ys, xs = np.nonzero(green)
    if xs.size == 0:
        raise RuntimeError("no green cursor found in the wordmark")
    return origin[0] + int(xs.min()) - 2, origin[1] + int(ys.min()) - 2, origin[0] + int(xs.max()) + 3, origin[1] + int(ys.max()) + 3


def build_frames(kit: Path) -> list[Image.Image]:
    canvas = glow_layer()
    canvas.alpha_composite(bokeh_layer())
    wordmark, origin, mark = wordmark_layer(kit)
    canvas.alpha_composite(wordmark)
    canvas.alpha_composite(handle_layer(kit))
    head_canvas, head, hx, hy = head_layer(kit)
    canvas.alpha_composite(head_canvas)
    source = Image.open(kit / "02-sin-fondo/gato-solo-1024.png").convert("RGBA")
    dot_mask, (bx0, by0, bx1, by1) = lens_dot_mask(source, head)
    cursor = cursor_box(mark, origin)
    patch = np.asarray(canvas.crop((hx + bx0, hy + by0, hx + bx1, hy + by1))).astype(np.float32)
    patch_mask = dot_mask[by0:by1, bx0:bx1][..., None]
    columns = np.linspace(0, 1, bx1 - bx0, dtype=np.float32)[None, :, None]
    frames = []
    for index in range(FRAMES):
        phase = index / FRAMES
        frame = canvas.copy()
        gain = 0.5 + 0.5 * np.sin(2 * math.pi * (columns * WAVE_CYCLES - phase))
        lit = patch.copy()
        lit[..., :3] = np.clip(patch[..., :3] * (1 + patch_mask * (WAVE_RANGE * gain - 0.5)), 0, 255)
        frame.paste(Image.fromarray(lit.astype(np.uint8), "RGBA"), (hx + bx0, hy + by0))
        if (index // BLINK_FRAMES) % 2 == 1:
            frame.paste((0, 0, 0, 0), cursor)  # cursor off: fully transparent, the rain shows through
        frames.append(frame)
    return frames


def main(kit: Path, out: Path) -> None:
    frames = build_frames(kit)
    out.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(out, format="WEBP", save_all=True, append_images=frames[1:], duration=round(1000 / FPS), loop=0,
                   quality=WEBP_QUALITY, alpha_quality=WEBP_ALPHA_QUALITY, method=6)
    print("written", out, f"{out.stat().st_size / 1024:.0f} KiB", f"{FRAMES} frames at {FPS} fps")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
