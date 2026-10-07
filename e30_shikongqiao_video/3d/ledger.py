# e30_shikongqiao_video/3d/ledger.py
# -*- coding: utf-8 -*-
"""P1 砌体账目: 每石一条记录。id=纯拓扑语义键(坐标永不入 id), uuid 主键+谱系。

P2-T1 schema v2(兼容扩展): EVIDENCE 增 inferred_construction; support_edge 以
capacity_curve=[[event_seq,capacity],...] 表达随事件序列衰减的支撑能力, 旧形
{active_from,active_to} 须先过 migrate_v1_to_v2。meta.schema 判别值保持 1——
既有负控钉死 schema==2 报错、正控钉死 schema==1 零错, 且迁移后须 validate==[],
三条联立唯一解是 v2 形态由边形状+枚举表达, 不动判别值。

修复轮语义(spec 00959bf 裁决): curve x=数值 event_seq; 左钳=0.0(曲线首点前
支撑不存在), 右钳=末点值; migrate 先判后写(不可插值的旧键不吞不写坏)。"""
import json
import math
import os
import re
import tempfile
import uuid as _uuid
from typing import Any, Dict, List, Optional

SCHEMA = 1  # v2 不 bump 判别值(见模块 docstring); 升级语义由 capacity_curve 形制承载
EVIDENCE = ("ashlar_truth", "core_reconstruction", "measured", "inferred_construction")
SUPPORT_TYPES = ("stone", "centering", "fill", "foundation", "temporary")
_ID_RE = re.compile(r"(ARCH\d\d|F\d\d|T[01])\.(EAST|WEST)\."
                    r"(RING|SPANDREL|PIER|IMPOST|BACK|PAVING|RAIL|POST|CARVE|CORE)\."
                    r"C\d+\.B\d+")

def _is_uuid4(s):
    # type: (Any) -> bool
    try:
        return _uuid.UUID(s).version == 4
    except (ValueError, TypeError, AttributeError):
        return False

def _num(v):
    # type: (Any) -> bool
    """可插值数值: int/float、非 bool、有限。migrate/validate 先判后写共用闸。"""
    return (isinstance(v, (int, float)) and not isinstance(v, bool)
            and math.isfinite(v))

def _curve_points(curve):
    # type: (Any) -> Optional[List[List[float]]]
    """capacity_curve=[[event_seq,capacity],...] 形态检查: 非空、每点二元数值组,
    且两坐标均为有限数(I3: NaN/inf 在形态闸门直接拒, 不再绕过「比较全 False」
    的单调闸门)。curve x 为数值 event_seq(与 events.py 序号一致), 非字符串事件名。
    形态不合法返回 None, 合法返回 float 化点位表。"""
    if not isinstance(curve, (list, tuple)) or not curve:
        return None
    pts = []  # type: List[List[float]]
    for p in curve:
        if not isinstance(p, (list, tuple)) or len(p) != 2:
            return None
        x, y = p[0], p[1]
        if isinstance(x, bool) or isinstance(y, bool):
            return None
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            return None
        fx, fy = float(x), float(y)
        if not (math.isfinite(fx) and math.isfinite(fy)):
            return None
        pts.append([fx, fy])
    return pts

def edge_capacity(edge, event_seq):
    # type: (Dict[str, Any], Any) -> float
    """支撑边在事件序号 event_seq 处的剩余承载能力: 按 curve 线性插值。
    I1/spec 00959bf 裁决: 曲线首点之前(x < pts[0][0])=0.0 左钳——支撑在其
    曲线开始前不存在; 末点之后=末点值右钳(开放端/永久边保持末点值)。
    curve x 为数值 event_seq, 非字符串事件名。无 curve/形态非法(未迁移 v1
    边、非有限点)=0.0; event_seq 非数值(None/str/list/bool)或非有限=0.0,
    一律不抛异常。点序为线性扫描: 长曲线调用方须自备 bisect/增量指针,
    勿在每石×每事件的内层循环里直调本函数。"""
    pts = _curve_points(edge.get("capacity_curve") if isinstance(edge, dict) else None)
    if not pts:
        return 0.0
    if isinstance(event_seq, bool) or not isinstance(event_seq, (int, float)):
        return 0.0
    x = float(event_seq)
    if not math.isfinite(x):
        return 0.0
    if x < pts[0][0]:
        return 0.0
    if x >= pts[-1][0]:
        return pts[-1][1]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            if x1 == x0:
                return y1
            return y0 + (x - x0) / (x1 - x0) * (y1 - y0)
    return pts[-1][1]

def migrate_v1_to_v2(led):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """v1→v2 原地迁移(I2 先判后写: 仅当值对可插值才 pop 旧键+写 curve;
    不可插值/拒迁的边旧键原样保留, 不吞键不写坏 curve; 幂等, 二次调用零变化)。
    规则(与 edge_capacity 的 I1 左钳=0.0 语义配套):
    {active_from:a, active_to:b} 皆数值且 a<b → [[a,1.0],[b,0.0]];
    a==b(瞬时窗, 主控裁决)→ [[0,1.0],[b,0.0]]: 保 v1 语义「to 之前活着」,
        单独 [[to,0.0]] 会被左钳误杀 to 之前的整个区间;
    a>b(反转窗)→ 拒迁不产出必红 curve, validate 报 SUPPORT_WINDOW_ORDER;
    仅 active_from=a → [[a,1.0]](a 起永久支撑, a 前不存在);
    仅 active_to=b → [[b,0.0]];
    两键皆 null 的静态边 → [[0,1.0]] 永久支撑(自 0 起, 不受左钳影响);
    任一侧非数值(字符串时窗如 "closure+7d"/bool/非有限)→ 原样不动,
        validate 报 SUPPORT_SHAPE 旧形不可插值并回显原值。
    已有 capacity_curve 的边原样保留; 非 dict 边不动(留给 validate 报
    SUPPORT_EDGE_SHAPE)。meta.schema 保持 1。返回同一 led 便于链式调用。"""
    for s in led.get("stones", []):
        for e in s.get("support_edges", []):
            if not isinstance(e, dict) or e.get("capacity_curve") is not None:
                continue
            if "active_from" not in e and "active_to" not in e:
                continue
            a = e.get("active_from")
            b = e.get("active_to")
            if a is None and b is None:
                e.pop("active_from", None)
                e.pop("active_to", None)
                e["capacity_curve"] = [[0, 1.0]]
                continue
            if _num(a) and _num(b):
                if a > b:
                    continue
                e.pop("active_from")
                e.pop("active_to")
                if a == b:
                    e["capacity_curve"] = [[0, 1.0], [b, 0.0]]
                else:
                    e["capacity_curve"] = [[a, 1.0], [b, 0.0]]
                continue
            if _num(a) and b is None:
                e.pop("active_from")
                e["capacity_curve"] = [[a, 1.0]]
                continue
            if _num(b) and a is None:
                e.pop("active_to")
                e["capacity_curve"] = [[b, 0.0]]
                continue
            # 任一侧非数值: 旧键保留, 交给 validate 可诊断
    return led

def family_key(zone, face, role, course, block):
    # type: (str, str, str, int, int) -> str
    return "%s.%s.%s.C%02d.B%02d" % (zone, face, role, course, block)

def new_stone(zone, face, role, course, block, family, params, transform,
              material, evidence="ashlar_truth", joint_historical_mm=10.0):
    # type: (...) -> Dict[str, Any]
    return {
        "id": family_key(zone, face, role, course, block),
        "uuid": str(_uuid.uuid4()),
        "family": family,
        "params": dict(params),
        "transform": [float(v) for v in transform],
        "material": material,
        "role_struct": role,
        "evidence": evidence,
        "support_edges": [],
        "joint_historical_mm": float(joint_historical_mm),
        "clearance_manufacturing_mm": None,
        "lineage": {"parent_id": None, "replaces": None},
        "stage_hint": None,
        "print": {"batch": None, "faces_up": "+Z", "min_feature_ok": None},
    }

def _validate_support_edge(sid, e, errs, known_event_seqs=None):
    # type: (str, Any, List[str], Optional[Any]) -> None
    """单条支撑边校验, 错误追加进 errs(validate_ledger 与 P2-T5 g3_check 共用)。
    码表: SUPPORT_EDGE_SHAPE 非 dict / SUPPORT_TYPE / SUPPORT_SHAPE 形制类(缺
    curve、旧形待迁、旧形不可插值、curve+active_* 混形、curve 形态非法含非有限)/
    SUPPORT_WINDOW_ORDER 反转窗不可迁 / CURVE_ORDER x 非升(I5 拆码)/
    CURVE_MONOTONIC y 回升(I5 拆码)/ CURVE_RANGE y 越出 [0,1] /
    CURVE_EVENT_UNKNOWN known_event_seqs 给定时 x 不在事件账本集合内。"""
    if not isinstance(e, dict):
        errs.append("SUPPORT_EDGE_SHAPE " + sid)
        return
    if e.get("type") not in SUPPORT_TYPES:
        errs.append("SUPPORT_TYPE " + sid)
    curve = e.get("capacity_curve")
    legacy = "active_from" in e or "active_to" in e
    if curve is None:
        if not legacy:
            errs.append("SUPPORT_SHAPE %s 缺 capacity_curve" % sid)
            return
        a = e.get("active_from")
        b = e.get("active_to")
        if _num(a) and _num(b) and a > b:
            errs.append("SUPPORT_WINDOW_ORDER %s active_from=%r > active_to=%r, "
                        "反转窗, migrate 拒迁" % (sid, a, b))
            return
        bad = [v for v in (a, b) if v is not None and not _num(v)]
        if bad:
            errs.append("SUPPORT_SHAPE %s 旧形不可插值: %r" % (sid, bad[0]))
            return
        errs.append("SUPPORT_SHAPE %s 旧形 active_from/active_to, "
                    "先过 migrate_v1_to_v2" % sid)
        return
    if legacy:
        errs.append("SUPPORT_SHAPE %s 混形: capacity_curve 与 "
                    "active_from/active_to 并存" % sid)
        return
    pts = _curve_points(curve)
    if pts is None:
        errs.append("SUPPORT_SHAPE %s capacity_curve 形态非法"
                    "(非空且每点二元有限数值组)" % sid)
        return
    for p in pts:
        if not 0.0 <= p[1] <= 1.0:
            errs.append("CURVE_RANGE %s capacity 越出 [0,1]: %s" % (sid, p))
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x1 <= x0:
            errs.append("CURVE_ORDER %s event 序号 x 须严格递增: %s→%s"
                        % (sid, [x0, y0], [x1, y1]))
        if y1 > y0:
            errs.append("CURVE_MONOTONIC %s capacity 须单调不增(此处回升): %s→%s"
                        % (sid, [x0, y0], [x1, y1]))
    if known_event_seqs is not None:
        for (x0, _y0) in pts:
            if x0 not in known_event_seqs:
                errs.append("CURVE_EVENT_UNKNOWN %s curve 事件序号 %r "
                            "不在已知事件集" % (sid, x0))

def validate_ledger(led, allow_clearance=False, known_event_seqs=None):
    # type: (Dict[str, Any], bool, Optional[Any]) -> List[str]
    """账目校验。allow_clearance=False(默认): clearance_manufacturing_mm 已置值
    报 CLEARANCE_PREMATURE(置值只许发生在 T6 导出时序内); True: 放行已置值记录,
    其余判据不豁免。known_event_seqs=None(默认)不查 curve 事件号; 给定集合时
    curve 的任一 x 不在其中 → CURVE_EVENT_UNKNOWN(P2-T5 与事件账本交叉闸)。"""
    errs = []  # type: List[str]
    meta = led.get("meta", {})
    if meta.get("schema") != SCHEMA:
        errs.append("SCHEMA meta.schema != %d" % SCHEMA)
    for k in ("curve_hash", "seed"):
        if k not in meta:
            errs.append("META_MISSING " + k)
    seen = set()
    seen_uuids = set()
    for s in led.get("stones", []):
        sid = s.get("id", "")
        if "id" not in s:
            errs.append("ID_MISSING uuid=%s" % s.get("uuid"))
        else:
            if not _ID_RE.fullmatch(sid):
                errs.append("ID_COORD or bad id: " + sid)
            if sid in seen:
                errs.append("ID_DUP " + sid)
            seen.add(sid)
        uid = s.get("uuid")
        if not _is_uuid4(uid):
            errs.append("UUID_BAD id=%s uuid=%r" % (sid, uid))
        if uid in seen_uuids:
            errs.append("UUID_DUP id=%s uuid=%s" % (sid, uid))
        seen_uuids.add(uid)
        if s.get("evidence") not in EVIDENCE:
            errs.append("EVIDENCE bad: %s" % s.get("evidence"))
        if s.get("clearance_manufacturing_mm") is not None \
                and not allow_clearance:
            errs.append("CLEARANCE_PREMATURE " + sid)
        for e in s.get("support_edges", []):
            _validate_support_edge(sid, e, errs, known_event_seqs)
    return errs

def load_ledger(path):
    # type: (str) -> Dict[str, Any]
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_ledger(led, path):
    # type: (Dict[str, Any], str) -> None
    # 原子写: 同目录临时件写完后 os.replace, dump 失败不截断原文件
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(suffix=".json.tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(led, f, ensure_ascii=False, indent=1, sort_keys=True)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise

def query(led, zone=None, role=None, material=None):
    # type: (Dict[str, Any], Optional[str], Optional[str], Optional[str]) -> List[Dict[str, Any]]
    out = []
    for s in led.get("stones", []):
        if zone is not None and not s.get("id", "").startswith(zone + "."):
            continue
        if role is not None and s.get("role_struct") != role:
            continue
        if material is not None and s.get("material") != material:
            continue
        out.append(s)
    return out
