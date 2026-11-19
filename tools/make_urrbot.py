#!/usr/bin/env python3
"""Urrbot: a computer-only fighter on Freeze's data with the user's sprites.

    python tools/make_urrbot.py STOCK_DIR mods/darthnox/assets

STOCK_DIR holds LF2's Freeze decrypted (freeze.txt, freeze_ball.txt,
freeze_column.txt) and freeze_col.bmp, dumped with a headless probe (HANDOFF.md).
The sheets come from the user's art (art/urrbot/urrbot_{0,1,2}_edit.webp ->
assets/urrbot_{0,1,2}.bmp via tools/import_sheet.py ... freeze_N.bmp SCALE, SCALE
0.61 / 0.61 / 0.59: ~73 px standing like Freeze on all three). Writes urrbot.txt,
ub_ball.txt, ub_column.txt, ub_spike.txt + ub_spike.bmp and the stand-in portraits
urrbot_f.bmp / urrbot_s.bmp (idle-frame crops).

Changes from Freeze (the user's spec, 2026-11-19):
  * D>A: the ice ball flies 60% faster (ub_ball: Freeze's ball, flying dvx x 1.6)
  * D>J: the icicle row raises one more spike after Freeze's three, larger than his
    largest (ub_spike: the large spike scaled SPIKE_SCALE, sprite and boxes); the row
    is ub_column, Freeze's column object whose walker drops the extra spike
  * no D^J whirlwind and no DvJ ice sword
"""
import os
import re
import sys

import numpy as np
from PIL import Image

URRBOT, BALL, SPIKE, COLUMN = 76, 77, 78, 79
BALL_SPEED = 1.6
SPIKE_SCALE = 1.4
BS = '\\'
ours = lambda f: 'mods' + BS + 'darthnox' + BS + f


def frames(text):
    return {int(m.group(1)): m.group(0) for m in re.finditer(r'<frame> (\d+) .*?<frame_end>', text, re.S)}


def header_line(block, key, value):
    lines = block.split('\n')
    for i, line in enumerate(lines):
        if 'pic:' in line:
            if re.search(rf'\b{key}: -?[\d.]+', line):
                lines[i] = re.sub(rf'\b{key}: -?[\d.]+', f'{key}: {value}', line)
            else:
                lines[i] = line.rstrip() + f'  {key}: {value}'
            break
    return '\n'.join(lines)


def urrbot(stock):
    text = open(stock, encoding='latin1').read()
    end = text.index('<bmp_end>')
    head = text[:end]
    head = re.sub(r'name:\s*\S+', 'name: Urrbot', head, count=1)
    head = re.sub(r'head:\s*\S+', lambda m: 'head: ' + ours('urrbot_f.bmp'), head, count=1)
    head = re.sub(r'small:\s*\S+', lambda m: 'small: ' + ours('urrbot_s.bmp'), head, count=1)
    for n in '012':
        head = head.replace(f'sprite{BS}sys{BS}freeze_{n}.bmp', ours(f'urrbot_{n}.bmp'))
    body = text[end:]
    # only D>A (235) and D>J (245): no D^J whirlwind (260), no DvJ ice sword (270)
    body = re.sub(r' ?hit_Uj: 260', '', body)
    body = re.sub(r' ?hit_Dj: 270', '', body)
    body = body.replace('oid: 209', f'oid: {BALL}')                      # the faster ball
    body = body.replace('action: 100  dvx: 0  dvy: 0  oid: 212', f'action: 100  dvx: 0  dvy: 0  oid: {COLUMN}')   # the longer row
    note = ("# Urrbot: LF2's Freeze (decrypted) with the user's sprites and changed specials,\n"
            "# made by tools/make_urrbot.py (see its docstring). Computer-only: hidden from select.\n")
    return note + head + body


def ball(stock):
    text = open(stock, encoding='latin1').read()
    fr = frames(text)
    for n, block in fr.items():
        if re.search(r'state: 3000\b', block):
            dvx = float(re.search(r'dvx: (-?[\d.]+)', block).group(1))
            text = text.replace(block, header_line(block, 'dvx', round(dvx * BALL_SPEED)))   # whole numbers: 9 -> 14
    return f"# Urrbot's ice ball: Freeze's (decrypted), flying {BALL_SPEED:g}x as fast. tools/make_urrbot.py\n" + text


def column(stock):
    """Freeze's column object; its walker (100-103) drops one more spike: ub_spike."""
    text = open(stock, encoding='latin1').read()
    fr = frames(text)
    walker_last = fr[103]
    new_last = header_line(header_line(walker_last, 'next', 104), 'wait', 5)
    extra = ('<frame> 104 column_mother\n'
             '   pic: 6  state: 3005  wait: 1  next: 1000  dvx: 6  dvy: 0  dvz: 0  centerx: 1  centery: 0  hit_a: 0  hit_d: 0  hit_j: 0\n'
             '   opoint:\n'
             f'      kind: 1  x: 78  y: 5  action: 0  dvx: 0  dvy: 0  oid: {SPIKE}  facing: 0\n'
             '   opoint_end:\n'
             '<frame_end>')
    text = text.replace(walker_last, new_last + '\n\n' + extra)
    return "# Urrbot's icicle row: Freeze's column object, its walker adds a fourth, larger spike (104). tools/make_urrbot.py\n" + text


def spike(stock):
    """Freeze's spike frames (all below 100) with every coordinate scaled, on ub_spike.bmp."""
    text = open(stock, encoding='latin1').read()
    end = text.index('<bmp_end>')
    cell = round(109 * SPIKE_SCALE)
    head = text[:end]
    line = f'file(0-27): {ours("ub_spike.bmp")}  w: {cell}  h: {cell}  row: 7  col: 4'
    head = re.sub(r'file\(0-27\):[^\n]*', lambda m: line, head)
    head = re.sub(r'\nfile\(28-37\):[^\n]*', '', head)
    s = lambda v: str(round(int(v) * SPIKE_SCALE))
    out = []
    for n, block in frames(text[end:]).items():
        if n >= 100:
            continue
        b = re.sub(r'(centerx|centery): (-?\d+)', lambda m: f'{m.group(1)}: {s(m.group(2))}', block)
        b = re.sub(r'(?m)^(\s+kind: \d+\s+)(x: -?\d+\s+y: -?\d+\s+w: \d+\s+h: \d+)',
                   lambda m: m.group(1) + re.sub(r'([xywh]): (-?\d+)', lambda k: f'{k.group(1)}: {s(k.group(2))}', m.group(2)), b)
        out.append(b)
    return (f"# Urrbot's large spike: Freeze's spike frames scaled x{SPIKE_SCALE:g} (sprite and boxes). tools/make_urrbot.py\n"
            + head + '<bmp_end>\n\n' + '\n\n'.join(out) + '\n')


def spike_sheet(src, dst):
    im = np.array(Image.open(src).convert('RGB'))
    cell, big = 109, round(109 * SPIKE_SCALE)
    out = np.zeros((4 * (big + 1), 7 * (big + 1), 3), np.uint8)
    for r in range(4):
        for c in range(7):
            sub = im[r * (cell + 1):r * (cell + 1) + cell, c * (cell + 1):c * (cell + 1) + cell]
            mask = Image.fromarray(((sub.sum(2) > 0) * 255).astype(np.uint8)).resize((big, big), Image.NEAREST)
            rgb = Image.fromarray(sub).resize((big, big), Image.LANCZOS)
            a = np.array(rgb)
            a[np.array(mask) == 0] = 0
            a[(np.array(mask) > 0) & (a.max(axis=2) < 8)] = (8, 8, 8)
            out[r * (big + 1):r * (big + 1) + big, c * (big + 1):c * (big + 1) + big] = a
    q = Image.fromarray(out).quantize(255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    idx = np.array(q, dtype=np.int16) + 1
    idx[out.sum(axis=2) == 0] = 0
    pal = q.getpalette()[:765]
    o = Image.fromarray(idx.astype(np.uint8), 'P')
    o.putpalette([0, 0, 0] + pal + [0, 0, 0] * (255 - len(pal) // 3))
    o.save(dst)


def portraits(assets):
    cell = Image.open(os.path.join(assets, 'urrbot_0.bmp')).convert('RGB').crop((0, 0, 79, 79))
    x0, y0, x1, y1 = cell.getbbox()
    side = 40
    left = (x0 + x1) // 2 - side // 2
    cell.crop((left, y0 - 1, left + side, y0 - 1 + side)).resize((120, 120), Image.LANCZOS).quantize(255).save(
        os.path.join(assets, 'urrbot_f.bmp'))
    cell.crop((left, y0 - 1, left + side, y0 - 1 + 45)).resize((40, 45), Image.LANCZOS).quantize(255).save(
        os.path.join(assets, 'urrbot_s.bmp'))


def main(stock_dir, assets):
    w = lambda name, text: open(os.path.join(assets, name), 'wb').write(text.encode('latin1'))
    w('urrbot.txt', urrbot(os.path.join(stock_dir, 'freeze.txt')))
    w('ub_ball.txt', ball(os.path.join(stock_dir, 'freeze_ball.txt')))
    w('ub_column.txt', column(os.path.join(stock_dir, 'freeze_column.txt')))
    w('ub_spike.txt', spike(os.path.join(stock_dir, 'freeze_column.txt')))
    spike_sheet(os.path.join(stock_dir, 'freeze_col.bmp'), os.path.join(assets, 'ub_spike.bmp'))
    portraits(assets)
    print('wrote urrbot.txt, ub_ball.txt, ub_column.txt, ub_spike.txt, ub_spike.bmp, urrbot_f/s.bmp')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
