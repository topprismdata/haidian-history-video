"""
haidian_kg/ontology/temporal.py
时间语义分层模型 (Temporal Semantics Layer)

整改依据（GPT 第1轮 P0-1 / P0-2 审查 + 第2轮时间语义审查）：
原 `ChronologicalPoint` 把四种完全不同的时间语义压进一个对象，导致
「乾隆十六年」「1751」「约770000 BP」「[-1046,-1045]」在查询层被当作同一种值。
本模块按 ISO 21127:2023 / CIDOC CRM 7.1.3 的 E2/E4/E52 语义重构。

设计原则（来自 CHGIS 冻结实例机制 + CIDOC CRM 时间模型）：
1. 历法纪年（ReignYear）与公历换算（GregorianDate）必须是两个独立对象，
   换算结果必须挂接权威换算基准（CalibrationTable），不允许裸存公历年。
2. 模糊年代用 DatePoint + UncertaintyRange 表达，绝不与确定年代共用字段。
3. 一切"持续存在"的东西挂 TimeSpan，一切"发生"的东西挂 DatePoint。
"""
from enum import Enum
from typing import List, Optional, Tuple
from pydantic import BaseModel, Field, validator


class Era(str, Enum):
    """标准历史断代（严格首尾无缝互斥）"""
    PREHISTORIC = "史前"          # 距今770万年 - 前1046
    PRE_QIN = "先秦"             # 前1046 - 前221
    QIN_HAN_NORTHERN = "秦汉魏晋南北朝"  # 前221 - 581
    SUI_TANG_FIVE_DYNASTIES = "隋唐五代"   # 581 - 938
    LIAO_JIN = "辽金"            # 938 - 1215
    YUAN = "元代"                # 1215 - 1368
    MING = "明代"                # 1368 - 1644
    QING = "清代"                # 1644 - 1912
    REPUBLIC = "民国"            # 1912 - 1949
    MODERN = "当代"              # 1949 - 今


class CalendarSystem(str, Enum):
    GREGORIAN = "公历"
    CHINESE_LUNISOLAR = "农历（夏正）"
    BP = "距今年代(BP)"          # 地质学测年惯例，BP=before present
    UNKNOWN = "纪年不详"


class CalibrationTable(str, Enum):
    """
    权威历法换算基准。绝不允许裸存公历年而无基准声明。
    GB/T 33661-2017《中华人民共和国的农历的编算和颁发》为中国大陆现行标准；
    紫金山天文台《中国天文年历》为清代以前换算的学界通行依据。
    """
    GB_T_33661_2017 = "GB/T 33661-2017 中华人民共和国农历编算和颁发"
    CN_ASTRONOMICAL_ALMANAC = "紫金山天文台《中国天文年历》"
    EARTH_VARVE_CHRONOLOGY = "湖泊年纹/冰芯等地质测年序列"
    UNCALIBRATED = "未校勘（学界通行换算）"


class ReignYear(BaseModel):
    """
    中国式纪年表达（CIDOC CRM E61 Time Primitive 的传统纪年形式）。
    例：「嘉平二年」「至元二十九年」「乾隆十六年」「七月癸未」
    关键约束：此对象只表达"文献怎么写的"，不做公历换算。
    """
    era: Era = Field(..., description="所属断代")
    reign_title: Optional[str] = Field(None, description="年号，如：嘉平、至元、乾隆")
    year_within_reign: Optional[int] = Field(None, description="年号内第几年，如：嘉平二年=2")
    lunar_month: Optional[int] = Field(None, description="农历月，如：七月=7")
    lunar_day: Optional[int] = Field(None, description="农历日")
    ganzhi: Optional[str] = Field(None, description="干支纪年，如：庚午、癸未")
    verbatim: str = Field(
        ...,
        description="文献原始纪年写法（一字不改），如：太平兴国四年七月癸未",
    )
    source_division_id: Optional[str] = Field(
        None, description="该纪年写法的出处篇卷ID（可溯源）"
    )


class GregorianDate(BaseModel):
    """
    公历换算结果。必须声明所用换算基准，否则不允许入库。
    """
    year: int = Field(..., description="公历年（负数为公元前；0年=公元前1年）")
    month: Optional[int] = Field(None, description="公历月 1-12")
    day: Optional[int] = Field(None, description="公历日 1-31")
    calendar: CalendarSystem = Field(CalendarSystem.GREGORIAN, description="该日期所属历法")
    calibration: CalibrationTable = Field(
        ..., description="换算所依据的权威历表"
    )
    uncertainty_years: Optional[int] = Field(
        None, description="换算不确定度（±年数），古本纪年常需推定朔闰"
    )

    @validator("uncertainty_years")
    def _non_negative_uncertainty(cls, v):
        if v is not None and v < 0:
            raise ValueError("【时态硬阻断】换算不确定度不得为负数")
        return v

    @validator("calibration")
    def _require_calibration(cls, v):
        """【历法硬阻断】公历换算必须声明权威基准，杜绝"裸公历年"入库"""
        if v == CalibrationTable.UNCALIBRATED:
            raise ValueError(
                "【历法硬阻断】公历换算结果必须声明权威历表基准！"
                "权威历表是带版本的证据来源，不是数据库隐藏的神谕函数。"
            )
        return v


class DatePoint(BaseModel):
    """
    离散时间点（CIDOC CRM E61 Time Primitive / P7 took place at the time-span）。
    用于「发生过的事件」。允许史前BP与考古测年。
    """
    id: str = Field(..., description="时间点唯一URI，如 dt_1771_qianlong16")
    label: str = Field(..., description="人类可读标签，如：乾隆十六年（1751）")
    reign_year: Optional[ReignYear] = Field(
        None, description="传统纪年表达（若有文献依据）"
    )
    gregorian: Optional[GregorianDate] = Field(
        None, description="公历换算结果（若可换算）"
    )
    bp_years: Optional[int] = Field(
        None, description="距今年代（史前专用），如：4000"
    )
    bp_calibration: Optional[CalibrationTable] = Field(
        None, description="BP测年所依据的地质/考古测年序列"
    )
    precision: str = Field(
        "day", description="时间精度: year / month / day / decade / century / approximate"
    )
    source_division_ids: List[str] = Field(
        default_factory=list,
        description="支撑该时间判定的全部篇卷ID（多出处需并存）",
    )
    conflicting_dates: List[str] = Field(
        default_factory=list,
        description="同期文献纪年互异时，其他候选DatePoint的ID（保留争议，不强行统一）",
    )


class TimeSpan(BaseModel):
    """
    时间区间（CIDOC CRM E52 Time-Span）。
    用于「持续存在」的历史实例：行政建制有效期、地名称谓有效期、水系形态有效期。
    CHGIS 铁律：任何一端不可知时用 None，绝不用 0 或 -9999 代替。
    """
    id: str = Field(..., description="时间区间唯一URI，如 ts_unit_wanping_938_1368")
    begin: Optional[DatePoint] = Field(None, description="起始时点（None=早于已知最早记录）")
    end: Optional[DatePoint] = Field(
        None, description="终止时点（None=至今仍存或下限不可知）"
    )
    label: str = Field(..., description="人类可读标签，如：938年-1368年")
    open_begin: bool = Field(False, description="起始是否开放（早于最早记录）")
    open_end: bool = Field(False, description="终止是否开放（至今仍存）")

    def overlaps(self, other: "TimeSpan") -> bool:
        """两个时间区间是否有重叠（时态检索核心算子）"""
        a_begin = -10**9 if (self.open_begin or self.begin is None) else self.begin.gregorian.year
        a_end = 10**9 if (self.open_end or self.end is None) else self.end.gregorian.year
        b_begin = -10**9 if (other.open_begin or other.begin is None) else other.begin.gregorian.year
        b_end = 10**9 if (other.open_end or other.end is None) else other.end.gregorian.year
        return a_begin <= b_end and b_begin <= a_end

    def contains(self, year: int) -> bool:
        a_begin = -10**9 if (self.open_begin or self.begin is None) else self.begin.gregorian.year
        a_end = 10**9 if (self.open_end or self.end is None) else self.end.gregorian.year
        return a_begin <= year <= a_end


class TemporalProcess(BaseModel):
    """
    渐变过程（CIDOC CRM E4 Period / P2 has sub-type，参照 CRMinf 的推理对象）。
    
    整改依据（GPT 第1轮 P0-1）：高梁→高粱的讹音传播、河道缓慢淤塞、村落范围逐渐扩展
    这些都【不存在可确定日期的离散事件】，绝不能硬塞进 HistoricalEvent。
    """
    id: str = Field(..., description="过程唯一URI，如 proc_gaoliang_phonetic_drift")
    process_type: str = Field(
        ...,
        description=(
            "过程类型: PHONETIC_DRIFT(语音讹变) / SILTATION(河道淤塞) / "
            "SPREAD(范围扩展) / SPOKEN_FORM_RISE(俗名兴起) / SPOKEN_FORM_DECAY(俗名消退) / "
            "HYDRAULIC_RECONNECT(水力连通改变) / ADMIN_RECLASSIFY(建制性质改变)"
        ),
    )
    subject_ids: List[str] = Field(..., description="作用对象ID列表")
    time_span: TimeSpan = Field(..., description="过程持续的时间区间")
    mechanism: str = Field(
        ...,
        description="演变机制说明（音变规律/淤积速率/扩界动因等）",
    )
    dating_basis: str = Field(
        ...,
        description="断代依据：必须说明为何只能给出区间而非确定年份（这是防伪核心）",
    )
    is_gradual: bool = Field(
        True, description="恒为True——若可确定日期应改用 HistoricalEvent"
    )
