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
