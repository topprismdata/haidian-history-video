"""E30 十七孔桥 几何 v2: 整体桥体 + 布尔挖券洞。

与 v1(bridge_geom.py)的根本差别:
  v1 = 一堆盒子/楔形棱柱拼接 -> 必然有阶梯与接缝, 且券洞靠"留空"近似。
  v2 = 先造**一个连续实心桥体**(截面随桥面弧线连续变化), 再用券洞实体做布尔差集。
      这样桥面与桥腹是光滑连续面, 券洞是真正的圆券通孔。
参数来自 facts.py（单一事实来源）。
"""
import bmesh
import math
from mathutils import Vector, Matrix

# ── 单一事实来源: 数值一律来自 facts.py(本体节, M2.5 冻结) ──
import facts as _F
import geom_math as _GM   # D3(P2-T2 修复轮 2026-10-07): 纵剖/收分纯数学单源, 本文件一行委托
BRIDGE_LEN, N_SPAN = _F.BRIDGE_LEN, _F.N_SPAN
DECK_UP_W, DECK_DOWN_W = _F.DECK_UP_W, _F.DECK_DOWN_W
SPRINGER = _F.SPRINGER
ARCH_RATIO = _F.ARCH_RATIO
RING_T = _F.RING_T
PIER_W = _F.PIER_W
PIER_W_INT = list(_F.PIER_W_INT)   # 六审四刀#2: 逐墩宽度表(中央收窄/两端渐厚), facts 单一来源
PIER_W_C, PIER_W_E = _F.PIER_W_C, _F.PIER_W_E
PIER_MAIN_W = _F.PIER_MAIN_W
PIER_FOUND_W = _F.PIER_FOUND_W
PIER_MAIN_W_C = _F.PIER_MAIN_W_C
PIER_FOUND_W_C = _F.PIER_FOUND_W_C
BRIDGE_ABUT = _F.BRIDGE_ABUT   # 尺寸决策只在 facts 一处做(T2b 归因后改); 生成器纯消费
SPAN_DISTINCT = list(_F.SPAN_DISTINCT)   # G1 更名: '半跨'语义数学上不可能(9值×2-1=17孔)
DECK_Z_END, DECK_Z_TOP = _F.DECK_Z_END, _F.DECK_Z_TOP
from assumptions import BODY_BOTTOM, MESH_TOL, VOID_CUT_MARGIN, VOID_CUT_WIDTH_K   # G1 分家: 建模假定/判据参数不属 facts
SEG = 40
NSEG_X = 240            # 桥体纵向分段(高密度 -> 光滑)
NSEG_ARC = 40           # 券洞圆弧分段
SPRING_BASE = SPRINGER  # 起拱线(中央孔) [M19] 仅存兼容锚, 逐孔真值走 arch_springer_z(i)
spandrel = _F.spandrel   # [M19] 逐孔拱肩厚剖面(单一数据源 facts.spandrel)


def arch_crown_z(i):
    """D3 委托: 公式单源 geom_math.arch_crown_z(语义逐位不变, core_hash 硬门)。"""
    return _GM.arch_crown_z(i)


def arch_rise_ratio(i):
    """矢跨比剖面: 消费 facts.rise_ratio(单一数据源, 六审四刀#1)。"""
    return _F.rise_ratio(i)


def arch_rise(i):
    return _GM.arch_rise(i)


def arch_springer_z(i):
    """D3 委托: 公式单源 geom_math.arch_springer_z(第 i 孔起拱线 = 冠 - 矢高)。"""
    return _GM.arch_springer_z(i)


SPANS = list(_GM.SPANS)


# [M14 归一] 两圆心尖拱纯数学移至 facts(与 PIER_W_INT 同模式: 规则即数据,
# qa_bridge 纯数据侧可无 bmesh 消费同一实现, 杜绝第二套公式失同步)。
arch_e = _F.arch_e
_arc_pair = _F._arc_pair
arch_z = _F.arch_z
arch_dzdx = _F.arch_dzdx
arch_signed_r = _F.arch_signed_r
CROWN_BLUNT_K, CROWN_BLUNT_CAP = _F.CROWN_BLUNT_K, _F.CROWN_BLUNT_CAP


def pier_w(i):
    """六审四刀#2: 第 i 内墩(i=1..16, 1-based)宽度。
    中央(i=8,9)=2.27 收窄 -9.2%, 端内墩(i=1,16)=2.73 渐宽 +9.2%, 线性渐变,
    严格轴对称; 16 墩之和恒等 (N_SPAN-1)*PIER_W=40.0 —— 总桥长严格守恒 BRIDGE_LEN=150.0。
    数据在 facts.PIER_W_INT(单一来源), 生成器纯消费; qa_bridge.derive 消费同一张表
    (规则即数据, 两处不存在可失同步的第二套公式)。"""
    return PIER_W_INT[i - 1]


PIER_X = list(_GM.PIER_X)   # D3 委托: 累加规则+桥长闭合断言单源 geom_math(逐位同表)


def deck_z(x):
    """桥面标高(抛物线母曲线, 中央最高): D3 委托, 公式单源 geom_math.deck_z
    (历史反向事故的防再发自检随公式迁入 geom_math, 导入即验)。"""
    return _GM.deck_z(x)


def build_body_bm():
    """连续实心桥体: 顶面随桥面弧线, 底面到水下, 侧面线性收分。"""
    bm = bmesh.new()
    x0 = -BRIDGE_LEN / 2.0
    rows = []
    for s in range(NSEG_X + 1):
        x = x0 + BRIDGE_LEN * s / NSEG_X
        zt = deck_z(x)
        ring = []
        for k in range(4):
            # 四角(逆时针): 左下(-y,z_bot) 右下 右上 左上
            if k == 0:   yy, zz = -1.0, BODY_BOTTOM
            elif k == 1: yy, zz =  1.0, BODY_BOTTOM
            elif k == 2: yy, zz =  1.0, zt
            else:        yy, zz = -1.0, zt
            hw = _GM.width_at(x, zz)   # D3 委托: 收分公式单源 geom_math(逐位同式)
            ring.append(bm.verts.new((x, yy * hw, zz)))
        rows.append(ring)
    for s in range(NSEG_X):
        a, b = rows[s], rows[s + 1]
        bm.faces.new((a[0], a[1], b[1], b[0]))     # 底
        bm.faces.new((a[3], b[3], b[2], a[2]))     # 顶(桥面)
        bm.faces.new((a[1], a[2], b[2], b[1]))     # +y 侧
        bm.faces.new((a[0], b[0], b[3], a[3]))     # -y 侧
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.normal_update()
    return bm


def build_void_bm():
    """17 个券洞的挖除体: 竖直半圆截面沿 y 拉伸的实体(挖完即成贯通券洞)。

    截面 = 下部矩形(洞身, z: 水下 -> 起拱线) + 上部半圆(券, z: 起拱线 -> 券顶+RING_T)
    沿 y 方向拉伸穿过整个桥体宽度, 保证布尔切穿。
    """
    bm = bmesh.new()
    for i in range(N_SPAN):
        span = SPANS[i]
        xc = (PIER_X[i] + PIER_X[i + 1]) / 2.0
        a = span / 2.0
        b = arch_rise(i)   # M12 P0-2: 矢高剖面(中央高/端矮)
        springer = arch_springer_z(i)
        w = DECK_DOWN_W * VOID_CUT_WIDTH_K   # 贯通系数外置 assumptions(与 SPANDREL_C 数值巧合, no_literals 锁)
        # 截面 = 下部竖直边墙(矩形基座) + 上部半圆券。半圆严格从 SPRINGER 起,
        # 不允许在券圈内部多出一段直边(GPT v4 扣分点)。
        # 闭合轮廓: 逆时针封闭无自相交
        # 底左 -> 底右 -> 右起拱点 -> 沿圆弧到左起拱点 -> 闭合回底左
        prof = [
            (xc - a, BODY_BOTTOM - 0.8),
            (xc + a, BODY_BOTTOM - 0.8),
            (xc + a, springer),
        ]
        for k in range(1, NSEG_ARC):
            xx = xc + a - 2.0 * a * k / NSEG_ARC
            prof.append((xx, arch_z(xx, xc, springer, a, b)))
        prof.append((xc - a, springer))
        n = len(prof)

        def hw_at(z):
            """该高度处桥体半宽 + 穿透余量 VOID_CUT_MARGIN(assumptions, 0.60m):
            确保切刀完全贯穿前后双侧收分墙面; 自相交轮廓修复后大余量不再产生残面横杠。
            D3 委托: 收分公式单源 geom_math.width_at(xc, z)(逐位同式)。"""
            return _GM.width_at(xc, z) + VOID_CUT_MARGIN

        A = [bm.verts.new((px, -hw_at(pz), pz)) for px, pz in prof]
        B = [bm.verts.new((px,  hw_at(pz), pz)) for px, pz in prof]
        for k in range(n):
            k2 = (k + 1) % n
            try: bm.faces.new((A[k], A[k2], B[k2], B[k]))     # 侧壁
            except ValueError: pass
        try: bm.faces.new(list(reversed(A)))                     # -y 端面
        except ValueError: pass
        try: bm.faces.new(B)                                     # +y 端面
        except ValueError: pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.normal_update()
    return bm


if __name__ == "__main__":
    bd = build_body_bm()
    vd = build_void_bm()
    print("桥体 verts=%d faces=%d" % (len(bd.verts), len(bd.faces)))
    print("挖除体 verts=%d faces=%d" % (len(vd.verts), len(vd.faces)))
    xs = [v.co.x for v in bd.verts]
    zs = [v.co.z for v in bd.verts]
    print("桥体 x %.3f..%.3f  z %.2f..%.2f" % (min(xs), max(xs), min(zs), max(zs)))
    tot = sum(SPANS) + sum(pier_w(i) for i in range(1, N_SPAN)) + 2 * BRIDGE_ABUT
    # (N_SPAN-1) 口径 = T2b 终审: 17 孔之间是 16 墩。旧版写死 16 正是当年
    # "-2.50m 假闭合差"的数字形状(facts 改孔数时这里会静默失配), 终审 I14 改为拓扑式。
    # 六审四刀#2: 内墩宽改逐墩剖面, 闭合校验必须按实际表求和(不再假定恒定 PIER_W)。
    print("闭合校验 %.2f (须 %.2f)" % (tot, BRIDGE_LEN))
    assert abs(tot - BRIDGE_LEN) < 0.01
    half = BRIDGE_LEN / 2.0
    assert abs(max(xs)) <= half + 0.001 and abs(min(xs)) >= -half - 0.001
    print("GEOM2_OK")
