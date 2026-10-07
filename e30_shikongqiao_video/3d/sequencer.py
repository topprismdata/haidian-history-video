# e30_shikongqiao_video/3d/sequencer.py
# -*- coding: utf-8 -*-
"""P2-T4 建造序列器: R0-R7 规则引擎 + frontier 状态机 → 事件流 + stage 分组。

输入: 石账(ledger v2, 5935 真源只读) + 券架表(centering.build_centering_for_arch)。
输出: {"events", "sequence", "frontier_trace", "meta"}; 券石支撑曲线回写石账
**副本** out/ledger_sequenced.json(原 ledger_full.json 永不改动)。

规则(spec v2.1 §2, 逐条实现+每规则≥1 测试):
- R0 良构性: seq 从 1 起全局连续递增; 每石恰出现在一个 MASONRY 事件; 角色可分类。
- R1 墩 z 升序: 孔内 IMPOST/PIER(墩肩/拱座)先砌, 逐石 z_bottom 非降序。
- R2 券架先行: 每孔先发 HOLD_EVENT(hole, stone_id=CEN-ARCHxx) 为立架锚事件
  (7 类事件词表中唯一可合法引用券架的持荷形态, events.py 前缀分流核); 全部
  RING 石 PLACE_STONE 的 prereq ⊇ {立架 seq} 且 seq ∈ (立架, 合龙) 开窗。
- R3 荷载平衡度: 券石按弧参数 θ 两侧交替——θ 中值镜像配对(东/西对称对),
  配对为放置单位; 每孔以**偶数位前缀(配对完成)与收尾前缀**核
  |W_L−W_R|/(W_L+W_R) ≤ ε。单石前缀(首块券石落座 W 单侧=满重)由墩台直接
  承托非拱作用承担, 不入核——否则闸恒假。W=体积×密度, 密度取 STONE_DENSITY=1.0:
  R3 比值对共同密度因子不变, 则例石作密度论题在册(C:A1-A5)但无数值, 禁发明
  [三红线]。体积估计纯消费 facts.arch_z 单源(弧长×环厚×width_at 桥宽)。
- R4 合龙持荷落架: CLOSE_RING(prereq ⊇ 该孔全部 RING 置放) → ≥min_hold 个
  HOLD_EVENT → DECENTER_START → WEDGE_RELEASE×k 沿 λ 栅格 {0.25,.5,.75,1.0}
  逐档全走(load_lambda=已释放荷载份额) → CENTERING_CLEAR。
  min_hold=3 [工程参数·敏感性]。
- R5a 环肩锁固: 环肩咬合石(params.clipped_by=="ring_band")与下部锁固肩
  (判据: 石底 z ≤ 该孔 extrados[facts.arch_z+params.ring_t] ∧ 石 bbox 与券架
  parts bbox[全局系] 无碰撞)排 CLOSE 后 CLEAR 前, prereq ⊇ {合龙 seq}。
- R5b 其余肩背胞: 其余 SPANDREL/BACK/CORE 排 CENTERING_CLEAR 后。
- R6 frontier 状态机: 孔状态 UNBUILT < RING_CLOSED < CLOSED_SUPPORTED <
  DECENTERING < CLEARED < FILLED; 跨孔组合表禁: 相邻孔同时 DECENTERING;
  孔 i DECENTERING 而 i±1 < CLOSED_SUPPORTED(跳孔落架)。组合表反推构造
  日程必须两波: 波1 逐孔砌至持荷(CLOSED_SUPPORTED), 波2 逐孔落架拆架填胞
  —— 否则首孔落架时邻孔必 UNBUILT, 恒违例。
- R7 面上最后: PAVING → RAIL/POST → CARVE 全局收尾(真账 5935 石暂无此四角色,
  形制就绪; 合成账钉测试)。

石账支撑曲线回写(回写副本, 石账纯度红线: 券架/事件不进石账):
- IMPOST/PIER: foundation 边 [[place,1.0]](墩台直接承托)。
- RING/R5a: centering 边按 λ 阶梯衰减 [[place,1.0],[DECENTER,1.0],
  [W1,0.75],[W2,0.5],[W3,0.25],[W4,0.0],[CLEAR,0.0]] + stone 边自持接管
  [[W4,1.0]](拱圈自持, RING)/[[CLEAR,1.0]](肩石落于环体)。
- 其余(R5b): stone 边 [[place,1.0]]。
全部 curve x 均为真实事件 seq(E.event_seqs 交叉核)。

史料引用(construction_history.md 编号, GRADES=inferred——序列细节靠通例+实物
反推, C:A3 明示则例无工序教科书): 立架/落架/拆架=C:A3/B14; 券石=C:A2/B14;
合龙/持荷=B14; 撞券石=C:A2; 背胞fill=C:A1; R7=C:A1。

Python 3.9.6 纯 stdlib, blender-free; 几何禁第二套公式(消费 geom_math/facts)。
"""
import copy
import json
import math
import os
from typing import Any, Dict, List, Optional

import ledger as L
import events as E
import centering as CEN
import geom_math as GM
import facts as F

EPS_DEFAULT = 0.15          # [工程参数·敏感性] R3 平衡度阈
MIN_HOLD_DEFAULT = E.MIN_HOLD_DEFAULT
LAMBDA_LADDER = (0.25, 0.5, 0.75, 1.0)   # λ 档全走(spec 1/4 步进)
STONE_DENSITY = 1.0         # R3 比值对共同密度不变, 不发明无出处常数[三红线]
PAIR_MIRROR_TOL = 1e-6      # θ 镜像配对容差(度)
EXTRADOS_EPS = 1e-9         # z 比较浮点容差

# 角色分类(R0 fail-closed: 未登记角色报错, 不静默归类)
IMPOST_ROLES = ("IMPOST", "PIER")            # R1: 墩肩/拱座, 立架前
RING_ROLE = "RING"
FILL_ROLES = ("SPANDREL", "BACK", "CORE")    # R5a/R5b 分类域
R7_PAVING = ("PAVING",)
R7_RAIL_POST = ("RAIL", "POST")
R7_CARVE = ("CARVE",)
KNOW_ROLES = IMPOST_ROLES + (RING_ROLE,) + FILL_ROLES + R7_PAVING + R7_RAIL_POST + R7_CARVE

R7_ORDER = ("PAVING", "RAIL_POST", "CARVE")

# frontier 状态(严格升序)
FRONTIER_STATES = ("UNBUILT", "RING_CLOSED", "CLOSED_SUPPORTED",
                   "DECENTERING", "CLEARED", "FILLED")
_STATE_RANK = {s: i for i, s in enumerate(FRONTIER_STATES)}

# 事件证据编号(refs/construction_history.md; 形制 A\d+|B\d+|C:[AB]\d+)
EV_IMPOST = "C:A2"          # 撞券石名目
EV_CEN = "C:A3/B14"         # 支拆券胎在册 + 落架拆除反证
EV_RING = "C:A2/B14"        # 券石名目 + 对称砌筑→合龙→落架序锚
EV_CLOSE = "B14/C:A2"       # 合龙石楔入
EV_HOLD = "B14"             # 合龙前拱圈不能自持→持荷
EV_SHOULDER = "B14"         # 券体依赖周围砌体共同工作(孔庆普拆除实证)
EV_FILL = "C:A1"            # 则例石作制度
EV_R7 = "C:A1"


class SequencerError(Exception):
    """序列构造自检失败(负控/自闸), 携带规则码(如 R3_IMBALANCE)。"""


# ---------------------------------------------------------------------------
# 石几何估计(纯 params 消费; 断面语义同 masonry2: wedge-std transform=块中心,
# slab transform=最小角(bbox 直写))
# ---------------------------------------------------------------------------

def _role(sid):
    # type: (str) -> str
    return sid.split(".")[2]


def _stone_xz(stone):
    # type: (Dict[str, Any]) -> Any
    """石中点 (x_mid, z_bottom, z_mid) 估计: wedge-std=transform 中心±h/2;
    slab=paramsgroup bbox; 其余回退 transform[2]。"""
    p = stone.get("params", {}) or {}
    role = _role(stone.get("id", ""))
    if role == "CORE" and isinstance(p.get("bbox"), dict):
        bb = p["bbox"]
        return ((bb["x0"] + bb["x1"]) / 2.0, bb["z0"],
                (bb["z0"] + bb["z1"]) / 2.0)
    tz = stone.get("transform", [0, 0, 0])[2]
    h = p.get("h")
    if isinstance(h, (int, float)) and not isinstance(h, bool):
        return (stone.get("transform", [0, 0, 0])[0], tz - h / 2.0, tz)
    return (stone.get("transform", [0, 0, 0])[0], tz, tz)


def stone_weight(stone, density=STONE_DENSITY):
    # type: (Dict[str, Any], float) -> float
    """石重=体积×密度。体积从 params 估: CORE= bbox 直积; RING=环厚×弧长×桥宽
    (弧长经 facts.arch_z 单源采样); 其余=w×h×d 断面矩形[估计]。"""
    p = stone.get("params", {}) or {}
    role = _role(stone.get("id", ""))
    if role == "CORE" and isinstance(p.get("bbox"), dict):
        bb = p["bbox"]
        vol = ((bb["x1"] - bb["x0"]) * (bb["y1"] - bb["y0"])
               * (bb["z1"] - bb["z0"]))
    elif role == RING_ROLE:
        vol = _ring_volume(stone)
    else:
        w = p.get("w", 0.0)
        h = p.get("h", 0.0)
        d = p.get("d", 0.0)
        vol = float(w) * float(h) * float(d)
    return vol * density


def _ring_volume(stone):
    # type: (Dict[str, Any]) -> float
    """券石体积: 环厚 params.ring_t × 内弧弧长(facts.arch_z 采样) ×
    桥宽(2×geom_math.width_at 石中高处)。"""
    p = stone.get("params", {}) or {}
    ring_t = float(p["ring_t"])
    xc = float(p["xc"])
    st = p["stations"]
    x0, x1 = float(st[0]), float(st[1])
    ai = int(stone["id"].split(".")[0][4:]) - 1
    a = GM.SPANS[ai] / 2.0
    b = GM.arch_rise(ai)
    springer = GM.arch_springer_z(ai)

    def z_lo(lx):
        return F.arch_z(lx, 0.0, springer, a, b)

    n = 8
    arc = 0.0
    prev = None  # type: Optional[tuple]
    for k in range(n + 1):
        gx = x0 + (x1 - x0) * k / float(n)
        cur = (gx, z_lo(gx - xc))
        if prev is not None:
            arc += math.hypot(cur[0] - prev[0], cur[1] - prev[1])
        prev = cur
    xm = (x0 + x1) / 2.0
    zm = z_lo(xm - xc) + ring_t / 2.0
    depth = 2.0 * GM.width_at(xm, zm)
    return ring_t * arc * depth


def _theta_mid(stone):
    # type: (Dict[str, Any]) -> float
    """券石弧参数中值(度)。"""
    ang = stone["params"]["angles"]
    return (float(ang[0]) + float(ang[1])) / 2.0


def _theta_left_frac(stone):
    # type: (Dict[str, Any]) -> float
    """券石重量归于左半拱(θ<0)的份额: 龙门石按 θ=0 分割。"""
    ang = stone["params"]["angles"]
    t0, t1 = float(ang[0]), float(ang[1])
    if t1 <= t0:
        return 0.5
    return min(1.0, max(0.0, (0.0 - t0) / (t1 - t0)))


def _plan_ring_banks(ring_stones):
    # type: (List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]
    """θ 镜像配对 → 放置单位(两侧交替); 单数收尾为龙门石独行行。"""
    order = sorted(ring_stones, key=_theta_mid)
    n = len(order)
    banks = []
    i, j = 0, n - 1
    while i < j:
        mi, mj = _theta_mid(order[i]), _theta_mid(order[j])
        if abs(mi + mj) > PAIR_MIRROR_TOL:
            raise SequencerError(
                "R3_PAIRING 券石 θ 非镜像对称: %s(%.4f) vs %s(%.4f)"
                % (order[i]["id"], mi, order[j]["id"], mj))
        banks.append([order[i], order[j]])
        i += 1
        j -= 1
    if i == j:
        banks.append([order[i]])
    return banks


def _ring_stone_box(stone):
    # type: (Dict[str, Any]) -> tuple
    """券石全局 bbox 估计(占位冲突用): stations x 跨 × 环厚 z 向 × 桥宽 y 向。"""
    p = stone["params"]
    ring_t = float(p["ring_t"])
    xc = float(p["xc"])
    st = p["stations"]
    ai = int(stone["id"].split(".")[0][4:]) - 1
    a = GM.SPANS[ai] / 2.0
    b = GM.arch_rise(ai)
    springer = GM.arch_springer_z(ai)
    xm = (float(st[0]) + float(st[1])) / 2.0
    z_lo = F.arch_z(xm - xc, 0.0, springer, a, b)
    hw = GM.width_at(xm, z_lo + ring_t / 2.0)
    return (min(float(st[0]), float(st[1])), max(float(st[0]), float(st[1])),
            -hw, hw, z_lo, z_lo + ring_t)


def _wedge_std_box(stone):
    # type: (Dict[str, Any]) -> tuple
    """wedge-std 石 bbox(masonry2 语义): x/z=块中心±, y=外缘|ty|内缘|ty|-d。"""
    t = stone.get("transform", [0, 0, 0])
    p = stone.get("params", {}) or {}
    w = float(p.get("w", 0.0))
    h = float(p.get("h", 0.0))
    d = float(p.get("d", 0.0))
    ty = float(t[1])
    y_out = abs(ty)
    y0, y1 = (y_out - d, y_out) if ty >= 0 else (-y_out, -(y_out - d))
    return (float(t[0]) - w / 2.0, float(t[0]) + w / 2.0,
            min(y0, y1), max(y0, y1),
            float(t[2]) - h / 2.0, float(t[2]) + h / 2.0)


def _slab_box(stone):
    # type: (Dict[str, Any]) -> tuple
    bb = (stone.get("params", {}) or {}).get("bbox")
    if not isinstance(bb, dict):
        return _wedge_std_box(stone)
    return (bb["x0"], bb["x1"], bb["y0"], bb["y1"], bb["z0"], bb["z1"])


def _stone_box(stone):
    # type: (Dict[str, Any]) -> tuple
    role = _role(stone.get("id", ""))
    if role == "CORE":
        return _slab_box(stone)
    if role == RING_ROLE:
        return _ring_stone_box(stone)
    return _wedge_std_box(stone)


def _boxes_collide(b1, b2, tol=EXTRADOS_EPS):
    # type: (tuple, tuple, float) -> bool
    return all(b1[2 * k + 1] > b2[2 * k] + tol
               and b2[2 * k + 1] > b1[2 * k] + tol for k in range(3))


def _centering_boxes_global(cen):
    # type: (Dict[str, Any]) -> List[tuple]
    """券架占位 bbox 全局系(parts bbox + xc 平移, centering.py 消费约定)。"""
    out = []
    xc = cen["xc"]
    for part in cen["parts"]:
        bx = part["bbox"]
        out.append((bx[0] + xc, bx[1] + xc, bx[2], bx[3], bx[4], bx[5]))
    return out


# ---------------------------------------------------------------------------
# 构造
# ---------------------------------------------------------------------------

def _hole_of(stone):
    # type: (Dict[str, Any]) -> str
    return stone["id"].split(".")[0]


def _arch_idx(zone):
    # type: (str) -> int
    return int(zone[4:]) - 1


def build_sequence(ledger, centerings, eps=EPS_DEFAULT,
                   min_hold=MIN_HOLD_DEFAULT, ring_order=None):
    # type: (Dict[str, Any], Any, float, int, Optional[Dict[str, List[str]]]) -> Dict[str, Any]
    """规则引擎主入口。ring_order: {zone: [ring stone id 顺序]} 可选显式券石
    顺序(负控注入位); None=按 θ 镜像配对自动派生。自检失败 raise SequencerError。
    """
    stones = ledger.get("stones", [])
    cen_by_zone = {}
    for c in (centerings or []):
        cen_by_zone[c["zone"]] = c
    by_id = {}
    holes = {}  # type: Dict[str, Dict[str, List[Dict[str, Any]]]]
    for s in stones:
        sid = s.get("id", "")
        if not sid:
            raise SequencerError("R0_NO_ID 石记录缺 id")
        if sid in by_id:
            raise SequencerError("R0_DUP_STONE 石 id 重复: %s" % sid)
        by_id[sid] = s
        role = _role(sid)
        if role not in KNOW_ROLES:
            raise SequencerError("R0_UNKNOWN_ROLE 石 %s 角色未登记: %s"
                                 % (sid, role))
        holes.setdefault(_hole_of(s), []).append(s)
    for zone in sorted(holes):
        if zone not in cen_by_zone:
            raise SequencerError("R2_NO_CENTERING 孔 %s 无券架记录" % zone)

    events = []  # type: List[Dict[str, Any]]
    trace = []  # type: List[Dict[str, Any]]
    stages = []  # type: List[Dict[str, Any]]
    edge_plan = {}  # type: Dict[str, List[Dict[str, Any]]]  # sid -> support_edges
    hole_report = []  # type: List[Dict[str, Any]]

    def emit(hole, etype, stone_id=None, prereq=(), load_lambda=None,
             evidence=EV_FILL, grade="inferred"):
        seq = len(events) + 1
        ev = E.new_event(seq, hole, etype, stone_id=stone_id,
                         prereq=list(prereq), load_lambda=load_lambda,
                         evidence=evidence, grade=grade)
        events.append(ev)
        return seq

    def open_stage(name, centering_id=None, evidence=EV_FILL):
        return {"id": "S%03d" % (len(stages) + 1), "stage": name,
                "event_range": None, "depends_on": None,
                "centering_id": centering_id, "evidence": evidence}

    def close_stage(st, first_seq, last_seq, dep_ids):
        st["event_range"] = [first_seq, last_seq]
        st["depends_on"] = list(dep_ids)
        stages.append(st)

    def stage_course_key(stone):
        return stone["id"].split(".")[3]

    # 两波推进(R6 语义要求: 孔 i 落架时邻孔 i±1 须 ≥ CLOSED_SUPPORTED,
    # 故逐孔"全合龙到持荷"先于任何落架 —— 波1 全孔到 CLOSED_SUPPORTED,
    # 波2 逐孔落架+拆架+肩背胞; 顺序均按孔号升序)。
    zones_sorted = sorted(holes)
    wave1 = {}  # type: Dict[str, Dict[str, Any]]
    for zone in zones_sorted:
        cen = cen_by_zone[zone]
        idx = _arch_idx(zone)
        a = GM.SPANS[idx] / 2.0
        b = GM.arch_rise(idx)
        springer = GM.arch_springer_z(idx)
        xc = GM.arch_center_x(idx)
        ring_t = float(next(s["params"]["ring_t"] for s in holes[zone]
                            if _role(s["id"]) == RING_ROLE))
        prev_stage = stages[-1]["id"] if stages else None

        def extrados_z(gx):
            return F.arch_z(gx - xc, 0.0, springer, a, b) + ring_t

        cen_boxes = _centering_boxes_global(cen)

        # -- R1: 墩肩/拱座 z 升序(立架前) --
        imposts = sorted((s for s in holes[zone]
                          if _role(s["id"]) in IMPOST_ROLES),
                         key=lambda s: (_stone_xz(s)[1], s["id"]))
        for st_course in _group_by(imposts, stage_course_key):
            st = open_stage("%s.IMPOST.%s" % (zone, stage_course_key(st_course[0])),
                            evidence=EV_IMPOST)
            lo = len(events) + 1
            for s in st_course:
                emit(zone, "PLACE_STONE", stone_id=s["id"], evidence=EV_IMPOST)
                edge_plan[s["id"]] = [{"type": "foundation",
                                       "capacity_curve": [[len(events), 1.0]]}]
            close_stage(st, lo, len(events), [prev_stage] if prev_stage else [])
            prev_stage = st["id"]

        # -- R2: 立架锚事件 --
        st = open_stage("%s.CENTER_ERECT" % zone, centering_id=cen["id"],
                        evidence=EV_CEN)
        lo = len(events) + 1
        erect_seq = emit(zone, "HOLD_EVENT", stone_id=cen["id"],
                         evidence=EV_CEN)
        close_stage(st, lo, len(events), [prev_stage] if prev_stage else [])
        prev_stage = st["id"]

        # -- R3: 券石 θ 镜像配对两侧交替 --
        ring_stones = [s for s in holes[zone]
                       if _role(s["id"]) == RING_ROLE]
        if ring_order is not None:
            order_ids = list(ring_order[zone])
            if sorted(order_ids) != sorted(s["id"] for s in ring_stones):
                raise SequencerError(
                    "R3_ORDER_SET ring_order 与该孔 RING 石集合不一致: %s" % zone)
            given = [by_id[sid] for sid in order_ids]
            banks = _banks_from_flat_order(given)
        else:
            banks = _plan_ring_banks(ring_stones)
        ring_seq_by_stone = {}
        for bi, bank in enumerate(banks):
            st = open_stage("%s.RING.bank%02d" % (zone, bi + 1),
                            centering_id=cen["id"], evidence=EV_RING)
            lo = len(events) + 1
            for s in sorted(bank, key=lambda s: (_theta_mid(s), s["id"])):
                seq = emit(zone, "PLACE_STONE", stone_id=s["id"],
                           prereq=[erect_seq], evidence=EV_RING)
                ring_seq_by_stone[s["id"]] = seq
            close_stage(st, lo, len(events), [prev_stage])
            prev_stage = st["id"]
        # R3 自闸(构造器即核, 负控注入点)
        _check_r3_order(banks, eps)

        # -- CLOSE_RING --
        st = open_stage("%s.CLOSE_RING" % zone, centering_id=cen["id"],
                        evidence=EV_CLOSE)
        lo = len(events) + 1
        close_seq = emit(zone, "CLOSE_RING",
                         prereq=[ring_seq_by_stone[s["id"]]
                                 for s in ring_stones],
                         evidence=EV_CLOSE)
        close_stage(st, lo, len(events), [prev_stage])
        prev_stage = st["id"]
        trace.append({"hole": zone, "state": "RING_CLOSED",
                      "at_seq": close_seq})

        # -- R5a: 环肩锁固(合龙后 CLEAR 前) --
        shoulders = []
        for s in holes[zone]:
            if _role(s["id"]) not in FILL_ROLES:
                continue
            if s["params"].get("clipped_by") == "ring_band" \
                    or _is_lock_shoulder(s, extrados_z, cen_boxes):
                shoulders.append(s)
        shoulders = sorted(shoulders,
                           key=lambda s: (_stone_xz(s)[1], s["id"]))
        for st_course in _group_by(shoulders, stage_course_key):
            st = open_stage("%s.SHOULDER.%s" % (zone, stage_course_key(st_course[0])),
                            centering_id=cen["id"], evidence=EV_SHOULDER)
            lo = len(events) + 1
            for s in st_course:
                emit(zone, "PLACE_STONE", stone_id=s["id"], prereq=[close_seq],
                     evidence=EV_SHOULDER)
            close_stage(st, lo, len(events), [prev_stage])
            prev_stage = st["id"]

        # -- R4: 持荷窗口 --
        st = open_stage("%s.HOLD" % zone, centering_id=cen["id"],
                        evidence=EV_HOLD)
        lo = len(events) + 1
        hold_seqs = [emit(zone, "HOLD_EVENT", stone_id=cen["id"],
                          prereq=[close_seq], evidence=EV_HOLD)
                     for _ in range(max(int(min_hold), 0))]
        close_stage(st, lo, len(events), [prev_stage])
        prev_stage = st["id"]
        trace.append({"hole": zone, "state": "CLOSED_SUPPORTED",
                      "at_seq": hold_seqs[-1] if hold_seqs else close_seq})

        # -- R5b 分类(排放留波2): 其余肩背胞 --
        rest = [s for s in holes[zone]
                if _role(s["id"]) in FILL_ROLES and s not in shoulders]
        rest = sorted(rest, key=lambda s: (_stone_xz(s)[1], s["id"]))
        wave1[zone] = {
            "cen": cen, "ring_stones": ring_stones,
            "ring_seq_by_stone": ring_seq_by_stone, "close_seq": close_seq,
            "hold_seqs": hold_seqs, "shoulders": shoulders, "rest": rest,
            "n_ring": len(ring_stones), "n_shoulder": len(shoulders),
            "n_fill": len(rest),
        }

    # -- 波2: 逐孔落架(λ 全阶)→拆架→肩背胞(R5b) --
    for zone in zones_sorted:
        w1 = wave1[zone]
        cen = w1["cen"]
        prev_stage = stages[-1]["id"] if stages else None
        st = open_stage("%s.DECENTER" % zone, centering_id=cen["id"],
                        evidence=EV_CEN)
        lo = len(events) + 1
        dseq = emit(zone, "DECENTER_START", stone_id=cen["id"],
                    prereq=[w1["close_seq"]] + w1["hold_seqs"],
                    evidence=EV_CEN)
        trace.append({"hole": zone, "state": "DECENTERING", "at_seq": dseq})
        wedge_seqs = []
        for lam in LAMBDA_LADDER:
            wedge_seqs.append(emit(zone, "WEDGE_RELEASE", stone_id=cen["id"],
                                   prereq=[dseq] + wedge_seqs,
                                   load_lambda=float(lam), evidence=EV_CEN))
        cseq = emit(zone, "CENTERING_CLEAR", stone_id=cen["id"],
                    prereq=[dseq, wedge_seqs[-1]] if wedge_seqs else [dseq],
                    evidence=EV_CEN)
        close_stage(st, lo, len(events), [prev_stage])
        prev_stage = st["id"]
        trace.append({"hole": zone, "state": "CLEARED", "at_seq": cseq})

        # 券石 centering 边(λ 阶梯衰减) + 自持边
        self_start = wedge_seqs[-1] if wedge_seqs else cseq
        for s in w1["ring_stones"]:
            edge_plan[s["id"]] = _supported_then_self_edges(
                w1["ring_seq_by_stone"][s["id"]], wedge_seqs, self_start,
                dstart=dseq, cseq=cseq)
        for s in w1["shoulders"]:
            edge_plan[s["id"]] = _supported_then_self_edges(
                _shoulder_place_seq(events, s["id"]), None, cseq,
                dstart=dseq, cseq=cseq)

        # -- R5b: 其余肩背胞(CLEAR 后), z_bottom 升序; 单阶段一孔一拍
        #    (13 层/孔会把 stage 数顶破 600 目标, 叙事上"填筑肩背"为一拍) --
        rest = w1["rest"]
        st = open_stage("%s.FILL" % zone, evidence=EV_FILL)
        lo = len(events) + 1
        for s in rest:
            emit(zone, "PLACE_STONE", stone_id=s["id"], prereq=[cseq],
                 evidence=EV_FILL)
            edge_plan[s["id"]] = [{"type": "stone",
                                   "capacity_curve": [[len(events), 1.0]]}]
        close_stage(st, lo, len(events), [prev_stage])
        prev_stage = st["id"]
        trace.append({"hole": zone, "state": "FILLED",
                      "at_seq": len(events)})
        hole_report.append({"zone": zone, "centering": cen["id"],
                            "n_ring": w1["n_ring"],
                            "n_shoulder": w1["n_shoulder"],
                            "n_fill": w1["n_fill"]})

    # -- R7: 面上最后 PAVING → RAIL/POST → CARVE --
    r7_groups = {"PAVING": [], "RAIL_POST": [], "CARVE": []}
    for s in stones:
        role = _role(s["id"])
        if role in R7_PAVING:
            r7_groups["PAVING"].append(s)
        elif role in R7_RAIL_POST:
            r7_groups["RAIL_POST"].append(s)
        elif role in R7_CARVE:
            r7_groups["CARVE"].append(s)
    for gname in R7_ORDER:
        grp = sorted(r7_groups[gname], key=lambda s: (_stone_xz(s)[1], s["id"]))
        if not grp:
            continue
        st = open_stage("%s.%s.GLOBAL" % (gname, "R7"), evidence=EV_R7)
        lo = len(events) + 1
        deps = [stages[-1]["id"]] if stages else []
        for s in grp:
            zh = _hole_of(s)
            emit(zh, "PLACE_STONE", stone_id=s["id"], evidence=EV_R7)
            edge_plan[s["id"]] = [{"type": "stone",
                                   "capacity_curve": [[len(events), 1.0]]}]
        close_stage(st, lo, len(events), deps)

    result = {
        "events": events,
        "sequence": stages,
        "frontier_trace": trace,
        "meta": {
            "n_stones": len(stones),
            "n_events": len(events),
            "eps": float(eps),
            "min_hold": int(min_hold),
            "hole_order": sorted(holes),
            "holes": hole_report,
            "generated_by": "sequencer.py P2-T4",
        },
        "_edge_plan": edge_plan,
    }
    return result


def _group_by(items, key):
    # type: (List[Dict[str, Any]], Any) -> List[List[Dict[str, Any]]]
    """按 key 分组, 组序 = 首次出现序(dict 插入序)——调用方已按 z 升序排过,
    重排回 course 键序会毁掉 R1 的 z 升序(真账 impost course 号与 z 反向)。"""
    out = {}  # type: Dict[Any, List[Dict[str, Any]]]
    for it in items:
        out.setdefault(key(it), []).append(it)
    return list(out.values())


def _banks_from_flat_order(flat):
    # type: (List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]
    """显式平铺顺序 → 每两石一配对单位(奇数收尾独行)。负控注入用。"""
    banks = []
    for k in range(0, len(flat) - 1, 2):
        banks.append([flat[k], flat[k + 1]])
    if len(flat) % 2 == 1:
        banks.append([flat[-1]])
    return banks


def _check_r3_order(banks, eps):
    # type: (List[List[Dict[str, Any]]], float) -> None
    """R3 前缀平衡度核(构造器自闸): 以配对完成(偶数位)前缀与收尾前缀为核。
    违例 raise SequencerError("R3_IMBALANCE ...")。"""
    w_l = w_r = 0.0
    placed = 0
    n_total = sum(len(bk) for bk in banks)
    for bank in banks:
        for s in bank:
            w = stone_weight(s)
            lf = _theta_left_frac(s)
            w_l += w * lf
            w_r += w * (1.0 - lf)
            placed += 1
        if placed % 2 == 0 or placed == n_total:
            tot = w_l + w_r
            if tot > 0.0:
                imb = abs(w_l - w_r) / tot
                if imb > eps:
                    raise SequencerError(
                        "R3_IMBALANCE 前缀 %d/%d 平衡度 %.4f > eps=%.3f "
                        "(W_L=%.3f W_R=%.3f)"
                        % (placed, n_total, imb, eps, w_l, w_r))


def _is_lock_shoulder(stone, extrados_z, cen_boxes):
    # type: (Dict[str, Any], Any, List[tuple]) -> bool
    """R5a 下部锁固肩判据: 石底 z ≤ 该孔 extrados 区 ∧ 石 bbox 与券架占位无碰撞。"""
    x_mid, z_bottom, _zm = _stone_xz(stone)
    if z_bottom > extrados_z(x_mid) + EXTRADOS_EPS:
        return False
    sb = _stone_box(stone)
    return not any(_boxes_collide(sb, cb) for cb in cen_boxes)


def _supported_then_self_edges(place_seq, wedge_seqs, self_start,
                               dstart=None, cseq=None):
    # type: (int, Optional[List[int]], int, Optional[int], Optional[int]) -> List[Dict[str, Any]]
    """centering 边(λ 阶梯衰减至 0) + stone 自持边。wedge_seqs=None →
    centering 边 [[place,1.0],[cseq,0.0]](肩石: 持荷期不卸载)。"""
    if wedge_seqs:
        curve = [[place_seq, 1.0], [dstart, 1.0]]
        for ws in wedge_seqs:
            curve.append([ws, 1.0 - _lambda_at(wedge_seqs, ws)])
        if cseq is not None:
            curve.append([cseq, 0.0])
    else:
        curve = [[place_seq, 1.0]]
        if cseq is not None:
            curve.append([cseq, 0.0])
    return [
        {"type": "centering", "capacity_curve": curve},
        {"type": "stone", "capacity_curve": [[self_start, 1.0]]},
    ]


def _lambda_at(wedge_seqs, seq):
    # type: (List[int], int) -> float
    k = wedge_seqs.index(seq)
    return float(LAMBDA_LADDER[k])


def _shoulder_place_seq(events, sid):
    # type: (List[Dict[str, Any]], str) -> int
    for e in events:
        if e.get("stone_id") == sid and e.get("etype") == "PLACE_STONE":
            return int(e["seq"])
    raise SequencerError("R5A_NO_PLACE 肩石 %s 无置放事件" % sid)


# ---------------------------------------------------------------------------
# 校验(check_sequence: 全规则复核, 负控入口; 返回错误码表, 空=绿)
# ---------------------------------------------------------------------------

def check_sequence(result, ledger, centerings, eps=EPS_DEFAULT,
                   min_hold=MIN_HOLD_DEFAULT):
    # type: (Dict[str, Any], Dict[str, Any], Any, float, int) -> List[str]
    """对 build_sequence 产物(或其篡改本)全量复核 R0-R7 + frontier。
    负控五组注入均经此入口判红。"""
    errs = []  # type: List[str]
    events = result.get("events", [])
    stone_ids = [s["id"] for s in ledger.get("stones", [])]
    cen_ids = [c["id"] for c in (centerings or [])]
    by_id = {s["id"]: s for s in ledger.get("stones", [])}
    cen_by_id = {c["id"]: c for c in (centerings or [])}
    zones = set(sid.split(".")[0] for sid in stone_ids)

    # R0: seq 连续 + 每石恰一次
    seqs = [e.get("seq") for e in events]
    if seqs != list(range(1, len(events) + 1)):
        errs.append("R0_SEQ 事件 seq 非从 1 起连续递增")
    stone_hits = {}  # type: Dict[str, int]
    for e in events:
        sid = e.get("stone_id")
        if sid is not None and e.get("etype") in E.MASONRY_TYPES:
            stone_hits[sid] = stone_hits.get(sid, 0) + 1
    for sid in stone_ids:
        n = stone_hits.get(sid, 0)
        if n != 1:
            errs.append("R0_STONE_ONCE 石 %s 出现 %d 次(应恰一次)" % (sid, n))
    for sid in stone_hits:
        if sid not in by_id:
            errs.append("R0_STONE_ONCE 事件引石 %s 不在石账" % sid)

    # R0: 每孔 CLOSE/DECENTER/CLEAR 恰一次(T3 覆盖类判据的生成侧闸)
    per_hole0 = {}  # type: Dict[str, Dict[str, int]]
    for e in events:
        zh = e.get("hole") or ""
        c0 = per_hole0.setdefault(zh, {})
        if e.get("etype") in ("CLOSE_RING", "DECENTER_START",
                              "CENTERING_CLEAR"):
            c0[e["etype"]] = c0.get(e["etype"], 0) + 1
    for zh, c0 in per_hole0.items():
        for etype, n in c0.items():
            if n > 1:
                errs.append("R0_HOLE_ONCE 孔 %s %s 出现 %d 次(应恰一次)"
                            % (zh, etype, n))

    # events.py 全量闸(交付硬约束: require_evidence=True)
    for msg in E.validate_event_ledger({"events": events}, cen_ids, stone_ids,
                                       min_hold=min_hold,
                                       require_evidence=True):
        errs.append("EVENTS " + msg)

    # 按孔索引事件
    by_hole = {}  # type: Dict[str, Dict[str, List[Dict[str, Any]]]]
    for e in events:
        by_hole.setdefault(e.get("hole") or "", {}).setdefault(
            e["etype"], []).append(e)

    for zone in sorted(by_hole):
        g = by_hole[zone]
        erects = g.get("HOLD_EVENT", [])
        closes = g.get("CLOSE_RING", [])
        decenter = sorted(g.get("DECENTER_START", []),
                          key=lambda e: e["seq"])
        wedges = sorted(g.get("WEDGE_RELEASE", []),
                        key=lambda e: e["seq"])
        clears = sorted(g.get("CENTERING_CLEAR", []),
                        key=lambda e: e["seq"])
        cen_id = "CEN-" + zone
        has_cen = cen_id in cen_by_id
        ring_places = sorted(
            (e for e in g.get("PLACE_STONE", [])
             if e.get("stone_id") and _role(e["stone_id"]) == RING_ROLE),
            key=lambda e: e["seq"])
        fill_places = sorted(
            (e for e in g.get("PLACE_STONE", [])
             if e.get("stone_id") and _role(e["stone_id"]) in FILL_ROLES),
            key=lambda e: e["seq"])
        impost_places = sorted(
            (e for e in g.get("PLACE_STONE", [])
             if e.get("stone_id") and _role(e["stone_id"]) in IMPOST_ROLES),
            key=lambda e: e["seq"])
        erect_seq = erects[0]["seq"] if erects else None
        close_seq = closes[0]["seq"] if closes else None
        dseq = decenter[0]["seq"] if decenter else None
        cseq = clears[0]["seq"] if clears else None

        # R1: 墩肩 z 升序
        zs = [_stone_xz(by_id[e["stone_id"]])[1] for e in impost_places
              if e.get("stone_id") in by_id]
        if any(zs[k + 1] < zs[k] - EXTRADOS_EPS for k in range(len(zs) - 1)):
            errs.append("R1_IMPOST_Z 墩肩石未按 z 升序: %s" % zone)

        # R2: 立架先行(有券架孔才核; 合成负控可无)
        if has_cen and ring_places:
            if erect_seq is None:
                errs.append("R2_NO_ERECT 孔 %s 无立架锚事件" % zone)
            else:
                if erects[0].get("stone_id") != cen_id:
                    errs.append("R2_ERECT_REF 立架事件未引用券架 %s" % cen_id)
                for e in ring_places:
                    if erect_seq not in (e.get("prereq") or []):
                        errs.append("R2_PREREQ 券石 %s prereq 缺立架 seq=%d"
                                    % (e.get("stone_id"), erect_seq))
                    if not (erect_seq < e["seq"] < (close_seq if close_seq
                                                    else e["seq"] + 1)):
                        errs.append("R2_WINDOW 券石 %s seq=%d 不在立架→合龙窗"
                                    % (e.get("stone_id"), e["seq"]))

        # R3: 前缀平衡度(偶数位前缀+收尾)
        _check_r3_events(errs, ring_places, by_id, zone, eps)

        # R4: λ 全阶 + HOLD 窗口归孔
        lam_seq = [w.get("load_lambda") for w in wedges]
        if lam_seq and lam_seq != list(LAMBDA_LADDER):
            errs.append("R4_LADDER 孔 %s λ 阶 %r ≠ %r"
                        % (zone, lam_seq, list(LAMBDA_LADDER)))
        if close_seq is not None and dseq is not None:
            n_hold = sum(1 for e in g.get("HOLD_EVENT", [])
                         if close_seq < e["seq"] < dseq
                         and e.get("stone_id") == cen_id)
            if n_hold < min_hold:
                errs.append("R4_HOLD 孔 %s CLOSE→DECENTER 窗口内本孔 HOLD %d "
                            "< min_hold=%d" % (zone, n_hold, min_hold))
        if clears and dseq is not None and clears[0]["seq"] < dseq:
            errs.append("R4_CLEAR_ORDER 孔 %s CLEAR 先于 DECENTER" % zone)

        # R5a/R5b: 分类与窗口
        if close_seq is not None and cseq is not None:
            idx = _arch_idx(zone) if zone.startswith("ARCH") else None
            if idx is not None:
                a = GM.SPANS[idx] / 2.0
                b = GM.arch_rise(idx)
                springer = GM.arch_springer_z(idx)
                xc = GM.arch_center_x(idx)
                ring_t = _hole_ring_t(by_id, zone)
                cen_boxes = (_centering_boxes_global(cen_by_id[cen_id])
                             if has_cen else [])
                for e in fill_places:
                    s = by_id.get(e["stone_id"])
                    if s is None:
                        continue
                    locked = s["params"].get("clipped_by") == "ring_band" \
                        or _is_lock_shoulder(
                            s, lambda gx: F.arch_z(gx - xc, 0.0, springer,
                                                   a, b) + ring_t,
                            cen_boxes)
                    if locked:
                        if not (close_seq < e["seq"] < cseq):
                            errs.append(
                                "R5A_WINDOW 锁固肩 %s seq=%d 不在合龙→拆架窗"
                                % (s["id"], e["seq"]))
                        if close_seq not in (e.get("prereq") or []):
                            errs.append("R5A_PREREQ 锁固肩 %s prereq 缺合龙"
                                        % s["id"])
                    else:
                        if e["seq"] < cseq:
                            errs.append("R5B_EARLY 肩背胞 %s seq=%d 先于拆架"
                                        % (s["id"], e["seq"]))

    # R6: frontier 组合表
    arch_zones = sorted(set(sid.split(".")[0] for sid in stone_ids
                            if sid.startswith("ARCH")))
    errs.extend(check_frontier(events, arch_zones))

    # R7: 面上最后 PAVING → RAIL/POST → CARVE
    errs.extend(_check_r7(events))
    return errs


def _hole_ring_t(by_id, zone):
    # type: (Dict[str, Dict[str, Any]], str) -> float
    for s in by_id.values():
        if s["id"].startswith(zone + ".") and _role(s["id"]) == RING_ROLE:
            return float(s["params"]["ring_t"])
    raise SequencerError("R5_NO_RING_T 孔 %s 无 RING 石 ring_t" % zone)


def _check_r3_events(errs, ring_places, by_id, zone, eps):
    # type: (List[str], List[Dict[str, Any]], Dict[str, Dict[str, Any]], str, float) -> None
    w_l = w_r = 0.0
    n = len(ring_places)
    for k, e in enumerate(ring_places):
        s = by_id.get(e.get("stone_id"))
        if s is None:
            errs.append("R3_STONE 孔 %s 券石 %s 不在石账" % (zone, e.get("stone_id")))
            continue
        w = stone_weight(s)
        lf = _theta_left_frac(s)
        w_l += w * lf
        w_r += w * (1.0 - lf)
        if (k + 1) % 2 == 0 or k + 1 == n:
            tot = w_l + w_r
            if tot > 0.0 and abs(w_l - w_r) / tot > eps:
                errs.append("R3_IMBALANCE 孔 %s 前缀 %d/%d 平衡度 %.4f > %.3f"
                            % (zone, k + 1, n, abs(w_l - w_r) / tot, eps))


def _check_r7(events):
    # type: (List[Dict[str, Any]]) -> List[str]
    errs = []  # type: List[str]
    group_last = {}  # type: Dict[str, int]
    group_first = {}  # type: Dict[str, int]
    arch_last = 0
    for e in events:
        sid = e.get("stone_id")
        if e.get("etype") != "PLACE_STONE" or not isinstance(sid, str) \
                or sid.count(".") < 3:
            continue  # 只核砌筑置放; HOLD/CLOSE 引 CEN id 不参与
        role = _role(sid)
        if role in R7_PAVING:
            g = "PAVING"
        elif role in R7_RAIL_POST:
            g = "RAIL_POST"
        elif role in R7_CARVE:
            g = "CARVE"
        else:
            arch_last = max(arch_last, e["seq"])
            continue
        group_first.setdefault(g, e["seq"])
        group_last[g] = e["seq"]
    order = [g for g in R7_ORDER if g in group_first]
    if order != [g for g in R7_ORDER if g in group_last]:
        errs.append("R7_ORDER R7 组缺失/乱序: %r" % order)
    for ga, gb in zip(order, order[1:]):
        if group_last[ga] >= group_first[gb]:
            errs.append("R7_ORDER %s(尾 %d) 未先于 %s(首 %d)"
                        % (ga, group_last[ga], gb, group_first[gb]))
    if order and arch_last and group_first[order[0]] <= arch_last:
        errs.append("R7_LAST R7 首事件 seq=%d 未排在主体(%d)之后"
                    % (group_first[order[0]], arch_last))
    return errs


# ---------------------------------------------------------------------------
# frontier 状态机(R6)
# ---------------------------------------------------------------------------

def derive_frontier(events):
    # type: (List[Dict[str, Any]]) -> List[Dict[str, Any]]
    """从事件流重建 frontier 轨迹(与构造轨迹同形; 篡改本经此入核)。"""
    trace = []
    per_hole = {}  # type: Dict[str, Dict[str, List[Dict[str, Any]]]]
    for e in events:
        per_hole.setdefault(e.get("hole") or "", {}).setdefault(
            e["etype"], []).append(e)
    for zone in sorted(per_hole):
        g = per_hole[zone]
        closes = sorted(g.get("CLOSE_RING", []), key=lambda e: e["seq"])
        holds = sorted(g.get("HOLD_EVENT", []), key=lambda e: e["seq"])
        dstarts = sorted(g.get("DECENTER_START", []), key=lambda e: e["seq"])
        clears = sorted(g.get("CENTERING_CLEAR", []), key=lambda e: e["seq"])
        fill_last = None
        cen_id = "CEN-" + zone
        for e in g.get("PLACE_STONE", []):
            sid = e.get("stone_id") or ""
            if _role(sid) in FILL_ROLES:
                if fill_last is None or e["seq"] > fill_last:
                    fill_last = e["seq"]
        if closes:
            trace.append({"hole": zone, "state": "RING_CLOSED",
                          "at_seq": closes[0]["seq"]})
            window = [h for h in holds
                      if closes[0]["seq"] < h["seq"]
                      and (not dstarts or h["seq"] < dstarts[0]["seq"])]
            if window:
                trace.append({"hole": zone, "state": "CLOSED_SUPPORTED",
                              "at_seq": window[-1]["seq"]})
        if dstarts:
            trace.append({"hole": zone, "state": "DECENTERING",
                          "at_seq": dstarts[0]["seq"]})
        if clears:
            trace.append({"hole": zone, "state": "CLEARED",
                          "at_seq": clears[0]["seq"]})
        if fill_last is not None:
            trace.append({"hole": zone, "state": "FILLED",
                          "at_seq": fill_last})
    return sorted(trace, key=lambda t: (t["at_seq"], t["hole"]))


def check_frontier(events, zones):
    # type: (List[Dict[str, Any]], List[str]) -> List[str]
    """R6 跨孔组合表核(对任意事件流): 逐转移推进状态向量, 禁
    相邻孔同 DECENTERING / 孔 i DECENTERING 而 i±1 < CLOSED_SUPPORTED。
    zones 必须传全孔表(石账 ARCH zone 全集)——无任何转移的 UNBUILT 孔也要
    参与邻接判, 否则跳孔落架会从空档孔漏过。"""
    errs = []  # type: List[str]
    trace = derive_frontier(events)
    zones = sorted(zones)
    rank_of = {z: i for i, z in enumerate(zones)}
    state = {z: "UNBUILT" for z in zones}
    prev_at = None
    for t in trace:
        z, st, at = t["hole"], t["state"], t["at_seq"]
        if _STATE_RANK[st] <= _STATE_RANK[state[z]]:
            errs.append("R6_STATE_ORDER 孔 %s 状态 %s 未严格前进而重放为 %s "
                        "(seq=%s)" % (z, state[z], st, at))
            continue
        state[z] = st
        if prev_at is not None and at < prev_at:
            errs.append("R6_SEQ_ORDER 轨迹 seq 回退: %s@%s" % (z, at))
        prev_at = at
        i = rank_of[z]
        for j in (i - 1, i + 1):
            if not (0 <= j < len(zones)):
                continue
            nz = zones[j]
            nrank = _STATE_RANK[state[nz]]
            if st == "DECENTERING":
                if state[nz] == "DECENTERING":
                    errs.append("R6_ADJ_DECENTERING 相邻孔 %s/%s 同落架 "
                                "(seq=%s)" % (z, nz, at))
                elif nrank < _STATE_RANK["CLOSED_SUPPORTED"]:
                    errs.append(
                        "R6_JUMP_DECENTER 孔 %s 落架时邻孔 %s 状态 %s "
                        "< CLOSED_SUPPORTED(跳孔落架, seq=%s)"
                        % (z, nz, state[nz], at))
    return errs


# ---------------------------------------------------------------------------
# 石账支撑曲线回写(副本; 原 ledger 永不改动)
# ---------------------------------------------------------------------------

def apply_support_edges(ledger, result):
    # type: (Dict[str, Any], Dict[str, Any]) -> Dict[str, Any]
    """深拷贝 ledger 并按 _edge_plan 回写 support_edges(替换; 真账原为空)。
    返回副本; 调用方自行 L.save_ledger 到 out/ledger_sequenced.json。"""
    out = copy.deepcopy(ledger)
    plan = result.get("_edge_plan", {})
    for s in out.get("stones", []):
        edges = plan.get(s.get("id"))
        if edges is not None:
            s["support_edges"] = copy.deepcopy(edges)
    return out


# ---------------------------------------------------------------------------
# CLI: 真账全链
# ---------------------------------------------------------------------------

_HERE = os.path.dirname(os.path.abspath(__file__))
_LEDGER_PATH = os.environ.get("E30_LEDGER_PATH") or os.path.join(
    _HERE, "out", "ledger_full.json")
_OUT_DIR = os.path.join(_HERE, "out")


def main():
    led = L.load_ledger(_LEDGER_PATH)
    zones = sorted(set(s["id"].split(".")[0] for s in led["stones"]))
    centerings = [CEN.build_centering_for_arch(_arch_idx(z)) for z in zones
                  if z.startswith("ARCH")]
    res = build_sequence(led, centerings)
    errs = check_sequence(res, led, centerings)
    if errs:
        for m in errs[:40]:
            print("ERR", m)
        print("check_sequence: %d 违例" % len(errs))
        return 1
    led2 = apply_support_edges(led, res)
    errs2 = L.validate_ledger(led2, allow_clearance=False,
                              known_event_seqs=E.event_seqs(res))
    if errs2:
        for m in errs2[:40]:
            print("ERR LEDGER", m)
        print("ledger_sequenced validate: %d 违例" % len(errs2))
        return 1
    if not os.path.isdir(_OUT_DIR):
        os.makedirs(_OUT_DIR)
    L.save_ledger(led2, os.path.join(_OUT_DIR, "ledger_sequenced.json"))
    seq_out = {k: res[k] for k in ("events", "sequence", "frontier_trace",
                                   "meta")}
    with open(os.path.join(_OUT_DIR, "sequence.json"), "w",
              encoding="utf-8") as f:
        json.dump(seq_out, f, ensure_ascii=False, indent=1, sort_keys=True)
    n_stage = len(res["sequence"])
    print("OK stones=%d events=%d stages=%d trace=%d holes=%d"
          % (res["meta"]["n_stones"], res["meta"]["n_events"], n_stage,
             len(res["frontier_trace"]), len(res["meta"]["hole_order"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
