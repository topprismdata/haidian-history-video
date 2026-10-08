# P2 终审修复报告（P2FinalFix, 2026-10-08）

任务: P2FinalReview 终审判 **FIX-FIRST**（3 blocker + 6 项裁决级 WARNING）。
主控修复清单按序全落地; 本报告 = merge_ready 三条的交付证据。

## 1. Blocker 修复

### BLK-1 sidecar 完备性有牙
- `tests/test_p2_g3_thrust.py::test_artifact_sha256_sidecar_matches_disk` 重写:
  旧判据 `len>=6`（实测删两行仍 1 passed）+ 缺失 `continue` 全部废除。
  新三段牙: ①`_SIDEAR_EXPECTED` 显式钉 8 路径集合（`_assert_sidecar_set`,
  删行/漏登记/重复登记即红; clean clone 亦可跑）; ②已录工件盘上缺失即
  fail-loud（`_assert_sidecar_present_and_matching`, B2b 纪律
  tests/test_p1_slice.py:439 同族; 全缺=clean clone 上层 skip 保留）;
  ③记录值==sha256 盘上实算。
- 变异负控: `test_sidecar_completeness_mutation_red`（tmp 副本删一行 →
  pytest.raises 红; tracked sidecar 零触碰）。

### BLK-2 ①红停车线 + 旁白派生化
- `run_g3`: gate_dag 红 → `raise G3_GATE_DAG_CONFLICT`（新异常,
  g3_check.py; 与 G3_FROZEN_GEOMETRY_CONFLICT/G3_DECENTER_ORDER_CONFLICT
  同礼, 报告挂 `exc.report`）。raise 点在三节齐后 —— 红报告含
  ①③④+W1 全部已算节; ③④红保持各自算毕即 raise 的既有语义（①红不改写
  其优先级, ③红的 exc.report 里 gate_dag.ok=False 同样可见）。
- `g3_check.main()` CLI: 三门任一红 → 红报告仍落盘（如实红读数 +
  generation 摘要）+ `STOP G3_GATE_RED` 行 + **rc=1**（交付链拒绝）。
- `narration.py`: "G3 三门全 ok" 硬编码常量废除 → `_gate_bits` 从报告
  ok 位派生（逐门 `dag=ok/stress=ok/imbalance=ok` 或 `dag=红(违例码 计数)`）;
  `_red_first_violations` 把红门首违例（含点名石）写进数据源行;
  缺节容错印 "未评"（③/④红 CLI 红报告缺后节不许 KeyError 断链）。
- **端到端负控**（新）: `tests/test_p2_full.py::
  test_e2e_support_edge_removal_cli_blocks_delivery` —— 沙盒副本摘 ARCH09
  一块券石 centering 支撑边 → `g3_check.py` 子进程 **rc!=0** + STOP 行 +
  红报告落盘点名违例石 → `narration.py` 子进程读同一红账 → beats **无
  "全 ok" 字样** + `dag=红` + `DAG_UNSUPPORTED` 点名 + 违例石 id 在表。
  走真 run_g3 链（终审指出 T8 五负控直调子门正是 BLK-2 漏因）。
- 旁白派生单测: `test_narration_gate_summary_derived_from_report_ok_bits`
  （绿印逐门 ok; 注入①红印红点名+违例码; 红文本仍过自身 lint）。

### BLK-3 DM 阈值口径统一
- 采纳 0.985 保守口径为交接口径: `g3_check.SWALLOW_THRESHOLD 0.99→0.985`
  （=sequencer.DM_SWALLOW_THRESHOLD）; `SWALLOW_THRESHOLD_INFO=0.99` 降为
  报告 info 对照（`scan["info_099"]` 同一 ratio_by_id 单源派生, 不二次扫描）。
  出货报告实测: 主口径 **29 块** placeholders + info 25 块@0.99 对照。
- 跨文件钉: `test_p2_sequencer.py::test_dm_swallow_threshold_cross_file_pinned`
  —— **无条件跑**（不寄生真账 skipif —— 终审面2 指出该反模式使钉在
  clean clone 永不跑）; 钉字面 0.985 + 两文件同值; monkeypatch 腿自证钉读
  活属性（判据非恒真）。同阈值两实现逐位同集=终审已实测（EQUAL=True,
  比率最大差 4.3e-7 属 6 位舍入）。

## 2. WARNING 组处置

- **票文件**（新）: `.superpowers/sdd/p2-carryover-tickets.md`
  票1 FILL/肩背胞几何支承判据缺位（验收判据写死: 对调任意两置放时刻→
  某门必红, 或口径文档保持已证范围）; 票2 R5b 填筑期 9163.9 单位未评
  （=已评顶载 4.8 倍, 验收=④增 R5b 评窗+util 表+篡改可见负控）;
  票3 IMPOST 恒 0 重（492 石无 'd' 键, 族体积 16.59; 验收=双实现同轮改+
  全门绿重跑）; 票4 券架几何注册表消费细则（P3）。
- **G3 承诺口径收口**: spec `docs/superpowers/specs/
  2026-10-07-p2-build-sequencer-design.md` §5 验收行回写已证范围
  （"5935 石账全覆盖=3931 入日程+2004 裁1 幻影; 券架注册落盘
  meta.centerings"; 新增 "G3 承诺口径=已证范围" 行: 券石除架外无悬空
  =真判据 / 每石支撑已存在=构造自证(z 升序)+事件时序(R5A_PREREQ/R0)
  非几何支承校验）+ narration_beats 口径注记行 + p2-progress.md 终态节
  —— 三处一致, 禁路线图原句无条件引用。
- **券架注册表落盘**（spec §3/§4 承诺兑现, 最小实现）:
  `sequencer.event_ledger_doc(res, centerings)` 增 `meta.centerings`
  17 副 `{id, zone, arch_idx, xc, family="wood-<zone>"}`（生成器单源取数,
  只进事件簿 meta, **石账零触碰**——纯度红线）; 盘上 event_ledger.json
  重出, validate_event_ledger(require_evidence=True)==[]。
  测试钉: `test_event_ledger_artifact_valid_and_idempotent` 扩 17 副逐字段
  钉（id/zone/arch_idx/xc/family vs 生成器现算）+ ledger_sequenced 无
  CEN- 石 id/无 centering params 纯度钉。
- **T6 报告与图件**: §0 标题下加 SUPERSEDED 就地横幅（11/17 读数已被
  §8.3 取代, 勿据本节取数/取图）; §1 图件行更正（实际生产者=
  test_p2_g3_thrust 真账测, 每轮重写 A08+A01）; 孤儿图
  `3d/m20_ctrl/g3_thrust_A07.png` 用最终模型重生成
  （**FEASIBLE, H=[31.256, 41.518]**, 与 §8.3 表逐位一致; 替换 10-07
  NO FEASIBLE 旧图）。
- **死码**: `run_g3(centerings=None)` 死参数删除（docstring 注
  "接口位→票4"）; `stage_hint` 恒 None 事实 + 注册表位置写入 beats
  P3 交接注记; `_stone_weight` 对无 w/h/d 断面键石 **raise**（fail-loud
  哨兵替代静默 0; IMPOST 误入承重积分集必响）, 配测试钉
  `test_impost_never_in_load_integral_and_weight_fails_loud`
  （IMPOST 不在 R5a 积分集 + raise 行为 + 真账角色集）。
- **W-1 重测预算**: clean-clone 重建测子进程 timeout 600→900s + 注记
  （独占实测 ~200s 量级 ×4.5 余量; 并发时段勿与全套同跑; **本机后台
  通道限流 ~2.4% 时不可用, 须前台独占**——主控通报+本轮实测复核）。

## 3. 计划外必要修复（如实报备）

- `sequencer.main()` 性能修复: `_in_void_ids(led)` 原在 `sched_ids`
  推导式内**逐石重算**（5935 × classify_stones 全账分类, 单次 2.5s
  → 隐性 ~4 小时纯 CPU 炸弹; 此前"真树直测 380s 未完"/重跑爬行的
  真因）。括出单次求值, 集合值不变 —— **行为零变化, 纯性能**。
  修复后全链实测: load+dmscan ~25s, build+check ~6s, validate+写盘 <1s。
- sidecar 重锚纪律: 被取代记录降为注释行（"重锚·被取代记录"前缀）,
  活动记录恒 8 条唯一路径 —— 完备性钉（唯一路径断言）要求如此。

## 4. merge_ready 三条证据

1. **全量 pytest 全绿**: `【见 §6 实测】`（clean-clone 重建测单独串行跑）。
2. **sidecar 逐条==盘上**: 8 条记录实算复核通过
   （test_artifact_sha256_sidecar_matches_disk 绿）; 三门读数 ok=True
   （g3 CLI OK 行: gate_dag=True gate_stress=True gate_imbalance=True,
   acceptance 17/17, robustness 17/17, viol_uniform_hmax=1）;
   g3_report 重生成 canonical_digest 更新
   （`7188388d…` 起, 盘上件摘要自洽钉 test_g3_report_artifact… 绿）。
3. **变异负控**: BLK-1 删 sidecar 行→红（mutation_red 测在）;
   BLK-2 摘支撑边→CLI rc!=0 + beats 无"全 ok"（e2e 测在）;
   BLK-3 改任一侧阈值→跨文件钉红（dm pin + monkeypatch 活属性腿在）。

## 5. 工件重锚账（本轮变更面）

| 工件 | 处置 |
|---|---|
| `3d/out/ledger_sequenced.json` | **逐位未动**（sha f7e26c2f… 与 T8 记录一致） |
| `3d/out/sequence.json` | **逐位未动**（sha 1cefc071…） |
| `3d/out/event_ledger.json` | 重出: +meta.centerings（新 sha a908f60d…, sidecar 重锚） |
| `3d/out/g3_report.json` | 重出: 0.985 口径 29 块 + info_099 + 新 digest |
| `3d/out/narration_beats.md` | 重出: 派生三门行 + 口径/P3 注记（新 sha d19d037d…, sidecar 重锚, lint=0） |
| `3d/m20_ctrl/g3_thrust_A07.png` | 最终模型重生成（FEASIBLE 带窗） |
| `3d/core_hash.json` 等 | 未触碰（blend/冻结域零改动） |

## 6. 测试实测（补录）

- **P2 批**（test_p2_full/g3_thrust/g3_dag/g3_imbalance/events/centering/
  sequencer/ledger_v2, deselect clean-clone）: **221 passed**, 158.40s
  —— 含端到端负控、旁白派生钉、DM 跨文件钉、sidecar 完备性+变异负控、
  注册表 17 副逐字段钉+石账纯度钉、IMPOST fail-loud 钉。
- **补集**（facts/freeze_manifest/l1_body/no_literals/p1_*/geom_math/
  register 13 文件）: **252 passed, 0 failed**, 87.57s（进度点全绿;
  collect-only 复核=252）。
- **clean-clone 重建测单独串行**: `pytest
  tests/test_p2_sequencer.py::test_sidecar_clean_clone_rebuild_matches_recorded`
  → **1 passed in 34.94s**（对修复后 HEAD = 130bf4f; git archive 干净克隆
  + 2 份 untracked 输入 + 重跑 sequencer + sequence.json sha==sidecar
  1cefc071…。注: 修复前 HEAD 同测子进程被本机限流钳 ~2.4% 且重建含
  _in_void_ids 炸弹, 两次 900s 内不可达 —— 性能括出后子进程 ~35s CPU,
  一次通过; 限流间歇性命中, 前台重试即可)。
- **合计 474 passed = 469 基线 + 5 新增**
  （e2e/旁白派生/DM 钉/sidecar 变异负控/IMPOST 钉）, 0 failed。
- 三门读数（g3 CLI OK 行, 重出后）: gate_dag=True gate_stress=True
  gate_imbalance=True acceptance=17/17 robustness=17/17 n_evals=192
  viol_uniform_hmax=1; W1 主口径 29 块@0.985 + info 25 块@0.99;
  narration_beats 重出 lint=0。

## 7. 遗留与交接

- 四张带判据票: `p2-carryover-tickets.md`（票1 优先级最高, P3 前裁决）。
- 本机后台通道 CPU 限流（~2.4%）持续存在: 长跑（sequencer/全量
  pytest/clean-clone 重建）须前台独占或内核内分块; 900s 预算注记已写入
  测试 docstring。
