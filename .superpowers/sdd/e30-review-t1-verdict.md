# E30 Task 1 审查报告（T1Review）

- 审查对象：`.superpowers/sdd/e30-review-t1-210627.txt`（范围 `56f66cc..d413985`）
- 被审提交：`d413985 feat(e30): T1 facts骨架+assumptions假设层+来源完备性测试`
- 需求来源：`.superpowers/sdd/e30-briefs/task-task-1-brief.md`
- 方法：独立跑 pytest（不采信实现者报告）＋ 简报代码块与仓库文件字节级比对 ＋ `/tmp` 下 13 个一次性突变探针（S0–S11c，未改仓库任何文件）
- 环境：python 3.9.6，`8 passed`（0.02s），EXIT=0

---

## 0. 范围与提交归属（先澄清 STAT 里的第 4 个文件）

- `d413985`（T1 本体）只改了 `3d/facts.py`(63行)、`3d/assumptions.py`(9行)、`tests/test_facts.py`(101行) —— **与本任务"只允许三个文件"的硬约束完全一致**。
- 范围内另一提交 `549076c` 只改了计划文档 `docs/superpowers/plans/2026-10-04-...md`（T2b/T3 嵌入代码的三处硬错误修订），属计划文本修正，**不是 T1 的越界改动**。审查范围内出现它不构成 T1 违规。
- 提交信息 `feat(e30): T1 facts骨架+assumptions假设层+来源完备性测试` 符合 `<type>(<scope>): <中文摘要>` 格式。（简报 Step 4 的 git add 行漏了 assumptions.py——简报自身笔误；实现者正确地把三个文件都纳入了提交。）

## A. 规格合规

### A1. Step 1 代码逐字落地 —— ✅ 完全一致

字节级比对（非目测）：

| 文件 | 简报代码块 | 仓库文件 | 结果 |
|---|---|---|---|
| `3d/facts.py` | 2453 B | 同 | **逐字一致（byte-identical）** |
| `3d/assumptions.py` | 442 B | 同 | **逐字一致（byte-identical）** |

全部 19 个数值（150.0 / 17 / 7.75 / 5.05 / 6.56 / 14.6 / 8.0 / 7.0 / 0.50 / 2.50 / 0.40 / SPAN_DISTINCT 九值 / 2.50 / 2.80 / 3.10 / 2.90 / 3.20 / 1.35 / DECK_Z_AT_PIER 九值）与简报一模一样，无任何数值改动。assumptions 五参数（-2.20 / 0.005 / 0.01 / 40 / 240）一致；G2 要求废除的 `CROWN_CLEARANCE_MIN` 确实不存在。三条禁令逐字进入 docstring。

### A2. Step 2 测试存在性 —— ✅ 全部存在且加强，无缺失

| 简报要求 | 交付形式 | 备注 |
|---|---|---|
| `test_every_constant_has_source` | 同名，改为收集缺失列表后一次断言（报错信息更全） | 等价加强 |
| `test_source_levels_valid` | `test_sources_value_shape` | **等级集合有偏离**，见 A2.1 |
| `test_no_pending_after_research` | `test_pending_gate_tracks_flag` | 由 if-早退改为随旗标动态判定，且把 [工作值] 一并纳入 True 后禁用——与全局约束"置 True 后禁止 [待核]/**[工作值]**"一致，比简报版（只禁 待核）更正确 |
| `test_span_distinct_shape` | `test_span_distinct_shape_and_symmetric_closure` | 保留 9+9 形状断言，追加对称展开/水路闭合 |

简报要求的 4 条测试一条不少、无一弱化。

**A2.1 等级集合偏离的裁定：偏离正当且必要。** 简报 Step 2 代码写的 `ok = {"测绘","文献","实拍","工作值","待核"}` 与简报自己的 Interfaces 行（"G1 修订：来源五级 测绘/档案/官方/图像推导/工作值"）直接矛盾；且 facts.py 的 SOURCES 使用 官方×6、图像推导×1——若逐字照抄 Step 2 的集合，这 7 条会判"等级非法"，测试根本不可能 PASS。实现者按 G1 五级 + 待核 取集合（`ALLOWED_LEVELS`，与 facts docstring 的五级定义逐字一致）是消解简报内部矛盾的唯一自洽解。登记为"对简报字面代码的有据偏离"，非缺陷。

### A3. 多做（超出简报的 4 条新增测试）—— 均有约束出处，不构成 YAGNI 违规

1. `test_sources_keys_are_live_names`（SOURCES 反向不得指向不存在常量）：核心判据"漏一即 fail"的双向封闭，防改名残留（如旧名 SPANS/HALF_SPANS）。合理。
2. `test_research_done_initially_false`：锁初始旗标。**简报没要求，且是本次唯一有实际副作用的多做**——见 B-发现 1。
3. `test_assumptions_not_in_sources`：全局硬约束"假设层不得出现在 SOURCES"的直接可执行化。必须做。
4. `test_docstring_carries_bans`：全局硬约束"三条禁令……必须可被测试锁住"的可执行化。方向必须做，但**只锁了 1/3**——见 B-发现 2。

无多做的文件、无多做的常量、无多余的接口名。Interfaces 列出的 21 个 facts 名 + 5 个 assumptions 名全部存在，一个不少。

### A4. 少做 —— 未发现

简报 Step 1–4 全部落地；Step 3 期望"4 passed"实为 8 passed（简报期望值相对其自身的加强实现已过期，属简报侧滞后，不是缺陷）。

### A5. 规格合规判定

**✅ 合规。** 数值逐字、文件范围逐字、测试全覆盖、提交格式合规；唯一字面偏离（测试等级集合）是消解简报内部矛盾的必要更正，已留痕。

---

## B. 代码质量

### B1. 恒真测试分析（逐个用突变探针证伪）

**结论：8 条测试中未发现恒真测试**——每一条都在至少一个故意破坏场景下转红（探针 S0–S10b，全部在 /tmp 副本上运行）：

| 测试 | 破坏方式（探针） | 结果 |
|---|---|---|
| `test_every_constant_has_source` | 新增 `PROBE_NUM=9.9` 不登记（S1） | ✅ 1 failed，**抓到** |
| `test_sources_keys_are_live_names` | SOURCES 塞入 `OLD_SPANS` 死键（S6） | ✅ 抓到 |
| `test_sources_value_shape` | 一条等级改为"官方页"（S5） | ✅ 抓到 |
| `test_research_done_initially_false` | 旗标翻 True（S3） | ✅ 抓到 |
| `test_pending_gate_tracks_flag` | 旗标翻 True，[待核]/[工作值] 共 12 条在册（S3） | ✅ 抓到 |
| `test_span_distinct_shape_and_symmetric_closure` | 尾跨 8.50→8.60 破坏 107.3（S8）；PIER_W 2.50→2.60（S4） | ✅ 两处都抓到 |
| `test_assumptions_not_in_sources` | 把 `NSEG_ARC` 塞进 SOURCES（S9） | ✅ 双测试抓到 |
| `test_docstring_carries_bans` | 整条禁令行删除（S7）；仅删"计量"关键词（S11c） | ✅ 抓到 |

**调度者点名核验的两项，实测回答：**

1. **覆盖率测试遍历的是 facts 模块实际常量（`dir(facts)` + 类型过滤），不是遍历 SOURCES 自身**。新增一个不进 SOURCES 的 **int/float/list** 常量会被抓（S1 实证 fail）。**但存在类型盲区**：`_public_constants` 只收集 `int/float/list`，新增 **str/tuple/dict/set** 常量时探针 S2 实测 **8 passed 全绿放行**——此时双向检查（含 `test_sources_keys_are_live_names`）都抓不到。该过滤器逐字承自简报，属继承缺陷而非实现者自创；但 test_facts.py 顶部"漏一即 fail"的声明相对过宽。降级为 Minor（当前 facts 无此类常量），修复方向：扩 `_public_constants` 的类型集或收窄 docstring 声明。
2. `test_baseline_green` **不在本次交付物中**——它只存在于计划文档的 T3 嵌入代码里（`tests/` 目录现仅 test_facts.py）。其质量归 T3 审查；此处仅提示：计划已自证 MET_CLOSURE 基线红（-2.50m）且"禁止调宽容差让它绿"，T2b Step 0 有正确的心态预设。

**两个"接近恒真"但不判恒真的点**：`test_pending_gate_tracks_flag` 在旗标 False 期间是空转（forbidden=() 恒空集）——这是旗标闸门的定义性行为而非恒真缺陷，同期 `test_sources_value_shape` 仍在有效工作；`test_span_distinct_shape_and_symmetric_closure` 第二条断言名义上写"自洽校验"，由于第一条已钉死 water==107.3，它数学上等价于钉死 `PIER_W==2.50`——S4 证明它可证伪（改 PIER_W 即红），**不是恒真**，但属于"伪装成自洽校验的取值钉死"，见 Minor-5。

**空注册表与模块级退化均有防线**：SOURCES 清空→coverage 抓（S10b）；assumptions 意外清空→`assert assumption_names` 护栏抓。

### B2. 来源等级诚实性

逐条对照五级定义与三条禁令，**未发现等级造假（把工作值标成官方类）**，且诚实度有多处加分项：

- **加分**：`DECK_Z_TOP` 标 [工作值] 并明写"(GPT建议)"——GPT 建议只作为工作值的出身披露，不冒充来源，恰好是禁令③的正确执行方式；`SPAN_DISTINCT` 标 [工作值] 且注明"中央孔8.50无公开测绘值"；`PUBLISHED_GENERAL_WIDTH` 与 `DECK_UP_W` 的口径冲突如实并存（conflict_unresolved），没有取均值抹平——符合"两源冲突不取区间值"的既有纪律；`PUBLISHED_BRIDGE_HEIGHT` 注明"禁映射DECK_Z_TOP"，防止 7.0 与 7.75 的基准面混淆。
- **`ARCH_RATIO` 标 [图像推导]：恰当。** 五级中"图像推导"本来就是合法等级；禁令①只禁止"未标定照片产生**绝对米制尺寸**"，而 0.50 是无量纲比值，不在禁令射程内；说明里明确"ESRGAN 版测量已退出计量链"——这是禁令②的**合规声明**（交代超标测量已被剔除），不是违规引用。"目视≈1.00"的精度低，但等级与说明诚实交代了这一点并留了"待测绘升级"路径。结论：名副其实。
- **`BRIDGE_ABUT` 说明中的"候选 2.00 GPT设计"：不构成违规。** 判定依据是登记的**等级字段**：此处等级为"待核"，即明确声明"目前没有合法来源"；说明字段披露候选值出身（GPT 设计提案 / 2.60 闭合推导）恰恰是防止后人把 GPT 数字误当档案证据的诚实做法。禁令③禁止的是"GPT 聊天记录**算**来源"——若等级写成 官方/档案 而出处写 GPT，才是违规。此处不违规。同理 `SPAN_DISTINCT` 的"GPT冻结表"披露也在 [工作值] 之下，合规。
- 唯一的等级语义瑕疵是 inline 注释与注册表的 6 处不一致，见 B4。

### B3. xfail 使用诚实性

**交付物中 xfail 出现次数 = 0**（对 `e30_shikongqiao_video/` 全树 grep 证实，测试 8 条全部是无标记的普通断言）。因此本任务不存在"非 strict xfail 把意外通过静默变 XPASS"的恒真温床。简报原版 `test_no_pending_after_research` 的 if-早退模式（flag=False 时 return）也被替换成了动态闸门，消除了"看起来在测实际啥都没测"的观感。

**给 T3 的前瞻提示（非 T1 缺陷）**：计划文档允许 `test_baseline_green` 在 T2 归因前打 xfail，但**未规定 `strict=True`**；而 T2b 的正当修复（BRIDGE_ABUT 定稿回填）恰会让基线转绿触发 XPASS。若 T3 实现时不加 `strict=True`，标记的摘除就依赖人的记忆。建议在 T3 简报中明写 `@pytest.mark.xfail(strict=True, reason="MET_CLOSURE -2.50m 待 T2b 归因")`。

### B4. 数值与等级一致性（inline 注释 vs SOURCES 注册表）

程序化比对全部 19 个常量，**13 条一致，6 条不一致**，全部同一模式——inline 写 `[待核]`、注册表写 `工作值`：

| 常量 | inline | 注册表 |
|---|---|---|
| PIER_W | [待核] | 工作值 |
| PIER_MAIN_W | [待核] | 工作值 |
| PIER_FOUND_W | [待核] | 工作值 |
| PIER_MAIN_W_C | [待核] | 工作值 |
| PIER_FOUND_W_C | [待核] | 工作值 |
| DECK_Z_AT_PIER | [待核] | 工作值 |

（其余 13 条：BRIDGE_LEN/N_SPAN/DECK_UP_W/DECK_DOWN_W/PUBLISHED_GENERAL_WIDTH/PUBLISHED_BRIDGE_HEIGHT=官方，DECK_Z_TOP/DECK_Z_END/SPRINGER/RING_T/SPAN_DISTINCT=工作值，ARCH_RATIO=图像推导，BRIDGE_ABUT=待核，inline 与注册表全一致。）

**这 6 处不一致是简报自身代码块原样带来的**（简报 facts.py 即如此写），实现者受"数值必须逐字照用"约束照抄，责任在简报。但缺陷是真实的：注册表是机器闸门唯一读取的权威（`test_pending_gate_tracks_flag` 只看 SOURCES）——若这 6 个数真如 inline 所说"待核"，则 RESEARCH_DONE 翻 True 时闸门会把它们当**已定稿工作值放行**，而人读注释仍以为未核。两个等级在当下都合法，故不阻塞本任务；必须在 T2 研究回填时二选一（真待核→注册表改"待核"，仅工作值→inline 注释去掉 [待核]），否则埋下冻结期语义漂移。已属应登记项。

### B-发现清单

**Critical：无。**（数值逐字、范围干净、测试在声明域内全部可证伪。）

**Important：**
1. `test_research_done_initially_false` 是**自爆式锁**：计划规定 M0 完成后把 RESEARCH_DONE 置 True，届时探针 S3 证明套件必然转红且持续红，直到有人手删/改这条简报没要求的测试。要么给它计划内的退役步骤（T2 任务里明写"删除本测试"），要么改成"不得在研究完成前为 True"的单向断言。当前形态会把未来某次合规操作变成假故障。
2. 全局约束要求"三条禁令……必须可被测试锁住"，`test_docstring_carries_bans` 实际只锁了禁令②的关键词（ESRGAN/计量）：探针 S11a/S11b 证明**删掉禁令①（未标定照片）或禁令③（GPT聊天）整句，套件仍然 8 passed**。应补 `assert "未标定照片" in doc` 与 `assert "GPT" in doc`（更稳的是对三句禁令全文各断言一次）。
3. （继承自简报，责任在简报、义务在 T2）B4 的 6 处 inline [待核] vs 注册表 工作值 不一致，须在 T2 回填时归一，并进 FACTS.md 冲突登记。

**Minor：**
4. `_public_constants` 类型盲区（str/tuple/dict/set 常量可不登记，S2 实证放行），与"漏一即 fail"的声明不匹配；承自简报同款过滤器。
5. `test_span_distinct_shape_and_symmetric_closure` 第二条断言把"PIER_W 钉死在 2.50"包装成"自洽校验"（S4 证明实为取值钉死）：T2b 正当修订墩宽时会以误导性消息"自洽校验失败"转红。建议改名为显式取值断言或移入 T2b 的闭合判据语境。
6. 建议性：T3 简报应为 xfail 补 `strict=True`（见 B3）；计划 Step 3 "Expected: 4 passed" 相对交付的 8 条已过期，宜在计划账本里改记 8。

### 证据可复现

- 独立验证：`cd /Volumes/macstudio/video-projects && python3 -m pytest e30_shikongqiao_video/tests/test_facts.py -v` → 8 passed。
- 突变探针脚本：`/tmp/t1_probe/run_probes.py`（S0–S10b）、`/tmp/t1_probe2/run_probes2.py`（S11a–c + inline/registry 比对），均为一次性脚本，未触碰仓库。
