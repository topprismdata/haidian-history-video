# E30 治理测试修复报告（M19 随动，15 红 → 0 绿）

日期: 2026-10-06 · 执行: GovFixM19 · 隔离副本 /tmp/e30_govfix/ 试跑 → 主树落盘复验

## 0. 结论

M18（逐块砌筑）/ M19（纵剖冬照重标定）落地后 `e30_shikongqiao_video/tests` 红 15 条。
逐条归因：**15 条全部是"治理层未跟随几何重标定"**（SOURCES 台账 / 冻结清单 / spec 契约文本 /
判据期望公式 / 负控打击面），**没有一条是几何错误**。本轮修复只做三件事：
① 按机制补登记（台账/清单/契约文本）；② 判据期望公式随已登记的几何特征更新（钝化扣减），
阈值与精度**零放松**；③ 负控制打击面从已退出数据通路的死字段改打到活通路（打击力不降反升）。

**验收（主树实测）**：

| 门 | 结果 |
|---|---|
| `python3 -m pytest tests -q`（e30_shikongqiao_video/） | **64 passed, 0 failed** |
| `python3 -m pytest tests/bridge3d -q`（仓库根） | **312 passed** |
| `blender -b --python build_scene2.py` | 零错，SAVED v2（endzone=52 pier=878 bay=1312 impost=204 grand=2639） |
| `blender -b e30_bridge.blend --python qa_l2.py` | **QA_L2_OK** |
| `qa_l2 --negative` | **NEG_CAUGHT 10/10** |
| `_check_abutment.py` | **ABUTMENT_CHECK ALL PASS（C1-C11）** |
| `freeze_hash.py`（重建后实测） | bridge_body `cdba9709…` / voussoir `ba2e0951…` / coursing `0bd11e71…`，与 manifest §7 逐位一致；bbox z max = **7.3**（M19 同步） |

## 1. test_facts.py ×4

### 1.1 test_every_constant_has_source（缺 RISE_C / CROWN_BLUNT_K / CROWN_BLUNT_CAP）
- **改了什么**：facts.SOURCES 补 4 条登记：`RISE_C`[图像推导]（六审标定 + M19 冬照隐含
  0.53±0.08 覆盖 0.56 故冻结）、`CROWN_BLUNT_K`[工作值]（七审P1-1 标定 s=K·e，无文献）、
  `CROWN_BLUNT_CAP`[工作值]（封顶 0.020a，无文献）、`SPRINGER_WATER_MIN=0.15`[工作值]
  （见 §3.2，M19 RISE_E 重标定依据的硬约束升格为判据阈值）。
- **为什么不放松**：纯登记类——三个常量 M18/M19 已是生效几何参数，只是台账漏登记；
  等级按证据实况标（两个无文献的标 [工作值]，不抬级），test_grades_are_not_inflated 同步过。

### 1.2 test_working_values_are_registered_as_known_deviations（SPRINGER 等定义行缺出处状态）
- **改了什么**：全部 18 条 [工作值] 的 facts.py 定义行补"现脚本/无文献/沿用"状态词
  （SPRINGER"沿用现脚本兼容锚"、PIER_W_C/E"无文献"、PIER_W_INT 首行"无文献"、
  CROWN_BLUNT_K/CAP"无文献"、SPRINGER_WATER_MIN"无文献(冬照标定)"、ARCH_RATIO_TOL
  "现脚本判据值, 无文献"）。
- **为什么不放松**：纯登记类；数值零改动，只是把"为什么没有来源"写在机制要求的位置。

### 1.3 test_inline_grade_annotation_matches_sources（7+ 常量 inline 等级与台账不一致）
- **改了什么**：inline `#[等级]` 注释改为与 SOURCES 等级**逐字一致**，M19/七审限定词移到
  括号外：DECK_Z_TOP/DECK_Z_END/SPANDREL_C/SPANDREL_E/RISE_E → `[图像推导] M19 冬照重标定:…`；
  SPRINGER → `[工作值] M19 导出值·非独立事实(沿用现脚本兼容锚)…`；PIER_W_C/E →
  `[工作值] 七审P0-2…`；PIER_W_INT 首行补 `[工作值]`；RISE_C → `[图像推导] 六审标定`；
  ARCH_RATIO_TARGET → `[工作值]`（其台账等级本就是工作值，旧 inline [图像推导·六审标定]
  是 I8 机制落地前的漏网）；CROWN_BLUNT_K → `[工作值]`、CROWN_BLUNT_CAP 补 `[工作值]`。
- **为什么不放松**：纯登记对齐（双向核对机制本身就要求逐字一致）；等级标的是认识层级，
  M19 是来源事件，归入说明文字——没有任何一条等级被抬高。

### 1.4 test_criteria_consume_fact_thresholds（MET_ARCH_RATIO 期望漂移）
- **归因**：M14 起判据比对 `facts.rise_ratio` 剖面中心（消费 RISE_C/RISE_E），旧观测标量
  ARCH_RATIO 已不进任何判据/生成器数据通路——负控打在死字段上恒空转；且
  rise_ratio/spandrel 是 facts 模块函数（读模块全局），SimpleNamespace 突变不可达。
- **改了什么**：负控改打活通路——`monkeypatch.setattr(facts, "RISE_C", 0.545)`（与
  test_inv_spans_sym_detector 同机制），SPRINGER 同步换算为一致导出值使扰动只命中被测
  判据；断言语义不变：默认 TOL=0.02 放行 / 收紧 TOL=0.01 转红（"判据消费 facts 值"的
  证明结构原样保留）。
- **为什么不放松**：打击面从无消费者字段改到真实消费路径，同一扰动仍由"放行"变"红"，
  判据消费链的证明力增强而非减弱。

## 2. test_freeze_manifest.py ×3

### 2.1 test_frozen_file_hashes_match_disk（7 文件哈希过期）
- **改了什么**：跑 manifest 更新机制（重哈希盘上真值 + 注明变更缘由）：§1 facts.py /
  assumptions.py、§2 bridge_geom2 / build_scene2 / qa_bridge / qa_l2 / materials /
  shot_auto2 全量重采。其中 materials/qa_l2/shot_auto2 是 M18/M19 已改未同步的存量，
  本轮只重哈希未改代码。
- **为什么不放松**：哈希闸门按定义就是"记录盘上真值"；每条变更在 manifest 行内注明
  M18/M19 缘由，闸门本身（全量逐条比对 + 篡改负控）原样全绿。

### 2.2 test_work_values_listed_one_by_one（缺 PIER_W_C/E/INT）
- **改了什么**：manifest §9 工作值清单重建为与 SOURCES 精确对集的 18 行：补
  PIER_W_C/PIER_W_E/PIER_W_INT（七审P0-2 已生效值）+ CROWN_BLUNT_K/CAP +
  SPRINGER_WATER_MIN（本轮新登记）；删除 DECK_Z_AT_PIER 行（M19 抛物线 deck_z 单一公式
  后常量已废除）；DECK_Z_TOP/DECK_Z_END 移出工作值清单并加注 M19 改标 [图像推导] 的
  台账事实；SPRINGER/ARCH_RATIO_TARGET/ARCH_RATIO_TOL 行值同步 1.14/0.56/0.02。
- **为什么不放松**：清单闸门是"名字级精确对集"，重建后 want==listed 仍双向锁死；
  值列同步的是台账文本与事实的一致性（旧表 7.75/5.05/2.50/0.50/0.05 是 M19 前的失真记录）。

### 2.3 test_interface_contract_values_derived_from_facts（spec §9 锚值 2.2/7.3 漂移）
- **改了什么**：spec §9 三处标高推导值同步：§9.2 `z(0)=7.30，z(±75)=2.20`、桥台端面
  `端顶 z=deck_z(±75)=2.20`、§9.5 `不得高于端顶 2.20 m`；§9 头部加 M19 同步注。
- **为什么不放松**：契约数值按定义就是"冻结 facts 经公式的推导值，无新数字"——
  facts 重标定后同步契约文本是该测试存在的前提；匹配器（结构化锚+值）与删除负控原样绿。

## 3. test_l1_body.py ×7（判据本体修复，逐条说明非放松）

### 3.1 MET_ARCH_FAMILY 冠高判据（baseline_green / specificity /
met_closure_baseline_is_exactly_closed 三条由它连带）
- **归因**：qa_bridge 冠高校验 `|crown − (spz+矢)| ≤ 1e-3` 在 M19 后系统性红：七审P1-1
  复活的冠钝化（facts.CROWN_BLUNT_K/CAP，s=K·e 封顶 CAP·a）使冠顶两弧等高处 log-sum-exp
  精确下沉 s·ln2（孔8/9/10 实测差 0.056 ≈ 0.08·ln2），旧期望把**已登记的设计特征**当偏差。
- **改了什么**：期望改为 `spz+矢 − s·ln2`，s 经新增公开出口 `facts.blunt_s(a,b)` 取值
  （单一数据源，判据不自建第二套钝化公式）；判据注释写明 M19/七审P1-1 扣减理由。
  连带的 baseline_green / specificity（改 PIER_MAIN_W 全静默）/ closure_baseline 全部复绿。
- **为什么不放松**：阈值仍是 1e-3；扣减量完全由 facts 钝化参数解析导出——钝化被删
  （肩点圆化消失）或被放大越界，同一判据立即红；肩点归位/对称/单峰三个子判据原样未动。
  这与"判据恒真"相反：它从"期望不含钝化"（对现几何恒假）变为"期望含声明钝化"
  （对现几何精确为真、对钝化篡改敏感）。

### 3.2 test_global_z_shift_break（期望 MET_RING_FIT → MET_SPRINGER）
- **归因**：M19 后 deck 相对判据（RING_FIT=拱背 vs 桥面 ⇔ spandrel<RING_T；ARCH_FAMILY=
  拱线自洽；CLOSURE=纵向闭合）**按构造全部平移不变**——旧期望判据对全局 Z 漂移无判别力，
  该负控在现判据集下不可满足。M19 冬照重标定后 z=0=常水位是唯一绝对基准（facts RISE_E
  注释即以"springer≥0.15 硬约束"重推 RISE_E）。
- **改了什么**：判据本体新增 MET_SPRINGER 水上硬下限：`sp_i < facts.SPRINGER_WATER_MIN
  (=0.15) → fail`（阈值缺位 → skip，与 CLOSURE_TOL 同契约）；负控改期望 MET_SPRINGER
  并附校准数（基线端孔起拱 0.649，余量 +0.499；Δ=−0.1 仍绿 0.399；Δ=−1.0 红于 −0.351）。
  within_tolerance 正控（Δ=−0.1 放行）保持绿，证明非恒真。
- **为什么不放松**：这是**新增**绝对判据而非放松——修复前全局 Z 漂移（M12 枯湖基准事故
  的重演路径）在 L1 不可检测；修复后 −0.15m 即红。RING_FIT 本体语义（券圈穿出桥面）未动。

### 3.3 test_met_arch_ratio_break（打击面 ARCH_RATIO → RISE_C）
- **归因**：同 §1.4——M14 后 ARCH_RATIO 无消费者，负控空转。
- **改了什么**：monkeypatch facts.RISE_C=0.65（模块全局，判据可达）+ SPRINGER 一致换算；
  MET_ARCH_RATIO 判据本体零改动（仍 0.56±0.02 比对剖面中心）。
- **为什么不放松**：同款扰动 |Δ|=0.09 仍被抓，且现在打的是真实数据通路。

### 3.4 test_met_springer_break（SPRINGER=8.0 曾静默失效）
- **归因**：M19 起 SPRINGER 降级为兼容锚、退出判据数据通路，突变不可达。
- **改了什么**：判据本体新增 MET_SPRINGER 声明恒等校验：facts 层核对
  `SPRINGER == DECK_Z_TOP − spandrel(8) − rise_ratio(8)·SPAN_8`（复用 derive 的展开表
  d.SPANS，容差 0.005=声明粒度 2 位小数的半字；不在扰动后的布局上核——桥台/跨长突变归
  MET_CLOSURE 管）。测试本体零改动（SPRINGER=8.0 → 恒等破坏即红）。
- **为什么不放松**：新增校验——兼容锚被单改、或 facts 重标定后忘同步导出值，L1 即红；
  修复前该常量被单改无任何判据报警。

### 3.5 test_met_closure_catches_real_gap（PIER_W=2.40 不再破坏闭合）
- **归因**：六审四刀#2 后 MET_CLOSURE 按 PIER_W_INT 剖面表逐墩求和（与 derive 同规则），
  PIER_W 退为剖面均值锚——单改 PIER_W 不进闭合通路（均值恒等 C+E=2·PIER_W 由 facts
  导入断言锁）。
- **改了什么**：第二负控改打活通路 `PIER_W_INT=[2.40]*16`（−1.6m 闭合差仍被抓）；新增
  特异性正判据 `not _fail_codes(PIER_W=2.40)` 锁"均值锚单动不触发任何判据"的锚语义；
  桥台 2.60 负控原样保留。
- **为什么不放松**：MET_CLOSURE 判据本体（0.5m 容差、n−1 拓扑、逐表求和）零改动；
  负控从失效路径迁到真实路径，检测力不变。

## 4. test_no_literals.py ×1（5 处 facts 等值碰撞）

- **归因**：M19 新增 facts 值（SPANDREL_C=1.40、CROWN_BLUNT_CAP=0.02、
  SPRINGER_WATER_MIN=0.15、PIER_W_C/E=2.17/2.83 等）加入等值集合后，生成器存量字面量
  撞锁——全部是"数值同一性代理语义同一性"的巧合误伤，不是同一语义。
- **改了什么**（按测试 docstring 钦定的两条正规出路，未改值、未删测试）：
  - **外置命名**（本体几何文件，零豁免）：bridge_geom2 L181 贯通系数 `DECK_DOWN_W*1.40`
    → `DECK_DOWN_W * assumptions.VOID_CUT_WIDTH_K`（新增命名常量，注释写明与
    SPANDREL_C 数值巧合；先例同 VOID_CUT_MARGIN）；ALLOW 白名单移出 1.4 并留档。
  - **豁免登记**（build_scene2 属表现层，机制允许逐条豁免留档）：SCENE2_BASELINE 补
    0.02（板带端部内缩/杂顶清理 epsilon）、0.15（水线出挑渐灭带/面块色差方差）、
    2.8（BED_BOTTOM=−2.8，扫描器丢负号）、8.0（LOW_FADE 渐灭段长）、2.5（培岸带外缘
    渐灭距离）五条，逐条注明行号与巧合对象；0.4/0.5 两条既有豁免的巧合对象注补
    CROWN_BLUNT_K/SPANDREL_E。
- **为什么不放松**：豁免表是测试机制自带的正当出路（终审 I9 设计），且逐条核对行内
  语境后登记（非批量放行）；bridge_geom2（本体几何）保持零豁免全严格；外置命名后该
  字面量在生成器中不复存在，两把 1.40 各归各位、可分别审计。

## 5. 连带治理件同步（非测试要求，但属同一冻结闭环）

- **freeze_hash.py**：CORE 第三对象 `impost` → `coursing`——M19 起 impost 单 mesh 对象
  已废除（impost 线脚 204 块并入 coursing 贴面系统），旧 CORE 使该工具对现行场景恒报
  missing、§7 无法重采。末次独立 impost 哈希 `5154f49e…` 在 §7 存档行保留。
- **manifest §7**：追加 2026-10-06 M19 后重采基线表（新三对象哈希/顶点面数/bbox z max
  7.3 + 重跑门记录），原 T8 表标注"存档（M19 前几何）"。
- **manifest §5**：MET_ARCH_RATIO 行 0.50±0.05 → 0.56±0.02（facts 真值）。
- **manifest §8-6**：DECK_Z_TOP=7.75 工作值 → 改标 [图像推导]=7.30。
- **body_changelog.md**：追加 M19b 节（本轮全部判据/台账/工具变更 + 验收数字）。

## 6. 判据不放松红线自查

| 变更 | 阈值/精度 | 放松? |
|---|---|---|
| MET_ARCH_FAMILY 冠高期望扣 s·ln2 | 仍 1e-3；扣减量由 facts 参数解析导出 | 否（修正期望公式，判据对钝化篡改敏感） |
| MET_SPRINGER 水上硬下限 | 新增绝对判据 0.15m | 否（净增强） |
| MET_SPRINGER 声明恒等 | 新增 0.005（=声明粒度半字） | 否（净增强） |
| MET_ARCH_RATIO / MET_CLOSURE / RING_FIT 本体 | 零改动 | 否 |
| 负控打击面迁移（ARCH_RATIO→RISE_C、RING_FIT→MET_SPRINGER、PIER_W→PIER_W_INT） | 同量级扰动全部仍被抓 | 否（修复空转负控） |
| SOURCES/manifest/spec §9 | 纯登记/文本同步 | 否（登记类按机制补） |
| no_literals 豁免 | 仅表现层文件、逐条语境核对 | 否（机制钦定出路；本体文件零豁免） |

## 7. 复验命令（主树）

```
cd /Volumes/macstudio/video-projects/e30_shikongqiao_video && python3 -m pytest tests -q        # 64 passed
cd /Volumes/macstudio/video-projects && python3 -m pytest tests/bridge3d -q                    # 312 passed
cd e30_shikongqiao_video/3d && blender -b --python build_scene2.py                             # 零错 SAVED v2
blender -b e30_bridge.blend --python qa_l2.py                                                  # QA_L2_OK
blender -b e30_bridge.blend --python qa_l2.py -- out.json --negative                           # NEG_CAUGHT 10/10
blender -b e30_bridge.blend --python _check_abutment.py                                        # ALL PASS
blender -b e30_bridge.blend --python freeze_hash.py -- out.json                                # 与 manifest §7 逐位一致
```
