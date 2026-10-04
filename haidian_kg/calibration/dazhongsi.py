"""
haidian_kg/calibration/dazhongsi.py
大钟寺（觉生寺）词条 —— 海淀历史地名知识库 E9 入库模块

数据唯一来源：《大钟寺》研究档案 v2（dazhongsi_video/research.md，两轮 GPT 复查后冻结）。
本模块是闭包方法 v3 的第一次真实 admission 事件：新词条的书进入 frontier。

证据分级映射（research.md 六级 → 本体表达，绝不混级）：
  [文献记载]   → TextualFact（古籍逐字引文，繁体原字形）+ VERIFIED 采信
  [现存实物]   → 一手碑刻挂 EPIGRAPHY；器物实测挂博物馆器物档案篇卷（记录式，非古籍引文）
  [研究推断]   → Proposition.inference_method + CONTESTED 采信（推断不得写成史实）
  [现代研究观点] → Proposition 标「有研究认为」+ CONTESTED 采信（非清代档案自述）
  [民间传说]   → FOLK_LEGEND 采信（冰道运钟、堆土造山）
  [存疑待考]   → CONTESTED + alternative_relations（铸年、铸钟厂地望、姚广孝监造）

E9 红线落位（research.md §10 择要）：
  - 1733 开工与 1734 赐名分属两个 State（st_js_1733 / st_js_1743 链），绝不混写同年
  - 1743 迁钟与 1746 大钟歌分挂两个篇卷（div_qgz_1743_shi / div_qgz_1746_ge）
  - 钟高 6.75 米为博物馆现行公开口径；不写「五到七米」，不与 5.5 米并列
  - 铭文只用「23 万余字」，不混 230,184 / 231,666 两套统计；用「铭铸」不用「刻」
  - 《燕邸纪闻》不建独立书目条目：引文挂 src_rxjwkc 并在 translator_note 标转引
  - 寺是祈雨场所 ≠ 钟参与祈雨：2023 专项课题结论落为 DISPROVEN（附反驳证据）
  - 天启弃置卧地约一百二十年，非「三百年」
  - 「华严钟」为讹名：至少晚明已流传，钟上并无《华严经》——名与实物不符
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
# 1. 文献与篇卷
# ==================================================================

SOURCES: List[HistoricalSource] = [
    # v2.1：一律取自统一书目表，一书一条，禁止在此另建
    source_by_title("敕建觉生寺碑文"),
    source_by_title("帝京景物略"),
    source_by_title("长安客话"),
    source_by_title("酌中志"),
    source_by_title("春明梦余录"),
    source_by_title("燕京岁时记"),
    source_by_title("万历野获编"),
    source_by_title("两宫鼎建记"),
    source_by_title("袁中郎全集"),
    source_by_title("清高宗御制诗文集"),
    source_by_title("钦定日下旧闻考"),
    source_by_title("大钟寺古钟博物馆馆史资料"),
]

DIVISIONS: List[SourceDivision] = [
    # 碑文（一手石刻）
    SourceDivision(id="div_beiwen_quanbei", source_id="src_jueshengsi_beiwen",
                   volume_number="全碑", section_title="雍正御制敕建觉生寺碑"),
    # 明人笔记（卷次待核，不得臆标）
    SourceDivision(id="div_djjwl_hjc", source_id="src_dijingjingwulue",
                   volume_number="卷次待核", section_title="汉经厂·大钟条"),
    SourceDivision(id="div_djjwl_liugeng", source_id="src_dijingjingwulue",
                   volume_number="卷次待核", section_title="万寿寺大钟条"),
    SourceDivision(id="div_cakh_wanshousi", source_id="src_changankehua",
                   volume_number="卷次待核", section_title="万寿寺条"),
    SourceDivision(id="div_zzz_dazhong", source_id="src_zuozhongzhi",
                   volume_number="卷次待核", section_title="大钟条"),
    SourceDivision(id="div_cmmyl_zhuzhongchang", source_id="src_chunmengmengyulu",
                   volume_number="卷次待核", section_title="铸钟厂条"),
    SourceDivision(id="div_yjsj_jueshengsi", source_id="src_yanjingsuishiji",
                   volume_number="全一卷", section_title="觉生寺大钟殿条"),
    SourceDivision(id="div_wlyhb_wanshousi", source_id="src_wanliyehuobian",
                   volume_number="卷次待核", section_title="万寿寺条"),
    SourceDivision(id="div_lgdjj_yunshi", source_id="src_lianggongdingjianji",
                   volume_number="卷次待核", section_title="搬运巨料凿井浇水条"),
    SourceDivision(id="div_yhd_wanshousi", source_id="src_yuanzhonglang",
                   volume_number="卷次待核", section_title="万寿寺观文皇旧钟"),
    # 官书：日下旧闻考卷77 国朝苑囿·乐善园后（万寿寺条引《燕邸纪闻》——转引，不独立建目）
    # E15 闸门裁定（2026-10-02）：旧记「卷100 西郊景物」系旧分类定位（郊坰门）致误；canonical=卷77
    SourceDivision(id="div_rxjwkc77_wanshousi", source_id="src_rxjwkc",
                   volume_number="卷77",
                   section_title="国朝苑囿·乐善园后·万寿寺条（引《燕邸纪闻》；旧记卷100系旧定位致误）"),
    # 御制诗：1743 短诗与 1746 大钟歌分挂两个篇卷，物理阻断同年剪接
    SourceDivision(id="div_qgz_1743_shi", source_id="src_qianlong_shiwenji",
                   volume_number="卷次待核", section_title="御制觉生寺大钟诗（乾隆八年）"),
    SourceDivision(id="div_qgz_1746_ge", source_id="src_qianlong_shiwenji",
                   volume_number="卷次待核", section_title="觉生寺大钟歌用沈德潜韵（乾隆十一年）"),
    # 馆藏公开资料（机构沿革 / 器物档案 / 祈雨课题，与古籍引文分层）
    SourceDivision(id="div_dzs_yange", source_id="src_dzs_history",
                   volume_number="馆史沿革", section_title="建置与保护沿革"),
    SourceDivision(id="div_dzs_bell", source_id="src_dzs_history",
                   volume_number="器物档案", section_title="永乐大钟实测数据"),
    SourceDivision(id="div_dzs_qiyu", source_id="src_dzs_history",
                   volume_number="专题课题", section_title="祈雨专项课题（2023结项）"),
]


# ==================================================================
# 2. 文本事实（古籍为繁体逐字引文；馆藏资料为记录式陈述，分层不混）
# ==================================================================

FACTS: List[TextualFact] = [
    # ---- 敕建觉生寺碑文（一手石刻）：选址、取名、赐名 ----
    TextualFact(
        id="tf_beiwen_ciming", division_id="div_beiwen_quanbei",
        verbatim_quote="爰賜名覺生寺",
        attested_string="覺生寺",
        source_year=_dt(1734, "dt_beiwen",
                        _ry(Era.QING, "雍正", 12, "雍正十二年")),
    ),
    TextualFact(
        id="tf_beiwen_xuankuang", division_id="div_beiwen_quanbei",
        verbatim_quote="高朗乾爽，林木佳茂",
        attested_string="高朗乾爽",
        source_year=_dt(1734, "dt_beiwen2",
                        _ry(Era.QING, "雍正", 12, "雍正十二年")),
    ),
    TextualFact(
        id="tf_beiwen_xingxing", division_id="div_beiwen_quanbei",
        verbatim_quote="右隔塵市之囂，左繞山川之勝",
        attested_string="塵市之囂",
        source_year=_dt(1734, "dt_beiwen3",
                        _ry(Era.QING, "雍正", 12, "雍正十二年")),
    ),
    TextualFact(
        id="tf_beiwen_juesheng", division_id="div_beiwen_quanbei",
        verbatim_quote="以無覺之覺，覺不生之生",
        attested_string="覺生",
        source_year=_dt(1734, "dt_beiwen4",
                        _ry(Era.QING, "雍正", 12, "雍正十二年")),
    ),
    # ---- 帝京景物略：汉经厂藏钟 / 万寿寺日供六僧 ----
    TextualFact(
        id="tf_djjwl_hjc", division_id="div_djjwl_hjc",
        verbatim_quote="向藏漢經廠",
        attested_string="漢經廠",
    ),
    TextualFact(
        id="tf_djjwl_liugeng", division_id="div_djjwl_liugeng",
        verbatim_quote="日供六僧擊之",
        attested_string="六僧",
    ),
    # ---- 长安客话：万寿寺方钟楼与钟声 ----
    TextualFact(
        id="tf_cakh_zhonglou", division_id="div_cakh_wanshousi",
        verbatim_quote="寺有方鐘樓，前臨大道，樓僅容鐘",
        attested_string="方鐘樓",
    ),
    TextualFact(
        id="tf_cakh_shengwen", division_id="div_cakh_wanshousi",
        verbatim_quote="聲聞數十里，其聲宏宏，時遠時近，有異他鐘",
        attested_string="聲聞數十里",
    ),
    TextualFact(
        id="tf_cakh_yizhi", division_id="div_cakh_wanshousi",
        verbatim_quote="近年自宮中移此，晝夜撞擊，聲聞數十里",
        attested_string="自宮中移此",
    ),
    # ---- 酌中志：万寿寺建大钟楼 / 日夜撞击 ----
    TextualFact(
        id="tf_zzz_zhonglou", division_id="div_zzz_dazhong",
        verbatim_quote="至於三十年後，於西直門外萬壽寺中建大鐘樓，懸大鐘一口",
        attested_string="萬壽寺",
    ),
    TextualFact(
        id="tf_zzz_shibawan", division_id="div_zzz_dazhong",
        verbatim_quote="此鐘日夜撞不絕聲，云十萬八千杵",
        attested_string="十萬八千杵",
    ),
    # ---- 日下旧闻考卷77 转《燕邸纪闻》：1607 徙置万寿寺（转引，不建独立书目） ----
    TextualFact(
        id="tf_yandijian_1607", division_id="div_rxjwkc77_wanshousi",
        verbatim_quote="今徙置之日為六月十六日，亦四丁未相符",
        attested_string="徙置",
        translator_note="《燕邸纪闻》原书不独立建目：此为《日下旧闻考》卷77万寿寺条转引（E15 闸门裁定：旧记卷100系致误）"
                        "丁未即万历三十五年(1607)；provenance 挂 src_rxjwkc",
    ),
    # ---- 春明梦余录：铸钟厂仆地巨钟（铸地推断旁证） ----
    TextualFact(
        id="tf_cmmyl_pudi", division_id="div_cmmyl_zhuzhongchang",
        verbatim_quote="舊鑄高二丈餘、闊一丈餘者，尚有十數仆地上",
        attested_string="舊鑄",
    ),
    # ---- 燕京岁时记：大钟殿形制 ----
    TextualFact(
        id="tf_yjsj_zhongdian", division_id="div_yjsj_jueshengsi",
        verbatim_quote="高五丈，下方上圓，四面皆窗，後有旋梯，左升右降",
        attested_string="旋梯",
    ),
    # ---- 万历野获编：万寿寺跨年落成 ----
    TextualFact(
        id="tf_wlyhb_jiasui", division_id="div_wlyhb_wanshousi",
        verbatim_quote="浹歲即成",
        attested_string="浹歲",
    ),
    # ---- 两宫鼎建记：冰道运巨料（方法旁证，非本钟史实） ----
    TextualFact(
        id="tf_lgdjj_diaojing", division_id="div_lgdjj_yunshi",
        verbatim_quote="每里掘一井，以澆旱船、資渴飲",
        attested_string="掘一井",
    ),
    TextualFact(
        id="tf_lgdjj_handong", division_id="div_lgdjj_yunshi",
        verbatim_quote="比時天寒地凍，正宜趁時發運",
        attested_string="天寒地凍",
    ),
    # ---- 袁中郎全集：移钟盛况 + 华严说与实物不符 ----
    TextualFact(
        id="tf_yhd_guanyuan", division_id="div_yhd_wanshousi",
        verbatim_quote="道傍觀者肩相摩，車騎數月猶馳逐",
        attested_string="觀者肩相摩",
    ),
    TextualFact(
        id="tf_yhd_neishu", division_id="div_yhd_wanshousi",
        verbatim_quote="外書佛母萬真言，內寫雜花八十軸",
        attested_string="雜花八十軸",
    ),
    # ---- 御制诗：1743 短诗（佛教语汇）与 1746 大钟歌（靖难忏悔话语）分卷 ----
    TextualFact(
        id="tf_qgz_1743_shanhou", division_id="div_qgz_1743_shi",
        verbatim_quote="善吼周三界",
        attested_string="善吼周三界",
        source_year=_dt(1743, "dt_qgz1743",
                        _ry(Era.QING, "乾隆", 8, "乾隆八年")),
    ),
    TextualFact(
        id="tf_qgz_kai", division_id="div_qgz_1746_ge",
        verbatim_quote="晁謀弗善野戰龍，金川門開烈焰紅",
        attested_string="金川門",
        source_year=_dt(1746, "dt_qgz1746",
                        _ry(Era.QING, "乾隆", 11, "乾隆十一年")),
    ),
    TextualFact(
        id="tf_qgz_chanhui", division_id="div_qgz_1746_ge",
        verbatim_quote="懺悔詎賴佛氏鐘",
        attested_string="懺悔",
        source_year=_dt(1746, "dt_qgz1746b",
                        _ry(Era.QING, "乾隆", 11, "乾隆十一年")),
    ),
    TextualFact(
        id="tf_qgz_zhuangchu", division_id="div_qgz_1746_ge",
        verbatim_quote="欲藉撞杵散憤氣",
        attested_string="撞杵",
        source_year=_dt(1746, "dt_qgz1746c",
                        _ry(Era.QING, "乾隆", 11, "乾隆十一年")),
    ),
    # ---- 馆藏公开资料：沿革（记录式陈述，非古籍引文） ----
    TextualFact(
        id="tf_dzs_1733", division_id="div_dzs_yange",
        verbatim_quote="觉生寺于雍正十一年（1733）正月开工，雍正十二年（1734）冬告成，"
                       "敕名「觉生寺」，选址西直门外曾家庄，占地约三万平方米；"
                       "十一年四月内务府已奏移钟事宜，允之，钟至乾隆八年方移成。",
        attested_string="觉生寺",
    ),
    TextualFact(
        id="tf_dzs_tianqi", division_id="div_dzs_yange",
        verbatim_quote="明天启年间，万寿寺永乐大钟因讹言撤下置地；至乾隆八年（1743）"
                       "移入觉生寺前，卧地约一百二十年。",
        attested_string="天启",
    ),
    TextualFact(
        id="tf_dzs_1743", division_id="div_dzs_yange",
        verbatim_quote="乾隆八年（1743），永乐大钟自万寿寺移入觉生寺大钟殿；"
                       "此后民间始称「大钟寺」，乾隆御笔「华严觉海」匾额悬于门上。",
        attested_string="大钟寺",
    ),
    TextualFact(
        id="tf_dzs_1957", division_id="div_dzs_yange",
        verbatim_quote="1957年10月28日，觉生寺公布为北京市第一批市级文物保护单位；"
                       "此后文物尽失，唯永乐大钟独存，寺屋亦长期失修被占。",
        attested_string="市级文物保护单位",
    ),
    TextualFact(
        id="tf_dzs_1985", division_id="div_dzs_yange",
        verbatim_quote="1985年10月4日，大钟寺古钟博物馆成立并正式开放；"
                       "「天王殿」「大雄宝殿」等处辟为钟铃展区，展品多为各地征集而来。",
        attested_string="大钟寺古钟博物馆",
    ),
    TextualFact(
        id="tf_dzs_1996", division_id="div_dzs_yange",
        # 【R12 回灌 2026-10-04】公布日期订正为 **1996-11-20**（国发〔1996〕47号
        # 《国务院关于公布第四批全国重点文物保护单位的通知》落款「一九九六年十一月二十日」，
        # 维基文库原件已核）。原写「1996年12月27日」无出处。批次第四批、编号 4-166 均正确。
        # 按 banners.py 团城演武厅的既有范式「两说并存取国务院文件口径」处理。
        verbatim_quote="1996年11月20日，国务院公布觉生寺为第四批全国重点文物保护单位，"
                       "编号4-166。",
        attested_string="全国重点文物保护单位",
        translator_note="公布日期取国发〔1996〕47号落款日期（一九九六年十一月二十日，维基文库"
                        "原件已核）。旧档「1996年12月27日」查无出处，已撤；批次与编号不变。",
    ),
    TextualFact(
        id="tf_dzs_metro", division_id="div_dzs_yange",
        verbatim_quote="北京地铁13号线设大钟寺站，站名沿用古刹俗称；"
                       "寺今为大钟寺古钟博物馆，北京市文物局直属单位。",
        attested_string="大钟寺站",
    ),
    # ---- 馆藏公开资料：器物实测（现行公开口径） ----
    TextualFact(
        id="tf_dzs_bell_dims", division_id="div_dzs_bell",
        verbatim_quote="永乐大钟重46.5吨，通高6.75米（博物馆现行公开口径），"
                       "钟肩外径2.4米，钟壁最薄94毫米、最厚185毫米；"
                       "钟面上下内外铭铸汉梵经咒，通称23万余字，"
                       "无臣工与工匠署名；现代测余音约3分钟。",
        attested_string="23万余字",
    ),
    # ---- 馆藏公开资料：祈雨（寺是场所 ≠ 钟参与） ----
    TextualFact(
        id="tf_dzs_qiyu_1778", division_id="div_dzs_qiyu",
        verbatim_quote="觉生寺为清代皇家祈雨场所，可落实的设坛祈雨记录始于乾隆四十三年"
                       "（1778）五月，坛设寺西墙外，依《大云轮请雨经》由僧众诵经祈雨；"
                       "乾隆四十七年（1782）、四十九年（1784）相继再举。",
        attested_string="祈雨",
    ),
    TextualFact(
        id="tf_dzs_qiyu_2023", division_id="div_dzs_qiyu",
        verbatim_quote="2023年馆专项课题核中国第一历史档案馆藏清代觉生寺祈雨档案，"
                       "未见永乐大钟直接参与仪式的记录，结项公告称研究纠正了"
                       "永乐大钟「非祈雨不鸣」的讹传。",
        attested_string="非祈雨不鸣",
    ),
]


# ==================================================================
# 3. 实体
# ==================================================================

ENTITIES: List[PersistentSpatialEntity] = [
    PersistentSpatialEntity(id="ent_jueshengsi", kind=PhysicalThingKind.RELIGIOUS_PRECINCT,
                            canonical_label="觉生寺（1743钟迁入后俗称大钟寺）"),
    PersistentSpatialEntity(id="ent_yongle_bell", kind=PhysicalThingKind.HUMAN_MADE_ARTIFACT,
                            canonical_label="永乐大钟（明代青铜巨钟）"),
    PersistentSpatialEntity(id="ent_wanshousi", kind=PhysicalThingKind.RELIGIOUS_PRECINCT,
                            canonical_label="万寿寺（西直门外广源闸西）"),
    PersistentSpatialEntity(id="ent_hanjingchang", kind=PhysicalThingKind.IMPERIAL_WORKSHOP,
                            canonical_label="汉经厂（明代皇家经厂）"),
    PersistentSpatialEntity(id="ent_zhuzhongchang", kind=PhysicalThingKind.IMPERIAL_WORKSHOP,
                            canonical_label="铸钟厂（明代铸钟厂坊，地望存疑）"),
]


# ==================================================================
# 4. 历时状态（每条状态：ReignYear 纪年挂靠 + evidence_fact_ids 溯源；
#    推断/争议的 epistemic status 落在 §7 命题与采信层）
# ==================================================================

STATES: List[HistoricalFeatureState] = [
    # ---- 觉生寺：1733 开工与 1734 赐名分属两个状态（E9 红线） ----
    HistoricalFeatureState(
        id="st_js_1733", entity_id="ent_jueshengsi",
        time_span=TimeSpan(id="ts_dzs_a", label="1733-1734 在建",
                           begin=_dt(1733, "ts_dzs_ab",
                                     _ry(Era.QING, "雍正", 11, "雍正十一年正月")),
                           end=_dt(1734, "ts_dzs_ae")),
        geometry="西直门外曾家庄，占地约三万平方米，「高朗干爽，林木佳茂」，"
                 "「右隔尘市之嚣，左绕山川之胜」",
        function="奉敕兴建中的皇家寺院（开工年；此年尚未赐名）",
        evidence_fact_ids=["tf_dzs_1733", "tf_beiwen_xuankuang", "tf_beiwen_xingxing"],
    ),
    HistoricalFeatureState(
        id="st_js_1734", entity_id="ent_jueshengsi",
        time_span=_ts(1734, 1742, "ts_dzs_b"),
        geometry="寺成，山门悬「敕建觉生寺」匾（康熙十七子果亲王书）",
        function="敕名觉生寺：「以无觉之觉，觉不生之生」；皇家梵刹（钟未至）",
        evidence_fact_ids=["tf_dzs_1733", "tf_beiwen_ciming", "tf_beiwen_juesheng"],
    ),
    HistoricalFeatureState(
        id="st_js_1743", entity_id="ent_jueshengsi",
        time_span=_ts(1743, 1911, "ts_dzs_c"),
        geometry="大钟殿居全寺最后、为全寺最高建筑，「下方上圆，四面皆窗，后有旋梯，"
                 "左升右降」，殿内须仰视观钟",
        function="永乐大钟移入后的皇家寺院（「先安钟后建楼」为建筑学推断，见命题层）",
        evidence_fact_ids=["tf_dzs_1743", "tf_yjsj_zhongdian"],
    ),
    HistoricalFeatureState(
        id="st_js_1778", entity_id="ent_jueshengsi",
        time_span=TimeSpan(id="ts_dzs_d", label="1778-1911 皇家祈雨场所",
                           begin=_dt(1778, "ts_dzs_db",
                                     _ry(Era.QING, "乾隆", 43, "乾隆四十三年五月",
                                         month=5)),
                           end=_dt(1911, "ts_dzs_de")),
        geometry="祈雨坛设于寺西墙外",
        function="清代皇家祈雨场所（可落实记录始于1778年5月；寺是祈雨场所，"
                 "不等于钟参与祈雨——见命题层2023课题结论）",
        evidence_fact_ids=["tf_dzs_qiyu_1778"],
    ),
    HistoricalFeatureState(
        id="st_js_1912", entity_id="ent_jueshengsi",
        time_span=_ts(1912, 1956, "ts_dzs_e"),
        geometry="山门前空地设摊，杂技戏曲，「打金钱眼」",
        function="平民化寺庙；农历正月初一至十五庙会为北京八大传统庙会之一，"
                 "春节期间每天敲钟108响",
        evidence_fact_ids=["tf_yjsj_zhongdian", "tf_dzs_metro"],
    ),
    HistoricalFeatureState(
        id="st_js_1957", entity_id="ent_jueshengsi",
        time_span=_ts(1957, 1984, "ts_dzs_f"),
        geometry="寺市长年失修，曾遭工厂占用，除永乐大钟外文物尽失",
        function="北京市第一批市级文物保护单位（1957-10-28公布）",
        evidence_fact_ids=["tf_dzs_1957"],
    ),
    HistoricalFeatureState(
        id="st_js_1985", entity_id="ent_jueshengsi",
        time_span=_ts(1985, 1995, "ts_dzs_g"),
        geometry="原天王殿改沿革展区、大雄宝殿辟编钟展厅（复制品）、观音殿为钟铃展区，"
                 "1994年扩九亭钟园",
        function="大钟寺古钟博物馆（1985-10-04成立开放），中国古钟专题博物馆",
        evidence_fact_ids=["tf_dzs_1985"],
    ),
    HistoricalFeatureState(
        id="st_js_1996", entity_id="ent_jueshengsi",
        time_span=_ts(1996, 2026, "ts_dzs_h"),
        geometry="中轴线稍向西倾斜（存误差）；北三环西路甲31号",
        function="第四批全国重点文物保护单位（1996-11-20 国发〔1996〕47号，编号4-166）；"
                 "13号线大钟寺站站名沿用俗称",
        evidence_fact_ids=["tf_dzs_1996", "tf_dzs_metro"],
    ),
    # ---- 永乐大钟：铸年存疑（起年取永乐元年下限，approximate；不得写定论） ----
    HistoricalFeatureState(
        id="st_bell_cast_hjc", entity_id="ent_yongle_bell",
        time_span=TimeSpan(id="ts_bell_a", label="永乐铸成（年代存疑）至汉经厂收藏",
                           begin=_dt(1403, "ts_bell_ab",
                                     _ry(Era.MING, "永乐", None, "明永乐年间"),
                                     precision="approximate"),
                           end=_dt(1606, "ts_bell_ae")),
        geometry="通高6.75米（博物馆现行公开口径），重46.5吨，钟壁最薄94毫米、最厚185毫米",
        material="青铜合金（铜80.54%、锡16.40%、铅1.12%，含微量金银）；"
                 "铭铸汉梵经咒23万余字，无臣工工匠署名",
        function="铸于永乐年间（铸年存疑待考，铸地推断见命题层）；「向藏汉经厂」，"
                 "现有文献未见其实际鸣钟确证",
        evidence_fact_ids=["tf_dzs_bell_dims", "tf_djjwl_hjc"],
    ),
    HistoricalFeatureState(
        id="st_bell_wanshousi", entity_id="ent_yongle_bell",
        time_span=_ts(1607, 1620, "ts_bell_b"),
        geometry="悬于万寿寺方钟楼，「前临大道，楼仅容钟」",
        material="同前（青铜巨钟，铭铸经咒）",
        function="万历三十五年(1607)六月十六日自宫中徙置万寿寺，日供六僧击之，"
                 "「昼夜撞击，声闻数十里」；皇家寺院佛事法器",
        evidence_fact_ids=["tf_yandijian_1607", "tf_zzz_zhonglou", "tf_cakh_zhonglou",
                           "tf_cakh_shengwen", "tf_cakh_yizhi", "tf_djjwl_liugeng"],
    ),
    HistoricalFeatureState(
        id="st_bell_laid", entity_id="ent_yongle_bell",
        time_span=TimeSpan(id="ts_bell_c", label="天启年间弃置-1742 卧地",
                           begin=_dt(1621, "ts_bell_cb",
                                     _ry(Era.MING, "天启", 1, "天启元年"),
                                     precision="approximate"),
                           end=_dt(1742, "ts_bell_ce")),
        function="因讹言（涉「白虎方不宜鸣钟」之类）撤下置地，卧地约一百二十年前后"
                 "（非「三百年」）",
        evidence_fact_ids=["tf_dzs_tianqi"],
    ),
    HistoricalFeatureState(
        id="st_bell_jueshengsi", entity_id="ent_yongle_bell",
        time_span=_ts(1743, 2026, "ts_bell_d"),
        geometry="悬觉生寺大钟殿，殿内空间狭小须仰视；碑在钟正东，碑侧正对"
                 "「大明永乐年月吉日制」年款牌位",
        material="同前（青铜巨钟，铭铸经咒）",
        function="乾隆八年(1743)移入觉生寺大钟殿至今；今为大钟寺古钟博物馆核心展陈",
        evidence_fact_ids=["tf_dzs_1743", "tf_yjsj_zhongdian", "tf_dzs_bell_dims"],
    ),
    # ---- 万寿寺：李太后建、冯保督建，皇家寺院 ----
    HistoricalFeatureState(
        id="st_ws_1578", entity_id="ent_wanshousi",
        time_span=TimeSpan(id="ts_ws_a", label="1578-1911 万寿寺",
                           begin=_dt(1578, "ts_ws_ab",
                                     _ry(Era.MING, "万历", 6, "万历六年六月",
                                         month=6)),
                           end=_dt(1911, "ts_ws_ae")),
        geometry="西直门外七里广源闸西；万历三十年后增建大钟楼（方钟楼，楼仅容钟）",
        function="李太后命太监冯保建的皇家寺院（万历五年三月开工、六年六月竣工，"
                 "「浃岁即成」跨年），有宫廷祝釐佛事——不是民间寺庙",
        evidence_fact_ids=["tf_wlyhb_jiasui", "tf_zzz_zhonglou", "tf_cakh_zhonglou"],
    ),
    # ---- 汉经厂 / 铸钟厂：明皇城厂坊（起年无考，开放起始） ----
    HistoricalFeatureState(
        id="st_hjc_ming", entity_id="ent_hanjingchang",
        time_span=TimeSpan(id="ts_hjc_a", label="明代汉经厂",
                           open_begin=True, begin=None,
                           end=_dt(1644, "ts_hjc_ae")),
        geometry="明代宫廷经厂（在京皇城，非海淀辖境）",
        function="皇家刻藏佛事厂坊；永乐大钟「向藏」于此（是否曾鸣钟无确证）",
        evidence_fact_ids=["tf_djjwl_hjc"],
    ),
    HistoricalFeatureState(
        id="st_zzc_ming", entity_id="ent_zhuzhongchang",
        time_span=TimeSpan(id="ts_zzc_a", label="明代铸钟厂",
                           open_begin=True, begin=None,
                           end=_dt(1644, "ts_zzc_ae")),
        geometry="德胜门东（今钟楼附近一说；具体地望存疑待考）",
        function="明代铸钟厂坊；厂内「旧铸高二丈余、阔一丈余者，尚有十数仆地上」",
        evidence_fact_ids=["tf_cmmyl_pudi"],
    ),
]


# ==================================================================
# 5. 身份断言：同一器物跨四空间 / 铸钟厂地望存疑
# ==================================================================

IDENTITIES: List[DiachronicIdentityAssertion] = [
    # 【E9 核心】同一口钟在铸钟厂/汉经厂→万寿寺→觉生寺四个空间被四种方式解释；
    # 器物同一性链条连续，解释层（见命题层）逐段降级
    DiachronicIdentityAssertion(
        id="dia_bell_same_continuant",
        subject_entity_ids=["ent_yongle_bell"],
        relation=IdentityRelation.SAME_CONTINUANT,
        time_span=_ts(1403, 2026, "ts_di1"),
        evidence_fact_ids=["tf_djjwl_hjc", "tf_yandijian_1607", "tf_dzs_1743"],
        status=EpistemicStatus.VERIFIED,
        alternative_relations=[
            "「向藏汉经厂」→丁未徙置万寿寺→乾隆八年移觉生寺，明清文献无异说，"
            "四空间同一器物",
            "汉经厂期与万寿寺期的器物同一性以《帝京景物略》《燕邸纪闻》为链，"
            "无同时代过秤档案（器物延续，档案链为间接）",
        ],
    ),
    # 铸钟厂位置：存疑待考（不得当定论写）
    DiachronicIdentityAssertion(
        id="dia_zzc_location",
        subject_entity_ids=["ent_zhuzhongchang"],
        relation=IdentityRelation.UNCERTAIN,
        time_span=TimeSpan(id="ts_di2", label="铸钟厂地望存疑", open_begin=True,
                           begin=None, end=_dt(1644, "ts_di2e")),
        evidence_fact_ids=["tf_cmmyl_pudi"],
        status=EpistemicStatus.CONTESTED,
        alternative_relations=[
            "德胜门东（今北京钟楼附近）为主流一说",
            "具体地望缺乏同时代测绘档案确证，仅据明清官书追记",
        ],
    ),
]


# ==================================================================
# 6. 名称与指称
# ==================================================================

APPELLATIONS: List[Appellation] = [
    Appellation(id="app_jueshengsi", label="觉生寺", kind=AppellationKind.HONORIFIC,
                valid_time_span=_ts(1734, 2026, "ts_n1"),
                attesting_fact_ids=["tf_beiwen_ciming", "tf_dzs_1733"]),
    # 1743 钟迁入后民间始称（俗称），官方名未改；13号线站名沿用
    Appellation(id="app_dazhongsi", label="大钟寺", kind=AppellationKind.VULGAR,
                valid_time_span=_ts(1743, 2026, "ts_n2"),
                attesting_fact_ids=["tf_dzs_1743", "tf_dzs_metro"]),
    # 讹名：钟上并无《华严经》，至少晚明已流传——note 必写（见 references provenance）
    Appellation(id="app_huayanbell", label="华严钟", kind=AppellationKind.MISPLACED_LEGEND,
                valid_time_span=_ts(1600, 2026, "ts_n3"),
                attesting_fact_ids=["tf_yhd_neishu"]),
    Appellation(id="app_yongledazhong", label="永乐大钟", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1403, 2026, "ts_n4"),
                attesting_fact_ids=["tf_dzs_bell_dims"]),
    Appellation(id="app_wanshousi", label="万寿寺", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1578, 2026, "ts_n5"),
                attesting_fact_ids=["tf_wlyhb_jiasui"]),
    Appellation(id="app_hanjingchang", label="汉经厂", kind=AppellationKind.OFFICIAL,
                valid_time_span=TimeSpan(id="ts_n6", label="明代",
                                         open_begin=True, begin=None,
                                         end=_dt(1644, "ts_n6e")),
                attesting_fact_ids=["tf_djjwl_hjc"]),
    Appellation(id="app_zhuzhongchang", label="铸钟厂", kind=AppellationKind.OFFICIAL,
                valid_time_span=TimeSpan(id="ts_n7", label="明代",
                                         open_begin=True, begin=None,
                                         end=_dt(1644, "ts_n7e")),
                attesting_fact_ids=["tf_cmmyl_pudi"]),
]

REFERENCES: List[ReferentialAssertion] = [
    ReferentialAssertion(id="rr_jueshengsi", appellation_id="app_jueshengsi",
                         referent_entity_id="ent_jueshengsi",
                         time_span=_ts(1734, 2026, "ts_r1"),
                         evidence_fact_ids=["tf_beiwen_ciming"]),
    ReferentialAssertion(id="rr_dazhongsi", appellation_id="app_dazhongsi",
                         referent_entity_id="ent_jueshengsi",
                         time_span=_ts(1743, 2026, "ts_r2"),
                         evidence_fact_ids=["tf_dzs_1743", "tf_dzs_metro"]),
    ReferentialAssertion(id="rr_huayanbell", appellation_id="app_huayanbell",
                         referent_entity_id="ent_yongle_bell",
                         time_span=_ts(1600, 2026, "ts_r3"),
                         evidence_fact_ids=["tf_yhd_neishu"],
                         provenance="「华严钟」为流传讹名：实物核对证明钟上并无《华严经》；"
                                    "「内外书华严八十一篇」之说与袁宏道诗句不符，"
                                    "只能说其描述与实物不符，不得替他编造观察过程；"
                                    "该名至少晚明万寿寺时期已广泛流传，"
                                    "不得断言「起源于」万寿寺"),
    ReferentialAssertion(id="rr_yongledazhong", appellation_id="app_yongledazhong",
                         referent_entity_id="ent_yongle_bell",
                         time_span=_ts(1403, 2026, "ts_r4"),
                         evidence_fact_ids=["tf_dzs_bell_dims"]),
    ReferentialAssertion(id="rr_wanshousi", appellation_id="app_wanshousi",
                         referent_entity_id="ent_wanshousi",
                         time_span=_ts(1578, 2026, "ts_r5"),
                         evidence_fact_ids=["tf_wlyhb_jiasui"]),
    ReferentialAssertion(id="rr_hanjingchang", appellation_id="app_hanjingchang",
                         referent_entity_id="ent_hanjingchang",
                         time_span=TimeSpan(id="ts_r6", label="明代",
                                            open_begin=True, begin=None,
                                            end=_dt(1644, "ts_r6e")),
                         evidence_fact_ids=["tf_djjwl_hjc"]),
    ReferentialAssertion(id="rr_zhuzhongchang", appellation_id="app_zhuzhongchang",
                         referent_entity_id="ent_zhuzhongchang",
                         time_span=TimeSpan(id="ts_r7", label="明代",
                                            open_begin=True, begin=None,
                                            end=_dt(1644, "ts_r7e")),
                         evidence_fact_ids=["tf_cmmyl_pudi"]),
]


# ==================================================================
# 7. 断言与采信：把交付档案的降格结论固化（推断/传说/现代观点绝不混级为史实）
# ==================================================================

PROPOSITIONS: List[Proposition] = [
    Proposition(
        id="prop_bell_cast_year",
        statement="永乐大钟铸于明永乐年间；具体铸年学界有争议，"
                  "博物馆公开口径只写「明永乐年间」（1424 不是学界定论）",
        derived_from_fact_ids=["tf_dzs_bell_dims"],
        inferred_subject_id="ent_yongle_bell",
        inference_method="众说并存且无同时代官档定论，故铸年一律存疑待考；"
                         "本库纪年只取「不早于永乐元年」下限并标 approximate",
        alternative_explanations=[
            "1418—1419 年前后铸成说",
            "1417 年始铸、1418 年前后基本完成说",
            "「永乐二十二年(1424)」说——证据层级不足，不得写为定论",
        ],
    ),
    Proposition(
        id="prop_bell_cast_zhuzhongchang",
        statement="永乐大钟当铸于德胜门东铸钟厂，首次迁移为铸钟厂→汉经厂"
                  "（此为现代研究推断，非文献直接记载）",
        derived_from_fact_ids=["tf_cmmyl_pudi", "tf_djjwl_hjc"],
        inferred_subject_id="ent_yongle_bell",
        inference_method="《春明梦余录》载厂内「尚有十数仆地上」巨钟→该厂有铸巨钟能力；"
                         "与《帝京景物略》「向藏汉经厂」逆向推出铸地→初藏地；"
                         "铸钟厂位置本身另存疑（见身份断言）",
        alternative_explanations=[
            "铸于他处说（无文证）",
            "汉经厂自设铸造作坊说（无文证）",
        ],
    ),
    Proposition(
        id="prop_hjc_no_ringing",
        statement="汉经厂时期现有文献未见其实际鸣钟的确证，研究者倾向主要处于收藏状态",
        derived_from_fact_ids=["tf_djjwl_hjc"],
        inferred_subject_id="ent_yongle_bell",
        inference_method="《帝京景物略》用「藏」、万寿寺期用「悬」，一字之差提示状态不同；"
                         "只说「未见确证」，不断言「从未使用」",
        alternative_explanations=[
            "汉经厂期或曾用于佛事鸣钟（无确证）",
        ],
    ),
    Proposition(
        id="prop_wanshou_royal",
        statement="万寿寺为李太后主持兴建的皇家寺院；「皇家法器变民间法器」等"
                  "多阶段模型是现代研究概括，不是历史机构分类",
        derived_from_fact_ids=["tf_zzz_zhonglou", "tf_wlyhb_jiasui", "tf_cakh_yizhi"],
        inferred_subject_id="ent_wanshousi",
        inference_method="李太后命冯保建、宫廷祝釐佛事、钟自宫中徙出——机构性质由建置与"
                         "使用者判定；不得说「大钟从皇家法器变成民间法器」",
        alternative_explanations=[
            "「皇家佛事—民间佛事—皇家祈雨—辞旧迎新」四阶段模型（现代研究概括，"
            "只可描述为「进入不同空间与人群」）",
        ],
    ),
    Proposition(
        id="prop_huayan_mismatch",
        statement="「华严钟」之名与「内外书华严八十一篇」之说至少晚明已广泛流传，"
                  "而实物铭文并无《华严经》；袁宏道「外书佛母万真言，内写杂花八十轴」"
                  "与实物不符",
        derived_from_fact_ids=["tf_yhd_neishu", "tf_yhd_guanyuan", "tf_dzs_bell_dims"],
        inferred_subject_id="ent_yongle_bell",
        inference_method="实物铭文核对为一手证据；可证的只是袁宏道描述与实物不符"
                         "（或沿用当时传闻），不得替他编造「未钻到钟内观察」的过程；"
                         "该名「至少到晚明已流传」，不说「起源于万寿寺」",
        alternative_explanations=[
            "「华严钟」或系时人沿用传闻之名而非实地核验（不作断言）",
        ],
    ),
    Proposition(
        id="prop_qianlong_1746",
        statement="乾隆十一年(1746)《觉生寺大钟歌用沈德潜韵》把大钟解释进靖难、罪责与"
                  "忏悔的话语中，并质疑佛钟能否洗脱罪责；乾隆八年(1743)御制诗仍是佛教"
                  "语汇——1743 迁钟与 1746 解释升级分三年讲",
        derived_from_fact_ids=["tf_qgz_kai", "tf_qgz_chanhui", "tf_qgz_zhuangchu",
                               "tf_qgz_1743_shanhou"],
        inferred_subject_id="ent_yongle_bell",
        inference_method="两诗分年比对：1743 诗「善吼周三界」尚是佛教语汇，1746 歌开篇即"
                         "靖难叙事——三年之差印证「解释覆盖器物」主题；"
                         "不得反向证明朱棣铸钟目的，不得说「乾隆认定朱棣铸钟是为忏悔」",
        alternative_explanations=[
            "「乾隆认定朱棣铸钟为忏悔」说——对诗文的过度引申，不采",
        ],
    ),
    Proposition(
        id="prop_modern_zhongjun",
        statement="有现代研究者认为乾隆作大钟歌是借永乐皇帝发挥，意在强化皇权、"
                  "告诫臣下「忠君」；此后诸家大钟歌叙事模式大多相似（非「高度一致」）",
        derived_from_fact_ids=["tf_qgz_kai"],
        inferred_subject_id="ent_yongle_bell",
        inference_method="现代学者解释框架，非清代档案自述；表述一律加「有研究认为」；"
                         "「政治空间/物证/忠君宣传」同属此层，不得写成清廷自白",
        alternative_explanations=[
            "乾隆个人佛学趣味与文学行为说",
        ],
    ),
    Proposition(
        id="prop_js_qiyu_1778",
        statement="觉生寺为清代皇家祈雨场所；可落实的设坛祈雨记录始于乾隆四十三年(1778)"
                  "五月，坛设寺西墙外，1782、1784 年亦有记录",
        derived_from_fact_ids=["tf_dzs_qiyu_1778"],
        inferred_subject_id="ent_jueshengsi",
        inference_method="中国第一历史档案馆藏档（馆方课题核档）；旧说「乾隆五十二年(1787)"
                         "下令辟觉生寺为祈雨场所」无可靠出处，删除",
        alternative_explanations=[
            "旧说 1787 年辟为祈雨场所（无可靠出处，已弃）",
        ],
    ),
    Proposition(
        id="prop_bell_qiyu_legend",
        statement="「非祈雨不鸣」「永乐大钟为皇家祈雨法器」系被纠正的旧有讹传",
        derived_from_fact_ids=["tf_dzs_qiyu_2023"],
        inferred_subject_id="ent_yongle_bell",
        inference_method="2023 年大钟寺专项课题核一史馆藏档，未见钟直接参与祈雨的记录；"
                         "寺是祈雨场所 ≠ 钟参与祈雨；引旧说必须注明为被纠正的旧说",
        alternative_explanations=[
            "旧说或源于庙会民俗想象（推测，无档）",
        ],
    ),
    Proposition(
        id="prop_dazhongsi_name",
        statement="乾隆八年(1743)钟迁入后民间始称「大钟寺」，官方名仍觉生寺；"
                  "13 号线站名沿用俗称",
        derived_from_fact_ids=["tf_dzs_1743", "tf_dzs_metro"],
        inferred_subject_id="ent_jueshengsi",
        inference_method="迁钟在前、俗称在后，因果链不可倒置——寺非为钟而建，"
                         "俗称不是敕名",
        alternative_explanations=[
            "站名沿用说（现代地名层，非官方改称）",
        ],
    ),
    Proposition(
        id="prop_dian_after_bell",
        statement="乾隆八年当为先置钟于木架、再围架建成大钟殿（建筑学推断，非文献记载）",
        derived_from_fact_ids=["tf_yjsj_zhongdian"],
        inferred_subject_id="ent_jueshengsi",
        inference_method="殿内空间狭小须仰视、旋梯绕钟——空间逻辑反推营造顺序；"
                         "标研究推断，不作史实",
        alternative_explanations=[
            "先建殿后移钟说（移钟入殿之工程细节无档）",
        ],
    ),
    Proposition(
        id="prop_bingdao_legend",
        statement="「沿途凿井浇水、冻结成冰道拖钟」为民间传说；《两宫鼎建记》只证明"
                  "该法明代确曾用于搬运大石料，用于此钟则为传说",
        derived_from_fact_ids=["tf_lgdjj_diaojing", "tf_lgdjj_handong"],
        inferred_subject_id="ent_yongle_bell",
        inference_method="方法旁证 ≠ 本钟史实；引用时必须分开「明代确有此法」与"
                         "「运钟用此法」两层",
        alternative_explanations=[
            "冰道运钟为信史说（无文献）",
        ],
    ),
    Proposition(
        id="prop_duitu_legend",
        statement="「堆土造山、把钟拖上土堆再建楼」为民间传说",
        derived_from_fact_ids=[],
        inferred_subject_id="ent_jueshengsi",
        inference_method="民俗流传，无文献档案支撑；与「先安钟后建楼」的建筑学推断分层",
        alternative_explanations=[
            "筑土山运钟说（无档）",
        ],
    ),
    Proposition(
        id="prop_shendu_yaoguangxiao",
        statement="铭文相传沈度书；姚广孝监造晚明文献已有明确记载，但缺乏同时代直接证据"
                  "（无铸钟当时官档、钟上无署名），学界仍有争议",
        derived_from_fact_ids=["tf_dzs_bell_dims"],
        inferred_subject_id="ent_yongle_bell",
        inference_method="姚广孝监造不贴「民间传说」（晚明《长安客话》等有明确文字），"
                         "亦不作定论（无同时代直接证据）——存疑待考",
        alternative_explanations=[
            "姚广孝监造说（晚明文献有载）",
            "证据不足存疑说（钟上无署名、无官档）",
        ],
    ),
]

ADOPTIONS: List[BeliefAdoption] = [
    BeliefAdoption(proposition_id="prop_bell_cast_year",
                   status=EpistemicStatus.CONTESTED, confidence=0.5,
                   adopted_by="E9交付档案v2",
                   rationale="铸年众说并存，博物馆公开口径只写「永乐年间」；"
                             "任何具体年份不得写成定论"),
    BeliefAdoption(proposition_id="prop_bell_cast_zhuzhongchang",
                   status=EpistemicStatus.CONTESTED, confidence=0.55,
                   adopted_by="E9交付档案v2",
                   rationale="仆地巨钟记载支持铸地推断，但属现代研究推断，"
                             "不得写成文献直接记载"),
    BeliefAdoption(proposition_id="prop_hjc_no_ringing",
                   status=EpistemicStatus.CONTESTED, confidence=0.6,
                   adopted_by="E9交付档案v2",
                   rationale="「藏」字用字之辨只支撑收藏倾向；无确证不断言从未使用"),
    BeliefAdoption(proposition_id="prop_wanshou_royal",
                   status=EpistemicStatus.VERIFIED, confidence=0.9,
                   adopted_by="E9交付档案v2",
                   rationale="建置与使用者（李太后/冯保/宫中移钟）确证皇家寺院性质；"
                             "四阶段模型降级为现代概括"),
    BeliefAdoption(proposition_id="prop_huayan_mismatch",
                   status=EpistemicStatus.VERIFIED, confidence=0.9,
                   adopted_by="E9交付档案v2",
                   rationale="实物铭文核对与晚明文本并置，名实不符成立；"
                             "只呈现事实，不编造观察过程"),
    BeliefAdoption(proposition_id="prop_qianlong_1746",
                   status=EpistemicStatus.VERIFIED, confidence=0.9,
                   adopted_by="E9交付档案v2",
                   rationale="两诗文本俱在、分年确凿；解释升级发生在迁钟三年后"),
    BeliefAdoption(proposition_id="prop_modern_zhongjun",
                   status=EpistemicStatus.CONTESTED, confidence=0.6,
                   adopted_by="E9交付档案v2",
                   rationale="现代学者解释框架，标「有研究认为」；不作清廷自白"),
    BeliefAdoption(proposition_id="prop_js_qiyu_1778",
                   status=EpistemicStatus.VERIFIED, confidence=0.9,
                   adopted_by="E9交付档案v2",
                   rationale="一史馆藏档支撑 1778 起点；1787 旧说无出处已删除"),
    BeliefAdoption(proposition_id="prop_bell_qiyu_legend",
                   status=EpistemicStatus.DISPROVEN, confidence=0.85,
                   adopted_by="E9交付档案v2",
                   rationale="2023 专项课题核档未见钟参与记录，结项公告明言纠正讹传；"
                             "反驳证据为祈雨课题档案事实",
                   refuting_fact_ids=["tf_dzs_qiyu_2023", "tf_dzs_qiyu_1778"]),
    BeliefAdoption(proposition_id="prop_dazhongsi_name",
                   status=EpistemicStatus.VERIFIED, confidence=0.85,
                   adopted_by="E9交付档案v2",
                   rationale="迁钟→俗称→站名链条完整；俗称非敕名"),
    BeliefAdoption(proposition_id="prop_dian_after_bell",
                   status=EpistemicStatus.CONTESTED, confidence=0.55,
                   adopted_by="E9交付档案v2",
                   rationale="建筑学推断而非文献记载，标研究推断"),
    BeliefAdoption(proposition_id="prop_bingdao_legend",
                   status=EpistemicStatus.FOLK_LEGEND, confidence=0.35,
                   adopted_by="E9交付档案v2",
                   rationale="方法旁证（运巨石）不等于运钟史实；传说过传说层"),
    BeliefAdoption(proposition_id="prop_duitu_legend",
                   status=EpistemicStatus.FOLK_LEGEND, confidence=0.3,
                   adopted_by="E9交付档案v2",
                   rationale="堆土造山为民俗流传，无档案"),
    BeliefAdoption(proposition_id="prop_shendu_yaoguangxiao",
                   status=EpistemicStatus.CONTESTED, confidence=0.5,
                   adopted_by="E9交付档案v2",
                   rationale="晚明有载但缺同时代直接证据；既不贴民间传说也不作定论"),
]


# ==================================================================
# 8. 空间变化事件：迁钟链（汉经厂→万寿寺→卧地→觉生寺）
# ==================================================================

TRANSFORMATIONS: List[PlaceTransformation] = [
    PlaceTransformation(
        id="pte_ws_1577_built", entity_id="ent_wanshousi",
        transformation=PlaceTransformationEvent.CONSTRUCTED,
        time_span=_ts(1577, 1578, "ts_pte1"),
        resulting_state_id="st_ws_1578",
        resulting_condition="万历五年(1577)三月开工、六年(1578)六月竣工，「浃岁即成」",
        evidence_fact_ids=["tf_wlyhb_jiasui"],
    ),
    PlaceTransformation(
        id="pte_js_1734_built", entity_id="ent_jueshengsi",
        transformation=PlaceTransformationEvent.CONSTRUCTED,
        time_span=_ts(1733, 1734, "ts_pte2"),
        resulting_state_id="st_js_1734",
        resulting_condition="雍正十一年(1733)正月开工、十二年(1734)冬告成，爰赐名觉生寺"
                            "（开工与赐名分属两年）",
        evidence_fact_ids=["tf_dzs_1733", "tf_beiwen_ciming"],
    ),
    PlaceTransformation(
        id="pte_bell_1607_relocate", entity_id="ent_yongle_bell",
        transformation=PlaceTransformationEvent.RELOCATED,
        time_span=_ts(1607, 1607, "ts_pte3"),
        resulting_state_id="st_bell_wanshousi",
        resulting_condition="万历三十五年(1607)六月十六日自宫中徙置万寿寺大钟楼",
        evidence_fact_ids=["tf_yandijian_1607", "tf_zzz_zhonglou"],
    ),
    PlaceTransformation(
        id="pte_bell_tianqi_laid", entity_id="ent_yongle_bell",
        transformation=PlaceTransformationEvent.RELOCATED,
        time_span=TimeSpan(id="ts_pte4", label="天启年间撤下置地",
                           begin=_dt(1621, "ts_pte4b",
                                     _ry(Era.MING, "天启", 1, "天启元年"),
                                     precision="approximate"),
                           end=_dt(1627, "ts_pte4e")),
        resulting_state_id="st_bell_laid",
        resulting_condition="因讹言撤下置地，卧地约一百二十年前后（非「三百年」）",
        evidence_fact_ids=["tf_dzs_tianqi"],
    ),
    PlaceTransformation(
        id="pte_bell_1743_relocate", entity_id="ent_yongle_bell",
        transformation=PlaceTransformationEvent.RELOCATED,
        time_span=_ts(1743, 1743, "ts_pte5"),
        resulting_state_id="st_bell_jueshengsi",
        resulting_condition="乾隆八年(1743)移入觉生寺大钟殿",
        evidence_fact_ids=["tf_dzs_1743"],
    ),
    PlaceTransformation(
        id="pte_js_1985_museum", entity_id="ent_jueshengsi",
        transformation=PlaceTransformationEvent.REBUILT,
        time_span=_ts(1985, 1985, "ts_pte6"),
        resulting_state_id="st_js_1985",
        resulting_condition="寺辟为大钟寺古钟博物馆，原殿宇改钟铃展区（展品多为征集）",
        evidence_fact_ids=["tf_dzs_1985"],
    ),
]

AGGREGATES: List[PlaceAggregate] = []
