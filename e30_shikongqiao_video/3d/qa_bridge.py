# -*- coding: utf-8 -*-
"""E30 本体判据 L1(纯数据)。只有 fail 阻塞; skip=未执行不算通过。"""
try:
    from types import SimpleNamespace
except ImportError:
    raise
import math

def _pier_w_at(f, i):
    """第 i 内墩(1-based)宽: facts 声明 PIER_W_INT 表时查表(与 bridge_geom2.pier_w
    消费同一张 facts 数据 —— 规则即数据, 不存在第二套公式可失同步);
    未声明表的 facts(框架合成桥)保持常数 f.PIER_W 的拓扑语义。"""
    tbl = getattr(f, "PIER_W_INT", None)
    if tbl is None:
        return f.PIER_W
    return tbl[i - 1]


def derive(f):
    """由 facts 推导 SPANS/PIER_X。递推规则必须与 bridge_geom2 完全一致:
    桥台宽 = f.BRIDGE_ABUT(T2b 终审定稿维持 1.35, 16内墩口径;
    Task 4 已把 geom 的 BRIDGE_ABUT 回填机制废除断点)。
    六审四刀#2: 内墩宽为逐墩剖面 —— facts.PIER_W_INT(i=1..16, 中央收窄/两端渐厚,
    16 墩之和恒等 (N_SPAN-1)*PIER_W=40.0, 总桥长守恒 BRIDGE_LEN), 与
    bridge_geom2.pier_w 同一数据源; 无表的 facts 退回常数 PIER_W。
    防御(终审 I11): SPAN_DISTINCT 不足 N_SPAN 项时不得 IndexError 崩溃 ——
    按 len(spans) 截断递推, 让 check_body 的 INV_SPANS_LEN 去"报告"这个破坏。"""
    spans = list(f.SPAN_DISTINCT) + list(reversed(f.SPAN_DISTINCT[:-1]))
    pier_x, acc = [], -f.BRIDGE_LEN / 2.0
    for i in range(min(f.N_SPAN, len(spans)) + 1):
        w = f.BRIDGE_ABUT if i in (0, f.N_SPAN) else _pier_w_at(f, i)
        pier_x.append(acc + w / 2.0)
        acc += w
        if i < f.N_SPAN and i < len(spans):
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

def _is_num(v):
    """实数(排除 bool —— bool 是 int 的子类, 必须显式排除; 与 bridge3d.schema.is_number 同口径)。"""
    return isinstance(v, (int, float)) and not isinstance(v, bool)


# check_body 逐项要求为数值的事实字段(终审 I11 前置校验; N_SPAN 另要求整型)
_NUMERIC_FIELDS = ("BRIDGE_LEN", "DECK_Z_TOP", "DECK_Z_END", "DECK_UP_W",
                   "DECK_DOWN_W", "SPRINGER", "ARCH_RATIO", "RING_T",
                   "PIER_W", "BRIDGE_ABUT")


def check_body(f):
    """三层: INV(拓扑不变量) / MET(度量, 阈值须有依据) / IMP(实现完整性)。
    判据契约(终审 I11): 损坏 facts 必须"报告"(fail/skip)而非崩溃 —— 
    与框架 run_l1 同行为; 真实破坏不得从 fail 降级为 skip。"""
    import assumptions as A
    out = []
    def add(lvl, name, msg):
        out.append((lvl, name, msg))
    # ── 前置类型/形状校验: 不足以下推时报 IMP_TYPES fail 并返回(不抛异常) ──
    if not isinstance(getattr(f, "N_SPAN", None), int) or isinstance(f.N_SPAN, bool):
        add("fail", "IMP_TYPES", "N_SPAN 须为 int, 实为 %r" % (getattr(f, "N_SPAN", None),))
    else:
        bad = [(n, type(getattr(f, n, None)).__name__) for n in _NUMERIC_FIELDS
               if not _is_num(getattr(f, n, None))]
        sd = getattr(f, "SPAN_DISTINCT", None)
        if not isinstance(sd, (list, tuple)):
            bad.append(("SPAN_DISTINCT", type(sd).__name__))
        elif any(not _is_num(x) for x in sd):
            bad.append(("SPAN_DISTINCT", "含非数值元素"))
        if bad:
            add("fail", "IMP_TYPES", "facts 字段类型非法, 判据无法执行: %s" % bad)
    if any(x[1] == "IMP_TYPES" for x in out):
        return out
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
    # 口径 = T2b 终审(2026-10-04): 内墩数 = N_SPAN - 1(17 孔之间是 16 个墩;
    # n-1 拓扑 + 卢沟桥10墩11孔/宝带桥53孔52墩文献佐证 + bridge_geom2 闭合断言同口径)。
    # 初版误按 15 墩硬编码产生 -2.50m 假闭合差(及"桥台 2.60"凑数解, 已作废);
    # 改用 (N_SPAN-1) 使判据随 facts 变化。
    # 阈值(终审 I12): 消费 facts.CLOSURE_TOL(登记于 SOURCES, 工作值); 缺失 → skip(未执行不算通过)。
    # 六审四刀#2: 内墩宽为逐墩剖面(PIER_W_INT), 闭合必须按 derive 同一规则逐墩求和;
    # 表缺失(合成 facts)→ 常数 PIER_W 拓扑; 表形状非法 → IMP_PIER_TABLE fail 并按常数降级
    # (判据报告而非崩溃, 与 I11 同契约)。
    tbl = getattr(f, "PIER_W_INT", None)
    if tbl is not None and (not isinstance(tbl, (list, tuple))
                            or len(tbl) != f.N_SPAN - 1
                            or any(not _is_num(x) or x <= 0 for x in tbl)):
        add("fail", "IMP_PIER_TABLE",
            "PIER_W_INT 须为 N_SPAN-1=%d 个正数的表, 实为 %r" % (f.N_SPAN - 1, tbl))
        tbl = None
    total = sum(d.SPANS) + sum(
        (tbl[i - 1] if tbl is not None else f.PIER_W)
        for i in range(1, f.N_SPAN)) + 2 * f.BRIDGE_ABUT
    closure_tol = getattr(f, "CLOSURE_TOL", None)
    if closure_tol is None:
        add("skip", "MET_CLOSURE", "facts 未声明 CLOSURE_TOL, 未执行(阈值必须有依据且进台账)")
    elif not _is_num(closure_tol) or closure_tol <= 0:
        add("fail", "IMP_TOLERANCE", "CLOSURE_TOL=%r 须为正数(坏容差会让闭合判据形同虚设)" % (closure_tol,))
    elif abs(total - f.BRIDGE_LEN) > closure_tol:
        add("fail", "MET_CLOSURE",
            "几何闭合差 %+.2fm: 跨和+墩+台=%.1f != 桥长%.1f "
            "(n-1 拓扑: 17 孔之间是 16 个墩; 蓝本文献佐证 卢沟桥10墩11孔/宝带桥53孔52墩。"
            " 基线 107.3+16×2.50+2×1.35=150.0 精确闭合, 若此判据触发说明 facts 偏离基线)"
            % (total - f.BRIDGE_LEN, total, f.BRIDGE_LEN))
    # ── MET 券族: 圆拟合残差(G2: f/l 只是必要条件) ──
    # 防御: N_SPAN 与 SPAN_DISTINCT 展开长度不一致时(INV_N_SPAN/INV_SPANS_LEN 已报 fail),
    # 本循环必须仍能返回完整判据报告而非 IndexError 崩溃 —— 判据必须"报告", 不能"崩溃"。
    # 全一致(N_SPAN=17)时 n_arch=17, 与逐孔遍历完全等价。
    n_arch = min(len(d.SPANS), len(d.PIER_X) - 1)
    for i in range(n_arch):
        xc = (d.PIER_X[i] + d.PIER_X[i + 1]) / 2.0
        a = d.SPANS[i] / 2.0
        # [M14] 旧 MET_ARCH_FAMILY 是恒真闸门: 它采样"合成半圆点集"再拟合圆,
        # 残差恒 0, 与真实拱线无关。M12 后拱为逐孔两圆心 ogee, 单圆前提作废。
        # 改测真实剖面 f.arch_z 的结构性不变量: 肩点归零/对称/单峰/冠高一致。
        b_i = f.rise_ratio(i) * d.SPANS[i]
        sp_i = d.deck_z(xc) - f.SPANDREL - b_i
        zl = f.arch_z(xc - a, xc, sp_i, a, b_i)
        zr = f.arch_z(xc + a, xc, sp_i, a, b_i)
        if abs(zl - sp_i) > 1e-3 or abs(zr - sp_i) > 1e-3:
            add("fail", "MET_ARCH_FAMILY", "孔%d 肩点不归位 z(±a)=(%.3f,%.3f) spz=%.3f"
                % (i + 1, zl, zr, sp_i))
        ts = [a * k / 40.0 for k in range(1, 40)]
        sym = max(abs(f.arch_z(xc + t, xc, sp_i, a, b_i)
                      - f.arch_z(xc - t, xc, sp_i, a, b_i)) for t in ts)
        if sym > 1e-6:
            add("fail", "MET_ARCH_FAMILY", "孔%d 拱线不对称 maxΔz=%.2e" % (i + 1, sym))
        zs = [f.arch_z(xc - a + t, xc, sp_i, a, b_i) for t in
              [2 * a * k / 40.0 for k in range(41)]]
        half = 20
        if any(zs[k + 1] - zs[k] < -1e-9 for k in range(half)) or \
           any(zs[k + 1] - zs[k] > 1e-9 for k in range(half, 40)):
            add("fail", "MET_ARCH_FAMILY", "孔%d 拱线非左升右降(多峰?)" % (i + 1,))
        crown_z = f.arch_z(xc, xc, sp_i, a, b_i)
        if abs(crown_z - (sp_i + b_i)) > 1e-3:
            add("fail", "MET_ARCH_FAMILY", "孔%d 冠高%.3f≠spz+矢%.3f" % (i + 1, crown_z, sp_i + b_i))
        # f/l 设计意图(终审 I12): 消费 facts.ARCH_RATIO_TARGET±ARCH_RATIO_TOL(原 0.50±0.05 硬写)。
        # 缺任一 → skip(未执行不算通过); 与框架 met_arch_ratio 同语义。
        ratio_target = getattr(f, "ARCH_RATIO_TARGET", None)
        ratio_tol = getattr(f, "ARCH_RATIO_TOL", None)
        if ratio_target is None or ratio_tol is None:
            add("skip", "MET_ARCH_RATIO", "facts 未声明 ARCH_RATIO_TARGET/ARCH_RATIO_TOL, 未执行")
        elif not (_is_num(ratio_target) and _is_num(ratio_tol)) or ratio_tol <= 0:
            add("fail", "IMP_TOLERANCE",
                "ARCH_RATIO_TARGET/TOL 非法: %r/%r(容差须为正数)" % (ratio_target, ratio_tol))
        elif abs(f.rise_ratio((f.N_SPAN - 1) // 2) - ratio_target) > ratio_tol:
            # [M14] 旧版比对常量 f.ARCH_RATIO(0.50, M12 前口径); 现比对剖面中心值
            add("fail", "MET_ARCH_RATIO", "中央矢跨=%.3f 偏离设计意图 %.2f±%.2f"
                % (f.rise_ratio((f.N_SPAN - 1) // 2), ratio_target, ratio_tol))
        # MET 结构自洽(G2 修订; M14 随 M12 语义: 冠=桥面-拱肩, 起拱=冠-矢, 逐孔)
        crown_i = d.deck_z(xc) - f.SPANDREL
        if crown_i + f.RING_T > d.deck_z(xc) + 1e-9:
            add("fail", "MET_RING_FIT", "孔%d 拱背%.2f 高于桥面%.2f(券圈穿出桥面)" % (i + 1, crown_i + f.RING_T, d.deck_z(xc)))
        if sp_i >= d.deck_z(xc):
            add("fail", "MET_SPRINGER", "孔%d 起拱线高于桥面" % (i + 1))
    if not (0 < f.DECK_UP_W < f.DECK_DOWN_W):
        add("fail", "MET_TAPER", "顶宽须小于底宽(收分)")
    if f.DECK_Z_TOP <= f.DECK_Z_END:
        add("fail", "MET_DECK_DIR", "桥面必须中央最高(历史事故回归)")
    if f.PIER_W <= 0.2 or f.BRIDGE_ABUT <= 0:
        add("fail", "IMP_DIM", "墩/台尺寸非法")
    return out
