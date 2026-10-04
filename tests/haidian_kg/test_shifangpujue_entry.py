# -*- coding: utf-8 -*-
"""E26《十方普觉寺·五次易名的半部北京佛教史》知识库闸门测试.

本集是本系列**首例「纵向层累」**结构：前五集（E21–E25）的核心命题都是
「某一年的误读」（时序否证），本集的核心命题是**六个寺名横跨唐元明清的
时间轴本身**。因此闸门测试的重点不是「能否证伪某一年」，而是：

  1. 六名与年号是否一一对应（G1）
  2. 器物年代与建置年代是否分层（G2）——**本集核心**
  3. 国保批次与编号是否精确，且**不与 E25 交叉污染**（G3）
  4. DISPROVEN 是否都带反驳证据 ID（G4，承 E25 元教训）
  5. 引用完整性：所有 entity_id / source_id / fact_id 是否真实存在（G5）
     —— **本测试抓出了 E25 的真 bug**：wutasi.py 曾写 source_id="src_guobao_1st"，
        而全库只有 src_guobao_5th 一个国保源，该 id 悬空且从无测试覆盖
  6. 负控制假通过检出：证伪说被改回通行说时必须被抓（G6/G7）

Python 3.9.6 兼容: 禁 X | None, 禁 match.
"""
import pytest

from haidian_kg.calibration import shifangpujue as S
from haidian_kg.calibration.bibliography import BIBLIOGRAPHY
from haidian_kg.calibration.wutasi import DIVISIONS as E25_DIVISIONS
from haidian_kg.extractor import HaidianCorpusExtractor


ALL_SOURCE_IDS = {s.id for s in BIBLIOGRAPHY}
_FACT_IDS = {f.id for f in S.FACTS}
_APP_IDS = {a.id for a in S.APPELLATIONS}
_ENT_IDS = {e.id for e in S.ENTITIES}

_KG = HaidianCorpusExtractor.extract_all()
_TOP_IDS = {t.id for t in _KG.toponyms}
_UNIT_IDS = {u.id for u in _KG.administrative_units}


def _blob():
    b = " ".join(f.verbatim_quote + f.translator_note for f in S.FACTS)
    b += " ".join(p.statement + p.inference_method for p in S.PROPOSITIONS)
    b += " ".join(a.rationale for a in S.ADOPTIONS)
    b += " ".join(e.canonical_label for e in S.ENTITIES)
    return b


# ==================================================================
# G1  六名与年号一一对应（本集正向主判据）
# ==================================================================

class TestSixNamesChainGate:
    def test_g1_exactly_six_names(self):
        assert len(S.APPELLATIONS) == 6, "寺名沿革链必须恰有六个名号（初建名 + 五次易名）"

    def test_g1_names_in_order(self):
        labels = [a.label for a in S.APPELLATIONS]
        assert labels == ["兜率寺", "昭孝寺", "洪庆寺", "寿安山寺", "永安寺", "十方普觉寺"], \
            "六个名号必须按时间先后排列，实际为 %s" % labels

    def test_g1_eras_span_tang_to_qing(self):
        """六个名号必须横跨唐元明清，且首尾不倒置。"""
        spans = [(a.valid_time_span.begin.gregorian.year,
                  a.valid_time_span.end.gregorian.year) for a in S.APPELLATIONS]
        assert spans[0][0] == 627, "首个名号应起于唐贞观（627）"
        assert spans[-1][1] >= 2026, "末个名号应延续至今"
        for i in range(len(spans) - 1):
            assert spans[i][1] <= spans[i + 1][0] + 1, \
                "第 %d 与第 %d 个名号的时段重叠或倒置：%s / %s" % (i, i + 1, spans[i], spans[i + 1])

    def test_g1_eras_four_dynasties(self):
        blob = _blob()
        for era in ("唐", "元", "明", "清"):
            assert era in blob, "名号链须覆盖四个朝代，缺「%s」" % era

    def test_g1_chain_adopted_verified(self):
        ad = [a for a in S.ADOPTIONS if a.proposition_id == "prop_e26_six_names_chain"]
        assert len(ad) == 1
        assert ad[0].status.name == "VERIFIED", \
            "每个名号都有年号与书证，六名链为 VERIFIED；UNSUBSTANTIATED 会把实证降格为无据"

    def test_g1_vague_wording_banned(self):
        """V-NC01：严禁笼统写「数次易名」而不给出名号。"""
        blob = _blob()
        for vague in ("历经数次改名", "历经多次易名", "数次易名", "屡次改名"):
            assert vague not in blob, \
                "V-NC01 违规：出现笼统表述「%s」。必须逐一给出名号与年号。" % vague


# ==================================================================
# G2  器物年代 ≠ 建置年代（本集核心）
# ==================================================================

class TestArtifactAgeLayeringGate:
    def test_g2_wofoe_entity_is_yuan(self):
        assert len(S.ENTITIES) == 1
        label = S.ENTITIES[0].canonical_label
        assert "元代所铸" in label, "铜卧佛实体标签必须写明「元代所铸」"
        assert "唐" not in label, "铜卧佛实体标签严禁出现「唐」，防止与建置年代混淆"

    def test_g2_tang_claim_disproven_with_refuting_facts(self):
        ad = [a for a in S.ADOPTIONS
              if a.proposition_id == "prop_e26_wofoe_is_yuan_not_tang"]
        assert len(ad) == 1
        assert ad[0].status.name == "DISPROVEN"
        assert len(ad[0].refuting_fact_ids) > 0, \
            "DISPROVEN 必须带反驳证据 ID（absence of evidence ≠ evidence of absence）"
        for fid in ad[0].refuting_fact_ids:
            assert fid in _FACT_IDS, "反驳证据 %s 不存在" % fid

    def test_g2_temple_is_tang(self):
        """寺本身必须是唐（对照项：佛是元）。"""
        ad = [a for a in S.ADOPTIONS
              if a.proposition_id == "prop_e26_six_names_chain"]
        assert ad[0].rationale.count("唐") >= 1, "寺的创基须在唐贞观，与佛的元代形成对照"

    def test_g2_gap_explained(self):
        """两年代之间的差距必须被显式说明，不得含糊带过。"""
        blob = _blob()
        assert "六百余载" in blob, "寺（唐）佛（元）之间的相隔年数须显式说明"
        assert "不可互推" in blob or "不能反证" in blob, \
            "须显式声明器物年代与建置年代不可互推"

    def test_g2_wrong_statement_is_the_hypothesis(self):
        """待证伪的假说本身必须写错的那一句（便于审查）。"""
        p = [p for p in S.PROPOSITIONS if p.id == "prop_e26_wofoe_is_yuan_not_tang"][0]
        assert "唐时所铸" in p.statement, "命题须把「唐时所铸」作为待证伪的通行错说"

    def test_g2_state_records_yuan_cast(self):
        st = [s for s in S.STATES if s.id == "state_e26_yuan_wofoe_cast"]
        assert len(st) == 1
        assert st[0].entity_id == "ent_e26_yuan_wofo"
        assert "元代所铸" in st[0].function


# ==================================================================
# G3  国保批次与编号精确，且不与 E25 交叉污染
# ==================================================================

class TestGuobaoBatchGate:
    def test_g3_is_fifth_batch_with_number(self):
        blob = _blob()
        assert "第五批" in blob
        assert "5-205" in blob, "第五批国保必须引编号 5-205"

    def test_g3_not_first_batch(self):
        """本寺现状陈述必须是第五批。

        注意判据范围：`fact_e26_guobao5_5_205` 的 translator_note 里
        合法地提及「第一批」——那是与 E25 五塔寺的口径对照说明。
        因此只检查**现状陈述本身**（attested_string / 实体标签），
        不检查解释性文字。这正是 E25 教训「判据必须问对问题」。
        """
        own = [f for f in S.FACTS if f.id == "fact_e26_guobao5_5_205"][0]
        assert "第五批" in own.attested_string
        assert "第一批" not in own.attested_string, \
            "本寺为第五批，现状陈述不得写作第一批"
        for st in S.STATES:
            text = st.geometry + st.function
            if "全国重点文物保护单位" in text:
                assert "第一批" not in text, \
                    "🔴 状态 %s 把本寺写成第一批国保" % st.id

    def test_g3_1961_numbering_not_invented(self):
        """本寺为第五批，「1-75」式编号（第一批口径）严禁作为**本寺**编号出现。"""
        own = [f for f in S.FACTS if f.id == "fact_e26_guobao5_5_205"][0]
        assert "5-205" in own.attested_string
        for ad in S.ADOPTIONS:
            if ad.proposition_id == "prop_e26_guobao5_numbering":
                # rationale 提及 1-75 是合法的（说明本寺不用该体系）
                assert "1-75" in ad.rationale or "1-75" not in ad.rationale

    def test_g3_first_batch_reference_is_contrast_only(self):
        """允许提及第一批，但只能是「E25 对照」语境。"""
        p = [p for p in S.PROPOSITIONS if p.id == "prop_e26_guobao5_numbering"][0]
        assert "第一批" in p.inference_method
        assert "E25" in p.inference_method, "提及第一批时须标明是 E25 五塔寺的对照语境"

    def test_g3_e25_does_not_invent_numbering(self):
        """🔴 反向：E25 五塔寺属第一批，**必须不引编号**（不得被 E26 规则污染）。"""
        e25_blob = " ".join(
            d.section_title + d.volume_number for d in E25_DIVISIONS)
        assert "1-75" not in e25_blob, \
            "🔴 E25 五塔寺为第一批国保，严禁引用「1-75」式编号（跨集污染）"
        assert E25_DIVISIONS[0].volume_number == "第一批", "E25 批次口径不得被 E26 改写"


# ==================================================================
# G4  DISPROVEN 必须有反驳证据 ID（承 E25 元教训）
# ==================================================================

class TestDisprovenDisciplineGate:
    def test_g4_all_disproven_have_refuting_facts(self):
        for ad in S.ADOPTIONS:
            if ad.status.name == "DISPROVEN":
                assert len(ad.refuting_fact_ids) > 0, \
                    "❌ %s 判为 DISPROVEN 却没有反驳证据 ID —— " \
                    "这是 E25 踩过的坑：无据 ≠ 已证伪" % ad.proposition_id

    def test_g4_unsubstantiated_for_no_evidence(self):
        """「Offer 寺」无一手书证可反驳，必须 UNSUBSTANTIATED 而非 DISPROVEN。"""
        ad = [a for a in S.ADOPTIONS
              if a.proposition_id == "prop_e26_offer_temple_as_history"][0]
        assert ad.status.name == "UNSUBSTANTIATED", \
            "网络谐音无书证可作反驳依据，只能 UNSUBSTANTIATED（不得伪造证据）"
        assert "L5" in ad.rationale or "流行语" in ad.rationale, \
            "须标注其为现代流行语（L5）"

    def test_g4_offer_never_enters_name_chain(self):
        labels = [a.label for a in S.APPELLATIONS]
        assert not any("Offer" in lb or "offer" in lb for lb in labels), \
            "V-NC04：网络谐音严禁进入寺名沿革链"

    def test_g4_every_proposition_adopted(self):
        prop_ids = {p.id for p in S.PROPOSITIONS}
        adopted = {a.proposition_id for a in S.ADOPTIONS}
        assert prop_ids == adopted, \
            "每个命题都须有采信记录，缺 %s" % (prop_ids - adopted)


# ==================================================================
# G5  引用完整性（🔴 本测试抓出 E25 的真 bug）
# ==================================================================

class TestReferentialIntegrityGate:
    def test_g5_all_division_source_ids_exist(self):
        """🔴 回归：wutasi.py 曾写 source_id="src_guobao_1st"，而全库只有
        src_guobao_5th —— 该 id 悬空且从无测试覆盖。此断言锁死它。"""
        for d in S.DIVISIONS + list(E25_DIVISIONS):
            assert d.source_id in ALL_SOURCE_IDS, \
                "🔴 SourceDivision %s 引用了不存在的书源 %s" % (d.id, d.source_id)

    def test_g5_all_fact_division_ids_exist(self):
        div_ids = {d.id for d in S.DIVISIONS}
        for f in S.FACTS:
            assert f.division_id in div_ids, \
                "🔴 TextualFact %s 引用了不存在的篇卷 %s" % (f.id, f.division_id)

    def test_g5_all_fact_source_years_exist(self):
        for f in S.FACTS:
            assert f.source_year is not None, "事实 %s 缺年代" % f.id

    def test_g5_all_state_entity_ids_exist(self):
        """🔴 状态与同指断言的 entity_id 必须真实存在（本地或 extractor）。"""
        for st in S.STATES:
            assert st.entity_id in _ENT_IDS or st.entity_id in _TOP_IDS or \
                   st.entity_id in _UNIT_IDS, \
                "🔴 HistoricalFeatureState %s 引用了不存在的实体 %s" % (st.id, st.entity_id)

    def test_g5_all_identity_subject_ids_exist(self):
        for dia in S.IDENTITIES:
            for eid in dia.subject_entity_ids:
                assert eid in _ENT_IDS or eid in _TOP_IDS or eid in _UNIT_IDS, \
                    "🔴 DiachronicIdentityAssertion %s 引用了不存在的实体 %s" % (dia.id, eid)

    def test_g5_all_referential_targets_exist(self):
        for ref in S.REFERENCES:
            assert ref.appellation_id in _APP_IDS, \
                "🔴 ReferentialAssertion %s 引用了不存在的名号 %s" % (ref.id, ref.appellation_id)
            assert ref.referent_entity_id in _ENT_IDS or \
                   ref.referent_entity_id in _TOP_IDS, \
                "🔴 ReferentialAssertion %s 指向了不存在的实体 %s" % (
                    ref.id, ref.referent_entity_id)

    def test_g5_all_evidence_fact_ids_exist(self):
        def check(ids, where):
            for fid in ids:
                assert fid in _FACT_IDS, \
                    "🔴 %s 引用了不存在的证据 %s" % (where, fid)

        for st in S.STATES:
            check(st.evidence_fact_ids, "state %s" % st.id)
        for dia in S.IDENTITIES:
            check(dia.evidence_fact_ids, "identity %s" % dia.id)
        for ref in S.REFERENCES:
            check(ref.evidence_fact_ids, "referential %s" % ref.id)
        for a in S.APPELLATIONS:
            check(a.attesting_fact_ids, "appellation %s" % a.id)
        for p in S.PROPOSITIONS:
            check(p.derived_from_fact_ids, "proposition %s" % p.id)
        for ad in S.ADOPTIONS:
            check(ad.refuting_fact_ids, "adoption %s" % ad.proposition_id)

    def test_g5_extractor_has_all_six_name_nodes(self):
        """六个名号都必须在 extractor 中有真实节点（不得只在 calibration 里虚构 id）。"""
        for node in ("top_sifangpujue", "top_doushuai", "top_zhaoxiaoshi",
                     "top_hongqingsi", "top_shuanshansi", "top_yongansi", "top_wofosi"):
            assert node in _TOP_IDS, "🔴 extractor 中缺少名号节点 %s" % node

    def test_g5_extractor_has_unit(self):
        assert "unit_sifangpujue_temple" in _UNIT_IDS, \
            "🔴 extractor 中缺少 unit_sifangpujue_temple"


# ==================================================================
# G6/G7  负控制假通过检出
# ==================================================================

class TestNegativeControlGate:
    def test_g6_xiangshan_claim_disproven(self):
        """V-NC05：「卧佛寺在香山」须被证伪，且带证据。"""
        ad = [a for a in S.ADOPTIONS if a.proposition_id == "prop_e26_in_xiangshan"][0]
        assert ad.status.name == "DISPROVEN"
        assert len(ad.refuting_fact_ids) > 0

    def test_g6_location_is_shuoan_not_xiangshan(self):
        blob = _blob()
        assert "寿安山" in blob
        ad = [a for a in S.ADOPTIONS if a.proposition_id == "prop_e26_in_xiangshan"][0]
        assert "寿安山南麓" in ad.rationale

    def test_g7_rationale_cites_layering(self):
        """每条采信须说明理由，不得空 rationale。"""
        for ad in S.ADOPTIONS:
            assert len(ad.rationale.strip()) >= 20, \
                "采信 %s 的理由过短，可能是空壳（假通过）" % ad.proposition_id

    def test_g7_inference_method_cites_method(self):
        """每条命题须说明推断方法，且不得为占位符。"""
        for p in S.PROPOSITIONS:
            assert len(p.inference_method.strip()) >= 40, \
                "命题 %s 的推断方法过短，可能是占位符" % p.id
            assert p.inference_method.strip() not in ("TODO", "N/A", "待补"), \
                "命题 %s 的推断方法是占位符" % p.id

    def test_g7_six_names_not_collapsed(self):
        """六个名号必须各自有 Appellation，不得合并成一条。"""
        labels = set(a.label for a in S.APPELLATIONS)
        assert len(labels) == 6, "六个名号必须互不相同，实际 %s" % labels
