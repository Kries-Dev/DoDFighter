#!/usr/bin/env python3
"""Ironhide: a computer-only fighter on Deep's data with the user's sprites.

    python tools/make_ironhide.py STOCK_DIR mods/darthnox/assets

STOCK_DIR holds LF2's Deep decrypted (deep.txt, deep_ball.txt; dumped with a
headless probe, see HANDOFF.md). The sheets come from the user's art
(art/ironhide/ironhide_{0,1,2}_edit.webp -> assets/ironhide_{0,1,2}.bmp via
tools/import_sheet.py ... deep_N.bmp SCALE, SCALE 0.61 / 0.59 / 0.44: the three
sheets were drawn at different sizes; these make him ~74 px standing like Deep). Writes ironhide.txt, ih_wave.txt and the
stand-in portraits ironhide_f.bmp / ironhide_s.bmp (idle-frame crops).

Changes from Deep (the user's spec, 2026-11-18):
  * only three specials: D>A, DvA, D>J (his D^J leap and the D>J from a grab are gone)
  * D>A: every blast throws two waves in a 30 degree cone (+-15 degrees in depth):
    ih_wave.txt is Deep's wave with two flying loops whose hit_j moves them
    WAVE_DZ px a tick nearer / further while they fly 15 px a tick forward
  * DvA: launches straight up (no forward push) and the sword spins twice
    (frames 261-264 played again as 286-289 before landing in 265); the spin's
    hits rest 4 ticks so the second spin hits too, its launch hits 54 -> 36
  * D>J: MP 150 -> STRAFE_MP, the middle of the dash (298-303, three of its hits)
    cut and one fast frame slowed, so it travels ~40% less far
  * he keeps Deep's voice (data\\045.wav on D>J): the user asked for it (2026-11-18);
    the rule against 045 is for the user's own fighters
"""
import os
import re
import sys

from PIL import Image

ID, WAVE_ID = 74, 75
WAVE_SPEED = 15                                   # Deep's wave: dvx 15 a tick
# depth speed for +-15 degrees: tan(15) x 15 = 4 in theory, but measured in a match the
# waves only fan to ~10.5 degrees at 4 (dz 36 over dx 195); 6 gives ~15
WAVE_DZ = 6
STRAFE_MP = 100
STRAFE_CUT = range(298, 304)                     # D>J frames dropped (297 jumps to 304)
DVA_SPIN = {261: 286, 262: 287, 263: 288, 264: 289}   # second spin's copies
BS = '\\'


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


def drop_field(block, key):
    return re.sub(rf' ?\b{key}: -?\d+', '', block)


def itr_launch_up(block, dvy=None):
    """Hits barely push sideways: itr dvx -> 1 (dvy kept, or set). Not 0: the engine
    gives a dvx 0 hit a default push of 5 the attacker's way (combat.lua)."""
    def fix(m):
        s = re.sub(r'dvx: -?\d+', 'dvx: 1', m.group(0))
        if dvy is not None:
            s = re.sub(r'dvy: -?\d+', f'dvy: {dvy}', s) if 'dvy:' in s else s.replace('dvx: 1', f'dvx: 1  dvy: {dvy}')
        return s
    return re.sub(r'itr:.*?itr_end:', fix, block, flags=re.S)


def ironhide(stock):
    text = open(stock, encoding='latin1').read()
    end = text.index('<bmp_end>')
    head = text[:end]
    ours = lambda f: 'mods' + BS + 'darthnox' + BS + f
    head = re.sub(r'name:\s*\S+', 'name: Ironhide', head, count=1)
    head = re.sub(r'head:\s*\S+', lambda m: 'head: ' + ours('ironhide_f.bmp'), head, count=1)
    head = re.sub(r'small:\s*\S+', lambda m: 'small: ' + ours('ironhide_s.bmp'), head, count=1)
    for n in '012':
        head = head.replace(f'sprite{BS}sys{BS}deep_{n}.bmp', ours(f'ironhide_{n}.bmp'))
    body = text[end:]
    fr = frames(body)

    def put(n, block):
        nonlocal body
        body = body.replace(fr[n], block)
        fr[n] = block

    # specials: keep hit_Fa (D>A 235), hit_Da (DvA 260), hit_Fj 290 (D>J); drop D^J and the grab's D>J
    for n, block in list(fr.items()):
        new = drop_field(block, 'hit_Uj')
        if re.search(r'hit_Fj: 310', new):
            new = drop_field(new, 'hit_Fj')
        if new != block:
            put(n, new)
    # D>A: a second wave one tick after each first, both on the cone's edges
    for n, block in list(fr.items()):
        m = re.search(r'opoint:.*?oid: 203.*?opoint_end:', block, re.S)
        if not m:
            continue
        first = m.group(0).replace('oid: 203', f'oid: {WAVE_ID}').replace('action: 0', 'action: 50')
        put(n, block.replace(m.group(0), first))
        nxt = int(re.search(r'next: (\d+)', block).group(1))
        second = first.replace('action: 50', 'action: 60')
        put(nxt, fr[nxt].replace('<frame_end>', '   ' + second + '\n<frame_end>', 1) if 'opoint:' not in fr[nxt] else fr[nxt])
    # DvA: straight-up launch, two spins
    for n in list(range(260, 286)):
        if n in fr:
            b = fr[n]
            if n in (263, 264, 279, 280):
                b = itr_launch_up(b, dvy=-14)       # these pulled the victim back; now they keep him going up
            else:
                b = itr_launch_up(b)
            put(n, b)
    # both spins hit: a 4-tick rest (Deep's 10 would skip the second spin), launch hits 54 -> 36
    for n in DVA_SPIN:
        b = re.sub(r'vrest: \d+', 'vrest: 4', fr[n])
        b = re.sub(r'injury: 54', 'injury: 36', b)
        put(n, b)
    for src, dst in DVA_SPIN.items():
        copy = fr[src].replace(f'<frame> {src} ', f'<frame> {dst} ', 1)
        nxt = DVA_SPIN.get(src + 1, 265) if src < 264 else 265
        copy = set_field(copy, 'next', nxt)
        body = body.replace('<frame> 285 ', copy + '\n\n<frame> 285 ', 1)
        fr[dst] = copy
    put(264, set_field(fr[264], 'next', 286))
    # D>J: cheaper, shorter, fewer hits
    put(290, set_field(fr[290], 'mp', STRAFE_MP))
    put(297, set_field(fr[297], 'next', 304))
    put(295, set_field(fr[295], 'dvx', 9))
    for n in STRAFE_CUT:
        body = body.replace(fr[n], '')
    note = ("# Ironhide: LF2's Deep (decrypted) with the user's sprites and changed specials,\n"
            "# made by tools/make_ironhide.py (see its docstring). Computer-only: hidden from select.\n")
    return note + head + body


def wave(stock):
    text = open(stock, encoding='latin1').read()
    end = text.index('<bmp_end>')
    fr = frames(text)
    extra = []
    for base, hit_j in ((50, 50 + WAVE_DZ), (60, 50 - WAVE_DZ)):
        for n in range(6):
            b = fr[n].replace(f'<frame> {n} ', f'<frame> {base + n} ', 1)
            b = re.sub(r'hit_j: -?\d+', f'hit_j: {hit_j}', b, count=1)
            b = set_field(b, 'next', base + n + 1 if n < 5 else base)
            extra.append(b)
    note = (f"# Ironhide's wave: Deep's (decrypted) with two more flying loops, 50-55 drifting\n"
            f"# {WAVE_DZ} px a tick one way in depth and 60-65 the other (hit_j - 50 = z speed): the\n"
            "# two edges of a 30 degree cone. Made by tools/make_ironhide.py.\n")
    return note + text[:end] + text[end:].rstrip() + '\n\n' + '\n\n'.join(extra) + '\n'


def portraits(assets):
    cell = Image.open(os.path.join(assets, 'ironhide_0.bmp')).convert('RGB').crop((0, 0, 79, 79))
    x0, y0, x1, y1 = cell.getbbox()
    side = 40
    left = (x0 + x1) // 2 - side // 2 - 2
    face = cell.crop((left, y0 - 1, left + side, y0 - 1 + side))
    face.resize((120, 120), Image.LANCZOS).quantize(255).save(os.path.join(assets, 'ironhide_f.bmp'))
    cell.crop((left, y0 - 1, left + side, y0 - 1 + 45)).resize((40, 45), Image.LANCZOS).quantize(255).save(
        os.path.join(assets, 'ironhide_s.bmp'))


def main(stock_dir, assets):
    open(os.path.join(assets, 'ironhide.txt'), 'wb').write(ironhide(os.path.join(stock_dir, 'deep.txt')).encode('latin1'))
    open(os.path.join(assets, 'ih_wave.txt'), 'wb').write(wave(os.path.join(stock_dir, 'deep_ball.txt')).encode('latin1'))
    portraits(assets)
    print('wrote ironhide.txt, ih_wave.txt, ironhide_f.bmp, ironhide_s.bmp')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
