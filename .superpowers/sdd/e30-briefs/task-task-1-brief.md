# Task 1: facts.py 本体节骨架 + 来源完备性测试

> 本文件由计划自动抽取，是该任务的**唯一需求来源**，其中数值必须逐字照用。

### Task 1: facts.py 本体节骨架 + 来源完备性测试

**Files:**
- Create: `e30_shikongqiao_video/3d/facts.py`
- Create: `e30_shikongqiao_video/3d/assumptions.py`（假设层: 判据参数+建模假定, 不参与冻结）
- Create: `e30_shikongqiao_video/tests/test_facts.py`（新建目录）

**Interfaces:**
- Produces(facts): `BRIDGE_LEN, N_SPAN, DECK_UP_W, DECK_DOWN_W, PUBLISHED_GENERAL_WIDTH, PUBLISHED_BRIDGE_HEIGHT, DECK_Z_TOP, DECK_Z_END, SPRINGER, ARCH_RATIO, RING_T, PIER_W, PIER_MAIN_W, PIER_FOUND_W, PIER_MAIN_W_C, PIER_FOUND_W_C, BRIDGE_ABUT(桥台长, T2b 裁决定稿), SPAN_DISTINCT(list[9] 完整净跨,对称展开为17), DECK_Z_AT_PIER(list[9])`；注册表 `SOURCES: dict[str, tuple[str, str]]`；旗标 `RESEARCH_DONE: bool`
- Produces(assumptions): `BODY_BOTTOM, MESH_TOL, CIRCLE_FIT_RTOL, NSEG_ARC, NSEG_X`（G2: 废 CROWN_CLEARANCE_MIN; G3: 离散段数是实现参数非事实）
- Consumes: 无（G1 修订: 来源五级 测绘/档案/官方/图像推导/工作值; HALF_SPANS 更名 SPAN_DISTINCT——"半跨"语义数学上不可能, 9 值系完整净跨对称展开, 总水路 107.3m+墩台≈150m 才自洽）

- [ ] **Step 1: 写 facts.py（当前值全部标 [待核] 或 [工作值]，数值=现脚本值，不改数）**

```python
# -*- coding: utf-8 -*-
"""E30 十七孔桥 尺寸事实清单（单一来源）。

等级: 测绘 > 档案 > 官方 > 图像推导 > 工作值。
"待核"只允许存在于 RESEARCH_DONE=False 期间。
冻结(M2.5)只锁非[工作值]条目; 改锁死条目必须写 3d/refs/body_changelog.md 并重跑本体判据。
禁令: 未标定照片不得产生绝对米制尺寸; 超分(ESRGAN)结果禁止进计量链; GPT 聊天记录不算来源。
Z 基准: Z=0 = 常水位水面(建模约定)。
"""

# --- 研究轮旗标: M0 完成后置 True ---
RESEARCH_DONE = False

# --- 全局 ---
BRIDGE_LEN = 150.0        # [官方] 北京市公园管理中心专题页"长150米"; 中新网2025/visitbeijing 多源一致
N_SPAN = 17               # [官方] 官方页明示17个券洞(非"桥名"推知, G1 修正)

# --- 桥面 ---
DECK_Z_TOP = 7.75         # [工作值] 现脚本值(GPT建议); 官方"高7米"基准面未注明, 见 PUBLISHED_BRIDGE_HEIGHT
DECK_Z_END = 5.05         # [工作值] 现脚本值
DECK_UP_W = 6.56          # [官方] 公园管理中心2019: "桥面上宽6.56米"
DECK_DOWN_W = 14.6        # [官方] 同页: "桥面下宽14.6米"
PUBLISHED_GENERAL_WIDTH = 8.0   # [官方] 2018页"宽八米"=通俗概括; 与 DECK_UP_W 口径冲突, conflict_unresolved
PUBLISHED_BRIDGE_HEIGHT = 7.0   # [官方] "高7米"; 测点/基准面未注明, 禁止映射 DECK_Z_TOP

# --- 券洞 ---
ARCH_RATIO = 0.50         # [图像推导] 近正面原始照目视近正对孔宽高比≈1.00; ESRGAN 版测量已退出计量链, 待测绘升级
SPRINGER = 2.50           # [工作值] 现脚本值
RING_T = 0.40             # [工作值] 现脚本值
SPAN_DISTINCT = [4.50, 4.90, 5.40, 5.90, 6.40, 6.90, 7.40, 8.00, 8.50]  # [工作值] 9个完整净跨(对称展开17孔), 总水路107.3m+墩台≈150m 自洽; 中央孔8.50无公开测绘值(G1复核)

# --- 墩与桥台 ---
PIER_W = 2.50             # [待核] 墩颈
PIER_MAIN_W = 2.80        # [待核] 水线上主墩
PIER_FOUND_W = 3.10       # [待核] 基础外扩
PIER_MAIN_W_C = 2.90      # [待核] 中央区加重
PIER_FOUND_W_C = 3.20     # [待核] 中央区基础
BRIDGE_ABUT = 1.35         # [待核] 现脚本生效值; T2b 闭合归因后定稿(候选: 2.00 GPT设计 / 2.60 闭合推导)

# --- 桥面纵坡控制点 ---
DECK_Z_AT_PIER = [5.30, 5.53, 5.82, 6.11, 6.40, 6.69, 6.97, 7.29, 7.55]  # [待核] 现脚本值

SOURCES = {
    "BRIDGE_LEN": ("官方", "北京市公园管理中心专题页; 中新网2025-12多源一致"),
    "N_SPAN": ("官方", "官方页明示17券洞"),
    "DECK_Z_TOP": ("工作值", "现脚本值; 官方高7米基准未注明"),
    "DECK_Z_END": ("工作值", "现脚本值"),
    "DECK_UP_W": ("官方", "公园管理中心2019: 桥面上宽6.56米"),
    "DECK_DOWN_W": ("官方", "同页: 桥面下宽14.6米"),
    "PUBLISHED_GENERAL_WIDTH": ("官方", "2018页: 宽八米; 与6.56口径冲突并存"),
    "PUBLISHED_BRIDGE_HEIGHT": ("官方", "高7米; 测点未注明, 禁映射DECK_Z_TOP"),
    "ARCH_RATIO": ("图像推导", "近正面原始照比例假设; ESRGAN退出计量链"),
    "SPRINGER": ("工作值", "现脚本值"),
    "RING_T": ("工作值", "现脚本值"),
    "SPAN_DISTINCT": ("工作值", "GPT冻结表, 中央孔8.50无公开测绘值"),
    "PIER_W": ("工作值", "现脚本值"),
    "PIER_MAIN_W": ("工作值", "现脚本值"),
    "PIER_FOUND_W": ("工作值", "现脚本值"),
    "PIER_MAIN_W_C": ("工作值", "现脚本值"),
    "PIER_FOUND_W_C": ("工作值", "现脚本值"),
    "BRIDGE_ABUT": ("待核", "现生效1.35; T2b闭合归因后定稿"),
    "DECK_Z_AT_PIER": ("工作值", "现脚本值"),
}
```

`assumptions.py`（假设层，全部不冻结）：

```python
# -*- coding: utf-8 -*-
"""建模假定与判据参数。非文物事实, 不进冻结; 改动须记录。
G2 修订: 废除无据的 CROWN_CLEARANCE_MIN=0.30(GPT聊天值), 换成结构自洽判据:
  拱背(extrados)=拱腹+RING_T 必须低于桥面 —— 这是拓扑必需, 不是经验常数。"""
BODY_BOTTOM = -2.20          # 桥体底面(水下不可见), 建模工作值
MESH_TOL = 0.005             # 网格数值容差(5mm), 券石入净空判据的 epsilon
CIRCLE_FIT_RTOL = 0.01       # 圆拟合残差/半径 上限(G2: f/l 只是必要条件, 半圆须残差证明)
NSEG_ARC = 40                # 券弧离散段数(实现参数, 非文物事实)
NSEG_X = 240                 # 桥体纵向分段(实现参数)
```

- [ ] **Step 2: 写来源完备性测试（先跑，必须 FAIL——RESEARCH_DONE=False 时只要求 SOURCES 覆盖；Task 2 后升级）**

`e30_shikongqiao_video/tests/test_facts.py`：

```python
# -*- coding: utf-8 -*-
import os, sys, importlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "3d"))
import facts

def _public_constants():
    out = []
    for n in dir(facts):
        if n.startswith("_") or n in ("SOURCES", "RESEARCH_DONE"):
            continue
        v = getattr(facts, n)
        if isinstance(v, (int, float, list)):
            out.append(n)
    return sorted(out)

def test_every_constant_has_source():
    for n in _public_constants():
        assert n in facts.SOURCES, "缺来源登记: %s" % n

def test_source_levels_valid():
    ok = {"测绘", "文献", "实拍", "工作值", "待核"}
    for n, (lvl, note) in facts.SOURCES.items():
        assert lvl in ok, "%s 等级非法: %s" % (n, lvl)
        assert note.strip(), "%s 出处说明为空" % n

def test_no_pending_after_research():
    if not facts.RESEARCH_DONE:
        return  # 研究轮前允许 待核
    pend = [n for n, (l, _) in facts.SOURCES.items() if l == "待核"]
    assert not pend, "研究完成仍有待核: %s" % pend

def test_span_distinct_shape():
    assert len(facts.SPAN_DISTINCT) == 9
    assert len(facts.DECK_Z_AT_PIER) == 9
```

- [ ] **Step 3: 跑测试确认 PASS（本任务只要求 SOURCES 覆盖）**

Run: `cd /Volumes/macstudio/video-projects && python3 -m pytest e30_shikongqiao_video/tests/test_facts.py -v`
Expected: 4 passed

- [ ] **Step 4: Commit**

```bash
cd /Volumes/macstudio/video-projects
git add e30_shikongqiao_video/3d/facts.py e30_shikongqiao_video/tests/test_facts.py
git commit -m "feat(e30): facts.py 本体节骨架+来源完备性测试(全[待核]/[工作值])"
```

---

