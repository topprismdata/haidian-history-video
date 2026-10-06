#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""M20 位姿初始化: 自动检拱洞 -> 链匹配 -> 多起点相机束拟合 -> ICP 精化。
消解人工粗标的系统性偏差与孔号歧义(中央孔在哪端/哪孔)。
"""
import itertools
import json
import math
import os
import sys


import numpy as np
import cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from m20_pipeline import Model, load_ctrl, OUT, pose_arr, project  # noqa: E402
from m20_fitcurves import cam_R, proj  # noqa: E402  同一降参相机模型


def detect_voids(image, band, min_area=2500):
    """拱洞暗域检测: 返回 [{"u_apex","v_apex","rows":[(v,ul,ur)...],"area"}] 按 u 排序。"""
    img = cv2.imread(image)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    v0, v1, u0, u1 = band
    g = gray[v0:v1, u0:u1]
    # 暗域: 相对局部大邻域均值显著偏暗
    bg = cv2.medianBlur(g, 61)
    mask = (g.astype(int) < bg.astype(int) - 26).astype(np.uint8) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,
                            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE,
                            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    out = []
    for k in range(1, n):
        x, y, w, h, area = stats[k]
        if area < min_area or h < 120 or w < 60:
            continue
        comp = (lab == k)
        ys, xs = np.where(comp)
        i_apex = int(np.argmin(ys))
        rows = []
        for dv in (0.15, 0.3, 0.45, 0.6):
            vv = int(y + dv * h)
            row = np.where(comp[vv - v0 + v0 - v0])[0] if False else np.where(comp[vv])[0]
            if len(row) > 4:
                rows.append((v0 + vv, u0 + int(row.min()), u0 + int(row.max())))
        out.append({"u_apex": float(u0 + xs[i_apex]), "v_apex": float(v0 + ys[i_apex]),
                    "area": int(area), "w": int(w), "h": int(h), "rows": rows})
    out.sort(key=lambda d: d["u_apex"])
    return out


def cam_rot(az, el):
    """光轴方位 az/俯仰 el(rad) -> cv2 旋转矩阵(行: 右,下,前)。"""
    fwd = np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)])
    up = np.array([0.0, 0.0, 1.0])
    right = np.cross(fwd, up)
    right /= np.linalg.norm(right)
    down = np.cross(fwd, right)
    return np.vstack([right, down, fwd])


def cam_model_proj(params, P, w, h):
    """params=[az,el,Cx,Cy,Cz,f] -> uv (n,2)"""
    az, el, Cx, Cy, Cz, f = params
    R = cam_rot(az, el)
    Pc = (np.asarray(P, np.float64) - np.array([Cx, Cy, Cz])) @ R.T
    z = Pc[:, 2]
    ok = z > 1.0
    u = f * Pc[:, 0] / np.maximum(z, 1e-6) + w / 2.0
    v = f * Pc[:, 1] / np.maximum(z, 1e-6) + h / 2.0
    u[~ok] = 1e6; v[~ok] = 1e6
    return np.stack([u, v], 1)


def fit_camera(model, obs, w, h, side, seeds, loss="soft_l1"):
    """obs: [{"arch":i}] 用冠点+1/4 点。seeds: [params]。多起点 scipy least_squares。"""
    from scipy.optimize import least_squares
    P, UV = [], []
    for o in obs:
        i = o["arch"]
        a = model.arches[i]
        pts = [("crown", 0.0)]
        P.append((a["xc"], side * model.hw(a["xc"], a["spz"] + a["b"]), a["spz"] + a["b"]))
        UV.append([o["u_apex"], o["v_apex"]])
        for xr in (-0.55, 0.55):
            x = a["xc"] + xr * a["a"]
            z = model.intrados_z(x, i)
            P.append((x, side * model.hw(x, z), z))
            uv = o["uv_quarter"].get(round(xr, 2))
            if uv is None:
                P.pop(); UV.pop()
            else:
                UV[-1] = uv
    P = np.array(P, np.float64); UV = np.array(UV, np.float64)

    def res(params):
        return (cam_model_proj(params, P, w, h) - UV).ravel()

    best = None
    for s0 in seeds:
        try:
            r = least_squares(res, np.array(s0, np.float64), loss=loss, f_scale=8.0,
                              max_nfev=4000)
        except Exception:
            continue
        rms = float(np.sqrt(np.mean(res(r.x) ** 2)))
        if best is None or rms < best[0]:
            best = (rms, r.x)
    return best


def make_seeds(model, side):
    seeds = []
    for d in (40, 55, 75, 100, 140, 200, 300):
        for xoff in (0.0, 0.3, 0.6, 0.9):
            for el in (-8, -4, 0, 3, 6):
                for fend in (700, 1500, 3000, 6000, 12000, 24000):
                    az = (0.0 if side > 0 else math.pi)  # 光轴基本沿 ±x? 先横看
                    seeds.append([az + side * math.pi / 2 + 0.0, math.radians(el),
                                  xoff * d, side * (d * 0.06), 1.5, float(fend)])
    return seeds


def cmd_init(image, band, side, tag, arch_range=None):
    model = Model(load_ctrl())
    img = cv2.imread(image)
    h, w = img.shape[:2]
    voids = detect_voids(image, band)
    print("voids: %d" % len(voids))
    for v in voids:
        print("  apex=(%.0f,%.0f) wh=(%d,%d) rows=%s" %
              (v["u_apex"], v["v_apex"], v["w"], v["h"],
               [(r[0], r[1], r[2]) for r in v["rows"][:2]]))
    vis = img.copy()
    for v in voids:
        cv2.circle(vis, (int(v["u_apex"]), int(v["v_apex"])), 7, (0, 0, 255), 2)
        cv2.putText(vis, "%.0f" % v["w"], (int(v["u_apex"]) - 15, int(v["v_apex"]) - 12),
                    0, 0.9, (0, 255, 255), 2)
    cv2.imwrite(os.path.join(OUT, "voids_%s.jpg" % tag), vis)


def cmd_deckfit(image, tag, marks_file):
    """桥面位姿: 望柱脚链(3D 已知: x=-75+150k/63, y=±3.24, z=deck_z(x))
    -> 降参相机(az,el,Cx,Cy,Cz,f,roll,X0) + 链方向 dr 与侧 side 假设搜索。
    marks: {"posts":[{"side":±1,"u":..,"v":..},...]} 按 近->远 排序,
    side=该柱在画面中的侧别(-1=左链)。"""
    from scipy.optimize import least_squares
    cfg = json.load(open(marks_file))
    model = Model(load_ctrl())
    img = cv2.imread(image)
    h, w = img.shape[:2]
    S = 150.0 / 63.0
    posts = cfg["posts"]
    n = len(posts)

    def post_xyz(j, X0L, X0R, dr, side_l):
        m = posts[j]
        sd = side_l * m.get("side", -1)
        X0 = X0L if m.get("side", -1) < 0 else X0R
        x = X0 + dr * m.get("s", j) * S
        return (x, sd * (model.c["DECK_UP_W"] / 2.0 - 0.18 + 0.14), model.deck_z(x))

    best = None
    for dr in (1, -1):
        for side_l in (1, -1):
            def res(p):
                Pp = np.array([post_xyz(j, p[7], p[8], dr, side_l)
                               for j in range(n)], np.float64)
                uv = proj(p[:7], Pp, w, h)
                r = (uv - np.array([[m["u"], m["v"]] for m in posts],
                                   np.float64)).ravel()
                cz_pen = 4.0 * max(0.0, abs(p[4] - (model.deck_z(p[2]) + 1.55)) - 0.25)
                cy_pen = 4.0 * max(0.0, abs(p[3]) - 3.05)
                el_pen = 4.0 * max(0.0, abs(p[1]) - math.radians(16))
                return np.append(r, [cz_pen, cy_pen, el_pen])

            seeds = []
            for azd in (55, 70, 110, 125):
                az = math.radians(azd if dr > 0 else -azd)
                for dist in (3, 6, 12, 25):
                    for f in (900, 1400, 2200, 3500):
                        x_end = (75 if dr > 0 else -75)
                        seeds.append([az, math.radians(-12),
                                      x_end + dist * math.cos(az),
                                      0.5 * side_l, 1.8, float(f), 0.0,
                                      x_end - dr * n * S, x_end - dr * n * S])
            for s0 in seeds:
                try:
                    r = least_squares(res, np.array(s0, np.float64), loss="soft_l1",
                                      f_scale=5.0, max_nfev=2500)
                except Exception:
                    continue
                rr = res(r.x)
                rms = float(np.sqrt(np.mean(rr[:-2] ** 2)))
                if best is None or rms < best[0]:
                    best = (rms, r.x.copy(), dr, side_l)
                    print("  dr=%+d side=%+d rms=%.2f f=%.0f C=(%.1f,%.2f,%.2f) X0L=%.1f X0R=%.1f"
                          % (dr, side_l, rms, r.x[5], r.x[2], r.x[3], r.x[4],
                             r.x[7], r.x[8]))
    rms, p, dr, side_l = best
    print("BEST dr=%+d side=%+d rms=%.2fpx" % (dr, side_l, rms))
    json.dump({"rms": rms, "params": list(map(float, p)), "dr": dr,
               "side": side_l, "w": w, "h": h, "image": image},
              open(os.path.join(OUT, "fit_%s.json" % tag), "w"), indent=1)
    vis = img.copy()
    for k in range(64):
        for sd in (-1, 1):
            x = -75.0 + k * S
            uv = proj(p[:7], np.array([(x, sd * 3.24, model.deck_z(x))],
                                      np.float64), w, h)[0]
            if -50 < uv[0] < w + 50 and -50 < uv[1] < h + 50:
                cv2.circle(vis, (int(uv[0]), int(uv[1])), 4,
                           (0, 0, 255) if sd < 0 else (0, 255, 0), 1)
    for yy in (-1.0333, 0.0, 1.0333):
        Pp = [(x, yy, model.deck_z(x)) for x in np.linspace(-75, 75, 200)]
        uv = proj(p[:7], np.array(Pp, np.float64), w, h).astype(np.int32)
        cv2.polylines(vis, [uv], False, (255, 0, 255), 1)
    cv2.imwrite(os.path.join(OUT, "fit_%s.jpg" % tag), vis,
                [cv2.IMWRITE_JPEG_QUALITY, 90])


def cmd_deckortho(tag, ppm=32.0, x0=None, x1=None):
    """桥面展开: 射线投到 z=deck_z(x) 曲面, (x,y) 正射 + 0.5m 网格 + 质量图。"""
    cfg = json.load(open(os.path.join(OUT, "fit_%s.json" % tag)))
    model = Model(load_ctrl())
    img = cv2.imread(cfg["image"])
    h, w = img.shape[:2]
    p = np.array(cfg["params"], np.float64)
    Cx = p[2]
    if x0 is None:
        x0 = max(-75.0, Cx - 4.0)
    if x1 is None:
        x1 = 75.0
    y0, y1 = -3.35, 3.35
    W = int(round((x1 - x0) * ppm)); H = int(round((y1 - y0) * ppm))
    xs = x0 + (np.arange(W) + 0.5) / ppm
    ys = y1 - (np.arange(H) + 0.5) / ppm
    P = np.empty((H, W, 3), np.float64)
    P[..., 0] = xs[None, :]
    P[..., 1] = ys[:, None]
    P[..., 2] = model.deck_z(P[..., 0])
    uv = proj(p[:7], P.reshape(-1, 3), w, h).reshape(H, W, 2)
    u = uv[..., 0]; v = uv[..., 1]
    valid = (u >= 0) & (u <= w - 2) & (v >= 0) & (v <= h - 2)
    u0 = np.clip(np.floor(u).astype(int), 0, w - 2)
    v0 = np.clip(np.floor(v).astype(int), 0, h - 2)
    fu = u - u0; fv = v - v0
    out = np.zeros((H, W, 3), np.float32)
    for c in range(3):
        ch = img[..., c].astype(np.float32)
        out[..., c] = (ch[v0, u0] * (1 - fu) * (1 - fv) + ch[v0, u0 + 1] * fu * (1 - fv)
                       + ch[v0 + 1, u0] * (1 - fu) * fv + ch[v0 + 1, u0 + 1] * fu * fv)
    out[~valid] *= 0.25
    # 质量图: 每正射像素对应的源采样步长 (m/px)
    eps = 0.08
    P2 = P.reshape(-1, 3).copy(); P2[:, 0] += eps
    du = np.linalg.norm(proj(p[:7], P2, w, h) - proj(p[:7], P.reshape(-1, 3), w, h),
                        axis=1) / eps
    mpp = np.clip(1.0 / np.maximum(du, 1e-6), 0, 1.0)
    qual = (np.clip(1.0 - mpp / 0.10, 0, 1) * 255).astype(np.uint8).reshape(H, W)
    qual[~valid.reshape(H, W)] = 0
    ortho = out.astype(np.uint8)
    # 网格 0.5m + 柱位线 + 模型带界
    for gx in np.arange(math.ceil(x0 / 0.5) * 0.5, x1 + 1e-6, 0.5):
        px = int((gx - x0) * ppm)
        maj = abs(gx % 2.381) < 0.25 or abs(gx) < 0.25
        cv2.line(ortho, (px, 0), (px, H - 1), (70, 70, 70) if not maj else (110, 110, 110), 1)
        if abs(gx % 2.0) < 0.25:
            cv2.putText(ortho, "%.0f" % gx, (px + 2, 12), 0, 0.35, (255, 255, 0), 1)
    for gy in np.arange(-3.0, 3.01, 0.5):
        py = int((y1 - gy) * ppm)
        cv2.line(ortho, (0, py), (W - 1, py), (110, 110, 110) if abs(gy % 1) < 1e-6 else (70, 70, 70), 1)
        cv2.putText(ortho, "%.1f" % gy, (2, py - 2), 0, 0.35, (255, 255, 0), 1)
    for yy in (-3.24, -1.0333, 0.0, 1.0333, 3.24):
        py = int((y1 - yy) * ppm)
        cv2.line(ortho, (0, py), (W - 1, py), (0, 215, 255), 1)
    cv2.imwrite(os.path.join(OUT, "deck_ortho_%s.png" % tag), ortho)
    cv2.imwrite(os.path.join(OUT, "deck_ortho_%s_q.png" % tag), qual)
    print("deck_ortho_%s.png %dx%d x[%.1f,%.1f]" % (tag, W, H, x0, x1))


def cmd_deckcurves(image, tag, rough_file):
    """路缘/栏底两条纵线: 粗样条 -> 梯度脊吸附 -> 密折线, 存 curves_<tag>.json。"""
    cfg = json.load(open(rough_file))
    img = cv2.imread(image)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    h, w = gray.shape
    out = {}
    for key in ("L", "R"):
        ctrl = np.array(cfg[key], np.float64)  # [[u,v],...] 粗控制点
        us = np.linspace(ctrl[0, 0], ctrl[-1, 0], 220)
        spl = np.interp(us, ctrl[:, 0], ctrl[:, 1])
        for it in range(3):
            snapped = []
            for u, v0 in zip(us, spl):
                r = 12 if it < 2 else 6
                vv = int(round(v0))
                lo, hi = max(1, vv - r), min(gray.shape[0] - 2, vv + r)
                if hi - lo < 4:
                    snapped.append(v0); continue
                col = gray[lo:hi + 1, int(round(u))]
                j = int(np.argmin(col))            # 暗谷(缝/阴影线)优先
                d1, d2, d3 = col[max(j - 1, 0)], col[j], col[min(j + 1, len(col) - 1)]
                den = d1 - 2 * d2 + d3
                off = 0.5 * (d1 - d3) / den if abs(den) > 1e-9 else 0.0
                off = max(-1.0, min(1.0, off))
                snapped.append(lo + j + off)
            spl = np.minimum(np.maximum(np.array(snapped), 1), gray.shape[0] - 2)
        out[key] = [[float(a), float(b)] for a, b in zip(us, spl)]
        vis = img.copy()
        cv2.polylines(vis, [np.array(out[key], np.int32)], False, (0, 0, 255), 1)
        cv2.imwrite(os.path.join(OUT, "curves_%s.jpg" % tag), vis,
                    [cv2.IMWRITE_JPEG_QUALITY, 90])
    json.dump(out, open(os.path.join(OUT, "curves_%s.json" % tag), "w"))
    print("curves_%s.json written" % tag)


def cmd_deckfit2(image, tag, curves_file, f_lo=500, f_hi=3000):
    """路缘双曲线拟合位姿: 点到曲线残差 + 在桥面上先验(硬惩罚)。"""
    from scipy.optimize import least_squares
    cv_ = json.load(open(curves_file))
    model = Model(load_ctrl())
    img = cv2.imread(image)
    h, w = img.shape[:2]
    YC = model.c["DECK_UP_W"] / 2.0 - 0.18 + 0.14   # 3.24 柱列线
    CURB = model.c["DECK_UP_W"] / 2.0               # 3.28 路缘

    def curb_pts(side, n=320, xlo=-75.0, xhi=75.0):
        xs = np.linspace(xlo, xhi, n)
        return np.stack([xs, np.full(n, side * CURB), model.deck_z(xs)], 1)

    curves = {s: np.array(cv_[s], np.float64) for s in ("L", "R")}
    best = None
    for dr in (1, -1):
        for side_l in (1, -1):
            cps = {s: curb_pts(side_l * (-1 if s == "L" else 1)) for s in ("L", "R")}

            def res(p):
                r = []
                for s in ("L", "R"):
                    uv = proj(p, cps[s], w, h)
                    m = (uv[:, 0] > -1e5) & (uv[:, 0] < w) & (uv[:, 1] > -1e5) & (uv[:, 1] < h)
                    if m.sum() < 8:
                        return np.full(8, 1e4)
                    q = uv[m]
                    obs = curves[s]
                    # 每观测点 -> 投影曲线最近距离(粗网格 1/3 抽样加速)
                    d = np.sqrt(((obs[:, None, :] - q[::3][None, :, :]) ** 2).sum(-1))
                    r.append(d.min(1))
                rr = np.concatenate(r)
                cz_pen = 6.0 * max(0.0, abs(p[4] - (model.deck_z(p[2]) + 1.55)) - 0.3)
                cy_pen = 6.0 * max(0.0, abs(p[3]) - 2.6)
                el_pen = 6.0 * max(0.0, abs(p[1]) - math.radians(15))
                return np.append(rr, [cz_pen, cy_pen, el_pen])

            seeds = []
            for azd in ((-10, -4, 0, 4, 10) if dr > 0 else (170, 176, 180, 184, 190)):
                az = math.radians(azd)
                for el in (-10, -5, 0):
                    for dist in (4, 8, 15, 30):
                        for f in (f_lo, (f_lo + f_hi) / 2, f_hi):
                            x_end = (-75 if dr > 0 else 75)
                            seeds.append([az, math.radians(el),
                                          x_end - dist * math.cos(az),
                                          0.8 * side_l, 2.9, float(f), 0.0])
            st1 = None
            for s0 in seeds:
                try:
                    r = least_squares(res, np.array(s0, np.float64), loss="soft_l1",
                                      f_scale=4.0, max_nfev=200)
                except Exception:
                    continue
                rr = res(r.x)
                rms = float(np.sqrt(np.mean(rr[:-3] ** 2)))
                pen = float(np.abs(rr[-3:]).sum())
                sc = rms + 0.3 * pen
                if st1 is None or sc < st1[0]:
                    st1 = (sc, r.x.copy())
            for s0 in (st1[1], st1[1] * np.array([1, 1, 1, 1, 1, 1.08, 1]),
                       st1[1] * np.array([1, 1, 1, 1, 1, 0.92, 1])):
                try:
                    r = least_squares(res, np.array(s0, np.float64), loss="soft_l1",
                                      f_scale=4.0, max_nfev=3000)
                except Exception:
                    continue
                rr = res(r.x)
                rms = float(np.sqrt(np.mean(rr[:-3] ** 2)))
                if best is None or rms + 0.3 * float(np.abs(rr[-3:]).sum()) \
                        < best[0] + 0.3 * best[2]:
                    best = (rms, r.x.copy(), float(np.abs(rr[-3:]).sum()))
                    print("  dr=%+d side=%+d rms=%.2f pen=%.1f f=%.0f C=(%.1f,%.2f,%.2f)"
                          % (dr, side_l, rms, best[2], r.x[5], r.x[2], r.x[3], r.x[4]))
    rms, p, pen = best
    print("BEST rms=%.2f pen=%.2f" % (rms, pen))
    json.dump({"rms": rms, "pen": pen, "params": list(map(float, p)), "w": w,
               "h": h, "image": image},
              open(os.path.join(OUT, "fit_%s.json" % tag), "w"), indent=1)
    vis = img.copy()
    for k in range(64):
        for sd in (-1, 1):
            x = -75.0 + k * (150.0 / 63.0)
            uv = proj(p, np.array([(x, sd * 3.24, model.deck_z(x))],
                                  np.float64), w, h)[0]
            if -50 < uv[0] < w + 50 and -50 < uv[1] < h + 50:
                cv2.circle(vis, (int(uv[0]), int(uv[1])), 4,
                           (0, 0, 255) if sd < 0 else (0, 255, 0), 1)
    for yy in (-1.0333, 0.0, 1.0333):
        Pp = [(x, yy, model.deck_z(x)) for x in np.linspace(-75, 75, 200)]
        uv = proj(p, np.array(Pp, np.float64), w, h).astype(np.int32)
        cv2.polylines(vis, [uv], False, (255, 0, 255), 1)
    cv2.imwrite(os.path.join(OUT, "fit_%s.jpg" % tag), vis,
                [cv2.IMWRITE_JPEG_QUALITY, 90])


if __name__ == "__main__":
    if sys.argv[1] == "init":
        cmd_init(sys.argv[2], [int(v) for v in sys.argv[3].split(",")],
                 int(sys.argv[4]), sys.argv[5])
    elif sys.argv[1] == "deckfit":
        cmd_deckfit(sys.argv[2], sys.argv[3], sys.argv[4])
    elif sys.argv[1] == "deckcurves":
        cmd_deckcurves(sys.argv[2], sys.argv[3], sys.argv[4])
    elif sys.argv[1] == "deckfit2":
        cmd_deckfit2(sys.argv[2], sys.argv[3], sys.argv[4])
    elif sys.argv[1] == "deckortho":
        cmd_deckortho(sys.argv[2])
