"""
haidian_kg/calibration/suburbs.py
郊区聚落词条（E5 一亩园 + E10 蓝靛厂）—— 海淀历史地名知识库入库模块

数据唯一来源（两份交付研究档案，不凭印象补写）：
  - yimuyuan_video/research.md（E5，v2 已经 ChatGPT 复查修订并冻结）
  - landianchang_video/research.md（E10，v1，2026-09-30 GPT 闸门 PASS WITH EDITS）

证据分级映射（research.md 分级 → 本体表达，绝不混级）：
  [L1 官书/图档/一手石刻] → TextualFact（繁体逐字引文 / 图档记录式陈述）+ VERIFIED
  [L2 政府/官方研究]      → 海淀区公开资料、文物局公开资料记录式事实 + VERIFIED
  [L3 地方文史]           → 与 L2 同挂记录事实但 translator_note 分层（刘诚连）
  [文献记载]（二手转引）  → translator_note 标转引，不当一手
  [民间传说]              → FOLK_LEGEND 采信 + alternative_explanations
  [存疑待考]              → CONTESTED / UNSUBSTANTIATED + 双方说法

E5 红线落位（research.md §六 → 机器判据）：
  - 皇帝正式亲耕耤田礼（真正的「一亩三分地」）在【先农坛】（L1 礼制史实）；
    一亩园只有民间亲耕传说（雍正帝演耕处，「缺少依据」）——本库结构上：
    ent_yimuyuan 无雍正年代任何状态（图档首证 1792），任何雍正年亲耕断言
    在审计层不可判通过；先农坛不入本库实体（非海淀地物）
  - 《八旬万寿盛典》（1792）图档证明的是【空间形态】（建筑院落、道路、水渠、
    土山）；「圆明园大宫门前附属院落、后勤及公务人员临时住舍」是【L2 功能解释】
    ——图证空间、研究释功能，两层分挂两个事实节点，不得混说「图证明宿舍」
  - 大宫门 ≠ 正大光明：大宫门是正门，正大光明是过二宫门后的正殿
  - 娘娘庙：康熙重建、光绪再建；刘诚连只能表述「再建/重修」非「始建」
  - 扇面湖按四段重排（1763 成湖 → 1860 毁后稻田 → 2000 填埋建市场 →
    2024 春夏复湖开放），不凑「260 年五次变身」；2024 不锁月日（「春夏」）
E10 红线落位（research.md §6 → 机器判据）：
  - 火器营不是放火的营：八旗专习枪炮专业部队（鸟枪、子母炮），近似明神机营；
    「放火的营房」混淆句在审计层必须拦截
  - 年份链 1688（汉军火器兼练大刀营）→ 1691（始设火器营）→ 1770（奏请迁建）
    → 1773（营区基本建成）四个年份不得混用；「建于乾隆三十五年」作起点是
    通行错讹（漏掉 1691）
  - 营房规模只报分项：官廨 1024 间、炮甲连房 6038 间、周围门楼 3176 座
    （《日下旧闻考》）；总数 7196 是分项相加非史料原文（禁用）、
    「四千余间」查无实据（点破）——分项数字入状态层，总数禁令入命题层；
    审计层对「四千余间 + 营房」混说句直接 BLOCK
  - 蓝靛厂不是民间染坊：明内府织染局外署（初名靛园厂），宫廷官署宦官掌控；
    染蓝植物（明永乐间）早于厂名约 170 年——地名是行政的产物
  - 西顶是北京五顶之一（唯一在海淀），非「五顶之首」「等级最高」；
    「旧京八顶」体系删除；北顶在朝阳奥森、南顶在丰台大红门外，方位不得错
  - 营区踪迹全无 ≠ 地名消亡：毁损≠消亡（火器营站/桥/路/横街/永山宅院留存）

模块导出与现有词条同构：SOURCES / DIVISIONS / FACTS / ENTITIES / STATES /
IDENTITIES / APPELLATIONS / REFERENCES / TRANSFORMATIONS / PROPOSITIONS /
ADOPTIONS / AGGREGATES。
"""
from typing import List

from ..ontology.temporal import (
    CalibrationTable, DatePoint, Era, GregorianDate, ReignYear, TimeSpan,
)
from ..ontology.epistemic import (
    BeliefAdoption, EpistemicStatus, HistoricalSource, Proposition,
    SourceCategory, SourceDivision, TextualFact,
)
from ..ontology.spatiotemporal import (
    Appellation, AppellationKind, DiachronicIdentityAssertion,
    HistoricalFeatureState, IdentityRelation, PersistentSpatialEntity,
    PhysicalThingKind, PlaceAggregate, PlaceTransformation,
    PlaceTransformationEvent, ReferentialAssertion,
)
from .bibliography import source_by_title

CAL = CalibrationTable.CN_ASTRONOMICAL_ALMANAC


def _ry(era, title, n, verbatim, month=None, ganzhi=None):
    """文献纪年表达（「文献怎么写的」），不做换算——换算挂 DatePoint.gregorian"""
    return ReignYear(era=era, reign_title=title, year_within_reign=n,
                     lunar_month=month, ganzhi=ganzhi, verbatim=verbatim)


def _dt(y, tag, reign=None, precision="year"):
    return DatePoint(id=tag, label=str(y), precision=precision, reign_year=reign,
                     gregorian=GregorianDate(year=y, calibration=CAL))


def _ts(y1, y2, tag):
    return TimeSpan(id=tag, label="%d-%d" % (y1, y2),
                    begin=_dt(y1, tag + "_b"), end=_dt(y2, tag + "_e"))


# ==================================================================
# 1. 文献与篇卷（一律取自统一书目表，一书一条，禁止在此另建）
# ==================================================================

SOURCES: List[HistoricalSource] = [
    # E5 一亩园侧
    source_by_title("钦定八旬万寿盛典"),
    source_by_title("海淀区人民政府公开史地沿革资料"),
    # E10 蓝靛厂侧
    source_by_title("清史稿"),
    source_by_title("大明会典"),
    source_by_title("钦定日下旧闻考"),
    source_by_title("酌中志"),
    source_by_title("重修西顶娘娘庙碑记"),
    source_by_title("北京市文物局公开文保资料"),
]

DIVISIONS: List[SourceDivision] = [
    # ---- E5 一亩园 ----
    # 官书图档（L1）：图绘部分，卷次按图绘册计
    SourceDivision(id="div_bx_tu", source_id="src_baxun_wanshou",
                   volume_number="图绘", section_title="图绘·一亩园区域"),
    # 海淀区公开资料（L2 记录式陈述，与古籍引文分层；政府网站转载按原作者层级计）
    SourceDivision(id="div_hd_yimuyuan", source_id="src_hd_gov_open",
                   volume_number="公开沿革",
                   section_title="一亩园条（考据反转与功能解释，北京日报·海淀发布2024-06转载，按原作者层级计L2）"),
    SourceDivision(id="div_hd_shanmianhu", source_id="src_hd_gov_open",
                   volume_number="公开沿革", section_title="扇面湖条（疏浚沿革与2024复建）"),
    SourceDivision(id="div_hd_niangniangmiao", source_id="src_hd_gov_open",
                   volume_number="公开沿革", section_title="一亩园娘娘庙条（始建链与区级文保）"),
    # ---- E10 蓝靛厂 ----
    SourceDivision(id="div_qsg_zhiguanzhi", source_id="src_qingshigao",
                   volume_number="职官志", section_title="火器营条（组建与官制沿革）"),
    SourceDivision(id="div_dmhnd_zhiran", source_id="src_daminghuidian",
                   volume_number="卷次待核", section_title="内府织染局条（宫廷官营作坊制度）"),
    SourceDivision(id="div_rxjwkc_waiying", source_id="src_rxjwkc",
                   volume_number="卷次待核", section_title="外火器营条（营房分项规模）"),
    SourceDivision(id="div_zzz_xiding", source_id="src_zuozhongzhi",
                   volume_number="卷次待核", section_title="西顶娘娘庙始建条"),
    SourceDivision(id="div_xdb_huixiang", source_id="src_xiding_miao_bei",
                   volume_number="全碑", section_title="重修碑记（四月庙会与官帑修葺）"),
    SourceDivision(id="div_wjbz_waiying", source_id="src_wjbz_open",
                   volume_number="文保公开资料", section_title="外火器营沿革与地名留存条"),
    SourceDivision(id="div_hd_xiding", source_id="src_hd_gov_open",
                   volume_number="公开沿革", section_title="西顶娘娘庙条（五顶方位与庙会）"),
    SourceDivision(id="div_hd_ldc", source_id="src_hd_gov_open",
                   volume_number="公开沿革", section_title="蓝靛厂条（靛园厂沿革与街市）"),
    SourceDivision(id="div_hd_fusi", source_id="src_hd_gov_open",
                   volume_number="公开沿革", section_title="清真寺与立马关帝庙条"),
]


# ==================================================================
# 2. 文本事实（古籍为繁体逐字引文；政府/机构公开资料为记录式陈述，分层不混）
# ==================================================================

FACTS: List[TextualFact] = [
    # ---- E5 一亩园：图档（L1）与功能解释（L2）分挂两个事实节点 ----
    TextualFact(
        id="tf_bx_tu", division_id="div_bx_tu",
        verbatim_quote="《八旬万寿盛典》图绘部分显示：一亩园区域有建筑院落、道路、"
                       "水渠、土山，为复杂的建筑区域",
        attested_string="一畝園",
        source_year=_dt(1792, "dt_bx",
                        _ry(Era.QING, "乾隆", 57, "乾隆五十七年")),
        translator_note="图档证明的是空间形态（L1）；功能解释见 tf_hd_func（L2），"
                        "两层不得混说为「图证明官员宿舍」",
    ),
    TextualFact(
        id="tf_hd_func", division_id="div_hd_yimuyuan",
        verbatim_quote="现代官方研究解释：一亩园为圆明园大宫门前附属院落、后勤及"
                       "公务人员临时住舍",
        attested_string="附属院落",
        translator_note="功能解释属 L2 现代研究，非 1792 图档自白；大宫门是圆明园"
                        "正门，正大光明是入大宫门、过二宫门后的正殿，二者非同一建筑",
    ),
    TextualFact(
        id="tf_hd_yanzheng", division_id="div_hd_yimuyuan",
        verbatim_quote="传说为雍正帝演耕处，但缺少依据",
        attested_string="演耕",
        translator_note="北京日报·海淀发布 2024-06（考据反转主源，政府网站转载按"
                        "原作者层级计 L2）；民间亲耕传说为 L5，与 L1 礼制史实"
                        "（耤田礼在先农坛）严格分层",
    ),
    TextualFact(
        id="tf_hd_minguo", division_id="div_hd_yimuyuan",
        verbatim_quote="清代地名「一亩园」、民国时期随土地开垦形成的村落、现代社区"
                       "为三个层次，不可画等号（圆明园管理处研究）",
        attested_string="民國村落",
    ),
    # ---- E5 扇面湖：四段层累，不凑五次 ----
    TextualFact(
        id="tf_smh_1763", division_id="div_hd_shanmianhu",
        verbatim_quote="乾隆二十八年（1763）疏浚成湖，旧称前湖，御道穿湖形似宫扇，"
                       "故名扇面湖",
        attested_string="扇面湖",
        source_year=_dt(1763, "dt_smh",
                        _ry(Era.QING, "乾隆", 28, "乾隆二十八年")),
    ),
    TextualFact(
        id="tf_smh_1860", division_id="div_hd_shanmianhu",
        verbatim_quote="1860年英法联军焚毁圆明园，扇面湖一带园林建筑俱损，"
                       "其后渐辟为稻田",
        attested_string="稻田",
    ),
    TextualFact(
        id="tf_smh_2000", division_id="div_hd_shanmianhu",
        verbatim_quote="2000年扇面湖故址填埋，建农贸市场",
        attested_string="农貿市場",
    ),
    TextualFact(
        id="tf_smh_2024", division_id="div_hd_shanmianhu",
        verbatim_quote="2024年春夏扇面湖建成并对公众开放：复挖3.2万平方米湖面、"
                       "560米亲水步道、18.62公顷绿化；地下遗迹覆土保护，御道、"
                       "水系、植物为展示性恢复，非原样复建",
        attested_string="展示性恢復",
        translator_note="不锁月日：「5月开放」与「6月竣工」两种官方口径并存，"
                        "统一表述「2024年春夏建成并对公众开放」",
    ),
    # ---- E5 一亩园娘娘庙：康熙重建、光绪再建；刘诚连分层（L3） ----
    TextualFact(
        id="tf_nm_kangxi", division_id="div_hd_niangniangmiao",
        verbatim_quote="一亩园娘娘庙（泰山圣母庙）较可靠资料记康熙重建、光绪再建；"
                       "乾隆晚期图档已见扇面湖西岸娘娘庙",
        attested_string="娘娘廟",
    ),
    TextualFact(
        id="tf_nm_guangxu", division_id="div_hd_niangniangmiao",
        verbatim_quote="光绪年间再建；御前掌玺太监刘诚连在庙西置四合院与菜园",
        attested_string="劉誠連",
        translator_note="刘诚连条为北京晚报文史（L3人物钩子），与官方再建记载分层；"
                        "若参与营建只能表述为「再建/重修」，非「始建」",
    ),
    TextualFact(
        id="tf_nm_2014", division_id="div_hd_niangniangmiao",
        verbatim_quote="2014年8月一亩园娘娘庙公布为海淀区区级文物保护单位；三路院落"
                       "现存中路后半，前殿关圣帝君、后殿九天娘娘",
        attested_string="區級文物保護單位",
    ),
    # ---- E10 火器营：年份链 1688/1691/1770/1773 不得混用 ----
    TextualFact(
        id="tf_qsg_dadao", division_id="div_qsg_zhiguanzhi",
        verbatim_quote="康熙二十七年，設漢軍火器兼練大刀營，置總管、翼長各一人，"
                       "副都統兼管",
        attested_string="漢軍火器兼練大刀營",
        source_year=_dt(1688, "dt_qsg1",
                        _ry(Era.QING, "康熙", 27, "康熙二十七年")),
    ),
    TextualFact(
        id="tf_qsg_shehuoqi", division_id="div_qsg_zhiguanzhi",
        verbatim_quote="三十年，始設火器營",
        attested_string="始設火器營",
        source_year=_dt(1691, "dt_qsg2",
                        _ry(Era.QING, "康熙", 30, "康熙三十年")),
        translator_note="与 tf_qsg_dadao 不是重复记载：先有大刀营（1688），"
                        "后正式定名火器营（1691），同一支部队的改名",
    ),
    TextualFact(
        id="tf_qsg_guanzhi", division_id="div_qsg_zhiguanzhi",
        verbatim_quote="雍正三年省察哈爾八旗護軍參領，改入本營為專缺；乾隆二十八年"
                       "改置營總、鳥槍護軍參領等職，乃官制調整非新設",
        attested_string="鳥槍護軍參領",
    ),
    TextualFact(
        id="tf_wjbz_qianjian", division_id="div_wjbz_waiying",
        verbatim_quote="乾隆三十五年（1770）管理火器营事务的蒙古都统色布腾巴勒珠尔"
                       "奏请迁建城西营房，乾隆批准；乾隆三十八年（1773）营区基本建成",
        attested_string="色布騰巴勒珠爾",
        translator_note="1773 为文物局公开资料口径（研究结论），非《清史稿》直接"
                        "记载；通行说法多作「乾隆三十五年建」，作起点即漏掉 1691",
    ),
    # ---- E10 营房规模：只报分项（《日下旧闻考》门楼数为一手明文） ----
    TextualFact(
        id="tf_rxjwkc_menlou", division_id="div_rxjwkc_waiying",
        verbatim_quote="周圍門樓三千一百七十六座",
        attested_string="門樓",
        translator_note="官廨1024间、官办义学等60间、炮甲连房6038间、水井16眼、"
                        "水房16间、泄水沟25道为二手资料转引分项记载（说法一）；"
                        "总数「7196间」系分项相加、非史料原文，禁用；"
                        "「四千余间」查无实据，点破时说「常见说法」",
    ),
    TextualFact(
        id="tf_wjbz_zongji", division_id="div_wjbz_waiying",
        verbatim_quote="火器营营区纵然已踪迹全无，但是现有部分建筑遗存，并有许多与"
                       "火器营相关的地名传世，比如著名的横街、永山宅院、老营房路、"
                       "火器营桥等",
        attested_string="地名傳世",
        translator_note="北京市文物局《海淀清代和硕庄亲王施地碑文考释》；"
                        "「踪迹全无」指营区建筑，不等于地名/地点消亡",
    ),
    TextualFact(
        id="tf_hd_neiwai", division_id="div_hd_ldc",
        verbatim_quote="火器营分内外两营：内火器营驻北京城内，设枪营、炮营；"
                       "外火器营建于西郊蓝靛厂",
        attested_string="外火器營",
    ),
    TextualFact(
        id="tf_hd_jingqi", division_id="div_hd_ldc",
        verbatim_quote="京旗外三营＝圆明园护卫营＋香山健锐营＋蓝靛厂外火器营，"
                       "全部位于北京西北郊，互为犄角呈三角之势；清皇室每年大量时间"
                       "在西郊行宫度过，此地必须陈以重兵；蓝靛厂东临昆玉河、"
                       "北接颐和园，自是要冲",
        attested_string="京旗外三營",
    ),
    TextualFact(
        id="tf_hd_metro", division_id="div_hd_ldc",
        verbatim_quote="火器营站即今北京地铁10号线车站，名字直接来自清代营房；"
                       "老营房路、火器营桥、横街、永山宅院等地名沿用至今",
        attested_string="火器營站",
    ),
    # ---- E10 蓝靛厂：官营作坊，非民间染坊 ----
    TextualFact(
        id="tf_hd_ldc_yongle", division_id="div_hd_ldc",
        verbatim_quote="明永乐年间此地开始与蓝靛生产相关，此地洼水清，种植蓼蓝、"
                       "山蓝等染料植物",
        attested_string="蓼藍",
        translator_note="「宫内派人」主体表述证据不足已删（闸门修正）；"
                        "具体年份不给，只说明永乐年间起",
    ),
    TextualFact(
        id="tf_hd_dingyuanchang", division_id="div_hd_ldc",
        verbatim_quote="明代中后期此地设作坊，最早称「靛园厂」，隶属内府织染局；"
                       "后因专产青蓝色染料改称「蓝靛厂」",
        attested_string="靛園廠",
        translator_note="「万历十五年（1587）」精确年份查无一手依据，已删除；"
                        "本条只说「明代已有蓝靛生产，后成厂名」",
    ),
    TextualFact(
        id="tf_dmhnd_zhiran", division_id="div_dmhnd_zhiran",
        verbatim_quote="《大明会典》载内府织染局官营作坊制度：织染局属皇宫大内"
                       "宫廷官署，由宦官掌控；明称内织染局，清改称织染局，"
                       "外署辖蓝靛厂",
        attested_string="織染局",
        translator_note="记录式陈述，未逐字录会典原文（万历朝重修本）；"
                        "「红利的红」是官署的官职色，非民间作坊",
    ),
    # ---- E10 西顶娘娘庙：五顶之一（唯一在海淀），非五顶之首 ----
    TextualFact(
        id="tf_zzz_xiding", division_id="div_zzz_xiding",
        verbatim_quote="萬曆三十六年，於藍靛廠始建西頂娘娘廟",
        attested_string="西頂娘娘廟",
        source_year=_dt(1608, "dt_zzz",
                        _ry(Era.MING, "万历", 36, "万历三十六年")),
    ),
    TextualFact(
        id="tf_xdb_hui", division_id="div_xdb_huixiang",
        verbatim_quote="重修西顶娘娘庙碑记：载四月进香庙会之盛况与官帑修葺",
        attested_string="官帑修葺",
        translator_note="清康熙内务府/顺天府立碑；本条为石刻档案记录式陈述，"
                        "未逐字录碑文",
    ),
    TextualFact(
        id="tf_hd_xiding_yange", division_id="div_hd_xiding",
        verbatim_quote="西顶娘娘庙明万历三十六年建，称护国洪蕊宫（一说洪慈宫）；"
                       "清康熙五十一年（1712）改称广仁宫碧霞元君庙，"
                       "又名西顶碧霞元君庙、西顶庙",
        attested_string="廣仁宮",
    ),
    TextualFact(
        id="tf_hd_miaohui", division_id="div_hd_xiding",
        verbatim_quote="庙会每年正月初一至十五、四月初一至十五举行；庙外空地有戏楼，"
                       "火器营南门外街道形成市集；活动有进香、戏曲、舞狮、武术表演、"
                       "踩高跷、舞五虎棍、划旱船、花会",
        attested_string="廟會",
        translator_note="另有「四月初一至十八」一说，口播只说两段不混说",
    ),
    TextualFact(
        id="tf_hd_wuding", division_id="div_hd_xiding",
        verbatim_quote="北京五顶指环京郊五座碧霞元君庙：东顶在东直门外（1950年代毁）、"
                       "南顶在丰台大红门外、中顶在右安门外丰台中顶村（存，国保）、"
                       "北顶在朝阳区奥林匹克公园西南角（存，国保）；"
                       "五顶中唯一在海淀者为西顶",
        attested_string="五頂",
        translator_note="「五顶之首」「等级最高」「旧京八顶中的五顶」三处均无史料"
                        "依据，一律不用；另有「五顶八庙」泛称",
    ),
    TextualFact(
        id="tf_hd_lima", division_id="div_hd_fusi",
        verbatim_quote="立马关帝庙清光绪年间建于蓝靛厂南大街东头、临长河；山门内"
                       "塑关羽坐骑赤兔马，立马姿态而得名；正殿屋顶绿色琉璃瓦",
        attested_string="立馬關帝廟",
    ),
    TextualFact(
        id="tf_hd_qingzhensi", division_id="div_hd_fusi",
        verbatim_quote="蓝靛厂清真寺约建于明万历年间，是海淀区现存清真寺中最早的"
                       "一座；2006年10月开工重建，2009年10月21日落成",
        attested_string="清真寺",
    ),
]


# ==================================================================
# 3. 实体（只承载身份，不带任何可见属性）
# ==================================================================

ENTITIES: List[PersistentSpatialEntity] = [
    # ---- E5 一亩园 ----
    PersistentSpatialEntity(id="ent_yimuyuan", kind=PhysicalThingKind.SETTLEMENT_AREA,
                            canonical_label="一亩园"),
    PersistentSpatialEntity(id="ent_shanmianhu", kind=PhysicalThingKind.HUMAN_MADE_CHANNEL,
                            canonical_label="扇面湖（乾隆间疏浚人工湖，旧称前湖）"),
    PersistentSpatialEntity(id="ent_niangniangmiao", kind=PhysicalThingKind.RELIGIOUS_PRECINCT,
                            canonical_label="一亩园娘娘庙（泰山圣母庙）"),
    # ---- E10 蓝靛厂 ----
    PersistentSpatialEntity(id="ent_landianchang", kind=PhysicalThingKind.SETTLEMENT_AREA,
                            canonical_label="蓝靛厂"),
    PersistentSpatialEntity(id="ent_waihuoqiying", kind=PhysicalThingKind.FORTIFIED_CAMP,
                            canonical_label="外火器营营房（蓝靛厂）"),
    PersistentSpatialEntity(id="ent_xiding", kind=PhysicalThingKind.RELIGIOUS_PRECINCT,
                            canonical_label="西顶娘娘庙（广仁宫）"),
    PersistentSpatialEntity(id="ent_limaguandi", kind=PhysicalThingKind.RELIGIOUS_PRECINCT,
                            canonical_label="立马关帝庙"),
    PersistentSpatialEntity(id="ent_qingzhensi", kind=PhysicalThingKind.RELIGIOUS_PRECINCT,
                            canonical_label="蓝靛厂清真寺"),
]


# ==================================================================
# 4. 历时状态（每条状态：纪年挂靠 + evidence_fact_ids 溯源）
# ==================================================================

STATES: List[HistoricalFeatureState] = [
    # ---- E5 一亩园：图档首证 1792；雍正年代无任何状态（亲耕传说无档） ----
    HistoricalFeatureState(
        id="st_yim_1792", entity_id="ent_yimuyuan",
        time_span=_ts(1792, 1859, "ts_yim_a"),
        geometry="《八旬万寿盛典》图绘：建筑院落、道路、水渠、土山的复杂建筑区域"
                 "（L1 图证空间形态）",
        material="院落、土山、水渠",
        function="圆明园大宫门前附属院落、后勤及公务人员临时住舍"
                 "（L2 功能解释，与图档分开标，不混说「图证明宿舍」）",
        evidence_fact_ids=["tf_bx_tu", "tf_hd_func"],
    ),
    HistoricalFeatureState(
        id="st_yim_1860", entity_id="ent_yimuyuan",
        time_span=_ts(1860, 1911, "ts_yim_b"),
        geometry="圆明园及其附属园囿遭焚毁，一亩园区域院落俱损",
        function="毁损后荒废（毁损≠消亡；地点持续体见身份断言）",
        evidence_fact_ids=["tf_smh_1860"],
    ),
    HistoricalFeatureState(
        id="st_yim_minguo", entity_id="ent_yimuyuan",
        time_span=_ts(1912, 1949, "ts_yim_c"),
        geometry="随土地开垦形成的村落",
        function="民国村落层（与清代地名、现代社区三层分开，不画等号）",
        evidence_fact_ids=["tf_hd_minguo"],
    ),
    HistoricalFeatureState(
        id="st_yim_modern", entity_id="ent_yimuyuan",
        time_span=_ts(1950, 2026, "ts_yim_d"),
        geometry="现代社区",
        function="现代社区层（清代地名「一亩园」的当代延续）",
        evidence_fact_ids=["tf_hd_minguo"],
    ),
    # ---- E5 扇面湖：1763 成湖 → 稻田 → 2000 填埋 → 2024 春夏复湖 ----
    HistoricalFeatureState(
        id="st_smh_1763", entity_id="ent_shanmianhu",
        time_span=_ts(1763, 1859, "ts_smh_a"),
        geometry="乾隆二十八年（1763）疏浚成湖，旧称前湖，御道穿湖形似宫扇",
        material="湖面与御道",
        function="御路景观水面（疏浚人工湖，非天然水道）",
        evidence_fact_ids=["tf_smh_1763"],
    ),
    HistoricalFeatureState(
        id="st_smh_1860", entity_id="ent_shanmianhu",
        time_span=_ts(1860, 1999, "ts_smh_b"),
        geometry="园毁后淤废，渐辟为稻田",
        function="农田水面（毁损后转型，非消亡）",
        evidence_fact_ids=["tf_smh_1860"],
    ),
    HistoricalFeatureState(
        id="st_smh_2000", entity_id="ent_shanmianhu",
        time_span=_ts(2000, 2023, "ts_smh_c"),
        geometry="故址填埋，建农贸市场",
        function="市场用地",
        evidence_fact_ids=["tf_smh_2000"],
    ),
    HistoricalFeatureState(
        id="st_smh_2024", entity_id="ent_shanmianhu",
        time_span=_ts(2024, 2026, "ts_smh_d"),
        geometry="复挖3.2万平方米湖面、560米亲水步道、18.62公顷绿化；"
                 "地下遗迹覆土保护",
        function="2024年春夏建成并对公众开放；御道、水系、植物为展示性恢复，"
                 "非原样复建（不锁月日：5月开放与6月竣工两种官方口径并存）",
        evidence_fact_ids=["tf_smh_2024"],
    ),
    # ---- E5 一亩园娘娘庙：康熙重建（具体年份无考）→ 光绪再建 → 现存 ----
    HistoricalFeatureState(
        id="st_nm_kangxi", entity_id="ent_niangniangmiao",
        time_span=TimeSpan(id="ts_nm_a", label="康熙重建-1859",
                           begin=_dt(1662, "ts_nm_ab",
                                     _ry(Era.QING, "康熙", 1, "康熙元年"),
                                     precision="approximate"),
                           end=_dt(1859, "ts_nm_ae")),
        geometry="泰山圣母庙（碧霞元君系统），乾隆晚期图档已见扇面湖西岸娘娘庙",
        material="庙宇砖木",
        function="较可靠资料记康熙重建（具体年份无考，起点取康熙元年下限，"
                 "approximate）；光绪年间再建（非始建）",
        evidence_fact_ids=["tf_nm_kangxi"],
    ),
    HistoricalFeatureState(
        id="st_nm_guangxu", entity_id="ent_niangniangmiao",
        time_span=_ts(1875, 1911, "ts_nm_b"),
        geometry="光绪年间再建；御前掌玺太监刘诚连在庙西置四合院与菜园（L3钩子）",
        material="庙宇砖木",
        function="再建/重修（刘诚连若参与营建只能表述为再建/重修，非始建）",
        evidence_fact_ids=["tf_nm_guangxu"],
    ),
    HistoricalFeatureState(
        id="st_nm_modern", entity_id="ent_niangniangmiao",
        time_span=_ts(1912, 2026, "ts_nm_c"),
        geometry="三路院落现存中路后半：前殿关圣帝君、后殿九天娘娘",
        function="2014年8月公布为海淀区区级文物保护单位",
        evidence_fact_ids=["tf_nm_2014"],
    ),
    # ---- E10 蓝靛厂：染料植物（永乐间）早于厂名约170年 ----
    HistoricalFeatureState(
        id="st_ldc_yongle", entity_id="ent_landianchang",
        time_span=TimeSpan(id="ts_ldc_a", label="明永乐年间起种蓝靛",
                           begin=_dt(1403, "ts_ldc_ab",
                                     _ry(Era.MING, "永乐", 1, "明永乐年间"),
                                     precision="approximate"),
                           end=_dt(1521, "ts_ldc_ae")),
        geometry="洼水清，种植蓼蓝、山蓝等染料植物",
        function="蓝靛生产原料种植（「宫内派人」表述证据不足已删；具体年份不给）",
        evidence_fact_ids=["tf_hd_ldc_yongle"],
    ),
    HistoricalFeatureState(
        id="st_ldc_ming", entity_id="ent_landianchang",
        time_span=TimeSpan(id="ts_ldc_b", label="明代中后期靛园厂-1644",
                           begin=_dt(1522, "ts_ldc_bb",
                                     _ry(Era.MING, "嘉靖", 1, "明代中后期（嘉靖起）"),
                                     precision="approximate"),
                           end=_dt(1644, "ts_ldc_be")),
        geometry="作坊区，初名靛园厂",
        function="明内府织染局外署：皇宫大内宫廷官署、由宦官掌控（非民间染坊）；"
                 "后因专产青蓝色染料改称「蓝靛厂」——地名记录的是官署设立那一刻，"
                 "是行政的产物不是自然的产物",
        evidence_fact_ids=["tf_hd_dingyuanchang", "tf_dmhnd_zhiran"],
    ),
    HistoricalFeatureState(
        id="st_ldc_qing", entity_id="ent_landianchang",
        time_span=_ts(1644, 1911, "ts_ldc_c"),
        geometry="京西驻防重地与庙市街：外火器营驻此，西顶庙会（火器营南门外街道"
                 "形成市集），另有立马关帝庙、清真寺",
        function="外火器营驻地与庙市街（京旗外三营互为犄角，蓝靛厂东临昆玉河、"
                 "北接颐和园，自是要冲）",
        evidence_fact_ids=["tf_wjbz_qianjian", "tf_hd_miaohui", "tf_hd_jingqi"],
    ),
    HistoricalFeatureState(
        id="st_ldc_modern", entity_id="ent_landianchang",
        time_span=_ts(1912, 2026, "ts_ldc_d"),
        geometry="今北京最堵的路口之一；火器营站（地铁10号线）、老营房路、"
                 "火器营桥、横街、永山宅院等地名沿用",
        function="地名留存层（一条街三层历史的当代遗产）",
        evidence_fact_ids=["tf_hd_metro", "tf_wjbz_zongji"],
    ),
    # ---- E10 外火器营：1770 奏请迁建 → 1773 基本建成 → 地名留存 ----
    HistoricalFeatureState(
        id="st_wai_1770", entity_id="ent_waihuoqiying",
        time_span=_ts(1770, 1772, "ts_wai_a"),
        geometry="乾隆三十五年（1770）奏请迁建城西蓝靛厂，营房营建中",
        function="外火器营迁建期：动因是兵制与空间（城内分驻操练不便、火器制造与"
                 "操练需要大片空间），不是军事形势突变",
        evidence_fact_ids=["tf_wjbz_qianjian"],
    ),
    HistoricalFeatureState(
        id="st_wai_1773", entity_id="ent_waihuoqiying",
        time_span=_ts(1773, 1911, "ts_wai_b"),
        geometry="营区沿西北—东南走向河道（今昆玉河一线）而建，轮廓不规范；"
                 "八旗翼长官廊建在西门外，营区内建关帝庙7座（各旗所建）",
        material="官廨1024间、官办义学等60间、炮甲连房6038间、周围门楼3176座"
                 "（《日下旧闻考》）、水井16眼、水房16间、泄水沟25道（分项记载；"
                 "总数不给，见命题层）",
        function="外火器营建成驻防：全营专习枪炮（鸟枪、子母炮），由总统大臣统辖，"
                 "负责守卫皇城；1773 为研究结论口径，非《清史稿》直接记载",
        evidence_fact_ids=["tf_rxjwkc_menlou", "tf_wjbz_qianjian", "tf_qsg_guanzhi"],
    ),
    HistoricalFeatureState(
        id="st_wai_1912", entity_id="ent_waihuoqiying",
        time_span=_ts(1912, 2026, "ts_wai_c"),
        geometry="营区建筑无存",
        function="营制终结后地名大量留存：火器营站、老营房路、火器营桥、横街、"
                 "永山宅院——有形的消失与无形的消失（毁损≠消亡）",
        evidence_fact_ids=["tf_wjbz_zongji", "tf_hd_metro"],
    ),
    # ---- E10 西顶娘娘庙：1608 始建 → 1712 改称广仁宫 → 现存 ----
    HistoricalFeatureState(
        id="st_xd_1608", entity_id="ent_xiding",
        time_span=_ts(1608, 1711, "ts_xd_a"),
        geometry="明万历三十六年（1608）于蓝靛厂始建，称护国洪蕊宫（一说洪慈宫）",
        material="庙宇砖木",
        function="北京五顶之一的碧霞元君庙（西顶）",
        evidence_fact_ids=["tf_zzz_xiding", "tf_hd_xiding_yange"],
    ),
    HistoricalFeatureState(
        id="st_xd_1712", entity_id="ent_xiding",
        time_span=_ts(1712, 1911, "ts_xd_b"),
        geometry="清康熙五十一年（1712）改称广仁宫碧霞元君庙",
        material="庙宇砖木，碑记载官帑修葺",
        function="京西香火最盛的碧霞元君古刹：庙会正月初一至十五、四月初一至十五，"
                 "庙外有戏楼，火器营南门外街道形成市集——庙反而是庙会的配角",
        evidence_fact_ids=["tf_hd_xiding_yange", "tf_xdb_hui", "tf_hd_miaohui"],
    ),
    HistoricalFeatureState(
        id="st_xd_modern", entity_id="ent_xiding",
        time_span=_ts(1912, 2026, "ts_xd_c"),
        geometry="现存，位于海淀区西顶路（四季青蓝靛厂），紧邻世纪金源时代购物中心",
        function="五顶中唯一在海淀、唯一现存且紧邻清代军事营房的一座"
                 "（特殊处不在等级，在位置）",
        evidence_fact_ids=["tf_hd_wuding"],
    ),
    # ---- E10 立马关帝庙 ----
    HistoricalFeatureState(
        id="st_lmgd_guangxu", entity_id="ent_limaguandi",
        time_span=TimeSpan(id="ts_lmgd_a", label="清光绪年间-2026",
                           begin=_dt(1875, "ts_lmgd_ab",
                                     _ry(Era.QING, "光绪", 1, "清光绪年间"),
                                     precision="approximate"),
                           end=_dt(2026, "ts_lmgd_ae")),
        geometry="蓝靛厂南大街东头、临长河（昆玉河）；座北朝南，山门内塑关羽坐骑"
                 "赤兔马（立马姿态、全身枣红）",
        material="正殿屋顶绿色琉璃瓦，有走兽、凸花盘龙瓦当",
        function="关帝庙（与西顶、清真寺同街并存：佛道、儒释、伊斯兰三套体系）",
        evidence_fact_ids=["tf_hd_lima"],
    ),
    # ---- E10 蓝靛厂清真寺 ----
    HistoricalFeatureState(
        id="st_qzs_wanli", entity_id="ent_qingzhensi",
        time_span=TimeSpan(id="ts_qzs_a", label="明万历年间始建-2005",
                           begin=_dt(1573, "ts_qzs_ab",
                                     _ry(Era.MING, "万历", 1, "明万历年间"),
                                     precision="approximate"),
                           end=_dt(2005, "ts_qzs_ae")),
        geometry="清真寺",
        function="海淀区现存清真寺中最早的一座（约建于明万历年间）",
        evidence_fact_ids=["tf_hd_qingzhensi"],
    ),
    HistoricalFeatureState(
        id="st_qzs_2009", entity_id="ent_qingzhensi",
        time_span=_ts(2009, 2026, "ts_qzs_b"),
        geometry="2006年10月开工重建，2009年10月21日落成",
        function="重建落成后的清真寺",
        evidence_fact_ids=["tf_hd_qingzhensi"],
    ),
]


# ==================================================================
# 5. 身份断言
# ==================================================================

IDENTITIES: List[DiachronicIdentityAssertion] = [
    # 【E5 核心】一亩园地点持续体：清代地名/民国村落/现代社区三层不可画等号
    DiachronicIdentityAssertion(
        id="dia_yimuyuan_sanceng",
        subject_entity_ids=["ent_yimuyuan"],
        relation=IdentityRelation.SAME_CONTINUANT,
        time_span=_ts(1792, 2026, "ts_di1"),
        evidence_fact_ids=["tf_bx_tu", "tf_hd_minguo"],
        status=EpistemicStatus.VERIFIED,
        alternative_relations=[
            "清代附属院落地名 → 民国垦殖村落 → 现代社区，三层社会身份不可画等号"
            "（圆明园管理处研究）",
            "地点为同一持续体，但各层功能全变（身份延续与属性变化正交）",
        ],
    ),
    # 西顶：护国洪蕊宫→广仁宫为同一庙改称
    DiachronicIdentityAssertion(
        id="dia_xiding_gaicheng",
        subject_entity_ids=["ent_xiding"],
        relation=IdentityRelation.SAME_CONTINUANT,
        time_span=_ts(1608, 2026, "ts_di2"),
        evidence_fact_ids=["tf_zzz_xiding", "tf_hd_xiding_yange"],
        status=EpistemicStatus.VERIFIED,
        alternative_relations=[
            "护国洪蕊宫（1608）→广仁宫碧霞元君庙（1712改称）为同一庙改称",
            "殿名「洪蕊宫/洪慈宫」两说并存，口播说「洪蕊宫（另有说洪慈宫）」或不提",
        ],
    ),
    # 【E10 核心】火器营分内外两营：外营迁蓝靛厂；营区毁损≠地名消亡
    DiachronicIdentityAssertion(
        id="dia_waiying_neiwai_split",
        subject_entity_ids=["ent_waihuoqiying"],
        relation=IdentityRelation.SPLIT,
        time_span=_ts(1770, 2026, "ts_di3"),
        evidence_fact_ids=["tf_hd_neiwai", "tf_wjbz_qianjian"],
        status=EpistemicStatus.VERIFIED,
        alternative_relations=[
            "火器营分内外两营：内营驻城内（枪营、炮营），外营迁蓝靛厂；"
            "本词条只入库外营",
            "「内/外」是城内/城外，不是方位褒贬",
            "营区建筑毁损后，地名（火器营站/桥/路）延续地点指称——毁损≠消亡",
        ],
    ),
]


# ==================================================================
# 6. 名称与指称
# ==================================================================

APPELLATIONS: List[Appellation] = [
    # ---- E5 ----
    Appellation(id="app_yimuyuan", label="一亩园", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1736, 2026, "ts_n1"),
                attesting_fact_ids=["tf_bx_tu", "tf_hd_minguo"]),
    Appellation(id="app_qianhu", label="前湖", kind=AppellationKind.OLD_NAME,
                valid_time_span=TimeSpan(id="ts_n2", label="旧称，至1763疏浚得名前",
                                         open_begin=True, begin=None,
                                         end=_dt(1762, "ts_n2e")),
                attesting_fact_ids=["tf_smh_1763"]),
    Appellation(id="app_shanmianhu", label="扇面湖", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1763, 2026, "ts_n3"),
                attesting_fact_ids=["tf_smh_1763"]),
    Appellation(id="app_niangniangmiao", label="一亩园娘娘庙",
                kind=AppellationKind.OFFICIAL,
                valid_time_span=TimeSpan(id="ts_n4", label="康熙重建以来",
                                         begin=_dt(1662, "ts_n4b",
                                                   _ry(Era.QING, "康熙", 1, "康熙元年"),
                                                   precision="approximate"),
                                         end=_dt(2026, "ts_n4e")),
                attesting_fact_ids=["tf_nm_kangxi"]),
    Appellation(id="app_taishan_shengmu", label="泰山圣母庙", kind=AppellationKind.VULGAR,
                valid_time_span=TimeSpan(id="ts_n5", label="依主神俗称",
                                         begin=_dt(1662, "ts_n5b",
                                                   _ry(Era.QING, "康熙", 1, "康熙元年"),
                                                   precision="approximate"),
                                         end=_dt(2026, "ts_n5e")),
                attesting_fact_ids=["tf_nm_kangxi"]),
    # ---- E10 ----
    Appellation(id="app_landianchang", label="蓝靛厂", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1522, 2026, "ts_n6"),
                attesting_fact_ids=["tf_hd_dingyuanchang"]),
    Appellation(id="app_dingyuanchang", label="靛园厂", kind=AppellationKind.OLD_NAME,
                valid_time_span=_ts(1522, 1644, "ts_n7"),
                attesting_fact_ids=["tf_hd_dingyuanchang"]),
    Appellation(id="app_waihuoqiying", label="外火器营", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1770, 2026, "ts_n8"),
                attesting_fact_ids=["tf_wjbz_qianjian", "tf_wjbz_zongji"]),
    Appellation(id="app_huoqiying", label="火器营", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1770, 2026, "ts_n9"),
                attesting_fact_ids=["tf_wjbz_zongji", "tf_hd_metro"]),
    Appellation(id="app_huoqiyingzhan", label="火器营站", kind=AppellationKind.STATION_NAME,
                valid_time_span=TimeSpan(id="ts_n10", label="今名",
                                         open_begin=True, begin=None,
                                         end=_dt(2026, "ts_n10e")),
                attesting_fact_ids=["tf_hd_metro"]),
    Appellation(id="app_xiding", label="西顶娘娘庙", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1608, 2026, "ts_n11"),
                attesting_fact_ids=["tf_zzz_xiding"]),
    Appellation(id="app_hongrui", label="护国洪蕊宫", kind=AppellationKind.OLD_NAME,
                valid_time_span=_ts(1608, 1711, "ts_n12"),
                attesting_fact_ids=["tf_hd_xiding_yange"]),
    Appellation(id="app_guangren", label="广仁宫", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1712, 2026, "ts_n13"),
                attesting_fact_ids=["tf_hd_xiding_yange"]),
    Appellation(id="app_limaguandi", label="立马关帝庙", kind=AppellationKind.OFFICIAL,
                valid_time_span=TimeSpan(id="ts_n14", label="清光绪年间以来",
                                         begin=_dt(1875, "ts_n14b",
                                                   _ry(Era.QING, "光绪", 1, "清光绪年间"),
                                                   precision="approximate"),
                                         end=_dt(2026, "ts_n14e")),
                attesting_fact_ids=["tf_hd_lima"]),
    Appellation(id="app_qingzhensi", label="蓝靛厂清真寺", kind=AppellationKind.OFFICIAL,
                valid_time_span=TimeSpan(id="ts_n15", label="明万历年间以来",
                                         begin=_dt(1573, "ts_n15b",
                                                   _ry(Era.MING, "万历", 1, "明万历年间"),
                                                   precision="approximate"),
                                         end=_dt(2026, "ts_n15e")),
                attesting_fact_ids=["tf_hd_qingzhensi"]),
]

REFERENCES: List[ReferentialAssertion] = [
    # ---- E5 ----
    ReferentialAssertion(id="rr_yimuyuan", appellation_id="app_yimuyuan",
                         referent_entity_id="ent_yimuyuan",
                         time_span=_ts(1736, 2026, "ts_r1"),
                         evidence_fact_ids=["tf_bx_tu", "tf_hd_minguo"]),
    ReferentialAssertion(id="rr_qianhu", appellation_id="app_qianhu",
                         referent_entity_id="ent_shanmianhu",
                         time_span=TimeSpan(id="ts_r2", label="旧称有效期",
                                            open_begin=True, begin=None,
                                            end=_dt(1762, "ts_r2e")),
                         evidence_fact_ids=["tf_smh_1763"]),
    ReferentialAssertion(id="rr_shanmianhu", appellation_id="app_shanmianhu",
                         referent_entity_id="ent_shanmianhu",
                         time_span=_ts(1763, 2026, "ts_r3"),
                         evidence_fact_ids=["tf_smh_1763"]),
    ReferentialAssertion(id="rr_niangniangmiao", appellation_id="app_niangniangmiao",
                         referent_entity_id="ent_niangniangmiao",
                         time_span=TimeSpan(id="ts_r4", label="康熙重建以来",
                                            begin=_dt(1662, "ts_r4b",
                                                      _ry(Era.QING, "康熙", 1, "康熙元年"),
                                                      precision="approximate"),
                                            end=_dt(2026, "ts_r4e")),
                         evidence_fact_ids=["tf_nm_kangxi", "tf_nm_2014"]),
    ReferentialAssertion(id="rr_taishan_shengmu", appellation_id="app_taishan_shengmu",
                         referent_entity_id="ent_niangniangmiao",
                         time_span=TimeSpan(id="ts_r5", label="依主神俗称",
                                            begin=_dt(1662, "ts_r5b",
                                                      _ry(Era.QING, "康熙", 1, "康熙元年"),
                                                      precision="approximate"),
                                            end=_dt(2026, "ts_r5e")),
                         evidence_fact_ids=["tf_nm_kangxi"]),
    # ---- E10 ----
    ReferentialAssertion(id="rr_landianchang", appellation_id="app_landianchang",
                         referent_entity_id="ent_landianchang",
                         time_span=_ts(1522, 2026, "ts_r6"),
                         evidence_fact_ids=["tf_hd_dingyuanchang"]),
    ReferentialAssertion(id="rr_dingyuanchang", appellation_id="app_dingyuanchang",
                         referent_entity_id="ent_landianchang",
                         time_span=_ts(1522, 1644, "ts_r7"),
                         evidence_fact_ids=["tf_hd_dingyuanchang"]),
    ReferentialAssertion(id="rr_waihuoqiying", appellation_id="app_waihuoqiying",
                         referent_entity_id="ent_waihuoqiying",
                         time_span=_ts(1770, 2026, "ts_r8"),
                         evidence_fact_ids=["tf_wjbz_qianjian", "tf_wjbz_zongji"]),
    ReferentialAssertion(id="rr_huoqiying", appellation_id="app_huoqiying",
                         referent_entity_id="ent_waihuoqiying",
                         time_span=_ts(1770, 2026, "ts_r9"),
                         evidence_fact_ids=["tf_wjbz_zongji", "tf_hd_metro"],
                         provenance="「火器营」今名指蓝靛厂外营故地（火器营站/桥/路）；"
                                    "1691—1769 建制期部队无独立空间实体入库，"
                                    "组建年份链见 prop_huoqiying_year_chain"),
    ReferentialAssertion(id="rr_huoqiyingzhan", appellation_id="app_huoqiyingzhan",
                         referent_entity_id="ent_waihuoqiying",
                         time_span=TimeSpan(id="ts_r10", label="今名",
                                            open_begin=True, begin=None,
                                            end=_dt(2026, "ts_r10e")),
                         evidence_fact_ids=["tf_hd_metro"]),
    ReferentialAssertion(id="rr_xiding", appellation_id="app_xiding",
                         referent_entity_id="ent_xiding",
                         time_span=_ts(1608, 2026, "ts_r11"),
                         evidence_fact_ids=["tf_zzz_xiding", "tf_hd_wuding"]),
    ReferentialAssertion(id="rr_hongrui", appellation_id="app_hongrui",
                         referent_entity_id="ent_xiding",
                         time_span=_ts(1608, 1711, "ts_r12"),
                         evidence_fact_ids=["tf_hd_xiding_yange"]),
    ReferentialAssertion(id="rr_guangren", appellation_id="app_guangren",
                         referent_entity_id="ent_xiding",
                         time_span=_ts(1712, 2026, "ts_r13"),
                         evidence_fact_ids=["tf_hd_xiding_yange"]),
    ReferentialAssertion(id="rr_limaguandi", appellation_id="app_limaguandi",
                         referent_entity_id="ent_limaguandi",
                         time_span=TimeSpan(id="ts_r14", label="清光绪年间以来",
                                            begin=_dt(1875, "ts_r14b",
                                                      _ry(Era.QING, "光绪", 1, "清光绪年间"),
                                                      precision="approximate"),
                                            end=_dt(2026, "ts_r14e")),
                         evidence_fact_ids=["tf_hd_lima"]),
    ReferentialAssertion(id="rr_qingzhensi", appellation_id="app_qingzhensi",
                         referent_entity_id="ent_qingzhensi",
                         time_span=TimeSpan(id="ts_r15", label="明万历年间以来",
                                            begin=_dt(1573, "ts_r15b",
                                                      _ry(Era.MING, "万历", 1, "明万历年间"),
                                                      precision="approximate"),
                                            end=_dt(2026, "ts_r15e")),
                         evidence_fact_ids=["tf_hd_qingzhensi"]),
]


# ==================================================================
# 7. 断言与采信：把交付档案的降格结论固化（传说/研究/史实绝不混级）
# ==================================================================

PROPOSITIONS: List[Proposition] = [
    # ---- E5 核心反转：先农坛才是礼制地点，一亩园只有传说 ----
    Proposition(
        id="prop_yimuyuan_not_jitian",
        statement="一亩园不是皇帝亲耕耤田礼场所：明清皇帝正式亲耕耤田礼（真正的"
                  "「一亩三分地」）在先农坛（L1 礼制史实）；一亩园只有民间亲耕"
                  "传说（「雍正帝演耕处」，官方明确「缺少依据」）——传说（L5）与"
                  "官方研究（L2）严格分层，先农坛才是礼制地点",
        derived_from_fact_ids=["tf_hd_yanzheng"],
        inferred_subject_id="ent_yimuyuan",
        inference_method="官方口径（北京日报·海淀发布2024-06，转载按原作者层级计"
                         "L2）明言传说缺少依据；本库 ent_yimuyuan 首证状态为 1792 "
                         "图档，雍正年代无任何有据状态——亲耕断言在审计层不可判通过",
        alternative_explanations=[
            "民间传说：雍正帝演耕处（L5，官方明确缺少依据）",
            "旅游文案：亲耕/亲蚕之说（L4/L5，仅传说层）",
        ],
    ),
    Proposition(
        id="prop_baxun_tu_vs_func",
        statement="《八旬万寿盛典》图档证明的是空间形态（建筑院落、道路、水渠、"
                  "土山）；「圆明园大宫门前附属院落、后勤及公务人员临时住舍」是"
                  "现代官方研究的功能解释（L2）——图证空间、研究释功能，"
                  "两层不得混说为「图证明官员宿舍」",
        derived_from_fact_ids=["tf_bx_tu", "tf_hd_func"],
        inferred_subject_id="ent_yimuyuan",
        inference_method="图档（L1）与功能解释（L2）分挂两个事实节点，物理分层",
        alternative_explanations=[
            "最严谨反转句（采用）：图档没有呈现一个孤零零的皇帝亲耕田，呈现的却是"
            "一整片密集的圆明园宫门前附属空间",
        ],
    ),
    Proposition(
        id="prop_dagongmen_zhengdian",
        statement="大宫门是圆明园正门；正大光明是入大宫门、过二宫门后的正殿——"
                  "二者非同一建筑，禁写「正大光明门（大宫门）」",
        derived_from_fact_ids=["tf_hd_func"],
        inferred_subject_id="ent_yimuyuan",
        inference_method="圆明园管理处研究（L2）建筑序列：门—二宫门—正殿",
        alternative_explanations=[],
    ),
    Proposition(
        id="prop_liuchenglian_rejian",
        statement="一亩园娘娘庙始建链：较可靠资料记康熙重建、光绪再建；太监刘诚连"
                  "（L3）若参与营建只能表述为「再建/重修」，非「始建」；始建链"
                  "证据薄，不承担核心张力",
        derived_from_fact_ids=["tf_nm_kangxi", "tf_nm_guangxu"],
        inferred_subject_id="ent_niangniangmiao",
        inference_method="官方再建记载（L2）与晚报文史（L3）分层；「始建」与"
                         "「再建」是两个断言强度",
        alternative_explanations=[
            "刘诚连始建说（证据不足，不采）",
        ],
    ),
    Proposition(
        id="prop_shanmianhu_chunxia",
        statement="扇面湖2024年建成开放不锁月日：「2024年5月开放」与「2024年6月"
                  "竣工」两种官方口径并存，统一表述「2024年春夏建成并对公众开放」",
        derived_from_fact_ids=["tf_smh_2024"],
        inferred_subject_id="ent_shanmianhu",
        inference_method="两种官方口径并存时不取单月，取并集时段",
        alternative_explanations=[],
    ),
    Proposition(
        id="prop_shanmianhu_counts",
        statement="扇面湖历史层累按四段重排：1763疏浚成湖→1860园毁后渐为稻田→"
                  "2000填埋建农贸市场→2024春夏复湖开放；不凑「260年五次变身」之数",
        derived_from_fact_ids=["tf_smh_1763", "tf_smh_1860", "tf_smh_2000",
                               "tf_smh_2024"],
        inferred_subject_id="ent_shanmianhu",
        inference_method="按可证状态分段计数，不为修辞凑数",
        alternative_explanations=[],
    ),
    # ---- E10 核心纠错：火器营 ----
    Proposition(
        id="prop_huoqiying_year_chain",
        statement="火器营年份链：康熙二十七年(1688)设汉军火器兼练大刀营（前身）→"
                  "康熙三十年(1691)始设火器营→乾隆三十五年(1770)色布腾巴勒珠尔"
                  "奏请迁建蓝靛厂→乾隆三十八年(1773)营区基本建成——四个年份不得"
                  "混用，「外火器营建于乾隆三十五年」作起点是通行错讹（漏掉1691）",
        derived_from_fact_ids=["tf_qsg_dadao", "tf_qsg_shehuoqi", "tf_qsg_guanzhi",
                               "tf_wjbz_qianjian"],
        inferred_subject_id="ent_waihuoqiying",
        inference_method="《清史稿·职官志》逐条系年 + 文物局公开资料口径；"
                         "1688 与 1691 是同一支部队的改名，不是重复记载",
        alternative_explanations=[
            "「乾隆三十五年建」通行说法（作起点即漏掉1691组建，弃）",
        ],
    ),
    Proposition(
        id="prop_huoqiying_not_fire",
        statement="火器营不是放火的营：清代八旗中专习枪炮的专业部队，操演有鸟枪"
                  "亦有子母炮（后膛装填，源自明代由西班牙传入的佛朗机），性质近似"
                  "明朝神机营，由总统大臣统辖、负责守卫皇城",
        derived_from_fact_ids=["tf_qsg_shehuoqi", "tf_qsg_guanzhi"],
        inferred_subject_id="ent_waihuoqiying",
        inference_method="编制与装备记载（鸟枪/子母炮/守卫皇城）直接否定"
                         "「放火」望文生义",
        alternative_explanations=[],
    ),
    Proposition(
        id="prop_neiwai_ying",
        statement="火器营分内外两营：内火器营驻北京城内设枪营、炮营；外火器营建于"
                  "西郊蓝靛厂——「内/外」是城内/城外，不是方位褒贬",
        derived_from_fact_ids=["tf_hd_neiwai"],
        inferred_subject_id="ent_waihuoqiying",
        inference_method="建制记载直接给出两营驻地面",
        alternative_explanations=[],
    ),
    Proposition(
        id="prop_fangcao_fenxiang",
        statement="营房规模只报分项：官廨1024间、官办义学等60间、炮甲连房6038间、"
                  "周围门楼3176座（《日下旧闻考》）、水井16眼、水房16间、泄水沟"
                  "25道；「营房共7196间」系分项相加、非史料原文，禁用；「营房四千"
                  "余间」查无实据，点破时说「常见说法」；「近万间」等模糊总数一律不给",
        derived_from_fact_ids=["tf_rxjwkc_menlou"],
        inferred_subject_id="ent_waihuoqiying",
        inference_method="二手资料数字互相矛盾时不给总数，只报可查分项；"
                         "门楼3176座为《日下旧闻考》一手明文",
        alternative_explanations=[
            "说法二：各种营房、官房合计「1700多间」（与分项并存，不给总数）",
        ],
    ),
    Proposition(
        id="prop_guanying_not_minjian",
        statement="蓝靛厂不是民间染坊村：明代中后期设靛园厂，隶内府织染局——皇宫"
                  "大内宫廷官署、由宦官掌控；染蓝植物种植（明永乐年间起）早于厂名"
                  "约170年——地名记录的是官署设立那一刻，地名是行政的产物不是"
                  "自然的产物",
        derived_from_fact_ids=["tf_dmhnd_zhiran", "tf_hd_dingyuanchang",
                               "tf_hd_ldc_yongle"],
        inferred_subject_id="ent_landianchang",
        inference_method="织染局建制性质（官署/宦官）由《大明会典》制度记载判定；"
                         "「万历十五年（1587）」查无一手依据已删",
        alternative_explanations=[
            "民间染坊村说（与官署建制记载冲突，不采）",
        ],
    ),
    Proposition(
        id="prop_jingqi_waisanying",
        statement="京旗外三营＝圆明园护卫营＋香山健锐营＋蓝靛厂外火器营，全部位于"
                  "北京西北郊，互为犄角呈三角之势；清皇室每年大量时间在西郊行宫"
                  "（三山五园）度过，此地必须陈以重兵；蓝靛厂东临昆玉河、北接"
                  "颐和园，自是要冲",
        derived_from_fact_ids=["tf_hd_jingqi"],
        inferred_subject_id="ent_waihuoqiying",
        inference_method="三营位置与皇家园林群格局对照；选点是战略（兵制与空间），"
                         "不是随机的村落驻军",
        alternative_explanations=[],
    ),
    Proposition(
        id="prop_xiding_wuding",
        statement="西顶是北京五顶之一、京西著名的碧霞元君古刹，特殊处不在等级而在"
                  "位置：五顶中唯一在海淀、唯一现存且紧邻清代军事营房；「五顶之首」"
                  "「等级最高」「旧京八顶中的五顶」三处均无史料依据，一律不用"
                  "（另有「五顶八庙」泛称）",
        derived_from_fact_ids=["tf_hd_wuding", "tf_hd_xiding_yange"],
        inferred_subject_id="ent_xiding",
        inference_method="五顶方位逐一核对（东顶东直门外、南顶丰台大红门外、"
                         "中顶右安门外、北顶朝阳奥森），无任何「之首/最高」记载",
        alternative_explanations=[
            "「五顶之首」说（无史料依据，弃）",
        ],
    ),
    Proposition(
        id="prop_miaohui_riqi",
        statement="西顶庙会在正月初一至十五、四月初一至十五举行（日期只说这两段，"
                  "不与「至十八」混说）；庙外空地有戏楼、火器营南门外街道形成市集"
                  "——庙反而是庙会的配角",
        derived_from_fact_ids=["tf_hd_miaohui", "tf_xdb_hui"],
        inferred_subject_id="ent_xiding",
        inference_method="碑记（一手石刻）与公开资料互证；日期并存口径中取两段"
                         "通行表述",
        alternative_explanations=[
            "「四月初一至十八」一说（record 于事实层 note，口播不混说）",
        ],
    ),
    Proposition(
        id="prop_xiding_xianling_legend",
        statement="西顶碧霞元君显灵传说属民间传说层，只说「香火极盛」，"
                  "不展开具体故事",
        derived_from_fact_ids=[],
        inferred_subject_id="ent_xiding",
        inference_method="民俗流传，无档案；传说不入史实层",
        alternative_explanations=[
            "显灵传说群（民俗流传，无档）",
        ],
    ),
    Proposition(
        id="prop_hangchuan_legend",
        statement="「整座营房平面似一艘扬帆起航的航船（正黄旗与八旗档房如船舵、"
                  "正蓝旗关帝庙旗杆如船桅）」出自《北京西山健锐营》二手转述，属"
                  "民间传说级描述；若用须说「据说」，不做本集骨架",
        derived_from_fact_ids=[],
        inferred_subject_id="ent_waihuoqiying",
        inference_method="二手转述不承担骨架；营区轮廓不规范的结构性解释（沿河走向）"
                         "可代之",
        alternative_explanations=[
            "营区沿西北—东南走向河道而建，故轮廓极不规范（结构性解释）",
        ],
    ),
    Proposition(
        id="prop_zongji_vs_diming",
        statement="外火器营营区踪迹全无，但地名大量留存（横街、永山宅院、老营房路、"
                  "火器营桥、火器营站）；三营结局对比：健锐营留下的是建筑，火器营"
                  "留下的是名字——有形的消失与无形的消失",
        derived_from_fact_ids=["tf_wjbz_zongji", "tf_hd_metro"],
        inferred_subject_id="ent_waihuoqiying",
        inference_method="文物局考释原话 + 今名延续；「踪迹全无」指营区建筑，"
                         "不等于地名/地点消亡",
        alternative_explanations=[],
    ),
    Proposition(
        id="prop_yongshan_uncertain",
        statement="「永山大宅」与外火器营营区的关联仅部分资料有称，存疑待考，"
                  "本词条不展开",
        derived_from_fact_ids=[],
        inferred_subject_id="ent_waihuoqiying",
        inference_method="部分资料称永山大宅与营区相关，无一手档案确证",
        alternative_explanations=[
            "永山宅院作为地名留存（文物局考释提及，与营区关联未确证）",
        ],
    ),
]

ADOPTIONS: List[BeliefAdoption] = [
    BeliefAdoption(proposition_id="prop_yimuyuan_not_jitian",
                   status=EpistemicStatus.VERIFIED, confidence=0.9,
                   adopted_by="E5交付档案v2（冻结）",
                   rationale="官方明言传说缺少依据；礼制史实（耤田在先农坛）为"
                             "L1 级，与 L5 传说严格分层"),
    BeliefAdoption(proposition_id="prop_baxun_tu_vs_func",
                   status=EpistemicStatus.VERIFIED, confidence=0.9,
                   adopted_by="E5交付档案v2（冻结）",
                   rationale="图档与功能解释分属 L1/L2，分挂两个事实节点"),
    BeliefAdoption(proposition_id="prop_dagongmen_zhengdian",
                   status=EpistemicStatus.VERIFIED, confidence=0.9,
                   adopted_by="E5交付档案v2（冻结）",
                   rationale="门—二宫门—正殿建筑序列明确，二者非同一建筑"),
    BeliefAdoption(proposition_id="prop_liuchenglian_rejian",
                   status=EpistemicStatus.CONTESTED, confidence=0.6,
                   adopted_by="E5交付档案v2（冻结）",
                   rationale="康熙重建/光绪再建为较可靠记载；刘诚连条为 L3 文史，"
                             "只可表述再建/重修"),
    BeliefAdoption(proposition_id="prop_shanmianhu_chunxia",
                   status=EpistemicStatus.VERIFIED, confidence=0.9,
                   adopted_by="E5交付档案v2（冻结）",
                   rationale="5月开放与6月竣工两种官方口径并存，取「春夏」并集"),
    BeliefAdoption(proposition_id="prop_shanmianhu_counts",
                   status=EpistemicStatus.VERIFIED, confidence=0.9,
                   adopted_by="E5交付档案v2（冻结）",
                   rationale="四段各有独立证据，重排计数不为修辞凑数"),
    BeliefAdoption(proposition_id="prop_huoqiying_year_chain",
                   status=EpistemicStatus.VERIFIED, confidence=0.9,
                   adopted_by="E10交付档案v1（GPT闸门采纳）",
                   rationale="《清史稿·职官志》逐条系年；1688/1691/1770/1773 "
                             "四年份不得混用"),
    BeliefAdoption(proposition_id="prop_huoqiying_not_fire",
                   status=EpistemicStatus.VERIFIED, confidence=0.95,
                   adopted_by="E10交付档案v1（GPT闸门采纳）",
                   rationale="编制装备记载直接否定望文生义；专习枪炮的专业部队"),
    BeliefAdoption(proposition_id="prop_neiwai_ying",
                   status=EpistemicStatus.VERIFIED, confidence=0.9,
                   adopted_by="E10交付档案v1（GPT闸门采纳）",
                   rationale="建制记载明确两营驻地；内外是城内/城外"),
    BeliefAdoption(proposition_id="prop_fangcao_fenxiang",
                   status=EpistemicStatus.VERIFIED, confidence=0.9,
                   adopted_by="E10交付档案v1（GPT闸门采纳）",
                   rationale="7196 为分项相加非史料原文；四千余间查无实据；只报分项"),
    BeliefAdoption(proposition_id="prop_guanying_not_minjian",
                   status=EpistemicStatus.VERIFIED, confidence=0.85,
                   adopted_by="E10交付档案v1（GPT闸门采纳）",
                   rationale="织染局为宫廷官署（宦官掌控）；厂名晚于物产约170年"),
    BeliefAdoption(proposition_id="prop_jingqi_waisanying",
                   status=EpistemicStatus.VERIFIED, confidence=0.85,
                   adopted_by="E10交付档案v1（GPT闸门采纳）",
                   rationale="三营犄角格局与三山五园重兵逻辑互证"),
    BeliefAdoption(proposition_id="prop_xiding_wuding",
                   status=EpistemicStatus.VERIFIED, confidence=0.9,
                   adopted_by="E10交付档案v1（GPT闸门采纳·重要更正）",
                   rationale="五顶方位逐一核对；「之首/最高/八顶」均无史料依据已删"),
    BeliefAdoption(proposition_id="prop_miaohui_riqi",
                   status=EpistemicStatus.VERIFIED, confidence=0.85,
                   adopted_by="E10交付档案v1（GPT闸门采纳）",
                   rationale="碑记一手石刻与公开资料互证；日期两段通行表述"),
    BeliefAdoption(proposition_id="prop_xiding_xianling_legend",
                   status=EpistemicStatus.FOLK_LEGEND, confidence=0.3,
                   adopted_by="E10交付档案v1（GPT闸门采纳）",
                   rationale="显灵传说为民俗流传，只说香火极盛不展开"),
    BeliefAdoption(proposition_id="prop_hangchuan_legend",
                   status=EpistemicStatus.FOLK_LEGEND, confidence=0.3,
                   adopted_by="E10交付档案v1（GPT闸门采纳）",
                   rationale="航船比喻为二手转述，若用须说「据说」，不做骨架"),
    BeliefAdoption(proposition_id="prop_zongji_vs_diming",
                   status=EpistemicStatus.VERIFIED, confidence=0.9,
                   adopted_by="E10交付档案v1（GPT闸门采纳）",
                   rationale="文物局考释原话与今名延续互证；建筑消失与名字留存"
                             "分属两层"),
    BeliefAdoption(proposition_id="prop_yongshan_uncertain",
                   status=EpistemicStatus.UNSUBSTANTIATED, confidence=0.2,
                   adopted_by="E10交付档案v1（GPT闸门采纳）",
                   rationale="永山大宅与营区关联无一手档案，存疑待考不展开"),
]


# ==================================================================
# 8. 空间变化事件
# ==================================================================

TRANSFORMATIONS: List[PlaceTransformation] = [
    PlaceTransformation(
        id="pte_yim_1860_damaged", entity_id="ent_yimuyuan",
        transformation=PlaceTransformationEvent.DAMAGED,
        time_span=_ts(1860, 1860, "ts_pte1"),
        resulting_state_id="st_yim_1860",
        resulting_condition="圆明园及其附属园囿遭焚毁，一亩园区域院落俱损，"
                            "其后渐辟稻田（毁损不是终点，地点持续体见身份断言）",
        evidence_fact_ids=["tf_smh_1860"],
    ),
    PlaceTransformation(
        id="pte_smh_1763_dredge", entity_id="ent_shanmianhu",
        transformation=PlaceTransformationEvent.CONSTRUCTED,
        time_span=_ts(1763, 1763, "ts_pte2"),
        resulting_state_id="st_smh_1763",
        resulting_condition="乾隆二十八年（1763）疏浚成湖，旧称前湖，御道穿湖"
                            "形似宫扇，故名扇面湖",
        evidence_fact_ids=["tf_smh_1763"],
    ),
    PlaceTransformation(
        id="pte_smh_2000_fill", entity_id="ent_shanmianhu",
        transformation=PlaceTransformationEvent.DEMOLISHED,
        time_span=_ts(2000, 2000, "ts_pte3"),
        resulting_state_id="st_smh_2000",
        resulting_condition="故址填埋建农贸市场",
        evidence_fact_ids=["tf_smh_2000"],
    ),
    PlaceTransformation(
        id="pte_smh_2024_restored", entity_id="ent_shanmianhu",
        transformation=PlaceTransformationEvent.REBUILT,
        time_span=_ts(2024, 2024, "ts_pte4"),
        resulting_state_id="st_smh_2024",
        resulting_condition="春夏建成并对公众开放：复挖湖面、亲水步道、绿化；"
                            "地下遗迹覆土保护，展示性恢复非原样复建",
        evidence_fact_ids=["tf_smh_2024"],
    ),
    PlaceTransformation(
        id="pte_nm_guangxu_rebuilt", entity_id="ent_niangniangmiao",
        transformation=PlaceTransformationEvent.REBUILT,
        time_span=_ts(1875, 1908, "ts_pte5"),
        resulting_state_id="st_nm_guangxu",
        resulting_condition="光绪年间再建（非始建；刘诚连若参与只能表述为再建/重修）",
        evidence_fact_ids=["tf_nm_guangxu"],
    ),
    PlaceTransformation(
        id="pte_wai_1770_relocate", entity_id="ent_waihuoqiying",
        transformation=PlaceTransformationEvent.RELOCATED,
        time_span=_ts(1770, 1773, "ts_pte6"),
        resulting_state_id="st_wai_1770",
        resulting_condition="乾隆三十五年（1770）色布腾巴勒珠尔奏请、乾隆批准，"
                            "自城内迁建城西蓝靛厂",
        evidence_fact_ids=["tf_wjbz_qianjian", "tf_hd_neiwai"],
    ),
    PlaceTransformation(
        id="pte_wai_1773_built", entity_id="ent_waihuoqiying",
        transformation=PlaceTransformationEvent.CONSTRUCTED,
        time_span=_ts(1773, 1773, "ts_pte7"),
        resulting_state_id="st_wai_1773",
        resulting_condition="营区基本建成（研究结论口径，非《清史稿》直接记载）",
        evidence_fact_ids=["tf_wjbz_qianjian"],
    ),
    PlaceTransformation(
        id="pte_xd_1712_renamed", entity_id="ent_xiding",
        transformation=PlaceTransformationEvent.REBUILT,
        time_span=_ts(1712, 1712, "ts_pte8"),
        resulting_state_id="st_xd_1712",
        resulting_condition="康熙五十一年（1712）改称广仁宫碧霞元君庙",
        evidence_fact_ids=["tf_hd_xiding_yange"],
    ),
    PlaceTransformation(
        id="pte_qzs_2009_rebuilt", entity_id="ent_qingzhensi",
        transformation=PlaceTransformationEvent.REBUILT,
        time_span=_ts(2009, 2009, "ts_pte9"),
        resulting_state_id="st_qzs_2009",
        resulting_condition="2006年10月开工重建，2009年10月21日落成",
        evidence_fact_ids=["tf_hd_qingzhensi"],
    ),
]

AGGREGATES: List[PlaceAggregate] = []
