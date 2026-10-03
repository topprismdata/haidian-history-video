"""
tests/haidian_kg/test_weigongcun_entry.py
魏公村／畏吾村 E21 入库闸门测试

每个测试锁一条闸门红线或负控制。红线被改写时测试必须失败——
「测试全过」若不能拦住红线改写，就是恒真测试，不允许存在。

本集特有红线：
  L1 分层铁律：《元史》(L2) 只证 族属/廉姓/廉孟子/卒年五十/追封魏国公谥文正；
     葬地与守冢廉姓属 查礼《畏吾村考》(L3 金石考据笔记)，畏吾部落聚居属
     乔松年《萝藦亭札记》(L3)——L2/L3 绝不混级（Task1 直核：卷126无「畏吾」）。
  L2 国保：大慧寺 5-199（第五批，2001）。
  L3 祖茔：李东阳祖茔挂《怀麓堂集》卷75（L2 转引层标注）。
  L4 档案地图：1915《实测京师四郊图》「魏公村」＝记录式转录，与古籍分层。
  NC1 汉族魏姓初建说必须 DISPROVEN。
  NC2 魏忠贤庄田说必须 DISPROVEN。
  NC3 「魏国公」爵位唯一定名诱因说必须 DISPROVEN（V-NC02）。
  NC4 守冢廉姓＝廉希宪后人保持 CONTESTED（查礼自标「疑即」，禁升格）。
  NC5 墓园复原 UNSUBSTANTIATED（V-NC03，禁AI生成复原图）。

Python 3.9.6：禁 X | None、禁 match。
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from haidian_kg.calibration import weigongcun as W
from haidian_kg.calibration import bibliography as BIB
from haidian_kg.calibration.people import PEOPLE
from haidian_kg.calibration.digital_resources import RESOURCES
from haidian_kg.production_exports import KnowledgeBase, audit_script
from haidian_kg.qa_gate import QAGate
from haidian_kg.ontology.epistemic import (
    EpistemicStatus, HistoricalSource, SourceCategory,
)
from haidian_kg.ontology.spatiotemporal import AppellationKind


#: 正片审计脚本：每句都是研究档案冻结结论，逐句必须「通过」
_GATE_SCRIPT = (
    "1280年廉希宪归葬大都宛平之西，守冢族人聚居之地号畏吾村。\n"
    "1513年大慧寺建于宛平县香山乡畏吾村。\n"
    "1700年前后畏吾村俗写已见畏兀村。\n"
    "1915年实测京师四郊图标绘魏公村。\n"
    "1951年中央民族学院选址于魏公村一带。\n"
    "2001年大慧寺列为全国重点文物保护单位，编号5-199。\n"
)

#: 对抗样本：消亡假通过 + 数字口径混说，逐句必须「非通过」
_ADV = (
    "1644年畏吾村彻底消失，此后不复存在。\n1513年大慧寺建成殿宇三百楹。",
    [("1644年畏吾村彻底消失，此后不复存在", "非通过"),
     ("1513年大慧寺建成殿宇三百楹", "非通过")],
)


@pytest.fixture(scope="module")
def kb():
    return KnowledgeBase(
        sources=W.SOURCES, divisions=W.DIVISIONS, facts=W.FACTS,
        entities=W.ENTITIES, states=W.STATES, identities=W.IDENTITIES,
        appellations=W.APPELLATIONS, references=W.REFERENCES,
        transformations=W.TRANSFORMATIONS, propositions=W.PROPOSITIONS,
        adoptions=W.ADOPTIONS, aggregates=W.AGGREGATES,
        people=PEOPLE, resources=RESOURCES)


def _prop(pid):
    for p in W.PROPOSITIONS:
        if p.id == pid:
            return p
    raise AssertionError("proposition 不存在: %s" % pid)


def _adopt(pid):
    for a in W.ADOPTIONS:
        if a.proposition_id == pid:
            return a
    raise AssertionError("adoption 不存在: %s" % pid)


def _fact(fid):
    for f in W.FACTS:
        if f.id == fid:
            return f
    raise AssertionError("fact 不存在: %s" % fid)


def _facts_of_source(source_id):
    div_ids = {d.id for d in W.DIVISIONS if d.source_id == source_id}
    return [f for f in W.FACTS if f.division_id in div_ids]


# ==================================================================
# 入库闸门
# ==================================================================

class TestWeigongcunEntryGate:
    def test_entry_passes_qa_gate(self, kb):
        rep = QAGate("weigongcun", kb, adversarial=_ADV).run()
        assert rep.passed, rep.render()

    def test_gate_has_zero_skip(self, kb):
        """skip 不算通过（判据缺数据必须显式暴露）。"""
        rep = QAGate("weigongcun", kb, adversarial=_ADV).run()
        skips = [f for f in rep.findings if f.level == "skip"]
        assert skips == [], "闸门存在未执行项: %s" % skips

    def test_adversarial_actually_blocked(self, kb):
        """负控制对称性：消亡断言与数字混说都必须被拦，防恒真闸门。"""
        results = audit_script(kb, _ADV[0])
        by_text = {r.claim.claim_text: r for r in results}
        for clause, expected in _ADV[1]:
            r = by_text.get(clause)
            assert r is not None, "对抗子句未产生审计结果: %s" % clause
            assert r.verdict.value != "通过", "假通过: %s" % clause

    def test_gate_script_every_sentence_passes(self, kb):
        """六句正片审计全部「通过」——证明审计真的命中了历史状态，不是 UNTESTABLE 凑数。"""
        results = audit_script(kb, _GATE_SCRIPT)
        assert len(results) == 6, [r.claim.claim_text for r in results]
        for r in results:
            assert r.verdict.value == "通过", (
                "%s -> %s: %s" % (r.claim.claim_text, r.verdict.value, r.reason))

    def test_all_sources_resolved(self, kb):
        """source_by_title 若漏配会静默返回 None——SOURCES 里不允许 None。"""
        assert all(isinstance(s, HistoricalSource) for s in W.SOURCES)

    def test_uses_unified_bibliography(self, kb):
        titles = [s.title for s in kb.sources.values()]
        assert len(titles) == len(set(titles)), "一书一条被破坏: %s" % titles
        assert "元史" in titles, "元史必须复用统一书目表节点"
        assert kb.sources["src_yuanshi"].category == SourceCategory.OFFICIAL_HISTORY
        # 与 1913 京西图是两部图籍，严禁并档
        assert "京西图（1913）" not in titles
        assert "实测京师四郊图（1915）" in titles

    def test_all_facts_traceable(self, kb):
        div_ids = set(kb.divisions.keys())
        for f in kb.facts.values():
            assert f.division_id in div_ids, f.id


# ==================================================================
# L1 分层铁律：《元史》与方志考据严密分层
# ==================================================================

class TestYuanshiVsGazetteerLayering:
    def test_no_yuanshi_fact_carries_weiwu_or_burial(self):
        """Task1 直核：卷126廉希宪传无「畏吾」、无葬地文——两条混入即混级。
        卷125「布魯海牙畏吾人也」是族属书证（合法），但不得出现村名。"""
        for f in _facts_of_source("src_yuanshi"):
            if f.division_id == "div_ys126_lianxixian":
                assert "畏吾" not in f.verbatim_quote, (
                    "%s 的引文混入「畏吾」——卷126无此书证" % f.id)
                assert "葬" not in f.verbatim_quote, (
                    "%s 的引文混入葬地文——卷126无葬地书证" % f.id)
            elif f.division_id == "div_ys125_buluhaiya":
                assert "村" not in f.verbatim_quote, (
                    "%s 的引文混入村名——卷125只证族属与得姓" % f.id)

    def test_yuanshi_facts_are_the_fixed_attested_set(self):
        """《元史》层：族属/廉姓由来/廉孟子/卒年五十/追封谥号——多一条即混级，少一条即缺证。"""
        ys = sorted(f.id for f in _facts_of_source("src_yuanshi"))
        assert ys == [
            "tf_ys125_lian_surname", "tf_ys125_weiwu_ren", "tf_ys126_death",
            "tf_ys126_duhao_jingshi", "tf_ys126_fengwei_guogong",
            "tf_ys126_hengyang_wang", "tf_ys126_identity", "tf_ys126_lianmengzi",
        ]

    def test_burial_evidence_hangs_on_chali_level3(self):
        """葬地/守冢链必须挂在查礼《畏吾村考》（金石类目，L3 转引），不得冒充正史。"""
        src = BIB.source_by_title("畏吾村考")
        assert src.category == SourceCategory.EPIGRAPHY, "查礼笔记属金石考据类目"
        f = _fact("tf_wwck_shouzhong_lian")
        assert f.division_id == "div_wwck_main"
        assert "转引" in f.translator_note, "L3 转引链必须显式标注"

    def test_tribe_evidence_hangs_on_qiaosongnian_level3(self):
        f = _fact("tf_lmt_weiwucun")
        assert f.division_id == "div_lmtzj_weiwu"
        assert "萝藦亭札记" in BIB.source_by_title("萝藦亭札记").title
        assert "转引" in f.translator_note

    def test_yuanshi_burial_quote_is_meta_disproven(self):
        """「《元史》载葬畏吾村」这一伪引文本身必须是 DISPROVEN 假说节点。"""
        a = _adopt("prop_yuanshi_burial_quote")
        assert a.status == EpistemicStatus.DISPROVEN
        ys_fact_ids = {f.id for f in _facts_of_source("src_yuanshi")}
        assert a.refuting_fact_ids, "证伪必须给反驳证据"
        assert set(a.refuting_fact_ids) & ys_fact_ids, (
            "反驳证据必须含《元史》自身事实（全传无葬地文的直证）")

    def test_chali_conjecture_prefix_preserved_and_contested(self):
        """「疑即」是查礼自标推测——引文必须完整保留，采信必须保持 CONTESTED。"""
        f = _fact("tf_wwck_shouzhong_lian")
        assert "疑即右丞後人" in f.verbatim_quote
        a = _adopt("prop_shouzhong_lian_descendant")
        assert a.status == EpistemicStatus.CONTESTED, "守冢廉姓=廉希宪后人禁升 VERIFIED"
        assert 0.3 <= a.confidence <= 0.7

    def test_huailutangji_is_level2_with_transit_mark(self):
        """李东阳祖茔=《怀麓堂集》L2，但引文经党宝海文转引，必须显式标注。"""
        src = BIB.source_by_title("怀麓堂集")
        assert src.author_person_id == "person_lidongyang"
        f = _fact("tf_hlt_zumu_weiwu")
        assert f.division_id == "div_hltj75_zumu"
        assert "转引" in f.translator_note
        assert "未直核" in f.translator_note

    def test_l3_sources_never_claim_collated_edition(self):
        """转引层不得标四库本等校勘底本冒充直核。"""
        for title in ("畏吾村考", "萝藦亭札记"):
            src = BIB.source_by_title(title)
            assert src.base_edition != "四库全书本", "%s 原刻未直核" % title
        # 怀麓堂集书影未直核，edition_note 必须带待核标记
        assert "待核" in BIB.source_by_title("怀麓堂集").edition_note


# ==================================================================
# 廉希宪正史事实（L2，直核）
# ==================================================================

class TestLianXixianYuanshiFacts:
    def test_lianmengzi_verbatim(self):
        f = _fact("tf_ys126_lianmengzi")
        assert "世祖嘉之目曰廉孟子" in f.verbatim_quote
        # research.md 转写句「帝尝以廉孟子称之」不是卷126原文，禁回填
        assert "帝嘗以" not in f.verbatim_quote

    def test_death_year_fifty(self):
        f = _fact("tf_ys126_death")
        assert "十七年十一月" in f.verbatim_quote
        assert "是夕希憲卒年五十" in f.verbatim_quote

    def test_posthumous_titles(self):
        f = _fact("tf_ys126_fengwei_guogong")
        assert "追封魏國公諡文正" in f.verbatim_quote
        assert "大德八年" in f.verbatim_quote, "追封在卒后二十四年，不得写卒时即封"
        f2 = _fact("tf_ys126_hengyang_wang")
        assert "恒陽王" in f2.verbatim_quote

    def test_clan_ethnicity_and_surname_from_juan125(self):
        f1 = _fact("tf_ys125_weiwu_ren")
        assert f1.verbatim_quote == "布魯海牙畏吾人也"
        f2 = _fact("tf_ys125_lian_surname")
        assert "故子孫皆姓廉氏" in f2.verbatim_quote
        assert f2.division_id == "div_ys125_buluhaiya"


# ==================================================================
# 大慧寺：建置与国保 5-199
# ==================================================================

class TestDahuisiGuobao:
    def test_zhangxiong_1513_built_in_weiwu(self):
        f = _fact("tf_rxjwkc98_dhs_build")
        assert "正徳癸酉" in f.verbatim_quote, "原文纪年作正德癸酉（=八年）"
        assert "司禮監太監張雄建寺于宛平縣香山鄉畏吾村" in f.verbatim_quote
        assert "賜額曰大慧" in f.verbatim_quote

    def test_juan98_is_jiaokeng_xi8(self):
        """research.md「郊垧西四」勘误：卷98门类为郊坰西八，不得回退。"""
        d = [x for x in W.DIVISIONS if x.id == "div_rxjwkc98_weiwu"][0]
        assert d.section_title == "郊坰西八"
        assert d.volume_number == "卷九十八"

    def test_guobao_5_199_written(self, kb):
        st = kb.states["st_dhs_2001"]
        assert "5-199" in st.geometry
        assert "2001" in st.geometry
        assert st.time_span.begin.gregorian.year == 2001

    def test_wanli_repair_by_wangxijue_not_shenshixing(self):
        """research.md「麦福万历重修/申时行碑」混淆勘误：重修撰记者是王锡爵。"""
        f = _fact("tf_rxjwkc98_dhs_wanli")
        assert "萬厯壬辰重修" in f.verbatim_quote
        assert "王鍚爵撰記" in f.verbatim_quote
        assert "申時行" not in f.verbatim_quote
        note = f.translator_note + _fact("tf_rxjwkc98_dhs_guan").translator_note
        assert "勘误" in note
        assert "麥某" in note or "麦" in note

    def test_lidongyang_wrote_founders_stele(self):
        f = _fact("tf_rxjwkc98_dhs_beiluo")
        assert "大學士茶陵李東陽為碑" in f.verbatim_quote

    def test_dahuisi_state_chain(self, kb):
        assert kb.state_at("ent_dahuisi", 1513).id == "st_dhs_1513"
        assert kb.state_at("ent_dahuisi", 1592).id == "st_dhs_1592"
        assert kb.state_at("ent_dahuisi", 2001).id == "st_dhs_2001"


# ==================================================================
# 李东阳祖茔与墓址湮灭
# ==================================================================

class TestLidongyangAncestorTomb:
    def test_ancestor_tomb_fact(self):
        f = _fact("tf_hlt_zumu_weiwu")
        assert "葬曾祖考妣于畏吾村" in f.verbatim_quote

    def test_tomb_site_lost_by_1783(self):
        f = _fact("tf_rxjwkc98_lidongyang_tomb_lost")
        assert f.verbatim_quote == "李東陽墓今無考"
        st = [s for s in W.STATES if s.id == "st_tomb_qing"][0]
        assert "tf_rxjwkc98_lidongyang_tomb_lost" in st.evidence_fact_ids
        assert "無考" in st.geometry or "无考" in st.geometry

    def test_no_ai_restoration_of_tombs(self):
        """V-NC03：墓园复原是无据推论，且证据视觉纪律入库。"""
        a = _adopt("prop_tomb_restoration")
        assert a.status == EpistemicStatus.UNSUBSTANTIATED
        assert a.confidence <= 0.1
        p = _prop("prop_tomb_restoration")
        assert "严禁" in p.inference_method, "禁AI复原红线必须写在推理方法里"
        assert "AI" in p.inference_method


# ==================================================================
# 1915 实测地图（L2 档案地图，记录式转录）
# ==================================================================

class TestMap1915:
    def test_map_fact_is_record_transcription(self):
        f = _fact("tf_1915_weigongcun")
        assert "魏公村" in f.attested_string
        assert f.source_year.gregorian.year == 1915
        assert "记录式转录" in f.translator_note, "地图标注无逐字文本，必须标转录层"
        assert "不得互冒" in f.translator_note

    def test_map_source_is_institutional_survey(self):
        src = BIB.source_by_title("实测京师四郊图（1915）")
        assert src.category == SourceCategory.MILITARY_SURVEY_MAP
        assert src.issuing_body, "机构图籍必须写明责任机构"
        assert "1913" not in src.title

    def test_weigongcun_appellation_from_1915(self):
        app = [a for a in W.APPELLATIONS if a.label == "魏公村"][0]
        assert app.kind == AppellationKind.EUPHEMISTIC, "1915 定名属雅化名"
        assert app.valid_time_span.begin.gregorian.year == 1915

    def test_rename_is_not_spatial_event(self):
        """改名是称谓层事件——不得伪造空间变换（P0-7 纪律）。"""
        for t in W.TRANSFORMATIONS:
            if t.entity_id == "ent_weigongcun":
                cond = t.resulting_condition or ""
                assert "定名" not in cond and "改名" not in cond
        assert any(t.id == "pte_wgc_1280_form" and
                   t.transformation.value == "新建" for t in W.TRANSFORMATIONS)


# ==================================================================
# 负控制：伪说必须 DISPROVEN / 保持降级
# ==================================================================

class TestNegativeControls:
    def test_han_wei_founder_disproven(self):
        """NC1：汉族魏姓（太监/地主）初建说必须 DISPROVEN 且有正史反驳。"""
        a = _adopt("prop_han_wei_founder")
        assert a.status == EpistemicStatus.DISPROVEN
        assert a.confidence >= 0.9
        refs = set(a.refuting_fact_ids)
        assert "tf_ys125_weiwu_ren" in refs, "族属反驳必须挂《元史》卷125"
        assert "tf_rxjwkc98_dhs_build" in refs or "tf_hlt_zumu_weiwu" in refs

    def test_weizhongxian_disproven_by_chronology(self):
        """NC2：魏忠贤庄田说必须 DISPROVEN，反驳证据须早于魏忠贤（1568年生）。"""
        a = _adopt("prop_weizhongxian_estate")
        assert a.status == EpistemicStatus.DISPROVEN
        assert "tf_rxjwkc98_dhs_build" in a.refuting_fact_ids, "1513 大慧寺早于魏忠贤"
        assert "tf_hlt_zumu_weiwu" in a.refuting_fact_ids

    def test_sole_title_cause_disproven(self):
        """NC3（V-NC02）：「魏国公」是唯一定名诱因说必须 DISPROVEN。"""
        a = _adopt("prop_weiguo_title_sole_cause")
        assert a.status == EpistemicStatus.DISPROVEN
        assert "tf_wwck_guohao" in a.refuting_fact_ids, "音转基底层是反驳核心"

    def test_title_convergence_stays_contested(self):
        """双重合流说保持 CONTESTED——两不抹杀，禁单边化。"""
        a = _adopt("prop_weiguo_title_convergence")
        assert a.status == EpistemicStatus.CONTESTED
        assert 0.3 <= a.confidence <= 0.7

    def test_tribe_origin_verified_with_layered_evidence(self):
        a = _adopt("prop_weiwu_tribe_origin")
        assert a.status == EpistemicStatus.VERIFIED
        refs = set(a.refuting_fact_ids) if a.refuting_fact_ids else set()
        derived = set(_prop("prop_weiwu_tribe_origin").derived_from_fact_ids)
        assert "tf_ys125_weiwu_ren" in derived, "族属层必须挂 L2"
        assert derived & {"tf_wwck_juzudi", "tf_wwck_start_yuan"}, "考据层必须挂 L3"

    def test_wei_jiacun_writing_not_attested(self):
        """「魏家村」书证待核（E21待核3）：不得入引文层与指称层。"""
        for f in W.FACTS:
            assert "魏家村" not in f.verbatim_quote, "%s 混入待核写法" % f.id
        assert not [a for a in W.APPELLATIONS if a.label == "魏家村"]
        # 直核书证是「魏吴村」
        assert _fact("tf_dbh_weiwu_cun").attested_string == "魏吳村"

    def test_weiwu5_folk_legend_stored_not_adopted(self):
        """「卫伍」是查礼明驳的望文生训：存档为 FOLK_LEGEND 指称，不采信。"""
        r = [x for x in W.REFERENCES if x.id == "ref_weiwu5"][0]
        assert r.status == EpistemicStatus.FOLK_LEGEND
        assert r.provenance and "殊失其義" in r.provenance


# ==================================================================
# 状态链与身份
# ==================================================================

class TestStateChain:
    def test_village_chain(self, kb):
        assert kb.state_at("ent_weigongcun", 1300).id == "st_wgc_yuan"
        assert kb.state_at("ent_weigongcun", 1513).id == "st_wgc_ming"
        assert kb.state_at("ent_weigongcun", 1700).id == "st_wgc_qing"
        assert kb.state_at("ent_weigongcun", 1930).id == "st_wgc_1915"
        assert kb.state_at("ent_weigongcun", 2000).id == "st_wgc_1951"

    def test_north_bank_redline(self):
        """V-NC05：村在高梁河北岸台地（Task2 MEC-4 冻结拓扑），不得漂到南岸。"""
        st = [s for s in W.STATES if s.id == "st_wgc_yuan"][0]
        assert "高梁河北岸" in st.geometry
        for s in W.STATES:
            blob = (s.geometry or "") + (s.function or "")
            assert "高梁河南岸" not in blob and "南岸台地" not in blob

    def test_village_is_same_continuant(self):
        d = [i for i in W.IDENTITIES if i.id == "dia_wgc_same_cont"][0]
        assert d.relation.value == "同一持续体"
        assert d.is_orthogonal_to_state_change is True, "改名与聚落本体存续正交"

    def test_village_and_tomb_and_temple_separate_entities(self, kb):
        """墓/寺/校与村分立：墓园湮灭不等于村消亡，寺存续不等于村存续。"""
        ids = set(kb.entities.keys())
        assert {"ent_weigongcun", "ent_lian_jiazu_mu",
                "ent_dahuisi", "ent_minzu_univ"} <= ids

    def test_tomb_chain_time_bounds(self, kb):
        st = kb.state_at("ent_lian_jiazu_mu", 1280)
        assert st.id == "st_tomb_yuan"
        assert st.time_span.begin.gregorian.year == 1280

    def test_no_state_without_evidence(self, kb):
        fact_ids = set(kb.facts.keys())
        for s in kb.states.values():
            assert s.evidence_fact_ids, s.id
            for e in s.evidence_fact_ids:
                assert e in fact_ids, "%s 引用不存在的引文 %s" % (s.id, e)
