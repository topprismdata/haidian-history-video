# P1-T5: printcheck 验证器(流形/自交/壁厚@scale/穿透/平面性/多壳/绕向) 单测。合成数据, 不渲桥。
# 修复轮(审查 BLOCK C1-C4/W1-W3/W5-W6/S1/S3): 每条新判据 = 失败测试 + 负控制。
import math
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "3d"))
import printcheck as PC
from families import family_mesh

S50 = 1 / 50.0


def _wedge_params():
    return {"w": 1.0, "h": 0.4, "d": 1.0,
            "proud": 0.006, "back": 0.3, "hw_b": 6.0, "hw_t": 5.9}


def _codes(r):
    return [i["code"] for i in r["issues"]]


def _has(r, code):
    return code in _codes(r)


def _prism(poly, h):
    """2D 多边形(可凹)沿 z 拉伸, 面绕向一致: 底 (0..n-1), 顶逆序, 侧 (k, n+k, n+k2, k2)。"""
    n = len(poly)
    v = [(x, y, 0.0) for (x, y) in poly] + [(x, y, h) for (x, y) in poly]
    f = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    for k in range(n):
        k2 = (k + 1) % n
        f.append((k, n + k, n + k2, k2))
    return v, f


def _l_prism():
    # L 棱柱(凹六边形底), 净厚 0.5m
    return _prism([(0.0, 0.0), (2.0, 0.0), (2.0, 0.5), (0.5, 0.5), (0.5, 1.5), (0.0, 1.5)], 0.5)


def _u_slot():
    # U 槽棱柱(凹八边形底), 净厚 0.5m, 槽宽 1.5m
    return _prism([(0.0, 0.0), (3.0, 0.0), (3.0, 1.5), (2.25, 1.5), (2.25, 0.5),
                   (0.75, 0.5), (0.75, 1.5), (0.0, 1.5)], 0.8)


def _rot_y(verts, deg):
    """绕 Y 轴旋转(度): x' = x c + z s, z' = -x s + z c。"""
    t = math.radians(deg)
    c, s = math.cos(t), math.sin(t)
    return [(x * c + z * s, y, -x * s + z * c) for (x, y, z) in verts]


def _offset_mesh(mesh, dx=0.0, dy=0.0, dz=0.0, idx=0):
    v = [(x + dx, y + dy, z + dz) for (x, y, z) in mesh[0]]
    f = [(i + idx, j + idx, k + idx, l + idx) for (i, j, k, l) in mesh[1]]
    return v, f


# ---------- Step1 brief 逐字测试 ----------

def test_good_wedge_passes():
    v, f = family_mesh("wedge-std", _wedge_params())
    r = PC.check_stone(v, f, scale=S50, min_wall_print_mm=1.2)
    assert r["ok"] and not r["issues"]


def test_open_box_non_manifold():
    v = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]
    f = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5)]   # 缺两面
    r = PC.check_stone(v, f)
    assert _has(r, "NON_MANIFOLD")


def test_thin_wall_at_scale():
    v, f = family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.03})  # 3cm@1:50=0.6mm
    r = PC.check_stone(v, f, scale=S50, min_wall_print_mm=1.2)
    assert _has(r, "THIN_WALL")


def test_penetration():
    a = family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.5})
    r = PC.gap_check(([0, 0, 0, 0, 0, 0], a), ([0.999, 0, 0, 0, 0, 0], a),
                     tol_model_mm=0.5, scale=S50)
    assert _has(r, "PENETRATION")   # 重叠 1mm > tol 0.5mm


# ---------- C2 INVALID_COORD(NaN/Inf 必拒, 不再 ok=True + volume=nan 下流) ----------

def test_nan_coord_rejected():
    v, f = family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.5})
    v = list(v)
    v[3] = (v[3][0], float("nan"), v[3][2])
    r = PC.check_stone(v, f, scale=S50, min_wall_print_mm=1.2)
    assert not r["ok"] and _has(r, "INVALID_COORD")


def test_inf_coord_rejected():
    v, f = family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.5})
    v = list(v)
    v[5] = (v[5][0], v[5][1], float("inf"))
    r = PC.check_stone(v, f, scale=S50, min_wall_print_mm=1.2)
    assert not r["ok"] and _has(r, "INVALID_COORD")


# ---------- C1 NON_PLANAR_FACE(折穿盒 apex 三档) ----------

def test_non_planar_folded_box_reported():
    # 折穿盒: 顶面一角下折 —— 面拓扑流形/自交判据对其沉默, 平面性判据必须报。
    for apex in (-0.5, -0.25, 1e-7):
        v, f = family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.5})
        v = [(x, y, apex if (x == 0.0 and y == 1.0 and z > 0) else z) for (x, y, z) in v]
        r = PC.check_stone(v, f, scale=S50, min_wall_print_mm=1.2)
        assert _has(r, "NON_PLANAR_FACE"), "apex=%r" % apex


def test_planarity_negative_families_and_prisms():
    # 负控: 干净族库 + L 棱柱 + U 槽 全平面(实测 dev=0~1.39e-17) 不误报。
    for v, f in (family_mesh("wedge-std", _wedge_params()),
                 family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.5}),
                 _l_prism(), _u_slot()):
        assert not _has(PC.check_stone(v, f, scale=S50, min_wall_print_mm=1.2), "NON_PLANAR_FACE"), \
            "planarity false-positive on %s" % (f[0][:2],)


# ---------- C3 MULTI_SHELL + DOUBLE_MATERIAL ----------

def test_multi_shell_disjoint_boxes_reported():
    a = family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.5})
    bv, bf = _offset_mesh(a, dx=5.0, idx=8)
    r = PC.check_stone(list(a[0]) + bv, list(a[1]) + bf, scale=S50, min_wall_print_mm=1.2)
    assert _has(r, "MULTI_SHELL")
    assert not _has(r, "SELF_INTERSECT") and not _has(r, "DOUBLE_MATERIAL")


def test_double_material_duplicate_shells_reported():
    # 重合双壳: 体积和 = 2 x bbox -> DOUBLE_MATERIAL(+MULTI_SHELL)。
    a = family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.5})
    bv, bf = _offset_mesh(a, idx=8)   # 同位, 索引独立
    r = PC.check_stone(list(a[0]) + bv, list(a[1]) + bf, scale=S50, min_wall_print_mm=1.2)
    assert _has(r, "DOUBLE_MATERIAL") and _has(r, "MULTI_SHELL")


def test_double_material_flush_interpenetration_reported():
    # 齐平互穿: vol 1.0 > bbox 0.7 (x1.43) -> 必报。
    a = family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.5})
    bv, bf = _offset_mesh(a, dx=0.4, idx=8)
    r = PC.check_stone(list(a[0]) + bv, list(a[1]) + bf, scale=S50, min_wall_print_mm=1.2)
    assert _has(r, "DOUBLE_MATERIAL")


def test_double_material_negative_clean_families():
    # 负控: 干净 slab(体积/bbox=1.00) 与 wedge(0.91) 零假阳。
    for v, f in (family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.5}),
                 family_mesh("wedge-std", _wedge_params())):
        assert not _has(PC.check_stone(v, f, scale=S50, min_wall_print_mm=1.2), "DOUBLE_MATERIAL")


# ---------- C4 NON_ORIENTABLE(有向边一致性) ----------

def test_non_orientable_reversed_face_reported():
    v, f = family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.5})
    f2 = list(f)
    f2[1] = tuple(reversed(f2[1]))   # 单面反绕 -> 该面 4 条有向边与邻面同向
    r = PC.check_stone(v, f2, scale=S50, min_wall_print_mm=1.2)
    assert _has(r, "NON_ORIENTABLE")
    det = next(i for i in r["issues"] if i["code"] == "NON_ORIENTABLE")["detail"]
    assert det.startswith("4 "), det


def test_non_orientable_negative_families_consistent_winding():
    # 负控: 族库全体内翻 = 绕向一致 -> 放行(printcheck 只保证一致, 不强制朝外)。
    for v, f in (family_mesh("wedge-std", _wedge_params()),
                 family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.5}),
                 _l_prism(), _u_slot()):
        assert not _has(PC.check_stone(v, f, scale=S50, min_wall_print_mm=1.2), "NON_ORIENTABLE")


# ---------- 自交 ----------

def test_self_intersect_needle_through_box():
    # 针穿过盒: 两个各自闭合的子网格拼成一 mesh -> 边计数全 2(NON_MANIFOLD 沉默),
    # 但针侧面穿过盒顶/底面 -> 必报 SELF_INTERSECT。
    box = family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.5})
    needle = family_mesh("slab", {"w": 0.08, "d": 0.08, "h": 1.0})
    nv = [(x + 0.46, y + 0.46, z - 0.25) for (x, y, z) in needle[0]]
    nf = [(i + 8, j + 8, k + 8, l + 8) for (i, j, k, l) in needle[1]]
    v = list(box[0]) + nv
    f = list(box[1]) + nf
    r = PC.check_stone(v, f, scale=S50, min_wall_print_mm=1.2)
    assert _has(r, "SELF_INTERSECT")
    assert not _has(r, "NON_MANIFOLD")   # 自交判据独立于流形判据


def test_self_intersect_negative_stacked_contact_not_flagged():
    # 负控制: 两盒共面叠置(面面接触, 顶点不共享)是接触不是穿透, 不得误报。
    lo = family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.5})
    hv, hf = _offset_mesh(lo, dz=0.5, idx=8)
    r = PC.check_stone(list(lo[0]) + hv, list(lo[1]) + hf, scale=S50, min_wall_print_mm=1.2)
    assert not _has(r, "SELF_INTERSECT")


def test_self_intersect_negative_offset_partial_contact():
    # 偏置共面「部分接触」(T 形交界/边界共线): 零体积重叠即接触, 不报自交。
    # 同构型的实体互穿归 gap_check 管(见 test_penetration 的 0.999 偏置)。
    lo = family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.5})
    hv, hf = _offset_mesh(lo, dx=0.2, dz=0.5, idx=8)
    r = PC.check_stone(list(lo[0]) + hv, list(lo[1]) + hf, scale=S50, min_wall_print_mm=1.2)
    assert not _has(r, "SELF_INTERSECT")


def test_self_intersect_coplanar_cross_reported():
    # 共面交叉两三角: 非流形 + 自交同时被抓(证明共面分支有效)。
    v = [(0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (2.0, 2.0, 0.0), (0.0, 2.0, 0.0),
         (1.0, -1.0, 0.0), (3.0, 1.0, 0.0), (1.0, 3.0, 0.0), (-1.0, 1.0, 0.0)]
    f = [(0, 1, 2), (4, 5, 6)]
    r = PC.check_stone(v, f)
    assert _has(r, "SELF_INTERSECT")
    assert _has(r, "NON_MANIFOLD")


def test_coplanar_inner_triangle_reported():
    # 共面包含: 小三角完全落在大三角内部(边界不相交), 仍须报自交。
    v = [(0.0, 0.0, 0.0), (4.0, 0.0, 0.0), (0.0, 4.0, 0.0),
         (1.0, 1.0, 0.0), (2.0, 1.0, 0.0), (1.0, 2.0, 0.0)]
    f = [(0, 1, 2), (3, 4, 5)]
    r = PC.check_stone(v, f)
    assert _has(r, "SELF_INTERSECT")


def test_coplanar_overlap_containment_beyond_index0_reported():
    # W3/Q3: 共面重叠、边界全共线无横穿、严格包含顶点不在 index 0 -> 旧判据(只测 [0])漏报。
    v = [(0.0, 0.0, 0.0), (4.0, 0.0, 0.0), (4.0, 4.0, 0.0), (0.0, 4.0, 0.0),
         (0.0, 0.0, 0.0), (8.0, 0.0, 0.0), (8.0, 6.0, 0.0), (0.0, 6.0, 0.0)]
    f = [(0, 1, 2, 3), (4, 5, 6, 7)]
    r = PC.check_stone(v, f, scale=S50, min_wall_print_mm=1.2)
    assert _has(r, "SELF_INTERSECT")


# ---------- 壁厚边界 ----------

def test_thin_wall_boundary_exactly_at_limit_passes():
    # 0.06m @1:50 = 1.2mm == min_wall -> 判据是严格小于, 不得报。
    v, f = family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.06})
    r = PC.check_stone(v, f, scale=S50, min_wall_print_mm=1.2)
    assert not _has(r, "THIN_WALL")


def test_thin_wall_proxy_rotated_slab_reported():
    # W1: 45° 斜置薄板 —— bbox 代理全轴 >1.2mm 沉默, 方向无关面片对代理必须抓到 0.6mm。
    v, f = family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.03})
    r = PC.check_stone(_rot_y(v, 45.0), f, scale=S50, min_wall_print_mm=1.2)
    det = [i for i in r["issues"] if i["code"] == "THIN_WALL"]
    assert det and all("pair" in i["detail"] for i in det), det


def test_thin_wall_proxy_negative_axis_aligned_and_rotated_thick():
    # 负控: 轴对齐厚件 / 45° 斜置厚件 / 族库厚壁 / L 棱柱 / U 槽 全不误报。
    tv, tf = family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.5})
    assert not _has(PC.check_stone(tv, tf, scale=S50, min_wall_print_mm=1.2), "THIN_WALL")
    assert not _has(PC.check_stone(_rot_y(tv, 45.0), tf, scale=S50, min_wall_print_mm=1.2), "THIN_WALL")
    for v, f in (family_mesh("wedge-std", _wedge_params()), _l_prism(), _u_slot()):
        assert not _has(PC.check_stone(v, f, scale=S50, min_wall_print_mm=1.2), "THIN_WALL")


# ---------- 穿透负控制 ----------

def test_no_penetration_when_touching_or_separated():
    a = family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.5})
    assert PC.gap_check(([0, 0, 0, 0, 0, 0], a), ([1.0, 0, 0, 0, 0, 0], a),
                        tol_model_mm=0.5, scale=S50)["issues"] == []      # 贴合, 重叠 0
    assert PC.gap_check(([0, 0, 0, 0, 0, 0], a), ([1.1, 0, 0, 0, 0, 0], a),
                        tol_model_mm=0.5, scale=S50)["issues"] == []      # 分离


def test_penetration_within_tol_not_flagged():
    # 重叠 0.2mm(model) <= tol 0.5mm -> 数值容差内, 不报。
    a = family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.5})
    r = PC.gap_check(([0, 0, 0, 0, 0, 0], a), ([0.9998, 0, 0, 0, 0, 0], a),
                     tol_model_mm=0.5, scale=S50)
    assert r["issues"] == []


def test_gap_check_rotated_entry_contract():
    # W2: entry 带 ledger 6 元组 transform; 判几何前必须先旋转再 AABB。
    # 长墙 A 沿 y; 横杆 B 本地沿 x, rz=90° 后横穿 A —— 纯 AABB(未旋系)对此=漏判(对照钉死)。
    wall = family_mesh("slab", {"w": 1.0, "d": 4.0, "h": 0.5})   # x∈[0,1], y∈[0,4]
    bar = family_mesh("slab", {"w": 3.0, "d": 1.0, "h": 0.5})    # 本地 x∈[0,3], y∈[0,1]
    hit = PC.gap_check(([0, 0, 0, 0, 0, 0], wall), ([1.05, 0.5, 0, 0, 0, math.pi / 2], bar),
                       tol_model_mm=0.5, scale=S50)
    assert _has(hit, "PENETRATION")   # 旋转后 x∈[0.05,1.05] 横穿墙
    miss = PC.gap_check(([0, 0, 0, 0, 0, 0], wall), ([1.05, 0.5, 0, 0, 0, 0.0], bar),
                        tol_model_mm=0.5, scale=S50)
    assert miss["ok"] and not miss["issues"]   # 同位移不旋转 -> 未旋 AABB 漏判(证明契约有效)
    clear = PC.gap_check(([0, 0, 0, 0, 0, 0], wall), ([3.05, 0.5, 0, 0, 0, math.pi / 2], bar),
                         tol_model_mm=0.5, scale=S50)
    assert clear["ok"] and not clear["issues"]   # 旋转后真分离 -> 干净(无假阳)


# ---------- 坏输入闸门(W5/W6) ----------

def test_degenerate_face_repeated_index_reported():
    v, f = family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.5})
    r = PC.check_stone(v, list(f) + [(0, 1, 1)], scale=S50, min_wall_print_mm=1.2)
    assert _has(r, "DEGENERATE_FACE")


def test_degenerate_face_two_vertex_reported():
    v, f = family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.5})
    r = PC.check_stone(v, list(f) + [(0, 1)], scale=S50, min_wall_print_mm=1.2)
    assert _has(r, "DEGENERATE_FACE")


def test_degenerate_mixed_does_not_crash_other_checks():
    # 退化面不参与拓扑/几何判据计数, 但其余检查照常跑, 不崩。
    v, f = family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.5})
    r = PC.check_stone(v, list(f) + [(0, 1, 1)], scale=S50, min_wall_print_mm=1.2)
    assert _has(r, "DEGENERATE_FACE")
    assert not _has(r, "MULTI_SHELL") and not _has(r, "SELF_INTERSECT")


def test_face_index_out_of_range_gated():
    v, f = family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.5})
    f = list(f)
    f[2] = (0, 1, 2, 99)
    r = PC.check_stone(v, f, scale=S50, min_wall_print_mm=1.2)   # 不得 IndexError
    assert not r["ok"] and _has(r, "FACE_INDEX_OUT_OF_RANGE")


def test_empty_mesh_reported():
    r = PC.check_stone([], [], scale=S50, min_wall_print_mm=1.2)
    assert not r["ok"] and _has(r, "EMPTY_MESH") and r["volume_m3"] == 0.0
    v, f = family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.5})
    r = PC.check_stone(v, [], scale=S50, min_wall_print_mm=1.2)
    assert _has(r, "EMPTY_MESH")


# ---------- 决策1: scale 域校验 + 关键字改名 ----------

def test_scale_domain_rejected():
    v, f = family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.5})
    for bad in (0.0, -1.0, 50.0):   # scale=0 旧实现崩在 1/scale; scale=50 永不触发 THIN_WALL
        for call in (lambda: PC.check_stone(v, f, scale=bad, min_wall_print_mm=1.2),
                     lambda: PC.gap_check(([0, 0, 0, 0, 0, 0], (v, f)),
                                          ([1, 0, 0, 0, 0, 0], (v, f)),
                                          tol_model_mm=0.5, scale=bad)):
            try:
                call()
                assert False, "scale=%r must raise ValueError" % (bad,)
            except ValueError:
                pass
    assert PC.check_stone(v, f, scale=1.0, min_wall_print_mm=1.2)["ok"]   # 边界 scale=1 合法


# ---------- S1 返回形状(JSON 报告契约) ----------

def test_issue_shape_is_structured_code_detail():
    v, f = family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.03})
    r = PC.check_stone(v, f, scale=S50, min_wall_print_mm=1.2)
    assert r["issues"] and all(set(i.keys()) == {"code", "detail"} for i in r["issues"])
    g = PC.gap_check(([0, 0, 0, 0, 0, 0], (v, f)), ([0.999, 0, 0, 0, 0, 0], (v, f)),
                     tol_model_mm=0.5, scale=S50)
    assert set(g.keys()) == {"ok", "issues"}
    assert g["issues"] and set(g["issues"][0].keys()) == {"code", "detail"}
    assert g["issues"][0]["code"] == "PENETRATION"


# ---------- S3 时序契约(docstring 写死) ----------

def test_timing_contract_documented():
    # 必须对导出前最终 post-inset 几何调用(inset 再吃 2x clearance, 跑前检查=放行薄件)。
    assert "post-inset" in (PC.check_stone.__doc__ or "")


# ---------- 体积(文件职责表含体积) ----------

def test_volume_matches_box():
    v, f = family_mesh("slab", {"w": 2.0, "d": 1.0, "h": 0.5})
    assert abs(PC.volume(v, f) - 1.0) < 1e-9
