"""
tests/haidian_kg/test_era6_ming.py
测试 Era 6（明代京师顺天府期，1368-1644）
验证沈榜《宛署杂记》农耕水网、明代卫所西三旗小旗军屯、金山一溜边山七十二府妃茔与中官村太监义地
"""
import pytest
from haidian_kg.ontology.schema import EvidenceLevel, EpistemicStatus
from haidian_kg.extractor import HaidianCorpusExtractor


def test_era6_ming_weisuo_and_wanshu_zaji_attestations():
    """验证沈榜宛署杂记牛栏庄书证、明代西三旗小旗军屯与中官村太监义茔实体"""
    ds = HaidianCorpusExtractor.load_or_extract()

    # 1. 验证建置实体
    unit_ids = {u.id for u in ds.administrative_units}
    assert "unit_xisanqi_garrison" in unit_ids, "缺失明代西三旗小旗军屯建置实体"
    assert "unit_niangniangfu_tomb" in unit_ids, "缺失明代金山一溜边山七十二府妃茔实体"
    assert "unit_zhongguan_cemetery" in unit_ids, "缺失明代中官村太监义茔建置实体"
    assert "unit_wanshousi_palace" in unit_ids, "缺失明代万寿寺长河行宫实体"

    # 2. 验证书证完整性
    atts = {a.id: a for a in ds.place_attestations}
    assert "attest_wanping_niulanzhuang" in atts, "缺失沈榜《宛署杂记》万历二十一年牛栏庄书证"
    assert "attest_shuntian_xisanqi" in atts, "缺失顺天府志明代卫所小旗分屯书证"
    assert "attest_wanshousi_mingshi" in atts, "缺失《明史·神宗本纪》万寿寺敕建书证"

    niulan_att = atts["attest_wanping_niulanzhuang"]
    assert niulan_att.evidence_level == EvidenceLevel.L3_GAZETTEER
    assert "宛平县志" in niulan_att.source_title or "宛署杂记" in niulan_att.source_title or "宛平" in niulan_att.source_title
    assert "牛栏庄" in niulan_att.quote


def test_era6_negative_control_xisanqi_and_concubines():
    """负控制断言：西三旗绝非清代八旗军制；娘娘府必须确认为明代皇帝妃嫔茔墓（非清代公主）"""
    ds = HaidianCorpusExtractor.load_or_extract()

    # 1. 检验西三旗建制起始年份必须在明代（1368-1644）
    xisanqi_unit = next((u for u in ds.administrative_units if u.id == "unit_xisanqi_garrison"), None)
    assert xisanqi_unit is not None
    assert xisanqi_unit.valid_start_year == 1368, "西三旗军屯始设公元年份必须锚定至明初（1368）"
    assert "小旗" in xisanqi_unit.description, "西三旗建置必须注明小旗军屯编制"

    # 2. 检验娘娘府墓茔性质
    nnf_unit = next((u for u in ds.administrative_units if u.id == "unit_niangniangfu_tomb"), None)
    assert nnf_unit is not None
    assert "妃" in nnf_unit.description, "娘娘府必须确认为明代妃嫔园寝，严禁清代公主附会"
