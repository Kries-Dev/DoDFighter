#!/usr/bin/env python3
"""Build a scrolling OpenLF2 stage from one painted panorama, with light animations.

    python tools/build_stage.py PICTURE OUT_DIR KEY "Stage Name" FLOOR_TOP FLOOR_BOTTOM [FLOOR_ROW] [neon=X0,Y0,X1,Y1 ...] [lamps=X0,Y0,X1,Y1 ...] [dim]

PICTURE       the painting (png/webp/jpg), side view, floor across the bottom
OUT_DIR       where KEY.bmp, KEY_*.bmp and KEY.txt go (mods/darthnox/assets/bg)
KEY           short file key; paths must stay under 29 characters ("roof")
FLOOR_TOP     source row of the floor's back edge (where fighters' feet stop)
FLOOR_BOTTOM  source row of the front edge
FLOOR_ROW     screen row the back edge should land on (default 413): this sets
              the scale, so every stage gets about the same floor depth
neon=...      a box in the picture's own pixels holding a neon tube or sign; its
              bright pixels buzz. (Neon is boxed by hand: its colour is often the
              same as the sky's.)
lamps=...     boxes (picture pixels) that hold the lamps; when given, only lights inside
              them flicker (for warm interiors, where sunlit floor patches and walls
              would otherwise be taken for lamps)
dim           a night painting: lamps are found at a lower brightness

The picture is scaled (never stretched) so FLOOR_TOP lands on FLOOR_ROW and the
bottom edge on the screen's bottom (550); the stage is as wide as the scaled
picture and scrolls. Anything above the screen is cropped; the top 128 px sit
under the HP/MP panel.

Light animations are found in the painting itself and written as small
transparent overlay layers that move with the stage:
  * warm lamps (bright yellow-orange blobs): each lamp gets a brighter glow that
    dips now and then, every lamp on its own rhythm, like an old bulb
  * neon (inside the given boxes): goes dark for a few ticks, twice in a row
    (a buzzing tube)
  * small warm specks (lit windows, glints): two sets that softly swap every 1.5 s
LF2 layer timers: a layer is visible on ticks c1..c2 of every cc (30 ticks/s).
Needs Pillow and numpy.
"""
import io, os, sys
import numpy as np
from PIL import Image

SCREEN_W, SCREEN_H, PANEL_H = 794, 550, 128
SHADOW = 'shadow: bg\\sys\\hkc\\s.bmp  shadowsize: 37 9'
PRIMES = (41, 47, 53, 59, 67, 71, 79, 83, 89, 97)


def quantize(rgb, transparent=None):
    """8-bit picture: index 0 = pure black (LF2's key colour), 255 colours for the art."""
    rgb = rgb.copy()
    opaque = np.ones(rgb.shape[:2], bool) if transparent is None else ~transparent
    rgb[opaque & (rgb.max(axis=2) < 8)] = (8, 8, 8)
    px = Image.fromarray(rgb[opaque].reshape(1, -1, 3), 'RGB').quantize(255, method=Image.MEDIANCUT)
    pal = px.getpalette()[:255 * 3]
    full = [0, 0, 0] + pal + [0, 0, 0] * (255 - len(pal) // 3)
    ref = Image.new('P', (1, 1)); ref.putpalette(full)
    idx = np.asarray(Image.fromarray(rgb, 'RGB').quantize(palette=ref, dither=Image.NONE)).copy()
    darkest = 1 + int(np.argmin([sum(full[3 * k:3 * k + 3]) for k in range(1, 256)]))
    idx[opaque & (idx == 0)] = darkest
    idx[~opaque] = 0
    out = Image.fromarray(idx.astype(np.uint8), 'P'); out.putpalette(full)
    return out


def save(img, path):
    buf = io.BytesIO(); img.save(buf, format='BMP')
    with open(path, 'wb') as f:
        f.write(buf.getvalue())


def blobs(mask, min_size):
    """Connected components (4-neighbour) of a boolean mask: list of (ys, xs)."""
    H, W = mask.shape
    seen = np.zeros_like(mask)
    found = []
    for y0, x0 in zip(*np.nonzero(mask)):
        if seen[y0, x0]:
            continue
        stack, ys, xs = [(y0, x0)], [], []
        seen[y0, x0] = True
        while stack:
            y, x = stack.pop()
            ys.append(y); xs.append(x)
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    stack.append((ny, nx))
        if len(ys) >= min_size:
            found.append((np.array(ys), np.array(xs)))
    return found


def grow(mask, r):
    out = mask.copy()
    for _ in range(r):
        m = out.copy()
        m[1:] |= out[:-1]; m[:-1] |= out[1:]; m[:, 1:] |= out[:, :-1]; m[:, :-1] |= out[:, 1:]
        out = m
    return out


def overlay(rgb, region, change, pad=3):
    """A transparent layer covering `region` (grown by pad), its pixels = change(rgb)."""
    ys, xs = np.nonzero(region)
    y0, y1, x0, x1 = max(0, ys.min() - pad), min(rgb.shape[0], ys.max() + pad + 1), max(0, xs.min() - pad), min(rgb.shape[1], xs.max() + pad + 1)
    area = grow(region, pad)[y0:y1, x0:x1]
    patch = change(rgb[y0:y1, x0:x1].astype(float), area)
    patch = np.clip(patch, 0, 255).astype(np.uint8)
    return quantize(patch, transparent=~area), x0, y0


def brighter(amount, warm=(255, 214, 140)):
    def f(px, area):
        out = px + (np.array(warm, float) - px) * amount
        return np.where(area[..., None], out, 0)
    return f


def darker(amount):
    def f(px, area):
        return np.where(area[..., None], px * (1 - amount), 0)
    return f


def build(picture, out_dir, key, name, floor_top, floor_bottom, floor_row=413, neon_boxes=(), dim=False, lamp_boxes=()):
    src = Image.open(picture).convert('RGB')
    W, H = src.size
    scale = (SCREEN_H - floor_row) / (H - floor_top)
    width, height = round(W * scale), round(H * scale)
    top = SCREEN_H - height
    rgb = np.asarray(src.resize((width, height), Image.LANCZOS))
    if top < 0:                                           # crop what is above the screen
        rgb, top = rgb[-top:], 0
    os.makedirs(out_dir, exist_ok=True)
    save(quantize(rgb), os.path.join(out_dir, f'{key}.bmp'))
    near = SCREEN_H - round((H - floor_top) * scale)
    far = SCREEN_H - round((H - floor_bottom) * scale)
    layers = [(f'mods/darthnox/bg/{key}.bmp', 0, width, 0, top, 0, 0, 0, 'the painting')]

    f = rgb.astype(int)
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    if dim:                                               # night: lamps are less bright
        warm = (lum > 170) & (r > 220) & (g > 140) & (b < 190) & (r - b > 70)
    else:
        warm = (lum > 200) & (r > 235) & (g > 170) & (b < 175) & (r - b > 90)
    crop = height - rgb.shape[0]                          # rows cut off above the screen
    if lamp_boxes:                                        # only the marked lamps
        allowed = np.zeros(warm.shape, bool)
        for X0, Y0, X1, Y1 in lamp_boxes:
            allowed[max(0, round(Y0 * scale) - crop):max(0, round(Y1 * scale) - crop), round(X0 * scale):round(X1 * scale)] = True
        warm &= allowed
    neon = np.zeros(warm.shape, bool)
    for X0, Y0, X1, Y1 in neon_boxes:
        x0, x1 = round(X0 * scale), round(X1 * scale)
        y0, y1 = max(0, round(Y0 * scale) - crop), max(0, round(Y1 * scale) - crop)
        box = np.zeros(warm.shape, bool); box[y0:y1, x0:x1] = True
        neon |= box & (lum > 150) & (r > 190) & (b > 140)
    found = []
    # nearby lamp pixels (a lantern and its glow, a light and its reflection) form one lamp
    lamps = []
    for ys, xs in blobs(grow(warm, 3), 6):
        region = np.zeros(warm.shape, bool); region[ys, xs] = True
        region &= warm
        if region.sum() >= 6:
            lamps.append(np.nonzero(region))
    lamps.sort(key=lambda bl: bl[1].min())
    small = [bl for bl in lamps if len(bl[0]) < 40]
    big = [bl for bl in lamps if len(bl[0]) >= 40]
    # warm lamps: a brighter glow that dips now and then, each on its own rhythm
    for k, (ys, xs) in enumerate(big):
        region = np.zeros(warm.shape, bool); region[ys, xs] = True
        img, x0, y0 = overlay(rgb, grow(region, 2), brighter(0.45), pad=3)
        cc = PRIMES[k % len(PRIMES)]
        found.append((img, x0, y0, cc, 0, cc - 5 - (k % 3) * 2, f'lamp {k + 1}'))
    # string lights: small bulbs in two alternating sets
    if small:
        for parity in (0, 1):
            region = np.zeros(warm.shape, bool)
            for ys, xs in small[parity::2]:
                region[ys, xs] = True
            if not region.any():
                continue                                  # only one bulb: no second set
            img, x0, y0 = overlay(rgb, grow(region, 1), brighter(0.35), pad=2)
            found.append((img, x0, y0, 90, parity * 45, parity * 45 + 44, f'small lights {"AB"[parity]}'))
    # neon: dark for a few ticks, twice in a row (a buzzing tube)
    for k, region in enumerate([neon] if neon.any() else []):
        img, x0, y0 = overlay(rgb, grow(region, 2), darker(0.6), pad=3)
        cc = 97 + 10 * k
        found.append((img, x0, y0, cc, 0, 2, f'neon {k + 1} off'))
        found.append((img, x0, y0, cc, 6, 7, f'neon {k + 1} off again'))
    for n, (img, x0, y0, cc, c1, c2, label) in enumerate(found):
        path = f'mods/darthnox/bg/{key}_{n + 1}.bmp'
        assert len(path) <= 29, path
        save(img, os.path.join(out_dir, f'{key}_{n + 1}.bmp'))
        layers.append((path, 1, width, x0, top + y0, cc, c1, c2, label))
    lines = [f'name: {name.replace(" ", "_")}',
             f'width: {width}   zboundary: {near} {far}',
             SHADOW, '',
             f'# Built by tools/build_stage.py from one painted panorama ({W}x{H}, scale {scale:.3f}):',
             '# the painting scrolls with the floor; the small layers are its lights,',
             '# animated with LF2 layer timers (visible on ticks c1..c2 of every cc).']
    for path, transparency, lw, x, y, cc, c1, c2, label in layers:
        lines += [f'# {label}', 'layer:', f'  {path}',
                  f'  transparency: {transparency}  width: {lw}  x: {x}  y: {y}' + (f'  cc: {cc}  c1: {c1}  c2: {c2}' if cc else ''),
                  'layer_end']
    with open(os.path.join(out_dir, f'{key}.txt'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(lines) + '\n')
    print(f'{key}: {width}x{rgb.shape[0]} at y {top}, scale {scale:.3f}, zboundary {near} {far}, '
          f'{len(big)} lamps, {len(small)} bulbs, neon layers {sum(1 for l in found if "neon" in l[6]) // 2}')
    return width, near, far


if __name__ == '__main__':
    dim = 'dim' in sys.argv[1:]
    args = [a for a in sys.argv[1:] if not a.startswith(('neon=', 'lamps=')) and a != 'dim']
    lamp_boxes = [tuple(int(v) for v in a[6:].split(',')) for a in sys.argv[1:] if a.startswith('lamps=')]
    boxes = [tuple(int(v) for v in a[5:].split(',')) for a in sys.argv[1:] if a.startswith('neon=')]
    if len(args) not in (6, 7):
        sys.exit(__doc__)
    build(args[0], args[1], args[2], args[3], int(args[4]), int(args[5]),
          *(int(v) for v in args[6:]), neon_boxes=boxes, dim=dim, lamp_boxes=lamp_boxes)
