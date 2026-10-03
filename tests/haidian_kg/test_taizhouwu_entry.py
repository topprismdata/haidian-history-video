# -*- coding: utf-8 -*-
"""tests/haidian_kg/test_taizhouwu_entry.py
太舟坞 E22 知识库入库闸门测试.

测试锁死 E22 核心学术红线与负控制:
1. 证据分层:
   - 《旧唐书》《新唐书》(L2) 确证神龙元年(705)设羁縻带州安置契丹降户;
   - 唐天宝九载焦金府墓志铭(L1) 确证带州治所寄治昌平清水店;
   - 《元史·河渠志》(L2) 确证至元二十九年(1292)郭守敬白浮引水渠傍西山南下;
   - 《日下旧闻考》卷104(L3) 确证黑龙潭在太舟坞村西, 康熙二十年建龙王庙;
   - 1915《实测京师四郊图》(L2档案地图) 确证「太舟塢」官方测绘定型。
2. 负控制判据:
   - NC1: 「唐代带州治所即今日太舟坞村」必须为 DISPROVEN (治所在昌平清水店);
   - NC2: 「已考古发掘出元代船坞木桩构件」必须为 UNSUBSTANTIATED (水利地理推断);
   - NC3: 「太舟坞地名源于带州音转」必须为 CONTESTED 假说 (音近但缺乏地望直核);
   - NC4: 「太舟坞源于元代白浮水利船坞」必须为 WELL_SUPPORTED / VERIFIED 假说;
3. 空间实体与指称:
   - ent_taizhouwu (聚落实体), ent_heilongtan (泉潭与古刹), ent_daizhou (唐代羁縻政区);
   - 正片审计脚本全量通过。

Python 3.9.6: 禁 X | None, 禁 match.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from haidian_kg.calibration import taizhouwu as T
from haidian_kg.calibration import bibliography as BIB
from haidian_kg.calibration.people import PEOPLE
from haidian_kg.calibration.digital_resources import RESOURCES
from haidian_kg.production_exports import KnowledgeBase, audit_script
from haidian_kg.qa_gate import QAGate
from haidian_kg.ontology.epistemic import (
    EpistemicStatus, HistoricalSource, SourceCategory,
)
from haidian_kg.ontology.spatiotemporal import AppellationKind


_GATE_SCRIPT = (
    "705年唐中宗神龙元年析营州置羁縻带州以安置契丹降户。\n"
    "750年唐天宝九载带州折冲都尉焦金府归葬于昌平县清水店之原。\n"
    "1292年元至元二十九年郭守敬开辟白浮堰，太舟坞成为山麓漕运官坞。\n"
    "1681年清康熙二十年黑龙潭建龙王庙并御制碑文。\n"
    "1783年乾隆朝官修日下旧闻考载黑龙潭在太舟坞村西。\n"
    "1915年北洋陆军测地局实测京师四郊图标绘太舟坞。\n"
)

#: 对抗样本：消亡假通过 + 数字口径混说，逐句必须「非通过」
_ADV = (
    "1681年太舟坞彻底消失，此后不复存在。\n705年带州置县五十处。",
    [("1681年太舟坞彻底消失，此后不复存在", "非通过"),
     ("705年带州置县五十处", "非通过")],
)


def _build_test_kb():
    return KnowledgeBase(
        sources=T.SOURCES,
        divisions=T.DIVISIONS,
        facts=T.FACTS,
        entities=T.ENTITIES,
        states=T.STATES,
        identities=T.IDENTITIES,
        appellations=T.APPELLATIONS,
        references=T.REFERENCES,
        transformations=T.TRANSFORMATIONS,
        propositions=T.PROPOSITIONS,
        adoptions=T.ADOPTIONS,
        aggregates=T.AGGREGATES,
        people=PEOPLE,
        resources=RESOURCES,
    )


def test_taizhouwu_entities_defined():
    assert "ent_taizhouwu" in T.ENTITIES_MAP
    assert "ent_heilongtan" in T.ENTITIES_MAP
    assert "ent_daizhou" in T.ENTITIES_MAP
    assert "太舟坞" in T.ENTITIES_MAP["ent_taizhouwu"].canonical_label
    assert "带州" in T.ENTITIES_MAP["ent_daizhou"].canonical_label

def test_sources_and_facts_layering():
    facts = {f.id: f for f in T.FACTS}
    assert "fact_jiutangshu_daizhou" in facts
    assert "fact_xintangshu_daizhou" in facts
    assert "fact_epitaph_qingshuidian" in facts
    assert "fact_yuanshi_baifuyan" in facts
    assert "fact_rixia_heilongtan" in facts

    # 志文出土实物核验
    ep_fact = facts["fact_epitaph_qingshuidian"]
    assert "清水店" in ep_fact.verbatim_quote
    assert "孤竹府" in ep_fact.verbatim_quote
    assert "焦金府" in ep_fact.translator_note


def test_negative_controls_rigorous():
    adoptions = {a.proposition_id: a for a in T.ADOPTIONS}

    # NC1: 带州治所在太舟坞村 -> 必须被驳斥 DISPROVEN
    nc1 = adoptions["prop_taizhouwu_is_daizhou_seat"]
    assert nc1.status == EpistemicStatus.DISPROVEN
    assert "昌平清水店" in nc1.rationale

    # NC2: 出土元代船坞木桩构件 -> 必须 UNSUBSTANTIATED
    nc2 = adoptions["prop_excavated_yuan_wharf"]
    assert nc2.status == EpistemicStatus.UNSUBSTANTIATED

    # NC3: 音转假说保持 CONTESTED
    nc3 = adoptions["prop_daizhou_phonetic_hypothesis"]
    assert nc3.status == EpistemicStatus.CONTESTED

    # NC4: 水利船坞假说保持 WELL_SUPPORTED
    nc4 = adoptions["prop_baifu_wharf_hypothesis"]
    assert nc4.status == EpistemicStatus.VERIFIED
def test_gate_audit_script_passes():
    kb = _build_test_kb()
    results = audit_script(kb, _GATE_SCRIPT)
    assert len(results) == 6
    for r in results:
        assert r.verdict.value == "通过", (
            "%s -> %s: %s" % (r.claim.claim_text, r.verdict.value, r.reason)
        )


def test_qa_gate_passes_for_taizhouwu():
    kb = _build_test_kb()
    rep = QAGate("taizhouwu", kb, adversarial=_ADV).run()
    assert rep.passed, rep.render()
