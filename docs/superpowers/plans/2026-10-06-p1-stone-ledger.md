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

### Task 1: ledger.py 数据模型与 id 纪律

**Files:**
- Create: `e30_shikongqiao_video/3d/ledger.py`
- Test: `e30_shikongqiao_video/tests/test_p1_ledger.py`

**Interfaces:**
- Produces: `new_stone(zone, face, role, course, block, family, params, transform, material, evidence="ashlar_truth", joint_historical_mm=10.0) -> dict`（**5 拓扑参含 face=EAST/WEST**, T1 审查裁决逐字代码为权威）；`family_key(zone, face, role, course, block) -> str`；`load_ledger(path)/save_ledger(led, path)`；`validate_ledger(led) -> List[str]`；`query(led, zone=None, role=None, material=None) -> List[dict]`

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

---

### Task 2: families.py 族库（确定性网格 + unique 烘焙）

**Files:**
- Create: `e30_shikongqiao_video/3d/families.py`
- Test: `e30_shikongqiao_video/tests/test_p1_families.py`

**Interfaces:**
- Consumes: 无（纯几何）
- Produces: `family_mesh(family, params) -> (verts, faces)`（verts: List[Tuple[float,float,float]] 米, faces: List[Tuple[int,...]]）；`bake_unique(stone_id, verts, faces, cache_dir, curve_hash) -> str`（返回 obj 路径）；`FAMILIES: Dict[str, callable]`

- [ ] **Step 1: 写失败测试**

```python
# e30_shikongqiao_video/tests/test_p1_families.py
import os, sys
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "3d"))
import families as F

def test_wedge_std_deterministic_and_manifold():
    p = {"w": 1.2, "h": 0.55, "d": 1.2, "proud": 0.006, "back": 0.30,
         "hw_b": 6.0, "hw_t": 5.84}
    v1, f1 = F.family_mesh("wedge-std", p)
    v2, f2 = F.family_mesh("wedge-std", p)
    assert v1 == v2 and f1 == f2          # 确定性
    assert len(v1) == 8 and len(f1) == 6  # 楔形六面
    # 流形: 每边恰好两面
    from collections import Counter
    ec = Counter()
    for face in f1:
        for i in range(len(face)):
            a, b = face[i], face[(i + 1) % len(face)]
            ec[(min(a, b), max(a, b))] += 1
    assert all(c == 2 for c in ec.values())

def test_wedge_std_follows_batter():
    p = {"w": 1.0, "h": 0.4, "d": 1.0, "proud": 0.006, "back": 0.30,
         "hw_b": 6.0, "hw_t": 5.9}
    v, f = F.family_mesh("wedge-std", p)
    ys_front = sorted(set(round(vv[1], 4) for vv in v))
    # 前脸上下沿 y 不同(随收分倾斜), 差≈hw_b-hw_t
    assert abs((max(ys_front) - min(ys_front)) - 0.0) > 1e-6

def test_bake_unique_cache_invalidates_on_curve_hash(tmp_path):
    v, f = F.family_mesh("wedge-std", {"w": 1.0, "h": 0.4, "d": 1.0,
                                       "proud": 0.006, "back": 0.3,
                                       "hw_b": 6.0, "hw_t": 5.9})
    p1 = F.bake_unique("ARCH09.EAST.SPANDREL.C03.B02", v, f,
                       str(tmp_path), "hashA")
    assert os.path.exists(p1)
    p2 = F.bake_unique("ARCH09.EAST.SPANDREL.C03.B02", v, f,
                       str(tmp_path), "hashB")
    assert p1 != p2  # curve_hash 变 -> 缓存失效重烘
```

- [ ] **Step 2: 跑测试确认失败**
Run: `python3 -m pytest tests/test_p1_families.py -q` → FAIL ModuleNotFoundError

- [ ] **Step 3: 最小实现**

```python
# e30_shikongqiao_video/3d/families.py
# -*- coding: utf-8 -*-
"""P1 族库: 参数化确定性网格。族=共享 mesh; unique=异形块烘焙缓存。"""
import hashlib
import os
from typing import Any, Dict, List, Tuple

def _wedge_std(params):
    # type: (Dict[str, Any]) -> Tuple[List[Tuple[float, float, float]], List[Tuple[int, ...]]]
    """收分楔形砧石(局部坐标: 原点在块左下前角, x=宽, y=深(向墙内为负), z=高)。
    前脸上下沿 y 随 hw_b/hw_t 倾斜(proud 出挑), 背向 -back。"""
    w = params["w"]; h = params["h"]; proud = params["proud"]; back = params["back"]
    hw_b = params["hw_b"]; hw_t = params["hw_t"]
    f0, f1 = proud, proud + (hw_b - hw_t)   # 前脸下/上沿 y(局部, 上沿内收)
    b0, b1 = f0 - back, f1 - back
    v = [(0.0, b0, 0.0), (w, b0, 0.0), (w, f0, 0.0), (0.0, f0, 0.0),
         (0.0, b1, h), (w, b1, h), (w, f1, h), (0.0, f1, h)]
    f = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
         (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    return v, f

def _slab(params):
    # type: (Dict[str, Any]) -> Tuple[List[Tuple[float, float, float]], List[Tuple[int, ...]]]
    """水平铺石/栏板类直盒。"""
    w, d, h = params["w"], params["d"], params["h"]
    v = [(0, 0, 0), (w, 0, 0), (w, d, 0), (0, d, 0),
         (0, 0, h), (w, 0, h), (w, d, h), (0, d, h)]
    f = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
         (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    return v, f

FAMILIES = {"wedge-std": _wedge_std, "slab": _slab}

def family_mesh(family, params):
    # type: (str, Dict[str, Any]) -> Tuple[List[Tuple[float, float, float]], List[Tuple[int, ...]]]
    return FAMILIES[family](params)

def bake_unique(stone_id, verts, faces, cache_dir, curve_hash):
    # type: (str, List[Tuple[float, float, float]], List[Tuple[int, ...]], str, str) -> str
    os.makedirs(cache_dir, exist_ok=True)
    tag = hashlib.sha1(("%s|%s" % (stone_id, curve_hash)).encode()).hexdigest()[:12]
    path = os.path.join(cache_dir, "%s_%s.obj" % (stone_id.replace(".", "_"), tag))
    with open(path, "w", encoding="utf-8") as fh:
        for v in verts:
            fh.write("v %.6f %.6f %.6f\n" % v)
        for fc in faces:
            fh.write("f " + " ".join(str(i + 1) for i in fc) + "\n")
    return path
```

- [ ] **Step 4: 跑测试通过** → 3 passed
- [ ] **Step 5: Commit** `feat(e30): P1-T2 族库(楔形/直盒确定性网格+unique烘焙curve_hash失效)`

---

### Task 3: masonry2.py 面石层（消费砖谱 → ledger）

**Files:**
- Create: `e30_shikongqiao_video/3d/masonry2.py`
- Test: `e30_shikongqiao_video/tests/test_p1_masonry2.py`

**Interfaces:**
- Consumes: `ledger.new_stone/family_key`、`families.family_mesh`、`bridge_geom2`（_hw/deck_z/arch 参数）、`stones/stones_pX.json`
- Produces: `face_stones(spec, arch_idx, side, hw_fn) -> List[dict]`；`build_face_layer(stones_dir, hw_fn, arches) -> List[dict]`

- [ ] **Step 1: 失败测试**（合成 spec：两层三块，验证 id/族参数/顺丁深/间隙字段/镜像 id）

```python
# e30_shikongqiao_video/tests/test_p1_masonry2.py
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "3d"))
import masonry2 as M2

SPEC = {"courses": [
    {"z0": 2.0, "blocks": [{"x0": 0.0, "x1": 1.2}, {"x0": 1.2, "x1": 2.0}]},
    {"z0": 2.55, "blocks": [{"x0": 0.0, "x1": 0.8}, {"x0": 0.8, "x1": 2.0}]}]}

def _hw(x, z):
    return 6.0 - 0.02 * (z - 2.0)

def test_face_stones_ids_and_depths():
    stones = M2.face_stones(SPEC, 8, 1, _hw, course_h=0.55)
    assert len(stones) == 4
    ids = [s["id"] for s in stones]
    assert ids[0] == "ARCH09.EAST.SPANDREL.C00.B00"
    assert ids[3] == "ARCH09.EAST.SPANDREL.C01.B01"
    # 顺丁相间: 同层奇偶块深不同(顺1.2/丁2.4 或参数表), 且都>0.5
    d0 = stones[0]["params"]["d"]; d1 = stones[1]["params"]["d"]
    assert d0 > 0.5 and d1 > 0.5 and abs(d0 - d1) > 0.3
    # 间隙两量分离: 历史缝10mm, 制造间隙未定
    assert all(s["joint_historical_mm"] == 10.0 for s in stones)
    assert all(s["clearance_manufacturing_mm"] is None for s in stones)

def test_face_stones_mirror_id():
    west = M2.face_stones(SPEC, 8, -1, _hw, course_h=0.55)
    assert west[0]["id"] == "ARCH09.WEST.SPANDREL.C00.B00"
```

- [ ] **Step 2: 失败确认**
- [ ] **Step 3: 实现**（顺丁规则：`(course+block) % 2 == 0` → 顺石深 STRETCHER_D=1.2，否则丁石 HEADER_D=2.4；transform=[xc, y_face, z0, 0,0,0]，y 由 hw_fn(x_mid, z_mid)+proud 定；params 含 w/h/d/proud/back/hw_b/hw_t（hw 在块上下沿取值））

```python
# e30_shikongqiao_video/3d/masonry2.py
# -*- coding: utf-8 -*-
"""P1 三层生成器: 面石(顺丁)/背衬/core cells -> ledger。"""
from typing import Any, Callable, Dict, List
import ledger as L

STRETCHER_D = 1.2
HEADER_D = 2.4
PROUD = 0.006
BACK = 0.30

def face_stones(spec, arch_idx, side, hw_fn, course_h=0.55):
    # type: (Dict[str, Any], int, int, Callable[[float, float], float], float) -> List[Dict[str, Any]]
    zone = "ARCH%02d" % arch_idx
    face = "EAST" if side > 0 else "WEST"
    out = []  # type: List[Dict[str, Any]]
    for ci, course in enumerate(spec.get("courses", [])):
        z0 = course["z0"]
        for bi, blk in enumerate(course["blocks"]):
            x0, x1 = blk["x0"], blk["x1"]
            xm = (x0 + x1) / 2.0
            zm = z0 + course_h / 2.0
            depth = STRETCHER_D if (ci + bi) % 2 == 0 else HEADER_D
            hw_b = hw_fn(xm, z0)
            hw_t = hw_fn(xm, z0 + course_h)
            y = hw_fn(xm, zm) + PROUD
            st = L.new_stone(zone, face, "SPANDREL", ci, bi, "wedge-std",
                             {"w": x1 - x0, "h": course_h, "d": depth,
                              "proud": PROUD, "back": BACK,
                              "hw_b": hw_b, "hw_t": hw_t},
                             [xm, y if side > 0 else -y, zm, 0.0, 0.0, 0.0],
                             "qingshi")
            out.append(st)
    return out
```

- [ ] **Step 4: 通过** → 2 passed
- [ ] **Step 5: Commit** `feat(e30): P1-T3 面石层生成器(砖谱->ledger, 顺丁相间, 两缝分离)`

---

### Task 4: masonry2 背衬层 + core cells

**Files:** Modify `3d/masonry2.py`；Test 同文件追加

- [ ] **Step 1: 失败测试**：背衬块 evidence=ashlar_truth、深 0.8-1.2、与面石丁石不穿透（间隙≥2mm 隐缝）；core cells evidence=core_reconstruction、按孔/层切（cell 高≤0.6m）、水密标记

```python
def test_backing_no_penetration_with_headers():
    faces = M2.face_stones(SPEC, 8, 1, _hw, course_h=0.55)
    backs = M2.backing_stones(SPEC, 8, 1, _hw, course_h=0.55, seed=7)
    hdr = [s for s in faces if s["params"]["d"] == M2.HEADER_D]
    for b in backs:
        y_in = abs(b["transform"][1]) - b["params"]["d"]   # 背衬内缘
        for h in hdr:
            y_h_in = abs(h["transform"][1]) - h["params"]["d"]
            if abs(b["transform"][2] - h["transform"][2]) < 0.55:
                assert y_in <= y_h_in - 0.002   # 隐缝>=2mm 不穿透

def test_core_cells_evidence_and_height():
    cells = M2.core_cells(8, _hw, z_lo=1.0, z_hi=6.0, seed=7)
    assert all(c["evidence"] == "core_reconstruction" for c in cells)
    assert all(c["params"]["h"] <= 0.6 for c in cells)
    assert len(cells) >= 8
```

- [ ] **Step 2-4: 实现+通过**（背衬：面石丁石内缘再退 2mm 起、深 0.8-1.2 伪随机(seed)；core cells：孔内 x 分 3 列 × z 每 0.6m 一层 × 前后合并单 cell，params 记 bbox）
- [ ] **Step 5: Commit** `feat(e30): P1-T4 背衬层+core cells(证据级core_reconstruction, 隐缝2mm)`

---

### Task 5: printcheck.py 验证器

**Files:** Create `3d/printcheck.py`；Test `tests/test_p1_printcheck.py`

- [ ] **Step 1: 失败测试**（合成：好楔形 pass；开口盒报 NON_MANIFOLD；自交盒报 SELF_INTERSECT；0.5mm 薄片报 THIN_WALL@1:50；两盒重叠 1mm 报 PENETRATION）

```python
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "3d"))
import printcheck as PC
from families import family_mesh

def test_good_wedge_passes():
    v, f = family_mesh("wedge-std", {"w": 1.0, "h": 0.4, "d": 1.0,
                                     "proud": 0.006, "back": 0.3,
                                     "hw_b": 6.0, "hw_t": 5.9})
    r = PC.check_stone(v, f, scale=1/50.0, min_wall_print_mm=1.2)
    assert r["ok"] and not r["issues"]

def test_open_box_non_manifold():
    v = [(0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,1),(1,0,1),(1,1,1),(0,1,1)]
    f = [(0,1,2,3),(4,5,6,7),(0,1,5,4),(1,2,6,5)]   # 缺两面
    r = PC.check_stone(v, f, scale=1.0, min_wall_print_mm=1.2)
    assert any("NON_MANIFOLD" in i for i in r["issues"])

def test_thin_wall_at_scale():
    v, f = family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.03})  # 3cm@1:50=0.6mm
    r = PC.check_stone(v, f, scale=1/50.0, min_wall_print_mm=1.2)
    assert any("THIN_WALL" in i for i in r["issues"])

def test_penetration():
    a = family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.5})
    r = PC.gap_check([(0,0,0), a], [(0.999,0,0), a], tol_mm=0.5, scale=1/50.0)
    assert PC._codes(r)["PENETRATION"]  # gap_check 现返 {ok,issues:[{code,detail}]}
```

- [ ] **Step 2-4**：实现（manifold=边计数==2；thin=任一维 bbox*scale*1000 < min_wall；penetration=AABB 重叠且重叠深>tol；self-intersect 用逐面 AABB 粗筛+三角相交精检，合成自交盒必报）
- [ ] **Step 5: Commit** `feat(e30): P1-T5 printcheck(流形/自交/壁厚@scale/穿透)`

---

### Task 6: export_print.py（inset 间隙 + STL/3MF + manifest + coupon）

**Files:** Create `3d/export_print.py`；Test `tests/test_p1_export.py`

- [ ] **Step 1: 失败测试**：inset 后块 bbox 收缩=2×clearance（每接触面）；STL 文件头/三角数正确；manifest 含 family×count 分批；coupon 组 3 间隙楔形接头存在

```python
def test_inset_shrinks_not_expands():
    v, f = family_mesh("wedge-std", {"w": 1.0, "h": 0.4, "d": 1.0,
                                     "proud": 0.006, "back": 0.3,
                                     "hw_b": 6.0, "hw_t": 5.9})
    v2 = E.inset(v, clearance_mm=0.3)
    xs1 = [p[0] for p in v]; xs2 = [p[0] for p in v2]
    assert (max(xs1) - min(xs1)) - (max(xs2) - min(xs2)) == pytest.approx(0.0006, abs=1e-6)

def test_manifest_family_batches(tmp_path):
    led = _two_stone_same_family_ledger()
    man = E.export_ledger(led, _mesh_fn, str(tmp_path), scale=1/50.0)
    fam = man["families"]["wedge-std"]
    assert fam["count"] == 2 and fam["stl"] .endswith(".stl")
```

- [ ] **Step 2-4**：实现 inset（每维向内收 clearance/1000；FIT_TIGHT=0.15/NORMAL=0.3/LOOSE=0.5mm）；STL 二进制写三角（quad 剖分）；3MF 用 zip+XML 最小实现；manifest.json（family→{count, stl, volume_cm3}、batch 按 220×220mm 床贪心装箱）；coupon_set 出 0.15/0.3/0.5 三间隙楔形对
- [ ] **Step 5: Commit** `feat(e30): P1-T6 导出(inset吃公差/STL+3MF/manifest分批/coupon组)`

---

### Task 7: build_scene2 三模式 + GN 装配

**Files:** Modify `3d/build_scene2.py`；Test：既有全门 + 新增 `tests/test_p1_scene.py`（--emit-lib 产 families.blend 且族数==ledger 族数；--layout 产 out/e30_bridge.blend 且 Object 数 < 50（GN 实例）；--proxy 与旧合并网格 L2 等价）

- [ ] **Step 1-4**：`--emit-lib`：遍历 ledger 族 → 每族一 mesh object 入 COL_FAMILIES → save families.blend；`--layout`：link families + 每石一 GN instance point（attribute: sid/fam/stage/mat）+ collection SPAN01..17/ABUT_E/ABUT_W/TEMP_WORKS；`--proxy`：现行合并网格路径（默认保留）
- [ ] **Step 5: Commit** `feat(e30): P1-T7 场景三模式(emit-lib/layout GN实例/proxy回归)`

---

### Task 8: P1A 中央孔 vertical slice 试印包（G2 门）

**Files:** Create `3d/p1a_slice.py`；产出 `out/print/central_slice/`（STL×N + manifest + 装配图 PNG + 切片说明 md）

- [ ] **Step 1-4**：取 ARCH09 全部面石+背衬+core cells（约 400 石）→ printcheck 全过 → export（FIT_NORMAL）→ 装配图（正射 ortho 投影 id 标注）→ 报告：族数/实例数/总体积/最长打印时长估（0.4mm 喷嘴 FDM 经验 12cm³/h）
- [ ] **Step 5: Commit** `feat(e30): P1-T8 中央孔试印包(G2门: 全石流形+壁厚+分批+装配图)`

---

## 自审记录
1. **Spec 覆盖**：§2 三层 truth volume=T3/T4；§3 schema+id 纪律=T1；§3.2 族库+缓存=T2；§3.2 间隙两级=T3(历史)+T6(制造)；§4 五模块=T1-T7；§5 GN 架构=T7；§6 测试=T1-T8 各带；§7 接口承诺=T1(support_edges/stage_hint)+T6(scale_params/batch)；§8 风险（丁石不布尔=T3 深度规则；雕刻件=T8 标记不修；曲线未封版=已过 G1）
2. **占位扫描**：无 TBD；每 step 有代码或精确命令
3. **类型一致**：family_mesh 签名 T2 定义 T3/T5/T6 消费一致；new_stone 参数序 T1 定义 T3 消费一致；inset(verts, clearance_mm) T6 内定义内消费
