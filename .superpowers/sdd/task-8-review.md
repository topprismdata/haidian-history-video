# Task 8 审查报告：L3 渲染存在性 + 负控制

- **审查对象**：Commit `fb64bf0` (`qa_v2/checks_render.py`, `tests/test_checks_render.py`)
- **审查输入**：`task-8-brief.md` 与 `review-1428f66..fb64bf0.diff`
- **审查日期**：2026-10-01

---

## 一、Spec 合规性审查

| 审查项 | 要求 | 实际实现 | 判定 |
|---|---|---|:---:|
| 导出接口 | `check_l3`, `assert_negative_control`, `NEGATIVE_CONTROL_SHIFT`, `LOW_CONFIDENCE`, `TAG_IDS` | 5 个接口/常量均已正确导出且签名完全一致 | ✅ |
| 阈值定义 | `NEGATIVE_CONTROL_SHIFT = 300`<br>`LOW_CONFIDENCE = 0.80` | `NEGATIVE_CONTROL_SHIFT: int = 300`<br>`LOW_CONFIDENCE: float = 0.80` 原样定义 | ✅ |
| 负控制平移拒绝 | `shift <= 0` 必须抛出 `AssertionError` | `assert shift > 0, "负控制的平移量必须 > 0，否则等于没验证"` | ✅ |
| 测试用例数量 | 6 个测试全部覆盖规定场景 | 6 个用例均实现：<br>1. `test_l3_passes_when_text_present`<br>2. `test_l3_fails_when_slot_empty`<br>3. `test_l3_ignores_tag_slot`<br>4. `test_l3_reports_low_confidence_as_warn`<br>5. `test_negative_control_passes_when_shifted_slot_is_empty`<br>6. `test_negative_control_detects_always_true_detector` | ✅ |
| 测试纪律 | 禁止真实加载 PaddleOCR 或 Remotion 渲染，全量使用合成 `OcrResult` | 全部使用合成 `OcrResult` 与内存 `_page` 构造数据，零外部重型依赖，执行毫秒级 | ✅ |
| YAGNI 违规检查 | 不提前占位 Task 9 (L5) / Task 10 (L6) | 代码中仅实现 L3 与负控制逻辑，无任何未实现的占位桩函数（无 `check_l5` / `check_l6` 存根） | ✅ |

**Spec 合规结论**：✅ **完全合规**

---

## 二、代码质量与核心约束审查

### 1. 坐标换算唯一性（最易错点）
- **板面到画布换算位置**：
  - `check_l3` 中：仅通过 `rect = plate_to_canvas(page.plate, s.x, s.y, s.w, s.h)` 换算一次槽位坐标至画布坐标。
  - `assert_negative_control` 中：仅通过 `rect = plate_to_canvas(page.plate, moved.x, moved.y, moved.w, moved.h)` 换算一次。
- **`text_at` 内部行为**：
  - `text_at` 仅接受 `canvas` 空间的 `Rect`，内部只解构 `rx, ry, rw, rh` 并判断 OCR box 中心点 `cx, cy` 是否在 `[rx - pad, rx + rw + pad]` 和 `[ry - pad, ry + rh + pad]` 内，只做 `(x1, y1, x2 - x1, y2 - y1)` 几何格式转换，**没有任何坐标缩放逻辑**。
- **结论**：全文及调用链**无二次缩放**，严格遵守「两套坐标空间（槽位=板面空间，OCR box=画布空间）」的原则。

### 2. 负控制入参污染防护
- 在 `assert_negative_control` 中：
  ```python
  moved = Slot(s.id, s.x + shift, s.y, s.w, s.h)
  ```
  构造了独立的局部 `Slot` 对象，**没有**对入参 `page.slots` 中的对象执行 `s.x += shift` 破坏性修改，保证了 `Page` 实例在多遍检查中的幂等性与可复用性。

### 3. TAG_IDS 双处过滤
- `check_l3`：
  ```python
  if s.id in TAG_IDS:
      continue  # 深底白字，交给 L6
  ```
- `assert_negative_control`：
  ```python
  if s.id in TAG_IDS:
      continue
  ```
- **结论**：两处均正确跳过深底白字的 tag 槽，避免负控制将其误算入未命中槽位数中。

### 4. 置信度判断对象
- 提取逻辑：
  ```python
  worst = min(f[2] for f in found)
  if worst < LOW_CONFIDENCE:
      ...
  ```
- **结论**：严格采用槽内 OCR 文本片段的**最低置信度** (`min`)，而非平均或最高置信度。符合「只要有一行字被裁切识别不清就应告警」的设计初衷。

### 5. Python 3.9.6 兼容性
- 严格使用 `from typing import List, Set` 等泛型类型注解。
- 无 `X | None` 联合类型语法（PEP 604）。
- 无 `match / case` 模式匹配语法（Python 3.10+）。
- 兼容性检查 100% 通过。

### 6. Docstring 与实测依据说明
- 模块级文档清晰记录了核心原理：「为什么弃用深色像素判定（E11 负控制实测空白区 583 墨像素误判通过）」。
- 阈值注释明确阐述了实测背景：
  - `NEGATIVE_CONTROL_SHIFT = 300`：超过任何板面的标题带高度，确保不会平移落入邻近有效槽。
  - `LOW_CONFIDENCE = 0.80`：依据 E11 实测数据（正向文本最低 0.828，插画篆书 0.350）。
- `assert_negative_control` 明确阐述了「证明判据非恒真」的科学价值。

---

## 三、审查发现与分级

- **Critical（阻断性缺陷）**：无。
- **Important（重要缺陷）**：无。
- **Minor（代码异味/注释瑕疵）**：
  - `qa_v2/checks_render.py` 第 1 行 docstring 写有：`"""L3 渲染存在性、L5 溢出、L6 tag 槽。需渲染帧，不用 OCR（L6 除外）。"""`。
    - **说明**：L3 实际核心正是依赖 OCR 文本做存在性校验（`OcrResult` + `text_at`）。此句属于前期架构草稿的描述残留（原意指 L5 溢出不用 OCR），不影响任何逻辑运行，后续 Task 9/10 丰富该模块时可顺手微调润色。

---

## 四、最终结论

- **Spec 合规**：✅
- **代码质量**：**Approved**（零阻断问题，工程质量扎实，边界防御严密）
