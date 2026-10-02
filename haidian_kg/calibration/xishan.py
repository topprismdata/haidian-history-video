"""
haidian_kg/calibration/xishan.py
西山一线词条（大觉寺·碧云寺·温泉·凤凰岭·北安河·金山）—— holdout run3 覆盖缺口批次

研究底稿唯一来源：docs/kg/research/xishan.md（古文原文已逐字落盘，在线源只作检索裁决）。
本批六个词条全部是 run3 KB 覆盖缺口 FP（清水院/大觉寺/碧云寺/温泉/凤凰岭/北安河/金山
真实地名未建词条），入库后吃掉 P 低的主因面。

证据分级映射（绝不混级）：
  [一手实物]   辽咸雍四年《旸台山清水院创造藏经记》碑（今存大觉寺）、碧云寺金刚宝座塔
               —— 器物本体；建年口径另有说明时两层分开
  [文献记载]   《日下旧闻考》卷100/卷106（转引《长安客话》《嘉靖祀典》《明典彙》
               《帝京景物略》《明英宗实录》——转引一律挂日下旧闻考篇卷并在
               translator_note 标转引，不另建书目条目）；《帝京景物略》卷六碧云寺条直取
  [现代记录]   文保批次/开放现状/景区定位挂机构公开资料（记录式陈述，与古籍引文分层）
  [存疑待考]   碧云寺创建者名字写法、龙泉寺始建年代、温泉庙、北安河得名、玉兰年代
               —— 全部落 Proposition + CONTESTED/UNSUBSTANTIATED 采信
  [民间传说]   金山「一溜边山七十二府」俗呼——四库本无此句原典，纯俗谚层

红线落位：
  - 大觉寺「始建」以辽碑为下限：辽代已成清水院，金章宗八院是明人追述，绝不倒置
  - 碧云寺：元碑年（至顺二年1331）≠改寺年（正德十一年1516）≠重饰年（天启三年1623），
    三年分属三个状态
  - 金山按 Main 纠偏口径：明代妃嫔皇子葬地总名（正统间起葬有官书支撑），金陵在房山
    已排除；与 settlements 模块 ent_jinshan 用跨模块同指断言挂钩，不重复建模
  - 北安河：村名官书首见乾隆朝；「金章宗行宫在北安河」式混说由审计负控制阻断
  - 「至今仍在使用/开放」类现状全部单独核查并挂机构口径，不与史实混写
"""
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
    HistoricalFeatureState, IdentityRelation, PlaceAggregate,
    PersistentSpatialEntity, PhysicalThingKind, PlaceTransformation,
    PlaceTransformationEvent, ReferentialAssertion,
)
from .bibliography import source_by_title

CAL = CalibrationTable.CN_ASTRONOMICAL_ALMANAC


def _ry(era, title, n, verbatim, month=None):
    return ReignYear(era=era, reign_title=title, year_within_reign=n,
                     lunar_month=month, verbatim=verbatim)


def _dt(y, tag, reign=None, precision="year"):
    return DatePoint(id=tag, label=str(y), precision=precision, reign_year=reign,
                     gregorian=GregorianDate(year=y, calibration=CAL))


def _ts(y1, y2, tag):
    return TimeSpan(id=tag, label="%d-%d" % (y1, y2),
                    begin=_dt(y1, tag + "_b"), end=_dt(y2, tag + "_e"))


def _open(end_year, tag, end_reign=None):
    """开放起始区间（成村年代无考等）：begin=None，绝不伪造 DatePoint"""
    return TimeSpan(id=tag, label="早期-" + str(end_year), open_begin=True,
                    begin=None, end=_dt(end_year, tag + "_e", end_reign))


# ==================================================================
# 1. 文献与篇卷（一律取自统一书目表，一书一条）
# ==================================================================

SOURCES: List[HistoricalSource] = [
    source_by_title("钦定日下旧闻考"),
    source_by_title("帝京景物略"),
    source_by_title("长安客话"),
    source_by_title("北京市文物局公开文保资料"),
    source_by_title("海淀区人民政府公开史地沿革资料"),
]

DIVISIONS: List[SourceDivision] = [
    # 日下旧闻考卷106 郊坰西十六：大觉寺条 / 香水院条 / 画眉山温泉条 / 百望山按语
    SourceDivision(id="div_xs_rxjwkc106_dajuesi", source_id="src_rxjwkc",
                   volume_number="卷106",
                   section_title="郊坰西十六·大觉寺条（含旸台山清水院创造藏经记、"
                                 "乾隆御制重修碑、按语）"),
    SourceDivision(id="div_xs_rxjwkc106_xiangshuiyuan", source_id="src_rxjwkc",
                   volume_number="卷106",
                   section_title="郊坰西十六·法云寺香水院条（转引帝京景物略）"),
    SourceDivision(id="div_xs_rxjwkc106_huameishan", source_id="src_rxjwkc",
                   volume_number="卷106",
                   section_title="郊坰西十六·画眉山温泉条（转引帝京景物略）"),
    SourceDivision(id="div_xs_rxjwkc106_beianhe", source_id="src_rxjwkc",
                   volume_number="卷106",
                   section_title="郊坰西十六·百望山条按语（安河与南安河北安河诸村）"),
    # 日下旧闻考卷100 郊坰西十：金山妃嫔葬地 / 景泰陵（转引长安客话、嘉靖祀典、明典彙）
    SourceDivision(id="div_xs_rxjwkc100_jinshan", source_id="src_rxjwkc",
                   volume_number="卷100",
                   section_title="郊坰西十·金山妃嫔皇子葬地条（转引长安客话、"
                                 "明嘉靖祀典、明典彙）"),
    # 帝京景物略卷六西山上·碧云寺条（直取非转引）
    SourceDivision(id="div_xs_djjwl6_biyunsi", source_id="src_dijingjingwulue",
                   volume_number="卷六",
                   section_title="西山上·碧云寺条"),
    # 现代机构资料（记录式陈述，与古籍引文分层）
    SourceDivision(id="div_xs_wjbz_dajuesi", source_id="src_wjbz_open",
                   volume_number="文保名录", section_title="大觉寺（第六批全国重点）"),
    SourceDivision(id="div_xs_wjbz_biyunsi", source_id="src_wjbz_open",
                   volume_number="文保名录", section_title="碧云寺（第五批全国重点）"),
    SourceDivision(id="div_xs_wjbz_jingtailing", source_id="src_wjbz_open",
                   volume_number="文保名录", section_title="景泰陵（第五批全国重点）"),
    SourceDivision(id="div_xs_hdgov_fenghuangling", source_id="src_hd_gov_open",
                   volume_number="景区沿革", section_title="凤凰岭自然风景区与龙泉寺"),
    SourceDivision(id="div_xs_hdgov_wenquan", source_id="src_hd_gov_open",
                   volume_number="区划沿革", section_title="温泉镇温泉村现行区划"),
]


# ==================================================================
# 2. 文本事实（古籍为逐字引文，繁体照录；机构资料为记录式陈述，分层不混）
# ==================================================================

FACTS: List[TextualFact] = [
    # ---- 大觉寺：辽碑（器物本体一手；此处为日下旧闻考卷106转录，碑今存寺内） ----
    TextualFact(
        id="tf_xs_liaobei_zhuanji", division_id="div_xs_rxjwkc106_dajuesi",
        verbatim_quote="旸台山者蓟壤之名峰清水院者幽都之胜概",
        attested_string="清水院",
        source_year=_dt(1068, "dt_xs_lb",
                        _ry(Era.LIAO_JIN, "咸雍", 4, "咸雍四年三月"))),
    TextualFact(
        id="tf_xs_liaobei_yinzang", division_id="div_xs_rxjwkc106_dajuesi",
        verbatim_quote="舍钱三十万葺诸僧舍又五十万募同志印大藏经凡五百七十九帙"
                       "创内外藏而龛措之",
        attested_string="五百七十九帙",
        source_year=_dt(1068, "dt_xs_lb2",
                        _ry(Era.LIAO_JIN, "咸雍", 4, "咸雍四年三月")),
        translator_note="碑文系卷106转录；碑今存大觉寺内为一手实物（器物层见 "
                        "ent_xs_liaobei），本库不另建碑刻书目条目"),
    TextualFact(
        id="tf_xs_liaobei_guanshu", division_id="div_xs_rxjwkc106_dajuesi",
        verbatim_quote="寺内龙王堂辽碑一僧志延撰咸雍四年立",
        attested_string="辽碑",
        source_year=_dt(1747, "dt_xs_lb3",
                        _ry(Era.QING, "乾隆", 12, "乾隆十二年"))),
    # ---- 大觉寺：宣德改名 / 金章宗八院（帝京景物略，卷106转引） ----
    TextualFact(
        id="tf_xs_xuande_gengming", division_id="div_xs_rxjwkc106_dajuesi",
        verbatim_quote="黑龙潭北十五里曰大觉寺宣德三年建寺故名灵泉宣宗易以今名",
        attested_string="大觉寺",
        source_year=_dt(1428, "dt_xs_xd",
                        _ry(Era.MING, "宣德", 3, "宣德三年")),
        translator_note="转引《帝京景物略》卷五大觉寺条（原书卷次,GPT审2-2核）；宿主挂日下旧闻考卷106"),
    TextualFact(
        id="tf_xs_jinzhangzong_bayuan", division_id="div_xs_rxjwkc106_dajuesi",
        verbatim_quote="金章宗西山八院寺其清水院也",
        attested_string="清水院",
        source_year=_dt(1190, "dt_xs_bayuan",
                        _ry(Era.LIAO_JIN, "明昌", 1, "明昌元年"),
                        precision="approximate"),
        translator_note="「西山八院」为明人追述语（帝京景物略），非金代自述；"
                        "金章宗朝起年取明昌元年近似"),
    # ---- 大觉寺：正统修 / 康熙修葺 / 乾隆发帑重修 / 无量寿佛殿 / 四宜堂 ----
    TextualFact(
        id="tf_xs_zhengtong_xiu", division_id="div_xs_rxjwkc106_dajuesi",
        verbatim_quote="正统十一年三月命工部右侍郎王祐督工修大觉寺",
        attested_string="大觉寺",
        source_year=_dt(1446, "dt_xs_zt",
                        _ry(Era.MING, "正统", 11, "正统十一年三月")),
        translator_note="转引《明英宗实录》卷139·正统十一年三月（原书卷次,GPT审2-1核）；宿主挂日下旧闻考卷106"),
    TextualFact(
        id="tf_xs_kangxi_qianlong_xiu", division_id="div_xs_rxjwkc106_dajuesi",
        verbatim_quote="大觉寺康熙五十九年世宗潜邸时特加修葺乾隆十二年皇上发帑重修",
        attested_string="大觉寺",
        source_year=_dt(1747, "dt_xs_ql",
                        _ry(Era.QING, "乾隆", 12, "乾隆十二年"))),
    TextualFact(
        id="tf_xs_wuliangshoufo", division_id="div_xs_rxjwkc106_dajuesi",
        verbatim_quote="无量寿佛殿额曰动静等观",
        attested_string="无量寿佛殿",
        source_year=_dt(1747, "dt_xs_wlsf",
                        _ry(Era.QING, "乾隆", 12, "乾隆十二年"))),
    TextualFact(
        id="tf_xs_siyitang", division_id="div_xs_rxjwkc106_dajuesi",
        verbatim_quote="寺旁精舍内恭悬世宗御书额曰四宜堂",
        attested_string="四宜堂",
        source_year=_dt(1747, "dt_xs_syt",
                        _ry(Era.QING, "乾隆", 12, "乾隆十二年"))),
    TextualFact(
        id="tf_xs_qianlong_beiwen", division_id="div_xs_rxjwkc106_dajuesi",
        verbatim_quote="大觉寺者金清水院故址明以灵泉寺更名",
        attested_string="清水院",
        source_year=_dt(1747, "dt_xs_qlbw",
                        _ry(Era.QING, "乾隆", 12, "乾隆十二年"))),
    # ---- 大觉寺：现状（现代机构记录式，单独核查层） ----
    TextualFact(
        id="tf_xs_djs_xianzhuang", division_id="div_xs_wjbz_dajuesi",
        verbatim_quote="大觉寺（今通称西山大觉寺）于2006年5月25日列入第六批"
                       "全国重点文物保护单位，现为对外开放的文物景区",
        attested_string="西山大觉寺",
        translator_note="机构公开资料记录式陈述，非古籍引文；批次与开放现状为"
                        "文保官网现行口径（2026-10 核查）"),
    # ---- 碧云寺：帝京景物略卷六直取（元碑/耶阿利吉/正德改寺/天启重饰） ----
    TextualFact(
        id="tf_xs_bys_yuanbei", division_id="div_xs_djjwl6_biyunsi",
        verbatim_quote="寺二元碑：一至順二年立，一元統三年立。白石黑章，"
                       "碑俚不文，而石文也以存。",
        attested_string="至順二年",
        source_year=_dt(1331, "dt_xs_bys1",
                        _ry(Era.YUAN, "至顺", 2, "至顺二年"))),
    TextualFact(
        id="tf_xs_bys_yealiji", division_id="div_xs_djjwl6_biyunsi",
        verbatim_quote="碧雲，庵于元耶阿利吉。",
        attested_string="耶阿利吉",
        source_year=_dt(1331, "dt_xs_bys2",
                        _ry(Era.YUAN, "至顺", 2, "至顺二年")),
        translator_note="《帝京景物略》只记创建者名「耶阿利吉」，未言世系；"
                        "今论著或作耶律阿利吉、耶律阿勒锡并系为耶律楚材后人，"
                        "写法与世系诸书不一——存疑待考（见命题层）"),
    TextualFact(
        id="tf_xs_bys_zhengde", division_id="div_xs_djjwl6_biyunsi",
        verbatim_quote="寺于正德十一年，飾于天啟三年，土之人亦曰「于公寺云」。",
        attested_string="正德十一年",
        source_year=_dt(1516, "dt_xs_bys3",
                        _ry(Era.MING, "正德", 11, "正德十一年"))),
    # ---- 碧云寺：金刚宝座塔/孙中山/现状（现代机构记录式，分层） ----
    TextualFact(
        id="tf_xs_bys_jingangta", division_id="div_xs_wjbz_biyunsi",
        verbatim_quote="碧云寺金刚宝座塔建于清乾隆十三年（1748），仿佛陀伽耶"
                       "精舍制式，为寺后最高建筑；塔今存（一手实物）。",
        attested_string="金刚宝座塔",
        source_year=_dt(1748, "dt_xs_bys4",
                        _ry(Era.QING, "乾隆", 13, "乾隆十三年")),
        translator_note="建年为现代机构通行口径（文保名录/景区资料多源一致），"
                        "非清代档案逐字引文；塔本体为一手实物"),
    TextualFact(
        id="tf_xs_bys_sunzhongshan", division_id="div_xs_wjbz_biyunsi",
        verbatim_quote="1925年4月2日孙中山灵柩暂厝碧云寺金刚宝座塔石券门内，"
                       "1929年5月敛服南下奉安南京中山陵后，衣冠封存塔内，"
                       "是为孙中山衣冠冢；停灵处普明妙觉殿后改建孙中山纪念堂。",
        attested_string="衣冠冢",
        source_year=_dt(1925, "dt_xs_bys5")),
    TextualFact(
        id="tf_xs_bys_xianzhuang", division_id="div_xs_wjbz_biyunsi",
        verbatim_quote="碧云寺于2001年6月25日列入第五批全国重点文物保护单位；"
                       "2023年11月起实施封闭保护修缮，2024年9月26日恢复开放。",
        attested_string="碧云寺",
        source_year=_dt(2001, "dt_xs_bys6"),
        translator_note="机构公开资料记录式陈述；开放现状为 2026-10 核查口径"),
    # ---- 温泉：泉眼（帝京景物略，卷106转引）+ 乾隆朝区划 + 现行区划 ----
    TextualFact(
        id="tf_xs_wq_quanyan", division_id="div_xs_rxjwkc106_huameishan",
        verbatim_quote="画眉山在西堂村之北产石黑色浮质而腻理入金宫为眉石"
                       "山北十里有温泉出焉",
        attested_string="温泉",
        translator_note="转引《帝京景物略》画眉山条；泉眼所在即今海淀温泉村一带，"
                        "成村年代无考"),
    TextualFact(
        id="tf_xs_wq_changping", division_id="div_xs_rxjwkc106_huameishan",
        verbatim_quote="画眉山北温泉今隶昌平州境",
        attested_string="昌平州境",
        source_year=_dt(1782, "dt_xs_wq2",
                        _ry(Era.QING, "乾隆", 47, "乾隆四十七年"))),
    TextualFact(
        id="tf_xs_wq_guishu", division_id="div_xs_hdgov_wenquan",
        verbatim_quote="温泉村今属北京市海淀区温泉镇。",
        attested_string="温泉镇",
        translator_note="机构公开资料记录式陈述，非古籍引文"),
    # ---- 凤凰岭/龙泉寺（现代机构记录式；山名与始建均存疑层） ----
    TextualFact(
        id="tf_xs_fhl_jingqu", division_id="div_xs_hdgov_fenghuangling",
        verbatim_quote="凤凰岭今为凤凰岭自然风景区，于20世纪90年代中期开发开放；"
                       "「凤凰岭」作为山体通称的明清文献记载未见确证。",
        attested_string="凤凰岭",
        source_year=_dt(1996, "dt_xs_fhl", precision="approximate"),
        translator_note="现代旅游景区定位是现代观点，非历史建置"),
    TextualFact(
        id="tf_xs_fhl_longquansi", division_id="div_xs_hdgov_fenghuangling",
        verbatim_quote="龙泉寺在凤凰岭山麓，景区与今志通行说法称其始建于辽代"
                       "应历初年（约951年），无早期纪年碑刻确证；现列为海淀区"
                       "文物保护单位，2005年恢复为宗教活动场所。",
        attested_string="龙泉寺",
        translator_note="通行说法是现代机构口径，不是辽代书证；始建年代存疑"
                        "（见命题层）"),
    TextualFact(
        id="tf_xs_fhl_feilaita", division_id="div_xs_hdgov_fenghuangling",
        verbatim_quote="飞来石塔原塔相传建于清光绪二年（1876），现塔为1998年"
                       "依原样重建。",
        attested_string="飞来石塔",
        translator_note="原塔建年系相传口径；现塔为现代重建物，不得当辽金古塔"),
    # ---- 北安河：官书首见 ----
    TextualFact(
        id="tf_xs_bah_cun", division_id="div_xs_rxjwkc106_beianhe",
        verbatim_quote="长乐河即安河其地有南安河北安河长乐诸村",
        attested_string="北安河",
        source_year=_dt(1782, "dt_xs_bah",
                        _ry(Era.QING, "乾隆", 47, "乾隆四十七年"))),
    # ---- 金山：明代妃嫔皇子葬地（卷100转引三条） ----
    TextualFact(
        id="tf_xs_js_jingtailin", division_id="div_xs_rxjwkc100_jinshan",
        verbatim_quote="景皇帝陵在金山口距西山不十里陵前坎窞树多白杨及樗"
                       "凡诸王公主夭殇者并葬金山口其与景皇陵相属又诸妃亦多葬此",
        attested_string="金山口",
        translator_note="转引《长安客话》；转引不另建书目条目"),
    TextualFact(
        id="tf_xs_js_feipin", division_id="div_xs_rxjwkc100_jinshan",
        verbatim_quote="仁宗诸妃俱陪葬献陵惟三妃别葬金山宣宗诸妃俱陪葬景陵"
                       "惟一妃别葬金山睿皇后钱氏合葬裕陵诸妃一葬绵山余葬金山"
                       "宪庙废后吴氏坟葬金山",
        attested_string="金山",
        translator_note="转引《明嘉靖祀典》；「妃嫔不入天寿山」制度系现代制度史归纳(从祀典个案体例推出,官书无明文条款——GPT审3-3)"
                        "即见此条体例"),
    TextualFact(
        id="tf_xs_js_wubei", division_id="div_xs_rxjwkc100_jinshan",
        verbatim_quote="宪庙十三妃始同为一墓嘉靖十三年以古世妇御妻皆九宜九妃"
                       "为一墓同一享殿内作七室两厢于是金山预造五墓各九数"
                       "以次葬焉",
        attested_string="金山",
        source_year=_dt(1534, "dt_xs_js",
                        _ry(Era.MING, "嘉靖", 13, "嘉靖十三年")),
        translator_note="转引《明典彙》"),
    TextualFact(
        id="tf_xs_js_huangzi", division_id="div_xs_rxjwkc100_jinshan",
        verbatim_quote="皇子葬金山者怀宪世子悼恭太子哀冲太子越靖王秀怀王",
        attested_string="悼恭太子",
        translator_note="转引《明嘉靖祀典》"),
    # ---- 金山：现状（现代机构记录式） ----
    TextualFact(
        id="tf_xs_js_jtl_xianzhuang", division_id="div_xs_wjbz_jingtailing",
        verbatim_quote="景泰陵（金山口）于2001年6月25日列入第五批全国重点"
                       "文物保护单位；金山南麓现划定「金山地下文物埋藏区」，周边另有"
                       "万安公墓、金山陵园等现代墓园（地面建筑毁废程度未经逐墓调查，"
                       "不作比例性判断——GPT审3-4）。",
        attested_string="景泰陵",
        source_year=_dt(2001, "dt_xs_js2"),
        translator_note="机构公开资料记录式陈述；现状单独核查层"),
]


# ==================================================================
# 3. 实体（只承载身份，形制全部下沉到状态）
# ==================================================================

ENTITIES: List[PersistentSpatialEntity] = [
    PersistentSpatialEntity(id="ent_xs_dajuesi",
                            kind=PhysicalThingKind.RELIGIOUS_PRECINCT,
                            canonical_label="大觉寺（旸台山麓，辽清水院故址）"),
    PersistentSpatialEntity(id="ent_xs_liaobei",
                            kind=PhysicalThingKind.HUMAN_MADE_ARTIFACT,
                            canonical_label="旸台山清水院创造藏经记碑（辽咸雍四年）"),
    PersistentSpatialEntity(id="ent_xs_biyunsi",
                            kind=PhysicalThingKind.RELIGIOUS_PRECINCT,
                            canonical_label="碧云寺（香山万安山东麓）"),
    PersistentSpatialEntity(id="ent_xs_jingangta",
                            kind=PhysicalThingKind.HUMAN_MADE_ARTIFACT,
                            canonical_label="碧云寺金刚宝座塔（清乾隆十三年）"),
    PersistentSpatialEntity(id="ent_xs_wenquan",
                            kind=PhysicalThingKind.SETTLEMENT_AREA,
                            canonical_label="温泉村"),
    # GPT审3-2：泉眼/村/镇三实体分立（明清书证对象=泉眼地望；村=聚落；
    # 镇=现代政区），无连续地名档案不建 sameAs——见 prop_xs_wenquan_split
    PersistentSpatialEntity(id="ent_xs_wq_quanyan",
                            kind=PhysicalThingKind.NATURAL_SPRING,
                            canonical_label="温泉（画眉山北泉眼）"),
    PersistentSpatialEntity(id="ent_xs_wenquanzhen",
                            kind=PhysicalThingKind.ADMIN_DIVISION,
                            canonical_label="温泉镇（海淀区，现代政区）"),
    PersistentSpatialEntity(id="ent_xs_fenghuangling",
                            kind=PhysicalThingKind.MOUNTAIN,
                            canonical_label="凤凰岭（西山山体）"),
    # GPT审3-17：山体地望与景区经营实体二分，1996 开园只挂景区——见 prop_xs_fhl_split
    PersistentSpatialEntity(id="ent_xs_fhl_jingqu",
                            kind=PhysicalThingKind.SCENIC_AREA,
                            canonical_label="凤凰岭自然风景区"),
    PersistentSpatialEntity(id="ent_xs_longquansi",
                            kind=PhysicalThingKind.RELIGIOUS_PRECINCT,
                            canonical_label="龙泉寺（凤凰岭山麓）"),
    PersistentSpatialEntity(id="ent_xs_beianhe",
                            kind=PhysicalThingKind.SETTLEMENT_AREA,
                            canonical_label="北安河村"),
    PersistentSpatialEntity(id="ent_xs_jinshan",
                            kind=PhysicalThingKind.TOMB_CLUSTER,
                            canonical_label="金山（明代妃嫔皇子葬地总名）"),
]


# ==================================================================
# 4. 历时状态（G5：同实体各状态起始年互异；开放起始用 begin=None）
# ==================================================================

STATES: List[HistoricalFeatureState] = [
    # ---- 大觉寺 ----
    HistoricalFeatureState(
        id="st_xs_djs_liao", entity_id="ent_xs_dajuesi",
        time_span=_ts(1068, 1189, "ts_xs_djs_a"),
        geometry="旸台山麓，依山而建；院内有泉（「坐西朝东」系现存建筑测绘层描述,辽代格局无考古/图志依据,不挂辽碑——GPT审3-1）",
        function="辽代清水院：信士邓从贵等舍钱葺僧舍、印大藏经五百七十九帙"
                 "创内外藏龛措之（寺之前身，建置下限以辽碑为准）",
        evidence_fact_ids=["tf_xs_liaobei_zhuanji", "tf_xs_liaobei_yinzang",
                           "tf_xs_liaobei_guanshu"]),
    HistoricalFeatureState(
        id="st_xs_djs_jin", entity_id="ent_xs_dajuesi",
        time_span=_ts(1190, 1214, "ts_xs_djs_b"),
        geometry="同前；旸台山麓水院",
        function="金章宗西山八院之一（「寺其清水院也」为明人追述，"
                 "非金代自述——见命题层八院归附说）",
        evidence_fact_ids=["tf_xs_jinzhangzong_bayuan"]),
    HistoricalFeatureState(
        id="st_xs_djs_lingquan", entity_id="ent_xs_dajuesi",
        time_span=_ts(1215, 1427, "ts_xs_djs_c"),
        geometry="金元易代之际一度荒败；宣德重建前旧基",
        function="金末至明初沿革无详载；重建时旧名灵泉（寺），旋易今名",
        evidence_fact_ids=["tf_xs_xuande_gengming", "tf_xs_qianlong_beiwen"]),
    HistoricalFeatureState(
        id="st_xs_djs_xuande", entity_id="ent_xs_dajuesi",
        time_span=_ts(1428, 1445, "ts_xs_djs_d"),
        geometry="宣德三年重建落成，宣宗赐易今名",
        function="明宣德重建更名大觉寺之皇家梵刹（改名年；非建寺始年）",
        evidence_fact_ids=["tf_xs_xuande_gengming"]),
    HistoricalFeatureState(
        id="st_xs_djs_zhengtong", entity_id="ent_xs_dajuesi",
        time_span=_ts(1446, 1719, "ts_xs_djs_e"),
        geometry="正统十一年三月敕工部右侍郎王祐督工修缮",
        function="明代沿用之大觉寺（正统敕修后）",
        evidence_fact_ids=["tf_xs_zhengtong_xiu"]),
    HistoricalFeatureState(
        id="st_xs_djs_yongzheng", entity_id="ent_xs_dajuesi",
        time_span=_ts(1720, 1746, "ts_xs_djs_f"),
        geometry="康熙五十九年世宗潜邸时特加修葺；增四宜堂，"
                 "僧性音奉旨住持，寺旁有性音塔",
        function="雍正潜邸檀越寺（皇家护持，增修非初建）",
        evidence_fact_ids=["tf_xs_kangxi_qianlong_xiu", "tf_xs_siyitang",
                           "tf_xs_qianlong_beiwen"]),
    HistoricalFeatureState(
        id="st_xs_djs_qianlong", entity_id="ent_xs_dajuesi",
        time_span=_ts(1747, 2005, "ts_xs_djs_g"),
        geometry="乾隆十二年发帑重修：弥勒殿额圆证妙果、正殿额无去来处、"
                 "无量寿佛殿额动静等观、大悲坛额最上法门，皆御书；"
                 "殿前碑阳刊世宗御制诗、碑阴刊乾隆御制文",
        function="乾隆朝重修后的皇家寺院（无量寿佛殿为中路主殿之一，"
                 "「动静等观」额即此殿）；金清水院故址的官方定性见乾隆御制碑",
        evidence_fact_ids=["tf_xs_kangxi_qianlong_xiu", "tf_xs_wuliangshoufo",
                           "tf_xs_siyitang", "tf_xs_qianlong_beiwen"]),
    HistoricalFeatureState(
        id="st_xs_djs_2006", entity_id="ent_xs_dajuesi",
        time_span=_ts(2006, 2026, "ts_xs_djs_h"),
        geometry="寺址今存；四宜堂白玉兰为寺内名物（植栽年代俗传辽植/清植"
                 "诸说分歧，无文献与树木档案确证——存疑不列年代）",
        function="第六批全国重点文物保护单位（2006-05-25公布），"
                 "今对外开放的文物景区（现状2026-10单独核查）",
        evidence_fact_ids=["tf_xs_djs_xianzhuang"]),
    # ---- 辽碑（器物本体） ----
    HistoricalFeatureState(
        id="st_xs_lb_1068", entity_id="ent_xs_liaobei",
        time_span=_ts(1068, 2026, "ts_xs_lb"),
        geometry="石碑一通，寺内龙王堂处；志延撰文，咸雍四年岁次戊申"
                 "三月癸酉朔四日丙子记",
        material="石质碑刻（今存原石）",
        function="旸台山清水院创造藏经记：记邓从贵等葺舍印藏五百七十九帙事；"
                 "大觉寺辽代已建清水院的一手实物证据",
        evidence_fact_ids=["tf_xs_liaobei_zhuanji", "tf_xs_liaobei_yinzang",
                           "tf_xs_liaobei_guanshu"]),
    # ---- 碧云寺 ----
    HistoricalFeatureState(
        id="st_xs_bys_yuan", entity_id="ent_xs_biyunsi",
        time_span=_ts(1331, 1515, "ts_xs_bys_a"),
        geometry="香山万安山东麓；元至顺二年、元统三年两碑立于寺（元碑原文记"
                 "「白石黑章，碑俚不文」）",
        function="元代碧云庵（创建者耶阿利吉，名字写法与世系存疑——见命题层）",
        evidence_fact_ids=["tf_xs_bys_yuanbei", "tf_xs_bys_yealiji"]),
    HistoricalFeatureState(
        id="st_xs_bys_zhengde", entity_id="ent_xs_biyunsi",
        time_span=_ts(1516, 1622, "ts_xs_bys_b"),
        geometry="正德十一年扩庵为寺，规制渐宏",
        function="改称碧云寺（于经扩建）；土人俗呼于公寺——改名年非建寺年",
        evidence_fact_ids=["tf_xs_bys_zhengde"]),
    HistoricalFeatureState(
        id="st_xs_bys_tianqi", entity_id="ent_xs_biyunsi",
        time_span=_ts(1623, 1747, "ts_xs_bys_c"),
        geometry="天启三年重饰，金碧交辉",
        function="明代名刹碧云寺（天启重饰年）",
        evidence_fact_ids=["tf_xs_bys_zhengde"]),
    HistoricalFeatureState(
        id="st_xs_bys_qianlong", entity_id="ent_xs_biyunsi",
        time_span=_ts(1748, 1911, "ts_xs_bys_d"),
        geometry="乾隆十三年增建金刚宝座塔于寺后（仿佛陀伽耶精舍制式）",
        function="清代扩建后的碧云寺（增建年为现代机构通行口径，塔本体一手实物）",
        evidence_fact_ids=["tf_xs_bys_jingangta"]),
    HistoricalFeatureState(
        id="st_xs_bys_1925", entity_id="ent_xs_biyunsi",
        time_span=_ts(1925, 1928, "ts_xs_bys_e"),
        geometry="孙中山灵柩暂厝金刚宝座塔石券门内；普明妙觉殿设灵堂",
        function="孙中山先生停灵之地（民国层事件，1925-04-02起）",
        evidence_fact_ids=["tf_xs_bys_sunzhongshan"]),
    HistoricalFeatureState(
        id="st_xs_bys_1929", entity_id="ent_xs_biyunsi",
        time_span=_ts(1929, 2000, "ts_xs_bys_f"),
        geometry="1929年5月敛服南奉后衣冠封存塔内为衣冠冢；"
                 "普明妙觉殿后改建孙中山纪念堂（宋庆龄题额，现代纪念性命名）",
        function="碧云寺与孙中山衣冠冢纪念地",
        evidence_fact_ids=["tf_xs_bys_sunzhongshan"]),
    HistoricalFeatureState(
        id="st_xs_bys_2001", entity_id="ent_xs_biyunsi",
        time_span=_ts(2001, 2023, "ts_xs_bys_g"),
        geometry="寺址今存，位于香山公园北部",
        function="第五批全国重点文物保护单位（2001-06-25公布）",
        evidence_fact_ids=["tf_xs_bys_xianzhuang"]),
    HistoricalFeatureState(
        id="st_xs_bys_2024", entity_id="ent_xs_biyunsi",
        time_span=_ts(2024, 2026, "ts_xs_bys_h"),
        geometry="2023年11月起封闭修缮，2024年9月26日恢复开放",
        function="修缮后正常对外开放的文物景区（现状2026-10单独核查）",
        evidence_fact_ids=["tf_xs_bys_xianzhuang"]),
    # ---- 金刚宝座塔（器物本体） ----
    HistoricalFeatureState(
        id="st_xs_jg_1748", entity_id="ent_xs_jingangta",
        time_span=_ts(1748, 2026, "ts_xs_jg"),
        geometry="寺后最高处汉白玉金刚宝座塔",
        material="汉白玉石构（今存原塔）",
        function="乾隆十三年建（建年为现代机构通行口径）；"
                 "1925-1929孙中山灵柩暂厝石券门，1929年后衣冠封存塔内",
        evidence_fact_ids=["tf_xs_bys_jingangta", "tf_xs_bys_sunzhongshan"]),
    # ---- 温泉 ----
    HistoricalFeatureState(
        id="st_xs_wq_ming", entity_id="ent_xs_wq_quanyan",
        time_span=_open(1643, "ts_xs_wq_a"),
        geometry="画眉山（西堂村之北，产眉石）北十里泉眼",
        function="明已有温泉泉眼记载（村名因泉得名）；泉温汤可浴",
        evidence_fact_ids=["tf_xs_wq_quanyan"]),
    HistoricalFeatureState(
        id="st_xs_wq_qing", entity_id="ent_xs_wq_quanyan",
        time_span=_ts(1644, 1911, "ts_xs_wq_b"),
        geometry="同前，泉眼如故",
        function="清代隶昌平州境（乾隆朝按语），非京县宛平辖",
        evidence_fact_ids=["tf_xs_wq_changping"]),
    HistoricalFeatureState(
        id="st_xs_wq_cun_1949", entity_id="ent_xs_wenquan",
        time_span=_ts(1949, 2026, "ts_xs_wq_c"),
        geometry="海淀区山后温泉镇治域内聚落（空间包含关系，见命题层）",
        function="温泉村今属北京市海淀区温泉镇；成村年代无考（村名因泉）",
        evidence_fact_ids=["tf_xs_wq_guishu"]),
    HistoricalFeatureState(
        id="st_xs_wq_zhen_now", entity_id="ent_xs_wenquanzhen",
        time_span=TimeSpan(id="ts_xs_wq_d", label="现行区划",
                           open_begin=True, begin=None,
                           end=_dt(2026, "ts_xs_wq_de")),
        geometry="北京市海淀区山后（治域边界以现行区划为准）",
        function="现代乡级行政区划（机构公开资料记录式陈述；置镇沿革年代"
                 "未核得一手档，不立置镇年代）",
        evidence_fact_ids=["tf_xs_wq_guishu"]),

    # ---- 凤凰岭 ----
    HistoricalFeatureState(
        id="st_xs_fhl_shanti", entity_id="ent_xs_fenghuangling",
        time_span=_open(1995, "ts_xs_fhl_a"),
        geometry="西山山体一段，山麓有龙泉寺等刹；山涧泉石自然地貌",
        function="自然山体；「凤凰岭」作为山名之明清文献记载未见确证（存疑）",
        evidence_fact_ids=["tf_xs_fhl_jingqu", "tf_xs_fhl_longquansi"]),
    HistoricalFeatureState(
        id="st_xs_fhl_jingqu", entity_id="ent_xs_fhl_jingqu",
        time_span=TimeSpan(id="ts_xs_fhl_b", label="1990年代中期-今",
                           begin=_dt(1996, "ts_xs_fhl_bb",
                                     precision="approximate"),
                           end=_dt(2026, "ts_xs_fhl_be")),
        geometry="凤凰岭自然风景区范围（北中南三线游径）",
        function="现代旅游景区（现代定位，非历史建置）；飞来石塔现塔为1998年"
                 "依原样重建之物",
        evidence_fact_ids=["tf_xs_fhl_jingqu", "tf_xs_fhl_feilaita"]),
    # ---- 龙泉寺 ----
    HistoricalFeatureState(
        id="st_xs_lqs_yuangu", entity_id="ent_xs_longquansi",
        time_span=_open(2004, "ts_xs_lqs_a"),
        geometry="凤凰岭山麓寺址；坐向与规制历代屡改",
        function="始建年代存疑：通行口径「辽应历初年（约951）僧继升创建」无早期"
                 "纪年碑刻确证；元至顺三年（1332）舍蓝蓝「于西山重修龙泉寺」"
                 "之记载是否即此寺亦存疑——均见命题层",
        evidence_fact_ids=["tf_xs_fhl_longquansi"]),
    HistoricalFeatureState(
        id="st_xs_lqs_2005", entity_id="ent_xs_longquansi",
        time_span=_ts(2005, 2026, "ts_xs_lqs_b"),
        geometry="修复后寺址",
        function="海淀区文物保护单位；2005年恢复为宗教活动场所（现代机构口径）",
        evidence_fact_ids=["tf_xs_fhl_longquansi"]),
    # ---- 北安河 ----
    HistoricalFeatureState(
        id="st_xs_bah_yuancun", entity_id="ent_xs_beianhe",
        time_span=_open(1781, "ts_xs_bah_a"),
        geometry="安河（长乐河）流域村落，与旸台山麓大觉寺相邻；"
                 "成村年代无考（得名词源存疑——见命题层）",
        function="山后村落（金代安和说与安河音转说皆无早期文证，"
                 "不立因果，不作沿革绑定）",
        evidence_fact_ids=["tf_xs_bah_cun"]),
    HistoricalFeatureState(
        id="st_xs_bah_1782", entity_id="ent_xs_beianhe",
        time_span=_ts(1782, 1911, "ts_xs_bah_b"),
        geometry="「长乐河即安河，其地有南安河、北安河、长乐诸村」——"
                 "与南安河、长乐并举",
        function="乾隆朝官书按语已载之村落（官书首见，成书乾隆四十七年）",
        evidence_fact_ids=["tf_xs_bah_cun"]),
    # ---- 金山（明代妃嫔皇子葬地总名） ----
    HistoricalFeatureState(
        id="st_xs_js_ming", entity_id="ent_xs_jinshan",
        time_span=_ts(1425, 1644, "ts_xs_js_a"),
        geometry="金山陵区：景皇帝陵在金山口，距西山不十里；"
                 "嘉靖十三年预造五墓各九数、同一享殿内作七室两厢；"
                 "娘娘府、董四墓等聚落与园寝在其域内（两实体由 settlements "
                 "模块建模，本条为陵区总名，非重复建模）",
        function="明代妃嫔皇子葬地：仁宗三妃、宣宗一妃别葬金山，英宗以降诸妃"
                 "多葬此，悼恭太子等皇子亦葬金山；「妃嫔不入天寿山」为现代制度史归纳(官书无明文——GPT审3-3)；"
                 "金代帝陵（金陵）在房山大房山，与本地无涉（见命题层）",
        evidence_fact_ids=["tf_xs_js_feipin", "tf_xs_js_jingtailin",
                           "tf_xs_js_wubei", "tf_xs_js_huangzi"]),
    HistoricalFeatureState(
        id="st_xs_js_1912", entity_id="ent_xs_jinshan",
        time_span=_ts(1912, 2026, "ts_xs_js_b"),
        geometry="地面建筑毁废状况未经逐墓调查；金山南麓划定地下文物埋藏区，周边另有万安公墓、金山陵园（GPT审3-4）；"
                 "景泰陵存",
        function="古葬区遗址；景泰陵2001年列第五批全国重点文物保护单位"
                 "（现状2026-10单独核查）",
        evidence_fact_ids=["tf_xs_js_jtl_xianzhuang"]),
]


# ==================================================================
# 5. 身份断言：跨模块同指（与 settlements 的 ent_jinshan）
# ==================================================================

IDENTITIES: List[DiachronicIdentityAssertion] = [
    DiachronicIdentityAssertion(
        id="dia_xs_jinshan_same_settlements",
        subject_entity_ids=["ent_xs_jinshan", "ent_jinshan"],
        relation=IdentityRelation.SAME_CONTINUANT,
        time_span=_ts(1425, 2026, "ts_xs_dia"),
        evidence_fact_ids=["tf_xs_js_feipin", "tf_xs_js_jingtailin"],
        status=EpistemicStatus.VERIFIED,
        alternative_relations=[
            "settlements 模块 ent_jinshan（金山明代皇家墓葬区）以 1951/2022-23 "
            "考古发掘与卷100 记录式陈述建模同一葬区；本模块以卷100 转引《长安客话》"
            "《嘉靖祀典》《明典彙》三条文献建模葬区总名——两实体同指金山葬区，"
            "本断言供 holdout collision 豁免与跨模块消歧",
        ],
    ),
]


# ==================================================================
# 6. 名称与指称
# ==================================================================

APPELLATIONS: List[Appellation] = [
    Appellation(id="app_xs_dajuesi", label="大觉寺", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1428, 2026, "ts_xs_n1"),
                attesting_fact_ids=["tf_xs_xuande_gengming",
                                    "tf_xs_kangxi_qianlong_xiu"]),
    Appellation(id="app_xs_qingshuiyuan", label="清水院",
                kind=AppellationKind.OLD_NAME,
                valid_time_span=_ts(1068, 1214, "ts_xs_n2"),
                attesting_fact_ids=["tf_xs_liaobei_zhuanji",
                                    "tf_xs_jinzhangzong_bayuan"]),
    Appellation(id="app_xs_lingquan", label="灵泉寺",
                kind=AppellationKind.OLD_NAME,
                valid_time_span=_ts(1428, 1428, "ts_xs_n3"),
                script_variants=["灵泉佛寺"],
                attesting_fact_ids=["tf_xs_xuande_gengming",
                                    "tf_xs_qianlong_beiwen"]),
    Appellation(id="app_xs_xishandajuesi", label="西山大觉寺",
                kind=AppellationKind.VULGAR,
                valid_time_span=_ts(1912, 2026, "ts_xs_n4"),
                attesting_fact_ids=["tf_xs_djs_xianzhuang"]),
    Appellation(id="app_xs_biyunsi", label="碧云寺",
                kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1516, 2026, "ts_xs_n5"),
                attesting_fact_ids=["tf_xs_bys_zhengde",
                                    "tf_xs_bys_xianzhuang"]),
    Appellation(id="app_xs_biyunan", label="碧云庵",
                kind=AppellationKind.OLD_NAME,
                valid_time_span=_ts(1331, 1516, "ts_xs_n6"),
                attesting_fact_ids=["tf_xs_bys_yealiji"]),
    Appellation(id="app_xs_yugongsi", label="于公寺",
                kind=AppellationKind.VULGAR,
                valid_time_span=_ts(1516, 1623, "ts_xs_n7"),
                attesting_fact_ids=["tf_xs_bys_zhengde"]),
    Appellation(id="app_xs_jingangta", label="金刚宝座塔",
                kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1748, 2026, "ts_xs_n8"),
                attesting_fact_ids=["tf_xs_bys_jingangta"]),
    Appellation(id="app_xs_wenquan", label="温泉", kind=AppellationKind.OFFICIAL,
                valid_time_span=TimeSpan(id="ts_xs_n9", label="明代-今",
                                         open_begin=True, begin=None,
                                         end=_dt(2026, "ts_xs_n9e")),
                attesting_fact_ids=["tf_xs_wq_quanyan", "tf_xs_wq_guishu"]),
    Appellation(id="app_xs_wenquancun", label="温泉村",
                kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1949, 2026, "ts_xs_n10"),
                attesting_fact_ids=["tf_xs_wq_guishu"]),
    Appellation(id="app_xs_wenquanzhen", label="温泉镇",
                kind=AppellationKind.OFFICIAL,
                valid_time_span=TimeSpan(id="ts_xs_n10b", label="现行-今",
                                         open_begin=True, begin=None,
                                         end=_dt(2026, "ts_xs_n10be")),
                attesting_fact_ids=["tf_xs_wq_guishu"]),
    Appellation(id="app_xs_fenghuangling", label="凤凰岭",
                kind=AppellationKind.OFFICIAL,
                valid_time_span=TimeSpan(id="ts_xs_n12", label="近现代-今",
                                         open_begin=True, begin=None,
                                         end=_dt(2026, "ts_xs_n12e")),
                attesting_fact_ids=["tf_xs_fhl_jingqu"]),
    Appellation(id="app_xs_fhl_jingqu", label="凤凰岭自然风景区",
                kind=AppellationKind.OFFICIAL,
                valid_time_span=TimeSpan(id="ts_xs_n12b", label="1990年代中期-今",
                                         open_begin=True, begin=None,
                                         end=_dt(2026, "ts_xs_n12be")),
                attesting_fact_ids=["tf_xs_fhl_jingqu"]),
    Appellation(id="app_xs_longquansi", label="龙泉寺",
                kind=AppellationKind.OFFICIAL,
                valid_time_span=TimeSpan(id="ts_xs_n13", label="传承至今",
                                         open_begin=True, begin=None,
                                         end=_dt(2026, "ts_xs_n13e")),
                attesting_fact_ids=["tf_xs_fhl_longquansi"]),
    Appellation(id="app_xs_beianhe", label="北安河",
                kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1782, 2026, "ts_xs_n14"),
                attesting_fact_ids=["tf_xs_bah_cun"]),
    Appellation(id="app_xs_jinshan", label="金山", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1425, 2026, "ts_xs_n15"),
                attesting_fact_ids=["tf_xs_js_feipin", "tf_xs_js_jingtailin"]),
    Appellation(id="app_xs_jinshankou", label="金山口",
                kind=AppellationKind.OLD_NAME,
                valid_time_span=_ts(1425, 2026, "ts_xs_n16"),
                attesting_fact_ids=["tf_xs_js_jingtailin",
                                    "tf_xs_js_jtl_xianzhuang"]),
    Appellation(id="app_xs_feipinyuan", label="妃嫔园",
                kind=AppellationKind.VULGAR,
                valid_time_span=_ts(1912, 2026, "ts_xs_n17"),
                attesting_fact_ids=["tf_xs_js_feipin"]),
]

REFERENCES: List[ReferentialAssertion] = [
    ReferentialAssertion(id="rr_xs_dajuesi", appellation_id="app_xs_dajuesi",
                         referent_entity_id="ent_xs_dajuesi",
                         time_span=_ts(1428, 2026, "ts_xs_r1"),
                         evidence_fact_ids=["tf_xs_xuande_gengming"]),
    ReferentialAssertion(id="rr_xs_qingshuiyuan",
                         appellation_id="app_xs_qingshuiyuan",
                         referent_entity_id="ent_xs_dajuesi",
                         time_span=_ts(1068, 1214, "ts_xs_r2"),
                         evidence_fact_ids=["tf_xs_liaobei_zhuanji",
                                            "tf_xs_jinzhangzong_bayuan"]),
    ReferentialAssertion(id="rr_xs_lingquan", appellation_id="app_xs_lingquan",
                         referent_entity_id="ent_xs_dajuesi",
                         time_span=_ts(1428, 1428, "ts_xs_r3"),
                         evidence_fact_ids=["tf_xs_xuande_gengming"]),
    ReferentialAssertion(id="rr_xs_xishandajuesi",
                         appellation_id="app_xs_xishandajuesi",
                         referent_entity_id="ent_xs_dajuesi",
                         time_span=_ts(1912, 2026, "ts_xs_r4"),
                         evidence_fact_ids=["tf_xs_djs_xianzhuang"]),
    ReferentialAssertion(id="rr_xs_biyunsi", appellation_id="app_xs_biyunsi",
                         referent_entity_id="ent_xs_biyunsi",
                         time_span=_ts(1516, 2026, "ts_xs_r5"),
                         evidence_fact_ids=["tf_xs_bys_zhengde"]),
    ReferentialAssertion(id="rr_xs_biyunan", appellation_id="app_xs_biyunan",
                         referent_entity_id="ent_xs_biyunsi",
                         time_span=_ts(1331, 1516, "ts_xs_r6"),
                         evidence_fact_ids=["tf_xs_bys_yealiji"]),
    ReferentialAssertion(id="rr_xs_yugongsi", appellation_id="app_xs_yugongsi",
                         referent_entity_id="ent_xs_biyunsi",
                         time_span=_ts(1516, 1623, "ts_xs_r7"),
                         evidence_fact_ids=["tf_xs_bys_zhengde"],
                         provenance="明人俗称（《帝京景物略》「土之人亦曰于公寺云」），"
                                    "因正德间太监于经扩寺而得俗名，非官称"),
    ReferentialAssertion(id="rr_xs_jingangta", appellation_id="app_xs_jingangta",
                         referent_entity_id="ent_xs_jingangta",
                         time_span=_ts(1748, 2026, "ts_xs_r8"),
                         evidence_fact_ids=["tf_xs_bys_jingangta"]),
    ReferentialAssertion(id="rr_xs_wenquan", appellation_id="app_xs_wenquan",
                         referent_entity_id="ent_xs_wq_quanyan",
                         time_span=TimeSpan(id="ts_xs_r9", label="明代-今",
                                            open_begin=True, begin=None,
                                            end=_dt(2026, "ts_xs_r9e")),
                         evidence_fact_ids=["tf_xs_wq_quanyan",
                                            "tf_xs_wq_changping"],
                         provenance="明清书证对象为泉眼/地望（GPT审3-2）："
                                    "「画眉山北十里有温泉出焉」「隶昌平州境」均指泉"),
    ReferentialAssertion(id="rr_xs_wenquancun",
                         appellation_id="app_xs_wenquancun",
                         referent_entity_id="ent_xs_wenquan",
                         time_span=_ts(1949, 2026, "ts_xs_r10"),
                         evidence_fact_ids=["tf_xs_wq_guishu"]),
    ReferentialAssertion(id="rr_xs_wenquanzhen",
                         appellation_id="app_xs_wenquanzhen",
                         referent_entity_id="ent_xs_wenquanzhen",
                         time_span=_ts(1949, 2026, "ts_xs_r10b"),
                         evidence_fact_ids=["tf_xs_wq_guishu"],
                         provenance="现代政区实体分立（GPT审3-2）；形符不进"
                                    "评测字形表（span 错位，见 holdout_eval）"),
    ReferentialAssertion(id="rr_xs_fenghuangling",
                         appellation_id="app_xs_fenghuangling",
                         referent_entity_id="ent_xs_fenghuangling",
                         time_span=TimeSpan(id="ts_xs_r12", label="近现代-今",
                                            open_begin=True, begin=None,
                                            end=_dt(2026, "ts_xs_r12e")),
                         evidence_fact_ids=["tf_xs_fhl_jingqu"],
                         provenance="「凤凰岭」作为山体通称主要流行于近现代（景区命名"
                                    "层）；明清文献未见确证，不比定为历史山名"),
    ReferentialAssertion(id="rr_xs_fhl_jingqu",
                         appellation_id="app_xs_fhl_jingqu",
                         referent_entity_id="ent_xs_fhl_jingqu",
                         time_span=TimeSpan(id="ts_xs_r12b", label="1990年代中期-今",
                                            open_begin=True, begin=None,
                                            end=_dt(2026, "ts_xs_r12be")),
                         evidence_fact_ids=["tf_xs_fhl_jingqu"],
                         provenance="景区经营实体与山体分立（GPT审3-17）：开放、"
                                    "游径、门票等只属景区层"),
    ReferentialAssertion(id="rr_xs_longquansi",
                         appellation_id="app_xs_longquansi",
                         referent_entity_id="ent_xs_longquansi",
                         time_span=TimeSpan(id="ts_xs_r13", label="传承至今",
                                            open_begin=True, begin=None,
                                            end=_dt(2026, "ts_xs_r13e")),
                         evidence_fact_ids=["tf_xs_fhl_longquansi"]),
    ReferentialAssertion(id="rr_xs_beianhe", appellation_id="app_xs_beianhe",
                         referent_entity_id="ent_xs_beianhe",
                         time_span=_ts(1782, 2026, "ts_xs_r14"),
                         evidence_fact_ids=["tf_xs_bah_cun"]),
    ReferentialAssertion(id="rr_xs_jinshan", appellation_id="app_xs_jinshan",
                         referent_entity_id="ent_xs_jinshan",
                         time_span=_ts(1425, 2026, "ts_xs_r15"),
                         evidence_fact_ids=["tf_xs_js_feipin",
                                            "tf_xs_js_jingtailin"]),
    ReferentialAssertion(id="rr_xs_jinshankou",
                         appellation_id="app_xs_jinshankou",
                         referent_entity_id="ent_xs_jinshan",
                         time_span=_ts(1425, 2026, "ts_xs_r16"),
                         evidence_fact_ids=["tf_xs_js_jingtailin"]),
    ReferentialAssertion(id="rr_xs_feipinyuan",
                         appellation_id="app_xs_feipinyuan",
                         referent_entity_id="ent_xs_jinshan",
                         time_span=_ts(1912, 2026, "ts_xs_r17"),
                         evidence_fact_ids=["tf_xs_js_feipin"],
                         provenance="「妃嫔园」为近现代文史著述对金山妃嫔葬地的概括性"
                                    "别称，非明代官称；制度依据为嘉靖祀典诸妃别葬金山"
                                    "条，故挂该文献为证但标注概括性质"),
]


# ==================================================================
# 7. 断言与采信：存疑全部显式标注（推断/传说/现代观点绝不混级为史实）
# ==================================================================

PROPOSITIONS: List[Proposition] = [
    Proposition(
        id="prop_xs_bayuan_guifu",
        statement="金章宗「西山八院（八大水院）」成员与今地对应诸说并存："
                  "《帝京景物略》明言香水院在妙高峰法云寺（「草际断碑香水院三字"
                  "尚存」）；今又有温泉后山说、凤凰岭龙泉寺水院说等现代归附——"
                  "八院名目本身系明人追述，归附皆后世比定，非金代文献自述",
        derived_from_fact_ids=["tf_xs_jinzhangzong_bayuan",
                               "tf_xs_wq_quanyan"],
        inferred_subject_id="ent_xs_dajuesi",
        inference_method="一手文献（《帝京景物略》）只给出法云寺=香水院一处直接"
                         "对位；其余对应皆现代著述归纳。两源冲突不取区间值："
                         "以文献原文口径为基准，温泉归附说降级为存疑",
        alternative_explanations=[
            "香水院=温泉后山说（现代归附，era4 长编层）",
            "潭水院=凤凰岭龙泉寺水院说（现代归附）",
        ],
    ),
    Proposition(
        id="prop_xs_bys_founder",
        statement="碧云庵创建者为元代「耶阿利吉」（《帝京景物略》原文）；"
                  "其是否即耶律楚材后人与名字写法（耶律阿利吉/耶律阿勒锡）"
                  "诸书不一——存疑待考",
        derived_from_fact_ids=["tf_xs_bys_yealiji", "tf_xs_bys_yuanbei"],
        inferred_subject_id="ent_xs_biyunsi",
        inference_method="明末文献只记名讳未言世系；后世比定与异写不入实体层，"
                         "只入命题层",
        alternative_explanations=[
            "耶律楚材后人说（今论著通行表述，无元断代档案直证）",
            "名讳异写说（阿利吉/阿勒锡为同名异译）",
        ],
    ),
    Proposition(
        id="prop_xs_jinling_fangshan",
        statement="金山为明代妃嫔皇子葬地总名；金代帝陵（金陵）在房山大房山，"
                  "与海淀金山无涉——「金代皇家陵区在金山」系地望误植",
        derived_from_fact_ids=["tf_xs_js_feipin", "tf_xs_js_wubei",
                               "tf_xs_js_huangzi"],
        inferred_subject_id="ent_xs_jinshan",
        inference_method="卷100 明代葬制三条转引俱言妃嫔皇子葬金山，无一言金代；"
                         "金陵地望为房山九龙山，学界无争议；两地面同名，"
                         "不得跨代混建",
        alternative_explanations=[
            "「金代皇家陵区」说（无书证，弃）",
        ],
    ),
    Proposition(
        id="prop_xs_qishierfu_suyan",
        statement="「一溜边山七十二府」为葬区俗呼，属民间俗谚层：《明史·后妃传》"
                  "《帝京景物略》《长安客话》与四库本《日下旧闻考》均无此八字原句，"
                  "不得挂在官书名下引",
        derived_from_fact_ids=["tf_xs_js_feipin"],
        inferred_subject_id="ent_xs_jinshan",
        inference_method="全书检索无命中→俗谚非原典；七十二府俗名已由 settlements "
                         "模块以 FOLK_LEGEND 登记，本模块不重复建名",
        alternative_explanations=[
            "era6 长编曾把该句标注为《明史·后妃传》/卷103 引文——已判为层级误标，"
            "提请修订长编（见研究底稿出处考订记录）",
        ],
    ),
    Proposition(
        id="prop_xs_wenquan_miao",
        statement="「明正德九年（1514）建温泉堂/温泉庙」之说无一手文献确证，"
                  "存疑待考；温泉有明文者为泉眼（画眉山北十里），非庙宇",
        derived_from_fact_ids=["tf_xs_wq_quanyan"],
        inferred_subject_id="ent_xs_wq_quanyan",
        inference_method="仅今人网页转述，未回查到明清原典；按「找不到就不列年代」"
                         "处理，庙宇建置不立状态",
        alternative_explanations=[
            "温泉堂/温泉庙说（无书证）",
            "泉眼崇拜或衍生民俗说（推测）",
        ],
    ),
    Proposition(
        id="prop_xs_longquansi_niandai",
        statement="龙泉寺始建年代存疑：通行口径「辽应历初年（约951）僧继升创建」"
                  "无早期纪年碑刻确证；元至顺三年（1332）舍蓝蓝「于西山重修"
                  "龙泉寺」之记载是否即凤凰岭龙泉寺亦存疑",
        derived_from_fact_ids=["tf_xs_fhl_longquansi"],
        inferred_subject_id="ent_xs_longquansi",
        inference_method="景区/今志口径为现代机构表述，非辽代书证；元代记载之"
                         "「西山龙泉寺」同名异地可能存在，两说并存不取区间值",
        alternative_explanations=[
            "辽应历初年始建说（通行口径，无早期碑证）",
            "元代舍蓝蓝重修说（记载同指存疑）",
            "始建年代不可考说（无早期纪年实物）",
        ],
    ),
    Proposition(
        id="prop_xs_wenquan_split",
        statement="温泉泉眼/温泉村/温泉镇三实体分立：明清书证对象是泉眼与地望"
                  "（画眉山北十里、隶昌平州境），村是聚落（成村年代无考，村名"
                  "因泉），镇是现代政区；「温泉村今属温泉镇」是空间包含关系，"
                  "不是同一实体。无连续地名档案不建 sameAs（GPT审3-2）",
        derived_from_fact_ids=["tf_xs_wq_quanyan", "tf_xs_wq_changping",
                               "tf_xs_wq_guishu"],
        inferred_subject_id="ent_xs_wq_quanyan",
        inference_method="实体类型分立判定：按书证对象类型（自然泉/聚落/政区）"
                         "分立实体，引文只证空间包含与得名关联，不证同指",
        alternative_explanations=[
            "「温泉村（温泉泉眼所在聚落）」合并表述（旧模型，GPT审3-2 判为"
            "实体类型污染，已拆）",
        ],
    ),
    Proposition(
        id="prop_xs_fhl_split",
        statement="凤凰岭山体地望与凤凰岭自然风景区（现代经营实体）二分："
                  "「20世纪90年代中期开发开放」只证明现代景区实体，景区边界"
                  "不得倒灌为历史山体范围；「凤凰岭」作山体通称的明清文献"
                  "记载未见确证（GPT审3-17）",
        derived_from_fact_ids=["tf_xs_fhl_jingqu"],
        inferred_subject_id="ent_xs_fhl_jingqu",
        inference_method="实体类型分立判定：山体（自然地貌）与景区（经营实体，"
                         "含游径/门票/管理机构）分立，开放事件只挂景区层，"
                         "两者以山麓空间关系连接",
        alternative_explanations=[
            "「今为凤凰岭自然风景区」单实体表述（旧模型，GPT审3-17 判为"
            "实体类型污染，已拆）",
        ],
    ),
    Proposition(
        id="prop_xs_beianhe_etymology",
        statement="北安河得名两说并存：①金代「安和」说；②安河（长乐河）音转/"
                  "方位前缀说——均无早期文证；可证者唯乾隆朝官书已载村名",
        derived_from_fact_ids=["tf_xs_bah_cun"],
        inferred_subject_id="ent_xs_beianhe",
        inference_method="官书首见（1782 成书）早于两说的任何文证；"
                         "音转说以「长乐河即安河」按语为旁证但不构成命名直证",
        alternative_explanations=[
            "金代安和说（无书证）",
            "安河音转说（旁证而非直证）",
        ],
    ),
    Proposition(
        id="prop_xs_bah_not_xinggong",
        statement="金章宗行宫水院（清水院）在旸台山麓，不在北安河村内；"
                  "「北安河金章宗行宫」是以今村名代指地片的今人表述，"
                  "不得由此推出北安河村金代已存或为行宫属地",
        derived_from_fact_ids=["tf_xs_jinzhangzong_bayuan", "tf_xs_bah_cun"],
        inferred_subject_id="ent_xs_beianhe",
        inference_method="空间自证：辽碑（1068）早于北安河村名官书首见（1782）"
                         "七百余年；两者仅相邻，无沿革绑定证据",
        alternative_explanations=[
            "行宫属地/金代已村说（无书证，弃）",
        ],
    ),
    Proposition(
        id="prop_xs_yulan_niandai",
        statement="大觉寺四宜堂白玉兰为寺内名物，但其植栽年代（俗传辽植/清植）"
                  "与树龄诸说分歧，无文献与树木档案确证——存疑不列年代",
        derived_from_fact_ids=[],
        inferred_subject_id="ent_xs_dajuesi",
        inference_method="媒体与景区口径流传、建置档案无载；按「数字找不到官方"
                         "档案就不列」纪律处理，只登记名物本身",
        alternative_explanations=[
            "辽代遗植说（无书证）",
            "清代植栽说（无书证）",
        ],
    ),
]

ADOPTIONS: List[BeliefAdoption] = [
    BeliefAdoption(proposition_id="prop_xs_bayuan_guifu",
                   status=EpistemicStatus.CONTESTED, confidence=0.5,
                   adopted_by="西山词条批次xishan",
                   rationale="八院是明人追述框架；归附对应只认《帝京景物略》"
                             "法云寺一例为文献口径，余者存疑"),
    BeliefAdoption(proposition_id="prop_xs_bys_founder",
                   status=EpistemicStatus.CONTESTED, confidence=0.5,
                   adopted_by="西山词条批次xishan",
                   rationale="明末原文只记「耶阿利吉」，世系与异写不混入实体层"),
    BeliefAdoption(proposition_id="prop_xs_jinling_fangshan",
                   status=EpistemicStatus.VERIFIED, confidence=0.9,
                   adopted_by="西山词条批次xishan",
                   rationale="卷100葬制文献与金陵房山地望无冲突空间；"
                             "按 Main 纠偏口径固化，地望误植排除"),
    BeliefAdoption(proposition_id="prop_xs_qishierfu_suyan",
                   status=EpistemicStatus.DISPROVEN, confidence=0.85,
                   adopted_by="西山词条批次xishan",
                   rationale="四库本全书检索无该句，era6 长编层级误标已立案；"
                             "反驳证据=检索记录（研究底稿出处考订）",
                   refuting_fact_ids=["tf_xs_js_feipin", "tf_xs_js_jingtailin"]),
    BeliefAdoption(proposition_id="prop_xs_wenquan_miao",
                   status=EpistemicStatus.UNSUBSTANTIATED, confidence=0.3,
                   adopted_by="西山词条批次xishan",
                   rationale="仅网页转述无原典；庙宇建置不立状态不列年代"),
    BeliefAdoption(proposition_id="prop_xs_longquansi_niandai",
                   status=EpistemicStatus.CONTESTED, confidence=0.45,
                   adopted_by="西山词条批次xishan",
                   rationale="三说并存且皆无早期纪年实证；通行口径只作口径引用"),
    BeliefAdoption(proposition_id="prop_xs_beianhe_etymology",
                   status=EpistemicStatus.CONTESTED, confidence=0.4,
                   adopted_by="西山词条批次xishan",
                   rationale="两说皆无早期文证；只固化官书首见事实"),
    BeliefAdoption(proposition_id="prop_xs_bah_not_xinggong",
                   status=EpistemicStatus.VERIFIED, confidence=0.85,
                   adopted_by="西山词条批次xishan",
                   rationale="时间先后由辽碑与官书首见直接给出；相邻≠沿革绑定"),
    BeliefAdoption(proposition_id="prop_xs_yulan_niandai",
                   status=EpistemicStatus.CONTESTED, confidence=0.4,
                   adopted_by="西山词条批次xishan",
                   rationale="名物可证、年代不可证；按不列无据数字纪律处理"),
]


# ==================================================================
# 8. 空间变化事件
# ==================================================================

TRANSFORMATIONS: List[PlaceTransformation] = [
    PlaceTransformation(
        id="pte_xs_djs_1428_rebuild", entity_id="ent_xs_dajuesi",
        transformation=PlaceTransformationEvent.REBUILT,
        time_span=_ts(1428, 1428, "ts_xs_pte1"),
        resulting_state_id="st_xs_djs_xuande",
        resulting_condition="宣德三年重建，故名灵泉、宣宗易以今名大觉寺",
        evidence_fact_ids=["tf_xs_xuande_gengming"]),
    PlaceTransformation(
        id="pte_xs_djs_1446_repair", entity_id="ent_xs_dajuesi",
        transformation=PlaceTransformationEvent.REBUILT,
        time_span=_ts(1446, 1446, "ts_xs_pte2"),
        resulting_state_id="st_xs_djs_zhengtong",
        resulting_condition="正统十一年三月王祐督工修缮",
        evidence_fact_ids=["tf_xs_zhengtong_xiu"]),
    PlaceTransformation(
        id="pte_xs_djs_1747_rebuild", entity_id="ent_xs_dajuesi",
        transformation=PlaceTransformationEvent.REBUILT,
        time_span=_ts(1747, 1747, "ts_xs_pte3"),
        resulting_state_id="st_xs_djs_qianlong",
        resulting_condition="乾隆十二年发帑重修，御书诸殿额",
        evidence_fact_ids=["tf_xs_kangxi_qianlong_xiu"]),
    PlaceTransformation(
        id="pte_xs_bys_1516_expand", entity_id="ent_xs_biyunsi",
        transformation=PlaceTransformationEvent.EXPANDED,
        time_span=_ts(1516, 1516, "ts_xs_pte4"),
        resulting_state_id="st_xs_bys_zhengde",
        resulting_condition="正德十一年扩庵为寺，俗呼于公寺",
        evidence_fact_ids=["tf_xs_bys_zhengde"]),
    PlaceTransformation(
        id="pte_xs_bys_1748_expand", entity_id="ent_xs_biyunsi",
        transformation=PlaceTransformationEvent.EXPANDED,
        time_span=_ts(1748, 1748, "ts_xs_pte5"),
        resulting_state_id="st_xs_bys_qianlong",
        resulting_condition="乾隆十三年增建金刚宝座塔",
        evidence_fact_ids=["tf_xs_bys_jingangta"]),
    PlaceTransformation(
        id="pte_xs_bys_2024_repair", entity_id="ent_xs_biyunsi",
        transformation=PlaceTransformationEvent.REBUILT,
        time_span=_ts(2024, 2024, "ts_xs_pte6"),
        resulting_state_id="st_xs_bys_2024",
        resulting_condition="2023年11月起封闭保护修缮，2024年9月26日恢复开放",
        evidence_fact_ids=["tf_xs_bys_xianzhuang"]),
    PlaceTransformation(
        id="pte_xs_js_1534_expand", entity_id="ent_xs_jinshan",
        transformation=PlaceTransformationEvent.EXPANDED,
        time_span=_ts(1534, 1534, "ts_xs_pte7"),
        resulting_state_id="st_xs_js_ming",
        resulting_condition="嘉靖十三年金山预造五墓各九数以次葬焉",
        evidence_fact_ids=["tf_xs_js_wubei"]),
    PlaceTransformation(
        id="pte_xs_fhl_1996_park", entity_id="ent_xs_fhl_jingqu",
        transformation=PlaceTransformationEvent.REBUILT,
        time_span=TimeSpan(id="ts_xs_pte8", label="1990年代中期",
                           begin=_dt(1996, "ts_xs_pte8b",
                                     precision="approximate"),
                           end=_dt(1996, "ts_xs_pte8e")),
        resulting_state_id="st_xs_fhl_jingqu",
        resulting_condition="凤凰岭自然风景区开放（现代旅游定位，非历史建置）",
        evidence_fact_ids=["tf_xs_fhl_jingqu"]),
    PlaceTransformation(
        id="pte_xs_lqs_2005_restore", entity_id="ent_xs_longquansi",
        transformation=PlaceTransformationEvent.REBUILT,
        time_span=_ts(2005, 2005, "ts_xs_pte9"),
        resulting_state_id="st_xs_lqs_2005",
        resulting_condition="2005年恢复为宗教活动场所",
        evidence_fact_ids=["tf_xs_fhl_longquansi"]),
]

AGGREGATES: List[PlaceAggregate] = []
