# e30_shikongqiao_video/tests/test_p1_families.py
import os, sys
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "3d"))
import families as F

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
    v, f = F.family_mesh("wedge-std", p)
    ys_front = sorted(set(round(vv[1], 4) for vv in v))
    # 前脸上下沿 y 不同(随收分倾斜), 差≈hw_b-hw_t
    assert abs((max(ys_front) - min(ys_front)) - 0.0) > 1e-6

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
