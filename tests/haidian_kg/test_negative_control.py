"""
tests/haidian_kg/test_negative_control.py
历史考据负控制与伪说证伪断言专项测试套件
严格验证知识图谱能主动隔离民间伪说与学术硬伤，确保学术推理防线牢固：
1. 西三旗：明代军屯小旗 vs 满洲八旗伪说 (强制标记 DISPROVEN，严禁进入正史链)
2. 高梁桥：1292年郭守敬建闸 vs 979年宋辽战役桥 (严禁时空倒置313年)
3. 六郎庄：牛栏庄-柳浪庄雅化 vs 杨家将驻军 (强制标记 FOLK_LEGEND，严禁标 VERIFIED)
4. 中关村：1913年京西图已见中关村 vs 陈垣独创提议 (强制标记 CONTESTED，多假说并存)
"""
import pytest
from haidian_kg.query import KGQueryEngine
from haidian_kg.ontology.schema import EpistemicStatus, EvidenceLevel


def test_negative_control_xisanqi_not_manchu():
    """负控制断言1：西三旗绝非清代满洲八旗驻军"""
    engine = KGQueryEngine()

    # 1. 查询西三旗的关联建置实体
    unit_labels = []
    for s, p, o in engine.graph.triples((None, None, None)):
        if "xisanqi" in str(s).lower() and "AdministrativeUnit" in str(o):
            for _, _, l in engine.graph.triples((s, None, None)):
                pass

    # 2. 检验西三旗书证中是否存在 DISPROVEN 伪说，且正史书证确凿为明代小旗
    atts = engine.get_attestations("西三旗")
    assert len(atts) >= 2, "西三旗必须同时包含正史书证与证伪伪说"

    disproven_claims = [a for a in atts if a["epistemic_status"] == EpistemicStatus.DISPROVEN.value]
    verified_claims = [a for a in atts if a["epistemic_status"] == EpistemicStatus.VERIFIED.value]

    assert len(disproven_claims) >= 1, "西三旗缺失八旗说证伪断言"
    assert "满洲" in disproven_claims[0]["attested_name"] or "满洲" in disproven_claims[0]["quote"], "证伪项应针对满洲八旗附会"

    assert len(verified_claims) >= 1, "西三旗缺失明代小旗军屯确证"
    assert "小旗" in verified_claims[0]["quote"] or "明代" in verified_claims[0]["quote"], "确证书证应指向明代小旗"


def test_negative_control_gaoliangqiao_temporal_inversion():
    """负控制断言2：高梁桥绝非979年宋辽高梁河之战时的桥梁（时空倒置313年）"""
    engine = KGQueryEngine()

    # 1. 检验证伪伪说列表中必须明确收录高梁桥宋辽战役桥说
    disproven_myths = engine.find_disproven_myths()
    gaoliang_myths = [m for m in disproven_myths if "高梁桥" in m["title"]]
    assert len(gaoliang_myths) >= 1, "高梁桥979年战场桥说必须被标记为证伪伪说 (DISPROVEN)"

    # 2. 检验高梁闸/高梁桥的始建书证年份必须严格晚于1290年（元代郭守敬）
    atts = engine.get_attestations("高梁桥")
    creation_years = []
    for a in atts:
        import rdflib
        HHTO = rdflib.Namespace("http://history.haidian.gov.cn/ontology/")
        att_ref = rdflib.URIRef(a["attestation_uri"])
        for _, _, yr in engine.graph.triples((att_ref, HHTO.recordedYear, None)):
            creation_years.append(int(yr))

    assert 1292 in creation_years, "高梁桥创建证据必须严格锚定至元至元二十九年（1292）"
    assert 979 not in [y for y in creation_years if y > 0 and y != 1950], "979年绝不可作为桥梁创建年份"


def test_negative_control_liulangzhuang_folk_legend():
    """负控制断言3：六郎庄杨六郎抗辽绝非真实历史，严禁标为VERIFIED"""
    engine = KGQueryEngine()

    atts = engine.get_attestations("六郎庄")
    legend_atts = [a for a in atts if "杨家将" in a["attested_name"] or "杨六郎" in a["attested_name"]]

    assert len(legend_atts) >= 1, "必须包含杨家将民间传说书证"
    for leg in legend_atts:
        assert leg["epistemic_status"] == EpistemicStatus.FOLK_LEGEND.value, "杨六郎传说状态必须严格为 FOLK_LEGEND"
        assert leg["evidence_level"] == EvidenceLevel.L5_FOLK_LEGEND.value, "杨六郎传说证据等级必须为 Level 5"


def test_negative_control_zhongguancun_competing_hypotheses():
    """负控制断言4：中关村命名多假说共存，1913年京西图已见中关村，陈垣提议不可作为唯一垄断解释"""
    engine = KGQueryEngine()

    contested = engine.find_contested_hypotheses()
    zgc_contested = [c for c in contested if "中关村" in c["title"] or "陈垣" in c["title"]]
    assert len(zgc_contested) >= 1, "中关村改名陈垣说必须被标定为学术争议假说 (CONTESTED)"

    # 演变前身必须为中官村太监义地
    lineage = engine.trace_evolution("中关村")
    labels = [hop["label"] for hop in lineage]
    assert "中官村" in labels, "中关村演变序列必须包含前身中官村"
