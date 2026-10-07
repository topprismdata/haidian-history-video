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


# ==== 修复轮新增(审查 H1/H2/H3/M1-M6/L2/L4) ====

# ---- H1 fail-closed 三闸: hole 键与石账 zone 交叉校验 ----

def test_event_hole_not_in_stone_zones_red():
    # S2: 事件 hole 写 'ARCH9' 而石 id zone 是 'ARCH09' → 旗舰判据曾整账假绿
    led = _chain_close()
    for e in led["events"]:
        e["hole"] = "ARCH9"
    errs = E.validate_event_ledger(led, CENS, CHAIN_STONES)
    assert any(e.startswith("HOLE_UNKNOWN") for e in errs)
    assert any(e.startswith("RING_SET_EMPTY") for e in errs)


def test_empty_stone_set_fails_closed_red():
    # S1: 传空石表 → 判据空转, 必须报不得整账绿
    errs = E.validate_event_ledger(_chain_close(), CENS, [])
    assert any(e.startswith("HOLE_UNKNOWN") for e in errs)
    assert any(e.startswith("RING_SET_EMPTY") for e in errs)


def test_ringless_stone_ledger_fails_closed_red():
    # 误接零 RING 角色的石表(如审计副本) → CLOSE 判据将空转必须报
    errs = E.validate_event_ledger(_chain_close(), CENS, [SPAND])
    assert any(e.startswith("RING_SET_EMPTY") for e in errs)


def test_masonry_ref_zone_mismatch_red():
    # 砌筑事件所引石的 zone 必须等于事件 hole
    led = _chain_close()
    led["events"][0]["stone_id"] = "ARCH10.EAST.RING.C01.B01"
    errs = E.validate_event_ledger(
        led, CENS, CHAIN_STONES + ["ARCH10.EAST.RING.C01.B01"])
    assert any(e.startswith("REF_HOLE_MISMATCH") for e in errs)


def test_masonry_without_hole_red():
    # fail-closed: 砌筑事件 hole=None 无法锚定孔, 一律红
    led = _chain_close()
    led["events"][0]["hole"] = None
    errs = E.validate_event_ledger(led, CENS, CHAIN_STONES)
    assert any(e.startswith("REF_HOLE_MISMATCH") for e in errs)


# ---- H2 两条裁决性质回归 pin ----

def test_neighbor_hole_cannot_dilute_hold_red():
    # d929428 裁决: HOLD 按本孔计数, 邻孔持荷不得稀释本孔养护窗
    arch10_spand = "ARCH10.EAST.SPANDREL.C01.B01"
    led = _ev(
        E.new_event(1, "ARCH09", "PLACE_STONE", stone_id=RING1),
        E.new_event(2, "ARCH09", "PLACE_STONE", stone_id=RING2, prereq=[1]),
        E.new_event(3, "ARCH09", "CLOSE_RING", prereq=[1, 2]),
        E.new_event(4, "ARCH10", "HOLD_EVENT"),
        E.new_event(5, "ARCH10", "HOLD_EVENT"),
        E.new_event(6, "ARCH10", "HOLD_EVENT"),
        E.new_event(7, "ARCH09", "DECENTER_START", stone_id=CEN, prereq=[3]),
    )
    errs = E.validate_event_ledger(led, CENS, [RING1, RING2, arch10_spand])
    hits = [e for e in errs if e.startswith("HOLD_INSUFFICIENT")]
    assert len(hits) == 1 and "hole=ARCH09" in hits[0]


def test_wedge_lambda_grouped_per_hole():
    # λ 严格升按孔分组: A/B 交替且各自升 → 绿(全局口径必误红); 仅 B 回退 → 红
    a1, a2 = "ARCH09.EAST.RING.C01.B01", "ARCH09.EAST.RING.C01.B02"
    b1, b2 = "ARCH10.EAST.RING.C01.B01", "ARCH10.EAST.RING.C01.B02"
    ca, cb = "CEN-ARCH09", "CEN-ARCH10"

    def _two_hole_chain(lam_a, lam_b):
        evs = [
            E.new_event(1, "ARCH09", "PLACE_STONE", stone_id=a1),
            E.new_event(2, "ARCH10", "PLACE_STONE", stone_id=b1),
            E.new_event(3, "ARCH09", "PLACE_STONE", stone_id=a2, prereq=[1]),
            E.new_event(4, "ARCH10", "PLACE_STONE", stone_id=b2, prereq=[2]),
            E.new_event(5, "ARCH09", "CLOSE_RING", prereq=[1, 3]),
            E.new_event(6, "ARCH10", "CLOSE_RING", prereq=[2, 4]),
        ]
        s = 7
        for hole in ("ARCH09", "ARCH10") * 3:  # 交替持荷
            evs.append(E.new_event(s, hole, "HOLD_EVENT"))
            s += 1
        evs.append(E.new_event(13, "ARCH09", "DECENTER_START",
                               stone_id=ca, prereq=[11]))
        evs.append(E.new_event(14, "ARCH10", "DECENTER_START",
                               stone_id=cb, prereq=[12]))
        evs.append(E.new_event(15, "ARCH09", "WEDGE_RELEASE", stone_id=ca,
                               prereq=[13], load_lambda=lam_a[0]))
        evs.append(E.new_event(16, "ARCH10", "WEDGE_RELEASE", stone_id=cb,
                               prereq=[14], load_lambda=lam_b[0]))
        evs.append(E.new_event(17, "ARCH09", "WEDGE_RELEASE", stone_id=ca,
                               prereq=[15], load_lambda=lam_a[1]))
        evs.append(E.new_event(18, "ARCH10", "WEDGE_RELEASE", stone_id=cb,
                               prereq=[16], load_lambda=lam_b[1]))
        return _ev(*evs)

    green = _two_hole_chain((0.25, 1.0), (0.25, 1.0))
    assert E.validate_event_ledger(green, [ca, cb], [a1, a2, b1, b2]) == []

    red = _two_hole_chain((0.25, 1.0), (0.75, 0.25))
    errs = E.validate_event_ledger(red, [ca, cb], [a1, a2, b1, b2])
    assert any(e.startswith("LAMBDA_MONOTONIC") and "hole=ARCH10" in e
               for e in errs)
    assert not any(e.startswith("LAMBDA_MONOTONIC") and "hole=ARCH09" in e
                   for e in errs)


# ---- H3 引用类分流 + affects 逐条核 ----

def test_masonry_ref_to_centering_red():
    # R1/R5 形: 砌筑事件挂券架 id, 笔误必须可见
    led = _chain_close()
    led["events"][0]["stone_id"] = CEN
    errs = E.validate_event_ledger(led, CENS, CHAIN_STONES)
    assert any(e.startswith("REF_CLASS_MISMATCH") for e in errs)


def test_decentering_ref_to_stone_red():
    # R2 形: 落架事件挂石 id
    led = _full_chain()
    led["events"][7]["stone_id"] = SPAND
    errs = E.validate_event_ledger(led, CENS, STONES)
    assert any(e.startswith("REF_CLASS_MISMATCH") for e in errs)


def test_affects_ref_unknown_red():
    led = _full_chain()
    led["events"][4]["affects"] = [["ARCH99.EAST.RING.C01.B01", [[3, 1.0]]]]
    led["events"][5]["affects"] = [["CEN-ARCH99", [[3, 1.0]]]]
    errs = E.validate_event_ledger(led, CENS, STONES)
    assert sum(1 for e in errs if e.startswith("AFFECT_REF_UNKNOWN")) == 2


def test_affects_shape_red():
    led = _full_chain()
    led["events"][4]["affects"] = [["only_ref"]]            # 非二元组
    led["events"][5]["affects"] = [[CEN, []]]               # 空 curve
    led["events"][6]["affects"] = [[CEN, [["3", 1.0]]]]     # x 非数值
    led["events"][7]["affects"] = [[CEN, [[3, float("nan")]]]]  # 非有限
    errs = E.validate_event_ledger(led, CENS, STONES)
    assert sum(1 for e in errs if e.startswith("AFFECT_SHAPE")) == 4


def test_affects_seq_unknown_red():
    led = _full_chain()
    led["events"][4]["affects"] = [[CEN, [[404, 1.0]]]]
    errs = E.validate_event_ledger(led, CENS, STONES)
    assert any(e.startswith("AFFECT_SEQ_UNKNOWN") for e in errs)


def test_affects_valid_green():
    led = _full_chain()
    led["events"][4]["affects"] = [[CEN, [[3, 1.0], [8, 0.0]]],
                                   [RING1, [[5, 1.0]]]]
    assert E.validate_event_ledger(led, CENS, STONES) == []


# ---- M1 崩溃路径: 必须返回错误列表, 不得 raise ----

def test_none_id_collections_return_errors_not_crash():
    errs = E.validate_event_ledger(_full_chain(), None, None)
    assert isinstance(errs, list) and errs
    assert any(e.startswith("HOLE_UNKNOWN") for e in errs)


def test_min_hold_none_reported_and_default_restored():
    led = _ev(
        E.new_event(1, "ARCH09", "PLACE_STONE", stone_id=RING1),
        E.new_event(2, "ARCH09", "PLACE_STONE", stone_id=RING2, prereq=[1]),
        E.new_event(3, "ARCH09", "CLOSE_RING", prereq=[1, 2]),
        E.new_event(4, "ARCH09", "DECENTER_START", stone_id=CEN, prereq=[3]),
    )
    errs = E.validate_event_ledger(led, CENS, [RING1, RING2], min_hold=None)
    assert any(e.startswith("MIN_HOLD_TYPE") for e in errs)
    assert any(e.startswith("HOLD_INSUFFICIENT") for e in errs)  # 回退默认 3


def test_missing_etype_key_reported_not_crash():
    led = _full_chain()
    del led["events"][7]["etype"]  # DECENTER_START 丢 etype 键
    errs = E.validate_event_ledger(led, CENS, STONES)
    assert any(e.startswith("ETYPE") for e in errs)


# ---- M2 λ 档位栅格 / M3 等值放行 pin ----

def test_wedge_lambda_off_grid_red():
    led = _full_chain()
    lam = [e for e in led["events"] if e["etype"] == "WEDGE_RELEASE"]
    lam[0]["load_lambda"] = 0.33
    lam[1]["load_lambda"] = 0.66
    errs = E.validate_event_ledger(led, CENS, STONES)
    assert sum(1 for e in errs if e.startswith("LAMBDA_STEP")) == 2


def test_wedge_lambda_quarter_grid_green():
    led = _full_chain()
    lam = [e for e in led["events"] if e["etype"] == "WEDGE_RELEASE"]
    lam[0]["load_lambda"] = 0.0
    lam[1]["load_lambda"] = 0.75
    assert E.validate_event_ledger(led, CENS, STONES) == []


def test_wedge_lambda_equal_steps_red():
    # 同档重复释放是账目错误: λ 相等也必须红(钉死 <= 而非 <)
    led = _full_chain()
    lam = [e for e in led["events"] if e["etype"] == "WEDGE_RELEASE"]
    lam[0]["load_lambda"] = 0.25
    lam[1]["load_lambda"] = 0.25
    errs = E.validate_event_ledger(led, CENS, STONES)
    assert any(e.startswith("LAMBDA_MONOTONIC") for e in errs)


# ---- M4 evidence 交付闸(需 require_evidence=True) ----

def test_evidence_placeholder_flagged_only_when_required():
    led = _chain_close()
    assert E.validate_event_ledger(led, CENS, CHAIN_STONES) == []
    errs = E.validate_event_ledger(led, CENS, CHAIN_STONES,
                                   require_evidence=True)
    assert sum(1 for e in errs if e.startswith("EVIDENCE_PLACEHOLDER")) == 6


def test_evidence_format_gate():
    led = _chain_close()
    for i, ev in enumerate(("rubbish", "A", 42, "B14", "C:A3", "B5/B6")):
        led["events"][i]["evidence"] = ev
    errs = E.validate_event_ledger(led, CENS, CHAIN_STONES,
                                   require_evidence=True)
    assert sum(1 for e in errs if e.startswith("EVIDENCE_FORMAT")) == 3
    assert not any(e.startswith("EVIDENCE_PLACEHOLDER") for e in errs)


# ---- M5 seq 起点 ----

def test_seq_start_must_be_zero_or_one():
    led = _chain_close()
    for e in led["events"]:
        e["seq"] += 1  # 2..7
    errs = E.validate_event_ledger(led, CENS, CHAIN_STONES)
    assert any(e.startswith("SEQ_START") for e in errs)
    led2 = _chain_close()
    for e in led2["events"]:
        e["seq"] -= 3  # -2..3
    errs2 = E.validate_event_ledger(led2, CENS, CHAIN_STONES)
    assert any(e.startswith("SEQ_START") for e in errs2)
    led3 = _ev(E.new_event(0, "ARCH09", "PLACE_STONE", stone_id=RING1),
               E.new_event(1, "ARCH09", "PLACE_STONE", stone_id=RING2,
                           prereq=[0]),
               E.new_event(2, "ARCH09", "CLOSE_RING", prereq=[0, 1]))
    assert E.validate_event_ledger(led3, CENS, [RING1, RING2]) == []


# ---- M6 event_seqs 访问器(T5/T8 交叉调用位) ----

def test_event_seqs_accessor_and_t5_wiring():
    assert E.event_seqs(_full_chain()) == list(range(1, 12))
    assert E.event_seqs([]) == []
    import inspect
    assert "known_event_seqs" in inspect.signature(
        L.validate_ledger).parameters


# ---- L2 隔离的 DECENTER_WITHOUT_CLOSE 用例 ----

def test_decenter_without_close_isolated_red():
    # B4 形: 整体删 CLOSE 并重排 → 红且无 seq 噪声(旧用例变异不隔离)
    led = _full_chain()
    led["events"] = [e for e in led["events"]
                     if e["etype"] != "CLOSE_RING"]
    for e in led["events"]:
        if e["seq"] >= 5:
            e["seq"] -= 1
        e["prereq"] = [p - 1 if p >= 4 else p for p in e["prereq"]]
    errs = E.validate_event_ledger(led, CENS, STONES)
    assert any(e.startswith("DECENTER_WITHOUT_CLOSE") for e in errs)
    assert not any(e.startswith(("SEQ_ORDER", "SEQ_GAP", "SEQ_TYPE"))
                   for e in errs)


# ---- L4 affects 深拷贝独立性 ----

def test_new_event_affects_deep_copy_independent():
    aff = [[CEN, [[3, 1.0]]]]
    ev = E.new_event(8, "ARCH09", "DECENTER_START", stone_id=CEN,
                     affects=aff)
    aff[0][1][0][0] = 99
    aff[0][1].append([100, 0.5])
    assert ev["affects"] == [[CEN, [[3, 1.0]]]]
