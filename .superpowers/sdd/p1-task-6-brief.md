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
