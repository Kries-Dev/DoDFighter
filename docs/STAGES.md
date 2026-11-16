# DoD Fighter: stages, stage mode and screenpack (plan)

Status (2026-11-15): Urban Bridge, and the pilot **Sunset Rooftop** (bg 62,
`art/stages/rooftop_sunset.webp`, built with `tools/build_stage.py`): one
painting (the user's second, wider version) scrolled 1839 px wide, music "Urban Jungle" (`match.lua` `MUSIC`), closed ends (side buildings = walls, set in
`camera.lua`), 21 light layers (lanterns, railing lights and reflections
flickering, string bulbs, windows twinkling, the pink neon tube buzzing). No
parallax yet: that needs the layers painted separately (section 4).

Rebuild:
```
python tools/build_stage.py art/stages/rooftop_sunset.webp mods/darthnox/assets/bg roof "Sunset Rooftop" 518 657 neon=1462,350,1532,374
```
(518/657 = the floor's back and front edge rows in the painting; the neon box
is in the painting's own pixels.) A stage needs one line in `catalog.lua`
(`stages_added`), its walls in `camera.lua` (`WALLS`) and its files in
`package.manifest`, and its music in `match.lua` (`MUSIC`).

**Stage mode** (2026-11-17): stage 1 = 1-1 Fortress Gate, 1-2 Barracks Yard, 1-3 Cell Block,
1-4 Barracks, 1-5 Throne Hall; stage 2 = the city below (was stage 1 on 2026-11-16).
Layout and music: `tools/stage_layout.py`. Rebuild commands:
```
python tools/build_stage.py art/stages/fort_gate.webp mods/darthnox/assets/bg gate "Fortress Gate" 495 655 lamps=1745,110,1850,185 lamps=380,530,560,625 lamps=880,520,960,560
python tools/build_stage.py art/stages/fort_yard.webp mods/darthnox/assets/bg yard "Barracks Yard" 472 655 lamps=1000,470,1080,560 lamps=150,540,320,580 lamps=480,560,760,610 dim
python tools/build_stage.py art/stages/cells.webp mods/darthnox/assets/bg cells "Cell Block" 492 655 lamps=250,180,370,280 lamps=940,180,1060,280 lamps=1640,180,1760,280 dim
python tools/build_stage.py art/stages/barracks.webp mods/darthnox/assets/bg barr "Barracks" 488 655 lamps=180,160,300,230 lamps=590,160,710,230 lamps=1060,160,1180,230 lamps=1740,160,1860,230 lamps=1075,360,1115,410 dim
python tools/build_stage.py art/stages/throne.webp mods/darthnox/assets/bg hall "Throne Hall" 488 655 lamps=310,80,460,210 lamps=890,0,1110,190 lamps=1540,80,1690,210 lamps=330,360,390,420 lamps=810,310,870,440 lamps=1130,310,1190,440 lamps=1610,360,1670,420 lamps=620,330,680,370 lamps=1320,330,1380,370 dim
```

**The city, now stage 2** (2026-11-16): 1-1 to 1-4 on the Sunset Rooftop, 1-5 on
the **Rooftop at Night** (bg 63, `art/stages/rooftop_night.webp`, its own boss
arena, 913 px). Waves, order and HP are LF2's own; only the scroll bounds and
item x positions are scaled to our stages. Music: "Urban Jungle" from 1-1,
"Urban Jungle end" from 1-5, "Boss appears 1" when 1-5's boss wave starts (1-4's boss wave keeps Urban Jungle). Every Bandit in stage 1 is EVS Fanboy (`SWAPS` in `stage_mode.lua`). How it's wired:

- `mods/darthnox/stage.txt` is our stage-mode file (LF2's stage.dat, decrypted,
  stage 1 edited; look for "# DoD"). After editing:
  `python tools/stage_dat.py mods/darthnox/stage.txt mods/darthnox/assets/stage.dat`.
- `stage_mode.lua` replaces base/game/stage (manifest `replace=`) only to read
  that file; `stage.lua` picks each sub-stage's background (`STAGES`) and swaps
  it between sub-stages; `match.lua` starts the run on it.
- Rules for the file: a sub-stage's last bound = its stage's right wall
  (`camera.lua`), since players must walk there to go on; **no two phases in a
  row may share a bound** (an engine quirk: the last phase then never ends).

Rebuild the night stage:
```
python tools/build_stage.py art/stages/rooftop_night.webp mods/darthnox/assets/bg roofn "Rooftop at Night" 690 895 dim
```

**Stage length**: the game width comes from the painting's proportions, not its pixel
count (the floor depth sets the scale): a 3:1 picture gives ~1800 px (~2.3 screens).
Image tools only output up to ~3:2, so longer stages are made by outpainting the
picture in pieces (continue it to the right, same horizon and floor) and stitching.
Stage-mode enemies ignore the side walls (`camera.lua`), so they can walk in.

## 1. What the engine can do (read from OpenLF2's scripts, not guessed)

| Feature | How it works | What it means for the art |
|---|---|---|
| Screen | 794 × 550; the HP/MP panel covers the top ~128 px | keep the top of every stage plain (sky, ceiling) |
| Stage width | any width; the camera scrolls between the side walls | versus stages ~1200–1600 px, stage-mode stages 2000–3000 px |
| Layers | any number, drawn back to front; each has a picture, x/y, and a **scroll width** | parallax: a layer scrolls in proportion to its width. A 794-wide layer stays still, a stage-wide layer moves with the floor, a wider one moves faster (foreground) |
| Transparency | per layer; **pure black (0,0,0) is see-through** | transparent layers come to me as PNG with alpha; I convert. Never use pure black in the art |
| Looping | a layer can repeat horizontally | clouds, skylines and fences can be one tile repeated |
| Animation | per layer timer: visible for frames c1–c2 of every cc ticks (30 ticks = 1 s) | blinking neon, flickering lamps, and **2–4-frame loops** (water shimmer, flags, smoke) made by alternating layers |
| Colour | each layer is an 8-bit picture: 255 colours + transparent | plenty per layer; big gradients may band slightly, so painterly over smooth |
| Floor | `zboundary`: the walkable band (back edge, front edge) in screen rows | the floor's perspective must match between stages (section 4) |
| Widescreen | OpenLF2 has an "expand" layout that shows more of a stage on wide windows | layers wider than the screen look right there too |
| Music | WMA 8 only (`tools/to_wma.ps1`) | send any format; I convert |

**Stage mode** is one data file (`data/stage.dat`): stages → phases → enemy
waves (who, how many, when, boss flag, the scroll bound per phase, music per
phase). We can replace it with our own file and our own fighters/grunts.

**Screenpack**: the menus draw a handful of named pictures: the title/menu
backdrop, the cursor, the character-select frame, the score board, the
pause/demo signs, plus the HP/MP panel. The mod can swap each of these, and
the title/menu screens are Lua, so layout and animation can change too.

## 2. One aesthetic for everything (rules every stage follows)

Our fighters are bold-outlined, flat cel-shaded, saturated (`STYLE.md`). The
stages must make them pop, not compete:

1. **Painted, no hard black outlines** in backgrounds (outlines belong to the
   fighters). Urban Bridge's painterly pixel look is the reference.
2. **Contrast falls off with depth**: the floor is the most detailed and
   saturated; mid layers are softer; the far layer is hazy and tinted toward the
   sky colour.
3. **The floor reads as a floor**: mid-value, low noise where fighters stand,
   no busy patterns, no bright spots that look like items or projectiles.
4. **One light direction per stage**, and its colour set by the stage's time
   of day (see the palette table in the chosen concept).
5. **Same camera** for every stage: side view, slight top-down tilt, horizon
   and floor at the rows in section 4.
6. **Same pixel density**: paint at 2× or 4× and I downscale, so every stage
   ends up equally crisp at game size.

## 3. Concepts (pick one)

### A. One city, one day (recommended)

Every stage is a district of the same river city, seen at a different time of
day. Urban Bridge is already the first. Stage mode is a journey across the
city from morning to night, so the palette itself tells the story and your
music can follow the clock (bright → warm → moody → neon → dawn finale).

| Stage | Time | Palette | Ideas for animation |
|---|---|---|---|
| Urban Bridge (done) | midday | blue, grey asphalt | water shimmer, drifting clouds |
| Harbour docks | late afternoon | teal water, rust, warm sun | cranes, gulls, waves, a passing boat |
| Old-town rooftops | sunset | orange sky, terracotta | flags, chimney smoke, laundry |
| Circus grounds (Mathilde) | dusk | purple sky, red-and-white tents | bulb strings blinking, spotlights |
| Neon market (Cod1eh) | night | magenta/cyan neon, wet street | signs flickering, rain, steam |
| Fencing hall / castle (DarthNox) | night, indoors | candlelight gold, navy banners | candles, banners swaying |
| Rooftop finale | dawn | pink-gold sky over the skyline | sunrise light shafts |

Why: it matches what exists, gives variety without breaking the look (same
city, same camera, palette by time of day), and every fighter gets a home stage.

### B. Each fighter's world

Musketeer town, jester circus, ninja village, bandit hideout… More variety,
but the stages pull in different directions (period, setting, colour), so
consistency rests entirely on the rules in section 2. Harder to keep unified.

### C. Neon night city

Everything at night in one city. The most consistent and the best match for an
animated screenpack (signs, rain, glow), but little variety between stages.

## 4. Technical template for every stage (give this to your image tool)

- **Canvas**: paint each stage as a panorama at **2× size**: height 1100 px,
  width 2 × stage width (versus: 2400–3200 px; stage mode: 4000–6000 px).
- **Camera rows (in game pixels, 550 high)**: top 0–128 under the HP panel
  (plain sky/ceiling); horizon around row 230–260; floor's back edge around row
  300; front edge 550. These keep the walkable band about the same everywhere.
- **Depth bands**: paint so the picture splits cleanly into horizontal bands,
  which I cut into parallax layers: sky (still or slow) / far (skyline,
  mountains) / mid (buildings, trees, railing) / floor. Things that cross a
  band line (a tall lamp post) are better as separate props.
- **Foreground props** (optional): separate PNGs with transparency (a post, a
  crate, hanging cables) that scroll faster in front of the fighters. Keep them
  at the screen edges so they never hide a fight.
- **Animated bits**: 2–4 frames each, same size and position, transparent
  background (a flag, a sign on/off, water glints). Or tell me what should move
  and I'll make it from the painting (blinks, shimmer and drifting clouds are
  easy for me to generate).
- **No pure black**, no text that must be read (it shrinks), no characters
  painted into the scene.

What I do with it: cut the layers, set each layer's scroll speed, convert to
8-bit, set the floor band, add the animation timers, wire up music, and test
it headless with fighters at both floor edges (as for Urban Bridge). A new tool
(`tools/build_stage.py`, the layered successor of `image_to_stage.py`) will make
that repeatable.

## 5. Stage mode (after the stages exist)

LF2's stage mode is 5 stages of increasing waves with bosses, plus survival.
Ours: the journey through the chosen concept's stages, waves of grunts
(restyled Bandit and Hunter, more later), and our fighters as stage bosses,
with a phase's music changing at the boss. We write our own stage file
(enemies, counts, HP, boss flags, scroll bounds) and a mod hook that loads it
instead of `data/stage.dat`.

## 6. Screenpack (title, menus, HUD)

Same art direction as the stages, built after the concept is fixed:

1. **Title / main menu**: a DoD Fighter logo and an animated backdrop (a
   skyline from the chosen concept with drifting clouds or blinking lights),
   with your menu music.
2. **Character select**: frame and background in the same palette.
3. **In-game HUD**: the HP/MP panel restyled.
4. **Score board, pause and loading screens**.

Send the logo as a PNG with transparency, as large as you have it.

## 7. Order of work

1. Pick the concept (A/B/C), or change it.
2. **Pilot stage**: you send one panorama (and props/animated bits if you
   have them); I build `build_stage.py` around it and we tune it until it
   looks right in game. This locks the template for the rest.
3. The remaining versus stages, one by one, with your music as it arrives.
4. Stage mode file and grunts.
5. Screenpack: logo and title first, then select, HUD, score board.
