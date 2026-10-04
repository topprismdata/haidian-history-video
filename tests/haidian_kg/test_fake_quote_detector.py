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
    # Q-010 结案：《元史》卷164 无「白家圈/石佛村」，无「西直门入城」，无「導瓮山泊」
    # （跨段拼接伪句：至元三十年赐名句被焊进至元二十八年上言）
    "过双塔、白家圈，出石佛村",
    "至西直门入城",
    "導瓮山泊",
    # Q-011 结案：「广源闸重修碑记」查无此碑；引文为现代概括体
    "广源闸者，长河上游巨闸也，通漕蓄水以济都城，乃元至元旧制",
    # Q-012 结案：《明史》卷20「萬壽」「壽寺」零命中，伪托本纪
    "万历五年三月，敕建万寿寺于都城西直门外高梁河畔，为圣母祝寿之所",
    # Q-013 结案：《宛署杂记》无「海甸在城西二十里」句（实文作「北海店」）；
    # 沈榜著《宛署杂记》不叫《宛平县志》，牛栏庄实文只有并列一句
    "海甸在城西二十里，平地泉涌，积水如淀",
    "宛平县城外西乡牛栏庄，地滨泉源，居民引水种稻",
    "为海淀园林之祖",
    # Q-014 结案：「五行百户为所」是残句讹文，典籍无此语
    "五行百户为所",
    # Q-015 结案：1983 年「京密引水渠沿线古水利工程勘察报告」查无此出版物
    "为全国唯一存世之白浮引水工程地面实物遗构",
    "全国唯一存世之郭守敬白浮引水工程古堰实体残段遗存",
    # Q-016 结案：《大清实录·世宗实录》无觉生寺赐名句（一手源是《敕建觉生寺碑》）
    "乃于都城西直门外高梁河北建寺，赐名觉生，设坛祈雨",
    # Q-017 结案：《御制诗三集》无苏州街联句（E12 冻结书证是《啸亭杂录》卷十）
    "水木依稀姑苏肆，市廛宛转入楼台",
    # Q-018 结案：安和桥额石「1781 御题+释义」三重伪（E2：转换时间与机制待考）
    "桥成，改木为石，额曰‘安和桥’，取安和景泰之义",
    # Q-019 结案：《北平地名通志》查无此书
    "安河桥在青龙桥东，因水流安恬、桥跨御河，俗名遂改作‘安河桥’",
    # Q-021 结案：《日下旧闻考》青龙桥「石闸下注通惠河」——卷次错(实为卷100)
    # + 水文方向错（青龙桥闸是昆明湖溢洪尾闾，汛期北泄清河，与通惠河不同系）
    "青龙桥在玉泉山之阴，跨长河水，石闸下注通惠河，水陆要冲，商旅云集",
    # Q-022 结案：《清高宗御制文二集》一亩园「仿先农坛躬耕籍田」伪
    # （E5 红线：❌一亩园≠亲耕耤田，真正的耤田礼在先农坛）
    "圆明园前置一亩园，仿先农坛躬耕籍田之礼，以示重本抑末",
    # Q-023 结案：政务院文委 1953「选定中关村为科研基地」批复公文查无此件
    "政务院批准文委与科学院关于选定海淀中关村为科研基地的方案，近代第一座科学城破土动工",
    # Q-024 结案：《北京历代太监墓石刻考》系年1900（现代机构出版于清末，纪年自证其伪）
    "中官村地多太监兆域，内廷诸中官合祀刚炳为神，建祠村东，置义地数百亩",
    # R7 结案：1913《京西图》只零星出现「中关」，不得写成已标绘「中关村」并取代中官村
    "海淀镇东二里图注标绘‘中关村’，明确标注为村落民居聚落",
    # R6 结案：《日下旧闻考》卷99「赐名大有庄」伪（官书在卷100且无赐名情节）
    "大有庄旧名穷八家，高宗纯皇帝临幸，以其名不协吉卜，赐名大有庄",
    # R2 结案：外火器营「营房四千（余）间」查无实据（E10 冻结：只报分项，不给总数）
    "建满蒙八旗营房四千余间",
    "建满蒙八旗营房四千间",
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
    # 🔴 E26 实测教训：判死留档的表述远不止「原引」一种。本次实测到
    #    「原写……」「《X》无此句」「字字不符」「降 L4 或删」等写法，
    #    之前一律误报。这是「判据问错了问题」的第三例。
    _QUARANTINE_MARKERS = (
        "🔴", "已判死", "已结案", "系伪引文", "原引",
        "原写", "无此句", "字字不符", "降 L", "判死",
        "查无", "伪引文", "非原文", "对不上", "实文",
    )

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


class TestGateIsNotTautological:
    """🔴 负控制：证明上面的判据**不是恒真的**。

    一组「全绿」的判据，输出上无法区分三件事：判据对 / 判据恒真 / 判据在测别的东西。
    本类把 DEAD_VERBATIM 逐条**反向输入**给判据逻辑本身（纯字符串层，不碰真实文件），
    要求每条都真的被命中；同时要求 DISPROVEN 检测在**干净条目**上不误报。

    纪律来源：`skill://detector-needs-negative-control`。
    """

    def test_every_dead_entry_is_actually_reachable(self):
        """每条 DEAD_VERBATIM 至少含一个非空白字符，且互不重复。

        空串会让 `q in line` **恒真** → 判据对任何 corpus 行都「命中」，
        反而在豁免逻辑下变成永不报错的空转；重复条目会让计数虚高。
        """
        for q in DEAD_VERBATIM:
            assert isinstance(q, str), "DEAD_VERBATIM 必须全是字符串"
            assert q.strip(), "🔴 DEAD_VERBATIM 混入空串：`%s in line` 恒真，判据空转" % q
        assert len(set(DEAD_VERBATIM)) == len(DEAD_VERBATIM), (
            "DEAD_VERBATIM 有重复项，会让计数虚高、掩盖真实条目"
        )

    def test_detector_fires_when_dead_quote_resurrects(self):
        """负控制正向：构造「伪引文以采信身份复活」的场景，判据必须报出。

        🔴 这不是假设性检查——Q-001（廉希宪传）在 calibration 层已判死、
        corpus 层却仍 VERIFIED 的历史，正是本判据要抓的对象。
        """
        marker = "中统元年赴开平，三月五日发燕京"  # 无判死标记的上下文行
        resurrected = marker + "\n" + "引昌平县白浮村神山泉，过双塔、白家圈，出石佛村"
        markers = TestNoDeadVerbatimResurrection._QUARANTINE_MARKERS
        hits = []
        lines = resurrected.splitlines()
        for i, line in enumerate(lines):
            for q in DEAD_VERBATIM:
                if q not in line:
                    continue
                if any(mk in line for mk in markers):
                    continue
                ctx = "\n".join(lines[max(0, i - 2):i + 1])
                if any(mk in ctx for mk in markers):
                    continue
                hits.append(q)
        assert hits, (
            "🔴 判据恒真：把已判死伪句放回 corpus（且无判死标记）竟然零命中，"
            "说明 DEAD_VERBATIM 与判据逻辑脱节，闸门形同虚设"
        )

    def test_disproven_detector_not_tautological(self):
        """负控制反向：判死留档行**有**标记时应被豁免——豁免与命中两条路都得会走。

        「挪不动 ≠ 恒真」：若豁免路径恒不触发，本判据就退化成
        「伪引文一律不得出现」，那会逼后人删证文，违反「证伪不等于删证」。
        """
        markers = TestNoDeadVerbatimResurrection._QUARANTINE_MARKERS
        line = "🔴 本条原引《宛署杂记》「海甸在城西二十里，平地泉涌，积水如淀」系伪造"
        exempted = any(mk in line for mk in markers)
        assert exempted, (
            "🔴 判死留档行未被豁免 —— 判据退化为「伪引文一律不得出现」，"
            "会逼后人删除证伪所需的原文（证伪不等于删证）"
        )
        # 反向：同样一句话去掉标记后必须被命中，否则豁免标记成了万能免死金牌
        bare = line.replace("🔴", "").replace("原引", "").replace("系伪造", "")
        bare_hits = [q for q in DEAD_VERBATIM if q in bare]
        assert bare_hits, (
            "🔴 去掉判死标记后判据仍不命中 —— 豁免标记形同万能免死金牌，"
            "任何人只要打一个标记就能让伪引文复活"
        )


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


# ==================================================================
# 🔴 E28 回归：L4-a 标识符豁免（编号 ≠ 数量）
# ==================================================================

class TestIdentifierExemptionGate:
    """国保编号（6-886 / 7-1973-3-009）是标识符不是数量。

    事故：编号上屏被 extract_numbers 拆成数量并要求口播念出，
    实现者被迫删编号卡（FinalizeE28），用删除证据的方式通过 L4-c ——
    违反 V-NC05（编号必须同卡附批次与公布年）。修复=_IDENTIFIER_RE 豁免。
    本类验证豁免的精确边界。
    """

    def test_identifiers_stripped(self):
        from qa_v2.checks_content import _IDENTIFIER_RE as R
        assert R.sub(" ", "编号 6-886（近现代）").strip() == "编号  （近现代）"
        assert R.sub(" ", "7-1973-3-009").strip() == ""
        assert R.sub(" ", "5-205").strip() == ""

    def test_quantities_not_stripped(self):
        from qa_v2.checks_content import _IDENTIFIER_RE as R
        for txt in ("雍正十二年（一七三四）", "长约五米", "一九四三年过录本", "户二万七百四十"):
            assert R.sub(" ", txt) == txt, "数量类数字不得被当标识符剥离：%r" % txt

    def test_l4a_exempt_behavior_via_extraction(self):
        """行为级验证：编号剥离后无数字可查（放行），数量照常抽出（仍被抓）。

        与 qa_v2.checks_content.check_l4a 的实际用法一致：
        want = extract_numbers(_IDENTIFIER_RE.sub(" ", screen_text))。
        """
        from qa_v2.checks_content import _IDENTIFIER_RE
        from qa_v2.normalize import extract_numbers

        # 编号上屏（P8 卡）：886 被剥离 → 不再要求口播念「八八六」。
        # 残留的 [6] 来自「第六批」——口播必念「第六批」，子集自然成立（E26 同款）。
        card = "第六批，编号 6-886（近现代重要史迹）"
        got = extract_numbers(_IDENTIFIER_RE.sub(" ", card))
        assert 886 not in got, "🔴 编号 886 未被剥离"
        assert got == [6], "残留应仅有「第六批」的 6，实际 %s" % got

        # 🔴 负控制：同一位置的「数量」写法必须照常抽出（豁免不过宽）
        # 数量照常抽出（接受比对）——12.2 被抽成 [12, 2] 是 extract 的既有粒度
        assert extract_numbers(_IDENTIFIER_RE.sub(" ", "通高 12.2 米")) == [12, 2]
        assert extract_numbers(_IDENTIFIER_RE.sub(" ", "编号 6886")) == [6886]
        assert extract_numbers(_IDENTIFIER_RE.sub(" ", "营房四千间")) == [4000]
