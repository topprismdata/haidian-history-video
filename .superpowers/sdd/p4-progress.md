# P4 关账报告: 中央五孔段打印制造包交付(p4-progress)

日期: 2026-10-08 · 计划: `docs/superpowers/plans/2026-10-08-p4-print-pack.md` · 状态: **P4 六任务关账(445fd90 拱线返工后基线重锚完成)**
一句话: **段包(1047 单元)可执行、三方守恒可机验、进度账就位; 打印执行归用户台架 —— P4 交付=制造包, 不是打印件。**

> **基线注记**: 本关账横跨 445fd90 拱线族返工(ogee→单心圆弧 17 孔, 用户实锤几何缺陷)。
> 返工前产出(1123 单元版)全部作废重出; 本报告数字以返工后重锚链(命令链 1→5+sequencer+g3+narration
> 本机重跑, 6 件与 merge 记录**逐字节复现**)为准。

## 一、拿到什么(制造包内容, 全部在 `3d/out/print/`)

| 工件 | 内容 | 守恒账 |
|---|---|---|
| `section5/` | ARCH07-11 段包: **manifest.json**(**31 批/1047 单元**/coupon 首件约定/分档 TIGHT 580·NORMAL 463·LOOSE 4) + STL+3MF×1047(maoshi 446/qingshi 601 分目录, 总体积 **7104.9 cm³**) + `coupon/` 配合试片 | 段 2747 石 = 出件 1047 + skipped 1700(逐 id 同排除桶) |
| `deferred_holes.json` | 留续清单: **12 孔**(ARCH01-06, 12-17) / 3188 石 / **990 单元**(unit_ids 全表; 返工前后逐字节不变) | 12∪5 孔 = 17 孔全集不交 |
| `thin_features.json` | 薄特征审计(1:50 打印当量 <1.2mm): **1202 条** = 结构薄件 8 + 浮雕细部 1194; **返工前后逐字节不变**(薄件=端剖面块宽/浮雕=proud 参数, 与拱线族无关) | 不回写账 |
| `section5/construction_cards.md` | 施工卡: 31 床批次总表(今日打印) + 装配次序 71 stage/1047 行(今日粘接, 逐行 [工程推断·非史料]) | 序 = sequence 原序过滤, 独立重算对账 |
| `section5/assembly/` | 每孔装配图 PNG×5 + 分号位表 CSV×5(床位权威, 行数==192/223/**217**/223/192) + 段总图 | CSV 行数==分孔单元数 |
| `section5/BASE_SPEC.md` | M5(a) 底座规格(**不打印**, 供台架/木工): **1105.72 × 308.80 × 13.0 mm**, 五孔孔心 x 表, 端槽 18.0×5.0 mm×2, 承重上界 **≈8.9 kg** [估算] | 全部数字盘上重算(测试钉, 已随新几何重推) |
| `print_status.json` | 进度账 init 模板: **1047 单元全 pending**(sidecar 登记) | 状态机 pending→printed→checked→glued / printed→redo→pending(可改派批) |

**三方守恒(pack_verify 独立重算, 关账实测 GREEN)**: 石级 `section 1047 ⊎ deferred 990 单元 ⊎ excluded 3898 石 == ledger 5935`(两两不交); 单元级 `1047+990 = 2037 == 重算 print_units == g2_report`。偷挪/丢失负控在测。

## 二、怎么用(用户台架开工流程)

1. **首件**: 打印 `section5/coupon/` 配合试片, 验 TIGHT/NORMAL/LOOSE 三档配合;
2. **打印**: 按 `construction_cards.md` 批次总表逐床打印(31 床); 估时参考 7104.9 cm³ ÷ 12 cm³/h ≈ **592h 实心体上界**(未扣 infill/支撑/重打; 权威=切片器);
3. **记账**: 每件打印完 `python3 3d/print_status.py advance --status 3d/out/print/print_status.json --unit <id> --to printed`(→checked→glued; 打坏 `--to redo` 后 `--to pending --batch <新批>` 改派), `query` 看进度 —— 断点续跑、非法迁移 raise、幂等落盘;
4. **装配**: 按装配次序节(71 stage)粘接, 床位以 CSV 为权威; 底座按 BASE_SPEC 制作(不打印)。

## 三、实测 vs 估算(两代实测的演进, 如实记录)

| 项 | spec §4 估算 | 返工前实测(T2, ogee) | **返工后实测(关账, 圆弧)** |
|---|---|---|---|
| 段打印单元 | ~913(2747×0.332) | 1123(+210, +23.0%) | **1047(+134, +14.7%)**, 实测率 0.381 |
| 全桥打印单元 | — | 2113 | **2037**(排除 3822→3898) |

**口径三代考古(全部各自守恒, 证明是口径代际差不是丢账)**:
`1974+3961`(P1-T8 原始轮) == `2113+3822`(T8b 逐石仲裁, 差 139=ring_band 123+thin 16) == `2037+3898`(445fd90 拱线返工, 差 −76=ring_band +40/in_void +24/void_cut +12) == `5935`。
**判据钉稳定不变量 = 石级三方逐 id 集合恒等**; 1974/2113 均为历史口径, 引用须带限定语(归因链: pack_verify docstring + test_p4_conservation 三代归因断言)。

## 四、commit 链(6 task + 返工重锚)

`5bf181b` T1 薄特征审计 → `284ee10` T2 段包出图(zones 参数默认零漂移) → `887afd4` T3 三方守恒 validator(+`0c26f8e` 口径考古落地) → `eed0a35` T4 装配图五张+施工卡 → `5bebfbb` T5 进度账状态机+底座规格 → **T6 本 commit**(sidecar 5 件 BLK-1 钉扩+关账报告)。中途并入 `445fd90` 拱线返工(RoundArchFix), P4 全链随新账重出。封禁面零触碰: 砖谱/G1 几何/FIT 分档/装箱约定/P1 语义; ledger/序列/三件套哈希经命令链复现互证。

## 五、本关账暴露的锚选型缺陷(给后续轮的债票)

- **发现**: 重锚链把 **uuid4 噪声件**(ledger_full/ledger_sequenced 石条目带逐次生成随机 uuid)与 **created_utc 时间戳件**(g2_report/excluded_ids/central manifest)当**字节锚**登记 —— 任何后 generation 都不可能逐字节复现, 即 merge 重锚块的两行在本机永远 red。
- **双盲互证**: 派生 g2_report/excluded_ids 逐字段恒等(仅时间戳异); sequencer 派生 sequence `77d2532b`/event_ledger `f370972f`/narration `cb000af1`/core_hash `b74ce261`(落回 v2 blend)全部**逐字节复现** merge 记录 —— 链无实质非确定性, 纯锚选型问题。
- **处置**: (A) 已执行 —— 两行换登本机 generation sha+证据注记, tracked 三件套回滚 merge 原字节(零 churn); **(B) 已于 2026-10-09(RoundArchFix 清债收官后)落地**: 5 噪声件(ledger_full/ledger_sequenced/excluded_ids/central manifest/section5 manifest)改登记 **content_sha256_excl_timing**(json 载入→剥 created_utc+stones[].uuid→sort_keys 紧凑 dumps→sha256, g3_report 先例推广), 判据集 `_CONTENT_HASHED`+归一化函数钉在 test_p2_g3_thrust; test_p4_section 的 CENTRAL_SHA 同步转 content 口径 —— 此后账代换(uuid/时间戳 reshuffle)不再假红, 内容变化(几何/计数)仍必红。core_hash 保持字节锚(确定性取决于 blend); 布尔修复最终 blend 落地后随冻结轮换值。

## 六、遗留与下一步

| 项 | 处置 | 归属 |
|---|---|---|
| 12 孔留续(990 单元/3188 石) | 清单在盘; 后续段包沿 zones 参数化出 | 后续 phase(用户排程) |
| M5 底座制作 | 规格=BASE_SPEC.md(1105.72×308.80×13.0); 打印底座=越界 | 用户台架 |
| M3 雕刻件(狮/兽) | 段内自然豁免(桥台/栏杆段外), 顺延续段 | 后续段包 |
| 打印执行 | P4 交付=制造包+工具链; 592h 量级长跑 | **用户台架** |
| assembly/ PNG 五张+段总图 | 返工前渲染(几何旧), CSV/卡已随新账重出; 重渲走装配门 | 后续重渲轮 |
| core_hash 换值 | **已办**: 布尔修复最终 blend adc59a5a 重冻结 = 28585991(2026-10-09; 过渡锚 84085824=3ac909d2 已更替) | 完成 |
| P2/P3 计数钉+film 链清债 | RoundArchFix 572b418/c1d653b/924c1da 已办大头; 残余见全量尾注 | RoundArchFix / P3 线 |

全量测试终数(主控前台 bg_8, 满速 578s, 含 (B) WIP): 分母 **539**(538+P3 新测 1), **528 passed / 11 failed**。红面全部为返工/清债在办债务, **与 (B) 改动零因果(spot-check 实证: stash (B) WIP 后 11 红照旧)**, P4 变更面零红: p2 推力实总体 1(r5a=1382/infeasible 钉, RoundArchFix 重钉复核在办)+P3 film 链 10(pace 2/layout 1/render_smoke 3/state 2/verify 3——stage 账本与事件钉跨相位脱钩, film 链重锚在办)。(B) 落地后账代换不再假红: 5 噪声件 content 锚判据即测即绿。sidecar 注记: `print_status.json` 钉 init 模板位, 台架推进后须随重锚轮更新该行。
