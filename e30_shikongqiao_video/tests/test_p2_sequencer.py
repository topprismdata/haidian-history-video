# e30_shikongqiao_video/tests/test_p2_sequencer.py
# -*- coding: utf-8 -*-
"""P2-T4 sequencer.py: R0-R7 规则引擎 + frontier 状态机 + 平衡度前缀 + 曲线回写。

判据(brief 接口节全量, 每规则≥1 测):
- R0 每石恰一次/seq 连续/角色可分类/每孔 CLOSE·DECENTER·CLEAR 恰一次;
  裁1: in_void 幻影石(classify_stones 单源, 与 excluded_ids.json 同源)
  不入日程 —— 正控(无事件无边, 原账不被 clipped 标污染)+ 负控(混入事件流
  必红 R0_IN_VOID_PHANTOM);
- R1 墩肩 z 升序; R2 RING prereq ⊇ 立架锚且在立架→合龙窗;
- R3 θ 镜像配对两侧交替, 偶数位前缀 |W_L−W_R|/(W_L+W_R)≤eps
  (负控: 手工把一侧三石前置 → 构造器 raise R3_IMBALANCE);
  F7: 密度 ×2600 整体重建, 事件流与 eps 判定逐位不变(反恒真自证权重已放大);
  F5: 体积=families.family_mesh+export_print.signed_volume 单源, 微账走真族;
- R4 CLOSE→≥min_hold 本孔 HOLD→DECENTER→WEDGE λ 全阶{.25,.5,.75,1}→CLEAR;
  F4: min_hold=0 构造器 raise(免持荷 fail-open 禁止);
- R5a 环肩咬合/锁固肩(clipped_by==ring_band ∨ 石底 z≤extrados ∧ 不撞券架)
  在合龙→**落架窗**(修复轮收紧: 上界 CLEAR→DECENTER_START, 负控: 落架中途
  砌肩必红); M2: 撞架石注入必被排除落 R5b; R5b 其余 SPANDREL/BACK/CORE 在拆架后;
- 裁2 曲线(capacity=荷载分担份额): RING centering 1−λ 阶梯 + stone λ 阶梯
  同点互补, 每事件点 Σ=1; 肩石仅 stone 自持边 [[place,1.0]](不坐木架) ——
  两者形状钉死(改"肩石不卸载"/"环石全程 1.0"必红); Σ≥1 核有牙
  (CAP_INVARIANT); M9: check_sequence 摘线(require_evidence 接线)必红;
- R6 frontier 状态严格前进 + 跨孔组合表(禁相邻孔同落架/禁跳孔落架;
  M7: 右邻 i+1 支路专属负控); F4: 无背胞孔不记 FILLED, at_seq=本孔末置放;
- R7 PAVING→RAIL/POST→CARVE 全局最后;
- 回写: 原账不动, 副本 support_edges capacity_curve x 全在事件集,
  validate_ledger(known_event_seqs)=[](ledger 侧单调律按边类型分型:
  退化型 CURVE_MONOTONIC / stone 型 STONE_CURVE_REGRESSION, 负控在
  test_p2_ledger_v2); 交付闸 validate_event_ledger(require_evidence=True)
  ==[] 硬约束(T3 复审 M4 裁决)。
负控五组: 悬空券石/邻孔稀释 HOLD/跳孔落架/单边领先超 ε/CLEAR 无 START 必红。
blender-free; 真账 5935 石全链(T6b 相位协变重账后 3931 入日程)为存在性 skip 的尾测,
含 in_void 滤除集与 excluded_ids.json 逐位交叉核。
"""
import copy
import json
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

def _wstd(w, h, d):
    # type: (float, float, float) -> Dict[str, Any]
    """wedge-std 全参数(F5 修复轮: classify_stones/stone_weight 走
    families.family_mesh 单源, proud/hw_b/hw_t 必填; 收分取确定性小值)。"""
    return {"h": h, "w": w, "d": d, "proud": 0.05,
            "hw_b": w / 2.0 - 0.02, "hw_t": w / 2.0 - 0.04}


def _micro_ledger():
    led = {"meta": {"schema": L.SCHEMA, "curve_hash": "micro", "seed": 1},
           "stones": []}
    for ai in (0, 1, 2):
        zone = "ARCH%02d" % (ai + 1)
        xc = GM.arch_center_x(ai)
        springer = GM.arch_springer_z(ai)
        crown = GM.arch_crown_z(ai)
        rt = MICRO_RING_T
        half_a = GM.SPANS[ai] / 2.0   # 跨半宽: 墩肩/锁固肩须在 |x-xc| ≥ 半跨
        # R1: 墩肩四 course(同孔 z 升序); x 在跨缘外(拱座语义, 且 classify
        # 不入 in_void 带 —— 真账 IMPOST 集在 in_void 桶为 0)
        for ci, dz in ((0, 0.60), (1, 0.45), (2, 0.30), (3, 0.15)):
            for fi, face in enumerate(("EAST", "WEST")):
                led["stones"].append(L.new_stone(
                    zone, face, "IMPOST", ci, 0, "wedge-std",
                    _wstd(1.05, 0.1, 0.42),
                    [xc + (half_a + 0.60) * (1 if face == "EAST" else -1),
                     4.8, springer - dz, 0.0, 0.0, 0.0], "qingshi"))
        # R3: 券石 θ 镜像(9 石: 四对+龙门石); family 走真源 wedge-std
        # (F5: 体积=families.family_mesh 散度积分, 微账不再有私有近似)
        angs = [(-88.0, -66.0), (-66.0, -44.0), (-44.0, -22.0),
                (-22.0, -11.0), (-11.0, 11.0), (11.0, 22.0),
                (22.0, 44.0), (44.0, 66.0), (66.0, 88.0)]
        for bi, (t0, t1) in enumerate(angs):
            x_off = 1.0 * (1 if t0 + t1 >= 0 else -1)
            led["stones"].append(L.new_stone(
                zone, "EAST", "RING", 0, bi + 1, "wedge-std",
                dict(_wstd(0.8, 0.5, 1.2),
                     angles=[t0, t1], ring_t=rt, xc=xc,
                     stations=[xc + x_off - 0.4, xc + x_off + 0.4],
                     n_ring=9, k=0, lift=0.0, through="full_depth"),
                [xc + x_off, 0.0,
                 F.arch_z(x_off, 0.0, springer, GM.SPANS[ai] / 2.0,
                          GM.arch_rise(ai)) + rt / 2.0,
                 0.0, 0.0, 0.0], "qingshi"))
        # R5a: 锁固肩(底 z ≤ extrados; x 在跨缘外不撞券架且不入 in_void 带
        #  —— 真账锁固肩分布在环带外侧墙体内)
        led["stones"].append(L.new_stone(
            zone, "EAST", "SPANDREL", 0, 0, "wedge-std",
            _wstd(0.38, 0.7, 1.2),
            [xc + half_a + 0.30, 4.8, springer - 0.20, 0.0, 0.0, 0.0],
            "qingshi"))
        led["stones"].append(L.new_stone(
            zone, "WEST", "BACK", 1, 1, "wedge-std",
            _wstd(0.38, 0.7, 1.2),
            [xc - half_a - 0.30, -4.8, springer - 0.20, 0.0, 0.0, 0.0],
            "qingshi"))
        # R5b: 其余肩背胞(底 z 高于 extrados 冠)
        hi = crown + rt + 0.5
        led["stones"].append(L.new_stone(
            zone, "EAST", "SPANDREL", 2, 0, "wedge-std",
            _wstd(0.38, 0.7, 1.2),
            [xc, 4.8, hi + 0.35, 0.0, 0.0, 0.0], "qingshi"))
        led["stones"].append(L.new_stone(
            zone, "WEST", "BACK", 1, 0, "wedge-std",
            _wstd(0.38, 0.7, 1.2),
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
            _wstd(0.5, 0.3, 0.8),
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
                            min_hold=MIN_HOLD, dm_ids=[])
    return res


def _zones(led):
    return sorted(set(s["id"].split(".")[0] for s in led["stones"]))


def _errs(res, led, cens, dm_ids=None):
    return SQ.check_sequence(res, led, cens, eps=EPS, min_hold=MIN_HOLD,
                             dm_ids=dm_ids)


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
        SQ.build_sequence(led2, _micro_centerings(),
                          dm_ids=[])


# ---------------------------------------------------------------------------
# 裁1: 幻影石过滤(in_void 不入日程; 与 excluded_ids.json 同源)
# ---------------------------------------------------------------------------

def _mid_void_stone(zone, ai):
    # type: (str, int) -> Dict[str, Any]
    """整块落在 ARCH(ai+1) 券洞净空中部的合成幻影石(跨缘内 x, 起拱线之上、
    内弧之下)。"""
    xc = GM.arch_center_x(ai)
    springer = GM.arch_springer_z(ai)
    crown = GM.arch_crown_z(ai)
    z_mid = (springer + crown) / 2.0
    return L.new_stone(zone, "EAST", "SPANDREL", 8, 8, "wedge-std",
                       _wstd(0.1, 0.1, 0.1),
                       [xc, 0.0, z_mid, 0.0, 0.0, 0.0], "qingshi")


def test_phantom_in_void_not_scheduled(built, micro):
    """裁1 正控: 洞内幻影石无 PLACE_STONE、无支撑边, checker 仍全绿;
    基础微账自身零幻影(其余合成石全在墙内)。"""
    assert SQ._in_void_ids(micro) == set(), "基础微账不应含 in_void 石"
    led2 = {"meta": micro["meta"],
            "stones": micro["stones"] + [_mid_void_stone("ARCH02", 1)]}
    phantom = led2["stones"][-1]["id"]
    res = SQ.build_sequence(led2, _micro_centerings(), eps=EPS,
                            min_hold=MIN_HOLD, dm_ids=[])
    assert res["meta"]["n_stones_in_void"] == 1
    assert res["meta"]["n_stones"] == len(micro["stones"])
    assert not any(e.get("stone_id") == phantom for e in res["events"])
    assert phantom not in res["_edge_plan"]
    led3 = SQ.apply_support_edges(led2, res)
    ps = next(s for s in led3["stones"] if s["id"] == phantom)
    assert ps["support_edges"] == []
    # 原 ledger 不被 classify 污染(params.clipped 不落原始账)
    assert all("clipped" not in s["params"] for s in micro["stones"])
    assert _errs(res, led2, _micro_centerings()) == []


def test_phantom_in_void_in_stream_red(built, micro):
    """裁1 负控: 幻影石以任何形态混入事件流 → R0_IN_VOID_PHANTOM 必红。"""
    led2 = {"meta": micro["meta"],
            "stones": micro["stones"] + [_mid_void_stone("ARCH02", 1)]}
    phantom = led2["stones"][-1]["id"]
    res = SQ.build_sequence(led2, _micro_centerings(), eps=EPS,
                            min_hold=MIN_HOLD, dm_ids=[])
    evs = copy.deepcopy(res["events"])
    evs.append(E.new_event(len(evs) + 1, "ARCH02", "PLACE_STONE",
                           stone_id=phantom, prereq=[], evidence="C:A1"))
    errs = _errs({"events": evs}, led2, _micro_centerings())
    assert any(m.startswith("R0_IN_VOID_PHANTOM") for m in errs), errs[:8]


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
                          min_hold=MIN_HOLD, ring_order=by_hole_ring_order,
                          dm_ids=[])


def test_r3_density_invariance(micro):
    """R3 真不变量(F7 替换旧恒真测): 密度整体 ×2600 重建, 事件流与 eps
    判定逐位不变 —— R3 判的是比值; 管线任何位置消费绝对重量都在此显形。
    末尾断言权重确已放大, 防不变量退化成恒真(密度根本没生效的假绿)。"""
    cens = _micro_centerings()
    base = SQ.build_sequence(micro, cens, eps=EPS, min_hold=MIN_HOLD, dm_ids=[])
    assert SQ.check_sequence(base, micro, cens, eps=EPS,
                             min_hold=MIN_HOLD) == []
    old = SQ.STONE_DENSITY
    try:
        SQ.STONE_DENSITY = 2600.0
        heavy = SQ.build_sequence(micro, cens, eps=EPS, min_hold=MIN_HOLD, dm_ids=[])
        errs_heavy = SQ.check_sequence(heavy, micro, cens, eps=EPS,
                                       min_hold=MIN_HOLD)
    finally:
        SQ.STONE_DENSITY = old
    assert errs_heavy == [], "密度 2600 下 eps 判定漂移: %s" % errs_heavy[:8]
    assert heavy["events"] == base["events"], "密度 2600 事件流逐位漂移"
    assert heavy["frontier_trace"] == base["frontier_trace"]
    assert heavy["sequence"] == base["sequence"]
    # 反恒真自证: 权重确实随密度放大(体积单源缓存的是体积, 重量随之变)
    s = micro["stones"][8]
    w1 = SQ.stone_weight(s)
    assert w1 > 0.0
    assert SQ.stone_weight(s, density=2600.0) == pytest.approx(w1 * 2600.0)


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
    dm = SQ._double_model_ids(micro, rbo_ids=[])   # 合成账显式空(免扫描)
    n_shoulder = 0
    for zone in _zones(micro):
        close = _by_hole(built["events"], zone, "CLOSE_RING")[0]["seq"]
        clear = _by_hole(built["events"], zone, "CENTERING_CLEAR")[0]["seq"]
        dstart = _by_hole(built["events"], zone, "DECENTER_START")[0]["seq"]
        assert close < dstart < clear
        ai = int(zone[4:]) - 1
        xc = GM.arch_center_x(ai)
        springer = GM.arch_springer_z(ai)
        a = GM.SPANS[ai] / 2.0
        b = GM.arch_rise(ai)
        extrados_z = lambda gx: F.arch_z(gx - xc, 0.0, springer, a, b) \
            + MICRO_RING_T
        band_dist = lambda gx, gz: F.arch_signed_r(gx, gz, xc, springer,
                                                   a, b) - MICRO_RING_T
        cen_boxes = SQ._centering_boxes_global(cens[zone])
        for e in built["events"]:
            if e["hole"] != zone or e["etype"] != "PLACE_STONE":
                continue
            s = by_id[e["stone_id"]]
            if s["id"].split(".")[2] not in SQ.FILL_ROLES:
                continue
            locked = s["id"] not in dm and (
                s["params"].get("clipped_by") == "ring_band"
                or SQ._is_lock_shoulder(s, extrados_z, cen_boxes, band_dist))
            if locked:
                n_shoulder += 1
                # 修复轮收紧: 窗上界 CLEAR → DECENTER_START(落架中途不得砌肩)
                assert close < e["seq"] < dstart
                assert close in e["prereq"]
            else:
                assert e["seq"] > clear
    assert n_shoulder == 6, "每孔恰 2 锁固肩(3 孔共 6), 实得 %d" % n_shoulder


def test_r5a_negative_shoulder_during_decenter_red(built, micro):
    """checker 收紧负控: 锁固肩挪入 DECENTER→CLEAR 窗(落架中途砌肩)必红。
    旧上界(CLEAR)对此恒绿 —— 本测钉死上界已收到 DECENTER_START。"""
    evs = copy.deepcopy(built["events"])
    zone = "ARCH02"
    close = _by_hole(evs, zone, "CLOSE_RING")[0]["seq"]
    dstart = _by_hole(evs, zone, "DECENTER_START")[0]["seq"]
    sh = next(e for e in evs if e["hole"] == zone
              and e["etype"] == "PLACE_STONE" and close < e["seq"] < dstart)
    evs.remove(sh)
    clear_idx = next(i for i, e in enumerate(evs)
                     if e["hole"] == zone and e["etype"] == "CENTERING_CLEAR")
    evs.insert(clear_idx, sh)          # 落到最后一个 WEDGE 与 CLEAR 之间
    _resequence(evs)
    errs = _errs({"events": evs}, micro, _micro_centerings())
    assert any(m.startswith("R5A_WINDOW") for m in errs), errs[:8]


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
    # 裁2: stone 自持边 = λ 阶梯(0→0.25→0.5→0.75→1.0 同点), 与 centering
    # 1−λ 阶梯互补 —— 任意事件点 Σ=1(荷载完整分担)
    assert L.edge_capacity(stone_edge, place) == 0.0
    assert L.edge_capacity(stone_edge, dstart) == 0.0
    assert [L.edge_capacity(stone_edge, w) for w in wedges] \
        == [0.25, 0.5, 0.75, 1.0]
    assert L.edge_capacity(stone_edge, clear) == 1.0
    assert L.edge_capacity(stone_edge, clear + 10) == 1.0
    for x in [place, dstart] + wedges + [clear]:
        assert L.edge_capacity(cen_edge, x) + L.edge_capacity(stone_edge, x) \
            == pytest.approx(1.0), x


# ---------------------------------------------------------------------------
# 修复轮: 裁2 曲线形状 + Σ≥1 不变量 + F4/M2/M7/M9 负控
# ---------------------------------------------------------------------------

def _shoulder_ids(res, zone):
    # type: (Dict[str, Any], str) -> List[str]
    """该孔锁固肩 id 表(合龙→落架窗内的 FILL 角色置放)。"""
    close = _by_hole(res["events"], zone, "CLOSE_RING")[0]["seq"]
    dstart = _by_hole(res["events"], zone, "DECENTER_START")[0]["seq"]
    return [e["stone_id"] for e in res["events"]
            if e["hole"] == zone and e["etype"] == "PLACE_STONE"
            and e.get("stone_id")
            and e["stone_id"].split(".")[2] in SQ.FILL_ROLES
            and close < e["seq"] < dstart]


def test_curve_r5a_shoulder_self_supported_only(built, micro):
    """裁2 肩石曲线: 仅 stone 自持边 [[place,1.0]] 全程, 无 centering 边
    (肩石坐已成环砌体, 不坐木架)。M3 堵死: 改回"肩石坐架、CLEAR 才卸载"
    (加回 centering 边)在本形状断言处必红。"""
    led2 = SQ.apply_support_edges(micro, built)
    for zone in _zones(micro):
        for sid in _shoulder_ids(built, zone):
            s = next(x for x in led2["stones"] if x["id"] == sid)
            types = [e["type"] for e in s["support_edges"]]
            assert types == ["stone"], (sid, types)
            place = next(e["seq"] for e in built["events"]
                         if e["etype"] == "PLACE_STONE"
                         and e["stone_id"] == sid)
            curve = s["support_edges"][0]["capacity_curve"]
            assert curve == [[place, 1.0]], (sid, curve)
            clear = _by_hole(built["events"], zone,
                             "CENTERING_CLEAR")[0]["seq"]
            assert L.edge_capacity(s["support_edges"][0], clear) == 1.0


def test_curve_sum_invariant_all_events(built, micro):
    """裁2 Σ≥1 不变量(全事件核): 每孔每个事件点上, 每块已置放石
    Σ(各边 capacity) ≥ 1 ——荷载任一时刻被完整分担。"""
    led2 = SQ.apply_support_edges(micro, built)
    for zone in _zones(micro):
        evs = sorted((e for e in built["events"] if e["hole"] == zone),
                     key=lambda e: e["seq"])
        for s in led2["stones"]:
            if not s["id"].startswith(zone + "."):
                continue
            if not s["support_edges"]:
                continue
            first = min(pt[0] for ed in s["support_edges"]
                        for pt in ed["capacity_curve"])
            for e in evs:
                if e["seq"] < first:
                    continue
                tot = sum(L.edge_capacity(ed, e["seq"])
                          for ed in s["support_edges"])
                assert tot >= 1.0 - 1e-9, (s["id"], e["seq"], tot)


def test_cap_invariant_catches_unshared_load(built, micro):
    """Σ≥1 核有牙: 篡改 edge_plan 让某券石在 W1 处自持份额缺失(0.25→0)
    → CAP_INVARIANT 必红(该点 Σ=0.75 < 1)。"""
    res = copy.deepcopy(built)
    ring_sid = next(s["id"] for s in micro["stones"]
                    if s["id"].startswith("ARCH02.") and ".RING." in s["id"])
    stone_edge = next(ed for ed in res["_edge_plan"][ring_sid]
                      if ed["type"] == "stone")
    dstart = _by_hole(built["events"], "ARCH02", "DECENTER_START")[0]["seq"]
    knot = next(pt for pt in stone_edge["capacity_curve"] if pt[0] > dstart)
    assert knot[1] == 0.25
    knot[1] = 0.0
    errs = _errs(res, micro, _micro_centerings())
    assert any(m.startswith("CAP_INVARIANT") for m in errs), errs[:8]


def test_f4_min_hold_zero_rejected(micro):
    """F4: min_hold=0 原为 fail-open(免持荷直接落架), 构造器现要求 ≥1。"""
    with pytest.raises(SQ.SequencerError, match="R4_MIN_HOLD"):
        SQ.build_sequence(micro, _micro_centerings(), eps=EPS, min_hold=0, dm_ids=[])


def test_f4_filled_trace_hole_local_and_derivable(micro):
    """F4 合成复现: ARCH03 无肩背胞可填 → 不发 FILL 阶段、不记 FILLED
    (旧代码记 FILLED@全局 len(events), 与 derive_frontier 失同步);
    有背胞孔 FILLED at_seq=本孔末个置放事件。"""
    led = _micro_ledger()
    rest_tokens = (".SPANDREL.C02.", ".BACK.C01.B00", ".CORE.C03.")
    led["stones"] = [s for s in led["stones"]
                     if not (s["id"].startswith("ARCH03.")
                             and any(t in s["id"] for t in rest_tokens))]
    res = SQ.build_sequence(led, _micro_centerings(), eps=EPS,
                            min_hold=MIN_HOLD, dm_ids=[])
    trace = res["frontier_trace"]
    by_hole = {}
    for t in trace:
        by_hole.setdefault(t["hole"], []).append(t["state"])
    assert "FILLED" not in by_hole.get("ARCH03", []), by_hole.get("ARCH03")
    for zone in ("ARCH01", "ARCH02"):
        fills = [e["seq"] for e in res["events"] if e["hole"] == zone
                 and e["etype"] == "PLACE_STONE"
                 and e["stone_id"].split(".")[2] in SQ.FILL_ROLES]
        clear = _by_hole(res["events"], zone, "CENTERING_CLEAR")[0]["seq"]
        post = [x for x in fills if x > clear]
        got = next(t["at_seq"] for t in trace if t["hole"] == zone
                   and t["state"] == "FILLED")
        assert got == max(post), (zone, got, max(post))
    # 构造轨迹与重建轨迹同形(空背胞孔两侧一致)
    assert SQ.derive_frontier(res["events"]) == trace


def test_m9_check_sequence_requires_evidence(built, micro):
    """M9: check_sequence 内 require_evidence=True 接线有牙 —— 摘线
    (证据换成占位符)必红 EVENTS EVIDENCE_PLACEHOLDER。"""
    evs = copy.deepcopy(built["events"])
    evs[7]["evidence"] = "R?:n"
    errs = _errs({"events": evs}, micro, _micro_centerings())
    assert any("EVIDENCE_PLACEHOLDER" in m for m in errs), errs[:8]


def test_m2_frame_collision_excluded_from_r5a(built, micro):
    """M2: _is_lock_shoulder 碰撞项专属负控 —— 注入底 z≤extrados ∧ 足印
    在锁固带内(径向) 但 bbox 撞券架的石, 必被 R5a 排除(落 R5b, CLEAR 后
    置放), checker 全绿。带闸先放过(径向 0.118 ≤ 0.35), 碰撞支是唯一
    否决项(P2-T6 裁决后判据三支仍各有专属负控)。"""
    led = _micro_ledger()
    cens = _micro_centerings()
    ai = 0
    xc = GM.arch_center_x(ai)
    springer = GM.arch_springer_z(ai)
    a = GM.SPANS[ai] / 2.0
    b = GM.arch_rise(ai)
    # 跨缘外 0.30m(微账肩石同位), 底 z 压到 springer−0.55: 足印径向距
    # ~+0.12(带内), 石身下探撞东端楔块(券架 x 向最外构件)。
    collider = L.new_stone(
        "ARCH01", "EAST", "SPANDREL", 5, 9, "wedge-std",
        dict(_wstd(0.38, 0.7, 1.2), d=2.0),
        [xc + a + 0.30, 0.0, springer - 0.55 + 0.35, 0.0, 0.0, 0.0],
        "qingshi")
    led["stones"].append(collider)
    cen_boxes = SQ._centering_boxes_global(cens[0])
    # 前提自证(判据三支: 底 z ≤ extrados ∧ 足印在锁固带内 ∧ 撞架)
    x_mid, z_bot, _ = SQ._stone_xz(collider)
    extr = F.arch_z(x_mid - xc, 0.0, springer, a, b) + MICRO_RING_T
    band_dist = (lambda gx, gz: F.arch_signed_r(gx, gz, xc, springer, a, b)
                 - MICRO_RING_T)
    r_foot = band_dist(x_mid, z_bot)
    assert z_bot <= extr, "前提失效: 撞架石底 z 高于 extrados"
    assert -1.0 <= r_foot <= SQ.LOCK_BAND_M, \
        "前提失效: 撞架足印不在锁固带内(r=%.3f), 判据测不到碰撞项" % r_foot
    assert any(SQ._boxes_collide(SQ._stone_box(collider), cb)
               for cb in cen_boxes), "前提失效: 未撞任何券架构件"
    assert not SQ._is_lock_shoulder(
        collider,
        lambda gx: F.arch_z(gx - xc, 0.0, springer, a, b) + MICRO_RING_T,
        cen_boxes, band_dist), "撞架石不得判锁固肩"
    res = SQ.build_sequence(led, cens, eps=EPS, min_hold=MIN_HOLD, dm_ids=[])
    clear = _by_hole(res["events"], "ARCH01", "CENTERING_CLEAR")[0]["seq"]
    place = next(e["seq"] for e in res["events"]
                 if e.get("stone_id") == collider["id"])
    assert place > clear, "撞架石必须落 R5b(CLEAR 后)"
    assert _errs(res, led, cens) == []


# ---------------------------------------------------------------------------
# P2-T6 裁决: 锁固带闸(径向) + 双建模占位剔除
# ---------------------------------------------------------------------------

def _band_fns(ai):
    # type: (int) -> Any
    xc = GM.arch_center_x(ai)
    springer = GM.arch_springer_z(ai)
    a = GM.SPANS[ai] / 2.0
    b = GM.arch_rise(ai)
    extrados_z = lambda gx: F.arch_z(gx - xc, 0.0, springer, a, b) \
        + MICRO_RING_T
    band_dist = lambda gx, gz: F.arch_signed_r(gx, gz, xc, springer,
                                               a, b) - MICRO_RING_T
    return extrados_z, band_dist


def test_r5a_lock_band_gate_radial_boundary(micro):
    """P2-T6 裁决带闸(单元): 足印距 extrados 面**径向** ≤0.35m 才锁固。
    微账既有肩石自证在带内; 同形石竖直下移、二分定位带界两侧: 带外
    (r>0.35)判 False, 带内(r≤0.35)判 True。竖直 z 距读法在陡肩段把切向
    偏移放大成假深度(且实测拆拱脚配重致 ARCH05/13 翻假) —— 径向是
    facts.arch_signed_r 单源 discipline, 本测钉死口径。"""
    base = next(s for s in micro["stones"]
                if s["id"] == "ARCH01.EAST.SPANDREL.C00.B00")
    extrados_z, band_dist = _band_fns(0)
    cen_boxes = []   # 单元测只测带闸; 碰撞支由 M2 专属负控覆盖
    x_mid, z_bot, _ = SQ._stone_xz(base)
    d0 = band_dist(x_mid, z_bot)
    assert -1.0 <= d0 <= SQ.LOCK_BAND_M, \
        "fixture 前提失效: 微账肩石足印不在锁固带内 r=%.3f" % d0
    assert SQ._is_lock_shoulder(base, extrados_z, cen_boxes, band_dist)

    def shift_down(stone, delta):
        st = copy.deepcopy(stone)
        t = list(st["transform"])
        t[2] -= delta
        st["transform"] = t
        return st

    lo, hi = 0.0, 6.0          # 竖直下移量二分: 找径向距过 0.35 的界
    # (径向几何: 固定 x 下移先靠近弧心 —— 跨缘外 x=2.55 处圆心在
    #  springer−e', 下移 ~3.2m 内 r 反而变小, 界外才单调增; hi 取宽)
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        st = shift_down(base, mid)
        _xm, zb, _z = SQ._stone_xz(st)
        if band_dist(_xm, zb) > SQ.LOCK_BAND_M:
            hi = mid
        else:
            lo = mid
    out_stone = shift_down(base, hi + 0.01)
    in_stone = shift_down(base, max(lo - 0.01, 0.0))
    for st in (out_stone, in_stone):
        _xm, zb, _z = SQ._stone_xz(st)
        assert zb <= extrados_z(_xm), "前提失效: 下移石底高于 extrados"
    _xm, zb_out, _z = SQ._stone_xz(out_stone)
    _xm, zb_in, _z = SQ._stone_xz(in_stone)
    r_out, r_in = band_dist(_xm, zb_out), band_dist(_xm, zb_in)
    assert r_out > SQ.LOCK_BAND_M, r_out
    assert not SQ._is_lock_shoulder(out_stone, extrados_z, cen_boxes,
                                    band_dist), "带外深肩石不得判锁固肩"
    assert r_in <= SQ.LOCK_BAND_M, r_in
    assert SQ._is_lock_shoulder(in_stone, extrados_z, cen_boxes, band_dist)
    print("径向带界: r_in=%.4f / r_out=%.4f (LOCK_BAND_M=%.2f, 竖直下移界=%.3f)"
          % (r_in, r_out, SQ.LOCK_BAND_M, lo))


def test_r5a_band_gate_deep_shoulder_lands_r5b(micro):
    """带闸构造级: 径向带外深肩石不入 SHOULDER 阶段(合龙→落架窗),
    落 R5b 在 CLEAR 后, checker 全绿; 对照带内肩石仍在窗内。"""
    led = _micro_ledger()
    cens = _micro_centerings()
    base = next(s for s in led["stones"]
                if s["id"] == "ARCH01.EAST.SPANDREL.C00.B00")
    extrados_z, band_dist = _band_fns(0)
    deep = copy.deepcopy(base)
    deep["id"] = "ARCH01.EAST.SPANDREL.5.5"
    deep["transform"] = list(deep["transform"])
    deep["transform"][2] -= 3.5     # 竖直压深 3.5m(过弧心垂足后径向出带)
    x_mid, z_bot, _ = SQ._stone_xz(deep)
    assert z_bot <= extrados_z(x_mid), "前提失效: 深肩石底高于 extrados"
    assert band_dist(x_mid, z_bot) > SQ.LOCK_BAND_M, \
        "前提失效: 深肩石仍在带内, 测不到带闸"
    led["stones"].append(deep)
    res = SQ.build_sequence(led, cens, eps=EPS, min_hold=MIN_HOLD, dm_ids=[])
    close = _by_hole(res["events"], "ARCH01", "CLOSE_RING")[0]["seq"]
    dstart = _by_hole(res["events"], "ARCH01", "DECENTER_START")[0]["seq"]
    clear = _by_hole(res["events"], "ARCH01", "CENTERING_CLEAR")[0]["seq"]
    place = next(e["seq"] for e in res["events"]
                 if e.get("stone_id") == deep["id"])
    assert place > clear, "带外深肩石必须落 R5b(CLEAR 后)"
    assert not (close < place < dstart)
    base_place = next(e["seq"] for e in res["events"]
                      if e.get("stone_id") == base["id"])
    assert close < base_place < dstart, "对照带内肩石应在 SHOULDER 窗"
    assert _errs(res, led, cens) == []


def test_dm_placeholder_excluded_from_r5a_and_tamper_red(micro):
    """裁决第 2 闸·双建模占位剔除: 完全吞没石(体素口径, 同 g3
    double_model_scan 单源)判占位 → build 不入 SHOULDER(落 R5b CLEAR 后);
    checker 带 dm_ids 全绿; **不带** dm_ids 的 checker(按 rbo 桶重算,
    合成石不在桶内 → 集合空)将其视为锁固肩, 而它实际排 CLEAR 后 →
    R5A_WINDOW 必红 —— 占位石混入 R5a 荷载的负控入口。"""
    led = _micro_ledger()
    cens = _micro_centerings()
    ring = next(s for s in led["stones"]
                if s["id"].startswith("ARCH01.EAST.RING."))
    fake = L.new_stone("ARCH01", "EAST", "BACK", 8, 8, "wedge-std",
                       _wstd(0.10, 0.10, 0.10), list(ring["transform"]),
                       "qingshi")
    led["stones"].append(fake)
    dm = SQ._double_model_ids(led, rbo_ids=[fake["id"]])
    assert dm == {fake["id"]}, "体素吞没扫描未识别全吞没合成石: %r" % dm
    res = SQ.build_sequence(led, cens, eps=EPS, min_hold=MIN_HOLD, dm_ids=dm)
    clear = _by_hole(res["events"], "ARCH01", "CENTERING_CLEAR")[0]["seq"]
    place = next(e["seq"] for e in res["events"]
                 if e.get("stone_id") == fake["id"])
    assert place > clear, "占位石必须剔出 R5a 落 R5b"
    assert _errs(res, led, cens, dm_ids=dm) == []
    errs2 = _errs(res, led, cens)          # 重算: 合成石不在真 rbo 桶 → 空
    assert any(m.startswith("R5A_WINDOW") and fake["id"] in m
               for m in errs2), errs2[:8]


def test_m7_r6_right_neighbor_unbuilt_red(built, micro):
    """M7 堵: R6 右邻支路(i+1) —— ARCH01 落架时右邻 ARCH02 仍 UNBUILT
    必红 R6_JUMP_DECENTER(既有负控只打左邻 i-1 支路)。"""
    evs = copy.deepcopy(built["events"])
    blk = [e for e in evs if e["hole"] == "ARCH01"
           and e["etype"] in ("DECENTER_START", "WEDGE_RELEASE",
                              "CENTERING_CLEAR")]
    rest = [e for e in evs if e not in blk]
    evs2 = _resequence(blk + rest)     # ARCH01 落架块插到最前
    errs = SQ.check_frontier(evs2, _zones(micro))
    assert any(m.startswith("R6_JUMP_DECENTER") for m in errs), errs[:8]


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
    # P2-T6 裁决: 双建模占位集一次扫描, build/check 共用(省一次 ~26s 体素扫)
    dm = SQ._double_model_ids(led)
    # [P2-T6b] 28→29: 相位协变改变石深 → 一块 rbo 石吞没率越过 0.985 界
    # (体素口径边界移位, 非判据变化; 归因见 p2-task-6-report.md §8)
    assert len(dm) == 29, "0.985 吞没口径占位集(T6b 重账实测), 实得 %d" % len(dm)
    res = SQ.build_sequence(led, cens, eps=EPS, min_hold=MIN_HOLD, dm_ids=dm)
    # 交付闸: require_evidence=True 硬约束
    errs = SQ.check_sequence(res, led, cens, eps=EPS, min_hold=MIN_HOLD,
                             dm_ids=dm)
    assert errs == [], "真账 check_sequence 违例(前 10): %s" % errs[:10]
    # 裁1: 幻影石过滤 —— 事件量级 6122→4070(=5935-2052 砌置放+187 券架事件);
    # in_void 滤除数与 excluded_ids.json 同源同值
    # [P2-T6b] 2052→2004: in_void 手性修复(_kept_pieces 上穿出界支)释放
    # 48 块跨缘真石(12 孔×4), 误删归零且两半桥对称(176/176)。
    # [拱线族返工 2026-10-08] 2004→2028: 新实测(重出 out/ledger_full.json +
    # out/sequence.json 直读, 非凑绿)——单心圆弧跨内分支在 b>a 三孔(8/9/10,
    # 起拱 horseshoe)比旧两圆心弧高, 净空边界上移吃进更多砧石; 逐孔分解
    # ARCH08 +4 / ARCH09 +16 / ARCH10 +4(合计 +24), 其余 14 孔逐位零差
    # (b<a 两族曲线恒等自证边界语义保持)。flare 细节见 body_changelog
    # ArchRoundFix 节"已知账"。
    assert res["meta"]["n_stones_in_void"] == 2028
    assert 3900 <= len(res["events"]) <= 4250
    # 真账 in_void 过滤交叉核: 被滤石集合 == excluded_ids.json["in_void"] 逐位
    _excl = os.path.join(os.path.dirname(__file__), "..", "3d", "out",
                         "print", "excluded_ids.json")
    if os.path.exists(_excl):
        with open(_excl, encoding="utf-8") as fh:
            want = set(json.load(fh)["buckets"]["in_void"])
        got = SQ._in_void_ids(led)
        assert got == want, "in_void 滤除集与旁挂全表不一致: %d vs %d, 差集=%r" \
            % (len(got), len(want), list(got ^ want)[:8])
    # [P2-T6b] R5a = 1342(收缩裁 1290 + in_void 释放 48 + dm/rbo 边界移位
    # 4: A13+2 A15+2)。带闸(径向 0.35m)在真账零额外剔除 —— 实体墙肩全部
    # 径向贴环。逐轮演化: 3187(含幻影)→1307→1290(收缩)→1342(重账)。
    assert res["meta"]["n_dm_excluded"] == 29
    # [审查 INFO 卫生] dm 剔除钉 id 清单(非仅计数): 盘上 sequence.json
    # meta.dm_excluded 须与本扫描逐位一致(id 字典序; 各条吞没率 ∈ 界内)
    # —— 归因可核对, 不再依赖报告正文全表。
    _seqp = os.path.join(os.path.dirname(__file__), "..", "3d", "out",
                         "sequence.json")
    if os.path.exists(_seqp):
        with open(_seqp, encoding="utf-8") as fh:
            dm_meta = json.load(fh)["meta"]["dm_excluded"]
        assert [d["id"] for d in dm_meta] == sorted(dm), \
            (len(dm_meta), sorted(dm)[:4])
        assert all(0.985 <= d["ratio"] <= 1.0 for d in dm_meta), \
            [d for d in dm_meta if not 0.985 <= d["ratio"] <= 1.0]
    r5a = 0
    for e in res["events"]:
        if e["etype"] != "PLACE_STONE" or not e.get("stone_id"):
            continue
        zh = e["hole"]
        close = next(x["seq"] for x in res["events"]
                     if x["hole"] == zh and x["etype"] == "CLOSE_RING")
        dstart = next(x["seq"] for x in res["events"]
                      if x["hole"] == zh and x["etype"] == "DECENTER_START")
        if close < e["seq"] < dstart:
            r5a += 1
    # [拱线族返工 2026-10-08] 1342→1382 新实测: +40 = excluded_ids 桶
    # ring_band_overlap 182→222(全部在 b>a 三孔, 环带随拱线族上移),
    # 推导同 n_stones_in_void 2028 条目。
    assert r5a == 1382, r5a
    # frontier 轨迹合法
    assert SQ.check_frontier(res["events"], zones) == []
    # stage 叙事分组目标 200-600
    assert 200 <= len(res["sequence"]) <= 600, len(res["sequence"])
    # 回写副本全链: validate_ledger(known_event_seqs) 零错
    led2 = SQ.apply_support_edges(led, res)
    errs2 = L.validate_ledger(led2, allow_clearance=False,
                              known_event_seqs=E.event_seqs(res))
    assert errs2 == [], errs2[:10]
    # RING 石 centering 边在 CLEAR 后为 0 且 λ 阶梯同点互补 Σ=1(裁2 真账抽查)
    ring = next(s for s in led2["stones"] if ".RING." in s["id"]
                and s["id"].startswith("ARCH09."))
    zone = "ARCH09"
    evs9 = [e for e in res["events"] if e["hole"] == zone]
    clear = next(e["seq"] for e in evs9 if e["etype"] == "CENTERING_CLEAR")
    wedges = [e["seq"] for e in evs9 if e["etype"] == "WEDGE_RELEASE"]
    cen_edge = next(e for e in ring["support_edges"]
                    if e["type"] == "centering")
    stone_edge = next(e for e in ring["support_edges"]
                      if e["type"] == "stone")
    assert L.edge_capacity(cen_edge, clear) == 0.0
    for w in wedges:
        assert L.edge_capacity(cen_edge, w) + L.edge_capacity(stone_edge, w) \
            == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# T7b 出口审查 R4 钉(λ 常数跨文件 / dm 逐孔回归 / sidecar 重建==记录)
# ---------------------------------------------------------------------------

def test_lambda_grid_constants_cross_file_pinned():
    """R4.3: λ 栅格三处常数同一裁决值跨文件钉 —— events.LAMBDA_GRID(档数)
    / sequencer.LAMBDA_LADDER(λ 全阶) / g3_check.LAMBDA_GRID_STEP(R6 对内
    同档容差) 互证, 改任一处即红(防静默错位④判据与 R6 容差)。"""
    import events as E2
    import g3_check as G3
    assert E2.LAMBDA_GRID == 4
    assert SQ.LAMBDA_LADDER == (0.25, 0.5, 0.75, 1.0)
    assert len(SQ.LAMBDA_LADDER) == E2.LAMBDA_GRID
    assert SQ.LAMBDA_LADDER[0] == pytest.approx(1.0 / E2.LAMBDA_GRID)
    assert SQ.LAMBDA_LADDER[-1] == pytest.approx(1.0)
    assert G3.LAMBDA_GRID_STEP == pytest.approx(1.0 / E2.LAMBDA_GRID)
    assert abs(SQ.LAMBDA_LADDER[1] - SQ.LAMBDA_LADDER[0]) \
        == pytest.approx(G3.LAMBDA_GRID_STEP)


def test_dm_swallow_threshold_cross_file_pinned(monkeypatch):
    """[P2 终审 BLK-3] W1 交接口径单值钉: g3_check.SWALLOW_THRESHOLD ==
    sequencer.DM_SWALLOW_THRESHOLD == 0.985(承重模型实际剔除集口径)。
    无条件跑(不寄生真账 skipif —— 终审面2: 那样钉在 clean clone 永不跑);
    双实现同阈值逐位同集已由终审实测(EQUAL=True, 比率差 4.3e-7 属 6 位
    舍入), 漂移面只在常数 —— 改任一侧即红。monkeypatch 腿自证钉读的是
    活属性非字面复制(判据非恒真)。"""
    import g3_check as G3
    assert SQ.DM_SWALLOW_THRESHOLD == pytest.approx(0.985)
    assert G3.SWALLOW_THRESHOLD == pytest.approx(SQ.DM_SWALLOW_THRESHOLD)
    # 旧 0.99 口径只准作 info 对照常量, 不得回坐交接口径
    assert G3.SWALLOW_THRESHOLD_INFO == pytest.approx(0.99)
    assert G3.SWALLOW_THRESHOLD_INFO != G3.SWALLOW_THRESHOLD
    monkeypatch.setattr(SQ, "DM_SWALLOW_THRESHOLD", 0.99)
    assert G3.SWALLOW_THRESHOLD != SQ.DM_SWALLOW_THRESHOLD, \
        "跨文件钉失牙: 改一侧后两值仍相等(钉读的不是活属性)"


def test_real_dm_per_hole_counts_match_top_level():
    """R4.1 回归钉: meta.holes[].n_dm_excluded 逐孔值 == meta.dm_excluded
    按孔分组计数 ∧ 逐孔和 == 顶层 —— 防波1 循环残留变量类缺陷复发
    (T7b 前 per-hole 恒 0 的陈旧账目, 出口审查 C4)。"""
    import collections
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "..", "3d", "out", "sequence.json")
    if not os.path.exists(p):
        pytest.skip("out/sequence.json 不在盘上")
    with open(p, encoding="utf-8") as f:
        sq = json.load(f)
    meta = sq["meta"]
    per = {h["zone"]: h["n_dm_excluded"] for h in meta["holes"]}
    cnt = collections.Counter(d["id"].split(".")[0]
                              for d in meta["dm_excluded"])
    assert per == {z: cnt.get(z, 0) for z in per}, (per, dict(cnt))
    assert sum(per.values()) == len(meta["dm_excluded"]) \
        == meta["n_dm_excluded"] == 29


@pytest.mark.skipif(
    not (os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", "3d", "out", "ledger_full.json"))
         and os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         "..", "3d", "out", "print",
                                         "excluded_ids.json"))
         and os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         "..", "3d", "refs",
                                         "artifact_sha256.txt"))),
    reason="真账 untracked 输入(ledger_full/excluded_ids)或 sidecar 不在盘上")
def test_sidecar_clean_clone_rebuild_matches_recorded(tmp_path):
    """R4.6 后半: sidecar 不只'记录==盘', 还要'干净克隆重建==记录' ——
    git archive HEAD(tracked 集)→ 拷两份 untracked 真账输入 → 重跑
    sequencer → sequence.json sha256 == sidecar 记录。钓 clean-clone
    隐形依赖(excluded_ids.json 缺失曾产出'另一种合法'账目 sha 70c90849,
    出口审查 F7; 现 _double_model_ratios 对缺失输入 fail-closed)。
    预算注记(P2 终审 W-1): 子进程 timeout=900s —— 独占实测 ~200s, ×4.5
    并发余量; 并发时段勿与全套同跑(600s 曾在加载机上 flake, 定性环境
    争用非回归), 本测单独串行跑。本机后台通道 CPU 限流至 ~2.4% 时本测
    必超时(限流下 ~10 倍爬行), 不可用 —— 须 bash 前台独占跑
    (pytest -k sidecar_clean_clone 或单独 pytest tests/test_p2_sequencer.py::本测)。"""
    import hashlib
    import subprocess
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(here, "..", ".."))
    proj = "e30_shikongqiao_video"
    # sidecar 记录值
    rec = {}
    with open(os.path.join(here, "..", "3d", "refs",
                           "artifact_sha256.txt"), encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or "  " not in line:
                continue
            sha, path = line.split()
            rec[path] = sha
    key = "3d/out/sequence.json"
    assert key in rec, "sidecar 缺 sequence.json 记录"
    # 干净克隆: archive 只含 tracked
    r = subprocess.run(["git", "archive", "HEAD", proj], cwd=root,
                       capture_output=True)
    assert r.returncode == 0, r.stderr
    import tarfile
    t = tarfile.open(fileobj=__import__("io").BytesIO(r.stdout))
    t.extractall(str(tmp_path))
    # 拷 untracked 真账输入(重建的合法前提; 缺失会被 sequencer fail-closed 拒)
    for rel in ("out/ledger_full.json", "out/print/excluded_ids.json"):
        dst = tmp_path / proj / "3d" / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        with open(os.path.join(root, proj, "3d", rel), "rb") as fi, \
                open(dst, "wb") as fo:
            fo.write(fi.read())
    r2 = subprocess.run([sys.executable, "sequencer.py"],
                        cwd=str(tmp_path / proj / "3d"), capture_output=True,
                        text=True, timeout=900)
    assert r2.returncode == 0, r2.stdout[-2000:] + r2.stderr[-2000:]
    out_seq = tmp_path / proj / "3d" / "out" / "sequence.json"
    h = hashlib.sha256(out_seq.read_bytes()).hexdigest()
    assert h == rec[key], "干净克隆重建 sequence.json sha != sidecar 记录"
