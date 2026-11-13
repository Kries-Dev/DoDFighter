#!/usr/bin/env python3
"""Add Mathilde's starry clone twirl to mathilde.bmp (pictures 104-107).

    python tools/make_mathilde_stars.py mods/darthnox/assets/mathilde.bmp

Her dance-spin pictures (56-59) with a ring of twinkling stars circling her,
for the DvJ clone. The ring turns a little each picture, the stars behind her
are hidden by her body, and their sizes pulse so the aura twinkles. Two unused
palette slots become a violet glow. Row 26 is written (or rewritten).
"""
import math, sys
import io
from PIL import Image

CELL, PITCH, COLS = 93, 94, 4      # 93 px cells, 1 px gutter
SOURCE_ROW, TARGET_ROW = 14, 26    # pictures 56-59 -> 104-107
RING = (44, 52, 37, 33)            # centre x, y and radii, around her body
STARS = 12
WHITE, PALE, GOLD = 1, 49, 39      # existing palette entries
VIOLET, LILAC = (190, 100, 220), (240, 185, 250)


def free_slots(sheet, n):
    # slots unused outside the row we write, so a re-run picks the same ones
    used = set(sheet.crop((0, 0, sheet.width, TARGET_ROW * PITCH)).get_flattened_data())
    free = [i for i in range(255, 0, -1) if i not in used]
    assert len(free) >= n, 'no free palette slots'
    return free[:n]


def put(px, x, y, colour, over):
    if 0 <= x < CELL and 0 <= y < CELL and (over or px[x, y] == 0):
        px[x, y] = colour


def star(px, x, y, arm, over, glow, glow2):
    for d in range(-arm, arm + 1):
        c = WHITE if abs(d) <= 1 else (PALE if abs(d) < arm else GOLD)
        put(px, x + d, y, c, over)
        put(px, x, y + d, c, over)
    if arm >= 3:
        for a, b in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            put(px, x + a, y + b, glow2, over)
            put(px, x + 2 * a, y + 2 * b, glow, over)


def main(path):
    with open(path, 'rb') as f:          # read into memory: Pillow memory-maps BMPs,
        sheet = Image.open(io.BytesIO(f.read()))   # which blocks overwriting on Windows
    sheet.load()
    assert sheet.mode == 'P', 'mathilde.bmp should be 8-bit palettised'
    rows = max(sheet.height // PITCH, TARGET_ROW + 1)
    if sheet.height < rows * PITCH:
        grown = Image.new('P', (sheet.width, rows * PITCH), 0)
        grown.putpalette(sheet.getpalette())
        grown.paste(sheet, (0, 0))
        sheet = grown
    glow, glow2 = free_slots(sheet, 2)
    pal = sheet.getpalette()
    pal[glow * 3:glow * 3 + 3], pal[glow2 * 3:glow2 * 3 + 3] = VIOLET, LILAC
    sheet.putpalette(pal)
    cx, cy, rx, ry = RING
    for col in range(COLS):
        x, y = col * PITCH, SOURCE_ROW * PITCH
        cell = sheet.crop((x, y, x + CELL, y + CELL))
        px = cell.load()
        for k in range(STARS):
            a = 2 * math.pi * k / STARS + col * 0.45            # the ring turns
            sx, sy = round(cx + rx * math.cos(a)), round(cy + ry * 0.55 * math.sin(a) - (k % 3 - 1) * 9)
            front = math.sin(a) > 0                              # lower half of the ring passes in front
            arm = (5, 2, 3, 1, 4, 2)[(k + col) % 6]                    # sizes pulse: twinkle
            star(px, sx, sy, arm, front, glow, glow2)
        sheet.paste(cell, (col * PITCH, TARGET_ROW * PITCH))
    out = io.BytesIO()                  # built in memory, then written in one go
    sheet.save(out, format='BMP')
    with open(path, 'wb') as f:
        f.write(out.getvalue())
    print(f'wrote pictures {TARGET_ROW * COLS}-{TARGET_ROW * COLS + 3}; sheet is now {rows} rows; glow slots {glow}, {glow2}')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
