# P4-T3 报告: 三方守恒双实现 validator(口径考古先行)

日期: 2026-10-08 · 执行: P4T3Conserve · 计划: docs/superpowers/plans/2026-10-08-p4-print-pack.md Task 3
状态: **完成**。commit: `feat(e30): P4-T3 三方守恒validator(口径考古+偷挪丢失负控)`(只含两个交付文件)

## 口径考古结论(给关账报告的关键输入: 1974 vs 2113 已解)

**疑点**: P1 关账行/计划接口写 "G2 全桥打印单元=1974"; T2 实测段 1123 单元(2747 石) + 留续 990 单元(3188 石) = 2113 ≠ 1974。

**裁决: 1974 是 T8 原始轮历史口径, 已被 T8b 更替; 2113 是现行口径。不是丢账, 是排除口径代际差。**

| 证据(g2_report.json 按 commit 逐版读回) | verdict | print_units | 排除桶(in_void/void_cut/ring_band/thin_merge) |
|---|---|---|---|
| 04f2e54 (P1-T8 原始轮, "1974" 出处) | PASS | **1974** | 2052/1520/**305**/**84** = 3961 |
| c74d54f (T8b 体量宇宙) | FAIL | **2113** | 2052/1520/**182**/**68** = 3822 |
| 10cb405 (T8c) | FAIL | 2113 | 同上 |
| 648ea30/258726f (T9/T9b, **P1 收官 2026-10-07 09:30**) | PASS | **2113** | 同上 |
| 35e37cd (P2-T6b 重跑, 盘上现行版) | PASS | 2113 | **2004**/**1568**/182/68 = 3822(桶内搬家 48 石, 单元数不变) |

- **差 139 精确归因**: T8b 对 ring_band_overlap 由"足印交占比>50% 一刀切"改为逐石 subsume/带裁仲裁 → 123 石回打印域(305→182); thin_merge 16 石回打印域(84→68)。1974+139=2113, 两代口径各自守恒(1974+3961 == 2113+3822 == 5935), 证明是**口径差不是丢账**。
- **三候选裁决**: (a) stone→unit 合并 —— **否**(1 单元=1 账面石, g2_report counts.print_stones==print_units==check_stone.n==2113, 无合并; T9 `#R<i>` run 升格分裂机制现行 475 带裁石全单 run 未触发); (b) deferred 990 是石级估算 —— **否**(deferred_holes.json `unit_ids` 是与 G2 同 print_scope 口径的逐 id 全表 990 条, 3188 是含排除的账面石数); (c) 排除项不同 —— **是, 但属代际差**(T8 原始轮 vs T8b 之后), 非 G2 判据内部不一致。
- **判据口径(pack_verify docstring 与测试双钉)**: 稳定不变量 = **石级三方恒等(逐 id 集合)**: section(1123) ⊎ deferred(990) ⊎ excluded(3822) == ledger(5935) 两两不交; 单元级同口径分段核对 1123+990=2113==重算 print_units。**1974 不作判据, 不硬凑** —— 只作历史口径记入 docstring/报告。

## 交付物

| 文件 | 说明 |
|---|---|
| `3d/pack_verify.py` | 新建: `recompute_view(ledger)` 独立重算(classify_full → print_scope → ring 处置, 与 G2 门 run_g2 前奏同序, blender-free 实测 93s) + `verify_pack(section_manifest, deferred_json, excluded_ids, ledger, recomputed=None)` 纯函数裁定 + CLI(`--section-manifest/--deferred/--excluded/--ledger/--json`, 退出码 0/1)。**不 import export_print/section_pack** —— 重算路径只经 p1a_slice(printcheck 排除口径唯一所有者); 8 组检查: 石级三方集合等式/双实现互证(scope+逐桶)/孔划分/分段成员(偷挪)/原料数(2747+3188=5935)/skipped 逐条同桶/单元 1:1 计数/curve_hash 代际防混 |
| `tests/test_p4_conservation.py` | 先红后绿 6 支: `test_stone_level_three_way_exact`(逐 id 集合等式+分段原料钉+与盘上三清单互证)、`test_unit_level_caliber_documented`(1:1 口径+g2_report 现行值+考古 token 钉进源码+两代口径各自守恒+差 139 归因等式)、`test_neg_steal`/`test_neg_drop`(篡改副本必红, 双探测码)、`test_import_isolation_probe`(AST import 面/subprocess sys.modules+命名空间持有/探针阴性对照三层)、`test_cli_json_ok_and_tampered`(注入重算, 退出码双相) |

## 验证证据(全前台实测)

- **红**: 模块未写时 `pytest tests/test_p4_conservation.py` → collection error(ImportError), 先红成立。
- **绿**: 6 passed in 91.28s(session fixture 一次重算 ~93s; Python 3.9.6)。
- **CLI 冒烟(真面真重算)**: `python3 3d/pack_verify.py --json` → exit 0, `{"ok":true,"三方":{"section":1123,"deferred":990,"excluded":3822},"total":5935,"units":{"sum":2113,"recomputed_print_units":2113}}`; 人读版 exit 0 `PACK_VERIFY OK 石级: …== ledger 5935`; 篡改 deferred → exit 1(test 钉)。
- **独立重算互证**: 从 ledger_full 重推 scope 2113/桶 3822 与盘上 excluded_ids.json **逐桶逐 id 相等**; section∪deferred == 重算 scope 且交空。
- 全量分母口径: 本任务新增 6 支; 未跑全量套件(P3 线并行编辑中, 按 Coop 纪律留给主控收尾一次跑)。

## 上报主控(关账输入)

1. **计划/spec 的 `total:1974` 接口数字已过时**(写计划时抄了 p1-progress Task8 原始行; P1 收官 T9 起实为 2113)。T6 关账请按 2113(段 1123+留续 990)引用, 1974 若出现须带"T8 原始轮历史口径"限定语; p1-progress.md 第 17 行(1974/3961)是历史行, 收官行在第 30 行。
2. P2-T6b 曾把 48 石在 in_void↔void_cut_fragment 间重分类(排除内部搬家)—— 若日后比对不同时期 excluded_ids.json 桶计数, 以 curve_hash 相同为前提, 本 validator 的 curve_hash 代际防混检查会拦混代输入。
3. 本报告按纪律未入 commit(只 add 两交付文件); 报告入库与否由主控定(先例: p4-task-2-report.md 已 tracked)。
