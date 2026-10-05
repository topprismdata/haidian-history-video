# -*- coding: utf-8 -*-
"""桥头靠山兽 v7(beasts2): 前探蹲坐+火焰瓣脊镇桥兽, 真拍重雕批(2026-10-05)。

历史依据(实拍 17_Arch_Bridge_Statue_over_Kunming_Lake_(3627588283) 剪影实证,
六审第五刀): 头前伸/吻近水平(额-鼻-嘴水平轮廓强), 颈斜向后上, 胸削瘦,
前腿直撑, 躯干向后拉长(前探动势); 背脊=7 片火焰瓣——有尖/每层向后倒伏/
前后层叠/瓣间凹口/大小递变/棱面硬轮廓(废 v6 圆椭球泡"葡萄脊");
云缘两侧披鬃顺披; 尾卷贴体侧后腿旁; 长方石座保留。
废 v4 高颈直立坐犬态 / v5 伏卧前探+单片巨卷 / v6 蹲坐昂首+圆泡云脊。

交付形态: beast_bm(size, variant, seed) -> 单只水密 bmesh; place_beasts(spots) ->
4 个 linked duplicate 共享 NVARIANTS 套 mesh。variant 0 张口 / 1 含珠微合。
Python 3.9 兼容(禁 match / X|None 注解)。
"""
import bmesh
import math

import bpy
from mathutils import Matrix, Vector

_CACHE = {}
NVARIANTS = 2

_SEG, _RING = 18, 10
_SEG_S, _RING_S = 14, 8
_SEG_M, _RING_M = 12, 7


def _ell(c, r, seg=_SEG, ring=_RING, rot_x=0.0, rot_y=0.0, rot_z=0.0):
    """闭合椭球(独立 bmesh)。极点扇面收口, 保证水密; 支持绕心旋转(鬃瓦/脊棱定向)。"""
    cx, cy, cz = c
    rx, ry, rz = r
    R = (Matrix.Rotation(rot_x, 3, 'X') @ Matrix.Rotation(rot_y, 3, 'Y')
         @ Matrix.Rotation(rot_z, 3, 'Z'))
    bm = bmesh.new()
    pt = R @ Vector((0.0, 0.0, rz))
    pb = R @ Vector((0.0, 0.0, -rz))
    top = bm.verts.new((pt.x + cx, pt.y + cy, pt.z + cz))
    bot = bm.verts.new((pb.x + cx, pb.y + cy, pb.z + cz))
    rows = []
    for i in range(1, ring):
        phi = math.pi * i / ring
        sp, cp = math.sin(phi), math.cos(phi)
        rows.append([])
        for j in range(seg):
            p = R @ Vector((rx * sp * math.cos(2 * math.pi * j / seg),
                            ry * sp * math.sin(2 * math.pi * j / seg),
                            rz * cp))
            rows[-1].append(bm.verts.new((p.x + cx, p.y + cy, p.z + cz)))
    for j in range(seg):
        bm.faces.new((top, rows[0][j], rows[0][(j + 1) % seg]))
        bm.faces.new((bot, rows[-1][(j + 1) % seg], rows[-1][j]))
    for i in range(len(rows) - 1):
        for j in range(seg):
            bm.faces.new((rows[i][j], rows[i + 1][j],
                          rows[i + 1][(j + 1) % seg], rows[i][(j + 1) % seg]))
    for f in bm.faces:
        f.smooth = True
    return bm


def _box(c, s, rot_y=0.0, rot_x=0.0, rot_z=0.0):
    """闭合盒(独立 bmesh), 支持绕 Y/X/Z 旋转(片状鬃/S 尾带定向)。"""
    cx, cy, cz = c
    sx, sy, sz = (v / 2.0 for v in s)
    R = (Matrix.Rotation(rot_x, 3, 'X') @ Matrix.Rotation(rot_y, 3, 'Y')
         @ Matrix.Rotation(rot_z, 3, 'Z'))
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
    for f in bm.faces:
        f.smooth = True
    return bm


def _frustum(c, s, tx=1.0, tz=1.0, rot_y=0.0, rot_x=0.0):
    """闭合楔形棱台(独立 bmesh)。+X 端面 y/z 缩 tx(前窄后宽), 顶面 x/y 缩 tz(楔形上收)。"""
    cx, cy, cz = c
    sx, sy, sz = (v / 2.0 for v in s)
    R = Matrix.Rotation(rot_x, 3, 'X') @ Matrix.Rotation(rot_y, 3, 'Y')
    bm = bmesh.new()
    vs = []
    for x in (-sx, sx):
        for y in (-sy, sy):
            for z in (-sz, sz):
                p = Vector((x, y, z))
                if x > 0.0:
                    p.y *= tx
                    p.z *= tx
                if z > 0.0:
                    p.x *= tz
                    p.y *= tz
                p = R @ p
                vs.append(bm.verts.new((p.x + cx, p.y + cy, p.z + cz)))
    for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1),
              (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
        bm.faces.new([vs[k] for k in f])
    for f in bm.faces:
        f.smooth = True
    return bm


def _blade(c, h, w, t, rot_y=-0.10):
    """火焰瓣(独立 bmesh): 底环 + 内收腰环 + 后掠尖锋 + 前埋钝底。

    腰环(0.70h)收至 0.55w → 瓣宽厚保持到中上段、末 30% 收尖(宽瓣尖锋,
    前后棱斜率递增=内凹火焰卷曲); 尖锋后掠 0.16h(合成顶点 ≈ 环心 +
    (-0.259h, +0.979h)); 钝底下沉 0.18h 前埋 0.06h, 令环刃整条埋入
    背脊体块(防切线退化/防瓣底悬丝)。
    """
    cx, cy, cz = c
    R = Matrix.Rotation(rot_y, 3, 'Y')
    bm = bmesh.new()
    ring, waist = [], []
    for j in range(6):
        a = math.pi * j / 3.0
        ca, sa = math.cos(a), math.sin(a)
        p = R @ Vector((w * ca, t * sa, 0.0))
        ring.append(bm.verts.new((p.x + cx, p.y + cy, p.z + cz)))
        q = R @ Vector((0.55 * w * ca - 0.112 * h, 0.62 * t * sa, 0.70 * h))
        waist.append(bm.verts.new((q.x + cx, q.y + cy, q.z + cz)))
    tp = R @ Vector((-0.16 * h, 0.0, h))
    bt = R @ Vector((0.06 * h, 0.0, -0.18 * h))
    va = bm.verts.new((tp.x + cx, tp.y + cy, tp.z + cz))
    vb = bm.verts.new((bt.x + cx, bt.y + cy, bt.z + cz))
    for j in range(6):
        k = (j + 1) % 6
        bm.faces.new((vb, ring[k], ring[j]))
        bm.faces.new((ring[j], ring[k], waist[k], waist[j]))
        bm.faces.new((waist[j], waist[k], va))
    return bm


def _sculpt_parts(variant):
    """前探蹲坐式靠山兽部件(单位高 1.0, 朝 +X)。返回 (P, N, F)。

    六审第五刀(2026-10-05, GPT 六审: 背脊整条重画+身体前探动势, 实拍
    17_Arch_Bridge_Statue_over_Kunming_Lake_(3627588283) 剪影实证):
    1. 背脊=7 片火焰瓣 _blade(六棱环+后掠尖锋+钝底埋背): 有尖/每层向后
       倒伏/前后层叠/瓣间深凹口/大小递变(中背最高≈头顶)/棱面硬轮廓;
       尖序 x 0.235→-0.58, 尖高 0.79→0.82(峰)→0.56。废 v6 圆椭球泡脊。
    2. 身体前探: 头前送+0.065(吻端至 0.70), 吻轴近水平(rot_y -0.21≈+12°,
       额-鼻-嘴水平轮廓强), 颈斜向后上(rot_y -0.35), 胸削瘦(rx 0.19→0.16)
       且前移, 躯干后拉(臀球 -0.30→-0.335, 胯-肩跨距 +16%), 前腿更直立
       (~4°), 整体降低(冠顶 0.953→0.857)。
    体块=椭球/盒(rot_y 定向: 负角 +X 端上仰/顶部向后倒伏, 正角相反);
    火焰瓣/披鬃/云/尾=C 壳先并再总并(瓣环刃/鬃锚/尾根均深埋体块保连通);
    五官=负刀 crease+后并凸件。剪影验收: 背脊锯齿锐形(尖+凹口, 无球轮廓)/
    头前伸吻水平/胸瘦腿直/瓣尖≤头顶 1.2×/尾贴腿侧。
    """
    P, N, F = [], [], []
    C = []

    def add(bm, lst=None):
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bm.normal_update()
        (lst if lst is not None else P).append(bm)

    def ell(c, r, seg=_SEG, ring=_RING, rot_x=0.0, rot_y=0.0, rot_z=0.0,
            carve=False):
        add(_ell(c, r, seg, ring, rot_x=rot_x, rot_y=rot_y, rot_z=rot_z),
            C if carve else None)

    def blade(c, h, w, t, rot_y=-0.10, carve=True):
        add(_blade(c, h, w, t, rot_y=rot_y), C if carve else None)

    def box(c, s, rot_y=0.0, rot_x=0.0, rot_z=0.0):
        add(_box(c, s, rot_y, rot_x, rot_z))

    def neg(bm):
        add(bm, N)

    def fin(bm):
        add(bm, F)

    hy = 0.0 if variant == 0 else 0.012
    tsy = 1.0 if variant == 0 else -1.0

    # 1. 长方石座(保留 v5)
    box((-0.09, 0, 0.042), (1.55, 0.58, 0.095))

    # 2. 前探躯干: 臀球后拉落座 + 腰腹拉长 + 胸削瘦前移 + 肩丘(头前伸支点)
    ell((-0.335, 0, 0.255), (0.20, 0.205, 0.185))   # 臀球(沉入座面, 顶 0.44)
    ell((-0.07, 0, 0.32), (0.22, 0.20, 0.13))       # 腰腹(腹线 0.19 上收)
    ell((0.175, 0, 0.375), (0.16, 0.195, 0.17))     # 挺胸(削瘦: 底0.205顶0.545)
    ell((0.27, 0, 0.50), (0.115, 0.18, 0.115))      # 肩丘(颈基)
    ell((0.30, 0, 0.55), (0.10, 0.115, 0.10), rot_y=-0.35)  # 咽喉填充(颏-胸桥)
    # 2b. 后肢折叠: 大腿 + 飞节 + 前伸后爪 + 三趾(贴体侧, 随臀后拉 -0.03)
    for sy in (1, -1):
        ell((-0.31, sy * 0.15, 0.19), (0.13, 0.085, 0.115))
        ell((-0.16, sy * 0.16, 0.135), (0.075, 0.06, 0.08))
        box((-0.04, sy * 0.155, 0.105), (0.16, 0.11, 0.05))
        for ty in (-0.032, 0.002, 0.036):
            ell((0.045, sy * 0.155 + ty, 0.10), (0.03, 0.016, 0.022),
                _SEG_S, _RING_S)

    # 3. 前肢直撑(更直立 ~4°, 上端斜入削瘦胸底) + 宽爪 + 三趾
    for sy in (1, -1):
        ell((0.32, sy * 0.135, 0.27), (0.08, 0.075, 0.13))
        ell((0.33, sy * 0.14, 0.15), (0.068, 0.075, 0.095))
        box((0.345, sy * 0.145, 0.10), (0.17, 0.13, 0.052))
        for ty in (-0.036, 0.002, 0.040):
            ell((0.435, sy * 0.145 + ty, 0.098), (0.034, 0.018, 0.025),
                _SEG_S, _RING_S)

    # 4. 头前伸: 颈斜向后上(-0.35), 吻轴近水平(-0.21≈+12°), 吻加长前送;
    #    额-鼻-嘴一线 z 0.775→0.815 水平轮廓强; 颏须垂桥接胸
    ell((0.315, 0, 0.58), (0.10, 0.12, 0.115), rot_y=-0.35)        # 颈
    ell((0.365, hy, 0.72), (0.13, 0.14, 0.12))                     # 颅
    ell((0.352, hy, 0.812), (0.108, 0.14, 0.045), rot_y=-0.15,
        carve=True)                                                # 冠盖
    ell((0.44, hy, 0.775), (0.095, 0.12, 0.038), rot_y=-0.19)      # 额檐(眉上收)
    ell((0.52, hy, 0.79), (0.105, 0.10, 0.06), rot_y=-0.21)        # 鼻梁
    ell((0.615, hy, 0.80), (0.06, 0.085, 0.048), rot_y=-0.21)      # 吻端
    ell((0.668, hy, 0.815), (0.032, 0.058, 0.028), rot_y=-0.21)    # 鼻镜
    for sy in (1, -1):
        ell((0.66, hy + sy * 0.05, 0.805), (0.026, 0.026, 0.022),
            _SEG_S, _RING_S)                                       # 鼻翼
        ell((0.445, hy + sy * 0.10, 0.72), (0.07, 0.055, 0.055))   # 颊垫
    ell((0.49, hy, 0.715), (0.10, 0.085, 0.05), rot_y=-0.21)       # 下颌(加深, 存活于口裂下缘)
    ell((0.39, hy, 0.645), (0.075, 0.08, 0.075), rot_y=-0.45,
        carve=True)                                                # 颏须
    for sy in (1, -1):
        ell((0.285, hy + sy * 0.10, 0.79), (0.035, 0.026, 0.042),
            _SEG_S, _RING_S, rot_x=sy * -0.4, rot_y=-0.35)         # 贴颅伏耳
        ell((0.445, hy + sy * 0.09, 0.79), (0.05, 0.04, 0.022),
            _SEG_S, _RING_S, rot_x=sy * 0.2, rot_y=-0.21)          # 眉脊

    # 5. 背脊火焰瓣 x7(六审第五刀: 有尖/向后倒伏/前后层叠/瓣间凹口/大小
    #    递变/棱面硬轮廓; rot_y -0.30+尖锋后掠 0.22h → 尖=环心+(-0.506h,
    #    +0.890h), 环刃深埋背线 0.03-0.09, 相邻瓣下半大重叠成瓦叠实心脊,
    #    凹口只落瓣高中部不落底)。废 v6 圆椭球泡脊。
    for (bx, bz, bh, bw, bt) in (
            (0.27, 0.60, 0.20, 0.060, 0.075),    # 项后鬃锋(从头颈后穿出, 尖0.80)
            (0.185, 0.46, 0.326, 0.115, 0.09),   # 尖0.78
            (0.05, 0.39, 0.449, 0.17, 0.11),     # 尖0.83
            (-0.085, 0.40, 0.466, 0.175, 0.115), # 中背峰 尖0.856≈头顶
            (-0.24, 0.39, 0.416, 0.15, 0.105),   # 尖0.80
            (-0.38, 0.385, 0.314, 0.105, 0.085), # 尖0.69(下沉保环刃埋臀)
            (-0.50, 0.33, 0.247, 0.09, 0.075)):  # 尖0.57(臀上收)
        blade((bx, 0, bz), bh, bw, bt)
    ell((-0.545, 0, 0.32), (0.09, 0.13, 0.085), rot_y=0.8, carve=True)  # 臀后垂云
    ell((-0.575, 0, 0.185), (0.085, 0.12, 0.10))                    # 垂云落地
    # 5b. 瓣缘两侧披鬃三对(向后顺披, 锚端嵌入瓣体+体侧双锚) + 头后卷勾
    for sy in (1, -1):
        ell((0.15, sy * 0.10, 0.49), (0.062, 0.05, 0.095),
            _SEG_S, _RING_S, rot_x=sy * 0.3, rot_y=-0.9, carve=True)
        ell((-0.11, sy * 0.10, 0.44), (0.065, 0.05, 0.10),
            _SEG_S, _RING_S, rot_x=sy * 0.3, rot_y=-0.9, carve=True)
        ell((-0.34, sy * 0.095, 0.41), (0.06, 0.048, 0.09),
            _SEG_S, _RING_S, rot_x=sy * 0.3, rot_y=-0.9, carve=True)
        ell((0.297, hy + sy * 0.10, 0.79), (0.04, 0.026, 0.05),
            _SEG_S, _RING_S, rot_y=-1.1, carve=True)               # 头后云卷勾

    # 6. 尾: 贴体侧后腿旁 S 卷, 梢上勾(variant 换侧); 首节锚入臀球,
    #    尾根瓦并壳(保雕饰簇单连通)
    ell((-0.42, tsy * 0.165, 0.30), (0.075, 0.055, 0.075), carve=True)
    tail_anchors = ((-0.44, 0.21, 0.35), (-0.49, 0.245, 0.31),
                    (-0.47, 0.25, 0.14), (-0.335, 0.235, 0.095),
                    (-0.235, 0.22, 0.115), (-0.19, 0.215, 0.17))
    for k in range(15):
        t = k / 14.0 * (len(tail_anchors) - 1)
        i = min(int(t), len(tail_anchors) - 2)
        f = t - i
        a, b = tail_anchors[i], tail_anchors[i + 1]
        cp = tuple(a[d] + (b[d] - a[d]) * f for d in range(3))
        ell((cp[0], tsy * cp[1], cp[2]), (0.034, 0.033, 0.034),
            _SEG_S, _RING_S, carve=True)
    ell((-0.185, tsy * 0.185, 0.21), (0.044, 0.040, 0.044), _SEG_S, _RING_S,
        carve=True)

    # 7. (旧云面波纹刻槽随 v6 圆泡云删除; 火焰瓣以六棱面与凹口承担雕刻语汇)

    # 8. 减法(负刀半凸穿出表面): 口裂楔刀(沿吻轴 -0.21) / 眼窝上割 / 鼻孔
    if variant == 0:
        neg(_frustum((0.585, hy, 0.758), (0.24, 0.052, 0.034),
                     tx=1.25, rot_y=-0.21))
    else:
        neg(_frustum((0.585, hy, 0.760), (0.24, 0.052, 0.024),
                     tx=1.25, rot_y=-0.21))
    for sy in (1, -1):
        neg(_ell((0.475, hy + sy * 0.088, 0.795), (0.038, 0.016, 0.018),
                 _SEG_S, _RING_S))
        neg(_ell((0.682, hy + sy * 0.024, 0.836), (0.012, 0.012, 0.010),
                 _SEG_S, _RING_S))

    # 8b. 后置凸件(负刀后并回): 凸眼珠 / 上唇獠牙(张口) 或 含珠(微合)
    for sy in (1, -1):
        # 眼珠中心须在眼窝负刀(0.475,±0.088,0.795)下外方, 埋入额檐实体,
        # 仅顶面探入窝内(否则整体悬在窝腔中成孤岛, 六审布尔诊断)
        fin(_ell((0.47, hy + sy * 0.096, 0.776), (0.026, 0.028, 0.026),
                 _SEG_S, _RING_S))
    if variant == 0:
        for sy in (1, -1):
            # 獠牙顶端须越过口裂楔刀上缘(x=0.585 处≈0.801)嵌入上颌实体
            fin(_ell((0.585, hy + sy * 0.040, 0.774), (0.015, 0.018, 0.048),
                     _SEG_S, _RING_S, rot_y=-0.21))
    else:
        # 含珠顶端同样越过楔刀上缘嵌入上颌(否则负刀后悬空断连)
        fin(_ell((0.59, hy, 0.776), (0.036, 0.036, 0.036), _SEG_S, _RING_S))

    # 9. 雕饰簇(鬃/云/尾)先并成单一壳, 再与体块一次并(避免切线布尔退化壳)
    if C:
        shell = _union_parts(C)
        bmc = bmesh.new()
        bmc.from_mesh(shell)
        bpy.data.meshes.remove(shell)
        bmesh.ops.recalc_face_normals(bmc, faces=bmc.faces[:])
        bmc.normal_update()
        P.append(bmc)
    return P, N, F

def _bool_step(me, tool_bm, op):
    """单步 EXACT 布尔(并/差), 返回新 mesh(临时对象用后即焚)。"""
    col = bpy.context.scene.collection
    tme = bpy.data.meshes.new("_beast2_tool")
    tool_bm.to_mesh(tme)
    ob = bpy.data.objects.new("_beast2_tool", tme)
    col.objects.link(ob)
    base = bpy.data.objects.new("_beast2_acc", me)
    col.objects.link(base)
    md = base.modifiers.new("op", 'BOOLEAN')
    md.operation = op
    md.solver = 'EXACT'
    md.object = ob
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    new_me = bpy.data.meshes.new_from_object(base.evaluated_get(dg))
    col.objects.unlink(ob)
    bpy.data.objects.remove(ob)
    bpy.data.meshes.remove(tme)
    col.objects.unlink(base)
    bpy.data.objects.remove(base)
    return new_me


def _union_parts(parts):
    """成对平衡树并集。长 EXACT 串链易在切线面处生退化壳, 两两归并降单步复杂度。"""
    level = []
    for pbm in parts:
        me = bpy.data.meshes.new("_beast2_part")
        pbm.to_mesh(me)
        pbm.free()
        level.append(me)
    while len(level) > 1:
        nxt = []
        for i in range(0, len(level) - 1, 2):
            tbm = bmesh.new()
            tbm.from_mesh(level[i + 1])
            nxt.append(_bool_step(level[i], tbm, 'UNION'))
            tbm.free()
        if len(level) % 2:
            nxt.append(level[-1])
        level = nxt
    return level[0]


def _weld(me):
    """焊缝清理(三审: 黑缝/破面): 重合点焊接 + 法线一致化。"""
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    me.update()


def _normalize(bm):
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
    col = bpy.context.scene.collection
    ob = bpy.data.objects.new("_beast2_densify", me)
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


def _mark_smooth(bm, angle_deg=45.0):
    thr = math.radians(angle_deg)
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        if len(e.link_faces) == 2 and e.calc_face_angle(math.pi) > thr:
            e.smooth = False
        else:
            e.smooth = True


def _purge_slivers(bm, min_verts=32):
    """清除布尔退化小碎片(<min_verts 的离连域)。返回 False 表示存在大块断裂。"""
    for v in bm.verts:
        v.tag = False
    comps = []
    for v0 in bm.verts:
        if v0.tag:
            continue
        comp = [v0]
        v0.tag = True
        stack = [v0]
        while stack:
            v = stack.pop()
            for e in v.link_edges:
                o = e.other_vert(v)
                if not o.tag:
                    o.tag = True
                    stack.append(o)
                    comp.append(o)
        comps.append(comp)
    if len(comps) <= 1:
        return True
    comps.sort(key=len, reverse=True)
    for comp in comps[1:]:
        if len(comp) >= min_verts:
            return False
        bmesh.ops.delete(bm, geom=comp, context='VERTS')
    return True


def _build_master(variant):
    pos, negl, finl = _sculpt_parts(variant)
    me = _union_parts(pos)
    bm = bmesh.new()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    _purge_slivers(bm)
    me = bpy.data.meshes.new("_beast2_struct")
    bm.to_mesh(me)
    bm.free()
    for nbm in negl:
        me = _bool_step(me, nbm, 'DIFFERENCE')
    for fbm in finl:
        me = _bool_step(me, fbm, 'UNION')
    _weld(me)
    bm = bmesh.new()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    # M10.1 补洞硬工序: 并集窄缝/切线交留下的穿透洞(四审 22 号图体侧黑缝根因)
    bedges = [e for e in bm.edges if len(e.link_faces) == 1]
    if bedges:
        bmesh.ops.holes_fill(bm, edges=bedges, sides=0)
        bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bedges2 = [e for e in bm.edges if len(e.link_faces) == 1]
    if bedges2:
        # holes_fill 失败的残余开边: voxel remesh 兜底(保证闭合流形, 面数代价可接受)
        tmp_me = bpy.data.meshes.new("_beast2_vox")
        bm.to_mesh(tmp_me)
        bm.free()
        ob = bpy.data.objects.new("_beast2_vox", tmp_me)
        bpy.context.scene.collection.objects.link(ob)
        md = ob.modifiers.new("vox", 'REMESH')
        md.mode = 'VOXEL'
        md.voxel_size = 0.016
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        tmp_me2 = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
        bpy.context.scene.collection.objects.unlink(ob)
        bpy.data.objects.remove(ob)
        bpy.data.meshes.remove(tmp_me)
        bm = bmesh.new()
        bm.from_mesh(tmp_me2)
        bpy.data.meshes.remove(tmp_me2)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bedges2 = [e for e in bm.edges if len(e.link_faces) == 1]
    print("beasts2 boundary edges: %d -> %d" % (len(bedges), len(bedges2)))
    if not _purge_slivers(bm):
        bm.free()
        raise RuntimeError("beasts2: variant %d 母模存在大块离连域(布尔断裂)" % variant)
    ncomp = count_components(bm)
    if ncomp != 1:
        bm.free()
        raise RuntimeError("beasts2: variant %d 母模不水密(连通域=%d>1)" % (variant, ncomp))
    _normalize(bm)
    me2 = bpy.data.meshes.new("_beast2_pre_densify")
    bm.to_mesh(me2)
    bm.free()
    out_me = _densify(me2) if len(me2.polygons) < 20000 else me2
    bm2 = bmesh.new()
    bm2.from_mesh(out_me)
    bpy.data.meshes.remove(out_me)
    _mark_smooth(bm2)
    out = bpy.data.meshes.new("_beast2_master_%d" % variant)
    bm2.to_mesh(out)
    bm2.free()
    return out


def _master(variant):
    if variant not in _CACHE:
        _CACHE[variant] = _build_master(variant)
    return _CACHE[variant]


def dispose_cache():
    for me in _CACHE.values():
        try:
            if me.users == 0:
                bpy.data.meshes.remove(me)
        except ReferenceError:
            pass
    _CACHE.clear()


def beast_bm(size=1.12, variant=0, seed=0):
    """靠山兽 bmesh。原点=底面中心, 朝 +X, 总高=size(含座)。连通域=1(水密)。"""
    bm = bmesh.new()
    bm.from_mesh(_master(variant % NVARIANTS))
    bmesh.ops.scale(bm, vec=(size, size, size), verts=bm.verts)
    return bm


def place_beasts(spots, name="beasts", size=1.12, material=None):
    """4 只靠山兽 linked duplicate 放置。spots: (x, y, z, idx, facing)。"""
    meshes = {}
    obs = []
    for i, sp in enumerate(spots):
        x, y, z, idx, facing = sp
        variant = int(idx) % NVARIANTS
        if variant not in meshes:
            bm = beast_bm(size, variant, seed=variant)
            me = bpy.data.meshes.new("%s_%d" % (name, variant))
            bm.to_mesh(me)
            bm.free()
            if material is not None:
                me.materials.append(material)
            meshes[variant] = me
        ob = bpy.data.objects.new("%s_%d" % (name, i), meshes[variant])
        ob.location = (x, y, z)
        ob.rotation_euler = (0.0, 0.0, 0.0 if facing >= 0 else math.pi)
        bpy.context.collection.objects.link(ob)
        obs.append(ob)
    return obs


def count_components(bm):
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


if __name__ == "__main__":
    for v in range(NVARIANTS):
        bm = beast_bm(1.12, v, seed=v)
        zs = [vt.co.z for vt in bm.verts]
        xs = [vt.co.x for vt in bm.verts]
        ys = [vt.co.y for vt in bm.verts]
        print("variant %d: verts=%d faces=%d comps=%d bbox x[%.3f,%.3f] y[%.3f,%.3f] z[%.3f,%.3f]"
              % (v, len(bm.verts), len(bm.faces), count_components(bm),
                 min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
