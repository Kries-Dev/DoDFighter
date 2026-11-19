#!/usr/bin/env python3
"""Write our stage-mode file from LF2's: which of our stages each sub-stage is fought
on, and its music. The waves themselves (who, how many, order, HP) stay LF2's, except
for the sub-stages in CUSTOM (1-1 to 1-3), whose waves are written here.

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
BOSS1 = BG + 'boss_1.wma'                                    # stage 1's boss music (1-5's boss wave)

# run id -> (stage key or None for LF2's own background, music from phase 0, boss music)
LAYOUT = {
    0: ('gate', STAGE1[0], None),          # 1-1: Fortress Gate, "Fortress Gate 1-1"
    1: ('yard', STAGE1[1], None),          # 1-2: Barracks Yard, "Barrack gates 1-2"
    2: ('cells', STAGE1[2], None),         # 1-3: Cell Block, "Cell Blocks 1-3"
    3: ('barr', STAGE1[3], None),          # 1-4: Barracks, "Barrack inner 1-4" (no switch at its boss wave)
    4: ('hall', STAGE1[4], BOSS1),         # 1-5: Throne Hall, "Grand Hall 1-5", then "Boss 1" at the boss wave
    10: ('roof', JUNGLE, None),            # 2-1 .. 2-4: Sunset Rooftop, "Urban Jungle"
    11: ('roof', None, None),
    12: ('roof', None, None),
    13: ('roof', None, None),
    14: ('roofn', JUNGLE_END, BOSS),       # 2-5: Rooftop at Night, "Urban Jungle end", "Boss appears 1"
}

# Sub-stages whose waves are ours instead of LF2's (bounds already in our stage's pixels).
# id 3000 = a random Bandit or Hunter each spawn; in stage 1 those are EVS Fanboy / EVS
# Hunter (stage_mode.lua SWAPS). times = how many in all, ratio 1 = scales with players.
def fortress_waves(hp, line1, line2, wall, boss_id, boss_hp):
    """Six waves under two shared lines, then a boss: about twice LF2's enemies (~25 for
    one player instead of ~12, ratio 1 entries scale with players), random EVS grunts
    plus one extra EVS Fanboy (Bandit 30 in stage 1) in every wave, drinks along the way
    (stage_mode.lua drops them inside the camera view), EVS grunts streaming in
    (<soldier>) while the boss stands. A wave's bound is a wall until it is cleared, so
    waves share bounds (the next starts at once, no GO arrow; only the last phase needs
    a bound of its own): six rising bounds felt like invisible walls every few steps."""
    g = lambda times, ratio=False: f'id: 3000  hp: {hp}  times: {times}' + ('  ratio: 1.0' if ratio else '')
    fanboy = f'id: 30  hp: {hp}'
    return [
        (line1, [fanboy, g(2, True), g(2)]),
        (line1, [fanboy, g(3, True), g(2)]),
        (line1, [fanboy, 'id: 122  x: 0  #milk', g(3, True), g(2)]),
        (line2, [fanboy, g(3, True), g(3)]),
        (line2, [fanboy, 'id: 123  x: 0  #beer', g(3, True), g(2)]),
        (wall, [fanboy, 'id: 122  x: 0  #milk', f'id: {boss_id}  hp: {boss_hp} <boss>',
                g(2, True) + '     <soldier>', g(2) + '  <soldier>']),
    ]


CUSTOM = {
    # 1-1 (2026-11-18, the user): Fortress Gate (wall 1523), grunts 60 HP (LF2's 50 +20%),
    # boss Ironhide (74)
    0: fortress_waves(60, 1100, 1500, 1523, 74, 300),
    # 1-2 (2026-11-19, the user): the same treatment on the Barracks Yard (wall 1365),
    # grunts 63 HP (+25%), boss Urrbot (76) at 375 HP (Ironhide's 300 +25%)
    1: fortress_waves(63, 1000, 1340, 1365, 76, 375),
    # 1-3 (2026-11-19, the user): the same again on the Cell Block (wall 1506), grunts 63 HP
    # (+25%), boss DSS (80) at 375 HP
    2: fortress_waves(63, 1100, 1480, 1506, 80, 375),
}


def layout(text, music_override=None):
    for sid, (key, music, boss) in sorted(LAYOUT.items()):
        music = (music_override or {}).get(sid, music)
        i = text.index(f'<stage> id: {sid} ')
        j = text.index('<stage_end>', i)
        block = text[i:j]
        if sid in CUSTOM:
            head = block.split('<phase>')[0].rstrip() + f'   # DoD: {key}; waves from tools/stage_layout.py CUSTOM'
            NL = '\n'
            phases = [f' bound: {b}{NL}' + ''.join(f'                {e}{NL}' for e in entries) + f'        <phase_end>{NL}{NL}        '
                      for b, entries in CUSTOM[sid]]
            if music:
                phases[0] = phases[0].replace(NL, f'{NL}                music: {music}{NL}', 1)
            text = text[:i] + head + NL + '        <phase>' + '<phase>'.join(phases).rstrip() + NL + text[j:]
            continue
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
