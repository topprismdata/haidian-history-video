"""
tests/haidian_kg/test_dazhongsi_entry.py
大钟寺（觉生寺）词条入库测试（E9，第一次闭包 v3 真实 admission）

史料基准（全部为 research.md v2 冻结结论 + 本体一手引文）：
- 1733 开工与 1734 赐名分属两个 State，绝不混写同年
- 钟链：永乐铸（存疑）→汉经厂（推断）→1607 万寿寺→天启弃置卧地约 120 年→1743 觉生寺
- 1743 迁钟与 1746 大钟歌分挂两个篇卷
- 祈雨：寺是场所（1778 起，西墙外设坛）≠ 钟参与（2023 课题 DISPROVEN）
- 「华严钟」为讹名：钟上并无《华严经》，至少晚明已流传
- 铭文「铭铸」23 万余字；钟高 6.75 米（博物馆口径）
"""
import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from haidian_kg.calibration import dazhongsi as D
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
        sources=D.SOURCES, divisions=D.DIVISIONS, facts=D.FACTS,
        entities=D.ENTITIES, states=D.STATES, identities=D.IDENTITIES,
        appellations=D.APPELLATIONS, references=D.REFERENCES,
        transformations=D.TRANSFORMATIONS, propositions=D.PROPOSITIONS,
        adoptions=D.ADOPTIONS, aggregates=D.AGGREGATES,
        people=PEOPLE, resources=RESOURCES)


#: 逐句期望的对抗样本：真陈述 + 「毁损=消亡」假通过
ADV = ("乾隆八年，永乐大钟移入觉生寺大钟殿。永乐大钟天启三年弃地，此后不复存在。",
       [("乾隆八年，永乐大钟移入觉生寺大钟殿", "通过"),
        ("永乐大钟天启三年弃地，此后不复存在", "非通过")])


# ==================================================================
# 入库闸门
# ==================================================================

class TestDazhongsiEntryGate:
    def test_entry_passes_gate(self, kb):
        rep = QAGate("dazhongsi", kb, adversarial=ADV).run()
        assert rep.passed, rep.render()

    def test_uses_unified_bibliography(self, kb):
        """一部书只能一个节点；《燕邸纪闻》不得独立建目"""
        titles = [s.title for s in kb.sources.values()]
        assert len(titles) == len(set(titles)), "同一本书被建成多条：%s" % titles
        assert "燕邸纪闻" not in titles, "《燕邸纪闻》是转引，不得独立建目"
        assert "钦定日下旧闻考" in titles, "转引引文的 provenance 必须挂日下旧闻考"

    def test_all_facts_traceable(self, kb):
        div_ids = set(kb.divisions.keys())
        for f in kb.facts.values():
            assert f.division_id in div_ids, f.id

    def test_yandijian_marked_as_transit_quote(self, kb):
        f = kb.facts["tf_yandijian_1607"]
        assert f.division_id == "div_rxjwkc100_wanshousi"
        assert "转引" in f.translator_note, "转引必须在 note 标明"


# ==================================================================
# E9 红线：状态链
# ==================================================================

class TestStateChain:
    def test_1733_1734_split(self, kb):
        """开工与赐名是两个年份，分属两个状态"""
        st_1733 = kb.state_at("ent_jueshengsi", 1733)
        st_1734 = kb.state_at("ent_jueshengsi", 1734)
        assert st_1733.id == "st_js_1733"
        assert st_1734.id == "st_js_1734"
        # 赐名碑文事实只允许挂在 1734 状态（结构性防混年）
        assert "tf_beiwen_ciming" not in st_1733.evidence_fact_ids
        assert "tf_beiwen_ciming" in st_1734.evidence_fact_ids
        assert "尚未赐名" in st_1733.function

    def test_bell_chain_years(self, kb):
        assert kb.state_at("ent_yongle_bell", 1600).id == "st_bell_cast_hjc"
        assert kb.state_at("ent_yongle_bell", 1610).id == "st_bell_wanshousi"
        assert kb.state_at("ent_yongle_bell", 1700).id == "st_bell_laid"
        assert kb.state_at("ent_yongle_bell", 1900).id == "st_bell_jueshengsi"

    def test_laid_about_120_years_not_300(self, kb):
        st = kb.states["st_bell_laid"]
        assert st.time_span.begin.gregorian.year == 1621
        assert st.time_span.end.gregorian.year == 1742
        for node in list(kb.states.values()) + list(kb.propositions.values()):
            text = "%s%s%s" % (getattr(node, "geometry", "") or "",
                               getattr(node, "function", "") or "",
                               getattr(node, "statement", "") or "")
            assert "卧地三百年" not in text and "躺了三百年" not in text, \
                "卧地约一百二十年，不得作三百年肯定表述"

    def test_cast_year_not_asserted(self, kb):
        ad = kb.adoptions["prop_bell_cast_year"]
        assert ad.status == EpistemicStatus.CONTESTED
        blob = " ".join(p.statement for p in kb.propositions.values())
        assert "1424" in blob and "定论" in blob, "1424 必须显式标注为非定论"

    def test_relocations_1607_1743(self, kb):
        assert kb.transformations["pte_bell_1607_relocate"].time_span.begin \
            .gregorian.year == 1607
        assert kb.transformations["pte_bell_1743_relocate"].time_span.begin \
            .gregorian.year == 1743

    def test_storyboard_survives(self, kb):
        sb = export_storyboard(kb, "ent_yongle_bell")
        assert [f.state_id for f in sb.frames] == [
            "st_bell_cast_hjc", "st_bell_wanshousi",
            "st_bell_laid", "st_bell_jueshengsi"]


# ==================================================================
# E9 红线：口径与分级
# ==================================================================

class TestMeasureAndGrading:
    def test_bell_height_museum_scope(self, kb):
        text = kb.states["st_bell_cast_hjc"].geometry + \
            kb.facts["tf_dzs_bell_dims"].verbatim_quote
        assert "6.75" in text, "钟高用博物馆口径 6.75 米"
        all_text = " ".join(
            "%s%s%s" % (s.geometry or "", s.material or "", s.function or "")
            for s in kb.states.values())
        assert "五到七" not in all_text and "5.5" not in all_text

    def test_inscription_counting(self, kb):
        q = kb.facts["tf_dzs_bell_dims"].verbatim_quote
        assert "23万余字" in q
        assert "230,184" not in q and "231,666" not in q, "两套统计不得混用"
        assert "铭铸" in q and "刻" not in q.replace("23", ""), "用「铭铸」不用「刻」"

    def test_huayan_is_misnomer_with_note(self, kb):
        ref = kb.references_by_id["rr_huayanbell"]
        assert ref.referent_entity_id == "ent_yongle_bell"
        assert "并无《华严经》" in ref.provenance, "华严钟讹名 note 必写"
        assert "晚明" in ref.provenance, "流传下限：至少晚明已流传，不得写起源"

    def test_qiyu_split_venue_vs_bell(self, kb):
        assert kb.adoptions["prop_js_qiyu_1778"].status == EpistemicStatus.VERIFIED
        ad = kb.adoptions["prop_bell_qiyu_legend"]
        assert ad.status == EpistemicStatus.DISPROVEN
        assert ad.refuting_fact_ids, "DISPROVEN 必须附反驳证据"
        assert all(fid in kb.facts for fid in ad.refuting_fact_ids)

    def test_qiyu_1778_not_1787(self, kb):
        st = kb.state_at("ent_jueshengsi", 1800)
        assert st.id == "st_js_1778"
        assert st.time_span.begin.reign_year.year_within_reign == 43

    def test_folk_legends_are_legends(self, kb):
        for pid in ("prop_bingdao_legend", "prop_duitu_legend"):
            assert kb.adoptions[pid].status == EpistemicStatus.FOLK_LEGEND, pid

    def test_1743_1746_separate_divisions(self, kb):
        shi = [f for f in kb.facts.values() if f.division_id == "div_qgz_1743_shi"]
        ge = [f for f in kb.facts.values() if f.division_id == "div_qgz_1746_ge"]
        assert shi and ge, "1743 诗与 1746 歌必须分挂两个篇卷"
        assert all(f.source_year.gregorian.year == 1743 for f in shi)
        assert all(f.source_year.gregorian.year == 1746 for f in ge)


# ==================================================================
# 审计器两向验证（抓真错 + 放真话）
# ==================================================================

class TestAudit:
    def test_false_extinction_blocked(self, kb):
        r = audit_script(kb, "永乐大钟天启三年弃地，此后不复存在。")
        assert r[0].verdict == AuditVerdict.BLOCK, r[0].reason

    def test_numeric_conflict_blocked(self, kb):
        """民国庙会数字必须与该状态记录一致；商摊 500 处 = 口径混说"""
        r = audit_script(kb, "1913年，觉生寺庙会曾有商摊500处。")
        assert r[0].verdict == AuditVerdict.BLOCK, r[0].reason

    def test_true_statement_passes(self, kb):
        r = audit_script(kb, "乾隆八年，永乐大钟移入觉生寺大钟殿。")
        assert r[0].verdict == AuditVerdict.PASS, r[0].reason

    def test_wrong_building_year_blocked_or_untestable(self, kb):
        """「寺为钟而建」在 1743 年敕建 = 红线，至少不得判通过"""
        r = audit_script(kb, "乾隆八年，官府为悬挂大钟敕建觉生寺。")
        assert r[0].verdict != AuditVerdict.PASS or "敕建" not in r[0].reason
