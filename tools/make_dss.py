#!/usr/bin/env python3
"""DSS: a computer-only fighter on Jack's data with the user's sprites (boss of 1-3).

    python tools/make_dss.py STOCK_DIR mods/darthnox/assets

STOCK_DIR holds LF2's Jack decrypted (jack.txt, dumped with a headless probe, see
HANDOFF.md). The sheets come from the user's art (art/dss/dss_{0,1}_edit.webp ->
assets/dss_{0,1}.bmp via tools/import_sheet.py ... jack_N.bmp; both fit at 0.54).
Jack's second-colour sheets (pictures 140-279) point at the same art. Writes
dss.txt and the stand-in portraits dss_f.bmp / dss_s.bmp (idle-frame crops).

Changes from Jack (the user's spec, 2026-11-19):
  * keeps Jack's D>A ball (240) and D^A flip (300-305)
  * the flip can be followed by a second flip: A late in the flip (304/305) goes
    to 310-315, a copy of the flip that costs FLIP2_MP, moves forward
    (FLIP2_DVX) to reach the target the first one launched, and has no third
  * DvA (new, 320-337, DVA_MP): three kicks on the run-attack kick pictures
    (16-18) that don't knock down, then Jack's ball-throwing animation without
    the ball; its fiery punch is the finisher hit that does
"""
import os
import re
import sys

from PIL import Image

ID = 80
FLIP2_MP = 75
FLIP2_DVX = 16                                   # the second flip chases the target the first launched
DVA_MP = 50
BS = '\\'
ours = lambda f: 'mods' + BS + 'darthnox' + BS + f

KICK_ITR = ('   itr:\n'
            '      kind: 0  x: 34  y: 19  w: 48  h: 36  dvx: 3  fall: 15  vrest: 5  bdefend: 16  injury: 25\n'
            '   itr_end:\n')
FINISH_ITR = ('   itr:\n'
              '      kind: 0  x: 40  y: 28  w: 50  h: 24  dvx: 10  dvy: -6  fall: 70  vrest: 15  bdefend: 60  injury: 45\n'
              '   itr_end:\n')
BDY = '   bdy:\n      kind: 0  x: 21  y: 12  w: 34  h: 66\n   bdy_end:\n'


def frames(text):
    return {int(m.group(1)): m.group(0) for m in re.finditer(r'<frame> (\d+) .*?<frame_end>', text, re.S)}


def set_field(block, key, value):
    """Set `key: value` on the frame's header line (the line with pic:)."""
    lines = block.split('\n')
    for i, line in enumerate(lines):
        if 'pic:' in line:
            if re.search(rf'\b{key}: -?\d+', line):
                lines[i] = re.sub(rf'\b{key}: -?\d+', f'{key}: {value}', line)
            else:
                lines[i] = line.rstrip() + f' {key}: {value}'
            break
    return '\n'.join(lines)


def header(n, name, pic, wait, nxt, cx, dvx=0, extra=''):
    return (f'<frame> {n} {name}\n'
            f'   pic: {pic}  state: 3  wait: {wait}  next: {nxt}  dvx: {dvx}  dvy: 0  dvz: 0  centerx: {cx}  centery: 79'
            f'  hit_a: 0  hit_d: 0  hit_j: 0{extra}\n')


def dva(fr):
    """Three kicks, then the ball throw without the ball."""
    out = []
    for k in range(3):
        b = 320 + 3 * k
        out.append(header(b, 'kick_combo', 16, 1, b + 1, 41, 4, f' mp: {DVA_MP}' if k == 0 else '')
                   + '  sound: data\\007.wav \n' + BDY + '<frame_end>')
        out.append(header(b + 1, 'kick_combo', 17, 2, b + 2, 42) + KICK_ITR + BDY + '<frame_end>')
        out.append(header(b + 2, 'kick_combo', 18, 2, b + 3 if k < 2 else 330, 41) + BDY + '<frame_end>')
    for src in range(240, 248):
        n = src - 240 + 330
        b = fr[src].replace(f'<frame> {src} ball1', f'<frame> {n} kick_finish', 1)
        b = re.sub(r' ?mp: \d+', '', b)
        b = re.sub(r' ?hit_Fa: \d+', '', b)
        b = re.sub(r'\s*opoint:.*?opoint_end:', '', b, flags=re.S)
        b = b.replace('data\\047.wav', 'data\\007.wav')
        nxt = int(re.search(r'next: (\d+)', b).group(1))
        if nxt != 999:
            b = set_field(b, 'next', nxt - 240 + 330)
        if src in (243, 244):                       # the fiery punch
            b = b.replace('   bdy:', FINISH_ITR + '   bdy:', 1)
        out.append(b)
    return out


def dss(stock):
    text = open(stock, encoding='latin1').read()
    end = text.index('<bmp_end>')
    head = text[:end]
    head = re.sub(r'name:\s*\S+', 'name: DSS', head, count=1)
    head = re.sub(r'head:\s*\S+', lambda m: 'head: ' + ours('dss_f.bmp'), head, count=1)
    head = re.sub(r'small:\s*\S+', lambda m: 'small: ' + ours('dss_s.bmp'), head, count=1)
    for n in '01':
        head = head.replace(f'sprite{BS}sys{BS}jack_{n}b.bmp', ours(f'dss_{n}.bmp'))
        head = head.replace(f'sprite{BS}sys{BS}jack_{n}.bmp', ours(f'dss_{n}.bmp'))
    body = text[end:]
    fr = frames(body)
    # DvA from wherever D>A starts
    body = body.replace('hit_Fa: 240', 'hit_Fa: 240 hit_Da: 320')
    fr = frames(body)
    # the second flip: A late in the flip
    for n in (304, 305):
        body = body.replace(fr[n], set_field(fr[n], 'hit_a', 310))
    copies = []
    for src in range(300, 306):
        b = fr[src].replace(f'<frame> {src} ', f'<frame> {src + 10} ', 1)
        nxt = int(re.search(r'next: (\d+)', b).group(1))
        if nxt != 999:
            b = set_field(b, 'next', nxt + 10)
        b = re.sub(r' ?mp: \d+', '', b)
        if src == 300:
            b = set_field(b, 'mp', FLIP2_MP)
        if src in (300, 301):
            b = set_field(b, 'dvx', FLIP2_DVX)
        copies.append(b)
    new = '\n\n'.join(copies + dva(fr))
    body = body.replace('<frame> 399 ', new + '\n\n<frame> 399 ', 1)
    note = ("# DSS: LF2's Jack (decrypted) with the user's sprites, a second flip and a DvA kick\n"
            "# combo, made by tools/make_dss.py (see its docstring). Computer-only: hidden from select.\n")
    return note + head + body


def portraits(assets):
    cell = Image.open(os.path.join(assets, 'dss_0.bmp')).convert('RGB').crop((0, 0, 79, 79))
    x0, y0, x1, y1 = cell.getbbox()
    side = 40
    left = (x0 + x1) // 2 - side // 2
    cell.crop((left, y0 - 1, left + side, y0 - 1 + side)).resize((120, 120), Image.LANCZOS).quantize(255).save(
        os.path.join(assets, 'dss_f.bmp'))
    cell.crop((left, y0 - 1, left + side, y0 - 1 + 45)).resize((40, 45), Image.LANCZOS).quantize(255).save(
        os.path.join(assets, 'dss_s.bmp'))


def main(stock_dir, assets):
    open(os.path.join(assets, 'dss.txt'), 'wb').write(dss(os.path.join(stock_dir, 'jack.txt')).encode('latin1'))
    portraits(assets)
    print('wrote dss.txt, dss_f.bmp, dss_s.bmp')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
