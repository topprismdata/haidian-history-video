"""
tests/haidian_kg/test_era7_qing.py
测试 Era 7（清代京师顺天府期，1644-1912）
验证三山五园帝国治理体系、圆明园八旗护军营、外火器营蓝靛厂与乾隆御题赐名流变
"""
import pytest
from haidian_kg.ontology.schema import EvidenceLevel, EpistemicStatus
from haidian_kg.extractor import HaidianCorpusExtractor


def test_era7_qing_imperial_gardens_and_banner_camps():
    """验证三山五园建置、八旗驻防营房（肖家河/树村/蓝靛厂）与日下旧闻考书证"""
    ds = HaidianCorpusExtractor.load_or_extract()

    # 1. 验证园林与旗营建置实体
    unit_ids = {u.id for u in ds.administrative_units}
    assert "unit_yuanmingyuan" in unit_ids, "缺失圆明园建置实体"
    assert "unit_changchunyuan" in unit_ids, "缺失畅春园建置实体"
    assert "unit_zhenghuangqi_camp" in unit_ids, "缺失肖家河正黄旗营房实体"
    assert "unit_xianghuangqi_camp" in unit_ids, "缺失树村镶黄旗营房实体"
    assert "unit_landianchang_town" in unit_ids, "缺失蓝靛厂外火器营实体"
    assert "unit_jianruiying_garrison" in unit_ids, "缺失香山健锐营八旗碉楼实体"

    # 2. 验证书证完整性
    atts = {a.id: a for a in ds.place_attestations}
    assert "attest_rixia_dayouzhuang" in atts, "缺失《日下旧闻考》大有庄赐名书证"
    assert "attest_rixia_landianchang" in atts, "缺失《日下旧闻考》外火器营迁驻蓝靛厂书证"
    assert "attest_xiaojiahe_daqing" in atts, "缺失《大清会典》肖家河正黄旗营房书证"
    assert "attest_suzhoujie_qianlong_poem" in atts, "缺失乾隆御制诗万寿山买卖街书证"

    dayou_att = atts["attest_rixia_dayouzhuang"]
    assert "穷八家" in dayou_att.quote
    assert "大有庄" in dayou_att.quote


def test_era7_negative_control_dayouzhuang_and_suzhoujie():
    """负控制断言：大有庄赐名必须有乾隆帝实名触发；苏州街必须确认为皇家内湖买卖街"""
    ds = HaidianCorpusExtractor.load_or_extract()

    # 1. 检验大有庄演变事件必须具备触发者为乾隆帝
    dayou_evt = next((e for e in ds.evolution_events if e.target_toponym_id == "top_dayouzhuang"), None)
    assert dayou_evt is not None
    assert dayou_evt.triggering_person == "清高宗乾隆帝", "大有庄赐名演变事件必须注明触发者为乾隆帝"

    # 2. 检验苏州街建制实体类别
    suzhou_unit = next((u for u in ds.administrative_units if u.id == "unit_suzhoujie_market"), None)
    assert suzhou_unit is not None
    assert suzhou_unit.unit_type == "ImperialGarden", "苏州街必须为皇家宫禁内湖集市，严禁定为民间集镇"
