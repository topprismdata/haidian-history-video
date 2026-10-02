"""
tests/haidian_kg/test_xishan.py
西山一线词条入库测试（holdout run3 覆盖缺口批次：大觉寺/碧云寺/温泉/凤凰岭/北安河/金山）

史料基准（全部为《钦定日下旧闻考》卷100/卷106 与《帝京景物略》卷六一手文本，
研究底稿 docs/kg/research/xishan.md 已逐字落盘原文）：
- 大觉寺：辽咸雍四年(1068)清水院（辽碑）→ 金章宗西山八院（明人追述）→
  宣德三年(1428)重建更名 → 正统十一年(1446)敕修 → 康熙五十九年(1720)修葺 →
  乾隆十二年(1747)发帑重修 → 2006 第六批全国重点
- 碧云寺：至顺二年(1331)元碑/碧云庵 → 正德十一年(1516)扩为寺 → 天启三年(1623)重饰
  → 乾隆十三年(1748)金刚宝座塔 → 1925-1929 孙中山停灵/衣冠 → 2001 第五批国保
- 金山：明代妃嫔皇子葬地总名（Main 纠偏口径），金陵在房山已排除；
  与 settlements 的 ent_jinshan 跨模块同指断言
- 「北安河金章宗行宫」式混说必须被阻断（时间先后：辽碑 1068 << 官书首见 1782）
"""
import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from haidian_kg.calibration import xishan as X
from haidian_kg.calibration import settlements as S
from haidian_kg.production_exports import (
    KnowledgeBase, audit_script, export_storyboard,
)
from haidian_kg.qa_gate import QAGate
from haidian_kg.ontology.video_contracts import AuditVerdict
from haidian_kg.ontology.spatiotemporal import IdentityRelation, EpistemicStatus

#: 逐句期望的对抗样本：真陈述 + 口径混说（乾隆十二年重修 ≠ 增五百间房）
ADV = ("1446年大觉寺奉敕重修。大觉寺在1747年重修时有房五百间。",
       [("1446年大觉寺奉敕重修", "通过"),
        ("大觉寺在1747年重修时有房五百间", "非通过")])


@pytest.fixture(scope="module")
def kb():
    return KnowledgeBase(
        sources=X.SOURCES, divisions=X.DIVISIONS, facts=X.FACTS,
        entities=X.ENTITIES, states=X.STATES, identities=X.IDENTITIES,
        appellations=X.APPELLATIONS, references=X.REFERENCES,
        transformations=X.TRANSFORMATIONS, propositions=X.PROPOSITIONS,
        adoptions=X.ADOPTIONS, aggregates=X.AGGREGATES)


# ==================================================================
# 入库闸门
# ==================================================================

class TestXishanEntryGate:
    def test_entry_passes_gate(self, kb):
        rep = QAGate("xishan", kb, adversarial=ADV).run()
        assert rep.passed, rep.render()

    def test_uses_unified_bibliography(self, kb):
        """一部书只能一个节点，不得按卷次重复建"""
        titles = [s.title for s in kb.sources.values()]
        assert len(titles) == len(set(titles)), "同一本书被建成多条：%s" % titles

    def test_all_facts_traceable(self, kb):
        div_ids = set(kb.divisions.keys())
        for f in kb.facts.values():
            assert f.division_id in div_ids, f.id

    def test_gate_catches_removed_fact(self, kb):
        """抽掉一条引文后闸门必须失败（防恒真）"""
        from copy import deepcopy
        kb2 = KnowledgeBase(
            sources=list(kb.sources.values()), divisions=list(kb.divisions.values()),
            facts=list(kb.facts.values()),
            entities=list(kb.entities.values()), states=list(kb.states.values()),
            identities=list(kb.identities),
            appellations=list(kb.appellations.values()),
            references=kb.references,
            transformations=list(kb.transformations.values()),
            propositions=list(kb.propositions.values()),
            adoptions=list(kb.adoptions.values()),
            aggregates=list(kb.aggregates.values()),
            people=[], resources=[])
        kb2.facts.pop("tf_xs_liaobei_zhuanji")
        rep = QAGate("xishan-broken", kb2, adversarial=ADV).run()
        assert not rep.passed, "抽掉引文后闸门仍通过 = 闸门恒真"


# ==================================================================
# 关键实体与 canonical_label
# ==================================================================

class TestKeyEntities:
    def test_nine_entities_present(self, kb):
        expected = {
            "ent_xs_dajuesi": "大觉寺",
            "ent_xs_biyunsi": "碧云寺",
            "ent_xs_wenquan": "温泉村",
            "ent_xs_wq_quanyan": "温泉",
            "ent_xs_wenquanzhen": "温泉镇",
            "ent_xs_fenghuangling": "凤凰岭",
            "ent_xs_fhl_jingqu": "凤凰岭自然风景区",
            "ent_xs_beianhe": "北安河村",
            "ent_xs_jinshan": "金山",
            "ent_xs_liaobei": "旸台山清水院创造藏经记碑",
            "ent_xs_jingangta": "碧云寺金刚宝座塔",
            "ent_xs_longquansi": "龙泉寺",
        }
        for eid, head in expected.items():
            assert eid in kb.entities, eid
            assert kb.entities[eid].canonical_label.startswith(head), \
                "%s canonical_label=%s" % (eid, kb.entities[eid].canonical_label)

    def test_entities_carry_no_visual_attributes(self, kb):
        """实体只承载身份，形制必须下沉到状态"""
        for e in kb.entities.values():
            assert not ({"geometry", "material", "function"} & set(e.model_fields_set))


# ==================================================================
# 关键年代断言（口径分离）
# ==================================================================

class TestChronology:
    def test_dajuesi_liao_stele_is_floor(self, kb):
        """建置下限以辽碑为准：1068 年清水院必须有状态"""
        st = kb.state_at("ent_xs_dajuesi", 1068)
        assert st is not None and st.id == "st_xs_djs_liao"
        assert kb.state_at("ent_xs_dajuesi", 1050) is None, \
            "辽咸雍四年前不得有建置状态"

    def test_jin_eight_courts_window(self, kb):
        st = kb.state_at("ent_xs_dajuesi", 1200)
        assert st.id == "st_xs_djs_jin"
        assert "八院" in st.function

    def test_xuande_rename_not_founding(self, kb):
        """1428 是改名年非始建年；1428 前另有辽金元状态"""
        assert kb.state_at("ent_xs_dajuesi", 1427).id == "st_xs_djs_lingquan"
        st = kb.state_at("ent_xs_dajuesi", 1428)
        assert "更名" in st.function or "易" in st.function

    def test_qianlong_1747_repair(self, kb):
        st = kb.state_at("ent_xs_dajuesi", 1800)
        assert st.id == "st_xs_djs_qianlong"
        assert "乾隆十二年" in st.geometry or "1747" in st.geometry

    def test_biyunsi_three_dates_separate(self, kb):
        """1331 元碑 / 1516 改寺 / 1623 重饰分属三个状态，绝不混写同年"""
        assert kb.state_at("ent_xs_biyunsi", 1400).id == "st_xs_bys_yuan"
        assert kb.state_at("ent_xs_biyunsi", 1550).id == "st_xs_bys_zhengde"
        assert kb.state_at("ent_xs_biyunsi", 1630).id == "st_xs_bys_tianqi"

    def test_biyunsi_repair_not_extinction(self, kb):
        """2024 大修重开：毁损≠消亡，不得出现消亡式表达"""
        pt = kb.transformations["pte_xs_bys_2024_repair"]
        hay = "%s %s" % (pt.resulting_state_id or "", pt.resulting_condition or "")
        for m in ("消亡", "不复存在", "已废弃"):
            assert m not in hay

    def test_jinshan_ming_burial_window(self, kb):
        st = kb.state_at("ent_xs_jinshan", 1534)
        assert st.id == "st_xs_js_ming"
        assert "妃" in st.function and "皇子" in st.function
        assert kb.state_at("ent_xs_jinshan", 1424) is None, \
            "仁宗朝(1425)前不得有金山妃嫔葬地状态"

    def test_beianhe_first_seen_1782(self, kb):
        """北安河村名官书首见乾隆朝；1782 前无具体状态（开放起始除外）"""
        st = kb.state_at("ent_xs_beianhe", 1782)
        assert st.id == "st_xs_bah_1782"
        # 1782 前只能命中开放起始状态（成村年代无考）
        st0 = kb.state_at("ent_xs_beianhe", 1700)
        assert st0.id == "st_xs_bah_yuancun"
        assert st0.time_span.open_begin is True
        assert st0.time_span.begin is None, "开放起始不得伪造 DatePoint"

    def test_no_same_begin_year_states(self, kb):
        """G5 复核：任一实体不得有同起始年的重复状态"""
        by_entity = {}
        for s in kb.states.values():
            by_entity.setdefault(s.entity_id, []).append(s)
        for eid, states in by_entity.items():
            years = [s.time_span.begin.gregorian.year for s in states
                     if s.time_span.begin and s.time_span.begin.gregorian]
            assert len(set(years)) == len(years), "%s 起始年重复：%s" % (eid, years)


# ==================================================================
# holdout 缺口面：字形表命中（本批目标全部可命中）
# ==================================================================

class TestHoldoutGapFaces:
    def test_registry_hits_all_gap_faces(self):
        """run3 的 KB 覆盖缺口 FP 面必须全部进入本模块字形表"""
        from haidian_kg.evaluation.holdout_eval import (
            build_name_registry, norm_eval)
        reg = build_name_registry(["xishan"])
        for form in ["清水院", "大觉寺", "西山大觉寺", "碧云寺", "碧云庵",
                     "温泉", "温泉村", "凤凰岭", "龙泉寺",
                     "北安河", "金山", "金山口"]:
            assert norm_eval(form) in reg.forms, "缺口面未入字形表：%s" % form

    def test_wenquanzhen_split_with_form_excluded(self):
        """GPT审3-2 双钉：①模型层「温泉镇」独立政区实体在册；
        ②评测层其形符仍排除——金标最长匹配会吃掉「温泉」字面，与挖掘器
        子串命中产生 span 错位 FP（scoped holdout 对照实测）。两层各自成立。"""
        from haidian_kg.ontology.spatiotemporal import PhysicalThingKind
        ent = {e.id: e for e in X.ENTITIES}["ent_xs_wenquanzhen"]
        assert ent.kind == PhysicalThingKind.ADMIN_DIVISION
        from haidian_kg.evaluation.holdout_eval import (
            build_name_registry, norm_eval)
        reg = build_name_registry(["xishan"])
        assert norm_eval("温泉镇") not in reg.forms

    def test_gold_extraction_on_holdout_style_text(self):
        """holdout 原文风格的段文本必须产出金标 mention"""
        from haidian_kg.evaluation.holdout_eval import (
            build_name_registry, extract_gold_mentions)
        reg = build_name_registry(["xishan"])
        seg = ("清水院（今大觉寺，北安河金章宗行宫与避暑水院）\n"
               "香水院（今海淀温泉镇温泉后山）\n"
               "潭水院（今海淀凤凰岭龙泉寺水院）\n"
               "金山在宛平县西三十里，俗呼一溜边山七十二府。")
        surfaces = {g.surface for g in extract_gold_mentions(
            seg, "test_seg", reg)}
        for need in ["清水院", "大觉寺", "北安河", "温泉", "凤凰岭", "龙泉寺", "金山"]:
            assert need in surfaces, "金标未命中：%s" % need

    def test_forms_map_to_entities(self):
        from haidian_kg.evaluation.holdout_eval import (
            build_name_registry, norm_eval)
        reg = build_name_registry(["xishan"])
        assert reg.entities_of(norm_eval("大觉寺")) == {"ent_xs_dajuesi"}
        assert reg.entities_of(norm_eval("清水院")) == {"ent_xs_dajuesi"}
        assert "ent_xs_biyunsi" in reg.entities_of(norm_eval("碧云寺"))
        assert "ent_xs_wq_quanyan" in reg.entities_of(norm_eval("温泉"))
        assert "ent_xs_wenquan" in reg.entities_of(norm_eval("温泉村"))
        assert "ent_xs_fenghuangling" in reg.entities_of(norm_eval("凤凰岭"))
        assert "ent_xs_fhl_jingqu" in reg.entities_of(
            norm_eval("凤凰岭自然风景区"))
        assert "ent_xs_beianhe" in reg.entities_of(norm_eval("北安河"))
        assert "ent_xs_jinshan" in reg.entities_of(norm_eval("金山"))


# ==================================================================
# 跨模块同指：金山 ↔ settlements.ent_jinshan
# ==================================================================

class TestCrossModuleIdentity:
    def test_jinshan_same_as_settlements(self, kb):
        """Main 纠偏口径：不重复建模，跨模块同指必须显式断言"""
        ids = [i for i in kb.identities
               if set(i.subject_entity_ids) == {"ent_xs_jinshan", "ent_jinshan"}]
        assert len(ids) == 1, "缺跨模块同指断言 dia_xs_jinshan_same_settlements"
        assert ids[0].relation == IdentityRelation.SAME_CONTINUANT
        assert ids[0].status == EpistemicStatus.VERIFIED
        assert set(ids[0].evidence_fact_ids) <= {
            f.id for f in kb.facts.values()}

    def test_jinshan_relation_state_mentions_domain(self, kb):
        """金山为陵区总名，娘娘府/董四墓在其域内（关系 state 表述）"""
        st = kb.states["st_xs_js_ming"]
        assert "娘娘府" in st.geometry and "董四墓" in st.geometry
        assert "总名" in st.geometry

    def test_jinling_fangshan_excluded(self, kb):
        """金陵在房山：金代陵区说必须显式排除"""
        p = kb.propositions["prop_xs_jinling_fangshan"]
        assert "房山" in p.statement
        assert kb.adoptions["prop_xs_jinling_fangshan"].status.value == "已确证"


# ==================================================================
# 存疑必须标注（G4）
# ==================================================================

class TestUncertaintyMarked:
    def test_longquansi_contested(self, kb):
        ad = kb.adoptions["prop_xs_longquansi_niandai"]
        assert ad.status.value == "学术争议"
        p = kb.propositions["prop_xs_longquansi_niandai"]
        assert "辽应历" in p.statement and "存疑" in p.statement

    def test_beianhe_etymology_contested(self, kb):
        ad = kb.adoptions["prop_xs_beianhe_etymology"]
        assert ad.status.value == "学术争议"
        assert "安和" in kb.propositions["prop_xs_beianhe_etymology"].statement

    def test_wenquan_miao_unsubstantiated(self, kb):
        ad = kb.adoptions["prop_xs_wenquan_miao"]
        assert ad.status.value == "无据推论"
        assert ad.confidence < 0.4

    def test_yulan_no_date_listed(self, kb):
        """玉兰：名物可登记、年代不列"""
        p = kb.propositions["prop_xs_yulan_niandai"]
        assert "无文献与树木档案确证" in p.statement
        assert kb.adoptions["prop_xs_yulan_niandai"].status.value == "学术争议"

    def test_qishierfu_is_folk_not_official(self, kb):
        ad = kb.adoptions["prop_xs_qishierfu_suyan"]
        assert ad.status.value == "已证伪"
        assert ad.refuting_fact_ids, "俗谚误标须附反驳证据"

    def test_xiangshuiyuan_conflict_not_interval(self, kb):
        """香水院两说：采文献原文口径，不取区间值"""
        p = kb.propositions["prop_xs_bayuan_guifu"]
        assert "法云寺" in p.statement
        assert "温泉后山说" in p.alternative_explanations[0]


# ==================================================================
# 审计层：本词条特有的错误必须能抓
# ==================================================================

class TestXishanAudit:
    def test_beianhe_not_jin_xinggong(self, kb):
        """「北安河金代已是行宫属地」必须被阻断/不可判通过"""
        r = audit_script(kb, "北安河在1200年已是金章宗行宫属地。")
        assert r[0].verdict != AuditVerdict.PASS, \
            "北安河村名官书首见1782，1200年无据可判"

    def test_dajuesi_not_jin_founding(self, kb):
        """「大觉寺为金章宗初创」矮化辽代：辽代状态在先，1446 前后的表述可判"""
        r = audit_script(kb, "1446年大觉寺奉敕重修。")
        assert r[0].verdict == AuditVerdict.PASS

    def test_jinshan_extinction_blocked(self, kb):
        """「金山已不复存在」：与持续存在断言矛盾，必须 BLOCK"""
        r = audit_script(kb, "金山在2000年已不复存在。")
        assert r[0].verdict == AuditVerdict.BLOCK

    def test_storyboard_frames(self, kb):
        """出图约束：大觉寺按状态分帧（辽院→宣德改名→乾隆重修→今）"""
        sb = export_storyboard(kb, "ent_xs_dajuesi")
        assert [f.state_id for f in sb.frames] == [
            "st_xs_djs_liao", "st_xs_djs_jin", "st_xs_djs_lingquan",
            "st_xs_djs_xuande", "st_xs_djs_zhengtong", "st_xs_djs_yongzheng",
            "st_xs_djs_qianlong", "st_xs_djs_2006"]


# ==================================================================
# 跨模块状态读取（ settlements 的 ent_jinshan 不被本模块遮蔽）
# ==================================================================

class TestSettlementsUnaffected:
    def test_settlements_jinshan_entity_untouched(self):
        """settlements 模块的 ent_jinshan 实体仍独立存在（本模块不遮蔽不重复建模）"""
        kb_s = KnowledgeBase(entities=S.ENTITIES, states=S.STATES)
        assert "ent_jinshan" in kb_s.entities
        assert kb_s.entities["ent_jinshan"].kind.value == "墓葬群"
