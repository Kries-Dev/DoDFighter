#!/usr/bin/env python3
"""Turn an edited (often upscaled) picture of an LF2 sprite sheet back into a
game-ready 8-bit sheet. The background may be white or black (found from the
corners); black is best, since edge blending into black reads as outline in game.

    python tools/import_sheet.py EDITED.png|webp OUT.bmp WIDTH HEIGHT [STOCK.bmp]

Used for the user's restyled Bandit (`art/bandit_0_edit.webp` -> bandit_0.bmp,
800 x 560). The edited picture keeps the stock layout (10 x 7 cells of 79 px
with a 1 px gutter) but may be any size and on a light background:

  * the background (near-white pixels connected to the picture's edges) is
    removed; light areas inside a sprite (a white shirt) stay
  * the picture is scaled to WIDTH x HEIGHT with an alpha-weighted box filter,
    then light grey pixels left on the sprite edge (the blend with the white
    background) are peeled off, so there's no white outline in game
  * colours are reduced to 255 (median cut) plus index 0 = pure black, the
    transparent colour; no sprite pixel is pure black
With STOCK.bmp (the stock sheet it redraws) each frame is fitted into its own
79 px cell on top of the stock frame instead: for an edit whose proportions
drifted from the sheet's (the user's bandit_1, 1448x1086), so a plain stretch
would push the lower rows off the grid. Use it whenever the rows don't line up.
Needs Pillow and numpy.
"""
import sys
from collections import deque
import numpy as np
from PIL import Image

BACKGROUND_MIN = 232      # light background: a pixel is background-ish if all channels are at least this
DARK_MAX = 12             # black background: ... if no channel is above this (outlines are darker greys, 16+)
OPAQUE = 0.5              # coverage needed after scaling for a pixel to be drawn
FRINGE_MIN, FRINGE_GREY = 135, 45   # edge pixels this light and this colourless are white-background blend
FRINGE_PASSES = 2                   # peel up to this many pixels of fringe off the sprite edge


def background(img):
    corners = [img[2, 2], img[2, -3], img[-3, 2], img[-3, -3]]
    if max(int(c.max()) for c in corners) <= DARK_MAX:     # drawn on black (LF2's own key colour)
        light = img.max(axis=2) <= DARK_MAX
    else:
        light = img.min(axis=2) >= BACKGROUND_MIN
    H, W = light.shape
    bg = np.zeros((H, W), bool)
    q = deque()
    for x in range(W):
        for y in (0, H - 1):
            if light[y, x] and not bg[y, x]:
                bg[y, x] = True; q.append((y, x))
    for y in range(H):
        for x in (0, W - 1):
            if light[y, x] and not bg[y, x]:
                bg[y, x] = True; q.append((y, x))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W and light[ny, nx] and not bg[ny, nx]:
                bg[ny, nx] = True; q.append((ny, nx))
    return bg


def peel_fringe(rgb, opaque):
    """Drop light, colourless pixels on the sprite edge: the anti-aliasing against
    the white background, which shows as a white outline on a dark stage."""
    lo, hi = rgb.min(axis=2).astype(int), rgb.max(axis=2).astype(int)
    fringe_colour = (lo >= FRINGE_MIN) & (hi - lo <= FRINGE_GREY)
    for _ in range(FRINGE_PASSES):
        clear = ~opaque
        edge = np.zeros_like(opaque)
        edge[1:, :] |= clear[:-1, :]; edge[:-1, :] |= clear[1:, :]
        edge[:, 1:] |= clear[:, :-1]; edge[:, :-1] |= clear[:, 1:]
        drop = opaque & edge & fringe_colour
        if not drop.any():
            break
        opaque = opaque & ~drop
    return opaque


def scale(channel, size):
    return np.asarray(Image.fromarray(channel.astype(np.float32), 'F').resize(size, Image.BOX))


def shrink(img, alpha, size):
    """Alpha-weighted box scaling: returns (rgb uint8, opaque mask), fringe peeled."""
    a = scale(alpha, size)
    rgb = np.stack([scale(img[..., k] * alpha, size) for k in range(3)], axis=2)
    opaque = a >= OPAQUE
    rgb = np.where(opaque[..., None], rgb / np.maximum(a, 1e-6)[..., None], 0)
    rgb = np.clip(np.rint(rgb), 0, 255).astype(np.uint8)
    return rgb, peel_fringe(rgb, opaque)


def bands(fg, count):
    """Split the picture into `count` horizontal bands at the emptiest rows between sprite rows."""
    profile = fg.sum(axis=1).astype(float)
    H = len(profile)
    cuts = [0]
    for k in range(1, count):
        guess = k * H // count
        lo, hi = max(cuts[-1] + 1, guess - H // (2 * count)), min(H - 1, guess + H // (2 * count))
        cuts.append(lo + int(np.argmin(profile[lo:hi])))
    return cuts + [H]


def fit_to_stock(img, alpha, stock_path, cols, rows, cell):
    """Place each edited frame in its cell, lined up on the stock frame: the edited
    picture may not keep the sheet's exact proportions, so rows drift if it is
    simply stretched. Each band x column is scaled uniformly (one scale for the
    whole sheet, chosen to best match the stock frames' size) and shifted to
    overlap the stock frame as much as possible."""
    stock = np.asarray(Image.open(stock_path).convert('RGB'))
    stock_fg = stock.max(axis=2) > 0
    H, W = alpha.shape
    pitch = cell + 1
    out_rgb = np.zeros((rows * pitch, cols * pitch, 3), np.uint8)
    out_op = np.zeros((rows * pitch, cols * pitch), bool)
    ys = bands(alpha > 0, rows)
    colw = W / cols
    cells = []
    for r in range(rows):
        for c in range(cols):
            sm = stock_fg[r * pitch:r * pitch + cell, c * pitch:c * pitch + cell]
            x0, x1 = int(round(c * colw)), int(round((c + 1) * colw))
            sub_a = alpha[ys[r]:ys[r + 1], x0:x1]
            if not sm.any() or not sub_a.any():
                continue
            cells.append((r, c, sm, img[ys[r]:ys[r + 1], x0:x1], sub_a))

    def place(sm, sub_img, sub_a, k):
        h, w = sub_a.shape
        size = (max(1, round(w * k)), max(1, round(h * k)))
        rgb, op = shrink(sub_img, sub_a, size)
        sy, sx = np.nonzero(sm)
        oy, ox = np.nonzero(op)
        if len(oy) == 0:
            return None
        # start from bottom-centre alignment, then search for the best overlap
        by = sy.max() - oy.max()
        bx = int(round((sx.min() + sx.max()) / 2 - (ox.min() + ox.max()) / 2))
        best = (-1, 0, 0)
        for dy in range(by - 8, by + 9):
            for dx in range(bx - 10, bx + 11):
                yy, xx = oy + dy, ox + dx
                ok = (yy >= 0) & (yy < cell) & (xx >= 0) & (xx < cell)
                score = sm[yy[ok], xx[ok]].sum() - 0.5 * (~ok).sum()
                if score > best[0]:
                    best = (score, dy, dx)
        score, dy, dx = best
        union = sm.sum() + len(oy) - max(score, 0)
        return score / max(union, 1), rgb, op, dy, dx

    # one scale for the whole sheet: the one whose frames overlap the stock ones best
    sample = cells[::max(1, len(cells) // 12)]
    best_k, best_iou = None, -1
    for k in np.arange(0.46, 0.62, 0.01):
        iou = np.mean([place(sm, si, sa, k)[0] for _, _, sm, si, sa in sample])
        if iou > best_iou:
            best_k, best_iou = k, iou
    print(f'scale {best_k:.2f} (mean overlap with the stock frames {best_iou:.2f})')
    for r, c, sm, si, sa in cells:
        res = place(sm, si, sa, best_k)
        if res is None:
            continue
        iou, rgb, op, dy, dx = res
        oy, ox = np.nonzero(op)
        yy, xx = oy + dy, ox + dx
        ok = (yy >= 0) & (yy < cell) & (xx >= 0) & (xx < cell)
        Y, X = yy[ok] + r * pitch, xx[ok] + c * pitch
        out_rgb[Y, X] = rgb[oy[ok], ox[ok]]
        out_op[Y, X] = True
        if iou < 0.5:
            print(f'  frame {r * cols + c}: overlap only {iou:.2f}, check it')
    return out_rgb, out_op


def save_sheet(rgb, opaque, out):
    rgb = rgb.copy()
    rgb[opaque & (rgb.max(axis=2) < 8)] = (8, 8, 8)            # pure black is the transparent key
    # 255 colours from the sprite pixels only, then index 0 = transparent black
    pixels = Image.fromarray(rgb[opaque].reshape(1, -1, 3), 'RGB')
    pal_img = pixels.quantize(255, method=Image.MEDIANCUT)
    pal = pal_img.getpalette()[:255 * 3]
    full = [0, 0, 0] + pal + [0, 0, 0] * (256 - 1 - len(pal) // 3)
    ref = Image.new('P', (1, 1)); ref.putpalette(full)
    sheet = Image.fromarray(rgb, 'RGB').quantize(palette=ref, dither=Image.NONE)
    idx = np.asarray(sheet).copy()
    idx[~opaque] = 0
    idx[opaque & (idx == 0)] = 1 + int(np.argmin([sum(full[3 * k:3 * k + 3]) for k in range(1, 256)]))
    outimg = Image.fromarray(idx.astype(np.uint8), 'P'); outimg.putpalette(full)
    outimg.save(out, format='BMP')
    print(f'{out}: {rgb.shape[1]}x{rgb.shape[0]}, {len(set(idx[opaque].tolist()))} colours + transparent')


def main(src, out, width, height, stock=None):
    img = np.asarray(Image.open(src).convert('RGB')).astype(np.float32)
    alpha = (~background(img.astype(np.int32))).astype(np.float32)
    if stock:
        rgb, opaque = fit_to_stock(img, alpha, stock, cols=10, rows=7, cell=79)
        rgb, opaque = rgb[:height, :width], opaque[:height, :width]
    else:
        rgb, opaque = shrink(img, alpha, (width, height))
    save_sheet(rgb, opaque, out)


if __name__ == '__main__':
    if len(sys.argv) not in (5, 6):
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5] if len(sys.argv) == 6 else None)
