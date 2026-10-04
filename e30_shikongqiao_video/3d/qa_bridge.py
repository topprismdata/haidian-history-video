# -*- coding: utf-8 -*-
"""E30 本体判据 L1(纯数据)。只有 fail 阻塞; skip=未执行不算通过。"""
try:
    from types import SimpleNamespace
except ImportError:
    raise
import math

def derive(f):
    """由 facts 推导 SPANS/PIER_X。递推规则必须与 bridge_geom2 完全一致:
    墩台宽 = f.BRIDGE_ABUT(Task 4 已把 geom 的 BRIDGE_ABUT 回填机制废除断点;
    当前值 1.35 为 T2b 闭合归因前的现值, 定稿后由 facts 单点更新)。"""
    spans = list(f.SPAN_DISTINCT) + list(reversed(f.SPAN_DISTINCT[:-1]))
    pier_x, acc = [], -f.BRIDGE_LEN / 2.0
    for i in range(f.N_SPAN + 1):
        w = f.BRIDGE_ABUT if i in (0, f.N_SPAN) else f.PIER_W
        pier_x.append(acc + w / 2.0)
        acc += w
        if i < f.N_SPAN:
            acc += spans[i]
    def deck_z(x):
        half = f.BRIDGE_LEN / 2.0
        ax = min(abs(x), half)
        k = (f.DECK_Z_TOP - f.DECK_Z_END) / (half * half)
        return f.DECK_Z_TOP - k * ax * ax
    return SimpleNamespace(SPANS=spans, PIER_X=pier_x, deck_z=deck_z)

def circle_fit_residual(pts):
    """C2/G2 核心增补: 圆拟合残差(证明'是圆', 而非只测 f/l 标量)。
    pts: [(x,z)] 拱腹采样点。返回 max| |P-C| - R | / R。代数拟合(Kasa)即可。"""
    import numpy as np
    A = np.array([[x, z, 1.0] for x, z in pts])
    b = np.array([x * x + z * z for x, z in pts])
    sol, *_ = np.linalg.lstsq(A, b, rcond=None)
    cx, cz = sol[0] / 2.0, sol[1] / 2.0
    r = math.sqrt(sol[2] + cx * cx + cz * cz)
    err = max(abs(math.hypot(x - cx, z - cz) - r) for x, z in pts)
    return err / r, (cx, cz, r)

def check_body(f):
    """三层: INV(拓扑不变量) / MET(度量, 阈值须有依据) / IMP(实现完整性)。"""
    import assumptions as A
    out = []
    def add(lvl, name, msg):
        out.append((lvl, name, msg))
    d = derive(f)
    # ── INV 拓扑不变量 ──
    if f.N_SPAN != 17:
        add("fail", "INV_N_SPAN", "孔数 %d != 17" % f.N_SPAN)
    if len(d.SPANS) != 17:
        add("fail", "INV_SPANS_LEN", "SPANS 长度 %d" % len(d.SPANS))
    else:
        if any(d.SPANS[i] != d.SPANS[16 - i] for i in range(8)):
            add("fail", "INV_SPANS_SYM", "跨序不对称")
        if any(d.SPANS[i] < d.SPANS[i - 1] - 1e-9 for i in range(1, 9)):
            add("fail", "INV_SPANS_MONO", "左半跨序非单调不减")
        if any(d.SPANS[i] < d.SPANS[i + 1] - 1e-9 for i in range(8, 16)):
            add("fail", "INV_SPANS_MONO", "右半跨序非单调增")
    # ── MET 几何闭合(G2 增补: 抓'对称但整体尺度错') ──
    # 口径注意: 本判据按 15 内墩计数(派发口径, -2.50m 即按此计);
    # derive 的 PIER_X 布局为 16 内墩(2 台+16 墩=18 支承)。两种口径的取舍归 T2b,
    # 本层禁止改计数或调阈值让 fail 变绿。
    total = sum(d.SPANS) + 15 * f.PIER_W + 2 * f.BRIDGE_ABUT
    if abs(total - f.BRIDGE_LEN) > 0.5:
        add("fail", "MET_CLOSURE", "几何闭合差 %.2fm: 跨和+墩+台=%.1f != 桥长%.1f (2026-10-04 实测 -2.50m: 桥台1.35偏小, 闭合推导应为2.60m, M0须归因)" % (total - f.BRIDGE_LEN, total, f.BRIDGE_LEN))
    # ── MET 券族: 圆拟合残差(G2: f/l 只是必要条件) ──
    # 防御: N_SPAN 与 SPAN_DISTINCT 展开长度不一致时(INV_N_SPAN/INV_SPANS_LEN 已报 fail),
    # 本循环必须仍能返回完整判据报告而非 IndexError 崩溃 —— 判据必须"报告", 不能"崩溃"。
    # 全一致(N_SPAN=17)时 n_arch=17, 与逐孔遍历完全等价。
    n_arch = min(len(d.SPANS), len(d.PIER_X) - 1)
    for i in range(n_arch):
        xc = (d.PIER_X[i] + d.PIER_X[i + 1]) / 2.0
        a = d.SPANS[i] / 2.0
        pts = [(xc - a * math.cos(math.pi * k / 20.0),
                f.SPRINGER + a * math.sin(math.pi * k / 20.0)) for k in range(21)]
        rtol, _ = circle_fit_residual(pts)
        if rtol > A.CIRCLE_FIT_RTOL:
            add("fail", "MET_ARCH_FAMILY", "孔%d 圆拟合残差/R=%.4f 超限(非圆弧?)" % (i + 1, rtol))
        # f/l 只留宽幅 sanity(设计意图半圆)
        if abs(f.ARCH_RATIO - 0.50) > 0.05:
            add("fail", "MET_ARCH_RATIO", "f/l=%.3f 偏离半圆设计意图" % f.ARCH_RATIO)
        # MET 结构自洽(G2 修订): 拱背=拱腹+RING_T 须低于桥面, 替代无据的0.30
        crown_i = f.SPRINGER + a
        if crown_i + f.RING_T > d.deck_z(xc) + 1e-9:
            add("fail", "MET_RING_FIT", "孔%d 拱背%.2f 高于桥面%.2f(券圈穿出桥面)" % (i + 1, crown_i + f.RING_T, d.deck_z(xc)))
        if f.SPRINGER >= d.deck_z(xc):
            add("fail", "MET_SPRINGER", "孔%d 起拱线高于桥面" % (i + 1))
    if not (0 < f.DECK_UP_W < f.DECK_DOWN_W):
        add("fail", "MET_TAPER", "顶宽须小于底宽(收分)")
    if f.DECK_Z_TOP <= f.DECK_Z_END:
        add("fail", "MET_DECK_DIR", "桥面必须中央最高(历史事故回归)")
    if f.PIER_W <= 0.2 or f.BRIDGE_ABUT <= 0:
        add("fail", "IMP_DIM", "墩/台尺寸非法")
    return out
