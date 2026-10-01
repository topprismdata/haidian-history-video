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
