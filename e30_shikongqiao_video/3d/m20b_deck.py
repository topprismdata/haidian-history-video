#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""m20b: deck 砖谱链. 栏板基线重捕 -> 望柱脚检测 -> 降参相机拟合(柱脚链+
基线, 相位 X0 自由+敏度分析) -> (x,y) 正射 m20_ortho_deck.png -> 缝线描摹
-> stones_deck.json (列线/行线弧长/两沟/柱对缝判定).
用法:
  python3 m20b_deck.py fit   FRAME TAG
  python3 m20b_deck.py ortho TAG X0 X1 PPM
  python3 m20b_deck.py seams TAG
"""
import json
import math
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from m20_pipeline import Model, load_ctrl, OUT  # noqa: E402
from m20_fitcurves import proj  # noqa: E402

S = 150.0 / 63.0   # 2.381 望柱中心距


def proj_pp(p, P):
    az, el, Cx, Cy, Cz, f, roll, u0, v0 = p[:9]
    q = proj([az, el, Cx, Cy, Cz, f, roll], P, 1280, 720)
    q[:, 0] += u0
    q[:, 1] += v0
    return q


def robust_curves(img, rough):
    """从粗曲线出发: poly2 稳健拟合 + 暗谷亚像素重捕."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    out = {}
    for key in ("L", "R"):
        pts = np.array(rough[key], np.float64)
        us = pts[:, 0]
        vs = pts[:, 1]
        for _ in range(3):
            cf = np.polyfit(us, vs, 2)
            resid = vs - np.polyval(cf, us)
            keep = np.abs(resid - np.median(resid)) < 3.5
            us, vs = us[keep], vs[keep]
        uf = np.arange(int(us.min()), min(int(us.max()) + 1, gray.shape[1] - 1))
        base = np.polyval(np.polyfit(us, vs, 2), uf)
        snap = []
        for u, v0 in zip(uf, base):
            vv = int(round(v0))
            lo, hi = max(1, vv - 9), min(gray.shape[0] - 2, vv + 9)
            if hi - lo < 6:
                snap.append((float(u), float(v0)))
                continue
            col = gray[lo:hi + 1, int(u)]
            j = int(np.argmin(col))
            d1, d2, d3 = col[max(j - 1, 0)], col[j], col[min(j + 1, len(col) - 1)]
            den = d1 - 2 * d2 + d3
            off = 0.5 * (d1 - d3) / den if abs(den) > 1e-9 else 0.0
            snap.append((float(u), float(lo + j + max(-1.0, min(1.0, off)))))
        out[key] = snap
    return out


def post_bases(img, curves):
    """沿基线找望柱脚: 缝暗度场里的宽亮段(柱础无缝)."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    out = {}
    for key in ("L", "R"):
        cs = curves[key]
        d = []
        for (u, v) in cs:
            ui, vi = int(u), int(round(v))
            win = gray[max(0, vi - 5):vi + 6, max(0, ui - 1):ui + 2]
            d.append(float(win.min()))
        d = np.array(d)
        # 亮段 = d 高于滑动中位 +8
        pad = np.pad(d, 15, mode="edge")
        bg = np.array([np.median(pad[k:k + 31]) for k in range(len(d))])
        hot = d > bg + 5.0
        segs = []
        k = 0
        while k < len(hot):
            if hot[k]:
                j = k
                while j < len(hot) and hot[j]:
                    j += 1
                if j - k >= 3:
                    segs.append((k, j))
                k = j
            else:
                k += 1
        bases = []
        for (a, b) in segs:
            um = float(np.mean([cs[i][0] for i in range(a, b)]))
            vm = float(np.mean([cs[i][1] for i in range(a, b)]))
            bases.append({"u": um, "v": vm, "w_px": b - a})
        out[key] = bases
    return out


def deck_z(model, x):
    return model.deck_z(x)


def fit_camera(model, frame, curves, bases, tag):
    from scipy.optimize import least_squares
    img = cv2.imread(frame)
    h, w = img.shape[:2]
    posts = []
    for key, sgn in (("L", -1), ("R", +1)):
        for b in bases[key]:
            posts.append({"side": sgn, "u": b["u"], "v": b["v"]})

    def curve_pts(side, n=160):
        xs = np.linspace(30.0, 75.0, n)
        return np.stack([xs, np.full(n, side * 3.28), model.deck_z(xs)], 1)

    cl = curve_pts(-1)
    cr = curve_pts(+1)
    obs_l = np.array(curves["L"], np.float64)
    obs_r = np.array(curves["R"], np.float64)

    def res(p):
        r = []
        for obs, cps in ((obs_l, cl), (obs_r, cr)):
            q = proj_pp(p, cps)
            d = np.sqrt(((obs[:, None, :] - q[None, :, :]) ** 2).sum(-1))
            di = d.min(1)
            di = np.sort(di)[:int(len(di) * 0.85)]   # 去尾 15%(锯齿/人影)
            r.extend(di.tolist())
        return np.array(r)

    LO = [math.radians(171.0), math.radians(-9.0), 66.0, -1.0,
          1.5, 300.0, math.radians(-6.0), -320.0, -320.0]
    HI = [math.radians(179.0), math.radians(-3.0), 80.0, 2.0,
          8.5, 900.0, math.radians(1.0), 320.0, 320.0]
    best = None
    for azd in (174.0, 175.5):
        for eld in (-6.0, -5.0):
            for f0 in (420.0, 480.0):
                for Cx0 in (71.0, 73.5, 76.0):
                    for rl0 in (math.radians(-2.7), 0.0):
                        p0 = [math.radians(azd), math.radians(eld), Cx0, 0.5,
                              model.deck_z(Cx0) + 1.55, f0, rl0, 0.0, 0.0]
                        try:
                            r = least_squares(res, np.array(p0), method="trf",
                                              bounds=(LO, HI), max_nfev=400)
                        except Exception:
                            continue
                        rms = float(np.sqrt(np.mean(res(r.x) ** 2)))
                        if best is None or rms < best[0]:
                            best = (rms, r.x.copy())
                            print("  curve-fit rms=%.2f f=%.0f C=(%.1f,%.2f,%.2f) "
                                  "roll=%.1f pp=(%.0f,%.0f)"
                                  % (rms, r.x[5], r.x[2], r.x[3],
                                     r.x[4], math.degrees(r.x[6]),
                                     r.x[7], r.x[8]))
    rms, p = best
    # 阶段B: X0 一维扫描(柱脚 u 对齐)
    posts_u = sorted([m["u"] for m in posts])
    def x0_score(X0):
        js = np.arange(0, 64)
        err = 0.0
        for sd in (-1, 1):
            xs = X0 + js * S
            P = np.stack([xs, np.full(len(xs), sd * 3.24),
                          model.deck_z(xs)], 1)
            uv = proj_pp(p, P)
            m = (uv[:, 0] > -50) & (uv[:, 0] < w + 50) & (uv[:, 1] > -50) &                 (uv[:, 1] < h + 50)
            uu = np.sort(uv[m, 0])
            if len(uu) == 0:
                return 1e9
            e = 0.0
            for u in posts_u:
                e += float(np.min(np.abs(uu - u))) ** 2
            err += e
        return err
    grid = np.arange(-75.0, 75.0 - S, 0.05)
    scores = [x0_score(g) for g in grid]
    scores = np.array(scores)
    k = int(np.argmin(scores))
    X0 = float(grid[k])
    # 相位敏度: 次极小 vs 主极小(±S 格)
    near = {"grid_phase_ref": round((-75.0) % S, 3)}
    for mm in (-2, -1, 1, 2):
        g = X0 + mm * S
        if -75 <= g <= 75 - S:
            near["%+d" % mm] = round(float(np.sqrt(x0_score(g))), 2)
    print("BEST curve rms=%.2fpx  X0=%.2f (mod S=%.3f) phase_neighbours=%s"
          % (rms, X0, X0 % S, near))
    p = np.array(list(p) + [X0])
    sens = near
    out = {"frame": frame, "rms": rms, "params": list(map(float, p)),
           "w": w, "h": h, "phase_rms": sens,
           "X0_modS": round(float(p[7] % S), 3)}
    json.dump(out, open(os.path.join(OUT, "m20b_deckfit_%s.json" % tag), "w"),
              indent=1)
    print("phase sensitivity (X0 shifted):", sens)
    # 可视化
    vis = img.copy()
    for mm in range(64):
        for sd in (-1, 1):
            X0 = p[7]
            x = X0 + mm * S
            if not (30 <= x <= 75):
                continue
            uv = proj([p[0],p[1],p[2],p[3],p[4],p[5],p[6]],
                      np.array([(x, sd * 3.24, model.deck_z(x))]), w, h)[0]
            if 0 <= uv[0] < w and 0 <= uv[1] < h:
                cv2.circle(vis, (int(uv[0]), int(uv[1])), 4,
                           (0, 0, 255) if sd < 0 else (0, 255, 0), 1)
    for sd, cps in ((-1, cl), (1, cr)):
        uv = proj(p[:7], cps, w, h).astype(np.int32)
        cv2.polylines(vis, [uv], False, (255, 0, 255), 1)
    cv2.imwrite(os.path.join(OUT, "m20b_deckfit_%s.jpg" % tag), vis,
                [cv2.IMWRITE_JPEG_QUALITY, 92])
    return out



def cmd_ortho(tag, x0=30.0, x1=78.0, ppm=32.0):
    cfg = json.load(open(os.path.join(OUT, "m20b_deckfit_%s.json" % tag)))
    model = Model(load_ctrl())
    img = cv2.imread(cfg["frame"])
    h, w = img.shape[:2]
    p = cfg["params"]
    y0, y1 = -3.35, 3.35
    W = int(round((x1 - x0) * ppm)); H = int(round((y1 - y0) * ppm))
    xg = x0 + (np.arange(W) + 0.5) / ppm
    yg = y1 - (np.arange(H) + 0.5) / ppm
    X = np.tile(xg, (H, 1))
    Y = np.tile(yg[:, None], (1, W))
    P = np.stack([X.ravel(), Y.ravel(), model.deck_z(X.ravel())], 1)
    uv = proj_pp(p[:9], P).reshape(H, W, 2)
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
    # 质量图
    eps = 0.08
    P2 = P.copy(); P2[:, 0] += eps
    du = np.linalg.norm(proj_pp(p[:9], P2) - proj_pp(p[:9], P), axis=1) / eps
    mpp = np.clip(1.0 / np.maximum(du, 1e-6), 0, 1.0)
    qual = (np.clip(1.0 - mpp / 0.10, 0, 1) * 255).astype(np.uint8).reshape(H, W)
    qual[~valid.reshape(H, W)] = 0
    ortho = out.astype(np.uint8)
    X0 = p[9] if len(p) > 9 else None
    cv2.imwrite(os.path.join(OUT, "m20_ortho_deck_clean.png"), ortho)
    # 柱位线(k 网格, X0 相位) + 0.5m 网格
    for gx in np.arange(math.ceil(x0 / 0.5) * 0.5, x1, 0.5):
        px = int((gx - x0) * ppm)
        cv2.line(ortho, (px, 0), (px, H - 1), (80, 80, 80), 1)
        if abs(gx % 2.0) < 0.25:
            cv2.putText(ortho, "%.0f" % gx, (px + 2, 12), 0, 0.35, (0, 255, 255), 1)
    for gy in np.arange(-3.0, 3.01, 0.5):
        py = int((y1 - gy) * ppm)
        cv2.putText(ortho, "%.1f" % gy, (2, py - 2), 0, 0.35, (0, 255, 255), 1)
        cv2.line(ortho, (0, py), (W - 1, py), (80, 80, 80), 1)
    if X0 is not None:
        j0 = int(math.ceil((x0 - X0) / S)); j1 = int((x1 - X0) / S)
        for j in range(j0, j1 + 1):
            x = X0 + j * S
            px = int((x - x0) * ppm)
            if 0 <= px < W:
                cv2.line(ortho, (px, 0), (px, H - 1), (0, 215, 255), 1)
    cv2.imwrite(os.path.join(OUT, "m20_ortho_deck.png"), ortho)
    cv2.imwrite(os.path.join(OUT, "m20_ortho_deck_q.png"), qual)
    print("m20_ortho_deck.png %dx%d x[%.1f,%.1f]" % (W, H, x0, x1))


def main():
    cmd = sys.argv[1]
    if cmd == "prep":
        frame = sys.argv[2]
        tag = sys.argv[3]
        img = cv2.imread(frame)
        rough = json.load(open(os.path.join(OUT, "rough_curves_1470.json")))
        rough["L"] = [[0, 556], [100, 545], [250, 505]] + \
            [p for p in rough["L"] if p[0] > 260]
        rough["R"] = rough["R"] + [[1280, 596]]
        cur = robust_curves(img, rough)
        json.dump(cur, open(os.path.join(OUT, "m20b_curves_%s.json" % tag), "w"))
        bases = post_bases(img, cur)
        json.dump(bases, open(os.path.join(OUT, "m20b_bases_%s.json" % tag), "w"))
        vis = img.copy()
        for key, col in (("L", (0, 0, 255)), ("R", (0, 255, 0))):
            cv2.polylines(vis, [np.array(cur[key], np.int32)], False, col, 1)
            for b in bases[key]:
                cv2.circle(vis, (int(b["u"]), int(b["v"])), 6, col, 1)
        cv2.imwrite(os.path.join(OUT, "m20b_deck_prep_%s.jpg" % tag), vis)
        print("curves L=%d R=%d bases L=%d R=%d"
              % (len(cur["L"]), len(cur["R"]), len(bases["L"]), len(bases["R"])))
    elif cmd == "ortho":
        cmd_ortho(sys.argv[2],
                  float(sys.argv[3]) if len(sys.argv) > 3 else 30.0,
                  float(sys.argv[4]) if len(sys.argv) > 4 else 78.0,
                  float(sys.argv[5]) if len(sys.argv) > 5 else 32.0)
    elif cmd == "fit":
        frame, tag = sys.argv[2], sys.argv[3]
        model = Model(load_ctrl())
        cur = json.load(open(os.path.join(OUT, "m20b_curves_%s.json" % tag)))
        bases = json.load(open(os.path.join(OUT, "m20b_bases_%s.json" % tag)))
        fit_camera(model, frame, cur, bases, tag)
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
