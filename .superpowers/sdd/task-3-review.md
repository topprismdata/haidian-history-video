# Task 3 数据加载层 审查报告

## 审查对象
- 需求规范：`/Volumes/macstudio/video-projects/.superpowers/sdd/task-3-brief.md`
- 变更范围：`qa_v2/data.py` (251 行) 与 `tests/test_data.py` (83 行)
- 提交哈希：`00fc304` (`feat(qa): 数据加载层（槽位/文案/页长/口播稿）`)

---

## 重点审查项逐项核验

### 1. `parse_pages_config` 的正则健壮性
- **转义引号 `\"` 与换行 `\n`**：
  - 正则 `_TEXT_RE = re.compile(r"text:\s*(\"(?:[^\"\\]|\\.)*\")")` 采用了互斥分支 `(?:[^\"\\]|\\.)*`，能精准匹配含转义字符的双引号字符串。
  - 后续调用 `json.loads(tm.group(1))` 进行标准反转义，正确保留 `\n` 换行符与 `\"` 双引号（在 `test_parse_pages_config_unescapes_newline` 中已通过测试）。
- **`backing: true` 与 `backing: "rgba(...)"` 形式**：
  - `_BACKING_RE = re.compile(r"backing:\s*(\"(?:[^\"\\]|\\.)*\"|true)")`。
  - 当为 `"true"` 时赋值为 `True`，当为字符串时调用 `json.loads` 解析为实际 rgba 字符串，未指定时默认 `True`，逻辑完全正确。
  - *(注：若显式配置 `backing: false` 会漏匹并走 default True，见后文 Minor 建议)*。
- **`kind: "tag"` 解析**：
  - 正则 `re.search(r"kind:\s*\"tag\"", rest)` 判定，匹配后赋 `"tag"`，否则 `None`；`TextItem.is_tag` 属性返回布尔值，符合规范。
- **作用域与块隔离**：
  - 先按 `^  (\d+):\s*\{` 切分顶层页块，防止跨页串扰；块内再提取 items。

### 2. 页长回退逻辑（三个数据源优先级与换算）
- **优先级**：严格遵循 `pageMap.ts` > `narration.json` > `narration.ts`，顺序未被颠倒。
- **换算方式**：
  1. `pageMap.ts`：读取 `PAGE_DURATIONS_SEC`，按 `round(sec * FPS)` 换算（已含 1.6s 留白）。
  2. `narration.json`：读取 `pageLenSec`，按 `round(pageLenSec * fps)` 换算。
  3. `narration.ts`：读取 `PAGE_AUDIO_SEC|AUDIO_SEC|AUDIO|DUR_SEC`，按 `round((a + 1.6) * FPS)` 换算，**严格执行了加 1.6s 留白的换算**。
- 若三者均不存在，抛出清晰异常 `SystemExit`。

### 3. `narration_text` 数据源独立性
- 仅读取 `VIDEO_ROOT / f"{ep}_video" / "narration" / "all.json"`。
- 文件不存在时直接返回空字典 `{}`。
- **绝对没有回退到 `subtitles.ts`**，彻底规避了 `subtitles.ts` 数字 token 污染（01…99 行号/下标）以及书名号简称导致的假阳性问题。

### 4. 职责边界（坐标空间隔离）
- `Slot.__init__`、`Slot.rect` 直接存储并返回整数矩形元组 `(x, y, w, h)`。
- `load_episode` 直接读取 `slots.json` 中的原始板面数据并赋给 `Slot` 与 `Page.plate`。
- **数据加载层没有任何对画布（1920×1080）的缩放与平移计算**，完全留在板面空间，换算职责纯净地留给 Task 1 的 `qa_v2.geometry` 模块。

### 5. 标定断言
- `tests/test_data.py` 中的关键标定断言原样保留：
  - `n_slots = sum(len(p.slots) for p in ep.pages)`
  - `n_items = sum(len(p.items) for p in ep.pages)`
  - `assert n_slots == 93` 与 `assert n_items == 93` 未被改小或降级。
  - E11 树村实测 8 页、首页 plate `(1672, 941)` 断言完整保留。

---

## 详细审查分析

### 1. Spec 合规性审查
- **类与方法签名**：
  - `Slot`：具备 `id`, `x`, `y`, `w`, `h` 属性、`__slots__` 及 `rect` 属性。
  - `TextItem`：具备 `slot_id`, `text`, `size`, `backing`, `kind` 属性、`__slots__` 及 `is_tag` 属性。
  - `Page`：具备 `number`, `plate`, `slots`, `items` 属性及 `slot(sid)` 查找方法。
  - `Episode`：具备 `name`, `pages`, `layout` 属性及 `page(num)`, `final_frame(num)` 方法。
  - 模块级导出：`ROOT`, `load_episode`, `parse_pages_config`, `narration_text` 全部到位。
- **测试覆盖度**：
  - Brief 所列 9 个测试用例全部原样实现，覆盖了基本解析、换行反转义、rgba 背景、默认字号、页数与尺寸、累加布局、93 槽位/文案标定、口播稿解析、缺失兜底。
- **YAGNI 违规检查**：
  - 无多余抽象，无冗余配置，数据模型轻量干净（使用 `__slots__` 优化内存与属性访问），无过早泛化。

### 2. 代码质量审查
- **Python 3.9 兼容性**：
  - 100% 遵照 Python 3.9.6 标准：使用 `typing.Optional`, `typing.List`, `typing.Tuple`, `typing.Dict`, `typing.Any`。
  - 无 PEP 604 联合类型（无 `X | None`），无 `match` 语法，类显式继承 `object`。
- **正则灾难性回溯（ReDoS）评估**：
  - `_ITEM_RE`：使用否定字符集 `[^\"]+` 与 `[^}]*`，前后有明确分隔界限，无嵌套量词。
  - `_TEXT_RE`：`(?:[^\"\\]|\\.)*` 中两个子分支字符集互斥（一个不含反斜杠与引号，一个以反斜杠开头），回溯树确定，无 ReDoS 风险。
  - `_BACKING_RE`、`_NUMS`、`_page_layout` 等正则均无重叠贪婪量词，不存在灾难性回溯风险。
- **文档与注释（为什么 / 意图）**：
  - Docstring 详尽记载了设计背景：
    - `Episode.final_frame` 说明了为何取尾部前 3 帧（避免 E11 P3 中途帧只填 3 行误报渲染缺失的坑）。
    - `_page_layout` 明确记录了 E9 累积到 P4 差 144 帧的教训，说明了 `pageMap > narration.json` 不可反。
    - `narration_text` 清晰阐述了不读 `subtitles.ts` 的两条实测经验（下标/行号污染与简称差异）。

### 3. 改进建议（非阻塞，供后续参考）

- **[Minor] `backing: false` 支持**：
  当前 `_BACKING_RE` 仅匹配 `true` 或字符串，若未来文案中显式写 `backing: false`，会无法匹配而走 `else: backing = True`。建议后续可优化为匹配 `true|false`。
- **[Minor] TypeScript 注释剔除**：
  `parse_pages_config` 在解析 `body` 时直接通过 `_ITEM_RE.finditer(body)` 提取。如果开发人员在 `items: [...]` 数组中临时用 `// { slotId: ... }` 注释掉某项，当前正则仍会提取该项。建议在 `for im in _ITEM_RE.finditer(...)` 前，可类似 `_nums` 先剔除行注释与块注释。
- **[Minor] `narration_text` 参数 `root`**：
  `narration_text(ep: str, root: Optional[pathlib.Path] = None)` 保留了 `root` 参数以兼容 brief 签名，但内部固定从 `VIDEO_ROOT`（`/Volumes/macstudio/video-projects`）加载。可在 docstring 中补充一句说明此口播稿统一归档在 `VIDEO_ROOT`。

---

## 结论

- **Spec 合规**：✅
- **代码质量**：Approved (全部重点审查项及格，3 项 Minor 建议供后续演进参考，无 Critical/Important 缺陷)
