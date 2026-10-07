# P1 Task 9 报告 — G2 转绿轮（W1/W2 收口 + 106 机制定位与修复 + 85 切割线收敛 + run 升格 + G2 重跑）

日期：2026-10-07（工作树 /tmp/e30_t9，分支 p1-t9，单 commit 落 main）
范围执行者：P1T9Green。改动面：`3d/export_print.py`（inset）、`3d/p1a_slice.py`（lift 覆盖/条带边界/抽稀豁免/打印单元/结构闸门）、`3d/dump_check_fixtures.py`（新）、`tests/test_p1_export.py`、`tests/test_p1_slice.py`、`tests/fixtures/check_106/*.json`（新 4 件）、`.gitignore`（fixture 白名单）、`out/print/*`（重生成）。本体路径零触碰。

## 0. 结论一句话

**G2 verdict FAIL → PASS**：check_stone 106→0、gap 0（保持）、final_scope 85→**0**（903 对全量复测）；全部闸门绿（e30 237 / bridge3d 312 / L2+NEG 10/10 / 33 断言 / freeze 三对象逐位）；判据/桶/阈值零放宽（1.2mm、10mm、抽样数、5mm/100cm³ 界全部未动）。

## 1. W1/W2 防篡改收口

- **W1**：`validate_g2_report` 的 subsume 材料闸由 OR（`subsumed>0 or subsumed_by_area_bucket>0`）改**严格 AND**（`n_subsumed>0 ⟹ removed_model_cm3.subsumed>0`），镜像 trim 侧。负控：r10 变体（n_subsumed=2、subsumed=0、面积桶账 5.8e7 在）必须红、材料账到手即绿（test_validate_g2_report_negative_controls）。现网真账 n_subsumed=0，闸门对真账 vacuous、对篡改有声。
- **W2**：真总体钉（③④⑤+材料恒等）在 `out/ledger_full.json` 缺失时由静默 `pytest.skip` 改 **fail-on-skip**（`_load_real_ledger_or_fail` raise，fail 信息含再产指令与显式 --deselect 逃生口）。负控：monkeypatch 假路径必须 raise（test_real_population_ledger_gate_fails_loud_when_missing）。理由：ledger 构建需 blender（build_ring_entries/_impost 硬依赖 bmesh），纯 pytest 环境无法自建，故"干净克隆自建"不可行，fail-on-skip 是唯一不假绿的诚实选项。

## 2. 106（带裁片 post-inset 自交）：机制定位 → 修复

### fixture（先钉后修，P1 处方）
`3d/dump_check_fixtures.py`（入库）：从真账重放 G2 前半程，dump 真失败件 pre-inset verts/faces+clr 到 `tests/fixtures/check_106/`（git 跟踪，干净克隆可跑）：同带全绿负控 1 件（ARCH03.EAST.SPANDREL.C07.B01；注：历史 anchor ARCH03.EAST.SPANDREL.C07.B00 经 T8c partner 足印守卫后已不是带裁石（status=out），按同孔同课程同带原则改取 B01）+ 真失败件 3 件（CORE/BACK/SPANDREL 各一，含最大极值带顶点件 ARCH01.EAST.CORE.C07.B00 band=16/16）。

### 机制（fixture 上逐轴二分实证，非假说）
EP.inset 旧实现只位移 bbox 极值顶点（域内顶点不动）。该**分段映射不单射**：极值面以整步 c 内移时，扫过所有距极值面 <c 的近极值内部顶点——带裁片切割折线密采样保证每个极值带内有 8~16 个这种顶点。实测解剖（ARCH05.EAST.BACK.C07.B00，x 轴单轴即可复现）：x-min 端帽面（-42.1960）内移 15mm 到 -42.1810，越过未动的侧壁近边（-42.1812）→ 端帽面穿过侧壁四边形（A 端帽×侧壁，不共享顶点）。与 T8c 全部实测事实吻合：pre-inset 全过/post-inset 全坏、随 clr 单调（c 越大越深越入）、与坐标系/平移无关、单轴假设不成立（不同件不同轴：CORE 件 z 单轴红、BACK/SPANDREL 件 x 单轴红）、legacy clip 对照组"零新增"（它们 pre-inset 就带病，不入 verdict）。

### 修复：逐轴仿射内缩（定理级，非 Plug&Pray）
`EP.inset` 改为关于 bbox 中心每轴把 [lo,hi] 线性映射到 [lo+c,hi−c]（ext≤2c 的扁/薄轴不动）。**单射仿射映射下内嵌网格不可能自交（定理）**；极值面（装配贴合面）精确退让 c；平面性/绕向/多壳拓扑逐项保持；post-inset 包围盒逐轴恰好缩 2c ⇒ thin_merge/fit 分档/桶归属逐件不变（475 裁片与全 2113 打印单元总体不变）。
**P0 问题回答（切割面装配余量来源）**：配合公差吃在 bbox 配合面（精确 c）；切割缝面（非轴对齐装饰面）退让 ≤c 且沿轴单调，缝配合由名义 GAP_W 承担（1:50 历史缝 0.2mm 本打不出，环-墙切割界面是表征缝非精密配合）。已写进 SLICE_NOTES「T9 口径」节。
**clr 单调断言反转**：4 件 fixture 在入库 clr 与 7.5/15/25mm 四档全部 0 自交（T8c 实测 15mm→106/106 全红，现 15mm→0）。
**体积口径更新**：仿射内缩体积恰乘三轴缩放系数 V1=|V0|·∏(ext−2c)/ext（对任意形状成立）；test_p1_export 两处楔形 (d−c) 闭式 pin 随旧分段映射一并作废，改钉仿射定律（slab 件 (w−2c)(h−2c)(d−2c) 闭式不变仍过）。

## 3. 85（ring↔链残留互穿）：几何解剖 → 三层根因全修

逐对解剖 ARCH06.EAST.CORE.C13.B01 vs RING.C00.B07（60.012mm/86456cm³）与 ARCH07.EAST.CORE.C14.B01 vs B07（36400cm³，depth=0；T8c 明细同族对 ARCH11.EAST.CORE.C14.B01=36424cm³ —— 初稿两块串行，T9b 订正），定位三个独立根因，全部修在 `_band_trim_polys` 折线带构造内（单一真相仍是环 params `_ring_lift_coverage`，零栅格反推）：

1. **lift 覆盖未含外弧角点越出段（24 条 depth>0 的根因）**：`_voussoir` 的 lift 是沿法向外弧外推（外弧=拱曲线法向偏移 ring_t+lift），端站 x0/x1 是【内弧】放射缝站；外弧角点 x = 端站 + sin(angle)·(ring_t+lift)，在拱顶两侧各越出 stations 约 50mm（ARCH06 实测 53/46mm）。旧覆盖只用 [x0,x1]：角点外条带 bound 缺 lift，环真剪影高出切割线 ~60mm（=lift−GAP），恰为 60.012mm 主碰对。修：`_ring_lift_coverage` 按 stations/angles/ring_t/lift 计算真实覆盖（pad 与 JOINT_GAP_BACK 取代数和、钳回 [x0,x1]；角度缺失退化=旧 [x0,x1] 逐位）。
2. **覆盖台阶落在条带内部被抹成斜坡（59 条 depth=0 的根因）**：bound 的 lift 台阶若不落在条带边界，单段线性插值把台阶抹平，覆盖边界邻域欠割至多一整个 lift（ARCH07 实测 hit z[6.29,6.33] vs 真界 6.336）。修：lift 覆盖边界强制加入 strip 端点集 xs。
3. **抽稀吃掉台阶点（最后 2 条 v_hit=0 掠穿的根因）**：台阶点恰落在来向平滑曲线上，1.5mm 共线判据把它当曲线中间点丢弃 → 右缘弦下切 13mm，环端面外缘高出弦 2mm 掠穿（A#27×B#4）。修：lift 覆盖台阶点永不抽稀（显式白名单）。

修后重放：final_scope n_pairs=903 **n_colliding=0**；裁片总体 475 不变、sliver 0、subsumed 0、y_violations 0；trim 材料账恒等不变（7.732e7 cm³）。钉死测试：`test_lift_coverage_pads_and_edge_is_strip_boundary`（pad 口径 + 无角度退化 + 台阶点必须在 poly 顶点上，用真 keystone 浅角 ±6.65° 复现抽稀丢点类）。

## 4. MULTI_SHELL run 升格 + 谱系 + 存量追偿

- `_print_units`：带裁多 run 石升格为独立打印单元（`<石id>#R<i>`，谱系 `parent_ids=[石id]`），run_g2 check 逐单元跑——多壳体不再以单件出现（审查裁决"MULTI_SHELL 不豁免"=真拆分不是豁免）。负控钉：同石两 run 不拆必红 MULTI_SHELL、拆后各自单壳干净（test_run_units_split_lineage_and_each_shell_clean）。现行真总体 475 石全单 run（run_units=0），机制为断料场景的结构保证。
- 报告/闸门：meta.counts 增 print_stones/run_units；守恒改双轨（print_stones+excluded==stones；print_units==print_stones+len(run_units)）；validate 负控（谱系被抹/差值破坏必红）。打包边界：export_slice 遇多 run 石响亮拒绝（逐 run STL 归 T5/T7 打包轮），不静默打 MULTI_SHELL 单件。
- 存量 870/1520 归口：legacy_clip_survey 增 `disposition`/`debt_ticket:"T5/T7"` 字段（本轮普查 842/1520 fail——数量与 T8c 870 的差异来自仿射 inset 与 lift 收敛对存量碎片的连带影响，债务口径不变）；覆盖率审计的 void_cut_fragment 洞面积是该桶第二笔待追偿账。存量几何质量零修改。

## 5. G2 重跑（blender 实测）

```
LEDGER_FULL stones=5935 (chain=5250 ring=193 impost=492) —— 数量/顶点双重互证 OK
G2_REPORT verdict=PASS check_fails=0 gap_fails=0 ring_colliding=0
validate_g2_report(新报告) = []
excluded_ids ↔ report 桶计数读回一致（run_gate 内建互证）
fit_tiers: TIGHT 1152 / NORMAL 947 / LOOSE 14（与 T8c 一致）
```
中央孔试印包按 PASS 重生成：manifest（无 superseded 标）、SLICE_NOTES（重生成正文+T9 口径节：装配余量来源/run 升格/存量追偿）、assembly_ortho.png、STL/3MF。

## 6. 全门回归（真树/工作树实测）

| 门 | 结果 |
|---|---|
| e30 tests | **237 passed**（基线 229 + 新 8：fixture×4+总体自证、W2 fail-loud 负控、lift 覆盖钉、run 升格钉、validate run_units 负控并入既有负控测试） |
| bridge3d | **312 passed** |
| qa_l2 | **QA_L2_OK**（0 fail / 0 skip / sampled 604）+ 负控 **NEG_CAUGHT 10/10** |
| _check_abutment | **ABUTMENT_CHECK ALL PASS**（33 断言） |
| freeze | 三对象 sha_sorted+sha_order 与 freeze_manifest §2（2026-10-06 重采）**逐位一致**（bridge_body cdba9709…/64428393…、voussoir ba2e0951…/bb2defc9…、coursing f2968f4c…）——本体路径零触碰实证 |
| 结构闸门 | validate_g2_report(新报告)=[]；excluded_ids↔report 读回互证过 |

## 7. 边界与移交

- 试印包打包层逐 run STL 未实现（现总体无多 run 石，遇多 run 石响亮拒绝）——归 T5/T7 打包轮。
- legacy clip 存量 842/1520 fail 与 void_cut_fragment 覆盖洞面积（coverage_audit）＝T5/T7 追偿范围输入，本轮未修。
- **覆盖率回潮披露（T9b 补记，审查 M4）**：ring_band_overlap 桶未覆盖 cells 6776（T8c, 27104cm²）→ 7007（本轮, 28028cm²），**+231 cells = +924cm²** —— 带裁割得更深（lift 包络收敛的副产）使该桶被剔材料足印变大；无阈值判据、不入 verdict，同批记 **T5/T7 债务输入**（与 legacy clip/void_cut_fragment 同单追偿）。
- `out/ledger_full.json` 含 uuid4/时间戳，字节级不可复现（既有行为）；结构级重建确定性由真总体钉（475/y 氏 0/材料恒等）钉住。
- 工作树：/tmp/e30_t9（分支 p1-t9）；out/_t9_replay_cache.json、e30_bridge.blend 为未跟踪工作副本，不入库。

## T9b 护栏收口轮（2026-10-07，出口审查 B1/B2/M1-M4 全项落地；本体零触碰）

执行者：P1T9bFix（隔离树 /tmp/e30_t9b，git archive d5fcbd2 前驱 237d470 + 盘上 ledger_full.json）。改动面：`3d/p1a_slice.py`（validate 三闸 + scope.print_stones + fit_tiers 口径注记 + lift 台阶点 0.1mm 去重 + 打印单元单次遍历）、`3d/dump_check_fixtures.py`（防自毁 + band_verts 入册）、`tests/test_p1_slice.py`（真总体/入库工件双钉 + 四组负控 + 薄轴×FIT 耦合钉）、`tests/fixtures/check_106/*.json`（+band_verts 元数据）、`out/print/*`（重导出）、本报告（§3/§7 订正）。判据/桶/阈值/抽样数零放宽。

### B1 中央孔试印包重导（审查放行前置）

`blender -b --python 3d/p1a_slice.py -- --g2` 全链重跑 2m1s：`G2_VERDICT PASS stones=5935 ring=193 impost=492 gap_pairs=340`。盘上 245 STL + 245 3MF 与 manifest 声明集**完全相等（490=490，孤儿 0、缺失 0）**；逐件体积复算（散度定理，STL float32 / 3MF 网格文本解析）：STL 最大相对差 9.441e-08、3MF 最大相对差 3.391e-07（均 ≤ 各自格式精度上限，无超差件），总体积 1814.2420 cm³ 与 manifest 族账一致。`ledger_print.json`、`assembly_ortho.png`（3200x1709）同批新写；入库 manifest/g2_report/excluded_ids diff 仅 created_utc + ledger uuid（既有字节级不可复现行为）+ 本轮新增键。报告 §5「按 PASS 重生成」自本轮起为事实陈述。

### B2 静默绿转可判（lift_at→0 恒零消融自证，前后实测原文）

消融方法：`_band_trim_polys.lift_at` 改恒 `return 0.0`（唯一改动），纯 python 重放 run_g2 重写 `out/print/g2_report.json`（与 run_gate 同函数同序列化），随后跑钉子测试：

```
消融侧重放:  ABLATED REPORT verdict=FAIL fsc n_pairs=903 n_colliding=107
（与审查方独立重放 107 一致；头号对 ARCH09.EAST.CORE.C14.B01×RING.C00.B09
  depth 173.298mm / collide_vol 405560cm3）

消融后 pytest（真账 fixture 一起跑，144.94s）:
FAILED tests/test_p1_slice.py::test_g2_report_shipped_artifact_pins - AssertionError: assert 'FAIL' == 'PASS'
ERROR tests/test_p1_slice.py::test_ring_trim_world_y_within_family_band_real_population
      - AssertionError: 真总体 ring↔链复测回潮: 107 条 (前3: [{'chain': 'ARCH09.EAST.CORE.C14.B01', ...}])
      assert 107 == 0
ERROR tests/test_p1_slice.py::test_ring_trim_east_west_centroid_y_sign_real_population - (同上 107 == 0)
1 failed, 2 passed, 37 deselected, 2 errors
```

恢复实现与报告后复验：`restored report verdict PASS fsc 0`，钉子组 `5 passed`。即审查方 SILENT(决定性) 项（lift_at 恒零 → 全套件 40 passed 一声不响）**转响亮红**：B2(a) 真总体 fixture 断言红、B2(b) 入库工件钉红。

结构闸门负控实测（validate 层，原报告对照 GREEN，四类篡改全红）：

```
原报告(对照)            -> GREEN(静默)
fsc.n_pairs=0           -> ['final_scope_check.n_pairs=0 < 复测地板 ring_total=193 (独立复测对数被抽走)']
fsc.n_pairs=1           -> ['final_scope_check.n_pairs=1 < 复测地板 ring_total=193 (独立复测对数被抽走)']
面积桶账抹零             -> ['n_area_bucket_measured=182>0 但 removed_model_cm3.subsumed_by_area_bucket==0 (面积桶材料账被静默抹; ...)']
legacy 追偿单删除        -> ['legacy_clip_survey.n=1520>0 但缺 disposition/debt_ticket (T5/T7 追偿单被静默蒸发)']
```

### M1 producer/gate 形状对齐（含一处审查未列的必然连锁修复）

- `run_g2` meta.scope 补 `"print_stones": len(scope)`（生产者键，validate 不再回退 print_units）。
- **run_units 守恒恒等式订正**：生产者对多 run 石记其【全部】run 单元（含 R0），旧闸 `print_units == print_stones + len(run_units)` 只对手写的"仅记增量"形状成立——第一份真实多 run 报告端到端必假红（正是审查 M1 指认的"机制从未端到端走通"的深层形状）。订正为 `print_units == print_stones − 多run石数 + len(run_units)`（多run石数 = run_units.parent_ids 去重数），identities 字符串同步。
- r11 负控升格 `test_run_g2_multirun_real_shape_scope_key_and_lineage_gate`：合成账 + 注入双 run 带裁 status 走**完整 run_g2 路径**，生产形状直接过 validate（端到端首次走通），篡改谱系/差值互证必红。

### M3 fixture 防自毁 + 元数据

- `dump_check_fixtures.py` main() 在清目录前加 `if not fails: raise`。实测（现实现重放 fails=0）：`RuntimeError: 当前实现重放无失败件(fails=0): 现行 fixtures 是 T8c/T9 历史失败证据...`，4 件 fixture 完好。
- fixture 元数据补 `band_verts`（生成器入册 + 存量 4 件按同公式补齐：16/10/11/11），几何漂移重生成时可见；测试补 post_ok↔post_fail_codes 互斥一致性断言（原注释声称钉 post_ok 一致性实际无断言，已修）。

### M4 nits

- §3 数字串位订正：ARCH07.EAST.CORE.C14.B01=**36400**cm³（36424 属 ARCH11.EAST.CORE.C14.B01，T8c 明细对账）。
- 覆盖率回潮披露记 §7：ring_band_overlap 未覆盖 6776→7007 cells（**+924cm²**，割得更深的副产），记 T5/T7 债务输入。
- 薄轴×FIT 耦合显式钉：`test_g2_gate_constants` 增 `2*max(FIT_PRINT_MM) < G2_MIN_WALL_PRINT_MM`（0.5*2=1.0 < 1.2；将来加宽 FIT 档破坏此前提必响亮）。
- lift 台阶点入 xs 前 0.1mm 去重（近重合丢重复端点不丢覆盖语义；现网真总体 0 例，纯防御，fsc/材料账钉未动即证）。
- `n_print_units` 单次遍历（主循环顺手计数，删二次 `_print_units` 求和）；`fit_tiers_caliber` 注记入 check_stone（按打印单元计数，多 run 石语义变化显式）；`_load_real_ledger_or_fail` type 注释 `-> dict` → `-> None`。

### 全门回归（本轮实测）

| 门 | 结果 |
|---|---|
| e30 tests | **239 passed**（237 基线 + 新 2：入库工件钉、多 run 端到端钉；消融往返后复跑同值） |
| bridge3d | **312 passed** |
| qa_l2 正检 | **QA_L2 ok=True / 0 fail / 0 warn / 0 skip / sampled=604** |
| qa_l2 负控 | **NEG_CAUGHT 10/10** |
| _check_abutment | **ABUTMENT_CHECK ALL PASS**（33 断言） |
| freeze | 三对象 sha 与 freeze_manifest §2（2026-10-06 重采）**逐位一致**：bridge_body cdba9709…/64428393…、voussoir ba2e0951…/bb2defc9…、coursing f2968f4c…；bridge_body 2648/1520、bbox z7.3 同表。本体路径零触碰（diff 文件清单不含 masonry*/bridge_geom*/build_scene2/facts/freeze） |
| 结构闸门 | validate_g2_report(新报告)=[]；excluded_ids↔report 桶计数互证过（run_gate 内建） |

### 备注（诚实边界）

- freeze_manifest §2 的 coursing 顶点/面数行（59716/34878）与 freeze_hash 现输出（66964/39466）不同，但 sha_sorted f2968f4c… 逐位一致——计数字面系信息项且口径先于现版工具，sha 为判据，本轮不改 §2（非本轮范围，留主控裁决）。
- 试印包 STL/3MF 为 gitignore 工作树产物（不入库），"与 manifest 逐位等"指盘上包与 manifest 声明集逐件一致；入库事实 = g2_report/manifest/excluded_ids/SLICE_NOTES。
- 消融与恢复往返仅动 `p1a_slice.py` 与 `out/print/g2_report.json` 两个文件，恢复以字节拷贝回滚（sha256 复核 CLEAN）。
