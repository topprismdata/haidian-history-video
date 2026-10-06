# e30_shikongqiao_video/tests/test_p1_families.py
import os, sys
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "3d"))
import families as F

def _y_span(p):
    """楔形全部顶点 y 跨度(hw_b>hw_t 且 d>收分差时 = d+(hw_b-hw_t))."""
    v, _ = F.family_mesh("wedge-std", p)
    ys = [vv[1] for vv in v]
    return max(ys) - min(ys)


def _front_top_minus_bottom(p):
    """前脸顶沿 y - 前脸底沿 y(每 z 层 y 最大者为前脸)."""
    v, _ = F.family_mesh("wedge-std", p)
    top = max(vv[1] for vv in v if abs(vv[2] - p["h"]) < 1e-12)
    bot = max(vv[1] for vv in v if abs(vv[2]) < 1e-12)
    return top - bot


def test_wedge_std_deterministic_and_manifold():
    p = {"w": 1.2, "h": 0.55, "d": 1.2, "proud": 0.006, "back": 0.30,
         "hw_b": 6.0, "hw_t": 5.84}
    v1, f1 = F.family_mesh("wedge-std", p)
    v2, f2 = F.family_mesh("wedge-std", p)
    assert v1 == v2 and f1 == f2          # 确定性
    assert len(v1) == 8 and len(f1) == 6  # 楔形六面
    # 流形: 每边恰好两面
    from collections import Counter
    ec = Counter()
    for face in f1:
        for i in range(len(face)):
            a, b = face[i], face[(i + 1) % len(face)]
            ec[(min(a, b), max(a, b))] += 1
    assert all(c == 2 for c in ec.values())

def test_wedge_std_follows_batter():
    p = {"w": 1.0, "h": 0.4, "d": 1.0, "proud": 0.006, "back": 0.30,
         "hw_b": 6.0, "hw_t": 5.9}
    delta = _front_top_minus_bottom(p)
    assert delta == pytest.approx(-(p["hw_b"] - p["hw_t"]))
    # 负控制①: 无收分(hw_b==hw_t) -> 前脸上下沿 y 差为 0
    flat = dict(p, hw_t=p["hw_b"])
    assert _front_top_minus_bottom(flat) == pytest.approx(0.0)
    # 负控制②: 反坡(hw_b<hw_t) -> 方向翻转(证明测的是方向关系而非数值巧合)
    rev = dict(p, hw_b=5.9, hw_t=6.0)
    d_rev = _front_top_minus_bottom(rev)
    assert d_rev == pytest.approx(-(rev["hw_b"] - rev["hw_t"]))
    assert d_rev > 0.0


def test_wedge_std_top_edge_batters_inward():
    # C2: 顶沿内收——前脸顶沿 y - 底沿 y == -(hw_b-hw_t)(带符号)
    p = {"w": 1.0, "h": 0.4, "d": 1.2, "proud": 0.006, "back": 0.30,
         "hw_b": 6.0, "hw_t": 5.84}
    assert _front_top_minus_bottom(p) == pytest.approx(-(p["hw_b"] - p["hw_t"]))

def test_bake_unique_cache_invalidates_on_curve_hash(tmp_path):
    v, f = F.family_mesh("wedge-std", {"w": 1.0, "h": 0.4, "d": 1.0,
                                       "proud": 0.006, "back": 0.3,
                                       "hw_b": 6.0, "hw_t": 5.9})
    p1 = F.bake_unique("ARCH09.EAST.SPANDREL.C03.B02", v, f,
                       str(tmp_path), "hashA")
    assert os.path.exists(p1)
    p2 = F.bake_unique("ARCH09.EAST.SPANDREL.C03.B02", v, f,
                       str(tmp_path), "hashB")
    assert p1 != p2  # curve_hash 变 -> 缓存失效重烘


def test_wedge_std_depth_follows_d():
    # C1: 深度由 d 决定——背沿 y = 前沿 y - d
    base = {"w": 1.0, "h": 0.4, "proud": 0.006, "back": 0.30,
            "hw_b": 6.0, "hw_t": 5.9}
    s1 = _y_span(dict(base, d=1.2))
    s2 = _y_span(dict(base, d=2.4))
    assert s2 - s1 > 0.3
    # 负控制: d 相等 -> 跨度差为 0
    assert s2 - _y_span(dict(base, d=2.4)) == pytest.approx(0.0)
    assert s1 == pytest.approx(1.2 + (6.0 - 5.9))
    # d 权威: 有 d 时 back 被忽略
    assert s1 == pytest.approx(_y_span(dict(base, d=1.2, back=9.9)))


def test_wedge_std_back_fallback_when_d_missing():
    # U1 兜底: d 缺失时 d = back + proud
    p = {"w": 1.0, "h": 0.4, "proud": 0.02, "back": 0.3,
         "hw_b": 6.0, "hw_t": 6.0}
    assert _y_span(p) == pytest.approx(0.02 + 0.3)


def test_slab_deterministic_and_manifold():
    # m2: slab 确定性与流形
    p = {"w": 1.5, "d": 0.8, "h": 0.3}
    v1, f1 = F.family_mesh("slab", p)
    v2, f2 = F.family_mesh("slab", p)
    assert v1 == v2 and f1 == f2
    assert len(v1) == 8 and len(f1) == 6
    from collections import Counter
    ec = Counter()
    for face in f1:
        for i in range(len(face)):
            a, b = face[i], face[(i + 1) % len(face)]
            ec[(min(a, b), max(a, b))] += 1
    assert all(c == 2 for c in ec.values())
