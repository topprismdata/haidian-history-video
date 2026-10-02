"""
tests/haidian_kg/test_expansion.py
地名⇄古书闭包扩展引擎测试（v3：身份三层 / SourceVisitKey / 双字形负控制）

用户提出的方法：「初始地名 → 引用古书 → 古书里又有地名 → 循环」
北京全域词条不可能全手工建，必须靠这个循环自然生长。

铁律（spec §2.5）：
1. 引擎只负责发现，入库必须过人工闸门（admitted 恒 []）
2. SourceVisitKey 先查后加——重访/已知名/重复候选三类事件分账
3. 挖出的 occurrence 必须带 source_id + evidence_fact_id（可溯源）
4. 词表繁简双字形——用负控制证明判据非恒真（M6）
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
from haidian_kg.ontology.epistemic import TextualFact
from haidian_kg.expansion import (
    ClosureExpander, ToponymMiner, SourceMiner,
    ToponymOccurrence, CandidatePlaceHypothesis,
    MINER_VERSION, RULE_PROFILE_VERSION,
    normalize_form, _STOPWORDS,
    LEADING_STOP_PREFIXES, strip_leading_stop_prefix,
)


def build_with_facts(mod, extra_facts=()):
    return KnowledgeBase(
        sources=mod.SOURCES,
        divisions=mod.DIVISIONS,
        facts=list(mod.FACTS) + list(extra_facts),
        entities=mod.ENTITIES, states=mod.STATES, identities=mod.IDENTITIES,
        appellations=mod.APPELLATIONS, references=mod.REFERENCES,
        transformations=getattr(mod, 'TRANSFORMATIONS', ()),
        propositions=mod.PROPOSITIONS, adoptions=mod.ADOPTIONS,
        aggregates=getattr(mod, 'AGGREGATES', ()),
        people=PEOPLE, resources=RESOURCES)


def build(mod):
    return build_with_facts(mod)


#: 篇卷 → 所属典籍（溯源断言用）
DIVISION_SOURCE = {}
for _m in (G, Y, B, S):
    for _d in _m.DIVISIONS:
        DIVISION_SOURCE[_d.id] = _d.source_id
ALL_FACT_IDS = {f.id for _m in (G, Y, B, S) for f in _m.FACTS}


@pytest.fixture(scope="module")
def report():
    exp = ClosureExpander(seed_kbs=[build(G), build(Y), build(B), build(S)])
    return exp.expand()


class TestClosureEngine:
    def test_seeds_collected(self, report):
        assert len(report.seeds) >= 20, "种子词条收集不全"

    def test_sources_mined(self, report):
        # 篇卷全集：原 20 卷 + 健锐营词条追加的 5 卷（banners 2026-10-02）
        assert len(report.sources_mined) == 25, "应挖遍全部篇卷"

    def test_finds_e1_e2_topics(self, report):
        """【核心】引擎必须自己发现 E1（萧家河）与 E2（安河桥）的主题。
        种子只有「萧家河北」，base 形不同——候选以归一形（简体）聚类"""
        forms = {h.normalized_form for h in report.candidates_found}
        assert "萧家河" in forms, "萧家河（E1 主题）未被发现"
        assert "安河桥" in forms, "安河桥（E2 主题）未被发现"

    def test_finds_e1_offshoot_shuiceng(self, report):
        """水礳（镶白旗营房坐落地，生僻通名）须由提示词法保住"""
        assert "水礳" in {h.normalized_form for h in report.candidates_found}

    def test_candidates_are_traceable(self, report):
        """每个 occurrence 必须带真实引文 id + 正确 source_id——不可溯源的发现无效"""
        for h in report.candidates_found:
            for o in h.occurrences:
                assert o.evidence_fact_id in ALL_FACT_IDS, \
                    "候选 %s 的来源引文 %s 不存在" % (h.normalized_form, o.evidence_fact_id)
                assert o.source_id, "候选 %s 的 occurrence source_id 为空（M1 未修）" % h.normalized_form
                assert o.source_id == DIVISION_SOURCE[o.division_id], \
                    "候选 %s 的 source_id %s 与篇卷 %s 归属不符" % (
                        h.normalized_form, o.source_id, o.division_id)

    def test_occurrence_ids_unique(self, report):
        ids = [o.occurrence_id for h in report.candidates_found
               for o in h.occurrences]
        assert len(ids) == len(set(ids)), "occurrence_id 必须唯一"

    def test_engine_does_not_admit(self, report):
        """【纪律】引擎只发现不收录，入库必须走人工闸门"""
        assert report.admitted == []

    def test_counters_split_and_rendered(self, report):
        """环避让混计已拆三类事件，render 分行显示（M2/M5）"""
        assert report.known_form_hits > 0, "已建词条字形命中必须被计数"
        assert report.revisited_visits == 0  # 四模块篇卷互不相同，单轮无重访
        assert report.duplicate_candidates == 0
        lines = report.render().splitlines()
        assert any("重访篇卷" in l for l in lines)
        assert any("命中已建词条字形" in l for l in lines)
        assert any("重复候选观察" in l for l in lines)


class TestIdentityThreeLayers:
    def test_hypothesis_clusters_cross_volume(self, report):
        """【P0-1】一名多书互证保留为 occurrence 列表（修 M2 证据塌缩）。
        萧家河：div_bqtz116（坐落蕭家河，提示词 high）+ div_rxjwkc72
        （蕭家河北有…，后缀 mid）→ 一个假说、多条书证、置信取最高"""
        hyps = [h for h in report.candidates_found
                if h.normalized_form == "萧家河"]
        assert len(hyps) == 1, "同名候选必须聚成一个假说"
        hyp = hyps[0]
        assert len(hyp.occurrences) >= 2, "萧家河两条独立书证不得塌缩成一条"
        divs = {o.division_id for o in hyp.occurrences}
        assert len(divs) >= 2, "互证书证应来自不同篇卷"
        ranks = [{"low": 0, "mid": 1, "high": 2}[o.confidence]
                 for o in hyp.occurrences]
        assert {"low": 0, "mid": 1, "high": 2}[hyp.confidence] == max(ranks), \
            "假说置信应取成员最高"

    def test_hypothesis_invariants(self, report):
        """每个假说：有 occurrence、置信合法、surface 归一后等于 normalized_form"""
        for h in report.candidates_found:
            assert isinstance(h, CandidatePlaceHypothesis)
            assert h.occurrences, "假说 %s 没有任何 occurrence" % h.normalized_form
            assert h.confidence in ("high", "mid", "low")
            for o in h.occurrences:
                assert isinstance(o, ToponymOccurrence)
                assert o.extractor_version == MINER_VERSION
                assert normalize_form(o.surface_form) == o.normalized_form


class TestVisitKeySemantics:
    def test_revisit_same_kb_object(self):
        """【P0-3】同一 KB 对象入队两次：VisitKey 先查后加→重访计数、不重复挖"""
        kb = build(B)
        rep = ClosureExpander(seed_kbs=[kb, kb]).expand()
        assert rep.revisited_visits == len(B.DIVISIONS), \
            "同 KB 二次入队必须逐篇卷计重访"
        assert len(rep.sources_mined) == len(B.DIVISIONS), "重访篇卷不得重复挖"

    def test_cross_kb_same_division_both_mined(self):
        """【M5】两个 KB 共引同卷：kb_id 进 VisitKey，各自 facts 各挖各的，
        第二个 KB 的独有书证不得被当成「环」丢掉"""
        from pydantic import ValidationError  # noqa: F401  仅确保环境一致
        extra = TextualFact(id="tf_extra_beiwu", division_id="div_bqtz116_yingjian",
                            verbatim_quote="别有北坞村民居。",
                            attested_string="北坞村")
        kb1 = build(B)
        kb2 = build_with_facts(B, [extra])
        rep = ClosureExpander(seed_kbs=[kb1, kb2]).expand()
        assert len(rep.sources_mined) == 2 * len(B.DIVISIONS), \
            "共引同卷的两个 KB 必须各挖一次"
        forms = {h.normalized_form for h in rep.candidates_found}
        assert "北坞村" in forms, "第二个 KB 的独有书证被静默跳过（M5 回归）"
        assert rep.duplicate_candidates > 0, \
            "两 KB 的同证 occurrence 应计为重复候选观察"
        # 同名候选仍聚成一个假说
        hyps = [h for h in rep.candidates_found if h.normalized_form == "北坞村"]
        assert len(hyps) == 1


class TestMinerDiscipline:
    def test_stopwords_filtered(self):
        """纪年/官职/旗制/机构复合词不得作为候选——繁简双字形（实锤 C1 简体侧）

        v4 迁移：纯地名字形（圆明园/清漪园/万寿山/稻田厂…）移出噪声表
        （它们是地点，「已知名不冒充新发现」改由 expander known 集合路由）；
        本用例改钉「迁移后仍是噪声」的旗制/纪年/职官词，并负控制迁移词
        确实已放行（防单向漂移）。"""
        m = ToponymMiner()
        for noise in ("雍正二年", "護軍校", "乾隆十六年",
                      # C1 修复的简体侧七词 + 八处（地名属性者已迁出）
                      "护军校", "八处",
                      # 旗制/机构复合词（非地点，v4 仍拦）
                      "圆明园八旗", "圆明园副将", "正黄旗"):
            assert m._is_noise(noise), "%s 应被判为噪声" % noise
        # v4 负控制：迁出的纯地名不再是噪声（通道可达性的前提）
        for place in ("圆明园", "清漪园", "畅春园", "静宜园",
                      "静明园", "万寿山", "稻田厂"):
            assert not m._is_noise(place), "%s 是地点，v4 起不得判为噪声" % place

    def test_stopwords_dual_script_symmetry(self):
        """【M6 负控制】_STOPWORDS 每个繁体词的简体对应也必须在表
        （仿 qa_gate.py G6 双字形覆盖检查器：词表不对称=简体语料漏拦）"""
        missing = []
        for w in sorted(_STOPWORDS):
            simp = normalize_form(w)
            if simp != w and simp not in _STOPWORDS:
                missing.append("%s→%s" % (w, simp))
        assert not missing, "停用词表缺简体侧字形: %s" % missing

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
        miner = ToponymMiner()
        f = TextualFact(id="tf_x", division_id="div_x",
                        verbatim_quote="測試句：營房坐落蕭家河，廨舍若干楹。",
                        attested_string="蕭家河")
        cands = miner.mine("src_x", "div_x", [f])
        occs = [o for o in cands if o.surface_form == "蕭家河"]
        assert len(occs) == 1, "同证同形只发一次（cue 与后缀命中去重）"
        assert occs[0].confidence == "high"  # 坐落(提示词)+河(通名)双证
        assert occs[0].source_id == "src_x", "M1: source_id 必须写入 occurrence"
        assert occs[0].extractor_method == "cue:坐落"

    def test_suffix_scan_exact_name(self):
        """【M6 负控制·M3】后缀扫描必须回溯出干净专名头：
        「水流自永定河入西山」→ 精确产出 永定河，绝不产出「永定河入西山」"""
        miner = ToponymMiner()
        f = TextualFact(id="tf_y", division_id="div_y",
                        verbatim_quote="水流自永定河入西山。",
                        attested_string="永定河")
        cands = miner.mine("src_y", "div_y", [f])
        surfaces = {o.surface_form for o in cands}
        hits = [o for o in cands if o.normalized_form == "永定河"]
        assert hits, "后缀扫描应召回永定河"
        hit = hits[0]
        assert hit.surface_form == "永定河", "surface 必须精确等于 永定河"
        assert hit.normalized_form == "永定河", "归一形必须精确等于 永定河"
        assert hit.extractor_method == "suffix_scan"
        assert "永定河入西山" not in surfaces, "尾窗污染「永定河入西山」仍在"

    def test_no_tail_window_pollution(self):
        """【M6 负控制·M3】「內務府於青龍橋設稻田廠」绝不产出「龍橋設稻田廠」

        v4 语义迁移：稻田廠 是真实地点（皇家稻田厂），已移出噪声表——
        本用例改为断言它被**干净取出**（污染名仍绝不出现）。"""
        miner = ToponymMiner()
        f = TextualFact(id="tf_z", division_id="div_z",
                        verbatim_quote="內務府於青龍橋設稻田廠，有倉署、倉廒、碾房，经理官種稻田。",
                        attested_string="青龍橋")
        cands = miner.mine("src_z", "div_z", [f])
        surfaces = {o.surface_form for o in cands}
        for polluted in ("龍橋設稻田廠", "橋設稻田廠", "青龍橋設稻田廠"):
            assert polluted not in surfaces, "尾窗污染 %s 仍在" % polluted
        assert "青龍橋" in surfaces, "青龍橋（於 锚点回溯）应被干净取出"
        assert "稻田廠" in surfaces, "稻田廠 是地点，v4 起应被干净召回"
        assert "倉署" not in surfaces and "倉廒" not in surfaces, \
            "泛称 倉署/倉廒 不得作为候选"

    def test_occurrence_provenance_filled(self):
        """【M1】mine() 收到的 source_id 必须写进每个 occurrence"""
        miner = ToponymMiner()
        f = TextualFact(id="tf_p", division_id="div_p",
                        verbatim_quote="營房坐落安河橋。",
                        attested_string="安河橋")
        cands = miner.mine("src_prov", "div_p", [f])
        assert cands, "安河橋应被发现"
        for o in cands:
            assert o.source_id == "src_prov" and o.source_id != ""


class TestC2KnownFormsRealCorpus:
    """【M6 负控制·C2】真实四模块语料：已建词条的繁体字形不得冒充新发现"""

    @pytest.fixture(scope="class")
    def rep(self):
        exp = ClosureExpander(seed_kbs=[build(G), build(Y), build(B), build(S)])
        return exp.expand()

    def test_known_traditional_forms_not_candidates(self, rep):
        """樹村/青龍橋/大有莊（含碾莊）是已知词条的繁体字形，不得回归为候选"""
        forms = {h.normalized_form for h in rep.candidates_found}
        surfaces = {o.surface_form for h in rep.candidates_found
                    for o in h.occurrences}
        for known in ("树村", "青龙桥", "大有庄", "碾庄"):
            assert known not in forms, "%s 已建词条，繁体字形回归为候选（C2 未修）" % known
        for trad in ("樹村", "青龍橋", "大有莊", "碾莊"):
            assert trad not in surfaces, "繁体字形 %s 仍出现在候选 occurrence 里" % trad

    def test_new_places_still_discovered(self, rep):
        """正控制：种子 base 形不同的新地点仍必须被发现；
        假说 name 精确等于归一形（废除恒真子串断言）"""
        forms = {h.normalized_form for h in rep.candidates_found}
        for expected in ("萧家河", "安河桥", "蓝靛厂", "保福寺",
                         "水礳", "达官村", "戾陵堰", "通惠河", "永定河"):
            assert expected in forms, "新地点 %s 未被发现（召回回退）" % expected
        ydh = next(h for h in rep.candidates_found
                   if h.normalized_form == "永定河")
        assert ydh.name == "永定河"

    def test_script_variants_extend_known_forms(self):
        """【C2 机制】Appellation.script_variants 必须并入已知字形表"""
        kb = build(B)
        exp = ClosureExpander(seed_kbs=[kb])
        base_forms = {h.normalized_form for h in exp.expand().candidates_found}
        assert "萧家河" in base_forms, "对照组：萧家河应被发现"
        kb.appellations["app_xiaojiahebei"].script_variants = ["萧家河"]
        rep2 = ClosureExpander(seed_kbs=[kb]).expand()
        assert "萧家河" not in {h.normalized_form for h in rep2.candidates_found}, \
            "script_variants 未并入 known_forms（C2 机制缺失）"
        assert rep2.known_form_hits > 0


class TestIdempotency:
    def test_double_expand_stable(self):
        """【M6 负控制】同一 expander 二次 expand 同一 KB：候选集与计数稳定"""
        exp = ClosureExpander(seed_kbs=[build(G), build(Y), build(B), build(S)])
        r1 = exp.expand()
        r2 = exp.expand()
        assert r1.seeds == r2.seeds
        assert r1.sources_mined == r2.sources_mined
        assert r1.admitted == r2.admitted == []
        for counter in ("revisited_visits", "known_form_hits", "duplicate_candidates"):
            assert getattr(r1, counter) == getattr(r2, counter), \
                "计数器 %s 二次运行不稳定" % counter
        assert len(r1.candidates_found) == len(r2.candidates_found)
        for h1, h2 in zip(r1.candidates_found, r2.candidates_found):
            assert h1.normalized_form == h2.normalized_form
            assert h1.confidence == h2.confidence
            sig1 = [(o.occurrence_id, o.surface_form, o.evidence_fact_id,
                     o.extractor_method) for o in h1.occurrences]
            sig2 = [(o.occurrence_id, o.surface_form, o.evidence_fact_id,
                     o.extractor_method) for o in h2.occurrences]
            assert sig1 == sig2, "假说 %s 的 occurrence 列表不稳定" % h1.normalized_form


class TestMinerContract:
    """【M4】spec 契约名 SourceMiner；自定义实现可注入；QuoteCorpusMiner 已删"""

    def test_protocol_and_alias_removed(self):
        import haidian_kg.expansion as ex
        assert hasattr(ex, "SourceMiner")
        assert not hasattr(ex, "QuoteCorpusMiner"), "QuoteCorpusMiner 别名应已删除"

    def test_custom_miner_injected_and_duplicates_accounted(self):
        """假说聚类去重：同名同证重复观察计 duplicate_candidates、不重复入列"""
        f = TextualFact(id="tf_dup", division_id="div_ymy_sj",
                        verbatim_quote="营房坐落萧家河。",
                        attested_string="萧家河")
        occ = ToponymMiner().mine("src_ymy_sijifang", "div_ymy_sj", [f])[0]

        class FakeMiner(object):
            """实现 SourceMiner 协议的测试替身（按 division_id 过滤）"""
            def __init__(self, occs):
                self.occs = occs

            def mine(self, source_id, division_id, facts):
                return [o for o in self.occs if o.division_id == division_id]

        kb = build(Y)  # 圆明园模块：无 萧家河 种子，不干扰
        rep = ClosureExpander(seed_kbs=[kb],
                              miner=FakeMiner([occ, occ])).expand()
        assert rep.duplicate_candidates == 1
        hyps = [h for h in rep.candidates_found if h.normalized_form == "萧家河"]
        assert len(hyps) == 1 and len(hyps[0].occurrences) == 1

    def test_version_constants(self):
        """v5：后缀 墓/街/房 + 边界垃圾前缀表（holdout run3 裁决落地）；
        版本进 SourceVisitKey，bump 即视为全部篇卷没挖过"""
        assert MINER_VERSION == "v5"
        assert RULE_PROFILE_VERSION == "rp-v5"


class TestV4KnownMentionChannel:
    """【v4】KnownMention 通道：已知名命中降级记录为 mention 事件，
    不进 CandidatePlaceHypothesis；纪律（admitted 恒 []、不重复膨胀候选）
    原样保留，变的是 mention 层可见性（holdout run1 裁决落地）。"""

    def test_known_label_hit_becomes_known_mention(self):
        """已建词条 label 在引文中命中 → KnownMention 事件 + 不进候选"""
        from haidian_kg.expansion import KnownMention
        kb = build(B)   # banners：树村/五圣庵 等是词条 label
        rep = ClosureExpander(seed_kbs=[kb]).expand()
        km_surfaces = [k.normalized_form for k in rep.known_mentions]
        assert km_surfaces, "已知名命中必须产出 KnownMention（v4 前是静默丢弃）"
        assert rep.known_form_hits == len(rep.known_mentions), \
            "计数器与事件明细必须同账"
        cand_forms = {h.normalized_form for h in rep.candidates_found}
        assert not (set(km_surfaces) & cand_forms), \
            "KnownMention 不得同时出现在候选聚类（不重复膨胀候选）"
        assert rep.admitted == [], "引擎只发现不收录（纪律不变）"
        for k in rep.known_mentions:
            assert isinstance(k, KnownMention)
            assert k.confidence == "known"
            assert k.evidence_fact_id in ALL_FACT_IDS, "KnownMention 必须可溯源"
            assert k.extractor_version == MINER_VERSION

    def test_unknown_places_still_candidates_same_run(self):
        """负控制：known 通道不吞新地名——同一次运行里未知地点照常进候选"""
        kb = build(B)
        rep = ClosureExpander(seed_kbs=[kb]).expand()
        cand_forms = {h.normalized_form for h in rep.candidates_found}
        assert "萧家河" in cand_forms, "未知地点必须仍是候选（known 通道不得过收）"
        km_forms = {k.normalized_form for k in rep.known_mentions}
        assert "萧家河" not in km_forms

    def test_place_names_leave_stopword_table_with_dual_script(self):
        """v4 迁移负控制（对偶 test_stopwords_filtered）：
        迁出词的繁简双侧都不得残留在 _STOPWORDS（双字形对称铁律）"""
        from haidian_kg.expansion import normalize_form, _STOPWORDS
        for place in ("圆明园", "清漪园", "畅春园", "静宜园",
                      "静明园", "万寿山", "昆明湖", "玉泉山", "稻田厂"):
            assert place not in _STOPWORDS
            assert normalize_form(place) not in _STOPWORDS
        # 但旗制复合词仍必须留表（不是地点）
        for keep in ("圆明园八旗", "圆明园副将"):
            assert keep in _STOPWORDS

    def test_markdown_and_boundary_chars_clean_extraction(self):
        """【rp-v4 P0 负控制】Markdown 记号与 今/名/记 边界字：
        命中面必须逐字干净，绝不产出带记号/边界字的 surface"""
        miner = ToponymMiner()
        f = TextualFact(
            id="tf_v4_md", division_id="div_v4_md",
            verbatim_quote="迁驻**蓝靛厂**；《碧云寺》重修；今大觉寺；名娘娘府；"
                           "卷九十八记外火器营自内城迁来。",
            attested_string="蓝靛厂")
        cands = miner.mine("src_v4", "div_v4_md", [f])
        surfaces = {o.surface_form for o in cands}
        for expect in ("蓝靛厂", "碧云寺", "大觉寺", "娘娘府", "外火器营"):
            assert expect in surfaces, "rp-v4 应干净召回 %s，实得 %s" % (
                expect, sorted(surfaces))
        junk = [s for s in surfaces
                if any(ch in s for ch in "*《》-#今名记")
                or s.startswith(("今", "名", "记"))]
        assert not junk, "记号/边界字渗入 surface: %s" % junk

    def test_yuanmingyuan_flows_but_compounds_suppressed(self):
        """圆明园（地点）v4 起可达；圆明园八旗/圆明园护军营（旗制机构）仍拦——
        防负控制：迁移不得变成泛溢"""
        miner = ToponymMiner()
        f = TextualFact(
            id="tf_v4_ymp", division_id="div_v4_ymp",
            verbatim_quote="圆明园护军营《圆明园八旗》驻防圈占圆明园周边田地。",
            attested_string="圆明园")
        surfaces = {o.surface_form for o in miner.mine("s", "div_v4_ymp", [f])}
        assert "圆明园" in surfaces, "纯地名 圆明园 必须可达（v4 迁移）"
        for compound in ("圆明园护军营", "圆明园八旗"):
            assert compound not in surfaces, "旗制机构 %s 仍须拦" % compound

    def test_source_visit_key_bumped_by_version(self):
        """MINER_VERSION/RULE_PROFILE 进 VisitKey：v4 升级即视为没挖过，
        旧版本不会因版本变更被误判重访"""
        kb = build(S)
        rep = ClosureExpander(seed_kbs=[kb]).expand()
        assert rep.revisited_visits == 0
        assert len(rep.sources_mined) == len(S.DIVISIONS)


# ---------------------------------------------------------------------------
# v5（holdout run3 裁决落地）：通名后缀 墓/街/房 + 边界垃圾前缀表
# ---------------------------------------------------------------------------

class TestV5SuffixChannels:
    """【v5】通名后缀 墓/街/房（含复合 营房/營房）。

    正控制：run3 R 侧 8 条 FN 面（董四墓×3 / 苏州街×2 / 三旗营房×3）
    在合成书证上必须命中；负控制：每条通道构造会过触发的文本，
    证明通道不是恒真（detector-needs-negative-control 纪律）。
    墓/街/房 繁简同形（无独立繁体字形），复合 营房/營房 双写。"""

    @staticmethod
    def _faces(quote):
        miner = ToponymMiner()
        f = TextualFact(id="tf_v5", division_id="div_v5",
                        verbatim_quote=quote, attested_string="")
        return [o.surface_form for o in miner.mine("src_v5", "div_v5", [f])]

    # ---------- 正控制：run3 FN 面 ----------

    def test_mu_suffix_recalls_dongsimu_three_contexts(self):
        """墓 通道：董四墓×3 种书证语境（篇目头/赐名句/水院地望）"""
        for quote in ("董四墓：明代皇室茔地，守茔董姓第四子于此。",
                      "明亡后看茔户聚居，名董四墓，曾以贡桃闻名。",
                      "泉水院在董四墓附近。"):
            faces = self._faces(quote)
            assert "董四墓" in faces, "「%s」应命中 董四墓，实得 %s" % (quote, faces)

    def test_jie_suffix_recalls_suzhoujie_simp_and_trad(self):
        """街 通道：苏州街×2（简体俗称语境 + 繁体官书引文，归一形收敛）"""
        faces = self._faces("俗称苏州街。")
        assert "苏州街" in faces, "简体侧应命中 苏州街，实得 %s" % faces
        trad = self._faces("居人稱為蘇州街。")
        assert "蘇州街" in trad, "繁体官书引文应命中 蘇州街，实得 %s" % trad
        miner = ToponymMiner()
        f = TextualFact(id="tf_v5_szj", division_id="div_v5",
                        verbatim_quote="居人稱為蘇州街。", attested_string="")
        occ = [o for o in miner.mine("src_v5", "div_v5", [f])
               if o.surface_form == "蘇州街"][0]
        assert occ.normalized_form == "苏州街", "蘇→苏 必须入归一映射（聚类同形）"

    def test_yingfang_compound_recalls_three_banner_camps(self):
        """营房 复合通道：旗名穿越回溯，三旗营房整词出面（run3 各 1 条 FN）"""
        assert "正黄旗营房" in self._faces("正黄旗营房驻肖家河村北。")
        assert "镶黄旗营房" in self._faces("镶黄旗营房驻树村西。")
        assert "鑲黄旗營房" in self._faces("鑲黄旗營房在树村西。")
        assert "正白旗营房" in self._faces("正白旗营房坐落树村东。")

    def test_banner_camp_end_to_end_candidate_and_mention(self):
        """引擎级：无该词条的 KB 里三旗营房书证产出候选；
        已建词条 KB（banners）里则走 KnownMention，不冒充新发现"""
        extra = TextualFact(id="tf_v5_yf", division_id="div_ymy_sj",
                            verbatim_quote="正黄旗营房驻肖家河村北。",
                            attested_string="正黄旗营房")
        rep = ClosureExpander(
            seed_kbs=[build_with_facts(Y, [extra])]).expand()
        assert "正黄旗营房" in {h.normalized_form
                               for h in rep.candidates_found}, \
            "营房复合通道在引擎层断裂（候选未产出）"
        rep_b = ClosureExpander(seed_kbs=[build(B)]).expand()
        assert "正黄旗营房" in {k.normalized_form for k in rep_b.known_mentions}, \
            "已建词条字形命中必须走 KnownMention 通道"

    # ---------- 负控制：通道不得恒真 ----------

    def test_mu_channel_negative_control(self):
        """墓 通道负控制：「居民依墓而居」不得因 墓 命中成地名；
        run3 垃圾面「居民依墓成村」「居民依墓」不得再出面。
        已知残留（记录在案）：「墓成村」——依 收进边界字后村通道的
        clause 尾窗，形合「专名+通名」无廉价判据可拒，留人工审。"""
        faces = self._faces("守茔户与居民依墓成村，名娘娘府。")
        for junk in ("居民依墓成村", "居民依墓"):
            assert junk not in faces, "垃圾面「%s」仍在: %s" % (junk, faces)
        leftover = self._faces("居民依墓而居。")
        assert leftover == [], "纯动宾结构不得因 墓 后缀出面: %s" % leftover

    def test_fang_channel_negative_control(self):
        """房 通道负控制：正房/厢房 类通用建筑词、整词 营房 不得成地名；
        复合名「正黄旗营房」不受停用词影响（整词成员判定非子串）"""
        for quote in ("正房三间，厢房两座。", "营房四千余间。"):
            faces = self._faces(quote)
            for junk in ("正房", "厢房", "营房", "營房"):
                assert junk not in faces, "「%s」在「%s」不得出面: %s" % (
                    junk, quote, faces)
        miner = ToponymMiner()
        for generic in ("正房", "厢房", "廂房", "营房", "營房", "步行街"):
            assert miner._is_noise(generic), "%s 应判为噪声" % generic
        assert not miner._is_noise("正黄旗营房"), "复合地名不得被整词噪声误伤"

    def test_jie_channel_negative_control(self):
        """街 通道负控制：步行街 不得因 街 命中成地名"""
        faces = self._faces("此段为步行街。")
        assert "步行街" not in faces, "步行街 不得出面: %s" % faces

    def test_flag_boundary_guard_unchanged(self):
        """rp-v3 旗边界不回归：单字 营/旗 通名仍不许穿越旗名
        （「鑲黄旗營」不得裂出 X旗營/旗營/黄旗营）"""
        faces = self._faces("鑲黄旗營驻树村。")
        for junk in ("鑲黄旗營", "黄旗營", "旗營"):
            assert junk not in faces, "旗名穿越守卫失效: %s" % junk


class TestV5LeadingStopPrefixes:
    """【v5】边界垃圾前缀表：run3 P 侧垃圾面逐类正/负控制。
    语义：面头命中前缀 → 剥离后重验证「专名+通名」，剥后不合格整面拒绝；
    剥后合法 → 以干净面出面（不断言实体存在，实体由词条层负责）。"""

    @staticmethod
    def _faces(quote):
        miner = ToponymMiner()
        f = TextualFact(id="tf_v5p", division_id="div_v5p",
                        verbatim_quote=quote, attested_string="")
        return [o.surface_form for o in miner.mine("src_v5p", "div_v5p", [f])]

    def test_table_covers_run3_categories(self):
        """表必须覆盖 run3 归因的四类成分（结构助词/动介/俗语引导/通用名词）"""
        for required in ("的", "将", "按", "建", "依", "刹",
                         "俗呼", "讹写作", "俗称",
                         "居民", "皇家", "十处", "后世", "枪炮",
                         "香山公园", "海淀公园", "海淀"):
            assert required in LEADING_STOP_PREFIXES, \
                "前缀表缺 run3 成分「%s」" % required

    def test_structural_particle_de(self):
        """结构助词 的：「的金代行宫园」拒绝（的 已入回溯边界字，面不再成形）"""
        faces = self._faces("著名的金代行宫园。")
        assert "的金代行宫园" not in faces
        assert "金代行宫园" in faces, "剥后合法面应出面: %s" % faces

    def test_verb_prefixes_jiang_an_jian_yi(self):
        """动词/介词 将/按/建/依：四类 run3 垃圾面全部拒绝"""
        faces = self._faces("将万寿山后湖。")
        assert "将万寿山后湖" not in faces and "万寿山后湖" in faces
        faces = self._faces("按八旗翼长驻香山静宜园下。")
        assert "按八旗" not in faces, "按八旗 不得出面: %s" % faces
        assert "八旗" not in faces
        faces = self._faces("建满蒙八旗营房四千余间。")
        for junk in ("建满蒙八旗", "满蒙八旗", "满蒙八旗营房", "建满蒙八旗营房"):
            assert junk not in faces, "「%s」不得出面: %s" % (junk, faces)
        assert self._faces("居民依墓而居。") == []

    def test_colloquial_guides(self):
        """俗语引导 俗呼/俗称/讹写作：垃圾面拒绝，剥后真名出面"""
        faces = self._faces("俗呼一溜边山。")
        assert "俗呼一溜边山" not in faces and "一溜边山" in faces
        faces = self._faces("讹写作六郎庄。")
        assert "讹写作六郎庄" not in faces and "六郎庄" in faces, \
            "剥后 六郎庄 应出面（run3 FP→可命中）: %s" % faces

    def test_generic_noun_leads(self):
        """通用名词开头 居民/皇家/十处/后世/枪炮：垃圾面拒绝"""
        faces = self._faces("皇家宫廷内湖。")
        assert "皇家宫廷内湖" not in faces and "宫廷内湖" in faces
        faces = self._faces("十处天然泉。")
        assert "十处天然泉" not in faces and "天然泉" in faces
        faces = self._faces("设枪炮演武场。")
        assert "枪炮演武场" not in faces and "枪炮" not in faces

    def test_compound_park_prefix_longest_first(self):
        """「香山公园香山」复合：剥 香山公园 → 香山（剥后合法即出面，
        不断言实体存在）；最长优先——「海淀公园香山」不得剥成「公园香山」"""
        faces = self._faces("圣水院在香山公园香山一带。")
        assert "香山公园香山" not in faces, "run3 垃圾面必须拒绝"
        faces = self._faces("海淀公园香山。")
        assert faces == ["香山"], "最长前缀优先失败: %s" % faces
        assert "公园香山" not in faces

    def test_haidian_prefix_strips_compound_keeps_bare(self):
        """海淀 前缀：「海淀温泉」「海淀区三里河」「海淀凤凰岭」剥出真名面；
        裸「海淀」「海淀镇」余量不足不剥（真名不误伤）"""
        faces = self._faces("香水院在今海淀温泉镇。")
        assert "海淀温泉" not in faces and "温泉" in faces, faces
        faces = self._faces("金代行宫园在海淀区三里河。")
        assert "海淀区三里河" not in faces and "三里河" in faces, faces
        faces = self._faces("海淀凤凰岭。")
        assert "海淀凤凰岭" not in faces and "凤凰岭" in faces, faces
        faces = self._faces("英法联军进犯，十月五日占海淀镇、圆明园。")
        assert "海淀镇" in faces, "余量 <2 不剥，「海淀镇」真名不得误伤: %s" % faces

    def test_strip_rejects_when_remainder_invalid(self):
        """剥后不合格 → 整面拒绝：剥出头是回溯边界字（依墓）、余量不足"""
        cleaned, peeled = strip_leading_stop_prefix("居民依墓")
        assert cleaned is None and peeled == ["居民"], \
            "剥出头 依 是边界字，必须整面拒绝"
        cleaned, peeled = strip_leading_stop_prefix("海淀温泉")
        assert cleaned == "温泉" and peeled == ["海淀"]
        cleaned, peeled = strip_leading_stop_prefix("海淀")
        assert cleaned == "海淀" and peeled == [], "余量 <2 不剥"

    def test_peel_recorded_in_note(self):
        """剥离必须留痕：occurrence.note 记剥前缀链（可溯源纪律）"""
        miner = ToponymMiner()
        f = TextualFact(id="tf_v5n", division_id="div_v5n",
                        verbatim_quote="讹写作六郎庄。", attested_string="")
        occ = [o for o in miner.mine("src_v5n", "div_v5n", [f])
               if o.surface_form == "六郎庄"][0]
        assert "讹写作" in occ.note, "剥前缀必须写进 note: %s" % occ.note
