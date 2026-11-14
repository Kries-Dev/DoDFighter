#!/usr/bin/env python3
"""Write Cod1eh's data file: cod1eh.txt.

    python tools/cod1eh_moves.py mods/darthnox/assets

Cod1eh (record 68) is a ninja: long sleeves, mask, a hidden blade on his right
forearm. His generic mechanics come from Rudolf (5), whose A already throws
shurikens (object 202, 15 MP a throw), so his basic attack is Rudolf's,
drawn as his own sidearm and overhand throws. The blade does the close work:
jump attack, running lunge, dash stab and the combo on a dizzy target.

Template stage: no special moves yet. object_data.lua (own_inputs) makes his
standing/walking/defend frames replace Rudolf's inputs, so Rudolf's transform,
vanish and clone can't be reached. Add specials to HITS and FRAMES.

Everything here is either his own frame (has bdy/itr, or a name Rudolf doesn't
use at that number) or a picture-only frame with Rudolf's exact name.
Edit the tables and re-run; the whole of cod1eh.txt is generated.
"""
import os, sys

CX, CY = 64, 86                   # sheet registration (autosprite_to_lf2.py output)
CELL = (118, 87, 18)              # w, h, rows of cod1eh.bmp
BODY = (CX - 15, CY - 72, 30, 72)

# Sheet pictures (row * 4 + column); rebuild command in mods/darthnox/README.md
IDLE, WALK, RUN = (0, 1, 2, 3), (4, 5, 6, 7), (8, 9, 10, 11)
THROW, THROW2, JUMP = (12, 13, 14, 15), (16, 17, 18, 19), (20, 21, 22)
SLASH, THRUST, DASH = (24, 25, 26), (28, 29, 30), (32, 33, 34)   # DASH: the thrust with afterimages
COMBO_PICS, HURT, FALL = (36, 37, 38, 39), (40, 41, 42), (44, 45, 46, 47)
BLOCK, ROLL, GRAB, TOSS = (48, 49, 50), (52, 53, 54, 55), (56, 57, 58, 59), (60, 61, 62)
ICE, BURN = (64, 65), (68, 69, 70)

SWISH = 'data\\008.wav'           # weapon swing (object_data.lua also swaps Rudolf's punch sounds for it)

MOVEMENT = [                      # agile: Rudolf's speed, a little more jump and dash
    ('walking_frame_rate', 3), ('walking_speed', 6.0), ('walking_speedz', 2.8),
    ('running_frame_rate', 3), ('running_speed', 12.5), ('running_speedz', 2.0),
    ('heavy_walking_speed', 4.2), ('heavy_walking_speedz', 2.0),
    ('heavy_running_speed', 7.0), ('heavy_running_speedz', 1.2),
    ('jump_height', -17.0), ('jump_distance', 11.0), ('jump_distancez', 3.75),
    ('dash_height', -10.0), ('dash_distance', 20.0), ('dash_distancez', 5.0),
    ('rowing_height', -2.0), ('rowing_distance', 5.0),
]

# Inputs on standing (0-3), walking (5-8) and defend (110). All 0 until his
# special moves are designed (D>A = Fa, D^A = Ua, DvA = Da, D>J = Fj, ...).
HITS = dict(Fa=0, Ua=0, Da=0, Fj=0, Uj=0, Dj=0, ja=0)


def itr(x, y, w, h, dvx=0, dvy=0, fall=0, vrest=0, arest=0, bdefend=0, injury=0, effect=0, kind=0):
    return (f'   itr:\n      kind: {kind}  x: {x}  y: {y}  w: {w}  h: {h}  dvx: {dvx}  dvy: {dvy}  fall: {fall}'
            f'  vrest: {vrest}  arest: {arest}  bdefend: {bdefend}  injury: {injury}  effect: {effect}\n   itr_end:\n')


def bdy(x, y, w, h):
    return f'   bdy:\n      kind: 0  x: {x}  y: {y}  w: {w}  h: {h}\n   bdy_end:\n'


def frame(n, name, pic, state, wait, nxt, dvx=0, dvy=0, mp=0, body=True, extra='', hits=None, sound=None):
    head = f'   pic: {pic}  state: {state}  wait: {wait}  next: {nxt}  dvx: {dvx}  dvy: {dvy}  dvz: 0  centerx: {CX}  centery: {CY}'
    if mp:
        head += f'  mp: {mp}'
    if sound:
        head += f'  sound: {sound}'
    if hits:
        head += '  ' + '  '.join(f'hit_{k}: {v}' for k, v in hits.items())
    return f'<frame> {n} {name}\n{head}\n{extra}{bdy(*BODY) if body else ""}<frame_end>\n'


def pic(n, name, picture, hits=None):
    """Picture-only frame: Rudolf's mechanics, our picture (name must be Rudolf's)."""
    return frame(n, name, picture, 0, 0, 0, body=False, hits=hits)


def blade(reach=50, y=58, h=28, **kw):   # hidden-blade hitbox in front of the chest
    return itr(CX + 4, CY - y, reach, h, **kw)


FRAMES = [
    '# Standing, walking, running (inputs live on standing, walking and defend)',
    *[pic(n, 'standing', IDLE[n], HITS) for n in range(4)],
    *[pic(5 + i, 'walking', WALK[i], HITS) for i in range(4)],
    pic(9, 'running', RUN[0]), pic(10, 'running', RUN[1]), pic(11, 'running', RUN[2]),
    *[pic(12 + i, 'heavy_obj_walk', WALK[i]) for i in range(4)],
    pic(16, 'heavy_obj_run', RUN[0]), pic(17, 'heavy_obj_run', RUN[1]), pic(18, 'heavy_obj_run', RUN[2]),
    pic(19, 'heavy_stop_run', JUMP[0]),

    '# Holding an item: his blade poses',
    *[pic(n, 'normal_weapon_atck', p) for n, p in zip((20, 21, 22, 23, 25, 26, 27, 28), SLASH + (SLASH[2],) + THRUST + (THRUST[2],))],
    *[pic(n, 'jump_weapon_atck', p) for n, p in zip((30, 31, 32, 33), SLASH + (SLASH[2],))],
    *[pic(n, 'run_weapon_atck', p) for n, p in zip((35, 36, 37), THRUST)],
    *[pic(n, 'dash_weapon_atck', p) for n, p in zip((40, 41, 42, 43), SLASH + (SLASH[2],))],
    *[pic(n, name, p) for n, name, p in ((45, 'light_weapon_thw', THROW2[0]), (46, 'light_weapon_thw', THROW2[1]),
                                         (47, 'light_weapon_thw', THROW2[2]), (50, 'heavy_weapon_thw', TOSS[0]),
                                         (51, 'heavy_weapon_thw', TOSS[1]), (52, 'sky_lgt_wp_thw', THROW2[0]),
                                         (53, 'sky_lgt_wp_thw', THROW2[1]), (54, 'sky_lgt_wp_thw', THROW2[2]))],
    *[pic(n, 'weapon_drink', p) for n, p in zip((55, 56, 57, 58), IDLE)],

    '# A: shurikens. Rudolf\'s throw (15 MP each, object 202 spawned on 62 / 66 / 69),\n'
    '# drawn as a sidearm throw, then an overhand one.',
    pic(59, 'punch', THROW[3]),
    pic(60, 'punch', THROW[0]), pic(61, 'punch', THROW[1]), pic(62, 'punch', THROW[2]), pic(63, 'punch', THROW[3]),
    pic(64, 'punch', THROW2[0]), pic(65, 'punch', THROW[0]), pic(66, 'punch', THROW2[2]), pic(67, 'punch', THROW2[3]),
    pic(68, 'punch', THROW2[1]), pic(69, 'punch', THROW2[2]),

    '# A on a dizzy target: hidden-blade combo, two stabs and a rising slash',
    frame(70, 'super_punch', COMBO_PICS[0], 3, 1, 71),
    frame(71, 'super_punch', COMBO_PICS[1], 3, 2, 72, dvx=2, sound=SWISH,
          extra=blade(52, dvx=2, fall=1, vrest=6, bdefend=16, injury=15)),
    frame(72, 'super_punch', COMBO_PICS[0], 3, 1, 73),
    frame(73, 'super_punch', COMBO_PICS[1], 3, 2, 74, dvx=2, sound=SWISH,
          extra=blade(52, dvx=2, fall=1, vrest=6, bdefend=16, injury=15)),
    frame(74, 'super_punch', COMBO_PICS[2], 3, 1, 75),
    frame(75, 'super_punch', COMBO_PICS[3], 3, 2, 76, dvx=3, sound=SWISH,
          extra=blade(56, y=80, h=70, dvx=4, dvy=-8, fall=70, vrest=15, bdefend=60, injury=55)),
    frame(76, 'super_punch', COMBO_PICS[3], 3, 6, 999),

    '# Jump attack: a downward slash with the blade; run attack: a lunging stab;\n'
    '# dash attack: the same stab with afterimages, harder.',
    frame(80, 'jump_attack', SLASH[0], 3, 1, 81, sound=SWISH),
    frame(81, 'jump_attack', SLASH[1], 3, 2, 82,
          extra=itr(CX - 4, CY - 64, 64, 84, dvx=7, dvy=5, fall=70, arest=15, bdefend=60, injury=35)),
    frame(82, 'jump_attack', SLASH[2], 3, 9, 999),
    frame(85, 'run_attack', THRUST[0], 3, 2, 86, dvx=6),
    frame(86, 'run_attack', THRUST[1], 3, 2, 87, dvx=8, sound=SWISH,
          extra=blade(62, dvx=8, dvy=-3, fall=70, vrest=15, bdefend=60, injury=45)),
    frame(87, 'run_attack', THRUST[2], 3, 3, 88),
    frame(88, 'run_attack', THRUST[2], 3, 4, 999),
    frame(90, 'dash_attack', DASH[0], 3, 1, 91),
    frame(91, 'dash_attack', DASH[1], 3, 1, 92, sound=SWISH),
    frame(92, 'dash_attack', DASH[1], 3, 2, 93,
          extra=blade(64, y=64, h=50, dvx=10, dvy=-3, fall=70, arest=15, bdefend=60, injury=60)),
    frame(93, 'dash_attack', DASH[2], 3, 2, 94),
    frame(94, 'dash_attack', THRUST[2], 3, 6, 999),

    '# Roll (run + D): invulnerable (no bdy), picks up items',
    frame(100, 'rowing', ROLL[1], 6, 2, 101, body=False),
    frame(101, 'rowing', ROLL[2], 6, 6, 0, body=False),
    *[frame(n, 'rowing', p, 6, 2, nxt, dvx=10, body=False, extra=itr(CX - 3, CY - 25, 13, 25, vrest=1, kind=7))
      for n, p, nxt in ((102, ROLL[0], 103), (103, ROLL[1], 104), (104, ROLL[2], 105), (105, ROLL[3], 219),
                        (106, ROLL[1], 219), (107, ROLL[3], 219))],
    frame(108, 'rowing', ROLL[1], 6, 3, 109, body=False),
    frame(109, 'rowing', ROLL[3], 6, 6, 0, body=False),

    '# Block, broken block, picking up',
    pic(110, 'defend', BLOCK[1], HITS), pic(111, 'defend', BLOCK[2], HITS), pic(95, 'dash_defend', BLOCK[1]),
    pic(112, 'broken_defend', BLOCK[0]), pic(113, 'broken_defend', HURT[1]), pic(114, 'broken_defend', BLOCK[0]),
    pic(115, 'picking_light', JUMP[0]), pic(116, 'picking_heavy', JUMP[0]), pic(117, 'picking_heavy', JUMP[0]),

    '# Grab and jab (A while holding), throws, being held',
    *[pic(120 + i, 'catching', GRAB[i]) for i in range(4)],
    *[pic(232 + i, 'throw_lying_man', TOSS[i]) for i in range(3)],
    *[pic(n, 'picked_caught', p) for n, p in zip(range(130, 145), HURT + (44, 45, 46, 46, 47, 45, 44, 45, 46, 46, 47, 45))],

    '# Hit, knocked down, lying, frozen, burning',
    *[pic(n, 'falling', p) for base in (180, 186) for n, p in zip(range(base, base + 6), FALL[:3] + (FALL[2], FALL[3], JUMP[0]))],
    pic(200, 'ice', ICE[0]), pic(201, 'ice', ICE[1]), pic(202, 'ice', ICE[0]),
    *[pic(203 + i, 'fire', p) for i, p in enumerate(BURN + (BURN[1],))],
    pic(207, 'tired', HURT[2]),
    *[pic(n, 'injured', p) for n, p in zip(range(220, 230), (40, 41, 41, 40, 40, 41, 40, 42, 41, 42))],
    pic(230, 'lying', FALL[3]), pic(231, 'lying', FALL[3]),

    '# Jump, dash, crouch',
    pic(210, 'jump', JUMP[0]), pic(211, 'jump', JUMP[1]), pic(212, 'jump', JUMP[2]),
    pic(213, 'dash', JUMP[2]), pic(214, 'dash', JUMP[2]), pic(216, 'dash', JUMP[2]), pic(217, 'dash', JUMP[2]),
    pic(215, 'crouch', JUMP[0]), pic(218, 'stop_running', JUMP[0]), pic(219, 'crouch2', JUMP[0]),
]


def header():
    w, h, rows = CELL
    lines = ['<bmp_begin>', 'name: Cod1eh', 'head: mods/darthnox/cod1eh_f.bmp', 'small: mods/darthnox/cod1eh_s.bmp',
             f'file(0-{rows * 4 - 1}): mods/darthnox/cod1eh.bmp', f'w: {w}  h: {h}  row: 4  col: {rows}']
    lines += [f'{k} {v:.6f}' if isinstance(v, float) else f'{k} {v}' for k, v in MOVEMENT]
    lines += ['<bmp_end>', '',
              '# Art: AutoSprite character "Cod1eh" (cmwghibin0036mf37uswhkfd3), every clip',
              '# from his "Idle Lock" pose, converted with tools/autosprite_to_lf2.py at s0.351931.',
              '# Generated by tools/cod1eh_moves.py: edit that, not this file.', '']
    return '\n'.join(lines)


def main(assets):
    with open(os.path.join(assets, 'cod1eh.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(header() + '\n' + '\n'.join(FRAMES))
    print('wrote cod1eh.txt')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
