# -*- coding: utf-8 -*-
"""E30 L1 本体判据测试: 正例 + 逐条判据的"故意破坏"负控制。

项目铁律: 每条判据必须先有"故意破坏"用例且破坏被抓, 否则判据无效。
判据×破坏矩阵的完整实测记录见 .superpowers/sdd/e30-briefs/task-task-3-report.md。

已知基线状态: MET_CLOSURE 按派发口径(15 内墩)恒红 -2.50m —— 这是判据在正确工作,
暴露真矛盾, T2b 归因中; 禁止调阈值/改计数迁就。相关断言已显式适配而非回避。
"""
import os, sys, importlib, math, types
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "3d"))
import facts, assumptions, qa_bridge

import pytest


def _mutate(**kw):
    m = types.SimpleNamespace(**{k: getattr(facts, k) for k in dir(facts) if not k.startswith("_")})
    for k, v in kw.items():
        setattr(m, k, v)
    return m


def _fails_on(name, **kw):
    r = qa_bridge.check_body(_mutate(**kw))
    codes = {x[1] for x in r if x[0] == "fail"}
    assert name in codes, "破坏未被抓(%s): %s" % (name, codes)


def _fail_codes(**kw):
    return {x[1] for x in qa_bridge.check_body(_mutate(**kw)) if x[0] == "fail"}


def test_baseline_green():
    """T2b 归因定稿(预期 BRIDGE_ABUT=2.60)后本测试转绿; strict=True 保证届时
    必须显式摘掉本标记, 不得静默 XPASS —— 那是"判据恒真却全绿"的形态。"""
    r = qa_bridge.check_body(facts)
    fails = [x for x in r if x[0] == "fail"]
    assert not fails, "基线不应 fail: %s" % fails


# 2026-10-04: 原先的 strict xfail 已摘除。T3 复核发现 -2.50m 闭合差是计划稿的
# 算术错误(误按 15 墩); 17 孔之间是 16 墩, 107.3+16×2.5+2×1.35=150.0 精确闭合。
# xfail 的存在本身就是危险信号: 它让"基线红"变成可接受状态。基线必须真绿。


def test_circle_fit_synthetic():
    # 真圆: 残差≈0 (实测 0.000000)
    pts = [(math.cos(t), math.sin(t)) for t in [math.pi*k/40 for k in range(41)]]
    rtol, _ = qa_bridge.circle_fit_residual(pts)
    assert rtol < 1e-3
    # 三心拱反例(G2): 同 f/l=0.5 但非圆, 残差必须大。
    # 实测: 尖顶三心拱残差 0.0626 > 0.05, 椭圆(1-0.5x^2)残差 0.0025 < 0.01(须放行)。
    def _three_center(n=41, pointiness=0.30):
        pts = []
        for k in range(n):
            t = -1.0 + 2.0 * k / (n - 1)
            z = 0.5 * math.sqrt(max(0.0, 1.0 - t * t)) * (1.0 + pointiness * abs(t))
            pts.append((t, z))
        return pts
    rtol3, _ = qa_bridge.circle_fit_residual(_three_center())
    assert rtol3 > 0.05, "尖顶三心拱残差 %.4f 未超 0.05, 判据抓不住非圆券" % rtol3
    # 椭圆必须被放行(它在圆拟合容差内, 不得误杀)
    rtol_e, _ = qa_bridge.circle_fit_residual(
        [(x, math.sqrt(max(0.0, 1 - x * x * 0.5))) for x in [-1 + 2 * k / 40 for k in range(41)]])
    assert rtol_e < 0.01, "椭圆残差 %.4f 过大, 判据过严" % rtol_e

# ── 边界负控(G2 A类: 符号方向证明) ──
def test_boundary_mono():
    r = qa_bridge.check_body(_mutate(SPAN_DISTINCT=[4.5,4.9,5.4,5.9,6.4,6.9,7.4,7.4,8.0]))
    assert not [x for x in r if x[0] == "fail" and x[1].startswith("INV_SPANS_MONO")], "相等应放行(非严格单调)"
    _fails_on("INV_SPANS_MONO", SPAN_DISTINCT=[4.5,4.9,5.4,5.95,5.9,6.4,6.9,7.4,8.0])

# ── 单点破坏(G2 B类: 一孔坏必须全局红) ──
def test_single_arch_break():
    # 实测修订: SPAN_DISTINCT 的展开规则(D + reversed(D[:-1]))恒构造回文(见
    # test_spans_expansion_is_palindrome), 故单孔变异不可能触发 INV_SPANS_SYM ——
    # 简报原断言(SYM)在 L1 不可达。单孔坏的全局红由 MET_CLOSURE 抓(跨和被破坏)。
    # SYM 检测器本身的负控在 test_inv_spans_sym_detector(检测器级)完成。
    sd = list(facts.SPAN_DISTINCT); sd[3] = sd[3] + 0.4   # 只改左第4孔
    codes = _fail_codes(SPAN_DISTINCT=sd)
    assert codes, "一孔坏必须全局红, 实测无任何 fail"
    assert "MET_CLOSURE" in codes, "单孔坏应破坏闭合被抓: %s" % codes

# ── 对称但尺度错(G2 C类: 关系判据抓不住, 闭合判据必须抓) ──
def test_symmetric_scale_break():
    sd = [x * 1.05 for x in facts.SPAN_DISTINCT]
    _fails_on("MET_CLOSURE", SPAN_DISTINCT=sd)

# ── 全局Z平移(G2 G类: 相对判据全过, datum判据须抓) ──
# 数值校准(实测): 基线 MET_RING_FIT 最小余量为孔1/17 的 +0.173m; deck_z 是
# TOP/END 的线性族, 整体下移 Δ 等量吃掉余量: Δ=0.1m 仍绿(余 0.073m),
# Δ=0.5m 即红(余 -0.327m)。故破坏量取 1.0m, 远离判定边界。
def test_global_z_shift_break():
    _fails_on("MET_RING_FIT",
              DECK_Z_TOP=facts.DECK_Z_TOP - 1.0, DECK_Z_END=facts.DECK_Z_END - 1.0)


# ── 边界: 平移量恰在容差内必须放行(证明判据不是恒真的) ──
def test_global_z_shift_within_tolerance_passes():
    r = qa_bridge.check_body(_mutate(DECK_Z_TOP=facts.DECK_Z_TOP - 0.1,
                                     DECK_Z_END=facts.DECK_Z_END - 0.1))
    assert not [x for x in r if x[0] == "fail" and x[1] == "MET_RING_FIT"], \
        "0.1m 平移(小于最小余量0.173m)不应触发 RING_FIT"

# ── 特异性(G2 J类: 无关破坏不应触发无关判据) ──
def test_specificity():
    # 闭合差已闭环(16 墩口径), 无需再排除任何判据: 改非本体字段必须全静默。
    r = qa_bridge.check_body(_mutate(PIER_MAIN_W=3.3))   # 改非本体字段
    fails = {x[1] for x in r if x[0] == "fail"}
    assert not fails, "无关字段改动不应触发本体判据: %s" % fails


# ══════════ 以下为本次补齐的负控制(每条先单独实测"改坏→被抓", 见报告矩阵) ══════════

# ── INV_N_SPAN: 孔数破坏必须被抓 ──
def test_inv_n_span_break():
    _fails_on("INV_N_SPAN", N_SPAN=15)


# ── INV_SPANS_LEN: 展开长度破坏必须被抓 ──
# 注: 取变长方向(D 10 个)。变短方向(D<9 个)会让 derive 的递推先 IndexError ——
# verbatim 递推按 N_SPAN=17 取 spans[i], 这是 facts 双字段损坏下的已知崩溃路径,
# 记录于报告; 判据对可表达的方向必须"报告"而非"崩溃"。
def test_inv_spans_len_break():
    _fails_on("INV_SPANS_LEN", SPAN_DISTINCT=facts.SPAN_DISTINCT + [9.0])


# ── INV_SPANS_SYM 的结构性说明: 展开规则恒构造回文 ──
def test_spans_expansion_is_palindrome():
    # 任意扰动下展开恒对称 ⇒ L1 经由 SPAN_DISTINCT 不可达 SYM。
    # SYM 真正防守的是"展开规则被改坏"(见 test_inv_spans_sym_detector)与 L2 实测跨序。
    for pert in (0.4, -0.3, 0.15):
        sd = [v + pert * (i % 3 == 1) for i, v in enumerate(facts.SPAN_DISTINCT)]
        d = qa_bridge.derive(_mutate(SPAN_DISTINCT=sd))
        assert len(d.SPANS) == 17
        assert all(d.SPANS[i] == d.SPANS[16 - i] for i in range(8)), \
            "展开规则被改动? 扰动 %+.2f 下不再回文" % pert


# ── INV_SPANS_SYM 检测器级负控: 非对称跨序必须被抓(证明非恒真) ──
def test_inv_spans_sym_detector(monkeypatch):
    real_derive = qa_bridge.derive

    def skewed_derive(f):
        d = real_derive(f)
        d.SPANS[3] = d.SPANS[3] + 0.4   # 模拟展开规则改坏/L2 实测非对称跨序
        return d

    monkeypatch.setattr(qa_bridge, "derive", skewed_derive)
    codes = {x[1] for x in qa_bridge.check_body(facts) if x[0] == "fail"}
    assert "INV_SPANS_SYM" in codes, "检测器级非对称未被 SYM 抓到: %s" % codes


# ── INV_SPANS_MONO 右半: 下行段回升必须被抓 ──
def test_inv_spans_mono_right_break():
    _fails_on("INV_SPANS_MONO", SPAN_DISTINCT=[4.5, 4.9, 5.4, 5.9, 6.4, 6.9, 8.0, 7.4, 8.5])


# ── MET_TAPER: 收分反转/退化必须被抓 ──
def test_met_taper_break():
    _fails_on("MET_TAPER", DECK_UP_W=16.0)   # 顶宽 > 底宽: 收分反转
    _fails_on("MET_TAPER", DECK_UP_W=0.0)    # 顶宽非正: 退化


# ── MET_DECK_DIR: 桥面中央必须最高(历史事故回归) ──
def test_met_deck_dir_break():
    _fails_on("MET_DECK_DIR", DECK_Z_TOP=4.0, DECK_Z_END=6.0)


# ── MET_ARCH_RATIO: f/l 偏离半圆设计意图必须被抓 ──
def test_met_arch_ratio_break():
    _fails_on("MET_ARCH_RATIO", ARCH_RATIO=0.65)


# ── MET_SPRINGER: 起拱线高于桥面必须被抓 ──
def test_met_springer_break():
    _fails_on("MET_SPRINGER", SPRINGER=8.0)   # 高于中央桥面 7.75


# ── IMP_DIM: 墩/台尺寸非法必须被抓 ──
def test_imp_dim_break():
    _fails_on("IMP_DIM", PIER_W=0.1)
    _fails_on("IMP_DIM", BRIDGE_ABUT=0)


# ── MET_CLOSURE 真负控: 闭合推导值必须让它变绿(证明不是恒真判据) ──
def test_met_closure_baseline_is_exactly_closed():
    """基线在 16 墩口径下精确闭合到 0.0000m —— MET_CLOSURE 必须恒静默。
    这条锁住"基线绿"这个事实本身: 若将来有人改 facts 使基线红, 这里立刻报。"""
    assert not _fail_codes(), "基线应零 fail, 实测: %s" % _fail_codes()


def test_met_closure_catches_real_gap():
    """真负控: 打破闭合必须被抓。基线 150.0 精确闭合, 桥台改 1.35->2.60 会多出 2.5m。"""
    assert "MET_CLOSURE" in _fail_codes(BRIDGE_ABUT=2.60), \
        "桥台改 2.60 会造成 +2.5m 闭合差, 判据必须抓到"
    assert "MET_CLOSURE" in _fail_codes(PIER_W=2.40), \
        "墩宽改 2.40 会造成 -2.4m 闭合差, 判据必须抓到"
