"""
tests/haidian_kg/test_query_engine.py
测试 SPARQL 与 NetworkX 历史地名推理与查询引擎 (query.py)
验证演变谱系追踪、断代检索、书证溯源与假说争议研判
"""
import pytest


def test_evolution_lineage_tracing():
    """验证沿革拓扑追踪能力：六郎庄、海淀、大有庄、中关村"""
    from haidian_kg.query import KGQueryEngine

    engine = KGQueryEngine()

    # 1. 六郎庄：牛栏庄 -> 柳浪庄 -> 六郎庄
    chain_liulang = engine.trace_evolution("六郎庄")
    labels_liulang = [hop["label"] for hop in chain_liulang]
    assert "牛栏庄" in labels_liulang, "六郎庄演变链缺失前身牛栏庄"
    assert "柳浪庄" in labels_liulang, "六郎庄演变链缺失中间态柳浪庄"
    assert labels_liulang[-1] == "六郎庄", "六郎庄终点实体不符"

    # 2. 海淀：海店 -> 海甸 -> 海淀
    chain_haidian = engine.trace_evolution("海淀")
    labels_haidian = [hop["label"] for hop in chain_haidian]
    assert "海店" in labels_haidian, "海淀演变链缺失元代海店"
    assert "海甸" in labels_haidian, "海淀演变链缺失明代海甸"

    # 3. 大有庄：穷八家 -> 大有庄
    chain_dayou = engine.trace_evolution("大有庄")
    labels_dayou = [hop["label"] for hop in chain_dayou]
    assert "穷八家" in labels_dayou, "大有庄演变链缺失穷八家"

    # 4. 中关村：中官村 -> 中关村
    chain_zgc = engine.trace_evolution("中关村")
    labels_zgc = [hop["label"] for hop in chain_zgc]
    assert "中官村" in labels_zgc, "中关村演变链缺失中官村"


def test_period_query_and_attestations():
    """验证按朝代检索书证与按地名提取证据链"""
    from haidian_kg.query import KGQueryEngine

    engine = KGQueryEngine()

    # 1. 按朝代检出元代书证
    yuan_attestations = engine.query_by_period("元")
    assert len(yuan_attestations) >= 3, "元代书证检出不足"
    yuan_names = {a["attested_name"] for a in yuan_attestations}
    assert any("海店" in n for n in yuan_names), "元代书证应包含海店"

    # 2. 检出安河桥的证据链，必须包含 Level 1 考古证据
    anhe_atts = engine.get_attestations("安河桥")
    assert len(anhe_atts) >= 1, "安河桥书证为空"
    levels = {a["evidence_level"] for a in anhe_atts}
    assert any("Level 1" in lvl for lvl in levels), "安河桥必须包含 Level 1 考古硬证据"


def test_contested_and_disproven_queries():
    """验证争议假说研判与已被证伪伪说检索"""
    from haidian_kg.query import KGQueryEngine

    engine = KGQueryEngine()

    # 1. 争议假说检出
    contested = engine.find_contested_hypotheses()
    assert len(contested) >= 2, "争议假说检出不足"
    titles = [c["title"] for c in contested]
    assert any("太舟坞" in t for t in titles), "争议假说应包含太舟坞"

    # 2. 证伪伪说检出（负控制）
    disproven = engine.find_disproven_myths()
    assert len(disproven) >= 2, "证伪伪说检出不足"
    myths = [d["title"] for d in disproven]
    assert any("西三旗" in m for m in myths), "证伪伪说应包含西三旗八旗说"
    assert any("高梁桥" in m for m in myths), "证伪伪说应包含高梁桥979年说"
