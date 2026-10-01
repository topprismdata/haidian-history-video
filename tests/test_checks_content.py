"""L4 内容闭环：槽里的字，对不对。

这是旧 QA 完全做不到的一层。E11 真实发生过的错：
P8 口播写「各占了一处」后又说树村占两处，算术自相矛盾 ——
深色墨判据对此毫无察觉。
"""
import pytest

from qa_v2.data import Page, Slot, TextItem
from qa_v2.frames import OcrResult
from qa_v2.checks_content import check_l4a, check_l4b, load_names

PLATE = (1920, 1080)


def _page(items, number=1):
    slots = [Slot(i.slot_id, 0, 0, 900, 120) for i in items]
    return Page(number, PLATE, slots, items)


def _ti(sid, text, size=20, kind=None):
    return TextItem(sid, text, size, True, kind)


def _ocr(page, mapping):
    """按 slotId -> 读回文本 构造 OcrResult（box 落在槽内）。"""
    texts, boxes, scores = [], [], []
    for k, v in mapping.items():
        for t in v:
            texts.append(t)
            boxes.append((10, 10, 400, 50))
            scores.append(0.99)
    return OcrResult(texts, boxes, scores)


# ── L4-a 数字 ──
def test_l4a_passes_when_numbers_match():
    p = _page([_ti("r1_total", "1550")])
    assert [f for f in check_l4a(p, _ocr(p, {"r1_total": ["1550"]}))
            if f.level == "fail"] == []


def test_l4a_catches_wrong_number():
    """「1485」写成「1486」—— 深色墨判据查不出，这里能查出。"""
    p = _page([_ti("r1_total", "1485")])
    fs = [f for f in check_l4a(p, _ocr(p, {"r1_total": ["1486"]}))
          if f.level == "fail"]
    assert len(fs) == 1 and fs[0].code == "NUMBER_MISMATCH"


def test_l4a_accepts_chinese_numeral():
    p = _page([_ti("note", "一千二百五十间")])
    assert [f for f in check_l4a(p, _ocr(p, {"note": ["1250 间"]}))
            if f.level == "fail"] == []


def test_l4a_accepts_speech_year():
    p = _page([_ti("sub", "雍正二年（1724）")])
    assert [f for f in check_l4a(p, _ocr(p, {"sub": ["一七二四年"]}))
            if f.level == "fail"] == []


def test_l4a_ignores_punctuation_only_diff():
    """E11 实测：OCR 噪声仅标点规范化。"""
    p = _page([_ti("sub", "树村·圆明园正北")])
    assert [f for f in check_l4a(p, _ocr(p, {"sub": ["树村.圆明园正北"]}))
            if f.level == "fail"] == []


def test_l4a_no_numbers_is_trivially_ok():
    p = _page([_ti("title", "一个村子，三重身份")])
    assert [f for f in check_l4a(p, _ocr(p, {"title": ["一个村子，三重身份"]}))
            if f.level == "fail"] == []


def test_l4a_warns_on_high_unknown_rate():
    p = _page([_ti("x", "一七二四 9999 一二三四五六七")])
    fs = [f for f in check_l4a(p, _ocr(p, {"x": ["一七二四 9999 一二三四五六七"]}))
          if f.code == "NUMBER_UNKNOWN_RATE"]
    assert len(fs) == 1 and fs[0].level == "warn"


def test_l4a_ignores_tag_slot():
    """tag 槽没有数字且由 L6 独立检查，L4-a 跳过。"""
    p = Page(1, PLATE, [Slot("tag", 0, 0, 100, 40)], [_ti("tag", "标签 123", 20, kind="tag")])
    o = _ocr(p, {"tag": ["标签"]})
    assert check_l4a(p, o) == []


# ── L4-b 专名 ──
def test_l4b_passes_when_name_present():
    p = _page([_ti("dir", "树村西")])
    names = {"树村", "肖家河", "蓝靛厂"}
    assert [f for f in check_l4b(p, _ocr(p, {"dir": ["树村西"]}), names)
            if f.level == "fail"] == []


def test_l4b_catches_wrong_place_name():
    p = _page([_ti("dir", "树村西")])
    names = {"树村", "肖家河"}
    fs = [f for f in check_l4b(p, _ocr(p, {"dir": ["肖家河西"]}), names)]
    assert any(f.code == "PROPER_NAME_MISSING" for f in fs)


def test_l4b_skips_when_names_table_empty():
    """专名表缺失必须 skip 而非 pass —— 否则新集漏填就静默通过。"""
    p = _page([_ti("dir", "树村西")])
    fs = check_l4b(p, _ocr(p, {"dir": ["树村西"]}), set())
    assert [f for f in fs if f.code == "NO_NAMES_TABLE"]


def test_l4b_ignores_tag_slot():
    """tag 槽跳过专名检查。"""
    p = Page(1, PLATE, [Slot("tag", 0, 0, 100, 40)], [_ti("tag", "树村标签", 20, kind="tag")])
    names = {"树村"}
    o = _ocr(p, {"tag": ["标签"]})
    assert check_l4b(p, o, names) == []


def test_l4_handles_missing_slot_gracefully():
    """文案引用了不存在的槽时，_ocr_text_for 返回空串，不抛异常崩溃。"""
    p = Page(1, PLATE, [], [_ti("nonexistent", "树村 1550")])
    names = {"树村"}
    o = OcrResult([], [], [])
    fs_a = check_l4a(p, o)
    assert any(f.code == "NUMBER_MISMATCH" for f in fs_a)
    fs_b = check_l4b(p, o, names)
    assert any(f.code == "PROPER_NAME_MISSING" for f in fs_b)


def test_names_file_loads():
    names = load_names()
    assert "树村" in names
    assert len(names) > 20
