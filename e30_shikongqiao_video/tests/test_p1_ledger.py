# e30_shikongqiao_video/tests/test_p1_ledger.py
import json, os, sys, uuid as _uuid
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "3d"))
import ledger as L

def test_family_key_topology_not_coords():
    k = L.family_key("ARCH09", "EAST", "RING", 12, 7)
    assert k == "ARCH09.EAST.RING.C12.B07"
    # id 不含坐标: 同一键在曲线重标定后不变(纪律由 validate 保证无浮点入 id)
    assert not any(ch in k for ch in ".0123456789-") or k.count(".") == 4

def test_new_stone_uuid_unique_and_lineage():
    a = L.new_stone("ARCH09", "EAST", "RING", 12, 7, "ring-wedge",
                    {"w": 0.7}, [0, 0, 0, 0, 0, 0], "qingshi")
    b = L.new_stone("ARCH09", "EAST", "RING", 12, 8, "ring-wedge",
                    {"w": 0.7}, [1, 0, 0, 0, 0, 0], "qingshi")
    assert a["uuid"] != b["uuid"]
    _uuid.UUID(a["uuid"])  # 合法 UUID4
    assert a["lineage"] == {"parent_id": None, "replaces": None}
    assert a["evidence"] == "ashlar_truth"
    assert a["joint_historical_mm"] == 10.0
    assert a["clearance_manufacturing_mm"] is None  # 导出前不许有制造间隙

def test_validate_rejects_coord_in_id_and_bad_evidence():
    s = L.new_stone("ARCH09", "EAST", "RING", 12, 7, "ring-wedge", {}, [0]*6, "qingshi")
    s["id"] = "ARCH09.EAST.RING.C12.07x3.21"   # 坐标混入 id
    led = {"meta": {"curve_hash": "h", "seed": 1, "schema": 1}, "stones": [s]}
    errs = L.validate_ledger(led)
    assert any("ID_COORD" in e for e in errs)
    s["id"] = "ARCH09.EAST.RING.C12.B07"; s["evidence"] = "guess"
    errs = L.validate_ledger(led)
    assert any("EVIDENCE" in e for e in errs)

def test_roundtrip_and_query(tmp_path):
    led = {"meta": {"curve_hash": "h", "seed": 1, "schema": 1}, "stones": [
        L.new_stone("ARCH09", "EAST", "RING", 12, 7, "ring-wedge", {}, [0]*6, "qingshi"),
        L.new_stone("ARCH09", "EAST", "SPANDREL", 3, 2, "wedge-std", {}, [0]*6, "qingshi"),
        L.new_stone("ARCH09", "EAST", "RAIL", 0, 1, "rail-post", {}, [0]*6, "marble")]}
    p = str(tmp_path / "ledger.json")
    L.save_ledger(led, p)
    got = L.load_ledger(p)
    assert len(got["stones"]) == 3
    assert len(L.query(got, role="RING")) == 1
    assert len(L.query(got, material="marble")) == 1
    assert len(L.query(got, zone="ARCH09", role="SPANDREL")) == 1
