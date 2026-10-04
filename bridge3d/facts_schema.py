# -*- coding: utf-8 -*-
"""bridge3d.facts_schema —— 事实层校验器(从 E30 tests/test_facts.py 泛化)。

项目 facts 模块除结构契约(见 schema)外, 还必须通过本模块的内容校验:

  1) SOURCES 必须覆盖每个 REQUIRED 常量与 REQUIRED_LISTS 序列(漏一即 fail);
  2) 登记等级必须在 GRADES 五级内;
  3) [工作值] 必须写明出处状态(为什么没有正式来源);
  4) 三条禁令必须写进项目 facts 的模块 docstring(逐条可删、逐条可证伪):
       ① 未标定照片不得产生绝对米制尺寸;
       ② 超分(如 ESRGAN)结果禁止进入计量链;
       ③ GPT 聊天记录不算来源。

判据语义: 只有 fail 阻塞; warn 不阻塞(RESEARCH_DONE=False 属研究进行中);
skip=未执行, 不算通过。

每条校验器本身必须可证伪: tests/bridge3d/test_facts_schema.py 对每条规则
各有"违反 → fail"的负控用例; 恒真审计同样覆盖本模块(见 negative_control)。
"""
import re

from .schema import Finding, has, get, REQUIRED, REQUIRED_LISTS, GRADES

WORKING = "工作值"

# 说明文字出现这些词 = 作者自认没有正式来源 → 等级必须是 [工作值]
_SELF_NO_SOURCE = ("无文献", "现脚本", "沿用", "无出处", "GPT设计", "提案", "待核", "工作值")

# 否定语境里的年份/机构不算可追溯出处
_NEGATION = ("未检回", "未公开", "查无", "无来源", "不可", "未找到", "未注明")

# [官方] 等级正面出处的机构词面(与年份同时出现才认定)
_INSTITUTION = ("北京", "公园管理", "日报", "中心", "局", "政府", "院", "园",
                "博物馆", "文物", "研究", "管理處", "管理处")

_YEAR_RE = re.compile(r"(19|20)\d{2}")


def _sources(f):
    """返回 SOURCES dict; 缺失返回 None(调用方自行 skip/fail)。"""
    if not has(f, "SOURCES"):
        return None
    src = get(f, "SOURCES")
    if not hasattr(src, "items"):
        return None
    return dict(src)


def _well_formed_entries(src):
    """只产出形状合法的 (name, grade, note); 形状问题是 check_source_shape 的轴。"""
    for name, v in src.items():
        if isinstance(v, (tuple, list)) and len(v) == 2:
            grade, note = v
            yield name, grade, note


def check_sources_complete(f):
    """SOURCES 必须覆盖每个 REQUIRED 常量与 REQUIRED_LISTS 序列。"""
    src = _sources(f)
    if src is None:
        return [Finding("fail", "FS_SOURCES_MISSING",
                        "缺 SOURCES 台账, 无法核对来源完备性")]
    missing = sorted(n for n in tuple(REQUIRED) + tuple(REQUIRED_LISTS) if n not in src)
    if missing:
        return [Finding("fail", "FS_SOURCES_MISSING", "缺来源登记: %r" % (missing,))]
    return []


def check_source_shape(f):
    """每条登记必须是 (等级, 说明) 二元组, 说明非空。"""
    src = _sources(f)
    if src is None:
        return [Finding("skip", "FS_SOURCE_SHAPE", "缺 SOURCES 台账, 未执行")]
    bad = []
    for name, v in src.items():
        if not (isinstance(v, (tuple, list)) and len(v) == 2):
            bad.append((name, v))
            continue
        grade, note = v
        if not isinstance(grade, str) or not isinstance(note, str) or not note.strip():
            bad.append((name, v))
    if bad:
        return [Finding("fail", "FS_SOURCE_SHAPE",
                        "登记须为 (等级, 非空说明): %r" % (bad,))]
    return []


def check_grades_legal(f):
    """等级必须落在 GRADES 五级内(任何等级外写法, 含[待核], 都非法)。"""
    src = _sources(f)
    if src is None:
        return [Finding("skip", "FS_GRADE_ILLEGAL", "缺 SOURCES 台账, 未执行")]
    bad = [(n, g) for n, g, _note in _well_formed_entries(src) if g not in GRADES]
    if bad:
        return [Finding("fail", "FS_GRADE_ILLEGAL",
                        "等级不在五级(%s)内: %r" % ("/".join(GRADES), bad))]
    return []


def check_stale_keys(f):
    """SOURCES 不得残留指向已改名/已删除常量的键。
    必填项残留 = fail(来源台账与事实脱节); 可选条目残留 = warn(记账漂移,
    不得阻塞 —— 缺可选事实必须走 skip 语义)。"""
    src = _sources(f)
    if src is None:
        return [Finding("skip", "FS_STALE_KEY", "缺 SOURCES 台账, 未执行")]
    req_keys = tuple(REQUIRED) + tuple(REQUIRED_LISTS)
    stale_hard = sorted(k for k in src if not hasattr(f, k) and k in req_keys)
    stale_soft = sorted(k for k in src if not hasattr(f, k) and k not in req_keys)
    out = []
    if stale_hard:
        out.append(Finding("fail", "FS_STALE_KEY",
                           "SOURCES 指向不存在的必填常量(改名后未清理?): %r" % (stale_hard,)))
    if stale_soft:
        out.append(Finding("warn", "FS_STALE_KEY_OPTIONAL",
                           "SOURCES 指向不存在的可选条目(记账漂移): %r" % (stale_soft,)))
    return out


def check_working_values_documented(f):
    """[工作值] 允许存在, 但每条必须写明出处状态(为什么没有正式来源)。"""
    src = _sources(f)
    if src is None:
        return [Finding("skip", "FS_WORKING_UNDOCUMENTED", "缺 SOURCES 台账, 未执行")]
    bad = []
    for name, grade, note in _well_formed_entries(src):
        if grade == WORKING and not any(k in note for k in _SELF_NO_SOURCE):
            bad.append((name, note))
    if bad:
        return [Finding("fail", "FS_WORKING_UNDOCUMENTED",
                        "%s 必须写明出处状态(%s 之一): %r"
                        % (WORKING, "/".join(_SELF_NO_SOURCE), bad))]
    return []


def check_no_grade_inflation(f):
    """等级不得高于其证据说明所能支撑的上限:
    说明自认无正式来源却标了更高等级 = 等级造假。"""
    src = _sources(f)
    if src is None:
        return [Finding("skip", "FS_GRADE_INFLATED", "缺 SOURCES 台账, 未执行")]
    inflated = []
    for name, grade, note in _well_formed_entries(src):
        if grade in GRADES and grade != WORKING and any(k in note for k in _SELF_NO_SOURCE):
            inflated.append((name, grade, note))
    if inflated:
        return [Finding("fail", "FS_GRADE_INFLATED",
                        "等级造假: 说明自认无正式来源却标了更高等级: %r" % (inflated,))]
    return []


def check_official_citation(f):
    """[官方] 等级必须在说明里给出正面可追溯出处: URL, 或 机构+年份 且不在否定语境。
    (E30 负控实证: 只查"有年份"会漏网 —— 否定语境"未检回"里的年份不算出处。)"""
    src = _sources(f)
    if src is None:
        return [Finding("skip", "FS_OFFICIAL_UNCITED", "缺 SOURCES 台账, 未执行")]
    bad = []
    for name, grade, note in _well_formed_entries(src):
        if grade != "官方":
            continue
        cited = [seg for seg in re.split(r"[;；,，]", note) if seg.strip()]
        positive = False
        for seg in cited:
            if "http" in seg:
                positive = True
                break
            if any(neg in seg for neg in _NEGATION):
                continue
            if _YEAR_RE.search(seg) and any(inst in seg for inst in _INSTITUTION):
                positive = True
                break
        if not positive:
            bad.append((name, note))
    if bad:
        return [Finding("fail", "FS_OFFICIAL_UNCITED",
                        "[官方] 缺正面可追溯出处(URL 或 机构+年份, 非否定语境): %r" % (bad,))]
    return []


def check_research_flag(f):
    """研究旗标: 必须是 bool; False → warn(研究进行中, 不阻塞但必须列出)。"""
    if not has(f, "RESEARCH_DONE"):
        return [Finding("fail", "FS_RESEARCH_FLAG", "缺 RESEARCH_DONE 登记旗标")]
    flag = get(f, "RESEARCH_DONE")
    if not isinstance(flag, bool):
        return [Finding("fail", "FS_RESEARCH_FLAG",
                        "RESEARCH_DONE=%r 须为 bool" % (flag,))]
    if flag is False:
        return [Finding("warn", "FS_RESEARCH_PENDING",
                        "RESEARCH_DONE=False: 研究轮未完成, 不阻塞但交付前必须翻 True")]
    return []


def check_assumptions_not_registered(f):
    """假设层不泄漏: 声明过的假设参数名不得进入 SOURCES(假设不参与来源与冻结)。"""
    if not has(f, "ASSUMPTION_NAMES"):
        return [Finding("skip", "FS_ASSUMPTION_ISOLATED",
                        "项目未声明 ASSUMPTION_NAMES, 无法核对")]
    names = list(get(f, "ASSUMPTION_NAMES"))
    src = _sources(f)
    if src is None:
        return [Finding("skip", "FS_ASSUMPTION_ISOLATED", "缺 SOURCES 台账, 未执行")]
    leak = sorted(set(names) & set(src.keys()))
    if leak:
        return [Finding("fail", "FS_ASSUMPTION_LEAK", "假设层参数混进 SOURCES: %r" % (leak,))]
    return []


def check_docstring_bans(f):
    """三条禁令必须逐条写进项目 facts 的模块 docstring —— 逐条锁, 删任一条都红。
    (E30 审查探针实证: 只锁一条时, 其余禁令整句删除仍全绿 = 恒真。)"""
    doc = getattr(f, "__doc__", None) or ""
    out = []
    if not ("照片" in doc and "米制" in doc):
        out.append(Finding("fail", "FS_BAN_PHOTO_METRIC",
                           "禁令①(未标定照片不得产生绝对米制尺寸)丢失或被改写"))
    if not (("超分" in doc or "ESRGAN" in doc) and "计量" in doc):
        out.append(Finding("fail", "FS_BAN_SUPERRES",
                           "禁令②(超分/ESRGAN 结果禁入计量链)丢失或被改写"))
    if "GPT" not in doc:
        out.append(Finding("fail", "FS_BAN_GPT_SOURCE",
                           "禁令③(GPT 聊天记录不算来源)丢失或被改写"))
    return out


FACT_CHECKS = (check_sources_complete, check_source_shape, check_grades_legal,
               check_stale_keys, check_working_values_documented,
               check_no_grade_inflation, check_official_citation,
               check_research_flag, check_assumptions_not_registered,
               check_docstring_bans)


def run_fact_checks(f):
    """跑全部事实层校验, 返回 list[Finding]。"""
    out = []
    for chk in FACT_CHECKS:
        out.extend(chk(f))
    return out
