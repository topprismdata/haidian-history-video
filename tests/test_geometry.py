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
    assert out_of_bounds((1672, 941, 10, 10), (1920, 1080)) is False
    assert out_of_bounds((1670, 941, 10, 10), (1672, 941)) is True
    assert out_of_bounds((-1, 0, 10, 10), (1672, 941)) is True


def test_out_of_bounds_allows_touching_edge():
    """右边缘刚好贴齐不算越界（等号边界）。"""
    assert out_of_bounds((1662, 931, 10, 10), (1672, 941)) is False
