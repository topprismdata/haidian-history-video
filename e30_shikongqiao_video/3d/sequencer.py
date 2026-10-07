# e30_shikongqiao_video/3d/sequencer.py
# -*- coding: utf-8 -*-
"""P2-T4 建造序列器: R0-R7 规则引擎 + frontier 状态机 → 事件流 + stage 分组。

输入: 石账(ledger v2, 5935 真源只读) + 券架表(centering.build_centering_for_arch)。
输出: {"events", "sequence", "frontier_trace", "meta"}; 券石支撑曲线回写石账
**副本** out/ledger_sequenced.json(原 ledger_full.json 永不改动)。

幻影石过滤(P2-T4 修复轮 裁1): sequencer 消费 build_scene2.classify_stones
(blender-free 纯逻辑段, 与 out/print/excluded_ids.json 同源)取 in_void 桶 ——
整块落在券洞净空内的石是画出来的"幻影石", 不生成 PLACE_STONE 事件、不写
支撑边; void_cut_fragment/ring_band_overlap/thin_merge 保留(真实裁石在墙里,
带裁片是真实砌体)。被滤石集合与 excluded_ids.json["in_void"] 逐位相等
(test_real_ledger_fullchain 交叉核)。

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
- R5a 环肩锁固(P2-T6 裁决收缩): 环肩咬合石(params.clipped_by=="ring_band")
  与下部锁固肩(判据: 石底 z ≤ 该孔 extrados[facts.arch_z+params.ring_t]
  ∧ 足印距 extrados 面 ≤LOCK_BAND_M —— 径向距, facts.arch_signed_r 单源,
  竖直 z 距在陡肩段(斜率~9)把切向偏移放大成假深度 ∧ 石 bbox 与券架
  parts bbox[全局系] 无碰撞), 且**剔除双建模占位**(_double_model_ids:
  rbo 桶逐石 V(stone∩RING∪)/V(stone) ≥ DM_SWALLOW_THRESHOLD 者 → R5b;
  其重量 ≥98.5% 已在 RING 实体内, R5a 再计即双算)。排 CLOSE 后
  **DECENTER_START 前**(修复轮 checker 收紧: 上界原为 CLEAR, 落架中途
  不得砌肩 —— T5 需"锁固后才落架"), prereq ⊇ {合龙 seq}。
- R5b 其余肩背胞: 其余 SPANDREL/BACK/CORE 排 CENTERING_CLEAR 后。
- R6 frontier 状态机: 孔状态 UNBUILT < RING_CLOSED < CLOSED_SUPPORTED <
  DECENTERING < CLEARED < FILLED; 跨孔组合表禁: 跳孔落架(孔 i
  DECENTERING 而 i±1 < CLOSED_SUPPORTED); 相邻孔同落架须**对内同档**
  (任一落架事件时两侧 λ 差 ≤ 一档 —— 主控 2026-10-07 裁决采纳多孔连拱
  "对称同步卸落": 波2 改全桥同波逐档, 每档全部孔 WEDGE_RELEASE 同 stage
  同档, 档差=0; 乱序同落架/单孔连升多档仍红。逐孔串行在 G3④墩不平衡门
  不可行, 顺序邻孔对有对间过渡残红, 见 p2-task-7-report.md §8)。
  组合表只要求**前视 1**: 落架孔的任一邻孔 ≥ CLOSED_SUPPORTED 即可 ——
  两波日程并非逻辑必然, 是 v1 的策略选择; 前视-1 的流水列同样满足
  组合表, 列为 P3 叙事可选项。
- R7 面上最后: PAVING → RAIL/POST → CARVE 全局收尾(真账 5935 石暂无此四角色,
  形制就绪; 合成账钉测试)。

石账支撑曲线回写(回写副本, 石账纯度红线: 券架/事件不进石账)。
**capacity 语义(修复轮 裁2): 荷载分担份额(load share), 非"剩余能力"** ——
curve 值回答"此时刻该支撑体分担这块石荷载的份额", 不变量: 任意事件点
Σ(各边 capacity) ≥ 1(任一时刻石的总荷载始终被完整分担; T5 g3_check 将作
验收断言, 本文件测试先钉)。注意 stone 边份额随砌体自持能力**上升**是
分担语义下的合法形状(ledger 侧 CURVE_MONOTONIC 仅约束退化型边)。
- IMPOST/PIER: foundation 边 [[place,1.0]](墩台直接承托)。
- RING: centering 边 1−λ 阶梯 [[place,1.0],[DECENTER,1.0],[W1,0.75],
  [W2,0.5],[W3,0.25],[W4,0.0],[CLEAR,0.0]] + stone 自持边 λ 阶梯
  [[place,0.0],[DECENTER,0.0],[W1,0.25],[W2,0.5],[W3,0.75],[W4,1.0],
  [CLEAR,1.0]](同点互补, 每事件点 Σ=1)。
- R5a 锁固肩: 仅 stone 自持边 [[place,1.0]](修复轮: 删 centering 边 ——
  R5a 判据已保证不撞券架, 肩石坐已成环砌体而非木架, 从落座起自持)。
- 其余(R5b): stone 边 [[place,1.0]]。
全部 curve x 均为真实事件 seq(E.event_seqs 交叉核)。

史料引用(construction_history.md 编号, GRADES=inferred——序列细节靠通例+实物
反推, C:A3 明示则例无工序教科书): 立架/落架/拆架=C:A3/B14; 券石=C:A2/B14;
合龙/持荷=B14; 撞券石=C:A2; 背胞fill=C:A1; R7=C:A1。

Python 3.9.6 纯 stdlib, blender-free; 几何禁第二套公式(消费 geom_math/facts)。
例外: _double_model_ids 在 rbo 桶∩账非空时延迟 import numpy+p1a_slice
(blender-free 段, P1 体素度量单源) —— 合成账交集空, 快速返回零依赖。
"""
import copy
import json
import os
from typing import Any, Dict, List, Optional, Set

import ledger as L
import events as E
import centering as CEN
import geom_math as GM
import facts as F
import families as FAM
import export_print as EP
import build_scene2 as BS2   # blender-free 纯逻辑段(classify_stones); 裁1 单源

EPS_DEFAULT = 0.15          # [工程参数·敏感性] R3 平衡度阈
MIN_HOLD_DEFAULT = E.MIN_HOLD_DEFAULT
LAMBDA_LADDER = (0.25, 0.5, 0.75, 1.0)   # λ 档全走(spec 1/4 步进)
STONE_DENSITY = 1.0         # R3 比值对共同密度不变, 不发明无出处常数[三红线]
PAIR_MIRROR_TOL = 1e-6      # θ 镜像配对容差(度)
EXTRADOS_EPS = 1e-9         # z 比较浮点容差
# [P2-T6 裁决·两层] R5a 收缩为真锁固带: 足印距 extrados 面 ≤0.35m(径向) 且
# 剔除双建模占位(0.985 吞没口径 28 石)。0.35 是唯一声明带宽, 不为绿而调。
LOCK_BAND_M = 0.35
DM_SWALLOW_THRESHOLD = 0.985

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


def stone_weight(stone, density=None):
    # type: (Dict[str, Any], Optional[float]) -> float
    """石重=体积×密度。体积单源(修复轮 F5): RING=族网格散度体积
    (families.family_mesh + export_print.signed_volume 现算, 按
    孔+块型缓存); CORE= params.bbox 直积; 其余=w×h×d 断面矩形[估计]。
    density=None 时取模块常量 STONE_DENSITY(调用时读, 供密度不变量
    测试整体换密度重建)。"""
    if density is None:
        density = STONE_DENSITY
    p = stone.get("params", {}) or {}
    role = _role(stone.get("id", ""))
    if role == "CORE" and isinstance(p.get("bbox"), dict):
        bb = p["bbox"]
        vol = ((bb["x1"] - bb["x0"]) * (bb["y1"] - bb["y0"])
               * (bb["z1"] - bb["z0"]))
    elif role == RING_ROLE:
        vol = _ring_stone_volume(stone)
    else:
        w = p.get("w", 0.0)
        h = p.get("h", 0.0)
        d = p.get("d", 0.0)
        vol = float(w) * float(h) * float(d)
    return vol * density


_MESH_VOL_CACHE = {}  # type: Dict[Any, float]


def _ring_stone_volume(stone):
    # type: (Dict[str, Any]) -> float
    """券石体积=族网格散度体积绝对值(flip_outward 归一后内翻为负, 物理
    体积取 |V|)。F5 硬约束: 不再有第二套环带近似公式 —— 与导出/打印链
    同一 families.family_mesh 单源。按 (孔, family, params 全量指纹) 缓存,
    同孔同块型(参数逐位同)只积分一次, 防 6000 石全链反复积分。"""
    p = stone.get("params") or {}
    sid = stone.get("id", "")
    key = (sid.split(".")[0], stone.get("family"),
           json.dumps(p, sort_keys=True))
    vol = _MESH_VOL_CACHE.get(key)
    if vol is None:
        verts, faces = FAM.family_mesh(stone["family"], p)
        vol = abs(EP.signed_volume(verts, faces))
        _MESH_VOL_CACHE[key] = vol
    return vol


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
    """占位冲突 bbox(修复轮 F5: RING 分派已删 —— 券石占位由族网格承担,
    不再保留 stations 近似第二套; 本函数仅服务 FILL 角色锁固判)。
    """
    role = _role(stone.get("id", ""))
    if role == "CORE":
        return _slab_box(stone)
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
# 幻影石过滤(裁1)与构造
# ---------------------------------------------------------------------------

def _in_void_ids(ledger):
    # type: (Dict[str, Any]) -> set
    """裁1: build_scene2.classify_stones(blender-free 纯逻辑段, 与
    out/print/excluded_ids.json 同源)取 in_void 桶 id 全集。传代理浅拷贝
    (params dict 单独复制) —— classify_stones 会给 clip 石打 params["clipped"]
    标, 石账入参在此必须保持未被污染(纯度红线)。"""
    proxies = [dict(s, params=dict(s.get("params") or {}))
               for s in ledger.get("stones", [])]
    cls = BS2.classify_stones(proxies)
    return set(sid for sid, (status, _polys) in cls.items()
               if status == "inside")


def _hole_of(stone):
    # type: (Dict[str, Any]) -> str
    return stone["id"].split(".")[0]


def _double_model_ids(ledger, rbo_ids=None, threshold=DM_SWALLOW_THRESHOLD):
    # type: (Dict[str, Any], Optional[List[str]], float) -> set
    """P2-T6 裁决·双建模占位剔除 id 集(= _double_model_ratios 的键集;
    实现说明见该函数 docstring)。"""
    return set(_double_model_ratios(ledger, rbo_ids=rbo_ids,
                                    threshold=threshold))


def _double_model_ratios(ledger, rbo_ids=None, threshold=DM_SWALLOW_THRESHOLD):
    # type: (Dict[str, Any], Optional[List[str]], float) -> Dict[str, float]
    """P2-T6 裁决·双建模占位剔除(带吞没率版): rbo 桶(ring_band_overlap)中
    V(stone∩RING∪)/V(stone) ≥ threshold(0.985 口径, 真账 29 石)者 ——
    它们 ≥98.5% 已被 RING 实体吞没, 重量在压力线模型里属 RING 已计部分,
    R5a 再计即双算 → 剔出 R5a 落 R5b。返回 {stone_id: 吞没率}(供
    sequence.json meta 落盘 id+吞没率清单, 幂等可 diff —— 审查 INFO:
    只落计数则归因可核对性缺口, §7.1 全表只能靠正文)。

    为何不 import g3_check 复用其 double_model_scan: g3 与本模块是两独立
    实现互证(测试钉死 g3 导入闭包无 sequencer), 反向依赖成环; 故按同一
    P1 度量单源(p1a_slice._voxel_unique_vol, 2cm 栅格, bbox 预筛,
    pre-inset)自实现同法扫描 —— 度量单源不变, 实现各自独立, 结果互证。

    rbo_ids=None 时读 out/print/excluded_ids.json 的 ring_band_overlap 桶;
    桶空或与账交集空(合成账) → 空集, 不触重依赖。交集非空而
    numpy/p1a_slice 缺失 → raise(度量无单源即拒绝出数, 不静默放空)。"""
    if rbo_ids is None:
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "out", "print", "excluded_ids.json")
        rbo_ids = []
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                rbo_ids = list(json.load(f).get("buckets", {})
                               .get("ring_band_overlap", []))
    by_id = {s["id"]: s for s in ledger.get("stones", [])}
    todo = sorted({sid for sid in (rbo_ids or ()) if sid in by_id})
    if not todo:
        return set()
    import numpy as np  # 延迟重依赖: 仅真账扫描需要
    import p1a_slice as P
    rings_by_zone = {}  # type: Dict[str, List[str]]
    for s in ledger.get("stones", []):
        if _role(s.get("id", "")) == RING_ROLE:
            rings_by_zone.setdefault(s["id"].split(".")[0], []).append(s["id"])
    mesh_cache = {}  # type: Dict[str, Any]

    def ring_mesh(rid):
        # type: (str) -> Any
        if rid not in mesh_cache:
            rv, rf = P.world_mesh(by_id[rid], {rid: ("out", None)})
            rv = np.asarray(rv, dtype=float)
            tris = P._flat_tris(P.PC._face_tris(rv, rf))
            mesh_cache[rid] = (rv, tris, rv.min(axis=0), rv.max(axis=0))
        return mesh_cache[rid]

    out = {}  # type: Dict[str, float]
    for sid in todo:
        st = by_id[sid]
        sv, sf = P.world_mesh(st, {sid: ("out", None)})
        SV = np.asarray(sv, dtype=float)
        lo, hi = SV.min(axis=0), SV.max(axis=0)
        rms = []
        for rid in rings_by_zone.get(sid.split(".")[0], ()):
            rv, tris, rlo, rhi = ring_mesh(rid)
            if bool((rlo <= hi + 1e-9).all() and (rhi >= lo - 1e-9).all()):
                rms.append((rv, tris))
        v_stone, _v_hit, v_unique, _inside = P._voxel_unique_vol(sv, sf, rms)
        ratio = (1.0 - v_unique / v_stone) if v_stone > 0 else 0.0
        if ratio >= threshold:
            out[sid] = float(ratio)
    return out


def _arch_idx(zone):
    # type: (str) -> int
    return int(zone[4:]) - 1


def build_sequence(ledger, centerings, eps=EPS_DEFAULT,
                   min_hold=MIN_HOLD_DEFAULT, ring_order=None, dm_ids=None):
    # type: (Dict[str, Any], Any, float, int, Optional[Dict[str, List[str]]], Optional[Set[str]]) -> Dict[str, Any]
    """规则引擎主入口。ring_order: {zone: [ring stone id 顺序]} 可选显式券石
    顺序(负控注入位); None=按 θ 镜像配对自动派生。自检失败 raise SequencerError。
    裁1: in_void 幻影石(classify_stones 单源)不入日程。min_hold 必须 ≥1
    (F4: 0=免持荷 fail-open, 构造器拒绝)。
    dm_ids: 双建模占位 id 集(None=按裁决阈值自扫, 真账 ~26s; 显式传空
    set() 跳过) —— P2-T6 裁决第 2 闸, 集合内 FILL 石剔出 R5a 落 R5b
    (其重量 ≥98.5% 已在 RING 实体内, 二次计荷即双算)。
    """
    if int(min_hold) < 1:
        raise SequencerError(
            "R4_MIN_HOLD min_hold=%r 必须 ≥1: 0 持荷=合龙即落架, fail-open 禁止"
            % (min_hold,))
    stones_all = ledger.get("stones", [])
    # R0 fail-closed 先行: id 缺失/重复/角色未登记优先报 —— 不被幻影石
    # 分类的几何错误遮蔽(未知角色石可能连 family_mesh 都进不去)。
    _seen_ids = set()
    for s in stones_all:
        sid = s.get("id", "")
        if not sid:
            raise SequencerError("R0_NO_ID 石记录缺 id")
        if sid in _seen_ids:
            raise SequencerError("R0_DUP_STONE 石 id 重复: %s" % sid)
        _seen_ids.add(sid)
        if _role(sid) not in KNOW_ROLES:
            raise SequencerError("R0_UNKNOWN_ROLE 石 %s 角色未登记: %s"
                                 % (sid, _role(sid)))
    in_void = _in_void_ids(ledger)
    if dm_ids is None:
        dm_ids = _double_model_ids(ledger)
    else:
        dm_ids = set(dm_ids)
    stones = [s for s in stones_all if s["id"] not in in_void]
    dm_hit = sum(1 for s in stones
                 if s["id"] in dm_ids and _role(s["id"]) in FILL_ROLES)
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

    # 两波推进(裁3 改写: R6 组合表只要求前视 1 —— 孔 i 落架时邻孔 i±1 须
    # ≥ CLOSED_SUPPORTED。两波并非逻辑必然, 是 v1 日程的策略选择: 任一时刻
    # 全部孔位同相, 快照面简单、叙事清晰。前视-1 的流水列(砌孔 i+1 与落架
    # 孔 i 交错)同样满足组合表, 列为 P3 叙事可选项。顺序均按孔号升序。)
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

        def band_dist(gx, gz):
            # 足印到 extrados 面的径向距离(facts.arch_signed_r 单源;
            # 竖直 z 距在陡肩段把切向偏移放大成假深度, 项目 discipline 用径向)
            return F.arch_signed_r(gx, gz, xc, springer, a, b) - ring_t

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

        # -- R5a: 环肩锁固(合龙后 CLEAR 前; P2-T6 裁决: 带闸+占位剔除) --
        shoulders = []
        n_dm_hole = 0
        for s in holes[zone]:
            if _role(s["id"]) not in FILL_ROLES:
                continue
            if s["id"] in dm_ids:
                n_dm_hole += 1
                continue
            if s["params"].get("clipped_by") == "ring_band" \
                    or _is_lock_shoulder(s, extrados_z, cen_boxes, band_dist):
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
                     for _ in range(int(min_hold))]
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
            "n_dm_hole": n_dm_hole,
            "n_fill": len(rest),
        }

    # -- 波2: 全桥对称同步落架(主控 2026-10-07 裁决: 多孔连拱"对称同步
    #    卸落"工法; 逐孔串行在 G3④墩不平衡门不可行, 顺序邻孔对亦有对间
    #    过渡残红 —— 探针见 p2-task-7-report.md §8)。档差=0: 每档全部孔
    #    WEDGE_RELEASE 同 stage 同档(每对邻孔同 λ, 不平衡=λ·|Hmin_A−Hmin_B|,
    #    相似跨≈0); λ 全阶后统一拆架, 再逐孔填筑肩背(R5b, 依赖各自 CLEAR)。
    prev_stage = stages[-1]["id"] if stages else None
    st = open_stage("DECENTER.DSTART.WAVE", evidence=EV_CEN)
    lo = len(events) + 1
    dseq_by = {}       # type: Dict[str, int]
    wedge_by = {}      # type: Dict[str, List[int]]
    for zone in zones_sorted:
        w1 = wave1[zone]
        dseq_by[zone] = emit(zone, "DECENTER_START", stone_id=w1["cen"]["id"],
                             prereq=[w1["close_seq"]] + w1["hold_seqs"],
                             evidence=EV_CEN)
        trace.append({"hole": zone, "state": "DECENTERING",
                      "at_seq": dseq_by[zone]})
        wedge_by[zone] = []
    close_stage(st, lo, len(events), [prev_stage])
    prev_stage = st["id"]
    for k, lam in enumerate(LAMBDA_LADDER):
        st = open_stage("DECENTER.WEDGE.%s.L%02d" % (k + 1, round(lam * 100)),
                        evidence=EV_CEN)
        lo = len(events) + 1
        for zone in zones_sorted:
            ws = wedge_by[zone]
            ws.append(emit(zone, "WEDGE_RELEASE",
                           stone_id=wave1[zone]["cen"]["id"],
                           prereq=[dseq_by[zone]] + ws,
                           load_lambda=float(lam), evidence=EV_CEN))
        close_stage(st, lo, len(events), [prev_stage])
        prev_stage = st["id"]
    st = open_stage("DECENTER.CLEAR.WAVE", evidence=EV_CEN)
    lo = len(events) + 1
    cseq_by = {}       # type: Dict[str, int]
    for zone in zones_sorted:
        ws = wedge_by[zone]
        cseq_by[zone] = emit(zone, "CENTERING_CLEAR",
                             stone_id=wave1[zone]["cen"]["id"],
                             prereq=[dseq_by[zone], ws[-1]] if ws
                             else [dseq_by[zone]],
                             evidence=EV_CEN)
        trace.append({"hole": zone, "state": "CLEARED", "at_seq": cseq_by[zone]})
    close_stage(st, lo, len(events), [prev_stage])
    prev_stage = st["id"]

    # 支撑曲线回写(裁2: capacity=荷载分担份额, 任意事件点 Σcapacity≥1)
    for zone in zones_sorted:
        w1 = wave1[zone]
        for s in w1["ring_stones"]:
            edge_plan[s["id"]] = _ring_support_edges(
                w1["ring_seq_by_stone"][s["id"]], wedge_by[zone],
                dseq_by[zone], cseq_by[zone])
        for s in w1["shoulders"]:
            # R5a 锁固肩: 只留 stone 自持边 1.0 全程(不坐木架, 落座即自持)
            edge_plan[s["id"]] = [{"type": "stone",
                                   "capacity_curve":
                                       [[_shoulder_place_seq(events, s["id"]),
                                         1.0]]}]

    # -- R5b: 其余肩背胞(各自 CLEAR 后; 全桥同波落架完毕再逐孔填筑),
    #    z_bottom 升序; 单阶段一孔一拍(13 层/孔会把 stage 数顶破 600 目标,
    #    叙事上"填筑肩背"为一拍) F4: 无肩背胞可填的孔不发 FILL 阶段、
    #    不记 FILLED(与 derive_frontier 同形); at_seq=本孔末个置放事件 --
    for zone in zones_sorted:
        w1 = wave1[zone]
        cseq = cseq_by[zone]
        rest = w1["rest"]
        if rest:
            st = open_stage("%s.FILL" % zone, evidence=EV_FILL)
            lo = len(events) + 1
            pseq = lo - 1
            for s in rest:
                pseq = emit(zone, "PLACE_STONE", stone_id=s["id"],
                            prereq=[cseq], evidence=EV_FILL)
                edge_plan[s["id"]] = [{"type": "stone",
                                       "capacity_curve": [[pseq, 1.0]]}]
            close_stage(st, lo, len(events), [prev_stage])
            prev_stage = st["id"]
            trace.append({"hole": zone, "state": "FILLED",
                          "at_seq": pseq})
        hole_report.append({"zone": zone, "centering": w1["cen"]["id"],
                            "n_ring": w1["n_ring"],
                            "n_shoulder": w1["n_shoulder"],
                            "n_dm_excluded": w1["n_dm_hole"],
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
            "n_stones_ledger": len(ledger.get("stones", [])),
            "n_stones_in_void": len(in_void),
            "n_dm_excluded": dm_hit,
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


def _is_lock_shoulder(stone, extrados_z, cen_boxes, band_dist):
    # type: (Dict[str, Any], Any, List[tuple], Any) -> bool
    """R5a 下部锁固肩判据(P2-T6 裁决收缩): 石底 z ≤ 该孔 extrados 区 ∧
    足印距 extrados 面 ≤ LOCK_BAND_M(径向, band_dist(x,z)=
    facts.arch_signed_r−ring_t; 竖直 z 距在陡肩段(斜率~9)把切向偏移放大
    成假深度 —— 实测竖直读法会拆掉拱脚稳定配重, ARCH05/13 翻不可行)
    ∧ 石 bbox 与券架占位无碰撞。"""
    x_mid, z_bottom, _zm = _stone_xz(stone)
    if z_bottom > extrados_z(x_mid) + EXTRADOS_EPS:
        return False
    if band_dist(x_mid, z_bottom) > LOCK_BAND_M + EXTRADOS_EPS:
        return False
    sb = _stone_box(stone)
    return not any(_boxes_collide(sb, cb) for cb in cen_boxes)


def _ring_support_edges(place_seq, wedge_seqs, dseq, cseq):
    # type: (int, List[int], Optional[int], Optional[int]) -> List[Dict[str, Any]]
    """RING 石支撑边(裁2): capacity=荷载分担份额。centering 边 1−λ 阶梯
    (1.0→0.75→0.5→0.25→0 于各 WEDGE_RELEASE, CLEAR=0) + stone 自持边 λ
    阶梯(0→0.25→0.5→0.75→1.0 同点)。两曲线同点互补, 任意事件点
    Σcapacity = 1 ≥ 1(卸载的同时砌体弧圈等量接管, 任一时刻总荷载完整
    被分担)。x 全为真实事件 seq。"""
    lam = [float(v) for v in LAMBDA_LADDER[:len(wedge_seqs)]]
    cen = [[place_seq, 1.0]]
    stn = [[place_seq, 0.0]]
    if dseq is not None:
        cen.append([dseq, 1.0])
        stn.append([dseq, 0.0])
    for k, ws in enumerate(wedge_seqs):
        cen.append([ws, 1.0 - lam[k]])
        stn.append([ws, lam[k]])
    if cseq is not None:
        cen.append([cseq, 0.0])
        stn.append([cseq, 1.0])
    return [
        {"type": "centering", "capacity_curve": cen},
        {"type": "stone", "capacity_curve": stn},
    ]


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
                   min_hold=MIN_HOLD_DEFAULT, dm_ids=None):
    # type: (Dict[str, Any], Any, Any, float, int, Optional[Set[str]]) -> List[str]
    """对 build_sequence 产物(或其篡改本)全量复核 R0-R7 + frontier。
    负控五组注入均经此入口判红。裁1: R0 恰一次核只对**入日程石**成立
    (in_void 幻影石按 classify_stones 同一单源重算, 且任何事件引用幻影石
    即 R0_IN_VOID_PHANTOM); result 带 _edge_plan 时加核 Σcapacity≥1 不变量
    (裁2, 采样点=每石自身 curve knot ∪ 本孔全部事件 seq, 分段线性下端点
    覆盖即全程覆盖)。dm_ids: 双建模占位集(None=按裁决阈值重算 —— 篡改
    防御默认; 与 build_sequence 传同一集可省一次扫描)。
    R5a 分类镜像与构造器同判据(带闸+占位剔除): 占位石/带外深肩石被排进
    合龙→落架窗 → R5A_WINDOW 必红(占位石混入 R5a 荷载的负控入口)。"""
    errs = []  # type: List[str]
    if int(min_hold) < 1:
        errs.append("R4_MIN_HOLD min_hold=%r 必须 ≥1(与构造器同闸, fail-open "
                    "禁止)" % (min_hold,))
    events = result.get("events", [])
    in_void = _in_void_ids(ledger)
    if dm_ids is None:
        dm_ids = _double_model_ids(ledger)
    else:
        dm_ids = set(dm_ids)
    stone_ids = [s["id"] for s in ledger.get("stones", [])
                 if s["id"] not in in_void]
    cen_ids = [c["id"] for c in (centerings or [])]
    by_id = {s["id"]: s for s in ledger.get("stones", [])}
    cen_by_id = {c["id"]: c for c in (centerings or [])}
    zones = set(sid.split(".")[0] for sid in stone_ids)

    # 裁1: 幻影石任何形态出现在事件流即红(含非砌筑事件引用)
    for e in events:
        sid = e.get("stone_id")
        if sid in in_void:
            errs.append("R0_IN_VOID_PHANTOM 石 %s 属 in_void 桶却出现在事件 "
                        "seq=%s(%s)" % (sid, e.get("seq"), e.get("etype")))

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
                    locked = s["id"] not in dm_ids and (
                        s["params"].get("clipped_by") == "ring_band"
                        or _is_lock_shoulder(
                            s,
                            lambda gx: F.arch_z(gx - xc, 0.0, springer,
                                                a, b) + ring_t,
                            cen_boxes,
                            lambda gx, gz: F.arch_signed_r(gx, gz, xc,
                                                           springer,
                                                           a, b) - ring_t))
                    if locked:
                        # 修复轮收紧: 上界 CLEAR → DECENTER_START(落架中途
                        # 不得砌肩; T5 需"锁固后才落架")。负控: 肩石挪入
                        # DECENTER→CLEAR 窗必红。
                        upper = dseq if dseq is not None else cseq
                        if not (close_seq < e["seq"] < upper):
                            errs.append(
                                "R5A_WINDOW 锁固肩 %s seq=%d 不在合龙→落架窗"
                                "(落架中途不得砌肩)" % (s["id"], e["seq"]))
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

    # 裁2: Σcapacity≥1 不变量(result 带 _edge_plan 时; 篡改本注入点)
    edge_plan = result.get("_edge_plan")
    if edge_plan:
        errs.extend(_check_capacity_invariant(edge_plan, events))
    return errs


def _check_capacity_invariant(edge_plan, events):
    # type: (Dict[str, List[Dict[str, Any]]], List[Dict[str, Any]]) -> List[str]
    """裁2 不变量: 任意事件点 Σ(各边 capacity) ≥ 1。语义=荷载分担份额:
    任一时刻石的完整荷载必须被支撑体集合完整分担。采样点 = 每石全部
    curve knot(必为真实事件 seq)∪ 其孔全部 ≥ 首 knot 的事件 seq ——
    capacity_curve 分段线性且端点 ≥1 则段内 ≥1, 故本采样覆盖连续全程,
    "全事件核过"是其子集。左钳语义(edge_capacity): 首 knot 前边不存在。"""
    errs = []  # type: List[str]
    tol = 1e-9
    seqs_by_hole = {}  # type: Dict[str, List[int]]
    for e in events:
        seqs_by_hole.setdefault(e.get("hole") or "", []).append(
            int(e["seq"]))
    for zh in seqs_by_hole:
        seqs_by_hole[zh] = sorted(set(seqs_by_hole[zh]))
    for sid in sorted(edge_plan):
        edges = edge_plan[sid]
        knots = sorted({int(pt[0]) for ed in edges
                        for pt in ed["capacity_curve"]})
        if not knots:
            errs.append("CAP_NO_CURVE 石 %s 支撑边缺 capacity_curve" % sid)
            continue
        samples = set(knots)
        for x in seqs_by_hole.get(sid.split(".")[0], ()):
            if x >= knots[0]:
                samples.add(x)
        for x in samples:
            tot = sum(L.edge_capacity(ed, x) for ed in edges)
            if tot < 1.0 - tol:
                errs.append("CAP_INVARIANT 石 %s seq=%d Σcapacity=%.6f < 1 "
                            "(荷载分担不完整)" % (sid, x, tot))
                break   # 每石报首违例, 防错误表刷屏
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
        # F4: FILLED=该孔 R5b 背胞填筑完成 —— 只数 CLEAR 后的 FILL 角色
        # 置放(合龙→落架窗内的锁固肩是波1 砌体, 不构成 FILLED; 无背胞孔
        # 不进 FILLED 态, 与构造轨迹同形)。
        clear_seq0 = clears[0]["seq"] if clears else None
        for e in g.get("PLACE_STONE", []):
            sid = e.get("stone_id") or ""
            if _role(sid) in FILL_ROLES and clear_seq0 is not None \
                    and e["seq"] > clear_seq0:
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
    """R6 跨孔组合表核(对任意事件流): 逐转移推进状态向量, 禁跳孔落架;
    相邻孔同落架须**对内同档**(λ 差 ≤ 一档 —— 主控 2026-10-07 裁决采纳
    多孔连拱"对称同步卸落": 全桥同波逐档合法, 乱序同落架仍红;
    与 g3_check._check_r6 两实现互证)。
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
                if nrank < _STATE_RANK["CLOSED_SUPPORTED"]:
                    errs.append(
                        "R6_JUMP_DECENTER 孔 %s 落架时邻孔 %s 状态 %s "
                        "< CLOSED_SUPPORTED(跳孔落架, seq=%s)"
                        % (z, nz, state[nz], at))
    errs.extend(_check_adj_rung_lock(events, zones, rank_of))
    return errs


def _check_adj_rung_lock(events, zones, rank_of):
    # type: (List[Dict[str, Any]], List[str], Dict[str, int]) -> List[str]
    """R6_ADJ 对内同档核(事件驱动; 与 g3_check._check_r6 同判据独立实现):
    任一 DECENTERING 事件时, 处于落架中的邻孔与本孔 λ 差须 ≤ 一档
    (LAMBDA_LADDER 步长)。全桥同波逐档(每档邻孔同 λ/差恰一事件拍 ≤一档)
    合法; 一方连升多档他方未动 = 乱序同落架, 红。λ 轨迹: dstart=0,
    WEDGE_RELEASE=load_lambda(非法值不推进, 形制由 events 判红), clear=1。"""
    errs = []  # type: List[str]
    tol = 1e-9
    step = LAMBDA_LADDER[1] - LAMBDA_LADDER[0]
    lam = {}      # type: Dict[str, float]
    dstart = {}   # type: Dict[str, int]
    clear = {}    # type: Dict[str, int]
    for e in sorted(events, key=lambda x: x["seq"]):
        zh = e.get("hole") or ""
        et = e.get("etype")
        i = rank_of.get(zh)
        if i is None or et not in E.DECENTERING_TYPES:
            continue
        seq = e["seq"]
        own = (0.0 if et == "DECENTER_START"
               else 1.0 if et == "CENTERING_CLEAR"
               else float(e.get("load_lambda") or 0.0))
        for j in (i - 1, i + 1):
            if not (0 <= j < len(zones)):
                continue
            nz = zones[j]
            ds, cl = dstart.get(nz), clear.get(nz)
            if ds is not None and seq >= ds and (cl is None or seq < cl):
                nl = lam.get(nz, 0.0)
                if abs(own - nl) > step + tol:
                    errs.append(
                        "R6_ADJ_DECENTERING 相邻孔 %s/%s 同落架失档 "
                        "(λ %.2f vs %.2f, 差>一档, seq=%d) —— 对内同档"
                        % (zh, nz, own, nl, seq))
        if et == "DECENTER_START":
            dstart[zh] = seq
        elif et == "CENTERING_CLEAR":
            clear[zh] = seq
        else:
            v = e.get("load_lambda")
            if isinstance(v, (int, float)) and not isinstance(v, bool) \
                    and 0.0 <= float(v) <= 1.0:
                lam[zh] = float(v)
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
    # 一次扫描同时出 id 集与吞没率(build/check 共用; 清单落盘 meta)
    dm_detail = _double_model_ratios(led)
    dm = set(dm_detail)
    res = build_sequence(led, centerings, dm_ids=dm)
    errs = check_sequence(res, led, centerings, dm_ids=dm)
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
    # [审查 INFO 卫生] dm 剔除清单落盘(幂等可 diff): id(字典序)+吞没率
    # (6 位舍入), 不再只有 n_dm_excluded 计数 —— 报告/测试钉该列表,
    # 归因可核对不再依赖会话正文。
    res["meta"]["dm_excluded"] = [
        {"id": sid, "ratio": round(dm_detail[sid], 6)}
        for sid in sorted(dm_detail)]
    L.save_ledger(led2, os.path.join(_OUT_DIR, "ledger_sequenced.json"))
    seq_out = {k: res[k] for k in ("events", "sequence", "frontier_trace",
                                   "meta")}
    with open(os.path.join(_OUT_DIR, "sequence.json"), "w",
              encoding="utf-8") as f:
        json.dump(seq_out, f, ensure_ascii=False, indent=1, sort_keys=True)
    n_stage = len(res["sequence"])
    print("OK stones=%d(in_void 滤除 %d, dm 占位剔除 %d) events=%d stages=%d "
          "trace=%d holes=%d"
          % (res["meta"]["n_stones"], res["meta"]["n_stones_in_void"],
             res["meta"]["n_dm_excluded"],
             res["meta"]["n_events"], n_stage,
             len(res["frontier_trace"]), len(res["meta"]["hole_order"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
