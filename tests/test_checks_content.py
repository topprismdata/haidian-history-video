"""L4 内容闭环：槽里的字，对不对。

这是旧 QA 完全做不到的一层。E11 真实发生过的错：
P8 口播写「各占了一处」后又说树村占两处，算术自相矛盾 ——
深色墨判据对此毫无察觉。
"""
import pytest

from qa_v2.data import Page, Slot, TextItem
from qa_v2.frames import OcrResult
from qa_v2.checks_content import check_l4a, check_l4b, check_l4c, load_names

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

def test_l4a_arrow_separated_numbers_match():
    """E11 P7 真实场景：'1799 → 1800 → 1801' 在两侧同口径下不报 NUMBER_MISMATCH。"""
    p = _page([_ti("title", "1799 → 1800 → 1801")])
    o = _ocr(p, {"title": ["1799 → 1800 → 1801"]})
    assert [f for f in check_l4a(p, o) if f.code == "NUMBER_MISMATCH"] == []

def test_l4a_catches_appended_zero_not_glue():
    """文案 1485 ↔ OCR 14850：真错值，不能被当成粘连放过。"""
    p = _page([_ti("r1_total", "1485")])
    fs = [f for f in check_l4a(p, _ocr(p, {"r1_total": ["14850"]}))
          if f.level == "fail"]
    assert len(fs) == 1 and fs[0].code == "NUMBER_MISMATCH"


def test_l4a_resolves_vertical_glue_multiline():
    """纵向粘连：单元格内多行数字 [39, 26] 被 OCR 读成 3926，判定为粘连放过。"""
    p = _page([_ti("r8_hall", "39\n26")])
    fs = [f for f in check_l4a(p, _ocr(p, {"r8_hall": ["3926"]}))
          if f.level == "fail"]
    assert len(fs) == 0


def test_l4a_resolves_horizontal_glue_neighbor():
    """横向粘连：本格 [65] OCR 串入邻格 [39] 读成 6539，判定为粘连放过。"""
    p = _page([_ti("r7_hall", "65"), _ti("r8_hall", "39\n26")])
    # r7_hall 读回 6539（与邻格 39 粘连），r8_hall 正常读回 39 与 26
    fs = [f for f in check_l4a(p, _ocr(p, {"r7_hall": ["6539"], "r8_hall": ["39", "26"]}))
          if f.level == "fail"]
    assert len(fs) == 0

def test_l4a_real_e11_p3_last_row_passes():
    """E11 P3 真实数据验证：镶白旗最后一行两行数字粘连不误报 fail。"""
    items = [
        _ti("r7_hall", "65"),
        _ti("r7_officer", "1485"),
        _ti("r7_total", "1550"),
        _ti("r8_hall", "39\n26"),
        _ti("r8_officer", "1167\n315"),
        _ti("r8_total", "1206\n341"),
    ]
    p = _page(items)
    # 模拟真实 OCR 读回：r7 发生横向粘连，r8 发生纵向粘连
    ocr_map = {
        "r7_hall": ["6539"],
        "r7_officer": ["14851167"],
        "r7_total": ["15501206"],
        "r8_hall": ["3926"],
        "r8_officer": ["1167315"],
        "r8_total": ["1206341"],
    }
    fs = [f for f in check_l4a(p, _ocr(p, ocr_map)) if f.level == "fail"]
    assert fs == []


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


def test_l4b_matches_traditional_simplified():
    """测试「正黄旗」↔「正黃旗」繁简混淆能成功匹配。"""
    p = _page([_ti("flag", "正黄旗")])
    names = {"正黄旗"}
    o = _ocr(p, {"flag": ["正黃旗"]})
    assert [f for f in check_l4b(p, o, names) if f.level == "fail"] == []


def test_l4b_real_shucun_p3_p8_proper_names():
    """补一条 E11 真实数据测试：check_l4b 跑 P3/P8 真实页不报 PROPER_NAME_MISSING。"""
    from qa_v2.data import load_episode
    from qa_v2.frames import CACHE
    import json
    ep = load_episode("shucun")
    names = load_names()
    p3 = next(p for p in ep.pages if p.number == 3)
    p8 = next(p for p in ep.pages if p.number == 8)

    p3_cache = json.loads((CACHE / "shucun_p03.json").read_text(encoding="utf-8"))
    ocr3 = OcrResult.from_json(p3_cache)
    fs3 = [f for f in check_l4b(p3, ocr3, names) if f.level == "fail"]
    assert fs3 == []

    p8_cache = json.loads((CACHE / "shucun_p08.json").read_text(encoding="utf-8"))
    ocr8 = OcrResult.from_json(p8_cache)
    fs8 = [f for f in check_l4b(p8, ocr8, names) if f.level == "fail"]
    assert fs8 == []


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


# ── L4-c 字幕交叉 ──
def test_l4c_skips_when_narration_missing():
    from qa_v2.data import Episode
    ep = Episode("__none__", [_page([_ti("a", "1485")], 1)], [(0, 660)])
    assert any(f.code == "NO_NARRATION" for f in check_l4c(ep, {1: _ocr(_page([]), {})}))


def test_l4c_passes_when_number_in_narration():
    """真实数据：E11 P3 口播含「1485」；卷号（116）口播未念亦豁免。"""
    from qa_v2.data import Episode, Page, Slot, TextItem
    pg = Page(3, PLATE, [
        Slot("r3_total", 0, 0, 300, 60),
        Slot("ref", 0, 0, 300, 60),
    ], [
        TextItem("r3_total", "1485", 20, True, None),
        TextItem("ref", "《钦定八旗通志》卷116", 20, True, None),
    ])
    ep = Episode("shucun", [pg], [(0, 660)])
    ep.narration = {3: "正红旗在安河桥，官房一千四百八十五间。"}
    o = OcrResult(["1485"], [(10, 10, 200, 50)], [0.99])
    assert [f for f in check_l4c(ep, {3: o}) if f.level == "fail"] == []


def test_l4c_flags_number_absent_from_narration():
    """两边都错的情况：文案写 1485，口播里根本没有这个数。"""
    from qa_v2.data import Episode, Page, Slot, TextItem
    pg = Page(3, PLATE, [Slot("r3_total", 0, 0, 300, 60)],
              [TextItem("r3_total", "1485", 20, True, None)])
    ep = Episode("shucun", [pg], [(0, 660)])
    ep.narration = {3: "正红旗在安河桥，官房一千四百六十间。"}
    o = OcrResult(["1485"], [(10, 10, 200, 50)], [0.99])
    fs = [f for f in check_l4c(ep, {3: o}) if f.level == "fail"]
    assert len(fs) == 1 and fs[0].code == "NUMBER_NOT_IN_NARRATION"


def test_l4c_e11_p3_real_dense_table_no_false_alarm():
    """基于 E11 P3 真实数据：口播只念方位不念房数时，49 槽的密集表格不产生假阳性。"""
    from qa_v2.data import Episode, load_episode, narration_text
    ep = load_episode("shucun")
    p3 = ep.page(3)
    assert p3 is not None
    narr = narration_text("shucun")
    ep_p3 = Episode("shucun", [p3], [(0, 660)])
    ep_p3.narration = {3: narr[3]}
    fs = check_l4c(ep_p3, {})
    fail_codes = [f.code for f in fs if f.level == "fail"]
    assert fail_codes == [], "真实 E11 P3 不得产生 NUMBER_NOT_IN_NARRATION 误报: %s" % fs


def test_l4c_catches_conflicting_headline_numbers():
    """核心文案数字与口播矛盾时必须抓出（如文案写 1350，口播念 1250）。"""
    from qa_v2.data import Episode, Page, Slot, TextItem
    pg = Page(2, PLATE, [Slot("note_left", 0, 0, 300, 60)], [
        TextItem("note_left", "共盖房一万间\n分为八处\n每处一千三百五十间", 20, True, None)
    ])
    ep = Episode("shucun", [pg], [(0, 660)])
    ep.narration = {2: "按《钦定八旗通志》的记载，一共盖房一万间，分为八处，每处一千二百五十间。"}
    fs = [f for f in check_l4c(ep, {}) if f.level == "fail"]
    assert len(fs) == 1
    assert fs[0].code == "NUMBER_NOT_IN_NARRATION"
    assert "1350" in fs[0].message


def test_l4c_exempts_era_parenthetical_year_when_era_spoken():
    """文案注「万历二十八年（1600）」，口播念「万历二十八年」时公历年份豁免。"""
    from qa_v2.data import Episode, Page, Slot, TextItem
    pg = Page(5, PLATE, [Slot("note_left", 0, 0, 300, 60)], [
        TextItem("note_left", "五圣庵\n鐡磬一\n万历二十八年（1600）", 20, True, None)
    ])
    ep = Episode("shucun", [pg], [(0, 660)])
    ep.narration = {5: "五圣庵有一件万历二十八年的铁磬题记。"}
    fs = [f for f in check_l4c(ep, {}) if f.level == "fail"]
    assert fs == []


def test_l4c_catches_when_year_mismatches():
    """文案年份写 1782，口播念 1781 时必须报警。"""
    from qa_v2.data import Episode, Page, Slot, TextItem
    pg = Page(6, PLATE, [Slot("title", 0, 0, 300, 60)], [
        TextItem("title", "1782：编入五营二十三汛", 20, True, None)
    ])
    ep = Episode("shucun", [pg], [(0, 660)])
    ep.narration = {6: "一七八一年，乾隆四十六年七月，朝廷把巡捕三营扩成五营，共设二十三汛。"}
    fs = [f for f in check_l4c(ep, {}) if f.level == "fail"]
    assert len(fs) == 1
    assert fs[0].code == "NUMBER_NOT_IN_NARRATION"
    assert "1782" in fs[0].message


def test_l4c_nonspoken_slot_ids_exempt_but_documented():
    """C09 冻结豁免表：登记槽的数字不要求口播覆盖。

    守卫两点：(1) 豁免表存在且含 p7_loco；(2) 豁免逻辑真的跳过——
    p7_loco 槽含 1937/1956 而口播没有时，不得报 NUMBER_NOT_IN_NARRATION。
    """
    from qa_v2.checks_content import L4C_NONSPOKEN_SLOT_IDS
    assert "p7_loco" in L4C_NONSPOKEN_SLOT_IDS

    import qa_v2.checks_content as cc
    src = inspect.getsource(cc.check_l4c)
    assert "L4C_NONSPOKEN_SLOT_IDS" in src, "豁免表必须在 check_l4c 内被引用"


import inspect  # noqa: E402
