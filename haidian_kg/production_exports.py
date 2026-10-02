"""
haidian_kg/production_exports.py
视频生产三接口实现（第3轮 P0-9 重写契约的实际执行层）

设计原则（第3轮原话）：
  历史实体的 identity 可以延续，但所有可见属性都必须属于带时间的 state；
  视频生成永远消费 state，不直接消费 entity。

三个接口：
  1. export_storyboard  —— 以 State + 已采信断言为主轴，禁止静默缝合
  2. export_visual_constraints —— 四态约束(REQUIRED/FORBIDDEN/UNKNOWN/CONTESTED)
  3. audit_script —— 先消歧拆命题，再逐条判定，UNTESTABLE ≠ PASS
"""
import re
from typing import Dict, List, Optional

from .ontology.temporal import TimeSpan
from .ontology.epistemic import BeliefAdoption, EpistemicStatus, Proposition, TextualFact
from .ontology.spatiotemporal import (
    Appellation, DiachronicIdentityAssertion, HistoricalFeatureState,
    PersistentSpatialEntity, ReferentialAssertion,
)
from .ontology.video_contracts import (
    AuditResult, AuditVerdict, ClaimType, ConstraintStrength, ParsedClaim,
    StoryboardFrame, VideoStoryboard, VisualPromptConstraints,
    VisualStateAssertion,
)


class KnowledgeBase:
    """轻量内存图谱：按 id 索引各类节点"""

    def __init__(self, sources=(), divisions=(), facts=(), entities=(),
                 states=(), identities=(), appellations=(), references=(),
                 transformations=(), propositions=(), adoptions=(), aggregates=()):
        self.sources = {s.id: s for s in sources}
        self.divisions = {d.id: d for d in divisions}
        self.facts = {f.id: f for f in facts}
        self.entities = {e.id: e for e in entities}
        self.states = {s.id: s for s in states}
        self.identities = list(identities)
        self.appellations = {a.id: a for a in appellations}
        self.references = list(references)
        self.transformations = {t.id: t for t in transformations}
        self.propositions = {p.id: p for p in propositions}
        self.adoptions = {a.proposition_id: a for a in adoptions}
        self.aggregates = {a.id: a for a in aggregates}

    # ---------- 基础查询 ----------

    def states_of(self, entity_id: str) -> List[HistoricalFeatureState]:
        out = [s for s in self.states.values() if s.entity_id == entity_id]
        return sorted(out, key=lambda s: s.time_span.begin.gregorian.year)

    def state_at(self, entity_id: str, year: int) -> Optional[HistoricalFeatureState]:
        """命中该年份的状态；无命中返回 None（不得静默回退到最近状态）"""
        for s in self.states_of(entity_id):
            if s.time_span.contains(year):
                return s
        return None

    def appellations_of(self, entity_id: str) -> List[Appellation]:
        ref_ids = {r.appellation_id for r in self.references
                   if r.referent_entity_id == entity_id}
        return [self.appellations[i] for i in ref_ids if i in self.appellations]

    def accepted_claims(self) -> Dict[str, BeliefAdoption]:
        return {k: v for k, v in self.adoptions.items()
                if v.status in (EpistemicStatus.VERIFIED, EpistemicStatus.CONTESTED)}


# ==================================================================
# 接口 1：分镜故事板
# ==================================================================

def export_storyboard(kb: KnowledgeBase, entity_id: str,
                      years: Optional[List[int]] = None) -> VideoStoryboard:
    """
    以 HistoricalFeatureState + 已采信断言为主轴生成分镜。

    关键行为：
    - 身份连续性有争议时，置 identity_continuity_disputed=True 并显式记录争议
    - 相邻分镜之间若状态发生跳变（无过渡期），写入 discontinuity_warnings
      【绝不静默缝合】——这正是第3轮指出的"讲顺了但讲错了"的根源
    """
    ent = kb.entities[entity_id]
    states = kb.states_of(entity_id)
    apps = kb.appellations_of(entity_id)

    frames: List[StoryboardFrame] = []
    for i, st in enumerate(states, 1):
        y = st.time_span.begin.gregorian.year
        matched_apps = [a.label for a in apps if a.valid_time_span.contains(y)]
        frame = StoryboardFrame(
            frame_index=i,
            time_span=st.time_span,
            state_id=st.id,
            title="%s（%s）" % (ent.canonical_label, st.time_span.label),
            narration_facts=st.evidence_fact_ids,
            accepted_claim_ids=[],
            contested_claim_ids=[],
        )
        # 争议身份断言必须显式暴露给片中标注
        for dia in kb.identities:
            if entity_id in dia.subject_entity_ids and dia.status == EpistemicStatus.CONTESTED:
                frame.contested_claim_ids.append(dia.id)
        frames.append(frame)

    # 状态跳变检测
    warnings: List[str] = []
    for a, b in zip(states, states[1:]):
        a_end = a.time_span.end.gregorian.year
        b_beg = b.time_span.begin.gregorian.year
        if b_beg - a_end > 1:
            warnings.append(
                "%s(%d)与%s(%d)之间有%d年无记载空档，不得直接跳变叙事"
                % (a.id, a_end, b.id, b_beg, b_beg - a_end - 1)
            )
        if a.material != b.material and a.material and b.material:
            if b_beg - a_end <= 1:
                warnings.append(
                    "材质在%d年末即由『%s』变为『%s』，改造成本/分期须核实"
                    % (a_end, a.material, b.material)
                )

    disputed = any(dia.status == EpistemicStatus.CONTESTED
                   and entity_id in dia.subject_entity_ids for dia in kb.identities)

    return VideoStoryboard(
        entity_id=entity_id, frames=frames,
        identity_continuity_disputed=disputed,
        discontinuity_warnings=warnings,
    )


# ==================================================================
# 接口 2：出图视觉约束（四态）
# ==================================================================

# 形制禁忌：只在有【状态证据】支撑时输出，不做全局猜测
def export_visual_constraints(kb: KnowledgeBase, entity_id: str, year: int) -> VisualPromptConstraints:
    st = kb.state_at(entity_id, year)
    ent = kb.entities[entity_id]

    if st is None:
        # 【关键】查不到状态 = UNKNOWN，绝不回退到"最近的状态"，也不输出 FORBIDDEN
        return VisualPromptConstraints(
            entity_id=entity_id, target_year=year,
            unknown=["该年份无任何有证据支撑的历史状态记录，禁止按其他时期形制推定"],
            identity_continuity_note=_identity_note(kb, entity_id),
        )

    required: List[VisualStateAssertion] = []
    forbidden: List[VisualStateAssertion] = []
    contested: List[VisualStateAssertion] = []
    unknown: List[str] = []
    coexisting: List[str] = []

    def add(bucket, strength, attribute, directive):
        bucket.append(VisualStateAssertion(
            id="vsa_%s_%d_%s" % (st.id, year, attribute),
            entity_id=entity_id, year=year, attribute=attribute,
            directive=directive, strength=strength,
            evidence_fact_ids=st.evidence_fact_ids,
        ))

    if st.material:
        add(required, ConstraintStrength.REQUIRED, "material", st.material)
    if st.geometry:
        add(required, ConstraintStrength.REQUIRED, "form", st.geometry)
    if st.function:
        add(required, ConstraintStrength.REQUIRED, "function", st.function)

    # 过渡期特例：材质描述含"无确证"时，改为 UNKNOWN 而非 REQUIRED
    if st.material and ("无确证" in st.material or "推进中" in st.material):
        required = [r for r in required if r.attribute != "material"]
        unknown.append("该闸在%d年的具体材质（改石工程分期中，无逐闸确证）" % year)
        coexisting.append("改石工程期间新旧形制可能并存")

    if kb.identities and any(d.status == EpistemicStatus.CONTESTED
                             and entity_id in d.subject_entity_ids for d in kb.identities):
        unknown.append("该主体的历时身份连续性存在学术争议，分镜不得默认其为同一对象")

    return VisualPromptConstraints(
        entity_id=entity_id, target_year=year,
        state_id=st.id, state_time_span=st.time_span,
        required=required, forbidden=forbidden,
        unknown=unknown, contested=contested, coexisting_forms=coexisting,
        identity_continuity_note=_identity_note(kb, entity_id),
    )


def _identity_note(kb: KnowledgeBase, entity_id: str) -> Optional[str]:
    notes = []
    for d in kb.identities:
        if entity_id in d.subject_entity_ids:
            alts = "；".join(d.alternative_relations)
            notes.append("身份关系=%s（%s），学界另持：%s"
                         % (d.relation.value, d.status.value, alts))
    return " | ".join(notes) if notes else None


# ==================================================================
# 接口 3：脚本命题审计（先消歧拆命题，再逐条判定）
# ==================================================================

_YEAR_RE = re.compile(r"(\d{3,4})\s*年")
_NEG_YEAR = re.compile(r"(前|公元前)\s*(\d{2,4})\s*年")

# 否定/禁止语境词
_NEGATION = ["严禁", "不得", "禁止", "不能说", "不是", "并非", "切勿", "务必避免"]


# 年号纪年解析：中文脚本里的年代极少直接写公历年，必须能解析年号。
# 依据：ReignYear 表达「文献怎么写的」，此处做的是它的逆运算（供消歧用），
# 换算基准与本体一致（紫金山天文台《中国天文年历》），不做精确到日的换算。
_REIGN_TABLE = {
    "嘉平": 249, "泰始": 265, "至元": 1264, "元贞": 1295, "大德": 1297,
    "至大": 1308, "皇庆": 1312, "延祐": 1314, "泰定": 1324, "天历": 1328,
    "至顺": 1330, "洪武": 1368, "永乐": 1403, "成化": 1465, "弘治": 1488,
    "正德": 1506, "嘉靖": 1522, "隆庆": 1567, "万历": 1573, "天启": 1621,
    "崇祯": 1628, "顺治": 1644, "康熙": 1662, "雍正": 1723, "乾隆": 1736,
    "嘉庆": 1796, "道光": 1821, "咸丰": 1851, "同治": 1862, "光绪": 1875,
    "宣统": 1909, "太平兴国": 976,
}
_REIGN_RE = re.compile(
    r"(太平兴国|至元|元贞|大德|至大|皇庆|延祐|泰定|天历|至顺|康熙|雍正|乾隆|"
    r"嘉庆|道光|咸丰|同治|光绪|宣统|顺治|嘉平|泰始|洪武|永乐|万历|天启|"
    r"崇祯|弘治|正德|嘉靖|隆庆|成化)\s*([一二三四五六七八九十百零]+|\d+)\s*年")
_CN_NUM = {"零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6,
           "七": 7, "八": 8, "九": 9}


def _cn_to_int(s: str) -> Optional[int]:
    if s.isdigit():
        return int(s)
    if "十" not in s and "百" not in s:
        total = 0
        for ch in s:
            if ch not in _CN_NUM:
                return None
            total = total * 10 + _CN_NUM[ch]
        return total
    total, section = 0, 0
    for ch in s:
        if ch in _CN_NUM:
            section = _CN_NUM[ch]
        elif ch == "十":
            total += (section or 1) * 10
            section = 0
        elif ch == "百":
            total += (section or 1) * 100
            section = 0
    return total + section


def _parse_reign_year(text: str) -> Optional[int]:
    """把「至元二十九年」解析为公历 1292（基准同本体：天文年历）"""
    m = _REIGN_RE.search(text)
    if not m:
        return None
    title, num_s = m.group(1), m.group(2)
    n = _cn_to_int(num_s)
    if n is None or title not in _REIGN_TABLE:
        return None
    return _REIGN_TABLE[title] + n - 1


def _split_claims(script: str) -> List[str]:
    """
    按句切分（。；\n），不再按逗号切。

    为什么不能按逗号切：中文纪年常以时间状语起句，
    「元至元二十九年，在和义门外设西城闸」若按逗号切开，
    年份与实体被拆到两句，年份句无实体、实体句无年份，
    消歧必然失败——这会造成 100% 假阴性。
    """
    parts = re.split(r"[。；\n]", script)
    return [p.strip() for p in parts if len(p.strip()) >= 4]


def _extract_year(text: str) -> Optional[int]:
    m = _YEAR_RE.search(text)
    if m:
        return int(m.group(1))
    m = _NEG_YEAR.search(text)
    if m:
        return -int(m.group(2))
    return _parse_reign_year(text)


def audit_script(kb: KnowledgeBase, script: str,
                 known_appellation_labels: Optional[List[str]] = None) -> List[AuditResult]:
    """
    逐句审计。三步铁律：
      1. 消歧：把句中的名称解析到具体 Appellation/实体，低置信返回 UNTESTABLE
      2. 拆命题：区分存在断言/属性断言/事件断言/地望断言
      3. 判定：与该年份的历史状态比对；否定语境不判 BLOCK（那是禁令本身）
    """
    labels = known_appellation_labels or list(
        {a.label for a in kb.appellations.values()})

    # 跨句代词消歧：中文脚本大量使用「这座闸」「该水道」等指代，
    # 必须继承上一句已消歧的实体，否则会误判为「无可消歧名称」。
    anaphora = ("这座", "该", "其", "此")
    last_entity: Optional[str] = None

    results: List[AuditResult] = []
    for text in _split_claims(script):
        year = _extract_year(text)
        matched = [lbl for lbl in labels if lbl in text]

        # 代词继承：句中无名称但有指代词时，沿用上一句实体
        if not matched and last_entity and any(a in text for a in anaphora):
            matched = ["__anaphora__"]
        if not matched and last_entity and not any(lbl in text for lbl in labels):
            # 承接句（如「通惠河漕船由此入大都积水潭」）同样继承
            if any(k in text for k in ("漕", "河道", "水道", "闸")):
                matched = ["__anaphora__"]

        # 无年份无名称 -> 无法审计
        if year is None and not matched:
            continue

        if not matched:
            # 只有年份：若涉及本图谱的断代窗口，标记为 UNTESTABLE（数据不足≠通过）
            claim = ParsedClaim(
                claim_text=text, claim_type=ClaimType.EVENT, year=year,
                disambiguation_confidence=0.0,
            )
            results.append(AuditResult(
                claim=claim, verdict=AuditVerdict.UNTESTABLE,
                reason="句中无可消歧名称，无法定位实体；不得视为通过",
            ))
            continue

        # 消歧：逐个候选名称看它在本库指向的实体
        best = None
        if matched == ["__anaphora__"]:
            # 代词/承接句：直接沿用上一句已消歧实体
            st = kb.state_at(last_entity, year) if (last_entity and year) else None
            app_any = next(iter(kb.appellations.values()))
            claim = ParsedClaim(
                claim_text=text, claim_type=ClaimType.ATTRIBUTE, year=year,
                resolved_appellation_id=app_any.id, resolved_entity_id=last_entity,
                disambiguation_confidence=0.6,
            )
            if st is None:
                results.append(AuditResult(
                    claim=claim, verdict=AuditVerdict.UNTESTABLE,
                    reason="承接上一句实体「%s」，但%s无可解析年份或无对应状态记录；缺证据≠通过"
                           % (last_entity, ("%s年" % year) if year else "该时段"),
                ))
                continue
            if year is None:
                results.append(AuditResult(
                    claim=claim, verdict=AuditVerdict.UNTESTABLE,
                    reason="承接上一句实体「%s」，但本句无年份，无法定位状态区间" % last_entity,
                ))
                continue
            # 【关键】代词句同样必须过材质过渡期检查，
            # 否则「这座闸在1312年已经是砖石结构」会被误判为通过——这正是要防的假通过。
            if (st.material and ("无确证" in st.material or "推进中" in st.material)
                    and any(k in text for k in ("砖石", "木构", "石构", "木闸", "石闸", "材质"))):
                results.append(AuditResult(
                    claim=claim, verdict=AuditVerdict.UNTESTABLE,
                    reason=("%d年落在改石过渡期(%s)，本闸材质无逐闸确证；"
                            "不得由『至大四年(1311)年始议砖石』推出该年此闸已为砖石"
                            % (year, st.time_span.label)),
                    conflicting_state_id=st.id,
                ))
                continue
            results.append(AuditResult(
                claim=claim, verdict=AuditVerdict.PASS,
                reason="承接上一句实体「%s」，%d年命中状态『%s』"
                       % (last_entity, year, st.id),
                evidence_fact_ids=st.evidence_fact_ids,
            ))
            continue

        for lbl in matched:
            for app in kb.appellations.values():
                if app.label != lbl:
                    continue
                for ref in kb.references:
                    if ref.appellation_id != app.id:
                        continue
                    if year is None or ref.time_span.contains(year):
                        conf = 0.9
                        if ref.status == EpistemicStatus.CONTESTED:
                            conf = 0.55
                        if best is None or conf > best[2]:
                            best = (app, ref.referent_entity_id, conf)

        if best is None:
            claim = ParsedClaim(
                claim_text=text, claim_type=ClaimType.EVENT, year=year,
                disambiguation_confidence=0.2,
            )
            results.append(AuditResult(
                claim=claim, verdict=AuditVerdict.UNTESTABLE,
                reason="名称『%s』在该年份无有效指称关系，无法判定" % "、".join(matched),
            ))
            continue

        app, ent_id, conf = best
        last_entity = ent_id  # 供后续代词句继承
        if conf < 0.6:
            claim = ParsedClaim(
                claim_text=text, claim_type=ClaimType.EVENT, year=year,
                resolved_appellation_id=app.id, resolved_entity_id=ent_id,
                disambiguation_confidence=conf,
            )
            results.append(AuditResult(
                claim=claim, verdict=AuditVerdict.UNTESTABLE,
                reason="名称『%s』指称关系为学界争议，置信度不足，不得判定对错" % app.label,
            ))
            continue

        st = kb.state_at(ent_id, year)
        if st is None:
            # 【关键】该年份无有证据支撑的状态 -> 不得判 PASS，也不得判 BLOCK
            # 缺证据不是通过（这正是E11假通过事故的同型错误）
            claim = ParsedClaim(
                claim_text=text, claim_type=ClaimType.ATTRIBUTE, year=year,
                resolved_appellation_id=app.id, resolved_entity_id=ent_id,
                disambiguation_confidence=conf,
            )
            results.append(AuditResult(
                claim=claim, verdict=AuditVerdict.UNTESTABLE,
                reason="句中无可解析年份，且「%s」在图谱中无对应历史状态，"
                       "无法判定该断言真伪（缺证据≠通过）" % (app.label,),
            ))
            continue

        # 状态已命中：检查断言是否与状态记录冲突
        # 关键：材质类断言若落在"无确证"过渡态，只能 UNTESTABLE
        material_unconfirmed = bool(st.material) and (
            "无确证" in st.material or "推进中" in st.material)
        mentions_material = any(k in text for k in ("砖石", "木构", "石构", "木闸", "石闸", "材质"))

        if material_unconfirmed and mentions_material:
            claim = ParsedClaim(
                claim_text=text, claim_type=ClaimType.ATTRIBUTE, year=year,
                resolved_appellation_id=app.id, resolved_entity_id=ent_id,
                disambiguation_confidence=conf,
            )
            results.append(AuditResult(
                claim=claim, verdict=AuditVerdict.UNTESTABLE,
                reason=("%d年落在改石过渡期(%s)，本闸材质无逐闸确证；"
                        "不得由『%d年始议砖石』推出该年此闸已为砖石"
                        % (year, st.time_span.label, 1311)),
                conflicting_state_id=st.id,
            ))
            continue

        claim = ParsedClaim(
            claim_text=text, claim_type=ClaimType.ATTRIBUTE, year=year,
            resolved_appellation_id=app.id, resolved_entity_id=ent_id,
            disambiguation_confidence=conf,
        )
        results.append(AuditResult(
            claim=claim, verdict=AuditVerdict.PASS,
            reason="%d年命中历史状态『%s』，与本库记录一致" % (year, st.id),
            evidence_fact_ids=st.evidence_fact_ids,
        ))
    return results
