"""
tests/haidian_kg/test_production_exports.py
视频生产三接口端到端回归测试（高梁河校准实例）

验收标准：第3轮"长河案例"必须撑得住，且三个接口的行为符合 P0-9 契约。
"""
import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from haidian_kg.calibration import gaoliang as G
from haidian_kg.production_exports import (
    KnowledgeBase, export_storyboard, export_visual_constraints, audit_script,
)
from haidian_kg.ontology.video_contracts import AuditVerdict


@pytest.fixture(scope="module")
def kb():
    return KnowledgeBase(
        sources=G.SOURCES, divisions=G.DIVISIONS, facts=G.FACTS,
        entities=G.ENTITIES, states=G.STATES, identities=G.IDENTITIES,
        appellations=G.APPELLATIONS, references=G.REFERENCES,
        transformations=G.TRANSFORMATIONS, propositions=G.PROPOSITIONS,
        adoptions=G.ADOPTIONS, aggregates=G.AGGREGATES,
    )


# ==================================================================
# 校准数据自身的完整性
# ==================================================================

class TestCalibrationIntegrity:
    def test_facts_never_cross_volumes(self, kb):
        """《水经注》卷十三与卷十四是两个独立篇卷，任何引文不得跨卷"""
        vol13 = {d.id for d in kb.divisions.values() if d.volume_number == "卷十三"}
        vol14 = {d.id for d in kb.divisions.values() if d.volume_number == "卷十四"}
        for f in kb.facts.values():
            assert not (f.division_id in vol13 and f.division_id in vol14)

    def test_no_four_thousand_qing(self, kb):
        """【已剔除的硬伤】刘靖工程灌田数字不得出现"四千顷\""""
        for f in kb.facts.values():
            assert "四千顷" not in f.verbatim_quote
        assert any("岁二千顷" in f.verbatim_quote for f in kb.facts.values())

    def test_liujing_250_precedes_songshui_527(self, kb):
        """【第3轮§1.1】曹魏嘉平二年(250)必须早于北魏《水经注》成书(527)"""
        f_liu = kb.facts["tf_sjz_liujing"]
        f_sj = kb.facts["tf_sjz_natural"]
        assert f_liu.source_year.gregorian.year == 527
        assert "嘉平二年" in f_liu.verbatim_quote
        # 250 < 527 必须在文案层显式成立
        st = kb.states["st_liujing_250"]
        assert st.time_span.begin.gregorian.year == 250

    def test_zhuozhou_not_bridge(self, kb):
        """《辽史》明载涿州驴车，不得出现"高梁桥下乘驴车"表述"""
        f = kb.facts["tf_liaoshi_zhuozhou"]
        assert "涿州" in f.verbatim_quote
        for f in kb.facts.values():
            assert "桥下乘驴车" not in f.verbatim_quote

    def test_xichengzha_is_facility_not_rivername(self, kb):
        """【第3轮§1.2】西城闸是水工设施名，不得进入河名演化链"""
        assert kb.entities["ent_xichengzha"].kind.value == "水工建筑物"
        assert kb.entities["ent_gaoliang_watercourse"].kind.value == "天然水道"

    def test_etymology_kept_contested(self, kb):
        """词源不得断言为定论（排除作物说≠证明津梁说）"""
        ad = kb.adoptions["prop_etymology_uncertain"]
        assert ad.status.value == "学术争议"


# ==================================================================
# 接口 1：分镜故事板
# ==================================================================

class TestStoryboard:
    def test_three_states_in_order(self, kb):
        sb = export_storyboard(kb, "ent_xichengzha")
        assert len(sb.frames) == 3
        assert sb.frames[0].state_id == "st_wood_1292"
        assert sb.frames[-1].state_id == "st_stone_1327"

    def test_material_jump_is_warned(self, kb):
        """木→石的状态跳变必须产生警告，不得静默缝合"""
        sb = export_storyboard(kb, "ent_xichengzha")
        assert sb.discontinuity_warnings, "材质跳变必须告警"
        assert any("木构" in w and "砖石" in w for w in sb.discontinuity_warnings)

    def test_frames_carry_evidence(self, kb):
        sb = export_storyboard(kb, "ent_xichengzha")
        for f in sb.frames:
            assert f.narration_facts, "每个分镜必须挂口播依据"


# ==================================================================
# 接口 2：出图视觉约束四态
# ==================================================================

class TestVisualConstraints:
    def test_1295_requires_wood(self, kb):
        vc = export_visual_constraints(kb, "ent_xichengzha", 1295)
        assert any("木构" in a.directive for a in vc.required)
        assert not vc.unknown

    def test_1312_is_unknown_not_stone(self, kb):
        """【第3轮§15 杀手测试】1312 不得输出砖石"""
        vc = export_visual_constraints(kb, "ent_xichengzha", 1312)
        assert not any("砖石" in a.directive for a in vc.required)
        assert vc.unknown, "过渡期必须显式声明无证据"
        assert not vc.forbidden, "过渡期不得输出 FORBIDDEN（把未知当否定）"
        assert vc.coexisting_forms

    def test_1330_requires_stone(self, kb):
        vc = export_visual_constraints(kb, "ent_xichengzha", 1330)
        assert any("砖石" in a.directive for a in vc.required)

    def test_year_without_state_is_all_unknown(self, kb):
        """【关键】无证据年份不得回退到最近状态"""
        vc = export_visual_constraints(kb, "ent_xichengzha", 1600)
        assert vc.state_id is None
        assert vc.required == [] and vc.forbidden == []
        assert vc.unknown and "禁止按其他时期形制推定" in vc.unknown[0]

    def test_prompt_block_has_four_states(self, kb):
        vc = export_visual_constraints(kb, "ent_xichengzha", 1312)
        block = vc.as_prompt_block()
        assert "必须" in block and "无证据" in block and "并存" in block


# ==================================================================
# 接口 3：脚本命题审计
# ==================================================================

class TestScriptAudit:
    def test_reign_year_parsed(self, kb):
        """中文年号必须能解析为公历年，否则审计全失效"""
        r = audit_script(kb, "元至元二十九年，在和义门外设西城闸。")
        assert r[0].claim.year == 1292
        assert r[0].claim.resolved_entity_id == "ent_xichengzha"

    def test_anaphora_inherits_entity(self, kb):
        """「这座闸」必须继承上一句实体，不得判为无法消歧"""
        r = audit_script(kb, "元至元二十九年设西城闸。这座闸在1295年仍是木构。")
        assert r[1].claim.resolved_entity_id == "ent_xichengzha"
        assert r[1].verdict == AuditVerdict.PASS

    def test_false_stone_claim_untestable(self, kb):
        """【防假通过】1312年"已经是砖石"不得判通过"""
        r = audit_script(kb, "元至元二十九年设西城闸。这座闸在1312年已经是砖石结构。")
        assert r[1].verdict == AuditVerdict.UNTESTABLE
        assert r[1].verdict != AuditVerdict.PASS
        assert "1311" in r[1].reason

    def test_contested_reference_untestable(self, kb):
        """战场落点学界争议时，低置信不得判定对错"""
        r = audit_script(kb, "宋太宗在太平兴国四年高梁河之战中，乘驴车从涿州逃回。")
        assert r[0].claim.year == 979
        assert r[0].verdict == AuditVerdict.UNTESTABLE
        assert r[0].claim.disambiguation_confidence < 0.6

    def test_no_year_no_pass(self, kb):
        """【E11 假通过同型】无年份无实体时不得判通过"""
        r = audit_script(kb, "元代以前闸坝全部使用木构，这是定论。")
        for x in r:
            assert x.verdict != AuditVerdict.PASS

    def test_untestable_dominates_wrong_data(self, kb):
        """关键性质：数据不全时宁可 UNTESTABLE，绝不假通过"""
        script = "这座闸在1751年一定是石砌的。乾隆年间河道改称长河。"
        rs = audit_script(kb, script)
        assert all(x.verdict == AuditVerdict.UNTESTABLE for x in rs if x.claim.year)
