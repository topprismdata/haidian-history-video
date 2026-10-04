# -*- coding: utf-8 -*-
"""bridge3d.negative_control —— 负控制基础设施(事实层与判据层通用)。

铁律: 每条判据必须有"故意破坏"用例且破坏被抓; 抓不到破坏的判据是恒真,
恒真与没测在输出上一模一样。本模块提供三层工具:

  1) 点状工具(测试里逐判据写破坏用例):
       mutate(f, **kw)                    克隆 facts 并覆盖字段(模块/Namespace 通用)
       assert_criterion_rejects(check, corrupt, expected_code)   破坏必须红
       assert_criterion_accepts(check, facts, forbidden_code)    基线/容差内必须静默
       patched_derive(**wrappers)         检测器级负控: 临时改坏推导规则
                                          (E30 结论: 展开规则恒回文, SYM 判据
                                           经由 facts 输入不可达, 只能靠本工具证明)

  2) 恒真检测(双向: ①破坏用例能红 ②合法基线必须绿 —— 只查①放得过
     "基线就红"的过度约束判据, MET_TAPER 原病与对称奇数孔契约均由此过审):
       default_corruptions(f)             按 schema 字段自动生成类型化破坏
       killability_report(...)            每个 fail 代码被哪些破坏触发过
       assert_no_always_true(...)         判据在合法基线上就 fail(过度约束) → fail;
                                          任何代码无破坏可触发 / 判据从未变红 /
                                          判据在破坏下崩溃而非报告 → 一律 fail
       assert_criterion_alive(...)        逐判据入口: codes 必须显式给出该判据
                                          声明的全部 fail 代码 —— 死判据(声明的代码
                                          无破坏可触发)必须报错; 聚合级 codes=None
                                          时死判据会被活判据的杀伤记录掩盖

  3) 语义工具:
       assert_skip_not_fail(findings)     缺可选事实必须走 skip, 绝不走 fail
"""
import inspect
from contextlib import contextmanager
from types import SimpleNamespace

from . import derive as _derive
from .schema import Finding, is_number, has, get, REQUIRED, OPTIONAL


CRASH_SAMPLE = 4   # 恒真审计报告中展示的崩溃样本数上限(报告可读性, 非判据)


# ══════════ 克隆与覆写 ══════════

def _detach(v):
    """克隆隔离: list/tuple/dict 复制一层(元素均为标量/不可变), 其余原样。"""
    if isinstance(v, list):
        return list(v)
    if isinstance(v, tuple):
        return tuple(v)
    if isinstance(v, dict):
        return dict(v)
    return v


def snapshot(f):
    """克隆 facts 的公开字段(模块与 Namespace 通用)。保留 __doc__(禁令锁的对象)。
    容器字段复制一层: 克隆上的原地修改不得影响原件(负控制的前提)。"""
    try:
        base = {k: v for k, v in vars(f).items() if not k.startswith("_")}
    except TypeError:
        base = {k: getattr(f, k) for k in dir(f) if not k.startswith("_")}
    doc = getattr(f, "__doc__", None)
    if doc is not None:
        base["__doc__"] = doc
    return {k: _detach(v) for k, v in base.items()}


def mutate(f, **kw):
    """克隆 facts 并覆盖字段; 原 facts 不被改动(覆盖值整体替换, 不做原地修改)。"""
    base = snapshot(f)
    base.update(kw)
    return SimpleNamespace(**base)


def dropped(f, *names):
    """克隆 facts 并删除字段(模拟"事实缺省")。"""
    base = snapshot(f)
    for n in names:
        base.pop(n, None)
    return SimpleNamespace(**base)


# ══════════ 判据输出读取 ══════════

def fail_codes(findings):
    return sorted(set(fd.code for fd in findings if fd.level == "fail"))


def skip_codes(findings):
    return sorted(set(fd.code for fd in findings if fd.level == "skip"))


def codes_of(check, f):
    """跑一次判据, 返回 (fail代码集, findings)。判据崩溃视为缺陷直接抛出。"""
    r = check(f)
    return set(c for c in fail_codes(r)), r


# ══════════ 点状负控 ══════════

def assert_criterion_rejects(check, corrupt_facts, expected_code, label=""):
    """破坏必须被抓: expected_code 必须出现在 fail 代码里, 否则本断言失败。
    判据崩溃(异常)也算失败 —— 判据必须"报告", 不能"崩溃"。"""
    tag = label or expected_code
    try:
        r = check(corrupt_facts)
    except Exception as e:   # noqa: BLE001
        raise AssertionError("判据崩溃而非报告(%s): %r" % (tag, e))
    got = fail_codes(r)
    if expected_code not in got:
        raise AssertionError("破坏未被抓(%s): 期望 fail 代码 %r, 实得 %r"
                             % (tag, expected_code, got))
    return r


def assert_criterion_accepts(check, facts, forbidden_code, label=""):
    """基线/容差内必须静默: forbidden_code 不得出现在 fail 代码里。"""
    r = check(facts)
    got = fail_codes(r)
    if forbidden_code in got:
        raise AssertionError("误报(%s): %s 不应触发, 实得 fail=%r"
                             % (label or "baseline", forbidden_code, got))
    return r


def assert_skip_not_fail(findings, context=""):
    """缺可选事实必须走 skip: 断言零 fail(skip/warn 任意)。skip=未执行, 不算通过。"""
    got = fail_codes(findings)
    if got:
        raise AssertionError("缺可选事实不得 fail(%s): %r" % (context, got))
    return findings


@contextmanager
def patched_derive(**wrappers):
    """检测器级负控: wrapper(orig_fn) -> 替换函数, 临时改坏 bridge3d.derive 上的推导,
    模拟"展开/递推规则被改坏"(L2 实测跨序等同源缺陷), 证明 INV 护栏非恒真。"""
    saved = {}
    try:
        for name, wrapper in wrappers.items():
            orig = getattr(_derive, name)
            saved[name] = orig
            setattr(_derive, name, wrapper(orig))
        yield
    finally:
        for name, orig in saved.items():
            setattr(_derive, name, orig)


# ══════════ 自动破坏用例生成 ══════════

_NUMERIC_FIELDS = tuple(n for n in REQUIRED + OPTIONAL if n not in
                        ("RELATIONS", "ASSUMPTION_NAMES"))


def default_corruptions(f):
    """按 schema 已知字段自动生成类型化破坏用例, 返回 [(label, facts')]。

    覆盖: 标量清零/反号/翻倍/偏移/缺省; 序列增删/缩放/清零/换序;
    SOURCES 删键/坏等级/等级造假/空说明; 旗标翻转; 假设层泄漏; 关系恒假;
    禁令 docstring 清空。自定义判据可在此之上追加(见 killability_report 参数)。
    """
    out = []
    snap = snapshot(f)

    def add(label, **kw):
        out.append((label, mutate(f, **kw)))

    for n in _NUMERIC_FIELDS:
        if not (has(f, n) and is_number(get(f, n))):
            continue
        v = get(f, n)
        add("zero:" + n, **{n: v * 0})
        add("neg:" + n, **{n: -v})
        add("scale2:" + n, **{n: v * 2})
        add("scale4:" + n, **{n: v * 4})
        add("scale8:" + n, **{n: v * 8})   # 高倍率: 高净空桥(如不对称大桥)的 SPRINGER 类破坏
        add("off1:" + n, **{n: v + 1})
        out.append(("missing:" + n, dropped(f, n)))

    n_span = get(f, "N_SPAN")
    if isinstance(n_span, int) and not isinstance(n_span, bool):
        add("type:N_SPAN_float", N_SPAN=float(n_span))   # 孔数非 int → IMP_REQUIRED_TYPE

    if has(f, "SPAN_DISTINCT"):
        d = list(get(f, "SPAN_DISTINCT"))
        if len(d) >= 2:
            add("list:drop_last:SPAN_DISTINCT", SPAN_DISTINCT=d[:-1])
            add("list:swap:SPAN_DISTINCT",
                SPAN_DISTINCT=d[:1] + [d[1], d[0]] + d[2:] if len(d) >= 2 else d)
            add("list:scale_first:SPAN_DISTINCT",
                SPAN_DISTINCT=[d[0] * 1.05] + d[1:])
            add("list:zero_first:SPAN_DISTINCT",
                SPAN_DISTINCT=[0.0] + d[1:])
        add("list:append:SPAN_DISTINCT", SPAN_DISTINCT=d + [d[0]])
        out.append(("missing:SPAN_DISTINCT", dropped(f, "SPAN_DISTINCT")))

    if has(f, "SOURCES") and hasattr(get(f, "SOURCES"), "items"):
        src = dict(get(f, "SOURCES"))
        if src:
            req_present = [k for k in REQUIRED if k in src]
            k0 = req_present[0] if req_present else sorted(src.keys())[0]
            s1 = dict(src); s1.pop(k0)
            add("sources:drop:%s" % k0, SOURCES=s1)
            out.append(("attr:gone:%s" % k0, dropped(f, k0)))
            s2 = dict(src); s2[k0] = ("传说", src[k0][1] if isinstance(src[k0], (tuple, list)) else "x")
            add("sources:bad_grade:%s" % k0, SOURCES=s2)
            s3 = dict(src); s3[k0] = (src[k0][0], "")
            add("sources:empty_note:%s" % k0, SOURCES=s3)
            working = [k for k, v in src.items()
                       if isinstance(v, (tuple, list)) and len(v) == 2 and v[0] == "工作值"]
            if working:
                kw_ = working[0]
                s4 = dict(src)
                s4[kw_] = ("官方", src[kw_][1])
                add("sources:inflate:%s" % kw_, SOURCES=s4)
                s6 = dict(src)
                s6[kw_] = ("工作值", "据说如此")
                add("sources:undocumented:%s" % kw_, SOURCES=s6)
            official = [k for k, v in src.items()
                        if isinstance(v, (tuple, list)) and len(v) == 2 and v[0] == "官方"]
            if official:
                ko = official[0]
                s5 = dict(src)
                s5[ko] = ("官方", "据说如此")
                add("sources:uncited:%s" % ko, SOURCES=s5)

    if has(f, "RESEARCH_DONE"):
        add("flag:research_done_false", RESEARCH_DONE=False)
        add("shape:RESEARCH_DONE_nonbool", RESEARCH_DONE="yes")   # 登记非 bool → IMP_REGS_SHAPE

    if has(f, "N_SPAN"):
        add("type:N_SPAN_bool", N_SPAN=True)           # bool 是 int 子类, 必须显式排除

    for n in ("ARCH_RATIO", "RING_T", "DECK_UP_W", "DECK_DOWN_W",
              "DECK_Z_TOP", "DECK_Z_END", "CLOSURE_TOL"):
        if has(f, n) and is_number(get(f, n)):
            add("shape:%s_nonnum" % n, **{n: "坏"})    # 可选条目类型非法 → IMP_OPTIONAL_TYPE

    if has(f, "SOURCES"):
        add("shape:SOURCES_not_dict", SOURCES=(0,))    # 非dict登记 → IMP_REGS_SHAPE(不得崩溃)

    if has(f, "RELATIONS"):
        add("shape:RELATIONS_not_dict", RELATIONS=(0,))  # 关系表形状坏 → IMP_RELATIONS_SHAPE

    for n in ("SOURCES", "RESEARCH_DONE"):
        out.append(("missing:" + n, dropped(f, n)))

    if has(f, "ASSUMPTION_NAMES") and has(f, "SOURCES") and len(snapshot(f).get("SOURCES", {})) > 0:
        leaked = list(get(f, "ASSUMPTION_NAMES")) + [sorted(get(f, "SOURCES").keys())[0]]
        add("assumptions:leak", ASSUMPTION_NAMES=leaked)

    if has(f, "RELATIONS") and hasattr(get(f, "RELATIONS"), "items"):
        rel = dict(get(f, "RELATIONS"))
        # 每条声明的关系各配一个恒假破坏 —— 逐判据审计时每条 REL_* 代码都必须可杀
        for r0 in sorted(rel.keys()):
            broken = dict(rel)
            broken[r0] = (lambda ff: False)
            add("relations:false:%s" % r0, RELATIONS=broken)

    add("doc:bans_stripped", __doc__="本项目 facts。")

    return out


# ══════════ 恒真检测 ══════════

def killability_report(check, f, corruptions=None, derive_corruptions=None):
    """报告每个 fail 代码被哪些破坏用例触发过。

    返回 {"kills": {code: [label...]}, "crashes": [(label, repr)...]}。
    判据在破坏下抛异常 = 崩溃而非报告, 记入 crashes(assert_no_always_true 视为失败)。

    derive_corruptions: [(label, {derive函数名: wrapper(orig)->corrupt})],
    用于"经由 facts 输入不可达"的护栏判据(如 INV_SUPPORTS_LEN: 递推规则恒产
    N_SPAN+1 个支承, 只能改坏推导本身才能杀)的检测器级负控。
    """
    if corruptions is None:
        corruptions = default_corruptions(f)
    kills = {}
    crashes = []
    baseline_codes = []

    def record(label, findings):
        for c in fail_codes(findings):
            lst = kills.setdefault(c, [])
            if label not in lst:
                lst.append(label)

    try:
        baseline_codes = fail_codes(check(f))
    except Exception as e:   # noqa: BLE001
        crashes.append(("baseline", repr(e)))
    for label, cf in corruptions:
        try:
            record(label, check(cf))
        except Exception as e:   # noqa: BLE001
            crashes.append((label, repr(e)))
    for label, wrappers in (derive_corruptions or []):
        try:
            with patched_derive(**wrappers):
                record(label, check(f))
        except Exception as e:   # noqa: BLE001
            crashes.append((label, repr(e)))
    return {"kills": kills, "crashes": crashes,
            "baseline_fail_codes": baseline_codes,
            "n_corruptions": len(corruptions)}


def assert_no_always_true(check, f, codes=None, corruptions=None,
                          derive_corruptions=None, require_baseline_green=True):
    """恒真检测(双向): 给定判据, 自动生成破坏用例并验证它会红; 恒真则本断言 fail。

    四种失败模式(输出上一模一样, 必须区分):
      1) 判据在**合法基线**上就 fail —— 过度约束("见谁都咬", MET_TAPER 原病 /
         对称奇数孔契约均由此过审) → 默认 fail(require_baseline_green=False 显式豁免);
      2) 判据在任何破坏下都不变红 —— 恒真(或破坏用例不足, 需追加自定义破坏);
      3) codes 中指定代码没有任何破坏能触发 —— 该代码是死判据
         (codes=None 时无法枚举"应然代码", 死判据会被活代码的杀伤记录掩盖;
          逐判据审计请用 assert_criterion_alive 显式点名);
      4) 判据在破坏下崩溃而非报告 —— 脆弱判据(铁律: 必须报告, 不能崩溃)。
    """
    rep = killability_report(check, f, corruptions=corruptions,
                             derive_corruptions=derive_corruptions)
    if rep["crashes"]:
        raise AssertionError("判据崩溃而非报告(必须修复为报告): %r"
                             % (rep["crashes"][:CRASH_SAMPLE],))
    if require_baseline_green and rep["baseline_fail_codes"]:
        raise AssertionError(
            "基线即红: 判据在合法事实上就 fail(过度约束/见谁都咬) —— "
            "负控制必须双向: 破坏能红之外, 合法基线必须绿。基线 fail 代码: %r"
            % (rep["baseline_fail_codes"],))
    if codes is None:
        codes = sorted(set(rep["kills"].keys()) | set(rep["baseline_fail_codes"]))
        if not codes:
            raise AssertionError(
                "恒真: 在 %d 个破坏用例下判据从未产生任何 fail —— 与没测一样"
                % rep["n_corruptions"])
    unkillable = [c for c in codes if not rep["kills"].get(c)]
    if unkillable:
        raise AssertionError(
            "恒真嫌疑: 以下 fail 代码无任何破坏用例可触发: %r (破坏用例 %d 个, "
            "覆盖到的代码: %r)" % (unkillable, rep["n_corruptions"],
                                  sorted(rep["kills"].keys())))
    return rep


def assert_criterion_alive(check, f, codes, corruptions=None,
                           derive_corruptions=None):
    """逐判据恒真审计入口(I5): codes 必须显式给出该判据文档声明的**全部** fail 代码。

    与聚合级 codes=None 的差别: 声明的代码若没有任何破坏能触发(死判据),
    此处必须报错, 不可能被其他活代码的杀伤记录掩盖。
    双向断言同时生效: 合法基线必须绿 + 每个声明代码必须可杀。
    """
    if not codes:
        raise AssertionError("assert_criterion_alive 必须显式给出 codes(空表=没有可证伪声明, "
                             "判据无牙), 不能静默放过")
    return assert_no_always_true(check, f, codes=tuple(codes),
                                 corruptions=corruptions,
                                 derive_corruptions=derive_corruptions)
