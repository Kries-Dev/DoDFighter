# DarthNox

`--mod mods/darthnox` adds **DarthNox** (record ID 61) to the character picker.

A musketeer with a 4-frame walk cycle, generated with AutoSprite and processed
through the project's slicer.

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

- `darthnox.bmp` — 404×75, 4 cells of 100×74, laid out 4 across × 1 down.
  Stock fighters use 79×79 cells and stand ~73px tall. DarthNox's 67×59 export
  was ~80% of stock height and slim for LF2's stocky style, so it is scaled
  ×1.25 tall and ×1.5 wide (`SCALE_Y` / `SCALE_X` in `tools/resize_darthnox.py`).
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
- `centerx: 39  centery: 73` — hip-centroid/ground-line registration, scaled with the art

## Portraits

LF2 uses two different images, and they must be different sizes:

| key | file | size | where |
|---|---|---|---|
| `head:` | `portrait_f.bmp` | 120×120 | character picker |
| `small:` | `portrait_s.bmp` | 40×45 | in-match HUD, beside the HP/MP bars |

Pointing both at one 80×80 image makes the HUD icon spill over the bars.
`portrait.bmp` (80×80) is kept as the source both are built from.

## Scale

Built at 1× (LF2 native). `scripts/base/game/constants.lua` sets the world to
794×550 and upscales for display, so sprites must be authored in 79-unit space.
The 316px masters are kept upstream; see the pipeline notes for the 4K question.

## Rebuilding

```
python3 build_darthnox.py      # slicer -> registration -> BMP -> this folder
```

`build_darthnox.py` lives upstream with the 316px masters. Until the sheet is
re-exported from those at the new size, `tools/resize_darthnox.py` rescales the
existing 1× art (supersampled, mapped back onto the same palette, index 0 kept
transparent) and builds both portraits:

```
python tools/resize_darthnox.py <67x59 sheet>.bmp mods/darthnox/assets/portrait.bmp <out dir>
```

Re-exporting from the masters at 100×74 will be sharper than this upscale.
