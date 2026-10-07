#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""closer_2017 位姿 v2: 5 参数 (C,az,el) 全局 Powell 多起点 -> snap+PnP(f=EXIF)
有界精化 + 物理约束拒绝 + 身份假设对照 (A=a0 / A=a1).
判据独立性: 位姿只用拱腹曲线(冠点粗 + snap 细), 不碰桥面线(它是测量目标, 防循环).
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
import m20b_c2017 as B  # noqa

model_ = B.model_
IMG = B.IMG
F_EXIF = 14614.0

OBS = {0: (2140.0, 1332.0), 1: (2485.0, 1198.0),
       2: (2855.0, 1118.0), 3: (3190.0, 1052.0)}


def crown3d(i, side):
    xc, spz, a, b = model_.arch(i)
    return np.array([xc, side * model_.hw(xc, spz + b), spz + b])


def resid5(p, side, f, w, h, mapping):
    Cx, Cy, Cz, az, el = p
    if Cz < 0.5:
        return np.full(8, 1e4)
    pose = B.pack([Cx, Cy, Cz], az, el, f, w, h)
    K = Kmat(f, w, h)
    rv = np.array(pose["rvec"]); tv = np.array(pose["tvec"])
    out = []
    for k, (u, v) in OBS.items():
        P = crown3d(mapping[k], side)
        pr = project(P[None, :], K, rv, tv)[0]
        out.extend([pr[0] - u, pr[1] - v])
    return np.array(out)


def global_init(side, w, h, mapping):
    best = []
    # 多起点: 网格 + Powell
    for Cx0 in (-130, -110, -95, -82):
        for Cy0 in (-70, -45, -25):
            for Cz0 in (3.0, 6.0):
                # az 初值: 从 C 看 A 冠, 加粗略 u 偏置
                PA = crown3d(mapping[0], side)
                d = PA - np.array([Cx0, Cy0, Cz0])
                az0 = math.atan2(d[1], d[0]) + 0.10
                el0 = math.atan2(d[2], math.hypot(d[0], d[1])) + 0.01
                p0 = np.array([Cx0, Cy0, Cz0, az0, el0])
                r = minimize(lambda p: float(np.sum(resid5(p, side, F_EXIF, w, h, mapping) ** 2)),
                             p0, method="Powell",
                             options={"maxiter": 3000, "xtol": 1e-4, "ftol": 1e-6})
                c = float(np.sum(resid5(r.x, side, F_EXIF, w, h, mapping) ** 2))
                best.append((c, r.x.copy()))
    best.sort(key=lambda t: t[0])
    return best[:4]


def snap_refine(pose0, arches, fix_f, w, h, win0=0.6):
    """窗口退火 snap+PnP: 先宽窗(0.6m)再收紧(0.3m). C_z 物理界外则拒绝."""
    pose = dict(pose0)
    for win in (win0, 0.4, 0.3, 0.3):
        B.half_win_m = win  # snap_edges 的默认参改由全局注入
        pose, obs = B.refine(pose, arches, iters=3, fix_f=fix_f)
    R, _ = cv2.Rodrigues(np.array(pose["rvec"]))
    C = -R.T @ np.array(pose["tvec"])
    pose["C_world"] = C.tolist()
    ok = (0.5 < C[2] < 40.0) and (-130 < C[0] < 40) and (-130 < C[1] < 20)
    return pose, obs, ok, C


def main():
    img = cv2.imread(IMG)
    h, w = img.shape[:2]
    results = {}
    for name, mapping, side in [("A0map", {0: 0, 1: 1, 2: 2, 3: 3}, -1.0),
                                ("A1map", {0: 1, 1: 2, 2: 3, 3: 4}, -1.0),
                                ("A0mapN", {0: 0, 1: 1, 2: 2, 3: 3}, 1.0)]:
        inits = global_init(side, w, h, mapping)
        print("%s 粗解 top: %s" % (name, ["%.0f" % c for c, _ in inits]))
        for gi, (c, p) in enumerate(inits[:2]):
            pose0 = B.pack(list(p[:3]), p[3], p[4], F_EXIF, w, h)
            pose_f, obs, ok, C = snap_refine(pose0, list(range(0, 7)), F_EXIF, w, h)
            print("  init%d cost=%.0f -> final rms=%.2f n=%d ok=%s C=(%.1f,%.1f,%.1f)"
                  % (gi, c, pose_f.get("rms") or -1, pose_f.get("n") or 0, ok, *C))
            if ok and (name not in results or (pose_f.get("rms") or 9e9) < results[name]["pose"].get("rms", 9e9)):
                B.render_wire(pose_f, os.path.join(OUT, "c2017_fit_%s.jpg" % name),
                              arches=range(0, 9))
                results[name] = {"pose": pose_f, "init_cost": c}
    keep = {k: {"pose": v["pose"], "init_cost": v["init_cost"]} for k, v in results.items()}
    with open(os.path.join(OUT, "m20b_pose_c2017_all.json"), "w") as fp:
        json.dump(keep, fp, indent=1)
    for k, v in keep.items():
        pp = v["pose"]
        print("%s: rms=%.2f f=%.0f C=%s" % (k, pp.get("rms") or -1, pp.get("f") or -1,
                                            np.round(pp.get("C_world", [0, 0, 0]), 1)))


if __name__ == "__main__":
    main()
