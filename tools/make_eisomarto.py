#!/usr/bin/env python3
"""Eisomarto: a computer-only fighter, the full Leo character (by Prince Freeza and
YinYin Falcon, the user's Leo.zip) with the user's sprites. Boss of stage 1-5.

    python tools/make_eisomarto.py Leo.zip mods/darthnox/assets [STOCK_OUT]

Reads from the zip: sprite/leo/leo.dat, leo_weapon.dat, leo_ball.dat (LF2's
encryption), leo_weapon.bmp, leo_ball.bmp (RLE-compressed: decoded here to plain
8-bit BMPs), 020.wav, 046.wav. The fighter sheet is the user's restyle
(art/eisomarto/eisomarto_edit.webp, Leo's 10 x 14 layout at 1.325x) put on the grid
by tools/import_sheet.py ... 800 1120 (assets/eisomarto.bmp, run that first); this
then moves each frame sideways onto Leo's own (align). STOCK_OUT, if given, gets
Leo's own sheet decoded (leo.bmp), for comparing.

Writes eisomarto.txt, eiso_knife.txt + .bmp, eiso_ball.txt + .bmp,
snd/eiso_020.wav, snd/eiso_046.wav and stand-in portraits eisomarto_f.bmp /
eisomarto_s.bmp (idle-frame crops).

Leo's moves are kept as they are; only paths and ids change (his readme's data.txt):
  * id 124 (leo_weapon, the shy knife he holds, a light weapon) is KNIFE
  * id 130 (leo_ball: energy bullets, bullet storm, double knife) is BALL; its
    frame 300 (state 8124, "become object 124") turns into KNIFE: that is how he
    draws the shy knife
  * leo_weapon's first file line named sprite/sys/weapon9.bmp (not in LF2) for the
    same pictures as leo_weapon.bmp; dropped
His original AI (ai/29.as) needs a ddraw.dll wrapper; ours is in mods/darthnox/ai.lua.
"""
import io
import os
import re
import struct
import sys
import zipfile

import numpy as np
from PIL import Image

ID, KNIFE, BALL = 83, 84, 85
KEY = b'SiuHungIsAGoodBearBecauseHeIsVeryGood'
BS = '\\'
ours = lambda f: 'mods' + BS + 'darthnox' + BS + f
leo = lambda f: 'sprite' + BS + 'leo' + BS + f


def decrypt(data):
    return bytes((data[i] - KEY[i % len(KEY)]) & 255 for i in range(123, len(data))).decode('latin1')


def rle8(data):
    """Decode an RLE8 BMP (Pillow can't) into a palette image."""
    off, = struct.unpack('<I', data[10:14])
    hsize, = struct.unpack('<I', data[14:18])
    w, h = struct.unpack('<ii', data[18:26])
    colours, = struct.unpack('<I', data[46:50])
    colours = colours or 256
    pal = data[14 + hsize:14 + hsize + 4 * colours]
    palette = []
    for i in range(colours):
        b, g, r = pal[4 * i:4 * i + 3]
        palette += [r, g, b]
    pix = np.zeros((abs(h), w), np.uint8)
    x, y, i, src = 0, 0, off, data
    while i < len(src):
        n, v = src[i], src[i + 1]
        i += 2
        if n:
            pix[y, x:x + n] = v
            x += n
        elif v == 0:
            x, y = 0, y + 1
        elif v == 1:
            break
        elif v == 2:
            x, y = x + src[i], y + src[i + 1]
            i += 2
        else:
            pix[y, x:x + v] = list(src[i:i + v])
            x += v
            i += v + (v & 1)
    if h > 0:
        pix = pix[::-1]
    img = Image.fromarray(pix, 'P')
    img.putpalette(palette + [0] * (768 - len(palette)))
    return img


def bitmap(data):
    comp, = struct.unpack('<I', data[30:34])
    return rle8(data) if comp == 1 else Image.open(io.BytesIO(data))


def common(text):
    for n in ('020', '046'):
        text = text.replace(leo(f'{n}.wav'), ours(f'snd{BS}eiso_{n}.wav'))
    text = re.sub(r'oid: *124\b', f'oid: {KNIFE}', text)
    text = re.sub(r'state: *8124\b', f'state: {8000 + KNIFE}', text)   # "become object 124": the drawn shy knife
    return re.sub(r'oid: *130\b', f'oid: {BALL}', text)


def fighter(z):
    text = decrypt(z('leo.dat'))
    text = re.sub(r'name:\s*\S+', 'name: Eisomarto', text, count=1)
    text = text.replace(leo('leo_f.bmp'), ours('eisomarto_f.bmp'))
    text = text.replace(leo('leo_s.bmp'), ours('eisomarto_s.bmp'))
    text = text.replace(leo('leo.bmp'), ours('eisomarto.bmp'))
    return ("# Eisomarto: Leo (Prince Freeza, YinYin Falcon; decrypted) with the user's sprites,\n"
            "# made by tools/make_eisomarto.py. Computer-only: hidden from select.\n") + common(text)


def knife(z):
    text = decrypt(z('leo_weapon.dat'))
    text = re.sub(r'[ \t]*file\(0-99\):\s*sprite\\sys\\weapon9\.bmp[^\n]*\n', '', text)
    text = text.replace(leo('leo_weapon.bmp'), ours('eiso_knife.bmp'))
    return "# Eisomarto's shy knife: Leo's leo_weapon (decrypted). tools/make_eisomarto.py\n" + common(text)


def ball(z):
    text = decrypt(z('leo_ball.dat'))
    text = text.replace(leo('leo_ball.bmp'), ours('eiso_ball.bmp'))
    return "# Eisomarto's bullets: Leo's leo_ball (decrypted). tools/make_eisomarto.py\n" + common(text)


def align(sheet_path, stock):
    """Move each cell of our sheet sideways onto Leo's own frame (best overlap,
    -3..8 px: the user's frames sit 0-8 px right of Leo's), so his centres and
    boxes fit. Running it again changes nothing (the best shift is then 0)."""
    # read through memory: Pillow maps an open BMP, and Windows then refuses the rewrite
    img = Image.open(io.BytesIO(open(sheet_path, 'rb').read()))
    a, o = np.array(img), np.array(stock.convert('P') if stock.mode != 'P' else stock)
    out = a.copy()
    for r in range(a.shape[0] // 80):
        for c in range(a.shape[1] // 80):
            cell = a[r * 80:r * 80 + 79, c * 80:c * 80 + 79]
            A, O = cell != 0, o[r * 80:r * 80 + 79, c * 80:c * 80 + 79] != 0
            if A.sum() < 50 or O.sum() < 50:
                continue
            score = lambda s: (np.roll(A, -s, 1) & O).sum() / max(1, (np.roll(A, -s, 1) | O).sum())
            s = max(range(-3, 9), key=score)
            moved = np.zeros_like(cell)
            if s >= 0:
                moved[:, :79 - s] = cell[:, s:]
            else:
                moved[:, -s:] = cell[:, :79 + s]
            out[r * 80:r * 80 + 79, c * 80:c * 80 + 79] = moved
    new = Image.fromarray(out, 'P')
    new.putpalette(img.getpalette())
    new.save(sheet_path)


def portraits(assets):
    cell = Image.open(os.path.join(assets, 'eisomarto.bmp')).convert('RGB').crop((0, 0, 79, 79))
    x0, y0, x1, y1 = cell.getbbox()
    side = 40
    left = (x0 + x1) // 2 - side // 2
    cell.crop((left, y0 - 1, left + side, y0 - 1 + side)).resize((120, 120), Image.LANCZOS).quantize(255).save(
        os.path.join(assets, 'eisomarto_f.bmp'))
    cell.crop((left, y0 - 1, left + side, y0 - 1 + 45)).resize((40, 45), Image.LANCZOS).quantize(255).save(
        os.path.join(assets, 'eisomarto_s.bmp'))


def main(zip_path, assets, stock_out=None):
    archive = zipfile.ZipFile(zip_path)
    z = lambda name: archive.read('sprite/leo/' + name)
    w = lambda name, text: open(os.path.join(assets, name), 'wb').write(text.encode('latin1'))
    w('eisomarto.txt', fighter(z))
    w('eiso_knife.txt', knife(z))
    w('eiso_ball.txt', ball(z))
    bitmap(z('leo_weapon.bmp')).save(os.path.join(assets, 'eiso_knife.bmp'))
    bitmap(z('leo_ball.bmp')).save(os.path.join(assets, 'eiso_ball.bmp'))
    for n in ('020', '046'):
        open(os.path.join(assets, 'snd', f'eiso_{n}.wav'), 'wb').write(z(f'{n}.wav'))
    stock = bitmap(z('leo.bmp'))
    if stock_out:
        stock.save(stock_out)
    align(os.path.join(assets, 'eisomarto.bmp'), stock)
    portraits(assets)
    print('wrote eisomarto.txt, eiso_knife.txt/.bmp, eiso_ball.txt/.bmp, snd/eiso_020/046.wav, eisomarto_f/s.bmp')


if __name__ == '__main__':
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    main(*sys.argv[1:])
