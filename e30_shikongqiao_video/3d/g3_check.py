# e30_shikongqiao_video/3d/g3_check.py
# -*- coding: utf-8 -*-
"""P2-T5+T6 g3_check.py: G3 第一层(①支撑活跃)+ snapshot 状态机 + 第三层
(③压力线刚块链, acceptance/robustness 双 case + 停车线)。

定位(三层力学门: ①支撑活跃+③压力线在本文件; ④推力包络 T7 后续扩展):
  sequencer 构造序列并自带 check_sequence; 本文件**不 import sequencer**
  (含传递闭包, 测试钉死) —— 从裸事件流+支撑边账独立重建建造快照, 与
  sequencer 的 Σ≥1 不变量做**两实现互证**(同 T2 跨源钉哲学)。frontier
  亦不吃 sequencer 的 derive_frontier/check_frontier, 由 holes_timeline
  从裸事件流独立重建后自核 R6 前视 1(跳孔落架/相邻同落架)。

接口:
  snapshots(events, ledger, in_void=None) -> iter[Snapshot]
      逐事件推进(单对象复用; 需留存用 snap.copy())。capacity 增量维护:
      每边只有在其 capacity_curve 结点(knot)处才重估(事件驱动小顶堆指针),
      绝不每事件全扫 —— 真账 4070 事件×4076 边在秒级(7.9M 点教训)。
      完整性论证: capacity_curve 分段线性, Σ(各边)在相邻结点间线性,
      故在**每个结点+每次置放**处核 Σ 即覆盖连续全程(与 sequencer
      _check_capacity_invariant 同一覆盖论证, 独立重写)。
  check_dag(snap) -> [viol]
      对 snap 这一步(事件级违例 + dirty 石级复核)返回违例码串, 纯读幂等。
      流式驱动用 check_dag_all(聚合全程)。
  check_dag_all(events, ledger, in_void=None) -> (viols, stats)
  holes_timeline(events) -> {hole: {erect,close,dstart,clear,holds}}
      立架锚=本孔首个 HOLD_EVENT(stone_id=="CEN-"+hole) —— 事件词表无
      ERECT 类, 这是 sequencer 下唯一合法形态(T4 交接 §6.5)。
  derive_in_void(ledger) -> frozenset
      幻影桶: build_scene2.classify_stones(与 sequencer/excluded_ids.json
      同一单源; 代理浅拷贝防 clipped 标污染原账)。判红逻辑独立, 单源复用
      属"双保险"定位(裁1)。
  double_model_scan(ledger, rbo_ids, threshold) -> dict
      W1 交接: ring_band_overlap 石被 RING∪ 实体体积吞没率(P1 同栅格度量
      p1a_slice._voxel_unique_vol 单源, bbox 预筛+面级栅格), ≥threshold 者
      进 placeholders。**g3 不判它们红**(单自持边 Σ=1.0 合规), 清单仅供
      P3 视觉隐藏。注: 主控口径 28 块(T4 修复轮会话内实测未落盘)与本扫描
      复现口径在阈值敏感带(0.985-0.99)内有出入, 以本扫描落盘清单为准
      (幂等可复现, 报告附敏感带明细)。
  run_g3(events, ledger, ..., r5a=None) -> report dict
      串 gate_dag(本文件)+double_model 清单(W1)+gate_stress(③压力线);
      T7 追加 gate_thrust 节(report 键即扩展点; Snapshot.present/capacity/
      by_hole/holes+copy() 即其所需快照面)。gate_stress.ok=False →
      raise G3_FROZEN_GEOMETRY_CONFLICT(停车线, 停报主控)。

T6 ③压力线(Heyman 刚块链; 见该节头注):
  pressure_line(ring_stones, extra_loads, band_in_out_fns, H_range,
                dzdx_fn=None, ring_t=None) -> dict
      brief 接口: {feasible, H:[min,max], polyline:[(x,z)...]}+诊断键。
      左右半环各扫 H(可行 y0 区间交), H 区间取两半环之交。
  stress_gate(ledger, r5a=None) -> dict
      逐孔 acceptance(RING+R5a 肩荷)/robustness(裸环) 双 case; 违例码
      STRESS_ACCEPTANCE_INFEASIBLE 点名孔。H 区间表在 holes[zh]。
  load_r5a_shoulders(path=None) -> {zone: [stone_id]}
      R5a 锁固肩集合单源读取(out/sequence.json .SHOULDER. 阶段, 1307 石)。
  plot_hole_pressure(hole, ledger, zone, path) -> str
      压力线诊断图(intrados/extrados/左右压力线叠画; matplotlib Agg)。

违例码(全部点名石/孔+seq, 字符串前缀可 grep):
  DAG_UNSUPPORTED          Σcapacity < 1(荷载分担不完整/全无)
  DAG_NO_ACTIVE_SUPPORT    无任何 capacity>0 边且自持 stone 边未达 1(全浮动)
  DAG_RING_NO_CENTERING    RING 石在合龙前 centering 边 capacity≤0(无架砌券)
  DAG_RING_BEFORE_ERECT    RING 石置放先于本孔立架锚(架未立先砌券)
  DAG_RING_SELFHOLD_EARLY  RING 石在合龙前自持 stone 边 >0(环未合成不自持)
  DAG_PHANTOM_IN_VOID      in_void 幻影石混入事件流/present(拒收入集)
  DAG_R6_JUMP_DECENTER     落架孔某邻孔未达合龙持荷(跳孔落架, 前视 1)
  DAG_R6_ADJ_DECENTERING   相邻孔同落架
  STRESS_ACCEPTANCE_INFEASIBLE  ③压力线 acceptance 无可行 H(停车线)

语义纪律: capacity=荷载分担份额(P2-T4 修复轮裁2, ledger.py 定稿);
石重(体积单源)①层无需, T6 按 sequencer.stone_weight 同一单源
(families.family_mesh+export_print.signed_volume×密度)独立取数
(本文件禁 import sequencer, 测试钉死), 禁第二套。

Python 3.9.6 纯 stdlib(blender-free; double_model_scan 另需 numpy,
经 p1a_slice blender-free 段)。
"""
import heapq
import json
import math
import os
import time
from typing import Any, Dict, List, Optional, Set, Tuple

import ledger as L
import events as E
import facts as F
import geom_math as GM

TOL = 1e-9                 # Σcapacity 判定容差(同 sequencer)
RING_ROLE = "RING"
CEN_PREFIX = "CEN-"

CODE_UNSUPPORTED = "DAG_UNSUPPORTED"
CODE_NO_ACTIVE = "DAG_NO_ACTIVE_SUPPORT"
CODE_RING_NO_CENTERING = "DAG_RING_NO_CENTERING"
CODE_RING_BEFORE_ERECT = "DAG_RING_BEFORE_ERECT"
CODE_RING_SELFHOLD_EARLY = "DAG_RING_SELFHOLD_EARLY"
CODE_PHANTOM = "DAG_PHANTOM_IN_VOID"
CODE_R6_JUMP = "DAG_R6_JUMP_DECENTER"
CODE_R6_ADJ = "DAG_R6_ADJ_DECENTERING"

DEFAULT_EXCLUDED_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "out", "print", "excluded_ids.json")
SWALLOW_THRESHOLD = 0.99   # W1: ≥99% 被 RING 实体吞没 → 双建模占位[工程参数]


def stone_role(sid):
    # type: (Any) -> str
    """family_key 形制 ZONE.FACE.ROLE.Cxx.Bxx 的 ROLE 段; 非石 id 返回 "?"。"""
    if not isinstance(sid, str):
        return "?"
    parts = sid.split(".")
    return parts[2] if len(parts) >= 3 else "?"


def hole_of_sid(sid):
    # type: (Any) -> str
    if not isinstance(sid, str):
        return ""
    return sid.split(".")[0]


def stone_edges(ledger):
    # type: (Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]
    """sid -> support_edges(仅非空边; 曲线表只读消费)。"""
    out = {}  # type: Dict[str, List[Dict[str, Any]]]
    for s in ledger.get("stones", []):
        edges = s.get("support_edges") or []
        if edges:
            out[s["id"]] = list(edges)
    return out


def derive_in_void(ledger):
    # type: (Dict[str, Any]) -> frozenset
    """裁1 幻影桶(单源 build_scene2.classify_stones, 代理浅拷贝防污染;
    与 sequencer._in_void_ids 同源同法 —— 判红逻辑在本文件独立)。"""
    import build_scene2 as BS2
    proxies = [dict(s, params=dict(s.get("params") or {}))
               for s in ledger.get("stones", [])]
    cls = BS2.classify_stones(proxies)
    return frozenset(sid for sid, (status, _polys) in cls.items()
                     if status == "inside")


def holes_timeline(events):
    # type: (List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]
    """从裸事件流独立重建 per-hole 生命周期(不吃 sequencer 任何产物)。
    erect=本孔首个 HOLD_EVENT(stone_id=="CEN-"+hole); holds=全部该形
    HOLD seq 表(R4 持荷窗核料); close/dstart/clear=各自首事件 seq。"""
    tl = {}  # type: Dict[str, Dict[str, Any]]
    for e in events:
        zh = e.get("hole") or ""
        h = tl.setdefault(zh, {"erect": None, "close": None,
                               "dstart": None, "clear": None,
                               "holds": []})
        et = e.get("etype")
        sid = e.get("stone_id")
        seq = e.get("seq")
        if et == "HOLD_EVENT":
            if isinstance(sid, str) and sid.startswith(CEN_PREFIX) \
                    and sid == CEN_PREFIX + zh and h["erect"] is None:
                h["erect"] = seq
            h["holds"].append(seq)
        elif et == "CLOSE_RING":
            if h["close"] is None:
                h["close"] = seq
        elif et == "DECENTER_START":
            if h["dstart"] is None:
                h["dstart"] = seq
        elif et == "CENTERING_CLEAR":
            if h["clear"] is None:
                h["clear"] = seq
    return tl


class Snapshot(object):
    """建造快照(单对象逐事件复用; 需留存请 copy())。

    字段:
      seq       当前事件 seq
      event     当前事件 dict(引用, 不拷贝)
      present   set[已砌石 id](幻影石拒收, 永不含 in_void)
      capacity  {(sid, edge_idx): 最近结点/置放处的 capacity 值}
                —— 结点间曲线线性, 结点值即采样值; 下游门(T6/T7)读它
                时注意语义是"最近结点处份额", 精确插值用 L.edge_capacity
      by_hole   {hole: {"stones": set, "rings": set}}(present 子集视图)
      holes     {hole: lifecycle dict(同 holes_timeline 形态, 增量态)}
      dirty     {sid: [待核 x, ...]}(本步置放或曲线结点触发; check_dag 的
                复核面 —— 每个 x 一个核点, 同事件多结点逐一核, 端点全覆盖)
      violations本步事件级违例(幻影/R6; 石级违例由 check_dag 现算)
      in_void   frozenset(幻影桶引用)
    """

    __slots__ = ("seq", "event", "present", "capacity", "by_hole", "holes",
                 "dirty", "violations", "in_void", "_edges", "_placed_at",
                 "_heap")

    def __init__(self, edges, in_void):
        # type: (Dict[str, List[Dict[str, Any]]], frozenset) -> None
        self.seq = 0
        self.event = None  # type: Optional[Dict[str, Any]]
        self.present = set()
        self.capacity = {}  # type: Dict[Tuple[str, int], float]
        self.by_hole = {}  # type: Dict[str, Dict[str, Set[str]]]
        self.holes = {}  # type: Dict[str, Dict[str, Any]]
        self.dirty = {}  # type: Dict[str, List[int]]
        self.violations = []  # type: List[str]
        self.in_void = in_void
        self._edges = edges
        self._placed_at = {}  # type: Dict[str, int]
        self._heap = []  # type: List[Tuple[int, str, int]]

    def copy(self):
        # type: () -> Snapshot
        cl = Snapshot(self._edges, self.in_void)
        cl.seq = self.seq
        cl.event = self.event
        cl.present = set(self.present)
        cl.capacity = dict(self.capacity)
        cl.by_hole = {zh: {"stones": set(v["stones"]),
                           "rings": set(v["rings"])}
                      for zh, v in self.by_hole.items()}
        cl.holes = {zh: {k: (list(v) if isinstance(v, list) else v)
                         for k, v in h.items()}
                    for zh, h in self.holes.items()}
        cl.dirty = dict(self.dirty)
        cl.violations = list(self.violations)
        cl._placed_at = dict(self._placed_at)
        cl._heap = list(self._heap)
        return cl


def _edge_knots(edge):
    # type: (Dict[str, Any]) -> List[int]
    """曲线结点 x 升序去重(形态非法→空表, 交由 Σ=0 判红)。"""
    pts = edge.get("capacity_curve")
    if not isinstance(pts, (list, tuple)):
        return []
    xs = set()
    for p in pts:
        if isinstance(p, (list, tuple)) and len(p) == 2 \
                and isinstance(p[0], (int, float)) \
                and not isinstance(p[0], bool):
            xs.add(int(p[0]))
    return sorted(xs)


def snapshots(events, ledger, in_void=None):
    # type: (List[Dict[str, Any]], Dict[str, Any], Optional[Set[str]]) -> Any
    """逐事件推进 snapshot(生成器; 单对象复用, 留存用 snap.copy())。

    增量机制: 每边结点入小顶堆 (x, sid, edge_idx); 推进到 seq 时弹尽
    x<=seq 的结点(精确在结点 x 处重估该边), dirty 记 sid→min(x)。
    置放时: 先应用该边全部 x<=place 的结点(左钳语义内联), 再入堆
    x>place 的未来结点。幻影石(④)拒收入集并记 DAG_PHANTOM_IN_VOID;
    落架事件记 R6 前视 1 跨孔核(邻孔须已合龙持荷/禁相邻同落架)。
    events 的 seq 必须严格递增(违者 ValueError —— g3 不猜错序流)。
    """
    if in_void is None:
        in_void = derive_in_void(ledger)
    else:
        in_void = frozenset(in_void)
    edges = stone_edges(ledger)
    snap = Snapshot(edges, in_void)

    # R6 邻接域: 事件孔 ∪ 石账孔(无事件孔也参与邻接判, 防"空档孔漏过"。
    # 同 T4 check_frontier 的 zones 语义, 但从本侧两个来源独立取集。)
    zones = {e.get("hole") for e in events if e.get("hole")}
    for s in ledger.get("stones", []):
        zones.add(hole_of_sid(s.get("id")))
    zone_order = sorted(z for z in zones if z)
    rank_of = {z: i for i, z in enumerate(zone_order)}

    prev_seq = None
    for ev in events:
        seq = ev.get("seq")
        if isinstance(seq, bool) or not isinstance(seq, int) \
                or (prev_seq is not None and seq <= prev_seq):
            raise ValueError(
                "snapshots: 事件 seq 必须为 int 且严格递增 "
                "(got %r after %r) —— g3 不猜错序事件流" % (seq, prev_seq))
        prev_seq = seq
        snap.seq = seq
        snap.event = ev
        snap.dirty = {}
        snap.violations = []
        et = ev.get("etype")
        zh = ev.get("hole") or ""
        sid = ev.get("stone_id")
        h = snap.holes.get(zh)

        # -- 事件级: 幻影残留闸(双保险, 拒收入集) --
        if sid is not None and sid in snap.in_void:
            snap.violations.append(
                "%s 石 %s seq=%d(%s) 属 in_void 桶, present 拒收"
                % (CODE_PHANTOM, sid, seq, et))
            if et in E.MASONRY_TYPES:
                _advance_knots(snap, seq)
                yield snap
                continue

        if et in ("PLACE_STONE", "ADD_FILL") and sid is not None:
            _place_stone(snap, sid, seq)
        elif et == "HOLD_EVENT":
            if h is None:
                h = snap.holes[zh] = {"erect": None, "close": None,
                                      "dstart": None, "clear": None,
                                      "holds": []}
            if isinstance(sid, str) and sid == CEN_PREFIX + zh \
                    and h["erect"] is None:
                h["erect"] = seq
            h["holds"].append(seq)
        elif et == "CLOSE_RING":
            if h is None:
                h = snap.holes[zh] = {"erect": None, "close": None,
                                      "dstart": None, "clear": None,
                                      "holds": []}
            if h["close"] is None:
                h["close"] = seq
        elif et == "DECENTER_START":
            if h is None:
                h = snap.holes[zh] = {"erect": None, "close": None,
                                      "dstart": None, "clear": None,
                                      "holds": []}
            if h["dstart"] is None:
                h["dstart"] = seq
            _check_r6(snap, zh, seq, zone_order, rank_of)
        elif et == "CENTERING_CLEAR":
            if h is None:
                h = snap.holes[zh] = {"erect": None, "close": None,
                                      "dstart": None, "clear": None,
                                      "holds": []}
            if h["clear"] is None:
                h["clear"] = seq

        _advance_knots(snap, seq)
        yield snap


def _lifecycle(snap, zh):
    # type: (Snapshot, str) -> Dict[str, Any]
    h = snap.holes.get(zh)
    if h is None:
        h = snap.holes[zh] = {"erect": None, "close": None, "dstart": None,
                              "clear": None, "holds": []}
    return h


def _place_stone(snap, sid, seq):
    # type: (Snapshot, str, int) -> None
    """置放: 入 present/by_hole, 应用边曲线 x<=seq 段(容量缓存取 seq 处
    插值), 未来结点入堆。核点=置放 seq(石只在 present 后受核)。"""
    zh = hole_of_sid(sid)
    snap.present.add(sid)
    bh = snap.by_hole.setdefault(zh, {"stones": set(), "rings": set()})
    bh["stones"].add(sid)
    if stone_role(sid) == RING_ROLE:
        bh["rings"].add(sid)
    snap._placed_at[sid] = seq
    snap.dirty[sid] = [seq]
    for i, ed in enumerate(snap._edges.get(sid, ())):
        for x in _edge_knots(ed):
            if x <= seq:
                # x<seq 的迟到结点只改容量缓存(核点仍=置放 seq, 边曲线在
                # seq 处的精确插值由 edge_capacity 现算)
                snap.capacity[(sid, i)] = L.edge_capacity(ed, seq)
            else:
                heapq.heappush(snap._heap, (x, sid, i))


def _advance_knots(snap, seq):
    # type: (Snapshot, int) -> None
    """弹尽 x<=seq 的曲线结点, 在结点 x 处重估该边; 每个结点 x 都是
    独立核点(dirty 列表), 同事件多结点逐一核 —— 分段线性端点全覆盖。"""
    heap = snap._heap
    while heap and heap[0][0] <= seq:
        x, sid, i = heapq.heappop(heap)
        ed = snap._edges.get(sid, ())[i]
        snap.capacity[(sid, i)] = L.edge_capacity(ed, x)
        snap.dirty.setdefault(sid, []).append(x)


def _supported_at(h, s):
    # type: (Dict[str, Any], int) -> bool
    """孔在事件 seq=s 时是否 ≥ CLOSED_SUPPORTED(独立重建, 同 derive_
    frontier 语义): 已合龙且 (close, dstart) 窗内已有持荷 HOLD 且该 HOLD
    seq<=s(状态按 seq 前进)。"""
    close = h.get("close")
    if close is None or close > s:
        return False
    dstart = h.get("dstart")
    for hs in h.get("holds", ()):
        if hs is None:
            continue
        if close < hs and hs <= s and (dstart is None or hs < dstart):
            return True
    return False


def _decentering_at(h, s):
    # type: (Dict[str, Any], int) -> bool
    dstart = h.get("dstart")
    if dstart is None or dstart > s:
        return False
    clear = h.get("clear")
    return clear is None or clear > s


def _check_r6(snap, zh, seq, zone_order, rank_of):
    # type: (Snapshot, str, int, List[str], Dict[str, int]) -> None
    """R6 前视 1(独立重建): 落架孔的每个既有邻孔须 ≥ 合龙持荷(禁跳孔),
    且不得相邻孔同落架。邻接=排序孔表 i±1(空档孔参与判)。"""
    i = rank_of.get(zh)
    if i is None:
        return
    for j in (i - 1, i + 1):
        if not (0 <= j < len(zone_order)):
            continue
        nz = zone_order[j]
        nh = snap.holes.get(nz)
        if nh is None:
            snap.violations.append(
                "%s 孔 %s 落架(seq=%d)时邻孔 %s 无任何事件(未合龙持荷)"
                % (CODE_R6_JUMP, zh, seq, nz))
            continue
        if _decentering_at(nh, seq):
            snap.violations.append(
                "%s 相邻孔 %s/%s 同落架(seq=%d)" % (CODE_R6_ADJ, zh, nz, seq))
        elif not _supported_at(nh, seq):
            snap.violations.append(
                "%s 孔 %s 落架(seq=%d)时邻孔 %s 未达合龙持荷(跳孔落架)"
                % (CODE_R6_JUMP, zh, seq, nz))


def check_dag(snap):
    # type: (Snapshot) -> List[str]
    """对 snap 这一步的违例(纯读, 幂等): 事件级(snap.violations, 已在
    snapshots 推进时记) + 石级(dirty 面复核, 在 dirty x 处精确插值)。

    石级四闸(在结点/置放 x 处核 —— 分段线性端点覆盖连续全程):
      Σ>=1; 活跃边>0 直到自持达 1; RING 合龙前 centering>0 且自持=0 且
      置放不先于立架。生命周期以 recorded seq 按 x 比对(as-of-x 语义,
      不受结点迟到影响)。"""
    out = list(snap.violations)
    for sid in sorted(snap.dirty):
        edges = snap._edges.get(sid, ())
        for x in sorted(snap.dirty[sid]):
            caps = [L.edge_capacity(ed, x) for ed in edges]
            tot = sum(caps)
            cen_tot = sum(
                caps[k] for k, ed in enumerate(edges)
                if isinstance(ed, dict) and ed.get("type") == "centering")
            stn_tot = sum(
                caps[k] for k, ed in enumerate(edges)
                if isinstance(ed, dict) and ed.get("type") == "stone")
            if tot < 1.0 - TOL:
                out.append(
                    "%s 石 %s seq=%d Σcapacity=%.6f < 1 (荷载分担不完整)"
                    % (CODE_UNSUPPORTED, sid, x, tot))
                if not any(c > TOL for c in caps) and stn_tot < 1.0 - TOL:
                    out.append(
                        "%s 石 %s seq=%d 无任何 capacity>0 支撑边且自持边未达 1"
                        % (CODE_NO_ACTIVE, sid, x))
            if stone_role(sid) == RING_ROLE:
                h = snap.holes.get(hole_of_sid(sid)) or {}
                close = h.get("close")
                if close is None or x < close:
                    if cen_tot <= TOL:
                        out.append(
                            "%s RING 石 %s seq=%d 合龙(seq=%s)前 centering 边 "
                            "capacity=%.6f ≤ 0 (无架砌券)"
                            % (CODE_RING_NO_CENTERING, sid, x, close, cen_tot))
                    if stn_tot > TOL:
                        out.append(
                            "%s RING 石 %s seq=%d 合龙(seq=%s)前自持 stone 边 "
                            "capacity=%.6f > 0 (环未合成不得自持)"
                            % (CODE_RING_SELFHOLD_EARLY, sid, x, close, stn_tot))
                placed = snap._placed_at.get(sid)
                erect = h.get("erect")
                if x == placed and (erect is None or erect > placed):
                    out.append(
                        "%s RING 石 %s seq=%d 置放先于本孔立架锚(erect=%s, "
                        "尚未发生或在本事件之后)"
                        % (CODE_RING_BEFORE_ERECT, sid, placed,
                           erect if erect is not None else "未发生"))
    return out


def check_dag_all(events, ledger, in_void=None):
    # type: (List[Dict[str, Any]], Dict[str, Any], Optional[Set[str]]) -> Tuple[List[str], Dict[str, Any]]
    """流式驱动: 全事件 snapshots + check_dag 聚合。stats 含耗时/快照数/
    石级复核步数/终态 present。"""
    t0 = time.perf_counter()
    viols = []  # type: List[str]
    n_checks = 0
    n_snaps = 0
    for snap in snapshots(events, ledger, in_void=in_void):
        viols.extend(check_dag(snap))
        n_checks += sum(len(xs) for xs in snap.dirty.values())
        n_snaps += 1
        final_present = snap.present
    stats = {
        "n_snapshots": n_snaps,
        "n_stone_checks": n_checks,
        "elapsed_s": time.perf_counter() - t0,
        "final_present": set(final_present) if n_snaps else set(),
    }
    return viols, stats


# ---------------------------------------------------------------------------
# W1 双建模债扫描(ring_band_overlap 石被 RING∪ 实体吞没率)
# ---------------------------------------------------------------------------

def _load_rbo_ids(path=None):
    # type: (Optional[str]) -> List[str]
    p = path or DEFAULT_EXCLUDED_PATH
    if not os.path.exists(p):
        return []
    with open(p) as f:
        excl = json.load(f)
    return list(excl.get("buckets", {}).get("ring_band_overlap", []))


def double_model_scan(ledger, rbo_ids=None, threshold=SWALLOW_THRESHOLD):
    # type: (Dict[str, Any], Optional[List[str]], float) -> Dict[str, Any]
    """逐 rbo 石量 V(stone∩RING∪)/V(stone)(P1 同栅格度量单源:
    p1a_slice._voxel_unique_vol, 2cm 栅格, bbox 预筛, pre-inset 口径)。
    返回 {threshold, n_rbo, ratio_by_id, placeholders[{id,swallow_ratio}],
    missing_ids, elapsed_s}。占位石**不判红**(单自持边 Σ=1.0 合规),
    清单仅供 P3 视觉隐藏(W1 交接)。numpy/p1a_slice 缺失时 raise(度量
    无单源即拒绝出数, 不静默放空)。"""
    import numpy as np  # 延迟重依赖: 仅本扫描需要
    import p1a_slice as P

    t0 = time.perf_counter()
    if rbo_ids is None:
        rbo_ids = _load_rbo_ids()
    by_id = {s["id"]: s for s in ledger.get("stones", [])}
    rings_by_zone = {}  # type: Dict[str, List[str]]
    for s in ledger.get("stones", []):
        if stone_role(s.get("id")) == RING_ROLE:
            rings_by_zone.setdefault(s["id"].split(".")[0], []).append(s["id"])

    mesh_cache = {}  # type: Dict[str, Any]

    def ring_mesh(rid):
        # type: (str) -> Any
        if rid not in mesh_cache:
            rv, rf = P.world_mesh(by_id[rid], {rid: ("out", None)})
            rv = np.asarray(rv, dtype=float)
            tris = P._flat_tris(P.PC._face_tris(rv, rf))
            lo, hi = rv.min(axis=0), rv.max(axis=0)
            mesh_cache[rid] = (rv, tris, lo, hi)
        return mesh_cache[rid]

    ratio_by_id = {}  # type: Dict[str, float]
    missing = []
    for sid in rbo_ids:
        st = by_id.get(sid)
        if st is None:
            missing.append(sid)
            continue
        sv, sf = P.world_mesh(st, {sid: ("out", None)})
        SV = np.asarray(sv, dtype=float)
        lo, hi = SV.min(axis=0), SV.max(axis=0)
        z = sid.split(".")[0]
        rms = []
        for rid in rings_by_zone.get(z, ()):
            rv, tris, rlo, rhi = ring_mesh(rid)
            if bool((rlo <= hi + 1e-9).all() and (rhi >= lo - 1e-9).all()):
                rms.append((rv, tris))
        v_stone, _v_hit, v_unique, _inside = P._voxel_unique_vol(sv, sf, rms)
        ratio_by_id[sid] = (1.0 - v_unique / v_stone) if v_stone > 0 else 0.0
    placeholders = [{"id": sid, "swallow_ratio": ratio_by_id[sid]}
                    for sid in sorted(ratio_by_id,
                                      key=lambda k: (-ratio_by_id[k], k))
                    if ratio_by_id[sid] >= threshold]
    return {
        "threshold": float(threshold),
        "n_rbo": len(rbo_ids or ()),
        "ratio_by_id": ratio_by_id,
        "placeholders": placeholders,
        "missing_ids": missing,
        "elapsed_s": time.perf_counter() - t0,
    }


# ---------------------------------------------------------------------------
# T6 ③压力线(Heyman 刚块链; acceptance/robustness 双 case)
# ---------------------------------------------------------------------------
# 物理口径(冻结, 停车线保护对象):
#   每孔左右半环(crown→springer)各为独立刚块链: 券石按 params 角域切块
#   (重量=export_print.signed_volume×密度 体积单源; 质心=烘焙网格散度质心,
#   与单源体积互证), 给定冠推力 H(水平, 作用高 y0 为自由参数)逐缝递推
#   合力 R_k=R_{k-1}+W_k(等价闭式: V_j=ΣW, M_j=ΣW(x_j-x̄)), R_k 的作用线
#   与块间放射缝(法向同 masonry._arch_normal = facts.arch_dzdx 单源)交点
#   沿缝参数 s 必须 ∈[0, ring_t](带内), 即缝交点落在 [intrados,extrados]。
#   每 H 下 y0 可行区间 = 各缝 y0-区间之交; H 可行 ⟺ 交非空。扫 H 网格
#   (0.1-1.2×qL²/8f, q:=全孔荷载/跨长)取可行区间, 边界二分细化; 网格边
#   被触及时自动外扩(删失防护, 覆盖机制非几何参数)。
#   双 case: acceptance=RING+R5a 锁固肩重(质心 x 落到对应缝间, 超出
#   [xc-a,xc+a] 的肩重直接入墩不进半环, 计数); robustness=裸环只记录。
#   停车线: acceptance 不可行 → run_g3 raise G3_FROZEN_GEOMETRY_CONFLICT
#   (点名孔); 禁调封卷几何参数自救, 阈值不为绿而调。
#
# 独立性: 本节不 import sequencer(传递闭包被测试钉死)。石重按同一单源
# (families.family_mesh + export_print.signed_volume)独立取数 —— 非第二套
# 公式; 密度归一 STONE_DENSITY=1.0 同 sequencer 约定(结果对共同密度因子
# 不变, 不发明无出处常数[三红线])。

STONE_DENSITY = 1.0        # 密度归一(同 sequencer.STONE_DENSITY)[三红线]
VOUSSOIR_INT_N = 64        # crown 跨块分件质心的垂直带积分 Simpson 结点数
H_GRID_STEP = 0.01         # H 扫描网格步长(H_ref 份额; 0.1-1.2 → 111 点)
H_REFINE_ITERS = 30        # 可行边界二分细化次数(初宽×2^-30)
H_EXTEND_MAX = 8           # 扫描端被触及时的最大外扩次数(每次 +1/4 跨距)
BAND_TOL = 1e-9            # 缝交点带内判定容差(沿缝 m)
EPS_X = 1e-9               # 站点/荷载归侧比较容差(m)

CODE_STRESS_INFEASIBLE = "STRESS_ACCEPTANCE_INFEASIBLE"
DEFAULT_SEQ_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "out", "sequence.json")


class G3_FROZEN_GEOMETRY_CONFLICT(Exception):
    """P2 停车线: acceptance 压力线不可行(冻结几何冲突) —— 停报主控;
    禁调封卷几何参数自救, 阈值不为绿而调(判据先行, 数字后置)。"""


_RING_VOL_CACHE = {}       # (孔, family, params 指纹) -> 体积(同 sequencer 缓存口径)


def _ring_mesh(stone):
    # type: (Dict[str, Any]) -> Tuple[List[Tuple[float, float, float]], List[Tuple[int, ...]]]
    """族网格单源(families.family_mesh; ring-wedge=烘焙确定性还原)。"""
    import families as FAM
    return FAM.family_mesh(stone.get("family"),
                           stone.get("params") or {})


def _ring_volume(stone):
    # type: (Dict[str, Any]) -> float
    """券石体积 = 族网格散度体积绝对值(families+export_print 同一单源,
    与 sequencer._ring_stone_volume 同式; 本文件禁 import sequencer(测试
    钉死)故按同一单源独立取数 —— 非第二套公式)。按(孔, family, params
    全量指纹)缓存, 同孔同块型只积分一次。"""
    import export_print as EP
    p = stone.get("params") or {}
    key = (stone.get("id", "").split(".")[0], stone.get("family"),
           json.dumps(p, sort_keys=True))
    vol = _RING_VOL_CACHE.get(key)
    if vol is None:
        verts, faces = _ring_mesh(stone)
        vol = abs(EP.signed_volume(verts, faces))
        _RING_VOL_CACHE[key] = vol
    return vol


def _mesh_centroid(verts, faces):
    # type: (List[Tuple[float, float, float]], List[Tuple[int, ...]]) -> Tuple[float, float, float]
    """多面体(体积, 质心x, 质心z) —— 散度定理, quad 扇形剖分, 纯 python。
    体积与 export_print.signed_volume 互证(调用方断言), 质心供弯矩臂;
    烘焙网格为全局朝向平移到 bbox 中心(p1a_slice.make_ring_entry 口径),
    故质心加 transform 即全局质心。"""
    acc_x = acc_z = vol6 = 0.0
    for f in faces:
        a = verts[f[0]]
        for k in range(1, len(f) - 1):
            b, c = verts[f[k]], verts[f[k + 1]]
            v6 = (a[0] * (b[1] * c[2] - b[2] * c[1])
                  - a[1] * (b[0] * c[2] - b[2] * c[0])
                  + a[2] * (b[0] * c[1] - b[1] * c[0]))
            vol6 += v6
            acc_x += (a[0] + b[0] + c[0]) * v6
            acc_z += (a[2] + b[2] + c[2]) * v6
    if abs(vol6) < 1e-18:
        return 0.0, 0.0, 0.0
    return abs(vol6) / 6.0, acc_x / (4.0 * vol6), acc_z / (4.0 * vol6)


def _stone_weight(stone, density=None):
    # type: (Dict[str, Any], Optional[float]) -> float
    """石重=体积×密度。体积分支与 sequencer.stone_weight 同式(RING=族
    网格散度体积 / CORE=params.bbox 直积 / 其余 w×h×d 断面[估计]);
    density=None 取 STONE_DENSITY(比值对共同密度不变[三红线])。"""
    if density is None:
        density = STONE_DENSITY
    p = stone.get("params", {}) or {}
    role = stone_role(stone.get("id", ""))
    if role == "CORE" and isinstance(p.get("bbox"), dict):
        bb = p["bbox"]
        vol = ((bb["x1"] - bb["x0"]) * (bb["y1"] - bb["y0"])
               * (bb["z1"] - bb["z0"]))
    elif role == RING_ROLE:
        vol = _ring_volume(stone)
    else:
        vol = (float(p.get("w", 0.0)) * float(p.get("h", 0.0))
               * float(p.get("d", 0.0)))
    return vol * density


def _theta_right_frac(stone):
    # type: (Dict[str, Any]) -> float
    """券石重量归于右半拱(x>x_c)的份额: 龙门石按 θ=0 分割(同
    sequencer._theta_left_frac 的镜像约定, 单一口径)。"""
    ang = stone["params"]["angles"]
    t0, t1 = float(ang[0]), float(ang[1])
    if t1 <= t0:
        return 0.5
    if t0 >= 0.0:
        return 1.0
    if t1 <= 0.0:
        return 0.0
    return (t1 - 0.0) / (t1 - t0)


def _vertical_band_centroid(z_in, z_out, x0, x1, n=VOUSSOIR_INT_N):
    # type: (Any, Any, float, float, int) -> Tuple[float, float]
    """[x0,x1] 上垂直带截面的(面积, ∫x·t dx/面积)Simpson 积分。仅 crown
    跨块分件的质心用(冠域缝法向≈(0,1), 径向≈垂直, 偏差二阶小); 其余石
    质心走烘焙网格散度质心(精确)。"""
    if x1 <= x0:
        return 0.0, 0.5 * (x0 + x1)
    h = (x1 - x0) / n
    A = M = 0.0
    for i in range(n + 1):
        x = x0 + h * i
        t = max(z_out(x) - z_in(x), 0.0)
        w = 1 if i in (0, n) else (4 if i % 2 == 1 else 2)
        A += w * t
        M += w * t * x
    A *= h / 3.0
    M *= h / 3.0
    return A, (M / A if A > 1e-12 else 0.5 * (x0 + x1))


def _hole_ring_params(ring_stones):
    # type: (List[Dict[str, Any]]) -> Tuple[float, float, float]
    """孔级拱参数 (xc, a, ring_t): RING 石 params 一致性校验(同孔须同
    xc/ring_t; 端点站点 ∈ {xc-a, xc, xc+a} —— 全环或单边半环皆合法),
    违者 ValueError —— 冻结几何异常不猜。"""
    xc = rt = None
    lo = float("inf")
    hi = float("-inf")
    for s in ring_stones:
        p = s.get("params") or {}
        if "xc" not in p or "stations" not in p:
            raise ValueError("pressure_line: RING 石 %s 缺 xc/stations params"
                             % s.get("id"))
        x = float(p["xc"])
        if xc is None:
            xc, rt = x, float(p["ring_t"])
        elif abs(x - xc) > 1e-9 or abs(float(p["ring_t"]) - rt) > 1e-9:
            raise ValueError(
                "pressure_line: 孔内 RING 石 %s xc/ring_t 不一致 "
                "(%r vs %r/%r)" % (s.get("id"), x, xc, rt))
        st = sorted(float(v) for v in p["stations"][:2])
        lo, hi = min(lo, st[0]), max(hi, st[1])
    if xc is None or hi - lo <= 2.0 * EPS_X:
        raise ValueError("pressure_line: 空半环/退化站点, 拒绝出数")
    a = max(hi - xc, xc - lo)
    for end, name in ((lo, "lo"), (hi, "hi")):
        if min(abs(end - (xc - a)), abs(end - xc),
               abs(end - (xc + a))) > 1e-6:
            raise ValueError(
                "pressure_line: 端点站点 %s=%.9f 不在 {xc-a, xc, xc+a}"
                "(xc=%.9f, a=%.9f, 冻结几何异常)" % (name, end, xc, a))
    return xc, a, rt


def _hole_bands(idx, ring_t):
    # type: (int, float) -> Dict[str, Any]
    """孔带函数(单源 facts.arch_z / geom_math 纵剖层): z_in=intrados,
    z_out=intrados+ring_t(绘图用; 可行性按缝上 s∈[0,ring_t] 径向带判,
    与 masonry 端面法向 ring_t 偏移一致), dzdx=缝法向斜率(端点 ±a 处
    arch 公式退化 (0,0) 法向 → 取内极限 a(1∓1e-6))。"""
    xc = GM.arch_center_x(idx)
    springer = GM.arch_springer_z(idx)
    a = GM.SPANS[idx] / 2.0
    b = GM.arch_rise(idx)

    def z_in(x):
        return F.arch_z(x - xc, 0.0, springer, a, b)

    def z_out(x):
        return z_in(x) + ring_t

    def dzdx(x):
        rel = min(max(x - xc, -a * (1.0 - 1e-6)), a * (1.0 - 1e-6))
        return F.arch_dzdx(rel, 0.0, springer, a, b)

    return {"xc": xc, "a": a, "b": b, "springer": springer,
            "z_in": z_in, "z_out": z_out, "dzdx": dzdx}


def _thrust_eval_H(joint_x, V, M, z_in, dzdx, ring_t, H):
    # type: (List[float], List[float], List[float], Any, Any, float, float) -> Dict[str, Any]
    """给定 H 求该半环的压力线: 逐缝 s_j=(y0-B_j)/D_j ∈[0,ring_t] 判,
    y0 可行区间 = 各缝区间之交(B_j=z_in(x_j)+M_j/H, D_j=n̂z+(V_j/H)n̂x;
    D≈0 = 合力与缝平行 → 不可行)。返回 {feasible, y0, y0_interval,
    joints:[{x,s,s_max,exit}]}(不可行时 y0 取需求区间中值供 exit 定位)。"""
    joints = []  # type: List[Dict[str, Any]]
    lo_y = float("-inf")
    hi_y = float("inf")
    for j, xj in enumerate(joint_x):
        Az = z_in(xj)
        d = dzdx(xj)
        nl = math.hypot(d, 1.0)
        nx, nz = -d / nl, 1.0 / nl
        B = Az + M[j] / H
        D = nz + (V[j] / H) * nx
        s_lo_t, s_hi_t = -BAND_TOL, ring_t + BAND_TOL
        if abs(D) < 1e-14:
            return {"feasible": False, "y0": B, "y0_interval": None,
                    "joints": [], "reason": "joint%d_parallel" % j}
        y_lo, y_hi = (B + s_lo_t * D, B + s_hi_t * D) if D > 0 \
            else (B + s_hi_t * D, B + s_lo_t * D)
        lo_y = max(lo_y, y_lo)
        hi_y = min(hi_y, y_hi)
        joints.append({"x": xj, "B": B, "D": D, "nx": nx, "nz": nz,
                       "Az": Az})
    feasible = hi_y >= lo_y - 1e-15
    y0 = 0.5 * (lo_y + hi_y)
    out_joints = []
    for jd in joints:
        s = (y0 - jd["B"]) / jd["D"]
        exit_tag = None
        if s < -BAND_TOL:
            exit_tag = "intrados"
        elif s > ring_t + BAND_TOL:
            exit_tag = "extrados"
        out_joints.append({"x": jd["x"], "s": s, "s_max": ring_t,
                           "exit": exit_tag, "z": jd["Az"] + s * jd["nz"]})
    return {"feasible": feasible, "y0": y0,
            "y0_interval": [lo_y, hi_y] if feasible else None,
            "joints": out_joints, "reason": None}


def _thrust_side(joint_x, loads, z_in, dzdx, ring_t, H_grid):
    # type: (List[float], List[Tuple[float, float]], Any, Any, float, List[float]) -> Dict[str, Any]
    """半环刚块链: 荷载按 x 排序取缝处前缀 (V_j, M_j), 对 H 网格逐点判
    可行, 边界二分细化。返回 {feasible, H:[min,max], H_mid, y0, joints,
    polyline, n_feasible, gaps}。"""
    ld = sorted(loads, key=lambda p: p[1])
    V = []  # type: List[float]
    M = []  # type: List[float]
    v = m = 0.0
    i = 0
    for xj in joint_x:
        while i < len(ld) and ld[i][1] <= xj + 1e-12:
            v += ld[i][0]
            m += ld[i][0] * ld[i][1]
            i += 1
        V.append(v)
        M.append(v * xj - m)
    if v <= 0.0:
        return {"feasible": False, "H": None, "H_mid": None, "y0": None,
                "joints": [], "polyline": [], "n_feasible": 0, "gaps": 0,
                "reason": "no_load"}

    def ok(H):
        return _thrust_eval_H(joint_x, V, M, z_in, dzdx, ring_t, H)

    feas = [ok(H)["feasible"] for H in H_grid]
    n_feas = sum(1 for f in feas if f)
    if n_feas == 0:
        mid = ok(0.5 * (H_grid[0] + H_grid[-1]))
        return {"feasible": False, "H": None, "H_mid": None, "y0": None,
                "joints": mid["joints"],
                "polyline": [(j["x"], j["z"]) for j in mid["joints"]],
                "n_feasible": 0, "gaps": 0, "reason": "no_feasible_H"}
    gaps = 0
    seen = False
    prev_f = False
    for f in feas:
        if f:
            if seen and not prev_f:
                gaps += 1          # 可行→不可行→可行: 非连结构(记录不判假)
            seen = True
        prev_f = f
    fi = feas.index(True)
    li = len(feas) - 1 - feas[::-1].index(True)

    def refine_down(lo_infeas, hi_feas):
        # type: (float, float) -> float
        """[不可行, 可行] 括号二分 → 可行下界(自可行侧收敛)。"""
        for _ in range(H_REFINE_ITERS):
            mid = 0.5 * (lo_infeas + hi_feas)
            if ok(mid)["feasible"]:
                hi_feas = mid
            else:
                lo_infeas = mid
        return hi_feas

    def refine_up(lo_feas, hi_infeas):
        # type: (float, float) -> float
        """[可行, 不可行] 括号二分 → 可行上界(自可行侧收敛)。"""
        for _ in range(H_REFINE_ITERS):
            mid = 0.5 * (lo_feas + hi_infeas)
            if ok(mid)["feasible"]:
                lo_feas = mid
            else:
                hi_infeas = mid
        return lo_feas

    h_min = H_grid[fi] if fi == 0 else refine_down(H_grid[fi - 1], H_grid[fi])
    h_max = H_grid[li] if li == len(feas) - 1 \
        else refine_up(H_grid[li], H_grid[li + 1])
    h_mid = 0.5 * (h_min + h_max)
    mid = ok(h_mid)
    poly = [(j["x"], j["z"]) for j in mid["joints"]]
    return {"feasible": True, "H": [h_min, h_max], "H_mid": h_mid,
            "y0": mid["y0"], "joints": mid["joints"], "polyline": poly,
            "n_feasible": n_feas, "gaps": gaps, "reason": None}


def pressure_line(ring_stones, extra_loads, band_in_out_fns, H_range,
                  dzdx_fn=None, ring_t=None, grid_step=H_GRID_STEP,
                  H_detail=()):
    # type: (List[Dict[str, Any]], List[Dict[str, Any]], Tuple[Any, Any], Tuple[float, float], Optional[Any], Optional[float], float, Tuple[float, ...]) -> Dict[str, Any]
    """压力线刚块链(brief 接口): 每孔左右半环各扫 H, 可行区间取交。

    ring_stones: 本孔 RING 石账条目(weight=体积单源×密度; 质心=烘焙网格
      散度质心, 冠跨块按 θ 分割 sequencer 同一口径, 分件质心用冠域垂直带
      积分); extra_loads: [{"x","weight"}](R5a 肩重/均布 q 等竖向荷载,
      x≥xc 归右半环, 超出 [xc-a,xc+a] 不入半环直接入墩并计数);
    band_in_out_fns: (z_in, z_out); dzdx_fn: 缝法向斜率单源(缺省= z_in
      中心差分, 数值替代); H_range: 绝对扫描区间; H_detail: 额外细查 H。
    返回 {feasible, H:[min,max]|None, polyline, polyline_left, H_min/max/mid,
    y0, sides{right,left}, sweep, censored, n_feasible, gaps, W_total,
    n_loads_dropped, detail{H: {feasible, joints[+side]}}}。"""
    z_in, z_out = band_in_out_fns
    if dzdx_fn is None:
        def dzdx_fn(x, _z=z_in):                        # type: ignore
            h = 1e-6
            return (_z(x + h) - _z(x - h)) / (2.0 * h)
    xc, a, rt = _hole_ring_params(ring_stones)
    if ring_t is not None:
        rt = float(ring_t)
    h_lo, h_hi = float(H_range[0]), float(H_range[1])
    if not (h_hi > h_lo > 0.0):
        raise ValueError("pressure_line: H_range 须 0<lo<hi (got %r)"
                         % (H_range,))

    loads = []          # type: List[Tuple[str, List[Tuple[float, float]]]]
    dropped = 0
    w_total = 0.0
    left = []           # type: List[Tuple[float, float]]
    right = []          # type: List[Tuple[float, float]]
    for s in ring_stones:
        w = _stone_weight(s)
        w_total += w
        verts, faces = _ring_mesh(s)
        vol, cx, _cz = _mesh_centroid(verts, faces)
        # 烘焙网格 = 全局朝向平移到 bbox 中心(质心锚口径) → 加 transform
        # 回全局; 质心体积与单源 signed_volume 互证(几何完整性)。
        cx += float(s.get("transform", (0.0, 0.0, 0.0))[0])
        sv = _ring_volume(s)
        if abs(vol - sv) > 1e-6 * max(sv, 1e-12):
            raise AssertionError(
                "pressure_line: %s 散度质心体积 %.12g 与单源 signed_volume "
                "%.12g 失配(几何完整性)" % (s.get("id"), vol, sv))
        st = sorted(float(v) for v in (s["params"]["stations"][:2]))
        if st[1] <= xc + EPS_X:
            left.append((w, cx))
        elif st[0] >= xc - EPS_X:
            right.append((w, cx))
        else:
            fr = _theta_right_frac(s)
            _ar, xr = _vertical_band_centroid(z_in, z_out, xc, st[1])
            _al, xl = _vertical_band_centroid(z_in, z_out, st[0], xc)
            right.append((w * fr, xr))
            left.append((w * (1.0 - fr), xl))
    for ld in extra_loads or ():
        x = float(ld["x"])
        w = float(ld["weight"])
        w_total += w
        if not (xc - a - EPS_X <= x <= xc + a + EPS_X):
            dropped += 1
            continue
        (right if x >= xc else left).append((w, x))

    all_st = [sorted(float(v) for v in (s["params"]["stations"][:2]))
              for s in ring_stones]
    joints_r = sorted({xc, xc + a}
                      | {x for st in all_st for x in st
                         if xc + EPS_X < x < xc + a - EPS_X})
    # 左半环镜像到升序空间(x'=2xc-x, 冠缝仍在 x'=xc)计算, 结果再镜像回
    joints_lm = sorted({xc, xc + a}
                       | {2.0 * xc - x for st in all_st for x in st
                          if xc - a + EPS_X < x < xc - EPS_X})

    def sweep(joint_x, ld):
        """H 网格扫描(步长=H_ref×grid_step; 端点被触及时自动外扩防删失)。"""
        step = grid_step * 0.5 * (h_lo + h_hi)
        n_g = int(math.floor((h_hi - h_lo) / step))
        gx = [h_lo + k * step for k in range(n_g + 1)]
        if gx[-1] < h_hi - 1e-15:
            gx.append(h_hi)
        censored = False
        res = _thrust_side(joint_x, ld, z_in, dzdx_fn, rt, gx)
        for _ in range(H_EXTEND_MAX):
            if res["n_feasible"] == 0:
                break
            h0, h1 = res["H"]
            touch_hi = h1 >= gx[-1] * (1.0 - 1e-12)
            touch_lo = h0 <= gx[0] * (1.0 + 1e-12)
            if not touch_hi and not touch_lo:
                break
            span = gx[-1] - gx[0]
            if touch_hi:
                gx = gx + [gx[-1] + span * (k + 1) / 4.0 for k in range(4)]
            if touch_lo:
                gx = [x for x in (gx[0] - span * (4.0 - k) / 4.0
                                  for k in range(4)) if x > 0.0] + gx
            censored = True
            res = _thrust_side(joint_x, ld, z_in, dzdx_fn, rt, gx)
        return res, gx, censored

    res_r, sweep_r, cen_r = sweep(joints_r, right)
    res_l, sweep_l, cen_l = sweep(joints_lm,
                                  [(w, 2.0 * xc - x) for w, x in left])
    # 空半环(该侧无石无荷, 如合成单边 fixture)为空真, 不参与判
    sides = [r for r in (res_r, res_l) if r["reason"] != "no_load"]
    if not sides:
        raise ValueError("pressure_line: 左右半环均无荷载, 拒绝出数")

    detail = {}
    left_m = [(w, 2.0 * xc - x) for w, x in left]
    for H in H_detail:
        jj = []
        feas_d = True
        for jx, ld, tag, mir in ((joints_r, right, "right", False),
                                 (joints_lm, left_m, "left", True)):
            if not ld:
                continue
            ev = _thrust_eval_H(jx, *_prefix(ld, jx), z_in, dzdx_fn, rt, H)
            feas_d = feas_d and ev["feasible"]
            js = _mirror_joints(ev["joints"], xc) if mir else ev["joints"]
            jj += [dict(j, side=tag) for j in js]
        detail[float(H)] = {"feasible": feas_d, "joints": jj}

    feasible = all(r["feasible"] for r in sides)
    if feasible:
        hmin = max(r["H"][0] for r in sides)
        hmax = min(r["H"][1] for r in sides)
        feasible = hmin <= hmax * (1.0 + 1e-15)
        if not feasible:
            hmin = hmax = None
    else:
        hmin = hmax = None
    return {
        "feasible": feasible,
        "H": [hmin, hmax] if feasible else None,
        "H_min": hmin, "H_max": hmax,
        "H_mid": (0.5 * (hmin + hmax)) if feasible else None,
        "polyline": res_r["polyline"],
        "polyline_left": [(2.0 * xc - x, z) for x, z in res_l["polyline"]],
        "y0": res_r["y0"],
        "sides": {"right": res_r, "left": _mirror_side(res_l, xc)},
        "sweep": [min(sweep_r[0], sweep_l[0]), max(sweep_r[-1], sweep_l[-1])],
        "censored": bool(cen_r or cen_l),
        "n_feasible": min(r["n_feasible"] for r in sides),
        "gaps": max(r["gaps"] for r in sides),
        "W_total": w_total,
        "n_loads_dropped": dropped,
        "detail": detail,
    }


def _prefix(ld, joint_x):
    # type: (List[Tuple[float, float]], List[float]) -> Tuple[List[float], List[float]]
    """缝处荷载前缀 (V_j, M_j)(与 _thrust_side 同式, 供 detail 细查)。"""
    srt = sorted(ld, key=lambda p: p[1])
    V, M = [], []
    v = m = 0.0
    i = 0
    for xj in joint_x:
        while i < len(srt) and srt[i][1] <= xj + 1e-12:
            v += srt[i][0]
            m += srt[i][0] * srt[i][1]
            i += 1
        V.append(v)
        M.append(v * xj - m)
    return V, M


def _mirror_joints(joints, xc):
    # type: (List[Dict[str, Any]], float) -> List[Dict[str, Any]]
    return [dict(j, x=2.0 * xc - j["x"]) for j in joints]


def _mirror_side(res, xc):
    # type: (Dict[str, Any], float) -> Dict[str, Any]
    """左半环结果镜像回全局坐标(内部以 2xc-x 升序计算)。"""
    out = dict(res)
    out["polyline"] = [(2.0 * xc - x, z) for x, z in res["polyline"]]
    out["joints"] = _mirror_joints(res["joints"], xc)
    return out


def load_r5a_shoulders(path=None):
    # type: (Optional[str]) -> Dict[str, List[str]]
    """R5a 锁固肩集合(sequencer 单源产物): out/sequence.json 的
    .SHOULDER. 阶段 event_range 内 PLACE_STONE stone_id 按孔分组
    (T4 meta.holes[].n_shoulder 合计 1307, 测试常驻断言)。
    文件缺失/无阶段 → {}(调用方记 note, 不静默造数)。"""
    p = path or DEFAULT_SEQ_PATH
    if not os.path.exists(p):
        return {}
    with open(p) as f:
        seqdoc = json.load(f)
    ev_by_seq = {e.get("seq"): e for e in seqdoc.get("events", [])}
    out = {}  # type: Dict[str, List[str]]
    for st in seqdoc.get("sequence", []):
        stage = st.get("stage", "")
        if ".SHOULDER." not in stage:
            continue
        zh = stage.split(".")[0]
        lo, hi = st.get("event_range") or (None, None)
        if lo is None:
            continue
        for q in range(int(lo), int(hi) + 1):
            e = ev_by_seq.get(q)
            if e and e.get("etype") == "PLACE_STONE" and e.get("stone_id"):
                out.setdefault(zh, []).append(e["stone_id"])
    return out


def stress_gate(ledger, r5a=None):
    # type: (Dict[str, Any], Optional[Dict[str, List[str]]]) -> Dict[str, Any]
    """G3③ 压力线门: 逐孔 acceptance(RING+R5a 肩荷)/robustness(裸环)
    双 case。acceptance 不可行 → 违例码 STRESS_ACCEPTANCE_INFEASIBLE
    (点名孔); run_g3 据此 raise 停车线。H_ref = W_half·L/(8f)
    (q:=W_half/L 归一, 仅扫描标尺; 区间可能出格由删失防护外扩覆盖)。"""
    t0 = time.perf_counter()
    if r5a is None:
        r5a = load_r5a_shoulders()
    by_zone = {}  # type: Dict[str, List[Dict[str, Any]]]
    for s in ledger.get("stones", []):
        if stone_role(s.get("id")) == RING_ROLE:
            by_zone.setdefault(hole_of_sid(s["id"]), []).append(s)
    known = {s["id"] for s in ledger.get("stones", [])}
    holes = {}  # type: Dict[str, Any]
    viols = []  # type: List[str]
    skipped = []  # type: List[str]
    r5a_note = None
    if r5a is not None and not r5a:
        r5a_note = "R5a 集合为空/sequence.json 不在盘上 —— acceptance 退化为裸环"
    for zh in sorted(by_zone):
        ring = by_zone[zh]
        try:
            _xc, _a, rt = _hole_ring_params(ring)
            idx = int(zh[4:]) - 1
            if not (0 <= idx < GM.N_SPAN):
                raise ValueError("孔序号越界")
        except ValueError as exc:
            skipped.append("%s(%s)" % (zh, exc))
            continue
        bp = _hole_bands(idx, rt)
        shoulder_loads = []
        n_r5a = 0
        for sid in (r5a or {}).get(zh, []):
            st = next((s for s in ledger.get("stones", [])
                       if s.get("id") == sid), None)
            if st is None:
                continue
            n_r5a += 1
            shoulder_loads.append({"x": float(st.get("transform", [0])[0]),
                                   "weight": _stone_weight(st)})
        w_hole = sum(_stone_weight(s) for s in ring) \
            + sum(l["weight"] for l in shoulder_loads)
        # H_ref = qL²/(8f), q:=W_hole/L(全孔荷载均摊全跨; 仅扫描标尺)
        h_ref = w_hole * 2.0 * bp["a"] / (8.0 * bp["b"]) if bp["b"] > 0 \
            else float("nan")
        span = (0.1 * h_ref, 1.2 * h_ref)
        acc = pressure_line(ring, shoulder_loads,
                            (bp["z_in"], bp["z_out"]), span,
                            dzdx_fn=bp["dzdx"], ring_t=rt)
        rob = pressure_line(ring, [], (bp["z_in"], bp["z_out"]), span,
                            dzdx_fn=bp["dzdx"], ring_t=rt)
        acc["H_ref"] = h_ref
        acc["ring_t"] = rt
        rob["H_ref"] = h_ref
        rob["ring_t"] = rt
        holes[zh] = {"acceptance": acc, "robustness": rob,
                     "n_ring": len(ring), "n_r5a": n_r5a}
        if not acc["feasible"]:
            viols.append(
                "%s hole=%s 无可行 H(sweep=[%.4g, %.4g]%s, W=%.3f, "
                "n_r5a=%d) —— 冻结几何冲突, 停报主控"
                % (CODE_STRESS_INFEASIBLE, zh, acc["sweep"][0],
                   acc["sweep"][1], " 删失" if acc["censored"] else "",
                   w_hole, n_r5a))
    counts = {}  # type: Dict[str, int]
    for v in viols:
        code = v.split(" ", 1)[0]
        counts[code] = counts.get(code, 0) + 1
    return {"ok": not viols, "violations": viols, "violation_counts": counts,
            "holes": holes, "n_holes": len(holes),
            "skipped_zones": skipped, "r5a_note": r5a_note,
            "elapsed_s": time.perf_counter() - t0}


def plot_hole_pressure(hole, ledger, zone, path, title=None):
    # type: (Dict[str, Any], Dict[str, Any], str, str, Optional[str]) -> str
    """压力线诊断图: intrados/extrados(径向带真值: 内弧采样+法向 ring_t
    外推)+ 左右半环 acceptance 压力线叠画。matplotlib Agg 延迟导入。"""
    import matplotlib
    matplotlib.use("Agg", force=True)
    matplotlib.rcParams["font.sans-serif"] = [
        "PingFang SC", "Hiragino Sans GB", "Arial Unicode MS",
        "STHeiti", "DejaVu Sans"]
    matplotlib.rcParams["axes.unicode_minus"] = False
    import matplotlib.pyplot as plt
    idx = int(zone[4:]) - 1
    rt = hole["acceptance"]["ring_t"]
    bp = _hole_bands(idx, rt)
    xc, a = bp["xc"], bp["a"]
    fig, ax = plt.subplots(figsize=(11, 4.2))
    xs = [xc - a + (2 * a) * i / 240.0 for i in range(241)]
    ax.plot(xs, [bp["z_in"](x) for x in xs], "b-", lw=1.6, label="intrados")
    off = []
    for x in xs:
        d = bp["dzdx"](x)
        nl = math.hypot(d, 1.0)
        off.append((x + rt * (-d / nl), bp["z_in"](x) + rt * (1.0 / nl)))
    ax.plot([p[0] for p in off], [p[1] for p in off], "b--", lw=1.2,
            label="extrados(+ring_t radial)")
    acc = hole["acceptance"]
    for key, lab, col in (("polyline", "thrust RIGHT", "red"),
                          ("polyline_left", "thrust LEFT", "darkorange")):
        poly = acc.get(key) or []
        if poly:
            ax.plot([p[0] for p in poly], [p[1] for p in poly], "-o",
                    color=col, ms=3, lw=1.4, label=lab)
    if acc.get("feasible"):
        sub = "H=[%.4f, %.4f]  H_ref(qL^2/8f)=%.4f  y0=%.3f  FEASIBLE" % (
            acc["H"][0], acc["H"][1], acc["H_ref"], acc["y0"] or 0.0)
    else:
        sub = "NO FEASIBLE H (sweep=[%.3g, %.3g]) —— 停车线" % tuple(acc["sweep"])
    ax.set_title("%s G3③ 压力线(acceptance=RING+R5a)\n%s"
                 % (title or zone, sub), fontsize=10)
    ax.set_xlabel("x (m)")
    ax.set_ylabel("z (m)")
    ax.legend(loc="upper center", ncol=4, fontsize=8)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# run_g3(报告串接; T7 在此追加 gate_thrust 节)
# ---------------------------------------------------------------------------

def run_g3(events, ledger, centerings=None, in_void=None, rbo_ids=None,
           threshold=SWALLOW_THRESHOLD, r5a=None):
    # type: (List[Dict[str, Any]], Dict[str, Any], Optional[List[Dict[str, Any]]], Optional[Set[str]], Optional[List[str]], float, Optional[Dict[str, List[str]]]) -> Dict[str, Any]
    """G3 报告: gate_dag(①)+double_model 清单(W1)+gate_stress(③压力线,
    T6)。扩展点: T7④ 加同形 gate_thrust 节。③ acceptance(RING+R5a 肩荷)
    不可行 → raise G3_FROZEN_GEOMETRY_CONFLICT 停报主控(停车线; 禁调封卷
    几何参数自救)。快照面用 snapshots(...)/Snapshot.copy()。"""
    viols, stats = check_dag_all(events, ledger, in_void=in_void)
    counts = {}  # type: Dict[str, int]
    for v in viols:
        code = v.split(" ", 1)[0]
        counts[code] = counts.get(code, 0) + 1
    if rbo_ids is None:
        rbo_ids = _load_rbo_ids()
    if rbo_ids:
        scan = double_model_scan(ledger, rbo_ids=rbo_ids, threshold=threshold)
    else:
        scan = {"threshold": float(threshold), "n_rbo": 0,
                "ratio_by_id": {}, "placeholders": [], "missing_ids": [],
                "elapsed_s": 0.0,
                "note": "rbo_ids 为空 —— 双建模扫描未运行(合成账/未提供桶)"}
    report = {
        "meta": {
            "n_events": len(events),
            "n_stones_ledger": len(ledger.get("stones", [])),
            "n_scheduled": len(stats["final_present"]),
            "generated_by": "g3_check.py P2-T5+T6",
        },
        "gate_dag": {
            "violations": viols,
            "violation_counts": counts,
            "ok": not viols,
            "n_snapshots": stats["n_snapshots"],
            "n_stone_checks": stats["n_stone_checks"],
            "elapsed_s": stats["elapsed_s"],
        },
        "double_model_placeholders": scan["placeholders"],
        "double_model_scan": scan,
        "w1_note": ("ring_band_overlap 占位石单自持边 Σ=1.0 合规, gate_dag "
                    "不判红; placeholders 仅供 P3 视觉隐藏(W1 交接)"),
    }
    report["gate_stress"] = stress_gate(ledger, r5a=r5a)
    if not report["gate_stress"]["ok"]:
        exc = G3_FROZEN_GEOMETRY_CONFLICT(
            "G3③压力线 acceptance 不可行(冻结几何冲突, 停报主控; 禁调封卷"
            "几何参数自救, 阈值不为绿而调): " + "; ".join(
                report["gate_stress"]["violations"]))
        exc.report = report          # 停报主控: 异常携带完整报告(gate_dag/W1/gate_stress)
        raise exc
    return report
