#!/usr/bin/env python3
"""Turn one painted picture into an OpenLF2 background (stage).

    python tools/image_to_stage.py PICTURE.png OUT_DIR NAME ROAD_TOP ROAD_BOTTOM [WIDTH]

PICTURE.png  any RGB/RGBA PNG (the art is scaled, never stretched)
NAME         stage name shown in the picker (spaces become underscores)
ROAD_TOP     first source-pixel row fighters may stand on (back edge of the floor)
ROAD_BOTTOM  last source-pixel row fighters may stand on (front edge)
WIDTH        stage width in game pixels, default 794 (one screen, like HK Coliseum)

Writes OUT_DIR/stage.bmp (8-bit, the picture scaled to WIDTH and bottom-aligned
to the 550-px screen) and prints the `zboundary` for the bg file, which is
ROAD_TOP/ROAD_BOTTOM mapped into screen pixels. The top 128 px of the screen sit
under the HP/MP panel, so keep the picture's important parts below that.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from autosprite_to_lf2 import read_png, write_bmp, area_resample, median_cut, nearest

SCREEN_H = 550
PANEL_H = 128


def build(picture, out_dir, name, road_top, road_bottom, width=794):
    os.makedirs(out_dir, exist_ok=True)
    W, H, img = read_png(picture)
    scale = width / W
    height = round(H * scale)
    top = SCREEN_H - height           # bottom-aligned; negative = cropped under the panel
    cell = area_resample(img, 0, 0, W, H, scale, width, height)
    colours = [(int(r), int(g), int(b)) for line in cell for (r, g, b, a) in line]
    pal = median_cut(colours[::3], 255)
    cache = {}
    rows = [[nearest(pal, (int(r), int(g), int(b)), cache) for (r, g, b, a) in line] for line in cell]
    write_bmp(os.path.join(out_dir, 'stage.bmp'), width, height, [(0, 0, 0)] + pal, rows)
    near = top + round(road_top * scale)
    far = top + round(road_bottom * scale)
    print(f'stage.bmp {width}x{height} at y {top}  (hidden under panel: {max(0, PANEL_H - top)} px)')
    print(f'name: {name.replace(" ", "_")}')
    print(f'width: {width}   zboundary: {near} {far}')
    return dict(width=width, height=height, top=top, near=near, far=far, pal=pal, rows=rows)


if __name__ == '__main__':
    if len(sys.argv) not in (6, 7):
        sys.exit(__doc__)
    a = sys.argv
    build(a[1], a[2], a[3], int(a[4]), int(a[5]), int(a[6]) if len(a) == 7 else 794)
