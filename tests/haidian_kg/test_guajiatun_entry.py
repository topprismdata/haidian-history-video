# -*- coding: utf-8 -*-
"""tests/haidian_kg/test_guajiatun_entry.py
挂甲屯 E23 知识库入库闸门测试.

测试锁死 E23 核心学术红线与负控制:
1. 证据分层:
   - 《宋史·杨延昭传》(L2) 确证杨延昭镇守河北三关高阳关一线;
   - 《清圣祖实录》《清史稿》(L2) 确证顺治十年吴应熊尚主、康熙十三年三藩变伏诛;
   - 《日下旧闻考》卷76(L2/L3) 确证挂甲屯为吴应熊额驸城遗址;
   - 1915《实测京师四郊图》(L2档案地图) 确证「掛甲屯」官方测绘定型。
2. 负控制判据:
   - NC1: 「杨六郎曾在此驻军挂甲」必须为 DISPROVEN (民间演义附会);
   - NC2: 「额驸城府第建筑完整保存至今」必须为 DISPROVEN (乾隆时已仅存聚落);
3. 空间实体与指称:
   - ent_guajiatun (聚落实体), ent_efucheng_site (额驸城遗址);
   - 正片审计脚本全量通过。

Python 3.9.6: 禁 X | None, 禁 match.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from haidian_kg.calibration import guajiatun as G
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
    "1653年清顺治十年和硕恪纯长公主下嫁吴应熊营建额驸城。\n"
    "1674年清康熙十三年吴应熊因三藩之乱伏诛，额驸城抄没荒废。\n"
    "1783年乾隆朝官修日下旧闻考载挂甲屯相传为吴应熊第遗址。\n"
    "1915年北洋陆军测地局实测京师四郊图标绘挂甲屯。\n"
)

#: 对抗样本：消亡假通过 + 数字口径混说，逐句必须「非通过」
_ADV = (
    "1674年挂甲屯彻底消失，此后不复存在。\n1653年吴应熊额驸府第置仆从五千名。",
    [("1674年挂甲屯彻底消失，此后不复存在", "非通过"),
     ("1653年吴应熊额驸府第置仆从五千名", "非通过")],
)


def _build_test_kb():
    return KnowledgeBase(
        sources=G.SOURCES,
        divisions=G.DIVISIONS,
        facts=G.FACTS,
        entities=G.ENTITIES,
        states=G.STATES,
        identities=G.IDENTITIES,
        appellations=G.APPELLATIONS,
        references=G.REFERENCES,
        transformations=G.TRANSFORMATIONS,
        propositions=G.PROPOSITIONS,
        adoptions=G.ADOPTIONS,
        aggregates=G.AGGREGATES,
        people=PEOPLE,
        resources=RESOURCES,
    )


def test_guajiatun_entities_defined():
    assert "ent_guajiatun" in G.ENTITIES_MAP
    assert "ent_efucheng_site" in G.ENTITIES_MAP
    assert "挂甲屯" in G.ENTITIES_MAP["ent_guajiatun"].canonical_label
    assert "额驸城" in G.ENTITIES_MAP["ent_efucheng_site"].canonical_label


def test_sources_and_facts_layering():
    facts = {f.id: f for f in G.FACTS}
    assert "fact_songshi_yangyanzhao" in facts
    assert "fact_rxjwk_guajiatun_efu" in facts
    assert "fact_szsl_wuyingxiong_reb" in facts
    assert "fact_qsg_kechun_gongzhu" in facts
    assert "fact_sjst1915_guajiatun" in facts

    gjt_fact = facts["fact_rxjwk_guajiatun_efu"]
    assert "額駙城" in gjt_fact.verbatim_quote
    assert "吳應熊" in gjt_fact.verbatim_quote


def test_negative_controls_rigorous():
    adoptions = {a.proposition_id: a for a in G.ADOPTIONS}

    # NC1: 杨六郎挂甲传说 -> 必须被驳斥 DISPROVEN
    nc1 = adoptions["prop_yang_liulang_guajia_legend"]
    assert nc1.status == EpistemicStatus.DISPROVEN
    assert "河北三关" in nc1.rationale

    # NC2: 额驸城地面建筑完整保存 -> 必须被驳斥 DISPROVEN
    nc2 = adoptions["prop_efucheng_existing_aboveground"]
    assert nc2.status == EpistemicStatus.DISPROVEN
    assert "仅存聚落" in nc2.rationale

    # 正事实
    p_efu = adoptions["prop_efucheng_site_guajiatun"]
    assert p_efu.status == EpistemicStatus.VERIFIED


def test_gate_audit_script_passes():
    kb = _build_test_kb()
    results = audit_script(kb, _GATE_SCRIPT)
    assert len(results) == 4
    for r in results:
        assert r.verdict.value == "通过", (
            "%s -> %s: %s" % (r.claim.claim_text, r.verdict.value, r.reason)
        )


def test_qa_gate_passes_for_guajiatun():
    kb = _build_test_kb()
    rep = QAGate("guajiatun", kb, adversarial=_ADV).run()
    assert rep.passed, rep.render()
