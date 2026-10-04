# -*- coding: utf-8 -*-
"""bridge3d.schema 契约测试: 结构校验每条规则可证伪(违反 → 必红)。"""
import sys
from os.path import dirname, join

import pytest

sys.path.insert(0, dirname(__file__))

from bridge3d import schema as S          # noqa: E402
from bridge3d.negative_control import mutate, dropped, fail_codes, skip_codes  # noqa: E402
from facts_synth import make_5, make_23   # noqa: E402

MAKERS = [make_5, make_23]


@pytest.mark.parametrize("make", MAKERS, ids=["n5", "n23"])
def test_synthetic_facts_structurally_valid(make):
    """合成 facts(5 孔/23 孔)必须零 fail —— 契约本身不得误伤合法项目。"""
    findings = S.validate_facts_module(make())
    assert not fail_codes(findings), S.summarize(findings)


@pytest.mark.parametrize("make", MAKERS, ids=["n5", "n23"])
@pytest.mark.parametrize("field", ["BRIDGE_LEN", "N_SPAN", "SPRINGER",
                                   "PIER_W", "BRIDGE_ABUT", "SPAN_DISTINCT",
                                   "SOURCES", "RESEARCH_DONE"])
def test_missing_required_is_fail(make, field):
    """每类必填项缺失必须红(可证伪)。"""
    r = S.validate_facts_module(dropped(make(), field))
    assert fail_codes(r), "删除 %s 未被抓" % field


def test_missing_required_codes_are_specific():
    r = S.validate_facts_module(dropped(make_5(), "BRIDGE_LEN"))
    assert "IMP_REQUIRED_MISSING" in fail_codes(r)
    r = S.validate_facts_module(dropped(make_5(), "SPAN_DISTINCT"))
    assert "IMP_LIST_MISSING" in fail_codes(r)
    r = S.validate_facts_module(dropped(make_5(), "SOURCES"))
    assert "IMP_REGS_MISSING" in fail_codes(r)


def test_non_int_n_span_rejected():
    """孔数是拓扑量: 5.0 / True 都不是合法 int。"""
    for bad in (5.0, True, "5", None):
        r = S.validate_facts_module(mutate(make_5(), N_SPAN=bad))
        assert fail_codes(r), "N_SPAN=%r 应被拒" % (bad,)


def test_bad_list_shape_rejected():
    for bad in ([], "3,4,5", [0.0, 4.0, 5.0], [3.0, "4", 5.0]):
        r = S.validate_facts_module(mutate(make_5(), SPAN_DISTINCT=bad))
        assert "IMP_LIST_SHAPE" in fail_codes(r), "SPAN_DISTINCT=%r 应被拒" % (bad,)


def test_bad_registry_shape_rejected():
    r = S.validate_facts_module(mutate(make_5(), SOURCES="没有台账"))
    assert "IMP_REGS_SHAPE" in fail_codes(r)
    r = S.validate_facts_module(mutate(make_5(), RESEARCH_DONE=1))
    assert "IMP_REGS_SHAPE" in fail_codes(r)


def test_malformed_relations_rejected():
    r = S.validate_facts_module(mutate(make_5(), RELATIONS={"r1": 42}))
    assert "IMP_RELATIONS_SHAPE" in fail_codes(r)
    r = S.validate_facts_module(mutate(make_5(), RELATIONS="不是表"))
    assert "IMP_RELATIONS_SHAPE" in fail_codes(r)


def test_relations_absent_is_skip_never_fail():
    """未声明 RELATIONS 是合法选择: skip 语义, 不得 fail。"""
    r = S.validate_facts_module(dropped(make_5(), "RELATIONS"))
    assert not fail_codes(r), S.summarize(r)
    assert "IMP_RELATIONS_ABSENT" in skip_codes(r)


def test_optional_missing_never_fails():
    """可选条目全部缺省: 零 fail(判据层各自 skip)。"""
    f = dropped(make_5(), "ARCH_RATIO", "RING_T", "DECK_UP_W", "DECK_DOWN_W",
                "DECK_Z_TOP", "DECK_Z_END", "CLOSURE_TOL",
                "ARCH_RATIO_TARGET", "ARCH_RATIO_TOL", "ASSUMPTION_NAMES")
    r = S.validate_facts_module(f)
    assert not fail_codes(r), S.summarize(r)


def test_optional_wrong_type_is_fail():
    """存在但类型非法比缺失更糟: 必须红。"""
    r = S.validate_facts_module(mutate(make_5(), CLOSURE_TOL="很大"))
    assert "IMP_OPTIONAL_TYPE" in fail_codes(r)
    r = S.validate_facts_module(mutate(make_5(), ASSUMPTION_NAMES=("A", 3)))
    assert "IMP_OPTIONAL_TYPE" in fail_codes(r)


def test_summarize_and_levels_helpers():
    findings = S.validate_facts_module(dropped(make_5(), "RELATIONS"))
    text = S.summarize(findings)
    assert "skip=1" in text and "IMP_RELATIONS_ABSENT" in text
    assert S.has_fail(findings) is False
