#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E20 MEC-4 四时代叠合图层生成（制作组示意，纯图形、零文字）。

产出 4 张 1920×1080 PNG（同一几何底稿，仅时代要素不同）：
  era_ming.png    明代：勺园在西南（湖区未成形，仅西南隅 pond 群）
  era_qing.png    清代：赐园湖区 + 水田纹理 + 西南弘雅园一带（虚线）
  era_minguo.png  民国：燕京大学建筑带 + 湖区疏浚 + 塔址圈
  era_today.png   今日：北京大学燕园（树点/石舫/条石遗址/勺园楼群区）

红线纪律：
- 图层内禁止渲染任何文字（OCR 负控制要求平移空白区无字）；命名全部走
  pages.config.ts 的 backing 文字槽与 tag 槽；
- MEC-4 = 制作组示意，须在页面以 tag 槽注明「示意 · 非测绘图」；
- Python 3.9.6：不使用 X | None、不使用 match。
"""
import hashlib
import json
import math
import os
import shutil

from PIL import Image, ImageDraw

OUT_TMP = "/tmp/chemistry-video/public/shaoyuan/mec4"
OUT_REPO = "/Volumes/macstudio/video-projects/assets/hist_shaoyuan/mec4"
SOURCES_CSV = "/tmp/chemistry-video/public/shaoyuan/sources.csv"

W, H = 1920, 1080
PAPER = (239, 230, 208)
PAPER_DEEP = (231, 220, 194)
GRID = (226, 215, 190)
ROAD = (219, 207, 180)

WATER_MING = (154, 176, 190)
LINE_MING = (47, 93, 124)
WATER_QING = (192, 196, 182)
LINE_QING = (122, 104, 78)
FIELD = (214, 190, 150)
WATER_REPUBLIC = (172, 186, 180)
BUILDING = (168, 158, 140)
BUILDING_LINE = (110, 98, 80)
WATER_TODAY = (152, 180, 170)
TREE = (61, 107, 84)
OCHRE = (168, 69, 44)
INDIGO = (47, 93, 124)
LEGEND = (124, 114, 145)


def blob(cx, cy, rx, ry, n=48, seed=7, wobble=0.16):
    """确定性有机多边形（无随机状态，重跑逐像素一致）。"""
    pts = []
    for i in range(n):
        a = 2.0 * math.pi * i / n
        k = math.sin(3.0 * a + seed) * 0.6 + math.sin(5.0 * a + 2 * seed) * 0.4
        r = 1.0 + wobble * k
        pts.append((cx + rx * r * math.cos(a), cy + ry * r * math.sin(a)))
    return pts


LAKE = blob(640, 545, 185, 112, seed=11)
ISLAND = blob(697, 552, 26, 16, seed=3, wobble=0.2)
POND_SW = [
    blob(212, 838, 44, 24, seed=5),
    blob(292, 878, 48, 26, seed=9),
    blob(238, 916, 30, 17, seed=2),
]
TREES = [
    (452, 470), (500, 448), (556, 434), (748, 432), (800, 456),
    (852, 500), (872, 556), (846, 612), (790, 652), (706, 676),
    (600, 682), (512, 664), (452, 626), (430, 560), (438, 508),
    (950, 600), (988, 636), (932, 540), (368, 690), (330, 730),
]
BUILDINGS = [
    (300, 470, 74, 38), (392, 506, 84, 42), (330, 562, 68, 36),
    (262, 522, 58, 32), (420, 588, 72, 36),
]
FIELDS_NE = [
    (900, 380, 150, 70), (1080, 420, 170, 80), (980, 500, 140, 66),
    (1150, 540, 120, 60),
]


def base_canvas():
    im = Image.new("RGB", (W, H), PAPER)
    dr = ImageDraw.Draw(im)
    for gy in range(0, H, 72):
        dr.line([(0, gy), (W, gy)], fill=GRID, width=1)
    for gx in range(0, W, 96):
        dr.line([(gx, 0), (gx, H)], fill=GRID, width=1)
    dr.line([(0, 742), (960, 700)], fill=ROAD, width=14)
    dr.line([(240, 1080), (420, 620)], fill=ROAD, width=10)
    return im, dr


def draw_ponds(dr, mode):
    for poly in POND_SW:
        if mode == "solid":
            dr.polygon(poly, fill=WATER_MING, outline=LINE_MING)
        elif mode == "dashed":
            dr.polygon(poly, outline=LINE_MING)
        else:
            dr.polygon(poly, outline=(196, 186, 168))


def draw_lake(dr, mode):
    if mode == "outline":
        dr.polygon(LAKE, outline=(190, 196, 188))
    elif mode == "qing":
        dr.polygon(LAKE, fill=WATER_QING, outline=LINE_QING)
        dr.polygon(ISLAND, fill=PAPER, outline=LINE_QING)
    elif mode == "republic":
        dr.polygon(LAKE, fill=WATER_REPUBLIC, outline=LINE_QING)
        dr.polygon(ISLAND, fill=PAPER, outline=LINE_QING)
    else:
        dr.polygon(LAKE, fill=WATER_TODAY, outline=(96, 122, 112))
        dr.polygon(ISLAND, fill=PAPER, outline=(96, 122, 112))


def draw_fields(dr):
    for (x, y, w, h) in FIELDS_NE:
        dr.rectangle([x, y, x + w, y + h], fill=FIELD, outline=LINE_QING)
        for i in range(1, 4):
            yy = y + h * i / 4
            dr.line([(x + 4, yy), (x + w - 4, yy)], fill=(200, 172, 128), width=1)


def draw_buildings(dr, mode):
    for (x, y, w, h) in BUILDINGS:
        if mode == "solid":
            dr.rectangle([x, y, x + w, y + h], fill=BUILDING, outline=BUILDING_LINE)
            dr.polygon([(x + 4, y), (x + w / 2, y - 14), (x + w - 4, y)], fill=BUILDING,
                       outline=BUILDING_LINE)
        else:
            dr.rectangle([x, y, x + w, y + h], outline=(178, 166, 146))


def draw_tower(dr, mode):
    cx, cy = 1010, 660
    if mode == "outline":
        dr.ellipse([cx - 26, cy - 26, cx + 26, cy + 26], outline=BUILDING_LINE, width=3)
        dr.polygon([(cx - 9, cy + 22), (cx, cy - 30), (cx + 9, cy + 22)], outline=BUILDING_LINE)
    else:
        dr.ellipse([cx - 22, cy - 22, cx + 22, cy + 22], fill=(120, 108, 92),
                   outline=BUILDING_LINE)
        dr.polygon([(cx - 8, cy + 18), (cx, cy - 26), (cx + 8, cy + 18)], fill=(90, 80, 66),
                   outline=BUILDING_LINE)


def draw_boat(dr, mode):
    if mode == "none":
        return
    x0, y0, x1, y1 = 578, 438, 646, 458
    dr.rectangle([x0, y0, x1, y1], fill=(206, 196, 176), outline=OCHRE)
    dr.rectangle([x0 + 8, y0 + 4, x1 - 8, y0 + 12], outline=OCHRE)


def draw_relic(dr):
    dr.rectangle([752, 416, 784, 440], fill=(150, 138, 118), outline=(90, 80, 66))


def draw_trees(dr):
    for (x, y) in TREES:
        dr.ellipse([x - 9, y - 9, x + 9, y + 9], fill=TREE)


def draw_shaoyuan_area_ming(dr):
    """明代勺园范围带：西南隅虚线圈（方位示意，非边界）。"""
    box = blob(250, 872, 190, 100, seed=17, wobble=0.1)
    dr.polygon(box, outline=INDIGO)
    for i in range(0, 36):
        a0 = i * 10
        a1 = a0 + 5
        dr.arc([60, 772, 440, 972], a0, a1, fill=INDIGO, width=3)


def dash_ring(dr, cx, cy, r, color, width=4, dash=14, gap=10):
    n = 72
    for i in range(n):
        if i % 2 == 0:
            a0 = 360.0 * i / n
            a1 = 360.0 * (i + 0.45) / n
            dr.arc([cx - r, cy - r * 0.78, cx + r, cy + r * 0.78], a0, a1, fill=color,
                   width=width)


def era_ming():
    im, dr = base_canvas()
    draw_lake(dr, "outline")
    draw_shaoyuan_area_ming(dr)
    draw_ponds(dr, "solid")
    draw_buildings(dr, "faint")
    return im


def era_qing():
    im, dr = base_canvas()
    draw_fields(dr)
    draw_lake(dr, "qing")
    draw_ponds(dr, "dashed")
    dash_ring(dr, 250, 872, 200, OCHRE, width=4)
    dash_ring(dr, 700, 545, 250, OCHRE, width=4)
    draw_buildings(dr, "faint")
    draw_boat(dr, "base")
    return im


def era_minguo():
    im, dr = base_canvas()
    draw_lake(dr, "republic")
    draw_ponds(dr, "ghost")
    draw_buildings(dr, "solid")
    dr.line([(300, 760), (1010, 660)], fill=(150, 138, 118), width=5)
    draw_tower(dr, "outline")
    draw_boat(dr, "base")
    return im


def era_today():
    im, dr = base_canvas()
    draw_lake(dr, "today")
    draw_ponds(dr, "ghost")
    draw_buildings(dr, "solid")
    draw_trees(dr)
    draw_tower(dr, "solid")
    draw_boat(dr, "base")
    draw_relic(dr)
    dash_ring(dr, 250, 872, 200, LEGEND, width=3)
    return im


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    for d in (OUT_TMP, OUT_REPO):
        if os.path.isdir(d):
            shutil.rmtree(d)
        os.makedirs(d)
    builders = [
        ("era_ming.png", era_ming, "MEC-4 四时代叠合层·明代（勺园在西南，湖区未成形）制作组示意·非测绘图"),
        ("era_qing.png", era_qing, "MEC-4 四时代叠合层·清代（赐园湖区与水田）制作组示意·非测绘图"),
        ("era_minguo.png", era_minguo, "MEC-4 四时代叠合层·民国（燕京大学建筑带）制作组示意·非测绘图"),
        ("era_today.png", era_today, "MEC-4 四时代叠合层·今日（北京大学燕园）兼 P1 索引底图·制作组示意·非测绘图"),
    ]
    rows = []
    for name, fn, title in builders:
        im = fn()
        p = os.path.join(OUT_TMP, name)
        im.save(p, format="PNG", optimize=True)
        shutil.copyfile(p, os.path.join(OUT_REPO, name))
        rows.append((name, title, sha256_of(p)))
        print("saved", p, im.size)
    with open(SOURCES_CSV, "a", encoding="utf-8") as f:
        for name, title, digest in rows:
            f.write(",".join([
                "mec4/" + name, title, "叠合示意", "制作组生成（本脚本）", "—",
                "scripts/gen_shaoyuan_mec4_maps.py", "2026-10-03",
                "制作组示意/非测绘图", digest, "MEC-4", "—",
            ]) + "\n")
    print("sources.csv appended", len(rows), "rows")


if __name__ == "__main__":
    main()
