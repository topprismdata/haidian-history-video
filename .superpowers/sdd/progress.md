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
- [ ] Task 3.5: 参考资产冻结（选图+掩膜）
- [ ] Task 4: bridge_geom2 从 facts 取数
- [ ] Task 5: qa_l2 Blender 网格判据 + 独立 validator
- [ ] Task 6: 桥体重建 + 5 机位渲染
- [ ] Task 7: 正交立面对叠 + 扰动标定阈值
- [ ] Task 8: 冷启动重建 + manifest + M2.5 冻结闸门

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

## 已核实的数字纠错（自审，非用户）

- **闭合差 -2.50m 是假矛盾**：17 孔之间是 **16** 个墩（不是 15），107.3+16×2.5+2×1.35 = **150.0 精确闭合**。原计划稿与我的记忆都按 15 墩算，凭空造出一个"待归因的真矛盾"，差点把正确的 `BRIDGE_ABUT=1.35` 改成 2.60。教训：**自己制造的算术矛盾不能当"待归因的真矛盾"**——T3 agent 照抄简报时对着既有代码断言 `bridge_geom2.py:180` 一对才发现。
- 圆拟合反例：椭圆残差仅 0.0025 < 阈值 0.01 **抓不到**；尖顶三心拱残差 0.0626 才对（G2 判据曾用错反例）

## 硬约束速查

- Python 3.9.6（禁 `X | None`、禁 `match`）；git 仅在仓库根执行
- 斜拍照片禁用于数值比例测量；GPT 聊天记录不算来源；ESRGAN 禁入计量链
- 只动 `e30_shikongqiao_video/3d/` 与 `e30_shikongqiao_video/tests/`
- 判据：只有 fail 阻塞；每条判据须有"故意破坏被抓"用例
