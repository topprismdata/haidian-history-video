# -*- coding: utf-8 -*-
"""haidian_kg/calibration/baijiatuan.py

E27《白家疃·纸上的疃，嘴里的滩》知识库校准模块。

本集的核心不是「某一年的误读」，而是**一个字里的三层证据**：

    《说文》田部「禽兽所践处」  →  《诗经·豳风·东山》「町疃鹿场」  →  陆游「村疃数家」

书证连续两千年。**「疃出自蒙古语、指围猎之地/屯田田庄」是现代趣谈，
无文献学支撑** —— 本集把它作为**被裁决的错说**呈现，而不是字源。

第二条张力在**同一个地名的两种读法**：
    口中念「白家滩」（tān）  ／  纸上写「白家疃」（tuǎn）
两种写法并存至少二百六十余年（乾隆间弘晓诗「滩白」→ 1970 年代
吴恩裕记俗名 → 1992 地名志）。**演变方向未考得，不得单取其一为「原名」定案。**

⚠️ 与 E27/E28 校订的关联（本模块已并入）：
    ① E28 证伪《帝京景物略》「平地温泉如沸」为伪引文，库内 attest_wenquan_dijing
       已由 E28 降为 DISPROVEN —— 本模块**不重复**该裁决。
    ② 「成村于辽金」与「明洪武屯田」两说并存，本模块立为 CONTESTED
       而非 VERIFIED（旧实现曾把三段强度悬殊的断言捆在一条里标 VERIFIED）。

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
#
# 🔴 E26 审核订正的教训：查无逐字原文者**不建成 TextualFact**。
#    schema 的 `verbatim_quote` 非空硬阻断正是为此设立——把自撰转写
#    当逐字引文塞进 fact，等于让伪造书证通过引用完整性闸门。
# ==================================================================

SOURCES: List[HistoricalSource] = [
    source_by_title("说文解字"),
    source_by_title("诗经"),
    source_by_title("陆游集"),
]

DIVISIONS: List[SourceDivision] = [
    SourceDivision(id="div_e27_shuowen_tian", source_id="src_shuowen",
                   volume_number="卷十三", section_title="田部·疃"),
    SourceDivision(id="div_e27_shijing_dongshan", source_id="src_shijing",
                   volume_number="豳风", section_title="东山"),
]


# ==================================================================
# 文本事实层：只有能核到逐字原文的才建成 fact
# ==================================================================

FACTS: List[TextualFact] = [
    # 《说文解字·田部》「疃」字条 —— 本集首要字源证据
    TextualFact(
        id="fact_e27_shuowen_tuan",
        division_id="div_e27_shuowen_tian",
        verbatim_quote="疃，禽獸所踐處也",
        attested_string="疃，禽兽所践处也",
        source_year=_dt(100, "dt_e27_shuowen"),
        translator_note=(
            "东汉许慎《说文解字》田部（L2 一部韵书，非本集自撰）。"
            "🔴 **本集首要字源证据**：「疃」是**汉字**，本义指禽兽践踏之处，"
            "即**田地中的阡陌小径与界畦**。这条与下条《诗经》构成两千年连续书证。"
        ),
    ),
    # 《诗经·豳风·东山》「町疃鹿场」—— 第二级证据
    TextualFact(
        id="fact_e27_shijing_tuan",
        division_id="div_e27_shijing_dongshan",
        verbatim_quote="町疃鹿場",
        attested_string="町疃鹿场",
        source_year=_dt(-600, "dt_e27_shijing"),
        translator_note=(
            "《诗经·豳风·东山》（约西周至春秋，L3 诗集传本）。"
            "「町疃」并用，「鹿场」即鹿苑牧地——与《说文》「禽兽所践处」"
            "**语义连贯**，构成字源的二级证据。毛传亦释「町疃，鹿迹也」。"
        ),
    ),
]


# ==================================================================
# 查无逐字书证者：不建成 TextualFact（E26 审核订正）
# ------------------------------------------------------------------
# 下列五项**广见于各类叙述**，但截至 2026-10-04 未核到可逐字引用的
# 原刊句，故**不进书证层**：
#   ① 允祥别业营建年（雍正二年造 / 雍正三年设指挥处，两说并存）
#   ② 弘晓《明善堂诗集》「滩白」句（转引自吴恩裕说，经樊志斌2015二转，未核原集）
#   ③ 曹雪芹《瓶湖懋斋记盛》（唯一书证为 1943 年孔祥泽过录本，无原件，真伪存争）
#   ④ 1992《海淀区地名志》「原名白家滩」（二手转述，未核原书）
#   ⑤ 教区册「白家瞳」写法（20世纪30—40年代堂口记录，L4 机构口径）
#
# 这些内容在片中照常陈述，但证据等级不得标 L2；成片与档案均按
# 「转述/存疑/传说」标注。
# ==================================================================


# ==================================================================
# 空间实体：怡贤亲王祠残碑（唯一 L1 实物）
# ==================================================================

ENTITIES: List[PersistentSpatialEntity] = [
    PersistentSpatialEntity(
        id="ent_e27_yixianqinci_beibi",
        kind=PhysicalThingKind.HUMAN_MADE_ARTIFACT,
        canonical_label=("敕建白家疃和硕怡亲王祠碑记（残碑，白家疃境内；"
                         "碑额存「敕建」与祠名；清雍正十年1732成祠；"
                         "海淀区文物保护单位）"),
    ),
]

ENTITIES_MAP: Dict[str, PersistentSpatialEntity] = {e.id: e for e in ENTITIES}

APPELLATIONS: List[Appellation] = [
    Appellation(
        id="app_e27_name_baijiatuan",
        label="白家疃",
        kind=AppellationKind.OFFICIAL,
        valid_time_span=_ts(1900, 2026, "ts_app_e27_main"),
        attesting_fact_ids=[],
    ),
    # 教区册异写
    Appellation(
        id="app_e27_name_baijiatong",
        label="白家瞳",
        kind=AppellationKind.TEXTUAL_CORRUPTION,
        valid_time_span=_ts(1930, 1949, "ts_app_e27_tong"),
        attesting_fact_ids=[],
    ),
]

STATES: List[HistoricalFeatureState] = [
    HistoricalFeatureState(
        id="state_e27_yixianqinci_built",
        entity_id="ent_e27_yixianqinci_beibi",
        label="清 · 雍正：怡贤亲王祠成祠（1732）",
        time_span=_ts(1732, 1732, "ts_st_e27_ci"),
        geometry="白家疃村（温泉镇）",
        function=("宗祠：为允祥（生前避雍正帝讳称允祥，雍正八年身后复名胤祥，"
                  "谥「贤」）而建，雍正十年落成；现为海淀区文物保护单位"),
        evidence_fact_ids=["fact_e27_shuowen_tuan"],
    ),
]

TRANSFORMATIONS: List[PlaceTransformation] = []

IDENTITIES: List[DiachronicIdentityAssertion] = [
    # 残碑 ⟷ 怡贤亲王祠（同址同物）
    DiachronicIdentityAssertion(
        id="dia_e27_beibi_祠",
        relation=IdentityRelation.SAME_CONTINUANT,
        subject_entity_ids=["ent_e27_yixianqinci_beibi", "top_baijiatuan"],
        time_span=_ts(1732, 2026, "ts_dia_e27"),
        evidence_fact_ids=["fact_e27_shuowen_tuan"],
        status=EpistemicStatus.VERIFIED,
        is_orthogonal_to_state_change=True,
    ),
]

REFERENCES: List[ReferentialAssertion] = []

AGGREGATES: List[PlaceAggregate] = []


# ==================================================================
# 命题层：字源裁决（本集核心）
# ==================================================================

PROPOSITIONS: List[Proposition] = [
    # —— NC1：疃字字源（本集正向主命题）——
    Proposition(
        id="prop_e27_tuan_is_hanzi",
        statement="「疃」出自蒙古语，意为围猎之地或屯田的田庄。",
        derived_from_fact_ids=["fact_e27_shuowen_tuan", "fact_e27_shijing_tuan"],
        inferred_subject_id="top_baijiatuan",
        inference_method=(
            "**字源否证**（本集核心）：《说文解字·田部》「疃，禽獸所踐處也」"
            "与《诗经·豳风·东山》「町疃鹿場」构成**两千年连续书证**，"
            "「疃」是汉字，本义为田地中的阡陌小径与界畦。"
            "「蒙古语围猎地/屯田田庄说」**无文献学支撑**，"
            "属现代趣谈。本集将其作为**被裁决的错说**呈现，不作字源。"
        ),
        alternative_explanations=[
            "「疃」在宋元以后确实大量用于北方村落名，"
            "但这属**词义引申**（村疃＝村落），与**字源**是两个层次",
        ],
    ),
    # —— NC2：滩/疃并存，演变方向不定案 ——
    Proposition(
        id="prop_e27_tan_tuan_direction",
        statement="白家疃的「疃」系由「滩」改写而来（滩是原名）。",
        derived_from_fact_ids=[],
        inferred_subject_id="top_baijiatuan",
        inference_method=(
            "**两说并存，不定案**：口传「白家滩」（tān）与文写「白家疃」（tuǎn）"
            "至少并存二百六十余年（乾隆间弘晓诗「滩白」→ 1970 年代吴恩裕记俗名"
            "→ 1992 地名志）。演变方向**未考得**："
            "既可能是「滩」改写作「疃」，也可能是「疃」的白读即「滩」。"
            "**不得单取其一为「原名」定案。**"
        ),
        alternative_explanations=[
            "教区册另有「白家瞳」写法，为「疃」的同音异写",
            "两种读法可能长期并存于同一地名的不同人群口传中",
        ],
    ),
    # —— NC8：成村年代无书证 ——
    Proposition(
        id="prop_e27_founded_liao_jin",
        statement="白家疃成村于辽金时代或更早。",
        derived_from_fact_ids=[],
        inferred_subject_id="top_baijiatuan",
        inference_method=(
            "**无书证，降级为传说**：辽金文献与金石均未检得。"
            "另有一说「明洪武屯田移民聚落」，亦无独立书证。"
            "两说并存，本片只标「相传/存疑」，**不得写成断代事实**。"
        ),
        alternative_explanations=["辽金说", "明洪武屯田说", "年代不可考"],
    ),
    # —— NC5/NC6：曹雪芹居留 ——
    Proposition(
        id="prop_e27_caoxueqin_settled",
        statement="曹雪芹晚年定居白家疃，终老于此。",
        derived_from_fact_ids=[],
        inferred_subject_id="top_baijiatuan",
        inference_method=(
            "**学术假说，且须带存疑框架**：唯一书证是无原件的《瓶湖懋斋记盛》"
            "过录本，真伪有争（吴恩裕、冯其庸主真；陈毓罴、刘世德质疑；"
            "郭若愚认为书法出自近人之手）。主真一派考订其居白家疃"
            "约当乾隆二十三年（1758）春至二十四年（1759）初，**约一年**。"
            "🔴 **严禁写成「晚年定居」「终老于此」**。"
        ),
        alternative_explanations=["主真派", "质疑派", "过录本系后人伪托"],
    ),
    # —— NC7：文保口径 ——
    Proposition(
        id="prop_e27_guobao",
        statement="白家疃境内有全国重点文物保护单位。",
        derived_from_fact_ids=[],
        inferred_subject_id="top_baijiatuan",
        inference_method=(
            "**文保口径**（本集零国保）：白家疃境内**无全国重点文物保护单位**。"
            "怡贤亲王祠为**海淀区文物保护单位**（区名录批次存疑，"
            "原始公布文件未核验）。本集**严禁出现任何「X-YYY」式国保编号**。"
        ),
        alternative_explanations=[],
    ),
]

ADOPTIONS: List[BeliefAdoption] = [
    BeliefAdoption(
        proposition_id="prop_e27_tuan_is_hanzi",
        status=EpistemicStatus.DISPROVEN,
        confidence=0.94,
        adopted_by="E27 正向主判据（字源否证，《说文》＋《诗经》双书证）",
        adopted_at=_dt(2026, "dt_ad_e27_nc1"),
        rationale=(
            "《说文》「疃，禽獸所踐處也」与《诗经》「町疃鹿場」构成两千年连续书证。"
            "「蒙古语围猎地说」无文献学支撑，DISPROVEN。"
        ),
        refuting_fact_ids=["fact_e27_shuowen_tuan", "fact_e27_shijing_tuan"],
    ),
    BeliefAdoption(
        proposition_id="prop_e27_tan_tuan_direction",
        # 无任何一手书证可定演变方向 —— absence of evidence ≠ evidence of absence
        status=EpistemicStatus.UNSUBSTANTIATED,
        confidence=0.9,
        adopted_by="E27 负控制 V-NC02（滩/疃并存，方向不定案）",
        adopted_at=_dt(2026, "dt_ad_e27_nc2"),
        rationale=(
            "两种读法并存二百六十余年，演变方向无定向书证。"
            "「滩是原名」与「疃的白读即滩」两说并存，严禁单取其一定案。"
        ),
    ),
    BeliefAdoption(
        proposition_id="prop_e27_founded_liao_jin",
        status=EpistemicStatus.UNSUBSTANTIATED,
        confidence=0.88,
        adopted_by="E27 负控制 V-NC08（成村年代无书证）",
        adopted_at=_dt(2026, "dt_ad_e27_nc8"),
        rationale=(
            "辽金说与明洪武屯田说均无书证，属传说层，严禁写成断代事实。"
        ),
    ),
    BeliefAdoption(
        proposition_id="prop_e27_caoxueqin_settled",
        status=EpistemicStatus.UNSUBSTANTIATED,
        confidence=0.85,
        adopted_by="E27 负控制 V-NC05/NC06（居留须带存疑、时长不得夸大）",
        adopted_at=_dt(2026, "dt_ad_e27_nc5"),
        rationale=(
            "唯一书证为无原件过录本，真伪存争；主真派考订居留约一年。"
            "「定居/终老」无据，严禁书写。"
        ),
    ),
    BeliefAdoption(
        proposition_id="prop_e27_guobao",
        # 🔴 absence of evidence ≠ evidence of absence：
        #    「境内有国保」是**无据**（国保名录无命中），不是**已证伪**
        #    （无「此处确非国保」的正面书证）。故 UNSUBSTANTIATED。
        status=EpistemicStatus.UNSUBSTANTIATED,
        confidence=0.93,
        adopted_by="E27 负控制 V-NC07（本集零国保，严禁国保编号）",
        adopted_at=_dt(2026, "dt_ad_e27_nc7"),
        rationale=(
            "国保名录中无白家疃境内条目；怡贤亲王祠为海淀区文物保护单位"
            "（区保批次存疑，原始公布文件未核验）。"
            "本集严禁出现任何「X-YYY」式国保编号。"
        ),
    ),
]
