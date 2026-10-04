# -*- coding: utf-8 -*-
"""bridge3d.derive —— 由 facts 推导几何量, 本模块不写死任何项目数值。

跨序声明 / 支承递推 / 纵坡母线全部参数化: 任意 n 孔桥走同一套代码。
跨序 SPAN_DISTINCT 允许两种合法形态(全长表 / 半侧对称表, 规则见 spans):
对称、奇数孔只是**便利路径的展开属性**, 不是框架对项目的普适要求 ——
不对称桥(卢沟桥东一拱≠西一拱)与偶数孔桥用全长表直接声明。
推导规则是"拓扑契约", 项目不得在本模块里塞自己的常数;
项目专属形态约束(如"中央孔最大两侧渐小""跨序回文")应写进项目 facts 的 RELATIONS。

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
    """SPAN_DISTINCT → 完整跨序(全长 N_SPAN 个)。

    两种合法声明形态(2026-10-05 终审 I1: 奇数对称不再是契约普适律):
      1) 全长表: len(SPAN_DISTINCT) == N_SPAN → 直接用作跨序, 不做任何变换。
         任何桥都可用: 不对称桥(卢沟桥东一拱≠西一拱)、偶数孔桥、等跨平桥。
      2) 半侧表(便利路径): 其余长度按 D + reversed(D[:-1]) 对称展开, 即
         "正中一孔最大两侧依次渐小"的对称奇数孔桥只需声明半侧含中央孔的净跨。
         该形态在结构上恒构造回文 —— 对称性是展开规则的属性, 不是框架对项目的要求;
         项目若声明对称形态, 应写进 facts.RELATIONS 由 IMP_RELATIONS 验证。
      两种形态之外的长度原样交给 INV_SPANS_LEN 报 fail(判据"报告", 不在此崩溃)。
    """
    d = list(_need(f, "SPAN_DISTINCT"))
    n = _need_int_span(f)
    if len(d) == n:
        return list(d)
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
