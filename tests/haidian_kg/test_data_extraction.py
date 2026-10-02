"""
tests/haidian_kg/test_data_extraction.py
测试海淀全域历史实体抽取器与结构化数据集 entities.json 的数据完整性与证据质量
"""
import json
import pathlib
import pytest
from haidian_kg.ontology.schema import (
    EvidenceLevel,
    EpistemicStatus,
    ToponymEntity,
    PlaceAttestationEntity,
    ToponymEventEntity,
    PhysicalFeatureEntity,
    AdministrativeUnitEntity,
)


def test_extracted_entities_json_structure():
    """验证 entities.json 存在且符合全量实体模型约束"""
    json_path = pathlib.Path("haidian_kg/data/entities.json")
    assert json_path.exists(), f"实体数据文件不存在: {json_path}"

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    required_keys = [
        "physical_features",
        "administrative_units",
        "toponyms",
        "place_attestations",
        "evolution_events",
        "competing_hypotheses",
    ]
    for key in required_keys:
        assert key in data, f"缺失顶级数据分组: {key}"

    # 实体规模断言
    assert len(data["physical_features"]) >= 12, "物理地物实体数量不足"
    assert len(data["administrative_units"]) >= 30, "建制实体数量不足"
    assert len(data["toponyms"]) >= 45, "地名实体数量不足"
    assert len(data["place_attestations"]) >= 50, "书证用例数量不足"
    assert len(data["evolution_events"]) >= 20, "演变事件数量不足"
    assert len(data["competing_hypotheses"]) >= 3, "争议假说数量不足"


def test_era_coverage_completeness():
    """验证六大历史地层（先秦-唐-辽金-元-明-清-近现代）全覆盖"""
    from haidian_kg.extractor import HaidianCorpusExtractor

    dataset = HaidianCorpusExtractor.load_or_extract()
    attestations = dataset.place_attestations

    eras_found = set()
    for att in attestations:
        text = att.dynasty
        for target in ["先秦", "唐", "辽", "金", "元", "明", "清", "民国", "现代", "当代"]:
            if target in text:
                eras_found.add(target)

    expected_eras = {"唐", "辽", "金", "元", "明", "清", "现代"}
    for exp in expected_eras:
        assert exp in eras_found, f"历史地层缺失: {exp}"


def test_evidence_levels_and_disproven_presence():
    """验证包含考古硬证据 (L1) 与已被证伪伪说 (L6/DISPROVEN)"""
    from haidian_kg.extractor import HaidianCorpusExtractor

    dataset = HaidianCorpusExtractor.load_or_extract()
    levels = {att.evidence_level for att in dataset.place_attestations}
    statuses = {att.epistemic_status for att in dataset.place_attestations}

    assert EvidenceLevel.L1_ARCHAEOLOGICAL in levels, "缺失 Level 1 考古硬证据书证"
    assert EvidenceLevel.L2_PRIMARY_DOC in levels, "缺失 Level 2 一手官刻金石书证"
    assert EvidenceLevel.L3_GAZETTEER in levels, "缺失 Level 3 正史方志纪实书证"
    assert EvidenceLevel.L5_FOLK_LEGEND in levels, "缺失 Level 5 民间传说书证"
    assert EvidenceLevel.L6_DISPROVEN in levels, "缺失 Level 6 证伪伪说书证"
    assert EpistemicStatus.DISPROVEN in statuses, "缺失 DISPROVEN 认识论状态"
