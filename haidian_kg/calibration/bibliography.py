"""
haidian_kg/calibration/bibliography.py
海淀史一手文献登记总表

v2.1 之前的问题（实测）：
- 《钦定日下旧闻考》因卷72/卷99被建成两条文献
- 《清仁宗睿皇帝实录》因卷46/卷76被建成两条文献
- 全部 12 条文献的 author_person_id 均为空
- 版本信息退化为一串自由文本

本表确立原则：
1. **一部书 = 一个 HistoricalSource 节点**，卷次一律归 SourceDivision
2. 作者/编者必须接 HistoricalPerson
3. 底本类型必须结构化（四库本/点校本/实测图…），供版本互校
4. 生卒年、成书年不确定者一律留空，严禁臆造
"""
from typing import Dict, List, Optional

from ..ontology.epistemic import HistoricalSource, SourceCategory
from ..ontology.temporal import CalibrationTable, DatePoint, GregorianDate, TimeSpan

CAL = CalibrationTable.CN_ASTRONOMICAL_ALMANAC

# 底本类型枚举值（写入 base_edition）
SISHU = "四库全书本"
ZHONGHUA = "中华书局点校本"
SHIBEN = "原本/石刻"
CETU = "实测图籍"


def _ts(y1, y2, tag):
    return TimeSpan(id=tag, label="%d-%d" % (y1, y2),
                    begin=DatePoint(id=tag + "b", label=str(y1),
                                    gregorian=GregorianDate(year=y1, calibration=CAL)),
                    end=DatePoint(id=tag + "e", label=str(y2),
                                  gregorian=GregorianDate(year=y2, calibration=CAL)))


# ==================================================================
# 权威书目：一书一条
# ==================================================================

BIBLIOGRAPHY: List[HistoricalSource] = [
    # ---------- 魏晋南北朝 ----------
    HistoricalSource(
        id="src_shuijingzhu", title="水经注",
        category=SourceCategory.GEOGRAPHICAL_TREATISE,
        author_person_id="person_lidaoyuan",
        version_description="杨守敬、熊会贞《水经注疏》中华书局点校本",
        base_edition=ZHONGHUA,
        edition_note="点校本以《永乐大典》辑补；卷十三漯水与卷十四鲍丘水为两个独立篇卷，"
                     "严禁拼接为一句原典",
    ),
    HistoricalSource(
        id="src_sanguozhi", title="三国志",
        category=SourceCategory.OFFICIAL_HISTORY,
        author_person_id="person_chen_shu",
        total_volumes=65,
        base_edition=ZHONGHUA,
        edition_note="《魏书》载刘靖为镇北将军、假节、都督河北诸军事，"
                     "非「督幽州」；灌田数历经二千/四千三百一十六/五千九百三十/万余顷诸说，"
                     "须分年分阶段，不可收束为单一数字",
    ),

    # ---------- 元代 ----------
    HistoricalSource(
        id="src_zhongtang", title="中堂事记",
        category=SourceCategory.LITERARY_COLLECTION,
        author_person_id="person_yuanweiyuan",
        edition_note="中统元年(1260)首载「海店」，为海淀成镇最早确证",
    ),
    HistoricalSource(
        id="src_yuanshi", title="元史",
        category=SourceCategory.OFFICIAL_HISTORY,
        compiler_person_ids=["person_owen_te"],
        total_volumes=210,
        base_edition=ZHONGHUA,
        edition_note="《河渠志》载至元二十九年开通惠河、闸坝用木、至大四年始议砖石、泰定四年讫工",
    ),
    HistoricalSource(
        id="src_liaoshi", title="辽史",
        category=SourceCategory.OFFICIAL_HISTORY,
        total_volumes=116,
        base_edition=ZHONGHUA,
        edition_note="卷八十四列传第十四·耶律休哥载高梁河之战「宋主仅以身免，至涿州，窃乘驴车遁去」",
    ),
    HistoricalSource(
        id="src_songshi", title="宋史",
        category=SourceCategory.OFFICIAL_HISTORY,
        total_volumes=496,
        base_edition=ZHONGHUA,
        edition_note="本纪第四·太宗一载太平兴国四年围幽州四十余日",
    ),

    # ---------- 明代 ----------
    HistoricalSource(
        id="src_wanshu", title="宛署杂记",
        category=SourceCategory.LOCAL_GAZETTEER,
        author_person_id="person_shenbang",
        edition_note="万历年间沈榜任宛平知县所撰，海淀一带明代聚落地名一手账本",
    ),

    HistoricalSource(
        id="src_ymy_sijifang", title="圆明园四十景图咏",
        category=SourceCategory.LITERARY_COLLECTION,
        author_person_id="person_qianlong",
        base_edition=SISHU,
        edition_note="乾隆十二年(1747)御制并命画院绘图、词臣题咏，"
                     "是圆明园景观定名与格局的一手文献",
    ),
    HistoricalSource(
        id="src_ymy_yuan", title="圆明园园史资料",
        category=SourceCategory.ARCHAEOLOGY_REPORT,
        version_description="圆明园管理处公开园史沿革",
        edition_note="建园、焚毁、接管与遗址公园建设的公开沿革资料",
    ),

    # ---------- 清代 ----------
    HistoricalSource(
        id="src_bqtz", title="钦定八旗通志",
        category=SourceCategory.OFFICIAL_HISTORY,
        # ⚠️ 实为356卷（卷首12 + 志269 + 表71）。
        #    先前凭印象写的「250卷」已作废——数字必须核实，不得臆造。
        total_volumes=356,
        compiled_time=_ts(1786, 1796, "ts_bqtz"),
        base_edition=SISHU,
        edition_note="乾隆五十一年(1786)下旨重修，嘉庆元年(1796)撰成赐名。"
                     "卷34驻防、卷55旗人、卷116营建志；"
                     "卷116「東四木村東邉」疑为讹字，"
                     "镶红旗方位以《日下旧闻考》卷72「静明园东北」为准",
    ),
    HistoricalSource(
        id="src_rxjwkc", title="钦定日下旧闻考",
        category=SourceCategory.OFFICIAL_HISTORY,
        base_edition=SISHU,
        total_volumes=160,
        edition_note="卷72官署门引《八旗册》载各旗廨舍/官房楹数；"
                     "卷73「其暢春園樹村香山三汛仍舊」证明树村汛1781前已存；"
                     "卷99郊坰西九载树村五圣庵、观音寺；卷130/131「独树村」在房山县，非海淀",
    ),
    HistoricalSource(
        id="src_rizhi", title="清仁宗睿皇帝实录",
        category=SourceCategory.OFFICIAL_HISTORY,
        base_edition=SHIBEN,
        edition_note="卷46嘉庆四年六月初二日设左右翼总兵；"
                     "卷76嘉庆五年十一月十七日谕副将移驻树村",
    ),
    HistoricalSource(
        id="src_qingshigao", title="清史稿",
        category=SourceCategory.OFFICIAL_HISTORY,
        base_edition=ZHONGHUA,
        edition_note="卷117职官四，民国官修，仅作旁证",
    ),
    HistoricalSource(
        id="src_huangchaowenxiantongkao", title="皇朝文献通考",
        category=SourceCategory.OFFICIAL_HISTORY,
        base_edition=SISHU,
        edition_note="卷87载乾隆四十六年巡捕三营添改五营设二十三汛",
    ),
    HistoricalSource(
        id="src_huangchaotongdian", title="皇朝通典",
        category=SourceCategory.OFFICIAL_HISTORY,
        base_edition=SISHU,
        edition_note="卷31载中营汛五：圆明园汛、畅春园汛、静宜园汛、树村汛、乐善园汛",
    ),
    HistoricalSource(
        id="src_zyztj", title="竹叶亭杂记",
        category=SourceCategory.LITERARY_COLLECTION,
        author_person_id="person_yaoxingzong",
        edition_note="姚元之撰，卷一记嘉庆六年副将移驻树村之实施",
    ),
    HistoricalSource(
        id="src_wushizhangzhi", title="武卫将军八旗都统实事求是",
        category=SourceCategory.OFFICIAL_HISTORY,
        base_edition=SISHU,
        edition_note="",
    ),
    HistoricalSource(
        id="src_daqinghuidian", title="钦定大清会典",
        category=SourceCategory.OFFICIAL_HISTORY,
        base_edition=SISHU,
        edition_note="卷100员额、卷33兵制志，载圆明园护军营员额",
    ),
    HistoricalSource(
        id="src_wuchengsiyuan", title="五城寺院册",
        category=SourceCategory.EPIGRAPHY,
        base_edition=SISHU,
        edition_note="《日下旧闻考》卷99引，载树村五圣庵、观音寺",
    ),
]

#: 常见简称 → 规范书名 归一表
TITLE_ALIASES: Dict[str, str] = {
    "日下旧闻考": "钦定日下旧闻考",
    "八旗通志": "钦定八旗通志",
    "大清会典": "钦定大清会典",
    "皇朝通典": "皇朝通典",
    "仁宗实录": "清仁宗睿皇帝实录",
    "清实录": "清仁宗睿皇帝实录",
}


def normalize_title(raw: str) -> str:
    """把简称归一到规范书名，防止同一本书被建成多条节点"""
    return TITLE_ALIASES.get(raw.strip(), raw.strip())


def source_by_title(title: str) -> Optional[HistoricalSource]:
    t = normalize_title(title)
    for s in BIBLIOGRAPHY:
        if s.title == t:
            return s
    return None
