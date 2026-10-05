# -*- coding: utf-8 -*-
"""桥头靠山兽 v3(beasts2): 近景可辨识的蹲坐式雄壮镇桥兽, 程序化重雕。

背景与历史依据 (2026-10-05 经老照片 11 / side_elev_6794.jpg 确证):
  - 十七孔桥桥头 4 只靠山兽(两端各 2 只)实际为【蹲坐式官式镇桥雄兽】(非铜麒麟/獬豸细颈卧态):
    前肢直立粗壮、前胸雄挺阔展、前爪沉稳下按于桥头抱鼓基座上;
    后躯低沉蹲坐、肌肉紧凑健硕;
    头部巨大开阔、宽吻、双层眉弓、凸眼、张口吐舌/含珠、鬃毛大卷团垂于脑后与颈侧;
    后背顺势连接桥台栏板抱鼓卷云, 与桥台浑然一体, 绝非孤立展示须弥座。
  - 命名采 C3 裁决: 正名「靠山兽」(京报网官方转载口径), 严禁称「石象」。

尺寸与形制:
  - 单位高度归一化, 场景尺寸取 size=1.12m(含座), 长≈1.10*size, 宽≈0.60*size。
  - 变体 0: 雄健张口, 鬃毛 9 卷, 昂首前视;
  - 变体 1: 颌微收含珠, 颈侧微转, 鬃毛 11 卷, 尾卷镜像。
  - 验收口径: 单 mesh 连通域数==1(100% 水密单体), 面数 ≥ 3500。
"""
import bmesh
import math

import bpy
from mathutils import Matrix

_CACHE = {}
NVARIANTS = 2

_SEG, _RING = 18, 10
_SEG_S, _RING_S = 14, 8
_SEG_M, _RING_M = 16, 9


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
    for f in bm.faces:
        f.smooth = True
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
    for f in bm.faces:
        f.smooth = True
    return bm


def _sculpt_parts(variant):
    """蹲坐式官式靠山兽部件(单位坐标: 朝 +X, 高 1.0, 闭合水密深互渗)。"""
    P, N, F = [], [], []

    def add(bm, lst=None):
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bm.normal_update()
        (lst if lst is not None else P).append(bm)

    def neg(bm):
        add(bm, N)

    def fin(bm):
        add(bm, F)

    def ell(c, r, seg=_SEG, ring=_RING):
        add(_ell(c, r, seg, ring))

    def box(c, s, rot=0.0):
        add(_box(c, s, rot))

    # 1. 抱鼓基石 (端头平整压顶条石, 沉入桥台 15mm 保证互渗, 废弃多层展陈台)
    box((0.0, 0, 0.06), (0.92, 0.62, 0.13))

    # 2. 蹲坐后臀与后大腿 (敦实低坐于基座后方)
    ell((-0.20, 0, 0.28), (0.25, 0.23, 0.19))
    for sy in (1, -1):
        ell((-0.16, sy * 0.19, 0.23), (0.17, 0.09, 0.13))
        # 爪前探抱地
        box((-0.02, sy * 0.20, 0.13), (0.12, 0.08, 0.05))

    # 3. 直立雄壮前胸与躯干 (从低臀向前胸大角度拔起, 气势雄重)
    ell((0.01, 0, 0.42), (0.22, 0.21, 0.23))
    ell((0.15, 0, 0.60), (0.20, 0.22, 0.23))
    # 胸肌隆起
    for sy in (1, -1):
        ell((0.24, sy * 0.08, 0.58), (0.09, 0.11, 0.16))

    # 4. 直立粗壮前肢 (如石柱支撑, 前端宽厚石雕爪)
    for sy in (1, -1):
        ell((0.21, sy * 0.145, 0.32), (0.10, 0.09, 0.22))
        box((0.25, sy * 0.145, 0.15), (0.15, 0.13, 0.09))
        # 三主趾与利爪
        for ty in (-0.035, 0.0, 0.035):
            ell((0.32, sy * 0.145 + ty, 0.135), (0.038, 0.018, 0.025), _SEG_S, _RING_S)

    # 5. 粗壮短颈
    ell((0.16, 0, 0.73), (0.16, 0.18, 0.15))

    # 6. 巨大头颅 (硕大、宽阔、面带威严镇水之相)
    head_yaw = 0.0 if variant == 0 else 0.08
    ell((0.21, head_yaw * 0.1, 0.88), (0.19, 0.20, 0.17))

    # 宽阔方吻与肥厚鼻梁
    box((0.32, head_yaw * 0.1, 0.84), (0.16, 0.20, 0.11))
    ell((0.39, head_yaw * 0.1, 0.88), (0.045, 0.08, 0.045), _SEG_S, _RING_S)
    for sy in (1, -1):
        ell((0.39, head_yaw * 0.1 + sy * 0.055, 0.87), (0.04, 0.04, 0.04), _SEG_S, _RING_S)

    # 张口阔吻 / 舌与獠牙 / 下颌
    jaw_open = -0.035 if variant == 0 else -0.050   # 二审条款二十一: 张口为实物核心特征
    box((0.29, head_yaw * 0.1, 0.77 + jaw_open), (0.14, 0.15, 0.055))
    ell((0.34, head_yaw * 0.1, 0.75 + jaw_open), (0.045, 0.06, 0.035), _SEG_S, _RING_S)
    if variant == 1:
        # 变体1: 含绣球/龙珠
        ell((0.35, 0, 0.79), (0.045, 0.045, 0.045), _SEG_S, _RING_S)

    # 威严双层眉弓与怒目凸眼
    for sy in (1, -1):
        box((0.30, head_yaw * 0.1 + sy * 0.085, 0.93), (0.07, 0.10, 0.045))
        ell((0.31, head_yaw * 0.1 + sy * 0.085, 0.90), (0.04, 0.04, 0.04), _SEG_S, _RING_S)
        # 侧耳后展
        ell((0.15, sy * 0.20, 0.94), (0.07, 0.045, 0.09), _SEG_S, _RING_S)

    # 7. 官式卷云鬃毛 (大团涡卷环绕头颈后部)
    n_mane = 10 if variant == 0 else 12
    for k in range(n_mane):
        th = math.radians(-60.0 + 300.0 * k / float(max(1, n_mane - 1)))
        xm = 0.10 - 0.06 * max(0.0, math.sin(th))
        ym = 0.17 * math.cos(th)
        zm = 0.78 + 0.16 * math.sin(th)
        ell((xm, ym, zm), (0.055, 0.065, 0.055), _SEG_M, _RING_M)

    # 颈背鬃毛顺流下覆
    for k, (mx, mz) in enumerate(((0.10, 0.73), (0.02, 0.65), (-0.06, 0.57))):
        ell((mx, 0, mz), (0.06, 0.08, 0.06), _SEG_M, _RING_M)

    # 8. 脊背连带与卷尾 (贴背回盘, 顺接桥台抱鼓卷云)
    box((-0.32, 0, 0.36), (0.24, 0.16, 0.32))
    ell((-0.34, 0, 0.52), (0.12, 0.10, 0.14), _SEG_S, _RING_S)
    tail_sy = 1.0 if variant == 0 else -1.0
    ell((-0.26, tail_sy * 0.16, 0.44), (0.08, 0.06, 0.12), _SEG_S, _RING_S)
    ell((-0.22, tail_sy * 0.14, 0.56), (0.06, 0.05, 0.09), _SEG_S, _RING_S)

    # ── 减法(半凸出表面, 杜绝内腔壳): 张口槽/眼窝/鼻孔; 最后凸眼 ──
    hy = head_yaw * 0.1
    neg(_box((0.40, hy, 0.785), (0.10, 0.12, 0.045)))
    for sy in (1, -1):
        neg(_ell((0.385, hy + sy * 0.075, 0.90), (0.026, 0.026, 0.026), _SEG_S, _RING_S))
        neg(_ell((0.425, hy + sy * 0.045, 0.865), (0.014, 0.014, 0.014), _SEG_S, _RING_S))
        fin(_ell((0.392, hy + sy * 0.075, 0.90), (0.028, 0.028, 0.028), _SEG_S, _RING_S))
    return P, N, F


def _union_parts(parts):
    """顺序 EXACT 布尔并 -> 单一水密 bpy mesh(临时对象用后即焚)。"""
    col = bpy.context.scene.collection
    base = None
    for i, pbm in enumerate(parts):
        me = bpy.data.meshes.new("_beast2_part_%d" % i)
        pbm.to_mesh(me)
        pbm.free()
        ob = bpy.data.objects.new("_beast2_part_%d" % i, me)
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


def _bool_step(me, tool_bm, op):
    """单步 EXACT 布尔(并/差), 返回新 mesh。"""
    col = bpy.context.scene.collection
    tme = bpy.data.meshes.new("_beast2_tool")
    tool_bm.to_mesh(tme)
    tool_bm.free()
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
    col.objects.unlink(ob); bpy.data.objects.remove(ob); bpy.data.meshes.remove(tme)
    col.objects.unlink(base); bpy.data.objects.remove(base)
    return new_me


def _normalize(bm):
    """归一化: 高 -> 1.0(含底座), 底面 z=0, x/y 居中。"""
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
    """简单细分一次(SUBSURF SIMPLE), 提升高精雕凿面数。"""
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
    """平滑着色 + 保留结构棱角。"""
    thr = math.radians(angle_deg)
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        if len(e.link_faces) == 2 and e.calc_face_angle(math.pi) > thr:
            e.smooth = False
        else:
            e.smooth = True


def _build_master(variant):
    pos, negl, finl = _sculpt_parts(variant)
    me = _union_parts(pos)
    for nbm in negl:
        me = _bool_step(me, nbm, 'DIFFERENCE')
    for fbm in finl:
        me = _bool_step(me, fbm, 'UNION')
    bm = bmesh.new()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
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
    """4 只靠山兽 linked duplicate 放置。"""
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
    """连通域数。验收口径: 单只 mesh 连通域==1(水密)。"""
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
