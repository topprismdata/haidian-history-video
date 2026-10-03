# -*- coding: utf-8 -*-
"""haidian_kg/calibration/dajuesi.py
大觉寺／清水院 时序否证层 —— 海淀历史地名知识库 E24 入库模块

模块定位（**不重复建模**）:
`haidian_kg/calibration/xishan.py` 已建成 `ent_xs_dajuesi`（大觉寺）、`ent_xs_liaobei`
（辽碑）、`ent_xs_beianhe`（北安河）等实体与 29 条事实。本模块**只补 E24 特有的
「时序否证层」**——把「通行说：大觉寺始建于金章宗」立为 DISPROVEN 假说节点，
并把「金章宗西山八院」标为明人追述（CONTESTED）、「白玉兰植栽年代」标为
UNSUBSTANTIATED。所有实体经 DiachronicIdentityAssertion 与 xishan 模块同指挂钩。

证据分级:
  [一手金石实物] 辽咸雍四年(1068)《旸台山清水院创造藏经记》碑（xishan 已录，本模块引用）
  [明人著述]     《帝京景物略》大觉寺条
  [清官书按语]   《钦定日下旧闻考》卷一百六

核心红线:
  NC1: 「始建于金章宗」→ DISPROVEN（辽碑 1068 早于金章宗在位 1189–1208 共 121 年）
  NC2: 「金章宗西山八院」→ CONTESTED（明人追述，非金代文献自述）
  NC3: 「白玉兰植栽年代」→ UNSUBSTANTIATED（无文献与树木档案）
  NC4: 「坐西朝东」两层分离（辽代方位记载 ≠ 今日建筑测绘层）

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
# 书源与篇卷（仅登记本集新引用的篇卷，实体归 xishan 模块）
# ==================================================================

SOURCES: List[HistoricalSource] = [
    source_by_title("钦定日下旧闻考"),
]

DIVISIONS: List[SourceDivision] = [
    SourceDivision(id="div_e24_rxjwkc106_dajuesi", source_id="src_rxjwkc",
                   volume_number="卷一百六", section_title="郊坰西十六·大觉寺条"),
]


# ==================================================================
# 文本事实层（E24 专属：本模块只立时序否证所需的三条书证）
# ==================================================================

FACTS: List[TextualFact] = [
    # 🔴 NC1 的决定性证据：辽碑「院之興止於近代」
    TextualFact(
        id="fact_e24_liao_bei_jin_jin",
        division_id="div_e24_rxjwkc106_dajuesi",
        verbatim_quote=("山之名傳諸前古院之興止於近代將構勝緣旋逢信士"
                        "今優婆塞南陽鄧公從貴善根生得浄行日嚴咸雍四年三月"
                        "舍錢三十萬葺諸僧舍又五十萬募同志印大藏經凡五百七十九帙"
                        "創內外藏而龕措之蒇事既周求為之記"),
        attested_string="院之興止於近代",
        source_year=_dt(1068, "dt_e24_liao_bei"),
        translator_note=(
            "🔴 本集最重要的一条书证（L1 一手金石）。辽咸雍四年（1068）《旸台山清水院"
            "创造藏经记》碑（僧志延撰，今存大觉寺）明载「院之興止於近代」——"
            "立碑时清水院已存在且「兴于近代」（距 1068 不远）。"
            "金章宗在位 1189–1208，晚于立碑 121 年，「大觉寺始建于金章宗」不成立。"
        ),
    ),
    # NC2：八院说是明人追述
    TextualFact(
        id="fact_e24_djjwl_bayuan",
        division_id="div_e24_rxjwkc106_dajuesi",
        verbatim_quote="金章宗西山八院寺其清水院也",
        attested_string="金章宗西山八院，寺其清水院也",
        source_year=_dt(1600, "dt_e24_djjwl"),
        translator_note=(
            "《帝京景物略》（明万历间成书）大觉寺条。此为 16 世纪明人对辽金旧事的"
            "追述与归纳，属明人著述层（L3），非金代文献自述。"
        ),
    ),
    # 三废三兴的清官书按语
    TextualFact(
        id="fact_e24_qingxiangzong_xiulu",
        division_id="div_e24_rxjwkc106_dajuesi",
        verbatim_quote=("大覺寺康熙五十九年世宗潛邸時特加修葺乾隆十二年皇上發帑重修"
                        "寺內彌勒殿額曰圓證妙果正殿額曰無去來處無量壽佛殿額曰動靜等觀"
                        "大悲壇額曰最上法門皆皇上御書"),
        attested_string="康熙五十九年世宗潛邸時特加修葺，乾隆十二年皇上發帑重修",
        source_year=_dt(1783, "dt_e24_qing_an"),
        translator_note=(
            "《钦定日下旧闻考》卷一百六臣等谨按（清官书按语，L2/L3）。载康熙五十九年"
            "（1720）世宗潜邸时特加修葺、乾隆十二年（1747）发帑重修，"
            "并载世宗潜邸时已「特加修葺」——证明明末废毁后确经清代两度重兴。"
        ),
    ),
]


# ==================================================================
# 空间实体（仅 E24 专属：辽代清水院状态锚点；主实体挂 xishan 同指断言）
# ==================================================================

ENTITIES: List[PersistentSpatialEntity] = [
    PersistentSpatialEntity(
        id="ent_e24_qingshuiyuan_liao",
        kind=PhysicalThingKind.RELIGIOUS_PRECINCT,
        canonical_label=("清水院（辽咸雍四年1068碑所载，旸台山麓，坐西朝东；"
                         "后为明灵泉寺、清大觉寺之基址）"),
    ),
]

ENTITIES_MAP: Dict[str, PersistentSpatialEntity] = {e.id: e for e in ENTITIES}

APPELLATIONS: List[Appellation] = [
    Appellation(
        id="app_e24_qingshuiyuan",
        label="清水院",
        kind=AppellationKind.OLD_NAME,
        valid_time_span=_ts(1068, 1428, "ts_app_e24_qsy"),
        attesting_fact_ids=["fact_e24_liao_bei_jin_jin"],
    ),
]

STATES: List[HistoricalFeatureState] = [
    HistoricalFeatureState(
        id="state_e24_qingshuiyuan_liao",
        entity_id="ent_e24_qingshuiyuan_liao",
        label="辽：清水院（1068 碑存，坐西朝东）",
        time_span=_ts(1068, 1125, "ts_st_e24_qsy"),
        geometry=("旸台山麓（今阳台山），幽都地界；据辽碑「院之興止於近代」"
                  "知辽代已成院；方位记「坐西朝东」"),
        function=("藏经结社：施主南陽鄧公從貴舍钱三十万葺僧舍、又五十万募印大藏经"
                  "五百七十九帙，创内外藏。印藏规模五百七十九帙为辽代雕印大藏经实物指标"),
        evidence_fact_ids=["fact_e24_liao_bei_jin_jin"],
    ),
]

TRANSFORMATIONS: List[PlaceTransformation] = []

IDENTITIES: List[DiachronicIdentityAssertion] = [
    # 与 xishan 模块的 ent_xs_dajuesi 同指：辽清水院 = 明灵泉寺 = 清大觉寺
    DiachronicIdentityAssertion(
        id="dia_e24_qsy_to_dajuesi",
        relation=IdentityRelation.SUCCESSOR,
        subject_entity_ids=["ent_e24_qingshuiyuan_liao", "ent_xs_dajuesi"],
        time_span=_ts(1068, 2026, "ts_dia_e24"),
        evidence_fact_ids=["fact_e24_liao_bei_jin_jin", "fact_e24_qingxiangzong_xiulu"],
        status=EpistemicStatus.VERIFIED,
        is_orthogonal_to_state_change=True,
    ),
]

REFERENCES: List[ReferentialAssertion] = [
    ReferentialAssertion(
        id="ref_e24_qingshuiyuan",
        appellation_id="app_e24_qingshuiyuan",
        referent_entity_id="ent_e24_qingshuiyuan_liao",
        time_span=_ts(1068, 1428, "ts_ref_e24_qsy"),
        evidence_fact_ids=["fact_e24_liao_bei_jin_jin"],
        status=EpistemicStatus.VERIFIED,
    ),
]

AGGREGATES: List[PlaceAggregate] = []


# ==================================================================
# 命题层（E24 核心：时序否证）与采信层
# ==================================================================

PROPOSITIONS: List[Proposition] = [
    # —— NC1：通行说被证伪（本系列第三例时序否证）——
    Proposition(
        id="prop_e24_jinzhangzong_founder",
        statement="大觉寺（清水院）始建于金章宗年间（金 1189–1208）。",
        derived_from_fact_ids=["fact_e24_liao_bei_jin_jin"],
        inferred_subject_id="ent_e24_qingshuiyuan_liao",
        inference_method=(
            "时序否证：辽咸雍四年（1068）《旸台山清水院创造藏经记》碑明载「院之興止於近代」，"
            "立碑时清水院已存在；金章宗在位 1189–1208，晚于立碑 121 年。"
            "通行说「大觉寺始建于金章宗」被出土金石一手实物直接证伪。"
            "本系列继 E21（元史葬地伪引文）、E23（杨六郎挂甲附会）之后的第三例时序否证。"
        ),
        alternative_explanations=[
            "「金清水院故址」是清人（乾隆御制碑）对辽代旧址的追认，不是创建年",
            "通行说可能源自明人《帝京景物略》对辽金旧事的追述（见 prop_e24_bayuan_mingren）",
        ],
    ),
    # —— NC2：八院说分层为明人追述 ——
    Proposition(
        id="prop_e24_bayuan_mingren",
        statement="清水院是金章宗所设「西山八院」之一（此说由明人归纳，非金代文献自述）。",
        derived_from_fact_ids=["fact_e24_djjwl_bayuan"],
        inferred_subject_id="ent_e24_qingshuiyuan_liao",
        inference_method=(
            "来源分层：《帝京景物略》（明万历间成书）载「金章宗西山八院，寺其清水院也」。"
            "此为 16 世纪明人对辽金旧事的追述与归纳（L3 明人著述层），"
            "不得写成金代文献自述。乾隆御制碑亦只说「金清水院故址」，未系于金章宗。"
        ),
        alternative_explanations=[
            "金章宗确曾营建西山八院（另说），但把清水院归入其中属明人归纳，缺乏金代直接书证",
        ],
    ),
    # —— NC3：白玉兰植栽年代无据 ——
    Proposition(
        id="prop_e24_magnolia_age",
        statement="大觉寺四宜堂前白玉兰为辽代所植（树龄逾千年）。",
        derived_from_fact_ids=[],
        inferred_subject_id="ent_xs_dajuesi",
        inference_method=(
            "无据：俗传辽植/清植诸说分歧，无文献与树木档案确证。本片只记「四宜堂前"
            "白玉兰一株，为寺中著名景观」，严禁列任何具体树龄或植栽年代。"
        ),
        alternative_explanations=["清代移植", "近代移栽", "年代不可考"],
    ),
    # —— 三废三兴（清官书按语正层）——
    Proposition(
        id="prop_e24_three_rebuilds",
        statement="大觉寺明万历末废毁（《帝京景物略》「今圯矣」），"
                  "清康熙五十九年（1720）世宗潜邸时特加修葺，乾隆十二年（1747）发帑重修。",
        derived_from_fact_ids=["fact_e24_qingxiangzong_xiulu"],
        inferred_subject_id="ent_xs_dajuesi",
        inference_method=(
            "明末废毁见《帝京景物略》「今圯矣」（另条书证，见 research.md §1.2）；"
            "清代两度重修见《日下旧闻考》卷一百六臣等谨按（L2/L3 清官书）。"
        ),
        alternative_explanations=[],
    ),
]

ADOPTIONS: List[BeliefAdoption] = [
    BeliefAdoption(
        proposition_id="prop_e24_jinzhangzong_founder",
        status=EpistemicStatus.DISPROVEN,
        confidence=0.97,
        adopted_by="E24 负控制 V-NC01（辽碑时序优先）",
        adopted_at=_dt(2026, "dt_ad_e24_nc1"),
        rationale=(
            "辽咸雍四年（1068）碑明载「院之興止於近代」，清水院辽代已成；"
            "金章宗在位晚 121 年。通行说 DISPROVEN。"
        ),
        refuting_fact_ids=["fact_e24_liao_bei_jin_jin"],
    ),
    BeliefAdoption(
        proposition_id="prop_e24_bayuan_mingren",
        status=EpistemicStatus.CONTESTED,
        confidence=0.6,
        adopted_by="E24 负控制 V-NC02（八院说分层）",
        adopted_at=_dt(2026, "dt_ad_e24_nc2"),
        rationale=(
            "「金章宗西山八院」为明人《帝京景物略》追述归纳，非金代文献自述。"
            "正片可用此说作文化背景，严禁写成金代史实。"
        ),
    ),
    BeliefAdoption(
        proposition_id="prop_e24_magnolia_age",
        status=EpistemicStatus.UNSUBSTANTIATED,
        confidence=0.95,
        adopted_by="E24 负控制 V-NC03（白玉兰不列年代）",
        adopted_at=_dt(2026, "dt_ad_e24_nc3"),
        rationale="无文献与树木档案确证，严禁列植栽年代或树龄。",
    ),
    BeliefAdoption(
        proposition_id="prop_e24_three_rebuilds",
        status=EpistemicStatus.VERIFIED,
        confidence=0.9,
        adopted_by="E24 清官书按语正层",
        adopted_at=_dt(2026, "dt_ad_e24_rebuild"),
        rationale="《日下旧闻考》卷一百六臣等谨按确证康熙、乾隆两度重修。",
    ),
]
