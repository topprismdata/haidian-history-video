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


import numpy as np
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
        for x in range(pad_x + 10, pad_x + w - size + 1, size):
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
