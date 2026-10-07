# e30_shikongqiao_video/tests/test_p2_events.py
# -*- coding: utf-8 -*-
"""P2-T3 events.py: 事件词表 + event_ledger schema + validate_event_ledger。

判据(brief 接口节全量): seq 严格递增无洞; etype∈词表; prereq 指向更小 seq 且
存在; CENTERING_CLEAR 前该孔必有 DECENTER_START; WEDGE_RELEASE 的 load_lambda
沿孔严格递增且落在[0,1]; 引用的 stone_id/centering_id 存在于传入集合; 每孔
CLOSE_RING 恰一次且其 prereq 覆盖该孔全部 RING 石(以传入 ledger 石记录列表核,
也接受纯 id 字符串表); DECENTER_START 前该孔 CLOSE→DECENTER 窗口内 HOLD_EVENT
数 ≥ min_hold(默认 3, [工程参数·敏感性]); grade∈{fact,context,inferred}。
blender-free。
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "3d"))
import events as E
import ledger as L

CEN = "CEN-ARCH09"
RING1 = "ARCH09.EAST.RING.C01.B01"
RING2 = "ARCH09.EAST.RING.C01.B02"
RING3 = "ARCH09.EAST.RING.C02.B01"
SPAND = "ARCH09.EAST.SPANDREL.C03.B01"
CHAIN_STONES = [RING1, RING2, SPAND]  # 六事件链账本: 只含其实际砌筑的两块 RING 石
STONES = [RING1, RING2, RING3, SPAND]
CENS = [CEN]


def _ev(*events):
    return {"events": list(events)}


def _chain_close():
    """合法 6 事件链: 立两券石→合龙→三持荷(无落架, 到 CLOSE+HOLD 为止)。"""
    return _ev(
        E.new_event(1, "ARCH09", "PLACE_STONE", stone_id=RING1),
        E.new_event(2, "ARCH09", "PLACE_STONE", stone_id=RING2, prereq=[1]),
        E.new_event(3, "ARCH09", "CLOSE_RING", prereq=[1, 2], grade="inferred"),
        E.new_event(4, "ARCH09", "HOLD_EVENT"),
        E.new_event(5, "ARCH09", "HOLD_EVENT"),
        E.new_event(6, "ARCH09", "HOLD_EVENT"),
    )


def _full_chain():
    """全生命周期 11 事件: 3券石→合龙→3持荷→落架开始→两级卸楔→CLEAR。"""
    return _ev(
        E.new_event(1, "ARCH09", "PLACE_STONE", stone_id=RING1),
        E.new_event(2, "ARCH09", "PLACE_STONE", stone_id=RING2, prereq=[1]),
        E.new_event(3, "ARCH09", "PLACE_STONE", stone_id=RING3, prereq=[2]),
        E.new_event(4, "ARCH09", "CLOSE_RING", stone_id=RING3, prereq=[1, 2, 3],
                    grade="inferred"),
        E.new_event(5, "ARCH09", "HOLD_EVENT"),
        E.new_event(6, "ARCH09", "HOLD_EVENT"),
        E.new_event(7, "ARCH09", "HOLD_EVENT"),
        E.new_event(8, "ARCH09", "DECENTER_START", stone_id=CEN, prereq=[7]),
        E.new_event(9, "ARCH09", "WEDGE_RELEASE", stone_id=CEN, prereq=[8],
                    load_lambda=0.25),
        E.new_event(10, "ARCH09", "WEDGE_RELEASE", stone_id=CEN, prereq=[9],
                    load_lambda=1.0),
        E.new_event(11, "ARCH09", "CENTERING_CLEAR", stone_id=CEN, prereq=[10]),
    )


# ---- 词表 / new_event 形制 ----

def test_event_types_vocab():
    assert E.EVENT_TYPES == ("PLACE_STONE", "CLOSE_RING", "HOLD_EVENT",
                             "DECENTER_START", "WEDGE_RELEASE", "CENTERING_CLEAR",
                             "ADD_FILL")


def test_new_event_shape_and_defaults():
    ev = E.new_event(7, "ARCH09", "CLOSE_RING", prereq=[5, 6])
    assert ev["seq"] == 7 and ev["hole"] == "ARCH09"
    assert ev["etype"] == "CLOSE_RING"
    assert ev["stone_id"] is None
    assert ev["prereq"] == [5, 6]
    assert ev["affects"] == []
    assert ev["load_lambda"] is None
    assert ev["evidence"] == "R?:n"
    assert ev["grade"] == "inferred"


def test_new_event_affects_passthrough():
    aff = [[CEN, [[3, 1.0], [8, 0.0]]]]
    ev = E.new_event(8, "ARCH09", "DECENTER_START", stone_id=CEN, affects=aff)
    assert ev["affects"] == aff


# ---- 正控: 合法链全绿 ----

def test_valid_six_event_chain_green():
    assert E.validate_event_ledger(_chain_close(), CENS, CHAIN_STONES) == []


def test_valid_full_chain_green():
    assert E.validate_event_ledger(_full_chain(), CENS, STONES) == []


def test_stones_accepts_ledger_dicts_as_well_as_ids():
    dicts = [L.new_stone("ARCH09", "EAST", "RING", 1, 1, "f", {}, [0]*16, "q"),
             L.new_stone("ARCH09", "EAST", "RING", 1, 2, "f", {}, [0]*16, "q"),
             L.new_stone("ARCH09", "EAST", "RING", 2, 1, "f", {}, [0]*16, "q"),
             L.new_stone("ARCH09", "EAST", "SPANDREL", 3, 1, "f", {}, [0]*16, "q")]
    assert E.validate_event_ledger(_full_chain(), CENS, dicts) == []


# ---- seq 严格递增无洞 ----

def test_out_of_order_seq_red():
    led = _chain_close()
    led["events"][1]["seq"] = 9  # 乱序: 9 之后回落到 3
    errs = E.validate_event_ledger(led, CENS, STONES)
    assert any(e.startswith("SEQ_ORDER") for e in errs)


def test_duplicate_seq_red():
    led = _chain_close()
    led["events"][2]["seq"] = 2
    errs = E.validate_event_ledger(led, CENS, CHAIN_STONES)
    assert any(e.startswith("SEQ_ORDER") for e in errs)


def test_seq_gap_red():
    led = _chain_close()
    # 末三事件整体后移一位(4,5,6→5,6,7): seq 4 成空洞
    for i in (3, 4, 5):
        led["events"][i]["seq"] += 1
    errs = E.validate_event_ledger(led, CENS, CHAIN_STONES)
    assert any(e.startswith("SEQ_GAP") for e in errs)


def test_seq_must_be_int_red():
    led = _chain_close()
    led["events"][3]["seq"] = "4"
    errs = E.validate_event_ledger(led, CENS, CHAIN_STONES)
    assert any(e.startswith("SEQ_TYPE") for e in errs)
    led2 = _chain_close()
    led2["events"][3]["seq"] = True  # bool 不是合法 seq
    errs2 = E.validate_event_ledger(led2, CENS, CHAIN_STONES)
    assert any(e.startswith("SEQ_TYPE") for e in errs2)


# ---- 词表与分级 ----

def test_unknown_etype_red():
    led = _chain_close()
    led["events"][2]["etype"] = "MAGIC_SNAP"
    errs = E.validate_event_ledger(led, CENS, CHAIN_STONES)
    assert any(e.startswith("ETYPE") for e in errs)


def test_invented_grade_red():
    led = _chain_close()
    led["events"][2]["grade"] = "definitely_happened"
    errs = E.validate_event_ledger(led, CENS, CHAIN_STONES)
    assert any(e.startswith("GRADE") for e in errs)


def test_valid_grades_green():
    led = _chain_close()
    led["events"][0]["grade"] = "fact"
    led["events"][1]["grade"] = "context"
    assert E.validate_event_ledger(led, CENS, CHAIN_STONES) == []


# ---- prereq ----

def test_prereq_pointing_forward_red():
    led = _chain_close()
    led["events"][1]["prereq"] = [3]  # 指向更大 seq
    errs = E.validate_event_ledger(led, CENS, CHAIN_STONES)
    assert any(e.startswith("PREREQ_ORDER") for e in errs)


def test_prereq_unknown_seq_red():
    led = _chain_close()
    led["events"][2]["prereq"] = [1, 2, 99]
    errs = E.validate_event_ledger(led, CENS, CHAIN_STONES)
    assert any(e.startswith("PREREQ_UNKNOWN") for e in errs)


# ---- 引用存在性 ----

def test_unknown_stone_ref_red():
    led = _chain_close()
    led["events"][0]["stone_id"] = "ARCH09.EAST.RING.C09.B09"
    errs = E.validate_event_ledger(led, CENS, CHAIN_STONES)
    assert any(e.startswith("STONE_UNKNOWN") for e in errs)


def test_unknown_centering_ref_red():
    led = _full_chain()
    led["events"][7]["stone_id"] = "CEN-ARCH99"
    errs = E.validate_event_ledger(led, CENS, STONES)
    assert any(e.startswith("CENTERING_UNKNOWN") for e in errs)


# ---- 落架链时序 ----

def test_clear_without_start_red():
    led = _full_chain()
    # 去掉 DECENTER_START 与其 prereq 链条: CLEAR 直接跟 WEDGE_RELEASE
    led["events"] = [e for e in led["events"] if e["etype"] != "DECENTER_START"]
    for e in led["events"]:
        if e["etype"] == "CENTERING_CLEAR":
            e["prereq"] = [9]
    errs = E.validate_event_ledger(led, CENS, STONES)
    assert any(e.startswith("CLEAR_WITHOUT_START") for e in errs)


def test_decenter_before_close_red():
    led = _full_chain()
    for e in led["events"]:
        if e["etype"] == "DECENTER_START":
            e["seq"] = 4
            e["prereq"] = [3]
        if e["etype"] == "CLOSE_RING":
            e["seq"] = 5
    errs = E.validate_event_ledger(led, CENS, STONES)
    assert any(e.startswith("DECENTER_WITHOUT_CLOSE") for e in errs)


# ---- WEDGE_RELEASE λ 单调 ----

def test_wedge_lambda_must_decrease_stepwise_red():
    led = _full_chain()
    lam = [e for e in led["events"] if e["etype"] == "WEDGE_RELEASE"]
    lam[0]["load_lambda"] = 0.75  # 0.75→1.0 仍升, 绿? 不: 改第二级回退
    lam[1]["load_lambda"] = 0.5
    errs = E.validate_event_ledger(led, CENS, STONES)
    assert any(e.startswith("LAMBDA_MONOTONIC") for e in errs)


def test_wedge_lambda_out_of_range_red():
    led = _full_chain()
    lam = [e for e in led["events"] if e["etype"] == "WEDGE_RELEASE"]
    lam[1]["load_lambda"] = 1.5
    errs = E.validate_event_ledger(led, CENS, STONES)
    assert any(e.startswith("LAMBDA_RANGE") for e in errs)


def test_wedge_lambda_missing_red():
    led = _full_chain()
    lam = [e for e in led["events"] if e["etype"] == "WEDGE_RELEASE"]
    lam[0]["load_lambda"] = None
    errs = E.validate_event_ledger(led, CENS, STONES)
    assert any(e.startswith("LAMBDA_MISSING") for e in errs)


def test_wedge_lambda_from_zero_green():
    # spec: λ∈{0,.25,.5,.75,1} 逐档核, 首档 0 合法
    led = _full_chain()
    lam = [e for e in led["events"] if e["etype"] == "WEDGE_RELEASE"]
    lam[0]["load_lambda"] = 0.0
    lam[1]["load_lambda"] = 0.5
    assert E.validate_event_ledger(led, CENS, STONES) == []


# ---- CLOSE_RING 恰一次 + prereq 覆盖全 RING ----

def test_close_ring_missing_one_stone_prereq_red():
    led = _chain_close()
    led["events"][2]["prereq"] = [1]  # 漏 RING2
    errs = E.validate_event_ledger(led, CENS, CHAIN_STONES)
    assert any(e.startswith("CLOSE_RING_PREREQ") for e in errs)


def test_close_ring_two_per_hole_red():
    led = _chain_close()
    led["events"].append(
        E.new_event(7, "ARCH09", "CLOSE_RING", prereq=[1, 2], grade="inferred"))
    errs = E.validate_event_ledger(led, CENS, CHAIN_STONES)
    assert any(e.startswith("CLOSE_RING_DUP") for e in errs)


def test_ring_stone_with_no_place_event_red():
    # 账本含 RING3(该孔第三块券石)但事件流从不砌筑它 → CLOSE 的 prereq 必缺它
    led = _chain_close()
    errs = E.validate_event_ledger(led, CENS, STONES)
    assert any(e.startswith("CLOSE_RING_PREREQ") for e in errs)


def test_ring_stone_without_close_red():
    # 账里有 RING 石(ARCH10)但事件流从不合龙该孔
    led = _chain_close()
    led["events"].append(
        E.new_event(7, "ARCH10", "PLACE_STONE",
                    stone_id="ARCH10.EAST.RING.C01.B01"))
    stones = CHAIN_STONES + ["ARCH10.EAST.RING.C01.B01"]
    errs = E.validate_event_ledger(led, CENS, stones)
    assert any(e.startswith("CLOSE_RING_MISSING") for e in errs)


# ---- MIN_HOLD ----

def test_decenter_with_insufficient_hold_red():
    led = _full_chain()
    # 只留 2 个持荷事件(默认 min_hold=3)
    led["events"] = [e for e in led["events"] if not (
        e["etype"] == "HOLD_EVENT" and e["seq"] == 7)]
    for e in led["events"]:
        if e["seq"] >= 8:
            e["seq"] -= 1
        e["prereq"] = [p - 1 if p >= 7 else p for p in e["prereq"]]
    errs = E.validate_event_ledger(led, CENS, STONES)
    assert any(e.startswith("HOLD_INSUFFICIENT") for e in errs)


def test_min_hold_parameter_lowers_bar():
    led = _full_chain()
    led["events"] = [e for e in led["events"] if not (
        e["etype"] == "HOLD_EVENT" and e["seq"] in (6, 7))]
    k = 0
    for e in led["events"]:
        if e["seq"] >= 6:
            e["seq"] -= 2
        e["prereq"] = [p - 2 if p >= 6 else p for p in e["prereq"]]
    assert E.validate_event_ledger(led, CENS, STONES, min_hold=1) == []
