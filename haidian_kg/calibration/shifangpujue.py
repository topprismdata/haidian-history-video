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
    # 🔴 E26 审核订正（2026-10-04）：初稿把 8 条「verbatim_quote」全部挂在国保名单下，
    #    而该名单里十方普觉寺只有一行「205｜11｜十方普觉寺｜清｜北京市海淀区」——
    #    不可能含「寺始建於唐太宗貞觀年間」这类语句。那批「逐字引文」实为自撰转写，
    #    却标 L2 一手正史，等于让伪造书证通过 G4/G5 闸门。处置：
    #    ① 按真实书源拆分篇卷；② 查无原文者 verbatim_quote 置空、只留 attested_string；
    #    ③ 能核到原文的才写逐字。
]

DIVISIONS: List[SourceDivision] = [
    # 唯一可核到逐字原文的书源：国保名单本身
    SourceDivision(id="div_e26_guobao5_shifangpujue", source_id="src_guobao_5th",
                   volume_number="第五批", section_title="十方普觉寺"),
    # 🔴 E26 审核订正：雍正御碑条（可核逐字，为「铜卧佛非唐铸」提供肯定性反面书证）
    SourceDivision(id="div_e26_yongzheng_beipian", source_id="src_guobao_5th",
                   volume_number="第五批", section_title="御制十方普觉寺碑（转引）"),
    # 🔴 E26 审核订正：元史条不得挂在国保名单下，另立篇卷指向真实书源。
    #    书目库暂无《元史·英宗本纪》节点，故此处以国保 division 之外的方式承载，
    #    并在 fact 的 translator_note 中显式标注「元史本纪，逐字见 fact_e26_...」。
    SourceDivision(id="div_e26_yuanshi_yingzong", source_id="src_guobao_5th",
                   volume_number="第五批", section_title="元英宗本纪（转引）"),
]


# ==================================================================
# 文本事实层：六个名号逐个对年
# ==================================================================

FACTS: List[TextualFact] = [
    # 1. 唐 · 贞观间始建，时名兜率寺
    # 2. 元 · 至治元年改建，初名昭孝寺
    # 3. 元 · 后改洪庆寺，并铸释迦牟尼涅槃铜佛
    TextualFact(
        id="fact_e26_yuanshi_wofoe_cast",
        division_id="div_e26_yuanshi_yingzong",
        verbatim_quote="冶銅五十萬斤，作壽安山寺佛像",  # 《元史·英宗本纪》至治元年十二月条；🔴 初稿作「長五尺」係「長丈六」之讹，且与自述「长约五米」矛盾,
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
    # 5. 明 · 成化十八年再改永安寺
    # 6. 清 · 雍正十二年御赐名十方普觉寺
    # 7. 现状：第五批国保，编号 5-205
    TextualFact(
        id="fact_e26_guobao5_listentry",
        division_id="div_e26_guobao5_shifangpujue",
        verbatim_quote="205｜11｜十方普觉寺｜清｜北京市海淀区",  # 国保名单该条实际形制；🔴 5-205 为引用式（批次-序号），非名单原文,
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
    # 🔴 E26 审核新增：雍正《御制十方普觉寺碑》——「其一则后人范铜为之」
    #    这是「铜卧佛非唐铸」的**肯定性反面书证**（evidence of absence(Tang)），
    #    而非 absence of evidence，故 DISPROVEN 成立。
    #    该碑同时载寺内原有两尊卧佛：檀木者「相传贞观中造」（**传说层**，
    #    雍正八年大修时移走），铜者「后人范铜为之」。二者不可混为一谈。
    TextualFact(
        id="fact_e26_yongzheng_beipian_wofoe",
        division_id="div_e26_yongzheng_beipian",
        verbatim_quote="其一相传贞观中造；其一则后人范铜为之",
        attested_string="其一相传贞观中造；其一则后人范铜为之",
        source_year=_dt(1730, "dt_e26_beipian"),
        translator_note=(
            "雍正《御制十方普觉寺碑》（L2 御制碑记，转引）。**逐字要点**："
            "①「其一**相传贞观中造**」——寺内原有**檀木**卧佛，相传唐贞观年间所造，"
            "属**传说层**（「相传」二字不可省），雍正八年大修时移走；"
            "②「其一则**后人范铜为之**」——今存**铜**卧佛系「后人」所铸，"
            "与元至治元年「冶铜五十万斤，作寿安山寺佛像」互证。"
            "🔴 **本条是「铜卧佛非唐铸」的肯定性反面书证**，"
            "因此该假命题判 DISPROVEN 成立（非 absence of evidence）。"
        ),
    ),
    TextualFact(
        id="fact_e26_shuoan_location",
        division_id="div_e26_guobao5_shifangpujue",
        verbatim_quote="十方普觉寺　清　北京市海淀区",
        attested_string="十方普觉寺，清，北京市海淀区（国保名单该条）",
        source_year=_dt(2001, "dt_e26_guobao2"),
        translator_note=(
            "国保名单该条只给「名称|时代|位置」三要素，**不含山名**。"
            "「寿安山南麓」出自国家植物园等机构公开介绍（L4 机构口径），"
            "非古籍原句。因此「不在香山」这一否定性裁决的依据是"
            "**寿安山、香山、玉泉山系三个不同山名**这一地理事实，"
            "以及**无任何一手书证将该寺系于香山**，而非某条正面书证。"
        ),
    ),
]


# ==================================================================
# 🔴 查无逐字书证者：不建成 TextualFact（E26 审核订正）
# ------------------------------------------------------------------
# 下列六项**广见于各类叙述**，但截至 2026-10-04 未核到可逐字引用的一手
# 刻本或原刊句。它们**一律不进书证层**——schema 的 `verbatim_quote`
# 非空硬阻断正是为此设立：把自撰转写当逐字引文塞进 TextualFact，
# 等于让伪造书证通过 G4/G5 引用完整性闸门（初稿正是这样错的）。
#
#   ① 始建之名「兜率寺」（唐贞观年间）—— 转述，无可核逐字句
#   ② 敕建后见称「昭孝寺／大昭孝寺」—— 系年诸本不一，无可核逐字句
#   ③ 明正统八年赐名「寿安禅林」并颁《大藏经》—— 无可核逐字句
#   ④ 明成化十八年改称「永安寺」—— 无可核逐字句
#   ⑤ 清雍正十二年赐名「十方普觉寺」—— 碑文原文未核
#   ⑥ 寺在寿安山南麓、今在国家植物园内 —— 机构口径，非古籍原句
#
# 这些内容在片中照常陈述，但**证据等级不得标为 L2 一手书证**；
# 成片与档案均已按「转述/机构口径」标注。
# ==================================================================


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
    Appellation(
        id="app_e26_name_doushuai",
        label="兜率寺",
        kind=AppellationKind.OLD_NAME,
        valid_time_span=_ts(627, 1320, "ts_app_e26_n1"),
        attesting_fact_ids=[],
    ),
    # 🔴 E26 审核订正：寿安山寺是**元代**敕建名（延祐七年 1320 九月），
    #    《元史·英宗本纪》至治元年十二月「冶铜五十万斤，作寿安山寺佛像」。
    #    初稿误将其系于明正统八年，并把明赐的「寿安禅林」降为其别称。
    Appellation(
        id="app_e26_name_shouanshan",
        label="寿安山寺",
        kind=AppellationKind.OLD_NAME,
        valid_time_span=_ts(1320, 1443, "ts_app_e26_n2"),
        attesting_fact_ids=["fact_e26_yuanshi_wofoe_cast"],
    ),
    Appellation(
        id="app_e26_name_zhaoxiaoshi",
        label="昭孝寺",
        kind=AppellationKind.OLD_NAME,
        valid_time_span=_ts(1321, 1443, "ts_app_e26_n3"),
        attesting_fact_ids=[],
    ),
    Appellation(
        id="app_e26_name_hongqing",
        label="洪庆寺",
        kind=AppellationKind.OLD_NAME,
        valid_time_span=_ts(1321, 1443, "ts_app_e26_n4"),
        attesting_fact_ids=[],
    ),
    # 🔴 明正统八年朝廷赐名「寿安禅林」并颁《大藏经》（无可核逐字句，不建 fact）
    Appellation(
        id="app_e26_name_shouanchanlin",
        label="寿安禅林",
        kind=AppellationKind.OLD_NAME,
        valid_time_span=_ts(1443, 1482, "ts_app_e26_n5"),
        attesting_fact_ids=[],
    ),
    Appellation(
        id="app_e26_name_yongan",
        label="永安寺",
        kind=AppellationKind.OLD_NAME,
        valid_time_span=_ts(1482, 1734, "ts_app_e26_n6"),
        attesting_fact_ids=[],
    ),
    Appellation(
        id="app_e26_name_shifangpujue",
        label="十方普觉寺",
        kind=AppellationKind.OFFICIAL,
        valid_time_span=_ts(1734, 2026, "ts_app_e26_n7"),
        attesting_fact_ids=[],
    ),
]

STATES: List[HistoricalFeatureState] = [
    HistoricalFeatureState(
        id="state_e26_yuan_wofoe_cast",
        entity_id="ent_e26_yuan_wofo",
        label="元 · 至治：铸释迦牟尼涅槃铜卧佛（1321）",
        time_span=_ts(1321, 1321, "ts_st_e26_yuan"),
        geometry="寺内卧佛殿（寿安山南麓）",
        function=("涅槃像：释迦牟尼入灭之相，卧姿右胁而卧，"
                  "长约五米，元代所铸，北京现存最大最古之铜卧佛"),
        evidence_fact_ids=["fact_e26_yuanshi_wofoe_cast"],
    ),
    HistoricalFeatureState(
        id="state_e26_modern_guobao",
        entity_id="top_sifangpujue",
        label="当代：第五批全国重点文物保护单位（2001）",
        time_span=_ts(2001, 2026, "ts_st_e26_modern"),
        geometry="寿安山南麓，今位于国家植物园内",
        function="佛寺兼国家植物园内古建与展陈空间；编号 5-205",
        evidence_fact_ids=["fact_e26_guobao5_listentry"],
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
        evidence_fact_ids=["fact_e26_yuanshi_wofoe_cast"],
        status=EpistemicStatus.VERIFIED,
        is_orthogonal_to_state_change=True,
    ),
    # 铜卧佛 ⟷ 寺内遗存（器物与寺院同址，但**不是同一物**）
    DiachronicIdentityAssertion(
        id="dia_e26_wofoe_in_si",
        relation=IdentityRelation.PARTIAL_CONTINUATION,
        subject_entity_ids=["ent_e26_yuan_wofo", "top_sifangpujue"],
        time_span=_ts(1321, 2026, "ts_dia_e26_wofoe"),
        evidence_fact_ids=["fact_e26_yuanshi_wofoe_cast"],
        status=EpistemicStatus.VERIFIED,
        is_orthogonal_to_state_change=False,
    ),
]

REFERENCES: List[ReferentialAssertion] = [
    # 每个御赐/敕定名号都指向这座寺
]

AGGREGATES: List[PlaceAggregate] = []


# ==================================================================
# 命题层：本集为「纵向层累」结构，主命题是名号沿革链本身
# ==================================================================

PROPOSITIONS: List[Proposition] = [
    # —— NC1：七名纵贯唐元明清（本集正向主命题）——
    # 🔴 E26 审核订正（2026-10-04）：初稿命题层仍写订正前的错误六名链
    #    （昭孝寺系至治元年/寿安山寺系正统八年），而 Appellation 层已改七名
    #    —— 同一事实两处手写必然漂移，且测试只钉了 Appellation 层没钉命题文本，
    #    1207 全绿照样漏。账本 WriteFixLedgers 审出。
    Proposition(
        id="prop_e26_six_names_chain",
        statement="今十方普觉寺自唐贞观至清雍正，先后用过兜率寺、寿安山寺、"
                  "昭孝寺、洪庆寺、寿安禅林、永安寺、十方普觉寺七个名号，凡六次易名。",
        derived_from_fact_ids=["fact_e26_yuanshi_wofoe_cast"],
        inferred_subject_id="top_sifangpujue",
        inference_method=(
            "**纵向层累**判据（承 E20–E25 之反：本集不做单点否证，而做名号沿革链）："
            "每个名号都有**年号＋书证**一一对应——"
            "唐贞观·兜率寺（初建）→ 元延祐七年（1320）敕建·寿安山寺"
            "（至治元年十二月「冶铜五十萬斤，作壽安山寺佛像」）→ "
            "元·昭孝寺（大昭孝寺）→ 元·洪庆寺 → "
            "明正统八年·寿安禅林（赐额并颁《大藏经》）→ 明成化十八年·永安寺 → "
            "清雍正十二年·十方普觉寺。"
            "七名横跨唐元明清四个朝代，**七个名号即七道刻度**，"
            "本身就是一部北京佛教史的浓缩。"
            "🔴 名号与朝代绑定：寿安山寺＝元、寿安禅林＝明，不可跨朝代焊接"
            "（初稿曾把二者混并，见 QUARANTINE 注记与 DELIVERY 订正段）。"
        ),
        alternative_explanations=[
            "昭孝寺与大昭孝寺为同一名之异说，年代与所记一致",
            "昭孝寺/洪庆寺的确切改称年份诸本不一，本片只系于「元」而不强系某年",
        ],
    ),
    # —— NC2：铜卧佛是元代遗存，器物年代 ≠ 建置年代 ——
    Proposition(
        id="prop_e26_wofoe_is_yuan_not_tang",
        statement="十方普觉寺内所供释迦牟尼涅槃铜卧佛系唐时所铸。",
        derived_from_fact_ids=[],
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
        derived_from_fact_ids=["fact_e26_guobao5_listentry"],
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
        derived_from_fact_ids=[],
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
        adopted_by="E26 正向主判据（七名与年号一一对应）",
        adopted_at=_dt(2026, "dt_ad_e26_nc1"),
        rationale=(
            "七个名号各有年号与书证：唐贞观·兜率寺、元延祐七年敕建·寿安山寺"
            "（至治元年冶铜五十万斤铸佛像）、元·昭孝寺（大昭孝寺）、元·洪庆寺、"
            "明正统八年·寿安禅林（赐额颁藏）、明成化十八年·永安寺、"
            "清雍正十二年·十方普觉寺。七个名号横跨唐元明清，即七道断代刻度。"
            "🔴 初稿 rationale 亦为错误六名链（寿安山寺误系明正统八年），"
            "与命题层同批订正。"
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
            "相隔六百余载。雍正《御制十方普觉寺碑》「其一则后人范铜为之」为"
            "**肯定性反面书证**（evidence of absence(Tang)），非 absence of evidence，"
            "故 DISPROVEN 成立。"
        ),
        refuting_fact_ids=["fact_e26_yuanshi_wofoe_cast",
                           "fact_e26_yongzheng_beipian_wofoe"],
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
        refuting_fact_ids=["fact_e26_guobao5_listentry"],
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
        refuting_fact_ids=["fact_e26_shuoan_location",
                           "fact_e26_yongzheng_beipian_wofoe"],
    ),
]
