"""
tests/haidian_kg/test_era3_sui_tang.py
测试 Era 3（隋唐五代幽州北境期，581-938）
验证隋临朔宫、唐幽州都督府、唐代羁縻带州焦君墓志铭硬证据与太舟坞争议假说
"""
import pytest
from haidian_kg.ontology.schema import EvidenceLevel, EpistemicStatus
from haidian_kg.extractor import HaidianCorpusExtractor


def test_era3_sui_tang_institutions_and_epitaph_attestations():
    """验证隋临朔宫、唐幽州都督府与唐天宝焦君墓志铭出土金石书证"""
    ds = HaidianCorpusExtractor.load_or_extract()

    # 1. 验证地物与建置
    feat_ids = {f.id for f in ds.physical_features}
    unit_ids = {u.id for u in ds.administrative_units}
    assert "feat_linshuogong_site" in feat_ids, "缺失隋临朔宫行宫遗迹地物"
    assert "unit_youzhou_commandery" in unit_ids, "缺失隋唐幽州都督府建置实体"
    assert "unit_daizhou_garrison" in unit_ids, "缺失唐代羁縻带州孤竹县建置实体"

    # 2. 验证书证
    atts = {a.id: a for a in ds.place_attestations}
    assert "attest_suishu_linshuogong" in atts, "缺失《隋书》幽州置临朔宫书证"
    assert "attest_tang_jiao_epitaph" in atts, "缺失唐天宝九载焦府君墓志铭金石硬证据"
    assert "attest_daizhou_tang_record" in atts, "缺失《旧唐书》带州寄治清水店书证"

    jiao_att = atts["attest_tang_jiao_epitaph"]
    assert jiao_att.evidence_level == EvidenceLevel.L1_ARCHAEOLOGICAL
    assert jiao_att.epistemic_status == EpistemicStatus.VERIFIED
    assert "焦" in jiao_att.quote or "带州" in jiao_att.quote


def test_era3_negative_control_taizhouwu_contested_not_verified():
    """负控制断言：太舟坞得名于带州绝不可标为确证信史，必须中立标为学术争议假说 CONTESTED"""
    ds = HaidianCorpusExtractor.load_or_extract()

    taizhou_hypos = [
        h for h in ds.competing_hypotheses
        if "带州" in h.hypothesis_title and "太舟坞" in h.hypothesis_title
    ]
    assert len(taizhou_hypos) >= 1, "必须包含太舟坞带州音转假说节点"
    hypo = taizhou_hypos[0]

    assert hypo.confidence_status != EpistemicStatus.VERIFIED, "太舟坞带州音转说绝不可标记为确证信史 (VERIFIED)"
    assert hypo.confidence_status == EpistemicStatus.CONTESTED, "太舟坞带州音转说必须保持学术争议状态 (CONTESTED)"
