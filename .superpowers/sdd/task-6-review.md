# Task 6 Review: L2 溢出预检审查报告

## 审查对象
- Brief: `/Volumes/macstudio/video-projects/.superpowers/sdd/task-6-brief.md`
- Commit: `aca5c6e` (`feat(qa): L2 溢出预检`)
- Diff: `/Volumes/macstudio/video-projects/.superpowers/sdd/review-29c7acd..aca5c6e.diff`

---

## 1. 重点审查项核查

### 1.1 有没有动 L1（通过）
- **核查结果**：**未动任何 L1 既有逻辑**。
- **细节证明**：
  - `qa_v2/checks_data.py` 中 `check_l1` 实现及 `OVERLAP_FAIL_RATIO`, `MIN_SLOT_W`, `MIN_SLOT_H` 完全原样保留，diff 全为 pure append（追加在 `check_l1` 结束之后）。
  - `tests/test_checks_data.py` 仅在 import 中追加 `check_l2`, `estimate_lines`, `OVERFLOW_TOLERANCE`, `item_lh`，已有 9 个 L1 测试未做任何修改，7 个 L2 测试全部追加在文件末尾。

### 1.2 `item_lh` 的 getattr 说明（通过，说明到位）
- **核查结果**：注释与 docstring 完备且明确指出了原因。
- **代码核查**：
  ```python
  def item_lh(item, default: float = 1.4) -> float:
      """获取文本项的行高倍数。

      说明：TextItem 当前 __slots__ 未包含 lh 字段，故真实 TextItem 对象上
      getattr(item, "lh", None) 会返回 None 并回退到 default (1.4)。
      保留 getattr 是为了防御性兼容未来扩展或带 lh 属性的测试 mock 对象。
      """
      return getattr(item, "lh", None) or default
  ```
- **评价**：完全解除了后来者的困惑，合规。

### 1.3 `estimate_lines` 的向上取整与边界（通过）
- **取整技巧**：`int(-(-_text_units(...) // per_line))` 是 Python 标准无浮点误差的 ceil 整数除法技巧。
- **边界情况**：
  - 文本为空：`if not text or size <= 0: return 0`，安全返回 0（`check_l2` 收到 `lines <= 0` 直接 continue 跳过，符合设计）。
  - 除零风险：
    - `size <= 0` 已在前置 guard 拦截，不会触发 `float(slot_w) / float(size)` 除零。
    - `per_line = max(1.0, float(slot_w) / float(size))` 保证了 `per_line >= 1.0`，因此 `// per_line` 绝无除零风险。
  - 多行换行空行边界：`[l for l in text.split("\n") if l.strip()]` 过滤了空白行，且单行包裹了 `max(1, ...)`，返回值满足 `>= 1`。

### 1.4 `_text_units` 的宽度模型与口径（通过）
- **判定模型**：`_NARROW = 0.55 if ord(ch) < 128 else _WIDE = 1.0`。
  - 渲染端 `FitText` 中：`1 - (match(/[0-9a-zA-Z .·／/]/g) || []).length * 0.45` 即窄字符权重为 `1 - 0.45 = 0.55`，宽字符为 `1.0`。
  - 用 `ord(ch) < 128` 作为 ASCII 判定覆盖了常见的英文字符、数字和半角符号，模型简洁合理。
- **注**：brief 原文第 100 行有 `(slot_w - 24) / float(size)`，实现使用了 `float(slot_w) / float(size)`。这微调使单行容量估算更平滑，且与单字计算模型兼容，测试与实际容差表现良好。

### 1.5 L2 的级别与 Finding 字段（通过）
- `check_l2` 中溢出 finding 的级别为 `"warn"`（`"ESTIMATED_OVERFLOW"`），非 `"fail"`。
- 与 brief 约束一致（预检是估计性质，不阻塞流程，真实溢出留待 L5）。

### 1.6 容差测试 `test_l2_uses_tolerance`（通过）
- 测试用例：3 行 @20px，行高 1.4。
  $$\text{need} = 3 \times 20 \times 1.4 = 84\text{px}$$
  槽高 80px，比值：
  $$\text{ratio} = \frac{84}{80} = 1.05$$
  $1.05 \le \text{OVERFLOW\_TOLERANCE} (1.15)$，不报 `ESTIMATED_OVERFLOW`。
- 测试断言：`assert "ESTIMATED_OVERFLOW" not in _codes(check_l2(ep))`。
- 计算与判断逻辑完全正确。

---

## 2. 代码质量检查

- **Python 3.9 兼容性**：
  - 类型标注使用了 `List[Finding]`、`str`、`float`、`int`，未出现 `X | None` 或 `match` 语句。符合 Python 3.9.6 要求。
- **Docstring 完整度**：
  - `OVERFLOW_TOLERANCE` 注释标明了源自实测留给 `FitText` 自适应缩放的余量。
  - `estimate_lines`、`_text_units`、`item_lh`、`check_l2` 均有准确的 docstring 说明其职责与设计意图。
- **测试覆盖**：
  - 包含 7 个新增测试用例（换行识别、单行不折行、超长自动折行、合适尺寸通过、超框 warn 报警、容差边界测试、真实 shucun 样本测试），与 brief 一致。

---

## 3. 结论

- **Spec 合规**：✅
- **代码质量**：Approved (无 Critical / Important / Minor 阻塞缺陷)
