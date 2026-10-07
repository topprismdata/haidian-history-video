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
