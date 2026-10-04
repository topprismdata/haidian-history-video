"""
tests/haidian_kg/test_era4_liao_jin.py
测试 Era 4（辽南京与金中都帝都期，938-1215）
验证大觉寺辽大安四年石碑硬物证、金中都立都、玉泉山芙蓉殿御泉与西山八大水院
"""
import pytest
from haidian_kg.ontology.schema import EvidenceLevel, EpistemicStatus
from haidian_kg.extractor import HaidianCorpusExtractor


def test_era4_liao_jin_institutions_and_stele_attestations():
    """验证辽南京宛平县分治、大觉寺辽碑硬证据、金中都建立与玉泉山芙蓉殿工程"""
    ds = HaidianCorpusExtractor.load_or_extract()

    # 1. 验证地物与都城实体
    feat_ids = {f.id for f in ds.physical_features}
    unit_ids = {u.id for u in ds.administrative_units}
    assert "feat_diaoyutai_lake" in feat_ids, "缺失海淀钓鱼台金代行宫蓄水地物"
    assert "unit_liao_nanjing" in unit_ids, "缺失辽南京析津府宛平县建置实体"
    assert "unit_jin_zhongdu" in unit_ids, "缺失金中都大兴府都城建置实体"
    assert "unit_shengshui_court" in unit_ids, "缺失金章宗西山圣水院（香山寺）建置实体"

    # 2. 验证核心书证
    atts = {a.id: a for a in ds.place_attestations}
    assert "attest_dajuesi_liao_stele" in atts, "缺失大觉寺清水院辽碑书证"
    assert "attest_yuquanshan_jinshi" in atts, "缺失《金史》玉泉山行宫书证"
    assert "attest_diaoyutai_dijing" in atts, "缺失钓鱼台书证"

    # 🔴 2026-10-04 订正：本断言原为 `assert "大辽大安四年" in liao_stele.quote`，
    # 那是**把伪碑文写成回归保护**。纪年实为**咸雍四年 1068**（碑末「嵗次戊申」干支回验；
    # 大安四年 1088 = 戊辰，与碑文明文矛盾），碑名为《暘臺山清水院創造藏經記》，
    # 撰者僧志延，施主为汉人优婆塞南陽鄧公從貴。详见 QUARANTINE.md Q-004。
    liao_stele = atts["attest_dajuesi_liao_stele"]
    assert liao_stele.evidence_level == EvidenceLevel.L1_ARCHAEOLOGICAL, (
        "清水院碑是现存原石，应为 L1；旧稿标 L2 与 corpus Level 1 自相矛盾")
    assert liao_stele.epistemic_status == EpistemicStatus.VERIFIED
    assert liao_stele.recorded_year == 1068, (
        "清水院碑纪年应为咸雍四年(1068)，非大安四年(1088)")
    for frag in ("嵗次戊申", "咸雍四年", "南陽鄧公從貴", "五百七十九帙", "院之興止于近代"):
        assert frag in liao_stele.quote, "碑文实录缺关键片段: %s" % frag
    # 伪碑名与伪纪年不得复活
    for dead in ("大辽大安四年", "重构佛殿", "契丹贵族"):
        assert dead not in liao_stele.quote, "伪碑文片段复活: %s" % dead

    # 玉泉山：仅「玉泉山行宮」为《金史》实书，芙蓉殿等已判死
    yuquan = atts["attest_yuquanshan_jinshi"]
    assert "玉泉山行宮" in yuquan.quote
    for dead in ("芙蓉殿", "大定二十六年", "同乐园洗马沟"):
        assert dead not in yuquan.quote, "《金史》伪引文片段复活: %s" % dead

    # 钓鱼台：金章宗说无书证，实文人物是金代文人王鬱
    diaoyu = atts["attest_diaoyutai_dijing"]
    assert "金王鬱" in diaoyu.quote, "钓鱼台实文应为「金王鬱釣魚臺」"
    for dead in ("章宗", "宛平县西十里", "积水成池"):
        assert dead not in diaoyu.quote, "钓鱼台伪引文片段复活: %s" % dead


def test_era4_negative_control_dajuesi_origin_and_jin_endpoint():
    """负控制断言：大觉寺始建绝非金代（必须由辽碑证实为辽代）；金中都都城实体严格止于1215年"""
    ds = HaidianCorpusExtractor.load_or_extract()

    # 1. 检验大觉寺书证：最早确证书证年份必须为辽代（1068），严禁被削矮至金代
    dajue_atts = [a for a in ds.place_attestations if a.toponym_id == "top_dajuesi"]
    stele_att = next((a for a in dajue_atts if "辽" in a.dynasty or a.recorded_year == 1068), None)
    assert stele_att is not None, "大觉寺必须包含辽代咸雍四年(1068)确证书证"
    # 🔴 干支互验前置规则：1068=戊申。碑刻纪年与干支不符即不得入库
    #    （本条旧稿 1088=戊辰 与碑文「戊申」矛盾，曾长期存活）
    assert "戊申" in stele_att.quote, "碑文须含干支「嵗次戊申」以供年号—干支互验"

    # 2. 检验金中都都城实体：valid_end_year 必须严格为 1215 年（蒙古攻破降为燕京）
    jin_unit = next((u for u in ds.administrative_units if u.id == "unit_jin_zhongdu"), None)
    assert jin_unit is not None
    assert jin_unit.valid_end_year == 1215, f"金中都都城实体终点年份错误: {jin_unit.valid_end_year}（应为1215年）"
