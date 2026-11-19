#!/usr/bin/env python3
"""BenniWr: a computer-only fighter, the full Clide character (by YinYin Falcon, the
user's copy) with the user's sprites. Boss of stage 1-4.

    python tools/make_benniwr.py CLIDE_DIR mods/darthnox/assets

CLIDE_DIR holds the character as the user gave it: clide.dat, clide_ball.dat (LF2's
encryption), clide_ball.bmp, clide_explode.bmp and the sounds hit.wav, s.wav,
s2.wav, xyell.wav. The fighter sheets are the user's restyle (art/benniwr/), put
on Clide's grid by tools/import_gridded.py (sheet 0 upscaled, 1 and 2 `native`). Writes benniwr.txt, bw_ball.txt, bw_ball.bmp, bw_explode.bmp, the
sounds as snd/bw_*.wav, and stand-in portraits benniwr_f.bmp / benniwr_s.bmp
(idle-frame crops of the new art).

Clide's moves are kept as they are; only paths and object ids change:
  * his ball object (oid 295) is ours, BALL
  * the unused "test" frame 249 spawned LF2 object 5; it spawns BALL instead
"""
import os
import re
import shutil
import sys

from PIL import Image

ID, BALL = 81, 82
KEY = b'SiuHungIsAGoodBearBecauseHeIsVeryGood'
BS = '\\'
ours = lambda f: 'mods' + BS + 'darthnox' + BS + f
SOUNDS = ('hit', 's', 's2', 'xyell')


def decrypt(path):
    d = open(path, 'rb').read()
    return bytes((d[i] - KEY[i % len(KEY)]) & 255 for i in range(123, len(d))).decode('latin1')


def common(text):
    for n in SOUNDS:
        text = text.replace(f'sprite{BS}clide{BS}{n}.wav', ours(f'snd{BS}bw_{n}.wav'))
    return re.sub(r'oid: 295\b', f'oid: {BALL}', text)


def benniwr(src):
    text = decrypt(os.path.join(src, 'clide.dat'))
    text = re.sub(r'name:\s*\S+', 'name: BenniWr', text, count=1)
    text = text.replace(f'sprite{BS}clide{BS}clide_f.bmp', ours('benniwr_f.bmp'))
    text = text.replace(f'sprite{BS}clide{BS}clide_s.bmp', ours('benniwr_s.bmp'))
    for n in '012':
        text = text.replace(f'sprite{BS}clide{BS}clide_{n}.bmp', ours(f'benniwr_{n}.bmp'))
    text = re.sub(r'oid: 5\b', f'oid: {BALL}', text)
    return ("# BenniWr: Clide (YinYin Falcon's character, decrypted) with the user's sprites,\n"
            "# made by tools/make_benniwr.py. Computer-only: hidden from select.\n") + common(text)


def ball(src):
    text = decrypt(os.path.join(src, 'clide_ball.dat'))
    text = text.replace(f'sprite{BS}clide{BS}clide_ball.bmp', ours('bw_ball.bmp'))
    text = text.replace(f'sprite{BS}clide{BS}clide_explode.bmp', ours('bw_explode.bmp'))
    return "# BenniWr's ball: Clide's (decrypted). tools/make_benniwr.py\n" + common(text)


def portraits(assets):
    cell = Image.open(os.path.join(assets, 'benniwr_0.bmp')).convert('RGB').crop((0, 0, 79, 79))
    x0, y0, x1, y1 = cell.getbbox()
    side = 40
    left = (x0 + x1) // 2 - side // 2
    cell.crop((left, y0 - 1, left + side, y0 - 1 + side)).resize((120, 120), Image.LANCZOS).quantize(255).save(
        os.path.join(assets, 'benniwr_f.bmp'))
    cell.crop((left, y0 - 1, left + side, y0 - 1 + 45)).resize((40, 45), Image.LANCZOS).quantize(255).save(
        os.path.join(assets, 'benniwr_s.bmp'))


def main(src, assets):
    w = lambda name, text: open(os.path.join(assets, name), 'wb').write(text.encode('latin1'))
    w('benniwr.txt', benniwr(src))
    w('bw_ball.txt', ball(src))
    shutil.copyfile(os.path.join(src, 'clide_ball.bmp'), os.path.join(assets, 'bw_ball.bmp'))
    shutil.copyfile(os.path.join(src, 'clide_explode.bmp'), os.path.join(assets, 'bw_explode.bmp'))
    for n in SOUNDS:
        shutil.copyfile(os.path.join(src, f'{n}.wav'), os.path.join(assets, 'snd', f'bw_{n}.wav'))
    portraits(assets)
    print('wrote benniwr.txt, bw_ball.txt, bw_ball.bmp, bw_explode.bmp, snd/bw_*.wav, benniwr_f/s.bmp')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
