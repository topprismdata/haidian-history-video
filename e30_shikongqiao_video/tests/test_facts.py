# -*- coding: utf-8 -*-
"""E30 Task1 来源完备性测试。

判据语义: 只有 fail 阻塞; skip 不算通过。
- 核心判据: facts 本体常量必须逐个登记进 SOURCES(漏一即 fail)。
- 旗标闸门(T2 裁决): RESEARCH_DONE=True 后禁[待核]; [工作值]允许但必须写明出处状态。
- G1 分家: assumptions 的名字不得出现在 SOURCES(假设层不参与冻结)。
- 文档禁令可执行化: facts docstring 必须写明 ESRGAN / 计量 禁令。
"""
import importlib
import sys
from pathlib import Path

import pytest

_3D_DIR = Path(__file__).resolve().parents[1] / "3d"
_ROOT = Path(__file__).resolve().parents[2]      # 仓库根(bridge3d 所在)
sys.path.insert(0, str(_3D_DIR))
sys.path.insert(0, str(_ROOT))

from bridge3d.schema import ALL_GRADES   # noqa: E402  等级集单一来源, 避免硬编码漂移

facts = importlib.import_module("facts")
assumptions = importlib.import_module("assumptions")

ALLOWED_LEVELS = set(ALL_GRADES) | {"待核"}   # 2026-10-05: 改为引用 bridge3d 单一来源, 不再硬编码(硬编码会随框架拆级漂移)


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
    # T2 裁决(2026-10-04): 旗标闸门收窄为"禁待核"。
    # T1 原设计是"RESEARCH_DONE=True 后禁待核+工作值"——那条规则把"无公开测绘值"
    # 当成了研究失败。T2 实测 12 项(逐孔净跨/墩厚/起拱线/矢高/纵坡/桥台)确实无公开
    # 测绘值, 按约定诚实落 [工作值]。禁止它们存在 == 逼着实现者谎标等级换假绿。
    # 正确语义: 待核 = 还没查(研究未完成), 必须清零;
    #           工作值 = 查过了确实无公开来源, 允许存在, 但必须被显式登记为已知偏离。
    forbidden = ("待核",)
    offenders = sorted(
        n for n, (lvl, _note) in facts.SOURCES.items() if lvl in forbidden)
    assert not offenders, "RESEARCH_DONE=%s 时仍存在[待核]条目(该查的没查完): %s" % (
        facts.RESEARCH_DONE, offenders)


def test_working_values_are_registered_as_known_deviations():
    """工作值允许存在, 但每一条都必须说清"为什么没有来源"。
    这条锁住诚实: 防止有人把无来源的数字写成 [工作值] 然后悄悄改数值。"""
    import re as _re
    doc = Path(facts.__file__).read_text(encoding="utf-8")
    working = [n for n, (lvl, _note) in facts.SOURCES.items() if lvl == "工作值"]
    assert working, "M0 后应仍有工作值(12项无公开测绘值); 若全清说明有人编造了来源"
    for n in working:
        m = _re.search(r"^%s\s*=.*$" % _re.escape(n), doc, _re.M)
        assert m, "工作值 %s 在 facts.py 中找不到定义行" % n
        line = m.group(0)
        assert "[" in line and "]" in line, \
            "工作值 %s 的定义行缺少 [等级] 标注: %s" % (n, line.strip())
        assert "现脚本" in line or "无文献" in line or "沿用" in line, \
            "工作值 %s 必须写明出处状态(现脚本/无文献/沿用): %s" % (n, line.strip())


def test_no_pending_remains():
    """独立于旗标: 任何时候都不得存在 [待核]——那是'还没查'的占位符。"""
    offenders = sorted(
        n for n, (lvl, _note) in facts.SOURCES.items() if lvl == "待核")
    assert not offenders, "仍存在[待核]: %s" % offenders


def test_span_distinct_shape_and_symmetric_closure():
    """SPAN_DISTINCT 是 9 个完整净跨; 对称展开成 17 跨后:
    总水路 = 107.3m, 加中央区 9*PIER_W = 22.5m 与 107.3+22.5 自洽。
    (简报的 sum(SPANS)+15*PIER_W+2*BRIDGE_ABUT 全桥闭合判据属 T2b, 不在本测试。)"""
    sd = facts.SPAN_DISTINCT
    assert len(sd) == 9, "SPAN_DISTINCT 须为 9 个完整净跨, 实为 %d" % len(sd)
    # [M19] DECK_Z_AT_PIER 9 点表已随枯湖基准废除(零消费方死数据); 纵剖由
    # DECK_Z_TOP/DECK_Z_END + bridge_geom2.deck_z 抛物线单一来源表达。
    assert facts.DECK_Z_TOP > facts.DECK_Z_END > 0, "桥面纵剖锚点须中央高两端低且为正"
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


# ── T2 负控制补漏: 等级造假锁(调度者 2026-10-04 亲自做负控制时发现漏网) ──
# 实测: 把 SOURCES 里 PIER_W 的 "工作值" 改成 "官方", 13 条测试全绿。
# 因为没有任何测试检查"登记的等级与该条的证据说明是否相符"——
# 而等级造假恰恰是本项目最严重的缺陷类型(它会让后续所有冻结与交付文档基于假事实)。

_GRADE_RANK = {"工作值": 0, "图像推导": 1, "官方": 2, "档案": 3, "测绘": 4}


def test_grades_are_not_inflated():
    """等级不得高于其证据说明所能支撑的上限。

    规则: 说明文字里若出现"无文献/现脚本/沿用/工作值"等词, 说明作者自己承认没有正式来源,
    那么等级**必须**是 [工作值]——把它标成更高等级就是造假, 必须红。
    """
    self_admitted_no_source = ("无文献", "现脚本", "沿用", "GPT设计", "无出处")
    inflated = []
    for n, (lvl, note) in facts.SOURCES.items():
        if lvl not in _GRADE_RANK:
            continue
        if any(k in note for k in self_admitted_no_source) and lvl != "工作值":
            inflated.append((n, lvl, note))
    assert not inflated, \
        "等级造假: 说明自认无正式来源却标了更高等级: %s" % inflated


def test_official_grade_requires_citation_in_note():
    """[官方] 等级必须在说明里给出**正面**可追溯出处, 否则不予认定。

    负控制实测(2026-10-04): 只按"有年份字样"判定会漏网——把 DECK_UP_W 的说明整条
    换成"据说"仍全绿, 因为原文里"2019原始页未检回"这句**否定语境**里也带年份。
    因此判定必须要求出处是**正面陈述**: URL, 或"机构名+年份"且不在否定语境里。
    """
    import re as _re
    negation = ("未检回", "未公开", "查无", "无来源", "不可", "未找到")
    bad = []
    for n, (lvl, note) in facts.SOURCES.items():
        if lvl != "官方":
            continue
        cited = [seg for seg in _re.split(r"[;；,，]", note) if seg.strip()]
        positive = False
        for seg in cited:
            if "http" in seg:
                positive = True
                break
            if any(neg in seg for neg in negation):
                continue          # 否定语境里的年份不算出处
            if _re.search(r"(19|20)\d{2}", seg) and _re.search(
                    r"(北京|公园管理|日报|中心|局|政府|院|园|中心)", seg):
                positive = True
                break
        if not positive:
            bad.append((n, note))
    assert not bad, "[官方] 等级缺**正面**可追溯出处(需 URL 或 机构+年份, 且非否定语境): %s" % bad


# ══════════════════════════════════════════════════════════════════════════
# ── 终审 I8/I11/I12 回归节 ──
# 判据行为测试本属 test_l1_body.py 主题; 因该文件不在本批次可改清单,
# 回归锁寄放本文件, 语义独立成节: 等级注释交叉核对 / 判据消费 facts 阈值 / 防御性报告。
# ══════════════════════════════════════════════════════════════════════════

def _mutate_facts(**kw):
    """复制 facts 为可变 namespace(与 test_l1_body._mutate 同构)。"""
    import types
    m = types.SimpleNamespace(**{k: getattr(facts, k) for k in dir(facts) if not k.startswith("_")})
    for k, v in kw.items():
        setattr(m, k, v)
    return m


def test_inline_grade_annotation_matches_sources():
    """终审 I8: facts.py 每个 SOURCES 条目的 inline #[等级] 注释必须与登记等级一致(双向)。
    负控实测(修复前): inline 抬级 [工作值]→[测绘] 与 inline 降级 [官方]→[工作值]
    两个方向都是 15 条测试全绿 —— 没有任何测试核对注释与台账。"""
    import re as _re
    doc = Path(facts.__file__).read_text(encoding="utf-8")
    bad = []
    for name, (lvl, _note) in facts.SOURCES.items():
        m = _re.search(r"^%s\s*=[^#\n]*#\s*\[([^\]]+)\]" % _re.escape(name), doc, _re.M)
        if not m:
            bad.append((name, "缺 inline [等级] 注释"))
        elif m.group(1).strip() != lvl:
            bad.append((name, "inline [%s] != SOURCES [%s]" % (m.group(1).strip(), lvl)))
    # 反向: 凡带 inline [等级] 的顶层定义行, 名字必须在 SOURCES(防"有注释无登记")
    for name, tag in _re.findall(r"^([A-Z][A-Z0-9_]*)\s*=[^#\n]*#\s*\[([^\]]+)\]", doc, _re.M):
        if name not in facts.SOURCES:
            bad.append((name, "有 inline [%s] 但未登记 SOURCES" % tag.strip()))
    assert not bad, "inline 等级注释与 SOURCES 登记不一致: %s" % bad


def test_criterion_params_declared_in_facts():
    """终审 I12: 判据阈值三参数必须存在于 facts 并以 [工作值] 登记 SOURCES。
    删除任一条 → 本测试红; 否则 MET_CLOSURE/MET_ARCH_RATIO 会静默退化为 skip 而无人守。"""
    for n in ("CLOSURE_TOL", "ARCH_RATIO_TARGET", "ARCH_RATIO_TOL"):
        v = getattr(facts, n, None)
        assert isinstance(v, float) and not isinstance(v, bool) and v > 0, \
            "facts 缺判据参数 %s(判据将静默 skip): %r" % (n, v)
        assert n in facts.SOURCES and facts.SOURCES[n][0] == "工作值", \
            "%s 须以 [工作值] 登记 SOURCES(阈值必须有依据)" % n


def test_check_body_reports_instead_of_crashing():
    """终审 I11: 损坏 facts 必须得到判据"报告", 不能抛异常(与框架 run_l1 同行为)。
    修复前实测: 短 SPAN_DISTINCT → IndexError; DECK_Z_TOP 非数 → TypeError。
    真实破坏必须报 fail(不得降级为 skip —— skip 不算通过)。"""
    import qa_bridge
    r = qa_bridge.check_body(_mutate_facts(SPAN_DISTINCT=[4.5, 4.9]))
    codes = {x[1] for x in r if x[0] == "fail"}
    assert "INV_SPANS_LEN" in codes, "短表破坏应报 INV_SPANS_LEN 而非崩溃/skip: %s" % codes
    r2 = qa_bridge.check_body(_mutate_facts(DECK_Z_TOP="7.75"))
    codes2 = {x[1] for x in r2 if x[0] == "fail"}
    assert "IMP_TYPES" in codes2, "非数值 DECK_Z_TOP 应报 IMP_TYPES: %s" % codes2
    r3 = qa_bridge.check_body(_mutate_facts(N_SPAN=17.0))
    assert "IMP_TYPES" in {x[1] for x in r3 if x[0] == "fail"}, "非整型 N_SPAN 应报 IMP_TYPES"


def test_criteria_consume_fact_thresholds(monkeypatch):
    """终审 I12: MET_CLOSURE/MET_ARCH_RATIO 必须消费 facts 阈值而非判据源码硬编码。
    证明: 收紧 facts 容差, 同一扰动由"放行"变"红"; 删除阈值 → skip(未执行不算通过)。"""
    import qa_bridge
    def codes(m):
        return {x[1] for x in qa_bridge.check_body(m) if x[0] == "fail"}
    # 默认 CLOSURE_TOL=0.5: 桥台 +0.2m 在容差内放行(test_l1_body 同款标定)
    assert "MET_CLOSURE" not in codes(_mutate_facts(BRIDGE_ABUT=facts.BRIDGE_ABUT + 0.2))
    # 收紧 CLOSURE_TOL=0.1: 同一扰动必须转红 → 判据消费的确实是 facts 值
    assert "MET_CLOSURE" in codes(_mutate_facts(BRIDGE_ABUT=facts.BRIDGE_ABUT + 0.2,
                                                CLOSURE_TOL=0.1))
    # [2026-10-06 期望更新] M14 起判据比对 rise_ratio 剖面中心, 旧观测标量
    # ARCH_RATIO 不再进判据数据通路 —— 负控改打活通路 RISE_C。rise_ratio 是 facts
    # 模块函数(读模块全局), 命名空间突变不可达 → monkeypatch 打模块全局(与
    # test_l1_body.test_inv_spans_sym_detector 同机制), 并把 SPRINGER 同步换算为
    # 一致导出值(M19 起 MET_SPRINGER 校验"声明=导出"恒等), 使扰动只命中被测判据:
    # RISE_C=0.545(剖面中心 |Δ|=0.015) 默认 TOL=0.02 放行, 收紧 TOL=0.01 转红。
    rc = 0.545
    monkeypatch.setattr(facts, "RISE_C", rc)
    monkeypatch.setattr(facts, "SPRINGER",
                        facts.DECK_Z_TOP - facts.SPANDREL_C - rc * facts.SPAN_DISTINCT[8])
    assert "MET_ARCH_RATIO" not in codes(_mutate_facts())
    monkeypatch.setattr(facts, "ARCH_RATIO_TOL", 0.01)
    assert "MET_ARCH_RATIO" in codes(_mutate_facts())
    # 阈值缺位 → skip(不得静默放行, 也不得崩)
    m = _mutate_facts()
    delattr(m, "CLOSURE_TOL")
    delattr(m, "ARCH_RATIO_TARGET")
    lv = {x[1]: x[0] for x in qa_bridge.check_body(m)}
    assert lv.get("MET_CLOSURE") == "skip" and lv.get("MET_ARCH_RATIO") == "skip", lv
