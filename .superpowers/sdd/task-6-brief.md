## Task 6: L2 几何可行性（渲染前预检）

**Files:**
- Modify: `qa_v2/checks_data.py`（追加 `check_l2`）
- Modify: `tests/test_checks_data.py`（追加测试）

**Interfaces:**
- Consumes: `qa_v2/data.py`、`qa_v2/report.py`
- Produces:
  - `check_l2(ep: Episode) -> List[Finding]`
  - `estimate_lines(text: str, slot_w: float, size: int) -> int`
  - `OVERFLOW_TOLERANCE = 1.15`

- [ ] **Step 1: 写失败的测试**

追加到 `tests/test_checks_data.py`：

```python
from qa_v2.checks_data import check_l2, estimate_lines, OVERFLOW_TOLERANCE


def test_estimate_lines_respects_manual_breaks():
    # 3 行，每行 4 字，槽宽足够 → 3 行
    assert estimate_lines("甲乙\n丙丁\n戊己", 500, 20) == 3


def test_estimate_lines_wraps_when_no_break():
    # 无 \n，25 个汉字，槽宽 500px @20px 字 → 每行约 25 字 → 1 行
    assert estimate_lines("一" * 25, 500, 20) == 1


def test_estimate_lines_wraps_to_multiple():
    # 100 字，槽宽 500px @20px → 每行 25 字 → 4 行
    assert estimate_lines("一" * 100, 500, 20) == 4


def test_l2_ok_when_fits():
    ep = _ep([_page([("a", 0, 0, 500, 100)], [("a", "甲乙丙丁", 20, True, None)])])
    assert _codes(check_l2(ep)) == []


def test_l2_warns_on_overflow():
    """E11 P4/P5 各有一处：文案多行装不下，首尾行被切在框外。
    当时靠目视发现，QA 全绿。"""
    ep = _ep([_page([("a", 0, 0, 500, 60)],           # 60px 装不下 4 行 @20px lh1.4
                    [("a", "甲\n乙\n丙\n丁", 20, True, None)])])
    fs = check_l2(ep)
    assert len(fs) == 1
    assert fs[0].code == "ESTIMATED_OVERFLOW"
    assert fs[0].level == "warn"


def test_l2_uses_tolerance():
    """刚好在 1.15 倍以内不该报。"""
    # 3 行 @20px lh1.4 = 84px；槽高 80px → 84/80 = 1.05 < 1.15
    ep = _ep([_page([("a", 0, 0, 500, 80)],
                    [("a", "甲\n乙\n丙", 20, True, None)])])
    assert "ESTIMATED_OVERFLOW" not in _codes(check_l2(ep))


def test_real_shucun_passes_l2():
    from qa_v2.data import load_episode
    fs = check_l2(load_episode("shucun"))
    assert [f for f in fs if f.level == "fail"] == []
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_checks_data.py -v -k "l2 or estimate"`
Expected: FAIL —— `ImportError: cannot import name 'check_l2'`

- [ ] **Step 3: 写最小实现**

追加到 `qa_v2/checks_data.py`：

```python
# ── L2 几何可行性（渲染前预检）────────────────────────────────────────

# 需要高度超过槽高此倍数才报 warn（FitText 内部有自适应缩放，
# 真实溢出点略高于理论值，1.15 是实测留的容差）
OVERFLOW_TOLERANCE = 1.15

# 单个汉字的宽度约等于字号；ASCII 约 0.55 倍
_WIDE = 1.0
_NARROW = 0.55


def _text_units(s):
    """估算文本的"字宽单位"：汉字 1.0，ASCII 0.55。"""
    n = 0.0
    for ch in s:
        n += _NARROW if ord(ch) < 128 else _WIDE
    return n


def estimate_lines(text, slot_w, size):
    """估算渲染后占几行。与 FitText 的 effW 同口径（宽字符算 1，窄字符 0.45~0.55）。"""
    if not text:
        return 0
    per_line = max(1.0, (slot_w - 24) / float(size))
    if "\n" in text:
        return sum(max(1, int(-(-_text_units(l) // per_line)))
                   for l in text.split("\n") if l.strip())
    return max(1, int(-(-_text_units(text) // per_line)))


def check_l2(ep):
    """渲染前的溢出预检。装不下就 warn，省得渲完再靠眼睛找。"""
    out = []
    for page in ep.pages:
        for item in page.items:
            slot = page.slot(item.slot_id)
            if slot is None or slot.h <= 0 or item.size <= 0:
                continue
            lines = estimate_lines(item.text, slot.w, item.size)
            if lines <= 0:
                continue
            need = lines * item.size * (item_lh(item))
            ratio = need / float(slot.h)
            if ratio > OVERFLOW_TOLERANCE:
                out.append(Finding(
                    "L2", page.number, item.slot_id, "warn",
                    "ESTIMATED_OVERFLOW",
                    "预计需 %.0fpx / 槽高 %dpx（%d 行 @%dpx）"
                    % (need, slot.h, lines, item.size),
                    {"ratio": round(ratio, 2), "lines": lines}))
    return out


def item_lh(item, default=1.4):
    return getattr(item, "lh", None) or default
```

- [ ] **Step 4: 跑测试确认通过**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_checks_data.py -v`
Expected: PASS —— 16 passed

- [ ] **Step 5: 提交**

```bash
cd /tmp/chemistry-video
git add qa/checks_data.py tests/test_checks_data.py
git commit -m "feat(qa): L2 溢出预检

渲染前就能算出文案装不装得下，省得渲完靠眼睛找。
E11 P4/P5 各有一处超框（当时目视发现，QA 全绿）。
容差 1.15 —— FitText 有自适应缩放，真实溢出点略高于理论值。"
```

---

