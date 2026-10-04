# -*- coding: utf-8 -*-
"""bridge3d.derive 测试: 推导是纯拓扑, 数值随 facts 走 —— 5 孔与 23 孔同一套代码。"""
import sys
from os.path import dirname, join

import pytest

sys.path.insert(0, dirname(__file__))

from bridge3d import derive                # noqa: E402
from bridge3d.schema import MissingFactError  # noqa: E402
from bridge3d.negative_control import mutate  # noqa: E402
from facts_synth import (make_5, make_23,    # noqa: E402
                         make_asym11, make_even6)  # noqa: E402

MAKERS = [make_5, make_23]
IDS = ["n5", "n23"]


@pytest.mark.parametrize("make", MAKERS, ids=IDS)
def test_spans_expansion_length_and_palindrome(make):
    f = make()
    sp = derive.spans(f)
    assert len(sp) == f.N_SPAN
    assert all(sp[i] == sp[len(sp) - 1 - i] for i in range(len(sp) // 2))


@pytest.mark.parametrize("make", MAKERS, ids=IDS)
def test_pier_count_is_topological_not_project_constant(make):
    """内墩数 = N_SPAN-1 纯拓扑推导, 对任意孔数成立(绝无写死值)。"""
    f = make()
    assert derive.pier_count(f) == f.N_SPAN - 1
    assert derive.support_count(f) == f.N_SPAN + 1


def test_pier_count_scales_across_n_spans():
    for n in (1, 2, 5, 16, 23, 100):
        f = mutate(make_5(), N_SPAN=n)
        assert derive.pier_count(f) == n - 1
        assert derive.support_count(f) == n + 1


def test_single_span_topology():
    """N_SPAN=1(无内墩)是合法拓扑: 两个桥台支承一跨。"""
    f = mutate(make_5(), N_SPAN=1, SPAN_DISTINCT=[5.0], BRIDGE_LEN=7.0)
    assert derive.spans(f) == [5.0]
    assert derive.pier_count(f) == 0
    xs = derive.pier_x(f)
    assert len(xs) == 2
    assert xs[0] == pytest.approx(-3.5 + 0.5)
    assert xs[1] == pytest.approx(3.5 - 0.5)
    assert derive.geometry_closure(f)[2] == pytest.approx(0.0, abs=1e-9)


@pytest.mark.parametrize("make", MAKERS, ids=IDS)
def test_pier_x_recursion_shape(make):
    f = make()
    xs = derive.pier_x(f)
    half = f.BRIDGE_LEN / 2.0
    assert len(xs) == f.N_SPAN + 1
    assert xs[0] == pytest.approx(-half + f.BRIDGE_ABUT / 2.0)
    assert xs[-1] == pytest.approx(half - f.BRIDGE_ABUT / 2.0)
    assert all(xs[i] < xs[i + 1] for i in range(len(xs) - 1))   # 升序


@pytest.mark.parametrize("make", MAKERS, ids=IDS)
def test_geometry_closure_exact(make):
    """合成 facts 精确闭合: 差值≈0(基线必须静默的前提)。"""
    computed, target, delta = derive.geometry_closure(make())
    assert delta == pytest.approx(0.0, abs=1e-9)
    assert computed == pytest.approx(target, abs=1e-9)


def test_geometry_closure_detects_break():
    """破坏: 桥台 +Δ → 总长多 2Δ(两端), 差值必须反映。"""
    f = mutate(make_5(), BRIDGE_ABUT=make_5().BRIDGE_ABUT + 0.3)
    _c, _t, delta = derive.geometry_closure(f)
    assert delta == pytest.approx(0.6, abs=1e-9)


@pytest.mark.parametrize("make", MAKERS, ids=IDS)
def test_deck_z_parabola(make):
    f = make()
    z = derive.deck_z(f)
    half = f.BRIDGE_LEN / 2.0
    assert z(0.0) == pytest.approx(f.DECK_Z_TOP, abs=1e-9)
    assert z(half) == pytest.approx(f.DECK_Z_END, abs=1e-9)
    assert z(-half) == pytest.approx(f.DECK_Z_END, abs=1e-9)
    assert z(0.25 * half) > z(0.75 * half) > z(half)   # 中央最高, 向两端单调降
    assert z(0.6 * half) == pytest.approx(z(-0.6 * half), abs=1e-12)  # 左右对称


def test_deck_z_missing_fact_raises_missing_fact_error():
    from bridge3d.negative_control import dropped as _dropped
    f = _dropped(make_5(), "DECK_Z_TOP")
    with pytest.raises(MissingFactError):
        derive.deck_z(f)


@pytest.mark.parametrize("make", MAKERS, ids=IDS)
def test_derive_never_crashes_on_missing_required(make):
    """缺必填事实 → MissingFactError(判据层降级 skip), 绝不静默给错值。"""
    from bridge3d.negative_control import dropped as _dropped
    f = _dropped(make(), "SPAN_DISTINCT")
    with pytest.raises(MissingFactError):
        derive.spans(f)
    with pytest.raises(MissingFactError):
        derive.geometry_closure(f)


# ══════════ SPAN_DISTINCT 两种声明形态（2026-10-05 终审 I1）══════════

def test_spans_full_length_list_used_verbatim():
    """全长表(len==N_SPAN)必须原样使用, 不做任何镜像变换 ——
    不对称桥(东端跨≠西端跨)与偶数孔桥借此表达。"""
    f = make_asym11()
    sp = derive.spans(f)
    assert sp == list(f.SPAN_DISTINCT), "全长表被改写: %r" % (sp,)
    assert sp[0] != sp[-1], "破坏用例本身失去不对称性"

    fe = make_even6()
    spe = derive.spans(fe)
    assert len(spe) == fe.N_SPAN == 6, "偶数孔桥展开 %d != %d" % (len(spe), fe.N_SPAN)


def test_spans_half_side_mirror_path_kept():
    """半侧表便利路径保持原行为: D + reversed(D[:-1]), 恒回文恒奇数长。"""
    f = make_5()
    assert derive.spans(f) == [3.0, 4.0, 5.0, 4.0, 3.0]


def test_spans_odd_length_mismatch_still_reported_not_crash():
    """两种形态之外的长度: 原样交给 INV_SPANS_LEN 报 fail, spans() 不崩。"""
    f = mutate(make_5(), SPAN_DISTINCT=[3.0, 4.0])       # 2 值: 非全长非半侧
    assert len(derive.spans(f)) == 3                      # 镜像路径, 长度不一致
    import bridge3d
    from bridge3d.negative_control import fail_codes
    assert "INV_SPANS_LEN" in fail_codes(bridge3d.run_l1(f))


def test_spans_missing_n_span_is_missing_fact_error():
    """N_SPAN 现在是展开的前置事实: 缺失 → MissingFactError(降级 skip, 不静默)。"""
    from bridge3d.negative_control import dropped as _dropped
    with pytest.raises(MissingFactError):
        derive.spans(_dropped(make_5(), "N_SPAN"))
