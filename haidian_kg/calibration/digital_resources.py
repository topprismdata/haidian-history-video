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
                         "⚠️ API 端点待人工核验：网络检索给出的 "
                         "/tgaz/placename/{id}.json 实测 404（2026-10-02），"
                         "接入代码前必须先用浏览器确认真实接口，"
                         "不得对未验证的 API 契约写代码",
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
