# -*- coding: utf-8 -*-
"""M11-B 参数化几何反演(七审有条件批准: 低维/跨照片/留验证集)。

几何参数 g (对称单调, 8 维, 禁 17 孔自由):
  u_i = |2i-16|/16 (中央孔=0)
  span_i   = span_e + (span_c - span_e)*(1-u)^p_shape
  rise_i   = span_i * (rise_c + rise_g*u)
  springer = s;  pier_w = w;  abut = (150 - Σspan - 16w)/2  (150m 硬约束)
  xc_i     = 累积(span+pier) 中心
landmark: 冠顶 (xc, face, s+rise) / 水面左右缘 (xc∓span/2, face, -wl_off_photo)
相机 nuisance 每照片 10 维: th,ph,D,tz,roll,wl_off,cx,cy,fs,k1 (先验同 cam_register)。
 certify 门见 tools/cert_gates.json (M11-D 事前冻结, ALL AND)。
证据等级: 反演值 = image-inferred (M11-E), 不升级官方/测绘。
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

HALF_W = CR.HALF_W
G0 = dict(span_c=8.51, span_e=4.5, p_shape=1.0, rise_c=0.50, rise_g=0.0,
          springer=2.5, pier_w=2.5)  # springer=湖面以上高
G_BOUNDS = dict(span_c=(7.0, 11.0), span_e=(3.0, 6.5), p_shape=(0.4, 2.5),
                rise_c=(0.30, 0.80), rise_g=(-0.2, 0.2), springer=(1.5, 6.0),
                pier_w=(1.5, 4.0))
GKEYS = ["span_c", "span_e", "p_shape", "rise_c", "rise_g", "springer", "pier_w"]


def geom(g):
    """-> (xc[17], span[17], rise[17], abut) 满足 Σspan+16w+2a=150。"""
    i = np.arange(17)
    u = np.abs(2 * i - 16) / 16.0
    span = g["span_e"] + (g["span_c"] - g["span_e"]) * (1 - u) ** g["p_shape"]
    rise = span * (g["rise_c"] + g["rise_g"] * u)
    w = g["pier_w"]
    abut = (F.BRIDGE_LEN - span.sum() - 16 * w) / 2.0
    xc = np.zeros(17)
    x = -F.BRIDGE_LEN / 2.0 + abut
    for k in range(17):
        xc[k] = x + span[k] / 2.0
        x += span[k] + w
    return xc, span, rise, abut


def landmarks(g, idx, face, wl_off):
    xc, span, rise, abut = geom(g)
    P3, tags = [], []
    for i in idx:
        P3.append(CR.to_world(xc[i], face, g["springer"] + rise[i]))
        tags.append("crown")
        P3.append(CR.to_world(xc[i] - span[i] / 2.0, face, -wl_off))
        tags.append("wl")
        P3.append(CR.to_world(xc[i] + span[i] / 2.0, face, -wl_off))
        tags.append("wr")
    return np.array(P3), tags


def photo_obs(photo_rel):
    from PIL import Image as PI
    path = os.path.join(ROOT, photo_rel)
    im = PI.open(path)
    W, H = im.size
    gray = np.asarray(im.convert("L"), np.float32)
    ex = im.getexif()
    ifd = ex.get_ifd(0x8769)
    fl = float(ifd.get(0x920A) or ex.get(0x920A))
    native_w = float(json.load(open(os.path.join(HERE, "photo_native_width.json")))
                     .get(os.path.basename(photo_rel), 3888.0))
    sensor_w = 22.2
    f_px = fl * native_w / sensor_w
    K = np.array([[f_px, 0.0, W / 2.0], [0.0, f_px, H / 2.0], [0.0, 0.0, 1.0]])
    det = CR.detect_arches(gray, 1500, 2350)
    med = np.median([a["w"] for a in det])
    arches = [a for a in det if a["w"] >= 0.5 * med]
    return W, H, K, arches


def fit_photo(photo_rel, g_fix=None, g0=None):
    """单照片: 相机 9 参(th,ph,D,tz,roll,cx,cy,fs,k1) + 几何 7 参(可选冻结)。"""
    W, H, K, arches = photo_obs(photo_rel)
    k_peak = int(np.argmax([a["w"] for a in arches]))
    shift = 8 - k_peak
    idx = list(range(shift, shift + len(arches)))
    pts2 = []
    for a in arches:
        pts2 += [a["crown"], a["wl"], a["wr"]]
    pts2 = np.array(pts2, float)
    g0 = dict(G0 if g0 is None else g0)
    tgt0 = np.array([0.0, 0.0, 4.0])
    ng = 0 if g_fix is not None else 7

    def unpack(p):
        cam = list(p[0:9])
        g = dict(g_fix) if g_fix is not None else dict(zip(GKEYS, p[9:16]))
        return cam, g

    def resid(p):
        cam, g = unpack(p)
        th, ph, D, tz, roll, cx, cy, fs, k1 = cam
        xc, span, rise, abut = geom(g)
        if abut <= 0.1:
            return np.full(pts2.size, 1e4)
        P3, _ = landmarks(g, idx, -HALF_W, 0.0)
        KK = K.copy()
        KK[0, 0:2] *= fs
        KK[1, 1] *= fs
        KK[0, 2] += cx
        KK[1, 2] += cy
        C = tgt0 + np.array([D * np.cos(th) * np.cos(ph),
                             D * np.sin(th) * np.cos(ph),
                             D * np.sin(ph)])
        C[2] = max(0.2, C[2])
        M = CR.look_at(C, tgt0 + np.array([0.0, 0.0, tz]), roll)
        pr, z = CR.project(P3, M, KK, k1)
        if (z <= 0).any():
            return np.full(pts2.size, 1e4)
        return (pr - pts2).ravel()

    best = None
    for th in np.arange(0, 2 * np.pi, np.pi / 6):
        x0 = [th, 0.10, 210.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0]
        lo = [th - 0.3, -0.35, 60, -6, -0.2, -58, -39, 0.97, -0.02]
        hi = [th + 0.3, 0.35, 900, 6, 0.2, 58, 39, 1.03, 0.02]
        if g_fix is None:
            x0 += [g0[k] for k in GKEYS]
            lo += [G_BOUNDS[k][0] for k in GKEYS]
            hi += [G_BOUNDS[k][1] for k in GKEYS]
        r = least_squares(resid, x0, bounds=(lo, hi))
        if best is None or r.cost < best.cost:
            best = r
    cam, g = unpack(best.x)
    r = resid(best.x).reshape(-1, 2)
    rmse = float(np.sqrt((r ** 2).sum(1).mean()))
    sim = 1.0 - float(np.sqrt((r ** 2).sum(1)).mean() / np.hypot(W, H))
    out = dict(photo=photo_rel, arch_indices=idx, rmse_px=round(rmse, 2),
               similarity_landmarks=round(sim, 4), cam=[round(float(v), 4) for v in cam],
               mode="joint" if g_fix is None else "camera_only")
    if g_fix is None:
        s2 = 2 * best.cost / max(1, pts2.size * 2 - best.x.size)
        try:
            cov = np.linalg.inv(best.jac.T @ best.jac) * s2
            sd = np.sqrt(np.diag(cov))
            out["geom_ci_1sigma"] = {k: round(float(sd[9 + j]), 4) for j, k in enumerate(GKEYS)}
        except np.linalg.LinAlgError:
            out["geom_ci_1sigma"] = None
        out["geom"] = {k: round(float(g[k]), 4) for k in GKEYS}
        xc, span, rise, abut = geom(g)
        out["span_sum"] = round(float(span.sum()), 3)
        out["abut"] = round(float(abut), 3)
    return out


def detect_clean(photo_rel, thr_list=(95, 110, 125)):
    """band/阈值扫描 + 半宽剔除, 返回 (W,H,K,arches)。end-on 照片亦可用。"""
    W, H, K0, _ = photo_obs(photo_rel)
    from PIL import Image as PI
    g = np.asarray(PI.open(os.path.join(ROOT, photo_rel)).convert("L"), np.float32)
    best = None
    for y0 in range(int(H * 0.35), int(H * 0.85), max(1, int(H * 0.04))):
        for thr in thr_list:
            det = CR.detect_arches(g, y0, min(H, y0 + int(H * 0.22)), thr=thr)
            if not det:
                continue
            med = np.median([a["w"] for a in det])
            det = [a for a in det if a["w"] >= 0.5 * med]
            if len(det) >= 6 and (best is None or len(det) > len(best[2])):
                best = (y0, thr, det)
    return W, H, K0, best[2] if best else []


def align_hypotheses(arches, n=17):
    """end-on: 宽单调 -> 两端假设; side: 宽峰=中央孔。返回 idx 候选列表。"""
    w = np.array([a["w"] for a in arches], float)
    k = len(arches)
    hyp = []
    kp = int(np.argmax(w))
    sh = 8 - kp
    if 0 <= sh and sh + k <= n:
        hyp.append(list(range(sh, sh + k)))
    hyp.append(list(range(0, k)))
    hyp.append(list(range(n - k, n)))
    seen = set()
    out = []
    for h in hyp:
        t = tuple(h)
        if t not in seen and h[-1] < n:
            seen.add(t)
            out.append(h)
    return out


def fit_joint(specs, g_fix=None):
    """specs: [(photo_rel, idx), ...]; 共享 g, 每照片 9 相机参。"""
    obs = []
    for photo_rel, idx in specs:
        W, H, K, arches = detect_clean(photo_rel) if not isinstance(idx, tuple) else (None,) * 4
        obs.append((photo_rel, idx, W, H, K, arches))
    pts2_all, meta = [], []
    for photo_rel, idx, W, H, K, arches in obs:
        pts2 = []
        for a in arches:
            pts2 += [a["crown"], a["wl"], a["wr"]]
        pts2_all.append(np.array(pts2, float))
        meta.append((idx, W, H, K))
    nph = len(obs)
    tgt0 = np.array([0.0, 0.0, 4.0])

    def resid(p):
        g = dict(zip(GKEYS, p[0:7])) if g_fix is None else dict(g_fix)
        xc, span, rise, abut = geom(g)
        if abut <= 0.1:
            return np.concatenate([np.full(q.size, 1e4) for q in pts2_all])
        res = []
        coff = 0 if g_fix is None else 0
        coff = 7 if g_fix is None else 0
        for j, (idx, W, H, K) in enumerate(meta):
            cam = p[coff + 9 * j: coff + 9 * j + 9]
            th, ph, D, tz, roll, cx, cy, fs, k1 = cam
            P3, _ = landmarks(g, idx, -HALF_W, 0.0)
            KK = K.copy()
            KK[0, 0:2] *= fs
            KK[1, 1] *= fs
            KK[0, 2] += cx
            KK[1, 2] += cy
            C = tgt0 + np.array([D * np.cos(th) * np.cos(ph),
                                 D * np.sin(th) * np.cos(ph),
                                 D * np.sin(ph)])
            C[2] = max(0.2, C[2])
            M = CR.look_at(C, tgt0 + np.array([0.0, 0.0, tz]), roll)
            pr, z = CR.project(P3, M, KK, k1)
            if (z <= 0).any():
                res.append(np.full(pts2_all[j].size, 1e4))
            else:
                res.append((pr - pts2_all[j]).ravel())
        return np.concatenate(res)

    best = None
    for th0 in np.arange(0, 2 * np.pi, np.pi / 6):
        x0, lo, hi = [], [], []
        if g_fix is None:
            x0 += [G0[k] for k in GKEYS]
            lo += [G_BOUNDS[k][0] for k in GKEYS]
            hi += [G_BOUNDS[k][1] for k in GKEYS]
        for j in range(nph):
            x0 += [th0, 0.10, 210.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0]
            lo += [th0 - 0.3, -0.35, 60, -6, -0.2, -58, -39, 0.97, -0.02]
            hi += [th0 + 0.3, 0.35, 900, 6, 0.2, 58, 39, 1.03, 0.02]
        r = least_squares(resid, x0, bounds=(lo, hi))
        if best is None or r.cost < best.cost:
            best = r
    p = best.x
    g = dict(zip(GKEYS, p[0:7])) if g_fix is None else dict(g_fix)
    out = dict(mode="joint" if g_fix is None else "camera_only", specs=[s[0] for s in specs])
    if g_fix is None:
        out["geom"] = {k: round(float(g[k]), 4) for k in GKEYS}
        xc, span, rise, abut = geom(g)
        out["span_sum"] = round(float(span.sum()), 3)
        out["abut"] = round(float(abut), 3)
        s2 = 2 * best.cost / max(1, best.fun.size - best.x.size)
        try:
            cov = np.linalg.inv(best.jac.T @ best.jac) * s2
            sd = np.sqrt(np.diag(cov))
            out["geom_ci_1sigma"] = {k: round(float(sd[j]), 4) for j, k in enumerate(GKEYS)}
        except np.linalg.LinAlgError:
            out["geom_ci_1sigma"] = None
    per = []
    rr = resid(p)
    off = 0
    for j, (idx, W, H, K) in enumerate(meta):
        e = rr[off:off + pts2_all[j].size].reshape(-1, 2)
        off += pts2_all[j].size
        per.append(dict(photo=obs[j][0], n_arch=len(idx),
                        rmse_px=round(float(np.sqrt((e ** 2).sum(1).mean())), 2),
                        similarity=round(1 - float(np.sqrt((e ** 2).sum(1)).mean() / np.hypot(W, H)), 4)))
    out["per_photo"] = per
    return out


if __name__ == "__main__" and os.environ.get("GEOM_JOINT"):
    import itertools
    A = "refs/balustrade_count/src/img_0439.jpg"
    B = "refs/balustrade_count/src/closer_2017.jpg"
    HOLD = "refs/balustrade_count/src/winter_20201221160537.jpg"
    Wa, Ha, Ka, ar_a = detect_clean(A)
    Wb, Hb, Kb, ar_b = detect_clean(B)
    hyp_a = align_hypotheses(ar_a)
    hyp_b = align_hypotheses(ar_b)
    results = []
    for ia, ib in itertools.product(hyp_a, hyp_b):
        r = fit_joint([(A, ia), (B, ib)])
        r["idx"] = [ia, ib]
        results.append(r)
        print("hyp", ia[0], ib[0], "rmse", [q["rmse_px"] for q in r["per_photo"]])
    best = min(results, key=lambda r: sum(q["rmse_px"] for q in r["per_photo"]))
    g = {k: v for k, v in best["geom"].items()}
    hold = []
    Wh, Hh, Kh, ar_h = detect_clean(HOLD)
    for ih in align_hypotheses(ar_h):
        rh = fit_joint([(HOLD, ih)], g_fix=g)
        hold.append(dict(idx=ih, per_photo=rh["per_photo"]))
    rep = dict(best_joint=best, holdout_winter=hold,
               gates=json.load(open(os.path.join(HERE, "cert_gates.json"))))
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    with open(os.path.join(ROOT, "delivery", "29_geom_inversion_pilot.json"), "w") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    photos = sys.argv[1:] or ["refs/balustrade_count/src/img_0439.jpg"]
    rep = [fit_photo(p) for p in photos]
    base = [fit_photo(p, g_fix=G0) for p in photos]
    for a, b in zip(rep, base):
        a["rmse_camera_only_baseline"] = b["rmse_px"]
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    with open(os.path.join(ROOT, "delivery", "29_geom_inversion_pilot.json"), "w") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)
