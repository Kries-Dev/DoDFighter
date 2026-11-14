#!/usr/bin/env python3
"""Write Cod1eh's data file: cod1eh.txt.

    python tools/cod1eh_moves.py mods/darthnox/assets

Cod1eh (record 68) is a ninja: long sleeves, mask, a hidden blade on his right
forearm. His generic mechanics come from Rudolf (5), whose A already throws
shurikens (object 202, 15 MP a throw), so his basic attack is Rudolf's,
drawn as his own sidearm and overhand throws. The blade does the close work:
jump attack, running lunge, dash stab and the combo on a dizzy target.

Specials (2026-11-14): D>A kunai fan, D^J smoke bomb (back flip; the smoke
slows enemies, physics.lua), DvA rope blade (pulls the target to him, combat.lua +
physics.lua), DvJ teleport stab (behind the nearest enemy, physics.lua), DJA
Izuna drop (command grab). object_data.lua (own_inputs) makes his
standing/walking/defend frames replace Rudolf's inputs entirely, so Rudolf's
transform, vanish and clone can't be reached. His roll goes further and stays
invulnerable a little longer than the stock roll.
Also writes his objects: c_kunai.txt (69), c_smoke.txt (70), c_rope.txt (71).

Everything here is either his own frame (has bdy/itr, or a name Rudolf doesn't
use at that number) or a picture-only frame with Rudolf's exact name.
Edit the tables and re-run; the whole of cod1eh.txt is generated.
"""
import os, sys

ABSOLUTE = 550                    # dvy above 500 sets the speed: dvy - 550 (see darthnox_moves.py)

CX, CY = 72, 86                   # sheet registration (autosprite_to_lf2.py output)
CELL = (117, 90, 23)              # w, h, rows of cod1eh.bmp
BODY = (CX - 15, CY - 72, 30, 72)

# Sheet pictures (row * 4 + column); rebuild command in mods/darthnox/README.md
IDLE, WALK, RUN = (0, 1, 2, 3), (4, 5, 6, 7), (8, 9, 10, 11)
THROW, THROW2, JUMP = (12, 13, 14, 15), (16, 17, 18, 19), (20, 21, 22)
SLASH, THRUST, DASH = (24, 25, 26), (28, 29, 30), (32, 33, 34)   # DASH: the thrust with afterimages
RISE, HURT, FALL = 36, (40, 41, 42), (44, 45, 46, 47)                 # RISE: rising bracer stab
COMBO_PICS = (THRUST[0], THRUST[1], THRUST[2], RISE)   # blade combo: the bracer stab twice, then the rise
BLOCK, ROLL, GRAB, TOSS = (48, 49, 50), (52, 53, 54, 55), (56, 57, 58, 59), (60, 61, 62)
ICE, BURN = (64, 65), (68, 69, 70)
FAN, FLIP, SEAL = (72, 73, 74), (76, 77, 78, 79), (80, 81, 82)   # kunai fan, back flip, hand seal
ROPE, DIVE = (84, 85, 86), (88, 89, 90, 91)        # rope throw (arm back, punch out, hold), Izuna head-first dive
BLANK = 23                                         # an empty cell: vanished (teleport)

KUNAI, SMOKE, ROPE_OBJ = 69, 70, 71               # his objects (catalog.lua)
PUFF = 30                                         # smoke object action: a short puff that doesn't slow
KUNAI_SND = 'data\\008.wav'
SMOKE_SND = 'data\\061.wav'     # Rudolf's vanish puff
ROPE_SND = 'data\\008.wav'      # a swish as the rope shoots out (045 sounded like Deep)
SLAM_SND = 'data\\030.wav'      # a heavy landing thud

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

# Inputs on standing (0-3), walking (5-8) and defend (110):
#   D>A kunai fan, D^J smoke bomb, DvA rope blade, DvJ teleport stab, DJA Izuna drop.
HITS = dict(Fa=235, Ua=0, Da=270, Fj=0, Uj=250, Dj=260, ja=280)
FAN_MP, SMOKE_MP, ROPE_MP, TELEPORT_MP, IZUNA_MP = 45, 100, 60, 150, 150
KUNAI_COUNT, KUNAI_DVY = 3, -3    # three kunai tossed slightly up; physics.lua drops them in an arc
FLIP_BACK, FLIP_UP = 10, 11       # smoke bomb: ~19 ticks in the air, ~190 px back
ROPE_REACH = (70, 140, 200, 210)  # DvA hitbox length per frame (the rope sprite matches)



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


def cpoint(x, y, vaction, injury=0, throwvx=0, throwvy=0, throwinjury=0, cover=10):
    return (f'   cpoint:\n      kind: 1  x: {x}  y: {y}  injury: {injury}  vaction: {vaction}  aaction: 0  jaction: 0'
            f'  taction: 0  throwvx: {throwvx}  throwvy: {throwvy}  throwvz: 0  hurtable: 0  throwinjury: {throwinjury}'
            f'  decrease: 0  dircontrol: 0  cover: {cover}\n   cpoint_end:\n')


def opoint(oid, x, y, action=0, dvx=0, facing=0, dvy=0):
    return f'   opoint:\n      kind: 1  x: {x}  y: {y}  action: {action}  dvx: {dvx}  dvy: {dvy}  oid: {oid}  facing: {facing}\n   opoint_end:\n'


def catch(x, y, w, h, catching, caught):
    return (f'   itr:\n      kind: 3  x: {x}  y: {y}  w: {w}  h: {h}  dvx: 0  dvy: 0  fall: 0  vrest: 7  arest: 0'
            f'  bdefend: 0  injury: 0  effect: 0  catchingact: {catching} {catching}  caughtact: {caught} {caught}\n   itr_end:\n')


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

    '# Roll (run + D): invulnerable (no bdy), picks up items. Further than the stock\n'
    '# roll (dvx 11, one more frame: ~165 px) and that frame is invulnerable too.',
    frame(100, 'rowing', ROLL[1], 6, 2, 101, body=False),
    frame(101, 'rowing', ROLL[2], 6, 6, 0, body=False),
    *[frame(n, 'rowing', p, 6, 2, nxt, dvx=11, body=False, extra=itr(CX - 3, CY - 25, 13, 25, vrest=1, kind=7))
      for n, p, nxt in ((102, ROLL[0], 103), (103, ROLL[1], 104), (104, ROLL[2], 105), (105, ROLL[3], 106),
                        (106, ROLL[0], 219), (107, ROLL[3], 219))],
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

    '# D>A  Kunai fan: arms crossed, then flung wide; three kunai (c_kunai.txt) fanned\n'
    '# out in depth (opoint facing 30 = three objects spread -5, 0, +5 in z), tossed\n'
    '# slightly up and falling in an arc like Rudolf\'s stars (gravity in physics.lua).',
    frame(235, 'kunai_fan', FAN[0], 3, 2, 236, mp=FAN_MP),
    frame(236, 'kunai_fan', FAN[1], 3, 1, 237),
    frame(237, 'kunai_fan', FAN[2], 3, 1, 238, sound=KUNAI_SND, extra=opoint(KUNAI, CX + 24, CY - 50, facing=KUNAI_COUNT * 10, dvy=KUNAI_DVY)),
    frame(238, 'kunai_fan', FAN[2], 3, 6, 999),

    '# D^J  Smoke bomb: he slams a smoke bomb at his feet (c_smoke.txt: a cloud that\n'
    '# lingers ~3 s and slows enemies inside it, physics.lua) and back-flips away.\n'
    '# Invulnerable for the first ticks of the flip.',
    frame(250, 'smoke_bomb', FLIP[0], 3, 1, 251, mp=SMOKE_MP),   # (an opoint on a move's first frame doesn't fire)
    frame(251, 'smoke_bomb', FLIP[1], 3, 1, 252, dvx=-FLIP_BACK, dvy=ABSOLUTE - FLIP_UP, body=False, sound=SMOKE_SND,
          extra=opoint(SMOKE, CX, CY)),
    frame(252, 'smoke_bomb', FLIP[1], 3, 3, 253, dvx=-FLIP_BACK, body=False),
    frame(253, 'smoke_bomb', FLIP[2], 3, 4, 254, dvx=-FLIP_BACK),
    frame(254, 'smoke_bomb', FLIP[3], 3, 30, 999, dvx=-FLIP_BACK),

    '# DvJ  Teleport stab: a hand seal, he vanishes in a puff, reappears behind the\n'
    '# nearest enemy (physics.lua moves him on entering 264) and stabs them in the back.',
    frame(260, 'teleport', SEAL[0], 3, 2, 261, mp=TELEPORT_MP),
    frame(261, 'teleport', SEAL[1], 3, 2, 262),
    frame(262, 'teleport', SEAL[2], 3, 1, 263, sound=SMOKE_SND, extra=opoint(SMOKE, CX, CY, action=PUFF)),
    frame(263, 'teleport', BLANK, 3, 4, 264, body=False),
    frame(264, 'teleport', BLANK, 3, 1, 265, body=False),
    frame(265, 'teleport', THRUST[0], 3, 1, 266, extra=opoint(SMOKE, CX, CY, action=PUFF)),
    frame(266, 'teleport', THRUST[1], 3, 2, 267, dvx=3, sound=SWISH,
          extra=blade(60, dvx=6, dvy=-4, fall=70, vrest=15, bdefend=60, injury=45)),
    frame(267, 'teleport', THRUST[2], 3, 3, 268),
    frame(268, 'teleport', THRUST[2], 3, 4, 999),

    '# DvA  Rope blade: he punches his arm out and the blade shoots off on a rope\n'
    '# (c_rope.txt, visual) to ~210 px; the hitboxes grow with it. A hit dizzies the\n'
    '# target and combat.lua/physics.lua reel them in to his feet, ready for his\n'
    '# blade combo (A on a dizzy target).',
    frame(270, 'rope_blade', ROPE[0], 3, 2, 271, mp=ROPE_MP),
    frame(271, 'rope_blade', ROPE[1], 3, 1, 272, sound=ROPE_SND,
          extra=opoint(ROPE_OBJ, CX + 26, CY - 50) + blade(ROPE_REACH[0], fall=50, vrest=30, bdefend=16, injury=20)),
    frame(272, 'rope_blade', ROPE[1], 3, 1, 273, extra=blade(ROPE_REACH[1], fall=50, vrest=30, bdefend=16, injury=20)),
    frame(273, 'rope_blade', ROPE[1], 3, 1, 274, extra=blade(ROPE_REACH[2], fall=50, vrest=30, bdefend=16, injury=20)),
    frame(274, 'rope_blade', ROPE[1], 3, 3, 275, extra=blade(ROPE_REACH[3], fall=50, vrest=30, bdefend=16, injury=20)),
    frame(275, 'rope_blade', ROPE[2], 3, 3, 276),
    frame(276, 'rope_blade', ROPE[0], 3, 2, 999),   # a miss: the rope comes back
    # A hit (combat.lua) puts him in 277 and reels the target in at REEL_SPEED
    # (physics.lua, Scorpion-style, ~1 s over full range) while the rope shortens
    # with them; when they arrive he goes to 278, and they are still dizzy.
    frame(277, 'rope_reel', ROPE[2], 3, 60, 278),
    frame(278, 'rope_reel', ROPE[0], 3, 3, 999),

    '# DJA  Izuna drop: a command grab (itr kind 3 catches anyone, even blocking).\n'
    '# He leaps up with them, flips upside down and drives them head-first into the\n'
    '# ground (physics.lua turns the landing into the slam, 288): 50 on impact, then\n'
    '# they bounce away (thrown, 20 more when they land).',
    frame(280, 'izuna_grab', GRAB[0], 3, 2, 281, mp=IZUNA_MP),
    frame(281, 'izuna_grab', GRAB[1], 3, 2, 282, extra=catch(CX + 2, CY - 62, 46, 56, 283, 132)),
    frame(282, 'izuna_grab', GRAB[2], 3, 5, 999),
    frame(283, 'izuna', GRAB[3], 9, 2, 284, extra=cpoint(CX + 30, CY - 40, 132)),
    frame(284, 'izuna', DIVE[0], 9, 1, 285, dvy=ABSOLUTE - 14, extra=cpoint(CX + 20, CY - 70, 134)),
    frame(285, 'izuna', DIVE[1], 9, 3, 286, extra=cpoint(CX + 10, CY - 60, 136, cover=11)),
    frame(286, 'izuna', DIVE[2], 9, 3, 287, dvy=ABSOLUTE, extra=cpoint(CX + 8, CY - 30, 136, cover=11)),
    frame(287, 'izuna', DIVE[2], 9, 40, 288, dvy=ABSOLUTE + 16, extra=cpoint(CX + 8, CY - 30, 136, cover=11)),
    frame(288, 'izuna_slam', DIVE[3], 9, 2, 289, sound=SLAM_SND, body=False, extra=cpoint(CX + 26, CY - 20, 136, injury=50, cover=11)),
    frame(289, 'izuna_slam', DIVE[3], 9, 2, 290, body=False,
          extra=cpoint(CX + 26, CY - 20, 181, throwvx=6, throwvy=-6, throwinjury=20, cover=11)),
    frame(290, 'izuna_slam', DIVE[3], 3, 8, 999, body=False),   # (the thrown body would hit him)
]


def header():
    w, h, rows = CELL
    lines = ['<bmp_begin>', 'name: Cod1eh', 'head: mods/darthnox/cod1eh_f.bmp', 'small: mods/darthnox/cod1eh_s.bmp',
             f'file(0-{rows * 4 - 1}): mods/darthnox/cod1eh.bmp', f'w: {w}  h: {h}  row: 4  col: {rows}']
    lines += [f'{k} {v:.6f}' if isinstance(v, float) else f'{k} {v}' for k, v in MOVEMENT]
    lines += ['<bmp_end>', '',
              '# Art: AutoSprite character "Cod1eh v2" (cmwgkkt7e00gdbhdkkqq4u1p5, bracer only), every clip',
              '# from his "Idle Lock" pose, converted with tools/autosprite_to_lf2.py at s0.350427.',
              '# Generated by tools/cod1eh_moves.py: edit that, not this file.', '']
    return '\n'.join(lines)


def obj_header(name, pic_file, cell, pictures=8):
    w, h = cell
    return '\n'.join(['<bmp_begin>', f'file(0-{pictures - 1}): {pic_file}  w: {w}  h: {h}  row: 4  col: {pictures // 4}',
                      'weapon_hit_sound: data\\020.wav', 'weapon_drop_sound: data\\020.wav',
                      'weapon_broken_sound: data\\020.wav', '<bmp_end>', '', f'# {name}',
                      '# Generated by tools/cod1eh_moves.py; art from tools/make_cod1eh_fx.py.', ''])


def obj_frame(n, name, picture, state, wait, nxt, center, dvx=0, hits='hit_a: 0  hit_d: 0  hit_j: 0', extra=''):
    return (f'<frame> {n} {name}\n   pic: {picture}  state: {state}  wait: {wait}  next: {nxt}  dvx: {dvx}  dvy: 0'
            f'  centerx: {center[0]}  centery: {center[1]}  {hits}\n{extra}<frame_end>\n')


KUNAI_SPEED, KUNAI_DAMAGE, KUNAI_DRAIN = 15, 22, 25   # ~20 frames of flight: ~600 px


def kunai_object():
    c = (20, 7)
    hit = itr(4, 2, 34, 10, dvx=4, fall=40, vrest=10, bdefend=16, injury=KUNAI_DAMAGE)
    body = bdy(4, 2, 34, 10)
    fly = [obj_frame(n, 'flying', n, 3000, 1, n + 1 if n < 3 else 0, c, dvx=KUNAI_SPEED,
                     hits=f'hit_a: {KUNAI_DRAIN}  hit_d: 40  hit_j: 0', extra=hit + body) for n in range(4)]
    ends = [obj_frame(base + k, name, 4 + k, state, 1, base + k + 1 if k < 3 else 1000, c)
            for base, name, state in ((10, 'hiting', 3001), (20, 'hit', 3002), (30, 'rebounding', 3003))
            for k in range(4)]
    ends += [obj_frame(40 + k, 'disappearing', 5 + k, 3004, 1, 41 + k if k < 2 else 1000, c) for k in range(3)]
    return obj_header("Cod1eh's kunai (D>A fan): flies straight, breaks on a hit like a ball.",
                      'mods/darthnox/c_kunai.bmp', (40, 14)) + '\n'.join(fly + ends)


SMOKE_LOOPS = 6                   # 6 x 4 frames x 4 ticks ~ 3 s of cloud, then it thins out


def smoke_object():
    c = (75, 84)
    loop = [obj_frame(n, 'smoke', n % 4, 3000, 3, n + 1, c) for n in range(SMOKE_LOOPS * 4)]
    fade = [obj_frame(SMOKE_LOOPS * 4 + k, 'smoke_fade', 4 + k, 3000, 3, SMOKE_LOOPS * 4 + k + 1 if k < 3 else 1000, c)
            for k in range(4)]
    puff = [obj_frame(PUFF + k, 'puff', 4 + k, 3000, 1, PUFF + k + 1 if k < 3 else 1000, c) for k in range(4)]
    return obj_header("Cod1eh's smoke: frames 0-27 the D^J cloud (physics.lua slows enemies inside it\n"
                      "# while it is below frame 24); 30-33 the teleport puff (no slow). Visual only.",
                      'mods/darthnox/c_smoke.bmp', (150, 96)) + '\n'.join(loop + fade + puff)


def rope_object():
    c = (2, 7)
    waits = (1, 1, 1, 2, 2, 1, 1, 1)
    frames = [obj_frame(n, 'rope', n, 3000, w, n + 1 if n < 7 else 1000, c) for n, w in enumerate(waits)]
    # 20-35: one length each (15, 28, ... 210 px); physics.lua holds the one that
    # reaches the target being reeled in, so the rope shortens as they come.
    frames += [obj_frame(20 + k, 'rope_reel', 8 + k, 3000, 99, 1000, c) for k in range(16)]
    return obj_header("Cod1eh's DvA rope blade, visual only (his frames carry the hitboxes).",
                      'mods/darthnox/c_rope.bmp', (230, 14), pictures=24) + '\n'.join(frames)


def main(assets):
    with open(os.path.join(assets, 'cod1eh.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(header() + '\n' + '\n'.join(FRAMES))
    for name, text in (('c_kunai.txt', kunai_object()), ('c_smoke.txt', smoke_object()), ('c_rope.txt', rope_object())):
        with open(os.path.join(assets, name), 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
    print('wrote cod1eh.txt, c_kunai.txt, c_smoke.txt, c_rope.txt')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
