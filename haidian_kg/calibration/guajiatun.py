# -*- coding: utf-8 -*-
"""haidian_kg/calibration/guajiatun.py
挂甲屯／额驸城词条 —— 海淀历史地名知识库 E23 入库模块

数据唯一来源：《挂甲屯·杨六郎传说与清初额驸城》研究档案 v1.0（guajiatun_video/research.md）
引文一律照录原文字形。

证据分级映射（research.md → 本体表达，绝不混级）：
  [一手正史文献] 《宋史》卷272杨延昭传 → TextualFact + VERIFIED（L2 正史列传）
  [一手正史文献] 《清圣祖实录》卷46、《清史稿》卷166 → TextualFact + VERIFIED（L2 正史实录）
  [官书政书] 《钦定日下旧闻考》卷76 → TextualFact + VERIFIED（L2/L3 官书）
  [民国实测地图] 1915《实测京师四郊图》 → 记录式转录 Fact（L2 档案地图）

核心红线与负控制：
  NC1: 「杨六郎曾在此驻军挂甲」必须为 DISPROVEN（宋史确证镇守河北三关，海淀属辽境）；
  NC2: 「挂甲屯即吴应熊额驸城遗址」为 VERIFIED（日下旧闻考官修正书直核）；
  NC3: 「额驸城地面建筑今仍完整保存」必须为 DISPROVEN（清乾隆时已仅存聚落）。

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
    source_by_title("宋史"),
    source_by_title("钦定日下旧闻考"),
    source_by_title("清圣祖仁皇帝实录"),
    source_by_title("清史稿"),
    source_by_title("实测京师四郊图（1915）"),
]

DIVISIONS: List[SourceDivision] = [
    SourceDivision(id="div_ss272_yangyanzhao", source_id="src_songshi",
                   volume_number="卷二百七十二", section_title="列传第三十一·杨延昭传"),
    SourceDivision(id="div_rxjwk76_guajiatun", source_id="src_rxjwkc",
                   volume_number="卷七十六", section_title="国朝苑囿·畅春园三·挂甲屯"),
    SourceDivision(id="div_szsl46_wuyingxiong", source_id="src_shengzushilu",
                   volume_number="卷四十六", section_title="康熙十三年夏四月庚辰"),
    SourceDivision(id="div_qsg166_gongzhu", source_id="src_qingshigao",
                   volume_number="卷一百六十六", section_title="表第六·公主表·太宗第十四女"),
    SourceDivision(id="div_sjst1915_guajiatun", source_id="src_jingshi_sijiaotu_1915",
                   volume_number="京西幅", section_title="万泉河以北·挂甲屯"),
]


# ==================================================================
# 文本事实层（Textual Facts）
# ==================================================================

FACTS: List[TextualFact] = [
    TextualFact(
        id="fact_songshi_yangyanzhao",
        division_id="div_ss272_yangyanzhao",
        verbatim_quote="延昭本名延朗莫州清苑人在邊防二十餘年繕治障塞契丹憚之目為楊六郎真宗時知保州定州高陽關",
        attested_string="延昭……在邊防二十餘年，繕治障塞，契丹憚之，目為楊六郎",
        source_year=_dt(999, "dt_ss_yyz"),
        translator_note="宋史确证杨延昭镇守河北三关，边防在保州高阳关一线（L2正史列传）。",
    ),
    TextualFact(
        id="fact_rxjwk_guajiatun_efu",
        division_id="div_rxjwk76_guajiatun",
        verbatim_quote="掛甲屯在海淀西北世傳吳應熊額駙府第遺址在此俗亦稱額駙城臣等謹按掛甲屯去暢春園不數里相傳吳應熊第遺址即其處今但存聚落名額駙城者蓋沿俗稱也",
        attested_string="掛甲屯在海淀西北，世傳吳應熊額駙府第遺址在此，俗亦稱額駙城",
        source_year=_dt(1783, "dt_rx_gjt"),
        translator_note="日下旧闻考确证挂甲屯即吴应熊额驸府第遗址，俗称额驸城（L2/L3官书）。",
    ),
    TextualFact(
        id="fact_szsl_wuyingxiong_reb",
        division_id="div_szsl46_wuyingxiong",
        verbatim_quote="康熙十三年夏四月庚辰平西王吳三桂反少保兼太子太保一等子吳應熊及其子吳世霖著即處絞其母及諸庶子免死給恪純長公主為奴",
        attested_string="吳應熊……著即處絞……給恪純長公主為奴",
        source_year=_dt(1674, "dt_szsl_wyx"),
        translator_note="清圣祖实录确证康熙十三年吴三桂反叛，吴应熊在京伏诛（L2正史实录）。",
    ),
    TextualFact(
        id="fact_qsg_kechun_gongzhu",
        division_id="div_qsg166_gongzhu",
        verbatim_quote="太宗第十四女和碩恪純長公主太宗庶妃奇壘氏生順治十年封和碩公主下嫁吳應熊康熙十三年應熊以謀叛伏誅四十三年公主薨年六十三",
        attested_string="順治十年，封和碩公主，下嫁吳應熊",
        source_year=_dt(1653, "dt_qsg_kc"),
        translator_note="清史稿确证顺治十年皇太极十四女和硕恪纯长公主下嫁吴应熊（L2正史官书）。",
    ),
    TextualFact(
        id="fact_sjst1915_guajiatun",
        division_id="div_sjst1915_guajiatun",
        verbatim_quote="民国四年（1915）北洋陆军测地局实测五万分之一《实测京师四郊图》京西幅，万泉河北侧、畅春园西侧工整标绘「掛甲屯」。",
        attested_string="掛甲屯",
        source_year=_dt(1915, "dt_1915_gjt"),
        translator_note="1915年北洋测地局实测五万分之一图正式标绘「掛甲屯」（L2档案地图）。",
    ),
]


# ==================================================================
# 空间实体与指称
# ==================================================================

ENTITIES: List[PersistentSpatialEntity] = [
    PersistentSpatialEntity(
        id="ent_guajiatun",
        kind=PhysicalThingKind.SETTLEMENT_AREA,
        canonical_label="挂甲屯（海淀万泉河北岸、畅春园西侧古聚落，清初吴应熊额驸府第遗址所在地）",
    ),
    PersistentSpatialEntity(
        id="ent_efucheng_site",
        kind=PhysicalThingKind.SETTLEMENT_AREA,
        canonical_label="额驸城遗址（清初吴应熊尚和硕恪纯长公主之京西赐第，俗称额驸城）",
    ),
]

ENTITIES_MAP: Dict[str, PersistentSpatialEntity] = {e.id: e for e in ENTITIES}

APPELLATIONS: List[Appellation] = [
    Appellation(
        id="app_gjt_standard",
        label="挂甲屯",
        kind=AppellationKind.OFFICIAL,
        valid_time_span=_ts(1674, 2026, "ts_app_gjt"),
        attesting_fact_ids=["fact_sjst1915_guajiatun"],
    ),
    Appellation(
        id="app_gjt_trad",
        label="掛甲屯",
        kind=AppellationKind.OFFICIAL,
        valid_time_span=_ts(1783, 1915, "ts_app_gjt_trad"),
        attesting_fact_ids=["fact_rxjwk_guajiatun_efu", "fact_sjst1915_guajiatun"],
    ),
    Appellation(
        id="app_efucheng",
        label="额驸城",
        kind=AppellationKind.VULGAR,
        valid_time_span=_ts(1653, 1783, "ts_app_efc"),
        attesting_fact_ids=["fact_rxjwk_guajiatun_efu"],
    ),
]

STATES: List[HistoricalFeatureState] = [
    HistoricalFeatureState(
        id="state_efucheng_early_qing",
        entity_id="ent_efucheng_site",
        label="清初：吴应熊额驸府第（额驸城）",
        time_span=_ts(1653, 1674, "ts_st_efc"),
        geometry="海淀镇西北数里，万泉河北岸，规制宏丽，俗呼额驸城",
        function="清初平西王之子吴应熊尚皇十四女之京西赐第别业，置家属仆从三百名",
        evidence_fact_ids=["fact_rxjwk_guajiatun_efu", "fact_szsl_wuyingxiong_reb"],
    ),
    HistoricalFeatureState(
        id="state_guajiatun_mid_qing",
        entity_id="ent_guajiatun",
        label="清中叶：万泉河畔御园西侧聚落",
        time_span=_ts(1674, 1911, "ts_st_gjt_mid"),
        geometry="畅春园西侧，南临万泉河，额驸第废而为村落",
        function="清代西郊皇家园林外围居住与服务聚落",
        evidence_fact_ids=["fact_rxjwk_guajiatun_efu", "fact_sjst1915_guajiatun"],
    ),
    HistoricalFeatureState(
        id="state_guajiatun_modern",
        entity_id="ent_guajiatun",
        label="民国至今：实测定名挂甲屯",
        time_span=_ts(1915, 2026, "ts_st_gjt_mod"),
        geometry="海淀区燕园街道辖区，南临万泉河路，北依圆明园",
        function="历史古村与现代居住街区，朱自清曾居于此",
        evidence_fact_ids=["fact_sjst1915_guajiatun"],
    ),
]

TRANSFORMATIONS: List[PlaceTransformation] = [
    PlaceTransformation(
        id="trans_efucheng_build",
        entity_id="ent_efucheng_site",
        transformation=PlaceTransformationEvent.CONSTRUCTED,
        time_span=_ts(1653, 1653, "ts_trans_efc"),
        resulting_state_id="state_efucheng_early_qing",
        resulting_condition="顺治十年吴应熊尚和硕恪纯长公主建府于海淀西郊",
        evidence_fact_ids=["fact_qsg_kechun_gongzhu"],
    ),
    PlaceTransformation(
        id="trans_wuyingxiong_fall",
        entity_id="ent_guajiatun",
        transformation=PlaceTransformationEvent.REBUILT,
        time_span=_ts(1674, 1674, "ts_trans_fall"),
        resulting_state_id="state_guajiatun_mid_qing",
        resulting_condition="康熙十三年吴应熊伏诛府第抄没荒废，渐成平民聚落挂甲屯",
        evidence_fact_ids=["fact_szsl_wuyingxiong_reb", "fact_rxjwk_guajiatun_efu"],
    ),
]

IDENTITIES: List[DiachronicIdentityAssertion] = [
    DiachronicIdentityAssertion(
        id="dia_efucheng_guajiatun",
        relation=IdentityRelation.SUCCESSOR,
        subject_entity_ids=["ent_efucheng_site", "ent_guajiatun"],
        time_span=_ts(1674, 1915, "ts_dia_efc"),
        evidence_fact_ids=["fact_rxjwk_guajiatun_efu"],
        status=EpistemicStatus.VERIFIED,
        is_orthogonal_to_state_change=True,
    ),
]

REFERENCES: List[ReferentialAssertion] = [
    ReferentialAssertion(
        id="ref_gjt_standard",
        appellation_id="app_gjt_standard",
        referent_entity_id="ent_guajiatun",
        time_span=_ts(1674, 2026, "ts_ref_gjt"),
        evidence_fact_ids=["fact_sjst1915_guajiatun"],
        status=EpistemicStatus.VERIFIED,
    ),
    ReferentialAssertion(
        id="ref_gjt_trad",
        appellation_id="app_gjt_trad",
        referent_entity_id="ent_guajiatun",
        time_span=_ts(1783, 1915, "ts_ref_gjt_trad"),
        evidence_fact_ids=["fact_rxjwk_guajiatun_efu", "fact_sjst1915_guajiatun"],
        status=EpistemicStatus.VERIFIED,
    ),
    ReferentialAssertion(
        id="ref_efucheng",
        appellation_id="app_efucheng",
        referent_entity_id="ent_efucheng_site",
        time_span=_ts(1653, 1783, "ts_ref_efc"),
        evidence_fact_ids=["fact_rxjwk_guajiatun_efu"],
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
        id="prop_efucheng_site_guajiatun",
        statement="挂甲屯在清代为吴应熊额驸府第遗址，民间俗称额驸城。",
        derived_from_fact_ids=["fact_rxjwk_guajiatun_efu"],
        inferred_subject_id="ent_guajiatun",
        inference_method="《钦定日下旧闻考》卷七十六官修正书明确记载（L2/L3）。",
        alternative_explanations=[],
    ),
    Proposition(
        id="prop_wuyingxiong_princess_marriage",
        statement="清顺治十年（1653）清太宗十四女和硕恪纯长公主下嫁平西王之子吴应熊。",
        derived_from_fact_ids=["fact_qsg_kechun_gongzhu", "fact_szsl_wuyingxiong_reb"],
        inferred_subject_id="ent_efucheng_site",
        inference_method="正史《清圣祖实录》与《清史稿》公主表确凿记录（L2）。",
        alternative_explanations=[],
    ),
    Proposition(
        id="prop_yangyanzhao_hebei_defense",
        statement="宋代名将杨延昭终身镇守河北三关与高阳关一线，从未在辽境幽州海淀驻兵。",
        derived_from_fact_ids=["fact_songshi_yangyanzhao"],
        inferred_subject_id="ent_guajiatun",
        inference_method="正史《宋史·杨延昭传》确证边防在河北，海淀当时属辽国腹地（L2）。",
        alternative_explanations=[],
    ),

    # 负控制命题
    Proposition(
        id="prop_yang_liulang_guajia_legend",
        statement="宋将杨六郎曾在此地屯兵征战，解下铠甲挂在树上，故名挂甲屯。",
        derived_from_fact_ids=[],
        inferred_subject_id="ent_guajiatun",
        inference_method="被正史《宋史》边防地理彻底否证：宋辽分界在白沟河以南，杨六郎从未来过海淀西郊，挂甲纯属民间评话演义附会。",
        alternative_explanations=["明清说书弹词流行后的民间地名附会"],
    ),
    Proposition(
        id="prop_efucheng_existing_aboveground",
        statement="吴应熊额驸城宏丽府第建筑完整保存至今。",
        derived_from_fact_ids=["fact_rxjwk_guajiatun_efu"],
        inferred_subject_id="ent_efucheng_site",
        inference_method="被《日下旧闻考》按语确证否证：乾隆时按语已注「今但存聚落，名額駙城者蓋沿俗稱也」，地面府第早已废毁。",
        alternative_explanations=["府第废而聚落存"],
    ),
]

ADOPTIONS: List[BeliefAdoption] = [
    BeliefAdoption(
        proposition_id="prop_efucheng_site_guajiatun",
        status=EpistemicStatus.VERIFIED,
        confidence=1.0,
        adopted_by="E23 官修政书直核",
        adopted_at=_dt(2026, "dt_ad_efc"),
        rationale="日下旧闻考卷76确证挂甲屯即吴应熊府第遗址，俗称额驸城。",
    ),
    BeliefAdoption(
        proposition_id="prop_wuyingxiong_princess_marriage",
        status=EpistemicStatus.VERIFIED,
        confidence=1.0,
        adopted_by="E23 正史书证",
        adopted_at=_dt(2026, "dt_ad_marry"),
        rationale="清实录与清史稿正史互证顺治十年尚主实录。",
    ),
    BeliefAdoption(
        proposition_id="prop_yangyanzhao_hebei_defense",
        status=EpistemicStatus.VERIFIED,
        confidence=1.0,
        adopted_by="E23 正史列传直核",
        adopted_at=_dt(2026, "dt_ad_yyz"),
        rationale="宋史杨延昭传确证边防在河北，从未涉足幽州西郊。",
    ),
    BeliefAdoption(
        proposition_id="prop_yang_liulang_guajia_legend",
        status=EpistemicStatus.DISPROVEN,
        confidence=0.95,
        adopted_by="E23 负控制 V-NC01",
        adopted_at=_dt(2026, "dt_ad_nc01"),
        rationale="杨延昭镇守河北三关，海淀属辽国南京腹地，杨六郎挂甲纯属民间演义神话，严禁作为史实叙述。",
        refuting_fact_ids=["fact_songshi_yangyanzhao"],
    ),
    BeliefAdoption(
        proposition_id="prop_efucheng_existing_aboveground",
        status=EpistemicStatus.DISPROVEN,
        confidence=0.95,
        adopted_by="E23 负控制 V-NC03",
        adopted_at=_dt(2026, "dt_ad_nc03"),
        rationale="日下旧闻考按语确证乾隆时府第遗址已无存，仅存聚落，严禁宣称府第建筑完整保存。",
        refuting_fact_ids=["fact_rxjwk_guajiatun_efu"],
    ),
]
