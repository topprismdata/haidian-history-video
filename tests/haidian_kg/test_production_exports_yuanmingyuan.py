"""
tests/haidian_kg/test_production_exports_yuanmingyuan.py
圆明三园校准实例回归测试（验证 P0-7 聚合与毁损算子）

第3轮原话：
  「圆明三园需要 PlaceAggregate，不是 Rename」
  「1860 更不能用 EXTINCTION_FOSSIL」
  「名称变化≠空间并入≠园林新建≠集合形成」
"""
import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from haidian_kg.calibration import yuanmingyuan as Y
from haidian_kg.production_exports import (
    KnowledgeBase, export_storyboard, export_visual_constraints, audit_script,
)
from haidian_kg.ontology.video_contracts import AuditVerdict


@pytest.fixture(scope="module")
def kb():
    return KnowledgeBase(
        sources=Y.SOURCES, divisions=Y.DIVISIONS, facts=Y.FACTS,
        entities=Y.ENTITIES, states=Y.STATES, identities=Y.IDENTITIES,
        appellations=Y.APPELLATIONS, references=Y.REFERENCES,
        transformations=Y.TRANSFORMATIONS, propositions=Y.PROPOSITIONS,
        adoptions=Y.ADOPTIONS, aggregates=Y.AGGREGATES,
    )


# ==================================================================
# 校准数据纪律
# ==================================================================

class TestYMYIntegrity:
    def test_three_gardens_are_separate_entities(self, kb):
        """三园各自有独立身份，不得合并"""
        assert len(kb.entities) == 3
        assert {e.id for e in kb.entities.values()} == {
            "ent_yuanmingyuan", "ent_changchunyuan", "ent_qichunyuan"}

    def test_aggregate_has_start_point(self, kb):
        """【第3轮】三园格局是1770前后形成的历史事实，不是永恒结构"""
        agg = kb.aggregates["agg_yuanming_three"]
        assert agg.time_span.begin.gregorian.year == 1770
        assert len(agg.member_entity_ids) == 3

    def test_no_extinction_transformation(self, kb):
        """【第3轮§7】焚毁是 DAMAGED / PARTIALLY_DESTROYED，绝非 extinction"""
        kinds = {t.transformation.value for t in kb.transformations.values()}
        assert "消亡" not in kinds and "废弃" not in kinds
        assert "部分毁损" in kinds and "毁损" in kinds

    def test_1928_only_takeover_not_park_name(self, kb):
        """『民国遗址公园』从材料推不出，须标 UNSUBSTANTIATED"""
        ad = kb.adoptions["prop_minguo_park_unproven"]
        assert ad.status.value == "无据推论"

    def test_uncertain_identity_records_both_sides(self, kb):
        """长春园是否由圆明园分裂 —— UNCERTAIN 须列出争议双方"""
        dia = next(d for d in kb.identities if d.id == "dia_ymy_ccy_relation")
        assert dia.relation.value == "存疑"
        assert len(dia.alternative_relations) >= 2


# ==================================================================
# 聚合与毁损
# ==================================================================

class TestAggregationAndDamage:
    def test_members_never_merged(self, kb):
        """聚合不改变成员身份：各成员仍有各自状态"""
        for eid in kb.aggregates["agg_yuanming_three"].member_entity_ids:
            assert kb.states_of(eid), "聚合成员必须保留自身状态"

    def test_burn_year_boundary(self, kb):
        """1860年焚毁当年即进入残存态，不得仍返回焚毁前状态"""
        assert kb.state_at("ent_yuanmingyuan", 1859).id == "st_ymy_1770"
        assert kb.state_at("ent_yuanmingyuan", 1860).id == "st_ymy_1860_ruins"

    def test_place_survives_1860(self, kb):
        """【核心】焚毁后地点持续存在至1988年遗址公园"""
        assert kb.state_at("ent_yuanmingyuan", 1880) is not None
        assert kb.state_at("ent_yuanmingyuan", 1990) is not None

    def test_four_state_chain(self, kb):
        sb = export_storyboard(kb, "ent_yuanmingyuan")
        assert len(sb.frames) == 4
        assert [f.state_id for f in sb.frames] == [
            "st_ymy_1770", "st_ymy_1860_ruins",
            "st_ymy_1900_ruins", "st_ymy_1988_park"]


# ==================================================================
# 身份注记按时间过滤（否则会误导导演）
# ==================================================================

class TestIdentityNoteTemporalFilter:
    def test_1750_identity_disputed(self, kb):
        vc = export_visual_constraints(kb, "ent_yuanmingyuan", 1750)
        assert any("身份" in u for u in vc.unknown)

    def test_1990_identity_settled(self, kb):
        """【关键修复】1860年后已确证同一持续体，1990年不应再报身份存疑"""
        vc = export_visual_constraints(kb, "ent_yuanmingyuan", 1990)
        assert not any("身份" in u for u in vc.unknown)
        assert "已确证" in (vc.identity_continuity_note or "")


# ==================================================================
# 出图约束
# ==================================================================

class TestYMYVisualConstraints:
    def test_1750_wooden(self, kb):
        vc = export_visual_constraints(kb, "ent_yuanmingyuan", 1750)
        assert any("木构" in a.directive for a in vc.required)

    def test_1860_ruins(self, kb):
        vc = export_visual_constraints(kb, "ent_yuanmingyuan", 1860)
        assert any("残存砖木" in a.directive for a in vc.required)
        assert not any("木构殿宇" in a.directive for a in vc.required)

    def test_1990_park(self, kb):
        vc = export_visual_constraints(kb, "ent_yuanmingyuan", 1990)
        assert any("遗址公园" in a.directive for a in vc.required)


# ==================================================================
# 脚本审计：消亡断言必须阻断
# ==================================================================

class TestExtinctionClaimBlocked:
    def test_extinction_claim_blocked(self, kb):
        """【核心防假通过】"焚毁后不复存在"必须 BLOCK"""
        r = audit_script(kb, "咸丰十年英法联军焚毁圆明园，此后圆明园成为废墟不復存在。")
        assert r[0].verdict == AuditVerdict.BLOCK
        assert r[0].verdict != AuditVerdict.PASS
        assert "毁损≠消亡" in r[0].reason

    def test_traditional_chinese_markers(self, kb):
        """繁体「不復存在」同样须被识别"""
        r = audit_script(kb, "圆明园在1860年后不復存在。")
        assert r[0].verdict == AuditVerdict.BLOCK

    def test_genuine_post_burn_facts_pass(self, kb):
        """真实的后续事实不得被误伤"""
        r = audit_script(kb, "1988年圆明园遗址公园正式开放。")
        assert r[0].verdict == AuditVerdict.PASS

    def test_building_year_parsed_from_reign(self, kb):
        r = audit_script(kb, "圆明园始建于康熙四十六年，是皇四子胤禛的赐园。")
        assert r[0].claim.year == 1707
        assert r[0].verdict == AuditVerdict.PASS
