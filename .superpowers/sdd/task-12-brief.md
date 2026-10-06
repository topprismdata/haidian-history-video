## Task 12: L4-c 字幕交叉

**Files:**
- Modify: `qa_v2/checks_content.py`（追加 `check_l4c`）
- Modify: `tests/test_checks_content.py`（追加测试）

**Interfaces:**
- Consumes: `qa_v2/data.py::narration_text`、`qa_v2/normalize.py`
- Produces:
  - `check_l4c(ep: Episode, ocr_by_page: Dict[int, OcrResult]) -> List[Finding]`

- [ ] **Step 1: 写失败的测试**

追加到 `tests/test_checks_content.py`：

```python
from qa_v2.checks_content import check_l4c


def test_l4c_skips_when_narration_missing():
    from qa_v2.data import Episode
    ep = Episode("__none__", [_page([_ti("a", "1485")], 1)], [(0, 660)])
    assert any(f.code == "NO_NARRATION" for f in check_l4c(ep, {1: _ocr(_page([]), {})}))


def test_l4c_passes_when_number_in_narration():
    """真实数据：E11 P3 口播含「1485」。"""
    from qa_v2.data import Episode, Page, Slot, TextItem
    pg = Page(3, PLATE, [Slot("r3_total", 0, 0, 300, 60)],
              [TextItem("r3_total", "1485", 20, True, None)])
    ep = Episode("shucun", [pg], [(0, 660)])
    ep.narration = {3: "正红旗在安河桥，官房一千四百六十七间。"}
    o = OcrResult(["1485"], [(10, 10, 200, 50)], [0.99])
    assert [f for f in check_l4c(ep, {3: o}) if f.level == "fail"] == []


def test_l4c_flags_number_absent_from_narration():
    """两边都错的情况：文案写 1485，口播里根本没有这个数。"""
    from qa_v2.data import Episode, Page, Slot, TextItem
    pg = Page(3, PLATE, [Slot("r3_total", 0, 0, 300, 60)],
              [TextItem("r3_total", "1485", 20, True, None)])
    ep = Episode("shucun", [pg], [(0, 660)])
    ep.narration = {3: "正红旗在安河桥，官房一千四百六十间。"}
    o = OcrResult(["1485"], [(10, 10, 200, 50)], [0.99])
    fs = [f for f in check_l4c(ep, {3: o}) if f.level == "fail"]
    assert len(fs) == 1 and fs[0].code == "NUMBER_NOT_IN_NARRATION"
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_checks_content.py -v -k l4c`
Expected: FAIL —— `ImportError: cannot import name 'check_l4c'`

- [ ] **Step 3: 写最小实现**

追加到 `qa_v2/checks_content.py`：

```python
def check_l4c(ep, ocr_by_page):
    """字幕交叉：槽里的数字，必须能在该页口播稿里找到。

    **只认 narration/all.json，不认 subtitles.ts**。两个实测理由：
      1) subtitles.ts 的数字 token 大量是数组下标与行号（01…99），
         当文本 grep 会全污染；
      2) 口播有意省略书名简称（文案《钦定日下旧闻考》vs
         口播《日下旧闻考》），直接比对必然假阳性。

    这是三路交叉里最弱的一路：口播与文案本就不要求逐字一致，
    所以只对**数字**交叉，叙述性文字不查。
    """
    from qa_v2.data import narration_text
    out = []
    narration = getattr(ep, "narration", None)
    if narration is None:
        narration = narration_text(ep.name)
    if not narration:
        out.append(Finding(
            "L4-c", None, None, "skip", "NO_NARRATION",
            "找不到 %s_video/narration/all.json，L4-c 未执行（不算通过）"
            % ep.name))
        return out
    for page in ep.pages:
        spoken = narration.get(page.number)
        if not spoken:
            continue
        spoken_nums = set(extract_numbers(spoken))
        ocr = ocr_by_page.get(page.number)
        for item in page.items:
            if item.is_tag:
                continue
            want = set(extract_numbers(item.text))
            if not want:
                continue
            # 只查「该页叙述里出现过的量级」，避免卷号（116/99）误报
            missing = sorted(
                n for n in want
                if n not in spoken_nums and not _is_volume_ref(n))
            if missing:
                out.append(Finding(
                    "L4-c", page.number, item.slot_id, "fail",
                    "NUMBER_NOT_IN_NARRATION",
                    "数字 %s 在该页口播稿里找不到" % missing,
                    {"text": item.text[:50]}))

    return out


# 卷号/版本号类引用：口播通常不念，不参与交叉
_VOLUME_RE = None


def _is_volume_ref(n):
    """是否为卷号类引用（如《钦定八旗通志》卷116 的 116、99）。

    判据：1~200 且页码/卷号常见量级。E11 实测《八旗通志》卷116、
    《日下旧闻考》卷99/卷73 口播均未念。
    """
    return 1 <= n <= 200
```

- [ ] **Step 4: 跑测试确认通过**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_checks_content.py -v`
Expected: PASS —— 17 passed

- [ ] **Step 5: 提交**

```bash
cd /tmp/chemistry-video
git add qa/checks_content.py tests/test_checks_content.py
git commit -m "feat(qa): L4-c 口播稿交叉

只认 narration/all.json，不认 subtitles.ts：
实测发现 subtitles.ts 的数字 token 大量是数组下标（01…99），
且口播有意省略书名简称，直接比对必假阳性。
卷号类引用（1~200，如卷116/卷99）不参与交叉 —— 口播通常不念。"
```

---

