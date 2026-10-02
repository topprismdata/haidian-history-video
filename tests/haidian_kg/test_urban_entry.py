"""
tests/haidian_kg/test_urban_entry.py
商业与近现代词条入库测试（E12 苏州街 + E13 中关村）

史料基准（全部为两份 research.md v2 冻结结论 + 原典复核，不凭印象断言）：
- 万寿街是真买卖的皇家街市；「太监宫女扮商贩」属园内买卖街（同乐园），
  移植给万寿街的断言必须被拦下（含句内「从此消失」混合句）
- 营建年份：昭梿《啸亭杂录》系年乾隆辛巳（1761）；1751/1761 两轮不混
- 毁废：《天咫偶闻》卷九「今已毁尽」；1860 年万寿街不设状态
  （无直接军事记录）——「1860 被焚毁」直说结构上不可通过；
  同句式对后溪河买卖街（B）则放行（园史直录焚毁），两向对照
- 中关村：「中关」1913 年已见于《京西图》，1953 初创神话必须被拦下；
  误植说挂当事人回忆（CONTESTED），陈垣说降「一说」（UNSUBSTANTIATED）
- 文献卷次两处考订留痕：《天咫偶闻》卷九（非卷七）、
  《汉书》高后纪（非交付档案所记高帝纪）
"""
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from haidian_kg.calibration import urban as U
from haidian_kg.calibration.people import PEOPLE
from haidian_kg.calibration.digital_resources import RESOURCES
from haidian_kg.production_exports import (
    KnowledgeBase, audit_script, export_storyboard,
)
from haidian_kg.qa_gate import QAGate
from haidian_kg.ontology.epistemic import EpistemicStatus
from haidian_kg.ontology.spatiotemporal import AppellationKind
from haidian_kg.ontology.video_contracts import AuditVerdict


@pytest.fixture(scope="module")
def kb():
    return KnowledgeBase(
        sources=U.SOURCES, divisions=U.DIVISIONS, facts=U.FACTS,
        entities=U.ENTITIES, states=U.STATES, identities=U.IDENTITIES,
        appellations=U.APPELLATIONS, references=U.REFERENCES,
        transformations=U.TRANSFORMATIONS, propositions=U.PROPOSITIONS,
        adoptions=U.ADOPTIONS, aggregates=U.AGGREGATES,
        people=PEOPLE, resources=RESOURCES)


#: 逐句期望的对抗样本（G7）：
#: 三条红线陈述必须非通过 + 五条真陈述必须放行（闸门非恒真的两向证明）
ADV = (
    "1860年，英法联军焚毁苏州街，街上太监开设的店铺从此消失。"
    "苏州街上的商贩都是太监宫女扮演的。"
    "1953年，中关村这个名字第一次出现。"
    "1913年，《京西图》上已标注「中关」。"
    "1800年，中官村一带是埋葬太监的义地。"
    "1850年，万寿街俗称苏州街，北达畅春园。"
    "1907年，万寿街俗称苏州街，晚清记载今已毁尽。"
    "1780年，同乐园买卖街开店者俱以内监为之。",
    [("1860年，英法联军焚毁苏州街，街上太监开设的店铺从此消失", "非通过"),
     ("苏州街上的商贩都是太监宫女扮演的", "非通过"),
     ("1953年，中关村这个名字第一次出现", "非通过"),
     ("1913年，《京西图》上已标注「中关」", "通过"),
     ("1800年，中官村一带是埋葬太监的义地", "通过"),
     ("1850年，万寿街俗称苏州街，北达畅春园", "通过"),
     ("1907年，万寿街俗称苏州街，晚清记载今已毁尽", "通过"),
     ("1780年，同乐园买卖街开店者俱以内监为之", "通过")],
)


def _states_text(kb_, entity_id=None) -> str:
    parts = []
    for s in kb_.states.values():
        if entity_id is not None and s.entity_id != entity_id:
            continue
        parts += [s.geometry or "", s.material or "", s.function or "",
                  s.admin_status or ""]
    return " ".join(parts)


# ==================================================================
# 入库闸门（九维 QA：fail=0, warn=0, skip=0）
# ==================================================================

class TestUrbanEntryGate:
    def test_entry_passes_gate_zero_warn_skip(self, kb):
        rep = QAGate("urban", kb, adversarial=ADV).run()
        assert rep.passed, rep.render()
        assert not [f for f in rep.findings if f.level == "warn"], rep.render()
        assert not [f for f in rep.findings if f.level == "skip"], rep.render()

    def test_exports_isomorphic(self):
        for name in ("SOURCES", "DIVISIONS", "FACTS", "ENTITIES", "STATES",
                     "IDENTITIES", "APPELLATIONS", "REFERENCES",
                     "TRANSFORMATIONS", "PROPOSITIONS", "ADOPTIONS",
                     "AGGREGATES"):
            assert hasattr(U, name), name

    def test_uses_unified_bibliography(self, kb):
        """一部书只能一个节点；新书目一律取自统一书目表"""
        titles = [s.title for s in kb.sources.values()]
        assert len(titles) == len(set(titles)), "同一本书被建成多条：%s" % titles

    def test_all_facts_traceable(self, kb):
        div_ids = set(kb.divisions.keys())
        for f in kb.facts.values():
            assert f.division_id in div_ids, f.id

    def test_new_books_and_people_registered(self):
        """commit a95ef48 预置的七书五人已经登记——本任务核对即可，不得改表"""
        from haidian_kg.calibration.bibliography import BIBLIOGRAPHY
        by_id = {s.id: s for s in BIBLIOGRAPHY}
        for sid, author in (("src_xiaoting_zalu", "person_zhaolian"),
                            ("src_tianzhi_ouwen", "person_zhenjun"),
                            ("src_hanshu", "person_bangu"),
                            ("src_baxun_wanshou", "person_agui")):
            assert by_id[sid].author_person_id == author, sid
        assert by_id["src_1913_jingxitu"].issuing_body
        assert by_id["src_daminghuidian"].issuing_body
        assert by_id["src_xiding_miao_bei"].category.value == "金石"
        pids = {p.id for p in PEOPLE}
        assert {"person_zhaolian", "person_zhenjun", "person_bangu",
                "person_agui", "person_hourenzhi"} <= pids


# ==================================================================
# 文献卷次考订留痕（两处纠正，不得反改回去）
# ==================================================================

class TestTextualCorrections:
    def test_tianzhi_ouwen_is_juan9(self, kb):
        """万寿街条经维基文库复核在卷九；预置书目表作卷七系误记，
        本词条按原书纠正并留痕"""
        assert kb.divisions["div_tzow9_jiaodiong"].volume_number == "卷九"
        f = kb.facts["tf_tzow_wanshoujie"]
        assert "今已毀盡" in f.verbatim_quote
        assert "卷九" in f.translator_note and "卷七" in f.translator_note
        from haidian_kg.calibration.bibliography import source_by_title
        assert "卷七" in (source_by_title("天咫偶闻").edition_note or ""), \
            "预置书目表的误记原样保留（不修改 bibliography.py），以词条篇卷为准"

    def test_hanshu_is_gaohouji_not_gaodiji(self, kb):
        """「诸中官」条经原书复核出《高后纪第三》高后八年春，非高帝纪"""
        div = kb.divisions["div_hanshu_gaohouji"]
        assert div.volume_number == "卷三" and "高后纪" in div.section_title
        f = kb.facts["tf_hanshu_zhongguan"]
        assert "諸中官" in f.verbatim_quote and "八年春" in f.verbatim_quote
        assert "高帝纪" in f.translator_note and "高后纪" in f.translator_note
        assert "前180" in f.translator_note

    def test_qingshigao_kept_as_downgraded_record(self, kb):
        """《清史稿》只作冲突存档：南巡者三挂 CONTESTED，不作据"""
        f = kb.facts["tf_qsg_nanxun"]
        assert "南巡者三" in f.verbatim_quote
        assert "降级" in f.translator_note and "不单独作据" in f.translator_note
        ad = kb.adoptions["prop_qsg_downgrade"]
        assert ad.status == EpistemicStatus.CONTESTED and ad.confidence <= 0.5


# ==================================================================
# E12 红线：万寿街（真买卖）与园内买卖街（太监扮装）严禁混淆
# ==================================================================

class TestSuzhoujieRedlines:
    def test_1761_not_1751(self, kb):
        """营建年份＝乾隆辛巳(1761)；1751 六旬属另一轮工程，无状态混淆"""
        st = kb.state_at("ent_wanshoujie", 1761)
        assert st is not None and st.id == "st_wsj_1761"
        ry = st.time_span.begin.reign_year
        assert ry.year_within_reign == 26 and ry.ganzhi == "辛巳"
        assert kb.state_at("ent_wanshoujie", 1751) is None
        prop = kb.propositions["prop_shuangwanshou"]
        assert "1751" in prop.statement and "1761" in prop.statement
        assert "两轮" in prop.statement
        ad = kb.adoptions["prop_jiancheng_1761"]
        assert ad.status == EpistemicStatus.VERIFIED
        assert "二十七年" in "；".join(
            kb.propositions["prop_jiancheng_1761"].alternative_explanations), \
            "二十七年异说只能以撤稿身份出现在备择解释里"

    def test_taijian_model_belongs_to_garden_only(self, kb):
        """万寿街状态层对「太监扮商贩」只允许否定性提及；扮装模式挂同乐园实体"""
        wsj_text = _states_text(kb, "ent_wanshoujie")
        assert "太监" in wsj_text, "禁令性提及必须显式存在"
        for sentence in re.split("[。；]", wsj_text):
            if "太监" in sentence:
                assert any(k in sentence for k in ("严禁", "不得", "禁止", "不设",
                                                   "非")), sentence
        tly = kb.states["st_tly_qianlong"]
        assert "俱以内监为之" in tly.function and "园子里" in tly.function
        ad = kb.adoptions["prop_wsj_zhenmaimai"]
        assert ad.status == EpistemicStatus.VERIFIED
        assert "布景性质" in kb.propositions["prop_wsj_zhenmaimai"].statement

    def test_1860_no_state_for_wanshoujie(self, kb):
        """1860 年万寿街无直接记录 → 不设状态：「被焚毁」直说结构上不可通过"""
        assert kb.state_at("ent_wanshoujie", 1860) is None
        assert kb.state_at("ent_wanshoujie", 1859).id == "st_wsj_1761"
        assert kb.state_at("ent_wanshoujie", 1861).id == "st_wsj_lingluo"
        r = audit_script(kb, "1860年，苏州街被英法联军焚毁。")
        assert r[0].verdict != AuditVerdict.PASS, r[0].reason

    def test_1860_contrast_houxihe_burn_passes(self, kb):
        """同一句式对 B（后溪河买卖街，园史直录焚毁）必须放行——两向对照"""
        r = audit_script(kb, "1860年，后溪河买卖街被焚毁。")
        assert r[0].verdict == AuditVerdict.PASS, r[0].reason
        st = kb.state_at("ent_houxihe_jie", 1860)
        assert st is not None and st.id == "st_hxh_qing"

    def test_huifei_koujing_tianzhi(self, kb):
        """毁废口径：《天咫偶闻》「今已毁尽」；状态层不得出现未限定的联军焚毁断言"""
        states_text = _states_text(kb)
        assert "英法联军烧毁" not in states_text, \
            "焚毁直说只能出现在禁令/命题层，不得进入状态层"
        assert "今已毀盡" in kb.facts["tf_tzow_wanshoujie"].verbatim_quote
        ad = kb.adoptions["prop_huifei_koujing"]
        assert ad.status == EpistemicStatus.VERIFIED
        assert "日就零落" in kb.facts["tf_tzow_lingluo"].verbatim_quote

    def test_ab_two_entities_distinct(self, kb):
        """A（万寿街）/B（后溪河）分属两个实体，同名不得互指"""
        assert kb.references_by_id["rr_suzhoujie"].referent_entity_id == \
            "ent_wanshoujie"
        assert kb.references_by_id["rr_hxh"].referent_entity_id == \
            "ent_houxihe_jie"
        prop = kb.propositions["prop_ab_distinct"]
        assert "两个对象" in prop.statement
        ad = kb.adoptions["prop_ab_distinct"]
        assert ad.status == EpistemicStatus.VERIFIED

    def test_dongji_motive_is_documented_not_legend(self, kb):
        """动机有清人记述（据昭梿记），但不得加心理戏"""
        q = kb.facts["tf_xtzl_1761"].verbatim_quote
        assert "素喜江南風景" in q and "年邁不宜遠行" in q
        states_text = _states_text(kb)
        for banned in ("念念不忘", "博母亲一笑", "博母欢心"):
            assert banned not in states_text, banned

    def test_storyboard_wanshoujie_gap_is_explicit(self, kb):
        """状态链：1761-1859 → 1861-1907，1860 空档必须显式暴露（不静默缝合）"""
        sb = export_storyboard(kb, "ent_wanshoujie")
        assert [f.state_id for f in sb.frames] == ["st_wsj_1761",
                                                   "st_wsj_lingluo"]
        assert any("1859" in w and "1861" in w
                   for w in sb.discontinuity_warnings), sb.discontinuity_warnings

    def test_storyboard_tongleyuan(self, kb):
        sb = export_storyboard(kb, "ent_tongleyuan_jie")
        assert [f.state_id for f in sb.frames] == ["st_tly_qianlong"]


# ==================================================================
# E13 红线：名称三段分层，1953 初创神话拦截
# ==================================================================

class TestZhongguancunRedlines:
    def test_zhongguan_not_invented_in_1953(self, kb):
        """「中关」1913 已见于《京西图》：1953 初创神话必须被拦下"""
        assert "中关" in kb.facts["tf_jingxitu_1913"].verbatim_quote
        assert "1913" in kb.facts["tf_jingxitu_1913"].verbatim_quote
        prop = kb.propositions["prop_zgc_two_step"]
        assert "两步走" in prop.statement and "1913" in prop.statement
        ad = kb.adoptions["prop_zgc_two_step"]
        assert ad.status == EpistemicStatus.VERIFIED
        r = audit_script(kb, "1953年，中关村这个名字第一次出现。")
        assert r[0].verdict != AuditVerdict.PASS, r[0].reason

    def test_name_three_layers(self, kb):
        """中官村（明清）→ 中关（1913 图证）→ 中关村（1950年代机构定名）分层"""
        assert kb.appellations["app_zhongguan_cun"].kind == \
            AppellationKind.VULGAR
        assert kb.appellations["app_zhongguan"].kind == \
            AppellationKind.EUPHEMISTIC
        assert kb.appellations["app_zgc"].valid_time_span.begin.gregorian.year \
            == 1953
        assert "中官坟" in kb.appellations["app_zhongguan_cun"].script_variants
        dia = kb.identities[0]
        assert dia.relation.value == "同一持续体"
        assert dia.status == EpistemicStatus.VERIFIED

    def test_yidi_not_whole_village(self, kb):
        """「中官坟」≠ 全村皆坟：范围辨析必须显式"""
        st = kb.states["st_zgc_yidi"]
        assert "非整村皆坟" in st.geometry
        prop = kb.propositions["prop_zgc_yidi"]
        assert "非整村皆坟" in "；".join(prop.alternative_explanations) + \
            prop.statement

    def test_wuzhi_is_oral_history(self, kb):
        """误植说挂「据当事人回忆」，CONTESTED；不得作「史载」"""
        ad = kb.adoptions["prop_zgc_1953_wuzhi"]
        assert ad.status == EpistemicStatus.CONTESTED and ad.confidence < 0.7
        prop = kb.propositions["prop_zgc_1953_wuzhi"]
        assert "当事人回忆" in prop.statement and "口述史料" in prop.statement

    def test_chenyuan_downgraded_to_yishuo(self, kb):
        """陈垣雅化说降「一说」：UNSUBSTANTIATED 且置信度低"""
        ad = kb.adoptions["prop_zgc_chenyuan"]
        assert ad.status == EpistemicStatus.UNSUBSTANTIATED
        assert ad.confidence <= 0.4
        prop = kb.propositions["prop_zgc_chenyuan"]
        assert "1913" in prop.statement, "1913 图证是降级的核心理由"

    def test_science_city_not_in_states(self, kb):
        """1950 年代中科院入驻无一手书证：只登记命题口径，状态层止于 1952"""
        assert kb.state_at("ent_zhongguancun", 1953) is None
        assert kb.state_at("ent_zhongguancun", 1952).id == "st_zgc_1913"
        ad = kb.adoptions["prop_zgc_kecheng"]
        assert "不入状态层" in kb.propositions["prop_zgc_kecheng"].statement
        assert ad.rationale

    def test_storyboard_zhongguancun(self, kb):
        sb = export_storyboard(kb, "ent_zhongguancun")
        assert [f.state_id for f in sb.frames] == ["st_zgc_yidi", "st_zgc_1913"]


# ==================================================================
# 审计器两向验证（抓真错 + 放真话）
# ==================================================================

class TestAudit:
    def test_taijian_transplant_blocked(self, kb):
        """「太监宫女扮商贩」移植给万寿街：无年份句不得判通过"""
        r = audit_script(kb, "苏州街上的商贩都是太监宫女扮演的。")
        assert r[0].verdict != AuditVerdict.PASS, r[0].reason

    def test_extinction_mixed_sentence_blocked(self, kb):
        """混合句（焚毁＋从此消失）：1860 无状态 → 非通过"""
        r = audit_script(kb, "1860年，英法联军焚毁苏州街，街上太监开设的店铺从此消失。")
        assert r[0].verdict != AuditVerdict.PASS, r[0].reason

    def test_yuannei_taijian_claim_passes(self, kb):
        """园内同句式放行——证明闸门不是见「太监」就拦（判据非恒真）"""
        r = audit_script(kb, "1780年，同乐园买卖街开店者俱以内监为之。")
        assert r[0].verdict == AuditVerdict.PASS, r[0].reason

    def test_1913_zhongguan_passes(self, kb):
        r = audit_script(kb, "1913年，《京西图》上已标注「中关」。")
        assert r[0].verdict == AuditVerdict.PASS, r[0].reason

    def test_1800_yidi_passes(self, kb):
        r = audit_script(kb, "1800年，中官村一带是埋葬太监的义地。")
        assert r[0].verdict == AuditVerdict.PASS, r[0].reason

    def test_1907_huijin_passes(self, kb):
        r = audit_script(kb, "1907年，万寿街俗称苏州街，晚清记载今已毁尽。")
        assert r[0].verdict == AuditVerdict.PASS, r[0].reason

    def test_1953_first_appearance_not_pass(self, kb):
        r = audit_script(kb, "1953年，中关村这个名字第一次出现。")
        assert r[0].verdict != AuditVerdict.PASS
        assert "缺证据" in r[0].reason
