"""
tests/haidian_kg/test_era8_9_modern.py
测试 Era 8-9（民国北平与当代科学城期，1912-至今）
验证1913年京西图实测中关村、清华燕大高校园区、1953年中科院选址与1988年新技术试验区
"""
import pytest
from haidian_kg.ontology.schema import EvidenceLevel, EpistemicStatus
from haidian_kg.extractor import HaidianCorpusExtractor


def test_era8_9_modern_cartography_and_hightech_zone_attestations():
    """验证1913京西图实测中关村、1953政务院中科院选址批复与1988国务院国函74号文"""
    ds = HaidianCorpusExtractor.load_or_extract()

    # 1. 验证现代科教建置实体
    unit_ids = {u.id for u in ds.administrative_units}
    assert "unit_tsinghua_academy" in unit_ids, "缺失清华大学建置实体"
    assert "unit_cas_zhongguancun" in unit_ids, "缺失中科院中关村科学城园区建置实体"
    assert "unit_zgc_hightech_zone" in unit_ids, "缺失中关村高新区试验区实体"

    # 2. 验证书证完整性
    atts = {a.id: a for a in ds.place_attestations}
    assert "attest_jingxi_map_1913" in atts, "缺失1913年实测北京四郊图（京西图）书证"
    assert "attest_zgc_1953_decision" in atts, "缺失1953年政务院中科院选址中关村批复书证"
    assert "attest_zgc_1980_seed" in atts, "缺失1980年陈春先硅谷第一粒种子书证"
    assert "attest_zgc_1988_zone" in atts, "缺失1988年国务院国函74号文批复书证"

    jx_att = atts["attest_jingxi_map_1913"]
    assert jx_att.recorded_year == 1913, "京西图实测公元年份必须严格为1913年"
    assert "中关村" in jx_att.quote

    doc_att = atts["attest_zgc_1988_zone"]
    assert doc_att.recorded_year == 1988
    assert "试验区" in doc_att.quote or "中关村" in doc_att.quote


def test_era8_9_negative_control_zgc_chenyuan_and_chengfu_fossil():
    """负控制断言：1913年已官方实测印制中关村，陈垣1930年代独创说不成立；成府村消亡但地名存续"""
    ds = HaidianCorpusExtractor.load_or_extract()

    # 1. 检验陈垣改名假说状态必须为 CONTESTED
    chen_hypo = next((h for h in ds.competing_hypotheses if "陈垣" in h.hypothesis_title), None)
    assert chen_hypo is not None
    assert chen_hypo.confidence_status == EpistemicStatus.CONTESTED, "陈垣提议中关村改名说必须为 CONTESTED 学术争议"
    assert "attest_jingxi_map_1913" in chen_hypo.disproven_by_attestation_ids, "陈垣单一独创说必须挂接1913京西图作为反证证据"

    # 2. 检验成府村消亡事件
    chengfu_evt = next((e for e in ds.evolution_events if e.id == "evt_chengfu_extinction"), None)
    assert chengfu_evt is not None
    assert chengfu_evt.event_type == "SpatialExtinctionEvent", "成府演变事件类型必须为空间消亡地名存续 (SpatialExtinctionEvent)"
    assert chengfu_evt.target_toponym_id == "top_chengfulu"
