# 十七孔桥·中央五孔 1:50 段包报告 (section5)

段=ARCH07-11(spec#4 M1c 代表段); 其余 12 孔留续见 deferred_holes.json
(留续清单语义即段外清单, 不出包)。片名口径: 十七孔桥·中央五孔 1:50。

## 全段汇总(实测)

| 项 | 值 |
|---|---|
| 段账面石 | 2747 |
| 打印单元(exported) | 1123 |
| skipped(带 reason) | 1624 |
| 守恒 | 2747 = 1123 + 1624 |
| 批数(220x220 床) | 34 |
| 总体积(打印件) | 7416.3 cm3 |
| maoshi 体积/件数 | 3769.4 cm3 / 484 |
| qingshi 体积/件数 | 3646.9 cm3 / 639 |
| fit 档分布 | LOOSE 10, NORMAL 501, TIGHT 612 |
| fit_diagonal 斜置 | 2 件 |
| oversize 独占批 | 0 件 |

## 预估偏差(spec#4 M1 估 ~913)

| 口径 | 打印单元 | 段石率 |
|---|---|---|
| spec 估算(2747 x 0.332) | 913 | 0.332 |
| 实测(本包) | 1123 | 0.409 |
| 偏差 | +210 | +23.0% |

## 分孔

| zone | 账面石 | 打印单元 | 排除 |
|---|---|---|---|
| ARCH07 | 512 | 192 | 320 |
| ARCH08 | 575 | 247 | 328 |
| ARCH09 | 573 | 245 | 328 |
| ARCH10 | 575 | 247 | 328 |
| ARCH11 | 512 | 192 | 320 |

## skipped 原因分布

| reason | 件数 |
|---|---|
| g2_excluded:in_void | 900 |
| g2_excluded:ring_band_overlap | 100 |
| g2_excluded:void_cut_fragment | 624 |

## 口径

- 1:50(scale=0.02); 打印件毫米 = 模型米 x 20; 床 220x220。
- 装箱: 贪心货架 + 90° 归一 + 45° 对角斜置(P1A 约定, manifest.batches,
  fit_diagonal 非独占批); 真放不下才 oversize 独占。
- FIT 自动分档(块最小维): <0.3m TIGHT / <1.0m NORMAL / 否则 LOOSE;
  clearance 双值见 manifest.stones(打印/模型)。
- 体积=散度定理(耳切对角约定口径, 实心体上界); CORE 与面石有意重叠
  (牺牲芯建模语义), 各族体积不可加和成净打印料。
- 打印单元=G2 scope 口径(p1a_slice 纯逻辑重建, 与 G2 门时序同序;
  零漂移由 tests/test_p4_section.py 对 central manifest 45fed1e8
  manifest 语义/ledger_print 逐字节/STL 数值(1e-6mm, 负控在测)钉)。
- coupon 首件约定: 每批首件打印前以同档 coupon 成对试配(1:1 真尺寸,
  缝=2x fit_print_mm 可实测), 12 件见 coupon/。
- 幂等: created_utc 归空(出包时刻不落盘, 溯源归 git); 3MF 容器时间
  归一(内层 model 零改动) -> 两连跑全树逐字节同。

## 复现

```
python3 3d/section_pack.py
```
