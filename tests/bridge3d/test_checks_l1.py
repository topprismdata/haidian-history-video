# -*- coding: utf-8 -*-
"""bridge3d.checks_l1 测试: 三层判据的正例 + 逐条"故意破坏"负控制 + skip 语义。

命名即验收:
  test_baseline_green_n5 / test_baseline_green_n23 —— 判据不依赖任何项目数值,
  5 孔与 23 孔(以及 E30 之外的一切 n)同一套判据都应基线全绿。
"""
import sys
from os.path import dirname, join

import pytest

sys.path.insert(0, dirname(__file__))

import bridge3d                              # noqa: E402
from bridge3d import checks_l1 as C          # noqa: E402
from bridge3d.negative_control import (       # noqa: E402
    mutate, dropped, fail_codes, skip_codes,
    assert_criterion_rejects, assert_criterion_accepts, assert_skip_not_fail)
from bridge3d.schema import summarize        # noqa: E402
from facts_synth import make_5, make_23      # noqa: E402

MAKERS = [make_5, make_23]
IDS = ["n5", "n23"]


# ══════════ 基线: 换孔数必须照常全绿(框架立身之本) ══════════

@pytest.mark.parametrize("make", MAKERS, ids=IDS)
def test_baseline_green(make):
    r = bridge3d.audit(make())
    assert not fail_codes(r), summarize(r)
    assert not skip_codes(r), "完整事实基线不应有 skip: %r" % skip_codes(r)


def test_baseline_green_n5():
    assert not fail_codes(bridge3d.audit(make_5()))


def test_baseline_green_n23():
    assert not fail_codes(bridge3d.audit(make_23()))


def test_run_l1_matches_audit_l1_part():
    assert fail_codes(bridge3d.run_l1(make_5())) == []


# ══════════ INV 拓扑: 逐条破坏 ══════════

@pytest.mark.parametrize("kw", [
    dict(N_SPAN=0), dict(N_SPAN=-5), dict(N_SPAN=5.0), dict(N_SPAN=True),
])
def test_inv_n_span_break(kw):
    assert_criterion_rejects(C.inv_n_span, mutate(make_5(), **kw), "INV_N_SPAN")


@pytest.mark.parametrize("sd", [
    [3.0, 4.0, 5.0, 4.0],                     # 展开 4 跨 != 5
    [3.0, 4.0, 5.0, 4.0, 3.0, 3.0],           # 展开 6 跨 != 5
])
def test_inv_spans_len_break(sd):
    assert_criterion_rejects(C.inv_spans_len, mutate(make_5(), SPAN_DISTINCT=sd),
                             "INV_SPANS_LEN")


def test_inv_spans_pos_break():
    for sd in ([0.0, 4.0, 5.0], [3.0, -4.0, 5.0]):
        assert_criterion_rejects(C.inv_spans_positive, mutate(make_5(), SPAN_DISTINCT=sd),
                                 "INV_SPANS_POS")


def test_inv_supports_len_break_detector_level():
    """支承数护栏: 递推规则被改坏(少产出一个支承)必须红(检测器级负控)。"""
    from bridge3d.negative_control import patched_derive
    f = make_5()
    with patched_derive(pier_x=lambda orig: (lambda ff: orig(ff)[:-1])):
        r = C.inv_supports_len(f)
    assert "INV_SUPPORTS_LEN" in fail_codes(r)


# ══════════ MET 度量: 逐条破坏 ══════════

@pytest.mark.parametrize("kw", [
    dict(BRIDGE_ABUT=2.0),                    # 桥台 +0.65 → 闭合差 +1.3
    dict(PIER_W=2.4),                         # 墩宽 +1.2 → 闭合差 +4.8
    dict(SPAN_DISTINCT=[3.15, 4.0, 5.0]),     # 单孔坏 → 对称但闭合差
    dict(SPAN_DISTINCT=[3.3, 4.2, 5.4]),      # 对称缩放 1.1 → 闭合差
])
def test_met_closure_break(kw):
    assert_criterion_rejects(C.met_closure, mutate(make_5(), **kw), "MET_CLOSURE")


def test_met_closure_within_tolerance_passes():
    """容差内微扰必须放行 —— 证明判据不是恒红。"""
    assert_criterion_accepts(C.met_closure,
                             mutate(make_5(), BRIDGE_LEN=make_5().BRIDGE_LEN + 0.005),
                             "MET_CLOSURE")


def test_met_closure_without_tolerance_is_skip():
    """阈值必须有依据: 无 facts.CLOSURE_TOL 且无显式参数 → skip, 绝不 fail。"""
    r = C.met_closure(dropped(make_5(), "CLOSURE_TOL"))
    assert_skip_not_fail(r, "MET_CLOSURE 无容差")
    assert "MET_CLOSURE" in skip_codes(r)


def test_met_closure_explicit_tol_parameter():
    """显式容差参数可替代 facts.CLOSURE_TOL(阈值依据来自调用方, 且真实生效)。"""
    f = mutate(dropped(make_5(), "CLOSURE_TOL"), BRIDGE_ABUT=2.0)   # 闭合差 +2.0
    assert "MET_CLOSURE" in fail_codes(C.met_closure(f, tol=0.005))
    # 容差放大到覆盖差值 → 放行(证明参数不是摆设):
    r2 = C.met_closure(mutate(make_5(), BRIDGE_ABUT=2.0), tol=5.0)
    assert "MET_CLOSURE" not in fail_codes(r2)


def test_met_deck_dir_break():
    assert_criterion_rejects(C.met_deck_camber,
                             mutate(make_5(), DECK_Z_TOP=3.0, DECK_Z_END=4.0),
                             "MET_DECK_DIR")


@pytest.mark.parametrize("kw", [dict(DECK_UP_W=7.0), dict(DECK_UP_W=0.0),
                                dict(DECK_UP_W=-1.0)])
def test_met_taper_break(kw):
    assert_criterion_rejects(C.met_taper, mutate(make_5(), **kw), "MET_TAPER")


def test_met_arch_ratio_break():
    assert_criterion_rejects(C.met_arch_ratio, mutate(make_5(), ARCH_RATIO=0.65),
                             "MET_ARCH_RATIO")


def test_met_arch_ratio_without_declared_intent_is_skip():
    """设计意图未声明 → skip(框架绝不自带"半圆"这类项目假设)。"""
    f = dropped(make_5(), "ARCH_RATIO_TARGET", "ARCH_RATIO_TOL")
    r = C.met_arch_ratio(f)
    assert_skip_not_fail(r, "MET_ARCH_RATIO 无设计意图")


@pytest.mark.parametrize("kw", [
    dict(DECK_Z_TOP=3.5),                     # 压桥面 → 中央拱背 4.0 穿出
    dict(ARCH_RATIO=0.8),                     # 矢高加大 → 拱背 1.2+4.0+0.3 穿出
    dict(RING_T=1.3),                         # 券圈加厚 → 穿出
])
def test_met_ring_fit_break(kw):
    assert_criterion_rejects(C.met_ring_fit, mutate(make_5(), **kw), "MET_RING_FIT")


def test_met_springer_break():
    assert_criterion_rejects(C.met_springer, mutate(make_5(), SPRINGER=5.0),
                             "MET_SPRINGER")


# ══════════ IMP 实现完整性: 逐条破坏 ══════════

@pytest.mark.parametrize("kw", [dict(PIER_W=0.0), dict(BRIDGE_ABUT=-1.0),
                                dict(BRIDGE_LEN=0.0), dict(PIER_W=-2.0)])
def test_imp_dim_break(kw):
    assert_criterion_rejects(C.imp_dims, mutate(make_5(), **kw), "IMP_DIM")


def test_imp_tolerance_break():
    for bad in (0.0, -0.01):
        assert_criterion_rejects(C.imp_tolerance, mutate(make_5(), CLOSURE_TOL=bad),
                                 "IMP_TOLERANCE")


def test_imp_sources_cover_break():
    f = make_5()
    src = {k: v for k, v in f.SOURCES.items() if k != "BRIDGE_LEN"}
    assert_criterion_rejects(C.imp_sources_cover, mutate(f, SOURCES=src),
                             "IMP_SOURCES_COVER")


def test_imp_grades_legal_break():
    f = make_5()
    src = dict(f.SOURCES)
    src["PIER_W"] = ("传说", "无文献, 沿用合成脚本值")
    assert_criterion_rejects(C.imp_grades_legal, mutate(f, SOURCES=src),
                             "IMP_GRADES_ILLEGAL")


def test_imp_assumptions_isolated_break():
    assert_criterion_rejects(C.imp_assumptions_isolated,
                             mutate(make_5(), ASSUMPTION_NAMES=("PIER_W",)),
                             "IMP_ASSUMPTION_LEAK")


def test_imp_assumptions_undeclared_is_skip():
    r = C.imp_assumptions_isolated(dropped(make_5(), "ASSUMPTION_NAMES"))
    assert_skip_not_fail(r, "ASSUMPTION_NAMES 未声明")


# ══════════ RELATIONS: 项目自声明的关系, 判据只验证声明 ══════════

def test_relation_break_is_reported_by_its_own_code():
    assert_criterion_rejects(bridge3d.run_l1,
                             mutate(make_5(), SPAN_DISTINCT=[4.0, 3.0, 5.0]),
                             "REL_central_span_largest")
    assert_criterion_rejects(bridge3d.run_l1,
                             mutate(make_5(), PIER_W=3.5),
                             "REL_pier_narrower_than_min_span")


def test_relation_exception_is_fail_not_crash():
    """声明坏掉的关系(抛异常)必须以 fail 呈现, 不得让整轮判据崩溃。"""

    def boom(f):
        raise RuntimeError("声明写错了")

    f = mutate(make_5(), RELATIONS={"boom": boom})
    r = bridge3d.run_l1(f)
    assert "REL_boom" in fail_codes(r), summarize(r)


def test_relation_missing_fact_is_skip():
    def needs_deck(f):
        raise bridge3d.MissingFactError("DECK_Z_TOP")

    f = mutate(make_5(), RELATIONS={"needs_deck": needs_deck})
    r = bridge3d.run_l1(f)
    assert "REL_needs_deck" in skip_codes(r)
    assert "REL_needs_deck" not in fail_codes(r)


def test_relation_nonbool_is_fail():
    f = mutate(make_5(), RELATIONS={"truthy": lambda f: 1})
    assert "REL_truthy" in fail_codes(bridge3d.run_l1(f))


# ══════════ skip 语义: 缺可选事实绝不 fail(硬性要求) ══════════

ALL_OPTIONALS = ("ARCH_RATIO", "RING_T", "DECK_UP_W", "DECK_DOWN_W",
                 "DECK_Z_TOP", "DECK_Z_END", "CLOSURE_TOL",
                 "ARCH_RATIO_TARGET", "ARCH_RATIO_TOL",
                 "ASSUMPTION_NAMES", "RELATIONS")


@pytest.mark.parametrize("make", MAKERS, ids=IDS)
@pytest.mark.parametrize("field", ALL_OPTIONALS)
def test_missing_single_optional_is_skip_not_fail(make, field):
    """逐个抽掉可选事实: 全轮判据零 fail, 且必须出现 skip(未执行≠通过)。"""
    f = dropped(make(), field)
    r = bridge3d.audit(f)
    assert_skip_not_fail(r, "缺 %s" % field)
    assert skip_codes(r), "缺 %s 应至少有一条判据声明 skip" % field


@pytest.mark.parametrize("make", MAKERS, ids=IDS)
def test_missing_all_optionals_is_skip_not_fail(make):
    """可选事实全部缺省: 剩下的只有 INV 拓扑 + IMP 完整性 —— 仍然零 fail;
    且拓扑层仍在岗(破坏 SPAN_DISTINCT 一致性必须照常红)。"""
    f0 = dropped(make(), *ALL_OPTIONALS)
    assert_skip_not_fail(bridge3d.audit(f0), "全部可选缺省")
    r1 = bridge3d.audit(mutate(f0, SPAN_DISTINCT=[3.0, 4.0]))   # 展开 4 跨 != 5
    assert "INV_SPANS_LEN" in fail_codes(r1), summarize(r1)


# ══════════ 特异性: 无关字段改动不触发任何判据 ══════════

@pytest.mark.parametrize("make", MAKERS, ids=IDS)
def test_specificity_unrelated_field_silent(make):
    base = fail_codes(bridge3d.audit(make()))
    after = fail_codes(bridge3d.audit(mutate(make(), PIER_CAP_W=99.0)))
    assert base == after


# ══════════ 23 孔桥的独立抽样破坏(证明参数化不止对 5 孔有效) ══════════

def test_n23_spot_breaks():
    f = make_23()
    assert_criterion_rejects(bridge3d.run_l1, mutate(f, BRIDGE_ABUT=2.6), "MET_CLOSURE")
    assert_criterion_rejects(bridge3d.run_l1, mutate(f, DECK_UP_W=10.0), "MET_TAPER")
    assert_criterion_rejects(bridge3d.run_l1, mutate(f, N_SPAN=17), "INV_SPANS_LEN")


def test_n23_within_tolerance_passes():
    f = mutate(make_23(), BRIDGE_LEN=make_23().BRIDGE_LEN + 0.005)
    assert_criterion_accepts(bridge3d.run_l1, f, "MET_CLOSURE")


# ══════════ 每条 fail 代码可被杀死(恒真审计, 含检测器级) ══════════

@pytest.mark.parametrize("make", MAKERS, ids=IDS)
def test_no_always_true_in_l1(make):
    """恒真检测: L1 全部 fail 代码都必须有破坏用例能触发。
    INV_SPANS_SYM / INV_SUPPORTS_LEN 经由 facts 输入不可达(E30 同款结论:
    展开规则恒回文、递推恒等长), 用 derive 级破坏(检测器级负控)证明。"""
    from bridge3d.negative_control import assert_no_always_true
    rep = assert_no_always_true(
        bridge3d.run_l1, make(),
        derive_corruptions=[
            ("skew_spans", {"spans": lambda orig: (lambda ff: [9.9] + orig(ff)[1:])}),
            ("short_supports", {"pier_x": lambda orig: (lambda ff: orig(ff)[:-1])}),
        ])
    assert "INV_SPANS_SYM" in rep["kills"], "SYM 必须由 derive 级破坏杀死"
    assert "INV_SUPPORTS_LEN" in rep["kills"], "支承数护栏必须由 derive 级破坏杀死"



# ══════════ MET_TAPER 边界（2026-10-04 框架化时发现的过度约束）══════════
# 原判据 `0 < 顶 < 底` 强制收分, 把十七孔桥(6.56/14.6)的构型误当普适律。
# 等宽桥(薄墩联拱石桥桥面宽基本不变)是合法构型, 强制收分会让它在基线就 fail。

def _fail_codes(f):
    return {fd.code for fd in C.run_l1(f) if fd.level == "fail"}


def _with(**over):
    import copy
    f = copy.copy(make_5())
    for k, v in over.items():
        setattr(f, k, v)
    return f


def test_met_taper_equal_width_is_legal():
    """等宽桥必须放行 —— 框架化核心要求: 不得把单项目构型当普适律。"""
    assert "MET_TAPER" not in _fail_codes(_with(DECK_UP_W=4.1, DECK_DOWN_W=4.1)), \
        "等宽桥被误判 fail; 顶宽=底宽是合法构型"


def test_met_taper_still_catches_inverted():
    """倒悬(顶宽 > 底宽)必须仍被抓 —— 放宽不能变成恒真。"""
    assert "MET_TAPER" in _fail_codes(_with(DECK_UP_W=9.9, DECK_DOWN_W=4.1)), \
        "倒悬未被抓, 判据被放宽成恒真"


def test_met_taper_still_catches_zero_and_negative():
    for bad in (0.0, -1.0):
        assert "MET_TAPER" in _fail_codes(_with(DECK_UP_W=bad, DECK_DOWN_W=4.1)), \
            "顶宽 %s 未被抓" % bad
