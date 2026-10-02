"""
haidian_kg/calibration/settlements.py
聚落类词条：大有庄 / 西三旗 / 青龙桥 / 娘娘府·董四墓

这一批的独特价值：交付档案已含 **证据分级 L1–L5 + 高危禁用清单**
（GPT 两轮复查后的降格结论），此前这些结论只存在于散文里，
无法被机器检查。本模块把它们正式接入本体的认识论层。

四级核心纪律（来自 E7 西三旗、E3 青龙桥、E2 大有庄、E9 娘娘府）：
  1. 「西三旗的旗来自明代小旗，不是清代八旗」——同名异物，两套制度不可混说
  2. 「青龙桥」名称年代存争议：元代白浮堰经过（强证），桥体年代（争议）
  3. 「七十二府」是民间俗称，无 72 座官方名录证据
  4. 「大有庄」乾隆赐名是传说，官方只证明乾隆朝已用此名

数据全部取自已冻结的交付 research.md，不凭印象补写。
"""
from typing import List

from ..ontology.temporal import (
    CalibrationTable, DatePoint, Era, GregorianDate, ReignYear, TimeSpan,
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
from .bibliography import source_by_title

CAL = CalibrationTable.CN_ASTRONOMICAL_ALMANAC


def _dt(y, tag, reign=None, precision="year"):
    return DatePoint(id=tag, label=str(y), precision=precision, reign_year=reign,
                     gregorian=GregorianDate(year=y, calibration=CAL))


def _ts(y1, y2, tag):
    return TimeSpan(id=tag, label="%d-%d" % (y1, y2),
                    begin=_dt(y1, tag + "_b"), end=_dt(y2, tag + "_e"))


# ==================================================================
# 1. 文献与篇卷
# ==================================================================

SOURCES: List[HistoricalSource] = [
    source_by_title("钦定日下旧闻考"),
    source_by_title("明史"),
    source_by_title("北京市三山五园传统地名保护名录"),
    source_by_title("海淀区地名志"),
]

DIVISIONS: List[SourceDivision] = [
    SourceDivision(id="div_rxjwkc100_xijiaojing", source_id="src_rxjwkc",
                   volume_number="卷100", section_title="西郊景物"),
    SourceDivision(id="div_mingshi_bingzhi", source_id="src_mingshi",
                   volume_number="兵志", section_title="卫所编制"),
    SourceDivision(id="div_mingyitongzhi", source_id="src_mingshi",
                   volume_number="地理志", section_title="一统志引文"),
    SourceDivision(id="div_diquminglu_xisanqi", source_id="src_hd_diqumingzhi",
                   volume_number="地名志", section_title="西三旗条"),
    SourceDivision(id="div_2024_minglu_qinglongqiao", source_id="src_2024_minglu",
                   volume_number="第一批", section_title="青龙桥条（名称出现年代）"),
]


# ==================================================================
# 2. 文本事实（只收 L1 官书/档案级）
# ==================================================================

FACTS: List[TextualFact] = [
    # ---- 大有庄：乾隆朝官书已用此名，御道条为全片最硬证据 ----
    TextualFact(
        id="tf_dyz_100", division_id="div_rxjwkc100_xijiaojing",
        verbatim_quote="達官村西南里許為大有莊，莊前為御道，道北有觀音菴、關帝廟。",
        attested_string="大有莊",
    ),
    TextualFact(
        id="tf_dyz_ming_objects", division_id="div_rxjwkc100_xijiaojing",
        verbatim_quote="村中觀音菴存明嘉靖四十年鐵爐、萬曆十九年鐵磬；關帝廟存成化二年鐵鐘。",
        attested_string="鐵磬",
    ),
    # ---- 西三旗：明代卫所小旗编制 ----
    TextualFact(
        id="tf_xsq_weisuo", division_id="div_mingshi_bingzhi",
        verbatim_quote="每百戶轄總旗二各五十人、小旗十各十人。",
        attested_string="小旗",
    ),
    TextualFact(
        id="tf_xsq_diquzhi", division_id="div_diquminglu_xisanqi",
        verbatim_quote="西三旗因清河以北牧馬場西側三個小旗駐點得名，西二旗即兩個小旗駐點。",
        attested_string="小旗駐點",
    ),
    # ---- 青龙桥：旧地名与通称 ----
    TextualFact(
        id="tf_qlq_100", division_id="div_rxjwkc100_xijiaojing",
        verbatim_quote="七里泊、碾莊係舊地名，今土人惟通稱曰青龍橋。",
        attested_string="青龍橋",
    ),
    TextualFact(
        id="tf_qlq_mingyitongzhi", division_id="div_mingyitongzhi",
        verbatim_quote="青龍橋跨其上。",
        attested_string="跨其上",
    ),
    TextualFact(
        id="tf_qlq_daotianchang", division_id="div_rxjwkc100_xijiaojing",
        verbatim_quote="康熙五十三年，內務府於青龍橋設稻田廠，有倉署、倉廒、碾房，经理官種稻田。",
        attested_string="稻田廠",
    ),
    # ---- 娘娘府/董四墓：1951 考古与 2022-23 发掘 ----
    TextualFact(
        id="tf_dsm_jinshan", division_id="div_rxjwkc100_xijiaojing",
        verbatim_quote="金山為明代皇家陵墓集中之區，景泰帝、諸王、公主及諸妃嬪葬此。",
        attested_string="金山",
    ),
]


# ==================================================================
# 3. 实体
# ==================================================================

ENTITIES: List[PersistentSpatialEntity] = [
    PersistentSpatialEntity(id="ent_dayouzhuang", kind=PhysicalThingKind.SETTLEMENT_AREA,
                            canonical_label="大有庄"),
    PersistentSpatialEntity(id="ent_xisanqi", kind=PhysicalThingKind.SETTLEMENT_AREA,
                            canonical_label="西三旗"),
    PersistentSpatialEntity(id="ent_qinglongqiao", kind=PhysicalThingKind.SETTLEMENT_AREA,
                            canonical_label="青龙桥镇"),
    PersistentSpatialEntity(id="ent_qinglongqiao_gate", kind=PhysicalThingKind.HYDRAULIC_STRUCTURE,
                            canonical_label="青龙桥闸（昆明湖溢洪枢纽）"),
    PersistentSpatialEntity(id="ent_niangniangfu", kind=PhysicalThingKind.SETTLEMENT_AREA,
                            canonical_label="娘娘府"),
    PersistentSpatialEntity(id="ent_dongsimu", kind=PhysicalThingKind.TOMB_CLUSTER,
                            canonical_label="董四墓（明墓群）"),
    PersistentSpatialEntity(id="ent_jinshan", kind=PhysicalThingKind.TOMB_CLUSTER,
                            canonical_label="金山明代皇家墓葬区"),
]


# ==================================================================
# 4. 历时状态
# ==================================================================

STATES: List[HistoricalFeatureState] = [
    # 大有庄：乾隆朝已用此名，庄前御道
    HistoricalFeatureState(
        id="st_dyz_qianlong", entity_id="ent_dayouzhuang",
        time_span=_ts(1736, 1911, "ts_d1"),
        geometry="村落，庄前为御道，道北有观音庵、关帝庙",
        material="村庙砖木",
        function="为皇家园林、官仓与营房服务的村落（官书体例的服务性聚落）",
        evidence_fact_ids=["tf_dyz_100", "tf_dyz_ming_objects"],
    ),
    # 西三旗：明代牧马场驻点
    HistoricalFeatureState(
        id="st_xsq_ming", entity_id="ent_xisanqi",
        time_span=_ts(1400, 1644, "ts_x1"),
        geometry="清河以北牧马养马场的驻点聚落",
        material="土坯营房、马厩",
        function="明代卫所牧马养马场驻点（小旗编制，非清代八旗）",
        evidence_fact_ids=["tf_xsq_weisuo", "tf_xsq_diquzhi"],
    ),
    # 青龙桥闸：乾隆扩昆明湖后的溢洪枢纽
    HistoricalFeatureState(
        id="st_qlqgate_qianlong", entity_id="ent_qinglongqiao_gate",
        time_span=_ts(1750, 1860, "ts_q1"),
        geometry="昆明湖西北端溢洪干渠上的闸，绕万寿山西麓接清河",
        material="闸门与渠岸",
        function="昆明湖溢洪枢纽，弘历称「昆明湖之尾闾」，内务府派员专管",
        evidence_fact_ids=["tf_qlq_daotianchang"],
    ),
    # 稻田厂：康熙五十三年设
    HistoricalFeatureState(
        id="st_qlq_daotian_1714", entity_id="ent_qinglongqiao",
        time_span=_ts(1714, 1860, "ts_q2"),
        geometry="稻田厂，有仓署、仓廒、碾房",
        material="仓廒砖木、碾房",
        function="内务府管理官种稻田、仓储与加工（非育种场）",
        evidence_fact_ids=["tf_qlq_daotianchang"],
    ),
    # 董四墓：1951 考古揭露
    HistoricalFeatureState(
        id="st_dsm_1951", entity_id="ent_dongsimu",
        time_span=_ts(1951, 1951, "ts_s1"),
        geometry="两座明墓：一号墓熹宗三妃合葬，二号墓神宗七嫔合葬",
        material="墓室砖石，出土银盆、凤冠",
        function="1951年中科院考古所发掘墓葬（身份基础强）",
        evidence_fact_ids=["tf_dsm_jinshan"],
    ),
]


# ==================================================================
# 5. 身份断言：同名不同制度
# ==================================================================

IDENTITIES: List[DiachronicIdentityAssertion] = [
    # 【E7 核心】西三旗的「旗」与清代八旗是两套制度，不是同一条演化线
    DiachronicIdentityAssertion(
        id="dia_xsq_flag_dual",
        subject_entity_ids=["ent_xisanqi"],
        relation=IdentityRelation.REPLACED_BY,
        time_span=_ts(1644, 1912, "ts_di1"),
        evidence_fact_ids=["tf_xsq_weisuo", "tf_xsq_diquzhi"],
        status=EpistemicStatus.VERIFIED,
        alternative_relations=[
            "地名志解释为明代小旗驻点（可对照，不可继承）",
            "清代西郊另有圆明园护军营等真八旗驻军体系，与之平行而非承袭",
        ],
    ),
    # 【E3 核心】青龙桥：白浮堰经过（强证）vs 桥体年代（争议）
    DiachronicIdentityAssertion(
        id="dia_qlq_bridge_age",
        subject_entity_ids=["ent_qinglongqiao"],
        relation=IdentityRelation.UNCERTAIN,
        time_span=TimeSpan(id="ts_di2", label="桥体年代存疑", open_begin=True,
                           begin=None, end=_dt(2026, "ts_di2e")),
        evidence_fact_ids=["tf_qlq_100", "tf_qlq_mingyitongzhi"],
        status=EpistemicStatus.CONTESTED,
        alternative_relations=[
            "元代白浮堰经过此带（证据强）",
            "现称青龙桥的桥体为郭守敬所建（证据不足）",
            "2024官方名录将「青龙桥」名称出现年代标为明代",
        ],
    ),
]


# ==================================================================
# 6. 名称与指称
# ==================================================================

APPELLATIONS: List[Appellation] = [
    Appellation(id="app_dyz", label="大有庄", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1736, 2026, "ts_n1"),
                attesting_fact_ids=["tf_dyz_100"]),
    Appellation(id="app_dyz_folk", label="穷八家", kind=AppellationKind.VULGAR,
                valid_time_span=_ts(1500, 1900, "ts_n2"),
                attesting_fact_ids=[]),
    Appellation(id="app_xsq", label="西三旗", kind=AppellationKind.GARRISON_CODE,
                valid_time_span=_ts(1400, 2026, "ts_n3"),
                attesting_fact_ids=["tf_xsq_diquzhi"]),
    Appellation(id="app_qlq", label="青龙桥", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1600, 2026, "ts_n4"),
                attesting_fact_ids=["tf_qlq_100", "tf_qlq_mingyitongzhi"]),
    Appellation(id="app_qili_po", label="七里泊", kind=AppellationKind.STREET_NAME,
                valid_time_span=TimeSpan(id="ts_n5", label="旧地名", open_begin=True,
                                        begin=None, end=_dt(1800, "ts_n5e")),
                attesting_fact_ids=["tf_qlq_100"]),
    Appellation(id="app_nianzhuang", label="碾庄", kind=AppellationKind.STREET_NAME,
                valid_time_span=TimeSpan(id="ts_n6", label="旧地名", open_begin=True,
                                        begin=None, end=_dt(1800, "ts_n6e")),
                attesting_fact_ids=["tf_qlq_100"]),
    Appellation(id="app_qishierfu", label="七十二府", kind=AppellationKind.FOLK_LEGEND,
                valid_time_span=_ts(1600, 2026, "ts_n7"),
                attesting_fact_ids=[]),
    Appellation(id="app_dongsimu_wrong", label="东四墓", kind=AppellationKind.TEXTUAL_CORRUPTION,
                valid_time_span=_ts(1700, 1900, "ts_n8"),
                attesting_fact_ids=[]),
]

REFERENCES: List[ReferentialAssertion] = [
    ReferentialAssertion(id="rr_dyz", appellation_id="app_dyz",
                         referent_entity_id="ent_dayouzhuang",
                         time_span=_ts(1736, 2026, "ts_r1"),
                         evidence_fact_ids=["tf_dyz_100"]),
    ReferentialAssertion(id="rr_dyz_folk", appellation_id="app_dyz_folk",
                         referent_entity_id="ent_dayouzhuang",
                         time_span=_ts(1500, 1900, "ts_r2"),
                         evidence_fact_ids=[],
                         status=EpistemicStatus.UNSUBSTANTIATED,
                         provenance="地方文史流传：乾隆朝之前称穷八家；无诏档依据，仅为俗称记忆"),
    ReferentialAssertion(id="rr_xsq", appellation_id="app_xsq",
                         referent_entity_id="ent_xisanqi",
                         time_span=_ts(1400, 2026, "ts_r3"),
                         evidence_fact_ids=["tf_xsq_diquzhi"]),
    ReferentialAssertion(id="rr_qlq", appellation_id="app_qlq",
                         referent_entity_id="ent_qinglongqiao",
                         time_span=_ts(1600, 2026, "ts_r4"),
                         evidence_fact_ids=["tf_qlq_100"]),
    ReferentialAssertion(id="rr_nnf", appellation_id="app_qishierfu",
                         referent_entity_id="ent_jinshan",
                         time_span=_ts(1600, 2026, "ts_r5"),
                         evidence_fact_ids=[],
                         status=EpistemicStatus.FOLK_LEGEND,
                         provenance="「一溜边山七十二府」为民间俗称；嘉靖奏疏与《琉璃厂杂记》均作二十余处，七十二为概数"),
]


# ==================================================================
# 7. 断言与采信：把交付档案的降格结论固化
# ==================================================================

PROPOSITIONS: List[Proposition] = [
    Proposition(
        id="prop_xsq_flag",
        statement="西三旗的「旗」来自明代卫所小旗（每旗十人），非清代八旗",
        derived_from_fact_ids=["tf_xsq_weisuo", "tf_xsq_diquzhi"],
        inferred_subject_id="ent_xisanqi",
        inference_method="《明史·兵志》卫所编制 + 地名志解释，二者可对照不可继承",
        alternative_relations=["清代西郊另有真八旗驻军体系，与之平行"],
    ),
    Proposition(
        id="prop_dyz_no_imperial_gift",
        statement="「乾隆赐名」为地方文史传说，官方只证明乾隆朝已用「大有庄」之名",
        derived_from_fact_ids=["tf_dyz_100"],
        inferred_subject_id="ent_dayouzhuang",
        inference_method="官书有御道条与村名，但无赐名诏书/御制诗/宫档",
        alternative_relations=[
            "地方文史：乾隆观《西郊胜景图》嫌「穷八家」不雅而赐名（无档案）",
            "人大清史研究所：村子渐富裕后自行更名（无赐名情节）",
        ],
    ),
    Proposition(
        id="prop_qishierfu_legend",
        statement="「一溜边山七十二府」为民间俗称，无 72 座官方名录证据",
        derived_from_fact_ids=["tf_dsm_jinshan"],
        inferred_subject_id="ent_jinshan",
        inference_method="嘉靖奏疏称「新旧陵墓约计二十余处」；周肇祥《琉璃厂杂记》称二十余",
        alternative_relations=["明代统计口径不一，民间以七十二为概数"],
    ),
    Proposition(
        id="prop_qlq_gangnian",
        statement="青龙桥闸为昆明湖溢洪枢纽，弘历称「昆明湖之尾闾」",
        derived_from_fact_ids=["tf_qlq_daotianchang"],
        inferred_subject_id="ent_qinglongqiao_gate",
        inference_method="《日下旧闻考》卷100载稻田厂仓署；内务府专管",
        alternative_relations=[],
    ),
]

ADOPTIONS: List[BeliefAdoption] = [
    BeliefAdoption(proposition_id="prop_xsq_flag", status=EpistemicStatus.VERIFIED,
                   confidence=0.9, adopted_by="E7交付档案v1.1",
                   rationale="《明史·兵志》与地名志互证，两套制度不可混说"),
    BeliefAdoption(proposition_id="prop_dyz_no_imperial_gift",
                   status=EpistemicStatus.CONTESTED, confidence=0.6,
                   adopted_by="E4交付档案v2",
                   rationale="官书只证名已用，赐名情节无档案；三说并列"),
    BeliefAdoption(proposition_id="prop_qishierfu_legend",
                   status=EpistemicStatus.FOLK_LEGEND, confidence=0.35,
                   adopted_by="E9交付档案v1.1",
                   rationale="民间俗称，无精确名录证据"),
    BeliefAdoption(proposition_id="prop_qlq_gangnian",
                   status=EpistemicStatus.VERIFIED, confidence=0.9,
                   adopted_by="E3交付档案v2",
                   rationale="官书与内务府管理双重支撑"),
]
