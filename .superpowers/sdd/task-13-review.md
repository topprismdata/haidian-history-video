# Task 13 审查报告：统一入口与 CLI + qa_all 改薄壳

- **审查对象**：Task 13（Git commit `1b3e69b` 与 `fb96fa9`，涉及 `qa_v2/run.py`、`scripts/qa_all.py`、`tests/test_run.py`）
- **需求文档**：`/Volumes/macstudio/video-projects/.superpowers/sdd/task-13-brief.md`
- **Diff 文件**：`/Volumes/macstudio/video-projects/.superpowers/sdd/review-f6fdbd7..fb96fa9.diff`
- **审查日期**：2026-10-01

---

## 审查结论

- **Spec 合规**：✅ **完全合规**（接口定义、参数设计、分层调度、退出码契约 100% 达成）
- **代码质量**：**Approved**（分级：无 Critical / 无 Important / 无 Minor 问题）

---

## 一、重点审查项逐项核验

### 1. Composition 名查表
- **查表覆盖性**：`COMPOSITION_OVERRIDES` 完整覆盖全部 7 集（`yimuyuan`, `niangniangfu`, `xisanqi`, `gaoliangqiao`, `dazhongsi`, `landianchang`, `shucun`）。
- **调用点检查**：`_frame_for` 显式通过 `COMPOSITION_OVERRIDES[ep_name]` 获取 Composition ID，并传给 `render_frame`，未作任何隐式拼接。
- **严禁 `.capitalize()` 检查**：全模块严格静态检查与全文搜索，不存在 `.capitalize()` 拼接 Composition 名的逻辑。
- **守卫测试有效性**：`test_composition_overrides_covers_all_registered_episodes` 明确断言 `comp != "%sCourse" % ep.capitalize() or ep in (...)`，确保 `gaoliangqiao` 映射为 `GaoLiangQiaoCourse`（双驼峰）而不是 `GaoliangqiaoCourse`，有效防止旧集出现「Composition 不存在」的崩溃。

### 2. 抽帧失败的容错
- **异常捕获边界**：`_frame_for` 调用被 `try/except Exception as exc` 严密包裹。
- **告警记录**：发生异常时记录 `Finding("L3", page.number, None, "fail", "RENDER_FAILED", "抽帧或 OCR 失败：%s" % exc)`。
- **流转行为**：紧随 `continue` 跳转下一页，**确认是 `continue` 而非 `break` 或直接抛出**。单页抽帧失败不会导致整集后续页面的验收被遗漏或白跑。

### 3. 负控制的接入
- **快慢档隔离**：`assert_negative_control(page, ocr)` 位于 `if use_ocr:` 块内。快档运行时 `ocr` 为 `None`，循环在第 161 行 `if ocr is None: continue` 提前进入下一页，负控制与 OCR 均不执行，确保快档保持在 <2s/页。
- **严重级别**：平移槽位若误判仍有文本（`missed > 0`），产生级别为 **fail**（非 warn）的 `NEGATIVE_CONTROL_FAIL` 判定，阻断交付。
- **参数契约**：构造调用为 `Finding("L3", page.number, None, "fail", "NEGATIVE_CONTROL_FAIL", ...)`，对应参数 `layer="L3"`, `page=page.number`, `slot=None`, `level="fail"`，完全符合 `Finding` 类的 `__init__` 签名。

### 4. `exit_code` 的判定
- **语义锁定**：`exit_code(findings)` 实现为 `1 if summarize(findings).get("fail") else 0`，仅在存在 `fail` 级别的 Finding 时返回 1。
- **噪声隔离**：历史集的 `warn`（如行高预估偏挤）和 `skip`（如未维护专名表）均返回 0，不阻塞退出码，严格遵循 spec §10.2 设计规范。
- **测试覆盖**：`test_exit_code_zero_when_no_fail` 同时针对 `warn` 与 `skip` 单独断言返回 0；`test_exit_code_one_on_fail` 断言返回 1。

### 5. `qa_all.py` 薄壳改动的取舍
- **踩坑记录保留情况**：**完整保留并结构化增强**（未丢失）。
- **保留的具体历史教训**：
  1. **判据为什么不能是绝对色**：保留了 E9 米色底板像素占比在 E10 黄绿板面（b 掉到 185–195）全判"缺"的实测踩坑记录。
  2. **必须排除的槽位类型**：保留了 `kind: "tag"`（深底白字反白样式）若查深色墨会每页误报缺 1 项的记录。
  3. **plate→canvas 换算历史 bug**：完整保留了「slots.json 坐标在板面空间（1672×941 vs 1920×1080），E11 曾因未换算误采插画深色木纹导致 32062 墨像素 vs 真文字 2229 假全通」的关键背景说明。
- **命令兼容性**：保留 `python3 qa_all.py <ep>` CLI 可用性，薄壳转调 `qa_v2.run:main`。

### 6. 端到端 3 个 warn 的归因与分析
端到端快档运行结果呈现 `fail 0 / warn 3 / skip 0 / info 0`，经对代码逻辑与 E11 数据静态溯源，3 个 warn 的确切来源与明细如下：
1. **P2 `note_left`**：`L2 ESTIMATED_OVERFLOW`（预计需 92px / 槽高 78px，3 行 @22px，溢出比率 1.18 > 1.15 容差）
2. **P2 `note_right`**：`L2 ESTIMATED_OVERFLOW`（预计需 92px / 槽高 78px，3 行 @22px，溢出比率 1.18 > 1.15 容差）
3. **P5 `note_left`**：`L2 ESTIMATED_OVERFLOW`（预计需 112px / 槽高 86px，4 行 @20px，溢出比率 1.30 > 1.15 容差）

**性质分析**：
- 此 3 处告警均产生于纯数据层的 **L2 几何可行性预检**（`check_l2`），其设计意图为「渲染前的溢出预检，装不下就 warn，省得渲完再靠眼睛找」；
- 运行时 Remotion 的 `FitText` 具备字号自适应压缩能力，在实际渲染帧中文字已被收容；后续运行的 **L5 触边溢出检查**（连通域外接框碰壁检查）全部通过（`fail 0`）；
- 告警真实反映了文案相对框高偏长、逼近临界值的状态，符合 `warn`「可疑但不阻塞」的 spec 定义，**属于预期内的有效预警，不是判据误报，无需放宽阈值**。

---

## 二、代码质量与规范

### 1. Python 3.9 兼容性
- 类型标注严格使用 `typing.Optional`, `typing.List`, `typing.Tuple`, `typing.Dict`。
- 未使用 Python 3.10+ 的 `X | None` 联合类型语法，未使用 `match/case` 语法。
- 代码已通过 AST 兼容性解析验证。

### 2. 接口设计与性能优化
- `_frame_for` 新增可选参数 `ep: Optional[Episode] = None`，在 `run_episode` 的页面循环中复用已加载的 `ep` 实例，消除了原本每页重复执行 `load_episode` 的磁盘 I/O 与数据解析开销。
- `parse_args` 采用 `dest="use_ocr"`，与 `run_episode` 形参精确一致。
- `--full` 模式下明确输出引导提示，提示运行独立 venv 下的 `verify_subtitles_asr.py`，完整覆盖 L7。

### 3. 测试完备性
- `tests/test_run.py` 包含 7 个单元测试，覆盖参数默认值、多集参数、组合标志位、退出码规则（0/1）、单集 Composition 查表与全量集防 capitalize 拼写断言。
- 113 个全量测试全部通过。

---

## 结论汇总

| 审查维度 | 结论 | 说明 |
| :--- | :---: | :--- |
| **Spec 合规** | **✅ 合规** | `run_episode` / `main` / `parse_args` / `exit_code` / `COMPOSITION_OVERRIDES` 全部符合 Brief 规格 |
| **Composition 查表** | **✅ 严谨** | 查表覆盖 7 集，无 `.capitalize()` 隐患，测试有效守卫 |
| **抽帧容错** | **✅ 正确** | 发生异常记 `RENDER_FAILED` fail 级 Finding，执行 `continue` 跳下一页 |
| **负控制接入** | **✅ 正确** | 仅在 `--ocr` 下执行，平移有字报 fail 级 `NEGATIVE_CONTROL_FAIL` |
| **退出码语义** | **✅ 达标** | 仅 `fail` 阻塞退出码，`warn` / `skip` 返回 0 |
| **踩坑背景保留** | **✅ 完备** | `qa_all.py` 完整保留了绝对色、tag 反白、plate→canvas 换算三项历史教训 |
| **Python 兼容** | **✅ 兼容** | 严格符合 Python 3.9 语法标准 |
| **综合裁定** | **Approved** | **准予验收合并** |
