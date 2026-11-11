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

- `darthnox.bmp` — 268×59, 4 cells of 67×59, laid out 4 across × 1 down
- **`row:` and `col:` are named backwards in the LF2 format.** `row:` is the
  number of pictures *per row* (columns) and `col:` is the number of rows —
  `object_data.cpp` reads them that way (`sheet.columns = require(..., "row:")`).
  A 4-across strip is therefore `row: 4  col: 1`. Getting it the wrong way round
  fails with `sprite rectangle outside texture`.
- 8-bit indexed, uncompressed, bottom-up BITMAPINFOHEADER
- **Palette index 0 is pure black and reserved for transparency.** OpenLF2 keys
  on RGB(0,0,0) via `SDL_SetColorKey`, so the exporter lifts any opaque pixel
  that would quantise to pure black up to (8,8,8). DarthNox's near-black cape
  and hat make this necessary — without it, parts of him render as holes.
- `centerx: 26  centery: 58` — from hip-centroid/ground-line registration

## Scale

Built at 1× (LF2 native). `scripts/base/game/constants.lua` sets the world to
794×550 and upscales for display, so sprites must be authored in 79-unit space.
The 316px masters are kept upstream; see the pipeline notes for the 4K question.

## Rebuilding

```
python3 build_darthnox.py      # slicer -> registration -> BMP -> this folder
```
