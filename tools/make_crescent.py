#!/usr/bin/env python3
"""Draw DarthNox's crescent sword-wave projectile as an 8-bit LF2 sheet.

    python tools/make_crescent.py OUT.bmp

4 x 2 cells of 34x64 (1px gutters, palette index 0 = transparent):
  pictures 0-3  flying (the edge shimmers, sparks drift)
  pictures 4-7  breaking up (dithered away, used for hit/rebound/vanish)
The crescent bulges to the right, the way it flies, and matches the fighter art:
bold navy outline, flat white-to-cyan shading.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from autosprite_to_lf2 import write_bmp

W, H = 34, 64
OUTLINE = (24, 34, 86)
SHADES = [(255, 255, 255), (214, 244, 255), (150, 214, 255), (92, 170, 240)]  # outer edge -> inner
PAL = [(0, 0, 0), OUTLINE] + SHADES


def frame(phase, keep=1.0):
    """phase 0..3 animates the shimmer; keep < 1 dithers the wave away."""
    cx, cy = 6.0, H / 2 - 0.5
    outer_r = 29.0
    inner_dx = 9.0 + (phase % 2)            # thickness pulses by a pixel
    inner_r = 28.0
    px = [[0] * W for _ in range(H)]
    inside = lambda x, y: (x - cx) ** 2 + ((y - cy) * 1.0) ** 2 <= outer_r ** 2 and \
        (x - cx + inner_dx) ** 2 + (y - cy) ** 2 > inner_r ** 2 and x >= cx - 2
    for y in range(H):
        for x in range(W):
            if inside(x + .5, y + .5):
                # distance to the outer rim picks the shade (bright leading edge)
                d = outer_r - math.hypot(x + .5 - cx, y + .5 - cy)
                shade = min(3, int(d / 2.2))
                px[y][x] = 2 + shade
    # bold outline around the shape
    out = [row[:] for row in px]
    for y in range(H):
        for x in range(W):
            if px[y][x] == 0 and any(0 <= x + dx < W and 0 <= y + dy < H and px[y + dy][x + dx]
                                     for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out[y][x] = 1
    # sparks trailing behind the wave
    for i in range(5):
        sy = int((i * 13 + phase * 7) % (H - 8)) + 4
        sx = int((i * 5 + phase * 3) % 8) + 1
        if out[sy][sx] == 0:
            out[sy][sx] = 2
    if keep < 1.0:
        thresholds = [[((x * 7 + y * 13) % 16) / 16 for x in range(W)] for y in range(H)]
        for y in range(H):
            for x in range(W):
                if out[y][x] and thresholds[y][x] >= keep:
                    out[y][x] = 0
    return out


def main(path):
    cells = [frame(p) for p in range(4)] + [frame(p, k) for p, k in zip(range(4), (0.75, 0.5, 0.3, 0.12))]
    SW, SH = 4 * (W + 1), 2 * (H + 1)
    sheet = [[0] * SW for _ in range(SH)]
    for i, cell in enumerate(cells):
        ox, oy = (i % 4) * (W + 1), (i // 4) * (H + 1)
        for y in range(H):
            sheet[oy + y][ox:ox + W] = cell[y]
    write_bmp(path, SW, SH, PAL, sheet)
    print(f'{path}: {SW}x{SH}, cells {W}x{H}, row: 4  col: 2')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
