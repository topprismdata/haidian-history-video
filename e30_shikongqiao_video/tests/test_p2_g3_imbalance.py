# e30_shikongqiao_video/tests/test_p2_g3_imbalance.py
# -*- coding: utf-8 -*-
"""P2-T7 g3_check.py ④墩推力不平衡(最小推力读数; λ 卸架档 + 核距双指标)。

物理口径(冻结, 判据先行数字后置; 2026-10-07 主控包络连续性裁决; 详见
g3_check.py T7 节头注):
  有效推力全孔同式 H_eff = λ × Hmin(H 区间下界; Heyman 最小推力原理,
  事件孔与已清账孔连续, λ=1 无间断); 旧"事件孔取 Hmax"口径降为敏感性
  对照(entry 的 *hmax 字段, 仅记录不判红)。sequencer 波2 = 全桥同波
  逐档(邻孔对档差=0), R6_ADJ 改"对内同档"(λ 差 ≤ 一档)。
  双指标独立输出(阈值互不派生, 一个红一个绿要能表达):
    倾覆裕度 ratio = M_res/M_unb ≥ 1.5 [现代裕度·敏感性]
      M_unb = |dH|×h_ref(h_ref=两侧作用高较大者, 保守), M_res = V×B/2
    核距(中三分律) e_kernel = |H_L·h_L − H_R·h_R|/V ≤ B/6(矩形基底核半宽)
  h_i = 起拱线作用高(GM.arch_springer_z 单源 − 基底 BODY_BOTTOM)。
  λ 档: WEDGE_RELEASE.load_lambda(events 1/4 栅格), DECENTER_START=0,
  CENTERING_CLEAR=1; 架吸收 1−λ, λ=0 档(架上满承载) → H_eff=0。

测试纪律(同 T5/T6): blender-free; 不 import sequencer(子进程探针钉);
合成微账只发落架类事件(无石), 几何全部 GM/F 现算不硬编码;
判据先自证非恒真(每个负控内嵌"判据活着"的对照)。
"""
import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "3d"))

import events as E
import facts as F
import geom_math as GM
import g3_check as G3

BB = -2.20  # assumptions.BODY_BOTTOM(测试自算作用高用, 不进判据)


# ---------------------------------------------------------------------------
# 合成微账工具: 纯落架事件流(无石), 几何现算
# ---------------------------------------------------------------------------

def _ev(seq, hole, etype, lam=None):
    return E.new_event(seq, hole, etype, load_lambda=lam)


def _ladder(seq0, hole):
    """一孔完整卸架块: dstart → λ={.25,.5,.75,1.0} → clear(7 事件)。"""
    evs = [_ev(seq0, hole, "DECENTER_START")]
    for k, lam in enumerate((0.25, 0.5, 0.75, 1.0)):
        evs.append(_ev(seq0 + 1 + k, hole, "WEDGE_RELEASE", lam=lam))
    evs.append(_ev(seq0 + 5, hole, "CENTERING_CLEAR"))
    return evs


def _pair_lockstep(a, b, seq0=1):
    """两邻孔同 stage 逐档同步卸架: 双 dstart → 逐档交错(λ 档差≤一档)
    → 双 clear(对称同步落架的理想序, Step1① 的"同步"语义)。"""
    evs = [_ev(seq0, a, "DECENTER_START"),
           _ev(seq0 + 1, b, "DECENTER_START")]
    s = seq0 + 2
    for lam in (0.25, 0.5, 0.75, 1.0):
        evs.append(_ev(s, a, "WEDGE_RELEASE", lam=lam))
        evs.append(_ev(s + 1, b, "WEDGE_RELEASE", lam=lam))
        s += 2
    evs.append(_ev(s, a, "CENTERING_CLEAR"))
    evs.append(_ev(s + 1, b, "CENTERING_CLEAR"))
    return evs


def _walk(events, H_env, pier_dims=None, ledger=None):
    return G3.imbalance_gate(
        events, H_env,
        ledger=ledger if ledger is not None else {"stones": []},
        in_void=frozenset(), pier_dims=pier_dims)


def _entry_at(gate, hole, etype, lam_val=None, pid="PIER01"):
    """取 (hole, etype[, λ]) 事件在该墩的记录(λ 精确匹配)。"""
    hits = [e for e in gate["events"]
            if e["hole"] == hole and e["etype"] == etype and e["pier_id"] == pid
            and (lam_val is None or e["lam_active"] == lam_val)]
    assert hits, (hole, etype, lam_val, pid)
    return hits[-1]


def _h_app(idx):
    """孔作用高(0-based): 起拱线 − 基底(与实现同源 GM, 测试不硬编码几何)。"""
    return GM.arch_springer_z(idx) - BB


def _snap_of(events, hole, etype, lam_val=None):
    for snap in G3.snapshots(events, {"stones": []}, in_void=frozenset()):
        ev = snap.event
        if ev.get("hole") == hole and ev.get("etype") == etype \
                and (lam_val is None or ev.get("load_lambda") == lam_val):
            return snap
    raise AssertionError("event not found: %s %s %r" % (hole, etype, lam_val))


# ---------------------------------------------------------------------------
# Step1 四测(brief 原文; 先红后绿)
# ---------------------------------------------------------------------------

def test_step1_symmetric_pair_lockstep_dh_near_zero_green():
    """①对称双孔同步卸架(逐档交错) → 共享墩 dH≤一档且末档精确 0, 两指标皆绿。"""
    evs = _pair_lockstep("ARCH01", "ARCH02")
    H_env = {"ARCH01": (30.0, 30.0), "ARCH02": (30.0, 30.0)}
    fat = {"PIER01": {"base_w": 6.0, "weight": 100.0}}
    gate = _walk(evs, H_env, pier_dims=fat)
    p1 = [e for e in gate["events"] if e["pier_id"] == "PIER01"]
    assert p1, "PIER01 无计算记录"
    # 同步逐档: 任一时刻 |dH| ≤ 一档(0.25·H) —— 同步卸架的不平衡上界
    for e in p1:
        assert abs(e["dH"]) <= 30.0 * 0.25 + 1e-9, e
    # 末档(两孔 λ 均=1)精确归零: 对称推力互抵
    last = _entry_at(gate, "ARCH02", "WEDGE_RELEASE", 1.0)
    assert last["dH"] == pytest.approx(0.0, abs=1e-9)
    assert last["verdict"] == "ok"
    assert last["verdict_ratio"] == "ok" and last["verdict_kernel"] == "ok"
    # 全程两指标皆绿
    assert all(e["verdict"] == "ok" for e in p1)


def test_step1_one_side_early_clear_other_unclosed_ratio_red():
    """②一侧提前 CLEAR 另一侧未合龙 → 单侧全推力, ratio<1.5 违例(红)。"""
    evs = _ladder(1, "ARCH01")          # ARCH01 落架到底
    # ARCH02 未合龙未落架(事件流中不存在) → 回馈 0(最不利)
    H_env = {"ARCH01": (10.45, 34.2), "ARCH02": (20.4, 48.2)}
    slim = {"PIER01": {"base_w": 3.1, "weight": 20.0}}
    gate = _walk(evs, H_env, pier_dims=slim)
    mid = _entry_at(gate, "ARCH01", "WEDGE_RELEASE", 0.25)
    full = _entry_at(gate, "ARCH01", "WEDGE_RELEASE", 1.0)
    clr = _entry_at(gate, "ARCH01", "CENTERING_CLEAR")
    # λ 小档尚绿(裕度随 λ 单调恶化)
    assert mid["verdict_ratio"] == "ok" and mid["ratio"] >= 1.5
    # 满档红: 单侧推力倾覆
    assert full["verdict_ratio"] == "RED" and full["ratio"] < 1.5
    assert clr["verdict_ratio"] == "RED"
    assert "IMB_RATIO_RED" in gate["violation_counts"]


def test_step1_lambda_zero_rung_dh_zero():
    """③λ=0 档(架上满承载) → dH=0 绿; 同流 λ 增档即非零(证 λ 门活着, 非恒零)。"""
    evs = [_ev(1, "ARCH01", "DECENTER_START"),
           _ev(2, "ARCH01", "WEDGE_RELEASE", lam=0.25)]
    H_env = {"ARCH01": (30.0, 30.0)}
    gate = _walk(evs, H_env, pier_dims={"PIER01": {"base_w": 3.1,
                                                   "weight": 60.0}})
    at0 = _entry_at(gate, "ARCH01", "DECENTER_START")
    assert at0["lam_active"] == 0.0
    assert at0["dH"] == 0.0 and at0["H_L"] == 0.0
    assert at0["ratio"] is None and at0["verdict"] == "ok"
    at25 = _entry_at(gate, "ARCH01", "WEDGE_RELEASE", 0.25)
    assert abs(at25["dH"]) > 0.0, "λ 档未接上(恒零 = 判据失效)"
    assert at25["H_L"] == pytest.approx(0.25 * 30.0, rel=1e-12)


def test_step1_ratio_green_kernel_red_fat_pier():
    """④a 独立性: 矮胖墩大水平力 → ratio 绿但 e_kernel 红(不被裕度掩盖)。"""
    evs = _ladder(1, "ARCH01")
    H_env = {"ARCH01": (37.0, 37.0)}
    fat = {"PIER01": {"base_w": 6.0, "weight": 100.0}}
    gate = _walk(evs, H_env, pier_dims=fat)
    full = _entry_at(gate, "ARCH01", "WEDGE_RELEASE", 1.0)
    assert full["verdict_ratio"] == "ok" and full["ratio"] >= 1.5
    assert full["verdict_kernel"] == "RED"
    assert full["e_kernel"] > full["kernel_half_w"]
    assert full["verdict"] != "ok"


def test_step1_ratio_red_kernel_green_balanced_moments():
    """④b 独立性(反之): 两孔推力矩恰好对消(H_R=H_L·h_L/h_R) → 核距绿但
    ratio 红 —— 核距不掩盖裕度, 且同流不同事件两判定互变(非恒绑定)。"""
    h1, h2 = _h_app(0), _h_app(1)
    HL = 60.0
    HR = HL * h1 / h2                    # 精确力矩对消(λ=1 时 M_center=0)
    evs = [_ev(1, "ARCH01", "DECENTER_START"),
           _ev(2, "ARCH01", "WEDGE_RELEASE", lam=1.0)]
    # ARCH01 卸架(事件孔→Hmax), ARCH02 已清账(λ=1, 非事件孔→Hmin=HR)
    evs2 = [_ev(0, "ARCH02", "CENTERING_CLEAR")] + evs
    H_env = {"ARCH01": (HL, HL), "ARCH02": (HR, HR)}
    light = {"PIER01": {"base_w": 3.1, "weight": 10.0}}
    gate = _walk(evs2, H_env, pier_dims=light)
    full = _entry_at(gate, "ARCH01", "WEDGE_RELEASE", 1.0)
    # 核距: 力矩对消 → e≈0 绿
    assert full["M_center"] == pytest.approx(0.0, abs=1e-9)
    assert full["verdict_kernel"] == "ok"
    # 裕度: |dH|×h_ref 大而 V·B/2 小 → 红
    assert full["verdict_ratio"] == "RED" and full["ratio"] < 1.5
    # 同流 dstart 事件核距红(M_center=HR·h2 大) —— 两指标逐事件独立表达
    at0 = _entry_at(gate, "ARCH01", "DECENTER_START")
    assert at0["verdict_kernel"] == "RED"


def test_step1_lambda1_event_hole_equals_cleared_continuity():
    """④c 包络连续性钉(主控裁决①): λ=1 事件孔与已清账孔同式(λ×Hmin) ——
    同墩在"A01 末档 WEDGE_RELEASE(事件孔)"与"A01 已清账后他孔事件"两
    时刻, H_L 与双指标逐位同(A01 λ 同为 1, 无 Hmax→Hmin 突跳)。"""
    evs = [_ev(1, "ARCH01", "DECENTER_START"),
           _ev(2, "ARCH01", "WEDGE_RELEASE", lam=1.0),
           _ev(3, "ARCH01", "CENTERING_CLEAR"),
           _ev(4, "ARCH02", "DECENTER_START")]
    H_env = {"ARCH01": (10.45, 34.2), "ARCH02": (20.4, 48.2)}
    gate = _walk(evs, H_env, pier_dims={"PIER01": {"base_w": 3.1,
                                                   "weight": 60.0}})
    at_w = _entry_at(gate, "ARCH01", "WEDGE_RELEASE", 1.0)
    at_b = _entry_at(gate, "ARCH02", "DECENTER_START")   # A01 清账(λ=1) 非事件孔
    for fld in ("H_L", "dH", "M_unb", "ratio", "e_kernel"):
        assert at_w[fld] == at_b[fld], (fld, at_w[fld], at_b[fld])
    assert at_w["H_L"] == pytest.approx(10.45)           # = Hmin×1, 非 Hmax


def test_r6_adj_rung_lock_wave_legal_skew_red():
    """主控裁决②机制钉(g3 侧独立重建): 相邻孔档差=0 同落架合法(全桥同波
    的邻孔对核); 一方连升多档他方未动 = 乱序同落架, R6_ADJ 仍红。"""
    def _block(seq0, hole):
        evs = [_ev(seq0, hole, "CLOSE_RING")]
        for k in range(3):
            evs.append(_ev(seq0 + 1 + k, hole, "HOLD_EVENT"))
        return evs
    # 档差=0 交错(全桥同波的邻孔对): 双合龙持荷 → 双 dstart → 逐档交错
    legal = (_block(1, "ARCH01") + _block(5, "ARCH02") +
             [_ev(9, "ARCH01", "DECENTER_START"),
              _ev(10, "ARCH02", "DECENTER_START")])
    s = 11
    for lam in (0.25, 0.5, 0.75, 1.0):
        legal.append(_ev(s, "ARCH01", "WEDGE_RELEASE", lam=lam))
        legal.append(_ev(s + 1, "ARCH02", "WEDGE_RELEASE", lam=lam))
        s += 2
    legal += [_ev(s, "ARCH01", "CENTERING_CLEAR"),
              _ev(s + 1, "ARCH02", "CENTERING_CLEAR")]
    H_env = {"ARCH01": (10.45, 34.2), "ARCH02": (20.4, 48.2)}
    # R6 层核: snapshot 重建无 JUMP/ADJ 违例(档差=0 同落架合法)
    led0 = {"stones": []}
    viols = []
    for snap in G3.snapshots(legal, led0, in_void=frozenset()):
        viols.extend(G3.check_dag(snap))
    assert not any(G3.CODE_R6_ADJ in v or G3.CODE_R6_JUMP in v
                   for v in viols), viols[:8]
    # 乱序: A02 连升两档(0.25→0.5)后 A01 才动 → 失档红
    skew = (_block(1, "ARCH01") + _block(5, "ARCH02") +
            [_ev(9, "ARCH02", "DECENTER_START"),
             _ev(10, "ARCH02", "WEDGE_RELEASE", lam=0.25),
             _ev(11, "ARCH02", "WEDGE_RELEASE", lam=0.5),
             _ev(12, "ARCH01", "DECENTER_START")])
    viols2 = []
    for snap in G3.snapshots(skew, led0, in_void=frozenset()):
        viols2.extend(G3.check_dag(snap))
    assert any(G3.CODE_R6_ADJ in v for v in viols2), viols2[:8]


# ---------------------------------------------------------------------------
# 五负控(spec §6 铁律: 每条先证判据非恒真)
# ---------------------------------------------------------------------------

def test_neg1_lambda_rungs_zeroed_all_dh_zero():
    """负① λ 档归零 → 全事件 dH 全 0; 同流未归零有非零(证 λ 接上了)。"""
    evs = _pair_lockstep("ARCH01", "ARCH02")
    H_env = {"ARCH01": (30.0, 30.0), "ARCH02": (30.0, 30.0)}
    fat = {"PIER01": {"base_w": 6.0, "weight": 100.0}}
    base = _walk(evs, H_env, pier_dims=fat)
    assert any(abs(e["dH"]) > 0.0 for e in base["events"]), \
        "基线全零 = λ 判据恒真(失效)"
    # λ 档归零 = WEDGE_RELEASE λ→0 ∧ 去 CLEAR(CLEAR 语义自带 λ=1, 非档位)
    evs0 = [dict(e, load_lambda=0.0) for e in evs
            if e["etype"] != "CENTERING_CLEAR"]
    z = _walk(evs0, H_env, pier_dims=fat)
    assert z["events"], "归零流仍须逐事件出数"
    for e in z["events"]:
        assert e["dH"] == 0.0 and e["H_L"] == 0.0 and e["H_R"] == 0.0, e
    assert z["violations"] == []


def test_neg2_zero_h_env_all_green_no_false_red():
    """负② H_env 全置 0 → 无推力无不平衡(绿是平凡), 验证不假红。"""
    evs = _ladder(1, "ARCH01")
    H_env = {"ARCH01": (0.0, 0.0), "ARCH02": (0.0, 0.0)}
    slim = {"PIER01": {"base_w": 3.1, "weight": 60.0}}
    gate = _walk(evs, H_env, pier_dims=slim)
    assert gate["events"]
    for e in gate["events"]:
        assert e["dH"] == 0.0 and e["M_unb"] == 0.0 and e["M_center"] == 0.0
        assert e["e_kernel"] == 0.0 and e["verdict"] == "ok"
    assert gate["ok"] is True and gate["violations"] == []


def test_neg3_h_doubling_monotone_ratio_down_kernel_up():
    """负③ 单孔 H 翻倍 → 其两侧墩 ratio 严格单调降、e_kernel 严格单调升。"""
    evs = _ladder(1, "ARCH01") + _ladder(8, "ARCH02")
    base_env = {"ARCH01": (10.0, 34.0), "ARCH02": (20.4, 48.2)}
    dbl_env = {"ARCH01": (10.0, 34.0), "ARCH02": (40.8, 96.4)}  # 仅 ARCH02 翻倍
    dims = {"PIER01": {"base_w": 3.1, "weight": 80.0},
            "PIER02": {"base_w": 3.1, "weight": 80.0}}
    g0 = _walk(evs, base_env, pier_dims=dims)
    g2 = _walk(evs, dbl_env, pier_dims=dims)
    for pid in ("PIER01", "PIER02"):
        e0 = _entry_at(g0, "ARCH02", "WEDGE_RELEASE", 1.0, pid)
        e2 = _entry_at(g2, "ARCH02", "WEDGE_RELEASE", 1.0, pid)
        assert e2["ratio"] < e0["ratio"], (pid, e0["ratio"], e2["ratio"])
        assert e2["e_kernel"] > e0["e_kernel"], (pid, e0, e2)
        assert abs(e2["dH"]) > abs(e0["dH"])


def test_neg4_base_widening_kernel_util_down_ratio_not_hurt():
    """负④ 墩基底加宽 → 核距利用率(e/半宽)严格降(B/6∝B) 且 ratio 不误伤(M_res∝B 升)。"""
    evs = _ladder(1, "ARCH01")
    H_env = {"ARCH01": (34.2, 34.2)}
    narrow = {"PIER01": {"base_w": 3.1, "weight": 80.0}}
    wide = {"PIER01": {"base_w": 6.2, "weight": 80.0}}
    gn = _walk(evs, H_env, pier_dims=narrow)
    gw = _walk(evs, H_env, pier_dims=wide)
    en = _entry_at(gn, "ARCH01", "WEDGE_RELEASE", 1.0)
    ew = _entry_at(gw, "ARCH01", "WEDGE_RELEASE", 1.0)
    util_n = en["e_kernel"] / en["kernel_half_w"]
    util_w = ew["e_kernel"] / ew["kernel_half_w"]
    assert util_w < util_n, (util_n, util_w)
    assert ew["ratio"] > en["ratio"], (en["ratio"], ew["ratio"])


def test_neg5_neighbor_clear_state_flip_sign_and_direction():
    """负⑤ 邻孔落架状态翻转 → dH 符号按回馈方向翻转且逐档差精确可预言。"""
    evs = [_ev(1, "ARCH01", "CENTERING_CLEAR"),   # 西邻已清账(λ=1→回馈 Hmin)
           _ev(2, "ARCH02", "DECENTER_START"),
           _ev(3, "ARCH02", "WEDGE_RELEASE", lam=0.75),
           _ev(4, "ARCH02", "WEDGE_RELEASE", lam=1.0)]
    H_env = {"ARCH01": (31.0, 31.0), "ARCH02": (39.74, 39.74)}
    gate = _walk(evs, H_env, pier_dims={"PIER01": {"base_w": 3.1,
                                                   "weight": 90.0}})
    d075 = _entry_at(gate, "ARCH02", "WEDGE_RELEASE", 0.75)["dH"]
    d100 = _entry_at(gate, "ARCH02", "WEDGE_RELEASE", 1.0)["dH"]
    # ARCH01 已落架回馈 +31(推 +x); ARCH02 卸架推 −x: 档位增长使符号翻转
    assert d075 > 0.0 > d100, (d075, d100)
    assert d100 - d075 == pytest.approx(-0.25 * 39.74, rel=1e-12)
    # 反向对照: 无回馈(ARCH01 未清账, λ=0)则两档全负 —— 回馈方向正确,
    # 且回馈项恰为 +Hmin_01(d075 与无回馈态之差)
    evs_b = [e for e in evs if e["hole"] != "ARCH01"]
    gb = _walk(evs_b, H_env, pier_dims={"PIER01": {"base_w": 3.1,
                                                   "weight": 90.0}})
    b075 = _entry_at(gb, "ARCH02", "WEDGE_RELEASE", 0.75)["dH"]
    b100 = _entry_at(gb, "ARCH02", "WEDGE_RELEASE", 1.0)["dH"]
    assert b075 < 0.0 and b100 < 0.0
    assert d075 - b075 == pytest.approx(31.0, rel=1e-12)   # 回馈 = +Hmin


# ---------------------------------------------------------------------------
# 接口契约 / 机制闸
# ---------------------------------------------------------------------------

def test_brief_interface_fields_and_gate_node_shape():
    """brief 接口: pier_imbalance 逐墩字段齐; gate 节与 gate_dag 同形。"""
    evs = _ladder(1, "ARCH01")
    H_env = {"ARCH01": (10.45, 34.2), "ARCH02": (20.4, 48.2)}
    slim = {"PIER01": {"base_w": 3.1, "weight": 60.0}}
    gate = _walk(evs, H_env, pier_dims=slim)
    for key in ("violations", "violation_counts", "ok", "elapsed_s"):
        assert key in gate, key                      # 同形节契约
    for e in gate["events"]:
        for fld in ("H_L", "H_R", "dH", "M_unb", "M_res", "ratio",
                    "e_kernel", "verdict"):
            assert fld in e, (fld, e)
        assert e["pier_id"] in ("PIER%02d" % k for k in range(1, 17))
    # 非 DECENTERING 事件不出数; DECENTERING 事件出邻墩记录(纯读不炸)
    snap = _snap_of([_ev(1, "ARCH01", "DECENTER_START")],
                    "ARCH01", "DECENTER_START")
    got = G3.pier_imbalance(snap, H_env, {"ARCH01": 0.0})
    assert set(got) == {"PIER01"} and got["PIER01"]["dH"] == 0.0
    snap2 = _snap_of([dict(_ev(1, "ARCH01", "DECENTER_START"),
                           etype="ADD_FILL")], "ARCH01", "ADD_FILL")
    assert G3.pier_imbalance(snap2, H_env, {}) == {}


def test_pier_dims_ledger_pier_stones_then_facts_fallback():
    """墩基底尺寸: ledger PIER 石 params 优先; 真账无 PIER 石 → facts 单源回退。"""
    x1 = GM.PIER_X[1]
    led = {"stones": [dict(id="ARCH02.EAST.PIER.C00.B00", family="slab",
                           transform=[x1, 0.0, 0.0, 0.0, 0.0, 0.0],
                           params={"w": 2.9, "found_w": 4.2, "h": 1.0})]}
    dims = G3._pier_dims_from_ledger(led)
    assert dims == {"PIER01": {"base_w": 4.2}}, dims
    evs = _ladder(1, "ARCH01")
    H_env = {"ARCH01": (30.0, 30.0)}
    gate = _walk(evs, H_env, ledger=led)
    e1 = _entry_at(gate, "ARCH01", "WEDGE_RELEASE", 1.0)
    assert e1["base_w"] == pytest.approx(4.2)
    assert e1["dims_source"] == "ledger_pier_stones"
    # 真账形态(无 PIER 石) → facts 回退: 端墩 FOUND_W, 中央对 8/9 FOUND_W_C
    gate2 = _walk(evs, H_env, ledger={"stones": []})
    e2 = _entry_at(gate2, "ARCH01", "WEDGE_RELEASE", 1.0)
    assert e2["base_w"] == pytest.approx(F.PIER_FOUND_W)
    assert e2["dims_source"] == "facts_fallback"
    assert G3._pier_base_w(8) == pytest.approx(F.PIER_FOUND_W_C)
    assert G3._pier_base_w(9) == pytest.approx(F.PIER_FOUND_W_C)
    # 墩重单调于 z_top 且为正(积分路径活着)
    zt8 = min(GM.arch_springer_z(7), GM.arch_springer_z(8))
    v_lo = G3._pier_weight(8, GM.arch_springer_z(7) - 1.0)
    v_hi = G3._pier_weight(8, zt8)
    assert 0.0 < v_lo < v_hi


def test_missing_event_hole_env_skipped_with_note():
    """事件孔缺 H 区间 → 跳过该事件并落 skip 注记(fail-closed 可见, 不静默)。"""
    evs = _ladder(1, "ARCH01")
    gate = _walk(evs, {}, pier_dims={"PIER01": {"base_w": 3.1, "weight": 60.0}})
    assert gate["events"] == []
    assert gate["n_skipped_events"] == len(evs)
    assert gate["skipped_note"]


def test_lambda_out_of_range_fails_closed():
    """λ 越界(>1) → ValueError 停(fail-closed, 禁静默钳位)。"""
    evs = [_ev(1, "ARCH01", "DECENTER_START"),
           _ev(2, "ARCH01", "WEDGE_RELEASE", lam=1.5)]
    with pytest.raises(ValueError):
        _walk(evs, {"ARCH01": (30.0, 30.0)})


def test_abutment_boundary_piers_skipped():
    """孔1 西侧/孔17 东侧为桥台(非内墩), 不出墩记录; 端孔只评 PIER01。"""
    evs = _ladder(1, "ARCH01") + _ladder(8, "ARCH17")
    H_env = {"ARCH01": (30.0, 30.0), "ARCH17": (20.0, 30.0)}
    gate = _walk(evs, H_env)
    pids = {e["pier_id"] for e in gate["events"]}
    assert "PIER00" not in pids and "PIER17" not in pids
    a1 = {e["pier_id"] for e in gate["events"] if e["hole"] == "ARCH01"}
    a17 = {e["pier_id"] for e in gate["events"] if e["hole"] == "ARCH17"}
    assert a1 == {"PIER01"} and a17 == {"PIER16"}


def test_g3_imbalance_path_no_sequencer_import():
    """独立性(子进程探针, 同 T5 纪律): imbalance 全路径不 import sequencer。"""
    code = (
        "import sys, os\n"
        "sys.path.insert(0, os.path.join(%r, '..', '3d'))\n"
        "import events as E, g3_check as G3\n"
        "def ev(s, h, t, lam=None):\n"
        "    return E.new_event(s, h, t, load_lambda=lam)\n"
        "evs = [ev(1,'ARCH01','DECENTER_START'), ev(2,'ARCH01','WEDGE_RELEASE',1.0)]\n"
        "g = G3.imbalance_gate(evs, {'ARCH01': (30.0, 30.0)},\n"
        "                      ledger={'stones': []}, in_void=frozenset(),\n"
        "                      pier_dims={'PIER01': {'base_w': 3.1, 'weight': 60.0}})\n"
        "assert g['events']\n"
        "print('sequencer' in sys.modules)\n"
    ) % (os.path.dirname(os.path.abspath(__file__)),)
    out = subprocess.run([sys.executable, "-c", code], capture_output=True,
                         text=True, timeout=120)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip().endswith("False"), out.stdout


# ---------------------------------------------------------------------------
# 真账全链(存在性 skip): 串接 stress H 区间 → 全事件逐墩 → 停车线协议
# ---------------------------------------------------------------------------

_HERE = os.path.dirname(os.path.abspath(__file__))
_SEQ = os.path.join(_HERE, "..", "3d", "out", "sequence.json")
_LEDSEQ = os.path.join(_HERE, "..", "3d", "out", "ledger_sequenced.json")
_NEED = [_SEQ, _LEDSEQ]


@pytest.mark.skipif(not all(os.path.exists(p) for p in _NEED),
                    reason="out/sequence.json+ledger_sequenced.json 不在盘上")
def test_real_ledger_gate_imbalance_fullchain():
    """真账(全桥同波落架序, P2-T7 包络连续性裁决重锚):
    ① run_g3 三节齐且正常返回(gate_imbalance 绿 —— 全桥同波对称同步卸落
       [工程推断·非史料] 在最小推力读数下不违例; 条件性见 viol_uniform_hmax)
    ② Hmax 保守敏感性对照字段在册(仅记录不判红);
    ③ 串行序 Hmin 口径仍深红 —— 头条发现的 robust 自证(卸架序决定性,
       非包络口径伪影; 由同账卸架块重排为逐孔串行探针复现)。
    判据先行数字后置: 红绿都是结论; 本测钉协议与结构。"""
    import ledger as L
    with open(_SEQ) as f:
        seqdoc = json.load(f)
    led = L.load_ledger(_LEDSEQ)
    events = seqdoc["events"]

    gate_stress = G3.stress_gate(led, r5a=G3.load_r5a_shoulders())
    assert gate_stress["ok"] is True          # T6b 成果不回退(17/17)
    r5a_full = G3.load_r5a_shoulders()
    H_env = {zh: h["acceptance"]["H"]
             for zh, h in gate_stress["holes"].items()
             if h["acceptance"].get("feasible")}
    assert len(H_env) == 17

    # ① 波账全链: 正常返回(停车线解除), 三节齐, gate_imbalance 不违例
    rep = G3.run_g3(events, led, in_void=frozenset(),
                    rbo_ids=[], r5a=r5a_full)
    for key in ("gate_dag", "gate_stress", "gate_imbalance"):
        assert key in rep, key                # 三节齐
    assert rep["gate_dag"]["ok"] is True
    assert rep["gate_stress"]["ok"] is True
    gate = rep["gate_imbalance"]
    assert gate["ok"] is True and gate["violations"] == []
    assert gate["n_evals"] == 192             # 17 孔 × 6 卸架事件 × 邻墩(端孔 1)
    assert gate["n_skipped_events"] == 0
    # ② Hmax 敏感性对照在册(Hmin 判 PASS 的同账上界记录)
    assert all("ratio_hmax" in e and "e_kernel_hmax" in e
               for e in gate["events"])
    worst_hmax_e = max(e["e_kernel_hmax"] for e in gate["events"])
    print("\n④真账(全桥同波): ok=%s n_evals=%d; Hmax 对照 worst e=%.3f"
          % (gate["ok"], gate["n_evals"], worst_hmax_e))
    for pid in ("PIER08", "PIER09"):
        rec = gate["piers"][pid]
        wr = rec["worst_ratio"]
        print("  %s worst e=%.3f/%.3f ratio=%.2f@%s(seq=%d)"
              % (pid, rec["worst_kernel"]["e_kernel"],
                 rec["worst_kernel"]["kernel_half_w"], wr["ratio"],
                 wr["hole"], wr["seq"]))

    # ③ 串行序 robust 自证: 同账卸架块重排为逐孔串行(逐孔错峰 [工程推断·
    #    非史料] 形态) → 在最小推力读数 + 本门静力图式(δ=0/μ0=0)下仍深红 →
    #    Hmin 口径仍深红(ADJ 失档违例属 R6 层, 本探针只评④门判据)
    blocks = {}
    for e in events:
        if e["etype"] in E.DECENTERING_TYPES:
            blocks.setdefault(e["hole"], []).append(e)
    serial = [dict(e, seq=i + 1) for i, e in enumerate(
        [e for z in sorted(blocks)
         for e in sorted(blocks[z], key=lambda x: x["seq"])])]
    g_serial = G3.imbalance_gate(serial, H_env, ledger=led,
                                 in_void=frozenset(), r5a=r5a_full)
    reds = sum(1 for e in g_serial["events"] if e["verdict"] != "ok")
    wk = max(((r["worst_kernel"]["e_kernel"], r["worst_kernel"]) for r in g_serial["piers"].values() if r["worst_kernel"]))
    util = wk[0] / wk[1]["kernel_half_w"]
    print("  串行序对照(最小推力读数, V 含孔顶反力 R2): red=%d/%d "
          "worst_e=%.3f util=%.3f (临界: 仅边际违例, 读数/图式微扰即翻绿;"
          " δ/μ0 敏感性轴见报告 §9)" % (reds, g_serial["n_evals"], wk[0], util))
    assert g_serial["ok"] is False and reds >= 1
