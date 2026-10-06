# P1 Task 8 报告 — G2 门（RING/IMPOST 入账 + 全桥 printcheck + 中央孔试印包）

**日期**: 2026-10-07
**分支**: e30-bridge-body
**Commit**: `feat(e30): P1-T8 G2门(RING/IMPOST入账+全桥printcheck+中央孔试印包)`

## G2 verdict

```
G2_VERDICT PASS stones=5935 ring=193 impost=492 gap_pairs=340
```

- `out/print/g2_report.json`: verdict=**PASS**, check_stone n=1974 打印单元 fail=0,
  gap_check 340 对(17 孔×20) fail=0（71 对 AABB 幻影经面级精判排除, 4 对背衬
  干涉入 assembly_fit 桶, 见"上游发现"）。
- 复现: `blender -b --python 3d/p1a_slice.py -- --g2`（约 17s）。

## 交付清单

1. **`3d/p1a_slice.py`**（新）:
   - `build_ring_entries()` / `build_impost_entries()`: spy 捕获
     `masonry.build_voussoir` / `masonry.build_impost` 的逐石图元调用参数,
     用**同一图元**（`masonry._voussoir` / `masonry._stone`）逐石重放提取网格
     （单一真相, 无第二套楔形公式）。数量互证 assert 响亮: RING 193 ==
     masonry_stats.voussoir_total 且逐孔分布一致; IMPOST 492 ==
     coursing_regions.impost。**顶点多重集互证**: 全局 bmesh 顶点表 ==
     逐石重放拼接表（1e-9 量化, 逐位一致）。
   - `make_ring_entry`（role RING, family `ring-wedge`, 质心锚, params 记
     xc/k/stations/angles/ring_t/lift 溯源）与 `make_impost_entry`（role
     IMPOST, family `impost-step`, wedge 前脸锚, params 记 xc/step/seg/proud）。
     全部纯函数, blender-free 可测。
   - `bridge_ledger_full()` = 现链 5250 + RING 193 + IMPOST 492 = **5935**,
     `validate_ledger` 0 错。
   - `print_scope()` / `run_g2()` / `gap_check_pair()` / `export_slice()` /
     `render_assembly()` / `write_slice_notes()`（见下）。
2. **masonry2 锚分派**（接线清单⑦）: `ring-wedge` 质心锚（off=transform,
   刻意不进 `_ANCHOR_MIN_CORNER`——不参与桥面截顶）; `impost-step` 与
   wedge-std 同前脸锚公式; 未知族照旧 raise。
3. **families.py**: `_baked` 载荷族（params.bake = 提取时的原网格, 确定性
   还原, 无第二套公式）, 注册 `ring-wedge`/`impost-step`。
4. **G2 全桥 printcheck**: 每打印单元 post-inset `check_stone`
   (scale=1/50, min_wall_print_mm=1.2) + 每孔 20 对相邻缝对 `gap_check`
   → `out/print/g2_report.json`（fail 列表空; scope 如实标: 雕件 P4 白名单外、
   桥台不入账、四个排除桶全带 id 与理由）。
5. **中央孔试印包** `out/print/central_slice/`: ARCH09 打印单元 234 石
   （RING 17 全深楔 + IMPOST 24 + SPANDREL 94 + BACK 94 + CORE 5）→
   STL+3MF×234 + `ledger_print.json` + `manifest.json`（family×count×volume、
   8 批 220mm 装箱、FIT 双值 TIGHT 92/NORMAL 140/LOOSE 2、超床件 2 块
   独占批: RING.B01/B17）+ `assembly_ortho.png`（3200×1709 正射侧视,
   RB/IM/S id 标注）+ `SLICE_NOTES.md`（1:50 口径/缝打印当量/超床清单/
   切片器朝向注意）。总体积 1546 cm³, 12cm³/h 经验估时 ~129h。
6. **测试**: `tests/test_p1_slice.py` 19 条 blender-free 单测（锚分派、baked
   还原、条目 id/账本校验、materialize 可逆性+锚漂移负控、耳切三角化、
   相邻对采样、G2 报告结构闸门+4 组篡改负控、gap 两级判负控、G2 常数）。
   Blender 侧互证（数量/顶点）在 `--g2` 运行内自 assert。

## 必须记录的三个技术发现（本轮实测, 非文档推演）

1. **耳切三角化是硬需求**: `_voussoir` 帽面是薄环扇（非凸）, 任意顶点扇形
   三角化产生覆盖/反绕三角 → RING 8 石 THIN_WALL(0.000mm) 假阳 + 裁剪片
   SELF_INTERSECT。`triangulate_faces`（四边形对角剖分 + ≥5 边形耳切,
   顶点逐位不动）消掉 784 NON_PLANAR + 110 SELF_INTERSECT + 8 RING 假阳。
2. **gap_check AABB 对径向缝是结构性假阳**: 券环放射缝面沿法向倾斜 ~70°,
   世界 AABB 必然互相咬合（W2 契约的转角假设救不了 AABB 判本身）。
   `gap_check_pair` 两级判: AABB 快筛 + 面级精判（printcheck 判据复用 +
   共面同向法线正面积重叠规则——对接缝反法线不算）。实测 340 对中 71 对
   幻影, 0 对真穿（除背衬桶外）。负控: 真互穿盒必抓, 平行错位斜带
   （真缝隙）必放。
3. **上游遗留: 背衬退让线与族网格锚定差半 taper**（⚠ 报请主控裁决后续）:
   `masonry2.backing_stones` 的退让比较以墙面线为基准, 但 wedge-std 族
   网格前/内缘面锚定在层带中点（ty=hw(xm,zm)+proud）, 实际内缘面比模型低
   taper/2。G2 抽样实测 4/66 spandrel-back 对实体互穿（最深 ~38mm 模型）,
   全桥估计 ~4% BACK 石（2290 块中 ~90 块）。本轮**不改上游**（T4/T5 已闭环,
   语义归其所有）, 处置: `gap_check.assembly_fit` 桶全量记录（ids+深度）+
   SLICE_NOTES 打印指引"毛石按面石内缘现场修配"。建议后续任务修
   backing_stones 退让公式（注意 test_backing_c1_judgement_boundary_calibration
   的 ±3mm 标定与新余量耦合）。

## scope（如实标注, 非静默收缩）

`print_units 1974 + 排除 3961 == 5935（守恒, 报告结构闸门钉死）`:
- in_void 2052（洞内理想化石, 布局即剔除=空气）
- void_cut_fragment 1520（切洞裁剪片: 与 RING 真几何带重复建模, 实测 400+
  件 <6cm 碎片/双壳; 打印以 RING 为准）
- ring_band_overlap 305（未裁剪但足印含券环带边界采样点, 与 RING 双重建模）
- thin_merge 84（post-inset 最小打印壁 <1.2mm 的截顶残层/窄条, 与邻层合印）
- 雕件（CARVE/RAIL/POST/PAVING）P4 白名单外、桥台砌体不入账（接线清单⑤⑥,
  本账本无此类石）。
中央孔切片同口径过滤（zone ∩ print_scope）。

## 回归（隔离树 /tmp/e30_p1/ 先行, 全绿后落地）

| 门 | 结果 |
|---|---|
| e30 tests（隔离树） | 210 passed, 2 failed（=无 git/仓库上下文的环境性失败, 真树通过） |
| e30 tests（真树） | **212 passed**（基线 191 + 新 19 + 2 环境性转绿） |
| bridge3d（真树 repo 根） | **312 passed** |
| proxy 冷重建 + freeze_hash | sha_sorted/nverts/nfaces/bbox **逐位一致**（baseline vs 新代码重建） |
| 真树既有 blend freeze_hash vs core_hash.json | **一致** |
| qa_l2 正检 | QA_L2_OK |
| qa_l2 负控 | NEG_CAUGHT 10/10 |
| proxy 本体路径 | 零触碰（build_scene2.py/masonry.py/facts.py 未改; freeze_manifest 不涉本轮文件） |

## 改动文件

- 新: `3d/p1a_slice.py`, `tests/test_p1_slice.py`
- 改: `3d/masonry2.py`（锚分派两分支）, `3d/families.py`（_baked 两族）,
  `.gitignore`（out/print 审计件白名单: g2_report.json / manifest.json /
  SLICE_NOTES.md; STL/3MF/PNG/blend 仍不入库）
- 产物（入库）: `3d/out/print/g2_report.json`,
  `3d/out/print/central_slice/manifest.json`,
  `3d/out/print/central_slice/SLICE_NOTES.md`
- 产物（不入库, 盘上交付）: `central_slice/*.stl|*.3mf`×234,
  `ledger_print.json`, `assembly_ortho.png`, `3d/out/ledger_full.json`

## 修复轮 (T8b, 2026-10-07, commit c74d54f)

**审查八条 + 审查方三裁 + 主控 1b/2A/六条增量 全部落地; G2 现状 = 诚实 FAIL(主控 2A 预授权红门), 归因清单如下。**

### A1(核心修复, 全绿闭环)
cap_to_deck wedge 截顶改 h/transform[2] 时同步重算 `transform[1] = side*(hw_wall(xm, z0+h2/2)+proud)`(backing front_c 语义同式兼容, 实际只有面石走此路径)。**A1 恒等式复验**(审查恒等式 `pen+BACKING_GAP ≡ −(|ty|−(hw+proud))`): 全链 2290 对逐对余量 **<1e-6mm**; pen>0 **116 对→0**(修复前最大 96.3mm, 全部是截顶石); G2 assembly_fit 实体相交 **30 对→0**(全量跑, 非抽样); 中央孔 0(与本审查方独立测定一致)。修复前 116/142 口径差 = 审查方按截顶石计 142、按 pen>0 对计 116, 同一机制。

### B3+B4(处置宇宙, 机制完整、红门在案)
- 面积判据: RING 烘焙网格逐三角 x-z 投影真剪影栅格(2cm), 分母=链石自身剪影格数; 吞没石(>50%)必排除(单测钉死)。
- volume 宇宙: ring↔{SPANDREL,BACK,CORE} pre-inset(bbox 预筛+面级精判含 B2 包含分支), unique_vol=V(stone)−V(stone∩RING∪) 同栅格同原点同步长; case_A(unique≤1%·V 且 ≤50cm³ 且顶点包含复证)→subsume 出集; case_B→masonry._hole_cut_polyline 单一真相折线 print-view 裁剪(承压带保座石 z<spz−GAP、环 lift 包络计入——首跑两处几何根因已修: 承压带吞环端 193 撞、keystone lift +0.07 出切割线), 同位 partner 对称传播(缝一致性, 二跑 gap 216 的根因); trim_empty 归 subsume 桶; 裁片薄片落 thin_merge("trimmed sliver")。
- final_scope_check: 最终 scope 全量独立 3D 复测(pre-inset), 不从桶成员/处置计数推导; 负控①(禁 subsume+强制 keep → n_colliding>0)真扰动管线验证, 非恒真。
- 负控②③④全落单测(吞没盒 case_A/咬角 case_B/post-inset 拒绝/两环各半 case_B)。

### D6/D7/E8
- excluded_ids.json 桶→ids 全表入库(.gitignore 白名单)。
- spandrel-back 全量跑(不再 20/孔), depth>5mm 或 AABB 交叠>100cm³ 计 fail, 界内豁免全量记账+WARN>50; 字段改名 aabb_min_axis_mm+新增 depth_mm(面级精判)。
- 体积口径: 耳切对角约定敏感性 **6.171e-3 实测复现**(193 环石双对角体积, 最差 ARCH07.RING.B13), 129h 实心体上界、CORE 非加和写入 g2_report.meta.volume_caliber + SLICE_NOTES; 装箱 90°/45° 旋转, 220²对角 311mm 件改 fit_diagonal 非独占批(250x70 负控仍 oversize); SLICE_NOTES 旧"4/66 抽样/~90 块"陈述删除。

### 主控六条回话
1. 裁剪=方案(b)落地(p1a 消费侧, 零触碰 clip_footprint/T7)。
2. 2A 执行: FAIL 即 raise 不出包, SLICE_NOTES 顶部"作废待 T9"横幅已打; **FAIL 时交付物=报告+excluded_ids+覆盖率审计+fail 矩阵, 全部落盘**。
3. subsume 判据按修正版(AND 双条件+B2 复证)落地。
4. 覆盖率审计入报告: in_void 160cm²(≈干净)/void_cut_fragment 262.4m²/ring_band 2.71m²/thin_merge 0.90m²(全桥 17 孔; 审查方中央孔单孔 clip 桶 16.8m² 与我 17 孔 262m²/17≈15.4m² 同量级互证; T8c 单位更正: 原 27.1m²/89.6cm² 两处 10× 单位误记)。
5. 对账表: /tmp/e30_probe/reconcile_arch09.json(35 id 双表共有, 审查方独有 112=已排除桶撞件[其表含 void_cut_fragment 全 population], 我独有 3=partner 传播件)。
6. in_void 桶干净(160cm² 洞缘量化余量); thin_merge 注释改"谁都不单独印"。

### 红门现状(主控 2A 预授权, T9 范围输入; T8c 归因更正)
verdict=**FAIL**: check_stone **106**(全部为带裁片 trim=True 106/106, pre-inset 全过/post-inset 全坏, 1-2 面对级 SELF_INTERSECT); gap **216**(T8c 更正: 全由 C-T8b-1 带裁石 y 落位伪造 —— 坐标系修复后重跑 **216→0**, counterfactual 实证; 原文"与 SELF_INTERSECT 石 id 集合重合、被自交片污染的面级判"不成立: 216 fail 共 **432 端点, 仅 104 ∈ 106 集**); ring↔链残留 **87/903**(T8c 复跑 **85/903**, 逐对明细+体素体积已入 report.final_scope_check.pairs)。归因(T8c 更正, **两项**): ①带裁片网格化质量 —— check ~106(T8c 复审实测: 失败与 FIT 余量大小单调 0.1mm→0/106, 1mm→4, 3mm→8, 7.5/15/25mm→106/106; 与坐标系无关[修复帧重建仍 106/106]、与整体平移无关[y+5m 判定不变]; 交叉三角集中于切割下缘近共线顶点; 原"薄片"措辞作废——本批 bbox 最小维 0.328-0.709m 模型, 非薄片) ②切割线追不上环真剪影 —— final_scope 残留 ~85 + void_cut 桶 262.4m² 无接替材料。判据/桶/阈值零放宽(主控禁令)。legacy clip 存量普查: 870/1520 fail(MULTI_SHELL 401/SELF_INTERSECT 560/THIN_WALL 1154, T5/T7 追偿输入)。

### 回归(真树实测)
e30 tests **224 passed**(基线 212+新 12, 含冻结哈希闸门)/bridge3d **312 passed**/freeze 三对象 sha_sorted **逐位一致**(build_scene2 仅 ledger 链改动)/qa_l2 **QA_L2_OK**+负控 **NEG_CAUGHT 10/10**/_check_abutment **ALL PASS**。中央孔试印包停在 T8 版+作废横幅(2A)。

## T8c 窄修复轮 (2026-10-07)

**范围: 复审 C-T8b-1(带裁石 y 落位)+ W-1(归因与单位更正)+ 重跑 G2 红门 + 复审第二轮可领走账折叠。红门维持红(主控 2A 预授权), 判据/桶/阈值零放宽。**

### C-T8b-1 修复(全绿闭环)
`_ring_trim_mesh` 改走 clip 同款局部管线: 世界足印 poly 先减锚 `lp=[(x-off0, z-off2)]` → `_prism_stitched(lp, yf, yb)`(保留 stitched 单壳) → 顶点 `M2.materialize` 回世界。反例锚 **ARCH03.EAST.SPANDREL.C07.B00**(ty=+3.3298): 修复前世界 y ∈ **[-5.0364, -2.5488]**, 修复后 **[0.8422, 3.3298]**(复审判定 ≈[0.84,3.33], 逐位吻合)。

### G2 红门(重跑实测, 三计数全部落主控区间)
verdict=**FAIL**: gap **216→0** / final_scope **87→85**(∈[80,90], n_pairs 903) / check_stone **106**(106±10; 且新旧 106 为**同一 id 集**, old∩new=106 —— 独立于 y bug, 如复审所判)。depth 记账: 旧 gap 216 条 fail 全为深度 0 的 containment 型命中(复审实测), 随伪落位消失; final_scope 85 条逐对明细入 report(24 条 depth_mm>0, max **60.012mm**; 61 条 depth=0 纯棱交叉退化), 严重度按体素体积降序, T9 首选前三 = ARCH06/12.EAST.CORE.C13.B01 vs RING.C00.B07(depth 60.012mm, ~8.6e4 cm³)与 ARCH09.EAST.CORE.C14.B01 vs RING.C00.B09 —— 与复审预判(CORE.C13/C14.B01 vs RING.B07/B09)一致。

### 材料账(复审领走账落地)
`removed_model_cm3.trimmed` 从恒 0.0 改为 **Σ 逐对 collide_vol_cm3_pre(=77,320,600 cm³ = 7.732e7, 单测钉死恒等)**; subsumed_by_area_bucket **5.83e7 cm³**(182 块, 与复审复算一致)。注: 复审预判 9.702e7 系守卫前口径(含 14 块异石足印传播件, 见下), 守卫后真值 7.732e7。

### 落位回归测试(第二战果: 当场抓出新 bug)
- 钉死③真总体 y 区间: `P.ring_trim_y_violations`(与 run_g2 内断言**同一实现**, 复审⑤升格) 对全部裁石断言世界 y ⊆ 原族整石带 ±1e-6; 总体 **475** 钉死。
- 钉死④真总体 y 符号: EAST 质心 y>0/WEST<0; CORE 全墙胞 y 向对称, 判据换形态 |cy|≤1e-3(实测 20 石全 0.0)。
- 钉死⑤ partner 传播足印契约: CORE→SPANDREL(_partner_id else 分支的错配)**拒绝传播**; 正向 SPANDREL→BACK 仍由既有钉死测试覆盖。
- **第二战果**: 上述③④首轮实测 14/489 石 y 越带 ~0.3m —— 根因 `_propagate_to_partner` 把 CORE kept(x 跨 ~3.2m、z 低一层)整块交给 SPANDREL, 剖面在局部域 [0,h] 外线性外推(例: ARCH07.EAST.SPANDREL.C13.B00 管线 y∈[1.0541,3.7228] vs 族带 [0.8276,3.4093], 裁片还落在别人的 x-z 格)。修复=角色守卫; 14 石回 scope 由主循环按自身足印裁决; 复跑总体 489→475, 三计数不变(106/0/85)。
- validate_g2_report 结构闸门 +4 组负控: final_scope.pairs 长度==n_colliding / n_trimmed↔trimmed_ids↔removed_model_cm3.trimmed 互证 / coverage uncovered_cm2↔uncovered_cells 同栅格互证(防审计被静默清零) / fail_matrix 求和==n_fail(真实嵌套结构 {code:{role:count}}); 合法 FAIL 变体作对照。
- 其余: trim 材料账恒等断言; run_gate excluded_ids↔report 写后读回互证; run_g2 FAIL 分支交付卫生(manifest `superseded:true/superseded_by:"T8c"`+reason; SLICE_NOTES 用现行 writer 重生成正文杀掉 T8 版 "verdict: PASS" 行与已判不实的"抽样实测 4 对/~4%"句, 再压作废横幅)。
- 卫生小账: sliver 双判第②条删除(2×clr 打印当量 0.3/0.6/1.0mm 全<①线 1.2mm, 死代码, n_trim_sliver=0 不变); D7 体积腿改 post-inset 同源(`_postinset_world` 单一构造点, gap 计数不变仍 0); SPANDREL_BACK_VOL_CM3 注释更正(体素交集体积, 非 AABB 盒); SLICE_NOTES 披露环-墙切割缝打印当量 = GAP_W 0.20 + 2×clr ≈ **0.5-0.8mm**(试印宽缝属口径预期)。

### check 106 机制(复审实测事实; 假说不作结论)
106/106 全部带裁片, pre-inset 全过/post-inset 全坏; 失败与 FIT 余量单调(clr 0.1mm→0, 1mm→4, 3mm→8, 7.5/15/25mm→106/106); 与坐标系无关(修复帧重建仍 106/106)、与整体平移无关(y+5m 判定不变); 单轴假设不成立(只关 z-inset, 24 抽样仅 5 转好); legacy clip 对照组同等顶点带内密度(p50=4)却零新增失败(80 抽样 newly-broken=0)→ 触发因子为带裁片特有几何特征, **尚未定位**; 交叉三角集中于切割下缘近共线顶点(距 z-min 0~4.8mm; 每件 8-10 顶点落在距极值面一个 clr 带内); "薄片"措辞作废(bbox 最小维 0.328-0.709m 模型 = 打印 6.6-14mm); 机制假说(inset 的 bbox 极值顶点位移 × 非均匀顶点分布 → 局部锯齿 → 相邻侧面翻折)两次合成复现失败, 不作结论。

### 处方转达(T9/处方轮输入)
P0 = inset 改按面分类内偏置(只对装配面施力) —— 正当理由是**语义正确性**与修 inset 对非箱形件的翻错, 不是"修复 106"的承诺; 落地必须同时回答切割面装配余量来源(逐面偏置 或 GAP_W/2 单独余量; 直接排除=精确贴合=装配失败)。P1 = 回归钉必须用真实失败件 fixture(现红, 机制修复后转绿; 合成非凸件已证抓不到)。P2 = 抽稀阈 ≥2×clr 仅降触发概率, 非根治。禁止: 调 sliver/min_wall 阈截走 106、豁免 MULTI_SHELL、final_scope de-minimis 界清 85。

### 回归(真树实测)
e30 tests **229 passed**(226+新 3, 含真总体钉死与结构闸门负控)/bridge3d **312 passed**/qa_l2 **QA_L2_OK**+负控 **NEG_CAUGHT 10/10**/_check_abutment **ALL PASS**/freeze 三对象 sha_sorted+sha_order **逐位一致**(bridge_body/voussoir/coursing)/validate_g2_report(新报告)=**[]**/excluded_ids↔report 桶计数读回一致。中央孔试印包: manifest 已记 superseded(T8c)+SLICE_NOTES 重生成+作废横幅。
