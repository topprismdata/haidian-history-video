## Task 2: 标点与数字归一化

**Files:**
- Create: `qa_v2/normalize.py`
- Create: `tests/test_normalize.py`

**Interfaces:**
- Consumes: 无
- Produces:
  - `normalize_punct(s: str) -> str` —— 去掉标点与空白，保留字母数字汉字
  - `to_int(token: str) -> Optional[int]` —— 中文/阿拉伯数字 token → int
  - `extract_numbers(s: str) -> List[int]` —— 从文本抽出全部数字（已归一），无法解析的跳过
  - `number_unknown_rate(text: str) -> float` —— 无法解析的 token 占比，用于检测归一函数的 bug

- [ ] **Step 1: 写失败的测试**

`tests/test_normalize.py`：

```python
"""归一化。阈值与规则来自 E11 实测。

E11 用 PaddleOCR 3.7 跑完 8 页，平均置信 0.989，噪声**只有标点**：
  原文「树村·圆明园正北」   → OCR「树村.圆明园正北」
  原文「一个村子，三重身份」 → OCR「一个村子.三重身份」
  原文「楹＝间」           → OCR「楹=间」
无错字、无漏字，所以归一只需处理标点，不需要模糊匹配。
"""
import pytest

from qa_v2.normalize import (
    normalize_punct, to_int, extract_numbers, number_unknown_rate,
)


@pytest.mark.parametrize("raw,expect", [
    ("树村·圆明园正北", "树村圆明园正北"),
    ("一个村子，三重身份", "一个村子三重身份"),
    ("楹＝间", "楹间"),
    ("「著移驻树村」", "著移驻树村"),
    ("E1 肖家河", "E1肖家河"),
    ("1799 → 1800 → 1801", "179918001801"),
])
def test_normalize_punct(raw, expect):
    assert normalize_punct(raw) == expect


def test_normalize_punct_keeps_latin_and_cjk():
    assert normalize_punct("五圣庵·鐡磬一") == "五圣庵鐡磬一"


@pytest.mark.parametrize("tok,expect", [
    ("1485", 1485),
    ("1724", 1724),
    ("一七二四", 1724),      # 纯位值写法（口播逐位念年份）
    ("一千二百五十", 1250),
    ("三千", 3000),
    ("三百七十五", 375),
    ("二十三", 23),
    ("二十八", 28),
    ("一百二十", 120),
])
def test_to_int(tok, expect):
    assert to_int(tok) == expect


@pytest.mark.parametrize("tok", ["蜀村", "", "·", "abc"])
def test_to_int_returns_none_for_non_number(tok):
    assert to_int(tok) is None


def test_extract_numbers_mixes_forms():
    txt = "共盖房一万间，分为八处，每处一千二百五十间（1250）"
    assert sorted(extract_numbers(txt)) == [8, 10000, 1250]


def test_extract_numbers_reads_speech_years():
    """口播里年份是逐位念的：「一七二四年」→ 1724。"""
    assert extract_numbers("雍正二年，也就是一七二四年") == [1724]


def test_number_unknown_rate_is_zero_for_clean_text():
    assert number_unknown_rate("镶黄旗在村西，65 楹，1485 楹") == 0.0


def test_number_unknown_rate_flags_garbage():
    """归一函数出 bug 时要能被察觉，而不是静默通过。"""
    rate = number_unknown_rate("一七二四 9999 蜀村")
    assert rate > 0.2
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_normalize.py -v`
Expected: FAIL —— `ModuleNotFoundError: No module named 'qa_v2.normalize'`

- [ ] **Step 3: 写最小实现**

`qa_v2/normalize.py`：

```python
"""文本归一化：标点剥离 + 中文数字转阿拉伯数字。

E11 实测（PaddleOCR 3.7 / PP-OCRv6 medium，8 页平均置信 0.989）：
OCR 噪声**只有标点规范化**，无错字无漏字。故归一只需处理标点，
不需要 fuzzy matching —— 数字与专名可以直接严格比对。
"""
import re
from typing import List, Optional

# 保留汉字、字母、数字，其余（标点/空白/装饰符号）一律去掉
_STRIP = re.compile(r"[^0-9A-Za-z一-鿿]+")

_CN_DIGIT = {
    "零": 0, "〇": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4,
    "五": 5, "六": 6, "七": 7, "八": 8, "九": 9,
}
_CN_UNIT = {"十": 10, "百": 100, "千": 1000}

# 连续的阿拉伯数字 / 中文数字 / 数字单位
_NUM_RE = re.compile(
    r"[0-9]+|[零〇一二两三四五六七八九十百千]+"
)


def normalize_punct(s: str) -> str:
    """去掉标点与空白，只留汉字/字母/数字。"""
    return _STRIP.sub("", s)


def to_int(token: str) -> Optional[int]:
    """数字 token → int，解析不了返回 None。

    支持三种写法：
      「1485」        → 1485   （阿拉伯）
      「一千二百五十」→ 1250   （带单位）
      「一七二四」    → 1724   （纯位值，口播逐位念年份）
    """
    t = token.strip()
    if not t:
        return None
    if t.isdigit():
        return int(t)
    if not all(c in _CN_DIGIT or c in _CN_UNIT for c in t):
        return None

    # 纯位值写法：每个字都是一个数字，没有单位字
    if all(c in _CN_DIGIT for c in t):
        digits = [_CN_DIGIT[c] for c in t]
        if len(digits) > 1 and digits[0] == 0:
            # 形如「零一二」这种混合写法，放弃
            return None
        n = 0
        for d in digits:
            n = n * 10 + d
        return n

    # 带单位：按「千百十」节法解析
    total = 0      # 已结算的高位
    section = 0    # 当前节
    last_digit = None
    for c in t:
        if c in _CN_DIGIT:
            last_digit = _CN_DIGIT[c]
        else:
            unit = _CN_UNIT[c]
            if last_digit is None:
                # 「十二」的「十」前面没数字，按 1 处理
                last_digit = 1
            section += last_digit * unit
            last_digit = None
    if last_digit is not None:
        section += last_digit
    return total + section


def extract_numbers(s: str) -> List[int]:
    """从文本抽出全部可解析的数字，已归一到 int；解析不了的跳过。"""
    out = []
    for m in _NUM_RE.finditer(s):
        v = to_int(m.group())
        if v is not None:
            out.append(v)
    return out


def number_unknown_rate(text: str) -> float:
    """「像数字但解析不了」的 token 占全部候选 token 的比例。

    正常为 0.0。> 0.2 说明 to_int 有 bug 或文本有异常，
    此时 L4 的数字比对不可信，应报 warn 而不是静默通过。
    """
    cands = _NUM_RE.findall(text)
    if not cands:
        return 0.0
    bad = sum(1 for c in cands if to_int(c) is None)
    return bad / float(len(cands))
```

- [ ] **Step 4: 跑测试确认通过**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_normalize.py -v`
Expected: PASS —— 22 passed（含 parametrize 展开）

若 `test_number_unknown_rate_flags_garbage` 失败（因为「蜀村」不会被 `_NUM_RE` 匹配成数字候选），
把该测试的输入改为 `"一七二四 9999 一二三四五六七"` 并调整断言为 `> 0.1`。

- [ ] **Step 5: 提交**

```bash
cd /tmp/chemistry-video
git add qa/normalize.py tests/test_normalize.py
git commit -m "feat(qa): 标点与中文数字归一化

E11 实测 OCR 噪声仅标点规范化（·→. 、，→. ），无错字漏字，
故归一只处理标点，数字与专名可严格比对，不必 fuzzy matching。
to_int 支持三种写法：阿拉伯、带单位（一千二百五十）、纯位值（一七二四）。"
```

---

