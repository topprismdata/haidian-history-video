# bridge3d 框架抽取报告（FrameworkExtract）

**状态**: DONE_WITH_CONCERNS（功能与验收全部达成；3 条顾虑见文末）

## 1. 交付

| 路径 | 内容 |
| --- | --- |
| `bridge3d/__init__.py` | 公开 API + 设计意图 docstring；`audit(f)` 一站式验收 |
| `bridge3d/schema.py` | facts 结构契约（duck typing + 显式检查，零继承）：REQUIRED / REQUIRED_LISTS / REQUIRED_REGS / OPTIONAL / GRADES 五级 / RELATIONS 关系型不变量；Finding(fail/warn/skip) 统一输出；`validate_facts_module` |
| `bridge3d/derive.py` | 纯拓扑推导，零项目数值：`spans`（对称展开 2n-1）/ `pier_x`（支承递推）/ `deck_z`（抛物线纵坡）/ `support_count`(=N_SPAN+1) / `pier_count`(=N_SPAN-1，拓扑推导非常量) / `geometry_closure` |
| `bridge3d/checks_l1.py` | 三层判据：INV（展开长度一致/回文护栏/跨宽为正/支承数/N_SPAN≥1 int）+ MET（闭合/纵坡中央最高/收分/券形比/拱背净空/起拱线）+ IMP（契约齐备/尺寸/容差合法/SOURCES 覆盖/等级合法/假设层隔离/RELATIONS 执行）。判据零项目数字，阈值一律来自 facts 或显式参数，前置缺失→skip |
| `bridge3d/facts_schema.py` | 事实层校验器（自 E30 test_facts.py 泛化）：SOURCES 完备/形状/等级五级/幽灵键(必填 fail/可选 warn)/工作值必须写明出处状态/等级造假/官方必须正面出处(否定语境年份无效)/研究旗标(bool；False=warn)/假设层不泄漏/三条禁令逐条锁 docstring |
| `bridge3d/negative_control.py` | 负控制基础设施：`mutate`/`dropped`（克隆隔离）/`assert_criterion_rejects`/`assert_criterion_accepts`/`assert_skip_not_fail`/`patched_derive`（检测器级负控）/`default_corruptions`（约 100 个自动类型化破坏用例）/`killability_report`/`assert_no_always_true`（恒真检测：杀不死=恒真、崩溃≠报告、基线红不自证） |
| `tests/bridge3d/`（7 文件 169 条） | 合成 facts：**5 孔小桥 + 23 孔大桥**（全部虚构工作值），逐判据破坏矩阵、skip 语义、特异性、检测器级负控、恒真审计自测、AST 字面量闸门 |
| `docs/bridge3d.md` | 第二个项目接入说明（1 页：三原则→facts 模板→audit→负控制义务→边界） |

## 2. 硬性验收证据

| 验收项 | 结果 |
| --- | --- |
| 等效全量 `python3 -m pytest tests/ e30_shikongqiao_video/tests/ -q` | **1552 passed**（root tests/ 1499，内含 bridge3d 169；E30 53） |
| E30 原有测试一条不少 | 简报时点 47 条全绿；现目录 53 条（新增 6 条为并发子任务 T7Register 的 `test_register.py`，未触碰原 47 条，**原 47 条含在内全绿**） |
| 判据源码无 `17`：`grep -n "\b17\b" bridge3d/*.py` | **零命中**（比"允许注释"更严；AST 闸门禁一切数值白名单外常量，且 5/17/23 三个孔数连注释都禁入） |
| N_SPAN=5 / 23 均通过 | `test_baseline_green_n5` / `test_baseline_green_n23`（audit 零 fail 零 skip）；16/100/单孔 N_SPAN=1 亦过拓扑测试 |
| 每条判据有"故意破坏"且被抓 | 逐代码破坏矩阵 + `assert_no_always_true`（含 derive 级：SYM/支承数护栏经由 facts 不可达，改坏推导必须红——E30 结论升格为框架设施） |
| 缺可选事实走 skip 不走 fail | `test_missing_single_optional_is_skip_not_fail`（11 可选项 × 2 桥）；实测：抽掉全部可选项 → `fail=0 warn=1 skip=7` |
| 简报原文命令 `pytest tests/bridge3d/ qa_v2_tests/ e30_shikongqiao_tests/...` | **无法执行**：`qa_v2_tests/` 在仓库不存在（pytest: file or directory not found）。qa_v2 七层验收的测试实际位于仓库根 `tests/`，已并入上面的等效命令 |

设计要点（供第二个项目）：拓扑（INV）与项目声明（RELATIONS）彻底分家——"中央孔最大两侧渐小"这类历史主张是**项目声明**，框架不预设；度量阈值（闭合容差、券形意图）没有依据就 skip，绝不自带"看起来合理"的数；E30 曾记录的"N_SPAN 与展开不一致→递推 IndexError 崩溃"已知缺陷在框架里改为 MissingFactError→判据报告而非崩溃。

## 3. E30 迁移清单（下一步任务用，本次未改任何 E30 文件）

`17` 出现位置（grep 实测）与处置：

| 位置 | 性质 | 迁移动作 |
| --- | --- | --- |
| `3d/qa_bridge.py:48-50` | **判据内项目常数**（`!=17`/`==17`/`!= 17` 消息） | 删除：一致性由框架 INV_SPANS_LEN(==N_SPAN) 承担；N_SPAN≥1 int 由框架 INV_N_SPAN 承担 |
| `3d/qa_bridge.py:60,68,74` | 注释/消息文本 | 随判据迁移改写，可保留历史口径说明 |
| `tests/test_facts.py:101,107` | 注释/docstring | 无需改（断言本身已是关系式：`len(expanded)==facts.N_SPAN`） |
| `tests/test_l1_body.py:41,89,121` | 注释 | 无需改 |
| `tests/test_l1_body.py:134` | `assert len(d.SPANS) == 17` | 改 `== facts.N_SPAN` |
| `tests/test_l1_body.py::test_inv_n_span_break`（N_SPAN=15） | 破坏用例指向旧判据 | 改期望代码：N_SPAN=15(展开 17)应红在 `INV_SPANS_LEN` |

`qa_bridge.check_body` 其余项目数字的迁移映射：

| 现状 | 迁移 |
| --- | --- |
| `INV_SPANS_MONO`（中央最大两侧渐小） | facts 增 `RELATIONS["central_span_largest"]`（历史主张属项目声明）；框架已验证该 RELATION 代码随破坏变红 |
| `MET_CLOSURE` 阈值 0.5 | facts 增 `CLOSURE_TOL = 0.5`（登记 [工作值]+T2b 出处），判据零改 |
| `MET_ARCH_RATIO` 0.50±0.05 | facts 增 `ARCH_RATIO_TARGET=0.5` / `ARCH_RATIO_TOL=0.05` |
| `MET_RING_FIT`/`MET_SPRINGER`/`MET_DECK_DIR`/`MET_TAPER` | 框架同名判据已参数化，直接换用 |
| `IMP_DIM` 的 `PIER_W<=0.2` 下限 | 0.2 是项目经验数 → RELATIONS（如 `pier_walkable`）或保留在项目侧测试 |
| `circle_fit_residual` | 属 L2 实测（合成模型点上恒≈0），留在项目 qa_l2，不入 L1 |
| `check_body` 单函数 | `run_l1(facts)` 替代；`assumptions.CIRCLE_FIT_RTOL` 留项目侧 |

## 4. 顾虑

1. **`qa_v2_tests/` 不存在**：硬性验收命令照抄会报 file not found。qa_v2 的测试在仓库根 `tests/`（与本次新建 `tests/bridge3d/` 同目录）。我未擅自移动/建目录（不碰 qa_v2 是硬约束，动 root tests/ 属仓库级决策）。等效命令全绿 1552 条。
2. **E30 测试数 47→53**：并发子任务在 `e30_shikongqiao_video/tests/` 新增 `test_register.py`（6 条）。原 47 条未被动过、全部在内全绿；"一条不少"按原基线成立。
3. **对既有 `tests/` 的连带修复为零、但有一个命名代价**：root `tests/haidian_kg/` 已有 `test_negative_control.py`（无 `__init__.py` 的 rootless 收集模式会模块名冲突），故框架侧命名为 `test_negative_control_tools.py`。若后续统一加 `__init__.py` 可改回。
