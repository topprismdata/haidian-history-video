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

_SEG, _RING = 18, 10          # 标准椭球分辨率(面数预算: 20 个标准椭球 ≈ 3960 面)
_SEG_S, _RING_S = 14, 8       # 小件(眼/须/尾/配件)
_SEG_M, _RING_M = 12, 7       # 鬃毛卷(9 团)


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


def _sculpt_parts(variant):
    """官式蹲狮子部件(单位坐标: 朝 +X, 高 1.0, 全部闭合体块, 深互渗供布尔并)。
    解剖要点见模块 docstring; 坐标即设计值, 注释给近景识别作用。"""
    P = []

    def add(bm):
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bm.normal_update()
        P.append(bm)

    def ell(c, r, seg=_SEG, ring=_RING):
        add(_ell(c, r, seg, ring))

    def box(c, s, rot=0.0):
        add(_box(c, s, rot))

    # ── 柱头接触底垫 + 后座(坐姿读感的根) ──
    box((0.01, 0, 0.012), (0.52, 0.38, 0.030))                 # 底垫(沉 3mm 防 Z 面 coplanar)
    box((-0.17, 0, 0.069), (0.44, 0.36, 0.138))                # 后座垫
    # ── 后躯: 臀大块 + 两侧腿臀 + 折叠后腿轮廓(侧面剪影关键) ──
    ell((-0.17, 0, 0.225), (0.260, 0.200, 0.190))
    ell((-0.15, 0.135, 0.200), (0.210, 0.085, 0.160))
    ell((-0.15, -0.135, 0.200), (0.210, 0.085, 0.160))
    ell((-0.255, 0.112, 0.160), (0.105, 0.065, 0.105), _SEG_S, _RING_S)
    ell((-0.255, -0.112, 0.160), (0.105, 0.065, 0.105), _SEG_S, _RING_S)
    # ── 胸 / 颈(胸前挺 + 颈圈垂饰) ──
    ell((0.145, 0, 0.335), (0.155, 0.185, 0.215))
    ell((0.090, 0, 0.510), (0.135, 0.165, 0.150))
    ell((0.115, 0, 0.470), (0.095, 0.190, 0.048))              # 颈圈带
    box((0.293, 0, 0.400), (0.034, 0.080, 0.100))              # 胸前垂饰(铃/牌)
    # ── 前肢并拢直立 + 爪 + 趾(3591 图正面主特征) ──
    box((0.155, 0.075, 0.185), (0.125, 0.085, 0.370))
    box((0.155, -0.075, 0.185), (0.125, 0.085, 0.370))
    box((0.225, 0.075, 0.040), (0.155, 0.100, 0.086))          # 左前爪
    box((0.225, -0.075, 0.040), (0.155, 0.100, 0.086))         # 右前爪
    for sy in (1, -1):
        for ty in (0.032, -0.032):
            box((0.293, sy * (0.075 + ty), 0.044), (0.036, 0.028, 0.050))   # 趾
    # ── 头: 颅 / 颧颊 / 双层眉弓 / 凸眼 / 宽吻 / 上翘鼻 / 下颌(留缝=口裂) ──
    ell((0.165, 0, 0.705), (0.135, 0.185, 0.145))              # 颅(大头, 头区≈0.40H)
    ell((0.175, 0, 0.630), (0.080, 0.185, 0.095))              # 颧颊
    ell((0.235, 0.060, 0.800), (0.040, 0.045, 0.040), _SEG_S, _RING_S)   # 额顶双卷(左)
    ell((0.235, -0.060, 0.800), (0.040, 0.045, 0.040), _SEG_S, _RING_S)  # 额顶双卷(右)
    for sy in (1, -1):
        box((0.245, sy * 0.082, 0.748), (0.062, 0.085, 0.042))    # 眉弓上层
        box((0.268, sy * 0.080, 0.725), (0.036, 0.080, 0.028))    # 眉弓下层
        ell((0.264, sy * 0.078, 0.704), (0.036, 0.037, 0.036), _SEG_S, _RING_S)  # 凸眼球
    box((0.285, 0, 0.652), (0.100, 0.140, 0.090))              # 宽扁吻
    box((0.325, 0, 0.694), (0.048, 0.088, 0.055))              # 上翘鼻头
    box((0.243, 0, 0.570), (0.135, 0.135, 0.042))              # 下颌(与吻底留 16mm 缝=口裂)
    ell((0.288, 0, 0.546), (0.034, 0.058, 0.044), _SEG_S, _RING_S)       # 下巴须团
    for sy in (1, -1):                                          # 髭须卷(嘴角下垂双卷)
        ell((0.276, sy * 0.100, 0.628), (0.026, 0.034, 0.032), _SEG_S, _RING_S)
        ell((0.262, sy * 0.112, 0.596), (0.024, 0.030, 0.030), _SEG_S, _RING_S)
    # ── 耳(颅顶侧角) ──
    for sy in (1, -1):
        box((0.110, sy * 0.135, 0.840), (0.078, 0.055, 0.060))
    # ── 卷云鬃: 环颅 9 团(顶团最大, 前倾成螺旋), 颈背整圈 + 胸侧披鬃(填喉凹) ──
    for k in range(9):
        th = math.radians(15.0 + k * 32.5)
        rr = 0.175
        rk = 0.058 + 0.014 * math.sin(th)
        cx = 0.095 + 0.050 * math.sin(th) + (0.012 if k % 2 else -0.012)
        ell((cx, rr * math.cos(th), 0.710 + rr * math.sin(th)),
            (rk * 1.25, rk, rk), _SEG_M, _RING_M)
    ell((0.020, 0, 0.620), (0.090, 0.190, 0.115))              # 颈背鬃(连通兜底)
    for sy in (1, -1):                                          # 胸侧披鬃
        ell((0.060, sy * 0.155, 0.500), (0.100, 0.075, 0.140))
    # ── 尾: 沿臀侧 S 卷上扬 + 尾梢团 ──
    for k in range(6):
        t = k / 5.0
        ell((-0.335 + 0.05 * t, 0.115 + 0.015 * t, 0.240 + 0.11 * t),
            (0.026, 0.024, 0.026), _SEG_S, _RING_S)
    ell((-0.285, 0.128, 0.365), (0.038, 0.034, 0.038), _SEG_S, _RING_S)  # 尾梢
    # ── 变体配件: 雄抱绣球 / 雌踏幼狮 ──
    if variant == 0:
        ell((0.300, -0.125, 0.054), (0.052, 0.052, 0.052), _SEG_S, _RING_S)
    else:
        ell((0.252, 0.135, 0.058), (0.072, 0.050, 0.052), _SEG_S, _RING_S)   # 幼狮身
        ell((0.320, 0.135, 0.088), (0.040, 0.038, 0.038), _SEG_S, _RING_S)   # 幼狮头
    return P


def _union_parts(parts):
    """顺序 EXACT 布尔并 -> 单一水密 bpy mesh(临时对象用后即焚)。"""
    col = bpy.context.scene.collection
    base = None
    for i, pbm in enumerate(parts):
        me = bpy.data.meshes.new("_lion2_part_%d" % i)
        pbm.to_mesh(me)
        pbm.free()
        ob = bpy.data.objects.new("_lion2_part_%d" % i, me)
        col.objects.link(ob)
        if base is None:
            base = ob
            continue
        md = base.modifiers.new("u", 'BOOLEAN')
        md.operation = 'UNION'
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


def _build_master(variant):
    parts = _sculpt_parts(variant)
    me = _union_parts(parts)
    bm = bmesh.new()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    _normalize(bm)
    # 布尔并吃掉 ~50% 内部面(深互渗所致), 简单细分补密度(近景棱面减半,
    # 凿感噪声采样更细)。注: 5.2.2 LTS 里 bmesh.ops.subdivide_edges 实测
    # 对任意输入静默无操作(cuts=1 亦然, cube 复现), 故走 SUBSURF(SIMPLE)
    # 修改器 —— 与布尔并同一条 new_from_object 管道, 实测有效且确定。
    me2 = bpy.data.meshes.new("_lion2_pre_densify")
    bm.to_mesh(me2)
    bm.free()
    out = _densify(me2)
    out.name = "_lion2_master_%d" % variant
    return out


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


def _master(variant):
    if variant not in _CACHE:
        _CACHE[variant] = _build_master(variant)
    return _CACHE[variant]


def place_lions(spots, material=None, main_H=0.30, cub_H=0.17,
                cub_dx=-0.10, cub_dy=0.11, cub_dz=-0.02):
    """蹲狮就位: N 个 linked duplicate 对象共享 2 个 mesh datablock。

    口径(2026-10-05 主控定): 单个重复构件用 linked duplicate(mesh 共享,
    每对象自有 transform), 不再把 N 份副本并进一个 bmesh —— 内存/文件不膨胀,
    "狮重做"的回归 diff 只涉及 1 个 mesh 哈希。验收: 单 mesh 连通域=1(水密),
    unique mesh 数=2(主狮变体0 / 柱侧幼狮变体1), 对象数=2×len(spots)。

    就位口径与旧 build_lions_bm 完全一致: 主狮在柱头 (x, y, z),
    幼狮在柱侧 (x-0.10, y+0.11·side, z-0.02)。每对象 scale=H(母模为单位高),
    微yaw ±2.6°(确定性整數式, 补共享 mesh 后失去的单只差异)。
    """
    m_main = _master(0)
    m_cub = _master(1)
    if material is not None:
        for me in (m_main, m_cub):
            if material not in me.materials[:]:
                me.materials.append(material)
    col = bpy.context.collection
    objs = []
    for (x, y, z, idx, side) in spots:
        yaw0 = (((idx * 13 + side) * 37) % 7 - 3) * 0.015   # ±2.6°, 确定性
        o = bpy.data.objects.new("lion_%03d_%+d" % (idx, side), m_main)
        o.location = (x, y, z)
        o.scale = (main_H, main_H, main_H)
        o.rotation_euler = (0.0, 0.0, yaw0)
        col.objects.link(o)
        objs.append(o)
        o2 = bpy.data.objects.new("lioncub_%03d_%+d" % (idx, side), m_cub)
        o2.location = (x + cub_dx, y + cub_dy * side, z + cub_dz)
        o2.scale = (cub_H, cub_H, cub_H)
        o2.rotation_euler = (0.0, 0.0, yaw0 * 0.5)
        col.objects.link(o2)
        objs.append(o2)
    return objs


def dispose_cache():
    """释放母模缓存(0 用户网格不留盘)。build_scene2 建完 lions 后调用。"""
    for me in _CACHE.values():
        try:
            if me.users == 0:
                bpy.data.meshes.remove(me)
        except ReferenceError:
            pass
    _CACHE.clear()


def _jitter(bm, H, seed):
    """seed 确定性低频噪声(凿石感): 幅度 0.55%H << 特征尺度, 接地圈只上不移。"""
    from math import sin, pi
    import random
    n = len(bm.verts)
    if n == 0:
        return
    h = (seed * 2654435761 + 1013904223) & 0x7FFFFFFF
    rng = random.Random(h)
    fr = [rng.uniform(2.5, 7.5) for _ in range(3)]
    fr2 = [rng.uniform(2.5, 7.5) for _ in range(3)]
    ph = [rng.uniform(0.0, 2.0 * pi) for _ in range(6)]
    amp = 0.0055 * H
    bm.normal_update()
    for v in bm.verts:
        x, y, z = v.co
        wx, wy, wz = x / H, y / H, z / H
        d = (sin(fr[0] * wx + ph[0]) + sin(fr[1] * wy + ph[1]) + sin(fr[2] * wz + ph[2])
             + 0.4 * (sin(fr2[0] * wx * 2.9 + ph[3])
                      + sin(fr2[1] * wy * 2.3 + ph[4])
                      + sin(fr2[2] * wz * 3.3 + ph[5])))
        d *= amp / 4.2                      # |d| 上界归一
        if wz < 0.04 and d < 0.0:
            d = 0.0                         # 底圈只抬防"悬爪"
        v.co += v.normal * d
    # 每只微差: 宽度 ±2.5% + 偏航 ±3°(绕自身原点, 就位平移由调用方做)
    m = Matrix.Rotation((rng.random() - 0.5) * 0.105, 4, 'Z') @ \
        Matrix.Diagonal((1.0, 1.0 + (rng.random() - 0.5) * 0.05, 1.0, 1.0))
    bmesh.ops.transform(bm, matrix=m, verts=bm.verts)
    bm.normal_update()


def lion_bm(H=0.30, variant=0, seed=0):
    """蹲狮 bmesh。原点=柱头面中心, 朝 +X, 总高 H, 宽~0.42H, 长~0.6H。
    variant: 0=雄狮抱绣球, 1=雌狮踏幼狮。seed 仅驱动凿感噪声(不改变解剖)。"""
    bm = bmesh.new()
    bm.from_mesh(_master(variant))
    bmesh.ops.scale(bm, vec=(H, H, H), verts=bm.verts)
    _jitter(bm, H, seed)
    return bm


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


if __name__ == "__main__":
    for v in (0, 1):
        bm = lion_bm(0.30, v, seed=v * 7)
        zs = [vt.co.z for vt in bm.verts]
        xs = [vt.co.x for vt in bm.verts]
        ys = [vt.co.y for vt in bm.verts]
        print("variant %d: verts=%d faces=%d comps=%d bbox x[%.3f,%.3f] y[%.3f,%.3f] z[%.3f,%.3f]"
              % (v, len(bm.verts), len(bm.faces), count_components(bm),
                 min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
