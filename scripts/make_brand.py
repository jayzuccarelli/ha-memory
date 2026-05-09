"""Generate brand assets: a clean notebook glyph in two sizes.

Outputs:
  custom_components/memory/brand/icon.png          256x256
  custom_components/memory/brand/icon@2x.png       512x512
  custom_components/memory/brand/logo.png          512x512
  custom_components/memory/brand/logo@2x.png      1024x1024

Design: rounded card with three horizontal lines (text), monochrome on
transparent background. Indigo fill (#3B5BDB) — distinct from the
default HA blue, signals "thought / persistent."
"""
from __future__ import annotations

import os
from PIL import Image, ImageDraw

BRAND_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "custom_components",
    "memory",
    "brand",
)
INDIGO = (59, 91, 219, 255)


def draw_notebook(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Outer card: rounded rectangle, 80% of canvas, centered
    pad = int(size * 0.10)
    radius = int(size * 0.10)
    bbox = (pad, pad, size - pad, size - pad)
    d.rounded_rectangle(bbox, radius=radius, fill=INDIGO)

    # Three horizontal "lines" — knock out by drawing transparent pills
    line_x0 = pad + int(size * 0.12)
    line_x1 = size - pad - int(size * 0.12)
    line_h = int(size * 0.06)
    line_radius = line_h // 2

    # Vertical positions: 35%, 50%, 65% of canvas
    for ratio in (0.35, 0.50, 0.65):
        y = int(size * ratio) - line_h // 2
        d.rounded_rectangle(
            (line_x0, y, line_x1, y + line_h),
            radius=line_radius,
            fill=(255, 255, 255, 230),
        )

    # Top "spine" tab — short rounded bar at top center suggesting a notebook clip
    spine_w = int(size * 0.30)
    spine_h = int(size * 0.05)
    spine_x0 = (size - spine_w) // 2
    d.rounded_rectangle(
        (spine_x0, pad - spine_h // 2, spine_x0 + spine_w, pad + spine_h // 2),
        radius=spine_h // 2,
        fill=INDIGO,
    )
    return img


def main() -> None:
    os.makedirs(BRAND_DIR, exist_ok=True)
    for name, size in (
        ("icon.png", 256),
        ("icon@2x.png", 512),
        ("logo.png", 512),
        ("logo@2x.png", 1024),
    ):
        out = os.path.join(BRAND_DIR, name)
        draw_notebook(size).save(out, "PNG", optimize=True)
        print(f"wrote {out} ({size}x{size})")


if __name__ == "__main__":
    main()
