# Task 11 审查报告：L4 内容闭环（数字严格 + 专名严格）

审查基于 commit `3a5e9d9`（diff `95b02bd..3a5e9d9`），对照需求文档 `task-11-brief.md`。

---

## 一、Spec 合规性审查

| 审查项 | 要求 | 实现情况 | 判定 |
|---|---|---|:---:|
| **接口导出** | 导出 `load_names`、`NAMES`、`check_l4a`、`check_l4b`、`UNKNOWN_RATE_WARN` | 全部按要求导出，类型注解完备，无多余或缺失符号 | ✅ |
| **阈值常量** | `UNKNOWN_RATE_WARN = 0.20` | 常量名与取值严格一致（0.20） | ✅ |
| **专名表路径** | `NAMES = pathlib.Path(__file__).with_name("names.txt")` | 严格一致 | ✅ |
| **专名表内容** | 32 项（地名/旗名/寺名/官名/园名/书名），原样照抄，禁止擅自增删 | 经逐项对比，正好 32 项，无任何擅自增删或修改 | ✅ |
| **测试完备性** | 需求 Step 5 要求 14 passed | 实现了全部 14 个测试用例（覆盖原样测试 + 3 个边界/保护测试） | ✅ |

### 专名表 32 项逐项核对

```text
树村、肖家河、蓝靛厂、圆明园、长春园、畅春园、静宜园、静明园、乐善园、广仁宫、
海甸、安河桥、镶黄旗、正白旗、正黄旗、正红旗、镶红旗、正蓝旗、镶蓝旗、镶白旗、
五圣庵、观音寺、总兵、副将、守备、护军校、参领、五城寺院册、日下旧闻考、
皇朝文献通考、竹叶亭杂记、钦定八旗通志
```
- **实际加载条目目数**：32
- **Brief 条目目数**：32
- **差异**：新增 0，缺失 0，原样录入。

---

## 二、代码质量与核心逻辑审查

### 1. 坐标换算唯一性（最易错点）
- **核查点**：`_ocr_text_for` 必须是 L4 唯一的换算点，`text_at` 内部不可再缩放。
- **核查结果**：
  1. `_ocr_text_for` 内部使用 `plate_to_canvas(page.plate, slot.x, slot.y, slot.w, slot.h)` 将槽位从板面坐标换算为画布坐标。
  2. 经查验 `qa_v2/frames.py` 中的 `text_at(ocr, rect)`，其直接使用传入的画布 `rect` 并配合 `pad=25` 与 OCR 识别框中心点比对，内部完全没有二次缩放或换算。
  3. `qa_v2/checks_content.py` 全文仅在 `_ocr_text_for` 第 69 行存在**唯一一处** `plate_to_canvas` 调用，没有第二处换算。完全合规。

### 2. 数字比对集合方向
- **核查点**：`check_l4a` 必须是 `missing = sorted(want - got)`（原文有的、读回没有的才报）。
- **核查结果**：
  ```python
  want = set(extract_numbers(item.text))
  ...
  got = set(extract_numbers(normalize_punct(got_raw)))
  ...
  missing = sorted(want - got)
  ```
  逻辑严密：只有 `want` 中存在且 `got` 中不存在的数字才会进入 `missing` 触发 `NUMBER_MISMATCH`；反向的「OCR 多读入插画杂散数字」不会误报，与 E11 实际业务场景一致。

### 3. `number_unknown_rate` 双重防线
- **核查点**：第一道防线检测归一失败率并报 `warn`（不可为 `fail`）；第二道防线严格比对数字。
- **核查结果**：
  ```python
  rate = number_unknown_rate(item.text)
  if rate > UNKNOWN_RATE_WARN:
      out.append(Finding(
          "L4-a", page.number, item.slot_id, "warn",
          "NUMBER_UNKNOWN_RATE",
          ...))

  missing = sorted(want - got)
  if missing:
      out.append(Finding(
          "L4-a", page.number, item.slot_id, "fail",
          "NUMBER_MISMATCH",
          ...))
  ```
  双重防线均存在：
  - 第一道为 `warn` 级别（归一解析不可信不等于内容必然错误，预警但不阻断）。
  - 第二道为 `fail` 级别，执行真正的缺失判定。

### 4. `check_l4b` 专名匹配
- **核查点**：原文包含专名（`n in item.text`）、专名本身过标点归一（`normalize_punct(n) not in got`）。
- **核查结果**：
  ```python
  want = [n for n in names if n in item.text]
  ...
  got = normalize_punct(_ocr_text_for(page, ocr, item.slot_id))
  missing = [n for n in want if normalize_punct(n) not in got]
  ```
  - 使用 `n in item.text` 确保是子串包含而非全等匹配。
  - 两侧均经过 `normalize_punct` 规范化，消除了书名号、标点等 OCR 识别波动对专名判定的干扰。

### 5. 专名表为空的处理（关键设计）
- **核查点**：必须报 `skip` 级 Finding，严禁静默 `pass` 或仅 `return []`。
- **核查结果**：
  ```python
  if not names:
      out.append(Finding(
          "L4-b", None, None, "skip", "NO_NAMES_TABLE",
          "专名表为空，L4-b 未执行（不算通过）。新集需维护 qa_v2/names.txt"))
      return out
  ```
  明确生成 `level="skip"`、`code="NO_NAMES_TABLE"` 的 Finding，避免新集在未配置专名表时假阳性通过。

### 6. tag 槽位过滤
- **核查点**：`check_l4a` 与 `check_l4b` 均需 `if item.is_tag: continue`。
- **核查结果**：
  - `check_l4a` 行 77: `if item.is_tag: continue`
  - `check_l4b` 行 113: `if item.is_tag: continue`
  - 并在测试用例 `test_l4a_ignores_tag_slot` 和 `test_l4b_ignores_tag_slot` 中进行了专项单测验证。

### 7. Python 3.9.6 兼容性与边界防御
- **类型系统**：严格遵守约束，使用 `Optional[pathlib.Path]` 代替 `Path | None`，无 `match/case` 语法。
- **边界鲁棒性**：
  - `load_names(path)` 兼容 `path` 为 `str`、`Path` 或 `None`。
  - `page.slot(slot_id) is None` 时，`_ocr_text_for` 安全返回 `""`，上层生成 `NUMBER_MISMATCH` / `PROPER_NAME_MISSING` 失败项，不会抛出 `AttributeError` 崩溃（见 `test_l4_handles_missing_slot_gracefully`）。
  - 原文无数字或无专名时短路 `continue`，零误报。
- **Docstring 完整性**：
  - 模块与函数 docstring 详尽说明了业务背景（E11 算术矛盾、OCR 噪声仅标点、不需要 fuzzy matching）。
  - `load_names` docstring 明确指明「空文件返回空 set —— 调用方须据此报 skip 而非 pass」。

---

## 三、审查结论

- **Spec 合规**：✅
- **代码质量**：Approved

代码实现精准对齐设计意图，尤其在坐标单点换算、专名表空表 skip 机制、双重警告防线及边界容错方面表现优秀。无阻塞性问题。
