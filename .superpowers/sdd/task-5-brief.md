## Task 5: L1 数据一致性

**Files:**
- Create: `qa_v2/checks_data.py`
- Create: `tests/test_checks_data.py`

**Interfaces:**
- Consumes: `qa_v2/data.py`（Task 3）、`qa_v2/geometry.py`（Task 1）、`qa_v2/report.py`（Task 4）
- Produces:
  - `check_l1(ep: Episode) -> List[Finding]`
  - 判据常量：`OVERLAP_FAIL_RATIO = 0.05`、`MIN_SLOT_W = 40`、`MIN_SLOT_H = 20`

- [ ] **Step 1: 写失败的测试**

`tests/test_checks_data.py`：

```python
"""L1 数据一致性：纯数据检查，不渲帧，<0.1s/页。"""
import pytest

from qa_v2.data import Episode, Page, Slot, TextItem
from qa_v2.checks_data import (
    check_l1, OVERLAP_FAIL_RATIO, MIN_SLOT_W, MIN_SLOT_H,
)


def _page(slots, items, plate=(1672, 941), number=1):
    return Page(number, plate, [Slot(*s) for s in slots],
                [TextItem(*i) for i in items])


def _ep(pages):
    layout = []
    cur = 0
    for p in pages:
        layout.append((cur, 660))
        cur += 660
    return Episode("t", pages, layout)


def _codes(fs):
    return sorted(f.code for f in fs)


def test_clean_episode_passes():
    ep = _ep([_page([("title", 0, 0, 400, 100)],
                    [("title", "标题", 26, True, None)])])
    assert _codes(check_l1(ep)) == []


def test_text_referencing_missing_slot():
    """E11 实测踩中：badge→evidence_tag 改名后文案侧漏改，
    boxOf 静默返回 10×10 兜底框，标签飞到画外。"""
    ep = _ep([_page([("evidence_tag", 1400, 20, 250, 60)],
                    [("badge", "[文献记载]", 20, True, "tag")])])
    codes = _codes(check_l1(ep))
    assert "TEXT_REFERENCES_MISSING_SLOT" in codes


def test_slot_with_no_text_is_flagged():
    ep = _ep([_page([("title", 0, 0, 400, 100),
                      ("subtitle", 0, 110, 400, 40)],
                    [("title", "标题", 26, True, None)])])
    assert "SLOT_WITHOUT_TEXT" in _codes(check_l1(ep))


def test_out_of_bounds_slot():
    ep = _ep([_page([("title", 1700, 0, 400, 100)],
                    [("title", "标题", 26, True, None)])])
    assert "SLOT_OUT_OF_BOUNDS" in _codes(check_l1(ep))


def test_tiny_slot_warns():
    """改名后残留旧坐标的典型症状：槽小得装不下字。"""
    ep = _ep([_page([("title", 0, 0, MIN_SLOT_W - 1, 100)],
                    [("title", "标题", 26, True, None)])])
    fs = [f for f in check_l1(ep) if f.code == "SLOT_TOO_SMALL"]
    assert len(fs) == 1 and fs[0].level == "warn"


def test_overlap_fails_above_threshold():
    ep = _ep([_page([("a", 0, 0, 400, 100), ("b", 380, 0, 400, 100)],
                    [("a", "甲", 20, True, None), ("b", "乙", 20, True, None)])])
    fs = [f for f in check_l1(ep) if f.code == "SLOT_OVERLAP"]
    assert len(fs) == 1 and fs[0].level == "fail"


def test_overlap_below_threshold_is_fine():
    """边框相邻不算叠。"""
    ep = _ep([_page([("a", 0, 0, 400, 100), ("b", 405, 0, 400, 100)],
                    [("a", "甲", 20, True, None), ("b", "乙", 20, True, None)])])
    assert "SLOT_OVERLAP" not in _codes(check_l1(ep))


def test_page_count_matches_layout():
    pages = [_page([("t", 0, 0, 100, 40)], [("t", "x", 20, True, None)],
                   number=i) for i in range(1, 4)]
    ep = Episode("t", pages, [(0, 660), (660, 660)])   # 布局只有 2 项
    assert "PAGE_COUNT_MISMATCH" in _codes(check_l1(ep))


def test_real_shucun_passes_l1():
    """E11 实测：93 槽位，重叠 0、越界 0、双向一致。"""
    from qa_v2.data import load_episode
    fs = check_l1(load_episode("shucun"))
    assert [f for f in fs if f.level == "fail"] == []
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_checks_data.py -v`
Expected: FAIL —— `ModuleNotFoundError: No module named 'qa_v2.checks_data'`

- [ ] **Step 3: 写最小实现**

`qa_v2/checks_data.py`：

```python
"""L1 数据一致性 + L2 几何可行性。纯数据，不渲帧，<0.2s/页。

L1 抓的是「静默失败」——最阴的一类：数据不匹配时代码仍能跑，
只是默默返回一个兜底值，最终表现为「某槽空白」或「文字飞到画外」。
E11 实测踩中：badge→evidence_tag 改名后文案侧漏改，
boxOf 找不到槽位却静默返回 10×10 兜底框。
"""
from typing import List

from qa_v2.geometry import overlap_ratio, out_of_bounds
from qa_v2.report import Finding

# 交叠面积占较小者的比例超过此值算 fail（边框相邻不算叠）
OVERLAP_FAIL_RATIO = 0.05
# 槽位尺寸下限：低于此值基本装不下任何文字
MIN_SLOT_W = 40
MIN_SLOT_H = 20


def check_l1(ep):
    """数据一致性。返回 List[Finding]。"""
    out = []
    if len(ep.pages) != len(ep.layout):
        out.append(Finding(
            "L1", None, None, "fail", "PAGE_COUNT_MISMATCH",
            "页数与页长表不符：%d 页 vs %d 项"
            % (len(ep.pages), len(ep.layout))))

    for page in ep.pages:
        have = set(s.id for s in page.slots)
        used = set(i.slot_id for i in page.items)

        for i in page.items:
            if i.slot_id not in have:
                out.append(Finding(
                    "L1", page.number, i.slot_id, "fail",
                    "TEXT_REFERENCES_MISSING_SLOT",
                    "文案引用了不存在的槽位（渲染时会静默走兜底框）",
                    {"text": i.text[:40]}))

        for s in page.slots:
            if s.id not in used:
                out.append(Finding(
                    "L1", page.number, s.id, "fail", "SLOT_WITHOUT_TEXT",
                    "槽位没有被任何文案引用（静默空洞）"))

            if out_of_bounds(s.rect, page.plate):
                out.append(Finding(
                    "L1", page.number, s.id, "fail", "SLOT_OUT_OF_BOUNDS",
                    "槽位越出板面 %dx%d" % page.plate,
                    {"rect": list(s.rect)}))

            if s.w < MIN_SLOT_W or s.h < MIN_SLOT_H:
                out.append(Finding(
                    "L1", page.number, s.id, "warn", "SLOT_TOO_SMALL",
                    "槽位过小，可能是改名后残留的旧坐标",
                    {"w": s.w, "h": s.h}))

        for i in range(len(page.slots)):
            for j in range(i + 1, len(page.slots)):
                a, b = page.slots[i], page.slots[j]
                r = overlap_ratio(a.rect, b.rect)
                if r > OVERLAP_FAIL_RATIO:
                    out.append(Finding(
                        "L1", page.number, a.id, "fail", "SLOT_OVERLAP",
                        "与 %s 交叠 %.0f%%" % (b.id, r * 100),
                        {"other": b.id, "ratio": round(r, 3)}))
    return out
```

- [ ] **Step 4: 跑测试确认通过**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_checks_data.py -v`
Expected: PASS —— 9 passed

- [ ] **Step 5: 提交**

```bash
cd /tmp/chemistry-video
git add qa/checks_data.py tests/test_checks_data.py
git commit -m "feat(qa): L1 数据一致性检查

抓的是静默失败：数据不匹配时代码仍能跑，只是默默返回兜底值。
E11 实测踩中 badge→evidence_tag 改名后文案侧漏改，boxOf 静默返回 10×10。
交叠阈值 5%（占较小槽面积），边框相邻不算叠。"
```

---

