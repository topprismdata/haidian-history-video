# e30_shikongqiao_video/3d/ledger.py
# -*- coding: utf-8 -*-
"""P1 砌体账目: 每石一条记录。id=纯拓扑语义键(坐标永不入 id), uuid 主键+谱系。"""
import json
import os
import re
import tempfile
import uuid as _uuid
from typing import Any, Dict, List, Optional

SCHEMA = 1
EVIDENCE = ("ashlar_truth", "core_reconstruction", "measured")
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

def validate_ledger(led):
    # type: (Dict[str, Any]) -> List[str]
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
        if s.get("clearance_manufacturing_mm") is not None:
            errs.append("CLEARANCE_PREMATURE " + sid)
        for e in s.get("support_edges", []):
            if not isinstance(e, dict):
                errs.append("SUPPORT_EDGE_SHAPE " + sid)
                continue
            if e.get("type") not in SUPPORT_TYPES:
                errs.append("SUPPORT_TYPE " + sid)
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
