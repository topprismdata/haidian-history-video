# -*- coding: utf-8 -*-
"""E29《郭守敬·一泉入都》旁白文本与音频流水线测试.

基线判据沿用 test_shifangpujue_audio.py，另加本集红线：
  V-NC02 口播禁「长河是郭守敬开的」，必须有「不是他开的」澄清；
  V-NC03 禁「泽被六百年/至今仍在供水」，必须有衰败链（不能通流＋湮没）；
  V-NC04 口播回归年须念原文刻分＋换算值（挂「据现代学者换算」）；
  V-NC06 「发明海拔」禁说，正表述「以海平面比较」；
  V-NC07 白浮泉在昌平不在海淀（口播必须显式「不在海淀」）；
  屏显纪律  旁白零 ASCII 数字（全字形汉字纪年）、零 U+3007。

🔴 音频时长判据为「条件激活」：E29 不在本轮跑 TTS（Main 统一串行执行），
   音频文件齐备前该判据 skip；齐备后自动生效（240-300s 承载区间）。

Python 3.9.6 兼容: 禁 X | None, 禁 match.
"""
import json
import pathlib
import re
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from qa_v2.normalize import extract_numbers

ROOT = pathlib.Path(__file__).resolve().parents[1]
NARR_FILE = ROOT / "guoshoujing_video" / "narration" / "all.json"
AUDIO_DIR = pathlib.Path("/tmp/chemistry-video/public/audio/guoshoujing")
CFG_FILE = ROOT / "remotion-template" / "src" / "guoshoujing" / "data" / "pages.config.ts"


def _narration():
    return json.loads(NARR_FILE.read_text(encoding="utf-8"))


def _cfg():
    from qa_v2.data import parse_pages_config
    return parse_pages_config(CFG_FILE.read_text(encoding="utf-8"))


def _blob():
    n = _narration()
    blob = " ".join(n.values())
    cfg = _cfg()
    blob += " ".join(it.text for items in cfg.values() for it in items)
    return blob


def _audio_ready():
    return all((AUDIO_DIR / ("p%02d.wav" % i)).exists() for i in range(1, 9))


# ==================================================================
# 1. 基本完整性
# ==================================================================

class TestNarrationBasic:
    def test_eight_segments(self):
        n = _narration()
        assert set(n.keys()) == {"p%02d" % i for i in range(1, 9)}, \
            "必须恰有 p01..p08，实际 %s" % sorted(n.keys())

    def test_segment_length_130_to_190(self):
        n = _narration()
        for k, v in n.items():
            assert 130 <= len(v) <= 190, "%s 字数 %d 超出 130-190 设计区间" % (k, len(v))

    def test_audio_duration_in_range(self):
        import wave
        if not _audio_ready():
            pytest.skip("E29 音频未生成（Main 统一串行跑 TTS），时长判据暂不激活")
        total = 0.0
        for i in range(1, 9):
            p = AUDIO_DIR / ("p%02d.wav" % i)
            with wave.open(str(p)) as w:
                total += w.getnframes() / float(w.getframerate())
        assert 240.0 <= total <= 300.0, "纯音频总时长 %.1fs 超出 240-300s 区间" % total


# ==================================================================
# 2. 屏显数字 ⊆ 口播数字（含 quote 槽，比 pages 测更严）
# ==================================================================

class TestScreenNumbersInNarration:
    def test_screen_numbers_are_subset_of_spoken(self):
        n = _narration()
        cfg = _cfg()
        MIN = 10
        for pno in sorted(cfg, key=int):
            spoken = set(extract_numbers(n["p%02d" % int(pno)]))
            for it in cfg[pno]:
                if not it.slot_id or "photo" in it.slot_id:
                    continue
                got = {v for v in extract_numbers(it.text) if v >= MIN}
                missing = got - spoken
                assert not missing, (
                    "P%s 槽位 %s 屏显数字 %s 未在当页口播念出（口播含 %s）"
                    % (pno, it.slot_id, sorted(missing), sorted(spoken))
                )


# ==================================================================
# 3. 屏显卫生：零 ASCII 数字 / 零 U+3007
# ==================================================================

class TestNarrationHygiene:
    def test_no_ascii_digits_in_narration(self):
        n = _narration()
        for k, v in n.items():
            assert not re.search(r"[0-9]", v), (
                "%s 旁白含 ASCII 数字（旁白纪年一律全字形汉字）" % k
            )

    def test_no_ideographic_zero(self):
        blob = _blob()
        assert "\u3007" not in blob, "U+3007 圆圈数字禁用（宋体不可见，OCR 漏读）"

    def test_full_char_years_spoken(self):
        n = " ".join(_narration().values())
        for y in ("一二三一年", "三百六十五日", "二十四刻二十五分", "三百六十五点二四二五"):
            assert y in n, "旁白缺少全字形纪年/数值「%s」" % y


# ==================================================================
# 4. 关键专名
# ==================================================================

class TestKeyProperNouns:
    def test_key_proper_nouns_spoken(self):
        n = " ".join(_narration().values())
        nouns = ["郭守敬", "白浮泉", "瓮山泊", "积水潭", "通惠河", "广源闸",
                 "授时历", "昌平", "海淀", "登封", "邢台", "大都"]
        missing = [w for w in nouns if w not in n]
        assert not missing, "口播缺少专名: %s" % missing

    def test_yuanshi_quote_spoken(self):
        n = " ".join(_narration().values())
        assert "西折而南" in n and "经瓮山泊" in n, "口播必须念出「西折而南，经瓮山泊」"
        assert "环汇于积水潭" in n, "口播必须念出「环汇于积水潭」"


# ==================================================================
# 5. V-NC02 长河非郭守敬所开
# ==================================================================

class TestChangheNotDugByGuo:
    def test_ban_dug_wording(self):
        blob = _blob()
        for wrong in ("开凿长河", "开挖长河", "郭守敬所开"):
            assert wrong not in blob, "V-NC02 违规：出现「%s」" % wrong

    def test_explicit_negation_spoken(self):
        n = " ".join(_narration().values())
        assert "长河不是他开的" in n, "口播必须显式澄清「长河不是他开的」"
        assert "比他老得多" in n, "口播必须给出「河道比他老」依据"

    def test_baifu_in_changping(self):
        n = " ".join(_narration().values())
        assert "白浮泉也从来不在海淀" in n, "V-NC07：口播必须显式「不在海淀」"
        assert "昌平龙山" in n, "口播必须给出白浮泉今址（昌平龙山）"


# ==================================================================
# 6. V-NC03 衰败链
# ==================================================================

class TestDecayChainSpoken:
    def test_ban_blessing_wording(self):
        blob = _blob()
        for wrong in ("泽被六百年", "泽被后世", "至今仍在供水"):
            assert wrong not in blob, "V-NC03 违规：出现「%s」" % wrong

    def test_decay_chain_spoken(self):
        n = " ".join(_narration().values())
        assert "不能通流" in n, "口播必须念出「不能通流」（延祐元年书证）"
        assert "湮没" in n, "口播必须念出「湮没」（乾隆己巳书证）"
        assert "大德十一年" in n and "三十多里" in n, "口播必须念出崩堤环节"
        assert "泉死得比人早" in n, "口播必须落到本集主轴句"

    def test_chief_died_after_silt(self):
        n = " ".join(_narration().values())
        assert "去世前两年" in n, "口播必须点明「郭守敬去世前两年」的时间差"


# ==================================================================
# 7. V-NC04 回归年
# ==================================================================

class TestRegressionYearSpoken:
    def test_verbatim_and_conversion_spoken(self):
        n = " ".join(_narration().values())
        assert "三百六十五日" in n and "二十四刻二十五分" in n, "口播必须念原文刻分"
        assert "三百六十五点二四二五日" in n, "口播必须念换算值"
        assert "据现代学者换算" in n, "换算必须挂「据现代学者换算」"

    def test_no_decimal_boast(self):
        blob = _blob()
        for wrong in ("精确到小数点", "小数点后四位"):
            assert wrong not in blob, "V-NC04 违规：出现「%s」" % wrong

    def test_banxing_same_year(self):
        n = " ".join(_narration().values())
        assert "就在这年冬天颁行天下" in n, "口播必须钉死「其年冬颁行」"


# ==================================================================
# 8. V-NC06 海拔表述
# ==================================================================

class TestHaibaSpoken:
    def test_positive_phrase_spoken(self):
        n = " ".join(_narration().values())
        assert "以海平面比较" in n, "口播必须给出「以海平面比较」正表述"

    def test_haiba_only_negated(self):
        blob = _blob()
        assert "发明了海拔" not in blob, "V-NC06 违规：「发明了海拔」任何语境禁用"
        for m in re.finditer("发明海拔", blob):
            pre = blob[max(0, m.start() - 2):m.start()]
            assert pre.endswith("不是"), (
                "V-NC06 违规：「发明海拔」出现在非否定语境：%r"
                % blob[max(0, m.start() - 12):m.start() + 8]
            )

    def test_thought_germ_framing(self):
        n = " ".join(_narration().values())
        assert "思想的萌芽" in n, "口播必须用「思想的萌芽」定性（非发明）"


# ==================================================================
# 9. V-NC05 二十七所
# ==================================================================

class TestSihai27Spoken:
    def test_27_stations_spoken(self):
        n = " ".join(_narration().values())
        assert "二十七个定点观测站" in n, "口播必须念「二十七个定点观测站」"
        assert "没有一个站设在今天的海淀" in n, "口播必须念「今海淀无站」"

    def test_no_whole_china_claim(self):
        n = " ".join(_narration().values())
        for wrong in ("测量了整个中国", "走遍西藏", "沿着长城测"):
            assert wrong not in n, "V-NC05 违规：口播出现「%s」" % wrong
