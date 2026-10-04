# -*- coding: utf-8 -*-
"""haidian_kg/calibration/guoshoujing.py

E29《郭守敬·一泉入都》知识库校准模块（系列收束集：人物×地名）。

本集是**水系总源头集**：E1 肖家河、E3 青龙桥、E8 高梁桥、E16 南长河等集的地物
全部长在郭守敬至元二十九年（1292）工程逻辑上。命题层主线两条：
    ① 正向闭环——通惠河（含白浮泉引水）为郭守敬建言并主持
      （本纪/列传/河渠志三处独立书证，V-NC01）；
    ② 辨伪收束——「长河郭守敬所开」「泽被六百年」「发明海拔」等全网流行说
      在本集一次钉死（V-NC02/03/06），反哺全部水系集口径库。

书证纪律（承 E26 审核订正）：
    本模块全部 verbatim_quote **逐字**取自 guoshoujing_video/research.md
    已直核原文（《元史》维基文库转录本；行状为四库转录本，标注逐字上屏前
    须对影印页复核）。查无逐字书证者（如「白浮堰」之后世纪称、登封观星台
    「元代遗构」之 L4 口径、明仿简仪「原件不存」之机构口径）**不建成
    TextualFact**，只在实体标签或命题推理文字中按其真实等级陈述。

🔴 查无逐字书证者清单（不入书证层）：
    ① 「白浮堰/白浮堰渠」系后世纪称——research.md §1.8(八) 明标 L4 转述
    ② 登封观星台「元代遗构/一批国保/世遗」——L4 机构口径
    ③ 明仿简仪「原件 1715 年被熔毁」——博物馆通行口径，原始文献未直核（§4-16）
    ④ 「沿等高线绕行」解释——现代水利史口径，未直核专书（§4-12）
    ⑤ 白浮泉遗址「1990 市保/2013 七批国保/大运河源头遗址公园」——L4 机构口径

DISPROVEN 纪律（承 E25 元教训）：每条 DISPROVEN 必须带 refuting_fact_ids；
无据者用 UNSUBSTANTIATED——absence of evidence ≠ evidence of absence。
本集唯一例外式判定：四海测验二十七所为**穷举名单**（传文「凡二十七所」＋
天文志恰 27 条互证），「名单之外设站」的否定属穷举排除，可判 DISPROVEN。

Python 3.9.6 兼容：禁 X | None，禁 match。
"""
from typing import Dict, List, Optional

from .bibliography import source_by_title
from ..ontology.epistemic import (
    BeliefAdoption, EpistemicStatus, HistoricalSource, Proposition,
    SourceCategory, SourceDivision, TextualFact,
)
from ..ontology.spatiotemporal import (
    Appellation, AppellationKind, DiachronicIdentityAssertion,
    HistoricalFeatureState, IdentityRelation, PersistentSpatialEntity,
    PhysicalThingKind, PlaceAggregate, PlaceTransformation,
    ReferentialAssertion,
)
from ..ontology.temporal import (
    CalibrationTable, DatePoint, GregorianDate, TimeSpan,
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

_SRC_YUANSHI = source_by_title("元史")
_SRC_RXJWKC = source_by_title("钦定日下旧闻考")
assert _SRC_YUANSHI is not None and _SRC_YUANSHI.id == "src_yuanshi"
assert _SRC_RXJWKC is not None and _SRC_RXJWKC.id == "src_rxjwkc"

SOURCES: List[HistoricalSource] = [
    _SRC_YUANSHI,
    _SRC_RXJWKC,
    # 《国朝文类》卷五十·齐履谦《知太史院事郭公行状》：元人一手行状（L3 顶格），
    # 本传即据行状删改而成（中华本《元史》卷164 校勘记六次据行状改字可证）。
    # 书目库原无此节点，本集新增；所引为四库转录本（无标点），
    # 逐字上屏前须对影印页复核（research.md §1.13 版本警告）。
    HistoricalSource(
        id="src_guochao_wenlei",
        title="国朝文类",
        category=SourceCategory.LITERARY_COLLECTION,
        edition_note="四库转录本直核（底本无标点）；齐履谦《知太史院事郭公行状》"
                     "为本传底本级参照。逐字上屏前以影印页复核。",
    ),
]

DIVISIONS: List[SourceDivision] = [
    # ── 《元史》卷164 列传·郭守敬传 ──
    SourceDivision(id="div_e29_gsj_zhuan", source_id="src_yuanshi",
                   volume_number="卷一百六十四", section_title="郭守敬传"),
    # 《元史》卷164 列传·王恂传（research.md 未注记卷次，照实标注转引）
    SourceDivision(id="div_e29_wangxun_zhuan", source_id="src_yuanshi",
                   volume_number="列传", section_title="王恂传（转引）"),
    # ── 《元史》卷64 河渠志一（通惠河／白浮甕山／海子分条立卷）──
    SourceDivision(id="div_e29_hqz_tonghui", source_id="src_yuanshi",
                   volume_number="卷六十四", section_title="河渠志一·通惠河"),
    SourceDivision(id="div_e29_hqz_baifu", source_id="src_yuanshi",
                   volume_number="卷六十四", section_title="河渠志一·白浮甕山"),
    SourceDivision(id="div_e29_hqz_haizi", source_id="src_yuanshi",
                   volume_number="卷六十四", section_title="河渠志一·海子"),
    # ── 《元史》本纪 ──
    SourceDivision(id="div_e29_benji_11", source_id="src_yuanshi",
                   volume_number="卷十一", section_title="世祖本纪八"),
    SourceDivision(id="div_e29_benji_17", source_id="src_yuanshi",
                   volume_number="卷十七", section_title="世祖本纪十四"),
    # ── 《元史》卷48 天文志（四海测验二十七所全名单）──
    SourceDivision(id="div_e29_tianwenzhi", source_id="src_yuanshi",
                   volume_number="卷四十八", section_title="天文志·四海测验"),
    # ── 《国朝文类》卷50 行状 ──
    SourceDivision(id="div_e29_xingzhuang", source_id="src_guochao_wenlei",
                   volume_number="卷五十", section_title="知太史院事郭公行状"),
    # ── 《日下旧闻考》 ──
    SourceDivision(id="div_e29_rxjwkc_77", source_id="src_rxjwkc",
                   volume_number="卷七十七", section_title="长河（转引 E16 直核）"),
    SourceDivision(id="div_e29_rxjwkc_84", source_id="src_rxjwkc",
                   volume_number="卷八十四", section_title="御制万寿山昆明湖记（转引 E16 直核）"),
]


# ==================================================================
# 文本事实层（verbatim 逐字取自 research.md 已直核原文）
# ==================================================================

FACTS: List[TextualFact] = [
    # ── 主持权三证之一：郭传「復置都水監，俾守敬領之」──
    TextualFact(
        id="fact_e29_fuzhi_dushuijian",
        division_id="div_e29_gsj_zhuan",
        verbatim_quote="於是復置都水監，俾守敬領之。帝命丞相以下皆親操畚鍤倡工，待守敬指授而後行事。",
        attested_string="復置都水監俾守敬領之",
        source_year=_dt(1370, "dt_e29_yuanshi_comp"),
        translator_note=(
            "《元史·郭守敬传》至元二十八年条（维基文库转录本直核）。"
            "**主持权三证之一**：复置都水监由守敬**领之**，且「待守敬指授而後行事」——"
            "工程指挥权在郭守敬，非仅建言人。"
        ),
    ),
    # ── 主持权三证之二：河渠志「都水監郭守敬奉詔興舉水利，因建言」──
    TextualFact(
        id="fact_e29_fengzhao_jianyan",
        division_id="div_e29_hqz_tonghui",
        verbatim_quote="都水監郭守敬奉詔興舉水利，因建言",
        attested_string="都水監郭守敬奉詔興舉水利因建言",
        source_year=_dt(1370, "dt_e29_yuanshi_comp2"),
        translator_note=(
            "《元史·河渠志一·通惠河》至元二十八年条（维基文库转录本直核）。"
            "**主持权三证之二**：建言人＝都水监郭守敬本人。「大都」二字据中华本校勘记一补。"
        ),
    ),
    # ── 主持权三证之三：本纪「命太史令郭守敬兼領都水監事」──
    TextualFact(
        id="fact_e29_benji_jianling",
        division_id="div_e29_benji_17",
        verbatim_quote="命太史令郭守敬兼領都水監事",
        attested_string="命太史令郭守敬兼領都水監事",
        source_year=_dt(1370, "dt_e29_yuanshi_comp3"),
        translator_note=(
            "《元史》卷十七·至元二十八年条（维基文库转录本直核）。"
            "**主持权三证之三**：本纪口径「兼領都水監事」。"
            "本纪（兼领）与列传（俾守敬领之）措辞微异，主持权指向一致。"
            "🔴 网络常说「至元二年任都水监」——实为都水**少监**（副职），须分层。"
        ),
    ),
    # ── 白浮泉引水段（郭传）：线路拓扑 ＋ 瓮山泊先在 ＋ 长河辨核心书证 ──
    TextualFact(
        id="fact_e29_baifu_route_zhuan",
        division_id="div_e29_gsj_zhuan",
        verbatim_quote="別引北山白浮泉水，西折而南，經瓮山泊，自西水門入城，環匯於積水潭，復東折而南，出南水門，合入舊運糧河。",
        attested_string="白浮泉水西折而南經瓮山泊環匯於積水潭",
        source_year=_dt(1370, "dt_e29_yuanshi_comp4"),
        translator_note=(
            "《元史·郭守敬传》至元二十八年条（维基文库转录本直核；此页「瓮山泊」用简体"
            "「瓮」，卷64同条作「甕」——用字照录，见 research.md §1.13）。"
            "① 线路拓扑三关键词：**西折而南 / 經瓮山泊 / 環匯於積水潭**——示意资产只画此"
            "拓扑关系，严禁编造精确走向；② 「**經**瓮山泊」证瓮山泊 1292 年前已存在，"
            "郭守敬只是让水经过它（D3「开凿昆明湖」之反证）；③ 该段循高梁河故道入城——"
            "河道先在，郭守敬是系统化利用（D4「长河郭守敬所开」之反证）。"
        ),
    ),
    # ── 河渠志：白浮村神山泉（白浮泉在昌平之书证）──
    TextualFact(
        id="fact_e29_baifu_cun",
        division_id="div_e29_hqz_tonghui",
        verbatim_quote="上自昌平縣白浮村引神山泉，西折南轉，過雙塔、榆河、一畝、玉泉諸水，至西水門入都城",
        attested_string="自昌平縣白浮村引神山泉",
        source_year=_dt(1370, "dt_e29_yuanshi_comp5"),
        translator_note=(
            "《元史·河渠志一·通惠河》（维基文库转录本直核）。"
            "源头为**昌平县白浮村**之神山泉——白浮泉在今**昌平区城南街道龙山**，不在海淀。"
            "沿途汇双塔、榆河、一亩、玉泉诸泉；玉泉山另有御用「金水河」线，两线并行不可混。"
        ),
    ),
    # ── 河渠志：白浮甕山条（昌平縣界）──
    TextualFact(
        id="fact_e29_baifu_cping_county",
        division_id="div_e29_hqz_baifu",
        verbatim_quote="白浮泉水在昌平縣界，西折而南，經甕山泊，自西水門入都城焉。",
        attested_string="白浮泉水在昌平縣界",
        source_year=_dt(1370, "dt_e29_yuanshi_comp6"),
        translator_note=(
            "《元史·河渠志一·白浮甕山》：「白浮甕山，即通惠河上源之所出也」条"
            "（维基文库转录本直核；此卷用「甕」）。与郭传「經瓮山泊」同源互证。"
        ),
    ),
    # ── 河渠志：通惠河全长唯一上屏口径 ──
    TextualFact(
        id="fact_e29_zongchang",
        division_id="div_e29_hqz_tonghui",
        verbatim_quote="總長一百六十四里一百四步",
        attested_string="總長一百六十四里一百四步",
        source_year=_dt(1370, "dt_e29_yuanshi_comp7"),
        translator_note=(
            "《元史·河渠志一·通惠河》（维基文库转录本直核）。"
            "🔴 V-NC09：通惠河长度只采此一个口径上屏；「160 里/200 里/5.5km」等混写禁用。"
            "闸数两口径（《元史》壩牐一十處共二十座 vs《新开通惠河碑》转引二十有四）"
            "只可并陈不可混用。"
        ),
    ),
    # ── 河渠志：首事/告成/赐名 ──
    TextualFact(
        id="fact_e29_shoushi_gaocheng",
        division_id="div_e29_hqz_tonghui",
        verbatim_quote="首事於至元二十九年之春，告成於三十年之秋，賜名曰通惠。",
        attested_string="首事於至元二十九年之春告成於三十年之秋賜名曰通惠",
        source_year=_dt(1370, "dt_e29_yuanshi_comp8"),
        translator_note=(
            "《元史·河渠志一·通惠河》（维基文库转录本直核）。"
            "工程区间：至元二十九年（1292）春动工，三十年（1293）秋告成，同年赐名通惠。"
            "郭传赐名场景：「帝還自上都，過積水潭，見舳艫敝水，大悅」。"
        ),
    ),
    # ── 河渠志：闸名（广源闸＝海淀境内第一闸名）──
    TextualFact(
        id="fact_e29_zhaming",
        division_id="div_e29_hqz_tonghui",
        verbatim_quote="其壩牐之名曰：廣源牐",
        attested_string="其壩牐之名曰廣源牐",
        source_year=_dt(1370, "dt_e29_yuanshi_comp9"),
        translator_note=(
            "《元史·河渠志一·通惠河》坝牐名录首闸（维基文库转录本直核；「牐」＝「閘」异体，"
            "照录）。广源闸即此闸系第一闸名，今海淀紫竹院街道（三山五园地名名录第二批标"
            "「元代」，L4）。🔴 元贞元年改名名单中**无**广源闸（沿用 E16-06）。"
        ),
    ),
    # ── 河渠志：积水潭（引水终点调蓄湖）──
    TextualFact(
        id="fact_e29_jishuitan",
        division_id="div_e29_hqz_haizi",
        verbatim_quote="海子一名積水潭，聚西北諸泉之水，流行入都城而匯于此，汪洋如海，都人因名焉。",
        attested_string="海子一名積水潭聚西北諸泉之水",
        source_year=_dt(1370, "dt_e29_yuanshi_comp10"),
        translator_note=(
            "《元史·河渠志一·海子岸条》（维基文库转录本直核）。"
            "积水潭＝引水系统终点调蓄湖，属郭守敬改造范围。"
            "「船停在什刹海」的地望依据即此湖。"
        ),
    ),
    # ── 衰败链·大德七年（1303）冲决 ──
    TextualFact(
        id="fact_e29_dade7_chongjue",
        division_id="div_e29_hqz_baifu",
        verbatim_quote="山水暴漲，漫流隄上，衝決水口",
        attested_string="山水暴漲衝決水口",
        source_year=_dt(1370, "dt_e29_yuanshi_comp11"),
        translator_note=(
            "《元史·河渠志一·白浮甕山》大德七年（1303）条（维基文库转录本直核）。"
            "原文纪日：「自閏五月二十九日始，晝夜雨不止，六月九日夜半」而后山水暴漲。"
            "衰败链第一环。"
        ),
    ),
    # ── 衰败链·大德十一年（1307）崩三十余里 ──
    TextualFact(
        id="fact_e29_dade11_beng",
        division_id="div_e29_hqz_baifu",
        verbatim_quote="巡視白浮甕山河隄，崩三十餘里",
        attested_string="白浮甕山河隄崩三十餘里",
        source_year=_dt(1370, "dt_e29_yuanshi_comp12"),
        translator_note=(
            "《元史·河渠志一·白浮甕山》大德十一年（1307）条（维基文库转录本直核）。"
            "衰败链第二环。"
        ),
    ),
    # ── 衰败链·皇庆元年（1312）修治 ──
    TextualFact(
        id="fact_e29_huangqing_xiu",
        division_id="div_e29_hqz_baifu",
        verbatim_quote="白浮甕山隄，多低薄崩陷處，宜修治",
        attested_string="白浮甕山隄多低薄崩陷處宜修治",
        source_year=_dt(1370, "dt_e29_yuanshi_comp13"),
        translator_note=(
            "《元史·河渠志一·白浮甕山》皇庆元年（1312）条（维基文库转录本直核）。"
            "同条纪功：「總修長三十七里二百十五步，計七萬三千七百七十三工」。衰败链第三环。"
        ),
    ),
    # ── 衰败链·延祐元年（1314）淤塞（本集核心反证）──
    TextualFact(
        id="fact_e29_yanyou_yuse",
        division_id="div_e29_hqz_baifu",
        verbatim_quote="自白浮甕山下至廣源牐隄隁，多淤澱淺塞，源泉微細，不能通流",
        attested_string="源泉微細不能通流",
        source_year=_dt(1370, "dt_e29_yuanshi_comp14"),
        translator_note=(
            "《元史·河渠志一·白浮甕山》延祐元年（1314）条（维基文库转录本直核；"
            "「隁」＝「堰」异体，照录）。**郭守敬卒（延祐三年，1316）前两年**，"
            "上源已「源泉微細，不能通流」——「泽被六百年」「至今仍在供水」之核心反证。"
            "泉眼湮塞确切年代未考得（research.md §4-9），书证链止于延祐已淤、乾隆不可详。"
        ),
    ),
    # ── 四海测验·凡二十七所（穷举名单之传文侧）──
    TextualFact(
        id="fact_e29_sihai_27suo",
        division_id="div_e29_gsj_zhuan",
        verbatim_quote="東至高麗，西極滇池，南踰朱崖，北盡鐵勒，四海測驗，凡二十七所。",
        attested_string="四海測驗凡二十七所",
        source_year=_dt(1370, "dt_e29_yuanshi_comp15"),
        translator_note=(
            "《元史·郭守敬传》至元十六年条（维基文库转录本直核）。"
            "**穷举名单**：天文志（卷48）全录 27 所名单，条数恰与传文「凡二十七所」合。"
            "名单无西藏（乌思藏）、无云南站点（最西西涼州/成都），今海淀境内无任何一站；"
            "「西極滇池」与名单不合为史传行文，存疑（research.md §4-5），正片只呈名单原文。"
            "「西極滇池」四字系传文行语照录，**不得**当作云南设站书证。"
        ),
    ),
    # ── 天文志：大都站（京师站；今海淀无站之参照）──
    TextualFact(
        id="fact_e29_dadu_station",
        division_id="div_e29_tianwenzhi",
        verbatim_quote="大都，北極出地四十度太強，夏至晷景長一丈二尺三寸六分，晝六十二刻，夜三十八刻",
        attested_string="大都北極出地四十度太強",
        source_year=_dt(1370, "dt_e29_yuanshi_comp16"),
        translator_note=(
            "《元史》卷四十八·天文志「四海測驗」大都条（维基文库转录本直核）。"
            "北京附近观测点＝**大都**（另有上都）；观测机构即太史院/司天台，"
            "今地推定在都城东南今建国门一带（北京天文馆现行口径 L4）。"
            "离今海淀最近的观测活动在城内——「观天的没有海淀」；"
            "郭守敬给海淀的是水（引水渠），不是台。"
        ),
    ),
    # ── 歲餘：回归年原文形态 ──
    TextualFact(
        id="fact_e29_suiyu",
        division_id="div_e29_gsj_zhuan",
        verbatim_quote="自宋大明壬寅年距至今日八百一十年，每歲合得三百六十五日二十四刻二十五分，其二十五分為今曆歲餘合用之數。",
        attested_string="每歲合得三百六十五日二十四刻二十五分",
        source_year=_dt(1370, "dt_e29_yuanshi_comp17"),
        translator_note=(
            "《元史·郭守敬传》十七年奏文「所考正者凡七事」之二（维基文库转录本直核）。"
            "授时历用百刻制：24 刻 25 分＝24.25 刻＝0.2425 日 → 365.2425 日/年。"
            "🔴 V-NC04：原文是**分数/刻分**，不是小数——禁用「精确到小数点后四位」；"
            "365.2425 之换算须挂「据现代学者换算」并作 L4 口径。"
        ),
    ),
    # ── 王恂传：以其年冬颁行（「次年颁行」之反证）──
    TextualFact(
        id="fact_e29_wangxun_banxing",
        division_id="div_e29_wangxun_zhuan",
        verbatim_quote="十七年，曆成，賜名授時曆，以其年冬，頒行天下。",
        attested_string="以其年冬頒行天下",
        source_year=_dt(1370, "dt_e29_yuanshi_comp18"),
        translator_note=(
            "《元史》列传·王恂传（research.md §1.7 直核引文；该传卷次本档未逐字注记，"
            "篇卷照实标「列传（转引）」）。成历于至元十七年（1280），**其年冬颁行**；"
            "与本纪卷十一至元十七年十一月「甲子，詔頒授時曆」互证。"
            "次年（1281，辛巳）是**行用**之始——通行「次年颁行」不准确。"
        ),
    ),
    # ── 本纪卷十一：诏颁授时历 ──
    TextualFact(
        id="fact_e29_benji_banli",
        division_id="div_e29_benji_11",
        verbatim_quote="甲子，詔頒授時曆",
        attested_string="詔頒授時曆",
        source_year=_dt(1370, "dt_e29_yuanshi_comp19"),
        translator_note=(
            "《元史》卷十一·至元十七年十一月条（维基文库转录本直核）。"
            "与王恂传「以其年冬，頒行天下」互证，颁行年＝成历年（1280）。"
        ),
    ),
    # ── 郭传：曆之本在於測驗 ──
    TextualFact(
        id="fact_e29_liben",
        division_id="div_e29_gsj_zhuan",
        verbatim_quote="曆之本在於測驗，而測驗之器莫先儀表",
        attested_string="曆之本在於測驗",
        source_year=_dt(1370, "dt_e29_yuanshi_comp20"),
        translator_note=(
            "《元史·郭守敬传》至元十三年奉命修历条（维基文库转录本直核）。"
            "P3 页眼：先造仪器后测天；简仪、高表、景符诸仪清单见同传仪器段。"
        ),
    ),
    # ── 行状：以海面较（海拔概念的思想萌芽，D2 一手出处）──
    TextualFact(
        id="fact_e29_haimian_jiao",
        division_id="div_e29_xingzhuang",
        verbatim_quote="嘗以海面較京師至汴梁地形高下之差",
        attested_string="以海面較京師至汴梁地形高下之差",
        source_year=_dt(1344, "dt_e29_wenlei_comp"),
        translator_note=(
            "齐履谦《知太史院事郭公行状》（《国朝文类》卷五十，四库转录本直核，底本无标点）。"
            "**D2 一手出处**：以海平面为参照比较两地高差，且以河流流速佐证。"
            "🔴 只可说「以海平面比较两地地形高差的思想见于行状」；"
            "「郭守敬发明了海拔」是现代概念回溯——行状未建立任何测量体系、基准面定义"
            "或术语，主旨亦为大都漕运地形判断服务。"
            "版本警告：另有版本作「京師與汴梁」，上屏前以影印页复核（research.md §4-11）。"
        ),
    ),
    # ── 行状：不可及者有三（P8 收束页眼）──
    TextualFact(
        id="fact_e29_bukeji_san",
        division_id="div_e29_xingzhuang",
        verbatim_quote="公以純德實學為世師法，然其不可及者有三：一曰水利之學，二曰厯數之學，三曰儀象制度之學。",
        attested_string="不可及者有三水利之學厯數之學儀象制度之學",
        source_year=_dt(1344, "dt_e29_wenlei_comp2"),
        translator_note=(
            "齐履谦《知太史院事郭公行状》总评（四库转录本直核；「厯」＝「曆」异体，照录）。"
            "P8 收束：水利／历数／仪象三学并峙。"
        ),
    ),
    # ── 日下旧闻考卷77：长河之名（D4 反证）──
    TextualFact(
        id="fact_e29_changhe_name",
        division_id="div_e29_rxjwkc_77",
        verbatim_quote="高梁橋在西直門之北，其水發源于玉泉，由昆明湖秀漪橋東流注，此即長河也",
        attested_string="此即長河也",
        source_year=_dt(1785, "dt_e29_rxjwkc_comp"),
        translator_note=(
            "《日下旧闻考》卷七十七（转引 E16 直核）。「长河」作为地名指称此段水道是"
            "**清代口径**（三山五园地名名录第二批亦标「清代」）；河道本体为高梁河故道，"
            "北魏《水经注》已记（E16-19 直核）。🔴 D4：郭守敬至元二十九年工程是把"
            "既有河道纳入通惠河上源并建闸系统化利用——不是凭空开河。"
        ),
    ),
    # ── 日下旧闻考卷84：乾隆自承湮没（衰败链末环）──
    TextualFact(
        id="fact_e29_qianlong_yanmo",
        division_id="div_e29_rxjwkc_84",
        verbatim_quote="歲己巳，考通惠河之源，而勒碑于麥莊橋。元史所載引白浮甕山諸泉云者，時皆湮沒不可詳",
        attested_string="時皆湮沒不可詳",
        source_year=_dt(1751, "dt_e29_kunminghuji"),
        translator_note=(
            "乾隆《万寿山昆明湖记》（1751 年作，追述己巳 1749 考源；转引 E16 直核"
            "《日下旧闻考》卷八十四；标点为录入者所加）。衰败链末环：乾隆朝考源时"
            "白浮、瓮山诸泉引水故迹已「湮沒不可詳」。逐字上屏前以影印页复核。"
        ),
    ),
    # ── 日下旧闻考卷84：昆明湖命名（D3 反证）──
    TextualFact(
        id="fact_e29_kunminghu_mingming",
        division_id="div_e29_rxjwkc_84",
        verbatim_quote="建大報恩延壽寺命名萬壽山並疏導玉泉諸派匯于西湖易名曰昆明湖",
        attested_string="易名曰昆明湖",
        source_year=_dt(1750, "dt_e29_kunminghu"),
        translator_note=(
            "乾隆十五年（1750）事，见御制文转录（《日下旧闻考》卷八十四；转引 E16 直核）。"
            "「昆明湖」之名与今湖体系**清代扩展**西湖（瓮山泊）而成——湖体名与形皆晚于"
            "郭守敬近四百六十年。🔴 「郭守敬扩大瓮山泊」：《元史》无载，未考得一手依据，"
            "只可说「用作调蓄」（research.md §4-4）。"
        ),
    ),
]

# ==================================================================
# 🔴 查无逐字书证者：不建成 TextualFact（承 E26 审核订正）
# ------------------------------------------------------------------
# 下列四项**广见于叙述**，但截至 2026-10-04 未核到可逐字引用的原文句，
# 一律不进书证层（verbatim_quote 非空硬阻断正是为此设立）：
#   ① 「白浮堰/白浮堰渠」后世纪称（research.md §1.8(八) L4 转述）
#   ② 登封观星台「元代遗构/第一批国保/世遗」（L4 机构口径）
#   ③ 明仿简仪「原件 1715 年被传教士熔毁」（博物馆通行口径，原始文献未直核）
#   ④ 「沿等高线绕行以维持坡降」（现代水利史口径，未直核专书）
#   ⑤ 「与历史上之北京城息息相关者首推白浮泉」（侯仁之语，媒体转述口径）
# 这些内容片中照常陈述，但证据等级不得标为 L2/L3 书证。
# ==================================================================


# ==================================================================
# 空间实体
# ==================================================================

ENTITIES: List[PersistentSpatialEntity] = [
    PersistentSpatialEntity(
        id="ent_e29_baifuquan",
        kind=PhysicalThingKind.NATURAL_SPRING,
        canonical_label=("白浮泉（神山泉）：昌平县城东龙山之下，元通惠河上源；"
                         "今九龙池无自然涌泉，泉眼湮塞确切年代未考得"),
    ),
    PersistentSpatialEntity(
        id="ent_e29_tonghuihe",
        kind=PhysicalThingKind.HUMAN_MADE_CHANNEL,
        canonical_label=("通惠河（含白浮泉引水渠）：郭守敬至元二十九年建言并主持开凿，"
                         "二十九年春首事、三十年秋告成；全长一百六十四里一百四步"),
    ),
    PersistentSpatialEntity(
        id="ent_e29_guangyuanzha",
        kind=PhysicalThingKind.HYDRAULIC_STRUCTURE,
        canonical_label=("广源闸（《元史》壩牐名录首闸「廣源牐」）：长河上，"
                         "今海淀区紫竹院街道；海淀境内与郭守敬直接相关的实物遗存之一"),
    ),
    PersistentSpatialEntity(
        id="ent_e29_wengshanpo",
        kind=PhysicalThingKind.NATURAL_WATERCOURSE,
        canonical_label=("瓮山泊（今昆明湖故址）：1292 年前已存在之调蓄湖，"
                         "郭守敬引水「經」之而非开凿之；乾隆十五年扩展后命名昆明湖"),
    ),
    PersistentSpatialEntity(
        id="ent_e29_jishuitan",
        kind=PhysicalThingKind.NATURAL_WATERCOURSE,
        canonical_label=("积水潭（海子）：元大都西北隅引水汇止之调蓄湖，"
                         "「汪洋如海」；今什刹海一带"),
    ),
    PersistentSpatialEntity(
        id="ent_e29_jianyi",
        kind=PhysicalThingKind.HUMAN_MADE_ARTIFACT,
        canonical_label=("简仪：郭守敬原制不存；明正统年间依旧制仿制，"
                         "今存南京紫金山天文台——画面不得把明仿制品说成原件"),
    ),
    PersistentSpatialEntity(
        id="ent_e29_dengfeng_guansingtai",
        kind=PhysicalThingKind.SINGLE_BUILDING,
        canonical_label=("登封观星台：元代遗构，二十七所之「河南府陽城」站；"
                         "第一批全国重点文物保护单位（机构口径）"),
    ),
]

ENTITIES_MAP: Dict[str, PersistentSpatialEntity] = {e.id: e for e in ENTITIES}

APPELLATIONS: List[Appellation] = [
    Appellation(
        id="app_e29_shenshanquan",
        label="神山泉",
        kind=AppellationKind.OLD_NAME,
        valid_time_span=_ts(1292, 2026, "ts_app_e29_n1"),
        attesting_fact_ids=["fact_e29_baifu_cun"],
    ),
    Appellation(
        id="app_e29_baifuquan",
        label="白浮泉",
        kind=AppellationKind.OFFICIAL,
        valid_time_span=_ts(1292, 2026, "ts_app_e29_n2"),
        attesting_fact_ids=["fact_e29_baifu_cping_county"],
    ),
    # 「白浮堰」为后世纪称（L4 转述，查无逐字书证，不建 fact）
    Appellation(
        id="app_e29_baifu_yan",
        label="白浮堰",
        kind=AppellationKind.VULGAR,
        valid_time_span=_ts(1292, 2026, "ts_app_e29_n3"),
        attesting_fact_ids=[],
    ),
    Appellation(
        id="app_e29_tonghuihe",
        label="通惠河",
        kind=AppellationKind.HONORIFIC,
        valid_time_span=_ts(1293, 2026, "ts_app_e29_n4"),
        attesting_fact_ids=["fact_e29_shoushi_gaocheng"],
    ),
    Appellation(
        id="app_e29_wengshanpo",
        label="瓮山泊",
        kind=AppellationKind.OLD_NAME,
        script_variants=["甕山泊"],
        valid_time_span=_ts(1292, 1750, "ts_app_e29_n5"),
        attesting_fact_ids=["fact_e29_baifu_route_zhuan"],
    ),
    Appellation(
        id="app_e29_kunminghu",
        label="昆明湖",
        kind=AppellationKind.OFFICIAL,
        valid_time_span=_ts(1750, 2026, "ts_app_e29_n6"),
        attesting_fact_ids=["fact_e29_kunminghu_mingming"],
    ),
    Appellation(
        id="app_e29_guangyuanzha",
        label="广源闸",
        kind=AppellationKind.OFFICIAL,
        script_variants=["廣源牐"],
        valid_time_span=_ts(1292, 2026, "ts_app_e29_n7"),
        attesting_fact_ids=["fact_e29_zhaming"],
    ),
    Appellation(
        id="app_e29_haizi",
        label="海子",
        kind=AppellationKind.OLD_NAME,
        valid_time_span=_ts(1292, 2026, "ts_app_e29_n8"),
        attesting_fact_ids=["fact_e29_jishuitan"],
    ),
]

STATES: List[HistoricalFeatureState] = [
    HistoricalFeatureState(
        id="state_e29_tonghui_build",
        entity_id="ent_e29_tonghuihe",
        label="元 · 至元二十九年至三十年：开凿通惠河",
        time_span=_ts(1292, 1293, "ts_st_e29_build"),
        geometry="白浮泉—瓮山泊—积水潭—通州高丽庄，總長一百六十四里一百四步",
        function="节水通漕：江南漕船直抵积水潭；每十里置一牐，凡为牐七（郭传口径）",
        evidence_fact_ids=["fact_e29_shoushi_gaocheng", "fact_e29_zongchang"],
    ),
    HistoricalFeatureState(
        id="state_e29_tonghui_silted",
        entity_id="ent_e29_tonghuihe",
        label="元 · 延祐元年：上源淤塞不能通流",
        time_span=_ts(1314, 1314, "ts_st_e29_silted"),
        geometry="自白浮甕山下至廣源牐隄隁，多淤澱淺塞",
        function="上源已淤，源泉微細不能通流——郭守敬卒前两年（差军千人疏治）",
        evidence_fact_ids=["fact_e29_yanyou_yuse"],
    ),
    HistoricalFeatureState(
        id="state_e29_guangyuanzha_yuan",
        entity_id="ent_e29_guangyuanzha",
        label="元 · 至元：壩牐之首「廣源牐」建置",
        time_span=_ts(1292, 1368, "ts_st_e29_gyz"),
        geometry="长河上（瓮山泊下泄入城段），今海淀紫竹院街道",
        function="通惠河坝牐之首，节水以通漕运",
        evidence_fact_ids=["fact_e29_zhaming"],
    ),
    HistoricalFeatureState(
        id="state_e29_jishuitan_hub",
        entity_id="ent_e29_jishuitan",
        label="元 · 至元三十年：舳艫敝水（帝过积水潭）",
        time_span=_ts(1293, 1293, "ts_st_e29_jst"),
        geometry="大都城内西北隅，引水環匯于此",
        function="引水系统终点调蓄湖；帝还自上都过积水潭见舳艫敝水大悦，赐名通惠",
        evidence_fact_ids=["fact_e29_jishuitan", "fact_e29_shoushi_gaocheng"],
    ),
    HistoricalFeatureState(
        id="state_e29_wengshanpo_yuan",
        entity_id="ent_e29_wengshanpo",
        label="元 · 至元：引水「經」瓮山泊（先在调蓄湖）",
        time_span=_ts(1292, 1314, "ts_st_e29_wsp"),
        geometry="青龙桥一带入泊，白浮泉水西折而南經之",
        function="白浮泉引水中途调蓄；《元史》只言「經」，无疏浚扩大之载",
        evidence_fact_ids=["fact_e29_baifu_route_zhuan", "fact_e29_baifu_cping_county"],
    ),
]

TRANSFORMATIONS: List[PlaceTransformation] = []

IDENTITIES: List[DiachronicIdentityAssertion] = [
    # 通惠河：身份延续而上源湮塞（属性变化与身份延续正交）
    DiachronicIdentityAssertion(
        id="dia_e29_tonghui_same",
        relation=IdentityRelation.SAME_CONTINUANT,
        subject_entity_ids=["ent_e29_tonghuihe"],
        time_span=_ts(1293, 2026, "ts_dia_e29_th"),
        evidence_fact_ids=["fact_e29_shoushi_gaocheng", "fact_e29_yanyou_yuse"],
        status=EpistemicStatus.VERIFIED,
        is_orthogonal_to_state_change=True,
        alternative_relations=[
            "上源白浮泉段元代中期已湮塞，今存者为下游故道——身份延续而水文形态已变",
        ],
    ),
    # 瓮山泊 → 今昆明湖：同一水体，名与形两变（清代扩展）
    DiachronicIdentityAssertion(
        id="dia_e29_wengshanpo_kunminghu",
        relation=IdentityRelation.PARTIAL_CONTINUATION,
        subject_entity_ids=["ent_e29_wengshanpo"],
        time_span=_ts(1292, 2026, "ts_dia_e29_wsp"),
        evidence_fact_ids=["fact_e29_baifu_route_zhuan", "fact_e29_kunminghu_mingming"],
        status=EpistemicStatus.VERIFIED,
        is_orthogonal_to_state_change=True,
        alternative_relations=[
            "今昆明湖为乾隆十五年扩展西湖（瓮山泊）而成，湖形已变——部分延续而非全同",
            "郭守敬对瓮山泊有无疏浚扩大，《元史》无载（存疑，不得采用扩大说）",
        ],
    ),
]

REFERENCES: List[ReferentialAssertion] = []

AGGREGATES: List[PlaceAggregate] = [
    PlaceAggregate(
        id="agg_e29_tonghui_system",
        label="通惠河引水体系（白浮泉—瓮山泊—积水潭）",
        time_span=_ts(1293, 2026, "ts_agg_e29"),
        member_entity_ids=[
            "ent_e29_baifuquan", "ent_e29_wengshanpo",
            "ent_e29_jishuitan", "ent_e29_guangyuanzha", "ent_e29_tonghuihe",
        ],
    ),
]


# ==================================================================
# 命题层：正向闭环（三证）＋ 辨伪收束（D 节五条全录）
# ==================================================================

PROPOSITIONS: List[Proposition] = [
    # —— NC1 正向主命题：通惠河为郭守敬建言并主持（三证闭环）——
    Proposition(
        id="prop_e29_tonghui_led_by_guo",
        statement="通惠河（含白浮泉引水）为郭守敬建言并主持。",
        derived_from_fact_ids=[
            "fact_e29_fengzhao_jianyan", "fact_e29_benji_jianling",
            "fact_e29_fuzhi_dushuijian",
        ],
        inferred_subject_id="ent_e29_tonghuihe",
        inference_method=(
            "**三处独立书证闭环**判据（V-NC01）：河渠志「都水監郭守敬奉詔興舉水利，"
            "因建言」（建言人）＋本纪「命太史令郭守敬兼領都水監事」（长官职）＋"
            "郭传「復置都水監，俾守敬領之」「待守敬指授而後行事」（指挥权）。"
            "本纪/列传/河渠志三处独立指向一致。一切「非郭守敬主持」类说法，"
            "凡拿不出文献原文的，一律不进正片。"
        ),
        alternative_explanations=[
            "「郭守敬只是建议，工程别人主持」说无任何文献原文支撑（不可考清单 §4-1）",
        ],
    ),
    # —— NC2「长河是郭守敬所开」——
    Proposition(
        id="prop_e29_changhe_dug_by_guo",
        statement="长河（今绣漪桥至高梁桥段）是郭守敬所开。",
        derived_from_fact_ids=[],
        inferred_subject_id="ent_e29_guangyuanzha",
        inference_method=(
            "**河道先在**判据（V-NC02，与 E8 红线 4、E16 红线 9 同口径钉死）："
            "①高梁水北魏《水经注》已记（E16-19 直核），金已有闸；②郭传「西折而南，"
            "**經**瓮山泊，自西水門入城」——水循高梁河故道入城，河道先在；"
            "③「长河」作为地名是清代口径（《日下旧闻考》卷七十七「此即長河也」，"
            "三山五园名录第二批标「清代」）。郭守敬至元二十九年工程是**系统化利用与"
            "重构**（纳入通惠河上源、建广源等闸），不是凭空开河。"
        ),
        alternative_explanations=[
            "「郭守敬开凿长河」多见于网络科普（L5），无任何书证",
        ],
    ),
    # —— NC3「发明海拔」——
    Proposition(
        id="prop_e29_haiba_invention",
        statement="郭守敬发明了海拔。",
        derived_from_fact_ids=[],
        inferred_subject_id="ent_e29_tonghuihe",
        inference_method=(
            "**概念回溯**判定（V-NC06，承 E26 查无书证纪律）：一手出处只有行状"
            "「嘗以海面較京師至汴梁地形高下之差」（fact_e29_haimian_jiao）——"
            "以海平面为参照比较高差的思想**确有一手文献内核**；但行状未建立任何"
            "测量体系、基准面定义或术语，且该段主旨为大都漕运地形判断服务；"
            "「海拔」作为系统概念是近代测绘学产物。查无「发明海拔」之任何原文——"
            "既无书证可证其成立，亦无原文可作逐字反驳，判 UNSUBSTANTIATED。"
        ),
        alternative_explanations=[
            "现代科技史称行状记载为海拔概念的思想萌芽（L4 口径，表述须挂「行状称」）",
        ],
    ),
    # —— NC3 正面：行状思想萌芽（VERIFIED）——
    Proposition(
        id="prop_e29_haiba_germ",
        statement="以海平面比较两地地形高差的思想见于元人齐履谦所撰郭守敬行状。",
        derived_from_fact_ids=["fact_e29_haimian_jiao"],
        inferred_subject_id="ent_e29_tonghuihe",
        inference_method=(
            "**一手引文直接支撑**判据：行状原文「嘗以海面較京師至汴梁地形高下之差」"
            "（L3 元人一手行状，中华本校勘记六次据行状改字可证行状为本传底本级参照）。"
            "表述纪律：只可说「以海平面比较两地地形高差的思想见于行状」，"
            "并挂「行状称」；不得升格为「发明海拔」。"
        ),
        alternative_explanations=[
            "另有版本作「京師與汴梁」（research.md §4-11），上屏前以影印页复核",
        ],
    ),
    # —— NC4「泽被六百年」——
    Proposition(
        id="prop_e29_zabei_600_years",
        statement="白浮泉引水系统泽被后世六百年，至今仍在供水。",
        derived_from_fact_ids=[],
        inferred_subject_id="ent_e29_tonghuihe",
        inference_method=(
            "**衰败链书证**判据（V-NC03）：大德七年（1303）「山水暴漲……衝決水口」"
            "→大德十一年（1307）「崩三十餘里」→皇庆元年（1312）「多低薄崩陷處，"
            "宜修治」→延祐元年（1314，郭守敬卒前两年）「多淤澱淺塞，源泉微細，"
            "不能通流」→乾隆己巳（1749）御制文自承「時皆湮沒不可詳」。"
            "有**肯定性反面书证链**（不是 absence of evidence），故 DISPROVEN 成立。"
            "今日九龙池无自然涌泉，遗址建成为大运河源头遗址公园（L4）。"
        ),
        alternative_explanations=[
            "元贞至泰定间积水潭海子岸有石砌维修记载——下游局部维护不等于上源活水",
        ],
    ),
    # —— NC5「白浮泉在海淀」——
    Proposition(
        id="prop_e29_baifu_in_haidian",
        statement="白浮泉在今海淀区。",
        derived_from_fact_ids=[],
        inferred_subject_id="ent_e29_baifuquan",
        inference_method=(
            "**双重书证**判据（V-NC07 空间自证）：河渠志「上自昌平縣白浮村引神山泉」"
            "＋白浮甕山条「白浮泉水在昌平縣界」——两处独立记载均系白浮泉于昌平县。"
            "今址：昌平区城南街道龙山（2013 第七批国保「白浮泉遗址」，L4）。"
            "「白浮泉现在是玉泉山/北海的泉眼」亦证伪：金水河条证玉泉另线。"
        ),
        alternative_explanations=[
            "引水渠「過……玉泉諸水」使海淀诸泉汇入通惠河——汇入不等于源头在海淀",
        ],
    ),
    # —— NC6 四海测验无海淀站点——
    Proposition(
        id="prop_e29_sihai_haidian_station",
        statement="四海测验二十七所中有观测站在今海淀境内。",
        derived_from_fact_ids=[],
        inferred_subject_id="ent_e29_dengfeng_guansingtai",
        inference_method=(
            "**穷举名单排除**判据（V-NC05）：天文志全录 27 所名单，条数恰与传文"
            "「凡二十七所」合——名单是穷举的，名单之外的否定属穷举排除而非 absence "
            "of evidence，故可判 DISPROVEN。名单最北铁勒、最南琼州；无西藏、无云南"
            "（最西西涼州/成都）；北京附近＝大都站（四十度太強）与上都站，"
            "观测机构在都城内。今海淀境内无任何一站——观天在城内，引水才经过海淀。"
            "「测量了万里长城/西藏/整个中国」均无书证；「西極滇池」为传文行语，"
            "与名单不合属存疑（§4-5），不作云南设站书证。"
        ),
        alternative_explanations=[
            "元司天台地望有异说（research.md §4-10），采用时挂机构名",
        ],
    ),
    # —— NC7「郭守敬开凿昆明湖」——
    Proposition(
        id="prop_e29_dug_kunminghu",
        statement="瓮山泊（昆明湖前身）是郭守敬开凿的。",
        derived_from_fact_ids=[],
        inferred_subject_id="ent_e29_wengshanpo",
        inference_method=(
            "**空间自证**判据（D3）：郭传「西折而南，經瓮山泊」＋河渠志「白浮泉水在"
            "昌平縣界，西折而南，經甕山泊」——两卷独立原文均用「**經**」字，"
            "证瓮山泊 1292 年前已存在；郭守敬只是让水经过它（用作调蓄）。"
            "「昆明湖」之名系乾隆十五年（1750）「易名曰昆明湖」，今湖体系清代扩展"
            "西湖而成。肯定性反证链成立，DISPROVEN。"
        ),
        alternative_explanations=[
            "元代积水潭海子岸石砌维修记载存在——但那是积水潭不是瓮山泊",
        ],
    ),
    # —— NC7b「郭守敬扩大瓮山泊」：查无书证，UNSUBSTANTIATED——
    Proposition(
        id="prop_e29_expanded_wengshanpo",
        statement="郭守敬至元二十九年工程扩大（疏浚）了瓮山泊。",
        derived_from_fact_ids=[],
        inferred_subject_id="ent_e29_wengshanpo",
        inference_method=(
            "**查无书证**判定（research.md §4-4）：《元史》纪、传、志仅言「經」瓮山泊，"
            "扩建说未考得一手依据——absence of evidence ≠ evidence of absence，"
            "判 UNSUBSTANTIATED（非 DISPROVEN）。画面若需表达调蓄功能，"
            "只能写「用作调蓄」，不得写「扩大/疏浚」。"
        ),
        alternative_explanations=["（无一手依据之说，本片不采用）"],
    ),
    # —— NC8「次年颁行」——
    Proposition(
        id="prop_e29_cinian_banxing",
        statement="《授时历》成历之后次年方颁行。",
        derived_from_fact_ids=[],
        inferred_subject_id="ent_e29_tonghuihe",
        inference_method=(
            "**两条 L2 互证**判据：王恂传「十七年，曆成，賜名授時曆，以其年冬，"
            "頒行天下」＋本纪卷十一至元十七年十一月「甲子，詔頒授時曆」——"
            "成历于至元十七年（1280），**其年冬颁行**；次年（1281，辛巳）是行用之始。"
            "通行「次年颁行」不准确，正片不采用。"
        ),
        alternative_explanations=[
            "纪传歧异另见王恂卒年（十八年 vs 十九年，§4-3），正片用模糊表述或采王恂传",
        ],
    ),
    # —— NC9 通惠河长度唯一口径（正向锚）——
    Proposition(
        id="prop_e29_zongchang_caliber",
        statement="通惠河全长为總長一百六十四里一百四步（《元史》唯一上屏口径）。",
        derived_from_fact_ids=["fact_e29_zongchang"],
        inferred_subject_id="ent_e29_tonghuihe",
        inference_method=(
            "**单口径纪律**判据（V-NC09）：通惠河长度只采《元史》「總長一百六十四里"
            "一百四步」上屏；「160 里/200 里/5.5 公里」等混写禁用。闸数两口径"
            "（《元史》二十座 vs《新开通惠河碑》转引二十有四）只可并陈不可混用。"
        ),
        alternative_explanations=[
            "《新开通惠河碑》载闸二十四座（转引口径），与《元史》二十座并陈",
        ],
    ),
]

ADOPTIONS: List[BeliefAdoption] = [
    BeliefAdoption(
        proposition_id="prop_e29_tonghui_led_by_guo",
        status=EpistemicStatus.VERIFIED,
        confidence=0.96,
        adopted_by="E29 正向主判据（本纪/列传/河渠志三证闭环）",
        adopted_at=_dt(2026, "dt_ad_e29_nc1"),
        rationale=(
            "三处独立书证指向一致：河渠志（建言人＝郭守敬）＋本纪（兼领都水监事）＋"
            "郭传（俾守敬领之、待守敬指授而後行事）。「非郭守敬主持」类说法拿不出"
            "任何文献原文，一律不进正片。"
        ),
        refuting_fact_ids=[],
    ),
    BeliefAdoption(
        proposition_id="prop_e29_changhe_dug_by_guo",
        status=EpistemicStatus.DISPROVEN,
        confidence=0.95,
        adopted_by="E29 负控制 V-NC02（长河非郭守敬所开）",
        adopted_at=_dt(2026, "dt_ad_e29_nc2"),
        rationale=(
            "河道先在：水循高梁河故道入城（郭传「經瓮山泊，自西水門入城」），"
            "北魏已记高梁水；「长河」地名是清代口径。郭守敬是系统化利用与重构，"
            "不是凭空开河。与 E8 红线 4、E16 红线 9 同口径。"
        ),
        refuting_fact_ids=["fact_e29_baifu_route_zhuan", "fact_e29_changhe_name"],
    ),
    BeliefAdoption(
        proposition_id="prop_e29_haiba_invention",
        # 查无「发明海拔」原文可证可驳：行状思想萌芽为真，概念拔高为现代回溯——
        # 无逐字书证支撑该断言本身，采 UNSUBSTANTIATED（absence of evidence
        # ≠ evidence of absence，承 E26 元教训）。
        status=EpistemicStatus.UNSUBSTANTIATED,
        confidence=0.9,
        adopted_by="E29 负控制 V-NC06（发明海拔＝现代概念回溯）",
        adopted_at=_dt(2026, "dt_ad_e29_nc3"),
        rationale=(
            "一手内核只有行状「以海面較」一句：思想萌芽为真，但无测量体系、无基准面"
            "定义、无术语，主旨为漕运地形判断。「发明海拔」无书证可证，亦无单条原文"
            "可作逐字反驳，故 UNSUBSTANTIATED；正面表述走 prop_e29_haiba_germ（VERIFIED）。"
        ),
    ),
    BeliefAdoption(
        proposition_id="prop_e29_haiba_germ",
        status=EpistemicStatus.VERIFIED,
        confidence=0.9,
        adopted_by="E29 正向判据（行状一手引文直接支撑）",
        adopted_at=_dt(2026, "dt_ad_e29_nc4"),
        rationale=(
            "行状原文逐字可核（四库转录本直核）：以海平面为参照比较高差并疑以流速佐证。"
            "表述纪律：只说「思想见于行状」，不升格为「发明海拔」。"
        ),
        refuting_fact_ids=[],
    ),
    BeliefAdoption(
        proposition_id="prop_e29_zabei_600_years",
        status=EpistemicStatus.DISPROVEN,
        confidence=0.95,
        adopted_by="E29 负控制 V-NC03（衰败链书证）",
        adopted_at=_dt(2026, "dt_ad_e29_nc5"),
        rationale=(
            "衰败链为**肯定性反面书证**：大德七年冲决→大德十一年崩三十余里→皇庆元年"
            "修治→延祐元年「源泉微細，不能通流」（郭守敬卒前两年）→乾隆己巳「時皆湮沒"
            "不可詳」。泉死得比人早，「泽被六百年」「至今仍在供水」证伪。"
        ),
        refuting_fact_ids=["fact_e29_yanyou_yuse", "fact_e29_qianlong_yanmo"],
    ),
    BeliefAdoption(
        proposition_id="prop_e29_baifu_in_haidian",
        status=EpistemicStatus.DISPROVEN,
        confidence=0.97,
        adopted_by="E29 负控制 V-NC07（白浮泉在昌平不在海淀）",
        adopted_at=_dt(2026, "dt_ad_e29_nc6"),
        rationale=(
            "河渠志两处独立记载均系白浮泉于昌平县（白浮村神山泉／白浮泉水在昌平縣界）；"
            "今址为昌平区城南街道龙山（第七批国保，L4）。玉泉山另线（金水河），"
            "与白浮泉无涉。"
        ),
        refuting_fact_ids=["fact_e29_baifu_cun", "fact_e29_baifu_cping_county"],
    ),
    BeliefAdoption(
        proposition_id="prop_e29_sihai_haidian_station",
        status=EpistemicStatus.DISPROVEN,
        confidence=0.93,
        adopted_by="E29 负控制 V-NC05（二十七所穷举名单排除）",
        adopted_at=_dt(2026, "dt_ad_e29_nc7"),
        rationale=(
            "天文志 27 所名单条数与传文「凡二十七所」恰合——名单穷举，名单之外设站"
            "属穷举排除而非 absence of evidence。无西藏、无云南站点；北京附近只有"
            "大都/上都两站，观测机构在都城内；今海淀境内无任何一站。"
        ),
        refuting_fact_ids=["fact_e29_sihai_27suo", "fact_e29_dadu_station"],
    ),
    BeliefAdoption(
        proposition_id="prop_e29_dug_kunminghu",
        status=EpistemicStatus.DISPROVEN,
        confidence=0.96,
        adopted_by="E29 负控制 NC7（瓮山泊先在，郭守敬使水經之）",
        adopted_at=_dt(2026, "dt_ad_e29_nc8"),
        rationale=(
            "郭传与河渠志两卷独立原文均用「經」字——瓮山泊 1292 年前已存在；"
            "「昆明湖」之名系乾隆十五年所赐，今湖为清代扩展而成。"
            "开凿说证伪；扩大说另判 UNSUBSTANTIATED（prop_e29_expanded_wengshanpo）。"
        ),
        refuting_fact_ids=[
            "fact_e29_baifu_route_zhuan", "fact_e29_baifu_cping_county",
            "fact_e29_kunminghu_mingming",
        ],
    ),
    BeliefAdoption(
        proposition_id="prop_e29_expanded_wengshanpo",
        # 《元史》无载：未考得一手依据，absence of evidence ≠ evidence of absence，
        # 采 UNSUBSTANTIATED（research.md §4-4）。
        status=EpistemicStatus.UNSUBSTANTIATED,
        confidence=0.9,
        adopted_by="E29 负控制 NC7b（扩大瓮山泊查无书证）",
        adopted_at=_dt(2026, "dt_ad_e29_nc9"),
        rationale=(
            "纪、传、志均只言「經」瓮山泊，扩建说未考得一手依据——无据可用"
            "UNSUBSTANTIATED，不得冒用 DISPROVEN。画面只可写「用作调蓄」。"
        ),
    ),
    BeliefAdoption(
        proposition_id="prop_e29_cinian_banxing",
        status=EpistemicStatus.DISPROVEN,
        confidence=0.93,
        adopted_by="E29 负控制 NC8（其年冬颁行，两条 L2 互证）",
        adopted_at=_dt(2026, "dt_ad_e29_nc10"),
        rationale=(
            "王恂传「以其年冬，頒行天下」＋本纪至元十七年十一月「甲子，詔頒授時曆」"
            "互证：颁行年＝成历年（1280）。次年（1281）是行用之始，「次年颁行」证伪。"
        ),
        refuting_fact_ids=["fact_e29_wangxun_banxing", "fact_e29_benji_banli"],
    ),
    BeliefAdoption(
        proposition_id="prop_e29_zongchang_caliber",
        status=EpistemicStatus.VERIFIED,
        confidence=0.95,
        adopted_by="E29 正向口径锚 V-NC09（长度单口径上屏）",
        adopted_at=_dt(2026, "dt_ad_e29_nc11"),
        rationale=(
            "《元史》「總長一百六十四里一百四步」为唯一上屏口径；闸数两口径并陈不混用"
            "（沿用 E16 红线 8）。"
        ),
        refuting_fact_ids=[],
    ),
]
