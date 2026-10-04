# -*- coding: utf-8 -*-
"""bridge3d.negative_control 测试: 负控制工具自身的负控制。

恒真检测工具必须能抓住: 恒绿判据 / 条件恒真判据 / 崩溃判据,
并且不能冤枉活判据(活判据必须能通过审计)。
"""
import sys
from os.path import dirname, join

import pytest

sys.path.insert(0, dirname(__file__))

from bridge3d import checks_l1 as C        # noqa: E402
from bridge3d.negative_control import (     # noqa: E402
    mutate, dropped, snapshot, fail_codes,
    assert_criterion_rejects, assert_criterion_accepts,
    patched_derive, default_corruptions,
    killability_report, assert_no_always_true)
from bridge3d.schema import MissingFactError  # noqa: E402
from facts_synth import make_5, make_23    # noqa: E402


# ══════════ mutate/dropped 克隆语义 ══════════

def test_mutate_does_not_touch_original():
    f = make_5()
    original_span = list(f.SPAN_DISTINCT)
    f2 = mutate(f, BRIDGE_LEN=999.0)
    assert f2.BRIDGE_LEN == 999.0
    assert f.BRIDGE_LEN != 999.0
    f2.SPAN_DISTINCT.append(123.0)           # 克隆上原地改, 原件不得受影响
    assert f.SPAN_DISTINCT == original_span


def test_dropped_removes_field_and_snapshot_keeps_doc():
    f = dropped(make_5(), "ARCH_RATIO")
    assert not hasattr(f, "ARCH_RATIO")
    assert snapshot(make_5())["__doc__"]     # 禁令锁的对象必须随克隆走


# ══════════ 点状断言工具 ══════════

def test_assert_rejects_passes_when_caught():
    assert_criterion_rejects(C.inv_n_span, mutate(make_5(), N_SPAN=-5), "INV_N_SPAN")


def test_assert_rejects_fails_when_not_caught():
    with pytest.raises(AssertionError, match="破坏未被抓"):
        assert_criterion_rejects(lambda f: [], make_5(), "ANY_CODE")


def test_assert_rejects_fails_on_crash():
    def crashing(f):
        raise ZeroDivisionError("boom")
    with pytest.raises(AssertionError, match="崩溃而非报告"):
        assert_criterion_rejects(crashing, make_5(), "ANY_CODE")


def test_assert_accepts_fails_on_false_positive():
    def always_red(f):
        from bridge3d.schema import Finding
        return [Finding("fail", "X", "恒红")]
    with pytest.raises(AssertionError, match="误报"):
        assert_criterion_accepts(always_red, make_5(), "X")


# ══════════ patched_derive(检测器级负控) ══════════

@pytest.mark.parametrize("make", [make_5, make_23], ids=["n5", "n23"])
def test_patched_derive_restores_state(make):
    import bridge3d.derive as D
    orig_spans = D.spans
    with patched_derive(spans=lambda orig: (lambda ff: orig(ff))):
        assert D.spans is not orig_spans
    assert D.spans is orig_spans             # 退出必须恢复


@pytest.mark.parametrize("make", [make_5, make_23], ids=["n5", "n23"])
def test_patched_derive_kills_spans_len_guard(make):
    """展开长度护栏经由 facts 输入不可达(展开恒与半侧表一致),
    检测器级破坏必须能杀 INV_SPANS_LEN。
    (原 SYM 护栏已随 2026-10-05 终审 I1 降级: 对称是项目 RELATIONS 自声明,
    不再是框架 INV 普适律; 展开规则本身的回文属性由 test_derive 单测锁。)"""
    f = make()
    assert not fail_codes(C.inv_spans_len(f))          # 基线绿
    with patched_derive(spans=lambda orig: (lambda ff: orig(ff)[:-1])):
        assert "INV_SPANS_LEN" in fail_codes(C.inv_spans_len(f))
    assert not fail_codes(C.inv_spans_len(f))          # 恢复后仍绿


# ══════════ 恒真检测工具的三种失败模式 ══════════

def test_always_green_criterion_is_flagged():
    with pytest.raises(AssertionError, match="恒真"):
        assert_no_always_true(lambda f: [], make_5())


def test_narrow_tautology_is_flagged():
    """只在永不出现的条件下变红 = 恒真: 自动破坏用例杀不死它。
    codes 显式点名该代码 → 审计必须报"无破坏可触发"; 不点名 → 报"从未变红"。"""
    def narrow(f):
        from bridge3d.schema import Finding
        if getattr(f, "N_SPAN", None) == 999999:
            return [Finding("fail", "NARROW", "x")]
        return []
    with pytest.raises(AssertionError, match="NARROW"):
        assert_no_always_true(narrow, make_5(), codes=("NARROW",))
    with pytest.raises(AssertionError, match="恒真"):
        assert_no_always_true(narrow, make_5())


def test_crashing_criterion_is_flagged():
    """崩溃不是报告: 破坏下抛异常的判据必须被判缺陷。"""
    def fragile(f):
        if f.BRIDGE_LEN == 0:
            raise ZeroDivisionError("boom")
        return []
    with pytest.raises(AssertionError, match="崩溃而非报告"):
        assert_no_always_true(fragile, make_5())


def test_live_criterion_passes_audit():
    """活判据不得被冤枉: N_SPAN<1 即红的判据应通过审计。"""
    def live(f):
        from bridge3d.schema import Finding
        n = getattr(f, "N_SPAN", None)
        if isinstance(n, bool) or not isinstance(n, int) or n < 1:
            return [Finding("fail", "LIVE", "x")]
        return []
    rep = assert_no_always_true(live, make_5())
    assert "LIVE" in rep["kills"]


def test_killability_report_records_baseline_separately():
    rep = killability_report(lambda f: [], make_5())
    assert rep["baseline_fail_codes"] == []
    assert rep["kills"] == {}                # 恒绿判据: 无任何代码被杀
    assert rep["crashes"] == []


# ══════════ 自动破坏用例生成 ══════════

def test_default_corruptions_covers_required_and_optionals():
    cors = default_corruptions(make_5())
    labels = [l for l, _ in cors]
    for field in ("BRIDGE_LEN", "N_SPAN", "PIER_W", "SPAN_DISTINCT",
                  "ARCH_RATIO", "DECK_Z_TOP", "CLOSURE_TOL"):
        assert any(("zero:" + field) in l or ("missing:" + field) in l
                   or field in l for l in labels), "破坏用例未覆盖 %s: %r" % (field, labels)
    assert any(l.startswith("doc:") for l in labels)
    assert any(l.startswith("sources:") for l in labels)


def test_default_corruptions_are_type_safe():
    """破坏用例本身不得把判据弄崩(类型安全): 逐个喂给 INV/MET 判据不得抛异常。"""
    for label, cf in default_corruptions(make_5()):
        for chk in (C.inv_n_span, C.inv_spans_len, C.met_closure,
                    C.met_taper, C.imp_dims):
            try:
                chk(cf)
            except MissingFactError:
                pass                          # 缺事实是合法降级
            except Exception as e:            # noqa: BLE001
                raise AssertionError("破坏用例 %s 使判据 %r 崩溃: %r"
                                     % (label, chk.__name__, e))


# ══════════ 双向恒真检测(2026-10-05 终审 I5) ══════════
# 旧检测器只查"能不能红", 放得过"基线就红"的过度约束判据
# (MET_TAPER 原病与对称奇数孔契约均由此过审), 且 codes=None 时死判据被掩盖。

def test_baseline_red_criterion_is_flagged():
    """见谁都咬的判据(合法基线上就红)必须被双向检测抓住 —— 修复前放行。"""
    from bridge3d.schema import Finding

    def bite_all(f):
        return [Finding("fail", "BITE", "x")]
    with pytest.raises(AssertionError, match="基线即红"):
        assert_no_always_true(bite_all, make_5())
    # 显式豁免才放行(豁免本身可见, 不是静默):
    rep = assert_no_always_true(bite_all, make_5(), require_baseline_green=False)
    assert "BITE" in rep["baseline_fail_codes"]


def test_overconstrained_morphology_criterion_caught():
    """MET_TAPER 原病复刻(强制收分 0<顶<底)在等宽桥基线上就红 ——
    双向检测必须抓, 这正是 I1 能存活到终审的机制漏洞。"""
    from bridge3d.schema import Finding
    from facts_synth import make_equal4

    def enforce_taper(f):
        from bridge3d.schema import is_number
        up = getattr(f, "DECK_UP_W", None)
        down = getattr(f, "DECK_DOWN_W", None)
        if not (is_number(up) and is_number(down)):
            return []                      # 前置缺失/非法走 skip 语义, 不崩(判据铁律)
        if not 0 < up < down:
            return [Finding("fail", "MET_TAPER", "强制收分")]
        return []
    with pytest.raises(AssertionError, match="基线即红"):
        assert_no_always_true(enforce_taper, make_equal4())


def test_criterion_alive_requires_explicit_codes():
    """逐判据入口: codes 必须显式; 声明的死代码必须报错(修复前 codes=None 静默掩盖)。"""
    from bridge3d.schema import Finding
    from bridge3d.negative_control import assert_criterion_alive

    def dead(f):
        if getattr(f, "N_SPAN", None) == 999999:
            return [Finding("fail", "DEAD", "x")]
        return []
    with pytest.raises(AssertionError, match="必须显式给出 codes"):
        assert_criterion_alive(dead, make_5(), codes=())
    with pytest.raises(AssertionError, match="DEAD"):
        assert_criterion_alive(dead, make_5(), codes=("DEAD",))
    # 活判据 + 正确的声明代码表 → 通过:
    def live(f):
        if getattr(f, "N_SPAN", None) is None or f.N_SPAN < 1:
            return [Finding("fail", "LIVE_A", "x")]
        if isinstance(f.N_SPAN, bool):
            return [Finding("fail", "LIVE_B", "x")]
        return []
    rep = assert_criterion_alive(live, make_5(), codes=("LIVE_A", "LIVE_B"))
    assert set(rep["kills"]) >= {"LIVE_A", "LIVE_B"}


@pytest.mark.parametrize("make", [make_5, make_23], ids=["n5", "n23"])
def test_l1_default_corruptions_cover_shape_and_type_axes(make):
    """新破坏轴(SOURCES 非dict / RESEARCH_DONE 非bool / RELATIONS 非dict /
    N_SPAN 浮点 / scale8)必须存在且类型安全(不得把判据弄崩)。"""
    labels = [l for l, _ in default_corruptions(make())]
    for want in ("shape:SOURCES_not_dict", "shape:RESEARCH_DONE_nonbool",
                 "shape:RELATIONS_not_dict", "type:N_SPAN_float"):
        assert want in labels, (want, labels)
    assert any(l.startswith("scale8:") for l in labels)
    f = make()
    from bridge3d.schema import Finding
    for label, cf in default_corruptions(f):
        try:
            C.run_l1(cf)
        except MissingFactError:
            pass
        except Exception as e:   # noqa: BLE001
            raise AssertionError("破坏 %s 使 run_l1 崩溃: %r" % (label, e))
