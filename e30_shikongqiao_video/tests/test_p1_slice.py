# -*- coding: utf-8 -*-
"""P1-T8 G2 门纯逻辑单测(blender-free; 不渲桥、不跑 masonry 提取)。

覆盖: RING/IMPOST 两新族锚语义(masonry2 分派)、families._baked 还原、
账目条目构造与 materialize 可逆性(含负控制)、耳切三角化(非凸环扇帽面)、
相邻缝对采样、G2 报告结构闸门(含篡改负控)、gap 两级判负控制。
Blender 内部分(数量/顶点互证)在 p1a_slice --g2 自 assert, 不在此重复。
"""
import copy
import json
import math
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
                            "print_stones": 2, "run_units": 0,
                            "ring_total": 193, "impost_total": 492},
                 "scope": {"print_units": 2, "print_stones": 2,
                           "run_units": [], "excluded": [
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
                       # n_pairs=827: T9b(B2c) 起结构闸门有复测对数地板(903→827 拱线族返工实测)
                       # (>= counts.ring_total), 合成底座同吃真总体口径。
                       "final_scope_check": {"n_pairs": 903,
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
    # ── T9 W1: subsume 材料闸严格 AND(镜像 trim 侧) —— 面积桶账
    # subsumed_by_area_bucket 是另一口径, 不可替代 volume 宇宙的
    # removed_model_cm3.subsumed(篡改=把 subsume 材料流记成 0 仍过闸) ──
    r10 = copy.deepcopy(base)                    # 合法 FAIL 变体打底
    r10["verdict"] = "FAIL"
    r10["check_stone"]["n_fail"] = 1
    r10["check_stone"]["fails"] = [{"id": "X", "issues": []}]
    r10["check_stone"]["fail_matrix"] = {"SELF_INTERSECT": 1}
    r10["ring_dedup"]["final_scope_check"]["n_colliding"] = 1
    r10["ring_dedup"]["final_scope_check"]["pairs"] = [{"chain": "X"}]
    r10["ring_dedup"]["summary"]["n_subsumed"] = 2
    r10["ring_dedup"]["subsumed_ids"] = ["A", "B"]
    r10["ring_dedup"]["summary"]["removed_model_cm3"]["subsumed"] = 0.0
    r10["ring_dedup"]["summary"]["removed_model_cm3"][
        "subsumed_by_area_bucket"] = 5.8e7       # 面积桶账在, 也必须红
    qs = P.validate_g2_report(r10)
    assert any("removed_model_cm3.subsumed" in q for q in qs), qs
    r10["ring_dedup"]["summary"]["removed_model_cm3"]["subsumed"] = 33.0
    assert P.validate_g2_report(r10) == []       # 材料账到手即绿
    # ── T9b(B2c): 复测对数地板 —— n_pairs=0/1 的"只测零对全绿"谎报必红
    # (审查 tamper: SILENT n_pairs=0/1 曾 GREEN), 地板=counts.ring_total ──
    rc = copy.deepcopy(base)
    for bad_pairs in (0, 1, 192):                # 192 == ring_total-1 也红
        rc["ring_dedup"]["final_scope_check"]["n_pairs"] = bad_pairs
        assert any("n_pairs" in q for q in P.validate_g2_report(rc)), bad_pairs
    rc["ring_dedup"]["final_scope_check"]["n_pairs"] = 193    # 地板上恢复绿
    assert P.validate_g2_report(rc) == []
    # ── T9b(M2): 面积桶材料账不可静默抹(n_area_bucket_measured>0 ⇒
    # subsumed_by_area_bucket>0; 真总体 182 块/5.83e7 cm3) ──
    rm2 = copy.deepcopy(base)                    # 合法变体: 账在
    rm2["ring_dedup"]["summary"]["n_area_bucket_measured"] = 182
    rm2["ring_dedup"]["summary"]["removed_model_cm3"][
        "subsumed_by_area_bucket"] = 5.8e7
    assert P.validate_g2_report(rm2) == []
    rm2["ring_dedup"]["summary"]["removed_model_cm3"][
        "subsumed_by_area_bucket"] = 0.0         # 账被抹
    assert any("subsumed_by_area_bucket" in q
               for q in P.validate_g2_report(rm2))
    # ── T9b(M2): legacy 存量追偿单不可静默蒸发(n>0 ⇒ disposition+
    # debt_ticket 必在; 真总体 1520/842 记 T5/T7) ──
    lg = copy.deepcopy(base)                     # 合法变体: 追偿单在
    lg["check_stone"]["legacy_clip_survey"] = {
        "n": 1520, "n_fail": 842, "matrix": {"SELF_INTERSECT": 842},
        "disposition": "excluded(以 RING 为准)", "debt_ticket": "T5/T7"}
    assert P.validate_g2_report(lg) == []
    lg["check_stone"]["legacy_clip_survey"].pop("debt_ticket")
    assert any("debt_ticket" in q for q in P.validate_g2_report(lg))
    lg["check_stone"]["legacy_clip_survey"] = {"n": 1520, "n_fail": 842,
                                               "matrix": {}}
    assert any("disposition" in q for q in P.validate_g2_report(lg))
    # ── T9 run 升格谱系闸: 形状必须由 run_g2 真实生成(T9b M1: 不再手写
    # 生产者不产的键) —— 端到端走 run_g2 见
    # test_run_g2_multirun_real_shape_scope_key_and_lineage_gate ──


def test_run_g2_multirun_real_shape_scope_key_and_lineage_gate():
    """T9b(M1): 合法多 run 报告由 run_g2 真实形状生成(参数化注入点: 合成
    账 + 注入 ring_trim 双 run status, 走完整 run_g2 路径), 生产者必须自
    带 meta.scope.print_stones 键(M1 补; 旧形状回退 print_units 曾把第一
    份合法多 run 报告假报守恒失败); 生产形状过结构闸门, 篡改谱系/差值
    互证必红 —— 多 run 机制(分桶->处置->升格->报告->闸门)端到端被走过。"""
    stone = _core_slab(0.0, 3.0, 0.1, 0.9, 4.0, 5.0)
    sid = stone["id"]
    run_a = [(0.0, 4.0), (0.8, 4.0), (0.8, 5.0), (0.0, 5.0)]
    run_b = [(2.2, 4.0), (3.0, 4.0), (3.0, 5.0), (2.2, 5.0)]
    led = {"meta": {"schema": LED.SCHEMA, "curve_hash": "syn", "seed": 0},
           "stones": [stone]}
    statuses = {sid: ("ring_trim", [run_a, run_b])}   # 注入点: 双 run 带裁
    rep = P.run_g2(led, statuses, pairs_per_arch=20)
    # 生产者形状: scope 以石计, run_units 记【全部】run 单元(含 R0),
    # print_units = print_stones - 多run石数 + len(run_units) = 2
    assert rep["meta"]["scope"]["print_stones"] == 1
    assert rep["meta"]["counts"]["print_stones"] == 1
    assert rep["meta"]["counts"]["run_units"] == 2
    assert rep["meta"]["counts"]["print_units"] == 2
    assert rep["check_stone"]["n"] == 2
    assert rep["meta"]["scope"]["run_units"] == [
        {"unit_id": sid + "#R0", "parent_ids": [sid], "role": "CORE"},
        {"unit_id": sid + "#R1", "parent_ids": [sid], "role": "CORE"}]
    # 生产者真实多 run 形状过结构闸门(第一份合法多 run 报告不许假红)
    graft = _good_report()
    graft["meta"]["counts"].update({"stones": 1, "print_units": 2,
                                    "print_stones": 1, "run_units": 2})
    graft["meta"]["scope"] = rep["meta"]["scope"]
    graft["check_stone"]["n"] = 2
    assert P.validate_g2_report(graft) == []
    graft["meta"]["scope"]["run_units"][0]["parent_ids"] = []   # 谱系被抹
    assert any("parent_ids" in q for q in P.validate_g2_report(graft))
    graft["meta"]["scope"]["run_units"][0]["parent_ids"] = [sid]
    graft["meta"]["counts"]["print_units"] = 3                  # 差值互证破坏
    assert any("print_units != print_stones" in q
               for q in P.validate_g2_report(graft))


def test_real_population_ledger_gate_fails_loud_when_missing(monkeypatch):
    """T9 W2 负控: ledger_full.json 缺失时真总体钉数据闸必须 raise
    (fail-on-skip), 而不是 pytest.skip 制造干净克隆假绿。"""
    import sys
    this_mod = sys.modules[__name__]
    monkeypatch.setattr(this_mod, "_LEDGER_FULL",
                        os.path.join(os.path.dirname(__file__),
                                     "fixtures", "no_such_ledger.json"))
    with pytest.raises(RuntimeError, match="fail-on-skip"):
        this_mod._load_real_ledger_or_fail()


_G2_REPORT_ARTIFACT = os.path.join(os.path.dirname(__file__), "..", "3d",
                                   "out", "print", "g2_report.json")


def test_g2_report_shipped_artifact_pins():
    """T9b(B2b): 入库工件钉 —— out/print/g2_report.json 是 G2 门的唯一交
    付事实, CI 必须直接读它; 不许 verdict/counts/fsc 只活在 blender 那一
    次运行和报告文字里(审查 tamper: lift_at 恒零后重导, 此钉必须红)。
    纯读文件亚秒级; 缺失 = fail-loud(W2 同纪律, 不静默 skip)。"""
    if not os.path.exists(_G2_REPORT_ARTIFACT):
        raise RuntimeError(
            "out/print/g2_report.json 不在盘上 —— 入库工件钉 fail-loud"
            "(T9b B2b): 先跑 blender -b --python 3d/p1a_slice.py -- --g2; "
            "或显式 --deselect 本钉(不许静默跳过)")
    with open(_G2_REPORT_ARTIFACT, encoding="utf-8") as fh:
        rep = json.load(fh)
    assert P.validate_g2_report(rep) == []
    assert rep["verdict"] == "PASS"
    counts = rep["meta"]["counts"]
    assert counts["print_stones"] == 2037  # [拱线族返工清债] 2113→2037(排除 +76: in_void +24/void_cut +12/ring_band +40)
    assert counts["print_units"] == 2037  # 同上
    assert counts["run_units"] == 0
    # M1 后生产者必须自带 scope.print_stones 真键(盘上工件同步钉)
    assert rep["meta"]["scope"]["print_stones"] == 2037  # 同上
    assert rep["meta"]["scope"]["run_units"] == []
    fsc = rep["ring_dedup"]["final_scope_check"]
    assert fsc["n_pairs"] == FINAL_SCOPE_N_PAIRS
    assert fsc["n_colliding"] == 0


def test_g2_gate_constants():
    assert P.G2_SCALE == 1.0 / 50.0
    assert P.G2_MIN_WALL_PRINT_MM == 1.2
    assert P.G2_GAP_TOL_MODEL_MM == 0.5
    assert P.G2_GAP_PAIRS_PER_ARCH == 20
    assert P.G2_N_ARCH == 17
    # T9b(M4): 薄轴分支与 FIT 档的隐式耦合显式钉 —— EP.inset 的
    # ext<=2c 不动轴分支结构安全的前提是最宽 FIT 档 2*clr=1.0mm < 最小
    # 打印壁 1.2mm(越界石必被 thin_merge 收走, 不存在"薄轴不退让还能
    # 打"的件); 将来加更宽 FIT 档破坏此不变式必须在此响亮, 不许静默
    # 失去配合面退让。
    assert 2.0 * max(P.EP.FIT_PRINT_MM.values()) < P.G2_MIN_WALL_PRINT_MM


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
# T9: 带裁片 post-inset 自交回归(真失败件 fixture, P1 处方: 合成非凸件抓
# 不到)。fixture 由 3d/dump_check_fixtures.py 从真账重放生成并入库
# (tests/fixtures/check_106/): 同带全绿负控 1 件 + 真失败件(极值带顶点数
# 降序, 跨角色)。判据: 任意档位 clr 下 post-inset 无 SELF_INTERSECT;
# 含 T8c 单调性反转钉(15mm 曾 106/106 全红, 现 0)。

_FIXTURE_DIR_106 = os.path.join(os.path.dirname(__file__), "fixtures",
                                "check_106")


def _check106_fixtures():
    # type: () -> list
    return sorted(f for f in os.listdir(_FIXTURE_DIR_106)
                  if f.endswith(".json"))


@pytest.mark.parametrize("fname", _check106_fixtures())
def test_check106_fixture_post_inset_no_self_intersect(fname):
    import export_print as EP
    with open(os.path.join(_FIXTURE_DIR_106, fname),
              encoding="utf-8") as fh:
        meta = json.load(fh)
    faces = [tuple(f) for f in meta["faces"]]
    # fixture 元数据自证(T9b M3): post_ok 与历史失败码互斥一致 —— post_ok
    # False 的件必须带着旧实现下的失败码入库(证据可审计), 负控件必须无
    # 码; band 顶点数在册且 >0(几何漂移重生成时可见, 防静默换件)。
    assert (not meta["post_ok"]) == bool(meta["post_fail_codes"])
    assert meta.get("band_verts", 0) > 0, \
        "%s 缺 band_verts 元数据(T9b M3)" % meta["id"]
    # T8c 单调性反转钉: 旧实现 15mm 档 106/106 全 SELF_INTERSECT; 现仿射
    # inset 实现下入库 clr 与 7.5/15/25mm 四档必须全部 0 自交(负控件同判,
    # 防"别改坏好件")。
    for clr in (meta["clr_model_mm"], 7.5, 15.0, 25.0):
        v2, f2 = EP.flip_outward(EP.inset(meta["verts_pre"], clr), faces)
        rep = P.PC.check_stone(v2, f2, scale=P.G2_SCALE,
                               min_wall_print_mm=P.G2_MIN_WALL_PRINT_MM)
        codes = sorted({i["code"] for i in rep["issues"]})
        assert "SELF_INTERSECT" not in codes, \
            "%s clr=%.1fmm post-inset 自交: %r" % (meta["id"], clr,
                                                   rep["issues"][:3])


def test_check106_fixture_population_and_control():
    """fixture 总体自证: 失败件 >=3 且跨角色, 负控件(post_ok=True)在列,
    防止 fixture 目录被清空后判据恒真(没有失败件的回归钉是摆设)。"""
    ids = _check106_fixtures()
    assert len(ids) >= 4, "fixture 缺失: %r" % ids
    metas = []
    for fn in ids:
        with open(os.path.join(_FIXTURE_DIR_106, fn),
                  encoding="utf-8") as fh:
            metas.append(json.load(fh))
    fails = [m for m in metas if not m["post_ok"]]
    controls = [m for m in metas if m["post_ok"]]
    assert len(fails) >= 3 and len(controls) >= 1
    assert {m["role"] for m in fails} >= {"SPANDREL", "BACK", "CORE"}


def test_lift_coverage_pads_and_edge_is_strip_boundary():
    """T9 85 钉(两类根因): ①lift 覆盖含外弧角点越出段(pad = sin·(ring_t+
    lift) 与 JOINT_GAP_BACK 的代数和, 钳回 [x0,x1]; 角度缺失 -> 覆盖==
    stations, 旧口径逐位); ②覆盖边界必须成为条带边界 —— 台阶落在条带内部
    时单段线性 bound 把台阶抹成斜坡, 覆盖边界邻域欠割至多一整个 lift
    (ARCH07.CORE.C14.B01 实测: hit z[6.29,6.33] vs 真界 6.336, 36400cm3)。"""
    # ① pad 口径
    cov = P._ring_lift_coverage({"stations": [-1.0, 1.0],
                                 "angles": [-6.650228459881308,
                                            6.650228459879352],
                                 "ring_t": 0.54, "lift": 0.07})
    proj = 0.54 + 0.07
    ext = math.sin(math.radians(6.650228459881308)) * proj
    assert cov[0] == pytest.approx(-1.0 - (ext - 0.004), abs=1e-12)
    assert cov[1] == pytest.approx(1.0 + (ext - 0.004), abs=1e-12)
    assert P._ring_lift_coverage({"stations": [-1.0, 1.0],
                                  "ring_t": 0.54, "lift": 0.07}) == \
        (-1.0, 1.0, 0.07)              # 无角度 -> 旧 stations 口径
    assert P._ring_lift_coverage({"stations": [-1.0, 1.0], "lift": 0.0}) \
        is None                        # 无 lift 无覆盖
    # ② 覆盖边界成条带边界 + 台阶点不被抽稀: 用真 keystone 的浅法向角
    # (±6.65°, ARCH06 实测) —— 台阶点恰落在来向平滑曲线上, 旧抽稀会把它
    # 当共线点丢掉(右缘弦下切 13mm -> 环端面掠穿), 所以钉"poly 恰在覆盖
    # 边界处有顶点"而不是只钉条带边界。
    stone = _core_slab(-2.0, 2.0, 0.1, 0.9, 6.0, 7.5)
    ring_p = {"stations": [-0.5, 0.5],
              "angles": [-6.650228459881308, 6.650228459879352],
              "ring_t": 0.54, "lift": 0.07}
    cov = P._ring_lift_coverage(ring_p)
    kept, _removed = P._band_trim_polys(stone, 8, [{"params": ring_p}])
    assert kept, "跨拱顶石必须产生带裁保留片"
    edge_xs = {p[0] for poly in kept for p in poly}
    for target in cov[:2]:
        assert any(abs(ex - target) < 1e-9 for ex in edge_xs), \
            ("覆盖边界 %r 不在条带边界上(台阶被抹成斜坡): %r"
             % (target, sorted(edge_xs)[:8]))


def test_run_units_split_lineage_and_each_shell_clean():
    """T9 run 升格钉(审查裁决: MULTI_SHELL 不豁免): 多 run 带裁石必须拆成
    独立打印单元(id '<石id>#R<i>', 谱系 parent_ids=[石id]), 每个单元单独
    过 check 无 MULTI_SHELL。负控: 不拆的整石单 mesh(旧行为)必须红
    MULTI_SHELL —— 升格是真拆分, 不是豁免重命名。单 run 石恒等返回自身。"""
    stone = _core_slab(0.0, 3.0, 0.1, 0.9, 4.0, 5.0)
    sid = stone["id"]
    run_a = [(0.0, 4.0), (0.8, 4.0), (0.8, 5.0), (0.0, 5.0)]
    run_b = [(2.2, 4.0), (3.0, 4.0), (3.0, 5.0), (2.2, 5.0)]
    statuses = {sid: ("ring_trim", [run_a, run_b])}
    # 负控: 整石单 mesh = 两个互断闭合壳 -> MULTI_SHELL 必红
    v_all, f_all = P.world_mesh(stone, statuses)
    rep_all = P.PC.check_stone(v_all, f_all, scale=P.G2_SCALE,
                               min_wall_print_mm=P.G2_MIN_WALL_PRINT_MM)
    assert any(i["code"] == "MULTI_SHELL" for i in rep_all["issues"]), \
        rep_all["issues"]
    # 升格: 拆成两个独立单元, 谱系 + 各自单壳干净
    units = P._print_units(stone, statuses)
    assert [u[0] for u in units] == [sid + "#R0", sid + "#R1"]
    for (uid, polys_view) in units:
        verts, faces = P._ring_trim_mesh(polys_view, stone)
        fit, clr_model = P.EP.fit_for_block(P.EP._extents_m(verts), P.G2_SCALE)
        v2, f2 = P.EP.flip_outward(P.EP.inset(verts, clr_model), faces)
        rep = P.PC.check_stone(v2, f2, scale=P.G2_SCALE,
                               min_wall_print_mm=P.G2_MIN_WALL_PRINT_MM)
        assert not any(i["code"] == "MULTI_SHELL" for i in rep["issues"]), \
            (uid, rep["issues"])
    # 单 run / 非带裁石恒等
    assert P._print_units(stone, {sid: ("ring_trim", [run_a])}) == \
        [(sid, None)]
    assert P._print_units(stone, {sid: ("out", [])}) == [(sid, None)]


# ---------------------------------------------------------------------------
# T8c 真总体落位回归(C-T8b-1 防再犯): 现有判据全 x-z 口径, y 向错位不可
# 见 —— 上面两条钉死测试是合成迷你账, 这里对【真账本全量 489 裁石】钉
# y 区间与符号。管线一次 ~140s(纯 python, 无 blender), module 级 fixture
# 两条测试共享。
_LEDGER_FULL = os.path.join(os.path.dirname(__file__), "..", "3d",
                            "out", "ledger_full.json")


def _load_real_ledger_or_fail():
    # type: () -> None
    """T9 W2: 真总体钉(③④⑤+材料恒等)的数据闸 —— ledger_full.json 缺失时
    【fail-on-skip】, 不再静默 skip。skip 会让"229 passed"掩盖 3 条未执行
    的钉子(干净克隆假绿); 真钉必须要么真跑、要么响亮失败。数据由
    `blender -b --python 3d/p1a_slice.py -- --g2` 一次性产出(需要 blender
    建 RING/IMPOST 账, 纯 pytest 环境无法自建), 故允许有意跳过者显式
    --deselect 本组钉子, 而不是被动绿灯。"""
    if not os.path.exists(_LEDGER_FULL):
        raise RuntimeError(
            "out/ledger_full.json 不在盘上 —— 真总体钉 fail-on-skip(T9 W2,"
            " 干净克隆不许假绿): 先跑 blender -b --python 3d/p1a_slice.py "
            "-- --g2 产出账本; 或显式 --deselect 真总体钉(不许静默跳过)")


@pytest.fixture(scope="module")
def real_ring_trim_state():
    _load_real_ledger_or_fail()
    led = copy.deepcopy(json.load(open(_LEDGER_FULL)))
    statuses = P.classify_full(led["stones"])
    sc = P.print_scope(led, statuses)
    arch_idx_of = {"ARCH%02d" % (i + 1): i for i in range(P.G2_N_ARCH)}
    rd = P._ring_dedup_dispositions(led, statuses, sc["scope"],
                                    sc["buckets"], arch_idx_of)
    # T9b(B2a): 真总体复测钉(审查 tamper 矩阵的决定性 SILENT 项) ——
    # lift_at 恒零消融时这里必须红(实测回潮 n_colliding=107), 不许
    # "85->0"只活在 blender 那一次运行与报告文字里。rd 已算好, 零额外
    # 成本; 漂移即总体变, 与 RING_TRIM_POPULATION 同族口径。
    fsc = rd["final_scope_check"]
    assert fsc["n_pairs"] == FINAL_SCOPE_N_PAIRS, \
        "真总体复测对数漂移: %d (期望 %d)" % (fsc["n_pairs"],
                                             FINAL_SCOPE_N_PAIRS)
    assert fsc["n_colliding"] == 0, \
        "真总体 ring↔链复测回潮: %d 条 (前3: %r)" % (
            fsc["n_colliding"], fsc["pairs"][:3])
    by_id = {s["id"]: s for s in led["stones"]}
    trim_ids = sorted(sid for sid, st in statuses.items()
                      if st[0] == "ring_trim")
    return by_id, statuses, trim_ids, rd


RING_TRIM_POPULATION = 435   # T8c 复测钉死: 传播守卫后真总体(漂移=总体变)
                             # [拱线族返工清债] 475→435 新实测(圆弧族环带重推导)
FINAL_SCOPE_N_PAIRS = 827    # T9b(B2a/b): ring↔链 bbox 预筛宇宙全量对数
                             # [拱线族返工清债 2026-10-08] 903→827 新实测(重出 g2_report;
                             # 圆弧族环带几何变化 → ring∩链 bbox 预筛宇宙收缩 76 对)
                             # (漂移=总体变; 入库报告与真重放同源钉)


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
