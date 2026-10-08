#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""冬照冠线逐孔校验(拱线族返工验收件, 2026-10-08)。

对指定位姿照片的每个可测孔: 沿模型 intrados 冠部带(±0.35a)采样, 投影到照片,
在曲线法向 ±WIN_PX 窗内找 石亮->洞暗 亚像素边界, 输出逐孔法向偏移 med/MAD(px)。
判读: 冠 z 由 rise 决定, 族返工(rise 零改动)后应与返工前同分布; med 恶化即停。

用法: python3 m20_crownline_check.py POSETAG a0,a1,... [--win 10]
"""
import json
import math
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from m20_pipeline import Model, load_ctrl, project, OUT  # noqa: E402
from m20b_crown import pose_pack, wall_pt, grad_field, bilin  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
TAG = argv[0]
ARCHES = [int(t) for t in argv[1].split(",")]
WIN_PX = float(argv[3]) if len(argv) > 3 and argv[2] == "--win" else 10.0


def curve_normal2d(p0, p1):
    d = np.array(p1) - np.array(p0)
    n = np.array([-d[1], d[0]])
    return n / max(1e-9, np.linalg.norm(n))


def main():
    model = Model(load_ctrl())
    p, rv, tv, K, img = pose_pack(TAG)
    side = int(p["side"])
    g, gx, gy = grad_field(img)
    h, w = img.shape[:2]
    out = {"pose": TAG, "image": os.path.basename(p["image"]), "win_px": WIN_PX,
           "arches": {}}
    for i in ARCHES:
        xc, spz, a, b = model.arch(i)
        xs = np.linspace(xc - 0.35 * a, xc + 0.35 * a, 41)
        pts3 = [wall_pt(model, float(x), model.intrados_z(float(x), i), side)
                for x in xs]
        uv = project(np.array(pts3, np.float64), K, rv, tv)
        offs = []
        for k in range(1, len(uv)):
            n2 = curve_normal2d(uv[k - 1], uv[k])
            # 法向朝洞内(暗侧): 指向画面下方(洞口在拱腹线下)
            if n2[1] < 0:
                n2 = -n2
            u0, v0 = uv[k]
            ss = np.arange(-WIN_PX, WIN_PX + 0.25, 0.25)
            us = u0 + n2[0] * ss
            vs = v0 + n2[1] * ss
            gmag = np.sqrt(bilin(gx, us, vs, w, h) ** 2 +
                           bilin(gy, us, vs, w, h) ** 2)
            lum = bilin(g, us, vs, w, h)
            if np.all(np.isnan(gmag)):
                continue
            kEdge = int(np.nanargmax(gmag))
            if gmag[kEdge] < 15.0:
                continue
            # 石(亮, s<0 侧)->洞(暗, s>0 侧)极性: 亮侧均值须高于暗侧
            lo = np.nanmean(lum[:kEdge]) if kEdge else np.nan
            hi = np.nanmean(lum[kEdge + 2:]) if kEdge + 2 < len(lum) else np.nan
            if not (np.isfinite(lo) and np.isfinite(hi)) or lo - hi < 10.0:
                continue
            y1, y2, y3 = gmag[kEdge - 1], gmag[kEdge], gmag[kEdge + 1]
            den = y1 - 2 * y2 + y3
            frac = 0.5 * (y1 - y3) / den if abs(den) > 1e-9 else 0.0
            offs.append(float(ss[kEdge] + frac * 0.25))
        if offs:
            arr = np.array(offs)
            med = float(np.median(arr))
            mad = float(1.4826 * np.median(np.abs(arr - med)))
            out["arches"][str(i)] = {"n": len(offs), "med_px": round(med, 2),
                                     "mad_px": round(mad, 2)}
            print("a%-2d n=%3d med=%+6.2fpx mad=%5.2fpx" % (i, len(offs), med, mad))
        else:
            out["arches"][str(i)] = {"n": 0, "med_px": None, "mad_px": None}
            print("a%-2d n=0 (无可检边)" % i)
    meds = [v["med_px"] for v in out["arches"].values() if v["med_px"] is not None]
    if meds:
        out["global_med_px"] = round(float(np.median(meds)), 2)
        print("GLOBAL med over %d arches: %+.2fpx" % (len(meds), out["global_med_px"]))
    fn = os.path.join(OUT, "crownline_check_%s.json" % TAG)
    json.dump(out, open(fn, "w"), indent=1, ensure_ascii=False)
    print("wrote", fn)


if __name__ == "__main__":
    main()
