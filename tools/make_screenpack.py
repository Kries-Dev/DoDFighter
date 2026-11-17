#!/usr/bin/env python3
"""Build the Deities of Death screenpack (mods/darthnox/assets/ui/).

    python tools/make_screenpack.py LF2_UI_DIR mods/darthnox/assets/ui

LF2_UI_DIR holds LF2's menu bitmaps (pe/*.bmp) dumped from the installer with a
headless probe (engine.read_resource("pe/<name>"), hex through error(); see
HANDOFF.md). Writes:

  * every blue LF2 menu sheet recoloured black / white / red (recolour(): the
    same rule as RECOLOUR in mods/darthnox/screenpack.lua, which applies it to
    the menus' plain fills and text colours)
  * menu_clip.bmp without LF2's logo strip and credits line, logo.bmp (circle
    logo + wordmark) that screenpack.lua draws in its place; menu_clip5 without
    the LF2 forum banners
  * menu_wait.bmp: the loading screen (circle logo + wordmark)
  * sky.bmp / sky_flash.bmp: the menu backdrop (storm clouds and the reaper from
    art/ui/reaper.webp; the flash is a lightning strike) and rain_0..10.bmp: rain
    streaks on black (keyed), one loop of 11 frames
Needs Pillow and numpy.
"""
import colorsys
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 794, 550
RAIN_FRAMES, RAIN_STEP = 11, 50          # 11 x 50 px = one screen height: a seamless loop
FONT_GOTHIC = 'C:/Windows/Fonts/OLDENGL.TTF'
FONT_BOLD = 'C:/Windows/Fonts/impact.ttf'
FONT_TEXT = 'C:/Windows/Fonts/segoeuib.ttf'

# Sheets drawn in LF2's blue that get recoloured (menu_back*, spark, shadow, win/lose stay).
RECOLOURED = ['menu_clip', 'menu_clip2', 'menu_clip3', 'menu_clip4', 'menu_clip5', 'menu_clip6',
              'charmenu', 'battlemode', 'battletroops', 'cma', 'cma2', 'cmc', 'cs2', 'cs3', 'cs4', 'cs5', 'cs6',
              'frame', 'bars', 'score_board1', 'score_board2', 'score_board3', 'score_board4', 'rface',
              'pause', 'demo', 'words0', 'words1', 'words5', 'back99_1', 'back99_2', 'back99_3', 'lf2_cursor']


def recolour(r, g, b):
    """LF2 blue -> ours: bright blues (text, borders) become light grey/white, darker
    blues (panels, boxes, the menu fill) a deep blood red. Other colours stay."""
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    if s < 0.2 or not (0.5 <= h <= 0.75):
        return r, g, b
    if v >= 0.62:
        grey = round(min(1.0, v * 0.95) * 255)
        return grey, grey, grey
    rr, gg, bb = colorsys.hsv_to_rgb(0.0, min(1.0, s * 0.9 + 0.1), v * 0.5)
    return round(rr * 255), round(gg * 255), round(bb * 255)


def recolour_sheet(src, dst):
    im = Image.open(src)
    assert im.mode == 'P', src
    pal = im.getpalette()[:768]
    new = []
    for i in range(0, len(pal), 3):
        new += recolour(*pal[i:i + 3])
    im.putpalette(new)
    im.save(dst)
    return im


def to_8bit(rgb, keyed):
    """RGB (numpy uint8) -> 8-bit BMP image. keyed: pure black stays index 0 (transparent);
    else nothing is pure black (an opaque picture)."""
    arr = rgb.copy()
    if not keyed:
        arr[(arr.sum(axis=2) == 0)] = (1, 1, 1)
    im = Image.fromarray(arr, 'RGB').quantize(255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = im.getpalette()[:765]
    idx = np.array(im, dtype=np.int16) + 1
    if keyed:
        idx[(arr.sum(axis=2) == 0)] = 0
    out = Image.fromarray(idx.astype(np.uint8), 'P')
    out.putpalette([0, 0, 0] + pal + [0, 0, 0] * (256 - 1 - len(pal) // 3))
    return out


def noise(w, h, seed, octaves=6):
    rng = np.random.default_rng(seed)
    total = np.zeros((h, w))
    amp, norm = 1.0, 0.0
    for o in range(octaves):
        cells = 2 ** (o + 2)
        grid = rng.random((cells + 1, int(cells * w / h) + 2))
        layer = np.array(Image.fromarray((grid * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)) / 255.0
        total += layer * amp
        norm += amp
        amp *= 0.55
    return total / norm


def reaper_layer(height):
    im = Image.open('art/ui/reaper.webp').convert('RGBA')
    a = np.array(im).astype(np.float64)
    # the art is on white: make near-white transparent, soft edge
    white = np.clip((a[..., :3].min(axis=2) - 215) / 30, 0, 1)
    a[..., 3] = a[..., 3] * (1 - white)
    im = Image.fromarray(a.astype(np.uint8), 'RGBA')
    im = im.crop(im.getbbox())
    return im.resize((round(im.width * height / im.height), height), Image.LANCZOS)


def bolt(draw, x, y, length, rng, width):
    points = [(x, y)]
    while y < length:
        x += rng.integers(-22, 23)
        y += rng.integers(14, 34)
        points.append((x, y))
        if rng.random() < 0.18:
            bx, by = x, y
            for _ in range(rng.integers(2, 5)):
                nx, ny = bx + rng.integers(-30, 31), by + rng.integers(12, 30)
                draw.line([(bx, by), (nx, ny)], fill=(255, 255, 255), width=1)
                bx, by = nx, ny
    draw.line(points, fill=(255, 255, 255), width=width)


def sky(flash):
    y = np.linspace(0, 1, H)[:, None]
    clouds = noise(W, H, 11)
    clouds = np.clip((clouds - 0.35) * 1.8, 0, 1) * (1 - y * 0.55)
    base = np.stack([8 + 30 * y, 6 + 6 * y, 8 + 6 * y], axis=2) * np.ones((H, W, 1))   # black -> deep red at the floor
    light = 70 if not flash else 175
    cloud_rgb = np.stack([clouds * light * 1.05, clouds * light * 0.93, clouds * light * 0.95], axis=2)
    img = np.clip(base + cloud_rgb, 0, 255)
    pic = Image.fromarray(img.astype(np.uint8), 'RGB')
    if flash:
        glow = Image.new('RGB', (W, H))
        d = ImageDraw.Draw(glow)
        bolt(d, 720, 0, 300, np.random.default_rng(5), 2)
        bolt(d, 770, 0, 170, np.random.default_rng(9), 1)
        halo = glow.filter(ImageFilter.GaussianBlur(7))
        halo = Image.fromarray((np.array(halo) * np.array([1.0, 0.35, 0.35])).astype(np.uint8))
        pic = Image.fromarray(np.clip(np.array(pic).astype(int) + np.array(halo) * 2 + np.array(glow), 0, 255).astype(np.uint8))
    # the reaper, left of the menu, feet on the floor; rim-lit in the flash
    reaper = reaper_layer(500)
    if flash:
        rim = Image.new('RGBA', reaper.size, (150, 140, 145, 0))
        rim.putalpha(reaper.getchannel('A').filter(ImageFilter.MaxFilter(3)).point(lambda v: v * 3 // 5))
        pic.paste(rim, (-8, H - reaper.height + 5), rim)
    pic.paste(reaper, (-10, H - reaper.height + 6), reaper)
    # a faint red mist along the floor
    arr = np.array(pic).astype(np.float64)
    mist = np.clip((y - 0.8) / 0.2, 0, 1)[..., None] * noise(W, H, 3)[..., None]
    arr += mist * np.array([60, 6, 6])
    return to_8bit(np.clip(arr, 0, 255).astype(np.uint8), keyed=False)


def rain():
    rng = np.random.default_rng(21)
    drops = [(rng.integers(0, W), rng.integers(0, H), rng.integers(9, 18), rng.integers(110, 200)) for _ in range(260)]
    frames = []
    for f in range(RAIN_FRAMES):
        im = Image.new('RGB', (W, H))
        d = ImageDraw.Draw(im)
        for x, y, length, shade in drops:
            yy = (y + f * RAIN_STEP) % H
            for dy in (0, -H):   # wrap
                d.line([(x, yy + dy), (x - length // 4, yy + dy + length)], fill=(shade, shade, shade + 10), width=1)
        frames.append(to_8bit(np.array(im), keyed=True))
    return frames


def font(path, size):
    return ImageFont.truetype(path, size)


def wordmark(w, h, big, onto=None, at=(0, 0)):
    """'Deities of Death' in white blackletter over a red 'FIGHTER' (on black, or drawn onto `onto`)."""
    im = onto if onto is not None else Image.new('RGB', (w, h))
    ox, oy = at
    d = ImageDraw.Draw(im)
    top = font(FONT_GOTHIC, big)
    sub = font(FONT_BOLD, max(12, big * 5 // 9))
    t1, t2 = 'Deities of Death', 'F I G H T E R'
    b1, b2 = d.textbbox((0, 0), t1, font=top), d.textbbox((0, 0), t2, font=sub)
    h1, h2 = b1[3] - b1[1], b2[3] - b2[1]
    gap = big // 10
    y0 = oy + (h - h1 - h2 - gap) // 2
    d.text((ox + (w - (b1[2] - b1[0])) // 2 - b1[0], y0 - b1[1]), t1, font=top, fill=(240, 240, 240))
    d.text((ox + (w - (b2[2] - b2[0])) // 2 - b2[0], y0 + h1 + gap - b2[1]), t2, font=sub, fill=(200, 16, 24))
    return im


def circle_logo(size):
    im = Image.open('art/ui/logo_circle.webp').convert('RGB')
    im = im.crop(im.getbbox())
    return im.resize((size, size), Image.LANCZOS)


LOGO = (440, 196)   # logo.bmp: screenpack.lua draws it where LF2's logo strip was


def logo():
    """Circle logo over the wordmark, keyed (black = transparent)."""
    w, h = LOGO
    pic = Image.new('RGB', (w, h))
    pic.paste(circle_logo(112), ((w - 112) // 2, 0))
    pic.paste(wordmark(w, 84, 46), (0, 112))
    return to_8bit(np.array(pic), keyed=True)


def put_rgb(sheet, rgb, box_xy, clear=None):
    """Paste an RGB picture into an 8-bit sheet using the sheet's palette (index 0 = black)."""
    pal = np.array(sheet.getpalette()[:768]).reshape(-1, 3).astype(int)
    a = np.array(rgb).astype(int)
    d = ((a[:, :, None, :] - pal[None, None, 1:, :]) ** 2).sum(axis=3)
    idx = d.argmin(axis=2) + 1
    idx[a.sum(axis=2) < 24] = 0
    arr = np.array(sheet)
    if clear:
        x0, y0, x1, y1 = clear
        arr[y0:y1, x0:x1] = 0
    x, y = box_xy
    arr[y:y + idx.shape[0], x:x + idx.shape[1]] = idx
    out = Image.fromarray(arr.astype(np.uint8), 'P')
    out.putpalette(sheet.getpalette())
    return out


def loading_screen():
    y = np.linspace(0, 1, H)[:, None, None]
    img = np.ones((H, W, 3)) * np.array([6, 4, 5]) + y * np.array([40, 4, 6])
    pic = Image.fromarray(img.astype(np.uint8), 'RGB')
    mask = Image.new('L', (300, 300))
    ImageDraw.Draw(mask).ellipse((1, 1, 298, 298), fill=255)
    pic.paste(circle_logo(300), ((W - 300) // 2, 70), mask)
    wordmark(520, 110, 56, onto=pic, at=((W - 520) // 2, 385))
    d = ImageDraw.Draw(pic)
    d.text((612, 12), 'Now Loading...', font=font(FONT_TEXT, 17), fill=(235, 235, 235))
    return to_8bit(np.array(pic), keyed=False)


def main(src, out):
    os.makedirs(out, exist_ok=True)
    sheets = {n: recolour_sheet(os.path.join(src, n + '.bmp'), os.path.join(out, n + '.bmp')) for n in RECOLOURED}
    # menu_clip: LF2's logo strip and credits line (top right) blanked; logo.bmp is drawn instead
    clip = sheets['menu_clip']
    arr = np.array(clip)
    arr[41:121, 0:496] = 0
    arr[0:40, 560:794] = 0
    clip2 = Image.fromarray(arr, 'P'); clip2.putpalette(clip.getpalette())
    clip2.save(os.path.join(out, 'menu_clip.bmp'))
    logo().save(os.path.join(out, 'logo.bmp'))
    small = Image.new('RGB', (496, 80))     # pages with less room (launch sub-pages): the strip's own size
    small.paste(circle_logo(78), (6, 1))
    small.paste(wordmark(404, 80, 40), (90, 0))
    to_8bit(np.array(small), keyed=True).save(os.path.join(out, 'logo_s.bmp'))
    # menu_clip5: the LF2 forum banners blanked
    arr = np.array(sheets['menu_clip5'])
    arr[203:387, 0:425] = 0
    c5 = Image.fromarray(arr, 'P'); c5.putpalette(sheets['menu_clip5'].getpalette())
    c5.save(os.path.join(out, 'menu_clip5.bmp'))
    loading_screen().save(os.path.join(out, 'menu_wait.bmp'))
    sky(False).save(os.path.join(out, 'sky.bmp'))
    sky(True).save(os.path.join(out, 'sky_flash.bmp'))
    for i, frame in enumerate(rain()):
        frame.save(os.path.join(out, f'rain_{i}.bmp'))
    print('wrote', len(RECOLOURED) + 3 + RAIN_FRAMES, 'pictures to', out)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
