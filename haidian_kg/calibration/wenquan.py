# -*- coding: utf-8 -*-
"""haidian_kg/calibration/wenquan.py

E28《温泉·「温泉」之前叫「石窝」》知识库校准模块。

本集定位（承 E26 纵向层累之后的首例变体）：
    E26 的主命题是名号沿革链本身；本集是「层累 ＋ 证伪」双主轴——
    ① 正向：泉名→堂名→山名→村名→镇名的五段接力，且**改名年代无书证**；
    ② 反向：库内两条温泉旧录（伪《帝京景物略》引文、「香水院＝温泉后山」）
       被一手文献证伪——本模块只建模证伪结论，不重复录入伪引文本身
       （伪引文已由 extractor 层 attest_wenquan_dijing 降级 L6_DISPROVEN，
       详见 tests/haidian_kg/test_e27_e28_claim_downgrades.py 的锁死测试）。

五条核心裁决（与设计规范 V-NC 一一对应）：
    V-NC01  万历官书《宛署杂记》正式村名是**石窝村**；「温泉」先泉名、
            正德甲戌（一五一四）成堂名、明末文献已立村名目。
            **改名具体年代无直接书证，严禁系于某年**。
    V-NC03  库内伪引《帝京景物略》「平地温泉如沸……驻跸沐浴之所」已判死：
            《帝京景物略》原文具在而无此句（肯定性反证，非 absence of
            evidence），故伪引命题可判 DISPROVEN。
    V-NC04  香水院断碑在**妙高峰法云寺**，「香水院＝温泉后山」判 DISPROVEN；
            八院（六院）名目与今地对应除清水院＝大觉寺有辽碑直证外
            均为后世考释。
    V-NC05  国保口径（L4 机构口径，编号原名单待复核——研究档案存疑 17）：
            辛亥滦州起义纪念园＝第六批（2006-05-25，6-886）；
            黑龙潭及龙王庙＝大运河子项（第六批 6-810 → 第七批 7-1973-3-009）。
            两处均非 1961 第一批。**因本地查无名单原件逐字行，国保口径
            不建 TextualFact，只入命题层并显式标注 L4 依据与待核状态**
            （承 E26「查无逐字书证者不建成 TextualFact」纪律）。
    V-NC06  泉眼今日存续状态未考得：仍在涌流／早已干涸两说均判
            UNSUBSTANTIATED（absence of evidence ≠ evidence of absence）；
            「慈禧题字」「故宫石料」同此。

Python 3.9.6 兼容：禁 X | None，禁 match。
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
    ReferentialAssertion,
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
    source_by_title("宛署杂记"),
    source_by_title("帝京景物略"),
    # 🔴 国保名单（第六批/第七批）不立书源篇卷：本地查无名单原件逐字行，
    #    研究档案存疑 17 明示「须与国务院公布名单原件复核」。
    #    按 E26 纪律：查无逐字书证者不建 TextualFact，故国保口径只入命题层。
]

DIVISIONS: List[SourceDivision] = [
    # 《宛署杂记》「温泉堂」条：电子文本经 ctext 核录，卷次待与刻本复核
    # （研究档案存疑 3：一说卷十六；成书年通行万历二十一年，另有二十年说）
    SourceDivision(id="div_e28_wanshu_wenquantang", source_id="src_wanshu",
                   volume_number="卷次待核（一说卷十六）",
                   section_title="温泉堂"),
    # 《帝京景物略》三条：通行归卷五「西城外」，卷次待与刻本复核（存疑 4）
    SourceDivision(id="div_e28_dijing_wenquan", source_id="src_dijingjingwulue",
                   volume_number="卷五西城外（通行归卷，待核）",
                   section_title="温泉"),
    SourceDivision(id="div_e28_dijing_heilongtan", source_id="src_dijingjingwulue",
                   volume_number="卷五西城外（通行归卷，待核）",
                   section_title="黑龙潭"),
    SourceDivision(id="div_e28_dijing_xiangshuiyuan", source_id="src_dijingjingwulue",
                   volume_number="卷五西城外（通行归卷，待核）",
                   section_title="法云寺（妙高峰·香水院断碑条）"),
]


# ==================================================================
# 文本事实层：四条逐字书证
# ==================================================================

FACTS: List[TextualFact] = [
    # 1.《宛署杂记》「温泉堂」条 —— 本集第一关键书证：
    #    万历官书里的正式村名是「石窩村」，不叫温泉村。
    TextualFact(
        id="fact_e28_wanshu_shiwo",
        division_id="div_e28_wanshu_wenquantang",
        verbatim_quote=("溫泉堂，在石窩村，離城五十里。本村有山，曰堂子山，"
                        "下有溫泉，正德甲戌谷太監建堂於其上，因名。"
                        "右僉都御史陳天祥記。"),
        attested_string="溫泉堂在石窩村；堂子山；正德甲戌谷太監建堂",
        source_year=_dt(1593, "dt_e28_wanshu"),
        translator_note=(
            "明万历年间宛平知县沈榜修《宛署杂记》（L3 明代官修志书；成书年"
            "通行万历二十一年，另有万历二十年说，本集只说「明万历年间」）。"
            "**逐字考订要点**：①「在**石窩村**」——万历官书正式村名是石窝村"
            "（采石场村），不是温泉村，本集改名无书证裁决的第一证据；"
            "②「離城五十里」——与今温泉村距旧城里程量级相合，且可与"
            "房山大石窝（同名异地）区分；③「曰堂子山」——山名明代写法；"
            "④「下有溫泉」——官书直证山下温泉出露，得名的实物前提；"
            "⑤「**正德甲戌**」——干支即正德九年（一五一四），温泉堂始建之年；"
            "⑥「谷太監建堂於其上」——仅存姓氏，名未考得；"
            "⑦「右僉都御史陳天祥記」——堂曾有撰记碑，今无存世记录。"
            "引文按原刻繁体字形，卷次待核（存疑 3）。"
        ),
    ),
    # 2.《帝京景物略》「温泉」条 —— 明末文献已以「温泉」立目；
    #    同时是伪引文的肯定性反证（原文具在而无「平地温泉如沸……」句）。
    TextualFact(
        id="fact_e28_dijing_wenquan",
        division_id="div_e28_dijing_wenquan",
        verbatim_quote=("山北十里，平疇良苗，溫泉出焉。泉如湯未至沸時，"
                        "甃而為池，以待浴者。泉雖溫乎，其出，能藻，能蟲魚，"
                        "禾黍早成，早於他之秋再旬。林後凋，草色久駐，"
                        "晚於他之秋再旬。資泉之民，無苦瘍躄。泉前數武，"
                        "有碧霞殿，單楹板扉。泉而東六十里，大湯山，又一溫泉。"
                        "再東三里，小湯山，又一溫泉。"),
        attested_string="溫泉出焉；甃而為池以待浴者；大湯山；小湯山",
        source_year=_dt(1635, "dt_e28_dijing_wq"),
        translator_note=(
            "刘侗、于奕正《帝京景物略》（崇祯八年刊，一六三五；L3 明末笔记）。"
            "**逐字考订要点**：①「山北十里」之「山」原文未指明，诸比定与今"
            "里程不合——只引原文，不断言山名（存疑 5）；②「泉如**湯未至沸時**」"
            "——水温精确描写；③「**甃而為池，以待浴者**」——泉被砌成浴池、"
            "对公众开放，民间的汤池不是皇家禁地；④「早於他之秋再旬……"
            "晚於他之秋再旬」——地热小气候物候观察；⑤「無苦瘍躄」——"
            "泉浴疗愈口碑；⑥「碧霞殿」今无存世记录（存疑 7）；"
            "⑦「泉而東六十里，大湯山……再東三里，小湯山」——地理锚点，"
            "坐实所记即今海淀温泉村之泉。"
            "🔴 **本条同时是伪引文的肯定性反证**：《帝京景物略》原文具在，"
            "其中并无「平地温泉如沸，冬月白气滃然，辽金帝王驻跸沐浴之所」句——"
            "伪引命题据此判 DISPROVEN（非 absence of evidence）。"
            "引文按原刻繁体字形，卷次待核（存疑 4）。"
        ),
    ),
    # 3.《帝京景物略》「黑龙潭」条 —— 「祈」（冷泉）侧的一手明录。
    TextualFact(
        id="fact_e28_dijing_heilongtan",
        division_id="div_e28_dijing_heilongtan",
        verbatim_quote=("黑龍潭在金山口北，依崗有龍王廟，碧殿丹垣，廊前為潭，"
                        "土人云有黑龍潛其中，故名黑龍潭。"),
        attested_string="黑龍潭；龍王廟；故名黑龍潭",
        source_year=_dt(1635, "dt_e28_dijing_hlt"),
        translator_note=(
            "《帝京景物略》「黑龙潭」条（L3；**系现代整理转引，上片前须回核"
            "明刻本／通行点校本**——研究档案存疑 4 尤指此条）。"
            "**逐字要点**：「**土人云**」三字表明「黑龍潛其中」系采俗说，"
            "刘侗本人只记庙与潭。与「温泉」条同卷相邻，构成明代文本里"
            "一冷一热两眼泉的并置：黑龙潭（冷泉、祈雨）与温泉（热泉、浴疗）"
            "相去数里——「祈」与「浴」分属两泉两庙，不得合并。"
        ),
    ),
    # 4.《帝京景物略》香水院断碑条 —— 「香水院＝温泉后山」的肯定性反证。
    TextualFact(
        id="fact_e28_dijing_xiangshuiyuan",
        division_id="div_e28_dijing_xiangshuiyuan",
        verbatim_quote="金章宗設六院遊覽，此其一院。草際斷碑，『香水院』三字存焉。",
        attested_string="香水院；斷碑；六院",
        source_year=_dt(1635, "dt_e28_dijing_xsyy"),
        translator_note=(
            "《帝京景物略》妙高峰法云寺条（L3，卷次待核）。明代人亲眼见过"
            "刻着「香水院」三字的断碑，位置在**妙高峰法云寺**，不在温泉后山——"
            "「西山八大水院之香水院＝温泉后山」（本库 era4_liao_jin.md 旧对应）"
            "据此判 DISPROVEN。🔴 两点纪律：①《帝京景物略》且作「**六院**」，"
            "诸本对八院名目与今地对应互异；②除清水院＝大觉寺有辽碑直证外，"
            "其余诸院与今地对应均为后世考释，温泉与金章宗的关联一律标"
            "「无据，存疑」。"
        ),
    ),
]


# ==================================================================
# 🔴 查无逐字书证者：不建成 TextualFact（承 E26 纪律）
# ------------------------------------------------------------------
# 下列五项**广见于各类叙述**，但截至 2026-10-04 未核到可逐字引用的
# 原件或原刊句，一律不进书证层（schema 的 verbatim_quote 非空硬阻断
# 正是为此设立）：
#
#   ① 国保口径：辛亥滦州起义纪念园＝第六批（2006-05-25，6-886）、
#      黑龙潭及龙王庙＝大运河子项（6-810 → 7-1973-3-009，另 1984 年
#      第三批北京市文保）——L4 机构口径，名单原件逐字行未落盘，
#      编号待与国务院公布名单原件复核（研究档案存疑 17）。
#   ② 黑龙潭龙王庙成化二十二年（一四八六）建庙碑、康熙二十年重建、
#      乾隆三年封「昭靈沛澤龍王之神」、黄琉璃筒瓦——区文委/机构口径转述。
#   ③ 显龙山明洪武二十七年（一三九四）、正统十年（一四四五）采石匠题记
#      ——区保条目口径转述，摩崖原文逐字未录。
#   ④ 「水流云在」崖刻与英敛之题注——题注见于研究档案转录，实物拓本未核。
#   ⑤ 滦州纪念坊「民國二十五年十一月馮玉祥」落款——机构口径转录。
#
# 这些内容在片中照常陈述并按「机构口径/转述」标注上屏；
# 证据等级不得冒标 L2 一手书证。
# ==================================================================


# ==================================================================
# 空间实体：泉、堂、山、纪念建筑群
# ==================================================================

ENTITIES: List[PersistentSpatialEntity] = [
    PersistentSpatialEntity(
        id="ent_e28_wenquan_spring",
        kind=PhysicalThingKind.NATURAL_SPRING,
        canonical_label="温泉泉眼（堂子山下温泉出露点；今日存续状态未考得）",
    ),
    PersistentSpatialEntity(
        id="ent_e28_wenquantang",
        kind=PhysicalThingKind.SINGLE_BUILDING,
        canonical_label="温泉堂（正德甲戌谷太监建于堂子山上；今无存世记录）",
    ),
    PersistentSpatialEntity(
        id="ent_e28_tangzishan",
        kind=PhysicalThingKind.MOUNTAIN,
        canonical_label="堂子山（又名显龙山；石灰岩，在温泉村南）",
    ),
    PersistentSpatialEntity(
        id="ent_e28_heilongtan_longwangmiao",
        kind=PhysicalThingKind.RELIGIOUS_PRECINCT,
        canonical_label="黑龙潭及龙王庙（金山口北；皇家祈雨之所，冷泉）",
    ),
    PersistentSpatialEntity(
        id="ent_e28_luanzhou_memorial",
        kind=PhysicalThingKind.MODERN_INSTITUTION,
        canonical_label="辛亥滦州起义纪念园（显龙山南麓；第六批国保 6-886 口径）",
    ),
]

ENTITIES_MAP: Dict[str, PersistentSpatialEntity] = {e.id: e for e in ENTITIES}

APPELLATIONS: List[Appellation] = [
    # 村名层：万历官书正式村名仍是石窝村；「温泉」明末文献已用。
    # 🔴 改名具体年代无书证——「石窝村」的时段下限只画到万历朝末，
    #    与「温泉村」的起点（帝京景物略刊年）之间**不接续、留缺口**，
    #    缺口即「无书证段」，不得用估计年份填平（V-NC01）。
    Appellation(
        id="app_e28_shiwo_village",
        label="石窝村",
        kind=AppellationKind.OLD_NAME,
        valid_time_span=_ts(1394, 1620, "ts_app_e28_shiwo"),
        attesting_fact_ids=["fact_e28_wanshu_shiwo"],
    ),
    Appellation(
        id="app_e28_wenquan_village",
        label="温泉村",
        kind=AppellationKind.OFFICIAL,
        valid_time_span=_ts(1635, 2026, "ts_app_e28_wq_village"),
        attesting_fact_ids=["fact_e28_dijing_wenquan"],
    ),
    # 山名层：明称堂子山；显龙山得名年代未考得（下限 1931 年墓园记录已用，
    # 上限清末民初——存疑 11），时段起点取可证下限。
    Appellation(
        id="app_e28_tangzishan",
        label="堂子山",
        kind=AppellationKind.OLD_NAME,
        valid_time_span=_ts(1514, 1911, "ts_app_e28_tzs"),
        attesting_fact_ids=["fact_e28_wanshu_shiwo"],
    ),
    Appellation(
        id="app_e28_xianlongshan",
        label="显龙山",
        kind=AppellationKind.OFFICIAL,
        valid_time_span=_ts(1931, 2026, "ts_app_e28_xls"),
        attesting_fact_ids=[],
    ),
    # 堂名层：泉名成堂名（官书自证「因名」）。
    Appellation(
        id="app_e28_wenquantang",
        label="温泉堂",
        kind=AppellationKind.OLD_NAME,
        valid_time_span=_ts(1514, 1620, "ts_app_e28_wqt"),
        attesting_fact_ids=["fact_e28_wanshu_shiwo"],
    ),
    # 泉名层：「温泉」先为泉名——《帝京景物略》以泉立目并系浴池。
    Appellation(
        id="app_e28_wenquan_spring_name",
        label="温泉（泉名）",
        kind=AppellationKind.VULGAR,
        valid_time_span=_ts(1635, 2026, "ts_app_e28_wq_spring"),
        attesting_fact_ids=["fact_e28_dijing_wenquan"],
    ),
]

STATES: List[HistoricalFeatureState] = [
    HistoricalFeatureState(
        id="state_e28_wenquantang_built",
        entity_id="ent_e28_wenquantang",
        label="明 · 正德甲戌：谷太监建堂于堂子山上，因泉得名（1514）",
        time_span=_ts(1514, 1514, "ts_st_e28_wqt"),
        geometry="堂子山上（山下有温泉出露）",
        function="汤沐之堂：泉名成堂名，山因堂得名的枢纽建置",
        evidence_fact_ids=["fact_e28_wanshu_shiwo"],
    ),
    HistoricalFeatureState(
        id="state_e28_spring_ming_recorded",
        entity_id="ent_e28_wenquan_spring",
        label="明 · 万历至崇祯：泉出露见诸官书与笔记（甃池浴疗）",
        time_span=_ts(1593, 1635, "ts_st_e28_spring_ming"),
        geometry="堂子山下（官书「下有溫泉」）；泉已被甃为浴池",
        function="民间汤池，对公众开放；泉浴疗愈口碑（無苦瘍躄）",
        evidence_fact_ids=["fact_e28_wanshu_shiwo", "fact_e28_dijing_wenquan"],
    ),
    HistoricalFeatureState(
        id="state_e28_tangzishan_limestone",
        entity_id="ent_e28_tangzishan",
        label="明 · 堂子山：石灰岩山体，村南，采石持续（1394-1445 题记）",
        time_span=_ts(1394, 1620, "ts_st_e28_tzs"),
        geometry="石灰岩，海拔约九十米，在温泉村南（区保条目口径）",
        function="采石场山体：「石窝」村名得名的实物来源；明称堂子山",
        evidence_fact_ids=["fact_e28_wanshu_shiwo"],
    ),
    HistoricalFeatureState(
        id="state_e28_heilongtan_pray",
        entity_id="ent_e28_heilongtan_longwangmiao",
        label="明清 · 黑龙潭龙王庙：皇家祈雨之所（冷泉）",
        time_span=_ts(1486, 1911, "ts_st_e28_hlt"),
        geometry="金山口北，依岗有龙王庙，廊前为潭",
        function="祈雨祀典（「祈」）；与温泉堂之「浴」分属两泉两庙，不得合并",
        evidence_fact_ids=["fact_e28_dijing_heilongtan"],
    ),
]

TRANSFORMATIONS: List[PlaceTransformation] = []

IDENTITIES: List[DiachronicIdentityAssertion] = [
    # 石窝村 ⟷ 温泉村：同一聚落的两次村名（改名年代无书证，缺口保留）
    DiachronicIdentityAssertion(
        id="dia_e28_village_rename",
        relation=IdentityRelation.SAME_CONTINUANT,
        subject_entity_ids=["top_wenquan"],
        time_span=_ts(1394, 2026, "ts_dia_e28_village"),
        evidence_fact_ids=["fact_e28_wanshu_shiwo"],
        status=EpistemicStatus.VERIFIED,
        is_orthogonal_to_state_change=True,
    ),
    # 堂子山 ⟷ 显龙山：同一山体，山名层累（显龙山得名年代存疑，见存疑 11）
    DiachronicIdentityAssertion(
        id="dia_e28_mountain_rename",
        relation=IdentityRelation.SAME_CONTINUANT,
        subject_entity_ids=["ent_e28_tangzishan"],
        time_span=_ts(1394, 2026, "ts_dia_e28_mountain"),
        evidence_fact_ids=["fact_e28_wanshu_shiwo"],
        status=EpistemicStatus.VERIFIED,
        is_orthogonal_to_state_change=True,
    ),
]

REFERENCES: List[ReferentialAssertion] = [
    # 「温泉」一名多指：泉、堂、村、镇共享音形，所指分层——
    # 命题层已按指称对象拆分，此处不立跨指断言。
]

AGGREGATES: List[PlaceAggregate] = []


# ==================================================================
# 命题层：层累正命题 ＋ 三条证伪 ＋ 三条存疑不入史
# ==================================================================

PROPOSITIONS: List[Proposition] = [
    # —— NC1（正向主命题）：五段接力，改名年代不系年 ——
    Proposition(
        id="prop_e28_name_ladder",
        statement=("温泉的地名身份按「泉→堂→山→村→镇」五段接力生成："
                   "山下温泉先有泉名；正德甲戌（一五一四）谷太监建温泉堂，"
                   "堂承泉名；山因堂得名叫堂子山（通行考释）；"
                   "村名由石窝村渐改温泉村；今为温泉镇。"),
        derived_from_fact_ids=["fact_e28_wanshu_shiwo",
                               "fact_e28_dijing_wenquan"],
        inferred_subject_id="top_wenquan",
        inference_method=(
            "**纵向层累 ＋ 缺口保留**判据：每一段都有独立书证——"
            "泉与堂（宛署杂记「下有溫泉」「建堂於其上，因名」）、"
            "山（「曰堂子山」，得自堂说是通行考释，原文未明言）、"
            "村（万历官书作石窝村，明末帝京景物略已以温泉立目）、"
            "镇（今政区）。🔴 **「村名由石窝改温泉」的具体年代无直接书证**，"
            "两村名时段之间保留缺口（1593-1635 之间），严禁系于某年。"
        ),
        alternative_explanations=[
            "堂子山得名是否因温泉堂属合理推断而非原文明言，本片标存疑",
            "「温泉」作为泉名的起始年代无书证，只可证明末已用",
        ],
    ),
    # —— NC2（证伪）：「自古因泉得名」——万历官书作石窝村 ——
    Proposition(
        id="prop_e28_village_not_ancient_spring_name",
        statement="温泉村自古因泉得名，村名与泉同龄；万历官书已作温泉村。",
        derived_from_fact_ids=[],
        inferred_subject_id="top_wenquan",
        inference_method=(
            "**官书反证**判据：万历《宛署杂记》正式村名是**石窝村**"
            "（采石场村），「温泉」此时只是泉名与堂名。"
            "村名与泉名「同龄」说不成立；「自古如此」被一手官书直接否定。"
            "改名年代无书证，只可写「明末文献已称温泉」。"
        ),
        alternative_explanations=["村名改称或经口语渐变，无行政改称档案传世"],
    ),
    # —— NC3（证伪）：库内伪引《帝京景物略》——原文具在而无此句 ——
    Proposition(
        id="prop_e28_fake_dijing_quote",
        statement=("《帝京景物略》卷五载：「平地温泉如沸，冬月白气滃然，"
                   "辽金帝王驻跸沐浴之所」。"),
        derived_from_fact_ids=[],
        inferred_subject_id="top_wenquan",
        inference_method=(
            "**原文具在式证伪**（肯定性反证，非 absence of evidence）："
            "《帝京景物略》「温泉」条原文经逐字核录（fact_e28_dijing_wenquan），"
            "其中并无此句；「辽金帝王驻跸沐浴」更无任何一手书证。"
            "该伪引文在库内已由 E28 判死（extractor 层 attest_wenquan_dijing "
            "降级 L6_DISPROVEN），本模块不重复录入伪引文本，只引用证伪结论。"
            "本村可证文字史的一手起点是明初采石题记与《宛署杂记》，"
            "辽金层系后人想象叠加。"
        ),
        alternative_explanations=["伪句或为后人概括混入网络文本，源头无刻本依据"],
    ),
    # —— NC4（证伪）：香水院不在温泉后山 ——
    Proposition(
        id="prop_e28_xiangshuiyuan_not_wenquan",
        statement="西山八大水院之香水院即温泉后山（金章宗设院处）。",
        derived_from_fact_ids=[],
        inferred_subject_id="ent_e28_tangzishan",
        inference_method=(
            "**断碑地望**判据：《帝京景物略》明记香水院在**妙高峰法云寺**"
            "（「草際斷碑，『香水院』三字存焉」，fact_e28_dijing_xiangshuiyuan）"
            "——明代人亲眼见过断碑，位置在妙高峰，不在温泉。"
            "诸本对八院（六院）名目与今地对应互异，除清水院＝大觉寺有辽碑"
            "直证外均为后世考释。温泉与金章宗的关联一律标「无据，存疑」。"
        ),
        alternative_explanations=["八院名目诸本互异，除清水院外均为后世考释"],
    ),
    # —— NC5：国保口径（L4 机构口径，编号原名单待复核）——
    Proposition(
        id="prop_e28_guobao_numbering",
        statement=("辛亥滦州起义纪念园为第一批全国重点文物保护单位；"
                   "黑龙潭及龙王庙亦为第一批，可按第一批体例引用编号。"),
        derived_from_fact_ids=[],
        inferred_subject_id="ent_e28_luanzhou_memorial",
        inference_method=(
            "**批次口径分层**判据（L4 机构口径，无古籍逐字书证，故本命题"
            "**不建 TextualFact、不判 DISPROVEN**，只作口径订正陈述）："
            "辛亥滦州起义纪念园＝**第六批**全国重点文物保护单位"
            "（二零零六年五月二十五日公布，编号 **6-886**，近现代重要史迹及"
            "代表性建筑类）；黑龙潭及龙王庙＝**大运河**国保子项"
            "（二零零六年列第六批 **6-810**，二零一三年并入第七批「大运河」"
            "**7-1973-3-009**），另为一九八四年第三批北京市文物保护单位。"
            "两处均非一九六一年第一批；一九六一年首批国保本无「X-YYY」式"
            "编号体系（该体系自一九八二年第二批起施行），"
            "「第一批可引编号」的表述本身即误。"
            "🔴 编号与批次据北京市文物局公开词条与名录口径，"
            "**须与国务院公布名单原件复核**（研究档案存疑 17）。"
        ),
        alternative_explanations=[
            "本集无 1961 第一批单位；第六批（2006）编号体系全程可用",
            "黑龙潭 6-810 与滦州纪念园 6-886 同为第六批公布，"
            "前者 2013 年并入大运河第七批，批次表述须带两条线",
        ],
    ),
    # —— NC6（双禁）：泉眼今日存续状态未考得 ——
    Proposition(
        id="prop_e28_spring_status_unknown",
        statement="天然温泉眼至今仍在涌流（或：早已干涸）。",
        derived_from_fact_ids=[],
        inferred_subject_id="ent_e28_wenquan_spring",
        inference_method=(
            "**双禁**判据（absence of evidence ≠ evidence of absence）："
            "天然温泉眼的今日存续状态**未考得**——无公开水文记载可证"
            "「仍在涌流」，亦无可证「早已干涸」。已证旁例仅限黑龙潭"
            "（二十一世纪初因超采地下水，水深不盈尺，L4），且黑龙潭与温泉"
            "是两眼泉、数里相隔，状态不得互推。故两说均 UNSUBSTANTIATED，"
            "片中只说「泉眼已不见于公开水文记载」，不落断言。"
        ),
        alternative_explanations=["黑龙潭「水深不盈尺」为已证旁例，不外推至温泉"],
    ),
    # —— NC7（不入史）：慈禧题字 ——
    Proposition(
        id="prop_e28_cixi_inscription",
        statement="「温泉」二字为慈禧太后御笔题写。",
        derived_from_fact_ids=[],
        inferred_subject_id="top_wenquan",
        inference_method=(
            "**无据不入史**判据：检索未考得任何文献与实物依据，"
            "亦无题刻存世记录；京西温泉御笔传说多系与昌平小汤山"
            "（乾隆「九华分秀」等）混淆。不入片，仅存疑清单留档（存疑 14）。"
        ),
        alternative_explanations=["御笔传说或与昌平小汤山乾隆题刻混淆"],
    ),
    # —— NC8（存疑不采）：故宫石料说 ——
    Proposition(
        id="prop_e28_gugong_shiliao",
        statement="石窝村是明代皇宫（故宫）石料产地，供汉白玉。",
        derived_from_fact_ids=[],
        inferred_subject_id="ent_e28_tangzishan",
        inference_method=(
            "**存疑不采**判据：当地采石有一手题记实证"
            "（明洪武二十七年、正统十年，区保条目口径），"
            "但「供故宫石料」仅见当代通俗文章，无档案依据；"
            "明代皇家石料主产地是**房山大石窝**（同名异地，以汉白玉闻名）——"
            "本村石窝见《宛署杂记》「離城五十里」＋堂子山＋山下温泉三重定位，"
            "两地严禁混写。本片只说「京西采石场村」，不外推石料用途。"
        ),
        alternative_explanations=["采石规模与用途无档案传世，用途推断均属外推"],
    ),
]

ADOPTIONS: List[BeliefAdoption] = [
    BeliefAdoption(
        proposition_id="prop_e28_name_ladder",
        status=EpistemicStatus.VERIFIED,
        confidence=0.92,
        adopted_by="E28 正向主判据（五段接力，逐段书证）",
        adopted_at=_dt(2026, "dt_ad_e28_nc1"),
        rationale=(
            "泉与堂（《宛署杂记》「下有溫泉」「正德甲戌谷太監建堂於其上，因名」）、"
            "山（「曰堂子山」，得自堂说标存疑）、村（万历官书作石窝村，"
            "明末帝京景物略已以温泉立目）、镇（今政区）逐段有据。"
            "改名具体年代无书证，村名时段保留缺口，不系年。"
        ),
        refuting_fact_ids=[],
    ),
    BeliefAdoption(
        proposition_id="prop_e28_village_not_ancient_spring_name",
        status=EpistemicStatus.DISPROVEN,
        confidence=0.95,
        adopted_by="E28 负控制 V-NC01（官书反证：万历正式村名是石窝村）",
        adopted_at=_dt(2026, "dt_ad_e28_nc2"),
        rationale=(
            "《宛署杂记》「溫泉堂，在石窩村」为万历官书的正式村名记录，"
            "直接否定「村名与泉同龄」「自古因泉得名」；"
            "改名年代无书证，只可写「明末文献已称温泉」。"
        ),
        refuting_fact_ids=["fact_e28_wanshu_shiwo"],
    ),
    BeliefAdoption(
        proposition_id="prop_e28_fake_dijing_quote",
        status=EpistemicStatus.DISPROVEN,
        confidence=0.97,
        adopted_by="E28 负控制 V-NC03（原文具在式证伪）",
        adopted_at=_dt(2026, "dt_ad_e28_nc3"),
        rationale=(
            "《帝京景物略》「温泉」条原文逐字核录在案"
            "（fact_e28_dijing_wenquan），其中无「平地温泉如沸……"
            "辽金帝王驻跸沐浴之所」句——原文具在而无此句属**肯定性反证**，"
            "非 absence of evidence，故 DISPROVEN 成立。"
            "「辽金帝王驻跸沐浴」另无任何一手书证。"
            "库内条目已由 extractor 层降级 L6_DISPROVEN，本模块不重复建模。"
        ),
        refuting_fact_ids=["fact_e28_dijing_wenquan"],
    ),
    BeliefAdoption(
        proposition_id="prop_e28_xiangshuiyuan_not_wenquan",
        status=EpistemicStatus.DISPROVEN,
        confidence=0.95,
        adopted_by="E28 负控制 V-NC04（香水院断碑地望）",
        adopted_at=_dt(2026, "dt_ad_e28_nc4"),
        rationale=(
            "《帝京景物略》明记香水院断碑在**妙高峰法云寺**"
            "（fact_e28_dijing_xiangshuiyuan），不在温泉后山；"
            "「香水院＝温泉后山」系本库 era4 旧对应，判 DISPROVEN。"
            "八院（六院）与今地对应除清水院＝大觉寺外均为后世考释。"
        ),
        refuting_fact_ids=["fact_e28_dijing_xiangshuiyuan"],
    ),
    BeliefAdoption(
        proposition_id="prop_e28_guobao_numbering",
        # 批次误置为「第一批」与官方机构口径冲突，但口径证据是 L4 机构词条、
        # 无本地逐字名单行——按纪律不判 DISPROVEN（否则须挂不存在的书证），
        # 以 UNSUBSTANTIATED 表达「该说法在可核书证层无据」，同时命题层
        # 已给出正确口径与待核状态（存疑 17）。
        status=EpistemicStatus.UNSUBSTANTIATED,
        confidence=0.85,
        adopted_by="E28 负控制 V-NC05（批次与编号精确；L4 口径待原件复核）",
        adopted_at=_dt(2026, "dt_ad_e28_nc5"),
        rationale=(
            "正确口径：纪念园＝第六批（2006-05-25，6-886）；"
            "黑龙潭及龙王庙＝大运河子项（6-810→7-1973-3-009），"
            "另 1984 年第三批北京市文保；两处均非 1961 第一批，"
            "而第一批本无「X-YYY」编号体系。因名单原件逐字行未落盘，"
            "不建 TextualFact、不判 DISPROVEN；编号须与国务院公布名单"
            "原件复核（存疑 17）。"
        ),
    ),
    BeliefAdoption(
        proposition_id="prop_e28_spring_status_unknown",
        # 泉眼存续状态未考得：涌流/干涸两说均无据。
        # 无据用 UNSUBSTANTIATED——absence of evidence ≠ evidence of absence。
        status=EpistemicStatus.UNSUBSTANTIATED,
        confidence=0.9,
        adopted_by="E28 负控制 V-NC06（泉眼现状双禁）",
        adopted_at=_dt(2026, "dt_ad_e28_nc6"),
        rationale=(
            "天然温泉眼今日存续状态未考得：无公开水文记载可证仍在涌流，"
            "亦无可证早已干涸。已证旁例仅黑龙潭（二十一世纪初超采地下水，"
            "水深不盈尺，L4），两泉数里相隔不得互推。片中只说"
            "「泉眼已不见于公开水文记载」，不落断言。"
        ),
    ),
    BeliefAdoption(
        proposition_id="prop_e28_cixi_inscription",
        status=EpistemicStatus.UNSUBSTANTIATED,
        confidence=0.9,
        adopted_by="E28 负控制（慈禧题字无据不入史）",
        adopted_at=_dt(2026, "dt_ad_e28_nc7"),
        rationale=(
            "未考得任何文献与实物依据，亦无题刻存世记录；"
            "御笔传说多系与昌平小汤山混淆。不入片，存疑清单留档（存疑 14）。"
        ),
    ),
    BeliefAdoption(
        proposition_id="prop_e28_gugong_shiliao",
        status=EpistemicStatus.UNSUBSTANTIATED,
        confidence=0.85,
        adopted_by="E28 负控制 V-NC02（故宫石料说存疑不采）",
        adopted_at=_dt(2026, "dt_ad_e28_nc8"),
        rationale=(
            "采石本身有明初题记实证，但「供故宫石料」仅见当代通俗文章，"
            "无档案依据；明代皇家石料主产地是房山大石窝（同名异地）。"
            "本片只说「京西采石场村」，不外推石料用途。"
        ),
    ),
]
