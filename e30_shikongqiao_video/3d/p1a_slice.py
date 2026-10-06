# e30_shikongqiao_video/3d/p1a_slice.py
# -*- coding: utf-8 -*-
"""P1-T8 G2 门: RING/IMPOST 入账(单一真相=masonry 图元) + 全桥 printcheck
+ 中央孔(ARCH09)试印包。

真几何源(接线清单①, 单一真相, 禁止第二套楔形公式):
  RING   <- spy 捕获 masonry.build_voussoir 的逐石调用参数, 再用同一图元
            masonry._voussoir 逐石重放提取网格;
  IMPOST <- spy 捕获 masonry.build_impost 的逐石 masonry._stone 调用参数,
            同图元逐石重放提取。
两链各带【顶点多重集互证】: 全局 bmesh 顶点排序表 == 逐石顶点排序表拼接
(1e-9 量化), 任何几何漂移 assert 响亮。数量互证: RING 总数 ==
masonry_stats.voussoir_total(193), IMPOST == coursing_regions.impost(492)。

账目条目(纯逻辑, blender-free 可测): role RING(family ring-wedge, 质心锚)
/ IMPOST(family impost-step, wedge 前脸锚); 局部网格经扇形三角化烘焙进
params.bake(families._baked 确定性还原), 锚语义见 masonry2._ANCHOR_CENTROID
/_ANCHOR_WEDGE_FRONT。

下游(全 blender-free): run_g2 出 G2 报告(全桥逐石 post-inset check_stone
scale=1/50 min_wall_print_mm=1.2 + 每孔 20 对相邻石 gap_check);
export_slice 出 out/print/central_slice/(STL/3MF/manifest)。

用法(blender 内):
  blender -b --python p1a_slice.py -- --g2          # 全链: 账目+互证+G2+试印包+装配图
  blender -b --python p1a_slice.py -- --ledger-only # 只建账+互证断言(快迭代)
普通 python: import p1a_slice 纯逻辑段(测试)或消费 out/ledger_full.json。
"""
import copy
import json
import math
import os
import sys
import time

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

# blender 依赖守护导入(与 build_scene2 同纪律): 无 bmesh(普通 pytest 环境)
# 置 None —— 提取函数不可用, 纯逻辑段(条目构造/锚语义/G2 报告/切片过滤/
# 相邻缝对采样/报告结构闸门)全部可用。
try:
    import bmesh as _bmesh
    import masonry as _MAS
    import bridge_geom2 as G
    _HAS_BLENDER = True
except ImportError:   # pragma: no cover - blender-free 环境
    _bmesh = None
    _MAS = None
    G = None
    _HAS_BLENDER = False

# T8b(case_B 带裁剪): masonry 的切割折线纯函数(_hole_cut_polyline/
# _bottom_bound/_clip_jamb)不触 bmesh, 但模块顶部 import bmesh 挡住了
# blender-free 环境。用空 bmesh 桩完成导入(用完即撤桩, masonry 持有的
# 是模块引用), 让"洞∪券环带"单一真相折线在 pytest 下可测 —— 裁剪与
# 提取(真 bmesh 用户)仍严格分离。
_MAS_PURE = False
if not _HAS_BLENDER:
    import types as _types
    _stubs = {}
    for _name in ("bmesh", "mathutils"):
        if sys.modules.get(_name) is None:
            _mod = _types.ModuleType(_name)
            if _name == "mathutils":
                # masonry 只在 bmesh 路径用 Vector/Matrix; 纯函数不触
                _mod.Vector = _mod.Matrix = object
            sys.modules[_name] = _mod
            _stubs[_name] = True
    try:
        import masonry as _mas_pure
        _MAS = _mas_pure          # 纯函数可用; 提取函数仍 _HAS_BLENDER 门控
        _MAS_PURE = True
    except ImportError:           # pragma: no cover
        pass
    finally:
        for _name in _stubs:
            sys.modules.pop(_name, None)
    del _types, _stubs

import build_scene2 as BS
import export_print as EP
import facts as _F
import ledger as L
import masonry2 as M2
import printcheck as PC

# ── 常量 ───────────────────────────────────────────────────────────────
RING_FAMILY = "ring-wedge"
IMPOST_FAMILY = "impost-step"
RING_MATERIAL = "qingshi"
IMPOST_MATERIAL = "qingshi"
RING_IMPOST_ROLES = ("RING", "IMPOST")
SLICE_ZONE_IDX = 8                       # 中央孔 ARCH09(0 基)
FULL_LEDGER_NAME = "ledger_full.json"
OUT_DIR = os.path.join(_HERE, "out")
PRINT_DIR = os.path.join(OUT_DIR, "print")
SLICE_DIR = os.path.join(PRINT_DIR, "central_slice")

# G2 门口径(接线清单③): 门常数写进名字, 报告与测试共引
G2_SCALE = 1.0 / 50.0
G2_MIN_WALL_PRINT_MM = 1.2
G2_GAP_TOL_MODEL_MM = 0.5
G2_GAP_PAIRS_PER_ARCH = 20
G2_N_ARCH = _F.N_SPAN

# 券环几何参考值(提取处 masonry.RING_T / build_voussoir keystone lift 同源;
# blender 侧 build_ring_entries 断言与 _MAS.RING_T 逐位相等, 漂移即响亮)
RING_T_REF = 0.54
KEYSTONE_LIFT_REF = 0.07


# ══ 纯逻辑段(blender-free) ════════════════════════════════════════════

def _cross2(o, a, b):
    # type: (tuple, tuple, tuple) -> float
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _point_in_tri(p, t0, t1, t2):
    # type: (tuple, tuple, tuple, tuple) -> bool
    d1 = _cross2(t0, t1, p)
    d2 = _cross2(t1, t2, p)
    d3 = _cross2(t2, t0, p)
    has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
    has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
    return not (has_neg and has_pos)


def _triangulate_simple(poly2d):
    # type: (list) -> list
    """简单多边形耳切三角化(x-z 投影)。券环帽面是【薄环扇】(非凸: 内弧向
    内凹), 任意顶点扇形化会产生互相覆盖/反绕三角(printcheck 实测: 帽面
    对 t=0.000mm THIN_WALL 假阳 + SELF_INTERSECT); 耳切对凸/非凸一致正确。
    数值退化(找不到耳)回退扇形并保持可运行。"""
    n = len(poly2d)
    if n < 3:
        return []
    area2 = 0.0
    for i in range(n):
        area2 += _cross2((0.0, 0.0), poly2d[i], poly2d[(i + 1) % n])
    ccw = area2 > 0.0
    idx = list(range(n))
    tris = []
    guard = 0
    while len(idx) > 3 and guard < 20 * n + 100:
        guard += 1
        m = len(idx)
        ear_at = -1
        for k in range(m):
            i0, i1, i2 = idx[(k - 1) % m], idx[k], idx[(k + 1) % m]
            cr = _cross2(poly2d[i0], poly2d[i1], poly2d[i2])
            if ccw and cr <= 1e-13:
                continue
            if (not ccw) and cr >= -1e-13:
                continue
            bad = False
            for j in idx:
                if j in (i0, i1, i2):
                    continue
                if _point_in_tri(poly2d[j], poly2d[i0], poly2d[i1],
                                 poly2d[i2]):
                    bad = True
                    break
            if not bad:
                ear_at = k
                break
        if ear_at < 0:
            break    # 数值退化兜底: 剩余顶点扇形化
        i0, i1, i2 = idx[(ear_at - 1) % len(idx)], idx[ear_at], \
            idx[(ear_at + 1) % len(idx)]
        tris.append((i0, i1, i2))
        idx.pop(ear_at)
    if len(idx) == 3:
        tris.append((idx[0], idx[1], idx[2]))
    elif len(idx) > 3:
        for t in range(1, len(idx) - 1):     # 退化兜底: 剩余扇形化
            tris.append((idx[0], idx[t], idx[t + 1]))
    return tris


def triangulate_faces(verts, faces):
    # type: (list, list) -> list
    """打印视图三角化: 3 边形直通; 4 边形对角线剖分(棱柱侧沿=条带面, 两对角
    等价); >=5 边形(券环帽面/裁剪片帽面/线脚前脸幕面)按 x-z 投影耳切。
    只动拓扑不动几何 —— 顶点表逐位不动(互证闸门只对顶点)。"""
    out = []
    for fc in faces:
        if len(fc) == 3:
            out.append((int(fc[0]), int(fc[1]), int(fc[2])))
        elif len(fc) == 4:
            out.append((int(fc[0]), int(fc[1]), int(fc[2])))
            out.append((int(fc[0]), int(fc[2]), int(fc[3])))
        else:
            poly2d = [(verts[i][0], verts[i][2]) for i in fc]
            for (a, b, c) in _triangulate_simple(poly2d):
                out.append((int(fc[a]), int(fc[b]), int(fc[c])))
    return out


def _bbox_center(verts):
    # type: (list) -> tuple
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    zs = [v[2] for v in verts]
    return ((min(xs) + max(xs)) / 2.0,
            (min(ys) + max(ys)) / 2.0,
            (min(zs) + max(zs)) / 2.0)


def _bake(world_verts, world_faces, center):
    # type: (list, list, tuple) -> tuple
    """世界网格 -> (质心锚局部 verts, 原始 faces) —— params.bake 载荷。
    烘焙=提取时的 masonry 原网格(单一真相); 打印视图三角化在 world_mesh
    消费时做(triangulate_faces), 不进 bake。"""
    local = [(v[0] - center[0], v[1] - center[1], v[2] - center[2])
             for v in world_verts]
    return local, [tuple(int(i) for i in fc) for fc in world_faces]


def make_ring_entry(arch_idx, k, world_verts, world_faces, trace,
                    material=RING_MATERIAL):
    # type: (int, int, list, list, dict, str) -> dict
    """RING 账目条目(纯): 质心锚 local + 溯源 params(xc/k/angles/stations)。
    全深筒券一块贯通前后墙, id face 记 EAST 为正典面(id 语法要求 EAST|WEST
    二选一), params.through="full_depth" 标记贯通语义。"""
    center = _bbox_center(world_verts)
    local, faces = _bake(world_verts, world_faces, center)
    params = {"xc": float(trace["xc"]), "k": int(k),
              "stations": [float(trace["x0"]), float(trace["x1"])],
              "angles": [float(trace["ang0"]), float(trace["ang1"])],
              "ring_t": float(trace["ring_t"]), "lift": float(trace["lift"]),
              "n_ring": int(trace["n"]), "through": "full_depth",
              "bake": {"v": local, "f": faces}}
    return L.new_stone("ARCH%02d" % (arch_idx + 1), "EAST", "RING", 0,
                       int(k) + 1, RING_FAMILY, params,
                       [center[0], center[1], center[2], 0.0, 0.0, 0.0],
                       material, evidence="ashlar_truth")


def make_impost_entry(arch_idx, k, world_verts, world_faces, trace,
                      material=IMPOST_MATERIAL):
    # type: (int, int, list, list, dict, str) -> dict
    """IMPOST 账目条目(纯): wedge 前脸锚(transform x/z=块中心, y=前脸位)。
    trace: xc/k/step/sgn(face 墙面)/x0/x1/z0/z1/proud/back/ty_front。"""
    x0, x1 = float(trace["x0"]), float(trace["x1"])
    z0, z1 = float(trace["z0"]), float(trace["z1"])
    w, h = x1 - x0, z1 - z0
    cx, cz = (x0 + x1) / 2.0, (z0 + z1) / 2.0
    proud = float(trace["proud"])
    ty = float(trace["ty_front"])
    off = (cx - w / 2.0, ty - proud, cz - h / 2.0)
    local = [(v[0] - off[0], v[1] - off[1], v[2] - off[2]) for v in world_verts]
    faces = [tuple(int(i) for i in fc) for fc in world_faces]
    params = {"w": w, "h": h, "proud": proud, "back": float(trace["back"]),
              "xc": float(trace["xc"]), "k": int(k), "step": int(trace["step"]),
              "arch_side": int(trace["sgn"]), "proj": float(trace["proj"]),
              "bake": {"v": local, "f": faces}}
    return L.new_stone("ARCH%02d" % (arch_idx + 1), trace["face"], "IMPOST",
                       int(trace["step"]), int(k) + 1, IMPOST_FAMILY, params,
                       [cx, ty, cz, 0.0, 0.0, 0.0],
                       material, evidence="ashlar_truth")


def classify_full(stones):
    # type: (list) -> dict
    """全桥账目(现链+RING+IMPOST)的 void 分类: RING/IMPOST 真几何直判 out ——
    其 AABB 必与洞带相交(券腹曲线穿过盒角), 是盒分类伪影, 真实多边形与
    净空零重叠; 打 params.clipped 标会误触 materialize 的烘焙网格 raise。
    其余石走 build_scene2.classify_stones 原语义零改动。"""
    out = BS.classify_stones(
        [s for s in stones if s.get("role_struct") not in RING_IMPOST_ROLES])
    for s in stones:
        if s.get("role_struct") in RING_IMPOST_ROLES:
            out[s["id"]] = ("out", [])
    return out


def world_mesh(stone, statuses):
    # type: (dict, dict) -> tuple
    """世界系网格(G2 与导出同一来源): 常规石走 materialize 默认族路径
    (RING/IMPOST= params.bake 经 families._baked); clip 石喂
    build_scene2.stone_local_mesh 烘焙棱柱(接线清单④, 与 families.blend
    emit 的族对象同一 stone_local_mesh 定义), materialize 对缺烘焙网格的
    clip 石 raise 是期望防线。输出经 triangulate_faces(打印视图: 三角面
    恒平面且耳切无覆盖; 顶点表逐位不动)。"""
    status, polys = statuses[stone["id"]]
    if status == "ring_trim":
        # T8b case_B: 带裁保留片(世界坐标 _prism_stitched 单壳)
        return _ring_trim_mesh(polys, stone)
    if status == "clip":
        local, faces = BS.stone_local_mesh(stone, status, polys)
        verts, faces = M2.materialize(stone, local, faces)
    else:
        verts, faces = M2.materialize(stone)
    return verts, triangulate_faces(verts, faces)


def _arch_normal2(x, band):
    # type: (float, dict) -> tuple
    """内弧单位法向(指向拱外), 与 masonry._arch_normal 同式(facts 单一来源)。"""
    d = _F.arch_dzdx(x, band["xc"], band["springer"], band["a"], band["b"])
    lng = math.hypot(d, 1.0)
    return (-d / lng, 1.0 / lng)


RING_RASTER_CELL = 0.02      # B3: RING 真剪影栅格步长(2cm x-z, 审查 probe13 口径)
RING_OVERLAP_RATIO = 0.5     # 面积占比 > 50% 才入 ring_band_overlap(只记账,
                             # 绝不是丢弃许可 —— 处置由 volume 宇宙裁决)


def _xz_cells_of_tris(tris, cell=RING_RASTER_CELL):
    # type: (list, float) -> set
    """三角面片 x-z 投影逐三角填格(格心在三角内)。闭曲面剪影 = 全部面
    投影的并集 —— 逐格中心采样, 不用 bbox(弦框含弦-弧间空气, 审查 B 口径)。"""
    cells = set()
    for t in tris:
        pa, pb, pc = t
        x0 = min(pa[0], pb[0], pc[0])
        x1 = max(pa[0], pb[0], pc[0])
        z0 = min(pa[2], pb[2], pc[2])
        z1 = max(pa[2], pb[2], pc[2])
        ix0, ix1 = int(math.floor(x0 / cell)), int(math.ceil(x1 / cell))
        iz0, iz1 = int(math.floor(z0 / cell)), int(math.ceil(z1 / cell))
        if ix1 <= ix0 or iz1 <= iz0:
            continue
        gx = (np.arange(ix0, ix1) + 0.5) * cell
        gz = (np.arange(iz0, iz1) + 0.5) * cell
        GX, GZ = np.meshgrid(gx, gz, indexing="ij")
        d1 = (pb[0] - pa[0]) * (GZ - pa[2]) - (pb[2] - pa[2]) * (GX - pa[0])
        d2 = (pc[0] - pb[0]) * (GZ - pb[2]) - (pc[2] - pb[2]) * (GX - pb[0])
        d3 = (pa[0] - pc[0]) * (GZ - pc[2]) - (pa[2] - pc[2]) * (GX - pc[0])
        inside = ~(((d1 < 0) | (d2 < 0) | (d3 < 0))
                   & ((d1 > 0) | (d2 > 0) | (d3 > 0)))
        for ii, jj in zip(*np.nonzero(inside)):
            cells.add((ix0 + int(ii), iz0 + int(jj)))
    return cells


def _stone_silhouette_cells(stone, statuses, cell=RING_RASTER_CELL):
    # type: (dict, dict, float) -> set
    """石块世界网格 x-z 真剪影格(可打印几何: clip/带裁石=裁后棱柱)。"""
    verts, faces = world_mesh(stone, statuses)
    return _xz_cells_of_tris(_flat_tris(PC._face_tris(
        np.asarray(verts, dtype=float), faces)), cell)


def _ring_footprint_raster(led, cell=RING_RASTER_CELL):
    # type: (dict, float) -> dict
    """RING 真剪影栅格(B 口径, 审查 probe13): {zone: set((ix,iz))} —— 每块
    RING 烘焙网格逐三角投影 x-z 填格的并集。不取石 bbox(弦框把弦-弧间
    空气记成环, 测的是另一个量)。"""
    raster = {}
    for s in led["stones"]:
        if s.get("role_struct") != "RING":
            continue
        zone = s["id"].split(".")[0]
        verts, faces = world_mesh(s, {s["id"]: ("out", [])})
        cells = raster.setdefault(zone, set())
        cells |= _xz_cells_of_tris(_flat_tris(PC._face_tris(
            np.asarray(verts, dtype=float), faces)), cell)
    return raster


def _ring_overlap_ratio(stone, raster, statuses, cell=RING_RASTER_CELL):
    # type: (dict, dict, dict, float) -> float
    """石足印(自身真剪影格数=分母, 非 bbox)与所在孔 RING 剪影并集的交
    面积占比。面积 ratio 只做记账/排除吞没石, 不做丢弃许可(T8b 纪律)。"""
    zone = stone["id"].split(".")[0]
    cells = raster.get(zone)
    if not cells:
        return 0.0
    own = _stone_silhouette_cells(stone, statuses, cell)
    if not own:
        return 0.0
    return len(own & cells) / float(len(own))


def print_scope(led, statuses):
    # type: (dict, dict) -> dict
    """G2 打印范围(试印单元)划分: RING/IMPOST 真几何全入; 链条石按
    实测几何分桶排除(全部带 id 记录, 如实入报告 scope):
      in_void           场景链洞内理想化石(布局即剔除) = 空气, 不印;
      void_cut_fragment 切洞裁剪片: 与 RING 带重复建模(实测 400+ 件 <6cm
                        碎片/双壳), 打印以 RING 为准;
      ring_band_overlap 未裁剪但足印(真剪影面积)与 RING 剪影交占比 >50%
                        的链条石(与 RING 双重建模; 完全吞没石必落此桶),
                        打印以 RING 为准。面积 ratio 只做排除吞没石的
                        记账判据, 低重叠回收石的真撞处置由 volume 宇宙
                        (ring_dedup)裁决 —— 它不是丢弃许可;
      thin_merge        post-inset 最小打印壁 < 1.2mm 的截顶残层/窄条。
                        语义 = 谁都不单独印它: 与邻层合印(合印后材料仍在
                        件上), 不可单独成件。
    雕件/桥台本就不在账(P4/接线清单⑤), 与 export 白名单同口径。"""
    raster = _ring_footprint_raster(led)
    scope = []
    buckets = {"in_void": [], "void_cut_fragment": [],
               "ring_band_overlap": [], "thin_merge": []}
    for s in led["stones"]:
        role = s.get("role_struct")
        if role in RING_IMPOST_ROLES:
            scope.append(s)
            continue
        st = statuses[s["id"]][0]
        if st == "inside":
            buckets["in_void"].append(s["id"])
            continue
        if st == "clip":
            buckets["void_cut_fragment"].append(s["id"])
            continue
        if _ring_overlap_ratio(s, raster, statuses) > RING_OVERLAP_RATIO:
            buckets["ring_band_overlap"].append(s["id"])
            continue
        verts, _faces = world_mesh(s, statuses)
        _fit, clr_model = EP.fit_for_block(EP._extents_m(verts), G2_SCALE)
        v2 = EP.inset(verts, clr_model)
        ext = EP._extents_m(v2)
        if min(ext) * G2_SCALE * 1000.0 < G2_MIN_WALL_PRINT_MM:
            buckets["thin_merge"].append(s["id"])
            continue
        scope.append(s)
    return {"scope": scope, "buckets": buckets}


def _gap_entry(stone, statuses):
    # type: (dict, dict) -> tuple
    """gap_check entry = (transform 6 元组, (post-inset verts, faces))。
    W2 契约: gap_check 内部 _xform 对 verts 施加【原始 transform 6 元组】
    (旋转+平移), 故 entry verts 必须是 world - transform[0:3](同帧还原),
    不是 world - anchor_offset —— 后者是 materialize 的放置偏移, 两者相差
    (w/2, proud, h/2), 曾致全对 8.5~85mm 假穿透。全账石旋转均为 0, 旋转
    不为 0 显式 raise(不支持即响亮)。"""
    if any(abs(r) > 1e-12 for r in stone["transform"][3:]):
        raise ValueError("_gap_entry: rotated stone %r not supported"
                         % (stone["id"],))
    verts, faces = world_mesh(stone, statuses)
    _fit, clr_model = EP.fit_for_block(EP._extents_m(verts), G2_SCALE)
    v2 = EP.inset(verts, clr_model)
    t = stone["transform"]
    local = [(v[0] - t[0], v[1] - t[1], v[2] - t[2]) for v in v2]
    return (list(t), (local, faces))


def _stone_xspan(stone):
    # type: (dict) -> tuple
    """世界 x 跨(BS.stone_world_bbox 纯实现, 兼容 bake 族)。"""
    x0, x1, _z0, _z1 = BS.stone_world_bbox(stone)
    return x0, x1


def adjacent_pairs(zone_stones):
    # type: (list) -> list
    """一孔范围内【同工艺相邻缝对】(缝=真缝/隐缝/装配贴合缝, 全部为设计
    贴合对)。跨工艺理想化重叠(core y_extent=full_wall 满墙、链面石起拱段
    压券环径向带)不是"相邻缝", 不入样 —— G2 判缝不判场景链重叠。返回
    排序去重的 [(type, id_a, id_b)]。"""
    rings, imposts, cores = [], [], []
    span = {}       # (role, face, course) -> [stones]
    back_of = {}    # (face, course, block) -> {SPANDREL: s, BACK: s}
    for s in zone_stones:
        toks = s["id"].split(".")
        role, face = toks[2], toks[1]
        course, block = int(toks[3][1:]), int(toks[4][1:])
        if role == "RING":
            rings.append(s)
        elif role == "IMPOST":
            imposts.append(s)
        elif role == "CORE":
            cores.append(s)
        elif role in ("SPANDREL", "BACK"):
            span.setdefault((role, face, course), []).append(s)
            back_of.setdefault((face, course, block), {})[role] = s
        else:
            raise ValueError("adjacent_pairs: unexpected role %r in %s"
                             % (role, s["id"]))
    pairs = set()

    def add(t, a, b):
        pairs.add((t, a, b) if a <= b else (t, b, a))

    def consecutive(stones, tag):
        ss = sorted(stones, key=lambda s: s["id"])
        for a, b in zip(ss, ss[1:]):
            add(tag, a["id"], b["id"])

    consecutive(rings, "ring-ring")
    consecutive(cores, "core-core")
    for key in sorted(span):
        consecutive(span[key], "%s-%s" % (key[0].lower(), key[0].lower()))
    for key in sorted(back_of):
        d = back_of[key]
        if "SPANDREL" in d and "BACK" in d:
            add("spandrel-back", d["SPANDREL"]["id"], d["BACK"]["id"])
    consecutive(sorted(imposts, key=lambda s: s["id"]), "impost-impost")
    # RING 端块 vs 同侧 IMPOST 段: 券脚 x 界贴合(fx=墩中线, JOINT_GAP 缝)
    imp_spans = [(s,) + _stone_xspan(s) for s in imposts]
    for rs in rings:
        rx0, rx1 = _stone_xspan(rs)
        for (s, ix0, ix1) in imp_spans:
            if abs(rx0 - ix1) < 1e-6 or abs(rx1 - ix0) < 1e-6:
                add("ring-impost", rs["id"], s["id"])
    return sorted(pairs)


def _sample_even(items, k):
    # type: (list, int) -> list
    """确定性等距抽样: n<=k 全取; 否则取 k 个等距点(含首尾)。"""
    n = len(items)
    if n <= k:
        return list(items)
    return [items[int(round(i * (n - 1.0) / (k - 1.0)))] for i in range(k)]


def _pair_overlap_depth_mm(entry_a, entry_b):
    # type: (tuple, tuple) -> float
    """两 entry 世界网格 AABB 的最小轴重叠(模型毫米) —— 干涉深度量级记录。"""
    (ta, (va, _fa)) = entry_a
    (tb, (vb, _fb)) = entry_b
    Va = PC._xform(np.asarray(va, dtype=float), ta)
    Vb = PC._xform(np.asarray(vb, dtype=float), tb)
    ov = (np.minimum(Va.max(axis=0), Vb.max(axis=0))
          - np.maximum(Va.min(axis=0), Vb.min(axis=0)))
    return float(min(ov) * 1000.0)


def gap_check_pair(entry_a, entry_b,
                   tol_model_mm=G2_GAP_TOL_MODEL_MM, scale=G2_SCALE):
    # type: (tuple, tuple, float, float) -> tuple
    """两级 gap 判(消费侧组合, printcheck.gap_check 契约零改动):
    ① PC.gap_check(AABB 快筛): 不相交/容差内 -> ok。
    ② AABB 相交时精判: 券环放射缝石的世界 AABB 相交是【径向缝的旋转幻影】
      (缝面沿法向倾斜 ~70°, 轴对齐盒必然互相咬合; W2 契约假定 RING 带
      transform 转角正是为此, 但 ABB 盒判对斜缝天然假阳) —— 复用
      printcheck 的面-面相交判据对两网格逐面对精检: 闭曲面实体相交
      <=> 表面相交; 无面相交 = 幻影重叠(aabb_phantom, ok)。
    ③ 包含型(C2/T8b): 面不相交但任一实体顶点严格入对方体内 = 吞没/包含
      互穿(AABB 必相交、表面永不相交, ②判不了) —— 射线奇偶判
      (_mesh_contains_points), 命中即 PENETRATION, 真实非幻影。
    返回 (report, aabb_phantom, depth_mm)。实相交 -> PENETRATION(缝面相穿
    即不合格, 不设深度容差; 制造间隙由 inset 表达)。depth_mm = 面级精判出
    的真深度(包含顶点最大入体深度, 模型毫米; 无包含顶点的纯棱交叉退化
    0.0 —— 深度记账交给 AABB 最小轴字段), ok 时恒 0.0。"""
    rep = PC.gap_check(entry_a, entry_b, tol_model_mm=tol_model_mm,
                       scale=scale)
    if rep["ok"]:
        return rep, False, 0.0
    (ta, (va, fa)) = entry_a
    (tb, (vb, fb)) = entry_b
    Va = PC._xform(np.asarray(va, dtype=float), ta)
    Vb = PC._xform(np.asarray(vb, dtype=float), tb)
    polys_a = [Va[list(f)] for f in fa]
    polys_b = [Vb[list(f)] for f in fb]
    norm_a = [PC._newell_normal(p) for p in polys_a]
    norm_b = [PC._newell_normal(p) for p in polys_b]
    tris_a = PC._face_tris(Va, fa)
    tris_b = PC._face_tris(Vb, fb)
    lo_a = np.array([p.min(axis=0) for p in polys_a])
    hi_a = np.array([p.max(axis=0) for p in polys_a])
    lo_b = np.array([p.min(axis=0) for p in polys_b])
    hi_b = np.array([p.max(axis=0) for p in polys_b])
    ov = np.all(lo_a[:, None, :] <= hi_b[None, :, :], axis=2) & \
        np.all(hi_a[:, None, :] >= lo_b[None, :, :], axis=2)
    for i, j in zip(*np.nonzero(ov)):
        if _pair_faces_cross(polys_a[i], polys_b[j], norm_a[i], norm_b[j],
                             tris_a[i], tris_b[j]):
            # 交叉对的真深度: 取 A 顶点入 B 体的最大深度(无包含顶点的
            # 纯棱交叉退化为 0.0, 深度记账交给 AABB 字段)
            depth = _containment_depth_mm(Va, _flat_tris(tris_b))
            return {"ok": False,
                    "issues": [{"code": "PENETRATION",
                                "detail": "mesh faces cross (refined), "
                                          "face A#%d x B#%d" % (i, j)}]}, \
                False, depth
    # ③ 包含型: 面不相交但顶点入体(吞没) —— 对称双向
    for (pts, other, label) in ((Va, (Vb, _flat_tris(tris_b)), "A"),
                                (Vb, (Va, _flat_tris(tris_a)), "B")):
        ins = _mesh_contains_points(other[1], pts)
        if ins.any():
            depths = {k: float(_point_tris_distance(pts[k], other[1]))
                      for k in np.nonzero(ins)[0]}
            k = max(depths, key=depths.get)
            return {"ok": False,
                    "issues": [{"code": "PENETRATION",
                                "detail": "containment: vertex %s#%d inside "
                                          "other solid (depth %.3fmm)"
                                          % (label, k, depths[k] * 1000.0)}]}, \
                False, depths[k] * 1000.0
    return {"ok": True, "issues": []}, True, 0.0


def _containment_depth_mm(Va, tris_b):
    # type: (object, object, list) -> float
    """A 的顶点入 B 体的最大深度(模型毫米; 无包含顶点返回 0.0)。"""
    ins = _mesh_contains_points(tris_b, Va)
    if not ins.any():
        return 0.0
    return max(float(_point_tris_distance(Va[k], tris_b))
               for k in np.nonzero(ins)[0]) * 1000.0


def _flat_tris(face_tris):
    # type: (list) -> list
    """PC._face_tris 的 [face -> [(3,3),...]] 摊平成 [(3,3),...]。"""
    return [t for face in face_tris for t in face]


def _mesh_contains_points(tris, pts):
    # type: (object, list, object) -> object
    """闭曲面包含判(射线奇偶, +x 向): 每点射线与网格全部三角求交, 奇数次
    => 点在体内。Möller–Trumbore 逐三角向量化(三角数小、点数大: 三角为
    外层循环, 点分块内层广播)。面上/共棱的点计 0 或 2 次 => 不算入 ——
    接触不是包含(C2 语义)。tris=摊平坐标三角(_flat_tris), pts=(n,3)。"""
    P = np.asarray(pts, dtype=float)
    inside = np.zeros(P.shape[0], dtype=np.int32)
    T = np.asarray(tris, dtype=float)                          # (m,3,3)
    e1 = T[:, 1] - T[:, 0]
    e2 = T[:, 2] - T[:, 0]
    d = np.array([1.0, 0.0, 0.0])
    pvec = np.cross(d, e2)                     # (m,3)
    det = np.einsum("ij,ij->i", e1, pvec)      # (m,)
    ok = np.abs(det) > 1e-14
    if not ok.any():
        return inside.astype(bool)
    inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
    lo = np.min(T.reshape(-1, 3), axis=0)
    hi = np.max(T.reshape(-1, 3), axis=0)
    L = float((hi - lo).max()) + 1.0
    chunk = 200_000
    for c0 in range(0, P.shape[0], chunk):
        Pc = P[c0:c0 + chunk]
        tvec = Pc[:, None, :] - T[None, :, 0, :]               # (n,m,3)
        u = np.einsum("nmk,mk->nm", tvec, pvec) * inv[None, :]
        qvec = np.cross(tvec, e1[None, :, :])
        v = np.einsum("nmk,k->nm", qvec, d) * inv[None, :]
        t = np.einsum("nmk,mk->nm", qvec, e2) * inv[None, :]
        hit = (ok[None, :] & (u >= 0.0) & (v >= 0.0) & (u + v <= 1.0)
               & (t > 1e-12) & (t < L))
        inside[c0:c0 + chunk] = np.count_nonzero(hit, axis=1) % 2
    return inside.astype(bool)


def _point_tris_distance(pt, tris):
    # type: (object, list) -> float
    """点到三角网格表面最小距离(模型米): 投影在三角形内取平面距, 否则取
    三条棱的点到线段距, 逐三角取最小。tris=摊平坐标三角(_flat_tris)。"""
    p = np.asarray(pt, dtype=float)
    T = np.asarray(tris, dtype=float)
    a, b, c = T[:, 0], T[:, 1], T[:, 2]
    ab, ac = b - a, c - a
    n = np.cross(ab, ac)
    nn = np.einsum("ij,ij->i", n, n)
    good = nn > 1e-18
    best = np.inf
    if good.any():
        ap = p - a
        d11 = np.einsum("ij,ij->i", ab, ab)
        d01 = np.einsum("ij,ij->i", ac, ac)
        d20 = np.einsum("ij,ij->i", ab, ap)
        d21 = np.einsum("ij,ij->i", ac, ap)
        d_ba = np.einsum("ij,ij->i", ab, ac)
        den = np.where(good, d11 * d01 - d_ba * d_ba, 1.0)
        v = (d01 * d20 - d11 * d21) / den
        w = (d11 * d21 - d_ba * d20) / den
        inside = good & (v >= 0.0) & (w >= 0.0) & (v + w <= 1.0)
        if inside.any():
            planar = np.abs(np.einsum("ij,ij->i", n, ap)) \
                / np.sqrt(np.maximum(nn, 1e-18))
            best = float(planar[inside].min())
    for (pa, pb) in ((a, b), (b, c), (c, a)):
        seg = pb - pa
        L2 = np.einsum("ij,ij->i", seg, seg)
        tt = np.clip(np.einsum("ij,ij->i", seg, p - pa)
                     / np.where(L2 > 1e-18, L2, 1.0), 0.0, 1.0)
        q = pa + tt[:, None] * seg
        edge = float(np.sqrt((np.einsum("ij,ij->i", q - p, q - p)).min()))
        best = min(best, edge)
    return best


def _pair_faces_cross(pts_i, pts_j, ni, nj, tris_i, tris_j):
    # type: (object, object, object, object, list, list) -> bool
    """两网格面对判(printcheck._face_pair_crosses 的双实体变体):
    非共面 -> 横穿判据同款; 共面 -> 【同向法线】且投影正面积重叠才判交叉 ——
    同向共面正面积重叠 = 两实体在同一平面同一侧滑移互穿(轴对齐盒斜推重叠
    即此型, printcheck._coplanar_faces_intersect 的边界判对边共线滑移漏报);
    反向法线 = 对接缝(A 顶面贴 B 底面), 装配贴合不算。三角化网格逐三角
    S-H 凸裁剪量面积; 非三角面退回边界判。"""
    if float(ni @ ni) <= PC._EPS * PC._EPS or \
            float(nj @ nj) <= PC._EPS * PC._EPS:
        return False
    d = [float((v - pts_i[0]) @ ni) for v in pts_j]
    if all(abs(x) <= PC._EPS for x in d):
        if float(ni @ nj) <= 0.0:
            return False
        if len(pts_i) == 3 and len(pts_j) == 3:
            return _coplanar_tri_overlap(pts_i, pts_j, ni)
        return PC._coplanar_faces_intersect(pts_i, pts_j, ni)
    return any(PC._tris_cross_non_coplanar(a, b)
               for a in tris_i for b in tris_j)


def _coplanar_tri_overlap(pts_i, pts_j, ni):
    # type: (object, object, object) -> bool
    P = PC._project2(pts_i, ni)
    Q = PC._project2(pts_j, ni)
    if _poly_signed_area2(P) < 0.0:
        P = P[::-1]
    if _poly_signed_area2(Q) < 0.0:
        Q = Q[::-1]
    poly = list(P)
    m = len(Q)
    for k in range(m):
        a, b = Q[k], Q[(k + 1) % m]
        out = []
        n = len(poly)
        if n == 0:
            break
        for r in range(n):
            p_cur, p_nxt = poly[r], poly[(r + 1) % n]
            c_cur = (b[0] - a[0]) * (p_cur[1] - a[1]) \
                - (b[1] - a[1]) * (p_cur[0] - a[0])
            c_nxt = (b[0] - a[0]) * (p_nxt[1] - a[1]) \
                - (b[1] - a[1]) * (p_nxt[0] - a[0])
            if c_cur >= 0.0:
                out.append(p_cur)
            if (c_cur > 0.0) != (c_nxt > 0.0):
                tt = c_cur / (c_cur - c_nxt)
                out.append((p_cur[0] + tt * (p_nxt[0] - p_cur[0]),
                            p_cur[1] + tt * (p_nxt[1] - p_cur[1])))
        poly = out
    if len(poly) < 3:
        return False
    return abs(_poly_signed_area2(poly)) > 1e-12


def _poly_signed_area2(poly):
    # type: (list) -> float
    n = len(poly)
    return 0.5 * sum(poly[i][0] * poly[(i + 1) % n][1]
                     - poly[(i + 1) % n][0] * poly[i][1]
                     for i in range(n))


def _issue(code, detail):
    # type: (str, str) -> dict
    return {"code": code, "detail": detail}


# ── T8b-B4: ring↔链 dedup 宇宙 + 体积处置(case_A subsume / case_B trim) ──

RING_DEDUP_ROLES = ("SPANDREL", "BACK", "CORE")
SUBSUME_REL_MAX = 0.01        # case_A: unique_vol <= 1% V(stone)
SUBSUME_ABS_CM3 = 50.0        # case_A: 且 unique_vol <= 50cm3(模型, 绝对地板)
SPANDREL_BACK_DEPTH_MM = 5.0   # D7: spandrel-back 实体相交豁免上界(模型 mm)
SPANDREL_BACK_VOL_CM3 = 100.0  # D7: 相交 AABB 体积上界(模型 cm3)
SPANDREL_BACK_WARN_N = 50      # D7: 豁免数超此值打 WARN


def _zone_rings(led):
    # type: (dict) -> dict
    """{zone: [RING stone, ...]}(按 id 排序, 确定性)。"""
    out = {}
    for s in led["stones"]:
        if s.get("role_struct") == "RING":
            out.setdefault(s["id"].split(".")[0], []).append(s)
    for z in out:
        out[z].sort(key=lambda s: s["id"])
    return out


def _preinset_world(stone, statuses):
    # type: (dict, dict) -> tuple
    """pre-inset 世界网格(处置体素判据用 —— FIT inset 会把配合缝当清道夫,
    用 post-inset 判处置 = 制造余量洗白重影, 审查负控③钉死此项)。"""
    return world_mesh(stone, statuses)


def _prism_stitched(poly, y_front, y_back):
    # type: (list, object, object) -> tuple
    """x-z 简单多边形 -> 沿 y 双剖面棱柱(单一闭合壳): 帽面耳切三角化
    (_triangulate_simple, 非凸安全 —— 券环带切割保留片是 x-单调但可非凸
    的多边形, _prism 的顶点扇形化会产生覆盖/自交三角, T8b 首跑实测
    MULTI_SHELL 475 石即此病)。侧沿每边界边一四边形, 前/背帽逐三角反向,
    水密单壳; 朝向交给 flip_outward 单一归一。"""
    n = len(poly)
    vf = [(x, float(y_front(z)), z) for (x, z) in poly]
    vb = [(x, float(y_back(z)), z) for (x, z) in poly]
    verts = vf + vb
    faces = []
    for (i, j, k) in _triangulate_simple(list(poly)):
        faces.append((i, j, k))
        faces.append((n + k, n + j, n + i))
    for i in range(n):
        j = (i + 1) % n
        faces.append((j, i, n + i, n + j))
    return verts, faces


def _ring_trim_mesh(polys, stone):
    # type: (list, list) -> tuple
    """带裁保留片 -> 世界网格(经 materialize 单一放置算子)。polys 是世界
    x-z; y 剖面(_family_y_profiles)定义在【局部 z(0..h)】上 —— 必须先减
    anchor offset 建局部棱柱, 再 materialize 加回(T8b 复审 [2]: 首版把
    世界 x-z 直喂剖面, 489 块裁片整体 y 错位 3~5m, 红门 216/87 的真因;
    钉死测试 test_ring_trim_world_y_interval)。多 run = 真断开材料, 各自
    闭合壳(MULTI_SHELL 不豁免, 审查裁决: run 升格独立单元留 T9)。"""
    off = M2.anchor_offset(stone["family"], stone["params"],
                           stone["transform"])
    yf, yb = BS._family_y_profiles(stone)
    verts = []     # type: list
    faces = []     # type: list
    for poly in polys:
        lp = [(x - off[0], z - off[2]) for (x, z) in poly]
        pv, pf = _prism_stitched(lp, yf, yb)
        faces.extend(tuple(i + len(verts) for i in fc) for fc in pf)
        verts.extend(pv)
    return M2.materialize(stone, verts, faces)


def _band_trim_polys(stone, arch_idx, rings):
    # type: (dict, int, list) -> tuple
    """case_B print-view 裁剪: 石足印减『洞∪券环带』。减除区间按 x 竖条:
      洞/拱带 |x-xc| < a+GAP_W:            减 z <= zc(x)  (void+band, 单一
      真相 = masonry._hole_cut_polyline 折线, 与贴拱切块同几何);
      承压带 a+GAP_W <= |x-xc| <= a+RING_T+GAP_W:
                                           减 [spz-GAP_W, zc(x)] —— 下界
        是座石面(环端承压于 z=spz, 墙顶 spz-GAP, masonry 同规则): 保留
        座石 z<spz-GAP 与环背上缘 z>zc(x) 两段;
      带外: 不减。
    zc(x) 加【环石 lift 包络】: 各 RING 的 params.lift 是账目单一真相
    (keystone 刚性上提, T8b 首跑漏计 -> 冠环上缘 0.06 高出切割线, 193 对
    残留互穿), bound(x) = zc(x) + max{lift_s: x ∈ station_s}。
    保留域 x-单调; 按 run 断开后每 run 一条简单多边形(底=bound 折线,
    顶=z1), 座石条为矩形, 供 _ring_trim_mesh 耳切成单壳。
    返回 (kept_polys 世界x-z, removed_z_area m^2); kept 空 = 全剔。
    场景层零触碰(statuses/多边形只活在 p1a 打印视图, 主控 1b 裁定)。"""
    x0, x1, z0, z1 = BS.stone_world_bbox(stone)
    pts = _MAS._hole_cut_polyline(arch_idx, x0, x1)
    if pts is None:
        return [], 0.0
    xc, spz, a, _b = _MAS._arch_of(arch_idx)
    gap = _MAS.GAP_W
    t_out = a + _MAS.RING_T + gap          # 减除域外缘(jamb 中心距)
    jamb = a + gap
    px = [p[0] for p in pts]
    pz = [p[1] for p in pts]

    def zc(x):
        # pts 对 x 单调(masonry 保证); 端点外 -> None(不减)
        if x < px[0] - 1e-9 or x > px[-1] + 1e-9:
            return None
        if x <= px[0]:
            return pz[0]
        if x >= px[-1]:
            return pz[-1]
        lo, hi = 0, len(px) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if px[mid] <= x:
                lo = mid
            else:
                hi = mid
        dx = px[hi] - px[lo]
        if abs(dx) < 1e-12:
            return max(pz[lo], pz[hi])     # 陡降段取高者(masonry 同规)
        f = (x - px[lo]) / dx
        return pz[lo] + f * (pz[hi] - pz[lo])

    def lift_at(x):
        # 环 lift 包络: 仅计 station 覆盖 x 的环(账目 params, 单一真相;
        # stations/lift 缺失的合成条目按 0 计 —— 真 ledger 由 make_ring_entry
        # 恒写这两键)
        best = 0.0
        for r in rings:
            p = r["params"]
            st = p.get("stations")
            if st and st[0] - 1e-9 <= x <= st[1] + 1e-9:
                best = max(best, float(p.get("lift", 0.0)))
        return best

    def seat(x):
        # 承压带座石面(z<spz-GAP 为墙); 非承压带 -> None(无座条)
        d = abs(x - xc)
        if jamb <= d <= t_out:
            return spz - gap
        return None

    xs = sorted({x0, x1}
                | {px_ for (px_, _pz) in pts if x0 < px_ < x1}
                | {b for b in (xc - jamb, xc + jamb, xc - t_out, xc + t_out)
                   if x0 < b < x1})
    upper = []       # (sa, sb, bound0, bound1) bound 已钳 [z0, z1]
    seats = []       # (sa, sb, seat_z)
    removed = 0.0
    for sa, sb in zip(xs[:-1], xs[1:]):
        if sb - sa <= 1e-12:
            continue
        zc0, zc1 = zc(sa), zc(sb)
        s0, s1 = seat(sa), seat(sb)
        if zc0 is None and zc1 is None:
            # 竖条与减除域无交(strip 端点均在折线覆盖外) -> 全保留
            continue
        b0 = min(zc0 + lift_at(sa), z1 + 1.0) if zc0 is not None else None
        b1 = min(zc1 + lift_at(sb), z1 + 1.0) if zc1 is not None else None
        # 座石条: 承压带内 z0..spz-GAP 保留(环端下缘从 spz 起, 留 GAP_W 缝)
        if s0 is not None and s1 is not None:
            seat_z = max(s0, s1, z0)
            if seat_z > z0 + 1e-12:
                seats.append((sa, sb, seat_z))
        # 上缘保留: z > zc+lift
        b0 = z0 if b0 is None else b0
        b1 = z0 if b1 is None else b1
        b0c = min(max(b0, z0), z1)
        b1c = min(max(b1, z0), z1)
        if b0c >= z1 - 1e-12 and b1c >= z1 - 1e-12:
            removed += (sb - sa) * (z1 - z0)   # 全在带/洞内
            continue
        upper.append((sa, sb, b0c, b1c))
        kept_h = (z1 - b0c + z1 - b1c) / 2.0
        removed += (sb - sa) * max(0.0, (z1 - z0) - kept_h)
    # run 断分(上缘保留域): 部分切割 strip(一端钳到 z1)是零高捏点 ——
    # 捏点进同一多边形会产生折叠三角(首跑 SELF_INTERSECT 86 处+假 AxB
    # 交叉的根因), 必须以捏点断 run; 断点两侧由相邻 run 各自收边。
    runs = []
    cur = []
    for st in upper:
        sa, sb, r0, r1 = st
        if min(r0, r1) >= z1 - 1e-9:
            if cur:
                runs.append(cur)
                cur = []
            continue
        cur.append(st)
    if cur:
        runs.append(cur)
    kept = []
    for run in runs:
        poly = []
        for (sa, sb, r0, r1) in run:
            if r0 < z1 - 1e-9:
                if not poly or poly[-1][0] < sa - 1e-12:
                    poly.append((sa, r0))
                elif abs(poly[-1][1] - r0) > 1e-12:
                    poly.append((sa, r0))
            if r1 < z1 - 1e-9:
                poly.append((sb, r1))
        if len(poly) < 2:
            continue
        poly.append((poly[-1][0], z1))
        poly.append((poly[0][0], z1))
        # 抽稀: 共线偏差 < 1.5mm 的中间点丢弃(折线 ARC_STEP 密采样产生
        # 大量近共线点 -> 耳切出薄片三角, printcheck eps=1e-9 边界假交叉;
        # 1.5mm << GAP_W=10mm, 不越缝口径)。共线点【跳过】, 不得拖动端点
        # (拖动会让边界穿过保留域, 首版实测自交根因)。
        simp = [poly[0], poly[1]]
        for p in poly[2:-1]:
            a, b = simp[-2], simp[-1]
            area2 = abs((b[0] - a[0]) * (p[1] - a[1])
                        - (b[1] - a[1]) * (p[0] - a[0]))
            seg = math.hypot(b[0] - a[0], b[1] - a[1])
            if seg > 1e-9 and area2 / seg > 1.5e-3:
                simp.append(p)
        simp.append(poly[-1])
        dedup = []
        for p in simp:
            if dedup and abs(dedup[-1][0] - p[0]) < 1e-12 \
                    and abs(dedup[-1][1] - p[1]) < 1e-12:
                continue
            dedup.append(p)
        if len(dedup) >= 3 and abs(_poly_signed_area2(dedup)) > 1e-12:
            kept.append(dedup)
    for (sa, sb, seat_z) in seats:
        kept.append([(sa, z0), (sb, z0), (sb, seat_z), (sa, seat_z)])
    return kept, removed


def _voxel_unique_vol(verts_s, faces_s, ring_meshes):
    # type: (list, list, list) -> tuple
    """同栅格体积吞没度量(审查修坑版): V(stone) 与 V(stone∩RING∪) 在
    【同原点同步长】格上数; step = min(2cm, 最小维/4)(薄片石自适应加密,
    防 step 失配出 ratio>1)。返回 (v_stone_cm3, v_hit_cm3, unique_cm3,
    any_vert_inside)。unique = stone 格数 − hit 格数(同一格集合作差,
    比值恒 <=1)。ring_meshes = [(verts, flat_tris), ...](bbox 已预筛)。"""
    Vs = np.asarray(verts_s, dtype=float)
    lo, hi = Vs.min(axis=0), Vs.max(axis=0)
    step = min(RING_RASTER_CELL, float((hi - lo).min()) / 4.0)
    step = max(step, 1e-4)
    gx = np.arange(math.floor(lo[0] / step) * step + step / 2.0,
                   hi[0] + step, step)
    gy = np.arange(math.floor(lo[1] / step) * step + step / 2.0,
                   hi[1] + step, step)
    gz = np.arange(math.floor(lo[2] / step) * step + step / 2.0,
                   hi[2] + step, step)
    GX, GY, GZ = np.meshgrid(gx, gy, gz, indexing="ij")
    pts = np.stack([GX.ravel(), GY.ravel(), GZ.ravel()], axis=1)
    tris_s = _flat_tris(PC._face_tris(Vs, faces_s))
    in_s = _mesh_contains_points(tris_s, pts)
    n_stone = int(in_s.sum())
    hit = np.zeros(pts.shape[0], dtype=bool)
    any_inside = False
    for (rv, rtris) in ring_meshes:
        R = np.asarray(rv, dtype=float)
        rlo, rhi = R.min(axis=0), R.max(axis=0)
        sel = np.all((pts >= rlo - step) & (pts <= rhi + step), axis=1)
        sel &= ~hit
        if not sel.any():
            continue
        sub = np.nonzero(sel)[0]
        ins = _mesh_contains_points(rtris, pts[sub])
        hit[sub[ins]] = True
        if not any_inside and ins.any():
            # B2 复证: 任一石顶点在任一环体内(case_A 双确认的第二条)
            any_inside = bool(_mesh_contains_points(rtris, Vs).any())
    v_cell = step ** 3 * 1e6   # m^3 -> cm3
    v_stone = n_stone * v_cell
    v_hit = int((in_s & hit).sum()) * v_cell
    return v_stone, v_hit, v_stone - v_hit, any_inside


def _preinset_gap_entry(stone, statuses):
    # type: (dict, dict) -> tuple
    """pre-inset gap entry(处置/复测专用): 与 _gap_entry 同构但不做 inset
    —— FIT 制造余量会把真重影洗成"无接触"(审查负控③), 处置判据与
    final_scope_check 必须吃 pre-inset 几何。"""
    if any(abs(r) > 1e-12 for r in stone["transform"][3:]):
        raise ValueError("_preinset_gap_entry: rotated stone %r not supported"
                         % (stone["id"],))
    verts, faces = world_mesh(stone, statuses)
    t = stone["transform"]
    local = [(v[0] - t[0], v[1] - t[1], v[2] - t[2]) for v in verts]
    return (list(t), (local, faces))


def _ring_dedup_dispositions(led, statuses, scope, buckets, arch_idx_of):
    # type: (dict, dict, list, dict, dict) -> dict
    """ring↔{SPANDREL,BACK,CORE} dedup 宇宙(pre-inset, bbox 预筛+面级精判
    含包含分支)与处置。verdict 语义: PENETRATION 不进 gap_check.fails
    (环↔链不是缝, 是同一材料两种表征), 按体积吞没裁决:
      case_A subsume: unique_vol <= 1%·V(stone) 且 <= 50cm3(模型) 且 B2
                      顶点包含复证 -> 整块出打印集归 ring_band_overlap
                      (理由带 unique_vol), 材料由 RING 全权代表;
      case_B trim:    其余真撞石不丢(丢了在墙上开洞) -> 按 masonry 单一
                      真相折线做 print-view 带裁剪(主控 1b), params 记
                      clipped_by="ring_band"; 裁后薄片落 thin_merge
                      ("trimmed sliver", 诚实归口);
      trim 空片 = 全在带/洞内 -> 同 case_A 归口(理由 trim_empty)。
    裁剪不改变石账目 id/transform, 只改 statuses 多边形(打印视图)。
    返回 ring_dedup 报告节。"""
    rings = _zone_rings(led)
    by_id = {s["id"]: s for s in led["stones"]}
    ring_entries = {}
    for z, rs in rings.items():
        ring_entries[z] = [(r["id"],) + world_mesh(r, statuses) for r in rs]
    ring_vol_cache = {}
    pairs_rep = []
    subsumed, trimmed, trim_sliver = [], [], []
    removed_sub_cm3 = removed_trim_cm3 = 0.0

    def _partner_id(stone):
        # 同位背衬/面石: ARCHxx.<face>.<ROLE>.C<i>.B<j> 的 ROLE 互换
        t = stone["id"].split(".")
        other = "BACK" if t[2] == "SPANDREL" else "SPANDREL"
        return ".".join([t[0], t[1], other, t[3], t[4]])

    def _apply_trim(stone, kept, entry):
        statuses[stone["id"]] = ("ring_trim", kept)
        stone["params"]["clipped"] = True
        stone["params"]["clipped_by"] = "ring_band"
        t_verts, _t_faces = world_mesh(stone, statuses)
        _fit, clr_model = EP.fit_for_block(EP._extents_m(t_verts), G2_SCALE)
        ext = EP._extents_m(EP.inset(t_verts, clr_model))
        min_print_mm = min(ext) * G2_SCALE * 1000.0
        # 薄片双判: ①打印壁 <1.2mm(原判据); ②最小维 < 2×配合余量(复审[3]:
        # 裁片近零厚保留条吃不下自身 FIT inset, 带伤进 check_stone 假报
        # SELF_INTERSECT —— 那是可判定的物理薄片, 诚实归口 thin_merge)
        if (min_print_mm < G2_MIN_WALL_PRINT_MM
                or min(ext) < 2.0 * clr_model / 1000.0):
            entry["trim_sliver"] = True
            entry["sliver_note"] = ("min_ext=%.3fm, clr=%.1fmm(model), "
                                    "min_print=%.3fmm"
                                    % (min(ext), clr_model, min_print_mm))
            trim_sliver.append(stone["id"])
            buckets["thin_merge"].append(stone["id"])
            scope.remove(stone)
        else:
            trimmed.append(stone["id"])

    def _propagate_to_partner(stone, kept, src_entry):
        """case_B 对称传播: 面石/背衬同块位同 x-z 足印, 一侧裁另一侧不裁
        会让 spandrel-back 缝对实体互穿(T8b 二跑 gap 216 fail 根因)。"""
        pid = _partner_id(stone)
        ps = by_id.get(pid)
        if ps is None or ps not in scope:
            return
        if statuses[pid][0] != "out":
            return
        entry2 = {"chain": pid, "rings": list(src_entry["rings"]),
                  "collide_vol_cm3_pre": src_entry["collide_vol_cm3_pre"],
                  "v_stone_cm3": src_entry["v_stone_cm3"],
                  "unique_vol_cm3": src_entry["unique_vol_cm3"],
                  "disposition": "trim_partner",
                  "reason": "same-block partner of %s (seam consistency)"
                            % stone["id"]}
        _apply_trim(ps, [list(p) for p in kept], entry2)
        pairs_rep.append(entry2)
    for s in list(scope):
        if s.get("role_struct") not in RING_DEDUP_ROLES:
            continue
        if statuses[s["id"]][0] != "out":
            continue    # 已被 partner 传播裁剪, 不再单独裁决
        zone = s["id"].split(".")[0]
        x0, x1, z0, z1 = BS.stone_world_bbox(s)
        hits = []
        for (rid, rv, rf) in ring_entries.get(zone, []):
            if rid in ring_vol_cache:
                rx0, rx1, rz0, rz1 = ring_vol_cache[rid]
            else:
                rx0, rx1, rz0, rz1 = BS.stone_world_bbox(by_id[rid])
                ring_vol_cache[rid] = (rx0, rx1, rz0, rz1)
            if x1 <= rx0 or x0 >= rx1 or z1 <= rz0 or z0 >= rz1:
                continue
            rep, _ph, _depth = gap_check_pair(_preinset_gap_entry(s, statuses),
                                              _preinset_gap_entry(by_id[rid],
                                                                  statuses))
            if rep["ok"]:
                continue
            hits.append(rid)
        if not hits:
            continue
        # 真撞: 同栅格体素度量(zone 全部相握环求并, 非单块 max —— 单 max
        # 会低估 collide、误判 case_B, 偏保守方向, 注明不当作精确值)
        verts, faces = _preinset_world(s, statuses)
        ring_meshes = []
        for rid in hits:
            rv, rf = world_mesh(by_id[rid], statuses)
            ring_meshes.append((rv, _flat_tris(PC._face_tris(
                np.asarray(rv, dtype=float), rf))))
        v_stone, v_hit, v_uniq, vert_inside = _voxel_unique_vol(
            verts, faces, ring_meshes)
        uniq_cm3 = v_uniq
        entry = {"chain": s["id"], "rings": hits,
                 "collide_vol_cm3_pre": round(v_hit, 3),
                 "v_stone_cm3": round(v_stone, 3),
                 "unique_vol_cm3": round(uniq_cm3, 3)}
        is_case_a = (uniq_cm3 <= SUBSUME_REL_MAX * v_stone
                     and uniq_cm3 <= SUBSUME_ABS_CM3 and vert_inside)
        if is_case_a:
            entry["disposition"] = "subsume"
            entry["reason"] = ("subsumed by RING (unique_vol=%.3fcm3, "
                               "vert_inside=true)" % uniq_cm3)
            subsumed.append(s["id"])
            buckets["ring_band_overlap"].append(s["id"])
            scope.remove(s)
            removed_sub_cm3 += v_uniq
        else:
            kept, _removed_area = _band_trim_polys(
                s, arch_idx_of[zone], rings.get(zone, []))
            if not kept:
                entry["disposition"] = "trim_empty"
                entry["reason"] = ("band trim kept nothing "
                                   "(fully in void+band; unique=%.3fcm3)"
                                   % uniq_cm3)
                subsumed.append(s["id"])
                buckets["ring_band_overlap"].append(s["id"])
                scope.remove(s)
                removed_sub_cm3 += v_uniq
            else:
                entry["disposition"] = "trim"
                entry["reason"] = ("trimmed to band cut line (masonry "
                                   "polyline; bearing seat kept below "
                                   "spz-GAP; ring lift envelope added)")
                st, _polys = statuses[s["id"]]
                assert st == "out", "trim 只适用于未裁剪石: %s" % s["id"]
                _apply_trim(s, kept, entry)
                _propagate_to_partner(s, kept, entry)
        pairs_rep.append(entry)
    # final_scope_check(独立 3D 复测): 处置后对【最终】scope 全量重测
    # ring↔链(pre-inset 面级精判含包含分支) —— 不从处置计数/桶成员推导。
    n_colliding = 0
    final_pairs = 0
    colliding_pairs = []
    for s in list(scope):
        if s.get("role_struct") not in RING_DEDUP_ROLES:
            continue
        zone = s["id"].split(".")[0]
        x0, x1, z0, z1 = BS.stone_world_bbox(s)
        for (rid, rv, rf) in ring_entries.get(zone, []):
            rx0, rx1, rz0, rz1 = BS.stone_world_bbox(by_id[rid])
            if x1 <= rx0 or x0 >= rx1 or z1 <= rz0 or z0 >= rz1:
                continue
            rep, _ph, _depth = gap_check_pair(
                _preinset_gap_entry(s, statuses),
                _preinset_gap_entry(by_id[rid], statuses))
            final_pairs += 1
            if not rep["ok"]:
                n_colliding += 1
                # 复审[5]: 逐对可审计 —— 带真交集体积(同栅格体素)
                cv, cf = _preinset_world(s, statuses)[0], None
                cv, cf = world_mesh(s, statuses)
                rv2, rf2 = world_mesh(by_id[rid], statuses)
                _vs, v_hit, _u, _vi = _voxel_unique_vol(
                    cv, cf, [(rv2, _flat_tris(PC._face_tris(
                        np.asarray(rv2, dtype=float), rf2)))])
                colliding_pairs.append({"chain": s["id"], "ring": rid,
                                        "depth_mm": round(_depth, 3),
                                        "collide_vol_cm3_pre":
                                            round(v_hit, 3)})
    summary = {"n_pairs_refined": len(pairs_rep),
               "n_subsumed": len(subsumed),
               "n_trimmed": len(trimmed),
               "n_trim_sliver": len(trim_sliver),
               "removed_model_cm3": {"subsumed": round(removed_sub_cm3, 3),
                                     "trimmed": round(removed_trim_cm3, 3)},
               "note": "unique_vol 同栅格度量; 相握环取并集(单块 max 会低"
                       "估 collide, 偏保守, 不作精确值); 处置判据全为 "
                       "pre-inset(post-inset 会把配合缝当清道夫, 审查负"
                       "控③)"}
    # 复审[5]记账洞: B3 面积桶吞没石的材料流此前不可见 —— 对面积桶内
    # 未走 volume 宇宙的吞没石逐块量 unique_vol(石−RING∪), 计入
    # subsumed_by_area_bucket(与 subsumed_by_volume 分列)。
    vol_by_id = {p["chain"]: p for p in pairs_rep}
    area_vol = 0.0
    area_n = 0
    for sid in buckets["ring_band_overlap"]:
        if sid in vol_by_id:
            continue      # volume 宇宙已处置(subsume/trim), 体积已在账
        s = by_id[sid]
        zone = sid.split(".")[0]
        verts, faces = _preinset_world(s, statuses)
        ring_meshes = []
        for (rid, rv, rf) in ring_entries.get(zone, []):
            rx0, rx1, rz0, rz1 = BS.stone_world_bbox(by_id[rid])
            x0, x1, z0, z1 = BS.stone_world_bbox(s)
            if x1 <= rx0 or x0 >= rx1 or z1 <= rz0 or z0 >= rz1:
                continue
            ring_meshes.append((rv, _flat_tris(PC._face_tris(
                np.asarray(rv, dtype=float), rf))))
        if not ring_meshes:
            continue
        _vs, _vh, uniq, _vi = _voxel_unique_vol(verts, faces, ring_meshes)
        area_vol += uniq
        area_n += 1
    summary["removed_model_cm3"]["subsumed_by_area_bucket"] = \
        round(area_vol, 3)
    summary["n_area_bucket_measured"] = area_n
    return {"pairs": pairs_rep, "summary": summary,
            "subsumed_ids": subsumed, "trimmed_ids": trimmed,
            "trim_sliver_ids": trim_sliver,
            "final_scope_check": {
                "n_pairs": final_pairs, "n_colliding": n_colliding,
                "pairs": colliding_pairs,
                "method": "最终 scope 全量 ring↔链 bbox 预筛+面级精判(含包"
                          "含分支)独立复测, 不从处置计数或桶成员推导"}}


def _coverage_audit(led, statuses, buckets, scope, arch_idx_of):
    # type: (dict, dict, dict, list, dict) -> list
    """覆盖率审计(主控第4条): 每排除/裁剪桶被剔材料的 x-z 面积中, 不被
    RING/void/任何 scope 石足印覆盖的部分(cm2)—— n_colliding=0 不足以
    证明墙上没洞, 此量下降才是"洞被补上"的真证据。分母用可打印几何
    (clip/裁片=裁后棱柱); 未覆盖 = own & ~ring & ~void & ~scope。"""
    cell = RING_RASTER_CELL
    raster = _ring_footprint_raster(led)
    scope_cells = {}
    for s in scope:
        zone = s["id"].split(".")[0]
        scope_cells.setdefault(zone, set()).update(
            _stone_silhouette_cells(s, statuses, cell))
    audit = []
    for bname in ("in_void", "void_cut_fragment", "ring_band_overlap",
                  "thin_merge"):
        per_zone = {}
        for sid in buckets[bname]:
            zone = sid.split(".")[0]
            per_zone.setdefault(zone, []).append(sid)
        uncovered = 0
        total = 0
        for zone, sids in sorted(per_zone.items()):
            i = arch_idx_of[zone]
            band = BS.arch_band(i)
            own = set()
            by_id = {s["id"]: s for s in led["stones"]}
            for sid in sids:
                own |= _stone_silhouette_cells(by_id[sid], statuses, cell)
            total += len(own)
            void = _void_cells(band, own, cell)
            unc = (own - raster.get(zone, set()) - void
                   - scope_cells.get(zone, set()))
            uncovered += len(unc)
        audit.append({"bucket": bname, "cells": total,
                      "uncovered_cells": uncovered,
                      "uncovered_cm2": round(uncovered * cell * cell * 1e4,
                                             1)})
    return audit


def _void_cells(band, cells, cell=RING_RASTER_CELL):
    # type: (dict, set, float) -> set
    """格集合中的洞内格(BS.point_in_void 同式同源, 标量判 —— 券腹曲线带
    双心弧+钝化分支, 不做第二套向量化公式)。"""
    out = set()
    for (ix, iz) in cells:
        if BS.point_in_void((ix + 0.5) * cell, (iz + 0.5) * cell, band):
            out.add((ix, iz))
    return out


def _pair_overlap_vol_cm3(entry_a, entry_b):
    # type: (tuple, tuple) -> float
    """两 entry 世界网格 AABB 交叠盒体积(模型 cm3) —— 相交体量的上界,
    只作 D7 豁免界记账, 不当精确相交体积。"""
    (ta, (va, _fa)) = entry_a
    (tb, (vb, _fb)) = entry_b
    Va = PC._xform(np.asarray(va, dtype=float), ta)
    Vb = PC._xform(np.asarray(vb, dtype=float), tb)
    ov = (np.minimum(Va.max(axis=0), Vb.max(axis=0))
          - np.maximum(Va.min(axis=0), Vb.min(axis=0)))
    if not np.all(ov > 0.0):
        return 0.0
    return float(np.prod(ov) * 1e6)


def write_excluded_ids(sc, led, path):
    # type: (dict, dict, str) -> str
    """D6: 排除件全量 id 旁挂(桶->ids 全表, 含 standing 空桶)。审计件
    入库(gitignore 白名单), 报告 excluded[].ids_sample 只是样本, 全表
    以本文件为准。返回路径。"""
    standing = {"carve_p4": [], "abut": []}
    all_buckets = dict(sc["buckets"])
    all_buckets.update({k: v for k, v in standing.items()
                        if k not in all_buckets})
    data = {"meta": {
                "schema": 1,
                "curve_hash": led.get("meta", {}).get("curve_hash"),
                "stones": len(led.get("stones", [])),
                "print_units": len(sc["scope"]),
                "excluded_total": sum(len(v) for v in sc["buckets"].values()),
                "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                             time.gmtime())},
            "buckets": {k: sorted(v) for k, v in sorted(all_buckets.items())}}
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1, sort_keys=True)
    print("EXCLUDED_IDS written", path)
    return path


def run_g2(led, statuses=None, pairs_per_arch=G2_GAP_PAIRS_PER_ARCH):
    # type: (dict, dict, int) -> dict
    """G2 全桥 printcheck(T8b 版): 打印单元划分(print_scope 面积判据) ->
    ring↔链 dedup 宇宙处置(case_A subsume / case_B 带裁剪, 审查裁决:
    PENETRATION 不进缝 fail —— 环↔链是同一材料的两种表征, 按体积吞没
    unique_vol 处置) -> 逐石 post-inset check_stone -> 缝宇宙(同工艺缝
    20/孔抽样 + spandrel-back 全量带界: 实体相交 depth>5mm 或 AABB 交叠
    >100cm3 计 fail, 界内豁免全量记账, 豁免>50 打 WARN) -> ring_dedup
    报告 + final_scope_check(对最终 scope 独立 3D 复测, 不从桶成员推导)
    + 覆盖率审计(被剔材料 x-z 不被 ring/void/scope 覆盖的洞面积)。
    verdict = PASS iff check_stone.n_fail==0 AND gap_check.n_fail==0 AND
    final_scope_check.n_colliding==0。"""
    led = copy.deepcopy(led)     # 处置就地打 params.clipped 标, 不污染 canonical
    if statuses is None:
        statuses = classify_full(led["stones"])
    sc = print_scope(led, statuses)
    scope = sc["scope"]
    buckets = sc["buckets"]
    arch_idx_of = {"ARCH%02d" % (i + 1): i for i in range(G2_N_ARCH)}
    # T8b-B4: 环↔链处置(可变: statuses 多边形/scope/buckets)
    ring_dedup = _ring_dedup_dispositions(led, statuses, scope, buckets,
                                          arch_idx_of)
    scope_ids = {s["id"] for s in scope}
    role_counts = {}
    fit_tiers = {}
    fails = []
    by_zone = {}
    for s in scope:
        role_counts[s["role_struct"]] = role_counts.get(s["role_struct"], 0) + 1
        by_zone.setdefault(s["id"].split(".")[0], []).append(s)
        verts, faces = world_mesh(s, statuses)
        fit, clr_model = EP.fit_for_block(EP._extents_m(verts), G2_SCALE)
        fit_tiers[fit] = fit_tiers.get(fit, 0) + 1
        v2, f2 = EP.flip_outward(EP.inset(verts, clr_model), faces)
        rep = PC.check_stone(v2, f2, scale=G2_SCALE,
                             min_wall_print_mm=G2_MIN_WALL_PRINT_MM)
        if not rep["ok"]:
            fails.append({"id": s["id"], "role": s["role_struct"],
                          "trim": s["params"].get("clipped_by") == "ring_band",
                          "issues": rep["issues"]})
    # fail 矩阵(code x role, 新裁/存量归因 —— 主控 2A: T9 范围输入)
    matrix = {}
    for f in fails:
        for iss in f["issues"]:
            code = iss["code"]
            matrix.setdefault(code, {}).setdefault(f["role"], 0)
            matrix[code][f["role"]] += 1
    # 旧 clip 片存量普查(void_cut_fragment 全量, 同判据; 只记账不入 verdict
    # —— 它们已按 RING 为准排除, 但其几何质量是 T5/T7 追偿的范围输入)
    by_id = {s["id"]: s for s in led["stones"]}
    legacy = {"n": len(buckets["void_cut_fragment"]), "n_fail": 0,
              "matrix": {}}
    for sid in buckets["void_cut_fragment"]:
        s = by_id[sid]
        verts, faces = world_mesh(s, statuses)
        _fit, clr_model = EP.fit_for_block(EP._extents_m(verts), G2_SCALE)
        v2, f2 = EP.flip_outward(EP.inset(verts, clr_model), faces)
        rep = PC.check_stone(v2, f2, scale=G2_SCALE,
                             min_wall_print_mm=G2_MIN_WALL_PRINT_MM)
        if not rep["ok"]:
            legacy["n_fail"] += 1
            for iss in rep["issues"]:
                legacy["matrix"][iss["code"]] = \
                    legacy["matrix"].get(iss["code"], 0) + 1
    gap_fails = []
    assembly_fit = []
    sb_warn = None
    pair_type_counts = {}
    n_phantom = 0
    per_arch = {}
    entries_cache = {}

    def _entry(sid):
        if sid not in entries_cache:
            entries_cache[sid] = _gap_entry(by_id[sid], statuses)
        return entries_cache[sid]

    for zi in range(G2_N_ARCH):
        zone = "ARCH%02d" % (zi + 1)
        cands = [p for p in adjacent_pairs(by_zone.get(zone, []))
                 if p[1] in scope_ids and p[2] in scope_ids]
        seam = [p for p in cands if p[0] != "spandrel-back"]
        sb = [p for p in cands if p[0] == "spandrel-back"]
        sampled = _sample_even(seam, pairs_per_arch)
        n_fail_z = 0
        for (typ, ia, ib) in sampled:
            pair_type_counts[typ] = pair_type_counts.get(typ, 0) + 1
            rep, phantom, _depth = gap_check_pair(_entry(ia), _entry(ib),
                                                  tol_model_mm=G2_GAP_TOL_MODEL_MM,
                                                  scale=G2_SCALE)
            if phantom:
                n_phantom += 1
            if not rep["ok"]:
                n_fail_z += 1
                gap_fails.append({"a": ia, "b": ib, "type": typ,
                                  "issues": rep["issues"]})
        # D7: spandrel-back 全量跑(不再 20/孔抽样), 实体相交带界
        # (复审[4]: AABB 交叠盒体积对同块位面对天然=整截面×taper, 判别力
        # 零 —— 体积腿改用 _voxel_unique_vol 同栅格真实交集体积)
        n_sb_fail_z = 0
        for (_typ, ia, ib) in sb:
            rep, _ph, depth = gap_check_pair(_entry(ia), _entry(ib),
                                             tol_model_mm=G2_GAP_TOL_MODEL_MM,
                                             scale=G2_SCALE)
            if rep["ok"]:
                continue
            aabb = _pair_overlap_depth_mm(_entry(ia), _entry(ib))
            if depth > SPANDREL_BACK_DEPTH_MM:
                vol = None      # 深度腿已判 fail, 体积腿不再量
                exempt = False
            else:
                # 体积腿: 同栅格真实交集体积(AABB 交叠盒对同块位面对无判
                # 别力, 复审[4])
                va_, fa_ = world_mesh(by_id[ia], statuses)
                vb_, fb_ = world_mesh(by_id[ib], statuses)
                _v_stone, v_hit, _u, _vi = _voxel_unique_vol(
                    va_, fa_, [(vb_, _flat_tris(PC._face_tris(
                        np.asarray(vb_, dtype=float), fb_)))])
                vol = v_hit
                exempt = not (vol > SPANDREL_BACK_VOL_CM3)
            assembly_fit.append({
                "a": ia, "b": ib,
                "aabb_min_axis_mm": round(aabb, 3),
                "depth_mm": round(depth, 3),
                "overlap_volume_cm3": (round(vol, 3)
                                       if vol is not None else None),
                "exempt": exempt})
            if not exempt:
                n_sb_fail_z += 1
                gap_fails.append({
                    "a": ia, "b": ib, "type": "spandrel-back-bounds",
                    "issues": [{"code": "PENETRATION",
                                "detail": "spandrel-back 实体相交超豁免界 "
                                          "(depth>%.1fmm 或真实交集体积>"
                                          "%.0fcm3)"
                                          % (SPANDREL_BACK_DEPTH_MM,
                                             SPANDREL_BACK_VOL_CM3)}]})
        n_fail_z += n_sb_fail_z
        exempt_n = sum(1 for e in assembly_fit if e["exempt"])
        if exempt_n > SPANDREL_BACK_WARN_N:
            sb_warn = ("spandrel-back 豁免对 %d > %d(现场修配毛石量偏大, "
                       "复配工时告警)" % (exempt_n, SPANDREL_BACK_WARN_N))
        per_arch[zone] = {"candidates": len(cands), "sampled": len(sampled),
                          "spandrel_back": len(sb), "n_fail": n_fail_z}
    bucket_reasons = {
        "in_void": "场景链洞内理想化石(GN in_void 布局即剔除)=空气, 不印",
        "void_cut_fragment": "切洞裁剪片: 与 RING 真几何带重复建模(实测 "
                             "400+ 件 <6cm 碎片/双壳/自交三角), 打印以 "
                             "RING 为准",
        "ring_band_overlap": "足印(真剪影面积)与 RING 剪影交占比>50% 的吞"
                             "没石 + volume 宇宙 case_A(subsume)石 —— 与 "
                             "RING 双重建模, 打印以 RING 为准(处置明细见 "
                             "gap_check.ring_dedup)",
        "thin_merge": "post-inset 最小打印壁 < 1.2mm 的截顶残层/窄条/带裁"
                      "薄片(trimmed sliver), 谁都不单独印: 与邻层合印",
    }
    excluded = []
    for bname in ("in_void", "void_cut_fragment", "ring_band_overlap",
                  "thin_merge"):
        ids = buckets[bname]
        excluded.append({
            "bucket": bname, "n": len(ids), "reason": bucket_reasons[bname],
            "ids_sample": sorted(ids)[:12],
        })
    # final_scope_check 已在 _ring_dedup_dispositions 内对最终 scope 独立
    # 复测(pre-inset, 不从桶成员推导); run_g2 只消费。
    report = {
        "meta": {"schema": 2, "gate": "G2",
                 "scale": float(G2_SCALE),
                 "scale_denom": int(round(1.0 / G2_SCALE)),
                 "min_wall_print_mm": float(G2_MIN_WALL_PRINT_MM),
                 "gap_tol_model_mm": float(G2_GAP_TOL_MODEL_MM),
                 "gap_pairs_per_arch": int(pairs_per_arch),
                 "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                              time.gmtime()),
                 "ledger_curve_hash": led.get("meta", {}).get("curve_hash"),
                 "volume_caliber": {
                     "statement": "manifest 体积=散度定理逐面求和, 三角化"
                                  "按 triangulate_faces 约定(四边形固定 "
                                  "0-2 对角剖分+>=5边形 x-z 耳切); "
                                  "_voussoir 侧面为翘曲四边形(JOINT_GAP "
                                  "前12.5/后4.0), 两对角约定实测最大体积"
                                  "相对差 6.2e-3 —— 体积数字是【耳切对角"
                                  "约定】口径, 换剖分器有 ~0.6% 级漂移",
                     "hours_basis": "12cm3/h 为 0.4mm 喷嘴 FDM 实心体经验"
                                    "上界, 未扣 infill/支撑/失败重打",
                     "core_overlap": "CORE y_extent=full_wall 与面石有意重"
                                     "叠(牺牲芯建模语义), 不是可加和的净"
                                     "打印料"},
                 "counts": {"stones": len(led["stones"]),
                            "print_units": len(scope),
                            "roles": dict(sorted(role_counts.items())),
                            "ring_total": sum(1 for s in led["stones"]
                                              if s["role_struct"] == "RING"),
                            "impost_total": sum(1 for s in led["stones"]
                                                if s["role_struct"] == "IMPOST")},
                 "scope": {
                     "print_units": len(scope),
                     "excluded": excluded,
                     "identities": "print_units + sum(excluded.n) == "
                                   "meta.counts.stones",
                     "excluded_standing": [
                         {"bucket": "carve_p4",
                          "reason": "CARVE/RAIL/POST/PAVING 等雕件与附属"
                                    "白名单外归 P4(接线清单⑥; 本账无此类"
                                    "石, export_print.MASONRY_ROLES 同口径)"},
                         {"bucket": "abut",
                          "reason": "ABUT 桥台砌体(八字墙/引道)本轮不入账"
                                    "(接线清单⑤)"}],
                     "by_design_overlaps":
                         "场景链条石/背衬/芯与 RING 全深筒券为表现层理想化"
                         "重叠; 打印单元按 print_scope 去重, 缝抽样只取"
                         "打印单元间同工艺缝对; 环↔链真撞由 volume 宇宙"
                         "处置(subsume/带裁剪)"}},
        "check_stone": {"n": len(scope), "n_fail": len(fails),
                        "fails": fails,
                        "fail_matrix": matrix,
                        "legacy_clip_survey": legacy,
                        "fit_tiers": dict(sorted(fit_tiers.items()))},
        "gap_check": {"n_pairs": sum(v["sampled"] for v in per_arch.values()),
                      "n_fail": len(gap_fails), "fails": gap_fails,
                      "n_aabb_phantom": n_phantom,
                      "assembly_fit": {
                          "n": len(assembly_fit),
                          "n_exempt": sum(1 for e in assembly_fit
                                          if e["exempt"]),
                          "warn": sb_warn,
                          "bounds": {"depth_mm": SPANDREL_BACK_DEPTH_MM,
                                     "volume_cm3": SPANDREL_BACK_VOL_CM3},
                          "disposition": "背衬毛石与同位面石实体干涉已根修"
                                         "(T8b-A1 截顶重算 y 锚, 全链恒等"
                                         "式 pen+GAP≡-(|ty|-(hw+proud)) "
                                         "2290 对余量<1e-6mm); 残留实体相"
                                         "交全量记账, 超 5mm/100cm3 界计 "
                                         "fail, 界内豁免=毛石现场修配",
                          "pairs": assembly_fit},
                      "method": "PC.gap_check AABB 快筛; AABB 相交对用 "
                                "printcheck 面-面相交判据精判(径向缝旋转"
                                "幻影不计 fail, 实相交即 PENETRATION); "
                                "spandrel-back 全量(不抽样)",
                      "pair_types": dict(sorted(pair_type_counts.items())),
                      "per_arch": per_arch},
        "ring_dedup": ring_dedup,
        "coverage_audit": _coverage_audit(led, statuses, buckets, scope,
                                          arch_idx_of),
    }
    ok = (report["check_stone"]["n_fail"] == 0
          and report["gap_check"]["n_fail"] == 0
          and ring_dedup["final_scope_check"]["n_colliding"] == 0)
    report["verdict"] = "PASS" if ok else "FAIL"
    return report


def validate_g2_report(rep):
    # type: (dict) -> list
    """报告结构闸门(纯; blender-free 测试复用): 形状/计数一致性/打印单元
    守恒/verdict 推导一致/PASS 时 fail 列表必空/17 孔抽样非空。返回问题
    列表(空=过)。"""
    p = []
    meta = rep.get("meta", {})
    cs = rep.get("check_stone", {})
    gp = rep.get("gap_check", {})
    if meta.get("gate") != "G2":
        p.append("meta.gate != G2")
    if meta.get("scale_denom") != 50:
        p.append("meta.scale_denom != 50")
    for name, sub in (("check_stone", cs), ("gap_check", gp)):
        for k in ("n_fail", "fails"):
            if k not in sub:
                p.append("%s.%s missing" % (name, k))
        if "n_fail" in sub and "fails" in sub and sub["n_fail"] != len(sub["fails"]):
            p.append("%s.n_fail != len(fails)" % name)
    counts = meta.get("counts", {})
    if cs.get("n") != counts.get("print_units"):
        p.append("check_stone.n != meta.counts.print_units")
    if counts.get("ring_total") != 193:
        p.append("counts.ring_total != 193")
    if counts.get("impost_total") != 492:
        p.append("counts.impost_total != 492")
    sc = meta.get("scope", {})
    ex_n = sum(e.get("n", 0) for e in sc.get("excluded", []))
    if sc.get("print_units", -1) + ex_n != counts.get("stones"):
        p.append("scope 守恒失败: print_units+excluded != stones")
    names = [e.get("bucket") for e in sc.get("excluded", [])]
    for need in ("in_void", "void_cut_fragment", "ring_band_overlap",
                 "thin_merge"):
        if need not in names:
            p.append("scope.excluded 缺桶 %s" % need)
    v = rep.get("verdict")
    rd = rep.get("ring_dedup", {})
    if v not in ("PASS", "FAIL"):
        p.append("verdict not PASS/FAIL")
    else:
        expect = ("PASS" if cs.get("n_fail") == 0 and gp.get("n_fail") == 0
                  and rd.get("final_scope_check", {}).get("n_colliding") == 0
                  else "FAIL")
        if v != expect:
            p.append("verdict inconsistent with n_fail")
        if v == "PASS" and (cs.get("fails") or gp.get("fails")):
            p.append("PASS with non-empty fails")
    pa = gp.get("per_arch", {})
    if len(pa) != G2_N_ARCH:
        p.append("gap_check.per_arch != %d zones" % G2_N_ARCH)
    for z, info in sorted(pa.items()):
        if not info.get("sampled"):
            p.append("%s empty gap sample" % z)
    # T8b 新结构: ring_dedup + final_scope_check + assembly_fit 形状
    if "summary" not in rd or "pairs" not in rd:
        p.append("ring_dedup missing summary/pairs")
    fsc = rd.get("final_scope_check", {})
    if "n_colliding" not in fsc:
        p.append("ring_dedup.final_scope_check.n_colliding missing")
    elif v == "PASS" and fsc.get("n_colliding", -1) != 0:
        p.append("PASS with final_scope_check.n_colliding > 0")
    af = gp.get("assembly_fit", {})
    if "n" not in af or "pairs" not in af:
        p.append("gap_check.assembly_fit missing n/pairs")
    else:
        if af["n"] != len(af["pairs"]):
            p.append("assembly_fit.n != len(pairs)")
        for pr in af["pairs"]:
            if "overlap_mm" in pr:
                p.append("assembly_fit 旧字段 overlap_mm 未改名 "
                         "aabb_min_axis_mm")
                break
            if "aabb_min_axis_mm" not in pr or "depth_mm" not in pr:
                p.append("assembly_fit pair 缺 aabb_min_axis_mm/depth_mm")
                break
    if not isinstance(rep.get("coverage_audit"), list) or \
            not rep.get("coverage_audit"):
        p.append("coverage_audit missing")
    if "volume_caliber" not in meta:
        p.append("meta.volume_caliber missing")
    return p


def slice_ledger(led, arch_idx=SLICE_ZONE_IDX, scope_ids=None):
    # type: (dict, int, set) -> dict
    """中央孔切片账目(纯): 该孔 zone 的【打印单元】(print_scope 口径与 G2
    门一致) —— in_void/切洞碎片/带重叠/薄片与全桥同口径排除; 不筛则全收
    (仅测试用)。"""
    zone = "ARCH%02d" % (arch_idx + 1)
    stones = [s for s in led["stones"] if s["id"].split(".")[0] == zone]
    if scope_ids is not None:
        stones = [s for s in stones if s["id"] in scope_ids]
    if not stones:
        raise ValueError("slice_ledger: empty zone %s" % zone)
    meta = dict(led.get("meta", {}))
    meta["slice_zone"] = zone
    return {"meta": meta, "stones": stones}


def _to_bed_mesh_fn(statuses):
    # type: (dict) -> object
    """export_ledger mesh_fn: world_mesh -> 床原点平移(与
    export_print._materialize_to_bed 同口径, 差异仅在 clip/bake 石来源)。"""
    def fn(stone):
        verts, faces = world_mesh(stone, statuses)
        mn = tuple(min(v[i] for v in verts) for i in range(3))
        return ([(v[0] - mn[0], v[1] - mn[1], v[2] - mn[2]) for v in verts],
                faces)
    return fn


def export_slice(led, statuses, out_dir=SLICE_DIR, arch_idx=SLICE_ZONE_IDX,
                 scale=G2_SCALE, scope_ids=None):
    # type: (dict, dict, str, int, float, set) -> dict
    """中央孔试印包(纯): STL+3MF+ledger_print+manifest(FIT 双值/分批/family
    x count x volume)。返回增强后的 manifest dict。"""
    led_s = slice_ledger(led, arch_idx, scope_ids=scope_ids)
    os.makedirs(out_dir, exist_ok=True)
    manifest = EP.export_ledger(led_s, mesh_fn=_to_bed_mesh_fn(statuses),
                                out_dir=out_dir, scale=scale)
    # 切片概览增强(family x count x volume 已有; 补 role 视角与 in-void 弃量)
    zone = "ARCH%02d" % (arch_idx + 1)
    roles = {}
    for s in led_s["stones"]:
        roles[s["role_struct"]] = roles.get(s["role_struct"], 0) + 1
    manifest["slice"] = {
        "zone": zone,
        "arch_idx": int(arch_idx),
        "stones": len(led_s["stones"]),
        "roles": dict(sorted(roles.items())),
        "note": "RING=全深筒券楔(贯通东西); IMPOST=起拱线出挑脚步(东西墙面"
                "各一套); SPANDREL/BACK/CORE=场景链条石/背衬/牺牲芯",
    }
    with open(os.path.join(out_dir, "manifest.json"), "w",
              encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1, sort_keys=True)
    return manifest


# ══ blender 段(账目提取/装配图) ════════════════════════════════════════

def _vert_tuple(v):
    # type: (object) -> tuple
    return (v.co.x, v.co.y, v.co.z)


def _bm_mesh(tb):
    # type: (object) -> tuple
    """临时 bmesh -> (verts, faces): 顶点创建序 + 面顶点索引(同一图元重放,
    不含任何第二套拓扑公式)。"""
    vmap = {}
    verts = []
    for v in tb.verts:
        vmap[v] = len(verts)
        verts.append(_vert_tuple(v))
    faces = [tuple(vmap[v] for v in f.verts) for f in tb.faces]
    return verts, faces


def _assert_same_points(global_pts, per_stone_pts, tag):
    # type: (list, list, str) -> None
    """顶点多重集互证(1e-9 量化): 全局 bmesh == 逐石重放拼接。"""
    key = lambda pts: sorted((round(x, 9), round(y, 9), round(z, 9))
                             for (x, y, z) in pts)  # noqa: E731
    a, b = key(global_pts), key(per_stone_pts)
    assert len(a) == len(b), \
        "%s 互证失败: 顶点数 %d != %d" % (tag, len(a), len(b))
    for i, (pa, pb) in enumerate(zip(a, b)):
        if pa != pb:
            raise AssertionError(
                "%s 互证失败: 第 %d 个顶点漂移 %r vs %r(单一真相被破坏)"
                % (tag, i, pa, pb))


def _masonry_stats():
    # type: () -> dict
    with open(os.path.join(_HERE, "masonry_stats.json"), "r",
              encoding="utf-8") as f:
        return json.load(f)


def build_ring_entries():
    # type: () -> tuple
    """RING 账目(blender): spy 捕获 build_voussoir 逐石参数 -> 同一图元
    masonry._voussoir 逐石重放提取 -> 质心锚烘焙条目。数量/顶点双重互证。"""
    if not _HAS_BLENDER:
        raise RuntimeError("build_ring_entries 需要 blender(bmesh/masonry)")
    captured = []
    orig = _MAS._voussoir

    def _spy(bm, x0, x1, xc, springer, a, b, ring_t, lift=0.0):
        captured.append((x0, x1, xc, springer, a, b, ring_t, lift))
        return orig(bm, x0, x1, xc, springer, a, b, ring_t, lift=lift)

    _MAS._voussoir = _spy
    try:
        bm = _bmesh.new()
        counts = _MAS.build_voussoir(bm, 0.0, _MAS.FACE_DEPTH)
        world = [_vert_tuple(v) for v in bm.verts]
        bm.free()
    finally:
        _MAS._voussoir = orig
    assert abs(_MAS.RING_T - RING_T_REF) < 1e-12, \
        "RING_T 漂移: masonry.RING_T=%r != p1a RING_T_REF=%r" \
        % (_MAS.RING_T, RING_T_REF)
    stats = _masonry_stats()
    assert sum(counts) == stats["voussoir_total"], \
        "RING 数量互证失败: build_voussoir=%d != masonry_stats.voussoir_total=%d" \
        % (sum(counts), stats["voussoir_total"])
    assert list(counts) == list(stats["voussoir_per_arch"]), \
        "RING 逐孔互证失败: %r != %r" % (counts, stats["voussoir_per_arch"])
    assert len(captured) == sum(counts), \
        "RING 捕获数 %d != 券石总数 %d" % (len(captured), sum(counts))
    entries = []
    replay = []
    si = 0
    for ai, n in enumerate(counts):
        for k in range(n):
            (x0, x1, xc, springer, a, b, ring_t, lift) = captured[si]
            si += 1
            tb = _bmesh.new()
            orig(tb, x0, x1, xc, springer, a, b, ring_t, lift=lift)
            sv, sf = _bm_mesh(tb)
            tb.free()
            replay.extend(sv)
            nx0, nz0 = _MAS._arch_normal(x0, xc, springer, a, b)
            nx1, nz1 = _MAS._arch_normal(x1, xc, springer, a, b)
            trace = {"xc": xc, "x0": x0, "x1": x1, "ring_t": ring_t,
                     "lift": lift, "n": n,
                     "ang0": math.degrees(math.atan2(nx0, nz0)),
                     "ang1": math.degrees(math.atan2(nx1, nz1))}
            entries.append(make_ring_entry(ai, k, sv, sf, trace))
    assert len(entries) == stats["voussoir_total"]
    _assert_same_points(world, replay, "RING")
    print("RING_LEDGER n=%d (voussoir_total=%d) OK"
          % (len(entries), stats["voussoir_total"]))
    return entries, {"per_arch": list(counts), "total": int(sum(counts))}


def build_impost_entries():
    # type: () -> tuple
    """IMPOST 账目(blender): spy 捕获 build_impost 逐石 _stone 参数 -> 同一
    图元逐石重放 -> wedge 前脸锚烘焙条目。归孔/数量/顶点三重互证。"""
    if not _HAS_BLENDER:
        raise RuntimeError("build_impost_entries 需要 blender(bmesh/masonry)")
    captured = []
    orig = _MAS._stone

    def _spy(bm, x0, x1, z0, z1, side, bottom=None, top=None,
             proud=_MAS.STONE_PROUD, back=_MAS.STONE_BACK,
             uv_x0=None, uv_z0=None):
        ok = orig(bm, x0, x1, z0, z1, side, bottom=bottom, top=top,
                  proud=proud, back=back, uv_x0=uv_x0, uv_z0=uv_z0)
        captured.append({"ok": bool(ok), "x0": x0, "x1": x1, "z0": z0,
                         "z1": z1, "side": side, "proud": proud,
                         "back": back})
        return ok

    _MAS._stone = _spy
    try:
        bm = _bmesh.new()
        n = _MAS.build_impost(bm)
        world = [_vert_tuple(v) for v in bm.verts]
        bm.free()
    finally:
        _MAS._stone = orig
    stats = _masonry_stats()
    assert n == stats["coursing_regions"]["impost"], \
        "IMPOST 数量互证失败: build_impost=%d != masonry_stats=%d" \
        % (n, stats["coursing_regions"]["impost"])
    placed = [c for c in captured if c["ok"]]
    assert len(placed) == n, "IMPOST 捕获成功数 %d != 返回值 %d" % (len(placed), n)

    def _attribute(cap):
        # -> (arch_idx, sgn, step)。归孔判据 = x 带包含于该孔该侧的 impost 带
        # [min(fx,px_out), max(...)](端点按 ±75 桥界截断; 带内分段边界与 fx
        # 无关, 不能用端点==fx 判) ∧ z1 == hl - (IMPOST_H/STEPS)*step。
        hits = []
        for i in range(G.N_SPAN):
            xc = (G.PIER_X[i] + G.PIER_X[i + 1]) / 2.0
            a = G.SPANS[i] / 2.0
            hl = G.arch_springer_z(i) - _MAS.GAP_W
            for sgn in (-1, 1):
                fx = xc + sgn * a
                if sgn > 0:
                    k = i + 1
                    w_out = G.BRIDGE_ABUT if k == G.N_SPAN else G.pier_w(k)
                    px_out = G.PIER_X[k] + w_out / 2.0
                else:
                    k = i
                    w_out = G.BRIDGE_ABUT if k == 0 else G.pier_w(k)
                    px_out = G.PIER_X[k] - w_out / 2.0
                lo = max(min(fx, px_out), -G.BRIDGE_LEN / 2.0)
                hi = min(max(fx, px_out), G.BRIDGE_LEN / 2.0)
                if cap["x0"] < lo - 1e-6 or cap["x1"] > hi + 1e-6:
                    continue
                step = int(round((hl - cap["z1"])
                                 / (_MAS.IMPOST_H / _MAS.IMPOST_STEPS)))
                if not 0 <= step < _MAS.IMPOST_STEPS:
                    continue
                if abs(hl - _MAS.IMPOST_H * step / _MAS.IMPOST_STEPS
                       - cap["z1"]) > 1e-6:
                    continue
                hits.append((i, sgn, step))
        assert len(hits) == 1, \
            "IMPOST 归孔失败/歧义: cap=%r -> %r" % (cap, hits)
        return hits[0]

    raw = []
    replay = []
    for cap in placed:
        tb = _bmesh.new()
        orig(tb, cap["x0"], cap["x1"], cap["z0"], cap["z1"], cap["side"],
             proud=cap["proud"], back=cap["back"])
        sv, sf = _bm_mesh(tb)
        tb.free()
        replay.extend(sv)
        ai, sgn, step = _attribute(cap)
        face = "EAST" if cap["side"] > 0 else "WEST"
        raw.append({"ai": ai, "sgn": sgn, "step": step, "face": face,
                    "cap": cap, "verts": sv, "faces": sf})
    _assert_same_points(world, replay, "IMPOST")
    # B 编号: 每 (孔, 墙面, 阶) 按 x0 排序(相邻段 B 相邻)
    groups = {}
    for it in raw:
        groups.setdefault((it["ai"], it["face"], it["step"]), []).append(it)
    entries = []
    for key in sorted(groups):
        for seg_idx, it in enumerate(sorted(groups[key],
                                            key=lambda t: t["cap"]["x0"])):
            cap = it["cap"]
            cx = (cap["x0"] + cap["x1"]) / 2.0
            cz = (cap["z0"] + cap["z1"]) / 2.0
            proud_total = cap["proud"]
            ty = (1.0 if it["face"] == "EAST" else -1.0) \
                * (_MAS._hw(cx, cz) + proud_total)
            trace = {"xc": (G.PIER_X[it["ai"]] + G.PIER_X[it["ai"] + 1]) / 2.0,
                     "step": it["step"], "sgn": it["sgn"], "face": it["face"],
                     "x0": cap["x0"], "x1": cap["x1"], "z0": cap["z0"],
                     "z1": cap["z1"], "proud": proud_total,
                     "back": cap["back"],
                     "proj": proud_total - _MAS.STONE_PROUD,
                     "ty_front": ty}
            entries.append(make_impost_entry(it["ai"], seg_idx,
                                             it["verts"], it["faces"], trace))
    assert len(entries) == n
    print("IMPOST_LEDGER n=%d (coursing_regions.impost=%d) OK" % (len(entries), n))
    return entries, {"total": int(n)}


def bridge_ledger_full():
    # type: () -> dict
    """全桥账目合并(接线清单②): 现链(build_scene2.bridge_ledger) + RING +
    IMPOST。validate_ledger 0 错由调用方/本函数断言。"""
    led = BS.bridge_ledger()
    ring, _ring_info = build_ring_entries()
    impost, _imp_info = build_impost_entries()
    led["stones"].extend(ring)
    led["stones"].extend(impost)
    led["meta"]["curve_hash"] = "e30-p1t8-full"
    led["meta"]["ring_total"] = len(ring)
    led["meta"]["impost_total"] = len(impost)
    errs = L.validate_ledger(led)
    assert not errs, "bridge_ledger_full 校验失败: %s" % errs[:5]
    print("LEDGER_FULL stones=%d (chain=%d ring=%d impost=%d)"
          % (len(led["stones"]),
             len(led["stones"]) - len(ring) - len(impost),
             len(ring), len(impost)))
    return led


# ── 装配图(blender 正射侧视 + id 标注) ─────────────────────────────────

_ROLE_RGB = {"RING": (0.92, 0.88, 0.78), "IMPOST": (0.85, 0.72, 0.45),
             "SPANDREL": (0.55, 0.58, 0.62), "BACK": (0.40, 0.43, 0.47),
             "CORE": (0.30, 0.31, 0.33)}


def render_assembly(led_slice, statuses, out_png, res_x=3200):
    # type: (dict, dict, str, int) -> str
    """正射侧视装配图(blender): 每石一对象按 role 着色, RING/IMPOST/西墙面
    石标 id(短标; 全 id 见 manifest.json)。相机 -Y 向 +Y, 桥轴未旋(账目
    坐标系), 与古建测绘正视图同口径。"""
    import bpy
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    stones = led_slice["stones"]
    wv = []      # 全局包围盒
    for s in stones:
        verts, faces = world_mesh(s, statuses)
        me = bpy.data.meshes.new(s["id"])
        me.from_pydata([tuple(v) for v in verts], [],
                       [tuple(f) for f in faces])
        me.validate()
        ob = bpy.data.objects.new(s["id"], me)
        sc.collection.objects.link(ob)
        role = s["role_struct"]
        ob.data.materials.append(_flat_mat(role, _ROLE_RGB.get(role,
                                                               (0.5, 0.5, 0.5))))
        wv.extend(verts)
    xs = [v[0] for v in wv]
    zs = [v[2] for v in wv]
    x0, x1, z0, z1 = min(xs), max(xs), min(zs), max(zs)
    xr, zr = x1 - x0, z1 - z0
    # id 标注: RING/IMPOST 全标, 西墙面(相机侧) SPANDREL 标短号
    for s in stones:
        toks = s["id"].split(".")
        role, face = toks[2], toks[1]
        if role == "RING":
            label, size = "RB%02d" % int(toks[4][1:]), 0.115
        elif role == "IMPOST" and face == "WEST":
            label, size = "IM.%d.%02d" % (int(toks[3][1:]),
                                          int(toks[4][1:])), 0.075
        elif role == "SPANDREL" and face == "WEST":
            label, size = "S%d.%d" % (int(toks[3][1:]), int(toks[4][1:])), 0.05
        else:
            continue
        verts = _stone_world_verts(s, statuses)
        c = _bbox_center(verts)
        y_lab = min(v[1] for v in verts) - 0.02
        _add_text(sc, label, (c[0], y_lab, c[2]), size)
    cd = bpy.data.cameras.new("Ortho")
    cd.type = 'ORTHO'
    cd.ortho_scale = xr * 1.04
    cd.clip_end = 2000.0
    cam = bpy.data.objects.new("Ortho", cd)
    sc.collection.objects.link(cam)
    cam.location = ((x0 + x1) / 2.0, -500.0, (z0 + z1) / 2.0)
    cam.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    sc.camera = cam
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 1
    try:
        cp = bpy.context.preferences.addons['cycles'].preferences
        cp.compute_device_type = 'METAL'
        for dv in cp.devices:
            dv.use = (dv.type == 'METAL')
        sc.cycles.device = 'GPU'
    except Exception:
        sc.cycles.device = 'CPU'
    sc.render.resolution_x = res_x
    sc.render.resolution_y = int(res_x * zr / xr * 1.06)
    sc.render.film_transparent = True
    sc.render.filepath = out_png
    bpy.ops.render.render(write_still=True)
    print("ASSEMBLY_PNG written %s (%dx%d)"
          % (out_png, sc.render.resolution_x, sc.render.resolution_y))
    return out_png


def _stone_world_verts(stone, statuses):
    # type: (dict, dict) -> list
    return world_mesh(stone, statuses)[0]


def _flat_mat(name, rgb):
    # type: (str, tuple) -> object
    import bpy
    m = bpy.data.materials.new("flat_" + name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs[0].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    em.inputs[1].default_value = 1.0
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs[0], out.inputs[0])
    return m


def _add_text(sc, body, loc, size):
    # type: (object, str, tuple, float) -> None
    import bpy
    cu = bpy.data.curves.new("lbl", type='FONT')
    cu.body = body
    cu.size = size
    cu.align_x = 'CENTER'
    cu.align_y = 'CENTER'
    ob = bpy.data.objects.new("lbl_" + body, cu)
    ob.location = loc
    ob.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    sc.collection.objects.link(ob)
    ob.data.materials.append(_flat_mat("label", (0.05, 0.05, 0.05)))


# ── SLICE_NOTES.md ─────────────────────────────────────────────────────

def write_slice_notes(manifest, report, out_dir=SLICE_DIR,
                      arch_idx=SLICE_ZONE_IDX):
    # type: (dict, dict, str, int) -> str
    """切片说明(带实测数): 1:50 口径/体积口径声明/缝打印当量/fit_diagonal
    斜置批/RING 真相弃用件清单/切片器注意。"""
    zone = "ARCH%02d" % (arch_idx + 1)
    overs = [b for b in manifest["batches"] if b.get("oversize")]
    over_ids = [i for b in overs for i in b["stones"]]
    diag_ids = [i for b in manifest["batches"]
                for i in b.get("fit_diagonal", [])]
    fam_lines = []
    for fam, info in sorted(manifest["families"].items()):
        fam_lines.append("| %s | %d | %.2f |" %
                         (fam.split("|")[0] + "(" + fam.split("|")[1][:8] + "…)"
                          if "|" in fam else fam,
                          info["count"], info["volume_cm3"]))
    role_counts = manifest["slice"]["roles"]
    total_cm3 = sum(v["volume_cm3"] for v in manifest["families"].values())
    est_h = total_cm3 / 12.0     # 0.4mm 喷嘴 FDM 经验 12 cm3/h
    rd = report.get("ring_dedup", {})
    rd_pairs = rd.get("pairs", [])
    trim_ids = sorted(p["chain"] for p in rd_pairs
                      if p.get("disposition") == "trim")
    lines = [
        "# %s 中央孔试印包 SLICE_NOTES" % zone,
        "",
        "G2 门产物: 全石流形+壁厚+分批+装配图 (report verdict: %s)"
        % report["verdict"],
        "",
        "## 口径",
        "- 模型比例 1:50 (scale=0.02); 打印件毫米 = 模型米 x 20。",
        "- 床 220x220mm; 贪心货架装箱(manifest.batches), 允许旋转: 90° 归一"
        "+45° 对角斜置(fit_diagonal 非独占批), 真放不下才 oversize 独占。",
        "- 配合缝双值: 每石 clearance_print_mm/clearance_model_mm 见"
        " manifest.stones (FIT 自动分档: 最小维 <0.3m TIGHT / <1.0m NORMAL"
        " / 否则 LOOSE)。",
        "",
        "## 体积口径声明(T8b-E8, 审查点 2/5)",
        "1. manifest 体积 = 散度定理逐面求和, 三角化按 triangulate_faces",
        "   约定(四边形固定 0-2 对角剖分 + ≥5 边形 x-z 耳切)。_voussoir",
        "   侧面是翘曲四边形(JOINT_GAP 前缘 12.5 / 后缘 4.0mm), 体积对剖分",
        "   对角约定敏感: 两对角约定实测最大相对差 6.2e-3 —— 本 manifest",
        "   的 cm3/h 数字是【耳切对角约定】口径, 换剖分器有 ~0.6% 级漂移,",
        "   不是同一数字。",
        "2. 估时 %.1fh 是【实心体上界】(12cm3/h 经验): 未扣 infill/支撑/" % est_h,
        "   失败重打; 实际耗时的唯一权威是切片器实测。",
        "3. CORE 体积与面石【有意重叠】(y_extent=full_wall, 牺牲芯建模语",
        "   义) —— 各族体积不可加和成'净打印料'; 与面石同批时以面石外形",
        "   为准抠芯。",
        "4. 超床件以旋转后判定: 对角斜置(fit_diagonal)非独占批 %d 块: %s"
        % (len(diag_ids), ", ".join(diag_ids[:8]) or "无"),
        "   真超床独占批(oversize) %d 块: %s"
        % (len(over_ids), ", ".join(over_ids[:8]) or "无"),
        "",
        "## 缝的打印当量(模型 mm -> 打印件 mm)",
        "- 券环放射缝 JOINT_GAP 12.5 -> 0.25; 后端 4.0 -> 0.08。",
        "- 砧石真缝 GAP_W 10.0 -> 0.20; 面石-背衬隐缝 BACKING_GAP 2.0 -> 0.04。",
        "- 装配制造间隙 FIT(TIGHT/NORMAL/LOOSE)= 0.15/0.30/0.50 (打印件",
        "  直接尺寸, 非 1:50 换算; 1:50 下历史缝仅 0.04-0.25mm, 打不出,",
        "  故配合靠 clearance 不靠历史缝)。",
        "",
        "## 构成",
        "| 族 | 数量 | 体积 cm3(打印件) |",
        "|---|---|---|",
        ] + fam_lines + [
        "",
        "- 石数: %d (roles: %s)" % (manifest["slice"]["stones"],
                                    json.dumps(role_counts, sort_keys=True)),
        "- 总体积: %.1f cm3(耳切对角约定口径, 实心体上界); 0.4mm 喷嘴 FDM"
        " 经验估时 ~%.1f h。" % (total_cm3, est_h),
        "",
        "## RING 真相弃用/修配件清单(T8b ring_dedup)",
        "- 带 subsume(整块弃, 材料由 RING 代表): %d 块; trim(按 masonry 切"
        "割折线裁短后保留拼装): %d 块; 裁后薄片(thin_merge, 不单独印): %d "
        "块。明细: g2_report.json ring_dedup.pairs(逐块 collide/unique 体"
        "积 pre-inset 口径)。" % (rd.get("summary", {}).get("n_subsumed", 0),
                                  rd.get("summary", {}).get("n_trimmed", 0),
                                  rd.get("summary", {}).get("n_trim_sliver",
                                                            0)),
    ] + (["- trim 修配件 id: " + ", ".join(trim_ids[:12])]
         if trim_ids else []) + [
        "",
        "## 切片器注意",
        "1. 底面平板朝上打印序: 每石以【最大平整面】贴床 —— RING/IMPOST 以",
        "   前脸(y 向大面)朝下, SPANDREL 以层带下缘贴床, CORE 以顶/底大面",
        "   贴床; 悬垂超过 45° 的券腹内弧面加支撑或摆成拱脚两端对称成对印。",
        "2. RING 楔形件放射缝端面薄(端孔 7 块时弦宽大、楔角小), 摆放时让",
        "   内弧朝上避免台阶纹打在券脸上。",
        "3. history 缝 0.2mm 级在 0.4mm 喷嘴下会糊死, 不要试图打缝 —— 缝",
        "   由装配间隙(FIT)表达; 相邻批拼装按 manifest.batch 顺序。",
        "4. 几何已打印视图三角化(triangulate_faces: 四边形对角剖分 + 非凸"
        "   帽面耳切), STL/3MF 全三角面, 无 >3 边形; 顶点未做任何修补,",
        "   与 families 账目逐位同源。",
        "5. 装配图 assembly_ortho.png 为 -Y 正射侧视(账目坐标系未旋桥轴),",
        "   RB<块>=券环块号, IM.<阶>.<段>=西墙起拱脚步, S<层>.<块>=西墙面石;",
        "   全 id -> 文件映射见 manifest.json stones[].stl。",
        "6. 面石-背衬隐缝设计值 2mm(T8b-A1 修复后全链恒等式核验); 若个别",
        "   对仍示实体干涉, 见 g2_report.json gap_check.assembly_fit(全量"
        "   对+真深度), 毛石按面石内缘现场修配。",
        "",
        "## 复现",
        "```",
        "blender -b --python 3d/p1a_slice.py -- --g2",
        "```",
    ]
    path = os.path.join(out_dir, "SLICE_NOTES.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("SLICE_NOTES written", path)
    return path


# ── 入口 ───────────────────────────────────────────────────────────────

def _save_full_ledger(led):
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, FULL_LEDGER_NAME)
    L.save_ledger(led, path)
    print("LEDGER_FULL_SAVED", path)
    return path


def run_gate(do_slice=True):
    # type: (bool) -> dict
    """G2 全链(blender): 建账+互证 -> G2 报告 -> 试印包。
    T8b 2A(主控裁定): verdict FAIL 即 raise、不出包 —— 含已知互穿件的包
    对打印者是陷阱; 交付物=报告+excluded_ids+覆盖率审计+fail 归因矩阵。
    中央孔旧包停在 T8 版, SLICE_NOTES 顶部打"作废"横幅。"""
    led = bridge_ledger_full()
    _save_full_ledger(led)
    statuses = classify_full(led["stones"])
    sc = print_scope(led, statuses)
    scope_ids = {s["id"] for s in sc["scope"]}
    os.makedirs(PRINT_DIR, exist_ok=True)
    report = run_g2(led, statuses)
    rep_path = os.path.join(PRINT_DIR, "g2_report.json")
    with open(rep_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1, sort_keys=True)
    write_excluded_ids(sc, led, os.path.join(PRINT_DIR, "excluded_ids.json"))
    problems = validate_g2_report(report)
    assert not problems, "g2_report 结构闸门失败: %s" % problems
    print("G2_REPORT written %s verdict=%s check_fails=%d gap_fails=%d "
          "ring_colliding=%d"
          % (rep_path, report["verdict"],
             report["check_stone"]["n_fail"], report["gap_check"]["n_fail"],
             report["ring_dedup"]["final_scope_check"]["n_colliding"]))
    if report["verdict"] != "PASS":
        head = (report["check_stone"]["fails"]
                + report["gap_check"]["fails"])[:3]
        notes = os.path.join(SLICE_DIR, "SLICE_NOTES.md")
        if os.path.exists(notes):
            with open(notes, "r", encoding="utf-8") as fh:
                body = fh.read()
            banner = ("> **T8b 门未过(verdict=%s), 本包作废待 T9。**"
                      "红门明细见 out/print/g2_report.json"
                      "(check_stone.fail_matrix / ring_dedup)。\n\n" %
                      report["verdict"])
            if not body.startswith("> **T8b"):
                with open(notes, "w", encoding="utf-8") as fh:
                    fh.write(banner + body)
            print("SLICE_NOTES banner: T8b 门未过, 中央孔包作废待 T9")
        raise RuntimeError("G2 门 FAIL: check=%d gap=%d ring_colliding=%d "
                           "首3: %s"
                           % (report["check_stone"]["n_fail"],
                              report["gap_check"]["n_fail"],
                              report["ring_dedup"]["final_scope_check"]
                              ["n_colliding"], head))
    out = {"ledger": led, "statuses": statuses, "report": report,
           "scope_ids": scope_ids}
    if do_slice:
        manifest = export_slice(led, statuses, scope_ids=scope_ids)
        render_assembly(slice_ledger(led, scope_ids=scope_ids), statuses,
                        os.path.join(SLICE_DIR, "assembly_ortho.png"))
        write_slice_notes(manifest, report)
        out["manifest"] = manifest
    print("G2_VERDICT %s stones=%d ring=%d impost=%d gap_pairs=%d"
          % (report["verdict"], report["meta"]["counts"]["stones"],
             report["meta"]["counts"]["ring_total"],
             report["meta"]["counts"]["impost_total"],
             report["gap_check"]["n_pairs"]))
    return out


def main():
    # type: () -> None
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    flags = set(argv)
    if "--ledger-only" in flags:
        led = bridge_ledger_full()
        _save_full_ledger(led)
        return
    if not flags or "--g2" in flags:
        run_gate(do_slice=True)
        return
    raise SystemExit("p1a_slice: unknown flags %r (use --g2 / --ledger-only)"
                     % (flags,))


if __name__ == "__main__":
    main()
