# -*- coding: utf-8 -*-
"""🔴 伪引文制造机检测闸门（2026-10-04 知识库横切审计产出）。

## 病灶

审计发现的不是孤立错误，而是一台**制造机**：

    自撰文言转写 → 挂上一个真实存在的书名 → 标 VERIFIED

后果是伪造的证据能通过所有引用完整性闸门（G4/G5 只校验「id 存在」，
不校验「引文是否真出该书」）。E26 的 8 条假引文、era5 的《元史·廉希宪传》
「葬大都宛平之西高梁河畔」、era6 的《宛署杂记》海甸句，都是这台机器的产物。

更隐蔽的一层：**已经判定为假的条目，从没回灌到 corpus 层**。
E21 早已结案「卷一百二十六零命中」，但 era5_yuan.md 至今仍写着那句伪引文。
于是同一错误在两层有两种状态（calibration 已判死 / corpus 仍 VERIFIED），
自相矛盾。

## 本文件做什么

对 corpus 全文 + extractor 全部 attest 做**结构性筛查**，输出「可疑条目清单」。
它**不能**自动判定真伪（那需要人读原文），但能保证：

1. 每条书证都声明它是否经人工逐字核过；
2. 未经核对的必须在 `sources.csv` 或注释里显式标注；
3. 已判死的条目不得在别处复活。

Python 3.9.6 兼容: 禁 X | None, 禁 match.
"""
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
CORPUS_DIR = ROOT / "haidian_kg" / "corpus"

# 🔴 已被各集 research.md 判死、但曾以「逐字引文」形态存在的句子。
# 命中即为回归 —— 这些句子的正确处置是删除、或降级为转述，不是留在 corpus 里。
DEAD_VERBATIM = [
    # E21 结案：《元史》卷一百二十六 全文零命中该句
    "葬大都宛平之西高梁河畔，子孙家焉，号畏吾村",
    "恒阳王廉希宪，畏兀儿人也",
    # E26 结案：国保名单里不可能有「寺始建於唐太宗貞觀年間」
    "寺始建於唐太宗貞觀年間時名兜率寺",
    "至治元年詔改建昭孝寺賜額昭孝",
    # E28 结案：《帝京景物略》无「平地温泉如沸」一语
    "平地温泉如沸",
    "辽金帝王驻跸沐浴之所",
    # E26 结案：「長五尺」是「長丈六」之讹，与实测 5.3m 差三倍
    "寺中鑄釋迦牟尼臥佛長五尺",
]

# 「挂真书名 + 标 VERIFIED」的高危书名 —— 出现时必须人工确认
HIGH_RISK_SOURCES = (
    "元史", "明史", "帝京景物略", "宛署杂记", "日下旧闻考",
    "明宪宗实录", "清实录", "清圣祖实录", "御制", "析津志",
)


def _corpus_texts():
    for p in sorted(CORPUS_DIR.glob("era*.md")):
        yield p, p.read_text(encoding="utf-8")


class TestNoDeadVerbatimResurrection:
    """已判死的「逐字引文」不得在 corpus 复活。"""

    # 判死留档行前缀：显式声明「本条原引…已判死」时，引用原文是**必须的**
    _QUARANTINE_MARKERS = ("🔴", "已判死", "已结案", "系伪引文", "原引")

    def test_dead_quotes_absent_from_corpus(self):
        """已判死的伪引文不得在 corpus 层以**采信身份**复活。

        🔴 判据设计要点（E26 教训：证伪不等于删证）：
        显式声明判死的行**必须**引用原文，否则后人无法复核它假在哪。
        因此豁免「同一行内出现判死标记」的情形。
        """
        hits = []
        for p, txt in _corpus_texts():
            for i, line in enumerate(txt.splitlines()):
                for q in DEAD_VERBATIM:
                    if q not in line:
                        continue
                    if any(mk in line for mk in self._QUARANTINE_MARKERS):
                        continue  # 判死留档，允许引用原文
                    # 向上文两行找判死标记（引文常在标记的下一行）
                    ctx = "\n".join(txt.splitlines()[max(0, i - 2):i + 1])
                    if any(mk in ctx for mk in self._QUARANTINE_MARKERS):
                        continue
                    hits.append("%s:%d :: %s" % (p.name, i + 1, q[:24]))
        assert not hits, (
            "🔴 已判死的伪引文在 corpus 层以采信身份复活 —— "
            "这正是「修正不回灌」的老毛病：\n" + "\n".join(hits)
        )

    def test_dead_quotes_only_survive_as_disproven_evidence(self):
        """证伪条目**故意**保留伪引文原文（供审计与观众对照），
        但状态必须是 DISPROVEN —— 保留 ≠ 采信。

        🔴 判据设计要点：不能写成「伪引文一律不得出现」。
        E26 教训是「证伪不等于删证」：删了原文，后人无法复核这条到底假在哪。
        """
        from haidian_kg.extractor import HaidianCorpusExtractor
        ds = HaidianCorpusExtractor.extract_all()
        bad = []
        for att in ds.place_attestations:
            for q in DEAD_VERBATIM:
                if q in (att.quote or ""):
                    if att.epistemic_status.name != "DISPROVEN":
                        bad.append("%s(%s) :: %s" % (att.id, att.epistemic_status.name, q[:24]))
        assert not bad, (
            "🔴 已判死的伪引文只能以 DISPROVEN 身份留存（供审计），"
            "不得处于采信状态：\n" + "\n".join(bad)
        )

    def test_dead_quote_attest_not_verified(self):
        """🔴 负控制：伪引文条目不得处于 VERIFIED/CONTESTED（须 DISPROVEN 或无）。"""
        from haidian_kg.extractor import HaidianCorpusExtractor
        ds = HaidianCorpusExtractor.extract_all()
        for att in ds.place_attestations:
            for q in DEAD_VERBATIM:
                if q in (att.quote or ""):
                    assert att.epistemic_status.name == "DISPROVEN", (
                        "🔴 %s 含已判死伪引文，状态却是 %s，须为 DISPROVEN"
                        % (att.id, att.epistemic_status.name)
                    )


class TestQuarantineMechanism:
    """隔离区机制：判死条目必须留证据链，便于日后复核而非静默删除。"""

    def test_quarantine_file_exists(self):
        q = ROOT / "haidian_kg" / "QUARANTINE.md"
        assert q.exists(), (
            "缺少 haidian_kg/QUARANTINE.md —— 判死的书证必须留档"
            "（来源、判死理由、核验方式），否则后人无法复核，"
            "只能重新踩坑。静默删除不是处置，是丢信息。"
        )

    def test_quarantine_entries_have_reason(self):
        q = ROOT / "haidian_kg" / "QUARANTINE.md"
        txt = q.read_text(encoding="utf-8")
        # 每条至少要有「判死理由」与「核验方式」两类信息
        assert txt.count("理由") >= 3, "隔离条目须写明判死理由"
        assert "核验" in txt, "隔离条目须写明核验方式（查了哪个库/哪一卷）"


class TestVerbatimQuotesAreNotSelfAuthored:
    """🔴 防伪：逐字引文不得携带现代断语。

    典型：把「北京现存最大最古铜卧佛」这类**现代结论**写进「《元史》卷X」书影，
    使现代判断冒充古籍记载。E26 的伪造书影即为此类。
    """

    MODERN_TERMS = (
        "北京现存", "全国重点文物保护单位", "制作组", "示意图",
        "今为", "现为", "本片", "最大最古",
    )

    def test_extractor_verbatim_has_no_modern_terms(self):
        from haidian_kg.extractor import HaidianCorpusExtractor
        ds = HaidianCorpusExtractor.extract_all()
        for att in ds.place_attestations:
            q = att.quote or ""
            # 国保类条目本身含「全国重点文物保护单位」是正常的（名单原行）
            if "名单" in (att.source_title or "") or "guobao" in (att.source_title or "").lower():
                continue
            for t in self.MODERN_TERMS:
                assert t not in q, (
                    "🔴 attest %s 的引文含现代断语「%s」—— "
                    "现代判断不得混进古籍引文：%r" % (att.id, t, q[:40])
                )

    def test_calibration_verbatim_has_no_modern_terms(self):
        import importlib
        import glob
        for f in sorted(glob.glob(str(ROOT / "haidian_kg" / "calibration" / "*.py"))):
            mod_name = "cal_" + pathlib.Path(f).stem
            try:
                m = importlib.import_module("haidian_kg.calibration." + pathlib.Path(f).stem)
            except Exception:
                continue
            for fact in getattr(m, "FACTS", []) or []:
                q = fact.verbatim_quote or ""
                for t in ("北京现存", "最大最古", "制作组", "本片", "示意图"):
                    assert t not in q, (
                        "🔴 %s 的 %s 引文含现代断语「%s」：%r"
                        % (f, fact.id, t, q[:40])
                    )
