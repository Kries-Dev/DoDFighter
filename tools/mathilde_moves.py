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

CX, CY = 44, 89                   # sheet registration (autosprite_to_lf2.py output)
CELL = (93, 93, 26)               # w, h, rows of mathilde.bmp
BODY = (CX - 15, CY - 72, 30, 72)
ABSOLUTE = 550                    # dvy above 500 sets the speed: dvy - 550 (see darthnox_moves.py)

# Sheet pictures (row * 4 + column), see mods/darthnox/README.md
IDLE, WALK, RUN = (0, 1, 2, 3), (4, 5, 6, 7), (8, 9, 10, 11)
SWING, POKE, JUMP = (12, 13, 14), (16, 17, 18), (20, 21)
HURT, FALL, SMASH, BLOCK = (24, 25, 26), (28, 29, 30, 31), (32, 33, 34), (36, 37, 38)
EXTEND, VAULT, THROWING = (40, 41, 42, 43), (44, 45, 46, 47), (48, 49, 50)
TWIRL, DANCE, ROLL, GRAB, THROW = (52, 53, 54, 55), (56, 57, 58, 59), (60, 61, 62, 63), (64, 65, 66, 67), (68, 69, 70)
ICE, BURN = (72, 73), (76, 77, 78)
VAULT_ICE, CAST = (80, 81, 82, 83), (84, 85, 86)   # vault with a frost aura; conjure-and-fling
COMBO_PICS = (88, 89, 90, 91, 92, 93, 94, 95)     # the staff-combo clip: eight strikes with motion arcs
VAULT_FIRE = (96, 97, 98, 99)                     # second vault, fire aura
DIVE = (100, 101, 102, 103)                       # EXTEND tilted 35 deg down (tools/make_mathilde_dive.py)

SWISH = 'data\\008.wav'           # weapon swing
WHOOSH = 'data\\045.wav'          # big swish (extension stab)
FLUTE = 'data\\056.wav'           # Henry's flute start (tornado)
CLONE = 'data\\062.wav'           # Rudolf's clone (unused now: she has her own)
PUNCH = 'data\\007.wav'           # LF2's punch impact (her grab-and-hit keeps it)
# Her own sounds (supplied as mp3, converted with tools/to_wav.ps1)
# Rebuilt 2026-11-13 from the original uploads (resampled, loudness matched to
# m_staff.wav) under fresh names; the old m_run/m_vault/m_twist/m_clone files
# loaded but were never heard in game, while m_staff.wav played on every move.
STAFF_SND = 'mods/darthnox/snd/m_staff.wav'    # homing staff cast
RUN_SND = 'mods/darthnox/snd/mrun.wav'         # running stab, D>A stab, diving stab
VAULT_SND = 'mods/darthnox/snd/mvault.wav'     # vault strikes
TWIST_SND = 'mods/darthnox/snd/mtwist.wav'     # tornado
CLONE_SND = 'mods/darthnox/snd/mclone.wav'     # clone
FIRE_SND = 'data\\070.wav'        # Firen's fire-trail sound (second vault)
FIREN_FLAME, GROUND_FIRE = 211, 50  # Firen's flame object and its ground-fire action

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
HITS = dict(Fa=235, Ua=245, Da=270, Fj=0, Uj=250, Dj=260, ja=0)   # DvA: the staff combo, also on its own

STAFF_DAMAGE = 35                 # homing staff copy (John's disc does 55)
STAFF_DRAIN = 6                   # its hp lost per frame: ~2.5 s of chasing
TORNADO_TICKS = 32                # the tornado object lifts for ~1 s (Henry's flute holds ~3 s)
TORNADO_SPEED = 4                 # it drifts forward ~130 px while it lifts
POLE_REACH = 170                  # D>A: the staff shoots out to 200 px (Wukong-style), m_pole.txt
POLE_SPAWN = (40, -41)            # where it leaves her staff, rel. to her feet (measured: staff tip +44, -41)
COMBO_SCALE = 0.24                 # DvA after the vault: Louis EX's DvA hits at 40%, more of them
VAULT_SPEED = 5                   # forward speed: lands ~140 px out, in front of a target the stab reached
LAUNCH = 13                       # launcher strike: upward speed given to a grounded target
DIVE_SPEED = 9                    # diving stab: 9 forward, 9 down = 45 degrees
VAULT_LAUNCH = 13                 # absolute launch speed: ~90 px, over a standing fighter


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
VAULT_FOLLOW = {'a': 300, 'Da': 310, 'ja': 315}   # vault 1: A = launcher strike, DvA = diving stab
VAULT2_FOLLOW = {'a': 295, 'Da': 310}             # vault 2: A = launcher strike (no third vault)
VAULT_MP = 20                                      # each vault costs this


def louis(injury):                # Louis EX's DvA hit, scaled
    return max(1, round(injury * COMBO_SCALE))


# DvA during the vault: a Louis EX-style flurry of staff strikes. Louis EX's DvA
# lands 40, 40, 30, 60, 70, 70, 55; this one lands ten hits at 40% of those
# (16-28 each). fall 1 keeps a standing victim flinching on every hit (the
# engine steps its stun counter 20/40/60, so anything bigger floors them by the
# 4th hit; 0 would count as 20), and vrest 6 (longer than a frame plus its 3-tick
# hit lag) so each frame lands once, until the last strike launches them (fall
# 70) and FREEZES them (effect 3). The freeze is on the finisher, not the vault:
# hitting a frozen fighter shatters the ice into a knockdown, which would cut
# the combo short. A victim already falling is juggled (dvy -10), like Louis
# EX's. She steps forward 2 px a frame to stay on them.
C = COMBO_PICS
COMBO_HITS = [  # (picture, injury from Louis EX, reach, dvx, dvy)
    (C[0], 40, 62, 2, 0), (C[1], 40, 62, 2, 0), (C[2], 30, 62, 2, 0), (C[3], 60, 62, 2, 0),
    (C[4], 40, 62, 2, 0), (C[5], 30, 62, 2, 0), (C[0], 60, 62, 2, 0), (C[2], 70, 66, 3, 0),
    (C[6], 55, 64, 2, 0), (C[7], 70, 68, 0, -20),
]
COMBO = ['# DvA (on its own, or out of either vault): ten staff strikes at 40% of Louis\n'
         '# EX\'s DvA, the last one launching and freezing',
         frame(270, 'staff_combo', C[3], 3, 1, 271, mp=40)]
for k, (picture, injury, reach, dvx, dvy) in enumerate(COMBO_HITS):
    last = k == len(COMBO_HITS) - 1
    COMBO.append(frame(271 + k, 'staff_combo', picture, 3, 1 if not last else 2, 272 + k, dvx=2,
                       sound=SWISH if k % 2 == 0 or last else None,
                       extra=staff(reach, dvx=dvx, dvy=dvy or -10, fall=70 if last else 1, vrest=6,
                                   bdefend=60 if last else 16, injury=louis(injury))))
COMBO.append(frame(271 + len(COMBO_HITS), 'staff_combo', C[7], 3, 12, 999, hits={'j': 240, 'ja': 315}))   # J: vault after the launcher

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
    frame(86, 'run_attack', EXTEND[1], 3, 2, 87, dvx=4, sound=RUN_SND, extra=staff(96, dvx=8, dvy=-3, fall=70, vrest=15, bdefend=60, injury=38)),
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
    *[pic(120 + i, 'catching', GRAB[i]) for i in range(4)],   # Davis's punch-impact sounds stay (object_data.lua swaps only for DarthNox)
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

    '# D>A  Staff extension: she stabs and the staff shoots out Wukong-style to\n'
    '# ~200 px (m_pole.txt, object 66, drawn from her staff tip) over ~9 ticks,\n'
    '# holds, and retracts; the hitbox grows with it (90, 150, 200 px). J during it vaults.',
    frame(235, 'staff_ext', EXTEND[0], 3, 2, 236, mp=50),
    frame(236, 'staff_ext', EXTEND[1], 3, 2, 237, sound=RUN_SND, hits={'j': 240, 'ja': 315},
          extra=opoint(66, CX + POLE_SPAWN[0], CY + POLE_SPAWN[1]) + staff(77, dvx=6, fall=40, vrest=20, bdefend=30, injury=32)),
    frame(237, 'staff_ext', EXTEND[1], 3, 2, 238, hits={'j': 240, 'ja': 315}, extra=staff(128, dvx=6, fall=40, vrest=20, bdefend=30, injury=32)),
    frame(238, 'staff_ext', EXTEND[2], 3, 3, 239, hits={'j': 240, 'ja': 315}, extra=staff(POLE_REACH, dvx=6, fall=40, vrest=20, bdefend=30, injury=32)),
    frame(239, 'staff_ext', EXTEND[2], 3, 4, 999, hits={'j': 240, 'ja': 315}),   # same staff line as 236-238 while the pole retracts

    '# Vault (J after the stab, or at the end of the DvA launcher; 20 MP): a flip,\n'
    '# no hit of its own. In the air: A = launcher strike (300), DvA = diving stab.\n'
    '# J after the strike = vault 2 (290, 20 MP), whose A (295) is the last strike.',
    *[frame(base + i, name, VAULT[min(i, 3)], 3, w, base + i + 1 if i < 4 else 999, dvx=dvx, dvy=dvy,
            mp=VAULT_MP if i == 0 else 0, body=i >= 3, hits=follow)
      for base, name, follow in ((240, 'vault', VAULT_FOLLOW), (290, 'vault2', VAULT2_FOLLOW))
      for i, (w, dvx, dvy) in enumerate([(1, 3, 0), (1, VAULT_SPEED, ABSOLUTE - VAULT_LAUNCH), (3, 0, 0), (3, 0, 0), (4, 0, 0)])],

    '# Launcher strike (A during a vault): one rising staff swing. A target on the\n'
    '# ground is launched (dvy -13); one already in the air only gets a small pop\n'
    '# (combat.lua), so it starts a juggle instead of sending them away.\n'
    '# 300-303 (vault 1, J = vault 2) and 295-298 (vault 2, ends the chain).',
    *[f for base, follow in ((300, {'j': 290}), (295, None)) for f in (
        frame(base, 'air_strike', SWING[0], 3, 1, base + 1, dvy=ABSOLUTE - 2, hits=follow),
        frame(base + 1, 'air_strike', SWING[1], 3, 2, base + 2, dvx=3, sound=VAULT_SND, hits=follow,
              extra=itr(CX - 25, CY - 85, 105, 150, dvx=4, dvy=-LAUNCH, fall=70, vrest=15, bdefend=60, injury=26)),
        frame(base + 2, 'air_strike', SWING[2], 3, 3, base + 3, hits=follow),
        frame(base + 3, 'air_strike', SWING[2], 3, 3, 999, hits=follow))],

    '# Diving stab: DJA during the D>A stab (a jump first, 315-316) or DvA during a\n'
    '# vault. A short hang, then she drives the staff down-forward at 45 degrees and\n'
    '# drops along it. Spikes an airborne target, knocks down a standing one.',
    frame(315, 'dive_jump', JUMP[0], 3, 1, 316, dvx=3, dvy=ABSOLUTE - 14, body=False),
    frame(316, 'dive_jump', JUMP[1], 3, 4, 310, dvx=3),
    frame(310, 'dive_stab', DIVE[0], 3, 1, 311, dvy=ABSOLUTE - 3),
    *[frame(311 + i, 'dive_stab', DIVE[1 + i], 3, 2 + i, 312 + i, dvx=DIVE_SPEED, dvy=ABSOLUTE + DIVE_SPEED,
            sound=RUN_SND if i == 0 else None,
            extra=itr(CX, CY - 45, 85, 100, dvx=8, dvy=8, fall=70, vrest=15, bdefend=60, injury=34)) for i in range(2)],
    frame(313, 'dive_stab', DIVE[3], 3, 4, 999, dvx=4, dvy=ABSOLUTE + DIVE_SPEED),

    '# D^A  Homing staff: a throwing motion that sends a spinning copy of the staff\n'
    '# (m_staff.txt, object 64) after the nearest enemy, like John\'s disc.',
    frame(245, 'staff_throw', CAST[0], 3, 2, 246, mp=75),
    frame(246, 'staff_throw', CAST[1], 3, 2, 247),
    frame(247, 'staff_throw', CAST[2], 3, 1, 248, sound=STAFF_SND, extra=opoint(64, CX + 28, CY - 48)),
    frame(248, 'staff_throw', CAST[2], 3, 5, 999),

    '# D^J  Tornado: she twirls and sends a magic tornado (m_tornado.txt, object 65)\n'
    '# drifting forward; its whirlwind itrs (kind 10/11, like Freeze\'s whirlwind)\n'
    '# match the drawing and lift anyone it touches for ~1 s.',
    frame(250, 'tornado', TWIRL[0], 3, 1, 251, mp=200),
    frame(251, 'tornado', TWIRL[1], 3, 1, 252, sound=TWIST_SND, extra=opoint(65, CX + 40, CY - 65)),
    *[frame(252 + i, 'tornado', TWIRL[i % 4], 3, 2, 253 + i if i < 5 else 258) for i in range(6)],
    frame(258, 'tornado', TWIRL[2], 3, 3, 999),

    '# DvJ  Clone: a dance spin, then a copy of herself (object 63) appears behind\n'
    '# her, AI-controlled like Rudolf\'s clones; objects.lua gives it 15 HP (Rudolf\'s\n'
    '# have 10).',
    frame(260, 'clone', DANCE[0], 3, 2, 261, mp=300),
    *[frame(261 + i, 'clone', DANCE[(i + 1) % 4], 3, 2, 262 + i) for i in range(4)],
    frame(265, 'clone', DANCE[1], 3, 1, 266, sound=CLONE_SND, extra=opoint(63, CX - 30, CY)),
    frame(266, 'clone', DANCE[3], 3, 3, 999),
] + COMBO


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
    # 16 frames x 2 ticks = 32 ticks of lift while drifting forward, then fade.
    # The boxes cover the drawn funnel: kind 10 lifts, kind 11 keeps the lifted up.
    c = (75, 65)
    lift = itr(25, 0, 100, 130, vrest=1, injury=1, kind=10) + itr(5, 0, 140, 130, vrest=1, injury=1, kind=11)
    spin = [ball_frame(n, 'tornado', n % 4, 3000, n + 1, c, dvx=TORNADO_SPEED, extra=lift) for n in range(16)]
    fade = [ball_frame(16 + i, 'tornado_fade', 4 + i, 3000, 17 + i if i < 3 else 1000, c, dvx=TORNADO_SPEED) for i in range(4)]
    return ball('Mathilde\'s D^J tornado: drifts forward and lifts what it touches for ~1 s.',
                'mods/darthnox/m_tornado.bmp', (150, 130), c, spin + fade)


def pole_ball():
    # The extended staff, drawn from her staff tip (centre at its left end). Visual
    # only: the hitbox is on her frames 236-238 and grows with it. Out over 9
    # ticks (70/140/200 px), held 6, back in over 8.
    c = (2, 8)
    timeline = [(0, 2), (1, 2), (2, 2), (3, 2), (4, 0), (5, 0), (6, 0), (7, 0)]   # (picture, wait): out 9 ticks, hold 3, back 4
    frames = []
    for n, (picture, wait) in enumerate(timeline):
        nxt = n + 1 if n < len(timeline) - 1 else 1000
        frames.append(ball_frame(n, 'pole', picture, 3000, nxt, c).replace('wait: 1', f'wait: {wait}'))
    return ball('Mathilde\'s D>A staff extension (Wukong-style), visual only.',
                'mods/darthnox/m_pole.bmp', (210, 16), c, frames)


def main(assets):
    with open(os.path.join(assets, 'mathilde.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(header() + '\n' + '\n'.join(FRAMES))
    with open(os.path.join(assets, 'm_staff.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(staff_ball())
    with open(os.path.join(assets, 'm_tornado.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(tornado_ball())
    with open(os.path.join(assets, 'm_pole.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(pole_ball())
    print('wrote mathilde.txt, m_staff.txt, m_tornado.txt, m_pole.txt')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
