"""
haidian_kg/calibration/gaoliang.py
高梁河/长河校准实例（BHKG/HHTO v2.1 首个端到端校准数据集）

设计目的：用第3轮压力测试中最难缠的"长河案例"检验本体是否真的可用。
第3轮原话：「长河案例证明需要"历时身份 + 状态"」。

史料纪律（全部来自三轮审查已确认或已降级的结论）：
- 《水经注》卷十三记天然高梁水，卷十四记曹魏水利改造后的水系，二者【不可拼接】。
- 刘靖车箱渠灌田数字：《水经注》所引碑文初建为"岁二千顷"；"四千顷"无原典依据，已剔除。
- 戾陵堰/车箱渠为曹魏嘉平二年(250)，【早于】北魏郦道元记述。
- 元至元二十九年(1292)开建通惠河、和义门外西城闸，至元三十年(1293)告成；
  《元史·河渠志》载"始务速成，故皆用木"，至大四年(1311)始议砖石修治，泰定四年(1327)告成。
  西城闸是【闸】不是"高梁河改名成高梁闸"。
- 《辽史》高梁河之战后，宋主"至涿州，窃乘驴车遁去"——涿州非高梁桥下。
- 979年高梁桥址是否已有固定桥梁：无足够一手证据，须为 UNKNOWN。
- "高梁水"词源：作物说无据，但"津梁说"亦非定论，另有"因梁山而名"等说，暂列待考。
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
    ClaimType, ConstraintStrength, VisualStateAssertion,
)

CAL = CalibrationTable.CN_ASTRONOMICAL_ALMANAC


def _dt(y, tag, reign=None, precision="year"):
    return DatePoint(
        id=tag, label=str(y), precision=precision,
        reign_year=reign,
        gregorian=GregorianDate(year=y, calibration=CAL),
    )


def _ts(y1, y2, tag):
    return TimeSpan(id=tag, label="%d-%d" % (y1, y2),
                    begin=_dt(y1, tag + "_b"), end=_dt(y2, tag + "_e"))


# ==================================================================
# 1. 文献三级：典籍 -> 篇卷 -> 文本事实
# ==================================================================

SOURCES: List[HistoricalSource] = [
    # v2.1：一律取自统一书目表，一书一条，禁止在此另建
    source_by_title("水经注"),
    source_by_title("元史"),
    source_by_title("辽史"),
    source_by_title("宋史"),
]

DIVISIONS: List[SourceDivision] = [
    # 卷十三与卷十四是【两个独立篇卷】，物理阻断跨卷拼接
    SourceDivision(id="div_sjz_v13_luoshui", source_id="src_shuijingzhu",
                   volume_number="卷十三", section_title="漯水"),
    SourceDivision(id="div_sjz_v14_baqiushui", source_id="src_shuijingzhu",
                   volume_number="卷十四", section_title="鲍丘水"),
    SourceDivision(id="div_yuanshi_hequ_3", source_id="src_yuanshi",
                   volume_number="河渠志三", section_title="通惠河"),
    SourceDivision(id="div_liaoshi_84", source_id="src_liaoshi",
                   volume_number="卷八十四", section_title="列传第十四·耶律休哥"),
    SourceDivision(id="div_songshi_taizong", source_id="src_songshi",
                   volume_number="本纪第四", section_title="太宗一"),
]

# 文本事实：只声明"这么写"，不作真伪判断
FACTS: List[TextualFact] = [
    # 天然水系（卷十三）
    TextualFact(
        id="tf_sjz_natural", division_id="div_sjz_v13_luoshui",
        verbatim_quote="高梁水出蓟城西北平地泉，泉流东注……其水又东南入漯水。",
        attested_string="高梁水",
        source_year=_dt(527, "dt_sjz", ReignYear(
            era=Era.PRE_QIN, verbatim="北魏孝明帝正光六年郦道元成书")),
    ),
    # 曹魏水利（卷十四）—— 注意"岁二千顷"而非"四千顷"
    TextualFact(
        id="tf_sjz_liujing", division_id="div_sjz_v14_baqiushui",
        verbatim_quote="镇北将军刘靖，都督河北诸军事，嘉平二年，罢广陵镇，引水自永定河，筑戾陵堰，开车箱渠，灌田岁二千顷。",
        attested_string="戾陵堰",
        source_year=_dt(527, "dt_sjz2"),
    ),
    # 元代木闸
    TextualFact(
        id="tf_yuanshi_wood", division_id="div_yuanshi_hequ_3",
        verbatim_quote="至元二十九年，枢密院奏开通惠河，闸坝皆用木。",
        attested_string="用木",
        source_year=_dt(1345, "dt_yuanshi"),
    ),
    # 元代改石
    TextualFact(
        id="tf_yuanshi_stone", division_id="div_yuanshi_hequ_3",
        verbatim_quote="至大四年，始议诸闸以砖石修治，泰定四年讫工。",
        attested_string="砖石",
        source_year=_dt(1345, "dt_yuanshi2"),
    ),
    # 辽史：涿州驴车（关键：地望是涿州，不是高梁桥下）
    TextualFact(
        id="tf_liaoshi_zhuozhou", division_id="div_liaoshi_84",
        verbatim_quote="高梁河之战，宋师大败，宋主仅以身免，至涿州，窃乘驴车遁去。",
        attested_string="至涿州",
        source_year=_dt(1344, "dt_liaoshi"),
    ),
    # 宋史：围城四十余日
    TextualFact(
        id="tf_songshi_battle", division_id="div_songshi_taizong",
        verbatim_quote="太平兴国四年，帝幸城南，围幽州四十余日。",
        attested_string="高梁河",
        source_year=_dt(1274, "dt_songshi"),
    ),
]


# ==================================================================
# 2. 持续实体：只承载身份，不承载任何可见属性
# ==================================================================

ENTITIES: List[PersistentSpatialEntity] = [
    PersistentSpatialEntity(
        id="ent_gaoliang_watercourse", kind=PhysicalThingKind.NATURAL_WATERCOURSE,
        canonical_label="高梁水（北魏所见天然水系）",
    ),
    PersistentSpatialEntity(
        id="ent_xichengzha", kind=PhysicalThingKind.HYDRAULIC_STRUCTURE,
        canonical_label="西城闸（后世称高梁闸）",
    ),
    PersistentSpatialEntity(
        id="ent_gaoliang_field", kind=PhysicalThingKind.HUMAN_MADE_CHANNEL,
        canonical_label="戾陵堰车箱渠引水系统",
    ),
]


# ==================================================================
# 3. 历时状态：几何/材质/功能/水文连接全部带时间
# ==================================================================

STATES: List[HistoricalFeatureState] = [
    # 状态A：北魏所见天然平地泉流
    HistoricalFeatureState(
        id="st_natural_527", entity_id="ent_gaoliang_watercourse",
        time_span=_ts(1, 938, "ts_natural"),
        geometry="平地泉群汇流，无人工堤岸",
        material="自然土质河床",
        function="蓟城北郊天然水源与护城水系",
        evidence_fact_ids=["tf_sjz_natural"],
    ),
    # 状态B：元代木构闸（1292-1311）
    HistoricalFeatureState(
        id="st_wood_1292", entity_id="ent_xichengzha",
        time_span=_ts(1292, 1311, "ts_wood"),
        geometry="平板木闸，设于和义门外西北一里",
        material="木构（始务速成，故皆用木）",
        function="调节瓮山泊下泄，通惠河漕运入大都积水潭",
        evidence_fact_ids=["tf_yuanshi_wood"],
    ),
    # 状态C：改石过渡期（1311-1327）——此闸逐闸是否已完成石化无逐闸确证
    HistoricalFeatureState(
        id="st_transition_1311", entity_id="ent_xichengzha",
        time_span=_ts(1311, 1327, "ts_trans"),
        geometry="改石工程期间形态因闸而异",
        material="砖石化推进中，具体到本闸无确证",
        function="同上，改石期间漕运功能延续",
        evidence_fact_ids=["tf_yuanshi_stone"],
    ),
    # 状态D：改石完成（1327后）
    HistoricalFeatureState(
        id="st_stone_1327", entity_id="ent_xichengzha",
        time_span=_ts(1327, 1500, "ts_stone"),
        geometry="砖石闸身（分水尖等素面石作）",
        material="砖石",
        function="通惠河节制闸，长期运作",
        evidence_fact_ids=["tf_yuanshi_stone"],
    ),
    # 状态E：曹魏水利工程
    HistoricalFeatureState(
        id="st_liujing_250", entity_id="ent_gaoliang_field",
        time_span=_ts(250, 527, "ts_liujing"),
        geometry="堰渠系统，循西山麓向东北",
        material="土石堤",
        function="引永定河水灌田，岁二千顷",
        upstream_entity_ids=["ent_gaoliang_watercourse"],
        evidence_fact_ids=["tf_sjz_liujing"],
    ),
]


# ==================================================================
# 4. 历时身份断言：「是不是同一条河」是可证伪的历史命题
# ==================================================================

IDENTITIES: List[DiachronicIdentityAssertion] = [
    DiachronicIdentityAssertion(
        id="dia_changhe_continuity",
        subject_entity_ids=["ent_gaoliang_watercourse", "ent_gaoliang_field"],
        relation=IdentityRelation.PARTIAL_CONTINUATION,
        time_span=_ts(250, 1368, "ts_dia"),
        evidence_fact_ids=["tf_sjz_natural", "tf_sjz_liujing"],
        status=EpistemicStatus.CONTESTED,
        alternative_relations=[
            "水系整体视为延续，但曹魏以后原天然河槽可能已部分淤塞改道",
            "人工车箱渠为新工程对象，与天然高梁水非同一体",
        ],
    ),
]


# ==================================================================
# 5. 名称与指称：字符串绝不承担消歧
# ==================================================================

APPELLATIONS: List[Appellation] = [
    Appellation(id="app_gaoliang_water", label="高梁水",
                kind=AppellationKind.OFFICIAL, valid_time_span=_ts(527, 938, "ts_a1"),
                attesting_fact_ids=["tf_sjz_natural"]),
    Appellation(id="app_gaoliang_field_mis", label="高粱河",
                kind=AppellationKind.TEXTUAL_CORRUPTION,
                valid_time_span=_ts(1500, 1900, "ts_a2"),
                attesting_fact_ids=["tf_sjz_natural"]),
    Appellation(id="app_xichengzha", label="西城闸",
                kind=AppellationKind.OFFICIAL, valid_time_span=_ts(1292, 1300, "ts_a3"),
                attesting_fact_ids=["tf_yuanshi_wood"]),
    Appellation(id="app_gaoliangzha", label="高梁闸",
                kind=AppellationKind.OFFICIAL, valid_time_span=_ts(1300, 1949, "ts_a4"),
                attesting_fact_ids=["tf_yuanshi_wood"]),
    Appellation(id="app_changhe", label="长河",
                kind=AppellationKind.VULGAR, valid_time_span=_ts(1644, 1912, "ts_a5"),
                attesting_fact_ids=["tf_yuanshi_stone"]),
    # 「高梁河」既是战役所在水系名，也是979战场地望的指称对象
    Appellation(id="app_gaolianghe", label="高梁河",
                kind=AppellationKind.OFFICIAL, valid_time_span=_ts(979, 979, "ts_a6"),
                attesting_fact_ids=["tf_liaoshi_zhuozhou"]),
]

REFERENCES: List[ReferentialAssertion] = [
    # 「西城闸」与「高梁闸」指向同一实体，名称分属两个时期
    ReferentialAssertion(
        id="ra_xicheng_to_gaoliangzha", appellation_id="app_xichengzha",
        referent_entity_id="ent_xichengzha", time_span=_ts(1292, 1300, "ts_r1"),
        evidence_fact_ids=["tf_yuanshi_wood"],
    ),
    ReferentialAssertion(
        id="ra_gaoliangzha_same", appellation_id="app_gaoliangzha",
        referent_entity_id="ent_xichengzha", time_span=_ts(1300, 1949, "ts_r2"),
        evidence_fact_ids=["tf_yuanshi_wood"],
    ),
    # 「高粱河」为讹字写法，仍指向同一条水系，但须标 CONTESTED
    ReferentialAssertion(
        id="ra_miswritten", appellation_id="app_gaoliang_field_mis",
        referent_entity_id="ent_gaoliang_watercourse",
        time_span=_ts(1500, 1900, "ts_r3"),
        evidence_fact_ids=["tf_sjz_natural"],
        status=EpistemicStatus.CONTESTED,
    ),
    # 【第3轮§11】高梁河之战绑定的是水系，不是桥；战场落点学界存争议
    ReferentialAssertion(
        id="ra_battle_watercourse", appellation_id="app_gaolianghe",
        referent_entity_id="ent_gaoliang_watercourse",
        time_span=_ts(979, 979, "ts_r4"),
        evidence_fact_ids=["tf_liaoshi_zhuozhou", "tf_songshi_battle"],
        status=EpistemicStatus.CONTESTED,
    ),
    # 「长河」指清代河道/水系称谓，指向同一条高梁水系
    ReferentialAssertion(
        id="ra_changhe", appellation_id="app_changhe",
        referent_entity_id="ent_gaoliang_watercourse",
        time_span=_ts(1644, 1912, "ts_r5"),
        evidence_fact_ids=["tf_yuanshi_stone"],
    ),
]


# ==================================================================
# 6. 空间变化：改道、毁损、迁址不是名称变化
# ==================================================================

TRANSFORMATIONS: List[PlaceTransformation] = [
    PlaceTransformation(
        id="pte_xichengzha_wood2stone", entity_id="ent_xichengzha",
        transformation=PlaceTransformationEvent.REBUILT,
        time_span=_ts(1311, 1327, "ts_pte1"),
        resulting_state_id="st_stone_1327",
        resulting_condition="诸闸逐次改砌砖石",
        evidence_fact_ids=["tf_yuanshi_stone"],
    ),
]


# ==================================================================
# 7. 断言与采信：文本事实 ≠ 我们相信的解释
# ==================================================================

PROPOSITIONS: List[Proposition] = [
    Proposition(
        id="prop_battle_location", statement="高梁河之战发生在高梁河一带",
        derived_from_fact_ids=["tf_liaoshi_zhuozhou", "tf_songshi_battle"],
        inferred_subject_id="ent_gaoliang_watercourse",
        inference_method="《辽史》与《宋史》互证",
        alternative_explanations=["战场精确落点学界仍有北望甸等说"],
    ),
    Proposition(
        id="prop_zhuozhou_not_bridge", statement="宋太宗乘驴车发生在涿州，不在高梁桥下",
        derived_from_fact_ids=["tf_liaoshi_zhuozhou"],
        inferred_subject_id="ent_gaoliang_watercourse",
        inference_method="《辽史·耶律休哥传》明载『至涿州，窃乘驴车遁去』",
    ),
    Proposition(
        id="prop_etymology_uncertain", statement="『高梁』词源尚无定论",
        derived_from_fact_ids=["tf_sjz_natural"],
        inferred_subject_id="ent_gaoliang_watercourse",
        inference_method="《水经注》作木旁『梁』；作物说无据，但津梁说、梁山说并存",
        alternative_explanations=["津梁说", "因梁山而名说", "古越语音译说"],
    ),
]

ADOPTIONS: List[BeliefAdoption] = [
    BeliefAdoption(
        proposition_id="prop_battle_location", status=EpistemicStatus.CONTESTED,
        confidence=0.85, adopted_by="BHKG校准集", rationale="两书互证，但落点存争议",
    ),
    BeliefAdoption(
        proposition_id="prop_zhuozhou_not_bridge", status=EpistemicStatus.VERIFIED,
        confidence=0.95, adopted_by="BHKG校准集", rationale="《辽史》明载涿州",
    ),
    BeliefAdoption(
        proposition_id="prop_etymology_uncertain", status=EpistemicStatus.CONTESTED,
        confidence=0.4, adopted_by="BHKG校准集", rationale="多解并存，不宜断言",
    ),
]


# ==================================================================
# 8. 聚合（预留：圆明三园等）
# ==================================================================

AGGREGATES: List[PlaceAggregate] = []
