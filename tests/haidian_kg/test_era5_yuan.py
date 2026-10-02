"""
tests/haidian_kg/test_era5_yuan.py
测试 Era 5（大蒙古国燕京与元大都期，1215-1368）
验证王恽1260年中堂事记首载海店、郭守敬通惠水利工程龙背村残堤、高昌畏吾村与大都建置
"""
import pytest
from haidian_kg.ontology.schema import EvidenceLevel, EpistemicStatus
from haidian_kg.extractor import HaidianCorpusExtractor


def test_era5_yuan_waterworks_and_first_attestation_of_haidian():
    """验证王恽1260首载海店、龙背村白浮堰残堤硬物证、高梁闸与廉希宪畏吾村"""
    ds = HaidianCorpusExtractor.load_or_extract()

    # 1. 验证地物与聚落实体
    feat_ids = {f.id for f in ds.physical_features}
    unit_ids = {u.id for u in ds.administrative_units}
    assert "feat_longbeicun_weir" in feat_ids, "缺失全国唯一存世郭守敬白浮引水工程龙背村残堤地物"
    assert "unit_haidian_town" in unit_ids, "缺失元代海店聚落建置实体"
    assert "unit_weiwu_village" in unit_ids, "缺失元代畏吾村聚落实体"

    # 2. 验证书证完整性
    atts = {a.id: a for a in ds.place_attestations}
    assert "attest_haidian_1260" in atts, "缺失王恽1260年中堂事记首载海店书证"
    assert "attest_gaoliangzha_1292" in atts, "缺失《元史·郭守敬传》至元二十九年创高梁闸书证"
    assert "attest_weiwucun_yuanshi" in atts, "缺失《元史·廉希宪传》畏吾村书证"

    haidian_att = atts["attest_haidian_1260"]
    assert haidian_att.recorded_year == 1260, "王恽海店书证书录公元年必须为1260年（中统元年）"
    assert "午憩海店" in haidian_att.quote


def test_era5_negative_control_temporal_enclosure_and_ethnicity():
    """负控制断言：王恽1260海店书证必须被Era 5（1215-1368）完全闭环包含；畏吾村必须确认为畏兀儿族源"""
    ds = HaidianCorpusExtractor.load_or_extract()

    # 1. 检验王恽1260年是否在 Era 5 范围（1215-1368）之内
    haidian_att = next((a for a in ds.place_attestations if a.id == "attest_haidian_1260"), None)
    assert haidian_att is not None
    assert 1215 <= haidian_att.recorded_year <= 1368, "海店首见公元年份（1260）必须严格落在 Era 5（1215-1368）时间区间内"

    # 2. 检验畏吾村族源描述
    weiwu_unit = next((u for u in ds.administrative_units if u.id == "unit_weiwu_village"), None)
    assert weiwu_unit is not None
    assert "畏兀儿" in weiwu_unit.description or "廉希宪" in weiwu_unit.description, "畏吾村必须具备畏兀儿/廉希宪族源标注，严禁汉族魏姓附会"
