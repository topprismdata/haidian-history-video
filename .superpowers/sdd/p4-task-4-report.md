# P4-T4 报告: 装配图(每孔+段总图) + 分号位表 + 施工卡(sequence 子序列钉)

日期: 2026-10-08 · 执行: P4T4Asm · 计划: docs/superpowers/plans/2026-10-08-p4-print-pack.md Task 4
状态: **完成**。commit: `feat(e30): P4-T4 装配图五张+施工卡(sequence子序列钉)`

## 交付物

| 文件 | 说明 |
|---|---|
| `3d/section_pack.py` | 修改(装配段): `bed_layout`(分号位重放)+`assembly_csvs`(每孔 CSV)+`build_cards`/`card_order_rows`/`card_lint`(施工卡+小 lint)+`render_section_assembly`(段总图)+`png_strip_meta`(PNG 去元数据)+`assembly_main`(装配门 CLI, blender/纯 python 双入口) |
| `tests/test_p4_section.py` | 追加 4 支: `test_five_assembly_orthos_exist` / `test_section_overview_exists` / `test_card_subsequence_order` / `test_card_tag_no_history`(先红后绿, 红=产物缺席实跑确认) |
| `3d/out/print/section5/assembly/ARCH07..11.png` | 每孔装配图 5 张: **直接复用 P1A `p1a_slice.render_assembly`**(同函数同观感: -Y 正射/Cycles 1 sample/role 配色/短 id 标注), 3200px 宽 |
| `3d/out/print/section5/assembly/ARCH07..11.csv` | 分号位表 5 张: unit_id→batch→床位(slot/x_mm/y_mm/w/d/diag/fit/role/material/place_seq), 行=(batch,slot) 放置序 |
| `3d/out/print/section5/assembly/section_overview.png` | 段总图 1 张: 五孔世界位拼合侧视 4800px + 墩位缺口标注 + M5(a) 底座端槽示意 + 图注 [设计选择] |
| `3d/out/print/section5/construction_cards.md` | 施工卡: 批次总表(34 床, 今日打印) + 装配次序(71 stage/1123 行, 今日粘接) |

## 出图实现选择(计划两种路径的取舍)

**走了 blender**(`blender -b --python 3d/section_pack.py -- --assembly`, 本机 blender 5.2.2 LTS 真跑):
- 每孔图=逐字节复用 P1A 出图函数 `render_assembly`——封禁面纪律下零复制。
- 段总图 P1A 无现成函数: 本体=P1A 场景原语的组合(`world_mesh`/`_flat_mat`/`_ROLE_RGB` 同源, 相机/渲染参数同式), 段级注记(墩位缺口/端槽示意/图注)为新增。
- 门控语义: blender 依赖只在**生成侧**(装配门), 判据查盘不重渲——产物入库为 tracked, 测试无 blender 也跑。
- 标注文字中文用 Hiragino Sans GB(blender `fonts.load` 实测可载), 载入失败降级 ASCII 文案。
- 纯 python 备选路径已实现未采用: `python3 3d/section_pack.py --assembly --cards-only`(卡+CSV 不触 bpy)。

## 三判据(plan T4 Step1)验证证据

**① 五张装配图+分号位表(`test_five_assembly_orthos_exist`)**
- 5 PNG 在盘(2.4-2.9MB, PNG 签名+逐块 CRC 验)+5 CSV 在盘; **CSV 行数==该孔打印单元数**(192/247/245/247/192, 与 manifest 分孔恰等, 不重不漏); batch 列与 manifest 单源; 床位坐标在 220 床内。
- 床位来源=**重放非权威**: `bed_layout` 以 export_ledger 同源足印(床平移网格极距-2x clearance, 打印毫米)重放 `EP._pack_beds` 货架游标(90° 归一/45° 外接方/换行换床逐步同式), **belt 与 manifest.batches 逐项对账**(批成员有序/fit_diagonal/oversize/used_mm ≤1e-6mm/批数)——装箱约定漂移即响亮 raise(P1A 约定零改动的可执行钉)。
- CSV 并集=1123; 每批 slot 集合=0..n-1; `place_seq`↔unit 与 sequence.json 1:1 互证(独立脚本全量抽验)。

**② 施工卡序==sequence 原序过滤(`test_card_subsequence_order`)**
- 期望子序列由测试**独立重算**(sequence.json: stage 依给定序 x 事件依 event_range 原序 x stone_id∈段单元), 与卡解析行**逐项相等**: 1123 事件恰一次全覆盖, 71 stage。
- 负控在测: 期望序非空且 `expected != expected[::-1]`(比较器有齿)——任何重排(按批/按 id/按孔聚类)必红。
- 口径说明: 段单元事件=PLACE_STONE 且 stone_id∈manifest 单元, 恰 1123/1123(中置架/卸架类事件 CEN-* 与 stone_id=None 者非单元行, 不入序; 卡头"口径"行有声明)。stage 过滤即"event_range 与段石交集"。

**③ 序行历史定性(`test_card_tag_no_history`)**
- 装配次序节 1123 行**逐行含字面 [工程推断·非史料]**(装配/卸架序无工序史料锚, P2 关账口径=T2/T7b 现行)。
- `SEC.card_lint`: **判域独立小 lint**(只查『装配次序』节序行: 缺字面标注→ORDER_ROW_UNTAGGED; 行内方括号标签过 narration 标签文法 `_tag_ok`→TAG_NOT_IN_VOCAB), **词表复用 narration_lint**。选择理由: narration 三闸(G0 编号/禁词/引语)面向口播稿, 对制造卡是假阳性面; 标签文法单源保词表不漂移。负控实跑: 去标注×2 行、伪标签 [史实] 均被抓。
- lint 不跑不构绿: `build_cards` 自检 card_lint 零发现才落盘(qa_l2 I4 同纪律)。

## 段总图注记的量化验证(看图判断全部转数值)

- **墩位缺口 4 带**: 相邻孔 zone 石 x 范围含拱上背衬互叠 ~2.2m(实测 gap=-2.17~-2.26m, 不可作锚)→改锚**相邻孔券环外缘**(立面可见孔边), 间隙异常即 raise。像素实测红簇中心 [1122,1960,2837,3674] vs 世界墩心推算 [1135,1972,2828,3665](82px/m), 差 ≤13px(≈0.16m)。
- 孔标签 5 簇 x=[719,1547,2402,3251,4059] vs 孔心 RING xc 推算 [726,1544,2400,3256,4074]; 底座带蓝采样 14921(下缘), 端槽标 2 簇(两端), 通栏图注 1 簇居中, 图注含 **[设计选择]** 字样。
- M5(a) 口径: 底座**不打印**, 图中只画端槽示意线框+文字声明(计划封禁: 打印底座=越界; 数字规格归 T5 BASE_SPEC)。

## 幂等(全局约束)

- **卡+CSV 两连跑逐字节同**, 且跨解释器同(系统 python3 产出 ↔ blender 内重产出, sha256 全等×6)。
- **每孔 PNG 两连跑逐字节同**(sha256×5): Cycles METAL 1 sample 固定 seed 像素确定 + `png_strip_meta` 剥离 blender 渲染统计块(tEXt/iTXt/tIME——整文件 sha 不稳的唯一来源, IDAT 像素流零改动, 逐块 CRC 重验)。
- PNG 去元数据后块类型 ⊆ {IHDR,PLTE,IDAT,IEND} 实测(6 张全洁净, 文件尾对齐)。
- 账只读: 全部跑动后 ledger_full `80de7a45`/central manifest `45fed1e8`/excluded `fa1a4ef3` 逐位未动; section5 manifest `ca1a58f4` 未动。

## 全量 pytest(分片前台, 分母 collect-only 实测)

- 分母口径: `pytest tests/ --collect-only -q` 实测 **524**(=T2 收官 497 + 本任务 4 + P4-T3 conservation 6 + P3 线入库增量 17); `research/geo/test_geo.py`(16 项)与 `3d/ab_texture_test.py`(模块级 import bpy 的历史散件)不在 tests/ 分片口径内, 沿 T2 先例。
- 七片合计 **524 passed / 0 failed**: ①p4_section+p4_scale+p4_conservation+p1_export+p1_printcheck+p1_families+p1_ledger+facts **129**; ②p1_slice **42**; ③p1_scene+l1_body+no_literals+freeze_manifest **58**; ④p2_ledger_v2/geom_math/events/centering/g3_dag/imbalance/thrust **165**; ⑤p2_sequencer+p2_full+p3_pace **72**; ⑥p1_masonry2+register+p3_state+p3_verify+p3_film_layout+p3_render_smoke+p3_script_lint+p3_silhouette **52**; ⑦p3_geometry **6**(首轮分片漏配, 补跑绿)。总墙钟 ≈14.5min, 全前台/后台通道满速(无 P2 期 2.4% 限流复现)。
- 本任务测试单独计时: `test_p4_section.py` 9 支 **102.3s**(含两连跑段包 fixture)。

## 产物 sha256(供 T6 sidecar 登记)

| 文件 | sha256 前 16 |
|---|---|
| section5/construction_cards.md | `e4af27556b89a912` |
| assembly/ARCH07.csv | `657fc2986d89b566` |
| assembly/ARCH08.csv | `5014e1fa519a196b` |
| assembly/ARCH09.csv | `8fe28305028cb7e6` |
| assembly/ARCH10.csv | `0a54ef18bb653e52` |
| assembly/ARCH11.csv | `67448520945a5c43` |
| assembly/ARCH07..11.png(×5) | `15a9e4c3c2267876` / `faa65cf823dfb6bc` / `a7331d21d16fe5af` / `7204b5cf7b7e25c7` / `34bc5411e0988cf6` |
| assembly/section_overview.png | `4b5064c0d30f4a24`(墩位修正后重渲, 以入库版为准) |

## 设计要点(下游消费)

- **床位权威=分号位表 CSV**; 施工卡批次总表只给床号/占用/行数, 不重复列单元(1123 行清单在 CSV, 卡内装配序行带批+床位交叉引用)。
- `card_order_rows` 解析器 lint/测试共用; 测试侧以 sequence.json 独立重算对账, 解析器漏/重排必红(同源风险被独立期望抵消)。
- sequence.json 为 P2 派生产物(不入库, gitignore), 卡内已嵌完整子序列(stage/seq/unit 三元组), 溯源链在 repo 内闭合; 相关测试与其余 ledger 依赖测试同层(真账亦为门产生产物)。
- PNG/civil 产物均 `add -f` 入库(判据要求 tracked 在盘, 干净树可见); 生成可由装配门逐字节再生。

## 并行纪律

未触碰 P3 线(3d/film/* 及其测试)与封禁面(ledger_full/砖谱/G1 几何/FIT 分档值/**P1A 装箱约定**——bed_layout 只重放+对账, export_print 零修改); 暂存区仅含本任务路径(section_pack.py + test_p4_section.py + 12 个产物 `add -f` + 本报告)。
