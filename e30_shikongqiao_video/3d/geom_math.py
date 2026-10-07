# -*- coding: utf-8 -*-
"""E30 纵剖/收分纯数学单源(零 bmesh; P2-T2 修复轮 D3 主控裁决 2026-10-07)。

deck_z / arch_crown_z / arch_springer_z / width_at 四式自 bridge_geom2 **原样
搬移**(表达式逐字不动, 常数读 facts/assumptions 命名值 —— 本模块不定义任何
新几何常数), 消费关系:
  - bridge_geom2(本体)改为 import 委托: 函数体一行转发, 几何逐位不变
    (core_hash 三对象逐位不变为硬门, freeze_manifest §7);
  - centering(P2 券架)/sequencer(T4)消费本模块, 不许再抄第二套公式;
  - 跨源钉(tests/test_p2_geom_math.py): 本模块 vs 石账(out/ledger_full.json)
    RING 龙门石 transform z 逐孔等(±1e-9) —— blender 侧 masonry 公式链生成的
    账本与本模块互证, 任一方漂移即红。

逐孔拱线(arch_z/arch_dzdx/rise_ratio/spandrel)本就是 facts 单源(M14 归一),
不在本模块重复; 本模块只收编"以 PIER_X/桥面为锚的纵剖层"。
"""
import facts as _F
from assumptions import BODY_BOTTOM as _BODY_BOTTOM

BRIDGE_LEN, N_SPAN = _F.BRIDGE_LEN, _F.N_SPAN
DECK_Z_TOP, DECK_Z_END = _F.DECK_Z_TOP, _F.DECK_Z_END
DECK_UP_W, DECK_DOWN_W = _F.DECK_UP_W, _F.DECK_DOWN_W
SPAN_DISTINCT = list(_F.SPAN_DISTINCT)
SPANS = list(SPAN_DISTINCT) + list(reversed(SPAN_DISTINCT[:-1]))

# 墩/台中心 x 表: 累加规则与 qa_bridge.derive 完全一致(规则即数据, 无第二套公式)。
PIER_X = []
_acc = -BRIDGE_LEN / 2.0
for _i in range(N_SPAN + 1):
    _w = _F.BRIDGE_ABUT if _i in (0, N_SPAN) else _F.pier_w(_i)
    PIER_X.append(_acc + _w / 2.0)
    _acc += _w
    if _i < N_SPAN:
        _acc += SPANS[_i]

# 桥长闭合硬门(自 bridge_geom2 原样搬移): 变宽剖面上累加必须严格回到 +BRIDGE_LEN/2。
assert abs(_acc - BRIDGE_LEN / 2.0) < 1e-9, \
    "桥长闭合破坏: 墩台累加终点 %.9f != +%.1f (PIER_W_INT 总和须恒等 (N_SPAN-1)*PIER_W)" \
    % (_acc, BRIDGE_LEN / 2.0)


def arch_center_x(i):
    """第 i 孔(0-based)孔心 x = 两邻墩/台中心的中点。"""
    return (PIER_X[i] + PIER_X[i + 1]) / 2.0


def deck_z(x):
    """桥面标高: 以**抛物线**为母曲线, 中央最高, 两端最低。

    z(x) = DECK_Z_TOP - K_DECK * x^2,  K_DECK 使 z(±75) = DECK_Z_END。
    (GPT v4 给定公式 z=7.55-0.0004267x^2; 用参数化写法便于调两端高度)

    ⚠ 此前版本用"控制点 smoothstep 插值", 数组未正确居中, 导致
      x=0 反而是最低点(5.15)、x=±60 最高 —— 桥面弧度**方向反了**。
      该错误由 GPT 看图发现(它说"读成中间低两头高"), 我未自查出来。
      故此处改为显式抛物线, 并加断言防止再次反向。
    """
    half = BRIDGE_LEN / 2.0
    ax = min(abs(x), half)
    k = (DECK_Z_TOP - DECK_Z_END) / (half * half)
    return DECK_Z_TOP - k * ax * ax


def arch_crown_z(i):
    """M12/M19: 第 i 孔拱冠标高 = 该孔中心处桥面标高 - 该孔拱肩厚(冠线跟随桥面
    camber; 拱肩 M19 起为逐孔剖面 facts.spandrel, 中央 1.4 → 端 0.5)。"""
    xc = arch_center_x(i)
    return deck_z(xc) - _F.spandrel(i)


def arch_rise(i):
    """第 i 孔矢高 = 矢跨比(facts.rise_ratio 剖面) × 净跨。"""
    return _F.rise_ratio(i) * SPANS[i]


def arch_springer_z(i):
    """第 i 孔起拱线 = 冠 - 矢高。端孔自动贴近水面(真实小端孔)。"""
    return arch_crown_z(i) - arch_rise(i)


def width_at(x, z):
    """桥体线性收分半宽: x 处桥面顶 zt=deck_z(x), z∈[BODY_BOTTOM, zt] 内插
    DECK_DOWN_W→DECK_UP_W 自 bridge_geom2._width_at/build_body_bm 原样搬移;
    masonry._hw 同式, D3 后统一消费本函数(第二套公式绝后)。"""
    zt = deck_z(x)
    if zt - _BODY_BOTTOM < 1e-9:
        return DECK_UP_W / 2.0
    f = (z - _BODY_BOTTOM) / (zt - _BODY_BOTTOM)
    f = max(0.0, min(1.0, f))
    return (DECK_DOWN_W + (DECK_UP_W - DECK_DOWN_W) * f) / 2.0


# ── 自检: 桥面必须中央最高(自 bridge_geom2 原样搬移, 导入即验) ──
def _assert_deck_correct():
    half = BRIDGE_LEN / 2.0
    hi = int(half)
    vals = [deck_z(float(x)) for x in range(-hi, hi + 1)]
    mx = max(vals)
    arg = vals.index(mx) - hi
    if abs(deck_z(0.0) - DECK_Z_TOP) > 0.01 or abs(mx - DECK_Z_TOP) > 0.01 or abs(arg) > 3:
        raise AssertionError(
            "桥面弧度反向! z(0)=%.2f (应=%.2f), 最大值在 x=%d" % (deck_z(0.0), DECK_Z_TOP, arg))
    if abs(deck_z(half) - DECK_Z_END) > 0.01:
        raise AssertionError("两端标高错: z(75)=%.2f 应=%.2f" % (deck_z(half), DECK_Z_END))


_assert_deck_correct()
