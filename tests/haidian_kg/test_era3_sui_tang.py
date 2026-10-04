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
    assert "attest_suishu_linshuogong" in atts, "缺失《隋书》大业七年临朔宫书证"
    assert "attest_tang_jiao_epitaph" in atts, "缺失带州孤竹府焦府君墓志条目（实体保留供审计）"
    assert "attest_daizhou_tang_record" in atts, "缺失《旧唐书》带州寄治清水店书证"

    # 🔴 2026-10-04 订正：本断言原为 `jiao_att.evidence_level == L1_ARCHAEOLOGICAL` +
    #    `VERIFIED` —— **把一具查无此志的拼装墓志保护成「出土金石硬证据」**。
    #    该墓志外部无任何著录/图版/释文，且以「君讳某」代讳名、句式与两唐书地理志逐字同构，
    #    属按志书结论反推的拼装体。详见 QUARANTINE.md Q-007。
    jiao_att = atts["attest_tang_jiao_epitaph"]
    assert jiao_att.epistemic_status == EpistemicStatus.UNSUBSTANTIATED, (
        "焦府君墓志查无著录，须为 UNSUBSTANTIATED，不得作为 L1 硬证据")
    assert jiao_att.evidence_level != EvidenceLevel.L1_ARCHAEOLOGICAL, (
        "查无此志的条目不得标 L1 考古硬证据")

    # 带州建制改由《旧唐书》实文支撑：置州在贞观十九年，神龙初是「放还」不是「置」
    daizhou = atts["attest_daizhou_tang_record"]
    assert daizhou.recorded_year == 645, "带州置州年应为贞观十九年(645)，非神龙元年(705)"
    for frag in ("贞观十九年", "州陷契丹后", "寄治于昌平县之清水店"):
        assert frag in daizhou.quote, "《旧唐书》带州条实文缺: %s" % frag
    for dead in ("神龙元年置", "领孤竹一县"):
        assert dead not in daizhou.quote, "带州伪引文片段复活: %s" % dead

    # 临朔宫：实文是「至涿郡之臨朔宮」，旧稿「幽州置临朔宫」为伪
    linshuo = atts["attest_suishu_linshuogong"]
    for frag in ("至涿郡之臨朔宮",):
        assert frag in linshuo.quote, "《隋书》实文缺: %s" % frag
    for dead in ("乙未", "驿赴", "幽州置临朔宫", "征天下兵"):
        assert dead not in linshuo.quote, "临朔宫伪引文片段复活: %s" % dead


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
