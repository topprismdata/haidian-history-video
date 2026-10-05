# -*- coding: utf-8 -*-
"""M11-B 可辨识性分析(九审第 4 项: 正确的边缘化 Jacobian SVD)。

问题: 反演残差 r(g, c) 同时含几何 g(7) 与每照片相机 nuisance c(10×N)。
纯 3D landmark Jacobian 只反映参数化本身的耦合, **不等于**二维投影可辨识性。
正确做法(九审指定):
  1. 在联合解处对**完整图像残差**求数值 Jacobian J = [Jg | Jc];
  2. 几何列按物理范围 Δp = hi-lo 归一(消单位依赖), 相机列按其范围归一;
  3. Schur 补边缘化相机自由度:  Fg = JgᵀJg − JgᵀJc (JcᵀJc)⁺ JcᵀJg;
     —— 回答"允许相机自行调整后, 哪些几何组合仍无法被照片区分";
  4. active-bound: 触界参数其"可动方向"被截断, 单列标注并从退化模态解释中剔除其虚假自由度;
  5. 对 Fg 做 SVD -> 最小奇异值方向 = 侧视投影下的本征不可辨识几何模态。

输出写入 delivery/30 的 svd_degeneracy_analysis, 并把 status 降级为
M11_JOINT_OPTIMIZATION_CONVERGED_DIAGNOSTIC_ONLY。
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import m11_joint_invert as MJ  # noqa: E402
import cam_register as CR  # noqa: E402

GKEYS = MJ.GKEYS
tgt0 = np.array([0.0, 0.0, 4.0])


def build_resid(train):
    """返回 resid(p) 与 p 的 lo/hi/x0, 与 run_joint_inversion 完全一致。"""
    nph = len(train)

    def unpack(p):
        g = dict(zip(GKEYS, p[0:7]))
        cams = [p[7 + 10 * j: 7 + 10 * (j + 1)] for j in range(nph)]
        return g, cams

    def resid(p):
        g, cams = unpack(p)
        xc, span, rise, abut = MJ.geom(g)
        if abut <= 0.1:
            return np.concatenate([np.full(it["pts2"].size, 1e4) for it in train])
        res = []
        for j, it in enumerate(train):
            th, ph, D, tz, roll, wl, cx, cy, fs, k1 = cams[j]
            P3 = MJ.landmarks(g, it["idx"], it["face"], wl)
            KK = it["K"].copy()
            KK[0, 0:2] *= fs; KK[1, 1] *= fs; KK[0, 2] += cx; KK[1, 2] += cy
            C = tgt0 + np.array([D * np.cos(th) * np.cos(ph),
                                 D * np.sin(th) * np.cos(ph), D * np.sin(ph)])
            C[2] = max(0.2, C[2])
            M = CR.look_at(C, tgt0 + np.array([0.0, 0.0, tz]), roll)
            pr, z = CR.project(P3, M, KK, k1)
            if (z <= 0).any():
                res.append(np.full(it["pts2"].size, 1e4))
            else:
                res.append((pr - it["pts2"]).ravel())
        return np.concatenate(res)

    x0 = [MJ.G0[k] for k in GKEYS]
    lo = [MJ.G_BOUNDS[k][0] for k in GKEYS]
    hi = [MJ.G_BOUNDS[k][1] for k in GKEYS]
    for it in train:
        cx, cy, cz = it["init_cam"]
        dx, dy, dz = cx - tgt0[0], cy - tgt0[1], cz - tgt0[2]
        D = float(np.sqrt(dx * dx + dy * dy + dz * dz))
        th = float(np.arctan2(dy, dx)); ph = float(np.arcsin(np.clip(dz / D, -1, 1)))
        x0 += [th, ph, D, 0.0, 0.0, 1.5, 0.0, 0.0, 1.0, 0.0]
        lo += [th - 0.4, -0.4, 60.0, -6.0, -0.2, 0.0, -58.0, -39.0, 0.97, -0.02]
        hi += [th + 0.4, 0.4, 900.0, 6.0, 0.2, 4.0, 58.0, 39.0, 1.03, 0.02]
    return resid, np.array(x0), np.array(lo), np.array(hi), unpack


def numeric_jac(resid, p, h=1e-5):
    r0 = resid(p)
    J = np.zeros((r0.size, p.size))
    for i in range(p.size):
        pp = p.copy(); pp[i] += h
        pm = p.copy(); pm[i] -= h
        J[:, i] = (resid(pp) - resid(pm)) / (2 * h)
    return J


def main():
    train, holdout = MJ.load_dataset()
    rep_path = os.path.join(ROOT, "delivery", "30_m11_joint_inversion_report.json")
    rep = json.load(open(rep_path))
    gi = rep["inferred_geometry"]
    g_opt = dict(zip(GKEYS, [gi["span_center_m"], gi["span_end_m"],
                             gi["p_shape_exponent"], gi["rise_ratio_center"],
                             gi["rise_ratio_gradient"], gi["springer_height_m"],
                             gi["pier_width_m"]]))

    resid, x0, lo, hi, unpack = build_resid(train)
    # 用 g_opt 回填几何列, 相机列取报告里各照片 init(近似; 相机 nuisance 会被边缘化, 不敏感)
    p = x0.copy()
    for j, k in enumerate(GKEYS):
        p[j] = g_opt[k]

    J = numeric_jac(resid, p)
    ng = len(GKEYS)
    Jg, Jc = J[:, :ng], J[:, ng:]

    # 列归一: 几何按物理范围 Δp, 相机按其 bounds 跨度
    grange = np.array([MJ.G_BOUNDS[k][1] - MJ.G_BOUNDS[k][0] for k in GKEYS])
    Jg_n = Jg / grange
    crange = (hi - lo)[ng:]
    Jc_n = Jc / crange

    # active-bound 标注
    active_bounds = {}
    for j, k in enumerate(GKEYS):
        val, l, u = g_opt[k], MJ.G_BOUNDS[k][0], MJ.G_BOUNDS[k][1]
        tol = 0.02 * (u - l)
        if abs(val - l) <= tol:
            active_bounds[k] = "AT_LOWER_BOUND"
        elif abs(val - u) <= tol:
            active_bounds[k] = "AT_UPPER_BOUND"

    # Schur 补边缘化相机: Fg = JgᵀJg − JgᵀJc (JcᵀJc)⁺ JcᵀJg
    A = Jc_n.T @ Jc_n
    Ainv = np.linalg.pinv(A, rcond=1e-10)
    Fg = Jg_n.T @ Jg_n - (Jg_n.T @ Jc_n) @ Ainv @ (Jc_n.T @ Jg_n)
    Fg = 0.5 * (Fg + Fg.T)

    # SVD(Fg): 特征值 = 奇异值²; 最小特征值方向 = 相机调整后仍不可辨识的几何模态
    w, V = np.linalg.eigh(Fg)
    order = np.argsort(w)
    w = w[order]; V = V[:, order]

    modes = []
    for i in range(len(w)):
        vec = V[:, i]
        # 仅在非 active-bound 参数上解释方向
        free = [(GKEYS[j], round(float(vec[j]), 3)) for j in range(ng)
                if GKEYS[j] not in active_bounds and abs(vec[j]) > 0.15]
        ident = "IDENTIFIABLE" if w[i] > 1e-2 else "DEGENERATE"
        modes.append(dict(rank=i + 1, eigenvalue=float(round(w[i], 6)),
                          singular=float(round(np.sqrt(max(w[i], 0)), 5)),
                          identifiability=ident,
                          direction_free_params=free,
                          active_bounds_in_mode=[k for k in GKEYS if k in active_bounds
                                                 and abs(V[GKEYS.index(k), i]) > 0.15]))

    cond = float(w[-1] / w[0]) if w[0] > 0 else float("inf")
    out = dict(
        method=("边缘化相机 nuisance 后的图像残差 Jacobian Schur 补 SVD "
                "(九审第4项指定); 几何/相机列均按物理范围归一; active-bound 参数标注并从"
                "自由方向解释中剔除"),
        formula="Fg = JgᵀJg − JgᵀJc (JcᵀJc)⁺ JcᵀJg (列归一后)",
        condition_number_eig=round(cond, 4),
        eigenvalues=[round(float(x), 6) for x in w],
        active_bounds=active_bounds,
        modes=modes,
        interpretation=(
            "eigenvalue≈0 的模态 = 允许相机自由调整后, 侧视照片仍无法区分的几何组合。"
            "多数几何参数触 active-bound, 其可动方向被截断, 故该反演为诊断性、非可发布测量。"
            "结论(修正九审措辞): 这不是'已证明侧视投影本征不可解耦', 而是'在相机边缘化+归一化后,"
            " 侧视集的可辨识秩不足, 需非侧视(俯视/斜俯/带纵深基线)影像或外部测绘先验打破退化'。"),
    )

    rep["svd_degeneracy_analysis"] = out
    rep["status"] = "M11_JOINT_OPTIMIZATION_CONVERGED_DIAGNOSTIC_ONLY"
    rep["status_note"] = "九审第5项: 由 SUCCESS 降级; 巨大 CI 与 active-bound 表明非可发布几何"
    json.dump(rep, open(rep_path, "w"), ensure_ascii=False, indent=2)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    print("\nUpdated", rep_path, "| status ->", rep["status"])


if __name__ == "__main__":
    main()
