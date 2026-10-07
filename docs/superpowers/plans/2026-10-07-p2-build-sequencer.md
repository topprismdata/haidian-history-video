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

### Task 1: ledger schema v2（capacity_curve + 枚举 + 迁移）

**Files:** Modify `3d/ledger.py`；Test `tests/test_p2_ledger_v2.py`

**Interfaces:** Produces: `EVIDENCE` 含 `"inferred_construction"`；`support_edge` 新形 `{target,type,capacity_curve:[[event_id,float],...],contact}`（旧 `{active_from,active_to}` 经 `migrate_v1_to_v2(led)` 转 `capacity_curve=[[active_from,1.0],[active_to,0.0]]`）；`validate_ledger` 认新形拒旧形（迁移后）；`edge_capacity(edge, event_seq:int) -> float`（按 curve 的 event 序号插值，curve 外=端值）。
Consumes: P1 ledger 全部现有 API 不破（G2 工件重放仍绿）。

- [ ] Step1 失败测试：旧 v1 报告经 migrate 后 validate==[]；`edge_capacity` 在 curve 三点 [(0,1.0),(5,0.5),(9,0.0)] 上 seq=2→0.75/seq=7→0.25/seq=20→0.0；未迁移 v1 边被 validate 报 `SUPPORT_SHAPE`；evidence=inferred_construction 合法、invented 非法。
- [ ] Step2 红 → Step3 实现（EVIDENCE 元组追加；validate 的 support_edges 分支改查 capacity_curve 列表单调不增；migrate 函数；edge_capacity 线性插值）→ Step4 绿（含 P1 既有 ledger 测试零回归）→ Step5 commit `feat(e30): P2-T1 ledger schema v2(capacity_curve+inferred_construction+迁移)`

---

### Task 2: centering.py 券架生成器

**Files:** Create `3d/centering.py`；Test `tests/test_p2_centering.py`

**Interfaces:** Produces: `build_centering(arch_idx, span, ring_t, lift, springer_z, deck_z_fn) -> dict`：`{id:"CEN-ARCH09", parts:[{kind:"post"|"waling"|"rib"|"wedge", verts:[...], faces:[(quad)...], bbox}], wedge_events:int, footprint_polys:[[(x,z)...]]}`；纯 python 六面体 quad（无 bpy）；排架柱间距 1.2m、柱底 BODY_BOTTOM、柱顶贴 extrados+30mm 楞木网、rib 板沿弧、卸架楔对数=每柱头 1 对（wedge_events=柱头对数）。
Consumes: facts（SPANS/rise_ratio/spandrel/BODY_BOTTOM）。

- [ ] Step1 失败测试：中央孔 span 8.5 → 柱排数=⌈8.5/1.2⌉+1=8；所有 part 闭合六面体（每 part 6 面 8 顶点 12 边各属 2 面）；rib 板 z 上缘 ≥ extrados+0.03−tol 且 ≤ extrados+0.06；wedge_events==柱头对数>0；footprint_polys 投影覆盖孔跨×环带区（面积>0）；端孔（span 4.5, crown 2.23）柱高 ≤ crown+ring_t+0.1。
- [ ] Step2 红 → Step3 实现 → Step4 绿 → Step5 commit `feat(e30): P2-T2 券架生成器(排架/楞木/券胎板/卸架楔, 纯python闭合体)`

---

### Task 3: events.py 事件账本

**Files:** Create `3d/events.py`；Test `tests/test_p2_events.py`

**Interfaces:** Produces: `EVENT_TYPES=("PLACE_STONE","CLOSE_RING","HOLD_EVENT","DECENTER_START","WEDGE_RELEASE","CENTERING_CLEAR","ADD_FILL")`；`new_event(seq:int, hole, etype, stone_id=None, prereq:[seq...], affects:[[edge_ref,[ev,f]...]], load_lambda=None, evidence="R?:n", grade="fact|context|inferred")`；`validate_event_ledger(ev_led, centering_ids, stone_ids) -> [str]`（seq 严格递增、etype 词表、prereq 指向更小 seq、CENTERING_CLEAR 前必须 DECENTER_START、WEDGE_RELEASE 单调、引用的 stone/centering 存在、每孔 CLOSE_RING 恰一次且其 prereq 含该孔全部 RING 石）。

- [ ] Step1 失败测试：合法 6 事件链绿；乱序 seq 红；CLEAR 无 START 红；CLOSE_RING 缺一块券石 prereq 红；未知 etype 红；grade=虚构值红。
- [ ] Step2 红 → Step3 实现 → Step4 绿 → Step5 commit `feat(e30): P2-T3 事件账本schema+校验器`

---

### Task 4: sequencer.py 规则引擎

**Files:** Create `3d/sequencer.py`；Test `tests/test_p2_sequencer.py`

**Interfaces:** Consumes: ledger（P1 全账含 support_edges）、centering 表、events。Produces: `build_sequence(ledger, centerings, eps=0.15, min_hold=3) -> {"events":[...], "sequence":[{id,stage,event_range,depends_on,centering_id,evidence}], "frontier_trace":[{hole,state,at_seq}]}`；规则：R1 墩 z 升序；R2 孔内 RING 依赖 CEN 立架事件；R3 券石按弧参数 θ 两侧交替且每前缀满足 |W_L−W_R|/(W_L+W_R)≤eps；R4 CLOSE_RING 后 min_hold 个 HOLD_EVENT 才 DECENTER_START，WEDGE_RELEASE×k 逐档 λ；R5a 环肩咬合石（params.clipped_by=="ring_band"∧非占架冲突）排 CLEAR 前、CLOSE 后；R5b 其余肩/背/胞排 CLEAR 后；R6 孔 frontier 状态机+跨孔允许组合表（禁：相邻孔同时 DECENTERING；禁：孔 i DECENTERING 而 i±1 状态 < CLOSED_SUPPORTED——即"跳孔落架"）；R7 PAVING→RAIL/POST→CARVE 全局最后。stage=连续事件的叙事分组（目标 200-600）。

- [ ] Step1 失败测试（合成 3 孔微账）：事件序满足全部 R 规则（逐规则断言）；frontier 轨迹合法（非法组合表 0 命中）；每石恰一次出现；stage 数在 [50,600]（合成）；R3 前缀平衡度逐事件核；负控预演：手工把一侧三石前置→构造器 raise `R3_IMBALANCE`。
- [ ] Step2 红 → Step3 实现 → Step4 绿 → Step5 commit `feat(e30): P2-T4 序列器(R0-R7规则+frontier状态机+平衡度前缀)`

---

### Task 5: g3_check.py ①支撑活跃 + snapshot 状态机

**Files:** Create `3d/g3_check.py`；Test `tests/test_p2_g3_dag.py`

**Interfaces:** Produces: `snapshots(events, ledger) -> iter[Snapshot]`（Snapshot={seq, present:set, capacity:{edge_ref:f}, by_hole}）；`check_dag(snap) -> [viol]`：每石 present 时其至少一支撑边 capacity>0（stone 支撑=下方石 present；centering=曲线值；fill/foundation 规则）；`run_g3(events, ledger, centerings) -> report dict`（串 ①③④，Task 6/7 填充）。
- [ ] Step1 失败测试：正常链 0 违例；抽走某 RING 石的 centering 支撑（curve 置 0 提前）→ `UNSUPPORTED` 点名该石；CLEAR 后环肩咬合石 pre-strike 依赖 RING present 违例可抓。
- [ ] Step2 红 → Step3 实现 → Step4 绿 → Step5 commit `feat(e30): P2-T5 G3①支撑活跃+snapshot状态机`

---

### Task 6: g3_check ③压力线（双 case）

**Files:** Modify `3d/g3_check.py`；Test `tests/test_p2_g3_thrust.py`

**Interfaces:** Produces: `pressure_line(ring_stones, extra_loads, band_in_out_fns, H_range) -> dict{feasible:bool, H:[min,max], polyline:[(x,z)...]}`——刚块链法：券石按楔块分割，给定 H 逐块递推合力（重心+面法向摩擦锥无穷大即纯压），压力线出入环带即不可行；acceptance=RING+pre-strike 石重加于对应块顶，robustness=仅 RING；扫 H 网格 0.1-1.2×qL²/8f 求可行区间。
- [ ] Step1 失败测试：半圆均载解析解对照（H≈qL²/8f ±5%）；环带加厚（内外距×1.5）可行区间变宽；把某楔块重心外移 0.3m → feasible 翻假（负控）；中央孔真账 acceptance feasible=True 且 robustness 记录不判红。
- [ ] Step2 红 → Step3 实现 → Step4 绿 → Step5 commit `feat(e30): P2-T6 G3③压力线刚块链(acceptance/robustness双case)`
- [ ] **红线**：中央孔 acceptance 不过 → `raise G3_FROZEN_GEOMETRY_CONFLICT`（不许调封卷参数自救）

---

### Task 7: g3_check ④H 包络不平衡 + λ + 核距

**Files:** Modify `3d/g3_check.py`；Test `tests/test_p2_g3_imbalance.py`

**Interfaces:** Produces: `pier_imbalance(snap, H_env_by_hole, lam) -> per-pier {H_L,H_R,dH, M_unb, M_res, ratio, e_kernel}`；DECENTERING 孔按 λ 档取 H_eff；邻孔取当前状态 H 区间对侧下界（保守）；`ratio≥1.5 [现代裕度]` + `e_kernel=|M_unb/V| ≤ 基底核半宽` 双指标；写入 run_g3 报告。
- [ ] Step1 失败测试：对称双孔同步卸架 dH≈0；一侧提前 CLEAR 另一侧未合龙 → ratio>1.5 红；λ=0 档（架上满承载）dH=0 绿；核距指标与裕度独立输出（一个红一个绿可表达）。
- [ ] Step2 红 → Step3 实现 → Step4 绿 → Step5 commit `feat(e30): P2-T7 G3④推力包络不平衡(λ卸架档+核距双指标)`

---

### Task 8: 真账全链 + narration lint + G3 报告（出口）

**Files:** Create `3d/narration.py`；Modify `3d/sequencer.py`（真账接线）；Test `tests/test_p2_full.py`；输出 `3d/out/sequence.json`、`out/event_ledger.json`、`out/g3_report.json`、`out/narration_beats.md`

- [ ] Step1 真账跑通：5935 石全序、事件 ~6000+、stage 200-600、frontier 轨迹合法；run_g3 全 PASS（双 case+五负控注入逐组红：悬空石/提前 CLEAR/跳孔落架/R3 单边领先/λ 档 H 篡改）
- [ ] Step2 narration_beats.md：每 stage→规则→G0 编号→旁白素材；`narration_lint(text)` 禁词表（样筏/线道子/对合龙口/管主剑/收分铁/铁搭头/"乾隆旨仿"/让古人说压力线类现代词）命中即红，配 2 负控
- [ ] Step3 全门：e30 239+新增 / bridge3d 312 / L2+NEG / 33 断言 / freeze 逐位（P2 零触本体）；validate_ledger(石账 v2 迁移后)==[] 且 G2 工件重放不破
- [ ] Step4 commit `feat(e30): P2-T8 真账序列+G3报告+旁白lint(P2出口, G3门)`

---

## 自审记录
1. **Spec 覆盖**：§2 R0-R7=T4；§3 四组件=T1-T7；§4 咬合石=T4 R5a+T6 acceptance、schema=T1、纯度=T2/T3 设计、红线=T6、ε/敏感性=T4 参数；§5 验收=T8 全项；§6 接口=T8 产物。缺口：无。
2. **占位扫描**：无 TBD；Task6 摩擦锥"无穷大=纯压"是压力线经典无摩擦界，摩擦档留 P3 后[工程参数]已在 spec λ 节，不阻塞。
3. **类型一致**：capacity_curve（T1）↔snap.capacity（T5）↔λ 档（T7）同名同形；events 词表 T3 定义 T4/T5/T6/T7 引用；Snapshot 由 T5 产 T6/T7 消费；`run_g3` 签名 T5 立 T6/T7 扩展 T8 调。
