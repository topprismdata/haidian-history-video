"""
haidian_kg/calibration/yuanmingyuan.py
圆明园/圆明三园校准实例（BHKG/HHTO v2.1 第二个端到端校准数据集）

设计目的：用第3轮压力测试的第二案例检验 P0-7（聚合与毁损算子）。

第3轮原话：
  「圆明园证明"地名演化"不能代替"空间对象演化"」
  「FISSION/FUSION 应从 Toponym 层搬出去」
  「圆明三园需要 PlaceAggregate，不是 Rename」
  「1860 更不能用 EXTINCTION_FOSSIL」

史料纪律（依第3轮已指出的官方资料约束）：
- 圆明园约始建于康熙四十六年(1707)，最初为胤禛赐园
- 长春园为后来另行兴建；绮春园系乾隆时期由相关旧园空间逐步纳入并定名
- 至乾隆三十五年(1770)前后，圆明、长春、绮春三园格局基本形成
  → 因此"三园集合"是一个【有起点的历史事实】，不是永恒结构
- 1860年英法联军焚毁，1900年再遭进一步毁损
  → 焚毁是 DAMAGED / PARTIALLY_DESTROYED，绝非 extinction
- 1928年北平特别市接管遗址；1976年圆明园管理处成立；1988年遗址公园正式开放
  → "民国遗址公园"若作为正式 institution/place type，从这批材料推不出，
    只能作为历史状态，且须标 CONTESTED

反例留证（第3轮点名必须能表达）：
  题目中的「康熙畅春园 → 乾隆西花园并入改称圆明园 → 拆出长春园/绮春园」
  不是可靠的 identity chain。本校准集不采用该链条。
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
# 1. 文献与篇卷
# ==================================================================

SOURCES: List[HistoricalSource] = [
    # v2.1：一律取自统一书目表，一书一条，禁止在此另建
    source_by_title("圆明园园史资料"),
    source_by_title("圆明园四十景图咏"),
]


DIVISIONS: List[SourceDivision] = [
    SourceDivision(id="div_ymy_yuan_yange", source_id="src_ymy_yuan",
                   volume_number="园史沿革", section_title="建园与焚毁"),
    SourceDivision(id="div_ymy_yuan_1949", source_id="src_ymy_yuan",
                   volume_number="园史沿革", section_title="接管与遗址公园建设"),
    SourceDivision(id="div_ymy_sj", source_id="src_ymy_sijifang",
                   volume_number="卷上", section_title="圆明四十景"),
]

# ==================================================================
# 2. 文本事实
# ==================================================================

FACTS: List[TextualFact] = [
    TextualFact(
        id="tf_ymy_1707", division_id="div_ymy_yuan_yange",
        verbatim_quote="圆明园始建于康熙四十六年(1707)，初为皇四子胤禛赐园。",
        attested_string="圆明园",
    ),
    TextualFact(
        id="tf_ymy_1770", division_id="div_ymy_yuan_yange",
        verbatim_quote="经乾隆朝陆续经营，至乾隆三十五年(1770)前后，圆明、长春、绮春三园格局基本形成。",
        attested_string="三园格局",
    ),
    TextualFact(
        id="tf_ymy_sijifang", division_id="div_ymy_sj",
        verbatim_quote="乾隆十二年(1747)，圆明园四十景图咏成，赐名并绘图咏之。",
        attested_string="四十景",
    ),
    TextualFact(
        id="tf_ymy_1860", division_id="div_ymy_yuan_yange",
        verbatim_quote="咸丰十年(1860)，英法联军攻入北京，圆明园遭焚毁，园内建筑多毁，惟残存建筑与禁园状态延续。",
        attested_string="焚毁",
    ),
    TextualFact(
        id="tf_ymy_1900", division_id="div_ymy_yuan_yange",
        verbatim_quote="1900年八国联军入北京，遗址再遭进一步毁损与掠取。",
        attested_string="再遭毁损",
    ),
    TextualFact(
        id="tf_ymy_1928", division_id="div_ymy_yuan_1949",
        verbatim_quote="1928年，北平特别市接管圆明园遗址。",
        attested_string="接管",
    ),
    TextualFact(
        id="tf_ymy_1988", division_id="div_ymy_yuan_1949",
        verbatim_quote="1976年圆明园管理处成立，1988年圆明园遗址公园正式开放。",
        attested_string="遗址公园",
    ),
]


# ==================================================================
# 3. 持续实体：三个园各自有独立身份
# ==================================================================

ENTITIES: List[PersistentSpatialEntity] = [
    PersistentSpatialEntity(
        id="ent_yuanmingyuan", kind=PhysicalThingKind.GARDEN_COMPLEX,
        canonical_label="圆明园",
    ),
    PersistentSpatialEntity(
        id="ent_changchunyuan", kind=PhysicalThingKind.GARDEN_COMPLEX,
        canonical_label="长春园",
    ),
    PersistentSpatialEntity(
        id="ent_qichunyuan", kind=PhysicalThingKind.GARDEN_COMPLEX,
        canonical_label="绮春园",
    ),
]


# ==================================================================
# 4. 历时状态：形制与毁损全部带时间
# ==================================================================

STATES: List[HistoricalFeatureState] = [
    HistoricalFeatureState(
        id="st_ymy_1770", entity_id="ent_yuanmingyuan",
        time_span=_ts(1707, 1859, "ts_ymy1"),
        geometry="三园格局中的主园，宫殿与园林并置",
        material="木构殿宇配园林土石",
        function="皇家离宫园林",
        evidence_fact_ids=["tf_ymy_1707", "tf_ymy_1770"],
    ),
    # 关键边界：1860年焚毁当年即进入残存态，不得仍返回焚毁前状态
    HistoricalFeatureState(
        id="st_ymy_1860_ruins", entity_id="ent_yuanmingyuan",
        time_span=_ts(1860, 1900, "ts_ymy2"),
        geometry="殿宇多毁，惟残存建筑",
        material="残存砖木，穹砌多已倾圮",
        function="禁园状态（残存建筑与残迹并存）",
        evidence_fact_ids=["tf_ymy_1860"],
    ),
    HistoricalFeatureState(
        id="st_ymy_1900_ruins", entity_id="ent_yuanmingyuan",
        time_span=_ts(1900, 1988, "ts_ymy3"),
        geometry="残迹进一步毁损，地面遗址裸露",
        material="残存砖石零星",
        function="遗址保管（1928年起由地方机构接管）",
        evidence_fact_ids=["tf_ymy_1900", "tf_ymy_1928"],
    ),
    HistoricalFeatureState(
        id="st_ymy_1988_park", entity_id="ent_yuanmingyuan",
        time_span=_ts(1988, 2026, "ts_ymy4"),
        geometry="遗址公园，残迹按原址保护展示",
        material="残存砖石原址",
        function="遗址公园与爱国主义教育基地",
        evidence_fact_ids=["tf_ymy_1988"],
    ),
    HistoricalFeatureState(
        id="st_ccy_1770", entity_id="ent_changchunyuan",
        time_span=_ts(1707, 1860, "ts_ccy1"),
        geometry="三园格局中的附园之一",
        material="园林土石",
        function="皇家离宫园林组成部分",
        evidence_fact_ids=["tf_ymy_1770"],
    ),
    HistoricalFeatureState(
        id="st_qcy_1770", entity_id="ent_qichunyuan",
        time_span=_ts(1770, 1860, "ts_qcy1"),
        geometry="三园格局中的附园之一，由相关旧园空间逐步纳入并定名",
        material="园林土石",
        function="皇家离宫园林组成部分",
        evidence_fact_ids=["tf_ymy_1770"],
    ),
]


# ==================================================================
# 5. 聚合：三园同时并存，不是"一裂为三"
# ==================================================================

AGGREGATES: List[PlaceAggregate] = [
    PlaceAggregate(
        id="agg_yuanming_three", label="圆明三园",
        # 【关键】集合有起点：至乾隆三十五年(1770)前后格局基本形成
        time_span=_ts(1770, 1860, "ts_agg"),
        member_entity_ids=["ent_yuanmingyuan", "ent_changchunyuan", "ent_qichunyuan"],
    ),
]


# ==================================================================
# 6. 空间变化：毁损 ≠ 消亡
# ==================================================================

TRANSFORMATIONS: List[PlaceTransformation] = [
    PlaceTransformation(
        id="pte_ymy_1860", entity_id="ent_yuanmingyuan",
        transformation=PlaceTransformationEvent.PARTIALLY_DESTROYED,
        time_span=_ts(1860, 1860, "ts_t1"),
        resulting_state_id="st_ymy_1860_ruins",
        resulting_condition="殿宇多毁，惟残存建筑与禁园状态",
        evidence_fact_ids=["tf_ymy_1860"],
    ),
    PlaceTransformation(
        id="pte_ymy_1900", entity_id="ent_yuanmingyuan",
        transformation=PlaceTransformationEvent.DAMAGED,
        time_span=_ts(1900, 1900, "ts_t2"),
        resulting_state_id="st_ymy_1900_ruins",
        resulting_condition="残迹进一步毁损与掠取",
        evidence_fact_ids=["tf_ymy_1900"],
    ),
    PlaceTransformation(
        id="pte_ymy_1988", entity_id="ent_yuanmingyuan",
        transformation=PlaceTransformationEvent.REBUILT,
        time_span=_ts(1988, 1988, "ts_t3"),
        resulting_state_id="st_ymy_1988_park",
        resulting_condition="遗址公园开放，残迹原址保护",
        evidence_fact_ids=["tf_ymy_1988"],
    ),
]


# ==================================================================
# 7. 身份断言：三园彼此是什么关系
# ==================================================================

IDENTITIES: List[DiachronicIdentityAssertion] = [
    DiachronicIdentityAssertion(
        id="dia_ymy_ccy_relation",
        subject_entity_ids=["ent_yuanmingyuan", "ent_changchunyuan"],
        relation=IdentityRelation.UNCERTAIN,
        time_span=_ts(1707, 1770, "ts_dia1"),
        evidence_fact_ids=["tf_ymy_1707", "tf_ymy_1770"],
        status=EpistemicStatus.CONTESTED,
        alternative_relations=[
            "长春园系后来另行兴建，非由圆明园分裂而来",
            "具体营建先后与空间交叠关系学界记载不一",
        ],
    ),
    DiachronicIdentityAssertion(
        id="dia_ymy_same_after_1860",
        subject_entity_ids=["ent_yuanmingyuan"],
        relation=IdentityRelation.SAME_CONTINUANT,
        time_span=_ts(1860, 2026, "ts_dia2"),
        evidence_fact_ids=["tf_ymy_1860", "tf_ymy_1900", "tf_ymy_1988"],
        status=EpistemicStatus.VERIFIED,
        alternative_relations=[],
    ),
]


# ==================================================================
# 8. 名称与指称
# ==================================================================

APPELLATIONS: List[Appellation] = [
    Appellation(id="app_ymy", label="圆明园",
                kind=AppellationKind.OFFICIAL, valid_time_span=_ts(1707, 2026, "ts_n1"),
                attesting_fact_ids=["tf_ymy_1707"]),
    Appellation(id="app_ccy", label="长春园",
                kind=AppellationKind.OFFICIAL, valid_time_span=_ts(1707, 2026, "ts_n2"),
                attesting_fact_ids=["tf_ymy_1770"]),
    Appellation(id="app_qcy", label="绮春园",
                kind=AppellationKind.OFFICIAL, valid_time_span=_ts(1770, 2026, "ts_n3"),
                attesting_fact_ids=["tf_ymy_1770"]),
    Appellation(id="app_sansanyuan", label="圆明三园",
                kind=AppellationKind.OFFICIAL, valid_time_span=_ts(1770, 1860, "ts_n4"),
                attesting_fact_ids=["tf_ymy_1770"]),
    Appellation(id="app_yiyizhiyuan", label="遗址公园",
                kind=AppellationKind.OFFICIAL, valid_time_span=_ts(1988, 2026, "ts_n5"),
                attesting_fact_ids=["tf_ymy_1988"]),
]

REFERENCES: List[ReferentialAssertion] = [
    ReferentialAssertion(
        id="rr_ymy", appellation_id="app_ymy",
        referent_entity_id="ent_yuanmingyuan", time_span=_ts(1707, 2026, "ts_r1"),
        evidence_fact_ids=["tf_ymy_1707"],
    ),
    ReferentialAssertion(
        id="rr_sansanyuan", appellation_id="app_sansanyuan",
        # 【第3轮§6】"圆明三园"指三个园组成的集合，不是某一个园
        referent_entity_id="ent_yuanmingyuan", time_span=_ts(1770, 1860, "ts_r2"),
        evidence_fact_ids=["tf_ymy_1770"],
        status=EpistemicStatus.CONTESTED,
    ),
    ReferentialAssertion(
        id="rr_yiyizhiyuan", appellation_id="app_yiyizhiyuan",
        referent_entity_id="ent_yuanmingyuan", time_span=_ts(1988, 2026, "ts_r3"),
        evidence_fact_ids=["tf_ymy_1988"],
    ),
]


# ==================================================================
# 9. 断言与采信
# ==================================================================

PROPOSITIONS: List[Proposition] = [
    Proposition(
        id="prop_1860_not_extinction",
        statement="1860年焚毁未导致圆明园地点消亡，其后仍有残存建筑、禁园与遗址保管",
        derived_from_fact_ids=["tf_ymy_1860", "tf_ymy_1900", "tf_ymy_1928"],
        inferred_subject_id="ent_yuanmingyuan",
        inference_method="1860、1900、1928、1988 四条书证连续证明地点持续存在",
        alternative_relations=[],
    ),
    Proposition(
        id="prop_sansanyuan_aggregate",
        statement="圆明、长春、绮春三园在1770至1860年间并存构成集合",
        derived_from_fact_ids=["tf_ymy_1770"],
        inferred_subject_id="ent_yuanmingyuan",
        inference_method="《园史沿革》明载三园格局基本形成",
        alternative_relations=["具体各园空间交叠范围学界记载不一"],
    ),
    Proposition(
        id="prop_minguo_park_unproven",
        statement="『民国遗址公园』作为正式机构名称，从现有材料推不出",
        derived_from_fact_ids=["tf_ymy_1928"],
        inferred_subject_id="ent_yuanmingyuan",
        inference_method="1928年仅记接管，未见以『遗址公园』为正式名之记载",
        alternative_relations=["可能存在他处所称民国时期公园化管理的次级记载，待考"],
    ),
]

ADOPTIONS: List[BeliefAdoption] = [
    BeliefAdoption(
        proposition_id="prop_1860_not_extinction",
        status=EpistemicStatus.VERIFIED, confidence=0.95,
        adopted_by="BHKG校准集",
        rationale="四条连续书证，地点未消亡，判定确证",
    ),
    BeliefAdoption(
        proposition_id="prop_sansanyuan_aggregate",
        status=EpistemicStatus.VERIFIED, confidence=0.9,
        adopted_by="BHKG校准集",
        rationale="《园史沿革》明载三园格局形成",
    ),
    BeliefAdoption(
        proposition_id="prop_minguo_park_unproven",
        status=EpistemicStatus.UNSUBSTANTIATED, confidence=0.3,
        adopted_by="BHKG校准集",
        rationale="无据推论，材料不足，不得作为定论使用",
    ),
]
