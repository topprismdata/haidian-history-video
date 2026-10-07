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
