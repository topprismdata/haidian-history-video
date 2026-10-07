#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""M20b 主测量: intrados 锚定差分法 (datum-free, pose 一阶误差免疫).
每列: 1) 模型拱腹曲线±0.25m 窗内定位真实 intrados 边(亚像素, 记录极性与强度)
      2) 从锚点沿墙面法向采强度剖面
      3) ring_w = s∈(0.26,0.82) 内显著边位置(m); D = s∈(Dm-0.35,Dm+0.35) 内显著边
   汇总: 列中位数±MAD + 双源交叉.
用法: python3 m20b_measure.py POSETAG a0,a1,... OUTTAG
"""
import json
import math
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from m20_pipeline import Model, load_ctrl, Kmat, project, OUT  # noqa
from m20b_crown import (pose_pack, wall_pt, wall_up, radial_surf, px_per_m,
                        grad_field, bilin)  # noqa
import facts as F  # noqa

RING_LO, RING_HI = 0.26, 0.82   # 环带先验窗(m, 覆盖 0.30-0.80 假设空间)


def subpix_edge(prof, ss, i0, half=2):
    y0, y1, y2 = prof[i0 - half], prof[i0], prof[i0 + half]
    den = y0 - 2 * y1 + y2
    if abs(den) < 1e-9:
        return float(i0)
    d = 0.5 * (y0 - y2) / den
    return i0 + float(np.clip(d, -half, half))


def scan_column(gx, gy, w, h, p3_intra, n3, K, rv, tv, s_max, step=0.008):
    """单列: 返回 dict(s_intra, pol_in, g_in, edges=[(s, grad, pol)...])."""
    ss = np.arange(-0.30, s_max, step)
    pts = p3_intra[None, :] + ss[:, None] * n3[None, :]
    uv = project(pts, K, rv, tv)
    gmag = np.sqrt(bilin(gx, uv[:, 0], uv[:, 1], w, h) ** 2 +
                   bilin(gy, uv[:, 0], uv[:, 1], w, h) ** 2)
    gsu = bilin(gx, uv[:, 0], uv[:, 1], w, h)
    gsv = bilin(gy, uv[:, 0], uv[:, 1], w, h)
    ok = ~np.isnan(gmag)
    if ok.sum() < len(ss) * 0.7:
        return None
    g = np.where(ok, gmag, 0.0).astype(np.float32)
    k = max(3, int(0.025 / step) | 1)
    ker = np.ones(k, np.float32) / k
    sm = np.convolve(g, ker, mode="same")
    # intrados: ±0.25m 窗内最强梯度
    i0a = int((0.0 - 0.25 - ss[0]) / step); i0b = int((0.0 + 0.25 - ss[0]) / step)
    i_in = i0a + int(np.argmax(sm[i0a:i0b]))
    s_in = ss[int(round(subpix_edge(sm, ss, i_in)))] if 1 < i_in < len(ss) - 2 else ss[i_in]
    # 极性: 沿法向的亮度方向 (gsu, gsv)·n3 在图像上的符号近似: 用灰度剖面符号
    return {"ss": ss, "gmag": sm, "s_in": float(s_in),
            "g_in": float(sm[i_in]), "uv": uv, "ok": ok}


def cmd_measure(tag, archstr, outtag):
    model = Model(load_ctrl())
    p, rv, tv, K, img = pose_pack(tag)
    g, gx, gy, w, h = (*grad_field(img), p["w"], p["h"])
    side = int(p["side"])
    out = {"pose": tag, "image": os.path.basename(img.__class__ and p["image"]),
           "f": p["f"], "rms": p.get("rms"), "side": side, "arches": {}}
    for ai in [int(t) for t in archstr.split(",")]:
        xc, spz, a, b = model.arch(ai)
        zc = model.intrados_z(xc, ai)
        deck_c = model.deck_z(xc)
        Dm = deck_c - zc
        s_pm = px_per_m(K, rv, tv, wall_pt(model, xc, zc, side),
                        wall_up(model, xc, zc, side))
        cols = []
        x = xc - 0.55 * a
        while x <= xc + 0.55 * a + 1e-9:
            zi = model.intrados_z(float(x), ai)
            n = radial_surf(model, float(x), ai, side)
            p3 = wall_pt(model, float(x), zi, side)
            r = scan_column(gx, gy, w, h, p3, n, K, rv, tv, Dm + 1.2)
            if r is not None:
                ss, gmag = r["ss"], r["gmag"]
                s_in = r["s_in"]
                # 环带边: (s_in+RING_LO, s_in+RING_HI) 窗内最强
                lo = np.searchsorted(ss, s_in + RING_LO)
                hi = np.searchsorted(ss, s_in + RING_HI)
                ring = None
                if hi - lo > 8:
                    i = lo + int(np.argmax(gmag[lo:hi]))
                    prom = gmag[i] - max(np.percentile(gmag[lo:i], 30) if i > lo else 0,
                                         0.0)
                    ring = (float(ss[int(round(subpix_edge(gmag, ss, i)))]), float(gmag[i]),
                            float(prom))
                # 桥面边: (Dm-0.35, Dm+0.35) 相对锚点
                lo2 = np.searchsorted(ss, s_in + max(0.30, Dm - 0.35))
                hi2 = np.searchsorted(ss, s_in + Dm + 0.35)
                deck = None
                if hi2 - lo2 > 8:
                    j = lo2 + int(np.argmax(gmag[lo2:hi2]))
                    deck = (float(ss[int(round(subpix_edge(gmag, ss, j)))]), float(gmag[j]))
                cols.append({"x_rel": round(float(x - xc), 3),
                             "s_in": round(s_in, 4),
                             "g_in": round(r["g_in"], 1),
                             "ring": None if ring is None else
                                    (round(ring[0] - s_in, 4), round(ring[1], 1)),
                             "deck": None if deck is None else
                                     (round(deck[0] - s_in, 4), round(deck[1], 1)),
                             "scale": round(s_pm, 1)})
            x += 0.08
        # 鲁棒汇总: 锚点对齐堆叠剖面(列中位), 径向缝/孤立噪点被中位压掉
        S = np.arange(-0.05, 1.85, 0.008)
        # 锚点对齐堆叠: 重放列, 存剖面
        stack_mat = []
        x = xc - 0.55 * a
        while x <= xc + 0.55 * a + 1e-9:
            zi = model.intrados_z(float(x), ai)
            n = radial_surf(model, float(x), ai, side)
            p3 = wall_pt(model, float(x), zi, side)
            r = scan_column(gx, gy, w, h, p3, n, K, rv, tv, Dm + 1.2)
            if r is not None:
                ss = r["ss"]
                prof = np.interp(S, ss - r["s_in"], r["gmag"],
                                 left=np.nan, right=np.nan)
                stack_mat.append(prof)
            x += 0.08
        rec = {"scale_z_px_per_m": round(s_pm, 1), "D_model": round(Dm, 3),
               "n_cols": len(cols)}
        if stack_mat:
            M = np.vstack(stack_mat)
            prof = np.nanmedian(M, axis=0)
            k = 5
            ker = np.ones(k) / k
            ps = np.convolve(np.nan_to_num(prof, nan=0.0), ker, mode="same")
            # 峰检测: 环带窗 / 桥面窗
            def peak(s_lo, s_hi):
                lo = np.searchsorted(S, s_lo); hi = np.searchsorted(S, s_hi)
                if hi - lo < 6:
                    return None
                i = lo + int(np.argmax(ps[lo:hi]))
                bg = float(np.median(ps[lo:hi]))
                return {"s": round(float(S[i]), 3), "g": round(float(ps[i]), 1),
                        "bg": round(bg, 1), "contrast": round(float(ps[i] / max(bg, 1e-6)), 2)}
            rec["stack_ring"] = peak(RING_LO, RING_HI)
            rec["stack_deck"] = peak(max(0.30, Dm - 0.45), Dm + 0.45)
            rec["stack_intra"] = {"s": 0.0, "g": round(float(ps[np.searchsorted(S, 0.02)]), 1)}
            rec["stack_profile"] = [round(float(t), 1) for t in ps[::4]]
            rec["stack_s_axis"] = [round(float(t), 3) for t in S[::4]]
        out["arches"][str(ai)] = rec
        rm = rec.get("stack_ring"); dm = rec.get("stack_deck")
        sw = None
        if rm and dm:
            sw = round(dm["s"] - rm["s"], 3)
            rec["spandrel_wall"] = sw
        print("a%-2d scale=%.0fpx/m ring=%s deck(Dm%.2f)=%s wall=%s"
              % (ai, s_pm,
                 "None" if not rm else "%.3f(c%.1f)" % (rm["s"], rm["contrast"]),
                 Dm, "None" if not dm else "%.3f(c%.1f)" % (dm["s"], dm["contrast"]),
                 "None" if sw is None else "%.3f" % sw))
    fn = os.path.join(OUT, "m20b_measure_%s.json" % outtag)
    with open(fn, "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print("wrote", fn)


def main():
    cmd_measure(sys.argv[1], sys.argv[2], sys.argv[3])


if __name__ == "__main__":
    main()
