# -*- coding: utf-8 -*-
"""tests/haidian_kg/test_dajuesi_entry.py
大觉寺 E24 时序否证层入库闸门测试.

本集特有红线:
  NC1 「始建于金章宗」必须 DISPROVEN —— 辽咸雍四年(1068)碑「院之興止於近代」早 121 年
  NC2 「金章宗西山八院」必须 CONTESTED —— 明人《帝京景物略》追述，非金代自述
  NC3 「白玉兰植栽年代」必须 UNSUBSTANTIATED
  正层 三废三兴（康熙 1720 / 乾隆 1747）必须 VERIFIED
  同指 辽清水院 ≡ xishan 模块 ent_xs_dajuesi（不重复建模）

Python 3.9.6: 禁 X | None、禁 match。
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from haidian_kg.calibration import dajuesi as D
from haidian_kg.calibration import xishan as X
from haidian_kg.calibration import bibliography as BIB
from haidian_kg.calibration.people import PEOPLE
from haidian_kg.calibration.digital_resources import RESOURCES
from haidian_kg.production_exports import KnowledgeBase, audit_script
from haidian_kg.qa_gate import QAGate
from haidian_kg.ontology.epistemic import EpistemicStatus, HistoricalSource
from haidian_kg.ontology.spatiotemporal import IdentityRelation


_GATE_SCRIPT = (
    "1068年清水院创内外藏而龛措之。\n"
    "1068年清水院印大藏经五百七十九帙。\n"
    "1068年清水院葺诸僧舍舍钱三十万。\n"
)

_ADV = (
    "1068年清水院彻底消失，此后不复存在。\n1068年清水院建屋五百间。",
    [("1068年清水院彻底消失，此后不复存在", "非通过"),
     ("1068年清水院建屋五百间", "非通过")],
)


def _kb():
    return KnowledgeBase(
        sources=D.SOURCES,
        divisions=D.DIVISIONS,
        facts=D.FACTS,
        entities=D.ENTITIES,
        states=D.STATES,
        identities=D.IDENTITIES,
        appellations=D.APPELLATIONS,
        references=D.REFERENCES,
        transformations=D.TRANSFORMATIONS,
        propositions=D.PROPOSITIONS,
        adoptions=D.ADOPTIONS,
        aggregates=D.AGGREGATES,
        people=PEOPLE,
        resources=RESOURCES,
    )


def _adopt(pid):
    for a in D.ADOPTIONS:
        if a.proposition_id == pid:
            return a
    raise AssertionError("adoption 不存在: %s" % pid)


def _fact(fid):
    for f in D.FACTS:
        if f.id == fid:
            return f
    raise AssertionError("fact 不存在: %s" % fid)


class TestDajuesiTimeOrderGate:
    def test_nc1_jinzhangzong_founder_disproven(self):
        """🔴 NC1：本集最核心红线。通行说必须被 DISPROVEN。"""
        a = _adopt("prop_e24_jinzhangzong_founder")
        assert a.status == EpistemicStatus.DISPROVEN
        assert "1068" in a.rationale and "121" in a.rationale
        assert a.refuting_fact_ids == ["fact_e24_liao_bei_jin_jin"]

    def test_nc1_evidence_quote_contains_key_phrase(self):
        f = _fact("fact_e24_liao_bei_jin_jin")
        assert "院之興止於近代" in f.verbatim_quote
        assert "咸雍四年" in f.verbatim_quote

    def test_nc2_bayuan_is_mingren_retelling(self):
        a = _adopt("prop_e24_bayuan_mingren")
        assert a.status == EpistemicStatus.CONTESTED
        assert "明人" in a.rationale

    def test_nc3_magnolia_age_unsubstantiated(self):
        a = _adopt("prop_e24_magnolia_age")
        assert a.status == EpistemicStatus.UNSUBSTANTIATED
        assert "严禁" in a.rationale

    def test_positive_three_rebuilds_verified(self):
        a = _adopt("prop_e24_three_rebuilds")
        assert a.status == EpistemicStatus.VERIFIED

    def test_same_as_xishan_no_duplicate_modeling(self):
        ids = [d.subject_entity_ids for d in D.IDENTITIES]
        assert any("ent_xs_dajuesi" in s for s in ids), "必须与 xishan 的 ent_xs_dajuesi 同指"
        rel = {d.relation for d in D.IDENTITIES}
        assert IdentityRelation.SUCCESSOR in rel
        # xishan 必须已建成大觉寺实体
        assert any(e.id == "ent_xs_dajuesi" for e in X.ENTITIES)

    def test_all_sources_resolved(self):
        assert all(isinstance(s, HistoricalSource) for s in D.SOURCES)

    def test_gate_script_passes(self):
        results = audit_script(_kb(), _GATE_SCRIPT)
        assert len(results) == 3
        for r in results:
            assert r.verdict.value == "通过", "%s -> %s: %s" % (
                r.claim.claim_text, r.verdict.value, r.reason)

    def test_qa_gate_passes(self):
        rep = QAGate("dajuesi", _kb(), adversarial=_ADV).run()
        assert rep.passed, rep.render()
