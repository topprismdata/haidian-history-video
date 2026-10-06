# Task 9: L5 溢出检测 Review 报告

- **审查对象**：Commit `50b4afe`（`feat(qa): L5 溢出检测`），Base: `02081a0`
- **审查输入**：
  - Brief: `/Volumes/macstudio/video-projects/.superpowers/sdd/task-9-brief.md`
  - Diff: `/Volumes/macstudio/video-projects/.superpowers/sdd/review-02081a0..50b4afe.diff`

---

## 1. Spec 合规审查

| 审查项 | 要求 | 实测/代码现状 | 结论 |
|---|---|---|:---:|
| **接口与函数** | `check_l5(page, png)`、`text_bbox_in_slot(a_g, rect)` | 完全实现，入参、出参类型与命名完全一致 | ✅ |
| **参数原样保留** | `TOUCH_MARGIN = 3`, `MIN_BLOB = 12` | 均显式声明并作为模块常量定义，值完全一致 | ✅ |
| **测试完备度** | 5 个 L5 相关测试 | 5 个测试全部追加在 `test_checks_render.py` 中 | ✅ |
| **L3 零改动约束** | L3 相关代码及测试一行不改 | 检查 diff，L3 逻辑（`check_l3`、`assert_negative_control`、`TAG_IDS`、`NEGATIVE_CONTROL_SHIFT`、`LOW_CONFIDENCE`）零修改；模块级 docstring 未改 | ✅ |
| **Remotion 隔离** | 测试不得调 Remotion | 纯 numpy 合成矩阵 + PIL 保存到 `tmp_path`，零 Remotion 依赖 | ✅ |

### 细项核验

1. **L3 零改动确认**：
   `qa_v2/checks_render.py` 原代码仅修改了顶部类型导入（追加 `Optional` 与 top-level imports），L3 相关的所有实现、常量、注释完全保持原样，没有任何非追加式逻辑修改。
2. **测试用例覆盖**：
   - `test_text_bbox_finds_centered_text`：验证居中文本外接框识别与边界内嵌。
   - `test_text_bbox_returns_none_when_blank`：验证空槽（无墨迹）返回 None。
   - `test_text_bbox_detects_touching_edge`：验证贴左边缘时判定外接矩形触边（`r[0] <= TOUCH_MARGIN`）。
   - `test_l5_ok_when_text_has_margin`：验证留有安全边距时不产生 `fail`。
   - `test_l5_fails_when_text_touches_edge`：验证文字贴边时准确命中 `TEXT_TOUCHES_SLOT_EDGE`。

---

## 2. 代码质量审查

### 2.1 核心算法顺序与有效性
`text_bbox_in_slot` 严格按 Brief 与设计原理执行：
1. **亮度二值化**：`sub < 130` 提取墨迹。
2. **形态学腐蚀**：`binary_erosion(..., iterations=1)` 消除 1px 细线描边与渐变阴影。
3. **连通域标记与面积去噪**：`label` + `sizes[i] >= MIN_BLOB (12)` 过滤细碎噪点。
4. **计算外接矩形**：基于过滤后的连通域计算 `(x, y, w, h)`。

顺序未颠倒，确保了腐蚀在连通域过滤前生效，符合物理层面对底板描边与文字笔画分离的预期。

### 2.2 坐标系修复（优秀亮点）
在 Brief 原文的伪代码中存在坐标系不一致的小矛盾：
- Brief Step 1 的 `test_text_bbox_finds_centered_text` 断言 `x > box[0]`（要求返回画布绝对坐标）。
- Brief Step 3 的 `text_bbox_in_slot` 却写了 `return (int(xs.min()), ...)`（槽内相对坐标），并在 `check_l5` 中写 `if tx <= TOUCH_MARGIN:`。

**实现者的处理**：
- `text_bbox_in_slot` 返回画布绝对坐标 `(int(x0 + xs.min()), int(y0 + ys.min()), ...)`，使 `test_text_bbox_finds_centered_text` 通过。
- 在 `check_l5` 中统一按画布坐标比对：
  - 左：`tx - rx <= TOUCH_MARGIN`
  - 上：`ty - ry <= TOUCH_MARGIN`
  - 右：`(rx + rw) - (tx + tw) <= TOUCH_MARGIN`
  - 下：`(ry + rh) - (ty + th) <= TOUCH_MARGIN`
- `Finding` 附加的 `text_rect` 与 `slot_rect` 均为统一的画布空间坐标，既修复了 Brief 的坐标矛盾，又支持了文字不仅贴边甚至溢出槽外（差值为负数）的情形判定。

### 2.3 边界与空值防御
- **越界裁剪**：`x0, y0 = max(0, x), max(0, y)` 与 `x1, y1 = min(W, x + w), min(H, y + h)`，即使槽位部分在视口外也能正确截取有效交集。
- **微小区域短路**：`x1 - x0 < 4 or y1 - y0 < 4` 直接返回 `None`。
- **空墨迹与噪点短路**：`not ink.any()`、`n == 0`、`not keep_ids`、`len(ys) == 0` 四层递进兜底，任何一层为空均安全返回 `None`。
- **空槽互斥处理**：`check_l5` 中遇到 `r is None` 执行 `continue`，不产生 `Finding`，确保空槽完全留给 L3 报告，不引发误报或双重报错。
- **色彩维度兼容**：追加了 `if sub.ndim == 3: sub = sub.mean(axis=2)` 防御逻辑，即便传入 RGB 图像也能自动转灰度处理，增强了鲁棒性。

### 2.4 合成图笔画保留验证
- `_slot_img` 模拟的字块笔画尺寸为 `(size-6) x (size-10) = 22 x 18 = 396 px`，经 1 像素腐蚀后核心依然连通且面积约 320 px，远大于 `MIN_BLOB = 12`，不会被形态学腐蚀破坏。
- `test_text_bbox_detects_touching_edge` 构造了贴近边缘 `0:20` 的墨条，腐蚀后外边缘在 x=1，小于等于 `TOUCH_MARGIN(3)`，有效验证触边检测。

### 2.5 规范与兼容性
- **Python 3.9 兼容**：全部类型注解使用 `Optional[Rect]`, `List[Finding]`, `Set[str]`，未引入 `| None` 或 `match/case` 语法。
- **Import 位置**：`qa_v2/checks_render.py` 中的所有依赖（`numpy`, `scipy.ndimage`, `PIL`, `Path` 等）均已规范提至模块顶部，函数体内无任何局部 `import`。
- **Docstring**：清晰记录了基于 E11 实测背景的底板分离原理、腐蚀 1px 消除描边阴影的原因及连通域面积过滤阈值的由来源由。

---

## 3. 分级发现 (Findings)

- **Critical**：无
- **Important**：无
- **Minor**：
  - `tests/test_checks_render.py` 中的 `import numpy as np` / `from PIL import Image` 等被追加在第 69 行（L3 测试之后、L5 测试之前），属于追加式提交风格。代码运行正常且无害，若追求纯粹的 PEP 8 代码风格，后续可在例行重构时统一并入文件头部。

---

## 4. 结论

- **Spec 合规**：✅
- **代码质量**：Approved (含 1 项 Minor 代码风格提示，无需打回)