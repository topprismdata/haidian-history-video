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
    before = C.inv_spans_sym
    import bridge3d.derive as D
    orig_spans = D.spans
    with patched_derive(spans=lambda orig: (lambda ff: orig(ff))):
        assert D.spans is not orig_spans
    assert D.spans is orig_spans             # 退出必须恢复
    assert C.inv_spans_sym is before


@pytest.mark.parametrize("make", [make_5, make_23], ids=["n5", "n23"])
def test_patched_derive_kills_sym_guard(make):
    """SYM 判据经由 facts 输入不可达(展开恒回文), 检测器级破坏必须能杀它。"""
    f = make()
    assert not fail_codes(C.inv_spans_sym(f))          # 基线绿
    with patched_derive(spans=lambda orig: (lambda ff: [9.9] + orig(ff)[1:])):
        assert "INV_SPANS_SYM" in fail_codes(C.inv_spans_sym(f))
    assert not fail_codes(C.inv_spans_sym(f))          # 恢复后仍绿


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
