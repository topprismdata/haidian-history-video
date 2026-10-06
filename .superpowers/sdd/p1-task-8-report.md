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
