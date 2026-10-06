#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""M20 deck 消减(K 角色铺石谱): 消点+截面单应, 无全局位姿。
输入: 帧 + 粗标(消点估计/截面/ curb 搜索带/梁柱 u) -> 
  1) vy: 横缝线束交点; vx: 纵线束交点
  2) 每截面 1D 单应(y: curbL=-3.28, curbR=+3.28); 特征暗谷 -> y(m)
  3) 每开间横缝计数 -> 板长=2.381/N
输出 deck_reduce_<tag>.json + 标注叠加图。
"""
import json
import math
import os
import sys

import cv2
import numpy as np

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "m20_ctrl")


def dark_troughs(gray, u, v0, v1, win=9, drop=12.0):
    col = gray[v0:v1, u].astype(float)
    out = []
    for i in range(win, len(col) - win):
        loc = col[i - win:i + win + 1]
        if col[i] == loc.min() and col[i] < loc.mean() - drop:
            # 亚像素: 抛物线
            d1, d2, d3 = col[i - 1], col[i], col[i + 1]
            den = d1 - 2 * d2 + d3
            off = 0.5 * (d1 - d3) / den if abs(den) > 1e-9 else 0.0
            out.append((v0 + i + off, float(col[i])))
    # 非极大值抑制(≥4px)
    keep = []
    for v, val in out:
        if keep and v - keep[-1][0] < 4:
            if val < keep[-1][1]:
                keep[-1] = (v, val)
        else:
            keep.append((v, val))
    return keep


def line_fit(pts):
    pts = np.array(pts, np.float64)
    A = np.stack([pts[:, 0], np.ones(len(pts))], 1)
    k, b = np.linalg.lstsq(A, pts[:, 1], rcond=None)[0]
    return k, b


def main():
    image, tag, cfg_path = sys.argv[1], sys.argv[2], sys.argv[3]
    cfg = json.load(open(cfg_path))
    img = cv2.imread(image)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    H, W = gray.shape
    vis = img.copy()

    # 1) vy: 横缝线段拟合求交(最小二乘线束)
    vlines = []
    for seg in cfg["transverse_segs"]:  # [[u1,v1,u2,v2],...] 沿横缝的人工粗线
        p = np.array(seg, np.float64).reshape(2, 2)
        d = p[1] - p[0]
        n = np.array([-d[1], d[0]]); n /= np.linalg.norm(n)
        c = float(n @ p[0])
        vlines.append((n, c))
        p1 = (int(seg[0]), int(seg[1])); p2 = (int(seg[2]), int(seg[3]))
        cv2.line(vis, p1, p2, (0, 255, 0), 1)
    N = np.array([n for n, c in vlines])
    Cc = np.array([c for n, c in vlines])
    _, _, vt = np.linalg.svd(np.stack([N[:, 0] * N[:, 0], N[:, 0] * N[:, 1],
                                       N[:, 1] * N[:, 1],
                                       N[:, 0] * Cc, N[:, 1] * Cc,
                                       Cc * Cc], 1), full_matrices=False)
    h = vt[-1]
    A2 = np.array([[h[0], h[1]], [h[1], h[2]]]); b2 = -np.array([h[3], h[4]])
    try:
        vy_pt = np.linalg.solve(A2, b2)
    except np.linalg.LinAlgError:
        vy_pt = np.array([W / 2.0, H / 2.0])
    vx_pt = cfg.get("vx_hint", None)

    # 2) curb 线: 每 section 在搜索带内取暗谷, 线性外推一致者保留
    sections = {}
    curb_rows = {"L": [], "R": []}
    for sec in cfg["sections"]:
        u = sec["u"]
        for s in ("L", "R"):
            v0, v1 = sec["curb_" + s]
            tr = dark_troughs(gray, u, v0, v1)
            if tr:
                # 取带内最接近线性趋势的谷: 首轮取最深
                v, val = min(tr, key=lambda t: t[1])
                curb_rows[s].append((u, v, val))
                sections.setdefault(u, {})["curb_" + s] = v
    # curb 线拟合 + 二轮重选
    fitk = {}
    for s in ("L", "R"):
        rows = [(u, v) for u, v, val in curb_rows[s]]
        fitk[s] = line_fit(rows)
    for sec in cfg["sections"]:
        u = sec["u"]
        for s in ("L", "R"):
            v0, v1 = sec["curb_" + s]
            k, b = fitk[s]
            tr = dark_troughs(gray, u, v0, v1)
            if not tr:
                continue
            v, val = min(tr, key=lambda t: abs(t[0] - (k * u + b)))
            if abs(v - (k * u + b)) < 6:
                sections.setdefault(u, {})["curb_" + s] = v
                cv2.circle(vis, (u, int(v)), 3, (0, 0, 255), 1)

    # 3) 截面 1D 单应: 已知 curbL=-3.28 curbR=+3.28, vy 为 y 方向消点(v 有限点)
    #    直线坐标系: 截面竖直线上点 (u,v), 单应 w(v)=(a v + b)/(c v + 1) -> y(m)
    #    三个已知: (vL,-3.28),(vR,3.28),(vy, inf => c*vy+1=0 => c=-1/vy_v)
    out_secs = {}
    for u, d in sorted(sections.items()):
        if "curb_L" not in d or "curb_R" not in d:
            continue
        vL, vR = d["curb_L"], d["curb_R"]
        vyv = vy_pt[1]
        # 解 (a,b): w(vL)=-3.28 w(vR)=3.28, c=-1/vyv
        c = -1.0 / vyv
        A = np.array([[vL, 1.0], [vR, 1.0]])
        yvec = np.array([-3.28 - 0, 3.28]) - 0  # w=a v+b (c 项并入常数移项)
        # w = (a v + b)/(c v + 1) => a v + b = y (c v + 1)
        A2 = np.array([[vL, 1.0], [vR, 1.0]])
        rhs = np.array([-3.28 * (c * vL + 1), 3.28 * (c * vR + 1)])
        a, bb = np.linalg.solve(A2, rhs)
        feats = []
        for (fv0, fv1, name) in sec.get("features", []):
            tr = dark_troughs(gray, u, fv0, fv1)
            for v, val in tr:
                y = (a * v + bb) / (c * v + 1)
                feats.append({"name": name, "v": float(v), "y": float(y),
                              "dark": val})
                cv2.circle(vis, (u, int(v)), 2, (255, 0, 255), 1)
        out_secs[u] = {"curb_L": vL, "curb_R": vR,
                       "a": float(a), "b": float(bb), "c": float(c),
                       "features": feats}
    # 4) 每开间横缝计数(沿给定带扫描横缝谷)
    bays = []
    for bay in cfg.get("bays", []):
        # bay: {"u0","u1","band_v0","band_v1"} 近似矩形带(近场)
        cnt = []
        for u in range(int(bay["u0"]), int(bay["u1"])):
            tr = dark_troughs(gray, u, bay["band_v0"], bay["band_v1"], win=6, drop=10)
            cnt.append(len(tr))
        n_med = int(np.median(cnt))
        bays.append({"bay": bay.get("name", ""), "n": n_med,
                     "spacing_m": (2.381 / n_med) if n_med else None})
    json.dump({"vy": [float(vy_pt[0]), float(vy_pt[1])],
               "sections": out_secs, "bays": bays},
              open(os.path.join(OUT, "deck_reduce_%s.json" % tag), "w"), indent=1)
    cv2.imwrite(os.path.join(OUT, "deck_reduce_%s.jpg" % tag), vis,
                [cv2.IMWRITE_JPEG_QUALITY, 90])
    for u, d in sorted(out_secs.items()):
        print("section u=%d curb=(%.1f,%.1f)" % (u, d["curb_L"], d["curb_R"]))
        for f in d["features"]:
            print("   %-10s v=%7.1f y=%+.3f m (dark %d)" % (f["name"], f["v"], f["y"], f["dark"]))
    for b in bays:
        print("bay %-8s n=%d spacing=%s" % (b["bay"], b["n"], b["spacing_m"]))


if __name__ == "__main__":
    main()
