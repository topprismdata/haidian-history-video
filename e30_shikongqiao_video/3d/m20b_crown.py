#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""M20b 冠部带解剖: 端孔/中央孔 环带径向宽 + 冠上拱肩厚 正射测量.
任务背景: facts.RING_T=0.40(STALE) vs masonry.RING_T=0.54 分叉, 端孔 extrados
穿桥面 4cm 真伪裁决 —— 测量优先: 环带宽(=券脸径向宽)与拱肩厚(冠内缘→桥面线)
都按"照片像素证据+误差棒"直读, 判读矩阵后才许改数.

子命令:
  crops POSETAG A0,A1,...          -> 冠部放大正射 + 模型特征线(诊断用)
  scan  POSETAG A0,A1,... [RINGREF]-> 主测量: 法向强度剖面边缘 -> JSON
判据: 全部"基准无关"(datum-free) —— 环带宽 = extrados边-intrados边(同射线),
拱肩厚 = 桥面线-intrados冠点(同一竖直线), 不依赖绝对 z 基准.
"""
import json
import math
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from m20_pipeline import (Model, load_ctrl, load_pose, Kmat, project, OUT)  # noqa

RING_MASONRY = 0.54   # masonry.RING_T (券石账目真值, 现行几何)
RING_FACTS = 0.40     # facts.RING_T (STALE 分叉侧)


def pose_pack(tag):
    cand = [os.path.join(OUT, "%s.json" % tag), os.path.join(OUT, "pose_%s.json" % tag)]
    p = json.load(open(next(c for c in cand if os.path.exists(c))))
    img_p = p["image"]
    if not os.path.exists(img_p):
        # /tmp/e30_m20C 绝对路径 -> 本树 refs 软链
        img_p = os.path.join(HERE, "refs", img_p.split("/3d/refs/")[-1])
    img = cv2.imread(img_p)
    assert img is not None, "cannot read %s (from %s)" % (img_p, p["image"])
    rv = np.array(p["rvec"], np.float64)
    tv = np.array(p["tvec"], np.float64)
    K = Kmat(p["f"], p["w"], p["h"])
    return p, rv, tv, K, img


def wall_pt(model, x, z, side):
    return np.array([x, side * model.hw(x, z), z], np.float64)


def wall_up(model, x, z, side):
    """墙面竖向切向(沿墙面走上): dz=1, dy=side*dhw/dz. 归一化.
    墙面收分 22°: hw=(DOWN+(UP-DOWN)*f)/2, f=(z-BOTTOM)/(deck-BOTTOM)."""
    deck = model.deck_z(x)
    dhwdz = (model.c["DECK_UP_W"] - model.c["DECK_DOWN_W"]) / (
        2.0 * (deck - model.c["BODY_BOTTOM"]))
    v = np.array([0.0, side * dhwdz, 1.0])
    return v / np.linalg.norm(v)


def radial_surf(model, x, i, side):
    """intrados 外法向在墙面面上的方向: n2=(-dzdx,1)/L (xz 剖面),
    投影到墙面切平面: (n2x, n2z*dywall/dz, n2z). 归一化."""
    import facts as F
    xc, spz, a, b = model.arch(i)
    d = F.arch_dzdx(x, xc, spz, a, b)
    L = math.hypot(d, 1.0)
    nx, nz = -d / L, 1.0 / L
    deck = model.deck_z(x)
    dhwdz = (model.c["DECK_UP_W"] - model.c["DECK_DOWN_W"]) / (
        2.0 * (deck - model.c["BODY_BOTTOM"]))
    v = np.array([nx, nz * side * dhwdz, nz])
    return v / np.linalg.norm(v)


model_ = None  # set in main


def sample_profile(img, K, rv, tv, p0, n3, s_range, step=0.01):
    """沿 3D 射线 p0 + s*n3 采样灰度. 返回 (s 数组, 灰度数组, 各点px)."""
    ss = np.arange(s_range[0], s_range[1] + 1e-9, step)
    pts = p0[None, :] + ss[:, None] * n3[None, :]
    uv = project(pts, K, rv, tv)
    h, w = img.shape[:2]
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    vals = np.full(len(ss), np.nan, np.float32)
    ok = (uv[:, 0] >= 1) & (uv[:, 0] < w - 2) & (uv[:, 1] >= 1) & (uv[:, 1] < h - 2)
    u = uv[ok, 0]; v = uv[ok, 1]
    u0 = np.floor(u).astype(int); v0 = np.floor(v).astype(int)
    fu = (u - u0).astype(np.float32); fv = (v - v0).astype(np.float32)
    vv = (g[v0, u0] * (1 - fu) * (1 - fv) + g[v0, u0 + 1] * fu * (1 - fv)
          + g[v0 + 1, u0] * (1 - fu) * fv + g[v0 + 1, u0 + 1] * fu * fv)
    vals[ok] = vv
    return ss, vals, uv


def px_per_m(K, rv, tv, p0, direction):
    """p0 处沿 direction(单位3D向量) 每 m 的像素位移."""
    eps = 0.05
    a = project(p0[None, :], K, rv, tv)[0]
    b = project((p0 + eps * direction)[None, :], K, rv, tv)[0]
    return float(np.hypot(*(b - a))) / eps


def subpeak(g, i0, sign=+1, half=2):
    """梯度峰值亚像素: 抛物线顶点. sign=+1 找最大."""
    if i0 < half or i0 >= len(g) - half:
        return float(i0)
    y0, y1, y2 = g[i0 - half], g[i0], g[i0 + half]
    den = (y0 - 2 * y1 + y2)
    if abs(den) < 1e-9:
        return float(i0)
    delta = 0.5 * (y0 - y2) / den
    if abs(delta) > half:
        return float(i0)
    return i0 + delta


def find_edges(ss, vals, s_intra, scale_pm):
    """在法向剖面上找: intrados边(暗→亮) 与 后续边(extrados/桥面).
    返回 dict(s_edge 列表, 每个附强度跳变量)."""
    v = vals.copy()
    ok = ~np.isnan(v)
    if ok.sum() < 10:
        return None
    idx = np.where(ok)[0]
    # 填充 + 平滑
    vv = v.copy()
    vv[~ok] = np.interp(ss[~ok], ss[ok], v[ok])
    k = max(3, int(round(0.03 * scale_pm)) | 1)  # ~3cm 平滑核
    ker = np.ones(k, np.float32) / k
    sm = np.convolve(vv, ker, mode="same")
    gr = np.gradient(sm) / (ss[1] - ss[0])  # per m
    out = []
    # intrados: s_intra 之前是洞内(暗), 第一个强上升沿
    i_in = int(np.searchsorted(ss, s_intra))
    lo, hi = max(0, i_in - int(round(0.15 * scale_pm / (ss[1] - ss[0])))), len(ss) - 1
    seg = gr[lo:hi]
    if len(seg) < 3:
        return None
    i1 = lo + int(np.argmax(seg))
    s1 = subpeak(gr, i1)
    out.append(("intrados", float(ss[int(round(s1))]), float(gr[i1])))
    # 后续边: intrados 之后全部显著下降沿(亮→暗)与上升沿候选, 取能量最强的
    # 下降沿 = extrados(环带外缘) 或 桥面线(墙顶→栏杆/天空)
    j0 = i1 + max(2, int(round(0.06 * scale_pm / (ss[1] - ss[0]))))
    seg2 = gr[j0:]
    if len(seg2) < 3:
        return out
    i2 = j0 + int(np.argmin(seg2))
    if gr[i2] < -0.35 * gr[i1] and gr[i2] < -20.0:  # 显著负边(至少 intrados 边强的35%, 绝对下限)
        s2 = subpeak(-gr, i2)
        out.append(("outer", float(ss[int(round(s2))]), float(gr[i2])))
    return out


def crop_crown(model, p, rv, tv, K, img, i, ppm, sx_half=1.6, zup=1.6, zdn=0.6,
               rings=(RING_MASONRY, RING_FACTS), tag=""):
    """冠部放大正射: 双线性重采样到 (x,z) 立面 + 模型特征线."""
    side = int(p["side"])
    xc, spz, a, b = model.arch(i)
    zc = model.intrados_z(xc, i)
    x0, x1 = xc - sx_half * a, xc + sx_half * a
    z1 = zc + zup
    z0 = zc - zdn
    W = int(round((x1 - x0) * ppm)); H = int(round((z1 - z0) * ppm))
    xs = x0 + (np.arange(W) + 0.5) / ppm
    zs = z1 - (np.arange(H) + 0.5) / ppm
    P = np.empty((H, W, 3), np.float64)
    P[..., 0] = xs[None, :]; P[..., 2] = zs[:, None]
    P[..., 1] = side * model.hw(P[..., 0], P[..., 2])
    uv = project(P.reshape(-1, 3), K, rv, tv).reshape(H, W, 2)
    h, w = img.shape[:2]
    u = uv[..., 0]; v = uv[..., 1]
    valid = (u >= 0) & (u <= w - 2) & (v >= 0) & (v <= h - 2)
    u0 = np.clip(np.floor(u).astype(int), 0, w - 2); v0 = np.clip(np.floor(v).astype(int), 0, h - 2)
    fu = (u - u0).astype(np.float32); fv = (v - v0).astype(np.float32)
    outim = np.zeros((H, W, 3), np.uint8)
    for c in range(3):
        ch = img[..., c].astype(np.float32)
        outim[..., c] = (ch[v0, u0] * (1 - fu) * (1 - fv) + ch[v0, u0 + 1] * fu * (1 - fv)
                         + ch[v0 + 1, u0] * (1 - fu) * fv + ch[v0 + 1, u0 + 1] * fu * fv).astype(np.uint8)
    outim[~valid] = (outim[~valid] * 0.25).astype(np.uint8)
    ext = (x0, x1, z0, z1, ppm)

    def xz2px(x, z):
        return (x - x0) * ppm, (z1 - z) * ppm

    im = outim.copy()
    # 网格 0.5m
    xx = math.ceil(x0 * 2) / 2
    while xx <= x1:
        u_, _ = xz2px(xx, 0)
        cv2.line(im, (int(u_), 0), (int(u_), H - 1), (60, 60, 60), 1)
        xx += 0.5
    zz = math.ceil(z0 * 2) / 2
    while zz <= z1:
        _, v_ = xz2px(0, zz)
        cv2.line(im, (0, int(v_)), (W - 1, int(v_)), (60, 60, 60), 1)
        cv2.putText(im, "%.1f" % zz, (3, int(v_) - 3), 0, 0.45, (0, 255, 255), 1)
        zz += 0.5
    ys = np.linspace(x0, x1, 300)
    def poly(fn, col, th=1):
        pts = []
        for x in ys:
            z = fn(float(x))
            if z0 <= z <= z1:
                u_, v_ = xz2px(x, z)
                pts.append((int(u_), int(v_)))
        if len(pts) > 2:
            cv2.polylines(im, [np.array(pts)], False, col, th, cv2.LINE_AA)

    def extr_z(x, rt):
        import facts as F
        xc0, spz0, a0, b0 = model.arch(i)
        d = F.arch_dzdx(x, xc0, spz0, a0, b0)
        Ln = math.hypot(d, 1.0)
        return model.intrados_z(x, i) + rt / Ln

    poly(lambda x: model.intrados_z(x, i), (255, 210, 0), 1)          # intrados
    poly(lambda x: extr_z(x, RING_MASONRY), (0, 130, 255), 1)         # 橙: 0.54 法向
    poly(lambda x: extr_z(x, RING_FACTS), (0, 220, 0), 1)             # 绿: 0.40 法向
    # 桥面线(墙面顶)
    xd = np.linspace(max(x0, -75), min(x1, 75), 300)
    pts = []
    for x in xd:
        z = model.deck_z(float(x))
        if z0 <= z <= z1:
            u_, v_ = xz2px(x, z)
            pts.append((int(u_), int(v_)))
    if len(pts) > 2:
        cv2.polylines(im, [np.array(pts)], False, (255, 0, 255), 1, cv2.LINE_AA)
    cv2.putText(im, "arch%d %s ppm=%.0f cyan=intrados orange=+0.54 green=+0.40 magenta=deck"
                % (i, tag, ppm), (8, H - 8), 0, 0.55, (255, 255, 255), 1)
    return im, ext

def cmd_crops(tag, arches, ppm=None):
    model = model_
    p, rv, tv, K, img = pose_pack(tag)
    for i in arches:
        xc, spz, a, b = model.arch(i)
        zc = model.intrados_z(xc, i)
        # 本孔竖向 px/m -> 输出 ppm = min(源分辨率上限, 160)
        s_pm = px_per_m(K, rv, tv, wall_pt(model, xc, zc, int(p["side"])),
                        wall_up(model, xc, zc, int(p["side"])))
        use = min(s_pm, 160.0) if ppm is None else ppm
        im, ext = crop_crown(model, p, rv, tv, K, img, i, use, tag=tag)
        fn = os.path.join(OUT, "m20b_crown_%s_a%d.png" % (tag, i))
        cv2.imwrite(fn, im)
        print("%s scale_z=%.1fpx/m -> %dx%d" % (fn, s_pm, im.shape[1], im.shape[0]))


def cmd_scan(tag, arches):
    """主测量: 每孔冠部多列法向剖面 -> intrados/外缘/桥面边 -> JSON."""
    model = model_
    p, rv, tv, K, img = pose_pack(tag)
    side = int(p["side"])
    res = {"pose": tag, "image": os.path.basename(p["image"]), "f": p["f"],
           "rms": p.get("rms"), "side": side, "arches": {}}
    for i in arches:
        xc, spz, a, b = model.arch(i)
        zc = model.intrados_z(xc, i)
        deck_c = model.deck_z(xc)
        s_pm = px_per_m(K, rv, tv, wall_pt(model, xc, zc, side), wall_up(model, xc, zc, side))
        # 冠部 ±0.55a 范围逐列(列距 0.1m)
        cols = []
        x = xc - 0.55 * a
        while x <= xc + 0.55 * a + 1e-9:
            zi = model.intrados_z(float(x), i)
            n = radial_surf(model, float(x), i, side)
            p0 = wall_pt(model, float(x), zi, side)
            ss, vals, _ = sample_profile(img, K, rv, tv, p0, n, (-0.25, 2.2))
            edges = find_edges(ss, vals, 0.0, s_pm)
            row = {"x": round(float(x - xc), 3),
                   "scale_px_per_m": round(s_pm, 1)}
            if edges:
                s_in = edges[0][1]
                row["s_intrados"] = round(s_in, 4)
                row["edge_in_strength"] = round(edges[0][2], 1)
                if len(edges) > 1:
                    row["s_outer"] = round(edges[1][1], 4)
                    row["ring_w_m"] = round(edges[1][1] - s_in, 4)
            cols.append(row)
            x += 0.10
        # 冠点竖直剖面到桥面上方: 拱肩测量(xc±0.25a)
        span_rows = []
        for dx in (-0.25 * a, 0.0, 0.25 * a):
            x = xc + dx
            zi = model.intrados_z(float(x), i)
            p0 = wall_pt(model, float(x), zi, side)
            ss, vals, _ = sample_profile(img, K, rv, tv, p0, wall_up(model, float(x), zi, side),
                                         (-0.25, deck_c - zi + 1.6))
            edges = find_edges(ss, vals, 0.0, s_pm)
            row = {"dx_a": round(dx / a, 2)}
            if edges:
                row["s_intrados"] = round(edges[0][1], 4)
                last = edges[-1]
                if len(edges) > 1:
                    row["s_deck"] = round(last[1], 4)
                    row["spandrel_m"] = round(last[1] - edges[0][1], 4)
            span_rows.append(row)
        res["arches"][str(i)] = {
            "scale_z_px_per_m": round(s_pm, 1),
            "crown_intrados_model_z": round(zc, 3),
            "deck_model_z_at_xc": round(deck_c, 3),
            "cols": cols, "spandrel_rows": span_rows}
        rs = [c.get("ring_w_m") for c in cols if c.get("ring_w_m") is not None]
        sps = [r.get("spandrel_m") for r in span_rows if r.get("spandrel_m") is not None]
        def med(v):
            return (float(np.median(v)), float(1.4826 * np.median(np.abs(v - np.median(v))))) if v else (None, None)
        rm, rmad = med(rs); sm, smad = med(sps)
        res["arches"][str(i)].update({
            "ring_w_med_m": None if rm is None else round(rm, 3),
            "ring_w_mad_m": None if rmad is None else round(rmad, 3),
            "ring_n": len(rs),
            "spandrel_med_m": None if sm is None else round(sm, 3),
            "spandrel_mad_m": None if smad is None else round(smad, 3),
            "spandrel_n": len(sps)})
        print("a%-2d ring=%.3f±%.3f (n=%d)  spandrel=%.3f±%.3f (n=%d)  scale=%.1fpx/m"
              % (i, rm or -1, rmad or -1, len(rs), sm or -1, smad or -1, len(sps), s_pm))
    fn = os.path.join(OUT, "m20b_crown_scan_%s.json" % tag)
    with open(fn, "w") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)
    print("wrote", fn)


def cmd_prof(tag, arch, xs):
    """原始法向剖面打印(探测设计用): 每 x 列 s 从 -0.2 到 2.2m 步长 0.02, 值缩放 0-9."""
    model = model_
    p, rv, tv, K, img = pose_pack(tag)
    side = int(p["side"])
    xc, spz, a, b = model.arch(arch)
    s_pm = px_per_m(K, rv, tv, wall_pt(model, xc, model.intrados_z(xc, arch), side),
                    wall_up(model, xc, model.intrados_z(xc, arch), side))
    for dx in [float(t) for t in xs.split(",")]:
        x = xc + dx
        zi = model.intrados_z(float(x), arch)
        n = radial_surf(model, float(x), arch, side)
        p0 = wall_pt(model, float(x), zi, side)
        ss, vals, _ = sample_profile(img, K, rv, tv, p0, n, (-0.20, 2.20), step=0.02)
        line = "".join(" .:-=+*#%@@"[int(min(9, max(0, v / 25.6)))] if not np.isnan(v) else "?"
                       for v in vals)
        print("dx=%+5.2f  s=-0.2->2.2m (%.0fpx/m)" % (dx, s_pm))
        print("       |%s|" % line)
        print("        s=0 @ col %d; 0.54m @ col %d; 1.0m @ col %d"
              % (int(0.20 / 0.02), int((0.20 + 0.54) / 0.02), int(1.20 / 0.02)))


def grad_field(img):
    """灰度 + Sobel 梯度幅值(亚像素双线性采样用)."""
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    gx = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3)
    return g, gx, gy


def bilin(chan, u, v, w, h):
    u0 = np.floor(u).astype(int); v0 = np.floor(v).astype(int)
    ok = (u0 >= 0) & (u0 < w - 2) & (v0 >= 0) & (v0 < h - 2)
    u0c = np.clip(u0, 0, w - 2); v0c = np.clip(v0, 0, h - 2)
    fu = (u - u0c).astype(np.float32); fv = (v - v0c).astype(np.float32)
    out = (chan[v0c, u0c] * (1 - fu) * (1 - fv) + chan[v0c, u0c + 1] * fu * (1 - fv)
           + chan[v0c + 1, u0c] * (1 - fu) * fv + chan[v0c + 1, u0c + 1] * fu * fv)
    out[~ok] = np.nan
    return out


def curve_score(model, tag_pose, gx, gy, w, h, i, mode, param, x_lo=None, x_hi=None,
                n_s=110):
    """曲线边缘对齐分: mode='ring' param=环带宽(m), mode='deck' param=桥面线竖移(m).
    score = 有效样本 |grad| 中位数(整体曲线一致性, 径向缝/孤立噪声被中位数压掉)."""
    p, rv, tv, K, img = tag_pose
    side = int(p["side"])
    xc, spz, a, b = model.arch(i)
    if x_lo is None:
        x_lo, x_hi = xc - 0.75 * a, xc + 0.75 * a
    xs = np.linspace(x_lo, x_hi, n_s)
    pts = np.empty((n_s, 3))
    for k, x in enumerate(xs):
        zi = model.intrados_z(float(x), i)
        if mode == "ring":
            n = radial_surf(model, float(x), i, side)
            d = param / math.sqrt(1.0 + _dzdx2(model, float(x), i))
            pts[k] = wall_pt(model, float(x), zi, side) + d * n
        else:
            zd = model.deck_z(float(x)) + param
            pts[k] = wall_pt(model, float(x), zd, side)
    uv = project(pts, K, rv, tv)
    gmag = np.sqrt(bilin(gx, uv[:, 0], uv[:, 1], w, h) ** 2 +
                   bilin(gy, uv[:, 0], uv[:, 1], w, h) ** 2)
    gmag = gmag[~np.isnan(gmag)]
    if len(gmag) < n_s * 0.5:
        return None
    return float(np.median(gmag)), float(np.mean(gmag)), len(gmag)


def _dzdx2(model, x, i):
    import facts as F
    xc, spz, a, b = model.arch(i)
    return F.arch_dzdx(x, xc, spz, a, b) ** 2


def sweep_axis(model, tag_pose, gf, i, mode, lo, hi, step, x_lo, x_hi):
    g, gx, gy, w, h = gf
    grid = np.arange(lo, hi + 1e-9, step)
    sc = []
    for t in grid:
        r = curve_score(model, tag_pose, gx, gy, w, h, i, mode, float(t), x_lo, x_hi)
        sc.append(r[0] if r else np.nan)
    sc = np.array(sc)
    ok = ~np.isnan(sc)
    if ok.sum() < len(grid) * 0.6:
        return None
    k = int(np.nanargmax(sc))
    # 抛物线亚像素
    if 0 < k < len(grid) - 1:
        y0, y1, y2 = sc[k - 1], sc[k], sc[k + 1]
        den = y0 - 2 * y1 + y2
        delta = 0.5 * (y0 - y2) / den if abs(den) > 1e-9 else 0.0
        delta = float(np.clip(delta, -1, 1))
    else:
        delta = 0.0
    t_best = float(grid[k] + delta * step)
    # 峰显著度: 峰值/本底(去掉峰±3格后的中位), 与半高全宽
    bg = np.nanmedian(np.delete(sc, np.arange(max(0, k - 3), min(len(sc), k + 4))))
    half = sc[k] - (sc[k] - bg) / 2.0
    above = np.where(sc >= half)[0]
    fwhm = float(grid[above[-1]] - grid[above[0]]) if len(above) else float("nan")
    return {"best": round(t_best, 4), "peak": round(float(sc[k]), 1),
            "bg": round(float(bg), 1), "contrast": round(float(sc[k] / max(bg, 1e-6)), 3),
            "fwhm": round(fwhm, 4), "grid": grid.tolist(), "score": np.round(sc, 1).tolist()}


def cmd_sweep(tag, arches):
    model = model_
    p, rv, tv, K, img = pose_pack(tag)
    gf = (*grad_field(img), p["w"], p["h"])
    side = int(p["side"])
    out = {"pose": tag, "image": os.path.basename(p["image"]), "f": p["f"],
           "rms": p.get("rms"), "side": side, "arches": {}}
    for i in arches:
        xc, spz, a, b = model.arch(i)
        zi_c = model.intrados_z(xc, i)
        deck_c = model.deck_z(xc)
        # 环带: 肩部扫(外缘与桥面线在肩部可分)
        ring = sweep_axis(model, (p, rv, tv, K, img), gf, i, "ring",
                          0.25, 0.85, 0.01, xc - 0.78 * a, xc + 0.78 * a)
        # 桥面线竖移: 冠部±0.55a
        deck = sweep_axis(model, (p, rv, tv, K, img), gf, i, "deck",
                          -0.45, 0.65, 0.01, xc - 0.55 * a, xc + 0.55 * a)
        s_pm = px_per_m(K, rv, tv, wall_pt(model, xc, zi_c, side),
                        wall_up(model, xc, zi_c, side))
        rec = {"scale_z_px_per_m": round(s_pm, 1),
               "model_D_crown": round(deck_c - zi_c, 3),
               "ring_sweep": ring, "deck_sweep": deck}
        if ring and deck:
            D_meas = (deck_c + deck["best"]) - zi_c
            rec["D_crown_meas"] = round(D_meas, 3)
            rec["spandrel_wall_if_ring"] = round(D_meas - ring["best"], 3)
            rec["pokes_above_deck"] = bool(ring["best"] > D_meas)
        out["arches"][str(i)] = rec
        if ring and deck:
            print("a%-2d ring=%.3f (peak/bg=%.2f fwhm=%.3f)  deckΔ=%+.3f (fwhm=%.3f)  "
                  "D=%.3f  spandrel_wall=%.3f%s"
                  % (i, ring["best"], ring["contrast"], ring["fwhm"], deck["best"],
                     deck["fwhm"], rec["D_crown_meas"], rec["spandrel_wall_if_ring"],
                     "  穿面" if rec["pokes_above_deck"] else ""))
        else:
            print("a%-2d ring=%s deck=%s (sweep 不可用)" % (i, bool(ring), bool(deck)))
    fn = os.path.join(OUT, "m20b_crown_sweep_%s.json" % tag)
    with open(fn, "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print("wrote", fn)


def main():
    global model_
    model_ = Model(load_ctrl())
    cmd = sys.argv[1]
    if cmd == "crops":
        cmd_crops(sys.argv[2], [int(t) for t in sys.argv[3].split(",")],
                  ppm=float(sys.argv[4]) if len(sys.argv) > 4 else None)
    elif cmd == "prof":
        cmd_prof(sys.argv[2], int(sys.argv[3]), sys.argv[4])
    elif cmd == "sweep":
        cmd_sweep(sys.argv[2], [int(t) for t in sys.argv[3].split(",")])
    elif cmd == "scan":
        cmd_scan(sys.argv[2], [int(t) for t in sys.argv[3].split(",")])
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
