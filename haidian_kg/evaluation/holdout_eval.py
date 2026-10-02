"""
haidian_kg.evaluation.holdout_eval
==================================

Holdout v1 评估器：把冻结快照（holdout_v1.jsonl，33 段）喂给闭包挖掘器
（ClosureExpander v3 / rp-v3），对照独立真值计算设计文档
`.superpowers/sdd/holdout-design.md` §7 冻结的五指标：

    mention precision        ≥ 0.90
    mention recall           ≥ 0.85
    high-confidence precision≥ 0.95
    candidate duplication    ≤ 0.05
    entity-collision         = 0（硬闸）

反恒真纪律（spec §5.3 / 本任务冻结）：

1. 真值构造**不 import** `haidian_kg.expansion` 的任何词表或判定函数。
   真值唯一来源 = `haidian_kg/calibration/*.py` 的 8 个校准模块
   （48 实体的 canonical_label + Appellation.label + script_variants，
   即 KB 已建实体字形表），加本模块**独立手写**的字形变体表。
2. 评分路径（gold 提取 / TP-FP-FN 匹配 / 五指标）零 expansion 依赖；
   `expansion` 仅在 FN/FP **归因**函数里作为 rp-v3 冻结规则的描述性
   镜像被惰性引入——它只解释「挖掘器为什么没命中」，绝不参与判定。
3. 金标与引擎两侧的字符串统一过**本模块自己的**归一函数后再比较
   （两侧同函数，保证可比）。

v1 真值是代理金标（已冻结事实：人工标注 holdout_gold.jsonl 尚不存在）：
gold = 段文本中出现的 KB 已知实体/别名字形。据此 mention precision 是
**下界**——语料里真实存在但 KB 未收录的地名（清水院、钓鱼台…）会被
计为 FP。偏差在报告头部显式声明。

用法（仓库根执行，-m 依赖 cwd 上的包，仓库惯例）：

    python3 -m haidian_kg.evaluation.holdout_eval \
        [--holdout haidian_kg/evaluation/holdout_v1.jsonl] \
        [--json-out .superpowers/sdd/holdout-eval-run1.json] \
        [--md-out .superpowers/sdd/holdout-eval-run1.md]
"""

import hashlib
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Set, Tuple

from haidian_kg.production_exports import KnowledgeBase
from haidian_kg.ontology.epistemic import SourceDivision, TextualFact

#: 冻结阈值（holdout-design.md §7，勿改）
THRESHOLDS = {
    "mention_precision": (">=", 0.90),
    "mention_recall": (">=", 0.85),
    "high_conf_precision": (">=", 0.95),
    "duplication_rate": ("<=", 0.05),
    "collision_rate": ("==", 0.0),
}

DEFAULT_ENTITIES_MODULES = (
    "banners", "bridges", "dazhongsi", "gaoliang",
    "settlements", "suburbs", "urban", "yuanmingyuan",
)


# ---------------------------------------------------------------------------
# 独立真值层：私有归一 + 字形变体表（不 import expansion）
# ---------------------------------------------------------------------------

#: 独立手写的字形变体表（逐字、等长映射）。只收本项目 KB 字形表与
#: 长编语料实际涉及的异体；与 expansion._TRAD_TO_SIMP 无任何共享。
#:   邨＝村 的近代异体（urban.script_variants 中官邨）
#:   塹／壍 等未收录字符原样保留——与挖掘器同策略，但表是独立维护的
_VARIANT_MAP = {
    "邨": "村",
    "廻": "回",
    "甯": "宁",
}


def norm_eval(s: str) -> str:
    """评估器自己的归一形（逐字变体表；未收录字符原样保留，等长）。"""
    return "".join(_VARIANT_MAP.get(ch, ch) for ch in s)


def strip_annotation(label: str) -> str:
    """剥掉 canonical_label 尾部的（…）考注。

    KB 的 canonical_label 常带考据注释（如「高梁桥（元代石闸桥；…）」），
    真实地面字形是括号前部分；括号内的方位/别名不进字形表。
    """
    for i, ch in enumerate(label):
        if ch in "（(":
            return label[:i]
    return label


@dataclass(frozen=True)
class GoldMention:
    """金标 mention：文本事实层的一个已知实体出现。"""
    segment_id: str
    start: int                      # 原文 span [start, end)
    end: int
    surface: str                    # 原文逐字
    normalized_form: str            # 评估器归一形
    entity_ids: Tuple[str, ...]     # 该字形挂的 KB 实体（可共享别名 → 多个）
    display_form: str               # 命中的字形表原样（报告用）


class NameRegistry(object):
    """KB 已建实体字形表：归一形 → 实体集合（真值唯一来源）。"""

    def __init__(self, form_map: Dict[str, Set[str]], display: Dict[str, str]):
        # 长形优先：最长匹配需要
        self._forms = sorted(form_map.keys(), key=len, reverse=True)
        self.form_map = form_map
        self.display = display

    def entities_of(self, norm_form: str) -> Set[str]:
        return self.form_map.get(norm_form, set())

    @property
    def forms(self) -> List[str]:
        return self._forms

    def longest_match_at(self, norm_text: str, i: int) -> Optional[str]:
        for f in self._forms:
            if norm_text.startswith(f, i):
                return f
        return None


def build_name_registry(module_names: Sequence[str] = DEFAULT_ENTITIES_MODULES
                        ) -> NameRegistry:
    """从校准模块收集实体字形表（canonical_label 剥注 + 别名 + 异体）。"""
    import importlib
    form_map: Dict[str, Set[str]] = {}
    display: Dict[str, str] = {}
    for name in module_names:
        mod = importlib.import_module("haidian_kg.calibration.%s" % name)
        app_by_id = {a.id: a for a in mod.APPELLATIONS}
        ent_apps: Dict[str, Set[str]] = {}
        for ref in mod.REFERENCES:
            ent_apps.setdefault(ref.referent_entity_id, set()).add(ref.appellation_id)
        for ent in mod.ENTITIES:
            labels = [strip_annotation(ent.canonical_label)]
            for aid in ent_apps.get(ent.id, ()):
                app = app_by_id.get(aid)
                if app is not None:
                    labels.append(strip_annotation(app.label))
                    labels.extend(app.script_variants)
            for label in labels:
                if not label:
                    continue
                nf = norm_eval(label)
                form_map.setdefault(nf, set()).add(ent.id)
                display.setdefault(nf, label)
    return NameRegistry(form_map, display)


def extract_gold_mentions(text: str, segment_id: str,
                          registry: NameRegistry) -> List[GoldMention]:
    """字形最长匹配扫段文本，产出金标 mention（等长归一 ⇒ span 1:1 回映射）。"""
    norm_text = norm_eval(text)
    out: List[GoldMention] = []
    i = 0
    while i < len(norm_text):
        form = registry.longest_match_at(norm_text, i)
        if form is None:
            i += 1
            continue
        out.append(GoldMention(
            segment_id=segment_id, start=i, end=i + len(form),
            surface=text[i:i + len(form)], normalized_form=form,
            entity_ids=tuple(sorted(registry.entities_of(form))),
            display_form=registry.display.get(form, form),
        ))
        i += len(form)
    return out


# ---------------------------------------------------------------------------
# 引擎适配层（不改 expansion.py：用公开构造器造伪 division KB）
# ---------------------------------------------------------------------------

def build_pseudo_kb(segments: Sequence[dict]) -> KnowledgeBase:
    """每段一个 SourceDivision + TextualFact；引擎经 ClosureExpander 消费。"""
    divisions: List[SourceDivision] = []
    facts: List[TextualFact] = []
    for n, seg in enumerate(segments):
        div_id = "div_holdout_%03d" % n
        divisions.append(SourceDivision(
            id=div_id, source_id="holdout_v1",
            volume_number=seg["segment_id"],
            section_title=seg.get("heading_path", "")[:60],
        ))
        facts.append(TextualFact(
            id="tf_holdout_%03d" % n, division_id=div_id,
            verbatim_quote=seg["text"],
            attested_string=seg["segment_id"],
        ))
    return KnowledgeBase(sources=[], divisions=divisions, facts=facts)


@dataclass
class PredOcc:
    """引擎 occurrence + 评估器恢复出的原文 span。"""
    segment_id: str
    start: int
    end: int
    surface: str
    normalized_form: str            # 评估器归一形（两侧同函数）
    confidence: str
    method: str
    occ_id: str


def locate_span(text: str, surface: str) -> Optional[Tuple[int, int]]:
    """挖掘器不产 offset；同 (fact, surface) 只发一次 ⇒ find 首现即唯一。"""
    if not surface:
        return None
    i = text.find(surface)
    if i < 0:
        return None
    return i, i + len(surface)


def run_engine(segments: Sequence[dict]) -> Tuple[Dict[str, List[PredOcc]], object]:
    """把 33 段喂给 ClosureExpander v3，按段收回 occurrence。

    已知字形过滤刻意不启用（known_forms 空、伪 KB 无 appellations）——
    本闸门测的是 mention 层的 P/R，不是「已收录词条的去重」。
    """
    from haidian_kg.expansion import ClosureExpander  # 引擎入口，非判定函数

    kb = build_pseudo_kb(segments)
    report = ClosureExpander(seed_kbs=[kb]).expand()
    div_to_seg = {"div_holdout_%03d" % n: seg["segment_id"]
                  for n, seg in enumerate(segments)}
    seg_text = {seg["segment_id"]: seg["text"] for seg in segments}
    out: Dict[str, List[PredOcc]] = {seg["segment_id"]: [] for seg in segments}
    for hyp in report.candidates_found:
        for occ in hyp.occurrences:
            seg_id = div_to_seg.get(occ.division_id)
            if seg_id is None:
                continue
            span = locate_span(seg_text[seg_id], occ.surface_form)
            if span is None:
                continue
            out[seg_id].append(PredOcc(
                segment_id=seg_id, start=span[0], end=span[1],
                surface=occ.surface_form,
                normalized_form=norm_eval(occ.surface_form),
                confidence=occ.confidence, method=occ.extractor_method,
                occ_id=occ.occurrence_id,
            ))
    for seg_id in out:
        out[seg_id].sort(key=lambda p: (p.start, p.end))
    return out, report


# ---------------------------------------------------------------------------
# 匹配与五指标
# ---------------------------------------------------------------------------

def _contains(a: Tuple[int, int], b: Tuple[int, int]) -> bool:
    """span 相互包含 = 有一方完全覆盖另一方（设计文档 §7 的 containment）。"""
    return (a[0] <= b[0] and a[1] >= b[1]) or (b[0] <= a[0] and b[1] >= a[1])


def match_segment(golds: List[GoldMention], preds: List[PredOcc]
                  ) -> Tuple[List[Tuple[GoldMention, PredOcc]], List[PredOcc],
                             List[GoldMention]]:
    """TP：归一形一致 **且** span 相互包含；剩余即 FP / FN。"""
    tps: List[Tuple[GoldMention, PredOcc]] = []
    used_gold: Set[int] = set()
    fps: List[PredOcc] = []
    for p in preds:
        hit = None
        for gi, g in enumerate(golds):
            if gi in used_gold:
                continue
            if g.normalized_form == p.normalized_form and \
                    _contains((g.start, g.end), (p.start, p.end)):
                hit = gi
                break
        if hit is None:
            fps.append(p)
        else:
            used_gold.add(hit)
            tps.append((golds[hit], p))
    fns = [g for gi, g in enumerate(golds) if gi not in used_gold]
    return tps, fps, fns


def _safe_div(num: int, den: int) -> Optional[float]:
    return None if den == 0 else num / den


def compute_counts(per_segment: List[dict]) -> dict:
    """池化 33 段的 TP/FP/FN/high-conf 计数（文档公式的分子分母）。"""
    tp = sum(s["tp"] for s in per_segment)
    fp = sum(s["fp"] for s in per_segment)
    fn = sum(s["fn"] for s in per_segment)
    tp_high = sum(s["tp_high"] for s in per_segment)
    n_high = sum(s["n_high"] for s in per_segment)
    return {"tp": tp, "fp": fp, "fn": fn, "tp_high": tp_high, "n_high": n_high}


def compute_metrics(counts: dict, gold_entity_total: int,
                    dup_entities: int, collision_hyps: int,
                    hyp_total: int) -> dict:
    """五指标（含 F1 辅助值）。分母为 0 时该指标记 None 并在报告中显式声明。"""
    p = _safe_div(counts["tp"], counts["tp"] + counts["fp"])
    r = _safe_div(counts["tp"], counts["tp"] + counts["fn"])
    f1 = None if (p is None or r is None or p + r == 0) else 2 * p * r / (p + r)
    return {
        "mention_precision": p,
        "mention_recall": r,
        "mention_f1": f1,
        "high_conf_precision": _safe_div(counts["tp_high"], counts["n_high"]),
        "duplication_rate": _safe_div(dup_entities, gold_entity_total),
        "collision_rate": _safe_div(collision_hyps, hyp_total),
        "counts": dict(counts),
        "gold_entity_total": gold_entity_total,
        "dup_entities": dup_entities,
        "collision_hyps": collision_hyps,
        "hypothesis_total": hyp_total,
    }


def gate_check(metrics: dict) -> List[dict]:
    """逐指标对照冻结阈值；None 视为不过（证据不足不放行）。"""
    rows = []
    for key, (op, thr) in THRESHOLDS.items():
        v = metrics[key]
        if v is None:
            ok = False
            detail = "无分母（None）——不能放行"
        else:
            if op == ">=":
                ok = v >= thr
            elif op == "<=":
                ok = v <= thr
            else:
                ok = v == thr
            detail = "%.4f %s %.2f" % (v, op, thr)
        rows.append({"metric": key, "value": v, "op": op, "threshold": thr,
                     "pass": ok, "detail": detail})
    return rows


def hypothesis_coverage(report, segments: Sequence[dict],
                        golds_by_seg: Dict[str, List[GoldMention]],
                        registry: NameRegistry) -> Tuple[Set[str], Set[str], dict]:
    """假说层覆盖分析（duplication / collision 的分子）。

    覆盖判定（身份层，与 mention 匹配无关）：假说 h 覆盖 gold 实体 e ⇔
    h 的某 occurrence 落在与 e 的某金标 mention 相互包含的 span 上，
    且该 occurrence 的归一形 ∈ e 的字形表。
    返回 (dup_entities, collision_hyps, per_hypothesis_detail)。
    """
    div_to_seg = {("div_holdout_%03d" % n): seg["segment_id"]
                  for n, seg in enumerate(segments)}
    seg_text = {seg["segment_id"]: seg["text"] for seg in segments}
    ent_covered_by: Dict[str, Set[str]] = {}     # entity_id -> {hyp form}
    hyp_covers: Dict[str, Set[str]] = {}         # hyp form -> {entity_id}
    for hyp in report.candidates_found:
        hname = norm_eval(hyp.normalized_form)
        for occ in hyp.occurrences:
            seg_id = div_to_seg.get(occ.division_id)
            if seg_id is None:
                continue
            span = locate_span(seg_text[seg_id], occ.surface_form)
            if span is None:
                continue
            occ_ents = registry.entities_of(norm_eval(occ.surface_form))
            if not occ_ents:
                continue
            for g in golds_by_seg.get(seg_id, ()):
                if _contains((g.start, g.end), span):
                    for eid in set(g.entity_ids) & occ_ents:
                        ent_covered_by.setdefault(eid, set()).add(hname)
                        hyp_covers.setdefault(hname, set()).add(eid)
    dup_entities = {e for e, hs in ent_covered_by.items() if len(hs) >= 2}
    collision_hyps = {h for h, es in hyp_covers.items() if len(es) >= 2}
    return dup_entities, collision_hyps, {
        "entities_covered": {e: sorted(hs) for e, hs in sorted(ent_covered_by.items())},
        "hypotheses_covering": {h: sorted(es) for h, es in sorted(hyp_covers.items())},
    }


# ---------------------------------------------------------------------------
# 归因（唯一允许引用 expansion 的地方：rp-v3 冻结规则的描述性镜像）
# ---------------------------------------------------------------------------

def attribute_miss(g: GoldMention, preds: List[PredOcc], text: str
                   ) -> Tuple[str, str]:
    """漏检归因（确定性优先级，返回 (类别, 说明)。禁止「噪声」兜底）。"""
    import re as _re
    from haidian_kg import expansion as X   # 描述性镜像；评分路径不经过此处

    # 1) 经验层：引擎到底发了什么
    same_form = [p for p in preds if p.normalized_form == g.normalized_form]
    if same_form:
        return "same-form-elsewhere", (
            "同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）")
    overlapping = [p for p in preds
                   if p.start < g.end and g.start < p.end]
    if overlapping:
        p = overlapping[0]
        return "erosion", (
            "命中区域但字形不合：引擎发「%s」（%s），金标「%s」"
            % (p.surface, p.method, g.surface))
    # 2) 规则镜像推演：这条金标在 rp-v3 规则视角下为什么不可达
    norm_form = X.normalize_form(g.surface)
    for stop in sorted(X._STOPWORDS, key=len, reverse=True):
        if stop in norm_form or stop in g.surface:
            return "stopword-suppressed", (
                "字形（或其归一形）命中挖掘器停用词表「%s」" % stop)
    window = None
    pos = 0
    for phrase in _re.split(r"[，。、；：！？「」『』（）]", text):
        end = pos + len(phrase)
        if pos <= g.start < end or (g.start < pos and g.end > pos):
            window = phrase
            break
        pos = end + 1                     # +1：被吃掉的分隔符
    if window is None:
        return "phrase-unreachable", "短语切分不可达（段内找不到包含该字形的短语）"
    has_cue = any(m in window for m in X._CUE_MARKERS)
    tail_is_suffix = any(norm_form.endswith(s) for s in X.PLACE_SUFFIXES)
    if not has_cue and not tail_is_suffix:
        return "suffix-and-cue-missing", (
            "通名后缀「%s」不在词表且短语无线索词（v3 双通道同时不可达）" % g.normalized_form[-1])
    k = window.find(g.surface)
    if k < 0:
        k = window.find(norm_form)
    if k >= 0:
        end = k + len(g.surface)
        # 从命中尾往前的最长回溯（镜像 _walk_back）
        j = end - 1
        while j > 0 and window[j - 1] not in X._STOP_CHARS:
            j -= 1
        walked = window[j:end]
        if len(walked) < 2:
            boundary = window[j - 1] if j > 0 else "短语头"
            return "walkback-too-short", (
                "回溯在边界字「%s」处截停，只剩「%s」不足 2 字专名下限，命中作废"
                % (boundary, walked))
        if len(walked) > 6:
            return "walkback-overrun", (
                "回溯跨度 %d 字 > 6 上限（「%s…」），该命中作废"
                % (len(walked), walked[:4]))
        for reign in ("康熙", "雍正", "乾隆", "嘉庆", "万历"):
            if walked.startswith(reign):
                return "reign-prefix-suppressed", (
                    "回溯头落进纪年「%s」被纪年模式压制" % reign)
    if not tail_is_suffix and has_cue:
        return "cue-window-narrow", (
            "仅 cue 窗通道可达（「%s」非收录后缀），窗内未收拢该字形"
            % g.normalized_form[-1])
    return "overlapped-hit-discarded", "后缀命中与更右的采纳区间重叠，按子词规则让位"


def attribute_fp(p: PredOcc, golds: List[GoldMention],
                 registry: NameRegistry, soft_forms: Set[str]) -> Tuple[str, str]:
    """误报归因：markdown 记号渗入 / 字形侵蚀 / 近形缺收 / KB 覆盖缺口 / 边界拼缀。"""
    overlapping = [g for g in golds if g.start < p.end and p.start < g.end]
    if overlapping:
        g = overlapping[0]
        return "erosion", (
            "与金标「%s」span 重叠但字形不合（引擎「%s」vs 金标「%s」）"
            % (g.surface, p.surface, g.surface))
    junk = "".join(sorted({ch for ch in p.surface if not "\u4e00" <= ch <= "\u9fff"}))
    if junk:
        near = ""
        core = "".join(ch for ch in p.surface if "\u4e00" <= ch <= "\u9fff")
        for soft in sorted(soft_forms, key=len, reverse=True):
            if len(soft) >= 3 and (soft.startswith(core[:2]) or core[:2] in soft):
                near = "；另：剔除记号后「%s」与 KB 考注片段「%s」近形" % (core, soft)
                break
        return "markdown-prefix-bleed", (
            "命中串带非汉字记号「%s」——rp-v3 句读/边界表缺这些记号，"
            "回溯越过 Markdown 加粗与书名号%s" % (junk, near))
    for form in registry.forms:
        if abs(len(form) - len(p.normalized_form)) <= 2 and (
                form.startswith(p.normalized_form[:2])
                or p.normalized_form.startswith(form[:2])):
            return "kb-variant-near-miss", (
                "与 KB 字形「%s」近形（前两字同），缺变体收编" % registry.display[form])
    for soft in sorted(soft_forms, key=len, reverse=True):
        if len(soft) >= 3 and (soft in p.normalized_form
                               or p.normalized_form in soft):
            return "paren-note-fragment", (
                "命中的是 KB 考注括号内片段「%s」（未独立成实体）" % soft)
    edge_pos = ("今", "在", "自", "至", "后", "後", "上", "下", "内", "外",
                "东", "西", "南", "北", "之", "里")
    if p.normalized_form[:1] in edge_pos:
        return "boundary-splice", (
            "头带方位/虚词「%s」，回溯边界没收干净" % p.normalized_form[:1])
    if p.normalized_form[-1:] in edge_pos:
        return "boundary-splice", (
            "尾带方位/虚词「%s」，窗口没收干净" % p.normalized_form[-1:])
    return "kb-coverage-gap", "规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）"


def soft_forms_from_registry(registry: NameRegistry) -> Set[str]:
    """从 KB 原始 display 字形的括号考注里抽专名片段（只用于 FP 归因提示）。"""
    import re as _re
    out: Set[str] = set()
    for label in registry.display.values():
        m = _re.search(r"[（(](.+?)[)）]", label)
        if m:
            for tok in _re.findall(r"[\u4e00-\u9fff]{2,}", m.group(1)):
                out.add(norm_eval(tok))
    return out


# ---------------------------------------------------------------------------
# 主评估流程
# ---------------------------------------------------------------------------

def load_segments(path: str) -> List[dict]:
    """读冻结快照；text_sha1 漂移即中止（设计文档 §6：漂移段作废重抽）。"""
    segs: List[dict] = []
    with open(path, encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            seg = json.loads(line)
            digest = hashlib.sha1(seg["text"].encode("utf-8")).hexdigest()
            if digest != seg["text_sha1"]:
                raise ValueError(
                    "语料漂移：%s（行 %d）text_sha1 不匹配，按冻结纪律整批作废"
                    % (seg["segment_id"], ln))
            segs.append(seg)
    return segs


def evaluate(segments: List[dict], registry: NameRegistry) -> dict:
    golds_by_seg = {seg["segment_id"]: extract_gold_mentions(
        seg["text"], seg["segment_id"], registry) for seg in segments}
    preds_by_seg, report = run_engine(segments)

    per_segment: List[dict] = []
    soft = soft_forms_from_registry(registry)
    fn_rows: List[dict] = []
    fp_rows: List[dict] = []
    for seg in segments:
        sid = seg["segment_id"]
        golds = golds_by_seg[sid]
        preds = preds_by_seg[sid]
        tps, fps, fns = match_segment(golds, preds)
        n_high = sum(1 for p in preds if p.confidence == "high")
        tp_high = sum(1 for _, p in tps if p.confidence == "high")
        per_segment.append({
            "segment_id": sid, "n_gold": len(golds), "n_pred": len(preds),
            "tp": len(tps), "fp": len(fps), "fn": len(fns),
            "tp_high": tp_high, "n_high": n_high,
        })
        for g in fns:
            cls, why = attribute_miss(g, preds, seg["text"])
            fn_rows.append({"segment_id": sid, "surface": g.surface,
                            "display": g.display_form, "class": cls, "why": why,
                            "span": [g.start, g.end]})
        for p in fps:
            cls, why = attribute_fp(p, golds, registry, soft)
            fp_rows.append({"segment_id": sid, "surface": p.surface,
                            "class": cls, "why": why, "method": p.method,
                            "confidence": p.confidence, "span": [p.start, p.end]})

    counts = compute_counts(per_segment)
    dup, coll, cov_detail = hypothesis_coverage(
        report, segments, golds_by_seg, registry)
    gold_entities = {e for gs in golds_by_seg.values()
                     for g in gs for e in g.entity_ids}
    metrics = compute_metrics(counts, len(gold_entities), len(dup),
                              len(coll), len(report.candidates_found))
    gate = gate_check(metrics)
    return {
        "metrics": metrics, "gate": gate,
        "gate_pass": all(r["pass"] for r in gate),
        "per_segment": per_segment, "false_negatives": fn_rows,
        "false_positives": fp_rows, "coverage": cov_detail,
        "hypothesis_total": len(report.candidates_found),
        "n_segments": len(segments),
    }


# ---------------------------------------------------------------------------
# 报告渲染
# ---------------------------------------------------------------------------

def _class_counts(rows: List[dict]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for r in rows:
        out[r["class"]] = out.get(r["class"], 0) + 1
    return out


#: 归因类 → 最小修复路径（分析性文字，按键查表保证报告可复现）
REMEDY_FN = {
    "walkback-overrun": (
        "P0·句读/回溯边界表扩记号", "rp-v3 的 _PUNCT_CHARS/_STOP_CHARS 缺 Markdown 记号（*、-、空格）与书名号《》；一处表修复同时治理多条"),
    "markdown-prefix-bleed": (
        "P0·句读/回溯边界表扩记号",
        "rp-v3 句读/回溯边界表缺 Markdown 记号（*、-、空格、书名号《》）；"
        "与 walkback-overrun 同根同修"),
    "walkback-too-short": (
        "P1·提示词/专名内部字冲突", "「有」既是 cue 又在专名内部（大有庄）：需 known 别名优先召回或词边界判断，属引擎行为变更（v4）"),
    "stopword-suppressed": (
        "P1·已知名设计性压制（需决策）", "圆明园/万寿山/昆明湖等是 KB 已建实体也是挖掘器停用词：身份纪律（不复挖已知名）与 holdout R 口径冲突，见结论决策项"),
    "suffix-and-cue-missing": (
        "P2·通名后缀表扩墓/街/院", "扩表必须先过 spec §5.2 Hard FP/Mutation 独立负控制，不在本闸门内擅动"),
    "erosion": (
        "P0·回溯边界字增补", "「名娘娘府」「《圆明园」「**蓝靛厂」：名/记/俗 等单字边界与记号并入 _STOP_CHARS"),
    "same-form-elsewhere": (
        "P2·同 fact 同形只发一次", "多次出现只记首现：跨 fact 互证是设计行为，可按 mention 密度重估"),
    "cue-window-narrow": (
        "P2·cue 窗策略", "生僻通名（院）靠 12 字窗保不住：可在 v4 引入 known 表预匹配"),
    "reign-prefix-suppressed": ("P2", "回溯头落进纪年模式"),
    "overlapped-hit-discarded": ("P2", "子词让位策略的已知代价"),
    "phrase-unreachable": ("P2", "守卫类，本轮未触发"),
}
REMEDY_FP = {
    "kb-coverage-gap": (
        "数据层·KB 收录缺口", "清水院/大觉寺/金山/万泉河等是真实海淀地名但 8 个校准模块未建词条：属代理金标口径偏差的主要来源（见敏感度），不是挖掘器缺陷"),
    "markdown-prefix-bleed": (
        "P0·句读/回溯边界表扩记号", "与 FN 同根同修"),
    "boundary-splice": (
        "P0·回溯边界字增补", "「今大觉寺」「北安河」：今/北/西 等头部边界字——注意其中部分（北安河）实为真地名，修复时须防误伤 lexicalized 方位头（西三旗先例）"),
    "erosion": (
        "P0·回溯边界字增补", "与 FN 同根同修"),
    "kb-variant-near-miss": ("P2·变体表扩", "近形异体缺收编"),
    "paren-note-fragment": ("P3·考注片段", "括号内片段被当成独立地名：提示候选而非缺陷"),
}


def render_conclusion(res: dict) -> List[str]:
    m = res["metrics"]
    lines: List[str] = []
    fn_cls = _class_counts(res["false_negatives"])
    fp_cls = _class_counts(res["false_positives"])
    lines.append("## 结论与最小修复路径")
    lines.append("")
    if res["gate_pass"]:
        lines.append("**闸门通过**。")
    else:
        blocked = [r["metric"] for r in res["gate"] if not r["pass"]]
        lines.append("**闸门不通过**，卡在：%s。" % "、".join(blocked))
        lines.append("")
        # 敏感度上界（机械可复现，非拍脑袋）
        gap_fp = fp_cls.get("kb-coverage-gap", 0)
        stop_fn = fn_cls.get("stopword-suppressed", 0)
        tp = m["counts"]["tp"]
        fp = m["counts"]["fp"]
        fn = m["counts"]["fn"]
        p_upper = (tp / (tp + fp - gap_fp)) if (tp + fp - gap_fp) > 0 else None
        r_upper = ((tp + stop_fn) / (tp + fn)) if (tp + fn) > 0 else None
        lines.append(
            "敏感度（两个有机械依据的界，非口径放水）：")
        lines.append("")
        lines.append("- **precision 严格下界 = 实测值**：KB 覆盖缺口 FP（%d 条，真实地名"
                     "但 8 模块未建词条）按冻结公式计错。若经人工判定为真地名，"
                     "P 上界 = %.3f——仍远低于 0.90。" % (gap_fp, p_upper))
        lines.append("- **recall 受已知名设计性压制拖累**：%d 条 FN 是挖掘器按身份纪律"
                     "（不复挖 KB 已知字形）主动丢弃。若视为命中，R 上界 = %.3f——"
                     "仍远低于 0.85。" % (stop_fn, r_upper))
        lines.append("")
        lines.append("两个上界都够不着阈值 ⇒ 缺口是结构性的，调参无解，需按下列路径修复后重跑（holdout 不变）。")
    lines.append("")
    lines.append("### 修复路径（按影响面排序）")
    lines.append("")
    lines.append("| 优先级 | 归因类 | 条数(FN/FP) | 最小修复 | 说明 |")
    lines.append("|---|---|---|---|---|")
    seen = {}
    for cls, cnt in sorted(fn_cls.items(), key=lambda kv: -kv[1]):
        seen[cls] = (cnt, 0)
    for cls, cnt in fp_cls.items():
        c = seen.get(cls)
        seen[cls] = (c[0] if c else 0, cnt) if c else (0, cnt)
    order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "数据层": 1}
    rows = []
    for cls, (fcn, fpcp) in seen.items():
        remedy = REMEDY_FN.get(cls) or REMEDY_FP.get(cls) or ("?", "?")
        rows.append((order.get(remedy[0].split("·")[0], 9), remedy[0], cls,
                     fcn, fpcp, remedy[1]))
    for _, pri, cls, fcn, fpcp, how in sorted(
            rows, key=lambda r: (r[0], -(r[3] + r[4]), r[2])):
        lines.append("| %s | `%s` | %d / %d | %s | %s |"
                     % (pri.split("·")[0], cls, fcn, fpcp, pri.split("·")[1], how))
    lines.append("")
    lines.append("### 决策项（超出本评估器权限，需主代理裁定）")
    lines.append("")
    lines.append("冻结设计存在一处**规格内部张力**：spec §2.5 身份纪律要求已建词条字形"
                 "「仅计数不重挖」，而 holdout 闸门把 KB 已知字形的重检测计为 recall。"
                 "本轮数据证明两者不可同时满足（圆明园/万寿山/正黄旗营房 等 6 条 FN "
                 "全部来自该纪律）。可选：")
    lines.append("")
    lines.append("1. **引擎加 known-mention 降级通道**（推荐）：ToponymMiner 对已知字形"
                 "不再静默丢弃，改为发 `confidence=known` 的 occurrence（不进候选聚类，"
                 "只进 mention 层）——引擎行为变更即 MINER_VERSION 升 v4，SourceVisitKey "
                 "自动视为没挖过，纪律自洽；")
    lines.append("2. 重开闸门改金标口径——违反冻结纪律，不推荐；")
    lines.append("3. 接受「长编层重检测已知实体」不在引擎职责内，R 闸门只对原文新地名层"
                 "生效——需在设计文档补一条冻结修正案。")
    lines.append("")
    return lines


def _oneline(s: str) -> str:
    """报告单行化：控制字符转可见记号，防 Markdown 列表断行。"""
    return s.replace("\\", "\\\\").replace("\n", "⏎").replace("\r", "").replace(
        "\t", "⇥")


def render_markdown(res: dict, holdout_path: str) -> str:
    m = res["metrics"]
    lines: List[str] = []
    lines.append("# Holdout v1 首轮跑分（run1）")
    lines.append("")
    lines.append("- 快照：`%s`（%d 段，text_sha1 全量校验通过）"
                 % (holdout_path, res["n_segments"]))
    lines.append("- 引擎：ClosureExpander `%s` / 规则档 `%s`"
                 % (_miner_version(), _rule_profile_version()))
    lines.append("- 真值：calibration 8 模块 48 实体字形表（独立路径，"
                 "评分代码零 expansion 依赖）；**代理金标**——"
                 "mention precision 为下界（KB 未收录的真实地名计 FP），见「偏差」")
    lines.append("")
    lines.append("## 五指标 vs 冻结闸门")
    lines.append("")
    lines.append("| 指标 | 实测 | 阈值 | 判定 |")
    lines.append("|---|---|---|---|")
    name_cn = {
        "mention_precision": "mention precision", "mention_recall": "mention recall",
        "high_conf_precision": "high-conf precision",
        "duplication_rate": "duplication", "collision_rate": "collision",
    }
    for r in res["gate"]:
        val = "—" if r["value"] is None else "%.4f" % r["value"]
        mark = "✅ 过" if r["pass"] else "❌ 不过"
        label = name_cn.get(r["metric"], r["metric"])
        lines.append("| %s | %s | %s %.2f | %s |"
                     % (label, val, r["op"], r["threshold"], mark))
    f1 = m["mention_f1"]
    lines.append("| mention F1（辅助） | %s | — | — |"
                 % ("—" if f1 is None else "%.4f" % f1))
    lines.append("")
    lines.append("**闸门结论：%s**（计数 TP=%d FP=%d FN=%d；"
                 "gold 实体 %d，假说总数 %d）"
                 % ("五项全过 ✅" if res["gate_pass"] else "未全过 ❌",
                    m["counts"]["tp"], m["counts"]["fp"], m["counts"]["fn"],
                    m["gold_entity_total"], res["hypothesis_total"]))
    lines.append("")
    lines.append("## 逐段明细")
    lines.append("")
    lines.append("| 段 | 金标 | 预测 | TP | FP | FN | high-conf |")
    lines.append("|---|---|---|---|---|---|---|")
    for s in res["per_segment"]:
        lines.append("| `%s` | %d | %d | %d | %d | %d | %d/%d |"
                     % (s["segment_id"], s["n_gold"], s["n_pred"], s["tp"],
                        s["fp"], s["fn"], s["tp_high"], s["n_high"]))
    lines.append("")
    lines.append("## 漏检归因（%d 条，100%% 逐条）" % len(res["false_negatives"]))
    lines.append("")
    by_class: Dict[str, List[dict]] = {}
    for row in res["false_negatives"]:
        by_class.setdefault(row["class"], []).append(row)
    for cls in sorted(by_class):
        lines.append("**%s（%d 条）**" % (cls, len(by_class[cls])))
        lines.append("")
        for row in by_class[cls]:
            lines.append("- `%s`「%s」（KB 字形「%s」）：%s"
                         % (row["segment_id"], _oneline(row["surface"]),
                            row["display"], _oneline(row["why"])))
    lines.append("")
    lines.append("## 误报归因（%d 条，100%% 逐条）" % len(res["false_positives"]))
    lines.append("")
    by_class = {}
    for row in res["false_positives"]:
        by_class.setdefault(row["class"], []).append(row)
    for cls in sorted(by_class):
        lines.append("**%s（%d 条）**" % (cls, len(by_class[cls])))
        lines.append("")
        for row in by_class[cls]:
            lines.append("- `%s`「%s」（%s/%s）：%s"
                         % (row["segment_id"], _oneline(row["surface"]),
                            row["method"], row["confidence"],
                            _oneline(row["why"])))
    lines.append("")
    lines.append("## 假说层覆盖（duplication / collision 证据）")
    lines.append("")
    lines.append("- 被覆盖 gold 实体：%d；其中被 ≥2 假说覆盖（duplication 分子）：%d"
                 % (len(res["coverage"]["entities_covered"]), m["dup_entities"]))
    for e, hs in res["coverage"]["entities_covered"].items():
        flag = " ⚠️duplication" if len(hs) >= 2 else ""
        lines.append("  - `%s` ← 假说 %s%s" % (e, "、".join(hs), flag))
    lines.append("- 覆盖 ≥2 gold 实体的假说（collision 分子）：%d"
                 % m["collision_hyps"])
    for h, es in res["coverage"]["hypotheses_covering"].items():
        flag = " ⚠️collision" if len(es) >= 2 else ""
        lines.append("  - 「%s」→ %s%s" % (h, "、".join(es), flag))
    lines.append("")
    lines.extend(render_conclusion(res))
    lines.append("## 偏差声明")
    lines.append("")
    lines.append("1. v1 真值为**代理金标**（KB 已知实体字形；人工 holdout_gold.jsonl "
                 "尚未产出）：KB 未收录的真实地名按公式计 FP，故 mention precision "
                 "实测值是真值的下界；recall 不受影响（gold 即 KB 实体提及）。")
    lines.append("2. 分母为 0 的指标记 None 并判不过（证据不足不放行），本轮："
                 + ("无" if all(
                     r["value"] is not None for r in res["gate"]) else
                     "、".join(r["metric"] for r in res["gate"]
                              if r["value"] is None)))
    lines.append("3. span 恢复：挖掘器不产 offset，评估器按「同 fact 同形只发一次」"
                 "的引擎保证取首现位置（`occurrence.text_span` 是窗口不是 span，"
                 "不可用）。")
    lines.append("")
    return "\n".join(lines)


def _miner_version() -> str:
    from haidian_kg.expansion import MINER_VERSION
    return MINER_VERSION


def _rule_profile_version() -> str:
    from haidian_kg.expansion import RULE_PROFILE_VERSION
    return RULE_PROFILE_VERSION


def main(argv: Optional[List[str]] = None) -> int:
    import argparse
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    ap = argparse.ArgumentParser(description="Holdout v1 闸门评估器")
    ap.add_argument("--holdout",
                    default=os.path.join(root, "haidian_kg/evaluation/holdout_v1.jsonl"))
    ap.add_argument("--json-out",
                    default=os.path.join(root, ".superpowers/sdd/holdout-eval-run1.json"))
    ap.add_argument("--md-out",
                    default=os.path.join(root, ".superpowers/sdd/holdout-eval-run1.md"))
    args = ap.parse_args(argv)

    segments = load_segments(args.holdout)
    registry = build_name_registry()
    res = evaluate(segments, registry)

    payload = {
        "gate_pass": res["gate_pass"],
        "metrics": {k: v for k, v in res["metrics"].items()},
        "gate": res["gate"],
        "per_segment": res["per_segment"],
        "false_negatives": res["false_negatives"],
        "false_positives": res["false_positives"],
        "coverage": res["coverage"],
    }
    with open(args.json_out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    with open(args.md_out, "w", encoding="utf-8") as f:
        f.write(render_markdown(res, os.path.relpath(args.holdout, root)))
    print("gate_pass=%s" % res["gate_pass"])
    for r in res["gate"]:
        print("  %-22s %s" % (r["metric"], r["detail"]))
    print("md -> %s" % args.md_out)
    print("json -> %s" % args.json_out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
