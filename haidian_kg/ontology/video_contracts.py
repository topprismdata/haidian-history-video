"""
haidian_kg/ontology/video_contracts.py
视频生产接口契约（P0-9 重写）

整改依据（GPT 第3轮 §13-§17）：

原 spec 的三个接口是字符串规则扫描式的，会产生生产级硬伤：
1. export_video_storyboard 以 entity 为主轴 → 会把不同时段信息压成一个"看起来顺畅"的镜头
2. export_visual_prompt_constraints 参数只有 (spatial_id, year) → 材质形制是 State 属性不是 Entity 属性
3. audit_script_text 只做敏感词扫描 → "979年两军在高梁石桥旁激战"这类句子必被误杀或误放

本模块重写契约，核心原则（第3轮原话）：
  历史实体的 identity 可以延续，但所有可见属性都必须属于带时间的 state；
  视频生成永远消费 state，不直接消费 entity。

木闸→石闸杀手测试（第3轮给出的验收标准）：
  1295 年  → 可以较强输出"木构"（至大四年1311年始议砖石，此前为木）
  1312 年  → 绝不能因为"1311年朝廷开始改石"就输出"石构"
  1327 年  → 若该闸已确认完成石化，才可输出"石构"
"""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

from .temporal import TimeSpan
from .epistemic import EpistemicStatus


class ConstraintStrength(str, Enum):
    """
    视觉约束强度四态（第3轮 §16 明确要求）。
    UNKNOWN 与 CONTESTED 必须显式返回给导演，不能偷偷猜。
    """
    REQUIRED = "必须出现"       # 有确凿证据支持
    FORBIDDEN = "严禁出现"     # 有确凿证据证否
    UNKNOWN = "证据不足"       # 该年份状态无证据
    CONTESTED = "学界争议"     # 存在竞争解释


class VisualStateAssertion(BaseModel):
    """
    视觉状态断言：视频引擎唯一可消费的硬约束来源。
    绝不从一般历史事实直接拼 prompt——必须先落成带证据的断言。
    """
    id: str = Field(..., description="视觉断言URI")
    entity_id: str = Field(..., description="实体ID")
    year: int = Field(..., description="适用公元年")
    attribute: str = Field(..., description="约束的属性：material/form/function/props")
    directive: str = Field(..., description="给图像生成的具体指令，如：木构闸坝，榫卯木石，无砖石包砌")
    strength: ConstraintStrength = Field(..., description="约束强度")
    evidence_fact_ids: List[str] = Field(..., description="支撑证据")
    confidence_note: Optional[str] = Field(
        None, description="UNKNOWN/CONTESTED 时必须说明原因，供导演判断"
    )


class VisualPromptConstraints(BaseModel):
    """
    重写后的出图约束契约（第3轮 §14）。

    原契约问题：参数只有 (spatial_id, year)，无法表达"同一实体在同年存在多套并存形制"，
    也无法表达 UNKNOWN。
    新契约：必须携带 evidence chain + 四态强度 + 并存形制。
    """
    entity_id: str = Field(..., description="实体ID")
    target_year: int = Field(..., description="目标公元年")
    state_id: Optional[str] = Field(
        None, description="命中的 HistoricalFeatureState ID"
    )
    state_time_span: Optional[TimeSpan] = Field(None, description="该状态的生效区间")
    required: List[VisualStateAssertion] = Field(
        default_factory=list, description="必须出现的视觉要素"
    )
    forbidden: List[VisualStateAssertion] = Field(
        default_factory=list, description="严禁出现的视觉要素"
    )
    unknown: List[str] = Field(
        default_factory=list, description="该年份无证据的方面（须显式告知导演）"
    )
    contested: List[VisualStateAssertion] = Field(
        default_factory=list, description="存在竞争解释的方面"
    )
    coexisting_forms: List[str] = Field(
        default_factory=list,
        description="同年并存的形制（如改石工程期间新旧并存）",
    )
    identity_continuity_note: Optional[str] = Field(
        None,
        description=(
            "若该实体身份连续性存在学术争议，此处必须显式说明，"
            "不得由系统自动择一编成流畅故事"
        ),
    )

    def as_prompt_block(self) -> str:
        """
        渲染成给图像生成的硬约束文本。
        四态缺一不可：只输出 required/forbidden 会让 UNKNOWN 被当成"没有限制"。
        """
        lines = ["【历史视觉约束 · 四态制】"]
        if self.state_id and self.state_time_span:
            lines.append("命中历史状态：%s（%s）" % (self.state_id, self.state_time_span.label))
        for a in self.required:
            lines.append("✓ 必须：%s（%s）" % (a.directive, a.attribute))
        for a in self.forbidden:
            lines.append("✗ 严禁：%s（%s）" % (a.directive, a.attribute))
        for a in self.contested:
            lines.append("? 存疑：%s —— %s" % (a.directive, a.confidence_note or "学界有争议"))
        for u in self.unknown:
            lines.append("· 无证据：%s（请导演人工判断，不要默认）" % u)
        for c in self.coexisting_forms:
            lines.append("‖ 并存：%s" % c)
        if self.identity_continuity_note:
            lines.append("※ 身份连续性存疑：%s" % self.identity_continuity_note)
        return "\n".join(lines)


class StoryboardFrame(BaseModel):
    """
    分镜帧：必须以 State + 已采信断言为主轴，不得以 Entity 为主轴。
    """
    frame_index: int = Field(..., description="分镜序号")
    time_span: TimeSpan = Field(..., description="本帧覆盖的时间区间")
    state_id: str = Field(..., description="本帧依据的历史状态ID")
    title: str = Field(..., description="分镜标题")
    narration_facts: List[str] = Field(
        default_factory=list, description="可作为口播依据的文本事实ID（仅已采信的）"
    )
    accepted_claim_ids: List[str] = Field(
        default_factory=list, description="本镜采用的已采信断言ID"
    )
    contested_claim_ids: List[str] = Field(
        default_factory=list, description="本镜涉及的争议断言（须在片中标注存疑）"
    )
    visual_constraints_ref: Optional[str] = Field(
        None, description="对应的出图约束对象引用"
    )


class VideoStoryboard(BaseModel):
    """重写后的分镜导出契约：连续性有争议时必须显式暴露，不得自动择一"""
    entity_id: str = Field(..., description="主体实体ID")
    frames: List[StoryboardFrame] = Field(default_factory=list, description="分镜序列")
    identity_continuity_disputed: bool = Field(
        False, description="该主体的历时身份连续性是否存在学术争议"
    )
    discontinuity_warnings: List[str] = Field(
        default_factory=list,
        description="分镜间的时间跳跃/状态断裂警告（禁止静默缝合）",
    )


class ClaimType(str, Enum):
    EXISTENCE = "存在断言"        # "某物在某年存在"
    ATTRIBUTE = "属性断言"        # "某物在某年是木的"
    EVENT = "事件断言"            # "某年某地发生某事"
    LOCATION = "地望断言"        # "某事发生在此地"


class ParsedClaim(BaseModel):
    """
    脚本解析出的原子命题（第3轮 §17）。
    关键：先消歧、再拆命题、最后逐条审计——不能只扫字符串。
    """
    claim_text: str = Field(..., description="原子命题文本")
    claim_type: ClaimType = Field(..., description="命题类型")
    resolved_entity_id: Optional[str] = Field(
        None, description="消歧后指向的实体ID（消歧失败则为空）"
    )
    resolved_appellation_id: Optional[str] = Field(
        None, description="命中的名称ID"
    )
    year: Optional[int] = Field(..., description="解析出的公元年")
    disambiguation_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="消歧置信度（低置信不得直接判定对错）"
    )


class AuditVerdict(str, Enum):
    BLOCK = "阻断"                 # 确证冲突，必须改稿
    WARN = "警告"                  # 存疑，建议改稿
    PASS = "通过"
    UNTESTABLE = "无法审计"        # 消歧失败/无证据——不等于通过


class AuditResult(BaseModel):
    """逐条命题的审计结论"""
    claim: ParsedClaim
    verdict: AuditVerdict = Field(..., description="审计结论")
    reason: str = Field(..., description="判定理由（必须可追溯到具体证据）")
    evidence_fact_ids: List[str] = Field(default_factory=list, description="依据证据")
    conflicting_state_id: Optional[str] = Field(
        None, description="与之冲突的历史状态ID"
    )
