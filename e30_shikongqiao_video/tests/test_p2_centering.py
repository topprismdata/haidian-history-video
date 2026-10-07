# -*- coding: utf-8 -*-
"""P2-T2 centering.py 券架生成器测试(blender-free)。

判据承 p2-task-2-brief Step1 + 主控补充设计:
  中央孔 span 8.5 → 柱排数=8; 每 part 闭合六面体(8 顶点 6 quad, 12 边各属 2 面);
  rib 板上缘 ∈ [extrados+0.03−tol, extrados+0.06]; wedge_events=柱头对数>0;
  footprint_polys 覆盖孔跨×环带区(面积>0); 端孔柱排数<中央 且 柱顶 z ≤ crown+ring_t+0.1。
拱形数学一律走 facts(单一数据源), 测试与实现不同源抄公式。
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "3d"))

import facts as F
import centering as C

TOL = 1e-9
TOL_Z = 1e-6

# 中央孔: idx 8, span 8.5(=SPAN_DISTINCT[-1]), springer 1.14(=facts.SPRINGER)
CENTRAL_IDX = 8
CENTRAL_SPAN = F.SPAN_DISTINCT[-1]          # 8.50
CENTRAL_SPRINGER = F.DECK_Z_TOP - F.SPANDREL_C - F.rise_ratio(CENTRAL_IDX) * CENTRAL_SPAN
RING_T = F.RING_T

# 端孔: idx 0, span 4.5, springer 近水 ~0.75(brief 锚: 端冠 2.23 = 0.79+0.32*4.5)
END_IDX = 0
END_SPAN = F.SPAN_DISTINCT[0]               # 4.50
END_SPRINGER = 0.79


def _central():
    return C.build_centering(CENTRAL_IDX, CENTRAL_SPAN, RING_T, 0.0,
                             CENTRAL_SPRINGER, lambda x: F.DECK_Z_TOP)


def _end():
    # 端孔跨上桥面 ≈ 端冠 + 端拱肩(冬照口径 crown2.23+spandrel_e0.5=2.73)
    crown = F.arch_z(0.0, 0.0, END_SPRINGER, END_SPAN / 2.0, F.rise_ratio(END_IDX) * END_SPAN)
    deck = crown + F.SPANDREL_E
    return C.build_centering(END_IDX, END_SPAN, RING_T, 0.0, END_SPRINGER,
                             lambda x: deck), crown


def _extrados(span, springer, arch_idx, x):
    a = span / 2.0
    b = F.rise_ratio(arch_idx) * span
    return F.arch_z(x, 0.0, springer, a, b) + RING_T


def _parts(res, kind):
    return [p for p in res["parts"] if p["kind"] == kind]


def _x_center(p):
    return (p["bbox"][0] + p["bbox"][1]) / 2.0


def _check_closed_hexahedron(part):
    """闭合六面体: 8 顶点 / 6 quad 面 / 12 边各恰属 2 面 / 每面共面 / bbox 与顶点一致。"""
    vs = part["verts"]
    fs = part["faces"]
    assert len(vs) == 8, "顶点数 != 8"
    assert len(fs) == 6, "面数 != 6"
    edges = []
    for f in fs:
        assert len(f) == 4, "非 quad 面"
        assert all(0 <= i < 8 for i in f)
        # 共面: 三向量混合积 = 0
        p0 = vs[f[0]]
        u = [vs[f[1]][k] - p0[k] for k in range(3)]
        v = [vs[f[2]][k] - p0[k] for k in range(3)]
        w = [vs[f[3]][k] - p0[k] for k in range(3)]
        n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
        assert abs(n[0] * w[0] + n[1] * w[1] + n[2] * w[2]) < 1e-9, "面不共面"
        for k in range(4):
            a, b = f[k], f[(k + 1) % 4]
            assert a != b
            edges.append((min(a, b), max(a, b)))
    assert len(set(edges)) == 12, "边数 != 12(或面间重复边)"
    cnt = Counter(edges)
    assert all(c == 2 for c in cnt.values()), "存在边不属于恰 2 面(非闭合)"
    bb = part["bbox"]
    for k in range(3):
        assert abs(min(v[k] for v in vs) - bb[2 * k]) < 1e-12
        assert abs(max(v[k] for v in vs) - bb[2 * k + 1]) < 1e-12


def _poly_area(pts):
    s = 0.0
    for i in range(len(pts)):
        x1, z1 = pts[i]
        x2, z2 = pts[(i + 1) % len(pts)]
        s += x1 * z2 - x2 * z1
    return abs(s) / 2.0


# ---------------------------------------------------------------- Step1 判据

def test_result_shape_and_id():
    res = _central()
    assert res["id"] == "CEN-ARCH08"
    assert set(res.keys()) >= {"id", "parts", "wedge_events", "footprint_polys"}
    assert len(res["parts"]) > 0
    assert {p["kind"] for p in res["parts"]} <= {"post", "waling", "rib", "wedge"}
    for kind in ("post", "waling", "rib", "wedge"):
        assert _parts(res, kind), "缺少 kind=%s 构件" % kind


def test_all_parts_are_closed_hexahedra():
    for res in (_central(), _end()[0]):
        for p in res["parts"]:
            _check_closed_hexahedron(p)


def test_central_post_rows():
    """中央孔 span 8.5 → 柱排数 = int(8.5/1.2)+1 = 8(每排两柱)。"""
    res = _central()
    stations = len(_parts(res, "waling"))
    assert stations == int(CENTRAL_SPAN / C.POST_SPACING) + 1 == 8
    assert len(_parts(res, "post")) == 2 * stations
    # 排距对称布点, 首末贴拱脚
    xs = sorted({_x_center(p) for p in _parts(res, "waling")})
    assert abs(xs[0] + CENTRAL_SPAN / 2.0) < TOL_Z
    assert abs(xs[-1] - CENTRAL_SPAN / 2.0) < TOL_Z


def test_two_bents_y_layout():
    """排架沿 y 两榀, 位于 ±(ring_t/2+0.1) 外(brief 补充设计)。"""
    res = _central()
    ys = sorted({(p["bbox"][2] + p["bbox"][3]) / 2.0 for p in _parts(res, "post")})
    y_out = RING_T / 2.0 + C.BENT_Y_CLEAR
    assert len(ys) == 2
    assert abs(ys[0] + y_out) < TOL_Z and abs(ys[1] - y_out) < TOL_Z


def test_rib_verts_in_extrados_band():
    """rib 板逐顶点: z ∈ [extrados+0.03, extrados+0.06](上缘≤+0.06, 下缘≥+0.03−tol)。"""
    res = _central()
    ribs = _parts(res, "rib")
    assert ribs
    for p in ribs:
        for v in p["verts"]:
            base = _extrados(CENTRAL_SPAN, CENTRAL_SPRINGER, CENTRAL_IDX, v[0]) + 0.03
            assert base - TOL_Z <= v[2] <= base + 0.03 + TOL_Z, \
                "rib 顶点越出券胎带: %r" % (v,)


def test_lift_raises_centering_surface():
    """lift>0 → 券胎面整体抬升 lift(预抬量), 且仍高于 lift=0 工况。"""
    lift = 0.02
    res = C.build_centering(CENTRAL_IDX, CENTRAL_SPAN, RING_T, lift,
                            CENTRAL_SPRINGER, lambda x: F.DECK_Z_TOP)
    for p in _parts(res, "rib"):
        for v in p["verts"]:
            base = _extrados(CENTRAL_SPAN, CENTRAL_SPRINGER, CENTRAL_IDX, v[0]) + 0.03 + lift
            assert base - TOL_Z <= v[2] <= base + 0.03 + TOL_Z
    assert max(p["bbox"][5] for p in _parts(res, "rib")) > \
        max(p["bbox"][5] for p in _parts(_central(), "rib")) - TOL_Z


def test_wedge_events_equal_post_heads():
    """卸架楔 = 每柱头一对(上下楔各一); wedge_events = 柱头对数 > 0。"""
    res = _central()
    posts = _parts(res, "post")
    wedges = _parts(res, "wedge")
    assert res["wedge_events"] == len(posts) > 0
    assert len(wedges) == 2 * res["wedge_events"]
    # 上下楔各名义高 0.12、斜面 1:8: 两端立边高均值=0.12, 高差=楔长/8
    for p in wedges:
        xlo, xhi = p["bbox"][0], p["bbox"][1]
        h = {}
        for v in p["verts"]:
            side = "lo" if abs(v[0] - xlo) < 1e-12 else "hi"
            h.setdefault(side, []).append(v[2])
        hlo = max(h["lo"]) - min(h["lo"])
        hhi = max(h["hi"]) - min(h["hi"])
        assert abs((hlo + hhi) / 2.0 - C.WEDGE_H) < TOL_Z, "楔名义高非 0.12"
        assert abs(abs(hlo - hhi) - (xhi - xlo) / C.WEDGE_SLOPE) < TOL_Z, "斜面非 1:8"
        assert abs(hlo - hhi) > 1e-6, "楔面无坡度"


def test_waling_sits_on_wedge_pairs():
    """柱顶 → 楔对(0.24) → 楞木(0.12) → 工作面: 堆叠逐层相接。"""
    res = _central()
    for w in _parts(res, "waling"):
        x = _x_center(w)
        assert abs(w["bbox"][4] - (w["bbox"][5] - C.WALING_H)) < TOL_Z
        below = [p for p in res["parts"] if p["kind"] == "wedge"
                 and abs(_x_center(p) - x) < C.POST_SPACING / 2.0]
        assert below
        for p in below:
            assert p["bbox"][5] <= w["bbox"][4] + TOL_Z
        posts = [p for p in _parts(res, "post")
                 if abs(_x_center(p) - x) < 1e-9]
        assert len(posts) == 2
        for pt in posts:
            assert abs(pt["bbox"][5] + 2 * C.WEDGE_H - w["bbox"][4]) < TOL_Z


def test_springing_and_arc_support_targets():
    """拱脚区(|x|>a−0.5)楞木顶贴 intrados 下方; 跨中柱顶工作面 = extrados+0.03。"""
    res = _central()
    a = CENTRAL_SPAN / 2.0
    n_spring = 0
    for w in _parts(res, "waling"):
        x = _x_center(w)
        if abs(x) > a - C.SPRINGER_ZONE:
            n_spring += 1
            expect = _extrados(CENTRAL_SPAN, CENTRAL_SPRINGER, CENTRAL_IDX, x) - RING_T
        else:
            expect = _extrados(CENTRAL_SPAN, CENTRAL_SPRINGER, CENTRAL_IDX, x) + 0.03
        assert abs(w["bbox"][5] - expect) < TOL_Z, "楞木顶高度失配 x=%r" % x
    assert n_spring == 2  # 中央孔两端各一排落入拱脚区


def test_footprint_covers_span_and_ring_band():
    """footprint_polys: 券胎板 x-z 外轮廓, 覆盖全跨, 面积>0, 顶缘进环带(+0.03 以上)。"""
    res = _central()
    polys = res["footprint_polys"]
    assert polys
    all_pts = [pt for poly in polys for pt in poly]
    assert _poly_area(polys[0]) > 0
    xs = [pt[0] for pt in all_pts]
    zs = [pt[1] for pt in all_pts]
    assert abs(min(xs) + CENTRAL_SPAN / 2.0) < TOL_Z
    assert abs(max(xs) - CENTRAL_SPAN / 2.0) < TOL_Z
    crown_ext = _extrados(CENTRAL_SPAN, CENTRAL_SPRINGER, CENTRAL_IDX, 0.0)
    assert max(zs) >= crown_ext + 0.03 - TOL_Z
    assert min(zs) <= crown_ext  # 带体自券胎面以下, 确在环带区投影内


def test_end_arch_fewer_rows_and_height_cap():
    """端孔(span 4.5, 端冠 2.23): 柱排数 < 中央孔; 柱顶 z ≤ crown+ring_t+0.1。"""
    res, crown = _end()
    assert abs(crown - 2.23) < 0.01  # brief 锚
    stations = len(_parts(res, "waling"))
    assert stations == int(END_SPAN / C.POST_SPACING) + 1
    assert stations < int(CENTRAL_SPAN / C.POST_SPACING) + 1
    posts = _parts(res, "post")
    assert posts
    top = max(p["bbox"][5] for p in posts)
    assert top <= crown + RING_T + 0.1
    # 端孔 springer 近水仍按统一柱底基准
    assert min(p["bbox"][4] for p in posts) == C.bottom_z()
    # 跨上桥面高于券胎面: 桥面拓扑夹持不误伤真实工况
    rib_top = max(p["bbox"][5] for p in _parts(res, "rib"))
    assert rib_top <= crown + RING_T + 0.06 + TOL_Z


def test_all_rib_rows_have_posts_under_waling_zone():
    """每排楞木下方确有楔对与两柱; 柱底一律 BODY_BOTTOM 基准。"""
    res = _central()
    z0 = C.bottom_z()
    for p in _parts(res, "post"):
        assert abs(p["bbox"][4] - z0) < TOL_Z
    xs = sorted({_x_center(p) for p in _parts(res, "waling")})
    assert len(xs) == len(_parts(res, "waling"))  # 一排一件楞木, x 互异
