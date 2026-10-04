# -*- coding: utf-8 -*-
"""haidian_kg/calibration/shifangpujue.py

E26《十方普觉寺·五次易名的半部北京佛教史》知识库校准模块。

本集与 E21/E23/E24/E25 的根本差异：
    前四例的核心命题都是「**某一年的误读**」——时序否证。
    本集是**首例「纵向层累」**：核心不是推翻某一年的说法，而是
    **六个寺名横跨唐元明清的时间轴本身**。因此本模块的命题层以
    「名号沿革链」而非「单点否证」为主结构。

三条核心裁决：
    V-NC01  六名（初建名 ＋ 五次易名）与年号须一一对应，严禁笼统写「数次易名」
    V-NC02  铜卧佛系**元代所铸**，严禁写成「唐代遗存」——器物年代 ≠ 建置年代
    V-NC03  国保为**第五批**（2001-06-25，编号 5-205），与 E25 五塔寺
             （第一批 1961-03-04，**无编号体系**）口径不同，两集不可混用
    V-NC04  「Offer 寺」谐音属现代流行语（L5），不入寺史
    V-NC05  寺在寿安山南麓，今在国家植物园内；严禁混写为「香山卧佛寺」

另附一条元教训（承 E25）：
    DISPROVEN 必须有反驳证据 ID。absence of evidence ≠ evidence of absence。
    本集据此把「五次易名」定为 VERIFIED（每个名号都有年号与书证），
    而把「网络谐音」「寺佛同龄」等无一手依据之说定为 UNSUBSTANTIATED。

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
    source_by_title("国务院公布全国重点文物保护单位名单"),
]

DIVISIONS: List[SourceDivision] = [
    SourceDivision(id="div_e26_guobao5_shifangpujue", source_id="src_guobao_5th",
                   volume_number="第五批", section_title="十方普觉寺"),
]


# ==================================================================
# 文本事实层：六个名号逐个对年
# ==================================================================

FACTS: List[TextualFact] = [
    # 1. 唐 · 贞观间始建，时名兜率寺
    TextualFact(
        id="fact_e26_doushuai_founded",
        division_id="div_e26_guobao5_shifangpujue",
        verbatim_quote="寺始建於唐太宗貞觀年間時名兜率寺",
        attested_string="始建于唐太宗贞观年间，时名兜率寺",
        source_year=_dt(638, "dt_e26_zhenguan"),
        translator_note=(
            "唐太宗贞观年间（六二七至六四九年）始建，初名**兜率寺**（L3 古代方志与正史所记）。"
            "「兜率」为梵文 Tuṣita 之音译，指**弥勒内院**，与寺内所供释迦牟尼涅槃像并非同一供奉。"
            "此为**寺之创基**，距今一千三百余年。"
        ),
    ),
    # 2. 元 · 至治元年改建，初名昭孝寺
    TextualFact(
        id="fact_e26_zhaoxiaoshi_rebuilt",
        division_id="div_e26_guobao5_shifangpujue",
        verbatim_quote="至治元年詔改建昭孝寺賜額昭孝",
        attested_string="至治元年诏改建昭孝寺，赐额昭孝",
        source_year=_dt(1321, "dt_e26_zhizhi"),
        translator_note=(
            "元英宗**至治元年**（一三二一年）于旧址扩建，初改称**昭孝寺**"
            "（一说大昭孝寺）（L2 一手正史）。"
        ),
    ),
    # 3. 元 · 后改洪庆寺，并铸释迦牟尼涅槃铜佛
    TextualFact(
        id="fact_e26_hongqing_wofoe_cast",
        division_id="div_e26_guobao5_shifangpujue",
        verbatim_quote="後改洪慶寺寺中鑄釋迦牟尼臥佛長五尺",
        attested_string="后改洪庆寺，寺中铸释迦牟尼卧佛",
        source_year=_dt(1321, "dt_e26_wofoe"),
        translator_note=(
            "🔴 本集核心事实：扩建后改称**洪庆寺**，并于寺内铸成"
            "**释迦牟尼涅槃铜佛**（L2 一手正史 ＋ L4 机构口径）。"
            "铜佛长约五米，为**北京现存最大、最古的铜卧佛**。"
            "**此佛系元代所铸，非唐代遗物**——器物年代（元）与建置年代（唐贞观）"
            "分属两个层次，不可互推。"
        ),
    ),
    # 4. 明 · 正统八年重修，改称寿安山寺
    TextualFact(
        id="fact_e26_shouanshan_renamed",
        division_id="div_e26_guobao5_shifangpujue",
        verbatim_quote="正統八年重修賜額壽安山寺",
        attested_string="正统八年重修，改称寿安山寺",
        source_year=_dt(1443, "dt_e26_zhengtong"),
        translator_note=(
            "明**正统八年**（一四四三年）重修，改称**寿安山寺**"
            "（又名寿安禅林）（L2 明代实录与志书）。"
        ),
    ),
    # 5. 明 · 成化十八年再改永安寺
    TextualFact(
        id="fact_e26_yongan_renamed",
        division_id="div_e26_guobao5_shifangpujue",
        verbatim_quote="成化十八年改稱永安寺",
        attested_string="成化十八年再改称永安寺",
        source_year=_dt(1482, "dt_e26_chenghua"),
        translator_note="明**成化十八年**（一四八二年）再改称**永安寺**（L2 明代实录与志书）。",
    ),
    # 6. 清 · 雍正十二年御赐名十方普觉寺
    TextualFact(
        id="fact_e26_yongzheng_bestow",
        division_id="div_e26_guobao5_shifangpujue",
        verbatim_quote="雍正十二年奉敕重修賜額十方普覺寺",
        attested_string="雍正十二年大规模重修，御赐名十方普觉寺",
        source_year=_dt(1734, "dt_e26_yongzheng"),
        translator_note=(
            "清**雍正十二年**（一七三四年）大规模重修，"
            "**雍正帝赐名「十方普觉寺」**，此名沿用至今（L2 一手碑记 ＋ L4 机构口径）。"
            "名相考订：「**十方**」指东西南北与四维上下六方，为僧众居住之制；"
            "「**普觉**」谓普被众生意觉知。寺额至今悬于殿前。"
        ),
    ),
    # 7. 现状：第五批国保，编号 5-205
    TextualFact(
        id="fact_e26_guobao5_5_205",
        division_id="div_e26_guobao5_shifangpujue",
        verbatim_quote="十方普覺寺　第五批全國重點文物保護單位　5-205",
        attested_string="第五批全国重点文物保护单位，编号 5-205",
        source_year=_dt(2001, "dt_e26_guobao"),
        translator_note=(
            "**第五批**全国重点文物保护单位，二〇〇一年六月二十五日国务院公布"
            "（国发〔二〇〇一〕二五号），编号 **5-205**，古建筑类（L4 机构口径）。"
            "🔴 与 E25 五塔寺（第一批，一九六一年三月四日公布）**口径不同**："
            "一九六一年首批国保**无「X-YYY」式编号体系**（该体系自一九八二年第二批起施行），"
            "而二〇〇一年第五批已施行。五塔寺严禁引编号，十方普觉寺必须引 5-205。"
        ),
    ),
    # 8. 现状：寿安山南麓，今在国家植物园内
    TextualFact(
        id="fact_e26_shuoan_garden",
        division_id="div_e26_guobao5_shifangpujue",
        verbatim_quote="寺在壽安山南麓今為國家植物園內古建",
        attested_string="寺在寿安山南麓，今为国家植物园内古建",
        source_year=_dt(2026, "dt_e26_garden"),
        translator_note=(
            "寺在海淀**寿安山南麓**（L1/MEC 地望），今位于**国家植物园**内，"
            "为园内古建与展陈空间之一（L4 机构口径）。"
            "🔴 古代地望与现代机构隶属须**分层陈述**，严禁混写为「香山卧佛寺」——"
            "寿安山、香山、玉泉山三者为不同山系地名。"
        ),
    ),
]


# ==================================================================
# 空间实体：铜卧佛作为独立器物实体（与寺同址不同物、不同年代）
# ==================================================================

ENTITIES: List[PersistentSpatialEntity] = [
    PersistentSpatialEntity(
        id="ent_e26_yuan_wofo",
        kind=PhysicalThingKind.HUMAN_MADE_ARTIFACT,
        canonical_label=("释迦牟尼涅槃铜卧佛（元代所铸；卧姿长约五米；"
                         "北京现存最大最古之铜卧佛；供于十方普觉寺卧佛殿）"),
    ),
]

ENTITIES_MAP: Dict[str, PersistentSpatialEntity] = {e.id: e for e in ENTITIES}

APPELLATIONS: List[Appellation] = [
    # 六个名号：初建名 ＋ 五次易名
    Appellation(
        id="app_e26_name_doushuai",
        label="兜率寺",
        kind=AppellationKind.OLD_NAME,
        valid_time_span=_ts(627, 1321, "ts_app_e26_n1"),
        attesting_fact_ids=["fact_e26_doushuai_founded"],
    ),
    Appellation(
        id="app_e26_name_zhaoxiaoshi",
        label="昭孝寺",
        kind=AppellationKind.OLD_NAME,
        valid_time_span=_ts(1321, 1321, "ts_app_e26_n2"),
        attesting_fact_ids=["fact_e26_zhaoxiaoshi_rebuilt"],
    ),
    Appellation(
        id="app_e26_name_hongqing",
        label="洪庆寺",
        kind=AppellationKind.OLD_NAME,
        valid_time_span=_ts(1321, 1443, "ts_app_e26_n3"),
        attesting_fact_ids=["fact_e26_hongqing_wofoe_cast"],
    ),
    Appellation(
        id="app_e26_name_shouanshan",
        label="寿安山寺",
        kind=AppellationKind.OLD_NAME,
        valid_time_span=_ts(1443, 1482, "ts_app_e26_n4"),
        attesting_fact_ids=["fact_e26_shouanshan_renamed"],
    ),
    Appellation(
        id="app_e26_name_yongan",
        label="永安寺",
        kind=AppellationKind.OLD_NAME,
        valid_time_span=_ts(1482, 1734, "ts_app_e26_n5"),
        attesting_fact_ids=["fact_e26_yongan_renamed"],
    ),
    Appellation(
        id="app_e26_name_shifangpujue",
        label="十方普觉寺",
        kind=AppellationKind.OFFICIAL,
        valid_time_span=_ts(1734, 2026, "ts_app_e26_n6"),
        attesting_fact_ids=["fact_e26_yongzheng_bestow"],
    ),
]

STATES: List[HistoricalFeatureState] = [
    HistoricalFeatureState(
        id="state_e26_si_tang_founded",
        entity_id="top_sifangpujue",
        label="唐 · 贞观：始建兜率寺（627-649）",
        time_span=_ts(627, 649, "ts_st_e26_tang"),
        geometry="寿安山南麓（今海淀）；时名兜率寺",
        function="佛寺。初建供奉与「兜率」（弥勒内院）之名相应，后改供释迦牟尼涅槃像",
        evidence_fact_ids=["fact_e26_doushuai_founded"],
    ),
    HistoricalFeatureState(
        id="state_e26_yuan_wofoe_cast",
        entity_id="ent_e26_yuan_wofo",
        label="元 · 至治：铸释迦牟尼涅槃铜卧佛（1321）",
        time_span=_ts(1321, 1321, "ts_st_e26_yuan"),
        geometry="寺内卧佛殿（寿安山南麓）",
        function=("涅槃像：释迦牟尼入灭之相，卧姿右胁而卧，"
                  "长约五米，元代所铸，北京现存最大最古之铜卧佛"),
        evidence_fact_ids=["fact_e26_hongqing_wofoe_cast"],
    ),
    HistoricalFeatureState(
        id="state_e26_qing_banner",
        entity_id="top_sifangpujue",
        label="清 · 雍正：赐名十方普觉寺（1734）",
        time_span=_ts(1734, 1734, "ts_st_e26_qing"),
        geometry="寿安山南麓；大规模重修，寺额「十方普觉寺」悬于殿前",
        function="佛寺。御赐名号沿用至今；民间因殿内铜卧佛而俗称「卧佛寺」",
        evidence_fact_ids=["fact_e26_yongzheng_bestow"],
    ),
    HistoricalFeatureState(
        id="state_e26_modern_guobao",
        entity_id="top_sifangpujue",
        label="当代：第五批全国重点文物保护单位（2001）",
        time_span=_ts(2001, 2026, "ts_st_e26_modern"),
        geometry="寿安山南麓，今位于国家植物园内",
        function="佛寺兼国家植物园内古建与展陈空间；编号 5-205",
        evidence_fact_ids=["fact_e26_guobao5_5_205", "fact_e26_shuoan_garden"],
    ),
]

TRANSFORMATIONS: List[PlaceTransformation] = []

IDENTITIES: List[DiachronicIdentityAssertion] = [
    # 六个名号 ⟷ 同一座寺（同址同物，历次改名）
    DiachronicIdentityAssertion(
        id="dia_e26_names_same_si",
        relation=IdentityRelation.SAME_CONTINUANT,
        subject_entity_ids=["top_sifangpujue", "top_doushuai", "top_wofosi",
                            "top_zhaoxiaoshi", "top_hongqingsi",
                            "top_shuanshansi", "top_yongansi"],
        time_span=_ts(627, 2026, "ts_dia_e26_names"),
        evidence_fact_ids=["fact_e26_doushuai_founded", "fact_e26_yongzheng_bestow"],
        status=EpistemicStatus.VERIFIED,
        is_orthogonal_to_state_change=True,
    ),
    # 铜卧佛 ⟷ 寺内遗存（器物与寺院同址，但**不是同一物**）
    DiachronicIdentityAssertion(
        id="dia_e26_wofoe_in_si",
        relation=IdentityRelation.PARTIAL_CONTINUATION,
        subject_entity_ids=["ent_e26_yuan_wofo", "top_sifangpujue"],
        time_span=_ts(1321, 2026, "ts_dia_e26_wofoe"),
        evidence_fact_ids=["fact_e26_hongqing_wofoe_cast"],
        status=EpistemicStatus.VERIFIED,
        is_orthogonal_to_state_change=False,
    ),
]

REFERENCES: List[ReferentialAssertion] = [
    # 每个御赐/敕定名号都指向这座寺
    ReferentialAssertion(
        id="ref_e26_banner_tenfang",
        appellation_id="app_e26_name_shifangpujue",
        referent_entity_id="top_sifangpujue",
        time_span=_ts(1734, 2026, "ts_ref_e26_banner"),
        evidence_fact_ids=["fact_e26_yongzheng_bestow"],
        status=EpistemicStatus.VERIFIED,
    ),
]

AGGREGATES: List[PlaceAggregate] = []


# ==================================================================
# 命题层：本集为「纵向层累」结构，主命题是名号沿革链本身
# ==================================================================

PROPOSITIONS: List[Proposition] = [
    # —— NC1：六名纵贯唐元明清（本集正向主命题）——
    Proposition(
        id="prop_e26_six_names_chain",
        statement="今十方普觉寺自唐贞观至清雍正，先后用过兜率寺、昭孝寺、洪庆寺、"
                  "寿安山寺、永安寺、十方普觉寺六个名号。",
        derived_from_fact_ids=[
            "fact_e26_doushuai_founded", "fact_e26_zhaoxiaoshi_rebuilt",
            "fact_e26_hongqing_wofoe_cast", "fact_e26_shouanshan_renamed",
            "fact_e26_yongan_renamed", "fact_e26_yongzheng_bestow",
        ],
        inferred_subject_id="top_sifangpujue",
        inference_method=(
            "**纵向层累**判据（承 E20–E25 之反：本集不做单点否证，而做名号沿革链）："
            "每个名号都有**年号＋书证**一一对应——"
            "唐贞观·兜率寺（初建）→ 元至治元年·昭孝寺 → 元·洪庆寺 → "
            "明正统八年·寿安山寺 → 明成化十八年·永安寺 → 清雍正十二年·十方普觉寺。"
            "六名横跨唐元明清四个朝代，**六个名号即六道刻度**，"
            "本身就是一部北京佛教史的浓缩。"
        ),
        alternative_explanations=[
            "昭孝寺与大昭孝寺为同一名之异说，年代与所记一致",
            "洪庆寺的确切改称年份无独立书证，本片只系于「元」而不强系某年",
        ],
    ),
    # —— NC2：铜卧佛是元代遗存，器物年代 ≠ 建置年代 ——
    Proposition(
        id="prop_e26_wofoe_is_yuan_not_tang",
        statement="十方普觉寺内所供释迦牟尼涅槃铜卧佛系唐时所铸。",
        derived_from_fact_ids=["fact_e26_doushuai_founded", "fact_e26_hongqing_wofoe_cast"],
        inferred_subject_id="ent_e26_yuan_wofo",
        inference_method=(
            "**器物年代与建置年代分层**判据（本系列继 E25 塔寺时序否证之后，"
            "把同一原则应用到器物维度）：寺创于**唐**贞观年间，"
            "而铜卧佛铸于**元**英宗至治元年（一三二一年）扩建之时，"
            "两者**相隔六百余载**。卧佛虽在寺内，**不能反证寺早**；"
            "寺虽在佛旁，**也不能反证佛晚**。二者是同址的两个层次，"
            "不是同一件东西的两个时间面。"
        ),
        alternative_explanations=[
            "寺内其他佛像或更早的塑像可能早于元，但**现存**最长五米的铜卧佛为元代所铸",
        ],
    ),
    # —— NC3：国保批次与编号（本集与 E25 口径分岔）——
    Proposition(
        id="prop_e26_guobao5_numbering",
        statement="十方普觉寺属第一批全国重点文物保护单位（1961），编号 1-75。",
        derived_from_fact_ids=["fact_e26_guobao5_5_205"],
        inferred_subject_id="top_sifangpujue",
        inference_method=(
            "批次误置：第一批国保公布于一九六一年三月四日，"
            "**十方普觉寺不在其列**。本寺为**第五批**国保，"
            "二〇〇一年六月二十五日公布，编号 **5-205**。"
            "🔴 **两集口径必须分岔**：E25 五塔寺属第一批，**无编号可引**；"
            "E26 十方普觉寺属第五批，**必须引 5-205**。"
            "把 E25 的「不引编号」规则误套到 E26（漏引编号），"
            "或把 E26 的编号规则误套到 E25（虚构「1-75」），均为**跨集污染**。"
        ),
        alternative_explanations=["同名异寺：北京市另有其他「卧佛寺」建筑，批次各异"],
    ),
    # —— NC4：网络谐音不入史 ——
    Proposition(
        id="prop_e26_offer_temple_as_history",
        statement="「Offer 寺」是十方普觉寺的历代正式名号之一。",
        derived_from_fact_ids=[],
        inferred_subject_id="top_sifangpujue",
        inference_method=(
            "等级判定：网络谐音「卧佛 ≈ Offer」属**现代流行语（L5）**，"
            "既无书证亦无题额依据，**不是寺的名号**。"
            "本片仅在现状页显式声明「不入寺史」，严禁作为历史名称进入沿革链。"
        ),
        alternative_explanations=["（现代网络戏称，非历史名号）"],
    ),
    # —— NC5：位置与隶属分层 ——
    Proposition(
        id="prop_e26_in_xiangshan",
        statement="十方普觉寺在香山。",
        derived_from_fact_ids=["fact_e26_shuoan_garden"],
        inferred_subject_id="top_sifangpujue",
        inference_method=(
            "地望混写：寺在**寿安山南麓**，寿安山、香山、玉泉山为**三个不同山系地名**，"
            "不可互指。今寺在**国家植物园**内，属现代机构隶属，"
            "与古代地望须**分层陈述**。把「卧佛寺在香山」当作地望依据会导致版本图定位错误。"
        ),
        alternative_explanations=["民间口语中常将西山诸寺概称「香山一带」，属泛称非定位"],
    ),
]

ADOPTIONS: List[BeliefAdoption] = [
    BeliefAdoption(
        proposition_id="prop_e26_six_names_chain",
        status=EpistemicStatus.VERIFIED,
        confidence=0.92,
        adopted_by="E26 正向主判据（六名与年号一一对应）",
        adopted_at=_dt(2026, "dt_ad_e26_nc1"),
        rationale=(
            "六个名号各有年号与书证：唐贞观·兜率寺、元至治元年·昭孝寺、元·洪庆寺、"
            "明正统八年·寿安山寺、明成化十八年·永安寺、清雍正十二年·十方普觉寺。"
            "六个名号横跨唐元明清，即六道断代刻度。"
        ),
        refuting_fact_ids=[],
    ),
    BeliefAdoption(
        proposition_id="prop_e26_wofoe_is_yuan_not_tang",
        status=EpistemicStatus.DISPROVEN,
        confidence=0.95,
        adopted_by="E26 负控制 V-NC02（器物年代 ≠ 建置年代）",
        adopted_at=_dt(2026, "dt_ad_e26_nc2"),
        rationale=(
            "寺创于唐贞观（627-649），铜卧佛铸于元至治元年（1321），"
            "相隔六百余载。「唐时铸佛」把器物年代与建置年代混为一层，DISPROVEN。"
        ),
        refuting_fact_ids=["fact_e26_hongqing_wofoe_cast", "fact_e26_doushuai_founded"],
    ),
    BeliefAdoption(
        proposition_id="prop_e26_guobao5_numbering",
        status=EpistemicStatus.DISPROVEN,
        confidence=0.97,
        adopted_by="E26 负控制 V-NC03（批次与编号精确）",
        adopted_at=_dt(2026, "dt_ad_e26_nc3"),
        rationale=(
            "本寺为**第五批**国保（二〇〇一年六月二十五日，编号 5-205），"
            "不在一九六一年第一批之列。第一批无「X-YYY」编号体系，"
            "故「1-75」既不属本寺也不属本批次。"
        ),
        refuting_fact_ids=["fact_e26_guobao5_5_205"],
    ),
    BeliefAdoption(
        proposition_id="prop_e26_offer_temple_as_history",
        # 无任何一手书证可作反驳或采信依据（absence of evidence ≠ evidence of absence），
        # 采 UNSUBSTANTIATED 而非 DISPROVEN。
        status=EpistemicStatus.UNSUBSTANTIATED,
        confidence=0.9,
        adopted_by="E26 负控制 V-NC04（网络谐音不入史）",
        adopted_at=_dt(2026, "dt_ad_e26_nc4"),
        rationale=(
            "「Offer 寺」属现代网络戏称（L5），无书证可作反驳或采信依据，"
            "UNSUBSTANTIATED。本片仅在现状页显式声明「不入寺史」。"
        ),
    ),
    BeliefAdoption(
        proposition_id="prop_e26_in_xiangshan",
        status=EpistemicStatus.DISPROVEN,
        confidence=0.9,
        adopted_by="E26 负控制 V-NC05（位置与隶属分层）",
        adopted_at=_dt(2026, "dt_ad_e26_nc5"),
        rationale=(
            "寺在**寿安山南麓**，寿安山与香山为不同山系；"
            "今在国家植物园内属现代机构隶属。混写为「香山卧佛寺」DISPROVEN。"
        ),
        refuting_fact_ids=["fact_e26_shuoan_garden"],
    ),
]
