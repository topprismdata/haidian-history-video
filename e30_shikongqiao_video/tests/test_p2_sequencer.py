# e30_shikongqiao_video/tests/test_p2_sequencer.py
# -*- coding: utf-8 -*-
"""P2-T4 sequencer.py: R0-R7 规则引擎 + frontier 状态机 + 平衡度前缀 + 曲线回写。

判据(brief 接口节全量, 每规则≥1 测):
- R0 每石恰一次/seq 连续/角色可分类/每孔 CLOSE·DECENTER·CLEAR 恰一次;
- R1 墩肩 z 升序; R2 RING prereq ⊇ 立架锚且在立架→合龙窗;
- R3 θ 镜像配对两侧交替, 偶数位前缀 |W_L−W_R|/(W_L+W_R)≤eps
  (负控: 手工把一侧三石前置 → 构造器 raise R3_IMBALANCE);
- R4 CLOSE→≥min_hold 本孔 HOLD→DECENTER→WEDGE λ 全阶{.25,.5,.75,1}→CLEAR;
- R5a 环肩咬合/锁固肩(clipped_by==ring_band ∨ 石底 z≤extrados ∧ 不撞券架)
  在合龙→拆架窗; R5b 其余 SPANDREL/BACK/CORE 在拆架后;
- R6 frontier 状态严格前进 + 跨孔组合表(禁相邻孔同落架/禁跳孔落架);
- R7 PAVING→RAIL/POST→CARVE 全局最后;
- 回写: 原账不动, 副本 support_edges capacity_curve x 全在事件集,
  validate_ledger(known_event_seqs)=[]; 交付闸 validate_event_ledger
  (require_evidence=True)==[] 硬约束(T3 复审 M4 裁决)。
负控五组: 悬空券石/邻孔稀释 HOLD/跳孔落架/单边领先超 ε/CLEAR 无 START 必红。
blender-free; 真账 5935 石全链为存在性 skip 的尾测。
"""
import copy
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "3d"))

import events as E
import ledger as L
import centering as CEN
import geom_math as GM
import facts as F
import sequencer as SQ

MICRO_RING_T = 0.41      # 合成环厚(取非 facts.RING_T 值防巧合)
EPS = 0.15               # [工程参数·敏感性] 与生产同阈
MIN_HOLD = 3
R7_Z = 5.0


# ---------------------------------------------------------------------------
# 合成 3 孔微账(ARCH01..03; 几何全部由 GM 现算, 不硬编码几何值)
# ---------------------------------------------------------------------------

def _micro_ledger():
    led = {"meta": {"schema": L.SCHEMA, "curve_hash": "micro", "seed": 1},
           "stones": []}
    for ai in (0, 1, 2):
        zone = "ARCH%02d" % (ai + 1)
        xc = GM.arch_center_x(ai)
        springer = GM.arch_springer_z(ai)
        crown = GM.arch_crown_z(ai)
        rt = MICRO_RING_T
        # R1: 墩肩四 course(同孔 z 升序)
        for ci, dz in ((0, 0.60), (1, 0.45), (2, 0.30), (3, 0.15)):
            for fi, face in enumerate(("EAST", "WEST")):
                led["stones"].append(L.new_stone(
                    zone, face, "IMPOST", ci, 0, "wedge-std",
                    {"h": 0.1, "w": 1.05, "d": 0.42},
                    [xc + 1.2 * (1 if face == "EAST" else -1), 4.8,
                     springer - dz, 0.0, 0.0, 0.0], "qingshi"))
        # R3: 券石 θ 镜像(9 石: 四对+龙门石)
        angs = [(-88.0, -66.0), (-66.0, -44.0), (-44.0, -22.0),
                (-22.0, -11.0), (-11.0, 11.0), (11.0, 22.0),
                (22.0, 44.0), (44.0, 66.0), (66.0, 88.0)]
        for bi, (t0, t1) in enumerate(angs):
            x_off = 1.0 * (1 if t0 + t1 >= 0 else -1)
            led["stones"].append(L.new_stone(
                zone, "EAST", "RING", 0, bi + 1, "voussoir",
                {"angles": [t0, t1], "ring_t": rt, "xc": xc,
                 "stations": [xc + x_off - 0.4, xc + x_off + 0.4],
                 "n_ring": 9, "k": 0, "lift": 0.0, "through": "full_depth"},
                [xc + x_off, 0.0,
                 F.arch_z(x_off, 0.0, springer, GM.SPANS[ai] / 2.0,
                          GM.arch_rise(ai)) + rt / 2.0,
                 0.0, 0.0, 0.0], "qingshi"))
        # R5a: 锁固肩(底 z ≤ extrados; y 面上不撞券架)
        led["stones"].append(L.new_stone(
            zone, "EAST", "SPANDREL", 0, 0, "wedge-std",
            {"h": 0.7, "w": 0.38, "d": 1.2},
            [xc, 4.8, springer - 0.20, 0.0, 0.0, 0.0], "qingshi"))
        led["stones"].append(L.new_stone(
            zone, "WEST", "BACK", 1, 1, "wedge-std",
            {"h": 0.7, "w": 0.38, "d": 1.2},
            [xc, -4.8, springer - 0.20, 0.0, 0.0, 0.0], "qingshi"))
        # R5b: 其余肩背胞(底 z 高于 extrados 冠)
        hi = crown + rt + 0.5
        led["stones"].append(L.new_stone(
            zone, "EAST", "SPANDREL", 2, 0, "wedge-std",
            {"h": 0.7, "w": 0.38, "d": 1.2},
            [xc, 4.8, hi + 0.35, 0.0, 0.0, 0.0], "qingshi"))
        led["stones"].append(L.new_stone(
            zone, "WEST", "BACK", 1, 0, "wedge-std",
            {"h": 0.7, "w": 0.38, "d": 1.2},
            [xc, -4.8, hi + 0.35, 0.0, 0.0, 0.0], "qingshi"))
        led["stones"].append(L.new_stone(
            zone, "EAST", "CORE", 3, 0, "slab",
            {"bbox": {"x0": xc - 0.5, "x1": xc + 0.5, "y0": -7.0,
                      "y1": 7.0, "z0": hi + 0.9, "z1": hi + 1.5},
             "h": 0.6, "w": 1.0, "d": 14.0, "y_extent": "full_wall"},
            [xc, 0.0, hi + 0.9, 0.0, 0.0, 0.0], "qingshi"))
    # R7: 面上最后四角色(挂 ARCH01; 真账暂无, 形制就绪)
    for role in ("PAVING", "RAIL", "POST", "CARVE"):
        led["stones"].append(L.new_stone(
            "ARCH01", "EAST", role, 9, 0, "wedge-std",
            {"h": 0.3, "w": 0.5, "d": 0.8},
            [GM.arch_center_x(0) - 1.0, 4.8, R7_Z, 0.0, 0.0, 0.0],
            "qingshi"))
    return led


def _micro_centerings():
    return [CEN.build_centering_for_arch(ai, ring_t=MICRO_RING_T)
            for ai in (0, 1, 2)]


@pytest.fixture(name="micro")
def micro_fixture():
    led = _micro_ledger()
    errs = L.validate_ledger(led)
    assert errs == [], "微账自身非法: %s" % errs
    return led


@pytest.fixture(name="built")
def built_fixture(micro):
    res = SQ.build_sequence(micro, _micro_centerings(), eps=EPS,
                            min_hold=MIN_HOLD)
    return res


def _zones(led):
    return sorted(set(s["id"].split(".")[0] for s in led["stones"]))


def _errs(res, led, cens):
    return SQ.check_sequence(res, led, cens, eps=EPS, min_hold=MIN_HOLD)


def _by_hole(events, zone, etype):
    return [e for e in events
            if e.get("hole") == zone and e.get("etype") == etype]


def _resequence(events):
    """保序重编号 seq=1..N(负控重排后的良构化; 陈旧 prereq 留给对应规则抓)。"""
    for k, e in enumerate(events):
        e["seq"] = k + 1
    return events


# ---------------------------------------------------------------------------
# R0 良构性
# ---------------------------------------------------------------------------

def test_r0_wellformed_and_positive_global(built, micro):
    seqs = [e["seq"] for e in built["events"]]
    assert seqs == list(range(1, len(built["events"]) + 1))
    masonry_ids = [e["stone_id"] for e in built["events"]
                   if e["etype"] in E.MASONRY_TYPES and e.get("stone_id")]
    assert sorted(masonry_ids) == sorted(s["id"] for s in micro["stones"])
    errs = _errs(built, micro, _micro_centerings())
    assert errs == [], "正控全绿失败: %s" % errs


def test_r0_hole_lifecycle_once(built, micro):
    for zone in _zones(micro):
        for etype in ("CLOSE_RING", "DECENTER_START", "CENTERING_CLEAR"):
            assert len(_by_hole(built["events"], zone, etype)) == 1, \
                (zone, etype)


def test_r0_unknown_role_fail_closed(micro):
    bad = L.new_stone("ARCH01", "EAST", "DOME", 9, 9, "wedge-std",
                      {"h": 0.1, "w": 0.1, "d": 0.1},
                      [0.0, 0.0, R7_Z, 0.0, 0.0, 0.0], "qingshi")
    led2 = {"meta": micro["meta"], "stones": micro["stones"] + [bad]}
    with pytest.raises(SQ.SequencerError, match="R0_UNKNOWN_ROLE"):
        SQ.build_sequence(led2, _micro_centerings())


# ---------------------------------------------------------------------------
# R1 墩肩 z 升序
# ---------------------------------------------------------------------------

def test_r1_impost_z_ascending(built, micro):
    by_id = {s["id"]: s for s in micro["stones"]}
    for zone in _zones(micro):
        zs = [SQ._stone_xz(by_id[e["stone_id"]])[1]
              for e in built["events"]
              if e["hole"] == zone and e["etype"] == "PLACE_STONE"
              and e["stone_id"].split(".")[2] == "IMPOST"]
        assert len(zs) == 8
        assert all(zs[k + 1] >= zs[k] for k in range(len(zs) - 1))


def test_r1_negative_impost_out_of_order(built, micro):
    evs = copy.deepcopy(built["events"])
    idxs = [i for i, e in enumerate(evs)
            if e["etype"] == "PLACE_STONE"
            and e["stone_id"].split(".")[2] == "IMPOST"
            and e["hole"] == "ARCH01"]
    assert len(idxs) == 8
    # 仅交换 seq 值(时序身份对调): R1 按 seq 排序即见 z 降
    evs[idxs[0]]["seq"], evs[idxs[-1]]["seq"] = \
        evs[idxs[-1]]["seq"], evs[idxs[0]]["seq"]
    errs = _errs({"events": evs}, micro, _micro_centerings())
    assert any(m.startswith("R1_IMPOST_Z") for m in errs), errs[:8]


# ---------------------------------------------------------------------------
# R2 券架先行
# ---------------------------------------------------------------------------

def test_r2_erect_before_ring(built, micro):
    for zone in _zones(micro):
        holds = _by_hole(built["events"], zone, "HOLD_EVENT")
        erect = holds[0]
        assert erect["stone_id"] == "CEN-" + zone
        close = _by_hole(built["events"], zone, "CLOSE_RING")[0]
        rings = [e for e in built["events"]
                 if e["hole"] == zone and e["etype"] == "PLACE_STONE"
                 and e["stone_id"].split(".")[2] == "RING"]
        assert rings
        for e in rings:
            assert erect["seq"] in e["prereq"]
            assert erect["seq"] < e["seq"] < close["seq"]


# ---------------------------------------------------------------------------
# R3 平衡度
# ---------------------------------------------------------------------------

def test_r3_banks_alternate_sides_and_prefix_balanced(built, micro):
    by_id = {s["id"]: s for s in micro["stones"]}
    for zone in _zones(micro):
        rings = [e for e in built["events"]
                 if e["hole"] == zone and e["etype"] == "PLACE_STONE"
                 and e["stone_id"].split(".")[2] == "RING"]
        mids = [SQ._theta_mid(by_id[e["stone_id"]]) for e in rings]
        # 两侧交替: 偶数位(0 基奇数下标)前缀左右重量平衡 ≤ eps
        w_l = w_r = 0.0
        for k, e in enumerate(rings):
            s = by_id[e["stone_id"]]
            w = SQ.stone_weight(s)
            lf = SQ._theta_left_frac(s)
            w_l += w * lf
            w_r += w * (1.0 - lf)
            if (k + 1) % 2 == 0 or k + 1 == len(rings):
                assert abs(w_l - w_r) / (w_l + w_r) <= EPS, (zone, k)


def test_r3_negative_one_side_leads(micro, built):
    """负控: 手工把 ARCH02 一侧三石前置 → 构造器 raise R3_IMBALANCE。"""
    by_hole_ring_order = {}
    for zone in _zones(micro):
        by_hole_ring_order[zone] = [
            e["stone_id"] for e in built["events"]
            if e["hole"] == zone and e["etype"] == "PLACE_STONE"
            and e["stone_id"].split(".")[2] == "RING"]
    tam = [sid for sid in by_hole_ring_order["ARCH02"]
           if SQ._theta_mid({s["id"]: s for s in micro["stones"]}[sid]) < 0]
    moved = tam[:3] + [sid for sid in by_hole_ring_order["ARCH02"]
                       if sid not in tam[:3]]
    by_hole_ring_order["ARCH02"] = moved
    with pytest.raises(SQ.SequencerError, match="R3_IMBALANCE"):
        SQ.build_sequence(micro, _micro_centerings(), eps=EPS,
                          min_hold=MIN_HOLD, ring_order=by_hole_ring_order)


def test_r3_density_invariance(micro):
    """R3 比值对共同密度因子不变(密度 1.0 不引入无出处常数的依据)。"""
    cens = _micro_centerings()
    w1 = SQ.stone_weight(micro["stones"][8], density=1.0)
    w3 = SQ.stone_weight(micro["stones"][8], density=2600.0)
    assert w3 == pytest.approx(w1 * 2600.0)


# ---------------------------------------------------------------------------
# R4 持荷窗口与 λ 全阶
# ---------------------------------------------------------------------------

def test_r4_hold_window_and_lambda_ladder(built, micro):
    for zone in _zones(micro):
        holds = _by_hole(built["events"], zone, "HOLD_EVENT")
        close = _by_hole(built["events"], zone, "CLOSE_RING")[0]["seq"]
        dstart = _by_hole(built["events"], zone, "DECENTER_START")[0]["seq"]
        window = [e for e in holds if close < e["seq"] < dstart]
        assert len(window) >= MIN_HOLD
        lams = [e["load_lambda"] for e in
                _by_hole(built["events"], zone, "WEDGE_RELEASE")]
        assert lams == [0.25, 0.5, 0.75, 1.0]
        clear = _by_hole(built["events"], zone, "CENTERING_CLEAR")[0]
        assert clear["seq"] > _by_hole(built["events"], zone,
                                       "WEDGE_RELEASE")[-1]["seq"]


def test_r4_negative_lambda_ladder_broken(built, micro):
    evs = copy.deepcopy(built["events"])
    w = [e for e in evs if e["hole"] == "ARCH02"
         and e["etype"] == "WEDGE_RELEASE"]
    w[-1]["load_lambda"] = 0.75  # 末档缺失(重复 0.75)
    errs = _errs({"events": evs}, micro, _micro_centerings())
    assert any(m.startswith("R4_LADDER") for m in errs), errs[:8]


# ---------------------------------------------------------------------------
# R5a/R5b 锁固肩与肩背胞
# ---------------------------------------------------------------------------

def test_r5a_shoulder_in_close_clear_window(built, micro):
    by_id = {s["id"]: s for s in micro["stones"]}
    cens = {c["zone"]: c for c in _micro_centerings()}
    n_shoulder = 0
    for zone in _zones(micro):
        close = _by_hole(built["events"], zone, "CLOSE_RING")[0]["seq"]
        clear = _by_hole(built["events"], zone, "CENTERING_CLEAR")[0]["seq"]
        ai = int(zone[4:]) - 1
        for e in built["events"]:
            if e["hole"] != zone or e["etype"] != "PLACE_STONE":
                continue
            s = by_id[e["stone_id"]]
            if s["id"].split(".")[2] not in SQ.FILL_ROLES:
                continue
            x_mid, z_bot, _ = SQ._stone_xz(s)
            extr = F.arch_z(x_mid - GM.arch_center_x(ai), 0.0,
                            GM.arch_springer_z(ai), GM.SPANS[ai] / 2.0,
                            GM.arch_rise(ai)) + MICRO_RING_T
            locked = z_bot <= extr and not any(
                SQ._boxes_collide(SQ._stone_box(s), cb)
                for cb in SQ._centering_boxes_global(cens[zone]))
            if locked:
                n_shoulder += 1
                assert close < e["seq"] < clear
                assert close in e["prereq"]
            else:
                assert e["seq"] > clear
    assert n_shoulder == 6, "每孔恰 2 锁固肩(3 孔共 6), 实得 %d" % n_shoulder


def test_r5b_fill_after_clear(built, micro):
    for zone in _zones(micro):
        clear = _by_hole(built["events"], zone, "CENTERING_CLEAR")[0]["seq"]
        fills = [e for e in built["events"]
                 if e["hole"] == zone and e["etype"] == "PLACE_STONE"
                 and e["stone_id"].split(".")[2] in SQ.FILL_ROLES]
        after = [e for e in fills if e["seq"] > clear]
        assert len(after) == 3, "每孔 3 肩背胞(胞1+背2)在拆架后"


# ---------------------------------------------------------------------------
# R6 frontier 状态机
# ---------------------------------------------------------------------------

def test_r6_trace_legal_and_checker_clean(built, micro):
    trace = built["frontier_trace"]
    assert trace
    per = {}
    for t in trace:
        per.setdefault(t["hole"], []).append(t["state"])
        assert t["state"] in SQ.FRONTIER_STATES
    for zone, states in per.items():
        ranks = [SQ._STATE_RANK[s] for s in states]
        assert ranks == sorted(ranks) and len(set(ranks)) == len(ranks)
    assert SQ.check_frontier(built["events"], _zones(micro)) == []
    # 构造轨迹与重建轨迹同形
    assert SQ.derive_frontier(built["events"]) == trace


def test_r6_nonadjacent_concurrent_decenter_allowed(built, micro):
    """组合表非恒红非恒绿: 隔孔(1,3)同落架(中孔已 CLOSED_SUPPORTED)合法 0 违例。"""
    evs = copy.deepcopy(built["events"])
    blk = [e for e in evs if e["hole"] == "ARCH03"
           and e["etype"] in ("DECENTER_START", "WEDGE_RELEASE",
                              "CENTERING_CLEAR")]
    rest = [e for e in evs if e not in blk]
    # 插到 ARCH01 的 DECENTER_START 之后 → 与 ARCH01 同时落架(非相邻)
    anchor = next(i for i, e in enumerate(rest)
                  if e["etype"] == "DECENTER_START"
                  and e["hole"] == "ARCH01") + 1
    evs2 = _resequence(rest[:anchor] + blk + rest[anchor:])
    errs = SQ.check_frontier(evs2, _zones(micro))
    assert errs == [], errs[:8]


def test_r6_negative_skip_hole_decenter(built, micro):
    """负控: 跳孔落架 —— ARCH03 在邻孔 ARCH02 合龙前落架必红。"""
    evs = copy.deepcopy(built["events"])
    blk = [e for e in evs if e["hole"] == "ARCH03"
           and e["etype"] in ("DECENTER_START", "WEDGE_RELEASE",
                              "CENTERING_CLEAR")]
    rest = [e for e in evs if e not in blk]
    # 插到 ARCH02 立架之后、合龙之前 → ARCH03 落架时 ARCH02 < CLOSED_SUPPORTED
    erect2 = next(i for i, e in enumerate(rest)
                  if e["hole"] == "ARCH02" and e["etype"] == "HOLD_EVENT")
    close2 = next(i for i, e in enumerate(rest)
                  if e["hole"] == "ARCH02" and e["etype"] == "CLOSE_RING")
    anchor = erect2 + 1
    assert anchor <= close2
    evs2 = _resequence(rest[:anchor] + blk + rest[anchor:])
    errs = SQ.check_frontier(evs2, _zones(micro))
    assert any(m.startswith("R6_JUMP_DECENTER") for m in errs), errs[:8]


def test_r6_negative_adjacent_decenter_forbidden(built, micro):
    """组合表第二支: 相邻孔同时 DECENTERING 必红(ARCH02 插入 ARCH01 落架窗)。"""
    evs = copy.deepcopy(built["events"])
    blk = [e for e in evs if e["hole"] == "ARCH02"
           and e["etype"] in ("DECENTER_START", "WEDGE_RELEASE",
                              "CENTERING_CLEAR")]
    rest = [e for e in evs if e not in blk]
    anchor = next(i for i, e in enumerate(rest)
                  if e["etype"] == "DECENTER_START"
                  and e["hole"] == "ARCH01") + 1
    evs2 = _resequence(rest[:anchor] + blk + rest[anchor:])
    errs = SQ.check_frontier(evs2, _zones(micro))
    assert any(m.startswith("R6_ADJ_DECENTERING") for m in errs), errs[:8]


# ---------------------------------------------------------------------------
# R7 面上最后
# ---------------------------------------------------------------------------

def test_r7_paving_rail_carve_last(built, micro):
    evs = built["events"]
    groups = {"PAVING": [], "RAIL_POST": [], "CARVE": []}
    arch_last = 0
    for e in evs:
        sid = e.get("stone_id")
        if e["etype"] != "PLACE_STONE" or not isinstance(sid, str) \
                or sid.count(".") < 3:
            continue
        role = sid.split(".")[2]
        if role == "PAVING":
            groups["PAVING"].append(e["seq"])
        elif role in ("RAIL", "POST"):
            groups["RAIL_POST"].append(e["seq"])
        elif role == "CARVE":
            groups["CARVE"].append(e["seq"])
        else:
            arch_last = max(arch_last, e["seq"])
    assert groups["PAVING"] and groups["RAIL_POST"] and groups["CARVE"]
    assert max(groups["PAVING"]) < min(groups["RAIL_POST"])
    assert max(groups["RAIL_POST"]) < min(groups["CARVE"])
    assert min(groups["PAVING"]) > arch_last


def test_r7_negative_carve_before_paving(built, micro):
    evs = copy.deepcopy(built["events"])
    carve = next(e for e in evs
                 if isinstance(e.get("stone_id"), str)
                 and e["stone_id"].endswith(".CARVE.C09.B00"))
    pav = next(e for e in evs
               if isinstance(e.get("stone_id"), str)
               and e["stone_id"].endswith(".PAVING.C09.B00"))
    evs.remove(carve)
    idx = evs.index(pav)
    evs.insert(idx, carve)
    _resequence(evs)
    errs = _errs({"events": evs}, micro, _micro_centerings())
    assert any(m.startswith("R7_ORDER") for m in errs), errs[:8]


# ---------------------------------------------------------------------------
# stage 分组
# ---------------------------------------------------------------------------

def test_stages_grouping(built):
    stages = built["sequence"]
    assert stages
    assert [s["id"] for s in stages] == \
        ["S%03d" % (i + 1) for i in range(len(stages))]
    lo_prev = 0
    for k, st in enumerate(stages):
        lo, hi = st["event_range"]
        assert lo == lo_prev + 1 and hi >= lo
        lo_prev = hi
        assert st["depends_on"] is not None
        if k > 0:
            assert stages[k - 1]["id"] in st["depends_on"]
        assert st["evidence"] and st["evidence"] != "R?:n"
    assert lo_prev == len(built["events"])
    # 券架相关阶段挂 centering_id
    cen_stages = [s for s in stages if s["centering_id"]]
    assert cen_stages
    assert all(s["centering_id"].startswith("CEN-") for s in cen_stages)
    assert 50 <= len(stages) <= 600


def test_stage_names_cover_phases(built):
    names = " ".join(s["stage"] for s in built["sequence"])
    for token in ("IMPOST", "CENTER_ERECT", "RING", "CLOSE_RING", "SHOULDER",
                  "HOLD", "DECENTER", "FILL", "PAVING", "CARVE"):
        assert token in names, token


# ---------------------------------------------------------------------------
# 回写: 原账不动 + 副本支撑曲线
# ---------------------------------------------------------------------------

def test_writeback_copy_only_and_curves(built, micro):
    before = copy.deepcopy(micro)
    led2 = SQ.apply_support_edges(micro, built)
    assert micro == before, "原账被改动"
    seqs = E.event_seqs(built)
    errs = L.validate_ledger(led2, allow_clearance=False,
                             known_event_seqs=seqs)
    assert errs == [], errs[:8]
    # 每石 ≥1 条支撑边; 依赖券架的石(RING/R5a)恰 2 条(承托+自持)
    n_edges = 0
    for s in led2["stones"]:
        n = len(s["support_edges"])
        assert 1 <= n <= 2, (s["id"], n)
        n_edges += n
    role_of = lambda sid: sid.split(".")[2]
    ring_ids = set(s["id"] for s in micro["stones"]
                   if role_of(s["id"]) == "RING")
    for s in led2["stones"]:
        types = sorted(e["type"] for e in s["support_edges"])
        if s["id"] in ring_ids:
            assert types == ["centering", "stone"], (s["id"], types)


def test_ring_capacity_ladder_via_edge_capacity(built, micro):
    led2 = SQ.apply_support_edges(micro, built)
    evs = built["events"]
    zone = "ARCH02"
    ring = next(s for s in led2["stones"]
                if s["id"].startswith(zone + ".") and ".RING." in s["id"])
    place = next(e["seq"] for e in evs if e["stone_id"] == ring["id"])
    dstart = _by_hole(evs, zone, "DECENTER_START")[0]["seq"]
    wedges = [e["seq"] for e in _by_hole(evs, zone, "WEDGE_RELEASE")]
    clear = _by_hole(evs, zone, "CENTERING_CLEAR")[0]["seq"]
    cen_edge = next(e for e in ring["support_edges"]
                    if e["type"] == "centering")
    assert L.edge_capacity(cen_edge, place - 1) == 0.0   # 左钳: 置放前不存在
    assert L.edge_capacity(cen_edge, place) == 1.0
    assert L.edge_capacity(cen_edge, dstart) == 1.0
    assert L.edge_capacity(cen_edge, wedges[0]) == 0.75
    assert L.edge_capacity(cen_edge, wedges[-1]) == 0.0
    assert L.edge_capacity(cen_edge, clear) == 0.0
    stone_edge = next(e for e in ring["support_edges"]
                      if e["type"] == "stone")
    assert L.edge_capacity(stone_edge, wedges[-1]) == 1.0  # 自持接管
    assert L.edge_capacity(stone_edge, clear + 10) == 1.0


# ---------------------------------------------------------------------------
# 交付闸: require_evidence=True 硬约束(T3 复审 M4)
# ---------------------------------------------------------------------------

def test_delivery_gate_require_evidence_true(built, micro):
    errs = E.validate_event_ledger(
        {"events": built["events"]},
        [c["id"] for c in _micro_centerings()],
        [s["id"] for s in micro["stones"]],
        min_hold=MIN_HOLD, require_evidence=True)
    assert errs == [], errs[:8]
    # 占位证据必红(钉死闸有牙)
    evs = copy.deepcopy(built["events"])
    evs[0]["evidence"] = "R?:n"
    errs = E.validate_event_ledger(
        {"events": evs}, [c["id"] for c in _micro_centerings()],
        [s["id"] for s in micro["stones"]],
        min_hold=MIN_HOLD, require_evidence=True)
    assert any(m.startswith("EVIDENCE_PLACEHOLDER") for m in errs)


# ---------------------------------------------------------------------------
# 负控五组(汇总位: 悬空券石 / 邻孔稀释 HOLD / CLEAR 无 START 在此,
# 其余两支见 R3/R6 测试)
# ---------------------------------------------------------------------------

def test_neg1_floating_voussoir(built, micro):
    """悬空券石: RING 石挪到拆架后置放 → R2_WINDOW 必红。"""
    evs = copy.deepcopy(built["events"])
    ring = next(e for e in evs if e["hole"] == "ARCH02"
                and e["etype"] == "PLACE_STONE"
                and e["stone_id"].split(".")[2] == "RING")
    evs.remove(ring)
    evs.append(ring)
    _resequence(evs)
    errs = _errs({"events": evs}, micro, _micro_centerings())
    assert any(m.startswith("R2_WINDOW") for m in errs), errs[:10]


def test_neg2_neighbor_diluted_hold(built, micro):
    """邻孔稀释 HOLD: ARCH02 窗口内 2 个 HOLD 改挂邻孔 → R4_HOLD 必红。"""
    evs = copy.deepcopy(built["events"])
    close = _by_hole(evs, "ARCH02", "CLOSE_RING")[0]["seq"]
    dstart = _by_hole(evs, "ARCH02", "DECENTER_START")[0]["seq"]
    moved = 0
    for e in evs:
        if e["hole"] == "ARCH02" and e["etype"] == "HOLD_EVENT" \
                and close < e["seq"] < dstart and moved < 2:
            e["hole"] = "ARCH03"
            e["stone_id"] = "CEN-ARCH03"
            moved += 1
    assert moved == 2
    errs = _errs({"events": evs}, micro, _micro_centerings())
    assert any(m.startswith("R4_HOLD") for m in errs), errs[:10]
    assert any("HOLD_INSUFFICIENT" in m for m in errs)


def test_neg3_clear_without_start(built, micro):
    """CLEAR 无 START: 删 ARCH02 落架块 → CLEAR_WITHOUT_START 必红。"""
    evs = copy.deepcopy(built["events"])
    dead = [e for e in evs if e["hole"] == "ARCH02"
            and e["etype"] in ("DECENTER_START", "WEDGE_RELEASE")]
    assert dead
    evs = [e for e in evs if e not in dead]
    _resequence(evs)
    errs = _errs({"events": evs}, micro, _micro_centerings())
    assert any("CLEAR_WITHOUT_START" in m for m in errs), errs[:10]


# ---------------------------------------------------------------------------
# 真账 5935 石全链(存在性 skip)
# ---------------------------------------------------------------------------

_REAL = os.path.join(os.path.dirname(__file__), "..", "3d", "out",
                     "ledger_full.json")


@pytest.mark.skipif(not os.path.exists(_REAL),
                    reason="out/ledger_full.json 不在盘上 —— 真账全链 fail-on-skip")
def test_real_ledger_fullchain():
    led = L.load_ledger(_REAL)
    assert len(led["stones"]) == 5935
    zones = sorted(set(s["id"].split(".")[0] for s in led["stones"]))
    assert len(zones) == 17
    cens = [CEN.build_centering_for_arch(int(z[4:]) - 1) for z in zones]
    res = SQ.build_sequence(led, cens, eps=EPS, min_hold=MIN_HOLD)
    # 交付闸: require_evidence=True 硬约束
    errs = SQ.check_sequence(res, led, cens, eps=EPS, min_hold=MIN_HOLD)
    assert errs == [], "真账 check_sequence 违例(前 10): %s" % errs[:10]
    # 事件量级 ~6000+
    assert len(res["events"]) > 6000
    # frontier 轨迹合法
    assert SQ.check_frontier(res["events"], zones) == []
    # stage 叙事分组目标 200-600
    assert 200 <= len(res["sequence"]) <= 600, len(res["sequence"])
    # 回写副本全链: validate_ledger(known_event_seqs) 零错
    led2 = SQ.apply_support_edges(led, res)
    errs2 = L.validate_ledger(led2, allow_clearance=False,
                              known_event_seqs=E.event_seqs(res))
    assert errs2 == [], errs2[:10]
    # 每石恰一 centering/stone 曲线族: RING 石中心ing 边在 CLEAR 后为 0
    ring = next(s for s in led2["stones"] if ".RING." in s["id"]
                and s["id"].startswith("ARCH09."))
    zone = "ARCH09"
    clear = _by_hole(res["events"], zone, "CENTERING_CLEAR")[0]["seq"]
    cen_edge = next(e for e in ring["support_edges"]
                    if e["type"] == "centering")
    assert L.edge_capacity(cen_edge, clear) == 0.0
