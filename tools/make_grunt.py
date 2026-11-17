#!/usr/bin/env python3
"""Make a restyled copy of a stock LF2 grunt (Bandit, Hunter ...) with the user's sprites.

    python tools/make_grunt.py STOCK.txt KEY "Display_Name"

STOCK.txt  the stock fighter's data, decrypted (e.g. stock-sprites/hunter/hunter.txt)
KEY        our file key: reads mods/darthnox/assets/KEY_0.bmp and KEY_1.bmp (made
           with tools/import_sheet.py ... STOCK_0.bmp), writes assets/KEY.txt and
           the portraits KEY_f.bmp (120x120) and KEY_s.bmp (40x45), cropped from the
           idle frame (stand-ins until real portraits come)
Everything below the header stays the stock fighter's: moves, damage, AI.
Pictures 140-279 (the stock "b" colour sheets, battle mode's second side) point at
the same two sheets. Used for EVS Fanboy (bandit) and EVS Hunter (hunter).
"""
import re
import sys
from PIL import Image

BS = '\\'


def main(stock, key, name):
    t = open(stock, 'rb').read().decode('latin1')
    end = t.index('<bmp_end>')
    head = t[:end]
    stock_key = re.search(r'file\(0-69\):\s*sprite\\sys\\(\w+)_0\.bmp', head)[1]
    ours = lambda f: 'mods' + BS + 'darthnox' + BS + f
    new = re.sub(r'name:\s*\S+', 'name: ' + name, head, count=1)
    new = re.sub(r'head:\s*\S+', lambda m: 'head: ' + ours(key + '_f.bmp'), new, count=1)
    new = re.sub(r'small:\s*\S+', lambda m: 'small: ' + ours(key + '_s.bmp'), new, count=1)
    for a, b in (('_0b', '_0'), ('_1b', '_1'), ('_0', '_0'), ('_1', '_1')):
        new = new.replace('sprite' + BS + 'sys' + BS + stock_key + a + '.bmp', ours(key + b + '.bmp'))
    note = (f"# {name.replace('_', ' ')}: a copy of LF2's {stock_key} (decrypted) with the user's sprites\n"
            f"# (art/{key}_*_edit.webp via tools/import_sheet.py), made by tools/make_grunt.py.\n"
            "# Everything below the header is the stock fighter's; pictures 140-279 reuse the two sheets.\n")
    open(f'mods/darthnox/assets/{key}.txt', 'wb').write((note + new + t[end:]).encode('latin1'))
    cell = Image.open(f'mods/darthnox/assets/{key}_0.bmp').convert('RGB').crop((0, 0, 79, 79))
    x0, y0, x1, y1 = cell.getbbox()
    side = int((x1 - x0) * 1.05)
    left = (x0 + x1) // 2 - side // 2
    cell.crop((left, y0 - 2, left + side, y0 - 2 + side)).resize((120, 120), Image.NEAREST).quantize(255).save(
        f'mods/darthnox/assets/{key}_f.bmp')
    cell.crop((left, y0 - 2, left + side, y0 - 2 + int(side * 45 / 40))).resize((40, 45), Image.LANCZOS).quantize(255).save(
        f'mods/darthnox/assets/{key}_s.bmp')
    print(new)


if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
