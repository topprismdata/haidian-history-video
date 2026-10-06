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
import build_scene2 as BS  # noqa: E402
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
        "meta": {"schema": 2, "gate": "G2", "scale": 0.02, "scale_denom": 50,
                 "volume_caliber": {"statement": "x"},
                 "counts": {"stones": 3, "print_units": 2,
                            "ring_total": 193, "impost_total": 492},
                 "scope": {"print_units": 2, "excluded": [
                     {"bucket": "in_void", "n": 1},
                     {"bucket": "void_cut_fragment", "n": 0},
                     {"bucket": "ring_band_overlap", "n": 0},
                     {"bucket": "thin_merge", "n": 0}]}},
        "check_stone": {"n": 2, "n_fail": 0, "fails": [],
                        "fail_matrix": {}, "legacy_clip_survey":
                            {"n": 0, "n_fail": 0, "matrix": {}}},
        "gap_check": {"n_pairs": 4, "n_fail": 0, "fails": [],
                      "assembly_fit": {"n": 0, "n_exempt": 0, "warn": None,
                                       "pairs": []},
                      "per_arch": {"ARCH%02d" % (i + 1):
                                   {"candidates": 4, "sampled": 4,
                                    "spandrel_back": 2, "n_fail": 0}
                                   for i in range(17)}},
        "ring_dedup": {"pairs": [], "summary": {"n_subsumed": 0,
                                                "n_trimmed": 0,
                                                "removed_model_cm3":
                                                    {"subsumed": 0.0,
                                                     "trimmed": 0.0}},
                       "trimmed_ids": [], "subsumed_ids": [],
                       "final_scope_check": {"n_pairs": 0,
                                             "n_colliding": 0,
                                             "pairs": []}},
        "coverage_audit": [{"bucket": "in_void", "cells": 0,
                            "uncovered_cells": 0, "uncovered_cm2": 0.0}],
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
    # ── T8c 结构闸门负控(复审: 全量记账要到手, 也要防被静默抹掉) ──
    r6 = copy.deepcopy(base)                     # 合法 FAIL 变体(对照)
    r6["verdict"] = "FAIL"
    r6["check_stone"]["n_fail"] = 1
    r6["check_stone"]["fails"] = [{"id": "X", "issues": []}]
    r6["check_stone"]["fail_matrix"] = {"SELF_INTERSECT": 1}
    r6["ring_dedup"]["final_scope_check"]["n_colliding"] = 1
    r6["ring_dedup"]["final_scope_check"]["pairs"] = [{"chain": "X"}]
    assert P.validate_g2_report(r6) == []
    r6["ring_dedup"]["final_scope_check"]["pairs"] = []   # 明细被清空
    assert any("pairs" in q for q in P.validate_g2_report(r6))
    r7 = copy.deepcopy(base)                     # trim 计数/账本互证
    r7["ring_dedup"]["summary"]["n_trimmed"] = 2
    r7["ring_dedup"]["trimmed_ids"] = ["A", "B"]
    r7["ring_dedup"]["summary"]["removed_model_cm3"]["trimmed"] = 12.5
    assert P.validate_g2_report(r7) == []
    r7["ring_dedup"]["trimmed_ids"] = []         # 计数被抹
    assert any("n_trimmed" in q for q in P.validate_g2_report(r7))
    r7["ring_dedup"]["trimmed_ids"] = ["A", "B"]
    r7["ring_dedup"]["summary"]["removed_model_cm3"]["trimmed"] = 0.0
    assert any("removed_model_cm3.trimmed" in q
               for q in P.validate_g2_report(r7))
    r8 = copy.deepcopy(base)                     # 覆盖率审计不许被清零
    r8["coverage_audit"][0] = {"bucket": "in_void", "cells": 25,
                               "uncovered_cells": 25, "uncovered_cm2": 0.0}
    assert any("uncovered_cm2" in q for q in P.validate_g2_report(r8))
    r8["coverage_audit"][0]["uncovered_cm2"] = 100.0     # 25 格 x 4cm2/格
    assert P.validate_g2_report(r8) == []
    r9 = copy.deepcopy(base)                     # fail_matrix 互证
    r9["verdict"] = "FAIL"
    r9["check_stone"]["n_fail"] = 1
    r9["check_stone"]["fails"] = [{"id": "X", "issues": []}]
    r9["check_stone"]["fail_matrix"] = {"SELF_INTERSECT": 2}
    assert any("fail_matrix" in q for q in P.validate_g2_report(r9))
    r9["check_stone"]["fail_matrix"] = {"SELF_INTERSECT": 1}
    assert P.validate_g2_report(r9) == []


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
    ③完全分离 -> ok; ④吞没盒(包含型, 面不相交但顶点在对方体内) ->
    PENETRATION; ⑤共面贴合(零体积重叠) -> ok。"""
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
    rep, ph, _depth = P.gap_check_pair(entry(va, fa, (0, 0, 0, 0, 0, 0)),
                               entry(vb, fb, (0, 0, 0, 0, 0, 0)))
    assert not rep["ok"] and not ph
    assert rep["issues"][0]["code"] == "PENETRATION"
    # ② AABB 相交(全轴正重叠)但实体不相交: 平行斜条带【法向】错开 0.15
    #    (带间隙 0.15/√2 ≈ 0.106 > 0; 径向缝幻影同构: AABB 咬合、面不相交)
    va, fa = diag_slab(0.0, 0.0)
    vb, fb = diag_slab(0.075, -0.075)
    rep, ph, _depth = P.gap_check_pair(entry(va, fa, (0, 0, 0, 0, 0, 0)),
                               entry(vb, fb, (0, 0, 0, 0, 0, 0)))
    assert ph is True and rep["ok"]
    # ③ 完全分离
    vc, fc = box(5, 6, 0, 1, 0, 1)
    rep, ph, _depth = P.gap_check_pair(entry(va, fa, (0, 0, 0, 0, 0, 0)),
                               entry(vc, fc, (0, 0, 0, 0, 0, 0)))
    assert rep["ok"] and not ph
    # ④ 吞没盒(C2 包含型负控): 小盒完全在大盒体内 —— AABB 全轴正重叠、
    #    两网格面永不相交, 旧两级判放成 aabb_phantom; 任一实体顶点在对方
    #    体内 => PENETRATION(包含型互穿不是缝)。
    vbig, fbig = box(0, 4, 0, 4, 0, 4)
    vsml, fsml = box(1, 2, 1, 2, 1, 2)
    rep, ph, _depth = P.gap_check_pair(entry(vbig, fbig, (0, 0, 0, 0, 0, 0)),
                               entry(vsml, fsml, (0, 0, 0, 0, 0, 0)))
    assert not rep["ok"] and not ph, "吞没盒必须判 PENETRATION(包含型)"
    assert rep["issues"][0]["code"] == "PENETRATION"
    # 反向(小盒作 A)同判 —— 包含判据对称
    rep, ph, _depth = P.gap_check_pair(entry(vsml, fsml, (0, 0, 0, 0, 0, 0)),
                               entry(vbig, fbig, (0, 0, 0, 0, 0, 0)))
    assert not rep["ok"] and not ph
    # 接触不算包含: 两盒共面贴合(面接触、零体积重叠)仍 ok
    vtan, ftan = box(4, 5, 0, 4, 0, 4)
    rep, ph, _depth = P.gap_check_pair(entry(vbig, fbig, (0, 0, 0, 0, 0, 0)),
                               entry(vtan, ftan, (0, 0, 0, 0, 0, 0)))
    assert rep["ok"], "共面贴合不得判包含互穿"


# ── T8b-B3: ring_band_overlap 面积判据(吞没石必排除, 低重叠回收) ──────

def _box_ring_entry(x0, x1, z0, z1, block=1):
    """合成 RING 条目: bake 网格 = x-z 矩形棱柱(质心锚), y 厚 1.0。"""
    cx, cz = (x0 + x1) / 2.0, (z0 + z1) / 2.0
    verts = [(x0, 0.0, z0), (x1, 0.0, z0), (x1, 0.0, z1), (x0, 0.0, z1),
             (x0, 1.0, z0), (x1, 1.0, z0), (x1, 1.0, z1), (x0, 1.0, z1)]
    faces = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2),
             (2, 6, 7, 3), (3, 7, 4, 0)]
    local = [(v[0] - cx, v[1] - 0.5, v[2] - cz) for v in verts]
    params = {"bake": {"v": local, "f": faces}}
    return LED.new_stone("ARCH09", "EAST", "RING", 0, block, "ring-wedge",
                         params, [cx, 0.5, cz, 0.0, 0.0, 0.0], "qingshi")


def _spandrel_at(xc, zc, w, h, course=0, block=1):
    params = {"w": w, "h": h, "d": 1.2, "proud": 0.006, "back": 0.3,
              "hw_b": 3.4, "hw_t": 3.3}
    return LED.new_stone("ARCH09", "EAST", "SPANDREL", course, block,
                         "wedge-std", params,
                         [xc, 3.3, zc, 0.0, 0.0, 0.0], "qingshi")


def test_ring_band_raster_area_criterion():
    """B3: 排除判据从 point-in-bbox 改面积法 —— 石足印与 RING 栅格(2cm x-z)
    交面积占比 >50% 才排除; 完全吞没石 ratio=1 必排除; 角碰低重叠石
    (ratio<=0.5)不得再被过剔(回收进 scope, 真撞与否交 gap 宇宙裁决)。"""
    ring = _box_ring_entry(0.0, 1.0, 4.0, 4.5)
    engulfed = _spandrel_at(0.5, 4.25, 0.4, 0.3)     # 足印全在 RING 足印内
    corner = _spandrel_at(1.1, 4.6, 0.4, 0.4)        # 只碰一角(overlap 6%级)
    far = _spandrel_at(5.0, 6.0, 0.5, 0.5)           # 与 RING 无涉
    led = {"meta": {"schema": LED.SCHEMA, "curve_hash": "syn", "seed": 0},
           "stones": [ring, engulfed, corner, far]}
    statuses = {s["id"]: ("out", []) for s in led["stones"]}
    raster = P._ring_footprint_raster(led)
    assert raster["ARCH09"], "RING 足印栅格为空"
    assert P._ring_overlap_ratio(engulfed, raster, statuses) == pytest.approx(1.0)
    r_corner = P._ring_overlap_ratio(corner, raster, statuses)
    assert 0.0 < r_corner <= 0.5, "角碰石占比应落在回收区间: %r" % r_corner
    assert P._ring_overlap_ratio(far, raster, statuses) == 0.0
    sc = P.print_scope(led, statuses)
    got = sc["buckets"]["ring_band_overlap"]
    assert got == [engulfed["id"]], "吞没石必排除, 角碰石必回收: %r" % (got,)
    scope_ids = {s["id"] for s in sc["scope"]}
    assert corner["id"] in scope_ids and far["id"] in scope_ids


def test_write_excluded_ids_sidecar(tmp_path):
    """D6: 排除件全量 id 旁挂 out/print/excluded_ids.json(桶->ids 全表,
    含 standing 空桶), 守恒计数入 meta。"""
    sc = {"scope": [{"id": "KEEP.1"}],
          "buckets": {"in_void": ["A"], "void_cut_fragment": [],
                      "ring_band_overlap": ["B", "C"], "thin_merge": []}}
    led = {"meta": {"curve_hash": "e30-p1t8-full"}, "stones": []}
    path = P.write_excluded_ids(sc, led, str(tmp_path / "excluded_ids.json"))
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    assert data["buckets"]["in_void"] == ["A"]
    assert data["buckets"]["ring_band_overlap"] == ["B", "C"]
    assert data["buckets"]["void_cut_fragment"] == []
    assert data["buckets"]["thin_merge"] == []
    assert data["buckets"]["carve_p4"] == [] and data["buckets"]["abut"] == []
    assert data["meta"]["curve_hash"] == "e30-p1t8-full"
    assert data["meta"]["excluded_total"] == 3
    assert data["meta"]["print_units"] == 1


def test_validate_g2_report_t8b_schema_negative_controls():
    """T8b 结构闸门负控: PASS 与 n_colliding>0 矛盾、旧 overlap_mm 字段、
    assembly_fit 缺真深度、缺 coverage_audit / volume_caliber 必被抓。"""
    base = _good_report()
    r1 = copy.deepcopy(base)
    r1["ring_dedup"]["final_scope_check"]["n_colliding"] = 2
    assert P.validate_g2_report(r1) != []
    r2 = copy.deepcopy(base)
    r2["gap_check"]["assembly_fit"] = {
        "n": 1, "pairs": [{"a": "X", "b": "Y", "overlap_mm": 3.0}]}
    assert P.validate_g2_report(r2) != []
    r3 = copy.deepcopy(base)
    r3["gap_check"]["assembly_fit"] = {
        "n": 1, "pairs": [{"a": "X", "b": "Y", "aabb_min_axis_mm": 3.0}]}
    assert P.validate_g2_report(r3) != []       # 缺 depth_mm(真深度)
    r4 = copy.deepcopy(base)
    r4.pop("coverage_audit")
    assert P.validate_g2_report(r4) != []
    r5 = copy.deepcopy(base)
    r5["meta"].pop("volume_caliber")
    assert P.validate_g2_report(r5) != []
    r6 = copy.deepcopy(base)
    r6["verdict"] = "FAIL"                      # 与全零 fail 矛盾
    assert P.validate_g2_report(r6) != []


# ── T8b-B4: volume 宇宙处置(审查四条负控 + case_A/B 边界) ─────────────

def _core_slab(x0, x1, y0, y1, z0, z1, block=1):
    params = {"w": x1 - x0, "h": z1 - z0, "d": y1 - y0,
              "bbox": {"x0": x0, "x1": x1, "y0": y0, "y1": y1,
                       "z0": z0, "z1": z1}}
    return LED.new_stone("ARCH09", "EAST", "CORE", 0, block, "slab",
                         params, [x0, y0, z0, 0.0, 0.0, 0.0], "maoshi")


def _mini_disposition_led(rings, chains):
    led = {"meta": {"schema": LED.SCHEMA, "curve_hash": "syn", "seed": 0},
           "stones": list(rings) + list(chains)}
    statuses = {s["id"]: ("out", []) for s in led["stones"]}
    scope = list(chains)
    buckets = {"in_void": [], "void_cut_fragment": [],
               "ring_band_overlap": [], "thin_merge": []}
    return led, statuses, scope, buckets


def _arch09_crown_z():
    band = BS.arch_band(8)
    return band["springer"] + band["b"]      # 冠底(intrados 顶) z


def test_case_a_engulfed_stone_subsumed_by_volume():
    """审查负控②a: 完全吞没石(体积 100% 在 RING 内)必须走完整处置函数落
    case_A(subsume) —— 出打印集归 ring_band_overlap, final_scope_check=0。"""
    cz = _arch09_crown_z()
    ring = _box_ring_entry(-0.2, 0.2, cz - 0.2, cz + 0.4)
    ring_whole = _box_ring_entry(-0.2, 0.2, cz - 0.2, cz + 0.4, block=2)
    engulfed = _core_slab(-0.1, 0.1, 0.1, 0.9, cz - 0.1, cz + 0.3)
    led, statuses, scope, buckets = _mini_disposition_led(
        [ring, ring_whole], [engulfed])
    rd = P._ring_dedup_dispositions(led, statuses, scope, buckets,
                                    {"ARCH09": 8})
    assert rd["summary"]["n_subsumed"] == 1
    assert engulfed["id"] in buckets["ring_band_overlap"]
    assert all(s["id"] != engulfed["id"] for s in scope)
    e = rd["pairs"][0]
    assert e["disposition"] == "subsume" and e["unique_vol_cm3"] <= 50.0
    assert rd["final_scope_check"]["n_colliding"] == 0


def test_case_b_corner_bite_trimmed_not_discarded():
    """审查负控②b: 只咬一角/底带的石(独有材料大)必须落 case_B(trim),
    不得进 case_A —— 防止'凡撞必丢'退化。裁片入 scope, params 记
    clipped_by=ring_band。"""
    cz = _arch09_crown_z()
    cut = cz + 0.55                       # 冠处切割线≈intrados+RING_T+GAP
    ring = _box_ring_entry(-0.2, 0.2, cz - 0.2, cz + 0.4)
    biter = _core_slab(-0.5, 0.5, 0.1, 0.9, cut - 0.35, cut + 0.35)
    led, statuses, scope, buckets = _mini_disposition_led([ring], [biter])
    rd = P._ring_dedup_dispositions(led, statuses, scope, buckets,
                                    {"ARCH09": 8})
    e = rd["pairs"][0]
    assert e["disposition"] == "trim", e
    assert e["unique_vol_cm3"] > P.SUBSUME_ABS_CM3, "咬合石不得误判 case_A"
    assert rd["summary"]["n_trimmed"] == 1
    assert biter["params"]["clipped_by"] == "ring_band"
    kept_ids = {s["id"] for s in scope}
    assert biter["id"] in kept_ids, "case_B 石必须保留(裁不是丢)"


def test_case_b_two_rings_each_half_not_case_a():
    """审查负控④: 两块环各吞一半的合成石(unique≈50%)必须落 case_B 而非
    case_A —— 防'单块 max 低估'与阈值口径漂移。"""
    cz = _arch09_crown_z()
    cut = cz + 0.55                       # 冠处切割线(intrados+RING_T+GAP)
    r1 = _box_ring_entry(-0.6, -0.1, cut - 0.5, cut - 0.05, block=1)
    r2 = _box_ring_entry(0.1, 0.6, cut - 0.5, cut - 0.05, block=2)
    half = _core_slab(-0.5, 0.5, 0.1, 0.9, cut - 0.3, cut + 0.3)
    led, statuses, scope, buckets = _mini_disposition_led([r1, r2], [half])
    rd = P._ring_dedup_dispositions(led, statuses, scope, buckets,
                                    {"ARCH09": 8})
    e = rd["pairs"][0]
    assert set(e["rings"]) == {r1["id"], r2["id"]}, "须对两环并集体素求交"
    assert e["disposition"] == "trim"
    assert e["unique_vol_cm3"] > 0.01 * e["v_stone_cm3"]


def test_disposition_uses_preinset_geometry():
    """审查负控③: 处置判据必须吃 pre-inset 几何 —— 构造 y 向仅 5mm 搭接
    的吞没石(post-inset 配合余量会把接触洗成无碰), 若实现误用 post-inset
    则宇宙根本找不到撞对, 处置不会发生。"""
    cz = _arch09_crown_z()
    ring = _box_ring_entry(-0.2, 0.2, cz - 0.2, cz + 0.4)
    sliver = _core_slab(-0.1, 0.1, 0.4, 0.6, cz - 0.1, cz + 0.3)
    # 石 y 深度 0.2m, 与环 y[0,1] 重叠; post-inset NORMAL 档 15mm/side 仍
    # 重叠 —— 改用更狠的判别: 断言处置用的 entry 无 inset(直接查函数)
    led, statuses, scope, buckets = _mini_disposition_led([ring], [sliver])
    rd = P._ring_dedup_dispositions(led, statuses, scope, buckets,
                                    {"ARCH09": 8})
    assert rd["summary"]["n_subsumed"] + rd["summary"]["n_trimmed"] >= 1
    # 机制钉死: pre-inset entry 顶点没有 inset 收缩(与 _gap_entry 差异)
    world = M2.materialize(sliver)[0]
    pre = P._preinset_gap_entry(sliver, statuses)
    post = P._gap_entry(sliver, statuses)
    w = max(v[1] for v in world) - min(v[1] for v in world)
    wp = (max(v[1] for v in pre[1][0]) - min(v[1] for v in pre[1][0]))
    wo = (max(v[1] for v in post[1][0]) - min(v[1] for v in post[1][0]))
    assert wp == pytest.approx(w, abs=1e-12), "pre-inset entry 不得收缩"
    assert wo < wp - 1e-3, "post-inset entry 应收缩(对照, 证明两者不同)"


def test_negative_control_disable_subsume_surfaces_collision():
    """审查负控①: 真扰动管线 —— 对已知 case_A 石禁用 subsume 通道且令
    带裁剪失效(裁剪返回整块), 重跑处置+复测: final_scope_check 必须
    n_colliding>0(不变式可破坏, 非恒真)。"""
    cz = _arch09_crown_z()
    ring = _box_ring_entry(-0.2, 0.2, cz - 0.2, cz + 0.4)
    engulfed = _core_slab(-0.1, 0.1, 0.1, 0.9, cz - 0.1, cz + 0.3)
    led, statuses, scope, buckets = _mini_disposition_led([ring],
                                                          [engulfed])
    orig = P._band_trim_polys
    x0, x1, z0, z1 = BS.stone_world_bbox(engulfed)
    full = [[(x0, z0), (x1, z0), (x1, z1), (x0, z1)]]

    def keep_all(stone, arch_idx, rings):
        return list(full), 0.0

    P._band_trim_polys = keep_all
    P.SUBSUME_ABS_CM3 = -1.0
    P.SUBSUME_REL_MAX = -1.0
    try:
        rd = P._ring_dedup_dispositions(led, statuses, scope, buckets,
                                        {"ARCH09": 8})
    finally:
        P._band_trim_polys = orig
        P.SUBSUME_ABS_CM3 = 50.0
        P.SUBSUME_REL_MAX = 0.01
    assert rd["pairs"][0]["disposition"] == "trim"
    assert rd["final_scope_check"]["n_colliding"] >= 1, \
        "禁用 subsume 后不变式必须破 —— 判据非恒真"


def test_ring_trim_world_y_interval_pinned():
    """复审[2]钉死测试①: 裁片世界 y 区间必须 ⊆ 名义 y 区间 ± clearance+eps
    —— 首版把世界 x-z 直喂局部 y 剖面且漏 off_y, 489 块整体错位 3~5m。
    y 区间判据零成本(纯 materialize, blender-free)。"""
    cz = _arch09_crown_z()
    cut = cz + 0.55
    ring = _box_ring_entry(-0.2, 0.2, cz - 0.2, cz + 0.4)
    biter = _core_slab(-0.5, 0.5, 0.1, 0.9, cut - 0.35, cut + 0.35)
    led, statuses, scope, buckets = _mini_disposition_led([ring], [biter])
    P._ring_dedup_dispositions(led, statuses, scope, buckets, {"ARCH09": 8})
    assert statuses[biter["id"]][0] == "ring_trim"
    wv, _wf = P.world_mesh(biter, statuses)
    ys = [v[1] for v in wv]
    p = biter["params"]["bbox"]
    lo_nom, hi_nom = p["y0"], p["y1"]
    assert lo_nom - 1e-9 <= min(ys) and max(ys) <= hi_nom + 1e-9, \
        "裁片世界 y 越出名义区间: [%r, %r] vs [%r, %r]" % (
            min(ys), max(ys), lo_nom, hi_nom)


def test_ring_trim_clears_partner_and_ring_solids():
    """复审[2]钉死测试②: 裁后与同位 partner、与 RING 的实体相交必须为 0
    (pre-inset 面级判) —— 钉'裁片不再撞'而非钉比值。面石/背衬同块位跨
    切割线, y 向按真实缝(面内缘 0.1 / 背衬外缘 0.098, 隐缝 2mm)。"""
    cz = _arch09_crown_z()
    cut = cz + 0.55
    ring = _box_ring_entry(-0.2, 0.2, cz - 0.2, cz + 0.4)
    fp = {"w": 1.0, "h": 0.7, "d": 0.5, "proud": 0.006,
          "hw_b": 0.6, "hw_t": 0.6, "back": 0.3}
    face = LED.new_stone("ARCH09", "EAST", "SPANDREL", 0, 1, "wedge-std",
                         fp, [0.0, 0.606, cut, 0.0, 0.0, 0.0], "qingshi")
    bp = {"w": 1.0, "h": 0.7, "d": 0.5, "proud": 0.0,
          "hw_b": 0.6, "hw_t": 0.6, "front_c": 0.0}
    partner = LED.new_stone("ARCH09", "EAST", "BACK", 0, 1, "wedge-std",
                            bp, [0.0, 0.098, cut, 0.0, 0.0, 0.0], "maoshi")
    led, statuses, scope, buckets = _mini_disposition_led(
        [ring], [face, partner])
    rd = P._ring_dedup_dispositions(led, statuses, scope, buckets,
                                    {"ARCH09": 8})
    trims = {p["chain"]: p["disposition"] for p in rd["pairs"]}
    assert trims.get(face["id"]) == "trim", trims
    assert trims.get(partner["id"]) == "trim_partner", trims
    stones = {s_["id"]: s_ for s_ in led["stones"]}
    for sid in (face["id"], partner["id"]):
        rep, _ph, _d = P.gap_check_pair(
            P._preinset_gap_entry(stones[sid], statuses),
            P._preinset_gap_entry(ring, statuses))
        assert rep["ok"], "%s 裁后仍撞 RING: %r" % (sid, rep["issues"])
    rep, _ph, _d = P.gap_check_pair(
        P._preinset_gap_entry(face, statuses),
        P._preinset_gap_entry(partner, statuses))
    assert rep["ok"], "裁后 face×partner 实体互穿: %r" % (rep["issues"],)


# ---------------------------------------------------------------------------
# T8c 真总体落位回归(C-T8b-1 防再犯): 现有判据全 x-z 口径, y 向错位不可
# 见 —— 上面两条钉死测试是合成迷你账, 这里对【真账本全量 489 裁石】钉
# y 区间与符号。管线一次 ~140s(纯 python, 无 blender), module 级 fixture
# 两条测试共享。
_LEDGER_FULL = os.path.join(os.path.dirname(__file__), "..", "3d",
                            "out", "ledger_full.json")


@pytest.fixture(scope="module")
def real_ring_trim_state():
    if not os.path.exists(_LEDGER_FULL):
        pytest.skip("out/ledger_full.json 不在盘上: 先跑 blender -b "
                    "--python 3d/p1a_slice.py -- --g2")
    led = copy.deepcopy(json.load(open(_LEDGER_FULL)))
    statuses = P.classify_full(led["stones"])
    sc = P.print_scope(led, statuses)
    arch_idx_of = {"ARCH%02d" % (i + 1): i for i in range(P.G2_N_ARCH)}
    rd = P._ring_dedup_dispositions(led, statuses, sc["scope"],
                                    sc["buckets"], arch_idx_of)
    by_id = {s["id"]: s for s in led["stones"]}
    trim_ids = sorted(sid for sid, st in statuses.items()
                      if st[0] == "ring_trim")
    return by_id, statuses, trim_ids, rd


RING_TRIM_POPULATION = 475   # T8c 复测钉死: 传播守卫后真总体(漂移=总体变)


def test_ring_trim_world_y_within_family_band_real_population(
        real_ring_trim_state):
    """T8c 钉死③(真总体 y 区间): 全部 ring_trim 裁片的世界 y 区间 ⊆ 原族
    整石世界 y 带 ±1e-6(判据 = P.ring_trim_y_violations, 与 run_g2 内
    断言同一实现, 不做第二套口径)。C-T8b-1 首版把世界 x-z 直喂局部剖
    面: 489 块整体错位 3~5m(ARCH03.EAST.SPANDREL.C07.B00 修复前
    y∈[-5.04,-2.55], 修复后 [0.84,3.33]; counterfactual: gap 216 -> 0)。
    同一判据第二战果: 抓到 partner 足印错传(CORE kept 交给 SPANDREL,
    剖面越域外推 y 越带 ~0.3m, 14 石)。"""
    by_id, statuses, trim_ids, rd = real_ring_trim_state
    assert len(trim_ids) == RING_TRIM_POPULATION, \
        "裁片总体漂移: %d (期望 %d)" % (len(trim_ids), RING_TRIM_POPULATION)
    bad = P.ring_trim_y_violations({"stones": list(by_id.values())},
                                   statuses)
    assert not bad, ("%d/%d 块裁片世界 y 越出原族 y 带(前10: id, trim_y, "
                     "family_y): %r" % (len(bad), len(trim_ids), bad[:10]))
    # trim 材料账: 账面值 == 逐对 collide_vol 之和(复审领走账, 目标口径)
    sm = rd["summary"]
    vol_sum = round(sum(p["collide_vol_cm3_pre"] for p in rd["pairs"]
                        if p["disposition"] in ("trim", "trim_partner")), 3)
    assert sm["n_trimmed"] == len(trim_ids)
    assert sm["removed_model_cm3"]["trimmed"] > 0.0
    assert sm["removed_model_cm3"]["trimmed"] == vol_sum, \
        "trim 材料账 != 逐对 collide 之和: %r vs %r" % (
            sm["removed_model_cm3"]["trimmed"], vol_sum)


def test_ring_trim_east_west_centroid_y_sign_real_population(
        real_ring_trim_state):
    """T8c 钉死④(真总体 y 符号): EAST 裁片质心 y>0、WEST<0 —— 首版 ty>0
    的 EAST 石落到负半平面(y∈[-5.04,-2.55]), x-z 口径判据全绿也看不见。
    无侧别 id 的裁片计数必须为 0(符号判据覆盖面自证)。"""
    by_id, statuses, trim_ids, _rd = real_ring_trim_state
    bad = []
    noside = []
    for sid in trim_ids:
        parts = sid.split(".")
        side = parts[1] if len(parts) > 2 else None
        role = parts[2] if len(parts) > 3 else None
        if side not in ("EAST", "WEST"):
            noside.append(sid)
            continue
        tv, _tf = P.world_mesh(by_id[sid], statuses)
        tys = [v[1] for v in tv]
        cy = sum(tys) / len(tys)
        if role == "CORE":
            # 全墙胞(y_extent=full_wall) y 向对称, 质心恒 ≈0 —— 符号判据
            # 对它换形态: y 错位必然破坏 |cy|≈0(实测真总体 20 石全 0.0)
            if abs(cy) > 1e-3:
                bad.append((sid, "CORE:sym", round(cy, 4)))
            continue
        if side == "EAST" and not cy > 0.0:
            bad.append((sid, "EAST", round(cy, 4)))
        if side == "WEST" and not cy < 0.0:
            bad.append((sid, "WEST", round(cy, 4)))
    assert not noside, "无侧别裁片(符号判据盲区): %r" % noside[:10]
    assert not bad, "%d 块裁片 y 符号错(侧别, 质心 y): %r" % (len(bad), bad[:10])


def test_partner_propagation_requires_same_footprint_role_pair():
    """T8c 钉死⑤: 传播只发生在 SPANDREL↔BACK 同足印对。_partner_id 的
    else 分支会把 CORE 的"partner"解析成 SPANDREL, 但承压胞与拱面石足印
    完全不同 —— 传播必须被拒, 否则面石拿到异石足印(CORE 胞 x 跨 ~3.2m、
    z 低一层), 剖面在 [0,h] 外线性外推, y 越出族带 ~0.3m。SPANDREL→BACK
    正向(传播仍发生)由 test_ring_trim_clears_partner_and_ring_solids 钉。"""
    cz = _arch09_crown_z()
    cut = cz + 0.55
    ring = _box_ring_entry(-0.2, 0.2, cz - 0.2, cz + 0.4)
    core = _core_slab(-0.5, 0.5, 0.1, 0.9, cut - 0.35, cut + 0.35)
    fp = {"w": 0.3, "h": 0.3, "d": 0.5, "proud": 0.006,
          "hw_b": 0.6, "hw_t": 0.6, "back": 0.3}
    face = LED.new_stone("ARCH09", "EAST", "SPANDREL", 0, 1, "wedge-std",
                         fp, [0.0, 0.606, cut + 1.0, 0.0, 0.0, 0.0],
                         "qingshi")
    led, statuses, scope, buckets = _mini_disposition_led(
        [ring], [core, face])
    rd = P._ring_dedup_dispositions(led, statuses, scope, buckets,
                                    {"ARCH09": 8})
    disp = {p["chain"]: p["disposition"] for p in rd["pairs"]}
    assert disp.get(core["id"]) == "trim", disp      # CORE 自身照常裁
    assert disp.get(face["id"]) is None, \
        "足印不同角色不得传播: %r" % disp.get(face["id"])
    assert statuses[face["id"]][0] == "out", \
        "面石足印未被碰到, 必须保持整石: %r" % (statuses[face["id"]][0],)
