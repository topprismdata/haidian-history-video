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
from haidian_kg.expansion import ClosureExpander, ToponymMiner


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
        """纪年/官职/皇家园林不得作为候选（繁简双字形）"""
        m = ToponymMiner()
        for noise in ("雍正二年", "護軍校", "圓明園", "乾隆十六年"):
            assert m._is_noise(noise), "%s 应被判为噪声" % noise

    def test_direction_suffix_stripped(self):
        """方位后缀剥离：樹村西邊 → 樹村"""
        
        miner = ToponymMiner()
        name, stripped = miner._strip_direction("樹村西邊")
        assert name == "樹村" and stripped == "西邊"
        name2, stripped2 = miner._strip_direction("藍靛廠西邊")
        assert name2 == "藍靛廠" and stripped2 == "西邊"
        # 无方位后缀则原样返回
        name3, stripped3 = miner._strip_direction("蕭家河")
        assert name3 == "蕭家河" and stripped3 is None

    def test_confidence_grading(self):
        """置信分级：提示词+通名双证=high，单证=mid"""
        from haidian_kg.ontology.epistemic import TextualFact
        miner = ToponymMiner()
        f = TextualFact(id="tf_x", division_id="div_x",
                        verbatim_quote="測試句：營房坐落蕭家河，廨舍若干楹。",
                        attested_string="蕭家河")
        cands = miner.mine("src_x", "div_x", [f])
        by_name = {c.name: c for c in cands}
        assert "蕭家河" in by_name
        assert by_name["蕭家河"].confidence == "high"  # 坐落(提示词)+河(通名)双证

    def test_suffix_scan_finds_cueless_names(self):
        """后缀扫描召回无线索词地名——提示词法的盲区"""
        from haidian_kg.ontology.epistemic import TextualFact
        miner = ToponymMiner()
        f = TextualFact(id="tf_y", division_id="div_y",
                        verbatim_quote="水流自永定河入西山。",
                        attested_string="永定河")
        cands = miner.mine("src_y", "div_y", [f])
        names = {c.name for c in cands}
        assert any("永定河" in n for n in names), "后缀扫描应召回永定河"
