# -*- coding: utf-8 -*-
"""E30 十七孔桥 P2-T2 券架(centering)生成器 —— 纯 python 闭合六面体, blender-free。

结构可信期清式满排架木券胎的工程复原模型(判据承
.superpowers/sdd/p2-task-2-brief.md Task 2 + 主控补充设计):

  - 排架沿 y 两榀(±(ring_t/2+BENT_Y_CLEAR) 外), 柱排数 = int(span/POST_SPACING)+1,
    沿跨对称均布; 柱底一律 assumptions.BODY_BOTTOM(端孔 springer 近水~0.75m
    亦不改基准, 柱排数随跨自然减少)。
  - 每柱头堆叠(自下而上): 柱 → 卸架楔一对(上下楔各 WEDGE_H=0.12m, 斜面 1:8,
    合计 0.24m) → 楞木(WALING_H=0.12) → 券胎板(rib, 沿弧 RIB_T=0.03)。
    一榀楞木横跨两柱头, 故每排 2 对楔: wedge_events = 柱头对数 = 柱数。
  - 支撑面目标: 拱脚区(|x−xc| > span/2−SPRINGER_ZONE)楞木顶直接贴 intrados
    下方(即楞木顶 = 拱腹线)即可; 跨中(拱段)工作面 = extrados + WORK_CLEAR(30mm)。
    券胎面 = extrados + WORK_CLEAR + lift(lift 为卸架预抬量, 0 时 rib 上缘
    恰在 extrados+0.06 —— brief 带宽上界)。
  - 桥面拓扑夹持: 一切支撑构件顶 z ≤ deck_z_fn(x)(券架永不高过桥面,
    拓扑必需, 非经验常数; 真实工况下中央 6.27<7.30 / 端孔 2.66<2.73 不触发)。
  - footprint_polys: 券胎板带 x-z 外轮廓(供 sequencer 占位冲突检查),
    与 rib 板同一采样, 保证二者投影逐点一致。

坐标约定: 孔局部系 —— xc=0 位于孔中心, y=0 为桥中线, z 绝对(常水位 z=0),
x 局部偏移直接传给 deck_z_fn(x)。

零硬编码孔参数: 拱形/跨径/环厚一律来自 facts(arch_z / rise_ratio / SPAN_DISTINCT /
RING_T / DECK_*)与 assumptions.BODY_BOTTOM。
[工程参数](实现工作值, 非史料常数): POST_SPACING / POST_SECTION / BENT_Y_CLEAR /
SPRINGER_ZONE / WORK_CLEAR / RIB_T / RIB_W / RIB_SEG_N / WALING_* / WEDGE_*。
"""
import math
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import facts as _F
from assumptions import BODY_BOTTOM as _BODY_BOTTOM

# --- [工程参数] 排架与堆叠 ---
POST_SPACING = 1.2      # 排架柱名义间距(m, brief 接口值); 排数 = int(span/此值)+1
POST_SECTION = 0.2      # 柱截面方木边长(m)
BENT_Y_CLEAR = 0.1      # 两榀排架在 ±(ring_t/2+此值) 外(brief 补充设计)
SPRINGER_ZONE = 0.5     # 拱脚区宽度: |x|>span/2−此值 时楞木贴 intrados 下方(brief 补充)
WORK_CLEAR = 0.03       # 跨中工作面: extrados+30mm(brief 接口"extrados+30mm 楞木网")
RIB_T = 0.03            # 券胎板厚(m); lift=0 时 rib 上缘 = extrados+0.06(brief 带宽上界)
RIB_W = 0.2             # 券胎板 y 向宽(m), 两行对位两榀排架
RIB_SEG_N = 24          # 券胎弧向离散段数(实现参数)
WALING_H = 0.12         # 楞木高(m)
WALING_W = 0.2          # 楞木 x 向宽(m)
WEDGE_H = 0.12          # 上/下楔各名义高 0.12m(brief 补充设计)
WEDGE_LEN = 0.48        # 楔 x 向长(m)
WEDGE_SLOPE = 8.0       # 斜面 1:8(高差 = WEDGE_LEN/WEDGE_SLOPE = 0.06m)
WEDGE_W = 0.2           # 楔 y 向宽(m)

_FACES = ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
          (3, 7, 6, 2), (0, 4, 7, 3), (1, 2, 6, 5))


def bottom_z():
    """柱底基准 z(= assumptions.BODY_BOTTOM; 真源单点, 供测试对锚)。"""
    return _BODY_BOTTOM


SPANS = list(_F.SPAN_DISTINCT) + list(reversed(_F.SPAN_DISTINCT[:-1]))
"""17 孔净跨表(=facts.SPAN_DISTINCT 对称展开; bridge_geom2 同一形态)。"""


def span_of(arch_idx):
    """第 arch_idx(0-based)孔净跨(m)。"""
    return SPANS[arch_idx]


def _u(arch_idx):
    return abs(2 * arch_idx - (_F.N_SPAN - 1)) / float(_F.N_SPAN - 1)


def arch_springer_z(arch_idx):
    """第 arch_idx 孔起拱线高: 由桥面/拱肩/矢跨比反推(中央孔恒等 facts.SPRINGER:
    7.30−1.40−0.56*8.50=1.14)。孔中桥面以 DECK_Z_TOP..DECK_Z_END 按同一 u 线性
    内插 —— 孔内 camber 二阶效应属表现层, 券架高度容差内不计。"""
    deck_c = _F.DECK_Z_TOP + (_F.DECK_Z_END - _F.DECK_Z_TOP) * _u(arch_idx)
    return deck_c - _F.spandrel(arch_idx) - _F.rise_ratio(arch_idx) * span_of(arch_idx)


def _box(x0, x1, y0, y1, zb0, zb1, zt0, zt1, kind):
    # type: (...) -> Dict
    """斜剪六面体: 底/顶面 z 随 x 线性(zb0/zb1, zt0/zt1), 恒过 (x=const, y=const)
    平面校验 → 6 面皆平面 quad, 12 边各属 2 面(闭合)。"""
    verts = [[x0, y0, zb0], [x1, y0, zb1], [x1, y1, zb1], [x0, y1, zb0],
             [x0, y0, zt0], [x1, y0, zt1], [x1, y1, zt1], [x0, y1, zt0]]
    bbox = (x0, x1, y0, y1, min(zb0, zb1, zt0, zt1), max(zb0, zb1, zt0, zt1))
    return {"kind": kind, "verts": verts, "faces": list(_FACES), "bbox": bbox}


def build_centering(arch_idx, span, ring_t, lift, springer_z, deck_z_fn):
    # type: (int, float, float, float, float, Callable[[float], float]) -> Dict
    """生成第 arch_idx 孔券架(brief 接口)。

    返回 {"id": "CEN-ARCH08", "parts": [{kind, verts, faces, bbox}...],
          "wedge_events": 柱头对数, "footprint_polys": [[(x,z)...]]}。
    deck_z_fn: 孔局部 x → 桥面顶 z(券架拓扑上界, 支撑面夹持不高于它)。
    lift: 卸架预抬量(m), 抬升整条券胎面(拱脚区贴拱腹目标不受 lift)。
    """
    a = span / 2.0
    b = _F.rise_ratio(arch_idx) * span
    y_out = ring_t / 2.0 + BENT_Y_CLEAR

    def intrados(x):
        return _F.arch_z(x, 0.0, springer_z, a, b)

    def extrados(x):
        return intrados(x) + ring_t

    def deck(x):
        return deck_z_fn(x)

    def surface(x):
        """券胎面(=跨中楞木顶/工作面), lift 抬升, 桥面夹持。"""
        return min(extrados(x) + WORK_CLEAR + lift, deck(x))

    def support_top(x):
        """该排楞木顶 z: 拱脚区贴 intrados 下方, 拱段用券胎面。"""
        if abs(x) > a - SPRINGER_ZONE:
            return min(intrados(x), deck(x))
        return surface(x)

    n_rows = max(int(span / POST_SPACING) + 1, 2)
    xs = [-a + span * k / float(n_rows - 1) for k in range(n_rows)]
    xs[0] = -a
    xs[-1] = a

    parts = []  # type: List[Dict]
    wedge_events = 0
    for x in xs:
        top = support_top(x)
        wedge_top = top - WALING_H
        post_top = wedge_top - 2 * WEDGE_H
        if post_top <= _BODY_BOTTOM:
            raise ValueError("柱顶(%.3f)不高于柱底基准(%.3f): 支撑面 %.3f 过低"
                             % (post_top, _BODY_BOTTOM, top))
        half = POST_SECTION / 2.0
        for y_c in (-y_out, y_out):
            parts.append(_box(x - half, x + half, y_c - half, y_c + half,
                              _BODY_BOTTOM, _BODY_BOTTOM, post_top, post_top, "post"))
            # 卸架楔一对: 下楔顶面斜(左高右低), 上楔底面同斜、顶面平(供楞木落平)
            d2 = WEDGE_LEN / WEDGE_SLOPE / 2.0
            wx0, wx1 = x - WEDGE_LEN / 2.0, x + WEDGE_LEN / 2.0
            wy0, wy1 = y_c - WEDGE_W / 2.0, y_c + WEDGE_W / 2.0
            mid = post_top + WEDGE_H
            parts.append(_box(wx0, wx1, wy0, wy1,
                              post_top, post_top, mid + d2, mid - d2, "wedge"))
            parts.append(_box(wx0, wx1, wy0, wy1,
                              mid + d2, mid - d2, wedge_top, wedge_top, "wedge"))
            wedge_events += 1
        parts.append(_box(x - WALING_W / 2.0, x + WALING_W / 2.0,
                          -(y_out + half), y_out + half,
                          wedge_top, wedge_top, top, top, "waling"))

    # 券胎板: 沿弧两行, 与 footprint 同一采样
    seg = RIB_SEG_N
    rxs = [-a + span * j / float(seg) for j in range(seg + 1)]
    rxs[0] = -a
    rxs[-1] = a
    for y_c in (-y_out, y_out):
        zb = [surface(x) for x in rxs]
        ry0, ry1 = y_c - RIB_W / 2.0, y_c + RIB_W / 2.0
        for j in range(seg):
            parts.append(_box(rxs[j], rxs[j + 1], ry0, ry1,
                              zb[j], zb[j + 1],
                              zb[j] + RIB_T, zb[j + 1] + RIB_T, "rib"))

    footprint = [(rxs[j], zb[j]) for j in range(seg + 1)] + \
                [(rxs[j], zb[j] + RIB_T) for j in range(seg, -1, -1)]

    return {
        "id": "CEN-ARCH%02d" % arch_idx,
        "parts": parts,
        "wedge_events": wedge_events,
        "footprint_polys": [footprint],
    }


def build_centering_for_arch(arch_idx, ring_t=None, lift=0.0):
    # type: (int, Optional[float], float) -> Dict
    """按孔号从 facts 单源取参建券架(sequencer 便捷入口):
    span=SPANS[i], ring_t=facts.RING_T, springer=arch_springer_z(i),
    孔内桥面取跨中值常数(见 arch_springer_z 注)。"""
    ring_t = _F.RING_T if ring_t is None else ring_t
    span = span_of(arch_idx)
    springer = arch_springer_z(arch_idx)
    deck_c = _F.DECK_Z_TOP + (_F.DECK_Z_END - _F.DECK_Z_TOP) * _u(arch_idx)

    def _deck(_x):
        return deck_c

    return build_centering(arch_idx, span, ring_t, lift, springer, _deck)
