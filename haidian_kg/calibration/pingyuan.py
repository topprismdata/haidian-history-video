"""
haidian_kg/calibration/pingyuan.py
海淀平原水系聚落线词条：六郎庄 / 万泉庄·万泉河·泉宗庙 / 海淀（海淀镇） / 三里河（阜成门外）

一手底本（引文本地化纪律 §5.1）：
  - 《钦定日下旧闻考》四库全书本 卷076/卷079：haidian_kg/evaluation/holdout_v2_pilot_draft.jsonl
    （pilot_rixia_juan076 / pilot_rixia_juan079 段，commit f069e8b，繁體逐字）
  - 卷71（官署十·稻田厂）/卷95（郊坰西五）/卷99（郊坰西九）：维基文库全覽3/全覽4 繁體頁逐字，
    原文全文存 docs/kg/research/pingyuan.md
  - 《中堂事记上》（秋涧集卷八十，ctext 四库本）逐字
  - 海淀区人民政府公开资料（记录式陈述，L2）逐字

本批四级标签纪律的落点：
  1. 六郎庄名号链（牛栏庄→柳浪庄→六郎庄）有政府记录 + 乾隆官书用名双源；
     「柳浪雅化」机制是后世整理，不与史实混挂
  2. 杨六郎驻军 = FOLK_LEGEND（区政府原文即用「附会」定性）
  3. 「乾隆以六郎庄写法不吉而改名」回源核查为查无官书依据 → UNSUBSTANTIATED
     （无档案 ≠ 不存在，不做 DISPROVEN；乾隆朝官书仍作「六郎莊」为对照证据）
  4. 泉宗庙敕建年代采官书两处互证（乾隆三十一年春经始、三十二年落成、泉名二十有八）；
     本地长编「乾隆四十三年/十三处泉名」与官书抵牾，在命题层注明不采
  5. 泉宗庙 1860 受创/今无存仅二手口径（维基引北青网2011），不入 KB 状态层
  6. 「万泉河」河名无清代官书直书书证 → 水道本体有书证、河名按现代通行名挂接（指称标无据）
  7. 三里河（阜成门外）与正阳门外三里河（前三门泄水渠）同名异地，命题层消歧义；
     「金代开挑」无书证，只证钓鱼台为「大金時舊跡」，存疑待考
  8. 先有庄后有园：牛栏庄（明）早于畅春园（康熙朝敕建）与清漪园（1750）两个多世纪
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
    HistoricalFeatureState, PersistentSpatialEntity,
    PhysicalThingKind, PlaceAggregate, PlaceTransformation,
    ReferentialAssertion,
)
from .bibliography import source_by_title

CAL = CalibrationTable.CN_ASTRONOMICAL_ALMANAC


def _dt(y, tag, reign=None, precision="year"):
    return DatePoint(id=tag, label=str(y), precision=precision, reign_year=reign,
                     gregorian=GregorianDate(year=y, calibration=CAL))


def _ts(y1, y2, tag):
    return TimeSpan(id=tag, label="%d-%d" % (y1, y2),
                    begin=_dt(y1, tag + "_b"), end=_dt(y2, tag + "_e"))


def _ts_open(end_y, tag, label):
    """起始不可知的区间（早于最早书证）——begin 必须为 None，不伪造纪年"""
    return TimeSpan(id=tag, label=label, open_begin=True, begin=None,
                    end=_dt(end_y, tag + "_e"))


def _ry_qianlong(n, verbatim):
    return ReignYear(era=Era.QING, reign_title="乾隆", year_within_reign=n,
                     verbatim=verbatim)


# ==================================================================
# 1. 文献与篇卷
# ==================================================================

SOURCES: List[HistoricalSource] = [
    source_by_title("钦定日下旧闻考"),
    source_by_title("中堂事记"),
    source_by_title("长安客话"),
    source_by_title("北京市三山五园传统地名保护名录"),
    source_by_title("海淀区人民政府公开史地沿革资料"),
]

DIVISIONS: List[SourceDivision] = [
    SourceDivision(id="div_zt_juanshang", source_id="src_zhongtang",
                   volume_number="卷八十", section_title="中堂事记上"),
    SourceDivision(id="div_rxjwkc71_guanshi", source_id="src_rxjwkc",
                   volume_number="卷七十一", section_title="官署十·稻田厂"),
    SourceDivision(id="div_rxjwkc76_yuanyou", source_id="src_rxjwkc",
                   volume_number="卷七十六", section_title="国朝苑囿·畅春园"),
    SourceDivision(id="div_rxjwkc79_quanzong", source_id="src_rxjwkc",
                   volume_number="卷七十九", section_title="国朝苑囿·泉宗庙"),
    SourceDivision(id="div_rxjwkc95_jiaojiong", source_id="src_rxjwkc",
                   volume_number="卷九十五", section_title="郊垌西五"),
    SourceDivision(id="div_rxjwkc99_jiaojiong", source_id="src_rxjwkc",
                   volume_number="卷九十九", section_title="郊垌西九"),
    SourceDivision(id="div_ckh_haidian", source_id="src_changankehua",
                   volume_number="卷次待核",
                   section_title="海淀条（本批据《日下旧闻考》卷七十九转录，见pilot_rixia_juan079）"),
    SourceDivision(id="div_hd_gov_liulangzhuang", source_id="src_hd_gov_open",
                   volume_number="史地沿革资料",
                   section_title="六郎庄村史馆条（北京海淀2021-07-20，记录式陈述）"),
    SourceDivision(id="div_hd_gov_jianzhi", source_id="src_hd_gov_open",
                   volume_number="史地沿革资料",
                   section_title="建置沿革条（海淀区政府2022-06，记录式陈述）"),
    SourceDivision(id="div_minglu_2024_llz", source_id="src_2024_minglu",
                   volume_number="第一批",
                   section_title="六郎庄条（名称出现年代，命题层参照，本批未引原文）"),
]


# ==================================================================
# 2. 文本事实（官书为繁体逐字；政府资料为记录式陈述，分层不混）
# ==================================================================

FACTS: List[TextualFact] = [
    # ---- 海淀：元初「海店」书证（现存最早，1260） ----
    TextualFact(
        id="tf_zt_haidian", division_id="div_zt_juanshang",
        verbatim_quote="六日丁夘午，憇海店，距京城廿里，凡省部未絶，事务于此，悉行决遣。",
        attested_string="海店",
        translator_note="中统元年(1260)王恽随行中书省官员行经；「海店」为现存最早书证"
                        "（书证下限，非建村年代）。据ctext四库本秋涧集卷八十逐字。",
    ),
    # ---- 海淀：淀分南北（长安客话，经卷79转录） ----
    TextualFact(
        id="tf_ckh_beihaidian", division_id="div_ckh_haidian",
        verbatim_quote="髙梁橋西北十里平地有泉四出瀦為小溪凡數十處北為北海淀南為南海淀"
                       "北海之水來自巴溝或云巴溝即南海淀也",
        attested_string="北海淀",
        translator_note="转录自《日下旧闻考》卷七十九所引（pilot_rixia_juan079:L124-L134），"
                        "繁体逐字；「淀」之词源另见tf_dian_qianquan。",
    ),
    TextualFact(
        id="tf_dian_qianquan", division_id="div_rxjwkc79_quanzong",
        verbatim_quote="左思魏都賦有掘鯉之淀或云即狐狸淀廣韻淀泊屬韻㑹淺泉也今京師有南淀北淀",
        attested_string="淺泉",
        translator_note="《日下旧闻考》卷七十九所引字书训释：「淀，浅泉也」——海淀得名词源书证"
                        "（pilot_rixia_juan079:L117-L123）。",
    ),
    # ---- 海淀：区政府建置沿革（记录式陈述） ----
    TextualFact(
        id="tf_hd_gov_etym", division_id="div_hd_gov_jianzhi",
        verbatim_quote="海淀镇一带在古代是一片浅湖区，当地人称之为“海淀”。后来在湖边逐渐形成"
                       "居民聚落，亦以“海淀”命名。“海淀”在历史文献中亦称为“海甸”“海店”。"
                       "在现存史料中最早见于元初王恽所撰《中堂事记》（见明叶盛《水东日记》）。",
        attested_string="海淀",
        translator_note="海淀区政府《建置沿革》2022-06，记录式陈述（L2），非古籍引文。",
    ),
    TextualFact(
        id="tf_hd_gov_1952", division_id="div_hd_gov_jianzhi",
        verbatim_quote="1949年7月，在海淀地区正式设置单一行政区域，称北平市第十六区。后两次更名，"
                       "于1952年9月1日命名为海淀区。",
        attested_string="海淀区",
        translator_note="同上；区名承驻地海淀镇之名（ propositions 层论断）。",
    ),
    # ---- 六郎庄：官书用名 + 稻田厂官场（卷71） ----
    TextualFact(
        id="tf_dcf_liulangzhuang_guanchang", division_id="div_rxjwkc71_guanshi",
        verbatim_quote="臣等謹案稻田厰廨宇建於玉泉山之青龍橋南嚮存貯米石倉厫及官署碾房具備焉"
                       "又官場二處一在功徳寺西房四間一在六郎莊南房十六間",
        attested_string="六郎莊",
        translator_note="乾隆朝官书稻田厂条仍作「六郎莊」，官场设村中（南房十六间）——"
                        "六郎庄为官田管理节点；亦为「乾隆朝无改名记载」之对照证据。",
    ),
    # ---- 六郎庄：区政府记录（名号链/方位/搬迁） ----
    TextualFact(
        id="tf_llz_gov_chain", division_id="div_hd_gov_liulangzhuang",
        verbatim_quote="六郎庄明代称牛栏庄，因风景秀丽，柳丝如浪，雅称柳浪庄，清代附会杨家将故事"
                       "称六郎庄，据文字记载已有600余年的历史。",
        attested_string="六郎庄",
        translator_note="北京海淀2021-07-20记录式陈述（L2）；「附会」为区政府原文定性。",
    ),
    TextualFact(
        id="tf_llz_gov_loc", division_id="div_hd_gov_liulangzhuang",
        verbatim_quote="六郎庄村在海淀区西南部，西临昆明湖路，距颐和园东墙约半里",
        attested_string="六郎庄",
        translator_note="现代地貌记录（L2）；「畅春园在村东北」由此与园址互证，官书无直接方位句。",
    ),
    TextualFact(
        id="tf_llz_gov_relocate", division_id="div_hd_gov_liulangzhuang",
        verbatim_quote="如今六郎庄村已经整体搬迁",
        attested_string="六郎庄",
        translator_note="2021年报道时点已搬迁；搬迁年份未见于本批证据，状态层不列年代。",
    ),
    # ---- 畅春园（卷76，pilot_rixia_juan076） ----
    TextualFact(
        id="tf_ccy_zai_nan_haidian", division_id="div_rxjwkc76_yuanyou",
        verbatim_quote="暢春園在南海淀大河莊之北繚垣一千六十丈有竒暢春園冊",
        attested_string="南海淀",
        translator_note="pilot_rixia_juan076:L1-L1；「在南海淀」直证园林建于海淀地名所指地带。",
    ),
    TextualFact(
        id="tf_ccy_li_wei", division_id="div_rxjwkc76_yuanyou",
        verbatim_quote="臣等謹按暢春園本前明戚畹武清侯李偉别墅聖祖仁皇帝因故址改建爰錫嘉名",
        attested_string="暢春園",
        translator_note="pilot_rixia_juan076:L2-L9；畅春园=明李伟清华园故址改建（清园晚于明园）。",
    ),
    TextualFact(
        id="tf_ccy_ji_haidian", division_id="div_rxjwkc76_yuanyou",
        verbatim_quote="都城西直門外十二里曰海淀淀有南有北自萬泉莊平地湧泉奔流㶁㶁滙于丹稜沜"
                       "沜之大以百頃",
        attested_string="萬泉莊",
        translator_note="圣祖御制畅春园记（pilot_rixia_juan076:L10-L12）；康熙朝官书已用「万泉庄」。",
    ),
    # ---- 泉宗庙（卷79，pilot_rixia_juan079） ----
    TextualFact(
        id="tf_qzm_gui_zhi", division_id="div_rxjwkc79_quanzong",
        verbatim_quote="泉宗廟建於萬泉莊繚垣三百九十四丈廟南為池左右立坊二廟門三楹榜曰泉宗廟"
                       "廟内為涵澤門三楹正殿三楹左右為配殿後為樞光閣上下五楹左右配殿各五楹"
                       "　泉宗廟冊",
        attested_string="泉宗廟",
        translator_note="pilot_rixia_juan079:L1-L4，末尾「泉宗廟冊」为原书出处标注。",
    ),
    TextualFact(
        id="tf_qzm_1767_zhanli", division_id="div_rxjwkc79_quanzong",
        verbatim_quote="祠建泉宗始昨春落成此日禮泉神為開稻町資輸注亦搆松軒備豫廵",
        attested_string="泉宗",
        source_year=_dt(1767, "dt_qzm_shi",
                        reign=_ry_qianlong(32, "乾隆三十二年")),
        translator_note="乾隆三十二年御制六月四日诣泉宗庙瞻礼诗（pilot_rixia_juan079:L17-L22）；"
                        "「始昨春」＝庙建于前一年（乾隆三十一年，1766）春，本年（1767）落成。",
    ),
    TextualFact(
        id="tf_qzm_28quan", division_id="div_rxjwkc79_quanzong",
        verbatim_quote="臣等謹按廟内外淙泉之處皇上各賜嘉名立石以誌其在廟門之外者凡三"
                       "南曰大沙泉小沙泉北曰沸泉",
        attested_string="大沙泉",
        translator_note="pilot_rixia_juan079:L91-L103；二十八泉名目自此续列（总数十有八见卷99谨按）。",
    ),
    TextualFact(
        id="tf_wqz_ji_core", division_id="div_rxjwkc79_quanzong",
        verbatim_quote="夫人皆知此為萬泉莊而泉之源又實在此此不可不正其名而核其實也"
                       "因命所司建泉宗廟於此地若大沙小沙巴溝皆立碣以誌之",
        attested_string="萬泉莊",
        translator_note="御制万泉庄记（pilot_rixia_juan079:L76-L90）；庄名不见于《日下旧闻》"
                        "《春明梦余录》，泉源正在此，立碣以志。",
    ),
    TextualFact(
        id="tf_wqz_shui_nanbei", division_id="div_rxjwkc79_quanzong",
        verbatim_quote="泉出萬泉莊名原㵼北石橋惟賸説巴溝",
        attested_string="萬泉莊",
        source_year=_dt(1770, "dt_qzm_shi35",
                        reign=_ry_qianlong(35, "乾隆三十五年")),
        translator_note="乾隆三十五年出畅春园门自堤上至泉宗庙诗（pilot_rixia_juan079:L23-L25）；"
                        "诗自注考订：万泉庄地高于巴沟，其水实自南而北，驳《日下旧闻》"
                        "《春明梦余录》「丹棱沜水出巴沟达于高梁」旧说为耳食之讹。",
    ),
    TextualFact(
        id="tf_qzm_jianan_28", division_id="div_rxjwkc99_jiaojiong",
        verbatim_quote="臣等謹按萬泉莊泉源隨地湧現乾隆三十二年皇上始於其地建泉宗廟廟内之泉"
                       "錫嘉名者凡二十有八謹載入苑囿門其廟外之泉若大沙泉小沙泉亦皆立碣以誌之"
                       "自是水之由萬泉莊注巴溝由巴溝入暢春園者其源流始大著",
        attested_string="萬泉莊",
        translator_note="卷九十九臣等谨按（维基文库全覽4繁體逐字，链接见research）；"
                        "敕建年份+泉数二十八+水系方向（庄→巴沟→畅春园）一提前后互证。",
    ),
    # ---- 三里河（卷95，郊坰西五） ----
    TextualFact(
        id="tf_slh_zhongming", division_id="div_rxjwkc95_jiaojiong",
        verbatim_quote="鐘樓懸銅鐘一識明嘉靖甲午年五月阜成門外三里河池水村太監麥闕造等字",
        attested_string="三里河",
        translator_note="圆觉禅寺铜钟铭（维基文库全覽4繁體逐字）；「三里河」地名书证下限1534。",
    ),
    TextualFact(
        id="tf_slh_bei", division_id="div_rxjwkc95_jiaojiong",
        verbatim_quote="碑稱阜成闗不三四里許地名三里河有古刹靈佑闗剏自明季正徳間",
        attested_string="三里河",
        translator_note="无量庵顺治十六年(1659)重修碑所记（维基文库全覽4繁體逐字）。",
    ),
    TextualFact(
        id="tf_slh_diaotai_jin", division_id="div_rxjwkc95_jiaojiong",
        verbatim_quote="臣等謹按釣魚臺在三里河西北里許乃大金時舊跡也臺前有泉從地涌出冬夏不竭",
        attested_string="釣魚臺",
        translator_note="金代旧迹为钓鱼台（三里河西北里许），非三里河河道本身——"
                        "「金代开挑」存疑命题的对照书证。",
    ),
    TextualFact(
        id="tf_slh_qianlong_junzhi", division_id="div_rxjwkc95_jiaojiong",
        verbatim_quote="命濬治成湖以受香山新開引河之水復於下口建設閘座俾資蓄洩"
                       "湖水合引河水由三里河達阜成門之䕶城河",
        attested_string="三里河",
        translator_note="乾隆三十八年(1773)濬治玉渊潭条（维基文库全覽4繁體逐字）；"
                        "三里河为玉渊潭下泄水道。",
    ),
]


# ==================================================================
# 3. 实体
# ==================================================================

ENTITIES: List[PersistentSpatialEntity] = [
    PersistentSpatialEntity(id="ent_liulangzhuang", kind=PhysicalThingKind.SETTLEMENT_AREA,
                            canonical_label="六郎庄（畅春园西旧村）"),
    PersistentSpatialEntity(id="ent_wanquanzhuang", kind=PhysicalThingKind.SETTLEMENT_AREA,
                            canonical_label="万泉庄"),
    PersistentSpatialEntity(id="ent_wanquanhe", kind=PhysicalThingKind.NATURAL_WATERCOURSE,
                            canonical_label="万泉河（万泉庄泉水北流水道）"),
    PersistentSpatialEntity(id="ent_quanzongmiao", kind=PhysicalThingKind.RELIGIOUS_PRECINCT,
                            canonical_label="泉宗庙（万泉庄泉神祠）"),
    PersistentSpatialEntity(id="ent_haidian", kind=PhysicalThingKind.SETTLEMENT_AREA,
                            canonical_label="海淀（海淀镇）"),
    PersistentSpatialEntity(id="ent_sanlihe", kind=PhysicalThingKind.NATURAL_WATERCOURSE,
                            canonical_label="三里河（阜成门外·海淀）"),
]


# ==================================================================
# 4. 历时状态（每条状态挂证据；推断/传说落 §7 命题与采信层）
# ==================================================================

STATES: List[HistoricalFeatureState] = [
    # ---- 六郎庄 ----
    HistoricalFeatureState(
        id="st_llz_ming", entity_id="ent_liulangzhuang",
        time_span=_ts_open(1644, "ts_llz_ming", "明代（旧名牛栏庄）"),
        geometry="海淀台地间的农耕村落，京西水田带",
        material="土坯房舍、稻田沟渠",
        function="明京西郊农耕聚落（政府记录称明代已名牛栏庄，600余年文字记载为年代下限）",
        evidence_fact_ids=["tf_llz_gov_chain"],
    ),
    HistoricalFeatureState(
        id="st_llz_qing", entity_id="ent_liulangzhuang",
        time_span=_ts(1644, 1911, "ts_llz_qing"),
        geometry="畅春园之西、昆明湖（清漪园）东墙外约半里的村落；村中有稻田厂官场（南房十六间）",
        material="村舍、官场房十六间",
        function="皇家园林腹地服务村落与官田管理节点（官书卷七十一载官场在村，乾隆朝仍作六郎莊）",
        evidence_fact_ids=["tf_dcf_liulangzhuang_guanchang", "tf_llz_gov_chain", "tf_llz_gov_loc"],
    ),
    HistoricalFeatureState(
        id="st_llz_modern", entity_id="ent_liulangzhuang",
        time_span=_ts_open(2026, "ts_llz_modern", "近年已整体搬迁（年份无档案，不列）"),
        geometry="村落形态消失，村民整体搬迁；村史馆设于树村北街",
        material=None,
        function="地名延续于路名与公园；现状按区政府2021年记录，搬迁年份无档案不列",
        evidence_fact_ids=["tf_llz_gov_relocate"],
    ),
    # ---- 万泉庄（泉群所在聚落） ----
    HistoricalFeatureState(
        id="st_wqz_springs", entity_id="ent_wanquanzhuang",
        time_span=_ts(1687, 1911, "ts_wqz_springs"),
        geometry="平地涌泉的泉群带（大沙泉、小沙泉等），庄地高于巴沟，其水自南而北流",
        material=None,
        function="海淀淀湖水系的泉源地；乾隆考订「泉之源正在此」，庙内外立碣名泉二十有八",
        evidence_fact_ids=["tf_ccy_ji_haidian", "tf_wqz_ji_core", "tf_qzm_jianan_28",
                           "tf_wqz_shui_nanbei"],
    ),
    # ---- 万泉河（水道本体有书证；河名为现代通行名，见指称层） ----
    HistoricalFeatureState(
        id="st_wqh_qing", entity_id="ent_wanquanhe",
        time_span=_ts(1687, 1911, "ts_wqh_qing"),
        geometry="万泉庄泉群北流注巴沟、由巴沟入畅春园一带淀湖（乾隆考订水自南而北，非南流）",
        material=None,
        function="海淀淀湖水系的南源补给水道；官书卷九十九：「水之由万泉庄注巴沟由巴沟入畅春园」",
        evidence_fact_ids=["tf_qzm_jianan_28", "tf_wqz_shui_nanbei"],
        upstream_entity_ids=["ent_wanquanzhuang"],
    ),
    # ---- 泉宗庙（庙依泉立：与万泉庄分挂两实体） ----
    HistoricalFeatureState(
        id="st_qzm_build", entity_id="ent_quanzongmiao",
        time_span=_ts(1766, 1767, "ts_qzm_build"),
        geometry="敕建皇家庙宇园林：缭垣三百九十四丈，庙南为池，立坊二，庙门三楹",
        material="官式殿宇、缭垣",
        function="乾隆三十一年(1766)春经始，三十二年(1767)六月落成，奉皇太后瞻礼",
        evidence_fact_ids=["tf_qzm_1767_zhanli", "tf_qzm_gui_zhi", "tf_qzm_jianan_28"],
    ),
    HistoricalFeatureState(
        id="st_qzm_standing", entity_id="ent_quanzongmiao",
        time_span=_ts(1767, 1911, "ts_qzm_standing"),
        geometry="普润殿供龙神，后为枢光阁；庙内外淙泉二十八处赐嘉名立石（大沙泉、小沙泉、沸泉等）",
        material="官式殿宇、缭垣",
        function="祀万泉庄泉群水神的皇家祠庙（庙依泉立，泉在庙中；引文仅证祀泉/礼泉神与水利资灌，「祈雨」无一手明文,降为现代功能解释——GPT审3-11）",
        evidence_fact_ids=["tf_qzm_gui_zhi", "tf_qzm_28quan", "tf_qzm_jianan_28"],
    ),
    # ---- 海淀（海淀镇） ----
    HistoricalFeatureState(
        id="st_hd_yuan", entity_id="ent_haidian",
        time_span=_ts(1260, 1368, "ts_hd_yuan"),
        geometry="大都城西北约二十里道侧水畔聚落（书证作「海店」）",
        material=None,
        function="1260年「海店」为现存最早地名书证下限（原句只证地名与里程,「淀泊畔聚落」系推读——GPT审3-12），非建村年代",
        evidence_fact_ids=["tf_zt_haidian", "tf_hd_gov_etym"],
    ),
    HistoricalFeatureState(
        id="st_hd_ming", entity_id="ent_haidian",
        time_span=_ts(1368, 1644, "ts_hd_ming"),
        geometry="明人所记为南/北海淀水域地望（高梁桥西北十里，平地泉四出）；「两聚落带」之聚落定性另待户籍坊里市集类书证（GPT审3-12）",
        material=None,
        function="京西名胜之地（明人记水域地望；聚落属性另证——GPT审3-12）",
        evidence_fact_ids=["tf_ckh_beihaidian", "tf_dian_qianquan"],
    ),
    HistoricalFeatureState(
        id="st_hd_qing", entity_id="ent_haidian",
        time_span=TimeSpan(id="ts_hd_qing", label="清代（园林借地而起）",
                           open_begin=True, begin=None, end=_dt(1911, "ts_hd_qing_e")),
        geometry="畅春园在南海淀大河庄之北（就明李伟清华园故址改建），园林借海淀之地而起，"
                 "海淀镇为三山五园门户集镇",
        material=None,
        function="皇家园林腹地与门户集镇",
        evidence_fact_ids=["tf_ccy_zai_nan_haidian", "tf_ccy_li_wei", "tf_ccy_ji_haidian"],
    ),
    HistoricalFeatureState(
        id="st_hd_modern", entity_id="ent_haidian",
        time_span=_ts(1949, 2026, "ts_hd_modern"),
        geometry="北平市第十六区（1949）驻地海淀镇；后两次更名，1952年9月1日定名海淀区",
        material=None,
        function="市辖区得名地（区名承驻地海淀镇之名）；海淀镇今已城市化",
        evidence_fact_ids=["tf_hd_gov_1952", "tf_hd_gov_etym"],
    ),
    # ---- 三里河（阜成门外） ----
    HistoricalFeatureState(
        id="st_slh_ming", entity_id="ent_sanlihe",
        time_span=_ts(1534, 1644, "ts_slh_ming"),
        geometry="阜成门外三四里的水道地片（旁有池水村），地名三里河",
        material=None,
        function="城西郊水道聚落片（嘉靖钟铭为地名书证下限；「金代开挑」无书证，见存疑命题）",
        evidence_fact_ids=["tf_slh_zhongming", "tf_slh_bei"],
    ),
    HistoricalFeatureState(
        id="st_slh_qing", entity_id="ent_sanlihe",
        time_span=_ts(1659, 1911, "ts_slh_qing"),
        geometry="玉渊潭下泄水道：乾隆三十八年濬治成湖、下口建闸，湖水合引河水由三里河达阜成门护城河",
        material=None,
        function="玉渊潭蓄泄水道，分流入前三门城河与通惠河",
        evidence_fact_ids=["tf_slh_bei", "tf_slh_qianlong_junzhi", "tf_slh_diaotai_jin"],
    ),
]


# ==================================================================
# 5. 身份断言（本批无跨模块同指；同名异地消歧义落命题层）
# ==================================================================

IDENTITIES: List[DiachronicIdentityAssertion] = []


# ==================================================================
# 6. 名称与指称
# ==================================================================

APPELLATIONS: List[Appellation] = [
    # 六郎庄名号链（同一持续体的三个名称期）
    Appellation(id="app_llz_niulanzhuang", label="牛栏庄", kind=AppellationKind.OLD_NAME,
                valid_time_span=_ts_open(1644, "ts_n_llz_nlz", "明代旧名"),
                attesting_fact_ids=["tf_llz_gov_chain"]),
    Appellation(id="app_llz_liulangzhuang", label="柳浪庄", kind=AppellationKind.EUPHEMISTIC,
                valid_time_span=_ts_open(1900, "ts_n_llz_llz", "明清间雅称"),
                attesting_fact_ids=["tf_llz_gov_chain"]),
    Appellation(id="app_llz", label="六郎庄", kind=AppellationKind.OFFICIAL,
                valid_time_span=TimeSpan(id="ts_n_llz", label="清代至今",
                                         open_begin=True, begin=None,
                                         end=_dt(2026, "ts_n_llz_e"), open_end=True),
                script_variants=["六郎莊"],
                attesting_fact_ids=["tf_dcf_liulangzhuang_guanchang", "tf_llz_gov_chain"]),
    # 万泉庄 / 万泉河 / 泉宗庙
    Appellation(id="app_wqz", label="万泉庄", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1687, 1911, "ts_n_wqz"),
                script_variants=["萬泉莊"],
                attesting_fact_ids=["tf_ccy_ji_haidian", "tf_qzm_jianan_28"]),
    Appellation(id="app_wqh", label="万泉河", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts_open(2026, "ts_n_wqh", "现代通行河名"),
                attesting_fact_ids=[]),
    Appellation(id="app_qzm", label="泉宗庙", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1767, 1911, "ts_n_qzm"),
                script_variants=["泉宗廟"],
                attesting_fact_ids=["tf_qzm_gui_zhi", "tf_qzm_jianan_28"]),
    # 海淀（地名本体）
    Appellation(id="app_hd", label="海淀", kind=AppellationKind.OFFICIAL,
                valid_time_span=TimeSpan(id="ts_n_hd", label="明清至今",
                                         open_begin=True, begin=None,
                                         end=_dt(2026, "ts_n_hd_e"), open_end=True),
                script_variants=["海甸"],
                attesting_fact_ids=["tf_hd_gov_etym", "tf_ckh_beihaidian"]),
    Appellation(id="app_hd_haidian_dian", label="海淀镇", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts_open(2026, "ts_n_hd_dian", "近代以来镇称"),
                attesting_fact_ids=["tf_hd_gov_etym"]),
    Appellation(id="app_hd_haidian", label="海店", kind=AppellationKind.OLD_NAME,
                valid_time_span=_ts_open(1368, "ts_n_hd_hd", "元初旧名"),
                attesting_fact_ids=["tf_zt_haidian", "tf_hd_gov_etym"]),
    Appellation(id="app_bhd", label="北海淀", kind=AppellationKind.OLD_NAME,
                valid_time_span=_ts(1368, 1687, "ts_n_bhd"),
                attesting_fact_ids=["tf_ckh_beihaidian"]),
    Appellation(id="app_nhd", label="南海淀", kind=AppellationKind.OLD_NAME,
                valid_time_span=_ts(1368, 1687, "ts_n_nhd"),
                attesting_fact_ids=["tf_ckh_beihaidian", "tf_ccy_zai_nan_haidian"]),
    # 三里河（阜成门外）
    Appellation(id="app_slh", label="三里河", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1534, 2026, "ts_n_slh"),
                attesting_fact_ids=["tf_slh_zhongming", "tf_slh_bei"]),
]

REFERENCES: List[ReferentialAssertion] = [
    ReferentialAssertion(id="rr_llz_nlz", appellation_id="app_llz_niulanzhuang",
                         referent_entity_id="ent_liulangzhuang",
                         time_span=_ts_open(1644, "ts_r_llz_nlz", "明代指称"),
                         evidence_fact_ids=["tf_llz_gov_chain"]),
    ReferentialAssertion(id="rr_llz_ya", appellation_id="app_llz_liulangzhuang",
                         referent_entity_id="ent_liulangzhuang",
                         time_span=_ts_open(1900, "ts_r_llz_ya", "明清间指称"),
                         evidence_fact_ids=["tf_llz_gov_chain"]),
    ReferentialAssertion(id="rr_llz", appellation_id="app_llz",
                         referent_entity_id="ent_liulangzhuang",
                         time_span=TimeSpan(id="ts_r_llz", label="清代至今",
                                            open_begin=True, begin=None,
                                            end=_dt(2026, "ts_r_llz_e"), open_end=True),
                         evidence_fact_ids=["tf_dcf_liulangzhuang_guanchang",
                                            "tf_llz_gov_chain"]),
    ReferentialAssertion(id="rr_wqz", appellation_id="app_wqz",
                         referent_entity_id="ent_wanquanzhuang",
                         time_span=_ts(1687, 1911, "ts_r_wqz"),
                         evidence_fact_ids=["tf_ccy_ji_haidian", "tf_qzm_jianan_28"]),
    ReferentialAssertion(id="rr_wqh", appellation_id="app_wqh",
                         referent_entity_id="ent_wanquanhe",
                         time_span=_ts_open(2026, "ts_r_wqh", "现代指称"),
                         evidence_fact_ids=[],
                         status=EpistemicStatus.UNSUBSTANTIATED,
                         provenance="「万泉河」为现代通行河名；本批未取得清代官书直书"
                                    "「万泉河」三字的书证，水道本体另有卷79/卷99书证"
                                    "（庄泉注巴沟入畅春园），此指称按现代名挂接"),
    ReferentialAssertion(id="rr_qzm", appellation_id="app_qzm",
                         referent_entity_id="ent_quanzongmiao",
                         time_span=_ts(1767, 1911, "ts_r_qzm"),
                         evidence_fact_ids=["tf_qzm_gui_zhi", "tf_qzm_jianan_28"]),
    ReferentialAssertion(id="rr_hd", appellation_id="app_hd",
                         referent_entity_id="ent_haidian",
                         time_span=TimeSpan(id="ts_r_hd", label="明清至今",
                                            open_begin=True, begin=None,
                                            end=_dt(2026, "ts_r_hd_e"), open_end=True),
                         evidence_fact_ids=["tf_hd_gov_etym", "tf_ckh_beihaidian"]),
    ReferentialAssertion(id="rr_hd_dian", appellation_id="app_hd_haidian_dian",
                         referent_entity_id="ent_haidian",
                         time_span=_ts_open(2026, "ts_r_hd_dian", "近代以来指称"),
                         evidence_fact_ids=["tf_hd_gov_etym"]),
    ReferentialAssertion(id="rr_hd_haidian", appellation_id="app_hd_haidian",
                         referent_entity_id="ent_haidian",
                         time_span=_ts_open(1368, "ts_r_hd_hd", "元初指称"),
                         evidence_fact_ids=["tf_zt_haidian"]),
    ReferentialAssertion(id="rr_bhd", appellation_id="app_bhd",
                         referent_entity_id="ent_haidian",
                         time_span=_ts(1368, 1687, "ts_r_bhd"),
                         evidence_fact_ids=["tf_ckh_beihaidian"]),
    ReferentialAssertion(id="rr_nhd", appellation_id="app_nhd",
                         referent_entity_id="ent_haidian",
                         time_span=_ts(1368, 1687, "ts_r_nhd"),
                         evidence_fact_ids=["tf_ckh_beihaidian"]),
    ReferentialAssertion(id="rr_slh", appellation_id="app_slh",
                         referent_entity_id="ent_sanlihe",
                         time_span=_ts(1534, 2026, "ts_r_slh"),
                         evidence_fact_ids=["tf_slh_zhongming", "tf_slh_bei"]),
]


# ==================================================================
# 7. 断言与采信：把降格结论固化（推断/传说/现代观点绝不混级为史实）
# ==================================================================

PROPOSITIONS: List[Proposition] = [
    Proposition(
        id="prop_llz_namechain",
        statement="六郎庄名号演变链：明代牛栏庄→（雅称）柳浪庄→清代六郎庄；"
                  "乾隆朝官书稻田厂条仍作「六郎莊」",
        derived_from_fact_ids=["tf_llz_gov_chain", "tf_dcf_liulangzhuang_guanchang"],
        inferred_subject_id="ent_liulangzhuang",
        inference_method="海淀区政府记录式陈述与《日下旧闻考》卷七十一官书用名互证；"
                         "「明」代下限取「600余年文字记载」；雅化机制属后世整理口径",
        alternative_explanations=[
            "民间另有「宋将驻兵纪念说」，无史料支撑（见 prop_llz_yangliulang）",
            "「康熙五十一年(1712)内务府总管赫奕奏折已见六郎庄」系二手转述，"
            "本批未亲见原件，不列事实层",
        ],
    ),
    Proposition(
        id="prop_llz_yangliulang",
        statement="杨六郎驻军六郎庄为民间传说附会，非宋辽史实",
        derived_from_fact_ids=["tf_llz_gov_chain"],
        inferred_subject_id="ent_liulangzhuang",
        inference_method="区政府原文即用「附会」定性；宋辽对峙前线在河北中部白沟河一线，"
                         "今海淀不在宋辽边境（现代历史地理常识性判断）；中新网2012报道同口径",
        alternative_explanations=[
            "村民纪念杨六郎的口碑传说（民间流传，不入事实链）",
            "附会出「拴马桩」「挂甲塔」等衍生传说地名",
        ],
    ),
    Proposition(
        id="prop_llz_qianlong_taboo",
        statement="「乾隆帝以『六郎庄』写法不吉而改名」之说查无官书依据",
        derived_from_fact_ids=["tf_dcf_liulangzhuang_guanchang"],
        inferred_subject_id="ent_liulangzhuang",
        inference_method="回源核查：乾隆朝官书《日下旧闻考》卷七十一稻田厂条仍作「六郎莊」，"
                         "无改名诏档/御制诗文记载；多轮检索未命中任何档案级来源",
        alternative_explanations=[
            "民间同类「因不吉欲改名」故事多系于慈禧太后（欲改「吉祥庄」未果），"
            "性质同为口头传说",
            "「六郎」谐音「落难」避讳说仅见晚近文旅解说与网络文章",
            "无档案≠不存在（absence of evidence），故标无据推论而非已证伪",
        ],
    ),
    Proposition(
        id="prop_llz_spatial",
        statement="先有庄后有园：牛栏庄（明）早于畅春园（康熙朝就李伟清华园故址改建）与"
                  "清漪园（乾隆十五年，1750）两个多世纪以上；六郎庄位于畅春园之西、"
                  "清漪园（颐和园）东墙外约半里",
        derived_from_fact_ids=["tf_llz_gov_chain", "tf_llz_gov_loc", "tf_ccy_li_wei"],
        inferred_subject_id="ent_liulangzhuang",
        inference_method="年代先后由村名记载年代与两园建置（明园故址改建/1750）比对；"
                         "「畅春园西」由今存地貌（园址在东北，村址在西侧昆明湖东岸）"
                         "与政府记录互证",
        alternative_explanations=[
            "乾隆朝官书无「六郎庄在畅春园西」的直接方位句，"
            "此为现代记录与地图学结论（不冒充官书方位）",
        ],
    ),
    Proposition(
        id="prop_qzm_date",
        statement="泉宗庙敕建年代：乾隆三十一年（1766）春经始，三十二年（1767）落成瞻礼；"
                  "庙内外淙泉锡嘉名者凡二十有八",
        derived_from_fact_ids=["tf_qzm_1767_zhanli", "tf_qzm_jianan_28"],
        inferred_subject_id="ent_quanzongmiao",
        inference_method="卷七十九御制诗「祠建泉宗始昨春落成此日」+卷九十九臣等谨按"
                         "「乾隆三十二年皇上始於其地建泉宗庙……锡嘉名者凡二十有八」"
                         "两处官书互证（pilot 一手原文）",
        alternative_explanations=[
            "本项目肖家河长编（era7_qing.md L31）作「乾隆四十三年敕建」「考订十三处泉名」——"
            "与卷七十九/卷九十九官书抵牾（泉数亦不合），不采、不取区间值",
        ],
    ),
    Proposition(
        id="prop_wqz_wanquan",
        statement="万泉庄为泉源所自出：庄名不见于《日下旧闻》《春明梦余录》，"
                  "乾隆考订「泉之源正在此」并立碣志名；水系方向自南而北"
                  "（庄泉注巴沟，由巴沟入畅春园一带淀湖）",
        derived_from_fact_ids=["tf_wqz_ji_core", "tf_qzm_jianan_28", "tf_wqz_shui_nanbei",
                               "tf_ccy_ji_haidian"],
        inferred_subject_id="ent_wanquanzhuang",
        inference_method="御制万泉庄记与卷九十九按语直证；乾隆以地势（庄高于巴沟高于丹棱沜）"
                         "订《长安客话》诸书「达高梁」逆流之讹",
        alternative_explanations=[
            "《日下旧闻》《春明梦余录》旧说以丹棱沜水出巴沟达于高梁——"
            "乾隆判为耳食之讹（「其水实自南而北，安得由巴沟逆流」）",
        ],
    ),
    Proposition(
        id="prop_hd_root",
        statement="「海淀」为系列地名之根：词源为浅湖之淀（《广韵》淀浅泉也）；"
                  "元初书证作「海店」（1260，现存最早）；淀分南北（北海淀/南海淀）；"
                  "清代皇家园林借地而起（畅春园在南海淀大河庄之北）；"
                  "1952年9月1日第十三区定名海淀区，区名承驻地海淀镇之名",
        derived_from_fact_ids=["tf_hd_gov_etym", "tf_zt_haidian", "tf_dian_qianquan",
                               "tf_ckh_beihaidian", "tf_ccy_zai_nan_haidian",
                               "tf_hd_gov_1952"],
        inferred_subject_id="ent_haidian",
        inference_method="区政府建置沿革记录+《中堂事记》书证+官书所引《长安客话》/康熙御制记"
                         "互证；区名承镇名、镇名承淀名的得名链",
        alternative_explanations=[
            "「海淀」得名另有「淀泊连片如海」与「南北淀合称」诸推断，均为词源推测，"
            "本批不判其优劣",
        ],
    ),
    Proposition(
        id="prop_slh_jindai",
        statement="海淀三里河「金代开挑」存疑待考：金代旧迹惟钓鱼台（三里河西北里许，"
                  "「乃大金時舊跡」），河道本身之金代起源无书证；"
                  "地名书证下限为明嘉靖甲午（1534）钟铭",
        derived_from_fact_ids=["tf_slh_diaotai_jin", "tf_slh_zhongming", "tf_slh_bei"],
        inferred_subject_id="ent_sanlihe",
        inference_method="钓鱼台金代旧迹为官书按语直证；三里河作为地名/水道的明证仅见"
                         "嘉靖钟铭与顺治碑；金主游幸处的存在不能推出水道为金代所挑"
                         "（场所年代与水道年代分层验证）",
        alternative_explanations=[
            "或说金中都水系（金水河/闸河）经此——本批未见书证支撑，存疑",
            "或说河道本为自然水道、后世疏浚——与乾隆三十八年濬治记录相容，但金代开挑仍无证",
        ],
    ),
    Proposition(
        id="prop_slh_disambig",
        statement="本条三里河为阜成门外三里河（今甘家口一带，海淀南部水道地片），"
                  "非正阳门外三里河（前三门泄水渠，今前门东三里河公园）——同名异地",
        derived_from_fact_ids=["tf_slh_zhongming", "tf_slh_bei", "tf_slh_qianlong_junzhi"],
        inferred_subject_id="ent_sanlihe",
        inference_method="官书本批三条书证均系于阜成门外；两名各因距城门里数得名，"
                         "城市线（前三门三里河）不在本批范围",
        alternative_explanations=[
            "正阳门外三里河见于明代城市水系记录，应由城区地名词条线另建实体并消歧",
        ],
    ),
]

ADOPTIONS: List[BeliefAdoption] = [
    BeliefAdoption(proposition_id="prop_llz_namechain", status=EpistemicStatus.VERIFIED,
                   confidence=0.85, adopted_by="pingyuan批2026-10-02",
                   rationale="官书用名+政府记录双源；演变机制细节标后世整理"),
    BeliefAdoption(proposition_id="prop_llz_yangliulang", status=EpistemicStatus.FOLK_LEGEND,
                   confidence=0.3, adopted_by="pingyuan批2026-10-02",
                   rationale="区政府原文「附会」定性+宋辽前线不在今海淀；holdout防线明令"
                             "只能标FOLK_LEGEND"),
    BeliefAdoption(proposition_id="prop_llz_qianlong_taboo",
                   status=EpistemicStatus.UNSUBSTANTIATED, confidence=0.3,
                   adopted_by="pingyuan批2026-10-02",
                   rationale="回源核查无官书依据；无档案≠不存在，故不标已证伪"),
    BeliefAdoption(proposition_id="prop_llz_spatial", status=EpistemicStatus.VERIFIED,
                   confidence=0.8, adopted_by="pingyuan批2026-10-02",
                   rationale="年代先后有建置证据；「畅春园西」方位无官书直接句故不满分"),
    BeliefAdoption(proposition_id="prop_qzm_date", status=EpistemicStatus.VERIFIED,
                   confidence=0.95, adopted_by="pingyuan批2026-10-02",
                   rationale="卷79御制诗+卷99谨按两处官书互证（pilot一手原文）；"
                             "长编讹数已在命题层注明不采"),
    BeliefAdoption(proposition_id="prop_wqz_wanquan", status=EpistemicStatus.VERIFIED,
                   confidence=0.9, adopted_by="pingyuan批2026-10-02",
                   rationale="御制万泉庄记与按语直证；水系方向有乾隆地势考订"),
    BeliefAdoption(proposition_id="prop_hd_root", status=EpistemicStatus.VERIFIED,
                   confidence=0.85, adopted_by="pingyuan批2026-10-02",
                   rationale="书证+政府记录互证；词源层为推断故不满分"),
    BeliefAdoption(proposition_id="prop_slh_jindai", status=EpistemicStatus.CONTESTED,
                   confidence=0.5, adopted_by="pingyuan批2026-10-02",
                   rationale="金代说无书证；明代1534下限确凿；争议双方并列"),
    BeliefAdoption(proposition_id="prop_slh_disambig", status=EpistemicStatus.VERIFIED,
                   confidence=0.9, adopted_by="pingyuan批2026-10-02",
                   rationale="官书三条书证均系阜成门外；城市线同名实体待城区词条线处理"),
]


# ==================================================================
# 8. 空间变化事件 / 集合（本批不立：搬迁无年份档案，不伪造纪年）
# ==================================================================

TRANSFORMATIONS: List[PlaceTransformation] = []

AGGREGATES: List[PlaceAggregate] = []
