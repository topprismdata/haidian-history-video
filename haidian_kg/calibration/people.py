"""
haidian_kg/calibration/people.py
海淀史常用历史人物实体

存在意义：
  v2.1 之前，全部 12 条文献的 author_person_id 都是空的——
  沈榜写《宛署杂记》、王恽写《中堂事记》、郦道元注《水经注》、
  姚元之撰《竹叶亭杂记》，人物与文献完全断链。
  这意味着无法回答「这位人物在海淀做过什么、留下了什么一手记录」。

本模块只收录与海淀史直接相关、且已在交付档案中实际引用的人物。
生卒年不确定者留空并注明，不臆造。
"""
from typing import List, Optional

from pydantic import BaseModel, Field

from ..ontology.temporal import TimeSpan


class PersonRole(str):
    MONARCH = "Monarch"
    HYDRAULIC_ENGINEER = "HydraulicEngineer"
    LOCAL_MAGISTRATE = "LocalMagistrate"
    MILITARY_COMMANDER = "MilitaryCommander"
    SCHOLAR_WRITER = "ScholarWriter"
    RELIGIOUS_FIGURE = "ReligiousFigure"
    IMPERIAL_SERVANT = "ImperialServant"


class HistoricalPerson(BaseModel):
    """历史人物实体（BHKG 第5支柱）"""
    id: str = Field(..., description="人物唯一URI")
    name: str = Field(..., description="姓名（正史/档案用字）")
    courtesy_name: Optional[str] = Field(None, description="字/号")
    aliases: List[str] = Field(default_factory=list, description="异名/别称")
    dynasty: str = Field(..., description="生活朝代")
    life_span: Optional[TimeSpan] = Field(
        None, description="生卒年（不确定则留空，严禁臆造）"
    )
    primary_role: str = Field(..., description="主要历史角色")
    official_titles: List[str] = Field(
        default_factory=list, description="曾任官职（照档案原文，不作归纳）"
    )
    authored_source_ids: List[str] = Field(
        default_factory=list, description="所撰/所注/所编典籍ID"
    )
    haidian_relevance: str = Field(
        ...,
        description="与海淀的关联（须可溯源至具体档案，不作推测）",
    )
    note: Optional[str] = Field(None, description="存疑与考订按语")


PEOPLE: List[HistoricalPerson] = [
    HistoricalPerson(
        id="person_lidaoyuan", name="郦道元",
        dynasty="北魏", primary_role=PersonRole.SCHOLAR_WRITER,
        authored_source_ids=["src_shuijingzhu"],
        haidian_relevance="《水经注》卷十三记高梁水出蓟城西北平地泉，为高梁水最早完整水文学实录",
        note="《水经注》成书年代学界有异说，节点中未臆定",
    ),
    HistoricalPerson(
        id="person_qianlong", name="乾隆帝",
        dynasty="清代", primary_role=PersonRole.MONARCH,
        official_titles=["清高宗"],
        authored_source_ids=["src_ymy_sijifang", "src_qianlong_shiwenji"],
        haidian_relevance="乾隆十二年(1747)御制《圆明园四十景图咏》；"
                          "乾隆三十五年(1770)前后圆明、长春、绮春三园格局基本形成；"
                          "乾隆八年(1743)御制《觉生寺大钟诗》、十一年(1746)御制"
                          "《觉生寺大钟歌用沈德潜韵》，两诗分年、不得剪接",
        note="《四十景图咏》为御制，命画院绘图、词臣题咏，"
             "是景观定名的一手依据，具体绘图与题咏者另有其人",
    ),
    HistoricalPerson(
        id="person_chen_shu", name="陈寿",
        dynasty="西晋", primary_role=PersonRole.SCHOLAR_WRITER,
        authored_source_ids=["src_sanguozhi"],
        haidian_relevance="《三国志·魏书》载刘靖都督河北诸军事、开渠灌田事",
        note="《三国志》系陈寿撰；《魏书》为其《三国志》中魏书部分",
    ),
    HistoricalPerson(
        id="person_liujing", name="刘靖",
        dynasty="曹魏", primary_role=PersonRole.HYDRAULIC_ENGINEER,
        official_titles=["镇北将军", "假节", "都督河北诸军事"],
        authored_source_ids=[],
        haidian_relevance="嘉平二年(250)筑戾陵堰、开车箱渠，引水灌田岁二千顷",
        note="《三国志》作「都督河北诸军事」，非「督幽州」；"
             "灌田数历经二千/四千三百一十六/五千九百三十/万余顷诸说，"
             "须分年分阶段，不可收束为单一数字",
    ),
    HistoricalPerson(
        id="person_yuanweiyuan", name="王恽",
        dynasty="元代", courtesy_name="秋涧",
        primary_role=PersonRole.SCHOLAR_WRITER,
        official_titles=["翰林学士", "太常卿"],
        authored_source_ids=["src_zhongtang"],
        haidian_relevance="中统元年(1260)《中堂事记》首载「海店」，为海淀成镇最早确证",
    ),
    HistoricalPerson(
        id="person_owen_te", name="欧阳玄",
        dynasty="元代", primary_role=PersonRole.SCHOLAR_WRITER,
        authored_source_ids=["src_yuanshi"],
        official_titles=["翰林学士", "国子祭酒"],
        haidian_relevance="至正三年(1343)总裁《元史》，与脱脱同领修书",
        note="《元史》为官修纪传体，纪年换算以本纪为准",
    ),
    HistoricalPerson(
        id="person_tuotuo", name="脱脱",
        dynasty="元代", primary_role=PersonRole.SCHOLAR_WRITER,
        authored_source_ids=["src_yuanshi", "src_jinshi"],
        official_titles=["御史大夫", "中书右丞相"],
        haidian_relevance="至正三年(1343)领修《元史》；至正间又领修辽、金、宋三史，"
                          "《金史》所载承安三年(1198)「勿毀高梁河閘，從民灌溉」"
                          "为金代高梁河已有人工水闸的一手记录",
    ),
    HistoricalPerson(
        id="person_guoshoujing", name="郭守敬",
        courtesy_name="若思", dynasty="元代",
        primary_role=PersonRole.HYDRAULIC_ENGINEER,
        official_titles=["昭文馆大学士", "知太史院事"],
        authored_source_ids=[],
        haidian_relevance="至元二十九年(1292)开建通惠河，和义门外设西城闸，"
                          "引白浮泉水经瓮山泊入大都积水潭",
    ),
    HistoricalPerson(
        id="person_yaoxingzong", name="姚元之",
        dynasty="清代", primary_role=PersonRole.SCHOLAR_WRITER,
        authored_source_ids=["src_zyztj"],
        haidian_relevance="《竹叶亭杂记》卷一记嘉庆六年圆明园副将移驻树村，"
                          "为移驻实施时间的一手旁证",
    ),
    HistoricalPerson(
        id="person_shenbang", name="沈榜",
        dynasty="明代", primary_role=PersonRole.LOCAL_MAGISTRATE,
        official_titles=["宛平知县"],
        authored_source_ids=["src_wanshu"],
        haidian_relevance="万历年间任宛平知县，《宛署杂记》为海淀一带明代聚落与地名的一手账本",
    ),
    HistoricalPerson(
        id="person_chenyuan", name="陈垣",
        dynasty="近代", primary_role=PersonRole.SCHOLAR_WRITER,
        haidian_relevance="提出中关村名改自「中官村」之說（存疑，学界有争议）",
        note="其说与「董四墓—中官村」一线的研究相关，但非定论，"
             "视频中如引用须标学术争议",
    ),
    HistoricalPerson(
        id="person_yueshengyang", name="岳升阳",
        dynasty="当代", primary_role=PersonRole.SCHOLAR_WRITER,
        haidian_relevance="提出树村唐代称「蜀村」、金代称「蜀社」，"
                          "若音转成立则树村之名逾千年，「因树得名」不成立",
        note="底层文献（唐墓志？金代碑刻？）未能核到，「蜀村」「蜀社」"
             "在通行古籍库中检索不到 —— 只能作存疑待考，不可作史实",
    ),
    # ---------- E9 大钟寺词条（2026-10-02 入库） ----------
    HistoricalPerson(
        id="person_liudong", name="刘侗",
        dynasty="明代", primary_role=PersonRole.SCHOLAR_WRITER,
        authored_source_ids=["src_dijingjingwulue"],
        haidian_relevance="《帝京景物略》记大钟「向藏漢經廠」「日供六僧擊之」，"
                          "为钟履历链（汉经厂期、万寿寺期）的一手明录",
        note="与于奕正合撰，刘侗属文、于奕正采辑；生卒年异说，故不填",
    ),
    HistoricalPerson(
        id="person_yuyizheng", name="于奕正",
        dynasty="明代", primary_role=PersonRole.SCHOLAR_WRITER,
        authored_source_ids=["src_dijingjingwulue"],
        haidian_relevance="《帝京景物略》合撰者，采辑京师景物，万寿寺大钟条出其手",
        note="合撰分工：刘侗属文、于奕正采辑；生卒年异说，故不填",
    ),
    HistoricalPerson(
        id="person_liuruoyu", name="刘若愚",
        dynasty="明代", primary_role=PersonRole.IMPERIAL_SERVANT,
        authored_source_ids=["src_zuozhongzhi"],
        haidian_relevance="《酌中志》记「至於三十年後，於西直門外萬壽寺中建大鐘樓，"
                          "懸大鐘一口」「日夜撞不絕聲，云十萬八千杵」，"
                          "为万寿寺期钟事的一手宦官记述",
        note="明末内府宦官，自撰生平忆录；生卒不详，故不填",
    ),
    HistoricalPerson(
        id="person_jiangyikui", name="蒋一葵",
        dynasty="明代", primary_role=PersonRole.SCHOLAR_WRITER,
        authored_source_ids=["src_changankehua"],
        haidian_relevance="《长安客话》记万寿寺「寺有方鐘樓，前臨大道，樓僅容鐘」"
                          "与大钟「聲聞數十里……有異他鐘」，为万寿寺期形制与声闻一手记载",
        note="万历间人；具体仕履与生卒不详，故不填",
    ),
    HistoricalPerson(
        id="person_sunchengze", name="孙承泽",
        dynasty="明末清初", primary_role=PersonRole.SCHOLAR_WRITER,
        authored_source_ids=["src_chunmengmengyulu"],
        haidian_relevance="《春明梦余录》记德胜门东铸钟厂「舊鑄高二丈餘、闊一丈餘者，"
                          "尚有十數仆地上」，为大钟铸于铸钟厂（现代研究推断）的关键旁证",
        note="明崇祯进士、入清仕至吏部侍郎，顺治间退居；生卒有异说，故不填",
    ),
    HistoricalPerson(
        id="person_fuchadunchong", name="富察敦崇",
        dynasty="清代", primary_role=PersonRole.SCHOLAR_WRITER,
        authored_source_ids=["src_yanjingsuishiji"],
        haidian_relevance="《燕京岁时记》记觉生寺大钟殿「高五丈，下方上圓，四面皆窗，"
                          "後有旋梯，左升右降」，为大钟殿形制一手记载；"
                          "所记庙会民俗属民俗史料层",
        note="清末满洲人；生卒不详，故不填",
    ),
    HistoricalPerson(
        id="person_shendefu", name="沈德符",
        dynasty="明代", primary_role=PersonRole.SCHOLAR_WRITER,
        authored_source_ids=["src_wanliyehuobian"],
        haidian_relevance="《万历野获编》记万寿寺营建「浹歲即成」，证万历五年(1577)开工、"
                          "六年(1578)竣工跨年完成，堵「同年建成」误说",
        note="万历间人；生卒不详，故不填",
    ),
    HistoricalPerson(
        id="person_hezhongshi", name="贺仲轼",
        dynasty="明代", primary_role=PersonRole.IMPERIAL_SERVANT,
        authored_source_ids=["src_lianggongdingjianji"],
        haidian_relevance="《两宫鼎建记》记明代搬运巨料「每里掘一井，以澆旱船、資渴飲」"
                          "「比時天寒地凍，正宜趁時發運」，为「冰道运钟」传说之方法旁证"
                          "（所记为大石料运输，非此钟本身）",
        note="万历间以荫入仕、预两宫营建事；生卒不详，故不填",
    ),
    HistoricalPerson(
        id="person_yuanhongdao", name="袁宏道",
        dynasty="明代", primary_role=PersonRole.SCHOLAR_WRITER,
        authored_source_ids=["src_yuanzhonglang"],
        haidian_relevance="《万寿寺观文皇旧钟》诗「道傍觀者肩相摩，車騎數月猶馳逐」记移钟"
                          "盛况；「外書佛母萬真言，內寫雜花八十軸」与实物铭文不符，"
                          "为「华严钟」讹名至晚明已流传的一手证据",
        note="万历间公安派领袖。其描述与实物不符，只能说明名实相左，"
             "不得替他编造「未入钟内观察」之类过程",
    ),
    HistoricalPerson(
        id="person_yongzheng", name="雍正帝",
        dynasty="清代", primary_role=PersonRole.MONARCH,
        official_titles=["清世宗"],
        authored_source_ids=["src_jueshengsi_beiwen"],
        haidian_relevance="雍正十一年(1733)正月敕建觉生寺于西直门外曾家庄，十二年(1734)冬"
                          "告成、御制碑文赐名「觉生寺」；十一年四月已允内务府移钟之奏",
        note="开工(1733)与赐名(1734)分属两年，碑文载选址与取名依据，不得混写同年",
    ),
    # ---------- E8高梁桥 / E2安河桥 桥类词条（2026-10-02 入库） ----------
    HistoricalPerson(
        id="person_zhangwei", name="张暐",
        dynasty="金代", primary_role=PersonRole.SCHOLAR_WRITER,
        official_titles=["礼部尚书"],
        authored_source_ids=["src_dajinjili"],
        haidian_relevance="主持进呈《大金集礼》（明昌六年，1195），金代官修礼制典章总集；"
                          "与《金史》互证金代高梁河水系官营管理制度背景",
        note="生卒不详，故不填；纂修起于大定间一说并存",
    ),
    HistoricalPerson(
        id="person_zhou_sun", name="周损",
        dynasty="明代", primary_role=PersonRole.SCHOLAR_WRITER,
        authored_source_ids=["src_dijingjingwulue"],
        haidian_relevance="《帝京景物略》编辑成书者（刘侗、于奕正同撰，周损编辑）；"
                          "书载「歲清明……都人踏青高梁橋」，为高梁桥明清踏青盛况一手明录",
        note="E8复查红线：《帝京景物略》不得说成刘侗一人所撰；生卒不详，故不填",
    ),
    # ---------- E5一亩园 / E10蓝靛厂 / E12苏州街 / E13中关村 词条入库（2026-10-02） ----------
    HistoricalPerson(
        id="person_bangu", name="班固",
        dynasty="东汉", primary_role=PersonRole.SCHOLAR_WRITER,
        official_titles=["中郎将", "玄武司马"],
        authored_source_ids=["src_hanshu"],
        haidian_relevance="《汉书》卷三《高后纪第三》高后八年（前180）载「诸中官、宦者令、丞皆赐爵"
                          "关内侯」，为「中官」代指宦官的上古正典词源依据（卷次据点校本核订）；"
                          "中关村原名中官村即源于明清太监公共义地",
        birth_year=32, death_year=92,
    ),
    HistoricalPerson(
        id="person_zhaolian", name="昭梿",
        dynasty="清代", primary_role=PersonRole.SCHOLAR_WRITER,
        official_titles=["礼亲王"],
        authored_source_ids=["src_xiaoting_zalu"],
        haidian_relevance="《啸亭杂录》卷十明确系年乾隆二十六年辛巳（1761）崇庆皇太后七旬圣寿"
                          "建万寿寺外买卖街（苏州街），为苏州街始建年代最硬清人笔记一手依据",
        birth_year=1776, death_year=1829,
    ),
    HistoricalPerson(
        id="person_zhenjun", name="震钧",
        dynasty="清末民初", primary_role=PersonRole.SCHOLAR_WRITER,
        authored_source_ids=["src_tianzhi_ouwen"],
        haidian_relevance="《天咫偶闻》卷九（郊坰）载万寿寺外买卖街「今已毁尽」，为苏州街咸丰十年后"
                          "最终荒废状态的一手清末民人观察纪实（卷次据维基文库核订）",
        birth_year=1857, death_year=1920,
    ),
    HistoricalPerson(
        id="person_agui", name="阿桂",
        dynasty="清代", primary_role=PersonRole.SCHOLAR_WRITER,
        official_titles=["武英殿大学士", "军机大臣"],
        authored_source_ids=["src_baxun_wanshou"],
        haidian_relevance="总纂《八旬万寿盛典》（乾隆五十七年，1792），图绘一亩园为"
                          "圆明园大宫门前附属院落、后勤及临时住舍，反转「皇帝亲耕田」民间传说",
        birth_year=1717, death_year=1797,
    ),
    HistoricalPerson(
        id="person_hourenzhi", name="侯仁之",
        dynasty="现代", primary_role=PersonRole.SCHOLAR_WRITER,
        official_titles=["中科院院士", "北京大学教授"],
        haidian_relevance="考证中关村地处永定河故道水湾地势、早期记作「中湾儿」；"
                          "开创北京历史地理学科，奠定三山五园水系与海淀聚落沿革学术基石",
        birth_year=1911, death_year=2013,
    ),
    # ---- E20 勺园·淑春园 词条新增（新增一手文献的作者，G9 一书一条配套） ----
    HistoricalPerson(
        id="person_xuefucheng", name="薛福成",
        dynasty="清末", primary_role=PersonRole.SCHOLAR_WRITER,
        official_titles=["都察院左副都御史", "驻英法意比四国公使"],
        authored_source_ids=["src_yongan_biji"],
        haidian_relevance="《庸庵笔记》卷三录《查抄和珅住宅花园清单》：花园一座楼台四十二所、"
                          "钦赐花园一座亭台六十四所——两条查抄口径的传世转录层，严禁与他档房数加总",
    ),
    HistoricalPerson(
        id="person_yixuan", name="奕譞",
        dynasty="清代", primary_role=PersonRole.SCHOLAR_WRITER,
        official_titles=["醇亲王"],
        authored_source_ids=["src_jiusitang_shigao"],
        haidian_relevance="《九思堂诗稿》卷七《中秋后二日游舒春園四律》序「是園乾隆年間屬和相珅，"
                          "籍沒後入官……後輾轉為睿邸園寓」，为和珅园→睿王园流转的时人追述；"
                          "蔚秀园主人游邻园咏《石舫》《孤屿》，为石舫清中后期尚存的咏物证据",
    ),
]
