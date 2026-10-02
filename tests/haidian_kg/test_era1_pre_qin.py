"""
tests/haidian_kg/test_era1_pre_qin.py
测试 Era 1（先秦封国与战国燕都期，前1046-前221）
验证琉璃河西周燕都青铜铭文硬证据、蓟城建置与高梁水先秦古道
"""
import pytest
from haidian_kg.ontology.schema import EvidenceLevel, EpistemicStatus
from haidian_kg.extractor import HaidianCorpusExtractor


def test_era1_pre_qin_enfeoffment_and_bronze_attestations():
    """验证周武王封燕封蓟、房山琉璃河克罍铭文硬证据与蓟城建置"""
    ds = HaidianCorpusExtractor.load_or_extract()

    # 1. 验证地物与都城实体
    feat_ids = {f.id for f in ds.physical_features}
    unit_ids = {u.id for u in ds.administrative_units}
    assert "feat_liulihe_site" in feat_ids, "缺失房山琉璃河西周燕都遗址地物"
    assert "unit_jicheng_capital" in unit_ids, "缺失先秦蓟国故城/燕都蓟城建置实体"

    # 2. 验证核心书证
    atts = {a.id: a for a in ds.place_attestations}
    assert "attest_shiji_zhou_wuwang" in atts, "缺失《史记·周本纪》封燕封蓟书证"
    assert "attest_ke_lei_bronze" in atts, "缺失房山琉璃河克罍‘命克侯于燕’青铜铭文硬证据"

    bronze_att = atts["attest_ke_lei_bronze"]
    assert bronze_att.evidence_level == EvidenceLevel.L1_ARCHAEOLOGICAL
    assert bronze_att.epistemic_status == EpistemicStatus.VERIFIED
    assert "克侯于燕" in bronze_att.quote


def test_era1_negative_control_gaoliangqiao_not_pre_qin():
    """负控制断言：高梁桥人工桥梁建筑绝不可出现在先秦断代（只能是古河道高梁水）"""
    ds = HaidianCorpusExtractor.load_or_extract()

    # 查询所有高梁桥的书证，验证其记录年份绝不可早于元代（1271年前后）
    gaoliangqiao_atts = [
        a for a in ds.place_attestations
        if a.toponym_id in ["top_gaoliangqiao", "top_gaoliangzha"]
    ]
    for att in gaoliangqiao_atts:
        if att.epistemic_status == EpistemicStatus.VERIFIED:
            assert att.recorded_year is not None
            assert att.recorded_year >= 1200, f"高梁桥确证书证年份异常提前至先秦/中古: {att.recorded_year}"
