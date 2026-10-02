"""
haidian_kg/ontology/epistemic.py
认识论分层与证据链模型 (Epistemic Layering)

整改依据（GPT 第1轮 + 第2轮审查）：
- P0: 「文献中确有此句」（文本事实层）与「我们因此相信此历史解释」（认识论信念层）
  混在同一个 AttestationEvidence 类里。系统会把古籍里的附会神话直接当 VERIFIED 事实入库。
- CIDOC CRM 官方本体本身不建模"信念"，但 CRMinf（CIDOC CRM for argumentation and
  inference）专门把 Proposition / Argument / Reasoning / BeliefValue / SourceAdoption 拆开。
  BHKG 既然定位为"防翻车闸门"，就必须采纳这一层。
- 负控制必须区分证伪强度：无证据 ≠ 不存在（absence of evidence ≠ evidence of absence）。

本模块严格分离三层：
  L-A 文本事实层 (TextualFact)     —— 文献原话确实这么写（可逐字核对）
  L-B 推理断言层 (Proposition)     —— 我们从文本推出的历史解释（可被推翻）
  L-C 信念采纳层 (BeliefAdoption)  —— 图谱当前采信哪条断言、置信度多少、谁采信
"""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, validator, model_validator

from .temporal import DatePoint, TimeSpan


class SourceCategory(str, Enum):
    """文献大类"""
    OFFICIAL_HISTORY = "正史"                    # 二十四史
    LOCAL_GAZETTEER = "地方志"                  # 《宛署杂记》《日下旧闻考》
    EPIGRAPHY = "金石"                          # 碑刻拓本（实物一手）
    GEOGRAPHICAL_TREATISE = "历史地理专著"       # 《水经注》
    LITERARY_COLLECTION = "文集笔记"            # 《中堂事记》
    ARCHAEOLOGY_REPORT = "考古发掘报告"
    MILITARY_SURVEY_MAP = "近代实测地图"         # 1913《京西图》
    ORAL_TRADITION = "口述访谈"                 # 民间口碑（最低等级）


class HistoricalSource(BaseModel):
    """文献实体（Level 1）"""
    id: str = Field(..., description="文献唯一URI，如 src_shuijingzhu")
    title: str = Field(..., description="典籍全名")
    category: SourceCategory = Field(..., description="文献类别")
    author_person_id: Optional[str] = Field(None, description="作者人物ID")
    compiled_time: Optional[TimeSpan] = Field(None, description="成书/修纂年代")
    version_description: Optional[str] = Field(
        None, description="版本说明（如：中华书局点校本《水经注疏》）"
    )
    author_id: Optional[str] = Field(
        None,
        description="作者人物ID（alias，保留以兼容旧数据；新数据用 author_person_id）",
    )


class SourceDivision(BaseModel):
    """文献篇卷实体（Level 2）—— 跨卷拼接的物理阻断点"""
    id: str = Field(..., description="篇卷唯一URI，如 div_sjz_vol13_luoshui")
    source_id: str = Field(..., description="所属典籍ID")
    volume_number: str = Field(..., description="卷数，如：卷十三、卷四、本纪第四")
    section_title: str = Field(..., description="篇名/志名，如：漯水、太宗一")
    parent_division_id: Optional[str] = Field(
        None, description="上级篇卷ID（支持卷→篇→条三级）"
    )


class TextualFact(BaseModel):
    """
    L-A 文本事实层：只声明"这段文字确实这样写"，不作任何真伪判断。

    这是防造假的底线：任何 verbatim_quote 必须能逐字回到某个 SourceDivision。
    """
    id: str = Field(..., description="文本事实唯一URI，如 tf_gaoliang_battle_taizong")
    division_id: str = Field(..., description="严格所属篇卷ID")
    verbatim_quote: str = Field(..., description="原典原文，一字不改")
    attested_string: str = Field(..., description="其中出现的关键实体字样")
    source_year: Optional[DatePoint] = Field(
        None, description="该文献本身的成书年代（不是引文所述事件的年代）"
    )
    translator_note: Optional[str] = Field(None, description="校勘记/异文说明")

    @validator("division_id")
    def _no_cross_volume(cls, v):
        """【防伪硬阻断】严禁跨卷拼接引文"""
        for sep in [",", "，", "&", "和", "及", "/"]:
            if sep in v:
                raise ValueError(
                    "【防伪硬阻断】严禁跨卷/跨篇拼接书证！"
                    "不同卷必须拆分为独立 TextualFact 节点！"
                )
        return v

    @validator("verbatim_quote")
    def _quote_not_empty(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError("【防伪硬阻断】引文不得为空或过短")
        return v


class EpistemicStatus(str, Enum):
    VERIFIED = "已确证"
    CONTESTED = "学术争议"
    FOLK_LEGEND = "民间附会"
    UNSUBSTANTIATED = "无据推论"       # ← 新增：无证据支撑的断言
    DISPROVEN = "已证伪"


class Proposition(BaseModel):
    """
    L-B 推理断言层：我们从某条文本事实推出的历史解释。

    关键：Proposition 可以被推翻；它的真伪取决于 BeliefAdoption 的采信状态。
    """
    id: str = Field(..., description="断言唯一URI")
    statement: str = Field(..., description="断言的完整陈述（可证伪的句子）")
    derived_from_fact_ids: List[str] = Field(
        ..., description="支撑本断言的 TextualFact ID 列表"
    )
    inferred_subject_id: Optional[str] = Field(
        None, description="断言所指向的空间/地名/事件实体ID"
    )
    inferred_time_span: Optional[TimeSpan] = Field(
        None, description="断言所指向的时间范围"
    )
    inference_method: str = Field(
        ...,
        description="推理方法（必须显式写出，是负控制审计的关键）",
    )
    alternative_explanations: List[str] = Field(
        default_factory=list,
        description="学界已有的其他解释（禁止只写一种解释）",
    )


class BeliefAdoption(BaseModel):
    """
    L-C 信念采纳层：图谱当前采信哪条断言、置信多少、依据是什么。

    这是 CRMinf 的核心：Propositions 是"可能的解释"，Adoption 才是"我们采信什么"。
    """
    proposition_id: str = Field(..., description="被采纳的断言ID")
    status: EpistemicStatus = Field(..., description="当前采信状态")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="置信度 0-1"
    )
    adopted_by: str = Field(..., description="采纳人/机构/规范")
    adopted_at: Optional[DatePoint] = Field(None, description="采纳时间")
    rationale: str = Field(..., description="采纳理由（必须说明为何不采信其他解释）")
    refuting_fact_ids: List[str] = Field(
        default_factory=list, description="反驳本断言的文本事实ID"
    )

    @model_validator(mode="after")
    def _disproven_needs_evidence(self):
        """
        【负控制硬约束】标记 DISPROVEN 必须有反驳证据，
        防止"无证据即断言不存在"的论证跳跃。
        """
        if self.status == EpistemicStatus.DISPROVEN and not self.refuting_fact_ids:
            raise ValueError(
                "【负控制硬阻断】标记为已证伪(DISPROVEN)必须提供反驳证据ID！"
                "无证据不等于不存在（absence of evidence ≠ evidence of absence）"
            )
        return self
