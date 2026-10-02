# 海淀与北京历史时空知识图谱（BHKG / HHTO v2.0）本体架构规范说明书
## 2026-10-02-haidian-kg-ontology-redesign-design.md

> 研制团队：topprismdata / claude assistant  
> 规范版本：BHKG / HHTO Ontology Spec v2.0  
> 理论渊源：CIDOC CRM (ISO 21127) 事件中心模型、CHGIS 冻结实例与时间切片模型、中国历史地理学术规范  
> 交付目标：为海淀与北京历史文化视频生产提供坚实、防伪、可溯源的“学术研究大脑”与“防翻车闸门”。

---

## 一、架构哲学：事件中心驱动与六大核心支柱

传统地名数据库通常将地名看作静态属性，导致空间位移、异名同地、古今混淆。
本本体严格采用 **CIDOC CRM 的“事件中心（Event-centric）”建模哲学** 与 **CHGIS 的“冻结实例（Frozen Instance）”生命周期模型**。

在客观历史上，物理空间本身具有连续性，而人类对空间的命名、割裂、合并、筑造与废弃，本质上全是由具体的**历史事件（Historical Event）**所驱动的。

### 核心六大支柱概念拓扑图：
```
                           【史书文献 (HistoricalSource)】
                                      │ 划分卷帙 (consists_of)
                                      ▼
                            【文献卷帙 (SourceDivision)】
                                      │ 提供见载 (attests)
                                      ▼
    【历史人物 (Person)】 ──参与/主导──▶ 【历史事件 (HistoricalEvent)】
            │  (participates)                 │ 发生于 (takes_place_at)
            │                               ▼
            │ 促成/题写 (triggers)    【空间实体 (SpatialEntity)】
            ▼                               ▲
  【地名演化/更名 (ToponymEvolution)】 ───所指称──┘ (identifies)
            │
            ▼ 锚定于 (bound_to)
  【年代时空点 (ChronologicalPoint)】
```

---

## 二、六大支柱详细模式规范 (Schema Specification)

### 支柱 1：年代时空体系 (Chronological Point & Time Span)
摒弃单一的公历标量，建立“公历区间 + 中国传统纪年四元组 + 史前距今年代”复合时间模型。

```python
class ChronologicalPoint(BaseModel):
  """时空年代锚点与生命周期时间窗"""

  gregorian_start_year: Optional[int] = Field(
      None, description="公历起始年（负数为公元前）"
  )
  gregorian_end_year: Optional[int] = Field(
      None, description="公历终止年（若为瞬时事件则等于起始年）"
  )
  dynasty: str = Field(
      ...,
      description=(
          "标准历史朝代：史前/先秦/秦汉/魏晋南北朝/隋唐五代/辽金/元代/明代/清代/民国/当代"
      ),
  )
  reign_title: Optional[str] = Field(
      None, description="帝王年号，如：嘉平二年、至元二十九年、乾隆十六年"
  )
  emperor: Optional[str] = Field(
      None, description="帝号/庙号，如：魏齐王曹芳、元世祖忽必烈、清高宗乾隆"
  )
  ganzhi: Optional[str] = Field(
      None, description="干支纪年，如：庚午、七月癸未"
  )
  circa_bp: Optional[int] = Field(
      None, description="距今年代（BP），专用于 Era 0 史前，如 770000 BP"
  )
  uncertainty_range: Optional[Tuple[int, int]] = Field(
      None, description="模糊时间上下限浮动范围，如 [-1046, -1045]"
  )
```

---

### 支柱 2：空间实体与相对拓扑网络 (Spatial Entity & Topology)
区分“物理自然地物（Phenomenal Place）”与“人文建置设施（Declarative Place）”，并构建严格的相对空间拓扑。

```python
class SpatialType(str, Enum):
  WATERCOURSE = "Watercourse"  # 自然水系（高梁河、万泉河）
  SPRING_WETLAND = "SpringWetland"  # 泉群湿地（巴沟、万泉）
  TERRAIN = "TerrainElevation"  # 山岳丘阜（西山、万寿山）
  SETTLEMENT = "Settlement"  # 聚落聚居区（海淀镇、肖家河）
  MILITARY_GARRISON = "MilitaryGarrison"  # 军事营防（圆明园护军营、外火器营）
  IMPERIAL_GARDEN = "ImperialGarden"  # 皇家园林（圆明园、畅春园）
  HYDRAULIC_FACILITY = "HydraulicFacility"  # 水利工程设施（西城闸、高梁桥）


class SpatialEntity(BaseModel):
  """空间地理实体"""

  id: str = Field(..., description="空间实体唯一URI，如 spat_gaoliang_river")
  standard_name: str = Field(..., description="空间实体标准规范名")
  spatial_type: SpatialType = Field(..., description="空间分类")
  wgs84_coord: Optional[Tuple[float, float]] = Field(
      None, description="[经度, 纬度]"
  )
  time_span: ChronologicalPoint = Field(
      ..., description="该实体在地理空间上客观存在的时间跨度"
  )

  # 空间相对拓扑关系（避免孤立点数据）
  part_of: List[str] = Field(
      default_factory=list,
      description="从属/包含空间实体ID（如：西城闸 part_of 通惠河水系）",
  )
  adjacent_to: List[str] = Field(
      default_factory=list,
      description="相邻空间实体ID（如：肖家河 adjacent_to 树村）",
  )
  upstream_of: List[str] = Field(
      default_factory=list,
      description="水系上游关联（如：瓮山泊 upstream_of 高梁河）",
  )
  downstream_of: List[str] = Field(
      default_factory=list, description="水系下游关联"
  )
  contemporary_site: Optional[str] = Field(
      None, description="现代对应地理位置精确描述"
  )
```

---

### 支柱 3：地名演化与生命周期网络 (Toponym & Evolution)
引入 CHGIS 冻结实例生命周期，地名作为称谓（Appellation），通过“命名/演变事件”与空间实体形成动态时间绑定。

```python
class EvolutionType(str, Enum):
  CREATION = "Creation"  # 始现诞生
  OFFICIAL_RENAME = "OfficialRename"  # 官方诏敕更名
  EUPHEMIC_RENAME = "EuphemicRename"  # 文人/官府雅化更名（如穷八家->大有庄）
  PHONETIC_CORRUPTION = (
      "PhoneticCorruption"  # 讹音演变（如臭水河->寿安河、带州->太舟坞）
  )
  FISSION = "Fission"  # 空间分化/裂变（一分为多）
  FUSION = "Fusion"  # 聚落合并（多合为一）
  EXTINCTION_FOSSIL = "ExtinctionFossil"  # 聚落本体消亡但地名化石存留（如成府村->成府路）


class ToponymNode(BaseModel):
  """历史地名冻结节点（Frozen Instance）"""

  id: str = Field(..., description="地名节点唯一URI，如 top_gaoliang_water_wei")
  standard_hanzi: str = Field(..., description="标准汉字规范书写")
  script_variants: List[str] = Field(
      default_factory=list, description="异体字/俗写字形，如 ['高梁', '高粱']"
  )
  pinyin: str = Field(..., description="标准汉语拼音")
  name_category: str = Field(
      ..., description="官称(Official)、俗名(Vulgar)、雅化名(Euphemism)、军屯号(GarrisonCode)"
  )
  identifies_spatial_id: str = Field(
      ..., description="本时间段所指称的物理空间实体ID"
  )
  valid_time_span: ChronologicalPoint = Field(
      ..., description="该地名称号适用的有效时间窗"
  )


class ToponymEvolutionEvent(BaseModel):
  """地名更名/演变事件"""

  id: str = Field(..., description="演变事件URI")
  evolution_type: EvolutionType = Field(..., description="演变算子类型")
  source_toponym_ids: List[str] = Field(..., description="演变前地名ID列表")
  target_toponym_ids: List[str] = Field(..., description="演变后地名ID列表")
  time_point: ChronologicalPoint = Field(..., description="演变发生年代")
  caused_by_historical_event_id: Optional[str] = Field(
      None, description="触发此演变的历史大事件ID"
  )
  trigger_actor_id: Optional[str] = Field(
      None, description="触发人物ID（如：乾隆帝、陈垣）"
  )
  evolution_rationale: str = Field(..., description="演变考据动因说明")
```

---

### 支柱 4：三级史书文献与证据防伪机制 (Sources & Epistemic Attestation)
从物理底层阻断“跨卷拼接假引文”和“无据推论”。

```python
class SourceCategory(str, Enum):
  OFFICIAL_HISTORY = "OfficialHistory"  # 二十四史正史
  LOCAL_GAZETTEER = "LocalGazetteer"  # 地方志书（宛署杂记、日下旧闻考）
  EPIGRAPHY = "Epigraphy"  # 金石碑刻拓本一手物证
  GEOGRAPHICAL_TREATISE = "GeographicalTreatise"  # 历史地理专著（水经注）
  LITERARY_COLLECTION = "LiteraryCollection"  # 私人文集（中堂事记）
  ARCHAEOLOGY_REPORT = "ArchaeologyReport"  # 田野考古发掘报告
  MILITARY_SURVEY_MAP = "MilitarySurveyMap"  # 近现代实测军用地图（1913京西图）


class HistoricalSource(BaseModel):
  """Level 1: 典籍/文献总体实体"""

  id: str = Field(..., description="文献唯一URI，如 src_shuijingzhu")
  title: str = Field(..., description="典籍全名，如《水经注》")
  category: SourceCategory = Field(..., description="文献类别")
  author_person_id: Optional[str] = Field(
      None, description="作者人物ID（关联 Person 实体）"
  )
  compiled_time: Optional[ChronologicalPoint] = Field(
      None, description="成书/修纂年代"
  )
  version_description: Optional[str] = Field(
      None, description="版本说明（如：中华书局点校本《水经注疏》）"
  )


class SourceDivision(BaseModel):
  """Level 2: 文献具体篇卷实体（彻底隔绝跨卷拼接）"""

  id: str = Field(
      ..., description="篇卷唯一URI，如 div_shuijingzhu_vol13_luoshui"
  )
  source_id: str = Field(..., description="所属典籍ID")
  volume_number: str = Field(..., description="卷数，如：卷十三、卷四、本纪第四")
  section_title: str = Field(
      ..., description="篇名/志名，如：漯水、太宗一、河渠志三"
  )


class AttestationEvidence(BaseModel):
  """Level 3: 一手书证证据节点"""

  id: str = Field(..., description="证据唯一URI")
  division_id: str = Field(
      ..., description="严格所属篇卷ID（禁止包含逗号或连接符跨卷！）"
  )
  verbatim_quote: str = Field(..., description="原典字句一字不改的原文引用")
  attested_string: str = Field(..., description="原典中见载的地名/事件关键词")
  evidence_level: EvidenceLevel = Field(
      ..., description="六级认识论证据等级(L1考古硬证据至L6证伪)"
  )
  epistemic_status: EpistemicStatus = Field(
      ..., description="判定状态：VERIFIED / CONTESTED / DISPROVEN"
  )
  attests_toponym_id: Optional[str] = Field(
      None, description="证明的地名实体ID"
  )
  attests_event_id: Optional[str] = Field(
      None, description="证明的历史事件实体ID"
  )

  @validator("division_id")
  def verify_no_cross_volume_stitching(cls, v):
    if any(sep in v for sep in [",", "，", "&", "和", "及"]):
      raise ValueError("【防伪硬阻断】严禁跨卷拼接书证！不同卷必须拆分为独立证据节点！")
    return v
```

---

### 支柱 5：历史人物实体 (Historical Person)
一等公民，参与重大历史事件并撰写历史文献。

```python
class PersonRole(str, Enum):
  MONARCH = "Monarch"  # 帝王君主（忽必烈、乾隆）
  HYDRAULIC_ENGINEER = "HydraulicEngineer"  # 水利工程师（郭守敬、刘靖）
  LOCAL_MAGISTRATE = "LocalMagistrate"  # 地方官吏（沈榜）
  MILITARY_COMMANDER = "MilitaryCommander"  # 军事将领（耶律休哥、刘克庄）
  SCHOLAR_WRITER = "ScholarWriter"  # 文人学者（郦道元、王恽、陈垣）
  RELIGIOUS_FIGURE = "ReligiousFigure"  # 僧道宗教人物（如礼、道深）


class HistoricalPerson(BaseModel):
  """历史人物实体"""

  id: str = Field(..., description="人物唯一URI，如 person_guo_shoujing")
  name: str = Field(..., description="姓名")
  courtesy_name: Optional[str] = Field(None, description="字号")
  dynasty: str = Field(..., description="生活朝代")
  time_span: Optional[ChronologicalPoint] = Field(
      None, description="生卒公元年份区间"
  )
  primary_role: PersonRole = Field(..., description="主要历史角色")
  official_titles: List[str] = Field(
      default_factory=list, description="曾任官职品阶"
  )
  authored_source_ids: List[str] = Field(
      default_factory=list, description="其所撰写/编纂的典籍ID列表"
  )
```

---

### 支柱 6：历史大事件实体 (Historical Event)
连接人物、空间与文献的枢纽，统领一切人类对地表的改造与动荡。

```python
class EventCategory(str, Enum):
  MILITARY_BATTLE = "MilitaryBattle"  # 战争战役（979高梁河之战）
  HYDRAULIC_PROJECT = "HydraulicProject"  # 水利工程（250车箱渠、1292通惠河立闸）
  IMPERIAL_CONSTRUCTION = "ImperialConstruction"  # 皇家营建（1707筑圆明园）
  ADMINISTRATIVE_CHANGE = "AdministrativeChange"  # 政区析置改革（938升幽州置宛平）
  WAR_DESTRUCTION = "WarDestruction"  # 战乱焚毁（1860火烧圆明园）
  TOPONYM_REVISION = "ToponymRevision"  # 重大官方更名颁旨


class HistoricalEvent(BaseModel):
  """历史重大事件实体"""

  id: str = Field(..., description="事件唯一URI，如 evt_battle_gaolianghe_979")
  title: str = Field(..., description="事件名称")
  category: EventCategory = Field(..., description="事件类别")
  time_point: ChronologicalPoint = Field(..., description="事件确切发生时间")
  location_spatial_id: str = Field(..., description="事件发生空间地点实体ID")
  primary_actors: List[str] = Field(
      default_factory=list, description="参与主要人物ID列表"
  )
  summary: str = Field(..., description="事件经过与结果摘要")
  evidenced_by_attestation_ids: List[str] = Field(
      ..., description="证明该事件的一手书证节点ID列表"
  )
```

---

## 三、负控制与防伪校验核心规则 (Negative Control Engine)

严格吸取外部专家复审教训，定义三类负控制规则，并在代码层强制执行：

```python
class RefutationType(str, Enum):
  ANACHRONISM = "Anachronism"  # 时代倒错（如979年战役画出元代石桥）
  SPURIOUS_ETYMOLOGY = "SpuriousEtymology"  # 伪词源（如因红高粱得名高梁河）
  MISPLACED_GEOGRAPHY = (
      "MisplacedGeography"  # 地望错位（如将涿州乘驴车移至西直门高梁桥下）
  )


class NegativeControlRule(BaseModel):
  id: str = Field(..., description="规则ID")
  target_subject_id: str = Field(..., description="所监控的地名或事件ID")
  refutation_type: RefutationType = Field(..., description="证伪类型")
  forbidden_claim: str = Field(..., description="严禁出现的错误表述/图画要素")
  evidence_refutation: str = Field(..., description="学术反驳确证依据")
  disproven_attestation_id: str = Field(
      ..., description="证伪所依据的书证/物证节点ID"
  )
```

---

## 四、服务视频制作的三大实战导出规范

本体不仅提供查询，必须能导出直接赋能后续视频制作的生产要素：

1. **`export_video_storyboard(spatial_id) -> List[StoryboardFrame]`**：
   输入地名或空间ID，自动按年代流水线生成：
   `[时间] -> [发生的历史大事件] -> [登场的历史人物] -> [该时期地名称谓] -> [空间形态] -> [一手引文背书]`。
   直接导出为剧本分镜时间线！

2. **`export_visual_prompt_constraints(spatial_id, year) -> PromptConstraint`**：
   输入地名与年份，自动检索该时代合法的物理材质与禁忌要素：
   - 时代建筑构制（如：1292元初西城闸必须为木构，严禁石闸；979辽宋决战严禁石拱桥）；
   - 水系自然风貌（平原泉群、原始土堤）。

3. **`audit_script_text(script_text) -> List[AuditViolation]`**：
   输入旁白脚本草稿，全自动对照 `NegativeControlRule` 库进行敏感词与史实冲突扫描，拦截时代倒错与民间附会伪说。
