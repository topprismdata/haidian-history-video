# Task 2b: 闭合差归因与冲突登记（G3 增设, 在 T4 前完成）

> 本文件由计划自动抽取，是该任务的**唯一需求来源**，其中数值必须逐字照用。

### Task 2b: 闭合差归因与冲突登记（G3 增设, 在 T4 前完成）

**Files:**
- Modify: `3d/facts.py`（BRIDGE_ABUT 定稿）、`3d/refs/FACTS.md`（冲突登记表）

**Interfaces:**
- Consumes: L1 的 MET_CLOSURE 判据
- Produces: 闭合差归因（已闭环, 见上述），或修正墩宽/跨序，或桥长口径修正），每个数值冲突一个 ID（C1 闭合差、C2 宽度6.56vs8、C3 高7vs7.75），状态 ∈{open,resolved,wontfix+理由}

- [x] **Step 0: 已闭环**——T3 复核发现 -2.50m 是计划稿算术错误(误按 15 墩); 17 孔间为 16 墩, 107.3+40.0+2.7=150.0 精确闭合。判据公式改用 `(N_SPAN-1)`, 基线应恒绿。

- [ ] **Step 1**: 用 MET_CLOSURE 输出归因分析写入 FACTS.md 冲突登记表；BRIDGE_ABUT 定稿回填 facts
- [ ] **Step 2**: pytest 全绿（含 baseline）；Commit `feat(e30): T2b 闭合差归因+冲突登记`

---

