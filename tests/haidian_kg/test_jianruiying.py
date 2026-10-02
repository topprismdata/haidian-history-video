"""
tests/haidian_kg/test_jianruiying.py
健锐营（香山健锐营）词条入库测试（追加于 banners 模块，军事营垒类）

史料基准（全部回源核对，2026-10-02）：
- 立营乾隆十四年(1749)：御制实胜寺碑记「合成功之旅立為健銳雲梯營」（纪年
  「乾隆十有四年嵗在己巳夏五月」）＋《清史稿》卷130「乾隆十四年，設雲梯兵一營」
  ——双源同指一年；乾隆十三年是设碉演云梯之年，不可混说
- 营制归属：清史稿卷130列于京营兵衛之制，驻防另立四类且不含健锐营——
  特设营制非八旗驻防，与圆明园八旗护军营并立非隶属
- 碉楼：官书按语总数「共計六十有七」，逐旗相加六十六，差一两说并存
- 兵额：唯清史稿「光、宣之季实存名数」为档案口径，不得冒充初设兵额
- 团城演武厅：1749年建；2006年第六批国保（国发〔2006〕19号，名录名
  「健锐营演武厅」Ⅲ-9）；现由北京大觉寺与团城管理处管理并开放
- holdout run3 缺口面「健锐营」必须能从实体字形表命中
"""
import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from haidian_kg.calibration import banners as B
from haidian_kg.calibration.people import PEOPLE
from haidian_kg.calibration.digital_resources import RESOURCES
from haidian_kg.production_exports import KnowledgeBase, audit_script
from haidian_kg.qa_gate import QAGate
from haidian_kg.ontology.video_contracts import AuditVerdict
from haidian_kg.ontology.spatiotemporal import (
    IdentityRelation, EpistemicStatus,
)
from haidian_kg.evaluation.holdout_eval import (
    build_name_registry, extract_gold_mentions, norm_eval,
)


@pytest.fixture(scope="module")
def kb():
    return KnowledgeBase(
        sources=B.SOURCES, divisions=B.DIVISIONS, facts=B.FACTS,
        entities=B.ENTITIES, states=B.STATES, identities=B.IDENTITIES,
        appellations=B.APPELLATIONS, references=B.REFERENCES,
        transformations=B.TRANSFORMATIONS, propositions=B.PROPOSITIONS,
        adoptions=B.ADOPTIONS, aggregates=B.AGGREGATES,
        people=PEOPLE, resources=RESOURCES)


#: 逐句对抗样本：立营之年（真）＋把碑文二千人讹作三千（口径混说）
ADV_JRY = ("乾隆十四年立健锐云梯营。云梯兵在乾隆十四年已有三千人。",
           [("乾隆十四年立健锐云梯营", "通过"),
            ("云梯兵在乾隆十四年已有三千人", "非通过")])


# ==================================================================
# 入库闸门
# ==================================================================

class TestJianruiEntryGate:
    def test_entry_passes_gate(self, kb):
        rep = QAGate("banners-jianrui", kb, adversarial=ADV_JRY).run()
        assert rep.passed, rep.render()

    def test_all_jry_facts_traceable(self, kb):
        div_ids = set(kb.divisions.keys())
        for fid, f in kb.facts.items():
            if fid.startswith("tf_qsg130") or fid.startswith("tf_rxjwkc10") \
                    or fid.startswith("tf_wjbz"):
                assert f.division_id in div_ids, fid

    def test_no_duplicate_source_titles(self, kb):
        titles = [s.title for s in kb.sources.values()]
        assert len(titles) == len(set(titles)), "同一本书被建成多条：%s" % titles

    def test_entities_carry_no_visual_attributes(self, kb):
        for e in kb.entities.values():
            if e.id.startswith("ent_jry_"):
                assert not ({"geometry", "material", "function"}
                            & set(e.model_fields_set)), e.id


# ==================================================================
# 立营年代：双源同指 1749，与选锋之年 1748 分离
# ==================================================================

class TestJianruiFounding:
    def test_no_camp_state_before_1749(self, kb):
        assert kb.state_at("ent_jry_ying", 1747) is None, \
            "乾隆十二年前不得有健锐营状态"
        assert kb.state_at("ent_jry_ying", 1749) is not None

    def test_dual_source_1749(self, kb):
        """御制碑纪年＋清史稿纪年双源，缺一不可"""
        assert "乾隆十有四年" in kb.facts["tf_rxjwkc102_bei_nian"].verbatim_quote
        assert "乾隆十四年，設雲梯兵一營" in \
            kb.facts["tf_qsg130_yunti"].verbatim_quote
        p = kb.propositions["prop_jry_found_year"]
        assert "tf_rxjwkc102_bei_nian" in p.derived_from_fact_ids
        assert "tf_qsg130_yunti" in p.derived_from_fact_ids
        assert kb.adoptions["prop_jry_found_year"].status == EpistemicStatus.VERIFIED

    def test_yunti_training_year_separate(self, kb):
        """乾隆十三年属于云梯兵训练态，不属于健锐营"""
        assert kb.state_at("ent_jry_yunti", 1748) is not None
        assert kb.state_at("ent_jry_yunti", 1750) is None

    def test_successor_identity(self, kb):
        ids = [i for i in kb.identities
               if set(i.subject_entity_ids) == {"ent_jry_yunti", "ent_jry_ying"}]
        assert len(ids) == 1
        assert ids[0].relation == IdentityRelation.SUCCESSOR
        assert ids[0].status == EpistemicStatus.VERIFIED
        assert "ent_jry_yunti" in kb.entities["ent_jry_ying"].supersedes_ids


# ==================================================================
# 营制归属：特设营制非八旗驻防，与圆明园八旗护军营并立
# ==================================================================

class TestJianruiMilitaryType:
    def test_admin_status_declares_special_system(self, kb):
        st = kb.state_at("ent_jry_ying", 1749)
        assert "兵衛之制" in st.admin_status
        assert "非八旗驻防" in st.admin_status

    def test_relation_state_cites_structure_evidence(self, kb):
        st = kb.state_at("ent_jry_ying", 1749)
        assert "tf_qsg130_zhufang" in st.evidence_fact_ids
        assert "tf_qsg130_ymy" in st.evidence_fact_ids
        ad = kb.adoptions["prop_jry_military_type"]
        assert ad.status == EpistemicStatus.VERIFIED

    def test_modern_grouping_marked_alternative(self, kb):
        """「京旗外三营」是现代通称，只能挂在另说里"""
        p = kb.propositions["prop_jry_military_type"]
        assert any("京旗外三营" in alt for alt in p.alternative_explanations)
        assert "京旗外三营" not in p.statement


# ==================================================================
# 碉楼：官书总数六十七，逐旗相加六十六，差一留证
# ==================================================================

class TestJianruiDiaolou:
    def test_official_total_recorded(self, kb):
        st = kb.state_at("ent_jry_diaolou", 1749)
        assert "六十有七" in st.geometry

    def test_off_by_one_documented_not_smoothed(self, kb):
        p = kb.propositions["prop_jry_diao67"]
        assert "差一" in p.statement
        assert "不取区间值" in p.statement or "两说并存" in p.statement
        assert kb.adoptions["prop_jry_diao67"].status == EpistemicStatus.VERIFIED

    def test_diaolou_chronology(self, kb):
        assert kb.state_at("ent_jry_diaolou", 1748) is None
        assert kb.state_at("ent_jry_diaolou", 1749) is not None

    def test_modern_surviving_count_not_fabricated(self, kb):
        """现存座数无官方测绘档，不得给数字"""
        st = kb.state_at("ent_jry_diaolou", 2020)
        assert st.id == "st_jry_diaolou_now"
        assert st.time_span.open_end is True
        for ch in "0123456789":
            assert ch not in st.geometry, "现状态不得出现未核数字"


# ==================================================================
# 兵额：唯「光宣之季」档案口径，不得冒充初设
# ==================================================================

class TestJianruiTroopNumbers:
    def test_guangxuan_era_numbers_only_in_late_state(self, kb):
        st = kb.state_at("ent_jry_ying", 1900)
        assert st.id == "st_jry_gx"
        assert "三千八百七十八" in st.geometry
        assert "光" in st.function or "光、宣之季" in st.function

    def test_early_state_does_not_claim_late_numbers(self, kb):
        st = kb.state_at("ent_jry_ying", 1750)
        assert "三千八百七十八" not in (st.geometry or "") \
            + (st.material or "") + (st.function or "") + (st.admin_status or "")

    def test_confused_era_blocked(self, kb):
        """把光宣之季兵额挂到乾隆朝，必须阻断"""
        r = audit_script(kb, "健锐营在乾隆二十年已有官兵三千八百七十八人。")
        assert r[0].verdict == AuditVerdict.BLOCK

    def test_correct_era_passes(self, kb):
        r = audit_script(kb, "健锐营在1900年有官兵三千八百七十八人。")
        assert r[0].verdict == AuditVerdict.PASS

    def test_no_daqing_huidian_claim(self, kb):
        """乾隆朝会典未核得引文——不得预支会典兵额结论"""
        for f in kb.facts.values():
            if f.id.startswith("tf_qsg130") or f.id.startswith("tf_rxjwkc10") \
                    or f.id.startswith("tf_wjbz"):
                assert "大清会典" not in f.verbatim_quote, f.id


# ==================================================================
# 团城演武厅：器物层＋现状核查＋数字口径分离
# ==================================================================

class TestJianruiTuancheng:
    def test_entity_and_appellations(self, kb):
        ent = kb.entities["ent_jry_tuancheng"]
        assert ent.canonical_label == "团城演武厅"
        apps = {a.label: a for a in kb.appellations_of("ent_jry_tuancheng")}
        assert "演武厅" in apps and "团城演武厅" in apps and "看城" in apps
        assert "演武㕔" in apps["演武厅"].script_variants

    def test_gunqiang_yanwuchang_not_an_entity(self, kb):
        """「枪炮演武场」是描述性短语，不设实体"""
        assert "枪炮演武场" not in kb.entities
        st = kb.state_at("ent_jry_tuancheng", 1749)
        assert "枪炮演武场" in st.function

    def test_modern_meters_only_in_modern_state(self, kb):
        old = kb.state_at("ent_jry_tuancheng", 1749)
        now = kb.state_at("ent_jry_tuancheng", 2020)
        assert "50.2" not in (old.geometry or "") and "3.42" not in (old.geometry or "")
        assert "50.2" in now.geometry and "3.42" in now.geometry

    def test_heritage_status_single_check(self, kb):
        """现状必须单独核查：市保→国保→现行管理机构"""
        now = kb.state_at("ent_jry_tuancheng", 2020)
        assert "1979" in now.admin_status and "2006" in now.admin_status
        assert "健锐营演武厅" in now.admin_status
        assert "Ⅲ－9" in now.admin_status or "Ⅲ-9" in now.admin_status
        assert "大觉寺与团城管理处" in now.admin_status
        assert now.time_span.open_end is True
        assert kb.state_at("ent_jry_tuancheng", 1979) is not None
        # 建筑自1749年起持续存在：1950年命中的是历史形制态而非现状态
        assert kb.state_at("ent_jry_tuancheng", 1950).id == "st_jry_tuancheng_1749"

    def test_national_heritage_dual_voice(self, kb):
        p = kb.propositions["prop_jry_tuancheng_status"]
        assert "2006年5月25日" in p.statement
        assert "2006年6月" in p.statement, "管理处口径差必须留证"


# ==================================================================
# holdout 缺口面：字形表命中（run3 kb-coverage-gap 的验收面）
# ==================================================================

HOLDOUT_SEGMENT = (
    "- **健锐营（乾隆十四年，1749）**：\n"
    "  - 乾隆平定金川特设云梯特种部队，按八旗翼长驻香山静宜园下，"
    "营建石碉楼数百座，名健锐营。"
)


class TestHoldoutCoverage:
    def test_registry_hits_jianrui(self, kb):
        reg = build_name_registry()
        nf = norm_eval("健锐营")
        assert nf in reg.form_map, "字形表缺「健锐营」——缺口面无法转正"
        assert "ent_jry_ying" in reg.form_map[nf]

    def test_segment_extracts_gold_mentions(self, kb):
        reg = build_name_registry()
        golds = extract_gold_mentions(HOLDOUT_SEGMENT, "era7_qing.md:L25-L26", reg)
        hit_ids = {eid for g in golds for eid in g.entity_ids}
        assert "ent_jry_ying" in hit_ids
        # 「名健锐营」句尾与标题两处健锐营都应成为金标
        jry_surfaces = [g.surface for g in golds
                        if "ent_jry_ying" in g.entity_ids]
        assert len(jry_surfaces) >= 2

    def test_diaolou_surface_covered(self, kb):
        reg = build_name_registry()
        golds = extract_gold_mentions(HOLDOUT_SEGMENT, "era7_qing.md:L25-L26", reg)
        hit_ids = {eid for g in golds for eid in g.entity_ids}
        assert "ent_jry_diaolou" in hit_ids, "「石碉楼」面未被字形表覆盖"

    def test_alias_forms_registered(self, kb):
        reg = build_name_registry()
        for form in ("健锐云梯营", "团城演武厅", "演武厅"):
            assert norm_eval(form) in reg.form_map, form


# ==================================================================
# 闸门非恒真（负控制）
# ==================================================================

class TestJianruiGateIsNotConstantTrue:
    def test_chronology_inversion_blocked(self, kb):
        """健锐营不可能设于雍正二年"""
        r = audit_script(kb, "健锐营在雍正二年已经设立。")
        assert r and r[0].verdict != AuditVerdict.PASS

    def test_pre_1748_claim_untestable(self, kb):
        r = audit_script(kb, "健锐营在1740年已有营房。")
        assert r and r[0].verdict != AuditVerdict.PASS, "缺证据≠通过"

    def test_wrong_training_number_blocked(self, kb):
        r = audit_script(kb, "云梯兵在乾隆十四年已有三千人。")
        assert r[0].verdict == AuditVerdict.BLOCK

    def test_gate_catches_removed_foundation_fact(self, kb):
        """抽掉立营碑文引文后闸门必须失败"""
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
        kb2.facts.pop("tf_rxjwkc102_bei_li")
        rep = QAGate("banners-jianrui-broken", kb2, adversarial=ADV_JRY).run()
        assert not rep.passed, "抽掉引文后闸门仍通过 = 闸门恒真"

    def test_unsubstantiated_alias_has_provenance(self, kb):
        ref = kb.references_by_id["rr_jry_xiangshan"]
        assert ref.status == EpistemicStatus.UNSUBSTANTIATED
        assert ref.provenance and "清档原文未核得" in ref.provenance
