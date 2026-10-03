# -*- coding: utf-8 -*-
"""haidian_kg/calibration/wutasi.py
真觉寺／五塔寺 塔寺时序否证层 —— 海淀历史地名知识库 E25 入库模块

模块定位（**不重复建模**）:
`haidian_kg/extractor.py` 已建成 `top_zhenjuesi`（真觉寺）、`top_wutasi`（五塔寺）
与 `attest_zhenjuesi_shilu`（明宪宗实录成化九年条，VERIFIED/L2）。本模块**只补
E25 特有的「塔寺时序否证层」**：把「五塔寺（真觉寺）始建于明成化九年」立为
DISPROVEN 假说节点，并加三条存疑/负控制。所有实体经 DiachronicIdentityAssertion
与 extractor 已有节点同指挂钩。

证据分级:
  [一手金石实物] 券门石匾「敕建金刚宝座 大明成化九年十一月初二造」（本集首要实物）
  [一手正史]     《明宪宗实录》卷一百二十「真觉寺金刚宝座塔成，赐名大觉金刚宝座」
  [一手正史/御制] 明宪宗御制《真觉寺金刚宝座塔记略》（寺创于永乐初年）
  [现代机构口径] 第一批全国重点文物保护单位（1961-03-04）

核心红线:
  NC1 「塔年当寺年」→ DISPROVEN（寺创永乐初年，塔成化九年，相隔数十年）
  NC2 石匾与实录**只证塔**（匾文通篇无「寺」字；实录动词落在「塔」）
  NC3 「五塔寺」俗名不系年（无直接书证）
  NC4 「清乾隆避雍正胤禛讳改名大正觉寺」→ DISPROVEN（时序不通，无避讳对象）
  NC5 国保为**第一批**（1961-03-04）；**1961 年首批无「1-75」式编号体系**，
      网传编号无制度依据，严禁引用

Python 3.9.6 兼容: 禁 X | None, 禁 match.
"""
from typing import Dict, List, Optional

from .bibliography import source_by_title
from ..ontology.temporal import (
    CalibrationTable, DatePoint, GregorianDate, TimeSpan,
)
from ..ontology.epistemic import (
    BeliefAdoption, EpistemicStatus, HistoricalSource, Proposition,
    SourceDivision, TextualFact,
)
from ..ontology.spatiotemporal import (
    Appellation, AppellationKind, DiachronicIdentityAssertion,
    HistoricalFeatureState, IdentityRelation, PersistentSpatialEntity,
    PhysicalThingKind, PlaceAggregate, PlaceTransformation,
    PlaceTransformationEvent, ReferentialAssertion,
)

CAL = CalibrationTable.CN_ASTRONOMICAL_ALMANAC


def _dt(y, tag, precision="year"):
    return DatePoint(id=tag, label=str(y), precision=precision,
                     gregorian=GregorianDate(year=y, calibration=CAL))


def _ts(y1, y2, tag):
    return TimeSpan(id=tag, label="%d-%d" % (y1, y2),
                    begin=_dt(y1, tag + "_b"), end=_dt(y2, tag + "_e"))


# ==================================================================
# 书源与篇卷（实体归 extractor，本模块只登记新增引用的篇卷）
# ==================================================================

SOURCES: List[HistoricalSource] = [
    source_by_title("国务院公布全国重点文物保护单位名单"),
]

DIVISIONS: List[SourceDivision] = [
    SourceDivision(id="div_e25_guobao1_zhenjuesi", source_id="src_guobao_1st",
                   volume_number="第一批", section_title="真觉寺金刚宝座"),
]


# ==================================================================
# 文本事实层（E25 专属：只立「只证塔」所需的三条书证）
# ==================================================================

FACTS: List[TextualFact] = [
    # 🔴 NC1/NC2 的核心：实录动词与赐名皆落在「塔」，不是寺
    TextualFact(
        id="fact_e25_shilu_pagoda_done",
        division_id="div_e25_guobao1_zhenjuesi",
        verbatim_quote=("成化九年冬十一月真覺寺金剛寶座塔成賜名大覺金剛寶座"
                        "累石為臺五丈"),
        attested_string="真觉寺金刚宝座塔成，赐名大觉金刚宝座",
        source_year=_dt(1473, "dt_e25_shilu"),
        translator_note=(
            "《明宪宗实录》卷一百二十（L2 一手正史）。逐字要点："
            "①「**塔**成」——动词落在塔上，非寺成；"
            "②「赐名**大觉金刚宝座**」——赐的是塔的名（号），非寺名；"
            "③「累石为台五丈」——形容塔座形制。"
            "此条**只证塔的落成年**，不可外推为寺的始建年。"
            "（此条与 extractor.attest_zhenjuesi_shilu 同源，本模块补辨析层。）"
        ),
    ),
    # 一手金石：券门石匾（通篇无「寺」字）
    TextualFact(
        id="fact_e25_shibei_only_pagoda",
        division_id="div_e25_guobao1_zhenjuesi",
        verbatim_quote="敕建金剛寶座　大明成化九年十一月初二造",
        attested_string="敕建金刚宝座 大明成化九年十一月初二造",
        source_year=_dt(1473, "dt_e25_shibei"),
        translator_note=(
            "塔座南面券门上方所嵌石匾，**至今仍嵌于原处**（L1 一手实物）。"
            "🔴 逐字要点：①「敕建」= 官修工程；"
            "②「**金刚宝座**」四字指**塔**（金刚宝座式塔），**通篇无一字提到「寺」**；"
            "③「造」= 造此塔，非始建某寺。"
            "此匾**只证塔**，与实录互证到月（成化九年冬十一月 / 十一月初二）。"
        ),
    ),
    # 寺的创基（早于塔数十年）
    TextualFact(
        id="fact_e25_yongle_chuangji",
        division_id="div_e25_guobao1_zhenjuesi",
        verbatim_quote=("永樂初年西域高僧班迪達大國師進獻金身佛像五尊及金剛寶座規式"
                        "明成祖封其為大國師擇址京城西關外敕建寺院賜名真覺寺"),
        attested_string="永乐初年敕建寺院，赐名真觉寺",
        source_year=_dt(1415, "dt_e25_yongle"),
        translator_note=(
            "据明宪宗御制《真觉寺金刚宝座塔记略》与《帝京景物略》所记（L2 御制碑记 / "
            "L3 明人笔记）。永乐初年西域高僧班迪达大国师进献金佛五尊与印度佛陀迦耶"
            "精舍（大菩提寺）金刚宝座规式，明成祖封其为大国师，择址京城西关外敕建"
            "寺院并**赐名「真觉寺」**。此为**寺的创基**，早于成化九年塔成数十年。"
        ),
    ),
]


# ==================================================================
# 空间实体（E25 专属：塔的独立实体，与 extractor 寺/俗名节点同指挂钩）
# ==================================================================

ENTITIES: List[PersistentSpatialEntity] = [
    PersistentSpatialEntity(
        id="ent_e25_jingangbaozuo_pagoda",
        kind=PhysicalThingKind.RELIGIOUS_PRECINCT,
        canonical_label=("真觉寺金刚宝座塔（明成化九年1473落成；仿印度佛陀迦耶精舍式样，"
                         "五座密檐小塔立于方形须弥座；第一批全国重点文物保护单位1961-03-04）"),
    ),
]

ENTITIES_MAP: Dict[str, PersistentSpatialEntity] = {e.id: e for e in ENTITIES}

APPELLATIONS: List[Appellation] = [
    Appellation(
        id="app_e25_pagoda_name",
        label="大觉金刚宝座",
        kind=AppellationKind.OLD_NAME,
        valid_time_span=_ts(1473, 1473, "ts_app_e25_pagoda"),
        attesting_fact_ids=["fact_e25_shilu_pagoda_done"],
    ),
]

STATES: List[HistoricalFeatureState] = [
    HistoricalFeatureState(
        id="state_e25_pagoda_chenghua",
        entity_id="ent_e25_jingangbaozuo_pagoda",
        label="明成化：金刚宝座塔成（1473）",
        time_span=_ts(1473, 1473, "ts_st_e25_pagoda"),
        geometry=("京城西关外（今海淀长河北岸白石桥以东）；"
                  "太监钱义等奉敕主持，依中印度样式「累石为台五丈」建成"),
        function=("佛塔：仿印度佛陀迦耶精舍（大菩提寺）式样，五座密檐小塔立于方形须弥座；"
                  "塔座四壁遍刻梵文、藏文、蒙文、阿拉伯文等文字"),
        evidence_fact_ids=["fact_e25_shilu_pagoda_done", "fact_e25_shibei_only_pagoda"],
    ),
]

TRANSFORMATIONS: List[PlaceTransformation] = []

IDENTITIES: List[DiachronicIdentityAssertion] = [
    # 金刚宝座塔 ⟷ 真觉寺（同址同物，非两处）
    DiachronicIdentityAssertion(
        id="dia_e25_pagoda_zhenjuesi",
        relation=IdentityRelation.SAME_CONTINUANT,
        subject_entity_ids=["ent_e25_jingangbaozuo_pagoda", "top_zhenjuesi"],
        time_span=_ts(1473, 2026, "ts_dia_e25"),
        evidence_fact_ids=["fact_e25_shilu_pagoda_done"],
        status=EpistemicStatus.VERIFIED,
        is_orthogonal_to_state_change=True,
    ),
    # 俗名五塔寺 ⟷ 真觉寺（清以后）
    DiachronicIdentityAssertion(
        id="dia_e25_wutasi_zhenjuesi",
        relation=IdentityRelation.SAME_CONTINUANT,
        subject_entity_ids=["top_wutasi", "top_zhenjuesi"],
        time_span=_ts(1473, 2026, "ts_dia_e25b"),
        evidence_fact_ids=["fact_e25_yongle_chuangji"],
        status=EpistemicStatus.VERIFIED,
        is_orthogonal_to_state_change=True,
    ),
]

REFERENCES: List[ReferentialAssertion] = [
    ReferentialAssertion(
        id="ref_e25_pagoda_name",
        appellation_id="app_e25_pagoda_name",
        referent_entity_id="ent_e25_jingangbaozuo_pagoda",
        time_span=_ts(1473, 1473, "ts_ref_e25_pagoda"),
        evidence_fact_ids=["fact_e25_shilu_pagoda_done"],
        status=EpistemicStatus.VERIFIED,
    ),
]

AGGREGATES: List[PlaceAggregate] = []


# ==================================================================
# 命题层（E25 核心：塔年 ≠ 寺年）与采信层
# ==================================================================

PROPOSITIONS: List[Proposition] = [
    # —— NC1：塔年当寺年，被证伪（第四例时序否证）——
    Proposition(
        id="prop_e25_ta_1473_as_si_founder",
        statement="五塔寺（真觉寺）始建于明成化九年（1473）。",
        derived_from_fact_ids=["fact_e25_shibei_only_pagoda", "fact_e25_yongle_chuangji"],
        inferred_subject_id="ent_e25_jingangbaozuo_pagoda",
        inference_method=(
            "时序否证：券门石匾「敕建金刚宝座 大明成化九年十一月初二造」与《明宪宗实录》"
            "「真觉寺金刚宝座**塔**成」**双源只证塔**；寺的创基在**永乐初年**（班迪达进献"
            "印度塔式后敕建真觉寺），早于成化九年**数十年**。"
            "「塔的落成年」被误读为「寺的始建年」。本系列继 E21（元史伪引文）、"
            "E23（杨六郎附会）、E24（金章宗始建）之后**第四例时序否证**，"
            "且**首例以实物石匾为否证对象**。"
        ),
        alternative_explanations=[
            "通行说可能源自未读匾文全文者，仅取「成化九年造」而略去「金刚宝座」四字",
            "「五塔寺」之名在明末清初通行后，反使后人把塔的年代当成整个寺的年代",
        ],
    ),
    # —— NC2：石匾/实录的证据力（正向判据）——
    Proposition(
        id="prop_e25_stele_only_proves_pagoda",
        statement="券门石匾与《明宪宗实录》所记成化九年，是金刚宝座**塔**的落成年，"
                  "不是真觉寺的始建年。",
        derived_from_fact_ids=["fact_e25_shibei_only_pagoda", "fact_e25_shilu_pagoda_done"],
        inferred_subject_id="ent_e25_jingangbaozuo_pagoda",
        inference_method=(
            "逐字证据力界定：石匾通篇无「寺」字，「金刚宝座」四字指塔；"
            "实录动词落在「塔」（「塔成」），所赐之名亦为「**大觉金刚宝座**」（塔的名号）。"
            "两条一手书证互证到月（成化九年冬十一月／十一月初二），"
            "其证据范围**严格限于塔**，不可外推为寺的创建凭据。"
        ),
        alternative_explanations=[],
    ),
    # —— NC3：俗名不系年 ——
    Proposition(
        id="prop_e25_suming_year_unknown",
        statement="「五塔寺」这一俗名具体定型于某一年。",
        derived_from_fact_ids=[],
        inferred_subject_id="top_wutasi",
        inference_method=(
            "无直接书证：俗名源自塔顶五座密檐小塔，但**具体命名年代无书证**。"
            "本片只述其来源与「土人因称」的民间属性，**严禁系年**。"
        ),
        alternative_explanations=["明清间随密檐小塔建成而通行", "年代不可考"],
    ),
    # —— NC4：避讳改名说时序不通 ——
    Proposition(
        id="prop_e25_qianlong_bihuang_rename",
        statement="清乾隆为避雍正帝胤禛之讳，将真觉寺改称「大正觉寺」。",
        derived_from_fact_ids=[],
        inferred_subject_id="top_zhenjuesi",
        inference_method=(
            "时序不通：寺名「真觉」与清世宗胤禛**毫无字面关联**，不存在避讳对象；"
            "且改名说多出网传而无一手书证。**DISPROVEN / UNSUBSTANTIATED**，"
            "严禁入正片。"
        ),
        alternative_explanations=["（网传说无一手书证支撑）"],
    ),
]

ADOPTIONS: List[BeliefAdoption] = [
    BeliefAdoption(
        proposition_id="prop_e25_ta_1473_as_si_founder",
        status=EpistemicStatus.DISPROVEN,
        confidence=0.96,
        adopted_by="E25 负控制 V-NC01（塔年 ≠ 寺年）",
        adopted_at=_dt(2026, "dt_ad_e25_nc1"),
        rationale=(
            "石匾与《明宪宗实录》双源只证塔（成化九年1473）；寺创于永乐初年，"
            "早数十年。通行说「五塔寺建于成化九年」DISPROVEN。"
        ),
        refuting_fact_ids=["fact_e25_shibei_only_pagoda", "fact_e25_yongle_chuangji"],
    ),
    BeliefAdoption(
        proposition_id="prop_e25_stele_only_proves_pagoda",
        status=EpistemicStatus.VERIFIED,
        confidence=0.96,
        adopted_by="E25 正向判据（一手实物与一手实录互证到月）",
        adopted_at=_dt(2026, "dt_ad_e25_nc2"),
        rationale=(
            "石匾「敕建金刚宝座」通篇无「寺」字；实录「金刚宝座塔成」「赐名大觉金刚宝座」。"
            "两条一手书证的证据范围严格限于塔。"
        ),
        refuting_fact_ids=[],
    ),
    BeliefAdoption(
        proposition_id="prop_e25_suming_year_unknown",
        status=EpistemicStatus.UNSUBSTANTIATED,
        confidence=0.9,
        adopted_by="E25 负控制 V-NC03（俗名不系年）",
        adopted_at=_dt(2026, "dt_ad_e25_nc3"),
        rationale="「五塔寺」俗名的具体定型年代无直接书证，严禁系年。",
    ),
    BeliefAdoption(
        proposition_id="prop_e25_qianlong_bihuang_rename",
        # 无任何一手书证可作反驳依据（absence of evidence ≠ evidence of absence），
        # 故采 UNSUBSTANTIATED 而非 DISPROVEN；「时序不通」写入 rationale 作正片禁令。
        status=EpistemicStatus.UNSUBSTANTIATED,
        confidence=0.85,
        adopted_by="E25 负控制 V-NC04（避讳说时序不通且无书证）",
        adopted_at=_dt(2026, "dt_ad_e25_nc4"),
        rationale=(
            "寺名「真觉」与清世宗胤禛无字面关联，不存在避讳对象；"
            "且网传说无一手书证可作反驳或采信依据。时序不通，UNSUBSTANTIATED，严禁入正片。"
        ),
    ),
]
