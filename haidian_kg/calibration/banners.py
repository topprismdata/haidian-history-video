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


# ==================================================================
# 10. 健锐营（香山健锐营）词条追加（holdout run3 kb-coverage-gap 面）
# ------------------------------------------------------------------
# 史料纪律（全部回源核对，2026-10-02）：
# - 立营年代双源：《钦定日下旧闻考》卷102载乾隆十四年(1749,己巳)御制实胜寺碑记
#   「合成功之旅立為健銳雲梯營」+《清史稿》卷130兵志「乾隆十四年，設雲梯兵一營」。
#   乾隆十三年(1748)是选锋演云梯之年，与立营之年分属两年，不可混说。
# - 营制归属：《清史稿》卷130将设云梯兵列于京营「兵衛之制」，
#   八旗驻防另立「畿辅/东三省/各直省/籓部」四类——健锐营属禁旅特设营制，
#   非八旗驻防；与圆明园八旗护军营同卷并列员额（本模块 banners 的驻防体系
#   是并立关系，不是隶属关系）。
# - 碉楼总数：卷102馆臣按「共計六十有七」；按卷101/卷102旗册逐旗数
#   （九九七七＋九七七七）加印房四隅合计六十六，官书总数与逐旗相加差一。
#   两说并存不取区间值（E9 纪律②），现代调查「六十八座」无官方测绘档不采。
# - 兵额：乾隆朝会典卷次原文未核得逐字引文；员额以《清史稿》卷130
#   「光、宣之季实存名数」为准并显式标注时段，不冒充初设兵额。
# - 团城演武厅现状单独核查（E8 纪律⑤）：1979市保/1988移交/2006第六批国保
#   （国发〔2006〕19号，名录名「健锐营演武厅」，编号Ⅲ-9）；现由北京大觉寺与
#   团城管理处管理并开放。现代测绘米数只入现状态，不入乾隆建成态。
# ==================================================================

_JRY_SOURCES: List[HistoricalSource] = [
    source_by_title("清史稿"),
]

_JRY_DIVISIONS: List[SourceDivision] = [
    SourceDivision(id="div_qsg130_bing", source_id="src_qingshigao",
                   volume_number="卷130", section_title="志一百五·兵一·八旗"),
    SourceDivision(id="div_rxjwkc101", source_id="src_rxjwkc",
                   volume_number="卷101", section_title="郊坰西十一"),
    SourceDivision(id="div_rxjwkc102", source_id="src_rxjwkc",
                   volume_number="卷102", section_title="郊坰西十二"),
    SourceDivision(id="div_wjbz_tuancheng", source_id="src_wjbz_open",
                   volume_number="文保公开资料",
                   section_title="团城演武厅历史沿革条（大觉寺与团城管理处）"),
    SourceDivision(id="div_wjbz_guobao6", source_id="src_wjbz_open",
                   volume_number="文保公开资料",
                   section_title="第六批全国重点文物保护单位名单条（国发〔2006〕19号）"),
]

_JRY_FACTS: List[TextualFact] = [
    # ---- 《清史稿》卷130 兵一（维基文库转录本，2026-10-02 逐字核对） ----
    TextualFact(
        id="tf_qsg130_yunti", division_id="div_qsg130_bing",
        verbatim_quote="乾隆十四年，設雲梯兵一營。又於昆明湖設趕繒船，以前鋒軍習水戰。",
        attested_string="設雲梯兵一營",
        translator_note="此句列于京营「兵衛之制」段内，非「八旗驻防」段——"
                        "健锐营前身为京营特设之云梯兵营的官书结构证据。",
    ),
    TextualFact(
        id="tf_qsg130_zhufang", division_id="div_qsg130_bing",
        verbatim_quote="八旗駐防之兵，大類有四：曰畿輔駐防兵，其籓部內附之眾，"
                       "及在京內務府、理籓院所轄悉附焉；曰東三省駐防兵；"
                       "曰各直省駐防兵，新疆駐防兵附焉；曰籓部兵。",
        attested_string="八旗駐防之兵",
        translator_note="驻防四类清单内无健锐营——「特设营制非驻防」的另一面证据。",
    ),
    TextualFact(
        id="tf_qsg130_ymy", division_id="div_qsg130_bing",
        verbatim_quote="圓明園隨同辦事營總二，營總六，護軍參領八，副護軍參領十六，"
                       "委護軍參領三十二，護軍校、副護軍校各百二十八，包衣營總一，"
                       "包衣護軍參領、副護軍參領各三，包衣護軍校九，凡三百三十六人。"
                       "護軍三千六百七十二，馬甲三百，槍甲四百，養育兵千八百二十六，"
                       "包衣護軍一百二十，包衣馬甲三十，包衣養育兵六十，凡六千四百八人。",
        attested_string="圓明園隨同辦事營總",
        translator_note="光宣之季员额段：圆明园护军营与健锐营条目紧相邻接、同属"
                        "京营兵衛序列——两营并立关系的一手结构证据。",
    ),
    TextualFact(
        id="tf_qsg130_e", division_id="div_qsg130_bing",
        verbatim_quote="健銳營翼長四，正參領八，副參領十六，委參領三十二，番子防禦一，"
                       "前鋒校、副前鋒校各七十，凡百有二人。前鋒千九百六十，委前鋒一千，"
                       "領催四，馬甲八十一，養育兵八百三十三，凡三千八百七十八人。",
        attested_string="健銳營翼長四",
        translator_note="官书原文自述时段为「光、宣之季实存名数」，不得冒充初设兵额；"
                        "乾隆朝会典卷次原文未核得，员额暂以此为唯一档案口径。",
    ),
    # ---- 《钦定日下旧闻考》卷101 郊坰西十一（四库本，维基文库 2026-10-02） ----
    TextualFact(
        id="tf_rxjwkc101_dong", division_id="div_rxjwkc101",
        verbatim_quote="静宜園東四旗健鋭雲梯營房之制鑲黄旗在佟峪村西碉樓九座"
                       "正白旗在公車府西碉樓九座鑲白旗在小府西碉樓七座"
                       "正藍旗在道公府西碉樓七座",
        attested_string="健鋭雲梯營房之制",
        translator_note="引《旗册》原文；「东四旗＝左翼、西四旗＝右翼」为八旗通制"
                        "之通行比附（现代通说），官书原文只作東四旗/西四旗。",
    ),
    TextualFact(
        id="tf_rxjwkc101_an", division_id="div_rxjwkc101",
        verbatim_quote="香山東四旗健鋭雲梯營房乾隆十四年奉命建設後西四旗同",
        attested_string="乾隆十四年奉命建設",
    ),
    # ---- 《钦定日下旧闻考》卷102 郊坰西十二（四库本，维基文库 2026-10-02） ----
    TextualFact(
        id="tf_rxjwkc102_xi", division_id="div_rxjwkc102",
        verbatim_quote="静宜園西四旗健銳雲梯營房之制正黄旗在永安村西碉樓九座"
                       "正紅旗在梵香寺東碉樓七座鑲紅旗在寳相寺南碉樓七座"
                       "鑲藍旗在鑲紅旗南碉樓七座",
        attested_string="健銳雲梯營房之制",
        translator_note="卷101作「健鋭」、卷102作「健銳」，鋭/銳为四库本用字之异，"
                        "各按原卷字形录入。",
    ),
    TextualFact(
        id="tf_rxjwkc102_yinfang", division_id="div_rxjwkc102",
        verbatim_quote="静宜園南樓門外有八旗印房",
        attested_string="八旗印房",
    ),
    TextualFact(
        id="tf_rxjwkc102_diao67", division_id="div_rxjwkc102",
        verbatim_quote="八旗印房四隅皆有碉樓一座乾隆十四年建合之東四旗西四旗各營碉樓共計六十有七",
        attested_string="共計六十有七",
        translator_note="馆臣按语口径为总数六十七；按卷101/卷102旗册逐旗数"
                        "（9+9+7+7＋9+7+7+7）加印房四隅合计六十六，差一——"
                        "总数与分计不同合，两说并存，不取区间值。",
    ),
    TextualFact(
        id="tf_rxjwkc102_ywt", division_id="div_rxjwkc102",
        verbatim_quote="演武㕔西北為實勝寺",
        attested_string="演武㕔",
        translator_note="「㕔」为四库本「廳」之用字；「演武厅」之名的一手官书明录。",
    ),
    TextualFact(
        id="tf_rxjwkc102_ssb", division_id="div_rxjwkc102",
        verbatim_quote="實勝寺殿前恭懸御書額曰顯大雄力並恭立乾隆十四年御制實勝寺記文碑"
                       "碑高丈餘方廣四面如一刻國書䝉古漢字梵書四體",
        attested_string="御制實勝寺記文碑",
    ),
    TextualFact(
        id="tf_rxjwkc102_bei_yuan", division_id="div_rxjwkc102",
        verbatim_quote="去嵗夏視師金川者久而弗告其功且苦酋之恃其碉也"
                       "則創為以碉攻碉之說將築碉焉朕謂攻碉已下策",
        attested_string="以碉攻碉",
        translator_note="御制实胜寺碑记（乾隆十四年五月），当事人一手记录金川之役"
                        "与设碉练兵缘起。「去嵗」即乾隆十三年。",
    ),
    TextualFact(
        id="tf_rxjwkc102_bei_xi", division_id="div_rxjwkc102",
        verbatim_quote="則命於西山之麓設為石碉也者而簡佽飛之士以習之"
                       "朱逾月得精其技者二千人更命大學士忠勇公傅恒為經畧統之以行",
        attested_string="西山之麓設為石碉",
        translator_note="「朱逾月」他本多作「未逾月」，转录本疑形讹，异文以碑拓/"
                        "点校本为准；「二千人」为碑文一手数字（精其技者之数）。",
    ),
    TextualFact(
        id="tf_rxjwkc102_bei_li", division_id="div_rxjwkc102",
        verbatim_quote="因命擇向庀材建寺於碉之側名之曰實勝夫已習之藝不可廢"
                       "已奏之績不可忘於是合成功之旅立為健銳雲梯營"
                       "並於寺之左右建屋居之間亦依山為碉以肖刮耳勒歪之境",
        attested_string="立為健銳雲梯營",
        translator_note="健锐云梯营立营之名句（已习之艺不可废，已奏之绩不可忘）；"
                        "碑文以「健銳雲梯營」全称为正，单称「健銳營」为后起省称。",
    ),
    TextualFact(
        id="tf_rxjwkc102_bei_nian", division_id="div_rxjwkc102",
        verbatim_quote="乾隆十有四年嵗在己巳夏五月之吉",
        attested_string="乾隆十有四年",
    ),
    TextualFact(
        id="tf_rxjwkc102_houji", division_id="div_rxjwkc102",
        verbatim_quote="寺左近健銳雲梯營實居之營之兵是役効力為尤多故不可不旌其前勞以勸夫後進",
        attested_string="健銳雲梯營實居之",
        translator_note="御制实胜寺后记（乾隆辛巳＝二十六年）：健锐营平定准噶尔回部"
                        "（大小和卓）战功之表彰，碑今存团城演武厅北城楼内。",
    ),
    TextualFact(
        id="tf_rxjwkc102_houji_yue", division_id="div_rxjwkc102",
        verbatim_quote="嵗時幸香山閱健銳兵用寓尹鐸晉陽之意不亦可乎",
        attested_string="幸香山閱健銳兵",
        translator_note="皇帝岁时幸香山阅健锐营——校阅制度的一手记载。",
    ),
    TextualFact(
        id="tf_rxjwkc102_fanzhu", division_id="div_rxjwkc102",
        verbatim_quote="俘來醜虜習故業卭籠令築㧞地高昔也禦我䕶其命今也歸我効其勞",
        attested_string="俘來醜虜習故業",
        translator_note="乾隆十五年御制番筑碉诗：金川俘虏参与筑碉的一手记载，"
                        "「碉为金川战俘所筑」之俗说的一手依据（器物建造者层）。",
    ),
    # ---- 北京市文物局公开文保资料（记录式陈述，与古籍分挂不互冒） ----
    TextualFact(
        id="tf_wjbz_tcywt_jianzhu", division_id="div_wjbz_tuancheng",
        verbatim_quote="团城演武厅位于风景秀丽的香山地区，始建于1749年(乾隆十四年)。"
                       "它是集城池（团城）、殿宇（演武厅、东西朝房）、西城楼门、碑亭、"
                       "校场为一体的别具特色的武备建筑群，古建艺术风格独特，建筑宏伟壮观。"
                       "分布在周围的还有八旗营房、印房、官学、石碉等。",
        attested_string="团城演武厅",
        translator_note="北京市文物局网站·北京大觉寺与团城管理处·团城演武厅·历史沿革页；"
                        "现行管理机构即「北京大觉寺与团城管理处」（文物局局属）。",
    ),
    TextualFact(
        id="tf_wjbz_tuancheng", division_id="div_wjbz_tuancheng",
        verbatim_quote="团城，也称看城。城内东西直径50.2米，南北直径40米，城高11米，"
                       "城厚5米。平面呈椭圆形，奇特的造型全国独一无二。",
        attested_string="也称看城",
        translator_note="米数为管理方现行公开测绘口径，只入现状态，不入乾隆建成态"
                        "（E8 纪律③：无文保测绘档年份归属的数字不混挂）。",
    ),
    TextualFact(
        id="tf_wjbz_biane", division_id="div_wjbz_tuancheng",
        verbatim_quote="以青色大城砖砌筑而成，南北各有券洞供人出入，"
                       "门洞上方各有汉白玉石匾一块，南城匾额曰“威宣壁垒”，"
                       "北城匾额曰“志喻金汤”，均为乾隆御书。",
        attested_string="威宣壁垒",
    ),
    TextualFact(
        id="tf_wjbz_wocei", division_id="div_wjbz_tuancheng",
        verbatim_quote="楼内有一长方形巨大卧碑，通高3.42米，浮雕云龙纹拱璧,"
                       "用满、蒙、汉、藏四种文字镌刻着“御制实胜寺后记”，"
                       "其中汉文为乾隆御笔",
        attested_string="御制實勝寺后记",
        translator_note="北城楼卧碑即《御制实胜寺后记》四体文碑——后记碑刻实物"
                        "现存位置的官方口径（器物本体）。",
    ),
    TextualFact(
        id="tf_wjbz_tcywt", division_id="div_wjbz_tuancheng",
        verbatim_quote="1979年团城演武厅公布为市级文物保护单位。1988年，市政府研究决定"
                       "团城演武厅由农场局移交市文物局进行管理保护，并于当年成立"
                       "北京市团城演武厅管理处。2006年6月被公布为全国重点文物保护单位，"
                       "定名为“健锐营演武厅”。",
        attested_string="健锐营演武厅",
        translator_note="管理处沿革页称「2006年6月」；国发〔2006〕19号公布日期为"
                        "2006年5月25日——两说并存，采用国务院文件口径，"
                        "差异系公布/转载时间口径不同。",
    ),
    TextualFact(
        id="tf_wjbz_guobao6", division_id="div_wjbz_guobao6",
        verbatim_quote="306　　　　Ⅲ－9　　　　健锐营演武厅　　　　清"
                       "　　　　　　　　北京市海淀区",
        attested_string="健锐营演武厅",
        translator_note="国发〔2006〕19号第六批全国重点文物保护单位名单古建筑类"
                        "第306号（编号Ⅲ-9），公布日期二○○六年五月二十五日；"
                        "名单经中国政府网/文化和旅游部网页核验（2026-10-02）。",
    ),
]

# ------------------------------------------------------------------
# 实体：营制（健锐营/云梯兵）＋器物层（团城演武厅/香山碉楼）
# ------------------------------------------------------------------

_JRY_ENTITIES: List[PersistentSpatialEntity] = [
    # 云梯兵：乾隆十三年选锋于香山演云梯之部队，健锐营前身
    PersistentSpatialEntity(id="ent_jry_yunti", kind=PhysicalThingKind.FORTIFIED_CAMP,
                            canonical_label="云梯兵（乾隆十三年香山演云梯之兵）"),
    # 健锐营本体：特设营制，非八旗驻防（独立实体，与圆明园八旗护军营并立）
    PersistentSpatialEntity(id="ent_jry_ying", kind=PhysicalThingKind.FORTIFIED_CAMP,
                            canonical_label="健锐营",
                            supersedes_ids=["ent_jry_yunti"]),
    # 团城演武厅：器物层（实存建筑群，第六批国保）
    PersistentSpatialEntity(id="ent_jry_tuancheng", kind=PhysicalThingKind.FORTIFIED_CAMP,
                            canonical_label="团城演武厅"),
    # 香山碉楼（俗称金川碉）：器物层
    PersistentSpatialEntity(id="ent_jry_diaolou", kind=PhysicalThingKind.FORTIFIED_CAMP,
                            canonical_label="香山碉楼（俗称金川碉）"),
]

_JRY_STATES: List[HistoricalFeatureState] = [
    # 云梯兵：乾隆十三年设碉练兵（碑记「去嵗夏…創為以碉攻碉之說」）
    HistoricalFeatureState(
        id="st_jry_yunti_1748", entity_id="ent_jry_yunti",
        time_span=_ts(1748, 1749, "ts_jy1"),
        geometry="于西山之麓设为石碉，简佽飞之士习云梯，逾月得精其技者二千人，"
                 "命大学士忠勇公傅恒为经略统之以行",
        material="操演碉楼为石砌（碑记「設為石碉」）",
        function="为攻金川碉楼特训的云梯兵（非经制营制，尚无营名）",
        evidence_fact_ids=["tf_rxjwkc102_bei_yuan", "tf_rxjwkc102_bei_xi",
                           "tf_rxjwkc102_fanzhu"],
    ),
    # 健锐营：乾隆十四年立营（碑记＋清史稿双源）
    HistoricalFeatureState(
        id="st_jry_1749", entity_id="ent_jry_ying",
        time_span=_ts(1749, 1911, "ts_jy2"),
        geometry="营房分东四旗西四旗两翼布列于静宜园（香山）东南两翼：镶黄旗佟峪村西、"
                 "正白旗公车府西、镶白旗小府西、正蓝旗道公府西；正黄旗永安村西、"
                 "正红旗梵香寺东、镶红旗宝相寺南、镶蓝旗镶红旗南（日下旧闻考引旗册）",
        material="碉楼石砌仿金川碉形制（碑记「間亦依山為碉」）",
        function="云梯攻碉特设营制（碑记「合成功之旅立為健銳雲梯營」，"
                 "演技逾月精其技者二千人即其班底）；皇帝岁时幸香山阅健锐兵",
        admin_status="禁旅八旗兵衛之制序列特设营制（清史稿卷130），非八旗驻防四类；"
                     "与圆明园八旗护军营同卷并列员额、同驻京西北郊，系并立非隶属",
        evidence_fact_ids=["tf_rxjwkc102_bei_li", "tf_qsg130_yunti",
                           "tf_rxjwkc101_dong", "tf_rxjwkc101_an",
                           "tf_rxjwkc102_xi", "tf_qsg130_zhufang",
                           "tf_qsg130_ymy", "tf_rxjwkc102_houji_yue"],
    ),
    # 健锐营：光宣之季实存员额（清史稿卷130，唯一档案口径）
    HistoricalFeatureState(
        id="st_jry_gx", entity_id="ent_jry_ying",
        time_span=_ts(1875, 1911, "ts_jy3"),
        geometry="翼长四，正参领八，副参领十六，委参领三十二，番子防御一，"
                 "前锋校、副前锋校各七十，凡百有二人；前锋千九百六十，委前锋一千，"
                 "领催四，马甲八十一，养育兵八百三十三，凡三千八百七十八人",
        function="光、宣之季实存名数（官书自述口径，非初设兵额）",
        evidence_fact_ids=["tf_qsg130_e"],
    ),
    # 团城演武厅：乾隆十四年建成（结构形制，不挂现代米数）
    HistoricalFeatureState(
        id="st_jry_tuancheng_1749", entity_id="ent_jry_tuancheng",
        time_span=_ts(1749, 1978, "ts_jy4"),
        geometry="集城池（团城）、殿宇（演武厅、东西朝房）、西城楼门、碑亭、校场"
                 "为一体的武备建筑群；团城椭圆城堡南北各有券洞，南匾「威宣壁垒」、"
                 "北匾「志喻金汤」均为乾隆御书，城上建南北两座城楼",
        material="青色大城砖砌筑（管理方现行口径，谓砖砌为乾隆原构）",
        function="健锐营合练及皇帝阅兵校阅场所（演武厅为演武场主体建筑；"
                 "「枪炮演武场」系描述性短语不设实体）",
        evidence_fact_ids=["tf_wjbz_tcywt_jianzhu", "tf_wjbz_biane",
                           "tf_rxjwkc102_ywt", "tf_rxjwkc102_houji_yue"],
    ),
    # 团城演武厅：现状（文保与管理，1979 起）
    HistoricalFeatureState(
        id="st_jry_tuancheng_modern", entity_id="ent_jry_tuancheng",
        time_span=TimeSpan(id="ts_jy5", label="1979年-今",
                           begin=_dt(1979, "ts_jy5b"), end=None, open_end=True),
        geometry="团城东西直径50.2米、南北直径40米、城高11米、城厚5米（管理方现行"
                 "公开测绘口径）；北城楼内存《御制实胜寺后记》四体文卧碑，通高3.42米",
        admin_status="1979年市保；1988年移交市文物局并成立北京市团城演武厅管理处；"
                     "2006年列第六批全国重点文物保护单位（国发〔2006〕19号，2006年"
                     "5月25日公布，序号306编号Ⅲ-9，名录名「健锐营演武厅」，管理处页"
                     "称2006年6月系口径差）；现由北京大觉寺与团城管理处管理并开放",
        function="以军事武备为主题的博物馆（常设团城演武厅历史沿革展）",
        evidence_fact_ids=["tf_wjbz_tuancheng", "tf_wjbz_wocei",
                           "tf_wjbz_tcywt", "tf_wjbz_guobao6"],
    ),
    # 香山碉楼：乾隆十四年建（官书口径总数六十七，逐旗相加六十六，两说并存）
    HistoricalFeatureState(
        id="st_jry_diaolou_1749", entity_id="ent_jry_diaolou",
        time_span=_ts(1749, 1911, "ts_jy6"),
        geometry="东四旗：镶黄旗佟峪村西九座、正白旗公车府西九座、镶白旗小府西七座、"
                 "正蓝旗道公府西七座；西四旗：正黄旗永安村西九座、正红旗梵香寺东七座、"
                 "镶红旗宝相寺南七座、镶蓝旗镶红旗南七座；八旗印房四隅各一座；"
                 "官书按语总数「共計六十有七」",
        material="石砌，仿金川碉形制（碑记「設為石碉」）",
        function="演云梯攻碉之具（乾隆十五年番筑碉诗：金川俘虏参与修筑）",
        evidence_fact_ids=["tf_rxjwkc101_dong", "tf_rxjwkc102_xi",
                           "tf_rxjwkc102_diao67", "tf_rxjwkc102_yinfang",
                           "tf_rxjwkc102_bei_xi", "tf_rxjwkc102_fanzhu"],
    ),
    # 香山碉楼：现状（现存数量无官方测绘总数，不列数字）
    HistoricalFeatureState(
        id="st_jry_diaolou_now", entity_id="ent_jry_diaolou",
        time_span=TimeSpan(id="ts_jy7", label="1988年-今",
                           begin=_dt(1988, "ts_jy7b"), end=None, open_end=True),
        geometry="部分碉楼存留于香山地区（管理方沿革页仍记周围分布石碉；"
                 "现存座数无官方测绘档总数，不列）",
        function="健锐营遗存（北京植物园等处存有训练碉楼遗迹）",
        evidence_fact_ids=["tf_wjbz_tcywt_jianzhu"],
    ),
]

_JRY_TRANSFORMATIONS: List[PlaceTransformation] = [
    PlaceTransformation(
        id="pte_jry_yunti_1748", entity_id="ent_jry_yunti",
        transformation=PlaceTransformationEvent.CONSTRUCTED,
        time_span=_ts(1748, 1748, "ts_jp1"),
        resulting_state_id="st_jry_yunti_1748",
        resulting_condition="乾隆十三年创以碉攻碉之议，西山设石碉练云梯兵",
        evidence_fact_ids=["tf_rxjwkc102_bei_yuan", "tf_rxjwkc102_bei_xi"],
    ),
    PlaceTransformation(
        id="pte_jry_ying_1749", entity_id="ent_jry_ying",
        transformation=PlaceTransformationEvent.CONSTRUCTED,
        time_span=_ts(1749, 1749, "ts_jp2"),
        resulting_state_id="st_jry_1749",
        resulting_condition="乾隆十四年金川奏凯，合成功之旅立为健锐云梯营",
        evidence_fact_ids=["tf_rxjwkc102_bei_li", "tf_qsg130_yunti"],
    ),
    PlaceTransformation(
        id="pte_jry_tuancheng_1749", entity_id="ent_jry_tuancheng",
        transformation=PlaceTransformationEvent.CONSTRUCTED,
        time_span=_ts(1749, 1749, "ts_jp3"),
        resulting_state_id="st_jry_tuancheng_1749",
        resulting_condition="乾隆十四年建团城演武厅，为健锐营合练校阅之所",
        evidence_fact_ids=["tf_wjbz_tcywt_jianzhu"],
    ),
    PlaceTransformation(
        id="pte_jry_diaolou_1749", entity_id="ent_jry_diaolou",
        transformation=PlaceTransformationEvent.CONSTRUCTED,
        time_span=_ts(1749, 1749, "ts_jp4"),
        resulting_state_id="st_jry_diaolou_1749",
        resulting_condition="乾隆十四年奉命建设（东四旗后西四旗同），印房四隅碉楼同年建",
        evidence_fact_ids=["tf_rxjwkc101_an", "tf_rxjwkc102_diao67"],
    ),
]

# 云梯兵→健锐营：同一批金川奏凯之旅整编定名（继承者关系，非同名改称）
_JRY_IDENTITIES: List[DiachronicIdentityAssertion] = [
    DiachronicIdentityAssertion(
        id="dia_jry_yunti_to_ying",
        subject_entity_ids=["ent_jry_yunti", "ent_jry_ying"],
        relation=IdentityRelation.SUCCESSOR,
        time_span=_ts(1748, 1749, "ts_jd1"),
        evidence_fact_ids=["tf_rxjwkc102_bei_xi", "tf_rxjwkc102_bei_li",
                           "tf_qsg130_yunti"],
        status=EpistemicStatus.VERIFIED,
        alternative_relations=[],
    ),
]

# ------------------------------------------------------------------
# 名称与指称（「健锐营」等 holdout 缺口面挂 here，供字形表命中）
# ------------------------------------------------------------------

_JRY_APPELLATIONS: List[Appellation] = [
    Appellation(id="app_jry_ying", label="健锐营",
                kind=AppellationKind.OFFICIAL, valid_time_span=_ts(1749, 1912, "ts_jn1"),
                attesting_fact_ids=["tf_qsg130_e"]),
    Appellation(id="app_jry_ymt", label="健锐云梯营",
                kind=AppellationKind.OFFICIAL, valid_time_span=_ts(1749, 1911, "ts_jn2"),
                attesting_fact_ids=["tf_rxjwkc102_bei_li", "tf_rxjwkc101_dong"]),
    Appellation(id="app_jry_yunti", label="云梯兵",
                kind=AppellationKind.OFFICIAL, valid_time_span=_ts(1748, 1749, "ts_jn3"),
                attesting_fact_ids=["tf_qsg130_yunti"]),
    Appellation(id="app_jry_xiangshan", label="香山健锐营",
                kind=AppellationKind.VULGAR, valid_time_span=_ts(1749, 2026, "ts_jn4"),
                attesting_fact_ids=[]),
    Appellation(id="app_jry_ywt", label="演武厅", script_variants=["演武㕔"],
                kind=AppellationKind.OFFICIAL, valid_time_span=_ts(1749, 2026, "ts_jn5"),
                attesting_fact_ids=["tf_rxjwkc102_ywt", "tf_wjbz_tcywt_jianzhu"]),
    Appellation(id="app_jry_tuancheng", label="团城演武厅",
                kind=AppellationKind.OFFICIAL, valid_time_span=_ts(1749, 2026, "ts_jn6"),
                attesting_fact_ids=["tf_wjbz_tcywt_jianzhu"]),
    Appellation(id="app_jry_kancheng", label="看城",
                kind=AppellationKind.VULGAR, valid_time_span=_ts(1749, 2026, "ts_jn7"),
                attesting_fact_ids=["tf_wjbz_tuancheng"]),
    Appellation(id="app_jry_diaolou", label="碉楼",
                kind=AppellationKind.VULGAR, valid_time_span=_ts(1749, 2026, "ts_jn8"),
                attesting_fact_ids=["tf_rxjwkc102_diao67"]),
    Appellation(id="app_jry_shidiao", label="石碉",
                kind=AppellationKind.VULGAR, valid_time_span=_ts(1749, 2026, "ts_jn9"),
                attesting_fact_ids=["tf_rxjwkc102_bei_xi", "tf_wjbz_tcywt_jianzhu"]),
]

_JRY_REFERENCES: List[ReferentialAssertion] = [
    ReferentialAssertion(
        id="rr_jry_ying", appellation_id="app_jry_ying",
        referent_entity_id="ent_jry_ying",
        time_span=_ts(1749, 1912, "ts_jr1"),
        evidence_fact_ids=["tf_qsg130_e"]),
    ReferentialAssertion(
        id="rr_jry_ymt", appellation_id="app_jry_ymt",
        referent_entity_id="ent_jry_ying",
        time_span=_ts(1749, 1911, "ts_jr2"),
        evidence_fact_ids=["tf_rxjwkc102_bei_li"]),
    ReferentialAssertion(
        id="rr_jry_yunti", appellation_id="app_jry_yunti",
        referent_entity_id="ent_jry_yunti",
        time_span=_ts(1748, 1749, "ts_jr3"),
        evidence_fact_ids=["tf_qsg130_yunti"]),
    # 「香山健锐营」：近现代俗称，未核得清档原文——挂检索用指称，
    # 显式标 UNSUBSTANTIATED 并写 provenance，不当官称使用
    ReferentialAssertion(
        id="rr_jry_xiangshan", appellation_id="app_jry_xiangshan",
        referent_entity_id="ent_jry_ying",
        time_span=_ts(1749, 2026, "ts_jr4"),
        evidence_fact_ids=[],
        status=EpistemicStatus.UNSUBSTANTIATED,
        provenance="近现代俗称/今人叙述用法（维基百科、海淀文史叙述），清档原文未核得；"
                   "挂字形表供检索命中，不作为清代官称使用"),
    ReferentialAssertion(
        id="rr_jry_ywt", appellation_id="app_jry_ywt",
        referent_entity_id="ent_jry_tuancheng",
        time_span=_ts(1749, 2026, "ts_jr5"),
        evidence_fact_ids=["tf_rxjwkc102_ywt", "tf_wjbz_tcywt_jianzhu"]),
    ReferentialAssertion(
        id="rr_jry_tuancheng", appellation_id="app_jry_tuancheng",
        referent_entity_id="ent_jry_tuancheng",
        time_span=_ts(1749, 2026, "ts_jr6"),
        evidence_fact_ids=["tf_wjbz_tcywt_jianzhu"]),
    ReferentialAssertion(
        id="rr_jry_kancheng", appellation_id="app_jry_kancheng",
        referent_entity_id="ent_jry_tuancheng",
        time_span=_ts(1749, 2026, "ts_jr7"),
        evidence_fact_ids=["tf_wjbz_tuancheng"]),
    ReferentialAssertion(
        id="rr_jry_diaolou", appellation_id="app_jry_diaolou",
        referent_entity_id="ent_jry_diaolou",
        time_span=_ts(1749, 2026, "ts_jr8"),
        evidence_fact_ids=["tf_rxjwkc102_diao67"]),
    ReferentialAssertion(
        id="rr_jry_shidiao", appellation_id="app_jry_shidiao",
        referent_entity_id="ent_jry_diaolou",
        time_span=_ts(1749, 2026, "ts_jr9"),
        evidence_fact_ids=["tf_rxjwkc102_bei_xi"]),
]

# ------------------------------------------------------------------
# 断言与采信：口径冲突全部留证（E9 纪律②：不取区间值）
# ------------------------------------------------------------------

_JRY_PROPOSITIONS: List[Proposition] = [
    Proposition(
        id="prop_jry_found_year",
        statement="健锐云梯营立于乾隆十四年(1749)：御制实胜寺碑记纪年"
                  "「乾隆十有四年嵗在己巳夏五月」与清史稿「乾隆十四年，設雲梯兵一營」"
                  "互证；乾隆十三年是设碉演云梯之年，与立营之年分属两年不可混说",
        derived_from_fact_ids=["tf_rxjwkc102_bei_nian", "tf_qsg130_yunti",
                               "tf_rxjwkc102_bei_li"],
        inferred_subject_id="ent_jry_ying",
        inference_method="当事人御制碑纪年与官书纪年双源互证；金川奏凯在春、"
                         "立营碑记在五月",
        alternative_explanations=[
            "「乾隆十三年设健锐营」说（部分二手叙述将选锋之年当作立营之年，"
            "与碑记纪年不合，不采）",
        ],
    ),
    Proposition(
        id="prop_jry_military_type",
        statement="健锐营属禁旅八旗兵衛之制中的特设营制，非八旗驻防：清史稿卷130将"
                  "「設雲梯兵一營」列于京营兵衛之制，八旗驻防另立畿辅/东三省/各直省/"
                  "籓部四类且不含健锐营；与圆明园八旗护军营同卷并列员额、同驻京西北郊，"
                  "两营并立而非隶属",
        derived_from_fact_ids=["tf_qsg130_yunti", "tf_qsg130_zhufang",
                               "tf_qsg130_ymy"],
        inferred_subject_id="ent_jry_ying",
        inference_method="官书志书结构证据（条目所属门类）＋驻防四类清单排除法",
        alternative_explanations=[
            "「京旗外三营（圆明园护军营＋香山健锐营＋外火器营）」并列口径系"
            "现代通称（海淀区地名志一系），本模块不采为清代官制表述",
        ],
    ),
    Proposition(
        id="prop_jry_diao67",
        statement="香山碉楼总数官书口径为「共計六十有七」（日下旧闻考卷102馆臣按）；"
                  "按卷101/卷102旗册逐旗数（九九七七＋九七七七）加印房四隅合计六十六，"
                  "官书总数与逐旗相加差一——两说并存不取区间值",
        derived_from_fact_ids=["tf_rxjwkc102_diao67", "tf_rxjwkc101_dong",
                               "tf_rxjwkc102_xi", "tf_rxjwkc102_yinfang"],
        inferred_subject_id="ent_jry_diaolou",
        inference_method="同一官书内总数与分计不同合，系馆臣按语间出入；"
                         "采用官书总数口径并保留差异来源",
        alternative_explanations=[
            "现代调查「六十八座/现存十一座」说（无官方测绘档佐证，不列数字）",
        ],
    ),
    Proposition(
        id="prop_jry_yunti_2000",
        statement="碑记称演云梯「逾月得精其技者二千人」，二千为御制碑一手数字"
                  "（精其技者之数，非选锋总数）；近现代著述另有选锋三百名、"
                  "扩至千名/三千名等说，未见清档原文，不列具体数",
        derived_from_fact_ids=["tf_rxjwkc102_bei_xi"],
        inferred_subject_id="ent_jry_yunti",
        inference_method="御制碑记为金川立营当事人一手记录；二手数字无档案只记其说",
        alternative_explanations=[
            "选锋三百名说（大觉寺与团城管理处科普口径）",
            "扩军至千名/三千名说（通行二手说法）",
        ],
    ),
    Proposition(
        id="prop_jry_tuancheng_status",
        statement="团城演武厅现状：1979年市保，1988年移交市文物局并成立管理处，"
                  "2006年列第六批全国重点文物保护单位（国发〔2006〕19号，2006年5月25日"
                  "公布，序号306编号Ⅲ-9，名录名「健锐营演武厅」；管理处沿革页称"
                  "「2006年6月」系公布/转载口径差，两说并存取国务院文件口径）；"
                  "现由北京大觉寺与团城管理处管理并开放为军事武备主题博物馆",
        derived_from_fact_ids=["tf_wjbz_tcywt", "tf_wjbz_guobao6",
                               "tf_wjbz_tcywt_jianzhu"],
        inferred_subject_id="ent_jry_tuancheng",
        inference_method="管理方现行公开沿革＋国务院公布名单核验；"
                         "「至今仍在服役/开放」类现状表述单独核查",
        alternative_explanations=[
            "「2006年6月」公布说（管理处沿革页口径）",
        ],
    ),
]

_JRY_ADOPTIONS: List[BeliefAdoption] = [
    BeliefAdoption(
        proposition_id="prop_jry_found_year", status=EpistemicStatus.VERIFIED,
        confidence=0.95, adopted_by="BHKG校准集",
        rationale="御制碑纪年与官书纪年双源一致，v1 长编「乾隆十四年」得以回源坐实",
    ),
    BeliefAdoption(
        proposition_id="prop_jry_military_type", status=EpistemicStatus.VERIFIED,
        confidence=0.9, adopted_by="BHKG校准集",
        rationale="志书门类结构为硬证据；「特设营制非驻防」写清与圆明园八旗护军营关系",
    ),
    BeliefAdoption(
        proposition_id="prop_jry_diao67", status=EpistemicStatus.VERIFIED,
        confidence=0.85, adopted_by="BHKG校准集",
        rationale="总数与逐旗相加差一两说并存，不取区间值；现代六十八座说不采",
    ),
    BeliefAdoption(
        proposition_id="prop_jry_yunti_2000", status=EpistemicStatus.VERIFIED,
        confidence=0.85, adopted_by="BHKG校准集",
        rationale="碑文一手数字可用；三百名/三千名等二手说无档案不列",
    ),
    BeliefAdoption(
        proposition_id="prop_jry_tuancheng_status", status=EpistemicStatus.VERIFIED,
        confidence=0.9, adopted_by="BHKG校准集",
        rationale="国保批次/编号经国务院文件核验，现状由管理机构官网核查",
    ),
]

# 模块级列表重绑定（文件尾部追加，不改动以上任何既有行）：
# holdout NameRegistry / KnowledgeBase 均按模块属性读取，
# 新词条必须并入同名列表才能进字形表与闸门。
SOURCES = SOURCES + _JRY_SOURCES
DIVISIONS = DIVISIONS + _JRY_DIVISIONS
FACTS = FACTS + _JRY_FACTS
ENTITIES = ENTITIES + _JRY_ENTITIES
STATES = STATES + _JRY_STATES
TRANSFORMATIONS = TRANSFORMATIONS + _JRY_TRANSFORMATIONS
IDENTITIES = IDENTITIES + _JRY_IDENTITIES
APPELLATIONS = APPELLATIONS + _JRY_APPELLATIONS
REFERENCES = REFERENCES + _JRY_REFERENCES
PROPOSITIONS = PROPOSITIONS + _JRY_PROPOSITIONS
ADOPTIONS = ADOPTIONS + _JRY_ADOPTIONS
