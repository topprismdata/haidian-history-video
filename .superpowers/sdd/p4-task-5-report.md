# P4-T5 报告: 进度账状态机(print_status) + M5(a) 底座规格(BASE_SPEC)

日期: 2026-10-08 · 执行: P4T5Status · 计划: docs/superpowers/plans/2026-10-08-p4-print-pack.md Task 5
状态: **完成**。commit: `feat(e30): P4-T5 进度账状态机+底座规格(数字推导钉)`

## 交付物

| 文件 | 说明 |
|---|---|
| `3d/print_status.py` | 新建: 进度账状态机 CLI 三命令(init/advance/query)。表驱动迁移(pending→printed→checked→glued 主链; printed→redo→pending 重打改派支链); 非法迁移 raise; 幂等落盘(零时间戳)+原子写+schema 版本头; redo→pending 可携 `--batch` 改派批次 |
| `3d/out/print/section5/BASE_SPEC.md` | 新建: M5(a) 底座规格(底座**不打印**, 供用户台架/木工)。底座长宽高=段 bbox+边距(推导式落文)、五孔定位槽位表(孔心 x=PIER_X facts 单源)、端槽收边说明、承重粗估(体积×密度上界, [估算]); 全部数字可从盘上工件重算 |
| `tests/test_p4_status.py` | 新建 6 支: legal_transitions / illegal_raise / idempotent_init / query_filter / cli_roundtrip / base_spec_numbers_from_manifest(先红后绿, 红两轮实跑确认) |

## 状态机设计

- **迁移表 = 唯一事实源**: `TRANSITIONS = {pending:{printed}, printed:{checked,redo}, redo:{pending}, checked:{glued}, glued:{}}`; `advance_unit` 只认此表, 表外迁移 `IllegalTransition`(ValueError 子类), **失败不改动状态任何字段**(单测+CLI 双验: 字节不变)。未知相位/未知单元/schema 头错 → ValueError。
- **重打改派**: `printed→redo→pending` 支链; `--batch` 仅限 redo→pending 窗口(其余携 batch raise), 改派入 history 审计链(`{"op":"reassign","batch":N,"from_batch":M}`)。冒烟实测 31→17 入账。
- **幂等落盘**: 状态内容零时间戳、`sort_keys`+固定缩进+尾换行 → 同态两连跑逐字节同(真账 1123 单元 init 双跑 rb 相等, advance 同初态两路 rb 相等, 单测钉); **原子写** = 同目录 `mkstemp`+`os.replace`(崩溃不留半文件)。
- **schema 版本头**: `{schema:1, kind:"print_status"}`, `validate_status` 把门, load/advance/query 全过门。
- **防误吞进度**: `init` 目标已存在且无 `--force` → 拒绝(exit 1)。
- 账面字段: `unit → {phase, batch, material, zone, history[]}`; 批次号单源 = `manifest.stones[].batch`(与施工卡批次总表同源, 未复制第二份); glued 语义 = 施工卡"今日粘接"行完成(对账口径写模块 docstring)。

## BASE_SPEC 推导链 (M5(a): 底座不打印, 数字全盘上推导)

- 数据源全部在盘: `manifest.json`(单元/批/体积/比例) × `out/ledger_full.json`+facts(世界包络/PIER_X)。包络与券环区间走 `p1a_slice.world_mesh` 纯逻辑路径(与 T4 段总图同源, **裁片按裁后实体计**: out=916 / ring_trim=207), 孔心 x 走 `geom_math.PIER_X` facts 累加式(桥长闭合硬门 import 自证)。
- 换算: mm = m × scale(0.02) × 1000。
- 关键数字(文档含推导式, 测试独立重算钉):
  - 段包络: 长 52.886002 m → **1057.72 mm**, 宽 13.374399 → **267.49**, 高 6.470000 → **129.40**;
  - 底座: L_底座 = 1057.72 + 2×24.0 = **1105.72 mm**, W_底座 = 267.49 + 2×24.0 = **315.49 mm**, H_底座 = **13.0 mm** [设计选择](厚=段总图示意 0.65 m×20 同参), 边距 24.0 mm [设计选择](=段总图 bx0=x0−1.2 m 同参), 顶面=段底 z0=0.830 m 平面;
  - 五孔孔心 x(底座基准): ARCH07 **144.71** / ARCH08 **343.99** / ARCH09 **552.86** / ARCH10 **761.73** / ARCH11 **961.02** mm; 自检点: ARCH09 孔心 == L/2(段包络对称); 相邻孔心间距 194.23/204.34/213.40/204.34/194.23(中孔最大=跨径规律); 券环 x 区间逐孔落表;
  - 端槽(M5(a) 收边): 2 处, 槽宽 **18.0 mm**(=0.9 m×20, 段总图示意同参)、槽深 **5.0 mm** [设计选择]、槽中心距底座端 **24.0 mm**(对齐段端投影线), 贯通宽; 端切面墩位 P6/P11 = ∓25.2635 m(facts), 包络端比墩心外扩 **1.1795 m**(IMPOST/BACK 出挑); 声明"不代表原墩延续"+段总图示意位以本规格为准;
  - 承重粗估 [估算]: qingshi 3646.89 cm³ × 639 + maoshi 3769.44 × 484 = 7416.33 cm³ × ρ上界 1.25 = **9270.41 g ≈ 9.3 kg**; 体积列逐项回 manifest 对表(±0.01)。

## 判据验证证据 (6 支, 先红后绿)

- **red 实证**(TDD Step1): 缺 `print_status.py` → import error×5; 缺 `BASE_SPEC.md` → 文件缺席 assert; 实跑确认后才实现。
- ① `test_status_legal_transitions`: **全合法迁移表驱动遍历**(TRANSITIONS 每条 from→to 逐一走通, history 尾项断言)+主链一贯到底+redo 改派支链(batch 0→99 断言入账)。
- ② `test_status_illegal_raise`: **12 组表外迁移逐一 raise 且相位不动**(含 glued 终态出边/redo 跳级); 未知相位/未知单元/改派窗口错用/schema 头错 → ValueError。
- ③ `test_status_idempotent_init`: 真账 init 双跑**逐字节同**; advance 同初态两路逐字节同; schema/kind/1123 单元/全 pending/批 0..33 断言。
- ④ `test_query_filter`: `--phase` 过滤精确(排序确定); counts 全相位补零; 未知相位 raise。
- ⑤ `test_cli_roundtrip`: 三命令 `main()` 接线(退出码/stdout JSON); **非法迁移 exit≠0 且文件字节不动**。
- ⑥ `test_base_spec_numbers_from_manifest`: 测试**独立重算管线**(ledger_full→build_print_view→slice_section→world_mesh×1123 石 + geom_math facts)对 BASE_SPEC 全数字钉: 包络 3 行(世界 6 位小数 ±1e-5, mm <1mm)、推导式算术自洽再现、五孔行(墩位 ±5e-5/孔心/券环区间 <1mm)、外扩幅值、承重 3 行(体积回 manifest ±0.01, 质量=体积×1.25 ±0.02)、口径标记([设计选择]/[估算]/M5(a)/不打印)与计数(1123/34 批/639/484)、端槽定案常数。**>1mm 即红, 禁手编数字执行到位**: 该测试自抓本人两处笔误(想当然单元 id —— RING 实带 EAST/WEST 且 B01 起编; 外扩符号 —— x0−PIER_X[6] 为负即包络端在墩心外侧), 均红驱动修测试事实、未动任何推导数字。

## CLI 冒烟(真账端到端, 前台实跑)

`init`(1123 units) → `advance --to printed` → `--to redo` → `--to pending --batch 17`(history: reassign 31→17) → `query --phase pending`(counts JSON) → 非法 `pending→glued` **exit=1**(错误入 stderr, 文件不动) → 无 `--force` 重 init **exit=1**。

## 账只读

全部跑动后: `ledger_full` 80de7a45 / section5 `manifest` ca1a58f4 / central manifest 45fed1e8 / `deferred_holes` fa8a6543 逐位未动。本任务不落仓库状态文件(`print_status.json` 由用户开工时 `init` 产出; 模板登记归 T6)。

## 全量 pytest(分片口径, 分母 collect-only 实测)

- 分母: `pytest tests/ --collect-only -q` 实测 **532**(= T4 关账 524 + 本任务 6 + 并行线入库增量 2); `research/geo` 与 `3d/ab_texture_test.py` 沿 T4 先例不在 tests/ 分片口径。
- 本任务分片: `tests/test_p4_status.py` **6 passed**(红/绿/修事实复绿三轮, 结论确定性不受跑速影响)。
- **全量套件今日未跑成, 如实移交 T6**: 三种启动方式(harness 通道 / nohup 脱离 / `script` 伪 TTY)全部被钳到 ~2.4% CPU —— `top` 实测 **596 进程全部 running 态而总 CPU 4.6%**(10 核: 8P+E), 长进程(>~3s CPU)无论前后台一律饿死(×40 墙钟), 短命令(collect-only 0.41s / CLI 冒烟 1.16s)满速。与 P2 期限流同签名且更广(进程级调度钳制, 非通道私有)。已杀全部爬行进程, 无残留。**本任务完成判定不依赖全量**: 变更面=3 个全新文件(零改既有文件), 唯一可能的全局副作用=收集期 import(532 collect-only 含本文件实跑通过)。全量零红收尾属计划 T6 Step2 关账门(彼时全部子代理已落, 亦符合合流后单次全验纪律)——若届时钳制仍在, T6 需按同证据甄别。

## 环境事实(影响执行方式, 非本任务缺陷)

- **本机进程级 CPU 钳制今日全程在册**: 4 个长作业一致 ~×40-42 墙钟(~2.2s CPU 爬 92-94s; ps 特征 = 2.4-2.5% CPU), 且**与启动方式无关**(harness 前后台通道 / nohup / 伪 TTY 全钳; `top` 实测 596 进程全 running 态总 CPU 4.6%, 见上节)。短命令不受影响(collect-only 0.41s / CLI 冒烟 1.16s / py_compile 满速)。与 P2 期两次空耗同签名, 本次证据升级为"进程调度钳制而非通道限流"。**处置**: 杀掉全部爬行进程(无残留), 长工作改为"短前台分片+collect-only+哈希对账"; 建议 T6 全量前先跑 ~3s CPU 探针(如 `pytest tests/test_p4_status.py -q` 计墙钟), >60s 即等钳制解除, 勿硬爬。
- **并行线在飞**: `git status` 见 `3d/film/*`、`tests/test_p3_*`、`test_p2_g3_thrust.py` 等 mid-modification(P3T8 试渲中)——T6 全量逐条甄别并发面后再定性; 本任务完成判定只依赖 p4 分片与上述账只读哈希。

## 边界与移交

- 打印执行归用户台架(P4 交付=制造包+进度账工具); `print_status.json` 模板与 sidecar 登记归 T6 关账。
- BASE_SPEC 端槽深 5.0 mm 为 T5 定案 [设计选择](槽宽 0.9 m 与 T4 段总图同参, 深度总图未定; 文档已声明"制造以本节为准")。
