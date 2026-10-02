"""
tests/haidian_kg/test_banners_entry.py
圆明园八旗护军营词条入库测试（第三类实体：军事营垒）

史料基准（全部为《钦定八旗通志》《钦定日下旧闻考》《清仁宗实录》一手官书）：
- 雍正二年(1724)设，每处 1250 间，分八处共 10000 间
- 乾隆十二年(1747)增护军百名/旗、添房 300 间/旗 → 1550 楹
  ⚠️ 初建与增建是两个年份，不可混说
- 卷116方位：镶黄旗树村西、正白旗树村东、正黄旗萧家河、正红旗安河桥
- 官房原文「護軍校護軍等官房」——「校」字不可漏
- 二手「北安河桥」系讹传，两部官书均作「安河桥」
- 树村汛 1781 之前已存在（卷73「三汛仍旧」）
- 副将移驻树村有三个时间点（1799/1800/1801），不是一个
"""
import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from haidian_kg.calibration import banners as B
from haidian_kg.calibration.people import PEOPLE
from haidian_kg.calibration.digital_resources import RESOURCES
from haidian_kg.production_exports import (
    KnowledgeBase, export_storyboard, export_visual_constraints, audit_script,
)
from haidian_kg.qa_gate import QAGate
from haidian_kg.ontology.video_contracts import AuditVerdict
from haidian_kg.ontology.spatiotemporal import (
    IdentityRelation, EpistemicStatus,
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


#: 逐句期望的对抗样本：真陈述 + 口径混说
ADV = ("雍正二年设圆明园八旗驻防。镶黄旗营房在雍正二年已有1550间。",
       [("雍正二年设圆明园八旗驻防", "通过"),
        ("镶黄旗营房在雍正二年已有1550间", "非通过")])


# ==================================================================
# 入库闸门
# ==================================================================

class TestBannersEntryGate:
    def test_entry_passes_gate(self, kb):
        rep = QAGate("banners", kb, adversarial=ADV).run()
        assert rep.passed, rep.render()

    def test_uses_unified_bibliography(self, kb):
        """一部书只能一个节点，不得按卷次重复建"""
        titles = [s.title for s in kb.sources.values()]
        assert len(titles) == len(set(titles)), "同一本书被建成多条：%s" % titles

    def test_all_facts_traceable(self, kb):
        div_ids = set(kb.divisions.keys())
        for f in kb.facts.values():
            assert f.division_id in div_ids, f.id


# ==================================================================
# 口径分离：初建 vs 增建
# ==================================================================

class TestScopeSeparation:
    def test_initial_1724_is_1250(self, kb):
        st = kb.state_at("ent_camp_xianghuang", 1724)
        assert "一千二百五十" in st.geometry or "1250" in st.geometry

    def test_after_1747_is_1550(self, kb):
        st = kb.state_at("ent_camp_xianghuang", 1800)
        assert "一千五百五十" in st.geometry or "1550" in st.geometry

    def test_confused_number_blocked(self, kb):
        """【核心】把增建后的 1550 挂到初建年份，必须阻断"""
        r = audit_script(kb, "镶黄旗营房在雍正二年已有1550间。")
        assert r[0].verdict == AuditVerdict.BLOCK
        assert "1550" in r[0].reason

    def test_correct_number_passes(self, kb):
        r = audit_script(kb, "镶黄旗营房在1780年已有1550间。")
        assert r[0].verdict == AuditVerdict.PASS

    def test_camp_count_claim_verified(self, kb):
        ad = kb.adoptions["prop_camp_count"]
        assert ad.status.value == "已确证"
        assert "1250" in kb.propositions["prop_camp_count"].statement


# ==================================================================
# 已修的 v1 错误必须留证
# ==================================================================

class TestV1ErrorsFixed:
    def test_1410_xiao_kept(self, kb):
        """官房原文含「校」字，护军校是另一级军职"""
        p = kb.propositions["prop_huojunxiao"]
        assert "校" in p.statement
        assert kb.adoptions["prop_huojunxiao"].status.value == "已确证"

    def test_anheqiao_not_beianqiao(self, kb):
        """二手「北安河桥」是讹传，官书均作「安河桥」"""
        ad = kb.adoptions["prop_zhenghong_anhe"]
        assert ad.status.value == "已确证"
        assert any(a.label == "北安河桥"
                   for a in kb.appellations.values()), "讹传须留证为独立名称"

    def test_shucun_etymology_unsubstantiated(self, kb):
        """「因树得名」是通行说法但无文献依据"""
        ad = kb.adoptions["prop_shucun_etimology"]
        assert ad.status.value == "无据推论"
        assert ad.confidence < 0.4


# ==================================================================
# 时序：三山五园相关史实不得倒错
# ==================================================================

class TestChronology:
    def test_camp_built_1724(self, kb):
        st = kb.state_at("ent_camp_xianghuang", 1723)
        assert st is None, "雍正二年前不得有营房状态"
        assert kb.state_at("ent_camp_xianghuang", 1724) is not None

    def test_xun_relocated_1801(self, kb):
        """副将移驻树村为嘉庆六年(1801)，不是一个模糊时间点"""
        pt = kb.transformations["pte_xun_1801_relocate"]
        assert pt.time_span.begin.gregorian.year == 1801
        # 1781年前的状态是开放起始（begin=None），state_at 必须取起始最晚的命中
        assert kb.state_at("ent_shucun_xun", 1700).id == "st_xun_pre1781"
        assert kb.state_at("ent_shucun_xun", 1801).id == "st_xun_1801"

    def test_open_begin_span_has_no_fake_datepoint(self, kb):
        """开放起始必须用 None，不得伪造无公历的 DatePoint"""
        st = kb.states["st_xun_pre1781"]
        assert st.time_span.open_begin is True
        assert st.time_span.begin is None, "开放起始不得伪造 DatePoint"

    def test_shucun_settlement_predates_camp(self, kb):
        """树村明代已有庙宇，营房是叠加不是拓荒"""
        assert kb.state_at("ent_shucun", 1600) is not None
        assert kb.state_at("ent_shucun", 1700) is not None

    def test_open_span_does_not_shadow_later_states(self):
        """
        【回归·真 bug】开放起始区间曾有两个致命后果：
          1. states_of 排序直接抛 AttributeError
          2. 即使不抛，按列表顺序取首个会让「1781年前已存」
             永远压过 1801-1911 的具体状态，导致 1801 年反而取到旧状态
        """
        from haidian_kg.calibration import banners as BB
        from haidian_kg.production_exports import KnowledgeBase as KB
        k = KB(states=BB.STATES, entities=BB.ENTITIES)
        # 排序不得抛错
        sts = k.states_of("ent_shucun_xun")
        assert [s.id for s in sts] == ["st_xun_pre1781", "st_xun_1801"]
        # 1801 必须取到具体状态而非开放状态
        assert k.state_at("ent_shucun_xun", 1801).id == "st_xun_1801"
        # 开放状态仍能正确命中更早年份
        assert k.state_at("ent_shucun_xun", 1700).id == "st_xun_pre1781"


class TestBannersGateIsNotConstantTrue:
    """八旗词条的闸门必须能抓住本词条特有的错误"""

    def test_scope_mixing_blocked(self, kb):
        """口径混说：把增建后的 1550 挂到初建年份"""
        rep = QAGate("banners", kb, adversarial=ADV).run()
        assert rep.passed, rep.render()
        r = audit_script(kb, "镶黄旗营房在雍正二年已有1550间。")
        assert r[0].verdict == AuditVerdict.BLOCK

    def test_chronology_inversion_blocked(self, kb):
        """时序倒错：把嘉庆六年的移驻挂到更早年份"""
        r = audit_script(kb, "副将在康熙年间就移驻树村。")
        assert r[0].verdict != AuditVerdict.PASS, \
            "康熙年间无副将移驻记录，不得判通过"

    def test_camp_before_1724_blocked(self, kb):
        """雍正二年前不得有营房状态"""
        assert kb.state_at("ent_camp_xianghuang", 1700) is None
        r = audit_script(kb, "镶黄旗营房在1700年已有1250间。")
        assert r[0].verdict != AuditVerdict.PASS

    def test_gate_catches_removed_fact(self, kb):
        """抽掉一条引文后闸门必须失败"""
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
        kb2.facts.pop("tf_bqtz116_yuanzheng")
        rep = QAGate("banners-broken", kb2, adversarial=ADV).run()
        assert not rep.passed, "抽掉引文后闸门仍通过 = 闸门恒真"


# ==================================================================
# 空间格局
# ==================================================================

class TestSpatialLayout:
    def test_eight_banners_aggregate(self, kb):
        agg = kb.aggregates["agg_yuanming_eight_banners"]
        assert len(agg.member_entity_ids) == 5, "本词条仅录方位明确者"
        assert agg.time_span.begin.gregorian.year == 1724

    def test_all_camps_are_fortified(self, kb):
        for eid, e in kb.entities.items():
            if "camp" in eid:
                assert e.kind.value == "营垒", eid

    def test_entities_carry_no_visual_attributes(self, kb):
        """实体只承载身份，形制必须下沉到状态"""
        for e in kb.entities.values():
            assert not ({"geometry", "material", "function"} & set(e.model_fields_set))


# ==================================================================
# 出图约束
# ==================================================================

class TestVisualConstraints:
    def test_1730_wooden(self, kb):
        vc = export_visual_constraints(kb, "ent_camp_xianghuang", 1730)
        assert any("一千二百五十" in a.directive for a in vc.required)

    def test_1800_after_expansion(self, kb):
        vc = export_visual_constraints(kb, "ent_camp_xianghuang", 1800)
        assert any("一千五百五十" in a.directive for a in vc.required)

    def test_storyboard_records_expansion(self, kb):
        sb = export_storyboard(kb, "ent_camp_xianghuang")
        assert len(sb.frames) == 2
        assert [f.state_id for f in sb.frames] == ["st_camp_1724", "st_camp_1747"]


class TestCrossModuleIdentity:
    def test_yuanmingyuan_parent_same_as_yuanmingyuan(self, kb):
        """holdout run2 collision 硬闸发现：圆明园在 banners（驻防空间母体）
        与 yuanmingyuan 模块（园林本体）双建模且无 identity 断言——
        跨模块同指必须显式断言，否则挖掘假说跨双实体计入 collision。"""
        ids = [i for i in kb.identities
               if set(i.subject_entity_ids) == {"ent_yuanmingyuan_parent",
                                                "ent_yuanmingyuan"}]
        assert len(ids) == 1, "缺跨模块同指断言 dia_ymy_parent_same"
        assert ids[0].relation == IdentityRelation.SAME_CONTINUANT
        assert ids[0].status == EpistemicStatus.VERIFIED
        # 关系断言不可挪用为同指证据：证据必须是驻防营建/方位事实
        assert set(ids[0].evidence_fact_ids) == {
            "tf_bqtz116_yuanzheng", "tf_bqtz116_fangwei"}
