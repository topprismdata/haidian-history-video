# e30_shikongqiao_video/tests/test_p1_ledger.py
import os, sys
import uuid as _uuid
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

# ---- 修复轮(T1 审查裁决): 负控补全 + uuid 主键 + 鲁棒 + fullmatch + 原子写 ----

META = {"curve_hash": "h", "seed": 1, "schema": 1}

def _led(stones, meta=None):
    return {"meta": dict(META if meta is None else meta), "stones": stones}

def _stone(zone="ARCH09", face="EAST", role="RING", course=12, block=7):
    return L.new_stone(zone, face, role, course, block, "ring-wedge",
                       {}, [0, 0, 0, 0, 0, 0], "qingshi")

def test_validate_positive_control_clean():
    # 正对照: 合规账目零错误(保证新增 UUID 检查不误伤 new_stone 产物)
    assert L.validate_ledger(_led([_stone()])) == []

def test_neg_id_dup():
    a, b = _stone(block=7), _stone(block=7)   # 同 id 不同 uuid
    assert a["id"] == b["id"] and a["uuid"] != b["uuid"]
    errs = L.validate_ledger(_led([a, b]))
    assert any(e.startswith("ID_DUP") for e in errs)

def test_neg_support_type():
    s = _stone()
    s["support_edges"] = [{"type": "glue"}]
    errs = L.validate_ledger(_led([s]))
    assert any(e.startswith("SUPPORT_TYPE") for e in errs)

def test_neg_schema_and_meta_missing():
    errs = L.validate_ledger(_led([], {"curve_hash": "h", "seed": 1, "schema": 2}))
    assert any(e.startswith("SCHEMA") for e in errs)
    errs = L.validate_ledger(_led([], {"seed": 1, "schema": 1}))
    assert any(e.startswith("META_MISSING") and "curve_hash" in e for e in errs)

def test_neg_clearance_premature():
    s = _stone()
    s["clearance_manufacturing_mm"] = 0.3
    errs = L.validate_ledger(_led([s]))
    assert any(e.startswith("CLEARANCE_PREMATURE") for e in errs)

def test_neg_uuid_dup():
    a, b = _stone(block=7), _stone(block=8)   # 不同 id, 复制 uuid
    b["uuid"] = a["uuid"]
    errs = L.validate_ledger(_led([a, b]))
    assert any(e.startswith("UUID_DUP") for e in errs)

def test_neg_uuid_bad():
    s = _stone()
    s["uuid"] = "not-a-uuid-4"
    errs = L.validate_ledger(_led([s]))
    assert any(e.startswith("UUID_BAD") for e in errs)

def test_neg_support_edge_shape_no_crash():
    s = _stone()
    s["support_edges"] = ["stone"]   # 非 dict 元素
    errs = L.validate_ledger(_led([s]))   # 必须不抛 AttributeError
    assert any(e.startswith("SUPPORT_EDGE_SHAPE") for e in errs)

def test_stone_missing_id_validate_and_query_robust():
    s = _stone()
    del s["id"]
    led = _led([s])
    errs = L.validate_ledger(led)
    assert any(e.startswith("ID_MISSING") for e in errs)
    assert L.query(led, zone="ARCH09") == []      # .get 路径, 不 KeyError
    assert len(L.query(led)) == 1

def test_id_fullmatch_rejects_trailing_newline():
    s = _stone()
    s["id"] = "ARCH09.EAST.RING.C12.B07\n"
    errs = L.validate_ledger(_led([s]))
    assert any("ID_COORD" in e for e in errs)

def test_save_ledger_atomic_survives_dump_failure(tmp_path, monkeypatch):
    led = _led([_stone()])
    p = str(tmp_path / "ledger.json")
    L.save_ledger(led, p)
    with open(p, "r", encoding="utf-8") as f:
        before = f.read()
    def boom(*a, **k):
        raise RuntimeError("boom")
    monkeypatch.setattr(L.json, "dump", boom)
    with pytest.raises(RuntimeError):
        L.save_ledger(led, p)
    with open(p, "r", encoding="utf-8") as f:
        assert f.read() == before        # 原文件未被截断(原子写)
    assert [f for f in os.listdir(str(tmp_path)) if ".tmp" in f] == []  # 无残留临时片
