# -*- coding: utf-8 -*-
"""E24《十方普觉寺·阳台山麓的千年清水院》Task 5: 页面与槽位系统测试.

验证:
1. slots.json 8 页完整, 与 pages.config.ts 槽位 id 1:1 双向一致;
2. 全部非 photo 槽位配置 backing: true (物理隔离红线);
3. 槽位坐标在 1920×1080 画布内, 宽高为正;
4. 屏显纪年数字（>=10）必须是当页口播数字的子集;
   逐字引文槽（slot_id 含 _quote）豁免——引文原样保留年号汉字，
   改写引文以迎合数字判据属篡改书证。红线改由 qa_v2 L4-c 承担。
5. remotion-template 与 /tmp/chemistry-video 副本一致性。
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from qa_v2.data import parse_pages_config
from qa_v2.normalize import extract_numbers

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE_DATA = ROOT / "remotion-template" / "src" / "shifangpujue" / "data"
SYNC_DATA = pathlib.Path("/tmp/chemistry-video/src/shifangpujue/data")
NARR_FILE = ROOT / "shifangpujue_video" / "narration" / "all.json"

MIN_YEAR = 10  # 只对纪年量级数字做子集判据（<10 的「一/三/六」等会被普通词误抓）


def _slots_data():
    return json.loads((TEMPLATE_DATA / "slots.json").read_text(encoding="utf-8"))


def _cfg():
    return parse_pages_config((TEMPLATE_DATA / "pages.config.ts").read_text(encoding="utf-8"))


def _narration():
    return json.loads(NARR_FILE.read_text(encoding="utf-8"))


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


def test_redline_no_fabricated_mansion_photo():
    """V-NC07：严禁 AI 生成辽代塔、碑形、契丹建筑或白玉兰复原图。"""
    cfg = _cfg()
    banned = ("仿古塔复原", "伪石匾", "虚构铜佛", "复原卧佛")
    for pno, items in cfg.items():
        for it in items:
            if it.kind != "photo":
                continue
            for b in banned:
                assert b not in it.text, f"P{pno} photo 槽疑似伪造复原图: {b}"


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
# E26 专属红线（🔴 三条判据纪律）
# ==================================================================

SEVEN_NAMES = ["兜率寺", "寿安山寺", "昭孝寺", "洪庆寺", "寿安禅林", "永安寺", "十方普觉寺"]


class TestE26SevenNames:
    """V-NC01：七个名号与年号一一对应，严禁笼统「数次易名」。"""

    def test_all_seven_names_on_screen(self):
        cfg = _cfg()
        blob = " ".join(
            it.text for items in cfg.values() for it in items
            if not it.slot_id or "photo" not in (it.slot_id or "")
        )
        for nm in SEVEN_NAMES:
            assert nm in blob, "V-NC01：屏显必须出现名号「%s」" % nm

    def test_no_vague_wording(self):
        cfg = _cfg()
        blob = " ".join(it.text for items in cfg.values() for it in items)
        for vague in ("数次易名", "历经多次改名", "屡次改名", "数次改名"):
            assert vague not in blob, "V-NC01 违规：笼统表述「%s」" % vague


class TestE26ArtifactAgeLayering:
    """V-NC02：铜卧佛系元代所铸，严禁「唐代遗存」。"""

    def test_wofoe_must_be_yuan(self):
        cfg = _cfg()
        p3 = " ".join(it.text for it in cfg[3])
        assert "元" in p3, "P3 必须标明铜卧佛铸于元代"
        for wrong in ("唐代遗存", "唐时铸", "唐代所铸"):
            assert wrong not in p3, "V-NC02 违规：P3 出现「%s」" % wrong

    def test_temple_is_tang(self):
        cfg = _cfg()
        p2 = " ".join(it.text for it in cfg[2])
        assert "唐太宗贞观年间" in p2, "P2 必须标明寺创于唐贞观年间"

    def test_gap_explicitly_stated(self):
        cfg = _cfg()
        p4 = " ".join(it.text for it in cfg[4])
        assert "六百余载" in p4, "P4 必须显式说明寺佛相隔年数"

    def test_cross_inference_forbidden(self):
        cfg = _cfg()
        p4 = " ".join(it.text for it in cfg[4])
        assert "反过" in p4 or "不可" in p4, "P4 必须显式禁止器物与建置年代互推"


class TestE26GuobaoAndLocation:
    """V-NC03 国保第五批 5-205；V-NC05 寿安山非香山。"""

    def test_guobao_fifth_batch_with_number(self):
        cfg = _cfg()
        p7 = " ".join(it.text for it in cfg[7])
        assert "第五批" in p7
        assert "5-205" in p7, "V-NC03：必须引编号 5-205"

    def test_no_first_batch_numbering(self):
        cfg = _cfg()
        p7 = " ".join(it.text for it in cfg[7])
        assert "1-75" not in p7, "🔴 1961 年首批无编号体系，严禁引用"

    def test_shi_fang_is_ten_not_six(self):
        """🔴 R2：原写「东西南北与四维上下六方」是算术错误（4+4+2=10）。"""
        cfg = _cfg()
        p6 = " ".join(it.text for it in cfg[6])
        assert "六方" not in p6, "🔴 「十方」是十个方位，屏显不得写成「六方」"
        assert "十个方位" in p6 or "十方" in p6

    def test_shuoan_not_xiangshan(self):
        cfg = _cfg()
        p7 = " ".join(it.text for it in cfg[7])
        assert "寿安山" in p7
        assert "不在香山" in p7, "V-NC05：必须显式澄清不在香山"

    def test_offer_temple_banned(self):
        cfg = _cfg()
        blob = " ".join(it.text for items in cfg.values() for it in items)
        for wrong in ("Offer寺", "Offer 寺"):
            assert wrong not in blob, "V-NC04 违规：谐音进入史实叙述"

    # 🔴 E26 判据设计教训：不能用 `1[4-9]\d\d` 抓四位公历 ——
    #    它会命中「二〇〇一年」这类全字形汉字里的相邻数字，产生必假的 fail。
    #    正确做法是查**阿拉伯年份黑名单**（只列本集真正禁止出现的写法）。
    BANNED_ARABIC_YEARS = ("1473", "1321", "1443", "1482", "1734", "2001", "627", "649", "1321")

    def test_banned_arabic_years_absent(self):
        """E24/E25 教训：屏显纪年一律用年号或全字形汉字，不写阿拉伯公历。"""
        cfg = _cfg()
        for pno, items in cfg.items():
            for it in items:
                if it.slot_id and ("photo" in it.slot_id or "quote" in it.slot_id):
                    continue
                for y in self.BANNED_ARABIC_YEARS:
                    assert y not in it.text, (
                        "P%d %s 含阿拉伯公历年份「%s」，应改用年号或全字形汉字"
                        % (pno, it.slot_id, y)
                    )

    def test_no_ideographic_zero(self):
        """E24 教训：U+3007 圆圈数字在宋体下不可见，OCR 会漏读。"""
        cfg = _cfg()
        for pno, items in cfg.items():
            for it in items:
                assert "\u3007" not in it.text, "P%d %s 含 U+3007 圆圈数字" % (pno, it.slot_id)

    def test_num_bare_four_digit_not_used(self):
        """四位阿拉伯数字若出现在屏显，一律可疑（编号 5-205 除外）。"""
        import re as _re
        cfg = _cfg()
        for pno, items in cfg.items():
            for it in items:
                if not it.slot_id or "photo" in it.slot_id:
                    continue
                stripped = it.text.replace("5-205", "")
                assert not _re.search(r"(?<![\-a-zA-Z0-9])\d{4}(?![\-a-zA-Z0-9])", stripped), (
                    "P%d %s 含四位裸数字" % (pno, it.slot_id)
                )
