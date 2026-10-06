# Task 12「L4-c 口播稿交叉」审查报告

## 审查结论

- **Spec 合规**：✅
- **代码质量**：Approved

---

## 1. 重点审查项逐项核验

### 1.1 是否动过 L4-a / L4-b 及已有常量
- **核验结果**：**未动任何已有实现**（纯追加）。
- **核验细节**：
  - `qa_v2/checks_content.py` 中仅在 imports 追加了 `Dict` 与 `Episode`，`NAMES`、`UNKNOWN_RATE_WARN`、`load_names`、`_ocr_text_for`、`check_l4a`、`check_l4b`、`names.txt` 均原样保留，无任何修改。
  - `tests/test_checks_content.py` 仅在 import 中追加 `check_l4c`，所有原有的 14 个测试用例未被触碰。

### 1.2 `_is_volume_ref` 判据与局限性说明
- **核验结果**：**完全符合要求**。
- **核验细节**：
  - 判据为 `1 <= n <= 200`，未被擅自“优化”为具体卷号白名单。
  - docstring 中明确写明局限性：
    > 局限性说明：粗启发式，会漏掉小数值的内容数字；只在数字量级明显是卷号时才可靠。例如房数（65）、人数等小数字若口播漏念也会被豁免，这是已知假阳性/假阴性来源。不改成具体卷号白名单是为了保持跨集泛化性。
  - 符合口头指示与工程决策约束。

### 1.3 `NO_NARRATION` 是否为 skip 级别
- **核验结果**：**是**。
- **核验细节**：
  ```python
  if not narration:
      out.append(Finding(
          "L4-c", None, None, "skip", "NO_NARRATION",
          "找不到 %s_video/narration/all.json，L4-c 未执行（不算通过）"
          % ep.name))
      return out
  ```
  没有静默返回 `[]`，而是产出 `level="skip"`、`code="NO_NARRATION"` 的 Finding 后 return。

### 1.4 `narration` 获取逻辑与动态挂载说明
- **核验结果**：**逻辑严谨，注释完备**。
- **核验细节**：
  - 代码通过 `narration = getattr(ep, "narration", None)` 取属性，若为 `None` 则从 `narration_text(ep.name)` 读取。
  - 带有明确注释：
    > Episode 类本身没有 narration 属性；测试中通过 ep.narration = {...} 动态挂载，真实运行走 narration_text(ep.name) 从 narration/all.json 读。
  - 既兼顾了单元测试时注入假数据的便利，又保障了真实运行时从 `narration/all.json` 读取。

### 1.5 tag 槽跳过
- **核验结果**：**已正确跳过**。
- **核验细节**：
  在遍历 `page.items` 时，首先检查 `if item.is_tag: continue`，避免证据标签/元数据槽中的数字参与交叉校验。

### 1.6 跨页匹配限制
- **核验结果**：**页面严格隔离，无跨页泄漏**。
- **核验细节**：
  - 遍历 `ep.pages` 时，每一页独立获取该页口播 `spoken = narration.get(page.number)`，并从中提取 `spoken_nums = set(extract_numbers(spoken))`。
  - 槽内数字 `missing` 的比对范围仅针对当前页的 `spoken_nums`，杜绝了全集全局匹配导致漏检的问题。

---

## 2. Spec 合规性详细审查

1. **接口与签名**：
   - 函数定义 `check_l4c(ep: Episode, ocr_by_page: Dict[int, OcrResult]) -> List[Finding]` 与 Spec/Brief 完全一致。
   - `_is_volume_ref(n: int) -> bool` 与 Spec 一致。
2. **测试用例完备性**：
   - `test_l4c_skips_when_narration_missing`：验证口播缺失时产出 `NO_NARRATION` skip Finding。
   - `test_l4c_passes_when_number_in_narration`：验证文案与口播数字吻合且卷号（116）被豁免时无 fail。
   - `test_l4c_flags_number_absent_from_narration`：验证口播缺少文案数字时精准拦截报 `NUMBER_NOT_IN_NARRATION` fail。
   - 3 个新增测试均已落实。

---

## 3. 代码质量审查

1. **Python 3.9 兼容性**：
   - 类型注解使用 `typing.Dict, List, Optional, Set`，未使用 `X | Y` 联合类型语法。
   - 无 `match` 语句。
   - 完全兼容 Python 3.9.6。
2. **文档与设计意图**：
   - 完整阐述了只认 `narration/all.json`、不认 `subtitles.ts` 的实测原因（数组下标污染与简称省略）。
   - 解释了为什么 L4-c 是三路交叉中最弱的一路（口播与文案叙述允许不一致，仅抓数字）。
   - 明确标注了 `_is_volume_ref` 的局限性与设计权衡。
3. **边界条件处理**：
   - 某页无口播稿（`spoken` 为空）：安全 `continue`，不崩溃。
   - 该页无数字或槽位无数字：安全判空跳过。
   - `_ocr_by_page` 中未使用的 `ocr` 参数预留规范（满足接口一致性）。

---

## 结论汇总

- **Spec 合规**：✅
- **代码质量**：Approved (无 Critical / Important / Minor 问题)
