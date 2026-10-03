"""
tests/haidian_kg/test_cishousi_entry.py
慈寿寺／永安万寿塔 E19 入库闸门测试

每个测试锁一条闸门红线或负控制。红线被改写时测试必须失败——
「测试全过」若不能拦住红线改写，就是恒真测试，不允许存在。

Python 3.9.6：禁 X | None、禁 match。
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from haidian_kg.calibration import cishousi as C
from haidian_kg.calibration.people import PEOPLE
from haidian_kg.calibration.digital_resources import RESOURCES
from haidian_kg.production_exports import KnowledgeBase, audit_script
from haidian_kg.ontology.epistemic import EpistemicStatus
from haidian_kg.ontology.video_contracts import AuditVerdict

import re

#: 闸门审计脚本：每句都是研究档案已冻结的结论，正片不得与之冲突
_GATE_SCRIPT = (
    "慈寿寺在阜成门外八里，是圣母慈圣皇太后所建。\n"
    "万历四年二月始事，万历六年仲秋既望落成。\n"
    "永安万寿塔名永安塔，十三级，与寺同期兴建。\n"
    "李太后捐帑倡建，潞王、公主暨诸宫眷助佐。\n"
    "乾隆二十二年奉敕修葺。\n"
    "1783年张居正所撰碑已无存，双碑仍在，九莲像仍供奉。\n"
    "光绪间今寺毁尽，惟浮图及碑存。\n"
)

_kb_area_holder = {}


def _kb_for_area():
    from haidian_kg.production_exports import KnowledgeBase
    if "kb" not in _kb_area_holder:
        _kb_area_holder["kb"] = KnowledgeBase(
            sources=C.SOURCES, divisions=C.DIVISIONS, facts=C.FACTS,
            entities=C.ENTITIES, states=C.STATES, identities=C.IDENTITIES,
            appellations=C.APPELLATIONS, references=C.REFERENCES,
            transformations=C.TRANSFORMATIONS, propositions=C.PROPOSITIONS,
            adoptions=C.ADOPTIONS, aggregates=C.AGGREGATES,
            people=PEOPLE, resources=RESOURCES)
    return _kb_area_holder["kb"]


@pytest.fixture(scope="module")
def kb():
    return KnowledgeBase(
        sources=C.SOURCES, divisions=C.DIVISIONS, facts=C.FACTS,
        entities=C.ENTITIES, states=C.STATES, identities=C.IDENTITIES,
        appellations=C.APPELLATIONS, references=C.REFERENCES,
        transformations=C.TRANSFORMATIONS, propositions=C.PROPOSITIONS,
        adoptions=C.ADOPTIONS, aggregates=C.AGGREGATES,
        people=PEOPLE, resources=RESOURCES)


def _prop(pid):
    for p in C.PROPOSITIONS:
        if p.id == pid:
            return p
    raise AssertionError("proposition 不存在: %s" % pid)


def _adopt(pid):
    for a in C.ADOPTIONS:
        if a.proposition_id == pid:
            return a
    raise AssertionError("adoption 不存在: %s" % pid)


def _ref(rid):
    for r in C.REFERENCES:
        if r.id == rid:
            return r
    raise AssertionError("reference 不存在: %s" % rid)


def _fact(fid):
    for f in C.FACTS:
        if f.id == fid:
            return f
    raise AssertionError("fact 不存在: %s" % fid)


# ==================================================================
# 入库闸门
# ==================================================================

class TestCishousiEntryGate:
    def test_entry_passes_gate(self, kb):
        """每句审计不得 BLOCK——BLOCK 即口播与档案冲突。"""
        results = audit_script(kb, _GATE_SCRIPT)
        blocked = [r for r in results if r.verdict == AuditVerdict.BLOCK]
        assert not blocked, "BLOCK: %s" % [(r.claim, r.reason) for r in blocked]

    def test_shi_and_ta_are_separate_entities(self, kb):
        """寺与塔必须分立——合并会让「寺院建筑亡、塔存」变成自相矛盾。"""
        assert kb.entities["ent_cishousi"].canonical_label.startswith("慈寿寺")
        assert kb.entities["ent_cishousi_ta"].canonical_label.startswith("永安万寿塔")

    def test_partial_continuation_not_successor(self):
        """光绪间寺毁而塔存：是部分延续，不是「塔取代了寺」。"""
        d = [i for i in C.IDENTITIES if i.id == "dia_ta_same_cont"][0]
        assert d.relation.value == "部分延续"
        assert d.is_orthogonal_to_state_change is True

    def test_guobao_code_written(self, kb):
        """国务院原始名单：编号 711／7-0711-3-009（待核 8 CLOSED）。"""
        st = kb.states["st_ta_now"]
        assert "7-0711-3-009" in st.geometry
        assert "711" in st.geometry


# ==================================================================
# E19 闸门 C01：塔 1576 竣工＝校勘推定，**不得升格**
# ==================================================================

class TestC01TowerCompletionIsInference:
    def test_1576_completion_is_contested_not_verified(self):
        a = _adopt("prop_tower_completion_1576")
        assert a.status == EpistemicStatus.CONTESTED, (
            "1576 塔已竣必须保持 CONTESTED——它是从讹文校勘推出的，"
            "不是原碑直读。升 VERIFIED 即为 C01 违规")
        assert a.confidence <= 0.35

    def test_inference_method_declares_cross_layer_problem(self):
        """跨层取证（按语层→引文层）必须写在推理方法里，不能藏起来。"""
        p = _prop("prop_tower_completion_1576")
        assert "跨层取证" in p.inference_method
        assert "故地" in p.inference_method, "必须写明「凡二岁告成」的宾语是故地（寺基址）"

    def test_alternative_explanations_at_least_three(self):
        """校勘推定必须列多种解释，禁止只写一种（本体硬约束）。"""
        p = _prop("prop_tower_completion_1576")
        assert len(p.alternative_explanations) >= 3

    def test_erroneous_text_stored_but_flagged_corruption(self):
        """「隆慶丙子」讹文要存档（供后人查校），但必须标为 TEXTUAL_CORRUPTION。"""
        app = [a for a in C.APPELLATIONS if a.id == "app_err_longqing"][0]
        assert app.kind.value == "文献讹字"
        f = _fact("tf_yhls_erroneous")
        assert "隆慶" not in f.verbatim_quote, "引文必须照录传抄文字，校改写在 translator_note"
        assert "宝塔工竣" in f.verbatim_quote or "寳塔工竣" in f.verbatim_quote
        assert "禁进口播" in f.translator_note


# ==================================================================
# 负控制：三条被证伪的流行说法
# ==================================================================

class TestNegativeControls:
    def test_jiu_lian_not_building_motive(self):
        """建寺缘起＝荐福+祈储，与九莲梦无涉（分层铁律）。"""
        a = _adopt("prop_jiu_lian_motive")
        assert a.status == EpistemicStatus.DISPROVEN
        assert "tf_zwzjj_motive" in a.refuting_fact_ids

    def test_monk_says_prefix_preserved(self):
        """「寺有僧自言」五字前缀必须完整——升格就靠删掉它。"""
        f = _fact("tf_djwl5_monk_says")
        assert "寺有僧自言" in f.verbatim_quote
        assert "菩薩後身" in f.verbatim_quote

    def test_funding_not_sole(self):
        a = _adopt("prop_sole_funding")
        assert a.status == EpistemicStatus.DISPROVEN
        assert "各邸復助" in _fact("tf_cs97_funding").verbatim_quote
        assert "潞王公主" in _fact("tf_zwzjj_funding").verbatim_quote

    def test_fire_drama_unsubstantiated(self):
        """「毁于清末大火」无一手记载——负控制，不是待考。"""
        a = _adopt("prop_cishousi_fire_drama")
        assert a.status == EpistemicStatus.UNSUBSTANTIATED
        assert a.confidence <= 0.15

    def test_temple_destruction_anchor_is_primary(self):
        """寺毁唯一硬锚是一手时人记，且「及碑」是复数。"""
        f = _fact("tf_tzoyw9_destroyed")
        assert "惟浮圖及碑存" in f.verbatim_quote
        assert "只剩塔" in f.translator_note or "不是只剩塔" in f.translator_note

    def test_1783_only_zhangjuzheng_stele_lost(self):
        """1783 亡的是张居正碑，不是两碑皆亡。"""
        st = kb_state = C.STATES[[s.id for s in C.STATES].index("st_cs_1783")]
        assert "张居正所撰碑已无存" in st.geometry
        assert "双碑仍在" in st.geometry
        assert "九莲像" in st.geometry


# ==================================================================
# 像素级直读修正：四处讹字不得回退
# ==================================================================

class TestPixelLevelTranscription:
    """2026-10-03 逐字放大直读修正了四处目视转写讹字。

    这批书影曾被目视转写处理，讹字恰好落在最要紧的论断字上，
    并据此试图推翻 C01。下游不得回退。
    """

    def test_gucheng_not_jiecheng(self):
        f = _fact("tf_cs97_completion")
        assert "告成" in f.verbatim_quote, "「凡二歲告成」——告，非皆"
        assert "皆成" not in f.verbatim_quote

    def test_suduobo_not_kongta(self):
        f = _fact("tf_cs97_tower")
        assert "窣堵波" in f.verbatim_quote, "窣堵波＝stupa，砖塔通称"
        assert "空塔波" not in f.verbatim_quote

    def test_zadi_not_zalang(self):
        f = _fact("tf_cs97_funding")
        assert "各邸復助" in f.verbatim_quote, "各邸＝诸王府邸"
        assert "各郎" not in f.verbatim_quote

    def test_sujiu_not_sujun(self):
        f = _fact("tf_cs97_funding")
        assert "因得速就如此" in f.verbatim_quote
        assert "速竣" not in f.verbatim_quote

    def test_stele_sides_not_swapped(self):
        """左碑紫竹、右碑鱼篮——曾被记反。"""
        assert "左碑前刻紫竹觀音像" in _fact("tf_cs97_tableleft").verbatim_quote
        assert "右碑前刻魚籧觀音像" in _fact("tf_cs97_tableright").verbatim_quote

    def test_zan_tongzuo_is_formula_not_author(self):
        f = _fact("tf_cs97_tableright")
        assert "贊同左" in f.verbatim_quote
        assert "体例" in f.translator_note, "「贊同左」是赞的体例同左碑，不是赞的作者在左碑"


# ==================================================================
# 2026-10-03 KB 伪引文修正：三处不得回退
# ==================================================================

class TestNoFabricatedQuotes:
    def test_dijingjingwulue_quote_replaced(self):
        """原引文「慈寿寺在阜成门外八里庄…京师地标也」在卷五不存在，已撤。"""
        f = _fact("tf_djwl5_site")
        assert "塔十三級" in f.verbatim_quote
        assert "京师地标也" not in f.verbatim_quote
        assert "伪引文" in f.translator_note

    def test_linglong_name_is_contested(self):
        """「明代即称玲珑宝塔」缺一手佐证，降 CONTESTED，不得作成播因果。"""
        a = _adopt("prop_linglong_early_name")
        assert a.status == EpistemicStatus.CONTESTED
        assert a.confidence <= 0.3

    def test_park_area_time_tense_marked(self):
        """7 公顷是 1990 建园资料，8.13 是现行名录——不得无时态混用。"""
        r = _ref("ref_park_area")
        assert r.status == EpistemicStatus.CONTESTED
        assert "7" in r.provenance and "8.13" in r.provenance


# ==================================================================
# 闸门 C02 / C06 / C10 的表述红线
# ==================================================================

class TestGateRedLines:
    def test_c02_ruins_include_steles(self):
        """C02：不得把遗存压成「只剩塔」——「惟浮圖及碑存」是复数。

        判据要能分辨「把遗存压成只剩塔」与「说明为什么不是只剩塔」——
        所以先剥掉带否定/禁令标记的说明性括注，再查禁用表述。
        """
        import re
        for st in C.STATES:
            blob = " ".join(filter(None, [st.geometry, st.function]))
            # 剥掉 **禁…** 与 ——… 形式的说明性括注
            stripped = re.sub(r"\*\*[^*]*\*\*", "", blob)
            stripped = re.sub(r"——[^—]*", "", stripped)
            assert "只剩塔" not in stripped, "C02 违规: %s" % st.id
            assert "一寺亡塔存" not in stripped
            assert "寺院建筑亡" not in stripped

    def test_c06_west_bank_not_south(self):
        """C06 硬伤：塔在昆玉河西岸，绝不是南岸。"""
        r = _ref("ref_geography")
        assert "西岸" in r.provenance
        assert "严禁写「南岸」" in r.provenance

    def test_c10_park_area_not_in_production_script(self):
        """C10：面积不进正片——审计脚本逐句不得声称公园面积。"""
        import re
        results = audit_script(kb=_kb_for_area(), script=_GATE_SCRIPT)
        for r in results:
            claim_text = getattr(r.claim, "claim_text", str(r.claim))
            stripped = re.sub(r"[（(][^）)]*[）)]", "", claim_text)
            assert "公顷" not in stripped, "C10 违规，面积不得进正片: %s" % claim_text

    def test_tower_height_no_false_precision(self):
        """塔高只说近 50 米，禁伪精确。"""
        st = C.STATES[[s.id for s in C.STATES].index("st_ta_now")]
        assert "近50米" in st.geometry
        stripped = re.sub(r"\*\*[^*]*\*\*", "", st.geometry)
        assert "50.36" not in stripped, "伪精确不得出现在事实描述中"

    def test_1757_repair_not_rebuild(self):
        """1757 只称修葺，规模无载。"""
        st = C.STATES[[s.id for s in C.STATES].index("st_cs_1757")]
        assert "规模无载" in st.function
        stripped = re.sub(r"\*\*[^*]*\*\*", "", st.function)
        assert "大修" not in stripped and "重建" not in stripped
