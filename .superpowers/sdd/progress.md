# E30《十七孔桥》桥体本体 M0→M2.5 实施进度 (SDD Ledger)

- 计划：`docs/superpowers/plans/2026-10-04-e30-bridge-body-m0-m25.md`
- 规范：`docs/superpowers/specs/2026-10-04-e30-bridge-facts-design.md`
- 分支：`e30-bridge-body`（从 main @ 1bcf644 切出）
- 任务序列：T1 → T2 → T2b → T2c → T3 → T3.5 → T4 → T5 → T6 → T7 → T8

## 任务

- [x] Task 1: facts.py 本体节骨架 + assumptions.py + 来源完备性测试 (commits d413985..<T1fix>, review clean: 规格✅/质量Approved, 8测试经13突变探针证伪; 修复后11测试)
- [x] Task 2: M0 研究回填 facts (commit cb64710; 数值零改动, 12项无公开测绘值诚实落[工作值]; C1-C5 冲突登记; 史料节; 3条顾虑: 2019原始页未检回/严雨篇名不符/C4实为三值冲突90-112-135) — 审查中发现旗标闸门设计缺陷, 已由主控裁决收窄
- [x] Task 2b: 闭合差归因 + 冲突登记（C1）→ **由 T3 顺带闭环**（16 墩口径）, T2bClosure agent 仅余对照研究价值
- [ ] Task 2c: 方法论文献核查 + 可信度缺口登记
- [x] Task 3: qa_bridge L1 三层判据 + 负控 (commit f250cad; 12判据×破坏用例矩阵; **发现闭合差是计划稿15墩算术错误, 17孔间为16墩精确闭合**; 主控修公式为 (N_SPAN-1) 并摘 xfail, 现 35 测试零 xfail)
- [x] Task 3.5: 参考资产冻结 (commit 21c6cd8; 冻结 frontal_2011.jpg+ref_mask.png, **未看本体重渲即冻结**; 主动落选观感最佳的 IMG_0398——实测跨桥 px/m 梯度 15.8→11.2 证明有透视, 不可证<15°; 落选审计表入 FACTS §6.3 防后续偷换)
- [x] Task 4: bridge_geom2 从 facts 取数 (commit 78c3cc3; **几何前后 SHA 逐字节相同** 桥体964v/960f sha e8cd1ced, 证明接线零漂移; 37测试; 发现C6桥台双值)
- [ ] Task 5: qa_l2 Blender 网格判据 + 独立 validator
- [x] Task 6: 桥体重建+5机位出图 (commit cf11ac3; **修出图桥轴 103.15→112.0 差8.85°** 此前立面全被压缩; 17孔序列实测对称递减正确; 主控另修 abutment_ground 漏旋转 bc485a5)
- [x] Task 7: L3 配准比对 (commit d30502f; 53测试; OVERLAY_IOU_MIN=0.76 由扰动标定取中点非拍脑袋; **诚实申报4项无判别力**并逐条归因; 渲染侧弃 RGB 阈值改 alpha(实测与真值 IoU 仅0.15); 主控补正券洞表效力边界——只跑渲染侧, facts错了会一致地错)
- [x] Task 8: 冷重建+manifest (commit 6d8a838 + 0b346e5; **几何硬门全 MATCH 主控独立复核**; 渲染像素复现**被 agent 证伪**(arch 5渲5异, 自适应采样调度非确定)→如实降级为配置锁定; 冻结态 CONDITIONAL_RECONSTRUCTION_FREEZE 待用户裁决)

## 通用框架 bridge3d（用户 2026-10-04 追加要求："十七孔桥只是第一个项目"）

- commit `7510737`：`bridge3d/`（schema 契约 / derive 拓扑推导 / checks_l1 18 条三层判据 / facts_schema 五级来源校验 / negative_control 负控制+恒真检测）+ `tests/bridge3d/` 169 条 + `docs/bridge3d.md`
- 源码 `grep -rn "\b17\b" bridge3d/*.py` **零命中**；合成 5 孔/23 孔桥证明不依赖 17
- **主控独立验证**（造一个框架测试里没有的构型：53 孔薄墩联拱桥）→ 暴露 **`MET_TAPER` 过度约束**（原强制收分，等宽桥非法）→ 修 `8f549c2`，53 孔桥基线 fail 2→0，1555 测试全绿
- **主控已定位、待裁定**：`inv_spans_sym` + `REQUIRED_LISTS=("SPAN_DISTINCT",)` 强制对称，但**卢沟桥（十七孔桥官方蓝本）实测左右不对称**（东拱 11.40 ≠ 西拱 12.35，两端墩距 16.49 ≠ 16.64，见 FACTS.md S6 引文）——框架当前契约接不了自己第一个项目的蓝本。影响比 MET_TAPER 大（写进了 schema 层）。已发审查员独立确认。

## 最终整支审查（44 commit，reviewer agent，裁定：修复后可合并）

**1 Critical + 16 Important（5 条标 ★ 须合并前处理）+ 11 Minor**

### C1（已修，`git add` 三文件）—— **推翻了我此前对用户报告的核心结论**

`build_scene2.py:5-6` `import materials as MAT` / `import lions as LIONS`，但 **materials.py / lions.py / bridge_geom.py 三个文件从未入库**（`git ls-files` tracked=0）。干净克隆（`git archive HEAD`）里 `import build_scene2` 直接 `ModuleNotFoundError`。

> **我此前报告"冷重建硬门通过、证明的是可重建而非恰好留下一个对的 .blend"——该结论当时不成立。**
> 它能重建只因为**我工作站上恰好有那两个文件**。审查员用 `git archive` 造干净克隆才暴露。
> **教训：验证"可从零重建"必须在干净克隆里做，不能在工作树里做。** 工作树里所有未跟踪文件都是隐形的依赖。

修复后我**在干净克隆里重跑并逐位复核**：`bridge_body` sorted=`6194d02d5557cc91` order=`829e255a47213aac`、`voussoir` `da5441c7628a3215`/`27395befa6ce4c9f`、`impost` `3db908a3a628646f`/`330ed36ca73ba3c4` —— 干净克隆与工作站**全部一致（含顶点顺序）**。这次是真的。

### 待修（FixStarred agent 进行中）

- **I1★** 对称性契约（用户已批准放宽）：偶数孔桥结构上不可表达（展开恒 2n−1），不对称桥无字段可表达；反例即蓝本卢沟桥
- **I2★** 冻结哈希闸门只覆盖 15 条中的 8 条，`render_shot.py` 已漂移无人报
- **I3★** L3 券洞硬判**只存在于文档**，代码里没有——实测少 1 孔 IoU=1.0000 仍 PASS，`VOID_XC_TOL` 全仓 0 处消费
- **I4★** L2 判据未执行仍报通过：`tot==0` 只 warn、`ok=not fails` → **skip 被当成 pass**，违反项目铁律
- **I5★** 恒真检测器只查"能不能红"、不查"合法基线该不该绿" → **MET_TAPER 那类过度约束能通过审查**。这是 I1 至今存活的机制

### 审查员的恒真总裁定（独立实验，非转述）

判据整体**不是恒真的**（L1 18 条、等级/禁令锁、L2 WALL_NORMAL、L3 IoU 轴均经 26 例手工破坏 + 真 Blender 验证"改坏会红"）；**但存在四类真实空转**：L3 券洞硬判只有文档、L2 未执行/负控脱靶都报 ok:true、恒真检测器不防"见谁都咬"与死判据、三处子串/真子集式假通过。诚实边界（12 条工作值、渲染非确定降级、L3 四轴无判别力、券洞表只跑渲染侧）**经核对均如实记录、无隐瞒**。

## Minor Findings 累积

- T1: SOURCES 覆盖率测试对 str/tuple/dict 类型常量有盲区（Minor，留 T2 观察）
- T1: facts.py 6 处 inline 注释写 `[待核]` 而 SOURCES 写「工作值」（PIER_W/PIER_MAIN_W/PIER_FOUND_W/PIER_MAIN_W_C/PIER_FOUND_W_C/DECK_Z_AT_PIER）→ **T2 必须归一并进冲突登记**
- .gitignore 已放行 e30 的 3d/ 与 tests/（commit 后补）

## 主控亲自做的负控制（2026-10-04，facts 测试层）

初版 13 测试看似完备，**实测 4/5 探针漏网**。逐个补锁后 15 测试，**6 探针全部被精确捕获**：

| 探针 | 结果 |
|---|---|
| 工作值谎标「官方」 | 初版**全绿漏网** → 补 `test_grades_are_not_inflated` |
| 官方级整条换成"据说" | 初版**全绿漏网**（"2019原始页未检回"否定语境里的年份骗过正则） → 补正面陈述判定 |
| 官方换二手转述"据百科 2025" | 已抓 |
| 官方只留否定语境 | 已抓 |
| 官方降级为工作值 | 已抓（同时暴露 N_SPAN 定义行注释未同步） |
| SOURCES 漏登一条 | 已抓 |

**新锁当场抓到 3 处数据缺陷**（不是测试的问题）：`DECK_DOWN_W`/`N_SPAN` 用"URL 同 X"间接引用、`PUBLISHED_BRIDGE_HEIGHT` 出处未拆段。均已改为自证引用。

**教训固化**：负控制探针自己也会静默失败——前两轮"全绿"里有一半是探针没改到文件（替换串与文件实际内容不符），第三轮探针因 `index('\n')` 吃掉逗号导致 SyntaxError 报成"1 error"。**探针必须先自证有效**（如 `assert old in s`），否则"漏网"结论不可信。

## T7 的结构性约束（T3.5 量化后确立, 影响 T7 设计）

库内**不存在**"合规（视偏角可证<15°）且高清（桥体带≥300px高）"的近正面照。冻结的 frontal_2011 桥带仅 **843×44 px**（单拱 25-38px），拱洞未抠空，**不足以做逐拱轮廓比对**。

因此 T7 只能执行**构图与轮廓一致性**低调口径（T2c 学术定性同源：hypothetical reconstruction）——可核：驼峰曲线走向、拱跨渐变方向、长高比例。**不得声称逐拱轮廓校核**。若要升级须补拍或外采（外采须履行出处登记，§6.2-8）。

## 已核实的数字纠错（自审，非用户）

- **C6 桥台双值**：本体 `BRIDGE_ABUT=1.35`（闭合唯一解）vs 构件 `BRIDGE_ABUT_TARGET=2.00`（GPT v4 提案，`build_scene2.py:310` 实际渲染用）。桥台是本体构件不得有两个长度——裁决统一 1.35，删 2.00，列入 T6 Step 0。

- **闭合差 -2.50m 是假矛盾**：17 孔之间是 **16** 个墩（不是 15），107.3+16×2.5+2×1.35 = **150.0 精确闭合**。原计划稿与我的记忆都按 15 墩算，凭空造出一个"待归因的真矛盾"，差点把正确的 `BRIDGE_ABUT=1.35` 改成 2.60。教训：**自己制造的算术矛盾不能当"待归因的真矛盾"**——T3 agent 照抄简报时对着既有代码断言 `bridge_geom2.py:180` 一对才发现。
- 圆拟合反例：椭圆残差仅 0.0025 < 阈值 0.01 **抓不到**；尖顶三心拱残差 0.0626 才对（G2 判据曾用错反例）

## 硬约束速查

- Python 3.9.6（禁 `X | None`、禁 `match`）；git 仅在仓库根执行
- 斜拍照片禁用于数值比例测量；GPT 聊天记录不算来源；ESRGAN 禁入计量链
- 只动 `e30_shikongqiao_video/3d/` 与 `e30_shikongqiao_video/tests/`
- 判据：只有 fail 阻塞；每条判据须有"故意破坏被抓"用例
