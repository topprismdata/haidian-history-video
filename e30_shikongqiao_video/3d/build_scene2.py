"""v2 场景: 整体桥体 + 布尔挖券洞 + 券脸楔石 + 栏杆 + 异兽。"""
import bpy, bmesh, os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bridge_geom2 as G
import materials as MAT
import lions2 as LIONS   # 蹲狮 v2: 母模布尔并 + linked duplicates(旧 lions.py 球堆叠已弃用)
import beasts2 as BEASTS # 靠山兽 v2: 4只 linked duplicates(5000+面/水密/正名靠山兽)
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
    """桥面大石板铺装 + 望柱(64/侧=128) + 双孔透空官式栏板 + 544只石狮位。"""
    bm = bmesh.new()
    LION_SPOTS = []
    rail_y = G.DECK_UP_W / 2.0 - 0.18
    n = 200
    prev = None
    # 桥面大石板铺装: 错缝石板排布, 杜绝纯平白片感
    for s in range(n + 1):
        x = -G.BRIDGE_LEN / 2.0 + G.BRIDGE_LEN * s / n
        z = G.deck_z(x)
        # 沿桥面分为左/中/右三块石板带, 带有极细的微下凹纵向石缝
        cur = [
            bm.verts.new((x, -rail_y, z)),
            bm.verts.new((x, -rail_y * 0.33, z)),
            bm.verts.new((x,  rail_y * 0.33, z)),
            bm.verts.new((x,  rail_y, z))
        ]
        if prev:
            for j in range(3):
                try: bm.faces.new((prev[j], cur[j], cur[j+1], prev[j+1]))
                except ValueError: pass
        prev = cur

    # 望柱 (64/侧 = 全桥两边合计 128 根望柱)
    NPOST = 63
    for side in (-1, 1):
        y = side * (rail_y + 0.14)
        for i in range(NPOST + 1):
            x = -G.BRIDGE_LEN / 2.0 + G.BRIDGE_LEN * i / NPOST
            z = G.deck_z(x)
            b, t = 0.22, z + 1.18
            # 方形望柱身 + 柱头承台
            v = [bm.verts.new(p) for p in (
                (x-b, y-0.16, z), (x+b, y-0.16, z), (x+b, y+0.16, z), (x-b, y+0.16, z),
                (x-b, y-0.16, t), (x+b, y-0.16, t), (x+b, y+0.16, t), (x-b, y+0.16, t))]
            for f in ((0,1,2,3),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)):
                try: bm.faces.new([v[k] for k in f])
                except ValueError: pass
            # 柱头石狮位: 狮底坐于 t (z+1.18), 主狮比例 0.32m
            LION_SPOTS.append((x, y, t, i, side))

        def slab(x1, z1, x2, z2, h, t, ycen):
            v = [bm.verts.new(p) for p in (
                (x1, ycen-t/2, z1), (x2, ycen-t/2, z2),
                (x2, ycen+t/2, z2), (x1, ycen+t/2, z1),
                (x1, ycen-t/2, z1+h), (x2, ycen-t/2, z2+h),
                (x2, ycen+t/2, z2+h), (x1, ycen+t/2, z1+h))]
            for f in ((0,1,2,3),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)):
                try: bm.faces.new([v[k] for k in f])
                except ValueError: pass

        # ── 官式双孔透空石栏板 (依据老照片 11 / 14_ref 真实形制重构) ──
        # 每开间含: 地栿(下槛) + 实心下华板 + 双孔透空区(含中梃荷叶墩) + 顶部寻杖扶手
        for i in range(NPOST):
            x1 = -G.BRIDGE_LEN / 2.0 + G.BRIDGE_LEN * i / NPOST
            x2 = -G.BRIDGE_LEN / 2.0 + G.BRIDGE_LEN * (i + 1) / NPOST
            z1, z2 = G.deck_z(x1), G.deck_z(x2)
            xc = (x1 + x2) / 2.0
            zc = (z1 + z2) / 2.0

            # 1. 地栿 (下槛石基): 高 0.18m, 宽 0.30m
            slab(x1 + 0.05, z1, x2 - 0.05, z2, 0.18, 0.30, y)

            # 2. 下华板 (实心下区): 高 0.22m, 宽 0.20m
            slab(x1 + 0.05, z1 + 0.18, x2 - 0.05, z2 + 0.18, 0.22, 0.20, y)

            # 3. 透空开窗区 (高 0.22m, 宽 0.20m):
            #    左边边框 (宽 0.14m)
            slab(x1 + 0.05, z1 + 0.40, x1 + 0.19, z1 + 0.40, 0.22, 0.20, y)
            #    中央中梃荷叶墩 (宽 0.20m)
            slab(xc - 0.10, zc + 0.40, xc + 0.10, zc + 0.40, 0.22, 0.20, y)
            #    右边边框 (宽 0.14m)
            slab(x2 - 0.19, z2 + 0.40, x2 - 0.05, z2 + 0.40, 0.22, 0.20, y)
            #    注: [x1+0.19, xc-0.10] 与 [xc+0.10, x2-0.19] 为真实透空镂孔!

            # 4. 寻杖 (压顶扶手石): 高 0.14m, 宽 0.24m, 贯通压顶
            slab(x1 + 0.05, z1 + 0.62, x2 - 0.05, z2 + 0.62, 0.14, 0.24, y)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.normal_update()
    return bm, LION_SPOTS


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
    # GPT v4 第3刀: 大块石作。层高 0.45-0.60m, 灰缝压到 8-15mm。
    # 2026-10-05 M7 勘误+接线(C2): M4「渲染基色走实拍暖白(252,245,227)」作废——
    # 主控分档复采 ref_elevation.jpg: 亮部 R-B=-6.2 / 中间调 -18.3 / 暗部 -31.1, **全档偏冷**,
    # M4 的暖白采样点误采(眩光/异区)。暖色属光照不属 albedo, 不得烘进基色。
    # 石种=青石(京报网/中新网2025-12-09逐字「以青石筑成桥体,以汉白玉为栏杆」),
    # albedo 走 qingshi_material 冷灰蓝; 栏杆/望柱/狮=汉白玉不变。
    m_body = MAT.qingshi_material("stone_body")
    m_ring = MAT.qingshi_material("stone_ring", (0.350, 0.382, 0.418))
    m_rail = MAT.marble_material("marble")
    m_water = MAT.water_material()
    m_earth = MAT.earth_material("shore_earth")

    # ── 墩脚基石带(实拍: 水上约1m 一道通长凸带, 其下有阴影线) ──
    def hwz(z):
        f = max(0.0, min(1.0, (z - G.BODY_BOTTOM) / (G.deck_z(0.0) - G.BODY_BOTTOM)))
        return (G.DECK_DOWN_W + (G.DECK_UP_W - G.DECK_DOWN_W) * f) / 2.0
    pl = bmesh.new()
    B0, B1, BOUT = 0.80, 1.20, 0.10
    # 墩脚基石带: 仅在 16 个桥墩及两端桥台表面出挑, 严禁横穿 17 个券洞净空!
    # 桥墩区间列表: 16 个实心分隔墩 + 2 端桥台
    plinth_segments = []
    # 左桥台
    plinth_segments.append((-G.BRIDGE_LEN / 2.0 - 1.5, -G.BRIDGE_LEN / 2.0 + G.BRIDGE_ABUT))
    # 16 个桥墩
    for i in range(G.N_SPAN - 1):
        px0 = G.PIER_X[i + 1]
        px1 = px0 + G.PIER_W
        plinth_segments.append((px0 + 0.02, px1 - 0.02))
    # 右桥台
    plinth_segments.append((G.BRIDGE_LEN / 2.0 - G.BRIDGE_ABUT, G.BRIDGE_LEN / 2.0 + 1.5))

    for (px0, px1) in plinth_segments:
        for side in (-1, 1):
            ya, yb = side * (hwz(B0) + BOUT), side * (hwz(B1) + BOUT)
            v = [pl.verts.new(q) for q in (
                (px0, ya, B0), (px1, ya, B0), (px1, yb, B1), (px0, yb, B1),
                (px0, side*hwz(B0), B0), (px1, side*hwz(B0), B0),
                (px1, side*hwz(B1), B1), (px0, side*hwz(B1), B1))]
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
    # ── 布尔残片清理(2026-10-05 二审修复): EXACT 布尔在桥体表面留下切刀侧壁残片
    #    (实测 13 顶点, 横向 -3.28~-3.7 / z 6.7~7.75), 悬在券脸前方 0.5~0.9m 遮挡题额区。
    #    判据: 桥身顶点不得超出自身收分轮廓 hw(z)+2cm(两端桥台加长区除外)。
    me = body.data
    bm = bmesh.new(); bm.from_mesh(me)
    rm = []
    for v in bm.verts:
        x, y, z = v.co
        if abs(x) > G.BRIDGE_LEN / 2.0 - 2.0:
            continue
        zt = G.deck_z(x)
        f = max(0.0, min(1.0, (z - G.BODY_BOTTOM) / (zt - G.BODY_BOTTOM)))
        hw = (G.DECK_DOWN_W + (G.DECK_UP_W - G.DECK_DOWN_W) * f) / 2.0
        if abs(y) > hw + 0.02:
            rm.append(v)
    if rm:
        bmesh.ops.delete(bm, geom=rm, context='VERTS')
    bm.to_mesh(me); bm.free(); me.update()
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
    # 靠山兽: linked duplicates(2026-10-05 最佳实践) —— 4 对象共享 2 个 mesh datablock,
    # 替代旧 build_beast_bm() 盒块堆叠(384 顶点)。单只 5000+ 面, 水密, 剪影清晰。
    beast_spots = []
    _bi = 0
    for xe in (-G.BRIDGE_LEN / 2 + 1.5, G.BRIDGE_LEN / 2 - 1.5):
        z = G.deck_z(xe)
        for k, side in enumerate((-1, 1)):
            y = side * (G.DECK_UP_W / 2 - 0.10) + side * k * 0.10
            facing = 1.0 if xe > 0 else -1.0
            beast_spots.append((xe, y, z, _bi, facing))
            _bi += 1
    beast_objs = BEASTS.place_beasts(beast_spots, name="beasts", size=1.12, material=m_rail)
    # 蹲狮: linked duplicates(2026-10-05 口径) —— 256 对象共享 2 个 mesh datablock,
    # 不再并成单个 "lions" 大 mesh(反模式: 文件膨胀/无法实例化/回归 diff 不归因)。
    lion_objs = LIONS.place_lions(spots, m_rail)
    # ── 第4刀改版(2026-10-05, 燕翅型桥台): 引道缓坡 + 两侧八字燕翅墙 + 岸坡地形 ──
    # 文献: 桥台形式三型——带燕翅(古籍"雁翅")/凹字/一字; 前墙古称金刚墙, 两侧八字形
    # 挡墙称燕翅墙(顺水金刚墙) —— 茅以升基金会《中国古代石拱桥——古桥各部名称》
    # (https://www.mysf.org.cn/Detail/index.html?id=691&aid=291)。
    # 视觉根因: 原楔形块垂直插水, 桥像漂着; 燕翅墙向岸斜展 + 岸坡承接才形成"接岸"读感。
    # 数值地位: 展开角35°/翼长24m/墙厚1.4m/岸坡顶2.1m 均为[工作值](无文献数值)。
    # ⚠ 2026-10-05 燕翅研究(refs/abutment_design.md): 原注「常见做法30-45°」无源已删;
    # 『带燕翅型』系形制推断非文献直陈; 卫星图版负读数: 岛端无出岸自由燕翅墙,
    # WING_L=24 与图版矛盾(观测展宽带仅8-10m), 修订≤12m或锚岸式待表现层批处理;
    # 本体端部1.35m桥台(facts.BRIDGE_ABUT, 已UNION进bridge_body)属本体, 不在此列, 未动。
    WING_L = 24.0            # 翼墙水平投影长
    WING_ANG = math.radians(35.0)
    WING_T = 1.4             # 翼墙厚
    BANK_Z = 2.1             # 岸坡顶标高(实拍两端岸线高于水面约2m)
    ab = bmesh.new()
    for sgn in (-1, 1):
        x_e = sgn * G.BRIDGE_LEN / 2.0
        z_e = G.deck_z(x_e)
        dy0 = G.DECK_DOWN_W / 2.0
        dxw = WING_L * math.cos(WING_ANG)
        dyw = dy0 + WING_L * math.sin(WING_ANG)
        # (1) 引道缓坡: 根部断面与本体端墙收分齐平(底=下宽半+0.06埋入, 顶=上宽半+0.12),
        #     坡面拍 battered 斜面 -> 与端墙无 V 形凹槽(垂直裙曾留黑三角缝, 实测复现)。
        #     2026-10-05 收窄: 原全下宽14.6m 读成"混凝土平台"; 真引道是路面宽,
        #     下部展开的端面由燕翅墙夹持(前墙/金刚墙读感)。
        RT0, RT1, RAMP_L = G.DECK_UP_W / 2.0 + 0.12, 5.2, 14.0
        B0W = dy0 + 0.06                       # 根部底半宽(埋入本体端墙)
        x_r = x_e - sgn * 0.06
        x_o = x_e + sgn * RAMP_L
        zt_tip = BANK_Z + 0.85                 # 坡端没入岸坡顶下
        vs = [ab.verts.new(p) for p in (
            (x_r, -B0W, G.BODY_BOTTOM), (x_r, B0W, G.BODY_BOTTOM),
            (x_o,  RT1, G.BODY_BOTTOM), (x_o, -RT1, G.BODY_BOTTOM),
            (x_r, -RT0, z_e), (x_r, RT0, z_e),
            (x_o,  RT1, zt_tip), (x_o, -RT1, zt_tip))]
        for f in ((0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)):
            try: ab.faces.new([vs[k] for k in f])
            except ValueError: pass
        # (2) 燕翅墙 x2: 自端墙根(埋入本体0.5m防露缝)八字斜展, 顶面沿轴向
        #     从桥面端高下斜至岸坡顶上方0.35m, 墙身直落水下基座。
        for side in (-1, 1):
            d = Vector((math.cos(WING_ANG), side * math.sin(WING_ANG)))
            n = Vector((-side * math.sin(WING_ANG), math.cos(WING_ANG)))  # 离轴法向
            z_root, z_tip = 3.60, BANK_Z + 0.35   # 翼墙顶=挡土墙高(工作值), 低于桥面
            A = Vector((x_e - sgn * 0.5, side * (G.DECK_UP_W / 2.0 - 0.1)))
            B = A + d * WING_L
            pts = [(A.x, A.y), (B.x, B.y),
                   (B.x + n.x * WING_T, B.y + n.y * WING_T),
                   (A.x + n.x * WING_T, A.y + n.y * WING_T)]
            def _ztop(px, py):
                f = max(0.0, min(1.0, (Vector((px, py)) - A).dot(d) / WING_L))
                return z_root * (1.0 - f) + z_tip * f
            vs = [ab.verts.new((px, py, G.BODY_BOTTOM)) for px, py in pts] \
               + [ab.verts.new((px, py, _ztop(px, py))) for px, py in pts]
            for f in ((4,5,6,7), (0,3,2,1), (0,1,5,4), (1,2,6,5), (2,3,7,6), (3,0,4,7)):
                try: ab.faces.new([vs[k] for k in f])
                except ValueError: pass
    bmesh.ops.recalc_face_normals(ab, faces=ab.faces[:]); ab.normal_update()
    bm_to_obj(ab, "abutment_ground", m_body)
    # (3) 岸坡地形: 两端各一片低矮岸坡(顶2.1-3.4m, 实拍岸线高于水面约2m),
    #     内缘塞入桥端/引道之下防裂缝, 外缘与沿岸两端以陡坡没入水下(-2.4m)自然生成水线。
    #     顶面起伏为确定性正弦叠加(非随机位移; 环境构件虽允许随机, 保持可复现)。
    bk = bmesh.new()
    for sgn in (-1, 1):
        x_e = sgn * G.BRIDGE_LEN / 2.0
        # 2026-10-05 修"岸坡生硬立方体"(主控量化: 岸缘水平梯度 max 81.7):
        #   ① 网格 24x40 -> 72x120: 4m 级刻面让岸线读成折线硬边;
        #   ② 横向宽度随 u 收窄(近桥端 ±30m 塞进翼墙足迹下防露切面, 向外展到 ±46m 再收)
        #     —— 首版 ±20m 起步把翼墙/引道端部的垂直切面露了出来(实测复现后回调);
        #   ③ 加两档高频正弦(确定性, 无随机)让岸线弯曲自然。
        NU, NV = 72, 120
        U0, U1, V0, V1 = -4.0, 96.0, -52.0, 62.0   # 相机侧收短, 防'绿色滑梯'楔形
        def bank_h(u, v):
            r = (u - U0) / (U1 - U0)
            fall = max(0.0, 1.0 - max(0.0, (r - 0.22) / 0.45)) ** 1.35
            half_w = 30.0 + 16.0 * min(1.0, r / 0.35)
            ev = max(0.0, 1.0 - max(0.0, (abs(v) - half_w) / 16.0)) ** 1.3
            zt = (BANK_Z + 0.65
                  + 0.45 * math.sin(u * 0.16) * math.cos(v * 0.11)
                  + 0.30 * math.sin(u * 0.28 + 1.7) * math.sin(v * 0.21)
                  + 0.12 * math.sin(u * 0.53 + 0.6) * math.sin(v * 0.37 + 2.1)
                  + 0.10 * math.sin(u * 1.10 + 2.6) * math.cos(v * 0.83 + 0.4)
                  + 0.06 * math.sin(u * 2.30 + 0.9) * math.sin(v * 1.70 + 1.1))
            return -2.4 + (zt + 2.4) * min(fall, ev)
        grid = []
        for i in range(NU + 1):
            row = []
            for j in range(NV + 1):
                u = U0 + (U1 - U0) * i / NU
                v = V0 + (V1 - V0) * j / NV
                row.append(bk.verts.new((x_e + sgn * u, v, bank_h(u, v))))
            grid.append(row)
        for i in range(NU):
            for j in range(NV):
                q = (grid[i][j], grid[i+1][j], grid[i+1][j+1], grid[i][j+1])
                try: bk.faces.new(q if sgn > 0 else (q[0], q[3], q[2], q[1]))
                except ValueError: pass
    bk.normal_update()
    bm_to_obj(bk, "shore_bank", m_earth)
    # (4) 大气透视(实拍: 昆明湖水汽+空气散射, 远端发灰对比度低):
    #     均匀体积散射盒罩住全场景。近地平线向水面掠射的长光程按距离积累雾感。
    #     密度为工作值(0.003实测过浓, 全画面发灰、倒影尽失; 降至0.0018):
    #     近端84.6m散射占比~14%、远端132.4m~21%。
    #     ⚠ 天空硬边的根因不在盒体尺寸: 是相机默认 clip_end=1000m 截断了
    #     >1000m 的体积出射面(Cycles 体积栈为空 => 该段雾效整体消失)。
    #     修复在出图脚本的相机上(clip_end=20000, 见 shot_auto2.py 注, 2026-10-05)。
    FOG_DENSITY = 0.0018
    fg = bmesh.new()
    bmesh.ops.create_cube(fg, size=1.0)
    for v0 in fg.verts:
        v0.co.x *= 5200.0; v0.co.y *= 5200.0
        v0.co.z = v0.co.z * 126.0 + 60.0   # 盒顶加高: 仰角光线渐出, 消除1.3度硬边带
    bm_to_obj(fg, "fog_volume", MAT.fog_material("fog", density=FOG_DENSITY,
                                                color=(0.42, 0.46, 0.53)))
    # 全部桥体与引道构件统一绕 Z 转桥轴方位。
    # 2026-10-04 修: abutment_ground 曾漏在此名单外(旋转 0° vs 本体 -112°),
    # 导致引道块孤悬水中且遮挡正交侧立面。T6 出图时用 hide_render 规避是绕过,
    # 根因在此——它与本体同父级 m_body, 本就该一起转。
    for n in ("bridge_body","impost","voussoir","deck_rail",
              "pier_plinth","deck_cornice","abutment_ground","shore_bank"):
        bpy.data.objects[n].rotation_euler = (0,0,-math.radians(BRIDGE_AXIS_AZ))
    for ob in lion_objs:   # 蹲狮随桥轴同转(叠加在各自柱头微yaw上)
        ob.rotation_euler.z += -math.radians(BRIDGE_AXIS_AZ)
    for ob in beast_objs:  # 靠山兽随桥轴同转
        ob.rotation_euler.z += -math.radians(BRIDGE_AXIS_AZ)
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
    sky.aerosol_density = 0.45; sky.ozone_density = 1.0   # M4: 气溶胶抬高(0.6实测地平线带过硬), 地平线雾感
    sky.ground_albedo = 0.12
    bgw = nt.nodes.new('ShaderNodeBackground')
    bgw.inputs['Strength'].default_value = 0.42
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
