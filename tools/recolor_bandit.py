#!/usr/bin/env python3
"""Recolour a stock Bandit sheet to the user's black-and-white Bandit.

    python tools/recolor_bandit.py STOCK_bandit_1.bmp OUT.bmp

The user restyled Bandit's first sheet (pictures 0-69, `art/bandit_0_edit.webp`):
black bandana, black trousers, white shirt, yellow gloves. His second sheet
(70-139: getting hit, run/dash attacks, weapon moves, burning/frozen) is still
the stock art, so this recolours its palette to match: the red bandana and the
blue trousers become charcoal greys, keeping their shading. Skin, shirt and
gloves are untouched. (The shirt's "K" emblem isn't added; that needs drawing.)
Palette-only, so every pixel and the transparent black stay exactly where they were.
"""
import io, sys
from PIL import Image

BANDANA = (28, 0.55)      # grey = base + shade * luminance: darker charcoal
TROUSERS = (18, 0.50)


def lum(r, g, b):
    return 0.299 * r + 0.587 * g + 0.114 * b


def recolour(r, g, b):
    if (r, g, b) == (0, 0, 0):
        return r, g, b                                   # transparent key
    if r > 90 and g < r * 0.5 and b < r * 0.5:           # red: the bandana (skin keeps more green)
        base, shade = BANDANA
    elif b > r + 25 and b > g + 10:                      # blue: the trousers
        base, shade = TROUSERS
    else:
        return r, g, b
    v = max(8, min(200, round(base + shade * lum(r, g, b))))
    return v, v, v


def main(src, out):
    with open(src, 'rb') as f:
        im = Image.open(io.BytesIO(f.read()))
    im.load()
    assert im.mode == 'P', 'expected an 8-bit sheet'
    pal = im.getpalette()
    changed = 0
    for k in range(len(pal) // 3):
        new = recolour(*pal[3 * k:3 * k + 3])
        if new != tuple(pal[3 * k:3 * k + 3]):
            changed += 1
        pal[3 * k:3 * k + 3] = new
    im.putpalette(pal)
    buf = io.BytesIO()
    im.save(buf, format='BMP')
    with open(out, 'wb') as f:
        f.write(buf.getvalue())
    print(f'{out}: {changed} palette colours recoloured')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
