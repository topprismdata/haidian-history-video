#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""m20b: A07 CCTV 链 v2. 橙光洞定位 -> 灰石环|洞内 (饱和度+明度) 边缘逐列
亚像素采样 -> 离散锚假设粗拟 -> (边缘关联 <-> solvePnP 焦扫) 迭代 ->
pose_<tag>.json + 质量报告(sx@arch7 决定 层界级/块级).
用法: python3 m20b_a07.py FRAME OUTTAG [side]
"""
import json
import math
import os
import sys

import cv2
import numpy as np
from scipy.optimize import least_squares

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from m20_pipeline import (Model, load_ctrl, OUT, Kmat, project, solve_pose)  # noqa
from m20_initpose import cam_model_proj  # noqa
from m20_fitcurves import cam_R  # noqa


def orange_blobs(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    H, S, V = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    mask = ((H >= 5) & (H <= 30) & (S > 90) & (V > 110)).astype(np.uint8) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,
                            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE,
                            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    out = []
    for k in range(1, n):
        x, y, w, h, area = stats[k]
        if area < 8000 or y < 430:      # 剔天空/亭子
            continue
        out.append({"u": float(x + w / 2), "v_apex": float(y), "w": int(w),
                    "h": int(h), "area": int(area)})
    out.sort(key=lambda d: -d["u"])
    return out, (H, S, V)



def apex_anchors(blobs, H, S, V, w, h):
    """逐列自橙顶上扫, 首个石质3连(H~100,S<90,V>95) = intrados 边.
    返回 [(u, v, blob_idx)]"""
    out = []
    for bi, b in enumerate(blobs):
        uc = int(round(b["u"]))
        for du in (-int(b["w"] * 0.25), -int(b["w"] * 0.12), 0,
                   int(b["w"] * 0.12), int(b["w"] * 0.25)):
            u = uc + du
            if u < 3 or u >= w - 3:
                continue
            va = int(b["v_apex"])
            run = 0
            for v in range(va - 2, max(8, va - 130), -1):
                stone = (85 <= H[v, u] <= 125 and S[v, u] < 90 and V[v, u] > 95)
                run = run + 1 if stone else 0
                if run >= 3:
                    out.append((float(u), float(v + run - 1 + 0.5), bi))
                    break
    return out


def intrados_samples(model, i, side, n=240):
    a = model.arches[i]
    P = []
    for k in range(n):
        xr = -a["a"] * 0.99 + 2 * a["a"] * 0.99 * k / (n - 1)
        x = a["xc"] + xr
        z = model.intrados_z(x, i)
        P.append((x, side * model.hw(x, z), z))
    return np.array(P, np.float64)


def snap_edges(model, pose, arches, hsv, w, h, win=25, step_min=18.0):
    """沿模型曲线投影点逐列扫 (S差+V降) 边缘 -> [(arch, x, z, u, v, score)]"""
    Hc, Sc, Vc = hsv
    rv, tv, K = (np.array(pose["rvec"]), np.array(pose["tvec"]),
                 Kmat(pose["f"], w, h))
    side = int(pose["side"])
    out = []
    for ai in arches:
        P3 = intrados_samples(model, ai, side, n=200)
        uv = project(P3, K, rv, tv)
        for j in range(0, 200, 2):
            u, v = uv[j]
            ui = int(round(u))
            if ui < 3 or ui >= w - 3:
                continue
            v0 = int(round(v)) - win
            v1 = int(round(v)) + win
            if v0 < 8 or v1 >= h - 8:
                continue
            sb = Sc[v0:v1, ui].astype(np.float32)
            vb = Vc[v0:v1, ui].astype(np.float32)
            ker = 4
            sm = np.convolve(sb, np.ones(2 * ker + 1) / (2 * ker + 1), "same")
            vm = np.convolve(vb, np.ones(2 * ker + 1) / (2 * ker + 1), "same")
            score = (sm[ker + 3:v1 - v0 - 2] - sm[2:v1 - v0 - ker - 3]) * 1.0 + \
                    (vm[2:v1 - v0 - ker - 3] - vm[ker + 3:v1 - v0 - 2]) * 1.0
            if len(score) < 5:
                continue
            k = int(np.argmax(score))
            if score[k] < step_min:
                continue
            k = max(1, min(len(score) - 2, k))
            vv = v0 + ker + 3 + k
            # 亚像素
            s1, s2, s3 = score[k - 1], score[k], score[k + 1]
            den = s1 - 2 * s2 + s3
            off = 0.5 * (s1 - s3) / den if abs(den) > 1e-9 else 0.0
            v_sn = vv + max(-1.0, min(1.0, off))
            x, y3, z = P3[j]
            out.append({"arch": ai, "x": float(x), "z": float(z),
                        "u": float(u), "v": float(v_sn),
                        "score": float(score[k])})
    return out


def solve_corr(model, corr, w, h, side, frame, tag, verbose=False):
    pts3d = np.array([(p["x"], side * model.hw(p["x"], p["z"]), p["z"])
                      for p in corr], np.float64)
    pts2d = np.array([(p["u"], p["v"]) for p in corr], np.float64)
    cdict = {"tag": tag, "image": frame, "side": side,
             "points": [{"spec": {"x": p["x"], "z": p["z"]},
                         "u": p["u"], "v": p["v"]} for p in corr]}
    return solve_pose(cdict, model, verbose=verbose)


def fit_crowns(model, obs, w, h, side, seeds):
    """冠点-only 降参相机拟合(fit_camera 的 crown 路有 pop bug, 自带实现)."""
    from scipy.optimize import least_squares
    P = np.array([(model.arches[o["arch"]]["xc"],
                   side * model.hw(model.arches[o["arch"]]["xc"],
                                   model.arches[o["arch"]]["spz"] +
                                   model.arches[o["arch"]]["b"]),
                   model.arches[o["arch"]]["spz"] + model.arches[o["arch"]]["b"])
                  for o in obs], np.float64)
    UV = np.array([(o["u_apex"], o["v_apex"]) for o in obs], np.float64)

    def res(p):
        f_pen = 4.0 * max(0.0, 700.0 - p[5]) + 4.0 * max(0.0, p[5] - 9000.0)
        return np.append(cam_model_proj(p, P, w, h) - UV, f_pen)

    best = None
    for s0 in seeds:
        try:
            r = least_squares(res, np.array(s0, np.float64), loss="soft_l1",
                              f_scale=12.0, max_nfev=600)
        except Exception:
            continue
        rms = float(np.sqrt(np.mean(res(r.x) ** 2)))
        if best is None or rms < best[0]:
            best = (rms, r.x)
    return best


def make_seeds_cctv(model, side):
    """相机在东端外侧(南面), 望向西半桥: az 125..170, 距离 50..150."""
    seeds = []
    for azd in range(125, 171, 9):
        az = math.radians(azd)
        ca, sa = math.cos(az), math.sin(az)
        for dist in (50, 80, 110, 150):
            for eld in (-4, 2, 8):
                for f in (1500.0, 2500.0, 4000.0, 6000.0):
                    seeds.append([az, math.radians(eld),
                                  10.0 - dist * ca, -dist * sa, 2.0, f])
    return seeds


def cmd_pose(frame, tag):
    model = Model(load_ctrl())
    img = cv2.imread(frame)
    h, w = img.shape[:2]
    side = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    blobs, hsv = orange_blobs(img)
    Hc, Sc, Vc = hsv
    anchors = apex_anchors(blobs, Hc, Sc, Vc, w, h)
    best = None
    print("blobs:", [(int(b["u"]), int(b["v_apex"]), b["w"]) for b in blobs])
    print("anchors:", len(anchors))
    # 粗拟: 锚点到冠弧(投影)距离, 离散锚
    crowns = {}
    for a0 in (0, 1, 2, 3):
        arches = [a0 + k for k in range(len(blobs))]
        arcs = {}
        for ai in arches:
            a = model.arches[ai]
            xs = np.linspace(a["xc"] - 1.3, a["xc"] + 1.3, 40)
            arcs[ai] = np.array([(x, side * model.hw(x, a["spz"] + a["b"]),
                                  a["spz"] + a["b"]) for x in xs])
        def res(p):
            r = []
            bias = p[6]
            for (u, v, bi) in anchors:
                ai = arches[bi]
                q = cam_model_proj(np.append(p[:6], 0.0), arcs[ai], w, h)
                d = np.sqrt(((q - np.array([u, v + bias])) ** 2).sum(1))
                r.append(float(d.min()))
            return np.array(r)
        best_a = None
        for s0 in make_seeds_cctv(model, side):
            try:
                rr = least_squares(res, np.append(np.array(s0, float)[:6], 40.0),
                                   method="trf",
                                   bounds=([math.radians(120), math.radians(-12),
                                            30.0, -60.0, -2.0, 700.0, 0.0],
                                           [math.radians(200), math.radians(14),
                                            160.0, 60.0, 12.0, 9000.0, 160.0]),
                                   max_nfev=250)
            except Exception:
                continue
            rms = float(np.sqrt(np.mean(res(rr.x) ** 2)))
            if best_a is None or rms < best_a[0]:
                best_a = (rms, rr.x)
        print("anchor a0=%d rms=%.1f f=%.0f bias=%.0f"
              % (a0, best_a[0], best_a[1][5], best_a[1][6]))
        if best is None or best_a[0] < best[0]:
            best = (best_a[0], best_a[1], a0)
    if best is None:
        raise SystemExit("no anchor fit")
    rms, p, a0 = best
    print("BEST a0=%d rms=%.1f" % (a0, rms))
    az, el, Cx, Cy, Cz, f = p[:6]
    R = cam_R(az, el, 0.0)
    C = np.array([Cx, Cy, Cz])
    rvec, _ = cv2.Rodrigues(R.astype(np.float64))
    pose = {"image": frame, "w": w, "h": h, "side": side, "f": float(f),
            "rvec": rvec.reshape(3).tolist(),
            "tvec": (-R @ C).astype(np.float64).tolist(),
            "rms": -1, "n": 0, "tag": tag}
    arches = [a0 + k for k in range(len(blobs))]
    for it, win in enumerate((70, 45, 28, 22)):
        edges = snap_edges(model, pose, arches, hsv, w, h, win=win)
        # 每孔限制点数与外点剔除: 距投影曲线 >10px 的丢
        keep = []
        rv, tv, K = (np.array(pose["rvec"]), np.array(pose["tvec"]),
                     Kmat(pose["f"], w, h))
        for e in edges:
            P3 = np.array([(e["x"], side * model.hw(e["x"], e["z"]), e["z"])])
            uv = project(P3, K, rv, tv)[0]
            if np.hypot(uv[0] - e["u"], uv[1] - e["v"]) > 10:
                continue
            keep.append(e)
        print("it%d: edges=%d kept=%d" % (it, len(edges), len(keep)))
        pose = solve_corr(model, keep, w, h, side, frame, tag,
                          verbose=(it == 3))
        pose["tag"] = tag
        json.dump(pose, open(os.path.join(OUT, "pose_%s.json" % tag), "w"),
                  indent=1)
        print("  rms=%.2fpx f=%.0f n=%d" % (pose["rms"], pose["f"], pose["n"]))
    # 可视化 + 报告
    vis = img.copy()
    rv, tv, K = (np.array(pose["rvec"]), np.array(pose["tvec"]),
                 Kmat(pose["f"], w, h))
    for ai in arches:
        P3 = intrados_samples(model, ai, side, n=120)
        uv = project(P3, K, rv, tv).astype(np.int32)
        cv2.polylines(vis, [uv], False, (0, 255, 255), 2)
    cv2.imwrite(os.path.join(OUT, "m20b_a07_fit_%s.jpg" % tag), vis)
    P3 = intrados_samples(model, 7, side, n=60)
    uv = project(P3, K, rv, tv)
    sx7 = float(np.mean(np.linalg.norm(np.diff(uv[:, :1], axis=0), axis=1))) \
        / (2 * 4.0 * 0.99 / 59)
    byarch = {}
    # 残差按孔(用 snap 最后一轮关联)
    edges = snap_edges(model, pose, arches, hsv, w, h)
    for e in edges:
        byarch.setdefault(e["arch"], []).append(e["score"])
    rep = {"frame": frame, "side": side, "rms": pose["rms"], "f": pose["f"],
           "anchor_a0": a0, "sx_arch7": round(sx7, 2),
           "edges_by_arch": {str(k): len(v) for k, v in sorted(byarch.items())}}
    json.dump(rep, open(os.path.join(OUT, "m20b_a07_report_%s.json" % tag), "w"),
              indent=1)
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    if sys.argv[1] == "pose":
        cmd_pose(sys.argv[2], sys.argv[3])
    else:
        raise SystemExit(__doc__)
