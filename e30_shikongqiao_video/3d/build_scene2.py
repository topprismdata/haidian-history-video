"""v2 场景: 整体桥体 + 布尔挖券洞 + 券脸楔石 + 栏杆 + 异兽。

P1-T7 三模式(2026-10-06): 默认 = proxy(现行合并网格路径, 行为逐位不变);
`--emit-lib` 出族库 out/families.blend; `--layout` 出 GN 实例装配 out/e30_layout.blend。
纯逻辑段(blender-free)见文件尾 P1-T7 节: pytest 可直接 import 本模块。
"""
import os
import sys
import math
_c=math.cos; _s=math.sin; _pi=math.pi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# blender 依赖一律守护导入: 无 bpy 环境(pytest/纯链复用)下置 None,
# blender 模式逐位不变; 纯逻辑段只用 facts/masonry2/families/ledger/export_print。
# S1(2026-10-07 审查修复): bpy 组与本体组分两个 try —— 旧版一把抓曾把
# "blender 可用但 bridge_geom2 等本体缺文件"吞成 bpy=None 静默降级; 现在
# bpy 可用而任一本体模块缺失即显式 ImportError, blender-free 环境不受影响。
try:
    import bpy, bmesh
    from mathutils import Vector, Matrix
    _HAS_BPY = True
except ImportError:   # pragma: no cover - blender-free 环境
    bpy = bmesh = None
    Vector = Matrix = None
    _HAS_BPY = False
try:
    import bridge_geom2 as G
    import materials as MAT
    import lions2 as LIONS   # 蹲狮 v2: 母模布尔并 + linked duplicates(旧 lions.py 球堆叠已弃用)
    import beasts2 as BEASTS # 靠山兽 v2: 4只 linked duplicates(5000+面/水密/正名靠山兽)
except ImportError:
    G = MAT = LIONS = BEASTS = None
if _HAS_BPY and (G is None or MAT is None or LIONS is None or BEASTS is None):
    raise ImportError(
        "build_scene2: bpy 可用但本体模块导入失败(G/MAT/LIONS/BEASTS 缺失="
        "%r) —— 不再静默降级" % ([n for n, m in (("bridge_geom2", G),
                                                 ("materials", MAT),
                                                 ("lions2", LIONS),
                                                 ("beasts2", BEASTS))
                                 if m is None],))

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


def build_deck_bm(rail_ext=None):
    """桥面大石板铺装 + 望柱(64/侧=128) + 双孔透空官式栏板 + 544只石狮位。

    rail_ext(八轮 P0-1): 引道栏杆延续段 —— dict(xs=柱位x列表(+侧),
    ztop(u)=路面顶, yedge(u)=路面半宽, drum=收头抱鼓石参数)。"""
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
        def slab(x1, z1, y1, x2, z2, y2, h, t):
            v = [bm.verts.new(p) for p in (
                (x1, y1-t/2, z1), (x2, y2-t/2, z2),
                (x2, y2+t/2, z2), (x1, y1+t/2, z1),
                (x1, y1-t/2, z1+h), (x2, y2-t/2, z2+h),
                (x2, y2+t/2, z2+h), (x1, y1+t/2, z1+h))]
            for f in ((0,1,2,3),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)):
                try: bm.faces.new([v[k] for k in f])
                except ValueError: pass
        # 每开间: 地栿 + 实心华板(合角双勾框) + 透空层(2瓶式瘿项) + 圆寻杖
        for i in range(NPOST):
            x1 = -G.BRIDGE_LEN / 2.0 + G.BRIDGE_LEN * i / NPOST
            x2 = -G.BRIDGE_LEN / 2.0 + G.BRIDGE_LEN * (i + 1) / NPOST
            z1, z2 = G.deck_z(x1), G.deck_z(x2)
            xc = (x1 + x2) / 2.0; zc = (z1 + z2) / 2.0
            slab(x1 + 0.12, z1, y, x2 - 0.12, z2, y, SILL_H, 0.22)                 # 地栿
            slab(x1 + 0.12, z1 + SILL_H, y, x2 - 0.12, z2 + SILL_H, y, PANEL_H, 0.16)  # 华板(实)
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
            slab(x1 + 0.12, z1 + RAIL_TOP - RAIL_T, y, x2 - 0.12, z2 + RAIL_TOP - RAIL_T, y, RAIL_T, 0.11)  # 寻杖

    # ── 八轮 P0-1: 栏杆沿引道连续落下(七审③"栏杆不是在最后一个孔突然结束") ──
    # 制式与桥面段相同(地栿/实心华板/合角框/瓶式瘿项/寻杖), 柱距沿坡等分;
    # z 跟路面标高(平台段=台帽), y 距路面边线 0.04(与桥面段同关系); 末端以
    # 地袱+抱鼓石收头(drum)[工作值: 鼓 r0.17 l0.55]。
    if rail_ext:
        xs = rail_ext["xs"]
        ztop = rail_ext["ztop"]
        yedge = rail_ext["yedge"]
        drum = rail_ext["drum"]
        for side in (-1, 1):
            for x0 in xs:                            # 望柱列(平台+坡道), 逐侧镜像
                x = x0 * side
                u = x0 - 75.0
                yc = side * (yedge(u) - 0.04)
                z = ztop(u)
                _boxc(bm, x, yc, z + POST_SHAFT / 2, PW * 2, PW * 2, POST_SHAFT)
                _boxc(bm, x, yc, z + POST_SHAFT + CAP_H / 2, PW * 2 * 1.04, PW * 2 * 1.04, CAP_H)
            chain = [G.BRIDGE_LEN / 2.0] + list(xs)  # 首开间自桥面末柱 x=+75 接续
            for x1, x2 in zip(chain[:-1], chain[1:]):
                m1, m2 = x1 * side, x2 * side
                u1, u2 = x1 - 75.0, x2 - 75.0
                z1, z2 = ztop(u1), ztop(u2)
                y1 = side * (yedge(u1) - 0.04)
                y2 = side * (yedge(u2) - 0.04)
                mx = (m1 + m2) / 2.0
                zc = (z1 + z2) / 2.0
                slab(m1 + 0.12 * side, z1, y1, m2 - 0.12 * side, z2, y2, SILL_H, 0.22)
                slab(m1 + 0.12 * side, z1 + SILL_H, y1, m2 - 0.12 * side, z2 + SILL_H, y2, PANEL_H, 0.16)
                zf = z1 + SILL_H; zb = z2 + SILL_H
                bw = (x2 - x1) - 0.24
                for (ex, ez, ew, eh) in ((mx, zf + 0.06, bw, 0.05),
                                         (mx, zb + PANEL_H - 0.06, bw, 0.05),
                                         (m1 + 0.18 * side, zf + PANEL_H / 2, 0.05, PANEL_H - 0.12),
                                         (m2 - 0.18 * side, zb + PANEL_H / 2, 0.05, PANEL_H - 0.12)):
                    _boxc(bm, ex, y1 + 0.09 if side > 0 else y1 - 0.09, ez, ew, 0.04, eh)
                zopen = zc + SILL_H + PANEL_H
                zrail = zc + RAIL_TOP
                for fx in (0.35, 0.65):
                    vx = m1 + (m2 - m1) * fx
                    _vase(bm, vx, y1 + (y2 - y1) * fx, zopen, zrail - RAIL_T)
                slab(m1 + 0.12 * side, z1 + RAIL_TOP - RAIL_T, y1,
                     m2 - 0.12 * side, z2 + RAIL_TOP - RAIL_T, y2, RAIL_T, 0.11)
            # 末端地袱(末柱->鼓座) + 抱鼓石: 鼓轴横贯栏线, 鼓底嵌地袱 0.04
            ue0 = chain[-1] - 75.0
            ud = drum["u"]
            xd = (75.0 + ud) * side
            yd = side * (yedge(ud) - 0.04)
            z_e0, zd = ztop(ue0), ztop(ud)
            slab(chain[-1] + 0.06, z_e0, yd, xd + side * drum["half"], zd, yd, SILL_H, 0.22)
            SEG = 12
            czd = zd + SILL_H + drum["r"] - 0.04
            rr = []
            for yy in (yd - drum["half"], yd + drum["half"]):
                rr.append([bm.verts.new((xd + drum["r"] * _c(2 * _pi * k / SEG), yy,
                                         czd + drum["r"] * _s(2 * _pi * k / SEG)))
                           for k in range(SEG)])
            for k in range(SEG):
                k2 = (k + 1) % SEG
                try: bm.faces.new((rr[0][k], rr[0][k2], rr[1][k2], rr[1][k]))
                except ValueError: pass
            for ring in rr:
                try: bm.faces.new(ring)
                except ValueError: pass

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.normal_update()
    # ── 砂浆缝带(M10.1d): 深色窄带贴桥面, 掠射角下以色读缝(凸起台阶会自遮挡) ──
    mb = bmesh.new()
    def mortar_strip(x0, x1, y0, y1, zm=None):
        zm = G.deck_z((x0 + x1) / 2.0) + 0.008 if zm is None else zm
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
    if rail_ext:                                    # 坡道横缝(开间界, 随路面展宽)
        for x0 in rail_ext["xs"][1:]:
            u = x0 - 75.0
            e = rail_ext["yedge"](u) - 0.12
            mortar_strip(x0 - 0.035, x0 + 0.035, -e, e, rail_ext["ztop"](u) + 0.008)
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
    # [八审材质刀] 冷灰蓝→青白石暖灰高漫反射: 基色提亮去蓝(0.43 级中性暖灰),
    # 缝侵蚀浅灰化在 materials.py, 暖灰污染在风化 ramp。
    # [M17] 缝权重按真照重定: 砧石间是零缝触边盒, 缝全靠程序线 -> 0.014m+0.72暗化
    # 才在 10m 视距读得出砌层(原 0.008/0.024 太弱, 反被色差噪声淹没)。
    # 券环: 放射缝是真实几何(JOINT_GAP 0.0125), 程序网格缝方向不对 -> joint≈0 关闭。
    m_body = MAT.qingshi_material("stone_body", block_var=0.08)
    m_ring = MAT.qingshi_material("stone_ring", (0.455, 0.450, 0.430),
                                  joint=0.0005, block_var=0.10, bump_strength=0.65)
    # [M18] 砧石间是真实几何缝(GAP_W=0.010, 露本体成暗线) -> 程序缝关(joint 0.0005)。
    # uv_joints 保留无害(缝宽≈0 时线不可见)。
    m_course = MAT.qingshi_material("stone_course", (0.440, 0.436, 0.416),
                                    joint=0.0005, block_var=0.04, bump_strength=0.22,
                                    uv_joints=True)
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
    # ── 八轮 P0-1 桥头-引道体系参数(2026-10-06: 作为独立建筑构件重做; 七审 50-60% 项)
    #    [九轮第二刀 2026-10-06 massing 收口: 台体靠桥端厚/向岸渐退(前脸 5.00->4.55),
    #     坡道侧墙非恒厚直板(实腹顶棱幂曲线外展 + 肩宽 1.27->0.15 递减 + 石颊露出
    #     1.35->0.75 渐退), 顶铺与侧台一起外展(铺装 3.28->5.00 / 实腹 4.55->5.15);
    #     燕翅墙维持删除。完成后桥头冻结。] ──
    # GPT 七审: "真实十七孔桥不是'17个孔+两个端头', 读感是 实体引道→厚重桥台→
    # 小孔渐起→17孔主体→厚重桥台→实体引道"。三个点名缺陷: ①实腹桥台横向未展开
    # (旧恒截面墩座偏薄) ②坡道偏短且端头临空 ③栏杆在桥端突然断掉。
    # 依据: refs/balustrade_count/src/side_elev_6794.jpg 侧视实测(2026-10-06 量化):
    #   末孔后桥头实体墙宽于末孔跨、墙面横缝分层; 坡道两侧石颊(挡墙)连续;
    #   栏杆沿坡道而下、以抱鼓石收头; 坡道端接岸上平地, 无临空端面。
    # 以下尺寸均为[工作值](照片比例读数 + 2.5%级缓坡/埋深不悬空约束折中)。
    ABUT_U0 = -0.8                     # 桥台根埋入本体端墙 0.8m(端墙厚 1.35, 不侵入末孔:
                                       #   末孔券脸内缘 |x|=73.65 < 75-0.8=74.2)
    ABUT_L = 5.2                       # 桥台纵长(根→前脸) 旧 3.0 -> 5.2: 台帽兼兽位平台
    ABUT_HW_ROOT = 6.50                # 台体平面半宽@根: 包络本体端墙(底半宽 7.3: 根底
                                       #   6.50+收分0.85=7.35, +0.05 出露)与水线石带 6.1
    ABUT_HW_FRONT = 4.55               # 台体平面半宽@前脸: 平面楔形收分(九轮"靠桥端厚、
                                       #   向岸渐退", 楔差 1.95m/6m), 前脸即坡道根部,
                                       #   台帽肩部承兽位(照: 兽坐台肩)
    # [M19 冬照重标定 2026-10-06] 桥头-岸系常数随桥面端标高 3.60->2.20 整体下移 1.4m
    # (冬照=常水位基准; 岸/坡/台原按枯湖水位照片拟合, 与桥的相对关系经九轮目视验收,
    #  故整体平移保形, 水线 z=0 与基脚带 WL_Z0/WL_Z1 不动)。坡度 (2.15-1.05)/42=2.62% 不变。
    ABUT_TOP_Z = 2.16                  # 台帽顶 = 桥面端标高 2.20 - 0.04(沉台帽下, 帽石缝)
    BATTER = 0.85                      # 侧墙竖向收分(底相对顶外放量, "斜向挡墙"读感)
    WL_OUT = 0.22                      # 水线基脚层出挑量(照面层次: 下碱出一皮)
    WL_Z0, WL_Z1 = -0.55, 0.0          # 基脚层标高带(跨水线, 带外 0.15m 渐灭)
    RAMP_L = 42.0                      # 坡道水平长 旧 24 -> 42(照片: 坡道≈3~4 倍末孔跨;
                                       #   42m 端部落岸, 坡度 1.10/42=2.62% 仍属缓坡)
    RAMP_EMBED = 0.06                  # 坡根嵌入台帽前脸 0.06(防露缝; 台帽顶 3.56 > 坡根 3.55)
    RAMP_U0 = ABUT_L - RAMP_EMBED      # 坡根 u = 5.14(嵌进台帽前脸)
    RAMP_U1 = RAMP_U0 + RAMP_L         # 坡端 u = 47.14
    RAMP_Z0 = 2.15                     # 坡顶面起点标高(台帽下 1cm, 读作石作分缝) [M19 -1.4]
    Z_TIP = 1.05                       # 坡端顶面标高(岸顶 BANK_Z 0.70 + 0.35) [M19 -1.4]
    RAMP_HW0, RAMP_HW1 = 3.28, 5.00    # 坡道铺装半宽: 根=桥面半宽(边线连续) -> 端外展
                                       #   (九轮"顶部铺装…略向外展开", 展量 +1.72)
    HW_SOLID_END = 5.15                # 坡端侧墙顶棱半宽 = 铺装 5.00 + 肩 0.15
                                       #   (根部肩 = 4.55-3.28 = 1.27: 侧墙厚度向岸渐退)
    PAD_Z = 1.02                       # 接岸地坪标高(坡端顶 1.05 - 0.03 石/土交接缝;
                                       #   坡端端面没入地坪, 消临空) [M19 -1.4]
    PAD_U0, PAD_U1 = 40.0, 84.0        # 接岸地坪纵向范围(u, 两端 smoothstep 过渡 6m/12m)
    PAD_FADE = 10.0                    # [M15 目视修] 6->10: 起坡段过渡加长, 消硬台阶边
    PAD_HW = 6.0                       # 地坪半宽 = 坡端半宽 5.0 + 6.0(岸上平地展开,
                                       #   照片: 坡端外地面横向放宽), 侧缘 2.0m 渐灭
    WING_L = 6.0                       # [M15 目视修x3] 10->6: 直线下斜墙身在凸形岸坡上中段悬空,
    #                                    只留根部八字收头(远端由坡道侧墙承担挡墙读感)
                                       #   坡道实腹侧墙(全程收分)接管, 翼墙只做桥头八字展
    WING_ANG = math.radians(38.0)      # 展角不变(六审方向保留)
    WING_T = 1.8                       # 翼墙厚不变
    WING_ROOT_U, WING_ROOT_Y = 3.0, 5.2  # 翼墙根(u,y): 台体腰部, y<该处台体半宽 5.55(埋入)
    BED_BOTTOM = -2.8                  # 桥台系底面: 低于岸坡全域最低(-2.4), 实义"稳固插入水底"
    BANK_Z = 0.70                      # 岸坡顶标高 [M19 -1.4](旧 2.1 承枯湖基准; 常水位上 0.7m 低岸,
                                       #   冬照桥端近水读感一致)
    REVEAL_HEAD = 1.35                 # 石颊露出高@台体(走廊岸坡挖低量): 头墙高露成
                                       #   "重量区"(九轮), 依据 side_elev_6794 头墙多层横缝高露
                                       #   [M19] 与桥的相对关系不变, 标高随整体 -1.4 自动跟随 road_top
    REVEAL_END = 0.75                  # 石颊露出高@坡端(沿用六审判据下限) ——
                                       #   露出高向岸线性渐退(九轮"向岸渐退")
    BERM_HW = 3.0                      # 培岸带半宽(实腹顶棱外): 九轮实测自然岸坡在
                                       #   u>30 段低于石面 2m+(fall 因子), 石颊向岸越露
                                       #   越高与照片相反 —— 培岸贴墙(只升不降)让岸线
                                       #   始终托住石颊, 石带本身执行 1.35->0.75 渐退
    BERM_U1 = RAMP_U1 + 4.0            # 培岸纵向末端(坡端外 4m 渐灭, 与接岸坪交叠)
    LOW_U, LOW_FADE = 44.0, 8.0        # 侧向低岸纵向范围(头墙+全程坡道)+ 渐灭段:
                                       #   [九轮实测] 自然岸丘(2.75±1.0)在正侧视里
                                       #   吞掉头墙/坡道侧壁(round8 side 渲染同病,
                                       #   照片 side_elev_6794 头墙侧前是低草滩/水面)
    LOW_Z = 0.30                       # 低岸顶标高(只压不抬: sin 凹谷保留自然起伏)
                                       #   [M19 重定] 旧 1.05 承枯湖基准; 新岸顶 0.70 下
                                       #   低草滩shelf取 0.30(常水位上 0.3m, 冬照桥端侧前
                                       #   近水草滩读感; 取 BANK-0.40, 不取 -0.35 防没水)
    LOW_EDGE = 3.0                     # 培岸带外缘到低岸的横向缓冲(九轮收紧 6->3:
                                       #   6m 渐灭带残留自然岸丘 3.0+ 吞侧视墙带)
    RAIL_END_U = RAMP_U1 - 2.0         # 栏杆坡道末端(距坡端 2m 收头抱鼓石)[工作值]
    # 坡道标高/半宽函数(u=|x|-75): 平台段(u<=ABUT_L)取台帽值, 使台-坡边线连续。
    def road_top(u):
        if u <= ABUT_L:
            return ABUT_TOP_Z
        f = max(0.0, min(1.0, (u - RAMP_U0) / RAMP_L))
        return RAMP_Z0 + (Z_TIP - RAMP_Z0) * f
    def road_half(u):
        f = max(0.0, min(1.0, (u - ABUT_L) / RAMP_L))
        return RAMP_HW0 + (RAMP_HW1 - RAMP_HW0) * f
    def abut_plan_hw(u):
        f = max(0.0, min(1.0, (u - ABUT_U0) / ABUT_L))
        return ABUT_HW_ROOT + (ABUT_HW_FRONT - ABUT_HW_ROOT) * f
    def ramp_solid_hw(u):
        # 坡道侧墙顶棱(实腹外廓, 九轮"非恒厚直板"): 台体前脸值起步(与台-坡接缝
        # C0 连续), 幂曲线外展至 HW_SOLID_END —— 顶棱不是直线; 肩宽(顶棱-铺装)
        # 由 1.27 收到 0.15, 侧墙厚度靠桥端厚、向岸渐退。
        t = max(0.0, min(1.0, (u - ABUT_L) / RAMP_L))
        return ABUT_HW_FRONT + (HW_SOLID_END - ABUT_HW_FRONT) * t ** 0.65
    def reveal_at(u):
        # 石颊露出高: 台体 REVEAL_HEAD -> 坡端 REVEAL_END 线性渐退(头墙重、岸端轻)
        t = max(0.0, min(1.0, (u - ABUT_L) / RAMP_L))
        return REVEAL_END + (REVEAL_HEAD - REVEAL_END) * (1.0 - t)
    def solid_hw(u):
        # 实腹顶棱总调度: 台体段=平面楔形, 坡道段=幂曲线外展(九轮)
        return abut_plan_hw(u) if u < ABUT_L else ramp_solid_hw(u)
    def wl_bump(z):
        # 水线基脚层出挑权重: [WL_Z0,WL_Z1] 全出挑, 上下 0.15m 渐灭(照面"下碱出挑一皮")
        if z >= WL_Z1 + 0.15 or z <= WL_Z0 - 0.15:
            return 0.0
        return min(1.0, (WL_Z1 + 0.15 - z) / 0.15, (z - (WL_Z0 - 0.15)) / 0.15)
    def side_hw(hw_plan, z, ztop):
        # 台体/坡体侧墙半宽: 平面收分 + 竖向收分(BATTER, 顶=hw_plan) + 基脚出挑
        return hw_plan + BATTER * (ztop - z) / (ztop - BED_BOTTOM) + WL_OUT * wl_bump(z)
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
    # 引道栏杆延续段柱位(八轮 P0-1): 台帽平台 2 开间(2.6+2.6) + 坡道沿坡等分
    # (~2.35m × 17 开间, 与桥面柱距 2.381 同级), 末端收头抱鼓石。
    _rail_xs = [75.0 + 2.6, 75.0 + ABUT_L]
    _nb = max(1, int(round((RAIL_END_U - ABUT_L) / 2.381)))
    _rail_xs += [75.0 + ABUT_L + (RAIL_END_U - ABUT_L) * k / _nb for k in range(1, _nb + 1)]
    deck_bm, mortar_bm, spots = build_deck_bm(rail_ext=dict(
        xs=_rail_xs, ztop=road_top, yedge=road_half,
        drum=dict(u=RAIL_END_U + 0.19, r=0.17, half=0.275)))
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
    # ── 桥头-引道体系(八轮 P0-1 重做 2026-10-06; 九轮第二刀 massing 收口) ──
    # 文献: 桥台前墙古称金刚墙, 两侧八字形挡墙称燕翅墙 —— 茅以升基金会《中国古代
    # 石拱桥——古桥各部名称》。GPT 八审九轮刀单: "台体靠桥端厚向岸渐退 / 坡道侧墙
    # 非恒厚 / 顶铺与侧台外展", 目标读感"拱桥结束→厚桥台承托→实腹坡体铺向岸上":
    #   ① 实腹桥台: 平面楔形(根 6.50 -> 前脸 4.55 半宽, 楔差 1.95m/6m, 九轮
    #      "靠桥端厚、向岸渐退"), 自基床 -2.8 通高到台帽 3.56 的实体, 侧墙竖向
    #      收分 + 水线基脚出挑一皮(照面层次), 台帽即兽位平台(照片: 靠山兽坐台肩);
    #      末孔券脸(73.65)到前脸(80.20) 6.55m 实腹。
    #   ② 实腹坡道 42m: 顶面 3.55 -> 2.45(2.62% 缓坡), 铺装边线 3.28->5.00 外展,
    #      侧墙顶棱 4.55->5.15 幂曲线外展(肩宽 1.27->0.15 递减 = 墙厚向岸渐退,
    #      非恒厚直板), 石颊露出高 1.35->0.75 渐退(头墙重、岸端轻); 坡端没入
    #      接岸地坪(PAD_Z=2.42), 消临空端面(七审②"真正接上岸")。
    #   ③ 燕翅墙维持删除([M15 目视修x4] 裁定: 直线下斜墙身是纯负资产), "连续
    #      斜向挡墙"由坡道侧墙承担, 八字收头感由台体楔形平面提供(九轮: 不复活)。
    # ⚠ 布尔废弃记录(2026-10-05 实测, 仍有效): 与本体的拼接一律走"埋入实体"免布尔
    #   (根埋端墙 0.8 / 坡根埋台帽 0.06), Blender 5.2 EXACT 求解器对下沉底面会静默失败。
    ab = bmesh.new()

    def _loft(x_e, sgn, us, hw_at, ztop_at):
        """沿 u 放样对称实体: hw_at(u,z)->半宽剖面, ztop_at(u)->顶标高, 底 BED_BOTTOM。
        环 = +y 侧(顶→底) + -y 侧(底→顶), 闭合边即顶面棱; 端部 n-gon 封口成流形。"""
        rings = []
        for u in us:
            zt = ztop_at(u)
            # 顶档必含; 水线带各档仅在低于顶面时参与(修复: 曾把顶档自己也滤掉,
            # 台体/坡体整体被削顶到 0.15 —— C1/C2 实测顶标高假值暴露)
            zs = [zt] + [z for z in (WL_Z1 + 0.15, WL_Z1, WL_Z0, WL_Z0 - 0.15, BED_BOTTOM)
                         if z < zt - 0.05]
            ring = [ab.verts.new((x_e + sgn * u, s * hw_at(u, z), z))
                    for s in (1.0, -1.0)
                    for z in (zs if s > 0 else list(reversed(zs)))]
            rings.append(ring)
        for ra, rb in zip(rings[:-1], rings[1:]):
            for k in range(len(ra)):
                k2 = (k + 1) % len(ra)
                try: ab.faces.new((ra[k], ra[k2], rb[k2], rb[k]))
                except ValueError: pass
        for r in (rings[0], rings[-1]):
            try: ab.faces.new(r)
            except ValueError: pass

    def _ztop_ramp(u):
        f = max(0.0, min(1.0, (u - RAMP_U0) / RAMP_L))
        return RAMP_Z0 + (Z_TIP - RAMP_Z0) * f

    def _hw_ramp(u, z):
        # 实腹半宽: 台体段(含坡根 0.06 埋接)取台体平面值(接缝 C0 连续),
        # 坡道段取侧墙顶棱 ramp_solid_hw
        return side_hw(solid_hw(u), z, _ztop_ramp(u))

    for sgn in (-1, 1):
        x_e = sgn * G.BRIDGE_LEN / 2.0
        # (0) 实腹桥台: u ∈ [-0.8, 5.2], 台帽顶 3.56, 根埋本体端墙(端墙 73.65~75)
        _loft(x_e, sgn,
              [ABUT_U0 + (ABUT_L - ABUT_U0) * i / 5.0 for i in range(6)],
              lambda u, z: side_hw(abut_plan_hw(u), z, ABUT_TOP_Z),
              lambda u: ABUT_TOP_Z)
        # (1) 实腹坡道: u ∈ [5.14, 47.14], 顶面沿坡, 根嵌台帽前脸 0.06
        _loft(x_e, sgn, [RAMP_U0 + RAMP_L * i / 14.0 for i in range(15)],
              _hw_ramp, _ztop_ramp)
        # (2) [M15 目视修x4] 燕翅墙删除: 三轮尝试(尖端+0.35悬空/埋0.55仍悬空/
        #     缩6m)均败——直线下斜墙身与走廊限高自我下压的岸坡无法自洽, 是纯负
        #     资产。七审"连续斜向挡墙"由坡道侧墙(顶棱随 ramp_solid_hw 外展)承担,
        #     八字收头感由台体楔形平面(根半宽6.50->前脸4.55)提供。
    bmesh.ops.recalc_face_normals(ab, faces=ab.faces[:]); ab.normal_update()
    # 桥台/坡道专署砌石材质(七审"石面露出带层次"): 横缝分层 course_h=0.62(照片下碱
    # 横缝节奏, 缝宽/凹深加强让远景读得出层) + 水线以下加深, 与桥身 qingshi 区分。
    # [工作值](对照 side_elev_6794: 头墙横缝强、块面齐、整体偏亮)
    m_abut = MAT.stone_material("abut_stone", (0.75, 0.73, 0.69), joint=0.06,
                                course_h=0.62, weather=0.42, waterline_h=0.45,
                                block_var=0.12, bump_strength=0.85, base_rough=0.85)
    bm_to_obj(ab, "abutment_ground", m_abut)
    # 坡道仰天石(八轮 P0-1): 白色边缘带沿坡道连续(照片: 坡缘亮带), 随 road_half 展宽;
    # 根端(5.14)埋进台帽前脸内, 与桥面仰天石在台帽两侧隔头相接。
    rc = bmesh.new()
    for sgn in (-1, 1):
        x_e = sgn * G.BRIDGE_LEN / 2.0
        for ye_s in (-1, 1):
            prev = None
            for k in range(41):
                u = RAMP_U0 + (RAMP_U1 - RAMP_U0) * k / 40.0
                x = x_e + sgn * u
                zt = _ztop_ramp(u)
                rh = road_half(u)        # 仰天石跟铺装边线(九轮: 顶棱-铺装间留肩,
                                         #  肩面即侧墙厚度, 由 m_abut 材质读出)
                ye0 = ye_s * (rh - 0.33)
                ye1 = ye_s * (rh + 0.10)
                cur = [rc.verts.new((x, ye0, zt - 0.10)), rc.verts.new((x, ye1, zt - 0.10)),
                       rc.verts.new((x, ye1, zt + 0.05)), rc.verts.new((x, ye0, zt + 0.05))]
                if prev:
                    for a2, b2 in ((0,1),(1,2),(2,3),(3,0)):
                        try: rc.faces.new((prev[a2], prev[b2], cur[b2], cur[a2]))
                        except ValueError: pass
                prev = cur
    rc.normal_update()
    bm_to_obj(rc, "ramp_cornice", m_rail)
    # (3) 岸坡地形: 两端各一片低矮岸坡(顶2.1-3.4m, 实拍岸线高于水面约2m),
    #     内缘塞入桥端/引道之下防裂缝, 外缘与沿岸两端以陡坡没入水下(-2.4m)自然生成水线。
    #     顶面起伏为确定性正弦叠加(非随机位移; 环境构件虽允许随机, 保持可复现)。
    bk = bmesh.new()
    for sgn in (-1, 1):
        x_e = sgn * G.BRIDGE_LEN / 2.0
        z_e = G.deck_z(x_e)
        # 六审#3④ 岸坡咬合(沿用) + 八轮 P0-1 接岸地坪(七审②"真正接上岸"):
        #   ① 台体/坡道走廊内岸坡压到石面下 0.75m —— 露出连续石颊(挡墙读感);
        #   ② 坡端外侧铺接岸地坪(PAD_Z=2.42, 低于坡端顶 0.03 作石/土交接缝):
        #     坡道端面没入地坪, 地坪向外 12m 渐灭接回自然岸形 —— 无临空端头;
        #   ③ 石底面 BED_BOTTOM(-2.8) 低于岸坡全域最低(-2.4) —— 无悬空缝隙。
        def _sm(t):
            t = max(0.0, min(1.0, t))
            return t * t * (3.0 - 2.0 * t)
        def _pad_w(u, v):
            """接岸地坪权重: 纵向 [PAD_U0,PAD_U1] 两端 smoothstep(尾段 12m),
            横向半宽 = 坡端半宽+PAD_HW, 侧缘 1.2m 渐灭。"""
            if u < PAD_U0 or u > PAD_U1:
                return 0.0
            hp = RAMP_HW1 + PAD_HW
            if abs(v) > hp:
                return 0.0
            if u < PAD_U0 + PAD_FADE:
                wu = _sm((u - PAD_U0) / PAD_FADE)
            elif u > PAD_U1 - 1.5 * PAD_FADE:
                wu = _sm((PAD_U1 - u) / (1.5 * PAD_FADE))
            else:
                wu = 1.0
            return wu * _sm((hp - abs(v)) / 4.0)   # 侧缘 2->4m 渐灭
        def _berm_w(u, v):
            """培岸贴墙权重(九轮): 坡道段 [ABUT_L-0.5, BERM_U1](台体段不培:
            头墙脚直接落草滩, 由 cap/low 压岸), 横向到实腹顶棱+BERM_HW,
            外缘渐灭; 坡端外 4m 纵向渐灭(与接岸坪交叠)。"""
            if u < ABUT_L - 0.5 or u > BERM_U1:
                return 0.0
            wu = _sm((u - (ABUT_L - 0.5)) / 1.0) if u < ABUT_L + 0.5 else 1.0
            if u > RAMP_U1:
                wu = _sm((BERM_U1 - u) / 4.0)
            return wu * _sm((solid_hw(u) + BERM_HW - abs(v)) / BERM_HW)
        def _low_w(u, v):
            """桥头侧向低岸权重(九轮): u∈[ABUT_U0, LOW_U+LOW_FADE] 且培岸带外
            (|v| > 实腹顶棱+BERM_HW+LOW_EDGE 渐入), 把自然岸顶压向 LOW_Z。
            只压不抬(自然凹谷保留); 培岸带内交给 berm/cap, 接岸坪后压(pad 接管)。"""
            if u < ABUT_U0 or u > LOW_U + LOW_FADE:
                return 0.0
            edge = solid_hw(u) + BERM_HW
            if abs(v) <= edge:
                return 0.0
            wu = 1.0 if u <= LOW_U else _sm((LOW_U + LOW_FADE - u) / LOW_FADE)
            return wu * _sm((abs(v) - edge) / LOW_EDGE)
        def _corr_caps(u, v):
            """走廊限高列表 [(cap_z, weight)]: 岸坡向 cap 作加权 min 下压。"""
            caps = []
            # 台体/坡道走廊: 岸坡压到石面下 reveal_at(u)(头 1.35 -> 端 0.75 渐退,
            # 九轮"重量区"), 走廊半宽=实腹顶棱; u>40 渐灭(接岸地坪接管)
            if -2.0 < u < 44.0:
                half = solid_hw(u)
                wu = 1.0 if u <= 40.0 else _sm((44.0 - u) / 4.0)
                # 台座平顶到培岸带外缘(九轮: 消"cap 渐灭带"露自然岸丘的缺口),
                # 外缘再 2.5m 渐灭交给低岸; 台体段直接压到草滩 1.30(照片: 头墙
                # 侧前是低草, 露出 2.26m 全高 —— 抬升台座会在侧视里成暗色平台)
                cap_z = road_top(u) - reveal_at(u) if u >= ABUT_L else 1.30
                wv = _sm((half + BERM_HW + 2.5 - abs(v)) / 2.5)
                caps.append((cap_z, wu * wv))
            # [M15x4] 燕翅墙走廊随翼墙删除

            return caps
        # 2026-10-05 修"岸坡生硬立方体"(主控量化: 岸缘水平梯度 max 81.7):
        #   ① 网格 24x40 -> 72x120: 4m 级刻面让岸线读成折线硬边;
        #     [八轮 P0-1 再加密 72x120 -> 108x168: 接岸地坪渐灭带在 1.4m 网格上
        #      出现折线亮缝(实测 axial 视图), 0.93m 级网格摊平法线突变]
        #   ② 横向宽度随 u 收窄(近桥端 ±30m 塞进翼墙足迹下防露切面, 向外展到 ±46m 再收)
        #     —— 首版 ±20m 起步把翼墙/引道端部的垂直切面露了出来(实测复现后回调);
        #   ③ 加两档高频正弦(确定性, 无随机)让岸线弯曲自然。
        NU, NV = 108, 168
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
            wl_ = _low_w(u, v)                   # 九轮: 桥头侧向低岸(只压不抬,
            if wl_ > 0.0 and z > LOW_Z:          #   露出侧墙全高, 正侧视可读)
                z += (LOW_Z - z) * wl_
            wp = _pad_w(u, v)                    # 八轮 P0-1: 接岸地坪(只升不降)
            if wp > 0.0:
                z += (PAD_Z - z) * wp
            wr = _berm_w(u, v)                   # 九轮: 培岸贴墙(只升不降, 实腹坡体
            if wr > 0.0:                         #   护坡, 让石颊露出高按 reveal_at 渐退)
                zb = road_top(u) - reveal_at(u)
                if zb > z:
                    z += (zb - z) * wr
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
              "pier_plinth","deck_cornice","ramp_cornice","abutment_ground","shore_bank"):
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




# ═══════════════════════════════════════════════════════════════════════
# P1-T7 纯逻辑段(blender-free)
# 全桥砌体账目链(masonry2 三层 × 17 孔 × 东西) + 券洞 void 裁剪 + 族清点 +
# GN 实例放置数学。只依赖 facts/assumptions/masonry2/families/ledger/
# export_print —— pytest 无 bpy 直测; 上面的三模式复用同一实现(单一真相)。
# 桥面/墩位从 facts 常量独立推导(与 bridge_geom2 同式; P1 惯例 hw_fn 注入,
# 先例 tests/test_p1_masonry2.py hw_p8), blender 模式跑 _check_geom_parity
# 断言两套推导零漂移。
# ═══════════════════════════════════════════════════════════════════════
import json as _json
import hashlib as _hashlib
import facts as _F
import assumptions as _ASSUM
from assumptions import BODY_BOTTOM as _BODY_BOTTOM
import masonry2 as _M2
import families as _FAM
import ledger as _LED
import export_print as _EP

COL_FAMILIES = "COL_FAMILIES"
LAYOUT_MAX_OBJECTS = 50          # --layout 场景 Object 硬门(主场景不持有 5000 Object; W1 对齐简报, 实测 20)
ARC_STEP = 0.04                  # void 弧段折线采样步长(m); 折线内接矢高 ~1e-4m 亚像素
ARC_N_SEG = 40                   # 单心圆弧角度离散段数(每半弧); 与 assumptions.NSEG_ARC 同义沿用
CLIP_EPS = 1e-9
VOID_Z_MIN = _BODY_BOTTOM - 2.0  # void 矩形部下界(低于一切砌体; 只为 SH 裁剪有限化)


def piers_and_spans():
    # type: () -> Tuple[List[float], List[float]]
    """墩位中心/孔跨(facts 累加式, 与 bridge_geom2.PIER_X 同式)。"""
    spans = list(_F.SPAN_DISTINCT) + list(reversed(list(_F.SPAN_DISTINCT)[:-1]))
    px = []
    acc = -_F.BRIDGE_LEN / 2.0
    for i in range(_F.N_SPAN + 1):
        w = _F.BRIDGE_ABUT if i in (0, _F.N_SPAN) else _F.PIER_W_INT[i - 1]
        px.append(acc + w / 2.0)
        acc += w
        if i < _F.N_SPAN:
            acc += spans[i]
    return px, spans


def deck_z_at(x):
    # type: (float) -> float
    """桥面抛物线(facts 常量版; bridge_geom2.deck_z 同式)。"""
    half = _F.BRIDGE_LEN / 2.0
    ax = min(abs(x), half)
    k = (_F.DECK_Z_TOP - _F.DECK_Z_END) / (half * half)
    return _F.DECK_Z_TOP - k * ax * ax


def hw_wall(x, z):
    # type: (float, float) -> float
    """墙面半宽收分参考(全宽线性内插, 半宽): 生成器 hw_fn 注入口。"""
    zt = deck_z_at(x)
    f = (z - _BODY_BOTTOM) / (zt - _BODY_BOTTOM)
    f = max(0.0, min(1.0, f))
    return (_F.DECK_DOWN_W + (_F.DECK_UP_W - _F.DECK_DOWN_W) * f) / 2.0


def arch_band(i):
    # type: (int) -> Dict[str, float]
    """第 i 孔(0 基)的 void 判定带: 拱心 x/半跨/矢高/起拱线/带界/顶界/弧外扩半宽。
    xe = facts.arch_x_extent(b>a 的 horseshoe 微外鼓, 单心圆唯一解几何必然)。"""
    px, spans = piers_and_spans()
    xc = (px[i] + px[i + 1]) / 2.0
    a = spans[i] / 2.0
    b = _F.rise_ratio(i) * spans[i]
    springer = deck_z_at(xc) - _F.spandrel(i) - b
    return {"xc": xc, "a": a, "b": b, "springer": springer,
            "xe": _F.arch_x_extent(a, b),
            "x_lo": px[i], "x_hi": px[i + 1], "z_hi": deck_z_at(xc)}


def point_in_void(x, z, band):
    # type: (float, float, Dict[str, float]) -> bool
    """点是否落在第 i 孔券洞净空内(矩形部 |x-xc|<a + 单心圆弧 intrados 内侧;
    圆内测试走 facts.arch_signed_r 单一来源, 与 build_void_bm 同式)。起拱线以上
    的 x 夹持用 xe(b>a 时弧微外鼓出 ±a, 由同一单源给出)。"""
    if z > band["springer"]:
        if z > band["springer"] + band["b"] + CLIP_EPS:
            return False
        xe = band.get("xe", band["a"])
        if abs(x - band["xc"]) > xe:
            return False
        return _F.arch_signed_r(x, z, band["xc"], band["springer"],
                                band["a"], band["b"]) < 0.0
    return abs(x - band["xc"]) < band["a"]


def _poly_area(poly):
    # type: (List[Tuple[float, float]]) -> float
    return 0.5 * sum(poly[j][0] * poly[(j + 1) % len(poly)][1]
                     - poly[(j + 1) % len(poly)][0] * poly[j][1]
                     for j in range(len(poly)))


def _cross3(o, a, b):
    # type: (Tuple[float, float], Tuple[float, float], Tuple[float, float]) -> float
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _sh_clip(subject, clip):
    # type: (List[Tuple[float, float]], List[Tuple[float, float]]) -> List[Tuple[float, float]]
    """Sutherland-Hodgman: subject ∩ 凸 clip。clip 方向自洽(负面积先反转)。"""
    if _poly_area(clip) < 0.0:
        clip = list(reversed(clip))
    out = list(subject)
    src = clip
    for i in range(len(src)):
        a = src[i]
        b = src[(i + 1) % len(src)]
        inp = out
        out = []
        if not inp:
            break
        s = inp[-1]
        sin = _cross3(a, b, s) >= -CLIP_EPS
        for e in inp:
            ein = _cross3(a, b, e) >= -CLIP_EPS
            if ein != sin:
                dc = (s[0] - e[0], s[1] - e[1])
                dab = (b[0] - a[0], b[1] - a[1])
                denom = dc[0] * dab[1] - dc[1] * dab[0]
                if abs(denom) > 1e-15:
                    t = ((a[0] - e[0]) * dab[1] - (a[1] - e[1]) * dab[0]) / denom
                    out.append((e[0] + t * dc[0], e[1] + t * dc[1]))
            if ein:
                out.append(e)
            s = e
            sin = ein
    return out


_ARC_POLY_CACHE = {}     # type: Dict[Tuple[int, int], List[Tuple[float, float]]]


def _void_piece_polys(band, key):
    # type: (Dict[str, float], int) -> List[List[Tuple[float, float]]]
    """void 净空凸分解: [拱下矩形部, 左弧段, 右弧段](有限多边形; 方向自洽)。
    [拱线族返工 2026-10-08] 弧段走 facts 单心圆弧: 每段 = 起拱弦半边 + 半弧
    (facts.arch_arc_pts 角度离散, 与 build_void_bm 切割折线同一顶点集);
    b>a 孔(8/9/10) horseshoe 外鼓段(≤2.7cm)随半弧自然含入, 弧段仍是凸多边形
    (圆盘∩z≥起拱线∩半平面的交)。key 由调用方按 arch 序号缓存。"""
    xc, a, spz = band["xc"], band["a"], band["springer"]
    b = band["b"]
    box = [(xc - a, VOID_Z_MIN), (xc + a, VOID_Z_MIN),
           (xc + a, spz), (xc - a, spz)]
    # 弧顶点集 = build_void_bm 切割折线同一离散(facts.arch_arc_pts 单源,
    # b>a 孔含起拱点->赤道单弦约定); 以冠点(最高点)分左右两个凸片。
    arc = _F.arch_arc_pts(xc, spz, a, b, ARC_N_SEG)
    ci = max(range(len(arc)), key=lambda k: arc[k][1])
    right = arc[:ci + 1]                      # 右起拱点 -> 冠
    halves = []
    for sign in (-1, 1):
        if sign > 0:
            half = right
        else:
            half = [((2.0 * xc - px), pz) for px, pz in right]
        # 环向: 底弦 -> 弧(起拱->冠, 首尾顶点由底弦/冠点显式给出) -> 中线闭合。
        # 右片 CCW; 左片为镜像(CW) —— _sh_clip 对 clip 负面积自动反转, 方向自洽。
        poly = [(xc, spz), (xc + sign * a, spz)] + half[1:-1] + [(xc, spz + b)]
        halves.append(poly)
    if key not in _ARC_POLY_CACHE:
        _ARC_POLY_CACHE[key] = [box] + halves
    return _ARC_POLY_CACHE[key]


def _dedupe_ring(poly, eps=1e-9):
    # type: (List[Tuple[float, float]], float) -> List[Tuple[float, float]]
    """去掉相邻重复点(SH 在裁剪边恰过矩形角点时会双发同一交点 -> 棱柱
    出重边不水密), 含首尾闭合点。"""
    out = []
    for p in poly:
        if not out or abs(p[0] - out[-1][0]) > eps or abs(p[1] - out[-1][1]) > eps:
            out.append(p)
    while len(out) >= 2 and abs(out[0][0] - out[-1][0]) <= eps \
            and abs(out[0][1] - out[-1][1]) <= eps:
        out.pop()
    return out


def _kept_pieces(x0, x1, z0, z1, band):
    # type: (float, float, float, float, Dict[str, float]) -> List[List[Tuple[float, float]]]
    """石块足印减去券洞净空后的【保留片】(墙侧, 世界 x-z, 逐片凸多边形)。
    x 按 [xc-a, xc, xc+a] 断成竖条: 洞外竖条整条保留; 洞内竖条按 ARC_STEP
    细分, 每子条保留拱腹线以上部分(梯形; 冠尖单独断点保证子条底边单调 ->
    凸)。拱线折线近似矢高 ~1e-4m 亚像素。"""
    xc, a, spz, b = band["xc"], band["a"], band["springer"], band["b"]
    vx0, vx1 = xc - a, xc + a
    kept = []      # type: List[List[Tuple[float, float]]]
    cuts = [x0, x1] + [v for v in (vx0, xc, vx1) if x0 < v < x1]
    cuts = sorted(set(cuts))
    # 拱腹弦线表 = 券洞挖除体折线的【同一顶点集】(facts.arch_half_arc 角度离散,
    # [拱线族返工 2026-10-08] 起 proxy 布尔切割与 layout 离散净空逐顶点一致,
    # 不引入第二种离散化)。b>a 孔的 horseshoe 外鼓点(|x-xc|>a)不入跨内弦表
    # —— 该域由 _void_piece_polys 弧段凸片经 SH 裁剪分类处理, 跨内弦线单调。
    arc = _F.arch_half_arc(xc, spz, a, b, 1, _ASSUM.NSEG_ARC)
    us = sorted({round(abs(px - xc), 9) for px, _ in arc if abs(px - xc) <= a + 1e-9})
    sta = [xc - u for u in reversed(us)] + [xc + u for u in us[1:]]   # 升序, 冠点不重复
    zv = {round(x, 9): _F.arch_z(x, xc, spz, a, b) for x in sta}

    def _chord(x):
        # cutter 折线在 x 处的高度(所在 station 区间线性内插)
        if x <= sta[0]:
            return zv[round(sta[0], 9)]
        if x >= sta[-1]:
            return zv[round(sta[-1], 9)]
        for s0, s1 in zip(sta[:-1], sta[1:]):
            if s0 <= x <= s1:
                t = (x - s0) / (s1 - s0)
                return zv[round(s0, 9)] + t * (zv[round(s1, 9)]
                                               - zv[round(s0, 9)])
        return zv[round(sta[-1], 9)]
    for sa, sb in zip(cuts[:-1], cuts[1:]):
        if sb <= vx0 + CLIP_EPS or sa >= vx1 - CLIP_EPS:
            # 洞外/墩内竖条整条保留。b>a 孔的 horseshoe 外鼓带(sa∈(vx1, vx1+2.7cm])
            # 亦走此支: 保留片最厚 2.7cm 渲染亚像素, 如实挂账(见 body_changelog)。
            kept.append([(sa, z0), (sb, z0), (sb, z1), (sa, z1)])
            continue
        inner = [x for x in sta if sa < x < sb]
        raw = ([(sa, _chord(sa))] + [(x, zv[round(x, 9)]) for x in inner]
               + [(sb, _chord(sb))])
        if not (min(z for _, z in raw) <= z1 and max(z for _, z in raw) >= z0):
            continue   # 整条弦线在 z 带外(全保留或全切除)
        pts = []
        started = False
        exited = False
        for k, (xx, zr) in enumerate(raw):
            if z0 <= zr <= z1:
                if not started:
                    if k > 0:
                        zt = z1 if raw[k - 1][1] > z1 else z0
                        t = (zt - raw[k - 1][1]) / (zr - raw[k - 1][1])
                        pts.append((raw[k - 1][0] + t * (xx - raw[k - 1][0]), zt))
                    started = True
                pts.append((xx, zr))
            elif started:
                zt = z1 if zr > z1 else z0
                t = (zt - raw[k - 1][1]) / (zr - raw[k - 1][1])
                pts.append((raw[k - 1][0] + t * (xx - raw[k - 1][0]), zt))
                exited = True
                break
        if not started or len(pts) < 2:
            continue
        if not exited:
            pts = pts + [(sb, z1), (sa, z1)]
        elif pts[-1][1] == z0:
            # 出界到块底以下: 底边沿 z0 延到 sb, 右边上行, 顶边回, 左边闭合
            pts = pts + [(sb, z0), (sb, z1), (sa, z1)]
        elif pts[-1][1] == z1:
            # [P2-T6b] 上穿出界(弦线带内上行后越过块顶): 带内段沿弦, 顶边
            # 沿 z1 折返首点 x 闭合。旧实现无此支 —— 2 点开环被 len>=3 丢弃
            # → 整条保留片蒸发, 石被误判 in_void(跨缘石 ARCH07.C04.B00 四石
            # 即此); station 网格按孔绝对 x 对齐, 镜像孔离散错位使该支只在
            # 单侧触发 = 手性伪影(in_void 180 vs 176)。
            pts = pts + [(pts[0][0], z1)]
        # 出界到 z1: pts 已止于 (x*, z1), 顶边沿 z1 回 sa 即闭合
        if len(pts) >= 3 and abs(_poly_area(pts)) > 1e-12:
            kept.append(pts)
    return kept


def clip_footprint(x0, x1, z0, z1, band, band_key=0):
    # type: (float, float, float, float, Dict[str, float], int) -> Tuple[str, List[List[Tuple[float, float]]]]
    """石块世界 x-z 足印对券洞净空分类:
    ("out", [])     全在净空外 -> 参数化族实例;
    ("inside", [])  全在净空内 -> 保留账目点, GN 按 in_void 剔除实例;
    ("clip", polys) 跨净空边界 -> 烘焙 unique 裁剪网格(polys = 净空以外的
                    【保留片】, 世界 x-z 凸多边形; 洞内部分被切除)。
    """
    if (x1 <= band["xc"] - band["a"] - CLIP_EPS
            or x0 >= band["xc"] + band["a"] + CLIP_EPS
            or z0 >= band["springer"] + band["b"] + CLIP_EPS
            or z1 <= VOID_Z_MIN):
        return "out", []
    rect = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
    void_area = 0.0
    for piece in _void_piece_polys(band, band_key):
        got = _dedupe_ring(_sh_clip(rect, piece))
        if len(got) >= 3:
            void_area += abs(_poly_area(got))
    ra = (x1 - x0) * (z1 - z0)
    if void_area <= 1e-12:
        return "out", []
    if void_area >= ra * (1.0 - 1e-9):
        return "inside", []
    kept = [p for p in _kept_pieces(x0, x1, z0, z1, band)
            if len(p) >= 3 and abs(_poly_area(p)) > 1e-12]
    if not kept:
        return "inside", []
    return "clip", kept


def _family_y_profiles(stone):
    # type: (Dict[str, Any]) -> Tuple[Any, Any]
    """族局部 y 剖面 (y_front(z), y_back(z)) —— 与 families.py 逐式同源。
    wedge-std: 前脸随收分线性内收; slab: 直盒 [0, d]。"""
    fam = stone["family"]
    p = stone["params"]
    if fam == "slab":
        d = float(p["d"])
        return (lambda z: d), (lambda z: 0.0)
    if fam == "wedge-std":
        f0 = float(p.get("proud", 0.0))
        f1 = f0 - (float(p["hw_b"]) - float(p["hw_t"]))
        h = float(p["h"])
        d = float(p.get("d", p.get("back", 0.3) + f0))

        def _yf(z):
            return f0 + (f1 - f0) * (z / h)
        return _yf, (lambda z: _yf(z) - d)
    raise ValueError("family_y_profiles: unknown family %r" % (fam,))


def _prism(poly, y_front, y_back):
    # type: (List[Tuple[float, float]], Any, Any) -> Tuple[List[Tuple[float, float, float]], List[Tuple[int, ...]]]
    """x-z 凸多边形 -> 沿 y 双剖面(y=y_front(z)/y_back(z))的棱柱网格。
    侧面绕向与前/背盖反向(每条环边一正一反, 水密); 整体体积朝向交给
    export_print.flip_outward 单一归一。"""
    n = len(poly)
    vf = [(x, y_front(z), z) for (x, z) in poly]
    vb = [(x, y_back(z), z) for (x, z) in poly]
    verts = vf + vb
    faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((j, i, n + i, n + j))
    return verts, faces


def stone_world_bbox(stone):
    # type: (Dict[str, Any]) -> Tuple[float, float, float, float]
    """石块世界 x-z 足印(无旋转前提; 带旋转的裁剪不支持, 显式 raise)。"""
    if any(abs(r) > 1e-12 for r in stone["transform"][3:]):
        raise ValueError("stone_world_bbox: rotated stone %r not supported"
                         % (stone["id"],))
    verts, _ = _FAM.family_mesh(stone["family"], stone["params"])
    off = _M2.anchor_offset(stone["family"], stone["params"],
                            stone["transform"])
    xs = [v[0] + off[0] for v in verts]
    zs = [v[2] + off[2] for v in verts]
    return min(xs), max(xs), min(zs), max(zs)


def classify_stones(stones, bands=None):
    # type: (List[Dict[str, Any]], Optional[List[Dict[str, float]]]) -> Dict[str, Tuple[str, List[List[Tuple[float, float]]]]]
    """逐石 void 分类(各石只对自己孔带判定; 孔带互不重叠, 块不会跨带)。
    W4(2026-10-07 审查): 判为 clip 的石在 params 打 clipped=True 标 ——
    masonry2.materialize 对无烘焙网格的带标石显式 raise, 把"整块族网格
    静默顶替裁剪片"的前向陷阱(导出/再放置路径)变成响亮错误。"""
    if bands is None:
        bands = [arch_band(i) for i in range(_F.N_SPAN)]
    zone_idx = {"ARCH%02d" % (i + 1): i for i in range(_F.N_SPAN)}
    out = {}
    for s in stones:
        i = zone_idx.get(s["id"].split(".")[0])
        if i is None:
            out[s["id"]] = ("out", [])
            continue
        x0, x1, z0, z1 = stone_world_bbox(s)
        status, polys = clip_footprint(x0, x1, z0, z1, bands[i], band_key=i)
        if status == "clip":
            s["params"]["clipped"] = True
        out[s["id"]] = (status, polys)
    return out


def stone_local_mesh(stone, status="out", polys=None):
    # type: (Dict[str, Any], str, Optional[List[List[Tuple[float, float]]]]) -> Tuple[List[Tuple[float, float, float]], List[Tuple[int, ...]]]
    """石的材料化前局部网格: 未裁剪走参数化族; clip 片 -> 双剖面棱柱
    (局部系, 世界 x/z 减锚点偏移; 体积朝向由 flip_outward 单一归一)。"""
    if status != "clip":
        return _FAM.family_mesh(stone["family"], stone["params"])
    off = _M2.anchor_offset(stone["family"], stone["params"],
                            stone["transform"])
    yf, yb = _family_y_profiles(stone)
    verts = []     # type: List[Tuple[float, float, float]]
    faces = []     # type: List[Tuple[int, ...]]
    for poly in polys:
        lp = [(x - off[0], z - off[2]) for (x, z) in poly]
        pv, pf = _prism(lp, yf, yb)
        faces.extend(tuple(i + len(verts) for i in fc) for fc in pf)
        verts.extend(pv)
    return _EP.flip_outward(verts, faces)


def family_center(stone):
    # type: (Dict[str, Any]) -> Tuple[float, float, float]
    """整块(完整族网格)bbox 中点(局部系) —— materialize/GN 实例的旋转中心。"""
    verts, _ = _FAM.family_mesh(stone["family"], stone["params"])
    return tuple((min(v[i] for v in verts) + max(v[i] for v in verts)) / 2.0
                 for i in range(3))


def placement_point(stone):
    # type: (Dict[str, Any]) -> Tuple[float, float, float]
    """GN 实例点 = materialize 旋转中心(块中心世界位) = family_center + 偏移。
    实例几何 = family_center 平移到原点的局部网格(centered_verts), 实例
    旋转属性 = transform 后三位 —— 组合恒等于 masonry2.materialize(测试钉)。"""
    c = family_center(stone)
    off = _M2.anchor_offset(stone["family"], stone["params"],
                            stone["transform"])
    return (c[0] + off[0], c[1] + off[1], c[2] + off[2])


def centered_verts(stone, verts=None):
    # type: (Dict[str, Any], Optional[List[Tuple[float, float, float]]]) -> List[Tuple[float, float, float]]
    c = family_center(stone)
    if verts is None:
        verts, _ = _FAM.family_mesh(stone["family"], stone["params"])
    return [(v[0] - c[0], v[1] - c[1], v[2] - c[2]) for v in verts]


def family_identity(stone, status="out"):
    # type: (Dict[str, Any], str) -> str
    """族身份: 跨洞裁剪石逐石唯一(uniq:<sid>), 其余按 (family, params) 去重。"""
    if status == "clip":
        return "uniq:" + stone["id"]
    return stone["family"] + "|" + _json.dumps(stone["params"], sort_keys=True,
                                               separators=(",", ":"))


def family_obj_name(identity, index=None):
    # type: (str, Optional[int]) -> str
    """COL_FAMILIES 对象名: 排序稳定 + <63 字节不截断。
    index 给定时前缀序号使 sorted(名) == census 排序序(Pick Instance 序双保险)。"""
    slug = _hashlib.sha1(identity.encode("utf-8")).hexdigest()[:12]
    base = ("fam_" + identity.split("|")[0].replace(":", "_") + "_" + slug)
    if index is None:
        return base[:63]
    return ("fam_%04d_" % index + base)[:63]


def census(stones, statuses):
    # type: (List[Dict[str, Any]], Dict[str, Tuple[str, List[List[Tuple[float, float]]]]]) -> Dict[str, Dict[str, Any]]
    """族清点: identity -> 首见石(key 排序序 = emit 的对象创建序)。"""
    fams = {}      # type: Dict[str, Dict[str, Any]]
    for s in stones:
        fams.setdefault(family_identity(s, statuses[s["id"]][0]), s)
    return {k: fams[k] for k in sorted(fams)}


def mirror_spec(spec):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """砖谱 x->-x 镜像(9..16 孔复用 8..0 谱; 与 masonry._mirror_spec 同式;
    该模块 import bmesh 不可 headless 复用, 故此处独立实现)。"""
    out = {}       # type: Dict[str, Any]
    cs = []
    for c in spec.get("courses", []):
        c2 = dict(c)
        bl = c2.get("blocks")
        if isinstance(bl, list) and bl and isinstance(bl[0], dict):
            c2["blocks"] = [{"x0": -b["x1"], "x1": -b["x0"]} for b in reversed(bl)]
        elif isinstance(bl, list):
            c2["blocks"] = [-v for v in reversed(bl)]
        cs.append(c2)
    if cs:
        out["courses"] = cs
    return out


def load_spec(stones_dir, arch_idx):
    # type: (str, int) -> Dict[str, Any]
    """第 arch_idx 孔(0..16)砖谱: 前半直读, 后半镜像复用。"""
    half = _F.N_SPAN // 2
    src = arch_idx if arch_idx <= half else (_F.N_SPAN - 1 - arch_idx)
    with open(os.path.join(stones_dir, "stones_p%d.json" % src),
              "r", encoding="utf-8") as f:
        spec = _json.load(f)
    return mirror_spec(spec) if arch_idx > half else spec


def cap_to_deck(stones, min_h=0.025, stats=None):
    # type: (List[Dict[str, Any]], float, Optional[Dict[str, Any]]) -> List[Dict[str, Any]]
    """场景链收口: 砌体顶截到桥面弧线。

    砖谱末层 z0 是照片描摹的平线; 桥面是抛物线(端孔一孔内落差可达 0.5m),
    平线末层按谱层高直砌会在桥面上方露出条带。规则: 每块按【块心】桥面标高
    截顶; 整块底已高于桥面(截后 h <= min_h)的场景侧不留 —— 那里的墙不存在,
    但必须记数归账(stats["skipped_below_deck"/"skipped_ids"], H1: 静默弃曾
    把超底 slab 藏成账实不符)。
    锚语义按族分派(masonry2.anchor_offset 同一分派表, H1 修复核心):
      wedge-std 块中心锚: z0=tz-h/2, 截顶后 zm=z0+h2/2、hw_t 随实高重算,
                         transform[1] 前脸锚按新层中同步重算(T8b-A1:
                         旧值锚原层中, 截顶石内错撞进背衬退让线);
      slab 最小角锚:     z0=tz(=bbox.z0), 截顶只改 params.h 与 bbox.z1,
                         transform[2] 不动, 维持 bbox.z0==transform[2]。
    桥面采样 x 一律块心: slab 用 bbox 中点 —— 旧版对 slab 误用最小角锚公式
    (z0=tz-h/2 半高虚低 + 采样 x0), 截顶线系统性偏高, CORE 顶穿桥面
    (实测越顶 29 块/旧断言口径)。只改本链自建 stone dict, 不触碰 masonry2
    生成器与其冻结测试语义。"""
    out = []
    for s in stones:
        p = s["params"]
        h = float(p["h"])
        if s["family"] in _M2._ANCHOR_MIN_CORNER:
            bb = p["bbox"]
            z0 = float(s["transform"][2])
            cap = deck_z_at(0.5 * (float(bb["x0"]) + float(bb["x1"])))
        else:
            z0 = float(s["transform"][2]) - h / 2.0
            cap = deck_z_at(float(s["transform"][0]))
        h2 = min(h, cap - z0)
        if h2 <= min_h:
            if stats is not None:
                stats["skipped_below_deck"] = \
                    stats.get("skipped_below_deck", 0) + 1
                stats.setdefault("skipped_ids", []).append(s["id"])
            continue
        if h2 < h - 1e-12:
            p["h"] = h2
            if s["family"] in _M2._ANCHOR_MIN_CORNER:
                p["bbox"]["z1"] = z0 + h2   # 最小角锚: transform[2] 不动
            else:
                s["transform"][2] = z0 + h2 / 2.0
                if s["family"] == "wedge-std" and "hw_t" in p:
                    p["hw_t"] = hw_wall(float(s["transform"][0]), z0 + h2)
                    # T8b-A1: 截顶后层带中点下移, 前脸锚(transform[1])必须
                    # 按新层中重算 —— 旧值仍锚在原层中 hw(zm_orig)+proud,
                    # 截顶石前脸/内缘面整体内错 δ=hw(zm_orig)-hw(zm_new),
                    # 撞进同位背衬退让线(审查恒等式
                    # pen+BACKING_GAP ≡ −(|ty|−(hw+proud)), 修复前全链
                    # 116 对 pen>0 全部是截顶石)。背衬石(front_c 锚)生而已
                    # 截不经此路径, 同式重算亦保持其语义。
                    c_key = "front_c" if "front_c" in p else "proud"
                    y_new = hw_wall(float(s["transform"][0]),
                                    z0 + h2 / 2.0) + float(p[c_key])
                    s["transform"][1] = (y_new if s["transform"][1] >= 0.0
                                         else -y_new)
                if "bbox" in p:
                    p["bbox"]["z1"] = z0 + h2
        out.append(s)
    return out


def bridge_ledger(stones_dir=None):
    # type: (Optional[str]) -> Dict[str, Any]
    """全桥砌体账目: 面石(谱)+背衬+core × 17 孔 × 东西两面。
    末层高兜底 = 拱心线桥面标高 - 谱末层 z0(砌体顶随桥面弧线封口);
    core 带界 = 孔带(首末孔外扩到桥端, 补桥台条带); z 带 = 水下底..桥面。
    整块超底弃石记入 meta.skipped_below_deck(_ids) 并打日志(H1 归账)。"""
    if stones_dir is None:
        stones_dir = os.path.join(HERE, "stones")
    px, _spans = piers_and_spans()
    skipped = {"skipped_below_deck": 0, "skipped_ids": []}
    stones = []    # type: List[Dict[str, Any]]
    for i in range(_F.N_SPAN):
        spec = load_spec(stones_dir, i)
        band = arch_band(i)
        ch = max(0.05, band["z_hi"] - spec["courses"][-1]["z0"])
        for side in (1, -1):
            faces = _M2.face_stones(spec, i, side, hw_wall, course_h=ch)
            faces = cap_to_deck(faces, stats=skipped)
            stones.extend(faces)
            # [P2-T6b] 背衬种子跨孔镜像锚: 东半孔用镜像孔种子, 配合
            # backing_stones 内的倒序消费, 镜像位深度与西镜像孔一致。
            seed_bk = (_F.N_SPAN - 1 - i) if _M2.bridge_mirror_phase(i) else i
            stones.extend(cap_to_deck(
                _M2.backing_stones(faces, hw_wall, seed=seed_bk), stats=skipped))
        x_lo = -_F.BRIDGE_LEN / 2.0 if i == 0 else band["x_lo"]
        x_hi = _F.BRIDGE_LEN / 2.0 if i == _F.N_SPAN - 1 else band["x_hi"]
        stones.extend(cap_to_deck(
            _M2.core_cells(i, hw_wall, _BODY_BOTTOM, band["z_hi"],
                           x_lo, x_hi, seed=i), stats=skipped))
    print("SKIPPED_BELOW_DECK n=%d" % skipped["skipped_below_deck"])
    return {"meta": {"schema": _LED.SCHEMA, "curve_hash": "e30-p1t7-bridge",
                     "seed": 0,
                     "skipped_below_deck": skipped["skipped_below_deck"],
                     "skipped_below_deck_ids": skipped["skipped_ids"]},
            "stones": stones}


def layout_group(stone):
    # type: (Dict[str, Any]) -> str
    """GN 分区 collection: CORE 石按块心 x 落 ABUT_W/ABUT_E/CORE, 其余按孔。"""
    if stone.get("role_struct") == "CORE":
        c = family_center(stone)
        off = _M2.anchor_offset(stone["family"], stone["params"],
                                stone["transform"])
        wx = c[0] + off[0]
        px, _spans = piers_and_spans()
        if wx < px[0]:
            return "ABUT_W"
        if wx > px[-1]:
            return "ABUT_E"
        return "CORE"
    return "SPAN" + stone["id"].split(".")[0][4:]


def layout_groups():
    # type: () -> List[str]
    return (["SPAN%02d" % (i + 1) for i in range(_F.N_SPAN)]
            + ["ABUT_E", "ABUT_W", "CORE"])


def _check_geom_parity():
    # type: () -> None
    """blender 模式硬门: facts 独立推导与 bridge_geom2 生成器零漂移。"""
    if G is None:
        return
    px, spans = piers_and_spans()
    for i in range(_F.N_SPAN + 1):
        assert abs(px[i] - G.PIER_X[i]) < 1e-9, "PIER_X 漂移 @%d" % i
    for i in range(_F.N_SPAN):
        assert abs(spans[i] - G.SPANS[i]) < 1e-9, "SPANS 漂移 @%d" % i
        band = arch_band(i)
        assert abs(band["springer"] - G.arch_springer_z(i)) < 1e-9, \
            "起拱线漂移 @%d" % i
        assert abs(deck_z_at(0.5 * (band["x_lo"] + band["x_hi"]))
                   - G.deck_z(0.5 * (band["x_lo"] + band["x_hi"]))) < 1e-9


def emit_lib():
    # type: () -> None
    """--emit-lib: 全桥账目 -> 每族一个局部网格对象入 COL_FAMILIES ->
    out/families.blend; 账目副本落 out/ledger_bridge.json 备审计。"""
    _check_geom_parity()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    led = bridge_ledger()
    errs = _LED.validate_ledger(led)
    if errs:
        raise ValueError("bridge ledger invalid: %s" % errs[:5])
    statuses = classify_stones(led["stones"])
    fams = census(led["stones"], statuses)
    col = bpy.data.collections.new(COL_FAMILIES)
    for idx, key in enumerate(sorted(fams)):
        st = fams[key]
        status, polys = statuses[st["id"]]
        verts, faces = stone_local_mesh(st, status, polys)
        c = family_center(st)
        cv = [(v[0] - c[0], v[1] - c[1], v[2] - c[2]) for v in verts]
        me = bpy.data.meshes.new(family_obj_name(key, idx))
        me.from_pydata(cv, [], [tuple(fc) for fc in faces])
        me.validate()
        ob = bpy.data.objects.new(me.name, me)
        col.objects.link(ob)
    bpy.context.scene.collection.children.link(col)
    out = os.path.join(HERE, "out")
    os.makedirs(out, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, "families.blend"))
    with open(os.path.join(out, "ledger_bridge.json"), "w",
              encoding="utf-8") as fp:
        _json.dump(led, fp, ensure_ascii=False)
    print("FAMILIES_EMIT n=%d" % len(fams))


def _gn_layout_node_group(fam_col):
    # type: (Any) -> Any
    """共享 GN 树: 点云 -> (in_void 剔点) -> Instance on Points
    (Collection Info separate+Pick Instance, 实例序号=fam_idx, 朝向=rot)。"""
    ng = bpy.data.node_groups.new("P1_LAYOUT_INSTANCES", 'GeometryNodeTree')
    ng.interface.new_socket("Geometry", in_out='INPUT',
                            socket_type='NodeSocketGeometry')
    ng.interface.new_socket("Instances", in_out='OUTPUT',
                            socket_type='NodeSocketGeometry')
    nin = ng.nodes.new('NodeGroupInput')
    ndel = ng.nodes.new('GeometryNodeDeleteGeometry')
    ndel.domain = 'POINT'
    ndel.mode = 'ALL'
    nvoid = ng.nodes.new('GeometryNodeInputNamedAttribute')
    nvoid.data_type = 'BOOLEAN'
    nvoid.inputs['Name'].default_value = "in_void"
    niop = ng.nodes.new('GeometryNodeInstanceOnPoints')
    niop.inputs['Pick Instance'].default_value = True
    ncoll = ng.nodes.new('GeometryNodeCollectionInfo')
    ncoll.inputs['Collection'].default_value = fam_col
    ncoll.transform_space = 'ORIGINAL'
    ncoll.inputs['Separate Children'].default_value = True
    ncoll.inputs['Reset Children'].default_value = False
    nidx = ng.nodes.new('GeometryNodeInputNamedAttribute')
    nidx.data_type = 'INT'
    nidx.inputs['Name'].default_value = "fam_idx"
    nrot = ng.nodes.new('GeometryNodeInputNamedAttribute')
    nrot.data_type = 'FLOAT_VECTOR'
    nrot.inputs['Name'].default_value = "rot"
    nout = ng.nodes.new('NodeGroupOutput')
    lk = ng.links.new
    lk(nin.outputs[0], ndel.inputs['Geometry'])
    lk(nvoid.outputs[0], ndel.inputs['Selection'])
    lk(ndel.outputs[0], niop.inputs['Points'])
    lk(ncoll.outputs['Instances'], niop.inputs['Instance'])
    lk(nidx.outputs[0], niop.inputs['Instance Index'])
    lk(nrot.outputs[0], niop.inputs['Rotation'])
    lk(niop.outputs['Instances'], nout.inputs[0])
    return ng


def layout_scene():
    # type: () -> None
    """--layout: 空场景 link families.blend 的 COL_FAMILIES -> 每分区一片
    点云(顶点=块中心; sid/fam/fam_idx/stage/mat/xyz/rot/in_void) -> 共享
    GN 树实例化; 场景 Object 数硬门 < LAYOUT_MAX_OBJECTS。"""
    _check_geom_parity()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    lib = os.path.join(HERE, "out", "families.blend")
    if not os.path.isfile(lib):
        raise RuntimeError("layout 需先 --emit-lib 生成 out/families.blend")
    bpy.ops.wm.link(directory=os.path.join(lib, "Collection"),
                    filename=COL_FAMILIES)
    # wm.link 会自动放一个 collection-instance empty; 摘掉只留数据引用,
    # COL_FAMILIES 不进 view layer -> 家族对象不计入场景 Object 数。
    for ob in list(bpy.data.objects):
        if ob.instance_type == 'COLLECTION':
            bpy.data.objects.remove(ob, do_unlink=True)
    fam_col = bpy.data.collections.get(COL_FAMILIES)
    if fam_col is None:
        raise RuntimeError("families.blend 缺 %s" % COL_FAMILIES)
    led = bridge_ledger()
    statuses = classify_stones(led["stones"])
    fams = census(led["stones"], statuses)
    key_order = sorted(fams)
    expect_names = [family_obj_name(k, i) for i, k in enumerate(key_order)]
    got_names = [ob.name for ob in fam_col.objects]
    if sorted(got_names) != sorted(expect_names):
        raise RuntimeError("族库对象与清点不一致: %d vs %d"
                           % (len(got_names), len(expect_names)))
    key_idx = {k: i for i, k in enumerate(key_order)}
    ng = _gn_layout_node_group(fam_col)
    cols = {}
    for g in layout_groups():
        c = bpy.data.collections.new(g)
        bpy.context.scene.collection.children.link(c)
        cols[g] = c
    by_group = {}     # type: Dict[str, List[Dict[str, Any]]]
    for s in led["stones"]:
        by_group.setdefault(layout_group(s), []).append(s)
    total = 0
    for g in layout_groups():
        stones_g = by_group.get(g, [])
        me = bpy.data.meshes.new("pts_" + g)
        me.from_pydata([placement_point(s) for s in stones_g], [], [])
        me.validate()
        n = len(stones_g)
        a_sid = me.attributes.new("sid", 'STRING', 'POINT')
        a_fam = me.attributes.new("fam", 'STRING', 'POINT')
        a_fi = me.attributes.new("fam_idx", 'INT', 'POINT')
        a_st = me.attributes.new("stage", 'STRING', 'POINT')
        a_mat = me.attributes.new("mat", 'STRING', 'POINT')
        a_xyz = me.attributes.new("xyz", 'FLOAT_VECTOR', 'POINT')
        a_rot = me.attributes.new("rot", 'FLOAT_VECTOR', 'POINT')
        a_iv = me.attributes.new("in_void", 'BOOLEAN', 'POINT')
        for k, s in enumerate(stones_g):
            status, _polys = statuses[s["id"]]
            # Blender 5.x STRING 属性值是 bytes
            a_sid.data[k].value = s["id"].encode("utf-8")
            a_fam.data[k].value = s["family"].encode("utf-8")
            a_fi.data[k].value = key_idx[family_identity(s, status)]
            a_st.data[k].value = (s.get("stage_hint") or "").encode("utf-8")
            a_mat.data[k].value = (s.get("material") or "").encode("utf-8")
            a_xyz.data[k].vector = tuple(s["transform"][:3])
            a_rot.data[k].vector = tuple(s["transform"][3:6])
            a_iv.data[k].value = (status == "inside")
        ob = bpy.data.objects.new("points_" + g, me)
        m = ob.modifiers.new("gn", 'NODES')
        m.node_group = ng
        cols[g].objects.link(ob)
        total += n
        print("LAYOUT_GROUP %s stones=%d" % (g, n))
    nobj = len(bpy.context.scene.objects)
    print("LAYOUT_STONES n=%d" % total)
    print("LAYOUT_OBJECTS n=%d" % nobj)
    if nobj >= LAYOUT_MAX_OBJECTS:
        raise RuntimeError("LAYOUT_OBJECTS %d >= %d" % (nobj, LAYOUT_MAX_OBJECTS))
    out = os.path.join(HERE, "out")
    os.makedirs(out, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, "e30_layout.blend"))


if __name__ == "__main__":
    _argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    _flags = {a for a in _argv if a.startswith("--")}
    if "--emit-lib" in _flags:
        emit_lib()
    elif "--layout" in _flags:
        layout_scene()
    else:
        # proxy(默认): 现行合并网格路径, 行为逐位不变
        build()
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "e30_bridge.blend"))
        print("SAVED v2")
