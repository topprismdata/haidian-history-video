# -*- coding: utf-8 -*-
"""M12 纵向母线几何反演(数据驱动, 九审P0-1/P0-2)。

关键修正(vs M11): 旧模型 springer 恒定 2.5m, 拱冠只随 span 微变 → 冠线太平(矢跨0.017 vs 照片0.034)。
真实桥: 拱冠线跟随桥面 camber(冠顶到桥面近似恒定拱肩厚 spandrel)。
本反演把 camber 作为一等参数, 用注册相机对多张近侧视图的**拱冠点**直接拟合:

  crown_z_i = camber_top - spandrel - camber_A * (2|xc_i|/L)^camber_e
  span_i(x) = span_e + (span_c - span_e)*(1-u)^p_shape,  u=|2i-16|/16
  xc_i = 累积(span+pier), 150m 硬约束闭合 abut
  rise_i = (rise_c)*span_i  (拱冠到起拱线高, 供拱形)

共享几何: [span_c, span_e, p_shape, pier_w, camber_top, camber_A, camber_e, rise_c] (8)
每照片相机 nuisance: [th,ph,D,tz,roll,cx,cy,fs,k1] (9)
观测: 每拱 3 点(冠顶 + 水面左右缘)。
可辨识性: 拟合后对完整图像残差 Jacobian 做相机边缘化 Schur 补 SVD(九审第4项)。
输出 delivery/geometry_m12.json + 更新可辨识性。spandrel 固定=旧中央拱肩厚(冠线只依赖 camber_top-spandrel)。
"""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy.optimize import least_squares

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import facts as F  # noqa: E402
import cam_register as CR  # noqa: E402

L = F.BRIDGE_LEN
HALF_W = CR.HALF_W
SPANDREL = 1.0  # 冠顶到桥面拱肩厚(固定; 冠线只依赖 camber_top-SPANDREL)
GKEYS = ["span_c", "span_e", "p_shape", "pier_w", "camber_top", "camber_A", "camber_e", "rise_c"]
G0 = dict(span_c=8.51, span_e=4.5, p_shape=1.0, pier_w=2.5,
          camber_top=7.75, camber_A=2.70, camber_e=2.0, rise_c=0.50)
GB = dict(span_c=(7.0, 10.0), span_e=(3.0, 6.0), p_shape=(0.5, 2.5), pier_w=(1.8, 3.5),
          camber_top=(6.0, 12.0), camber_A=(1.5, 8.0), camber_e=(1.0, 4.0), rise_c=(0.30, 0.80))


def geom(g):
    i = np.arange(17)
    u = np.abs(2 * i - 16) / 16.0
    span = g["span_e"] + (g["span_c"] - g["span_e"]) * (1 - u) ** g["p_shape"]
    w = g["pier_w"]
    abut = (L - span.sum() - 16 * w) / 2.0
    xc = np.zeros(17)
    x = -L / 2.0 + abut
    for k in range(17):
        xc[k] = x + span[k] / 2.0
        x += span[k] + w
    crown_z = g["camber_top"] - SPANDREL - g["camber_A"] * (2 * np.abs(xc) / L) ** g["camber_e"]
    rise = g["rise_c"] * span
    return xc, span, crown_z, rise, abut


def arch_pts(g, idx, face, wl):
    xc, span, crown_z, rise, abut = geom(g)
    P = []
    for i in idx:
        P.append(CR.to_world(xc[i], face, crown_z[i]))
        P.append(CR.to_world(xc[i] - span[i] / 2.0, face, -wl))
        P.append(CR.to_world(xc[i] + span[i] / 2.0, face, -wl))
    return np.array(P, float)


def register_photo(rel, y0, y1, thr, keep, f_px):
    im = Image.open(os.path.join(ROOT, rel))
    W, H = im.size
    g = np.asarray(im.convert("L"), np.float32)
    det = CR.detect_arches(g, y0, y1, thr=thr)
    arches = [a for a in det if keep[0] < a["crown"][0] < keep[1]]
    K = np.array([[f_px, 0.0, W / 2.0], [0.0, f_px, H / 2.0], [0.0, 0.0, 1.0]])
    return W, H, K, arches


def _clip_center(arches, n=17, center=8):
    """最宽冠=中央孔对齐 center, 越界裁剪。返回 (arches, idx)。"""
    kp = int(np.argmax([a["w"] for a in arches]))
    start = center - kp
    keep_a, keep_i = [], []
    for k, a in enumerate(arches):
        i = start + k
        if 0 <= i <= n - 1:
            keep_a.append(a); keep_i.append(i)
    return keep_a, keep_i


def build_obs():
    # 三张近侧/轻斜视图, 各自人工定拱号(中央孔=idx8 对齐最宽冠)
    specs = []
    # ovf474a34b: 13 冠, idx1..13
    # ovf474a34b: 近侧 13 冠
    rel = "refs/community_photos_openverse/ovf474a34b_File_Seventeen-Arch_Bridge_of_Summer_Palace_JPG.jpg"
    _im = Image.open(os.path.join(ROOT, rel)); _W, _H = _im.size
    W, H, K, ar = register_photo(rel, 1106, 1106 + int(_H * 0.22), 105, (200, 3600), 38.0 * 4592 / 23.4)
    ar, idx = _clip_center(ar)
    specs.append(("ovf474a34b", W, H, K, ar, idx))
    # img_0439: 中央 7 冠
    im2 = Image.open(os.path.join(ROOT, "refs/balustrade_count/src/img_0439.jpg"))
    W2, H2 = im2.size
    g2 = np.asarray(im2.convert("L"), np.float32)
    d2 = CR.detect_arches(g2, 1500, 2350)
    med2 = np.median([a["w"] for a in d2]); ar2 = [a for a in d2 if a["w"] >= 0.5 * med2]
    K2 = np.array([[85.0 * 3888 / 22.2, 0, W2 / 2.0], [0, 85.0 * 3888 / 22.2, H2 / 2.0], [0, 0, 1.0]])
    ar2, idx2 = _clip_center(ar2)
    specs.append(("img_0439", W2, H2, K2, ar2, idx2))
    return specs




def fit(specs, freeze_geom=False, g_init=None):
    tgt0 = np.array([0.0, 0.0, 4.0])
    obs = []
    for name, W, H, K, arches, idx in specs:
        pts2 = []
        for a in arches:
            pts2 += [a["crown"], a["wl"], a["wr"]]
        obs.append(dict(name=name, W=W, H=H, K=K, idx=idx, pts2=np.array(pts2, float)))
    ng = 0 if freeze_geom else 8

    def resid(p):
        g = dict(zip(GKEYS, p[0:8])) if not freeze_geom else dict(g_init)
        xc, span, crown_z, rise, abut = geom(g)
        if abut <= 0.1:
            return np.concatenate([np.full(o["pts2"].size, 1e4) for o in obs])
        res = []
        for j, o in enumerate(obs):
            th, ph, D, tz, roll, cx, cy, fs, k1 = p[ng + 9 * j: ng + 9 * j + 9]
            P3 = arch_pts(g, o["idx"], -HALF_W, 0.0)
            KK = o["K"].copy(); KK[0, 0:2] *= fs; KK[1, 1] *= fs; KK[0, 2] += cx; KK[1, 2] += cy
            C = tgt0 + np.array([D * np.cos(th) * np.cos(ph), D * np.sin(th) * np.cos(ph), D * np.sin(ph)])
            C[2] = max(0.2, C[2])
            M = CR.look_at(C, tgt0 + np.array([0.0, 0.0, tz]), roll)
            pr, z = CR.project(P3, M, KK, k1)
            res.append(np.full(o["pts2"].size, 1e4) if (z <= 0).any() else (pr - o["pts2"]).ravel())
        return np.concatenate(res)

    x0 = [G0[k] for k in GKEYS] if not freeze_geom else []
    lo = [GB[k][0] for k in GKEYS] if not freeze_geom else []
    hi = [GB[k][1] for k in GKEYS] if not freeze_geom else []
    # 相机初值: 每张用单图 solve_pose 估
    for o in obs:
        P3 = arch_pts(G0, o["idx"], -HALF_W, 0.0)
        M0, _, _, _, _ = CR.solve_pose(P3, o["pts2"], o["K"].copy(),
                                       np.ones((len(P3), 2)),
                                       np.array([k % 3 != 0 for k in range(len(P3))]))
        C = M0[0:3, 3]
        d = C - tgt0
        D = float(np.linalg.norm(d)); th = float(np.arctan2(d[1], d[0])); ph = float(np.arcsin(np.clip(d[2] / D, -1, 1)))
        x0 += [th, ph, D, 0, 0, 0, 0, 1.0, 0.0]
        lo += [th - 0.4, -0.4, 60, -6, -0.2, -58, -39, 0.97, -0.02]
        hi += [th + 0.4, 0.4, 900, 6, 0.2, 58, 39, 1.03, 0.02]
    r = least_squares(resid, x0, bounds=(lo, hi), xtol=1e-8, ftol=1e-8)
    g = dict(zip(GKEYS, r.x[0:8])) if not freeze_geom else dict(g_init)
    cams = [r.x[ng + 9 * j: ng + 9 * j + 9] for j in range(len(obs))]
    rr = resid(r.x)
    per = []
    off = 0
    for o in obs:
        e = rr[off:off + o["pts2"].size].reshape(-1, 2); off += o["pts2"].size
        rmse = float(np.sqrt((e ** 2).sum(1).mean()))
        per.append(dict(name=o["name"], n_arch=len(o["idx"]), rmse_px=round(rmse, 2),
                        rmse_pctW=round(rmse / o["W"] * 100, 3),
                        sim=round(1 - float(np.sqrt((e ** 2).sum(1)).mean() / np.hypot(o["W"], o["H"])), 4)))
    return g, cams, per, r, resid, obs, ng


def marginal_svd(resid, r, ng, nobs):
    """相机边缘化后的几何可辨识性 Schur 补(九审第4项正确法)。"""
    p = r.x
    h = 1e-4
    r0 = resid(p)
    J = np.zeros((r0.size, p.size))
    for i in range(p.size):
        pp = p.copy(); pp[i] += h
        pm = p.copy(); pm[i] -= h
        J[:, i] = (resid(pp) - resid(pm)) / (2 * h)
    if ng == 0:
        return None
    Jg, Jc = J[:, :8], J[:, 8:]
    grange = np.array([GB[k][1] - GB[k][0] for k in GKEYS])
    crange = (np.tile([0.8, 0.8, 840, 12, 0.4, 116, 78, 0.06, 0.04], nobs))
    Jg_n = Jg * grange; Jc_n = Jc * crange  # 无量纲参数 q: dr/dq = dr/dp * Δp
    A = np.linalg.pinv(Jc_n.T @ Jc_n, rcond=1e-10)
    Fg = Jg_n.T @ Jg_n - (Jg_n.T @ Jc_n) @ A @ (Jc_n.T @ Jg_n)
    Fg = 0.5 * (Fg + Fg.T)
    w, V = np.linalg.eigh(Fg)
    o = np.argsort(w); w = w[o]; V = V[:, o]
    modes = []
    for i in range(len(w)):
        vec = V[:, i]
        comp = {GKEYS[j]: round(float(vec[j]), 3) for j in range(8) if abs(vec[j]) > 0.15}
        modes.append(dict(rank=i + 1, eig=round(float(w[i]), 5),
                          ident=("DEGENERATE" if w[i] < 1e-2 else "identifiable"),
                          direction=comp))
    return dict(formula="Fg=JgᵀJg−JgᵀJc(JcᵀJc)⁺JcᵀJg, 列按物理范围归一, 相机边缘化",
                eigenvalues=[round(float(x), 5) for x in w],
                condition_number=round(float(w[-1] / max(w[0], 1e-12)), 3) if w[0] > 0 else None,
                modes=modes)


def main():
    specs = build_obs()
    g, cams, per, r, resid, obs, ng = fit(specs)
    xc, span, crown_z, rise, abut = geom(g)
    # 冠线矢跨比(拟合后模型) 用同估计器复测
    def sag(cx, cy):
        cx = np.array(cx, float); cy = np.array(cy, float)
        o = np.argsort(cx); cx, cy = cx[o], cy[o]
        a, b, c = np.polyfit(cx, cy, 2); x0, x1 = cx.min(), cx.max(); xm = (x0 + x1) / 2
        return ((np.polyval([a, b, c], x0) + np.polyval([a, b, c], x1)) / 2 - np.polyval([a, b, c], xm)) / (x1 - x0)
    model_crown_sag = sag(xc[1:14], crown_z[1:14])
    svd = marginal_svd(resid, r, ng, len(obs))
    out = dict(
        status="M12_CAMBER_INVERSION",
        inferred={k: round(float(g[k]), 4) for k in GKEYS},
        derived=dict(abut_m=round(float(abut), 3), span_sum_m=round(float(span.sum()), 3),
                     deck_sagitta_m=round(float(g["camber_A"]), 3),
                     crown_line_sagitta_span=model_crown_sag,
                     crown_z_profile_m=[round(float(z), 3) for z in crown_z],
                     span_profile_m=[round(float(s), 3) for s in span],
                     rise_profile_m=[round(float(x), 3) for x in rise]),
        per_photo=per,
        identifiability=svd,
        note="crown_z 跟随 deck camber(恒定拱肩 spandrel=1.0); camber_A=桥面矢高; camber_e=曲率形状指数",
    )
    os.makedirs(os.path.join(ROOT, "delivery"), exist_ok=True)
    with open(os.path.join(ROOT, "delivery", "geometry_m12.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
