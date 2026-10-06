# -*- coding: utf-8 -*-
"""P1-T8 G2 门纯逻辑单测(blender-free; 不渲桥、不跑 masonry 提取)。

覆盖: RING/IMPOST 两新族锚语义(masonry2 分派)、families._baked 还原、
账目条目构造与 materialize 可逆性(含负控制)、耳切三角化(非凸环扇帽面)、
相邻缝对采样、G2 报告结构闸门(含篡改负控)、gap 两级判负控制。
Blender 内部分(数量/顶点互证)在 p1a_slice --g2 自 assert, 不在此重复。
"""
import copy
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "3d"))
import masonry2 as M2  # noqa: E402
import families as FAM  # noqa: E402
import ledger as LED  # noqa: E402
import p1a_slice as P  # noqa: E402


# ── 锚语义分派(接线清单⑦) ─────────────────────────────────────────────

def test_ring_wedge_centroid_anchor():
    assert M2.anchor_offset("ring-wedge", {},
                            [1.0, 2.0, 3.0, 0.0, 0.0, 0.0]) == (1.0, 2.0, 3.0)


def test_impost_step_uses_wedge_semantics():
    got = M2.anchor_offset("impost-step", {"w": 2.0, "h": 0.4,
                                           "proud": 0.06},
                           [10.0, -5.0, 4.0, 0.0, 0.0, 0.0])
    assert got == (9.0, -5.06, 3.8)


def test_ring_wedge_not_min_corner_cap_semantics():
    # 券环是真几何, 不得进 cap_to_deck 的最小角截顶名单
    assert "ring-wedge" not in M2._ANCHOR_MIN_CORNER
    assert "impost-step" not in M2._ANCHOR_MIN_CORNER


def test_unknown_family_still_raises():
    with pytest.raises(ValueError):
        M2.anchor_offset("ring-wedge-x", {}, [0.0, 0.0, 0.0, 0.0, 0.0, 0.0])


# ── families._baked 还原 ──────────────────────────────────────────────

def test_baked_family_roundtrip():
    bake = {"v": [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 1.0, 0.0]],
            "f": [[0, 1, 2]]}
    for fam in ("ring-wedge", "impost-step"):
        v, f = FAM.family_mesh(fam, {"bake": bake})
        assert [tuple(x) for x in v] == [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0),
                                         (1.0, 1.0, 0.0)]
        assert f == [(0, 1, 2)]


def test_baked_family_unknown_raises():
    with pytest.raises(KeyError):
        FAM.family_mesh("no-such-family", {})


# ── 账目条目构造 + materialize 可逆性 ─────────────────────────────────

def _ring_world():
    # 环扇棱柱(12 顶点, 与 _voussoir 拓扑同构): x-z 环扇 + y 向拉伸
    inner = [(0.0, 0.0), (0.5, 0.1), (1.0, 0.4)]
    outer = [(1.4, 0.9), (0.6, 0.7), (-0.2, 0.5)]
    prof = inner + outer
    y0, y1 = -3.0, 3.0
    verts = [(x, y0, z) for (x, z) in prof] + [(x, y1, z) for (x, z) in prof]
    m = len(prof)
    faces = [(0, 1, 2, 3, 4, 5), (11, 10, 9, 8, 7, 6)] + \
            [(i, (i + 1) % m, (i + 1) % m + m, i + m) for i in range(m)]
    return verts, faces


def test_make_ring_entry_id_role_and_materialize_roundtrip():
    verts, faces = _ring_world()
    trace = {"xc": -63.894, "x0": -64.1, "x1": -63.2, "ring_t": 0.54,
             "lift": 0.0, "n": 15, "ang0": 12.5, "ang1": 24.0}
    st = P.make_ring_entry(8, 6, verts, faces, trace)
    assert st["id"] == "ARCH09.EAST.RING.C00.B07"
    assert st["role_struct"] == "RING"
    assert st["family"] == "ring-wedge"
    assert st["evidence"] == "ashlar_truth"
    assert st["params"]["xc"] == trace["xc"]
    assert st["params"]["angles"] == [12.5, 24.0]
    assert st["params"]["through"] == "full_depth"
    # id 语法过账本校验
    led = {"meta": {"schema": LED.SCHEMA, "curve_hash": "t", "seed": 0},
           "stones": [st]}
    assert LED.validate_ledger(led) == []
    # 质心锚 + bake: materialize 精确还原世界网格(顶点多重集)
    import masonry2 as M2
    wv, wf = M2.materialize(st)
    assert sorted(round(c, 9) for v in wv for c in v) == \
        sorted(round(c, 9) for v in verts for c in v)


def test_make_ring_entry_rejects_anchor_drift():
    """负控制: transform 被篡改(锚漂移 1cm)时 materialize 不再还原世界网格
    —— 可逆性判据对真差异敏感。"""
    verts, faces = _ring_world()
    trace = {"xc": 0.0, "x0": 0.0, "x1": 1.0, "ring_t": 0.54, "lift": 0.0,
             "n": 15, "ang0": 0.0, "ang1": 1.0}
    st = P.make_ring_entry(8, 0, verts, faces, trace)
    bad = copy.deepcopy(st)
    bad["transform"][0] += 0.01
    import masonry2 as M2
    wv, _wf = M2.materialize(bad)
    dev = max(abs(a[0] - b[0]) for a, b in zip(wv, verts))
    assert dev > 0.009, "等价判据对真差异无感"


def test_make_impost_entry_wedge_anchor_roundtrip():
    # impost 脚步块: x∈[10,11], z∈[4,4.1], 前脸 y=2.0(proud=0.05), 逐角变 y
    x0, x1, z0, z1 = 10.0, 11.0, 4.0, 4.1
    p = 0.05
    yf = [2.00, 2.01, 2.01, 2.02]      # 四角前脸 y(x,z)
    back = 0.35
    verts = [(x0, yf[0] - back, z0), (x1, yf[1] - back, z0),
             (x1, yf[1], z0), (x0, yf[0], z0),
             (x0, yf[2] - back, z1), (x1, yf[3] - back, z1),
             (x1, yf[3], z1), (x0, yf[2], z1)]
    faces = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
             (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    cx, cz = (x0 + x1) / 2.0, (z0 + z1) / 2.0
    trace = {"xc": 9.0, "step": 1, "sgn": 1, "face": "EAST", "x0": x0,
             "x1": x1, "z0": z0, "z1": z1, "proud": p, "back": back,
             "proj": 0.0, "ty_front": 2.01}
    st = P.make_impost_entry(8, 0, verts, faces, trace)
    assert st["id"] == "ARCH09.EAST.IMPOST.C01.B01"
    assert st["family"] == "impost-step"
    assert st["params"]["w"] == pytest.approx(1.0)
    assert st["params"]["h"] == pytest.approx(0.1)
    led = {"meta": {"schema": LED.SCHEMA, "curve_hash": "t", "seed": 0},
           "stones": [st]}
    assert LED.validate_ledger(led) == []
    import masonry2 as M2
    wv, _wf = M2.materialize(st)
    assert sorted(round(c, 9) for v in wv for c in v) == \
        sorted(round(c, 9) for v in verts for c in v)


# ── 三角化(非凸环扇帽面耳切) ─────────────────────────────────────────

def _annular_sector_pts():
    # 薄环扇(非凸多边形, 与券环帽面同构): 内弧 3 点 + 外弧 3 点
    return [(0.0, 0.0), (0.5, 0.05), (1.0, 0.2),
            (1.4, 0.7), (0.6, 0.6), (-0.2, 0.4)]


def test_triangulate_simple_nonconvex_sector_is_simple():
    pts = _annular_sector_pts()
    tris = P._triangulate_simple(pts)
    assert len(tris) == len(pts) - 2
    # 每个三角形与多边形同向(耳切性质: 无反绕/无覆盖)
    area = sum(P._cross2((0, 0), pts[i], pts[(i + 1) % len(pts)])
               for i in range(len(pts)))
    for (a, b, c) in tris:
        assert P._cross2(pts[a], pts[b], pts[c]) * area > 0


def test_triangulate_faces_counts_and_vertex_preservation():
    verts, faces = _ring_world()
    out = P.triangulate_faces(verts, faces)
    # 2 个六边形帽面(各 4 三角) + 6 个侧四边形(各 2 三角)
    assert len(out) == 8 + 12
    used = sorted(set(i for fc in out for i in fc))
    assert used == list(range(len(verts)))


def test_triangulate_faces_quad_passthrough():
    verts = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]
    out = P.triangulate_faces(verts, [(0, 1, 2, 3)])
    assert out == [(0, 1, 2), (0, 2, 3)]


# ── 相邻缝对采样 ──────────────────────────────────────────────────────

def _mk(zone, face, role, course, block, family="wedge-std"):
    params = {"w": 1.0, "h": 0.5, "d": 1.2, "proud": 0.006,
              "hw_b": 3.4, "hw_t": 3.3, "back": 0.3}
    if family == "ring-wedge" or family == "impost-step":
        params = {"bake": {"v": [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0],
                                 [1.0, 1.0, 0.0]],
                           "f": [[0, 1, 2]]}}
        if family == "impost-step":
            params.update({"w": 1.0, "h": 0.5, "proud": 0.006})
    return LED.new_stone(zone, face, role, course, block, family,
                         params, [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "qingshi")


def test_adjacent_pairs_types_and_dedup():
    stones = []
    for b in (1, 2, 3):
        stones.append(_mk("ARCH09", "EAST", "SPANDREL", 0, b))
        stones.append(_mk("ARCH09", "EAST", "BACK", 0, b))
    for b in (1, 2):
        stones.append(_mk("ARCH09", "EAST", "RING", 0, b, "ring-wedge"))
    stones.append(_mk("ARCH09", "EAST", "CORE", 0, 1, "slab"))
    stones.append(_mk("ARCH09", "EAST", "CORE", 0, 2, "slab"))
    stones.append(_mk("ARCH09", "EAST", "IMPOST", 0, 1, "impost-step"))
    stones.append(_mk("ARCH09", "EAST", "IMPOST", 0, 2, "impost-step"))
    pairs = P.adjacent_pairs(stones)
    types = {t for (t, _a, _b) in pairs}
    assert {"ring-ring", "spandrel-spandrel", "back-back", "spandrel-back",
            "core-core", "impost-impost"} <= types
    # 全部为同 zone 对且去重有序
    assert pairs == sorted(set(pairs))
    assert all(a.split(".")[0] == "ARCH09" and b.split(".")[0] == "ARCH09"
               for (_t, a, b) in pairs)


def test_sample_even_deterministic_and_bounded():
    items = list(range(100))
    s = P._sample_even(items, 20)
    assert len(s) == 20 and s[0] == 0 and s[-1] == 99
    assert s == P._sample_even(items, 20)
    assert P._sample_even(items[:5], 20) == items[:5]


# ── G2 报告结构闸门(含篡改负控) ───────────────────────────────────────

def _good_report():
    return {
        "meta": {"schema": 1, "gate": "G2", "scale": 0.02, "scale_denom": 50,
                 "counts": {"stones": 3, "print_units": 2,
                            "ring_total": 193, "impost_total": 492},
                 "scope": {"print_units": 2, "excluded": [
                     {"bucket": "in_void", "n": 1},
                     {"bucket": "void_cut_fragment", "n": 0},
                     {"bucket": "ring_band_overlap", "n": 0},
                     {"bucket": "thin_merge", "n": 0}]}},
        "check_stone": {"n": 2, "n_fail": 0, "fails": []},
        "gap_check": {"n_pairs": 4, "n_fail": 0, "fails": [],
                      "per_arch": {"ARCH%02d" % (i + 1):
                                   {"candidates": 4, "sampled": 4,
                                    "n_fail": 0}
                                   for i in range(17)}},
        "verdict": "PASS",
    }


def test_validate_g2_report_accepts_consistent_pass():
    assert P.validate_g2_report(_good_report()) == []


def test_validate_g2_report_negative_controls():
    base = _good_report()
    r1 = copy.deepcopy(base)
    r1["verdict"] = "FAIL"                      # verdict 与 n_fail 矛盾
    assert P.validate_g2_report(r1) != []
    r2 = copy.deepcopy(base)
    r2["check_stone"]["fails"].append({"id": "X", "issues": []})
    r2["check_stone"]["n_fail"] = 1             # PASS 带非空 fail
    assert P.validate_g2_report(r2) != []
    r3 = copy.deepcopy(base)
    r3["meta"]["counts"]["ring_total"] = 192    # 数量互证被破坏
    assert P.validate_g2_report(r3) != []
    r4 = copy.deepcopy(base)
    r4["meta"]["scope"]["excluded"][0]["n"] = 2  # 守恒被破坏(2+0 != 3)
    assert P.validate_g2_report(r4) != []
    r5 = copy.deepcopy(base)
    del r5["gap_check"]["per_arch"]["ARCH09"]    # 17 孔抽样缺孔
    assert P.validate_g2_report(r5) != []


def test_g2_gate_constants():
    assert P.G2_SCALE == 1.0 / 50.0
    assert P.G2_MIN_WALL_PRINT_MM == 1.2
    assert P.G2_GAP_TOL_MODEL_MM == 0.5
    assert P.G2_GAP_PAIRS_PER_ARCH == 20
    assert P.G2_N_ARCH == 17


# ── run_g2 合成小账(范围分桶 + 判据行为) ──────────────────────────────

def _synthetic_led():
    """迷你账: 一块健康面石 + 一块截顶薄片(thin_merge 桶) + 一块在洞内
    石(in_void 桶)。几何手工构造, 不依赖真链。"""
    good = LED.new_stone("ARCH09", "EAST", "SPANDREL", 0, 1, "wedge-std",
                         {"w": 1.0, "h": 0.5, "d": 1.2, "proud": 0.006,
                          "back": 0.3, "hw_b": 3.4, "hw_t": 3.3},
                         [0.0, 3.35, 4.0, 0.0, 0.0, 0.0], "qingshi")
    thin = LED.new_stone("ARCH09", "EAST", "SPANDREL", 1, 1, "wedge-std",
                         {"w": 1.0, "h": 0.03, "d": 1.2, "proud": 0.006,
                          "back": 0.3, "hw_b": 3.3, "hw_t": 3.29},
                         [0.0, 3.2, 4.3, 0.0, 0.0, 0.0], "qingshi")
    inside = LED.new_stone("ARCH09", "EAST", "CORE", 0, 1, "slab",
                           {"w": 1.0, "h": 0.6, "d": 2.0,
                            "bbox": {"x0": -0.5, "x1": 0.5, "y0": -1.0,
                                     "y1": 1.0, "z0": 1.0, "z1": 1.6}},
                           [-0.5, -1.0, 1.0, 0.0, 0.0, 0.0], "maoshi")
    return {"meta": {"schema": LED.SCHEMA, "curve_hash": "syn", "seed": 0},
            "stones": [good, thin, inside]}


def test_run_g2_synthetic_scope_buckets_and_report():
    led = _synthetic_led()
    statuses = {s["id"]: ("out", []) for s in led["stones"]}
    statuses["ARCH09.EAST.CORE.C00.B01"] = ("inside", [])
    rep = P.run_g2(led, statuses, pairs_per_arch=20)
    cs, gp = rep["check_stone"], rep["gap_check"]
    assert cs["n"] == rep["meta"]["counts"]["print_units"]
    ids = {s["id"] for s in led["stones"]}
    n_excluded = sum(e["n"] for e in rep["meta"]["scope"]["excluded"])
    assert cs["n"] + n_excluded == len(ids)
    # 薄片进 thin_merge, 洞内进 in_void, 健康石入打印单元
    buckets = {e["bucket"]: e["n"] for e in rep["meta"]["scope"]["excluded"]}
    assert buckets["thin_merge"] == 1
    assert buckets["in_void"] == 1
    assert buckets["void_cut_fragment"] == 0
    assert buckets["ring_band_overlap"] == 0
    assert rep["check_stone"]["n_fail"] == 0
    assert rep["verdict"] == "PASS"
    # 健康石逐石过检(打印单元=1 块 good)
    assert rep["meta"]["counts"]["print_units"] == 1


def test_gap_check_pair_negative_control_real_cross_and_phantom():
    """负控制: ①真实互穿的两盒 -> PENETRATION;
    ②AABB 相交但实体不相交(平行斜条带 = 径向缝幻影造型) -> ok+aabb_phantom;
    ③完全分离 -> ok。"""
    def box(x0, x1, y0, y1, z0, z1):
        v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
             (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        # 管线一致: world_mesh 输出为三角化面(共面正面积判只在三角面生效)
        f = P.triangulate_faces(v, [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
                                    (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)])
        return v, f

    def diag_slab(dx, dy):
        """对角条带棱柱(厚 0.1, 沿 (1,1) 方向): AABB 是大矩形, 实体是细斜带。
        dy/dx 平移平行条带 -> 实体不相交而 AABB 相交(径向缝幻影同构)。"""
        v = [(0.0 + dx, 0.0 + dy, 0.0), (1.0 + dx, 1.0 + dy, 0.0),
             (1.0 + dx, 1.1 + dy, 0.0), (0.0 + dx, 0.1 + dy, 0.0),
             (0.0 + dx, 0.0 + dy, 1.0), (1.0 + dx, 1.0 + dy, 1.0),
             (1.0 + dx, 1.1 + dy, 1.0), (0.0 + dx, 0.1 + dy, 1.0)]
        f = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
             (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
        return v, f

    def entry(v, f, t):
        return (list(t), (v, f))

    # ① 真互穿: 两盒在 x 上重叠 0.2
    va, fa = box(0, 1, 0, 1, 0, 1)
    vb, fb = box(0.8, 1.8, 0, 1, 0, 1)
    rep, ph = P.gap_check_pair(entry(va, fa, (0, 0, 0, 0, 0, 0)),
                               entry(vb, fb, (0, 0, 0, 0, 0, 0)))
    assert not rep["ok"] and not ph
    assert rep["issues"][0]["code"] == "PENETRATION"
    # ② AABB 相交(全轴正重叠)但实体不相交: 平行斜条带【法向】错开 0.15
    #    (带间隙 0.15/√2 ≈ 0.106 > 0; 径向缝幻影同构: AABB 咬合、面不相交)
    va, fa = diag_slab(0.0, 0.0)
    vb, fb = diag_slab(0.075, -0.075)
    rep, ph = P.gap_check_pair(entry(va, fa, (0, 0, 0, 0, 0, 0)),
                               entry(vb, fb, (0, 0, 0, 0, 0, 0)))
    assert ph is True and rep["ok"]
    # ③ 完全分离
    vc, fc = box(5, 6, 0, 1, 0, 1)
    rep, ph = P.gap_check_pair(entry(va, fa, (0, 0, 0, 0, 0, 0)),
                               entry(vc, fc, (0, 0, 0, 0, 0, 0)))
    assert rep["ok"] and not ph
