# e30_shikongqiao_video/3d/g3_check.py
# -*- coding: utf-8 -*-
"""P2-T5+T6+T7 g3_check.py: G3 第一层(①支撑活跃)+ snapshot 状态机 + 第三层
(③压力线刚块链, acceptance/robustness 双 case + 停车线; ④墩推力不平衡(最小推力读数, T7b 改称——判据已非包络)
不平衡, λ 卸架档+核距双指标+排程停车线)。

定位(三层力学门: ①支撑活跃+③压力线+④墩不平衡·最小推力读数(T7)均在本文件):
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
      串 gate_dag(本文件)+double_model 清单(W1)+gate_stress(③压力线)
      +gate_imbalance(④墩不平衡·最小推力读数, T7; 键名沿④包络期保持兼容)。gate_stress.ok=False →
      raise G3_FROZEN_GEOMETRY_CONFLICT(停车线, 停报主控);
      gate_imbalance.ok=False → raise G3_DECENTER_ORDER_CONFLICT
      (排程冲突停车线, 报告挂 exc.report 含逐墩账+卸架顺序建议)。
  pier_imbalance(snap, H_env_by_hole, lam, pier_dims=None) -> dict
      brief 接口(T7④): 当前事件(snap.event 须 DECENTERING 类)下该孔
      两侧内墩 {pier_id: {H_L,H_R,dH,M_unb,M_res,ratio,e_kernel,verdict,
      verdict_ratio,verdict_kernel,...}}; λ 态由调用方按事件推进。
  imbalance_gate(events, H_env_by_hole, ledger, in_void, pier_dims) -> dict
      ④门: 逐 DECENTERING 事件全墩双指标(λ 卸架档+核距), H 区间取
      ③acceptance 可行区间(同报告单源); 同形节+piers 汇总+advice。

T6 ③压力线(Heyman 刚块链; 见该节头注):
  pressure_line(ring_stones, extra_loads, band_in_out_fns, H_range,
                dzdx_fn=None, ring_t=None) -> dict
      brief 接口: {feasible, H:[min,max], polyline:[(x,z)...]}+诊断键。
      左右半环各扫 H(可行 y0 区间交), H 区间取两半环之交。
      ring_t 覆盖参=缝检验截面厚(P2-T6 裁决: acceptance 传
      ring_t+LOCK_BAND_M 结构带, 带石自重仍计入块链 W_k)。
  stress_gate(ledger, r5a=None) -> dict
      逐孔 acceptance(结构带=RING+胶结锁固带)/robustness(裸环) 双 case;
      违例码 STRESS_ACCEPTANCE_INFEASIBLE 点名孔。H 区间表在 holes[zh]
      (acceptance.band_t=0.35 为结构带加厚, robustness.band_t=0)。
  load_r5a_shoulders(path=None) -> {zone: [stone_id]}
      R5a 锁固肩集合单源读取(out/sequence.json .SHOULDER. 阶段;
      P2-T6 裁决收缩后 = 真锁固带: 足印距 extrados ≤0.35m 径向 ∧
      非双建模占位, 计数测试常驻断言)。
  plot_hole_pressure(hole, ledger, zone, path) -> str
      压力线诊断图(intrados/extrados/结构带外脸/左右压力线叠画;
      matplotlib Agg)。

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
  IMB_RATIO_RED            ④墩倾覆裕度 ratio<1.5(卸架序排程冲突)
  IMB_KERNEL_RED           ④墩基底核距 e>B/6(中三分律超核, 排程冲突)

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
from assumptions import BODY_BOTTOM as _BODY_BOTTOM

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
                 "_heap", "_win_last", "_lam")

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
        self._win_last = {}  # type: Dict[str, Optional[int]]
        self._lam = {}  # type: Dict[str, float]

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
        cl._win_last = dict(self._win_last)
        cl._lam = dict(self._lam)
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

    # W-1: 持荷窗全量预扫 —— CLOSED_SUPPORTED 的判据是"窗内全部 HOLD 已
    # 发生"(= derive_frontier 的 window[-1] 语义)。增量态只见迄今事件,
    # 不预扫则窗中段落架恒绿(窗内首个 HOLD 即持荷), 与构造侧分歧; 故从
    # 手上全量事件流预扫每孔窗内末个 HOLD seq(snapshots 的入参本就是
    # 完整流, 非真流式)。
    ev_close = {}  # type: Dict[str, int]
    ev_dstart = {}  # type: Dict[str, int]
    for e in events:
        zh0 = e.get("hole") or ""
        et0 = e.get("etype")
        q0 = e.get("seq")
        if not isinstance(q0, int) or isinstance(q0, bool):
            continue
        if et0 == "CLOSE_RING":
            ev_close.setdefault(zh0, q0)
        elif et0 == "DECENTER_START":
            ev_dstart.setdefault(zh0, q0)
    for zh0 in set(ev_close) | set(ev_dstart):
        close0 = ev_close.get(zh0)
        dstart0 = ev_dstart.get(zh0)
        hs = [e["seq"] for e in events
              if (e.get("hole") or "") == zh0
              and e.get("etype") == "HOLD_EVENT"
              and close0 is not None and close0 < e["seq"]
              and (dstart0 is None or e["seq"] < dstart0)]
        snap._win_last[zh0] = max(hs) if hs else None

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
            h = _ensure_hole(snap, zh)
            if isinstance(sid, str) and sid == CEN_PREFIX + zh \
                    and h["erect"] is None:
                h["erect"] = seq
            h["holds"].append(seq)
        elif et == "CLOSE_RING":
            h = _ensure_hole(snap, zh)
            if h["close"] is None:
                h["close"] = seq
        elif et == "DECENTER_START":
            h = _ensure_hole(snap, zh)
            if h["dstart"] is None:
                h["dstart"] = seq
            snap._lam[zh] = 0.0     # dstart ⟹ λ=0 显式归零(重建架再卸路径
            # 下 λ 良定; 词表不支持二次落架, 二次 dstart=新一轮卸架从 0 起)
            _check_r6(snap, zh, seq, zone_order, rank_of,
                      etype=et, lam_val=0.0)
        elif et == "WEDGE_RELEASE":
            # λ 轨迹(R6 对内同档判 + ④门消费): 缺值/越界 ValueError
            # fail-closed(与 imbalance_gate._lam_advance 同语义, 去顺序
            # 耦合 —— 形制缺陷在此即停, 不静默沿用上一档)
            v = ev.get("load_lambda")
            if not isinstance(v, (int, float)) or isinstance(v, bool) \
                    or not (0.0 <= float(v) <= 1.0):
                raise ValueError(
                    "snapshots: %s WEDGE_RELEASE seq=%s load_lambda=%r "
                    "缺值/越界[0,1] —— fail-closed" % (zh, seq, v))
            snap._lam[zh] = float(v)
            _check_r6(snap, zh, seq, zone_order, rank_of,
                      etype=et, lam_val=snap._lam[zh])
        elif et == "CENTERING_CLEAR":
            h = _ensure_hole(snap, zh)
            if h["clear"] is None:
                h["clear"] = seq
            _check_r6(snap, zh, seq, zone_order, rank_of,
                      etype=et, lam_val=1.0)

        _advance_knots(snap, seq)
        yield snap


def _ensure_hole(snap, zh):
    # type: (Snapshot, str) -> Dict[str, Any]
    """取(或建)孔生命周期 dict —— snapshots 四个生命周期分支共用的
    初始化 helper(W-4: 原四份逐字内联拷贝 + 零调用的死函数 _lifecycle
    已删, 初始化只此一份)。形态同 holes_timeline 的 setdefault 初值。"""
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


def _supported_at(snap, zh, s):
    # type: (Snapshot, str, int) -> bool
    """孔 zh 在事件 seq=s 时是否 ≥ CLOSED_SUPPORTED(独立重建)。W-1 修后
    与 derive_frontier 同构: 已合龙 ∧ 持荷窗 (close, dstart) 内**全部**
    HOLD 已发生 —— 判据 = 预扫的窗内末个 HOLD(snap._win_last) ≤ s, 即
    状态恰在 window[-1] 翻真(derive_frontier 的 at_seq)。旧实现"增量态
    窗内任一(首个) HOLD 即持荷"与构造侧分歧 —— 邻孔窗内中段落架可
    sequencer 红/g3 绿, 削弱互证(test_w1 钉死)。窗内无 HOLD(或未合龙)
    → 永不 CLOSED_SUPPORTED。"""
    h = snap.holes.get(zh) or {}
    close = h.get("close")
    if close is None or close > s:
        return False
    win_last = snap._win_last.get(zh)
    return win_last is not None and win_last <= s


def _decentering_at(h, s):
    # type: (Dict[str, Any], int) -> bool
    dstart = h.get("dstart")
    if dstart is None or dstart > s:
        return False
    clear = h.get("clear")
    return clear is None or clear > s


def _lam_at(snap, zh):
    # type: (Snapshot, str) -> float
    """孔 zh 在 snap 时刻的 λ(环已承载份额; 未落架/无记录 = 0 架上满承载)。"""
    return snap._lam.get(zh, 0.0)


def _check_r6(snap, zh, seq, zone_order, rank_of, etype=None, lam_val=None):
    # type: (Snapshot, str, int, List[str], Dict[str, int], Optional[str], Optional[float]) -> None
    """R6 前视 1(独立重建): 落架孔的每个既有邻孔须 ≥ 合龙持荷(禁跳孔);
    相邻孔同落架须**档位锁定**(对内同档, 主控 2026-10-07 裁决: 多孔连拱
    对称同步卸落 —— 逐孔串行在④墩不平衡门不可行): 任一 DECENTERING
    事件时, 处于落架中的邻孔与本孔 λ 差 ≤ 一档(LAMBDA_GRID_STEP);
    超档 = 乱序同落架仍红。邻接=排序孔表 i±1(空档孔参与判)。"""
    i = rank_of.get(zh)
    if i is None:
        return
    own = lam_val if lam_val is not None else _lam_at(snap, zh)
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
            nl = _lam_at(snap, nz)
            if abs(own - nl) > LAMBDA_GRID_STEP + TOL:
                snap.violations.append(
                    "%s 相邻孔 %s/%s 同落架失档(λ %.2f vs %.2f, 差>一档, "
                    "seq=%d) —— 对内同档" % (CODE_R6_ADJ, zh, nz, own, nl,
                                             seq))
        elif not _supported_at(snap, nz, seq):
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


def _drain_tail_knots(snap):
    # type: (Snapshot) -> int
    """W-2: 事件流末尾后排空结点堆 —— x>末事件 seq 的未来结点同样是
    分段线性端点; 不排空则"端点全覆盖"论证在流外失效(sequencer 端
    _check_capacity_invariant 核每边全部 knot, g3 不得留静默盲区:
    畸形账可借尾部结点逃逸)。返回核点数; dirty 留给调用方 check_dag
    统一复核。堆内结点只属已置放石(入堆仅在置放时), "石存在后才核"
    的物理前提不变。"""
    n = 0
    heap = snap._heap
    while heap:
        x, sid, i = heapq.heappop(heap)
        ed = snap._edges.get(sid, ())[i]
        snap.capacity[(sid, i)] = L.edge_capacity(ed, x)
        snap.dirty.setdefault(sid, []).append(x)
        n += 1
    return n


def check_dag_all(events, ledger, in_void=None):
    # type: (List[Dict[str, Any]], Dict[str, Any], Optional[Set[str]]) -> Tuple[List[str], Dict[str, Any]]
    """流式驱动: 全事件 snapshots + check_dag 聚合。stats 含耗时/快照数/
    石级复核步数/终态 present。W-2: 流尾把结点堆排空再核一遍 ——
    x>末事件 seq 的结点(曲线在流外衰减/变化的段)也在核查域内; 真账
    构造保证结点皆真实事件 seq, 排空为零开销。"""
    t0 = time.perf_counter()
    viols = []  # type: List[str]
    n_checks = 0
    n_snaps = 0
    n_tail = 0
    final_present = set()  # type: Set[str]
    for snap in snapshots(events, ledger, in_void=in_void):
        viols.extend(check_dag(snap))
        n_checks += sum(len(xs) for xs in snap.dirty.values())
        n_snaps += 1
        final_present = snap.present
    if n_snaps:
        n_tail = _drain_tail_knots(snap)
        if n_tail:
            snap.violations = []   # 事件级违例已随流聚合, 此步仅石级复核
            viols.extend(check_dag(snap))
            n_checks += n_tail
    stats = {
        "n_snapshots": n_snaps,
        "n_stone_checks": n_checks,
        "n_tail_checks": n_tail,
        "elapsed_s": time.perf_counter() - t0,
        "final_present": set(final_present),
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
# 物理口径(冻结, 停车线保护对象; P2-T6 裁决轮修订"结构带"假设):
#   每孔左右半环(crown→springer)各为独立刚块链: 券石按 params 角域切块
#   (重量=export_print.signed_volume×密度 体积单源; 质心=烘焙网格散度质心,
#   与单源体积互证), 给定冠推力 H(水平, 作用高 y0 为自由参数)逐缝递推
#   合力 R_k=R_{k-1}+W_k(等价闭式: V_j=ΣW, M_j=ΣW(x_j-x̄)), R_k 的作用线
#   与块间放射缝(法向同 masonry._arch_normal = facts.arch_dzdx 单源)交点
#   沿缝参数 s 必须 ∈[0, 截面厚], 即缝交点落在结构截面内。每 H 下 y0 可
#   行区间 = 各缝 y0-区间之交; H 可行 ⟺ 交非空。扫 H 网格(0.1-1.2×qL²/8f,
#   q:=全孔荷载/跨长)取可行区间, 边界二分细化; 网格边被触及时自动外扩
#   (删失防护, 覆盖机制非几何参数)。
#
#   [P2-T6 主控裁决两层之二·结构协同假设] acceptance 的截面 = 结构带:
#   锁固带石(sequencer 收缩后 R5a: 足印距 extrados ≤LOCK_BAND_M 径向 ∧
#   非双建模占位)与券脸石餬灰胶结(C:A5 张嘉贞"餬灰璺"一手; 卢沟桥
#   "石工鳞砌"通例), 受压单体内协同工作 —— 锁固带是拱截面的加厚部分,
#   非铰接裸环上的外荷载(旧口径双重保守: 荷载全计 + 缝检验带只到
#   extrados)。实现: 带石自重仍计入块链 W_k(移出"外荷载"≠从链消失,
#   双重放松会失真), s 检验截面厚放宽为 ring_t + LOCK_BAND_M(该孔有
#   胶结锁固带时); params.ring_t 零触碰。带以上满高拱肩余下部分
#   (= 收缩后 R5b)按排程在 CENTERING_CLEAR 后砌, 不在落架工况在位。
#   robustness 裸环 case 原样保留(永久对照, s∈[0,ring_t])。
#   失效边界(显式): 若灰浆未结强度, 锁固带不参与截面, 落架时机须后移
#   至拱肩近满("拱肩砌至大半再撤架"的历史工法力学解释) —— 届时由本门
#   停车线红显形, 不许调带宽自救(0.35 唯一声明值)。
#   停车线: acceptance 不可行 → run_g3 raise G3_FROZEN_GEOMETRY_CONFLICT
#   (点名孔); 禁调封卷几何参数自救, 阈值不为绿而调。
#
# 独立性: 本节不 import sequencer(传递闭包被测试钉死)。石重按同一单源
# (families.family_mesh + export_print.signed_volume)独立取数 —— 非第二套
# 公式; 密度归一 STONE_DENSITY=1.0 同 sequencer 约定(结果对共同密度因子
# 不变, 不发明无出处常数[三红线])。LOCK_BAND_M 与 sequencer.LOCK_BAND_M
# 同一裁决值各自声明(互证纪律), 常驻测试钉同值。

STONE_DENSITY = 1.0        # 密度归一(同 sequencer.STONE_DENSITY)[三红线]
LOCK_BAND_M = 0.35         # [P2-T6 裁决] 径向锁固带宽(结构带加厚量; 与
                           # sequencer.LOCK_BAND_M 同一裁决值, 测试钉同值)
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


def _crown_wedge(ring_stones, xc):
    # type: (List[Dict[str, Any]], float) -> Optional[Tuple[float, float, float]]
    """冠楔几何推导(全孔统一): 站点域跨冠缝 xc 的环块被 xc 截出的接触带
    [st0, st1] 及其短半宽 crown_hw=min(xc−st0, st1−xc)(取短半宽=最保守
    侧; 真账跨冠块每孔恰 1 块, max 语义在唯一块下为空操作)。st0/st1 即
    字面杠杆(简支两支点)的支点缝。无跨冠块(合成单边 fixture)→ None。"""
    best = None
    for s in ring_stones:
        st = sorted(float(v) for v in (s["params"]["stations"][:2]))
        if st[0] < xc < st[1]:
            hw = min(xc - st[0], st[1] - xc)
            if best is None or hw > best[2]:
                best = (st[0], st[1], hw)
    return best


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
      x≥xc 归右半环, 超出 [xc-a,xc+a] 不入半环直接入墩并计数;
      落在冠楔接触带 [st0,st1](跨冠缝环块两缝=简支两支点)内者按字面
      连续杠杆 fr=(x−st0)/(st1−st0) 分派, 左=1−fr, 跨带边界连续);
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
    # 冠楔(几何推导, 全孔统一): 跨冠缝环块被 xc 截出的接触带 [st0, st1],
    # 两缝即简支两支点; crown_hw=短半宽(诊断暴露, 供测试钉值)。
    all_st = [sorted(float(v) for v in (s["params"]["stations"][:2]))
              for s in ring_stones]
    wedge = _crown_wedge(ring_stones, xc)
    crown_hw = wedge[2] if wedge else 0.0
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
        # [P2-T6c→d 字面连续杠杆] 质心落在冠楔接触带 st0≤x≤st1(两缝=简支
        # 两支点)内的竖向荷载按**字面杠杆**分派: 右半环份额 fr=(x−st0)/
        # (st1−st0), 左=1−fr —— 与同函数跨冠环块的 θ 连续分派
        # (_theta_right_frac)同构, 跨带边界连续(带边 fr=0/1 精确衔接
        # "整列归所属半环", 无阶跃)。带外整列归所属半环。演化链: 更旧
        # tie-break 100% 归右(序号伪影, 与"相位全按西缘"同族) → 50/50
        # 平摊(带边 O(w/2) 阶跃, 口径与环石连续分派不一致) → 本口径。
        # 镜像协变: 镜像孔的 fr 自动取 1−fr(构造性)。出口审查实测
        # (2026-10-07): lever_span acceptance/robustness 17/17, 窗口相对
        # 50/50 态位移 ≤2.34, 跨带边界连续; 仅"整列归单侧"(fr=0/1)翻红。
        if wedge and wedge[0] <= x <= wedge[1]:
            fr = (x - wedge[0]) / (wedge[1] - wedge[0])
            if fr > 0.0:
                right.append((fr * w, x))
            if fr < 1.0:
                left.append(((1.0 - fr) * w, x))
        else:
            (right if x >= xc - EPS_X else left).append((w, x))

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
        "crown_hw": crown_hw,
        "crown_wedge": [wedge[0], wedge[1]] if wedge else None,
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
    (P2-T6 裁决收缩后合计 1290 = 旧 1307 − 17 占位剔除; 测试常驻断言)。
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
    """G3③ 压力线门: 逐孔 acceptance(结构带=RING+胶结锁固带)/robustness
    (裸环) 双 case。[P2-T6 裁决] acceptance 截面厚 = ring_t + LOCK_BAND_M
    (该孔存在胶结锁固带时; 带石自重仍计入块链 W_k —— 移出"外荷载"≠从链
    消失), robustness 恒 s∈[0,ring_t]。acceptance 不可行 → 违例码
    STRESS_ACCEPTANCE_INFEASIBLE(点名孔); run_g3 据此 raise 停车线。
    H_ref = W_hole·L/(8f)(q:=W_hole/L 归一, 仅扫描标尺; 区间可能出格由
    删失防护外扩覆盖)。"""
    t0 = time.perf_counter()
    if r5a is None:
        r5a = load_r5a_shoulders()
    by_zone = {}  # type: Dict[str, List[Dict[str, Any]]]
    stones_by_id = {}  # type: Dict[Any, Dict[str, Any]]
    for s in ledger.get("stones", []):
        stones_by_id[s.get("id")] = s      # 一次建索引: R5a 逐 id 查 O(1)
        if stone_role(s.get("id")) == RING_ROLE:
            by_zone.setdefault(hole_of_sid(s["id"]), []).append(s)
    holes = {}  # type: Dict[str, Any]
    viols = []  # type: List[str]
    skipped = []  # type: List[str]
    r5a_note = None
    if r5a is not None and not r5a:
        r5a_note = "R5a 集合为空/sequence.json 不在盘上 —— acceptance 退化为裸环(无胶结锁固带)"
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
        # 结构带荷载项: 锁固带石自重按质心 x 计入块链 W_k(截面自重,
        # 非"外荷载"; 超出 [xc-a,xc+a] 者直接入墩不进半环, pressure_line
        # 内计数)。
        shoulder_loads = []
        n_r5a = 0
        for sid in (r5a or {}).get(zh, []):
            st = stones_by_id.get(sid)
            if st is None:
                continue
            n_r5a += 1
            # [P2-T6b] 荷载 x = 石质心(锚语义 H1 单源: slab=最小角锚,
            # 质心 = bbox 中点; wedge-std = 中心锚 transform[0]) —— 旧实现
            # 直用 transform[0], 对 min-corner slab 是左缘非质心, 跨孔镜像
            # 下角↔角翻转使 CORE 肩载错位一个胞宽(O(1) 手性, C14.B01 级
            # 大块即此)。同 masonry2.anchor_offset/_world_top_center_x
            # 分派表语义, 禁第二套。
            p_st = st.get("params") or {}
            bb = p_st.get("bbox")
            lx = (0.5 * (float(bb["x0"]) + float(bb["x1"]))
                  if isinstance(bb, dict) else float(st["transform"][0]))
            shoulder_loads.append({"x": lx, "weight": _stone_weight(st)})
        # [P2-T6 结构协同假设] 有胶结锁固带 → s 检验截面厚 ring_t+0.35
        # (径向结构带); 无带孔 acceptance≡robustness(裸环)。
        rt_eff = rt + (LOCK_BAND_M if n_r5a > 0 else 0.0)
        w_hole = sum(_stone_weight(s) for s in ring) \
            + sum(l["weight"] for l in shoulder_loads)
        # H_ref = qL²/(8f), q:=W_hole/L(全孔荷载均摊全跨; 仅扫描标尺)
        h_ref = w_hole * 2.0 * bp["a"] / (8.0 * bp["b"]) if bp["b"] > 0 \
            else float("nan")
        span = (0.1 * h_ref, 1.2 * h_ref)
        acc = pressure_line(ring, shoulder_loads,
                            (bp["z_in"], bp["z_out"]), span,
                            dzdx_fn=bp["dzdx"], ring_t=rt_eff)
        rob = pressure_line(ring, [], (bp["z_in"], bp["z_out"]), span,
                            dzdx_fn=bp["dzdx"], ring_t=rt)
        acc["H_ref"] = h_ref
        acc["ring_t"] = rt
        acc["band_t"] = rt_eff - rt
        rob["H_ref"] = h_ref
        rob["ring_t"] = rt
        rob["band_t"] = 0.0
        holes[zh] = {"acceptance": acc, "robustness": rob,
                     "n_ring": len(ring), "n_r5a": n_r5a,
                     "w_band": sum(l["weight"] for l in shoulder_loads),
                     "band_bonded": n_r5a > 0}
        if not acc["feasible"]:
            viols.append(
                "%s hole=%s 结构带(ring_t+%.2f) acceptance 无可行 H"
                "(sweep=[%.4g, %.4g]%s, W=%.3f, n_r5a=%d) —— 冻结几何冲突, "
                "停报主控"
                % (CODE_STRESS_INFEASIBLE, zh, acc["band_t"],
                   acc["sweep"][0], acc["sweep"][1],
                   " 删失" if acc["censored"] else "", w_hole, n_r5a))
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
    acc = hole["acceptance"]
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
    band_t = acc.get("band_t") or 0.0
    if band_t > 0.0:
        # [P2-T6 结构协同假设] 结构带外脸: acceptance 缝检验截面 = 环+胶结锁固带
        off2 = []
        for x in xs:
            d = bp["dzdx"](x)
            nl = math.hypot(d, 1.0)
            off2.append((x + (rt + band_t) * (-d / nl),
                         bp["z_in"](x) + (rt + band_t) * (1.0 / nl)))
        ax.plot([p[0] for p in off2], [p[1] for p in off2], "c:",
                lw=1.4, label="structural band(+%.2f)" % band_t)
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
# T7 ④墩推力不平衡(最小推力读数; λ 卸架档 + 核距双指标)
# ---------------------------------------------------------------------------
# 物理口径(冻结; 2026-10-07 主控包络连续性裁决 + T7b 出口审查条件化修订,
# 判据先行数字后置; G3 三层力学门的第三检):
#   落一孔的架 → 该孔以水平推力外推其两侧墩顶; 邻孔仍驻架/未合龙 → 不回馈
#   反向推力 → 墩身承受不平衡水平力+弯矩。sequencer 把 DECENTERING 建模为
#   渐进(λ=环已承载份额∈[0,1], 架吸收 1−λ), 有效推力全孔同式:
#     H_eff = λ × Hmin(H 区间下界读数)。
#   [T7b R1·主张条件化] H∈[Hmin,Hmax] 皆静力可及(Heyman 安全定理), Hmin
#   是拱自由偏好平衡的点估计**非保守界**(最小推力定理前提=沉降到位, 卸架
#   中环仍被架约束位移); 本门在该读数下不违例 ⇒ **不能判定可行, 只能判定
#   不违例**。换读数的条件性机器可读: gate 节 `viol_uniform_hmax`(一致
#   Hmax 读数违例组合数)+ entry 的 *hmax 字段; 敏感性四轴(α/N/δ/μ0)见
#   报告 §9。卸架顺序([工程推断·非史料], 见 sequencer 波2 注)。
#   卸架顺序(主控裁决采纳"对称同步落架"): sequencer 波2 改**全桥同波逐档**
#   (每档全部孔 WEDGE_RELEASE 同 stage, 档差=0 —— 每对邻孔同 λ, 不平衡
#   =λ×|Hmin_A−Hmin_B|, 相似跨≈0); R6_ADJ 相应改"对内同档": 相邻孔同落架
#   须 λ 差 ≤ 一档(LAMBDA_GRID_STEP), 乱序同落架仍红(判据见 _check_r6/
#   sequencer.check_frontier 两实现互证)。
#   经典砌体墩验算双指标(独立输出, 阈值互不派生 —— 一个红一个绿要能表达):
#     1) 倾覆裕度 ratio = M_res/M_unb ≥ 1.5 [现代裕度·敏感性, 非史料常数]:
#        M_unb = |dH|×h_ref(h_ref=两侧作用高较大者, 保守单臂),
#        M_res = V×B/2(竖向合力 V 作用于基底形心, 抗倾臂 B/2)。
#     2) 核距(中三分律) e_kernel = |H_L·h_L − H_R·h_R|/V ≤ B/6(矩形基底
#        核半宽): 绕基底中线精确合力矩/竖向合力; 超核 → 基底出现拉应力区
#        (砌体抗拉≈0)即失稳。
#   等作用高时核距严于 1.5 裕度(e≤B/6 ⟺ ratio≥3), 两判定差异的表达域 =
#   B/6<e≤B/3 带 + 两侧作用高异高(deck camber, 真账相邻孔即异高) ——
#   独立输出即为此(逐事件逐墩双 verdict, 互不掩盖)。[T7b·真账有牙性]
#   本桥 Hmin 读数下 ratio 最松 3.438 ≫1.5 —— 真账唯一有牙的判据是中三
#   分核距, 1.5 裕度在本桥为装饰性第二读数(报告 §9 声明)。
#   墩重(保守最小): 基底(BODY_BOTTOM)至两邻孔起拱线较低者; 纵深=
#   2×geom_math.width_at(收分单源) Simpson 积分; 墩宽 facts.pier_w。
#   [T7b R2·V 完整性] V 另加墩顶两邻孔 RING+R5a 带竖向反力之半和
#   (卸架时确在位, 经楔座传墩; δ 反力偏心保守取 0, μ0 驻架孔回馈保守
#   取 0 —— 两缺省的敏感性轴见报告 §9)。
#   基底宽: ledger PIER 石 params.found_w 优先(真账无 PIER 石, 2026-10-07
#   实查 5935 石仅 SPANDREL/BACK/CORE/RING/IMPOST)→ facts.PIER_FOUND_W
#   (_C 中央对 k∈{8,9}) 回退, 不硬编码。
#   λ 档: WEDGE_RELEASE.load_lambda(events 1/4 栅格单源),
#   DECENTER_START=0, CENTERING_CLEAR=1; 越界/缺值 ValueError
#   fail-closed(禁静默钳位; snapshots 与 ④门同语义)。
#   停车线(排程侧): run_g3 真账 gate_imbalance 红 → raise
#   G3_DECENTER_ORDER_CONFLICT(点名墩/事件 + λ 临界 + 卸架顺序建议);
#   修正走 sequencer 排程, 禁调 λ/裕度/核宽自救凑绿。红绿都是结论:
#   不违例 = 最小推力读数下不违例(条件化, 见上)。
#
# 独立性: 本节不 import sequencer(传递闭包测试钉死); λ 栅格语义与
# sequencer.LAMBDA_LADDER/events.LAMBDA_GRID 同一裁决值各自声明(互证纪律)。

RATIO_MIN = 1.5            # [现代裕度·敏感性] 倾覆裕度下限(brief 指定)
KERNEL_FRAC = 6.0          # 矩形基底核半宽 = B/6(中三分律, 几何事实非阈值)
LAMBDA_GRID_STEP = 0.25    # λ 档步长(events.LAMBDA_GRID=4 同一裁决值各自声明)
CODE_IMB_RATIO = "IMB_RATIO_RED"
CODE_IMB_KERNEL = "IMB_KERNEL_RED"
_PIER_W_NODES = 32         # 墩纵深 Simpson 结点数(width_at 线性 → 精确)
_PIER_STATICS_CACHE = {}   # (k, z_top) -> (B, V) facts 路径缓存


class G3_DECENTER_ORDER_CONFLICT(Exception):
    """P2 停车线(排程侧): ④墩推力不平衡超阈 —— 卸架顺序不可行, 停报主控。
    修正走 sequencer 排程(对称孔同 stage 逐档同步落架/邻孔先落架);
    禁调 λ/裕度/核宽自救(判据先行, 数字后置)。报告挂 exc.report
    (gate_dag/gate_stress/gate_imbalance 三节 + 逐墩账 + 顺序建议)。"""


def _hole_idx(zh):
    # type: (str) -> int
    """孔名 "ARCH08" → 0-based 拱索引 7(词表形制, 非法名 ValueError)。"""
    if not isinstance(zh, str) or not zh.startswith("ARCH") \
            or not zh[4:].isdigit():
        raise ValueError("pier_imbalance: 非法孔名 %r" % (zh,))
    return int(zh[4:]) - 1


def _pier_base_w(k):
    # type: (int) -> float
    """墩 k(1..16) 基底宽(facts 单源回退路径): 基础宽登记值, 中央对
    k∈{8,9}(与 PIER_W_C 同一"中央"定义 i=8,9)取 _C 变体。"""
    return F.PIER_FOUND_W_C if k in (8, 9) else F.PIER_FOUND_W


def _pier_weight(k, z_top):
    # type: (int, float) -> float
    """墩身自重(保守最小): 宽 facts.pier_w(k) × 纵深 2×GM.width_at(收分
    单源, [BODY_BOTTOM, z_top] Simpson; width_at 对 z 线性 → 积分精确)
    × 密度 1.0(STONE_DENSITY 同 sequencer 约定, 不发明常数[三红线])。"""
    x = GM.PIER_X[k]
    w = F.pier_w(k)
    n = _PIER_W_NODES
    h = (z_top - _BODY_BOTTOM) / n
    acc = 0.0
    for i in range(n + 1):
        z = _BODY_BOTTOM + i * h
        c = 1 if i in (0, n) else (4 if i % 2 else 2)
        acc += c * 2.0 * GM.width_at(x, z)
    return w * (h / 3.0) * acc


def _pier_dims_from_ledger(ledger):
    # type: (Dict[str, Any]) -> Dict[str, Dict[str, float]]
    """ledger PIER 石 → {pier_id: {"base_w": 基底宽}}(brief"墩基底尺寸从
    ledger PIER 石 params 取"; 约定: params.found_w=基底宽, transform[0]
    ≈墩心 x 归最近 PIER_X; 同墩多石取最宽)。真账无 PIER 石 → 空表(调用方
    走 facts 回退)。"""
    out = {}  # type: Dict[str, Dict[str, float]]
    for s in (ledger or {}).get("stones", []):
        if stone_role(s.get("id")) != "PIER":
            continue
        p = s.get("params") or {}
        fw = p.get("found_w")
        tr = s.get("transform") or []
        if not isinstance(fw, (int, float)) or isinstance(fw, bool) \
                or not tr or not isinstance(tr[0], (int, float)) \
                or isinstance(tr[0], bool) or fw <= 0.0:
            raise ValueError(
                "pier_dims_from_ledger: PIER 石 %s params.found_w/transform "
                "非法(%r, %r) —— fail-closed" % (s.get("id"), fw, tr))
        k = min(range(1, F.N_SPAN),
                key=lambda j: abs(GM.PIER_X[j] - float(tr[0])))
        pid = "PIER%02d" % k
        if pid not in out or fw > out[pid]["base_w"]:
            out[pid] = {"base_w": float(fw)}
    return out


def _hole_top_loads(ledger, r5a=None):
    # type: (Dict[str, Any], Optional[Dict[str, List[str]]]) -> Dict[str, float]
    """孔顶在位竖向荷载单源(④V 完整性, P2-T7b 主控裁决 R2): 每孔
    RING 全部 + R5a 锁固带石(r5a 缺省 load_r5a_shoulders() 单源)的
    自重和 —— 落架时确在位(波1 砌体, R5a 窗=合龙→落架), 经楔座把竖向
    反力传墩; 密度 1.0 同门约定。返回 {zone: W_top}。"""
    if r5a is None:
        r5a = load_r5a_shoulders()
    by_id = {s["id"]: s for s in (ledger or {}).get("stones", [])}
    ring_w = {}  # type: Dict[str, float]
    for s in (ledger or {}).get("stones", []):
        if stone_role(s.get("id")) == RING_ROLE:
            ring_w[hole_of_sid(s["id"])] = \
                ring_w.get(hole_of_sid(s["id"]), 0.0) + _stone_weight(s)
    out = {}  # type: Dict[str, float]
    for zh in sorted(set(ring_w) | set(r5a or {})):
        w = ring_w.get(zh, 0.0)
        for sid in (r5a or {}).get(zh, []):
            st = by_id.get(sid)
            if st is not None:
                w += _stone_weight(st)
        out[zh] = w
    return out


def _pier_statics(k, dims, top_L=0.0, top_R=0.0):
    # type: (int, Optional[Dict[str, Dict[str, float]]], float, float) -> Tuple[float, float, str]
    """墩 k 静力量 (基底宽 B, 竖向合力 V, 来源)。优先级:
    dims 条目(base_w 必填; 无 weight → V 走 facts 积分+孔顶反力, 来源
    ledger_pier_stones; 有 weight → 全 override) > facts 回退(缓存)。

    [P2-T7b 主控裁决 R2·V 完整性=正确性修复] V = 墩身自重(保守最小积分)
    + (W_top_L + W_top_R)/2 —— 墩顶两邻孔 RING+R5a 带竖向反力(卸架时确
    在位、经楔座传墩; 各孔每 Springing 分摊半重); δ(反力偏心距)保守取 0
    (不对倾覆/核距给任何力臂 credit), μ0(驻架孔回馈)保守取 0(声明保守,
    敏感性轴见报告 §9)。"""
    pid = "PIER%02d" % k
    z_top = min(GM.arch_springer_z(k - 1), GM.arch_springer_z(k))
    key = (k, round(z_top, 9))
    hit = _PIER_STATICS_CACHE.get(key)
    if hit is None:
        hit = (_pier_base_w(k), _pier_weight(k, z_top))
        _PIER_STATICS_CACHE[key] = hit
    b_facts, v_body = hit
    v = v_body + (top_L + top_R) / 2.0   # R2·V 完整性: 墩顶两孔半跨反力
    if dims and pid in dims:
        d = dims[pid]
        b, w = d.get("base_w"), d.get("weight")
        if not isinstance(b, (int, float)) or isinstance(b, bool) \
                or b <= 0.0:
            raise ValueError("pier_statics: %s.base_w=%r 非法(须正数) "
                             "—— fail-closed" % (pid, b))
        if w is None:
            return float(b), v, "ledger_pier_stones"
        if not isinstance(w, (int, float)) or isinstance(w, bool) \
                or w <= 0.0:
            raise ValueError("pier_statics: %s.weight=%r 非法(须正数) "
                             "—— fail-closed" % (pid, w))
        return float(b), float(w), "override"
    return b_facts, v, "facts_fallback"


def _h_app(zh):
    # type: (str) -> float
    """孔推力作用高 = 起拱线标高 − 基底(GM.arch_springer_z 单源)。"""
    return GM.arch_springer_z(_hole_idx(zh)) - _BODY_BOTTOM


def _lam_of(lam, zh):
    # type: (Dict[str, float], str) -> float
    """孔当前 λ(缺省 0=架上满承载); 在册值域防御。"""
    v = lam.get(zh, 0.0)
    if not isinstance(v, (int, float)) or isinstance(v, bool) \
            or not (0.0 <= float(v) <= 1.0):
        raise ValueError("pier_imbalance: %s λ=%r 非法(须∈[0,1])" % (zh, v))
    return float(v)


def _env_of(H_env_by_hole, zh):
    # type: (Dict[str, Any], str) -> Optional[Tuple[float, float]]
    """孔 H 可行区间 (Hmin, Hmax); 缺 → None(贡献 0 并在 entry 落注记)。"""
    env = H_env_by_hole.get(zh)
    if env is None:
        return None
    lo, hi = (float(env[0]), float(env[1]))
    if not (0.0 <= lo <= hi):
        raise ValueError("pier_imbalance: %s H 区间 %r 非法(须 0≤min≤max)"
                         % (zh, env))
    return lo, hi


def _pier_calc(k, ev_hole, lam, H_env_by_hole, dims, ev_etype="?",
               top_loads=None):
    # type: (int, str, Dict[str, float], Dict[str, Any], Optional[Dict[str, Dict[str, float]]], str, Optional[Dict[str, float]]) -> Dict[str, Any]
    """墩 k(1..16, PIER_X[k] 中心, 两邻孔 ARCH0k/ARCH0k+1) 在当前 λ 态下
    的双指标账(pure; pier_imbalance 与建议扫描共用)。

    [主控 2026-10-07 包络连续性裁决] 有效推力一律 H_eff = λ × Hmin
    (Heyman 最小推力原理: 逐档缓释木楔时拱向最小推力收敛 —— 事件孔与
    已清账孔同式, λ=1 处无 Hmax→Hmin 突跳, 与收账态连续)。旧口径
    "事件孔取 Hmax"降为**保守敏感性对照**: ratio_hmax/e_kernel_hmax/
    dH_hmax 仅记录不判红(PASS 判据 = Hmin 物理口径)。"""
    zh_l, zh_r = "ARCH%02d" % k, "ARCH%02d" % (k + 1)
    env_l, env_r = _env_of(H_env_by_hole, zh_l), _env_of(H_env_by_hole, zh_r)
    lo_l, hi_l = env_l if env_l else (0.0, 0.0)
    lo_r, hi_r = env_r if env_r else (0.0, 0.0)
    lam_l, lam_r = _lam_of(lam, zh_l), _lam_of(lam, zh_r)
    # [Hmin 物理口径, PASS 判据] 全孔同式 λ×Hmin: 逐档缓释时拱向最小推力,
    # 事件孔与已清账孔连续(λ=1 无间断), 与收账态全绿自洽
    h_l = lam_l * lo_l
    h_r = lam_r * lo_r
    dh = h_l - h_r                       # 净水平推力(+x 为正)
    # [Hmax 敏感性对照, 仅记录不判红] 事件孔取区间上界的旧保守包络
    h_lx = lam_l * (hi_l if ev_hole == zh_l else lo_l)
    h_rx = lam_r * (hi_r if ev_hole == zh_r else lo_r)
    dhx = h_lx - h_rx
    ha_l, ha_r = _h_app(zh_l), _h_app(zh_r)
    h_ref = max(ha_l, ha_r)              # 保守单臂
    m_unb = abs(dh) * h_ref
    m_center = abs(h_l * ha_l - h_r * ha_r)   # 绕基底中线精确合力矩
    tl = top_loads or {}
    b, v, src = _pier_statics(k, dims, tl.get(zh_l, 0.0), tl.get(zh_r, 0.0))
    m_res = v * b / 2.0
    half_w = b / KERNEL_FRAC
    ratio = (m_res / m_unb) if m_unb > TOL else None
    e_kernel = m_center / v
    v_r = "ok" if (ratio is None or ratio >= RATIO_MIN - TOL) else "RED"
    v_k = "ok" if e_kernel <= half_w + TOL else "RED"
    if v_r == "ok" and v_k == "ok":
        verdict = "ok"
    else:
        verdict = "+".join(
            t for t, v_ in (("RATIO_RED", v_r), ("KERNEL_RED", v_k))
            if v_ == "RED")
    m_unb_x = abs(dhx) * h_ref
    ratio_x = (m_res / m_unb_x) if m_unb_x > TOL else None
    e_kernel_x = abs(h_lx * ha_l - h_rx * ha_r) / v
    return {"pier_id": "PIER%02d" % k, "hole": ev_hole, "etype": ev_etype,
            "H_L": h_l, "H_R": h_r, "dH": dh,
            "M_unb": m_unb, "M_center": m_center, "M_res": m_res,
            "ratio": ratio, "e_kernel": e_kernel, "kernel_half_w": half_w,
            "dH_hmax": dhx, "M_unb_hmax": m_unb_x, "ratio_hmax": ratio_x,
            "e_kernel_hmax": e_kernel_x,
            "h_L": ha_l, "h_R": ha_r, "h_ref": h_ref,
            "V": v, "base_w": b, "dims_source": src,
            "lam_L": lam_l, "lam_R": lam_r,
            "verdict_ratio": v_r, "verdict_kernel": v_k, "verdict": verdict,
            "env_missing": [z for z, e in ((zh_l, env_l), (zh_r, env_r))
                            if e is None]}


def pier_imbalance(snap, H_env_by_hole, lam, pier_dims=None,
                   top_loads=None):
    # type: (Snapshot, Dict[str, Any], Dict[str, float], Optional[Dict[str, Dict[str, float]]], Optional[Dict[str, float]]) -> Dict[str, Dict[str, Any]]
    """brief 接口: 对 snap 当前事件(须为 DECENTERING 类)算该孔两侧内墩的
    {pier_id: {H_L,H_R,dH,M_unb,M_res,ratio,e_kernel,verdict,...}}。
    λ 态由调用方按事件推进(WEDGE_RELEASE=load_lambda, DECENTER_START=0,
    CENTERING_CLEAR=1); 非 DECENTERING 事件返回 {}。桥台侧(k=0/17)不评。"""
    ev = snap.event
    if ev is None or ev.get("etype") not in E.DECENTERING_TYPES:
        return {}
    zh = ev.get("hole") or ""
    idx = _hole_idx(zh)
    out = {}  # type: Dict[str, Dict[str, Any]]
    for k in (idx, idx + 1):             # 西墩 PIER_X[idx], 东墩 PIER_X[idx+1]
        if k < 1 or k > F.N_SPAN - 1:    # 0/17 = 桥台, 不在本门域
            continue
        out["PIER%02d" % k] = _pier_calc(k, zh, lam, H_env_by_hole,
                                         pier_dims, ev_etype=ev.get("etype"),
                                         top_loads=top_loads)
    return out


def _lam_advance(lam, ev):
    # type: (Dict[str, float], Dict[str, Any]) -> None
    """按事件推进 λ 态(in place): WEDGE_RELEASE=load_lambda(缺值/越界
    ValueError fail-closed), CENTERING_CLEAR=1.0, DECENTER_START=0
    (显式归零 —— "拆架重建再卸"路径下 λ 良定; 本词表不支持二次落架,
    二次 DECENTER_START 即按新一轮卸架从 0 起, 与 R4_LADDER 全阶一致)。"""
    zh = ev.get("hole") or ""
    et = ev.get("etype")
    if et == "WEDGE_RELEASE":
        v = ev.get("load_lambda")
        if not isinstance(v, (int, float)) or isinstance(v, bool) \
                or not (0.0 <= float(v) <= 1.0):
            raise ValueError(
                "imbalance_gate: %s WEDGE_RELEASE seq=%s load_lambda=%r "
                "缺值/越界[0,1] —— fail-closed" % (zh, ev.get("seq"), v))
        lam[zh] = float(v)
    elif et == "CENTERING_CLEAR":
        lam[zh] = 1.0
    elif et == "DECENTER_START":
        lam[zh] = 0.0


def _pier_advice(entry, H_env_by_hole, dims):
    # type: (Dict[str, Any], Dict[str, Any], Optional[Dict[str, Dict[str, float]]]) -> List[str]
    """超阈墩的可执行顺序建议(用 entry 内冻结的事件时刻邻孔 λ 态):
    ① λ 临界扫描(邻孔态不动, 事件孔 λ∈[0,1] 0.05 步); ② 同 stage 逐档
    同步落架(档差≤一档)的末档残余核算 —— 同步后仍红则点名"须两孔同档
    同时释放或走冻结几何变更流程(加宽基底, 非本门可放)"。"""
    pid, zh = entry["pier_id"], entry["hole"]
    idx = _hole_idx(zh)
    k = int(pid[4:])                     # "PIER08" → 8(1..16)
    zh_l, zh_r = "ARCH%02d" % k, "ARCH%02d" % (k + 1)
    zh_o = zh_r if zh == zh_l else zh_l  # 共享本墩的另一邻孔
    if entry["verdict_ratio"] == "RED":
        worst = "ratio=%.2f<%.2f" % (entry["ratio"], RATIO_MIN)
    else:
        worst = "e_kernel=%.3f>B/6=%.3f" % (entry["e_kernel"],
                                            entry["kernel_half_w"])
    base = {zh_l: entry["lam_L"], zh_r: entry["lam_R"]}
    lam_a = entry["lam_active"]
    passing = []
    for i in range(21):
        trial = dict(base)
        trial[zh] = 0.05 * i
        if _pier_calc(k, zh, trial, H_env_by_hole, dims)["verdict"] == "ok":
            passing.append(0.05 * i)
    if passing and max(passing) >= 1.0 - 1e-9:
        crit = "λ 全域可过(与现账态矛盾, 请复核)"
    elif passing:
        hi_p = max(passing)
        if hi_p < lam_a:
            crit = "邻孔当前态(%s λ=%.2f)下本孔 λ≤%.2f 可过(现 %.2f)" \
                % (zh_o, base[zh_o], hi_p, lam_a)
        else:
            crit = "本孔 λ≥%.2f 才可过 —— 对侧孔 %s(λ=%.2f)已主导推本墩" \
                % (min(passing), zh_o, base[zh_o])
    else:
        crit = "邻孔当前态(%s λ=%.2f)下本孔任何 λ 均超阈" % (zh_o, base[zh_o])
    if base[zh_o] >= 1.0 - 1e-9:
        first = ("邻孔 %s 已全落架(回馈已取保守下界 Hmin) —— 本墩残余不平衡"
                 "为本孔推力包络固有, 排程侧无可再让" % zh_o)
    else:
        first = ("卸架顺序建议: 与邻孔 %s 同 stage 逐档同步落架(档差≤%.2f) / "
                 "先落架邻孔 %s 至 λ=1 再落本孔"
                 % (zh_o, LAMBDA_GRID_STEP, zh_o))
    # 同 stage 逐档同步(档差≤一档)末档残余: 本孔 λ_a, 邻孔 λ_a−一档
    trial = dict(base)
    trial[zh] = lam_a
    trial[zh_o] = max(0.0, lam_a - LAMBDA_GRID_STEP)
    e3 = _pier_calc(k, zh, trial, H_env_by_hole, dims)
    resid = ("同 stage 逐档同步(档差≤%.2f)末档残余核算: %s"
             % (LAMBDA_GRID_STEP,
                "可过(dH=%.2f)" % e3["dH"] if e3["verdict"] == "ok"
                else "仍超阈(%s) —— 须两孔同档同时释放或走冻结几何变更"
                     "流程(加宽基底, 非本门可放)" % e3["verdict"]))
    return ["%s(seq=%d %s %s λ=%.2f %s): %s; %s; %s"
            % (pid, entry["seq"], zh, entry["etype"], lam_a, worst, crit,
               first, resid)]


def _imbalance_walk(events, H_env_by_hole, ledger, in_void, dims, top_loads):
    # type: (List[Dict[str, Any]], Dict[str, Any], Optional[Dict[str, Any]], Optional[Set[str]], Dict[str, Dict[str, float]], Dict[str, float]) -> Tuple[List[Dict[str, Any]], List[str], int]
    """④门评估走(单遍): 逐 DECENTERING 事件 × 邻墩出 entry + 违例串。
    供 imbalance_gate 主读数与 viol_uniform_hmax 一致-Hmax 读数两次调用。"""
    lam = {}  # type: Dict[str, float]
    viols = []  # type: List[str]
    entries = []  # type: List[Dict[str, Any]]
    n_skip = 0
    for snap in snapshots(events, ledger if ledger is not None
                          else {"stones": []}, in_void=in_void):
        ev = snap.event
        if ev is None or ev.get("etype") not in E.DECENTERING_TYPES:
            continue
        _lam_advance(lam, ev)
        zh = ev.get("hole") or ""
        if zh not in H_env_by_hole:
            n_skip += 1        # 事件孔无 H 读数: 无法出数, 落注记不静默
            continue
        seq = ev.get("seq")
        for pid, e in pier_imbalance(snap, H_env_by_hole, lam,
                                     pier_dims=dims,
                                     top_loads=top_loads).items():
            e["seq"] = seq
            e["lam_active"] = _lam_of(lam, zh)
            entries.append(e)
            if e["verdict_ratio"] == "RED":
                viols.append(
                    "%s pier=%s seq=%d hole=%s %s λ=%.2f dH=%.3f "
                    "ratio=%.3f<%.2f (M_res=%.2f M_unb=%.2f V=%.2f B=%.2f)"
                    % (CODE_IMB_RATIO, pid, seq, zh, e["etype"],
                       e["lam_active"], e["dH"], e["ratio"], RATIO_MIN,
                       e["M_res"], e["M_unb"], e["V"], e["base_w"]))
            if e["verdict_kernel"] == "RED":
                viols.append(
                    "%s pier=%s seq=%d hole=%s %s λ=%.2f e_kernel=%.3f>"
                    "B/6=%.3f (M_center=%.2f V=%.2f B=%.2f)"
                    % (CODE_IMB_KERNEL, pid, seq, zh, e["etype"],
                       e["lam_active"], e["e_kernel"], e["kernel_half_w"],
                       e["M_center"], e["V"], e["base_w"]))
    return entries, viols, n_skip


def imbalance_gate(events, H_env_by_hole, ledger=None, in_void=None,
                   pier_dims=None, r5a=None):
    # type: (List[Dict[str, Any]], Dict[str, Any], Optional[Dict[str, Any]], Optional[Set[str]], Optional[Dict[str, Dict[str, float]]], Optional[Dict[str, List[str]]]) -> Dict[str, Any]
    """G3④ 门: 逐 DECENTERING 事件在 snapshot 上算两侧内墩双指标(同形节:
    violations/violation_counts/ok/elapsed_s + events 逐墩账 + piers 汇总
    + advice)。事件孔缺 H 区间 → 跳过并落 skipped 注记(fail-closed
    可见); 邻孔缺 → 贡献 0 并逐 entry 落 env_missing。V 含墩顶两孔
    RING+R5a 竖向反力(R2 完整性, r5a 缺省 load_r5a_shoulders 单源)。
    [T7b R1·条件性机器可读] `viol_uniform_hmax` = 一致 Hmax 读数(α=1,
    全孔同式取 Hmax)下的违例组合数 —— H∈[Hmin,Hmax] 皆静力可及, Hmin 是
    点估计非保守界: 本门在 Hmin 读数下不违例 ⇒ 只能判定不违例, 不能判定
    可行; 该数字即"换读数即翻红"的量化。entry 的 *hmax 字段 = box 非对称
    读数(事件孔 Hmax/其余 Hmin), 第三种读数供对照。
    判据先行的红绿都是结论 —— ok=False 时 run_g3 raise
    G3_DECENTER_ORDER_CONFLICT。"""
    t0 = time.perf_counter()
    dims = dict(_pier_dims_from_ledger(ledger or {}))
    if pier_dims:
        dims.update(pier_dims)
    top_loads = _hole_top_loads(ledger or {}, r5a)
    entries, viols, n_skip = _imbalance_walk(events, H_env_by_hole, ledger,
                                             in_void, dims, top_loads)
    counts = {}  # type: Dict[str, int]
    for v in viols:
        code = v.split(" ", 1)[0]
        counts[code] = counts.get(code, 0) + 1
    piers = {}  # type: Dict[str, Dict[str, Any]]
    for e in entries:
        rec = piers.setdefault(e["pier_id"], {
            "base_w": e["base_w"], "V": e["V"],
            "dims_source": e["dims_source"], "n_evals": 0,
            "worst_ratio": None, "worst_kernel": None})
        rec["n_evals"] += 1
        wr, wk = rec["worst_ratio"], rec["worst_kernel"]
        if e["ratio"] is not None and (wr is None or e["ratio"] < wr["ratio"]):
            rec["worst_ratio"] = e
        if wk is None or e["e_kernel"] > wk["e_kernel"]:
            rec["worst_kernel"] = e
    advice = []  # type: List[str]
    if viols:
        for pid in sorted(piers):
            rec = piers[pid]
            worst = rec["worst_ratio"] if (
                rec["worst_ratio"] is not None
                and rec["worst_ratio"]["verdict_ratio"] == "RED") \
                else rec["worst_kernel"]
            if worst is not None:
                advice.extend(_pier_advice(worst, H_env_by_hole, dims))
    # R1·条件性机器可读: 一致 Hmax 读数(α=1, 全孔同式取 Hmax)下的违例
    # 组合数 —— H∈[Hmin,Hmax] 皆静力可及, Hmin 是点估计非保守界: 本门在
    # Hmin 读数下不违例 ⇒ 只能判定不违例, 不能判定可行; 该数字即"换读数
    # 即翻红"的条件性量化。
    u_env = {z: (float(e_[1]), float(e_[1]))
             for z, e_ in H_env_by_hole.items()}
    viol_uniform_hmax = sum(
        1 for e in _imbalance_walk(events, u_env, ledger, in_void, dims,
                                   top_loads)[0] if e["verdict"] != "ok")
    return {"ok": not viols, "violations": viols, "violation_counts": counts,
            "elapsed_s": time.perf_counter() - t0,
            "n_evals": len(entries), "n_skipped_events": n_skip,
            "viol_uniform_hmax": viol_uniform_hmax,
            "skipped_note": ("事件孔缺 acceptance H 区间(③门未出/不可行), "
                             "本门跳过该事件 — fail-closed 注记" if n_skip
                             else ""),
            "piers": piers, "events": entries, "advice": advice}


# ---------------------------------------------------------------------------
# run_g3(报告串接: gate_dag(①)+gate_stress(③)+gate_imbalance(④, T7))
# ---------------------------------------------------------------------------

def run_g3(events, ledger, centerings=None, in_void=None, rbo_ids=None,
           threshold=SWALLOW_THRESHOLD, r5a=None):
    # type: (List[Dict[str, Any]], Dict[str, Any], Optional[List[Dict[str, Any]]], Optional[Set[str]], Optional[List[str]], float, Optional[Dict[str, List[str]]]) -> Dict[str, Any]
    """G3 报告: gate_dag(①)+double_model 清单(W1)+gate_stress(③压力线)
    +gate_imbalance(④墩不平衡·最小推力读数, T7)。③ acceptance(结构带=环+
    胶结锁固带; P2-T6 裁决)不可行 → raise G3_FROZEN_GEOMETRY_CONFLICT
    停报主控(停车线; 禁调封卷几何参数自救)。④ λ 卸架档+核距双指标逐
    DECENTERING 事件全墩: H 区间取③ acceptance 可行区间(同报告单源);
    红 → raise G3_DECENTER_ORDER_CONFLICT(排程冲突, 停报主控, 报告挂
    exc.report 含逐墩账+卸架顺序建议; 修正走 sequencer, 禁调 λ/裕度/
    核宽自救)。快照面用 snapshots(...)/Snapshot.copy()。"""
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
            "generated_by": "g3_check.py P2-T5+T6+T7",
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
    # T7④: H 区间单源 = ③ acceptance 可行区间(同报告, 不重算不造第二套)
    H_env = {zh: h["acceptance"]["H"]
             for zh, h in report["gate_stress"]["holes"].items()
             if h["acceptance"].get("feasible")}
    report["gate_imbalance"] = imbalance_gate(events, H_env, ledger=ledger,
                                              in_void=in_void, r5a=r5a)
    if not report["gate_imbalance"]["ok"]:
        exc = G3_DECENTER_ORDER_CONFLICT(
            "G3④墩推力不平衡超阈(卸架顺序排程冲突, 停报主控; 修正走 "
            "sequencer 排程, 禁调 λ/裕度/核宽自救): " + "; ".join(
                report["gate_imbalance"]["violations"][:6])
            + (" ...共 %d 条" % len(report["gate_imbalance"]["violations"])
               if len(report["gate_imbalance"]["violations"]) > 6 else ""))
        exc.report = report          # 停报主控: 三节齐 + 逐墩账 + 顺序建议
        raise exc
    return report
