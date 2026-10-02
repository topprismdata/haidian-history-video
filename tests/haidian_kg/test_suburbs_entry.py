"""
tests/haidian_kg/test_suburbs_entry.py
郊区聚落词条入库测试（E5 一亩园 + E10 蓝靛厂）

史料基准（全部为两份 research.md 冻结/闸门结论，不凭印象断言）：
- 皇帝正式亲耕耤田礼（「一亩三分地」）在【先农坛】；一亩园只有民间亲耕传说
  （「雍正帝演耕处，但缺少依据」）——先农坛礼制混淆与皇帝亲耕断言必须被拦下：
  ent_yimuyuan 无雍正年代任何状态（图档首证 1792），审计层不可判通过
- 《八旬万寿盛典》(1792) 图证空间形态；「大宫门前附属院落、后勤住舍」是 L2
  功能解释——两层分挂两个事实节点；大宫门≠正大光明
- 娘娘庙：康熙重建、光绪再建；刘诚连只能「再建/重修」非「始建」
- 扇面湖四段层累（1763/1860/2000/2024春夏），不凑「五次变身」；2024 不锁月日
- 火器营不是放火的营；年份链 1688/1691/1770/1773 不得混用（「建于1770」作
  起点是通行错讹）；营房只报分项（1024/6038/3176），7196 与「四千余间」禁用
  ——「放火营房+四千余间」混说句在审计层必须 BLOCK
- 蓝靛厂是明内府织染局外署（靛园厂），非民间染坊；1587 查无一手依据已删
- 西顶是北京五顶之一（唯一在海淀），「五顶之首/等级最高/八顶」禁用；
  北顶朝阳奥森、南顶丰台大红门外，方位不得错
- 营区踪迹全无 ≠ 地名消亡：毁损≠消亡（「从此消失」必须 BLOCK）
"""
import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from haidian_kg.calibration import suburbs as SB
from haidian_kg.calibration.people import PEOPLE
from haidian_kg.calibration.digital_resources import RESOURCES
from haidian_kg.production_exports import (
    KnowledgeBase, audit_script, export_storyboard,
)
from haidian_kg.qa_gate import QAGate
from haidian_kg.ontology.epistemic import EpistemicStatus
from haidian_kg.ontology.video_contracts import AuditVerdict


@pytest.fixture(scope="module")
def kb():
    return KnowledgeBase(
        sources=SB.SOURCES, divisions=SB.DIVISIONS, facts=SB.FACTS,
        entities=SB.ENTITIES, states=SB.STATES, identities=SB.IDENTITIES,
        appellations=SB.APPELLATIONS, references=SB.REFERENCES,
        transformations=SB.TRANSFORMATIONS, propositions=SB.PROPOSITIONS,
        adoptions=SB.ADOPTIONS, aggregates=SB.AGGREGATES,
        people=PEOPLE, resources=RESOURCES)


#: 逐句期望的对抗样本（G7）：真陈述放行 + 三类必须拦下的混淆句
ADV = (
    # E5 真陈述：1792 图档空间形态（L1）
    "1792年，官修《八旬万寿盛典》图绘一亩园区域有建筑院落、道路、水渠与土山。"
    # E5 红线①：皇帝亲耕断言（雍正帝演耕传说无档）——一亩园无雍正状态，不得通过
    "雍正五年，皇帝在一亩园行亲耕耤田礼。"
    # E5 红线②：先农坛礼制混淆——耤田礼制地点在先农坛，不得判给一亩园
    "1727年，一亩园即皇帝行耤田礼的先农坛礼制地点。"
    # E10 真陈述：1770 奏请迁建
    "1770年，管理火器营事务的蒙古都统奏请迁建外火器营。"
    # E10 红线③：「放火的营房」望文生义 + 「四千余间」查无实据——数字口径冲突 BLOCK
    "1800年，外火器营是放火的营房，营房四千余间。"
    # E10 红线④：营区建筑毁损 ≠ 地名消亡（地名留存）
    "1912年，外火器营从此消失。"
    # E10 真陈述：分项数字与状态记录一致
    "1773年，外火器营营区基本建成，官廨1024间、炮甲连房6038间。"
    # E10 真陈述：西顶改称（护国洪蕊宫→广仁宫为同一庙）
    "1712年，西顶娘娘庙改称广仁宫碧霞元君庙。",
    [("1792年，官修《八旬万寿盛典》图绘一亩园区域有建筑院落、道路、水渠与土山",
      "通过"),
     ("雍正五年，皇帝在一亩园行亲耕耤田礼", "非通过"),
     ("1727年，一亩园即皇帝行耤田礼的先农坛礼制地点", "非通过"),
     ("1770年，管理火器营事务的蒙古都统奏请迁建外火器营", "通过"),
     ("1800年，外火器营是放火的营房，营房四千余间", "非通过"),
     ("1912年，外火器营从此消失", "非通过"),
     ("1773年，外火器营营区基本建成，官廨1024间、炮甲连房6038间", "通过"),
     ("1712年，西顶娘娘庙改称广仁宫碧霞元君庙", "通过")],
)


def _states_text(kb_) -> str:
    parts = []
    for s in kb_.states.values():
        parts += [s.geometry or "", s.material or "", s.function or "",
                  s.admin_status or ""]
    return " ".join(parts)


def _all_text(kb_) -> str:
    return _states_text(kb_) + " " + " ".join(
        p.statement for p in kb_.propositions.values())


# ==================================================================
# 入库闸门（九维 QA：fail=0, warn=0, skip=0）
# ==================================================================

class TestSuburbsEntryGate:
    def test_entry_passes_gate_zero_warn_skip(self, kb):
        rep = QAGate("suburbs", kb, adversarial=ADV).run()
        assert rep.passed, rep.render()
        assert not [f for f in rep.findings if f.level == "warn"], rep.render()
        assert not [f for f in rep.findings if f.level == "skip"], rep.render()

    def test_uses_unified_bibliography(self, kb):
        """一部书只能一个节点；新书目一律取自统一书目表"""
        titles = [s.title for s in kb.sources.values()]
        assert len(titles) == len(set(titles)), "同一本书被建成多条：%s" % titles
        assert "钦定八旬万寿盛典" in titles
        assert "重修西顶娘娘庙碑记" in titles

    def test_all_facts_traceable(self, kb):
        div_ids = set(kb.divisions.keys())
        for f in kb.facts.values():
            assert f.division_id in div_ids, f.id

    def test_new_books_registered_with_authors(self):
        """预登记书目与人名（commit a95ef48）直接 import 使用，本任务核对即可"""
        from haidian_kg.calibration.bibliography import source_by_title
        src = source_by_title("钦定八旬万寿盛典")
        assert src is not None and src.author_person_id == "person_agui"
        assert source_by_title("大明会典") is not None
        assert source_by_title("清史稿") is not None
        bei = source_by_title("重修西顶娘娘庙碑记")
        assert bei is not None and bei.category.value == "金石"
        # 转载文章按原作者层级计：北京日报不得独立建目
        from haidian_kg.calibration.bibliography import BIBLIOGRAPHY
        assert "北京日报" not in {s.title for s in BIBLIOGRAPHY}

    def test_baxun_tu_and_func_layered(self, kb):
        """图档（L1）与功能解释（L2）必须分挂两个事实节点"""
        assert kb.facts["tf_bx_tu"].division_id == "div_bx_tu"
        assert kb.facts["tf_hd_func"].division_id == "div_hd_yimuyuan"
        assert kb.facts["tf_bx_tu"].division_id != kb.facts["tf_hd_func"].division_id


# ==================================================================
# E5 红线：先农坛礼制与皇帝亲耕传说严格分层
# ==================================================================

class TestYimuyuanRedlines:
    def test_xiannantan_confusion_blocked(self, kb):
        """耤田礼制地点在先农坛（非海淀地物，不入本库）；
        「一亩园即先农坛礼制地点」在审计层不得通过"""
        assert kb.state_at("ent_yimuyuan", 1727) is None
        r = audit_script(kb, "1727年，一亩园是明清皇帝行耤田礼的先农坛礼制地点。")
        assert r[0].verdict != AuditVerdict.PASS, r[0].reason
        # 结构防线：先农坛不是本库实体或名称，混说无从指称落地
        labels = {a.label for a in kb.appellations.values()}
        assert not any("先农坛" in lbl for lbl in labels)
        assert not any("先农坛" in e.canonical_label
                       for e in kb.entities.values())

    def test_emperor_plowing_assertion_blocked(self, kb):
        """「雍正帝演耕处」是传说（官方明确缺少依据）；
        亲耕断言在一亩园无雍正状态支撑，必须拦下"""
        assert kb.state_at("ent_yimuyuan", 1730) is None
        begins = sorted(s.time_span.begin.gregorian.year
                        for s in kb.states_of("ent_yimuyuan"))
        assert begins[0] == 1792, "一亩园首证状态必须是1792图档"
        r = audit_script(kb, "雍正五年，皇帝在一亩园行亲耕耤田礼。")
        assert r[0].verdict == AuditVerdict.UNTESTABLE, r[0].reason
        # 分层：官方否定有据（L2），礼制史实点名先农坛
        assert "缺少依据" in kb.facts["tf_hd_yanzheng"].verbatim_quote
        prop = kb.propositions["prop_yimuyuan_not_jitian"]
        assert "先农坛" in prop.statement
        ad = kb.adoptions["prop_yimuyuan_not_jitian"]
        assert ad.status == EpistemicStatus.VERIFIED

    def test_dagongmen_not_zhengdaguangming(self, kb):
        """大宫门是正门，正大光明是正殿——禁写「正大光明门（大宫门）」"""
        states_text = _states_text(kb)
        assert "正大光明门" not in states_text
        prop = kb.propositions["prop_dagongmen_zhengdian"]
        assert "正殿" in prop.statement and "正门" in prop.statement

    def test_liuchenglian_rejian_not_shijian(self, kb):
        """刘诚连只能表述「再建/重修」，非「始建」"""
        prop = kb.propositions["prop_liuchenglian_rejian"]
        assert "再建/重修" in prop.statement and "非「始建」" in prop.statement
        assert kb.adoptions["prop_liuchenglian_rejian"].status == \
            EpistemicStatus.CONTESTED

    def test_shanmianhu_four_segments_no_five(self, kb):
        """四段层累（1763/1860/2000/2024），不凑「五次变身」；2024 不锁月日"""
        begins = sorted(s.time_span.begin.gregorian.year
                        for s in kb.states_of("ent_shanmianhu"))
        assert begins == [1763, 1860, 2000, 2024]
        st = kb.states["st_smh_2024"]
        assert "春夏" in st.function and "2024" in st.function
        assert "展示性恢复" in st.function and "非原样复建" in st.function
        st_text = _states_text(kb)
        assert "五次变身" not in st_text
        assert "2024年5月竣工" not in st_text and "2024年6月竣工" not in st_text
        # 禁凑数纪律句挂在命题层
        assert "五次变身" in kb.propositions["prop_shanmianhu_counts"].statement

    def test_storyboard_yimuyuan_chain(self, kb):
        sb = export_storyboard(kb, "ent_yimuyuan")
        assert [f.state_id for f in sb.frames] == [
            "st_yim_1792", "st_yim_1860", "st_yim_minguo", "st_yim_modern"]


# ==================================================================
# E10 红线：火器营年份链、放火混淆、营房数字、官署性质
# ==================================================================

class TestLandianchangRedlines:
    def test_fire_camp_confusion_blocked(self, kb):
        """「放火的营房」+「四千余间」：数字与状态记录冲突，必须 BLOCK"""
        r = audit_script(kb, "1800年，外火器营是放火的营房，营房四千余间。")
        assert r[0].verdict == AuditVerdict.BLOCK, r[0].reason
        prop = kb.propositions["prop_huoqiying_not_fire"]
        assert "不是放火的营" in prop.statement
        assert "鸟枪" in prop.statement and "子母炮" in prop.statement

    def test_year_chain_1688_not_as_huoqiying(self, kb):
        """1688 是大刀营前身；「1688年设立火器营」与「1770 始建」都是错讹；
        年份链 1688/1691/1770/1773 不得混用"""
        begins = sorted(s.time_span.begin.gregorian.year
                        for s in kb.states_of("ent_waihuoqiying"))
        assert begins == [1770, 1773, 1912], "外火器营状态链必须是1770/1773/1912"
        r = audit_script(kb, "1688年，清廷正式设立火器营。")
        assert r[0].verdict != AuditVerdict.PASS, r[0].reason
        prop = kb.propositions["prop_huoqiying_year_chain"]
        for y in ("1688", "1691", "1770", "1773"):
            assert y in prop.statement, y
        assert kb.adoptions["prop_huoqiying_year_chain"].status == \
            EpistemicStatus.VERIFIED
        # 1688 与 1691 是同一部队改名，不是重复记载
        assert "改名" in kb.facts["tf_qsg_shehuoqi"].translator_note
        # 清史稿引文保持繁体原文
        assert kb.facts["tf_qsg_shehuoqi"].verbatim_quote == "三十年，始設火器營"

    def test_camp_numbers_items_only_no_total(self, kb):
        """营房只报分项（1024/6038/3176）；7196 与「四千余间」不入状态层，
        禁令挂命题层"""
        st_text = _states_text(kb)
        assert "1024" in st_text and "6038" in st_text and "3176" in st_text
        for banned in ("7196", "四千余", "近万间"):
            assert banned not in st_text, banned
        prop = kb.propositions["prop_fangcao_fenxiang"]
        assert "7196" in prop.statement and "非史料原文" in prop.statement
        assert "四千余间" in prop.statement and "查无实据" in prop.statement
        # 门楼 3176 座为《日下旧闻考》一手明文
        assert "三千一百七十六座" in kb.facts["tf_rxjwkc_menlou"].verbatim_quote

    def test_true_item_numbers_pass(self, kb):
        """分项数字与状态记录一致的真陈述放行"""
        r = audit_script(kb, "1773年，外火器营营区基本建成，官廨1024间、炮甲连房6038间。")
        assert r[0].verdict == AuditVerdict.PASS, r[0].reason

    def test_guanying_not_minjian_dye_works(self, kb):
        """蓝靛厂是明内府织染局外署（宫廷官署），不是民间染坊；
        1587 与「宫内派人」两个已删表述不得复活"""
        st_text = _states_text(kb)
        assert "织染局" in st_text and "官署" in st_text
        assert "非民间染坊" in st_text
        assert "民间染坊" in kb.propositions["prop_guanying_not_minjian"].statement
        for f in kb.facts.values():
            assert "1587" not in f.verbatim_quote, f.id
            assert "宫内派人" not in f.verbatim_quote, f.id
        assert kb.facts["tf_hd_ldc_yongle"].verbatim_quote.startswith("明永乐年间")

    def test_neiwai_ying_city_in_out(self, kb):
        """内营驻城内（枪营、炮营），外营在西郊蓝靛厂；内外是城内/城外"""
        prop = kb.propositions["prop_neiwai_ying"]
        assert "枪营、炮营" in prop.statement and "城内/城外" in prop.statement

    def test_damage_is_not_extinction(self, kb):
        """营区踪迹全无 ≠ 地名消亡：「从此消失」必须 BLOCK（地名留存续体）"""
        r = audit_script(kb, "1912年，外火器营从此消失。")
        assert r[0].verdict == AuditVerdict.BLOCK, r[0].reason
        st = kb.states["st_wai_1912"]
        assert "地名" in st.function and "留存" in st.function
        dia = next(d for d in kb.identities if d.id == "dia_waiying_neiwai_split")
        assert dia.status == EpistemicStatus.VERIFIED
        assert dia.time_span.contains(1912)
        assert kb.adoptions["prop_zongji_vs_diming"].status == \
            EpistemicStatus.VERIFIED

    def test_storyboard_waiying_chain(self, kb):
        sb = export_storyboard(kb, "ent_waihuoqiying")
        assert [f.state_id for f in sb.frames] == [
            "st_wai_1770", "st_wai_1773", "st_wai_1912"]


# ==================================================================
# E10 红线：西顶五顶方位与庙会日期
# ==================================================================

class TestXidingRedlines:
    def test_wuding_position_discipline(self, kb):
        """五顶方位不得错；「五顶之首/等级最高/八顶」禁用；西顶唯一在海淀"""
        q = kb.facts["tf_hd_wuding"].verbatim_quote
        assert "东直门外" in q and "大红门外" in q and "奥林匹克公园" in q
        assert "唯一在海淀" in q
        prop = kb.propositions["prop_xiding_wuding"]
        assert "唯一在海淀" in prop.statement and "五顶之首" in prop.statement
        st_text = _states_text(kb)
        for banned in ("五顶之首", "等级最高", "八顶"):
            assert banned not in st_text, banned

    def test_miaohui_dates_two_ranges_only(self, kb):
        """庙会日期只说正月初一至十五、四月初一至十五，不与「至十八」混说"""
        st_text = _states_text(kb)
        assert "正月初一至十五" in st_text and "四月初一至十五" in st_text
        assert "至十八" not in st_text
        assert "庙反而是庙会的配角" in \
            kb.propositions["prop_miaohui_riqi"].statement
        # 「至十八」一说只允许留存在事实层 note
        assert "至十八" in kb.facts["tf_hd_miaohui"].translator_note

    def test_legends_are_legends(self, kb):
        """显灵传说与航船比喻都是民间传说级，不做骨架"""
        for pid in ("prop_xiding_xianling_legend", "prop_hangchuan_legend"):
            assert kb.adoptions[pid].status == EpistemicStatus.FOLK_LEGEND, pid
        assert "据说" in kb.propositions["prop_hangchuan_legend"].statement

    def test_guangren_rename_same_temple(self, kb):
        """护国洪蕊宫→广仁宫为同一庙改称（1608/1712 两段状态）"""
        assert kb.state_at("ent_xiding", 1608).id == "st_xd_1608"
        assert kb.state_at("ent_xiding", 1712).id == "st_xd_1712"
        dia = next(d for d in kb.identities if d.id == "dia_xiding_gaicheng")
        assert dia.status == EpistemicStatus.VERIFIED


# ==================================================================
# 审计器两向验证（抓真错 + 放真话）
# ==================================================================

class TestAudit:
    def test_true_statements_pass(self, kb):
        """真陈述必须放行：图档形态、迁建奏请、西顶改称"""
        for text in ("1792年，官修《八旬万寿盛典》图绘一亩园区域有建筑院落、道路、水渠与土山。",
                     "1770年，管理火器营事务的蒙古都统奏请迁建外火器营。",
                     "1712年，西顶娘娘庙改称广仁宫碧霞元君庙。"):
            r = audit_script(kb, text)
            assert r[0].verdict == AuditVerdict.PASS, (text, r[0].reason)

    def test_plowing_untestable_not_pass(self, kb):
        """缺证据≠通过：雍正亲耕断言返回 UNTESTABLE 而非 PASS"""
        r = audit_script(kb, "雍正五年，皇帝在一亩园行亲耕耤田礼。")
        assert r[0].verdict == AuditVerdict.UNTESTABLE
        assert "不得视为通过" in r[0].reason or "无有效指称" in r[0].reason

    def test_historical_name_qianhu_resolves(self, kb):
        """旧称「前湖」仍可消歧到扇面湖实体（开放起始区间）"""
        r = audit_script(kb, "1760年，前湖一带还是洼地水面。")
        assert r[0].verdict in (AuditVerdict.PASS, AuditVerdict.UNTESTABLE)
