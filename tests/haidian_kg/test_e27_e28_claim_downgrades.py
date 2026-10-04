# -*- coding: utf-8 -*-
"""E27/E28 考订回归测试：库内过度断言与伪引文的降级锁死。

🔴 背景：E27《白家疃》与 E28《温泉》的档案考订，各自在库内**证伪/降级**了既有条目。
这些条目此前**从无测试覆盖**，所以错误的断言能长期以 `VERIFIED` 存活。
本测试文件把三处修正钉死，防止回退。

三处修正：
  1. `attest_wenquan_dijing` —— **伪引文**。《帝京景物略》无「平地温泉如沸，冬月白气滃然，
     辽金帝王驻跸沐浴之所」一语。旧实现标 `VERIFIED`，等于让伪造证据升格为一手著录。
  2. `attest_baijiatuan_*` —— **过度断言**。旧实现把三段强度悬殊的说法
     （成村叙事 / 怡亲王祠 / 曹雪芹居留）捆在一条里标 `VERIFIED`，现已拆成三条分别定级。
  3. `era4_liao_jin.md` 的「西山八大水院今地对应」—— 除清水院有辽碑直证外
     全部是后世考释；旧对应「香水院＝温泉后山」已被《帝京景物略》断碑证据证伪。

Python 3.9.6 兼容: 禁 X | None, 禁 match.
"""
import pathlib

import pytest

from haidian_kg.extractor import HaidianCorpusExtractor

ROOT = pathlib.Path(__file__).resolve().parents[2]
CORPUS = ROOT / "haidian_kg" / "corpus" / "era4_liao_jin.md"

_KG = HaidianCorpusExtractor.extract_all()
_BY_ID = {a.id: a for a in _KG.place_attestations}


# ==================================================================
# 1. E28：伪引文必须降级
# ==================================================================

class TestWenquanFakeCitationGate:
    def test_fake_quote_not_verified(self):
        a = _BY_ID["attest_wenquan_dijing"]
        assert a.epistemic_status.name == "DISPROVEN", \
            "🔴 《帝京景物略》无此句，伪引文必须 DISPROVEN；回退到 VERIFIED 即为" \
            "「让伪造证据升格为一手著录」"

    def test_fake_quote_text_preserved_for_audit(self):
        """证伪不等于删证——原文必须保留以便审计与观众对照。"""
        a = _BY_ID["attest_wenquan_dijing"]
        assert "平地温泉如沸" in a.quote, \
            "被证伪的伪引文必须原样保留（供 P6 证伪页与审计对照），不得静默删除"

    def test_no_liaojin_emperor_bathing_claim_in_kg(self):
        """「辽金帝王驻跸沐浴」无一手书证，库内不得有 VERIFIED 版本。

        🔴 判据设计教训（E28 实施时踩到）：不能用裸关键词「沐浴」全表扫——
        `attest_xiangshan_jinshi`（香山大永安寺）的合法引文里就有「沐浴」，
        与温泉无关。必须**同时限定「驻跸」或「辽金」**。
        """
        for a in _KG.place_attestations:
            if a.toponym_id != "top_wenquan":
                continue  # 只查温泉名下条目
            if "驻跸" in a.quote or "辽金" in a.quote:
                assert a.epistemic_status.name != "VERIFIED", \
                    "🔴 「辽金帝王驻跸沐浴」无一手书证，%s 不得标 VERIFIED" % a.id


# ==================================================================
# 2. E27：混合断言必须拆分定级
# ==================================================================

class TestBaijiatuanClaimDecompositionGate:
    def test_three_claims_are_separate(self):
        for aid in ("attest_baijiatuan_founding",
                    "attest_baijiatuan_yixianqin",
                    "attest_baijiatuan_caoxueqin"):
            assert aid in _BY_ID, "E27 要求把三条强度悬殊的断言拆开建模，缺 %s" % aid

    def test_founding_claim_is_contested_not_verified(self):
        """成村叙事三说并存（辽金 / 明洪武屯田 / 无定向书证），不得定案。"""
        a = _BY_ID["attest_baijiatuan_founding"]
        assert a.epistemic_status.name == "CONTESTED", \
            "成村诸说并存无定向书证，必须 CONTESTED（定案即伪断言）"
        assert a.evidence_level.name == "L5_FOLK_LEGEND", \
            "成村叙事属传说层，证据级应为 L5"

    def test_yixianqin_stele_is_verified_l1(self):
        """怡贤亲王祠残碑碑额是 L1 实物，可作 VERIFIED。"""
        a = _BY_ID["attest_baijiatuan_yixianqin"]
        assert a.epistemic_status.name == "VERIFIED"
        assert a.evidence_level.name == "L1_ARCHAEOLOGICAL", \
            "残碑碑额是金石实物，须标 L1"

    def test_caoxueqin_claim_is_contested(self):
        """曹雪芹居留：唯一书证为无原件过录本，属学术假说，禁写「定居/终老」。"""
        a = _BY_ID["attest_baijiatuan_caoxueqin"]
        assert a.epistemic_status.name == "CONTESTED", \
            "曹雪芹白家疃居留仅有文献引述、无第一手档案支持，不得 VERIFIED"
        # 🔴 判据设计教训：禁词检查不能把否定式「非定居」也算命中。
        #    正确做法是先剥掉否定式，再查剩余部分是否还有裸的「定居」。
        stripped = a.quote.replace("非定居", "").replace("非终老", "")
        for wrong in ("定居", "终老", "晚年长期居住"):
            assert wrong not in stripped, \
                "🔴 禁写「定居/终老」：%s 出现在肯定语境（%r）" % (wrong, a.quote)
        assert "非定居" in a.quote, "必须显式标注「非定居」"


# ==================================================================
# 3. E28：八大水院今地对应必须降级
# ==================================================================

class TestEightWaterCourtsGate:
    def test_corpus_file_exists(self):
        assert CORPUS.exists(), "找不到 %s" % CORPUS

    def test_xiangshuiyuan_mapping_falsified(self):
        """🔴 「香水院＝温泉后山」已被《帝京景物略》断碑证据证伪。"""
        txt = CORPUS.read_text(encoding="utf-8")
        assert "香水院（今海淀温泉镇温泉后山）" not in txt, \
            "🔴 旧对应「香水院＝温泉后山」已证伪（《帝京景物略》记断碑在妙高峰法云寺）"
        assert "妙高峰" in txt, "须写明香水院断碑在妙高峰法云寺"

    def test_only_qingshuiyuan_is_verified(self):
        """除清水院＝大觉寺有辽碑直证外，今地对应全部是后世考释。"""
        txt = CORPUS.read_text(encoding="utf-8")
        assert "除清水院外 `UNSUBSTANTIATED`" in txt or \
               "除清水院外 UNSUBSTANTIATED" in txt, \
            "须显式声明：除清水院（辽碑直证）外，今地对应均为通行考释"

    def test_court_count_dispute_recorded(self):
        """诸本对水院数目不一致（《帝京景物略》作「六院」）。"""
        txt = CORPUS.read_text(encoding="utf-8")
        assert "六院" in txt, "须记载数目诸说并存（《帝京景物略》作「六院」）"

    def test_whole_section_not_plainly_verified(self):
        """🔴 回归：整段不得再无条件标 VERIFIED。"""
        txt = CORPUS.read_text(encoding="utf-8")
        i = txt.find("西山八大水院")
        assert i > 0
        seg = txt[i:i + 2200]
        assert seg.count("UNSUBSTANTIATED") >= 1, \
            "八大水院段须含 UNSUBSTANTIATED 降级声明"


# ==================================================================
# 4. 元纪律：DISPROVEN 条目必须带可审计的理由
# ==================================================================

class TestDisprovenAuditabilityGate:
    def test_disproven_entries_have_source_recorded(self):
        """被证伪的条目仍须记录出处与年代，否则无法审计。"""
        for a in _KG.place_attestations:
            if a.epistemic_status.name == "DISPROVEN":
                assert a.source_title, "DISPROVEN 条目 %s 缺 source_title，无法审计" % a.id
                assert a.recorded_year, "DISPROVEN 条目 %s 缺 recorded_year" % a.id

    def test_every_attest_has_evidence_level(self):
        for a in _KG.place_attestations:
            assert a.evidence_level is not None, "attest %s 缺 evidence_level" % a.id
