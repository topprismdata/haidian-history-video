# -*- coding: utf-8 -*-
"""P1-T3 面石层生成器单测(合成 spec, 不依赖 blender; hw_fn 依赖注入)。"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "3d"))
import masonry2 as M2  # noqa: E402

SPEC = {"courses": [
    {"z0": 2.0, "blocks": [{"x0": 0.0, "x1": 1.2}, {"x0": 1.2, "x1": 2.0}]},
    {"z0": 2.55, "blocks": [{"x0": 0.0, "x1": 0.8}, {"x0": 0.8, "x1": 2.0}]}]}


def _hw(x, z):
    return 6.0 - 0.02 * (z - 2.0)


def test_face_stones_ids_and_depths():
    stones = M2.face_stones(SPEC, 8, 1, _hw, course_h=0.55)
    assert len(stones) == 4
    ids = [s["id"] for s in stones]
    assert ids[0] == "ARCH09.EAST.SPANDREL.C00.B00"
    assert ids[3] == "ARCH09.EAST.SPANDREL.C01.B01"
    # 顺丁相间: 同层奇偶块深不同(顺1.2/丁2.4 或参数表), 且都>0.5
    d0 = stones[0]["params"]["d"]
    d1 = stones[1]["params"]["d"]
    assert d0 > 0.5 and d1 > 0.5 and abs(d0 - d1) > 0.3
    # 间隙两量分离: 历史缝10mm, 制造间隙未定
    assert all(s["joint_historical_mm"] == 10.0 for s in stones)
    assert all(s["clearance_manufacturing_mm"] is None for s in stones)


def test_face_stones_mirror_id():
    west = M2.face_stones(SPEC, 8, -1, _hw, course_h=0.55)
    assert west[0]["id"] == "ARCH09.WEST.SPANDREL.C00.B00"


def test_face_stones_accepts_edge_list_blocks():
    # 真实砖谱 stones_pX.json 的 blocks 是沿 x 的界边表, 不是 {x0,x1} 字典
    spec = {"courses": [{"z0": 2.0, "blocks": [0.0, 1.2, 2.0]}]}
    stones = M2.face_stones(spec, 0, 1, _hw, course_h=0.55)
    assert [s["id"] for s in stones] == [
        "ARCH01.EAST.SPANDREL.C00.B00", "ARCH01.EAST.SPANDREL.C00.B01"]
    assert stones[0]["params"]["w"] == 1.2
    assert stones[1]["params"]["w"] == 0.8


def test_build_face_layer_aggregates_sides(tmp_path):
    (tmp_path / "stones_p8.json").write_text(json.dumps(SPEC), encoding="utf-8")
    got = M2.build_face_layer(str(tmp_path), _hw, [8])
    assert len(got) == 8
    assert [s["id"] for s in got[:2]] == [
        "ARCH09.EAST.SPANDREL.C00.B00", "ARCH09.EAST.SPANDREL.C00.B01"]
    assert all(s["id"].startswith("ARCH09.WEST.") for s in got[4:])
