# DoD Fighter — DarthNox

An original character for [OpenLF2](https://github.com/OpenLF2/OpenLF2), the
MIT-licensed reimplementation of Little Fighter 2.

Drop `mods/darthnox` into an OpenLF2 checkout and launch with:

```
openlf2 --mod mods/darthnox
```

DarthNox appears in the Versus picker as record ID 61.

## Status

A musketeer with idle, walk, run, two sword attacks and a jump. The art set is deliberately
incomplete — see *Incremental art* below for why that still produces a fully
playable fighter.

| | |
|---|---|
| Authored | sprite sheet, portraits, movement speeds, standing (0–3), walking (5–8), running (9–11), attacks (60–62, 65–67), super attack (70–73), jump attack (80–82), run attack (85–88), jump (210–212, 215) |
| Inherited | every other frame's mechanics — states, `itr`/`bdy` boxes, next-wiring, catches, falls |

## Incremental art

A complete LF2 character needs roughly 214 frames. Rather than block on that,
`object_data.lua` inherits a base fighter's entire frame table and overrides
only the sprites and centres. Unauthored frames fall back to a held idle pose,
so the character is playable with a fraction of the art done.

Add frames to `assets/darthnox.txt` and they stop falling back automatically —
no Lua changes required.

## Sprite conventions

- `assets/darthnox.bmp` — 344×522, 24 cells of 85×86 with 1px gutters, `row: 4  col: 6`
  (idle, walk, run, slash, thrust, jump)
- `assets/portrait_f.bmp` 120×120 (`head:`), `assets/portrait_s.bmp` 40×45 (`small:`)
- 8-bit indexed, uncompressed, bottom-up `BITMAPINFOHEADER`
- **Palette index 0 is pure black and reserved for transparency.** OpenLF2 keys
  on RGB(0,0,0) via `SDL_SetColorKey`, so any opaque pixel that would quantise
  to pure black is lifted to (8,8,8). DarthNox's near-black cape and hat make
  this necessary — without it, parts of him render as holes.
- `centerx: 39  centery: 85` — AutoSprite's foot pivot, shared by every frame

## Scale

Built at 1× (LF2 native). `scripts/base/game/constants.lua` in OpenLF2 sets the
world to 794×550 and upscales for display, so sprites are authored in 79-unit
space. 316px masters are kept outside this repo; the 4K path would mean raising
those constants and replacing the base game's own 794-scale backgrounds.

## Animation notes

Art comes from AutoSprite (character "DarthNox LF2 v4"): 16-frame idle, walk
and run clips at 256px, 4 frames each. Walk and run start from the idle's
"Idle Lock" pose so the head never changes size (see `STYLE.md`). At `wait: 3` a
4-frame cycle runs 12 ticks. `tools/autosprite_to_lf2.py` does the conversion —
foot-pivot registration, uniform downscale, 255-colour palette with index 0
kept for the colour key, and 1px cell gutters.

## Licence

Code and data here: MIT. This repository contains no Little Fighter 2 assets;
OpenLF2 requires your own copy of the original installer.
