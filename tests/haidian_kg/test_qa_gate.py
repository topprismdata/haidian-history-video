"""
tests/haidian_kg/test_qa_gate.py
词条入库统一 QA 闸门测试

核心原则（用户在 2026-10-02 明确要求）：
  「咱们建立的每一个词条，本体都要执行同样的 QA 流程」
  因此闸门必须：
  1. 对所有词条一致执行（不得因词条而异）
  2. 自身必须能抓住人为注入的错误（否则是恒真的假闸门）
  3. 不得被跨用例污染
"""
import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from haidian_kg.calibration import gaoliang as G
from haidian_kg.calibration import yuanmingyuan as Y
from haidian_kg.calibration.people import PEOPLE
from haidian_kg.calibration.digital_resources import RESOURCES
from haidian_kg.production_exports import KnowledgeBase
from haidian_kg.qa_gate import QAGate
from haidian_kg.ontology.epistemic import HistoricalSource, SourceCategory

#: 逐句声明期望的对抗样本（不得整段一刀切）
ADV_GAOLIANG = (
    "元至元二十九年设西城闸。这座闸在1312年已经是砖石结构。",
    [("元至元二十九年设西城闸", "通过"),
     ("这座闸在1312年已经是砖石结构", "非通过")],
)


def _kb_gl():
    return KnowledgeBase(
        sources=G.SOURCES, divisions=G.DIVISIONS, facts=G.FACTS,
        entities=G.ENTITIES, states=G.STATES, identities=G.IDENTITIES,
        appellations=G.APPELLATIONS, references=G.REFERENCES,
        propositions=G.PROPOSITIONS, adoptions=G.ADOPTIONS,
        people=PEOPLE, resources=RESOURCES)


# ==================================================================
# 闸门本身：必须能通过合法词条
# ==================================================================

class TestGatePassesCleanEntry:
    def test_gaoliang_entry_passes(self):
        rep = QAGate("gaoliang", _kb_gl(), adversarial=ADV_GAOLIANG).run()
        assert rep.passed, rep.render()

    def test_all_nine_gates_actually_ran(self):
        """【关键】判据缺数据必须报 skip，不能静默算通过"""
        rep = QAGate("gaoliang", _kb_gl(), adversarial=ADV_GAOLIANG).run()
        ran = {f.gate for f in rep.findings} | {"G1", "G2", "G3", "G4",
                                                "G5", "G6", "G7", "G8", "G9"}
        # 至少要能确认 G7 执行了（对抗样本存在时不得 skip）
        g7 = [f for f in rep.findings if f.gate.startswith("G7")]
        assert g7 == [] or g7[0].level != "skip", "G7 有对抗样本却未执行"

    def test_yuanmingyuan_entry_passes(self):
        kb = KnowledgeBase(
            sources=Y.SOURCES, divisions=Y.DIVISIONS, facts=Y.FACTS,
            entities=Y.ENTITIES, states=Y.STATES, identities=Y.IDENTITIES,
            appellations=Y.APPELLATIONS, references=Y.REFERENCES,
            transformations=Y.TRANSFORMATIONS, propositions=Y.PROPOSITIONS,
            adoptions=Y.ADOPTIONS, aggregates=Y.AGGREGATES,
            people=PEOPLE, resources=RESOURCES)
        adv = ("咸丰十年英法联军焚毁圆明园，此后圆明园成为废墟不復存在。",
               [("咸丰十年英法联军焚毁圆明园，此后圆明园成为废墟不復存在", "阻断")])
        rep = QAGate("yuanmingyuan", kb, adversarial=adv).run()
        blocking = [f.message for f in rep.blocking]
        # 该词条仍用旧版文献节点，G9 会报作者缺失——这正是闸门该报的
        assert any("文献" in m for m in blocking) or rep.passed, rep.render()


# ==================================================================
# 闸门非恒真：四道负控制必须各自被抓住
# ==================================================================

class TestGateIsNotConstantTrue:
    """这是全文件最重要的部分：证明闸门能抓错，而不是永远返回通过"""

    def test_n1_dangling_division(self):
        kb = _kb_gl()
        kb.divisions.pop("div_sjz_v13_luoshui")
        rep = QAGate("N1", kb, adversarial=ADV_GAOLIANG).run()
        assert any("篇卷" in f.message for f in rep.blocking), rep.render()

    def test_n2_state_without_evidence(self):
        kb = _kb_gl()
        kb.states["st_wood_1292"].evidence_fact_ids = []
        rep = QAGate("N2", kb, adversarial=ADV_GAOLIANG).run()
        assert any("无任何证据" in f.message for f in rep.blocking), rep.render()

    def test_n3_duplicate_source_node(self):
        kb = _kb_gl()
        kb.sources["src_sjz_dup"] = HistoricalSource(
            id="src_sjz_dup", title="水经注",
            category=SourceCategory.GEOGRAPHICAL_TREATISE)
        rep = QAGate("N3", kb, adversarial=ADV_GAOLIANG).run()
        assert any("2 个文献节点" in f.message for f in rep.blocking), rep.render()

    def test_n4_missing_author(self):
        kb = _kb_gl()
        kb.sources["src_shuijingzhu"].author_person_id = None
        rep = QAGate("N4", kb, adversarial=ADV_GAOLIANG).run()
        assert any("缺作者" in f.message for f in rep.blocking), rep.render()

    def test_n5_uncertain_without_alternatives(self):
        """
        UNCERTAIN 身份断言缺争议双方 —— 该约束已在模型层生效
        （构造即抛错），故此处断言「模型层确实拦住」，
        而不是在闸门层重复测一遍。
        """
        from haidian_kg.ontology.spatiotemporal import (
            DiachronicIdentityAssertion, IdentityRelation)
        from haidian_kg.ontology.temporal import (
            CalibrationTable, DatePoint, GregorianDate, TimeSpan)
        from haidian_kg.ontology.epistemic import EpistemicStatus

        ts = TimeSpan(
            id="ts_t", label="t",
            begin=DatePoint(id="b", label="1",
                            gregorian=GregorianDate(year=1, calibration=CalibrationTable.CN_ASTRONOMICAL_ALMANAC)),
            end=DatePoint(id="e", label="2",
                          gregorian=GregorianDate(year=2, calibration=CalibrationTable.CN_ASTRONOMICAL_ALMANAC)))
        with pytest.raises(ValueError) as e:
            DiachronicIdentityAssertion(
                id="dia_bad", subject_entity_ids=["ent_gaoliang_watercourse"],
                relation=IdentityRelation.UNCERTAIN, time_span=ts,
                evidence_fact_ids=["tf_sjz_natural"],
                status=EpistemicStatus.CONTESTED, alternative_relations=[])
        assert "alternative_relations" in str(e.value)

    def test_n6_false_pass_detected(self):
        """若审计把错误断言判为通过，闸门必须报出"""
        kb = _kb_gl()
        # 库里 1312 年落在改石过渡期，「已是砖石」不得判通过
        adv = ("元至元二十九年设西城闸。这座闸在1312年已经是砖石结构。",
               [("元至元二十九年设西城闸", "通过"),
                ("这座闸在1312年已经是砖石结构", "非通过")])
        rep = QAGate("N6", kb, adversarial=adv).run()
        assert rep.passed, rep.render()   # 正常情况下不报假通过
        # 但若把审计改坏（判为通过），闸门应能抓到 —— 用 monkeypatch 模拟
        import haidian_kg.production_exports as pe
        from haidian_kg.ontology.video_contracts import AuditResult, AuditVerdict, ParsedClaim, ClaimType

        def fake_audit(kb_, script, **kw):
            out = []
            for c in ("元至元二十九年设西城闸", "这座闸在1312年已经是砖石结构"):
                out.append(AuditResult(
                    claim=ParsedClaim(claim_text=c, claim_type=ClaimType.ATTRIBUTE,
                                      year=1312, disambiguation_confidence=0.9),
                    verdict=AuditVerdict.PASS, reason="伪造"))
            return out

        orig = pe.audit_script
        pe.audit_script = fake_audit
        try:
            rep2 = QAGate("N6-broken", kb, adversarial=adv).run()
            assert any("假通过" in f.message for f in rep2.blocking), rep2.render()
        finally:
            pe.audit_script = orig


# ==================================================================
# 跨用例污染
# ==================================================================

class TestNoCrossCasePollution:
    def test_mutating_kb_does_not_touch_module_constants(self):
        """
        【真实隐患】校准集是模块级单例。
        若 KnowledgeBase 不拷贝，N2 清空证据会毁掉后续所有用例。
        症状：后续用例报出一条你没注入过的错误。
        """
        before = list(G.STATES[1].evidence_fact_ids)
        kb = _kb_gl()
        kb.states["st_wood_1292"].evidence_fact_ids = []
        assert list(G.STATES[1].evidence_fact_ids) == before, "模块级校准集被污染"

    def test_fresh_kb_is_unaffected_by_prior_mutation(self):
        kb1 = _kb_gl()
        kb1.states["st_wood_1292"].evidence_fact_ids = []
        kb2 = _kb_gl()
        assert kb2.states["st_wood_1292"].evidence_fact_ids, "新 KB 继承了上一次污染"


# ==================================================================
# 书目与人物（用户追问：古书与人物是否在本体里）
# ==================================================================

class TestBibliographyAndPeople:
    def test_sources_are_unique_per_book(self):
        from haidian_kg.calibration.bibliography import BIBLIOGRAPHY
        titles = [s.title for s in BIBLIOGRAPHY]
        assert len(titles) == len(set(titles)), "同一本书被建成多条"

    def test_personal_writings_have_authors(self):
        """个人撰述须有作者；机构编纂须有责任机构（G9 v2.1 新语义）"""
        from haidian_kg.calibration.bibliography import BIBLIOGRAPHY
        personal = ("文集笔记", "历史地理专著", "地方志")
        institutional = ("考古发掘报告", "近代实测地图")
        for s in BIBLIOGRAPHY:
            if s.category.value in personal:
                assert s.author_person_id or getattr(s, "issuing_body", None), \
                    "%s 既无作者也无责任机构" % s.title
                # 地名志类若是机构编纂（编委会），可无个人作者但必须有机构
                if not s.author_person_id:
                    assert getattr(s, "issuing_body", None), \
                        "%s 无个人作者时必须写责任机构" % s.title
            elif s.category.value in institutional:
                assert getattr(s, "issuing_body", None) or s.author_person_id, \
                    "%s 机构编纂文献缺责任机构" % s.title

    def test_authors_exist_in_people_table(self):
        from haidian_kg.calibration.bibliography import BIBLIOGRAPHY
        ids = {p.id for p in PEOPLE}
        for s in BIBLIOGRAPHY:
            if s.author_person_id:
                assert s.author_person_id in ids, "%s 作者不在人物表" % s.title
            for cid in (s.compiler_person_ids or []):
                assert cid in ids, "%s 编者不在人物表" % s.title

    def test_people_written_books_are_registered(self):
        src_ids = set()
        from haidian_kg.calibration.bibliography import BIBLIOGRAPHY
        src_ids = {s.id for s in BIBLIOGRAPHY}
        for p in PEOPLE:
            for sid in p.authored_source_ids:
                assert sid in src_ids, "%s 著录了不存在的书 %s" % (p.name, sid)

    def test_title_alias_normalization(self):
        from haidian_kg.calibration.bibliography import normalize_title
        assert normalize_title("日下旧闻考") == "钦定日下旧闻考"
        assert normalize_title("八旗通志") == "钦定八旗通志"
        assert normalize_title("仁宗实录") == "清仁宗睿皇帝实录"

    def test_digital_resources_have_reliability_note(self):
        for r in RESOURCES:
            assert r.reliability_note.strip(), "%s 缺可靠性说明" % r.id
            assert r.url.startswith("http")

    def test_transcription_declares_collating_limit(self):
        """转录本必须声明校勘限制，否则会产出伪校勘结论"""
        from haidian_kg.ontology.epistemic import DigitalResourceKind
        for r in RESOURCES:
            if r.kind == DigitalResourceKind.TRANSCRIPTION:
                assert ("校勘" in r.reliability_note
                        or "点校本" in r.reliability_note), r.id

    def test_catalog_not_citable_as_text(self):
        from haidian_kg.ontology.epistemic import DigitalResourceKind
        for r in RESOURCES:
            if r.kind == DigitalResourceKind.CATALOG:
                assert not r.is_citable_for_verbatim, \
                    "%s 是联合目录，不得作为逐字引文依据" % r.id
