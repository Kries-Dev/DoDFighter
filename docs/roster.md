# Roster stats

Read from the game data by a headless probe (OpenLF2 + the DarthNox mod,
2026-11-13). Use it to balance new fighters against the stock cast.

## Shared by everyone

- **HP 500, MP 500** for every fighter in Versus (`points.full`); LF2 has no
  per-character health. MP regenerates on its own (faster at low HP).
- **Defence** is the same for everyone except DarthNox (takes 10% more
  damage, `armor` 91) and the three armored characters below.
- **Rolling** (run + D) is invulnerable for everyone except Julian and Knight.
- Jump height is the launch speed; peak height in pixels is about
  86 × (speed / 16.3)² (Davis: 16.3 → 86 px, measured).

## Fighters

| Fighter | Walk | Run | Jump (speed → ≈px) | Dash | Punch dmg | Armor | Invulnerable moves |
|---|---|---|---|---|---|---|---|
| **Mathilde** (63) | **7.0** | **13.5** | 16.3 → 86 | 21 | 22 (staff), chains into a 40 smash | none; **takes +25% damage** | vault launch; roll |
| **Cod1eh** (68) | 6.0 | 12.5 | 17.0 → 94 | 20 | (shuriken, Rudolf's) | none; **takes +15% damage** | roll |
| **DarthNox** (61) | **6.0** | 10.5 | 16.3 → 86 | 19 | 30 (sword) | none; **takes +10% damage** | D^A launch (4 ticks); parry counter stab (whole stab); roll |
| Davis (11) | 5.0 | 10.0 | 16.3 → 86 | 18 | 20 | — | D^A (4 of 21 ticks); roll |
| Deep (1) | 5.0 | 8.5 | 16.3 → 86 | 16 | 35 | — | roll |
| Dennis (9) | 5.0 | 10.5 | 16.3 → 86 | 18 | 30 | — | roll |
| Woody (10) | 5.0 | 10.0 | 16.3 → 86 | 18 | 20 | — | teleport D^J / DvJ (16 of 29 ticks); D>J fly crash (2); roll |
| John (2) | 5.0 | 11.2 | 16.3 → 86 | 18 | 20 | — | roll |
| Henry (4) | 5.0 | 11.0 | 16.3 → 86 | 18 | (bow) | — | roll |
| Rudolf (5) | 6.0 | 13.0 | 16.3 → 86 | 18 | (shuriken) | — | roll |
| Louis (6) | 5.0 | 9.0 | 18.7 → 113 | 17.5 | 20 | **yes** while standing, walking, dashing, jumping or blocking | DJA transform (all 72 ticks); roll |
| Firen (7) | 5.0 | 9.6 | 16.3 → 86 | 18 | 20 | — | roll |
| Freeze (8) | 5.0 | 9.3 | 16.3 → 86 | 18 | 20 | — | roll |
| Louis EX (50) | 6.2 | 14.0 | 18.7 → 113 | 20 | 35 | — | roll |
| Firzen (51) | 6.0 | 13.0 | 17.0 → 94 | 22 | 20 | — | roll |
| Julian (52) | 5.8 | 12.0 | 17.3 → 97 | 19 | 35 | **yes** (super armor unless hit in the last ~1 s) | DJA (11 of 22 ticks); **no roll i-frames** |
| Knight (37) | 6.0 | 8.5 | 13.5 → 59 | 16 | (sword) | **yes** (super armor unless hit in the last ~1 s) | **no roll i-frames** |
| Jan (36) | 5.2 | 11.9 | 16.3 → 86 | 18 | 20 | — | roll |
| Sorcerer (34) | 4.8 | 11.1 | 16.1 → 84 | 17.7 | 15 | — | roll |
| Jack (33) | 5.0 | 9.9 | 16.3 → 86 | 18 | 20 | — | roll |
| Mark (32) | 4.4 | 9.0 | 13.3 → 57 | 13 | 35 | — | roll |
| Monk (35) | 4.0 | 8.0 | 16.3 → 86 | 15 | 20 | — | roll |
| Hunter (31) | 4.2 | 8.4 | 16.3 → 86 | 15 | (bow) | — | roll |
| Bandit (30) | 4.0 | 8.0 | 16.3 → 86 | 15 | 20 | — | roll |
| Bat (38) | 5.0 | 10.0 | 16.3 → 86 | 18 | 20 | — | D>J (4 of 23 ticks); roll |
| Justin (39) | 5.0 | 10.0 | 16.3 → 86 | 18 | 20 | — | roll |

"Punch dmg" is the best hit of the A, A combo. Henry, Hunter, Rudolf and Knight
attack with weapons/projectiles from their normal-attack frames, so it isn't a
plain number.

## Special moves (MP cost, best direct hit, i-frames)

Projectile damage lives in the projectile object, so "proj" moves show no
direct hit here.

| Fighter | Moves |
|---|---|
| **Mathilde** | D>A staff extension 50 MP, ~200 px, 32 (J: vault, freezing strike 22; J again: fire vault, burning strike 30 + ground fire) · DvA staff combo 40 MP, 10 hits ~148, last hit freezes (also out of either vault) · D^A homing staff 75 MP, 35 · D^J tornado 200 MP, drifts forward and lifts for ~1 s, ~35 · DvJ clone 300 MP, AI copy with 15 HP |
| **DarthNox** | D>A crescent 60 MP, proj 21 · D>J lunge 75 MP, 11 × ~4 hits · D^A rising slash 100 MP, 45 (+20), i-frames on launch · DvA flurry 50 MP, 3 × 14 + 22 finisher (+20 MP per extra round) · DJA parry 200 MP, counter 70 + dizzy, counter is invulnerable · D>J can cancel into D^A |
| Davis | D>A ball 40 · D^A dragon punch 225 MP, 85 · DvA many punch 75 MP, 45 · D^J jump hit 25 MP |
| Deep | D>A blast 75 MP, proj · DvA jump sword 75 MP, 54 · D>J dash sword 150 MP, 54 · D^J jump sword |
| Dennis | D>A ball 40 · D^A chase ball 100 · DvA many foot 75 MP, 45 · D>J whirlwind kick 75 MP, 45 |
| Woody | D>A ball 125 · D^A uppercut 70 · DvA 50 MP, 20 · D>J fly crash 200 MP, 85 · D^J / DvJ teleport 50 MP |
| John | D>A disc 75 · D^A biscuit 250 · D>J force field 100 · D^J heal other 350 · DvJ heal self 350 |
| Henry | D>A blast push 150 · D>J super arrow 200 · D^J flute 350 · DJA 5 arrows 150 |
| Rudolf | D>A shuriken 100 · D>J jump sword 35 · D^J disappear 350 · DvJ clone 350 · DJA transform |
| Louis | D>A blast push 150 · D>J 1000 kicks 50 MP, 30 · D^J catch 100 · DJA transform (invulnerable) |
| Firen | D>A fireball 75 · D>J burn run 75 MP, 45 · D^J explosion 300 · DvJ flame 150 |
| Freeze | D>A ice ball 100 · D>J icicle 150 · D^J whirlwind 300 · DvJ ice sword 150 |
| Louis EX | D>A air push 100 · DvA up spear 70 |
| Firzen | D^A disaster 100 · D>J ball 25 · D^J volcano 250 |
| Julian | D>A ball 10 · D^A uppercut 80 · D>J big ball 125 · D^J explosion 100 · DJA 25 (i-frames) |
| Knight | D>A sword 45 |
| Jan | D^A 150 · D^J 200 (projectiles/heals) |
| Sorcerer | D>A 75 · D>J 125 · D^J heal other 350 · DvJ heal self 350 |
| Jack | D>A ball 50 · D^A uppercut 125 MP, 70 |
| Mark | D>A charge 45 · D>J 50 MP, 80 |
| Monk | D>A ball 100 MP, 35 |
| Bat | D>A ball 125 · D>J 50 MP, 60 · D^J bats 200 |
| Justin | D>A ball 75 · DvA 75 MP, 55 |
