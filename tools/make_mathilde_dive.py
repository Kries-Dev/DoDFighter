#!/usr/bin/env python3
"""Add Mathilde's diving-stab row to mathilde.bmp (pictures 100-103).

    python tools/make_mathilde_dive.py mods/darthnox/assets/mathilde.bmp

Her staff-extension frames (pictures 40-43) tilted nose-down by TILT degrees
around her waist, for the DvA-during-the-vault diving stab. Row 25 is written
(or rewritten, so this can be re-run after the sheet is rebuilt).
"""
import sys
from PIL import Image

CELL, PITCH, COLS = 93, 94, 4      # 93 px cells, 1 px gutter
SOURCE_ROW, TARGET_ROW = 10, 25    # pictures 40-43 -> 100-103
PIVOT = (44, 49)                   # her waist: centre (44, 89) minus 40
TILT = 35                          # degrees, clockwise = staff pointing down-forward


def main(path):
    sheet = Image.open(path)
    assert sheet.mode == 'P', 'mathilde.bmp should be 8-bit palettised'
    rows = max(sheet.height // PITCH, TARGET_ROW + 1)
    if sheet.height < rows * PITCH:
        grown = Image.new('P', (sheet.width, rows * PITCH), 0)
        grown.putpalette(sheet.getpalette())
        grown.paste(sheet, (0, 0))
        sheet = grown
    for col in range(COLS):
        x, y = col * PITCH, SOURCE_ROW * PITCH
        cell = sheet.crop((x, y, x + CELL, y + CELL))
        # Index 0 is the transparent key; NEAREST keeps the palette indices intact.
        tilted = cell.rotate(-TILT, resample=Image.NEAREST, center=PIVOT, fillcolor=0)
        sheet.paste(tilted, (col * PITCH, TARGET_ROW * PITCH))
    sheet.save(path)
    print(f'wrote pictures {TARGET_ROW * COLS}-{TARGET_ROW * COLS + 3}; sheet is now {rows} rows')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
