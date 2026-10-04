"""v2 场景: 整体桥体 + 布尔挖券洞 + 券脸楔石 + 栏杆 + 异兽。"""
import bpy, bmesh, os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bridge_geom2 as G
import materials as MAT
import lions as LIONS
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
BRIDGE_AXIS_AZ = 112.0     # 北京建筑大学口径(东端略南/西端略北), 供后续光影用


def mat(name, rgb, rough=0.85):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    b.inputs["Roughness"].default_value = rough
    return m


def bm_to_obj(bm, name, material):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.data.materials.append(material)
    bpy.context.collection.objects.link(ob)
    return ob


def build_voussoir_bm():
    """券脸楔石: 贴侧墙【外表面】的薄浮雕(0.10m), 表达砌缝。

    硬约束(负控制可查): 券石顶点不得落在任何券洞净空内 —— 否则会横穿洞口
    把洞"腰斩"(曾出现每洞一道黑横杠)。判据: |x - xc| >= 净跨/2 或 z <= 起拱线。

    半圆券从 SPRINGER 起, 不含起拱线以下的直边段。
    块数: 中央 15 / 中 13 / 端 11(奇数, 留拱顶石)。
    """
    bm = bmesh.new()
    RELIEF = 0.10
    GAP = 0.018
    for i in range(G.N_SPAN):
        span = G.SPANS[i]
        xc = (G.PIER_X[i] + G.PIER_X[i + 1]) / 2.0
        a = span / 2.0
        b = a * 2.0 * G.ARCH_RATIO
        ci = abs(i - (G.N_SPAN - 1) / 2.0)
        N = 15 if ci <= 1.5 else (13 if ci <= 3.5 else 11)
        deck_c = G.deck_z(xc)
        for k in range(N):
            t0 = math.pi * k / N + GAP
            t1 = math.pi * (k + 1) / N - GAP
            rt = RELIEF * (0.94 + 0.12 * (((k * 7 + i * 3) % 5) / 4.0))
            quad = []
            for tt in (t0, t1):
                zz = G.SPRINGER + b * math.sin(tt)
                # 该高度桥体侧墙外表面(线性收分)
                f = max(0.0, min(1.0, (zz - G.BODY_BOTTOM) / (deck_c - G.BODY_BOTTOM)))
                hw = (G.DECK_DOWN_W + (G.DECK_UP_W - G.DECK_DOWN_W) * f) / 2.0
                # ⚠ 券石必须贴在侧墙外表面(yo=hw), 薄层向【外】凸出,
                #   不可向内(y<hw)——否则薄片伸进洞内, 在洞内投出横贯暗带,
                #   表现为"每个洞被一道黑横杠腰斩"(已实测复现)。
                yo = hw
                for yy in (yo + rt, yo, -yo, -(yo + rt)):
                    quad.append((xc + a * math.cos(tt), yy, zz))
            vs = [bm.verts.new(p) for p in quad]
            for f in ((0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)):
                try: bm.faces.new([vs[k] for k in f])
                except ValueError: pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.normal_update()
    return bm


def build_deck_bm():
    """桥面(薄板) + 望柱(64/侧=128) + 栏板 + 蹲狮 + 桥头异兽4只。"""
    bm = bmesh.new()
    LION_SPOTS = []
    rail_y = G.DECK_UP_W / 2.0 - 0.18
    n = 200
    prev = None
    for s in range(n + 1):
        x = -G.BRIDGE_LEN / 2.0 + G.BRIDGE_LEN * s / n
        z = G.deck_z(x)
        cur = [bm.verts.new((x, -rail_y, z)), bm.verts.new((x, rail_y, z))]
        if prev:
            try: bm.faces.new((prev[0], cur[0], cur[1], prev[1]))
            except ValueError: pass
        prev = cur
    # 望柱 64/侧
    NPOST = 63
    for side in (-1, 1):
        y = side * (rail_y + 0.14)
        for i in range(NPOST + 1):
            x = -G.BRIDGE_LEN / 2.0 + G.BRIDGE_LEN * i / NPOST
            z = G.deck_z(x)
            b, t = 0.24, z + 1.20
            v = [bm.verts.new(p) for p in (
                (x-b, y-0.17, z), (x+b, y-0.17, z), (x+b, y+0.17, z), (x-b, y+0.17, z),
                (x-b, y-0.17, t), (x+b, y-0.17, t), (x+b, y+0.17, t), (x-b, y+0.17, t))]
            for f in ((0,1,2,3),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)):
                try: bm.faces.new([v[k] for k in f])
                except ValueError: pass
            # 蹲狮: 独立 mesh(见 lions.py), 稍后合并
            LION_SPOTS.append((x, y, z + 1.18, i, side))
        # ── 石栏板(GPT v4 第2刀): 厚实体, 远景才读成"石栏板"而非"细横杆" ──
        # 有效高 0.62, 板厚 0.14; 下槛 0.18 高; 顶部扶手 0.13 厚
        # 栏板: 远景要读成"连续石栏板"而非"细横杆"。
        # 关键不是更高, 而是【更厚 + 更贴近桥面边缘 + 满铺不断缝】。
        # 原 0.14m 厚在 2.38m 柱距下几乎不可见 -> 读成栅栏(已实测复现)。
        PANEL_H, PANEL_T, SILL_H, SILL_T, RAIL_T = 0.66, 0.26, 0.20, 0.34, 0.20

        def slab(x1, z1, x2, z2, h, t, ycen):
            v = [bm.verts.new(p) for p in (
                (x1, ycen-t/2, z1), (x2, ycen-t/2, z2),
                (x2, ycen+t/2, z2), (x1, ycen+t/2, z1),
                (x1, ycen-t/2, z1+h), (x2, ycen-t/2, z2+h),
                (x2, ycen+t/2, z2+h), (x1, ycen+t/2, z1+h))]
            for f in ((0,1,2,3),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)):
                try: bm.faces.new([v[k] for k in f])
                except ValueError: pass

        for i in range(NPOST):
            x1 = -G.BRIDGE_LEN / 2.0 + G.BRIDGE_LEN * i / NPOST
            x2 = -G.BRIDGE_LEN / 2.0 + G.BRIDGE_LEN * (i + 1) / NPOST
            z1, z2 = G.deck_z(x1), G.deck_z(x2)
            # 满铺: 栏板/下槛/扶手连续通长, 望柱压在栏板外侧 —— 形成连续白石边界
            slab(x1+0.05, z1+SILL_H, x2-0.05, z2+SILL_H, PANEL_H, PANEL_T, y)
            slab(x1+0.05, z1,        x2-0.05, z2,        SILL_H, SILL_T, y)
            slab(x1+0.05, z1+SILL_H+PANEL_H, x2-0.05, z2+SILL_H+PANEL_H, 0.15, RAIL_T, y)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.normal_update()
    return bm, LION_SPOTS


def build_lions_bm(spots):
    """每根望柱柱头放蹲狮。GPT v4: 每侧 16 根 5 狮柱 + 48 根 4 狮柱 = 272, 两侧 544。
    544 只全做高模不现实 -> 每柱放 1 只 LOD-M(约 0.22m 高) + 柱侧 1 只小狮,
    合计 2*64*2 = 256 只实体, 其余以柱头狮群轮廓表示(远景不可分辨)。"""
    import math as _m
    bm = bmesh.new()
    for (x, y, z, idx, side) in spots:
        L = LIONS.lion_bm(0.30, variant=idx % 2, seed=idx * 13 + side)
        # 平移就位(望柱柱头)
        bmesh.ops.translate(L, verts=L.verts, vec=(x, y, z))
        # 合并
        me = bpy.data.meshes.new("_tmp_lion")
        L.to_mesh(me); L.free()
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
        # 柱侧小狮(幼狮)
        L2 = LIONS.lion_bm(0.17, variant=1, seed=idx * 29)
        bmesh.ops.translate(L2, verts=L2.verts, vec=(x - 0.10, y + 0.11 * side, z - 0.02))
        me2 = bpy.data.meshes.new("_tmp_lion2")
        L2.to_mesh(me2); L2.free()
        bm.from_mesh(me2)
        bpy.data.meshes.remove(me2)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.normal_update()
    return bm


def build_beast_bm():
    """桥头大型石兽 4 只(两端各 2 只)。

    GPT v4 第1刀: 这 4 只是"一眼认出十七孔桥"性价比最高的识别增强,
    必须比望柱狮大约 4-5 倍。工作值: 高 1.05-1.20m, 长 1.15-1.35m, 宽 0.45-0.55m,
    中心距 1.1-1.4m。园方未命名, 故按"蹲兽"轮廓做(低身、张口、卷尾、阔胸)。
    """
    bm = bmesh.new()
    H, Lg, Wd = 1.12, 1.25, 0.50        # 高/长/宽
    for xe in (-G.BRIDGE_LEN/2 + 1.5, G.BRIDGE_LEN/2 - 1.5):
        z = G.deck_z(xe)
        for k, side in enumerate((-1, 1)):
            y = side * (G.DECK_UP_W/2 - 0.10) + side * k * 0.10
            sx = 1.0 if xe > 0 else -1.0
            def box(cx, cy, cz, sx_, sy_, sz_):
                b = [bm.verts.new(p) for p in (
                    (cx-sx_/2, cy-sy_/2, cz), (cx+sx_/2, cy-sy_/2, cz),
                    (cx+sx_/2, cy+sy_/2, cz), (cx-sx_/2, cy+sy_/2, cz),
                    (cx-sx_/2, cy-sy_/2, cz+sz_), (cx+sx_/2, cy-sy_/2, cz+sz_),
                    (cx+sx_/2, cy+sy_/2, cz+sz_), (cx-sx_/2, cy+sy_/2, cz+sz_))]
                for f in ((0,1,2,3),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)):
                    try: bm.faces.new([b[k] for k in f])
                    except ValueError: pass
            # 须弥座
            box(xe, y, z+0.10, Lg*1.10, Wd*1.35, 0.20)
            # 躯干(低伏)
            box(xe, y, z+0.20+0.30, Lg*0.92, Wd*0.92, 0.58)
            # 前胸(略高)
            box(xe+sx*0.30, y, z+0.20+0.42, Lg*0.42, Wd*0.86, 0.48)
            # 头(偏大, 前伸)
            box(xe+sx*0.52, y, z+0.20+0.72, Lg*0.30, Wd*0.72, 0.36)
            # 吻
            box(xe+sx*0.70, y, z+0.20+0.66, Lg*0.16, Wd*0.52, 0.22)
            # 前腿
            for fy in (-0.16, 0.16):
                box(xe+sx*0.40, y+fy, z+0.10, 0.16, 0.14, 0.26)
            # 后座
            box(xe-sx*0.34, y, z+0.10, 0.20, Wd*0.80, 0.22)
            # 卷尾
            for j in range(4):
                a = j/3.0
                box(xe - sx*(0.44+0.06*a), y + side*0.10*a,
                    z+0.20+0.58+0.10*a, 0.12, 0.12, 0.12)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.normal_update()
    return bm


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    # GPT v4 第3刀: 大块石作。层高 0.45-0.60m, 灰缝压到 8-15mm,
    # 风化噪声降 50% —— 原参数像"规则砖墙+云斑噪声", 石头颗粒太碎。
    # 实拍订正(RM-123108 4x): 墙身=暖灰白大块砌石, 券圈=明显更白的汉白玉
    m_body = MAT.stone_material("stone_body", (0.640, 0.600, 0.520),
                                joint=0.007, course_h=0.68, weather=0.22)
    m_ring = MAT.stone_material("stone_ring", (0.850, 0.828, 0.775),
                                joint=0.010, course_h=0.24, weather=0.14)
    m_rail = MAT.marble_material("marble")
    m_water = MAT.water_material()

    # ── 墩脚基石带(实拍: 水上约1m 一道通长凸带, 其下有阴影线) ──
    def hwz(z):
        f = max(0.0, min(1.0, (z - G.BODY_BOTTOM) / (G.deck_z(0.0) - G.BODY_BOTTOM)))
        return (G.DECK_DOWN_W + (G.DECK_UP_W - G.DECK_DOWN_W) * f) / 2.0
    pl = bmesh.new()
    B0, B1, BOUT = 0.80, 1.20, 0.10
    X0, X1 = -G.BRIDGE_LEN / 2.0 - 3.0, G.BRIDGE_LEN / 2.0 + 3.0
    for side in (-1, 1):
        ya, yb = side * (hwz(B0) + BOUT), side * (hwz(B1) + BOUT)
        v = [pl.verts.new(q) for q in (
            (X0, ya, B0), (X1, ya, B0), (X1, yb, B1), (X0, yb, B1),
            (X0, side*hwz(B0), B0), (X1, side*hwz(B0), B0),
            (X1, side*hwz(B1), B1), (X0, side*hwz(B1), B1))]
        for fc in ((0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)):
            try: pl.faces.new([v[k] for k in fc])
            except ValueError: pass
    bmesh.ops.recalc_face_normals(pl, faces=pl.faces[:]); pl.normal_update()
    bm_to_obj(pl, "pier_plinth", m_ring)

    # ── 桥沿仰天石(实拍: 桥面边缘一道白色凸出带, 比墙身白) ──
    co = bmesh.new()
    n = 200
    prev = None
    ye0, ye1 = -G.DECK_UP_W / 2.0 - 0.10, G.DECK_UP_W / 2.0 + 0.10
    for k in range(n + 1):
        x = -G.BRIDGE_LEN / 2.0 + G.BRIDGE_LEN * k / n
        z = G.deck_z(x)
        cur = [co.verts.new((x, ye0, z - 0.10)), co.verts.new((x, ye1, z - 0.10)),
               co.verts.new((x, ye1, z + 0.05)), co.verts.new((x, ye0, z + 0.05))]
        if prev:
            for a, b2 in ((0,1),(1,2),(2,3),(3,0)):
                try: co.faces.new((prev[a], prev[b2], cur[b2], cur[a]))
                except ValueError: pass
        prev = cur
    bmesh.ops.recalc_face_normals(co, faces=co.faces[:]); co.normal_update()
    bm_to_obj(co, "deck_cornice", m_rail)
    # 水面
    wb = bmesh.new()
    S = 2500.0
    wb.faces.new([wb.verts.new(p) for p in ((-S,-S,0),(S,-S,0),(S,S,0),(-S,S,0))])
    bm_to_obj(wb, "water", m_water)
    # 桥体
    body = bm_to_obj(G.build_body_bm(), "bridge_body", m_body)
    void = bm_to_obj(G.build_void_bm(), "void_tmp", m_body)
    m = body.modifiers.new("carve", 'BOOLEAN')
    m.operation = 'DIFFERENCE'
    m.solver = 'EXACT'
    m.object = void
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.data.objects.remove(void, do_unlink=True)
    # 桥台加长(GPT v4 第4刀): 每端 BRIDGE_ABUT=1.35m 且向岸收分。
    # 值取 facts.BRIDGE_ABUT(T2b 闭合归因唯一解: 107.3+16*2.50+2*1.35=150.0 精确闭合);
    # GPT 设计提案 2.00(assumptions.BRIDGE_ABUT_TARGET)未获事实地位, 不进生成器。
    ab = bmesh.new()
    for sgn in (-1, 1):
        x_out = sgn * G.BRIDGE_LEN / 2.0
        x_in = x_out - sgn * G.BRIDGE_ABUT
        zt = G.deck_z(x_out)
        w_out = G.DECK_UP_W * 1.05
        w_in = G.DECK_DOWN_W * 0.98
        vs = [ab.verts.new(p) for p in (
            (x_out, -w_out/2, G.BODY_BOTTOM), (x_out, w_out/2, G.BODY_BOTTOM),
            (x_in,  w_in/2,  G.BODY_BOTTOM), (x_in, -w_in/2, G.BODY_BOTTOM),
            (x_out, -w_out/2, zt), (x_out, w_out/2, zt),
            (x_in,  w_in/2,  zt), (x_in, -w_in/2, zt))]
        for f in ((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)):
            try: ab.faces.new([vs[k] for k in f])
            except ValueError: pass
    bmesh.ops.recalc_face_normals(ab, faces=ab.faces[:]); ab.normal_update()
    abut = bm_to_obj(ab, "abutments", m_body)
    m2 = body.modifiers.new("ab", 'BOOLEAN'); m2.operation='UNION'; m2.solver='EXACT'; m2.object=abut
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.modifier_apply(modifier=m2.name)
    bpy.data.objects.remove(abut, do_unlink=True)
    # ── 布尔后修正券洞内壁法线 ──
    # EXACT 求解器会打乱内壁法线 -> 朝外的面渲染成黑楔/死黑洞(实测 494/494 拱腹面背心)。
    # 判据(几何上严格): 空腔内的面, 法线必须指向该洞的"内法线方向":
    #   拱段(z>SPRINGER): 圆弧内法线 = 面心 -> 圆心(xc, SPRINGER)
    #   矩形段(z<=SPRINGER): 内法线 = 水平指向洞轴 x=xc
    #
    # 2026-10-04 两处修正(由 L2 判据 qa_l2.py 的真阳性暴露, 见 .superpowers/sdd/e30-briefs/task-task-5-report.md):
    #  ①过滤条件曾写成 `if abs(n.y) < 0.05: continue` 并注"径向面才需要判"——注释与代码相反,
    #    |n.y|≈0 正是径向面(拱腹面)却被跳过, 264 次翻转全打在 ±y 侧墙面上, 拱腹 0→0 不变。
    #    现改为 `> 0.05: continue`: 只处理侧墙面, 拱腹面由下面的"指向圆心"判据负责。
    #  ②本工序原先在桥台 UNION **之前**, 防护不了 UNION 引入的新破面; 现移到 UNION 之后。
    me = body.data
    cavities = [(G.PIER_X[i] + G.PIER_X[i + 1]) / 2.0 for i in range(G.N_SPAN)]
    flipped = 0
    for poly in me.polygons:
        c = poly.center
        for idx, xc in enumerate(cavities):
            a = G.SPANS[idx] / 2.0
            if abs(c.x - xc) > a + 0.05: continue
            n = poly.normal
            if abs(n.y) > 0.05: continue          # 侧墙面(|y|法线)不判, 只判径向面
            if c.z > G.SPRINGER + 0.05:
                b = a * 2.0 * G.ARCH_RATIO
                dx, dz = c.x - xc, c.z - G.SPRINGER
                if dz > b or (dx*dx + dz*dz) > (a + 0.2) ** 2: continue
                ax_, az_ = -dx, -dz
            else:
                if abs(c.x - xc) > a - 0.02: continue
                ax_, az_ = (xc - c.x), 0.0
            L = math.hypot(ax_, az_)
            if L < 1e-6: continue
            if n.x * ax_ / L + n.z * az_ / L < 0.0:
                poly.flip(); flipped += 1
            break
    me.update()
    print("  翻转券洞内壁破面: %d" % flipped)
    # ── 起拱线石 impost (GPT v4 建议第3项) ──
    # 直边墙 -> 半圆券的转折处本该有一块横向凸出的承托石。
    # 缺它时该处法线突变成锐棱, 在洞内形成一条贯通的黑色暗带(实测复现)。
    imp = bmesh.new()
    IMP_H, IMP_OUT = 0.50, 0.06
    for i in range(G.N_SPAN):
        xc = (G.PIER_X[i] + G.PIER_X[i + 1]) / 2.0
        a = G.SPANS[i] / 2.0
        deck_c = G.deck_z(xc)
        for sgn in (-1, 1):
            f = max(0.0, min(1.0, (G.SPRINGER - G.BODY_BOTTOM) / (deck_c - G.BODY_BOTTOM)))
            hw = (G.DECK_DOWN_W + (G.DECK_UP_W - G.DECK_DOWN_W) * f) / 2.0
            # 起拱线石贴在券洞两侧的内壁上, 从 z-SPRINGER-IMP_H/2 到 +IMP_H/2
            x0 = xc + sgn * a
            v = [imp.verts.new(p) for p in (
                (x0, sgn*(hw-0.02), G.SPRINGER-IMP_H/2),
                (x0, sgn*(hw+IMP_OUT), G.SPRINGER-IMP_H/2),
                (x0, sgn*(hw+IMP_OUT), G.SPRINGER+IMP_H/2),
                (x0, sgn*(hw-0.02), G.SPRINGER+IMP_H/2))]
            for f2 in ((0,1,2,3),(3,2,1,0)):
                try: imp.faces.new([v[k] for k in f2])
                except ValueError: pass
    bmesh.ops.recalc_face_normals(imp, faces=imp.faces[:]); imp.normal_update()
    bm_to_obj(imp, "impost", m_ring)
    bm_to_obj(build_voussoir_bm(), "voussoir", m_ring)
    deck_bm, spots = build_deck_bm()
    bm_to_obj(deck_bm, "deck_rail", m_rail)
    bm_to_obj(build_lions_bm(spots), "lions", m_rail)   # 蹲狮独立层
    bm_to_obj(build_beast_bm(), "beasts", m_rail)
    # ── 第4刀: 两端地形接口 (GPT v4) ──
    # 真桥一端接东堤、一端接南湖岛, 不是 150m 桥体独立漂在水里。
    # 每端接 5m 石铺缓坡 + 微隆起地面, 埋掉大部 14.6m 端面。
    ab = bmesh.new()
    for sgn in (-1, 1):
        x_e = sgn * G.BRIDGE_LEN / 2.0
        x_o = x_e + sgn * 42.0                     # 长堤延伸到画外, 读作接岸
        z_e = G.deck_z(x_e)
        z_o = 0.8                                   # 堤远端接近水面
        S = 9.0                                     # 堤面宽度渐扩
        v = [ab.verts.new(p) for p in (
            (x_e, -G.DECK_DOWN_W/2, G.BODY_BOTTOM), (x_e, G.DECK_DOWN_W/2, G.BODY_BOTTOM),
            (x_o,  G.DECK_DOWN_W/2 + S, G.BODY_BOTTOM), (x_o, -G.DECK_DOWN_W/2 - S, G.BODY_BOTTOM),
            (x_e, -G.DECK_DOWN_W/2, z_e), (x_e, G.DECK_DOWN_W/2, z_e),
            (x_o,  G.DECK_DOWN_W/2 + S, z_o), (x_o, -G.DECK_DOWN_W/2 - S, z_o))]
        for f in ((0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)):
            try: ab.faces.new([v[k] for k in f])
            except ValueError: pass
    bmesh.ops.recalc_face_normals(ab, faces=ab.faces[:]); ab.normal_update()
    bm_to_obj(ab, "abutment_ground", m_body)
    # 全部桥体与引道构件统一绕 Z 转桥轴方位。
    # 2026-10-04 修: abutment_ground 曾漏在此名单外(旋转 0° vs 本体 -112°),
    # 导致引道块孤悬水中且遮挡正交侧立面。T6 出图时用 hide_render 规避是绕过,
    # 根因在此——它与本体同父级 m_body, 本就该一起转。
    for n in ("bridge_body","impost","voussoir","deck_rail","lions","beasts",
              "pier_plinth","deck_cornice","abutment_ground"):
        bpy.data.objects[n].rotation_euler = (0,0,-math.radians(BRIDGE_AXIS_AZ))
    # 照明
    w = bpy.data.worlds.new("World"); bpy.context.scene.world = w; w.use_nodes=True
    nt = w.node_tree
    for n in list(nt.nodes):
        if n.bl_idname != 'ShaderNodeOutputWorld':
            nt.nodes.remove(n)
    outw = [n for n in nt.nodes if n.bl_idname=='ShaderNodeOutputWorld'][0]
    sky = nt.nodes.new('ShaderNodeTexSky')
    sky.sky_type = 'PREETHAM'
    # 实拍口径(RM-123108): 晴空深蓝, 太阳在相机左后侧高仰角, 侧光掠桥脸
    sky.sun_elevation = math.radians(35.0)
    sky.sun_rotation = math.radians(292.0)    # WNW: 侧掠相机面(NW), 石头受暖阳
    sky.altitude = 10; sky.air_density = 1.0
    sky.aerosol_density = 0.25; sky.ozone_density = 1.0
    sky.ground_albedo = 0.12
    bgw = nt.nodes.new('ShaderNodeBackground')
    bgw.inputs['Strength'].default_value = 0.38
    nt.links.new(sky.outputs['Color'], bgw.inputs['Color'])
    nt.links.new(bgw.outputs['Background'], outw.inputs['Surface'])
    d1 = bpy.data.lights.new("Key", type='SUN'); d1.energy=3.9; d1.angle=math.radians(1.2)
    d1.color = (1.0, 0.94, 0.84)
    o1 = bpy.data.objects.new("Key", d1); bpy.context.collection.objects.link(o1)
    # Key 对齐天空太阳: az292(WNW) elev35 -> 光行向 ESE 下
    from mathutils import Vector as _V
    o1.rotation_euler = _V((0.760, -0.307, -0.574)).to_track_quat('-Z','Y').to_euler()
    sc = bpy.context.scene
    sc.render.engine='CYCLES'; sc.cycles.device='GPU'
    cp = bpy.context.preferences.addons['cycles'].preferences
    try: cp.compute_device_type='METAL'
    except Exception: pass
    for dv in cp.devices: dv.use = (dv.type=='METAL')
    sc.cycles.samples=200; sc.cycles.use_adaptive_sampling=True
    sc.cycles.adaptive_threshold=0.008; sc.cycles.use_denoising=True
    sc.cycles.max_bounces=6
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    sc.render.image_settings.file_format='PNG'
    return sc


if __name__ == "__main__":
    build()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "e30_bridge.blend"))
    print("SAVED v2")
