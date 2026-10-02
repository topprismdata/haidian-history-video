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


class DigitalResourceKind(str, Enum):
    """
    数字资源性质（v2.1 新增）。

    关键学术纪律：转录本 ≠ 校勘本。
    维基文库/中国哲学书电子化计划提供的是【转录文本】，
    它们可用于「这段话在某转录本里怎么写」，但不能替代
    中华书局点校本这类【校勘本】的异文判断。
    混淆二者，等于把「网上抄的」当成「校勘过的」。
    """
    TRANSCRIPTION = "转录本"          # 维基文库/cts/cbeta：可用于引文定位
    COLLATED_EDITION = "校勘本"       # 中华书局点校本：可用于异文判断
    SCAN = "影印本"                   # 影印图像：有版式与字形信息
    GIS_DATASET = "地理数据集"         # CHGIS 等
    CATALOG = "联合目录"               # 仅作书目信息，不作文本依据


class DigitalResource(BaseModel):
    """
    数字资源记录（v2.1 新增）。

    为什么要独立成类而不是塞进一个 url 字符串：
    1. 同一部书常有多个数字版本（维基文库 + ctext + 影印），
       必须分别记录且各带性质标签
    2. 引文若只录书名卷次而无资源定位，审稿人无法一键复核
    3. 「转录本」与「校勘本」混用会产生伪校勘结论
    """
    id: str = Field(..., description="资源唯一URI")
    source_id: str = Field(..., description="所属典籍ID")
    kind: DigitalResourceKind = Field(..., description="资源性质")
    platform: str = Field(
        ..., description="承载平台，如：维基文库 / 中国哲学书电子化计划 / 国学大师"
    )
    url: str = Field(..., description="可点击定位地址")
    division_id: Optional[str] = Field(
        None, description="若该资源只覆盖特定篇卷，则指向具体篇卷"
    )
    accessed_at: Optional[DatePoint] = Field(
        None, description="核验日期（学术引用必填，便于复核者重访）"
    )
    reliability_note: str = Field(
        ...,
        description=(
            "可靠性说明（必填）：此资源可否用于异文判断？"
            "转录本须注明『未校勘，异文以点校本为准』"
        ),
    )
    is_citable_for_verbatim: bool = Field(
        ..., description="是否可作为逐字引文的正式依据"
    )

    @model_validator(mode="after")
    def _transcription_cannot_be_collated(self):
        """【学术红线】转录本不得被当作异文判断依据"""
        if self.kind == DigitalResourceKind.TRANSCRIPTION and self.is_citable_for_verbatim:
            # 允许引文定位，但必须在 note 中显式声明限制
            if "校勘" not in self.reliability_note and "点校本" not in self.reliability_note:
                raise ValueError(
                    "【G9数字资源】转录本若标为可作逐字引文依据，"
                    "必须在 reliability_note 中声明校勘限制（未校勘，异文以点校本为准）"
                )
        return self


class HistoricalSource(BaseModel):
    """
    文献实体（Level 1）—— 一部书就是一个节点，不得按篇卷重复建。

    【v2.1 整改】此前《钦定日下旧闻考》因卷72/卷99被建成两条、
    《清仁宗实录》因卷46/卷76被建成两条，导致：
      - 无法回答「这部书共有多少卷、成于何时、作者是谁」
      - 版本信息退化为一串自由文本，无法做版本互校
    正确做法：一部书 = 一个 HistoricalSource，篇卷挂在 SourceDivision 之下。
    """
    id: str = Field(..., description="文献唯一URI，如 src_shuijingzhu")
    title: str = Field(..., description="典籍全名（规范书名，不含卷次）")
    category: SourceCategory = Field(..., description="文献类别")
    author_person_id: Optional[str] = Field(
        None, description="作者人物ID（关联 HistoricalPerson 实体）"
    )
    compiler_person_ids: List[str] = Field(
        default_factory=list, description="编者/校订者人物ID列表"
    )
    compiled_time: Optional[TimeSpan] = Field(
        None, description="成书/修纂年代（清官书常多次纂修，须分段表达）"
    )
    total_volumes: Optional[int] = Field(
        None, description="总卷数（未知则留空，不得臆造）"
    )
    version_description: Optional[str] = Field(
        None, description="所据版本说明（自由描述）"
    )
    base_edition: Optional[str] = Field(
        None,
        description=(
            "底本类型：SISHU（四库全书本）/ ZHONGHUA（中华书局点校本）/ "
            "DAFANG（大藏经）/ 拓本 / 实测图 / 抄本 等"
        ),
    )
    edition_note: Optional[str] = Field(
        None, description="校勘依据与异文说明"
    )
    issuing_body: Optional[str] = Field(
        None,
        description=(
            "责任机构（机构编纂类文献必填，如：北京市规划自然资源委员会 / "
            "海淀区人民政府 / 中科院考古所）。官修正史无个人作者属正常，"
            "但机构书必须有责任方，否则无法问责"
        ),
    )
    url: Optional[str] = Field(
        None, description="数字资源地址（如维基文库/中国哲学书电子化计划条目）"
    )

    @model_validator(mode="after")
    def _source_needs_identity(self):
        """文献必须有规范书名与类别，否则无法作为一级实体参与溯源"""
        if not self.title.strip():
            raise ValueError("【G1文献】书名不得为空")
        if "卷" in self.title and any(ch.isdigit() for ch in self.title):
            # 允许「元史·河渠志」这类含志名的书，但不允许「钦定日下旧闻考卷72」
            if self.title.count("卷") >= 1 and "·" not in self.title:
                raise ValueError(
                    "【G1文献】书名不得含卷次：%s。卷次应归 SourceDivision，"
                    "一部书只能有一个 HistoricalSource 节点。" % self.title
                )
        return self


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
