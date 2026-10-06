#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""m20b: A08 逐块重描读图包.
子命令:
  prep   ARCH TAG      -> 无网格正射 m20b_ortho_<TAG>_clean.png + 0.1m 网格
                          m20b_ortho_<TAG>_g01.png + 质量图
  strips ARCH TAG SP   -> 每层读图条带 m20b_read_<TAG>_cNN.png (3x, 0.1m 网格,
                          旧谱边界=绿, 自动候选=橙三角)
  cand   ARCH TAG      -> 自动候选 JSON (无网格图上逐列暗谷, 可见域掩膜)
坐标: x=桥轴 m, z=水面起算 m (M19 基准). ppm=80.
"""
import json
import math
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from m20_pipeline import (Model, load_ctrl, load_pose, load_stones, OUT,  # noqa
                          ortho_rectify, xz_to_px)

PPM = 80.0


def enhance(crop):
    """CLAHE + unsharp: 突出缝线(读图专用, 不改数据)."""
    g = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    g = cv2.createCLAHE(2.6, (8, 8)).apply(g)
    g = cv2.GaussianBlur(g, (0, 0), 2.2)
    g = cv2.addWeighted(cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY), 1.55, g, -0.55, 0)
    return cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)


def arch_ext(model, i, margin=2.0):
    a = model.arches[i]
    x0 = a["xc"] - a["a"] - margin
    x1 = a["xc"] + a["a"] + margin
    z1 = model.deck_z(a["xc"]) + 0.45
    return x0, x1, 0.0, z1


def hole_zcut(model, i):
    """孔洞切割下沿 z(x): |xr|<a 用 extrados+GAP; a<=|xr|<a+GAP 用 spz;
    更外侧无洞(返回 0 = 全带可见)."""
    a = model.arches[i]
    xs = np.arange(a["bay_x0"] - 0.3, a["bay_x1"] + 0.3, 1.0 / PPM)
    zc = []
    for x in xs:
        xr = abs(x - a["xc"])
        if xr < a["a"]:
            zc.append(model.extrados_z(x, i) + 0.01)
        elif xr < a["a"] + 0.02:
            zc.append(a["spz"])
        else:
            zc.append(0.0)
    return xs, np.array(zc)


def cmd_prep(arch, tag):
    model = Model(load_ctrl())
    pose = load_pose(tag)
    i = int(arch)
    ortho, ext, qual = ortho_rectify(model, pose, i)
    cv2.imwrite(os.path.join(OUT, "m20b_ortho_%s_a%d_clean.png" % (tag, i)), ortho)
    cv2.imwrite(os.path.join(OUT, "m20b_ortho_%s_a%d_q.png" % (tag, i)), qual)
    # 0.1m 网格版
    im = ortho.copy()
    x0, x1, z0, z1 = ext[:4]
    H, W = im.shape[:2]
    x = math.ceil(x0 / 0.1) * 0.1
    while x <= x1 + 1e-6:
        u, _ = xz_to_px(ext, x, 0)
        major = abs(x % 0.5) < 1e-6
        col = (150, 150, 150) if major else (70, 70, 70)
        cv2.line(im, (int(u), 0), (int(u), H - 1), col, 1)
        if major:
            cv2.putText(im, "%+.1f" % x, (int(u) + 2, 12), 0, 0.34, (0, 255, 255), 1)
        x += 0.1
    z = 0.1
    while z <= z1:
        _, v = xz_to_px(ext, 0, z)
        major = abs(z % 0.5) < 1e-6
        col = (150, 150, 150) if major else (70, 70, 70)
        cv2.line(im, (0, int(v)), (W - 1, int(v)), col, 1)
        if major:
            cv2.putText(im, "%.1f" % z, (3, int(v) - 3), 0, 0.34, (0, 255, 255), 1)
        z += 0.1
    # 模型特征线: 孔切割下沿(白) + 湾缘(黄)
    xs, zc = hole_zcut(model, i)
    pts = [tuple(int(t) for t in xz_to_px(ext, float(x), float(z)))
           for x, z in zip(xs, zc) if 0 <= z <= z1]
    cv2.polylines(im, [np.array(pts)], False, (255, 255, 255), 1, cv2.LINE_AA)
    for bx in (model.arches[i]["bay_x0"], model.arches[i]["bay_x1"]):
        u, _ = xz_to_px(ext, bx, 0)
        cv2.line(im, (int(u), 0), (int(u), H - 1), (0, 215, 255), 1)
    cv2.imwrite(os.path.join(OUT, "m20b_ortho_%s_a%d_g01.png" % (tag, i)), im)
    print("prep done: clean/g01/q x[%.2f,%.2f] z[0,%.2f]" % (x0, x1, z1))


def _course_bands(model, stones, i):
    a = model.arches[i]
    deck_top = max(model.deck_z(a["bay_x0"] + (a["bay_x1"] - a["bay_x0"]) * k / 15.0)
                   for k in range(16)) - 0.10
    cs = sorted(stones["courses"], key=lambda c: c["z0"])
    out = []
    for ci, c in enumerate(cs):
        z0c = c["z0"]
        z1c = cs[ci + 1]["z0"] if ci + 1 < len(cs) else deck_top
        out.append((ci, z0c, z1c, c))
    return out


def cmd_autoedges(arch, tag, sp=None):
    """逐边定量核验: 候选(C)+旧边(O) 在层带可见域的横向梯度剖面峰值.
    verdict: accept(候选, conf足, |off|<=0.05) / retain(旧边, |off|<=0.15)
    / weak(信号弱) / hidden(无可见域). 写 m20b_edges_<TAG>_a<A>.json"""
    i = int(arch)
    model = Model(load_ctrl())
    pose = load_pose(tag)
    spath = sp or os.path.join(HERE, "stones", "stones_p%d.json" % i)
    stones = load_stones(spath)
    ortho, ext, _ = ortho_rectify(model, pose, i)
    g = cv2.createCLAHE(2.6, (8, 8)).apply(cv2.cvtColor(ortho, cv2.COLOR_BGR2GRAY))
    gray = g.astype(np.float32)
    gu = np.abs(np.diff(gray, axis=1))
    xs_hole, zc_hole = hole_zcut(model, i)
    x0, x1, _, z1e = ext[:4]
    a = model.arches[i]

    def band_rows(z0c, z1c, u):
        x = x0 + (u + 0.5) / PPM
        j = int(np.clip((x - xs_hole[0]) * PPM, 0, len(zc_hole) - 1))
        ins = min(0.10, 0.3 * max(z1c - z0c, 0.0))
        zhi, zlo = z1c - ins, z0c + ins
        zbot = max(zlo, zc_hole[j] + 0.06)
        if zbot >= zhi:
            return None
        r1 = int(round((z1e - zhi) * PPM))
        r0 = int(round((z1e - zbot) * PPM))
        return (r1, r0) if r0 > r1 else None

    out = []
    for ci, z0c, z1c, c in _course_bands(model, stones, i):
        cands = [(x, "C") for x in
                 json.load(open(os.path.join(OUT, "m20b_cand_%s_a%d.json"
                                             % (tag, i))))[ci]["cand"]]
        olds = [(float(x), "O") for x in (c.get("blocks") or [])
                if a["bay_x0"] + 0.05 < float(x) < a["bay_x1"] - 0.05]
        rows = []
        for x, kind in cands + olds:
            uc = int(round((x - x0) * PPM))
            r = band_rows(z0c, z1c, uc)
            if r is None:
                rows.append({"x": x, "kind": kind, "verdict": "hidden"})
                continue
            r1, r0 = r
            w = int(round(0.16 * PPM))
            lo, hi = max(uc - w, 1), min(uc + w, gray.shape[1] - 1)
            prof = gu[r1:r0, lo:hi].mean(axis=0)
            if len(prof) < 9:
                rows.append({"x": x, "kind": kind, "verdict": "hidden"})
                continue
            k = int(np.argmax(prof))
            med = float(np.median(prof)) + 1e-6
            conf = float(prof[k] / med)
            p1, p2, p3 = prof[max(k - 1, 0)], prof[k], prof[min(k + 1, len(prof) - 1)]
            den = p1 - 2 * p2 + p3
            sub = 0.5 * (p1 - p3) / den if abs(den) > 1e-9 else 0.0
            u_fit = lo + k + max(-1.0, min(1.0, sub)) + 0.5
            x_fit = x0 + u_fit / PPM
            off = x_fit - x
            if kind == "C":
                v = "accept" if (conf >= 2.0 and abs(off) <= 0.12) else "weak"
            else:
                v = "retain" if (conf >= 1.8 and abs(off) <= 0.15) else \
                    ("shift" if conf >= 1.8 else "weak")
            rows.append({"x": float(x), "kind": kind,
                         "x_fit": round(float(x_fit), 3),
                         "off": round(float(off), 3),
                         "conf": round(float(conf), 2), "verdict": v})
        out.append({"ci": ci, "z0": round(z0c, 3), "edges": rows})
        print("c%02d z0=%.2f: %s" % (ci, z0c,
              [(r["kind"], round(r["x"], 2), r["verdict"],
                r.get("conf", "-")) for r in rows]))
    with open(os.path.join(OUT, "m20b_edges_%s_a%d.json" % (tag, i)), "w") as f:
        json.dump(out, f, indent=1)


def cmd_zfit(arch, tag, sp=None):
    """逐层量测: 照片中该层线相对谱 z0 的亚像素竖向偏移(可见域中位数).
    输出建议 z0 与每层 offsets。"""
    i = int(arch)
    model = Model(load_ctrl())
    pose = load_pose(tag)
    spath = sp or os.path.join(HERE, "stones", "stones_p%d.json" % i)
    stones = load_stones(spath)
    ortho, ext, _ = ortho_rectify(model, pose, i)
    g = cv2.createCLAHE(2.6, (8, 8)).apply(cv2.cvtColor(ortho, cv2.COLOR_BGR2GRAY))
    gray = g.astype(np.float32)
    xs_hole, zc_hole = hole_zcut(model, i)
    x0, x1, _, z1e = ext[:4]
    W = gray.shape[1]
    out = []
    for ci, z0c, z1c, c in _course_bands(model, stones, i):
        offs = []
        for u in range(2, W - 2):
            x = x0 + (u + 0.5) / PPM
            a = model.arches[i]
            if not (a["bay_x0"] + 0.2 < x < a["bay_x1"] - 0.2):
                continue
            j = int(np.clip((x - xs_hole[0]) * PPM, 0, len(zc_hole) - 1))
            ztop = zc_hole[j]
            if ztop > z0c + 0.02:      # 层线在洞内/水下 -> 不可见
                continue
            v0 = int(round((z1e - (z0c + 0.22)) * PPM))
            v1 = int(round((z1e - (z0c - 0.22)) * PPM))
            if v0 < 2 or v1 >= gray.shape[0] - 2:
                continue
            prof = gray[v0:v1, u - 1:u + 2].mean(axis=1)
            k = int(np.argmin(prof))
            if k < 4 or k > len(prof) - 5:
                continue
            # 谷底须显著: 比两侧肩(±4px)暗 >=8
            if not (prof[k] < prof[max(k - 5, 0):k - 2].mean() - 8.0
                    and prof[k] < prof[k + 3:k + 6].mean() - 8.0):
                continue
            p1, p2, p3 = prof[k - 1], prof[k], prof[k + 1]
            den = p1 - 2 * p2 + p3
            sub = 0.5 * (p1 - p3) / den if abs(den) > 1e-9 else 0.0
            off_px = (k + max(-1.0, min(1.0, sub))) - 0.5 * len(prof)
            if abs(off_px) > 10:       # 只认 ±0.125m 内的线
                continue
            offs.append(off_px / PPM)
        if len(offs) >= 6:
            med = float(np.median(offs))
            mad = float(np.median(np.abs(np.array(offs) - med)))
            out.append({"ci": ci, "z0": round(z0c, 3), "n": len(offs),
                        "off_m": round(med, 4), "mad_m": round(mad, 4),
                        "z0_fit": round(z0c + med, 3)})
        else:
            out.append({"ci": ci, "z0": round(z0c, 3), "n": len(offs),
                        "off_m": None, "z0_fit": None})
        print(out[-1])
    with open(os.path.join(OUT, "m20b_zfit_%s_a%d.json" % (tag, i)), "w") as f:
        json.dump(out, f, indent=1)


def cmd_layers(arch, tag):
    """层线复读: 两腹可见墙带逐行灰度剖面 -> 暗谷亚像素 -> 层线 z 候选.
    输出 m20b_layers_<TAG>_a<A>.json + 侧剖图."""
    i = int(arch)
    model = Model(load_ctrl())
    pose = load_pose(tag)
    ortho, ext, _ = ortho_rectify(model, pose, i)
    gray = cv2.cvtColor(ortho, cv2.COLOR_BGR2GRAY).astype(np.float32)
    g = cv2.createCLAHE(2.6, (8, 8)).apply(cv2.cvtColor(ortho, cv2.COLOR_BGR2GRAY))
    g = g.astype(np.float32)
    xs_hole, zc_hole = hole_zcut(model, i)
    x0, x1, _, z1e = ext[:4]
    H, W = gray.shape
    # 可见掩膜(洞以上)与侧带列范围
    vis = np.ones((H, W), bool)
    for u in range(W):
        x = x0 + (u + 0.5) / PPM
        j = int(np.clip((x - xs_hole[0]) * PPM, 0, len(zc_hole) - 1))
        r = int(round((z1e - zc_hole[j]) * PPM))
        if 0 <= r < H:
            vis[r:, u] = False          # z 低于切割线 -> 洞/水
    a = model.arches[i]
    bands = []
    for lo, hi in ((a["bay_x0"] + 0.15, a["bay_x0"] + 1.35),
                   (a["bay_x1"] - 1.35, a["bay_x1"] - 0.15)):
        u0 = int((lo - x0) * PPM)
        u1 = int((hi - x0) * PPM)
        prof = np.where(vis[:, u0:u1], g[:, u0:u1], np.nan).mean(axis=1)
        prof_s = np.convolve(np.nan_to_num(prof, nan=np.nanmean(prof)),
                             np.ones(3) / 3.0, "same")
        pad = np.pad(prof_s, 15, mode="edge")
        bg = np.array([np.median(pad[k:k + 31]) for k in range(len(prof_s))])
        d = bg - prof_s                  # 暗谷
        d[~np.isfinite(d)] = 0
        cand = []
        u = 3
        while u < len(d) - 4:
            if d[u] >= 8 and d[u] >= d[u - 1] and d[u] >= d[u + 1]:
                d1, d2, d3 = d[u - 1], d[u], d[u + 1]
                den = d1 - 2 * d2 + d3
                off = 0.5 * (d1 - d3) / den if abs(den) > 1e-9 else 0.0
                z = z1e - (u + off + 0.5) / PPM
                cand.append(round(float(z), 3))
                u += 4
            else:
                u += 1
        bands.append({"span": [lo, hi], "lines": cand})
        print("flank x[%.2f,%.2f]: %s" % (lo, hi, cand))
    with open(os.path.join(OUT, "m20b_layers_%s_a%d.json" % (tag, i)), "w") as f:
        json.dump(bands, f, indent=1)


def cmd_cand(arch, tag):
    """自动候选: 无网格正射逐列暗谷(层带内), 输出 JSON。"""
    i = int(arch)
    model = Model(load_ctrl())
    pose = load_pose(tag)
    stones = load_stones(os.path.join(HERE, "stones", "stones_p%d.json" % i))
    ortho, ext, _ = ortho_rectify(model, pose, i)
    gray = enhance(ortho).astype(np.float32)[..., 0]
    xs_hole, zc_hole = hole_zcut(model, i)
    x0, x1, z0e, z1e = ext[:4]
    out = []
    for ci, z0c, z1c, c in _course_bands(model, stones, i):
        # 可见行掩膜(按列): 层带内位于洞切割线以上的行
        va = int(round((z1e - (z1c - 0.10)) * PPM))
        vb = int(round((z1e - (z0c + 0.10)) * PPM))
        va = max(va, 0)
        rows = []
        for u in range(gray.shape[1]):
            x = x0 + (u + 0.5) / PPM
            j = int(np.clip((x - xs_hole[0]) * PPM, 0, len(zc_hole) - 1))
            ztop = zc_hole[j]
            ins = min(0.10, 0.3 * max(z1c - z0c, 0.0))
            zhi, zlo = z1c - ins, z0c + ins
            zbot = max(zlo, ztop + 0.06)   # 洞缘内缩, 防洞暗边污染剖面
            if zbot >= zhi:
                rows.append(np.nan)
                continue
            r1 = int(round((z1e - zhi) * PPM))
            r0 = int(round((z1e - zbot) * PPM))
            rows.append(float(gray[r1:r0, u].mean()))
        prof = np.array(rows)
        ok = ~np.isnan(prof)
        if ok.sum() < 30:
            out.append({"ci": ci, "z0": z0c, "cand": []})
            continue
        # 背景剔除: 滑动中位数(窗 41px)后取 暗谷 + 水平梯度能量(竖缝=暗亮对)
        pad = np.pad(prof, 21, mode="edge")
        bg = np.array([np.nanmedian(pad[k:k + 43]) for k in range(len(prof))])
        dark = bg - prof
        dark[~ok] = 0
        gcol = np.zeros_like(dark)
        gu = np.zeros_like(gray)
        gu[:, :-1] = np.abs(np.diff(gray, axis=1))
        for u in range(len(dark)):
            if not ok[u]:
                continue
            x = x0 + (u + 0.5) / PPM
            j = int(np.clip((x - xs_hole[0]) * PPM, 0, len(zc_hole) - 1))
            zz1 = min(z1c - 0.10, zc_hole[j])
            if zz1 <= z0c + 0.10:
                continue
            r1 = int(round((z1e - zz1) * PPM))
            r0 = int(round((z1e - (z0c + 0.10)) * PPM))
            gcol[u] = float(gu[r1:r0, max(u - 1, 0):u + 2].mean())
        d = 1.0 * dark + 2.0 * gcol
        d = np.convolve(d, np.ones(3) / 3.0, mode="same")
        vis = d[ok]
        med = float(np.median(vis))
        mad = float(np.median(np.abs(vis - med))) + 1e-6
        thr = max(2.5, med + 3.0 * mad)
        floor = max(2.5, 0.5 * thr)
        peaks = []
        u = 2
        while u < len(d) - 3:
            if d[u] >= floor and d[u] >= d[u - 1] and d[u] >= d[u + 1]:
                peaks.append(u)
                u += 3
            else:
                u += 1
        peaks.sort(key=lambda u: -d[u])
        cand = []
        a = model.arches[i]
        for u in peaks:
            if d[u] < floor or len(cand) >= 12:
                break
            xx = x0 + (u + 0.5) / PPM
            if not (a["bay_x0"] + 0.15 < xx < a["bay_x1"] - 0.15):
                continue
            if any(abs(xx - c) < 0.3 for c in cand):
                continue
            d1, d2, d3 = d[u - 1], d[u], d[u + 1]
            den = d1 - 2 * d2 + d3
            off = 0.5 * (d1 - d3) / den if abs(den) > 1e-9 else 0.0
            xx = x0 + (u + off + 0.5) / PPM
            cand.append(round(xx, 3))
        cand.sort()
        out.append({"ci": ci, "z0": round(z0c, 3), "cand": cand})
    with open(os.path.join(OUT, "m20b_cand_%s_a%d.json" % (tag, i)), "w") as f:
        json.dump(out, f, indent=1)
    print("cand:", [(o["ci"], len(o["cand"])) for o in out])


def cmd_strips(arch, tag, sp=None):
    i = int(arch)
    model = Model(load_ctrl())
    pose = load_pose(tag)
    spath = sp or os.path.join(HERE, "stones", "stones_p%d.json" % i)
    stones = load_stones(spath)
    cand = {}
    cpath = os.path.join(OUT, "m20b_cand_%s_a%d.json" % (tag, i))
    if os.path.isfile(cpath):
        cand = {o["ci"]: o["cand"] for o in json.load(open(cpath))}
    ortho, ext, _ = ortho_rectify(model, pose, i)
    z1e = ext[3]
    xs_hole, zc_hole = hole_zcut(model, i)
    Z = 3
    a = model.arches[i]
    sx0, sx1 = a["bay_x0"] - 0.25, a["bay_x1"] + 0.25
    for ci, z0c, z1c, c in _course_bands(model, stones, i):
        zctx = 0.22
        v_lo = xz_to_px(ext, 0, min(z1c + zctx, z1e))[1]
        v_hi = xz_to_px(ext, 0, max(z0c - zctx, 0.02))[1]
        u_lo, _ = xz_to_px(ext, sx0, 0)
        u_hi, _ = xz_to_px(ext, sx1, 0)
        u_lo, u_hi, v_lo, v_hi = int(u_lo), int(u_hi), max(0, int(v_lo)), int(v_hi)
        crop = ortho[v_lo:v_hi, u_lo:u_hi]
        if crop.shape[0] < 4:
            continue
        big = cv2.resize(enhance(crop), (crop.shape[1] * Z, crop.shape[0] * Z),
                         interpolation=cv2.INTER_CUBIC)
        # 网格: 0.1m 竖线(25% 透明混合, 端头刻度实线)
        ov = big.copy()
        x = math.ceil(sx0 / 0.1) * 0.1
        while x <= sx1 + 1e-6:
            u, _ = xz_to_px(ext, x, 0)
            uu = int((u - u_lo) * Z)
            major = abs(x % 0.5) < 1e-6
            col = (160, 160, 160) if major else (60, 60, 60)
            cv2.line(ov, (uu, 0), (uu, big.shape[0] - 1), col, 1)
            x += 0.1
        cv2.addWeighted(ov, 0.22, big, 0.78, 0, big)
        x = math.ceil(sx0 / 0.1) * 0.1
        while x <= sx1 + 1e-6:
            u, _ = xz_to_px(ext, x, 0)
            uu = int((u - u_lo) * Z)
            major = abs(x % 0.5) < 1e-6
            col = (170, 170, 170) if major else (70, 70, 70)
            t = 9 if major else 5
            cv2.line(big, (uu, 0), (uu, t), col, 1)
            cv2.line(big, (uu, big.shape[0] - 1 - t), (uu, big.shape[0] - 1), col, 1)
            if major:
                cv2.putText(big, "%+.1f" % x, (uu + 2, 13), 0, 0.5, (0, 255, 255), 1)
                cv2.putText(big, "%+.1f" % x, (uu + 2, big.shape[0] - 4), 0, 0.5,
                            (0, 255, 255), 1)
            x += 0.1
        # 洞切割线(白)
        pts = []
        for x in np.arange(sx0, sx1, 0.02):
            j = int(np.clip((x - xs_hole[0]) * PPM, 0, len(zc_hole) - 1))
            z = zc_hole[j]
            if z0c - 0.05 <= z <= z1c + 0.05:
                u, v = xz_to_px(ext, x, z)
                pts.append((int((u - u_lo) * Z), int((v - v_lo) * Z)))
        if len(pts) > 2:
            cv2.polylines(big, [np.array(pts)], False, (255, 255, 255), 1, cv2.LINE_AA)
        # 旧谱边界(绿, 底部三角)
        bl = c.get("blocks") or []
        for e in bl:
            if sx0 < e < sx1:
                u, _ = xz_to_px(ext, e, 0)
                uu = int((u - u_lo) * Z)
                cv2.line(big, (uu, big.shape[0] - 14), (uu, big.shape[0] - 1),
                         (0, 255, 0), 1)
        # 自动候选(橙, 顶部倒三角)
        for e in cand.get(ci, []):
            if sx0 < e < sx1:
                u, _ = xz_to_px(ext, e, 0)
                uu = int((u - u_lo) * Z)
                cv2.line(big, (uu, 16), (uu, 30), (0, 130, 255), 1)
                cv2.circle(big, (uu, 12), 4, (0, 130, 255), 1)
        cv2.imwrite(os.path.join(OUT, "m20b_read_%s_a%d_c%02d_z%.2f.png"
                                 % (tag, i, ci, z0c)), big)
    print("strips written:", len(stones["courses"]))


def cmd_cards(arch, tag):
    """每层候选卡片: 每个候选 x 的 6x 放大窗口(±0.32m), 十字线+刻度,
    供逐个判 接受/移位/否决。输出 m20b_cards_<TAG>_a<A>_cNN.png"""
    i = int(arch)
    model = Model(load_ctrl())
    pose = load_pose(tag)
    stones = load_stones(os.path.join(HERE, "stones", "stones_p%d.json" % i))
    cpath = os.path.join(OUT, "m20b_cand_%s_a%d.json" % (tag, i))
    cand = {o["ci"]: o["cand"] for o in json.load(open(cpath))}
    ortho, ext, _ = ortho_rectify(model, pose, i)
    Z = 6
    HW = 0.32
    for ci, z0c, z1c, c in _course_bands(model, stones, i):
        cc = cand.get(ci, [])
        old = [e for e in (c.get("blocks") or [])]
        rows = []
        v_lo = int(xz_to_px(ext, 0, z1c - 0.02)[1])
        v_hi = int(xz_to_px(ext, 0, z0c + 0.02)[1])
        for x in cc + old:
            u, _ = xz_to_px(ext, x, 0)
            u0 = int(u - HW * PPM)
            u1 = int(u + HW * PPM)
            crop = ortho[max(v_lo, 0):v_hi, u0:u1]
            if crop.size == 0:
                continue
            big0 = cv2.resize(enhance(crop), (crop.shape[1] * Z, crop.shape[0] * Z),
                              interpolation=cv2.INTER_CUBIC)
            big = cv2.copyMakeBorder(big0, 44, 0, 0, 0, cv2.BORDER_CONSTANT, value=(0, 0, 0))
            uc = int((u - u0) * Z)
            cv2.line(big, (uc, 44), (uc, big.shape[0] - 1), (0, 0, 255), 1)
            # 0.1m 刻度(灰短横) 与 0.5m(黄)
            xt = math.ceil((x - HW) / 0.1) * 0.1
            while xt <= x + HW:
                ut, _ = xz_to_px(ext, xt, 0)
                ut = int((ut - u0) * Z)
                col = (0, 255, 255) if abs(xt % 0.5) < 1e-6 else (120, 120, 120)
                cv2.line(big, (ut, big.shape[0] - 12), (ut, big.shape[0] - 1), col, 1)
                if abs(xt % 0.5) < 1e-6:
                    cv2.putText(big, "%+.1f" % xt, (ut + 3, big.shape[0] - 16),
                                0, 0.6, (0, 255, 255), 1)
                xt += 0.1
            tagc = "C" if x in cc else "O"
            cv2.putText(big, "%s x=%+.3f" % (tagc, x), (6, 34), 0, 1.1,
                        (0, 255, 0) if tagc == "C" else (0, 200, 0), 2)
            rows.append(big)
        if not rows:
            continue
        W = max(r.shape[1] for r in rows)
        H = sum(r.shape[0] + 4 for r in rows) + 18
        canvas = np.full((H, W, 3), 15, np.uint8)
        cv2.putText(canvas, "course %02d z0=%.3f  (C=candidate O=old)" % (ci, z0c),
                    (4, 13), 0, 0.5, (255, 255, 255), 1)
        y = 18
        for r in rows:
            canvas[y:y + r.shape[0], :r.shape[1]] = r
            y += r.shape[0] + 4
        cv2.imwrite(os.path.join(OUT, "m20b_cards_%s_a%d_c%02d.png" % (tag, i, ci)),
                    canvas)
    print("cards written")


def main():
    cmd = sys.argv[1]
    if cmd == "prep":
        cmd_prep(sys.argv[2], sys.argv[3])
    elif cmd == "autoedges":
        cmd_autoedges(sys.argv[2], sys.argv[3],
                      sys.argv[4] if len(sys.argv) > 4 else None)
    elif cmd == "zfit":
        cmd_zfit(sys.argv[2], sys.argv[3],
                 sys.argv[4] if len(sys.argv) > 4 else None)
    elif cmd == "layers":
        cmd_layers(sys.argv[2], sys.argv[3])
    elif cmd == "cards":
        cmd_cards(sys.argv[2], sys.argv[3])
    elif cmd == "cand":
        cmd_cand(sys.argv[2], sys.argv[3])
    elif cmd == "strips":
        cmd_strips(sys.argv[2], sys.argv[3],
                   sys.argv[4] if len(sys.argv) > 4 else None)
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
