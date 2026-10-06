# QA v2 实施进度

- 计划：`docs/superpowers/plans/2026-10-01-qa-v2-implementation.md`
- 分支：`qa-v2`（从 `97d9c2f` 起）
- 包名：`qa_v2`（`/tmp/chemistry-video/qa/` 被 E6–E10 缓存占用）
- 代码位置：`/Volumes/macstudio/video-projects/qa_v2/`、`.../tests/`
  （工程副本下有软链；git 命令一律在 video-projects 执行）

## 任务

- [x] Task 1  坐标换算
- [x] Task 2  标点与数字归一 —— commits bfd3279..6157857, review clean (0 findings)
- [x] Task 3  数据加载 —— commits 6157857..00fc304, review clean (0 C/I, 3 Minor)
- [x] Task 4  Finding 与报告 —— commits 00fc304..b2b72f3, review clean (1 Minor: 建议 assert→raise)
- [x] Task 5  L1 数据一致性 —— commits b2b72f3..29c7acd, review clean (0 findings)
- [x] Task 6  L2 溢出预检 —— commits 29c7acd..aca5c6e, review clean
- [x] Task 7  抽帧与 OCR 缓存 —— commits aca5c6e..6663f9b, review clean (1 Minor 已当场修: 冗余导入)
- [ ] Task 8  L3 + 负控制
- [x] Task 9  L5 溢出检测 —— commits 02081a0..50b4afe, review clean (1 Minor: 测试文件中段 import，纯风格)
- [x] Task 10 L6 tag 槽 —— commits 50b4afe..95b02bd, review clean (0 findings)
- [ ] Task 11 L4-a/L4-b 内容闭环
- [x] Task 12 L4-c 口播稿交叉 —— commits 3a5e9d9..f6fdbd7, review clean (0 findings)
- [x] Task 13 统一入口与 CLI —— commits f6fdbd7..fb96fa9, review clean (0 findings)
  端到端实测：fail 0 / warn 3 / 判定通过。3 warn 均为 L2 预检（ratio 1.18/1.18/1.30>1.15），
  L5 真实渲染通过 —— 预检宁可多报、最终由 L5 裁决，符合设计。
- [x] Task 14 端到端验收与负控制留证 —— commits fb96fa9..517576d, review n/a（验收 task）
  三类破坏全部被抓：SLOT_OVERLAP(100%交叠) / SLOT_RENDER_EMPTY(负控制证明非恒真) /
  NUMBER_MISMATCH(1486 vs 读回1485)。数据已恢复并验证，113 测试全过。
  实测耗时：L1+L2 1.90ms/集 · L3+L5+L6 523ms/集 · 快档 0.81s/集 · L4 冷识别 10.6s/页

## Minor findings 累积（交最终整支 review 分诊）

- Task 1：实现者修正了 brief 里 `test_out_of_bounds_detects_overflow` 的断言矛盾
  （`1672+10 > 1672` 原判 False 不自洽）——是计划笔误，不是实现问题
- Task 1：实现者清理了 brief 示例代码里的残留无用赋值
- Task 1：.gitignore 补了 qa_v2 放行规则（brief 未提及）

## 状态

**全部完成，已合并到 main（f874388）。**

- 14 个 task 全部完成并通过 task review
- 最终整支 review 报 2 Critical / 2 Important / 若干 Minor，全部已修
- 修复轮次：fix1（C1/C2/I1/I2）→ fix2（L4-c 重设计，19 假阳性→0）
  → fix3（OCR 粘连 + 负控制 bug，9 fail→2）→ fix4（繁简归一，2→0）
- 最终：快档 0.81s/集、全档 90s/集，E11 **fail 0**，**139 测试全过**

## 交付

- `docs/qa/README.md` —— 交付说明（含 6 个已修问题与 5 条已知限制）
- `docs/qa/2026-10-01-qa-v2-e11-report.md` —— E11 验收与负控制留证
- `docs/superpowers/specs/2026-10-01-qa-v2-design.md` —— 规格
- `docs/superpowers/plans/2026-10-01-qa-v2-implementation.md` —— 实现计划

- [x] Task 1  坐标换算 —— commits 97d9c2f..bfd3279, review clean（3 Minor 均是修正 brief 笔误）
