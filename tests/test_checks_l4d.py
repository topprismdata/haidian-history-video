# -*- coding: utf-8 -*-
"""L4-d 引文一致性测试（2026-10-02，E12/E13 盲区补）。

校准集：E12《苏州街》p6 真实事故——口播「震钧写下五个字：今已毁尽」，
画面即四字原文，观者同秒可证伪。本文件第一个用例就是它的回归钉。
"""
from qa_v2.data import Episode, Page, Slot, TextItem
from qa_v2.frames import OcrResult
from qa_v2.checks_content import check_l4d

PLATE = (1920, 1080)


def _ep(narration: dict, numbers=(1, 6)) -> Episode:
    pages = [Page(n, PLATE, [], []) for n in numbers]
    ep = Episode("suzhoujie", pages, [(0, 660)] * len(numbers))
    ep.narration = narration          # 测试直接注入，不走 narration/all.json
    return ep


def test_e12_p6_regression_stated_five_actual_four():
    """E12 p6 原始事故文案：写「五个字」，引文实为 4 字 → 必须抓。"""
    ep = _ep({6: "震钧在《天咫偶闻》里写下五个字：今已毁尽。"})
    fs = check_l4d(ep)
    hits = [f for f in fs if f.code == "QUOTE_COUNT_MISMATCH"]
    assert len(hits) == 1
    f = hits[0]
    assert f.page == 6 and f.level == "fail"
    assert f.detail["stated"] == 5 and f.detail["actual"] == 4


def test_corrected_four_chars_passes():
    """E12 v2 修正后文案：四个字+四字引文 → 无 finding。"""
    ep = _ep({6: "震钧在《天咫偶闻》里写下四个字：今已毁尽。"})
    assert check_l4d(ep) == []


def test_count_after_quote_also_caught():
    """计数词在引文之后（「……」四个字）同样覆盖。"""
    ep = _ep({1: "碑上刻着「永定河神」六个大字，笔力遒劲。"})
    hits = [f for f in check_l4d(ep) if f.code == "QUOTE_COUNT_MISMATCH"]
    assert len(hits) == 1 and hits[0].detail["actual"] == 4


def test_digit_count_and_ten_char_quote_pass():
    """阿拉伯数字计数、十字引文、引文内标点不计入，均应通过。"""
    ep = _ep({1: "匾上写的是「永定河神庙」5 个字。"})
    assert check_l4d(ep) == []
    ep2 = _ep({1: "他只留下「一二三四五六七八九十」十个字。"})
    assert check_l4d(ep2) == []


def test_short_or_no_count_quotes_ignored():
    """无计数词的普通引文、单字引文不产生 finding。"""
    ep = _ep({1: "这里就是「中关」的「关」字来历，与「坟地」有关。"})
    assert check_l4d(ep) == []


def test_quote_on_screen_ocr_verification():
    """--ocr：引文在 OCR 文本中 → 无 warn；缺失 → warn 不 fail。"""
    ep = _ep({6: "震钧写下四个字：今已毁尽，至今读来刺目。"})
    hit = OcrResult(["画面上 今已毁尽"], [[10, 10, 200, 60]], [0.97])
    assert check_l4d(ep, {6: hit}) == []
    miss = OcrResult(["画面上别的字"], [[10, 10, 200, 60]], [0.97])
    fs = check_l4d(ep, {6: miss})
    assert [f.code for f in fs] == ["QUOTE_NOT_ON_SCREEN"]
    assert fs[0].level == "warn"


def test_quote_trad_simp_folded_for_screen_check():
    """上屏核验两侧走同一归一：口播繁体引文 vs OCR 简体文本要能对上。"""
    ep = _ep({6: "旗籍写作「正黃旗」，与画面一致。"})
    o = OcrResult(["正黄旗 三个字"], [[10, 10, 200, 60]], [0.97])
    assert check_l4d(ep, {6: o}) == []


def test_no_narration_skips():
    """没有口播稿 → skip（不算通过），与其他层同一纪律。
    用不可解析的假集名，避免碰真实 suzhoujie 的 narration/all.json。"""
    ep = Episode("__l4d_test__", [Page(1, PLATE, [], [])], [(0, 660)])
    fs = check_l4d(ep)
    assert len(fs) == 1 and fs[0].code == "NO_NARRATION"
    assert fs[0].level == "skip"


def test_numeric_quote_skips_screen_check():
    """shucun P2 实测：数字性引文（量词短语）归 L4-c 管，屏检跳过。"""
    ep = _ep({2: "鼎盛时房数「一千五百多间」，规模惊人。"})
    miss = OcrResult(["画面只有数字"], [[10, 10, 200, 60]], [0.97])
    assert check_l4d(ep, {2: miss}) == []


def test_excerpt_of_quote_counts_as_on_screen():
    """shucun P7 实测：画面节引上谕（只摘「移驻树村」），≥4 字片段命中
    即视为上屏，不告警。"""
    ep = _ep({7: "上谕有言：「所有圆明园副将，著移驻树村。」"})
    o = OcrResult(["副将移驻树村"], [[10, 10, 300, 60]], [0.97])
    assert check_l4d(ep, {7: o}) == []


def test_content_mismatch_still_warns():
    """屏检的真实价值：计数对但引文内容与画面不符（今已 vs 至今）→ warn。"""
    ep = _ep({6: "震钧写下四个字：至今毁尽。"})
    o = OcrResult(["画面：今已毁尽"], [[10, 10, 200, 60]], [0.97])
    fs = check_l4d(ep, {6: o})
    assert [f.code for f in fs] == ["QUOTE_NOT_ON_SCREEN"]
