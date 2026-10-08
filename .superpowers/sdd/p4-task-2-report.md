# P4-T2 报告: export_print zones 参数化 + 段包出图(section5)

日期: 2026-10-08 · 执行: P4T2Section · 计划: docs/superpowers/plans/2026-10-08-p4-print-pack.md Task 2
状态: **完成**。commit: `feat(e30): P4-T2 段包出图(zones参数默认零漂移+deferred互补)`

## 交付物

| 文件 | 说明 |
|---|---|
| `3d/export_print.py` | 修改: `export_ledger(..., zones=None)` 选孔过滤。过滤点只在账遍历处(区外石记 `manifest.skipped` 带 `reason="zone_not_selected"`, 选区记 `meta.zones`); 分档/装箱/FIT 约定零改动; 默认 None 逐字节不变 |
| `3d/section_pack.py` | 新建: 段包编排(load/build_print_view/slice_section/deferred_plan/pack + CLI)。全 blender-free(纯逻辑, **无需 bpy 门控**) |
| `tests/test_p4_section.py` | 计划 Step1 三判据 + zones 过滤语义(合成) + 全树幂等, 共 5 支 |
| `3d/out/print/section5/` | 段包: manifest.json(34 批/1123 单元/coupon 首件/conservation 汇总) + PACK_REPORT.md + ledger_print.json + maoshi\|qingshi 分目录 STL+3MF(1123 石 x2) + coupon/ 12 件 |
| `3d/out/print/deferred_holes.json` | 留续清单: 12 孔/3188 石/990 单元(unit_ids 全表, T3 validator 对账输入) |

入库产物按 central_slice 先例只收 manifest 级三个文件(manifest/PACK_REPORT/deferred, `add -f`); STL/ledger_print 可由代码+真账逐字节再生(幂等测在证), 不入库。

## 三判据(plan T2 Step1)验证证据

**① zones=None 零漂移(`test_default_zone_none_reproduces_central`)**
- 基线在位: 盘上 central manifest sha256 == `45fed1e8bb64…b9e8d`(sidecar 钉值)。
- 同一真账(80de7a45)+同一 G2 切片口径重跑: **manifest 语义等值**(容器/串/整型精确, 浮点 rel=1e-12)、**ledger_print.json 逐字节同**、**245 石 STL 数值等值**。
- STL 门为"数值等值(≤1e-6 mm)+结构同(尺寸/三角数)", 非逐字节 —— 首跑实测: 门时几何产自 blender 捆绑 numpy, 裁剪面重合处近零相消坐标与本机 numpy 差 ~1e-13 mm(最大 6.1e-14, 8/384 个 float32 场), 恰逢 float32 舍入边界翻红; 逐石 volume rel=1e-12 已把真实漂移压到 1e-10 mm 级, 数值门兜底"同体积异顶点排布"类回归。**负控在测**: 单坐标 0.01mm 扰动/文件截断必红(`_stl_close_negative_control`), 判据非恒真。
- belt: `zones=["ARCH09"]` 走新参数路径对同一子账产出同一包(参数化路径与默认路径互证)。

**② 段守恒(`test_section5_counts_conservation_basic`)**
- **2747 = 1123 (manifest.stones) + 1624 (manifest.skipped)**, 逐 id 恰一次, 集合恰等段内全集。
- skipped **全带 reason** 且与盘上排除账(excluded_ids `fa1a4ef3`)逐 id 同桶: in_void 900 / void_cut_fragment 624 / ring_band_overlap 100; role 过滤语义沿用 P1(无 reason, 合成测钉)。
- ARCH09 子集 245 == central manifest 石集(跨包互证)。

**③ deferred 互补(`test_deferred_complement`)**
- 12 孔(ARCH01-06, 12-17)∪ 段 5 孔 = 17 孔全集, 不交; 石 3188+2747=5935, 单元 990+1123=2113 合账; 落盘两连跑逐字节同。

## 关账实测数字(供 T6 把 spec ~913 估算修成实测)

| 项 | spec#4 M1 估算 | 实测(本包) | 偏差 |
|---|---|---|---|
| 段打印单元 | ~913 (2747 x 0.332 单元率外推) | **1123** | **+210 (+23.0%)**, 实测率 0.409 |

| 汇总 | 值 |
|---|---|
| 段账面石 / 出件 / skipped | 2747 / 1123 / 1624 |
| 批数(220x220) | 34 (fit_diagonal 斜置 2 件, oversize 0) |
| 总体积(打印件, 耳切对角约定口径) | 7416.3 cm3 = maoshi 3769.4 (x484) + qingshi 3646.9 (x639) |
| fit 档分布 | TIGHT 612 / NORMAL 501 / LOOSE 10 |
| 分孔出件 | ARCH07 192 / ARCH08 247 / ARCH09 245 / ARCH10 247 / ARCH11 192 |
| 估时参考 | 7416.3 cm3 ÷ 12 cm3/h ≈ 618h 实心体上界(未扣 infill/支撑/重打; 权威=切片器实测) |

产物 sha256(供 T6 sidecar 登记): section5/manifest.json `ca1a58f4a77ef575…b4e9a`; PACK_REPORT.md `267d5670582661…cff56`; deferred_holes.json `fa8a65438746f5…bb3ff`。

## 幂等(全局约束)

- 生产 CLI 两连跑: **2262 文件全树 shasum 逐字节同**(含 3MF —— 容器 ZipInfo 时间归一, 内层 model 零改动); 措辞修订后重出, 除 PACK_REPORT.md 外 2261 文件再证逐位同。
- `manifest.meta.created_utc=""` 归空(出包时刻不落盘, 溯源归 git); deferred/report 全数字来自 manifest 单源, 无时钟字段。
- 账只读: 全部跑动后 `ledger_full.json` 仍 `80de7a45ff32…e9ce`, central manifest 仍 `45fed1e8…`, excluded_ids 仍 `fa1a4ef3…`。

## 设计要点(下游消费)

- `build_print_view`(纯逻辑)与 `p1a_slice.run_g2` 前奏同序(classify_full → print_scope → ring_dedup 处置; 处置标打在深拷贝副本, 原账不落标), 并断言宇宙闭合(scope ∪ 排除桶 = 全账且不交); 其正确性即由判据①的逐字节复现背书 —— 零漂移测兼作重建正确性证明。
- `pack()` 内 `zones` 二次过滤作 belt(子账已按段切片, belt 拦到即切片/过滤漂移, 响亮 raise)。
- `manifest.slice` 扩型: `zones` 列表 + 保留 `zone`=首孔键(向后兼容, 计划自审钉) + `arch_idx` 列表化; `coupon` 首件约定登记(1:1 三档配合试片 12 件随包)。
- 留续清单带 `unit_ids` 全表: T3 `pack_verify` 的三方对账(段+留续+排除=2113 单元/1974 口径重算)可直接对集合。

## 验证证据(全部实跑)

- TDD: 先红(collection error: `ModuleNotFoundError: section_pack`)后绿; 合成 fast 测 0.05s 单独先行绿。
- `pytest tests/test_p4_section.py -q` → **5 passed** (99.6s, 含两连跑段包)。
- 全量 pytest 分片前台(>55s 分片转后台通道但满速完成), 六片合计 **497 passed / 0 failed**: ①p4_section+p4_scale+p1_export+p1_printcheck+p1_families+p1_ledger+facts **119**; ②p1_slice **42**; ③p1_scene+l1_body+no_literals+freeze_manifest **58**; ④p2_ledger_v2/geom_math/events/centering+g3_dag/imbalance/thrust **165**; ⑤p2_sequencer+p2_full+p3_pace **69**; ⑥p1_masonry2+register+p3_state+p3_verify **44**。481 基线 + 本任务 5 + P3 线新增 11(test_p3_state/p3_verify, 已入库文件) = 497。
- 生产 CLI 原样跑通并打印守恒/偏差汇总(见上表)。

## 并行纪律

未触碰 P3 线(3d/film/*)与封禁面(ledger_full/砖谱/G1 几何/FIT 分档值/装箱约定零修改 —— zones 仅是账遍历处的过滤); 暂存区仅含本任务路径(export_print.py + section_pack.py + test_p4_section.py + 三个产物 `add -f`)。
