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
    s = _stone()
    s["support_edges"] = [{"target": "t", "type": "temporary", "active_from": 2}]
    s2 = _stone(zone="ARCH10", block=1)
    s2["support_edges"] = [{"target": "t", "type": "fill", "active_to": 6}]
    led = _led([s, s2])
    L.migrate_v1_to_v2(led)
    assert L.validate_ledger(led) == []
    assert L.edge_capacity(led["stones"][0]["support_edges"][0], 100) == pytest.approx(1.0)
    assert L.edge_capacity(led["stones"][1]["support_edges"][0], 0) == pytest.approx(0.0)


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
    e = _v2_edge()
    assert L.edge_capacity(e, 20) == pytest.approx(0.0)
    assert L.edge_capacity(e, -3) == pytest.approx(1.0)


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
    assert any(e.startswith("CURVE_MONOTONIC") for e in errs)


def test_validate_rejects_malformed_curve():
    s = _stone()
    s["support_edges"] = [_v2_edge(curve=[[0, 1.0, 2.0]])]
    errs = L.validate_ledger(_led([s]))
    assert any(e.startswith("SUPPORT_SHAPE") for e in errs)
    s2 = _stone(zone="ARCH10", block=1)
    s2["support_edges"] = [_v2_edge(curve=[])]
    errs2 = L.validate_ledger(_led([s2]))
    assert any(e.startswith("SUPPORT_SHAPE") for e in errs2)
