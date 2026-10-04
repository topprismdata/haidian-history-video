# -*- coding: utf-8 -*-
"""bridge3d.derive —— 由 facts 推导几何量, 本模块不写死任何项目数值。

跨序展开 / 支承递推 / 纵坡母线全部参数化: 任意 n 孔桥(含偶数孔上限说明见 spans)
走同一套代码。推导规则是"拓扑契约", 项目不得在本模块里塞自己的常数;
项目专属形态约束(如"中央孔最大两侧渐小")应写进项目 facts 的 RELATIONS。

所有函数在必填事实缺失时抛 MissingFactError(判据层捕获后降级 skip)。
"""
from .schema import MissingFactError, is_number


def _need(f, name):
    if not hasattr(f, name):
        raise MissingFactError(name)
    return getattr(f, name)


def _need_positive(f, name):
    v = _need(f, name)
    if not is_number(v) or v <= 0:
        raise MissingFactError(name)   # 非法尺寸视为"不可用", 由 IMP 层报 fail
    return v


def _need_int_span(f):
    n = _need(f, "N_SPAN")
    if isinstance(n, bool) or not isinstance(n, int):
        raise MissingFactError("N_SPAN")
    return n


def spans(f):
    """对称展开 SPAN_DISTINCT → 完整跨序。

    展开规则: D + reversed(D[:-1]), 即 2n-1 个净跨(中央孔只计一次),
    这要求 SPAN_DISTINCT 语义为"半侧含中央孔的完整净跨"。
    展开长度与 N_SPAN 的一致性由 INV 判据验证, 此处不做任何项目假设。
    """
    d = list(_need(f, "SPAN_DISTINCT"))
    return d + list(reversed(d[:-1]))


def pier_count(f):
    """内墩数 = N_SPAN - 1(纯拓扑推导, 不是任何项目的常量)。"""
    return _need_int_span(f) - 1


def support_count(f):
    """支承总数 = N_SPAN + 1(两端桥台 + 内墩)。"""
    return _need_int_span(f) + 1


def pier_x(f):
    """支承中心递推: 从 -BRIDGE_LEN/2 起, 两端宽 BRIDGE_ABUT、中间宽 PIER_W,
    逐个累加净跨。返回 N_SPAN+1 个 x 坐标(升序)。
    递推与项目几何生成器必须同口径(闭合一致性由 MET_CLOSURE 把关)。
    N_SPAN 多于展开跨数时(双字段不一致)抛 MissingFactError —— 判据必须"报告"
    (INV_SPANS_LEN)而非崩溃(E30 曾把这条崩溃路径记为已知缺陷, 框架不再继承)。"""
    half = _need_positive(f, "BRIDGE_LEN") / 2.0
    n = _need_int_span(f)
    pier_w = _need_positive(f, "PIER_W")
    abut_w = _need_positive(f, "BRIDGE_ABUT")
    sp = spans(f)
    if len(sp) < n:
        raise MissingFactError("SPAN_DISTINCT 展开长度 %d < N_SPAN %d (双字段不一致)"
                               % (len(sp), n))
    xs, acc = [], -half
    for i in range(n + 1):
        w = abut_w if i in (0, n) else pier_w
        xs.append(acc + w / 2.0)
        acc += w
        if i < n:
            acc += sp[i]
    return xs


def deck_z(f):
    """桥面纵坡母线(抛物线, 中央最高两端最低): 返回 z(x) 函数。

    需要 DECK_Z_TOP / DECK_Z_END / BRIDGE_LEN; 任一缺失或非法 → MissingFactError。
    """
    top = _need(f, "DECK_Z_TOP")
    end = _need(f, "DECK_Z_END")
    half = _need_positive(f, "BRIDGE_LEN") / 2.0
    if not (is_number(top) and is_number(end)):
        raise MissingFactError("DECK_Z_TOP/DECK_Z_END")
    k = (top - end) / (half * half)

    def z(x):
        ax = min(abs(x), half)
        return top - k * ax * ax

    return z


def geometry_closure(f):
    """几何闭合: 返回 (计算总长, 目标总长, 差值)。

    计算总长 = sum(净跨) + (N_SPAN-1)*PIER_W + 2*BRIDGE_ABUT —— 全部拓扑推导,
    无任何项目常数; 差值超容差(来自 facts.CLOSURE_TOL 或显式参数)由 MET 判据报。
    """
    total_spans = sum(spans(f))
    computed = (total_spans
                + pier_count(f) * _need_positive(f, "PIER_W")
                + 2.0 * _need_positive(f, "BRIDGE_ABUT"))
    target = _need_positive(f, "BRIDGE_LEN")
    return (computed, target, computed - target)
