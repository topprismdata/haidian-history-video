"""
tests/haidian_kg/test_sanshiwuyuan.py
三山五园主线词条入库测试（香山静宜园 / 万寿山清漪园颐和园 / 静明园玉泉山 /
畅春园 / 三山五园概念）

史料基准（底本=维基文库四库本 raw wikitext + holdout_v2_pilot_draft 本地快照，
全部引文已逐条按底本子串校验）：
- 静宜园：乾隆乙丑(1745)秋兴工、丙寅(1746)春园成、御题二十八景（记+诗双源）
- 清漪园：乾隆十五年(1750)命名万寿山/改昆明湖，园成于辛巳(1761)——三个年份严禁混一
- 静明园：澄心园(1680)→静明园(1692)；金代行宫有金史明文、芙蓉殿「旧传…无考」
- 畅春园：本李伟清华园故址（pilot 卷76/卷79），康熙听政之所；建成年份诸说并存
- 恩佑寺：世宗为圣祖荐福建（不是乾隆为雍正）；恩慕寺：乾隆四十二年(1777)
- 三山五园：清代官方只有「三山」建制，咸丰十年「五园三山」最早连称，
  光绪间舆图始题「三山五园」，固定语序为后世概括——标现代研究框架
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from haidian_kg.calibration import sanshiwuyuan as S
from haidian_kg.calibration import yuanmingyuan as Y
from haidian_kg.calibration.people import PEOPLE
from haidian_kg.calibration.digital_resources import RESOURCES
from haidian_kg.production_exports import KnowledgeBase, audit_script
from haidian_kg.qa_gate import QAGate
from haidian_kg.ontology.epistemic import EpistemicStatus
from haidian_kg.ontology.spatiotemporal import IdentityRelation

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
PILOT = os.path.join(REPO, "haidian_kg", "evaluation",
                     "holdout_v2_pilot_draft.jsonl")

#: 逐句期望的对抗样本：真陈述 + 年代错置（静宜园雍正元年尚不存在）
ADV = ("乾隆十一年静宜园御题二十八景。雍正元年静宜园二十八景已经建成。",
       [("乾隆十一年静宜园御题二十八景", "通过"),
        ("雍正元年静宜园二十八景已经建成", "非通过")])


@pytest.fixture(scope="module")
def kb():
    return KnowledgeBase(
        sources=S.SOURCES, divisions=S.DIVISIONS, facts=S.FACTS,
        entities=S.ENTITIES, states=S.STATES, identities=S.IDENTITIES,
        appellations=S.APPELLATIONS, references=S.REFERENCES,
        transformations=S.TRANSFORMATIONS, propositions=S.PROPOSITIONS,
        adoptions=S.ADOPTIONS, aggregates=S.AGGREGATES,
        people=PEOPLE, resources=RESOURCES)


@pytest.fixture(scope="module")
def pilot_text():
    """卷76/卷79 本地快照全文（引文本地化纪律的机器回查底本）"""
    texts = {"76": [], "79": []}
    with open(PILOT, encoding="utf-8") as f:
        for line in f:
            o = json.loads(line)
            seg = o["segment_id"]
            if seg.startswith("pilot_rixia_juan076:"):
                texts["76"].append(o["text"])
            elif seg.startswith("pilot_rixia_juan079:"):
                texts["79"].append(o["text"])
    return {k: "".join(v) for k, v in texts.items()}


# ==================================================================
# 入库闸门
# ==================================================================

class TestSanshiwuyuanEntryGate:
    def test_entry_passes_gate(self, kb):
        rep = QAGate("sanshiwuyuan", kb, adversarial=ADV).run()
        assert rep.passed, rep.render()

    def test_uses_unified_bibliography(self, kb):
        titles = [s.title for s in kb.sources.values()]
        assert len(titles) == len(set(titles)), "同一本书被建成多条：%s" % titles
        # 模块内新建书目不得与中央书目表重名（经 source_by_title 复用的除外）
        from haidian_kg.calibration.bibliography import BIBLIOGRAPHY, source_by_title
        central = {s.title for s in BIBLIOGRAPHY}
        reused = {source_by_title(t).title for t in titles if source_by_title(t)}
        in_module_new = set(titles) - reused
        assert not (in_module_new & central), \
            "模块内新建书目与中央书目表重名：%s" % (in_module_new & central)

    def test_all_facts_traceable(self, kb):
        div_ids = set(kb.divisions.keys())
        for f in kb.facts.values():
            assert f.division_id in div_ids, f.id


# ==================================================================
# 关键实体与 id 冲突
# ==================================================================

class TestKeyEntities:
    def test_core_gardens_and_mountains_exist(self, kb):
        expect = {
            "ent_xiangshan": "香山",
            "ent_jingyiyuan": "静宜园",
            "ent_wanshoushan": "万寿山（旧称瓮山）",
            "ent_qingyiyuan": "颐和园（前身清漪园）",
            "ent_kunminghu": "昆明湖（旧称西湖）",
            "ent_yuquanshan": "玉泉山",
            "ent_jingmingyuan": "静明园（玉泉山行宫苑）",
            "ent_changchunyuan_kangxi": "畅春园",
            "ent_enyousi": "恩佑寺",
            "ent_enmusi": "恩慕寺",
            "ent_sanshiwuyuan": "三山五园（京西皇家园林群概念合称）",
        }
        for eid, label in expect.items():
            assert eid in kb.entities, eid
            assert kb.entities[eid].canonical_label == label, eid

    def test_no_id_conflict_with_yuanmingyuan_module(self):
        mine = {e.id for e in S.ENTITIES}
        theirs = {e.id for e in Y.ENTITIES}
        assert not (mine & theirs), "实体 id 冲突：%s" % (mine & theirs)

    def test_changchunyuan_disambiguation(self, kb):
        """畅春园拼音与长春园同形，必须用 _kangxi 后缀且不得指向同一实体"""
        assert "ent_changchunyuan" not in kb.entities  # 长春园在 yuanmingyuan 模块
        assert kb.entities["ent_changchunyuan_kangxi"].canonical_label == "畅春园"

    def test_entities_carry_no_visual_attributes(self, kb):
        for e in kb.entities.values():
            assert not ({"geometry", "material", "function"} & set(e.model_fields_set)), e.id


# ==================================================================
# 乾隆年代数字必须双源
# ==================================================================

class TestQianlongDatesDualSource:
    def test_jingyiyuan_1745_1746_two_series(self, kb):
        """1745兴工/1746成园：静宜园记 + 乾隆十一年诗系，两系并存"""
        assert "乙丑" in kb.facts["tf_jyy_ji_1745"].verbatim_quote
        assert "丙寅" in kb.facts["tf_jyy_1746"].verbatim_quote
        assert "二十有八" in kb.facts["tf_jyy_28jing"].verbatim_quote
        # 1745/1746 分属两个状态（建置期与成园期），不得合并为一个年份口径
        assert kb.state_at("ent_jingyiyuan", 1745).id == "st_jyy_1745"
        assert kb.state_at("ent_jingyiyuan", 1746).id == "st_jyy_1746"
        assert kb.state_at("ent_jingyiyuan", 1744) is None

    def test_qingyiyuan_three_year_chain(self, kb):
        """1750命名 / 1751建寺语境 / 1761园成——三个年份分挂，不混写一年"""
        assert kb.facts["tf_qyy_1750"].verbatim_quote.startswith("今上乾隆十五年")
        assert "辛巳" in kb.facts["tf_qyy_1761"].verbatim_quote
        assert kb.state_at("ent_qingyiyuan", 1749) is None
        assert kb.state_at("ent_qingyiyuan", 1750).id == "st_qyy_1750"
        assert kb.state_at("ent_qingyiyuan", 1761).id == "st_qyy_1761"

    def test_kunminghu_naming_dual_source(self, kb):
        """昆明湖命名双源：卷84臣等谨按 + 御制记（湖既成因赐名）"""
        assert "易名曰昆明湖" in kb.facts["tf_qyy_1750"].verbatim_quote
        assert "賜名萬壽山昆明湖" in kb.facts["tf_kmh_ciming"].verbatim_quote
        # 汉武典故是乾隆自述用典，不是汉武帝史实
        q = kb.facts["tf_kmh_hanwu"].verbatim_quote
        assert "漢武" in q and "唐堯" in q

    def test_g5_no_duplicate_begin_years(self, kb):
        by_entity = {}
        for s in kb.states.values():
            by_entity.setdefault(s.entity_id, []).append(s)
        for eid, states in by_entity.items():
            years = [s.time_span.begin.gregorian.year for s in states
                     if s.time_span.begin and s.time_span.begin.gregorian]
            assert len(years) == len(set(years)), "%s 同起始年重复状态" % eid


# ==================================================================
# holdout 缺口面：本批目标字面必须能从字形表命中
# ==================================================================

HOLDOUT_FACES = [
    ("香山", "ent_xiangshan"),
    ("静宜园", "ent_jingyiyuan"),
    ("香山公园", "ent_jingyiyuan"),
    ("万寿山", "ent_wanshoushan"),
    ("瓮山", "ent_wanshoushan"),
    ("清漪园", "ent_qingyiyuan"),
    ("颐和园", "ent_qingyiyuan"),
    ("昆明湖", "ent_kunminghu"),
    ("西湖", "ent_kunminghu"),
    ("玉泉山", "ent_yuquanshan"),
    ("静明园", "ent_jingmingyuan"),
    ("澄心园", "ent_jingmingyuan"),
    ("畅春园", "ent_changchunyuan_kangxi"),
    ("恩佑寺", "ent_enyousi"),
    ("恩慕寺", "ent_enmusi"),
    ("三山五园", "ent_sanshiwuyuan"),
    ("五园三山", "ent_sanshiwuyuan"),
    ("万寿山后湖", "ent_houxihe"),
    ("后溪河", "ent_houxihe"),
]


class TestHoldoutGapFaces:
    @pytest.mark.parametrize("label,ent", HOLDOUT_FACES)
    def test_label_resolves_to_entity(self, kb, label, ent):
        apps = [a for a in kb.appellations.values() if a.label == label]
        assert apps, "缺口面未挂名称：%s" % label
        refs = [r for r in kb.references if r.appellation_id == apps[0].id]
        assert refs, "名称无指称断言：%s" % label
        assert any(r.referent_entity_id == ent for r in refs), \
            "%s 应指 %s" % (label, ent)

    def test_yiheyuan_clean_lake_renamed_1888(self, kb):
        """清漪园→颐和园改名链：同一实体两个名段"""
        ref_qyy = [r for r in kb.references if r.appellation_id == "app_qyy"][0]
        ref_yhy = [r for r in kb.references if r.appellation_id == "app_yhy"][0]
        assert ref_qyy.referent_entity_id == ref_yhy.referent_entity_id
        assert ref_qyy.referent_entity_id == "ent_qingyiyuan"


# ==================================================================
# 畅春园：清华园故址 vs 澄心园讹说（pilot 本地快照回查）
# ==================================================================

class TestChangchunyuanFoundation:
    def test_pilot_quotes_are_local_substrings(self, kb, pilot_text):
        """卷76/卷79 全部书证必须能逐字回到本地 pilot 快照（防底本漂移）"""
        ju76_quotes = ["tf_ccy_ce", "tf_ccy_liwei", "tf_ccy_ji_yizhi",
                       "tf_ccy_ji_gui", "tf_ccy_tingzheng", "tf_ccy_taihou",
                       "tf_eyou_guihong", "tf_eyou_ce", "tf_eyou_yongzheng",
                       "tf_emusi_1777"]
        ju79_quotes = ["tf_qhy_guzhi", "tf_qhy_yanshuanglou"]
        for fid in ju76_quotes:
            assert kb.facts[fid].verbatim_quote in pilot_text["76"], fid
        for fid in ju79_quotes:
            assert kb.facts[fid].verbatim_quote in pilot_text["79"], fid

    def test_chengxinyuan_points_to_jingmingyuan_not_ccy(self, kb):
        """澄心园是玉泉山静明园前身，绝不指向畅春园"""
        ref = [r for r in kb.references if r.appellation_id == "app_cxy"][0]
        assert ref.referent_entity_id == "ent_jingmingyuan"

    def test_chengxin_chain_marked_disproven(self, kb):
        ad = kb.adoptions["prop_ccy_not_chengxin"]
        assert ad.status == EpistemicStatus.DISPROVEN
        assert "tf_ccy_liwei" in ad.refuting_fact_ids

    def test_qinghua_guzhi_verified(self, kb):
        ad = kb.adoptions["prop_ccy_qinghua_guzhi"]
        assert ad.status == EpistemicStatus.VERIFIED
        assert "清华园" in kb.propositions["prop_ccy_qinghua_guzhi"].statement

    def test_ccy_open_begin_state(self, kb):
        """建成年份诸说并存 → 康熙朝状态用开放起始，1700 年可命中"""
        st = kb.state_at("ent_changchunyuan_kangxi", 1700)
        assert st is not None and st.id == "st_ccy_kangxi"
        assert st.time_span.open_begin is True and st.time_span.begin is None


# ==================================================================
# 恩佑寺/恩慕寺：建者与年份分层
# ==================================================================

class TestEnusiEnmusi:
    def test_enusi_built_by_yongzheng_for_shengzu(self, kb):
        p = kb.propositions["prop_eyou_built_by_yongzheng"]
        ad = kb.adoptions["prop_eyou_built_by_yongzheng"]
        assert ad.status == EpistemicStatus.VERIFIED
        assert "世宗" in p.statement and "圣祖" in p.statement

    def test_no_attribution_to_qianlong_for_yongzheng(self, kb):
        """负向钉：恩佑寺建者必须是世宗/雍正侧表述；
        「乾隆为雍正荐福」者系安佑宫，必须以纠正句形式出现"""
        hits = [p for p in kb.propositions.values() if "恩佑寺" in p.statement]
        assert hits
        for p in hits:
            assert ("世宗" in p.statement or "雍正" in p.statement), p.id
        assert any("安佑宫" in p.statement for p in hits), \
            "缺「乾隆为雍正荐福者系安佑宫」的混淆纠正句"

    def test_enmusi_1777(self, kb):
        st = kb.state_at("ent_enmusi", 1777)
        assert st is not None and st.id == "st_emsi_1777"
        assert kb.state_at("ent_enmusi", 1776) is None


# ==================================================================
# 三山五园概念：聚合而非同指
# ==================================================================

class TestSanshiwuyuanConcept:
    def test_aggregate_members(self, kb):
        agg = kb.aggregates["agg_sanshiwuyuan"]
        assert set(agg.member_entity_ids) == {
            "ent_changchunyuan_kangxi", "ent_yuanmingyuan", "ent_qingyiyuan",
            "ent_jingmingyuan", "ent_jingyiyuan"}
        assert agg.time_span.begin.gregorian.year == 1750

    def test_cross_module_member_matches_yuanmingyuan_module(self):
        """成员引用的 ent_yuanmingyuan 必须是 yuanmingyuan.py 的真实实体 id"""
        assert any(e.id == "ent_yuanmingyuan" for e in Y.ENTITIES)

    def test_sanshan_aggregate(self, kb):
        agg = kb.aggregates["agg_sanshan"]
        assert set(agg.member_entity_ids) == {
            "ent_wanshoushan", "ent_yuquanshan", "ent_xiangshan"}

    def test_no_identity_assertion_on_concept(self, kb):
        """成员关系非同指：概念实体不得挂任何 identity 断言"""
        for d in kb.identities:
            assert "ent_sanshiwuyuan" not in d.subject_entity_ids

    def test_modern_framework_marked(self, kb):
        ad = kb.adoptions["prop_sswy_modern_framework"]
        assert ad.status == EpistemicStatus.VERIFIED
        p = kb.propositions["prop_sswy_modern_framework"]
        assert "后世概括" in p.statement
        assert len(p.alternative_explanations) >= 2, "学界异说须并列"


# ==================================================================
# 「后湖」两指消歧 + 翠微山负向钉
# ==================================================================

class TestHouhuAndCuiwei:
    def test_houhu_bare_name_not_appellation(self, kb):
        """GPT审3-7：裸名「后湖」两指（静明园内后湖 卷85 / 万寿山后溪河带
        今通称），不得作为 ent_houxihe 的 appellation——防名称链揉合两实体。
        限定名「万寿山后湖」(app_hxh_houhu) 保留，标 UNSUBSTANTIATED。"""
        assert "app_houhu" not in set(kb.appellations), "裸名「后湖」不得复为 appellation"
        refs = [r for r in kb.references if r.appellation_id == "app_houhu"]
        assert refs == [], "裸名「后湖」不得挂 ent_houxihe 指称断言"
        ref = [r for r in kb.references if r.appellation_id == "app_hxh_houhu"][0]
        assert ref.status == EpistemicStatus.UNSUBSTANTIATED
        assert ref.provenance
        assert ref.referent_entity_id == "ent_houxihe"

    def test_cuiwei_mountain_is_not_xiangshan_alias(self, kb):
        """翠微山非香山别名（翠微山=平坡山，今石景山八大处）；
        负向钉：不得以任何名称把翠微山挂到香山"""
        for a in kb.appellations.values():
            assert "翠微山" not in a.label, a.id
        for r in kb.references:
            if r.referent_entity_id == "ent_xiangshan":
                assert r.appellation_id != "app_cuiwei", r.id

    def test_jmy_houhu_ambiguity_recorded(self, kb):
        ad = kb.adoptions["prop_houhu_ambiguity"]
        assert ad.status == EpistemicStatus.CONTESTED


# ==================================================================
# 现状单独核查（最高危项）
# ==================================================================

class TestCurrentStatus:
    def test_xiangshan_park_open(self, kb):
        st = kb.state_at("ent_xiangshan", 2020)
        assert st is not None and "香山公园" in st.function

    def test_yiheyuan_park_open(self, kb):
        st = kb.state_at("ent_qingyiyuan", 2020)
        assert st is not None and "颐和园" in st.function

    def test_yuquanshan_closed(self, kb):
        st = kb.state_at("ent_jingmingyuan", 2020)
        assert st is not None and "不对外开放" in st.function

    def test_ccy_only_two_gates_left(self, kb):
        st = kb.state_at("ent_changchunyuan_kangxi", 2020)
        assert st is not None and "两座山门" in st.geometry


# ==================================================================
# 审计与负控制
# ==================================================================

class TestAuditAndNegativeControl:
    def test_correct_1746_claim_passes(self, kb):
        r = audit_script(kb, "乾隆十一年静宜园御题二十八景。")
        assert r[0].verdict.value == "通过", r[0].reason

    def test_chronology_inversion_blocked(self, kb):
        r = audit_script(kb, "雍正元年静宜园二十八景已经建成。")
        assert r[0].verdict.value != "通过"

    def test_yiheyuan_before_1888_unresolvable_as_yiheyuan(self, kb):
        """1870 年说「颐和园」——名称指称窗口未开，不得判通过"""
        r = audit_script(kb, "颐和园在1870年已是皇家园林。")
        assert r[0].verdict.value != "通过"

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
        kb2.facts.pop("tf_jyy_1746")
        rep = QAGate("sanshiwuyuan-broken", kb2, adversarial=ADV).run()
        assert not rep.passed, "抽掉成园书证后闸门仍通过 = 闸门恒真"

    def test_identity_rename_same_continuant(self, kb):
        ids = [d for d in kb.identities if d.id == "dia_qyy_yhy_same"]
        assert len(ids) == 1
        assert ids[0].relation == IdentityRelation.SAME_CONTINUANT
        assert ids[0].status == EpistemicStatus.VERIFIED
