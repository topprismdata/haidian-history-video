# -*- coding: utf-8 -*-
"""E28《温泉·「温泉」之前叫「石窝」》页面与槽位系统测试.

依据：docs/superpowers/specs/2026-10-04-e28-wenquan-design.md（APPROVED）。
负控制纪律：判据先在已知正确内容上跑通（本文件即校准集），
禁 U+3007 / 禁内审标记 / 禁阿拉伯公历年 / 国保编号须附批次与公布年。
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from qa_v2.data import parse_pages_config
from qa_v2.normalize import extract_numbers

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE_DATA = ROOT / "remotion-template" / "src" / "wenquan" / "data"
SYNC_DATA = pathlib.Path("/tmp/chemistry-video/src/wenquan/data")
NARR_FILE = ROOT / "wenquan_video" / "narration" / "all.json"
PAGES_DIR = ROOT / "remotion-template" / "src" / "wenquan" / "pages"

# 国保编号例外白名单（V-NC05：标识符非纪年，可上屏但须附批次与公布年）
GUOBAO_CODES = ("7-1973-3-009", "6-886", "6-810")


def _slots_data():
    return json.loads((TEMPLATE_DATA / "slots.json").read_text(encoding="utf-8"))


def _cfg():
    return parse_pages_config((TEMPLATE_DATA / "pages.config.ts").read_text(encoding="utf-8"))


def _narration():
    return json.loads(NARR_FILE.read_text(encoding="utf-8"))


def _strip_codes(t):
    for c in GUOBAO_CODES:
        t = t.replace(c, " ")
    return t


def _photo_captions():
    """从 Page0*.tsx 抓取 PhotoFrame caption（屏显真实文字，属 OCR 判据范围）。"""
    caps = {}
    for f in sorted(PAGES_DIR.glob("Page0*.tsx")):
        pno = int(f.stem[5:7])
        caps.setdefault(pno, [])
        caps[pno] += re.findall(r'caption: "([^"]+)"', f.read_text(encoding="utf-8"))
    return caps


def _screen_text(pno, cfg):
    """第 pno 页全部可见文字槽（非 photo）。"""
    return [it for it in cfg[pno] if it.kind != "photo"]


# ==================================================================
# 1. 结构完整性
# ==================================================================

def test_slots_json_has_8_pages():
    data = _slots_data()
    assert sorted(data.keys()) == [f"p{i:02d}" for i in range(1, 9)]
    for k, pdata in data.items():
        assert pdata["plate"] == [1920, 1080]
        assert len(pdata["slots"]) >= 5


def test_slots_and_pages_config_bidirectional_match():
    cfg = _cfg()
    data = _slots_data()
    for pno in range(1, 9):
        k = f"p{pno:02d}"
        slot_ids = {s["id"] for s in data[k]["slots"]}
        cfg_ids = {it.slot_id for it in cfg[pno]}
        assert cfg_ids == slot_ids, (
            f"{k} 槽位两侧不一致: slots.json 独有 {slot_ids - cfg_ids}, "
            f"pages.config.ts 独有 {cfg_ids - slot_ids}"
        )


def test_all_text_slots_have_backing():
    cfg = _cfg()
    for pno, items in cfg.items():
        for it in items:
            if it.kind == "photo":
                continue
            assert it.backing, f"P{pno} 槽位 {it.slot_id} 缺少 backing（物理隔离红线）"


def test_all_slots_within_canvas():
    for page_key, pdata in _slots_data().items():
        for s in pdata["slots"]:
            x, y, w, h = s["x"], s["y"], s["w"], s["h"]
            assert x >= 0 and y >= 0, f"{page_key}/{s['id']} 负坐标"
            assert x + w <= 1920, f"{page_key}/{s['id']} 宽度越界: {x}+{w}"
            assert y + h <= 1080, f"{page_key}/{s['id']} 高度越界: {y}+{h}"


def test_text_slots_do_not_overlap():
    """同页文字槽两两不相交（photo 槽与文字槽分列，文字槽之间严禁叠压）。"""
    for page_key, pdata in _slots_data().items():
        boxes = [s for s in pdata["slots"] if "photo" not in s["id"]]
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                a, b = boxes[i], boxes[j]
                sep = (a["x"] + a["w"] <= b["x"] or b["x"] + b["w"] <= a["x"] or
                       a["y"] + a["h"] <= b["y"] or b["y"] + b["h"] <= a["y"])
                assert sep, f"{page_key} 文字槽叠压: {a['id']} × {b['id']}"


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
# 2. 屏显判据（E24 教训源头 + E13 同函数纪律）
# ==================================================================

def test_screen_numbers_subset_of_spoken():
    """屏显数字 ⊆ 口播数字。两侧同一 extract_numbers，同一国保编号剔除。"""
    cfg = _cfg()
    narr = _narration()
    spoken = {int(k[1:]): set(extract_numbers(v)) for k, v in narr.items()}
    caps = _photo_captions()
    for pno in range(1, 9):
        screen = set()
        for it in cfg[pno]:
            if it.kind == "photo":
                continue
            screen |= set(extract_numbers(_strip_codes(it.text)))
        for c in caps.get(pno, []):
            screen |= set(extract_numbers(_strip_codes(c)))
        excess = screen - spoken[pno]
        assert not excess, f"P{pno} 屏显多出口播没有的数字: {sorted(excess)}"


BANNED_ARABIC_YEARS = (
    "1394", "1445", "1486", "1514", "1593", "1635", "1681", "1738",
    "1913", "1931", "1936", "1937", "1949", "1984", "2001", "2003",
    "2006", "2013",
)


def test_banned_arabic_years_absent():
    cfg = _cfg()
    caps = _photo_captions()
    for pno in range(1, 9):
        texts = [it.text for it in cfg[pno] if it.kind != "photo"] + caps.get(pno, [])
        for t in texts:
            for y in BANNED_ARABIC_YEARS:
                assert y not in t, f"P{pno} 含阿拉伯公历年「{y}」，应改年号或全字形"


def test_no_digits_outside_guobao_whitelist():
    """国保编号是唯一放行的阿拉伯数字（V-NC05 例外），其余一律全字形。"""
    cfg = _cfg()
    caps = _photo_captions()
    for pno in range(1, 9):
        texts = [(it.slot_id, it.text) for it in cfg[pno] if it.kind != "photo"]
        texts += [(f"caption{i}", c) for i, c in enumerate(caps.get(pno, []))]
        for sid, t in texts:
            stripped = _strip_codes(t)
            bad = re.findall(r"[0-9]", stripped)
            assert not bad, f"P{pno} {sid} 出现白名单外阿拉伯数字: {stripped!r}"


def test_no_ideographic_zero_anywhere():
    """U+3007 圆圈数字在宋体下不可见（OCR 漏读），屏显链路全文件零命中。"""
    files = [TEMPLATE_DATA / "slots.json", TEMPLATE_DATA / "pages.config.ts",
             TEMPLATE_DATA / "pageMap.ts", NARR_FILE]
    caps_dir = PAGES_DIR
    files += sorted(caps_dir.glob("Page0*.tsx"))
    for f in files:
        s = f.read_text(encoding="utf-8")
        assert "\u3007" not in s, f"{f.name} 含 U+3007 圆圈数字"


def test_no_internal_audit_markers():
    """V-NC08：内审标记、集号、路径、分级标签、管线术语零上屏。"""
    cfg = _cfg()
    caps = _photo_captions()
    pat = re.compile(
        r"🔴|🟡|E2[0-9]|/tmp/|\.py|\.json|\.csv|TODO|L[1-5]\b|MEC-|VEC-|§"
        r"|知识库|研究档案|entities\.json|wenquan"
    )
    for pno in range(1, 9):
        texts = [it.text for it in cfg[pno]] + caps.get(pno, [])
        for t in texts:
            m = pat.search(t)
            assert not m, f"P{pno} 屏显含内审标记「{m.group(0)}」: {t[:40]!r}"


def test_no_emoji_on_screen():
    cfg = _cfg()
    for pno, items in cfg.items():
        for it in items:
            for ch in it.text:
                assert not (0x1F300 <= ord(ch) <= 0x1FAFF or ord(ch) in (0xFE0F, 0x2757)), (
                    f"P{pno} {it.slot_id} 含 emoji: {ch!r}"
                )


# ==================================================================
# 3. V-NC01 地名层累：顺序不可倒置，改名不得系年
# ==================================================================

class TestVNC01NameLadder:
    def test_chain_order_on_p8(self):
        cfg = _cfg()
        chain = [it for it in cfg[8] if it.slot_id == "p8_chain"]
        assert len(chain) == 1, "P8 必须有且仅有一条五段命名链"
        t = chain[0].text
        marks = ["泉 · ", "堂 · ", "山 · ", "村 · ", "镇 · "]
        pos = [t.index(m) for m in marks]
        assert pos == sorted(pos), "V-NC01：五段链顺序必须是 泉→堂→山→村→镇"

    def test_no_ancient_spring_name_claim(self):
        """V-NC01：禁「自古因泉得名」。"""
        blob = " ".join(it.text for items in _cfg().values() for it in items)
        for bad in ("自古", "村名与泉同龄"):
            assert bad not in blob, f"V-NC01 违规：屏显出现「{bad}」"

    def test_rename_not_dated(self):
        """改名具体年代无书证——严禁「某年由石窝村改称温泉村」式表述。"""
        blob = " ".join(it.text for items in _cfg().values() for it in items)
        for bad in ("由石窝村改称", "改称温泉村", "改名温泉村", "改叫温泉村"):
            assert bad not in blob, f"V-NC01 违规：改名被系年「{bad}」"

    def test_wanli_official_name_is_shiwo(self):
        cfg = _cfg()
        p4 = " ".join(it.text for it in cfg[4])
        assert "石窩村" in p4, "P4 必须引《宛署杂记》原字「石窩村」"
        assert "不叫温泉" in p4, "P4 必须点明万历官书正式村名不叫温泉"


# ==================================================================
# 4. V-NC02 一手起点是明初，伪引不得进入采信层
# ==================================================================

class TestVNC02MingStart:
    def test_bathing_quote_only_in_p6_falsified_card(self):
        cfg = _cfg()
        hits = []
        for pno, items in cfg.items():
            for it in items:
                if "沐浴之所" in it.text:
                    hits.append((pno, it))
        assert len(hits) == 1, "「沐浴之所」只准出现在 P6 伪引卡一处"
        pno, it = hits[0]
        assert pno == 6, "「沐浴之所」只准出现在 P6"
        assert "伪引" in it.text, "伪引卡必须带「伪引」前缀"
        assert it.backing == "rgba(213,208,198,0.94)", "伪引卡必须灰化底"

    def test_zhubi_only_in_p6(self):
        cfg = _cfg()
        for pno, items in cfg.items():
            for it in items:
                if "驻跸" in it.text:
                    assert pno == 6 and "伪引" in it.text, "「驻跸」只准在 P6 伪引卡"

    def test_gugong_hanbaiyu_only_with_rejection(self):
        cfg = _cfg()
        hits = [it for items in cfg.values() for it in items
                if "故宫" in it.text or "汉白玉" in it.text]
        for it in hits:
            assert "不采" in it.text, f"{it.slot_id} 「故宫/汉白玉」命中必须带「不采」语境"

    def test_earliest_first_hand_is_ming_quarrying(self):
        cfg = _cfg()
        p3 = " ".join(it.text for it in cfg[3])
        for need in ("洪武二十七年", "正统十年", "一三九四", "一四四五", "采石匠"):
            assert need in p3, f"P3 缺明初采石题记要素「{need}」"


# ==================================================================
# 5. V-NC03 伪引卡 / 原文卡同框并排
# ==================================================================

class TestVNC03FalsifiedVsOriginal:
    def test_fake_card_grey_dashed_with_prefix(self):
        cfg = _cfg()
        fake = [it for it in cfg[6] if it.slot_id == "p6_fake"]
        assert len(fake) == 1
        it = fake[0]
        assert it.backing == "rgba(213,208,198,0.94)", "伪引卡必须灰化底"
        assert "伪引" in it.text and "已证伪" in it.text, "伪引卡必须带「伪引 · 已证伪」前缀"
        assert "平地温泉如沸" in it.text and "冬月白气滃然" in it.text, "伪引卡必须逐字收录伪句"

    def test_original_card_paper_solid_with_original_text(self):
        cfg = _cfg()
        orig = [it for it in cfg[6] if it.slot_id == "p6_orig"]
        assert len(orig) == 1
        it = orig[0]
        assert it.backing == "rgba(247,240,223,0.95)", "原文卡必须卡纸实底"
        assert "原文" in it.text, "原文卡必须带「原文」前缀"
        assert "山北十里" in it.text and "甃而為池" in it.text, "原文卡必须逐字收录原文"

    def test_two_cards_same_screen_with_vs(self):
        cfg = _cfg()
        ids = {it.slot_id for it in cfg[6]}
        assert {"p6_fake", "p6_orig", "p6_vs"} <= ids, "伪引卡/原文卡/VS 必须同屏并排"
        data = _slots_data()["p06"]["slots"]
        by_id = {s["id"]: s for s in data}
        f, o, v = by_id["p6_fake"], by_id["p6_orig"], by_id["p6_vs"]
        assert f["y"] == o["y"], "伪引卡与原文卡必须并排（同一水平带）"
        assert f["x"] + f["w"] <= v["x"] and v["x"] + v["w"] <= o["x"], "VS 必须在两卡之间"

    def test_page6_has_no_borrowed_folio(self):
        """资产未补制前 P6 降级 TextOnly——严禁挪用《帝京景物略》书影顶替。"""
        cfg = _cfg()
        assert not [it for it in cfg[6] if it.kind == "photo"], "P6 不得有 photo 槽"
        src = (PAGES_DIR / "Page06.tsx").read_text(encoding="utf-8")
        assert "staticFile" not in src, "P6 页面不得引用任何图片"

    def test_rare_glyphs_present(self):
        """滃/甃/躄/窩 为引文原字形，严禁形近字替换或删字。"""
        blob = " ".join(it.text for items in _cfg().values() for it in items)
        for ch in ("滃", "甃", "躄", "窩"):
            assert ch in blob, f"屏显缺引文原字形「{ch}」"


# ==================================================================
# 6. V-NC04 香水院不在温泉后山
# ==================================================================

class TestVNC04Xiangshuiyuan:
    def test_every_hit_anchored_to_miaogaofeng_or_doubted(self):
        cfg = _cfg()
        hits = [it for items in cfg.values() for it in items if "香水院" in it.text]
        assert hits, "屏显必须出现香水院考订"
        for it in hits:
            ok = ("妙高峰" in it.text or
                  any(w in it.text for w in ("存疑", "考释", "无据")))
            assert ok, f"{it.slot_id} 「香水院」命中缺「妙高峰/存疑/考释/无据」锚定"


# ==================================================================
# 7. V-NC05 国保批次与编号
# ==================================================================

class TestVNC05GuobaoNumbering:
    def test_codes_only_on_p8(self):
        cfg = _cfg()
        for pno, items in cfg.items():
            for it in items:
                for c in GUOBAO_CODES:
                    if c in it.text:
                        assert pno == 8, f"国保编号 {c} 只准出现在 P8（现 P{pno}）"

    def test_6_886_with_batch_and_year(self):
        cfg = _cfg()
        host = [it for it in cfg[8] if "6-886" in it.text]
        assert len(host) == 1
        t = host[0].text
        assert "第六批" in t and "二零零六" in t, "6-886 必须同卡附「第六批」与「二零零六」"
        assert "近现代重要史迹" in t, "6-886 必须附类别"

    def test_6_810_with_batch_and_canal(self):
        cfg = _cfg()
        host = [it for it in cfg[8] if "6-810" in it.text]
        assert len(host) == 1
        t = host[0].text
        assert ("大运河" in t or "第六批" in t) and "二零零六" in t, (
            "6-810 必须同卡附批次/大运河与公布年"
        )

    def test_7_1973_with_batch_and_canal(self):
        cfg = _cfg()
        host = [it for it in cfg[8] if "7-1973-3-009" in it.text]
        assert len(host) == 1
        t = host[0].text
        assert "第七批" in t and "大运河" in t, "7-1973-3-009 必须同卡附「第七批」「大运河」"

    def test_no_first_batch_misattribution(self):
        cfg = _cfg()
        p8 = " ".join(it.text for it in cfg[8])
        assert "第一批" not in p8, "本集无 1961 第一批单位，严禁出现「第一批」"

    def test_numbering_pending_review_note(self):
        cfg = _cfg()
        p8 = " ".join(it.text for it in cfg[8])
        assert "原件复核" in p8, "P8 必须标「编号与批次据名录口径，须与原件复核」"


# ==================================================================
# 8. V-NC06 泉眼现状双禁
# ==================================================================

class TestVNC06SpringDoubleBan:
    BANNED = ("至今仍在涌流", "至今还在冒热水", "早已干涸", "泉已枯竭", "涌流", "干涸")

    def test_assertions_only_in_negated_context(self):
        cfg = _cfg()
        hits = []
        for pno, items in cfg.items():
            for it in items:
                for b in self.BANNED:
                    if b in it.text:
                        hits.append((pno, it, b))
        assert hits, "双禁判据必须在真实数据上命中（防恒真）"
        for pno, it, b in hits:
            neg = any(w in it.text for w in ("不写", "不说", "未考得", "不作断言"))
            assert neg, f"P{pno} {it.slot_id} 「{b}」落在肯定陈述"

    def test_heilongtan_paddle_attributed(self):
        """「水深不盈尺」必须写明是黑龙潭，不得挪用为温泉现状。"""
        cfg = _cfg()
        for pno, items in cfg.items():
            for it in items:
                if "不盈尺" in it.text:
                    assert "黑龙潭" in it.text, f"{it.slot_id} 「不盈尺」须注明黑龙潭"

    def test_cixi_nuanquan_never_mentioned(self):
        blob = " ".join(it.text for items in _cfg().values() for it in items)
        narr = json.dumps(_narration(), ensure_ascii=False)
        for bad in ("慈禧", "暖泉", "白家疃温泉"):
            assert bad not in blob, f"V-NC 存疑落位违规：屏显出现「{bad}」"
            assert bad not in narr, f"口播出现「{bad}」"


# ==================================================================
# 9. V-NC09 caption 限定语
# ==================================================================

CAPTION_QUALIFIERS = {
    "dijing_jingwulue_folio": ["依公开文本排印 · 非原刊扫描"],
    "wanshu_zaji_folio": ["依公开文本排印 · 非原刊扫描"],
    "caishi_moyai_shiyi": ["制作组绘制示意 · 非实物照片", "刻痕非释文"],
    "shuiliu_yunzai_moyai": ["制作组绘制示意 · 非实物照片", "字体排印非手迹"],
    "heilongtan_longwangmiao": ["制作组绘制示意 · 非实物照片"],
    "luanzhou_jinianta": ["制作组绘制示意 · 非实物照片"],
    "mec3_diming_timeline": ["制作组示意 · 非测绘拓扑"],
    "mec4_quanming_chain": ["制作组示意 · 非测绘拓扑"],
}


def _asset_captions():
    """staticFile("wenquan/<asset>.png") 与同 PhotoSpec caption 的配对。"""
    pairs = {}
    for f in sorted(PAGES_DIR.glob("Page0*.tsx")):
        src = f.read_text(encoding="utf-8")
        for m in re.finditer(
            r'staticFile\("wenquan/([a-z0-9_]+)\.png"\),\s*caption: "([^"]+)"', src
        ):
            pairs[m.group(1)] = m.group(2)
    return pairs


def test_all_ten_assets_used():
    pages_src = ""
    for f in sorted(PAGES_DIR.glob("Page0*.tsx")):
        pages_src += f.read_text(encoding="utf-8")
    for asset in list(CAPTION_QUALIFIERS) + [
        "beijing_1915_shiwo_roi", "sanshanyuan_xiangshan_roi",
    ]:
        assert asset in pages_src, f"资产 {asset} 未落位"


def test_caption_qualifier_phrases_exact():
    pairs = _asset_captions()
    for asset, quals in CAPTION_QUALIFIERS.items():
        assert asset in pairs, f"{asset} 无 frame caption（须走 PhotoFrame 装裱）"
        for q in quals:
            assert q in pairs[asset], f"{asset} caption 缺限定语「{q}」: {pairs[asset]!r}"


def test_caption_no_affirmative_real_photo_words():
    caps = _photo_captions()
    for pno, lst in caps.items():
        for c in lst:
            for w in ("实景", "实拍", "拓片"):
                assert w not in c, f"P{pno} caption 出现禁词「{w}」"
            for w in ("原刊", "手迹"):
                i = c.find(w)
                if i >= 0:
                    assert "非" in c[max(0, i - 6):i], f"P{pno} caption 「{w}」缺「非」限定"


def test_mec1_no_spring_label_on_old_map():
    """《三山五园图》切片必须标明温泉村在图幅之外，不得加温泉标注。"""
    caps = _photo_captions()
    blob = " ".join(c for lst in caps.values() for c in lst)
    cfg_blob = " ".join(it.text for items in _cfg().values() for it in items)
    assert "温泉村在图幅之外" in blob or "温泉村在图幅之外" in cfg_blob


# ==================================================================
# 10. 祈/浴功能分层（V-NC09 附判）
# ==================================================================

class TestPrayBathSeparation:
    def test_qi_yu_cards_each_carry_distinct_spring(self):
        cfg = _cfg()
        qi = [it for it in cfg[5] if it.slot_id == "p5_card_qi"]
        yu = [it for it in cfg[5] if it.slot_id == "p5_card_yu"]
        assert qi and yu, "P5 必须有祈/浴两张对置卡"
        assert "黑龙潭" in qi[0].text and "冷泉" in qi[0].text
        assert "温泉堂" in yu[0].text and "热泉" in yu[0].text

    def test_no_merged_claim(self):
        cfg = _cfg()
        for pno, items in cfg.items():
            for it in items:
                if "祈雨" in it.text and "沐浴" in it.text:
                    ok = any(w in it.text for w in ("黑龙潭", "温泉", "冷泉", "热泉", "分属"))
                    assert ok, f"{it.slot_id} 祈/浴同卡缺区分词"
