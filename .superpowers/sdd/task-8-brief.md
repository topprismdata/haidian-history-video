## Task 8: L3 渲染存在性 + 负控制

**Files:**
- Create: `qa_v2/checks_render.py`
- Create: `tests/test_checks_render.py`

**Interfaces:**
- Consumes: `qa_v2/frames.py`、`qa_v2/data.py`、`qa_v2/geometry.py`、`qa_v2/report.py`
- Produces:
  - `check_l3(page: Page, ocr: OcrResult) -> List[Finding]`
  - `NEGATIVE_CONTROL_SHIFT = 300` —— 负控制平移量（px）
  - `assert_negative_control(page: Page, ocr: OcrResult) -> int` —— 返回「负控制未命中」的槽位数，必须为 0

- [ ] **Step 1: 写失败的测试**

`tests/test_checks_render.py`：

```python
"""L3 渲染存在性 + 负控制。

L3 判据：**槽内必须有属于这个槽位的 OCR 文本**。
不是「区域内有深色像素」——后者在插画上恒真。
E11 实测：随手挑的「空白区」有 583 墨像素被误判通过。
"""
import pytest

from qa_v2.data import Page, Slot
from qa_v2.frames import OcrResult
from qa_v2.checks_render import (
    check_l3, assert_negative_control, NEGATIVE_CONTROL_SHIFT,
)

PLATE = (1672, 941)


def _page(slots, number=1):
    return Page(number, PLATE, [Slot(*s) for s in slots], [])


def test_l3_passes_when_text_present():
    p = _page([("title", 0, 0, 400, 100)])
    o = OcrResult(["一个村子"], [(100, 30, 350, 80)], [0.99])
    assert [f for f in check_l3(p, o) if f.level == "fail"] == []


def test_l3_fails_when_slot_empty():
    """这就是旧判据漏掉的情况：槽里什么都没有。"""
    p = _page([("title", 0, 0, 400, 100)])
    o = OcrResult(["远处插画上的字"], [(1400, 700, 1600, 740)], [0.99])
    fs = [f for f in check_l3(p, o) if f.level == "fail"]
    assert len(fs) == 1
    assert fs[0].code == "SLOT_RENDER_EMPTY"


def test_l3_ignores_tag_slot():
    """tag 槽由 L6 用独立判据查，L3 不重复报。"""
    p = _page([("evidence_tag", 1400, 0, 200, 60)])
    o = OcrResult([], [], [])
    assert check_l3(p, o) == []


def test_l3_reports_low_confidence_as_warn():
    p = _page([("a", 0, 0, 400, 100)])
    o = OcrResult(["难认的字"], [(100, 30, 350, 80)], [0.40])
    fs = [f for f in check_l3(p, o) if f.code == "OCR_LOW_CONFIDENCE"]
    assert len(fs) == 1 and fs[0].level == "warn"


def test_negative_control_passes_when_shifted_slot_is_empty():
    """把槽位平移 300px 落到插画区，应判为空。
    这是判据非恒真的证明 —— 旧 QA 缺的就是这个。"""
    p = _page([("title", 0, 0, 400, 100)])
    # 文字只出现在原位 (100,30)，平移后槽位中心落到别处
    o = OcrResult(["一个村子"], [(100, 30, 350, 80)], [0.99])
    assert assert_negative_control(p, o) == 0


def test_negative_control_detects_always_true_detector():
    """反例：若检测器恒真，负控制必须报出来而不是悄悄过。"""
    p = _page([("title", 0, 0, 400, 100)])
    o = OcrResult(["一个村子"], [(100, 30, 350, 80)], [0.99])
    # 把平移量设成 0（等于不验证）应当被拒绝
    with pytest.raises(AssertionError):
        assert_negative_control(p, o, shift=0)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_checks_render.py -v`
Expected: FAIL —— `ModuleNotFoundError: No module named 'qa_v2.checks_render'`

- [ ] **Step 3: 写最小实现**

`qa_v2/checks_render.py`：

```python
"""L3 渲染存在性、L5 溢出、L6 tag 槽。需渲染帧，不用 OCR（L6 除外）。

**为什么不用「区域内有深色像素」**：E11 实测负控制 —— 随手挑的
「空白区」有 583 墨像素被判为通过（落在插画深色木器上）。
该判据对插画底色敏感，板图越暗误判率越高。L3 一律用「该槽该有的文本」。
"""
from typing import List

from qa_v2.data import Page, Slot
from qa_v2.frames import OcrResult, text_at
from qa_v2.geometry import plate_to_canvas
from qa_v2.report import Finding

TAG_IDS = {"evidence_tag"}

# 负控制：把槽位平移这么多 px 后必须判为空。
# 300 超过任何板面的标题带高度，不会落回真槽。
NEGATIVE_CONTROL_SHIFT = 300

# OCR 置信低于此值报 warn（E11 实测最低 0.350 出现在插画篆书上，
# 槽位内文字实测最低 0.828）
LOW_CONFIDENCE = 0.80


def check_l3(page, ocr):
    """槽内必须有 OCR 文本。"""
    out = []
    for s in page.slots:
        if s.id in TAG_IDS:
            continue  # 深底白字，交给 L6
        rect = plate_to_canvas(page.plate, s.x, s.y, s.w, s.h)
        found = text_at(ocr, rect)
        if not found:
            out.append(Finding(
                "L3", page.number, s.id, "fail", "SLOT_RENDER_EMPTY",
                "槽内无 OCR 文本（该槽没渲出内容）",
                {"canvas_rect": list(rect)}))
            continue
        worst = min(f[2] for f in found)
        if worst < LOW_CONFIDENCE:
            out.append(Finding(
                "L3", page.number, s.id, "warn", "OCR_LOW_CONFIDENCE",
                "OCR 置信偏低 %.2f，可能字被裁切" % worst,
                {"text": found[0][0][:30], "score": round(worst, 3)}))
    return out


def assert_negative_control(page, ocr, shift=NEGATIVE_CONTROL_SHIFT):
    """负控制：平移槽位后应判为空。返回「未命中」的槽位数。

    判据恒真时这个数 > 0 —— 旧 QA 缺的正是这个证明。
    shift=0 会被拒绝：那等于没验证。
    """
    assert shift > 0, "负控制的平移量必须 > 0，否则等于没验证"
    not_caught = 0
    for s in page.slots:
        if s.id in TAG_IDS:
            continue
        moved = Slot(s.id, s.x + shift, s.y, s.w, s.h)
        rect = plate_to_canvas(page.plate, moved.x, moved.y,
                               moved.w, moved.h)
        if text_at(ocr, rect):
            not_caught += 1
    return not_caught
```

- [ ] **Step 4: 跑测试确认通过**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_checks_render.py -v`
Expected: PASS —— 6 passed

- [ ] **Step 5: 提交**

```bash
cd /tmp/chemistry-video
git add qa/checks_render.py tests/test_checks_render.py
git commit -m "feat(qa): L3 渲染存在性 + 负控制

判据是「该槽该有的 OCR 文本」，不是「区域内有深色像素」——
后者在 E11 实测中对插画恒真（空白区 583 墨像素被判通过）。
assert_negative_control 证明判据非恒真，这是旧 QA 缺的东西。
置信阈值 0.80 来自 E11 实测（槽内最低 0.828，插画篆书 0.350）。"
```

---

