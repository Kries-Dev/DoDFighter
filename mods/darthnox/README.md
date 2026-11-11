# DarthNox

`--mod mods/darthnox` adds **DarthNox** (record ID 61) to the character picker.

A musketeer with idle, walk, run, two sword attacks and a jump, generated with AutoSprite
(character "DarthNox LF2 v4") and converted with `tools/autosprite_to_lf2.py`.

## What is authored vs inherited

| | |
|---|---|
| Authored | sprite sheet, portraits, movement speeds, standing (0–3), walking (5–8), running (9–11), attacks (60–62, 65–67), super attack (70–73), jump attack (80–82), run attack (85–88), jump (210–212, 215) |
| Inherited | every other frame's mechanics — states, `itr`/`bdy` boxes, next-wiring, catches, falls |

Unauthored frames fall back to `IDLE_PICTURE` (see `object_data.lua`), so the
fighter is playable immediately and unfinished actions read as a held pose
rather than a missing sprite. Add frames to `darthnox.txt` and they stop
falling back — no Lua changes needed.

Like the example character, this still needs the player's installer for the
base game's mechanics.

## Why `.txt` and not `.dat`

OpenLF2 decides by file extension whether to decrypt: `read_data_text` in
`src/resources/data_file.cpp` runs *any* path ending in `.dat` through the LF2
cipher unconditionally. Authored mod data is plaintext, so a `.dat` extension
makes the engine decrypt it into garbage and fail with
`NUL or 0x1A byte in data text`.

Keep authored character data as `.txt`. Only genuinely encrypted files from the
original game may use `.dat`.

## Sprite sheet

- `darthnox.bmp` — 344×522, 24 cells of 85×86, 4 across × 6 down (`row: 4  col: 6`).
  Pictures 0–3 idle, 4–7 walk, 8–11 run, 12–14 slash, 16–18 thrust,
  20–22 jump (crouch, rise, air). Stock fighters use
  79×79 cells and stand ~73px tall; DarthNox's tallest frame is 82px because
  the hat and plume sit on top of a head as big as Davis's.
- LF2 proportions are super-deformed: about 3 heads tall, head a third of the
  body, short broad torso, big gloves and boots. Earlier designs at ~5 heads
  (v1/v3) had heads far too small next to Davis, and a slim anime version (v2)
  read as a stick figure. Black hair, clean-shaven.
- Keep the rapier short and thick: a thin blade disappears at 74px, and
  AutoSprite's stock idle/walk dropped v2's thin blade entirely (custom clips
  describing the blade "fully visible in every frame" brought it back).
- **Every cell is followed by a 1px gutter**, like stock LF2 sheets (79px cells
  at an 80px pitch, 10×80 = 800 wide). `scripts/base/game/object_data.lua`
  addresses cell (c, r) at `x = c*(w+1)`, `y = r*(h+1)`, so a sheet must be at
  least `columns*(w+1) - 1` wide. A tightly packed 268px strip puts picture 3 at
  x 204–271, past the edge, and fails with `sprite rectangle outside texture`.
  Gutter pixels are palette index 0 (transparent). Note: `--headless` and
  `--input-trace` runs do not perform this check — only the windowed renderer does.
- **`row:` and `col:` are named backwards in the LF2 format.** `row:` is the
  number of pictures *per row* (columns) and `col:` is the number of rows —
  `object_data.cpp` reads them that way (`sheet.columns = require(..., "row:")`).
  A 4-across strip is therefore `row: 4  col: 1`.
- 8-bit indexed, uncompressed, bottom-up BITMAPINFOHEADER
- **Palette index 0 is pure black and reserved for transparency.** OpenLF2 keys
  on RGB(0,0,0) via `SDL_SetColorKey`, so the exporter lifts any opaque pixel
  that would quantise to pure black up to (8,8,8). DarthNox's near-black cape
  and hat make this necessary — without it, parts of him render as holes.
- `centerx: 39  centery: 85` — AutoSprite's foot pivot; every frame is registered
  on it, so one centre pair is right for all pictures

## Portraits

LF2 uses two different images, and they must be different sizes:

| key | file | size | where |
|---|---|---|---|
| `head:` | `portrait_f.bmp` | 120×120 | character picker |
| `small:` | `portrait_s.bmp` | 40×45 | in-match HUD, beside the HP/MP bars |

Pointing both at one 80×80 image makes the HUD icon spill over the bars.
Both are cropped from the AutoSprite base image by `tools/autosprite_portrait.py`,
on a dark backdrop like the stock faces. `portrait.bmp` is the old design's
80×80 source, kept for `tools/resize_darthnox.py`.

## Scale

Built at 1× (LF2 native). `scripts/base/game/constants.lua` sets the world to
794×550 and upscales for display, so sprites must be authored in 79-unit space.
The 316px masters are kept upstream; see the pipeline notes for the 4K question.

## Style

The look is locked — see `STYLE.md` at the repo root before generating any
new art.

## Rebuilding

From AutoSprite (download each spritesheet's sheet PNG and atlas JSON):

```
python tools/autosprite_to_lf2.py out s0.345992 idle.png,idle.json,4 walk.png,walk.json,4,1,14 run.png,run.json,4,1,4 \n    slash.png,slash.json,@5/6/7 thrust.png,thrust.json,@3/5/12 jump.png,jump.json,@12/9/6,ground
python tools/autosprite_portrait.py base.png out 130,60,730,660 230,170,610,598
```

The first prints the `w/h/row/col/centerx/centery` values for `darthnox.txt`.
Add a row (e.g. `run.png,run.json,4`) to extend the sheet; pictures continue
row by row (row 2 = 8–11, ...). The 82 is the tallest frame's height in game
pixels — keep it the same across rebuilds so he doesn't change size.

`tools/resize_darthnox.py` is the older tool that rescaled the first design's
67×59 sheet; it is kept for reference.
