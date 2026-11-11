# DoD Fighter — DarthNox

An original character for [OpenLF2](https://github.com/OpenLF2/OpenLF2), the
MIT-licensed reimplementation of Little Fighter 2.

Drop `mods/darthnox` into an OpenLF2 checkout and launch with:

```
openlf2 --mod mods/darthnox
```

DarthNox appears in the Versus picker as record ID 61.

## Status

A musketeer with a working 4-frame walk cycle. The art set is deliberately
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

- `assets/darthnox.bmp` — 404×75, four 100×74 cells with 1px gutters, `row: 4  col: 1`
- `assets/portrait_f.bmp` 120×120 (`head:`), `assets/portrait_s.bmp` 40×45 (`small:`)
- 8-bit indexed, uncompressed, bottom-up `BITMAPINFOHEADER`
- **Palette index 0 is pure black and reserved for transparency.** OpenLF2 keys
  on RGB(0,0,0) via `SDL_SetColorKey`, so any opaque pixel that would quantise
  to pure black is lifted to (8,8,8). DarthNox's near-black cape and hat make
  this necessary — without it, parts of him render as holes.
- `centerx: 26  centery: 58` — from hip-centroid and ground-line registration

## Scale

Built at 1× (LF2 native). `scripts/base/game/constants.lua` in OpenLF2 sets the
world to 794×550 and upscales for display, so sprites are authored in 79-unit
space. 316px masters are kept outside this repo; the 4K path would mean raising
those constants and replacing the base game's own 794-scale backgrounds.

## Animation notes

The walk uses source frames 3, 7, 10 and 15 of a 16-frame AutoSprite sheet,
selected to minimise variance across the cyclic transitions (CV 0.010) rather
than to minimise the seam. Generated motion is rarely truly cyclic; what reads
as smooth is *uniform* steps, not small ones. At `wait: 3` the cycle runs 16
ticks — 0.53s — matching LF2's own walk timing.

## Licence

Code and data here: MIT. This repository contains no Little Fighter 2 assets;
OpenLF2 requires your own copy of the original installer.
