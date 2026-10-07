# P2 Task 8 报告 — 真账全链 + 五组负控 + 出口工件 + narration beats/lint(P2 出口, G3 门)

日期: 2026-10-08。范围执行者: P2T8Impl。改动面: `3d/narration.py`(新)、
`3d/sequencer.py`(真账接线级小改)、`3d/g3_check.py`(接线级小改)、
`tests/test_p2_full.py`(新)、`3d/refs/artifact_sha256.txt`(sidecar 追加)、
产物 `3d/out/{event_ledger,g3_report}.json` + `3d/out/narration_beats.md`
(untracked, sidecar 钉)。判据/阈值/封卷几何/砖谱零触碰; 三门 ok=True 既成
事实零回退。

## 0. 结论一句话

T8 出口闭合: 真账全链(5935 石全序 / 事件 **4118** / stages **408** —— 实测数
如实钉, brief 预估 ~6000+/200-600 已被实测取代, 未凑数)经 run_g3 三门
ok=True(acceptance/robustness 双 **17/17** + ④门 **0/192** +
`viol_uniform_hmax=1` 条件性在册); 五组负控注入逐组被对应门点名(每组带
"不注入不误报"对照); `event_ledger.json`(交付闸 require_evidence==[] + 幂等
两连跑逐字节相同)与 `g3_report.json`(三节+条件性字段+生成命令+HEAD 头注+
去计时内容摘要自洽)落盘; `narration.py` beats(408 stage 全量, 卸架序=R4/R6
勘误落表, 四叙事铁律行级标注)过自身 lint 零红; 禁词 lint 三道闸配 2 负控+
空表不构绿纪律。全门回归 469/312/L2+NEG/33 断言/freeze 逐位/G2 重放全绿。

## 1. 交付物与数字(全部实测)

| 工件 | 内容 | 验证 |
|---|---|---|
| `3d/out/event_ledger.json` | `{"schema": "event-ledger-v1", meta{n_events=4118, hole_order×17}, events×4118}` | 交付闸 `validate_event_ledger(require_evidence=True)==[]`; 幂等两连跑 cmp 逐字节相同; 盘上件==重生成件; sha `e7087ffd…` 入 sidecar |
| `3d/out/g3_report.json` | gate_dag/gate_stress/gate_imbalance 三节齐 + W1 清单 + `meta.generation{command="python3 3d/g3_check.py", git_head=fb17df4(40 位), content_sha256_excl_timing}` | 三门 ok 全 True; acceptance/robustness 17/17; n_evals=192; viol_uniform_hmax=1; 摘要从盘上文件重算核对一致 |
| `3d/out/narration_beats.md` | 427 行: 四铁律节 + G3 读数节 + 408 条逐 stage beats(stage→规则号→G0→素材) | 盘上件==`build_beats_text` 纯函数重生成; `narration_lint(全文)==[]`; 四铁律在对应行显式标注; sha `565f4884…` 入 sidecar |
| `3d/narration.py`(新) | beats 构造(纯函数) + 禁词 lint 三道闸 + CLI(lint 零红才落盘) | 18 测(test_p2_full) |
| `3d/sequencer.py`(改) | +`EVENT_LEDGER_SCHEMA`/`event_ledger_doc`/`dump_event_ledger`; main() 交付闸不过**拒绝落盘**, 过则写 event_ledger.json | 重跑后 sequence.json `1cefc071…` / ledger_sequenced `f7e26c2f…` 与 sidecar 既有记录**逐位一致**(接线零漂移实证) |
| `3d/g3_check.py`(改) | +`_strip_elapsed`/`canonical_digest`/`main()` CLI; 三门红仍走停车线异常原样抛出, CLI 不接判据 | 真账 rc=0(33.9s), 打印 OK G3_REPORT 三 True |

幂等/稳定性口径: 事件簿无计时字段 → 两连跑逐字节相同; g3_report.json 含
`elapsed_s`, 文件字节两次生成必不同(与 ledger_full uuid4 同口径的既有行为),
完整性锚=`content_sha256_excl_timing`(除 elapsed_s 与 meta.generation 外逐
字段 sha256, test_p2_full 从盘上文件重算核对一致)。

## 2. 真账接线(sequencer/g3 各一小改, 判据零触碰)

- 事件簿容器与序列化是**唯一出口**: `event_ledger_doc(res)` events 原样引用,
  不出第二套事件流; `dump_event_ledger` 为 main 与 test_p2_full 共用(幂等 cmp
  单源)。main() 落盘前过交付闸 `validate_event_ledger(require_evidence=True)`,
  违例拒绝写盘(exit 1) —— 账不干净不出门。
- g3 CLI 只串接: 读 `out/ledger_sequenced.json` + `out/sequence.json` →
  `run_g3(rbo_ids=None)`(W1 双建模全桶扫描单源) → 落盘 + generation 头注。
  三门任一红 → `G3_FROZEN_GEOMETRY_CONFLICT`/`G3_DECENTER_ORDER_CONFLICT`
  原样抛出(停报主控), 本 CLI 不接判据。

## 3. 五组负控(逐组"注入→门点名"+ 不注入不误报; 全部真账 4118 事件流)

| # | 注入(真账篡改) | 对应门点名(实测) | 不注入对照 |
|---|---|---|---|
| ① | 悬空石: 删 ARCH09 一枚 RING 石 support_edges | g3 gate_dag `DAG_UNSUPPORTED 石 ARCH09.EAST.RING.C00.B01 seq=1015 Σcapacity=0.000000 < 1`(点名该石; 同出 NO_ACTIVE_SUPPORT/RING_NO_CENTERING) | 同引擎同账 `check_dag_all==[]` |
| ② | 提前 CLEAR: ARCH05 本孔 CLEAR↔DECENTER_START seq 对调 | `check_sequence` → `R4_CLEAR_ORDER 孔 ARCH05 CLEAR 先于 DECENTER`(events 生命周期 `CLEAR_WITHOUT_START` 同捕) | 夹具 `check_sequence(res)==[]` |
| ③ | 跳孔落架: ARCH02 dstart 越过 ARCH01 合龙 | g3 gate_dag `DAG_R6_JUMP_DECENTER 孔 ARCH02 落架(seq=35)时邻孔 ARCH01 未达合龙持荷`; sequencer `check_frontier` → `R6_JUMP_DECENTER` 两实现互证 | 基线 dag 零违例 |
| ④ | R3 单边领先: ARCH09 券石邻 bank 一石对调(右 bank1↔左 bank2) | `check_sequence` → `R3_IMBALANCE 孔 ARCH09 前缀 2/17 平衡度 1.0000 > 0.150`(且仅此一族码) | 夹具零错 |
| ⑤ | λ 档篡改: ARCH08 首档 WEDGE↔ARCH09 末档 WEDGE **时点对调**(λ 值随事件走, 每孔阶梯仍全阶) | g3 gate_dag `DAG_R6_ADJ_DECENTERING 相邻孔 ARCH09/ARCH08 同落架失档(λ 1.00 vs 0.00, 差>一档)`(共 6 条) | 基线 dag 零违例 |
| ⑤b | H 篡改可见性: ARCH02 acceptance H 区间翻倍直喂 `imbalance_gate` | ④门读数 **19 entries `dH` 严格变化**(PIER01 dH −2.483→−7.579, ratio 30.540→10.006) —— H 是④门活输入, 篡改可观测不被静默吞(T7 探针③同法) | 真 H 基线 `imbalance_gate` 0/192 ok=True |

注入实现全部为"对调 seq 值/删边"类最小篡改, 排序后喂同一门引擎; 断言只认
门点名码 + 孔/石 id, 不认"红了就行"。

## 4. narration beats + 禁词 lint

- **beats**(`build_beats_text`, 纯函数只读计数字段, 与计时无关): 每条 stage 行
  = `id | stage 名 | 规则=R0-R7 | G0=事件证据号 | 事件区间·石数 | 素材要点`。
  规则号按 stage 形制映射: IMPOST→R1 / CENTER_ERECT、CLOSE_RING→R2 /
  RING.bank→R3 / HOLD→R4 / SHOULDER→R5a / FILL→R5b / DECENTER 三波(DSTART
  .WAVE、WEDGE.1..4.L{25,50,75,100}、CLEAR.WAVE)→**R4/R6(T7 勘误: 非 R5,
  测试钉"R4/R6 在行内且规则段无 R5")** / PAVING/RAIL_POST/CARVE.GLOBAL→R7。
  未登记 stage 名 `stage_rule` raise(fail-closed)。
- **四叙事铁律行级标注**(与 T6 §7.2/§9、T7b §9 口径逐字一致): ①裸环合龙即
  自承(robustness 17/17)→全部 17 条 CLOSE_RING 行; ②acceptance 17/17 是模型
  族结论(餬灰胶结协同+冠缝共享支点两假设, 失效边界 p2-task-6-report §7.2/§9)
  →全部 SHOULDER 行; ③卸架序 [工程推断·非史料](C:A3 则例无工序教科书)+串行
  序=本门图式下的临界定(6/192, util 1.009, p2-task-7-report §9.2)非不可行
  证明→DSTART.WAVE 行; ④对称同步卸架=安全族(0/192@最小推力读数)→WEDGE 行。
- **narration_lint 三道闸**(Findings 带 kind/line/col/word):
  1. `BANNED_WORD`: 样筏/线道子/对合龙口/管主剑/收分铁/铁搭头/"乾隆旨仿"
     (refs/construction_history.md 旁白红线+B 线术语正字), 逐词点名+位置;
  2. 现代工程词(压力线/倾覆裕度/中三分/三分点/推力线/极限分析/安全系数/稳定
     系数/弯矩/剪力/偏心距): 入「」『』“”引语(古人台词)→`MODERN_TERM_IN_QUOTE`
     **一票红, 标签不豁免**(B1: 古人无压力线概念); 入叙述未挂 [现代分析]→
     `MODERN_TERM_UNTAGGED`([工程推断] 不豁免现代力学词);
  3. `UNSOURCED_CLAIM`: 断言行无 G0 证据号(A\d+/B\d+/C:[AB]\d+, 边界防伪)且
     无允许标签([现代分析]/[工程推断·…]/[工程参数·敏感性]/[工作值]/[推断]/
     [通例迁移·卢沟桥]/[存疑待考]/[文献记载]/[图像推导]…)。豁免=空行/`#`标题/
     ```代码栅栏/行首元数据前缀(生成命令:/数据源:/对照账:/回放:)。
  空表纪律: `BANNED_WORDS` 被清空 → `NO_WORDS_TABLE` finding, `narration_ok`
  为假 —— **禁词表空不算过**(skip≠pass, qa_l2 I4 同纪律)。
- 负控 2 组 + 附加: ①7 禁词逐词注入必红(点名词+line/col); ②9 行合规样例
  (挂 G0 号/标签/元数据)零误伤; 另: 现代词引语红/未挂标签红/挂标签放行/
  [工程推断] 不豁免、无源断言行红+结构行豁免、词表非空钉(防空表回归)、
  **beats 全文过自身 lint 零红**(lint 能守 beats)。

## 5. 全门回归(brief Step3 逐条, 真树实测)

| 门 | 结果 |
|---|---|
| e30 全量 `python3 -m pytest tests -q` | **469 passed**(451 基线 + 18 新: 真账全链 2 + 三门 1 + 五负控 6 + 工件 3 + beats 1 + lint 5), 268.9s |
| bridge3d | **312 passed**(0.53s) |
| qa_l2(blender 5.2.2 LTS, e30_bridge.blend) | **QA_L2_OK**(rc=0, fails=0 skips=0) + 负控 **QA_L2_NEG_CAUGHT**(翻转 10 面全部被 WALL_NORMAL 抓到, 10/604 坏面, rc=0) |
| _check_abutment | **ABUTMENT_CHECK ALL PASS**(33 条 PASS 断言逐行) |
| freeze 逐位 | `test_freeze_manifest` 13 passed; sidecar `test_artifact_sha256_sidecar_matches_disk` 8 条记录值==盘上实算(含新增 2 条); sequence.json `1cefc071…`/ledger_sequenced `f7e26c2f…` 重跑后逐位未动(本体路径零触碰实证) |
| validate_ledger(v2) | `validate_ledger(led2, allow_clearance=False, known_event_seqs)==[]`(真账 5935 石回写副本; sequencer.main 内同一闸 rc=0) |
| G2 工件重放 | `validate_g2_report(out/print/g2_report.json)==[]`, verdict=PASS 不破 |

## 6. 边界与移交

- **执行环境注记(诚实披露)**: 本机当日后台任务 CPU 配额异常(经 bash 后台
  通道派生的进程实测 ~2.4% CPU), 长命令(`python3 3d/sequencer.py` 全链)两次
  后台爬行后按纪律终止; 产物改经 eval 内核**逐步执行 main() 同一函数链**落盘
  (事件簿=sequencer.main 尾段同一函数; G3 报告=g3_check.main 全函数 rc=0;
  beats=narration.main 全函数 rc=0), 并由 test_p2_full 的"盘上件==重生成件"
  逐字节断言兜底 —— 工件与生成器单源关系不受运行通道影响。pytest 全量
  (含 clean-clone sidecar 重建测, 子进程 600s 限内完成)实跑通过, 证明判据链
  对执行通道无隐含依赖。
- `g3_report.json` 不入 sidecar(字节含计时天然不稳定), 以报告内
  `content_sha256_excl_timing` 为完整性锚; 事件簿/旁白表(确定性字节)入
  sidecar。复现命令链已写入 sidecar 头注(步骤 2b/2c/2d)。
- beats 素材要点为 P3 起点而非成稿: 台词/字幕仍需过 P3 阶段的 GPT 审校闸
  (E14-E17 纪律); 本表职责是"每条素材自带证据号或标签, lint 可守"。
- 已知限制沿 T7b §9.4 #8: ④门只评 DECENTERING 事件, ADD_FILL 填筑期偏载不
  在本门(P3 前补, 本轮未扩)。
- 移交 P3: narration_beats.md(逐 stage 素材) + event_ledger.json(逐事件账) +
  g3_report.json(三门读数+条件性字段) + W1 双建模占位清单(P3 视觉隐藏)。
