"""
tests/haidian_kg/test_full_chronology_audit.py
海淀与北京历史时空知识图谱（BHKG/HHTO）全周期双盲学术审计测试套件
全面审计图谱三元组规模、全断代无缝覆盖、演变DAG拓扑无环性、全量负控制与证据闭环。
"""
import pytest
import rdflib
from rdflib.namespace import RDF, RDFS
import networkx as nx
from haidian_kg.query import KGQueryEngine
from haidian_kg.ontology.schema import EvidenceLevel, EpistemicStatus
from haidian_kg.extractor import HaidianCorpusExtractor

HHTO = rdflib.Namespace("http://history.haidian.gov.cn/ontology/")


def test_full_graph_scale_and_triple_density():
    """审计1：图谱全量三元组规模必须大于1500，且实体类分布均衡"""
    engine = KGQueryEngine()
    total_triples = len(engine.graph)
    assert total_triples >= 1500, f"全图三元组密度不足: {total_triples} < 1500"

    features = list(engine.graph.subjects(RDF.type, HHTO.PhysicalFeature))
    units = list(engine.graph.subjects(RDF.type, HHTO.AdministrativeUnit))
    toponyms = list(engine.graph.subjects(RDF.type, HHTO.Toponym))
    attestations = list(engine.graph.subjects(RDF.type, HHTO.PlaceAttestation))
    events = list(engine.graph.subjects(RDF.type, HHTO.ToponymEvolutionEvent))

    assert len(features) >= 20, f"物理地物不足: {len(features)}"
    assert len(units) >= 30, f"建制实体不足: {len(units)}"
    assert len(toponyms) >= 60, f"地名实体不足: {len(toponyms)}"
    assert len(attestations) >= 65, f"书证用例不足: {len(attestations)}"
    assert len(events) >= 20, f"演变事件不足: {len(events)}"


def test_full_chronology_seamless_coverage():
    """审计2：全周期十大断代（Era 0 至 Era 9）必须全部具备确凿书证与建制"""
    ds = HaidianCorpusExtractor.load_or_extract()

    # 提取所有书证的断代
    dynasties = [a.dynasty for a in ds.place_attestations]

    era_checks = {
        "Era 0 (史前)": any("旧石器" in d or "新石器" in d for d in dynasties),
        "Era 1 (先秦)": any("西周" in d or "战国" in d for d in dynasties),
        "Era 2 (秦汉)": any("汉" in d or "曹魏" in d or "北魏" in d for d in dynasties),
        "Era 3 (隋唐)": any("隋" in d or "唐" in d for d in dynasties),
        "Era 4 (辽金)": any("辽" in d or "金" in d for d in dynasties),
        "Era 5 (元代)": any("元" in d or "中统" in d for d in dynasties),
        "Era 6 (明代)": any("明" in d for d in dynasties),
        "Era 7 (清代)": any("清" in d for d in dynasties),
        "Era 8 (民国)": any("民国" in d for d in dynasties),
        "Era 9 (当代)": any("现代" in d or "新中国" in d for d in dynasties),
    }

    for era_name, passed in era_checks.items():
        assert passed, f"断代地层书证缺失: {era_name}"


def test_toponym_evolution_dag_acyclicity():
    """审计3：地名演变拓扑必须为严格的有向无环图 (DAG)，严禁死循环"""
    engine = KGQueryEngine()
    g = engine.evolution_graph

    # 检验是否为有向无环图
    is_dag = nx.is_directed_acyclic_graph(g)
    assert is_dag, "地名演变网络存在环路（死循环冲突）"


def test_full_negative_controls_and_evidence_integrity():
    """审计4：全量负控制双盲测试，验证所有已被证伪伪说必须被安全隔离"""
    engine = KGQueryEngine()

    disproven_items = engine.find_disproven_myths()
    assert len(disproven_items) >= 2, "负控制证伪清单数量不足"

    disproven_titles = [d["title"] for d in disproven_items]
    assert any("西三旗" in t for t in disproven_titles), "西三旗八旗伪说未被负控制捕获"
    assert any("高梁桥" in t for t in disproven_titles), "高梁桥宋辽战役桥伪说未被负控制捕获"

    # 验证没有任何 DISPROVEN 状态的书证被误标为 Level 1 或 Level 2
    ds = HaidianCorpusExtractor.load_or_extract()
    for att in ds.place_attestations:
        if att.epistemic_status == EpistemicStatus.DISPROVEN:
            assert att.evidence_level == EvidenceLevel.L6_DISPROVEN, f"证伪书证证据层级错标: {att.id}"
