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

    # 【R11-5 回灌 2026-10-04】本条旧版是**拟托书证**，已整体修正：
    #   ①书名与人名错配：沈榜著《宛署杂记》（万历二十一年刊），
    #     **《宛平县志》是康熙间官修的另一本书**，两者不可混挂；
    #   ②旧引文「宛平县城外西乡牛栏庄，地滨泉源，居民引水种稻」**卷五无此句**——
    #     卷五《德字·街道》只有西出西直门的里程村落并列，无「地滨泉源/引水种稻」描写。
    # 现挂真实书证（党宝海《魏公村考》转录，已与人大 iqh/ctext/维基百科交叉核）。
    assert "宛署杂记" in niulan_att.source_title, (
        "🔴 沈榜著《宛署杂记》；原挂《宛平县志·舆地志》系书名与人名错配")
    assert niulan_att.source_author == "沈榜"

    # ⚠️ 归一纪律（memory 铁律：「两侧用同一组归一函数」）：官书引文是**繁体**。
    # 旧断言写简体 `"牛栏庄" in quote` 恒红——不是数据错，是**没做繁简归一**。
    # ⚠️ 实测两张归一表对本句都不完备：expansion.normalize_form 出 "牛欄庄"（漏 欄），
    #    holdout_eval.norm_eval 同。**混合形**（牛欄庄）说明两表**不能**用来断言
    #    「简体命中」——那会得到恒假测试。正确的不变式是：书证里**含该地名**。
    # 故此处断言书证挂的地名字样（attested_name，简体系）与引文里的**繁体原形**同时在场。
    # 实文句末并列「曰小南庄、曰八里沟、曰牛欄庄」——牛栏庄确实在此句中。
    # ⚠️ 字形纪律：转录底本不同则末字繁简不同（「牛欄莊」／「牛欄庄」两者皆见）。
    # 断言对象是「该地名出现在里程并列原句中」这件事，**不是**它的繁简形态——
    # 写死单字形会让换底本时测试恒红。故两种末字字形任一命中即通过。
    assert ("牛欄莊" in niulan_att.quote) or ("牛欄庄" in niulan_att.quote), (
        "《宛署杂记》卷五街道条原句含『牛欄莊』或『牛欄庄』；got=%r" % niulan_att.quote)
    # 里程并列的定位锚点（证明这不是一条孤立的孤立引文）
    assert "北海店" in niulan_att.quote, "卷五原句作『又十里曰北海店，其旁曰…』，定位锚点须在"
    # 负控制：伪造后句已撤，命中即回归
    assert "地滨泉源" not in niulan_att.quote, (
        "🔴 「地滨泉源，居民引水种稻」系后人据地理想补，卷五无此句，不得复活")
    assert "引水种稻" not in niulan_att.quote, (
        "🔴 「引水种稻」同属伪造，不得复活")


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
