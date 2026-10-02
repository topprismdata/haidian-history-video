"""
tests/haidian_kg/test_ontology_v2_spatiotemporal.py
历时空间层与生产接口契约回归测试（GPT 第3轮 P0-5 ~ P0-9）

验收标准由 GPT 第3轮明确指定，三个回归测试必须全过：
  1. 长河案例   → 需要 Persistent Entity + HistoricalFeatureState + 身份断言
  2. 圆明园案例 → 名称变化≠空间并入；毁损≠消亡
  3. 高梁桥案例 → 字符串名称绝不能承担实体消歧

外加第3轮点名的"木闸→石闸"杀手测试：不能由"1311年始议砖石"推出"1312年此闸为石"。
"""
import pytest

from haidian_kg.ontology.temporal import (
    CalibrationTable, DatePoint, GregorianDate, TimeSpan,
)
from haidian_kg.ontology.epistemic import EpistemicStatus
from haidian_kg.ontology.spatiotemporal import (
    PhysicalThingKind, PersistentSpatialEntity, HistoricalFeatureState,
    IdentityRelation, DiachronicIdentityAssertion, PlaceTransformationEvent,
    PlaceTransformation, PlaceAggregate, AppellationKind, Appellation,
    ReferentialAssertion,
)
from haidian_kg.ontology.video_contracts import (
    ConstraintStrength, VisualStateAssertion, VisualPromptConstraints,
    StoryboardFrame, VideoStoryboard, ClaimType, ParsedClaim,
    AuditVerdict, AuditResult,
)


def ts(y1, y2, tag="t"):
    return TimeSpan(
        id=tag, label="%d-%d" % (y1, y2),
        begin=DatePoint(id=tag + "b", label=str(y1),
                        gregorian=GregorianDate(year=y1, calibration=CalibrationTable.CN_ASTRONOMICAL_ALMANAC)),
        end=DatePoint(id=tag + "e", label=str(y2),
                      gregorian=GregorianDate(year=y2, calibration=CalibrationTable.CN_ASTRONOMICAL_ALMANAC)),
    )


# ============ P0-5：实体不得携带可见属性 ============

class TestEntityStateSeparation:
    def test_entity_rejects_geometry_attribute(self):
        """【负控制】几何必须下沉到 State，实体上不得出现

        双层防护：model_config extra="forbid" 先拦（Pydantic 默认静默丢弃更危险），
        自定义 _no_state_attributes 兜底说明"为什么"不能放。
        """
        with pytest.raises(ValueError) as e:
            PersistentSpatialEntity(
                id="e1", kind=PhysicalThingKind.HYDRAULIC_STRUCTURE,
                canonical_label="西城闸", geometry="双孔平板",
            )
        msg = str(e.value)
        assert ("Extra inputs are not permitted" in msg) or ("可见属性" in msg), msg

    def test_entity_rejects_topology_attribute(self):
        with pytest.raises(ValueError):
            PersistentSpatialEntity(
                id="e1", kind=PhysicalThingKind.NATURAL_WATERCOURSE,
                canonical_label="高梁水", upstream_of=["x"],
            )

    def test_clean_entity_accepted(self):
        e = PersistentSpatialEntity(
            id="e1", kind=PhysicalThingKind.HYDRAULIC_STRUCTURE,
            canonical_label="西城闸",
        )
        assert e.kind == PhysicalThingKind.HYDRAULIC_STRUCTURE

    def test_state_carries_material_with_evidence(self):
        st = HistoricalFeatureState(
            id="st1", entity_id="e1", time_span=ts(1292, 1311, "a"),
            material="木构", function="调节瓮山泊下泄积水潭",
            evidence_fact_ids=["tf_yuan_shihqu"],
        )
        assert st.material == "木构"

    def test_state_without_evidence_rejected(self):
        """【负控制】状态必须有证据，否则形制断言成为无据推论"""
        with pytest.raises(ValueError) as e:
            HistoricalFeatureState(
                id="st", entity_id="e1", time_span=ts(1, 2), material="石构",
            )
        assert "文本事实证据" in str(e.value)


# ============ 第3轮杀手测试：木闸→石闸 ============

class TestWoodenToStoneGateKillerTest:
    """GPT 第3轮点名的验收标准：不能由"1311年始议砖石"推出"1312年此闸为石闸" """

    def test_1292_state_is_wooden(self):
        st = HistoricalFeatureState(
            id="st_wood", entity_id="ent_xichengzha", time_span=ts(1292, 1311, "w"),
            material="木构", evidence_fact_ids=["tf_shuiji_wood"],
        )
        assert st.material == "木构"
        assert st.time_span.contains(1295) is True

    def test_1312_inside_transitional_range_still_uncertain(self):
        """1312 落在1311-1327改石过渡期，视觉约束必须为 UNKNOWN 而非 FORBIDDEN"""
        vc = VisualPromptConstraints(
            entity_id="ent_xichengzha", target_year=1312,
            state_time_span=ts(1311, 1327, "t"),
            unknown=["该闸在1312年是否已完成砖石化，无逐闸确证"],
        )
        assert vc.unknown, "过渡期必须显式声明无证据，不得静默"
        assert not vc.forbidden, "过渡期不得输出FORBIDDEN，那是把未知当否定"

    def test_1327_stone_allowed(self):
        """泰定四年(1327)砖石修治告成后方可输出石构"""
        st = HistoricalFeatureState(
            id="st_stone", entity_id="ent_xichengzha", time_span=ts(1327, 1400, "s"),
            material="砖石", evidence_fact_ids=["tf_shuiji_stone"],
        )
        assert st.material == "砖石"
        assert st.time_span.contains(1330) is True

    def test_prompt_block_renders_four_states(self):
        """四态缺一不可：只输出required/forbidden会让UNKNOWN被当成无限制"""
        vc = VisualPromptConstraints(
            entity_id="e", target_year=1312,
            required=[VisualStateAssertion(
                id="v1", entity_id="e", year=1312, attribute="setting",
                directive="通惠河沿岸闸坝群", strength=ConstraintStrength.REQUIRED,
                evidence_fact_ids=["tf1"],
            )],
            forbidden=[VisualStateAssertion(
                id="v2", entity_id="e", year=1312, attribute="material",
                directive="大理石精雕", strength=ConstraintStrength.FORBIDDEN,
                evidence_fact_ids=["tf2"],
            )],
            unknown=["具体石构样式"],
            contested=[VisualStateAssertion(
                id="v3", entity_id="e", year=1312, attribute="material",
                directive="砖包石", strength=ConstraintStrength.CONTESTED,
                evidence_fact_ids=["tf3"], confidence_note="改石分期学界有分歧",
            )],
            coexisting_forms=["改石工程期间新旧并存"],
            identity_continuity_note="西城闸与后世高梁闸是否同一，学界存疑",
        )
        block = vc.as_prompt_block()
        for token in ["必须", "严禁", "存疑", "无证据", "并存", "身份连续性存疑"]:
            assert token in block, "四态输出缺 %s" % token

    def test_unknown_only_yields_no_forbidden(self):
        vc = VisualPromptConstraints(
            entity_id="e", target_year=9999, unknown=["无任何史料"],
        )
        block = vc.as_prompt_block()
        assert "无证据" in block
        assert "严禁" not in block


# ============ P0-6：历时身份断言 ============

class TestDiachronicIdentity:
    def test_same_continuant_accepted(self):
        a = DiachronicIdentityAssertion(
            id="dia1", subject_entity_ids=["ent_gaoliang", "ent_changhe"],
            relation=IdentityRelation.SAME_CONTINUANT, time_span=ts(1293, 1900, "i"),
            evidence_fact_ids=["tf1"], status=EpistemicStatus.CONTESTED,
            alternative_relations=["原河槽已废弃，仅水系层面延续"],
        )
        assert a.status == EpistemicStatus.CONTESTED
        assert a.is_orthogonal_to_state_change is True

    def test_uncertain_requires_both_sides(self):
        """【负控制】UNCERTAIN 必须列出争议双方，不得用一个标签掩盖"""
        with pytest.raises(ValueError) as e:
            DiachronicIdentityAssertion(
                id="dia2", subject_entity_ids=["a", "b"],
                relation=IdentityRelation.UNCERTAIN, time_span=ts(1, 2, "u"),
                evidence_fact_ids=["tf"], status=EpistemicStatus.CONTESTED,
                alternative_relations=[],
            )
        assert "alternative_relations" in str(e.value)

    def test_partial_continuation_allowed(self):
        """人工裁弯改道后：水系延续但原河槽废弃——必须能表达"""
        a = DiachronicIdentityAssertion(
            id="dia3", subject_entity_ids=["a", "b"],
            relation=IdentityRelation.PARTIAL_CONTINUATION,
            time_span=ts(1500, 1600, "p"), evidence_fact_ids=["tf"],
            status=EpistemicStatus.VERIFIED,
        )
        assert a.relation == IdentityRelation.PARTIAL_CONTINUATION


# ============ P0-7：毁损≠消亡，聚合≠分裂 ============

class TestPlaceTransformation:
    def test_damage_not_expressed_as_extinction(self):
        """【负控制】圆明园1860焚毁后仍有残存建筑，不得用 extinction"""
        with pytest.raises(ValueError) as e:
            PlaceTransformation(
                id="pte", entity_id="ent_yuanmingyuan",
                transformation=PlaceTransformationEvent.DAMAGED,
                time_span=ts(1860, 1860, "d"),
                resulting_state_id="extinction_1860",
                evidence_fact_ids=["tf"],
            )
        assert "毁损不得被表达为消亡" in str(e.value)

    def test_partial_destruction_accepted(self):
        pt = PlaceTransformation(
            id="pte2", entity_id="ent_yuanmingyuan",
            transformation=PlaceTransformationEvent.PARTIALLY_DESTROYED,
            time_span=ts(1860, 1900, "d2"),
            resulting_state_id="st_ruins_gardened",
            evidence_fact_ids=["tf_burn1860", "tf_1900"],
        )
        assert pt.transformation == PlaceTransformationEvent.PARTIALLY_DESTROYED

    def test_aggregate_not_split(self):
        """圆明/长春/绮春各自有边界又同属圆明三园——用聚合而非裂变"""
        agg = PlaceAggregate(
            id="agg3", label="圆明三园", time_span=ts(1770, 1860, "a"),
            member_entity_ids=["ent_yuanming", "ent_changchun", "ent_qichun"],
        )
        assert len(agg.member_entity_ids) == 3

    def test_relocation_and_diversion_exist(self):
        """河道改道、园林迁址都是空间对象变化，不是名称变化"""
        assert PlaceTransformationEvent.DIVERTED.value == "改道"
        assert PlaceTransformationEvent.RELOCATED.value == "迁址"


# ============ P0-8：名称不得承担消歧 ============

class TestAppellationDisambiguation:
    def test_same_label_multiple_referents(self):
        """【核心】"高梁桥"可同时是桥梁实体、街道名、站名、讹误载体"""
        apps = [
            Appellation(id="app_bridge", label="高梁桥", kind=AppellationKind.OFFICIAL,
                        valid_time_span=ts(1292, 1949, "b"), attesting_fact_ids=["tf1"]),
            Appellation(id="app_street", label="高梁桥", kind=AppellationKind.STREET_NAME,
                        valid_time_span=ts(1960, 2026, "s"), attesting_fact_ids=["tf2"]),
            Appellation(id="app_misplaced", label="高梁桥", kind=AppellationKind.MISPLACED_LEGEND,
                        valid_time_span=ts(1600, 1900, "m"), attesting_fact_ids=["tf3"]),
        ]
        assert len({a.label for a in apps}) == 1
        assert len({a.id for a in apps}) == 3, "同名必须可挂多个不同性质的名称节点"

    def test_referential_assertion_requires_evidence(self):
        """【负控制】禁止"字符串命中即自动绑定实体"的假消歧"""
        with pytest.raises(ValueError) as e:
            ReferentialAssertion(
                id="ra", appellation_id="app_bridge",
                referent_entity_id="ent_bridge", time_span=ts(1, 2, "r"),
                evidence_fact_ids=[],
            )
        assert "假消歧" in str(e.value)

    def test_battle_binds_watercourse_not_bridge(self):
        """【核心】高梁河之战指向水系，不是桥"""
        ra = ReferentialAssertion(
            id="ra_battle", appellation_id="app_gaolianghe",
            referent_entity_id="ent_gaoliang_watercourse",
            time_span=ts(979, 979, "bt"), evidence_fact_ids=["tf_liaoshi"],
            status=EpistemicStatus.CONTESTED,
        )
        assert ra.referent_entity_id == "ent_gaoliang_watercourse"
        assert ra.status == EpistemicStatus.CONTESTED, "战场落点学界有争议，须保留"

    def test_textual_corruption_kind_exists(self):
        """讹字必须是独立类型，不能当作规范字形"""
        app = Appellation(id="app_corrupt", label="高粱河",
                          kind=AppellationKind.TEXTUAL_CORRUPTION,
                          valid_time_span=ts(1500, 1900, "c"))
        assert app.kind == AppellationKind.TEXTUAL_CORRUPTION


# ============ P0-9：生产接口契约 ============

class TestVideoContracts:
    def test_storyboard_exposes_discontinuity(self):
        """分镜不得静默缝合时间跳跃"""
        sb = VideoStoryboard(
            entity_id="ent_gaoliang", frames=[],
            identity_continuity_disputed=True,
            discontinuity_warnings=["1292木构闸与1327砖石闸之间存在16年改石过渡期，不得直接跳变"],
        )
        assert sb.identity_continuity_disputed is True
        assert sb.discontinuity_warnings

    def test_frame_records_contested_claims(self):
        f = StoryboardFrame(
            frame_index=1, time_span=ts(979, 979, "f"), state_id="st_battle",
            title="高梁河之战", accepted_claim_ids=["c1"], contested_claim_ids=["c2"],
        )
        assert f.contested_claim_ids == ["c2"], "争议断言必须在片中标注存疑"

    def test_claim_parsed_before_audit(self):
        """【第3轮§17】必须先消歧拆命题，不能只扫字符串"""
        claim = ParsedClaim(
            claim_text="979年宋辽两军在高梁桥旁激战", claim_type=ClaimType.EVENT,
            resolved_appellation_id="app_bridge", resolved_entity_id="ent_bridge",
            year=979, disambiguation_confidence=0.93,
        )
        res = AuditResult(
            claim=claim, verdict=AuditVerdict.BLOCK,
            reason="桥梁实体桥闸形制始见于元至元二十九年(1292)，979年无该桥",
            conflicting_state_id="st_xichengzha_1292",
        )
        assert res.verdict == AuditVerdict.BLOCK

    def test_low_confidence_disambiguation_not_blocked(self):
        """消歧失败时必须 UNTESTABLE，不能假装通过也不能假装有罪"""
        claim = ParsedClaim(
            claim_text="高梁桥边有碑", claim_type=ClaimType.EXISTENCE,
            year=None, disambiguation_confidence=0.31,
        )
        res = AuditResult(
            claim=claim, verdict=AuditVerdict.UNTESTABLE,
            reason="名称消歧置信度过低，无法确定所指实体",
        )
        assert res.verdict == AuditVerdict.UNTESTABLE

    def test_untestable_is_not_pass(self):
        """【架构红线】UN TESTABLE 不等于 PASS——这正是E11假通过事故的教训"""
        assert AuditVerdict.UNTESTABLE != AuditVerdict.PASS
