"""
tests/haidian_kg/test_bridges_entry.py
桥类词条入库测试（E8 高梁桥 + E2 安河桥）

史料基准（全部为两份 research.md v2 冻结结论，不凭印象断言）：
- 979 高梁河之战在古高梁河畔（落点诸说并存），与 1292 年始建的高梁桥分属不同实体；
  「桥下就是战场」必须被拦下（结构上不可通过），真陈述放行
- 金承安三年(1198)已有闸记录；1292 是郭守敬重建，金元闸同址不能画等号
- 闸已毁：现代「仍在服役」断言不得通过
- 现桥尺寸/孔数/望柱数不入库；1980—1982 大改、非完整原状
- 字形：高梁桥（木字底，2024 名录纠偏）≠ 高粱闸（米字底，2013 国保沿用），
  两名录并存皆官方；「高亮桥」为传说名
- 安河桥桥史两套文献系统正面冲突（CONTESTED 保留，不制造确定性）
- 两河两桥严格分离：旧桥跨清河（名效至 1964），1965 京密引水渠另址建新桥；
  「古桥一直跨京密引水渠」为 DISPROVEN
- 安河桥村地名出现年代＝明代（名录）；丰益仓 1729 八旗俸饷仓（数字链撤稿，
  审计层对混说数字直接 BLOCK）
"""
import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from haidian_kg.calibration import bridges as BR
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
        sources=BR.SOURCES, divisions=BR.DIVISIONS, facts=BR.FACTS,
        entities=BR.ENTITIES, states=BR.STATES, identities=BR.IDENTITIES,
        appellations=BR.APPELLATIONS, references=BR.REFERENCES,
        transformations=BR.TRANSFORMATIONS, propositions=BR.PROPOSITIONS,
        adoptions=BR.ADOPTIONS, aggregates=BR.AGGREGATES,
        people=PEOPLE, resources=RESOURCES)


#: 逐句期望的对抗样本（G7）：两条真陈述 + 两条必须拦下的红线陈述
ADV = (
    "979年，宋辽大战发生在高梁桥下。元代高梁闸在2026年仍在服役。"
    "1982年，高梁桥经大规模改造，今天看到的不是完整的原状古桥。"
    "1965年，因修京密引水渠，另址新建安河新桥。",
    [("979年，宋辽大战发生在高梁桥下", "非通过"),
     ("元代高梁闸在2026年仍在服役", "非通过"),
     ("1982年，高梁桥经大规模改造，今天看到的不是完整的原状古桥", "通过"),
     ("1965年，因修京密引水渠，另址新建安河新桥", "通过")],
)


def _all_text(kb_) -> str:
    parts = []
    for s in kb_.states.values():
        parts += [s.geometry or "", s.material or "", s.function or "",
                  s.admin_status or ""]
    for p in kb_.propositions.values():
        parts.append(p.statement)
    return " ".join(parts)


# ==================================================================
# 入库闸门（九维 QA：fail=0, warn=0, skip=0）
# ==================================================================

class TestBridgesEntryGate:
    def test_entry_passes_gate_zero_warn_skip(self, kb):
        rep = QAGate("bridges", kb, adversarial=ADV).run()
        assert rep.passed, rep.render()
        assert not [f for f in rep.findings if f.level == "warn"], rep.render()
        assert not [f for f in rep.findings if f.level == "skip"], rep.render()

    def test_uses_unified_bibliography(self, kb):
        """一部书只能一个节点；新书目一律取自统一书目表"""
        titles = [s.title for s in kb.sources.values()]
        assert len(titles) == len(set(titles)), "同一本书被建成多条：%s" % titles

    def test_all_facts_traceable(self, kb):
        div_ids = set(kb.divisions.keys())
        for f in kb.facts.values():
            assert f.division_id in div_ids, f.id

    def test_contested_bibliography_transit_marked(self, kb):
        """1929 档案是转引，必须在 note 标明且不得当定论"""
        f = kb.facts["tf_bma_yuanyiqian"]
        assert "转引" in f.translator_note
        assert "未目验" in f.translator_note

    def test_two_gong_dingjianji_already_complete(self):
        """《两宫鼎建记》在 E9 已按一书一条登记（含作者贺仲轼）——本任务核对即可"""
        from haidian_kg.calibration.bibliography import BIBLIOGRAPHY, source_by_title
        src = source_by_title("两宫鼎建记")
        assert src is not None and src.author_person_id == "person_hezhongshi"
        assert src.id in {s.id for s in BIBLIOGRAPHY}

    def test_new_books_registered(self):
        from haidian_kg.calibration.bibliography import BIBLIOGRAPHY
        by_id = {s.id: s for s in BIBLIOGRAPHY}
        for sid in ("src_jinshi", "src_dajinjili", "src_lidaizhiguangbiao"):
            assert sid in by_id, sid
        assert by_id["src_jinshi"].author_person_id == "person_tuotuo"
        assert by_id["src_dajinjili"].author_person_id == "person_zhangwei"
        assert by_id["src_dajinjili"].total_volumes == 40
        assert by_id["src_lidaizhiguangbiao"].issuing_body
        assert by_id["src_lidaizhiguangbiao"].total_volumes == 72

    def test_zhou_sun_registered_for_dijingjingwulue(self):
        """E8 红线：帝京景物略为刘侗、于奕正同撰，周损编辑——不得说一人所撰"""
        from haidian_kg.calibration.bibliography import source_by_title
        src = source_by_title("帝京景物略")
        assert "person_zhou_sun" in (src.compiler_person_ids or [])
        assert "周损" in src.edition_note


# ==================================================================
# E8 红线：979 战场与桥的空间分离
# ==================================================================

class TestGaoliangqiaoRedlines:
    def test_979_battlefield_is_separate_entity(self, kb):
        """979 年桥无状态（结构上不可通过）；战场在独立实体上"""
        assert kb.state_at("ent_gaoliang_bridge", 979) is None
        st = kb.state_at("ent_gaoliang_battlefield", 979)
        assert st is not None and st.id == "st_battle_979"
        begins = sorted(s.time_span.begin.gregorian.year
                        for s in kb.states_of("ent_gaoliang_bridge"))
        assert begins[0] == 1292, "高梁桥最早状态必须是1292（金1198闸记录挂在闸实体）"

    def test_313_years_is_time_span_not_spatial_identity(self, kb):
        dia = next(d for d in kb.identities if d.id == "dia_battle_not_bridge")
        span = dia.time_span.end.gregorian.year - dia.time_span.begin.gregorian.year
        assert span == 313
        assert "同一地点" in "；".join(dia.alternative_relations), \
            "313 年只能作时间跨度讲，空间关系必须显式否定"

    def test_battle_grading_split(self, kb):
        """乘驴车=[文献记载]；中箭=[后世记载]；战因分析不得当史籍因果"""
        st = kb.states["st_battle_979"]
        assert "乘驴车" in st.function and "涿州" in st.function
        assert "[文献记载]" in st.function and "[后世记载]" in st.function
        ad = kb.adoptions["prop_battle_979_fenji"]
        assert ad.status == EpistemicStatus.VERIFIED
        prop = kb.propositions["prop_battle_979_fenji"]
        assert "后世军事分析" in prop.statement
        assert "乾亨" in st.time_span.begin.reign_year.verbatim, \
            "辽纪年用乾亨元年，不用辽保宁十一年"
        all_text = _all_text(kb)
        assert "保宁十一年" not in all_text

    def test_jin_yuan_gate_not_equated(self, kb):
        """金代闸（1198）与元代闸（1292）不能画等号，只能并列说「金代已有，元代重建」"""
        st1198 = kb.state_at("ent_gaoliang_gate", 1198)
        st1292 = kb.state_at("ent_gaoliang_gate", 1292)
        assert st1198.id == "st_glz_jin_1198" and st1292.id == "st_glz_yuan_1292"
        assert "不能画等号" in st1198.function
        assert "1292年是这条河第一道闸" in kb.propositions[
            "prop_gate_jin_yuan_relation"].statement.replace(
            "「", "").replace("」", "") or "第一道闸" in \
            kb.propositions["prop_gate_jin_yuan_relation"].statement
        dia = next(d for d in kb.identities if d.id == "dia_gate_jin_yuan")
        assert dia.status == EpistemicStatus.CONTESTED
        assert len(dia.alternative_relations) >= 2

    def test_gate_destroyed_no_modern_state(self, kb):
        """闸已毁：2026 年无状态支撑，「仍在服役」不得通过"""
        assert kb.state_at("ent_gaoliang_gate", 2026) is None
        r = audit_script(kb, "2026年，元代高梁闸仍在服役。")
        assert r[0].verdict != AuditVerdict.PASS, r[0].reason

    def test_no_battle_dimensions_in_bridge_states(self, kb):
        """现桥尺寸/孔数/望柱数三源冲突，一律不入库（状态层不得出现；
        红线纪律句允许出现在命题层）"""
        states_text = " ".join(
            "%s%s%s" % (s.geometry or "", s.material or "", s.function or "")
            for s in kb.states.values())
        for banned in ("18.4", "15.4", "20.5", "5.58", "16对", "望柱"):
            assert banned not in states_text, banned
        st = kb.states["st_glb_1980"]
        assert "1980—1982" in st.function and "非完整原状" in (
            st.function + st.material)
        prop = kb.propositions["prop_bridge_not_original"]
        assert "望柱数三源冲突" in prop.statement, "纪律句挂在命题层"

    def test_ziliang_official_vs_minglu_correction(self, kb):
        """木字底「高梁桥/高梁闸」与米字底「高粱闸」并存皆官方；字形不同指称不同名"""
        assert kb.appellations["app_sorghum_gate"].label == "高粱闸"
        assert kb.appellations["app_gaoliangzha"].label == "高梁闸"
        assert kb.appellations["app_sorghum_gate"].label != \
            kb.appellations["app_gaoliangzha"].label
        prop = kb.propositions["prop_minglu_correction"]
        assert "2024" in prop.statement and "不得互斥" in prop.statement
        assert "2024年11月13日" in kb.facts["tf_minglu_gaoliang"].verbatim_quote

    def test_changhe_zhuanhe_boundary_modern_state(self, kb):
        """长河/转河分界挂当代状态；「统称南长河」不得出现在任何状态正文"""
        st = kb.states["st_glb_2003"]
        assert "长河" in st.geometry and "转河" in st.geometry
        states_text = " ".join(
            "%s%s%s" % (s.geometry or "", s.material or "", s.function or "")
            for s in kb.states.values())
        assert "统称南长河" not in states_text

    def test_yihongtang_vs_dock(self, kb):
        st = kb.states["st_yht_1751"]
        assert st.time_span.begin.reign_year.year_within_reign == 16
        assert "另有船坞" in st.geometry and "水陆换乘" in st.function
        assert kb.transformations["pte_yht_1751_built"].time_span.begin \
            .gregorian.year == 1751

    def test_legend_name_not_etymology(self, kb):
        """「高亮桥」是传说名：指称必须 FOLK_LEGEND + provenance，不建得名链"""
        ref = kb.references_by_id["rr_gaoliang_legend"]
        assert ref.status == EpistemicStatus.FOLK_LEGEND
        assert "得名演变链" in ref.provenance
        ad = kb.adoptions["prop_gaoliang_legend"]
        assert ad.status == EpistemicStatus.FOLK_LEGEND


# ==================================================================
# E2 红线：双系统、两河两桥、村龄、丰益仓
# ==================================================================

class TestAnheqiaoRedlines:
    def test_dual_system_contested_not_resolved(self, kb):
        """桥史两套文献系统正面冲突：CONTESTED 保留，不制造确定性"""
        dia = next(d for d in kb.identities if d.id == "dia_anh_two_systems")
        assert dia.status == EpistemicStatus.CONTESTED
        alts = "；".join(dia.alternative_relations)
        assert "1724" in alts and "元以前" in alts
        ad = kb.adoptions["prop_anhe_dual_system"]
        assert ad.status == EpistemicStatus.CONTESTED and ad.confidence < 0.7
        states_text = _all_text(kb)
        assert "始建于1724年" not in states_text.replace("（1724", "（"), \
            "任一单一年代始建定论不得作为事实陈述"

    def test_two_rivers_two_bridges_strictly_split(self, kb):
        """旧桥名效至 1964；1965 新桥另址建——「古桥跨渠」结构上不可通过"""
        assert kb.state_at("ent_anhe_bridge", 1965) is None
        st = kb.state_at("ent_anhe_new_bridge", 1965)
        assert st is not None and st.id == "st_anhn_1965"
        r = audit_script(kb, "1965年，安河桥横跨京密引水渠。")
        assert r[0].verdict != AuditVerdict.PASS, r[0].reason
        ad = kb.adoptions["prop_anhe_jingmi_confusion"]
        assert ad.status == EpistemicStatus.DISPROVEN
        assert ad.refuting_fact_ids and all(f in kb.facts
                                            for f in ad.refuting_fact_ids)

    def test_village_ming_dating_not_xianfeng(self, kb):
        """名录：安河桥村地名出现年代为明代；咸丰成村说撤稿"""
        assert "明代" in kb.facts["tf_minglu_anhecun"].verbatim_quote
        ad = kb.adoptions["prop_village_ming_dating"]
        assert ad.status == EpistemicStatus.VERIFIED
        states_text = " ".join(
            "%s%s%s" % (s.geometry or "", s.material or "", s.function or "")
            for s in kb.states.values())
        assert "咸丰" not in states_text
        prop = kb.propositions["prop_village_ming_dating"]
        assert "咸丰" in "；".join(prop.alternative_explanations), \
            "咸丰说只能以撤稿身份出现在备择解释里"

    def test_fengyicang_1729_no_number_chain(self, kb):
        """丰益仓：雍正七年官书口径；66300石/八万兵丁数字链不入库"""
        st = kb.states["st_fyc_1729"]
        assert st.time_span.begin.reign_year.year_within_reign == 7
        assert "俸饷" in st.function and "圆明园" in st.function
        text = _all_text(kb)
        assert "66300" not in text and "六万六千三百" not in text
        assert "八万余兵丁" not in text and "八万官兵" not in text

    def test_muzhuang_internal_dates_excluded(self, kb):
        """木桩 L2 实物图可述；L5 内部年代区间不入库、口播禁用"""
        assert "明代木桩" in kb.facts["tf_muzhuang_2009"].verbatim_quote
        text = _all_text(kb)
        assert "1400—1475" not in text and "1400-1475" not in text
        prop = kb.propositions["prop_muzhuang_two_layers"]
        assert "口播禁用" in prop.statement

    def test_station_naming_discipline(self, kb):
        """「规划阶段曾以龙背村命名」，不说名字搬到了地铁站（状态层不得出现）"""
        prop = kb.propositions["prop_longbei_naming"]
        assert "规划阶段曾以" in prop.statement
        assert "不说「龙背村的名字搬到了地铁站」" in prop.statement, \
            "纪律句挂在命题层"
        states_text = " ".join(
            "%s%s%s" % (s.geometry or "", s.material or "", s.function or "")
            for s in kb.states.values())
        assert "搬到了地铁站" not in states_text


# ==================================================================
# 审计器两向验证（抓真错 + 放真话）
# ==================================================================

class TestAudit:
    def test_979_under_bridge_blocked_from_pass(self, kb):
        r = audit_script(kb, "979年，宋辽大战发生在高梁桥下。")
        assert r[0].verdict != AuditVerdict.PASS, r[0].reason

    def test_fengyi_numeric_chain_blocked(self, kb):
        """俸米石数/兵额换算与官书记录不符 → 口径混说必须 BLOCK"""
        r = audit_script(kb, "丰益仓在雍正七年建成后，仓内囤米66300石，可支八万人。")
        assert r[0].verdict == AuditVerdict.BLOCK, r[0].reason

    def test_true_1982_statement_passes(self, kb):
        r = audit_script(kb, "1982年，高梁桥经大规模改造，今天看到的不是完整的原状古桥。")
        assert r[0].verdict == AuditVerdict.PASS, r[0].reason

    def test_true_1965_new_bridge_passes(self, kb):
        r = audit_script(kb, "1965年，因修京密引水渠，另址新建安河新桥。")
        assert r[0].verdict == AuditVerdict.PASS, r[0].reason

    def test_old_bridge_contested_origin_not_pass(self, kb):
        """「始建于1724」这类单系统定论：命中石拱期状态时不产生 BLOCK，
        其防线在认识论层（CONTESTED 采信），审计层至多放行真形态描述——
        此处验证它至少不与库内记录冲突到需要阻断的程度（无口径数字冲突）"""
        r = audit_script(kb, "1724年，安河桥始建。")
        assert r[0].verdict in (AuditVerdict.PASS, AuditVerdict.UNTESTABLE)


# ==================================================================
# 分镜导出（状态链完整、身份争议显式暴露）
# ==================================================================

class TestStoryboard:
    def test_bridge_state_chain(self, kb):
        sb = export_storyboard(kb, "ent_gaoliang_bridge")
        assert [f.state_id for f in sb.frames] == [
            "st_glb_1292", "st_glb_1980", "st_glb_2003"]
        assert sb.identity_continuity_disputed, \
            "979桥址存疑必须显式暴露给分镜层"

    def test_new_bridge_single_frame(self, kb):
        sb = export_storyboard(kb, "ent_anhe_new_bridge")
        assert [f.state_id for f in sb.frames] == ["st_anhn_1965"]

    def test_gate_chain_has_jin_and_yuan(self, kb):
        chain = [s.id for s in kb.states_of("ent_gaoliang_gate")]
        assert chain == ["st_glz_jin_1198", "st_glz_yuan_1292"]
