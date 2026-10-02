"""
haidian_kg/calibration/urban.py
商业与近现代词条：苏州街（E12 万寿街）／中关村（E13）

数据全部取自已冻结的交付 research.md v2，不凭印象补写：
  - suzhoujie_video/research.md（v2，GPT 复核 18 条全采纳后冻结）
  - zhongguancun_video/research.md（v2，2026-10-02 冻结）

本批五条核心纪律（每条都来自交付档案的红线清单）：
  1. 万寿寺外买卖街（万寿街，俗称苏州街）是真买卖的皇家街市；
     「太监宫女扮商贩」的一手记载（姚元之《竹叶亭杂记》）属园内买卖街
     （同乐园等），严禁移植给万寿街——这是 v2 复查拦下的对象混同硬伤。
  2. 万寿街营建年份口径：昭梿《啸亭杂录》卷十系年乾隆辛巳（1761）七旬万寿
     之年；1751 六旬（倚虹堂/万寿寺一修）与 1761 七旬（万寿寺再修/五塔寺
     再修/万寿街营建）分属两轮，不得混为一轮。
  3. 毁废口径：《天咫偶闻》卷九「自庚申秋御园被毁……日就零落」＋
     「今已毁尽」——万寿街自身无直接军事焚毁记录，1860 年不设状态，
     「被英法联军烧毁」直说在结构上无状态支撑（缺证据≠通过）。
  4. 中关村名称三段分层：明清「中官村」（义地俗称）→ 1913《京西图》
     已标注「中关」（雅化在先）→ 1950 年代机构定名（信笺误植＝当事人
     回忆，口述史料；陈垣说降「一说」）。「中关」不是 1953 年才出现。
  5. 文献卷次两处考订（本模块纠正预置书目表/交付档案的笔误并留痕）：
     - 《天咫偶闻》万寿街条经维基文库复核在卷九（郊坰），非卷七；
     - 《汉书》「诸中官」条经原书复核出《高后纪第三》高后八年（前180）春，
       非交付档案所记《高帝纪》；「中官」指宦官的词源结论不变。
"""
import re
from typing import List

from ..ontology.temporal import (
    CalibrationTable, DatePoint, Era, GregorianDate, ReignYear, TimeSpan,
)
from ..ontology.epistemic import (
    BeliefAdoption, EpistemicStatus, HistoricalSource, Proposition,
    SourceDivision, TextualFact,
)
from ..ontology.spatiotemporal import (
    Appellation, AppellationKind, DiachronicIdentityAssertion,
    HistoricalFeatureState, IdentityRelation, PersistentSpatialEntity,
    PhysicalThingKind, PlaceAggregate, PlaceTransformation,
    PlaceTransformationEvent, ReferentialAssertion,
)
from .bibliography import source_by_title

CAL = CalibrationTable.CN_ASTRONOMICAL_ALMANAC


def _ry(era, title, n, verbatim, ganzhi=None):
    """文献纪年表达（「文献怎么写的」），不做换算——换算挂 DatePoint.gregorian"""
    return ReignYear(era=era, reign_title=title, year_within_reign=n,
                     ganzhi=ganzhi, verbatim=verbatim)


def _dt(y, tag, reign=None, precision="year"):
    return DatePoint(id=tag, label=str(y), precision=precision, reign_year=reign,
                     gregorian=GregorianDate(year=y, calibration=CAL))


def _ts(y1, y2, tag):
    return TimeSpan(id=tag, label="%d-%d" % (y1, y2),
                    begin=_dt(y1, tag + "_b"), end=_dt(y2, tag + "_e"))


# ==================================================================
# 1. 文献与篇卷（一律取自统一书目表，一书一条）
# ==================================================================

SOURCES: List[HistoricalSource] = [
    source_by_title("钦定日下旧闻考"),
    source_by_title("啸亭杂录"),
    source_by_title("天咫偶闻"),
    source_by_title("竹叶亭杂记"),
    source_by_title("清史稿"),
    source_by_title("海淀区人民政府公开史地沿革资料"),
    # ---- E13 中关村 ----
    source_by_title("汉书"),
    source_by_title("京西图（1913）"),
]

DIVISIONS: List[SourceDivision] = [
    # ---- E12 苏州街 ----
    SourceDivision(id="div_rxjwkc77_changhe", source_id="src_rxjwkc",
                   volume_number="卷77",
                   section_title="国朝苑囿·长河乐善园（万寿街按语·倚虹堂·万寿寺碑文）"),
    SourceDivision(id="div_xtzl10_suzhoujie", source_id="src_xiaoting_zalu",
                   volume_number="卷十", section_title="苏州街条"),
    SourceDivision(id="div_tzow9_jiaodiong", source_id="src_tianzhi_ouwen",
                   volume_number="卷九", section_title="郊坰（西直门外·万寿寺条）"),
    SourceDivision(id="div_zyztj1_tongleyuan", source_id="src_zyztj",
                   volume_number="卷一", section_title="圆明园同乐园买卖街条"),
    SourceDivision(id="div_qsg214_houfei", source_id="src_qingshigao",
                   volume_number="卷214", section_title="后妃（崇庆皇太后）"),
    SourceDivision(id="div_hdgov_yiheyuan", source_id="src_hd_gov_open",
                   volume_number="公开园史", section_title="颐和园（清漪园）沿革页"),
    # ---- E13 中关村 ----
    SourceDivision(id="div_hanshu_gaohouji", source_id="src_hanshu",
                   volume_number="卷三", section_title="高后纪第三（高后八年春）"),
    SourceDivision(id="div_jingxitu_1913", source_id="src_1913_jingxitu",
                   volume_number="民国二年图幅",
                   section_title="中关村一带标注（记录式转录）"),
]


# ==================================================================
# 2. 文本事实（古籍为繁体逐字引文；机构资料为记录式陈述，分层不混）
# ==================================================================

FACTS: List[TextualFact] = [
    # ---- 日下旧闻考 卷77：官书记名＋俗称＋位置走向（全片最硬书证） ----
    TextualFact(
        id="tf_rxjwkc77_wanshoujie", division_id="div_rxjwkc77_changhe",
        verbatim_quote="又按萬壽寺之西路北設關門，內有長衢列肆，北達暢春園，"
                       "為萬壽街，居人稱為蘇州街。詳見苑囿門。",
        attested_string="萬壽街",
        source_year=_dt(1783, "dt_rxjwkc77",
                        _ry(Era.QING, "乾隆", 48, "乾隆四十八年")),
        translator_note="臣等谨按语（乾隆朝官修，1783 纂辑告竣）；"
                        "引文以四库本原书为准，维基文库仅作检索承载。",
    ),
    TextualFact(
        id="tf_rxjwkc77_yihongtang", division_id="div_rxjwkc77_changhe",
        verbatim_quote="乾隆十六年聖母皇太后六旬萬壽，自長河至高梁橋易輦進宮，"
                       "因建是堂。",
        attested_string="六旬萬壽",
        source_year=_dt(1783, "dt_rxjwkc77b",
                        _ry(Era.QING, "乾隆", 48, "乾隆四十八年")),
    ),
    TextualFact(
        id="tf_rxjwkc77_zaixiu", division_id="div_rxjwkc77_changhe",
        verbatim_quote="以聖節崇啟經壇於萬壽寺，爰敕內府丹堊即工，"
                       "視乾隆辛未例弗懈益虔。",
        attested_string="視乾隆辛未例",
        source_year=_dt(1783, "dt_rxjwkc77c",
                        _ry(Era.QING, "乾隆", 48, "乾隆四十八年")),
        translator_note="御制重修万寿寺碑文截称（七旬圣寿、崇启经坛于万寿寺）；"
                        "「视乾隆辛未例」钉死 1761 再修循 1751（辛未）成例，"
                        "两轮工程不得混为一轮。",
    ),
    TextualFact(
        id="tf_rxjwkc77_liangxiu", division_id="div_rxjwkc77_changhe",
        verbatim_quote="萬壽寺明萬曆五年建，乾隆十六年重修，二十六年再修。",
        attested_string="二十六年再修",
        source_year=_dt(1783, "dt_rxjwkc77d",
                        _ry(Era.QING, "乾隆", 48, "乾隆四十八年")),
        translator_note="万寿寺按语：两次大修年份一手钉死。",
    ),
    # ---- 啸亭杂录 卷十：营建年份（辛巳=1761）＋动机的一手清人笔记 ----
    TextualFact(
        id="tf_xtzl_1761", division_id="div_xtzl10_suzhoujie",
        verbatim_quote="乾隆辛巳，孝聖憲皇后七旬誕辰，純皇以后素喜江南風景，"
                       "以年邁不宜遠行，因於萬壽寺旁造屋，仿江南式樣。"
                       "市廛坊巷，無不畢具，長至數里，以奉鑾輿往來遊行，"
                       "俗名曰蘇州街云。",
        attested_string="蘇州街",
        source_year=_dt(1829, "dt_xtzl",
                        _ry(Era.QING, "道光", None, "道光年间"),
                        precision="approximate"),
        translator_note="维基文库卷十原文已核（2026-10-02）。「纯皇以后素喜江南风景」"
                        "之「后」指太后；「以奉銮舆往来游行」未提太监扮商贩。",
    ),
    # ---- 天咫偶闻 卷九：毁废口径两段（同卷相承） ----
    TextualFact(
        id="tf_tzow_wanshoujie", division_id="div_tzow9_jiaodiong",
        verbatim_quote="寺西城關為萬壽街，俗稱蘇州街。兩行列肆，全仿蘇州。"
                       "舊傳太后喜蘇州風景，建此仿之，今已毀盡。",
        attested_string="今已毀盡",
        source_year=_dt(1907, "dt_tzow",
                        _ry(Era.QING, "光绪", 33, "光绪三十三年")),
        translator_note="卷次考订：万寿街条经维基文库原文复核在卷九（郊坰）；"
                        "预置书目表 edition_note 作卷七系误记，本篇卷按原书纠正，"
                        "不得反改回卷七。「旧传」二字为清人自标传闻。",
    ),
    TextualFact(
        id="tf_tzow_lingluo", division_id="div_tzow9_jiaodiong",
        verbatim_quote="自庚申秋御園被毀，翠輦不來。湖上諸園及甸鎮長街，"
                       "日就零落。",
        attested_string="日就零落",
        source_year=_dt(1907, "dt_tzow2",
                        _ry(Era.QING, "光绪", 33, "光绪三十三年")),
        translator_note="庚申即咸丰十年（1860）；与「今已毁尽」同卷相承，"
                        "为「1860 遭劫后日渐零落」口径的一手清人记述。",
    ),
    # ---- 竹叶亭杂记 卷一：园内买卖街「内监开店」一手原书（E11 已核同书） ----
    TextualFact(
        id="tf_zyztj_neijian", division_id="div_zyztj1_tongleyuan",
        verbatim_quote="開店者俱以內監為之。其古玩等器，由崇文門監督先期於"
                       "外城各肆中採擇交入。",
        attested_string="內監",
        translator_note="同乐园买卖街（园内）宫市模式一手记载；"
                        "严禁把该模式移植给园外万寿街。",
    ),
    TextualFact(
        id="tf_zyztj_jiaqing", division_id="div_zyztj1_tongleyuan",
        verbatim_quote="嘉慶四年此例停止。",
        attested_string="嘉慶四年",
    ),
    # ---- 清史稿 卷214：后出史书降级记录（仅存档冲突，不作据） ----
    TextualFact(
        id="tf_qsg_nanxun", division_id="div_qsg214_houfei",
        verbatim_quote="上每出巡幸，輒奉太后以行，南巡者三。",
        attested_string="南巡者三",
        source_year=_dt(1927, "dt_qsg", precision="approximate"),
        translator_note="《清史稿》1914 设馆、1927 匆促刊印，民国官修降级旁证："
                        "「南巡者三」与故宫博物院资料（至少前四次随行）冲突，"
                        "徽号首字「崇德」与乾隆朝碑文「崇庆」冲突——"
                        "巡幸次数、徽号、年份均不单独作据。",
    ),
    # ---- 海淀政府公开园史（记录式陈述，与古籍引文分层） ----
    TextualFact(
        id="tf_hdgov_shisi", division_id="div_hdgov_yiheyuan",
        verbatim_quote="清漪园建筑一百零一处，市肆共两处：西所买卖街、后溪河买卖街。",
        attested_string="后溪河买卖街",
        translator_note="记录式转录（官方网载园史，非古籍引文），不得与古籍互冒。",
    ),
    TextualFact(
        id="tf_hdgov_1860", division_id="div_hdgov_yiheyuan",
        verbatim_quote="咸丰十年（1860）九月英法联军进犯，十月五日占海淀镇、"
                       "六日占圆明园，劫掠焚毁诸园。",
        attested_string="劫掠焚毁",
        translator_note="记录式转录：1860 直录焚毁仅及园苑；万寿街自身无直接军事记录。",
    ),
    # ---- 汉书 卷三 高后纪：「中官」= 宦官的正典词源 ----
    TextualFact(
        id="tf_hanshu_zhongguan", division_id="div_hanshu_gaohouji",
        verbatim_quote="八年春，封中謁者張釋卿為列侯。諸中官、宦者令、丞皆賜爵"
                       "關內侯，食邑。",
        attested_string="諸中官",
        translator_note="卷次考订：交付档案 v2 与预置书目表均记作《高帝纪》，"
                        "经核原书实出《高后纪第三》高后八年（前180）春；"
                        "「中官」指宦官的词源结论不变，卷次按原书纠正。"
                        "点校本断句作「宦者令、丞」。",
    ),
    # ---- 京西图 1913：「中关」雅化在先的实测图证 ----
    TextualFact(
        id="tf_jingxitu_1913", division_id="div_jingxitu_1913",
        verbatim_quote="1913年（民国二年）北洋政府内务部测绘局实测印制二万五千分之一"
                       "《京西图》，中关村一带聚落位置已标注「中关」；清末民初测绘图上"
                       "「中关」雅化写法零星出现。",
        attested_string="中关",
        source_year=_dt(1913, "dt_jingxitu",
                        _ry(Era.REPUBLIC, "民国", 2, "民国二年")),
        translator_note="记录式转录：实测地图标注无逐字文本可引，此为档案内容的转写；"
                        "与古籍引文分层，不得互冒。",
    ),
]


# ==================================================================
# 3. 实体
# ==================================================================

ENTITIES: List[PersistentSpatialEntity] = [
    # ---- E12 ----
    PersistentSpatialEntity(id="ent_wanshoujie",
                            kind=PhysicalThingKind.SETTLEMENT_AREA,
                            canonical_label="万寿街（俗称苏州街）"),
    PersistentSpatialEntity(id="ent_tongleyuan_jie",
                            kind=PhysicalThingKind.SETTLEMENT_AREA,
                            canonical_label="圆明园同乐园买卖街"),
    PersistentSpatialEntity(id="ent_houxihe_jie",
                            kind=PhysicalThingKind.SETTLEMENT_AREA,
                            canonical_label="清漪园后溪河买卖街（今颐和园苏州街）"),
    # ---- E13 ----
    PersistentSpatialEntity(id="ent_zhongguancun",
                            kind=PhysicalThingKind.SETTLEMENT_AREA,
                            canonical_label="中关村（明清中官村）"),
]


# ==================================================================
# 4. 历时状态
# ==================================================================

STATES: List[HistoricalFeatureState] = [
    # ---- 万寿街：1761 辛巳营建至 1859（1860 年不设状态，见功能栏口径） ----
    HistoricalFeatureState(
        id="st_wsj_1761", entity_id="ent_wanshoujie",
        time_span=TimeSpan(id="ts_wsj_a", label="1761-1859 辛巳建街至庚申前夜",
                           begin=_dt(1761, "ts_wsj_ab",
                                     _ry(Era.QING, "乾隆", 26, "乾隆二十六年辛巳",
                                         ganzhi="辛巳")),
                           end=_dt(1859, "ts_wsj_ae")),
        geometry="万寿寺西路北设关门，门内长衢列肆，北达畅春园；"
                 "仿江南市廛坊巷，长至数里",
        function="真买卖的皇家街市（居人称为苏州街）：屋是真屋、买卖是真买卖，"
                 "亦带布景性质；为圣母七旬圣寿与銮舆往来游观而设；"
                 "「太监宫女扮商贩」属园内买卖街（见 ent_tongleyuan_jie），"
                 "严禁移植给本街；运转状态止于1859——1860（庚申）当年本街"
                 "无直接记录，不设1860年状态",
        evidence_fact_ids=["tf_rxjwkc77_wanshoujie", "tf_xtzl_1761"],
    ),
    HistoricalFeatureState(
        id="st_wsj_lingluo", entity_id="ent_wanshoujie",
        time_span=_ts(1861, 1907, "ts_wsj_b"),
        geometry="两行列肆的市街渐次零落倾颓",
        function="庚申(1860)御园被毁、翠辇不来，街市日渐零落；"
                 "晚清《天咫偶闻》记「今已毁尽」（毁废口径：渐变零落有清人记述，"
                 "本街直接焚毁记录缺——1860年状态阙如，焚毁直说无状态支撑）",
        evidence_fact_ids=["tf_tzow_wanshoujie", "tf_tzow_lingluo",
                           "tf_hdgov_1860"],
    ),
    # ---- 同乐园买卖街：园内宫市（「太监扮商贩」模式的唯一归属） ----
    HistoricalFeatureState(
        id="st_tly_qianlong", entity_id="ent_tongleyuan_jie",
        time_span=TimeSpan(id="ts_tly_a", label="乾隆年间-1799 园内宫市买卖街",
                           begin=_dt(1736, "ts_tly_ab",
                                     _ry(Era.QING, "乾隆", None, "乾隆年间"),
                                     precision="approximate"),
                           end=_dt(1799, "ts_tly_ae",
                                   _ry(Era.QING, "嘉庆", 4, "嘉庆四年"))),
        geometry="同乐园旁仿民间街市的园内市肆店铺",
        function="园内买卖街宫市：「开店者俱以内监为之」，古玩等器由崇文门监督"
                 "先期采择交入，走堂挑外城肆中声音响亮者充之；"
                 "「太监扮商贩」模式属此（园子里），不属于园外万寿街；"
                 "嘉庆四年此例停止",
        evidence_fact_ids=["tf_zyztj_neijian", "tf_zyztj_jiaqing"],
    ),
    # ---- 后溪河买卖街：清漪园市肆两处之一，1860 有园史直录焚毁 ----
    HistoricalFeatureState(
        id="st_hxh_qing", entity_id="ent_houxihe_jie",
        time_span=TimeSpan(id="ts_hxh_a", label="清漪园时期-1860 市肆水街",
                           open_begin=True, begin=None,
                           end=_dt(1860, "ts_hxh_ae",
                                   _ry(Era.QING, "咸丰", 10, "咸丰十年庚申",
                                       ganzhi="庚申"))),
        geometry="两街夹一河的水街形式（缩微布景性质，与万寿街真实尺度成对照；"
                 "具体尺寸诸说不入状态层，见命题层）",
        function="清漪园市肆两处之一（西所买卖街、后溪河买卖街）；"
                 "咸丰十年(1860)英法联军劫掠焚毁诸园，市肆同罹其难——"
                 "本主体1860焚毁有园史直录，与万寿街（无直接焚毁记录）严禁混同",
        evidence_fact_ids=["tf_hdgov_shisi", "tf_hdgov_1860"],
    ),
    # ---- 中关村：明清义地时期 ----
    HistoricalFeatureState(
        id="st_zgc_yidi", entity_id="ent_zhongguancun",
        time_span=TimeSpan(id="ts_zgc_a", label="明清-1912 太监义地时期",
                           begin=_dt(1368, "ts_zgc_ab",
                                     _ry(Era.MING, None, None, "明清两代"),
                                     precision="approximate"),
                           end=_dt(1912, "ts_zgc_ae")),
        geometry="中官坟义地散布于今中关村一带（非整村皆坟）",
        function="明清年老出宫太监置义地（公共墓地）作身后葬地：富裕太监置地、"
                 "贫困太监聚居守墓；民间称「中官村／中官坟／中官屯」"
                 "（「中官」即宦官，词源见《汉书·高后纪》；一手方志缺，"
                 "民间称谓＋刚秉庙实体＋侯仁之故道考证三角支撑，见命题层）",
        evidence_fact_ids=["tf_hanshu_zhongguan"],
    ),
    HistoricalFeatureState(
        id="st_zgc_1913", entity_id="ent_zhongguancun",
        time_span=_ts(1913, 1952, "ts_zgc_b"),
        geometry="1913年《京西图》实测图上聚落位置标注作「中关」",
        function="清末民初测绘图「中关」雅化写法零星出现（地图雅化≠改名）；"
                 "1950年代初官方档案与当地习惯写法仍作「中官村／中官邨」；"
                 "本状态止于1952——1950年代中科院入驻与机构定名属回忆录/院史"
                 "层级，见命题层（不入状态层）",
        evidence_fact_ids=["tf_jingxitu_1913"],
    ),
]


# ==================================================================
# 5. 身份断言
# ==================================================================

IDENTITIES: List[DiachronicIdentityAssertion] = [
    # 【E13 核心】中官村→中关村是同一聚落的两步改名，不是 1953 凭空新造
    DiachronicIdentityAssertion(
        id="dia_zgc_name_continuity",
        subject_entity_ids=["ent_zhongguancun"],
        relation=IdentityRelation.SAME_CONTINUANT,
        time_span=_ts(1368, 2026, "ts_dia_zgc"),
        evidence_fact_ids=["tf_hanshu_zhongguan", "tf_jingxitu_1913"],
        status=EpistemicStatus.VERIFIED,
        alternative_relations=[
            "「中关村」1953年一次性改名说（不成立）：1913年《京西图》已见「中关」，"
            "雅化在先，机构定名只是第二步",
            "中官坟范围辨析：坟地散布于今中关村一带，非整村皆坟",
        ],
    ),
]


# ==================================================================
# 6. 名称与指称
# ==================================================================

APPELLATIONS: List[Appellation] = [
    # ---- E12 ----
    Appellation(id="app_wanshoujie", label="万寿街", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1761, 1907, "ts_app_ws"),
                attesting_fact_ids=["tf_rxjwkc77_wanshoujie",
                                    "tf_tzow_wanshoujie"]),
    Appellation(id="app_suzhoujie", label="苏州街", kind=AppellationKind.VULGAR,
                valid_time_span=_ts(1761, 1907, "ts_app_szj"),
                attesting_fact_ids=["tf_rxjwkc77_wanshoujie", "tf_xtzl_1761"]),
    Appellation(id="app_tly", label="同乐园买卖街", kind=AppellationKind.OFFICIAL,
                valid_time_span=TimeSpan(id="ts_app_tly",
                                         label="乾隆年间-嘉庆四年",
                                         begin=_dt(1736, "ts_app_tly_b",
                                                   _ry(Era.QING, "乾隆", None,
                                                       "乾隆年间"),
                                                   precision="approximate"),
                                         end=_dt(1799, "ts_app_tly_e")),
                attesting_fact_ids=["tf_zyztj_neijian"]),
    Appellation(id="app_hxh", label="后溪河买卖街", kind=AppellationKind.OFFICIAL,
                valid_time_span=TimeSpan(id="ts_app_hxh", label="清漪园时期-1860",
                                         open_begin=True, begin=None,
                                         end=_dt(1860, "ts_app_hxh_e")),
                attesting_fact_ids=["tf_hdgov_shisi"]),
    Appellation(id="app_hxh_now", label="颐和园苏州街", kind=AppellationKind.OFFICIAL,
                valid_time_span=TimeSpan(id="ts_app_hxn", label="沿用至今",
                                         open_begin=True, begin=None,
                                         open_end=True, end=None),
                attesting_fact_ids=[]),
    # ---- E13 ----
    Appellation(id="app_zhongguan_cun", label="中官村", kind=AppellationKind.VULGAR,
                script_variants=["中官坟", "中官屯", "中官邨"],
                valid_time_span=TimeSpan(id="ts_app_zgc0", label="明清-1950年代初",
                                         open_begin=True, begin=None,
                                         end=_dt(1952, "ts_app_zgc0_e")),
                attesting_fact_ids=[]),
    Appellation(id="app_zhongguan", label="中关", kind=AppellationKind.EUPHEMISTIC,
                valid_time_span=_ts(1913, 1952, "ts_app_zgc1"),
                attesting_fact_ids=["tf_jingxitu_1913"]),
    Appellation(id="app_zgc", label="中关村", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1953, 2026, "ts_app_zgc2"),
                attesting_fact_ids=[]),
]

REFERENCES: List[ReferentialAssertion] = [
    # ---- E12：A（万寿街）与 B（后溪河）两个对象、四组名称，各指其一 ----
    ReferentialAssertion(id="rr_wanshoujie", appellation_id="app_wanshoujie",
                         referent_entity_id="ent_wanshoujie",
                         time_span=_ts(1761, 1907, "ts_rr_ws"),
                         evidence_fact_ids=["tf_rxjwkc77_wanshoujie"]),
    ReferentialAssertion(id="rr_suzhoujie", appellation_id="app_suzhoujie",
                         referent_entity_id="ent_wanshoujie",
                         time_span=_ts(1761, 1907, "ts_rr_szj"),
                         evidence_fact_ids=["tf_rxjwkc77_wanshoujie",
                                            "tf_xtzl_1761"],
                         provenance="官书按语「居人称为苏州街」＋昭梿「俗名曰苏州街」"
                                    "双重书证；今路名/站名承续此俗称"
                                    "（线位不等同，见命题层）"),
    ReferentialAssertion(id="rr_tly", appellation_id="app_tly",
                         referent_entity_id="ent_tongleyuan_jie",
                         time_span=TimeSpan(id="ts_rr_tly", label="乾隆年间-1799",
                                            begin=_dt(1736, "ts_rr_tly_b",
                                                      _ry(Era.QING, "乾隆", None,
                                                          "乾隆年间"),
                                                      precision="approximate"),
                                            end=_dt(1799, "ts_rr_tly_e")),
                         evidence_fact_ids=["tf_zyztj_neijian"]),
    ReferentialAssertion(id="rr_hxh", appellation_id="app_hxh",
                         referent_entity_id="ent_houxihe_jie",
                         time_span=TimeSpan(id="ts_rr_hxh", label="清漪园时期-1860",
                                            open_begin=True, begin=None,
                                            end=_dt(1860, "ts_rr_hxh_e")),
                         evidence_fact_ids=["tf_hdgov_shisi"]),
    ReferentialAssertion(id="rr_hxh_now", appellation_id="app_hxh_now",
                         referent_entity_id="ent_houxihe_jie",
                         time_span=TimeSpan(id="ts_rr_hxn", label="沿用至今",
                                            open_begin=True, begin=None,
                                            open_end=True, end=None),
                         evidence_fact_ids=["tf_hdgov_shisi"],
                         provenance="今颐和园景点名，与前身清漪园后溪河买卖街同地延续；"
                                    "与 A 主体（万寿寺旁万寿街）是两个对象，"
                                    "同场出现必须限定词"),
    # ---- E13：三段名称分层 ----
    ReferentialAssertion(id="rr_zhongguan_cun", appellation_id="app_zhongguan_cun",
                         referent_entity_id="ent_zhongguancun",
                         time_span=TimeSpan(id="ts_rr_zgc0", label="明清-1950年代初",
                                            open_begin=True, begin=None,
                                            end=_dt(1952, "ts_rr_zgc0_e")),
                         evidence_fact_ids=[],
                         status=EpistemicStatus.UNSUBSTANTIATED,
                         provenance="民间称谓层：明清太监义地聚落俗称；一手方志缺"
                                    "（不引《宛署杂记》），以民间称谓＋刚秉庙实体"
                                    "＋侯仁之故道考证三角支撑；《汉书》「中官」词源"
                                    "只证语义，不直证书名"),
    ReferentialAssertion(id="rr_zhongguan", appellation_id="app_zhongguan",
                         referent_entity_id="ent_zhongguancun",
                         time_span=_ts(1913, 1952, "ts_rr_zgc1"),
                         evidence_fact_ids=["tf_jingxitu_1913"]),
    ReferentialAssertion(id="rr_zgc", appellation_id="app_zgc",
                         referent_entity_id="ent_zhongguancun",
                         time_span=_ts(1953, 2026, "ts_rr_zgc2"),
                         evidence_fact_ids=[],
                         status=EpistemicStatus.UNSUBSTANTIATED,
                         provenance="1950年代机构定名（1953 信笺误植＝当事人回忆，"
                                    "口述史料，见命题层）；今日用名属实，"
                                    "但本库无一手书证——缺证据≠通过"),
]


# ==================================================================
# 7. 空间变化事件
# ==================================================================

TRANSFORMATIONS: List[PlaceTransformation] = [
    PlaceTransformation(
        id="pte_wsj_1761_built", entity_id="ent_wanshoujie",
        transformation=PlaceTransformationEvent.CONSTRUCTED,
        time_span=_ts(1761, 1761, "ts_pte_ws1"),
        resulting_state_id="st_wsj_1761",
        resulting_condition="乾隆辛巳(1761)圣母七旬诞辰之年，万寿寺旁仿江南造屋，"
                            "市廛坊巷毕具，长至数里（「营建于」优于「某日落成」）",
        evidence_fact_ids=["tf_xtzl_1761"],
    ),
    PlaceTransformation(
        id="pte_wsj_lingluo", entity_id="ent_wanshoujie",
        transformation=PlaceTransformationEvent.DAMAGED,
        time_span=_ts(1860, 1907, "ts_pte_ws2"),
        resulting_state_id="st_wsj_lingluo",
        resulting_condition="庚申(1860)御园被毁、翠辇不来，街市日渐零落，"
                            "晚清记「今已毁尽」（渐变毁废有清人记述，"
                            "直接焚毁记录缺）",
        evidence_fact_ids=["tf_tzow_lingluo", "tf_tzow_wanshoujie"],
    ),
    PlaceTransformation(
        id="pte_tly_1799_stop", entity_id="ent_tongleyuan_jie",
        transformation=PlaceTransformationEvent.ABANDONED,
        time_span=_ts(1799, 1799, "ts_pte_tly"),
        resulting_condition="嘉庆四年此例停止（内监扮装宫市模式终止）",
        evidence_fact_ids=["tf_zyztj_jiaqing"],
    ),
    PlaceTransformation(
        id="pte_hxh_1860_burned", entity_id="ent_houxihe_jie",
        transformation=PlaceTransformationEvent.DAMAGED,
        time_span=_ts(1860, 1860, "ts_pte_hxh"),
        resulting_condition="咸丰十年(1860)九月英法联军进犯，十月劫掠焚毁诸园，"
                            "后溪河市肆同罹其难（园史直录；与万寿街的无直录"
                            "形成对照）",
        evidence_fact_ids=["tf_hdgov_1860"],
    ),
]


# ==================================================================
# 8. 断言与采信：把交付档案的降格结论固化
# ==================================================================

PROPOSITIONS: List[Proposition] = [
    # ---- E12 ----
    Proposition(
        id="prop_wsj_zhenmaimai",
        statement="万寿街是真买卖的皇家街市（也带布景性质）：屋是真屋、买卖是真买卖，"
                  "为圣母七旬圣寿与銮舆往来游观而设；「太监宫女扮商贩」属园内买卖街"
                  "（同乐园等），严禁移植给万寿街",
        derived_from_fact_ids=["tf_xtzl_1761", "tf_zyztj_neijian",
                               "tf_rxjwkc77_wanshoujie"],
        inferred_subject_id="ent_wanshoujie",
        inference_method="贾珺《圆明园买卖街钩沉》「真正的商业街，尽管也带有一定的"
                         "布景性质」；《啸亭杂录》只言「以奉銮舆往来游行」；"
                         "《竹叶亭杂记》内监开店属同乐园（园内）——对象限定",
        alternative_explanations=[
            "北京旅游网等串台源把后溪河/万寿山后描述与万寿寺—畅春园连续空间混同——"
            "凡此判疑似混同源，不采用",
        ],
    ),
    Proposition(
        id="prop_tly_neijian_yuannei",
        statement="「太监宫女扮商贩」的宫市模式一手记载属园内买卖街：同乐园买卖街"
                  "「开店者俱以内监为之」（姚元之《竹叶亭杂记》卷一），嘉庆四年停止——"
                  "对照层可讲园内买卖街，但每次必须限定「园子里」",
        derived_from_fact_ids=["tf_zyztj_neijian", "tf_zyztj_jiaqing"],
        inferred_subject_id="ent_tongleyuan_jie",
        inference_method="一手原书（E11 已核同书）；王致诚书札所记扮装戏码亦属园内",
        alternative_explanations=[],
    ),
    Proposition(
        id="prop_shuangwanshou",
        statement="长河沿线两轮万寿工程不得混为一轮：乾隆十六年辛未（1751）六旬"
                  "（倚虹堂、万寿寺一修、五塔寺一修）与乾隆二十六年辛巳（1761）七旬"
                  "（万寿寺再修、五塔寺再修、万寿街营建）分属两轮",
        derived_from_fact_ids=["tf_rxjwkc77_yihongtang", "tf_rxjwkc77_zaixiu",
                               "tf_rxjwkc77_liangxiu", "tf_xtzl_1761"],
        inferred_subject_id="ent_wanshoujie",
        inference_method="卷77 碑文与按语互证；辛未=1751 由御制诗自注自证，"
                         "辛巳必为 1761（七旬）——干支凡涉及必回原文自证",
        alternative_explanations=[
            "干支误配说：检索中曾见 AI 摘要把「辛巳」错配乾隆十六年（1751）——已证伪",
        ],
    ),
    Proposition(
        id="prop_jiancheng_1761",
        statement="万寿街营建年份口径：昭梿《啸亭杂录》卷十记营建于乾隆辛巳（1761）"
                  "七旬万寿之年（「营建于」优于「某日落成」）；「二十七年异说」未核到"
                  "书名卷次，不采用",
        derived_from_fact_ids=["tf_xtzl_1761"],
        inferred_subject_id="ent_wanshoujie",
        inference_method="清人笔记系年，维基文库卷十原文已核",
        alternative_explanations=[
            "「有史料记为二十七年」：未核到原文，v2 已删除此异说",
        ],
    ),
    Proposition(
        id="prop_huifei_koujing",
        statement="毁废口径：庚申（1860）西郊园苑遭劫、翠辇不来，街市日渐零落；"
                  "晚清《天咫偶闻》卷九记「今已毁尽」——万寿街自身无直接军事记录，"
                  "不得直说其 1860 年被英法联军一把火烧毁",
        derived_from_fact_ids=["tf_tzow_wanshoujie", "tf_tzow_lingluo",
                               "tf_hdgov_1860"],
        inferred_subject_id="ent_wanshoujie",
        inference_method="《天咫偶闻》卷九同卷相承两段（庚申御园被毁→日就零落→"
                         "今已毁尽）；1860 直录焚毁仅及园苑",
        alternative_explanations=[
            "万寿街直接军事焚毁记录缺：毁废是渐变过程，非一次性焚毁",
        ],
    ),
    Proposition(
        id="prop_ab_distinct",
        statement="万寿寺旁万寿街（俗称苏州街，北达畅春园）与清漪园后溪河买卖街"
                  "（今颐和园「苏州街」景点）是两个对象：A 为真买卖的皇家街市、"
                  "毁后未复建；B 为缩微布景水街、1860 有焚毁直录——同场出现必须限定词",
        derived_from_fact_ids=["tf_rxjwkc77_wanshoujie", "tf_hdgov_shisi",
                               "tf_hdgov_1860"],
        inferred_subject_id="ent_wanshoujie",
        inference_method="官书按语与园史市肆条分指两地；贾珺文明确分列京西诸买卖街",
        alternative_explanations=[
            "二手混同源：凡同时描述「后溪河」与「万寿寺—畅春园」连续空间者，"
            "判疑似串台，不采用",
        ],
    ),
    Proposition(
        id="prop_name_lives",
        statement="街废名存：清代万寿街的俗称「苏州街」今仍用作海淀城市道路名与"
                  "地铁站名（10号线＋16号线2023-12-30换乘），但今路名承续的是历史地名，"
                  "线位不等同清代原线",
        derived_from_fact_ids=["tf_tzow_wanshoujie"],
        inferred_subject_id="ent_wanshoujie",
        inference_method="今貌（百科/北京市交通委，未入库）；GIS 叠图前不谈「走廊」",
        alternative_explanations=[
            "「今路即清代原线」说：不成立，线位不等同",
        ],
    ),
    Proposition(
        id="prop_qsg_downgrade",
        statement="《清史稿》为后出史书（1914 设馆、1927 匆促刊印）：徽号首字作"
                  "「崇德」与乾隆朝碑文「崇庆」冲突、南巡作「三次」与故宫资料"
                  "（至少前四次随行）冲突——巡幸次数、徽号、年份均不单独作据",
        derived_from_fact_ids=["tf_qsg_nanxun"],
        inferred_subject_id=None,
        inference_method="民国官修降级旁证；乾隆朝文献优先（卷77 碑文作"
                         "「崇庆慈宣康惠敦和裕寿」）",
        alternative_explanations=[
            "《清史稿》卷214 原文照录存档，仅作冲突记录",
        ],
    ),
    # ---- E13 ----
    Proposition(
        id="prop_zgc_yidi",
        statement="中关村明清时期为太监义地与聚居点，民间称中官村／中官坟／中官屯"
                  "（「中官」即宦官）；义地散布一带，非整村皆坟",
        derived_from_fact_ids=["tf_hanshu_zhongguan"],
        inferred_subject_id="ent_zhongguancun",
        inference_method="《汉书·高后纪》词源＋民间称谓＋刚秉庙实体地望"
                         "（今北大物理楼北侧）＋侯仁之永定河故道「中湾儿」考证，"
                         "三角支撑；一手方志缺，不引《宛署杂记》",
        alternative_explanations=[
            "「中湾儿」水湾地貌参与命名一说（侯仁之一系考证：地处永定河故道，"
            "地势低洼有水湾）",
            "中官坟范围辨析：坟地散布于今中关村一带，非整个街区皆坟",
        ],
    ),
    Proposition(
        id="prop_zgc_two_step",
        statement="「中关」写法不是 1953 年凭空创造：1913 年《京西图》已零星出现；"
                  "改名是「清末民初地图雅化＋1950 年代机构定名」两步走",
        derived_from_fact_ids=["tf_jingxitu_1913"],
        inferred_subject_id="ent_zhongguancun",
        inference_method="实测地图标注直接证据；1950 年代初官方档案与当地习惯写法"
                         "仍作「中官村／中官邨」",
        alternative_explanations=[
            "1953 年一次性改名说（不成立）：与 1913 年图证冲突",
        ],
    ),
    Proposition(
        id="prop_zgc_1953_wuzhi",
        statement="1953 年「中关村」定名的主流叙事为信笺误植说：中科院《中华地理志》"
                  "编辑部自南京迁京，经办人（袁保诚）只闻读音未见文字，将「中官村」"
                  "写成「中关村」，印错信封将错就错沿用——属当事人回忆（口述史料），"
                  "须挂出处，不得作「史载」",
        derived_from_fact_ids=["tf_jingxitu_1913"],
        inferred_subject_id="ent_zhongguancun",
        inference_method="中科院老同志丘宝剑等回忆（《中国科学院院报》2009 纪念文、"
                         "科学网 2009）；回忆录证级；时值三反五反，纸张金贵反对浪费",
        alternative_explanations=[
            "陈垣（或汤用彤）提议雅化说：流传广但无一手文献支撑，"
            "且无法解释 1913 年地图已有「中关」",
        ],
    ),
    Proposition(
        id="prop_zgc_chenyuan",
        statement="「北平时期陈垣提议改中关」旧说不得作定论：无一手文献，"
                  "且 1913 年《京西图》已有「中关」——降级为「一说」级传说",
        derived_from_fact_ids=["tf_jingxitu_1913"],
        inferred_subject_id="ent_zhongguancun",
        inference_method="以 1913 图证检核旧说时间线；人物表 person_chenyuan 条"
                          "本注存疑",
        alternative_explanations=[
            "信笺误植说（当事人回忆，口述史料层级）",
        ],
    ),
    Proposition(
        id="prop_zgc_kecheng",
        statement="1950 年代起中科院入驻中关村：1951 征地建科研基地（近北大清华）、"
                  "1953《中华地理志》编辑部迁京、1954 科源社区特楼与近代物理所进驻"
                  "（钱三强、何泽慧等，郭沫若题字）——本库无一手书证，不入状态层，"
                  "口播须挂官方院史出处",
        derived_from_fact_ids=["tf_jingxitu_1913"],
        inferred_subject_id="ent_zhongguancun",
        inference_method="官方院史（未入库）；本命题仅登记口径，状态层止于 1952",
        alternative_explanations=[],
    ),
]

ADOPTIONS: List[BeliefAdoption] = [
    BeliefAdoption(proposition_id="prop_wsj_zhenmaimai",
                   status=EpistemicStatus.VERIFIED, confidence=0.9,
                   adopted_by="E12交付档案v2（suzhoujie_video/research.md冻结）",
                   rationale="贾珺文＋《啸亭杂录》＋《竹叶亭杂记》对象限定三重支撑；"
                             "v2 复查第 1 条拦下的对象混同硬伤"),
    BeliefAdoption(proposition_id="prop_tly_neijian_yuannei",
                   status=EpistemicStatus.VERIFIED, confidence=0.9,
                   adopted_by="E12交付档案v2（suzhoujie_video/research.md冻结）",
                   rationale="一手原书；对照层每次限定「园子里」"),
    BeliefAdoption(proposition_id="prop_shuangwanshou",
                   status=EpistemicStatus.VERIFIED, confidence=0.9,
                   adopted_by="E12交付档案v2（suzhoujie_video/research.md冻结）",
                   rationale="卷77 碑文按语互证；辛未/辛巳干支原文自证"),
    BeliefAdoption(proposition_id="prop_jiancheng_1761",
                   status=EpistemicStatus.VERIFIED, confidence=0.85,
                   adopted_by="E12交付档案v2（suzhoujie_video/research.md冻结）",
                   rationale="清人笔记一手系年；二十七年异说未核到原文，不采用"),
    BeliefAdoption(proposition_id="prop_huifei_koujing",
                   status=EpistemicStatus.VERIFIED, confidence=0.85,
                   adopted_by="E12交付档案v2（suzhoujie_video/research.md冻结）",
                   rationale="《天咫偶闻》卷九一手清末记述；直接焚毁记录缺，"
                             "毁废按渐变口径表达"),
    BeliefAdoption(proposition_id="prop_ab_distinct",
                   status=EpistemicStatus.VERIFIED, confidence=0.9,
                   adopted_by="E12交付档案v2（suzhoujie_video/research.md冻结）",
                   rationale="官书与园史分指两地；A/B 混同是本集最大对象陷阱"),
    BeliefAdoption(proposition_id="prop_name_lives",
                   status=EpistemicStatus.VERIFIED, confidence=0.8,
                   adopted_by="E12交付档案v2（suzhoujie_video/research.md冻结）",
                   rationale="今名承续属实；线位不等同清代原线"),
    BeliefAdoption(proposition_id="prop_qsg_downgrade",
                   status=EpistemicStatus.CONTESTED, confidence=0.5,
                   adopted_by="E12交付档案v2（suzhoujie_video/research.md冻结）",
                   rationale="《清史稿》与故宫资料/乾隆朝碑文两处冲突，"
                             "降级旁证不单独作据"),
    BeliefAdoption(proposition_id="prop_zgc_yidi",
                   status=EpistemicStatus.CONTESTED, confidence=0.65,
                   adopted_by="E13交付档案v2（zhongguancun_video/research.md冻结）",
                   rationale="义地说为学界主流叙事，但一手方志缺——"
                             "三角支撑（民间称谓＋刚秉庙＋侯仁之）成立而证级有限"),
    BeliefAdoption(proposition_id="prop_zgc_two_step",
                   status=EpistemicStatus.VERIFIED, confidence=0.9,
                   adopted_by="E13交付档案v2（zhongguancun_video/research.md冻结）",
                   rationale="1913 实测图为直接书证；两步走是唯一能同时解释"
                             "图证与 1950 年代档案的口径"),
    BeliefAdoption(proposition_id="prop_zgc_1953_wuzhi",
                   status=EpistemicStatus.CONTESTED, confidence=0.6,
                   adopted_by="E13交付档案v2（zhongguancun_video/research.md冻结）",
                   rationale="当事人回忆为口述史料，非「史载」；与陈垣说并存，"
                             "前者证级更高"),
    BeliefAdoption(proposition_id="prop_zgc_chenyuan",
                   status=EpistemicStatus.UNSUBSTANTIATED, confidence=0.3,
                   adopted_by="E13交付档案v2（zhongguancun_video/research.md冻结）",
                   rationale="无一手文献；且 1913 图证在其时间线上难以安放——"
                             "registry 旧条「北平时期陈垣提议改中关」不成立"),
    BeliefAdoption(proposition_id="prop_zgc_kecheng",
                   status=EpistemicStatus.VERIFIED, confidence=0.7,
                   adopted_by="E13交付档案v2（zhongguancun_video/research.md冻结）",
                   rationale="官方院史口径可信但未入库；只登记口径不设状态，"
                             "口播挂出处"),
]


# ==================================================================
# 9. 空间集合
# ==================================================================

AGGREGATES: List[PlaceAggregate] = []
