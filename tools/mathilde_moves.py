#!/usr/bin/env python3
"""Write Mathilde's data files: mathilde.txt, m_staff.txt, m_tornado.txt.

    python tools/mathilde_moves.py mods/darthnox/assets

Mathilde (record 63) is a fast jester dancer with a bo staff: very fast, takes
25% more damage (armor 80, match.lua), short recovery and chaining normals.
Her generic mechanics (getting hit, falls, grabs ...) come from Davis (11);
everything here is either her own frame (has bdy/itr, or a name Davis doesn't
use at that number) or a picture-only frame with Davis's exact name.
Edit the tables and re-run; the whole of mathilde.txt is generated.
"""
import os, sys

CX, CY = 44, 85                   # sheet registration (autosprite_to_lf2.py output)
CELL = (89, 89, 20)               # w, h, rows of mathilde.bmp
BODY = (CX - 15, CY - 72, 30, 72)
ABSOLUTE = 550                    # dvy above 500 sets the speed: dvy - 550 (see darthnox_moves.py)

# Sheet pictures (row * 4 + column), see mods/darthnox/README.md
IDLE, WALK, RUN = (0, 1, 2, 3), (4, 5, 6, 7), (8, 9, 10, 11)
SWING, POKE, JUMP = (12, 13, 14), (16, 17, 18), (20, 21)
HURT, FALL, SMASH, BLOCK = (24, 25, 26), (28, 29, 30, 31), (32, 33, 34), (36, 37, 38)
EXTEND, VAULT, THROWING = (40, 41, 42, 43), (44, 45, 46, 47), (48, 49, 50)
TWIRL, DANCE, ROLL, GRAB, THROW = (52, 53, 54, 55), (56, 57, 58, 59), (60, 61, 62, 63), (64, 65, 66, 67), (68, 69, 70)
ICE, BURN = (72, 73), (76, 77, 78)

SWISH = 'data\\008.wav'           # weapon swing
WHOOSH = 'data\\045.wav'          # big swish (extension stab)
FLUTE = 'data\\056.wav'           # Henry's flute start (tornado)
CLONE = 'data\\062.wav'           # Rudolf's clone

MOVEMENT = [                      # very fast: walk/run above everyone in the main cast
    ('walking_frame_rate', 3), ('walking_speed', 7.0), ('walking_speedz', 3.2),
    ('running_frame_rate', 3), ('running_speed', 13.5), ('running_speedz', 2.3),
    ('heavy_walking_speed', 5.0), ('heavy_walking_speedz', 2.4),
    ('heavy_running_speed', 8.5), ('heavy_running_speedz', 1.6),
    ('jump_height', -16.3), ('jump_distance', 11.5), ('jump_distancez', 4.0),
    ('dash_height', -10.0), ('dash_distance', 21.0), ('dash_distancez', 5.0),
    ('rowing_height', -2.0), ('rowing_distance', 5.0),
]

# Inputs on standing (0-3), walking (5-8) and defend (110):
#   D>A staff extension (J during it: vault), D^A homing staff, D^J tornado, DvJ clone.
HITS = dict(Fa=235, Ua=245, Da=0, Fj=0, Uj=250, Dj=260, ja=0)

STAFF_DAMAGE = 35                 # homing staff copy (John's disc does 55)
STAFF_DRAIN = 6                   # its hp lost per frame: ~2.5 s of chasing
TORNADO_TICKS = 30                # ~1 s of lift (Henry's flute holds ~3 s)
VAULT_LAUNCH = 15                 # absolute launch speed: ~90 px, over a standing fighter


def itr(x, y, w, h, dvx=0, dvy=0, fall=0, vrest=0, arest=0, bdefend=0, injury=0, effect=0, kind=0):
    return (f'   itr:\n      kind: {kind}  x: {x}  y: {y}  w: {w}  h: {h}  dvx: {dvx}  dvy: {dvy}  fall: {fall}'
            f'  vrest: {vrest}  arest: {arest}  bdefend: {bdefend}  injury: {injury}  effect: {effect}\n   itr_end:\n')


def bdy(x, y, w, h):
    return f'   bdy:\n      kind: 0  x: {x}  y: {y}  w: {w}  h: {h}\n   bdy_end:\n'


def opoint(oid, x, y, action=0, facing=0):
    return f'   opoint:\n      kind: 1  x: {x}  y: {y}  action: {action}  dvx: 0  dvy: 0  oid: {oid}  facing: {facing}\n   opoint_end:\n'


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
    """Picture-only frame: Davis's mechanics, our picture (name must be Davis's)."""
    return frame(n, name, picture, 0, 0, 0, body=False, hits=hits)


def staff(reach=54, **kw):        # staff hitbox in front of the chest
    kw.setdefault('effect', 0)
    return itr(CX + 2, CY - 56, reach, 26, **kw)


PICK_UP = itr(CX - 19, CY - 22, 37, 24, vrest=1, kind=2)

FRAMES = [
    '# Standing, walking, running (inputs live on standing, walking and defend)',
    *[pic(n, 'standing', IDLE[n], HITS) for n in range(4)],
    *[pic(5 + i, 'walking', WALK[i], HITS) for i in range(4)],
    pic(9, 'running', RUN[0]), pic(10, 'running', RUN[1]), pic(11, 'running', RUN[2]),
    pic(12, 'heavy_obj_walk', WALK[0]), pic(13, 'heavy_obj_walk', WALK[1]), pic(14, 'heavy_obj_walk', WALK[2]),
    pic(15, 'heavy_obj_walk', WALK[3]), pic(16, 'heavy_obj_run', RUN[0]), pic(17, 'heavy_obj_run', RUN[1]),
    pic(18, 'heavy_obj_run', RUN[2]), pic(19, 'heavy_stop_run', JUMP[0]),

    '# Holding an item: the staff swing / poke / smash / extension poses',
    *[pic(n, 'normal_weapon_atck', p) for n, p in zip((20, 21, 22, 23, 25, 26, 27, 28), SWING + (14,) + POKE + (18,))],
    *[pic(n, 'jump_weapon_atck', p) for n, p in zip((30, 31, 32, 33), SMASH + (34,))],
    *[pic(n, 'run_weapon_atck', p) for n, p in zip((35, 36, 37), EXTEND[:3])],
    *[pic(n, 'dash_weapon_atck', p) for n, p in zip((40, 41, 42, 43), SMASH + (34,))],
    *[pic(n, name, p) for n, name, p in ((45, 'light_weapon_thw', THROW[0]), (46, 'light_weapon_thw', THROW[1]),
                                         (47, 'light_weapon_thw', THROW[2]), (50, 'heavy_weapon_thw', THROW[0]),
                                         (51, 'heavy_weapon_thw', THROW[1]), (52, 'sky_lgt_wp_thw', THROW[0]),
                                         (53, 'sky_lgt_wp_thw', THROW[1]), (54, 'sky_lgt_wp_thw', THROW[2]))],

    '# A, A, A: swing -> poke -> overhead smash. Short frames, and hit_a chains each\n'
    '# into the next for combos; 22 per hit, the smash 40 and a knockdown.',
    frame(60, 'punch', SWING[0], 3, 1, 61, extra=PICK_UP),
    frame(61, 'punch', SWING[1], 3, 1, 62, sound=SWISH, extra=staff(54, dvx=2, fall=20, vrest=8, bdefend=25, injury=22)),
    frame(62, 'punch', SWING[2], 3, 1, 999, hits={'a': 65}),
    frame(65, 'punch', POKE[0], 3, 1, 66, extra=PICK_UP),
    frame(66, 'punch', POKE[1], 3, 1, 67, sound=SWISH, extra=staff(62, dvx=2, fall=20, vrest=8, bdefend=25, injury=22)),
    frame(67, 'punch', POKE[2], 3, 1, 999, hits={'a': 70}),
    frame(70, 'super_punch', SMASH[0], 3, 2, 71),
    frame(71, 'super_punch', SMASH[1], 3, 1, 72, dvx=3, sound=SWISH,
          extra=itr(CX - 6, CY - 82, 74, 82, dvx=8, fall=70, vrest=15, bdefend=60, injury=40)),
    frame(72, 'super_punch', SMASH[2], 3, 3, 73),
    frame(73, 'super_punch', SMASH[2], 3, 2, 999),
    '# Jump attack: the overhead smash in the air; run attack: a running extension poke',
    frame(80, 'jump_attack', SMASH[0], 3, 1, 81, sound=SWISH),
    frame(81, 'jump_attack', SMASH[1], 3, 1, 82, extra=itr(CX - 8, CY - 80, 74, 80, dvx=7, dvy=7, fall=70, arest=15, bdefend=60, injury=40)),
    frame(82, 'jump_attack', SMASH[2], 3, 9, 999),
    frame(85, 'run_attack', EXTEND[0], 3, 3, 86, dvx=6),
    frame(86, 'run_attack', EXTEND[1], 3, 2, 87, dvx=4, sound=WHOOSH, extra=staff(96, dvx=8, dvy=-3, fall=70, vrest=15, bdefend=60, injury=38)),
    frame(87, 'run_attack', EXTEND[2], 3, 3, 88),
    frame(88, 'run_attack', EXTEND[3], 3, 3, 999),
    *[pic(n, 'dash_attack', p) for n, p in zip((90, 91, 92, 93, 94), SMASH + (34, 34))],

    '# Roll (run + D): invulnerable (no bdy), picks up items',
    frame(100, 'rowing', ROLL[1], 6, 2, 101, body=False),
    frame(101, 'rowing', ROLL[2], 6, 6, 0, body=False),
    *[frame(n, 'rowing', p, 6, 2, nxt, dvx=10, body=False, extra=itr(CX - 3, CY - 25, 13, 25, vrest=1, kind=7))
      for n, p, nxt in ((102, ROLL[0], 103), (103, ROLL[1], 104), (104, ROLL[2], 105), (105, ROLL[3], 219),
                        (106, ROLL[1], 219), (107, ROLL[3], 219))],
    frame(108, 'rowing', ROLL[1], 6, 3, 109, body=False),
    frame(109, 'rowing', ROLL[3], 6, 6, 0, body=False),

    '# Block, broken block, picking up',
    pic(110, 'defend', BLOCK[1], HITS), pic(111, 'defend', BLOCK[1]), pic(95, 'dash_defend', BLOCK[1]),
    pic(112, 'broken_defend', BLOCK[0]), pic(113, 'broken_defend', BLOCK[2]), pic(114, 'broken_defend', BLOCK[0]),
    pic(115, 'picking_light', JUMP[0]), pic(116, 'picking_heavy', JUMP[0]), pic(117, 'picking_heavy', JUMP[0]),

    '# Grab and staff jab (A while holding), throws, being held',
    *[pic(120 + i, 'catching', GRAB[i]) for i in range(4)],
    *[pic(232 + i, 'throw_lying_man', THROW[i]) for i in range(3)],
    *[pic(n, 'picked_caught', p) for n, p in zip(range(130, 145), HURT + (28, 29, 30, 30, 31, 29, 28, 29, 30, 30, 31, 29))],

    '# Hit, knocked down, lying, frozen, burning',
    *[pic(n, 'falling', p) for base in (180, 186) for n, p in zip(range(base, base + 6), FALL[:3] + (FALL[2], FALL[3], JUMP[0]))],
    pic(200, 'ice', ICE[0]), pic(201, 'ice', ICE[1]), pic(202, 'ice', ICE[0]),
    *[pic(203 + i, 'fire', p) for i, p in enumerate(BURN + (BURN[1],))],
    pic(207, 'tired', HURT[2]),
    *[pic(n, 'injured', p) for n, p in zip(range(220, 230), (24, 25, 25, 24, 24, 25, 24, 26, 25, 26))],
    pic(230, 'lying', FALL[3]), pic(231, 'lying', FALL[3]),

    '# Jump, dash, crouch',
    pic(210, 'jump', JUMP[0]), pic(211, 'jump', JUMP[1]), pic(212, 'jump', JUMP[1]),
    pic(213, 'dash', JUMP[1]), pic(214, 'dash', JUMP[1]), pic(216, 'dash', JUMP[1]), pic(217, 'dash', JUMP[1]),
    pic(215, 'crouch', JUMP[0]), pic(218, 'stop_running', JUMP[0]), pic(219, 'crouch2', JUMP[0]),

    '# D>A  Staff extension: she slides to the end of the staff and stabs at full\n'
    '# length (~110 px reach). Press J during it to vault over the staff (240).',
    frame(235, 'staff_ext', EXTEND[0], 3, 1, 236, mp=50),
    frame(236, 'staff_ext', EXTEND[1], 3, 1, 237, dvx=8, sound=WHOOSH, hits={'j': 240},
          extra=staff(110, dvx=6, fall=40, vrest=15, bdefend=30, injury=32)),
    frame(237, 'staff_ext', EXTEND[2], 3, 3, 238, hits={'j': 240}, extra=staff(110, dvx=6, fall=40, vrest=15, bdefend=30, injury=32)),
    frame(238, 'staff_ext', EXTEND[3], 3, 3, 999, hits={'j': 240}),

    '# Vault (J during the extension): plant, launch over the staff (invulnerable,\n'
    '# absolute dvy so hit lag can\'t stack it), a landing kick, then a plain fall.',
    frame(240, 'vault', VAULT[0], 3, 1, 241, dvx=4, body=False),
    frame(241, 'vault', VAULT[1], 3, 1, 242, dvx=10, dvy=ABSOLUTE - VAULT_LAUNCH, body=False),
    frame(242, 'vault', VAULT[2], 3, 3, 243, body=False),
    frame(243, 'vault', VAULT[3], 3, 3, 244, extra=itr(CX - 10, CY - 62, 62, 62, dvx=6, fall=70, vrest=15, bdefend=30, injury=25)),
    frame(244, 'vault', VAULT[3], 3, 4, 999),

    '# D^A  Homing staff: a throwing motion that sends a spinning copy of the staff\n'
    '# (m_staff.txt, object 64) after the nearest enemy, like John\'s disc.',
    frame(245, 'staff_throw', THROWING[0], 3, 2, 246, mp=75),
    frame(246, 'staff_throw', THROWING[1], 3, 1, 247, sound=SWISH, extra=opoint(64, CX + 28, CY - 48)),
    frame(247, 'staff_throw', THROWING[2], 3, 4, 248),
    frame(248, 'staff_throw', THROWING[2], 3, 1, 999),

    f'# D^J  Tornado: she twirls inside a magic tornado (m_tornado.txt, object 65, a\n'
    f'# visual) while whirlwind itrs (kind 10/11, Henry\'s flute) lift and hold anyone\n'
    f'# around her for ~{TORNADO_TICKS} ticks (1 s); then they drop.',
    frame(250, 'tornado', TWIRL[0], 3, 1, 251, mp=200),
    frame(251, 'tornado', TWIRL[1], 3, 1, 252, sound=FLUTE, extra=opoint(65, CX, CY - 65)),
] + [frame(252 + i, 'tornado', TWIRL[i % 4], 3, TORNADO_TICKS // 6 - 1, 253 + i if i < 5 else 258,
           extra=itr(CX - 75, CY - 150, 150, 220, vrest=1, injury=1, kind=10)
           + itr(CX - 130, CY - 140, 260, 210, vrest=1, injury=1, kind=10)
           + itr(CX - 165, CY - 120, 330, 190, vrest=1, injury=1, kind=11))
     for i in range(6)] + [
    frame(258, 'tornado', TWIRL[2], 3, 3, 999),

    '# DvJ  Clone: a dance spin, then a copy of herself (object 63) appears behind\n'
    '# her, AI-controlled like Rudolf\'s clones; objects.lua gives it 15 HP (Rudolf\'s\n'
    '# have 10).',
    frame(260, 'clone', DANCE[0], 3, 2, 261, mp=300),
    *[frame(261 + i, 'clone', DANCE[(i + 1) % 4], 3, 2, 262 + i) for i in range(4)],
    frame(265, 'clone', DANCE[1], 3, 1, 266, sound=CLONE, extra=opoint(63, CX - 30, CY)),
    frame(266, 'clone', DANCE[3], 3, 3, 999),
]


def header():
    w, h, rows = CELL
    lines = ['<bmp_begin>', 'name: Mathilde', 'head: mods/darthnox/mathilde_f.bmp', 'small: mods/darthnox/mathilde_s.bmp',
             f'file(0-{rows * 4 - 1}): mods/darthnox/mathilde.bmp', f'w: {w}  h: {h}  row: 4  col: {rows}']
    lines += [f'{k} {v:.6f}' if isinstance(v, float) else f'{k} {v}' for k, v in MOVEMENT]
    lines += ['<bmp_end>', '',
              '# Art: AutoSprite character "Mathilde LF2" (cmweo6j3b0098no9evut0e4hc), every clip',
              '# from her "Idle Lock" pose, converted with tools/autosprite_to_lf2.py at s0.345992.',
              '# Generated by tools/mathilde_moves.py: edit that, not this file.', '']
    return '\n'.join(lines)


def ball(name, pic_file, cell, center, frames):
    w, h = cell
    return '\n'.join([f'<bmp_begin>', f'file(0-7): {pic_file}  w: {w}  h: {h}  row: 4  col: 2',
                      'weapon_hit_sound: data\\020.wav', 'weapon_drop_sound: data\\020.wav',
                      'weapon_broken_sound: data\\020.wav', '<bmp_end>', '', f'# {name}', ''] + frames)


def ball_frame(n, name, picture, state, nxt, center, dvx=0, hits='hit_a: 0  hit_d: 0  hit_j: 0', extra=''):
    return (f'<frame> {n} {name}\n   pic: {picture}  state: {state}  wait: 1  next: {nxt}  dvx: {dvx}  dvy: 0'
            f'  centerx: {center[0]}  centery: {center[1]}  {hits}\n{extra}<frame_end>\n')


def staff_ball():
    c, box = (32, 32), (4, 18, 56, 28)
    fly = [ball_frame(n, 'flying', n, 3000, n + 1 if n < 3 else 999, c, dvx=11,
                      hits=f'hit_a: {STAFF_DRAIN}  hit_d: 40  hit_j: 0  hit_Fa: 1',
                      extra=itr(*box, dvx=9, fall=70, vrest=10, bdefend=16, injury=STAFF_DAMAGE) + bdy(*box)) for n in range(4)]
    ends = [ball_frame(base + i, name, 4 + i if base < 40 else 5 + i, st,
                       1000 if (i == 3 if base < 40 else i == 2) else base + i + 1, c)
            for base, name, st in ((10, 'hiting', 3001), (20, 'hit', 3002), (30, 'rebounding', 3003), (40, 'disappearing', 3004))
            for i in range(4 if base < 40 else 3)]
    return ball('Mathilde\'s homing staff: hit_Fa 1 = chase the nearest enemy.', 'mods/darthnox/m_staff.bmp', (64, 64), c, fly + ends)


def tornado_ball():
    c = (75, 65)
    spin = [ball_frame(n, 'tornado', n % 4, 3000, n + 1, c) for n in range(16)]
    fade = [ball_frame(16 + i, 'tornado_fade', 4 + i, 3000, 17 + i if i < 3 else 1000, c) for i in range(4)]
    return ball('The tornado around Mathilde\'s D^J: visual only (the lift is on her frames).',
                'mods/darthnox/m_tornado.bmp', (150, 130), c, spin + fade)


def main(assets):
    with open(os.path.join(assets, 'mathilde.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(header() + '\n' + '\n'.join(FRAMES))
    with open(os.path.join(assets, 'm_staff.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(staff_ball())
    with open(os.path.join(assets, 'm_tornado.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(tornado_ball())
    print('wrote mathilde.txt, m_staff.txt, m_tornado.txt')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
