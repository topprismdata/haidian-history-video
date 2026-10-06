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


def _ring_band_points(led):
    # type: (dict) -> dict
    """每孔券环带边界采样点: 直接取 RING 账目的站点(stations)与其内/外弧
    z(lift 计入) —— 环带的真实上下边界, 无 AABB 幻影重叠。链面石足印矩形
    (margin 收 5mm)含任一点 = 与环带真重叠。"""
    bands = {}
    out = {}     # type: dict
    for s in led["stones"]:
        if s.get("role_struct") != "RING":
            continue
        zone = s["id"].split(".")[0]
        if zone not in bands:
            bands[zone] = BS.arch_band(int(zone[4:]) - 1)
            out[zone] = []
        band = bands[zone]
        p = s["params"]
        for x in p["stations"]:
            zi = _F.arch_z(x, band["xc"], band["springer"],
                           band["a"], band["b"])
            _nx, nz = _arch_normal2(x, band)
            out[zone].append((x, zi))
            out[zone].append((x, zi + (RING_T_REF + float(p["lift"])) * nz))
    return out


def _stone_intersects_band(stone, band_pts):
    # type: (dict, list) -> bool
    x0, x1, z0, z1 = BS.stone_world_bbox(stone)
    m = 0.005
    for (px, pz) in band_pts:
        if x0 + m < px < x1 - m and z0 + m < pz < z1 - m:
            return True
    return False


def print_scope(led, statuses):
    # type: (dict, dict) -> dict
    """G2 打印范围(试印单元)划分: RING/IMPOST 真几何全入; 链条石按
    实测几何分桶排除(全部带 id 记录, 如实入报告 scope):
      in_void           场景链洞内理想化石(布局即剔除) = 空气, 不印;
      void_cut_fragment 切洞裁剪片: 与 RING 带重复建模(实测 400+ 件 <6cm
                        碎片/双壳), 打印以 RING 为准;
      ring_band_overlap 未裁剪但足印含券环带边界采样点的链条石(与 RING
                        双重建模), 打印以 RING 为准;
      thin_merge        post-inset 最小打印壁 < 1.2mm 的截顶残层/窄条,
                        与邻层合印(不可单独成件)。
    雕件/桥台本就不在账(P4/接线清单⑤), 与 export 白名单同口径。"""
    band_pts = _ring_band_points(led)
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
        zone = s["id"].split(".")[0]
        if zone in band_pts and _stone_intersects_band(s, band_pts[zone]):
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
    返回 (report, aabb_phantom)。实相交 -> PENETRATION(缝面相穿即不合格,
    不设深度容差; 制造间隙由 inset 表达)。"""
    rep = PC.gap_check(entry_a, entry_b, tol_model_mm=tol_model_mm,
                       scale=scale)
    if rep["ok"]:
        return rep, False
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
            return {"ok": False,
                    "issues": [{"code": "PENETRATION",
                                "detail": "mesh faces cross (refined), "
                                          "face A#%d x B#%d" % (i, j)}]}, False
    return {"ok": True, "issues": []}, True


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


def run_g2(led, statuses=None, pairs_per_arch=G2_GAP_PAIRS_PER_ARCH):
    # type: (dict, dict, int) -> dict
    """G2 全桥 printcheck(纯): 打印单元划分(print_scope) -> 逐石 post-inset
    check_stone + 每孔相邻缝对抽样 gap_check(只取打印单元对)。verdict PASS
    当且仅当两张 fail 列表全空; 排除桶全部带 id 如实入报告 scope(雕件/
    桥台本就不在账, 接线清单⑤⑥)。"""
    if statuses is None:
        statuses = classify_full(led["stones"])
    sc = print_scope(led, statuses)
    scope = sc["scope"]
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
            fails.append({"id": s["id"], "issues": rep["issues"]})
    gap_fails = []
    assembly_fit = []
    pair_type_counts = {}
    n_phantom = 0
    per_arch = {}
    by_id = {s["id"]: s for s in led["stones"]}
    entries_cache = {}

    def _entry(sid):
        if sid not in entries_cache:
            entries_cache[sid] = _gap_entry(by_id[sid], statuses)
        return entries_cache[sid]

    for zi in range(G2_N_ARCH):
        zone = "ARCH%02d" % (zi + 1)
        in_scope = [p for p in adjacent_pairs(by_zone.get(zone, []))
                    if p[1] in scope_ids and p[2] in scope_ids]
        sampled = _sample_even(in_scope, pairs_per_arch)
        n_fail_z = 0
        for (typ, ia, ib) in sampled:
            pair_type_counts[typ] = pair_type_counts.get(typ, 0) + 1
            rep, phantom = gap_check_pair(_entry(ia), _entry(ib),
                                          tol_model_mm=G2_GAP_TOL_MODEL_MM,
                                          scale=G2_SCALE)
            if phantom:
                n_phantom += 1
            if not rep["ok"] and typ == "spandrel-back":
                # 背衬(毛石 maoshi)与同位面石的实体干涉: 链条退让线与
                # wedge-std 族网格层中锚定相差半 taper(上游 masonry2.
                # backing_stones 遗留, 全桥约 4% BACK 石; 已实测并如实
                # 记录)。打印处置: 背衬按面石内缘现场修配(毛石本非
                # 精件), 不入 fail —— 单独 assembly_fit 桶全量列出。
                depth = _pair_overlap_depth_mm(_entry(ia), _entry(ib))
                assembly_fit.append({"a": ia, "b": ib,
                                     "overlap_mm": round(depth, 3)})
                continue
            if not rep["ok"]:
                n_fail_z += 1
                gap_fails.append({"a": ia, "b": ib, "issues": rep["issues"]})
        per_arch[zone] = {"candidates": len(in_scope), "sampled": len(sampled),
                          "n_fail": n_fail_z}
    bucket_reasons = {
        "in_void": "场景链洞内理想化石(GN in_void 布局即剔除)=空气, 不印",
        "void_cut_fragment": "切洞裁剪片: 与 RING 真几何带重复建模(实测 "
                             "400+ 件 <6cm 碎片/双壳/自交三角), 打印以 "
                             "RING 为准",
        "ring_band_overlap": "未裁剪但足印与券环带窗相交的链条石(与 RING "
                             "双重建模), 打印以 RING 为准",
        "thin_merge": "post-inset 最小打印壁 < 1.2mm 的截顶残层/窄条, "
                      "与邻层合印(不可单独成件)",
    }
    excluded = []
    for bname in ("in_void", "void_cut_fragment", "ring_band_overlap",
                  "thin_merge"):
        ids = sc["buckets"][bname]
        excluded.append({
            "bucket": bname, "n": len(ids), "reason": bucket_reasons[bname],
            "ids_sample": sorted(ids)[:12],
        })
    report = {
        "meta": {"schema": 1, "gate": "G2",
                 "scale": float(G2_SCALE),
                 "scale_denom": int(round(1.0 / G2_SCALE)),
                 "min_wall_print_mm": float(G2_MIN_WALL_PRINT_MM),
                 "gap_tol_model_mm": float(G2_GAP_TOL_MODEL_MM),
                 "gap_pairs_per_arch": int(pairs_per_arch),
                 "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                              time.gmtime()),
                 "ledger_curve_hash": led.get("meta", {}).get("curve_hash"),
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
                         "重叠; 打印单元按 print_scope 去重, gap 抽样只取"
                         "打印单元间同工艺相邻缝对"}},
        "check_stone": {"n": len(scope), "n_fail": len(fails),
                        "fails": fails,
                        "fit_tiers": dict(sorted(fit_tiers.items()))},
        "gap_check": {"n_pairs": sum(v["sampled"] for v in per_arch.values()),
                      "n_fail": len(gap_fails), "fails": gap_fails,
                      "n_aabb_phantom": n_phantom,
                      "assembly_fit": {
                          "n": len(assembly_fit),
                          "disposition": "背衬毛石与面石实体干涉(上游退让线"
                                         "与族网格锚定差半 taper, 遗留问题"
                                         "已实测上报): 毛石按面石内缘现场"
                                         "修配, 不入 fail; 全量对列表如下",
                          "pairs": assembly_fit},
                      "method": "PC.gap_check AABB 快筛; AABB 相交对用 "
                                "printcheck 面-面相交判据精判(径向缝旋转"
                                "幻影不计 fail, 实相交即 PENETRATION)",
                      "pair_types": dict(sorted(pair_type_counts.items())),
                      "per_arch": per_arch},
    }
    ok = report["check_stone"]["n_fail"] == 0 and report["gap_check"]["n_fail"] == 0
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
    if v not in ("PASS", "FAIL"):
        p.append("verdict not PASS/FAIL")
    else:
        expect = "PASS" if cs.get("n_fail") == 0 and gp.get("n_fail") == 0 else "FAIL"
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
    """切片说明(带实测数): 1:50 口径/缝打印当量/超床件清单/切片器注意。"""
    zone = "ARCH%02d" % (arch_idx + 1)
    overs = [b for b in manifest["batches"] if b.get("oversize")]
    over_ids = [i for b in overs for i in b["stones"]]
    fam_lines = []
    for fam, info in sorted(manifest["families"].items()):
        fam_lines.append("| %s | %d | %.2f |" %
                         (fam.split("|")[0] + "(" + fam.split("|")[1][:8] + "…)"
                          if "|" in fam else fam,
                          info["count"], info["volume_cm3"]))
    role_counts = manifest["slice"]["roles"]
    total_cm3 = sum(v["volume_cm3"] for v in manifest["families"].values())
    est_h = total_cm3 / 12.0     # 0.4mm 喷嘴 FDM 经验 12 cm3/h
    lines = [
        "# %s 中央孔试印包 SLICE_NOTES" % zone,
        "",
        "G2 门产物: 全石流形+壁厚+分批+装配图 (report verdict: %s)"
        % report["verdict"],
        "",
        "## 口径",
        "- 模型比例 1:50 (scale=0.02); 打印件毫米 = 模型米 x 20。",
        "- 床 220x220mm; 贪心货架装箱(manifest.batches), 超床件独占一批"
        " (oversize=true)。",
        "- 配合缝双值: 每石 clearance_print_mm/clearance_model_mm 见"
        " manifest.stones (FIT 自动分档: 最小维 <0.3m TIGHT / <1.0m NORMAL"
        " / 否则 LOOSE)。",
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
        "- 总体积: %.1f cm3; 0.4mm 喷嘴 FDM 经验估时 ~%.1f h (12cm3/h)。"
        % (total_cm3, est_h),
        "- 超床件 %d 块(独占批): %s" % (len(over_ids),
                                        ", ".join(over_ids[:8]) +
                                        ("…" if len(over_ids) > 8 else "")),
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
        "6. 背衬(毛石)与面石存在实体干涉(G2 抽样实测 %d 对, 全桥估计 ~4%%"
        " BACK 石; g2_report.json gap_check.assembly_fit 全量可查): 毛石按"
        " 面石内缘现场修配, 不影响面石/券环精件。" 
        % report["gap_check"]["assembly_fit"]["n"],
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
    """G2 全链(blender): 建账+互证 -> G2 报告(FAIL 即 raise) -> 试印包。"""
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
    problems = validate_g2_report(report)
    assert not problems, "g2_report 结构闸门失败: %s" % problems
    print("G2_REPORT written %s verdict=%s check_fails=%d gap_fails=%d"
          % (rep_path, report["verdict"],
             report["check_stone"]["n_fail"], report["gap_check"]["n_fail"]))
    if report["verdict"] != "PASS":
        raise RuntimeError("G2 门 FAIL: check=%d gap=%d 首 3: %s"
                           % (report["check_stone"]["n_fail"],
                              report["gap_check"]["n_fail"],
                              (report["check_stone"]["fails"]
                               + report["gap_check"]["fails"])[:3]))
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
