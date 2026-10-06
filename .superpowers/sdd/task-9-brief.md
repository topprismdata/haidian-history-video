## Task 9: L5 溢出检测

**Files:**
- Modify: `qa_v2/checks_render.py`（追加 `check_l5`）
- Modify: `tests/test_checks_render.py`（追加测试）

**Interfaces:**
- Consumes: `qa_v2/frames.py`、`qa_v2/data.py`、`qa_v2/geometry.py`、`qa_v2/report.py`
- Produces:
  - `check_l5(page: Page, png: Path) -> List[Finding]`
  - `text_bbox_in_slot(a_g: np.ndarray, rect: Rect) -> Optional[Rect]` —— 槽内文字外接框（`x,y,w,h`），找不到返回 None
  - `TOUCH_MARGIN = 3` —— 墨迹距槽边小于此值算触边

- [ ] **Step 1: 写失败的测试**

追加到 `tests/test_checks_render.py`：

```python
import numpy as np
import pytest
from PIL import Image
from qa_v2.checks_render import check_l5, text_bbox_in_slot, TOUCH_MARGIN


def _slot_img(w, h, text_rows, pad_x=30, pad_y=20, size=28):
    """造一张槽位图：白底 + 居中若干行「字」（深色横条模拟笔画）。"""
    a = np.full((h + 2 * pad_y, w + 2 * pad_x, 3), 250, dtype=np.uint8)
    lh = int(size * 1.4)
    total = len(text_rows) * lh
    y0 = (a.shape[0] - total) // 2
    for i in range(len(text_rows)):
        yy = y0 + i * lh + 4
        for x in range(pad_x + 10, pad_x + w - 10, size):
            a[yy:yy + size - 6, x:x + size - 10] = 60
    return a


def test_text_bbox_finds_centered_text():
    a = _slot_img(500, 100, ["甲乙丙丁"])
    box = (30, 20, 500, 100)
    r = text_bbox_in_slot(a, box)
    assert r is not None
    x, y, w, h = r
    assert x > box[0] and y > box[1]
    assert x + w < box[0] + box[2]
    assert y + h < box[1] + box[3]


def test_text_bbox_returns_none_when_blank():
    a = np.full((140, 560, 3), 250, dtype=np.uint8)
    assert text_bbox_in_slot(a, (30, 20, 500, 100)) is None


def test_text_bbox_detects_touching_edge():
    a = np.full((100, 100, 3), 250, dtype=np.uint8)
    a[10:90, 0:20] = 60          # 文字贴住左边
    r = text_bbox_in_slot(a, (0, 0, 100, 100))
    assert r[0] <= TOUCH_MARGIN


def test_l5_ok_when_text_has_margin(tmp_path):
    a = _slot_img(500, 100, ["甲乙丙丁"])
    p = tmp_path / "s.png"
    Image.fromarray(a).save(p)
    page = _page([("note_left", 30, 20, 500, 100)], number=5)
    # 直接用板面坐标=画布坐标的简版 plate 免去换算干扰
    page.plate = (1920, 1080)
    assert [f for f in check_l5(page, p) if f.level == "fail"] == []


def test_l5_fails_when_text_touches_edge(tmp_path):
    a = np.full((100, 100, 3), 250, dtype=np.uint8)
    a[10:90, 0:25] = 60          # 文字溢出到槽外
    p = tmp_path / "s2.png"
    Image.fromarray(a).save(p)
    page = _page([("note_left", 0, 0, 100, 100)], number=5)
    page.plate = (1920, 1080)
    fs = [f for f in check_l5(page, p) if f.level == "fail"]
    assert len(fs) == 1 and fs[0].code == "TEXT_TOUCHES_SLOT_EDGE"
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_checks_render.py -v -k "l5 or text_bbox"`
Expected: FAIL —— `ImportError: cannot import name 'check_l5'`

- [ ] **Step 3: 写最小实现**

追加到 `qa_v2/checks_render.py`：

```python
# ── L5 溢出检测 ──────────────────────────────────────────────────────

# 墨迹距槽边小于此值算触边（实测 FitText 的 padding 是 10px 12px）
TOUCH_MARGIN = 3
# 面积小于此值的连通域视为噪点
MIN_BLOB = 12


def text_bbox_in_slot(a_g, rect):
    """在槽位矩形内找「文字」的外接框，返回 (x, y, w, h)。

    为什么要先分离底板：槽位有 backing 底板（浅色圆角矩形 + 深色描边
    与阴影），直接量「墨迹包围盒」量到的是底板边缘 —— E11 实测两个
    溢出与否的版本量出**完全相同**的数（恒差 28px），判据失效。

    做法：亮度 <130 视为墨，二值化后腐蚀 1 像素去掉描边与阴影，
    再按连通域面积过滤掉细碎噪点。
    """
    from scipy.ndimage import binary_erosion, label
    import numpy as np

    x, y, w, h = rect
    H, W = a_g.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x1 - x0 < 4 or y1 - y0 < 4:
        return None
    sub = a_g[y0:y1, x0:x1]
    ink = binary_erosion(sub < 130, iterations=1)
    if not ink.any():
        return None
    lab, n = label(ink)
    if n == 0:
        return None
    sizes = np.bincount(lab.ravel())
    keep_ids = [i for i in range(1, n + 1) if sizes[i] >= MIN_BLOB]
    if not keep_ids:
        return None
    keep = np.isin(lab, keep_ids)
    ys, xs = np.where(keep)
    if len(ys) == 0:
        return None
    return (int(xs.min()), int(ys.min()),
            int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1))


def check_l5(page, png):
    """文字外接框触边即溢出。"""
    from PIL import Image
    a = np.array(Image.open(str(png)).convert("L"))
    out = []
    for s in page.slots:
        if s.id in TAG_IDS:
            continue
        rect = plate_to_canvas(page.plate, s.x, s.y, s.w, s.h)
        r = text_bbox_in_slot(a, rect)
        if r is None:
            continue  # 空槽由 L3 报，这里不重复
        tx, ty, tw, th = r
        rx, ry, rw, rh = rect
        hits = []
        if tx <= TOUCH_MARGIN:
            hits.append("左")
        if ty <= TOUCH_MARGIN:
            hits.append("上")
        if tx + tw >= rw - TOUCH_MARGIN:
            hits.append("右")
        if ty + th >= rh - TOUCH_MARGIN:
            hits.append("下")
        if hits:
            out.append(Finding(
                "L5", page.number, s.id, "fail", "TEXT_TOUCHES_SLOT_EDGE",
                "文字贴到槽边（%s），疑似被裁切" % "、".join(hits),
                {"text_rect": [tx, ty, tw, th],
                 "slot_rect": [rx, ry, rw, rh]}))
    return out
```

在文件头补上 `import numpy as np`（避免每个函数内重复 import）。

- [ ] **Step 4: 跑测试确认通过**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_checks_render.py -v`
Expected: PASS —— 11 passed

- [ ] **Step 5: 提交**

```bash
cd /tmp/chemistry-video
git add qa/checks_render.py tests/test_checks_render.py
git commit -m "feat(qa): L5 溢出检测

必须先分离 backing 底板再量文字：直接量墨迹包围盒得到的是底板描边与阴影，
E11 实测溢出与否两个版本量出完全相同的数（恒差 28px），判据失效。
做法：亮度<130 二值化 → 腐蚀 1px 去描边 → 连通域面积 >=12px 去噪。"
```

---

