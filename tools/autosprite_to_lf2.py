#!/usr/bin/env python3
"""Turn AutoSprite RGBA spritesheets into one 8-bit LF2/OpenLF2 sprite sheet.

    python tools/autosprite_to_lf2.py OUT_DIR HEIGHT ROW_SPEC [ROW_SPEC ...]

ROW_SPEC is  SHEET.png,ATLAS.json,N[,FIRST,LAST]  -- take N evenly spaced frames
from that AutoSprite sheet as one row of the output. FIRST/LAST (inclusive,
0-based) limit the pick to part of the clip -- e.g. 2,13 to skip the standing
frames a pose-anchored loop starts and ends on. Example (idle, walk, run rows):

    python tools/autosprite_to_lf2.py out 82 idle.png,idle.json,4 walk.png,walk.json,4 run.png,run.json,4,2,13

N may instead be @A/B/C -- exactly those clip frames (0-based), e.g. the
wind-up, strike and follow-through of an attack: slash.png,slash.json,@3/6/9

A trailing ,ground on a ROW_SPEC stands every frame of that row on its own
lowest pixel instead of the clip's foot pivot -- for jumps, where the clip lifts
the character but the engine already does that.

A trailing ,trail draws two dithered afterimages of the whole body behind the
character (for dashes and lunges); ,blades draws ghost copies of the sword arm
above and below it (for rapid stabs, like Davis's many-punch). LF2 sprites have
no alpha, so the ghosts are a checkerboard of tinted pixels, which reads as
see-through at game size. Flags can be combined: ...,@3/4/8,trail

HEIGHT may instead be sNUMBER -- a fixed scale (e.g. s0.3460) instead of
"tallest frame = HEIGHT px". Use it once the size is approved, so a raised
sword or a jump can't shrink the whole character.

Writes OUT_DIR/darthnox.bmp and prints the darthnox.txt header values
(w, h, row:, col:, centerx, centery). Pictures are numbered row by row:
row 0 = pictures 0..N-1, row 1 = N..2N-1, and so on.

What it guarantees (see mods/darthnox/README.md for why each matters):
  * every frame is registered on AutoSprite's foot pivot, so one
    centerx/centery is correct for all pictures
  * HEIGHT is the tallest selected frame's height in game pixels; one uniform
    scale is used for every frame so nothing changes size between frames
  * 1px gutter after every cell (OpenLF2 reads cell c at x = c*(w+1))
  * palette index 0 = pure black = transparent; no opaque pixel is pure black
No third-party libraries: PNG decode, resample and quantise are all here.
"""
import json, math, struct, sys, zlib


# ---------------------------------------------------------------- PNG / BMP --
def read_png(path):
    data = open(path, 'rb').read()
    assert data[:8] == b'\x89PNG\r\n\x1a\n', path
    pos, idat, ihdr, plte, trns = 8, b'', None, None, None
    while pos < len(data):
        n, = struct.unpack('>I', data[pos:pos + 4])
        kind, body = data[pos + 4:pos + 8], data[pos + 8:pos + 8 + n]
        pos += 12 + n
        if kind == b'IHDR': ihdr = struct.unpack('>IIBBBBB', body)
        elif kind == b'PLTE': plte = body
        elif kind == b'tRNS': trns = body
        elif kind == b'IDAT': idat += body
    W, H, depth, ctype, _, _, interlace = ihdr
    assert depth == 8 and interlace == 0, f'{path}: need 8-bit non-interlaced PNG'
    bpp = {6: 4, 2: 3, 0: 1, 4: 2, 3: 1}[ctype]
    raw, stride = zlib.decompress(idat), W * bpp
    out, prev, i = [], bytearray(stride), 0
    for _ in range(H):
        f = raw[i]; line = bytearray(raw[i + 1:i + 1 + stride]); i += 1 + stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0
            b = prev[x]; c = prev[x - bpp] if x >= bpp else 0
            if f == 1: line[x] = (line[x] + a) & 255
            elif f == 2: line[x] = (line[x] + b) & 255
            elif f == 3: line[x] = (line[x] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c; pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        out.append(line); prev = line
    def px(row, x):
        if ctype == 6: return tuple(row[x * 4:x * 4 + 4])
        if ctype == 2: return tuple(row[x * 3:x * 3 + 3]) + (255,)
        if ctype == 0: v = row[x]; return (v, v, v, 255)
        if ctype == 4: v = row[x * 2]; return (v, v, v, row[x * 2 + 1])
        idx = row[x]; r, g, b = plte[idx * 3:idx * 3 + 3]
        return (r, g, b, trns[idx] if trns and idx < len(trns) else 255)
    return W, H, [[px(r, x) for x in range(W)] for r in out]


def write_bmp(path, W, H, pal, rows):
    pal = list(pal) + [(0, 0, 0)] * (256 - len(pal))
    stride = (W + 3) & ~3
    pixels = b''.join(bytes(rows[H - 1 - y]) + b'\0' * (stride - W) for y in range(H))
    palb = b''.join(bytes((b, g, r, 0)) for r, g, b in pal[:256])
    off = 14 + 40 + len(palb)
    out = b'BM' + struct.pack('<IHHI', off + len(pixels), 0, 0, off)
    out += struct.pack('<IiiHHIIiiII', 40, W, H, 1, 8, 0, len(pixels), 2835, 2835, 256, 0)
    open(path, 'wb').write(out + palb + pixels)


# --------------------------------------------------------------- resampling --
def area_resample(img, x0, y0, w, h, scale, ow, oh, clip=None):
    """Box-filter img region starting at (x0, y0) by `scale` (<1) into ow x oh.
    Premultiplied alpha so transparent pixels don't darken edges. clip =
    (x0, y0, x1, y1): source pixels outside it count as transparent (keeps a
    neighbouring frame of the source sheet out of a widened cell)."""
    H, W = len(img), len(img[0])
    if clip:
        cx0, cy0, cx1, cy1 = clip
    else:
        cx0, cy0, cx1, cy1 = 0, 0, W, H
    inv = 1.0 / scale
    out = []
    for oy in range(oh):
        sy0, sy1 = y0 + oy * inv, y0 + (oy + 1) * inv
        row = []
        for ox in range(ow):
            sx0, sx1 = x0 + ox * inv, x0 + (ox + 1) * inv
            acc = [0.0, 0.0, 0.0, 0.0]; area = 0.0
            for yy in range(int(math.floor(sy0)), int(math.ceil(sy1))):
                wy = min(sy1, yy + 1) - max(sy0, yy)
                if wy <= 0: continue
                for xx in range(int(math.floor(sx0)), int(math.ceil(sx1))):
                    wx = min(sx1, xx + 1) - max(sx0, xx)
                    if wx <= 0: continue
                    wgt = wx * wy; area += wgt
                    if cx0 <= xx < cx1 and cy0 <= yy < cy1:
                        r, g, b, a = img[yy][xx]; a /= 255.0
                        acc[0] += r * a * wgt; acc[1] += g * a * wgt; acc[2] += b * a * wgt; acc[3] += a * wgt
            a = acc[3] / area if area else 0.0
            row.append((acc[0] / acc[3], acc[1] / acc[3], acc[2] / acc[3], a) if acc[3] > 0 else (0, 0, 0, 0.0))
        out.append(row)
    return out


# --------------------------------------------------------------- quantising --
def median_cut(colours, n):
    boxes = [colours]
    while len(boxes) < n:
        boxes.sort(key=lambda b: -len(b))
        split = None
        for i, b in enumerate(boxes):
            if len(b) < 2: continue
            ranges = [max(c[k] for c in b) - min(c[k] for c in b) for k in range(3)]
            if max(ranges) == 0: continue
            split = i; break
        if split is None: break
        b = boxes.pop(split)
        ranges = [max(c[k] for c in b) - min(c[k] for c in b) for k in range(3)]
        k = ranges.index(max(ranges))
        b.sort(key=lambda c: c[k]); m = len(b) // 2
        boxes += [b[:m], b[m:]]
    pal = []
    for b in boxes:
        r = round(sum(c[0] for c in b) / len(b)); g = round(sum(c[1] for c in b) / len(b)); bl = round(sum(c[2] for c in b) / len(b))
        if (r, g, bl) == (0, 0, 0) or max(r, g, bl) < 8: r, g, bl = max(r, 8), max(g, 8), max(bl, 8)
        pal.append((r, g, bl))
    return pal


def nearest(pal, c, cache):
    if c not in cache:
        cache[c] = 1 + min(range(len(pal)), key=lambda i: (pal[i][0] - c[0]) ** 2 * 3 + (pal[i][1] - c[1]) ** 2 * 4 + (pal[i][2] - c[2]) ** 2 * 2)
    return cache[c]


# -------------------------------------------------------------- afterimages --
TRAIL_REACH = 27                    # game px the farthest afterimage sits behind
GHOST_TINT = (110, 175, 255)        # blue, mixed 60/40 into the ghost so it reads as an echo
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]   # ordered-dither thresholds


def ghost(cell, offsets, front_of=None, band=None, cover=None):
    """Draw dithered copies of the cell's opaque pixels shifted by each (dx, dy),
    under the original, nearest copy first. cover: share of pixels kept per copy
    (default fades 0.75, 0.5, 0.25 with distance). front_of / band: only copy
    pixels right of that x and between those rows (the sword arm, not the hat)."""
    h, w = len(cell), len(cell[0])
    src = [row[:] for row in cell]
    cover = cover or [0.75, 0.5, 0.25, 0.25][:len(offsets)]
    for n, (dx, dy) in enumerate(offsets):
        for y in range(h):
            for x in range(w):
                if BAYER[y % 4][x % 4] >= cover[n] * 16:
                    continue
                sx, sy = x - dx, y - dy
                if not (0 <= sx < w and 0 <= sy < h) or (front_of is not None and sx < front_of):
                    continue
                if band and not band[0] <= sy <= band[1]:
                    continue
                r, g, b, a = src[sy][sx]
                if a < 0.5 or cell[y][x][3] >= 0.5:
                    continue
                cell[y][x] = (r * .4 + GHOST_TINT[0] * .6, g * .4 + GHOST_TINT[1] * .6, b * .4 + GHOST_TINT[2] * .6, 1.0)


# ------------------------------------------------------------------- main ----
def main(out_dir, height, specs):
    import os
    os.makedirs(out_dir, exist_ok=True)
    fixed_scale = float(height[1:]) if height.startswith('s') else None
    height = None if fixed_scale else int(height)
    rows_in = []   # per output row: list of (img, cell, trim, pivot_px)
    row_flags = []
    for spec in specs:
        parts = spec.split(',')
        flags = set()
        while parts[-1] in ('ground', 'trail', 'blades'):
            flags.add(parts.pop())
        ground = 'ground' in flags
        png, atlas, n = parts[0], parts[1], parts[2]
        span = (int(parts[3]), int(parts[4])) if len(parts) == 5 else None
        explicit = [int(v) for v in n[1:].split('/')] if n.startswith('@') else None
        W, H, img = read_png(png)
        meta = json.load(open(atlas))
        frames = meta['frames']
        keys = sorted(frames, key=lambda k: int(k))
        fs = meta['meta'].get('frame_size') or frames[keys[0]]['w']
        piv = meta['meta'].get('pivot') or {'x': 0.5, 'y': 0.95}
        if explicit:
            pick = [keys[i] for i in explicit]
        else:
            n = int(n)
            if span:
                keys = keys[span[0]:span[1] + 1]
            pick = [keys[round(i * len(keys) / n) % len(keys)] for i in range(n)]
        row = []
        for k in pick:
            f = frames[k]
            cell = (f['x'], f['y'], f['w'], f['h']) if 'x' in f else (f['frame']['x'], f['frame']['y'], f['frame']['w'], f['frame']['h'])
            # visible box inside the cell, from alpha
            x0, y0, w, h = cell
            ys = [y for y in range(h) if any(img[y0 + y][x0 + x][3] > 32 for x in range(w))]
            xs = [x for x in range(w) if any(img[y0 + y][x0 + x][3] > 32 for y in ys)]
            trim = (xs[0], ys[0], xs[-1] + 1, ys[-1] + 1)
            # ground: stand this frame on its own lowest pixel, so a clip that
            # moves the character up (a jump) doesn't add to the engine's own
            # jump height.
            foot_y = trim[3] if ground else piv['y'] * h
            row.append((img, cell, trim, (piv['x'] * w, foot_y)))
        rows_in.append(row)
        row_flags.append(flags)

    # One registration box (relative to pivot) that holds every selected frame.
    L = min(t[0] - p[0] for r in rows_in for (_, _, t, p) in r)
    T = min(t[1] - p[1] for r in rows_in for (_, _, t, p) in r)
    R = max(t[2] - p[0] for r in rows_in for (_, _, t, p) in r)
    B = max(t[3] - p[1] for r in rows_in for (_, _, t, p) in r)
    tallest = max(t[3] - t[1] for r in rows_in for (_, _, t, p) in r)
    scale = fixed_scale or height / tallest
    if any('trail' in f for f in row_flags):
        L -= TRAIL_REACH / scale       # room for the afterimages behind the body
    cw, ch = math.ceil((R - L) * scale), math.ceil((B - T) * scale)
    centerx, centery = round(-L * scale), round(-T * scale)

    cells = []
    for r in rows_in:
        out_row = []
        for img, (x0, y0, w, h), trim, (px, py) in r:
            out_row.append(area_resample(img, x0 + px + L, y0 + py + T, w, h, scale, cw, ch, clip=(x0, y0, x0 + w, y0 + h)))
        cells.append(out_row)
    for ri, flags in enumerate(row_flags):
        for cell in cells[ri]:
            if 'trail' in flags: ghost(cell, [(-9, 0), (-18, 0), (-TRAIL_REACH, 0)])
            if 'blades' in flags: ghost(cell, [(-3, -11), (-5, 10), (-2, -20), (-6, 18)], front_of=centerx + 6,
                                        band=(centery - 56, centery - 14), cover=[0.75, 0.75, 0.5, 0.5])

    opaque = [(int(c[0]), int(c[1]), int(c[2])) for row in cells for cell in row for line in cell for c in line if c[3] >= 0.5]
    pal = median_cut(opaque, 255)
    cache = {}
    cols, nrows = max(len(r) for r in cells), len(cells)
    SW, SH = cols * (cw + 1), nrows * (ch + 1)
    sheet = [[0] * SW for _ in range(SH)]
    for ri, row in enumerate(cells):
        for ci, cell in enumerate(row):
            for y in range(ch):
                for x in range(cw):
                    r, g, b, a = cell[y][x]
                    if a >= 0.5:
                        sheet[ri * (ch + 1) + y][ci * (cw + 1) + x] = nearest(pal, (int(r), int(g), int(b)), cache)
    write_bmp(os.path.join(out_dir, 'darthnox.bmp'), SW, SH, [(0, 0, 0)] + pal, sheet)
    print(f'scale s{scale:.6f}  sheet {SW}x{SH}  cells {cw}x{ch}  colours {len(pal)}+key')
    print(f'darthnox.txt:  w: {cw}  h: {ch}  row: {cols}  col: {nrows}   centerx: {centerx}  centery: {centery}')


if __name__ == '__main__':
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
