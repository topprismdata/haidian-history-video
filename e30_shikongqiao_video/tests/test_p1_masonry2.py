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


# ── T3 审查修复: 层高从砖谱自身推导(消层间纵向插穿) ──────────────────
# 真实砖谱层间距不等(p8 的 15 个层间隔 0.144~0.641m); 定高 0.55 会让矮层
# 砖顶插进上层砖体 —— 最差 C0 实高 0.144 却按 0.55 建, 穿 0.406m。
REAL_P8 = os.path.join(os.path.dirname(__file__), "..", "3d",
                       "stones", "stones_p8.json")

# 不等距合成砖谱: 层间隔 0.144 / 0.56, 末层无上层起算线可依
UNEQUAL_SPEC = {"courses": [
    {"z0": 0.146, "blocks": [0.0, 1.0]},
    {"z0": 0.290, "blocks": [0.0, 1.0]},
    {"z0": 0.850, "blocks": [0.0, 1.0]}]}


def _course_idx(stone):
    # ARCH09.EAST.SPANDREL.C00.B00 -> 0
    return int(stone["id"].split(".")[3][1:])


def test_face_stones_derives_heights_from_spec_gaps():
    # course_h 不传(None) -> h_i = z0_{i+1} - z0_i; 末层回退默认层带高
    stones = M2.face_stones(UNEQUAL_SPEC, 8, 1, _hw)
    hs = [s["params"]["h"] for s in stones]
    assert hs == [0.290 - 0.146, 0.850 - 0.290, M2.DEFAULT_COURSE_H]
    # z 中点与上下沿随本层实高走, 不再按定高外扩
    for course, s in zip(UNEQUAL_SPEC["courses"], stones):
        z0, h = course["z0"], s["params"]["h"]
        assert abs(s["transform"][2] - (z0 + h / 2.0)) < 1e-12
        assert s["params"]["hw_b"] == _hw(0.5, z0)
        assert s["params"]["hw_t"] == _hw(0.5, z0 + h)


def test_face_stones_explicit_course_h_is_last_layer_fallback():
    # 显式传参只兜末层; 其余层仍由砖谱推导(等距砖谱下值不变)
    stones = M2.face_stones(UNEQUAL_SPEC, 8, 1, _hw, course_h=0.55)
    assert [s["params"]["h"] for s in stones] == [
        0.290 - 0.146, 0.850 - 0.290, 0.55]


def test_real_p8_spec_has_no_vertical_penetration():
    # 真实砖谱: 任意相邻两层, 下层砖顶不得越过上层砖底
    with open(REAL_P8, "r", encoding="utf-8") as f:
        spec = json.load(f)
    z0s = [c["z0"] for c in spec["courses"]]
    stones = M2.face_stones(spec, 8, 1, _hw)
    hs = [0.0] * len(z0s)
    for s in stones:
        hs[_course_idx(s)] = s["params"]["h"]
    assert hs[:-1] == [z0s[i + 1] - z0s[i] for i in range(len(z0s) - 1)]
    for i, h in enumerate(hs):
        assert h > 0.0, "C%02d 层高非正: %r" % (i, h)
        if i + 1 < len(z0s):
            assert z0s[i] + h <= z0s[i + 1] + 1e-9, "C%02d 顶插穿 C%02d 底" % (
                i, i + 1)


def test_build_face_layer_derives_heights_by_default(tmp_path):
    (tmp_path / "stones_p8.json").write_text(json.dumps(UNEQUAL_SPEC),
                                             encoding="utf-8")
    got = M2.build_face_layer(str(tmp_path), _hw, [8])
    assert [s["params"]["h"] for s in got[:3]] == [
        0.290 - 0.146, 0.850 - 0.290, M2.DEFAULT_COURSE_H]
    # 末层兜底值可透传
    tail = M2.build_face_layer(str(tmp_path), _hw, [8], course_h=0.40)
    assert [s["params"]["h"] for s in tail[:3]] == [
        0.290 - 0.146, 0.850 - 0.290, 0.40]
