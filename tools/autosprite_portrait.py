#!/usr/bin/env python3
"""Build LF2 portraits from an AutoSprite base image.

    python tools/autosprite_portrait.py BASE.png OUT_DIR  HEAD_BOX  SMALL_BOX

HEAD_BOX / SMALL_BOX are x0,y0,x1,y1 crops in BASE.png pixels:
  HEAD_BOX  (square)        -> OUT_DIR/portrait_f.bmp  120x120  ('head:', picker)
  SMALL_BOX (40:45 aspect)  -> OUT_DIR/portrait_s.bmp   40x45   ('small:', HUD)

The base's light background (opaque white or transparent), flood-filled from
the image edges, is replaced with BACKDROP so the face sits on a dark panel
like the stock LF2 faces. Output is 8-bit; no pixel is pure black.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from autosprite_to_lf2 import read_png, write_bmp, area_resample, median_cut, nearest

BACKDROP = (22, 30, 58)


def knock_out_background(img):
    H, W = len(img), len(img[0])
    def bg(p): return p[3] < 32 or min(p[:3]) >= 236
    seen = [[False] * W for _ in range(H)]
    stack = [(x, y) for x in range(W) for y in (0, H - 1)] + [(x, y) for y in range(H) for x in (0, W - 1)]
    while stack:
        x, y = stack.pop()
        if seen[y][x] or not bg(img[y][x]): continue
        seen[y][x] = True
        img[y][x] = BACKDROP + (255,)
        if x > 0: stack.append((x - 1, y))
        if x < W - 1: stack.append((x + 1, y))
        if y > 0: stack.append((x, y - 1))
        if y < H - 1: stack.append((x, y + 1))
    # composite anything semi-transparent onto the backdrop
    for row in img:
        for i, (r, g, b, a) in enumerate(row):
            if a < 255:
                t = a / 255
                row[i] = (round(r * t + BACKDROP[0] * (1 - t)), round(g * t + BACKDROP[1] * (1 - t)),
                          round(b * t + BACKDROP[2] * (1 - t)), 255)


def save(img, box, size, path):
    x0, y0, x1, y1 = box
    scale = size[0] / (x1 - x0)
    cell = area_resample(img, x0, y0, x1 - x0, y1 - y0, scale, *size)
    colours = [(int(r), int(g), int(b)) for line in cell for (r, g, b, a) in line]
    pal = median_cut(colours, 255)
    cache = {}
    rows = [[nearest(pal, (int(r), int(g), int(b)), cache) for (r, g, b, a) in line] for line in cell]
    write_bmp(path, size[0], size[1], [(0, 0, 0)] + pal, rows)


def main(base, out_dir, head_box, small_box):
    os.makedirs(out_dir, exist_ok=True)
    _, _, img = read_png(base)
    knock_out_background(img)
    save(img, tuple(map(int, head_box.split(','))), (120, 120), os.path.join(out_dir, 'portrait_f.bmp'))
    save(img, tuple(map(int, small_box.split(','))), (40, 45), os.path.join(out_dir, 'portrait_s.bmp'))
    print('wrote portrait_f.bmp (120x120) and portrait_s.bmp (40x45)')


if __name__ == '__main__':
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    main(*sys.argv[1:])
