# P3-T2 任务报告：film_state.py 帧→状态机

- **commit**: `2bce3d2` `feat(e30): P3-T2 帧状态机(在场集/券架/λ档纯函数)`
- **文件**: `3d/film/film_state.py`(187 行)、`tests/test_p3_state.py`(224 行)，仅此两文件入 commit
- **日期**: 2026-10-08；Python 3.9.6；blender-free；P2 工件零修改只读

## 1. 接口落地（签名与计划钉死一致）

- `load_pace(path) -> dict`：json 读入 + 缺顶键(fps/total_frames/stages) ValueError；深校验仍归 pace_build.validate_pace
- `stage_at_frame(pace, f) -> int`：bisect_right(starts, f)-1；f∉[0, total_frames) raise IndexError（两端实测）
- `state_at_frame(pace, sequence, f) -> dict`：键面恰为 6 键 {stage, event_cursor, visible(frozenset), centering_up(frozenset), wedge_lambda(dict), phase(str)}，测试 set(s0)==_STATE_KEYS 钉死
- 词表单源：`from events import DECENTERING_TYPES, EVENT_TYPES`（3d/events.py），import 即对 EVENT_TYPES 自检两处单事件名防拼写漂移；本模块不复制词表容器
- **consumes 澄清**：状态机本体只吃 pace.json + sequence.json；ledger_sequenced.json 仅测试读（幻影钉），运行时无依赖

## 2. 判定规则全表（T3 film_verify 独立实现的唯一接口文档）

同步写死在 film_state.py 模块 docstring（§1-6），与下表逐条同源：

| # | 量 | 规则 | 真账对照 |
|---|---|---|---|
| 1 | stage_at_frame | stage i 拥有帧区间 [start_i, end_i)；越界 IndexError | 408 stage 无缝，start[0]=0，末 end=7200 |
| 2 | event_cursor | **= 当前 stage 的 last_event**（「stage 首帧即本 stage 事件全部就位」，stage 粒度整拍推进，stage 内不细分） | 计划合成测钉死 frame0→cursor5；真账末帧 cursor=4118 |
| 3 | visible | {e.stone_id \| etype=="PLACE_STONE" 且 seq≤cursor}；字段名是 **stone_id**（计划稿 `stone` 为已知偏差） | 末帧恰 3931；CLOSE_RING 真账 stone_id=None、HOLD_EVENT 引券架 id，天然不入 |
| 4 | centering_up | erected − cleared；erected={s.centering_id \| stage 名以 ".CENTER_ERECT" 结尾且 s.event_range[1]≤cursor}（**CENTER_ERECT 是 stage 名后缀非 etype**，真账该 stage 装单个 HOLD_EVENT/stone_id=券架 id，sequencer.py R2 发射处）；cleared={e.stone_id \| etype=="CENTERING_CLEAR" 且 seq≤cursor}（**卸架走事件流**：DECENTER.CLEAR.WAVE 全局波次 stage 的 centering_id=null，只能按事件取） | 17 副 CEN-ARCHxx：erect 段 [27..] 单事件；clear seq 2198..2214 逐孔 |
| 5 | wedge_lambda | key universe = {e.hole \| etype∈DECENTERING_TYPES}（**λ 挂 hole 字段不挂 stage 名**，非 17 孔假设）；每孔：未出 DECENTER_START→0.0；已出 CENTERING_CLEAR→1.0；否则最近一次 WEDGE_RELEASE 的 load_lambda（START 后未出楔 0.0）。CLEAR 与末档 λ=1.0 数值重合但按事件类型显式分流 | 17 孔×四档 0.25/0.5/0.75/1.0；DSTART/WEDGE/CLEAR 17/68/17 事件 |
| 6 | phase | 全局三段：cursor<全账首 DECENTER_START seq→"BUILD"；cursor<全账末 CENTERING_CLEAR seq→"DECENTER"；否则"DONE"；无落架事件的小账恒 "BUILD"；START 无 CLEAR 的账恒 "DECENTER"（不崩，测试钉）[设计选择·计划未钉词表] | BUILD 0..4362 / DECENTER 4363..4512 / DONE 4513..7199（first_dstart=2113, last_clear=2214） |

**两条约定推论（T3 必须一致复刻）**：
- 规则 2 的整拍语义 ⇒ 落架波按 stage 整拍推进：WEDGE.1.L25 stage 首帧 17 孔同时到 0.25 档，不在 stage 内逐孔走；同理 DECENTER.CLEAR.WAVE 拍首帧全账即 "DONE"（清架在其首帧整体落地）。
- 规则 4 的 erect 触发取 event_range[1]（stage 完整越过），与规则 2 的「拍首帧=事件已落」自洽：立架拍自身帧内 cursor==erange[1] → 券架在场。

## 3. TDD 过程

- 红：先写 8 支测试跑 `pytest tests/test_p3_state.py` → `ModuleNotFoundError: No module named 'film_state'`（collection 中断）
- 绿：实现后 8 passed（计划 Step1 合成测逐字、边界、λ 四档梯、券架在离场、无 CLEAR 相位、真账三钉）
- 中途自纠两处：①合成测 _mini_pace 与手写 stage 表 event_range 错位（fixture 错，非实现错）；②实现审查发现「有 START 无 CLEAR」账 `cursor < last_clr(None)` TypeError → 改 `last_clr is None or` + 新增 test_phase_decenter_without_clear 钉

## 4. 真账验证（3d/out 只读）

- **末帧 3931 钉**：f=7199 → stage=407、cursor=4118、len(visible)=3931、phase=DONE、centering_up=∅、wedge_lambda 17 孔全 1.0
- **幻影 2004 缺席钉**：ledger_sequenced 5935 石 − PLACE_STONE 日程 3931 = **2004** 块幻影；全片 stride-97 抽样 75 帧 + 末帧 visible∩phantom=∅，且末帧 visible 恰等于日程集（不多不少）
- 关键帧抽查：f=0 cursor=10/BUILD；f=7084（S408 首帧）cursor 即 4118/终态（规则 2 整拍语义的直接体现）
- **性能预算**：全 7200 帧 state_at_frame 连扫 6.85s（0.95ms/帧）→ T3 双实现 stride-7 对拍 ≈1s、T5 逐帧驱动 ≈7s 量级，可接受
- load_pace/stage_at_frame 真账：7200 帧全越界两端 IndexError 实测

## 5. 全量 pytest 分片明细（P4 红窗窗口口径）

单条全量命令会被 harness 转 >55s 后台通道；按文件分 6 片前台跑，**合计 488 passed / 0 红**（474 P1/P2 基线 + 3 test_p3_pace + 3 test_p4_scale + **8 新增**）：

| 片 | 文件 | 结果 | 耗时 |
|---|---|---|---|
| 1 | facts / freeze_manifest / l1_body / no_literals / p1_export / p1_families | 89 passed | 0.3s |
| 2a | p1_ledger / p1_masonry2 / p1_printcheck / register | 89 passed | 0.6s |
| 2b | p1_scene / p1_slice | 65 passed | 107.4s |
| 3 | p2_centering / p2_events / p2_geom_math / p2_ledger_v2 / p2_sequencer | 160 passed | 71.9s |
| 4 | p2_full / p2_g3_dag / p2_g3_imbalance / p2_g3_thrust | 71 passed | 122.5s |
| 5 | p3_pace / **p3_state(8)** / p4_scale | 13+1 → 14 passed | 1.0s |

- **P4 红窗 ignore（沿 T1 先例，不改对方文件）**：分片期间 P4 线新落 `tests/test_p4_section.py`（顶层 import section_pack，模块未落地）→ 全目录 collect 报 1 error、其用例不计数。本门按「忽略该文件、逐文件分片收全 488」口径收，与 T1 报告 §4 的 Main 裁定同款。
- **基线口径差注记**：Main 下发的「基线 481」与实测差 1——P4-T1 报告自称全量 481 passed 且其分片明细合计不足 481（自身算术缺口）；本次直接 --collect-only 实测全目录（不含 p4_section 红文件）为 **487 collected（T2 前）**，逐文件数（p1_slice 42/p1_scene 23/p2 单元 124/g3 51/sequencer 46/p2_full 20 等均与 P4 报告一致）推出 T2 前基线 = 474+3+3 = **480**，加我 8 支 = 488。481 疑为对方分片重复计数的 1，特此留痕供 Main 核。
- 片 2b/3/4 超 55s 被 harness 转后台，但当日后台通道全速（real≈user），结果照收。

## 6. 给 T3/T5 的交接注记

1. T3 独立实现**只准**以本文 §2 表（=film_state docstring §1-6）为规格，算法自选（计划建议 stage 前缀和+二分）；对拍 `==` 依赖 dict 值等，λ 全为二进制精确小数（0.25 档系），无浮点陷阱。
2. T5 逐帧消费：visible 排实例、centering_up 驱动券架 collection 显隐、wedge_lambda 驱动楔石位移档、phase 可作相机段切分（段界帧 4363/4513 实测见 §4）。
3. 幻影 2004 的钉在 test_real_phantom_2004_never_visible（结构性：无 PLACE_STONE 事件即不可见），T3 的负控篡改测勿动真账，用副本。
4. 词表再漂移防线：film_state import 即自检 EVENT_TYPES；若 P2 改词表，本模块 import 期即红。
