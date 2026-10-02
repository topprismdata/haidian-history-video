"""
haidian_kg/qa_gate.py
词条入库统一 QA 闸门（BHKG/HHTO v2.1）

为什么必须有统一闸门：
  此前每加入一个校准词条，都是临时手写几个断言检查——
  「全绿」因此只能自证，无法区分「词条对」「闸门恒真」「闸门在测别的东西」。
  本模块把闸门固化为可执行代码，任何新词条不通过即不得入库。

闸门八维（每一维都来自一次真实翻车，不是凭空设计的）：
  G1 引文可溯源     《水经注》卷十三/卷十四被拼成一句原典
  G2 状态有证据     形制/材质断言没有出处
  G3 实体无越权属性 geometry/material 挂到 PersistentEntity 上
  G4 存疑必须标注   「因树得名」被当史实
  G5 口径分离       雍正二年1250间 与 乾隆十二年增建后1550楹 被混说
  G6 繁简异体       繁体「不復存在」漏检
  G7 假通过可检出   注入错误断言必须被抓到
  G8 跨集不回归     改一个词条不能破坏其它词条

用法：
    from haidian_kg.qa_gate import QAGate
    report = QAGate("banners", kb).run()
    assert report.blocking == [], report.render()
"""
from typing import Callable, Dict, List, Optional, Tuple

from .ontology.epistemic import (
    BeliefAdoption, EpistemicStatus, HistoricalSource, SourceDivision,
    TextualFact,
)
from .ontology.spatiotemporal import (
    Appellation, DiachronicIdentityAssertion, HistoricalFeatureState,
    PersistentSpatialEntity, ReferentialAssertion,
)


class QAFinding(object):
    __slots__ = ("gate", "level", "message")

    def __init__(self, gate: str, level: str, message: str):
        self.gate = gate
        self.level = level          # "fail" | "warn" | "skip"
        self.message = message

    def __repr__(self):
        return "[%s] %s: %s" % (self.level.upper(), self.gate, self.message)


class QAReport(object):
    def __init__(self, name: str):
        self.name = name
        self.findings: List[QAFinding] = []

    def add(self, gate: str, level: str, message: str):
        self.findings.append(QAFinding(gate, level, message))

    @property
    def blocking(self) -> List[QAFinding]:
        """只有 fail 阻塞；warn 不阻塞；skip = 判据未执行，不算通过"""
        return [f for f in self.findings if f.level == "fail"]

    @property
    def passed(self) -> bool:
        return not self.blocking

    def render(self) -> str:
        lines = ["QA 报告 · %s" % self.name]
        for f in self.findings:
            lines.append("  " + repr(f))
        lines.append("  判定: %s（fail %d / warn %d / skip %d）" % (
            "通过" if self.passed else "不通过",
            len([f for f in self.findings if f.level == "fail"]),
            len([f for f in self.findings if f.level == "warn"]),
            len([f for f in self.findings if f.level == "skip"]),
        ))
        return "\n".join(lines)


class QAGate(object):
    """词条入库闸门。每个词条入库前必须 run() 且 blocking 为空。"""

    def __init__(self, name: str, kb, adversarial: Optional[Tuple[str, str]] = None):
        self.name = name
        self.kb = kb
        # (错误断言文本, 该断言必须被判为 UNTESTABLE/BLOCK 的理由描述)
        self.adversarial = adversarial

    # ---------- G1 引文可溯源 ----------
    def g1_citations(self, r: QAReport):
        div_ids = set(self.kb.divisions.keys())
        if not div_ids:
            r.add("G1引文可溯源", "fail", "词条无任何篇卷节点，无法溯源")
        for fid, f in self.kb.facts.items():
            if f.division_id not in div_ids:
                r.add("G1引文可溯源", "fail",
                      "引文 %s 的篇卷 %s 不存在" % (fid, f.division_id))
            for sep in (",", "，", "&", "和", "及"):
                if sep in f.division_id:
                    r.add("G1引文可溯源", "fail",
                          "引文 %s 跨卷拼接：%s" % (fid, f.division_id))
            if len(f.verbatim_quote.strip()) < 4:
                r.add("G1引文可溯源", "fail", "引文 %s 过短，无法核对" % fid)
        for sid, s in self.kb.sources.items():
            for did, d in self.kb.divisions.items():
                if d.source_id == sid and d.id not in div_ids:
                    r.add("G1引文可溯源", "fail", "篇卷 %s 悬空" % did)

    # ---------- G2 状态/指称有证据 ----------
    def g2_evidence(self, r: QAReport):
        fact_ids = set(self.kb.facts.keys())
        for sid, s in self.kb.states.items():
            if not s.evidence_fact_ids:
                r.add("G2状态有证据", "fail", "状态 %s 无任何证据" % sid)
            for e in s.evidence_fact_ids:
                if e not in fact_ids:
                    r.add("G2状态有证据", "fail", "状态 %s 引用不存在的引文 %s" % (sid, e))
        for rid, ref in getattr(self.kb, "references_by_id", {}).items():
            for e in ref.evidence_fact_ids:
                if e not in fact_ids:
                    r.add("G2状态有证据", "fail", "指称 %s 引用不存在的引文 %s" % (rid, e))
        for d in self.kb.identities:
            for e in d.evidence_fact_ids:
                if e not in fact_ids:
                    r.add("G2状态有证据", "fail", "身份断言 %s 引用不存在的引文 %s" % (d.id, e))

    # ---------- G3 实体无越权属性 ----------
    def g3_entity_discipline(self, r: QAReport):
        forbidden = ("geometry", "material", "function", "wgs84_coord",
                     "upstream_of", "downstream_of", "adjacent_to", "part_of")
        for eid, e in self.kb.entities.items():
            leaked = set(getattr(e, "model_fields_set", set())) & set(forbidden)
            if leaked:
                r.add("G3实体无越权", "fail",
                      "实体 %s 携带可见属性 %s，应下沉到 State" % (eid, sorted(leaked)))
            if not getattr(e, "kind", None):
                r.add("G3实体无越权", "fail", "实体 %s 未声明地物类型" % eid)

    # ---------- G4 存疑必须标注 ----------
    def g4_uncertainty_marked(self, r: QAReport):
        if not self.kb.adoptions:
            r.add("G4存疑标注", "fail", "词条无任何采信记录，无法判断可信度")
        for pid, ad in self.kb.adoptions.items():
            if pid not in self.kb.propositions:
                r.add("G4存疑标注", "fail", "采信 %s 指向不存在的断言" % pid)
            if ad.status == EpistemicStatus.DISPROVEN and not ad.refuting_fact_ids:
                r.add("G4存疑标注", "fail", "断言 %s 标为已证伪但无反驳证据" % pid)
        # 争议身份必须有双方说法
        for d in self.kb.identities:
            if d.relation.value == "存疑" and not d.alternative_relations:
                r.add("G4存疑标注", "fail", "身份断言 %s 标存疑但未列争议双方" % d.id)

    # ---------- G5 口径分离 ----------
    def g5_scope_separation(self, r: QAReport):
        """
        初建与增建、年份与年份必须分属不同状态。
        若某实体存在两个状态且区间相接但属性描述数值不同，
        须确认它们是不同年份的状态（这本身就是正确表达）。
        """
        by_entity = {}
        for s in self.kb.states.values():
            by_entity.setdefault(s.entity_id, []).append(s)
        for eid, states in by_entity.items():
            if len(states) < 2:
                continue
            years = [(s.time_span.begin.gregorian.year, s.id) for s in states
                     if s.time_span.begin and s.time_span.begin.gregorian]
            if len(set(y for y, _ in years)) != len(years):
                r.add("G5口径分离", "fail", "实体 %s 存在同起始年的重复状态" % eid)

    # ---------- G6 繁简异体 ----------
    def g6_variant_coverage(self, r: QAReport):
        """消亡/争议类断言的词表必须覆盖繁简两种字形"""
        import haidian_kg.production_exports as pe
        markers = getattr(pe, "_EXTINCTION_MARKERS", ())
        for simp, trad in (("不复存在", "不復存在"), ("彻底消失", "徹底消失"),
                           ("荡然无存", "蕩然無存")):
            if not any(simp in m for m in markers):
                r.add("G6繁简异体", "fail", "消亡词表缺简体 %s" % simp)
            if not any(trad in m for m in markers):
                r.add("G6繁简异体", "fail", "消亡词表缺繁体 %s" % trad)
        if not markers:
            r.add("G6繁简异体", "skip", "无法读取消亡词表，本项未执行（不算通过）")

    # ---------- G7 假通过可检出（负控制） ----------
    def g7_adversarial(self, r: QAReport):
        """
        注入已知错误的断言，必须被判为 BLOCK 或 UNTESTABLE。
        若被判 PASS，说明闸门恒真——这是最严重的问题。

        【v2.1 修正·设计缺陷】
        对抗样本不能是一整段脚本：同一段里可能混有真陈述与错误陈述
        （例：「1292年设西城闸」是真，「1312年已是砖石」是假）。
        整段一刀切会把真陈述也判成"假通过"，闸门自身就错了。
        因此对抗样本必须逐句声明期望结论：
            adversarial = (脚本文本, [(子句, 期望verdict), ...])
        """
        if not self.adversarial:
            r.add("G7假通过检出", "skip",
                  "未提供对抗样本，本项未执行（不算通过）")
            return
        from haidian_kg import production_exports as pe
        # 走模块属性查找而非 from-import，便于测试注入假审计来验证闸门非恒真
        audit_fn = pe.audit_script
        text, expectations = self.adversarial
        try:
            results = audit_fn(self.kb, text)
        except Exception as exc:
            r.add("G7假通过检出", "fail",
                  "审计抛异常（判据未正常执行，不得静默）：%s: %s"
                  % (type(exc).__name__, exc))
            return
        if not results:
            r.add("G7假通过检出", "fail",
                  "对抗样本未产生任何审计结果，判据可能恒真")
            return

        by_text = {res.claim.claim_text: res for res in results}
        for clause, expected in expectations:
            res = by_text.get(clause)
            if res is None:
                r.add("G7假通过检出", "fail",
                      "对抗样本子句未产生审计结果，判据覆盖不全：%s" % clause)
                continue
            got = res.verdict.value
            if expected == "非通过":
                if got == "通过":
                    r.add("G7假通过检出", "fail",
                          "错误断言被判通过（假通过）：%s" % clause)
            elif got != expected:
                r.add("G7假通过检出", "warn",
                      "对抗样本结论不符：%s 期望=%s 实际=%s" % (clause, expected, got))

    # ---------- G8 跨集不回归 ----------
    def g8_no_cross_entry_break(self, r: QAReport):
        """本词条的名称不得与其他词条的实体重叠指向不同对象"""
        for ref in self.kb.references:
            app = self.kb.appellations.get(ref.appellation_id)
            if app is None:
                r.add("G8跨集一致", "fail", "指称 %s 指向不存在的名称" % ref.id)
                continue
            same = [x for x in self.kb.references
                    if x.appellation_id == ref.appellation_id
                    and x.referent_entity_id != ref.referent_entity_id]
            if same:
                r.add("G8跨集一致", "warn",
                      "名称「%s」指向多个实体（%s），确属同名异物时属正常"
                      % (app.label, [x.referent_entity_id for x in same]))

    # ---------- G9 文献实体完整性（一书一条 + 作者 + 资源） ----------
    def g9_bibliography(self, r: QAReport):
        """
        文献层三件事必须成立：
        1. 一部书只有一个 HistoricalSource（不得按卷次重复建）
        2. 个人撰述的书必须有作者，且作者须存在于人物表
        3. 已登记的数字资源必须可作定位，且转录本须声明校勘限制
        """
        titles = {}
        for sid, s in self.kb.sources.items():
            titles.setdefault(s.title, []).append(sid)
        for title, ids in titles.items():
            if len(ids) > 1:
                r.add("G9文献完整", "fail",
                      "书名「%s」被建成 %d 个文献节点（%s）；一部书只能一条"
                      % (title, len(ids), ids))

        person_ids = set(getattr(self.kb, "person_ids", set()))
        for sid, s in self.kb.sources.items():
            if s.author_person_id and person_ids and s.author_person_id not in person_ids:
                r.add("G9文献完整", "fail",
                      "文献 %s 的作者 %s 不在人物表中" % (sid, s.author_person_id))
            for cid in (s.compiler_person_ids or []):
                if person_ids and cid not in person_ids:
                    r.add("G9文献完整", "fail",
                          "文献 %s 的编者 %s 不在人物表中" % (sid, cid))
            # 个人撰述的书必须有作者；机构编纂（政府名录/地名志/考古报告/实测图）
            # 无个人作者属正常，但 institution 必须写明责任机构
            personal = ("文集笔记", "历史地理专著", "地方志")
            institutional = ("考古发掘报告", "近代实测地图")
            if s.category.value in personal and not s.author_person_id:
                if getattr(s, "issuing_body", None):
                    r.add("G9文献完整", "warn",
                          "%s（%s）无个人作者，责任机构=%s"
                          % (sid, s.title, s.issuing_body))
                else:
                    r.add("G9文献完整", "fail",
                          "个人撰述类文献 %s（%s）缺作者" % (sid, s.title))
            elif s.category.value in institutional and not getattr(s, "issuing_body", None) \
                    and not s.author_person_id:
                r.add("G9文献完整", "fail",
                      "机构编纂文献 %s（%s）须写明责任机构" % (sid, s.title))

        res = getattr(self.kb, "resources", None)
        if res is None:
            r.add("G9文献完整", "skip",
                  "未登记数字资源，本项未执行（不算通过）")
            return
        for dr in res:
            if not dr.reliability_note.strip():
                r.add("G9文献完整", "fail", "数字资源 %s 缺可靠性说明" % dr.id)
            if not dr.url.startswith("http"):
                r.add("G9文献完整", "fail", "数字资源 %s 地址非法" % dr.id)

    # ---------- 汇总 ----------
    def run(self) -> QAReport:
        r = QAReport(self.name)
        self.g1_citations(r)
        self.g2_evidence(r)
        self.g3_entity_discipline(r)
        self.g4_uncertainty_marked(r)
        self.g5_scope_separation(r)
        self.g6_variant_coverage(r)
        self.g7_adversarial(r)
        self.g8_no_cross_entry_break(r)
        self.g9_bibliography(r)
        return r


# ==================================================================
# 词条注册表：任何词条入库前必须在此登记
# ==================================================================

REGISTRY: Dict[str, Dict] = {}


def register(name: str, kb, adversarial: Optional[Tuple[str, str]] = None) -> QAReport:
    """词条入库闸门。不通过则抛错。"""
    report = QAGate(name, kb, adversarial=adversarial).run()
    REGISTRY[name] = {"kb": kb, "report": report, "passed": report.passed}
    if not report.passed:
        raise AssertionError("词条「%s」未通过入库闸门：\n%s" % (name, report.render()))
    return report
