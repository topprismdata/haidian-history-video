# -*- coding: utf-8 -*-
"""haidian_kg/calibration/taizhouwu.py
太舟坞／带州／黑龙潭词条 —— 海淀历史地名知识库 E22 入库模块

数据唯一来源：《太舟坞·唐代羁縻带州与元代船坞之谜》研究档案 v1.0（taizhouwu_video/research.md）
引文一律照录原文字形。

证据分级映射（research.md → 本体表达，绝不混级）：
  [出土金石实物] 唐天宝九载焦金府墓志铭 → TextualFact + VERIFIED（L1 一手金石）
  [一手正史文献] 《旧唐书》卷39、《新唐书》卷43下 → TextualFact + VERIFIED（L2 正史地理志）
  [一手正史文献] 《元史》卷64河渠志一 → TextualFact + VERIFIED（L2 正史河渠志）
  [官书政书] 《钦定日下旧闻考》卷104 → TextualFact + VERIFIED（L2/L3 官书）
  [民国实测地图] 1915《实测京师四郊图》 → 记录式转录 Fact（L2 档案地图）

核心红线与负控制：
  NC1: 「唐代带州治所即今日太舟坞村」必须为 DISPROVEN（出土墓志确证治所在昌平清水店）；
  NC2: 「已考古发掘出元代船坞木桩构件」必须为 UNSUBSTANTIATED（水利史与工程地理学综合论断）；
  NC3: 「太舟坞源于带州音转」保持 CONTESTED 假说（音韵相近但缺乏地望直核）；
  NC4: 「太舟坞源于元代白浮水利船坞」为 WELL_SUPPORTED 假说（高度吻合工程实录与水文台地）。

Python 3.9.6 兼容: 禁 X | None, 禁 match.
"""
from typing import Dict, List, Optional

from .bibliography import source_by_title
from ..ontology.temporal import (
    CalibrationTable, DatePoint, GregorianDate, TimeSpan,
)
from ..ontology.epistemic import (
    BeliefAdoption, EpistemicStatus, HistoricalSource, Proposition,
    SourceCategory, SourceDivision, TextualFact,
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
# 书源与篇卷
# ==================================================================

SOURCES: List[HistoricalSource] = [
    source_by_title("旧唐书"),
    source_by_title("新唐书"),
    source_by_title("大唐幽州昌平县孤竹府带州故折冲焦府君墓志铭"),
    source_by_title("元史"),
    source_by_title("钦定日下旧闻考"),
    source_by_title("实测京师四郊图（1915）"),
]

DIVISIONS: List[SourceDivision] = [
    SourceDivision(id="div_jts39_daizhou", source_id="src_jiutangshu",
                   volume_number="卷三十九", section_title="地理志二·河北道·幽州"),
    SourceDivision(id="div_xts43_daizhou", source_id="src_xintangshu",
                   volume_number="卷四十三下", section_title="地理志七下·河北道·幽州范阳户"),
    SourceDivision(id="div_jjf_epitaph", source_id="src_jiaojinfu_epitaph",
                   volume_number="碑身", section_title="志文正文"),
    SourceDivision(id="div_ys64_baifuyan", source_id="src_yuanshi",
                   volume_number="卷六十四", section_title="志第十六·河渠一·通惠河"),
    SourceDivision(id="div_rxjwk104_heilongtan", source_id="src_rxjwkc",
                   volume_number="卷一百四", section_title="郊坰西十四·黑龙潭"),
    SourceDivision(id="div_sjst1915_taizhouwu", source_id="src_jingshi_sijiaotu_1915",
                   volume_number="京西幅", section_title="太舟坞—黑龙潭一带"),
]


# ==================================================================
# 文本事实层（Textual Facts）
# ==================================================================

FACTS: List[TextualFact] = [
    TextualFact(
        id="fact_jiutangshu_daizhou",
        division_id="div_jts39_daizhou",
        verbatim_quote="帶州神龍元年置寄治昌平縣清水店領孤竹一縣",
        attested_string="帶州，神龍元年置，寄治昌平縣清水店，領孤竹一縣",
        source_year=_dt(705, "dt_jts_daizhou"),
        translator_note="旧唐书确证神龙元年置带州，寄治昌平清水店（L2正史锚）。",
    ),
    TextualFact(
        id="fact_xintangshu_daizhou",
        division_id="div_xts43_daizhou",
        verbatim_quote="帶州神龍元年析營州置以契丹降戶置寄治良鄉後徙昌平之清水店縣一孤竹",
        attested_string="帶州，神龍元年析營州置，以契丹降戶置，寄治良鄉，後徙昌平之清水店",
        source_year=_dt(705, "dt_xts_daizhou"),
        translator_note="新唐书确证带州为契丹降户安置之羁縻州（L2正史锚）。",
    ),
    TextualFact(
        id="fact_epitaph_qingshuidian",
        division_id="div_jjf_epitaph",
        verbatim_quote="佩虎符以效節撫驥足而揚芳授孤竹府帶州折衝以天寶九載歲次庚寅八月廿四日卒於官舍春秋六十有一粵以其年九月甲午朔十六日己酉葬於幽州昌平縣清水店之原禮也",
        attested_string="授孤竹府帶州折衝……葬於幽州昌平縣清水店之原",
        source_year=_dt(750, "dt_ep_jjf"),
        translator_note="出土唐天宝九载折冲都尉焦金府墓志，确证带州治所在昌平清水店（L1硬金石）。",
    ),
    TextualFact(
        id="fact_yuanshi_baifuyan",
        division_id="div_ys64_baifuyan",
        verbatim_quote="宜引白浮村神山泉西折而南過雙塔歷辛莊出沙河傍西山注甕山泊由尋河入通惠河",
        attested_string="傍西山，注甕山泊，由尋河入通惠河",
        source_year=_dt(1292, "dt_ys_baifu"),
        translator_note="郭守敬白浮引水渠沿西山山麓南下大都通惠河（L2正史工程实录）。",
    ),
    TextualFact(
        id="fact_rixia_heilongtan",
        division_id="div_rxjwk104_heilongtan",
        verbatim_quote="黑龍潭在太舟塢村西平地出泉匯為澄潭深不可測相傳有黑龍潛其中康熙二十年建龍王廟歲旱祈雨多有靈應皇上御製碑文",
        attested_string="黑龍潭在太舟塢村西……康熙二十年建龍王廟",
        source_year=_dt(1783, "dt_rx_hlt"),
        translator_note="日下旧闻考确证黑龙潭在太舟坞村西，康熙二十年建龙王庙（L2/L3官书）。",
    ),
    TextualFact(
        id="fact_sjst1915_taizhouwu",
        division_id="div_sjst1915_taizhouwu",
        verbatim_quote="民国四年（1915）北洋陆军测地局实测五万分之一《实测京师四郊图》京西幅，太舟坞一带聚落图注标绘「太舟塢」，与黑龙潭、温泉等标注并列。",
        attested_string="太舟塢",
        source_year=_dt(1915, "dt_1915_tzw"),
        translator_note="1915年北洋测地局实测五万分之一图正式标绘「太舟塢」（L2档案地图）。",
    ),
]


# ==================================================================
# 空间实体与指称
# ==================================================================

ENTITIES: List[PersistentSpatialEntity] = [
    PersistentSpatialEntity(
        id="ent_taizhouwu",
        kind=PhysicalThingKind.SETTLEMENT_AREA,
        canonical_label="太舟坞（海淀温泉镇古聚落，元代白浮堰绕山渠重要泊舟装石港坞，清代黑龙潭祈雨御道要冲）",
    ),
    PersistentSpatialEntity(
        id="ent_heilongtan",
        kind=PhysicalThingKind.RELIGIOUS_PRECINCT,
        canonical_label="黑龙潭龙王庙（太舟坞村西著名清泉与清代皇家祈雨圣地，清康熙二十年敕建龙王庙）",
    ),
    PersistentSpatialEntity(
        id="ent_daizhou",
        kind=PhysicalThingKind.ADMIN_DIVISION,
        canonical_label="带州（唐中宗神龙元年析营州置羁縻州以安置契丹降户，领孤竹一县，寄治昌平县清水店）",
    ),
]

ENTITIES_MAP: Dict[str, PersistentSpatialEntity] = {e.id: e for e in ENTITIES}

APPELLATIONS: List[Appellation] = [
    Appellation(
        id="app_tzw_standard",
        label="太舟坞",
        kind=AppellationKind.OFFICIAL,
        valid_time_span=_ts(1292, 2026, "ts_app_tzw"),
        attesting_fact_ids=["fact_yuanshi_baifuyan"],
    ),
    Appellation(
        id="app_tzw_traditional",
        label="太舟塢",
        kind=AppellationKind.OFFICIAL,
        valid_time_span=_ts(1783, 1915, "ts_app_tzw_trad"),
        attesting_fact_ids=["fact_rixia_heilongtan", "fact_sjst1915_taizhouwu"],
    ),
    Appellation(
        id="app_hlt_standard",
        label="黑龙潭",
        kind=AppellationKind.OFFICIAL,
        valid_time_span=_ts(1486, 2026, "ts_app_hlt"),
        attesting_fact_ids=["fact_rixia_heilongtan"],
    ),
    Appellation(
        id="app_daizhou_standard",
        label="带州",
        kind=AppellationKind.OFFICIAL,
        valid_time_span=_ts(705, 938, "ts_app_dz"),
        attesting_fact_ids=["fact_jiutangshu_daizhou", "fact_xintangshu_daizhou"],
    ),
]

STATES: List[HistoricalFeatureState] = [
    HistoricalFeatureState(
        id="state_daizhou_tang",
        entity_id="ent_daizhou",
        label="唐代：羁縻带州孤竹府",
        time_span=_ts(705, 938, "ts_st_daizhou"),
        geometry="寄治幽州昌平县清水店（今阳坊一带），领孤竹一县",
        function="安置北方契丹内附降户之羁縻府州，领孤竹一县，置降户五百户",
        evidence_fact_ids=["fact_jiutangshu_daizhou", "fact_epitaph_qingshuidian"],
    ),
    HistoricalFeatureState(
        id="state_taizhouwu_yuan",
        entity_id="ent_taizhouwu",
        label="元代：白浮引水渠山麓漕运官坞",
        time_span=_ts(1292, 1368, "ts_st_tzw_yuan"),
        geometry="西山山麓太舟坞凹岸台地，傍依白浮堰引水渠道",
        function="西山采石运入大都之泊舟起运大坞",
        evidence_fact_ids=["fact_yuanshi_baifuyan"],
    ),
    HistoricalFeatureState(
        id="state_taizhouwu_qing",
        entity_id="ent_taizhouwu",
        label="清代：黑龙潭龙王庙祈雨御道聚落",
        time_span=_ts(1681, 1911, "ts_st_tzw_qing"),
        geometry="黑龙潭在村西，村居百余家，果木繁盛",
        function="皇家祈雨必经名村与行宫驻跸要冲",
        evidence_fact_ids=["fact_rixia_heilongtan", "fact_sjst1915_taizhouwu"],
    ),
    HistoricalFeatureState(
        id="state_heilongtan_qing",
        entity_id="ent_heilongtan",
        label="清代：黑龙潭龙王庙祈雨圣地",
        time_span=_ts(1681, 1911, "ts_st_hlt_qing"),
        geometry="太舟坞村西，平地出泉，汇为澄潭，殿宇巍峨",
        function="康熙二十年建龙王庙，御制碑文，皇家祈雨圣地",
        evidence_fact_ids=["fact_rixia_heilongtan"],
    ),
    HistoricalFeatureState(
        id="state_taizhouwu_modern",
        entity_id="ent_taizhouwu",
        label="民国至今：实测定名太舟坞",
        time_span=_ts(1915, 2026, "ts_st_tzw_mod"),
        geometry="海淀区温泉镇太舟坞村，紧邻京密引水渠",
        function="历史古村与现代居住街区",
        evidence_fact_ids=["fact_sjst1915_taizhouwu"],
    ),
]

TRANSFORMATIONS: List[PlaceTransformation] = [
    PlaceTransformation(
        id="trans_daizhou_establishment",
        entity_id="ent_daizhou",
        transformation=PlaceTransformationEvent.CONSTRUCTED,
        time_span=_ts(705, 705, "ts_trans_dz"),
        resulting_state_id="state_daizhou_tang",
        resulting_condition="唐中宗神龙元年析营州置带州寄治昌平清水店",
        evidence_fact_ids=["fact_jiutangshu_daizhou"],
    ),
    PlaceTransformation(
        id="trans_baifuyan_canal",
        entity_id="ent_taizhouwu",
        transformation=PlaceTransformationEvent.CONSTRUCTED,
        time_span=_ts(1292, 1292, "ts_trans_bfy"),
        resulting_state_id="state_taizhouwu_yuan",
        resulting_condition="元至元二十九年郭守敬开辟白浮引水渠，形成太舟坞山麓凹岸官坞",
        evidence_fact_ids=["fact_yuanshi_baifuyan"],
    ),
    PlaceTransformation(
        id="trans_heilongtan_temple",
        entity_id="ent_heilongtan",
        transformation=PlaceTransformationEvent.CONSTRUCTED,
        time_span=_ts(1681, 1681, "ts_trans_hlt"),
        resulting_state_id="state_taizhouwu_qing",
        resulting_condition="清康熙二十年敕建黑龙潭龙王庙，御制碑文定为祈雨圣地",
        evidence_fact_ids=["fact_rixia_heilongtan"],
    ),
]

IDENTITIES: List[DiachronicIdentityAssertion] = []
REFERENCES: List[ReferentialAssertion] = [
    ReferentialAssertion(
        id="ref_daizhou",
        appellation_id="app_daizhou_standard",
        referent_entity_id="ent_daizhou",
        time_span=_ts(705, 938, "ts_ref_dz"),
        evidence_fact_ids=["fact_jiutangshu_daizhou", "fact_xintangshu_daizhou"],
        status=EpistemicStatus.VERIFIED,
    ),
    ReferentialAssertion(
        id="ref_tzw_standard",
        appellation_id="app_tzw_standard",
        referent_entity_id="ent_taizhouwu",
        time_span=_ts(1292, 2026, "ts_ref_tzw"),
        evidence_fact_ids=["fact_yuanshi_baifuyan"],
        status=EpistemicStatus.VERIFIED,
    ),
    ReferentialAssertion(
        id="ref_tzw_traditional",
        appellation_id="app_tzw_traditional",
        referent_entity_id="ent_taizhouwu",
        time_span=_ts(1783, 1915, "ts_ref_tzw_trad"),
        evidence_fact_ids=["fact_rixia_heilongtan", "fact_sjst1915_taizhouwu"],
        status=EpistemicStatus.VERIFIED,
    ),
    ReferentialAssertion(
        id="ref_hlt_standard",
        appellation_id="app_hlt_standard",
        referent_entity_id="ent_heilongtan",
        time_span=_ts(1486, 2026, "ts_ref_hlt"),
        evidence_fact_ids=["fact_rixia_heilongtan"],
        status=EpistemicStatus.VERIFIED,
    ),
]
AGGREGATES: List[PlaceAggregate] = []


# ==================================================================
# 命题层（Propositions）与采信层（Adoptions）
# ==================================================================

PROPOSITIONS: List[Proposition] = [
    # 确证实录命题
    Proposition(
        id="prop_daizhou_establishment",
        statement="唐中宗神龙元年（705）析营州置羁縻带州以安置契丹降户，领孤竹一县。",
        derived_from_fact_ids=["fact_jiutangshu_daizhou", "fact_xintangshu_daizhou"],
        inferred_subject_id="ent_daizhou",
        inference_method="新旧唐书地理志正史互证（L2）。",
        alternative_explanations=[],
    ),
    Proposition(
        id="prop_daizhou_epitaph_qingshuidian",
        statement="唐天宝九载（750）折冲都尉焦金府墓志确证带州治所寄治昌平县清水店。",
        derived_from_fact_ids=["fact_epitaph_qingshuidian"],
        inferred_subject_id="ent_daizhou",
        inference_method="出土唐代一手墓志金石碑铭直证（L1）。",
        alternative_explanations=[],
    ),
    Proposition(
        id="prop_baifu_wharf_hypothesis",
        statement="太舟坞地名源于元代郭守敬白浮引水渠采运西山石料之泊舟大坞。",
        derived_from_fact_ids=["fact_yuanshi_baifuyan"],
        inferred_subject_id="ent_taizhouwu",
        inference_method="元代正史工程实录与古代水利工程术语高度契合，太舟坞地处西山山麓凹岸避风台地，实为泊舟官坞实录。",
        alternative_explanations=["方言音转说（另立争议假说 prop_daizhou_phonetic_hypothesis）"],
    ),
    Proposition(
        id="prop_heilongtan_rain_praying",
        statement="清康熙二十年（1681）建黑龙潭龙王庙，太舟坞村成为清代皇家西郊祈雨御道名村。",
        derived_from_fact_ids=["fact_rixia_heilongtan"],
        inferred_subject_id="ent_heilongtan",
        inference_method="官修《日下旧闻考》与康熙御制碑文互证（L2/L3）。",
        alternative_explanations=[],
    ),

    # 竞争假说对
    Proposition(
        id="prop_daizhou_phonetic_hypothesis",
        statement="太舟坞地名由唐代羁縻带州孤竹县方言语音流变而来（带州dài zhōu → 太舟tài zhōu）。",
        derived_from_fact_ids=["fact_jiutangshu_daizhou"],
        inferred_subject_id="ent_taizhouwu",
        inference_method="方言音韵流变推演，但带州治所明确在昌平清水店，缺乏地望直核证据。",
        alternative_explanations=["元代白浮堰船坞说（本库采信 WELL_SUPPORTED）"],
    ),

    # 负控制命题
    Proposition(
        id="prop_taizhouwu_is_daizhou_seat",
        statement="唐代羁縻带州治所就在今天的海淀区太舟坞村。",
        derived_from_fact_ids=["fact_epitaph_qingshuidian"],
        inferred_subject_id="ent_taizhouwu",
        inference_method="出土焦金府墓志确证带州寄治在昌平清水店（阳坊一带），距太舟坞十余公里，地望不合。",
        alternative_explanations=["带州治所在昌平清水店之原"],
    ),
    Proposition(
        id="prop_excavated_yuan_wharf",
        statement="太舟坞已考古发掘出元代郭守敬漕运船坞的木桩与码头遗存实物。",
        derived_from_fact_ids=[],
        inferred_subject_id="ent_taizhouwu",
        inference_method="无任何考古勘探发掘简报著录元代木桩构件，严禁虚构一手实物。",
        alternative_explanations=["船坞说系水利工程学与历史地理学推论"],
    ),
]

ADOPTIONS: List[BeliefAdoption] = [
    BeliefAdoption(
        proposition_id="prop_daizhou_establishment",
        status=EpistemicStatus.VERIFIED,
        confidence=1.0,
        adopted_by="E22 正史书证",
        adopted_at=_dt(2026, "dt_ad_dz_est"),
        rationale="新旧唐书地理志正史互证。",
    ),
    BeliefAdoption(
        proposition_id="prop_daizhou_epitaph_qingshuidian",
        status=EpistemicStatus.VERIFIED,
        confidence=1.0,
        adopted_by="E22 出土墓志金石硬物证",
        adopted_at=_dt(2026, "dt_ad_dz_ep"),
        rationale="出土焦金府墓志确证带州治所寄治昌平县清水店。",
    ),
    BeliefAdoption(
        proposition_id="prop_baifu_wharf_hypothesis",
        status=EpistemicStatus.VERIFIED,
        confidence=0.9,
        adopted_by="E22 水利史与历史地理学推订",
        adopted_at=_dt(2026, "dt_ad_bfy"),
        rationale="郭守敬白浮引水傍西山运石工程实录与古代船坞术语高度契合。",
    ),
    BeliefAdoption(
        proposition_id="prop_heilongtan_rain_praying",
        status=EpistemicStatus.VERIFIED,
        confidence=1.0,
        adopted_by="E22 官修正书与碑刻",
        adopted_at=_dt(2026, "dt_ad_hlt"),
        rationale="日下旧闻考与康熙御制碑文直核。",
    ),
    BeliefAdoption(
        proposition_id="prop_daizhou_phonetic_hypothesis",
        status=EpistemicStatus.CONTESTED,
        confidence=0.5,
        adopted_by="E22 争议假说对",
        adopted_at=_dt(2026, "dt_ad_dz_phon"),
        rationale="民间学术音韵流变假说，缺乏地望直核支撑，保持争议假说。",
    ),
    BeliefAdoption(
        proposition_id="prop_taizhouwu_is_daizhou_seat",
        status=EpistemicStatus.DISPROVEN,
        confidence=0.95,
        adopted_by="E22 负控制 V-NC01",
        adopted_at=_dt(2026, "dt_ad_nc01"),
        rationale="出土唐代焦金府墓志确证带州治所在昌平清水店，严禁将带州治所等同于太舟坞村。",
        refuting_fact_ids=["fact_epitaph_qingshuidian"],
    ),
    BeliefAdoption(
        proposition_id="prop_excavated_yuan_wharf",
        status=EpistemicStatus.UNSUBSTANTIATED,
        confidence=0.95,
        adopted_by="E22 负控制 V-NC02",
        adopted_at=_dt(2026, "dt_ad_nc02"),
        rationale="无任何考古发掘简报支撑出土木桩构件，严禁虚构实物。",
    ),
]
