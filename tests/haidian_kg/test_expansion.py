"""
tests/haidian_kg/test_expansion.py
地名⇄古书闭包扩展引擎测试

用户提出的方法：「初始地名 → 引用古书 → 古书里又有地名 → 循环」
北京全域词条不可能全手工建，必须靠这个循环自然生长。

三条铁律：
1. 引擎只负责发现，入库必须过 QA 闸门（用户定的纪律）
2. 已见集合防环——高梁河出现在十几部书里，没有去重会无限循环
3. 挖出的候选必须带来源引文 id（可溯源），否则无法审
"""
import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from haidian_kg.calibration import gaoliang as G, yuanmingyuan as Y, banners as B, settlements as S
from haidian_kg.calibration.people import PEOPLE
from haidian_kg.calibration.digital_resources import RESOURCES
from haidian_kg.production_exports import KnowledgeBase
from haidian_kg.expansion import ClosureExpander, QuoteCorpusMiner


def build(mod):
    return KnowledgeBase(
        sources=mod.SOURCES, divisions=mod.DIVISIONS, facts=mod.FACTS,
        entities=mod.ENTITIES, states=mod.STATES, identities=mod.IDENTITIES,
        appellations=mod.APPELLATIONS, references=mod.REFERENCES,
        transformations=getattr(mod, 'TRANSFORMATIONS', ()),
        propositions=mod.PROPOSITIONS, adoptions=mod.ADOPTIONS,
        aggregates=getattr(mod, 'AGGREGATES', ()),
        people=PEOPLE, resources=RESOURCES)


@pytest.fixture(scope="module")
def report():
    exp = ClosureExpander(seed_kbs=[build(G), build(Y), build(B), build(S)])
    return exp.expand()


class TestClosureEngine:
    def test_seeds_collected(self, report):
        assert len(report.seeds) >= 20, "种子词条收集不全"

    def test_sources_mined(self, report):
        assert len(report.sources_mined) == 20, "应挖遍全部篇卷"

    def test_finds_e1_e2_topics(self, report):
        """【核心】引擎必须自己发现 E1（萧家河）与 E2（安河桥）的主题"""
        names = {c.name for c in report.candidates_found}
        assert "蕭家河" in names, "萧家河（E1 主题）未被发现"
        assert "安河橋" in names, "安河桥（E2 主题）未被发现"

    def test_finds_e1_offshoot_shuiceng(self, report):
        """水礳（镶白旗营房坐落地）须被发现"""
        assert "水礳" in {c.name for c in report.candidates_found}

    def test_candidates_are_traceable(self, report):
        """每个候选必须带来源引文 id——不可溯源的发现无效"""
        fact_ids = set()
        for mod in (G, Y, B, S):
            fact_ids.update(f.id for f in mod.FACTS)
        for c in report.candidates_found:
            assert c.evidence_fact_id in fact_ids, \
                "候选 %s 的来源引文 %s 不存在" % (c.name, c.evidence_fact_id)

    def test_cycle_avoidance(self, report):
        """已见集合必须工作：同名候选/同书不重复入队"""
        assert report.cycles_avoided > 0

    def test_engine_does_not_admit(self, report):
        """【纪律】引擎只发现不收录，入库必须走闸门"""
        assert report.admitted == []


class TestMinerDiscipline:
    def test_stopwords_filtered(self):
        m = QuoteCorpusMiner()
        assert not m._plausible("雍正二年"), "纪年不得作为地名"
        assert not m._plausible("護軍校"), "官职不得作为地名"
        assert not m._plausible("圓明園"), "皇家园林已在库里，不是村落地名"

    def test_clip_respects_punctuation(self):
        m = QuoteCorpusMiner()
        assert m._clip("大有莊，莊前為御道") == "大有莊"
        assert m._clip("青龍橋。") == "青龍橋"
