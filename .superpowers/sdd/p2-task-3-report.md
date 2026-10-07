# P2 Task 3 报告：events.py 事件账本（词表 + schema + validate_event_ledger）

- **状态：DONE**
- **Commit：`1abb57d`**（分支 `e30-bridge-body`，仓库根 `/Volumes/macstudio/video-projects/`）
  - 信息：`feat(e30): P2-T3 事件账本schema+校验器`
  - `git add` 显式列两路径，2 files changed, 531 insertions(+)：`e30_shikongqiao_video/3d/events.py`（新，210 行）、`e30_shikongqiao_video/tests/test_p2_events.py`（新，321 行，29 条测试）。P2-T2 并行文件零卷入（commit 前后 `git status` 核对过）。
- **回归（按派发纪律=我的文件+ledger 套）**：`python3 -m pytest tests/test_p2_events.py tests/test_p2_ledger_v2.py tests/test_p1_ledger.py -q` → **`58 passed in 0.04s`**（29 新 + 14 P2-T1 + 15 P1 全绿）。全量留主控。
- **隔离树说明**：全局约束「隔离树 `/tmp/e30_p2/` 先行」——本 task 为纯增量两新文件、零触碰任何既有文件与 T2 并行面（centering/stones 资产），直接在真实树开发并以 `git add` 显式限路径提交，规避 T1 报告记的隔离伪影类问题。

## 产出接口（与 brief 一致 + 一处扩展）

- `EVENT_TYPES = ("PLACE_STONE","CLOSE_RING","HOLD_EVENT","DECENTER_START","WEDGE_RELEASE","CENTERING_CLEAR","ADD_FILL")`（spec v2.1 §3 词表，钉死在 `test_event_types_vocab`）。
- `new_event(seq, hole, etype, stone_id=None, prereq=None, affects=None, load_lambda=None, evidence="R?:n", grade="inferred") -> dict`：`affects=[[edge_ref,[[event_seq,factor],...]],...]` 与 ledger v2 `capacity_curve` 同形，sequencer 可直接写入支撑边；`prereq/affects` 传入即拷贝，缺省空表。`grade` 默认 `"inferred"`（brief 只列合法值未指定默认；取最保守声明级）。
- `validate_event_ledger(ev_led, centering_ids, stone_ids, min_hold=3) -> [str]`：第四参为派发要求「MIN_HOLD(参数,默认3)」的落点，默认 `MIN_HOLD_DEFAULT=3`，标注 [工程参数·敏感性]（B15 灰浆通例只作背景注，非史料常数）。
- `ev_led` 取 `{"events":[...]}`（dict 或裸列表皆可）；`stone_ids` **同时接受 ledger 石记录 dict 列表或纯 id 字符串表**（dict 取 `id` 键）——派发判据明说「传 ledger stones 列表核」，T4 传哪种形态都接得住。`centering_ids` 同理。

## 判据实现与关键裁决

1. **stone_id 承载被作用对象引用，按 `"CEN-"` 前缀分流**：砌筑类（PLACE/CLOSE/FILL）核 `stone_ids`，落架类（DECENTER_START/WEDGE_RELEASE/CENTERING_CLEAR）核 `centering_ids`（T2 id 形如 `CEN-ARCH09`，只字符串引用核，不 import centering）。错误码 `STONE_UNKNOWN`/`CENTERING_UNKNOWN`。brief 签名无独立 centering_id 参数，这是唯一能同时满足「引用存在」判据与签名形状的读法。
2. **seq 三连码**：`SEQ_TYPE`（非 int，含 bool/str）、`SEQ_ORDER`（非严格递增，含重复）、`SEQ_GAP`（相邻事件序号差>1，无洞）。首事件 seq 不限起点（1 或 0 皆可），从第二事件起要求逐 +1。
3. **prereq**：`PREREQ_TYPE/PREREQ_UNKNOWN/PREREQ_ORDER` 三码；prereq<seq 的约束**蕴含 DAG 无环**（G3 ①门可直接依赖，无需再跑环检测）。
4. **落架链时序**：`CLEAR_WITHOUT_START`（该孔 CLEAR 前必有更小 seq 的 DECENTER_START）；`DECENTER_WITHOUT_CLOSE`、`CLOSE_RING_MISSING` 为枚举判据的蕴含项补码——「每孔 CLOSE_RING 恰 1」与「CLOSE 后持荷才准 DECENTER」逻辑上要求合龙先于落架、账内有 RING 石的孔必须有合龙，否则判据 6/7 无法闭合（RING 石孔集合由 `family_key` 形制 `ZONE.FACE.ROLE.Cxx.Bxx` 的 parts[0]=孔、parts[2]="RING" 解析）。`CLOSE_RING_DUP`（同孔>1）、`CLOSE_RING_PREREQ`（该孔每块 RING 石必须有 PLACE_STONE 事件且其 seq∈close.prereq；无 PLACE 事件同样报此码，`test_ring_stone_with_no_place_event_red` 锁住）。
5. **WEDGE_RELEASE λ**：`LAMBDA_MISSING/LAMBDA_TYPE/LAMBDA_RANGE(0..1)/LAMBDA_MONOTONIC(沿孔严格递增)`。首档 λ=0 合法（spec 逐档核 λ∈{0,.25,.5,.75,1}，0=脱楔未承重检查点），`test_wedge_lambda_from_zero_green` 锁住。**单调取严格升**：同档重复释放是账目错误不是物理事实。
6. **HOLD_INSUFFICIENT**：窗口=(该孔 CLOSE.seq, DECENTER.seq) 开区间内**etype==HOLD_EVENT** 计数 < min_hold。⚠️ 语义分歧见顾虑 1。
7. **etype/grade**：`ETYPE bad:`/`GRADE bad:`（与 ledger.py 既有风格同形）。`GRADES=("fact","context","inferred")`。

## TDD 五步记录

1. **Step1 失败测试**：`tests/test_p2_events.py` 29 条，逐条对 brief Step1 清单（合法 6 事件链绿 / 乱序 seq 红 / CLEAR 无 START 红 / CLOSE_RING 缺一块券石 prereq 红 / 未知 etype 红 / grade 虚构值红）+ 派发判据全量 9 项扩测（seq 洞/bool seq、prereq 前指/不存在、λ 回退/越界/缺失/首档0、双 CLOSE、无合龙之孔、缺 PLACE 之券石、min_hold 红与参数降档绿、dict 形态石列表兼容、affects 透传）。夹具双套：`CHAIN_STONES`（六事件链实际砌筑的两块 RING 石）与 `STONES`（全链三块），防「账里有石未砌」污染正控。
2. **Step2 红**：`ModuleNotFoundError: No module named 'events'` → collection error（实现前基线）。
3. **Step3 实现**：`3d/events.py`，纯 stdlib（仅 `typing`），无 I/O 无副作用；Python 3.9.6：type comments、无 `match`、无 `X|None`。
4. **Step4 绿**：`29 passed`；叠加 ledger 套 `58 passed`。
5. **Step5 commit**：`1abb57d`，中文信息按 brief 原文，`git add` 显式双路径。

## 负控制自证

每条红判据都配了「破坏能被抓住」的独立用例（29 条中 20 红 8 绿 1 词表）；绿链正控与红用例成对（如 λ：乱序红 vs 首档 0 绿；HOLD：默认 3 红 vs min_hold=1 绿），防恒真。

## 顾虑（供主控/T4/T5）

1. **HOLD 窗口计数口径**：spec §「合龙后至少 3 个**结构事件**才准 DECENTER_START」，brief 派发判据明写「**HOLD_EVENT 数** ≥ MIN_HOLD」。二者不同（前者窗口含 PLACE/CLOSE 后任意事件）。已按 **brief**（HOLD_EVENT 计数）实现——若主控裁定按 spec 原口径，改 `validate_event_ledger` 的 holds 采集一处即可，测试需同步两条。
2. `affects` 与 `evidence` 内容未校验（brief 判据未列）：edge_ref 存在性、capacity_curve 形态合法性留给 G3/T5 接 ledger 时核（`evidence="R?:n"` 默认值是占位串，lint 应在 narration/acceptance 层抓）。
3. 同一 stone_id 被 PLACE 两次不报错（`place_by_stone` 首见为准，brief 未列「重砌」判据）；sequencer 若需防重，宜在生成侧而非校验侧，或届时补 `PLACE_DUP` 码。
4. `hole=None`（桥台/墩等非孔工事事件）按 None 键正常分组，无 RING 石表 → CLOSE 相关判据自动豁免。

## 修复轮 (b23a9f1, 2026-10-07)

审查 REQUEST CHANGES(3H+7M+5L) 全量处置；TDD 先红后绿；29 既有测试零删改，新增 25 条 → 文件内 54 条；全量 `python3 -m pytest tests -q` **331 passed**（基线 306 + 25，零新增红）。Python 3.9.6 编译通过。

### H1 fail-closed 三闸（events.py `_check_refs`/`_check_hole_lifecycle`）
- `HOLE_UNKNOWN`：事件 hole ∉ 石账 zone 集（`sid.split('.')[0]`，`count('.')>=3`）→ 红
- `REF_HOLE_MISMATCH`：砌筑事件(MASONRY 类) stone_id 的 zone ≠ hole（含 hole=None，fail-closed）
- `RING_SET_EMPTY`：有 CLOSE_RING 而该孔在传入石账无 RING 石 → 报"判据将空转"
- 探针 S1（空石表）/S2（hole 写 ARCH9 石 id 是 ARCH09）由整账假绿变红

### H2 裁决性质回归 pin + 变异自证（改反口径必红的测试名，实测）
| 定点突变 | 必红测试（实测杀死） |
|---|---|
| 拆 H1 三闸 | `test_event_hole_not_in_stone_zones_red` `test_empty_stone_set_fails_closed_red` `test_ringless_stone_ledger_fails_closed_red` `test_masonry_ref_zone_mismatch_red` `test_masonry_without_hole_red` |
| HOLD 改全局窗口计数 | `test_neighbor_hole_cannot_dilute_hold_red` |
| λ 改跨孔全局比较 | `test_wedge_lambda_grouped_per_hole`（绿相 A/B 交替即误红"前档 1.0"，与预测一致） |
| 引用类分流拆除 | `test_masonry_ref_to_centering_red` `test_decentering_ref_to_stone_red` |
| `lam<=prev` → `<`（等值放行） | `test_wedge_lambda_equal_steps_red` |
| LAMBDA_STEP 栅格拆 | `test_wedge_lambda_off_grid_red` |
| affects 核拆（_curve_points + seq∈by_seq） | `test_affects_shape_red` `test_affects_seq_unknown_red` |
7 组突变全部被杀、无幸存；变异后除期望集外既有 29 条保持绿（隔离性）。变异脚本锚点均 assert 自证（吸取"负控探针自证"教训）；跑毕 cmp 还原，树干净。

### H3 引用类分流 + affects 逐条核
- MASONRY={PLACE_STONE,CLOSE_RING,ADD_FILL} 要求 sid∈stone_set；DECENTERING={DECENTER_START,WEDGE_RELEASE,CENTERING_CLEAR} 要求 sid∈cen_set；形与类不符 `REF_CLASS_MISMATCH`（前缀降级为类内 tie-break，HOLD_EVENT 等沿用前缀存在性核）
- affects 逐条：ref 前缀分流存在性(`AFFECT_REF_UNKNOWN`)、curve 点形=[int 事件序号, 有限数值](`AFFECT_SHAPE`，复用 `ledger._curve_points`，未重写)、x∈by_seq(`AFFECT_SEQ_UNKNOWN`)

### M1-M7 / L1-L5
- **M1** `stone_ids/centering_ids=None`→按空集；非 int `min_hold`→`MIN_HOLD_TYPE`+回退默认 3；缺 etype 键→`ETYPE` 红（分组循环改 `e.get("etype")`），三条崩溃路径全堵，契约"返回错误列表"恢复
- **M2** `LAMBDA_STEP`：[0,1] 域内再核 1/4 档栅格（`|4λ-round(4λ)|>1e-9` 红，0.33/0.125 实红；0/0.75 绿）
- **M3** 等值放行已 pin（上表）
- **M4** `require_evidence=False` 默认关、交付闸开：`EVIDENCE_PLACEHOLDER`(None/''/"R?:n") + `EVIDENCE_FORMAT`(按 refs/construction_history.md 实测形制 `A\d+|B\d+|C:[AB]\d+`，容 `/`、`-` 组合)。**为何 opt-in**：new_event 默认 "R?:n" 被 `test_new_event_shape_and_defaults` 钉死且 29 绿测全依赖默认值，无条件判红必破零删改纪律；T4/T5 终验须显式传 True
- **M5** `SEQ_START`：首事件 seq ∈ {0,1}（起点 2/负起点红，0 起链绿）
- **M6** 导出 `event_seqs(ev_led)`（dict/裸表两形态，滤非 dict/非 int）；docstring 写明 T5 用法 `L.validate_ledger(led, known_event_seqs=E.event_seqs(ev_led))`；已在真账 out/ledger_full.json(5935 石) 交叉冒烟通过
- **M7** 覆盖类验收（注册不落架券架/λ 未走满/无 WEDGE 即 CLEAR/同孔双 DECENTER/孤立 WEDGE/重砌/CORE 抢砌）写入 docstring **非目标**节，归属 T4 生成侧 + T5 frontier——请主控将该结论带进 T5 brief
- **L1** 132 行单函数拆为 `_check_shapes/_check_refs(+_check_affects/_check_evidence)/_check_prereqs/_check_hole_lifecycle`，共享状态入 ctx dict
- **L2** 旧变异不隔离用例保留不动，新增 B4 形隔离用例 `test_decenter_without_close_isolated_red`（断言无 SEQ_* 噪声）
- **L3** `k = 0` 死变量在既有测试体内，按"29 既有测试零删改"纪律未动，留待下轮顺手清理
- **L4** new_event affects 深拷贝两级 + 独立性测试；docstring 改口径"传入即深拷贝两级"
- **L5** 消费约定进 docstring：errs==[] ⇒ prereq 图无环；hole=zone 前置；seq 起点；λ 栅格口径；M6 用法

### 报告勘误（对应审查 report_accuracy.需更正）
顾虑 1 已随 d929428 同源；"传入即拷贝"已改为两级深拷贝并补测试；λ 档位现为真实判据（LAMBDA_STEP）；CEN- 分流的"形与类不可判"代价已由 REF_CLASS_MISMATCH 消除。
