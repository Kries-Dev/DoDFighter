#!/usr/bin/env python3
"""Draw Cod1eh's effect sprites as 8-bit LF2 sheets (no AutoSprite credits).

    python tools/make_cod1eh_fx.py OUT_DIR

kunai.bmp    4 x 2 cells of 40x14: 0-3 a flying kunai (steel blade, crimson-wrapped
             grip, ring) with a glint moving along it, 4-7 a spark as it hits.
smoke.bmp    4 x 2 cells of 150x96: 0-3 a churning smoke cloud (see-through
             dither so fighters inside stay visible), 4-7 the same thinning out.
rope.bmp     4 x 6 cells of 230x14: 0-7 the DvA rope blade shooting out and being
             yanked back (a twisted rope with his blade on the end); 8-23 one
             length each (15-210 px) for reeling a target in.
Palette and look match the fighters: bold dark outline, flat shading.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from autosprite_to_lf2 import write_bmp

BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
PAL = [(0, 0, 0), (28, 28, 38), (110, 118, 132), (186, 194, 208), (242, 246, 252), (100, 18, 28), (172, 36, 46),
       (86, 58, 38), (150, 108, 66), (84, 86, 96), (134, 136, 146), (184, 186, 194), (222, 224, 230), (255, 226, 110)]
OUTLINE, STEEL_D, STEEL, STEEL_HI, GRIP_D, GRIP, ROPE_D, ROPE, SMOKE_D, SMOKE, SMOKE_L, SMOKE_W, SPARK = range(1, 14)


def sheet(cells, w, h, path):
    rows = (len(cells) + 3) // 4
    SW, SH = 4 * (w + 1), rows * (h + 1)
    out = [[0] * SW for _ in range(SH)]
    for i, cell in enumerate(cells):
        ox, oy = (i % 4) * (w + 1), (i // 4) * (h + 1)
        for y in range(h):
            out[oy + y][ox:ox + w] = cell[y]
    write_bmp(path, SW, SH, PAL, out)
    print(f'{path}: {SW}x{SH}, cells {w}x{h}, row: 4  col: {rows}')


def outline(px):
    H, W = len(px), len(px[0])
    edge = [(x, y) for y in range(H) for x in range(W) if px[y][x] == 0 and any(
        0 <= x + a < W and 0 <= y + b < H and px[y + b][x + a] not in (0, OUTLINE)
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for x, y in edge:
        px[y][x] = OUTLINE
    return px


def kunai(px, x0, y, length=34, glint=None):
    """A kunai pointing right, its butt ring at x0, centred on row y."""
    ring, grip, blade = 5, 11, length - 16
    for x in range(x0, x0 + length):
        t = x - x0
        if t < ring:                                   # ring
            for dy in (-2, 2):
                px[y + dy][x] = STEEL
            if t in (0, ring - 1):
                for dy in (-1, 0, 1):
                    px[y + dy][x] = STEEL
        elif t < ring + grip:                          # wrapped grip
            for dy in (-1, 0, 1):
                px[y + dy][x] = GRIP if (t + dy) % 3 else GRIP_D
        else:                                          # leaf blade: widest a third of the way
            k = (t - ring - grip) / blade
            half = round(3.5 * (k / 0.33 if k < 0.33 else (1 - k) / 0.67))
            for dy in range(-half, half + 1):
                px[y + dy][x] = STEEL_HI if dy < 0 else (STEEL if dy == 0 else STEEL_D)
            if glint is not None and abs(t - glint) <= 1:
                for dy in range(-half, 1):
                    px[y + dy][x] = STEEL_HI
    return px


def kunai_frame(phase, W=40, H=14):
    px = [[0] * W for _ in range(H)]
    kunai(px, 2, H // 2, glint=18 + phase * 4)
    return outline(px)


def spark_frame(k, W=40, H=14):
    px = [[0] * W for _ in range(H)]
    cx, cy, r = 30, H // 2, 2 + k * 2
    for a in range(8):
        ang = a * math.pi / 4
        for d in range(max(0, r - 3), r + 1):
            x, y = round(cx + math.cos(ang) * d), round(cy + math.sin(ang) * d * 0.6)
            if 0 <= x < W and 0 <= y < H:
                px[y][x] = SPARK if d == r else STEEL_HI
    return px


PUFFS = [(-48, 10, 26), (-22, -4, 32), (8, 6, 30), (36, -6, 28), (54, 12, 22), (-10, 22, 26), (24, 24, 24),
         (-36, -20, 18), (10, -22, 20), (40, -24, 14)]   # x, y offsets from the cloud centre, radius


def smoke_frame(phase, keep=1.0, W=150, H=96):
    px = [[0] * W for _ in range(H)]
    cx, cy = W / 2, H / 2 + 8
    for i, (ox, oy, r) in enumerate(PUFFS):
        a = phase * math.pi / 2 + i
        px_, py_ = cx + ox + 3 * math.cos(a), cy + oy + 2 * math.sin(a) - phase * 1.5
        rr = r * (1 + 0.06 * math.sin(a * 1.7))
        for y in range(max(0, int(py_ - rr)), min(H, int(py_ + rr) + 1)):
            for x in range(max(0, int(px_ - rr)), min(W, int(px_ + rr) + 1)):
                d = math.hypot(x + .5 - px_, (y + .5 - py_) * 1.15) / rr
                if d > 1:
                    continue
                shade = SMOKE_W if (y - py_) < -rr * 0.35 else SMOKE_L if d < 0.55 else SMOKE if d < 0.85 else SMOKE_D
                cover = (0.8 if d < 0.7 else 0.55) * keep          # see-through: fighters show through
                if BAYER[(y + phase) % 4][(x + phase) % 4] < cover * 16 and (px[y][x] == 0 or shade > px[y][x]):
                    px[y][x] = shade
    return px


ROPE_LENGTHS = (70, 140, 200, 210, 210, 140, 80, 30)   # out over 3 frames, holds, yanked back
REEL_LENGTHS = tuple(15 + 13 * k for k in range(16))   # 8-23 (15-210 px): held while a target is reeled in


def rope_frame(length, W=230, H=14):
    px = [[0] * W for _ in range(H)]
    y = H // 2
    tip = length
    for x in range(2, max(3, tip - 16)):                 # twisted rope
        px[y][x] = ROPE if x % 4 < 2 else ROPE_D
        px[y - 1][x] = ROPE_D if x % 4 == 1 else ROPE
    kunai(px, max(2, tip - 18), y, length=18 + 6)          # his blade on the end
    return outline(px)


def main(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    sheet([kunai_frame(i) for i in range(4)] + [spark_frame(k) for k in range(4)], 40, 14, os.path.join(out_dir, 'kunai.bmp'))
    sheet([smoke_frame(i) for i in range(4)] + [smoke_frame(i, k) for i, k in zip(range(4), (0.7, 0.45, 0.25, 0.1))],
          150, 96, os.path.join(out_dir, 'smoke.bmp'))
    sheet([rope_frame(n) for n in ROPE_LENGTHS + REEL_LENGTHS], 230, 14, os.path.join(out_dir, 'rope.bmp'))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
