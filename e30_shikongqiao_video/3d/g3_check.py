# e30_shikongqiao_video/3d/g3_check.py
# -*- coding: utf-8 -*-
"""P2-T5 G3 第一层(①支撑活跃)+ snapshot 状态机: 对任意事件流做独立力学核。

定位(三层力学门第一层, T6③压力线/T7④推力包络在本文件后续扩展):
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
  run_g3(events, ledger, ...) -> report dict
      串 gate_dag(本文件)+double_model 清单; T6/T7 追加 gate_stress/
      gate_thrust 节(report 键即扩展点; Snapshot.present/capacity/by_hole/
      holes+copy() 即其所需快照面)。

违例码(全部点名石/孔+seq, 字符串前缀可 grep):
  DAG_UNSUPPORTED          Σcapacity < 1(荷载分担不完整/全无)
  DAG_NO_ACTIVE_SUPPORT    无任何 capacity>0 边且自持 stone 边未达 1(全浮动)
  DAG_RING_NO_CENTERING    RING 石在合龙前 centering 边 capacity≤0(无架砌券)
  DAG_RING_BEFORE_ERECT    RING 石置放先于本孔立架锚(架未立先砌券)
  DAG_RING_SELFHOLD_EARLY  RING 石在合龙前自持 stone 边 >0(环未合成不自持)
  DAG_PHANTOM_IN_VOID      in_void 幻影石混入事件流/present(拒收入集)
  DAG_R6_JUMP_DECENTER     落架孔某邻孔未达合龙持荷(跳孔落架, 前视 1)
  DAG_R6_ADJ_DECENTERING   相邻孔同落架

语义纪律: capacity=荷载分担份额(P2-T4 修复轮裁2, ledger.py 定稿);
石重(体积单源)①层无需, T6 需要时走 sequencer.stone_weight 同源路径
(export_print.signed_volume×密度), 禁第二套。

Python 3.9.6 纯 stdlib(blender-free; double_model_scan 另需 numpy,
经 p1a_slice blender-free 段)。
"""
import heapq
import json
import os
import time
from typing import Any, Dict, List, Optional, Set, Tuple

import ledger as L
import events as E

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
# run_g3(报告串接; T6/T7 在此追加 gate_stress/gate_thrust 节)
# ---------------------------------------------------------------------------

def run_g3(events, ledger, centerings=None, in_void=None, rbo_ids=None,
           threshold=SWALLOW_THRESHOLD):
    # type: (List[Dict[str, Any]], Dict[str, Any], Optional[List[Dict[str, Any]]], Optional[Set[str]], Optional[List[str]], float) -> Dict[str, Any]
    """G3 报告: gate_dag(①)+double_model 清单(W1)。扩展点: T6③/T7④
    各加同形 report 节(gate_stress/gate_thrust); 快照面用
    snapshots(...)/Snapshot.copy()(present/capacity/by_hole/holes 全量)。"""
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
            "generated_by": "g3_check.py P2-T5",
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
    return report
