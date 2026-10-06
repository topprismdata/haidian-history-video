#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""M20 位姿初始化 v2: 人工曲线标记(点到曲线距离) + 降参相机(az,el,Cx,Cy,Cz,f,roll)
多起点拟合, 同时搜索孔号身份假设 (A,B) 与脸侧 side。输出 pose_<tag>.json。
"""
import itertools
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from m20_pipeline import Model, load_ctrl, OUT  # noqa: E402

IMG_W = IMG_H = None


def cam_R(az, el, roll):
    fwd = np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)])
    up = np.array([0.0, 0.0, 1.0])
    right = np.cross(fwd, up); right /= np.linalg.norm(right)
    down = np.cross(fwd, right)
    R = np.vstack([right, down, fwd])
    cr, sr = math.cos(roll), math.sin(roll)
    Rr = np.array([[cr, -sr, 0], [sr, cr, 0], [0, 0, 1.0]])
    return Rr @ R


def proj(params, P, w, h):
    az, el, Cx, Cy, Cz, f, roll = params
    R = cam_R(az, el, roll)
    Pc = (np.asarray(P, np.float64) - np.array([Cx, Cy, Cz])) @ R.T
    z = Pc[:, 2]
    ok = z > 2.0
    u = np.where(ok, f * Pc[:, 0] / np.maximum(z, 1e-6) + w / 2.0, 1e7)
    v = np.where(ok, f * Pc[:, 1] / np.maximum(z, 1e-6) + h / 2.0, 1e7)
    return np.stack([u, v], 1)


def curve_pts(model, i, side, n=120, span=0.985):
    a = model.arches[i]
    out = []
    for k in range(n):
        xr = -a["a"] * span + 2 * a["a"] * span * k / (n - 1)
        x = a["xc"] + xr
        z = model.intrados_z(x, i)
        out.append((x, side * model.hw(x, z), z))
    return np.array(out, np.float64)


def pt_polyline_dist(uv, poly):
    """uv (m,2) 到折线 poly (n,2) 的最小距离。"""
    d = np.linalg.norm(uv[:, None, :] - poly[None, :, :], axis=2)
    return d.min(axis=1)


def fit(model, marks, hyp, side, w, h, seeds, verbose=False):
    ia, ib = hyp
    curves = {"A": curve_pts(model, ia, side), "B": curve_pts(model, ib, side)}
    marr = [(m, curves[m["slot"]]) for m in marks]

    def res(p):
        out = []
        for m, cp in marr:
            uv = proj(p, cp, w, h)
            q = np.array([[m["u"], m["v"]]], np.float64)
            out.append(pt_polyline_dist(q, uv)[0])
        return np.array(out)

    best = None
    from scipy.optimize import least_squares
    for s0 in seeds:
        try:
            r = least_squares(res, np.array(s0, np.float64), loss="soft_l1",
                              f_scale=6.0, max_nfev=150)
        except Exception:
            continue
        rms = float(np.sqrt(np.mean(res(r.x) ** 2)))
        if best is None or rms < best[0]:
            best = (rms, r.x.copy())
    # 二阶段: 最优邻域精化
    for s0 in [best[1],
               best[1] * np.array([1, 1, 1.05, 1, 1, 1.1, 1]),
               best[1] * np.array([1, 1, 0.95, 1, 1, 0.9, 1])]:
        try:
            r = least_squares(res, np.array(s0, np.float64), loss="soft_l1",
                              f_scale=6.0, max_nfev=2500)
        except Exception:
            continue
        rms = float(np.sqrt(np.mean(res(r.x) ** 2)))
        if rms < best[0]:
            best = (rms, r.x.copy())
    return best


def m18_seeds(model, ia, side):
    """由 M18 仿射标定反推的弱透视相机种子(该照片上 0.76px 残差验证过):
    sy=181px/m(正视), sx=34px/m(斜视) -> 光轴与立面夹 ~11°; 冠点 A 锚 (2167,1340)。"""
    a = model.arches[ia]
    z_ref = a["spz"] + a["b"]
    y_ref = side * model.hw(a["xc"], z_ref)
    P_ref = np.array([a["xc"], y_ref, z_ref])
    seeds = []
    for azd in (9.0, 11.0, 13.0):
        for D in (50.0, 65.0, 80.0, 100.0):
            for el in (-2.0, 0.0, 2.0, 4.0):
                az = math.radians(azd) * (1 if side < 0 else -1)
                elr = math.radians(el)
                f = D * 181.0
                dirv = np.array([math.cos(elr) * math.cos(az),
                                 math.cos(elr) * math.sin(az), math.sin(elr)])
                C = P_ref - D * dirv
                seeds.append([az, elr, C[0], C[1], C[2], f, 0.0])
    return seeds


def main():
    image = sys.argv[1]
    tag = sys.argv[2]
    # 标记文件: {"marks":[{"arch":i,"u":..,"v":..}], "arch_a":..,"arch_b":..}
    cfg = json.load(open(sys.argv[3]))
    model = Model(load_ctrl())
    import cv2
    img = cv2.imread(image)
    h, w = img.shape[:2]
    marks = cfg["marks"]
    hyps = [tuple(v) for v in cfg.get("hyps", [[8, 9], [9, 8], [8, 7], [7, 8],
                                               [9, 10], [7, 6]])]
    results = []
    for side in cfg.get("sides", [-1]):
        seeds = m18_seeds(model, hyps[0][0], side)
        for hyp in hyps:
            b = fit(model, marks, hyp, side, w, h, seeds)
            if b is None:
                continue
            rms, p = b
            results.append((rms, hyp, side, p))
            print("hyp A%d,B%d side=%+d rms=%.2fpx az=%.1f° el=%.1f° C=(%.1f,%.1f,%.1f) f=%.0f roll=%.2f°"
                  % (hyp[0], hyp[1], side, rms, math.degrees(p[0]) % 360,
                     math.degrees(p[1]), p[2], p[3], p[4], p[5], math.degrees(p[6])))
    results.sort(key=lambda r: r[0])
    rms, hyp, side, p = results[0]
    print("BEST: hyp=%s side=%+d rms=%.2fpx" % (hyp, side, rms))
    # 可视化
    curves_vis = img.copy()
    for i in set(hyp) | {hyp[0] + 1, hyp[0] - 1, hyp[1] + 1, hyp[1] - 1}:
        if 0 <= i < 17:
            uv = proj(p, curve_pts(model, i, side), w, h).astype(np.int32)
            cv2.polylines(curves_vis, [uv], False, (0, 255, 255), 2)
            uv = proj(p, curve_pts(model, i, side, span=1.16), w, h).astype(np.int32)
            cv2.polylines(curves_vis, [uv], False, (255, 0, 255), 1)
    for m in marks:
        cv2.circle(curves_vis, (int(m["u"]), int(m["v"])), 6, (0, 0, 255), 2)
    small = cv2.resize(curves_vis, (1900, int(1900 * h / w)))
    cv2.imwrite(os.path.join(OUT, "fit_%s.jpg" % tag), small,
                [cv2.IMWRITE_JPEG_QUALITY, 88])
    json.dump({"rms": rms, "hyp": list(hyp), "side": side,
               "params": list(map(float, p)), "w": w, "h": h, "image": image},
              open(os.path.join(OUT, "fit_%s.json" % tag), "w"), indent=1)


if __name__ == "__main__":
    main()
