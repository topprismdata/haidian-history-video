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

### Task 6: g3_check ③压力线（双 case）

**Files:** Modify `3d/g3_check.py`；Test `tests/test_p2_g3_thrust.py`

**Interfaces:** Produces: `pressure_line(ring_stones, extra_loads, band_in_out_fns, H_range) -> dict{feasible:bool, H:[min,max], polyline:[(x,z)...]}`——刚块链法：券石按楔块分割，给定 H 逐块递推合力（重心+面法向摩擦锥无穷大即纯压），压力线出入环带即不可行；acceptance=RING+pre-strike 石重加于对应块顶，robustness=仅 RING；扫 H 网格 0.1-1.2×qL²/8f 求可行区间。
- [ ] Step1 失败测试：半圆均载解析解对照（H≈qL²/8f ±5%）；环带加厚（内外距×1.5）可行区间变宽；把某楔块重心外移 0.3m → feasible 翻假（负控）；中央孔真账 acceptance feasible=True 且 robustness 记录不判红。
- [ ] Step2 红 → Step3 实现 → Step4 绿 → Step5 commit `feat(e30): P2-T6 G3③压力线刚块链(acceptance/robustness双case)`
- [ ] **红线**：中央孔 acceptance 不过 → `raise G3_FROZEN_GEOMETRY_CONFLICT`（不许调封卷参数自救）
