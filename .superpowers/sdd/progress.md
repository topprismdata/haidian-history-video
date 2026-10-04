# E30《十七孔桥》桥体本体 M0→M2.5 实施进度 (SDD Ledger)

- 计划：`docs/superpowers/plans/2026-10-04-e30-bridge-body-m0-m25.md`
- 规范：`docs/superpowers/specs/2026-10-04-e30-bridge-facts-design.md`
- 分支：`e30-bridge-body`（从 main @ 1bcf644 切出）
- 任务序列：T1 → T2 → T2b → T2c → T3 → T3.5 → T4 → T5 → T6 → T7 → T8

## 任务

- [ ] Task 1: facts.py 本体节骨架 + assumptions.py + 来源完备性测试
- [ ] Task 2: M0 研究回填 facts（存疑清单逐条）
- [ ] Task 2b: 闭合差归因 + 冲突登记（C1）
- [ ] Task 2c: 方法论文献核查 + 可信度缺口登记
- [ ] Task 3: qa_bridge L1 三层判据 + 负控
- [ ] Task 3.5: 参考资产冻结（选图+掩膜）
- [ ] Task 4: bridge_geom2 从 facts 取数
- [ ] Task 5: qa_l2 Blender 网格判据 + 独立 validator
- [ ] Task 6: 桥体重建 + 5 机位渲染
- [ ] Task 7: 正交立面对叠 + 扰动标定阈值
- [ ] Task 8: 冷启动重建 + manifest + M2.5 冻结闸门

## Minor Findings 累积

（无）

## 硬约束速查

- Python 3.9.6（禁 `X | None`、禁 `match`）；git 仅在仓库根执行
- 斜拍照片禁用于数值比例测量；GPT 聊天记录不算来源；ESRGAN 禁入计量链
- 只动 `e30_shikongqiao_video/3d/` 与 `e30_shikongqiao_video/tests/`
- 判据：只有 fail 阻塞；每条判据须有"故意破坏被抓"用例
