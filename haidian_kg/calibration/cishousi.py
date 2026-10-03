"""
haidian_kg/calibration/cishousi.py
慈寿寺／永安万寿塔词条 —— 海淀历史地名知识库 E19 入库模块

数据唯一来源：《慈寿寺》研究档案 v1.1（cishousi_video/research.md，2026-10-03 闸门 C01–C10 修订后冻结）。

证据分级映射（research.md 六级 → 本体表达，绝不混级）：
  [文献记载]   → TextualFact（古籍逐字引文）+ VERIFIED
  [官书]       → TextualFact（卷 97 按语等官书原话）+ VERIFIED
  [目验级时人记] → TextualFact（天咫偶闻「寺毁尽，惟浮图及碑存」）
  [校勘推定]   → Proposition + BeliefAdoption(CONTESTED)，**不升 VERIFIED**
  [寺僧相传]   → FOLK_LEGEND（「寺有僧自言梦」出自佛书，属寺僧口述层）
  [现行口径]   → TextualFact + 挂现行机构（文物局/园林局/交通委），与古代层分挂

E19 闸门红线落位（research.md §4 冻结规则）：
  - C01（最重要）：「塔在 1576 年内竣工」= 校勘推定 inferred_emendation，**不是直接实证**。
    野获编「故地經始于萬曆四年凡二歲告成」一句的宾语是「故地」（寺基址），塔在同一句中
    未被列为落成宾语；用同页按语「臣等謹按慈壽寺及塔」回溯改写引文宾语属跨层取证
    （按语层→引文层），E9 纪禁止。canonical = 塔与寺同期兴建；1578 整体落成不动。
  - 建寺缘起（荐冥祉＋祈嗣）与九莲菩萨梦**严格分层**：梦是造像层/信仰层，不是建寺之因。
  - 建寺资金=集资非独资（捐帑＋潞王公主宫眷内侍各助），禁「太后独资」。
  - 一塔二碑，无双塔（「两」的是塔下碑亭里的两通碑）。
  - 1757 只称「奉敕修葺」，规模无载，禁「乾隆大修/重建」。
  - 寺毁过程不虚构：「光绪间寺毁，惟浮图及碑存」是一手锚，火情细节无任何一手记载。
  - 双碑像主采卷 97 官书口径（左紫竹观音／右鱼篮观音），文物局「左刻九莲菩萨」另挂
    CONTESTED 现代表述；九莲是寺内后殿供奉像，**不是碑刻像**。
  - 张居正碑 1783 已无存：所引碑文出自《明张文忠公全集》传世文本，禁写「碑现存」。
  - 天宁寺「隋塔摹也」三层分挂：明人认隋 → 今考辽；口播不得写成「仿辽塔而建的辽式塔」。
  - 塔高只说「近 50 米」（文物部门口径），禁伪精确如「50.36 米」。

2026-10-03 像素级复核修正（E19 研究层发现的三处伪引文，勿回退）：
  - 《帝京景物略》卷五原 KB 引文「慈寿寺在阜成门外八里庄，神宗生母李太后建，浮屠十三级，
    巍峨插天，京师地标也」**在卷五影印本中不存在**（p92/p93 逐字核对）。已改为实读到的
    「宗祈胤嗣卜地阜成門外八里建寺，有永安壽塔塔十三級」。
  - 《燕都游览志》卷三「八里庄有慈寿寺舍利宝塔，雕饰玲珑秀出」与卷 97 按语所引不符
    （按语只记「宝藏阁系圣母御笔题…今頺楹殘礎」），VERIFIED 降 CONTESTED。
  - 「慈寿寺毁于清末大火」——火灾细节无一手记载，改为「光绪间寺毁，惟浮图及碑存」。

口播转录纪律（E19 血泪教训）：书影引文**必须逐字放大直读**。本次曾对影印本书影做目视转写，
引入四处讹字（皆/告、竣/就、郎/邸、空塔波/窣堵波），且讹字恰落在最要紧的论断字上，
并据此试图推翻 C01。下游引文库请勿以「目视」为凭。
"""
from typing import List

from .bibliography import source_by_title
from ..ontology.temporal import (
    CalibrationTable, DatePoint, GregorianDate, TimeSpan,
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


# ==================================================================
# 工具
# ==================================================================

# 换算基准：与 dazhongsi.py 同款，中国历代 astronomical almanac 换算法
CAL = CalibrationTable.CN_ASTRONOMICAL_ALMANAC


def _dt(y, tag, reign=None, precision="year"):
    return DatePoint(id=tag, label=str(y), precision=precision, reign_year=reign,
                     gregorian=GregorianDate(year=y, calibration=CAL))


def _ts(y1, y2, tag):
    return TimeSpan(id=tag, label="%d-%d" % (y1, y2),
                    start=_dt(y1, tag + "_s"), end=_dt(y2, tag + "_e"))


# ==================================================================
# 书源与篇卷
# ==================================================================

SOURCES: List[HistoricalSource] = [
    # v2.1：一律取自统一书目表，一书一条，禁止在此另建
    source_by_title("钦定日下旧闻考"),
    source_by_title("帝京景物略"),
    source_by_title("天咫偶闻"),
    source_by_title("万历野获编"),
    source_by_title("明张文忠公全集"),
]

DIVISIONS: List[SourceDivision] = [
    # 卷 97 慈寿寺条——本集最硬的一手官书层，且有原书影印（2026-10-03 像素级直读）
    SourceDivision(id="div_rxjwkc97_cishousi", source_id="src_rxjwkc",
                   volume_number="卷九十七", section_title="慈寿寺条"),
    # 卷 100 慈寿寺条（「隆慶丙子」讹文所在，正片不采）
    SourceDivision(id="div_rxjwkc100_cishousi", source_id="src_rxjwkc",
                   volume_number="卷一百", section_title="慈寿寺条"),
    SourceDivision(id="div_djwl5_cishousi", source_id="src_dijingjingwulue",
                   volume_number="卷五", section_title="慈寿寺条"),
    SourceDivision(id="div_tzoyw9_cishousi", source_id="src_tianzhi_ouwen",
                   volume_number="卷九", section_title="西郊诸寺·慈寿寺"),
    SourceDivision(id="div_yhls_cishousi", source_id="src_wanliyehuobian",
                   volume_number="卷次待核", section_title="转引慈寿寺碑"),
    SourceDivision(id="div_zwzjj_beizhi", source_id="src_zhangjuzheng_jiwen",
                   volume_number="文集卷四", section_title="敕建大慈寿寺碑记"),
]


# ==================================================================
# 文本事实层（逐字引文，繁体原字形）
# 注意：以下引文为 2026-10-03 对原书影印逐字放大直读所得，
#      讹字（皆/告、竣/就、郎/邸、空塔波/窣堵波）已在上游修正。
# ==================================================================

FACTS: List[TextualFact] = [
    # —— 卷 97：本集最硬证据之一 ——
    TextualFact(
        id="tf_cs97_location",
        division_id="div_rxjwkc97_cishousi",
        verbatim_quote="原慈壽寺去阜成門八里聖母慈聖皇太后所建",
        attested_string="慈壽寺",
        source_year=_dt(1783, "dt_rxjwkc97_comp", precision="decade"),
    ),
    TextualFact(
        id="tf_cs97_completion",
        division_id="div_rxjwkc97_cishousi",
        verbatim_quote="蓋正德間大增谷大用故地經始于萬曆四年凡二歲告成",
        attested_string="故地經始于萬曆四年凡二歲告成",
        source_year=_dt(1783, "dt_rxjwkc97_comp", precision="decade"),
        translator_note=(
            "E19 闸门 C01 关键句。宾语是「故地」（太监谷大用故地＝寺基址），"
            "**塔在同一句中未被列为落成宾语**；其下「名永安塔」是记塔名状而非记塔成。"
            "「告成」非「皆成」——2026-10-03 像素级直读修正。"
            "「凡二歲」=两年，与于慎行碑「至六年仲秋既望落成」自洽。"
        ),
    ),
    TextualFact(
        id="tf_cs97_tower",
        division_id="div_rxjwkc97_cishousi",
        verbatim_quote="入門門即有窣堵波高入雲表名永安塔",
        attested_string="窣堵波……名永安塔",
        source_year=_dt(1783, "dt_rxjwkc97_comp", precision="decade"),
        translator_note=(
            "「窣堵波」＝梵语 stupa，砖塔通称；2026-10-03 像素级直读修正"
            "（初曾目视转写作「空塔波」，讹字）。塔名「永安塔」以此为最硬出处。"
        ),
    ),
    TextualFact(
        id="tf_cs97_funding",
        division_id="div_rxjwkc97_cishousi",
        verbatim_quote="慈聖既捐帑各邸復助之因得速就如此",
        attested_string="慈聖既捐帑各邸復助之",
        source_year=_dt(1783, "dt_rxjwkc97_comp", precision="decade"),
        translator_note=(
            "集资非独资的官书层书证。「各邸」＝诸王府邸，2026-10-03 修正"
            "（初目视作「各郎」）。「速就」非「速竣」，同批修正。"
        ),
    ),
    # —— 卷 97 续：双碑像主（唯一一手直读）——
    TextualFact(
        id="tf_cs97_beipai",
        division_id="div_rxjwkc97_cishousi",
        verbatim_quote="本朝乾隆二十二年奉敕修葺塔下碑亭二座碑前刻紫竹觀音像",
        attested_string="奉敕修葺塔下碑亭二座",
        source_year=_dt(1783, "dt_rxjwkc97_comp", precision="decade"),
        translator_note="1757 修葺是官书明载的唯一清代整修节点，**规模无载，禁写「大修/重建」**。",
    ),
    TextualFact(
        id="tf_cs97_tableleft",
        division_id="div_rxjwkc97_cishousi",
        verbatim_quote="左碑前刻紫竹觀音像",
        attested_string="左碑……紫竹觀音像",
        source_year=_dt(1783, "dt_rxjwkc97_comp", precision="decade"),
        translator_note=(
            "**左碑像主＝紫竹观音**（卷 97 官书直读）。2026-10-03 像素级直读，"
            "曾误记为「右碑紫竹」，左右颠倒已修正。"
        ),
    ),
    TextualFact(
        id="tf_cs97_tableright",
        division_id="div_rxjwkc97_cishousi",
        verbatim_quote="右碑前刻魚籧觀音像贊同左",
        attested_string="右碑……魚籧觀音像",
        source_year=_dt(1783, "dt_rxjwkc97_comp", precision="decade"),
        translator_note=(
            "**右碑像主＝鱼篮观音**。「贊同左」是「其赞体例与左碑相同」，"
            "不是「赞的作者在左碑」。黄辉撰的是背面「後刻闗聖像并贊」。"
        ),
    ),
    TextualFact(
        id="tf_cs97_1783",
        division_id="div_rxjwkc97_cishousi",
        verbatim_quote="香雲閣東偏有九蓮像一尊高尺餘",
        attested_string="九蓮像一尊高尺餘",
        source_year=_dt(1783, "dt_rxjwkc97_comp", precision="decade"),
        translator_note=(
            "1783 年九莲像在**寺内香云阁东偏**供奉——这是**寺内供奉像**，"
            "与碑刻像主（紫竹／鱼篮）无关。闸门要求用此句杜绝「碑上刻九莲」的误读。"
        ),
    ),
    # —— 帝京景物略：建寺缘起与九莲梦（原典出处）——
    TextualFact(
        id="tf_djwl5_motive",
        division_id="div_djwl5_cishousi",
        verbatim_quote="慈聖皇太后為禱子",
        attested_string="為禱子",
        source_year=_dt(1635, "dt_djwl5_comp"),
    ),
    TextualFact(
        id="tf_djwl5_site",
        division_id="div_djwl5_cishousi",
        verbatim_quote="宗祈胤嗣卜地阜成門外八里建寺有永安壽塔塔十三級",
        attested_string="阜成門外八里建寺……塔十三級",
        source_year=_dt(1635, "dt_djwl5_comp"),
        translator_note=(
            "2026-10-03 像素级直读修正。KB 原引文「慈寿寺在阜成门外八里庄，"
            "神宗生母李太后建，浮屠十三级，巍峨插天，京师地标也」**在卷五影印本中不存在**，"
            "系后人概括回填的伪引文，已撤。塔十三级由本条直证。"
        ),
    ),
    TextualFact(
        id="tf_djwl5_lotus",
        division_id="div_djwl5_cishousi",
        verbatim_quote="七寶冠帔坐一金鳳九首",
        attested_string="七寶冠帔坐一金鳳九首",
        source_year=_dt(1635, "dt_djwl5_comp"),
        translator_note="九莲菩萨像「跨凤九首」的晚明文本层记载——**文献记载/官书目验，不是考古硬证据**（闸门 C03）。",
    ),
    TextualFact(
        id="tf_djwl5_merit",
        division_id="div_djwl5_cishousi",
        verbatim_quote="授太后經曰九蓮經",
        attested_string="九蓮經",
        source_year=_dt(1635, "dt_djwl5_comp"),
    ),
    TextualFact(
        id="tf_djwl5_monk_says",
        division_id="div_djwl5_cishousi",
        verbatim_quote="寺有僧自言夢或告曰太后菩薩後身也",
        attested_string="寺有僧自言夢……菩薩後身也",
        source_year=_dt(1635, "dt_djwl5_comp"),
        translator_note=(
            "**「寺有僧自言」五字前缀完整可读**——这是闸门 C03 要求的降级措辞的"
            "原著出处。口播必须带「寺有僧自言」/「寺僧相传」，绝不可升格为史实。"
        ),
    ),
    # —— 天咫偶闻：寺毁唯一硬锚 ——
    TextualFact(
        id="tf_tzoyw9_destroyed",
        division_id="div_tzoyw9_cishousi",
        verbatim_quote="今寺毀盡惟浮圖及碑存",
        attested_string="寺毀盡惟浮圖及碑存",
        source_year=_dt(1908, "dt_tzoyw9_comp", precision="decade"),
        translator_note=(
            "**寺毁遗存的唯一一手锚**。注意「惟浮图**及碑**存」是复数——"
            "遗存是塔＋碑，不是「只剩塔」（闸门 C02）。「毁于清末大火」无一手记载，"
            "火情细节不得入画入口播。"
        ),
    ),
    TextualFact(
        id="tf_tzoyw9_thirteen",
        division_id="div_tzoyw9_cishousi",
        verbatim_quote="浮圖十三級與天寧寺相同",
        attested_string="浮圖十三級與天寧寺相同",
        source_year=_dt(1908, "dt_tzoyw9_comp", precision="decade"),
    ),
    # —— 张居正碑（传世文本，1783 已无存）——
    TextualFact(
        id="tf_zwzjj_motive",
        division_id="div_zwzjj_beizhi",
        verbatim_quote="為穆考薦福今上祈儲",
        attested_string="為穆考薦福今上祈儲",
        source_year=_dt(1584, "dt_zwzjj_comp", precision="decade"),
        translator_note=(
            "**建寺缘起的碑文级表述**：荐福（穆宗）+ 祈储（神宗）。"
            "此句证明建寺动机**与九莲梦无涉**——梦属造像层（闸门 C03 分层要求）。"
            "原碑 1783 已无存，此处为《明张文忠公全集》传世文本，禁写「碑现存/拓片」。"
        ),
    ),
    TextualFact(
        id="tf_zwzjj_started",
        division_id="div_zwzjj_beizhi",
        verbatim_quote="時以萬厯丙子春二月始事",
        attested_string="萬厯丙子春二月始事",
        source_year=_dt(1584, "dt_zwzjj_comp", precision="decade"),
        translator_note="**1576 是始事年，不是落成年**。禁「万历四年建成」。",
    ),
    TextualFact(
        id="tf_zwzjj_funding",
        division_id="div_zwzjj_beizhi",
        verbatim_quote="出宮中供奉金若干兩潞王公主暨諸宮眷助佐若干金",
        attested_string="出宮中供奉金……潞王公主暨諸宮眷助佐",
        source_year=_dt(1584, "dt_zwzjj_comp", precision="decade"),
        translator_note="集资非独资的碑文层书证（与卷 97「捐帑各邸復助」同向）。",
    ),
    # —— 野获编转引明碑（讹文所在，正片不采）——
    TextualFact(
        id="tf_yhls_erroneous",
        division_id="div_yhls_cishousi",
        verbatim_quote="〔萬曆〕丙子造大䕶國慈夀寺寳塔工竣入院焚修",
        attested_string="寶塔工竣",
        source_year=_dt(1610, "dt_yhls_comp", precision="decade"),
        translator_note=(
            "🔴 **讹文映射档，禁进口播**。传抄本作「隆慶丙子」，但隆庆朝（1567-1572）"
            "无丙子年，讹。校作万历丙子（1576）虽最合理，**仍属校勘判断而非原碑直读**——"
            "「发现错误 ≠ 已证明唯一正确改法」。此句若被读作「塔 1576 已竣」，即触闸门 C01。"
        ),
    ),
]


# ==================================================================
# 空间实体（寺与塔分立）
# ==================================================================

ENTITIES: List[PersistentSpatialEntity] = [
    PersistentSpatialEntity(id="ent_cishousi", kind=PhysicalThingKind.RELIGIOUS_PRECINCT,
                            canonical_label="慈寿寺（阜成门外八里庄，万历四年始事六年落成，光绪间毁）"),
    PersistentSpatialEntity(id="ent_cishousi_ta", kind=PhysicalThingKind.HUMAN_MADE_ARTIFACT,
                            canonical_label="永安万寿塔（慈寿寺塔，八角十三级密檐实心砖塔，近50米）"),
    PersistentSpatialEntity(id="ent_linglong_gongyuan", kind=PhysicalThingKind.GARDEN_COMPLEX,
                            canonical_label="玲珑公园（1990年以慈寿寺塔为中心建成）"),
]


# ==================================================================
# 历史状态链
# ==================================================================

STATES: List[HistoricalFeatureState] = [
    HistoricalFeatureState(
        id="st_cs_pre1576", entity_id="ent_cishousi", label="寺前状态：谷大用故地",
        time_span=_ts(1505, 1576, "ts_cs_pre"),
        geometry="阜成门外八里庄，太监谷大用故地；邻侧另有摩诃庵（费寀碑记地三十亩、园圃二顷五十余亩）",
        function="寺前状态：尚未营建",
        evidence_fact_ids=["tf_cs97_completion"],
    ),
    HistoricalFeatureState(
        id="st_cs_building", entity_id="ent_cishousi", label="万历四年至六年营建中",
        time_span=_ts(1576, 1578, "ts_cs_build"),
        geometry="万历四年二月始事，冯保卜地、杨辉董役",
        function="营建中的皇家寺院；资金为捐帑＋潞王公主宫眷内侍捐助（集资非独资）",
        evidence_fact_ids=["tf_zwzjj_started", "tf_zwzjj_funding", "tf_cs97_funding"],
    ),
    HistoricalFeatureState(
        id="st_cs_1578", entity_id="ent_cishousi", label="万历六年仲秋既望整体落成",
        time_span=_ts(1578, 1757, "ts_cs_1578"),
        geometry="外山门/天王殿/钟鼓楼/永安寿塔/中延寿殿/后宁安阁/伽蓝祖师大士地藏四殿/画廊百楹/禅堂方丈三所；赐园一区、庄田三十顷",
        function="盛期皇家寺院，寺内奉九莲菩萨像；**塔与寺同期兴建**",
        evidence_fact_ids=["tf_cs97_completion", "tf_zwzjj_started"],
    ),
    HistoricalFeatureState(
        id="st_cs_1757", entity_id="ent_cishousi", label="乾隆二十二年奉敕修葺",
        time_span=_ts(1757, 1783, "ts_cs_1757"),
        geometry="塔下碑亭二座；御书额「栴檀寳地」「香云」，阁联「智珠朗暎光明藏，意蘂常舒歡喜園」",
        function="乾隆二十二年奉敕修葺（**规模无载，禁写「大修/重建」**）",
        evidence_fact_ids=["tf_cs97_beipai"],
    ),
    HistoricalFeatureState(
        id="st_cs_1783", entity_id="ent_cishousi", label="卷97纂竣时：碑一亡、双碑在、九莲像在",
        time_span=_ts(1783, 1783, "ts_cs_1783"),
        geometry="张居正所撰碑已无存；塔下双碑仍在（左紫竹观音／右鱼篮观音）；香云阁东偏九莲像一尊高尺余",
        function="卷97纂竣时的寺塔状态（**碑一亡≠双碑皆亡**）",
        evidence_fact_ids=["tf_cs97_1783", "tf_cs97_beipai", "tf_cs97_tableleft", "tf_cs97_tableright"],
    ),
    HistoricalFeatureState(
        id="st_cs_guangxu", entity_id="ent_cishousi", label="光绪间：寺毁尽，惟塔及碑存",
        time_span=_ts(1880, 1900, "ts_cs_gx"),
        geometry="「今寺毀盡，惟浮圖及碑存」（天咫偶闻）——**「及碑」是复数，遗存是塔＋碑不是只剩塔**",
        function="寺毁，仅余塔与两通明碑；**毁因无档案，火事禁写**",
        evidence_fact_ids=["tf_tzoyw9_destroyed"],
    ),
    HistoricalFeatureState(
        id="st_ta_1578", entity_id="ent_cishousi_ta", label="塔与寺同期兴建",
        time_span=_ts(1576, 1578, "ts_ta_build"),
        geometry="八角十三级密檐实心砖塔，「窣堵波高入雲表」；名永安塔/永安寿塔",
        function="与寺同期兴建（**1576 年内是否竣工＝校勘推定，见 prop_tower_completion_1576**）",
        evidence_fact_ids=["tf_cs97_tower", "tf_djwl5_site", "tf_tzoyw9_thirteen"],
    ),
    HistoricalFeatureState(
        id="st_ta_now", entity_id="ent_cishousi_ta", label="现状：国保·公园内孤塔",
        time_span=_ts(1957, 2026, "ts_ta_now"),
        geometry="塔高「近50米」（文物部门口径，**禁伪精确如 50.36 米**）；1957 首批北京市文保、1987 划定保护范围、2013 第七批国保（编号711／7-0711-3-009）；今在玲珑公园内",
        function="全国重点文物保护单位「慈寿寺塔」，玲珑公园的核心遗存",
        evidence_fact_ids=["tf_cs97_tower"],
    ),
]


# ==================================================================
# 地名指称（塔名系统四源同物）
# ==================================================================

APPELLATIONS: List[Appellation] = [
    Appellation(id="app_si_cishousi", label="慈寿寺", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1578, 2026, "ts_ap1"),
                attesting_fact_ids=["tf_cs97_location", "tf_djwl5_site"]),
    Appellation(id="app_ta_yongan", label="永安塔", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1578, 2026, "ts_ap2"),
                attesting_fact_ids=["tf_cs97_tower"]),
    Appellation(id="app_ta_yongan2", label="永安寿塔", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1578, 2026, "ts_ap3"),
                attesting_fact_ids=["tf_djwl5_site"]),
    Appellation(id="app_ta_shang", label="永安万寿塔", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1578, 2026, "ts_ap4"),
                attesting_fact_ids=["tf_cs97_tower"]),
    # 玲珑宝塔：明代即有此称**尚缺一手佐证**。
    # KB 原引《燕都游览志》「雕饰玲珑秀出，京师游人呼为玲珑宝塔」并标 VERIFIED，
    # 但卷97按语引该书只记「宝藏阁系圣母御笔题…今頺楹殘礎」，已降 CONTESTED（见 prop_linglong_early_name）。
    # 《玲珑塔》唱段与本塔无可证实的传播关系——**不作成播因果**（闸门 C08）。
    Appellation(id="app_ta_linglong", label="玲珑塔", kind=AppellationKind.VULGAR,
                valid_time_span=_ts(1900, 2026, "ts_ap5"),
                attesting_fact_ids=["tf_tzoyw9_destroyed"]),
    Appellation(id="app_si_ningan", label="宁安阁", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1578, 1757, "ts_ap6"),
                attesting_fact_ids=["tf_cs97_1783"]),
    # 宝藏阁：御笔归属**阙疑**（燕都游览志记宝藏阁为圣母御笔，帝京景物略记宁安阁为慈圣手书，
    # 乾隆官书裁定「記載互異……姑並存之以闕疑」）。口播只能说「相传为太后手书」。
    Appellation(id="app_si_baocang", label="宝藏阁", kind=AppellationKind.OLD_NAME,
                valid_time_span=_ts(1578, 1757, "ts_ap7"),
                attesting_fact_ids=["tf_cs97_1783"]),
    Appellation(id="app_linglong_gongyuan", label="玲珑公园", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1990, 2026, "ts_ap9"),
                attesting_fact_ids=["tf_tzoyw9_destroyed"]),
    # 讹文映射档：野获编传抄作「隆慶丙子」，隆庆朝（1567-1572）无丙子年，讹。
    # 校作万历丙子虽最合理但**仍属校勘判断**——「发现错误 ≠ 已证明唯一正确改法」。
    # 严禁进口播（见 tf_yhls_erroneous 与 prop_tower_completion_1576）。
    Appellation(id="app_err_longqing", label="隆慶丙子（讹文）", kind=AppellationKind.TEXTUAL_CORRUPTION,
                valid_time_span=_ts(1610, 1610, "ts_ap8"),
                attesting_fact_ids=["tf_yhls_erroneous"]),
]


# ==================================================================
# 命题层（含 C01 校勘推定）
# ==================================================================

PROPOSITIONS: List[Proposition] = [
    # —— C01：塔 1576 竣工＝校勘推定，**不升 VERIFIED** ——
    Proposition(
        id="prop_tower_completion_1576",
        statement="永安万寿塔在万历四年（1576）内已竣工（早于寺整体落成）。",
        derived_from_fact_ids=["tf_yhls_erroneous", "tf_cs97_completion", "tf_zwzjj_started"],
        inferred_subject_id="ent_cishousi_ta",
        inference_method=(
            "inferred_emendation（校勘推定）：卷100 传抄作「隆慶丙子……寶塔工竣」，"
            "隆庆朝无丙子年，讹；校作万历丙子（1576）虽最合理，**但「发现错误 ≠ "
            "已证明唯一正确改法」**。憨山《古风淳公塔铭》只言万历丙子「敕建大慈壽寺成」，"
            "未言塔竣。更关键：野获编「故地經始于萬曆四年凡二歲告成」一句的宾语是"
            "**「故地」即寺基址**，塔未被列为落成宾语；用同页按语「臣等謹按慈壽寺及塔」"
            "回溯改写引文宾语属**跨层取证（按语层→引文层）**，为 E9 纪禁止的证据混级。"
        ),
        alternative_explanations=[
            "塔确在 1576 年内先行竣工（讹文校作万历丙子的读法）",
            "塔 1576 已成部分工程，1578 仲秋与寺同时告成（卷97「凡二歲告成」的自然读法）",
            "塔工竣年与寺落成年本不相同，讹文原文所指非塔",
        ],
    ),
    Proposition(
        id="prop_jiu_lian_motive",
        statement="太后梦见九莲菩萨是慈寿寺的建寺动机。",
        derived_from_fact_ids=["tf_zwzjj_motive", "tf_djwl5_monk_says", "tf_djwl5_merit"],
        inferred_subject_id="ent_cishousi",
        inference_method=(
            "证据分层判定：碑文级建寺动机表述为「為穆考薦福今上祈儲」（荐福＋祈储），"
            "**与九莲梦无涉**。九莲叙事属**造像层/信仰层**（梦菩萨数现授《九莲经》→"
            "範金祀之于后殿）。「太后是菩萨后身」更内嵌一层口述：原典明写「寺有僧自言夢」。"
        ),
        alternative_explanations=[
            "梦是建寺动机的触发（民间流传层说法，但无碑文级支撑）",
            "梦与建寺并行不悖，各自独立发生（分层说，本集采信）",
        ],
    ),
    Proposition(
        id="prop_sole_funding",
        statement="慈寿寺由李太后独资营建。",
        derived_from_fact_ids=["tf_cs97_funding", "tf_zwzjj_funding"],
        inferred_subject_id="ent_cishousi",
        inference_method=(
            "两源同向否证：卷97「慈聖既捐帑各邸復助之」＋张居正碑「出宮中供奉金……"
            "潞王公主暨諸宮眷助佐若干金」。李太后是倡建者与主要出资者之一，非唯一出资者。"
        ),
        alternative_explanations=[
            "（本集无支持「独资」的一手证据）",
        ],
    ),
    Proposition(
        id="prop_cishousi_fire_drama",
        statement="慈寿寺毁于清末大火。",
        derived_from_fact_ids=["tf_tzoyw9_destroyed"],
        inferred_subject_id="ent_cishousi",
        inference_method=(
            "**无据推论**。天咫偶闻只记「今寺毀盡，惟浮圖及碑存」，未记毁因；"
            "《宸垣识略》《光绪顺天府志》同样只记寺毁不记火。「火灾」是现代通行说法"
            "（文旅页/维基），无一手依据。"
        ),
        alternative_explanations=[
            "光绪间某次火灾（无档案）",
            "年久失修渐圮（无过程档案）",
            "战乱/改用途（无档案）",
        ],
    ),
    Proposition(
        id="prop_linglong_early_name",
        statement="「玲珑宝塔」是明代天启年间已流传的称呼。",
        derived_from_fact_ids=[],
        inferred_subject_id="ent_cishousi_ta",
        inference_method=(
            "KB 原引《燕都游览志卷三》「八里庄有慈寿寺舍利宝塔，雕饰玲珑秀出，京师游人呼为"
            "玲珑宝塔」并标 VERIFIED，但卷97按语引该书**只记「宝藏阁系圣母御笔题……"
            "今頺楹殘礎」**，无玲珑塔记述。2026-10-03 降为 CONTESTED。"
        ),
        alternative_explanations=[
            "明代已有此称，只是所据非燕都游览志",
            "明代无此称，「玲珑塔」系清代以后形成（当前采信）",
        ],
    ),
]

ADOPTIONS: List[BeliefAdoption] = [
    # C01：采信「塔与寺同期兴建」，不采信「1576 塔已竣」
    BeliefAdoption(
        proposition_id="prop_tower_completion_1576",
        status=EpistemicStatus.CONTESTED,
        confidence=0.30,
        adopted_by="E19 闸门（cishousi_video/gpt_review.txt C01）",
        adopted_at=_dt(2026, "dt_e19_gate"),
        rationale=(
            "维持降级为 inferred_emendation。理由：(1) 野获编「凡二歲告成」宾语是「故地」"
            "（寺基址），塔未被列为落成宾语；(2) 用同页按语回溯改写引文宾语是跨层取证，"
            "为 E9 纪禁止；(3)「凡二歲」=两年，与于慎行碑「經始于萬厯四年二月，至六年"
            "仲秋既望落成」天然自洽，读成 1576 即成需额外假设，而该假设恰来自卷100 讹文。"
            "**1578 整体落成不受影响。** 正片不提塔的单独竣工年。"
        ),
        refuting_fact_ids=["tf_cs97_completion"],
    ),
    BeliefAdoption(
        proposition_id="prop_jiu_lian_motive",
        status=EpistemicStatus.DISPROVEN,
        confidence=0.9,
        adopted_by="E19 闸门 C03",
        adopted_at=_dt(2026, "dt_e19_gate_c03"),
        rationale=(
            "碑文级建寺动机明写「為穆考薦福今上祈儲」，与九莲梦无涉。九莲叙事属造像层；"
            "「太后后身」原典自带「寺有僧自言」口述前缀，属寺僧相传，不得升格。"
        ),
        refuting_fact_ids=["tf_zwzjj_motive"],
    ),
    BeliefAdoption(
        proposition_id="prop_sole_funding",
        status=EpistemicStatus.DISPROVEN,
        confidence=0.95,
        adopted_by="E19 负控制 2（与 E15 同款红线）",
        adopted_at=_dt(2026, "dt_e19_gate_nc2"),
        rationale="卷97 与张居正碑两源同向明载有王府公主宫眷捐助，非独资。",
        refuting_fact_ids=["tf_cs97_funding", "tf_zwzjj_funding"],
    ),
    BeliefAdoption(
        proposition_id="prop_cishousi_fire_drama",
        status=EpistemicStatus.UNSUBSTANTIATED,
        confidence=0.1,
        adopted_by="E19 负控制（寺毁过程不虚构）",
        adopted_at=_dt(2026, "dt_e19_gate_nc"),
        rationale="三份清代文献（宸垣识略/光绪顺天府志/天咫偶闻）均只记寺毁不记毁因。",
        refuting_fact_ids=["tf_tzoyw9_destroyed"],
    ),
    BeliefAdoption(
        proposition_id="prop_linglong_early_name",
        status=EpistemicStatus.CONTESTED,
        confidence=0.25,
        adopted_by="E19 研究层像素级复核（2026-10-03）",
        adopted_at=_dt(2026, "dt_e19_recheck"),
        rationale=(
            "KB 原引《燕都游览志》该句与卷97按语所引内容不符，降 CONTESTED。"
            "口播可作「民间称玲珑塔」但**不得作成播因果**，"
            "《玲珑塔》唱段与本塔无可证实传播关系（闸门 C08）。"
        ),
    ),
]


# ==================================================================
# 空间变换
# ==================================================================

TRANSFORMATIONS: List[PlaceTransformation] = [
    PlaceTransformation(
        id="pte_cs_1578_done", entity_id="ent_cishousi",
        transformation=PlaceTransformationEvent.CONSTRUCTED,
        time_span=_ts(1576, 1578, "ts_pte_cs1"),
        resulting_state_id="st_cs_1578",
        resulting_condition="万历四年二月始事，六年仲秋既望整体落成，赐名慈寿",
        evidence_fact_ids=["tf_zwzjj_started", "tf_cs97_completion"],
    ),
    PlaceTransformation(
        id="pte_cs_1757_repair", entity_id="ent_cishousi",
        transformation=PlaceTransformationEvent.REBUILT,
        time_span=_ts(1757, 1757, "ts_pte_cs2"),
        resulting_state_id="st_cs_1757",
        resulting_condition="乾隆二十二年奉敕修葺（**规模无载**）",
        evidence_fact_ids=["tf_cs97_beipai"],
    ),
    PlaceTransformation(
        id="pte_cs_guangxu_destroy", entity_id="ent_cishousi",
        transformation=PlaceTransformationEvent.DEMOLISHED,
        time_span=_ts(1880, 1900, "ts_pte_cs3"),
        resulting_state_id="st_cs_guangxu",
        resulting_condition="寺毁尽，惟浮图及碑存（**毁因无档案**）",
        evidence_fact_ids=["tf_tzoyw9_destroyed"],
    ),
    PlaceTransformation(
        id="pte_lg_1990_park", entity_id="ent_cishousi_ta",
        transformation=PlaceTransformationEvent.REBUILT,
        time_span=_ts(1990, 1990, "ts_pte_lg1"),
        resulting_state_id="st_ta_now",
        resulting_condition="海淀区以塔为中心建成玲珑公园；**面积口径分歧（1990 资料约 7 公顷／现行名录 8.13 公顷），正片不出现面积**（闸门 C10）",
        evidence_fact_ids=["tf_tzoyw9_destroyed"],
    ),
]

AGGREGATES: List[PlaceAggregate] = []


# ==================================================================
# 跨时同一性：寺与塔必须分立（E19 关键判定）
# ==================================================================

IDENTITIES: List[DiachronicIdentityAssertion] = [
    # 🔴 寺与塔必须分立——「寺院建筑亡、塔存」说的是两件事，不得合并成一个实体
    DiachronicIdentityAssertion(
        id="dia_ta_same_cont",
        subject_entity_ids=["ent_cishousi_ta", "ent_cishousi"],
        relation=IdentityRelation.PARTIAL_CONTINUATION,
        time_span=_ts(1880, 2026, "ts_dia1"),
        evidence_fact_ids=["tf_tzoyw9_destroyed", "tf_cs97_tower"],
        status=EpistemicStatus.VERIFIED,
        alternative_relations=[
            IdentityRelation.SUCCESSOR,
        ],
        is_orthogonal_to_state_change=True,
    ),
]


# ==================================================================
# 指称断言：现行口径与古代层分挂，绝不混级
# ==================================================================

REFERENCES: List[ReferentialAssertion] = [
    # 双碑像主冲突：卷97官书直读 vs 现行文物局口径
    ReferentialAssertion(
        id="ref_beipai_xiangzhu",
        appellation_id="app_ta_shang",
        referent_entity_id="ent_cishousi_ta",
        time_span=_ts(1783, 1783, "ts_r1"),
        evidence_fact_ids=["tf_cs97_tableleft", "tf_cs97_1783"],
        status=EpistemicStatus.CONTESTED,
        provenance=(
            "左碑像主：卷97官书直读作「左碑前刻紫竹觀音像」；现行北京市文物局口径称「左刻九蓮菩薩像」。"
            "**本集采卷97官书口径**（有原书影印可逐字直读）。"
            "九莲是寺内香云阁东偏的供奉像（tf_cs97_1783），**不是碑刻像**——"
            "「左刻九莲」易被误读为碑上刻九莲，此处明确切分。"
        ),
    ),
    # 塔高口径
    ReferentialAssertion(
        id="ref_ta_height",
        appellation_id="app_ta_shang",
        referent_entity_id="ent_cishousi_ta",
        time_span=_ts(2013, 2026, "ts_r2"),
        evidence_fact_ids=["tf_tzoyw9_thirteen"],
        status=EpistemicStatus.VERIFIED,
        provenance=(
            "塔高采文物部门现行公开口径「近50米」；「五十多米」（文旅平台另一页）作差异注记。"
            "两口径均无正式测绘档名目，**禁「通高50.36米」类伪精确**。"
        ),
    ),
    # 玲珑公园面积：时态混用，正片已删
    ReferentialAssertion(
        id="ref_park_area",
        appellation_id="app_linglong_gongyuan",
        referent_entity_id="ent_linglong_gongyuan",
        time_span=_ts(1990, 2026, "ts_r3"),
        evidence_fact_ids=["tf_tzoyw9_destroyed"],
        status=EpistemicStatus.CONTESTED,
        provenance=(
            "1990建园资料约7公顷（含水面0.3公顷）；现行北京市园林绿化局名录8.13公顷。"
            "统计口径/边界变化未核。**该数字与主线无叙事收益，正片不出现面积**（闸门 C10）。"
        ),
    ),
    # 地理关系：西岸不是南岸（闸门 C06 硬伤）
    ReferentialAssertion(
        id="ref_geography",
        appellation_id="app_si_cishousi",
        referent_entity_id="ent_cishousi",
        time_span=_ts(1578, 2026, "ts_r4"),
        evidence_fact_ids=["tf_djwl5_site"],
        status=EpistemicStatus.VERIFIED,
        provenance=(
            "塔位在**昆玉河西岸**的长河之滨、八里庄一带（自航天桥向西望）。"
            "海淀区政协与北京市园林绿化局双源一致。**严禁写「南岸」**（闸门 C06 硬伤）。"
        ),
    ),
]
