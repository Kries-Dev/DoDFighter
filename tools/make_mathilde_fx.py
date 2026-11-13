#!/usr/bin/env python3
"""Draw Mathilde's effect sprites as 8-bit LF2 sheets (no AutoSprite credits).

    python tools/make_mathilde_fx.py OUT_DIR

staff.bmp    4 x 2 cells of 64x64: pictures 0-3 a spinning bo staff (black,
             gold caps) with a magenta magic glow, 4-7 the same breaking up.
tornado.bmp  4 x 2 cells of 150x130: pictures 0-3 a swirling magic tornado
             (see-through dither so fighters inside stay visible), 4-7 fading.
Palette and look match the fighters: bold dark outline, flat shading.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from autosprite_to_lf2 import write_bmp

BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
# 0 transparent, then: outline, staff black, staff highlight, gold, gold light,
# glow outer, glow mid, glow inner, white sparkle
PAL = [(0, 0, 0), (36, 16, 44), (24, 22, 30), (70, 66, 84), (214, 160, 40), (255, 222, 110),
       (120, 50, 170), (190, 100, 220), (245, 180, 250), (255, 250, 255)]
OUTLINE, BLACK, SHINE, GOLD, GOLD_HI, GLOW1, GLOW2, GLOW3, WHITE = range(1, 10)


def sheet(cells, w, h, path):
    SW, SH = 4 * (w + 1), 2 * (h + 1)
    out = [[0] * SW for _ in range(SH)]
    for i, cell in enumerate(cells):
        ox, oy = (i % 4) * (w + 1), (i // 4) * (h + 1)
        for y in range(h):
            out[oy + y][ox:ox + w] = cell[y]
    write_bmp(path, SW, SH, PAL, out)
    print(f'{path}: {SW}x{SH}, cells {w}x{h}, row: 4  col: 2')


def fade(cell, keep):
    # scattered (hashed) so it doesn't beat against the Bayer dither already in the art
    return [[v if v == 0 or ((x * 73 + y * 151) * 2654435761 >> 7) % 97 < keep * 97 else 0
             for x, v in enumerate(row)] for y, row in enumerate(cell)]


def staff_frame(angle, phase, W=64, H=64):
    cx, cy = W / 2, H / 2
    half, thick = 27, 2.6
    ca, sa = math.cos(angle), math.sin(angle)
    px = [[0] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            dx, dy = x + .5 - cx, y + .5 - cy
            along, across = dx * ca + dy * sa, -dx * sa + dy * ca
            if abs(along) <= half and abs(across) <= thick:
                if abs(along) > half - 6:
                    px[y][x] = GOLD_HI if across < -0.8 else GOLD
                else:
                    px[y][x] = SHINE if across < -1.4 else BLACK
    # outline, then a dithered magic glow 1-4 px out, shimmering with the phase
    dist = [[0 if px[y][x] else 99 for x in range(W)] for y in range(H)]
    for d in range(1, 6):
        for y in range(H):
            for x in range(W):
                if dist[y][x] == 99 and any(0 <= x + a < W and 0 <= y + b < H and dist[y + b][x + a] == d - 1
                                            for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    dist[y][x] = d
    for y in range(H):
        for x in range(W):
            d = dist[y][x]
            if d == 1:
                px[y][x] = OUTLINE
            elif 2 <= d <= 5:
                colour, cover = {2: (GLOW3, 1.0), 3: (GLOW2, 0.75), 4: (GLOW1, 0.5), 5: (GLOW1, 0.25)}[d]
                if BAYER[(y + phase) % 4][(x + phase) % 4] < cover * 16:
                    px[y][x] = colour
    for k in range(4):              # sparkles trailing the spin
        a = angle + 2.2 + k * 0.35
        sx, sy = int(cx + math.cos(a) * (half - 2)), int(cy + math.sin(a) * (half - 2))
        if 0 <= sx < W and 0 <= sy < H and px[sy][sx] == 0:
            px[sy][sx] = WHITE
    return px


def tornado_frame(phase, W=150, H=130):
    """A funnel, wide at the top and narrow at the bottom, of spiral bands that
    wrap around it (curved by the funnel's roundness) with open air between them,
    so fighters inside stay visible."""
    px = [[0] * W for _ in range(H)]
    cx = W / 2
    for y in range(H):
        t = y / (H - 1)                       # 0 top .. 1 bottom
        radius = 70 - 50 * t ** 0.8
        for x in range(W):
            u = (x + .5 - cx) / radius
            if abs(u) > 1:
                continue
            around = math.asin(u)             # angle around the funnel's axis
            band = math.sin(around * 2.0 + y * 0.21 - phase * 1.57)
            rim = abs(u)
            if band > 0.55:
                colour, cover = (GLOW3 if band > 0.85 else GLOW2), 0.55 + 0.45 * rim
            elif band > 0.25:
                colour, cover = GLOW1, 0.3 + 0.3 * rim
            else:
                continue                      # open air between the bands
            if BAYER[y % 4][(x + phase) % 4] < cover * 16:
                px[y][x] = colour
            if rim > 0.95 and band > 0.25:
                px[y][x] = OUTLINE
    for k in range(16):                       # sparkles riding the bands
        sy = int((k * 29 + phase * 9) % (H - 6)) + 3
        r = 70 - 50 * (sy / (H - 1)) ** 0.8
        sx = int(cx + math.sin(k * 1.7 + phase * 0.8) * r * 0.85)
        for a, b in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            if 0 <= sx + a < W and 0 <= sy + b < H:
                px[sy + b][sx + a] = WHITE
    return px


def main(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    spins = [staff_frame(i * math.pi / 4, i) for i in range(4)]
    sheet(spins + [fade(staff_frame(i * math.pi / 4, i), k) for i, k in zip(range(4), (0.7, 0.45, 0.25, 0.1))],
          64, 64, os.path.join(out_dir, 'staff.bmp'))
    twisters = [tornado_frame(i) for i in range(4)]
    sheet(twisters + [fade(tornado_frame(i), k) for i, k in zip(range(4), (0.7, 0.45, 0.25, 0.1))],
          150, 130, os.path.join(out_dir, 'tornado.bmp'))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
