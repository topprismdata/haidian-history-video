"""v2 场景: 整体桥体 + 布尔挖券洞 + 券脸楔石 + 栏杆 + 异兽。"""
import bpy, bmesh, os, sys, math
_c=math.cos; _s=math.sin; _pi=math.pi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bridge_geom2 as G
import materials as MAT
import lions2 as LIONS   # 蹲狮 v2: 母模布尔并 + linked duplicates(旧 lions.py 球堆叠已弃用)
import beasts2 as BEASTS # 靠山兽 v2: 4只 linked duplicates(5000+面/水密/正名靠山兽)
from mathutils import Vector, Matrix

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
        b = G.arch_rise(i)   # M12: 与券洞同起拱线/矢高, 消除环腿悬空横条
        ci = abs(i - (G.N_SPAN - 1) / 2.0)
        N = 15 if ci <= 1.5 else (13 if ci <= 3.5 else 11)
        deck_c = G.deck_z(xc)
        for k in range(N):
            t0 = math.pi * k / N + GAP
            t1 = math.pi * (k + 1) / N - GAP
            rt = RELIEF * (0.94 + 0.12 * (((k * 7 + i * 3) % 5) / 4.0))
            quad = []
            for tt in (t0, t1):
                zz = G.arch_springer_z(i) + b * math.sin(tt)
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
    # 桥面大石板铺装(M10.1 四审指令3): 3 带 × 63 块实体石板, 板间 2.5cm 真缝 +
    # 确定性 ±3.6mm 磨耗高差 —— 缝在几何里, 近景一眼可辨(旧共面条带渲染为纯白片)。
    bands = [(-rail_y, -rail_y / 3.0), (-rail_y / 3.0, rail_y / 3.0), (rail_y / 3.0, rail_y)]
    NSLAB = 63
    for b, (y0, y1) in enumerate(bands):
        off = 0.5 if b == 1 else 0.0          # 中带错缝半块
        for i in range(NSLAB + 1):
            xa = -G.BRIDGE_LEN / 2.0 + G.BRIDGE_LEN * (i + off * 0.5) / NSLAB
            xb = -G.BRIDGE_LEN / 2.0 + G.BRIDGE_LEN * (i + 1 + off * 0.5) / NSLAB
            xa = max(xa, -G.BRIDGE_LEN / 2.0 + 0.02)
            xb = min(xb, G.BRIDGE_LEN / 2.0 - 0.02)
            if xb - xa < 0.10:
                continue
            xa += 0.030; xb -= 0.030
            xm = (xa + xb) / 2.0
            j = (((i * 13 + b * 7) % 5) - 2) * 0.0018
            # 顶面四角各自取桥面曲线高度+磨耗 jitter: 平板顶在纵坡上会翘边 ±2.3cm
            # 遮住砂浆缝带(四审 20 号无缝根因), 随坡顶面偏差<1mm
            zta = G.deck_z(xa) + j
            ztb = G.deck_z(xb) + j
            zb = G.deck_z(xm) - 0.25
            y0g, y1g = y0 + 0.030, y1 - 0.030
            v = [bm.verts.new(p) for p in (
                (xa, y0g, zb), (xb, y0g, zb), (xb, y1g, zb), (xa, y1g, zb),
                (xa, y0g, zta), (xb, y0g, ztb), (xb, y1g, ztb), (xa, y1g, zta))]
            for f in ((0,1,2,3),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)):
                try: bm.faces.new([v[k] for k in f])
                except ValueError: pass

    # ── M13 望柱+栏板 真制式(rail_params_m12.json 实测: 0.27细方柱/实心华板合角框/瓶式瘿项/圆寻杖) ──
    import json as _rj
    RP = _rj.load(open(os.path.join(HERE, "refs/rail_params_m12.json")))
    PW = RP["post_width"] / 2.0            # 望柱半宽 ~0.135
    CAP_H = 0.16                            # 柱头承托石(六审"承托薄化": 0.31→0.16 薄板)
    RAIL_TOP = 0.92                         # 寻杖顶距桥面
    # off_13 官拍整改(2026-10-05): 栏上柱台≈头块 0.31≈狮高。旧 post_height 1.34
    # (栏上段 0.42≈1.3×狮高)偏高; 柱身收到寻杖顶+0.03。
    # 六审整改(2026-10-05 "望柱台身修长、承托薄, 狮如柱头自然生长"): 承托石 0.31 方台
    # 压成 0.16 薄板(宽 1.08→1.04 柱宽, 近乎齐口), 柱身截面 0.27 细方不变;
    # 柱全高 0.95+0.16=1.11, 狮高 0.272 直接蹲在薄板上。
    POST_SHAFT = RAIL_TOP + 0.03           # 柱身(不含头块)
    PANEL_H = RP["panel_height"]            # 华板 0.36
    SILL_H = RP["lower_rail_thickness"]     # 地栿 0.11
    RAIL_T = RP["rail_top_thickness"]       # 寻杖 0.10
    NPOST = 63

    def _boxc(bmm, cx, cy, cz, dx, dy, dz):
        x0,x1,y0,y1,z0,z1 = cx-dx/2,cx+dx/2,cy-dy/2,cy+dy/2,cz-dz/2,cz+dz/2
        vs=[bmm.verts.new(q) for q in ((x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),
            (x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1))]
        for f in ((0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)):
            try: bmm.faces.new([vs[k] for k in f])
            except ValueError: pass

    def _vase(bmm, cx, cy, z0, z1):
        """瓶式瘿项: 喇叭足+鼓腹+束颈+仰莲口, 车削剖面。"""
        h = z1 - z0
        prof = [(0.0,0.055),(0.10,0.05),(0.11,0.16),(0.055,0.24),
                (0.09,0.40),(0.11,0.55),(0.06,0.72),(0.05,0.86),(0.085,1.0)]
        SEG=12
        rings=[]
        for (rf,tf) in prof:
            z=z0+tf*h; r=rf*min(0.24,h*0.42)
            ring=[bmm.verts.new((cx+r*_c(_a), cy+r*_s(_a), z)) for _a in [2*_k*_pi/SEG for _k in range(SEG)]]
            rings.append(ring)
        for a in range(len(rings)-1):
            for k in range(SEG):
                k2=(k+1)%SEG
                try: bmm.faces.new((rings[a][k],rings[a][k2],rings[a+1][k2],rings[a+1][k]))
                except ValueError: pass
        for ring in (rings[0],rings[-1]):
            try: bmm.faces.new(ring)
            except ValueError: pass

    for side in (-1, 1):
        y = side * (rail_y + 0.14)
        for i in range(NPOST + 1):
            x = -G.BRIDGE_LEN / 2.0 + G.BRIDGE_LEN * i / NPOST
            z = G.deck_z(x)
            # 柱身(素平, 转角线脚用材质) + 柱头承托石(六审薄化: 近齐口薄板)
            _boxc(bm, x, y, z + POST_SHAFT/2, PW*2, PW*2, POST_SHAFT)
            _boxc(bm, x, y, z + POST_SHAFT + CAP_H/2, PW*2*1.04, PW*2*1.04, CAP_H)
            LION_SPOTS.append((x, y, z + POST_SHAFT + CAP_H, i, side))
        def slab(x1, z1, x2, z2, h, t, ycen):
            v = [bm.verts.new(p) for p in (
                (x1, ycen-t/2, z1), (x2, ycen-t/2, z2),
                (x2, ycen+t/2, z2), (x1, ycen+t/2, z1),
                (x1, ycen-t/2, z1+h), (x2, ycen-t/2, z2+h),
                (x2, ycen+t/2, z2+h), (x1, ycen+t/2, z1+h))]
            for f in ((0,1,2,3),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)):
                try: bm.faces.new([v[k] for k in f])
                except ValueError: pass
        # 每开间: 地栿 + 实心华板(合角双勾框) + 透空层(2瓶式瘿项) + 圆寻杖
        for i in range(NPOST):
            x1 = -G.BRIDGE_LEN / 2.0 + G.BRIDGE_LEN * i / NPOST
            x2 = -G.BRIDGE_LEN / 2.0 + G.BRIDGE_LEN * (i + 1) / NPOST
            z1, z2 = G.deck_z(x1), G.deck_z(x2)
            xc = (x1 + x2) / 2.0; zc = (z1 + z2) / 2.0
            slab(x1 + 0.12, z1, x2 - 0.12, z2, SILL_H, 0.22, y)                 # 地栿
            slab(x1 + 0.12, z1 + SILL_H, x2 - 0.12, z2 + SILL_H, PANEL_H, 0.16, y)  # 华板(实)
            # 合角双勾凹框: 面板外凸细边框(四边) 内退
            zf = z1 + SILL_H; zb = z2 + SILL_H
            bw = (x2 - x1) - 0.24
            for (ex, ez, ew, eh) in ((xc, zf+0.06, bw, 0.05),(xc, zb+PANEL_H-0.06, bw, 0.05),
                                     (x1+0.18, zf+PANEL_H/2, 0.05, PANEL_H-0.12),
                                     (x2-0.18, zb+PANEL_H/2, 0.05, PANEL_H-0.12)):
                _boxc(bm, ex, y+0.09 if side>0 else y-0.09, ez+ (0 if abs(ez-zf)<0.1 else 0), ew, 0.04, eh)
            # 透空层: 栏板顶(z+SILL+PANEL) -> 寻杖底, 2 瓶式瘿项 于 ±35%
            zopen = zc + SILL_H + PANEL_H
            zrail = zc + RAIL_TOP
            for fx in (0.35, 0.65):
                vx = x1 + (x2 - x1) * fx
                _vase(bm, vx, y, zopen, zrail - RAIL_T)
            slab(x1 + 0.12, z1 + RAIL_TOP - RAIL_T, x2 - 0.12, z2 + RAIL_TOP - RAIL_T, RAIL_T, 0.11, y)  # 寻杖

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.normal_update()
    # ── 砂浆缝带(M10.1d): 深色窄带贴桥面, 掠射角下以色读缝(凸起台阶会自遮挡) ──
    mb = bmesh.new()
    def mortar_strip(x0, x1, y0, y1):
        zm = G.deck_z((x0 + x1) / 2.0) + 0.008
        vv = [mb.verts.new(q) for q in (
            (x0, y0, zm - 0.02), (x1, y0, zm - 0.02), (x1, y1, zm - 0.02), (x0, y1, zm - 0.02),
            (x0, y0, zm), (x1, y0, zm), (x1, y1, zm), (x0, y1, zm))]
        for f in ((0,1,2,3),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)):
            try: mb.faces.new([vv[k] for k in f])
            except ValueError: pass
    XL = G.BRIDGE_LEN / 2.0 - 0.05
    for i in range(NSLAB + 1):                      # 横缝(每板界)
        xb = -G.BRIDGE_LEN / 2.0 + G.BRIDGE_LEN * i / NSLAB
        if -XL < xb < XL:
            mortar_strip(xb - 0.035, xb + 0.035, -rail_y, rail_y)
    for i in range(NSLAB + 1):                      # 中带错缝横缝(半块位)
        xb = -G.BRIDGE_LEN / 2.0 + G.BRIDGE_LEN * (i + 0.5) / NSLAB
        if -XL < xb < XL:
            mortar_strip(xb - 0.035, xb + 0.035, -rail_y / 3.0, rail_y / 3.0)
    for yb in (-rail_y / 3.0, rail_y / 3.0):        # 纵缝(三带界)
        mortar_strip(-XL, XL, yb - 0.035, yb + 0.035)
    bmesh.ops.recalc_face_normals(mb, faces=mb.faces[:])
    mb.normal_update()
    return bm, mb, LION_SPOTS


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
    # [六审B] 砌缝视觉三级层级(要求 券石100%/横缝40-50%/竖缝20-30%, 此前普通
    # 缝~60-70% 抢券石的戏): 几何 2068+ 块全保留, 只调材质权重。
    # [七审P1-3] 层级再降一级 100/40/25 -> 100/28/15; 券石"100"不再靠更黑的缝,
    # 靠楔形节奏+几何出入(筒券/放射缝), joint 0.026->0.020 bump 0.75->0.65。
    m_body = MAT.qingshi_material("stone_body", block_var=0.14)
    m_ring = MAT.qingshi_material("stone_ring", (0.362, 0.392, 0.426),
                                  joint=0.020, block_var=0.26, bump_strength=0.65)
    m_course = MAT.qingshi_material("stone_course", (0.345, 0.376, 0.410),
                                    joint=0.008, block_var=0.06, bump_strength=0.16)
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
        # [M14 修复] 旧式 [center, center+PIER_W] 恒宽假设且右半偏覆盖:
        # void 布尔把伸进洞口的部分裁掉后, 每墩只剩右半水线石, 左半裸墙。
        # PIER_W 变剖面后此假设更错。改为中心 ± pier_w/2 全宽覆盖。
        pc = G.PIER_X[i + 1]
        hw2 = G.pier_w(i + 1) / 2.0
        plinth_segments.append((pc - hw2 + 0.02, pc + hw2 - 0.02))
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
    bm_to_obj(pl, "pier_plinth", m_course)

    # ── 桥沿仰天石(实拍: 桥面边缘一道白色凸出带, 比墙身白) ──
    co = bmesh.new()
    n = 200
    # M10.1e 根因: 旧版仰天石为全宽盖层(deck+5cm), 压住全部石板缝与砂浆带
    # (四审 20 号"桥面纯白片"真因)。改仅两侧 0.43m 边缘带。
    for ye0, ye1 in ((-G.DECK_UP_W / 2.0 - 0.10, -G.DECK_UP_W / 2.0 + 0.33),
                     (G.DECK_UP_W / 2.0 - 0.33, G.DECK_UP_W / 2.0 + 0.10)):
        prev = None
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
    # ── 六审第3刀参数(2026-10-05: 两端桥台/引桥/坡道体量加重) ──
    # GPT 六审定性: "桥两端的桥台、坡道、端部侧墙体量太弱...全桥像17孔拱廊模型"。
    # 四项要求: ①引道加长 22~26m ②燕翅墙加厚外展、底面插入水底 ③端孔外侧 3.5~5.0m
    # 实体石砌墩座 ④岸坡与桥台咬合无穿模无悬空。各值为[工作值](审查方向+实拍校准)。
    # ⚠ 旧"卫星负读数 WING_L≤12 收窄"注记: 表现层六审裁定=加重, 收窄方案搁置;
    #   WING_L 维持 24.0(与新引道长度对齐, 不再加长), 加强走厚度/展角/埋深三路。
    ABUT_EXT = 3.0                     # 墩座前伸: 前端面至桥端 3.0m; 加埋入 0.10 与本体端墙
                                       #   1.35, 末孔外石墙总厚 4.45m ∈ 3.5~5.0
    ABUT_EMBED = 0.10                  # 墩座埋入本体端 0.10m(防露缝; 外轮廓全程高出本体
                                       #   端面剪影 >=2cm, 无共面无 z-fighting)
    ABUT_HALF_B = 7.45                 # 墩座底半宽(本体底半宽 7.3, +0.15 全高度包络)
    ABUT_HALF_T = 3.60                 # 墩座顶半宽(台帽全宽 7.20 > 桥面 6.56)
    RAMP_L = 24.0                      # 引道缓坡长 14.0 -> 24.0(顶面 3.56->2.95m, 2.5% 真实缓坡)
    WING_L = 24.0                      # 翼墙水平投影长(不变, 与 RAMP_L 对齐)
    WING_ANG = math.radians(38.0)      # 展角 35 -> 38 度(六审"向外展")
    WING_T = 1.8                       # 翼墙厚 1.4 -> 1.8(六审"加厚"; 审查示例 0.60->0.85
                                       #   低于现状值, 按方向性要求执行 +29%)
    BED_BOTTOM = -2.8                  # 桥台系底面: 低于岸坡全域最低(-2.4), 实义"稳固插入水底"
    BANK_Z = 2.1                       # 岸坡顶标高(实拍两端岸线高于水面约2m, 不变)
    ROAD_ROOT_DROP = 0.04              # 引道顶面沉台帽下 4cm(帽石收边, 兼消共面 z-fighting)
    # ⚠ 布尔废弃记录(2026-10-05 实测): 旧"abutments"块走 EXACT UNION 并入本体 ——
    #   切割体底面与本体底面共面(-2.2)时可以并入, 底面下沉(-2.8)后 Blender 5.2 EXACT
    #   求解器【静默失败】(双侧无效果; MANIFOLD 亦无效; 单侧成功/失败随浮动参数漂移)。
    #   故墩座改为免布尔实体, 直接并入 abutment_ground(与引道/燕翅墙同材质同物体)。
    #   实心性依据: 端面 x=±75 为实心墙(拱口在 ±y 侧翼, 距端面 1.695m), 墩座无需掏洞。
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
            spz = G.arch_springer_z(idx)          # M12: 逐孔起拱线
            if c.z > spz + 0.05:
                b = G.arch_rise(idx)
                dx, dz = c.x - xc, c.z - spz
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
    # ── 布尔残片清理(2026-10-05 二审修复, M9 移至桥台 UNION 与法线翻转之后: 幻影外壳由 UNION 重构产生): EXACT 布尔在桥体表面留下切刀侧壁残片
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
    print('STRAY_CLEANUP removed verts:', len(rm))
    if rm:
        bmesh.ops.delete(bm, geom=rm, context='VERTS')
    bm.to_mesh(me); bm.free(); me.update()
    print("  翻转券洞内壁破面: %d" % flipped)
    # ── M13 逐块砌筑: 真放射券石环 + 桥墩/拱肩贴面砧石 ──
    import masonry as MAS
    import json as _json
    _hwf = (G.DECK_DOWN_W + G.DECK_UP_W) / 4.0   # 墙面平均半宽
    _vb, _cb, _mstats = MAS.build_masonry(_hwf)
    bm_to_obj(_vb, "voussoir", m_ring)
    bm_to_obj(_cb, "coursing", m_course)
    # pier_plinth 水线石带: 拱改高后起拱线近水面, 石带会伸进洞口成横条 -> void 布尔裁净
    _cut2 = bm_to_obj(G.build_void_bm(), "void_cutter2", m_ring)
    _pp = bpy.data.objects["pier_plinth"]
    _m2 = _pp.modifiers.new("vc", 'BOOLEAN'); _m2.operation='DIFFERENCE'; _m2.solver='EXACT'; _m2.object=_cut2
    bpy.context.view_layer.objects.active = _pp
    bpy.ops.object.modifier_apply(modifier=_m2.name)
    bpy.data.objects.remove(_cut2, do_unlink=True)
    with open(os.path.join(HERE, "masonry_stats.json"), "w") as _f:
        _json.dump(_mstats, _f, ensure_ascii=False, indent=1)
    print("MASONRY voussoir/arch", _mstats["voussoir_per_arch"], "total", _mstats["grand_total"])
    deck_bm, mortar_bm, spots = build_deck_bm()
    # 桥面专署汉白玉: 7cm 凹缝 bump 强刻画(横缝周期=柱距 2.381m), 掠射角读缝
    m_deck = MAT.stone_material("deck_marble", (0.865, 0.840, 0.795), joint=0.07,
                                course_h=2.381, weather=0.40, waterline_h=0.35,
                                block_var=0.15, bump_strength=0.85, base_rough=0.80)
    bm_to_obj(deck_bm, "deck_rail", m_deck)
    m_mortar = MAT.stone_material("deck_mortar", (0.16, 0.15, 0.14), joint=0.0,
                                  course_h=1.0, weather=0.3, waterline_h=0.1,
                                  block_var=0.05, bump_strength=0.2, base_rough=0.95)
    bm_to_obj(mortar_bm, "deck_mortar", m_mortar)
    # 靠山兽: linked duplicates(2026-10-05 最佳实践) —— 4 对象共享 2 个 mesh datablock,
    # 替代旧 build_beast_bm() 盒块堆叠(384 顶点)。单只 5000+ 面, 水密, 剪影清晰。
    beast_spots = []
    _bi = 0
    # 2026-10-05 M9b(三审指令1/22号图): 靠山兽坐栏杆端头抱鼓石位 —— 基面=寻杖顶
    # (deck+0.76), 位于端开间中心, 横向与望柱列齐; 兽背卷云顺接栏板端头(17 号裁切实证构图)。
    for xe in (-G.BRIDGE_LEN / 2 + 1.19, G.BRIDGE_LEN / 2 - 1.19):
        z = G.deck_z(xe) + 0.76
        for k, side in enumerate((-1, 1)):
            y = side * (G.DECK_UP_W / 2 - 0.18 + 0.14)
            facing = 1.0 if xe > 0 else -1.0
            beast_spots.append((xe, y, z, _bi, facing))
            _bi += 1
    beast_objs = BEASTS.place_beasts(beast_spots, name="beasts", size=1.12, material=m_rail)
    # 蹲狮: linked duplicates(2026-10-05 口径) —— 256 对象共享 2 个 mesh datablock,
    # 不再并成单个 "lions" 大 mesh(反模式: 文件膨胀/无法实例化/回归 diff 不归因)。
    lion_objs = LIONS.place_lions(spots, m_rail)
    # ── 引道缓坡 + 八字燕翅墙(六审第3刀改版 2026-10-05) ──
    # 文献: 桥台形式三型——带燕翅(古籍"雁翅")/凹字/一字; 前墙古称金刚墙, 两侧八字形
    # 挡墙称燕翅墙(顺水金刚墙) —— 茅以升基金会《中国古代石拱桥——古桥各部名称》
    # (https://www.mysf.org.cn/Detail/index.html?id=691&aid=291)。
    # 视觉根因: 原楔形块垂直插水, 桥像漂着; 燕翅墙向岸斜展 + 岸坡承接才形成"接岸"读感。
    # 历史: 第4刀(燕翅型)建立; 卫星图版负读数(refs/abutment_design.md, WING_L≤12 收窄)
    # 已被六审裁定搁置——表现层实测渲染两端体量太弱是最大宏观遗漏, 方向=加重。
    # 本刀: 墩座前伸 3.1m(恒截面收分棱柱, 全高度吞没本体端面, 见上方布尔废弃记录) /
    # RAMP_L 14->24m / WING_T 1.4->1.8m / 展角 35->38° / 翼墙根移至墩座段
    # (与石桥台连续) / 底面统一下沉 BED_BOTTOM(-2.8, 低于岸坡最低 -2.4)插入水底。
    ab = bmesh.new()
    for sgn in (-1, 1):
        x_e = sgn * G.BRIDGE_LEN / 2.0
        z_e = G.deck_z(x_e)
        # (0) 实体石砌桥台墩座: x ∈ [75-0.10, 75+3.0], 恒截面收分(底半宽 7.45 ->
        #     顶半宽 3.60), 台帽平接桥面端标高。外轮廓全程高出本体端面剪影 >=2cm
        #     (体侧) / 0.32m(顶缘) -> 本体端墙被完整包络, 无缝无共面; 底沉 BED_BOTTOM
        #     成基脚。末孔券石到前端面之间 4.45m 实体石墙承托(六审#3 3.5~5.0m)。
        xin = x_e + sgn * (G.BRIDGE_ABUT - ABUT_EMBED)     # = 74.90 (埋入本体端)
        xfa = x_e + sgn * ABUT_EXT                         # = 78.00 (前端面)
        vs = [ab.verts.new(p) for p in (
            (xin, -ABUT_HALF_B, BED_BOTTOM), (xfa, -ABUT_HALF_B, BED_BOTTOM),
            (xfa,  ABUT_HALF_B, BED_BOTTOM), (xin,  ABUT_HALF_B, BED_BOTTOM),
            (xin, -ABUT_HALF_T, z_e), (xfa, -ABUT_HALF_T, z_e),
            (xfa,  ABUT_HALF_T, z_e), (xin,  ABUT_HALF_T, z_e))]
        for f in ((0,1,2,3),(4,5,6,7),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)):
            try: ab.faces.new([vs[k] for k in f])
            except ValueError: pass
        # (1) 石砌引道缓坡: 根部嵌进墩座前墙 0.06m, 顶面沉台帽下 ROAD_ROOT_DROP
        #     (帽石收边, 无共面); 以 2.5% 缓降延伸 RAMP_L=24m, 坡端没入岸坡;
        #     底半宽 = 端部 apron 半宽 + 0.06 埋入。
        RT0, RT1 = G.DECK_UP_W / 2.0 + 0.12, 5.2
        B0W = RT1 + 0.06
        x_r = x_e + sgn * (ABUT_EXT - 0.06)
        x_o = x_e + sgn * (ABUT_EXT + RAMP_L)
        zr0 = z_e - ROAD_ROOT_DROP
        zt_tip = BANK_Z + 0.85                 # 坡端没入岸坡顶下
        vs = [ab.verts.new(p) for p in (
            (x_r, -B0W, BED_BOTTOM), (x_r, B0W, BED_BOTTOM),
            (x_o,  RT1, BED_BOTTOM), (x_o, -RT1, BED_BOTTOM),
            (x_r, -RT0, zr0), (x_r, RT0, zr0),
            (x_o,  RT1, zt_tip), (x_o, -RT1, zt_tip))]
        for f in ((0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)):
            try: ab.faces.new([vs[k] for k in f])
            except ValueError: pass
        # (2) 燕翅墙 x2: 根部自墩座前段埋入 0.5m(与石桥台连续, 防露缝)八字斜展,
        #     顶面沿轴向从台帽标高下斜至岸坡顶上方 0.35m, 墙身直落水底基床。
        for side in (-1, 1):
            d = Vector((math.cos(WING_ANG), side * math.sin(WING_ANG)))
            n = Vector((-side * math.sin(WING_ANG), math.cos(WING_ANG)))  # 离轴法向
            z_root, z_tip = z_e, BANK_Z + 0.35   # 翼墙顶=桥面端标高(台帽下缘), 低于桥面
            A = Vector((x_e + sgn * (ABUT_EXT - 0.5), side * (G.DECK_UP_W / 2.0 - 0.1)))
            B = A + d * WING_L
            pts = [(A.x, A.y), (B.x, B.y),
                   (B.x + n.x * WING_T, B.y + n.y * WING_T),
                   (A.x + n.x * WING_T, A.y + n.y * WING_T)]
            def _ztop(px, py):
                f = max(0.0, min(1.0, (Vector((px, py)) - A).dot(d) / WING_L))
                return z_root * (1.0 - f) + z_tip * f
            vs = [ab.verts.new((px, py, BED_BOTTOM)) for px, py in pts] \
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
        z_e = G.deck_z(x_e)
        # 六审#3④ 岸坡咬合(六审第3刀): 在引道与两道燕翅墙的走廊条带内, 岸坡肩线
        # 强制压到石面以下 0.75m(smoothstep 过渡) —— 露出真挡墙高度, 保证:
        #   ① 石引道两侧/燕翅墙身露出 0.75~1.8m 石颊, 是"石砌引桥压在坡地基座上"
        #     而非贴地彩带(首版 0.45/0.28 低视角实测读感单薄, 复验后加深);
        #   ② 走廊内任何 (u,v) 岸坡不高于石面 —— 无穿模;
        #   ③ 石底面 BED_BOTTOM(-2.8) 低于岸坡全域最低(-2.4) —— 无悬空缝隙。
        U_R0, U_R1 = ABUT_EXT - 0.06, ABUT_EXT - 0.06 + RAMP_L   # 坡根/坡端(局部 u)
        Z_TIP = BANK_Z + 0.85
        Z_R0 = z_e - ROAD_ROOT_DROP
        RT0C, RT1C = G.DECK_UP_W / 2.0 + 0.12, 5.2
        def _sm(t):
            t = max(0.0, min(1.0, t))
            return t * t * (3.0 - 2.0 * t)
        def _corr_caps(u, v):
            """走廊限高列表 [(cap_z, weight)]: 岸坡向 cap 作加权 min 下压。"""
            caps = []
            # 引道走廊: 坡端外再压 3m 保证端面咬合
            if -1.0 < u < U_R1 + 3.0:
                uc = min(u, U_R1)
                fr = max(0.0, min(1.0, (uc - U_R0) / RAMP_L))
                z_road = Z_R0 + (Z_TIP - Z_R0) * fr
                half = RT0C + (RT1C - RT0C) * fr
                wu = 1.0 if u <= U_R1 else _sm(1.0 - (u - U_R1) / 3.0)
                wv = _sm((half + 2.5 - abs(v)) / 2.5)
                caps.append((z_road - 0.75, wu * wv))
            # 燕翅墙走廊 x2: 墙顶下 0.75
            for side in (-1, 1):
                ax_ = ABUT_EXT - 0.5
                ay_ = side * (G.DECK_UP_W / 2.0 - 0.1)
                dx_ = math.cos(WING_ANG)
                dy_ = side * math.sin(WING_ANG)
                t = ((u - ax_) * dx_ + (v - ay_) * dy_) / WING_L
                t = max(0.0, min(1.0, t))
                cx_ = ax_ + dx_ * WING_L * t
                cy_ = ay_ + dy_ * WING_L * t
                dist = math.hypot(u - cx_, v - cy_)
                lim = WING_T / 2.0 + 0.9
                if dist < lim:
                    z_w = z_e * (1.0 - t) + (BANK_Z + 0.35) * t
                    caps.append((z_w - 0.75, _sm((lim - dist) / 0.9)))
            return caps
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
            z = -2.4 + (zt + 2.4) * min(fall, ev)
            for z0, w0 in _corr_caps(u, v):
                if w0 > 0.0:
                    z += (min(z, z0) - z) * w0
            return z
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
    for n in ("bridge_body","voussoir","coursing","deck_rail","deck_mortar",
              "pier_plinth","deck_cornice","abutment_ground","shore_bank"):
        bpy.data.objects[n].rotation_euler = (0,0,-math.radians(BRIDGE_AXIS_AZ))
    # 2026-10-05 M9 根因修复: 狮/兽对象此前只转朝向不转位置 -> 全桥狮群悬空错位
    # (二审"浮狮"与三审 21 号对照图集群漂在开间中的真因)。位置与朝向一并绕桥轴旋转。
    Rz = Matrix.Rotation(-math.radians(BRIDGE_AXIS_AZ), 4, 'Z')
    for ob in lion_objs:
        ob.location = Rz @ ob.location
        ob.rotation_euler.z += -math.radians(BRIDGE_AXIS_AZ)
    for ob in beast_objs:
        ob.location = Rz @ ob.location
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
