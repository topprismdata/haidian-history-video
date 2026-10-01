"""L1 数据一致性：纯数据检查，不渲帧，<0.1s/页。"""
import pytest

from qa_v2.data import Episode, Page, Slot, TextItem
from qa_v2.checks_data import (
    check_l1, OVERLAP_FAIL_RATIO, MIN_SLOT_W, MIN_SLOT_H,
    check_l2, estimate_lines, OVERFLOW_TOLERANCE, item_lh,
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
