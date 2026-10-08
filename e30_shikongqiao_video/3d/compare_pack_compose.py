# -*- coding: utf-8 -*-
"""M23 照片对照包 - 拼图合成(纯 Python, 不依赖 Blender)。

每组一张拼图: 左照片 | 右渲染, 顶部标注(角度/照片来源/位姿来源), 底部两侧注记。
输出: 3d/out/compare_pack/pairs/pair_*.jpg
用法: python3 compare_pack_compose.py [--pairs a,b,c,d,e,e2,f]
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "out", "compare_pack")
REN = os.path.join(OUT, "renders")
PAIRS = os.path.join(OUT, "pairs")
WINTER_FULL = os.path.join(HERE, "refs", "balustrade_count", "src", "winter_20201221160537.jpg")

FONT_CANDS = ["/System/Library/Fonts/PingFang.ttc",
              "/System/Library/Fonts/Hiragino Sans GB.ttc",
              "/System/Library/Fonts/STHeiti Medium.ttc",
              "/Library/Fonts/Arial Unicode.ttf"]

HDR_H, CAP_H, PAD, DIV = 64, 40, 12, 4


def font(sz):
    for p in FONT_CANDS:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except Exception:
                continue
    return ImageFont.load_default()


def label_bar(w, text, h, align="left"):
    im = Image.new("RGB", (w, h), (24, 26, 30))
    d = ImageDraw.Draw(im)
    f = font(int(h * 0.52))
    bbox = d.textbbox((0, 0), text, font=f)
    tw = bbox[2] - bbox[0]
    x = PAD if align == "left" else max(PAD, w - tw - PAD)
    d.text((x, (h - (bbox[3] - bbox[1])) // 2 - bbox[1]), text, font=f, fill=(232, 230, 224))
    return im


def side_caption(w, left_text, right_text):
    im = Image.new("RGB", (w, CAP_H), (24, 26, 30))
    d = ImageDraw.Draw(im)
    f = font(int(CAP_H * 0.48))
    d.text((PAD, CAP_H // 5), left_text, font=f, fill=(150, 200, 150))
    d.text((w // 2 + PAD, CAP_H // 5), right_text, font=f, fill=(150, 180, 220))
    return im


def compose_pair(title, photo, render, sub_left, sub_right, out_name, max_w=1920):
    """photo/render: 同尺寸 PIL RGB。左右拼接 + 头注 + 侧注。"""
    assert photo.size == render.size, (photo.size, render.size)
    pw, ph = photo.size
    scale = min(1.0, (max_w - DIV) / float(2 * pw))
    nw, nh = int(pw * scale), int(ph * scale)
    photo = photo.resize((nw, nh), Image.LANCZOS)
    render = render.resize((nw, nh), Image.LANCZOS)
    W = nw * 2 + DIV
    canvas = Image.new("RGB", (W, HDR_H + nh + CAP_H), (24, 26, 30))
    canvas.paste(label_bar(W, title, HDR_H), (0, 0))
    canvas.paste(photo, (0, HDR_H))
    canvas.paste(render, (nw + DIV, HDR_H))
    canvas.paste(side_caption(W, sub_left, sub_right), (0, HDR_H + nh))
    os.makedirs(PAIRS, exist_ok=True)
    outp = os.path.join(PAIRS, out_name)
    canvas.save(outp, quality=92)
    print("PAIR_OK", outp, canvas.size)
    return outp


def crop_scale(img, box, out_wh):
    return img.crop(box).resize(out_wh, Image.LANCZOS)


# ── 各组 ──

def pair_a():
    photo = Image.open(os.path.join(HERE, "refs", "ref_elevation.jpg")).convert("RGB")
    ren = Image.open(os.path.join(REN, "a_front.png")).convert("RGB")
    M = 70  # 照片桥带外扩边距(px, 同 5.62px/m ≈ 12m 上下文)
    box = (462 - M, 416 - M, 1305 + M, 460 + M)
    pc = photo.crop(box)
    # 渲染与照片同 ppm(5.62) 同配准 -> 裁剪框直接同像素坐标(尺寸不同时按 ppm 换算)
    rw, rh = ren.size
    sx, sy = rw / 1920.0, rh / 879.0
    rbox = (int(box[0] * sx), int(box[1] * sy), int(box[2] * sx), int(box[3] * sy))
    rc = ren.crop(rbox).resize(pc.size, Image.LANCZOS)
    return compose_pair(
        "组a 正视全景 | 照片: frontal_2011 (T3.5冻结 refs/ref_elevation.jpg, Canon 400D, ~2011摄制版) | "
        "渲染: 正交正视, ppm=5.62 同尺度配准(水线中点对齐), blend=e30_bridge(M18砧石/M19冬照Z基准), seed=20261004",
        pc, rc,
        "照片 frontal_2011 (近正交正视, 1920x879)",
        "渲染 正交正视 (L3 IoU 基线同管线视角)",
        "pair_a_frontal.jpg")


def pair_arch(lab, ftag, crop_json):
    GOLDEN = os.environ.get("GOLDEN") == "1"
    photo = Image.open(os.path.join(HERE, f"real_券洞{lab}.jpg")).convert("RGB")
    grp = {"A": "b", "B": "c", "C": "d"}[lab]
    ren = Image.open(os.path.join(REN, f"{'golden_' if GOLDEN else ''}{grp}_{ftag}.png")).convert("RGB")
    box = crop_json[lab]["crop"]  # 1920x1080 标定画幅坐标
    rw, rh = ren.size
    s = rw / 1920.0
    rbox = tuple(int(v * s) for v in box)
    rc = ren.crop(rbox).resize(photo.size, Image.LANCZOS)
    arch = crop_json[lab]["arch"]
    lit = ("金光对齐版 v3(日沿桥轴低角+拱腹暖面光+暖渐变天穹)=对照主图" if GOLDEN
           else "中性光版=材质判读基准")
    return compose_pair(
        f"组{grp} 券洞特写 (券洞{lab}) | 照片: real_券洞{lab}.jpg (M0研究裁片, 无EXIF/无标定位姿) | "
        f"渲染: m20B 位姿相机 {ftag} 水线约束修正版 (solvePnP+wlfit), 孔位 a{arch} | 光照: {lit}",
        photo, rc,
        f"照片 real_券洞{lab}.jpg ({photo.size[0]}x{photo.size[1]}, 来源未登记)",
        f"渲染 {'金光v3 ' if GOLDEN else '中性 '}{ftag} 位姿 孔a{arch} 裁窗 (仅量级对照: 位姿非本照片标定)",
        f"pair_{grp}_quandong{lab}_{ftag}{'_GOLDEN' if GOLDEN else ''}.jpg")


def pair_e():
    GOLDEN = os.environ.get("GOLDEN") == "1"
    photo = Image.open(WINTER_FULL).convert("RGB").resize((3552, 2368), Image.LANCZOS)
    ren = Image.open(os.path.join(REN, "golden_e_winter.png" if GOLDEN else "e_winter.png")).convert("RGB")
    if ren.size != photo.size:
        ren = ren.resize(photo.size, Image.LANCZOS)
    return compose_pair(
        "组e 冬照端视全景 | 照片: winter_20201221160537.jpg (2020-12-21 冬至金光, 7106x4737) | "
        "渲染: m20C_pose_winter 位姿相机 (M19 冬照 Z 基准, n=7 强退化如实声明), seed=20261004 | 光照: "+("金光对齐版=对照主图" if os.environ.get("GOLDEN")=="1" else "中性光版=材质判读基准"),
        photo, ren,
        "照片 冬照全景 (金光穿洞时段, 湖面冰封)",
        "渲染 同位姿全画幅 (标注位: 光照时段未复现→见待改进清单)",
        "pair_e_winter%s.jpg" % ("_GOLDEN" if os.environ.get("GOLDEN") == "1" else ""))


def pair_e2(ext_renders=None):
    """东端特写: 冬照 wire_end 区域(去注记的干净源裁剪) vs 渲染同窗裁剪。"""
    full = Image.open(WINTER_FULL).convert("RGB")
    fw, fh = full.size
    # wire_end(2106x1000) 是该区域放大版; 区域按 2.4x 反推(模板配准失效, 人工定位东端)
    s = 2.4
    cx, cy = 5480, 2330  # 东端三孔+兽(全图坐标, 目视定位)
    w2, h2 = int(2106 / s), int(1000 / s)
    box = (cx - w2 // 2, cy - h2 // 2, cx - w2 // 2 + w2, cy - h2 // 2 + h2)
    box = (max(0, box[0]), max(0, box[1]), min(fw, box[2]), min(fh, box[3]))
    pc = full.crop(box)
    ren = Image.open(os.path.join(REN, "e_winter.png")).convert("RGB")
    rw, rh = ren.size
    k = rw / float(fw)
    rbox = tuple(int(v * k) for v in box)
    rc = ren.crop(rbox).resize(pc.size, Image.LANCZOS)
    return compose_pair(
        "组e2 冬照东端特写 | 照片: winter_20201221160537.jpg 东端裁剪(基准展示片 m20_ctrl/winter_wire_end.jpg 同窗, 原片无注记) | "
        "渲染: m20C 位姿相机同窗 (M19 Z 基准)",
        pc, rc,
        "照片 冬照东端 (栏板/望柱/靠山兽/端孔)",
        "渲染 同窗裁剪 (造型级: 兽/狮程序化雕刻细节非细节级)",
        "pair_e2_winter_end.jpg")


def pair_f():
    sys.path.insert(0, HERE)
    from m20_pipeline import Model, load_ctrl  # 纯 python+cv2, 系统环境
    model = Model(load_ctrl())
    strips = []
    xs = []
    for i in (5, 6, 7):
        p = os.path.join(HERE, "m20_ctrl", f"m20B_ortho_a{i}.png")
        a = model.arches[i]
        ext = (a["xc"] - a["a"] - 2.0, a["xc"] + a["a"] + 2.0)
        strips.append((i, Image.open(p).convert("RGB"), ext))
        xs += list(ext)
    ppm = 80.0
    x0, x1 = min(xs), max(xs)
    W = int(round((x1 - x0) * ppm))
    Hs = [s.size[1] for _, s, _ in strips]
    H = max(Hs)
    mos = Image.new("RGB", (W, H), (0, 0, 0))
    for i, s, ext in strips:
        mos.paste(s, (int(round((ext[0] - x0) * ppm)), 0))
    ren = Image.open(os.path.join(REN, "f_side.png")).convert("RGB")
    pr = json.load(open(os.path.join(OUT, "params", "f_side.json")))
    water_row = pr["camera"]["water_row_px"]
    assert abs(pr["camera"]["hppm"] - ppm) < 0.01, "render ppm 与照片条不一致"
    # 三行: 每孔 照片正射条 | 渲染同窗段(同为 80px/m 方像素, 直接裁剪不缩放)
    rows = []
    for i, s, ext in strips:
        bx = (int(round((ext[0] - x0) * ppm)), int(round(water_row - s.size[1])),
              int(round((ext[1] - x0) * ppm)), int(round(water_row)))
        rc = ren.crop(bx)
        if rc.size != s.size:
            rc = rc.resize(s.size, Image.LANCZOS)
        rows.append((i, s, rc))
    gap = 6
    Wc = max(s.size[0] for _, s, _ in rows) * 2 + DIV
    Hc = HDR_H + sum(r[1].size[1] + gap for r in rows) + CAP_H
    canvas = Image.new("RGB", (Wc, Hc), (24, 26, 30))
    canvas.paste(label_bar(Wc,
        "组f 侧视全景 | 照片: m20B_ortho_a5+a6+a7 正射拼接(由三帧 CCTV 位姿重采样, ppm=80, 非单一实拍) | "
        "渲染: 正交侧视同 ppm 同窗口, seed=20261004", HDR_H), (0, 0))
    y = HDR_H
    for i, s, rc in rows:
        canvas.paste(s, (0, y))
        canvas.paste(rc, (s.size[0] + DIV, y))
        y += s.size[1] + gap
    canvas.paste(side_caption(Wc, "照片 正射拼接 (帧间亮度不连续=源片差异; 孔a5|a6|a7)",
                              "渲染 正交侧视 (同窗同比例)"), (0, y))
    outp = os.path.join(PAIRS, "pair_f_side.jpg")
    canvas.save(outp, quality=90)
    print("PAIR_OK", outp, canvas.size)
    return outp


def main():
    which = sys.argv[1].split("=")[1] if len(sys.argv) > 1 and "=" in sys.argv[1] else "a,b,c,d,e,e2,f"
    labs = which.split(",")
    cj_path = os.path.join(HERE, "out", "compare_pack", "crop_boxes.json")
    cj = json.load(open(cj_path)) if os.path.exists(cj_path) else {}
    if not cj:
        cj = json.load(open("/tmp/crop_boxes.json"))
        # 补充 rms
        for k, v in cj.items():
            p = json.load(open(os.path.join(HERE, f"m20_ctrl/m20B_pose_{v['ftag']}.json")))
            v["rms"] = round(p["rms"], 1)
    for lab in labs:
        if lab == "a":
            pair_a()
        elif lab in ("b", "c", "d"):
            m = {"b": "A", "c": "B", "d": "C"}[lab]  # 券洞A/B/C ↔ 渲染 b_f150/c_f175/d_f675
            pair_arch(m, cj[m]["ftag"], cj)
        elif lab == "e":
            pair_e()
        elif lab == "e2":
            pair_e2()
        elif lab == "f":
            pair_f()
    print("COMPOSE_DONE", labs)


if __name__ == "__main__":
    main()
