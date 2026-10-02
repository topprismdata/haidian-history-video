"""
haidian_kg/ontology/spatiotemporal.py
历时空间层：Persistent Entity / HistoricalFeatureState / 身份连续性断言

整改依据（GPT 第3轮实战压力测试 P0-5 ~ P0-8）：

第3轮三案例击穿了 v2.0 的 SpatialEntity + ToponymEvolution 粒度：
  案例1 长河：同一水系跨1500年多次人工改造，"是不是同一条河"本身是历史命题
  案例2 圆明园：名称变化≠空间并入≠园林新建≠集合形成；1860焚毁≠地点消亡
  案例3 高梁桥：字符串"高梁桥"同时是桥梁/街道/站名/战场误植，名称绝不能承担消歧

核心工程原则（第3轮原话）：
  历史实体的 identity 可以延续，但所有可见属性都必须属于带时间的 state；
  视频生成永远消费 state，不直接消费 entity。

本模块因此把几何、材质、功能、水文连接、空间组成全部从 Entity 下沉到 State。
"""
from enum import Enum
from typing import List, Optional, Tuple
from pydantic import BaseModel, Field, model_validator, ConfigDict

from .temporal import TimeSpan
from .epistemic import EpistemicStatus


class PhysicalThingKind(str, Enum):
    """
    现实地物类型（CIDOC CRM E18 Physical Thing / E24 Human-Made Thing / E26 Physical Feature）。
    关键：河流/桥梁/宫苑是 PhysicalThing，Place 只是它占据的空间范围。
    """
    NATURAL_WATERCOURSE = "天然水道"
    HUMAN_MADE_CHANNEL = "人工渠道"
    HYDRAULIC_STRUCTURE = "水工建筑物"       # 闸、坝、桥
    MOUNTAIN = "山阜"
    SETTLEMENT_AREA = "聚落占地"
    GARDEN_COMPLEX = "园林建筑群"
    FORTIFIED_CAMP = "营垒"
    RELIGIOUS_PRECINCT = "寺院道场"
    TOMB_CLUSTER = "墓葬群"
    MODERN_INSTITUTION = "近代机构建筑"
    # E9大钟寺词条入库新增：器物与皇家厂坊此前无对应类别，
    # 把永乐大钟错挂"寺院道场"、把汉经厂/铸钟厂错挂"近代机构建筑"都会污染 kind 语义。
    # 依据 CIDOC CRM E18 Physical Thing 下属 E22 Human-Made Object 划出：
    HUMAN_MADE_ARTIFACT = "人工器物"            # 可移动人工器物（E22），如永乐大钟
    IMPERIAL_WORKSHOP = "皇家厂坊"              # 御用厂坊机构及其占地，如汉经厂、铸钟厂
    # E8高梁桥/E2安河桥词条入库新增：古战场与官仓此前无对应类别，
    # 把979高梁河之战战场地望错挂"聚落占地"、把丰益仓错挂"皇家厂坊"都会污染 kind 语义。
    HISTORIC_BATTLEFIELD = "古战场"             # 历史战役战场地望，如979年高梁河之战（与后世桥闸分属不同实体）
    STATE_GRANARY = "官仓"                      # 国家/八旗仓储机构及其占地，如丰益仓


class PersistentSpatialEntity(BaseModel):
    """
    持续存在的空间实体（Persistent Entity）—— 只承载"身份"，不承载任何可见属性。

    严禁在此挂载：坐标、材质、功能、上下游、相邻。
    这些全部属于 HistoricalFeatureState。

    【关键实现约束】model_config extra="forbid"：
    Pydantic 默认会【静默丢弃】未声明字段——那意味着传了 material= 也不报错，
    数据无声消失。实体层必须直接拒绝任何额外属性，否则"属性该下沉到 State"
    这条架构红线形同虚设。
    """
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="实体唯一URI，如 ent_gaoliang_watercourse")
    kind: PhysicalThingKind = Field(..., description="现实地物类型")
    canonical_label: str = Field(..., description="工作用规范标签（不作为消歧依据）")
    supersedes_ids: List[str] = Field(
        default_factory=list, description="被本实体取代的前身实体ID"
    )

    @model_validator(mode="after")
    def _no_state_attributes(self):
        """【架构硬阻断】实体上不得出现任何可见属性——它们属于 State"""
        forbidden = {"geometry", "material", "function", "wgs84_coord",
                     "upstream_of", "downstream_of", "adjacent_to", "part_of"}
        leaked = forbidden & set(self.model_fields_set)
        if leaked:
            raise ValueError(
                "【架构硬阻断】PersistentSpatialEntity 不得携带可见属性 %s！"
                "几何/材质/功能/拓扑必须下沉到 HistoricalFeatureState。" % sorted(leaked)
            )
        return self


class FeatureState(str, Enum):
    """单条状态的可见属性属性集（全部带时间）"""
    GEOMETRY = "几何形态"
    MATERIAL = "材质形制"
    FUNCTION = "功能用途"
    HYDRAULIC_LINKAGE = "水文连通"
    SPATIAL_COMPOSITION = "空间组成"
    ADMINISTRATIVE_STATUS = "行政性质"
    VISUAL_CONSTRAINT = "视觉约束"


class HistoricalFeatureState(BaseModel):
    """
    历时状态（P0-5 核心新增）：某个实体在某个时间区间内的一组确定属性。

    这是视频管线唯一应当消费的对象。
    元初通惠河闸坝为求速成先用木构，《元史·河渠志》载至大四年（1311）始议砖石修治、
    泰定四年（1327）告成——因此"这个闸在某个具体年份能不能画成石头"是 State 问题，
    不是 Entity 问题。绝不能由"1311 年朝廷开始改石"推出"1312 年此闸必为石闸"。
    """
    id: str = Field(..., description="状态唯一URI，如 st_xichengzha_1292_wood")
    entity_id: str = Field(..., description="所属持续实体ID")
    time_span: TimeSpan = Field(..., description="该状态的生效区间")
    geometry: Optional[str] = Field(None, description="几何形态描述，如：双孔平板石闸")
    material: Optional[str] = Field(None, description="材质形制，如：木构/素面条石")
    function: Optional[str] = Field(None, description="功能用途，如：调节瓮山泊下泄积水潭")
    upstream_entity_ids: List[str] = Field(
        default_factory=list, description="上游连通的实体ID（时态有效）"
    )
    downstream_entity_ids: List[str] = Field(
        default_factory=list, description="下游连通的实体ID（时态有效）"
    )
    member_of_aggregate_ids: List[str] = Field(
        default_factory=list, description="所属空间集合ID（如圆明三园）"
    )
    admin_status: Optional[str] = Field(None, description="行政性质，如：在京畿/隶属宛平县")
    evidence_fact_ids: List[str] = Field(
        default_factory=list, description="支撑本状态的文本事实ID"
    )

    @model_validator(mode="after")
    def _needs_evidence(self):
        """【负控制】状态必须有证据，否则形制断言就是凭空的"""
        if not self.evidence_fact_ids:
            raise ValueError(
                "【负控制硬阻断】HistoricalFeatureState 必须挂接至少一条文本事实证据！"
                "否则形制/材质断言将成为无据推论。"
            )
        return self


class IdentityRelation(str, Enum):
    """历时身份连续性关系类型（P0-6）"""
    SAME_CONTINUANT = "同一持续体"          # 水体系统视为延续
    PARTIAL_CONTINUATION = "部分延续"       # 水系延续但原河槽已废弃
    SUCCESSOR = "继承者"                    # 后来者接续前身
    REPLACED_BY = "被取代"                 # 原物消失他物代之
    SPLIT = "分裂"
    MERGE = "合并"
    UNCERTAIN = "存疑"                     # 学术争议中


class DiachronicIdentityAssertion(BaseModel):
    """
    历时身份断言（P0-6 核心新增）：把"是不是同一个"变成可被证伪的历史命题。

    "这是同一条河"从来不是数据库的原始真理，而是需要证据支撑、
    且允许学界争议（CONTESTED）的历史地理学命题。
    """
    id: str = Field(..., description="身份断言URI，如 dia_gaoliang_same_continuant")
    subject_entity_ids: List[str] = Field(..., description="被断言为同一/延续的实体ID列表")
    relation: IdentityRelation = Field(..., description="身份关系类型")
    time_span: TimeSpan = Field(..., description="该身份关系成立的区间")
    evidence_fact_ids: List[str] = Field(
        ..., description="支撑该身份判定的文本事实ID"
    )
    status: EpistemicStatus = Field(..., description="学术采信状态（可为CONTESTED）")
    alternative_relations: List[str] = Field(
        default_factory=list, description="学界其他解释（禁止只写一种）"
    )
    is_orthogonal_to_state_change: bool = Field(
        True,
        description=(
            "恒为True：身份可延续而属性全变，或属性微变而身份存疑——两者正交"
        ),
    )

    @model_validator(mode="after")
    def _uncertain_needs_both_sides(self):
        """存疑的身份断言必须同时记录争议双方，不得只写一种"""
        if self.relation == IdentityRelation.UNCERTAIN and not self.alternative_relations:
            raise ValueError(
                "【负控制硬阻断】UNCERTAIN 身份断言必须列出 alternative_relations，"
                "否则等于用一个标签掩盖争议。"
            )
        return self


class PlaceTransformationEvent(str, Enum):
    """
    空间对象变化算子（P0-7：从 ToponymEvolution 拆出）。
    Toponym 层只负责"名称—所指"关系，不再承担空间变化。
    """
    CONSTRUCTED = "新建"
    EXPANDED = "扩展"
    CONTRACTED = "收缩"
    DIVERTED = "改道"
    RELOCATED = "迁址"
    DAMAGED = "毁损"
    PARTIALLY_DESTROYED = "部分毁损"
    ABANDONED = "废弃"
    DEMOLISHED = "拆除"
    REBUILT = "重建"


class PlaceTransformation(BaseModel):
    """空间对象变化事件（P0-7）：回答"这个空间对象发生了什么" """
    id: str = Field(..., description="变化事件URI，如 pte_yuanmingyuan_1860_burn")
    entity_id: str = Field(..., description="被改变的实体ID")
    transformation: PlaceTransformationEvent = Field(..., description="变化类型")
    time_span: TimeSpan = Field(..., description="发生时间")
    resulting_state_id: Optional[str] = Field(
        None, description="变化后产生的新 HistoricalFeatureState ID"
    )
    resulting_condition: Optional[str] = Field(
        None,
        description="变化后的空间状态描述，如：残存建筑与禁园状态",
    )
    evidence_fact_ids: List[str] = Field(..., description="支撑证据")

    @model_validator(mode="after")
    def _damage_is_not_extinction(self):
        """
        【负控制】毁损≠消亡。
        圆明园1860焚毁后仍有残存建筑与禁园状态、1900年再遭毁损，
        地点本体并未消亡——不得用 extinction 表达 damage。
        """
        if self.transformation in (
            PlaceTransformationEvent.DAMAGED,
            PlaceTransformationEvent.PARTIALLY_DESTROYED,
        ):
            markers = ("extinction", "消亡", "已废弃", "不复存在")
            hay = "%s %s" % (self.resulting_state_id or "", self.resulting_condition or "")
            hit = [m for m in markers if m in hay]
            if hit:
                raise ValueError(
                    "【负控制硬阻断】毁损不得被表达为消亡（命中 %s）！"
                    "圆明园1860焚毁后仍有残存建筑与禁园状态。" % hit
                )
        return self


class PlaceAggregate(BaseModel):
    """
    空间集合（P0-6/7）：圆明园、长春园、绮春园各自有边界与身份，
    又共同组成"圆明三园"——这是有边界的同时性集合，不是"一裂为三"。
    """
    id: str = Field(..., description="集合URI，如 agg_yuanming_three_gardens")
    label: str = Field(..., description="集合名称，如：圆明三园")
    time_span: TimeSpan = Field(..., description="集合成立区间")
    member_entity_ids: List[str] = Field(..., description="成员实体ID")


class AppellationKind(str, Enum):
    """
    名称类型（P0-8）。
    字符串"高梁桥"绝不能承担实体消歧——它是名称，所指才是实体。

    v2.1 补齐：交付档案中确有「七十二府」这类民间传说名，
    原枚举无对应项，会迫使数据方把它错标为 FOLK_LEGEND 之外的类。
    """
    OFFICIAL = "官称"
    VULGAR = "俗名"
    EUPHEMISTIC = "雅化名"
    GARRISON_CODE = "军屯字号"
    STATION_NAME = "现代站名"
    STREET_NAME = "现代路街名"
    TEXTUAL_CORRUPTION = "文献讹字"       # 如"高粱"讹作"高梁"
    MISPLACED_LEGEND = "讹误载体"       # 如"涿州驴车"误植于桥下
    FOLK_LEGEND = "民间传说名"          # 如"一溜边山七十二府"，无官方名录
    OLD_NAME = "旧地名"                 # 如"七里泊""碾庄"，后被通称取代
    HONORIFIC = "敕名"                  # 如经正式诏敕赐名（须有档案依据）


class Appellation(BaseModel):
    """
    名称（P0-8 核心新增）。名称本身是时间有界的指称，不携带任何空间属性。
    """
    id: str = Field(..., description="名称URI，如 app_gaoliangqiao_official")
    label: str = Field(..., description="字面写法，如：高梁桥")
    script_variants: List[str] = Field(default_factory=list, description="异体字/讹字")
    kind: AppellationKind = Field(..., description="名称类型")
    valid_time_span: TimeSpan = Field(..., description="该名称的有效区间")
    attesting_fact_ids: List[str] = Field(
        default_factory=list, description="证明该名称存在的文本事实ID"
    )


class ReferentialAssertion(BaseModel):
    """
    名称—所指关系（P0-8）：多对多，且必须可被证伪。

    "高梁河之战"指向的是水系，不是桥。
    绝不能因为字符串命中"高梁桥"就把战场事件绑到桥实体上。

    【v2.1 补充·传说名】民间传说名（如「穷八家」「七十二府」）确实需要
    表达"民间认为这个名指这个地方"，但依据是民俗传闻而非档案。
    此类必须：evidence_fact_ids 可空，但 status 必须为
    FOLK_LEGEND 或 UNSUBSTANTIATED，且 provenance 必须写明依据性质。
    """
    id: str = Field(..., description="指称断言URI")
    appellation_id: str = Field(..., description="名称ID")
    referent_entity_id: str = Field(..., description="该名称在此期间所指的实体ID")
    referent_state_id: Optional[str] = Field(
        None, description="若所指为特定状态而非实体，则指向状态ID"
    )
    time_span: TimeSpan = Field(..., description="该指称关系成立的区间")
    evidence_fact_ids: List[str] = Field(..., description="支撑证据")
    status: EpistemicStatus = Field(
        EpistemicStatus.VERIFIED, description="采信状态（战场落点可为CONTESTED）"
    )
    provenance: Optional[str] = Field(
        None,
        description="传说名必填：说明依据性质（如地方文史/民俗传闻），与档案证据区分",
    )

    @model_validator(mode="after")
    def _need_evidence_or_legend_status(self):
        has_evidence = bool(self.evidence_fact_ids)
        legend_status = self.status in (EpistemicStatus.FOLK_LEGEND,
                                        EpistemicStatus.UNSUBSTANTIATED)
        if not has_evidence:
            if not legend_status:
                raise ValueError(
                    "【负控制硬阻断】指称断言必须有证据；"
                    "确无档案证据的传说名必须显式标为"
                    " FOLK_LEGEND/UNSUBSTANTIATED 并写 provenance，"
                    "否则会出现'名称字符串命中即自动绑定实体'的假消歧。"
                )
            if not self.provenance:
                raise ValueError(
                    "【负控制硬阻断】无档案证据的传说指称必须写 provenance，"
                    "说明依据性质（地方文史/民俗传闻），与档案证据区分。"
                )
        return self
