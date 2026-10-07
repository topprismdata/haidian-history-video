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
    r = PC.check_stone(v, f, scale=1/50.0, min_wall_mm=1.2)
    assert r["ok"] and not r["issues"]

def test_open_box_non_manifold():
    v = [(0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,1),(1,0,1),(1,1,1),(0,1,1)]
    f = [(0,1,2,3),(4,5,6,7),(0,1,5,4),(1,2,6,5)]   # 缺两面
    r = PC.check_stone(v, f)
    assert any("NON_MANIFOLD" in i for i in r["issues"])

def test_thin_wall_at_scale():
    v, f = family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.03})  # 3cm@1:50=0.6mm
    r = PC.check_stone(v, f, scale=1/50.0, min_wall_mm=1.2)
    assert any("THIN_WALL" in i for i in r["issues"])

def test_penetration():
    a = family_mesh("slab", {"w": 1.0, "d": 1.0, "h": 0.5})
    r = PC.gap_check([(0,0,0), a], [(0.999,0,0), a], tol_mm=0.5, scale=1/50.0)
    assert any("PENETRATION" in i for i in r)
```

- [ ] **Step 2-4**：实现（manifold=边计数==2；thin=任一维 bbox*scale*1000 < min_wall；penetration=AABB 重叠且重叠深>tol；self-intersect 用逐面 AABB 粗筛+三角相交精检，合成自交盒必报）
- [ ] **Step 5: Commit** `feat(e30): P1-T5 printcheck(流形/自交/壁厚@scale/穿透)`
