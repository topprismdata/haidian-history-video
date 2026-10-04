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
    assert "attest_jingxi_map_1913" in atts, "缺失1913年《京西图》书证"
    assert "attest_zgc_1951_land" in atts, "缺失1951年中科院选址（中科院官方院史）书证"
    assert "attest_zgc_1980_seed" in atts, "缺失1980年陈春先硅谷第一粒种子书证"
    assert "attest_zgc_1988_zone" in atts, "缺失1988年国务院国函74号文批复书证"

    jx_att = atts["attest_jingxi_map_1913"]
    # 【R7 回灌 2026-10-04】旧断言 `assert "中关村" in quote` 超出了 E13 冻结论据：
    # 1913 年《京西图》（二万五千分之一）上**只零星出现「中关」**；「中关村」三字
    # 是 1953 年中科院信笺误植后定型。且五万分之一《实测京师四郊图》是 **1915**，
    # 与 1913《京西图》是**两张图**，原 KB 把二者捏成一张。
    assert jx_att.recorded_year == 1913, "《京西图》实测公元年份必须严格为1913年"
    assert "二万五千分之一" in jx_att.source_title, (
        "🔴 1913 年《京西图》是二万五千分之一；五万分之一《实测京师四郊图》是 1915 年，"
        "两张图不得混挂（E13/E21 冻结论据）")
    assert "中关" in jx_att.quote, "E13 冻结论据只到「中关」零星出现"
    # 负控制：1913 不得被写成已定名/已取代
    assert "取代" not in jx_att.quote, (
        "🔴 1950年代初官方档案仍作「中官村」，1913 不构成取代，不得如此表述")

    # 【R9①】1953 政务院批复公文查无此件，已判 DISPROVEN；真实口径是 1951 年选址
    assert atts["attest_zgc_1953_decision"].epistemic_status == EpistemicStatus.DISPROVEN, (
        "🔴 政务院文委1953批复公文核不出，须 DISPROVEN（保留原文供审计）")
    land = atts["attest_zgc_1951_land"]
    assert land.recorded_year == 1951, "E13 硬年份表：中科院1951年在西北郊征地"
    assert "1951" in land.quote

    # 【R8】机构全名不得漏「发展」二字
    seed = atts["attest_zgc_1980_seed"]
    assert "先进技术发展服务部" in seed.quote, (
        "🔴 机构全名是「北京等离子体学会先进技术发展服务部」，漏「发展」即错")
    assert "先进技术服务部" not in seed.quote.replace("先进技术发展服务部", ""), (
        "🔴 「先进技术服务部」是漏字形态，不得出现")

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
    assert "attest_jingxi_map_1913" in chen_hypo.disproven_by_attestation_ids, (
        "陈垣单一独创说必须挂接1913《京西图》作为反证证据（雅化早于1930年代）")

    # 【R7】改名事件层必须同步降级：不得把 1913 当定名年、不得写「学堂进驻」驱动说
    zg_evt = next((e for e in ds.evolution_events if e.id == "evt_zhongguan_euphemism"), None)
    assert zg_evt is not None
    assert zg_evt.occurred_year is None, (
        "🔴 改名是「地图雅化(清末民初)＋机构定名(1950年代)」两步走，不得锁 1913 为定名年")
    assert "因新式学堂进驻" not in zg_evt.description, (
        "🔴 「因新式学堂进驻」驱动说无任何书证，属自撰机制")
    assert "1953" in zg_evt.description, "定名锚点应落在1953年信笺误植（E13 冻结）"

    # 2. 检验成府村消亡事件
    chengfu_evt = next((e for e in ds.evolution_events if e.id == "evt_chengfu_extinction"), None)
    assert chengfu_evt is not None
    assert chengfu_evt.event_type == "SpatialExtinctionEvent", "成府演变事件类型必须为空间消亡地名存续 (SpatialExtinctionEvent)"
    assert chengfu_evt.target_toponym_id == "top_chengfulu"
