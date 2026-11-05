"""
Crop 16 personality portraits from a sheet photo into static/avatars/*.png.

1. Put your screenshot here:
     static/source/personalities-sheet.png
   (or .jpg / .webp)

2. Run:
     python scripts/crop_personalities.py

The sheet is expected as 4 rows × 4 columns in this order (16Personalities-style):

  Analysts:  INTJ INTP ENTJ ENTP
  Diplomats: INFJ INFP ENFJ ENFP
  Sentinels: ISTJ ISFJ ESTJ ESFJ
  Explorers: ISTP ISFP ESTP ESFP

Optional fine-tuning via env vars:
  CROP_PAD=0.06   # shrink each cell inward (0–0.2)
  CROP_TOP=0.0    # fraction of image to skip at top (title bar)
  CROP_BOTTOM=0.0
  CROP_LEFT=0.0
  CROP_RIGHT=0.0
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("Install Pillow first:  pip install Pillow")

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "static" / "source"
OUT = ROOT / "static" / "avatars"

GRID = [
    ["INTJ", "INTP", "ENTJ", "ENTP"],
    ["INFJ", "INFP", "ENFJ", "ENFP"],
    ["ISTJ", "ISFJ", "ESTJ", "ESFJ"],
    ["ISTP", "ISFP", "ESTP", "ESFP"],
]


def find_source() -> Path:
    for name in (
        "personalities-sheet.png",
        "personalities-sheet.jpg",
        "personalities-sheet.jpeg",
        "personalities-sheet.webp",
        "personalities.png",
        "personalities.jpg",
    ):
        path = SOURCE_DIR / name
        if path.exists():
            return path
    matches = sorted(
        p
        for p in SOURCE_DIR.glob("*")
        if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
    )
    if matches:
        return matches[0]
    sys.exit(
        f"No sheet image found.\n"
        f"Save your photo as:\n  {SOURCE_DIR / 'personalities-sheet.png'}\n"
        f"Then run this script again."
    )


def main() -> None:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    src = find_source()
    img = Image.open(src).convert("RGBA")
    w, h = img.size

    top = float(os.environ.get("CROP_TOP", "0"))
    bottom = float(os.environ.get("CROP_BOTTOM", "0"))
    left = float(os.environ.get("CROP_LEFT", "0"))
    right = float(os.environ.get("CROP_RIGHT", "0"))
    pad = float(os.environ.get("CROP_PAD", "0.06"))

    x0 = int(w * left)
    y0 = int(h * top)
    x1 = int(w * (1 - right))
    y1 = int(h * (1 - bottom))
    grid = img.crop((x0, y0, x1, y1))
    gw, gh = grid.size
    cell_w, cell_h = gw / 4, gh / 4

    for r, row in enumerate(GRID):
        for c, code in enumerate(row):
            cx0 = int(c * cell_w + cell_w * pad)
            cy0 = int(r * cell_h + cell_h * pad)
            cx1 = int((c + 1) * cell_w - cell_w * pad)
            cy1 = int((r + 1) * cell_h - cell_h * pad)
            tile = grid.crop((cx0, cy0, cx1, cy1))
            # Square portrait centered
            tw, th = tile.size
            side = min(tw, th)
            sx = (tw - side) // 2
            sy = (th - side) // 2
            tile = tile.crop((sx, sy, sx + side, sy + side)).resize((240, 240), Image.Resampling.LANCZOS)
            out = OUT / f"{code}.png"
            tile.save(out, "PNG")
            print("wrote", out.name)

    print("done — home/result pages will prefer these PNGs over SVGs")


if __name__ == "__main__":
    main()
