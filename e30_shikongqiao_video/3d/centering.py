# -*- coding: utf-8 -*-
"""E30 十七孔桥 P2-T2 券架(centering)生成器 —— 纯 python 闭合六面体, blender-free。

**D1 工作面基准 = 拱腹 intrados**(主控裁决 2026-10-07 修复轮): rib 板顶沿拱腹
曲线 z = arch_z(x) − RIB_GAP(施工隙 5mm), 楞木/柱顶随之下移; 旧"拱脚区贴
intrados / 跨中工作面 = extrados+30mm"支撑分叉删除, 全线贴 intrados。

**楔副行程语义**: 上下楔 1:8 斜面副行程 = WEDGE_LEN/WEDGE_SLOPE = 0.06m, 语义 =
**合龙后压缩沉落**(圈环合龙后敲楔落架, 木作压缩、拱圈沉落至设计承位), 不是
"抬环脱架"的预抬量 —— lift 参数即沉落状态模拟量 ∈ [0, WEDGE_TRAVEL]。

**与 facts.RING_T 分叉解耦**(D2 停车线主控裁决 2026-10-07): 工作面贴拱腹后,
券架几何不需要环厚; 残留的环带尺寸需求(两榀排架 y 位 = ±(ring_t/2+间隙))一律
用**石账 params.ring_t 现算**(stone_ring_t(i)), 不引 facts.RING_T(已裁 STALE)。

消费 geom_math 单源(D3): SPANS/arch_springer_z/孔心表/桥面真抛物线; 本文件
禁止出现第二套纵剖公式。尺寸常量(DECK_* 经 geom_math)与 assumptions.BODY_BOTTOM
单点引用。Python 3.9.6。
"""
from typing import Callable, Dict, List, Optional
import json
import os

import facts as _F
import geom_math as _GM   # D3(P2-T2 修复轮): SPANS/起拱线/桥面/孔心表单源, 禁止第二套公式
from assumptions import BODY_BOTTOM as _BODY_BOTTOM

_HERE = os.path.dirname(os.path.abspath(__file__))
_LEDGER_PATH = os.environ.get("E30_LEDGER_PATH") or os.path.join(_HERE, "out", "ledger_full.json")

# --- [工程参数] 排架与堆叠 ---
POST_SPACING = 1.2      # 排架柱名义间距(m, brief 接口值); 排数 = int(span/此值)+1
POST_SECTION = 0.2      # 柱截面方木边长(m)
BENT_Y_CLEAR = 0.1      # 两榀排架在 ±(ring_t/2+此值) 外(brief 补充设计)
RIB_GAP = 0.005         # D1 施工隙(m): rib 板顶在拱腹下方 5mm, 全线贴 intrados
RIB_T = 0.03            # 券胎板厚(m)
RIB_W = 0.2             # 券胎板 y 向宽(m), 两行对位两榀排架
RIB_SEG_N = 24          # 券胎弧向离散段数(实现参数)
WALING_H = 0.12         # 楞木高(m)
WALING_W = 0.2          # 楞木 x 向宽(m)
WEDGE_H = 0.12          # 上/下楔各名义高 0.12m(brief 补充设计)
WEDGE_LEN = 0.48        # 楔 x 向长(m)
WEDGE_SLOPE = 8.0       # 斜面 1:8(总行程 = WEDGE_LEN/WEDGE_SLOPE = 0.06m)
WEDGE_TRAVEL = WEDGE_LEN / WEDGE_SLOPE
                        # 楔副总行程 0.06m —— D1 语义 = 合龙后压缩沉落上限(非脱环)
WEDGE_W = 0.2           # 楔 y 向宽(m)

_FACES = ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
          (3, 7, 6, 2), (0, 4, 7, 3), (1, 2, 6, 5))


def bottom_z():
    """柱底基准 z(= assumptions.BODY_BOTTOM; 真源单点, 供测试对锚)。"""
    return _BODY_BOTTOM


SPANS = list(_GM.SPANS)
"""17 孔净跨表(D3: 单源 geom_math.SPANS; bridge_geom2 同一形态)。"""


def span_of(arch_idx):
    """第 arch_idx(0-based)孔净跨(m)。"""
    return SPANS[arch_idx]


def arch_springer_z(arch_idx):
    """第 arch_idx 孔起拱线(D3 委托 geom_math.arch_springer_z: 桥面抛物线在孔心
    的值 − 拱肩 − 矢高; 中央孔恒等 facts.SPRINGER=1.14)。旧本地"DECK_Z_TOP..END
    按 u 线性内插"变体已废除 —— 第二套纵剖公式与 geom_math 单源裁决不容。"""
    return _GM.arch_springer_z(arch_idx)


_RING_T_BY_ARCH = {}  # type: Dict[int, float]


def stone_ring_t(arch_idx):
    # type: (int) -> float
    """第 arch_idx 孔券石账目 params.ring_t(现算; D2 停车线裁决 2026-10-07)。

    **centering 与 facts.RING_T 分叉解耦**: facts.RING_T=0.40 已裁 STALE(与券石
    账目 params.ring_t=0.54 分叉, 债务票 M20b), 券架不再消费它 —— 环带相关的
    唯一合法来源是石账每孔 params.ring_t(M20b 标定 ring_t(i) 后自动跟随)。
    石账缺失 → 响亮 raise(fail-on-skip 同纪律, 不静默兜底), 或由调用方显式传
    ring_t 绕开本读取。结果按孔缓存(账本一次性扫描)。"""
    if arch_idx not in _RING_T_BY_ARCH:
        if not os.path.exists(_LEDGER_PATH):
            raise RuntimeError(
                "out/ledger_full.json 不在盘上 —— stone_ring_t 现算不可用"
                "(先跑 blender -b --python 3d/p1a_slice.py -- --g2), "
                "或显式传 ring_t 参数; 禁止回退 facts.RING_T(STALE, D2 停车线裁决)")
        with open(_LEDGER_PATH, "r", encoding="utf-8") as fh:
            led = json.load(fh)
        vals = {}  # type: Dict[int, set]
        for s in led["stones"]:
            if ".RING." in s.get("id", ""):
                ai = int(s["id"].split(".")[0][4:]) - 1
                vals.setdefault(ai, set()).add(float(s["params"]["ring_t"]))
        for ai, vs in vals.items():
            if max(vs) - min(vs) > 1e-12:
                raise ValueError("孔%d 券石账目 ring_t 不唯一: %r" % (ai + 1, sorted(vs)))
            _RING_T_BY_ARCH[ai] = vs.pop()
    if arch_idx not in _RING_T_BY_ARCH:
        raise ValueError("石账无孔%d 的 RING 条目, ring_t 现算不可用" % (arch_idx + 1))
    return _RING_T_BY_ARCH[arch_idx]


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
    """生成第 arch_idx 孔券架(brief 接口; 几何语义 D1/D4/D5/D6, 2026-10-07)。

    返回 {"id": "CEN-ARCH%02d" % (arch_idx+1)(D4 1 基), "zone": "ARCH%02d"
    (石账 zone 同形), "arch_idx": arch_idx, "xc": 孔心全局 x(geom_math 孔心表),
    "parts": [{kind, verts, faces, bbox}...], "wedge_events": 柱头对数,
    "footprint": [{"poly": [(x,z)...], "y0", "y1", "kind"}...按榀/构件组](D6)}。

    坐标: 孔局部系(xc=0 孔中, y=0 桥中线, z 绝对/常水位 0)。**占位体积取
    parts[].bbox 加全局 xc 平移**(sequencer 占位冲突检查口径); footprint 仅
    rib 带轮廓(D6), 不承担占位语义。
    deck_z_fn: 孔局部 x → 桥面顶 z(拓扑上界)。D5: 夹持从 min() 改 **raise** ——
    工作面(rib 顶, 全链最高点)高于桥面即 DECK_CLASH(附 x 位置与余量), 排位与
    rib 采样双重覆盖; 不许静默压低把几何错误藏进支撑链。
    lift: 合龙后压缩沉落量 ∈ [0, WEDGE_TRAVEL](D1: 楔副 1:8 行程 0.06m 语义 =
    合龙后压缩沉落, 非脱环预抬); 越行程/负值 raise。

    工作面(D1): rib 板顶 = arch_z(x) − RIB_GAP − lift, 全线贴拱腹; 堆叠自上而下
    rib(RIB_T) → 楞木(WALING_H) → 楔对(2×WEDGE_H, 1:8) → 柱(至 BODY_BOTTOM)。
    """
    if not (0.0 <= lift <= WEDGE_TRAVEL):
        raise ValueError(
            "lift=%.4f 超出楔副行程 [0, %.4f](D1 沉落语义: lift 是合龙后压缩沉落"
            "量, 上限=楔副 1:8 总行程)" % (lift, WEDGE_TRAVEL))
    a = span / 2.0
    b = _F.rise_ratio(arch_idx) * span
    y_out = ring_t / 2.0 + BENT_Y_CLEAR
    zone = "ARCH%02d" % (arch_idx + 1)

    def intrados(x):
        return _F.arch_z(x, 0.0, springer_z, a, b)

    def face(x):
        """工作面: rib 板顶 = 拱腹 − 施工隙 − 沉落(D1 全线贴 intrados, 无分叉)。"""
        return intrados(x) - RIB_GAP - lift

    def deck_guard(x, z):
        """D5: 桥面拓扑夹持 —— 受检面高于桥面即 DECK_CLASH raise(附 x 与余量)。"""
        d = deck_z_fn(x)
        if z > d:
            raise ValueError(
                "DECK_CLASH: x=%.3f 工作面 %.4f 高于桥面 %.4f (余量 %+.4f) —— "
                "券架不得高于桥面(孔%d)" % (x, z, d, d - z, arch_idx + 1))

    def support_top(x):
        """楞木顶(= rib 板底): 工作面下让出 rib 厚。"""
        return face(x) - RIB_T

    n_rows = max(int(span / POST_SPACING) + 1, 2)
    xs = [-a + span * k / float(n_rows - 1) for k in range(n_rows)]
    xs[0] = -a
    xs[-1] = a

    # D5 夹持(先于任何构件生成): 排位点 + rib 采样点双重覆盖工作面最高点
    for x in xs:
        deck_guard(x, face(x))

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
            # 卸架楔一对: 下楔顶面斜(左高右低), 上楔底面同斜、顶面平(供楞木落平)。
            # 行程语义(D1): 合龙后敲楔, 副面滑移 ≤0.06m 供拱圈压缩沉落, 非脱环抬升。
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

    # 券胎板: 沿弧两行(与 footprint 同一采样); 板顶 = 工作面, 板底让出 RIB_T
    seg = RIB_SEG_N
    rxs = [-a + span * j / float(seg) for j in range(seg + 1)]
    rxs[0] = -a
    rxs[-1] = a
    for x in rxs:
        deck_guard(x, face(x))
    zb = [face(x) - RIB_T for x in rxs]   # rib 底(搁在楞木顶上)
    footprint = []  # type: List[Dict]
    for y_c in (-y_out, y_out):
        ry0, ry1 = y_c - RIB_W / 2.0, y_c + RIB_W / 2.0
        for j in range(seg):
            parts.append(_box(rxs[j], rxs[j + 1], ry0, ry1,
                              zb[j], zb[j + 1],
                              zb[j] + RIB_T, zb[j + 1] + RIB_T, "rib"))
        # D6: 每榀一条 {poly(x-z 底缘去+顶缘回), y0, y1, kind}; 孔局部系, 全局平移用 xc
        footprint.append({
            "poly": [(rxs[j], zb[j]) for j in range(seg + 1)] +
                    [(rxs[j], zb[j] + RIB_T) for j in range(seg, -1, -1)],
            "y0": ry0,
            "y1": ry1,
            "kind": "rib",
        })

    return {
        "id": "CEN-" + zone,                     # D4: 1 基(石账 zone/事件账同形)
        "zone": zone,
        "arch_idx": arch_idx,
        "xc": _GM.arch_center_x(arch_idx),       # D4: 全局孔心(平移字段)
        "parts": parts,
        "wedge_events": wedge_events,
        "footprint": footprint,
    }


def build_centering_for_arch(arch_idx, ring_t=None, lift=0.0):
    # type: (int, Optional[float], float) -> Dict
    """按孔号单源取参建券架(sequencer 便捷入口):
    span=SPANS[i], ring_t=**石账 params.ring_t 现算**(stone_ring_t(i); 不引
    facts.RING_T —— D2 停车线裁决: centering 与 RING_T STALE 分叉解耦, M20b
    标定 ring_t(i) 后自动跟随), springer=arch_springer_z(i),
    桥面 = geom_math.deck_z 真抛物线(孔心全局 x + 孔局部 x) —— 夹持/DECK_CLASH
    判的是真桥面, 不再是"跨中值常数"近似(D3 消费 geom_math 后免费获得)。"""
    ring_t = stone_ring_t(arch_idx) if ring_t is None else ring_t
    span = span_of(arch_idx)
    springer = arch_springer_z(arch_idx)
    xc0 = _GM.arch_center_x(arch_idx)

    def _deck(local_x):
        return _GM.deck_z(xc0 + local_x)

    return build_centering(arch_idx, span, ring_t, lift, springer, _deck)
