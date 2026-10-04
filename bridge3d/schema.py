# -*- coding: utf-8 -*-
"""bridge3d.schema —— facts 模块结构契约(duck typing + 显式检查, 不强制继承)。

一个古建三维项目的"事实层"(facts)是一个普通模块/Namespace, 用常量声明事实。
本模块只定义 facts 必须满足的形状(名字即契约), 项目侧零继承、零样板类。

契约分层:
  REQUIRED       必填标量常量(缺/类型错 → fail)
  REQUIRED_LISTS 必填序列(对称展开规则见 derive.spans)
  REQUIRED_REGS  必填登记(SOURCES 来源台账 / RESEARCH_DONE 研究旗标)
  OPTIONAL       已知可选条目(缺省 → 相关判据 skip; skip=未执行, 不算通过也不阻塞)
  GRADES         来源五级: 测绘 > 档案 > 官方 > 图像推导 > 工作值
  RELATIONS      项目自声明的关系型不变量 {名称: callable(f)->bool};
                 判据只验证"项目自己声明的约束", 框架不预设任何具体形态。

设计铁律(为何存在本包):
  1) 判据源码不出现任何项目数值 —— 项目常数只存在于项目 facts;
     判据只验证"facts 自身声明的关系"是否成立。
  2) 只有 fail 阻塞; warn 不阻塞; skip=未执行, 不算通过。
  3) 每条判据必须配"故意破坏"用例且破坏被抓(见 negative_control),
     否则判据恒真, 与没测一样。

判据输出统一为 Finding(level, code, msg)。
"""
from collections import namedtuple

# ── 契约: 必填常量(名字是契约的一部分) ──
REQUIRED = ("BRIDGE_LEN", "N_SPAN", "SPRINGER", "PIER_W", "BRIDGE_ABUT")

# ── 契约: 必填序列(完整净跨, 对称展开为 N_SPAN 个, 规则见 derive.spans) ──
REQUIRED_LISTS = ("SPAN_DISTINCT",)

# ── 契约: 必填登记 ──
REQUIRED_REGS = ("SOURCES", "RESEARCH_DONE")

# ── 允许缺省的条目(缺省时相关判据走 skip 语义, 不得 fail) ──
OPTIONAL = (
    "ARCH_RATIO",          # 券的矢高/跨高比(f/l); 缺省 → 券形类判据 skip
    "RING_T",              # 券圈厚; 缺省 → 拱背净空判据 skip
    "DECK_UP_W", "DECK_DOWN_W",   # 桥面顶/底宽; 缺省 → 收分判据 skip
    "DECK_Z_TOP", "DECK_Z_END",   # 桥面中央/端部标高; 缺省 → 纵坡类判据 skip
    "CLOSURE_TOL",         # 几何闭合容差(带单位, 须有依据); 缺省 → 闭合判据 skip
    "ARCH_RATIO_TARGET", "ARCH_RATIO_TOL",  # 券形设计意图与容差; 缺省 → 券形比判据 skip
    "ASSUMPTION_NAMES",    # 假设层参数名清单; 缺省 → 假设层隔离判据 skip
    "RELATIONS",           # 关系型不变量表; 缺省 → 视为项目未声明额外约束
)

# ── 来源五级(优先级从高到低) ──
GRADES = ("测绘", "档案", "官方", "图像推导", "工作值")

# ── 判据等级: 只有 fail 阻塞; skip=未执行不算通过 ──
LEVELS = ("fail", "warn", "skip")

Finding = namedtuple("Finding", ["level", "code", "msg"])


class MissingFactError(AttributeError):
    """判据所需事实缺失。MET 层捕获后降级为 skip(缺可选事实绝不得 fail)。"""


def is_number(v):
    """实数(排除 bool —— bool 是 int 的子类, 必须显式排除)。"""
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def has(f, name):
    return hasattr(f, name)


def get(f, name, default=None):
    return getattr(f, name, default)


def fail_codes(findings):
    return sorted(set(fd.code for fd in findings if fd.level == "fail"))


def warn_codes(findings):
    return sorted(set(fd.code for fd in findings if fd.level == "warn"))


def skip_codes(findings):
    return sorted(set(fd.code for fd in findings if fd.level == "skip"))


def has_fail(findings):
    return any(fd.level == "fail" for fd in findings)


def summarize(findings):
    """人读摘要: 计数 + 全部 fail/warn/skip 逐条。"""
    n_fail = sum(1 for fd in findings if fd.level == "fail")
    n_warn = sum(1 for fd in findings if fd.level == "warn")
    n_skip = sum(1 for fd in findings if fd.level == "skip")
    lines = ["fail=%d warn=%d skip=%d" % (n_fail, n_warn, n_skip)]
    for fd in findings:
        if fd.level in ("fail", "warn", "skip"):
            lines.append("[%s] %s: %s" % (fd.level, fd.code, fd.msg))
    return "\n".join(lines)


def _num_field_findings(f, name, missing_code, type_code, type_hint):
    if not has(f, name):
        return [Finding("fail", missing_code, "缺必填常量 %s" % name)]
    v = get(f, name)
    if not is_number(v):
        return [Finding("fail", type_code,
                        "%s 类型非法: %r (须为实数%s)" % (name, v, type_hint))]
    return []


def validate_facts_module(f):
    """结构校验: 契约常量/序列/登记/关系表齐备且类型合法。返回 list[Finding]。

    本函数是 IMP(实现完整性)层的主体, 由 checks_l1 纳入 L1 输出。
    每条违规一个 fail; 结构健全返回空表(RELATIONS 未声明 → skip, 属合法选择)。
    """
    out = []
    for name in REQUIRED:
        out.extend(_num_field_findings(f, name, "IMP_REQUIRED_MISSING",
                                       "IMP_REQUIRED_TYPE", ""))
    n_span = get(f, "N_SPAN")
    if is_number(n_span) and not isinstance(n_span, int):
        out.append(Finding("fail", "IMP_REQUIRED_TYPE",
                           "N_SPAN=%r 须为 int(孔数是拓扑量, 不是测量值)" % (n_span,)))
    for name in REQUIRED_LISTS:
        if not has(f, name):
            out.append(Finding("fail", "IMP_LIST_MISSING", "缺必填序列 %s" % name))
            continue
        seq = get(f, name)
        if not isinstance(seq, (list, tuple)) or len(seq) == 0:
            out.append(Finding("fail", "IMP_LIST_SHAPE",
                               "%s 须为非空 list/tuple, 实为 %r" % (name, seq)))
            continue
        bad = [v for v in seq if not (is_number(v) and v > 0)]
        if bad:
            out.append(Finding("fail", "IMP_LIST_SHAPE",
                               "%s 含非法元素(须为正数): %r" % (name, bad)))
    for name in REQUIRED_REGS:
        if not has(f, name):
            out.append(Finding("fail", "IMP_REGS_MISSING", "缺必填登记 %s" % name))
    src = get(f, "SOURCES")
    if src is not None and not hasattr(src, "items"):
        out.append(Finding("fail", "IMP_REGS_SHAPE",
                           "SOURCES 须为 dict(名称 → (等级, 出处说明))"))
    flag = get(f, "RESEARCH_DONE")
    if flag is not None and not isinstance(flag, bool):
        out.append(Finding("fail", "IMP_REGS_SHAPE",
                           "RESEARCH_DONE=%r 须为 bool(研究轮旗标)" % (flag,)))
    if has(f, "RELATIONS"):
        rel = get(f, "RELATIONS")
        if not hasattr(rel, "items"):
            out.append(Finding("fail", "IMP_RELATIONS_SHAPE",
                               "RELATIONS 须为 dict(名称 → callable(f)->bool)"))
        else:
            for rname, fn in rel.items():
                if not callable(fn):
                    out.append(Finding("fail", "IMP_RELATIONS_SHAPE",
                                       "RELATIONS[%r] 不是 callable" % (rname,)))
    else:
        out.append(Finding("skip", "IMP_RELATIONS_ABSENT",
                           "项目未声明 RELATIONS(无额外关系约束, 合法)"))
    for name in ("CLOSURE_TOL", "ARCH_RATIO_TARGET", "ARCH_RATIO_TOL",
                 "ARCH_RATIO", "RING_T", "DECK_UP_W", "DECK_DOWN_W",
                 "DECK_Z_TOP", "DECK_Z_END"):
        if has(f, name) and get(f, name) is not None and not is_number(get(f, name)):
            out.append(Finding("fail", "IMP_OPTIONAL_TYPE",
                               "可选条目 %s 存在但类型非法: %r" % (name, get(f, name))))
    if has(f, "ASSUMPTION_NAMES"):
        an = get(f, "ASSUMPTION_NAMES")
        if not isinstance(an, (list, tuple)) or any(not isinstance(x, str) for x in an):
            out.append(Finding("fail", "IMP_OPTIONAL_TYPE",
                               "ASSUMPTION_NAMES 须为字符串序列, 实为 %r" % (an,)))
    return out
