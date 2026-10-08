# P4 代表段打印工程 print-pack 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把中央五孔段（ARCH07-11，2747 石）出成可执行打印制造包（分批/装配图/施工卡/进度账/留续清单），三方守恒可机验（P4 门）。

**Architecture:** 复用 export_print 引擎（zones 参数化扩展）+ scale_params 薄特征审计 + 双实现守恒 validator + print_status 状态账。几何/砖谱/石账零触碰；P1 代码可扩不可改语义（inset/FIT/装箱约定不动，P1A 实证口径）。

**Tech Stack:** Python 3.9.6（stdlib+numpy）、bpy（仅网格提取路径，若需）、既有 export_print/printcheck。

## Global Constraints

- Python 3.9.6；测试 blender-free（网格路径门控 skipif）
- **封禁面**：ledger_full/砖谱/G1 几何/`FIT_PRINT_MM` 分档值/P1A 装箱约定（贪心+45° 斜置）零修改；D2 已定稿=沿用 FIT
- 材质组语义钉死：qingshi=青石面石 / maoshi=毛石背衬与 core（masonry2 单源）
- 段=ARCH07-11；片名口径"十七孔桥·中央五孔 1:50"，产物与文档禁"全桥"字样（留续清单除外，其语义就是"非全桥"）
- 幂等：所有落盘产物两连跑逐字节同；sidecar 登记 section5 manifest/deferred/print_status 模板
- 长命令前台；中文 commit `feat(e30): P4-Tn ...`；全量 pytest 零红收尾
- M5 默认 (a) 底座不打印——只出 BASE_SPEC（尺寸/端槽），打印它=越界

## 文件结构

| 文件 | 职责 |
|---|---|
| `3d/scale_params.py` | 新建：薄特征审计（<1.2mm 打印当量→清单）+ per-stone print 参数装配（不回写 ledger） |
| `3d/export_print.py` | 修改：`export_ledger(..., zones=None)` 选区参数（默认 None=现行为不变） |
| `3d/section_pack.py` | 新建：段包 CLI（出包+守恒+装配图+施工卡编排） |
| `3d/pack_verify.py` | 新建：三方守恒**独立**重算（不 import export_print 的装箱码） |
| `3d/print_status.py` | 新建：进度账 CLI（待打/已打/已检/已装/重打改派） |
| `3d/out/print/section5/`、`deferred_holes.json`、`thin_features.json`、`BASE_SPEC.md` | 产物 |
| `tests/test_p4_scale.py` `test_p4_section.py` `test_p4_conservation.py` `test_p4_status.py` | TDD |

---

### Task 1: scale_params 薄特征审计

**Files:** Create `3d/scale_params.py`; Test `tests/test_p4_scale.py`

**Interfaces:** Consumes ledger_full + families 网格（mesh 顶点）；Produces `thin_features(ledger, scale=1/50, floor_mm=1.2) -> [{"stone":id,"min_feature_print_mm":x,"where":"bbox_min_dim|face_sliver"}...]`（保守用块最小维×scale×1000，与 printcheck 壁厚口径区分并在 docstring 写明）+ CLI 落 `thin_features.json`（段内子集）。

- [ ] **Step 1 失败测试**：`test_thin_detect_synthetic`（手搭一块 0.02m 薄石→打印当量 1.0mm<1.2 必列）；`test_section5_thin_list_empty_or_documented`（真账段内清单落盘，若非空→逐条 M3 豁免注记字段，空则断言空——**如实测如实报，禁调 floor 凑空**）；`test_no_ledger_writeback`（跑前后 ledger sha 不变）
- [ ] **Step 2 红 → Step 3 实现 → Step 4 绿 → Step 5 commit** `feat(e30): P4-T1 薄特征审计(打印当量口径, 不回写账)`

### Task 2: export_print zones 参数 + 段包出图

**Files:** Modify `3d/export_print.py`（加 `zones: Optional[List[str]]=None` 过滤参数，默认行为逐字节不变——用现 central_slice 重跑对 sha 证之）; Create `3d/section_pack.py`; Test `tests/test_p4_section.py`

**Interfaces:** Produces `out/print/section5/`：manifest.json（batches/stones/clearance 双值/coupon 首件约定，slice 字段扩为 `{"zones":["ARCH07"..'ARCH11'],...}`）、STL/3MF 目录按 maoshi/qingshi 分、`deferred_holes.json`（12 孔清单+计数）。

- [ ] **Step 1 失败测试**：`test_default_zone_none_reproduces_central`（zones=None 重跑中央孔→manifest 与盘上 45fed1e8 语义等值（除时间字段），证参数化零漂移）；`test_section5_counts_conservation_basic`（段石数 2747=Σmanifest.stones+Σskipped，双计数）；`test_deferred_complement`（deferred ∪ section = 17 孔全集不交）
- [ ] **Step 2 红 → Step 3 实现（export_print 过滤点在账遍历处，勿动装箱/FIT）→ Step 4 绿 → Step 5 commit** `feat(e30): P4-T2 段包出图(zones参数默认零漂移+deferred互补)`

### Task 3: 三方守恒双实现 validator

**Files:** Create `3d/pack_verify.py`; Test `tests/test_p4_conservation.py`

**Interfaces:** Consumes section5 manifest + deferred_holes + excluded_ids + ledger；Produces `verify_pack() -> {"ok":bool,"三方":{"section":n,"deferred":m,"excluded":k},"total":1974}`——**独立重算路径**：从 ledger 按 printcheck 排除口径重推 1974 全集（不 import export_print 装箱码），与两清单对集合。

- [ ] **Step 1 失败测试**：`test_three_way_exact`（段+留续+排除=1974 全桥账，逐 id 集合等式）；`test_neg_steal`（副本：从 deferred 抽一个 id 塞进 section 清单→必红）；`test_neg_drop`（删一个 unit 不出现在任何一侧→必红）
- [ ] **Step 2 红 → Step 3 实现 → Step 4 绿 → Step 5 commit** `feat(e30): P4-T3 三方守恒双实现(偷挪/丢失负控在测)`

### Task 4: 装配图（每孔+段总图）+ 施工卡

**Files:** Modify `3d/section_pack.py`（装配段）; Test `tests/test_p4_section.py`（追加）

**Interfaces:** 每孔 assembly_ortho 复用 P1A 出图函数；段总图=五孔侧视拼合+墩位缺口标注（M5(a) 底座端槽示意）；施工卡=sequence.json 中段内事件子序列（stage→unit→"今日打印/今日粘接"），序标 [工程推断·非史料]。

- [ ] **Step 1 失败测试**：`test_five_assembly_orthos_exist`（5 张 PNG+分号位表 CSV）；`test_card_subsequence_order`（施工卡事件序==sequence 原序过滤，不许重排）；`test_card_tag_no_history`（卡内卸架/装配序行含 [工程推断·非史料] 字样，lint 词表复用）
- [ ] **Step 2 红 → Step 3 实现 → Step 4 绿 → Step 5 commit** `feat(e30): P4-T4 装配图五张+施工卡(sequence子序列钉)`

### Task 5: print_status 进度账 + M5 底座规格

**Files:** Create `3d/print_status.py`、`out/print/section5/BASE_SPEC.md`; Test `tests/test_p4_status.py`

**Interfaces:** `print_status.py`：`init/advance/query` 三命令（batch×unit 状态机：pending→printed→checked→glued；printed→redo(重打改派)→pending；非法迁移 raise）；幂等落盘+schema 版本头。BASE_SPEC.md：底座尺寸=段包络+端槽位（从 manifest bbox 推导，数字进文件），标 [设计选择]。

- [ ] **Step 1 失败测试**：`test_status_legal_transitions`（全合法迁移表驱动）；`test_status_illegal_raise`（pending→glued 等非法→raise）；`test_status_idempotent`（两连跑逐字节同）；`test_base_spec_numbers_from_manifest`（规格数字与 manifest bbox 一致性重算）
- [ ] **Step 2 红 → Step 3 实现 → Step 4 绿 → Step 5 commit** `feat(e30): P4-T5 进度账状态机+底座规格(数字推导钉)`

### Task 6: sidecar 登记 + P4 关账

**Files:** Modify `3d/refs/artifact_sha256.txt`; Create `.superpowers/sdd/p4-progress.md`

- [ ] **Step 1** section5 manifest/deferred/thin_features 入 sidecar（沿用 BLK-1 有牙纪律：路径集合钉+缺失 fail-loud）
- [ ] **Step 2** 全量 pytest 零红；`pack_verify` CLI 输出贴关账报告；p4-progress.md（含 ~913 单元/500h 预估的**实测修正值**——以出包实数为准，如实替换 spec 估算）
- [ ] **Step 3** commit `feat(e30): P4-T6 sidecar登记+关账报告(实测单元数)`；**停**：打印执行归用户台架，P4 交付=制造包

---

## 自审记录

- spec §3.1-6 全覆盖：T1(1)/T2(2)/T4(3)/T5(4,5)/T3+T6(验收面)/T2(留续=§0 M1)。
- 无占位符；zones 默认零漂移测（T2S1）防 P1 行为回归；守恒 validator 独立路径防同义反复。
- 类型一致：manifest.slice 字段扩型向后兼容（保留 zone 键=首孔语义并入 zones）。
