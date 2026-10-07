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
