#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""closer_2017 位姿 v3: 8 点 PnP(4 冠 + 4 檐口, 破共线) -> snap-intrados 退火精化.
最终位姿只由拱腹边缘决定(檐口仅用于初始化, 防桥面循环论证).
身份假设对照: A=a0 / A=a1.
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
import m20b_c2017 as B  # noqa

model_ = B.model_
IMG = B.IMG
F_EXIF = 14614.0

APEX = {0: (2140.0, 1332.0), 1: (2485.0, 1198.0),
        2: (2855.0, 1118.0), 3: (3190.0, 1052.0)}
# 檐口线(顶层挑檐顶缘) 手读: img_x -> raw y; 3D x 用其下方可见拱的桥轴 x(仅初始化用)
CORN = [(2000.0, 990.0, -72.0), (2400.0, 953.0, -64.0),
        (2800.0, 925.0, -56.0), (3200.0, 907.0, -48.0)]


def crown3d(i, side):
    xc, spz, a, b = model_.arch(i)
    return np.array([xc, side * model_.hw(xc, spz + b), spz + b])


def cornice3d(x, side):
    z = model_.deck_z(x)
    return np.array([x, side * model_.hw(x, z), z])


def init_pnp(mapping, side, w, h):
    K = Kmat(F_EXIF, w, h)
    P3, P2 = [], []
    for k, u in APEX.items():
        P3.append(crown3d(mapping[k], side)); P2.append(u)
    # 檐口 3D x 跟随身份: 置于各可见拱冠正上方
    for (ix, v, _), k in zip(CORN, sorted(APEX)):
        xc_, spz_, a_, b_ = model_.arch(mapping[k])
        P3.append(cornice3d(xc_, side)); P2.append((ix, v))
    P3 = np.array(P3); P2 = np.array(P2, float)
    ok, rv, tv = cv2.solvePnP(P3, P2, K, None, flags=cv2.SOLVEPNP_SQPNP)
    pr = project(P3, K, rv, tv)
    res = np.sqrt(np.sum((pr - P2) ** 2, 1))
    R, _ = cv2.Rodrigues(rv); C = -R.T @ tv
    return {"image": IMG, "w": w, "h": h, "side": int(side), "f": F_EXIF,
            "rvec": rv.reshape(3).tolist(), "tvec": tv.reshape(3).tolist(),
            "rms": float(np.sqrt(np.mean(res ** 2))), "n": len(P3),
            "C_world": np.asarray(C).ravel().tolist()}, res


def polarity_ok(pose, mapping, w, h):
    """拱腹极性: 内侧(-0.05..-0.2m 法向)应比外侧(+0.05..+0.2m)暗 ≥10 灰阶,
    且 ≥60% 采样成立 —— 防锁到砌缝/影线."""
    img = cv2.imread(IMG)
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    K = Kmat(pose["f"], w, h)
    rv = np.array(pose["rvec"]); tv = np.array(pose["tvec"])
    side = int(pose["side"])
    good_all = []
    for k in mapping:
        i = mapping[k]
        xc, spz, a, b = model_.arch(i)
        xs = np.linspace(xc - 0.85 * a, xc + 0.85 * a, 25)
        import facts as F
        okay = 0; tot = 0
        for x in xs:
            zi = model_.intrados_z(float(x), i)
            d = F.arch_dzdx(float(x), xc, spz, a, b)
            Ln = math.hypot(d, 1.0)
            n_in = np.array([d / Ln, 0.0, -1.0 / Ln])   # 内法向(指洞内)
            P0 = np.array([x, side * model_.hw(float(x), zi), zi])
            pts_in = P0[None, :] + np.arange(0.05, 0.21, 0.02)[:, None] * n_in[None, :]
            pts_out = P0[None, :] - np.arange(0.05, 0.21, 0.02)[:, None] * n_in[None, :]
            def samp(P):
                uv = project(P, K, rv, tv)
                u = np.clip(uv[:, 0], 0, w - 2); v = np.clip(uv[:, 1], 0, h - 2)
                return g[v.astype(int), u.astype(int)]
            vi, vo = samp(pts_in), samp(pts_out)
            tot += 1
            if vi.mean() < vo.mean() - 10:
                okay += 1
        good_all.append(okay / max(tot, 1))
    return good_all


def main():
    img = cv2.imread(IMG)
    h, w = img.shape[:2]
    out = {}
    trials = []
    for s in (0, 1, 2, 3):
        m = {k: v + s for k, v in {0: 0, 1: 1, 2: 2, 3: 3}.items()}
        trials.append(("A%dmapN" % s, m, 1.0))
        trials.append(("A%dmapS" % s, m, -1.0))
    for name, mapping, side in trials:
        p0, res0 = init_pnp(mapping, side, w, h)
        pol = polarity_ok(p0, mapping, w, h)
        print("%s init: rms=%.1fpx C=(%.1f,%.1f,%.1f) 极性=%s" %
              (name, p0["rms"], p0["C_world"][0], p0["C_world"][1], p0["C_world"][2],
               [round(t, 2) for t in pol]), flush=True)
        if p0["rms"] > 60 or min(pol) < 0.6:
            print("  init 过差或极性不符, 跳过")
            continue
        B.render_wire(p0, os.path.join(OUT, "c2017_init_%s.jpg" % name), arches=range(0, 9))
        # snap 退火: 窗口 0.8 -> 0.5 -> 0.35 -> 0.3, 每档 3 轮 PnP 交替
        pose = dict(p0)
        obs = []
        for win in (0.8, 0.5, 0.35, 0.3):
            B.HALF_WIN = win
            pose, obs = B.refine(pose, list(range(0, 7)), iters=3, fix_f=F_EXIF)
        R, _ = cv2.Rodrigues(np.array(pose["rvec"]))
        C = -R.T @ np.array(pose["tvec"])
        pose["C_world"] = C.tolist()
        okphys = (0.5 < C[2] < 45.0) and (-150 < C[0] < 40) and (-150 < C[1] < 40)
        print("  refined: rms=%.2f n=%d C=(%.1f,%.1f,%.1f) ok=%s"
              % (pose.get("rms") or -1, pose.get("n") or 0, *C, okphys))
        if okphys:
            fn = "c2017_fit_%s.jpg" % name
            B.render_wire(pose, os.path.join(OUT, fn), arches=range(0, 9))
            # 逐孔快照残差
            K = Kmat(pose["f"], w, h)
            rv = np.array(pose["rvec"]); tv = np.array(pose["tvec"])
            from collections import defaultdict
            by = defaultdict(list)
            for P3s, uv, i, dx in obs:
                pr = project(P3s[None, :], K, rv, tv)[0]
                by[i].append(float(np.hypot(*(pr - uv))))
            pose["snap_resid"] = {str(i): {"med": round(float(np.median(v)), 2),
                                           "max": round(float(max(v)), 2), "n": len(v)}
                                  for i, v in sorted(by.items())}
            pose["exif_fpx"] = F_EXIF
            pose["method"] = "cornice+apex PnP init, intrados snap anneal refine (f=EXIF)"
            pose["init_mapping"] = name
            out[name] = pose
    with open(os.path.join(OUT, "m20b_pose_c2017.json"), "w") as fp:
        json.dump(out, fp, indent=1)
    print("saved %d 假设" % len(out))


if __name__ == "__main__":
    main()
