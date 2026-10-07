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

1. **两波日程是 R6 组合表的逻辑推论**, 不是风格选择: 任何"孔 i 落架"都要求 i±1 已合龙持荷, 逐孔一次到底的日程恒违例。T5 g3 的 acceptance case(环+锁固肩)在波2 首孔即出现。
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
