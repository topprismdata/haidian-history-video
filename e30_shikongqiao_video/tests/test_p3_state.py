# -*- coding: utf-8 -*-
"""P3-T2 帧状态机测试.

计划 Task 2 Step 1 合成测逐字(已知偏差: 计划稿事件字段写 `stone`, 真账 schema
为 `stone_id` —— 合成数据按真账用 stone_id, 见 p3-task-2-report §偏差)。
另加: stage 边界 / λ 四档梯 / 券架在离场合成测 + 真账末帧 3931 钉 +
幻影 2004 块缺席钉(设计 spec 终态回归口径)。
只读 3d/out 真账工件; blender-free; Python 3.9.6。
"""
import json
import os
import sys

import pytest

REPO3D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_3D = os.path.join(REPO3D, "3d")
for _p in (_3D, os.path.join(_3D, "film")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from film_state import load_pace, stage_at_frame, state_at_frame  # noqa: E402

_SEQ_PATH = os.path.join(_3D, "out", "sequence.json")
_PACE_PATH = os.path.join(_3D, "out", "film", "pace.json")
_LEDGER_PATH = os.path.join(_3D, "out", "ledger_sequenced.json")

_STATE_KEYS = {"stage", "event_cursor", "visible", "centering_up",
               "wedge_lambda", "phase"}


def _mini_pace(n_stage, ev_per, frames_per):
    """n_stage 个 stage、每 stage ev_per 事件 / frames_per 帧的合成 pace."""
    return {"fps": 30, "total_frames": n_stage * frames_per, "stages": [
        {"id": "S%03d" % (i + 1), "first_event": i * ev_per + 1,
         "last_event": (i + 1) * ev_per, "frames": frames_per,
         "pad_frames": 0, "start": i * frames_per,
         "end": (i + 1) * frames_per} for i in range(n_stage)]}


# ── 计划 Task 2 Step 1 逐字(仅 stone→stone_id 按真账 schema 修正) ──

def test_state_at_frame_synthetic():
    pace = _mini_pace(6, 5, 10)
    seq = {"events": [{"seq": i + 1, "etype": "PLACE_STONE",
                       "stone_id": "ARCH01.X.%02d" % i} for i in range(30)]}
    s0 = state_at_frame(pace, seq, 0)      # stage0: 事件1..5 → 前5石
    assert len(s0["visible"]) == 5 and s0["stage"] == 0
    s59 = state_at_frame(pace, seq, 59)    # 末帧 = 30 石全在
    assert len(s59["visible"]) == 30 and s59["event_cursor"] == 30
    # 契约键面与容器类型钉死(T3 对拍 / T5 消费)
    assert set(s0) == _STATE_KEYS
    assert isinstance(s0["visible"], frozenset)
    assert isinstance(s0["centering_up"], frozenset)
    assert isinstance(s0["wedge_lambda"], dict)
    assert isinstance(s0["phase"], str)
    assert s0["wedge_lambda"] == {} and s0["centering_up"] == frozenset()
    assert s0["phase"] == "BUILD"          # 合成账无落架事件 → 恒 BUILD
    # 逐帧: stage 首帧即该 stage 事件全部落地(cursor=stage.last_event)
    for i in range(6):
        st = state_at_frame(pace, seq, i * 10)
        assert st["event_cursor"] == (i + 1) * 5
        assert len(st["visible"]) == (i + 1) * 5


def test_stage_at_frame_boundaries():
    pace = _mini_pace(6, 5, 10)
    for i in range(6):
        assert stage_at_frame(pace, i * 10) == i   # 每 stage start 帧归属本 stage
    assert stage_at_frame(pace, 15) == 1
    assert stage_at_frame(pace, 59) == 5           # total_frames-1 = 末 stage
    with pytest.raises(IndexError):
        stage_at_frame(pace, 60)                   # == total_frames 越界
    with pytest.raises(IndexError):
        stage_at_frame(pace, -1)


def _ladder_events():
    """ARCH01 全档落架梯 + ARCH02 半程波次(同账异孔, 互不串档)."""
    evs = [{"seq": 1, "etype": "DECENTER_START", "hole": "ARCH01",
            "stone_id": "CEN-ARCH01"}]
    for j, lam in enumerate((0.25, 0.5, 0.75, 1.0)):
        evs.append({"seq": 2 + j, "etype": "WEDGE_RELEASE", "hole": "ARCH01",
                    "stone_id": "CEN-ARCH01", "load_lambda": lam})
    evs += [
        {"seq": 6, "etype": "CENTERING_CLEAR", "hole": "ARCH01",
         "stone_id": "CEN-ARCH01"},
        {"seq": 7, "etype": "DECENTER_START", "hole": "ARCH02",
         "stone_id": "CEN-ARCH02"},
        {"seq": 8, "etype": "WEDGE_RELEASE", "hole": "ARCH02",
         "stone_id": "CEN-ARCH02", "load_lambda": 0.5},
    ]
    return evs


def test_wedge_lambda_ladder():
    pace = _mini_pace(8, 1, 10)
    seq = {"events": _ladder_events()}
    # START(λ=0) → 四档 0.25/0.5/0.75/1.0 → CLEAR 后恒 1
    for i, want in enumerate((0.0, 0.25, 0.5, 0.75, 1.0, 1.0)):
        st = state_at_frame(pace, seq, i * 10)
        assert st["wedge_lambda"]["ARCH01"] == want, i
    st7 = state_at_frame(pace, seq, 60)    # cursor=7: ARCH02 刚 START
    assert st7["wedge_lambda"]["ARCH01"] == 1.0    # 已 CLEAR 不被后续波次回改
    assert st7["wedge_lambda"]["ARCH02"] == 0.0    # START 未出档
    st8 = state_at_frame(pace, seq, 70)
    assert st8["wedge_lambda"]["ARCH02"] == 0.5
    # λ universe = 有落架事件的孔(hole 字段, 非全局 17 孔假设)
    assert set(st8["wedge_lambda"]) == {"ARCH01", "ARCH02"}


def test_centering_up_lifecycle():
    """券架在场 = CENTER_ERECT(stage 名后缀) 已越界 且 CENTERING_CLEAR 未越."""
    stages = [
        {"id": "S001", "stage": "ARCH01.IMPOST.C02", "centering_id": None,
         "event_range": [1, 2], "depends_on": [], "evidence": "C:T"},
        {"id": "S002", "stage": "ARCH01.CENTER_ERECT",
         "centering_id": "CEN-ARCH01", "event_range": [3, 3],
         "depends_on": [], "evidence": "C:T"},
        {"id": "S003", "stage": "ARCH01.RING.C01", "centering_id": "CEN-ARCH01",
         "event_range": [4, 5], "depends_on": [], "evidence": "C:T"},
        {"id": "S004", "stage": "DECENTER.DSTART.WAVE", "centering_id": None,
         "event_range": [6, 6], "depends_on": [], "evidence": "C:T"},
        {"id": "S005", "stage": "DECENTER.CLEAR.WAVE", "centering_id": None,
         "event_range": [7, 7], "depends_on": [], "evidence": "C:T"},
    ]
    pace = {"fps": 30, "total_frames": 50, "stages": [
        {"id": s["id"], "first_event": s["event_range"][0],
         "last_event": s["event_range"][1], "frames": 10, "pad_frames": 0,
         "start": 10 * i, "end": 10 * (i + 1)}
        for i, s in enumerate(stages)]}
    seq = {"sequence": stages, "events": [
        {"seq": 1, "etype": "PLACE_STONE", "hole": "ARCH01",
         "stone_id": "ARCH01.A"},
        {"seq": 2, "etype": "PLACE_STONE", "hole": "ARCH01",
         "stone_id": "ARCH01.B"},
        {"seq": 3, "etype": "HOLD_EVENT", "hole": "ARCH01",
         "stone_id": "CEN-ARCH01"},
        {"seq": 4, "etype": "PLACE_STONE", "hole": "ARCH01",
         "stone_id": "ARCH01.C"},
        {"seq": 5, "etype": "PLACE_STONE", "hole": "ARCH01",
         "stone_id": "ARCH01.D"},
        {"seq": 6, "etype": "DECENTER_START", "hole": "ARCH01",
         "stone_id": "CEN-ARCH01"},
        {"seq": 7, "etype": "CENTERING_CLEAR", "hole": "ARCH01",
         "stone_id": "CEN-ARCH01"},
    ]}
    s1 = state_at_frame(pace, seq, 0)      # 立架前: 不在场
    assert s1["centering_up"] == frozenset()
    assert s1["phase"] == "BUILD"
    s2 = state_at_frame(pace, seq, 10)     # CENTER_ERECT stage 帧 → 在场
    assert s2["centering_up"] == frozenset(["CEN-ARCH01"])
    # HOLD_EVENT 的 stone_id 是券架 id, 永不进 visible(只认 PLACE_STONE)
    assert s2["visible"] == frozenset(["ARCH01.A", "ARCH01.B"])
    s4 = state_at_frame(pace, seq, 30)     # DSTART: 仍在场, 波次段
    assert s4["centering_up"] == frozenset(["CEN-ARCH01"])
    assert s4["phase"] == "DECENTER"
    assert s4["wedge_lambda"] == {"ARCH01": 0.0}   # START 未出档
    s5 = state_at_frame(pace, seq, 40)     # CLEAR → 离场, 收尾段
    assert s5["centering_up"] == frozenset()
    assert s5["phase"] == "DONE"
    assert s5["wedge_lambda"] == {"ARCH01": 1.0}


def test_phase_decenter_without_clear():
    """有 START 无 CLEAR 的账(合成小账): DECENTER 段不崩, 恒 DECENTER."""
    pace = _mini_pace(2, 1, 10)
    seq = {"events": [
        {"seq": 1, "etype": "PLACE_STONE", "hole": "ARCH01",
         "stone_id": "ARCH01.A"},
        {"seq": 2, "etype": "DECENTER_START", "hole": "ARCH01",
         "stone_id": "CEN-ARCH01"},
    ]}
    assert state_at_frame(pace, seq, 0)["phase"] == "BUILD"
    assert state_at_frame(pace, seq, 10)["phase"] == "DECENTER"
    assert state_at_frame(pace, seq, 19)["phase"] == "DECENTER"


# ── 真账钉(3d/out 只读) ──

def _real():
    pace = load_pace(_PACE_PATH)
    with open(_SEQ_PATH, encoding="utf-8") as fh:
        seq = json.load(fh)
    return pace, seq


def test_load_pace_real_schema():
    pace = load_pace(_PACE_PATH)
    assert pace["fps"] == 30 and pace["total_frames"] == 7200
    assert len(pace["stages"]) == 408
    assert pace["stages"][0]["start"] == 0
    with pytest.raises(IndexError):
        stage_at_frame(pace, 7200)
    assert stage_at_frame(pace, 7199) == 407


def test_real_last_frame_pin_3931():
    """末帧 = 终态回归口径: 在场集 3931, 券架全卸, λ 全 1, DONE."""
    pace, seq = _real()
    st = state_at_frame(pace, seq, pace["total_frames"] - 1)
    assert st["stage"] == 407 and st["event_cursor"] == 4118
    assert len(st["visible"]) == 3931
    assert st["phase"] == "DONE"
    assert st["centering_up"] == frozenset()
    assert len(st["wedge_lambda"]) == 17
    assert all(v == 1.0 for v in st["wedge_lambda"].values())


def test_real_phantom_2004_never_visible():
    """幻影 2004 块(5935 账面 − 3931 日程)全片永不在场: 无 PLACE_STONE 事件,
    结构上不可见; 末帧 visible 恰等于日程集(不多不少)."""
    pace, seq = _real()
    with open(_LEDGER_PATH, encoding="utf-8") as fh:
        ledger_ids = set(s["id"] for s in json.load(fh)["stones"])
    sched = set(e["stone_id"] for e in seq["events"]
                if e["etype"] == "PLACE_STONE")
    phantom = ledger_ids - sched
    assert len(sched) == 3931
    assert len(phantom) == 2004
    total = pace["total_frames"]
    for f in list(range(0, total, 97)) + [total - 1]:
        assert not (state_at_frame(pace, seq, f)["visible"] & phantom), f
    assert state_at_frame(pace, seq, total - 1)["visible"] == frozenset(sched)
