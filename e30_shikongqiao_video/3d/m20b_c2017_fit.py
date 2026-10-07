#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""closer_2017 位姿: 边距变换自动寻优(Nelder-Mead) + 快照PnP精化.
score = mean(DT at projected intrados samples, arches 0..6) + 离框惩罚.
"""
import json
import math
import os
import sys

import cv2
import numpy as np
from scipy.optimize import minimize

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from m20_pipeline import Model, load_ctrl, Kmat, project, OUT  # noqa
import m20b_c2017 as B  # noqa (pack/render_wire/refine/snap_edges)

IMG = B.IMG
model_ = B.model_


def edge_dt():
    img = cv2.imread(IMG)
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # 暗洞边界为主: Canny 高低门限取中
    e = cv2.Canny(g, 40, 120)
    dt = cv2.distanceTransform(255 - e, cv2.DIST_L2, 3).astype(np.float32)
    return img, dt


def pose_from_params(p, w, h):
    Cx, Cy, Cz, az, el, f = p
    return B.pack([Cx, Cy, Cz], az, el, f, w, h)


def score(p, dt, w, h, arches):
    pose = pose_from_params(p, w, h)
    K = Kmat(pose["f"], w, h)
    rv = np.array(pose["rvec"]); tv = np.array(pose["tvec"])
    side = -1
    pts = []
    for i in arches:
        xc, spz, a, b = model_.arch(i)
        xs = np.linspace(xc - 0.9 * a, xc + 0.9 * a, 25)
        for x in xs:
            z = model_.intrados_z(float(x), i)
            pts.append([x, side * model_.hw(float(x), z), z])
    pts = np.array(pts)
    uv = project(pts, K, rv, tv)
    ok = (uv[:, 0] >= 0) & (uv[:, 0] < w - 1) & (uv[:, 1] >= 0) & (uv[:, 1] < h - 1)
    if ok.sum() < 0.7 * len(pts):
        return 60.0
    u = np.clip(uv[ok, 0], 0, w - 2).astype(int)
    v = np.clip(uv[ok, 1], 0, h - 2).astype(int)
    dvals = dt[v, u]
    return float(np.mean(dvals)) + 20.0 * (1 - ok.mean())


def main():
    img, dt = edge_dt()
    h, w = img.shape[:2]
    arches = list(range(0, 7))
    inits = [
        [-98, -47, 4.0, 1.05, -0.013, 14614],
        [-105, -40, 5.0, 0.95, -0.02, 14614],
        [-92, -52, 3.0, 1.12, -0.008, 14614],
        [-98, -47, 4.0, 1.05, -0.013, 13000],
    ]
    best = None
    for p0 in inits:
        r = minimize(score, np.array(p0, float), args=(dt, w, h, arches),
                     method="Nelder-Mead",
                     options={"maxiter": 600, "xatol": 0.05, "fatol": 0.02})
        print("init", [round(t, 3) for t in p0], "-> score %.2f @ %s"
              % (r.fun, [round(t, 3) for t in r.x]))
        if best is None or r.fun < best.fun:
            best = r
    p = best.x
    print("BEST score=%.2f C=(%.1f,%.1f,%.2f) az=%.4f el=%.4f f=%.0f"
          % (best.fun, p[0], p[1], p[2], p[3], p[4], p[5]))
    pose = pose_from_params(p, w, h)
    B.render_wire(pose, os.path.join(OUT, "c2017_nm.jpg"), arches=range(0, 8))
    # 快照精化两轮: 一轮 EXIF 定焦, 一轮自由焦对照
    pose_fix, obs = B.refine(pose, arches, iters=4, fix_f=14614.0)
    print("fix_f rms=%.2f n=%d" % (pose_fix["rms"], pose_fix["n"]))
    pose_free, _ = B.refine(pose, arches, iters=4, fix_f=None)
    print("free_f rms=%.2f n=%d f=%.1f" % (pose_free["rms"], pose_free["n"], pose_free["f"]))
    pose_fix["exif_fpx"] = 14614.0
    pose_fix["method"] = "NM edge-DT coarse + snap-PnP refine (f=EXIF fixed)"
    with open(os.path.join(OUT, "m20b_pose_c2017.json"), "w") as fp:
        json.dump(pose_fix, fp, indent=1)
    B.render_wire(pose_fix, os.path.join(OUT, "c2017_fit.jpg"), arches=range(0, 8))
    B.render_wire(pose_free, os.path.join(OUT, "c2017_fit_free.jpg"), arches=range(0, 8))
    # 残差按孔统计
    from collections import defaultdict
    by = defaultdict(list)
    for P3, uv, i, dx in obs:
        K = Kmat(pose_fix["f"], pose_fix["w"], pose_fix["h"])
        pr = project(P3[None, :], K, np.array(pose_fix["rvec"]), np.array(pose_fix["tvec"]))[0]
        by[i].append(np.hypot(*(pr - uv)))
    for i in sorted(by):
        r = np.array(by[i])
        print("arch%d resid med=%.2f max=%.2f n=%d" % (i, np.median(r), r.max(), len(r)))


if __name__ == "__main__":
    main()
