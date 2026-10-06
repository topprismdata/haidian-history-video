# e30_shikongqiao_video/tests/test_p1_printcheck.py
# P1-T5: printcheck 验证器(流形/自交/壁厚@scale/穿透) 单测。合成数据, 不渲桥。
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "3d"))
import printcheck as PC
from families import family_mesh

S50 = 1 / 50.0


def _wedge_params():
    return {"w": 1.0, "h": 0.4, "d": 1.0,
            "proud": 0.006, "back": 0.3, "hw_b": 6.0, "hw_t": 5.9}


# ---------- Step1 brief 逐字测试 ----------

def test_good_wedge_passes():
    v, f = family_mesh("wedge-std", _wedge_params())
    r = PC.check_stone(v, f, scale=S50, min_wall_mm=1.2)
    assert r["ok"] and not r["issues"]


def test_open_box_non_manifold():
    v = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]
    f = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5)]   # 缺两面
    r = PC.check_stone(v, f)
    assert any("NON_MANIFOLD" in i for i in r["issues"])


def test_thin_wall_at_scale():
    v, f = family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.03})  # 3cm@1:50=0.6mm
    r = PC.check_stone(v, f, scale=S50, min_wall_mm=1.2)
    assert any("THIN_WALL" in i for i in r["issues"])


def test_penetration():
    a = family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.5})
    r = PC.gap_check([(0, 0, 0), a], [(0.999, 0, 0), a], tol_mm=0.5, scale=S50)
    assert any("PENETRATION" in i for i in r)   # 重叠 1mm > tol 0.5mm


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
    r = PC.check_stone(v, f, scale=S50, min_wall_mm=1.2)
    assert any("SELF_INTERSECT" in i for i in r["issues"])
    assert not any("NON_MANIFOLD" in i for i in r["issues"])  # 自交判据独立于流形判据


def test_self_intersect_negative_stacked_contact_not_flagged():
    # 负控制: 两盒共面叠置(面面接触, 顶点不共享)是接触不是穿透, 不得误报。
    lo = family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.5})
    hi = family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.5})
    hv = [(x, y, z + 0.5) for (x, y, z) in hi[0]]
    hf = [(i + 8, j + 8, k + 8, l + 8) for (i, j, k, l) in hi[1]]
    r = PC.check_stone(list(lo[0]) + hv, list(lo[1]) + hf, scale=S50, min_wall_mm=1.2)
    assert not any("SELF_INTERSECT" in i for i in r["issues"])


def test_self_intersect_negative_offset_partial_contact():
    # 偏置共面「部分接触」(T 形交界/边界共线): 零体积重叠即接触, 不报自交。
    # 同构型的实体互穿归 gap_check 管(见 test_penetration 的 0.999 偏置)。
    lo = family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.5})
    hi = family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.5})
    hv = [(x + 0.2, y, z + 0.5) for (x, y, z) in hi[0]]
    hf = [(i + 8, j + 8, k + 8, l + 8) for (i, j, k, l) in hi[1]]
    r = PC.check_stone(list(lo[0]) + hv, list(lo[1]) + hf, scale=S50, min_wall_mm=1.2)
    assert not any("SELF_INTERSECT" in i for i in r["issues"])


def test_self_intersect_coplanar_cross_reported():
    # 共面交叉两三角: 非流形 + 自交同时被抓(证明共面分支有效)。
    v = [(0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (2.0, 2.0, 0.0), (0.0, 2.0, 0.0),
         (1.0, -1.0, 0.0), (3.0, 1.0, 0.0), (1.0, 3.0, 0.0), (-1.0, 1.0, 0.0)]
    f = [(0, 1, 2), (4, 5, 6)]
    r = PC.check_stone(v, f)
    assert any("SELF_INTERSECT" in i for i in r["issues"])
    assert any("NON_MANIFOLD" in i for i in r["issues"])


def test_coplanar_inner_triangle_reported():
    # 共面包含: 小三角完全落在大三角内部(边界不相交), 仍须报自交。
    v = [(0.0, 0.0, 0.0), (4.0, 0.0, 0.0), (0.0, 4.0, 0.0),
         (1.0, 1.0, 0.0), (2.0, 1.0, 0.0), (1.0, 2.0, 0.0)]
    f = [(0, 1, 2), (3, 4, 5)]
    r = PC.check_stone(v, f)
    assert any("SELF_INTERSECT" in i for i in r["issues"])


# ---------- 壁厚边界 ----------

def test_thin_wall_boundary_exactly_at_limit_passes():
    # 0.06m @1:50 = 1.2mm == min_wall -> 判据是严格小于, 不得报。
    v, f = family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.06})
    r = PC.check_stone(v, f, scale=S50, min_wall_mm=1.2)
    assert not any("THIN_WALL" in i for i in r["issues"])


# ---------- 穿透负控制 ----------

def test_no_penetration_when_touching_or_separated():
    a = family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.5})
    assert PC.gap_check([(0, 0, 0), a], [(1.0, 0, 0), a], tol_mm=0.5, scale=S50) == []      # 贴合, 重叠 0
    assert PC.gap_check([(0, 0, 0), a], [(1.1, 0, 0), a], tol_mm=0.5, scale=S50) == []      # 分离


def test_penetration_within_tol_not_flagged():
    # 重叠 0.2mm(model) <= tol 0.5mm -> 数值容差内, 不报。
    a = family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.5})
    r = PC.gap_check([(0, 0, 0), a], [(0.9998, 0, 0), a], tol_mm=0.5, scale=S50)
    assert r == []


# ---------- 体积(文件职责表含体积) ----------

def test_volume_matches_box():
    v, f = family_mesh("slab", {"w": 2.0, "d": 1.0, "h": 0.5})
    assert abs(PC.volume(v, f) - 1.0) < 1e-9
