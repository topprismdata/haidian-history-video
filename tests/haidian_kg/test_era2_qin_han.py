"""
tests/haidian_kg/test_era2_qin_han.py
测试 Era 2（秦汉魏晋十六国北朝期，前221-581）
验证清河汉墓群考古硬证据、曹魏车箱渠水利引水与北魏郦道元《水经注》高梁水源流
"""
import pytest
from haidian_kg.ontology.schema import EvidenceLevel, EpistemicStatus
from haidian_kg.extractor import HaidianCorpusExtractor


def test_era2_qin_han_archaeology_and_watercourse_attestations():
    """验证清河汉墓群考古硬证据、水经注高梁水与三国志车箱渠书证"""
    ds = HaidianCorpusExtractor.load_or_extract()

    # 1. 验证地物与水利设施
    feat_ids = {f.id for f in ds.physical_features}
    unit_ids = {u.id for u in ds.administrative_units}
    assert "feat_qinghe_han_tombs" in feat_ids, "缺失海淀清河汉墓群考古遗址地物"
    assert "feat_chexiangqu_canal" in feat_ids, "缺失曹魏车箱渠水利古道地物"
    assert "unit_guangyang_commandery" in unit_ids, "缺失秦汉广阳郡/广阳国蓟县建置"

    # 2. 验证书证完整性
    atts = {a.id: a for a in ds.place_attestations}
    assert "attest_qinghe_han_tombs_dig" in atts, "缺失清河汉墓群考古发掘报告书证"
    assert "attest_sanguozhi_liujing" in atts, "缺失《三国志·刘靖传》车箱渠书证"
    assert "attest_gaolianghe_shuijingzhu" in atts, "缺失《水经注》高梁水书证"

    # 3. 验证证据层级
    qinghe_att = atts["attest_qinghe_han_tombs_dig"]
    assert qinghe_att.evidence_level == EvidenceLevel.L1_ARCHAEOLOGICAL
    assert qinghe_att.epistemic_status == EpistemicStatus.VERIFIED

    # 🔴 2026-10-04 订正：旧断言 `"出蓟县西北平地" in quote` 是在**保护伪引文**——
    # 《水经注》卷十三实文作「水出**薊城**西北平地」（城，非县），且旧稿缀的
    # 「水色清莹，草木丰茂」在《水经注》全卷检索零命中、属自撰。详见 corpus/era2 §1.4。
    sjz_att = atts["attest_gaolianghe_shuijingzhu"]
    assert "水出薊城西北平地" in sjz_att.quote
    assert "泉流東注" in sjz_att.quote, "「泉流东注」是平原泉群判断的直接书证"
    for dead in ("水色清莹", "草木丰茂", "出蓟县"):
        assert dead not in sjz_att.quote, "《水经注》伪引文片段复活: %s" % dead


def test_era2_negative_control_canal_spatial_integrity():
    """负控制断言：车箱渠渠身流经海淀南部，但堰首戾陵堰必须明确位于石景山"""
    ds = HaidianCorpusExtractor.load_or_extract()

    # 检索车箱渠地物描述
    chexiang_feat = next((f for f in ds.physical_features if f.id == "feat_chexiangqu_canal"), None)
    assert chexiang_feat is not None
    assert "海淀南部" in chexiang_feat.description or "八里庄" in chexiang_feat.description
    assert "石景山" in chexiang_feat.description, "必须准确说明堰首位于石景山永定河出山口"
