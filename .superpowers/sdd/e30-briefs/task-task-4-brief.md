# Task 4: bridge_geom2 从 facts 取数（消灭字面尺寸）

> 本文件由计划自动抽取，是该任务的**唯一需求来源**，其中数值必须逐字照用。

### Task 4: bridge_geom2 从 facts 取数（消灭字面尺寸）

**Files:**
- Modify: `e30_shikongqiao_video/3d/bridge_geom2.py`（头部常量区，约 15-46 行）
- Create: `e30_shikongqiao_video/tests/test_no_literals.py`

**Interfaces:**
- Consumes: facts（Task 1/2）
- Produces: bridge_geom2 模块常量全部来自 facts；`G.*` 属性名不变（build_scene2 零改动）

- [ ] **Step 1: 替换常量区为 facts 导入（保留 SPANS/PIER_X 递推与 deck_z 不动）**

把 `BRIDGE_LEN, N_SPAN = 150.0, 17` 至 `SPRING_BASE = SPRINGER` 的字面常量区替换为（`SPRING_BASE` 亦改为消费 SPRINGER）：

```python
# ── 单一事实来源: 数值一律来自 facts.py(本体节, M2.5 冻结) ──
import facts as _F
BRIDGE_LEN, N_SPAN = _F.BRIDGE_LEN, _F.N_SPAN
DECK_UP_W, DECK_DOWN_W = _F.DECK_UP_W, _F.DECK_DOWN_W
SPRINGER = _F.SPRINGER
ARCH_RATIO = _F.ARCH_RATIO
RING_T = _F.RING_T
PIER_W = _F.PIER_W
PIER_MAIN_W = _F.PIER_MAIN_W
PIER_FOUND_W = _F.PIER_FOUND_W
PIER_MAIN_W_C = _F.PIER_MAIN_W_C
PIER_FOUND_W_C = _F.PIER_FOUND_W_C
BRIDGE_ABUT = _F.BRIDGE_ABUT   # 尺寸决策只在 facts 一处做(T2b 归因后改); 生成器纯消费
SPAN_DISTINCT = list(_F.SPAN_DISTINCT)   # G1 更名: '半跨'语义数学上不可能(9值×2-1=17孔)
DECK_Z_AT_PIER = list(_F.DECK_Z_AT_PIER)
DECK_Z_END, DECK_Z_TOP = _F.DECK_Z_END, _F.DECK_Z_TOP
from assumptions import BODY_BOTTOM, MESH_TOL   # G1 分家: 建模假定/判据参数不属 facts
```

并删除原"券形定论"注释块下 `ARCH_RATIO = 0.50` 一行（注释保留移到 facts.py，已在 Task 1 完成）。文件头 docstring 里"参数沿用 GPT v3 工作值表"改为"参数来自 facts.py（单一事实来源）"。

**桥台值不在此任务改**（G3-阻断项采纳）：BRIDGE_ABUT 1.35→2.00 是尺寸决策，必须等 T2b 闭合差归因后由 facts 给出（推导值可能是 2.6m），**generator 是纯消费者，禁止为凑 150m 自行选值**。本任务只把递推改为消费 `facts.BRIDGE_ABUT`（T1 起该名即存在，初值 1.35 保持现状+`[待核]`），递推行改为：

```python
for i in range(N_SPAN + 1):
    w = BRIDGE_ABUT if i in (0, N_SPAN) else PIER_W
```

删除旧 `BRIDGE_ABUT = 1.35` 字面行（值进 facts）。T2b 裁决后只改 facts 一处。

- [ ] **Step 2: 写无字面尺寸测试（AST 扫 float 字面量，白名单外即 fail）**

`e30_shikongqiao_video/tests/test_no_literals.py`：

```python
# -*- coding: utf-8 -*-
import ast, os

HERE = os.path.join(os.path.dirname(__file__), "..", "3d")
# 白名单治理: 只准加无量纲容差/循环参量; 任何带单位的尺寸一律进 facts。
# 0.5 已被移出白名单(调度者 2026-10-04 修正): 它正是 ARCH_RATIO 的值,
# 留在白名单里等于允许"券形判据的核心数字"以字面量形式藏回生成器而不报错。
ALLOW = {0.0, 1.0, 2.0, -1.0, 1e-9}

def _floats(path):
    tree = ast.parse(open(os.path.join(HERE, path), encoding="utf-8").read())
    out = set()
    for nd in ast.walk(tree):
        if isinstance(nd, ast.Constant) and isinstance(nd.value, float):
            out.add(nd.value)
    return out

def test_geom_no_dimension_literals():
    bad = sorted(f for f in _floats("bridge_geom2.py") if f not in ALLOW)
    assert not bad, "bridge_geom2.py 出现白名单外字面数: %s" % bad


# ── 负控制: 这条测试本身会不会恒真? ──
# 若把 0.5 重新放进白名单, ARCH_RATIO 就能以字面量形式藏回生成器而测试全绿。
# 用 facts 的实际值反证: 凡是"恰好等于某个 facts 常量"的字面量, 一律不允许, 无论它在不在白名单。
def test_no_literal_equal_to_any_fact_value():
    import sys
    sys.path.insert(0, HERE)
    import facts as F
    fact_vals = {}
    for n in dir(F):
        if n.startswith("_") or n in ("SOURCES", "RESEARCH_DONE"):
            continue
        v = getattr(F, n)
        if isinstance(v, float):
            fact_vals.setdefault(v, []).append(n)
        elif isinstance(v, (list, tuple)):
            for x in v:
                if isinstance(x, float):
                    fact_vals.setdefault(x, []).append(n)
    bad = []
    for f in _floats("bridge_geom2.py"):
        if f in fact_vals and f not in ALLOW:
            bad.append((f, fact_vals[f]))
    assert not bad, "bridge_geom2.py 出现与 facts 常量相同的字面量(应改为引用 facts): %s" % bad
```

- [ ] **Step 3: 跑全部 facts/L1/无字面 测试 + Blender 构建冒烟**

Run: `cd /Volumes/macstudio/video-projects && python3 -m pytest e30_shikongqiao_video/tests -v`
Expected: 全过
Run: `cd /Volumes/macstudio/video-projects/e30_shikongqiao_video/3d && blender -b --factory-startup --python build_scene2.py 2>&1 | grep -E "SAVED|Error"`
Expected: `SAVED v2`

- [ ] **Step 4: Commit**

```bash
cd /Volumes/macstudio/video-projects
git add e30_shikongqiao_video/3d/bridge_geom2.py e30_shikongqiao_video/tests/test_no_literals.py
git commit -m "refactor(e30): bridge_geom2 常量区接入 facts 单一来源, AST 禁字面尺寸"
```

---

