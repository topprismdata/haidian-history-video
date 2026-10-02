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
        id="src_mingshi", title="明史",
        category=SourceCategory.OFFICIAL_HISTORY,
        total_volumes=332,
        base_edition=ZHONGHUA,
        edition_note="《兵志》载卫所编制：卫5600人→千户所1120→百户所112，"
                     "每百户辖总旗2各50人、小旗10各10人；"
                     "《地理志》引《明一统志》「青龙桥跨其上」",
    ),
    HistoricalSource(
        id="src_hd_diqumingzhi", title="海淀区地名志",
        category=SourceCategory.LOCAL_GAZETTEER,
        issuing_body="北京市海淀区地名志编纂委员会",
        edition_note="解释西三旗为清河以北牧马场西侧三个小旗驻点，"
                     "西二旗即两个小旗驻点；同组还有东二旗、东三旗。"
                     "属地名志解释（L2/L3），非档案直证",
    ),
    HistoricalSource(
        id="src_2024_minglu", title="北京市三山五园传统地名保护名录",
        category=SourceCategory.LOCAL_GAZETTEER,
        issuing_body="北京市规划和自然资源委员会",
        edition_note="2024年第一批421处；「青龙桥」名称出现年代标为明代。"
                     "属政府正式名录（L2），不能替代文保测绘档案",
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
        id="src_ccvg", title="CCVG 中国数字村庄数据（Chinese Village Data）",
        category=SourceCategory.LOCAL_GAZETTEER,
        issuing_body="匹兹堡大学图书馆系统东亚馆",
        edition_note="2,601 行政村数据（2022-11，源 2,701 部村志）CSV 批量下载，"
                     "开放数据。用途：古今夹逼裁决档——历史地名查 TGAZ 政区归属、"
                     "当代村名在 CCVG 验证存续；两源皆命中→高置信；"
                     "仅 CCVG 命中→提示近代/当代新名（海淀村落粒度唯一可得源）",
    ),
    HistoricalSource(
        id="src_dila", title="DILA/DDBC 地名规范资料库",
        category=SourceCategory.LOCAL_GAZETTEER,
        issuing_body="法鼓文理学院 DILA（台湾）",
        edition_note="佛典相关中国历史地名（寺/山/政区/佛迹）权威档，"
                     "带经纬度，秦至今；Web Services API + KML + 开放下载，"
                     "站点自述 open-sourced。用途：异源裁决档——宗教/文献视角"
                     "与 CHGIS 完全独立，对寺/庙/山/泉类海淀地名有独立考证价值"
                     "（大钟寺/万寿寺/大觉寺类词条直接受益）",
    ),
    HistoricalSource(
        id="src_ccts", title="CCTS 中华文明之时空基础架构",
        category=SourceCategory.GEOGRAPHICAL_TREATISE,
        issuing_body="中研院人社中心 GIS 专题中心（台湾）",
        edition_note="先秦至清代/当代，谭其骧图集为本；政区+聚落点+明清驿站图层；"
                     "地名整合检索 API + OGC WMTS，学术使用授权。"
                     "用途：同源确认档——与 TGAZ 同宗谭图但独立实现，"
                     "TGAZ 命中后的二次确认（裁决增量小于 DILA/CCVG）",
    ),
    HistoricalSource(
        id="src_ccts_mhpname", title="CCTS《讀史方輿紀要》地名研究资料库",
        category=SourceCategory.GEOGRAPHICAL_TREATISE,
        issuing_body="中研院人社中心 GIS 专题中心（台湾）",
        edition_note="61,685 个明代县级以下历史微观地名，分类包括村、馆、店、庄、"
                     "寨、场、集、乡、埠、宅，以及寺、墓、桥、闸、井、铺、堡、驿等；"
                     "WMTS 图层 ad1582_10_2s。非开放许可证（用户协议限制再授权/分发）；"
                     "纪律：作为 reference-only match 外部对照依据（存 URI/ID 与匹配证据），"
                     "绝不全量复制入可再发布的正式 KB",
    ),
    HistoricalSource(
        id="src_mcgd", title="MCGD 近代中国时空数据库（Modern China Geospatial Database）",
        category=SourceCategory.GEOGRAPHICAL_TREATISE,
        issuing_body="法国艾克斯-马赛大学（Aix-Marseille University / ERC ENP-China）",
        edition_note="47.3 万条地名与异名记录（Zenodo CSV，持续更新），"
                     "包含大量中文名、拼音与近代外文（英法等）历史转写对应同一 Location ID；"
                     "用于近代史料外文转写与异名消歧（正式使用前核验 Zenodo License）",
    ),
    HistoricalSource(
        id="src_tgaz", title="TGAZ 时空地名辞典（Temporal Gazetteer）",
        category=SourceCategory.LOCAL_GAZETTEER,
        issuing_body="哈佛燕京学社 × 复旦大学历史地理研究中心（CHGIS 项目）",
        edition_note="基于 CHGIS 的历史地名时空数据库，覆盖秦至清(前221-1911)，"
                     "提供地名/年代/类型检索与 API；用途：闭包候选的权威裁决依据——"
                     "候选地名若能在 TGAZ 命中，即有独立书目佐证，"
                     "置信度从 mid 升 high；未命中不否决（地方性小地名可能未收录）",
    ),
    HistoricalSource(
        id="src_chgis", title="CHGIS 中国历史地理信息系统",
        category=SourceCategory.GEOGRAPHICAL_TREATISE,
        issuing_body="哈佛燕京学社 × 复旦大学历史地理研究中心",
        base_edition="GIS数据集",
        edition_note="秦至清连续政区边界与居民点时空序列（Shapefile/KML/DBF），"
                     "V6 为最新版；学术免费使用（CC BY-NC 类），商用需授权；"
                     "引用规范：CHGIS, Version 6. Cambridge: Harvard Yenching "
                     "Institute and Fudan Center for Historical Geography",
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
        issuing_body="圆明园管理处",
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

    # ---------- 明清北京寺钟文献（E9 大钟寺词条入库，2026-10-02） ----------
    # 每书作者/机构必填；引文一律按原刻本繁体字形逐字核对，不得以简体转写冒充原文。
    HistoricalSource(
        id="src_dijingjingwulue", title="帝京景物略",
        category=SourceCategory.LITERARY_COLLECTION,
        author_person_id="person_liudong",
        compiler_person_ids=["person_yuyizheng", "person_zhou_sun"],
        base_edition=SISHU,
        edition_note="刘侗、于奕正合撰（刘侗属文、于奕正采辑），周损编辑成书"
                     "（E8复查红线：不得说刘侗一人所撰）。记大钟「向藏漢經廠」"
                     "「日供六僧擊之」，为钟履历链的两处一手明录；"
                     "又记「歲清明……都人踏青高梁橋」为高梁桥踏青盛况一手明录。"
                     "引文按原刻繁体字形（漢經廠），卷次待核、不得臆标",
    ),
    HistoricalSource(
        id="src_zuozhongzhi", title="酌中志",
        category=SourceCategory.LITERARY_COLLECTION,
        author_person_id="person_liuruoyu",
        edition_note="明末宦官刘若愚忆撰之内府见闻。记「至於三十年後，於西直門外萬壽寺中"
                     "建大鐘樓，懸大鐘一口」「日夜撞不絕聲，云十萬八千杵」，"
                     "为万寿寺期一手宦官记述；繁体原字形核对，卷次待核",
    ),
    HistoricalSource(
        id="src_changankehua", title="长安客话",
        category=SourceCategory.LITERARY_COLLECTION,
        author_person_id="person_jiangyikui",
        edition_note="万历间蒋一葵撰。记万寿寺「寺有方鐘樓，前臨大道，樓僅容鐘」与大钟"
                     "「聲聞數十里，其聲宏宏，時遠時近，有異他鐘」；"
                     "书名繁体作《長安客話》，引文逐字核对，卷次待核",
    ),
    HistoricalSource(
        id="src_chunmengmengyulu", title="春明梦余录",
        category=SourceCategory.LITERARY_COLLECTION,
        author_person_id="person_sunchengze",
        total_volumes=70,
        base_edition=SISHU,
        edition_note="孙承泽撰。记德胜门东铸钟厂「舊鑄高二丈餘、闊一丈餘者，尚有十數仆地上」，"
                     "为大钟铸于铸钟厂（现代研究推断）的关键旁证；卷次待核",
    ),
    HistoricalSource(
        id="src_yanjingsuishiji", title="燕京岁时记",
        category=SourceCategory.LITERARY_COLLECTION,
        author_person_id="person_fuchadunchong",
        edition_note="清末富察敦崇撰，全一卷。记觉生寺大钟殿「高五丈，下方上圓，四面皆窗，"
                     "後有旋梯，左升右降」；所记庙会民俗（打金钱眼等）为民俗史料，"
                     "与佛事功能分属两层，不得混级",
    ),
    HistoricalSource(
        id="src_wanliyehuobian", title="万历野获编",
        category=SourceCategory.LITERARY_COLLECTION,
        author_person_id="person_shendefu",
        edition_note="沈德符撰，分类编排、另有补遗。记万寿寺营建「浹歲即成」，"
                     "证万历五年(1577)开工、六年(1578)竣工跨年完成，堵「同年建成」误说；"
                     "卷次待核",
    ),
    HistoricalSource(
        id="src_lianggongdingjianji", title="两宫鼎建记",
        category=SourceCategory.LITERARY_COLLECTION,
        author_person_id="person_hezhongshi",
        edition_note="贺仲轼记万历年间两宫灾后修建事宜。记搬运巨料「每里掘一井，以澆旱船、"
                     "資渴飲」「比時天寒地凍，正宜趁時發運」——该方法明代确曾用于运巨石，"
                     "仅可作「冰道运钟」传说之方法旁证，不得当成本钟史实",
    ),
    HistoricalSource(
        id="src_jueshengsi_beiwen", title="敕建觉生寺碑文",
        category=SourceCategory.EPIGRAPHY,
        author_person_id="person_yongzheng",
        base_edition=SHIBEN,
        edition_note="雍正御制，寺内原碑（石刻一手）。载选址「高朗乾爽，林木佳茂」"
                     "「右隔塵市之囂，左繞山川之勝」、取名「以無覺之覺，覺不生之生」、"
                     "「爰賜名覺生寺」。引文按碑石原字核对；"
                     "开工(1733)与赐名(1734)分属两年，不得混写同年",
    ),
    HistoricalSource(
        id="src_qianlong_shiwenji", title="清高宗御制诗文集",
        category=SourceCategory.LITERARY_COLLECTION,
        author_person_id="person_qianlong",
        base_edition=SISHU,
        edition_note="乾隆八年(1743)《御制觉生寺大钟诗》仍佛教语汇（「善吼周三界」），"
                     "乾隆十一年(1746)《觉生寺大钟歌用沈德潜韵》始绑定靖难与忏悔叙事"
                     "（「晁謀弗善野戰龍」「懺悔詎賴佛氏鐘」）。两诗分属两篇卷，"
                     "严禁剪接为同年同作",
    ),
    HistoricalSource(
        id="src_yuanzhonglang", title="袁中郎全集",
        category=SourceCategory.LITERARY_COLLECTION,
        author_person_id="person_yuanhongdao",
        edition_note="袁宏道撰。《万寿寺观文皇旧钟》诗「道傍觀者肩相摩，車騎數月猶馳逐」"
                     "记移钟盛况；「外書佛母萬真言，內寫雜花八十軸」与实物铭文不符，"
                     "证「华严钟」之名与八十一卷华严说至晚明已流传。卷次待核",
    ),
    HistoricalSource(
        id="src_dzs_history", title="大钟寺古钟博物馆馆史资料",
        category=SourceCategory.ARCHAEOLOGY_REPORT,
        issuing_body="大钟寺古钟博物馆",
        version_description="博物馆公开沿革、器物档案与专题课题结项公告",
        edition_note="1957市保/1980文保所/1985博物馆成立/1996国保(4-166)沿革，"
                     "钟高6.75米等现行公开口径，1778祈雨设坛记录与2023祈雨专项课题"
                     "「纠正非祈雨不鸣讹传」结论的公开出处。属机构公开资料(L2/L3)，"
                     "与古籍逐字引文分挂不同篇卷，不得互冒",
    ),
    # ---------- E8高梁桥 / E2安河桥 桥类词条入库（2026-10-02） ----------
    # 每书作者/机构必填；引文一律按原刻本繁体字形逐字核对，不得以简体转写冒充原文。
    # 机构名录/档案用官书类目登记并写明责任机构；地方文史口碑类用口述访谈类目，与档案分层。
    HistoricalSource(
        id="src_jinshi", title="金史",
        category=SourceCategory.OFFICIAL_HISTORY,
        author_person_id="person_tuotuo",
        total_volumes=135,
        base_edition=ZHONGHUA,
        edition_note="元至正间脱脱领修。载金代高梁河闸灌溉事：承安三年(1198)"
                     "「命勿毀高梁河閘，從民灌溉」——金代此河段已有人工水闸的一手记录，"
                     "堵「1292年是这条河第一道闸」误说。引文逐字核对以中华书局点校本为准；"
                     "志内篇次卷次待核、不得臆标",
    ),
    HistoricalSource(
        id="src_dajinjili", title="大金集礼",
        category=SourceCategory.OFFICIAL_HISTORY,
        author_person_id="person_zhangwei",
        total_volumes=40,
        base_edition=SISHU,
        edition_note="金代官修礼制典章总集，明昌六年(1195)礼部尚书张暐等进呈"
                     "（纂修起于大定间一说并存），清四库馆自《永乐大典》辑出。"
                     "与《金史》互证金代高梁河水系官营管理制度背景。"
                     "本词条登记篇卷备核，具体引文待核原典后补，不得预支结论",
    ),
    HistoricalSource(
        id="src_lidaizhiguangbiao", title="钦定历代职官表",
        category=SourceCategory.OFFICIAL_HISTORY,
        issuing_body="清高宗敕撰（四库全书馆）",
        total_volumes=72,
        base_edition=SISHU,
        edition_note="乾隆朝敕撰官书。卷八《户部仓场衙门表》载丰益仓："
                     "在德胜门外安河桥，雍正七年(1729)建，供守卫圆明园八旗官军俸饷。"
                     "引文以维基文库/识典古籍转录本定位，逐字句以原刻本核对后方可引用",
    ),
    HistoricalSource(
        id="src_minglu_2", title="三山五园地区传统地名保护名录（第二批）",
        category=SourceCategory.OFFICIAL_HISTORY,
        issuing_body="北京市规划和自然资源委员会、北京市海淀区人民政府",
        edition_note="政府正式名录（官书类，非个人撰述）：2024-11-13公布，"
                     "批准文件落款2025-06-20，2025年10月由市规划自然资源委网站公开发布。"
                     "「高梁桥」列入，标准用字为木字底「梁」（字形纠偏）；"
                     "「安河桥村」地名出现年代列为明代，并载村界四至（东、南至清河，"
                     "西至京密引水渠，北至正红旗村）。名录证地名出现年代，"
                     "不直接等同考古意义上的聚落形成",
    ),
    HistoricalSource(
        id="src_bma_1929", title="北平市工务局郊区桥梁档案",
        category=SourceCategory.OFFICIAL_HISTORY,
        issuing_body="北平市工务局（1929年调查）",
        edition_note="安河桥桥史「系统B」出处：始建于元代以前；明正统十四年(1449)重修；"
                     "康熙五十九年(1720)重建石拱桥；光绪十二年(1886)再修。"
                     "本库经研究论文（香港中文大学《历史人类学学刊》系）转引使用，"
                     "L1转引→暂按L2；1929年原档扫描件未目验前，"
                     "不得宣布「元以前始建」为新定论，与「系统A」两说并存不裁决",
    ),
    HistoricalSource(
        id="src_wjbz_open", title="北京市文物局公开文保资料",
        category=SourceCategory.ARCHAEOLOGY_REPORT,
        issuing_body="北京市文物局",
        version_description="文保单位公开沿革与现状口径",
        edition_note="记录式陈述（非古籍引文）：1980年代初展宽高梁桥路时重修（约1980—1982）；"
                     "2003年古桥南北各建公路桥、不再供道路通行；界桥（桥南西城区展览路街道、"
                     "桥北海淀区北下关街道）；2013年「高粱闸」（文保名录沿用米字底）列为大运河"
                     "北京段第七批国保遗产点；桥上置闸称高梁闸（又称西城闸）、该闸已毁。"
                     "与古籍逐字引文分挂不同篇卷，不得互冒",
    ),
    HistoricalSource(
        id="src_hd_gov_open", title="海淀区人民政府公开史地沿革资料",
        category=SourceCategory.OFFICIAL_HISTORY,
        issuing_body="北京市海淀区人民政府",
        edition_note="政府公开沿革（记录式陈述）：乾隆十六年(1751)长河通航、桥西建倚虹堂"
                     "（南岸另有船坞，两建筑分列）；高梁桥为今长河与转河衔接点"
                     "（桥西至白石桥为长河、桥东往积水潭为转河）；1965年因修京密引水渠于"
                     "青龙桥东北约0.5公里另址新建安河新桥；安河桥一带1990—2000年代多轮改造",
    ),
    HistoricalSource(
        id="src_anheqiao_xiaoshi", title="安河桥小史（老北京网）",
        category=SourceCategory.ORAL_TRADITION,
        issuing_body="老北京网（地方文史）",
        edition_note="安河桥桥史「系统A」出处（L3/L4，口播须软化）：雍正二年(1724)始建木桥、"
                     "乾隆年间改建单孔石拱；单孔石拱桥面隆起俗称「罗锅桥」（两系统兼容）；"
                     "石额刻「安和桥」旧料、近现代通行写「安河桥」；民国时安河桥村为"
                     "青龙桥镇域内较大聚落。与1929档案「系统B」正面冲突，两说并存不裁决",
    ),
    HistoricalSource(
        id="src_sxwj", title="三山五园水系变迁",
        category=SourceCategory.ARCHAEOLOGY_REPORT,
        issuing_body="公开出版研究（2026年出版，出版机构待核；经北京新闻报导核验）",
        edition_note="2009年清河河底施工时安河桥下出土明代木桩，本书刊布实物图（L2）。"
                     "木料年代区间之说属项目内部检测资料（L5，原始报告未公开），"
                     "不入库、口播禁用；木桩「桥基」身份存疑，只说「出土的明代木桩」",
    ),
    # ---------- E5一亩园 / E10蓝靛厂 / E12苏州街 / E13中关村 词条入库（2026-10-02） ----------
    HistoricalSource(
        id="src_baxun_wanshou", title="钦定八旬万寿盛典",
        category=SourceCategory.OFFICIAL_HISTORY,
        author_person_id="person_agui",
        base_edition="武英殿刻本",
        edition_note="乾隆五十七年（1792）成书。图绘一亩园为圆明园大宫门前附属院落、"
                     "后勤及公务人员临时住舍，反转「皇帝亲耕一亩三分地」民间传说",
    ),
    HistoricalSource(
        id="src_daminghuidian", title="大明会典",
        category=SourceCategory.OFFICIAL_HISTORY,
        issuing_body="明礼部官修（徐溥、李东阳等纂修）",
        base_edition="万历刻本",
        edition_note="载内官监染坊、蓝靛厂等宫廷专属官营作坊制度，"
                     "证蓝靛厂初为宫廷官署作坊而非普通村民染坊",
    ),
    HistoricalSource(
        id="src_xiaoting_zalu", title="啸亭杂录",
        category=SourceCategory.LITERARY_COLLECTION,
        author_person_id="person_zhaolian",
        base_edition="清道光刻本",
        edition_note="卷十载乾隆辛巳（1761）崇庆皇太后七旬圣寿建万寿寺外买卖街（万寿街/苏州街），"
                     "为苏州街作为真正买卖街始建年代的最硬一手笔记依据",
    ),
    HistoricalSource(
        id="src_tianzhi_ouwen", title="天咫偶闻",
        category=SourceCategory.LITERARY_COLLECTION,
        author_person_id="person_zhenjun",
        base_edition="光绪三十三年刻本",
        edition_note="卷七载万寿寺外买卖街「今已毁尽」，为苏州街咸丰朝后毁废现状的一手清末记述",
    ),
    HistoricalSource(
        id="src_hanshu", title="汉书",
        category=SourceCategory.OFFICIAL_HISTORY,
        author_person_id="person_bangu",
        base_edition="百衲本二十四史",
        edition_note="《高帝纪》载「诸中官、宦者令丞」，为「中官」代指太监的正典溯源；"
                     "中关村明清原名中官村/中官坟/中官屯，为太监公共义地",
    ),
    HistoricalSource(
        id="src_1913_jingxitu", title="京西图（1913）",
        category=SourceCategory.MILITARY_SURVEY_MAP,
        issuing_body="北洋政府内务部测绘局 / 陆军测量局",
        base_edition="二万五千分之一实测地形图",
        edition_note="1913年实测地图已零星出现「中关」雅化写法，证「中关」非1953年凭空创造，"
                     "而是近代测绘谐音雅化的历史沿革产物",
    ),
    HistoricalSource(
        id="src_xiding_miao_bei", title="重修西顶娘娘庙碑记",
        category=SourceCategory.EPIGRAPHY,
        issuing_body="清康熙内务府 / 顺天府",
        edition_note="蓝靛厂西顶广仁宫（碧霞元君庙）重修碑刻；"
                     "载四月庙会盛况与官帑修葺，为蓝靛厂庙会民俗与皇家香火一手石刻实证",
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
    # E9 大钟寺词条新补
    "御制觉生寺碑文": "敕建觉生寺碑文",
    "觉生寺碑": "敕建觉生寺碑文",
    "高宗御制诗文集": "清高宗御制诗文集",
    "袁宏道集": "袁中郎全集",
    "大钟寺博物馆馆史资料": "大钟寺古钟博物馆馆史资料",
    # E8/E2 桥类词条新补
    "历代职官表": "钦定历代职官表",
    "北平工务局桥梁档案": "北平市工务局郊区桥梁档案",
    "第二批名录": "三山五园地区传统地名保护名录（第二批）",
    "三山五园名录（第二批）": "三山五园地区传统地名保护名录（第二批）",
    # E5/E10/E12/E13 新补
    "八旬万寿盛典": "钦定八旬万寿盛典",
    "明会典": "大明会典",
    "京西图": "京西图（1913）",
    "西顶庙碑": "重修西顶娘娘庙碑记",
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
