"""
tests/haidian_kg/test_era0_prehistoric.py
测试 Era 0（史前与古人类文明期）考古硬证据、海淀本土遗光寺石器文化与负控制阻断
"""
import pytest
from haidian_kg.ontology.schema import EvidenceLevel, EpistemicStatus
from haidian_kg.extractor import HaidianCorpusExtractor


def test_era0_prehistoric_sites_and_c14_attestations():
    """验证包含周口店、山顶洞、王府井、东胡林、上宅及海淀遗光寺硬证据"""
    ds = HaidianCorpusExtractor.load_or_extract()

    # 1. 验证地物遗址
    feat_ids = {f.id for f in ds.physical_features}
    assert "feat_zhoukoudian" in feat_ids, "缺失周口店龙骨山古人类遗址"
    assert "feat_yiguangsi_site" in feat_ids, "缺失海淀四季青遗光寺新石器遗址"
    assert "feat_donghulin_site" in feat_ids, "缺失门头沟东胡林人遗址"

    # 2. 验证书证均为 Level 1 考古硬证据
    atts = {a.id: a for a in ds.place_attestations}
    assert "attest_zhoukoudian_peking_man" in atts, "缺失北京直立人考古书证"
    assert "attest_shandingdong_needle" in atts, "缺失山顶洞人骨针硬证据"
    assert "attest_yiguangsi_axe" in atts, "缺失海淀遗光寺出土磨制石斧证据"

    # 🔴 2026-10-04 订正：旧断言要求遗光寺条目为 `L1_ARCHAEOLOGICAL + VERIFIED` ——
    # **把一条查无著录的采集点记录保护成「海淀最早考古硬证据」**。外部检索无任何
    # 「遗光寺出土新石器石器」著录，所挂《北京海淀区出土文物志》书名未获核实，
    # 且「现藏两馆」无出处。详见 QUARANTINE.md Q-008。
    axe_att = atts["attest_yiguangsi_axe"]
    assert axe_att.epistemic_status == EpistemicStatus.UNSUBSTANTIATED, (
        "遗光寺采集点查无著录，须为 UNSUBSTANTIATED")
    assert axe_att.evidence_level != EvidenceLevel.L1_ARCHAEOLOGICAL, (
        "查无著录的条目不得标 L1 考古硬证据")


def test_era0_negative_control_mythology_blocked():
    """负控制断言：黄帝阪泉之战绝不可作为信史 VERIFIED，必须标为传说或争议"""
    ds = HaidianCorpusExtractor.load_or_extract()

    # 检索关于阪泉之战或黄帝的假说与书证
    yellow_emperor_hypos = [
        h for h in ds.competing_hypotheses
        if "阪泉" in h.hypothesis_title or "黄帝" in h.hypothesis_title
    ]
    assert len(yellow_emperor_hypos) >= 1, "必须包含阪泉之战神话假说判定节点"

    for hypo in yellow_emperor_hypos:
        assert hypo.confidence_status != EpistemicStatus.VERIFIED, "阪泉之战黄帝神话绝不可标记为确证信史 (VERIFIED)"
        assert hypo.confidence_status in [EpistemicStatus.FOLK_LEGEND, EpistemicStatus.CONTESTED]
