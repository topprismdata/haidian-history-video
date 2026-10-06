## Task 10: L6 tag 槽判据

**Files:**
- Modify: `qa_v2/checks_render.py`（追加 `check_l6`）
- Modify: `tests/test_checks_render.py`（追加测试）

**Interfaces:**
- Consumes: 同上
- Produces:
  - `check_l6(page: Page, png: Path) -> List[Finding]`
  - `WHITE_MIN = 200`、`WHITE_MAX_RATIO = 0.40`

- [ ] **Step 1: 写失败的测试**

追加到 `tests/test_checks_render.py`：

```python
from qa_v2.checks_render import check_l6, WHITE_MIN, WHITE_MAX_RATIO


def test_l6_passes_when_white_text_on_dark():
    """tag 槽是深底白字，深色墨判据天然不适用 —— 旧 QA 直接排除，
    所以证据标签从不被检查。"""
    a = np.full((80, 300, 3), 90, dtype=np.uint8)      # 深底
    a[30:50, 60:240] = 245                              # 白字
    p = _tmp_png(a)
    page = _page([("evidence_tag", 0, 0, 300, 80)], number=1)
    page.plate = (1920, 1080)
    assert [f for f in check_l6(page, p) if f.level == "fail"] == []


def test_l6_fails_when_tag_not_rendered():
    a = np.full((80, 300, 3), 90, dtype=np.uint8)      # 全深底，没字
    p = _tmp_png(a)
    page = _page([("evidence_tag", 0, 0, 300, 80)], number=1)
    page.plate = (1920, 1080)
    fs = [f for f in check_l6(page, p) if f.level == "fail"]
    assert len(fs) == 1 and fs[0].code == "TAG_SLOT_EMPTY"


def test_l6_flags_all_white_slab():
    """整槽全白说明判据抓错了区域，不是有字。"""
    a = np.full((80, 300, 3), 250, dtype=np.uint8)
    p = _tmp_png(a)
    page = _page([("evidence_tag", 0, 0, 300, 80)], number=1)
    page.plate = (1920, 1080)
    fs = check_l6(page, p)
    assert any(f.code == "TAG_SLOT_ALL_WHITE" for f in fs)


def test_real_shucun_passes_l6():
    from qa_v2.data import load_episode
    import pathlib
    ep = load_episode("shucun")
    outdir = pathlib.Path("/tmp/qa_shucun_frames")
    outdir.mkdir(parents=True, exist_ok=True)
    from qa_v2.frames import render_frame
    for p in ep.pages:
        png = outdir / ("p%02d.png" % p.number)
        if not png.exists():
            render_frame("shucun", p.number, ep.final_frame(p.number), png)
        assert [f for f in check_l6(p, png) if f.level == "fail"] == [], p.number
```

在测试文件顶部加辅助函数：

```python
def _tmp_png(a, name="t.png"):
    from PIL import Image
    import tempfile, pathlib
    d = pathlib.Path(tempfile.mkdtemp())
    p = d / name
    Image.fromarray(a).save(p)
    return p
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_checks_render.py -v -k l6`
Expected: FAIL —— `ImportError: cannot import name 'check_l6'`

- [ ] **Step 3: 写最小实现**

追加到 `qa_v2/checks_render.py`：

```python
# ── L6 tag 槽 ────────────────────────────────────────────────────────

# 白字阈值（深底白字反白样式）
WHITE_MIN = 200
# 白像素占比上限：超过说明抓到的是浅色底板而非文字块
WHITE_MAX_RATIO = 0.40
# 白像素占比下限：低于说明槽里没东西
WHITE_MIN_RATIO = 0.01


def check_l6(page, png):
    """tag 型槽（深底白字）的独立判据。

    旧 qa_all.py 用 TAG_IDS 把这类槽直接排除 —— 于是**证据标签
    从不被检查**。E11 实测 8 个 evidence_tag 槽全部有值
    （[文献记载]/[官书记载]/[存疑待考]/[原书记载]/[实录记载]/[系列联动]），
    说明判据可用。
    """
    from PIL import Image
    a = np.array(Image.open(str(png)).convert("RGB"))
    out = []
    for s in page.slots:
        items = [i for i in page.items if i.slot_id == s.id]
        if not items or not items[0].is_tag:
            continue
        rect = plate_to_canvas(page.plate, s.x, s.y, s.w, s.h)
        rx, ry, rw, rh = rect
        H, W = a.shape[:2]
        x1, y1 = min(W, rx + rw), min(H, ry + rh)
        sub = a[max(0, ry):y1, max(0, rx):x1]
        if sub.size == 0:
            continue
        white = (sub.min(axis=2) > WHITE_MIN).mean()
        if white < WHITE_MIN_RATIO:
            out.append(Finding(
                "L6", page.number, s.id, "fail", "TAG_SLOT_EMPTY",
                "证据标签槽内无白字（tag 是深底白字，此槽未渲染）",
                {"white_ratio": round(float(white), 4)}))
        elif white > WHITE_MAX_RATIO:
            out.append(Finding(
                "L6", page.number, s.id, "warn", "TAG_SLOT_ALL_WHITE",
                "槽内几乎全白，可能抓错区域",
                {"white_ratio": round(float(white), 4)}))
    return out
```

- [ ] **Step 4: 跑测试确认通过**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_checks_render.py -v`
Expected: PASS —— 15 passed

- [ ] **Step 5: 提交**

```bash
cd /tmp/chemistry-video
git add qa/checks_render.py tests/test_checks_render.py
git commit -m "feat(qa): L6 tag 槽独立判据

旧 qa_all.py 用 TAG_IDS 把 tag 槽直接排除，于是证据标签从不被检查。
tag 是深底白字，判据改为找白像素块，占比 1%~40% 为正常。
E11 实测 8 个 evidence_tag 槽全部有值，判据可用。"
```

---

