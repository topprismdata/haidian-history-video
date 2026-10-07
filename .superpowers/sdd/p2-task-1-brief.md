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

### Task 1: ledger schema v2（capacity_curve + 枚举 + 迁移）

**Files:** Modify `3d/ledger.py`；Test `tests/test_p2_ledger_v2.py`

**Interfaces:** Produces: `EVIDENCE` 含 `"inferred_construction"`；`support_edge` 新形 `{target,type,capacity_curve:[[event_id,float],...],contact}`（旧 `{active_from,active_to}` 经 `migrate_v1_to_v2(led)` 转 `capacity_curve=[[active_from,1.0],[active_to,0.0]]`）；`validate_ledger` 认新形拒旧形（迁移后）；`edge_capacity(edge, event_seq:int) -> float`（按 curve 的 event 序号插值，curve 外=端值）。
Consumes: P1 ledger 全部现有 API 不破（G2 工件重放仍绿）。

- [ ] Step1 失败测试：旧 v1 报告经 migrate 后 validate==[]；`edge_capacity` 在 curve 三点 [(0,1.0),(5,0.5),(9,0.0)] 上 seq=2→0.75/seq=7→0.25/seq=20→0.0；未迁移 v1 边被 validate 报 `SUPPORT_SHAPE`；evidence=inferred_construction 合法、invented 非法。
- [ ] Step2 红 → Step3 实现（EVIDENCE 元组追加；validate 的 support_edges 分支改查 capacity_curve 列表单调不增；migrate 函数；edge_capacity 线性插值）→ Step4 绿（含 P1 既有 ledger 测试零回归）→ Step5 commit `feat(e30): P2-T1 ledger schema v2(capacity_curve+inferred_construction+迁移)`
