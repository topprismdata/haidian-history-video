# P4-T1 报告: scale_params 薄特征审计(打印当量口径, 不回写账)

日期: 2026-10-08 · 执行: P4T1Scale · 计划: docs/superpowers/plans/2026-10-08-p4-print-pack.md Task 1
状态: **完成**。commit: `feat(e30): P4-T1 薄特征审计(打印当量口径, 不回写账)`

## 交付物

| 文件 | 说明 |
|---|---|
| `3d/scale_params.py` | 新建。`thin_features(ledger, scale=1/50, floor_mm=1.2, zones, excluded_buckets)` + CLI |
| `tests/test_p4_scale.py` | 计划 Step1 三支测 + CLI 幂等/计数断言(3 个测试函数) |
| `3d/out/print/thin_features.json` | 真账产物(schema 1, 520KB, 两连跑逐字节同) |
| 本报告 | 供 T2-T6 消费 |

## 两口径区分(docstring 与本报告互引)

1. **本审计 = 块最小维打印可打印性粗筛**: 石块族网格 bbox 最小维 × scale(1/50) × 1000(打印当量毫米) < floor_mm(1.2, 严格小于)→ `bbox_min_dim` 条目; 块体放行但出墙面浮雕 proud 当量 sub-floor → `face_sliver` 条目(一石一条, bbox 优先)。
2. **printcheck.check_stone 的 THIN_WALL = 模型侧流形壁厚判据**(post-inset 网格逐轴 bbox + 面片对代理 W1)。两者互为粗筛/精检, 本模块不复算也不替代 printcheck。

dims 取法与 export_print 同一口径: 族网格顶点 bbox 轴向极差(`_extents_m`), 网格经 `families.family_mesh` 单源获取(与 `masonry2.materialize` 默认路径同源; 账内 5935 石 transform 旋转分量全零, 平移不改极差, 测试内对真账薄石实证局部=世界极差)。

## 实测结果(真账封 sha 80de7a45, 段=ARCH07-11, 扫描 2747 石)

**thin_total = 1202**(非空, 如实测如实报, 未调 floor):

| where | 数量 | 明细 |
|---|---|---|
| `bbox_min_dim`(结构薄件) | **8** | 段端剖面收窄块 ×8: `ARCH07.{EAST,WEST}.{SPANDREL,BACK}.C06.B08`、`ARCH11.{EAST,WEST}.{SPANDREL,BACK}.C06.B00`, 均为 w=0.058m → **1.16mm 打印当量**(差 0.04mm) |
| `face_sliver`(浮雕细部) | **1194** | SPANDREL wedge-std 1154 件(proud=0.006m→0.12mm) + IMPOST impost-step 40 件(proud≈0.0413m→0.8267mm) |

交叉验证: 8 件结构薄件**全部**已在 P1 `excluded_ids.json` 的 `ring_band_overlap` 桶(与券环带双重建模, 打印以 RING 为准, 不单独出件)——本审计独立复得同一集合, 与 P1 排除口径互证一致; CLI 侧逐条注记 `excluded_ids.ring_band_overlap`。(4 件薄 SPANDREL 兼有 sub-floor 浮雕, 按更严的 bbox 口径记, 不重复计条。)

## M3 处置建议(T2-T6 消费)

- **M3(雕刻件)本身**: 段内无狮/兽(在桥台与栏杆, 段外)→ v1 自然豁免、顺延续段(spec §0)。本清单所有条目均非雕刻件, 逐条 `m3_note` 已注明。
- **8 件结构薄件**: P1 已裁定不单独出件(ring_band_overlap, 真实裁石在墙里)。段包侧无需新动作; T2 出 section5 manifest 时它们本就不入打印单元; 段端剖面收边由 M5(a) 底座端槽承担。**禁**为凑 1.2mm 改几何(G1 封版)。
- **1194 件浮雕细部**: 0.12/0.83mm 出墙面浮雕在 1:50 打印当量下低于 floor, 打印后浮雕损失属**外观项**(P1A 实物反馈"打过, 整体可用"与之相容); 建议表面处理/分色补足, 不影响结构打印与装配。T2 的 manifest per-stone 参数无需为它们改 clearance。

## 验证证据(全部实跑)

- TDD: 先红(`ModuleNotFoundError: scale_params`)后绿。
- `pytest tests/test_p4_scale.py -q` → **3 passed**(合成薄石必列+厚石/恰在 floor/厚浮雕三重负控; 真账段清单 8+1194 逐 id 钉; 账 sha 逐位不变)。
- 验收 CLI 原样跑通并打印计数: `薄特征审计: 段=ARCH07,ARCH08,ARCH09,ARCH10,ARCH11 扫描 2747 石 -> thin_total=1202 (bbox_min_dim=8, face_sliver=1194) -> 3d/out/print/thin_features.json`。
- 幂等: 同命令两连跑, `cmp` 逐字节同。
- 账不回写: CLI 两连跑前后 `ledger_full.json` sha256 逐位不变(80de7a45ff32…e9ce)。
- 全量 `python3 -m pytest tests -q`: **零红, 481 passed / 0 failed / 0 error**。因本机 harness 对 >55s 命令强制转后台通道, 按文件/用例分片前台跑全 23 个测试文件(重测用无时限通道单跑, 全速实测 92s/71s/80s), 合计 481 passed; 其中含本任务新增 3 支(test_p4_scale)与 P3 并行线 test_p3_pace 3 支(当日实跑亦绿)。明细: chunk1 86(p4_scale/p1_printcheck/p1_families/p1_ledger/facts) + p1_slice 42/42(分片: A21+B1 11+fixture参数4+lift1+population_control1+units_split1+ring_trim重测3) + masonry2/no_literals/freeze_manifest/population_control 38 + p1_scene 23 + p1_export 28 + p2 单元 124(ledger_v2/geom_math/events/centering/register) + g3 51(dag/imbalance/thrust) + p2_sequencer 46 + p2_full 20 + p1_l1_body 20 + p3_pace 3。

## 并行纪律

未触碰 P3 线(3d/film/*)与任何封禁面(ledger/砖谱/G1 几何/FIT 分档值/装箱约定零修改); 暂存区仅含本任务四个路径。
