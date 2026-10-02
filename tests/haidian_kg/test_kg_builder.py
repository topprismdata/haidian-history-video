"""
tests/haidian_kg/test_kg_builder.py
测试 RDF 知识图谱构建器 (builder.py) 与 Turtle 全量导出文件 (haidian_kg.ttl) 的三元组完整性与本体语义约束
"""
import pathlib
import pytest
import rdflib
from rdflib.namespace import RDF, RDFS, OWL

HHTO = rdflib.Namespace("http://history.haidian.gov.cn/ontology/")


def test_kg_builder_graph_triples():
    """验证构建生成的 RDF 图谱规模、类型实例化与核心拓扑边"""
    from haidian_kg.builder import HaidianKGBuilder

    builder = HaidianKGBuilder()
    g = builder.build_graph()

    # 1. 图谱规模断言
    total_triples = len(g)
    assert total_triples >= 450, f"三元组规模不足: {total_triples} < 450"

    # 2. 核心类实例数断言
    toponyms = list(g.subjects(RDF.type, HHTO.Toponym))
    attestations = list(g.subjects(RDF.type, HHTO.PlaceAttestation))
    events = list(g.subjects(RDF.type, HHTO.ToponymEvolutionEvent))
    features = list(g.subjects(RDF.type, HHTO.PhysicalFeature))
    units = list(g.subjects(RDF.type, HHTO.AdministrativeUnit))

    assert len(toponyms) >= 45, f"地名实体实例不足: {len(toponyms)}"
    assert len(attestations) >= 50, f"书证用例实例不足: {len(attestations)}"
    assert len(events) >= 20, f"演变事件实例不足: {len(events)}"
    assert len(features) >= 12, f"物理地物实例不足: {len(features)}"
    assert len(units) >= 25, f"建制实体实例不足: {len(units)}"

    # 3. 核心语义边断言
    attested_in_edges = list(g.triples((None, HHTO.attestedIn, None)))
    assert len(attested_in_edges) >= 45, f"见载书证边缺失: {len(attested_in_edges)}"

    # 4. 证据层级与认识论标签断言
    evidence_levels = set(g.objects(None, HHTO.evidenceLevel))
    assert any("Level 1" in str(lit) for lit in evidence_levels), "图谱缺失 Level 1 考古证据字面量"
    assert any("Level 6" in str(lit) for lit in evidence_levels), "图谱缺失 Level 6 证伪证据字面量"


def test_exported_turtle_file_validity():
    """验证 haidian_kg.ttl 导出文件存在且语法合法"""
    from haidian_kg.builder import HaidianKGBuilder

    builder = HaidianKGBuilder()
    ttl_path = pathlib.Path("haidian_kg/data/haidian_kg.ttl")
    builder.export_turtle(ttl_path)

    assert ttl_path.exists(), "全量图谱导出文件不存在"

    g_loaded = rdflib.Graph()
    g_loaded.parse(str(ttl_path), format="turtle")
    assert len(g_loaded) >= 450, "导出的 Turtle 文件三元组过少"
