#!/usr/bin/env python3
"""Rescale DarthNox's 8-bit LF2 art without third-party libraries.

    python tools/resize_darthnox.py SRC_SHEET.bmp SRC_PORTRAIT.bmp OUT_DIR

Writes into OUT_DIR:
  darthnox.bmp    sprite sheet scaled by SCALE, 1px gutter after every cell
  portrait_f.bmp  120x120 'head:' image (character picker)
  portrait_s.bmp  40x45   'small:' image (in-match HUD)
and prints the w/h/centerx/centery values to put in darthnox.txt.

Engine rules this preserves (see mods/darthnox/README.md):
  * cell (c, r) lives at x = c*(w+1), y = r*(h+1)            -> gutters
  * pure black RGB(0,0,0) is the transparent colour key       -> index 0 only
  * opaque pixels never map to pure black                     -> palette 1..255

Resampling: 4x4 supersampled bilinear on premultiplied colour, so edges
blend instead of staircasing; result is mapped back to the source palette.
"""
import struct, sys, os

SCALE = 1.25            # stock fighters stand ~73px tall; DarthNox's art is 59px
SRC_CELL = (67, 59)     # source cell size (tightly packed or guttered both work)
SRC_COLUMNS = 4
SRC_CENTER = (26, 58)   # centerx / centery of the source art
HEAD_SIZE = (120, 120)
SMALL_SIZE = (40, 45)
SMALL_CROP = (20, 6, 80, 74)   # face box in the 80x80 portrait (x0, y0, x1, y1), 40:45 aspect


def read_bmp(path):
    d = open(path, 'rb').read()
    off = struct.unpack_from('<I', d, 10)[0]
    hs, W, H, _, bpp, comp = struct.unpack_from('<IiiHHI', d, 14)
    assert bpp == 8 and comp == 0, f'{path}: need 8-bit uncompressed, got {bpp}/{comp}'
    ncol = struct.unpack_from('<I', d, 46)[0] or 256
    pal = [tuple(d[14 + hs + i * 4: 14 + hs + i * 4 + 3][::-1]) for i in range(ncol)]
    stride = (W + 3) & ~3
    flip, H = H > 0, abs(H)
    rows = [list(d[off + ((H - 1 - y) if flip else y) * stride:][:W]) for y in range(H)]
    return W, H, pal, rows


def write_bmp(path, W, H, pal, rows):
    pal = list(pal) + [(0, 0, 0)] * (256 - len(pal))
    stride = (W + 3) & ~3
    pixels = b''.join(bytes(rows[H - 1 - y]) + b'\0' * (stride - W) for y in range(H))
    palb = b''.join(bytes((b, g, r, 0)) for r, g, b in pal[:256])
    off = 14 + 40 + len(palb)
    out = b'BM' + struct.pack('<IHHI', off + len(pixels), 0, 0, off)
    out += struct.pack('<IiiHHIIiiII', 40, W, H, 1, 8, 0, len(pixels), 2835, 2835, 256, 0)
    open(path, 'wb').write(out + palb + pixels)


def to_rgba(pal, rows):
    """Palette rows -> float RGBA rows, pure black = transparent."""
    out = []
    for row in rows:
        r2 = []
        for i in row:
            c = pal[i]
            r2.append((0.0, 0.0, 0.0, 0.0) if c == (0, 0, 0) else (c[0], c[1], c[2], 1.0))
        out.append(r2)
    return out


def resample(img, sx0, sy0, sw, sh, dw, dh, ss=4):
    """Area of img (sx0, sy0, sw, sh) -> dw x dh, premultiplied bilinear, ss x ss supersampling."""
    H, W = len(img), len(img[0])

    def px(x, y):
        if x < 0 or y < 0 or x >= W or y >= H:
            return (0.0, 0.0, 0.0, 0.0)
        r, g, b, a = img[y][x]
        return (r * a, g * a, b * a, a)

    def bilinear(fx, fy):
        x0, y0 = int(fx // 1), int(fy // 1)
        tx, ty = fx - x0, fy - y0
        acc = [0.0] * 4
        for (xx, yy, w) in ((x0, y0, (1 - tx) * (1 - ty)), (x0 + 1, y0, tx * (1 - ty)),
                            (x0, y0 + 1, (1 - tx) * ty), (x0 + 1, y0 + 1, tx * ty)):
            if w:
                p = px(xx, yy)
                for k in range(4):
                    acc[k] += p[k] * w
        return acc

    out = []
    kx, ky = sw / dw, sh / dh
    for y in range(dh):
        row = []
        for x in range(dw):
            acc = [0.0] * 4
            for j in range(ss):
                for i in range(ss):
                    # sample positions in source pixel-centre space
                    fx = sx0 + (x + (i + 0.5) / ss) * kx - 0.5
                    fy = sy0 + (y + (j + 0.5) / ss) * ky - 0.5
                    p = bilinear(fx, fy)
                    for k in range(4):
                        acc[k] += p[k]
            n = ss * ss
            a = acc[3] / n
            if a > 0:
                row.append((acc[0] / n / a, acc[1] / n / a, acc[2] / n / a, a))
            else:
                row.append((0.0, 0.0, 0.0, 0.0))
        out.append(row)
    return out


def quantise(img, pal, alpha_cut=0.5):
    """RGBA -> palette indices. Transparent -> 0; opaque -> nearest of indices 1..255."""
    candidates = [(i, c) for i, c in enumerate(pal) if i > 0 and c != (0, 0, 0)]
    cache = {}
    rows = []
    for row in img:
        r2 = []
        for (r, g, b, a) in row:
            if a < alpha_cut:
                r2.append(0)
                continue
            key = (int(r), int(g), int(b))
            if key not in cache:
                cache[key] = min(candidates, key=lambda ic: (ic[1][0] - key[0]) ** 2 * 3
                                 + (ic[1][1] - key[1]) ** 2 * 4 + (ic[1][2] - key[2]) ** 2 * 2)[0]
            r2.append(cache[key])
        rows.append(r2)
    return rows


def main(src_sheet, src_portrait, out_dir):
    os.makedirs(out_dir, exist_ok=True)

    # --- sprite sheet -------------------------------------------------------
    W, H, pal, rows = read_bmp(src_sheet)
    cw, ch = SRC_CELL
    pitch = cw + 1 if W >= SRC_COLUMNS * (cw + 1) - 1 else cw   # accept guttered or packed input
    rgba = to_rgba(pal, rows)
    nw, nh = round(cw * SCALE), round(ch * SCALE)
    sheet_w, sheet_h = SRC_COLUMNS * (nw + 1), nh + 1
    sheet = [[0] * sheet_w for _ in range(sheet_h)]
    bottom = 0
    for c in range(SRC_COLUMNS):
        cell = quantise(resample(rgba, c * pitch, 0, cw, ch, nw, nh), pal)
        for y in range(nh):
            sheet[y][c * (nw + 1): c * (nw + 1) + nw] = cell[y]
            if any(cell[y]):
                bottom = max(bottom, y)
    write_bmp(os.path.join(out_dir, 'darthnox.bmp'), sheet_w, sheet_h, pal, sheet)

    # --- portraits ----------------------------------------------------------
    PW, PH, ppal, prows = read_bmp(src_portrait)
    prgba = to_rgba(ppal, prows)
    head = quantise(resample(prgba, 0, 0, PW, PH, *HEAD_SIZE), ppal)
    write_bmp(os.path.join(out_dir, 'portrait_f.bmp'), *HEAD_SIZE, ppal, head)
    x0, y0, x1, y1 = SMALL_CROP
    small = quantise(resample(prgba, x0, y0, x1 - x0, y1 - y0, *SMALL_SIZE), ppal)
    write_bmp(os.path.join(out_dir, 'portrait_s.bmp'), *SMALL_SIZE, ppal, small)

    cx = round(SRC_CENTER[0] * SCALE)
    cy = round((SRC_CENTER[1] + 0.5) * SCALE - 0.5)
    print(f'sheet {sheet_w}x{sheet_h}  cells {nw}x{nh}  lowest opaque row {bottom}')
    print(f'darthnox.txt:  w: {nw}  h: {nh}  row: {SRC_COLUMNS}  col: 1   centerx: {cx}  centery: {cy}')


if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
