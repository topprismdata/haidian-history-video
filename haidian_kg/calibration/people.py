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
        authored_source_ids=["src_ymy_sijifang"],
        haidian_relevance="乾隆十二年(1747)御制《圆明园四十景图咏》；"
                          "乾隆三十五年(1770)前后圆明、长春、绮春三园格局基本形成",
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
        authored_source_ids=["src_yuanshi"],
        official_titles=["御史大夫", "中书右丞相"],
        haidian_relevance="至正三年领修《元史》",
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
]
