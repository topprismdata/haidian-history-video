#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""p2017 终版位姿: M18 仿射锚(sx=34.1, sy=181, 冠(2167,1340)) -> 逐列暗边自动采样
(带模型 x 对应, 无沿曲线滑动自由度) -> 7 参透视拟合 -> pose_p2017.json。
M18 仿射在 274 点 0.76px 验证; M19 新曲线仅改 z 数值, 像素映射不变。
"""
import json
import math
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from m20_pipeline import Model, load_ctrl, OUT  # noqa: E402
from m20_fitcurves import cam_R, proj  # noqa: E402
from scipy.optimize import least_squares  # noqa: E402

SX, SY, U0, V0 = 34.1, 181.0, 2167.0, 1340.0   # M18 冠点锚(该照片)


def sample_curve(model, i, side, img_gray, xr_grid, win=150.0, u_off=0.0):
    """逐列在仿射预测 v 附近找 暗边(石->洞) 亚像素行。返回 [(x,z,u,v)]。"""
    a = model.arches[i]
    out = []
    for xr in xr_grid:
        x = a["xc"] + xr
        z = model.intrados_z(x, i)
        u_aff = U0 + SX * x + u_off
        v_aff = V0 + SY * (a["spz"] + a["b"] - z)
        u = int(round(u_aff))
        v_lo = int(max(1, v_aff - win))
        v_hi = int(min(img_gray.shape[0] - 7, v_aff + win))
        if v_hi - v_lo < 20 or u < 3 or u > img_gray.shape[1] - 4:
            continue
        col = img_gray[:, u].astype(float)
        best, bv = -1e9, None
        for v in range(v_lo, v_hi):
            above = col[v - 6:v - 1].mean()
            below = col[v + 2:v + 7].mean()
            drop = above - below
            if drop > best:
                best, bv = drop, v
        if bv is None or best < 12.0:
            continue
        d1, d2, d3 = col[bv - 1], col[bv], col[bv + 1]
        den = d1 - 2 * d2 + d3
        off = 0.5 * (d1 - d3) / den if abs(den) > 1e-9 else 0.0
        off = max(-1.0, min(1.0, off))
        out.append((x, side * model.hw(x, z), z, float(u_aff), bv + off, best))
    return out


def main():
    image = "refs/community_photos_details/2017-05-20_A_closer_view_of_the_17-arch_bridge.jpg"
    model = Model(load_ctrl())
    img = cv2.imread(image)
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    side = -1
    xr = list(np.arange(-0.72, 0.721, 0.05))
    samples = {}
    # B 孔(拱9) 冠点实测 2485 vs 仿射 2523: 逐孔 u 偏置(透视尺度差)
    UOFF = {8: 0.0, 9: 2485.0 - (U0 + SX * 10.443), 7: 2485.0 - (U0 + SX * (-10.444))}
    for i in (8, 9):
        s = sample_curve(model, i, side, gray, xr, u_off=UOFF[i])
        samples[i] = s
        print("arch %d: %d samples (u_off %.1f)" % (i, len(s), UOFF[i]))
    # 7 参相机拟合(直接重投影残差)
    P, UV = [], []
    for i, s in samples.items():
        for (x, y, z, u, v, cf) in s:
            P.append((x, y, z))
            UV.append((u, v))
    P = np.array(P, np.float64)
    UV = np.array(UV, np.float64)

    def res(p):
        return (proj(p, P, w, h) - UV).ravel()

    best = None
    a8 = model.arches[8]
    zr = a8["spz"] + a8["b"]
    yr = side * model.hw(a8["xc"], zr)
    Pref = np.array([a8["xc"], yr, zr])
    for D in (40.0, 55.0, 70.0, 90.0, 120.0, 170.0, 250.0):
        for azd in (8.0, 11.0, 14.0):
            az = math.radians(azd)
            dirv = np.array([math.cos(az), math.sin(az), 0.0])
            C = Pref - D * dirv
            for f in (D * 160.0, D * 181.0, D * 205.0):
                p0 = np.array([az, 0.0, C[0], C[1], C[2], f, 0.0])
                try:
                    r = least_squares(res, p0, loss="soft_l1", f_scale=5.0,
                                      max_nfev=3000)
                except Exception:
                    continue
                rr = res(r.x)
                rms = float(np.sqrt(np.mean(rr ** 2)))
                if best is None or rms < best[0]:
                    best = (rms, r.x.copy())
    rms, p = best
    pr = proj(p, P, w, h)
    resv = np.linalg.norm(pr - UV, axis=1)
    print("FINAL rms=%.2fpx med=%.2f max=%.2f n=%d f=%.0f" %
          (rms, np.median(resv), resv.max(), len(P), p[5]))
    # ── 对应仿射(线性, 无滑动自由度): M18 验证法的自动化 ──
    aff = {}
    for i in samples:
        S = samples[i]
        A = np.array([[x, z, 1.0] for (x, y, z, u, v, cf) in S])
        ru = np.linalg.lstsq(A, np.array([u for s5 in S for u in [s5[3]]]), rcond=None)[0] \
            if False else np.linalg.lstsq(A, np.array([s5[3] for s5 in S]), rcond=None)[0]
        rv = np.linalg.lstsq(A, np.array([s5[4] for s5 in S]), rcond=None)[0]
        eu = A @ ru - np.array([s5[3] for s5 in S])
        ev = A @ rv - np.array([s5[4] for s5 in S])
        er = np.hypot(eu, ev)
        keep = er < max(6.0, 2.5 * np.median(er))
        ru = np.linalg.lstsq(A[keep], np.array([s5[3] for s5, k in zip(S, keep) if k]), rcond=None)[0]
        rv = np.linalg.lstsq(A[keep], np.array([s5[4] for s5, k in zip(S, keep) if k]), rcond=None)[0]
        eu = A[keep] @ ru - np.array([s5[3] for s5, k in zip(S, keep) if k])
        ev = A[keep] @ rv - np.array([s5[4] for s5, k in zip(S, keep) if k])
        err = float(np.hypot(eu, ev).mean())
        aff[i] = (ru, rv, err, int(keep.sum()), len(S))
        print("affine arch %d: rms=%.2fpx kept %d/%d sx=%.2f" %
              (i, err, keep.sum(), len(S), ru[0]))
    affout = {}
    for i in aff:
        affout[str(i)] = {"u": [float(t) for t in aff[i][0]],
                          "v": [float(t) for t in aff[i][1]],
                          "rms": aff[i][2], "kept": aff[i][3], "n": aff[i][4]}
    json.dump(affout, open(os.path.join(OUT, "affine_p2017.json"), "w"), indent=1)
    # 可视化
    vis = img.copy()
    for i in (7, 8, 9):
        uv = proj(p, curve_pts_all(model, i, side), w, h).astype(np.int32)
        cv2.polylines(vis, [uv], False, (0, 255, 255), 2)
    for (x, y, z, u, v, cf) in sum(samples.values(), []):
        cv2.circle(vis, (int(u), int(v)), 3, (0, 0, 255), 1)
    small = cv2.resize(vis, (1900, int(1900 * h / w)))
    cv2.imwrite(os.path.join(OUT, "pose_p2017_vis.jpg"), small,
                [cv2.IMWRITE_JPEG_QUALITY, 88])
    R = cam_R(p[0], p[1], p[6])
    C = np.array(p[2:5])
    rv, _ = cv2.Rodrigues(R)
    tv = -R @ C
    json.dump({"image": image, "w": w, "h": h, "side": side,
               "f": float(p[5]), "rvec": rv.reshape(3).tolist(),
               "tvec": tv.reshape(3).tolist(), "rms": rms, "n": len(P),
               "params": list(map(float, p)),
               "per_arch": {str(i): len(samples[i]) for i in samples}},
              open(os.path.join(OUT, "pose_p2017.json"), "w"), indent=1)
    print("saved pose_p2017.json")


def curve_pts_all(model, i, side, n=140, span=0.99):
    a = model.arches[i]
    out = []
    for k in range(n):
        xr = -a["a"] * span + 2 * a["a"] * span * k / (n - 1)
        x = a["xc"] + xr
        z = model.intrados_z(x, i)
        out.append((x, side * model.hw(x, z), z))
    return np.array(out, np.float64)


if __name__ == "__main__":
    main()
