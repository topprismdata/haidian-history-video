# Task 8: M2.5 冻结包（止于用户闸门）

> 本文件由计划自动抽取，是该任务的**唯一需求来源**，其中数值必须逐字照用。

### Task 8: M2.5 冻结包（止于用户闸门）

**Files:**
- Create: `e30_shikongqiao_video/3d/refs/freeze_M25.md`
- Create: `e30_shikongqiao_video/3d/refs/body_changelog.md`

**Interfaces:**
- Consumes: Task 2-7 全部产物
- Produces: 冻结包文档；用户批准后 facts 本体节锁死

- [ ] **Step 1: 出 5 机位素颜图（环境用当前锁定值，不新调）**

Run（在 3d/ 下）:
```
blender -b --python ortho.py -- side 2200
blender -b --python shot_auto2.py -- hero 1600 96
blender -b --python shot_auto2.py -- arch 1600 96
```
（rail/lion 特写机位属 M3 附属件，本体冻结包不含）

- [ ] **Step 2: 写 freeze_M25.md**：判据结果（pytest 计数、L2 JSON、IoU 值）、ortho 对叠图路径、已知偏差清单（来自 Task 7 Step 3）、facts 等级分布统计（测绘/文献/实拍/工作值 各几条）

- [ ] **Step 3: 初始化 body_changelog.md**

```markdown
# 本体变更记录
## 2026-10-XX M2.5 冻结前基线
- commit: <填充提交哈希>
- 状态: 待用户目验
```

- [ ] **Step 4: 冷启动重建（G3 硬门）**: 删除 e30_bridge.blend 与全部渲染产物 → 从干净状态依次执行 T4 构建→T5 L2→T6→T7，核心几何顶点哈希与判据报告必须与冻结候选一致。Manifest `3d/refs/freeze_manifest.md`：facts/assumptions 快照、生成器/判据 commit 哈希、Blender 版本、参考资产哈希、容差配置、5 机位图哈希、已知偏差豁免表

- [ ] **Step 5: 向用户提交冻结包并 STOP**——用户批准后按事实覆盖度声明冻结状态：`FACTUAL_FREEZE`（本体全部关键尺寸有测绘/档案级来源）或 `CONDITIONAL_RECONSTRUCTION_FREEZE`（仍依赖工作值，逐条列出）；回填 changelog 并 Commit；未批准则按用户意见开变更记录走重跑判据流程

```bash
cd /Volumes/macstudio/video-projects
git add e30_shikongqiao_video/3d/refs
git commit -m "docs(e30): M2.5 本体冻结包(判据全绿+对叠图+已知偏差)"
```

---

## Self-Review（三轮，已执行，留痕 `3d/refs/design_audit.md`）

- **R1 几何/事实一致性**：抓到 geom 递推用 `BRIDGE_ABUT`(1.35) 而 derive 用 `BRIDGE_ABUT_TARGET`(2.00) 的断点 → Task 4 增加递推修复；facts 全部条目已带等级。
- **R2 判据有效性**：抓到 qa_l2 负控翻转发生在测量之后（负控无效）→ 改为先翻转再测；内壁法线瞄准向量存在运算符优先级 bug（会解包 tuple 崩溃）→ 重写为"拱腹面→圆心"简洁版；SPANS_MONO 原实现对右半的判断式错误 → 重写为两行 any()。
- **R3 可执行性**：Task 7 引用不存在的 `shot_side_from_ortho.png` → 改 `ortho_side.png`；AST 白名单加治理注记（尺寸禁入白名单）；测试计数复核（T1=4、T3=8）。
- **Spec 覆盖**：spec §1→T1/T2、§2 本体→T4/T6、§3 L1/L2/L3+负控→T3/T5/T7、§7 M0-M2.5→T1-T8；M3-M6 另出计划二（spec 已声明拆分）。
- **类型一致性**：`check_body(f)`/`derive(f)`、`facts.*` 常量名、`OVERLAY_IOU_MIN` 唯一定义点，均已核对。
