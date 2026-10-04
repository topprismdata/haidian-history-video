# -*- coding: utf-8 -*-
"""E26《十方普觉寺》旁白文本与音频流水线测试.

验证:
1. 8 段旁白齐全, 纯音频总时长在合理区间 (240-300s);
2. 屏显关键数字必须是口播数字的子集 (E24 教训的源头);
3. 关键专名必须口播;
4. V-NC02 铜卧佛元代所铸 —— 口播与屏显均不得写「唐代遗存」;
5. V-NC03 第五批国保 + 编号 5-205 —— 不得出现 1961 第一批口径;
6. V-NC05 寿安山南麓, 不得混写为香山;
7. V-NC04「Offer 寺」不入史。
"""
import json
import pathlib
import re
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from qa_v2.normalize import extract_numbers

ROOT = pathlib.Path(__file__).resolve().parents[1]
NARR_FILE = ROOT / "shifangpujue_video" / "narration" / "all.json"
AUDIO_DIR = pathlib.Path("/tmp/chemistry-video/public/audio/shifangpujue")
CFG_FILE = ROOT / "remotion-template" / "src" / "shifangpujue" / "data" / "pages.config.ts"


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


# ==================================================================
# 1. 基本完整性
# ==================================================================

class TestNarrationBasic:
    def test_eight_segments(self):
        n = _narration()
        assert set(n.keys()) == {"p%02d" % i for i in range(1, 9)}, \
            "必须恰有 p01..p08，实际 %s" % sorted(n.keys())

    def test_all_segments_non_trivial(self):
        n = _narration()
        for k, v in n.items():
            assert len(v) >= 100, "%s 太短（%d 字），撑不起一页" % (k, len(v))

    def test_audio_duration_in_range(self):
        import wave
        total = 0.0
        for i in range(1, 9):
            p = AUDIO_DIR / ("p%02d.wav" % i)
            assert p.exists(), "缺少音频 %s（先跑 gen_tts_shifangpujue.sh）" % p
            with wave.open(str(p)) as w:
                total += w.getnframes() / float(w.getframerate())
        assert 240.0 <= total <= 300.0, "纯音频总时长 %.1fs 超出 240-300s 区间" % total

    def test_single_page_not_exceeding_audio_length(self):
        """每页字数不得超页音频 15s 承载 (约 12 字/秒 → 180 字)。"""
        n = _narration()
        for k, v in n.items():
            assert len(v) <= 200, "%s 字数 %d 超单页承载上限" % (k, len(v))


# ==================================================================
# 2. 屏显数字 ⊆ 口播数字 (E24 教训的源头)
# ==================================================================

class TestScreenNumbersInNarration:
    def test_screen_numbers_are_subset_of_spoken(self):
        """🔴 E24 教训：屏显上的每一个数字都必须在该页口播里念出来。

        E24 因为屏显写 1068 而口播只念年号「一〇六八」，被判 fail。
        本条是第一道拦截。
        """
        n = _narration()
        cfg = _cfg()
        MIN = 10  # 只对纪年量级做子集判据
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
# 3. 关键专名
# ==================================================================

class TestKeyProperNouns:
    def test_six_names_spoken(self):
        """🔴 V-NC01：六个名号必须在口播中出现（屏显有不算数）。"""
        n = " ".join(_narration().values())
        for nm in ("兜率寺", "昭孝寺", "洪庆寺", "寿安山寺", "永安寺", "十方普觉寺"):
            assert nm in n, "口播缺少名号「%s」" % nm

    def test_key_proper_nouns_spoken(self):
        n = " ".join(_narration().values())
        nouns = ["卧佛寺", "寿安山", "国家植物园", "弥勒内院",
                 "释迦牟尼", "雍正", "正统", "成化", "至治"]
        missing = [w for w in nouns if w not in n]
        assert not missing, "口播缺少专名: %s" % missing

    def test_no_vague_wording_in_narration(self):
        n = " ".join(_narration().values())
        for vague in ("历经数次改名", "历经多次易名", "数次易名", "屡次改名"):
            assert vague not in n, "V-NC01 违规：口播出现笼统表述「%s」" % vague


# ==================================================================
# 4. V-NC02 器物年代 ≠ 建置年代
# ==================================================================

class TestArtifactAgeLayering:
    def test_wofoe_must_be_yuan_in_narration(self):
        blob = _blob()
        assert "元代" in blob or "元朝" in blob or "元至治元年" in blob, \
            "必须明确铜卧佛铸于元代"
        for wrong in ("唐代铜卧佛", "唐代遗存", "唐时铸", "唐代所铸"):
            assert wrong not in blob, "V-NC02 违规：出现「%s」" % wrong

    def test_temple_is_tang(self):
        n = " ".join(_narration().values())
        assert "贞观" in n, "必须写明寺创于唐贞观年间"

    def test_gap_explicitly_spoken(self):
        n = " ".join(_narration().values())
        assert "六百多年" in n or "六百余载" in n, "必须显式说出寺佛相隔年数"

    def test_cross_inference_forbidden_in_narration(self):
        n = " ".join(_narration().values())
        assert "反过" in n or "不能" in n, "必须显式禁止器物与建置年代互推"


# ==================================================================
# 5. V-NC03 国保批次与编号
# ==================================================================

class TestGuobaoBatch:
    def test_fifth_batch_and_number_spoken(self):
        """🔴 第五批国保必须口播编号 5-205。

        口播按 TTS 习惯念「五杠二零五」，屏显写「5-205」——
        两种写法都算过，两侧都不算才失败。
        """
        n = " ".join(_narration().values())
        assert "第五批" in n
        assert ("5-205" in n) or ("五杠二零五" in n), \
            "🔴 第五批国保必须口播编号（屏显 5-205 / 口播 五杠二零五）"

    def test_no_first_batch_numbering(self):
        blob = _blob()
        for wrong in ("1-75", "一批全国重点文物保护单位"):
            assert wrong not in blob, "🔴 1961 年首批口径严禁用于本寺：%s" % wrong

    def test_batch_date_spoken(self):
        n = " ".join(_narration().values())
        assert "二〇〇一年六月二十五日" in n or "2001" in n, "必须口播公布日期"

    def test_not_misplaced_to_first_batch(self):
        n = " ".join(_narration().values())
        # 「第一批」在本集只能作为 E25 对照出现，不得指本寺
        for m in re.finditer(r"第一批", n):
            ctx = n[max(0, m.start() - 12):m.start() + 12]
            assert "五塔寺" in ctx, \
                "「第一批」出现处须标明是 E25 五塔寺的对照语境，实际：%r" % ctx


# ==================================================================
# 6. V-NC04/V-NC05
# ==================================================================

class TestLocationAndFolkName:
    def test_shuoan_spoken(self):
        n = " ".join(_narration().values())
        assert "寿安山" in n, "必须口播寿安山"

    def test_not_in_xiangshan(self):
        n = " ".join(_narration().values())
        assert "不在香山" in n, "🔴 V-NC05：必须显式澄清不在香山"

    def test_offer_temple_banned(self):
        blob = _blob()
        assert "Offer" not in blob and "offer" not in blob, \
            "🔴 V-NC04：网络谐音严禁进入史实叙述"

    def test_caveat_spoken(self):
        n = " ".join(_narration().values())
        assert "不进寺史" in n or "不是寺的名字" in n, \
            "必须显式声明谐音不入寺史"
