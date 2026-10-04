# -*- coding: utf-8 -*-
"""Step 1.6 扰动标定: OVERLAY_IOU_MIN / VOID_XC_TOL 的阈值依据(可复现)。

设计(Brumana 2019: 精度须与目标挂钩; Lague 2013: 裸距离阈值无意义, 须配置信区间):
  扰动全部在掩膜空间按**物理量**实施(px/m = 渲染 bbox 宽 / BRIDGE_LEN, 值打印),
  与"生成器参数改动后重渲"几何等价; 随机项(纵向分段扰动)固定种子 SEED。

  扰动模型与生成器闭合法则一致(FACTS C1: Σ跨 + 16 墩 + 2 台 = 150 闭合):
    - 墩宽 ±10%(可接受): 闭合强制跨补偿 → 孔宽均变 ∓, 孔心不动(BRIDGE_LEN 是事实锚);
    - 跨度 ±5%(不可接受): SPAN_DISTINCT 整体缩放 → 孔位随跨序列**累积漂移**(外孔最大);
  两轴的 Δxc 签名由此可分, Δw 单轴不可分(0.0015 vs 0.0017 重叠)——分轴声明, 不硬凑。

  E1 敏感度(指标本身有无判别力): 基线渲染原始剪影 vs 扰动渲染原始剪影(不填孔,
     券洞信息参与) —— 对应简报 G2 版"IoU(跨度)/IoU(对称性)/IoU(矢高比)"曲线。
  E2 守备值(判据在真实比对上的工作点): T3.5 人工掩膜 vs 填实后的扰动渲染
     (构图级口径, FACTS §6.4)。参考掩膜按 §6.2-2 拱洞计入白区 → 券洞轴对 E2
     **结构性失明**(band=rej_blind, 失明被量化成数据而非口头声明);
     E2 阈值只在 E2 可见轴(acc vs rej_vis)之间取。
  V  券洞表响应: void_table 相对基线的 孔数差 / max|Δxc| / max|Δw|。

判定纪律: 若"可接受区间"与"不可接受区间"无可分性, 结论只能是"无判别力"
(写 FACTS.md), 禁止挑一个能过的数当阈值。

复现: cd e30_shikongqiao_video/3d && python3 refs/calibrate_iou.py
"""
import os
import sys

import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))          # .../3d/refs
sys.path.insert(0, os.path.dirname(HERE))                  # .../3d
import register_overlay as R   # noqa: E402
import facts as F              # noqa: E402  单一事实来源(只读)

SEED = 20261004
BRIDGE_LEN = F.BRIDGE_LEN          # 150.0 [官方]
PIER_W = F.PIER_W                  # 2.50 [工作值]
ARCH_RATIO = F.ARCH_RATIO          # 0.50 [图像推导]
N_SPAN = F.N_SPAN                  # 17 [官方]

RENDER = os.path.join(os.path.dirname(HERE), "ortho_side.png")
REF = os.path.join(HERE, "ref_mask.png")


# ── 孔洞组件工具 ──

def hole_label(raw):
    filled = R.solidify(raw)
    holes = filled & ~raw
    return ndimage.label(holes, structure=np.ones((3, 3)))


def big_holes(raw):
    """按 xc 升序的显著券洞 [(label_id, (rows, cols)), ...](已滤望柱缝级碎孔)。
    label_id 从 1 起(ndimage.label 约定, 0=背景), 可直接用于 lab == label_id。"""
    lab, _ = hole_label(raw)
    Wm = raw.shape[1]
    out = []
    for lbl, sl in enumerate(ndimage.find_objects(lab), start=1):
        if sl is None:
            continue
        w = sl[1].stop - sl[1].start
        if float(w) / Wm >= R.VOID_MIN_WNORM:
            xc = (sl[1].start + sl[1].stop - 1) / 2.0 / Wm
            out.append((xc, lbl, sl))
    out.sort()
    return [(i, sl) for _, i, sl in out], lab


# ── 扰动算子(均返回 raw 布尔掩膜副本) ──

def pert_segment_shift(raw, pxm, rng):
    """可接受: 纵向分段扰动, 每段竖向 ±0.5m(17 段, 段界 = 相邻券洞包围盒边中点)。"""
    out = raw.copy()
    holes, _ = big_holes(raw)
    Wm = raw.shape[1]
    edges = [0.0]
    for a, b in zip(holes, holes[1:]):
        edges.append((a[1][1].start + b[1][1].stop) / 2.0)
    edges.append(float(Wm))
    for k in range(len(edges) - 1):
        c0, c1 = int(edges[k]), int(edges[k + 1])
        if c1 <= c0:
            continue
        dy = float(rng.uniform(-0.5, 0.5)) * pxm
        strip = out[:, c0:c1].astype(np.float32)
        out[:, c0:c1] = ndimage.shift(strip, (dy, 0), order=1, mode="nearest") > 0.5
    return out


def _rescale_one_hole(raw, comp_mask, rows, cols, frac):
    """单孔绕孔心水平缩放(frac>1 变宽; <1 变窄)。逐行实施, 只动孔沿, 无环圈伪蚀。"""
    for r in range(rows.start, rows.stop):
        xs = np.where(comp_mask[r, cols.start:cols.stop])[0]
        if len(xs) == 0:
            continue
        l = cols.start + xs.min(); rgt = cols.start + xs.max()
        c = (l + rgt) / 2.0
        half_new = (rgt - l + 1) / 2.0 * frac
        nl = int(round(c - half_new)); nr = int(round(c + half_new))
        if frac > 1.0:                                   # 变宽: 两侧向环圈雕空
            raw[r, max(0, nl):l] = False
            raw[r, rgt + 1:min(raw.shape[1], nr + 1)] = False
        elif frac < 1.0:                                 # 变窄: 两侧孔沿补回环圈
            raw[r, l:max(l, nl)] = True
            raw[r, min(rgt + 1, nr + 1):rgt + 1] = True


def _remap_cols(raw, xs_src):
    """整幅水平重映射: 目标列 j 取源列 xs_src[j](线性插值)。用于跨度累积漂移。"""
    Hm, Wm = raw.shape
    rows = np.broadcast_to(np.arange(Hm, dtype=np.float64)[:, None], (Hm, Wm))
    cols = np.broadcast_to(xs_src[None, :], (Hm, Wm))
    out = ndimage.map_coordinates(raw.astype(np.float32), [rows, cols],
                                  order=1, mode="nearest")
    return out > 0.5


def pert_span(raw, frac):
    """不可接受: 跨度整体 ±5%, **闭合法则下**桥长固定(FACTS C1) → 跨补偿使每孔宽
    ±5%(孔心近似不动)。这是固定 BRIDGE_LEN 管线中"跨度错"的真实表现形态。"""
    out = raw.copy()
    holes, lab = big_holes(raw)
    for i, sl in holes:
        _rescale_one_hole(out, lab == i, sl[0], sl[1], 1.0 + frac)
    return out


def pert_span_uniform(raw, frac):
    """判别力边界证明: 桥整体均匀缩放 ±5%(不闭合, 桥长随动, 画布随桥扩)。
    尺度无关归一化(bbox 宽高独立)在数学上**必然**吸收纯均匀缩放 —— 预期 E1≈1、
    券洞表不变。此行是"L3 对跨度整体缩放轴无判别力"结论的实证, 不是可抓缺陷。"""
    Hm, Wm = raw.shape
    Wn = int(round(Wm * (1.0 + frac)))
    xs_src = np.arange(Wn, dtype=np.float64) / (1.0 + frac)
    rows = np.broadcast_to(np.arange(Hm, dtype=np.float64)[:, None], (Hm, Wn))
    cols = np.broadcast_to(xs_src[None, :], (Hm, Wn))
    out = ndimage.map_coordinates(raw.astype(np.float32), [rows, cols],
                                  order=1, mode="nearest")
    return out > 0.5


def pert_pier(raw, frac, pxm):
    """可接受: 墩宽 ±10%, 闭合法则下跨补偿(FACTS C1) → 每孔宽均变 ∓16·PIER_W·frac/17,
    孔心不动(BRIDGE_LEN 事实锚, 布局保持对称)。"""
    out = raw.copy()
    holes, lab = big_holes(raw)
    dw_m = frac * (N_SPAN - 1) * PIER_W / N_SPAN         # 每孔宽变化(米), 闭合补偿
    for i, sl in holes:
        w_px = sl[1].stop - sl[1].start
        w_m = w_px / pxm
        frac_h = 1.0 - dw_m / w_m
        if not (0.0 < frac_h):
            continue
        _rescale_one_hole(out, lab == i, sl[0], sl[1], frac_h)
    return out


def pert_arch_ratio(raw, ratio_new):
    """不可接受: 矢高比 ARCH_RATIO 0.45↔0.55 —— 券洞竖向缩放(孔底/起拱线不动),
    上界压在净空线(填实轮廓顶+2px)以内, 模拟同构图约束下的重建。"""
    out = raw.copy()
    filled = R.solidify(raw)
    holes, lab = big_holes(raw)
    k = ratio_new / ARCH_RATIO
    for i, sl in holes:
        comp = lab == i
        for c in range(sl[1].start, sl[1].stop):
            ys = np.where(comp[sl[0].start:sl[0].stop, c])[0]
            if len(ys) == 0:
                continue
            t = sl[0].start + ys.min(); b = sl[0].start + ys.max()
            ntop = int(round((b + 1) - (b + 1 - t) * k))
            cap = int(np.argmax(filled[:, c])) + 2        # 净空线(列顶+2px 环圈)
            if k > 1.0:
                ntop = max(ntop, cap)
                if ntop < t:
                    out[ntop:t, c] = False                # 孔顶上抬, 环圈变薄
            else:
                ntop = min(ntop, b)
                if ntop > t:
                    out[t:ntop, c] = True                 # 孔顶下压, 环圈变厚
    return out


def pert_fill_hole(raw, which):
    """不可接受: 缺 1 个券洞。which='main'(最宽孔/主孔) / 'end'(端孔, 最隐蔽)。"""
    out = raw.copy()
    holes, lab = big_holes(raw)
    if which == "end":
        i, sl = holes[0]
    else:
        i, sl = max(holes, key=lambda t: t[1][1].stop - t[1][1].start)
    out[lab == i] = True
    return out


def pert_topcurve(raw, mode):
    """不可接受且 E2 可见(构图级): 驼峰曲线破坏。mode='flatten' 削平 / 'invert' 纵坡反向。
    官方定性口径: "正中一孔最大两侧渐小"+ 驼峰中间最高(FACTS §1/§6.4), 两者均违反。"""
    out = np.zeros_like(raw)
    for c in range(raw.shape[1]):
        ys = np.where(raw[:, c])[0]
        if len(ys) == 0:
            continue
        t, b = ys.min(), ys.max()
        out[t:b + 1, c] = True
    tops = np.array([np.where(out[:, c])[0].min() for c in range(out.shape[1])
                     if out[:, c].any()])
    tf = int(tops.max())                                  # 最低 deck 顶 = 端部水平
    for c in range(raw.shape[1]):
        ys = np.where(out[:, c])[0]
        if len(ys) == 0:
            continue
        t, b = ys.min(), ys.max()
        if mode == "flatten":
            nt = tf
        else:                                             # invert: 关于 tf 镜像
            nt = min(2 * tf - t, b)
        out[nt:b + 1, c] = True
        out[:nt, c] = False
    return out


# ── 度量 ──

def pxm_of(raw):
    filled = R.solidify(raw)
    ys, xs = np.where(filled)
    return (xs.max() - xs.min() + 1) / BRIDGE_LEN


def table_diff(tab_base, tab_pert):
    """券洞表差: (孔数差, max|Δxc|, max|Δw|, 缺失孔最近距)。
    孔数不等时 Δxc/Δw 按前 min(n) 个对齐并单列缺失距(索引错位不冒充位置差)。"""
    dn = len(tab_pert) - len(tab_base)
    n = min(len(tab_base), len(tab_pert))
    dxc = [abs(a[0] - b[0]) for a, b in zip(tab_base[:n], tab_pert[:n])]
    dw = [abs(a[1] - b[1]) for a, b in zip(tab_base[:n], tab_pert[:n])]
    miss = 0.0
    if dn != 0:
        have = [xc for xc, _ in tab_pert] or [0.0]
        gone = [xc for xc, _ in tab_base]
        miss = max(min(abs(g - h) for h in have) for g in gone) if dn < 0 else 0.0
    return dn, (max(dxc) if dxc else 0.0), (max(dw) if dw else 0.0), miss


def main():
    rng = np.random.default_rng(SEED)
    raw = R._load_render(RENDER)
    ref = R._load_ref(REF)
    pxm = pxm_of(raw)
    print("px/m = %.4f (bbox %d px / %.1f m); SEED=%d" %
          (pxm, int(round(pxm * BRIDGE_LEN)), BRIDGE_LEN, SEED))
    base_tab = R.void_table(raw)
    base_e2 = R.iou_silhouette(ref, R.solidify(raw))
    print("基线券洞表 n=%d; 基线 E2(填实 vs ref) = %.4f" % (len(base_tab), base_e2))

    segs = [("seg_shift#%d" % k, pert_segment_shift(raw, pxm, rng), "acc", "xc")
            for k in range(5)]
    # (名称, 掩膜, E2 区间, 券洞表信号轴): vsig ∈ xc/dw/none —— 哪根轴承载该扰动的表信号
    cases = segs + [
        ("pier+10%", pert_pier(raw, +0.10, pxm), "acc", "dw"),
        ("pier-10%", pert_pier(raw, -0.10, pxm), "acc", "dw"),
        ("span+5%(闭合)", pert_span(raw, +0.05), "rej", "dw"),
        ("span-5%(闭合)", pert_span(raw, -0.05), "rej", "dw"),
        ("span+5%(均匀缩放)", pert_span_uniform(raw, +0.05), "blind", "none"),
        ("arch_ratio=0.45", pert_arch_ratio(raw, 0.45), "rej", "none"),
        ("arch_ratio=0.55", pert_arch_ratio(raw, 0.55), "rej", "none"),
        ("fill_main_void", pert_fill_hole(raw, "main"), "rej", "xc"),
        ("fill_end_void", pert_fill_hole(raw, "end"), "rej", "xc"),
        ("flatten_camelback", pert_topcurve(raw, "flatten"), "rej_vis", "xc"),
        ("invert_camelback", pert_topcurve(raw, "invert"), "rej_vis", "xc"),
    ]

    print()
    print("%-22s %8s %8s %5s %8s %8s %8s %9s %4s" %
          ("case", "E1_raw", "E2_solid", "nD", "dXCmax", "dWmax", "missXC", "band", "sig"))
    acc_e2, rejvis_e2 = [], []
    acc_xc, rej_xc = [], []
    acc_dw, rej_dw = [], []
    for name, m, band, vsig in cases:
        e1 = R.iou_silhouette(raw, m)
        e2 = R.iou_silhouette(ref, R.solidify(m))
        dn, dxc, dw, miss = table_diff(base_tab, R.void_table(m))
        print("%-22s %8.4f %8.4f %5d %8.4f %8.4f %8.4f %9s %4s" %
              (name, e1, e2, dn, dxc, dw, miss, band, vsig))
        # 位置轴信号: 孔数不变看 dxc; 孔数变看 miss(索引错位不冒充位置差)
        xsig = dxc if dn == 0 else miss
        if band == "acc":
            acc_e2.append(e2)
            if vsig == "xc":
                acc_xc.append(xsig)
            if vsig == "dw":
                acc_dw.append(dw)
        elif band == "rej_vis":
            rejvis_e2.append(e2)
            if vsig == "xc":
                rej_xc.append(xsig)
        elif band == "rej":
            if vsig == "xc":
                rej_xc.append(xsig)
            if vsig == "dw":
                rej_dw.append(dw)
        # band == "blind": 无判别力证明行, 不进任何区间

    print()
    print("── E2(实体轮廓 vs 人工掩膜, 构图级) ──")
    print("E2 可见-可接受区间: [%.4f, %.4f]   E2 可见-不可接受区间: [%.4f, %.4f]" %
          (min(acc_e2), max(acc_e2), min(rejvis_e2), max(rejvis_e2)))
    if min(acc_e2) > max(rejvis_e2):
        thr = round((min(acc_e2) + max(rejvis_e2)) / 2.0, 2)
        print("OVERLAY_IOU_MIN 可分 -> 建议值 %.2f (两区间中点)" % thr)
    else:
        print("OVERLAY_IOU_MIN 无判别力 -> 不得取值(写 FACTS.md)")
    print("E2 对券洞轴(span/arch/fill)失明: 其 E2≈基线(上表 rej 行), 券洞轴由 void_table 守")
    print()
    print("── V(券洞位置表) ──")
    print("|Δxc|: 可接受 max %.4f   不可接受(位置轴信号) min %.4f" %
          (max(acc_xc) if acc_xc else -1, min(rej_xc) if rej_xc else -1))
    if acc_xc and rej_xc and max(acc_xc) < min(rej_xc):
        print("VOID_XC_TOL 可分 -> 建议值 %.4f (两区间中点)" %
              ((max(acc_xc) + min(rej_xc)) / 2.0))
    else:
        print("VOID_XC_TOL 无判别力")
    print("Δw 不可分声明: 墩宽±10%%(max %.4f) 与 跨度±5%%闭合(max %.4f) 区间重叠,"
          " L3 不以 Δw 硬判, 两轴归 L1 闭合算术 + facts 冻结值 + T8 哈希一致"
          % (max(acc_dw) if acc_dw else -1, max(rej_dw) if rej_dw else -1))


if __name__ == "__main__":
    main()
