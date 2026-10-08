# -*- coding: utf-8 -*-
"""P3-T4 渲染侧参数单源(film_geometry)测试.

计划 Task 4 Step 1 原文三支(锚点确定性 / 桥体净空 / λ下沉量级) + 合同三支
(home_position 对账逐位 / 剪影证据字段 / 机位表 phase 词表 —— T5 消费面).
净空反查独立走 geom_math(P2 几何单源: hw=width_at, deck_z), 与被测模块
不共享 import 别名; 只读 3d/out/ledger_sequenced.json; blender-free;
Python 3.9.6。
"""
import json
import os
import random
import sys

import pytest

REPO3D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_3D = os.path.join(REPO3D, "3d")
for _p in (_3D, os.path.join(_3D, "film")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import geom_math as GM  # noqa: E402  净空反查单源(P2 只读)

from film_geometry import (  # noqa: E402
    CAMERA_TRACKS,
    SILHOUETTE_SLOTS,
    WEDGE_DROP_M,
    home_position,
    lift_anchor,
    yard_anchor,
)

_LEDGER_PATH = os.path.join(_3D, "out", "ledger_sequenced.json")
_POSES = {"lever", "chisel", "crowbar"}
_EPS = 1e-9


def _sample_ids(n, seed):
    """真账随机 n 石(固定种子 → 抽样本身确定性)."""
    with open(_LEDGER_PATH, "r", encoding="utf-8") as fh:
        stones = json.load(fh)["stones"]
    return [s["id"] for s in random.Random(seed).sample(stones, n)]


def _zone_family_ids():
    """每 (zone, family) 组合抽首块: 17×4=68, 覆盖 yard 网格全域."""
    with open(_LEDGER_PATH, "r", encoding="utf-8") as fh:
        stones = json.load(fh)["stones"]
    seen = {}
    for s in stones:
        seen.setdefault((s["id"].split(".")[0], s["family"]), s["id"])
    assert len(seen) == 17 * 4          # 网格覆盖面前置自检(账缺陷早爆)
    return [seen[k] for k in sorted(seen)]


# ── 计划 Task 4 Step 1 原文三支 ──

def test_anchors_deterministic():
    for sid in _sample_ids(40, seed=1):
        assert yard_anchor(sid) == yard_anchor(sid)
        assert lift_anchor(sid) == lift_anchor(sid)
        assert home_position(sid) == home_position(sid)
    a = yard_anchor(_sample_ids(1, seed=2)[0])
    assert isinstance(a, tuple) and len(a) == 3
    assert all(isinstance(v, float) for v in a)


def test_yield_no_overlap_with_body():
    # yard: y 向在 hw(x,z)+0.5m 外(设计主判据; 兜底判据 deck+2m 由 z=deck+1
    # 构造上不满足, 故 y 判必须真过 —— 双断言防"兜底掩目标")
    for sid in _zone_family_ids():
        x, y, z = yard_anchor(sid)
        clear_y = abs(y) >= GM.width_at(x, z) + 0.5 - _EPS
        assert clear_y, (sid, x, y, z)
        assert clear_y or z >= GM.deck_z(x) + 2.0 - _EPS
    # lift: z 判 deck_z+2m(就位位正上方过路点; y 在体内合法, 走 z 判)
    for sid in _sample_ids(100, seed=3):
        x, y, z = lift_anchor(sid)
        assert z >= GM.deck_z(x) + 2.0 - _EPS, (sid, x, y, z)
    # 四族在任一 zone 内码位互异(散列定序双射占列, 无叠码)
    zone_ids = _zone_family_ids()
    cells = {yard_anchor(sid)[:2] for sid in zone_ids[:4]}   # sorted→ARCH01 四族
    assert len(cells) == 4, cells


def test_wedge_drop_positive_small():
    assert isinstance(WEDGE_DROP_M, float)
    assert 0.0 < WEDGE_DROP_M < 0.1


# ── 合同(T5 消费面) ──

def test_home_position_matches_ledger():
    with open(_LEDGER_PATH, "r", encoding="utf-8") as fh:
        idx = {s["id"]: s["transform"] for s in json.load(fh)["stones"]}
    assert len(idx) == 5935              # 幻影 2004 + 日程 3931, 全账可查
    for sid in random.Random(7).sample(sorted(idx), 100):
        assert home_position(sid) == tuple(idx[sid][:3]), sid
    with pytest.raises(KeyError):        # 未知 id 必硬错, 防静默 0 位
        home_position("ARCH99.EAST.RING.C00.B00")


def test_silhouette_evidence_fields():
    assert 0 < len(SILHOUETTE_SLOTS) <= 6
    for slot in SILHOUETTE_SLOTS:
        assert set(slot) >= {"pos", "pose", "evidence"}
        assert slot["pose"] in _POSES
        assert isinstance(slot["evidence"], str) and slot["evidence"].strip()
        assert "C:A4" in slot["evidence"]
        assert len(slot["pos"]) == 3
        assert all(isinstance(v, (int, float)) for v in slot["pos"])
    assert {s["pose"] for s in SILHOUETTE_SLOTS} == _POSES   # 三形制齐备


def test_camera_tracks_phase_keys():
    # T5 按 film_state.phase 字段取机位: 键面必须恰为三段词表
    assert set(CAMERA_TRACKS) == {"BUILD", "DECENTER", "DONE"}
    for phase, cam in CAMERA_TRACKS.items():
        assert isinstance(cam["cam_id"], str) and cam["cam_id"]
        assert cam["projection"] in ("ORTHO", "PERSP")
        locs = [cam[k] for k in ("loc", "loc_start", "loc_end") if k in cam]
        assert locs, phase               # 至少一个机位坐标(缓推段给起讫)
        for loc in locs:
            assert len(loc) == 3
            assert all(isinstance(v, (int, float)) for v in loc)
