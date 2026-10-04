# -*- coding: utf-8 -*-
"""bridge3d.checks_l1 —— L1 判据(纯数据, 无 Blender/渲染依赖)。

三层:
  INV  拓扑不变量(任何 n 孔桥普适): 孔数正整数 / 展开长度一致 /
       跨宽为正 / 支承数 = N_SPAN+1
       (形态约束如对称/单峰不是普适律, 由项目 facts.RELATIONS 自声明)
  MET  度量自洽(阈值必须有依据, 来自 facts 或显式参数): 几何闭合 / 纵坡方向 /
       收分方向 / 券形比 / 拱背净空 / 起拱线低于桥面
  IMP  实现完整性: 契约常量与登记齐备 / SOURCES 覆盖必填项 / 等级合法 /
       假设层不泄漏进来源台账 / 项目自声明关系(RELATIONS)成立

铁律:
  1) 本文件不出现任何项目数值 —— 项目常数只存在于项目 facts;
     判据只验证"facts 自身声明的关系"。唯一字面量是浮点等值容差 EPS 与拓扑量 0/1/2。
  2) 只有 fail 阻塞; 可选事实缺失 → skip(未执行不算通过), 绝不因缺可选事实而 fail。
  3) 判据必须"报告", 不能"崩溃": 前置缺失/非法一律降级 skip, 合法性由 IMP 层报 fail。
"""
from . import derive as _derive
from .schema import (Finding, MissingFactError, is_number, has, get,
                     REQUIRED, REQUIRED_LISTS, GRADES, validate_facts_module)

EPS = 1e-9   # 纯浮点等值容差(实现参数, 非文物尺寸)


# ══════════ 内部防护 ══════════

def _skip(code, msg):
    return [Finding("skip", code, msg)]


def _int_span_or_skip(f, code):
    """N_SPAN 必须是 >=1 的 int 才能做拓扑推导; 否则本判据 skip(INV/IMP 负责 fail)。"""
    n = get(f, "N_SPAN")
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        return None, _skip(code, "N_SPAN 缺失或非法(%r), 未执行; 合法性由 INV_N_SPAN/IMP 报告" % (n,))
    return n, []


def _prereq_ok(f, num_names=(), pos_names=()):
    """MET 前置检查: 缺失 / 非数 / 非正 → 返回 skip 说明; 全齐返回 None。"""
    missing = [n for n in num_names if not has(f, n)]
    nonnum = [n for n in num_names if has(f, n) and not is_number(get(f, n))]
    nonpos = [n for n in pos_names
              if not has(f, n) or not is_number(get(f, n)) or get(f, n) <= 0]
    if missing or nonnum or nonpos:
        return _skip("__prereq__", "缺=%r 非数=%r 非正=%r" % (missing, nonnum, nonpos))
    return None


def _prereq_skip_for(code, f, num_names=(), pos_names=()):
    bad = _prereq_ok(f, num_names, pos_names)
    if bad is None:
        return None
    return [Finding("skip", code,
                    "前置事实缺失/非法(%s), 未执行; 完整性问题由 IMP 层报告" % bad[0].msg)]


# ══════════ INV 拓扑不变量(普适, 不依赖可选事实) ══════════

def inv_n_span(f):
    """孔数是拓扑量: 必须 int 且 >= 1(bool 是 int 子类, 显式排除)。"""
    n = get(f, "N_SPAN")
    if n is None and not has(f, "N_SPAN"):
        return _skip("INV_N_SPAN", "缺 N_SPAN, 未执行; 由 IMP_REQUIRED_MISSING 报告")
    if isinstance(n, bool) or not isinstance(n, int):
        return [Finding("fail", "INV_N_SPAN",
                        "N_SPAN=%r 须为 int(孔数是拓扑量, 不是测量值)" % (n,))]
    if n < 1:
        return [Finding("fail", "INV_N_SPAN", "N_SPAN=%d < 1" % n)]
    return []


def inv_spans_len(f):
    """对称展开后的跨数必须等于 N_SPAN(双字段一致性)。"""
    n, guard = _int_span_or_skip(f, "INV_SPANS_LEN")
    if guard:
        return guard
    try:
        sp = _derive.spans(f)
    except MissingFactError:
        return _skip("INV_SPANS_LEN", "缺 SPAN_DISTINCT, 未执行; 由 IMP_LIST_MISSING 报告")
    if len(sp) != n:
        return [Finding("fail", "INV_SPANS_LEN",
                        "展开跨数 %d != N_SPAN %d (SPAN_DISTINCT 与 N_SPAN 不一致)" % (len(sp), n))]
    return []


def inv_spans_positive(f):
    """每个净跨必须为正(零宽/负宽 = 拓扑无意义)。"""
    try:
        sp = _derive.spans(f)
    except MissingFactError:
        return _skip("INV_SPANS_POS", "缺 SPAN_DISTINCT, 未执行")
    bad = [(i + 1, v) for i, v in enumerate(sp) if not (is_number(v) and v > 0)]
    if bad:
        return [Finding("fail", "INV_SPANS_POS", "存在非正净跨: %r" % (bad,))]
    return []


def inv_supports_len(f):
    """支承递推必须产出 N_SPAN+1 个支承(两端桥台 + N_SPAN-1 内墩)。"""
    n, guard = _int_span_or_skip(f, "INV_SUPPORTS_LEN")
    if guard:
        return guard
    try:
        xs = _derive.pier_x(f)
    except MissingFactError:
        return _skip("INV_SUPPORTS_LEN", "支承递推前置缺失, 未执行; 由 IMP 报告")
    if len(xs) != _derive.support_count(f):
        return [Finding("fail", "INV_SUPPORTS_LEN",
                        "支承数 %d != N_SPAN+1 = %d (递推规则被改坏?)"
                        % (len(xs), _derive.support_count(f)))]
    return []


# ══════════ MET 度量自洽(阈值有依据; 前置缺失 → skip) ══════════

def met_closure(f, tol=None):
    """几何闭合: sum(净跨)+(N_SPAN-1)*PIER_W+2*BRIDGE_ABUT 与 BRIDGE_LEN 之差
    不得超过容差。容差来源优先级: 显式参数 tol > facts.CLOSURE_TOL;
    两者皆无 → skip(阈值必须有依据, 框架绝不默认一个"看起来合理"的数)。"""
    code = "MET_CLOSURE"
    guard = _prereq_skip_for(code, f, pos_names=("BRIDGE_LEN", "PIER_W", "BRIDGE_ABUT"))
    if guard:
        return guard
    t = tol if tol is not None else get(f, "CLOSURE_TOL")
    if t is None:
        return _skip(code, "无闭合容差依据(既无显式参数也无 facts.CLOSURE_TOL), 未执行")
    if not is_number(t) or t <= 0:
        return _skip(code, "闭合容差非法(%r), 未执行; 由 IMP_TOLERANCE 报告" % (t,))
    try:
        computed, target, delta = _derive.geometry_closure(f)
    except MissingFactError as e:
        return _skip(code, "推导所需事实缺失(%s), 未执行" % (e,))
    if abs(delta) > t:
        return [Finding("fail", code,
                        "几何闭合差 %+.4f 超容差 %.4f: 跨和+内墩+桥台=%.4f != 桥长=%.4f "
                        "(拓扑口径: 内墩数=N_SPAN-1)"
                        % (delta, t, computed, target))]
    return []


def met_deck_camber(f):
    """桥面不得两端高中央低(反向纵坡=砌体桥不成立的真错误)。

    2026-10-05 终审 I1 放宽(与 MET_TAPER 同款教训): 原判据写 `顶 > 端`(强制起拱),
    把拱桥构型当普适律。**平桥(顶=端, 无拱起)是合法构型**, 强制严格 `>` 会让它
    在基线就报 fail。真正的物理约束只有"端部不得高于中央"(倒拱), 等高(平桥)
    与起拱(顶>端)都放行。
    """
    code = "MET_DECK_DIR"
    guard = _prereq_skip_for(code, f, num_names=("DECK_Z_TOP", "DECK_Z_END"),
                             pos_names=("BRIDGE_LEN",))
    if guard:
        return guard
    top, end = get(f, "DECK_Z_TOP"), get(f, "DECK_Z_END")
    if not top >= end:
        return [Finding("fail", code,
                        "桥面不得两端高中央低: DECK_Z_TOP %.3f < DECK_Z_END %.3f"
                        % (top, end))]
    return []


def met_taper(f):
    """桥宽方向: 0 < 顶宽 <= 底宽。缺失 → skip。

    2026-10-04 框架化时放宽: 原判据写 `0 < 顶 < 底`(强制收分), 那是把十七孔桥
    (上宽 6.56 / 下宽 14.6)的构型误当普适律。**等宽桥是合法构型**(薄墩联拱石桥
    桥面宽基本不变), 强制收分会让这类桥在基线就报 fail —— 只有"通用框架"这条要求
    才会暴露, E30 自身永远碰不到。
    真正的物理约束只有"顶宽不得大于底宽"(否则是倒悬, 砌体桥不成立);
    等宽(=)与收分(<)都放行。
    """
    code = "MET_TAPER"
    guard = _prereq_skip_for(code, f, num_names=("DECK_UP_W", "DECK_DOWN_W"))
    if guard:
        return guard
    up, down = get(f, "DECK_UP_W"), get(f, "DECK_DOWN_W")
    if not (0 < up <= down):
        return [Finding("fail", code,
                        "桥宽关系非法: 顶宽 %.3f 底宽 %.3f (须 0 < 顶 <= 底; "
                        "等宽合法, 仅倒悬非法)" % (up, down))]
    return []


def met_arch_ratio(f):
    """券形比 f/l 必须落在项目自声明的设计意图 TARGET±TOL 内。
    设计意图是项目声明, 不是框架常数 —— 没声明 → skip。"""
    code = "MET_ARCH_RATIO"
    guard = _prereq_skip_for(code, f,
                             num_names=("ARCH_RATIO", "ARCH_RATIO_TARGET", "ARCH_RATIO_TOL"))
    if guard:
        return guard
    ratio, tgt, t = get(f, "ARCH_RATIO"), get(f, "ARCH_RATIO_TARGET"), get(f, "ARCH_RATIO_TOL")
    if abs(ratio - tgt) > t:
        return [Finding("fail", code,
                        "f/l=%.4f 偏离声明设计意图 %.4f±%.4f" % (ratio, tgt, t))]
    return []


def _openings(f):
    """逐孔 (中心x, 净跨)。前置由调用方保证。"""
    xs = _derive.pier_x(f)
    sp = _derive.spans(f)
    return [((xs[i] + xs[i + 1]) / 2.0, sp[i]) for i in range(min(len(sp), len(xs) - 1))]


def met_ring_fit(f):
    """拱背(拱腹+券圈厚)必须低于桥面 —— 结构自洽, 替代任何无据的净空常数。"""
    code = "MET_RING_FIT"
    guard = _prereq_skip_for(code, f,
                             num_names=("ARCH_RATIO", "RING_T", "DECK_Z_TOP", "DECK_Z_END",
                                        "SPRINGER"),
                             pos_names=("BRIDGE_LEN", "PIER_W", "BRIDGE_ABUT"))
    if guard:
        return guard
    try:
        z = _derive.deck_z(f)
        openings = _openings(f)
    except MissingFactError as e:
        return _skip(code, "推导所需事实缺失(%s), 未执行" % (e,))
    ratio, ring_t, springer = get(f, "ARCH_RATIO"), get(f, "RING_T"), get(f, "SPRINGER")
    bad = []
    for i, (xc, span_w) in enumerate(openings):
        crown = springer + ratio * span_w
        if crown + ring_t > z(xc) + EPS:
            bad.append((i + 1, crown + ring_t, z(xc)))
    if bad:
        return [Finding("fail", code,
                        "拱背穿出桥面(孔号, 拱背标高, 桥面标高): %r" % (bad,))]
    return []


def met_springer(f):
    """起拱线必须低于其孔中心处的桥面。"""
    code = "MET_SPRINGER"
    guard = _prereq_skip_for(code, f, num_names=("SPRINGER", "DECK_Z_TOP", "DECK_Z_END"),
                             pos_names=("BRIDGE_LEN", "PIER_W", "BRIDGE_ABUT"))
    if guard:
        return guard
    try:
        z = _derive.deck_z(f)
        openings = _openings(f)
    except MissingFactError as e:
        return _skip(code, "推导所需事实缺失(%s), 未执行" % (e,))
    springer = get(f, "SPRINGER")
    bad = [(i + 1, z(xc)) for i, (xc, _w) in enumerate(openings) if springer >= z(xc)]
    if bad:
        return [Finding("fail", code,
                        "起拱线 %.3f 高于桥面(孔号, 桥面标高): %r" % (springer, bad))]
    return []


# ══════════ IMP 实现完整性 ══════════

def imp_contract(f):
    """契约结构: 必填常量/序列/登记齐备且类型合法(主体在 schema.validate_facts_module)。"""
    return list(validate_facts_module(f))


def imp_dims(f):
    """存在但非法的尺寸(非正)必须报 —— 生成器消费前最后一道闸。缺失 → skip。"""
    bad = []
    for name in ("BRIDGE_LEN", "PIER_W", "BRIDGE_ABUT"):
        if has(f, name):
            v = get(f, name)
            if not is_number(v) or v <= 0:
                bad.append((name, v))
    if not bad and not all(has(f, n) for n in ("BRIDGE_LEN", "PIER_W", "BRIDGE_ABUT")):
        return _skip("IMP_DIM", "尺寸常量未全部出现, 缺席者由 IMP_REQUIRED_MISSING 报告")
    if bad:
        return [Finding("fail", "IMP_DIM", "尺寸非法(须为正数): %r" % (bad,))]
    return []


def imp_tolerance(f):
    """CLOSURE_TOL 若声明必须合法(正数)—— 坏容差会让闭合判据形同虚设。"""
    if not has(f, "CLOSURE_TOL") or get(f, "CLOSURE_TOL") is None:
        return _skip("IMP_TOLERANCE", "未声明 CLOSURE_TOL(闭合判据将 skip)")
    t = get(f, "CLOSURE_TOL")
    if not is_number(t) or t <= 0:
        return [Finding("fail", "IMP_TOLERANCE",
                        "CLOSURE_TOL=%r 须为正数(容差必须有依据且合法)" % (t,))]
    return []


def imp_sources_cover(f):
    """SOURCES 必须覆盖每个必填常量与必填序列(漏一即 fail)。"""
    if not has(f, "SOURCES"):
        return _skip("IMP_SOURCES_COVER", "缺 SOURCES, 由 IMP_REGS_MISSING 报告")
    keys = set(get(f, "SOURCES").keys())
    missing = sorted(n for n in tuple(REQUIRED) + tuple(REQUIRED_LISTS) if n not in keys)
    if missing:
        return [Finding("fail", "IMP_SOURCES_COVER", "必填项缺来源登记: %r" % (missing,))]
    return []


def imp_grades_legal(f):
    """来源等级必须落在 GRADES 五级内(含"待核"在内的一切等级外写法都非法)。"""
    if not has(f, "SOURCES"):
        return _skip("IMP_GRADES_LEGAL", "缺 SOURCES, 由 IMP_REGS_MISSING 报告")
    bad = []
    for k, v in get(f, "SOURCES").items():
        grade = v[0] if isinstance(v, (tuple, list)) and v else None
        if grade not in GRADES:
            bad.append((k, grade))
    if bad:
        return [Finding("fail", "IMP_GRADES_ILLEGAL",
                        "等级不在五级(%s)内: %r" % ("/".join(GRADES), bad))]
    return []


def imp_assumptions_isolated(f):
    """假设层不泄漏: 声明过的假设参数名不得出现在 SOURCES(假设不参与来源与冻结)。"""
    if not has(f, "ASSUMPTION_NAMES"):
        return _skip("IMP_ASSUMPTION_ISOLATED",
                     "项目未声明 ASSUMPTION_NAMES, 无法核对假设层隔离")
    names = list(get(f, "ASSUMPTION_NAMES"))
    if not has(f, "SOURCES"):
        return _skip("IMP_ASSUMPTION_ISOLATED", "缺 SOURCES, 由 IMP_REGS_MISSING 报告")
    leak = sorted(set(names) & set(get(f, "SOURCES").keys()))
    if leak:
        return [Finding("fail", "IMP_ASSUMPTION_LEAK",
                        "假设层参数混进来源台账: %r" % (leak,))]
    return []


def imp_relations(f):
    """项目自声明的关系型不变量: 判据只验证声明的约束。
    关系返回 False → fail; 抛 MissingFactError → skip; 抛其它异常 → fail(声明已坏)。"""
    if not has(f, "RELATIONS"):
        return _skip("IMP_RELATIONS_ABSENT", "项目未声明 RELATIONS(合法)")
    rel = get(f, "RELATIONS")
    if not hasattr(rel, "items"):
        return _skip("IMP_RELATIONS_ABSENT", "RELATIONS 形状非法, 由 IMP_RELATIONS_SHAPE 报告")
    out = []
    for name, fn in rel.items():
        code = "REL_%s" % name
        if not callable(fn):
            out.append(Finding("fail", code, "关系 %r 不是 callable" % (name,)))
            continue
        try:
            ok = fn(f)
        except MissingFactError as e:
            out.append(Finding("skip", code, "关系所需事实缺失(%s), 未执行" % (e,)))
            continue
        except Exception as e:   # noqa: BLE001 —— 声明坏掉必须可见, 不得静默
            out.append(Finding("fail", code, "关系抛出异常(声明本身坏了): %r" % (e,)))
            continue
        if not isinstance(ok, bool):
            out.append(Finding("fail", code, "关系返回值须为 bool, 实为 %r" % (ok,)))
        elif not ok:
            out.append(Finding("fail", code, "项目自声明关系不成立"))
    return out


# ══════════ 汇总 ══════════

INV_CHECKS = (inv_n_span, inv_spans_len, inv_spans_positive, inv_supports_len)
MET_CHECKS = (met_closure, met_deck_camber, met_taper, met_arch_ratio,
              met_ring_fit, met_springer)
IMP_CHECKS = (imp_contract, imp_dims, imp_tolerance, imp_sources_cover,
              imp_grades_legal, imp_assumptions_isolated, imp_relations)


def default_checks():
    """默认判据集(INV+MET+IMP)。项目可用 run_l1(f, checks=...) 自选子集。"""
    return list(INV_CHECKS) + list(MET_CHECKS) + list(IMP_CHECKS)


def run_l1(f, closure_tol=None, checks=None):
    """跑 L1 判据, 返回 list[Finding]。closure_tol 显式覆盖闭合容差。"""
    out = []
    for chk in (checks if checks is not None else default_checks()):
        if chk is met_closure and closure_tol is not None:
            out.extend(met_closure(f, tol=closure_tol))
        else:
            out.extend(chk(f))
    return out
