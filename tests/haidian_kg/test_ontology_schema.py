"""
tests/haidian_kg/test_ontology_schema.py
测试本体定义文件 haidian_ontology.ttl 的 RDF/OWL 规范性以及 schema.py 的强类型校验能力
"""
import pathlib
import pytest
import rdflib
from rdflib.namespace import RDF, RDFS, OWL

HHTO = rdflib.Namespace("http://history.haidian.gov.cn/ontology/")


def test_ontology_turtle_syntax_and_classes():
    """验证 haidian_ontology.ttl 语法合法并包含核心四分法类"""
    ontology_path = pathlib.Path("haidian_kg/ontology/haidian_ontology.ttl")
    assert ontology_path.exists(), f"本体文件不存在: {ontology_path}"

    g = rdflib.Graph()
    g.parse(str(ontology_path), format="turtle")
    assert len(g) > 20, "本体三元组数量过少"

    # 验证核心四分法类
    classes = set(g.subjects(RDF.type, OWL.Class))
    expected_classes = [
        HHTO.Toponym,
        HHTO.PhysicalFeature,
        HHTO.AdministrativeUnit,
        HHTO.PlaceAttestation,
        HHTO.ToponymEvolutionEvent,
        HHTO.SourceDocument,
        HHTO.CompetingHypothesis,
    ]
    for cls in expected_classes:
        assert cls in classes, f"缺失核心类: {cls}"

    # 验证关键对象属性
    properties = set(g.subjects(RDF.type, OWL.ObjectProperty))
    expected_props = [
        HHTO.evolvedFrom,
        HHTO.attestedIn,
        HHTO.fromSource,
        HHTO.evolutionTriggeredBy,
        HHTO.competesWith,
        HHTO.locatedAtFeature,
    ]
    for prop in expected_props:
        assert prop in properties, f"缺失核心对象属性: {prop}"


def test_pydantic_schema_validation():
    """验证 Python Pydantic 实体模型校验逻辑与枚举约束"""
    from haidian_kg.ontology.schema import (
        ToponymEntity,
        PhysicalFeatureEntity,
        AdministrativeUnitEntity,
        PlaceAttestationEntity,
        ToponymEventEntity,
        EvidenceLevel,
        EpistemicStatus,
    )

    # 1. 物理地物
    feat = PhysicalFeatureEntity(
        id="feat_wanquanhe",
        label="万泉河古道及水网洼地",
        feature_type="WetlandRiver",
        coordinates=[116.30, 39.98],
    )
    assert feat.label == "万泉河古道及水网洼地"

    # 2. 地名实体
    top = ToponymEntity(
        id="top_haidian",
        standard_form="海淀",
        script_hanzi="海淀",
        phonetic_pinyin="hǎi diàn",
        name_type="official",
    )
    assert top.standard_form == "海淀"

    # 3. 书证凭证实体
    attest = PlaceAttestationEntity(
        id="attest_haidian_1260",
        toponym_id="top_haidian",
        attested_name="海店",
        source_title="中堂事记",
        source_author="王恽",
        recorded_year=1260,
        dynasty="元代（中统元年）",
        quote="六日丁卯，午憩海店，距京城廿里",
        evidence_level=EvidenceLevel.L2_PRIMARY_DOC,
        epistemic_status=EpistemicStatus.VERIFIED,
    )
    assert attest.recorded_year == 1260
    assert attest.evidence_level == EvidenceLevel.L2_PRIMARY_DOC

    # 4. 演变事件实体
    evt = ToponymEventEntity(
        id="evt_euphemism_liulangzhuang",
        event_type="EuphemisticRenamingEvent",
        source_toponym_id="top_niulanzhuang",
        target_toponym_id="top_liulangzhuang",
        description="牛栏庄因垂柳依依雅化为柳浪庄",
        dynasty="清初康熙年间",
    )
    assert evt.event_type == "EuphemisticRenamingEvent"
