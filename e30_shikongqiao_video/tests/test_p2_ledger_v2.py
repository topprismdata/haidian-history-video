# e30_shikongqiao_video/tests/test_p2_ledger_v2.py
# -*- coding: utf-8 -*-
"""P2-T1 ledger schema v2: capacity_curve 支撑边 + inferred_construction + v1→v2 迁移。

schema v2 不改 meta.schema 判别值(SCHEMA 保持 1): 既有负控
(test_p1_ledger.test_neg_schema_and_meta_missing)钉死 schema==2 必须报 SCHEMA 错,
正控钉死 schema==1 必须零错; 同时 brief 要求迁移后 validate==[]。三条约束联立
唯一解 = v2 形态由 support_edge 的 capacity_curve + evidence 枚举表达, 迁移是原地
形制改写且幂等。

brief Step1 例「curve[(0,1.0),(5,0.5),(9,0.0)] seq=2→0.75」与同节定义的线性插值
不自洽(2/5 处线性值是 0.8, 半值点 0.75 对应 seq=2.5), 按线性语义实现并以 2.5→0.75
保留 brief 的半值检查点。
"""
import json
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "3d"))
import ledger as L

META = {"curve_hash": "h", "seed": 1, "schema": 1}
CURVE3 = [[0, 1.0], [5, 0.5], [9, 0.0]]


def _led(stones):
    return {"meta": dict(META), "stones": stones}


def _stone(zone="ARCH09", face="EAST", role="RING", course=12, block=7,
           evidence="ashlar_truth"):
    return L.new_stone(zone, face, role, course, block, "ring-wedge",
                       {}, [0, 0, 0, 0, 0, 0], "qingshi", evidence=evidence)


def _v1_edge(**kw):
    e = {"target": "ARCH09.EAST.RING.C11.B03", "type": "centering",
         "active_from": 3, "active_to": 7, "contact": "seat"}
    e.update(kw)
    return e


def _v2_edge(curve=None, **kw):
    e = {"target": "ARCH09.EAST.RING.C11.B03", "type": "centering",
         "capacity_curve": CURVE3 if curve is None else curve,
         "contact": "seat"}
    e.update(kw)
    return e


# ---- 证据枚举 ----

def test_inferred_construction_evidence_legal_and_invented_illegal():
    assert L.validate_ledger(_led([_stone(evidence="inferred_construction")])) == []
    errs = L.validate_ledger(_led([_stone(evidence="invented")]))
    assert any(e.startswith("EVIDENCE") for e in errs)


# ---- 旧形拒收 / 新形合法 / 迁移 ----

def test_unmigrated_v1_edge_reports_support_shape():
    s = _stone()
    s["support_edges"] = [_v1_edge()]
    errs = L.validate_ledger(_led([s]))
    assert any(e.startswith("SUPPORT_SHAPE") for e in errs)


def test_v2_edge_validates_clean():
    s = _stone()
    s["support_edges"] = [_v2_edge()]
    assert L.validate_ledger(_led([s])) == []


def test_migrate_v1_to_v2_then_validate_clean():
    s = _stone()
    s["support_edges"] = [_v1_edge()]
    led = _led([s])
    out = L.migrate_v1_to_v2(led)
    assert out is led
    assert L.validate_ledger(led) == []
    assert led["meta"]["schema"] == 1  # 判别值不动: v2 由边形制表达
    e = led["stones"][0]["support_edges"][0]
    assert e["capacity_curve"] == [[3, 1.0], [7, 0.0]]
    assert "active_from" not in e and "active_to" not in e
    assert e["target"] == "ARCH09.EAST.RING.C11.B03"
    assert e["type"] == "centering" and e["contact"] == "seat"


def test_migrate_is_idempotent():
    s = _stone()
    s["support_edges"] = [_v1_edge(), _v2_edge()]
    led = _led([s])
    L.migrate_v1_to_v2(led)
    once = json.dumps(led, sort_keys=True)
    L.migrate_v1_to_v2(led)
    assert json.dumps(led, sort_keys=True) == once


def test_migrate_touches_edgeless_ledger_unchanged():
    led = _led([_stone(), _stone(zone="ARCH10", block=2)])
    before = json.dumps(led, sort_keys=True)
    L.migrate_v1_to_v2(led)
    assert json.dumps(led, sort_keys=True) == before


def test_migrated_g2_style_v1_ledger_replays_green():
    # G2 工件形态: 全账无支撑边; v2 下 validate 依旧零错
    led = _led([_stone(), _stone(zone="F01", role="PIER", course=3, block=1)])
    assert L.validate_ledger(L.migrate_v1_to_v2(led)) == []


def test_migrate_open_ended_and_immediate_release_edges():
    # I1 新语义下的单侧键契约: from-only=起点后永久(右钳保留), 起点前不存在(左钳 0.0);
    # to-only=[[to,0.0]] 全区间 0.0(退化死边).
    s = _stone()
    s["support_edges"] = [{"target": "t", "type": "temporary", "active_from": 2}]
    s2 = _stone(zone="ARCH10", block=1)
    s2["support_edges"] = [{"target": "t", "type": "fill", "active_to": 6}]
    led = _led([s, s2])
    L.migrate_v1_to_v2(led)
    assert L.validate_ledger(led) == []
    assert led["stones"][0]["support_edges"][0]["capacity_curve"] == [[2, 1.0]]
    assert L.edge_capacity(led["stones"][0]["support_edges"][0], 0) == pytest.approx(0.0)
    assert L.edge_capacity(led["stones"][0]["support_edges"][0], 100) == pytest.approx(1.0)
    assert L.edge_capacity(led["stones"][1]["support_edges"][0], 0) == pytest.approx(0.0)
    assert L.edge_capacity(led["stones"][1]["support_edges"][0], 100) == pytest.approx(0.0)


# ---- edge_capacity 线性插值 + 端值钳制 ----

def test_edge_capacity_linear_interpolation():
    e = _v2_edge()
    assert L.edge_capacity(e, 0) == pytest.approx(1.0)
    # brief 例 seq=2→0.75 与线性定义矛盾, 线性值 0.8; 半值点在 2.5
    assert L.edge_capacity(e, 2) == pytest.approx(0.8)
    assert L.edge_capacity(e, 2.5) == pytest.approx(0.75)
    assert L.edge_capacity(e, 5) == pytest.approx(0.5)
    assert L.edge_capacity(e, 7) == pytest.approx(0.25)
    assert L.edge_capacity(e, 9) == pytest.approx(0.0)


def test_edge_capacity_clamps_outside_curve():
    # I1: 左钳=0.0(曲线首点前支撑不存在, spec 00959bf 裁决); 右钳保持末点值.
    e = _v2_edge()
    assert L.edge_capacity(e, 20) == pytest.approx(0.0)
    assert L.edge_capacity(e, -3) == pytest.approx(0.0)


def test_edge_capacity_legacy_or_curveless_edge_is_zero():
    assert L.edge_capacity(_v1_edge(), 4) == pytest.approx(0.0)
    assert L.edge_capacity({}, 4) == pytest.approx(0.0)


# ---- 曲线非法形态 ----

def test_validate_rejects_capacity_increase():
    s = _stone()
    s["support_edges"] = [_v2_edge(curve=[[0, 0.5], [5, 1.0]])]
    errs = L.validate_ledger(_led([s]))
    assert any(e.startswith("CURVE_MONOTONIC") for e in errs)


def test_validate_rejects_non_ascending_event_ids():
    s = _stone()
    s["support_edges"] = [_v2_edge(curve=[[5, 1.0], [5, 0.5]])]
    errs = L.validate_ledger(_led([s]))
    # I5 拆码: x 非升归 CURVE_ORDER, 不再混报 CURVE_MONOTONIC
    assert any(e.startswith("CURVE_ORDER") for e in errs)


def test_validate_rejects_malformed_curve():
    s = _stone()
    s["support_edges"] = [_v2_edge(curve=[[0, 1.0, 2.0]])]
    errs = L.validate_ledger(_led([s]))
    assert any(e.startswith("SUPPORT_SHAPE") for e in errs)
    s2 = _stone(zone="ARCH10", block=1)
    s2["support_edges"] = [_v2_edge(curve=[])]
    errs2 = L.validate_ledger(_led([s2]))
    assert any(e.startswith("SUPPORT_SHAPE") for e in errs2)


# ---- I1 左钳语义 ----

def test_edge_not_alive_before_curve_starts():
    e = _v2_edge(curve=[[8, 1.0], [20, 0.0]])
    assert L.edge_capacity(e, 0) == pytest.approx(0.0)
    assert L.edge_capacity(e, 7.999) == pytest.approx(0.0)
    assert L.edge_capacity(e, 8) == pytest.approx(1.0)
    assert L.edge_capacity(e, 30) == pytest.approx(0.0)


def test_edge_capacity_non_numeric_seq_is_zero():
    # S docstring 精度: 非数值/非有限 seq → 0.0, 不抛 TypeError
    e = _v2_edge()
    assert L.edge_capacity(e, None) == pytest.approx(0.0)
    assert L.edge_capacity(e, "3") == pytest.approx(0.0)
    assert L.edge_capacity(e, [3]) == pytest.approx(0.0)
    assert L.edge_capacity(e, float("nan")) == pytest.approx(0.0)
    assert L.edge_capacity(e, float("inf")) == pytest.approx(0.0)


# ---- I2 migrate 先判后写 ----

def test_migrate_string_window_not_swallowed():
    s = _stone()
    s["support_edges"] = [{"target": "t", "type": "temporary",
                           "active_from": 3, "active_to": "closure+7d"}]
    led = _led([s])
    L.migrate_v1_to_v2(led)
    e = led["stones"][0]["support_edges"][0]
    assert "capacity_curve" not in e
    assert e["active_from"] == 3 and e["active_to"] == "closure+7d"
    errs = L.validate_ledger(led)
    assert any(x.startswith("SUPPORT_SHAPE") and "不可插值" in x
               and "closure+7d" in x for x in errs)
    L.migrate_v1_to_v2(led)  # 幂等: 二次仍不写坏
    assert "capacity_curve" not in led["stones"][0]["support_edges"][0]


def test_migrate_both_null_static_edge_becomes_permanent():
    s = _stone()
    s["support_edges"] = [{"target": "t", "type": "stone",
                           "active_from": None, "active_to": None}]
    led = _led([s])
    L.migrate_v1_to_v2(led)
    e = led["stones"][0]["support_edges"][0]
    assert e["capacity_curve"] == [[0, 1.0]]
    assert "active_from" not in e and "active_to" not in e
    assert L.validate_ledger(led) == []
    assert L.edge_capacity(e, 0) == pytest.approx(1.0)
    assert L.edge_capacity(e, 999) == pytest.approx(1.0)


def test_migrate_from_equals_to_is_instant_release_window():
    # 主控裁决: from==to 瞬时窗 → [[0,1.0],[to,0.0]] (v1 语义 to 之前活着;
    # 独立 [[to,0.0]] 会被 I1 左钳误杀整个 to 之前区间)
    s = _stone()
    s["support_edges"] = [{"target": "t", "type": "temporary",
                           "active_from": 5, "active_to": 5}]
    led = _led([s])
    L.migrate_v1_to_v2(led)
    e = led["stones"][0]["support_edges"][0]
    assert e["capacity_curve"] == [[0, 1.0], [5, 0.0]]
    assert "active_from" not in e and "active_to" not in e
    assert L.validate_ledger(led) == []
    assert L.edge_capacity(e, 0) == pytest.approx(1.0)
    assert L.edge_capacity(e, 3) == pytest.approx(0.4)  # 沿 curve 线性趋零, 不被左钳清零
    assert L.edge_capacity(e, 5) == pytest.approx(0.0)


def test_migrate_reversed_window_refused_and_reported():
    s = _stone()
    s["support_edges"] = [{"target": "t", "type": "temporary",
                           "active_from": 9, "active_to": 3}]
    led = _led([s])
    L.migrate_v1_to_v2(led)
    e = led["stones"][0]["support_edges"][0]
    assert "capacity_curve" not in e  # 不产出必红 curve
    assert e["active_from"] == 9 and e["active_to"] == 3
    errs = L.validate_ledger(led)
    assert any(x.startswith("SUPPORT_WINDOW_ORDER") for x in errs)


# ---- I3 非有限堵 ----

def test_validate_rejects_non_finite_curve_points():
    s = _stone()
    s["support_edges"] = [_v2_edge(curve=[[0, float("nan")], [5, 0.0]])]
    assert any(e.startswith("SUPPORT_SHAPE")
               for e in L.validate_ledger(_led([s])))
    s2 = _stone(zone="ARCH10", block=1)
    s2["support_edges"] = [_v2_edge(curve=[[float("nan"), 1.0], [5, 0.0]])]
    assert any(e.startswith("SUPPORT_SHAPE")
               for e in L.validate_ledger(_led([s2])))
    s3 = _stone(zone="ARCH11", block=1)
    s3["support_edges"] = [_v2_edge(curve=[[0, 1.0], [float("inf"), 0.0]])]
    assert any(e.startswith("SUPPORT_SHAPE")
               for e in L.validate_ledger(_led([s3])))


def test_edge_capacity_non_finite_curve_is_zero_not_phantom():
    # NaN 曾绕过单调闸门(比较全 False)后走线性插值产出 NaN 污染下游
    e = _v2_edge(curve=[[0, 1.0], [float("nan"), 0.0]])
    assert L.edge_capacity(e, 5) == pytest.approx(0.0)


# ---- I4 混形拒 ----

def test_validate_rejects_mixed_curve_and_legacy_keys():
    s = _stone()
    e = _v2_edge()
    e["active_from"] = 3
    s["support_edges"] = [e]
    errs = L.validate_ledger(_led([s]))
    assert any(x.startswith("SUPPORT_SHAPE") and "混形" in x for x in errs)


# ---- I5 拆码: CURVE_ORDER(x 非升) vs CURVE_MONOTONIC(y 回升) ----

def test_curve_order_and_monotonic_are_separate_codes():
    s = _stone()
    s["support_edges"] = [_v2_edge(curve=[[5, 1.0], [2, 0.5]])]  # x 降序 y 合规
    errs = L.validate_ledger(_led([s]))
    assert any(e.startswith("CURVE_ORDER") for e in errs)
    assert not any(e.startswith("CURVE_MONOTONIC") for e in errs)
    s2 = _stone(zone="ARCH10", block=1)
    s2["support_edges"] = [_v2_edge(curve=[[0, 0.5], [5, 1.0]])]  # y 回升 x 合规
    errs2 = L.validate_ledger(_led([s2]))
    assert any(e.startswith("CURVE_MONOTONIC") for e in errs2)
    assert not any(e.startswith("CURVE_ORDER") for e in errs2)


# ---- S: CURVE_RANGE 值域闸 ----

def test_validate_curve_range():
    s = _stone()
    s["support_edges"] = [_v2_edge(curve=[[0, 1.5], [5, 0.0]])]
    assert any(e.startswith("CURVE_RANGE")
               for e in L.validate_ledger(_led([s])))
    s2 = _stone(zone="ARCH10", block=1)
    s2["support_edges"] = [_v2_edge(curve=[[0, 1.0], [5, -0.2]])]
    errs2 = L.validate_ledger(_led([s2]))
    assert any(e.startswith("CURVE_RANGE") for e in errs2)
    assert not any(e.startswith("CURVE_MONOTONIC") for e in errs2)  # y 降序合规


# ---- S: known_event_seqs 可选交叉闸 (P2-T5 g3_check 用) ----

def test_validate_known_event_seqs_cross_gate():
    s = _stone()
    s["support_edges"] = [_v2_edge(curve=[[0, 1.0], [5, 0.0]])]
    assert L.validate_ledger(_led([s])) == []              # 默认 None 零影响
    assert L.validate_ledger(_led([s]), known_event_seqs={0, 2, 5}) == []
    errs = L.validate_ledger(_led([s]), known_event_seqs={0, 2})
    assert any(e.startswith("CURVE_EVENT_UNKNOWN") for e in errs)
