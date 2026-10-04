# -*- coding: utf-8 -*-
"""bridge3d.facts_schema 测试: 每条事实层校验器可证伪(违反 → 必红) + 基线全绿。"""
import sys
from os.path import dirname, join

import pytest

sys.path.insert(0, dirname(__file__))

from bridge3d import facts_schema as FS    # noqa: E402
from bridge3d.schema import warn_codes     # noqa: E402
from bridge3d.negative_control import (     # noqa: E402
    mutate, dropped, fail_codes,
    assert_criterion_rejects, assert_no_always_true)
from bridge3d.schema import summarize       # noqa: E402
from facts_synth import make_5, make_23     # noqa: E402

MAKERS = [make_5, make_23]
IDS = ["n5", "n23"]


# ══════════ 基线 ══════════

@pytest.mark.parametrize("make", MAKERS, ids=IDS)
def test_synthetic_facts_pass_all_fact_checks(make):
    r = FS.run_fact_checks(make())
    assert not fail_codes(r), summarize(r)
    assert not warn_codes(r), summarize(r)


def _src(f, key):
    return {k: v for k, v in f.SOURCES.items() if k != key}


def _with_entry(f, key, value):
    s = dict(f.SOURCES)
    s[key] = value
    return mutate(f, SOURCES=s)


# ══════════ 逐条可证伪矩阵 ══════════

@pytest.mark.parametrize("make", MAKERS, ids=IDS)
def test_missing_source_entry_fails(make):
    assert_criterion_rejects(FS.check_sources_complete,
                             mutate(make(), SOURCES=_src(make(), "N_SPAN")),
                             "FS_SOURCES_MISSING")


@pytest.mark.parametrize("make", MAKERS, ids=IDS)
def test_empty_note_fails(make):
    assert_criterion_rejects(FS.check_source_shape,
                             _with_entry(make(), "PIER_W", ("工作值", "")),
                             "FS_SOURCE_SHAPE")


@pytest.mark.parametrize("make", MAKERS, ids=IDS)
def test_illegal_grade_fails(make):
    """五级之外的任何等级写法(含"待核"这类占位符)都非法。"""
    assert_criterion_rejects(FS.check_grades_legal,
                             _with_entry(make(), "PIER_W", ("待核", "还没查")),
                             "FS_GRADE_ILLEGAL")
    assert_criterion_rejects(FS.check_grades_legal,
                             _with_entry(make(), "PIER_W", ("传说", "据说")),
                             "FS_GRADE_ILLEGAL")


@pytest.mark.parametrize("make", MAKERS, ids=IDS)
def test_stale_required_key_fails_and_optional_key_warns(make):
    # 必填常量的属性没了而 SOURCES 还登记着 → 来源台账与事实脱节, fail:
    f_gone = dropped(make(), "BRIDGE_LEN")
    assert_criterion_rejects(FS.check_stale_keys, f_gone, "FS_STALE_KEY")
    # 幽灵键(从来不是常量)属记账噪声 → warn 不阻塞:
    r_ghost = FS.check_stale_keys(_with_entry(make(), "GHOST_DIM",
                                              ("工作值", "无文献, 幽灵键")))
    assert "FS_STALE_KEY_OPTIONAL" in warn_codes(r_ghost)
    assert not fail_codes(r_ghost)
    # 可选条目残留只 warn 不 fail(缺可选事实必须走 skip 语义):
    f2 = dropped(make(), "ARCH_RATIO")   # 属性没了, SOURCES 还登记着
    r = FS.check_stale_keys(f2)
    assert "FS_STALE_KEY_OPTIONAL" in warn_codes(r), summarize(r)
    assert not fail_codes(r)


@pytest.mark.parametrize("make", MAKERS, ids=IDS)
def test_undocumented_working_value_fails(make):
    assert_criterion_rejects(FS.check_working_values_documented,
                             _with_entry(make(), "SPRINGER", ("工作值", "据说如此")),
                             "FS_WORKING_UNDOCUMENTED")


@pytest.mark.parametrize("make", MAKERS, ids=IDS)
def test_grade_inflation_fails(make):
    """说明自认无正式来源却标更高等级 = 等级造假, 必红。"""
    f = make()
    inflated = dict(f.SOURCES)
    inflated["SPRINGER"] = ("官方", "无文献, 沿用合成脚本值")
    assert_criterion_rejects(FS.check_no_grade_inflation, mutate(f, SOURCES=inflated),
                             "FS_GRADE_INFLATED")


@pytest.mark.parametrize("make", MAKERS, ids=IDS)
def test_official_without_citation_fails(make):
    """[官方] 无正面出处(含否定语境里的年份)不予认定。"""
    assert_criterion_rejects(FS.check_official_citation,
                             _with_entry(make(), "BRIDGE_LEN",
                                         ("官方", "据说长很多")),
                             "FS_OFFICIAL_UNCITED")
    # 否定语境里的年份不算出处(E30 负控实证的漏网场景):
    assert_criterion_rejects(FS.check_official_citation,
                             _with_entry(make(), "BRIDGE_LEN",
                                         ("官方", "2024 年档案未检回, 查无")),
                             "FS_OFFICIAL_UNCITED")


@pytest.mark.parametrize("make", MAKERS, ids=IDS)
def test_official_with_institution_year_passes(make):
    f = _with_entry(make(), "BRIDGE_LEN",
                    ("官方", "虚构文保中心 2024 公告(无 URL 口径)"))
    assert not fail_codes(FS.check_official_citation(f))


@pytest.mark.parametrize("make", MAKERS, ids=IDS)
def test_research_flag_semantics(make):
    assert_criterion_rejects(FS.check_research_flag, mutate(make(), RESEARCH_DONE="yes"),
                             "FS_RESEARCH_FLAG")
    r = FS.check_research_flag(mutate(make(), RESEARCH_DONE=False))
    assert "FS_RESEARCH_PENDING" in warn_codes(r), summarize(r)
    assert not fail_codes(r)


@pytest.mark.parametrize("make", MAKERS, ids=IDS)
def test_assumption_leak_fails(make):
    assert_criterion_rejects(FS.check_assumptions_not_registered,
                             mutate(make(), ASSUMPTION_NAMES=("PIER_W",)),
                             "FS_ASSUMPTION_LEAK")


@pytest.mark.parametrize("make", MAKERS, ids=IDS)
@pytest.mark.parametrize("ban_case,doc", [
    ("FS_BAN_PHOTO_METRIC", "禁令: 超分(ESRGAN)结果禁入计量链; GPT 聊天记录不算来源。"),
    ("FS_BAN_SUPERRES", "禁令: 未标定照片不得产生绝对米制尺寸; GPT 聊天记录不算来源。"),
    ("FS_BAN_GPT_SOURCE", "禁令: 未标定照片不得产生绝对米制尺寸; 超分结果禁入计量链。"),
])
def test_each_docstring_ban_is_independently_falsifiable(make, ban_case, doc):
    """三条禁令逐条可删、逐条必红(E30 审查探针教训: 只锁一条时其余全成摆设)。"""
    assert_criterion_rejects(FS.check_docstring_bans, mutate(make(), __doc__=doc),
                             ban_case)


# ══════════ 整轮事实层: 恒真审计 + skip 语义 ══════════

@pytest.mark.parametrize("make", MAKERS, ids=IDS)
def test_no_always_true_in_fact_checks(make):
    rep = assert_no_always_true(FS.run_fact_checks, make())
    for code in ("FS_SOURCES_MISSING", "FS_GRADE_ILLEGAL", "FS_GRADE_INFLATED",
                 "FS_OFFICIAL_UNCITED", "FS_WORKING_UNDOCUMENTED",
                 "FS_STALE_KEY", "FS_ASSUMPTION_LEAK",
                 "FS_BAN_PHOTO_METRIC", "FS_BAN_SUPERRES", "FS_BAN_GPT_SOURCE"):
        assert code in rep["kills"], "%s 无破坏可触发(恒真嫌疑)" % code


@pytest.mark.parametrize("make", MAKERS, ids=IDS)
def test_missing_sources_degrades_to_skip_not_fail(make):
    """SOURCES 整体缺失: 完备性必须红, 深度校验器必须 skip 而非连锁误报。"""
    f = dropped(make(), "SOURCES")
    r = FS.run_fact_checks(f)
    assert "FS_SOURCES_MISSING" in fail_codes(r)
    assert "FS_GRADE_ILLEGAL" in [x.code for x in r if x.level == "skip"]


# ══════════ 逐校验器显式点名恒真审计（2026-10-05 终审 I5）══════════

_FACT_CHECKER_CODES = [
    (FS.check_sources_complete, ("FS_SOURCES_MISSING",)),
    (FS.check_source_shape, ("FS_SOURCE_SHAPE",)),
    (FS.check_grades_legal, ("FS_GRADE_ILLEGAL",)),
    (FS.check_stale_keys, ("FS_STALE_KEY",)),
    (FS.check_working_values_documented, ("FS_WORKING_UNDOCUMENTED",)),
    (FS.check_no_grade_inflation, ("FS_GRADE_INFLATED",)),
    (FS.check_official_citation, ("FS_OFFICIAL_UNCITED",)),
    (FS.check_research_flag, ("FS_RESEARCH_FLAG",)),
    (FS.check_assumptions_not_registered, ("FS_ASSUMPTION_LEAK",)),
    (FS.check_docstring_bans, ("FS_BAN_PHOTO_METRIC", "FS_BAN_SUPERRES",
                               "FS_BAN_GPT_SOURCE")),
]

_ALT = [make_23]      # make_5 由上一节全量覆盖; 基线 green 侧在 test_checks_l1 六构型


@pytest.mark.parametrize("chk_codes", _FACT_CHECKER_CODES,
                         ids=lambda cc: cc[0].__name__)
@pytest.mark.parametrize("make", [make_5] + _ALT, ids=["n5", "n23"])
def test_each_fact_checker_alive_with_explicit_codes(chk_codes, make):
    """事实层每条校验器: 基线绿 + 声明的全部 fail 代码逐一可杀(死校验器必须报错)。"""
    from bridge3d.negative_control import assert_criterion_alive
    chk, codes = chk_codes
    assert_criterion_alive(chk, make(), codes)
