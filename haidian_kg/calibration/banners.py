"""
haidian_kg/calibration/banners.py
圆明园八旗护军营校准实例（BHKG/HHTO v2.1 第三个端到端校准数据集）

设计目的：验证「军事营垒」类实体 + 多实体空间格局 + 官额时变。

史料纪律（全部为《钦定八旗通志》等一手官书原文，已核维基文库四库本）：
- 《钦定八旗通志》卷116营建志：雍正二年设，共盖房一万间，分八处，每处1250间
  ⚠️ 初建是 1250 间/处；"1550"是乾隆十二年增护军100名/旗、添房300间/旗之后的数字。
  **初建与增建是两个年份，不可混说。**
- 卷116方位原文：镶黄旗坐落树村西边、正白旗坐落树村东边、正黄旗坐落萧家河、
  正红旗坐落安河桥、镶蓝旗坐落蓝靛厂西边……
  ⚠️ "萧家河北有正黄旗护军营房"的"北"是方位词（营房在河的北边），
  **不是"村北"这一称谓**。
- 《钦定日下旧闻考》卷72引《八旗册》：廨舍与官房分列，
  "楹"=一间；65+1485=1550 恰与 1250+300 吻合。
  ⚠️ 原书为"護軍校護軍等官房"——**"校"字不可漏**，护军校是另一级军职。
- 正红旗方位以《日下旧闻考》卷72"静明园东北"为准；
  卷116转录"東四木村東邉"疑为讹字（海淀无此地名）。
- 二手"正红旗营房在北安河桥西北"系讹传，两部官书均作"安河桥"。
- 树村汛：卷73"其暢春園樹村香山三汛仍舊"——"仍旧"表明1781之前已存在，
  1781只是编入五营二十三汛经制之年。
- 副将移驻树村有三个时间点（1799设总兵/1800下诏/1801实施），不是一个。
"""
from typing import List

from ..ontology.temporal import (
    CalibrationTable, DatePoint, Era, GregorianDate, ReignYear, TimeSpan,
)
from ..ontology.epistemic import (
    BeliefAdoption, EpistemicStatus, HistoricalSource, Proposition,
    SourceCategory, SourceDivision, TextualFact,
)
from .bibliography import source_by_title
from ..ontology.spatiotemporal import (
    Appellation, AppellationKind, DiachronicIdentityAssertion,
    HistoricalFeatureState, IdentityRelation, PersistentSpatialEntity,
    PhysicalThingKind, PlaceAggregate, PlaceTransformation,
    PlaceTransformationEvent, ReferentialAssertion,
)
from ..ontology.video_contracts import (
    VisualStateAssertion, ConstraintStrength,
)

CAL = CalibrationTable.CN_ASTRONOMICAL_ALMANAC


def _dt(y, tag, reign=None, precision="year"):
    return DatePoint(
        id=tag, label=str(y), precision=precision, reign_year=reign,
        gregorian=GregorianDate(year=y, calibration=CAL),
    )


def _ts(y1, y2, tag):
    return TimeSpan(id=tag, label="%d-%d" % (y1, y2),
                    begin=_dt(y1, tag + "_b"), end=_dt(y2, tag + "_e"))


# ==================================================================
# 1. 文献
# ==================================================================

SOURCES: List[HistoricalSource] = [
    # v2.1：一律取自统一书目表，一书一条，禁止在此另建
    source_by_title("钦定八旗通志"),
    source_by_title("钦定日下旧闻考"),
    source_by_title("清仁宗睿皇帝实录"),
    source_by_title("竹叶亭杂记"),
]


DIVISIONS: List[SourceDivision] = [
    SourceDivision(id="div_bqtz116_yingjian", source_id="src_bqtz",
                   volume_number="卷116", section_title="营建志"),
    SourceDivision(id="div_bqtz34_zhuoshu", source_id="src_bqtz",
                   volume_number="卷34", section_title="驻防"),
    SourceDivision(id="div_rxjwkc72_baqi", source_id="src_rxjwkc",
                   volume_number="卷72", section_title="官署门引《八旗册》"),
    SourceDivision(id="div_rxjwkc99_jiaojiong", source_id="src_rxjwkc",
                   volume_number="卷99", section_title="郊坰西九"),
    SourceDivision(id="div_rizhi46_yu", source_id="src_rizhi",
                   volume_number="卷46", section_title="嘉庆四年六月初二日谕"),
    SourceDivision(id="div_rizhi76_yu", source_id="src_rizhi",
                   volume_number="卷76", section_title="嘉庆五年十一月十七日谕"),
    SourceDivision(id="div_zyztj1", source_id="src_zyztj",
                   volume_number="卷一", section_title="圆明园驻防"),
]


# ==================================================================
# 2. 文本事实
# ==================================================================

FACTS: List[TextualFact] = [
    TextualFact(
        id="tf_bqtz116_yuanzheng", division_id="div_bqtz116_yingjian",
        verbatim_quote="圓明園八旗駐防，雍正二年設，共蓋房一萬間，分為八處，每處一千二百五十間。",
        attested_string="雍正二年設",
    ),
    TextualFact(
        id="tf_bqtz116_fangwei", division_id="div_bqtz116_yingjian",
        verbatim_quote="鑲黄旗營房坐落樹村西邊，正白旗營房坐落樹村東邊，鑲白旗營房坐落水礳，正藍旗營房坐落保福寺，正黄旗營房坐落蕭家河，正红旗營房坐落安河橋，鑲藍旗營房坐落藍靛廠西邊。",
        attested_string="營房坐落",
    ),
    TextualFact(
        id="tf_qianlong12_zeng", division_id="div_bqtz116_yingjian",
        verbatim_quote="乾隆十二年每旗增護軍一百名各添房三百間。",
        attested_string="添房三百間",
    ),
    TextualFact(
        id="tf_bq72_huangqi", division_id="div_rxjwkc72_baqi",
        verbatim_quote="鑲黄旗營房坐落樹村西邊，廨舍六十五楹，護軍校護軍等官房一千四百八十五楹。",
        attested_string="樹村西邊",
    ),
    TextualFact(
        id="tf_bq72_zhengbai", division_id="div_rxjwkc72_baqi",
        verbatim_quote="正白旗營房坐落樹村東邊，廨舍六十五楹，護軍校護軍等官房一千四百六十四楹。",
        attested_string="樹村東邊",
    ),
    TextualFact(
        id="tf_bq72_zhenghuang", division_id="div_rxjwkc72_baqi",
        verbatim_quote="蕭家河北有正黄旗護軍營房，廨舍六十五楹，護軍校護軍等官房一千四百八十五楹。",
        attested_string="蕭家河北",
    ),
    TextualFact(
        id="tf_rx99_wushengan", division_id="div_rxjwkc99_jiaojiong",
        verbatim_quote="樹村有五聖菴，觀音寺。",
        attested_string="五聖菴",
    ),
    TextualFact(
        id="tf_rizhi76_yu", division_id="div_rizhi76_yu",
        verbatim_quote="定左翼總兵駐正陽門外、右翼總兵駐圓明園，所有圓明園副將，著移駐樹村。",
        attested_string="著移駐樹村",
    ),
    TextualFact(
        id="tf_zyztj_shishi", division_id="div_zyztj1",
        verbatim_quote="六年改左翼總兵駐紮城外，右翼總兵駐紮圓明園。先是副將駐圓明園，自總兵駐園，副將則移駐樹村。",
        attested_string="移駐樹村",
    ),
]


# ==================================================================
# 3. 实体：营房、汛署、村落、庙宇
# ==================================================================

ENTITIES: List[PersistentSpatialEntity] = [
    # 八所护军营房（仅录方位明确者）
    PersistentSpatialEntity(id="ent_camp_xianghuang", kind=PhysicalThingKind.FORTIFIED_CAMP,
                            canonical_label="镶黄旗营房（树村西）"),
    PersistentSpatialEntity(id="ent_camp_zhengbai", kind=PhysicalThingKind.FORTIFIED_CAMP,
                            canonical_label="正白旗营房（树村东）"),
    PersistentSpatialEntity(id="ent_camp_zhenghuang", kind=PhysicalThingKind.FORTIFIED_CAMP,
                            canonical_label="正黄旗营房（萧家河北）"),
    PersistentSpatialEntity(id="ent_camp_zhenghong", kind=PhysicalThingKind.FORTIFIED_CAMP,
                            canonical_label="正红旗营房（安河桥）"),
    PersistentSpatialEntity(id="ent_camp_xianglan", kind=PhysicalThingKind.FORTIFIED_CAMP,
                            canonical_label="镶蓝旗营房（蓝靛厂西）"),
    # 树村汛署
    PersistentSpatialEntity(id="ent_shucun_xun", kind=PhysicalThingKind.FORTIFIED_CAMP,
                            canonical_label="树村汛署"),
    # 聚落
    PersistentSpatialEntity(id="ent_shucun", kind=PhysicalThingKind.SETTLEMENT_AREA,
                            canonical_label="树村"),
    # 庙宇（明代即有）
    PersistentSpatialEntity(id="ent_wushengan", kind=PhysicalThingKind.RELIGIOUS_PRECINCT,
                            canonical_label="五圣庵"),
    PersistentSpatialEntity(id="ent_guanyinsi", kind=PhysicalThingKind.RELIGIOUS_PRECINCT,
                            canonical_label="观音寺"),
    # 圆明园本体（八旗驻防的空间母体）
    PersistentSpatialEntity(id="ent_yuanmingyuan_parent", kind=PhysicalThingKind.GARDEN_COMPLEX,
                            canonical_label="圆明园"),
]


# ==================================================================
# 4. 聚合：八旗驻防是一个同时性集合
# ==================================================================

AGGREGATES: List[PlaceAggregate] = [
    PlaceAggregate(
        id="agg_yuanming_eight_banners", label="圆明园八旗驻防",
        time_span=_ts(1724, 1912, "ts_aggb"),
        member_entity_ids=[
            "ent_camp_xianghuang", "ent_camp_zhengbai", "ent_camp_zhenghuang",
            "ent_camp_zhenghong", "ent_camp_xianglan",
        ],
    ),
]


# ==================================================================
# 5. 历时状态：官房数随年份变化（1250 → 1550 不可混说）
# ==================================================================

STATES: List[HistoricalFeatureState] = [
    # 雍正二年初建：每处 1250 间
    HistoricalFeatureState(
        id="st_camp_1724", entity_id="ent_camp_xianghuang",
        time_span=_ts(1724, 1747, "ts_c1"),
        geometry="每处营房一千二百五十间，分八处，共盖房一万间",
        material="官房土墙灰瓦，廨舍六十五楹另计",
        function="八旗护军营房（镶黄旗）",
        evidence_fact_ids=["tf_bqtz116_yuanzheng", "tf_bq72_huangqi"],
    ),
    # 乾隆十二年增护军、添房后：1550 楹
    HistoricalFeatureState(
        id="st_camp_1747", entity_id="ent_camp_xianghuang",
        time_span=_ts(1747, 1911, "ts_c2"),
        geometry="廨舍六十五楹，護軍校護軍等官房一千四百八十五楹，合计一千五百五十楹",
        material="官房土墙灰瓦",
        function="八旗护军营房（镶黄旗），额兵增后规模",
        evidence_fact_ids=["tf_qianlong12_zeng", "tf_bq72_huangqi"],
    ),
    # 树村汛：1781之前已存在（卷73「三汛仍旧」）
    # 开放起始必须用 begin=None，不得伪造一个无公历的 DatePoint
    HistoricalFeatureState(
        id="st_xun_pre1781", entity_id="ent_shucun_xun",
        time_span=TimeSpan(id="ts_x1", label="1781年前已存",
                           open_begin=True, begin=None, end=_dt(1780, "ts_x1e")),
        geometry="树村汛设守备署，署在树村南",
        material="汛署房舍",
        function="巡捕五营之一汛（卷73称三汛仍旧，表明1781前已存）",
        evidence_fact_ids=["tf_rizhi76_yu"],
    ),
    # 嘉庆六年副将移驻树村
    HistoricalFeatureState(
        id="st_xun_1801", entity_id="ent_shucun_xun",
        time_span=_ts(1801, 1911, "ts_x2"),
        geometry="副将衙署添建于树村",
        material="衙署房舍",
        function="圆明园副将移驻，督察五汛",
        evidence_fact_ids=["tf_rizhi76_yu", "tf_zyztj_shishi"],
    ),
    # 树村明代庙宇
    HistoricalFeatureState(
        id="st_shucun_ming", entity_id="ent_shucun",
        time_span=_ts(1500, 1724, "ts_sm"),
        geometry="村内有五圣庵、观音寺",
        material="寺庵砖木",
        function="庙宇聚落（万历二十八年铁磬、天启六年铁钟为证）",
        evidence_fact_ids=["tf_rx99_wushengan"],
    ),
    # 圆明园母体：八旗驻防的依托园林
    HistoricalFeatureState(
        id="st_ymy_parent_1724", entity_id="ent_yuanmingyuan_parent",
        time_span=_ts(1724, 1911, "ts_yp"),
        geometry="皇家离宫园林（此处仅记其作为八旗驻防依托的空间母体）",
        material="园林宫殿（形制详见圆明园词条）",
        function="八旗驻防的空间母体，营房环其分布",
        evidence_fact_ids=["tf_bqtz116_yuanzheng", "tf_bqtz116_fangwei"],
    ),
]


# ==================================================================
# 6. 空间变化
# ==================================================================

TRANSFORMATIONS: List[PlaceTransformation] = [
    PlaceTransformation(
        id="pte_camp_1724_built", entity_id="ent_camp_xianghuang",
        transformation=PlaceTransformationEvent.CONSTRUCTED,
        time_span=_ts(1724, 1724, "ts_p1"),
        resulting_state_id="st_camp_1724",
        resulting_condition="雍正二年设，每处1250间",
        evidence_fact_ids=["tf_bqtz116_yuanzheng"],
    ),
    PlaceTransformation(
        id="pte_camp_1747_expand", entity_id="ent_camp_xianghuang",
        transformation=PlaceTransformationEvent.EXPANDED,
        time_span=_ts(1747, 1747, "ts_p2"),
        resulting_state_id="st_camp_1747",
        resulting_condition="乾隆十二年增护军百名，添房三百间",
        evidence_fact_ids=["tf_qianlong12_zeng"],
    ),
    PlaceTransformation(
        id="pte_xun_1801_relocate", entity_id="ent_shucun_xun",
        transformation=PlaceTransformationEvent.RELOCATED,
        time_span=_ts(1801, 1801, "ts_p3"),
        resulting_state_id="st_xun_1801",
        resulting_condition="副将自圆明园移驻树村，添建衙署",
        evidence_fact_ids=["tf_rizhi76_yu", "tf_zyztj_shishi"],
    ),
]


# ==================================================================
# 7. 身份断言
# ==================================================================

IDENTITIES: List[DiachronicIdentityAssertion] = [
    DiachronicIdentityAssertion(
        id="dia_shucun_continuity",
        subject_entity_ids=["ent_shucun", "ent_shucun_xun"],
        relation=IdentityRelation.SAME_CONTINUANT,
        time_span=_ts(1500, 1911, "ts_d1"),
        evidence_fact_ids=["tf_rx99_wushengan", "tf_rizhi76_yu"],
        status=EpistemicStatus.VERIFIED,
        alternative_relations=[],
    ),
    # 跨模块同指（holdout run2 collision 硬闸发现的 KB 数据缺陷修复）：
    # banners 的驻防空间母体与 yuanmingyuan 模块的圆明园本体是同一座园子——
    # banners 建模时为八旗驻防聚合另立母体实体，未挂身份断言，导致挖掘假说
    # 「圆明园」跨双实体计入 collision。注意 dia_ymy_ccy_relation 是关系断言，
    # 不可挪用为同指证据；此处证据取八旗通志营建/方位二事实。
    DiachronicIdentityAssertion(
        id="dia_ymy_parent_same",
        subject_entity_ids=["ent_yuanmingyuan_parent", "ent_yuanmingyuan"],
        relation=IdentityRelation.SAME_CONTINUANT,
        time_span=_ts(1724, 1911, "ts_d2"),
        evidence_fact_ids=["tf_bqtz116_yuanzheng", "tf_bqtz116_fangwei"],
        status=EpistemicStatus.VERIFIED,
        alternative_relations=[],
    ),
]


# ==================================================================
# 8. 名称与指称
# ==================================================================

APPELLATIONS: List[Appellation] = [
    Appellation(id="app_xianghuang_yf", label="镶黄旗营房",
                kind=AppellationKind.OFFICIAL, valid_time_span=_ts(1724, 1911, "ts_n1"),
                attesting_fact_ids=["tf_bqtz116_fangwei"]),
    Appellation(id="app_shucunxi", label="树村西",
                kind=AppellationKind.STREET_NAME, valid_time_span=_ts(1724, 1911, "ts_n2"),
                attesting_fact_ids=["tf_bq72_huangqi"]),
    Appellation(id="app_xiaojiahebei", label="萧家河北",
                kind=AppellationKind.STREET_NAME, valid_time_span=_ts(1724, 1911, "ts_n3"),
                attesting_fact_ids=["tf_bq72_zhenghuang"]),
    Appellation(id="app_shucun_xun", label="树村汛",
                kind=AppellationKind.OFFICIAL, valid_time_span=_ts(1700, 1911, "ts_n4"),
                attesting_fact_ids=["tf_rizhi76_yu"]),
    Appellation(id="app_beianqiao_mis", label="北安河桥",
                kind=AppellationKind.MISPLACED_LEGEND, valid_time_span=_ts(1900, 2026, "ts_n5"),
                attesting_fact_ids=[]),
    Appellation(id="app_ymy_banners", label="圆明园八旗驻防",
                kind=AppellationKind.OFFICIAL, valid_time_span=_ts(1724, 1911, "ts_n7"),
                attesting_fact_ids=["tf_bqtz116_yuanzheng"]),
    Appellation(id="app_shucun_name", label="树村",
                kind=AppellationKind.STANDARD if hasattr(AppellationKind, "STANDARD")
                else AppellationKind.OFFICIAL,
                valid_time_span=_ts(1500, 2026, "ts_n6"),
                attesting_fact_ids=["tf_rx99_wushengan"]),
]

REFERENCES: List[ReferentialAssertion] = [
    ReferentialAssertion(
        id="rr_xianghuang", appellation_id="app_xianghuang_yf",
        referent_entity_id="ent_camp_xianghuang",
        time_span=_ts(1724, 1911, "ts_r1"),
        evidence_fact_ids=["tf_bqtz116_fangwei"],
    ),
    ReferentialAssertion(
        id="rr_shucunxun", appellation_id="app_shucun_xun",
        referent_entity_id="ent_shucun_xun", time_span=_ts(1700, 1911, "ts_r2"),
        evidence_fact_ids=["tf_rizhi76_yu"],
    ),
    # 「圆明园八旗驻防」指向集合母体（圆明园），营房为其下属
    ReferentialAssertion(
        id="rr_ymy_banners", appellation_id="app_ymy_banners",
        referent_entity_id="ent_yuanmingyuan_parent",
        time_span=_ts(1724, 1911, "ts_r3"),
        evidence_fact_ids=["tf_bqtz116_yuanzheng", "tf_bqtz116_fangwei"],
    ),
]


# ==================================================================
# 9. 断言与采信：已修的 v1 错误必须留证
# ==================================================================

PROPOSITIONS: List[Proposition] = [
    Proposition(
        id="prop_camp_count",
        statement="雍正二年初建每处1250间；1550楹是乾隆十二年增建后的数字",
        derived_from_fact_ids=["tf_bqtz116_yuanzheng", "tf_qianlong12_zeng", "tf_bq72_huangqi"],
        inferred_subject_id="ent_camp_xianghuang",
        inference_method="1250+300=1550，与官书官房数吻合，初建与增建分属两年",
        alternative_relations=[],
    ),
    Proposition(
        id="prop_huojunxiao",
        statement="官房原文为「護軍校護軍等官房」，护军校是另一级军职，不可漏字",
        derived_from_fact_ids=["tf_bq72_huangqi"],
        inferred_subject_id="ent_camp_xianghuang",
        inference_method="卷72原文校勘",
        alternative_relations=[],
    ),
    Proposition(
        id="prop_zhenghong_anhe",
        statement="正红旗营房在安河桥，二手「北安河桥」系讹传",
        derived_from_fact_ids=["tf_bqtz116_fangwei"],
        inferred_subject_id="ent_camp_zhenghong",
        inference_method="两部官书均作安河桥",
        alternative_relations=[],
    ),
    Proposition(
        id="prop_shucun_etimology",
        statement="「树村」因树得名的通行说法缺乏文献依据；树村之名或更早",
        derived_from_fact_ids=["tf_rx99_wushengan"],
        inferred_subject_id="ent_shucun",
        inference_method="未找到清民文献支持因树得名；蜀村/蜀社音转说底层文献未核到",
        alternative_relations=["因树多而得名说（通行，无据）", "蜀村→树村音转说（待考）"],
    ),
]

ADOPTIONS: List[BeliefAdoption] = [
    BeliefAdoption(
        proposition_id="prop_camp_count", status=EpistemicStatus.VERIFIED,
        confidence=0.95, adopted_by="BHKG校准集",
        rationale="三书互证，1250与1550分属两年，v1混说已修",
    ),
    BeliefAdoption(
        proposition_id="prop_huojunxiao", status=EpistemicStatus.VERIFIED,
        confidence=0.9, adopted_by="BHKG校准集",
        rationale="原书校勘，v1漏「校」字已修",
    ),
    BeliefAdoption(
        proposition_id="prop_zhenghong_anhe", status=EpistemicStatus.VERIFIED,
        confidence=0.9, adopted_by="BHKG校准集",
        rationale="两部官书均作安河桥",
    ),
    BeliefAdoption(
        proposition_id="prop_shucun_etimology", status=EpistemicStatus.UNSUBSTANTIATED,
        confidence=0.25, adopted_by="BHKG校准集",
        rationale="因树得名说无文献依据；音转说底层文献未核到，均不可作史实",
    ),
]
