"""
tests/haidian_kg/test_pingyuan.py
海淀平原水系聚落线词条入库测试（pingyuan 批）

史料基准（全部一手/记录式，原文存 docs/kg/research/pingyuan.md）：
- 六郎庄：明牛栏庄→雅称柳浪庄→清代六郎庄（区政府记录+卷71官书用名「六郎莊」）；
  杨六郎驻军只能标 FOLK_LEGEND；「乾隆嫌不吉改名」回源为查无官书依据 → UNSUBSTANTIATED
- 泉宗庙：乾隆三十一年(1766)春经始、三十二年(1767)落成（卷79御制诗「祠建泉宗始昨春落成此日」
  +卷99谨按「乾隆三十二年皇上始於其地建泉宗庙」）；泉名凡二十有八；缭垣三百九十四丈；
  长编「乾隆四十三年/十三处泉名」与官书抵牾不采
- 万泉庄：平地涌泉泉源所自出；水自南而北（庄注巴沟入畅春园）；「万泉河」河名无清代书证
- 海淀：词源浅湖之淀；元初书证「海店」（1260）；1952.9.1 第十三区定名海淀区（区名承镇名）
- 三里河（阜成门外）：嘉靖甲午(1534)钟铭为地名书证下限；金代旧迹惟钓鱼台，河道金代开挑存疑；
  与正阳门外三里河（前三门）同名异地
"""
import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from haidian_kg.calibration import pingyuan as P
from haidian_kg.calibration.people import PEOPLE
from haidian_kg.calibration.digital_resources import RESOURCES
from haidian_kg.production_exports import (
    KnowledgeBase, export_storyboard, export_visual_constraints, audit_script,
)
from haidian_kg.qa_gate import QAGate
from haidian_kg.ontology.video_contracts import AuditVerdict
from haidian_kg.ontology.epistemic import EpistemicStatus
from haidian_kg.ontology.spatiotemporal import AppellationKind


@pytest.fixture(scope="module")
def kb():
    return KnowledgeBase(
        sources=P.SOURCES, divisions=P.DIVISIONS, facts=P.FACTS,
        entities=P.ENTITIES, states=P.STATES, identities=P.IDENTITIES,
        appellations=P.APPELLATIONS, references=P.REFERENCES,
        transformations=P.TRANSFORMATIONS, propositions=P.PROPOSITIONS,
        adoptions=P.ADOPTIONS, aggregates=P.AGGREGATES,
        people=PEOPLE, resources=RESOURCES)


#: 逐句对抗样本：真陈述 + 泉数讹写（官书作二十八，讹作三十）
ADV = ("泉宗庙于乾隆三十二年落成，庙内外淙泉立碣二十八处。"
       "泉宗庙于乾隆三十二年立碣名泉三十处。",
       [("泉宗庙于乾隆三十二年落成，庙内外淙泉立碣二十八处", "通过"),
        ("泉宗庙于乾隆三十二年立碣名泉三十处", "非通过")])


# ==================================================================
# 入库闸门
# ==================================================================

class TestPingyuanEntryGate:
    def test_entry_passes_gate(self, kb):
        rep = QAGate("pingyuan", kb, adversarial=ADV).run()
        assert rep.passed, rep.render()

    def test_uses_unified_bibliography(self, kb):
        titles = [s.title for s in kb.sources.values()]
        assert len(titles) == len(set(titles)), "同一本书被建成多条：%s" % titles

    def test_all_facts_traceable(self, kb):
        div_ids = set(kb.divisions.keys())
        for f in kb.facts.values():
            assert f.division_id in div_ids, f.id


# ==================================================================
# 关键实体与字形表（holdout 缺口面必须能从字形表命中）
# ==================================================================

class TestRegistryFaces:
    """本批目标面：holdout run3 KB 覆盖缺口 FP 的真实地名必须可命中"""

    @pytest.fixture(scope="class")
    def registry(self):
        from haidian_kg.evaluation.holdout_eval import (
            build_name_registry, norm_eval,
        )
        reg = build_name_registry(["settlements", "pingyuan"])
        reg.norm = norm_eval
        return reg

    def _forms_of(self, registry, ent_id):
        return {f for f in registry.forms
                if ent_id in registry.entities_of(f)}

    def test_liulangzhuang_chain_faces(self, registry):
        for face in ("六郎庄", "柳浪庄", "牛栏庄"):
            ents = registry.entities_of(registry.norm(face))
            assert "ent_liulangzhuang" in ents, "%s 未进字形表" % face

    def test_liulangzhuang_traditional_variant(self, registry):
        ents = registry.entities_of(registry.norm("六郎莊"))
        assert "ent_liulangzhuang" in ents, "官书繁体「六郎莊」未收"

    def test_wanquan_line_faces(self, registry):
        assert self._forms_of(registry, "ent_wanquanzhuang")
        assert self._forms_of(registry, "ent_wanquanhe")
        assert self._forms_of(registry, "ent_quanzongmiao")

    def test_haidian_faces(self, registry):
        for face in ("海淀", "海甸", "海店", "北海淀", "南海淀"):
            ents = registry.entities_of(registry.norm(face))
            assert "ent_haidian" in ents, "%s 未进字形表" % face

    def test_sanlihe_face(self, registry):
        assert self._forms_of(registry, "ent_sanlihe")

    def test_holdout_segments_hit(self, registry):
        """直接对 holdout v1 真实段做金标抽取：本批面必须全部命中"""
        import json
        from haidian_kg.evaluation.holdout_eval import extract_gold_mentions
        holdout = os.path.join(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))),
            "haidian_kg", "evaluation", "holdout_v1.jsonl")
        must_hit = {
            "era7_qing.md:L31-L31": {"万泉庄", "泉宗庙"},
            "era7_qing.md:L39-L40": {"牛栏庄", "柳浪庄", "六郎庄", "万泉河"},
            "era4_liao_jin.md:L55-L55": {"三里河"},
        }
        found = {}
        with open(holdout, encoding="utf-8") as fh:
            for line in fh:
                seg = json.loads(line)
                sid = seg.get("segment_id", "")
                if sid not in must_hit:
                    continue
                golds = extract_gold_mentions(seg["text"], sid, registry)
                surfaces = {g.surface for g in golds}
                found[sid] = surfaces
                for face in must_hit[sid]:
                    assert face in surfaces, "%s：面「%s」未命中（got %s）" % (
                        sid, face, sorted(surfaces))


# ==================================================================
# 六郎庄：名号链、传说分层、乾隆不吉说证伪核查
# ==================================================================

class TestLiulangzhuang:
    def test_chain_appellations_all_linked(self, kb):
        for label, kind in (("牛栏庄", AppellationKind.OLD_NAME),
                            ("柳浪庄", AppellationKind.EUPHEMISTIC),
                            ("六郎庄", AppellationKind.OFFICIAL)):
            apps = [a for a in kb.appellations.values()
                    if a.label == label and a.kind == kind]
            assert apps, "名号 %s（%s）缺失" % (label, kind)
            app_id = apps[0].id
            refs = [r for r in kb.references if r.appellation_id == app_id]
            assert refs and refs[0].referent_entity_id == "ent_liulangzhuang"

    def test_ming_state_then_qing_state(self, kb):
        assert kb.state_at("ent_liulangzhuang", 1600) is not None, "明代无牛栏庄状态"
        st = kb.state_at("ent_liulangzhuang", 1761)
        assert st is not None and st.id == "st_llz_qing"
        assert "六郎莊" in st.function or "官场" in st.function

    def test_yangliulang_is_folk_legend_only(self, kb):
        ad = kb.adoptions["prop_llz_yangliulang"]
        assert ad.status == EpistemicStatus.FOLK_LEGEND
        assert ad.confidence < 0.4

    def test_qianlong_taboo_unsubstantiated_not_disproven(self, kb):
        """回源核查：无官书依据 → 无据推论（不做已证伪：无档案≠不存在）"""
        ad = kb.adoptions["prop_llz_qianlong_taboo"]
        assert ad.status == EpistemicStatus.UNSUBSTANTIATED
        prop = kb.propositions["prop_llz_qianlong_taboo"]
        assert "查无官书依据" in prop.statement
        # 对照证据：乾隆朝官书仍作六郎莊
        assert "六郎莊" in kb.facts["tf_dcf_liulangzhuang_guanchang"].verbatim_quote

    def test_village_predates_gardens(self, kb):
        """空间关系自证：庄（明）先于畅春园（康熙朝）与清漪园（1750）"""
        prop = kb.propositions["prop_llz_spatial"]
        assert "早于" in prop.statement and "1750" in prop.statement
        assert kb.state_at("ent_liulangzhuang", 1600) is not None

    def test_modern_state_records_relocation_without_fake_year(self, kb):
        st = kb.states["st_llz_modern"]
        assert st.time_span.open_begin is True
        assert st.time_span.begin is None, "搬迁年份无档案，不得伪造 DatePoint"
        assert "整体搬迁" in (st.geometry or "") + (st.function or "")


# ==================================================================
# 泉宗庙年代：官书互证 vs 长编讹数
# ==================================================================

class TestQuanzongmiaoDates:
    def test_construction_1766_1767(self, kb):
        """乾隆三十一年春经始、三十二年落成（卷79御制诗+卷99谨按两处官书）"""
        assert kb.state_at("ent_quanzongmiao", 1765) is None, "1765 年前不得有泉宗庙状态"
        st = kb.state_at("ent_quanzongmiao", 1766)
        assert st is not None and st.id == "st_qzm_build"
        st = kb.state_at("ent_quanzongmiao", 1767)
        assert st is not None, "三十二年应已落成"

    def test_28_springs_in_state_record(self, kb):
        st = kb.states["st_qzm_standing"]
        assert "二十八处" in st.geometry
        f = kb.facts["tf_qzm_jianan_28"]
        assert "二十有八" in f.verbatim_quote

    def test_longbian_wrong_year_rejected(self, kb):
        """长编「乾隆四十三年敕建/十三处泉名」与官书抵牾，命题层注明不采"""
        prop = kb.propositions["prop_qzm_date"]
        alts = " ".join(prop.alternative_explanations)
        assert "乾隆四十三年" in alts and "不采" in alts
        ad = kb.adoptions["prop_qzm_date"]
        assert ad.status == EpistemicStatus.VERIFIED and ad.confidence >= 0.9

    def test_temple_depends_on_springs_but_entities_separate(self, kb):
        """庙（祀泉）与庄（泉源）分挂两实体，不复合建模"""
        assert "ent_quanzongmiao" in kb.entities and "ent_wanquanzhuang" in kb.entities
        prop = kb.propositions["prop_wqz_wanquan"]
        assert prop.inferred_subject_id == "ent_wanquanzhuang"
        st = kb.states["st_qzm_standing"]
        assert "万泉庄泉群水神" in st.function

    def test_1860_ruin_not_in_kb(self, kb):
        """泉宗庙 1860 受创/今无存仅二手口径，不得入 KB 状态层"""
        assert kb.state_at("ent_quanzongmiao", 1900).id == "st_qzm_standing"
        for st in kb.states_of("ent_quanzongmiao"):
            assert "无存" not in (st.geometry or "") + (st.function or "")


# ==================================================================
# 万泉河：水向 + 河名挂接 honesty
# ==================================================================

class TestWanquanHe:
    def test_flows_north_south_to_beizhu(self, kb):
        st = kb.states["st_wqh_qing"]
        assert "自南而北" in st.geometry
        assert "ent_wanquanzhuang" in st.upstream_entity_ids

    def test_river_name_is_modern_unsubstantiated(self, kb):
        """「万泉河」河名无清代官书直书书证：指称必须显式标无据并写 provenance"""
        ref = kb.references_by_id["rr_wqh"]
        assert ref.evidence_fact_ids == []
        assert ref.status == EpistemicStatus.UNSUBSTANTIATED
        assert "现代" in (ref.provenance or "")


# ==================================================================
# 海淀：词源根、年代链、1952 区名
# ==================================================================

class TestHaidian:
    def test_yuan_attestation_1260(self, kb):
        st = kb.states["st_hd_yuan"]
        assert st.time_span.begin.gregorian.year == 1260
        f = kb.facts["tf_zt_haidian"]
        assert "海店" in f.verbatim_quote

    def test_ming_north_south_dian(self, kb):
        assert kb.state_at("ent_haidian", 1500).id == "st_hd_ming"
        assert "北海淀" in kb.facts["tf_ckh_beihaidian"].verbatim_quote

    def test_district_named_1952(self, kb):
        st = kb.state_at("ent_haidian", 1960)
        assert st is not None and st.id == "st_hd_modern"
        assert "1952年9月1日" in kb.facts["tf_hd_gov_1952"].verbatim_quote
        prop = kb.propositions["prop_hd_root"]
        assert "区名承驻地海淀镇之名" in prop.statement

    def test_no_district_entity_double_modeling(self, kb):
        """海淀区（政区）不另立实体：得名链入命题，避免地名本体双建模"""
        assert "ent_haidianqu" not in kb.entities
        assert not any(a.label == "海淀区" for a in kb.appellations.values())


# ==================================================================
# 三里河：金代存疑 + 前三门消歧义
# ==================================================================

class TestSanlihe:
    def test_ming_attestation_1534(self, kb):
        assert kb.state_at("ent_sanlihe", 1534) is not None
        assert kb.state_at("ent_sanlihe", 1200) is None, "金代无河道状态（存疑不得立状态）"
        assert "嘉靖甲午" in kb.facts["tf_slh_zhongming"].verbatim_quote

    def test_jindai_claim_contested(self, kb):
        ad = kb.adoptions["prop_slh_jindai"]
        assert ad.status == EpistemicStatus.CONTESTED
        prop = kb.propositions["prop_slh_jindai"]
        assert "存疑待考" in prop.statement
        # 分层验证：金代旧迹是钓鱼台（场所），不等于河道金代开挑
        assert "钓鱼台" in prop.statement and "无书证" in prop.statement

    def test_disambiguation_from_qiansanmen(self, kb):
        prop = kb.propositions["prop_slh_disambig"]
        assert "正阳门外三里河" in prop.statement
        assert "同名异地" in prop.statement


# ==================================================================
# 审计层：口径混说必须被拦（泉数 28 vs 讹写 30）
# ==================================================================

class TestAudit:
    def test_correct_spring_count_passes(self, kb):
        r = audit_script(kb, "泉宗庙于乾隆三十二年落成，庙内外淙泉立碣二十八处。")
        assert r[0].verdict == AuditVerdict.PASS, r[0].reason

    def test_wrong_spring_count_blocked(self, kb):
        r = audit_script(kb, "泉宗庙于乾隆三十二年立碣名泉三十处。")
        assert r[0].verdict == AuditVerdict.BLOCK
        assert "30" in r[0].reason or "三十" in r[0].reason

    def test_year_only_claim_not_pass(self, kb):
        """庙成之前（乾隆二十年，1755）不得有落成断言通过；缺证据≠通过"""
        r = audit_script(kb, "泉宗庙于乾隆二十年落成。")
        assert r[0].verdict != AuditVerdict.PASS
        # 长编「乾隆四十三年落成」落在存世态区间内，审计层无法按年份拦——
        # 由命题层（prop_qzm_date 注明不采）+ 泉数对抗样本双重覆盖
        r2 = audit_script(kb, "泉宗庙于乾隆四十三年立碣名泉三十处。")
        assert r2[0].verdict == AuditVerdict.BLOCK


# ==================================================================
# 闸门非恒真 + 实体纪律 + 出图约束
# ==================================================================

class TestGateIsNotConstantTrue:
    def test_gate_catches_removed_fact(self, kb):
        from copy import deepcopy
        kb2 = KnowledgeBase(
            sources=list(kb.sources.values()), divisions=list(kb.divisions.values()),
            facts=list(kb.facts.values()),
            entities=list(kb.entities.values()), states=list(kb.states.values()),
            identities=kb.identities,
            appellations=list(kb.appellations.values()), references=kb.references,
            transformations=list(kb.transformations.values()),
            propositions=list(kb.propositions.values()),
            adoptions=list(kb.adoptions.values()),
            aggregates=list(kb.aggregates.values()),
            people=list(kb.people.values()), resources=kb.resources)
        kb2.facts.pop("tf_qzm_jianan_28")
        rep = QAGate("pingyuan-broken", kb2, adversarial=ADV).run()
        assert not rep.passed, "抽掉关键引文后闸门仍通过 = 闸门恒真"

    def test_entities_carry_no_visual_attributes(self, kb):
        for e in kb.entities.values():
            assert not ({"geometry", "material", "function"} & set(e.model_fields_set))

    def test_storyboard_frames(self, kb):
        sb = export_storyboard(kb, "ent_quanzongmiao")
        assert [f.state_id for f in sb.frames] == ["st_qzm_build", "st_qzm_standing"]

    def test_visual_constraints_1767(self, kb):
        vc = export_visual_constraints(kb, "ent_quanzongmiao", 1767)
        assert any("二十八处" in a.directive for a in vc.required)

    def test_visual_constraints_1500_unknown(self, kb):
        """1500 年泉宗庙未建：必须 UNKNOWN，不得回退到其他时期形制"""
        vc = export_visual_constraints(kb, "ent_quanzongmiao", 1500)
        assert vc.state_id is None
        assert vc.unknown
