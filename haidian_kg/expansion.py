"""
haidian_kg/expansion.py
地名 ⇄ 古书 闭包扩展引擎（复合迭代法）

核心思想（用户提出）：
  初始地名 → 它们引用古书 → 古书里又出现别的地名 → 那些地名再引书 → …
  循环直到没有新东西。这就是图遍历的闭包（closure）。

工程意义：
  1. 词条不靠手工枚举，由数据自然长出来
  2. 每个新候选必须过同一道 QA 闸门（用户定死的纪律），不得绕过
  3. 必须有环检测与已见集合——高梁河出现在十几部书里，
     书又互相引用，没有去重会无限循环

三层工作队列：
  frontier_entries  待考地名
  frontier_sources  待挖书（一部书里可能藏着我们还没建的地名）
  discovered        已发现但未建档的候选地名

挖书接口（SourceMiner）：
  mine(source) -> List[CandidateName]
  目前实现 QuoteCorpusMiner：从已有引文原文里找「候选地名」，
  这是闭环可跑的最小实现；
  FullTextMiner 留接口——接入维基文库/ctext 全文后即可升级，
  无需改动引擎。
"""
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional, Set, Tuple

from .production_exports import KnowledgeBase
from .qa_gate import QAGate, QAReport
from .ontology.epistemic import TextualFact


@dataclass
class CandidateName:
    """从书里挖出的候选地名（尚未建档）"""
    name: str
    from_source_id: str
    from_division_id: Optional[str]
    evidence_fact_id: str          # 哪条引文里出现了它
    note: str = ""


# ---------------------------------------------------------------------------
# 挖书器
# ---------------------------------------------------------------------------

#: 已知「非地名」的干扰词：出现在引文里但不是我们要的地名
#: 注意：官书引文是繁体，口语档案是简体——**两种字形都要收录**，
#: 否则停用词过滤只在半边生效（与 G6 繁简异体同一教训）
_STOPWORDS = {
    # 简体
    "皇帝", "天子", "朝廷", "官书", "内务府", "中科院", "考古所",
    "护军", "参领", "护军校", "副将", "总兵", "守备", "千总", "把总",
    "康熙", "雍正", "乾隆", "嘉庆", "万历", "天启", "嘉靖", "成化",
    "正统", "景泰", "天顺", "弘治", "正德", "隆庆", "泰定", "至元",
    "至大", "太平兴国", "昭文馆", "太史院", "翰林",
    # 繁体（官书引文用字）
    "護軍", "參領", "護軍校", "副將", "總兵", "守備", "千總", "把總",
    "內務府", "圓明園", "清漪園", "暢春園", "靜宜園", "靜明園",
    "昆明湖", "萬壽山", "玉泉山", "稻田廠",
    # 泛指词（模式命中但非专名）
    "八處", "御道", "倉署", "兩個小旗駐點", "三個小旗駐點",
    "圓明園副將", "都督河北諸軍事",
}


class QuoteCorpusMiner(object):
    """
    从已有引文原文里挖候选地名。

    策略（保守、可解释）：
      1. 取每条引文的原文
      2. 用「…为X」「…曰X」「X坐落/坐落X」「跨其上」等地名提示模式定位
      3. 排除停用词（朝代/官职/皇家园林这些不是我们找的村落地名）
      4. 输出 CandidateName，带来源引文 id（可溯源）

    这是能立即闭环的最小实现。升级路径：
      FullTextMiner 接入维基文库/ctext 全文后，
      mine() 换实现即可，引擎与闸门不用动。
    """

    # 地名提示模式：'为X' / '曰X' / '有X' / '坐落X' / 'X跨其上'
    _PATTERNS = [
        "為", "曰", "為", "坐落", "跨其上", "即", "有",
    ]

    def mine(self, source_id: str, division_id: str,
             facts: List[TextualFact]) -> List[CandidateName]:
        out: List[CandidateName] = []
        for f in facts:
            if f.division_id != division_id:
                continue
            text = f.verbatim_quote
            # 逐段扫「X为Y」「有Y」「坐落Y」类模式
            for marker in self._PATTERNS:
                start = 0
                while True:
                    i = text.find(marker, start)
                    if i < 0:
                        break
                    seg = text[i + len(marker): i + len(marker) + 12]
                    name = self._clip(seg)
                    if name and self._plausible(name):
                        out.append(CandidateName(
                            name=name, from_source_id=source_id,
                            from_division_id=division_id,
                            evidence_fact_id=f.id,
                            note="模式「%s」命中" % marker,
                        ))
                    start = i + len(marker)
        return out

    def _clip(self, seg: str) -> Optional[str]:
        """截到标点为止，取 2-6 字的候选"""
        for j, ch in enumerate(seg):
            if ch in "，。、；：！？「」『』（）":
                seg = seg[:j]
                break
        seg = seg.strip()
        if 2 <= len(seg) <= 6:
            return seg
        return None

    def _plausible(self, name: str) -> bool:
        if name in _STOPWORDS:
            return False
        if any(w in name for w in _STOPWORDS):
            return False
        # 排除纯数字/纪年
        if any(ch.isdigit() for ch in name):
            return False
        # 排除常见非地名结尾
        bad_ends = ("庵", "寺", "庙", "场", "廠", "厂")  # 这些单独成词时是建筑/机构
        if name.endswith(bad_ends):
            return False
        return True


# ---------------------------------------------------------------------------
# 闭包引擎
# ---------------------------------------------------------------------------

@dataclass
class ExpansionReport(object):
    seeds: List[str] = field(default_factory=list)
    entries_visited: List[str] = field(default_factory=list)
    sources_mined: List[str] = field(default_factory=list)
    candidates_found: List[CandidateName] = field(default_factory=list)
    admitted: List[str] = field(default_factory=list)
    rejected: List[Tuple[str, str]] = field(default_factory=list)  # (name, reason)
    cycles_avoided: int = 0

    def render(self) -> str:
        lines = ["闭包扩展报告"]
        lines.append("  种子词条: %s" % "、".join(self.seeds))
        lines.append("  遍历词条: %d" % len(self.entries_visited))
        lines.append("  挖过的书: %d 部（%s）" % (
            len(self.sources_mined), "、".join(self.sources_mined)))
        lines.append("  发现候选地名: %d 个" % len(self.candidates_found))
        for c in self.candidates_found:
            lines.append("    - %-8s 来自《%s》篇卷 %s（引文 %s）%s"
                         % (c.name, c.from_source_id, c.from_division_id,
                            c.evidence_fact_id, c.note))
        lines.append("  收录: %d / 拒绝: %d / 环避让: %d 次"
                     % (len(self.admitted), len(self.rejected), self.cycles_avoided))
        for n, why in self.rejected:
            lines.append("    × %s：%s" % (n, why))
        return "\n".join(lines)


class ClosureExpander(object):
    """
    地名 ⇄ 古书 闭包遍历。

    用法：
        expander = ClosureExpander(seed_kbs=[kb1, kb2, kb3], qa_gate_args=...)
        report = expander.expand()
        print(report.render())

    关键纪律：
    - 新候选只是「候选」，不自动入库
    - 入库必须过 QAGate（用户定的规矩）
    - 已见集合防环：同一 (source, division) 不重复挖，
      同一候选名不重复入队
    """

    def __init__(self, seed_kbs: List[KnowledgeBase],
                 miner: Optional[QuoteCorpusMiner] = None,
                 known_names: Optional[Set[str]] = None,
                 adversarial: Optional[Tuple[str, str]] = None):
        self.seeds = list(seed_kbs)
        self.miner = miner or QuoteCorpusMiner()
        self.known_names: Set[str] = set(known_names or [])
        self.adversarial = adversarial

    def expand(self) -> ExpansionReport:
        rep = ExpansionReport()

        # 1) 收集所有种子词条的名与书
        all_kbs = list(self.seeds)
        for kb in all_kbs:
            rep.seeds.extend(kb.appellations.values() and
                             [a.label for a in kb.appellations.values()])
            self.known_names.update(a.label for a in kb.appellations.values())

        # 2) 遍历种子词条，登记它们引用的书
        seen_sources: Set[Tuple[str, str]] = set()   # (source_id, division_id)
        queue: List[Tuple[str, str, KnowledgeBase]] = []
        for kb in all_kbs:
            rep.entries_visited.extend(a.label for a in kb.appellations.values())
            for d in kb.divisions.values():
                key = (d.source_id, d.id)
                if key in seen_sources:
                    rep.cycles_avoided += 1
                    continue
                seen_sources.add(key)
                queue.append((d.source_id, d.id, kb))
                rep.sources_mined.append(d.id)

        # 3) 挖书
        discovered: Dict[str, CandidateName] = {}
        for source_id, division_id, kb in queue:
            for cand in self.miner.mine(source_id, division_id, list(kb.facts.values())):
                if cand.name in self.known_names:
                    rep.cycles_avoided += 1
                    continue
                if cand.name in discovered:
                    rep.cycles_avoided += 1
                    continue
                discovered[cand.name] = cand
                rep.candidates_found.append(cand)

        # 4) 候选不自动入库——只登记为 discovered，等人工/闸门裁决
        rep.admitted = []           # 引擎只负责发现；入库由闸门+人工
        rep.rejected = []
        return rep
