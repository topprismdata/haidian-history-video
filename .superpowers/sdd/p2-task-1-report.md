# P2 Task 1 报告：ledger schema v2（capacity_curve + inferred_construction + 迁移）

- **状态：DONE**
- **Commit：`93d4a4a`**（分支 `e30-bridge-body`，仓库根 `/Volumes/macstudio/video-projects/`）
  - 信息：`feat(e30): P2-T1 ledger schema v2(capacity_curve+inferred_construction+迁移)`
  - `git commit --only` 限定两文件，2 files changed, 258 insertions(+), 3 deletions(-)：`e30_shikongqiao_video/3d/ledger.py`（改）、`e30_shikongqiao_video/tests/test_p2_ledger_v2.py`（新，14 条测试）。同窗口 P2-T2 的未跟踪文件（`tests/test_p2_centering.py`、`3d/stones/stones_deck.json`）未被卷入。
- **全量回归：`cd e30_shikongqiao_video && python3 -m pytest tests -q --ignore=tests/test_p2_centering.py` → 末行 `253 passed in 111.18s`**（基线 239 + 新增 14 ≥ 243 ✓；`--ignore` 系 P2-T2 红阶段文件 `ModuleNotFoundError: No module named 'centering'`，与 T1 无关，由其 owner 修复）。

## 主控已批的两项裁决（Main 2026-10-07 批准）

1. **schema v2 不 bump `meta.schema` 判别值（SCHEMA 保持 1），v2 由「边形制 + 枚举」版本化表达**。理由：既有负控 `test_p1_ledger.test_neg_schema_and_meta_missing` 钉死 `schema==2 → SCHEMA 错`，正控钉死 `schema==1 → 零错`，再叠加 brief「迁移后 validate==[]」，三条约束联立无解可同时满足 bump 方案；而真实 G2 账工件扫描为 **0 条非空 support_edges**（全 out/**/*.json 实测），故「未迁移 v1 形边直接报 `SUPPORT_SHAPE`」不破坏任何既有数据重放。迁移=原地形制改写，`meta.schema` 不动，幂等。
2. **brief Step1 例「curve[(0,1.0),(5,0.5),(9,0.0)] seq=2→0.75」是算术错，以 brief 自述的线性插值语义为准**：seq=2 的线性值 = 1.0−(2/5)×0.5 = **0.8**；0.75 的真实半值点是 seq=2.5。测试同时断言 `2→0.8`（线性正确性）与 `2.5→0.75`（保留 brief 的半值检查点）；`7→0.25`、`20→0.0`（curve 外=端值）、`−3→1.0`（负 seq=首端值）全部按 brief 通过。

## TDD 五步执行记录

1. **Step1 失败测试**：隔离树 `/tmp/e30_p2/`（`3d` 仅排除 >2.4G 重资产，`refs/stones/textures/...` 软链回真实树；`bridge3d` 软链），逐 brief 接口写 `tests/test_p2_ledger_v2.py` 14 条：迁移后 `validate==[]`、幂等（二次调用 json 逐字节同）、`edge_capacity` 三点曲线插值/钳制、未迁移 v1 边 `SUPPORT_SHAPE`、`CURVE_MONOTONIC`（capacity 回升 + event 序号不升两例）、畸形 curve、`inferred_construction` 合法 / `invented` 非法、G2 无边形制重放绿、单侧键边迁移（仅 active_from→[[2,1.0]] 恒 1.0；仅 active_to→[[6,0.0]] 恒 0.0）。
2. **Step2 红**：`13 failed, 1 passed`（唯一过的 `test_v2_edge_validates_clean` 是 v1 校验器不查边形态所致，符合预期）。
3. **Step3 实现**（只动 `3d/ledger.py`）：
   - `EVIDENCE` 追加 `"inferred_construction"`（元组末位，纯增量）。
   - `_curve_points(curve)`：形态检查器（非空、每点二元数值组、拒 bool），供 validate 与 edge_capacity 共用。
   - `edge_capacity(edge, event_seq)`：按 curve 线性插值、curve 外钳制端点值；无 curve/形态非法（含未迁移 v1 边）返回 0.0 不抛异常。
   - `migrate_v1_to_v2(led)`：原地、幂等、返回同一 led 可链式；`{active_from,active_to}` → `capacity_curve=[[active_from,1.0],[active_to,0.0]]`，pop 旧键、保留 target/type/contact；已有 capacity_curve 的边原样跳过（幂等第二道保险：`a is None and b is None` 直接 continue）。
   - `validate_ledger` support_edges 分支重排：非 dict → `SUPPORT_EDGE_SHAPE`（不变）；`type` 检查（不变）→ 新增：无 curve 且带 active_* → `SUPPORT_SHAPE … 旧形…先过 migrate_v1_to_v2`；无 curve 且无 active_* → `SUPPORT_SHAPE … 缺 capacity_curve`；curve 形态非法 → `SUPPORT_SHAPE`；相邻点 `x1<=x0 或 y1>y0` → `CURVE_MONOTONIC`。**既有错误码前缀零改动**（SUPPORT_TYPE/SUPPORT_EDGE_SHAPE/CLEARANCE_PREMATURE/…），新码 SUPPORT_SHAPE/CURVE_MONOTONIC 为增量；`SUPPORT_SHAPE` 不与 `SUPPORT_EDGE_SHAPE` 前缀冲突（startswith 互不误捕）。签名 `validate_ledger(led, allow_clearance=False)` 未动，export_print/p1a_slice/build_scene2 三消费方按原形调用（`build_scene2.py:1512` 动态读 `_LED.SCHEMA`，仍 1，无兼容问题）。
4. **Step4 绿**：隔离树 `test_p2_ledger_v2.py + test_p1_ledger.py` → `29 passed`（14 新 + 15 既有 P1 全绿）；隔离树全量 `251 passed, 2 failed`——两条均为隔离布局伪影（`test_freeze_manifest` 的 `_REPO=parents[2]` 在 /tmp 下缺 docs/spec 与 git 仓，且 **ledger.py 不在 manifest 冻结清单**，本体路径零触碰）；真实树全量 `253 passed`（上）。
5. **Step5 commit**：`93d4a4a`，中文信息按 brief 原文，`--only` 限定文件。

## 自审

- **brief 验收逐条对账**：迁移后 validate==[] ✓（`test_migrate_v1_to_v2_then_validate_clean`）；curve 三点插值 ✓（线性语义，0.75 修正见裁决 2）；未迁移 v1 边 SUPPORT_SHAPE ✓；inferred_construction 合法/invented 非法 ✓；CURVE_MONOTONIC ✓；幂等 ✓（json.dumps 逐字节比对）。
- **G2 出口约束**：真实账工件 0 支撑边 → `validate_ledger(v1 数据)` 依旧零错，由 `test_migrated_g2_style_v1_ledger_replays_green` 与既有 15 条 P1 测试双重锁住；`migrate` 是纯加法（无 curve 边不动）。
- **Python 3.9.6**：type comments + `Optional[X]`，无 `match`、无 `X | None`；`py_compile` 过。
- **消费方接口**：`validate_ledger` 形参不变；新增三函数为模块级新符号，无重名冲突（全仓 grep ledger/EVIDENCE/SCHEMA 消费方核查过）。
- **负控制内建**：新判据全部配破坏用例（capacity 回升、x 不升、三元组点、空 curve、旧形残留、非法 evidence），破坏能被抓住才计分。

## 顾虑（供主控/后续 task）

1. `edge_capacity` 对未迁移/畸形边返回 0.0（保守无支撑）而非抛错——G3 若要把「未迁移账」当硬错误，请在 g3_check 入口先跑 `validate_ledger`（旧形边必被 SUPPORT_SHAPE 抓住），别依赖 0.0 与「真零承载」的区分。
2. CURVE_MONOTONIC 同时管辖「capacity 单调不增」与「event 序号严格递增」两事（序号乱序会让插值歧义）；brief 只点名前者，消息文本已写明双重语义。
3. `capacity` 值域 [0,1] 未设校验（brief 未要求、无消费方假设依赖）；若 P2-T5 g3_check 出现按比例乘承载的用法，建议届时补 `CURVE_RANGE`。

## 修复轮（审查五项 Important + S 项，commit `f370d4f`）

- **TDD**：12 条新测试先红（`14 failed`）后绿；全量回归 `python3 -m pytest tests -q` → **306 passed**（基线 294 + 净增 12，零新增红；首跑基线以本轮为准）。Python 3.9.6 `py_compile` 过；P1 既有码前缀（SUPPORT_EDGE_SHAPE/SUPPORT_TYPE/…）零破坏。

### I1 左钳改 0.0（G3 假绿危害，最高优先）
`edge_capacity` x<曲线首点 → **0.0**（支撑在其曲线开始前不存在，spec 00959bf 裁决）；右钳保持末点值。**前后对照（实测探针）**：curve=`[[8,1.0],[20,0.0]]`、seq=0 → 旧 **1.0**（左钳=首点值，把尚未出现的支撑当满承载，G3 恒绿）→ 新 **0.0**。同步改两处被钉语义测试：`test_edge_capacity_clamps_outside_curve`（-3→0.0）、`test_migrate_open_ended_and_immediate_release_edges`（from-only 边 seq=0→0.0 / seq=100→1.0 右钳永久；to-only=[[6,0.0]] 全区间 0.0），新增 `test_edge_not_alive_before_curve_starts`（8 前=0、8 点=1.0、30 右钳=0）。

### I2 migrate 先判后写
仅当值对可插值（`_num`=数值非 bool 有限）才 pop 旧键+写 curve；否则**旧键原样保留不吞**，validate 可诊断：
- 字符串时窗（`active_to:"closure+7d"`）→ 不写坏，报 `SUPPORT_SHAPE … 旧形不可插值: 'closure+7d'`（回显原值）；二次 migrate 仍不动（测试钉幂等）。
- 两键皆 null 静态边 → `[[0,1.0]]` 永久支撑（自 0 起，与 I1 左钳配套）。
- from>to 反转窗 → **拒迁不产出必红 curve**，报 `SUPPORT_WINDOW_ORDER`。
- from==to 瞬时窗（主控裁决）→ `[[0,1.0],[to,0.0]]`，v1 语义「to 之前活着」沿 curve 线性趋零；单独 `[[to,0.0]]` 会被左钳误杀（探针 seq=3→0.4，seq=0→1.0，seq=5→0.0）。

### I3 非有限堵
`_curve_points` 加 `math.isfinite(x) and math.isfinite(y)`，NaN/inf 在形态闸即拒（原「比较全 False」绕过单调闸门的通道封死）；测试：NaN capacity / NaN seq 点 / inf x → `SUPPORT_SHAPE`，NaN curve 的 `edge_capacity`→0.0 不产 NaN。

### I4 混形拒
curve 与残留 `active_*` 并存 → `SUPPORT_SHAPE … 混形`（早退不误入 curve 检查）。

### I5 拆码
`CURVE_ORDER`（x 非升）与 `CURVE_MONOTONIC`（y 回升）分码，误导文本纠正；`test_validate_rejects_non_ascending_event_ids` 前缀改 CURVE_ORDER，新增 `test_curve_order_and_monotonic_are_separate_codes` 双负控（各码互不误报）。

### S 项
1. `CURVE_RANGE` 值域闸 [0,1]（当前账 0 条 curve，零代价；越界回显点值）。
2. `_validate_support_edge(sid, e, errs, known_event_seqs=None)` 抽函数（validate_ledger 与 P2-T5 g3_check 共用，docstring 带码表）。
3. docstring 精度：非数值/非有限 seq → 0.0 不抛（堵 TypeError 路径，测试 None/"3"/[3]/NaN/inf）；「长曲线调用方须自备 bisect/增量指针」注记；curve x=数值 event_seq 非字符串。
4. `validate_ledger(..., known_event_seqs=None)` 可选交叉闸：给定时 curve x 不在集合 → `CURVE_EVENT_UNKNOWN`；默认 None 零影响（三消费方 build_scene2/export_print/p1a_slice 形参不变，回归全绿）。

**原「顾虑」2/3 已由本轮闭环**（拆码、CURVE_RANGE）；顾虑 1 语义不变且强化：未迁移/畸形/左钳外一律 0.0，validate 侧新增码可诊断到具体原因。
