## Task 1: 坐标换算与矩形运算

**Files:**
- Create: `qa_v2/__init__.py`
- Create: `qa_v2/geometry.py`
- Create: `tests/conftest.py`
- Create: `tests/test_geometry.py`

**Interfaces:**
- Consumes: 无（首个 task）
- Produces:
  - `CANVAS = (1920, 1080)` 模块常量
  - `plate_to_canvas(plate: Sequence[int], x: float, y: float, w: float, h: float) -> Tuple[int, int, int, int]` —— 板面坐标 → 画布像素矩形
  - `scale_of(plate: Sequence[int]) -> Tuple[float, float, float]` —— 返回 `(scale, offset_x, offset_y)`
  - `overlap_ratio(a: Rect, b: Rect) -> float` —— 交叠面积 / 较小者面积，无交叠返回 0.0
  - `out_of_bounds(rect: Rect, plate: Sequence[int]) -> bool`
  - `Rect = Tuple[int, int, int, int]`（`(x, y, w, h)`）

- [ ] **Step 1: 写失败的测试**

`tests/test_geometry.py`：

```python
"""坐标换算的回归测试。

背景：qa_all.py 曾把 1672×941 的板面坐标直接切 1920×1080 的渲染帧，
P5 采到的是插画上的香炉（墨像素 32062）而不是文字（2229），判据恒真。
本文件的 E11 实测锚点就是为防这个 bug 回归。
"""
from qa_v2.geometry import (
    CANVAS, scale_of, plate_to_canvas, overlap_ratio, out_of_bounds,
)

E11_PLATE = (1672, 941)


def test_scale_of_1672x941():
    s, ox, oy = scale_of(E11_PLATE)
    assert s == max(1920 / 1672, 1080 / 941)
    assert ox == 0.0          # 宽是约束边，横向正好铺满
    assert oy < 0             # 高有 0.29px 富余，居中后上边为负


def test_scale_of_1920x1080_is_identity():
    s, ox, oy = scale_of((1920, 1080))
    assert s == 1.0 and ox == 0.0 and oy == 0.0


def test_plate_to_canvas_e11_p5_note_left():
    """E11 P5 note_left：板面 (214,781,505,86) → 画布 (246,897,580,99)。

    这组数字来自实测：旧判据在板面坐标处采到插画（32062 墨像素），
    真文字在换算后的位置（2229 墨像素）。
    """
    x, y, w, h = plate_to_canvas(E11_PLATE, 214, 781, 505, 86)
    assert (x, y) == (246, 897)
    assert abs(w - 580) <= 1 and abs(h - 99) <= 1


def test_plate_to_canvas_1920_plate_is_identity():
    assert plate_to_canvas((1920, 1080), 100, 200, 300, 40) == (100, 200, 300, 40)


def test_plate_to_canvas_never_shrinks():
    """缩放只会放大（1672→1920），不能变小，否则采样区反而变小。"""
    _, w, _ = plate_to_canvas(E11_PLATE, 0, 0, 100, 100)[1:2] + (100,)
    x, y, w, h = plate_to_canvas(E11_PLATE, 0, 0, 100, 100)
    assert w > 100 and h > 100


def test_overlap_ratio_identical_is_one():
    r = (0, 0, 100, 100)
    assert overlap_ratio(r, r) == 1.0


def test_overlap_ratio_disjoint_is_zero():
    assert overlap_ratio((0, 0, 10, 10), (100, 100, 10, 10)) == 0.0


def test_overlap_ratio_uses_smaller_as_denominator():
    """小框完全落在大框内 → 交叠比 = 1.0（对小框而言全被覆盖）。"""
    assert overlap_ratio((0, 0, 100, 100), (10, 10, 10, 10)) == 1.0


def test_overlap_ratio_half():
    assert abs(overlap_ratio((0, 0, 10, 10), (5, 0, 10, 10)) - 0.5) < 1e-9


def test_out_of_bounds_detects_overflow():
    assert out_of_bounds((1672, 941, 10, 10), (1672, 941)) is False
    assert out_of_bounds((1670, 941, 10, 10), (1672, 941)) is True
    assert out_of_bounds((-1, 0, 10, 10), (1672, 941)) is True


def test_out_of_bounds_allows_touching_edge():
    """右边缘刚好贴齐不算越界（等号边界）。"""
    assert out_of_bounds((1662, 931, 10, 10), (1672, 941)) is False
```

`tests/conftest.py`（本 task 只需要空壳，后续 task 追加 fixture）：

```python
import pathlib
import sys

# 让 `import qa.xxx` 在未安装包的情况下也能工作
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_geometry.py -v`
Expected: FAIL —— `ModuleNotFoundError: No module named 'qa'`

- [ ] **Step 3: 写最小实现**

`qa_v2/__init__.py`（空文件）。

`qa_v2/geometry.py`：

```python
"""坐标换算与槽位矩形运算。

**为什么这个模块存在**：QA 判据全部建立在「槽位矩形内应有该槽位的字」上，
矩形取错位置，判据就退化成「这块地方有没有深色像素」——而插画上到处都是。

E11 实测的反面教材：qa_all.py 未做 plate→canvas 换算，P5 采到香炉木架
（墨像素 32062）而非文字（2229），判据恒真，"8/8 通过"是假的。

坐标空间（务必分清）：
  * 板面空间 —— slots.json 里的 x/y/w/h，尺寸见各页 plate（1672×941 或 1920×1080）
  * 画布空间 —— 渲染帧像素，恒为 CANVAS；PlatePage 用 objectFit:"cover" 铺满
OCR 返回的 rec_boxes 已在画布空间，**不要再乘缩放**。
"""
from typing import Sequence, Tuple

CANVAS = (1920, 1080)
Rect = Tuple[int, int, int, int]


def scale_of(plate: Sequence[int]) -> Tuple[float, float, float]:
    """cover 缩放系数与居中偏移，返回 (scale, offset_x, offset_y)。"""
    pw, ph = plate[0], plate[1]
    s = max(CANVAS[0] / pw, CANVAS[1] / ph)
    return s, (CANVAS[0] - pw * s) / 2.0, (CANVAS[1] - ph * s) / 2.0


def plate_to_canvas(
    plate: Sequence[int], x: float, y: float, w: float, h: float
) -> Rect:
    """板面坐标 → 画布像素矩形（四舍五入到 int）。"""
    s, ox, oy = scale_of(plate)
    return (
        int(round(ox + x * s)),
        int(round(oy + y * s)),
        int(round(w * s)),
        int(round(h * s)),
    )


def overlap_ratio(a: Rect, b: Rect) -> float:
    """交叠面积占较小矩形面积的比例；无交叠返回 0.0。"""
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ix = min(ax + aw, bx + bw) - max(ax, bx)
    iy = min(ay + ah, by + bh) - max(ay, by)
    if ix <= 0 or iy <= 0:
        return 0.0
    inter = ix * iy
    smaller = min(aw * ah, bw * bh)
    if smaller <= 0:
        return 0.0
    return inter / smaller


def out_of_bounds(rect: Rect, plate: Sequence[int]) -> bool:
    """槽位矩形是否越出板面边界。"""
    x, y, w, h = rect
    return x < 0 or y < 0 or x + w > plate[0] or y + h > plate[1]
```

- [ ] **Step 4: 跑测试确认通过**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_geometry.py -v`
Expected: PASS —— 11 passed

- [ ] **Step 5: 提交**

```bash
cd /tmp/chemistry-video
git add qa/__init__.py qa/geometry.py tests/conftest.py tests/test_geometry.py
git commit -m "feat(qa): 坐标换算与矩形运算

plate→canvas cover 换算是所有渲染判据的前提。qa_all.py 曾缺这一步，
E11 P5 采到插画（墨 32062）而非文字（2229），判据恒真。
E11 实测锚点已写成回归测试。"
```

---

