# DarthNox

`--mod mods/darthnox` adds **DarthNox** (record ID 61) to the character picker.

A musketeer with a 4-frame idle and a 4-frame walk, generated with AutoSprite
(character "DarthNox LF2") and converted with `tools/autosprite_to_lf2.py`.

## What is authored vs inherited

| | |
|---|---|
| Authored | sprite sheet, portrait, movement speeds, standing (0–3), walking (5–8), running (9–11) |
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

- `darthnox.bmp` — 268×154, 8 cells of 66×76, 4 across × 2 down
  (`row: 4  col: 2`). Pictures 0–3 = idle, 4–7 = walk. Stock fighters use
  79×79 cells and stand ~73px tall; the tallest frame here is 74px.
- The art is drawn with LF2-style proportions (large head, broad torso, short
  thick rapier) so it reads at 74px without stretching. The earlier realistic
  design needed a ×1.8 horizontal stretch and its thin rapier vanished at this
  size.
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
- `centerx: 27  centery: 74` — AutoSprite's foot pivot; every frame is registered
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

## Rebuilding

From AutoSprite (download each spritesheet's sheet PNG and atlas JSON):

```
python tools/autosprite_to_lf2.py out 74 idle.png,idle.json,4 walk.png,walk.json,4
python tools/autosprite_portrait.py base.png out 190,40,670,520 340,80,620,395
```

The first prints the `w/h/row/col/centerx/centery` values for `darthnox.txt`.
Add a row (e.g. `run.png,run.json,4`) to extend the sheet; pictures continue
row by row (row 2 = 8–11, ...). The 74 is the tallest frame's height in game
pixels — keep it the same across rebuilds so he doesn't change size.

`tools/resize_darthnox.py` is the older tool that rescaled the first design's
67×59 sheet; it is kept for reference.
