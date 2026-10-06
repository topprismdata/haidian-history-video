# Task 1 代码审查报告：坐标换算与矩形运算

- **评审 commit**: `bfd3279`（`feat(qa): 坐标换算与矩形运算`）
- **基准 diff**: `/Volumes/macstudio/video-projects/.superpowers/sdd/review-97d9c2f..bfd3279.diff`
- **需求参考**: `/Volumes/macstudio/video-projects/.superpowers/sdd/task-1-brief.md`
- **执行环境**: Python 3.9.6 / macOS darwin arm64

---

## 1. Spec 合规审查

逐条对照 brief 中的 Interfaces 与 Acceptance 要求：

### 1.1 接口与签名（Interfaces）
- [x] **`CANVAS = (1920, 1080)`**：一致，类型与数值完全匹配。
- [x] **`Rect = Tuple[int, int, int, int]`**：一致。
- [x] **`scale_of(plate: Sequence[int]) -> Tuple[float, float, float]`**：一致，返回值 `(scale, offset_x, offset_y)` 语义一致。
- [x] **`plate_to_canvas(plate: Sequence[int], x: float, y: float, w: float, h: float) -> Rect`**：一致（brief 接口写 `Tuple[int, int, int, int]`，实现使用等价类型别名 `Rect`，一致）。
- [x] **`overlap_ratio(a: Rect, b: Rect) -> float`**：一致。
- [x] **`out_of_bounds(rect: Rect, plate: Sequence[int]) -> bool`**：一致。

### 1.2 文件清单与位置
- [x] `qa_v2/__init__.py`：已创建，为空文件，符合 brief。
- [x] `qa_v2/geometry.py`：已创建，位于根目录 `qa_v2/`。
- [x] `tests/conftest.py`：已创建，将项目根目录加入 `sys.path`。
- [x] `tests/test_geometry.py`：已创建，包含 11 个单元测试函数。
- [x] `.gitignore` 同步放行 `!/qa_v2/` 和 `!/qa_v2/**`（避免误被 git 忽略，保持仓库健康）。

### 1.3 Brief 范围外实现（YAGNI 检查）
- 无多余公共函数、无多余类、无过度工程设计。纯函数实现，依赖仅有标准库 `typing`。

### 1.4 Brief 要求但未实现项目
- 核心功能全部实现，无遗漏项。

---

## 2. 代码质量审查

### 2.1 数值阈值与实测标定
- **E11 标定参数一致性**：
  - `CANVAS = (1920, 1080)` 准确无误。
  - `scale_of((1672, 941))` 严格按照 `max(1920 / 1672, 1080 / 941)` 换算，居中 offset 公式严格吻合。
  - P5 实测锚点 `(214, 781, 505, 86)` 换算后验证 `(246, 897)` 与 `w≈580, h≈99`，与 brief 完全一致。
- **边界判定严格性**：
  - `out_of_bounds` 采用严格不等号 `x < 0 or y < 0 or x + w > plate[0] or y + h > plate[1]`，刚好贴齐右/下边缘不算越界，符合规范。

### 2.2 Python 3.9 兼容性
- [x] 没有使用 `X | None` 联合类型语法（使用 `typing.Tuple`, `Sequence`）。
- [x] 没有使用 Python 3.10 `match / case` 模式匹配。
- [x] 语法符合 Python 3.9.6 标准。

### 2.3 测试有效性与测试断言分析
审查 `tests/test_geometry.py` 中各项测试的断言质量：
- 大多数测试断言明确、数值敏感。
- **发现 1 处测试用例参数不匹配（Minor）**：
  在 `test_out_of_bounds_detects_overflow` 中：
  ```python
  # brief 写法：
  assert out_of_bounds((1672, 941, 10, 10), (1672, 941)) is False  # 实际上这个用例在 brief 中自身存在笔误或意图混乱
  ```
  实现者将其修改为：
  ```python
  assert out_of_bounds((1672, 941, 10, 10), (1920, 1080)) is False
  assert out_of_bounds((1670, 941, 10, 10), (1672, 941)) is True
  assert out_of_bounds((-1, 0, 10, 10), (1672, 941)) is True
  ```
  - **原因分析**：brief 原始第 90 行写的是 `out_of_bounds((1672, 941, 10, 10), (1672, 941)) is False`，如果 `x=1672, w=10, plate=(1672, 941)`，则 `x+w = 1682 > 1672`，按定义这明显是越界的（应该为 True），brief 原断言 `is False` 本身是有 bug 的。实现者将其 plate 改为了 `(1920, 1080)` 使得该矩形合法未越界（`1672+10=1682 <= 1920` 且 `941+10=951 <= 1080`），成功规避了 brief 原始断言的自相矛盾。这是一个合理修正。
- **死代码清理（较 brief 优化）**：
  在 `test_plate_to_canvas_never_shrinks` 中，brief 第 66 行有一行无用的死代码：
  `_, w, _ = plate_to_canvas(E11_PLATE, 0, 0, 100, 100)[1:2] + (100,)`
  实现者去除了这行无用赋值，只保留了真正的断言语句，保持了测试整洁。

### 2.4 命名与注释（Docstring）
- 模块 docstring 清晰阐述了**为什么**必须区分两套坐标空间（详细记载了旧 QA 在 E11 P5 把 1672×941 切到 1920×1080 采到香炉木架墨像素 32062 导致假阳性通过的真实事故），交代了设计根因与防退化意图。
- 提醒了 OCR 返回的坐标已在画布空间不可二次缩放的工程陷阱。
- 函数命名表达准确、自解释性强。

---

## 3. 问题分级与建议

- **Critical**: 无
- **Important**: 无
- **Minor**:
  - `tests/conftest.py` 中的注释写道 `# 让 import qa_v2.xxx 在未安装包的情况下也能工作`，修改了 brief 原始的 `import qa.xxx`，与项目改用 `qa_v2` 包名保持一致，符合实际。

---

## 4. 结论

- **Spec 合规**：✅
  - 缺项：无
  - 多余项：无（`.gitignore` 放行 `qa_v2` 为项目基础设施必要微调）
- **代码质量**：Approved
  - 针对 brief 原始测试用例中 `out_of_bounds` 矛盾断言作了正确自洽的修正；
  - 剔除了 brief 测试样例中的无用残留语句；
  - 完美兼容 Python 3.9.6；docstring 详尽记录了背景与物理意义。
