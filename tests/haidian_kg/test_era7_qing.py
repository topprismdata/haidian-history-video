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
    # 【R6 回灌 2026-10-04】旧断言 `assert "穷八家" in quote` 断言的是**被撤的伪引文**：
    # 旧数据挂《日下旧闻考》卷九十九「大有庄旧名穷八家…赐名大有庄」——E4 已核
    # ①官书原句在**卷一百**（非卷九十九）；②「赐名」情节无诏书/御制诗/宫档出处，
    # 属 L3 地方文史「据载」，不得挂在官书书证上。已拆为两条 attest。
    assert "卷一百" in dayou_att.source_title, (
        "🔴 官书原句在《日下旧闻考》卷一百（E4 已直核），非卷九十九")
    assert "达官村西南里许为大有庄" in dayou_att.quote, (
        "E4 冻结的官书 L1 原句；got=%r" % dayou_att.quote)
    assert "御道" in dayou_att.quote, "御道条是 E4 全片最硬证据之一，不得丢"
    # 负控制：赐名/穷八家不得复活在官书书证里
    assert "赐名" not in dayou_att.quote, (
        "🔴 「赐名」是 L3 据载层，无诏书出处，不得挂在官书书证上")
    assert "穷八家" not in dayou_att.quote, (
        "🔴 「穷八家」不在这条官书原句里，复活即回归")

    # 赐名故事已单独降为传说层
    lore = atts.get("attest_dayouzhuang_imperial_naming_lore")
    assert lore is not None, "赐名故事须保留在传说层条目中（证伪不等于删证）"
    assert lore.epistemic_status == EpistemicStatus.FOLK_LEGEND
    assert lore.recorded_year is None, (
        "🔴 赐名故事不锁 1750 年（E4：无诏书出处，系年是 KB 自加）")


def test_era7_negative_control_dayouzhuang_and_suzhoujie():
    """负控制断言：大有庄赐名**不得**当史实（E4 冻结 L3 据载层）；苏州街必须确认为皇家内湖买卖街"""
    ds = HaidianCorpusExtractor.load_or_extract()

    # 1. 检验大有庄演变事件：赐名故事是 L3 传说，**不得**挂乾隆帝实名触发、不锁 1750
    # 【R6 回灌 2026-10-04】旧断言要求 `triggering_person == "清高宗乾隆帝"`——
    # 那是把传说当史实写进事件层（撤证不撤结论的变体）。E4 冻结：赐名说无诏书/
    # 御制诗/宫档出处，另有「渐富裕后自行更名」的竞争解释。事件层必须同步降级。
    dayou_evt = next((e for e in ds.evolution_events if e.target_toponym_id == "top_dayouzhuang"), None)
    assert dayou_evt is not None
    assert dayou_evt.triggering_person is None, (
        "🔴 大有庄赐名说无诏书出处，事件层不得实名触发者为乾隆帝（E4 红线）")
    assert dayou_evt.occurred_year is None, (
        "🔴 赐名说不锁 1750 年（E4：系年是 KB 自加）")
    assert "传说" in dayou_evt.description or "L3" in dayou_evt.description, (
        "🔴 事件描述须显式标注该情节为传说/据载层，不得读作史实")

    # 2. 检验苏州街建制实体类别
    suzhou_unit = next((u for u in ds.administrative_units if u.id == "unit_suzhoujie_market"), None)
    assert suzhou_unit is not None
    assert suzhou_unit.unit_type == "ImperialGarden", "苏州街必须为皇家宫禁内湖集市，严禁定为民间集镇"

    # 3. 【R11-2】苏州街真实书证是昭梿《啸亭杂录》卷十，伪联句须留 DISPROVEN
    atts = {a.id: a for a in ds.place_attestations}
    assert atts["attest_suzhoujie_xiaoting"].quote.startswith("乾隆辛巳"), (
        "E12 冻结书证为《啸亭杂录》卷十「苏州街」条（维基文库原文已核）")
    assert atts["attest_suzhoujie_qianlong_poem"].epistemic_status == EpistemicStatus.DISPROVEN, (
        "🔴 《御制诗三集》联句为拟托书证，须 DISPROVEN（保留原文供审计）")
