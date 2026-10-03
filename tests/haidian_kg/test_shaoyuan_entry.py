"""
tests/haidian_kg/test_shaoyuan_entry.py
勺园·淑春园·未名湖词条入库测试（E20 知识库与事实本体入库）

史料基准（全部为 shaoyuan_video/research.md v1.1 + shaoyuan_video/gpt_review.txt 正式闸门裁决）：
- E01/E02: 勺园与和珅海淀赐园（淑春园）分立两个实体；和珅园是否即名「淑春园」
  必须建模为学术争议（何瑜·故宫博物院院刊2021 vs 郝黎·恭王府博物馆2026），
  BeliefAdoption 状态 = CONTESTED
- E03: 1784 赐和珅年份不得作为确证事实入库（CONTESTED，退出口播白名单）
- E04: 查抄和珅海淀园内房数严格为 1003 间（A10 原文「房一千零三间」），严禁写 1030
- E05: 楼台42所与亭台64所系不同查抄清单口径，严禁擅自加总
- E06: 吴彬《勺园祓禊图》绘于 1615 年（明万历乙卯），严禁写「己卯」
- 国保: 国务院第五批，编号 5-475，名单名「未名湖燕园建筑」
- 链名正名: 「和珅海淀赐园链」不再称「淑春园链」（E01 闸门）；马戛尔尼属弘雅园链不入和珅链（E11）
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from haidian_kg.calibration import shaoyuan as SY
from haidian_kg.calibration import bibliography as BIB
from haidian_kg.calibration.people import PEOPLE
from haidian_kg.calibration.digital_resources import RESOURCES
from haidian_kg.production_exports import (
    KnowledgeBase, audit_script, _numbers_in,
)
from haidian_kg.qa_gate import QAGate
from haidian_kg.ontology.epistemic import EpistemicStatus
from haidian_kg.ontology.video_contracts import AuditVerdict


# ==================================================================
# 入库闸门审计脚本与对抗样本
# ==================================================================

#: 正片级陈述：每句都必须与状态记录一致，不得 BLOCK
_GATE_SCRIPT = (
    "1612年前后米万钟在海淀清华园之东筑勺园又名风烟里。\n"
    "1763年淑春园之名已见于水田档案。\n"
    "1790年和珅在海淀的赐园俗称十笏园。\n"
    "1799年查抄十笏园得花园内房一千零三间。\n"
    "1799年查抄十笏园得花园内房一千零三十间。\n"
    "1801年弘雅园改作圆明园值日公所即集贤院。\n"
    "1860年集贤院毁后不复存在。\n"
    "1928年未名湖之名已见于燕大学生文字。\n"
    "2001年未名湖燕园建筑列入第五批全国重点文物保护单位。\n"
)

#: G7 对抗样本：真句必须通过，两句已知错误必须被拦下（假通过=闸门恒真）
ADV = (
    _GATE_SCRIPT,
    [
        ("1799年查抄十笏园得花园内房一千零三间", "通过"),
        ("1799年查抄十笏园得花园内房一千零三十间", "非通过"),
        ("1860年集贤院毁后不复存在", "非通过"),
    ]
)


@pytest.fixture(scope="module")
def kb():
    return KnowledgeBase(
        sources=SY.SOURCES, divisions=SY.DIVISIONS, facts=SY.FACTS,
        entities=SY.ENTITIES, states=SY.STATES, identities=SY.IDENTITIES,
        appellations=SY.APPELLATIONS, references=SY.REFERENCES,
        transformations=SY.TRANSFORMATIONS, propositions=SY.PROPOSITIONS,
        adoptions=SY.ADOPTIONS, aggregates=SY.AGGREGATES,
        people=PEOPLE, resources=RESOURCES)


def _prop(pid):
    for p in SY.PROPOSITIONS:
        if p.id == pid:
            return p
    raise AssertionError("proposition 不存在: %s" % pid)


def _adopt(pid):
    for a in SY.ADOPTIONS:
        if a.proposition_id == pid:
            return a
    raise AssertionError("adoption 不存在: %s" % pid)


def _fact(fid):
    for f in SY.FACTS:
        if f.id == fid:
            return f
    raise AssertionError("fact 不存在: %s" % fid)


def _ref(rid):
    for r in SY.REFERENCES:
        if r.id == rid:
            return r
    raise AssertionError("reference 不存在: %s" % rid)


def _dump_text():
    """把全模块自由文本拼成一锅，供红线负控扫描（严禁的写法一露头就 fail）"""
    parts = []
    for e in SY.ENTITIES:
        parts.append(e.canonical_label)
    for f in SY.FACTS:
        parts += [f.verbatim_quote, f.attested_string or "",
                  f.translator_note or ""]
    for st in SY.STATES:
        parts += [st.geometry or "", st.function or "",
                  st.material or "", st.admin_status or ""]
    for ap in SY.APPELLATIONS:
        parts += [ap.label] + list(ap.script_variants)
    for r in SY.REFERENCES:
        parts.append(r.provenance or "")
    for p in SY.PROPOSITIONS:
        parts += [p.statement, p.inference_method] + list(p.alternative_explanations)
    for a in SY.ADOPTIONS:
        parts.append(a.rationale)
    for t in SY.TRANSFORMATIONS:
        parts.append(t.resulting_condition or "")
    for i in SY.IDENTITIES:
        parts.append(" ".join(i.alternative_relations))
    return "\n".join(x for x in parts if x)


# ==================================================================
# 入库闸门
# ==================================================================

class TestShaoyuanEntryGate:
    def test_entry_passes_gate(self, kb):
        rep = QAGate("shaoyuan", kb, adversarial=ADV).run()
        assert rep.passed, rep.render()

    def test_adversarial_room_count_actually_blocked(self, kb):
        """负控制不得恒真：1030 假句的 BLOCK 必须真的发生"""
        results = audit_script(kb, "1799年查抄十笏园得花园内房一千零三十间。")
        assert results, "对抗样本未产生任何审计结果，判据可能恒真"
        assert results[0].verdict == AuditVerdict.BLOCK, \
            "1030 假数未被拦截（假通过）：%s" % results[0].reason

    def test_uses_unified_bibliography(self, kb):
        titles = [s.title for s in kb.sources.values()]
        assert len(titles) == len(set(titles)), "同一本书被建成多条：%s" % titles
        for s in SY.SOURCES:
            via = BIB.source_by_title(s.title)
            assert via is not None, "书源 %s 未挂统一书目表" % s.title
            assert via.id == s.id

    def test_all_facts_traceable(self, kb):
        div_ids = set(kb.divisions.keys())
        for f in kb.facts.values():
            assert f.division_id in div_ids, f.id

    def test_guobao_5475_written(self, kb):
        """国务院第五批：5-475「未名湖燕园建筑」——闸门硬锚"""
        st = kb.states["st_yj_1952"]
        assert "5-475" in st.geometry
        assert "未名湖燕園建築" in st.geometry
        f = _fact("tf_guobao_5475")
        assert "未名湖燕園建築" in f.verbatim_quote
        assert "国家文物重点保护单位" not in _dump_text(), \
            "规范名为「全国重点文物保护单位」（负控制15）"


# ==================================================================
# E01/E02：两个园址系统分立；名称争议建模为 CONTESTED
# ==================================================================

class TestE01TwoSystemsDistinct:
    def test_shaoyuan_vs_shuchunyuan_distinct_entities(self):
        """勺园与和珅海淀赐园（淑春园）必须分立为两个实体"""
        ids = [e.id for e in SY.ENTITIES]
        for ent_id in ("ent_shaoyuan", "ent_shuchunyuan",
                       "ent_yanjing_campus", "ent_weiming_lake"):
            assert ent_id in ids, "缺少计划要求的实体: %s" % ent_id

    def test_he_shen_garden_naming_dispute_modeled_as_contested(self):
        """E01/E02: 和珅园是否即淑春园必须建模为学术争议 CONTESTED"""
        adopt = _adopt("prop_shuchunyuan_he_shen_identity")
        assert adopt.status == EpistemicStatus.CONTESTED
        assert "何瑜" in adopt.rationale and "郝黎" in adopt.rationale
        ref = _ref("rr_shuchun")
        assert ref.status == EpistemicStatus.CONTESTED
        assert ref.referent_entity_id == "ent_shuchunyuan"

    def test_zhaolian_double_anchor_two_gardens(self):
        """昭梿卷九双锚：勺园（→集贤院）与和相十笏园分写两处——两链不同园的时人硬证"""
        assert "集賢院" in _fact("tf_xiaoting_jixianyuan").verbatim_quote
        assert "十笏園" in _fact("tf_xiaoting_shihu").verbatim_quote
        assert "成邸" in _fact("tf_xiaoting_shihu").verbatim_quote

    def test_two_chains_not_one_line_disproven(self):
        prop = _prop("prop_two_chains_one_line")
        adopt = _adopt("prop_two_chains_one_line")
        assert adopt.status == EpistemicStatus.DISPROVEN
        assert "tf_xiaoting_shihu" in adopt.refuting_fact_ids

    def test_appellations_never_bridge_the_two_chains(self):
        """勺园/淑春园两个名称绝不得指向对方的实体或未名湖（链间不得倒推）"""
        by_app = {}
        for r in SY.REFERENCES:
            by_app.setdefault(r.appellation_id, set()).add(r.referent_entity_id)
        assert by_app.get("app_shaoyuan") == {"ent_shaoyuan"}
        assert by_app.get("app_shuchun") == {"ent_shuchunyuan"}
        for app_id in ("app_shaoyuan", "app_shuchun"):
            assert "ent_weiming_lake" not in by_app.get(app_id, set()), \
                "「%s」不得指向未名湖实体（两链不混接）" % app_id

    def test_chain_renamed_he_shen_not_shuchun(self):
        """链名正名：「和珅海淀赐园」不再称「淑春园链」——实体规范标签必须带争议标记"""
        ent = [e for e in SY.ENTITIES if e.id == "ent_shuchunyuan"][0]
        assert "和珅" in ent.canonical_label
        assert "争议" in ent.canonical_label or "有争议" in ent.canonical_label


class TestE02Shuchun1763Contested:
    def test_1763_archive_fact_exists(self):
        f = _fact("tf_shuchun_shuitian_1763")
        assert "淑春園" in f.verbatim_quote
        assert "北樓門" in f.verbatim_quote
        assert "水田" in f.verbatim_quote

    def test_early_name_is_not_hard_evidence(self):
        """「淑春园名早于和珅」不得作为园属今北大的硬证（E02 撤销）"""
        prop = _prop("prop_shuchun_name_early_evidence")
        adopt = _adopt("prop_shuchun_name_early_evidence")
        assert adopt.status == EpistemicStatus.DISPROVEN
        assert "tf_shuchun_shuitian_1763" in adopt.refuting_fact_ids
        assert "争议" in prop.inference_method or "何瑜" in prop.inference_method


# ==================================================================
# E03：1784 赐园年份不得成为确证事实
# ==================================================================

class TestE03No1784AsConfirmedFact:
    def test_no_fact_carries_1784_grant(self):
        for f in SY.FACTS:
            assert "乾隆四十九年" not in f.verbatim_quote, f.id
            assert "1784" not in f.verbatim_quote, f.id

    def test_no_state_carries_1784(self):
        for st in SY.STATES:
            blob = "%s|%s" % (st.geometry or "", st.function or "")
            assert "1784" not in blob, st.id
            assert "乾隆四十九年" not in blob, st.id

    def test_grant_year_proposition_contested(self):
        adopt = _adopt("prop_grant_year_1784")
        assert adopt.status == EpistemicStatus.CONTESTED
        assert "1784" in adopt.rationale, "争议年份须在 rationale 里被明确记录"

    def test_state_uses_safe_wording(self):
        st = kb_state("ent_shuchunyuan", 1790)
        assert "乾隆后期" in st.geometry


def kb_state(entity_id, year):
    from haidian_kg.production_exports import KnowledgeBase as KB
    k = KB(sources=SY.SOURCES, divisions=SY.DIVISIONS, facts=SY.FACTS,
           entities=SY.ENTITIES, states=SY.STATES, identities=SY.IDENTITIES,
           appellations=SY.APPELLATIONS, references=SY.REFERENCES,
           transformations=SY.TRANSFORMATIONS, propositions=SY.PROPOSITIONS,
           adoptions=SY.ADOPTIONS, aggregates=SY.AGGREGATES,
           people=PEOPLE, resources=RESOURCES)
    st = k.state_at(entity_id, year)
    assert st is not None, "%s @%s 无状态" % (entity_id, year)
    return st


# ==================================================================
# E04：房数严格 1003，严禁 1030
# ==================================================================

class TestE04RoomCount1003:
    def test_house_count_is_1003_not_1030(self):
        f = _fact("tf_hsnd_fang1003")
        assert "一千零三間" in f.verbatim_quote
        assert "1030" not in f.verbatim_quote
        assert "遊廊樓亭共房三百五十七間" in f.verbatim_quote

    def test_1003_is_canonical_reading(self):
        assert 1003 in _numbers_in("房一千零三間")

    def test_1030_banned_everywhere(self):
        dump = _dump_text()
        assert "1030" not in dump
        assert "一千零三十" not in dump

    def test_fallacy_modeled_as_disproven(self):
        adopt = _adopt("prop_room_count_1030")
        assert adopt.status == EpistemicStatus.DISPROVEN
        assert "tf_hsnd_fang1003" in adopt.refuting_fact_ids


# ==================================================================
# E05：不同查抄清单口径，严禁加总
# ==================================================================

class TestE05SeparateInventories:
    def test_two_gardens_two_facts(self):
        f1 = _fact("tf_yongansi_garden1")
        f2 = _fact("tf_yongansi_garden2")
        assert f1.id != f2.id
        assert "樓臺四十二所" in f1.verbatim_quote
        # E05 裁决：原文作「亭臺六十四所」，不得写成「楼台64」
        assert "亭臺六十四所" in f2.verbatim_quote

    def test_no_single_fact_mixes_the_two_counts(self):
        for f in SY.FACTS:
            both = ("四十二" in f.verbatim_quote and "六十四" in f.verbatim_quote)
            assert not both, "单条引文混装两个查抄口径: %s" % f.id

    def test_counts_are_numerically_disjoint(self):
        n1 = {n for n in _numbers_in(_fact("tf_yongansi_garden1").verbatim_quote) if n >= 10}
        n2 = {n for n in _numbers_in(_fact("tf_yongansi_garden2").verbatim_quote) if n >= 10}
        assert 42 in n1 and 64 in n2
        assert not (n1 & n2), "两条清单数字集有交集，无法证明口径分立：%s" % (n1 & n2)

    def test_summing_banned_in_module_text(self):
        dump = _dump_text()
        assert "一百零六" not in dump, "楼台42+亭台64 擅自加总"
        assert "一百六十" not in dump

    def test_fallacy_modeled_as_disproven(self):
        adopt = _adopt("prop_inventory_sum")
        assert adopt.status == EpistemicStatus.DISPROVEN
        for fid in ("tf_yongansi_garden1", "tf_yongansi_garden2", "tf_hsnd_fang1003"):
            assert fid in adopt.refuting_fact_ids


# ==================================================================
# E06：吴彬卷 1615 乙卯，严禁「己卯」
# ==================================================================

class TestE06WuBinYimao1615:
    def test_wu_bin_inscription_emended_to_yimao(self):
        f = _fact("tf_wubian_tiba")
        # 底本作「已」（形讹），〔乙〕为校勘字（仿 cishousi 讹文体例，E06 两可读法之一）
        assert "已〔乙〕卯" in f.verbatim_quote
        assert "乙卯" in (f.translator_note or "")
        assert f.source_year.gregorian.year == 1615

    def test_jimao_never_appears(self):
        assert "己卯" not in _dump_text(), "「己卯」是另一干支，绝非「乙卯」异写（E06）"

    def test_mi_wanzhong_dingsi_1617(self):
        f = _fact("tf_miwanzhong_tiba")
        assert "丁巳三月寫" in f.verbatim_quote
        assert f.source_year.gregorian.year == 1617

    def test_jimao_fallacy_disproven(self):
        adopt = _adopt("prop_wubian_jimao")
        assert adopt.status == EpistemicStatus.DISPROVEN
        assert "tf_wubian_tiba" in adopt.refuting_fact_ids


# ==================================================================
# 负控制与归因纪律（E07/E08/E09/E10/E11 + 研究档案负控制清单）
# ==================================================================

class TestNegativeControls:
    def test_weiminghu_is_not_shaoyuan_site(self):
        """负控制1：未名湖≠米万钟勺园故址"""
        adopt = _adopt("prop_weiminghu_shaoyuan_zhi")
        assert adopt.status == EpistemicStatus.DISPROVEN
        assert "tf_rxjwkc79_bukao" in adopt.refuting_fact_ids

    def test_shaoyuan_destruction_cause_unattributed(self):
        """负控制7：勺园毁因无文据，不得归因明末战乱"""
        adopt = _adopt("prop_sy_destruction_cause")
        assert adopt.status == EpistemicStatus.DISPROVEN

    def test_qianmu_not_the_creator(self):
        """负控制5/E09：钱穆不是「未名湖」最初命名者；1928 已出现"""
        adopt = _adopt("prop_qianmu_created_name")
        assert adopt.status == EpistemicStatus.DISPROVEN
        assert "1928" in adopt.rationale

    def test_1931_vote_was_for_buildings(self):
        """E08：1931-05-02 是燕大建筑命名投票，不是湖名投票"""
        adopt = _adopt("prop_1931_lake_vote")
        assert adopt.status == EpistemicStatus.DISPROVEN
        assert "建筑" in _prop("prop_1931_lake_vote").inference_method

    def test_lake_frequency_order_needs_fenghu(self):
        """E07：1929—1931 频次为 枫湖>无名湖>睿湖>未名湖——漏枫湖即假排序"""
        adopt = _adopt("prop_lake_freq_three_names")
        assert adopt.status == EpistemicStatus.DISPROVEN
        assert "枫湖" in adopt.rationale
        labels = [a.label for a in SY.APPELLATIONS]
        for name in ("无名湖", "睿湖", "枫湖"):
            assert name in labels, "学生时代并用湖名缺 %s" % name

    def test_shifang_is_not_a_crime_exhibit(self):
        """负控制2：二十罪第十三条原文无「石舫」，「僭侈逾制→石舫」是现代引申"""
        assert "石舫" not in _fact("tf_zui13").verbatim_quote
        adopt = _adopt("prop_shifang_weizhi_zuizheng")
        assert adopt.status == EpistemicStatus.DISPROVEN
        assert "tf_zui13" in adopt.refuting_fact_ids

    def test_shuchun_lake_identity_not_hard_fact(self):
        """「未名湖=淑春园故湖」降为现代口径层 CONTESTED，不作硬事实（E01 框架）"""
        adopt = _adopt("prop_weiminghu_shuchun_lianghu")
        assert adopt.status == EpistemicStatus.CONTESTED

    def test_majierni_belongs_to_hongya_chain(self):
        """E11：马戛尔尼属勺园—弘雅园链，严禁在和珅园链实体状态中出现"""
        adopt = _adopt("prop_majierni_hongya")
        assert adopt.status == EpistemicStatus.CONTESTED
        for st in SY.STATES:
            if st.entity_id == "ent_shuchunyuan":
                blob = "%s|%s" % (st.geometry or "", st.function or "")
                assert "马戛尔尼" not in blob, st.id

    def test_kangxi_jihana_removed(self):
        """E10：「康熙赐积哈纳」删除——积哈纳为乾隆朝人物，官网口径内部矛盾"""
        adopt = _adopt("prop_kangxi_jihana")
        assert adopt.status == EpistemicStatus.DISPROVEN
        assert "积哈纳" in adopt.rationale

    def test_1612_1614_not_hard_dates(self):
        """E12：建园年份挂现代口径，必须带「约」"""
        adopt = _adopt("prop_1612_hard_dates")
        assert adopt.status == EpistemicStatus.DISPROVEN
        st = kb_state("ent_shaoyuan", 1613)
        assert "约1612" in st.geometry

    def test_yixuan_hearsay_prefixes_preserved(self):
        """传闻层自注「傳聞」「聞」必须照录，防绝对化（E9 分层纪律）"""
        assert "傳聞" in _fact("tf_yixuan_xu").verbatim_quote
        assert "聞" in _fact("tf_yixuan_guyu").verbatim_quote

    def test_shiping_from_yuanmingyuan_not_heshen(self):
        """四-4：石屏四条＝圆明园夹镜鸣琴联刻移入，非和珅物"""
        f = _fact("tf_shiping_shi")
        assert "夾鏡" in f.verbatim_quote
        st = kb_state("ent_shiping", 1980)
        assert "移入" in st.geometry and "非和珅" in st.geometry


# ==================================================================
# 状态链与查询
# ==================================================================

class TestStateChain:
    def test_shaoyuan_chain_states(self):
        assert kb_state("ent_shaoyuan", 1620).id == "st_sy_ming"
        assert kb_state("ent_shaoyuan", 1783).id == "st_sy_fei"
        assert kb_state("ent_shaoyuan", 2000).id == "st_sy_1981"

    def test_hongya_jixian_states(self):
        assert kb_state("ent_hongya_jixian", 1750).id == "st_hy_qianqi"
        assert kb_state("ent_hongya_jixian", 1810).id == "st_hy_jixianyuan"
        assert kb_state("ent_hongya_jixian", 1870).id == "st_hy_hui"

    def test_he_shen_garden_states(self):
        assert kb_state("ent_shuchunyuan", 1765).id == "st_sc_1763"
        assert kb_state("ent_shuchunyuan", 1790).id == "st_sc_qianlong"
        assert kb_state("ent_shuchunyuan", 1799).id == "st_sc_1799"
        assert kb_state("ent_shuchunyuan", 1845).id == "st_sc_ruiwang"
        assert kb_state("ent_shuchunyuan", 1870).id == "st_sc_1860"
        assert kb_state("ent_shuchunyuan", 1940).id == "st_sc_1920"

    def test_weiming_lake_state(self):
        st = kb_state("ent_weiming_lake", 1960)
        assert st.id == "st_wm_1926"
        assert "1928" in st.geometry

    def test_1799_boundary_takes_latest_state(self):
        st = kb_state("ent_shuchunyuan", 1799)
        assert "一千零三間" in (st.geometry or ""), "1799 边界必须落到查抄状态"


# ==================================================================
# 书目与转引纪律
# ==================================================================

class TestBibliographyDiscipline:
    def test_transit_quotes_hang_on_rixia_juan79(self):
        """《长安客话》原书未直核：A2/A5 引文必须挂日下旧闻考卷79 转录层（quoted_via）"""
        f = _fact("tf_cck_xinzhu")
        assert f.division_id == "div_rxjwkc79_shaoyuan"
        assert "转引" in (f.translator_note or "")
        f5 = _fact("tf_cck_naming")
        assert f5.division_id == "div_rxjwkc79_shaoyuan"

    def test_yuanzhao_and_anzhao_layers_separated(self):
        """卷79 原引层与「臣等谨按」按语层必须分立篇卷（禁跨层取证）"""
        assert _fact("tf_cck_xinzhu").division_id != _fact("tf_rxjwkc79_bukao").division_id
        assert _fact("tf_rxjwkc79_bukao").division_id == "div_rxjwkc79_anzhao"

    def test_new_primary_sources_registered(self):
        for title in ("清代和珅档案史料", "庸庵笔记", "九思堂诗稿",
                      "钦定大清会典事例", "北京大学公开校史与校园文物资料",
                      "国务院公布全国重点文物保护单位名单"):
            s = BIB.source_by_title(title)
            assert s is not None, "缺少新增一手文献: %s" % title

    def test_huidian_shili_not_merged_with_huidian(self):
        """《钦定大清会典》与《钦定大清会典事例》是两部书，不得并档"""
        a = BIB.source_by_title("钦定大清会典")
        b = BIB.source_by_title("会典事例")
        assert a is not None and b is not None and a.id != b.id

    def test_heshen_quanandang_aliases_into_compilation(self):
        s = BIB.source_by_title("和珅犯罪全案档")
        assert s is not None and s.id == "src_qingdai_heshen_dangshi"

    def test_sw_chain_identity_contested(self):
        dia = [i for i in SY.IDENTITIES if i.id == "dia_sw_chain"][0]
        assert dia.status == EpistemicStatus.CONTESTED
        assert dia.alternative_relations, "争议身份必须列出其他解释"
        assert dia.subject_entity_ids == ["ent_shaoyuan", "ent_hongya_jixian"]
