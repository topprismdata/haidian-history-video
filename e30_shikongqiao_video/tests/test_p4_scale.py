# P4-T1: scale_params 薄特征审计单测(合成必列/真账如实/账只读)。合成数据+真账只读, blender-free。
# 口径: 本审计=块最小维×scale×1000<floor 的打印可打印性粗筛;
# printcheck.check_stone THIN_WALL=模型侧流形壁厚精检 —— 两口径互为粗筛/精检, 不互替。
import hashlib
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "3d"))

import scale_params as SP
from export_print import _extents_m
from families import family_mesh
from masonry2 import materialize

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(REPO, "3d", "out", "ledger_full.json")
SEG5 = ["ARCH07", "ARCH08", "ARCH09", "ARCH10", "ARCH11"]
# 真账实测(封 sha 80de7a45 账 + floor 1.2mm): 段端剖面收窄块 8 件, w=0.058m -> 1.16mm
REAL_BBOX_THIN = [
    "ARCH07.EAST.BACK.C06.B08",
    "ARCH07.EAST.SPANDREL.C06.B08",
    "ARCH07.WEST.BACK.C06.B08",
    "ARCH07.WEST.SPANDREL.C06.B08",
    "ARCH11.EAST.BACK.C06.B00",
    "ARCH11.EAST.SPANDREL.C06.B00",
    "ARCH11.WEST.BACK.C06.B00",
    "ARCH11.WEST.SPANDREL.C06.B00",
]


def _slab(sid, w, d, h):
    return {"id": sid, "family": "slab", "role_struct": "CORE", "material": "maoshi",
            "params": {"w": w, "d": d, "h": h},
            "transform": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]}


def _wedge(sid, proud, w=1.0, h=0.4, d=1.0):
    return {"id": sid, "family": "wedge-std", "role_struct": "SPANDREL",
            "material": "qingshi",
            "params": {"w": w, "h": h, "d": d, "proud": proud,
                       "back": 0.3, "hw_b": 6.0, "hw_t": 5.9},
            "transform": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]}


def _by_id(feats):
    return {f["stone"]: f for f in feats}


def test_thin_detect_synthetic():
    """手搭 0.02m 薄石 -> 打印当量 0.4mm < 1.2 必列; 厚石/厚浮雕负控必不列; floor 严格小于。"""
    led = {"meta": {"schema": 1}, "stones": [
        _slab("T.THIN.00", 0.5, 0.3, 0.02),   # 0.02m -> 0.4mm < 1.2 必列(bbox_min_dim)
        _slab("T.OK.00", 0.5, 0.3, 0.10),     # 2.0mm 负控: 不列
        _slab("T.EDGE.00", 0.5, 0.3, 0.06),   # 恰在 floor 上(1.2mm): 严格小于 -> 不列
        _wedge("T.SLV.00", 0.004),            # 块最小维 8mm 打得动, 但 proud 浮雕 0.08mm -> face_sliver
        _wedge("T.POK.00", 0.10),             # proud 2.0mm 负控: 不列
    ]}
    feats = SP.thin_features(led)
    m = _by_id(feats)
    assert set(m) == {"T.THIN.00", "T.SLV.00"}
    f = m["T.THIN.00"]
    assert f["where"] == "bbox_min_dim"
    assert abs(f["min_feature_print_mm"] - 0.4) < 1e-9
    s = m["T.SLV.00"]
    assert s["where"] == "face_sliver"
    assert abs(s["min_feature_print_mm"] - 0.08) < 1e-9
    # 块级薄件优先于浮雕细部: 一块既是薄块又带 sub-floor 浮雕 -> 记 bbox_min_dim(整块不可印, 更严)
    # (wedge-std 的 y 向极差 = d + (hw_b-hw_t); 取 hw_b=hw_t 使 y 极差=d, 控制单一变量)
    led2 = {"meta": {"schema": 1},
            "stones": [_wedge("T.BOTH.00", 0.004, w=0.5, h=0.4, d=0.02)]}
    led2["stones"][0]["params"]["hw_t"] = 6.0
    both = _by_id(SP.thin_features(led2))["T.BOTH.00"]
    assert both["where"] == "bbox_min_dim"
    assert abs(both["min_feature_print_mm"] - 0.4) < 1e-9


def test_section5_thin_list_empty_or_documented():
    """真账段内清单: 如实测如实报(8 结构薄件+1198 浮雕细部), 非空则逐条带 m3_note; 禁调 floor 凑空。"""
    with open(LEDGER, "r", encoding="utf-8") as fh:
        led = json.load(fh)
    feats = SP.thin_features(led, zones=SEG5)
    # 真账非空(如实测): 结构薄件恰为 8 件段端剖面块, 且逐 id 对上
    bbox = [f for f in feats if f["where"] == "bbox_min_dim"]
    assert sorted(f["stone"] for f in bbox) == REAL_BBOX_THIN
    for f in bbox:
        assert abs(f["min_feature_print_mm"] - 1.16) < 1e-6
        assert f["m3_note"]
    # 段内普杄件无漏报(负控): 任取厚块不在清单
    listed = set(f["stone"] for f in feats)
    seg_ids = [s["id"] for s in led["stones"] if s["id"].split(".")[0] in SEG5]
    assert len(seg_ids) == 2747
    assert len(feats) == 1202            # 实测: 8 结构薄件 + 1194 浮雕细部(4 件薄 SPANDREL 记 bbox 口径)
    assert len(listed) == len(feats)     # 一石一条, 不重复
    for f in feats:
        assert isinstance(f["m3_note"], str) and f["m3_note"].strip()
    # dims 同口径实证: 报薄石的世界网格极差(export_print.materialize)与族网格极差一致
    by_id = {s["id"]: s for s in led["stones"]}
    for sid in REAL_BBOX_THIN[:2]:
        s = by_id[sid]
        v_loc, _ = family_mesh(s["family"], s["params"])
        v_wld, _ = materialize(s)
        assert min(_extents_m(v_loc)) == min(_extents_m(v_wld))


def _sha256(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _run_cli(out_path):
    import subprocess
    cmd = [sys.executable, os.path.join(REPO, "3d", "scale_params.py"),
           "--ledger", LEDGER, "--zones", ",".join(SEG5), "--out", out_path]
    p = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    assert out_path in p.stdout and "1202" in p.stdout   # CLI 打印计数
    return p


def test_no_ledger_writeback():
    """跑 thin_features + CLI 落盘前后, ledger_full sha256 逐位不变(账不回写)。"""
    sha0 = _sha256(LEDGER)
    with open(LEDGER, "r", encoding="utf-8") as fh:
        led = json.load(fh)
    SP.thin_features(led, zones=SEG5)
    with tempfile.TemporaryDirectory() as td:
        out1 = os.path.join(td, "thin1.json")
        out2 = os.path.join(td, "thin2.json")
        _run_cli(out1)
        _run_cli(out2)
        assert _sha256(LEDGER) == sha0
        # 幂等: 两连跑逐字节同(全局约束)
        with open(out1, "rb") as fh:
            b1 = fh.read()
        with open(out2, "rb") as fh:
            b2 = fh.read()
        assert b1 == b2
        doc = json.loads(b1.decode("utf-8"))
        assert doc["thin_total"] == 1202
        assert doc["by_where"] == {"bbox_min_dim": 8, "face_sliver": 1194}
        assert doc["zones"] == SEG5
        assert doc["stones_scanned"] == 2747
        assert [f["stone"] for f in doc["features"]] == \
            sorted(f["stone"] for f in doc["features"])
        # CLI 侧 excluded_ids 富注记: 8 件结构薄件注记点名 P1 桶 ring_band_overlap
        for f in doc["features"]:
            if f["where"] == "bbox_min_dim":
                assert "excluded_ids.ring_band_overlap" in f["m3_note"]
