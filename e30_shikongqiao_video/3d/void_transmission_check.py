#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""渲染级洞形透光闸(void transmission gate; 拱线族返工清债 2026-10-08)。

对正交侧视渲(ortho.py side)逐孔采样【开口内网格】(intrados 内偏 0.15-0.45m,
springer+0.10 以上), 检验亮度分布: 洞若凿通 → 内部为暗四分位主导(双峰);
布尔静默失败(实心墙) → 全部 ≈ 墙面亮(单峰)。判据: 暗样本占比 dark_frac
< 0.30 → 该孔红(未透)。

用法:
  python3 void_transmission_check.py <ortho_side.png> [--json out.json]
依赖: 3d/out/print/section5/BASE_SPEC.md 不需要; 只读 facts/geom_math。
退出码: 0 = 全孔透; 1 = 有孔未透(红)。
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import facts as F  # noqa: E402
import geom_math as GM  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
PNG = argv[0]
OUT_JSON = None
if "--json" in argv:
    OUT_JSON = argv[argv.index("--json") + 1]

W, H = 1600, 672
ORTHO_SCALE = 165.0
CAMZ = 3.5
WALL_BAND_Z = (3.0, 4.5)      # 墩身实体基准带(孔间 x=±10.4 墩)


def main():
    im = np.asarray(Image.open(PNG).convert("L"), dtype=float)
    H_img, W_img = im.shape
    scale = W_img / ORTHO_SCALE
    cx, cy = W_img / 2.0, H_img / 2.0

    def px(x, z):
        return (int(round(cx + x * scale)), int(round(cy + (CAMZ - z) * scale)))

    # 墙面基准: 墩中心=PIER_X 值本身(±5.335/±15.552/…, 墩宽 2.17 取 ±0.5),
    # z 带 2.5-5.0 = 实体墩身(孔间)。注意 (PIER_X[k]+PIER_X[k+1])/2 是孔心!
    refs = []
    for k in range(1, F.N_SPAN):
        x0 = GM.PIER_X[k]
        if abs(x0) > 70:
            continue
        for z in np.arange(2.5, 5.0 + 1e-9, 0.25):
            for dx in (-0.5, 0.0, 0.5):
                u, v = px(x0 + dx, z)
                if 0 <= v < H_img and 0 <= u < W_img:
                    refs.append(im[v, u])
    wall = float(np.median(refs))
    thr = wall * 0.4              # 暗判: 低于墙面 40%(洞内=暗/透背景)
    out = {"png": os.path.basename(PNG), "wall_median": round(wall, 1),
           "dark_thr": round(thr, 1), "arches": {}}
    n_red = 0
    for i in range(F.N_SPAN):
        xc = GM.arch_center_x(i)
        a = GM.SPANS[i] / 2.0
        b = GM.arch_rise(i)
        spz = GM.arch_springer_z(i)
        d, R = F.arch_circle(a, b)
        vals = []
        # 开口内网格: x ∈ xc±0.75a, z ∈ spz+0.15 .. 弧下 0.15
        for fx in np.linspace(-0.75, 0.75, 15):
            x = xc + fx * a
            z_arc = spz + d + math.sqrt(max(0.0, R * R - (x - xc) ** 2))
            for fz in np.linspace(0.15, max(0.16, (z_arc - spz) - 0.15), 7):
                u, v = px(x, spz + fz)
                if 0 <= v < H_img and 0 <= u < W_img:
                    vals.append(im[v, u])
        if not vals:
            out["arches"]["ARCH%02d" % (i + 1)] = {"n": 0, "verdict": "skip"}
            continue
        arr = np.array(vals)
        dark = float((arr < thr).mean())
        verdict = "open" if dark >= 0.30 else "NOT-THROUGH"
        if verdict != "open":
            n_red += 1
        out["arches"]["ARCH%02d" % (i + 1)] = {
            "n": len(arr), "dark_frac": round(dark, 2),
            "median": round(float(np.median(arr)), 1), "verdict": verdict}
    fails = {k: v for k, v in out["arches"].items() if v.get("verdict") == "NOT-THROUGH"}
    print("透光闸: wall=%.1f thr=%.1f | 未透孔 %d/17 %s"
          % (wall, thr, n_red, json.dumps(fails, ensure_ascii=False)
             if fails else "(全透)"))
    if OUT_JSON:
        json.dump(out, open(OUT_JSON, "w"), ensure_ascii=False, indent=1)
    sys.exit(1 if n_red else 0)


if __name__ == "__main__":
    main()
