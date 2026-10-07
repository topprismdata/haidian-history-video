# P2-T4 序列器 实施报告(sequencer.py)

- Task: P2-T4 `3d/sequencer.py`(新) + `tests/test_p2_sequencer.py`(新)
- 隔离树: `/tmp/e30_p2/`(先红后绿, 全部 TDD)
- Commit: `93a9be1` `feat(e30): P2-T4 序列器(R0-R7+frontier+平衡度+曲线回写)`(单 commit, 2 文件 1713 行)
- 基线: 首跑全量回归 348 passed(2026-10-07, T1-T3 后); 交付回归 379 passed(=348+28 本任务+3 并行落盘, 零新增红)

## 1. 交付物

| 文件 | 内容 |
|---|---|
| `3d/sequencer.py` | 规则引擎 R0-R7 + frontier 状态机 + `build_sequence` / `check_sequence` / `check_frontier` / `derive_frontier` / `apply_support_edges` / CLI main |
| `tests/test_p2_sequencer.py` | 28 测: 合成 3 孔微账逐规则 + 负控五组 + 真账 5935 石全链(存在性 skip) |
| `3d/out/ledger_sequenced.json` | 石账**副本**(原账零改动), 5935 石 support_edges capacity_curve 回写, 9315 条边 |
| `3d/out/sequence.json` | events 6122 + sequence 424 stages(含 event_range) + frontier_trace 85 转移 + meta |

## 2. 接口(brief 滞后处按 T1-T3 最新接口)

- 消费: `L.validate_ledger/load_ledger/save_ledger/edge_capacity`, `E.new_event/validate_event_ledger/event_seqs`,
  `CEN.build_centering_for_arch(id 1基/zone/xc/parts.bbox/footprint)`, `GM.SPANS/arch_rise/arch_springer_z/arch_center_x/width_at`,
  `F.arch_z`(券腹曲线单源——R5a extrados 与 R3 弧长均经它, 禁第二套公式)。
- `build_sequence(ledger, centerings, eps=0.15, min_hold=3, ring_order=None)`
  → `{"events", "sequence":[{id,stage,event_range,depends_on,centering_id,evidence}], "frontier_trace":[{hole,state,at_seq}], "meta", "_edge_plan"}`。
- `check_sequence(result, ledger, centerings, eps, min_hold) -> [错误码]`(空=绿), 负控统一入口。

## 3. 规则逐条(R0-R7, 每条有测)

- **R0 良构**: seq 从 1 连续递增; 每石恰一次 MASONRY 事件; 角色白名单 fail-closed(IMPOST/PIER/RING/SPANDREL/BACK/CORE/PAVING/RAIL/POST/CARVE); 每孔 CLOSE/DECENTER/CLEAR 恰一次。
- **R1 墩 z 升序**: IMPOST/PIER 立架前置放, z_bottom 非降(真账 ARCH01 impost course 号与 z 反向, 分组必须保 z 序——`_group_by` 保插入序, 教训记 §6)。
- **R2 券架先行**: 每孔先发 `HOLD_EVENT(hole, stone_id=CEN-ARCHxx)` 为立架锚(7 类词表中唯一可合法引券架的形态, events.py 前缀分流核); 全部 RING 置放 prereq⊇{立架} 且 seq∈(立架,合龙) 开窗。
- **R3 平衡度 ε=0.15**: 券石按 params.angles θ 中值镜像配对(`|θ_i+θ_j|≤1e-6°`), 配对=放置单位(B01+B07/B02+B06/B03+B05/龙门石); 偶数位前缀+收尾前缀核 `|W_L−W_R|/(W_L+W_R)≤ε`。单石前缀(首块券石落座单侧=满重)由墩台直接承托非拱作用承担, 不入核——否则闸恒假。W=体积×密度, **STONE_DENSITY=1.0**: R3 比值对共同密度因子不变, 则例石作密度论题在册(C:A1-A5)但无数值, 禁发明[三红线]。体积: RING=环厚×facts.arch_z 弧长×2·width_at; CORE=bbox 直积; 其余=w·h·d(masonry2 断面语义)。
- **R4**: CLOSE(prereq⊇全部 RING 置放) → 3×HOLD(本孔, 挂 CEN) → DECENTER_START → WEDGE_RELEASE×4 λ={.25,.5,.75,1.0} 全阶(load_lambda=已释放份额, 沿孔严格递增) → CENTERING_CLEAR。
- **R5a**: `clipped_by=="ring_band"` ∨ 下部锁固肩(判据: 石底 z ≤ 该孔 extrados=F.arch_z+params.ring_t ∧ 石 bbox 与券架 parts.bbox 全局系无碰撞) → 合龙后拆架前, prereq⊇{合龙}。真账分类 3187/5250 肩背胞为 R5a(端孔大侧墙+拱腹以下填腹按判据归锁固), 其余 2063 归 R5b。
- **R5b**: 其余 SPANDREL/BACK/CORE 拆架后 z_bottom 升序置放。
- **R6 frontier**: 状态 UNBUILT<RING_CLOSED<CLOSED_SUPPORTED<DECENTERING<CLEARED<FILLED; 组合表禁相邻孔同 DECENTERING、禁 i DECENTERING 而 i±1 <CLOSED_SUPPORTED。**组合表反推日程必须两波**: 波1 逐孔砌至持荷(全孔 CLOSED_SUPPORTED), 波2 逐孔落架→拆架→填胞——逐孔一次到底则首孔落架时邻孔必 UNBUILT 恒违例(实现迭代中踩中并修正)。`check_frontier` 接受**任意**事件流+全孔 zone 表(空档孔也要参与邻接判), 负控注入经它判红。
- **R7**: PAVING→RAIL/POST→CARVE 全局最后(真账暂无此四角色=0 事件, 形制就绪, 合成账钉死顺序+全局最后)。

## 4. capacity_curve 回写方案(石账副本, 原账永不改动)

> (修复轮按主控裁2 更新语义: capacity=荷载分担份额; RING stone 边 λ 阶梯、
> R5a 肩石仅自持边 —— **本节表格已被 §8 修复轮表取代**, 此处保留作修复前
> 记录。)

| 石类 | 边 |
|---|---|
| IMPOST/PIER | `foundation [[place,1.0]]` |
| RING | `centering [[place,1],[DECENTER,1],[W1,0.75],[W2,0.5],[W3,0.25],[W4,0],[CLEAR,0]]` + `stone [[W4,1.0]]`(λ 阶梯=曲线阶梯, 自持在满释放时接管) |
| R5a 肩 | `centering [[place,1],[CLEAR,0]]` + `stone [[CLEAR,1.0]]` |
| 其余/R7 | `stone [[place,1.0]]` |

全部 curve x=真实事件 seq; `L.validate_ledger(copy, known_event_seqs=E.event_seqs(res))==[]`(M6 交叉闸自此有牙); `edge_capacity` 实测: 置放前 0(左钳)/持荷期 1/λ 阶梯 0.75→0/CLEAR 后 0(承托边)+自持边 1。

## 5. 验证(全部实测)

- 微账 28 测全绿(合成 3 孔 ARCH01-03, 几何全由 GM 现算不硬编码; centering 显式 ring_t=0.41 免 stone_ring_t 缓存/账本路径耦合); 合成 stage 数 51, 钉死 brief 合成界 [50,600]。
- 真账全链: 5935 石 → 6122 事件(=5935 置放+17×11 券架操作), `E.validate_event_ledger(require_evidence=True, min_hold=3)==[]`(T3 复审 M4 硬约束+占位证据必红钉死), `check_sequence==[]`, frontier 轨迹合法 0 命中, R3 前缀全过, stage 424∈[200,600], CLI `python3 3d/sequencer.py` OK。
- 负控五组必红: ①悬空券石(RING 挪拆架后→R2_WINDOW) ②邻孔稀释 HOLD(2 HOLD 改挂邻孔→R4_HOLD+HOLD_INSUFFICIENT) ③跳孔落架(ARCH03 提前落架→R6_JUMP_DECENTER) ④单边领先超 ε(一侧三石前置 ring_order→构造器 raise R3_IMBALANCE) ⑤CLEAR 无 START(删落架块→CLEAR_WITHOUT_START)。另证组合表非恒红非恒绿: 隔孔同落架合法 0 违例 / 相邻孔同落架 R6_ADJ_DECENTERING 必红。
- 全量回归: 首跑基线 348 passed → 交付 376 passed, 零新增红。

## 6. 实现要点/坑(供 T5-T8 与后续任务)

1. **两波日程是 v1 的策略选择, 不是 R6 组合表的逻辑推论**(修复轮 裁3 改写,
   原表述"逻辑推论/恒违例"系过度推断): 组合表只要求**前视 1** —— 任何
   "孔 i 落架"都要求 i±1 已合龙持荷, 满足它的日程不唯一。v1 选两波(波1 全孔
   砌至持荷, 波2 逐孔落架+拆架+填胞)换来任一时刻全孔同相的简单快照面, 便于
   叙事分幕; 前视-1 的流水列(砌孔 i+1 与落架孔 i 交错)同样合法、工期更紧,
   列为 P3 叙事可选项。
2. `_group_by` 必须保插入序: 真账 impost/肩石 course 号与 z 反向(端孔 C02 在最下), 按 course 键重排会静默毁掉 R1 的 z 序。
3. R3 核的单位是"θ 对称配对完成的前缀"(偶数位), 每单石前缀核会恒假(首块券石单侧满重); 负控注入走 `ring_order` 参数直入构造器。
4. 密度取 1.0 而非发明常数: R3 是比值, 共同因子约去; 已有测试钉 `density=2600` 时权重线性放大。
5. HOLD_EVENT(挂 CEN id)兼作立架锚: 事件词表无 ERECT 类, 这是 events.py 校验器下唯一合法形态; T5 的 HOLD zone 交叉注意 stone_id 是 CEN 前缀。
6. 真账 R5a 占肩背胞 61%: 判据"石底 z≤extrados 区"按字面实现(extrados 单源 facts.arch_z+params.ring_t), 端孔大侧墙与拱腹下填腹按判据归锁固肩, 拆架前完成——与"加载预压后落架"通例相容; 若主控要收紧为"贴 extrados 一层带", 只动 `_is_lock_shoulder` 一处。
7. R7 四角色真账为 0: ID 形制与调度已就绪, M20 后续若导出 PAVING/RAIL/POST/CARVE 石自动入列。

## 7. T5 交接

- `result["_edge_plan"]`(sid→support_edges)即 apply 前的曲线表; `E.event_seqs(res)` 供 `L.validate_ledger(known_event_seqs=)`。
- frontier 转移语义在 `derive_frontier`(可从任意事件流重建), g3 snapshot 可复用其 per-hole 生命周期定位。
- `python3 3d/sequencer.py` 一键重生成两工件(E30_LEDGER_PATH 环境变量同 centering.py 约定)。

## 8. 修复轮（2026-10-07, 审查 1C+3H, 主控三裁决 + F1-F9/M2-M9 清单）

改动文件: `3d/sequencer.py`、`tests/test_p2_sequencer.py`、`3d/ledger.py`（主控
授权扩围, 见下「授权记录」）、`tests/test_p2_ledger_v2.py`（同授权）。工件
`3d/out/sequence.json`、`3d/out/ledger_sequenced.json` 重生成
（`python3 3d/sequencer.py` → EXIT=0: OK stones=3883(in_void 滤除 2052)
events=4070 stages=418 trace=85 holes=17）。

### 裁1 幻影石过滤 —— 数字前后对照

| 量 | 修复前 | 修复后 | 依据 |
|---|---|---|---|
| 事件数 | 6122 | **4070**（=3883 砌置放 + 17 孔×11 券架事件） | 2052 in_void 石不再发 PLACE_STONE |
| 入日程石 | 5935 | **3883** | 同上 |
| R5a 锁固肩 | 3187 | **1307** | 见下归因 |
| 支撑边总数 | 9315 | **4076**（=3883×1 + 193 RING 第二边） | 幻影石无边 + 肩石删 centering 边（裁2） |
| stages | 542 | 418 | SHOULDER/FILL 阶段随石数收缩 |

- 单源: `sequencer._in_void_ids` 消费 `build_scene2.classify_stones`
  （blender-free 纯逻辑段, 与 `out/print/excluded_ids.json` 同一管线）, 代理浅
  拷贝传入防 `clipped` 标污染原账（`test_phantom_in_void_not_scheduled` 断言
  原账零污染）。
- **逐位交叉核**: 被滤石集合 == `excluded_ids.json["in_void"]`（2052 id 集合
  相等, `test_real_ledger_fullchain` 常驻断言）。
- void_cut_fragment(1520)/ring_band_overlap(182)/thin_merge(68) 全保留（真实
  裁石在墙里）。
- checker 侧新增 `R0_IN_VOID_PHANTOM`（幻影石以任何形态混入事件流必红, 负控
  `test_phantom_in_void_in_stream_red`）; R0 恰一次核只对入日程石成立。
- **R5a 1307 vs 主控预估 ~400-600 的归因**: 判据未动（z_bottom ≤ extrados ∧
  不撞券架）。修复前 R5a=3187 含 **1880 块幻影石**（洞内、不撞薄架）; 滤除后
  余量全部为真实砌体: **1042 块环带裁片**（void_cut/ring_band_overlap 保留
  石, 恰是抱拱圈肩部的真实锁固砌体）+ **265 块实体墙肩石** + 碰撞项另排除
  390 块撞架裁片落 R5b。预估未计"保留裁片占 extrados 带"这一项; 判据语义
  （环肩咬合锁固）与 1307 的构成一致, 未为凑数放宽/收紧判据。

### 裁2 F1 曲线语义（Critical）—— capacity=荷载分担份额

| 石类 | 边（修复后） |
|---|---|
| IMPOST/PIER | `foundation [[place,1.0]]`（不变） |
| RING | `centering [[place,1],[dstart,1],[W1,0.75],[W2,0.5],[W3,0.25],[W4,0],[CLEAR,0]]` + `stone [[place,0],[dstart,0],[W1,0.25],[W2,0.5],[W3,0.75],[W4,1.0],[CLEAR,1.0]]`（λ 阶梯同点互补, 每事件点 Σ=1） |
| R5a 肩 | `stone [[place,1.0]]` 仅此一条（删 centering 边: 肩石坐已成环砌体不坐木架, 落座即自持） |
| 其余/R7 | `stone [[place,1.0]]`（不变） |

- **Σ≥1 不变量**: 任意事件点 Σ(各边 capacity) ≥ 1。构造器内建
  `_check_capacity_invariant`（采样点 = 每石 curve knot ∪ 本孔全部事件 seq;
  分段线性端点覆盖即全程覆盖）; **独立复核**（脚本直接扫
  `ledger_sequenced.json`）: 3883 石 × 全事件点, **0 违例, worst Σ = 1.0**
  （分担恰好完整）。T5 g3_check 将作验收断言, 本轮测试先钉:
  `test_curve_sum_invariant_all_events`（微账全事件核）+
  `test_cap_invariant_catches_unshared_load`（W1 处 0.25→0 篡改必红）。
- **M3 堵死**: 曲线形状逐值钉死 —— `test_ring_capacity_ladder_via_edge_capacity`
  （stone 边 λ 全阶 + 每点 Σ≈1）、`test_curve_r5a_shoulder_self_supported_only`
  （肩石类型表 == ["stone"] 且 curve == [[place,1.0]]）。改"肩石不卸载"（加回
  centering 边）或"环石全程 1.0"（stone 恒 1）均在形状断言处必红。
- **checker 收紧（配套）**: `R5A_WINDOW` 上界 CLEAR → **DECENTER_START**（落架
  中途不得砌肩; T5 需"锁固后才落架"）。正控窗口断言改 `close < seq < dstart`;
  新负控 `test_r5a_negative_shoulder_during_decenter_red`（肩石挪入
  DECENTER→CLEAR 窗必红 —— 旧上界对此恒绿）。

#### 授权记录（ledger.py 扩围, 主控 2026-10-07 IRC 裁决为准）

裁2 的 stone 边 λ 阶梯（0→1.0 递增）与 `ledger.py` P2-T1 审查轮引入的
`CURVE_MONOTONIC`（y 单调不增, `test_p2_ledger_v2.py` 负控钉死）直接相撞:
validate_ledger 在 main() 工件闸 / test_writeback / test_real 三处硬门全被
触发, 工件无法重生。推导链: 旧曲线（stone 边 [[W4,1.0]]）在 W1..W3 处
Σ=0.75/0.5/0.25 < 1 —— **Σ≥1 数学上强制 stone 边递增**, 不存在合法递减编码;
而 CURVE_MONOTONIC 编码的恰是裁2 明文退役的「剩余能力」语义。主控裁决
「A 的加强版」: (1) CURVE_MONOTONIC 按 type 收窄且补反向闸 —— 退化型边
（centering/foundation/fill/temporary）单调不增原语义保留; **stone 边单调不
减**, 回落报新码 `STONE_CURVE_REGRESSION`（堵"自持份额衰减"静默假绿通道）;
(2) ledger docstring 语义定稿: capacity=荷载分担份额, Σ≥1 由 T5 验收（ledger
层单边无事件流全貌, 不做跨边求和）; (3) 负控两条进 test_p2_ledger_v2
（`test_stone_edge_regression_red_decreasing_allowed` /
`test_stone_edge_regression_red_on_decreasing`, 原 centering 负控零改动仍绿,
实测 28 passed）。diff: ledger.py 条件分型 + 两处 docstring, 约 12 行。

### 裁3 两波 = v1 日程策略选择

- 代码注释（build_sequence 两波推进注, 原 344-347 行）与本报告 §6.1 改写为
  "前视 1"表述（见 §6.1 修复轮改写文本）; **日程代码零改动**（两波实现保留,
  波1 全孔砌至持荷 → 波2 逐孔落架+拆架+填胞, 孔号升序）。

### F4 / F5 / F7 / M2 / M7 / M9 逐项

- **F4**: ① R6 右邻支路负控 `test_m7_r6_right_neighbor_unbuilt_red`（ARCH01
  落架块前置 → 右邻 ARCH02 UNBUILT 必红 R6_JUMP_DECENTER; 既有负控只打 i−1
  支路）。② `min_hold=0` 由 fail-open（0 个 HOLD 直接落架）改为构造器 raise
  `R4_MIN_HOLD`（`test_f4_min_hold_zero_rejected`）, check_sequence 同闸。
  ③ FILLED 轨迹: 无背胞孔不记 FILLED、不发空 FILL 阶段, at_seq=本孔末个置放
  事件（旧代码记全局 len(events), 空背胞孔与 derive_frontier 失同步）;
  derive_frontier 侧 FILLED 只数 CLEAR 后的 FILL 角色置放（合龙→落架窗内的
  锁固肩不再误计）。合成复现钉: `test_f4_filled_trace_hole_local_and_derivable`
  （ARCH03 删空背胞 → 构造/重建两轨迹仍同形）。
- **F5 体积单源（硬约束）**: 删 `_ring_volume`（环厚×弧长×桥宽近似）与
  `_ring_stone_box`（stations 占位框）第二套公式; `stone_weight` RING 分支改
  `families.family_mesh` + `export_print.signed_volume` 现算（散度体积取 |V|,
  与导出/打印链同一族库）, 按（孔, family, params 全量指纹）缓存防 6000 石
  反复积分。微账 RING 石改走真族（wedge-std 全参数）, 不再有私有近似;
  `_stone_box` RING 分派删除。R3 权重随之变: **偶数前缀最大失衡
  0.0367 → 0.002147**（主控预估 ~0.002 量级, 实测 ARCH12 前缀 2）,
  eps=0.15 闸余量扩大 17 倍。
- **F7**: `test_r3_density_invariance` 旧测只验 `w(2600) == 2600·w(1)`（乘法
  实现的恒真复述）; 换真不变量: `SQ.STONE_DENSITY=2600` 整体重建 → 事件流/
  frontier/sequence 逐位相等 + eps 判定零漂移; 末尾反恒真自证（权重确已
  ×2600, 防密度未生效的假绿）。`stone_weight` 密度默认改调用时读模块常量。
- **M2**: `_is_lock_shoulder` 碰撞项专属负控
  `test_m2_frame_collision_excluded_from_r5a` —— 注入"底 z ≤ extrados 但
  bbox 撞券架最低构件"的石, 断言判据两前提成立（自证不恒真）、判 False、
  端到端落 R5b（CLEAR 后）且 checker 全绿。
- **M9**: check_sequence 内 require_evidence=True 接线（原有）补"摘线必红"
  测试 `test_m9_check_sequence_requires_evidence`（证据换 "R?:n" → EVENTS
  EVIDENCE_PLACEHOLDER）。

### 验收核对

- [x] `python3 3d/sequencer.py` EXIT=0, 工件更新: events **4070**（~4100±）、
      stages 418、trace 85
- [x] R5a **1307**（预估带 ~400-600 未中, 归因见上; 判据零改动, 构成=1042
      保留裁片 + 265 实体墙肩, 语义自洽）
- [x] Σ≥1 不变量全事件核过（check_sequence 内建 + 独立脚本复扫工件, 0 违例,
      worst Σ=1.0）
- [x] `validate(require_evidence=True) == []`（真账 + 微账全绿; M9 摘线必红）
- [x] 负控全红得住: 原五组（悬空券石/邻孔稀释 HOLD/跳孔落架/单边领先/CLEAR
      无 START）+ 新增 R0_IN_VOID_PHANTOM / R5A_WINDOW 收紧 / CAP_INVARIANT /
      M2 撞架 / M7 右邻 / M9 摘线 / F4 min_hold=0 / R4_LADDER / R1 乱序 /
      R7 乱序 + ledger 侧 STONE_CURVE_REGRESSION 双向
- [x] 真账 in_void 交叉核: 滤除集 == excluded_ids.json["in_void"]（2052, 逐位）
- [x] 全量 `python3 -m pytest tests -q` 全绿: **392 passed**（修复前基线 379,
      净增 13 判据/负控, 零新增红）
- [x] R3 失衡 0.0367 → 0.002147（本节数字已更新 ✓）

### 教训（changelog 一句的完整版）

T1 审查轮给 capacity_curve 加单调不增闸时, 把「剩余能力」这一**当时的数据语
义**写成了无 type 分型的普适律; T4 修复轮把语义换成「荷载分担份额」时, 该闸
从防线变成静默否决 settled 裁决的墙 —— 验证器编码的语义前提必须与数据语义
同生共死, 换语义时先盘点哪些闸门以旧语义为真值条件; 反向闸（stone 只增不减）
与正向闸成对补齐, 才是分型而不是豁免。
