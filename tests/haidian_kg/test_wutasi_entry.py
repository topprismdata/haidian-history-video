# -*- coding: utf-8 -*-
"""tests/haidian_kg/test_wutasi_entry.py
五塔寺 E25 塔寺时序否证层入库闸门测试.

本集特有红线:
  NC1 「塔年当寺年」必须 DISPROVEN —— 石匾+实录只证塔，寺创于永乐初年
  NC2 石匾/实录**只证塔** 必须 VERIFIED（正向判据）
  NC3 「五塔寺」俗名必须 UNSUBSTANTIATED（不系年）
  NC4 避讳改名说必须 DISPROVEN（时序不通）
  NC5 国保为第一批（1961-03-04），且**1961 年首批无「1-75」式编号体系**
  同指 金刚宝座塔 ⟷ top_zhenjuesi；俗名五塔寺 ⟷ top_zhenjuesi（不重复建模）

Python 3.9.6: 禁 X | None、禁 match。
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from haidian_kg.calibration import wutasi as W
from haidian_kg.calibration.people import PEOPLE
from haidian_kg.calibration.digital_resources import RESOURCES
from haidian_kg.production_exports import KnowledgeBase, audit_script
from haidian_kg.qa_gate import QAGate
from haidian_kg.ontology.epistemic import EpistemicStatus, HistoricalSource
from haidian_kg.ontology.spatiotemporal import IdentityRelation


# 审计句必须含可消歧实体名。「大觉金刚宝座」是本模块唯一登记的塔之名号
# （app_e25_pagoda_name），故正片审计句围绕该名号构造；「金刚宝座塔」
# 是塔的通称而非登记指称，单独出现时无法消歧——这与正片用「金刚宝座」
# 四字（石匾原文）并不矛盾，两者用途不同。
_GATE_SCRIPT = (
    "1473年大觉金刚宝座塔成于京城西关外。\n"
    "1473年大觉金刚宝座塔成，太监钱义奉敕主持。\n"
)

_ADV = (
    "1473年金刚宝座塔彻底消失，此后不复存在。\n1473年金刚宝座塔建屋五百间。",
    [("1473年金刚宝座塔彻底消失，此后不复存在", "非通过"),
     ("1473年金刚宝座塔建屋五百间", "非通过")],
)


def _kb():
    return KnowledgeBase(
        sources=W.SOURCES,
        divisions=W.DIVISIONS,
        facts=W.FACTS,
        entities=W.ENTITIES,
        states=W.STATES,
        identities=W.IDENTITIES,
        appellations=W.APPELLATIONS,
        references=W.REFERENCES,
        transformations=W.TRANSFORMATIONS,
        propositions=W.PROPOSITIONS,
        adoptions=W.ADOPTIONS,
        aggregates=W.AGGREGATES,
        people=PEOPLE,
        resources=RESOURCES,
    )


def _adopt(pid):
    for a in W.ADOPTIONS:
        if a.proposition_id == pid:
            return a
    raise AssertionError("adoption 不存在: %s" % pid)


def _fact(fid):
    for f in W.FACTS:
        if f.id == fid:
            return f
    raise AssertionError("fact 不存在: %s" % fid)


class TestWutasiTimeOrderGate:
    def test_nc1_pagoda_year_as_temple_year_disproven(self):
        """🔴 NC1：本集核心。塔年当寺年必须 DISPROVEN。"""
        a = _adopt("prop_e25_ta_1473_as_si_founder")
        assert a.status == EpistemicStatus.DISPROVEN
        assert "永乐" in a.rationale
        assert "1473" in a.rationale

    def test_nc1_stele_only_mentions_pagoda_not_si(self):
        """🔴 NC2：石匾通篇无「寺」字，「金刚宝座」四字指塔。"""
        f = _fact("fact_e25_shibei_only_pagoda")
        assert "敕建金剛寶座" in f.verbatim_quote
        assert "寺" not in f.verbatim_quote, "石匾原文不得含「寺」字"
        assert "只证塔" in f.translator_note

    def test_nc2_stele_only_proves_pagoda_verified(self):
        a = _adopt("prop_e25_stele_only_proves_pagoda")
        assert a.status == EpistemicStatus.VERIFIED
        assert "塔" in a.rationale

    def test_nc2_shilu_verb_on_pagoda(self):
        """实录动词落在「塔」，所赐之名亦为塔的名号。"""
        f = _fact("fact_e25_shilu_pagoda_done")
        assert "金剛寶座塔成" in f.verbatim_quote
        assert "賜名大覺金剛寶座" in f.verbatim_quote

    def test_nc3_suming_year_unsubstantiated(self):
        a = _adopt("prop_e25_suming_year_unknown")
        assert a.status == EpistemicStatus.UNSUBSTANTIATED
        assert "严禁系年" in a.rationale

    def test_nc4_bihuang_rename_unsubstantiated(self):
        """避讳说无一手书证可作反驳依据（absence of evidence ≠ evidence of absence），
        故采 UNSUBSTANTIATED 而非 DISPROVEN；「时序不通」写入 rationale 作正片禁令。"""
        a = _adopt("prop_e25_qianlong_bihuang_rename")
        assert a.status == EpistemicStatus.UNSUBSTANTIATED
        assert "时序不通" in a.rationale

    def test_nc5_guobao_first_batch_no_numbering(self):
        """🔴 NC5：必须第一批（1961-03-04），且不得出现「1-75」式编号。"""
        blob = " ".join(f.verbatim_quote + f.translator_note for f in W.FACTS)
        blob += " ".join(p.statement + p.inference_method for p in W.PROPOSITIONS)
        blob += " ".join(a.rationale for a in W.ADOPTIONS)
        blob += " ".join(e.canonical_label for e in W.ENTITIES)
        assert "第一批" in blob, "必须写明第一批国保"
        assert "1961-03-04" in blob or "一九六一" in blob, "必须写明 1961-03-04 公布"
        assert "1-75" not in blob, "1961 年首批无「1-75」式编号体系，严禁引用网传编号"

    def test_same_as_extractor_no_duplicate_modeling(self):
        ids = [d.subject_entity_ids for d in W.IDENTITIES]
        assert any("top_zhenjuesi" in s for s in ids), "必须与 extractor 的 top_zhenjuesi 同指挂钩"
        assert any("top_wutasi" in s for s in ids), "俗名五塔寺须与 top_zhenjuesi 挂钩"
        rels = {d.relation for d in W.IDENTITIES}
        assert IdentityRelation.SAME_CONTINUANT in rels
        assert len(rels) == 1, "塔与寺、寺与俗名皆为同一持续体"

    def test_all_sources_resolved(self):
        assert all(isinstance(s, HistoricalSource) for s in W.SOURCES)

    def test_gate_script_passes(self):
        results = audit_script(_kb(), _GATE_SCRIPT)
        assert len(results) == 2
        for r in results:
            assert r.verdict.value == "通过", "%s -> %s: %s" % (
                r.claim.claim_text, r.verdict.value, r.reason)

    def test_qa_gate_passes(self):
        rep = QAGate("wutasi", _kb(), adversarial=_ADV).run()
        assert rep.passed, rep.render()
