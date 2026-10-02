"""
tests/haidian_kg/test_era4_liao_jin.py
测试 Era 4（辽南京与金中都帝都期，938-1215）
验证大觉寺辽大安四年石碑硬物证、金中都立都、玉泉山芙蓉殿御泉与西山八大水院
"""
import pytest
from haidian_kg.ontology.schema import EvidenceLevel, EpistemicStatus
from haidian_kg.extractor import HaidianCorpusExtractor


def test_era4_liao_jin_institutions_and_stele_attestations():
    """验证辽南京宛平县分治、大觉寺辽碑硬证据、金中都建立与玉泉山芙蓉殿工程"""
    ds = HaidianCorpusExtractor.load_or_extract()

    # 1. 验证地物与都城实体
    feat_ids = {f.id for f in ds.physical_features}
    unit_ids = {u.id for u in ds.administrative_units}
    assert "feat_diaoyutai_lake" in feat_ids, "缺失海淀钓鱼台金代行宫蓄水地物"
    assert "unit_liao_nanjing" in unit_ids, "缺失辽南京析津府宛平县建置实体"
    assert "unit_jin_zhongdu" in unit_ids, "缺失金中都大兴府都城建置实体"
    assert "unit_shengshui_court" in unit_ids, "缺失金章宗西山圣水院（香山寺）建置实体"

    # 2. 验证核心书证
    atts = {a.id: a for a in ds.place_attestations}
    assert "attest_dajuesi_liao_stele" in atts, "缺失辽大安四年大觉寺清水院石碑书证"
    assert "attest_yuquanshan_jinshi" in atts, "缺失《金史》玉泉山芙蓉殿御泉书证"
    assert "attest_diaoyutai_dijing" in atts, "缺失钓鱼台金章宗垂钓积水成池书证"

    liao_stele = atts["attest_dajuesi_liao_stele"]
    assert liao_stele.evidence_level == EvidenceLevel.L1_ARCHAEOLOGICAL or liao_stele.evidence_level == EvidenceLevel.L2_PRIMARY_DOC
    assert liao_stele.epistemic_status == EpistemicStatus.VERIFIED
    assert "大辽大安四年" in liao_stele.quote


def test_era4_negative_control_dajuesi_origin_and_jin_endpoint():
    """负控制断言：大觉寺始建绝非金代（必须由辽碑证实为辽代）；金中都都城实体严格止于1215年"""
    ds = HaidianCorpusExtractor.load_or_extract()

    # 1. 检验大觉寺书证：最早确证书证年份必须为辽代（1088年前后），严禁被削矮至金代
    dajue_atts = [a for a in ds.place_attestations if a.toponym_id == "top_dajuesi"]
    stele_att = next((a for a in dajue_atts if "辽" in a.dynasty or a.recorded_year == 1088), None)
    assert stele_att is not None, "大觉寺必须包含辽代大安四年确证书证"

    # 2. 检验金中都都城实体：valid_end_year 必须严格为 1215 年（蒙古攻破降为燕京）
    jin_unit = next((u for u in ds.administrative_units if u.id == "unit_jin_zhongdu"), None)
    assert jin_unit is not None
    assert jin_unit.valid_end_year == 1215, f"金中都都城实体终点年份错误: {jin_unit.valid_end_year}（应为1215年）"
