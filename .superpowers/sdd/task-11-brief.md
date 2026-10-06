## Task 11: L4 内容闭环 —— 数字严格

**Files:**
- Create: `qa_v2/names.txt`
- Create: `qa_v2/checks_content.py`
- Create: `tests/test_checks_content.py`

**Interfaces:**
- Consumes: `qa_v2/normalize.py`、`qa_v2/frames.py`、`qa_v2/data.py`、`qa_v2/geometry.py`、`qa_v2/report.py`
- Produces:
  - `load_names(path: Path = NAMES) -> Set[str]` —— 读专名表
  - `NAMES = Path(__file__).with_name("names.txt")`
  - `check_l4a(page: Page, ocr: OcrResult) -> List[Finding]` —— 数字严格
  - `check_l4b(page: Page, ocr: OcrResult, names: Set[str]) -> List[Finding]` —— 专名严格
  - `UNKNOWN_RATE_WARN = 0.20`

- [ ] **Step 1: 写失败的测试**

`tests/test_checks_content.py`：

```python
"""L4 内容闭环：槽里的字，对不对。

这是旧 QA 完全做不到的一层。E11 真实发生过的错：
P8 口播写「各占了一处」后又说树村占两处，算术自相矛盾 ——
深色墨判据对此毫无察觉。
"""
import pytest

from qa_v2.data import Page, Slot, TextItem
from qa_v2.frames import OcrResult
from qa_v2.checks_content import check_l4a, check_l4b, load_names

PLATE = (1920, 1080)


def _page(items, number=1):
    slots = [Slot(i.slot_id, 0, 0, 900, 120) for i in items]
    return Page(number, PLATE, slots, items)


def _ti(sid, text, size=20):
    return TextItem(sid, text, size, True, None)


def _ocr(page, mapping):
    """按 slotId -> 读回文本 构造 OcrResult（box 落在槽内）。"""
    texts, boxes, scores = [], [], []
    for k, v in mapping.items():
        for t in v:
            texts.append(t)
            boxes.append((10, 10, 400, 50))
            scores.append(0.99)
    return OcrResult(texts, boxes, scores)


# ── L4-a 数字 ──
def test_l4a_passes_when_numbers_match():
    p = _page([_ti("r1_total", "1550")])
    assert [f for f in check_l4a(p, _ocr(p, {"r1_total": ["1550"]}))
            if f.level == "fail"] == []


def test_l4a_catches_wrong_number():
    """「1485」写成「1486」—— 深色墨判据查不出，这里能查出。"""
    p = _page([_ti("r1_total", "1485")])
    fs = [f for f in check_l4a(p, _ocr(p, {"r1_total": ["1486"]}))
          if f.level == "fail"]
    assert len(fs) == 1 and fs[0].code == "NUMBER_MISMATCH"


def test_l4a_accepts_chinese_numeral():
    p = _page([_ti("note", "一千二百五十间")])
    assert [f for f in check_l4a(p, _ocr(p, {"note": ["1250 间"]}))
            if f.level == "fail"] == []


def test_l4a_accepts_speech_year():
    p = _page([_ti("sub", "雍正二年（1724）")])
    assert [f for f in check_l4a(p, _ocr(p, {"sub": ["一七二四年"]}))
            if f.level == "fail"] == []


def test_l4a_ignores_punctuation_only_diff():
    """E11 实测：OCR 噪声仅标点规范化。"""
    p = _page([_ti("sub", "树村·圆明园正北")])
    assert [f for f in check_l4a(p, _ocr(p, {"sub": ["树村.圆明园正北"]}))
            if f.level == "fail"] == []


def test_l4a_no_numbers_is_trivially_ok():
    p = _page([_ti("title", "一个村子，三重身份")])
    assert [f for f in check_l4a(p, _ocr(p, {"title": ["一个村子，三重身份"]}))
            if f.level == "fail"] == []


def test_l4a_warns_on_high_unknown_rate():
    p = _page([_ti("x", "一七二四 9999 一二三四五六七")])
    fs = [f for f in check_l4a(p, _ocr(p, {"x": ["一七二四 9999 一二三四五六七"]}))
          if f.code == "NUMBER_UNKNOWN_RATE"]
    assert len(fs) == 1 and fs[0].level == "warn"


# ── L4-b 专名 ──
def test_l4b_passes_when_name_present():
    p = _page([_ti("dir", "树村西")])
    names = {"树村", "肖家河", "蓝靛厂"}
    assert [f for f in check_l4b(p, _ocr(p, {"dir": ["树村西"]}), names)
            if f.level == "fail"] == []


def test_l4b_catches_wrong_place_name():
    p = _page([_ti("dir", "树村西")])
    names = {"树村", "肖家河"}
    fs = [f for f in check_l4b(p, _ocr(p, {"dir": ["肖家河西"]}), names)]
    assert any(f.code == "PROPER_NAME_MISSING" for f in fs)


def test_l4b_skips_when_names_table_empty():
    """专名表缺失必须 skip 而非 pass —— 否则新集漏填就静默通过。"""
    p = _page([_ti("dir", "树村西")])
    fs = check_l4b(p, _ocr(p, {"dir": ["树村西"]}), set())
    assert [f for f in fs if f.code == "NO_NAMES_TABLE"]


def test_names_file_loads():
    names = load_names()
    assert "树村" in names
    assert len(names) > 20
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_checks_content.py -v`
Expected: FAIL —— `ModuleNotFoundError: No module named 'qa_v2.checks_content'`

- [ ] **Step 3: 建专名表**

`qa_v2/names.txt`（每行一个，`#` 开头为注释；E11 专名，E12 起追加）：

```
# 专名表：L4-b 内容校验用
# 只放「读错就说明内容错了」的专名。
# 地名 / 旗名 / 寺名 / 官名 / 园名 / 书名。
树村
肖家河
蓝靛厂
圆明园
长春园
畅春园
静宜园
静明园
乐善园
广仁宫
海甸
安河桥
镶黄旗
正白旗
正黄旗
正红旗
镶红旗
正蓝旗
镶蓝旗
镶白旗
五圣庵
观音寺
总兵
副将
守备
护军校
参领
五城寺院册
日下旧闻考
皇朝文献通考
竹叶亭杂记
钦定八旗通志
```

- [ ] **Step 4: 写最小实现**

`qa_v2/checks_content.py`：

```python
"""L4 内容闭环：槽里的字，对不对。

旧 QA 只判「区域里有深色像素」，写错字照样通过。E11 真实发生过：
P8 口播「各占了一处」后又说树村占两处，算术自相矛盾 —— 无机器能发现。

L4 分三子层，任一不过即该槽 fail：
  L4-a 数字严格 —— 「1485」写成「1486」要能抓
  L4-b 专名严格 —— 专名表命中项必须逐个出现
  L4-c 字幕交叉 —— 与口播稿原文对数字（Task 12）

前提：E11 实测 OCR 噪声**只有标点规范化**（·→. 、，→. ），
无错字无漏字。所以不需要 fuzzy matching，数字与专名可以严格比对。
"""
import pathlib
from typing import List, Set

from qa_v2.data import Page
from qa_v2.frames import OcrResult
from qa_v2.normalize import (
    extract_numbers, normalize_punct, number_unknown_rate,
)
from qa_v2.report import Finding

NAMES = pathlib.Path(__file__).with_name("names.txt")

# 无法解析的数字 token 占比超过此值报 warn
# （防止 to_int 有 bug 却静默通过）
UNKNOWN_RATE_WARN = 0.20


def load_names(path=None):
    """读专名表。空文件返回空 set —— 调用方须据此报 skip 而非 pass。"""
    p = path or NAMES
    if not p.exists():
        return set()
    out = set()
    for line in p.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            out.add(s)
    return out


def _ocr_text_for(page, ocr, slot_id):
    """取该槽内的 OCR 读回文本。"""
    from qa_v2.frames import text_at
    from qa_v2.geometry import plate_to_canvas
    slot = page.slot(slot_id)
    if slot is None:
        return ""
    rect = plate_to_canvas(page.plate, slot.x, slot.y, slot.w, slot.h)
    return "".join(t for t, _, _ in text_at(ocr, rect))


def check_l4a(page, ocr):
    """数字严格：原文里的每个数字都必须出现在 OCR 读回里。"""
    out = []
    for item in page.items:
        if item.is_tag:
            continue
        want = set(extract_numbers(item.text))
        if not want:
            continue
        got_raw = _ocr_text_for(page, ocr, item.slot_id)
        got = set(extract_numbers(normalize_punct(got_raw)))

        rate = number_unknown_rate(item.text)
        if rate > UNKNOWN_RATE_WARN:
            out.append(Finding(
                "L4-a", page.number, item.slot_id, "warn",
                "NUMBER_UNKNOWN_RATE",
                "数字归一失败率 %.0f%%，本槽数字比对不可信"
                % (rate * 100), {"text": item.text[:40]}))

        missing = sorted(want - got)
        if missing:
            out.append(Finding(
                "L4-a", page.number, item.slot_id, "fail",
                "NUMBER_MISMATCH",
                "数字对不上：期望 %s，读回 %s"
                % (missing, sorted(got)),
                {"expect": item.text[:50], "ocr": got_raw[:50]}))
    return out


def check_l4b(page, ocr, names):
    """专名严格：原文命中的专名必须逐个出现在 OCR 读回里。"""
    out = []
    if not names:
        out.append(Finding(
            "L4-b", None, None, "skip", "NO_NAMES_TABLE",
            "专名表为空，L4-b 未执行（不算通过）。新集需维护 qa_v2/names.txt"))
        return out
    for item in page.items:
        if item.is_tag:
            continue
        want = [n for n in names if n in item.text]
        if not want:
            continue
        got = normalize_punct(_ocr_text_for(page, ocr, item.slot_id))
        missing = [n for n in want if normalize_punct(n) not in got]
        if missing:
            out.append(Finding(
                "L4-b", page.number, item.slot_id, "fail",
                "PROPER_NAME_MISSING",
                "专名对不上：缺 %s" % "、".join(missing),
                {"expect": item.text[:50]}))
    return out
```

- [ ] **Step 5: 跑测试确认通过**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_checks_content.py -v`
Expected: PASS —— 14 passed

- [ ] **Step 6: 提交**

```bash
cd /tmp/chemistry-video
git add qa_v2/names.txt qa/checks_content.py tests/test_checks_content.py
git commit -m "feat(qa): L4 内容闭环（数字严格 + 专名严格）

旧 QA 查不出「1485 写成 1486」。E11 真实发生过 P8 算术自相矛盾
（口播说各占一处又说树村占两处），无机器能发现。
专名表缺失时报 skip 而非 pass —— 否则新集漏填就静默通过。
前提：E11 实测 OCR 噪声仅标点，不需要 fuzzy matching。"
```

---

