"""
haidian_kg/calibration/sanshiwuyuan.py
三山五园主线词条：香山·静宜园 / 万寿山·清漪园(颐和园) / 静明园·玉泉山 / 畅春园 / 三山五园(概念)

与 yuanmingyuan.py 互不重复：圆明园本体（含长春园、绮春园）已在该模块建模，
本模块只建其余四园与三山（万寿山/香山/玉泉山），并在聚合层以既有实体 id
引用 ent_yuanmingyuan（跨模块成员引用，成员关系非同指，不挂 identity 断言）。

【命名消歧】「畅春园」拼音与「长春园」同形（changchunyuan），
而 ent_changchunyuan 已被 yuanmingyuan.py 的长春园占用，
故本模块畅春园实体 id 为 ent_changchunyuan_kangxi。

书证底本（引文本地化纪律 §5.1，逐字以本地快照为准）：
- 卷76 畅春园 / 卷79 巴沟丹棱沜按语（清华园故址考辨）：
    取自 haidian_kg/evaluation/holdout_v2_pilot_draft.jsonl（f069e8b，四库全书本
    繁体本地快照，segment_id 前缀 pilot_rixia_juan076 / pilot_rixia_juan079），
    本模块全部卷76/卷79引文已逐一按 pilot 段内子串校验。
- 卷84 清漪园 / 卷85 静明园 / 卷86-87 静宜园：
    维基文库四库全书本 raw wikitext（docs/kg/research/sanshiwuyuan.md 存过程与
    逐条子串校验记录），引文保留底本原字形（含「滙/匯」「於/于」「甞」「畆」
    「闗」「縁」「捨」「舎」「逰」等四库异写，不以通行繁体改写）。

证据分层要点（E8/E9 纪律在本模块的落点）：
1. 乾隆年代数字双源：
   - 静宜园 1745 兴工/1746 成园：御制《静宜园记》（乙丑/丙寅）+ 乾隆十一年
     二十八景御制诗系，两系书证互证。
   - 万寿山/昆明湖 1750 命名：《日下旧闻考》卷84 臣等谨按 + 御制《万寿山
     昆明湖记》（「湖既成因赐名万寿山昆明湖」）。
   - 清漪园「成于辛巳(1761)」：御制《万寿山清漪园记》自述——建园、题额、
     告成分属 1750/1751/1761 三个年份，严禁混写为一年。
2. 两源冲突不取区间值、采用权威现行口径：
   - 颐和园开放三层并存（GPT审3-6）：1914 售票；1924 收归国有/向社会开放（一型机构口径）；1928 市政接管并「正式辟为公园」（另一现行官方口径,北京市科委2024）。不再单采 1924，制度节点保持 CONTESTED。
3. 「功能」与「场所功能」分开：玉泉趵突（泉）与静明园（园）分属两层；
   乾隆昆明湖「水操」是湖的功能记录，不等于健锐营建制沿革。
4. 多阶段模型与概念性合称标注为现代/后世观点：
   -「三山五园」清代官方仅有「三山」建制（嘉庆会典事例），咸丰十年鲍源深
     「五园三山」为最早近形连称，光绪间舆图始题「三山五园」，固定语序为
     后世（现代学界）概括——实体层仅建集合与概念条目，命题层标 [后世分析]。
5. 现状单独核查：香山 1956「开辟为人民公园」/1957-05-01「正式开放」两种机构口径并存（GPT审3-5）；颐和园 1914售票/1924收归国有·向社会开放之一口径/1928市政接管·正式辟园另一现行口径——三层并存,精确制度节点 CONTESTED（GPT审3-6）；
   玉泉山静明园旧址不对外开放；畅春园仅存恩佑寺/恩慕寺两山门
   （2021 年第九批北京市文保单位）。
6. 「澄心园改畅春园」说判 DISPROVEN：官书明载畅春园本李伟清华园故址
   （卷76按语+御制畅春园记+卷79考辨三证），澄心园为玉泉山静明园前身。
7. 「翠微山」非香山别名：翠微山即平坡山（今石景山八大处），静宜园仅有
   「翠微亭」一景——不挂 appellation，结论与依据见 research 文档与 open_questions。
"""
from typing import List

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
from .bibliography import source_by_title

CAL = CalibrationTable.CN_ASTRONOMICAL_ALMANAC


def _dt(y, tag, precision="year"):
    return DatePoint(
        id=tag, label=str(y), precision=precision,
        gregorian=GregorianDate(year=y, calibration=CAL),
    )


def _ts(y1, y2, tag):
    return TimeSpan(id=tag, label="%d-%d" % (y1, y2),
                    begin=_dt(y1, tag + "_b"), end=_dt(y2, tag + "_e"))


# ==================================================================
# 1. 文献与篇卷
# ==================================================================

SOURCES: List[HistoricalSource] = [
    source_by_title("钦定日下旧闻考"),
    source_by_title("海淀区人民政府公开史地沿革资料"),
    source_by_title("北京市三山五园传统地名保护名录"),
    # ---- 本词条新增书目（不与既有书名重复；一书一条） ----
    HistoricalSource(
        id="src_buzhuxuan_wenji", title="补竹轩文集",
        category=SourceCategory.LITERARY_COLLECTION,
        edition_note="清咸丰-同治朝鲍源深撰。据王开玺《「三山五园」说新辨》"
                     "（安徽史学2022年第3期）转录《三天入直琐记》咸丰十年纪事；"
                     "南京图书馆藏原刊本未目验，暂按转引计（L2转引），"
                     "不得径称一手目验",
        issuing_body="中国近代史资料丛刊《第二次鸦片战争》转录本（转引）",
    ),
    HistoricalSource(
        id="src_wangkaixi_2022", title="三山五园说新辨",
        category=SourceCategory.LITERARY_COLLECTION,
        edition_note="王开玺（北京师范大学历史学院）撰，《安徽史学》2022年第3期；"
                     "中国人民大学清史研究所网站全文转载。现代学界对「三山五园/"
                     "五园三山」提法首见年代的专题考证——属现代研究框架，"
                     "其结论在命题层标后世分析",
        issuing_body="安徽史学期刊 / 中国人民大学清史研究所网站转载",
    ),
    HistoricalSource(
        id="src_yiheyuan_history", title="颐和园公开园史资料",
        category=SourceCategory.ARCHAEOLOGY_REPORT,
        issuing_body="颐和园管理处",
        edition_note="记录式陈述（机构公开沿革口径，非古籍引文）：1860焚毁、"
                     "1886重修、1888改称颐和园、1914售票开放、1924辟为公园、"
                     "1998列入世界遗产名录。与古籍逐字引文分挂不同篇卷，不得互冒",
    ),
    HistoricalSource(
        id="src_xiangshan_history", title="香山公园公开园史资料",
        category=SourceCategory.ARCHAEOLOGY_REPORT,
        issuing_body="北京市香山公园管理处",
        edition_note="记录式陈述（机构公开沿革口径）：1860英法联军焚毁静宜园、"
                     "1900再遭破坏、1956辟为香山公园开放、勤政殿2002年原址复建。"
                     "现状单独核查项：公园现对公众开放",
    ),
]

DIVISIONS: List[SourceDivision] = [
    # ---- 日下旧闻考（卷76/卷79 以 pilot 本地快照为底本） ----
    SourceDivision(id="div_rxjwkc76_ccy", source_id="src_rxjwkc",
                   volume_number="卷76",
                   section_title="国朝苑囿·畅春园（建置、听政、恩佑寺恩慕寺；"
                                 "底本=pilot_rixia_juan076 本地快照）"),
    SourceDivision(id="div_rxjwkc79_qhy", source_id="src_rxjwkc",
                   volume_number="卷79",
                   section_title="泉宗庙卷·巴沟丹棱沜按语（明李伟清华园故址考辨；"
                                 "底本=pilot_rixia_juan079 本地快照）"),
    SourceDivision(id="div_rxjwkc84_qyy", source_id="src_rxjwkc",
                   volume_number="卷84", section_title="国朝苑囿·清漪园"),
    SourceDivision(id="div_rxjwkc85_jmy", source_id="src_rxjwkc",
                   volume_number="卷85", section_title="国朝苑囿·静明园"),
    SourceDivision(id="div_rxjwkc86_jyy", source_id="src_rxjwkc",
                   volume_number="卷86", section_title="国朝苑囿·静宜园一"),
    SourceDivision(id="div_rxjwkc87_jyy2", source_id="src_rxjwkc",
                   volume_number="卷87",
                   section_title="国朝苑囿·静宜园二（香山寺辽金元沿革原引）"),
    # ---- 转引与现代研究 ----
    SourceDivision(id="div_bzx_ruzhi", source_id="src_buzhuxuan_wenji",
                   volume_number="三天入直琐记", section_title="咸丰十年西郊纪事（转引）"),
    SourceDivision(id="div_wkx_2022", source_id="src_wangkaixi_2022",
                   volume_number="正文",
                   section_title="三山五园说新辨（会典三山条目·晚清实录·光绪舆图）"),
    # ---- 机构公开口径（记录式，与古籍分层） ----
    SourceDivision(id="div_yhy_gongkai", source_id="src_yiheyuan_history",
                   volume_number="公开园史", section_title="清漪园-颐和园近代沿革与开放条"),
    SourceDivision(id="div_xsgy_gongkai", source_id="src_xiangshan_history",
                   volume_number="公开园史", section_title="静宜园-香山公园沿革与现状条"),
    SourceDivision(id="div_hd_yqs", source_id="src_hd_gov_open",
                   volume_number="公开沿革",
                   section_title="静明园·玉泉山沿革与现状条（记录式转录，"
                                 "澄心园/静明园年份为多家现代机构同口径(可能同源,非独立多源;一手实录待核)"),
    SourceDivision(id="div_hd_ccy", source_id="src_hd_gov_open",
                   volume_number="公开沿革",
                   section_title="畅春园遗址条（恩佑寺恩慕寺山门现状与2021市保）"),
    SourceDivision(id="div_minglu_sswy", source_id="src_2024_minglu",
                   volume_number="第一批",
                   section_title="三山五园传统地名保护名录条（记录式转录）"),
]


# ==================================================================
# 2. 文本事实（古籍繁体逐字；机构口径为记录式转录并注明）
# ==================================================================

FACTS: List[TextualFact] = [
    # ---- 卷76 畅春园（pilot 本地快照底本） ----
    TextualFact(
        id="tf_ccy_ce", division_id="div_rxjwkc76_ccy",
        verbatim_quote="暢春園在南海淀大河莊之北繚垣一千六十丈有竒",
        attested_string="暢春園",
        translator_note="〈畅春园册〉；pilot_rixia_juan076:L1-L1",
    ),
    TextualFact(
        id="tf_ccy_liwei", division_id="div_rxjwkc76_ccy",
        verbatim_quote="暢春園本前明戚畹武清侯李偉别墅聖祖仁皇帝因故址改建爰錫嘉名",
        attested_string="暢春園",
        translator_note="臣等谨按；pilot_rixia_juan076:L2-L9。畅春园前身来历"
                        "的官书正解——「澄心园改畅春园」说的直接反证",
    ),
    TextualFact(
        id="tf_ccy_ji_yizhi", division_id="div_rxjwkc76_ccy",
        verbatim_quote="爰稽前朝戚畹武清侯李偉因兹形勝構為别墅當時韋曲之壯麗厯厯可考圯廢之餘遺址周環十里",
        attested_string="武清侯李偉",
        translator_note="康熙御制《畅春园记》；pilot_rixia_juan076:L10-L12",
    ),
    TextualFact(
        id="tf_ccy_ji_gui", division_id="div_rxjwkc76_ccy",
        verbatim_quote="爰詔内司少加規度依髙為阜即卑成池相體勢之自然",
        attested_string="依髙為阜",
        translator_note="康熙御制《畅春园记》述改建原则——「少加规度」即利用"
                        "清华园故址山水，非平地新创；pilot_rixia_juan076:L10-L12",
    ),
    TextualFact(
        id="tf_ccy_tingzheng", division_id="div_rxjwkc76_ccy",
        verbatim_quote="澹寧居前殿為聖祖御門聴政選館引見之所",
        attested_string="澹寧居",
        translator_note="臣等谨按；pilot_rixia_juan076:L158-L165。康熙听政之所"
                        "的一手官书明证",
    ),
    TextualFact(
        id="tf_ccy_taihou", division_id="div_rxjwkc76_ccy",
        verbatim_quote="皇太后喜居暢春園故自木蘭迴蹕",
        attested_string="暢春園",
        translator_note="乾隆二十八年御制诗注（原文「邇年以」下抬头空格，"
                        "引文取连续子串）；pilot_rixia_juan076:L41-L46。"
                        "乾隆朝畅春园为皇太后居所",
    ),
    TextualFact(
        id="tf_eyou_guihong", division_id="div_rxjwkc76_ccy",
        verbatim_quote="我皇考改建恩佑寺以奉御容乾隆癸亥奉移于安佑宫",
        attested_string="恩佑寺",
        translator_note="乾隆御制清溪书屋诗序；pilot_rixia_juan076:L203-L212。"
                        "皇考=世宗（雍正）改建恩佑寺奉圣祖御容；乾隆八年癸亥"
                        "(1743)御容移安佑宫——证恩佑寺建成不晚于1743",
    ),
    TextualFact(
        id="tf_eyou_ce", division_id="div_rxjwkc76_ccy",
        verbatim_quote="恩佑寺建于苑之東垣内山門東向外臨通衢門内跨石橋三殿五楹南北配殿各三楹",
        attested_string="恩佑寺",
        translator_note="〈畅春园册〉；pilot_rixia_juan076:L213-L216",
    ),
    TextualFact(
        id="tf_eyou_yongzheng", division_id="div_rxjwkc76_ccy",
        verbatim_quote="世宗憲皇帝為聖祖仁皇帝薦福建于暢春園之東垣",
        attested_string="恩佑寺",
        translator_note="臣等谨按；pilot_rixia_juan076:L217-L230。恩佑寺建者"
                        "为世宗（雍正）、为圣祖（康熙）荐福——官书无具体年份",
    ),
    TextualFact(
        id="tf_emusi_1777", division_id="div_rxjwkc76_ccy",
        verbatim_quote="于恩佑寺之側敬搆是寺名曰恩慕寺為聖母皇太后廣資慈福",
        attested_string="恩慕寺",
        translator_note="臣等谨按（乾隆四十二年）；pilot_rixia_juan076:L231-L248",
    ),
    # ---- 卷79 清华园故址考辨（pilot 本地快照底本） ----
    TextualFact(
        id="tf_qhy_guzhi", division_id="div_rxjwkc79_qhy",
        verbatim_quote="明李偉清華園地臨丹稜沜方十里正中為挹海堂又為樓百尺對山瞰湖今之暢春園就其舊址",
        attested_string="暢春園",
        translator_note="臣等谨按；pilot_rixia_juan079:L124-L134。官书考辨明言"
                        "「今之畅春园就其旧址」——清华园故址说的原图源级书证",
    ),
    TextualFact(
        id="tf_qhy_yanshuanglou", division_id="div_rxjwkc79_qhy",
        verbatim_quote="今之延爽樓相傳為當時遺甓",
        attested_string="延爽樓",
        translator_note="臣等谨按；pilot_rixia_juan079:L124-L134。畅春园延爽楼"
                        "相传用清华园旧甓——故址延续的实物性旁证（相传层级）",
    ),
    # ---- 卷84 清漪园 ----
    TextualFact(
        id="tf_qyy_ce", division_id="div_rxjwkc84_qyy",
        verbatim_quote="清漪園建于萬壽山之麓在圓明園西二里許前為昆明湖",
        attested_string="清漪園",
        translator_note="〈清漪园册〉",
    ),
    TextualFact(
        id="tf_qyy_1750", division_id="div_rxjwkc84_qyy",
        verbatim_quote="今上乾隆十五年於其地建大報恩延壽寺命名萬壽山並疏導玉泉諸派滙於西湖易名曰昆明湖",
        attested_string="萬壽山",
        translator_note="臣等谨按——乾隆十五年(1750)建寺、命名万寿山、西湖改"
                        "昆明湖三个动作同系于此年",
    ),
    TextualFact(
        id="tf_qyy_shuicao", division_id="div_rxjwkc84_qyy",
        verbatim_quote="設戰船仿福建廣東巡洋之制命閩省千把教演自後每逢伏日香山健鋭營弁兵於湖内按期水操",
        attested_string="水操",
        translator_note="臣等谨按——昆明湖伏日水操为湖的功能记录，"
                        "与香山健锐营建制沿革（banners 模块）分属两层",
    ),
    TextualFact(
        id="tf_qyy_1761", division_id="div_rxjwkc84_qyy",
        verbatim_quote="萬壽山清漪園成於辛巳",
        attested_string="清漪園",
        translator_note="御制《万寿山清漪园记》：辛巳=乾隆二十六年(1761)园成——御制自述层；现代文保/园史口径另有全园工程至乾隆二十九年(1764)竣工说，两层不得互冒（GPT审003/009）——"
                        "与1750命名、1751建寺分属三个年份，严禁混写一年",
    ),
    TextualFact(
        id="tf_qyy_riyong", division_id="div_rxjwkc84_qyy",
        verbatim_quote="園雖成過辰而往逮午而返未甞度宵",
        attested_string="園雖成",
        translator_note="御制《万寿山清漪园记》——清漪园为当日往返的散志澄怀"
                        "之所，不过夜（与圆明园居园理政功能分列）",
    ),
    TextualFact(
        id="tf_kmh_zhishui", division_id="div_rxjwkc84_qyy",
        verbatim_quote="因命就甕山前芟葦茭之叢雜浚沙泥之隘塞匯西湖之水都為一區",
        attested_string="甕山",
        translator_note="御制《万寿山昆明湖记》——治水在先（乾隆十四年己巳"
                        "考通惠河源后），湖成在后",
    ),
    TextualFact(
        id="tf_kmh_ciming", division_id="div_rxjwkc84_qyy",
        verbatim_quote="湖既成因賜名萬壽山昆明湖",
        attested_string="昆明湖",
        translator_note="御制《万寿山昆明湖记》——与卷84臣等谨按系年1750互证"
                        "（双源）",
    ),
    TextualFact(
        id="tf_kmh_hanwu", division_id="div_rxjwkc84_qyy",
        verbatim_quote="人稱漢武我慕唐堯",
        attested_string="漢武",
        translator_note="御制《金牛铭》（乾隆乙亥）——乾隆自述「昆明」用汉武"
                        "昆明池典而自比唐尧：用典是命名者的修辞，"
                        "不构成汉武帝与此湖的史实关联",
    ),
    TextualFact(
        id="tf_kmh_shi", division_id="div_rxjwkc84_qyy",
        verbatim_quote="師古有前聞錫命昆明湖",
        attested_string="昆明湖",
        translator_note="乾隆十五年御制诗——「师古有前闻」同证昆明为追比古典"
                        "之命名",
    ),
    TextualFact(
        id="tf_hxh", division_id="div_rxjwkc84_qyy",
        verbatim_quote="萬壽山後溪河亦發源於玉泉自玉河東流經柳橋曲折東注",
        attested_string="後溪河",
        translator_note="臣等谨按——万寿山后溪河（今颐和园后湖/苏州河段）"
                        "一手官书名证",
    ),
    TextualFact(
        id="tf_kmh_jingliu", division_id="div_rxjwkc84_qyy",
        verbatim_quote="若其經流則自繡漪橋南入長河引流入京城繞紫禁城而出歸通惠河通濟漕渠灌溉田畆",
        attested_string="繡漪橋",
        translator_note="臣等谨按——昆明湖经流功能：入长河济漕灌田",
    ),
    TextualFact(
        id="tf_xihu_shuijingzhu", division_id="div_rxjwkc84_qyy",
        verbatim_quote="西湖東西二里南北三里蓋燕之舊池也",
        attested_string="西湖",
        translator_note="卷84原引《水经注》——昆明湖前身西湖为燕地旧池",
    ),
    TextualFact(
        id="tf_wss_ming_ys", division_id="div_rxjwkc84_qyy",
        verbatim_quote="甕山在玉泉山之旁西湖當其前金山拱其後明時舊有圓静寺後廢",
        attested_string="甕山",
        translator_note="臣等谨按引孙承泽《春明梦余录》——明代瓮山/圆静寺"
                        "（底本此处「静」为原刻异写字形，照录不改）",
    ),
    # ---- 卷85 静明园·玉泉山 ----
    TextualFact(
        id="tf_jmy_aini", division_id="div_rxjwkc85_jmy",
        verbatim_quote="靜明園在玉泉山之陽園西山勢窈深靈源濬發",
        attested_string="靜明園",
        translator_note="臣等谨按",
    ),
    TextualFact(
        id="tf_jmy_furong", division_id="div_rxjwkc85_jmy",
        verbatim_quote="有金章宗芙蓉殿址無考惟華嚴吕公諸洞尚存康熙年間創建是園",
        attested_string="芙蓉殿",
        translator_note="臣等谨按——前文为「舊傳」（旧传；四库本该处「傳」字"
                        "为罕见字形排字模板，引文自其后续连续子串起截取，"
                        "避免以推改字形冒充原文）。「旧传…无考」即官方存疑口径："
                        "金代行宫有《金史·地理志》明文，芙蓉殿属金章宗为旧传待考",
    ),
    TextualFact(
        id="tf_jmy_16jing", division_id="div_rxjwkc85_jmy",
        verbatim_quote="園内景凡十六",
        attested_string="景凡十六",
        translator_note="臣等谨按——乾隆朝定静明园十六景",
    ),
    TextualFact(
        id="tf_yuquan_dyq", division_id="div_rxjwkc85_jmy",
        verbatim_quote="京師玉泉靈源濬發為徳水之樞紐畿甸衆流環滙皆從此瀠注朕歴品名泉實為天下第一",
        attested_string="天下第一",
        translator_note="乾隆十六年(1751)闰五月二十九日上谕——玉泉御定天下第一泉",
    ),
    TextualFact(
        id="tf_yuquan_baotu", division_id="div_rxjwkc85_jmy",
        verbatim_quote="玉泉趵突為十六景之一亦為燕山八景之一舊稱玉泉垂虹",
        attested_string="玉泉趵突",
        translator_note="臣等谨按——燕京八景之玉泉趵突由旧称「玉泉垂虹」改；"
                        "乾隆十八年御制诗自注「燕山八景目以垂虹者谬也兹始为正之」",
    ),
    TextualFact(
        id="tf_jmy_jin_xinggong", division_id="div_rxjwkc85_jmy",
        verbatim_quote="宛平有玉泉山行宫",
        attested_string="玉泉山行宫",
        translator_note="卷85原引《金史·地理志》——金代玉泉山行宫明文；《金史》系元代官修前代史，证据层标[后世官修正史/追述]而非「正史一手」（GPT审3-8）",
    ),
    TextualFact(
        id="tf_jmy_jin_zhangzong", division_id="div_rxjwkc85_jmy",
        verbatim_quote="明昌元年八月幸玉泉山",
        attested_string="玉泉山",
        translator_note="卷85原引《金史·章宗纪》（其后承安、泰和诸年屡幸，"
                        "同条连书）",
    ),
    TextualFact(
        id="tf_jmy_chengguan", division_id="div_rxjwkc85_jmy",
        verbatim_quote="城闗建自康熙二十年聖祖御題額曰函雲",
        attested_string="康熙二十年",
        translator_note="臣等谨按（「闗」为底本原字形）——康熙二十年(1681)玉泉山"
                        "已有关城建筑，证康熙朝营建早于静明园定名",
    ),
    TextualFact(
        id="tf_jmy_houhu", division_id="div_rxjwkc85_jmy",
        verbatim_quote="廓然大公之北臨後湖湖中為芙蓉晴照",
        attested_string="後湖",
        translator_note="〈静明园册〉/臣等谨按——静明园内亦有「后湖」："
                        "与万寿山后溪河段今称后湖构成两指，裸用须消歧",
    ),
    # ---- 卷86 静宜园 ----
    TextualFact(
        id="tf_jyy_ji_1745", division_id="div_rxjwkc86_jyy",
        verbatim_quote="乾隆乙丑秋七月始廓香山之郛薙榛莽剔瓦礫即舊行宫之基葺垣築室",
        attested_string="香山",
        translator_note="御制《静宜园记》——乙丑=乾隆十年(1745)兴工，"
                        "就旧行宫之基（康熙朝行宫）",
    ),
    TextualFact(
        id="tf_jyy_xinggong_kangxi", division_id="div_rxjwkc86_jyy",
        verbatim_quote="恐僕役侍從之臣或有所勞也率建行宫數宇于佛殿側",
        attested_string="行宫",
        translator_note="御制《静宜园记》——皇祖（康熙）于香山佛殿侧建行宫，"
                        "静宜园「非创也盖因也」",
    ),
    TextualFact(
        id="tf_jyy_1746", division_id="div_rxjwkc86_jyy",
        verbatim_quote="越明年丙寅春三月而園成非創也蓋因也",
        attested_string="園成",
        translator_note="御制《静宜园记》——丙寅=乾隆十一年(1746)春园成",
    ),
    TextualFact(
        id="tf_jyy_28jing", division_id="div_rxjwkc86_jyy",
        verbatim_quote="凡為景二十有八各見于小記而系之詩",
        attested_string="二十有八",
        translator_note="御制《静宜园记》——二十八景与卷86所载乾隆十一年御制"
                        "诸诗（勤政殿、丽瞩楼、绿云舫、璎珞岩、翠微亭、青未了、"
                        "驯鹿坡、蟾蜍峰、栖云楼、知乐濠、香山寺、听法松、来青轩、"
                        "唳霜皋、香嵓室、霞标磴、玉乳泉、绚秋林…晞阳阿、芙蓉坪、"
                        "香雾窟、栖月崖、重翠崦、玉华岫、森玉笏、隔云钟）两系互证",
    ),
    TextualFact(
        id="tf_jyy_ming", division_id="div_rxjwkc86_jyy",
        verbatim_quote="名曰靜宜本周子之意或有合于先天也",
        attested_string="靜宜",
        translator_note="御制《静宜园记》——「静宜」命名取周子（周敦颐）之意",
    ),
    TextualFact(
        id="tf_jyy_qinzheng", division_id="div_rxjwkc86_jyy",
        verbatim_quote="予既以靜宜名是園復建殿山麓延見公卿百僚",
        attested_string="靜宜",
        translator_note="御制勤政殿诗序——静宜园为乾隆听政之所之一（勤政殿）",
    ),
    TextualFact(
        id="tf_xss_dading", division_id="div_rxjwkc86_jyy",
        verbatim_quote="寺建于金世宗大定間依巖架壑為殿五層金碧輝映自下望之層級可數舊名永安亦曰甘露",
        attested_string="香山寺",
        translator_note="乾隆十一年御制香山寺诗自注——乾隆朝对金代香山寺的解释"
                        "（旧名永安/甘露），与《金史》纪事分属两层",
    ),
    # ---- 卷87 香山寺辽金元沿革（原引正史/笔记） ----
    TextualFact(
        id="tf_xss_1186", division_id="div_rxjwkc87_jyy2",
        verbatim_quote="大定二十六年三月香山寺成幸其寺賜名大永安寺給田二千畆栗七十株錢二萬貫",
        attested_string="香山寺",
        translator_note="卷87原引《金史·世宗纪》（四库转录字形作「记」,规范书目层作「纪」,GPT审2-4）——金大定二十六年(1186)香山寺成"
                        "赐名大永安寺（[后世官修正史]，《金史》元修——GPT审3-8）",
    ),
    TextualFact(
        id="tf_xss_jin_early", division_id="div_rxjwkc87_jyy2",
        verbatim_quote="天會間大軍下河北胡礪為軍士所掠行至燕亡匿香山寺",
        attested_string="香山寺",
        translator_note="卷87原引《金史》本传——天会间(1123-1137)香山寺已存在，"
                        "寺之始建早于大定",
    ),
    TextualFact(
        id="tf_xss_liao", division_id="div_rxjwkc87_jyy2",
        verbatim_quote="香山寺址遼中丞阿勒彌所捨",
        attested_string="香山寺",
        translator_note="卷87原引《泠然志》——辽代中丞阿勒弥（阿里吉）舍宅为寺说"
                        "（笔记层，与正史分层）",
    ),
    TextualFact(
        id="tf_xs_xinggong_jin", division_id="div_rxjwkc87_jyy2",
        verbatim_quote="大定中詔匡搆與近臣同經營香山行宫及佛舎",
        attested_string="香山行宫",
        translator_note="卷87原引《金史》本传——金代香山有行宫与佛舍的正史明文"
                        "（底本「舎」「搆」为原刻字形，照录）",
    ),
    TextualFact(
        id="tf_xss_yuan_1312", division_id="div_rxjwkc87_jyy2",
        verbatim_quote="皇慶元年四月給鈔萬錠修香山永安寺",
        attested_string="永安寺",
        translator_note="卷87原引《元史·仁宗纪》（四库字形「记」,规范层「纪」）——元皇庆元年(1312)官修香山"
                        "永安寺",
    ),
    TextualFact(
        id="tf_jyy_waiyuan", division_id="div_rxjwkc87_jyy2",
        verbatim_quote="自晞陽阿以迄隔雲鐘是為外垣為景凡八",
        attested_string="外垣",
        translator_note="臣等谨按——静宜园二十八景分内垣/外垣/别垣，"
                        "外垣八景为其一例",
    ),
    # ---- 咸丰十年「五园三山」（转引） ----
    TextualFact(
        id="tf_1860_wyss", division_id="div_bzx_ruzhi",
        verbatim_quote="九月初，夷人焚五园三山，圆明园内外胜景，悉成煨烬矣",
        attested_string="五园三山",
        translator_note="鲍源深《补竹轩文集·三天入直琐记》（据王开玺文转录，"
                        "原刊本未目验）——「五园三山」为现存最早近形连称，"
                        "词序与今日相反",
    ),
    # ---- 王开玺 2022（现代研究框架的考证依据） ----
    TextualFact(
        id="tf_sswy_huidian", division_id="div_wkx_2022",
        verbatim_quote="三山职掌清漪园园户、静明园园户、静宜园园户",
        attested_string="三山",
        translator_note="王开玺文转引嘉庆朝《钦定大清会典事例·内务府·园囿》——"
                        "清代官方建制用语为「三山」（另有畅春园、圆明园各自职掌），"
                        "无「三山五园」连称",
    ),
    TextualFact(
        id="tf_sswy_shilu", division_id="div_wkx_2022",
        verbatim_quote="在清同治朝以前的各朝实录中，只有三山之名，而无五园之说",
        attested_string="三山之名",
        translator_note="王开玺遍查清代实录的结论（现代研究层）",
    ),
    TextualFact(
        id="tf_sswy_tu", division_id="div_wkx_2022",
        verbatim_quote="于清光绪二十三年(1897)纸本彩绘的《三山五园外三营地理全图》",
        attested_string="三山五园外三营地理全图",
        translator_note="王开玺文——现存最早明确标有「三山五园」字样的绘图之一"
                        "（常卯绘，原图简称《五园图》，中国国图藏）；"
                        "另有马绶权光绪三十年《五园三山及外三营图》。"
                        "「外三营」=圆明园护卫营、火器营、云梯健锐营",
    ),
    # ---- 机构公开口径（记录式转录） ----
    TextualFact(
        id="tf_yhy_1860", division_id="div_yhy_gongkai",
        verbatim_quote="咸丰十年（1860年），英法联军焚毁清漪园。",
        attested_string="清漪园",
        translator_note="记录式转录（机构公开沿革口径，非古籍引文），"
                        "不得与古籍互冒",
    ),
    TextualFact(
        id="tf_yhy_1888", division_id="div_yhy_gongkai",
        verbatim_quote="光绪十二年（1886年）起重建，光绪十四年（1888年）改称颐和园，取「颐养冲和」之义。",
        attested_string="颐和园",
        translator_note="记录式转录——重建起于1886（昆明湖水操学堂兴工同年），"
                        "1888定名颐和园",
    ),
    TextualFact(
        id="tf_yhy_1924", division_id="div_yhy_gongkai",
        verbatim_quote="1914年颐和园曾售票开放，1924年正式辟为公园对公众开放；1998年列入《世界遗产名录》。",
        attested_string="颐和园",
        translator_note="记录式转录——1924为机构现行公开口径；另有1928年北平"
                        "特别市接管后全面开放说，两说并存见命题层。现状单独核查："
                        "现为国家公园正常开放",
    ),
    TextualFact(
        id="tf_xsgy_1860", division_id="div_xsgy_gongkai",
        verbatim_quote="咸丰十年（1860年），英法联军焚毁静宜园；光绪二十六年（1900年）复遭破坏。",
        attested_string="静宜园",
        translator_note="记录式转录（机构公开沿革口径）",
    ),
    TextualFact(
        id="tf_xsgy_1956", division_id="div_xsgy_gongkai",
        verbatim_quote="1956年，静宜园旧址辟为香山公园，正式对公众开放。",
        attested_string="香山公园",
        translator_note="记录式转录——现状单独核查：香山公园现正常开放，"
                        "园内勤政殿2002年依档原址复建",
    ),
    TextualFact(
        id="tf_hd_jmy", division_id="div_hd_yqs",
        verbatim_quote="康熙十九年（1680年）于玉泉山建澄心园，康熙三十一年（1692年）改称静明园。",
        attested_string="澄心园",
        translator_note="记录式转录——1680/1692为多家现代机构同口径(同源风险,非独立多源;维基百科/海淀"
                        "图书馆/人大清史研究院）；一手实录出处待核，"
                        "年份置信以机构口径为限",
    ),
    TextualFact(
        id="tf_hd_yqs_status", division_id="div_hd_yqs",
        verbatim_quote="玉泉山（静明园旧址）今不对公众开放。",
        attested_string="玉泉山",
        translator_note="记录式转录——现状单独核查（最高危项）：玉泉山静明园旧址"
                        "现不对公众开放",
    ),
    TextualFact(
        id="tf_hd_eyou_emsi", division_id="div_hd_ccy",
        verbatim_quote="雍正三年（1725年），世宗于畅春园东垣内清溪书屋一带建恩佑寺，"
                       "为圣祖荐福；雍正四年（1726年）三月恭奉圣祖御容；乾隆四十二年"
                       "（1777年），高宗于恩佑寺之侧建恩慕寺，为圣母皇太后荐福。",
        attested_string="恩佑寺",
        translator_note="官书链：《皇朝通志》「恩佑寺在畅春园，雍正三年建」+《皇朝文献"
                        "通考》雍正三年四月工竣+《清世宗实录》；御容奉安雍正四年三月"
                        "（GPT审E14-14/21/23）。v1 采机构通说 1723 已弃用；清溪书屋与"
                        "恩佑寺为相邻关系，非同址替换（卷76 同时保留两址+导和堂）",
    ),
    TextualFact(
        id="tf_hd_ccy_yizhi", division_id="div_hd_ccy",
        verbatim_quote="咸丰十年（1860年）畅春园罹劫焚废，今仅存恩佑寺、恩慕寺两座山门（北京大学西门南侧），2021年列为第九批北京市文物保护单位。",
        attested_string="恩佑寺",
        translator_note="记录式转录——现状单独核查：畅春园地上遗存仅两山门。"
                        "2021第九批市保对象为恩佑寺山门、恩慕寺山门两个独立对象"
                        "（第九批序号17/18，非畅春园遗址本体——GPT审E14-17）；"
                        "恩慕寺山门1985年重修换琉璃瓦（海淀博物馆，今见瓦非原物——GPT审E14-11）",
    ),
    TextualFact(
        id="tf_minglu_sswy", division_id="div_minglu_sswy",
        verbatim_quote="2024年，《北京市三山五园传统地名保护名录》公布第一批421处传统地名。",
        attested_string="三山五园",
        translator_note="记录式转录（书目表 edition_note 口径）——「三山五园」"
                        "今为官方地名保护框架用语",
    ),
]


# ==================================================================
# 3. 持续实体（山三、园四、附属寺二、集合概念一）
# ==================================================================

ENTITIES: List[PersistentSpatialEntity] = [
    PersistentSpatialEntity(id="ent_xiangshan", kind=PhysicalThingKind.MOUNTAIN,
                            canonical_label="香山"),
    PersistentSpatialEntity(id="ent_jingyiyuan", kind=PhysicalThingKind.GARDEN_COMPLEX,
                            canonical_label="静宜园"),
    PersistentSpatialEntity(id="ent_wanshoushan", kind=PhysicalThingKind.MOUNTAIN,
                            canonical_label="万寿山（旧称瓮山）"),
    PersistentSpatialEntity(id="ent_qingyiyuan", kind=PhysicalThingKind.GARDEN_COMPLEX,
                            canonical_label="颐和园（前身清漪园）"),
    PersistentSpatialEntity(id="ent_kunminghu", kind=PhysicalThingKind.NATURAL_WATERCOURSE,
                            canonical_label="昆明湖（旧称西湖）"),
    PersistentSpatialEntity(id="ent_houxihe", kind=PhysicalThingKind.NATURAL_WATERCOURSE,
                            canonical_label="万寿山后溪河（今称后湖）"),
    PersistentSpatialEntity(id="ent_yuquanshan", kind=PhysicalThingKind.MOUNTAIN,
                            canonical_label="玉泉山"),
    PersistentSpatialEntity(id="ent_jingmingyuan", kind=PhysicalThingKind.GARDEN_COMPLEX,
                            canonical_label="静明园（玉泉山行宫苑）"),
    # 拼音与 yuanmingyuan.py 的长春园(ent_changchunyuan)同形，加 _kangxi 消歧
    PersistentSpatialEntity(id="ent_changchunyuan_kangxi", kind=PhysicalThingKind.GARDEN_COMPLEX,
                            canonical_label="畅春园"),
    PersistentSpatialEntity(id="ent_enyousi", kind=PhysicalThingKind.RELIGIOUS_PRECINCT,
                            canonical_label="恩佑寺"),
    PersistentSpatialEntity(id="ent_enmusi", kind=PhysicalThingKind.RELIGIOUS_PRECINCT,
                            canonical_label="恩慕寺"),
    # 「三山五园」为概念性合称（后世概括），实体只承担字符串消歧与指称，
    # 成员关系走 PlaceAggregate，绝不挂 identity 断言
    PersistentSpatialEntity(id="ent_sanshiwuyuan", kind=PhysicalThingKind.GARDEN_COMPLEX,
                            canonical_label="三山五园（京西皇家园林群概念合称）"),
]


# ==================================================================
# 4. 历时状态
# ==================================================================

STATES: List[HistoricalFeatureState] = [
    # ---- 香山（山岳） ----
    HistoricalFeatureState(
        id="st_xs_jin", entity_id="ent_xiangshan",
        time_span=_ts(1186, 1644, "ts_xs1"),
        geometry="西山一脉的山岳林地，山腰有香山寺（大永安寺，殿五层依岩架壑）",
        material="山体林泉、寺刹砖木",
        function="辽金元明皇家寺刹与游幸之山：金大定二十六年(1186)香山寺成赐名"
                 "大永安寺并给田二千亩，金帝于香山置行宫，元皇庆元年(1312)官修永安寺",
        evidence_fact_ids=["tf_xss_1186", "tf_xss_jin_early", "tf_xss_liao",
                           "tf_xs_xinggong_jin", "tf_xss_yuan_1312"],
    ),
    HistoricalFeatureState(
        id="st_xs_qing_xinggong", entity_id="ent_xiangshan",
        time_span=_ts(1662, 1745, "ts_xs2"),
        geometry="香山佛殿侧建行宫数宇，朴俭无丹雘之饰",
        material="行宫殿宇若干",
        function="清初康熙朝香山行宫，乾隆帝乾隆八年(1743)始往游后屡幸",
        evidence_fact_ids=["tf_jyy_xinggong_kangxi", "tf_jyy_ji_1745"],
    ),
    HistoricalFeatureState(
        id="st_xs_jingyi", entity_id="ent_xiangshan",
        time_span=_ts(1745, 1859, "ts_xs3"),
        geometry="静宜园依香山而建：内垣、外垣、别垣三重，御题二十八景错布山径",
        material="宫苑殿宇、山石林泉",
        function="皇家苑囿（静宜园）之山；乾隆十一年(1746)园成后为帝听政游幸之所",
        evidence_fact_ids=["tf_jyy_ji_1745", "tf_jyy_1746", "tf_jyy_28jing",
                           "tf_jyy_qinzheng", "tf_jyy_waiyuan"],
    ),
    HistoricalFeatureState(
        id="st_xs_1860", entity_id="ent_xiangshan",
        time_span=_ts(1860, 1956, "ts_xs4"),
        geometry="殿宇多毁，残迹与山林并存",
        material="残存砖石、山林",
        function="残存禁地：1860英法联军焚毁静宜园，1900复遭破坏，民国间荒废",
        evidence_fact_ids=["tf_xsgy_1860", "tf_1860_wyss"],
    ),
    HistoricalFeatureState(
        id="st_xs_1956", entity_id="ent_xiangshan",
        time_span=_ts(1956, 2026, "ts_xs5"),
        geometry="山林公园，部分景点原址复建（勤政殿2002依档复建）",
        material="公园建筑与山林植被",
        function="香山公园（1956开放，现状：对公众开放的城市山林公园）",
        evidence_fact_ids=["tf_xsgy_1956"],
    ),
    # ---- 静宜园（苑囿本体） ----
    HistoricalFeatureState(
        id="st_jyy_1745", entity_id="ent_jingyiyuan",
        time_span=_ts(1745, 1746, "ts_jyy1"),
        geometry="乾隆乙丑(1745)秋七月兴工：廓香山之郛、即旧行宫之基葺垣筑室",
        material="宫苑初构",
        function="静宜园营建期（在康熙行宫基础上因革，非平地新创）",
        evidence_fact_ids=["tf_jyy_ji_1745", "tf_jyy_xinggong_kangxi",
                           "tf_jyy_1746"],
    ),
    HistoricalFeatureState(
        id="st_jyy_1746", entity_id="ent_jingyiyuan",
        time_span=_ts(1746, 1859, "ts_jyy2"),
        geometry="丙寅(1746)春三月园成；二十八景分内垣、外垣、别垣",
        material="宫苑殿宇、山石林泉",
        function="皇家苑囿兼听政之所：定名静宜（取周子之意），勤政殿延见公卿百僚，"
                 "御题二十八景各系以诗",
        evidence_fact_ids=["tf_jyy_1746", "tf_jyy_28jing", "tf_jyy_ming",
                           "tf_jyy_qinzheng", "tf_jyy_waiyuan"],
    ),
    HistoricalFeatureState(
        id="st_jyy_1860", entity_id="ent_jingyiyuan",
        time_span=_ts(1860, 1900, "ts_jyy3"),
        geometry="殿宇多毁，残存建筑与残迹并存",
        material="残存砖木",
        function="残存禁园状态（1860焚毁当年即入残存态）",
        evidence_fact_ids=["tf_xsgy_1860", "tf_1860_wyss"],
    ),
    HistoricalFeatureState(
        id="st_jyy_1900", entity_id="ent_jingyiyuan",
        time_span=_ts(1900, 1956, "ts_jyy4"),
        geometry="残迹进一步毁损，民国间荒废",
        material="残迹",
        function="荒废遗址（1900复遭破坏）",
        evidence_fact_ids=["tf_xsgy_1860"],
    ),
    HistoricalFeatureState(
        id="st_jyy_1956", entity_id="ent_jingyiyuan",
        time_span=_ts(1956, 2026, "ts_jyy5"),
        geometry="静宜园旧址辟为香山公园",
        material="公园设施与山林",
        function="香山公园（1956开放，现状单独核查：对公众开放）",
        evidence_fact_ids=["tf_xsgy_1956"],
    ),
    # ---- 万寿山（山岳，旧称瓮山） ----
    HistoricalFeatureState(
        id="st_wss_ming", entity_id="ent_wanshoushan",
        time_span=TimeSpan(id="ts_wss0", label="明-乾隆十四年称瓮山", open_begin=True,
                           begin=None, end=_dt(1750, "ts_wss0_e")),
        geometry="玉泉山旁、西湖（今昆明湖）之北的山阜；明时山腰有圆静寺（后废）",
        material="山体、寺刹残迹",
        function="明代称瓮山（春明梦余录口径），湖山相望的京西名胜",
        evidence_fact_ids=["tf_wss_ming_ys", "tf_kmh_zhishui"],
    ),
    HistoricalFeatureState(
        id="st_wss_1750", entity_id="ent_wanshoushan",
        time_span=_ts(1750, 1860, "ts_wss1"),
        geometry="山阳建大报恩延寿寺，佛香阁等殿宇层叠",
        material="梵宫殿宇千楹（御制碑记语）",
        function="乾隆十五年(1750)瓮山命名万寿山（逢皇太后六旬大庆），"
                 "清漪园之山",
        evidence_fact_ids=["tf_qyy_1750", "tf_kmh_ciming", "tf_qyy_1761"],
    ),
    HistoricalFeatureState(
        id="st_wss_1860", entity_id="ent_wanshoushan",
        time_span=_ts(1860, 1886, "ts_wss2"),
        geometry="殿宇多毁",
        material="残存砖石",
        function="残存禁地（1860焚毁）",
        evidence_fact_ids=["tf_yhy_1860", "tf_1860_wyss"],
    ),
    HistoricalFeatureState(
        id="st_wss_1886", entity_id="ent_wanshoushan",
        time_span=_ts(1886, 2026, "ts_wss3"),
        geometry="重修后殿阁沿山势层叠（佛香阁组群）",
        material="重修宫苑殿宇",
        function="颐和园万寿山（1886起重建、1888改称颐和园；现状：开放公园）",
        evidence_fact_ids=["tf_yhy_1888", "tf_yhy_1924"],
    ),
    # ---- 清漪园→颐和园（同一持续体，1888改名） ----
    HistoricalFeatureState(
        id="st_qyy_1750", entity_id="ent_qingyiyuan",
        time_span=_ts(1750, 1761, "ts_qyy1"),
        geometry="清漪园建于万寿山之麓，圆明园西二里许，前为昆明湖",
        material="宫苑营建中",
        function="乾隆十五年(1750)赐名清漪园：治湖、命名、建寺同段展开；"
                 "园至乾隆二十六年辛巳(1761)方成",
        evidence_fact_ids=["tf_qyy_ce", "tf_qyy_1750", "tf_kmh_ciming",
                           "tf_qyy_1761"],
    ),
    HistoricalFeatureState(
        id="st_qyy_1761", entity_id="ent_qingyiyuan",
        time_span=_ts(1761, 1860, "ts_qyy2"),
        geometry="园成：万寿山前山殿宇、昆明湖堤桥、后溪河市肆水街（后溪河买卖街"
                 "见 urban 模块条目）",
        material="宫苑殿宇、堤桥、水街铺面",
        function="皇家苑囿——帝后过辰而往、逮午而返、未尝度宵的散志澄怀之所"
                 "（不当夜宿居园用），与圆明园居园理政功能分列",
        evidence_fact_ids=["tf_qyy_1761", "tf_qyy_riyong", "tf_hxh"],
    ),
    HistoricalFeatureState(
        id="st_qyy_1860", entity_id="ent_qingyiyuan",
        time_span=_ts(1860, 1886, "ts_qyy3"),
        geometry="殿宇多毁，残迹裸露",
        material="残存砖石",
        function="残存禁园状态（1860焚毁）",
        evidence_fact_ids=["tf_yhy_1860", "tf_1860_wyss"],
    ),
    HistoricalFeatureState(
        id="st_qyy_1888", entity_id="ent_qingyiyuan",
        time_span=_ts(1886, 1924, "ts_qyy4"),
        geometry="重修宫苑（1886起），1888改称颐和园",
        material="重修殿宇",
        function="颐和园——取「颐养冲和」之义，为慈禧太后颐养游憩兼御园听政之所",
        evidence_fact_ids=["tf_yhy_1888"],
    ),
    HistoricalFeatureState(
        id="st_qyy_1924", entity_id="ent_qingyiyuan",
        time_span=_ts(1924, 2026, "ts_qyy5"),
        geometry="公园化宫苑，残迹与重修建筑并存展示",
        material="宫苑建筑与园林",
        function="颐和园公园（1914售票开放、1924正式辟为公园；1998列入世界遗产"
                 "名录；现状单独核查：对公众开放）",
        evidence_fact_ids=["tf_yhy_1924"],
    ),
    # ---- 昆明湖 ----
    HistoricalFeatureState(
        id="st_kmh_xihu", entity_id="ent_kunminghu",
        time_span=TimeSpan(id="ts_kmh0", label="燕地旧池西湖-乾隆十四年",
                           open_begin=True, begin=None,
                           end=_dt(1750, "ts_kmh0_e")),
        geometry="西湖：东西二里、南北三里的天然湖泊（水经注「燕之旧池」），"
                 "玉泉诸泉所潴",
        material="湖体",
        function="玉泉山泉水潴蓄的京西北巨浸，明代西湖景稻畦千顷",
        evidence_fact_ids=["tf_xihu_shuijingzhu", "tf_kmh_zhishui"],
    ),
    HistoricalFeatureState(
        id="st_kmh_1750", entity_id="ent_kunminghu",
        time_span=_ts(1750, 2026, "ts_kmh1"),
        geometry="拓浚后的昆明湖：新湖之廓与深两倍于旧，西堤六桥、东堤闸洞",
        material="湖体、堤闸",
        function="乾隆十五年(1750)西湖易名昆明湖（师古用汉武昆明池典，"
                 "乾隆自述「人称汉武我慕唐尧」）；蓄水通漕、灌溉田亩、"
                 "伏日水操；今为颐和园湖面",
        evidence_fact_ids=["tf_qyy_1750", "tf_kmh_ciming", "tf_kmh_zhishui",
                           "tf_kmh_hanwu", "tf_kmh_shi", "tf_kmh_jingliu",
                           "tf_qyy_shuicao"],
    ),
    # ---- 万寿山后溪河（后湖） ----
    HistoricalFeatureState(
        id="st_hxh_open", entity_id="ent_houxihe",
        time_span=TimeSpan(id="ts_hxh0", label="万寿山后溪河（开放起讫）",
                           open_begin=True, begin=None,
                           open_end=True, end=None),
        geometry="发源于玉泉、自玉河东流经柳桥曲折东注的万寿山北麓河湖带",
        material="河湖水道",
        function="万寿山后溪河（卷84官书名）；今颐和园后湖/苏州河段，"
                 "两岸买卖街（清漪园后溪河买卖街另见 urban 模块条目，"
                 "与本河体是街与河两个对象）",
        evidence_fact_ids=["tf_hxh"],
    ),
    # ---- 玉泉山（山岳） ----
    HistoricalFeatureState(
        id="st_yqs_jin", entity_id="ent_yuquanshan",
        time_span=_ts(1190, 1644, "ts_yqs1"),
        geometry="西山山麓泉山，泉出石罅潴为池",
        material="山体泉脉、行宫佛舍遗构",
        function="金代行宫所在山：《金史·地理志》明载「宛平有玉泉山行宫」，"
                 "章宗明昌以降屡幸；金章宗芙蓉殿行宫仅旧传（官书注无考）",
        evidence_fact_ids=["tf_jmy_jin_xinggong", "tf_jmy_jin_zhangzong",
                           "tf_jmy_furong"],
    ),
    HistoricalFeatureState(
        id="st_yqs_1662", entity_id="ent_yuquanshan",
        time_span=_ts(1662, 1692, "ts_yqs2"),
        geometry="康熙朝山上已有城关（康熙二十年建，御题「函云」）等建筑",
        material="关城、殿宇",
        function="康熙朝玉泉山营建期（早于澄心园/静明园定名序列）",
        evidence_fact_ids=["tf_jmy_chengguan", "tf_hd_jmy"],
    ),
    HistoricalFeatureState(
        id="st_yqs_1692", entity_id="ent_yuquanshan",
        time_span=_ts(1692, 1751, "ts_yqs3"),
        geometry="玉泉山行宫苑（澄心园→静明园）所在山",
        material="山体泉脉、宫苑建筑",
        function="静明园（1692定名）之山，行宫禁苑",
        evidence_fact_ids=["tf_hd_jmy", "tf_jmy_aini"],
    ),
    HistoricalFeatureState(
        id="st_yqs_1751", entity_id="ent_yuquanshan",
        time_span=_ts(1751, 2026, "ts_yqs4"),
        geometry="山腹泉源上出，趵突如珠",
        material="山体泉脉",
        function="乾隆十六年(1751)御品天下第一泉；燕京八景「玉泉趵突」"
                 "（旧称玉泉垂虹，乾隆改称）；现状单独核查：山仍存，"
                 "静明园旧址不对外开放",
        evidence_fact_ids=["tf_yuquan_dyq", "tf_yuquan_baotu",
                           "tf_hd_yqs_status"],
    ),
    # ---- 静明园（苑囿本体） ----
    HistoricalFeatureState(
        id="st_jmy_1692", entity_id="ent_jingmingyuan",
        time_span=_ts(1692, 1859, "ts_jmy1"),
        geometry="玉泉山之阳的行宫苑：康熙年间创建，乾隆朝略加修葺成十六景",
        material="宫苑殿宇、泉石",
        function="皇家行宫禁苑：澄心园（1680）于康熙三十一年(1692)改称静明园；"
                 "玉泉趵突列燕京八景并御定天下第一泉；"
                 "金章宗芙蓉殿行宫为旧传、官书注无考",
        evidence_fact_ids=["tf_hd_jmy", "tf_jmy_aini", "tf_jmy_16jing",
                           "tf_jmy_furong", "tf_yuquan_dyq",
                           "tf_yuquan_baotu", "tf_jmy_houhu"],
    ),
    HistoricalFeatureState(
        id="st_jmy_1860", entity_id="ent_jingmingyuan",
        time_span=_ts(1860, 2026, "ts_jmy2"),
        geometry="殿宇多毁，残迹在玉泉山内",
        material="残存砖石",
        function="残存遗址；1860罹劫，现状单独核查：玉泉山静明园旧址不对外开放",
        evidence_fact_ids=["tf_1860_wyss", "tf_hd_yqs_status"],
    ),
    # ---- 畅春园 ----
    HistoricalFeatureState(
        id="st_ccy_kangxi", entity_id="ent_changchunyuan_kangxi",
        time_span=TimeSpan(id="ts_ccy0", label="康熙朝建成-康熙六十一年",
                           open_begin=True, begin=None,
                           end=_dt(1722, "ts_ccy0_e")),
        geometry="缭垣一千六十丈有奇；中路澹宁居、东路清溪书屋、西路无逸斋等，"
                 "买卖街建于河之南岸",
        material="宫苑殿宇（朴俭少加规度，因清华园故址山水）",
        function="康熙避喧听政之所：澹宁居御门听政、选馆引见；"
                 "本朝建成年份诸说并存（1684经始/1687告成/1690初建），"
                 "官书不载具体年份",
        evidence_fact_ids=["tf_ccy_ce", "tf_ccy_liwei", "tf_ccy_ji_yizhi",
                           "tf_ccy_ji_gui", "tf_ccy_tingzheng"],
    ),
    HistoricalFeatureState(
        id="st_ccy_1723", entity_id="ent_changchunyuan_kangxi",
        time_span=_ts(1723, 1859, "ts_ccy1"),
        geometry="园东垣增恩佑寺（1725建成）、恩慕寺（1777）；寿萱春永为皇太后寝殿",
        material="宫苑殿宇、两寺殿宇",
        function="皇太后园与帝问安驻跸之地：乾隆朝太后喜居畅春园，"
                 "帝自木兰回跸辄命驾问安",
        evidence_fact_ids=["tf_ccy_taihou", "tf_hd_eyou_emsi", "tf_eyou_ce",
                           "tf_emusi_1777"],
    ),
    HistoricalFeatureState(
        id="st_ccy_1860", entity_id="ent_changchunyuan_kangxi",
        time_span=_ts(1860, 2026, "ts_ccy2"),
        geometry="园毁，今仅存恩佑寺、恩慕寺两座山门（北京大学西门南侧）",
        material="两座山门（歇山无梁、黄琉璃瓦石券门）",
        function="遗址（2021年两山门列为第九批北京市文物保护单位）；"
                 "现状单独核查：地上遗存仅两山门",
        evidence_fact_ids=["tf_1860_wyss", "tf_hd_ccy_yizhi"],
    ),
    # ---- 恩佑寺 ----
    HistoricalFeatureState(
        id="st_eyou_1723", entity_id="ent_enyousi",
        time_span=_ts(1725, 1859, "ts_eyou1"),
        geometry="苑之东垣内：山门东向外临通衢，三殿五楹、南北配殿各三楹，"
                 "山门额「敬建恩佑寺」（世宗雍正御书——GPT审E14-05，勿与"
                 "恩慕寺乾隆御书混淆）",
        material="殿宇（正殿奉三世佛，左药师右无量寿佛）",
        function="世宗（雍正）为圣祖（康熙）荐福之寺：雍正三年(1725)建成"
                 "（《皇朝通志》/《皇朝文献通考》），雍正四年(1726)三月恭奉"
                 "圣祖御容，乾隆八年(1743)御容奉移安佑宫（GPT审E14-14）；"
                 "与清溪书屋为相邻关系非同址替换",
        evidence_fact_ids=["tf_eyou_yongzheng", "tf_eyou_ce", "tf_eyou_guihong",
                           "tf_hd_eyou_emsi"],
    ),
    HistoricalFeatureState(
        id="st_eyou_1860", entity_id="ent_enyousi",
        time_span=_ts(1860, 2026, "ts_eyou2"),
        geometry="殿宇尽毁，仅存山门",
        material="山门一座",
        function="遗址；2021年恩佑寺山门列为第九批北京市文物保护单位",
        evidence_fact_ids=["tf_hd_ccy_yizhi"],
    ),
    # ---- 恩慕寺 ----
    HistoricalFeatureState(
        id="st_emsi_1777", entity_id="ent_enmusi",
        time_span=_ts(1777, 1859, "ts_emsi1"),
        geometry="恩佑寺之右（侧），殿宇规制与恩佑寺同；山门额「敬建恩慕寺」"
                 "（高宗乾隆御书——GPT审E14-05；山门1985年重修换琉璃瓦）",
        material="殿宇（正殿奉药师佛一尊、左右药师佛一百八尊）",
        function="乾隆四十二年(1777)高宗为圣母皇太后广资慈福而建（绍承家法："
                 "恩佑寺为皇考为圣祖荐福所建）",
        evidence_fact_ids=["tf_emusi_1777", "tf_hd_eyou_emsi"],
    ),
    HistoricalFeatureState(
        id="st_emsi_1860", entity_id="ent_enmusi",
        time_span=_ts(1860, 2026, "ts_emsi2"),
        geometry="殿宇尽毁，仅存山门",
        material="山门一座",
        function="遗址；2021年恩慕寺山门列为第九批北京市文物保护单位",
        evidence_fact_ids=["tf_hd_ccy_yizhi"],
    ),
    # ---- 三山五园（概念合称） ----
    HistoricalFeatureState(
        id="st_sswy_guanzhi", entity_id="ent_sanshiwuyuan",
        time_span=TimeSpan(id="ts_sswy0", label="清代官方建制（开放起）",
                           open_begin=True, begin=None,
                           end=_dt(1911, "ts_sswy0_e")),
        geometry="京西北郊万寿山、玉泉山、香山三山与其苑囿带",
        material="皇家园林建筑群",
        function="清代官方建制用语只有「三山」（嘉庆会典事例：三山职掌清漪园、"
                 "静明园、静宜园园户），畅春园、圆明园各自职掌；"
                 "同治以前实录只有三山之名而无五园之说",
        evidence_fact_ids=["tf_sswy_huidian", "tf_sswy_shilu"],
    ),
    HistoricalFeatureState(
        id="st_sswy_1860", entity_id="ent_sanshiwuyuan",
        time_span=_ts(1860, 2026, "ts_sswy1"),
        geometry="东起清华熙春一带、西迄香山的皇家园林带（广义）",
        material="园林建筑群",
        function="合称的演变：咸丰十年(1860)鲍源深「夷人焚五园三山」为现存最早"
                 "近形连称；光绪二十三年(1897)常卯图题「三山五园外三营地理全图」、"
                 "光绪三十年(1904)马绶权图题「五园三山」；「三山五园」固定语序为"
                 "后世（现代学界）概括——现代研究框架，非清代官方称谓；"
                 "2024年三山五园传统地名保护名录为现行官方框架用语",
        evidence_fact_ids=["tf_1860_wyss", "tf_sswy_tu", "tf_minglu_sswy"],
    ),
]


# ==================================================================
# 5. 聚合：三山与五园同时并存，不是一裂为多
# ==================================================================

AGGREGATES: List[PlaceAggregate] = [
    PlaceAggregate(
        id="agg_sanshan", label="三山",
        time_span=_ts(1750, 1860, "ts_agg_ss"),
        member_entity_ids=["ent_wanshoushan", "ent_yuquanshan", "ent_xiangshan"],
    ),
    PlaceAggregate(
        id="agg_sanshiwuyuan", label="三山五园（五园成员）",
        time_span=_ts(1750, 1860, "ts_agg_sswy"),
        # 成员园五座：畅春园、圆明园、清漪园(颐和园)、静明园、静宜园。
        # 【跨模块引用】ent_yuanmingyuan 为 yuanmingyuan.py 实体（圆明园本体，
        # 含长春园/绮春园子园），本模块只引用 id 不重复建模；
        # 成员关系非同指，不挂 DiachronicIdentityAssertion。
        member_entity_ids=["ent_changchunyuan_kangxi", "ent_yuanmingyuan",
                           "ent_qingyiyuan", "ent_jingmingyuan", "ent_jingyiyuan"],
    ),
]


# ==================================================================
# 6. 空间变化：毁损 ≠ 消亡
# ==================================================================

TRANSFORMATIONS: List[PlaceTransformation] = [
    PlaceTransformation(
        id="pte_kmh_1750", entity_id="ent_kunminghu",
        transformation=PlaceTransformationEvent.EXPANDED,
        time_span=_ts(1750, 1750, "ts_t_kmh"),
        resulting_state_id="st_kmh_1750",
        resulting_condition="西湖拓浚为昆明湖，新湖之廓与深两倍于旧",
        evidence_fact_ids=["tf_kmh_zhishui", "tf_qyy_1750"],
    ),
    PlaceTransformation(
        id="pte_xs_1860", entity_id="ent_xiangshan",
        transformation=PlaceTransformationEvent.DAMAGED,
        time_span=_ts(1860, 1860, "ts_t_xs1"),
        resulting_state_id="st_xs_1860",
        resulting_condition="静宜园焚毁，山岳残存",
        evidence_fact_ids=["tf_xsgy_1860", "tf_1860_wyss"],
    ),
    PlaceTransformation(
        id="pte_xs_1956", entity_id="ent_xiangshan",
        transformation=PlaceTransformationEvent.REBUILT,
        time_span=_ts(1956, 1956, "ts_t_xs2"),
        resulting_state_id="st_xs_1956",
        resulting_condition="旧址辟为香山公园开放",
        evidence_fact_ids=["tf_xsgy_1956"],
    ),
    PlaceTransformation(
        id="pte_jyy_1860", entity_id="ent_jingyiyuan",
        transformation=PlaceTransformationEvent.PARTIALLY_DESTROYED,
        time_span=_ts(1860, 1860, "ts_t_jyy1"),
        resulting_state_id="st_jyy_1860",
        resulting_condition="殿宇多毁，残存建筑与禁园状态并存",
        evidence_fact_ids=["tf_xsgy_1860", "tf_1860_wyss"],
    ),
    PlaceTransformation(
        id="pte_jyy_1900", entity_id="ent_jingyiyuan",
        transformation=PlaceTransformationEvent.DAMAGED,
        time_span=_ts(1900, 1900, "ts_t_jyy2"),
        resulting_state_id="st_jyy_1900",
        resulting_condition="残迹再遭破坏，渐次荒废",
        evidence_fact_ids=["tf_xsgy_1860"],
    ),
    PlaceTransformation(
        id="pte_jyy_1956", entity_id="ent_jingyiyuan",
        transformation=PlaceTransformationEvent.REBUILT,
        time_span=_ts(1956, 1956, "ts_t_jyy3"),
        resulting_state_id="st_jyy_1956",
        resulting_condition="旧址辟为香山公园对公众开放",
        evidence_fact_ids=["tf_xsgy_1956"],
    ),
    PlaceTransformation(
        id="pte_wss_1860", entity_id="ent_wanshoushan",
        transformation=PlaceTransformationEvent.DAMAGED,
        time_span=_ts(1860, 1860, "ts_t_wss1"),
        resulting_state_id="st_wss_1860",
        resulting_condition="山中殿宇焚毁，山体残存",
        evidence_fact_ids=["tf_yhy_1860", "tf_1860_wyss"],
    ),
    PlaceTransformation(
        id="pte_wss_1886", entity_id="ent_wanshoushan",
        transformation=PlaceTransformationEvent.REBUILT,
        time_span=_ts(1886, 1886, "ts_t_wss2"),
        resulting_state_id="st_wss_1886",
        resulting_condition="光绪十二年起重修，为颐和园万寿山",
        evidence_fact_ids=["tf_yhy_1888"],
    ),
    PlaceTransformation(
        id="pte_qyy_1860", entity_id="ent_qingyiyuan",
        transformation=PlaceTransformationEvent.PARTIALLY_DESTROYED,
        time_span=_ts(1860, 1860, "ts_t_qyy1"),
        resulting_state_id="st_qyy_1860",
        resulting_condition="殿宇多毁，残存建筑与残迹并存",
        evidence_fact_ids=["tf_yhy_1860", "tf_1860_wyss"],
    ),
    PlaceTransformation(
        id="pte_qyy_1888", entity_id="ent_qingyiyuan",
        transformation=PlaceTransformationEvent.REBUILT,
        time_span=_ts(1888, 1888, "ts_t_qyy2"),
        resulting_state_id="st_qyy_1888",
        resulting_condition="重修改称颐和园（同一持续体改名，见身份断言）",
        evidence_fact_ids=["tf_yhy_1888"],
    ),
    PlaceTransformation(
        id="pte_jmy_1860", entity_id="ent_jingmingyuan",
        transformation=PlaceTransformationEvent.DAMAGED,
        time_span=_ts(1860, 1860, "ts_t_jmy"),
        resulting_state_id="st_jmy_1860",
        resulting_condition="园毁，残迹存玉泉山内",
        evidence_fact_ids=["tf_1860_wyss", "tf_hd_yqs_status"],
    ),
    PlaceTransformation(
        id="pte_ccy_1860", entity_id="ent_changchunyuan_kangxi",
        transformation=PlaceTransformationEvent.DAMAGED,
        time_span=_ts(1860, 1860, "ts_t_ccy"),
        resulting_state_id="st_ccy_1860",
        resulting_condition="园罹劫焚废，仅存恩佑寺恩慕寺两山门",
        evidence_fact_ids=["tf_1860_wyss", "tf_hd_ccy_yizhi"],
    ),
    PlaceTransformation(
        id="pte_eyou_1860", entity_id="ent_enyousi",
        transformation=PlaceTransformationEvent.PARTIALLY_DESTROYED,
        time_span=_ts(1860, 1860, "ts_t_eyou"),
        resulting_state_id="st_eyou_1860",
        resulting_condition="殿宇毁，山门独存",
        evidence_fact_ids=["tf_hd_ccy_yizhi"],
    ),
    PlaceTransformation(
        id="pte_emsi_1860", entity_id="ent_enmusi",
        transformation=PlaceTransformationEvent.PARTIALLY_DESTROYED,
        time_span=_ts(1860, 1860, "ts_t_emsi"),
        resulting_state_id="st_emsi_1860",
        resulting_condition="殿宇毁，山门独存",
        evidence_fact_ids=["tf_hd_ccy_yizhi"],
    ),
]


# ==================================================================
# 7. 身份断言：清漪园→颐和园为同一持续体改名
# ==================================================================

IDENTITIES: List[DiachronicIdentityAssertion] = [
    DiachronicIdentityAssertion(
        id="dia_qyy_yhy_same",
        subject_entity_ids=["ent_qingyiyuan"],
        relation=IdentityRelation.SAME_CONTINUANT,
        time_span=_ts(1888, 2026, "ts_dia_qyy"),
        evidence_fact_ids=["tf_yhy_1888", "tf_yhy_1924"],
        status=EpistemicStatus.VERIFIED,
        alternative_relations=[],
    ),
]


# ==================================================================
# 8. 名称与指称
# ==================================================================

APPELLATIONS: List[Appellation] = [
    Appellation(id="app_xs", label="香山", kind=AppellationKind.OFFICIAL,
                valid_time_span=TimeSpan(id="ts_n_xs", label="辽金以来-今",
                                         open_begin=True, begin=None,
                                         end=_dt(2026, "ts_n_xs_e")),
                attesting_fact_ids=["tf_jyy_ji_1745", "tf_xss_1186"]),
    Appellation(id="app_jyy", label="静宜园", kind=AppellationKind.HONORIFIC,
                valid_time_span=_ts(1746, 2026, "ts_n_jyy"),
                attesting_fact_ids=["tf_jyy_ming", "tf_jyy_1746"]),
    Appellation(id="app_xsgy", label="香山公园", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1956, 2026, "ts_n_xsgy"),
                attesting_fact_ids=["tf_xsgy_1956"]),
    Appellation(id="app_wss", label="万寿山", kind=AppellationKind.HONORIFIC,
                valid_time_span=_ts(1750, 2026, "ts_n_wss"),
                attesting_fact_ids=["tf_qyy_1750", "tf_kmh_ciming"]),
    Appellation(id="app_wengshan", label="瓮山", kind=AppellationKind.OLD_NAME,
                valid_time_span=TimeSpan(id="ts_n_weng", label="明代-乾隆十五年",
                                         open_begin=True, begin=None,
                                         end=_dt(1750, "ts_n_weng_e")),
                attesting_fact_ids=["tf_wss_ming_ys", "tf_kmh_zhishui"]),
    Appellation(id="app_qyy", label="清漪园", kind=AppellationKind.HONORIFIC,
                valid_time_span=_ts(1750, 1888, "ts_n_qyy"),
                attesting_fact_ids=["tf_qyy_ce", "tf_qyy_1750"]),
    Appellation(id="app_yhy", label="颐和园", kind=AppellationKind.HONORIFIC,
                valid_time_span=_ts(1888, 2026, "ts_n_yhy"),
                attesting_fact_ids=["tf_yhy_1888"]),
    Appellation(id="app_kmh", label="昆明湖", kind=AppellationKind.HONORIFIC,
                valid_time_span=_ts(1750, 2026, "ts_n_kmh"),
                attesting_fact_ids=["tf_kmh_ciming", "tf_kmh_shi"]),
    Appellation(id="app_xihu", label="西湖", kind=AppellationKind.OLD_NAME,
                valid_time_span=TimeSpan(id="ts_n_xihu", label="燕地旧称-乾隆十五年",
                                         open_begin=True, begin=None,
                                         end=_dt(1750, "ts_n_xihu_e")),
                attesting_fact_ids=["tf_xihu_shuijingzhu"]),
    Appellation(id="app_hxh", label="后溪河", kind=AppellationKind.OFFICIAL,
                valid_time_span=TimeSpan(id="ts_n_hxh", label="乾隆朝官书名-今",
                                         open_begin=True, begin=None,
                                         end=_dt(2026, "ts_n_hxh_e")),
                attesting_fact_ids=["tf_hxh"]),
    Appellation(id="app_hxh_houhu", label="万寿山后湖", kind=AppellationKind.VULGAR,
                valid_time_span=TimeSpan(id="ts_n_hxh_hh", label="现代通称",
                                         open_begin=True, begin=None,
                                         end=_dt(2026, "ts_n_hxh_hh_e")),
                attesting_fact_ids=[]),
    # app_houhu「后湖」裸名已移除（GPT审3-7）：裸名两指（静明园内后湖 卷85/
    # 万寿山后溪河带今通称），不得作为 ent_houxihe appellation；限定名
    # 「万寿山后湖」(app_hxh_houhu) 保留。检索遇裸用必须带山名前缀消歧。
    Appellation(id="app_yqs", label="玉泉山", kind=AppellationKind.OFFICIAL,
                valid_time_span=TimeSpan(id="ts_n_yqs", label="金代以来-今",
                                         open_begin=True, begin=None,
                                         end=_dt(2026, "ts_n_yqs_e")),
                attesting_fact_ids=["tf_jmy_jin_zhangzong",
                                    "tf_jmy_jin_xinggong"]),
    Appellation(id="app_jmy", label="静明园", kind=AppellationKind.HONORIFIC,
                valid_time_span=_ts(1692, 2026, "ts_n_jmy"),
                attesting_fact_ids=["tf_jmy_aini", "tf_hd_jmy"]),
    Appellation(id="app_cxy", label="澄心园", kind=AppellationKind.OLD_NAME,
                valid_time_span=_ts(1680, 1692, "ts_n_cxy"),
                attesting_fact_ids=["tf_hd_jmy"]),
    Appellation(id="app_ccy", label="畅春园", kind=AppellationKind.HONORIFIC,
                valid_time_span=TimeSpan(id="ts_n_ccy", label="康熙朝赐名-今",
                                         open_begin=True, begin=None,
                                         end=_dt(2026, "ts_n_ccy_e")),
                attesting_fact_ids=["tf_ccy_liwei", "tf_ccy_taihou"]),
    Appellation(id="app_eyou", label="恩佑寺", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1723, 2026, "ts_n_eyou"),
                attesting_fact_ids=["tf_eyou_yongzheng", "tf_eyou_ce"]),
    Appellation(id="app_emsi", label="恩慕寺", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1777, 2026, "ts_n_emsi"),
                attesting_fact_ids=["tf_emusi_1777"]),
    Appellation(id="app_sswy", label="三山五园", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1897, 2026, "ts_n_sswy"),
                attesting_fact_ids=["tf_sswy_tu", "tf_minglu_sswy"]),
    Appellation(id="app_wyss", label="五园三山", kind=AppellationKind.OLD_NAME,
                valid_time_span=_ts(1860, 1911, "ts_n_wyss"),
                attesting_fact_ids=["tf_1860_wyss"]),
]

REFERENCES: List[ReferentialAssertion] = [
    ReferentialAssertion(id="rr_xs", appellation_id="app_xs",
                         referent_entity_id="ent_xiangshan",
                         time_span=TimeSpan(id="ts_r_xs", label="辽金以来-今",
                                            open_begin=True, begin=None,
                                            end=_dt(2026, "ts_r_xs_e")),
                         evidence_fact_ids=["tf_jyy_ji_1745"]),
    ReferentialAssertion(id="rr_jyy", appellation_id="app_jyy",
                         referent_entity_id="ent_jingyiyuan",
                         time_span=_ts(1746, 2026, "ts_r_jyy"),
                         evidence_fact_ids=["tf_jyy_ming", "tf_jyy_28jing"]),
    ReferentialAssertion(id="rr_xsgy", appellation_id="app_xsgy",
                         referent_entity_id="ent_jingyiyuan",
                         time_span=_ts(1956, 2026, "ts_r_xsgy"),
                         evidence_fact_ids=["tf_xsgy_1956"]),
    ReferentialAssertion(id="rr_xs_park_alias", appellation_id="app_xsgy",
                         referent_entity_id="ent_xiangshan",
                         time_span=_ts(1956, 2026, "ts_r_xsgy_xs"),
                         evidence_fact_ids=["tf_xsgy_1956"]),
    ReferentialAssertion(id="rr_wss", appellation_id="app_wss",
                         referent_entity_id="ent_wanshoushan",
                         time_span=_ts(1750, 2026, "ts_r_wss"),
                         evidence_fact_ids=["tf_qyy_1750"]),
    ReferentialAssertion(id="rr_wengshan", appellation_id="app_wengshan",
                         referent_entity_id="ent_wanshoushan",
                         time_span=TimeSpan(id="ts_r_weng", label="明代-乾隆十五年",
                                            open_begin=True, begin=None,
                                            end=_dt(1750, "ts_r_weng_e")),
                         evidence_fact_ids=["tf_wss_ming_ys"]),
    ReferentialAssertion(id="rr_qyy", appellation_id="app_qyy",
                         referent_entity_id="ent_qingyiyuan",
                         time_span=_ts(1750, 1888, "ts_r_qyy"),
                         evidence_fact_ids=["tf_qyy_ce", "tf_qyy_1750"]),
    ReferentialAssertion(id="rr_yhy", appellation_id="app_yhy",
                         referent_entity_id="ent_qingyiyuan",
                         time_span=_ts(1888, 2026, "ts_r_yhy"),
                         evidence_fact_ids=["tf_yhy_1888"]),
    ReferentialAssertion(id="rr_kmh", appellation_id="app_kmh",
                         referent_entity_id="ent_kunminghu",
                         time_span=_ts(1750, 2026, "ts_r_kmh"),
                         evidence_fact_ids=["tf_kmh_ciming"]),
    ReferentialAssertion(id="rr_xihu", appellation_id="app_xihu",
                         referent_entity_id="ent_kunminghu",
                         time_span=TimeSpan(id="ts_r_xihu", label="燕地旧称-乾隆十五年",
                                            open_begin=True, begin=None,
                                            end=_dt(1750, "ts_r_xihu_e")),
                         evidence_fact_ids=["tf_xihu_shuijingzhu"]),
    ReferentialAssertion(id="rr_hxh", appellation_id="app_hxh",
                         referent_entity_id="ent_houxihe",
                         time_span=TimeSpan(id="ts_r_hxh", label="乾隆朝官书名-今",
                                            open_begin=True, begin=None,
                                            end=_dt(2026, "ts_r_hxh_e")),
                         evidence_fact_ids=["tf_hxh"]),
    ReferentialAssertion(id="rr_hxh_houhu", appellation_id="app_hxh_houhu",
                         referent_entity_id="ent_houxihe",
                         time_span=TimeSpan(id="ts_r_hxh_hh", label="现代通称",
                                            open_begin=True, begin=None,
                                            end=_dt(2026, "ts_r_hxh_hh_e")),
                         evidence_fact_ids=[],
                         status=EpistemicStatus.UNSUBSTANTIATED,
                         provenance="「万寿山后湖」为现代通称（颐和园后山后溪河带），"
                                    "未检得一手书证；仅按现代口语指称挂接"),
    # rr_houhu 随 app_houhu 一并移除（GPT审3-7）
    ReferentialAssertion(id="rr_yqs", appellation_id="app_yqs",
                         referent_entity_id="ent_yuquanshan",
                         time_span=TimeSpan(id="ts_r_yqs", label="金代以来-今",
                                            open_begin=True, begin=None,
                                            end=_dt(2026, "ts_r_yqs_e")),
                         evidence_fact_ids=["tf_jmy_jin_zhangzong"]),
    ReferentialAssertion(id="rr_jmy", appellation_id="app_jmy",
                         referent_entity_id="ent_jingmingyuan",
                         time_span=_ts(1692, 2026, "ts_r_jmy"),
                         evidence_fact_ids=["tf_jmy_aini", "tf_hd_jmy"]),
    ReferentialAssertion(id="rr_cxy", appellation_id="app_cxy",
                         referent_entity_id="ent_jingmingyuan",
                         time_span=_ts(1680, 1692, "ts_r_cxy"),
                         evidence_fact_ids=["tf_hd_jmy"]),
    ReferentialAssertion(id="rr_ccy", appellation_id="app_ccy",
                         referent_entity_id="ent_changchunyuan_kangxi",
                         time_span=TimeSpan(id="ts_r_ccy", label="康熙朝赐名-今",
                                            open_begin=True, begin=None,
                                            end=_dt(2026, "ts_r_ccy_e")),
                         evidence_fact_ids=["tf_ccy_liwei"]),
    ReferentialAssertion(id="rr_eyou", appellation_id="app_eyou",
                         referent_entity_id="ent_enyousi",
                         time_span=_ts(1723, 2026, "ts_r_eyou"),
                         evidence_fact_ids=["tf_eyou_yongzheng"]),
    ReferentialAssertion(id="rr_emsi", appellation_id="app_emsi",
                         referent_entity_id="ent_enmusi",
                         time_span=_ts(1777, 2026, "ts_r_emsi"),
                         evidence_fact_ids=["tf_emusi_1777"]),
    ReferentialAssertion(id="rr_sswy", appellation_id="app_sswy",
                         referent_entity_id="ent_sanshiwuyuan",
                         time_span=_ts(1897, 2026, "ts_r_sswy"),
                         evidence_fact_ids=["tf_sswy_tu", "tf_minglu_sswy"]),
    ReferentialAssertion(id="rr_wyss", appellation_id="app_wyss",
                         referent_entity_id="ent_sanshiwuyuan",
                         time_span=_ts(1860, 1911, "ts_r_wyss"),
                         evidence_fact_ids=["tf_1860_wyss"]),
]


# ==================================================================
# 9. 断言与采信（分层不混级）
# ==================================================================

PROPOSITIONS: List[Proposition] = [
    Proposition(
        id="prop_jyy_1746_dual",
        statement="静宜园乾隆十年乙丑(1745)秋兴工、十一年丙寅(1746)春园成并御题"
                  "二十八景——年份由御制《静宜园记》与乾隆十一年二十八景御制诗"
                  "两系书证互证（双源），营建跨越两年、成园在1746",
        derived_from_fact_ids=["tf_jyy_ji_1745", "tf_jyy_1746",
                               "tf_jyy_28jing"],
        inferred_subject_id="ent_jingyiyuan",
        inference_method="《静宜园记》纪日（乙丑/丙寅）与卷86按「乾隆十一年御制"
                         "诸诗」系年互相锁定；二手「1747赐名」说与两系书证不合，"
                         "不采",
        alternative_explanations=["部分二手资料作「乾隆十二年(1747)基本落成赐名」，"
                               "与官书「丙寅春三月而园成」矛盾"],
    ),
    Proposition(
        id="prop_xss_jin_1186",
        statement="香山寺金大定二十六年(1186)成、赐名大永安寺（《金史·世宗纪》"
                  "一手），寺之存在更早至天会间；乾隆称旧名永安/甘露属乾隆朝"
                  "对金代寺的解释层",
        derived_from_fact_ids=["tf_xss_1186", "tf_xss_jin_early",
                               "tf_xss_dading", "tf_xss_liao"],
        inferred_subject_id="ent_xiangshan",
        inference_method="正史纪事与乾隆诗注分挂两层：1186建成为金史明文；"
                         "辽代舍宅说（泠然志）为笔记层并存",
        alternative_explanations=["辽中丞阿勒弥舍宅为寺说（《泠然志》），"
                               "与金史纪事不矛盾但层级更低"],
    ),
    Proposition(
        id="prop_furong_daikao",
        statement="玉泉山金代行宫有《金史·地理志》明文；「金章宗芙蓉殿行宫」"
                  "仅旧传，乾隆朝官书已明注「无考」——存疑待考，不得作定论",
        derived_from_fact_ids=["tf_jmy_jin_xinggong", "tf_jmy_furong",
                               "tf_jmy_jin_zhangzong"],
        inferred_subject_id="ent_yuquanshan",
        inference_method="分层：正史（行宫）＞乾隆朝官书按语（旧传…无考）＞"
                         "明代笔记（长安客话/帝京景物略言芙蓉殿）",
        alternative_explanations=["长安客话「山顶有金行宫芙蓉殿故址相传章宗尝避暑"
                               "于此」与帝京景物略「山旧有芙蓉殿金章宗行宫也」"
                               "为明清笔记层口径"],
    ),
    Proposition(
        id="prop_ccy_qinghua_guzhi",
        statement="畅春园为康熙因明武清侯李伟清华园故址改建（卷76按语、御制"
                  "畅春园记、卷79考辨「今之畅春园就其旧址」三证），非「澄心园"
                  "改名」；澄心园为玉泉山静明园前身，二者不可混",
        derived_from_fact_ids=["tf_ccy_liwei", "tf_ccy_ji_yizhi",
                               "tf_qhy_guzhi", "tf_hd_jmy"],
        inferred_subject_id="ent_changchunyuan_kangxi",
        inference_method="官书三处独立表述一致指向清华园故址；"
                         "澄心园→静明园链条另有机构口径，与畅春园无关",
        alternative_explanations=[],
    ),
    Proposition(
        id="prop_ccy_not_chengxin",
        statement="「康熙二十三年(1684)澄心园改畅春园」不成立：官书无澄心园与"
                  "畅春园承继的任何表述，澄心园在玉泉山（静明园前身）",
        derived_from_fact_ids=["tf_ccy_liwei", "tf_qhy_guzhi", "tf_hd_jmy"],
        inferred_subject_id="ent_changchunyuan_kangxi",
        inference_method="反证：官书口径为「本前明戚畹武清侯李伟别墅因故址改建」；"
                         "澄心园书证全部系于玉泉山",
        alternative_explanations=["个别二手材料将两园沿革串写混淆"],
    ),
    Proposition(
        id="prop_ccy_year_contested",
        statement="畅春园建成年代诸说并存：康熙二十三年(1684)经始、二十六年"
                  "(1687)告成、二十九年(1690)初建三说，官书不载具体年份",
        derived_from_fact_ids=["tf_ccy_ji_yizhi", "tf_ccy_tingzheng"],
        inferred_subject_id="ent_changchunyuan_kangxi",
        inference_method="康熙御制记自述「爰诏内司少加规度…既成而以畅春为名」"
                         "而不系年；二手年份互歧，故状态层用开放起始",
        alternative_explanations=["康熙二十三年南巡归后经始说",
                               "康熙二十六年告成说（人大清史所系）",
                               "康熙二十九年初建说（王开玺文）"],
    ),
    Proposition(
        id="prop_eyou_built_by_yongzheng",
        statement="恩佑寺为世宗（雍正）为圣祖（康熙）荐福建于畅春园东垣——"
                  "不是「乾隆为雍正荐福」（乾隆为雍正荐福者系圆明园安佑宫）；"
                  "雍正元年(1723)年份为机构通说，官书不载具体年份",
        derived_from_fact_ids=["tf_eyou_yongzheng", "tf_eyou_guihong",
                               "tf_hd_eyou_emsi"],
        inferred_subject_id="ent_enyousi",
        inference_method="卷76按语明书建者与荐福对象；乾隆诗序「我皇考改建恩佑寺"
                         "以奉御容」旁证；年份采机构口径并注明性质",
        alternative_explanations=["乾隆七年(1742)前后建成的安佑宫（圆明园）才是"
                               "乾隆为雍正荐福之所，与恩佑寺不可混"],
    ),
    Proposition(
        id="prop_sswy_modern_framework",
        statement="「三山五园」固定称谓是后世概括：清代官方仅有「三山」建制与"
                  "诸园分称（会典/实录无连称），咸丰十年「五园三山」为现存最早"
                  "近形连称，光绪间舆图始题「三山五园」，现代学界沿用并定型"
                  "——现代研究框架，非清代官方称谓",
        derived_from_fact_ids=["tf_sswy_huidian", "tf_sswy_shilu",
                               "tf_1860_wyss", "tf_sswy_tu"],
        inferred_subject_id="ent_sanshiwuyuan",
        inference_method="王开玺(2022)考证路径：会典条目→实录词频→鲍源深→"
                         "常卯/马绶权舆图；本库按其结论挂后世分析层",
        alternative_explanations=["郑艳/何瑜「民间统称/泛称论」",
                               "樊志斌「三五观念行文说」（鲍源深个人修辞）",
                               "张恩荫「五园=圆明五园」说（学界多不认同）"],
    ),
    Proposition(
        id="prop_houhu_ambiguity",
        statement="「后湖」一名至少两指：静明园内后湖（卷85「廓然大公之北临"
                  "后湖」）与万寿山后溪河段今通称后湖——裸用必须带山名前缀消歧",
        derived_from_fact_ids=["tf_jmy_houhu", "tf_hxh"],
        inferred_subject_id="ent_houxihe",
        inference_method="两处官书用例对照；「万寿山后湖」专指颐和园后溪河带，"
                         "静明园后湖无专名化通称",
        alternative_explanations=["静明园后湖或即十六景芙蓉晴照所在湖面（书证未明，"
                               "不入库）"],
    ),
    Proposition(
        id="prop_yhy_open_1924",
        statement="颐和园以1924年为正式辟为公园开放节点（机构现行公开口径）；"
                  "另有1928年北平特别市接管后全面开放说，两说并存",
        derived_from_fact_ids=["tf_yhy_1924"],
        inferred_subject_id="ent_qingyiyuan",
        inference_method="现状单独核查：机构口径（1924）为主流表述，"
                         "1928为接管管理完善节点说",
        alternative_explanations=["1928年北平特别市政府接管并规范管理说"],
    ),
]

ADOPTIONS: List[BeliefAdoption] = [
    BeliefAdoption(proposition_id="prop_jyy_1746_dual",
                   status=EpistemicStatus.VERIFIED, confidence=0.95,
                   adopted_by="三山五园词条v1",
                   rationale="两系书证（记+诗系）互锁1745/1746，"
                             "不用二手1747说"),
    BeliefAdoption(proposition_id="prop_xss_jin_1186",
                   status=EpistemicStatus.VERIFIED, confidence=0.9,
                   adopted_by="三山五园词条v1",
                   rationale="金史纪事为正史一手；乾隆诗注另层不混"),
    BeliefAdoption(proposition_id="prop_furong_daikao",
                   status=EpistemicStatus.CONTESTED, confidence=0.5,
                   adopted_by="三山五园词条v1",
                   rationale="正史证行宫、旧传证芙蓉殿而官书注无考——"
                             "存疑待考，不得作定论使用"),
    BeliefAdoption(proposition_id="prop_ccy_qinghua_guzhi",
                   status=EpistemicStatus.VERIFIED, confidence=0.95,
                   adopted_by="三山五园词条v1",
                   rationale="官书三证一致，故址链条闭合"),
    BeliefAdoption(proposition_id="prop_ccy_not_chengxin",
                   status=EpistemicStatus.DISPROVEN, confidence=0.85,
                   adopted_by="三山五园词条v1",
                   rationale="官书口径与澄心园书证全面反证「澄心园改畅春园」说",
                   refuting_fact_ids=["tf_ccy_liwei", "tf_qhy_guzhi",
                                      "tf_hd_jmy"]),
    BeliefAdoption(proposition_id="prop_ccy_year_contested",
                   status=EpistemicStatus.CONTESTED, confidence=0.6,
                   adopted_by="三山五园词条v1",
                   rationale="官书不系年，三说并存；状态层用开放起始防伪精确"),
    BeliefAdoption(proposition_id="prop_eyou_built_by_yongzheng",
                   status=EpistemicStatus.VERIFIED, confidence=0.95,
                   adopted_by="三山五园词条v1",
                   rationale="官书明文建者与荐福对象；纠正任务书「乾隆为雍正"
                             "荐福(1744)」之混淆（安佑宫才是）"),
    BeliefAdoption(proposition_id="prop_sswy_modern_framework",
                   status=EpistemicStatus.VERIFIED, confidence=0.9,
                   adopted_by="三山五园词条v1",
                   rationale="会典/实录无连称+1860近形连称+1897图名——"
                             "固定语系后世概括，标现代研究框架"),
    BeliefAdoption(proposition_id="prop_houhu_ambiguity",
                   status=EpistemicStatus.CONTESTED, confidence=0.7,
                   adopted_by="三山五园词条v1",
                   rationale="两处官书用例证明两指，消歧规则入检索纪律"),
    BeliefAdoption(proposition_id="prop_yhy_open_1924",
                   status=EpistemicStatus.CONTESTED, confidence=0.7,
                   adopted_by="三山五园词条v1",
                   rationale="机构现行口径1924为主，1928说并存不裁决"),
]
