# -*- coding: utf-8 -*-
"""桥头靠山兽 v4(beasts2): 蹲坐式官式镇桥兽, 三审修复批(2026-10-05)。

历史依据(老照片 11 / 17 号裁切实证): 直立粗壮前肢宽爪按地、雄挺前胸、巨大阔吻头颅、
明显张口、层片状卷云鬃环颈、背顺接桥台抱鼓; 废细颈麒麟卧态与展陈须弥座。
三审修复指令1落实: 吻部前出+上颌唇缘/下颌分层+口裂负刀半凸; 鬃改片状层叠; 布尔后焊缝清理。

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


def _sculpt_parts(variant):
    """蹲坐式靠山兽部件(单位高 1.0, 朝 +X)。返回 (P, N, F)。

    终审重雕造型语言: 扁椭球叠棱 + 楔形棱台(_frustum) + 负刀 crease;
    废气球胸/球串鬃/鳍片/机械口裂。六项剪影验收: 头高~0.28 / 前肢垂直 /
    口裂>=0.06 / 三层弧鬃半嵌错缝 / S 扁带贴臀尾 / 座接触宽。
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

    def box(c, s, rot_y=0.0, rot_x=0.0, rot_z=0.0):
        add(_box(c, s, rot_y, rot_x, rot_z))

    def fru(c, s, tx=1.0, tz=1.0, rot_y=0.0, rot_x=0.0):
        add(_frustum(c, s, tx, tz, rot_y, rot_x))

    def neg(bm):
        add(bm, N)

    def fin(bm):
        add(bm, F)

    hy = 0.0 if variant == 0 else 0.012

    # 1. 抱鼓基石(端头压顶条石, 沉入桥台互渗; 废展陈须弥座)
    box((0.0, 0, 0.06), (0.92, 0.62, 0.13))

    # 2. 蹲坐后臀与后大腿(座部体量) + 后爪前探抱地
    ell((-0.235, 0, 0.335), (0.205, 0.215, 0.195))
    for sy in (1, -1):
        ell((-0.175, sy * 0.195, 0.295), (0.165, 0.085, 0.155))
        box((-0.055, sy * 0.20, 0.155), (0.115, 0.085, 0.055))
        for ty in (-0.032, 0.004, 0.040):
            ell((0.005, sy * 0.20 + ty, 0.140), (0.034, 0.017, 0.024), _SEG_S, _RING_S)

    # 3. 胸腔: 前后两枚扁椭球叠出胸肌棱线; 前壁竖直、腰身收窄(废气球)
    ell((-0.025, 0, 0.415), (0.215, 0.185, 0.225))
    ell((0.155, 0, 0.515), (0.105, 0.215, 0.215))
    for sy in (1, -1):
        ell((0.215, sy * 0.095, 0.435), (0.06, 0.08, 0.135))

    # 4. 直立前肢(石柱 90 度垂直) + 宽厚石雕爪 + 三趾
    for sy in (1, -1):
        ell((0.215, sy * 0.15, 0.315), (0.07, 0.08, 0.19))
        ell((0.225, sy * 0.15, 0.47), (0.055, 0.065, 0.075))
        box((0.245, sy * 0.15, 0.16), (0.135, 0.12, 0.06))
        for ty in (-0.038, 0.0, 0.038):
            ell((0.315, sy * 0.15 + ty, 0.145), (0.04, 0.019, 0.026), _SEG_S, _RING_S)

    # 5. 短颈: 楔形棱台上收(顶面收缩), 微前倾
    fru((0.095, 0, 0.66), (0.14, 0.28, 0.15), tz=0.66, rot_y=-0.13)

    # 6. 头颅两层: 颊段(宽下层) + 额段(收顶上层, 前缘成眉台阶)
    fru((0.185, hy, 0.84), (0.30, 0.40, 0.14), tx=0.85)
    fru((0.16, hy, 0.938), (0.265, 0.385, 0.09), tx=0.78, tz=0.55)

    # 6b. 吻部: 前窄后宽棱台 + 鼻镜扁椭球 + 獠颊垫(圆化侧壁)
    fru((0.34, hy, 0.855), (0.21, 0.30, 0.125), tx=0.70)
    ell((0.455, hy, 0.875), (0.038, 0.08, 0.03))
    for sy in (1, -1):
        ell((0.335, hy + sy * 0.125, 0.845), (0.085, 0.04, 0.06))

    # 6c. 独立下颌层(小颊台) + 下巴须球; 后贴扁平耳
    fru((0.30, hy, 0.745), (0.15, 0.13, 0.07), tx=0.55)
    ell((0.352, hy, 0.71), (0.03, 0.05, 0.036))
    for sy in (1, -1):
        box((0.10, hy + sy * 0.155, 0.945), (0.075, 0.035, 0.065),
            rot_x=sy * -0.6)

    # 7. 鬃: 三层鬃披(阶梯环领, 层缘即雕层棱线) + 每层贴弧鬃瓦
    #    (扁椭球瓦片径向半嵌, 圈间错缝 + 垂檐 0.012, 侧弧 -10~190 度)
    fru((0.088, 0, 0.715), (0.12, 0.30, 0.13), tz=0.78, rot_y=-0.13)
    fru((0.075, 0, 0.645), (0.13, 0.33, 0.135), tz=0.78, rot_y=-0.13)
    fru((0.055, 0, 0.575), (0.13, 0.36, 0.145), tz=0.80, rot_y=-0.10)
    n_mane = 8
    for ri, (rr, zc, xk, ph, rw) in enumerate((
            (0.135, 0.715, 0.088, 0.0, 0.028),
            (0.158, 0.645, 0.070, 0.5, 0.030),
            (0.178, 0.565, 0.052, 0.25, 0.032))):
        for k in range(n_mane):
            th = math.radians(-10.0 + 200.0 * (k + ph) / float(n_mane))
            ell((xk, rr * math.cos(th), zc + rr * math.sin(th) - 0.012),
                (0.056, rw, 0.10), _SEG_S, _RING_S, rot_x=th, carve=True)

    # 7b. 鬃梢顺流披肩(半嵌瓦片, 废椭球团块)
    for sy in (1, -1):
        ell((0.03, sy * 0.165, 0.585), (0.06, 0.016, 0.055), _SEG_S, _RING_S,
            rot_x=sy * 0.35, carve=True)

    # 8. 脊线: 连续低棱(细长扁椭球沿背线半嵌搭接, 废突点)
    for (bx, bz) in ((0.10, 0.705), (-0.035, 0.64), (-0.17, 0.535),
                     (-0.26, 0.50)):
        ell((bx, 0, bz), (0.075, 0.022, 0.022), _SEG_S, _RING_S, carve=True)

    # 8b. 背顺接桥台抱鼓(靠山) + 卷云端头
    fru((-0.315, 0, 0.35), (0.25, 0.17, 0.30), tz=0.5)
    ell((-0.34, 0, 0.53), (0.11, 0.095, 0.12), _SEG_S, _RING_S)

    # 9. 尾: 贴臀单条 S 扁带(三节瓦片搭接深半嵌, 废球串; variant 换侧)
    tsy = 1.0 if variant == 0 else -1.0
    ell((-0.295, tsy * 0.13, 0.46), (0.045, 0.018, 0.075), _SEG_S, _RING_S,
        rot_x=tsy * 0.7, carve=True)
    ell((-0.315, tsy * 0.195, 0.345), (0.05, 0.018, 0.085), _SEG_S, _RING_S,
        rot_x=tsy * 0.35, carve=True)
    ell((-0.245, tsy * 0.255, 0.235), (0.06, 0.018, 0.065), _SEG_S, _RING_S,
        rot_x=tsy * 0.5, rot_z=tsy * 0.25, carve=True)

    # 10. 减法(负刀全部半凸穿出表面, 防内腔):
    #     口裂楔刀(浅腔厚唇) / 眉弓折痕 / 眼窝 / 鼻孔
    if variant == 0:
        neg(_frustum((0.42, hy, 0.806), (0.25, 0.124, 0.048), tx=1.55))
    else:
        neg(_frustum((0.42, hy, 0.806), (0.25, 0.124, 0.028), tx=1.55))
    for sy in (1, -1):
        ell((0.343, hy + sy * 0.098, 0.922), (0.05, 0.022, 0.026), _SEG_S, _RING_S)
        neg(_ell((0.352, hy + sy * 0.096, 0.958), (0.045, 0.016, 0.022),
                 _SEG_S, _RING_S))
        neg(_ell((0.358, hy + sy * 0.094, 0.892), (0.028, 0.030, 0.028), _SEG_S, _RING_S))
        neg(_ell((0.483, hy + sy * 0.032, 0.875), (0.014, 0.014, 0.012), _SEG_S, _RING_S))

    # 10b. 后置凸件(负刀后并回): 凸眼珠 / 上唇獠牙(张口) 或 含珠(微合)
    for sy in (1, -1):
        fin(_ell((0.361, hy + sy * 0.094, 0.889), (0.036, 0.038, 0.036), _SEG_S, _RING_S))
    if variant == 0:
        for sy in (1, -1):
            fin(_ell((0.443, hy + sy * 0.055, 0.838), (0.02, 0.022, 0.045),
                     _SEG_S, _RING_S))
    else:
        fin(_ell((0.34, hy, 0.775), (0.042, 0.042, 0.042), _SEG_S, _RING_S))

    # 11. 雕饰簇(鬃瓦/脊棱/尾带)先并成单一壳, 再与体块一次并:
    #     避免逐片对阶梯棱边的切线布尔退化壳
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
    out_me = _densify(me2)
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
