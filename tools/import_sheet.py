#!/usr/bin/env python3
"""Turn an edited (often upscaled) picture of an LF2 sprite sheet back into a
game-ready 8-bit sheet.

    python tools/import_sheet.py EDITED.png|webp OUT.bmp WIDTH HEIGHT

Used for the user's restyled Bandit (`art/bandit_0_edit.webp` -> bandit_0.bmp,
800 x 560). The edited picture keeps the stock layout (10 x 7 cells of 79 px
with a 1 px gutter) but may be any size and on a light background:

  * the background (near-white pixels connected to the picture's edges) is
    removed; light areas inside a sprite (a white shirt) stay
  * the picture is scaled to WIDTH x HEIGHT with an alpha-weighted box filter,
    so sprite edges don't pick up a white halo
  * colours are reduced to 255 (median cut) plus index 0 = pure black, the
    transparent colour; no sprite pixel is pure black
Needs Pillow and numpy.
"""
import sys
from collections import deque
import numpy as np
from PIL import Image

BACKGROUND_MIN = 232      # a pixel is background-ish if all channels are at least this
OPAQUE = 0.5              # coverage needed after scaling for a pixel to be drawn


def background(img):
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


def scale(channel, size):
    return np.asarray(Image.fromarray(channel.astype(np.float32), 'F').resize(size, Image.BOX))


def main(src, out, width, height):
    img = np.asarray(Image.open(src).convert('RGB')).astype(np.float32)
    alpha = (~background(img.astype(np.int32))).astype(np.float32)
    size = (width, height)
    a = scale(alpha, size)
    rgb = np.stack([scale(img[..., k] * alpha, size) for k in range(3)], axis=2)
    opaque = a >= OPAQUE
    rgb = np.where(opaque[..., None], rgb / np.maximum(a, 1e-6)[..., None], 0)
    rgb = np.clip(np.rint(rgb), 0, 255).astype(np.uint8)
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
    print(f'{out}: {width}x{height}, {len(set(idx[opaque].tolist()))} colours + transparent')


if __name__ == '__main__':
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
