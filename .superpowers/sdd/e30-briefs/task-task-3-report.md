# Task 3 报告：L1 本体比例判据 + 负控制

- **状态**: DONE_WITH_CONCERNS
- **Commit**: `f250cad`（分支 `e30-bridge-body`，仅 2 文件 +288 行）
- **文件**: `e30_shikongqiao_video/3d/qa_bridge.py`（新建）、`e30_shikongqiao_video/tests/test_l1_body.py`（新建）
- **测试**: `python3 -m pytest e30_shikongqiao_video/tests/ -v` → **33 passed, 1 xfailed**（test_facts 15 条一条不少；test_l1_body 18 passed + 1 strict xfail）
- **每个新补测试均先单独运行验证**（11/11 逐条 `-k` 单跑通过，破坏→被抓先经独立脚本实测）

## MET_CLOSURE 当前状态

**已闭环（绿）**。初版（派发口径 15 内墩）基线 fail（147.50 vs 150.00，差 -2.50m），经 `xfail(strict=True)`
呈现 XFAIL，真负控证明非恒真。**T2b 终审裁决：内墩数 = N_SPAN−1（17 孔 16 墩，n−1 拓扑 + 卢沟桥
10墩11孔/宝带桥53孔52墩文献佐证 + bridge_geom2.py:180 断言同口径）**——-2.50m 系初版 15 墩误口径的
算术产物，非桥台真偏小；`BRIDGE_ABUT=1.35` 定稿维持（"2.60"凑数解作废）。口径归一后基线
`107.3+16×2.5+2×1.35 = 150.000` 精确闭合、零 fail；strict xfail 按设计 XPASS 报错后显式摘除，
`test_baseline_green` 现直接断言全绿。裁决详见 task-task-2b-report.md §4/§5；文末追记有完整时间线。

## 判据 × 故意破坏矩阵（全部实测）

| 判据 | 破坏用例 | 实测结果 | 抓获判据 | 测试 |
|---|---|---|---|---|
| INV_N_SPAN | `N_SPAN=15` | ✅ 被抓 | INV_N_SPAN(+MET_CLOSURE) | test_inv_n_span_break |
| INV_SPANS_LEN | `SPAN_DISTINCT` 10 个（变长） | ✅ 被抓 | INV_SPANS_LEN(+CLOSURE+RING_FIT) | test_inv_spans_len_break |
| INV_SPANS_SYM | `sd[3]+0.4`（单孔变异） | ⚠️ **L1 不可达**：展开恒回文，仅 MET_CLOSURE 抓 | —（见下行） | test_single_arch_break(修订) |
| INV_SPANS_SYM（检测器级） | monkeypatch derive → 非对称 SPANS | ✅ 被抓 | INV_SPANS_SYM | test_inv_spans_sym_detector |
| INV_SPANS_MONO 左半 | `[..., 5.95, 5.9, ...]` 回升 | ✅ 被抓 | INV_SPANS_MONO | test_boundary_mono |
| INV_SPANS_MONO 右半 | `sd[6]=8.0 > sd[7]=7.4` | ✅ 被抓 | INV_SPANS_MONO | test_inv_spans_mono_right_break |
| INV_SPANS_MONO 边界 | 相邻等跨 `7.4,7.4` | ✅ 正确放行（非严格单调） | — | test_boundary_mono |
| MET_CLOSURE | 跨序 ×1.05（对称但尺度错） | ✅ 被抓 | MET_CLOSURE | test_symmetric_scale_break |
| MET_CLOSURE **真负控** | `BRIDGE_ABUT=2.60` | ✅ **变绿（零 fail）**——非恒真 | — | test_met_closure_true_negative |
| MET_ARCH_FAMILY | 判据本体不可达（L1 券弧为构造采样，恒真圆） | 检测器级：真圆 0.000000 / 三心拱 **0.0626>0.05 被抓** / 椭圆 0.0025 放行 | 检测器级 | test_circle_fit_synthetic |
| MET_ARCH_RATIO | `ARCH_RATIO=0.65` | ✅ 被抓 | MET_ARCH_RATIO | test_met_arch_ratio_break |
| MET_RING_FIT | 桥面整体 -1.0m | ✅ 被抓（基线最小余量 +0.173m @ 孔1/17） | MET_RING_FIT | test_global_z_shift_break |
| MET_RING_FIT 边界 | -0.1m（< 0.173m 余量） | ✅ 正确放行 | — | test_global_z_shift_within_tolerance_passes |
| MET_SPRINGER | `SPRINGER=8.0`（> 中央桥面 7.75） | ✅ 被抓 | MET_SPRINGER | test_met_springer_break |
| MET_TAPER | `DECK_UP_W=16.0`（>14.6 收分反转）/ `=0`（退化） | ✅ 均被抓 | MET_TAPER | test_met_taper_break |
| MET_DECK_DIR | `DECK_Z_TOP=4.0 < DECK_Z_END=6.0` | ✅ 被抓 | MET_DECK_DIR | test_met_deck_dir_break |
| IMP_DIM | `PIER_W=0.1` / `BRIDGE_ABUT=0` | ✅ 均被抓 | IMP_DIM | test_imp_dim_break |
| 特异性（J类） | `PIER_MAIN_W=3.3`（无关字段） | ✅ 除已知基线 MET_CLOSURE 外全静默 | — | test_specificity(适配) |

## 与简报的差异（全部为必要最小修正，已在代码注释+此处双记录）

1. **`derive` docstring**：`BRIDGE_ABUT_TARGET` → `f.BRIDGE_ABUT`（派发预告的陈旧点①，代码本就取 `f.BRIDGE_ABUT`）。
2. **MET_CLOSURE 文案**：简报代码已是 -2.50m 口径（陈旧点②"1.2m"仅存于 Step 2 注释，未照抄）；另补中性注释标记"15 内墩计数 vs derive 16 内墩布局"口径问题归 T2b。
3. **check_body 券循环上加防御上界** `n_arch = min(len(SPANS), len(PIER_X)-1)`：否则 `N_SPAN=15`/短 `SPAN_DISTINCT` 的破坏用例会让 check_body **IndexError 崩溃而非报告 fail**（判据必须"报告"不能"崩溃"）。`N_SPAN=17` 全一致时与逐字版完全等价（min=17）。
4. **test_single_arch_break 断言修订**：简报断言 `sd[3]+0.4` 触发 `INV_SPANS_SYM`——**数学上不可能**：展开规则 `D + reversed(D[:-1])` 恒构造回文（实测任意扰动下回文恒成立，test_spans_expansion_is_palindrome）。按简报原意"一孔坏必须全局红"改断言 MET_CLOSURE；SYM 检测器本身用 monkeypatch derive 的检测器级负控证明非恒真。
5. **test_specificity 排除 MET_CLOSURE**：基线恒红是其设计行为，`assert not fails` 原样必红；改为"除 MET_CLOSURE 外全静默"，保留特异性本意。
6. **test_global_z_shift_break 注释勘误**：简报称"平移 0.5m 仍在容差内(已实测)"——**实测相反**：最小余量 +0.173m，0.5m 平移必红（余 -0.327m）；测试值 1.0m（红）/0.1m（绿）不变，仅注释改为实测值。

## 顾虑清单

1. **【重要，已私信 T2bClosure】-2.50m 是"墩数口径"产物，非桥台真偏小**：derive 布局为 2台+**16墩**=18支承（17 孔间 16 内墩），按 16 墩口径 `107.3+16×2.5+2×1.35 = 150.0000`（差 +0.0000，精确闭合；derive 闭走总长实测 150.0000；`bridge_geom2.py:180` 自身断言即 16 墩且通过）。15 墩口径系逐字照抄派发代码，我无权改。若 T2b 裁 16 墩口径，`BRIDGE_ABUT=1.35` 即闭合、基线自动转绿（届时 strict xfail XPASS 报错属预期）。**→ 已解决：T2b 终审裁 16 墩口径，基线真绿，见文末追记。**
2. **MET_ARCH_FAMILY 在 L1 不可由 facts 触发**：券弧采样是构造性真圆（残差 ~1e-16），判据在该层结构性恒真；其检测器（circle_fit_residual）负控已过（三心拱 0.0626 被抓/椭圆放行），**真实覆盖要等 T5 Blender 网格 L2 的实测采样点**——建议 T5 计划明确承接。
3. **verbatim `derive` 的已知崩溃路径**：`N_SPAN>17` 或 `SPAN_DISTINCT` 短于 9 时递推 IndexError（先于判据报告）。本次只修了 check_body 侧防御；derive 侧未动（须与 bridge_geom2 逐字一致，且该输入属 facts 双字段损坏场景）。若 T4 接线时认为需要，可在 facts 校验层拦。
4. 简报"Expected: 10 passed"已过时：按派发追加要求实为 19 条（18 passed + 1 strict xfail），符合追加清单本意。

## 追记（同日，T2b 终审裁决后）

**时间线**：T3 初版 `f250cad`（15 墩派发口径，基线 fail→strict xfail）→ 我实测发现 16 墩口径精确闭合并移交
T2bClosure → T2b 终审裁 16 墩口径（task-task-2b-report.md §4/§5）→ 裁决由后续提交落档（含 `085b46d`
MET_CLOSURE 文案更正、公式改 `(N_SPAN-1)`、摘 xfail、test_specificity 恢复简报原形、真负控拆分为
`test_met_closure_baseline_is_exactly_closed` + `test_met_closure_catches_real_gap`）→ 我的收尾 `f88f7c4`
（模块/函数 docstring 与注释块对齐终审口径、清陈旧"15 墩/2.60"表述、补阈值内微扰负控、删未用 `import pytest`）。

**更正一处 T2b 复述**：③称"(f.N_SPAN-1) 修改系我所落"——不实，我初版按派发逐字保留 15 并留言待裁；
公式落地系 T2b/T2c 后续提交完成，我仅做文案收尾。

**MET_CLOSURE 负控终态（16 墩口径，全部实测）**：
| 用例 | 闭合差 | 结果 |
|---|---|---|
| 基线（ABUT=1.35） | 0.000 | ✅ 静默（精确闭合） |
| ABUT=1.45（+0.1，阈值内） | +0.2 | ✅ 静默（0.5m 容差真实存在，非过敏） |
| ABUT=2.60（作废的 15 墩凑数解） | +2.5 | ✅ 被抓 |
| PIER_W=2.40 | −1.6 | ✅ 被抓 |
| 跨序 ×1.05 | +5.4 | ✅ 被抓 |

**最终测试**：`python3 -m pytest e30_shikongqiao_video/tests/ -v` → **35 passed, 0 xfailed**
（test_facts 15 条不变 + test_l1_body 20 条；本报告上方矩阵中 MET_CLOSURE 各行为初版 15 墩口径下的历史实测，
以本追记表为准；其余 11 条判据的破坏矩阵不受口径裁决影响，维持原文）。
T2b 请求⑤（fail 文案指向裁决）已随 `085b46d` 落地并在 `f88f7c4` 中核定为一致。
