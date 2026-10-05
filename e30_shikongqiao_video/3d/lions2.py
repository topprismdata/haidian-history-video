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
    """官式蹲狮子部件(单位坐标: 朝 +X, 高 1.0)。v4 减法瘦身(去玩具感):
    躯干 ry/rz 收 9-10%, 颅收 6%, 眉弓双层楔形, 鼻梁棱台加长 10% + 鼻头扁方台,
    口裂刻深 0.02, 前肢上粗下细棱台 + 三趾分缝, 鬃改 12 片贴颅放射扁片(厚 0.02 半嵌)。
    返回 (pos, neg, final):
    pos 先布尔并, neg 再布尔减(口裂/鼻孔/眼窝/趾缝——均开口于表面不穿透),
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

    # ── 柱头接触底垫 + 后座(坐姿读感的根) ──
    box((0.01, 0, 0.012), (0.52, 0.38, 0.030))                 # 底垫(沉 3mm 防 Z 面 coplanar)
    box((-0.17, 0, 0.069), (0.44, 0.36, 0.138))                # 后座垫
    # ── 后躯: 臀收 9%(ry/rz) + 两侧腿臀收 10% + 折叠后腿轮廓(侧面剪影关键) ──
    ell((-0.17, 0, 0.220), (0.260, 0.182, 0.173))
    ell((-0.15, 0.135, 0.198), (0.210, 0.076, 0.147))
    ell((-0.15, -0.135, 0.198), (0.210, 0.076, 0.147))
    ell((-0.255, 0.112, 0.160), (0.105, 0.062, 0.100), _SEG_S, _RING_S)
    ell((-0.255, -0.112, 0.160), (0.105, 0.062, 0.100), _SEG_S, _RING_S)
    for sy in (1, -1):                                          # 后肢贴地立柱(破臀球剪影)
        add(_taper((-0.300, sy * 0.108, 0.025), (0.075, 0.052),
                   (-0.235, sy * 0.108, 0.210), (0.105, 0.075)), P)
    # ── 胸窄而深(ry 收 10%) / 颈收 9% / 颈圈带 ──
    ell((0.145, 0, 0.335), (0.155, 0.167, 0.198))
    ell((0.090, 0, 0.510), (0.135, 0.150, 0.138))
    ell((0.115, 0, 0.470), (0.095, 0.185, 0.046))              # 颈圈带
    add(_frustum((0.278, 0, 0.452), (0.086, 0.024),
                 (0.300, 0, 0.348), (0.048, 0.018), tilt_x=-0.008), P)   # 绶带式垂饰(浅浮雕, 上宽下窄)
    # ── 前肢并拢直立: 上粗下细棱台 + 爪 + 三趾(前伸) ──
    for sy in (1, -1):
        add(_taper((0.185, sy * 0.075, 0.018), (0.096, 0.062),
                   (0.148, sy * 0.075, 0.372), (0.126, 0.086)), P)
        box((0.205, sy * 0.075, 0.050), (0.140, 0.102, 0.120))          # 前爪(包裹腿根, 杜绝脱节砖块感)
        for ty in (0.030, 0.0, -0.030):
            box((0.285, sy * 0.075 + ty, 0.044), (0.034, 0.026, 0.055))  # 趾(伸出爪面)
    # ── 头: 颅收 6% / 颧颊 / 额顶双卷(压扁) / 双层楔形眉弓 / 宽吻 /
    #    楔形鼻梁(加长 10%) + 鼻头扁方台 / 下颌(与吻融合) ──
    ell((0.165, 0, 0.705), (0.127, 0.174, 0.136))              # 颅(头区≈0.36H)
    ell((0.175, 0, 0.630), (0.072, 0.170, 0.095))              # 颧颊(收)
    for sy in (1, -1):
        ell((0.235, sy * 0.060, 0.800), (0.040, 0.045, 0.032), _SEG_S, _RING_S)   # 额顶双卷(压扁)
    # ── 面部: 颅-吻-颌连续椭球(互渗成整面, 无叠盒) ──
    ell((0.24, 0, 0.675), (0.105, 0.105, 0.085))               # 吻(长椭, 融入颅)
    ell((0.30, 0, 0.725), (0.060, 0.050, 0.028), _SEG_S, _RING_S)        # 鼻梁-鼻头脊(半嵌吻背)
    ell((0.25, 0, 0.585), (0.075, 0.105, 0.052))               # 颌-下巴(弧面下颏, 替方盒)
    # ── 耳(弧面圆丘, 穿出鬃领) ──
    for sy in (1, -1):
        ell((0.105, sy * 0.148, 0.812), (0.040, 0.030, 0.038), _SEG_S, _RING_S)
    # ── 鬃: 绕头轴 12 齿放射层片鬃领(连续环带, 每齿=一片, 相位错动叠压), 替 9 团球串 ──
    add(_mane_band(), P)
    ell((0.020, 0, 0.618), (0.095, 0.170, 0.105))              # 颈背鬃(连通兜底, 收窄)
    for sy in (1, -1):                                          # 胸侧披鬃(收窄)
        ell((0.060, sy * 0.155, 0.500), (0.100, 0.065, 0.128))
    # ── 尾: 沿臀侧 S 卷上扬 + 尾梢团 ──
    for k in range(6):
        t = k / 5.0
        ell((-0.335 + 0.05 * t, 0.115 + 0.015 * t, 0.240 + 0.11 * t),
            (0.026, 0.024, 0.026), _SEG_S, _RING_S)
    ell((-0.285, 0.128, 0.365), (0.038, 0.034, 0.038), _SEG_S, _RING_S)  # 尾梢
    # ── 变体配件: 抱球 / 含珠 (幼狮改独立幼狮母模, v3 544 体系) ──
    if acc == "ball":
        ell((0.300, -0.125, 0.054), (0.052, 0.052, 0.052), _SEG_S, _RING_S)
    else:
        ell((0.300, 0, 0.600), (0.048, 0.048, 0.048), _SEG_S, _RING_S)      # 口含珠
    # ── 减法(开口于表面, 不穿透): 口裂深刻弧(0.02, 两端上挑) / 鼻孔×2(吻背) /
    #    眉弓刻线×2 / 前肢分趾负缝×2×2 ──
    for k in range(7):                                          # 口裂: 刻在颌/吻底前面, 两端上挑
        yy = -0.055 + 0.0183 * k
        t = (yy / 0.055) ** 2
        neg_ell((0.315, yy, 0.600 + 0.022 * t), (0.030, 0.020, 0.020))
    for sy in (1, -1):
        neg_ell((0.322, sy * 0.014, 0.748), (0.012, 0.010, 0.010))   # 鼻孔浅凹(鼻脊背上开口)
        neg_ell((0.283, sy * 0.085, 0.748), (0.012, 0.030, 0.010))   # 眉弓刻线(额面浅雕)
        for ty in (0.015, -0.015):                                   # 分趾负缝(爪/趾前面开口)
            add(_box((0.318, sy * 0.075 + ty, 0.045), (0.032, 0.007, 0.052)), N)
    # ── 最后并入: 眼球凸片(扁化半嵌颅面) ──
    for sy in (1, -1):
        fin_ell((0.285, sy * 0.085, 0.720), (0.016, 0.032, 0.024))
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
    """幼狮部件(单位高 1.0, 朝 +X)。kind: 0 攀爬(前肢前倾 15°) 1 偎依仰头 25°
    2 侧头探 50° 3 伏卧(压扁 0.7 头侧贴地)。v4: 躯干 ry 收 12%/头收 8% 去幼熊感,
    三角楔耳贴颅侧, 细棱台四肢+分趾缝, 鬃改 8 片贴颅层片, 四态剪影拉大。"""
    P, N, F = [], [], []

    def add(bm, lst):
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bm.normal_update()
        lst.append(bm)

    def ell(c, r, lst=None):
        add(_ell(c, r, _SEG_S, _RING_S), P if lst is None else lst)

    def box(c, s, rot=0.0):
        add(_box(c, s, rot), P)

    def bpart(bm):
        add(_xform(bm, body_m), P)

    def bneg(bm):
        add(_xform(bm, body_m), N)

    lie = 1.0 if kind == 3 else 0.0          # 伏卧
    squash = 0.70 if kind == 3 else 1.0      # 伏卧压扁 0.7(绕 z=0), 微增宽保体量
    lean = -math.radians(15.0) if kind in (0, 3) else 0.0   # 前肢前倾(kind0 搭母狮腿; kind3 前伸趴姿)
    pitch = math.radians(25.0) if kind == 1 else 0.0   # 仰头
    yaw = math.radians(50.0) if kind == 2 else 0.0     # 侧头
    roll = math.radians(30.0) if kind == 3 else 0.0    # 头侧贴地

    body_m = Matrix.Diagonal((1.0 + 0.06 * (1.0 - squash), 1.0, squash, 1.0))

    # ── 躯干(瘦: ry 收 12%, rz/rx 再收) + 臀 + 颈楔(随姿态查表) ──
    bpart(_ell((-0.06, 0, 0.20 - lie * 0.06), (0.215, 0.136, 0.140 - lie * 0.045)))
    bpart(_ell((0.10, 0, 0.24 - lie * 0.08), (0.17, 0.128, 0.155 - lie * 0.05)))
    nz = (0.36, 0.395, 0.36, 0.25)[kind]
    nrot = (-0.15, -0.15, -0.30, 0.0)[kind]
    bpart(_box((0.14, 0, nz), (0.15, 0.11, 0.17), rot_y=nrot))
    # ── 头组(局部系建模 -> 姿态矩阵): 颅收 8% / 吻台 / 鼻头扁方台 / 眉弓扁楔 /
    #    三角楔耳贴颅侧 / 鬃 8 齿层片鬃领 ──
    hz = (0.52, 0.57, 0.52, 0.32)[kind]
    hx = (0.16, 0.16, 0.16, 0.185)[kind]
    head_m = (Matrix.Translation((hx, yaw * 0.06, hz))
              @ Matrix.Rotation(roll, 4, 'X')
              @ Matrix.Rotation(-pitch, 4, 'Y')
              @ Matrix.Rotation(yaw, 4, 'Z'))

    def hpart(bm, lst=None):
        add(_xform(bm, head_m), P if lst is None else lst)

    hpart(_ell((0.0, 0, 0.0), (0.133, 0.138, 0.129)))                 # 颅(收 8%)
    hpart(_ell((0.105, 0, -0.020), (0.075, 0.075, 0.055)))            # 吻(长椭融颅)
    hpart(_ell((0.115, 0, -0.075), (0.055, 0.065, 0.032)))            # 颌-下巴弧面
    hpart(_ell((0.155, 0, 0.008), (0.036, 0.032, 0.018)))             # 鼻脊(半嵌吻背)
    hpart(_frustum((0.045, 0, 0.052), (0.140, 0.030),                 # 横眉檐(浅雕)
                   (0.112, 0, 0.046), (0.095, 0.008)))
    for sy in (1, -1):
        hpart(_ell((0.020, sy * 0.130, 0.078), (0.032, 0.024, 0.030)))    # 耳圆丘(穿鬃领)
    hpart(_mane_band(cz=0.0, nflute=8,                                  # 8 齿层片鬃领(贴颅小领)
                     xs=(-0.075, -0.030, 0.020, 0.075),
                     base=(0.065, 0.136, 0.136, 0.116),
                     amp=(0.003, 0.012, 0.012, 0.006), r_in=0.06))
    # ── 前肢细棱台(kind0 前倾 15°) + 爪 + 三趾 ──
    for sy in (1, -1):
        bpart(_xform(_taper((0.150, sy * 0.072, 0.020), (0.052, 0.040),
                            (0.170, sy * 0.072, 0.300), (0.070, 0.055)),
                     Matrix.Rotation(lean, 4, 'Y'), (0.160, sy * 0.072, 0.160)))
    px = 0.205 + 0.030 * (1.0 if kind in (0, 3) else 0.0)   # kind0 爪前伸搭腿; kind3 前伸趴姿
    for sy in (1, -1):
        bpart(_box((px, sy * 0.072, 0.038), (0.098, 0.062, 0.050)))
        for ty in (0.020, 0.0, -0.020):
            bpart(_box((px + 0.046, sy * 0.072 + ty, 0.040), (0.026, 0.017, 0.032)))
    # ── 后腿折叠(细) + 爪 ──
    for sy in (1, -1):
        bpart(_ell((-0.14, sy * 0.10, 0.14 - lie * 0.04), (0.115, 0.048, 0.100)))
        bpart(_box((-0.06, sy * 0.10, 0.055 - lie * 0.02), (0.085, 0.050, 0.050)))
    # ── 尾 S 卷贴臀(kind3 外移防被增宽的躯干吞没) ──
    ty_o = 0.105 if kind == 3 else 0.085
    bpart(_ell((-0.20, ty_o, 0.19 - lie * 0.05), (0.032, 0.026, 0.052)))
    bpart(_ell((-0.205, ty_o + 0.005, 0.26 - lie * 0.06), (0.028, 0.026, 0.048)))
    bpart(_ell((-0.170, ty_o + 0.010, 0.32 - lie * 0.07), (0.027, 0.023, 0.036)))
    # ── 减法: 口裂 + 浅刻眼窝(吻台前角) + 前肢分趾缝(随体姿态) ──
    for sy in (1, -1):
        hpart(_ell((0.158, sy * 0.010, -0.058), (0.012, 0.012, 0.008)), N)
        hpart(_ell((0.128, sy * 0.040, 0.022), (0.012, 0.016, 0.009)), N)
        for ty in (0.010, -0.010):
            bneg(_box((px + 0.054, sy * 0.072 + ty, 0.040), (0.028, 0.006, 0.032)))
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
        offsets = [
            ( 0.10,  0.06, -0.015, 0.90),
            ( 0.10, -0.06, -0.010, 1.05),
            (-0.10,  0.06, -0.015, 0.95),
            (-0.10, -0.06, -0.010, 1.00),
        ]
        for c_idx in range(n_cubs):
            d_axis, d_trans, dz, scale_mul = offsets[c_idx]
            wx = x + _BX * d_axis + _NX * d_trans
            wy = y + _BY * d_axis + _NY * d_trans
            cub_var = (idx * 3 + c_idx) % NVARIANTS_CUB
            h = cub_H * scale_mul
            o_cub = bpy.data.objects.new("lion_cub_%03d_%+d_%d" % (idx, side, c_idx), m_cubs[cub_var])
            o_cub.location = (wx, wy, z + dz)
            o_cub.scale = (h, h, h)
            o_cub.rotation_euler = (0.0, 0.0, c_idx * 0.5 - 0.75)
            col.objects.link(o_cub)
            objs.append(o_cub)
    return objs


if __name__ == "__main__":
    for v in range(NVARIANTS_TOTAL):
        m = _master(v)
        print("Master %d (%s): faces=%d" % (v, "adult" if v < 4 else "cub", len(m.polygons)))
