# -*- coding: utf-8 -*-
"""望柱蹲狮 v2(lions2): 近景可辨识的明清官式蹲狮, 程序化重雕。

背景: 旧 lions.py 是"球块堆叠"(256 只实体被布尔前各自碎成 ~28 片, 共 7168 连通域,
近景呈无定形白块)。本模块以 2026-10-05 下载的卢沟桥望柱狮照片为造型参考
(refs/lugou_lion/, Wikimedia Commons CC/GFDL, 仅作造型参照不入成片素材):
十七孔桥(1754 清官式园林桥)与卢沟桥同属官式蹲狮谱系, 取其解剖正确性
(大头~40%全高/双层眉弓/凸眼/宽上翘吻/口裂/髭须卷/卷云鬃/阔胸垂饰/并拢前肢+趾/低臀/卷尾),
纹样从简(清式程式化), 不做毛发。

与旧实现的接口差异: lion_bm(H, variant, seed) -> bmesh(原点=柱头面, 朝向 +X,
高=H)签名不变; 场景接入改走 place_lions(spots, material) —— N 个 linked
duplicate 对象共享 2 个 mesh datablock(主狮/幼狮各一, 单位高, H 走对象 scale)。
验收口径(2026-10-05 主控定): 每套 mesh 连通域数=1(水密单狮), unique mesh 数=2,
对象数=2×柱数(256), 单 mesh 面数 >= 4000。每只实例的微差异靠对象 transform
(scale/yaw), 不再逐只改几何(共享 mesh 的代价, 已知限制)。

Python 3.9 兼容(禁 match / X|None 注解)。
"""
import bmesh
import math

import bpy
from mathutils import Matrix

# 母模缓存: {variant: bpy.data.Mesh}(单位高, 归一化)。0 用户网格, dispose 后即弃。
_CACHE = {}

# 4 种主狮 + 4 种幼狮 = 8 套水密母模
NVARIANTS_MAIN = 4
NVARIANTS_CUB = 4
NVARIANTS_TOTAL = 8

# 桥轴坐标系(与 build_scene2.BRIDGE_AXIS_AZ 同源): 幼狮偏移沿 B/N 而非世界 X/Y
_AZ = math.radians(112.0)
_BX, _BY = math.cos(-_AZ), math.sin(-_AZ)
_NX, _NY = -_BY, _BX

_SEG, _RING = 18, 10          # 标准椭球分辨率(面数预算: 20 个标准椭球 ≈ 3960 面)
_SEG_S, _RING_S = 14, 8       # 小件(眼/须/尾/配件)


def _ell(c, r, seg=_SEG, ring=_RING):
    """闭合椭球(独立 bmesh)。极点扇面收口, 保证水密。"""
    cx, cy, cz = c
    rx, ry, rz = r
    bm = bmesh.new()
    top = bm.verts.new((cx, cy, cz + rz))
    bot = bm.verts.new((cx, cy, cz - rz))
    rows = []
    for i in range(1, ring):
        phi = math.pi * i / ring
        sp, cp = math.sin(phi), math.cos(phi)
        rows.append([bm.verts.new((cx + rx * sp * math.cos(2 * math.pi * j / seg),
                                   cy + ry * sp * math.sin(2 * math.pi * j / seg),
                                   cz + rz * cp))
                     for j in range(seg)])
    for j in range(seg):
        bm.faces.new((top, rows[0][j], rows[0][(j + 1) % seg]))
        bm.faces.new((bot, rows[-1][(j + 1) % seg], rows[-1][j]))
    for i in range(len(rows) - 1):
        for j in range(seg):
            bm.faces.new((rows[i][j], rows[i + 1][j],
                          rows[i + 1][(j + 1) % seg], rows[i][(j + 1) % seg]))
    return bm


def _box(c, s, rot_y=0.0):
    """闭合盒(独立 bmesh)。"""
    from mathutils import Vector
    cx, cy, cz = c
    sx, sy, sz = (v / 2.0 for v in s)
    R = Matrix.Rotation(rot_y, 3, 'Y')
    bm = bmesh.new()
    vs = []
    for x in (-sx, sx):
        for y in (-sy, sy):
            for z in (-sz, sz):
                p = R @ Vector((x, y, z))
                vs.append(bm.verts.new((p.x + cx, p.y + cy, p.z + cz)))
    for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1),
              (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
        bm.faces.new([vs[k] for k in f])
    return bm


def _frustum(c_back, s_back, c_front, s_front, tilt_x=0.0):
    """闭合棱台(独立 bmesh): 后矩形截面 s_back=(sy,sz) 在 c_back, 前截面 s_front 在
    c_front, 前截面外缘随 y 附加 tilt_x 绝对 z 偏移(绶带贴胸微倾)。用于楔形鼻梁/绶带垂饰。"""
    bm = bmesh.new()
    v = []
    for k, (cc, ss) in enumerate(((c_back, s_back), (c_front, s_front))):
        sy, sz = (vv / 2.0 for vv in ss)
        for y in (-sy, sy):
            for z in (-sz, sz):
                tilt = tilt_x * y / sy if (k == 1 and sy) else 0.0
                v.append(bm.verts.new((cc[0], y + cc[1], z + cc[2] + tilt)))
    # v 排列: [back(y-,z-), back(y-,z+), back(y+,z-), back(y+,z+),
    #          front(y-,z-), front(y-,z+), front(y+,z-), front(y+,z+)]
    for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1),
              (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
        bm.faces.new([v[k] for k in f])
    return bm


def _taper(c_bot, s_bot, c_top, s_top):
    """闭合 Z 轴棱台(独立 bmesh): 底截面 s_bot=(sx,sy) 在 c_bot, 顶截面 s_top 在
    c_top。上粗下细直立前肢 / 细棱台幼狮四肢。"""
    bm = bmesh.new()
    v = []
    for cc, ss in ((c_bot, s_bot), (c_top, s_top)):
        sx, sy = (uu / 2.0 for uu in ss)
        for x in (-sx, sx):
            for y in (-sy, sy):
                v.append(bm.verts.new((x + cc[0], y + cc[1], cc[2])))
    for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1),
              (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
        bm.faces.new([v[k] for k in f])
    return bm


def _xform(bm, mat, pivot=(0.0, 0.0, 0.0)):
    """原位仿射变换(部件局部->摆位)。只动顶点坐标, 拓扑不变, 水密性不受影响。"""
    from mathutils import Vector
    p = Vector(pivot)
    for vv in bm.verts:
        vv.co = mat @ (vv.co - p) + p
    return bm


def _mane_band(cy=0.0, cz=0.705, nflute=12, naz=64, xs=(0.075, 0.130, 0.175, 0.215),
               base=(0.110, 0.185, 0.185, 0.156), amp=(0.004, 0.022, 0.022, 0.012),
               r_in=0.105):
    """实心波浪鬃环(独立 bmesh): 绕头轴(X)的桶形鬃领, 外缘 nflute 圆脊放射层片,
    脊圆谷尖、谷隐入颅内(借颅面包埋)成叠压层片; 逐脊微噪声破机械感。
    内壁 r_in 深埋颅内, 前后环面封口, 全水密。替代"球串鬃/贴片鬃"。"""
    bm = bmesh.new()
    rows = []
    for li in range(4):
        row = []
        for j in range(naz):
            az = 2.0 * math.pi * j / naz
            s = math.sin(nflute * az + li * 0.12)
            lobe = (s if s > 0.0 else 0.0) ** 0.6          # 圆脊埋谷
            r = (base[li] + amp[li] * lobe
                 + 0.004 * math.sin(7.3 * j + li * 2.1))   # 逐脊微噪声
            row.append(bm.verts.new((xs[li], cy + r * math.cos(az), cz + r * math.sin(az))))
        rows.append(row)
    rin = []
    for x in (xs[0], xs[3]):
        row = []
        for j in range(naz):
            az = 2.0 * math.pi * j / naz
            row.append(bm.verts.new((x, cy + r_in * math.cos(az), cz + r_in * math.sin(az))))
        rin.append(row)
    for li in range(3):                                   # 外缘波浪面
        for j in range(naz):
            j2 = (j + 1) % naz
            bm.faces.new((rows[li][j], rows[li][j2], rows[li + 1][j2], rows[li + 1][j]))
    for j in range(naz):                                  # 内壁(深埋颅内)
        j2 = (j + 1) % naz
        bm.faces.new((rin[0][j2], rin[0][j], rin[1][j], rin[1][j2]))
    for j in range(naz):                                  # 前/后环面封口
        j2 = (j + 1) % naz
        bm.faces.new((rows[0][j], rows[0][j2], rin[0][j2], rin[0][j]))
        bm.faces.new((rows[3][j2], rows[3][j], rin[1][j], rin[1][j2]))
    return bm


def _sculpt_adult_parts(acc):
    """官式蹲狮部件(单位坐标: 朝 +X, 高 1.0)。v5 重雕(九审"造型语言"整改):
    按颐和园十七孔桥实拍(refs/community_photos_details/ 6+ 张)量纲重设全身:
    头+鬃区高 ≈0.55H(颅顶鬃 z≈1.0, 下颏 z≈0.52), 鬃环外径 ±0.27;
    躯干低伏紧凑: 胸拱底 z≈0.18, 肩肘最宽 ±0.28, 臀球顶 z≈0.48(远低于头);
    前肢粗短立柱(高 0.35H, 单腿宽 0.15H)+ 前扑大爪; 后肢折叠(臀球+伏地后爪);
    面部去卡通: 隆眉横檐 + 半嵌鼓眼(无黑珠) + 宽扁吻 + 低位上挑口裂(随吻面作曲)
    + 颊部鼓凸融入鬃; 鬃 14 齿波浪领垂胸, 额头压扁双卷。
    返回 (pos, neg, final):
    pos 先布尔并, neg 再布尔减(口裂/鼻孔/眼睑刻/趾缝——均开口于表面不穿透),
    final 最后并入(眼睑凸片)。全部闭合体块, 深互渗保证连通域=1。"""
    P, N, F = [], [], []

    def add(bm, lst):
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bm.normal_update()
        lst.append(bm)

    def ell(c, r, seg=_SEG, ring=_RING, lst=None):
        add(_ell(c, r, seg, ring), P if lst is None else lst)

    def box(c, s, rot=0.0):
        add(_box(c, s, rot), P)

    def neg_ell(c, r):
        add(_ell(c, r, _SEG_S, _RING_S), N)

    def fin_ell(c, r):
        add(_ell(c, r, _SEG_S, _RING_S), F)

    # ── 底垫(薄削角板, 替旧"光面方盒"座: 只垫不座, 高 0.048) ──
    add(_taper((0.0, 0, 0.004), (0.82, 0.60),
               (0.0, 0, 0.048), (0.76, 0.55)), P)
    # ── 后躯: 低臀球 + 腰背填充 + 折叠后肢(飞节+前伏后爪) ──
    ell((-0.24, 0, 0.26), (0.20, 0.215, 0.22))
    ell((-0.05, 0, 0.40), (0.19, 0.245, 0.155))                # 腰背(鬃下顺坡)
    for sy in (1, -1):
        ell((-0.13, sy * 0.16, 0.10), (0.075, 0.055, 0.10))    # 飞节
        ell((0.015, sy * 0.155, 0.05), (0.125, 0.062, 0.05))   # 后爪(前伏贴地)
    # ── 胸: 深而宽, 底缘 0.18 成胸拱(幼狮栖拱下); 肩肘外凸 ──
    ell((0.10, 0, 0.38), (0.20, 0.26, 0.19))
    for sy in (1, -1):
        ell((0.13, sy * 0.225, 0.30), (0.055, 0.045, 0.06))    # 肘凸
    # ── 前肢: 粗短立柱(0.35H) + 前扑大爪 + 趾 ──
    for sy in (1, -1):
        add(_taper((0.19, sy * 0.14, 0.02), (0.16, 0.18),
                   (0.185, sy * 0.14, 0.35), (0.18, 0.20)), P)
        ell((0.27, sy * 0.13, 0.05), (0.13, 0.085, 0.06))      # 爪
        for tk in range(4):                                     # 趾(并排小盒)
            box((0.36, sy * 0.13 + (tk - 1.5) * 0.042, 0.06),
                (0.065, 0.034, 0.07))
    # ── 头颈: 颅 + 颈背鬃 + 颔下须髯(下颏-胸过渡) ──
    ell((0.10, 0, 0.73), (0.15, 0.19, 0.155))                  # 颅
    ell((-0.05, 0, 0.58), (0.115, 0.21, 0.175))                # 颈背鬃
    ell((-0.02, 0, 0.72), (0.13, 0.20, 0.19))                  # 鬃后圆枕(圆颅背剪影)
    ell((-0.04, 0, 0.80), (0.15, 0.21, 0.20))                  # 冠后圆枕(去方角)
    ell((0.245, 0, 0.485), (0.075, 0.11, 0.06))                # 须髯(颏下连胸)
    ell((0.30, 0.05, 0.45), (0.024, 0.030, 0.016), _SEG_S, _RING_S)   # 髯卷×3
    ell((0.30, -0.05, 0.45), (0.024, 0.030, 0.016), _SEG_S, _RING_S)
    ell((0.285, 0, 0.425), (0.024, 0.030, 0.016), _SEG_S, _RING_S)
    # ── 面(连续面版, 从鬃环前口探出): 隆眉横檐 / 鼻梁 / 吻 / 颊 / 鼻头 / 下颏 ──
    for sy in (1, -1):                                          # 双弧眉脊(压眼上, 外端下垂)
        add(_frustum((0.215, sy * 0.088, 0.775), (0.095, 0.022),
                     (0.255, sy * 0.092, 0.750), (0.075, 0.014)), P)
    ell((0.235, 0, 0.762), (0.035, 0.045, 0.020), _SEG_S, _RING_S)   # 眉心(印堂)
    add(_frustum((0.24, 0, 0.75), (0.085, 0.024),
                 (0.315, 0, 0.688), (0.118, 0.032)), P)        # 鼻梁(向下展宽)
    ell((0.285, 0, 0.655), (0.085, 0.125, 0.062))              # 吻(宽扁)
    ell((0.345, 0, 0.685), (0.035, 0.075, 0.026))              # 鼻头(扁球)
    for sy in (1, -1):
        ell((0.335, sy * 0.062, 0.668), (0.030, 0.030, 0.020), _SEG_S, _RING_S)  # 鼻翼
        ell((0.235, sy * 0.135, 0.63), (0.055, 0.060, 0.05), _SEG_S, _RING_S)  # 颊
    ell((0.29, 0, 0.565), (0.06, 0.085, 0.045))                # 下颏
    # ── 耳(鬃顶侧微凸) / 额顶双卷(压扁浅浮雕) ──
    for sy in (1, -1):
        ell((0.05, sy * 0.16, 0.90), (0.030, 0.026, 0.032), _SEG_S, _RING_S)
        ell((0.19, sy * 0.052, 0.86), (0.036, 0.042, 0.020), _SEG_S, _RING_S)
    ell((0.20, 0, 0.80), (0.030, 0.034, 0.017), _SEG_S, _RING_S)
    # ── 鬃: 14 齿波浪领(垂胸披肩) + 两肩披鬃(鬃-胸过渡体) ──
    add(_mane_band(cy=0.0, cz=0.73, nflute=12, naz=64,
                   xs=(-0.10, -0.03, 0.045, 0.115),
                   base=(0.17, 0.24, 0.24, 0.205),
                   amp=(0.006, 0.036, 0.036, 0.018), r_in=0.125), P)
    for sy in (1, -1):
        ell((-0.02, sy * 0.20, 0.46), (0.11, 0.10, 0.17))
    # ── 尾: 沿臀后坡 S 卷上扬 + 尾梢团 ──
    tail_anchors = ((-0.31, 0.12, 0.13), (-0.385, 0.145, 0.20), (-0.41, 0.155, 0.285),
                    (-0.375, 0.16, 0.36), (-0.32, 0.162, 0.415))
    for k in range(11):                                  # 逐段插值, 邻距 <= 2r 保连通
        t = k / 10.0 * (len(tail_anchors) - 1)
        i = min(int(t), len(tail_anchors) - 2)
        f = t - i
        a, b = tail_anchors[i], tail_anchors[i + 1]
        cp = tuple(a[d] + (b[d] - a[d]) * f for d in range(3))
        ell(cp, (0.027, 0.025, 0.027), _SEG_S, _RING_S)
    ell((-0.30, 0.165, 0.445), (0.042, 0.038, 0.042), _SEG_S, _RING_S)
    # ── 变体配件: 抱球(左爪下) / 含珠(口内) ──
    if acc == "ball":
        ell((0.28, -0.15, 0.055), (0.055, 0.055, 0.055), _SEG_S, _RING_S)
    else:
        ell((0.352, 0, 0.642), (0.038, 0.038, 0.038), _SEG_S, _RING_S)
    # ── 减法(开口于表面, 不穿透): 口裂(低位上挑, 随吻面走) / 鼻孔×2 /
    #    眼睑上刻×2 / 前爪趾缝×2×3 / 后爪趾缝×2×2 ──
    for k in range(7):                                          # 口裂: 弧随吻面, 端点上挑
        yy = -0.09 + 0.03 * k
        t = (yy / 0.095) ** 2
        zz = 0.612 + 0.028 * t
        xx = 0.285 + 0.085 * math.sqrt(max(0.05, 1.0 - ((zz - 0.655) / 0.062) ** 2)) - 0.018
        neg_ell((xx, yy, zz), (0.028, 0.019, 0.016))
    for sy in (1, -1):
        neg_ell((0.372, sy * 0.032, 0.688), (0.014, 0.015, 0.009))   # 鼻孔(鼻头前坡)
        neg_ell((0.252, sy * 0.09, 0.748), (0.010, 0.028, 0.008))    # 眼睑上刻(眉脊下)
        for ty in (-0.042, 0.0, 0.042):                              # 前爪趾缝
            add(_box((0.365, sy * 0.13 + ty, 0.06), (0.032, 0.008, 0.075)), N)
        for ty in (-0.024, 0.024):                                   # 后爪趾缝
            add(_box((0.115, sy * 0.155 + ty, 0.05), (0.026, 0.006, 0.055)), N)
    # ── 最后并入: 眼球(小鼓眼, 半嵌颅面埋眉下, 无黑珠) ──
    for sy in (1, -1):
        fin_ell((0.245, sy * 0.085, 0.718), (0.018, 0.036, 0.028))
    return P, N, F


def _boolean_chain(pos, neg, final):
    """顺序 EXACT 布尔: pos 依序并 -> neg 依序减 -> final 依序并。
    返回单一水密 bpy mesh(临时对象用后即焚)。neg 刀具须与实体浅交(不穿透)。"""
    col = bpy.context.scene.collection

    def _to_mesh(pbm, i):
        me = bpy.data.meshes.new("_lion2_part_%d" % i)
        pbm.to_mesh(me)
        pbm.free()
        return me

    def _step(base, me, op):
        ob = bpy.data.objects.new("_lion2_tool", me)
        col.objects.link(ob)
        md = base.modifiers.new("b", 'BOOLEAN')
        md.operation = op
        md.solver = 'EXACT'
        md.object = ob
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        new_me = bpy.data.meshes.new_from_object(base.evaluated_get(dg))
        base.modifiers.remove(md)
        old = base.data
        base.data = new_me
        bpy.data.meshes.remove(old)
        col.objects.unlink(ob)
        bpy.data.objects.remove(ob)
        bpy.data.meshes.remove(me)

    base = None
    i = 0
    for lst, op in ((pos, 'UNION'), (neg, 'DIFFERENCE'), (final, 'UNION')):
        for pbm in lst:
            me = _to_mesh(pbm, i)
            i += 1
            if base is None:
                base = bpy.data.objects.new("_lion2_acc", me)
                col.objects.link(base)
                continue
            _step(base, me, op)
    res = base.data
    col.objects.unlink(base)
    bpy.data.objects.remove(base)
    return res


def _normalize(bm):
    """归一化: 高 -> 1.0, 底面 z=0, x/y 居中。"""
    zs = [v.co.z for v in bm.verts]
    zmin, zmax = min(zs), max(zs)
    s = 1.0 / (zmax - zmin)
    bmesh.ops.scale(bm, vec=(s, s, s), verts=bm.verts)
    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    bmesh.ops.translate(bm, verts=bm.verts,
                        vec=(-(min(xs) + max(xs)) / 2.0,
                             -(min(ys) + max(ys)) / 2.0,
                             -min(v.co.z for v in bm.verts)))


def _densify(me):
    """简单细分一次(SUBSURF, SIMPLE: 位移形状零漂移), 返回新 mesh。"""
    col = bpy.context.scene.collection
    ob = bpy.data.objects.new("_lion2_densify", me)
    col.objects.link(ob)
    md = ob.modifiers.new("s", 'SUBSURF')
    md.subdivision_type = 'SIMPLE'
    md.levels = 1
    md.render_levels = 1
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    new_me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    col.objects.unlink(ob)
    bpy.data.objects.remove(ob)
    bpy.data.meshes.remove(me)
    return new_me


def _mark_smooth(bm, angle_deg=40.0):
    """平滑着色 + 按二面角标硬边(等价 auto-smooth): 面全 smooth,
    夹角 > angle_deg 的边标 sharp。消"纸工艺"平 facet 观感, 同时保住
    部件交界的凿刻棱线。"""
    thr = math.radians(angle_deg)
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        if len(e.link_faces) == 2 and e.calc_face_angle(math.pi) > thr:
            e.smooth = False
        else:
            e.smooth = True


def _build_master_adult(acc, mirror):
    pos, neg, final = _sculpt_adult_parts(acc)
    me = _boolean_chain(pos, neg, final)
    bm = bmesh.new()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    ncomp = count_components(bm)
    if ncomp != 1:
        bm.free()
        raise RuntimeError("lions2 adult %s 不水密(连通域=%d)" % (acc, ncomp))
    _normalize(bm)
    if mirror:
        bmesh.ops.scale(bm, vec=(1.0, -1.0, 1.0), verts=bm.verts)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me2 = bpy.data.meshes.new("_lion2_pre_densify")
    bm.to_mesh(me2)
    bm.free()
    out = _densify(me2)
    bm = bmesh.new()
    bm.from_mesh(out)
    bpy.data.meshes.remove(out)
    _mark_smooth(bm)
    out = bpy.data.meshes.new("_lion2_master_%s_%d" % (acc, int(mirror)))
    bm.to_mesh(out)
    bm.free()
    return out




def dispose_cache():
    """释放母模缓存(0 用户网格不留盘)。build_scene2 建完 lions 后调用。"""
    for me in _CACHE.values():
        try:
            if me.users == 0:
                bpy.data.meshes.remove(me)
        except ReferenceError:
            pass
    _CACHE.clear()




def count_components(bm):
    """连通域数(顶点洪泛)。验收口径: 全桥 lions 对象应 == 狮只数。"""
    bm.verts.ensure_lookup_table()
    for v in bm.verts:
        v.tag = False
    n = 0
    for v0 in bm.verts:
        if v0.tag:
            continue
        n += 1
        stack = [v0]
        v0.tag = True
        while stack:
            v = stack.pop()
            for e in v.link_edges:
                o = e.other_vert(v)
                if not o.tag:
                    o.tag = True
                    stack.append(o)
    return n



# ── v3 幼狮母模: 解剖化(躯干/颈/头颅/吻/眉/眼/耳/鬃/四肢/趾/尾), 4 姿态 ──

def _sculpt_cub_parts(kind):
    """幼狮部件(单位高 1.0, 朝 +X)。v5 重雕: 四姿态全部是"贴伏/攀附"语汇,
    供 place_lions 压进母体表面(半嵌浮雕感), 不再是落地独立小狮:
    kind 0 攀爬(前身直立前爪扒母体, 仰头 30°) 1 偎依(胸前仰头 20°)
    2 伏卧(伏母臀/背, 头前探微俯) 3 怀中伏(压扁贴伏, 头外转 35°)。
    造型: 头大(头+鬃区 ≈0.45H)无颈, 躯干横卵, 背平(贴母体), 四肢短粗,
    鬃 8 齿小领。返回 (P, N, F), 全闭合体块深互渗(母模水密 连通域=1)。"""
    P, N, F = [], [], []

    def add(bm, lst):
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bm.normal_update()
        lst.append(bm)

    def ell(c, r, lst=None):
        add(_ell(c, r, _SEG_S, _RING_S), P if lst is None else lst)

    def box(c, s, rot=0.0):
        add(_box(c, s, rot), P)

    def neg_ell(c, r):
        add(_ell(c, r, _SEG_S, _RING_S), N)

    def bpart(bm):
        add(_xform(bm, body_m), P)

    def bneg(bm):
        add(_xform(bm, body_m), N)

    lie = 1.0 if kind == 2 else 0.0          # 伏卧(贴背): 躯干压扁前移
    squash = (1.0, 1.0, 0.75, 0.80)[kind]
    lean = (0.45, 0.10, 0.30, 0.40)[kind]   # 前肢绕底枢轴前摆(0/3 扒, 2 前伸)
    pitch = math.radians((30, 20, -10, -5)[kind])
    yaw = math.radians((0, 0, 0, 35)[kind])
    roll = 0.0

    body_m = Matrix.Diagonal((1.0 + 0.06 * (1.0 - squash), 1.0, squash, 1.0))

    # ── 躯干(横卵, 背平贴母体) + 胸肩(与头直连, 无颈) ──
    bpart(_ell((-0.04, 0, 0.29 - lie * 0.06), (0.225, 0.16, 0.16 - lie * 0.04)))
    bpart(_ell((0.13, 0, 0.32 - lie * 0.05), (0.14, 0.155, 0.17)))
    # ── 头组(局部系建模 -> 姿态矩阵): 大颅直连胸, 大吻, 隆眉, 小鼓眼 ──
    hz = (0.58, 0.60, 0.47, 0.47)[kind]
    hx = (0.15, 0.15, 0.185, 0.185)[kind]
    head_m = (Matrix.Translation((hx, yaw * 0.05, hz))
              @ Matrix.Rotation(roll, 4, 'X')
              @ Matrix.Rotation(-pitch, 4, 'Y')
              @ Matrix.Rotation(yaw, 4, 'Z'))

    def hpart(bm, lst=None):
        add(_xform(bm, head_m), P if lst is None else lst)

    hpart(_ell((0.0, 0, 0.0), (0.15, 0.165, 0.15)))              # 颅
    hpart(_ell((0.105, 0, -0.045), (0.07, 0.095, 0.048)))        # 吻(宽扁)
    hpart(_ell((0.09, 0, -0.10), (0.05, 0.07, 0.028)))           # 下颏
    hpart(_frustum((0.04, 0, 0.075), (0.17, 0.024),              # 隆眉横檐
                   (0.075, 0, 0.058), (0.13, 0.012)))
    for sy in (1, -1):
        hpart(_ell((0.085, sy * 0.052, 0.040), (0.011, 0.020, 0.015)))   # 小鼓眼(半嵌)
        hpart(_ell((-0.03, sy * 0.125, 0.12), (0.028, 0.024, 0.030)))   # 耳
    hpart(_ell((0.075, 0, 0.105), (0.024, 0.028, 0.014)))        # 额卷(压扁)
    hpart(_mane_band(cy=0.0, cz=0.0, nflute=8, naz=40,
                     xs=(-0.10, -0.025, 0.04, 0.095),
                     base=(0.135, 0.19, 0.19, 0.155),
                     amp=(0.006, 0.022, 0.022, 0.011), r_in=0.08))
    # ── 前肢短粗(绕底枢轴前摆: 端头始终衔接胸, 摆向前上作扒附) + 爪 + 趾 ──
    for sy in (1, -1):
        bpart(_xform(_taper((0.19, sy * 0.078, 0.02), (0.065, 0.055),
                            (0.155, sy * 0.078, 0.32), (0.085, 0.065)),
                     Matrix.Rotation(lean, 4, 'Y'), (0.17, sy * 0.078, 0.17)))
    px = 0.18 + 0.03 * (1.0 if kind in (2, 3) else 0.0)
    for sy in (1, -1):
        bpart(_box((px, sy * 0.078, 0.042), (0.11, 0.075, 0.065)))
        for ty in (0.020, 0.0, -0.020):
            bpart(_box((px + 0.042, sy * 0.075 + ty, 0.044), (0.024, 0.016, 0.030)))
    # ── 后腿折叠(短) + 爪 ──
    for sy in (1, -1):
        bpart(_ell((-0.15, sy * 0.105, 0.14 - lie * 0.04), (0.115, 0.05, 0.105)))
        bpart(_box((-0.05, sy * 0.105, 0.045 - lie * 0.02), (0.085, 0.05, 0.05)))
    # ── 尾(短, 贴臀) ──
    ty_o = 0.105
    bpart(_ell((-0.21, ty_o, 0.20 - lie * 0.06), (0.030, 0.024, 0.045)))
    bpart(_ell((-0.215, ty_o + 0.005, 0.27 - lie * 0.07), (0.027, 0.023, 0.040)))
    # ── 减法: 口裂(低位上挑随吻面) + 前肢趾缝(随体姿态) ──
    for k in range(5):
        yy = -0.05 + 0.025 * k
        t = (yy / 0.055) ** 2
        zz = -0.062 + 0.018 * t
        xx = 0.105 + 0.07 * math.sqrt(max(0.04, 1.0 - ((zz + 0.045) / 0.048) ** 2
                                          - (yy / 0.09) ** 2)) - 0.010
        hpart(_ell((xx, yy, zz), (0.016, 0.015, 0.008)), N)
    for sy in (1, -1):
        for ty in (-0.016, 0.016):
            bneg(_box((px + 0.050, sy * 0.075 + ty, 0.047), (0.026, 0.006, 0.030)))
    return P, N, F


def _build_master_cub(kind):
    pos, neg, final = _sculpt_cub_parts(kind)
    me = _boolean_chain(pos, neg, final)
    bm = bmesh.new()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    ncomp = count_components(bm)
    if ncomp != 1:
        bm.free()
        raise RuntimeError("lions2 cub %d 不水密(连通域=%d)" % (kind, ncomp))
    _normalize(bm)
    me2 = bpy.data.meshes.new("_cub_pre_densify")
    bm.to_mesh(me2)
    bm.free()
    out = _densify(me2)
    bm = bmesh.new()
    bm.from_mesh(out)
    bpy.data.meshes.remove(out)
    _mark_smooth(bm)
    out = bpy.data.meshes.new("_cub_master_%d" % kind)
    bm.to_mesh(out)
    bm.free()
    return out


_ADULT_KEYS = (("ball", False), ("ball", True), ("pearl", False), ("pearl", True))


def _master(variant):
    """0..3 成年主狮(抱球/抱球镜像/含珠/含珠镜像), 4..7 幼狮四姿态。"""
    if variant not in _CACHE:
        if variant < 4:
            acc, mir = _ADULT_KEYS[variant]
            _CACHE[variant] = _build_master_adult(acc, mir)
        else:
            _CACHE[variant] = _build_master_cub(variant - 4)
    return _CACHE[variant]


def place_lions(spots, material=None, main_H=0.32, cub_H=0.15):
    """544 只石狮 Linked Duplicates 放置系统 (128 主狮 + 416 幼狮 = 544 狮)。"""
    m_mains = [_master(v) for v in range(NVARIANTS_MAIN)]
    m_cubs = [_master(NVARIANTS_MAIN + v) for v in range(NVARIANTS_CUB)]
    if material is not None:
        for me in (m_mains + m_cubs):
            if material not in me.materials[:]:
                me.materials.append(material)
    col = bpy.context.collection
    objs = []
    for i, (x, y, z, idx, side) in enumerate(spots):
        main_variant = idx % NVARIANTS_MAIN
        yaw0 = (((idx * 13 + side) * 37) % 7 - 3) * 0.02
        o_main = bpy.data.objects.new("lion_adult_%03d_%+d" % (idx, side), m_mains[main_variant])
        o_main.location = (x, y, z)
        o_main.scale = (main_H, main_H, main_H)
        o_main.rotation_euler = (0.0, 0.0, yaw0)
        col.objects.link(o_main)
        objs.append(o_main)
        n_cubs = 4 if i < 32 else 3
        # 幼狮贴伏位(母狮单位系): (u 母体轴向, v 横向×side 朝栏外, z 基高·main_H,
        #  scale_mul, yaw 外转角)。全部深嵌母体表面(扒胸/怀中/伏臀/贴腹),
        # 半露浮雕感 —— 不再落地独立摆放(九审"幼狮像独立玩偶"整改)。
        cub_slots = (
            ( 0.25, 0.140, -0.010, 0.72, 0.35),   # 0 攀爬: 藏母前肢后探首扒胸
            ( 0.37, 0.075, -0.010, 0.62, 0.00),   # 1 怀中伏: 胸拱下双爪间探首(齐爪线)
            (-0.26, 0.210,  0.280, 0.80, 0.95),   # 2 伏臀: 伏母臀侧, 头外转
            (-0.04, 0.300,  0.300, 0.68, 1.30),   # 3 贴伏: 压肩鬃下侧腹(浮雕)
        )
        for c_idx in range(n_cubs):
            u_off, v_off, zu, scale_mul, yaw_c = cub_slots[c_idx]
            d_axis = u_off * main_H
            d_trans = side * v_off * main_H
            wx = x + _BX * d_axis + _NX * d_trans
            wy = y + _BY * d_axis + _NY * d_trans
            cub_var = (idx * 3 + c_idx) % NVARIANTS_CUB
            h = cub_H * scale_mul
            o_cub = bpy.data.objects.new("lion_cub_%03d_%+d_%d" % (idx, side, c_idx), m_cubs[cub_var])
            o_cub.location = (wx, wy, z + zu * main_H)
            o_cub.scale = (h, h, h)
            o_cub.rotation_euler = (0.0, 0.0, yaw0 + side * yaw_c)
            col.objects.link(o_cub)
            objs.append(o_cub)
    return objs


if __name__ == "__main__":
    for v in range(NVARIANTS_TOTAL):
        m = _master(v)
        print("Master %d (%s): faces=%d" % (v, "adult" if v < 4 else "cub", len(m.polygons)))
