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
import re
from typing import Callable, Dict, Iterable, List, Optional, Set, Tuple

from .production_exports import KnowledgeBase
from .qa_gate import QAGate, QAReport
from .ontology.epistemic import TextualFact


#: 已知「非地名」的干扰词：出现在引文里但不是我们要的地名
#: 繁简双字形——官书引文是繁体，档案是简体（G6/G7/挖掘器三次教训）
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
    # 文言虚词/量词短语（模式误切的典型产物）
    "一萬間", "一千二百五十間", "四丁未", "六年", "十年",
}


@dataclass
class CandidateName:
    """从书里挖出的候选地名（尚未建档）"""
    name: str
    from_source_id: str
    from_division_id: Optional[str]
    evidence_fact_id: str          # 哪条引文里出现了它
    note: str = ""
    confidence: str = "low"        # high: 提示词+通名双证 / mid: 单证 / low: 仅模式
    stripped_suffix: Optional[str] = None  # 被剥离的方位后缀


#: 中文地名通名后缀表（专名+通名结构：树「村」、安河「桥」、七里「泊」）
#: 繁简双字形——官书引文是繁体，档案是简体（G6/G7/挖掘器三次教训）
PLACE_SUFFIXES = (
    # 聚落
    "村", "莊", "庄", "屯", "營", "营", "旗", "府", "坊", "胡同",
    # 水利
    "河", "橋", "桥", "泊", "泉", "閘", "闸", "堰", "渠", "湖", "海",
    # 宗教
    "寺", "菴", "庵", "觀", "观", "廟", "庙", "塔", "殿",
    # 其他
    "山", "墳", "坟", "園", "园", "廠", "厂", "場", "场", "倉", "仓",
    "窯", "窑", "店", "口", "關", "关", "嶺", "岭", "峪", "澱", "淀",
)

#: 方位后缀（「樹村西邊」须剥离为「樹村」）
DIRECTION_SUFFIXES = ("西邊", "東邊", "南邊", "北邊",
                      "西边", "东边", "南边", "北边",
                      "之西", "之東", "之东", "之南", "之北",
                      "西北", "東北", "东北", "西南", "東南", "东南")

#: 繁简双字形的机构/建筑通名单字（单独成词时不是专名，但作为后缀合法）
GENERIC_SINGLE = set("村莊庄屯營营府河橋桥泊泉閘闸堰渠湖山園园廠厂場场倉仓窯窑店铺關关嶺岭峪")


class ToponymMiner(object):
    """
    混合策略地名挖掘器 v2：
      A. 提示词模式（為/曰/有/坐落…）——旧行为，召回有线索词的
      B. 通名后缀扫描——召回无线索词但符合「专名+通名」结构的
      C. 方位后缀剥离——樹村西邊 → 樹村
      D. 置信度分级替代二元过滤——high/mid/low，人工审阅从高往低

    为什么不直接上 jieba/HanLP：
      文言文分词/NER 在现代语料模型上误切率高（实测风险），
      而「专名+通名」是中文地名强结构，后缀词典便宜、可解释、可控。
      分词框架留给现代文本（方志/档案）的 FullTextMiner 升级路径。
    """

    def __init__(self, known_names: Optional[Set[str]] = None):
        self.known_names = set(known_names or [])
        self._stopwords = set(_STOPWORDS)

    # ---------- 公共 ----------

    def mine(self, source_id: str, division_id: str,
             facts: List[TextualFact]) -> List[CandidateName]:
        out: List[CandidateName] = []
        seen_in_call = set()
        for f in facts:
            if f.division_id != division_id:
                continue
            text = f.verbatim_quote
            # A. 提示词模式
            for marker in ("為", "曰", "有", "坐落", "跨其上", "即"):
                start = 0
                while True:
                    i = text.find(marker, start)
                    if i < 0:
                        break
                    seg = text[i + len(marker): i + len(marker) + 12]
                    cand = self._make_candidate(seg, f, "提示词「%s」" % marker,
                                                has_cue=True)
                    if cand and cand.name not in seen_in_call:
                        seen_in_call.add(cand.name)
                        out.append(cand)
                    start = i + len(marker)
            # B. 通名后缀扫描（无线索词也能召回）
            for cand in self._suffix_scan(text, f):
                if cand.name not in seen_in_call:
                    seen_in_call.add(cand.name)
                    out.append(cand)
        return out

    # ---------- 内部 ----------

    def _clip(self, seg: str) -> Optional[str]:
        for j, ch in enumerate(seg):
            if ch in "，。、；：！？「」『』（）":
                seg = seg[:j]
                break
        return seg.strip() or None

    def _strip_direction(self, name: str) -> Tuple[str, Optional[str]]:
        for suf in DIRECTION_SUFFIXES:
            if name.endswith(suf) and len(name) > len(suf):
                return name[:-len(suf)], suf
        return name, None

    def _has_place_suffix(self, name: str) -> bool:
        return any(name.endswith(s) for s in PLACE_SUFFIXES)

    def _make_candidate(self, seg: str, fact: TextualFact,
                        note: str, has_cue: bool) -> Optional[CandidateName]:
        raw = self._clip(seg)
        if not raw:
            return None
        name, stripped = self._strip_direction(raw)
        if not (2 <= len(name) <= 6):
            return None
        if self._is_noise(name):
            return None
        suffix_ok = self._has_place_suffix(name) or (
            stripped and self._has_place_suffix(stripped))
        # 置信度分级：双证 high，单证 mid
        if has_cue and suffix_ok:
            conf = "high"
        elif has_cue or suffix_ok:
            conf = "mid"
        else:
            conf = "low"
        return CandidateName(
            name=name, from_source_id="", from_division_id=fact.division_id,
            evidence_fact_id=fact.id,
            note=note + ("；剥离方位「%s」" % stripped if stripped else ""),
            confidence=conf, stripped_suffix=stripped,
        )

    def _suffix_scan(self, text: str, fact: TextualFact) -> List[CandidateName]:
        """B. 通名后缀扫描：按标点切短语，短语尾部符合专名+通名即候选"""
        out = []
        for phrase in re.split(r"[，。、；：！？「」『』（）]", text):
            phrase = phrase.strip()
            if not (3 <= len(phrase) <= 12):
                continue
            # 取短语尾部 2-6 字窗口，找以通名结尾的子串
            for size in (2, 3, 4, 5, 6):
                if len(phrase) < size:
                    break
                tail = phrase[-size:]
                if not self._has_place_suffix(tail):
                    continue
                head = phrase[:-size]
                # 头部若是动词/虚词开头，才可能是「X+地名」结构
                if head and head[-1] in "於在自從从往到":
                    name, stripped = self._strip_direction(tail)
                    if self._is_noise(name):
                        break
                    conf = "mid" if len(name) >= 2 else "low"
                    out.append(CandidateName(
                        name=name, from_source_id="",
                        from_division_id=fact.division_id,
                        evidence_fact_id=fact.id,
                        note="后缀扫描「…%s%s」" % (head[-1], tail),
                        confidence=conf, stripped_suffix=stripped))
                    break
        return out

    def _is_noise(self, name: str) -> bool:
        if name in self._stopwords or self.known_names:
            if name in self._stopwords:
                return True
        if name in self.known_names:
            return True
        if any(ch.isdigit() for ch in name):
            return True
        # 纪年/帝号模式（繁简）
        for reign in ("康熙", "雍正", "乾隆", "嘉庆", "萬曆", "万历", "天啟", "天启",
                      "嘉靖", "成化", "至元", "至大", "泰定", "太平興國", "太平兴国"):
            if name.startswith(reign):
                return True
        # 官职/机构模式（繁简）
        for kw in ("護軍", "护军", "副將", "副将", "總兵", "总兵", "內務府", "内务府",
                   "御道", "倉署", "仓署", "碾房", "都督"):
            if kw in name:
                return True
        return False


# 向后兼容别名
QuoteCorpusMiner = ToponymMiner


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
