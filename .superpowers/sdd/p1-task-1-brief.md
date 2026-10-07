# P1 砌体实体引擎（stone-ledger）实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把十七孔桥从"合并网格+程序贴面"转为每石一账目、每石一个可打印流形实体的砌体数据系统（ledger + 族库 + 验证器 + 导出器 + 场景分层装配）。

**Architecture:** ledger.json 是唯一真相（拓扑语义 id + uuid + 谱系 + 证据级 + 时窗支撑边 + 历史缝/制造间隙两量分离）；族库 = 参数化 bmesh 生成函数（确定性）+ unique 异形烘焙缓存；场景 = Geometry Nodes 实例（point=石, attribute=id/family/stage），主场景不持有 5000 Object；导出 = 逐块临时实例化→inset→STL/3MF→销毁，canonical 永远是 mesh+ledger。

**Tech Stack:** Python 3.9.6（禁 `X | None`、禁 `match`）、Blender 4.x bpy/bmesh（headless `blender -b`）、numpy、仓库既有治理测试套件。

## Global Constraints
- Python 3.9.6：`Optional[X]` 不用 `X | None`；无 match 语句
- 不放松任何既有判据；新判据必须带负控制（破坏能被抓住）
- 产物（*.blend/shot_*.png/ledger_cache）gitignore；代码+JSON 才入库
- 中文提交信息 `<type>(<scope>): <摘要>`
- 几何冻结项零触碰：facts.py 曲线/RISE_C/SPAN/PIER_W/impost 参数/砖谱 JSON 内容
- 测试位置：`e30_shikongqiao_video/tests/test_p1_*.py`（治理套件同目录）；合成数据单测不渲桥
- 每 task 结束 commit；隔离工作树 `/tmp/e30_p1/`（cp 主树 3d，refs 软链）

## 文件结构
| 文件 | 职责 | 新/改 |
|---|---|---|
| `3d/ledger.py` | schema/IO/校验/查询/id 规则 | 新 |
| `3d/families.py` | 族网格生成（确定性）+ unique 烘焙 + 缓存失效 | 新 |
| `3d/masonry2.py` | 三层生成器：面石(顺丁)/背衬/core cells → ledger | 新 |
| `3d/printcheck.py` | 流形/自交/壁厚/穿透/体积 | 新 |
| `3d/export_print.py` | inset 间隙/STL+3MF/装配 manifest/coupon | 新 |
| `3d/build_scene2.py` | `--emit-lib/--layout/--proxy` 三模式 + GN 装配 | 改 |
| `3d/ledger/ledger.json` | 主索引（生成物，入库） | 新 |
| `tests/test_p1_ledger.py` 等 5 个 | 单测 | 新 |

---

## Global Constraints
- Python 3.9.6：`Optional[X]` 不用 `X | None`；无 match 语句
- 不放松任何既有判据；新判据必须带负控制（破坏能被抓住）
- 产物（*.blend/shot_*.png/ledger_cache）gitignore；代码+JSON 才入库
- 中文提交信息 `<type>(<scope>): <摘要>`
- 几何冻结项零触碰：facts.py 曲线/RISE_C/SPAN/PIER_W/impost 参数/砖谱 JSON 内容
- 测试位置：`e30_shikongqiao_video/tests/test_p1_*.py`（治理套件同目录）；合成数据单测不渲桥
- 每 task 结束 commit；隔离工作树 `/tmp/e30_p1/`（cp 主树 3d，refs 软链）


### Task 1: ledger.py 数据模型与 id 纪律

**Files:**
- Create: `e30_shikongqiao_video/3d/ledger.py`
- Test: `e30_shikongqiao_video/tests/test_p1_ledger.py`

**Interfaces:**
- Produces: `new_stone(zone, role, course, block, family, params, transform, material, evidence="ashlar_truth", joint_historical_mm=10.0) -> dict`；`family_key(zone, role, course, block) -> str`；`load_ledger(path)/save_ledger(led, path)`；`validate_ledger(led) -> List[str]`；`query(led, zone=None, role=None, material=None) -> List[dict]`

- [ ] **Step 1: 写失败测试**

```python
# e30_shikongqiao_video/tests/test_p1_ledger.py
import json, os, sys, uuid as _uuid
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "3d"))
import ledger as L

def test_family_key_topology_not_coords():
    k = L.family_key("ARCH09", "EAST", "RING", 12, 7)
    assert k == "ARCH09.EAST.RING.C12.B07"
    # id 不含坐标: 同一键在曲线重标定后不变(纪律由 validate 保证无浮点入 id)
    assert not any(ch in k for ch in ".0123456789-") or k.count(".") == 4

def test_new_stone_uuid_unique_and_lineage():
    a = L.new_stone("ARCH09", "EAST", "RING", 12, 7, "ring-wedge",
                    {"w": 0.7}, [0, 0, 0, 0, 0, 0], "qingshi")
    b = L.new_stone("ARCH09", "EAST", "RING", 12, 8, "ring-wedge",
                    {"w": 0.7}, [1, 0, 0, 0, 0, 0], "qingshi")
    assert a["uuid"] != b["uuid"]
    _uuid.UUID(a["uuid"])  # 合法 UUID4
    assert a["lineage"] == {"parent_id": None, "replaces": None}
    assert a["evidence"] == "ashlar_truth"
    assert a["joint_historical_mm"] == 10.0
    assert a["clearance_manufacturing_mm"] is None  # 导出前不许有制造间隙

def test_validate_rejects_coord_in_id_and_bad_evidence():
    s = L.new_stone("ARCH09", "EAST", "RING", 12, 7, "ring-wedge", {}, [0]*6, "qingshi")
    s["id"] = "ARCH09.EAST.RING.C12.07x3.21"   # 坐标混入 id
    led = {"meta": {"curve_hash": "h", "seed": 1, "schema": 1}, "stones": [s]}
    errs = L.validate_ledger(led)
    assert any("ID_COORD" in e for e in errs)
    s["id"] = "ARCH09.EAST.RING.C12.B07"; s["evidence"] = "guess"
    errs = L.validate_ledger(led)
    assert any("EVIDENCE" in e for e in errs)

def test_roundtrip_and_query(tmp_path):
    led = {"meta": {"curve_hash": "h", "seed": 1, "schema": 1}, "stones": [
        L.new_stone("ARCH09", "EAST", "RING", 12, 7, "ring-wedge", {}, [0]*6, "qingshi"),
        L.new_stone("ARCH09", "EAST", "SPANDREL", 3, 2, "wedge-std", {}, [0]*6, "qingshi"),
        L.new_stone("ARCH09", "EAST", "RAIL", 0, 1, "rail-post", {}, [0]*6, "marble")]}
    p = str(tmp_path / "ledger.json")
    L.save_ledger(led, p)
    got = L.load_ledger(p)
    assert len(got["stones"]) == 3
    assert len(L.query(got, role="RING")) == 1
    assert len(L.query(got, material="marble")) == 1
    assert len(L.query(got, zone="ARCH09", role="SPANDREL")) == 1
```

- [ ] **Step 2: 跑测试确认失败**
Run: `cd /Volumes/macstudio/video-projects/e30_shikongqiao_video && python3 -m pytest tests/test_p1_ledger.py -q`
Expected: FAIL（ModuleNotFoundError: ledger）

- [ ] **Step 3: 最小实现**

```python
# e30_shikongqiao_video/3d/ledger.py
# -*- coding: utf-8 -*-
"""P1 砌体账目: 每石一条记录。id=纯拓扑语义键(坐标永不入 id), uuid 主键+谱系。"""
import json
import re
import uuid as _uuid
from typing import Any, Dict, List, Optional

SCHEMA = 1
EVIDENCE = ("ashlar_truth", "core_reconstruction", "measured")
_ID_RE = re.compile(r"^(ARCH\d\d|F\d\d|T[01])\.(EAST|WEST)\."
                    r"(RING|SPANDREL|PIER|IMPOST|BACK|PAVING|RAIL|POST|CARVE|CORE)\."
                    r"C\d+\.B\d+$")

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
    for s in led.get("stones", []):
        sid = s.get("id", "")
        if not _ID_RE.match(sid):
            errs.append("ID_COORD or bad id: " + sid)
        if sid in seen:
            errs.append("ID_DUP " + sid)
        seen.add(sid)
        if s.get("evidence") not in EVIDENCE:
            errs.append("EVIDENCE bad: %s" % s.get("evidence"))
        if s.get("clearance_manufacturing_mm") is not None:
            errs.append("CLEARANCE_PREMATURE " + sid)
        for e in s.get("support_edges", []):
            if e.get("type") not in ("stone", "centering", "fill",
                                     "foundation", "temporary"):
                errs.append("SUPPORT_TYPE " + sid)
    return errs

def load_ledger(path):
    # type: (str) -> Dict[str, Any]
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_ledger(led, path):
    # type: (Dict[str, Any], str) -> None
    with open(path, "w", encoding="utf-8") as f:
        json.dump(led, f, ensure_ascii=False, indent=1, sort_keys=True)

def query(led, zone=None, role=None, material=None):
    # type: (Dict[str, Any], Optional[str], Optional[str], Optional[str]) -> List[Dict[str, Any]]
    out = []
    for s in led.get("stones", []):
        if zone is not None and not s["id"].startswith(zone + "."):
            continue
        if role is not None and s["role_struct"] != role:
            continue
        if material is not None and s["material"] != material:
            continue
        out.append(s)
    return out
```

- [ ] **Step 4: 跑测试确认通过**
Run: 同 Step 2。Expected: 4 passed

- [ ] **Step 5: Commit**
```bash
git add e30_shikongqiao_video/3d/ledger.py e30_shikongqiao_video/tests/test_p1_ledger.py
git commit -m "feat(e30): P1-T1 ledger数据模型(拓扑id+uuid+谱系+证据级+两缝分离)"
```

