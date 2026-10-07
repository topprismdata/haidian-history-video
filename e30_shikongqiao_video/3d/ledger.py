# e30_shikongqiao_video/3d/ledger.py
# -*- coding: utf-8 -*-
"""P1 砌体账目: 每石一条记录。id=纯拓扑语义键(坐标永不入 id), uuid 主键+谱系。

P2-T1 schema v2(兼容扩展): EVIDENCE 增 inferred_construction; support_edge 以
capacity_curve=[[event_seq,capacity],...] 表达随事件序列衰减的支撑能力, 旧形
{active_from,active_to} 须先过 migrate_v1_to_v2。meta.schema 判别值保持 1——
既有负控钉死 schema==2 报错、正控钉死 schema==1 零错, 且迁移后须 validate==[],
三条联立唯一解是 v2 形态由边形状+枚举表达, 不动判别值。"""
import json
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

def _curve_points(curve):
    # type: (Any) -> Optional[List[List[float]]]
    """capacity_curve=[[event_seq,capacity],...] 形态检查: 非空、每点二元数值组。
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
        pts.append([float(x), float(y)])
    return pts

def edge_capacity(edge, event_seq):
    # type: (Dict[str, Any], float) -> float
    """支撑边在事件序号 event_seq 处的剩余承载能力: 按 curve 线性插值,
    curve 外钳制为端点值。无 curve/形态非法(如未迁移的 v1 边)=0.0, 不抛异常。"""
    pts = _curve_points(edge.get("capacity_curve") if isinstance(edge, dict) else None)
    if not pts:
        return 0.0
    x = float(event_seq)
    if x <= pts[0][0]:
        return pts[0][1]
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
    """v1→v2 原地迁移(幂等, 二次调用零变化): 旧形 support_edge
    {active_from,active_to} → capacity_curve=[[active_from,1.0],[active_to,0.0]];
    单侧键缺失迁成单点恒值边(如仅 active_from=2 → [[2,1.0]])。已有
    capacity_curve 的边原样保留; 非 dict 边不动(留给 validate 报 SUPPORT_EDGE_SHAPE)。
    meta.schema 保持 1。返回同一 led 便于链式调用。"""
    for s in led.get("stones", []):
        for e in s.get("support_edges", []):
            if not isinstance(e, dict) or e.get("capacity_curve") is not None:
                continue
            a = e.pop("active_from", None)
            b = e.pop("active_to", None)
            if a is None and b is None:
                continue
            curve = []  # type: List[List[Any]]
            if a is not None:
                curve.append([a, 1.0])
            if b is not None:
                curve.append([b, 0.0])
            e["capacity_curve"] = curve
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

def validate_ledger(led, allow_clearance=False):
    # type: (Dict[str, Any], bool) -> List[str]
    """账目校验。allow_clearance=False(默认): clearance_manufacturing_mm 已置值
    报 CLEARANCE_PREMATURE(置值只许发生在 T6 导出时序内); True: 放行已置值记录,
    其余判据不豁免。"""
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
            if not isinstance(e, dict):
                errs.append("SUPPORT_EDGE_SHAPE " + sid)
                continue
            if e.get("type") not in SUPPORT_TYPES:
                errs.append("SUPPORT_TYPE " + sid)
            curve = e.get("capacity_curve")
            if curve is None:
                if "active_from" in e or "active_to" in e:
                    errs.append("SUPPORT_SHAPE %s 旧形 active_from/active_to, "
                                "先过 migrate_v1_to_v2" % sid)
                else:
                    errs.append("SUPPORT_SHAPE %s 缺 capacity_curve" % sid)
                continue
            pts = _curve_points(curve)
            if pts is None:
                errs.append("SUPPORT_SHAPE %s capacity_curve 形态非法" % sid)
                continue
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                if x1 <= x0 or y1 > y0:
                    errs.append("CURVE_MONOTONIC %s event 序号须递增且 capacity "
                                "单调不增: %s→%s" % (sid, [x0, y0], [x1, y1]))
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
