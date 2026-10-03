"""
haidian_kg/calibration/shaoyuan.py
勺园·淑春园·未名湖词条 —— 海淀历史地名知识库 E20 入库模块

数据唯一来源：《勺园·淑春园》研究档案 v1.1（shaoyuan_video/research.md，2026-10-03）
＋ gpt_review.txt 正式闸门裁决（E01—E12，最终框架＝「两个园址系统＋一个后期合流区」）。

证据分级映射（research.md 五级 → 本体表达，绝不混级）：
  [文献记载]   → TextualFact（古籍逐字引文）+ VERIFIED
  [官书考订]   → TextualFact（卷79 臣等谨按按语层，与原引层分立篇卷）
  [一手档案]   → TextualFact（查抄档/水田档/上谕；本档均经恭博转引，note 标 quoted_via）
  [时人记述]   → TextualFact（昭梿/奕譞/潘德舆；「傳聞」「聞」前缀照录防绝对化）
  [现代研究]   → Proposition + BeliefAdoption（争议双方各记其据，不判死）
  [现代官方口径] → 状态 geometry/function 文本，挂机构名，不升古代层

E20 闸门红线落位（本模块的结构性承诺，tests/haidian_kg/test_shaoyuan_entry.py 守卫）：
  - E01/E02【最重要】：勺园链（勺園→弘雅園→集賢院，西南）与和珅园链（和珅海淀赐园／
    十笏园→1799永瑆→睿王园系统，未名湖一带）分立两个实体系统；「和珅园是否即名淑春园」
    ＝学术争议（何瑜·故宫博物院院刊2021 vs 郝黎·恭王府博物馆2026），
    prop_shuchunyuan_he_shen_identity + BeliefAdoption(CONTESTED)，指称断言 rr_shuchun 亦 CONTESTED。
    链名正名：「和珅海淀赐园链」不再称「淑春园链」。
  - E02：1763 淑春园水田档只证「有一处名为淑春园的官园」；何瑜据「北楼门」判其在圆明园北部；
    「名早于和珅＝硬证」已撤销（prop_shuchun_name_early_evidence DISPROVEN）。
  - E03：1784 赐和珅年份不得作为确证事实入库——prop_grant_year_1784 CONTESTED；
    状态层只用「乾隆后期/乾隆年间」措辞，1784/乾隆四十九年不进事实与状态。
  - E04：查抄房数严格为 1003 间（A10「現查得和珅花園內房一千零三間」），
    严禁「一千零三十/1030」；错值建模为 prop_room_count_1030 DISPROVEN。
  - E05：「樓臺四十二所」（花园一座）与「亭臺六十四所，四角更樓十二座，更夫一百二十名」
    （钦赐花园一座）系不同查抄清单口径，分立两条 TextualFact，严禁加总/拼一个园林总表；
    「亭台64」不得写作「楼台64」。
  - E06：吴彬《勺园祓禊图》自题底本作「已」，校作「已〔乙〕卯」——1615 年干支为乙卯；
    「己」是另一干支绝非异写，全模块严禁出现（负控扫描）。
  - E07/E08/E09：湖名频次须含枫湖居首（枫湖>无名湖>睿湖>未名湖）；
    1931-05-02 是燕大建筑命名投票非湖名投票；「未名湖」1928 已出现、1931 前后渐成公认，
    钱穆是赞成者不是创造者。
  - E10：「康熙赐积哈纳」删除（积哈纳为乾隆朝人物，PKU 官网口径内部矛盾）；弘雅园断代待核。
  - E11：马戛尔尼属勺园—弘雅园链，禁入和珅园链实体；口播须挂「据何瑜考证」归因。
  - E12：建园年份「约1612—1614」必须带「约」（明代当时文本只证「新築」无纪年）。
  - 国保：国务院第五批 5-475「未名湖燕园建筑」（2001-06-25，国发〔2001〕25号）。

引文本地化纪律（§5.1）：全部逐字引文以 research.md 附录A 本地底本为准；
转引一律 quoted_via 并在 translator_note 标明；《长安客话》原书未直核，
引文挂日下旧闻考卷79 转录层（原引层与按语层分立篇卷）。
"""
from typing import List

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
    PlaceTransformationEvent, ReferentialAssertion,
)


# ==================================================================
# 工具
# ==================================================================

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
    # 一律取自统一书目表，一书一条，禁止在此另建
    source_by_title("钦定日下旧闻考"),
    source_by_title("帝京景物略"),
    source_by_title("清仁宗睿皇帝实录"),
    source_by_title("清史稿"),
    source_by_title("啸亭杂录"),
    source_by_title("清代和珅档案史料"),
    source_by_title("庸庵笔记"),
    source_by_title("九思堂诗稿"),
    source_by_title("钦定大清会典事例"),
    source_by_title("探秘和珅时期的花园"),
    source_by_title("北京大学公开校史与校园文物资料"),
    source_by_title("国务院公布全国重点文物保护单位名单"),
]

DIVISIONS: List[SourceDivision] = [
    # 帝京景物略卷五（wikisource 直核，directlyVerified）
    SourceDivision(id="div_djwl5_haidian", source_id="src_dijingjingwulue",
                   volume_number="卷五", section_title="海淀条（勺园段＋叶向高评）"),
    # 卷79 原引层：《长安客话》《燕都游览志》诸条经此转录（原书未直核，quoted_via）
    SourceDivision(id="div_rxjwkc79_shaoyuan", source_id="src_rxjwkc",
                   volume_number="卷79",
                   section_title="郊坰门·海淀勺园诸条原引（长安客话/燕都游览志转录层）"),
    # 卷79 按语层：臣等谨按（官方考订，与原引分立，禁跨层取证）
    SourceDivision(id="div_rxjwkc79_anzhao", source_id="src_rxjwkc",
                   volume_number="卷79", section_title="臣等谨按（勺园方位与存佚考订）"),
    # 清代官书/档案（引文经恭博转引，原件未直核，note 标 quoted_via）
    SourceDivision(id="div_rizhi_vol37", source_id="src_rizhi",
                   volume_number="卷三十七", section_title="嘉庆四年正月和珅罪状上谕"),
    SourceDivision(id="div_qsg_319", source_id="src_qingshigao",
                   volume_number="卷319", section_title="和珅传"),
    SourceDivision(id="div_xiaoting_vol9", source_id="src_xiaoting_zalu",
                   volume_number="卷九", section_title="京师园亭（勺园改集贤院／和相十笏园双锚）"),
    SourceDivision(id="div_hsnd_chaojia", source_id="src_qingdai_heshen_dangshi",
                   volume_number="嘉庆四年",
                   section_title="查抄和珅海淀花园档（含《和珅犯罪全案档》；恭博转引）"),
    SourceDivision(id="div_yongan_vol3", source_id="src_yongan_biji",
                   volume_number="卷三", section_title="查抄和珅住宅花园清单（恭博转引）"),
    SourceDivision(id="div_jiusitang_vol7", source_id="src_jiusitang_shigao",
                   volume_number="卷七",
                   section_title="中秋后二日游舒春園四律（序及《孤屿》注；恭博转引）"),
    SourceDivision(id="div_huidian_shili", source_id="src_huidian_shili",
                   volume_number="卷次待核",
                   section_title="内务府园囿·淑春园水田档与弘雅园赏改档（恭博转引）"),
    # 现代层（机构公开口径，与古代层分挂）
    SourceDivision(id="div_gongbo_heshen", source_id="src_gongbo_research",
                   volume_number="正文",
                   section_title="探秘和珅时期的花园（郝黎，2026-03-24；清档/清人诗文转引层）"),
    SourceDivision(id="div_pku_shiguan_weiminghu", source_id="src_pku_open",
                   volume_number="校史馆",
                   section_title="未名湖名字的由来（新京报2026-01-09转载，目验）"),
    SourceDivision(id="div_pku_lib_scrolls", source_id="src_pku_open",
                   volume_number="图书馆",
                   section_title="勺园两卷题跋与1982条石遗址（经中华读书报2010-10-22转录）"),
    SourceDivision(id="div_pku_fdcb_shifang", source_id="src_pku_open",
                   volume_number="校园文物档案",
                   section_title="石舫与石屏条（fdcb.pku.edu.cn，目验）"),
    SourceDivision(id="div_guobao5_ymh", source_id="src_guobao_5th",
                   volume_number="第五批", section_title="未名湖燕园建筑条（国发〔2001〕25号）"),
]


# ==================================================================
# 文本事实层（逐字引文；繁体照录附录A；讹校以〔〕标出）
# ==================================================================

FACTS: List[TextualFact] = [
    # —— 勺园（明）：当时文本 ——
    TextualFact(
        id="tf_djwl_baimu",
        division_id="div_djwl5_haidian",
        verbatim_quote="米太僕勺園,百畝耳,望之等深,步焉則等遠",
        attested_string="勺園……百畝耳",
        source_year=_dt(1635, "dt_djwl5_comp"),
        translator_note=(
            "「百亩」是勺园规模的唯一当时文本量级（清华园十里对读）；"
            "上屏须挂原典。E8 红线合撰（刘侗/于奕正）。"
        ),
    ),
    TextualFact(
        id="tf_djwl_yexianggao",
        division_id="div_djwl5_haidian",
        verbatim_quote="李園壯麗,米園曲折。米園不俗,李園不酸",
        attested_string="李園壯麗,米園曲折",
        source_year=_dt(1635, "dt_djwl5_comp"),
        translator_note=(
            "叶向高过海淀语，P2 四句分四行上屏（wikisource 直核）。"
            "与 E14 清华园构成「京国两名园」对读。"
        ),
    ),
    TextualFact(
        id="tf_cck_xinzhu",
        division_id="div_rxjwkc79_shaoyuan",
        verbatim_quote="水曹郎米萬鍾仲詔新築也,曰勺園,又曰風煙里",
        attested_string="新築也,曰勺園,又曰風煙里",
        source_year=_dt(1783, "dt_rxjwkc79_comp", precision="decade"),
        translator_note=(
            "quoted_via＝日下旧闻考卷79（原书《长安客话》未直核，转引层）。"
            "E12：明代当时文本只证「新築」无纪年——建园年份必须带「约」"
            "（约1612—1614 为现代口径），不得与 1615 题跋同等级。"
        ),
    ),
    TextualFact(
        id="tf_cck_mijiayuan",
        division_id="div_rxjwkc79_shaoyuan",
        verbatim_quote="都人稱曰米家園",
        attested_string="米家園",
        source_year=_dt(1783, "dt_rxjwkc79_comp", precision="decade"),
        translator_note="quoted_via＝卷79；都人称谓层。",
    ),
    TextualFact(
        id="tf_cck_mijiadeng",
        division_id="div_rxjwkc79_shaoyuan",
        verbatim_quote="因繪園中景為燈,邱壑亭臺纖悉具備,都人又稱米家燈",
        attested_string="米家燈",
        source_year=_dt(1783, "dt_rxjwkc79_comp", precision="decade"),
        translator_note=(
            "quoted_via＝卷79。米家灯＝园景自绘为灯；吕邦耀即席诗"
            "「米家燈是米家園」同条可证两名互文。"
        ),
    ),
    TextualFact(
        id="tf_cck_naming",
        division_id="div_rxjwkc79_shaoyuan",
        verbatim_quote="淀之水濫觴一勺,都人米仲詔濬之,築為勺園",
        attested_string="淀之水濫觴一勺",
        source_year=_dt(1783, "dt_rxjwkc79_comp", precision="decade"),
        translator_note=(
            "《长安客话》清华园条（卷79 补），quoted_via。A5 校记：转录页此下"
            "「米顔之曰清華」五字句读存疑——上屏只用本句。"
        ),
    ),
    # —— 卷79 按语层（官方考订，与原引分立） ——
    TextualFact(
        id="tf_rxjwkc79_east",
        division_id="div_rxjwkc79_anzhao",
        verbatim_quote="是勺園應在清華園之東",
        attested_string="勺園應在清華園之東",
        source_year=_dt(1783, "dt_rxjwkc79_anzhao"),
        translator_note="按语层方位考订（带「應在」测语，非实测边界）。",
    ),
    TextualFact(
        id="tf_rxjwkc79_bukao",
        division_id="div_rxjwkc79_anzhao",
        verbatim_quote="今其園不可攷,海淀之東有米家墳在焉",
        attested_string="今其園不可攷",
        source_year=_dt(1783, "dt_rxjwkc79_anzhao"),
        translator_note=(
            "乾隆朝官书自认勺园故址已不可考——勺园存佚的最硬断代锚，"
            "也是「勺园故址边界只到方位级」的冻结依据（四-6）。"
            "归因（明末战乱）无任何文据（负控制7，见 prop_sy_destruction_cause）。"
        ),
    ),
    # —— 弘雅园→集贤院（勺园链） ——
    TextualFact(
        id="tf_hongya_1801",
        division_id="div_huidian_shili",
        verbatim_quote="賞滿漢文職堂官弘雅園一區,為圓明園值日公所",
        attested_string="弘雅園一區,為圓明園值日公所",
        source_year=_dt(1899, "dt_huidian_comp", precision="decade"),
        translator_note=(
            "嘉庆六年辛酉（1801），quoted_via＝恭博引《钦定大清会典事例》/实录系统"
            "（卷次待核，原件未直核）——即集贤院之设。"
            "「弘雅园」三字待清代原典直核（待核2）；E10 已把「弘雅园存在」与"
            "「康熙赐积哈纳」拆分，后句删除（见 prop_kangxi_jihana）。"
        ),
    ),
    TextualFact(
        id="tf_xiaoting_jixianyuan",
        division_id="div_xiaoting_vol9",
        verbatim_quote="今改集賢院,為六曹卿貳寓直之所",
        attested_string="今改集賢院",
        source_year=_dt(1838, "dt_xiaoting_comp", precision="decade"),
        translator_note=(
            "昭梿时人硬锚（闸门待核9关闭：卷九直核）。与「和相十笏園……近為成邸所居」"
            "分写两处——勺园链与和珅园链不同园的关键时人书证（E01 强化）。"
        ),
    ),
    TextualFact(
        id="tf_xiaoting_shihu",
        division_id="div_xiaoting_vol9",
        verbatim_quote="以和相十笏園為最,近為成邸所居",
        attested_string="和相十笏園",
        source_year=_dt(1838, "dt_xiaoting_comp", precision="decade"),
        translator_note=(
            "昭梿亲历嘉庆事的时人记述；「成邸」＝成亲王永瑆。"
            "十笏园为和珅海淀赐园的时人口径（园名与「淑春园」关系另有争议，E01）。"
        ),
    ),
    # —— 和珅园链：档案与谕旨（均经恭博转引） ——
    TextualFact(
        id="tf_shuchun_shuitian_1763",
        division_id="div_huidian_shili",
        verbatim_quote="圓明園所交淑春園並北樓門外等處水田一頃二十三畝六分三厘,歲徵租銀三十九兩一錢九分五厘有奇",
        attested_string="淑春園",
        source_year=_dt(1899, "dt_huidian_comp", precision="decade"),
        translator_note=(
            "乾隆二十八年癸未（1763，与 E15 同干支互证）；quoted_via＝恭博。"
            "🔴 E02：只证 1763 有一处以水田交租、名为淑春园的官园；"
            "何瑜据「北楼门」位置判其在圆明园北部而非今北大——"
            "「淑春园名早于和珅」不得作为园属今北大的硬证（见 prop_shuchun_name_early_evidence）。"
        ),
    ),
    TextualFact(
        id="tf_yixuan_xu",
        division_id="div_jiusitang_vol7",
        verbatim_quote="是園乾隆年間屬和相珅,籍沒後入官。傳聞:禁園工作,每取材于茲,足譚亭臺之侈之鉅。後輾轉為睿邸園寓,雖棟宇僅存,山水之秀美固自若也",
        attested_string="是園乾隆年間屬和相珅",
        source_year=_dt(1865, "dt_jiusitang_v7", precision="decade"),
        translator_note=(
            "奕譞《中秋后二日游舒春園四律》序（恭博转引《故宫珍本丛刊》584册p145）。"
            "「傳聞」二字照录——传闻层自注，防绝对化。仅言「乾隆年間屬和相珅」，"
            "无受赐年份（E03 的时人层上限）。诗题作「舒春園」：淑/舒异写，"
            "为郝黎一方的清人材料（E01 争议另一方）。同卷咏及《石舫》《孤屿》——"
            "石舫清中后期尚存的咏物证据。"
        ),
    ),
    TextualFact(
        id="tf_yixuan_guyu",
        division_id="div_jiusitang_vol7",
        verbatim_quote="聞是嶼樓閣肖禁園蓬島瑤臺制度,逮問後列入大罪之一",
        attested_string="聞是嶼樓閣肖禁園蓬島瑤臺制度",
        source_year=_dt(1865, "dt_jiusitang_v7", precision="decade"),
        translator_note=(
            "《孤屿》诗原注。「聞」前缀完整可读——传闻层自注。"
            "与二十罪第十三条互为独立层：罪状原文无石舫/孤屿字样（见 tf_zui13）。"
        ),
    ),
    TextualFact(
        id="tf_zui13",
        division_id="div_rizhi_vol37",
        verbatim_quote="昨將和珅家產查抄,所蓋楠木房屋,僭侈逾制,其多寶閣及隔段式樣,皆倣照寧壽宮制度;其園寓點綴,竟與圓明園蓬島瑤臺無異,不知是何居心。其大罪十三。",
        attested_string="僭侈逾制……蓬島瑤臺無異",
        source_year=_dt(1799, "dt_rizhi_v37"),
        translator_note=(
            "嘉庆四年正月二十大罪第十三条；quoted_via＝恭博转引《仁宗实录》卷37"
            "（未直核原件）。🔴 原文无「石舫」二字——「僭侈逾制→石舫」是现代文章引申"
            "（负控制2，见 prop_shifang_weizhi_zuizheng）。引文上屏繁体照录，禁插「石舫」。"
        ),
    ),
    TextualFact(
        id="tf_yongansi_garden1",
        division_id="div_yongan_vol3",
        verbatim_quote="花園一座,樓臺四十二所",
        attested_string="樓臺四十二所",
        source_year=_dt(1890, "dt_yongan_comp", precision="decade"),
        translator_note=(
            "《庸庵笔记》卷三查抄清单（恭博转引，原书未直核）。"
            "🔴 E05：与「欽賜花園一座亭臺六十四所」系不同查抄材料的两个花园口径，"
            "严禁与他档房数拼作一个园林总表或加总。"
        ),
    ),
    TextualFact(
        id="tf_yongansi_garden2",
        division_id="div_yongan_vol3",
        verbatim_quote="欽賜花園一座,亭臺六十四所,四角更樓十二座,更夫一百二十名",
        attested_string="亭臺六十四所",
        source_year=_dt(1890, "dt_yongan_comp", precision="decade"),
        translator_note=(
            "🔴 E05 裁决：原文作「亭臺六十四所」——不得写成「楼台64」；"
            "两个花园两条口径，分列不拼总。"
        ),
    ),
    TextualFact(
        id="tf_hsnd_fang1003",
        division_id="div_hsnd_chaojia",
        verbatim_quote="現查得和珅花園內房一千零三間,遊廊樓亭共房三百五十七間",
        attested_string="房一千零三間",
        source_year=_dt(1799, "dt_hsnd_chaojia"),
        translator_note=(
            "海淀花园查抄档；quoted_via＝恭博转引一史馆《和珅犯罪全案档》"
            "（影印《和珅秘档》第九册，未直核原件）。"
            "🔴 E04 红线：房数＝1003 间（一千零三）；任何添位讹读值全模块禁现"
            "（负控扫描守卫，错值只以 DISPROVEN 命题定性存档）；"
            "与庸庵笔记两条花园清单系不同查抄材料，分列不拼总（E05）。"
        ),
    ),
    TextualFact(
        id="tf_yongli_grant",
        division_id="div_rizhi_vol37",
        verbatim_quote="和珅之宅,已賞給慶郡王永璘居住;和珅之園,已賞給成親王永瑆居住",
        attested_string="和珅之園,已賞給成親王永瑆居住",
        source_year=_dt(1799, "dt_rizhi_v37b"),
        translator_note=(
            "嘉庆四年三月；quoted_via＝恭博。园宅分赏两王：宅归庆郡王永璘、"
            "园归成亲王永瑆——禁串写。P7 湖名「睿湖」伏笔的起点在此链。"
        ),
    ),
    TextualFact(
        id="tf_qsg_yongli",
        division_id="div_qsg_319",
        verbatim_quote="三月,和珅以罪誅,沒其園第,賜永瑆",
        attested_string="沒其園第,賜永瑆",
        source_year=_dt(1928, "dt_qsg_comp", precision="year"),
        translator_note="国史层旁证，与实录同向；quoted_via＝恭博。",
    ),
    TextualFact(
        id="tf_pandeyu_feiyuan",
        division_id="div_gongbo_heshen",
        verbatim_quote="一徑四山合,上相舊園亭。繞山十二三里,煙草為誰青",
        attested_string="繞山十二三里",
        source_year=_dt(1830, "dt_pandeyu", precision="decade"),
        translator_note=(
            "潘德舆《水调歌头·游海淀和相废园》（原书未编目，quoted_via＝恭博）。"
            "时人记述层：园周「十二三里」/园池归渔人/楼贮巨自鸣钟——废园景象描写，"
            "量级为文学口径非实测。"
        ),
    ),
    TextualFact(
        id="tf_binliang_fang",
        division_id="div_gongbo_heshen",
        verbatim_quote="繽紛珂繖馳中禁,壯麗樓臺擬上林(園中樓閣均倣圓明園內規模建造,頗多僭越)",
        attested_string="園中樓閣均倣圓明園內規模建造",
        source_year=_dt(1830, "dt_binliang", precision="decade"),
        translator_note=(
            "斌良《游故相园感题》自注（quoted_via＝恭博）。清人观感层"
            "「仿圆明园规模」，与罪状十三条「蓬岛瑶台」句同向互证——"
            "均为观感/引申层，原文皆无「石舫」。"
        ),
    ),
    TextualFact(
        id="tf_gongbo_weiminghu",
        division_id="div_gongbo_heshen",
        verbatim_quote="淑春園的小湖已闢為未名湖",
        attested_string="淑春園的小湖已闢為未名湖",
        source_year=_dt(2026, "dt_gongbo_2026"),
        translator_note=(
            "恭博口径（侯仁之系统同口径）。E01 新考订框架下降为现代口径层："
            "未名湖水面承继的是今址清代园林水系，「＝淑春园故湖」存在园名与"
            "空间归属的考订分歧——见 prop_weiminghu_shuchun_lianghu（CONTESTED），不作硬事实。"
        ),
    ),
    # —— 现代层：校史与文物 ——
    TextualFact(
        id="tf_weiminghu_1928",
        division_id="div_pku_shiguan_weiminghu",
        verbatim_quote="一九二八。十一,改舊作于海甸未名湖畔!",
        attested_string="海甸未名湖畔",
        source_year=_dt(2026, "dt_pku_xsg_2026"),
        translator_note=(
            "北大校史馆考：郭德浩《落花》文末落款（1929-05 刊《燕大月刊》文艺专号），"
            "「未名湖」最早书面用例。E09：不是钱穆临时创造的新名字——"
            "1928 已出现，1931 前后渐成公认。引文逐字上屏。"
        ),
    ),
    TextualFact(
        id="tf_lake_names_1929_31",
        division_id="div_pku_shiguan_weiminghu",
        verbatim_quote="1929—1931 各名出现次数:無名湖>睿湖>未名湖",
        attested_string="無名湖>睿湖>未名湖",
        source_year=_dt(2026, "dt_pku_xsg_2026b"),
        translator_note=(
            "🔴 E07：校史馆文漏第一名——北大校友网据燕大报刊统计为"
            "「枫湖>无名湖>睿湖>未名湖」。本条不得作完整频次排序使用；"
            "画频次图必须含枫湖居首（prop_lake_freq_three_names DISPROVEN）。"
        ),
    ),
    TextualFact(
        id="tf_weiminghu_1931vote",
        division_id="div_pku_shiguan_weiminghu",
        verbatim_quote="1931-05-02《燕京大學校刊》推出燕大建筑命名投票",
        attested_string="燕大建筑命名投票",
        source_year=_dt(2026, "dt_pku_xsg_2026c"),
        translator_note=(
            "🔴 E08：那次是燕大建筑命名投票，不是未名湖名称四选一投票；"
            "此后临湖轩集会钱穆赞成「未名湖」、冰心等支持；"
            "校方从未正式给湖作行政命名（prop_1931_lake_vote DISPROVEN）。"
        ),
    ),
    TextualFact(
        id="tf_wubian_tiba",
        division_id="div_pku_lib_scrolls",
        verbatim_quote="已〔乙〕卯歲上巳日寫",
        attested_string="已〔乙〕卯歲上巳日寫",
        source_year=_dt(1615, "dt_wubian_tiba"),
        translator_note=(
            "吴彬《勺园祓禊图》自题；转录经中华读书报2010-10-22（张红扬，目验），"
            "画卷本体未目验。🔴 E06：1615 年干支为乙卯；底本转录作「已」，"
            "系「乙」之形讹，校作「已〔乙〕卯」（〔〕内为校勘字，仿 cishousi 讹文体例）；"
            "「己」是另一干支绝非异写——全模块严禁出现该误写（负控扫描守卫）。"
            "上巳日＝1615-03-31。"
        ),
    ),
    TextualFact(
        id="tf_miwanzhong_tiba",
        division_id="div_pku_lib_scrolls",
        verbatim_quote="丁巳三月寫",
        attested_string="丁巳三月寫",
        source_year=_dt(1617, "dt_mi_tiba"),
        translator_note=(
            "米万钟《勺园修禊图》自题，万历四十五年丁巳（1617）。"
            "翁万戈推断为吴卷临本，「再创作」说并存（A17）。"
            "「祓禊图（吴彬）/修禊图（米万钟）」双名统一，「祗图」异写禁上屏。"
        ),
    ),
    TextualFact(
        id="tf_wengtonghe_riji",
        division_id="div_pku_lib_scrolls",
        verbatim_quote="傍晚歸,見吳彬畫米萬鍾勺園圖",
        attested_string="見吳彬畫米萬鍾勺園圖",
        source_year=_dt(1885, "dt_wength_riji"),
        translator_note=(
            "翁同龢光绪十一年四月十二日（1885-05-25）日记；两卷流转锚："
            "翁同龢购入→翁万戈1948携美→2010-09-13 捐赠北大图书馆。"
        ),
    ),
    TextualFact(
        id="tf_1982_tiaoshi",
        division_id="div_pku_lib_scrolls",
        verbatim_quote="1982年春五号楼北侧湖岸下2米发现三整块长方形条石铺砌建筑遗址",
        attested_string="三整块长方形条石铺砌建筑遗址",
        source_year=_dt(2010, "dt_zhdsb_2010"),
        translator_note=(
            "「应当是米萬鍾勺園某湖西岸建築的殘存部分」为研究者判断"
            "（中华读书报2010-10-22转述）。原始考古简报待核（待核8）：只可写"
            "「发现建筑基础遗迹/条石遗存」，禁「考古发掘证明勺园边界」——"
            "这是勺园故址在燕园范围内的唯一考古实物线索（方位级，非边界级）。"
        ),
    ),
    TextualFact(
        id="tf_shiping_shi",
        division_id="div_pku_fdcb_shifang",
        verbatim_quote="畫舫平臨蘋岸闊,飛樓俯瞰柳蔭多。夾鏡光澄風四面,垂虹影界水中央。",
        attested_string="夾鏡光澄風四面",
        source_year=_dt(2026, "dt_pku_fdcb"),
        translator_note=(
            "四条石屏刻诗（北大文物档案/校友网转引）。诗＝乾隆题圆明园夹镜鸣琴联刻，"
            "圆明园毁后移入燕园（PKU 校友网＋中新网2010 双源）——非和珅淑春园原物"
            "（四-4 冻结，最易讲错的一件实物）。「俯瞰」他源作「俯映」，"
            "异文待核（待核7）：屏显冻结前须以现场高清拓片逐字核完整四句。"
        ),
    ),
    TextualFact(
        id="tf_guobao_5475",
        division_id="div_guobao5_ymh",
        verbatim_quote="未名湖燕園建築",
        attested_string="未名湖燕園建築",
        source_year=_dt(2001, "dt_guobao5"),
        translator_note=(
            "2001-06-25 国发〔2001〕25号，第五批全国重点文物保护单位，编号 5-475，"
            "类别近现代重要史迹及代表性建筑。名录原文页逐字待核（待核6）；"
            "名称与编号经北京市文物局公开页确认（闸门P8）。"
            "表述规范：全称「全国重点文物保护单位」，禁任何缩略变体（负控制15）。"
        ),
    ),
]


# ==================================================================
# 空间实体（两个园址系统＋一个后期合流区，实体分立）
# ==================================================================

ENTITIES: List[PersistentSpatialEntity] = [
    PersistentSpatialEntity(id="ent_shaoyuan", kind=PhysicalThingKind.GARDEN_COMPLEX,
                            canonical_label="勺园（明·米万钟，海淀清华园之东，清前期故址一带为弘雅园）"),
    PersistentSpatialEntity(id="ent_hongya_jixian", kind=PhysicalThingKind.GARDEN_COMPLEX,
                            canonical_label="弘雅园→集贤院（勺园故址清前期园林，1801改圆明园值日公所，1860毁）"),
    # E01：实体 id 用 ent_shuchunyuan（计划接口约定），规范标签必须带争议标记——
    # 链名正名「和珅海淀赐园链」，不再称「淑春园链」
    PersistentSpatialEntity(id="ent_shuchunyuan", kind=PhysicalThingKind.GARDEN_COMPLEX,
                            canonical_label="和珅海淀赐园（俗称十笏园；是否即名「淑春园」有争议；1799赏永瑆，后入睿王园系统）"),
    PersistentSpatialEntity(id="ent_weiming_lake", kind=PhysicalThingKind.NATURAL_WATERCOURSE,
                            canonical_label="未名湖（燕园核心水面，承继今址清代园林水系）"),
    PersistentSpatialEntity(id="ent_yanjing_campus", kind=PhysicalThingKind.MODERN_INSTITUTION,
                            canonical_label="燕京大学校园→北京大学燕园（1920购地，「未名湖燕园建筑」5-475）"),
    PersistentSpatialEntity(id="ent_shifang_base", kind=PhysicalThingKind.HUMAN_MADE_ARTIFACT,
                            canonical_label="石舫底座（和珅海淀赐园系统遗构，今存未名湖畔）"),
    PersistentSpatialEntity(id="ent_shiping", kind=PhysicalThingKind.HUMAN_MADE_ARTIFACT,
                            canonical_label="石屏四条（乾隆题圆明园夹镜鸣琴联刻移入，非和珅物）"),
    PersistentSpatialEntity(id="ent_boya_ta", kind=PhysicalThingKind.SINGLE_BUILDING,
                            canonical_label="博雅塔（1924—1925水塔，仿通州燃灯塔外形）"),
]


# ==================================================================
# 历史状态链
# ==================================================================

STATES: List[HistoricalFeatureState] = [
    # ---- 勺园（明） ----
    HistoricalFeatureState(
        id="st_sy_ming", entity_id="ent_shaoyuan", label="明万历间：米万钟筑勺园（约1612—1614，现代口径）",
        time_span=_ts(1612, 1644, "ts_sy1"),
        geometry="海淀，清华园之东（卷79按语「應在清華園之東」）；百亩（《帝京景物略》「百畝耳」）；"
                 "又名風煙里，都人称米家園、米家燈；建园年份挂现代口径（约1612—1614，E12「约」字必留）",
        function="明万历间米万钟私园（万历二十三年乙未进士，号友石，「南董北米」）",
        evidence_fact_ids=["tf_cck_xinzhu", "tf_djwl_baimu", "tf_cck_naming",
                           "tf_rxjwkc79_east", "tf_cck_mijiadeng"],
    ),
    HistoricalFeatureState(
        id="st_sy_fei", entity_id="ent_shaoyuan", label="明末清初渐废；乾隆朝官书「今其園不可攷」",
        time_span=_ts(1644, 1801, "ts_sy2"),
        geometry="勺园故址渐废；最硬断代锚＝乾隆朝官书按语「今其園不可攷，海淀之東有米家墳在焉」；"
                 "故址边界只到方位级（四-6：百亩/清华园之东/今燕园西南隅一带，禁画精确边界）；"
                 "毁因无文据，归因禁写（负控制7）",
        function="废园/故址",
        evidence_fact_ids=["tf_rxjwkc79_bukao"],
    ),
    HistoricalFeatureState(
        id="st_sy_1981", entity_id="ent_shaoyuan", label="1981：勺园旧址建留学生楼群，恢复「勺园」旧称",
        time_span=_ts(1981, 2026, "ts_sy3"),
        geometry="1981 年在勺园旧址（燕园西南隅一带）建留学生楼群，恢复的是「名」不是「园」"
                 "（负控制14：今勺园≠米家勺园原址原样）；「勺园」与「勺园楼群」同帧时后者必须带「今」字限定",
        function="北京大学留学生公寓区（今勺园）",
        evidence_fact_ids=["tf_rxjwkc79_bukao", "tf_xiaoting_jixianyuan"],
    ),
    # ---- 弘雅园→集贤院（勺园链，西南系统） ----
    HistoricalFeatureState(
        id="st_hy_qianqi", entity_id="ent_hongya_jixian", label="清前期：弘雅园（断代待核）",
        time_span=_ts(1662, 1801, "ts_hy1"),
        geometry="勺园故址一带的清前期园林，曾为郑亲王邸园，后归内务府；"
                 "「康熙赐积哈纳」已删（E10：PKU 官网口径内部矛盾，积哈纳为乾隆朝人物）；"
                 "「弘雅园」三字待清代原典直核（待核2）；乾隆朝御制诗注桥梁「洪雅园即米万钟勺园」"
                 "见闸门 E10（园名异写洪/弘）",
        function="清前期园囿→郑亲王邸园→内务府",
        evidence_fact_ids=["tf_hongya_1801", "tf_xiaoting_jixianyuan"],
    ),
    HistoricalFeatureState(
        id="st_hy_jixianyuan", entity_id="ent_hongya_jixian", label="1801：改圆明园值日公所（集贤院）",
        time_span=_ts(1801, 1860, "ts_hy2"),
        geometry="嘉庆六年辛酉（1801）「賞滿漢文職堂官弘雅園一區，為圓明園值日公所」——即集贤院，"
                 "俗谓六曹卿贰寓直之所（昭梿）；马戛尔尼使团寓所说属此链"
                 "（口播须挂「据故宫学者何瑜考证」归因，禁清宫档案体；E11：不入和珅园链）",
        function="圆明园值日公所/官员寓直公所",
        evidence_fact_ids=["tf_hongya_1801", "tf_xiaoting_jixianyuan"],
    ),
    HistoricalFeatureState(
        id="st_hy_hui", entity_id="ent_hongya_jixian", label="1860：毁于兵燹",
        time_span=_ts(1860, 1981, "ts_hy3"),
        geometry="咸丰十年庚申区域遭兵燹，集贤院毁（现代口径）；"
                 "「囚英法俘虏招报复」说＝侯仁之自注「相傳」，传闻层禁作史实",
        function="废址",
        evidence_fact_ids=["tf_hongya_1801", "tf_xiaoting_jixianyuan"],
    ),
    HistoricalFeatureState(
        id="st_hy_legacy", entity_id="ent_hongya_jixian", label="1981：勺园楼群「集贤厅」承接旧名",
        time_span=_ts(1981, 2026, "ts_hy4"),
        geometry="勺园留学生楼群以「集贤厅」等命名承接弘雅园—集贤院旧名（今名承接，非园存）",
        function="名称承接",
        evidence_fact_ids=["tf_hongya_1801"],
    ),
    # ---- 和珅海淀赐园（十笏园；「淑春园」名称关系有争议） ----
    HistoricalFeatureState(
        id="st_sc_1763", entity_id="ent_shuchunyuan", label="1763：「淑春園」名已见于水田档案（归属争议）",
        time_span=_ts(1763, 1775, "ts_sc1"),
        geometry="乾隆二十八年癸未档案「圓明園所交淑春園並北樓門外等處水田一頃二十三畝六分三厘，"
                 "歲徵租銀三十九兩一錢九分五厘有奇」——以水田交租的官园；该园是否即今北大相关园址"
                 "存在学术争议（E02：何瑜据「北楼门」判在圆明园北部）",
        function="内务府官园（园名归属争议见 prop_shuchunyuan_he_shen_identity）",
        evidence_fact_ids=["tf_shuchun_shuitian_1763"],
    ),
    HistoricalFeatureState(
        id="st_sc_qianlong", entity_id="ent_shuchunyuan",
        label="乾隆后期：和珅海淀赐园（十笏园；受赐年份与园名均有争议）",
        time_span=_ts(1775, 1799, "ts_sc2"),
        geometry="乾隆后期和珅在海淀获御赐园林（受赐年份争议：何瑜推约乾隆四十六年、"
                 "郝黎只稳到乾隆年间——原始谕旨未核，另一现代口径年份亦不得进正式口播，"
                 "见命题层受赐年份争议[CONTESTED]）；园中「樓閣均倣圓明園內規模建造」（斌良诗自注）；"
                 "奕譞诗序仅言「乾隆年間屬和相珅」",
        function="和珅别墅园（俗称十笏园，见昭梿）",
        evidence_fact_ids=["tf_yixuan_xu", "tf_binliang_fang"],
    ),
    HistoricalFeatureState(
        id="st_sc_1799", entity_id="ent_shuchunyuan", label="嘉庆四年：赐死查抄，园赏成亲王永瑆",
        time_span=_ts(1799, 1830, "ts_sc3"),
        geometry="嘉庆四年己未正月和珅赐死查抄；二十罪第十三条涉楠木房屋与园寓点缀"
                 "（原文无「石舫」二字）；查抄档案「現查得和珅花園內房一千零三間，遊廊樓亭共房三百五十七間」"
                 "（E04：房数＝1003；不同查抄材料分列不拼总[E05]）；"
                 "三月「和珅之園，已賞給成親王永瑆居住」（宅归永璘，园归永瑆，禁串）",
        function="抄没→赐成亲王永瑆",
        evidence_fact_ids=["tf_zui13", "tf_hsnd_fang1003", "tf_yongansi_garden1",
                           "tf_yongansi_garden2", "tf_yongli_grant", "tf_qsg_yongli"],
    ),
    HistoricalFeatureState(
        id="st_sc_ruiwang", entity_id="ent_shuchunyuan",
        label="道光间：辗转入睿亲王（仁寿）名下（睿王园/睿邸）",
        time_span=_ts(1830, 1860, "ts_sc4"),
        geometry="园辗转入睿亲王仁寿名下（唐克扬系统；奕譞诗序「後輾轉為睿邸園寓」时人追述互证）；"
                 "清末民初地图称睿王園/睿邸；奕譞游邻园咏《石舫》《孤屿》——石舫中后期尚存的咏物证据；"
                 "潘德舆词：园周「繞山十二三里」",
        function="睿王园系统（湖名「睿湖」伏笔）",
        evidence_fact_ids=["tf_yixuan_xu", "tf_yixuan_guyu", "tf_pandeyu_feiyuan"],
    ),
    HistoricalFeatureState(
        id="st_sc_1860", entity_id="ent_shuchunyuan", label="1860：兵燹重创，沦为废园",
        time_span=_ts(1860, 1920, "ts_sc5"),
        geometry="咸丰十年庚申区域遭兵燹（分寸＝重创，不写「一夜归零」）；"
                 "「雖棟宇僅存，山水之秀美固自若也」",
        function="废园",
        evidence_fact_ids=["tf_yixuan_xu"],
    ),
    HistoricalFeatureState(
        id="st_sc_1920", entity_id="ent_shuchunyuan", label="民国：园地入陈树藩手；1920 前后燕大购地",
        time_span=_ts(1920, 2026, "ts_sc6"),
        geometry="民国园地入陕西督军陈树藩之手；1920 前后司徒雷登购淑春园等故地"
                 "（六万银元、退二万充奖学金——司徒雷登回忆系统转述，契约未核，待核4）；"
                 "故湖经疏浚纳入校园（「＝未名湖」挂现代口径层，归属争议见 prop_weiminghu_shuchun_lianghu）",
        function="故地转入燕京大学校园",
        evidence_fact_ids=["tf_shuchun_shuitian_1763", "tf_gongbo_weiminghu"],
    ),
    # ---- 未名湖 ----
    HistoricalFeatureState(
        id="st_wm_1926", entity_id="ent_weiming_lake",
        label="1926 前后：故湖疏浚纳入校园→未名湖",
        time_span=_ts(1926, 2026, "ts_wm1"),
        geometry="未名湖水面承继今址清代园林水系（该带先后属和珅园、成亲王园、睿王园系统；"
                 "旧研究常称淑春园水面，但园名与空间归属存在考订分歧[E01]）；"
                 "1928-11「未名湖」最早书面用例；1929—1931 并用名含无名湖/睿湖/未名湖，"
                 "校友网燕大报刊统计频次为枫湖>无名湖>睿湖>未名湖（E07）；1931 前后渐成公认；"
                 "1924—1925 湖东南建水塔（今博雅塔）",
        function="燕园核心水面",
        evidence_fact_ids=["tf_weiminghu_1928", "tf_lake_names_1929_31",
                           "tf_weiminghu_1931vote", "tf_gongbo_weiminghu"],
    ),
    # ---- 燕京大学校园→北大燕园 ----
    HistoricalFeatureState(
        id="st_yj_1920", entity_id="ent_yanjing_campus",
        label="1920 前后购地建校→1926 秋迁入运行→1929 正式开幕",
        time_span=_ts(1920, 1952, "ts_yj1"),
        geometry="1920 前后购得淑春园等故地（United Board/Yale 档案：1920 夏取得新校址，闸门P6）；"
                 "墨菲总体规划、翟伯协办；1926 秋开始迁入并运行；1929 正式开幕；"
                 "1924-07 打深井，1924—1925 建水塔（仿通州燃灯塔外形，13 级、高 37 米，"
                 "钢筋混凝土——今博雅塔；非古塔、非燕园旧物）",
        function="燕京大学校园（1919 合并组建，司徒雷登任校长）",
        evidence_fact_ids=["tf_weiminghu_1928"],
    ),
    HistoricalFeatureState(
        id="st_yj_1952", entity_id="ent_yanjing_campus",
        label="1952：北大迁入→1990 市保→2001 国保 5-475",
        time_span=_ts(1952, 2026, "ts_yj2"),
        geometry="1952 院系调整北京大学自沙滩迁入燕园（「迁入/合并」，校史叙事归各校官方口径，"
                 "本集只讲这块地[负控制10]）；1990-10「原燕京大学未名湖區」列北京市文物保护单位；"
                 "2001-06-25「未名湖燕園建築」列第五批全国重点文物保护单位"
                 "（编号 5-475，近现代重要史迹及代表性建筑）；石屏四条与石舫底座今同置未名湖北岸",
        function="北京大学燕园（全国重点文物保护单位「未名湖燕园建筑」所在）",
        evidence_fact_ids=["tf_guobao_5475"],
    ),
    # ---- 石舫底座 ----
    HistoricalFeatureState(
        id="st_sf_qing", entity_id="ent_shifang_base", label="清：和珅园池石舫（奕譞咏物证其尚存）",
        time_span=_ts(1775, 1920, "ts_sf1"),
        geometry="仿清漪园清晏舫规制而略小（市文物局宋惕冰文口径，单源；尺寸不上口播——负控制12）；"
                 "位置三说并存（北大文物档案「未名湖北岸，健齋以東，土山之陽」/市文物局「湖岛东岸」/"
                 "恭博「小岛东岸」），口播只用「未名湖畔」；今人把「僭侈逾制」连到石舫＝现代引申层，"
                 "罪状原文无石舫（E01/P1、负控制2）",
        function="和珅海淀赐园系统遗构（名称归属争议见 prop_shuchunyuan_he_shen_identity）",
        evidence_fact_ids=["tf_yixuan_xu", "tf_zui13"],
    ),
    HistoricalFeatureState(
        id="st_sf_now", entity_id="ent_shifang_base", label="今：未名湖畔石舫残基",
        time_span=_ts(1920, 2026, "ts_sf2"),
        geometry="石舫基座今存未名湖畔，可登临；燕大建校后纳入校园（毕业照第一背景）",
        function="校园遗构景观",
        evidence_fact_ids=["tf_yixuan_xu"],
    ),
    # ---- 石屏四条 ----
    HistoricalFeatureState(
        id="st_sp_now", entity_id="ent_shiping", label="圆明园夹镜鸣琴联刻移入燕园",
        time_span=_ts(1860, 2026, "ts_sp1"),
        geometry="四条石屏刻乾隆题圆明园夹镜鸣琴联诗（移入年代无档，待核7；圆明园毁后移入，"
                 "PKU 校友网＋中新网2010 双源）——非和珅淑春园原物（四-4 冻结）；"
                 "与石舫同置≠原属同园（北大文物档案连述不采）；"
                 "「俯瞰/俯映」异文待核，屏显冻结前须现场拓片逐字核",
        function="移入遗存刻石",
        evidence_fact_ids=["tf_shiping_shi"],
    ),
    # ---- 博雅塔 ----
    HistoricalFeatureState(
        id="st_bt_1925", entity_id="ent_boya_ta", label="1924—1925 水塔（今博雅塔）",
        time_span=_ts(1924, 2026, "ts_bt1"),
        geometry="1924-07 打深井，1924—1925 建水塔；仿通州燃灯塔外形，13 级、高 37 米，"
                 "钢筋混凝土中空螺旋梯（北大文物页口径）；水塔功能已弃；"
                 "非古塔非辽塔、塔里无舍利（负控制11）；「一塔湖图」为谐音玩笑引语（负控制10）；"
                 "任何帧不得画成砖木古塔质感（混凝土＋密檐外形）",
        function="水塔→校园地标（今名博雅塔）",
        evidence_fact_ids=["tf_weiminghu_1928"],
    ),
]


# ==================================================================
# 地名指称
# ==================================================================

APPELLATIONS: List[Appellation] = [
    Appellation(id="app_shaoyuan", label="勺园", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1612, 2026, "ts_ap_sy"),
                attesting_fact_ids=["tf_cck_xinzhu", "tf_cck_naming"]),
    Appellation(id="app_fengyanli", label="风烟里", kind=AppellationKind.OLD_NAME,
                script_variants=["風煙里"],
                valid_time_span=_ts(1612, 1644, "ts_ap_fyl"),
                attesting_fact_ids=["tf_cck_xinzhu"]),
    Appellation(id="app_mijiayuan", label="米家园", kind=AppellationKind.VULGAR,
                script_variants=["米家園"],
                valid_time_span=_ts(1612, 1644, "ts_ap_mjy"),
                attesting_fact_ids=["tf_cck_mijiayuan"]),
    Appellation(id="app_mijiadeng", label="米家灯", kind=AppellationKind.VULGAR,
                script_variants=["米家燈"],
                valid_time_span=_ts(1612, 1644, "ts_ap_mjd"),
                attesting_fact_ids=["tf_cck_mijiadeng"]),
    Appellation(id="app_hongya", label="弘雅园", kind=AppellationKind.OFFICIAL,
                script_variants=["弘雅園", "洪雅园", "洪雅園"],
                valid_time_span=_ts(1662, 1801, "ts_ap_hy"),
                attesting_fact_ids=["tf_hongya_1801"]),
    Appellation(id="app_jixianyuan", label="集贤院", kind=AppellationKind.OFFICIAL,
                script_variants=["集賢院"],
                valid_time_span=_ts(1801, 1981, "ts_ap_jxy"),
                attesting_fact_ids=["tf_xiaoting_jixianyuan", "tf_hongya_1801"]),
    # 「淑春园」：官方档案确有其名（1763），但所指是否即今和珅园址存在学术争议——
    # 指称断言 rr_shuchun 挂 CONTESTED（E01 争议建模，不判死）
    Appellation(id="app_shuchun", label="淑春园", kind=AppellationKind.OFFICIAL,
                script_variants=["淑春園", "舒春園", "舒春园"],
                valid_time_span=_ts(1763, 1920, "ts_ap_sc"),
                attesting_fact_ids=["tf_shuchun_shuitian_1763", "tf_yixuan_xu"]),
    Appellation(id="app_shihu", label="十笏园", kind=AppellationKind.VULGAR,
                script_variants=["十笏園"],
                valid_time_span=_ts(1775, 1860, "ts_ap_shihu"),
                attesting_fact_ids=["tf_xiaoting_shihu"]),
    Appellation(id="app_ruiwangyuan", label="睿王园", kind=AppellationKind.OLD_NAME,
                script_variants=["睿王園", "睿邸"],
                valid_time_span=_ts(1830, 1920, "ts_ap_rwy"),
                attesting_fact_ids=["tf_yixuan_xu"]),
    Appellation(id="app_weiminghu", label="未名湖", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1928, 2026, "ts_ap_wmh"),
                attesting_fact_ids=["tf_weiminghu_1928"]),
    Appellation(id="app_wuminghu", label="无名湖", kind=AppellationKind.OLD_NAME,
                script_variants=["無名湖"],
                valid_time_span=_ts(1929, 1931, "ts_ap_wmh2"),
                attesting_fact_ids=["tf_lake_names_1929_31"]),
    Appellation(id="app_ruihu", label="睿湖", kind=AppellationKind.OLD_NAME,
                valid_time_span=_ts(1929, 1931, "ts_ap_rh"),
                attesting_fact_ids=["tf_lake_names_1929_31"]),
    Appellation(id="app_fenghu", label="枫湖", kind=AppellationKind.OLD_NAME,
                script_variants=["楓湖"],
                valid_time_span=_ts(1929, 1931, "ts_ap_fh"),
                attesting_fact_ids=["tf_lake_names_1929_31"]),
    Appellation(id="app_shifang", label="石舫", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1775, 2026, "ts_ap_sf"),
                attesting_fact_ids=["tf_yixuan_xu"]),
    Appellation(id="app_boya", label="博雅塔", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1925, 2026, "ts_ap_bt"),
                attesting_fact_ids=[]),
    Appellation(id="app_guobao", label="未名湖燕园建筑", kind=AppellationKind.OFFICIAL,
                script_variants=["未名湖燕園建築"],
                valid_time_span=_ts(2001, 2026, "ts_ap_gb"),
                attesting_fact_ids=["tf_guobao_5475"]),
]


# ==================================================================
# 命题层（E01—E12 闸门裁决的建模落位）
# ==================================================================

PROPOSITIONS: List[Proposition] = [
    Proposition(
        id="prop_shuchunyuan_he_shen_identity",
        statement="和珅海淀赐园即名「淑春园」（两园一名）。",
        derived_from_fact_ids=["tf_shuchun_shuitian_1763", "tf_yixuan_xu",
                               "tf_xiaoting_shihu"],
        inferred_subject_id="ent_shuchunyuan",
        inference_method=(
            "争议建模，不判死（E01）。何瑜（故宫博物院院刊2021）据一史馆档案与样式雷图："
            "1763《会典事例》淑春园在长春园北（据「北楼门」位置），今北大另有十公主淑春园，"
            "和珅园为其东邻十笏园，1799 给永瑆、1838 再给睿亲王仁寿，后与相邻淑春园合称睿王园。"
            "郝黎（恭王府博物馆2026-03-24）据奕譞、丰绅殷德等清人材料主张和珅园很可能即名淑春园。"
            "两说均有清人材料支撑。"
        ),
        alternative_explanations=[
            "何瑜：淑春园在长春园北；和珅园为相邻的十笏园，二者非一名之异写",
            "郝黎：和珅园即名淑春园，十笏园为其别称/俗名（奕譞诗题「舒春園」佐证）",
        ],
    ),
    Proposition(
        id="prop_grant_year_1784",
        statement="乾隆四十九年（1784）淑春园/和珅园赐给和珅。",
        derived_from_fact_ids=["tf_yixuan_xu"],
        inferred_subject_id="ent_shuchunyuan",
        inference_method=(
            "年份未定且园名本身有争议（E03 升为最高优先级待核）。何瑜将和珅十笏园受赐推到"
            "约乾隆四十六年；郝黎只稳到「乾隆年间」；北大文物档案/校史文作乾隆四十九年"
            "（现代口径，原始谕旨未核，待核5）。两套研究连园名都未统一，"
            "1784/1781 均不得当稳定节点。"
        ),
        alternative_explanations=[
            "约乾隆四十六年（何瑜推算）",
            "乾隆四十九年（北大文物档案/校史文现代口径，无原始谕旨）",
            "乾隆年间宽断（郝黎；奕譞诗序时人上限）",
        ],
    ),
    Proposition(
        id="prop_shuchun_name_early_evidence",
        statement="淑春园名早于和珅受园，证明该园即今北大相关园址。",
        derived_from_fact_ids=["tf_shuchun_shuitian_1763"],
        inferred_subject_id="ent_shuchunyuan",
        inference_method=(
            "跨层取证（E02 撤销）。1763 档案只证有一处以水田交租的淑春园官园；"
            "何瑜据「北楼门」位置把该园定位到圆明园北部而非北大。"
            "「名称存在早」不等于「园址即今北大」。"
        ),
        alternative_explanations=[
            "1763 淑春园即今北大相关园址（侯仁之—恭博旧说系统）",
            "1763 淑春园在圆明园北，与今北大园址无涉（何瑜 2021）",
        ],
    ),
    Proposition(
        id="prop_room_count_1030",
        statement="和珅海淀园内房数在流传中被添位误读（原文「房一千零三間」，讹作五位数）。",
        derived_from_fact_ids=["tf_hsnd_fang1003"],
        inferred_subject_id="ent_shuchunyuan",
        inference_method=(
            "文字性硬伤建模（E04）。A10 原文「現查得和珅花園內房一千零三間」＝1003 间；"
            "添位讹读值在数据层（事实/状态/指称）与口播层全模块禁现（负控扫描守卫），"
            "错值只以本 DISPROVEN 命题定性存档，不复写其形。"
        ),
        alternative_explanations=[
            "（本集无支持讹读的一手依据）",
        ],
    ),
    Proposition(
        id="prop_inventory_sum",
        statement="楼台四十二所与亭台六十四所可加总为同一园林的统一统计。",
        derived_from_fact_ids=["tf_yongansi_garden1", "tf_yongansi_garden2",
                               "tf_hsnd_fang1003"],
        inferred_subject_id="ent_shuchunyuan",
        inference_method=(
            "证据拼接过度（E05）。抄家清单列「两座花园」（花园一座楼台四十二所；"
            "钦赐花园一座亭台六十四所……），海淀花园查抄档另记「房一千零三间」——"
            "不同查抄材料、不同统计口径，不得拼成一个园林总表；郝黎原文亦先列两园再另引海淀档。"
        ),
        alternative_explanations=[
            "两个花园数字可互换/相加（错误读法）",
            "分列口径：楼台42所＝花园一座；亭台64所＋更楼12＋更夫120＝钦赐花园一座；"
            "房1003间＝海淀花园查抄档（本集采信）",
        ],
    ),
    Proposition(
        id="prop_wubian_jimao",
        statement="吴彬《勺园祓禊图》自题「已卯歲上巳日寫」，「已」是干支用字异写，绘年当作「已卯」。",
        derived_from_fact_ids=["tf_wubian_tiba"],
        inferred_subject_id="ent_shaoyuan",
        inference_method=(
            "文字学硬伤建模（E06）。1615 年干支为乙卯；底本转录作「已」系「乙」之形讹，"
            "校作「已〔乙〕卯」。把「已」解释成另一干支的「异写」是错的——"
            "那是换个干支改绘年，不是校勘。"
        ),
        alternative_explanations=[
            "底本确作「已」，为「乙」之形讹（故宫院刊相关论文、翁万戈材料均作乙卯岁上巳日写）",
            "绘年另有所据（无任何版本支持）",
        ],
    ),
    Proposition(
        id="prop_shifang_weizhi_zuizheng",
        statement="石舫是和珅「僭侈逾制」罪的罪证。",
        derived_from_fact_ids=["tf_zui13", "tf_yixuan_guyu"],
        inferred_subject_id="ent_shifang_base",
        inference_method=(
            "证据拼接（负控制2）。二十罪第十三条原文只涉楠木房屋（仿宁寿宫制度）与"
            "园寓点缀（类蓬岛瑶台），无「石舫」二字；奕譞《孤屿》注亦自标「聞」传闻层。"
            "「僭侈逾制→石舫」是现代文章（市文物局宋惕冰文等）由「蓬岛瑶台」句引申。"
            "口播只可说「今人把这条罪名连到石舫上」。"
        ),
        alternative_explanations=[
            "石舫即违制罪证（现代引申，无原文支撑）",
            "罪名所涉为楠木房屋与园寓点缀，与石舫无直接文本关联（本集采信）",
        ],
    ),
    Proposition(
        id="prop_two_chains_one_line",
        statement="勺园→弘雅园→集贤院与和珅赐园→永瑆→睿邸是同一条产权链，未名湖属勺园链。",
        derived_from_fact_ids=["tf_xiaoting_shihu", "tf_xiaoting_jixianyuan",
                               "tf_rxjwkc79_bukao"],
        inferred_subject_id="ent_shuchunyuan",
        inference_method=(
            "昭梿《啸亭杂录》卷九把两处园分写：「勺園……今改集賢院」与"
            "「和相十笏園……近為成邸所居」——时人硬证两链分立（E01，闸门待核9关闭）。"
            "未名湖一带属和珅园链，勺园故址在燕园西南隅（1982 条石遗址方位级佐证）。"
        ),
        alternative_explanations=[
            "一条产权链接力（低质旅游文案常见，判错）",
            "两个园址系统＋一个后期合流区（本集采信）",
        ],
    ),
    Proposition(
        id="prop_weiminghu_shaoyuan_zhi",
        statement="未名湖即米万钟勺园故址（勺园故湖）。",
        derived_from_fact_ids=["tf_rxjwkc79_bukao", "tf_1982_tiaoshi"],
        inferred_subject_id="ent_weiming_lake",
        inference_method=(
            "强负控制（四-5）。乾隆官书「今其園不可攷」＋勺园故址在燕园西南隅一带"
            "（名录/侯仁之系统/1982 条石遗址），与湖不重合；未名湖水面承继的是"
            "今址清代园林水系（和珅园—成亲王园—睿王园系统）。"
            "凡「未名湖即勺园旧址」一律判错。"
        ),
        alternative_explanations=[
            "湖即勺园故湖（常见错误表述）",
            "湖承继今址清代园林水系，勺园故址另在西南隅（本集采信）",
        ],
    ),
    Proposition(
        id="prop_weiminghu_shuchun_lianghu",
        statement="未名湖就是淑春园故湖。",
        derived_from_fact_ids=["tf_gongbo_weiminghu", "tf_shuchun_shuitian_1763"],
        inferred_subject_id="ent_weiming_lake",
        inference_method=(
            "E01 新考订框架：旧研究（侯仁之系统＋恭博「淑春園的小湖已闢為未名湖」）常称"
            "淑春园水面，但园名和空间归属存在新的考订分歧——不宜写成硬事实，"
            "更稳表述＝「未名湖水面承继今址清代园林水系；这一带先后属和珅园、"
            "成亲王园及睿王园系统」。"
        ),
        alternative_explanations=[
            "未名湖＝淑春园故湖（侯仁之—恭博系统）",
            "淑春园在长春园北，今未名湖带属十笏园系统（何瑜 2021）",
        ],
    ),
    Proposition(
        id="prop_qianmu_created_name",
        statement="「未名湖」是钱穆命名/临时创造的新名字。",
        derived_from_fact_ids=["tf_weiminghu_1928", "tf_weiminghu_1931vote"],
        inferred_subject_id="ent_weiming_lake",
        inference_method=(
            "1928-11 学生郭德浩落款已见「未名湖」，而钱穆 1930 秋才到燕大；"
            "1931 临湖轩集会钱穆是「赞成」此名，冰心等支持。E09 定稿表述："
            "「未名湖」不是钱穆临时创造的新名字；它在 1928 年已经出现，"
            "到 1931 年前后逐渐成为公认名称；燕大校方从未正式给湖作行政命名。"
        ),
        alternative_explanations=[
            "冰心拍板说（并存口径，不采单一）",
            "未名社影响说（并存口径，不采单一）",
            "1928 已有书面用例＋1931 集会渐成公认（本集采信）",
        ],
    ),
    Proposition(
        id="prop_1931_lake_vote",
        statement="1931-05-02 的投票是未名湖名称的投票。",
        derived_from_fact_ids=["tf_weiminghu_1931vote"],
        inferred_subject_id="ent_weiming_lake",
        inference_method=(
            "事件性质错误（E08）。那次是燕大建筑命名投票，不是未名湖名称四选一投票；"
            "湖名的公认形成于其后的命名氛围（临湖轩集会），校方从未行政命名。"
        ),
        alternative_explanations=[
            "湖名四选一投票（错误）",
            "燕大建筑命名投票，湖名在其氛围中渐定（本集采信）",
        ],
    ),
    Proposition(
        id="prop_lake_freq_three_names",
        statement="1929—1931 湖名出现次数排序为無名湖>睿湖>未名湖（三名即完整）。",
        derived_from_fact_ids=["tf_lake_names_1929_31"],
        inferred_subject_id="ent_weiming_lake",
        inference_method=(
            "数据硬伤（E07）。北大校友网基于燕大报刊统计明确为：枫湖>无名湖>睿湖>未名湖——"
            "校史馆文漏第一名枫湖。若画频次条形图必须加入枫湖居首，"
            "或改用名称时间带（未名池→校湖→无名湖→未名湖→睿湖→枫湖）。"
        ),
        alternative_explanations=[
            "三名排序（漏枫湖，错误）",
            "四名排序：枫湖>无名湖>睿湖>未名湖（本集采信）",
        ],
    ),
    Proposition(
        id="prop_kangxi_jihana",
        statement="康熙年间弘雅园赐郑亲王积哈纳。",
        derived_from_fact_ids=["tf_hongya_1801"],
        inferred_subject_id="ent_hongya_jixian",
        inference_method=(
            "E10：PKU 官网同页「康熙年间」与积哈纳（乾隆朝人物）断代冲突，句删除；"
            "何瑜据史料考康熙二十六年后这里已作翰林值房「弘雅园」；乾隆十八年赐简亲王奇通阿，"
            "后转郑亲王一系。「弘雅园存在」与「康熙赐积哈纳」拆分，后句不用。"
        ),
        alternative_explanations=[
            "康熙二十六年后已作翰林值房弘雅园（何瑜）",
            "积哈纳为乾隆朝人物，康熙赐说不成立（官网内部矛盾自证）",
        ],
    ),
    Proposition(
        id="prop_majierni_hongya",
        statement="1793 年马戛尔尼使团寓居弘雅园（可作无归因的史实陈述）。",
        derived_from_fact_ids=["tf_hongya_1801"],
        inferred_subject_id="ent_hongya_jixian",
        inference_method=(
            "待核3 部分关闭，可用但须归因。何瑜据巴罗《马戛尔尼使团使华观感》认定"
            "1793 入住洪雅园；西人叙述本身可证明曾住园林，但「园名＝洪雅园」"
            "主要是现代史家识别；故宫博物院词条无此载。口播必须挂"
            "「据故宫学者何瑜考证」；禁做成清宫档案体。属勺园—弘雅园链，"
            "绝不入和珅园链（E11：塞入永瑆→睿邸链页会重新制造两链混接）。"
        ),
        alternative_explanations=[
            "寓所即洪雅园（何瑜考订）",
            "西人只证曾住某园林，园名为现代识别（更稳归因层）",
        ],
    ),
    Proposition(
        id="prop_sy_destruction_cause",
        statement="勺园毁于明末战乱（李自成/清兵入关）。",
        derived_from_fact_ids=["tf_rxjwkc79_bukao"],
        inferred_subject_id="ent_shaoyuan",
        inference_method=(
            "无据推论（负控制7）。没有任何文据记载勺园毁因；最硬断代＝"
            "乾隆朝官书「今其園不可攷」。归因不给。"
        ),
        alternative_explanations=[
            "明末战乱毁（无文据）",
            "清初圈占/改建渐废（无文据）",
            "自然圮废（无文据）",
        ],
    ),
    Proposition(
        id="prop_1612_hard_dates",
        statement="米万钟 1612—1614 年筑勺园，是与 1615 题跋同等级的硬日期。",
        derived_from_fact_ids=["tf_cck_xinzhu", "tf_wubian_tiba"],
        inferred_subject_id="ent_shaoyuan",
        inference_method=(
            "精度过高（E12）。明代当时文本（《长安客话》经卷79转录）只证「新築」无纪年；"
            "「1612—1614」为北大勺园官网等现代口径，须带「约」；"
            "不得把 1612/1614 当与 1615 题跋（有自题干支）同等级的硬日期。"
        ),
        alternative_explanations=[
            "约1612—1614（现代口径，带「约」，本集采信）",
            "万历年间宽断（更保守）",
        ],
    ),
]

ADOPTIONS: List[BeliefAdoption] = [
    BeliefAdoption(
        proposition_id="prop_shuchunyuan_he_shen_identity",
        status=EpistemicStatus.CONTESTED,
        confidence=0.5,
        adopted_by="E20 闸门 E01（gpt_review.txt：争议建模，不判死）",
        adopted_at=_dt(2026, "dt_e20_gate"),
        rationale=(
            "何瑜（故宫博物院院刊2021）用一史馆档案/奏销档/样式雷图反驳侯仁之旧说：淑春园在"
            "长春园北，和珅园为其东邻十笏园；郝黎（恭王府博物馆2026-03-24）据奕譞「舒春園屬和相珅」、"
            "丰绅殷德等清人材料主张和珅园很可能即名淑春园。两边都有实质证据，"
            "科学的处理是把争议本身建模出来，不替任何一方判死。链名正名：和珅海淀赐园链。"
        ),
    ),
    BeliefAdoption(
        proposition_id="prop_grant_year_1784",
        status=EpistemicStatus.CONTESTED,
        confidence=0.2,
        adopted_by="E20 闸门 E03（1784 退出口播白名单）",
        adopted_at=_dt(2026, "dt_e20_gate_e03"),
        rationale=(
            "1784/1781 均不得进正式口播：何瑜推约乾隆四十六年，郝黎只稳到乾隆年间，"
            "北大文物档案作 1784（现代口径，原始谕旨未核，待核5）。"
            "两套研究连园名都未统一，不应把任何单一年份当稳定节点；"
            "正片只说「乾隆后期，和珅在海淀拥有御赐园林」。"
        ),
    ),
    BeliefAdoption(
        proposition_id="prop_shuchun_name_early_evidence",
        status=EpistemicStatus.DISPROVEN,
        confidence=0.9,
        adopted_by="E20 闸门 E02",
        adopted_at=_dt(2026, "dt_e20_gate_e02"),
        rationale=(
            "1763 档案只证「有一处名为淑春园的官园」；何瑜据「北楼门」把它定位在圆明园北部。"
            "「名早于和珅＝硬证」表述撤销，不得接入今北大链。"
        ),
        refuting_fact_ids=["tf_shuchun_shuitian_1763", "tf_xiaoting_shihu"],
    ),
    BeliefAdoption(
        proposition_id="prop_room_count_1030",
        status=EpistemicStatus.DISPROVEN,
        confidence=0.99,
        adopted_by="E20 闸门 E04（数字红线）",
        adopted_at=_dt(2026, "dt_e20_gate_e04"),
        rationale=(
            "A10 原文「現查得和珅花園內房一千零三間」＝1003 间。"
            "讹读值在数据层（事实/状态/指称）全模块禁现；错值只以本 DISPROVEN 命题存档。"
        ),
        refuting_fact_ids=["tf_hsnd_fang1003"],
    ),
    BeliefAdoption(
        proposition_id="prop_inventory_sum",
        status=EpistemicStatus.DISPROVEN,
        confidence=0.95,
        adopted_by="E20 闸门 E05（口径分离）",
        adopted_at=_dt(2026, "dt_e20_gate_e05"),
        rationale=(
            "「花園一座樓臺四十二所」「欽賜花園一座亭臺六十四所…」与「房一千零三間」"
            "系不同查抄材料、不同统计口径；P4 做成「不同查抄材料分别记载」，绝不能加总；"
            "另按原文用「亭臺六十四所」，不得写「楼台64」。"
        ),
        refuting_fact_ids=["tf_yongansi_garden1", "tf_yongansi_garden2", "tf_hsnd_fang1003"],
    ),
    BeliefAdoption(
        proposition_id="prop_wubian_jimao",
        status=EpistemicStatus.DISPROVEN,
        confidence=0.99,
        adopted_by="E20 闸门 E06（文字学红线）",
        adopted_at=_dt(2026, "dt_e20_gate_e06"),
        rationale=(
            "1615＝乙卯；底本「已」为「乙」形讹，校作「已〔乙〕卯」。"
            "把形讹解释成另一干支的异写＝换干支改绘年，不是校勘；"
            "故宫院刊相关论文与翁万戈材料均作乙卯岁上巳日写。"
            "该误写全模块禁现（含命题层，负控扫描）。"
        ),
        refuting_fact_ids=["tf_wubian_tiba"],
    ),
    BeliefAdoption(
        proposition_id="prop_shifang_weizhi_zuizheng",
        status=EpistemicStatus.DISPROVEN,
        confidence=0.95,
        adopted_by="E20 闸门 P1/负控制2",
        adopted_at=_dt(2026, "dt_e20_gate_p1"),
        rationale=(
            "罪状原文无石舫字样；「僭侈逾制→石舫」为现代引申；"
            "石舫与清漪园清晏舫的仿建关系＝市文物局单源口径，画面可注、口播禁坐实；"
            "「孤屿仿蓬岛瑶台列入大罪」按奕譞原注「聞」传闻层处理。"
        ),
        refuting_fact_ids=["tf_zui13", "tf_yixuan_guyu"],
    ),
    BeliefAdoption(
        proposition_id="prop_two_chains_one_line",
        status=EpistemicStatus.DISPROVEN,
        confidence=0.95,
        adopted_by="E20 闸门 E01（两链分立＋昭梿双锚）",
        adopted_at=_dt(2026, "dt_e20_gate_e01b"),
        rationale=(
            "《啸亭杂录》卷九直核：昭梿本人就把勺园（今集贤院）与和相十笏园（近为成邸所居）"
            "作为两处园来写。画面双线图必须两色区分，「勺园链」不得画箭头指向「未名湖」。"
        ),
        refuting_fact_ids=["tf_xiaoting_shihu", "tf_xiaoting_jixianyuan"],
    ),
    BeliefAdoption(
        proposition_id="prop_weiminghu_shaoyuan_zhi",
        status=EpistemicStatus.DISPROVEN,
        confidence=0.98,
        adopted_by="E20 研究档案负控制1（四-5 冻结）",
        adopted_at=_dt(2026, "dt_e20_nc1"),
        rationale=(
            "乾隆官书「今其園不可攷」＋勺园故址在燕园西南隅（名录/侯仁之系统/1982 条石遗址）"
            "与湖不重合。凡见「未名湖即米万钟勺园旧址」一律判错。"
        ),
        refuting_fact_ids=["tf_rxjwkc79_bukao", "tf_1982_tiaoshi"],
    ),
    BeliefAdoption(
        proposition_id="prop_weiminghu_shuchun_lianghu",
        status=EpistemicStatus.CONTESTED,
        confidence=0.45,
        adopted_by="E20 闸门 E01 框架（降级为现代口径层）",
        adopted_at=_dt(2026, "dt_e20_gate_wmh"),
        rationale=(
            "「未名湖＝淑春园故湖」不宜再写成硬事实：何瑜新考订下园名和空间归属存在分歧。"
            "更稳表述：未名湖水面承继今址清代园林水系；这一带先后属和珅园、"
            "成亲王园及睿王园系统；旧研究常称其为淑春园水面。"
        ),
    ),
    BeliefAdoption(
        proposition_id="prop_qianmu_created_name",
        status=EpistemicStatus.DISPROVEN,
        confidence=0.97,
        adopted_by="E20 闸门 E09/负控制5",
        adopted_at=_dt(2026, "dt_e20_gate_e09"),
        rationale=(
            "1928-11 学生落款已见「未名湖」，钱穆 1930 秋才到燕大；"
            "正确表述＝学生 1928 年已写下「未名湖」；1931 年临湖轩集会上钱穆赞成此名，"
            "冰心等支持，从此叫定；校方从未行政命名。"
        ),
        refuting_fact_ids=["tf_weiminghu_1928", "tf_weiminghu_1931vote"],
    ),
    BeliefAdoption(
        proposition_id="prop_1931_lake_vote",
        status=EpistemicStatus.DISPROVEN,
        confidence=0.95,
        adopted_by="E20 闸门 E08",
        adopted_at=_dt(2026, "dt_e20_gate_e08"),
        rationale=(
            "1931-05-02 是燕大建筑命名投票；湖名投票说法画错事件性质。"
            "条形图/时间带均不得把该日画成湖名投票。"
        ),
        refuting_fact_ids=["tf_weiminghu_1931vote"],
    ),
    BeliefAdoption(
        proposition_id="prop_lake_freq_three_names",
        status=EpistemicStatus.DISPROVEN,
        confidence=0.95,
        adopted_by="E20 闸门 E07",
        adopted_at=_dt(2026, "dt_e20_gate_e07"),
        rationale=(
            "北大校友网基于燕大报刊统计：枫湖>无名湖>睿湖>未名湖——校史馆三名称排序漏了"
            "第一名枫湖。坚持画频次条形图必须加入枫湖；更优方案是改名称时间带。"
        ),
        refuting_fact_ids=["tf_lake_names_1929_31"],
    ),
    BeliefAdoption(
        proposition_id="prop_kangxi_jihana",
        status=EpistemicStatus.DISPROVEN,
        confidence=0.9,
        adopted_by="E20 闸门 E10",
        adopted_at=_dt(2026, "dt_e20_gate_e10"),
        rationale=(
            "积哈纳为乾隆朝人物，PKU 官网「康熙年间赐积哈纳」与其同页人物断代自相矛盾，句删除；"
            "弘雅园存在本身按何瑜清代材料链升级（康熙二十六年后翰林值房→乾隆十八年赐奇通阿→"
            "转郑亲王一系→1801 改集贤院）。"
        ),
        refuting_fact_ids=["tf_hongya_1801"],
    ),
    BeliefAdoption(
        proposition_id="prop_majierni_hongya",
        status=EpistemicStatus.CONTESTED,
        confidence=0.5,
        adopted_by="E20 闸门 待核3/E11",
        adopted_at=_dt(2026, "dt_e20_gate_mje"),
        rationale=(
            "不必禁用但须归因：口播「据故宫学者何瑜考证，1793 年马戛尔尼使团曾入住洪雅园」；"
            "故宫博物院词条无此载，禁清宫档案体；属勺园—弘雅园链，移回 P3 左线，"
            "严禁塞入永瑆→睿亲王→陈树藩的废园流转页（两链混接）。"
        ),
    ),
    BeliefAdoption(
        proposition_id="prop_sy_destruction_cause",
        status=EpistemicStatus.DISPROVEN,
        confidence=0.9,
        adopted_by="E20 研究档案负控制7",
        adopted_at=_dt(2026, "dt_e20_nc7"),
        rationale=(
            "勺园毁因无任何文据；最硬断代＝乾隆朝官书「今其園不可攷」。"
            "正片不给具体归因。"
        ),
        refuting_fact_ids=["tf_rxjwkc79_bukao"],
    ),
    BeliefAdoption(
        proposition_id="prop_1612_hard_dates",
        status=EpistemicStatus.DISPROVEN,
        confidence=0.9,
        adopted_by="E20 闸门 E12",
        adopted_at=_dt(2026, "dt_e20_gate_e12"),
        rationale=(
            "明代当时文本只证「新築」；正片说「万历年间，约 1612—1614」，"
            "「约」字必留；不上屏与 1615 题跋同等级的裸年份。"
        ),
        refuting_fact_ids=["tf_cck_xinzhu", "tf_wubian_tiba"],
    ),
]


# ==================================================================
# 空间变换
# ==================================================================

TRANSFORMATIONS: List[PlaceTransformation] = [
    PlaceTransformation(
        id="pte_sy_1612_build", entity_id="ent_shaoyuan",
        transformation=PlaceTransformationEvent.CONSTRUCTED,
        time_span=_ts(1612, 1614, "ts_pt_sy1"),
        resulting_state_id="st_sy_ming",
        resulting_condition="万历年间米万钟筑勺园（约1612—1614，现代口径，「约」字必留[E12]）；"
                            "又名風煙里，取意「淀之水濫觴一勺」",
        evidence_fact_ids=["tf_cck_xinzhu", "tf_cck_naming", "tf_djwl_baimu"],
    ),
    PlaceTransformation(
        id="pte_sy_fei", entity_id="ent_shaoyuan",
        transformation=PlaceTransformationEvent.ABANDONED,
        time_span=_ts(1644, 1783, "ts_pt_sy2"),
        resulting_state_id="st_sy_fei",
        resulting_condition="明末清初渐废；乾隆朝官书按语「今其園不可攷」"
                            "（毁因无文据，归因禁写[负控制7]）",
        evidence_fact_ids=["tf_rxjwkc79_bukao"],
    ),
    PlaceTransformation(
        id="pte_hy_1801_convert", entity_id="ent_hongya_jixian",
        transformation=PlaceTransformationEvent.REBUILT,
        time_span=_ts(1801, 1801, "ts_pt_hy1"),
        resulting_state_id="st_hy_jixianyuan",
        resulting_condition="嘉庆六年「賞滿漢文職堂官弘雅園一區，為圓明園值日公所」——集贤院之设",
        evidence_fact_ids=["tf_hongya_1801", "tf_xiaoting_jixianyuan"],
    ),
    PlaceTransformation(
        id="pte_hy_1860_destroy", entity_id="ent_hongya_jixian",
        transformation=PlaceTransformationEvent.DEMOLISHED,
        time_span=_ts(1860, 1860, "ts_pt_hy2"),
        resulting_state_id="st_hy_hui",
        resulting_condition="咸丰十年毁于兵燹（现代口径）；「囚英法俘虏招报复」说＝传闻层禁作史实",
        evidence_fact_ids=["tf_hongya_1801"],
    ),
    PlaceTransformation(
        id="pte_sc_1860_damage", entity_id="ent_shuchunyuan",
        transformation=PlaceTransformationEvent.DAMAGED,
        time_span=_ts(1860, 1860, "ts_pt_sc1"),
        resulting_state_id="st_sc_1860",
        resulting_condition="咸丰十年兵燹重创（分寸＝重创，非「一夜归零」）；"
                            "「雖棟宇僅存，山水之秀美固自若也」",
        evidence_fact_ids=["tf_yixuan_xu"],
    ),
    PlaceTransformation(
        id="pte_wm_1926_dredge", entity_id="ent_weiming_lake",
        transformation=PlaceTransformationEvent.CONSTRUCTED,
        time_span=_ts(1926, 1926, "ts_pt_wm1"),
        resulting_state_id="st_wm_1926",
        resulting_condition="故湖经疏浚纳入燕大校园；水面承继今址清代园林水系（链属表述见争议建模）",
        evidence_fact_ids=["tf_weiminghu_1928", "tf_gongbo_weiminghu"],
    ),
    PlaceTransformation(
        id="pte_yj_1920_build", entity_id="ent_yanjing_campus",
        transformation=PlaceTransformationEvent.CONSTRUCTED,
        time_span=_ts(1920, 1929, "ts_pt_yj1"),
        resulting_state_id="st_yj_1920",
        resulting_condition="1920 前后购地，墨菲规划；1926 秋迁入运行，1929 正式开幕（United Board/Yale 档案口径）",
        evidence_fact_ids=["tf_weiminghu_1928"],
    ),
    PlaceTransformation(
        id="pte_sp_relocate", entity_id="ent_shiping",
        transformation=PlaceTransformationEvent.RELOCATED,
        time_span=_ts(1860, 1926, "ts_pt_sp1"),
        resulting_state_id="st_sp_now",
        resulting_condition="圆明园夹镜鸣琴乾隆联刻毁后移入燕园（移入年代无档，待核7；非和珅物[四-4]）",
        evidence_fact_ids=["tf_shiping_shi"],
    ),
]

AGGREGATES: List[PlaceAggregate] = []


# ==================================================================
# 跨时同一性
# ==================================================================

IDENTITIES: List[DiachronicIdentityAssertion] = [
    # 西南系统：勺园故址→弘雅园→集贤院。乾隆四十六年御制诗注「洪雅园即米万钟勺园」
    # 提供有力桥梁（E10），但「弘雅园」三字尚待清代原典直核（待核2）——CONTESTED 不升确证
    DiachronicIdentityAssertion(
        id="dia_sw_chain",
        subject_entity_ids=["ent_shaoyuan", "ent_hongya_jixian"],
        relation=IdentityRelation.PARTIAL_CONTINUATION,
        time_span=_ts(1662, 2026, "ts_dia_sw"),
        evidence_fact_ids=["tf_rxjwkc79_bukao", "tf_hongya_1801",
                           "tf_xiaoting_jixianyuan"],
        status=EpistemicStatus.CONTESTED,
        alternative_relations=[
            "同一持续体（乾隆御制诗注桥梁成立时的读法）",
            "继承者（弘雅园为勺园故址上新建园林的读法）",
        ],
        is_orthogonal_to_state_change=True,
    ),
    # 未名湖与和珅园系统：水面承继今址清代园林水系，链属受 E01 争议影响
    DiachronicIdentityAssertion(
        id="dia_weiminghu_shuixi",
        subject_entity_ids=["ent_weiming_lake", "ent_shuchunyuan"],
        relation=IdentityRelation.PARTIAL_CONTINUATION,
        time_span=_ts(1920, 2026, "ts_dia_wm"),
        evidence_fact_ids=["tf_gongbo_weiminghu", "tf_weiminghu_1928"],
        status=EpistemicStatus.CONTESTED,
        alternative_relations=[
            "继承者（湖面为疏浚后新水体，非原池直接延续）",
            "存疑（园名归属争议未决，链属表述随之存疑）",
        ],
        is_orthogonal_to_state_change=True,
    ),
]


# ==================================================================
# 指称断言：古代层与现行层分挂，绝不混级
# ==================================================================

REFERENCES: List[ReferentialAssertion] = [
    ReferentialAssertion(
        id="rr_shaoyuan",
        appellation_id="app_shaoyuan",
        referent_entity_id="ent_shaoyuan",
        time_span=_ts(1612, 2026, "ts_r_sy"),
        evidence_fact_ids=["tf_cck_xinzhu", "tf_cck_naming"],
        status=EpistemicStatus.VERIFIED,
        provenance=(
            "勺园＝米万钟园；1981 起兼指留学生楼群（恢复旧称）——"
            "「名承」非「园存」（负控制14），与明代园林不混指。"
        ),
    ),
    ReferentialAssertion(
        id="rr_hongya",
        appellation_id="app_hongya",
        referent_entity_id="ent_hongya_jixian",
        time_span=_ts(1662, 1801, "ts_r_hy"),
        evidence_fact_ids=["tf_hongya_1801"],
        status=EpistemicStatus.VERIFIED,
        provenance=(
            "1801 档案经恭博转引《会典事例》/实录系统（quoted_via，原件未直核）；"
            "「康熙赐积哈纳」句已删（E10）；园名异写洪/弘（乾隆诗注）。"
        ),
    ),
    ReferentialAssertion(
        id="rr_jixianyuan",
        appellation_id="app_jixianyuan",
        referent_entity_id="ent_hongya_jixian",
        time_span=_ts(1801, 1981, "ts_r_jxy"),
        evidence_fact_ids=["tf_xiaoting_jixianyuan", "tf_hongya_1801"],
        status=EpistemicStatus.VERIFIED,
        provenance="昭梿卷九直核（待核9关闭）；1981 后由勺园楼群「集贤厅」承接旧名。",
    ),
    ReferentialAssertion(
        id="rr_shuchun",
        appellation_id="app_shuchun",
        referent_entity_id="ent_shuchunyuan",
        time_span=_ts(1763, 1920, "ts_r_sc"),
        evidence_fact_ids=["tf_shuchun_shuitian_1763", "tf_yixuan_xu"],
        status=EpistemicStatus.CONTESTED,
        provenance=(
            "E01 争议建模：何瑜（故宫博物院院刊2021）把 1763 淑春园定位圆明园北部、"
            "判和珅园为其东邻十笏园；郝黎（恭王府博物馆2026-03-24）据奕譞/丰绅殷德"
            "主张和珅园很可能即名淑春园。两说均有清人材料，不判死。"
        ),
    ),
    ReferentialAssertion(
        id="rr_shihu",
        appellation_id="app_shihu",
        referent_entity_id="ent_shuchunyuan",
        time_span=_ts(1775, 1860, "ts_r_shihu"),
        evidence_fact_ids=["tf_xiaoting_shihu"],
        status=EpistemicStatus.VERIFIED,
        provenance=(
            "昭梿时人口径直核（待核9关闭）；与「勺園今改集賢院」分写两处——"
            "两链不同园的时人硬证。"
        ),
    ),
    ReferentialAssertion(
        id="rr_ruiwangyuan",
        appellation_id="app_ruiwangyuan",
        referent_entity_id="ent_shuchunyuan",
        time_span=_ts(1830, 1920, "ts_r_rwy"),
        evidence_fact_ids=["tf_yixuan_xu"],
        status=EpistemicStatus.VERIFIED,
        provenance="奕譞「後輾轉為睿邸園寓」＋清末民初地图睿王園/睿邸；「睿湖」湖名源此。",
    ),
    ReferentialAssertion(
        id="rr_weiminghu",
        appellation_id="app_weiminghu",
        referent_entity_id="ent_weiming_lake",
        time_span=_ts(1928, 2026, "ts_r_wmh"),
        evidence_fact_ids=["tf_weiminghu_1928"],
        status=EpistemicStatus.VERIFIED,
        provenance="1928-11 最早书面用例；1931 前后渐成公认；校方从未行政命名（E08/E09）。",
    ),
    ReferentialAssertion(
        id="rr_wuminghu",
        appellation_id="app_wuminghu",
        referent_entity_id="ent_weiming_lake",
        time_span=_ts(1929, 1931, "ts_r_wmh2"),
        evidence_fact_ids=["tf_lake_names_1929_31"],
        status=EpistemicStatus.VERIFIED,
        provenance="学生时代并用名；频次排序须含枫湖居首（E07）。",
    ),
    ReferentialAssertion(
        id="rr_ruihu",
        appellation_id="app_ruihu",
        referent_entity_id="ent_weiming_lake",
        time_span=_ts(1929, 1931, "ts_r_rh"),
        evidence_fact_ids=["tf_lake_names_1929_31"],
        status=EpistemicStatus.VERIFIED,
        provenance="睿王园遗名在学生时代的湖名留痕。",
    ),
    ReferentialAssertion(
        id="rr_fenghu",
        appellation_id="app_fenghu",
        referent_entity_id="ent_weiming_lake",
        time_span=_ts(1929, 1931, "ts_r_fh"),
        evidence_fact_ids=["tf_lake_names_1929_31"],
        status=EpistemicStatus.VERIFIED,
        provenance="E07：校友网燕大报刊统计频次第一名——画频次图必须含此名。",
    ),
    ReferentialAssertion(
        id="rr_shifang",
        appellation_id="app_shifang",
        referent_entity_id="ent_shifang_base",
        time_span=_ts(1775, 2026, "ts_r_sf"),
        evidence_fact_ids=["tf_yixuan_xu"],
        status=EpistemicStatus.VERIFIED,
        provenance="奕譞咏《石舫》证清中后期尚存；今存残基；「石舫＝罪证」说法见负控制2。",
    ),
    ReferentialAssertion(
        id="rr_guobao",
        appellation_id="app_guobao",
        referent_entity_id="ent_yanjing_campus",
        time_span=_ts(2001, 2026, "ts_r_gb"),
        evidence_fact_ids=["tf_guobao_5475"],
        status=EpistemicStatus.VERIFIED,
        provenance=(
            "国发〔2001〕25号第五批，编号 5-475；市保前身＝1990「原燕京大学未名湖區」。"
        ),
    ),
]
