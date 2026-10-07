# e30_shikongqiao_video/tests/test_p2_g3_dag.py
# -*- coding: utf-8 -*-
"""P2-T5 g3_check.py: G3 第一层(①支撑活跃)+ snapshot 状态机 + 独立Σ交叉验证。

判据(brief 接口节全量):
- Snapshot(seq, present, capacity, by_hole, ...) 逐事件增量推进 —— capacity
  增量维护(事件驱动结点指针, 非每事件全扫; 7.9M 点教训), 全 4070 事件 <10s;
- check_dag 四闸:
  ① 每石 present 后 Σcapacity≥1(荷载分担完整; 与 sequencer._check_capacity_
    invariant 同不变量但**独立实现交叉验证**, T2 跨源钉哲学);
  ② 每石任一时刻至少一条活跃支撑边(capacity>0)直到其自持 stone 边达 1.0;
  ③ RING 专项: 合龙前(CLOSE_RING 前)必须有 centering 边 capacity>0
    (R2 违约=架未立先砌 DAG_RING_BEFORE_ERECT / 无架砌券 DAG_RING_NO_
    CENTERING), 且自持 stone 边在合龙前必须为 0(环未合成不得自持,
    DAG_RING_SELFHOLD_EARLY);
  ④ 幻影残留闸: present 集永不含 in_void 石(双保险, 即便上游漏滤;
    DAG_PHANTOM_IN_VOID)。
- 跨孔(R6 独立重建): g3 不吃 sequencer 的 frontier_trace/derive_frontier,
  从裸事件流重建 per-hole 生命周期(holes_timeline), 落架孔前视 1:
  邻孔须已合龙持荷(禁跳孔落架 DAG_R6_JUMP_DECENTER)/禁相邻孔同落架
  (DAG_R6_ADJ_DECENTERING)。
- W1 双建模债交接: ≥99% 被 RING 实体吞没的 ring_band_overlap 石**不判红**
  (单自持边 Σ=1.0 合规), 只进 run_g3 报告 double_model_placeholders
  (id+吞没率, P1 体素单源度量), 供 P3 视觉隐藏。
- 独立性: g3_check 禁 import sequencer(含传递闭包) —— 两独立实现互证。

五负控: ①删 RING centering 边→UNSUPPORTED ②架未立先砌券→BEFORE_ERECT
③自持边提前衰减(Σ 掉破 1)→UNSUPPORTED / 提前自持→SELFHOLD_EARLY
④in_void 石混入 present→幻影闸红 ⑤邻孔错序(跳孔落架/相邻同落架)→
g3 自建 R6 判红。
微账几何同 test_p2_sequencer(3 孔 ARCH01-03, 单源 GM 现算); 真账 4070 事件
全链(存在性 skip)为性能(<10s)+W1 清单+trace 交叉核的常驻断言。
"""
import copy
import json
import os
import subprocess
import sys
import time

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "3d"))

import events as E
import ledger as L
import centering as CEN
import geom_math as GM
import facts as F
import sequencer as SQ          # 仅造微账 fixture 用; g3 本体禁 import(见独立性测)
import g3_check as G3

MICRO_RING_T = 0.41
EPS = 0.15
MIN_HOLD = 3
R7_Z = 5.0
TOL = 1e-9


# ---------------------------------------------------------------------------
# 合成 3 孔微账(同 test_p2_sequencer 几何: 全部由 GM 现算, 不硬编码几何值)
# ---------------------------------------------------------------------------

def _wstd(w, h, d):
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
        half_a = GM.SPANS[ai] / 2.0
        for ci, dz in ((0, 0.60), (1, 0.45), (2, 0.30), (3, 0.15)):
            for fi, face in enumerate(("EAST", "WEST")):
                led["stones"].append(L.new_stone(
                    zone, face, "IMPOST", ci, 0, "wedge-std",
                    _wstd(1.05, 0.1, 0.42),
                    [xc + (half_a + 0.60) * (1 if face == "EAST" else -1),
                     4.8, springer - dz, 0.0, 0.0, 0.0], "qingshi"))
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


def _resequence(events):
    """保序重编号 seq=1..N(负控重排后的良构化)。"""
    for k, e in enumerate(events):
        e["seq"] = k + 1
    return events


@pytest.fixture(name="micro")
def micro_fixture():
    led = _micro_ledger()
    errs = L.validate_ledger(led)
    assert errs == [], "微账自身非法: %s" % errs
    return led


@pytest.fixture(name="sched")
def scheduled_fixture(micro):
    """真链产物: build_sequence 事件流 + apply_support_edges 回写副本。"""
    res = SQ.build_sequence(micro, _micro_centerings(), eps=EPS,
                            min_hold=MIN_HOLD)
    assert SQ.check_sequence(res, micro, _micro_centerings(),
                             eps=EPS, min_hold=MIN_HOLD) == []
    return SQ.apply_support_edges(micro, res), res


def _all(events, led, **kw):
    return G3.check_dag_all(events, led, **kw)


def _ring_sid(zone, face="EAST", which=0, led=None):
    sids = sorted(s["id"] for s in led["stones"]
                  if s["id"].startswith(zone + "." + face + ".RING."))
    return sids[which]


# ---------------------------------------------------------------------------
# 正控: 全流 0 违例 + snapshot 结构 + Σ 互补形状
# ---------------------------------------------------------------------------

def test_positive_full_stream_clean(sched):
    (led2, res), micro = sched, None
    events = res["events"]
    viols, stats = _all(events, led2)
    assert viols == [], viols[:8]
    assert stats["n_snapshots"] == len(events)
    assert stats["n_stone_checks"] > 0
    assert stats["elapsed_s"] < 10.0
    # 终态 present = 全部入日程石
    sched_ids = {e["stone_id"] for e in events
                 if e["etype"] in E.MASONRY_TYPES and e.get("stone_id")}
    assert stats["final_present"] == sched_ids
    assert "ARCH01.EAST.RING.C00.B01" in sched_ids


def test_snapshot_capacity_complementary_at_wedges(sched):
    """RING 石 centering/stone 双边在每个 WEDGE/CLEAR 结点 Σ==1(同点互补)。"""
    led2, res = sched
    events = res["events"]
    zone = "ARCH01"
    rings = sorted(s["id"] for s in led2["stones"]
                   if s["id"].startswith(zone + ".EAST.RING."))
    knots = [e["seq"] for e in events
             if e["hole"] == zone
             and e["etype"] in ("WEDGE_RELEASE", "CENTERING_CLEAR")]
    assert knots
    want = set(knots)
    seen = 0
    for snap in G3.snapshots(events, led2):
        if snap.seq not in want:
            continue
        for sid in rings:
            if sid not in snap.present:
                continue
            edges = G3.stone_edges(led2)[sid]
            tot = sum(L.edge_capacity(ed, snap.seq) for ed in edges)
            assert tot == pytest.approx(1.0, abs=1e-9), (sid, snap.seq, tot)
            seen += 1
    assert seen == len(rings) * len(knots)


def test_holes_timeline_matches_frontier_trace(sched):
    """g3 独立重建的 per-hole 生命周期与构造侧 frontier_trace 同值(交叉核)。"""
    led2, res = sched
    events = res["events"]
    tl = G3.holes_timeline(events)
    by_state = {}
    for t in res["frontier_trace"]:
        by_state.setdefault(t["hole"], {})[t["state"]] = t["at_seq"]
    assert set(tl) == set(by_state)
    for zone, h in tl.items():
        ref = by_state[zone]
        assert h["close"] == ref["RING_CLOSED"]
        assert h["dstart"] == ref["DECENTERING"]
        assert h["clear"] == ref["CLEARED"]
        # 立架锚 = 本孔首个 HOLD_EVENT, 且先于全部 RING 置放
        ring_places = [e["seq"] for e in events
                       if e["hole"] == zone and e["etype"] == "PLACE_STONE"
                       and G3.stone_role(e["stone_id"]) == "RING"]
        assert ring_places and h["erect"] < min(ring_places)


def test_snapshot_fields_and_copy(sched):
    led2, res = sched
    events = res["events"]
    it = G3.snapshots(events, led2)
    snap = next(it)
    assert snap.seq == 1 and snap.event is events[0]
    first_sid = events[0]["stone_id"]
    assert snap.present == {first_sid}
    assert snap.by_hole["ARCH01"]["stones"] == {first_sid}
    held = snap.copy()
    for snap2 in it:
        pass
    # 复本是独立快照: 后续推进不改变早先 copy
    assert held.present == {first_sid}
    assert held.seq == 1


def test_double_model_scan_empty_and_missing(sched, micro):
    led2, res = sched
    rep = G3.double_model_scan(led2, rbo_ids=[])
    assert rep["placeholders"] == [] and rep["ratio_by_id"] == {}
    rep2 = G3.double_model_scan(led2, rbo_ids=["ARCH01.EAST.NOPE.C99.B99"])
    assert rep2["missing_ids"] == ["ARCH01.EAST.NOPE.C99.B99"]
    assert rep2["placeholders"] == []


# ---------------------------------------------------------------------------
# 负控五组
# ---------------------------------------------------------------------------

def test_neg1_ring_centering_edge_removed(sched):
    """①删某 RING 石 centering 边 → UNSUPPORTED 点名该石。"""
    led2, res = sched
    events = res["events"]
    sid = _ring_sid("ARCH02", which=0, led=led2)
    tam = copy.deepcopy(led2)
    st = next(s for s in tam["stones"] if s["id"] == sid)
    n0 = len(st["support_edges"])
    st["support_edges"] = [e for e in st["support_edges"]
                           if e.get("type") != "centering"]
    assert len(st["support_edges"]) == n0 - 1
    viols, _stats = _all(events, tam)
    hits = [v for v in viols if G3.CODE_UNSUPPORTED in v and sid in v]
    assert hits, viols[:10]


def test_neg2_ring_place_before_erect(sched):
    """②架未立先砌券(PLACE 排到立架前) → DAG_RING_BEFORE_ERECT 必红。"""
    led2, res = sched
    events = copy.deepcopy(res["events"])
    zone = "ARCH03"
    sid = _ring_sid(zone, which=0, led=led2)
    place = next(e for e in events if e.get("stone_id") == sid)
    erect = next(e for e in events if e["hole"] == zone
                 and e["etype"] == "HOLD_EVENT")
    events.remove(place)
    idx = events.index(erect)
    events.insert(idx, place)
    _resequence(events)
    viols, _stats = _all(events, led2)
    assert any(G3.CODE_RING_BEFORE_ERECT in v and sid in v for v in viols), \
        viols[:10]


def test_neg3_selfhold_edge_never_grows(sched):
    """③石自持边提前衰减(g3 层测 Σ 掉破 1): stone 边恒 0 → 卸楔各档 Σ<1。"""
    led2, res = sched
    events = res["events"]
    sid = _ring_sid("ARCH01", which=0, led=led2)
    tam = copy.deepcopy(led2)
    st = next(s for s in tam["stones"] if s["id"] == sid)
    place = min(pt[0] for ed in st["support_edges"]
                for pt in ed["capacity_curve"])
    for ed in st["support_edges"]:
        if ed.get("type") == "stone":
            ed["capacity_curve"] = [[place, 0.0]]   # 自持永不成长
    viols, _stats = _all(events, tam)
    hits = [v for v in viols if G3.CODE_UNSUPPORTED in v and sid in v]
    assert hits, viols[:10]
    # Σ 掉破 1 的量级可见(如 Σ=0.75/0.5/0.25/0)
    assert any("Σcapacity=0." in v for v in hits)


def test_neg3b_selfhold_before_close(sched):
    """③b自持边提前置 1(合龙前环自持) → DAG_RING_SELFHOLD_EARLY 必红。"""
    led2, res = sched
    events = res["events"]
    sid = _ring_sid("ARCH02", which=0, led=led2)
    tam = copy.deepcopy(led2)
    st = next(s for s in tam["stones"] if s["id"] == sid)
    for ed in st["support_edges"]:
        if ed.get("type") == "stone":
            ed["capacity_curve"] = [[min(pt[0] for e2 in st["support_edges"]
                                         for pt in e2["capacity_curve"]),
                                     1.0]]
    viols, _stats = _all(events, tam)
    assert any(G3.CODE_RING_SELFHOLD_EARLY in v and sid in v for v in viols), \
        viols[:10]


def test_neg4_phantom_in_void_mixed_in(sched, micro):
    """④in_void 石混入 present → 幻影闸红, 且 present 拒收该石。"""
    led2, res = sched
    events = copy.deepcopy(res["events"])
    victim = next(s["id"] for s in micro["stones"]
                  if G3.stone_role(s["id"]) == "SPANDREL")
    in_void = {victim}
    ghost = dict(events[0], stone_id=victim, seq=len(events) + 1)
    events.append(ghost)
    _resequence(events)
    viols, stats = _all(events, led2, in_void=in_void)
    assert any(G3.CODE_PHANTOM in v and victim in v for v in viols), viols[:10]
    assert victim not in stats["final_present"]


def test_neg5_jump_hole_decenter(sched):
    """⑤邻孔错序(跳孔落架): ARCH03 落架块插到 ARCH02 合龙前 → g3 自建
    R6 判红(不吃 sequencer 的 frontier)。"""
    led2, res = sched
    events = copy.deepcopy(res["events"])
    blk = [e for e in events if e["hole"] == "ARCH03"
           and e["etype"] in ("DECENTER_START", "WEDGE_RELEASE",
                              "CENTERING_CLEAR")]
    rest = [e for e in events if e not in blk]
    erect2 = next(i for i, e in enumerate(rest)
                  if e["hole"] == "ARCH02" and e["etype"] == "HOLD_EVENT")
    evs2 = _resequence(rest[:erect2 + 1] + blk + rest[erect2 + 1:])
    viols, _stats = _all(evs2, led2)
    assert any(G3.CODE_R6_JUMP in v for v in viols), viols[:12]


def test_neg5b_adjacent_holes_decenter_together(sched):
    """⑤b相邻孔同落架: ARCH02 落架块插进 ARCH01 落架窗 → ADJ_DECENTERING。"""
    led2, res = sched
    events = copy.deepcopy(res["events"])
    blk = [e for e in events if e["hole"] == "ARCH02"
           and e["etype"] in ("DECENTER_START", "WEDGE_RELEASE",
                              "CENTERING_CLEAR")]
    rest = [e for e in events if e not in blk]
    anchor = next(i for i, e in enumerate(rest)
                  if e["etype"] == "DECENTER_START"
                  and e["hole"] == "ARCH01") + 1
    evs2 = _resequence(rest[:anchor] + blk + rest[anchor:])
    viols, _stats = _all(evs2, led2)
    assert any(G3.CODE_R6_ADJ in v for v in viols), viols[:12]


# ---------------------------------------------------------------------------
# 机制闸
# ---------------------------------------------------------------------------

def test_non_monotonic_events_rejected(sched):
    led2, res = sched
    events = copy.deepcopy(res["events"][:5])
    events[2]["seq"] = events[1]["seq"]
    with pytest.raises(ValueError, match="seq"):
        list(G3.snapshots(events, led2))


def test_fully_floating_stone_no_active_support(sched):
    """无边石: UNSUPPORTED + NO_ACTIVE_SUPPORT 同点双码(全浮动)。"""
    led2, res = sched
    events = copy.deepcopy(res["events"])
    sid = next(s["id"] for s in led2["stones"]
               if G3.stone_role(s["id"]) == "BACK")
    tam = copy.deepcopy(led2)
    st = next(s for s in tam["stones"] if s["id"] == sid)
    place = next(e["seq"] for e in events if e.get("stone_id") == sid)
    st["support_edges"] = [{"type": "stone",
                            "capacity_curve": [[place, 0.0]]}]
    viols, _stats = _all(events, tam)
    assert any(G3.CODE_UNSUPPORTED in v and sid in v for v in viols)
    assert any(G3.CODE_NO_ACTIVE in v and sid in v for v in viols)


def test_g3_check_pure_no_dirty_mutation(sched):
    """check_dag 对同一 snapshot 幂等(纯读, 不清 dirty)。"""
    led2, res = sched
    events = res["events"]
    for snap in G3.snapshots(events, led2):
        pass
    v1 = G3.check_dag(snap)
    v2 = G3.check_dag(snap)
    assert v1 == v2


def test_g3_independent_no_sequencer_import():
    """独立性: g3_check 导入闭包不含 sequencer(两独立实现互证的前提)。"""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    code = ("import sys; sys.path.insert(0, %r); import g3_check; "
            "print('sequencer' in sys.modules)" % os.path.join(root, "3d"))
    out = subprocess.run([sys.executable, "-c", code], cwd=root,
                         capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip().endswith("False"), out.stdout


# ---------------------------------------------------------------------------
# 真账 5935 石全链(存在性 skip): 4070 事件 <10s + W1 清单 + trace 交叉核
# ---------------------------------------------------------------------------

_HERE = os.path.dirname(os.path.abspath(__file__))
_SEQ = os.path.join(_HERE, "..", "3d", "out", "sequence.json")
_LEDSEQ = os.path.join(_HERE, "..", "3d", "out", "ledger_sequenced.json")
_EXCL = os.path.join(_HERE, "..", "3d", "out", "print", "excluded_ids.json")

_NEED = [_SEQ, _LEDSEQ]


@pytest.mark.skipif(not all(os.path.exists(p) for p in _NEED),
                    reason="out/sequence.json+ledger_sequenced.json 不在盘上")
def test_real_ledger_g3_fullchain():
    with open(_SEQ) as f:
        seqdoc = json.load(f)
    led = L.load_ledger(_LEDSEQ)
    events = seqdoc["events"]
    assert len(events) == 4070

    t0 = time.perf_counter()
    viols, stats = G3.check_dag_all(events, led)
    el = time.perf_counter() - t0
    print("g3 真账 4070 事件 snapshot+check: %.2fs (含 in_void 推导)"
          % el)
    assert viols == [], viols[:10]     # 除 W1 白名单外零违例(清单不判红)
    assert stats["n_snapshots"] == 4070
    assert el < 10.0, "性能闸: %.2fs ≥ 10s" % el
    assert len(stats["final_present"]) == 3883

    # in_void 推导与 excluded_ids.json 逐位相等(幻影闸单源交叉核)
    in_void = G3.derive_in_void(led)
    if os.path.exists(_EXCL):
        with open(_EXCL) as f:
            excl = json.load(f)
        assert in_void == set(excl["buckets"]["in_void"])

    # 幻影残留闸负控(真账): 混入一枚 in_void 石必红
    if os.path.exists(_EXCL):
        with open(_EXCL) as f:
            excl = json.load(f)
        victim = sorted(excl["buckets"]["in_void"])[0]
        evs2 = copy.deepcopy(events)
        evs2.append(dict(evs2[-1], stone_id=victim, seq=len(evs2) + 1))
        viols2, _ = G3.check_dag_all(evs2, led, in_void=in_void)
        assert any(G3.CODE_PHANTOM in v and victim in v for v in viols2)

    # W1 双建模债清单: ≥99% 吞没的 rbo 石进报告, 不判红, 单自持边合规
    # (T6 起 run_g3 串 gate_stress; 真账中央 6 孔 acceptance 不可行 →
    #  停车线 raise, 报告挂异常 .report —— 两门数据不受影响)
    try:
        rep = G3.run_g3(events, led, in_void=in_void)
    except G3.G3_FROZEN_GEOMETRY_CONFLICT as exc:
        rep = exc.report
    ph = rep["double_model_placeholders"]
    print("double_model_placeholders: %d 块" % len(ph))
    for p in ph:
        print("  %s  吞没率=%.4f" % (p["id"], p["swallow_ratio"]))
    assert ph, "W1 清单为空 —— 吞没扫描失效"
    by_id = {s["id"]: s for s in led["stones"]}
    for p in ph:
        st = by_id[p["id"]]
        edges = st.get("support_edges", [])
        tot = sum(L.edge_capacity(e, pt[0])
                  for e in edges for pt in e["capacity_curve"])
        # 单自持边: 每个 knot 点 Σ==1.0(这就是 g3 不判它们的理由)
        assert tot >= len(edges) - TOL
        xs = sorted({pt[0] for e in edges for pt in e["capacity_curve"]})
        for x in xs:
            assert sum(L.edge_capacity(e, x) for e in edges) \
                == pytest.approx(1.0, abs=1e-9)
    assert rep["gate_dag"]["violations"] == []
    print("run_g3: dag %.2fs, 吞没扫描 %.2fs"
          % (rep["gate_dag"]["elapsed_s"],
             rep["double_model_scan"]["elapsed_s"]))
