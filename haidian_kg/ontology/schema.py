"""
haidian_kg/ontology/schema.py
海淀历史地名知识图谱核心实体与数据模式规范 (Pydantic models)
符合 Python 3.9+，严格定义四分法实体、演变事件与六级证据枚举。
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class EvidenceLevel(str, Enum):
    """六级认识论证据分层"""
    L1_ARCHAEOLOGICAL = "Level 1 (考古硬证据)"
    L2_PRIMARY_DOC = "Level 2 (一手官刻金石)"
    L3_GAZETTEER = "Level 3 (正史方志纪实)"
    L4_MODERN_SCHOLARSHIP = "Level 4 (近代学界考订)"
    L5_FOLK_LEGEND = "Level 5 (民间口碑传说)"
    L6_DISPROVEN = "Level 6 (明确证伪伪说)"


class EpistemicStatus(str, Enum):
    """认识论确证状态"""
    VERIFIED = "VERIFIED"        # 考据确证
    CONTESTED = "CONTESTED"      # 学术争议/多说并存
    FOLK_LEGEND = "FOLK_LEGEND"  # 民间附会/非真实历史
    # 无据推论：**查无著录**（连来源都不存在），既非证伪、也非多说并存。
    # 🔴 不得用 CONTESTED 代替——那会把「不存在材料」误读成「学界有争议」，
    #    即 absence of evidence ≠ evidence of absence 的反面。
    #    2026-10-04 补：本成员此前只存在于同名 enum ontology/epistemic.py，
    #    schema.py 漏定义导致 extractor 等 schema 侧调用方 AttributeError。
    UNSUBSTANTIATED = "UNSUBSTANTIATED"  # 无据推论/查无著录（未进入可采信层）
    DISPROVEN = "DISPROVEN"      # 已证伪/伪假说（负控制断言）


class PhysicalFeatureEntity(BaseModel):
    """核心四分法之一：物理空间地物 (Phenomenal Place)"""
    id: str = Field(..., description="实体唯一URI标识符，如 feat_wanquanhe")
    label: str = Field(..., description="地物中文标准名称")
    feature_type: str = Field(..., description="地物类别: Watercourse, Wetland, TerrainElevation, HydraulicFacility")
    coordinates: Optional[List[float]] = Field(None, description="[经度, 纬度] WGS84")
    description: Optional[str] = Field(None, description="地质/水文空间描述")


class AdministrativeUnitEntity(BaseModel):
    """核心四分法之二：建置制度实体 (Declarative Place)"""
    id: str = Field(..., description="建置实体唯一URI，如 unit_shisanqi_garrison")
    label: str = Field(..., description="建置官方名称")
    unit_type: str = Field(..., description="建制类别: Settlement, MilitaryGarrison, ImperialGarden, ReligiousSite, BurialGround, ModernInstitution")
    located_at_feature_id: Optional[str] = Field(None, description="关联的物理地物实体ID")
    valid_start_year: Optional[int] = Field(None, description="建制始设公元年份")
    valid_end_year: Optional[int] = Field(None, description="建制裁撤公元年份")
    description: Optional[str] = Field(None, description="建制职责与辖域背景")


class ToponymEntity(BaseModel):
    """核心四分法之三：地名称号实体 (Appellation)"""
    id: str = Field(..., description="地名唯一URI，如 top_haidian")
    standard_form: str = Field(..., description="规范中文汉字书写")
    script_hanzi: str = Field(..., description="历史汉字字形")
    phonetic_pinyin: Optional[str] = Field(None, description="汉语拼音")
    name_type: str = Field("standard", description="地名性质: standard, vulgar(俗名), euphemistic(雅化名), official(官方赐名), folk(民间传说名)")
    associated_unit_id: Optional[str] = Field(None, description="所指称的建置/功能实体ID")
    predecessor_toponym_id: Optional[str] = Field(None, description="直接承袭的前序地名ID")


class PlaceAttestationEntity(BaseModel):
    """核心四分法之四：史料书证凭证实体 (Place Attestation as First-class Node)"""
    id: str = Field(..., description="书证凭证唯一URI，如 attest_haidian_1260")
    toponym_id: str = Field(..., description="见载的地名实体ID")
    attested_name: str = Field(..., description="文献中出现的字样文本")
    source_title: str = Field(..., description="文献书名/碑刻名，如《中堂事记》")
    source_author: Optional[str] = Field(None, description="文献作者/立碑主体")
    recorded_year: Optional[int] = Field(None, description="成书/刻立/事件公元年份")
    dynasty: str = Field(..., description="历史断代纪年，如 元代（中统元年）")
    quote: str = Field(..., description="文献原始文句引文")
    evidence_level: EvidenceLevel = Field(..., description="六级证据分层")
    epistemic_status: EpistemicStatus = Field(EpistemicStatus.VERIFIED, description="确证状态")
    notes: Optional[str] = Field(None, description="考据学按语或反驳说明")


class ToponymEventEntity(BaseModel):
    """地名演变生命周期事件"""
    id: str = Field(..., description="事件唯一URI，如 evt_rename_liulangzhuang")
    event_type: str = Field(..., description="事件类型: CreationEvent, ImperialNamingEvent, PhoneticShiftEvent, EuphemisticRenamingEvent, FolkAppropriationEvent, AdministrativeShiftEvent, SpatialExtinctionEvent")
    source_toponym_id: Optional[str] = Field(None, description="演变前地名ID")
    target_toponym_id: str = Field(..., description="演变后地名ID")
    dynasty: Optional[str] = Field(None, description="事件发生朝代")
    occurred_year: Optional[int] = Field(None, description="公元年份")
    description: str = Field(..., description="演变动因与历史经过说明")
    triggering_person: Optional[str] = Field(None, description="改名触发者（如乾隆帝、陈垣）")


class CompetingHypothesisEntity(BaseModel):
    """地名渊源争议假说"""
    id: str = Field(..., description="假说唯一URI，如 hypo_taizhouwu_tang")
    toponym_id: str = Field(..., description="关联地名ID")
    hypothesis_title: str = Field(..., description="假说简题")
    claim_summary: str = Field(..., description="核心论点叙述")
    supported_by_attestation_ids: List[str] = Field(default_factory=list, description="支持该说的书证ID列表")
    disproven_by_attestation_ids: List[str] = Field(default_factory=list, description="证伪/反驳该说的证据ID列表")
    confidence_status: EpistemicStatus = Field(..., description="假说当前置信状态: VERIFIED, CONTESTED, DISPROVEN")
