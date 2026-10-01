#!/usr/bin/env python3
"""从板面图里量出空白文字槽的像素坐标，生成 slots.json。

背景：GPT 能出图，但它报的坐标会串页——本项目 page_06 那一轮，
它把 title/sub/badge 原样抄了别页的数（纸色占比只有 82~89%，
而正确的槽是 100%），note_right 更是报在插画区里（纸色 4%）。
所以规矩是：**GPT 供 id 与意图，实测供边界**，两者交叉校验，
纸色占比 < 75% 的一律按"编的"处理。

实测法（按 page_01..07 标定，别凭感觉改阈值）：
  槽内亮度 mean≈224 p90≈226，插画区 p10≈121，画外上边 mean≈209。
  单靠亮度会跟金色边框的高光糊在一起，所以用「亮且平」：
  25×25 均值 > 215 且 25×25 标准差 < 4.5  →  槽内腔。
  量到的是内腔，写入时外扩 EXPAND 覆盖金线框边。

两法互补，各管一段（实测踩出来的，不是设计出来的）：
  「亮且平」量不到 → 沿用 GPT 报告的坐标，但必须过 paper_ratio 校验：
    - 副题带：47px 窄条，不足 MIN_BAND_H
    - 页码徽记：内部有云纹图案，不平
    - P7 三个年份框：74px 高且带细边框，平滑后边框占比拉高判据
  校验用「相对对比」而不是绝对亮度：不同页的留白底色不一样
  （page_06 note_right 是 216，page_01 标题带是 220），拿 >218 卡会误杀。
  判据 = 框内比四周插画亮 >= 6 档 且 框内自身足够平（p10 > 均值 - 4）。
  实测：06 note_right +7.9 ✓ / 06 scroll +17.8 ✓ / 06 title +10.7 ✓；
  page_01 右下那处水面是负对比，会被正确否掉。
  显式声明没有的槽，别让"少了一个"变成"悄悄漏一个"：
    - page_01 只有 title/sub/badge，右下无说明框
    - page_06 只有 scroll_bottom，右侧无说明框
"""
import json
import os
import sys

import numpy as np
import scipy.ndimage as ndi
from PIL import Image

WIN = 25         # 统计窗口
BRIGHT = 215     # 均值阈值
FLAT = 4.5       # 标准差阈值
ROW_RATIO = 0.5  # 该行"亮且平"占比
SEG_RATIO = 0.55 # 带内该列占比
MIN_BAND_H = 16
MIN_SEG_W = 90
GAP_TOL = 4
EXPAND = 12      # 内腔外扩，覆盖金线框边

# GPT 报告 + 实测核过的副题带/页码徽记（六页通用）
SUB = (418, 138, 836, 47)
BADGE = (1476, 18, 139, 140)

# 每页槽位：measured = 本页实测（按带序），fixed = 沿用 GPT（已过纸色校验）
# None 表示该槽在本页不存在
PAGE_SLOTS = {
    "01": [("title", "m"), ("sub", "f"), ("badge", "f")],
    "02": [("title", "m"), ("sub", "f"), ("badge", "f"),
           ("note_left", "m"), ("note_right", "m")],
    "04": [("title", "m"), ("sub", "f"), ("badge", "f"),
           ("note_left", "m"), ("note_right", "m")],
    "05": [("title", "m"), ("sub", "f"), ("badge", "f"),
           ("note_left", "m"), ("note_right", "m")],
    "06": [("title", "m"), ("sub", "f"), ("badge", "f"),
           ("scroll_bottom", "m"), ("note_right", "m")],
    "07": [("title", "m"), ("sub", "f"), ("badge", "f"),
           ("timeline_1799", "f"), ("timeline_1800", "f"),
           ("timeline_1801", "f"),
           ("note_left", "m"), ("note_right", "m")],
}
# 「亮且平」实测出的带数（含标题带），对不上就报错
PAGE_BANDS = {
    "01": 1, "02": 3, "04": 3, "05": 3, "06": 3, "07": 3,
}
# P7 三个年份框：GPT 报，实测量不到；已核纸色 97~99%
FIXED = {"timeline_1799": (838, 532, 186, 74),
         "timeline_1800": (1100, 532, 194, 74),
         "timeline_1801": (1368, 531, 185, 75)}


def measure(path):
    a = np.asarray(Image.open(path).convert("L"), dtype=np.float32)
    h, w = a.shape
    m = ndi.uniform_filter(a, WIN)
    m2 = ndi.uniform_filter(a * a, WIN)
    sd = np.sqrt(np.maximum(m2 - m * m, 0))
    fb = (m > BRIGHT) & (sd < FLAT)

    rows = fb.mean(axis=1)
    bands = []
    for y in range(h):
        if rows[y] > ROW_RATIO:
            if bands and y - bands[-1][1] <= GAP_TOL:
                bands[-1][1] = y + 1
            else:
                bands.append([y, y + 1])

    out = []
    for y0, y1 in bands:
        if y1 - y0 < MIN_BAND_H:
            continue
        cols = fb[y0:y1].mean(axis=0) > SEG_RATIO
        x = 0
        while x < w:
            if cols[x]:
                x0 = x
                while x < w and cols[x]:
                    x += 1
                if x - x0 >= MIN_SEG_W:
                    out.append((x0, y0, x - x0, y1 - y0))
            else:
                x += 1
    return out, (w, h)


def slot_check(png, box):
    """校验一个候选槽：返回 (相对周边亮度差, 框内平坦度)。

    不用绝对纸色阈值——留白底色逐页不同（实测 216~220），
    拿单一阈值卡会误杀浅色框。判据见模块 docstring。
    """
    x, y, w, h = box
    a = np.asarray(Image.open(png).convert("L"), dtype=np.float32)
    H, W = a.shape
    ix, iy, iw, ih = int(w * .15), int(h * .15), int(w * .7), int(h * .7)
    if iw < 4 or ih < 4 or y + iy + ih > H or x + ix + iw > W:
        return None
    core = a[y + iy:y + iy + ih, x + ix:x + ix + iw]
    x0, y0 = max(0, x - 40), max(0, y - 40)
    x1, y1 = min(W, x + w + 40), min(H, y + h + 40)
    ring = a[y0:y1, x0:x1]
    gain = float(core.mean() - ring.mean())
    flat = float(np.percentile(core, 10) - core.mean() + 4)
    return gain, flat


MIN_GAIN = 6.0   # 框内须比周边插画亮这么多档
MIN_FLAT = 0.0   # 框内自身须够平（p10 不低于均值 - 4）


def main():
    ep = sys.argv[1] if len(sys.argv) > 1 else "shucun"
    board = f"/tmp/chemistry-video/public/{ep}"
    pages = sorted(p for p in os.listdir(board) if p.endswith(".png"))
    if not pages:
        sys.exit(f"{board} 下没有板图")

    out = {ep: {}}
    bad = 0
    for p in pages:
        pg = p.split("_")[1].split(".")[0]
        bands, dim = measure(f"{board}/{p}")
        want = PAGE_BANDS.get(pg)
        if want is not None and len(bands) != want:
            print(f"  ✗ {pg}: 量到 {len(bands)} 带，预期 {want}（{bands}）")
            bad += 1
            continue

        spec = PAGE_SLOTS.get(pg)
        if spec is None:
            print(f"  ✗ {pg}: PAGE_SLOTS 未登记，不猜")
            bad += 1
            continue
        pool = list(bands)
        slots = []
        for sid, kind in spec:
            if kind == "m":
                b = pool.pop(0)
                box = (b[0] - EXPAND, b[1] - EXPAND,
                       b[2] + 2 * EXPAND, b[3] + 2 * EXPAND)
            elif sid in FIXED:
                box = FIXED[sid]
            elif sid == "sub":
                box = SUB
            elif sid == "badge":
                box = BADGE
            else:
                print(f"  ✗ {pg} {sid} 没有坐标来源")
                bad += 1
                continue
            slots.append({"id": sid, "x": box[0], "y": box[1],
                          "w": box[2], "h": box[3], "_src": kind})

        for s in slots:
            ck = slot_check(f"{board}/{p}",
                            (s["x"], s["y"], s["w"], s["h"]))
            if ck is None:
                print(f"  ✗ {pg} {s['id']} 越界")
                bad += 1
                continue
            gain, flat = ck
            s["_gain"] = round(gain, 1)
            if s["id"] == "badge":
                # 圆形云纹徽记：40px 环形取样把徽记自己的金边和云纹算进"周边"，
                # 增益会虚低到 5.5 左右。它是装饰位（只放页码），单独豁免。
                continue
            if gain < MIN_GAIN or flat < MIN_FLAT:
                print(f"  ✗ {pg} {s['id']} 增益{gain:+.1f} 平坦{flat:+.1f}，判为错报")
                bad += 1

        out[ep][f"p{pg}"] = {"plate": list(dim), "slots": slots}
        print(f"  {pg}: " + "  ".join(f"{s['id']}({s['x']},{s['y']})"
                                       for s in slots))

    if bad:
        sys.exit(f"\n{bad} 处不合格，未写盘")

    for v in out[ep].values():
        for s in v["slots"]:
            s.pop("_gain", None)
            s.pop("_src", None)
    with open(f"/tmp/chemistry-video/src/{ep}/data/slots.json", "w",
              encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("\n写入 slots.json")


if __name__ == "__main__":
    main()
