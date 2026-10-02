"""
haidian_kg/calibration/digital_resources.py
海淀史一手文献的数字资源登记（可复核定位）

学术纪律（本模块存在的原因）：
1. **引文必须可一键复核**。只记书名卷次，审稿人无法验证。
2. **转录本 ≠ 校勘本**。维基文库/ctext 提供的是转录文本，
   可用于「这段话在某转录本里怎么写」，但**不能替代点校本做异文判断**。
   混淆二者 = 把「网上抄的」当成「校勘过的」，会产生伪校勘结论。
3. **核验日期必填**。数字资源会变、会删，学术引用须记访问时间。
4. **卷数等硬数据必须核实**。本次即发现
   《钦定八旗通志》实为356卷（卷首12 + 志269 + 表71），
   先前凭印象写的「250卷」已作废。

所有 URL 均来自实际检索结果，未凭空构造。
"""
from typing import Dict, List, Optional

from ..ontology.epistemic import DigitalResource, DigitalResourceKind
from ..ontology.temporal import CalibrationTable, DatePoint, GregorianDate

CAL = CalibrationTable.CN_ASTRONOMICAL_ALMANAC
SISHU_NOTE = "四库全书底本转录，未校勘；异文判断以中华书局点校本为准"


def _accessed(tag="dr_checked"):
    return DatePoint(id=tag, label="2026-10-02", precision="day",
                     gregorian=GregorianDate(year=2026, month=10, day=2,
                                             calibration=CAL))


RESOURCES: List[DigitalResource] = [
    # ---------- 专业历史地名词库（候选裁决权威依据）----------
    # 多源调研结论(.superpowers/sdd/gazetteer-survey.md)三档架构:
    #   古今夹逼(CCVG+TGAZ) / 异源裁决(DILA) / 同源确认(CCTS)
    DigitalResource(
        id="dr_ccvg_data",
        source_id="src_ccvg",
        kind=DigitalResourceKind.CATALOG,
        platform="匹兹堡大学 Chinese Village Data",
        url="https://www.chinesevillagedata.library.pitt.edu/",
        accessed_at=_accessed(),
        reliability_note="2,601 行政村 CSV（2022-11，源 2,701 村志），开放数据；"
                         "无 API，CSV 批量下载（Pitt D-Scholarship 存档）；"
                         "接入方式：一次性下载建本地倒排索引（零 API 成本）；"
                         "当代村志与 TGAZ 历史政区构成古今夹逼裁决",
        is_citable_for_verbatim=False,
    ),
    DigitalResource(
        id="dr_dila_place",
        source_id="src_dila",
        kind=DigitalResourceKind.CATALOG,
        platform="法鼓文理学院 DILA authority",
        url="https://authority.dila.edu.tw/place",
        accessed_at=_accessed(),
        reliability_note="佛典地名权威档，Web Services API + KML + 开放下载，"
                         "免注册；与 CHGIS 视角完全独立（异源裁决），"
                         "寺庙/山泉类地名有独立考证价值",
        is_citable_for_verbatim=False,
    ),
    DigitalResource(
        id="dr_ccts_api",
        source_id="src_ccts",
        kind=DigitalResourceKind.GIS_DATASET,
        platform="中研院 CCTS",
        url="https://ccts.sinica.edu.tw",
        accessed_at=_accessed(),
        reliability_note="地名整合检索 API + OGC WMTS（depositar.io 托管）；"
                         "与 TGAZ 同宗谭图、独立实现——同源确认档；"
                         "endpoint 公开程度与授权细节接入前须再核",
        is_citable_for_verbatim=False,
    ),
    DigitalResource(
        id="dr_ccts_mhpname",
        source_id="src_ccts_mhpname",
        kind=DigitalResourceKind.CATALOG,
        platform="中研院 CCTS 专题研究",
        url="https://ccts.sinica.edu.tw/mhpname.html",
        accessed_at=_accessed(),
        reliability_note="61,685 个明代县级以下微观地名（村/庄/店/寨/桥/闸/铺/堡等），"
                         "WMTS 图层 ad1582_10_2s；非开放许可证（用户协议禁止再授权/转让）；"
                         "纪律：作为 reference-only match 对照（仅存外部匹配证据与 URI），"
                         "禁止全量复制入可再发布的正式 KB",
        is_citable_for_verbatim=False,
    ),
    DigitalResource(
        id="dr_mcgd_zenodo",
        source_id="src_mcgd",
        kind=DigitalResourceKind.GIS_DATASET,
        platform="Zenodo (Aix-Marseille / ERC ENP-China)",
        url="https://zenodo.org/records/14938699",
        accessed_at=_accessed(),
        reliability_note="47.3 万条地名与异名记录 CSV 批量下载；"
                         "优势：中文名与近代外文（英法）历史转写对应同一 Location ID；"
                         "用于近代西文史料地名消歧与异名归一（正式摄入前核验 License）",
        is_citable_for_verbatim=False,
    ),
    DigitalResource(
        id="dr_tgaz_api",
        source_id="src_tgaz",
        kind=DigitalResourceKind.CATALOG,
        platform="复旦大学 TGAZ（CHGIS 时空地名辞典）",
        url="https://tgaz.fudan.edu.cn/",
        accessed_at=_accessed(),
        reliability_note="学术权威时空地名库（CHGIS 项目），"
                         "用于候选地名裁决：命中即获独立书目佐证；"
                         "仅作书目与时空定位参考，不替代一手书证的逐字引文。"
                         "✅ REST API 验证可用（tgaz.fudan.edu.cn/tgaz/indexAPI.html）："
                         "搜索 GET /tgaz/placename?fmt=json&n=<UTF8名>，"
                         "精准 GET /tgaz/placename/json/hvd_<id>；"
                         "前缀 LIKE 匹配，繁简均收，license CC BY-NC 4.0。"
                         "CHGIS 1820 与 1911 年层包含县级以下聚落（如 1911 宛平县「西大營」，类型「村镇」）；"
                         "实测：萬壽寺 1 命中、西山 19 命中、樹村 0（未命中不否决）",
        is_citable_for_verbatim=False,
    ),
    DigitalResource(
        id="dr_chgis_data",
        source_id="src_chgis",
        kind=DigitalResourceKind.GIS_DATASET,
        platform="哈佛 CHGIS 官方数据区",
        url="https://chgis.fas.harvard.edu/",
        accessed_at=_accessed(),
        reliability_note="GIS 政区边界与居民点数据集，学术免费（CC BY-NC 类）；"
                         "用于空间对齐与断代核查，不作为文字引文依据",
        is_citable_for_verbatim=False,
    ),
    # ---------- 维基文库（四库全书本转录）----------
    DigitalResource(
        id="dr_bqtz_ws_root",
        source_id="src_bqtz",
        kind=DigitalResourceKind.TRANSCRIPTION,
        platform="维基文库",
        url="https://zh.wikisource.org/wiki/欽定八旗通志_(四庫全書本)",
        accessed_at=_accessed(),
        reliability_note=SISHU_NOTE,
        is_citable_for_verbatim=True,
    ),
    DigitalResource(
        id="dr_bqtz_ws_v292",
        source_id="src_bqtz",
        kind=DigitalResourceKind.TRANSCRIPTION,
        platform="维基文库",
        url="https://zh.wikisource.org/wiki/%E6%AC%BD%E5%AE%9A%E5%85%AB%E6%97%97%E9%80%9A%E5%BF%97_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B7292",
        division_id="div_bqtz116_yingjian",
        accessed_at=_accessed(),
        reliability_note=SISHU_NOTE,
        is_citable_for_verbatim=True,
    ),
    DigitalResource(
        id="dr_bqtz_ctext",
        source_id="src_bqtz",
        kind=DigitalResourceKind.TRANSCRIPTION,
        platform="中国哲学书电子化计划",
        url="https://ctext.org/wiki.pl?if=en&chapter=590961&remap=gb",
        accessed_at=_accessed(),
        reliability_note="ctext 转录本，未校勘；仅用于交叉比对字句，不作异文依据",
        is_citable_for_verbatim=True,
    ),
    # ---------- 书目信息 ----------
    DigitalResource(
        id="dr_bqtz_dpm",
        source_id="src_bqtz",
        kind=DigitalResourceKind.CATALOG,
        platform="故宫博物院数字文物库",
        url="https://www.dpm.org.cn/lemmas/243997.html",
        accessed_at=_accessed(),
        reliability_note="仅用于书目信息（作者、成书、卷数），不作文本依据",
        is_citable_for_verbatim=False,
    ),
]

#: 书名 → 资源ID 速查
RESOURCE_INDEX: Dict[str, List[str]] = {}
for _r in RESOURCES:
    RESOURCE_INDEX.setdefault(_r.source_id, []).append(_r.id)


def resources_for(source_id: str) -> List[DigitalResource]:
    return [r for r in RESOURCES if r.source_id == source_id]
