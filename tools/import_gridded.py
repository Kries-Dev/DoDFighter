#!/usr/bin/env python3
"""Put a sprite sheet that has grid lines drawn on it onto LF2's grid (79 px cells,
1 px gutter), as an 8-bit sheet with index 0 = transparent black.

    python tools/import_gridded.py EDIT OUT.bmp COLS ROWS [native]

`native`: the edit is already at game size on LF2's grid with an exact-black
background (BenniWr's sheets 1 and 2): exact black is transparent, everything else
is kept as drawn, the gutters are cleared.
Otherwise (an upscaled edit, BenniWr's sheet 0): the grid lines are found (columns /
rows that are mostly a green-grey line), a band of LINE_MARGIN px around each is
cleared, every cell between them is scaled to 79 x 79, and dark pixels (max channel
<= DARK) connected to the cell edge are transparent; dark pixels inside the sprite
stay (no holes in black trousers).
import_sheet.py is for edits without grid lines: its fit and background removal get
confused by them (2026-11-20: black lines and holes on BenniWr).
"""
import sys
from collections import deque

import numpy as np
from PIL import Image

LINE_MARGIN = 3
DARK = 14


def runs(idx):
    """Group consecutive indices: [(first, last), ...]."""
    out = []
    for i in idx:
        if out and i == out[-1][1] + 1:
            out[-1][1] = i
        else:
            out.append([i, i])
    return out


def edge_dark(cell):
    """Mask of dark pixels connected to the cell's edge."""
    h, w = cell.shape[:2]
    dark = cell.max(axis=2) <= DARK
    seen = np.zeros((h, w), bool)
    q = deque((y, x) for y in range(h) for x in (0, w - 1) if dark[y, x])
    q.extend((y, x) for x in range(w) for y in (0, h - 1) if dark[y, x])
    for y, x in q:
        seen[y, x] = True
    while q:
        y, x = q.popleft()
        for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
            if 0 <= ny < h and 0 <= nx < w and dark[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True
                q.append((ny, nx))
    return seen


def save(rgb, clear, dst):
    """rgb: H x W x 3, clear: transparent mask. Index 0 = black = transparent; no
    drawn pixel maps to it."""
    drawn = rgb.copy()
    drawn[clear] = 0
    q = Image.fromarray(drawn).quantize(255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    idx = np.array(q, dtype=np.int16) + 1
    idx[clear] = 0
    pal = q.getpalette()[:765]
    pal += [0] * (765 - len(pal))
    out = Image.fromarray(idx.astype(np.uint8), 'P')
    out.putpalette([0, 0, 0] + pal)
    out.save(dst)
    print(f'{dst}: {out.size[0]}x{out.size[1]}, {len(np.unique(idx)) - 1} colours + transparent')


def native(src, dst, cols, rows):
    a = np.array(Image.open(src).convert('RGB'))[:rows * 80, :cols * 80]
    clear = a.max(axis=2) == 0
    clear[:, 79::80] = True
    clear[79::80, :] = True
    save(a, clear, dst)


def upscaled(src, dst, cols, rows):
    a = np.array(Image.open(src).convert('RGB')).astype(int)
    line = (a[:, :, 1] > a[:, :, 0] + 25) & (a[:, :, 1] > 60)
    xs = [(f + l) / 2 for f, l in runs(np.where(line.sum(0) > a.shape[0] * 0.35)[0])]
    ys = [(f + l) / 2 for f, l in runs(np.where(line.sum(1) > a.shape[1] * 0.35)[0])]
    xs = ([0] if xs[0] > 20 else []) + xs
    ys = ([0] if ys[0] > 20 else []) + ys
    assert len(xs) >= cols + 1 and len(ys) >= rows + 1, (xs, ys)
    out = np.zeros((rows * 80, cols * 80, 3), np.uint8)
    clear = np.ones((rows * 80, cols * 80), bool)
    for r in range(rows):
        for c in range(cols):
            x0, x1 = int(xs[c]) + LINE_MARGIN, int(xs[c + 1]) - LINE_MARGIN + 1
            y0, y1 = int(ys[r]) + LINE_MARGIN, int(ys[r + 1]) - LINE_MARGIN + 1
            pitch_x, pitch_y = (xs[c + 1] - xs[c]) / 80, (ys[r + 1] - ys[r]) / 80
            w, h = round((x1 - x0) / pitch_x), round((y1 - y0) / pitch_y)
            ox, oy = round(LINE_MARGIN / pitch_x), round(LINE_MARGIN / pitch_y)
            w, h = min(w, 79 - ox), min(h, 79 - oy)
            cell = Image.fromarray(a[y0:y1, x0:x1].astype(np.uint8)).resize((w, h), Image.LANCZOS)
            cell = np.array(cell)
            m = edge_dark(cell)
            out[r * 80 + oy:r * 80 + oy + h, c * 80 + ox:c * 80 + ox + w] = cell
            clear[r * 80 + oy:r * 80 + oy + h, c * 80 + ox:c * 80 + ox + w] = m
    # specks: drawn pixels with no drawn neighbour (scaling noise near the lines)
    d = np.pad(~clear, 1)
    neighbours = sum(np.roll(np.roll(d, dy, 0), dx, 1) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx)[1:-1, 1:-1]
    clear |= ~clear & (neighbours == 0)
    save(out, clear, dst)


if __name__ == '__main__':
    if len(sys.argv) not in (5, 6):
        sys.exit(__doc__)
    src, dst, cols, rows = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    (native if len(sys.argv) == 6 and sys.argv[5] == 'native' else upscaled)(src, dst, cols, rows)
