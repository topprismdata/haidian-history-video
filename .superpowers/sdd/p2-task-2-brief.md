# P2 建造序列器 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 5935 石 + 17 副券架排成史实可挂账、力学可验证的建造序列（sequence.json + event_ledger.json），G3 三层力学门（①DAG ③压力线 ④推力包络不平衡）全 PASS 后交 P3。

**Architecture:** centering.py 生成券架（纯 python quad 网格，注册进 event_ledger 不进石账）；sequencer.py 按 R0-R7 规则+frontier 状态机产出事件流与 stage 分组；g3_check.py 逐事件 snapshot 做支撑活跃/压力线/墩不平衡三检，acceptance=环+锁固肩、robustness=裸环双 case；ledger schema 升 v2（capacity_curve+inferred_construction 枚举）带迁移。

**Tech Stack:** Python 3.9.6 纯 stdlib+numpy（无 bpy——centering/sequencer/g3 全 blender-free，可测性优先）；scipy 不用（压力线纯 python 实现）。

## Global Constraints
- Python 3.9.6：`Optional[X]`、无 match；测试 blender-free
- 石账纯度：券架/事件永不进 stone ledger（5935 真源）
- 冻结防污染：③ 双 case 都不过 → raise 停报主控，禁改封卷几何参数
- 三红线：不发明 μ/cot 类伪史料常数；ε=0.15/MIN_HOLD=3 标 [工程参数·敏感性]；史料引用必须 G0 编号
- 中文 commit `feat(e30): P2-Tn ...`；全门回归：e30 tests / bridge3d 312 / L2 / 33 断言 / freeze 逐位（P2 零触本体路径）
- 隔离树 `/tmp/e30_p2/` 先行

## 文件结构
| 文件 | 职责 |
|---|---|
| `3d/ledger.py` | schema v2：EVIDENCE+inferred_construction；support_edge 支持 capacity_curve；`migrate_v1_to_v2()` |
| `3d/centering.py` | 券架几何生成（bents/ledger-walings/rib 板/wedges）+ centering 表 |
| `3d/events.py` | 事件词表+event_ledger schema+validate_event_ledger |
| `3d/sequencer.py` | 规则引擎→event 流+stage 分组→sequence.json |
| `3d/g3_check.py` | snapshot 状态机+①活跃+③压力线+④H 包络/不平衡/λ/核距 |
| `3d/narration.py` | beats 表+禁词 lint |
| `tests/test_p2_*.py` ×6 | 各模块 TDD |

---

## Global Constraints
- Python 3.9.6：`Optional[X]`、无 match；测试 blender-free
- 石账纯度：券架/事件永不进 stone ledger（5935 真源）
- 冻结防污染：③ 双 case 都不过 → raise 停报主控，禁改封卷几何参数
- 三红线：不发明 μ/cot 类伪史料常数；ε=0.15/MIN_HOLD=3 标 [工程参数·敏感性]；史料引用必须 G0 编号
- 中文 commit `feat(e30): P2-Tn ...`；全门回归：e30 tests / bridge3d 312 / L2 / 33 断言 / freeze 逐位（P2 零触本体路径）
- 隔离树 `/tmp/e30_p2/` 先行

### Task 2: centering.py 券架生成器

**Files:** Create `3d/centering.py`；Test `tests/test_p2_centering.py`

**Interfaces:** Produces: `build_centering(arch_idx, span, ring_t, lift, springer_z, deck_z_fn) -> dict`：`{id:"CEN-ARCH09", parts:[{kind:"post"|"waling"|"rib"|"wedge", verts:[...], faces:[(quad)...], bbox}], wedge_events:int, footprint_polys:[[(x,z)...]]}`；纯 python 六面体 quad（无 bpy）；排架柱间距 1.2m、柱底 BODY_BOTTOM、柱顶贴 extrados+30mm 楞木网、rib 板沿弧、卸架楔对数=每柱头 1 对（wedge_events=柱头对数）。
Consumes: facts（SPANS/rise_ratio/spandrel/BODY_BOTTOM）。

- [ ] Step1 失败测试：中央孔 span 8.5 → 柱排数=⌈8.5/1.2⌉+1=8；所有 part 闭合六面体（每 part 6 面 8 顶点 12 边各属 2 面）；rib 板 z 上缘 ≥ extrados+0.03−tol 且 ≤ extrados+0.06；wedge_events==柱头对数>0；footprint_polys 投影覆盖孔跨×环带区（面积>0）；端孔（span 4.5, crown 2.23）柱高 ≤ crown+ring_t+0.1。
- [ ] Step2 红 → Step3 实现 → Step4 绿 → Step5 commit `feat(e30): P2-T2 券架生成器(排架/楞木/券胎板/卸架楔, 纯python闭合体)`
