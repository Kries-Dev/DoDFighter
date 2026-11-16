#!/usr/bin/env python3
"""Write our stage-mode file from LF2's: which of our stages each sub-stage is fought
on, and its music. The waves themselves (who, how many, order, HP) stay LF2's.

    python tools/stage_layout.py tools/lf2_stage.txt mods/darthnox/stage.txt
    python tools/stage_dat.py mods/darthnox/stage.txt mods/darthnox/assets/stage.dat

tools/lf2_stage.txt is LF2's data/stage.dat decrypted (tools/stage_dat.py decrypts;
keep it unedited). For each sub-stage in
LAYOUT (run id: 0 = 1-1, 4 = 1-5, 10 = 2-1 ...):
  * the scroll bounds are scaled so the last one is the stage's right wall (players
    must walk there to go on; the walls are camera.lua's WALLS), never below one
    screen (794), and kept strictly rising: when two phases in a row share a bound
    the engine never ends the last phase
  * item/prisoner x positions are scaled the same way (negative x = walk in from
    the left, left alone)
  * music: `music` plays from the first phase, `boss` when a boss phase starts;
    LF2's own music lines are dropped (None keeps LF2's)
The backgrounds themselves are picked in mods/darthnox/stage.lua (STAGES) and must
match the walls used here.
"""
import re
import sys

SCREEN_W = 794
BG = 'mods/darthnox/bg/'
WALL = {'roof': 1749, 'roofn': 863, 'gate': 1523, 'yard': 1365, 'cells': 1506, 'barr': 1471, 'hall': 1471}   # = camera.lua WALLS
JUNGLE, JUNGLE_END, BOSS = BG + 'urban_jungle.wma', BG + 'jungle_end.wma', BG + 'boss_appears.wma'
STAGE1 = [BG + f'fort_{n}.wma' for n in range(1, 6)]        # stage 1's five tracks (fort_1 ... fort_5)

# run id -> (stage key or None for LF2's own background, music from phase 0, boss music)
LAYOUT = {
    0: ('gate', None, None),               # 1-1: Fortress Gate
    1: ('yard', None, None),               # 1-2: Barracks Yard
    2: ('cells', None, None),              # 1-3: Cell Block
    3: ('barr', None, None),               # 1-4: Barracks
    4: ('hall', None, None),               # 1-5: Throne Hall
    10: ('roof', JUNGLE, None),            # 2-1 .. 2-4: Sunset Rooftop, "Urban Jungle"
    11: ('roof', None, None),
    12: ('roof', None, None),
    13: ('roof', None, None),
    14: ('roofn', JUNGLE_END, BOSS),       # 2-5: Rooftop at Night, "Urban Jungle end", "Boss appears 1"
}


def layout(text, music_override=None):
    for sid, (key, music, boss) in sorted(LAYOUT.items()):
        music = (music_override or {}).get(sid, music)
        i = text.index(f'<stage> id: {sid} ')
        j = text.index('<stage_end>', i)
        block = text[i:j]
        phases = block.split('<phase>')
        head = phases[0].rstrip()
        if key:
            wall = WALL[key]
            last = max(int(b) for b in re.findall(r'bound:\s*(\d+)', block))
            f = wall / last
            head += f'   # DoD: {key}; bounds and x scaled x{f:.3f} (last bound = its right wall)'
        else:
            f = None
            head += '   # DoD: LF2\'s background'
        out, prev = [head + '\n        '], 0
        for k, ph in enumerate(phases[1:]):
            if f:
                b = int(re.search(r'bound:\s*(\d+)', ph)[1])
                b = max(SCREEN_W, round(b * f), prev + 17)
                prev = b
                ph = re.sub(r'bound:\s*\d+', f'bound: {b}', ph, count=1)
                ph = re.sub(r'(?<![-\d])x:\s*(\d+)', lambda m: f'x: {round(int(m[1]) * f)}', ph)
            new_music = music if k == 0 else None
            if boss and '<boss>' in ph:
                new_music = boss
            if music or boss:
                ph = re.sub(r'\n\s*music:[^\n]*', '', ph)
            if new_music:
                ph = re.sub(r'^( bound: \d+[^\n]*\n)', lambda m: m[1] + f'                music: {new_music}\n', ph, count=1)
            out.append(ph)
        text = text[:i] + '<phase>'.join(out) + text[j:]
    return text


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src = open(sys.argv[1], 'rb').read().decode('latin1')
    open(sys.argv[2], 'wb').write(layout(src).encode('latin1'))
    print(f'{sys.argv[2]}: stages {sorted(LAYOUT)}')
