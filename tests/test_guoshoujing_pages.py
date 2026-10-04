# -*- coding: utf-8 -*-
"""E29《郭守敬·一泉入都》页面与槽位系统测试.

基线判据沿用 test_shifangpujue_pages.py（8 页 / 双向匹配 / backing / 画布 /
屏显数字 ⊆ 口播 / 运行时同步），另加本集红线：

  V-NC02  正片 slots 禁出现「郭守敬开凿长河/开挖长河」——长河河道先在
  V-NC03  「泽被六百年/至今仍在供水」零命中——延祐元年已不能通流
  V-NC04  禁「精确到小数点」——原文是刻分制
  V-NC06  「海拔」只准出现在否定语境；必须给出「以海平面比较」正表述
  V-NC05  27 所为穷举名单口径（「凡二十七所」须逐字上屏）
  屏显纪律  禁 U+3007；禁 ASCII 数字（全字形汉字纪年）；SVG 只准画图形禁 <text>；
            示意/排印件 caption 必须带红线标签

Python 3.9.6 兼容: 禁 X | None, 禁 match.
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from qa_v2.data import parse_pages_config
from qa_v2.normalize import extract_numbers

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE_DATA = ROOT / "remotion-template" / "src" / "guoshoujing" / "data"
SYNC_DATA = pathlib.Path("/tmp/chemistry-video/src/guoshoujing/data")
PAGES_DIR = ROOT / "remotion-template" / "src" / "guoshoujing" / "pages"
NARR_FILE = ROOT / "guoshoujing_video" / "narration" / "all.json"

MIN_YEAR = 10  # 只对纪年量级数字做子集判据（<10 的「一/三/六」等会被普通词误抓）


def _slots_data():
    return json.loads((TEMPLATE_DATA / "slots.json").read_text(encoding="utf-8"))


def _cfg():
    return parse_pages_config((TEMPLATE_DATA / "pages.config.ts").read_text(encoding="utf-8"))


def _narration():
    return json.loads(NARR_FILE.read_text(encoding="utf-8"))


def _blob():
    return " ".join(it.text for items in _cfg().values() for it in items)


# ==================================================================
# 基线判据（照 shifangpujue 范式）
# ==================================================================

def test_slots_json_has_8_pages():
    data = _slots_data()
    assert len(data) == 8
    for i in range(1, 9):
        k = f"p{i:02d}"
        assert k in data, f"缺少 {k}"
        assert data[k]["plate"] == [1920, 1080]
        assert len(data[k]["slots"]) >= 5


def test_slots_and_pages_config_bidirectional_match():
    cfg = _cfg()
    slots = _slots_data()
    assert len(cfg) == 8, f"pages.config.ts 解析页数不为 8: {len(cfg)}"
    for i in range(1, 9):
        k = f"p{i:02d}"
        slot_ids = {s["id"] for s in slots[k]["slots"]}
        cfg_ids = {it.slot_id for it in cfg[i] if it.slot_id}
        assert not (slot_ids - cfg_ids), f"{k} slots.json 中的槽位未声明: {slot_ids - cfg_ids}"
        assert not (cfg_ids - slot_ids), f"{k} pages.config.ts 中的槽位未在 slots.json: {cfg_ids - slot_ids}"


def test_all_text_slots_have_backing():
    cfg = _cfg()
    for pno, items in cfg.items():
        for it in items:
            if it.kind == "photo":
                continue
            assert it.backing, f"P{pno} 槽位 {it.slot_id} 缺少 backing: true (物理隔离红线)"


def test_all_slots_within_canvas():
    for page_key, pdata in _slots_data().items():
        for s in pdata["slots"]:
            x, y, w, h = s["x"], s["y"], s["w"], s["h"]
            assert x >= 0 and y >= 0, f"{page_key}/{s['id']} 坐标为负"
            assert w > 0 and h > 0, f"{page_key}/{s['id']} 宽高必须正数"
            assert x + w <= 1920, f"{page_key}/{s['id']} 宽度越界: {x}+{w}"
            assert y + h <= 1080, f"{page_key}/{s['id']} 高度越界: {y}+{h}"


def test_screen_years_subset_of_spoken():
    cfg = _cfg()
    narr = _narration()
    for pno in range(1, 9):
        k = f"p{pno:02d}"
        spoken = {n for n in extract_numbers(narr[k]) if n >= MIN_YEAR}
        for it in cfg[pno]:
            if it.kind == "photo" or it.slot_id is None:
                continue
            if "quote" in it.slot_id:
                continue  # 逐字引文豁免
            screen = {n for n in extract_numbers(it.text) if n >= MIN_YEAR}
            excess = screen - spoken
            assert not excess, (
                f"P{pno} 槽位 {it.slot_id} 屏显纪年 {sorted(excess)} 未在当页口播念出 "
                f"(口播含 {sorted(spoken)})"
            )


def test_runtime_data_synced():
    assert SYNC_DATA.exists(), f"运行时目录不存在: {SYNC_DATA}"
    for filename in ["slots.json", "pages.config.ts", "pageMap.ts"]:
        src = TEMPLATE_DATA / filename
        dst = SYNC_DATA / filename
        assert dst.exists(), f"运行时未同步: {filename}"
        assert src.read_text(encoding="utf-8") == dst.read_text(encoding="utf-8"), (
            f"正本与副本不一致: {filename}"
        )


# ==================================================================
# E29 专属红线
# ==================================================================

class TestE29ChangheNotDugByGuo:
    """V-NC02：长河河道先在，正片禁「郭守敬开凿长河/开挖长河」。"""

    def test_ban_dug_wording(self):
        blob = _blob()
        for wrong in ("开凿长河", "开挖长河", "郭守敬所开", "长河是郭守敬开的"):
            assert wrong not in blob, "V-NC02 违规：屏显出现「%s」" % wrong

    def test_p7_states_river_precedes(self):
        p7 = " ".join(it.text for it in _cfg()[7])
        assert "长河不是他开的" in p7, "P7 必须显式澄清长河非郭守敬所开"
        assert "先在" in p7, "P7 必须给出「河道先在」依据"

    def test_p7_names_qing_gazetteer(self):
        p7 = " ".join(it.text for it in _cfg()[7])
        assert "清代才叫开" in p7, "P7 必须说明「长河」地名系清代口径"


class TestE29NoSixHundredYearsBlessing:
    """V-NC03：「泽被六百年/至今仍在供水」零命中。"""

    def test_ban_blessing_wording(self):
        blob = _blob()
        for wrong in ("泽被六百年", "泽被后世", "至今仍在供水", "沿用至今六百年"):
            assert wrong not in blob, "V-NC03 违规：屏显出现「%s」" % wrong

    def test_p7_chain_has_yanyou(self):
        p7 = " ".join(it.text for it in _cfg()[7])
        assert "源泉微細，不能通流" in p7 or "源泉微细" in p7.replace("細", "细"), \
            "P7 必须给出延祐元年淤塞书证"
        assert "卒前两年" in p7, "P7 必须点明「郭守敬卒前两年」（泉死得比人早）"


class TestE29RegressionYearFormat:
    """V-NC04：原文是百刻-百分制，禁「精确到小数点」。"""

    def test_no_decimal_point_claim(self):
        blob = _blob()
        for wrong in ("精确到小数点", "小数点后四位"):
            assert wrong not in blob, "V-NC04 违规：屏显出现「%s」" % wrong

    def test_p5_has_verbatim_and_conversion(self):
        p5 = " ".join(it.text for it in _cfg()[5])
        assert "三百六十五日二十四刻二十五分" in p5, "P5 必须逐字上屏原文刻分形态"
        assert "三百六十五点二四二五日" in p5, "P5 必须给出换算值（挂「据现代学者换算」）"
        assert "据现代学者换算" in p5, "换算必须挂 L4 口径标签"

    def test_p5_banxing_same_year(self):
        p5 = " ".join(it.text for it in _cfg()[5])
        assert "其年冬，颁行天下" in p5 and "不是次年" in p5, \
            "P5 必须钉死「其年冬颁行」、禁「次年颁行」"


class TestE29HaibaPhrasing:
    """V-NC06：「海拔」只准否定语境；正表述为「以海平面比较」。"""

    def test_positive_phrase_present(self):
        p8 = " ".join(it.text for it in _cfg()[8])
        assert "以海平面比较" in p8, "P8 必须给出「以海平面比较地形高差」的正表述"

    def test_haiba_only_negated(self):
        blob = _blob()
        assert "发明了海拔" not in blob, "V-NC06 违规：「发明了海拔」任何语境禁用"
        for m in re.finditer("发明海拔", blob):
            pre = blob[max(0, m.start() - 2):m.start()]
            assert pre.endswith("不是"), (
                "V-NC06 违规：「发明海拔」出现在非否定语境：%r"
                % blob[max(0, m.start() - 12):m.start() + 8]
            )


class TestE29Sihai27:
    """V-NC05：二十七所穷举名单口径，今海淀无站。"""

    def test_p4_quote_verbatim_27suo(self):
        p4 = " ".join(it.text for it in _cfg()[4])
        assert "四海測驗，凡二十七所。" in p4, "P4 必须逐字上屏「四海測驗，凡二十七所。」"

    def test_no_haidian_station_claim(self):
        p4 = " ".join(it.text for it in _cfg()[4])
        assert "无一站" in p4, "P4 必须显式说明今海淀境内无观测站"
        blob = _blob()
        for wrong in ("测量了整个中国", "走遍西藏", "测量长城"):
            assert wrong not in blob, "V-NC05 违规：屏显出现「%s」" % wrong


class TestE29BaifuRoute:
    """P6 主轴：白浮村神山泉＋里程单口径＋示意免责。"""

    def test_p6_verbatim_route(self):
        p6 = " ".join(it.text for it in _cfg()[6])
        assert "西折而南，經瓮山泊，自西水門入城，環匯於積水潭" in p6, \
            "P6 必须逐字上屏《元史》线路原文（含「經」字——瓮山泊先在）"

    def test_p6_single_length_caliber(self):
        p6 = " ".join(it.text for it in _cfg()[6])
        assert "一百六十四里一百四步" in p6, "P6 必须用《元史》唯一里程口径"
        assert "一百六十里" not in p6 and "二百里" not in p6, "V-NC09：混写口径禁用"

    def test_p6_schematic_disclaimer(self):
        p6 = " ".join(it.text for it in _cfg()[6])
        assert "非测绘拓扑" in p6 or "非測繪拓撲" in p6, "P6 示意图必须带免责标签"


class TestE29ScreenHygiene:
    """屏显纪律：U+3007 零、ASCII 数字零（全字形）、SVG 禁 <text>、caption 红线标签。"""

    def test_no_ideographic_zero(self):
        for pno, items in _cfg().items():
            for it in items:
                assert "\u3007" not in it.text, "P%d %s 含 U+3007 圆圈数字" % (pno, it.slot_id)

    def test_no_ascii_digits_in_text_slots(self):
        for pno, items in _cfg().items():
            for it in items:
                if it.kind == "photo":
                    continue
                assert not re.search(r"[0-9]", it.text), (
                    "P%d %s 含 ASCII 数字（屏显一律全字形汉字纪年）：%r"
                    % (pno, it.slot_id, it.text[:24])
                )

    def test_svg_pages_draw_no_text(self):
        """🔴 E26 教训：SVG 硬编码文字会让负控制误报「判据恒真」。SVG 只准画图形。"""
        for f in sorted(PAGES_DIR.glob("Page0*.tsx")):
            src = f.read_text(encoding="utf-8")
            assert "<text" not in src, f"{f.name} 含 SVG <text>（文字必须走槽位）"
            assert "<tspan" not in src, f"{f.name} 含 SVG <tspan>"

    def test_photo_captions_carry_redline(self):
        for f in sorted(PAGES_DIR.glob("Page0*.tsx")):
            src = f.read_text(encoding="utf-8")
            caps = re.findall(r"caption:\s*\"([^\"]+)\"", src)
            if f.name == "Page08.tsx":
                continue  # node 槽无 PhotoFrame caption
            assert caps, f"{f.name} 未发现任何 caption"
            for c in caps:
                assert re.search(r"非实物照片|非原刊扫描|非测绘拓扑|非地图投影", c), (
                    f"{f.name} caption 缺红线标签: {c}"
                )

    def test_no_fabricated_realphoto_claims(self):
        """示意资产绝不可标注成「实景/实拍/拓片」；「非实物照片/非原刊扫描」为合法红线标签。"""
        for f in sorted(PAGES_DIR.glob("Page0*.tsx")):
            src = f.read_text(encoding="utf-8")
            for wrong in ("实景", "实拍", "拓片"):
                assert wrong not in src, f"{f.name} caption 疑似伪造实物 claims: {wrong}"
            # 否定形（非X）合法，肯定形非法
            for m in re.finditer("(实物照片|原刊扫描)", src):
                pre = src[max(0, m.start() - 1):m.start()]
                assert pre == "非", (
                    f"{f.name} 出现非否定形「{m.group(1)}」"
                )


class TestE29ProperNounsOnScreen:
    def test_key_nouns_on_screen(self):
        blob = _blob()
        for nm in ("郭守敬", "白浮泉", "瓮山泊", "通惠河",
                   "广源闸", "授时历", "昌平", "海淀", "登封"):
            assert nm in blob, "屏显缺少专名「%s」" % nm
        # 引文照录繁体（V-NC08 繁简异体照录），简繁任一形即过
        assert "积水潭" in blob or "積水潭" in blob, "屏显缺少专名「积水潭/積水潭」"

    def test_p8_sum_present(self):
        p8 = " ".join(it.text for it in _cfg()[8])
        assert "泉死得比人早" in p8, "P8 必须落到本集主轴句"
