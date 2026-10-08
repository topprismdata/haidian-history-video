# -*- coding: utf-8 -*-
"""洞形透光闸门判读(系统 python3+cv2): 输入正交侧视帧, 输出 ARCHGATE json。

每孔两指标: ①封闭暗孔面积 vs 模型拱腹半圆盘期望(抓未切/矩形槽)
②顶缘单圆(Kasa)拟合 rmse(抓 ogee 错形; 圆弧拱单圆 rmse→0)。
"""
import json
import math
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
AXIS = math.radians(112.0)
LUM_DARK = 0.04      # 线性域: 洞/背景(近黑) vs 亮墙
AREA_TOL = 0.35
ARC_RMSE_MAX = 0.30
MIN_PASS = 15


def main():
    frame = sys.argv[1]
    out_json = sys.argv[2] if len(sys.argv) > 2 else "/tmp/arch_gate.json"
    ppm = 165.0 / 1600.0
    img = cv2.imread(frame, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise SystemExit("frame missing")
    if img.ndim == 3 and img.shape[2] == 4:
        alpha = img[..., 3]
        g = cv2.cvtColor(img[..., :3], cv2.COLOR_BGR2GRAY)
    else:
        g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        alpha = np.full(g.shape, 255, np.uint8)
    # 关键: 拱洞下缘直通水线(画面底边界的亮区外), 不垫亮带则洞与外部暗区连通 → 全部误判 no_opening
    PAD = 40
    g = np.vstack([g, np.full((PAD, g.shape[1]), 255.0, np.float32)])
    alpha = np.vstack([alpha, np.full((PAD, alpha.shape[1]), 255, np.uint8)])
    H, W = g.shape
    bright = ((alpha > 127) & (g > 25)).astype(np.uint8)  # 不透明实体=墙
    ff = bright.copy()
    mask = np.zeros((H + 2, W + 2), np.uint8)
    cv2.floodFill(ff, mask, (0, 0), 1)
    holes_mask = ((ff == 0) & (bright == 0)).astype(np.uint8)
    n, lab, stats, cents = cv2.connectedComponentsWithStats(holes_mask, 8)

    ctrl = json.load(open(os.path.join(HERE, "m20_ctrl", "model_ctrl.json")))
    exp = []
    for i in range(17):
        a = ctrl["arches"][str(i)]
        area_m2 = math.pi * a["a"] * a["a"] / 2.0
        exp.append(dict(i=i, xc=a["xc"], a=a["a"], area_px=area_m2 * ppm * ppm))
    cands = []
    for j in range(1, n):
        x, y, w, h, area = stats[j]
        if area < 250:
            continue
        cands.append(dict(j=j, x=x, y=y, w=w, h=h, area=area, cx=cents[j][0], cy=cents[j][1]))
    cands.sort(key=lambda d: d["cx"])

    rows = []
    used = set()
    for e in sorted(exp, key=lambda e: e["xc"]):
        u_exp = W / 2.0 + e["xc"] * ppm
        best, bd = None, 1e18
        for cd in cands:
            if cd["j"] in used:
                continue
            dd = abs(cd["cx"] - u_exp)
            if dd < bd:
                bd, best = dd, cd
        if best is None or bd > (e["area_px"] ** 0.5 / ppm) * ppm * 0.8:
            rows.append(dict(arch=e["i"], verdict="RED", reason="no_opening(未切/被填)"))
            continue
        used.add(best["j"])
        area_rel = abs(best["area"] - e["area_px"]) / e["area_px"]
        if area_rel > AREA_TOL:
            rows.append(dict(arch=e["i"], verdict="RED", reason="area_mismatch(矩形槽/未切)",
                             area_rel=round(area_rel, 2)))
            continue
        comp = (lab == best["j"]).astype(np.uint8)
        pts = []
        for col in range(best["x"], best["x"] + best["w"]):
            rr = np.nonzero(comp[:, col])[0]
            if len(rr):
                pts.append((col, rr.min()))
        P = np.array([((p[0] - W / 2.0) / ppm, (H / 2.0 - p[1]) / ppm + 3.5) for p in pts])
        A = np.c_[2 * P[:, 0], 2 * P[:, 1], np.ones(len(P))]
        b2 = (P ** 2).sum(1)
        sol, *_ = np.linalg.lstsq(A, b2, rcond=None)
        cx0, cz0 = sol[0], sol[1]
        r0 = math.sqrt(max(1e-9, sol[2] + cx0 * cx0 + cz0 * cz0))
        rmse = float(np.sqrt(np.mean((np.linalg.norm(P - [cx0, cz0], axis=1) - r0) ** 2)))
        ok = rmse <= ARC_RMSE_MAX
        rows.append(dict(arch=e["i"], verdict="PASS" if ok else "RED",
                         reason=None if ok else "shape_not_circle(ogee 类)",
                         circle_center=[round(cx0, 2), round(cz0, 2)], circle_r=round(r0, 2),
                         arc_rmse_m=round(rmse, 3), area_rel=round(area_rel, 2)))
    npass = sum(1 for r in rows if r["verdict"] == "PASS")
    gate = "PASS" if npass == 17 else "RED"
    out = dict(gate=gate, pass_n=npass, arches=rows, ppm=round(ppm, 3),
               thresholds=dict(area_tol=AREA_TOL, arc_rmse_max_m=ARC_RMSE_MAX),
               calibration="两红一绿(2026-10-08): ogee RED(shape)/voidcut-3ac909d2 RED(no_opening|area)/圆弧 PASS")
    print("ARCHGATE " + json.dumps(out, ensure_ascii=False))
    json.dump(out, open(out_json, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
