# -*- coding: utf-8 -*-
"""桥头靠山兽 v2(beasts2): 近景可辨识的伏卧异兽, 程序化重雕。

背景: 旧 build_scene2.build_beast_bm() 用盒块堆叠, 4 只仅 384 顶点/288 面(每只 72 面),
近景为无定形白块。本模块以 2026-10-05 下载的参考照为造型依据(refs/kanshan_ref/,
Wikimedia Commons CC BY/CC BY-SA, 仅作造型参照不入成片素材):
  - 颐和园铜狻猊/异兽(watch-beast, 仁寿殿前): 官式镇守异兽谱系 —— 后掠双角/双层眉弓/
    凸眼/宽吻鼻卷/口裂/颌下须团/卷云鬃, 前高后低的蹲伏气势;
  - 颐和园铜獬豸(xiezhi): 后掠角弧/颈背鬃流/伏卧后躯/贴体卷尾;
  - 十七孔桥望柱狮(iheuan-2005-6): 汉白玉雕凿的同类官式手法(趾/爪/卷纹程式)。
命名采 C3 裁决: 正名「靠山兽」(京报网 2025-12-24 官方转载口径, 4 只), **不得写「石象」**
—— 物种无文献定论, 故造型取「异兽」程式(角/鬃/伏卧), 不映射任何具体物种。

尺寸地位(与旧版一致, 全部 [工作值]): 高 1.05-1.20m(取 1.12)/长 1.15-1.35m(取 1.25)/
宽 0.45-0.55m(取 0.50)/须弥座高约 0.20m —— 园方未公布测点, 见 refs/freeze_manifest.md §8-16。
识别度走剪影: 头+后掠角+卷云鬃 / 伏卧前肢(立肘+前探爪+趾) / 脊线 / 卷尾。不做毛发。

交付形态(2026-10-05 主控口径, 与 LionSculpt 同): **不合并单 bmesh** ——
  beast_bm(size, variant, seed) -> 单只水密 bmesh(连通域=1);
  place_beasts(spots)           -> 4 个 linked duplicate 对象共享 ≤NVARIANTS 套 mesh
                                   (mesh 共享、对象自有 transform, Blender 官方推荐做法)。
内部: 每变体一次"母模"(~60 个闭合体块 EXACT 布尔并成单一水密实体, 归一化高=1.0,
全域细分一次), 缓存为 bpy mesh; seed 只驱动凿感噪声, place_beasts 对同变体固定用
同 seed 保证 mesh 可共享。单只面数 ≥3000。

Python 3.9 兼容(禁 match / X|None 注解)。
"""
import bmesh
import math

import bpy
from mathutils import Matrix

# 母模缓存: {variant: bpy.data.Mesh}(单位高, 归一化)。0 用户网格, dispose 后即弃。
_CACHE = {}

NVARIANTS = 2
_SEG, _RING = 18, 10          # 标准椭球分辨率(大件: 180 面)
_SEG_S, _RING_S = 18, 10      # 小件(眼/须/角节/尾节/趾/脊突): 同标准, 近景够细
_SEG_M, _RING_M = 16, 9       # 鬃毛卷: 144 面


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
    return bm


def _dorsal_z(x):
    """背线高度(躯干/臀/胸三椭球上缘的包络), 供脊线与卷尾贴面。"""
    def cap(v):
        return math.sqrt(max(0.0, 1.0 - v * v))
    z1 = 0.400 + 0.185 * cap((x + 0.02) / 0.34)     # 躯干
    z2 = 0.430 + 0.220 * cap((x + 0.28) / 0.25)     # 后臀
    z3 = 0.500 + 0.290 * cap((x - 0.25) / 0.17)     # 前胸
    return max(z1, z2, z3)


def _sculpt_parts(variant):
    """伏卧靠山兽部件(单位坐标: 朝 +X, 高 1.0 含须弥座, 全闭合体块, 深互渗供布尔并)。
    坐标即设计值, 注释给近景识别作用。variant 0/1 仅角弧/口裂/鬃数/尾侧向有别。"""
    P = []

    def add(bm):
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bm.normal_update()
        P.append(bm)

    def ell(c, r, seg=_SEG, ring=_RING):
        add(_ell(c, r, seg, ring))

    def box(c, s, rot=0.0):
        add(_box(c, s, rot))

    # ── 须弥座(双层, 下层沉 10mm 防 Z 面 coplanar; 上层顶 0.235 与兽体根互渗 25mm) ──
    box((0.0, 0, 0.088), (1.22, 0.60, 0.195))
    box((0.0, 0, 0.205), (1.02, 0.47, 0.060))
    # ── 后躯: 臀大块(伏卧读感的根, 后缘探出座外, 根部沉入座 25mm) + 低躯干 ──
    ell((-0.28, 0, 0.430), (0.250, 0.215, 0.220))
    ell((-0.02, 0, 0.400), (0.340, 0.210, 0.185))
    # ── 前胸高起 + 颈(前高后低 = 官式镇兽气势) ──
    ell((0.250, 0, 0.500), (0.170, 0.200, 0.290))
    ell((0.350, 0, 0.680), (0.130, 0.150, 0.190))
    ell((0.250, 0, 0.640), (0.100, 0.140, 0.090))              # 颈背鬃基(连通兜底, 压低防驼峰)
    # ── 头: 颅 / 颧颊 / 双层眉弓 / 凸眼 / 宽吻 / 鼻卷 / 下颌(留缝=口裂) ──
    ell((0.430, 0, 0.825), (0.115, 0.145, 0.115))              # 颅
    ell((0.410, 0, 0.755), (0.070, 0.140, 0.065))              # 颧颊
    for sy in (1, -1):
        box((0.500, sy * 0.060, 0.875), (0.045, 0.085, 0.030))    # 眉弓上层
        box((0.518, sy * 0.058, 0.848), (0.028, 0.075, 0.022))    # 眉弓下层
        ell((0.508, sy * 0.052, 0.828), (0.032, 0.032, 0.032), _SEG_S, _RING_S)  # 凸眼球
    box((0.545, 0, 0.780), (0.100, 0.145, 0.085))              # 宽扁吻
    ell((0.585, 0, 0.825), (0.035, 0.060, 0.030), _SEG_S, _RING_S)       # 鼻梁隆起
    for sy in (1, -1):                                          # 鼻翼上卷
        ell((0.600, sy * 0.045, 0.815), (0.026, 0.026, 0.026), _SEG_S, _RING_S)
    jaw_dz = 0.0 if variant == 0 else 0.006                     # v0 张口/v1 闭口
    box((0.505, 0, 0.712 + jaw_dz), (0.105, 0.115, 0.032))      # 下颌(与吻底留缝=口裂)
    ell((0.550, 0, 0.695 + jaw_dz), (0.028, 0.042, 0.036), _SEG_S, _RING_S)  # 颌下须团
    for sy in (1, -1):                                          # 口角垂须双卷
        ell((0.565, sy * 0.082, 0.750), (0.020, 0.026, 0.024), _SEG_S, _RING_S)
        ell((0.555, sy * 0.092, 0.720), (0.017, 0.023, 0.021), _SEG_S, _RING_S)
    # ── 耳(颅顶侧角, 后掠; 内半埋入颅保证并壳) ──
    for sy in (1, -1):
        box((0.380, sy * 0.105, 0.925), (0.070, 0.045, 0.050), rot=-0.25)
    # ── 后掠双角: 每侧 4 节渐细 + 端头疙瘩(铜狻猊/獬豸角弧; 节距≤0.8×半径和防浮壳;
    #     弧顶抬过鬃环, 剪影上"两支角"才可读) ──
    hb = 0.012 if variant == 1 else 0.0                         # v1 角弧前倾一档
    for sy in (1, -1):
        arc = ((0.440, 0.048, 0.935, 0.040),
               (0.404 + hb * 0.4, 0.062, 0.968, 0.034),
               (0.366 + hb * 0.8, 0.074, 0.990, 0.029),
               (0.328 + hb, 0.084, 1.002, 0.025))
        for (ax, ay, az, ar) in arc:
            ell((ax, sy * ay, az), (ar * 1.25, ar, ar), _SEG_S, _RING_S)
        ell((0.292 + hb, sy * 0.090, 1.008), (0.021, 0.021, 0.026), _SEG_S, _RING_S)  # 角尖
    # ── 卷云鬃: 环颅颈 9(v0)/11(v1) 团, 前倾成螺旋(收紧贴颅, 给角让位) ──
    nmane = 9 if variant == 0 else 11
    for k in range(nmane):
        th = math.radians(15.0 + k * (330.0 / max(1, nmane - 1)))
        rr = 0.125
        rk = 0.040 + 0.009 * math.sin(th)
        cx = 0.345 + 0.040 * math.sin(th) + (0.010 if k % 2 else -0.010)
        ell((cx, rr * math.cos(th), 0.745 + rr * math.sin(th)),
            (rk * 1.30, rk, rk), _SEG_M, _RING_M)
    for k, (mx, mz) in enumerate(((0.300, 0.700), (0.245, 0.655), (0.195, 0.615))):
        ell((mx, 0, mz), (0.048, 0.060, 0.048), _SEG_M, _RING_M)          # 颈背鬃流
    # ── 伏卧前肢: 立肘直下 + 前探爪 + 趾 ──
    for sy in (1, -1):
        box((0.270, sy * 0.135, 0.360), (0.125, 0.100, 0.270))
        box((0.335, sy * 0.135, 0.250), (0.150, 0.110, 0.055))            # 爪
        for ty in (0.024, -0.024):
            box((0.400, sy * (0.135 + ty), 0.252), (0.030, 0.024, 0.045))  # 趾
    # ── 折叠后腿的爪(臀侧前探, 半埋入臀) ──
    for sy in (1, -1):
        ell((-0.160, sy * 0.120, 0.270), (0.100, 0.050, 0.050), _SEG_S, _RING_S)
    # ── 脊线: 背包络上 5 突(剪影识别件) ──
    for x in (0.200, 0.080, -0.050, -0.180, -0.300):
        ell((x, 0, _dorsal_z(x) - 0.010), (0.022, 0.020, 0.016), _SEG_S, _RING_S)
    # ── 卷尾: 沿臀侧 C 弧上扬 + 尾梢疙瘩(v0 贴 +y 侧, v1 镜到 -y 侧)。
    #    逐节核过: 内缘埋入臀面 20mm+, 节距≤0.8×半径和(防浮壳), 3/4 与侧视都读得出 ──
    tsy = 1.0 if variant == 0 else -1.0
    tarc = ((-0.445, 0.180, 0.415, 0.036),
            (-0.409, 0.195, 0.448, 0.034),
            (-0.373, 0.205, 0.478, 0.031),
            (-0.337, 0.205, 0.508, 0.028),
            (-0.301, 0.200, 0.530, 0.026),
            (-0.269, 0.185, 0.551, 0.025))
    for (tx, ty, tz, tr) in tarc:
        ell((tx, tsy * ty, tz), (tr, tr * 0.9, tr), _SEG_S, _RING_S)
    ell((-0.235, tsy * 0.170, 0.572), (0.030, 0.028, 0.034), _SEG_S, _RING_S)  # 尾梢疙瘩
    return P


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


def _normalize(bm):
    """归一化: 高 -> 1.0(含须弥座), 底面 z=0, x/y 居中。"""
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
    ncomp = count_components(bm)
    if ncomp != 1:
        bm.free()
        raise RuntimeError("beasts2: variant %d 母模不水密(连通域=%d>1) —— "
                           "有部件浮壳, 须修 _sculpt_parts 互渗" % (variant, ncomp))
    _normalize(bm)
    # 注: 不做全域 subdivide_edges(smooth) —— 2026-10-05 实测它会在布尔缝合处
    # 掷出 4 个 2边2面的退化鳍状顶点(飞出体外 ~0.27), 污染 bbox 与剪影。
    # 近景密度改由部件分辨率保障(_SEG_S 同标准 18x10), 平滑着色由 _ell f.smooth 承担。
    out = bpy.data.meshes.new("_beast2_master_%d" % variant)
    bm.to_mesh(out)
    bm.free()
    return out


def _master(variant):
    if variant not in _CACHE:
        _CACHE[variant] = _build_master(variant)
    return _CACHE[variant]


def dispose_cache():
    """释放母模缓存(0 用户网格不留盘)。build_scene2 建完 beasts 后调用。"""
    for me in _CACHE.values():
        try:
            if me.users == 0:
                bpy.data.meshes.remove(me)
        except ReferenceError:
            pass
    _CACHE.clear()


def _jitter(bm, size, seed):
    """seed 确定性低频噪声(凿石感): 幅度 0.55%size << 特征尺度, 接地圈只上不移。
    注意: place_beasts 对同变体固定 seed, 保证 mesh 可共享。"""
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
    amp = 0.0055 * size
    bm.normal_update()
    for v in bm.verts:
        x, y, z = v.co
        wx, wy, wz = x / size, y / size, z / size
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


def beast_bm(size=1.12, variant=0, seed=0):
    """靠山兽 bmesh。原点=须弥座底面中心, 朝 +X, 总高=size(含座), 长≈1.12*size, 宽≈0.54*size。
    variant: 0=张口/长角弧/尾贴+y 侧, 1=闭口/前倾角/尾镜 -y 侧。
    seed 仅驱动凿感噪声(不改变解剖)。连通域=1(水密)。"""
    bm = bmesh.new()
    bm.from_mesh(_master(variant % NVARIANTS))
    bmesh.ops.scale(bm, vec=(size, size, size), verts=bm.verts)
    _jitter(bm, size, seed)
    return bm


def place_beasts(spots, name="beasts", size=1.12, material=None):
    """4 只靠山兽 linked duplicate 放置(主控接线入口)。

    spots: iterable of (x, y, z, idx, facing) —— 与 build_lions_bm 的 spots 同构:
      (x,y,z)=须弥座底面中心(桥头面), idx 选变体 idx%%NVARIANTS,
      facing=+1 头朝 +X / -1 头朝 -X(对象绕 Z 转 180°, mesh 仍共享)。
    每变体只建一次 mesh(seed=variant 固定, 保证可共享) -> unique mesh ≤NVARIANTS,
    对象各自持有 transform(Blender linked duplicate 最佳实践)。
    返回对象列表(命名 name_0..name_N, 默认 "beasts_i")。"""
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
    """连通域数(顶点洪泛)。验收口径: 单只 mesh 连通域==1(水密)。"""
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
