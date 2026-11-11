# DoD Fighter — DarthNox

An original character for [OpenLF2](https://github.com/OpenLF2/OpenLF2), the
MIT-licensed reimplementation of Little Fighter 2.

Drop `mods/darthnox` into an OpenLF2 checkout and launch with:

```
openlf2 --mod mods/darthnox
```

DarthNox appears in the Versus picker as record ID 61.

## Status

A musketeer with a 4-frame idle and a 4-frame walk. The art set is deliberately
incomplete — see *Incremental art* below for why that still produces a fully
playable fighter.

| | |
|---|---|
| Authored | sprite sheet, portrait, movement speeds, standing (0–3), walking (5–8), running (9–11) |
| Inherited | every other frame's mechanics — states, `itr`/`bdy` boxes, next-wiring, catches, falls |

## Incremental art

A complete LF2 character needs roughly 214 frames. Rather than block on that,
`object_data.lua` inherits a base fighter's entire frame table and overrides
only the sprites and centres. Unauthored frames fall back to a held idle pose,
so the character is playable with a fraction of the art done.

Add frames to `assets/darthnox.txt` and they stop falling back automatically —
no Lua changes required.

## Sprite conventions

- `assets/darthnox.bmp` — 276×150, eight 68×74 cells with 1px gutters, `row: 4  col: 2`
  (pictures 0–3 idle, 4–7 walk)
- `assets/portrait_f.bmp` 120×120 (`head:`), `assets/portrait_s.bmp` 40×45 (`small:`)
- 8-bit indexed, uncompressed, bottom-up `BITMAPINFOHEADER`
- **Palette index 0 is pure black and reserved for transparency.** OpenLF2 keys
  on RGB(0,0,0) via `SDL_SetColorKey`, so any opaque pixel that would quantise
  to pure black is lifted to (8,8,8). DarthNox's near-black cape and hat make
  this necessary — without it, parts of him render as holes.
- `centerx: 27  centery: 74` — AutoSprite's foot pivot, shared by every frame

## Scale

Built at 1× (LF2 native). `scripts/base/game/constants.lua` in OpenLF2 sets the
world to 794×550 and upscales for display, so sprites are authored in 79-unit
space. 316px masters are kept outside this repo; the 4K path would mean raising
those constants and replacing the base game's own 794-scale backgrounds.

## Animation notes

Art comes from AutoSprite (character "DarthNox LF2 v3"): 16-frame idle and walk
clips at 256px, of which 4 evenly spaced frames each are used. At `wait: 3` a
4-frame cycle runs 12 ticks. `tools/autosprite_to_lf2.py` does the conversion —
foot-pivot registration, uniform downscale, 255-colour palette with index 0
kept for the colour key, and 1px cell gutters.

## Licence

Code and data here: MIT. This repository contains no Little Fighter 2 assets;
OpenLF2 requires your own copy of the original installer.
