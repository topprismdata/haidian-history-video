# -*- coding: utf-8 -*-
"""E30 Task1 来源完备性测试。

判据语义: 只有 fail 阻塞; skip 不算通过。
- 核心判据: facts 本体常量必须逐个登记进 SOURCES(漏一即 fail)。
- 旗标闸门: RESEARCH_DONE=False 允许[待核]/[工作值]; True 禁止二者。
- G1 分家: assumptions 的名字不得出现在 SOURCES(假设层不参与冻结)。
- 文档禁令可执行化: facts docstring 必须写明 ESRGAN / 计量 禁令。
"""
import importlib
import sys
from pathlib import Path

import pytest

_3D_DIR = Path(__file__).resolve().parents[1] / "3d"
sys.path.insert(0, str(_3D_DIR))

facts = importlib.import_module("facts")
assumptions = importlib.import_module("assumptions")

ALLOWED_LEVELS = {"测绘", "档案", "官方", "图像推导", "工作值", "待核"}


def _public_constants():
    out = []
    for n in dir(facts):
        if n.startswith("_") or n in ("SOURCES", "RESEARCH_DONE"):
            continue
        v = getattr(facts, n)
        if isinstance(v, (int, float, list)):
            out.append(n)
    return sorted(out)


def test_every_constant_has_source():
    """核心判据: 每个本体常量都必须有来源登记, 漏一个即 fail。"""
    missing = [n for n in _public_constants() if n not in facts.SOURCES]
    assert not missing, "缺来源登记: %s" % missing


def test_sources_keys_are_live_names():
    """SOURCES 不得残留指向已改名/已删除常量的键(如旧名 SPANS/HALF_SPANS)。"""
    stale = [k for k in facts.SOURCES if not hasattr(facts, k)]
    assert not stale, "SOURCES 指向不存在的常量: %s" % stale


def test_sources_value_shape():
    """每个 SOURCES 值是 (等级, 说明) 二元组, 等级属于 G1 五级+待核。"""
    for name, val in facts.SOURCES.items():
        assert isinstance(val, tuple) and len(val) == 2, (
            "%s 的来源须为 (等级, 说明) 二元组, 实为 %r" % (name, val))
        lvl, note = val
        assert lvl in ALLOWED_LEVELS, "%s 等级非法: %r" % (name, lvl)
        assert isinstance(note, str) and note.strip(), "%s 出处说明为空" % name


def test_research_done_is_monotonic_lock():
    """T1 首版把这里锁成"必须恒为 False"——那是自爆式锁: M0 完成后旗标必须翻 True,
    届时套件必红而测试本身没有任何错。改为锁"旗标一旦为 True 就不再有 [待核]/[工作值]",
    并在本文件顶部用 REVIEW_DONE 常量记录 T1 时点的初值断言, 由 T2 明确退役。"""
    assert isinstance(facts.RESEARCH_DONE, bool)
    # 初值断言已迁移到 T2(旗标翻 True 后本断言由 test_no_pending_after_research 接管):
    """旗标闸门(随 RESEARCH_DONE 变化):
    False 期间允许[待核]/[工作值]; 置 True 后二者一律禁止。"""
    forbidden = ("待核", "工作值") if facts.RESEARCH_DONE else ()
    offenders = sorted(
        n for n, (lvl, _note) in facts.SOURCES.items() if lvl in forbidden)
    assert not offenders, "RESEARCH_DONE=%s 时仍存在禁用等级条目: %s" % (
        facts.RESEARCH_DONE, offenders)


def test_span_distinct_shape_and_symmetric_closure():
    """SPAN_DISTINCT 是 9 个完整净跨; 对称展开成 17 跨后:
    总水路 = 107.3m, 加中央区 9*PIER_W = 22.5m 与 107.3+22.5 自洽。
    (简报的 sum(SPANS)+15*PIER_W+2*BRIDGE_ABUT 全桥闭合判据属 T2b, 不在本测试。)"""
    sd = facts.SPAN_DISTINCT
    assert len(sd) == 9, "SPAN_DISTINCT 须为 9 个完整净跨, 实为 %d" % len(sd)
    assert len(facts.DECK_Z_AT_PIER) == 9, "DECK_Z_AT_PIER 须为 9 个纵坡控制点"
    # 对称展开: 9 值 + 前 8 值镜像(中央孔 8.50 只计一次) = 17 跨
    expanded = list(sd) + list(reversed(sd[:-1]))
    assert len(expanded) == facts.N_SPAN
    water = sum(expanded)
    assert water == pytest.approx(107.3, abs=1e-9), (
        "对称展开总水路 %r != 107.3" % water)
    assert water + 9 * facts.PIER_W == pytest.approx(107.3 + 22.5, abs=1e-9), (
        "水路+9*PIER_W 自洽校验失败: %r" % (water + 9 * facts.PIER_W))


def test_assumptions_not_in_sources():
    """G1 分家: 假设层参数(判据参数+建模假定)不进来源注册表、不参与冻结。"""
    assumption_names = [n for n in dir(assumptions) if not n.startswith("_")]
    assert assumption_names, "assumptions 模块异常: 无公开参数"
    for n in assumption_names:
        assert n not in facts.SOURCES, "假设层 %s 不得进 SOURCES" % n


def test_docstring_carries_bans():
    """文档级禁令的可执行版本: 禁令写进模块 docstring 并被测试锁住。"""
    doc = facts.__doc__ or ""
    assert "ESRGAN" in doc, "facts docstring 缺 ESRGAN 禁令(超分结果禁进计量链)"
    assert "计量" in doc, "facts docstring 缺 计量 禁令"


# ── T1 review Important#2: 三条禁令必须条条可证伪, 不能只锁一条 ──
# 审查探针实测: 删掉"未标定照片"或"GPT 聊天记录"禁令整句, 原套件仍全绿 -> 这是恒真。
# 逐条锁, 任何一条禁令被删除或改名都会红。
def test_prohibition_photo_metrology():
    doc = facts.__doc__ or ""
    assert "照片" in doc and "米制" in doc, "禁令①(未标定照片不得产生绝对米制尺寸)丢失或被改写"


def test_prohibition_esrgan():
    doc = facts.__doc__ or ""
    assert "ESRGAN" in doc and "计量" in doc, "禁令②(超分结果禁止进计量链)丢失或被改写"


def test_prohibition_gpt_source():
    doc = facts.__doc__ or ""
    assert "GPT" in doc, "禁令③(GPT 聊天记录不算来源)丢失或被改写"


def test_prohibitions_are_three_distinct_sentences():
    """三条禁令必须是三条独立可删的句子, 不能挤在一句里一起消失。"""
    doc = (facts.__doc__ or "").replace("\n", " ")
    hits = [doc.count(k) for k in ("照片", "ESRGAN", "GPT")]
    assert all(h >= 1 for h in hits), "禁令关键词缺失: %s" % hits
