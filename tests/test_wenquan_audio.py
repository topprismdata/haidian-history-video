# -*- coding: utf-8 -*-
"""E28《温泉·「温泉」之前叫「石窝」》旁白文本与音频流水线测试."""
import json
import pathlib
import re
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from qa_v2.normalize import extract_numbers

ROOT = pathlib.Path(__file__).resolve().parents[1]
NARR_FILE = ROOT / "wenquan_video" / "narration" / "all.json"
AUDIO_DIR = pathlib.Path("/tmp/chemistry-video/public/audio/wenquan")
CFG_FILE = ROOT / "remotion-template" / "src" / "wenquan" / "data" / "pages.config.ts"


def _narration():
    return json.loads(NARR_FILE.read_text(encoding="utf-8"))


def _cfg():
    from qa_v2.data import parse_pages_config
    return parse_pages_config(CFG_FILE.read_text(encoding="utf-8"))


# ==================================================================
# 1. 基本完整性
# ==================================================================

class TestNarrationBasic:
    def test_eight_segments(self):
        n = _narration()
        assert sorted(n.keys()) == [f"p{i:02d}" for i in range(1, 9)]
        for k, v in n.items():
            assert 130 <= len(v) <= 190, "%s 字数 %d 越界（130-190）" % (k, len(v))

    def test_no_ascii_digits(self):
        """旁白禁阿拉伯数字（含公历年与编号）——编号只在屏显白名单。"""
        for k, v in _narration().items():
            bad = re.findall(r"[0-9]", v)
            assert not bad, f"{k} 口播含阿拉伯数字: {bad}"

    def test_no_ideographic_zero(self):
        for k, v in _narration().items():
            assert "\u3007" not in v, f"{k} 口播含 U+3007"

    def test_audio_files_exist(self):
        for i in range(1, 9):
            p = AUDIO_DIR / f"p{i:02d}.wav"
            assert p.exists(), "缺少音频 %s（先跑 gen_tts_wenquan.sh）" % p
            assert p.stat().st_size > 10000, f"{p.name} 疑似空音频"

    def test_durations_json_matches_audio(self):
        import subprocess
        dur_file = ROOT / "wenquan_video" / "narration" / "durations.json"
        assert dur_file.exists(), "缺 durations.json（先跑 build_remotion_data.py）"
        d = json.loads(dur_file.read_text(encoding="utf-8"))
        assert sorted(d.keys()) == [f"p{i:02d}" for i in range(1, 9)]
        for k in d:
            out = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "csv=p=0", str(AUDIO_DIR / f"{k}.wav")],
                capture_output=True, text=True, check=True).stdout.strip()
            assert abs(float(out) - d[k]) < 0.2, f"{k} durations.json 与实测偏差过大"


# ==================================================================
# 2. 屏显数字 ⊆ 口播数字（E13 纪律：两侧同一函数）
# ==================================================================

class TestScreenNumbersInNarration:
    def test_screen_numbers_are_subset_of_spoken(self):
        cfg = _cfg()
        narr = _narration()
        spoken = {int(k[1:]): set(extract_numbers(v)) for k, v in narr.items()}
        for pno in range(1, 9):
            screen = set()
            for it in cfg[pno]:
                if it.kind == "photo":
                    continue
                t = it.text
                for c in ("7-1973-3-009", "6-886", "6-810"):
                    t = t.replace(c, " ")
                screen |= set(extract_numbers(t))
            excess = screen - spoken[pno]
            assert not excess, f"P{pno} 屏显多出口播没有的数字: {sorted(excess)}"


# ==================================================================
# 3. V-NC01 核心叙事：石窝 → 温泉，改名不系年
# ==================================================================

class TestVNC01Narration:
    def test_shiwo_spoken(self):
        n = _narration()
        assert "石窝村" in n["p01"] and "采石场" in n["p01"], "P1 必须埋「石窝村＝采石场」钩子"
        assert "石窝村" in n["p04"], "P4 必须念出《宛署杂记》石窝村"
        assert "仍是石窝村" in n["p04"], "P4 必须点明万历官书正式村名仍是石窝村"

    def test_no_ancient_claim(self):
        blob = json.dumps(_narration(), ensure_ascii=False)
        for bad in ("自古", "村名与泉同龄"):
            assert bad not in blob, f"V-NC01 违规：口播出现「{bad}」"

    def test_no_rename_year(self):
        blob = json.dumps(_narration(), ensure_ascii=False)
        for bad in ("由石窝村改称", "改称温泉村", "改名温泉村"):
            assert bad not in blob, f"V-NC01 违规：口播把改名系于某年「{bad}」"

    def test_wanshu_verbatim_spoken(self):
        n = _narration()
        for frag in ("温泉堂", "离城五十里", "堂子山", "下有温泉",
                     "正德甲戌", "谷太监", "因名", "陈天祥"):
            assert frag in n["p04"], f"P4 口播缺《宛署杂记》逐字要素「{frag}」"

    def test_zhengde_ganzhi_with_year(self):
        n = _narration()
        assert "正德甲戌" in n["p04"] and "一五一四" in n["p04"], (
            "P4 干支与全字形纪年必须同念（闸门①口径）"
        )


# ==================================================================
# 4. V-NC03 伪引文只在证伪语境
# ==================================================================

class TestVNC03Narration:
    def test_fake_quote_only_in_p6_with_rejection(self):
        n = _narration()
        hits = [k for k, v in n.items() if "沐浴之所" in v]
        assert hits == ["p06"], "伪句只准出现在 P6"
        assert "没有这句" in n["p06"], "P6 必须显式说「没有这句」"

    def test_original_quote_spoken(self):
        n = _narration()
        # 口播引文按原刻字形（溫泉出焉），与 P6 原文卡逐字同形。
        assert "山北十里" in n["p06"] and "溫泉出焉" in n["p06"], "P6 必须念出原文"

    def test_xiangshuiyuan_refuted(self):
        n = _narration()
        assert "香水院" in n["p06"] and "妙高峰" in n["p06"], (
            "V-NC04：香水院必须在 P6 被锚定到妙高峰"
        )

    def test_ming_start_spoken(self):
        assert "从明代开始" in _narration()["p06"], "P6 必须落「文字史从明代开始」"


# ==================================================================
# 5. V-NC06 泉眼现状双禁 + 黑龙潭归属
# ==================================================================

class TestVNC06Narration:
    def test_double_ban_in_p8(self):
        n = _narration()
        assert "未考得" in n["p08"], "P8 必须说「未考得」"
        assert "不说它仍在涌流" in n["p08"], "P8 必须显式否认「仍在涌流」断言"
        assert "也不说它早已干涸" in n["p08"], "P8 必须显式否认「早已干涸」断言"

    def test_heilongtan_attributed(self):
        n = _narration()
        i = n["p08"].index("不盈尺")
        assert "黑龙潭" in n["p08"][max(0, i - 30):i], "「不盈尺」前文必须点名黑龙潭"


# ==================================================================
# 6. 祈/浴分层 + 关键名物
# ==================================================================

class TestKeyFacts:
    def test_pray_bath_separation_spoken(self):
        n = _narration()
        assert "龙王庙求雨" in n["p05"] and "温泉堂沐浴" in n["p05"]
        assert "一个祈一个浴, 两眼泉两座庙" in n["p05"], "P5 必须念出祈/浴分属两泉"

    def test_legend_not_fact(self):
        n = _narration()
        assert "八十八岁" in n["p05"] and "传说" in n["p05"], "乾隆八十八岁必须标传说"

    def test_guobao_batches_spoken(self):
        n = _narration()
        assert "第六批国保" in n["p08"] and "二零零六" in n["p08"]
        assert "一九八四" in n["p08"] and "第三批" in n["p08"]
        assert "第七批" in n["p08"] and "大运河" in n["p08"]

    def test_xianshilong_three_layers(self):
        n = _narration()
        for frag in ("水流云在", "英敛之", "民国二年", "宣统退位次年",
                     "一九三一", "滦州起义纪念园", "精神不死", "浩气长存",
                     "民国二十五年十一月"):
            assert frag in n["p07"], f"P7 口播缺「{frag}」"

    def test_dijing_quote_spoken_p2(self):
        n = _narration()
        for frag in ("崇祯八年", "帝京景物略", "山北十里", "温泉出焉",
                     "汤未至沸", "甃而为池", "以待浴者", "大汤山", "小汤山"):
            assert frag in n["p02"], f"P2 口播缺《帝京景物略》要素「{frag}」"

    def test_quarrying_spoken_p3(self):
        n = _narration()
        for frag in ("洪武二十七年", "一三九四", "正统十年", "一四四五",
                     "采石匠", "五十一年", "两百年"):
            assert frag in n["p03"], f"P3 口播缺采石题记要素「{frag}」"

    def test_no_internal_markers(self):
        blob = json.dumps(_narration(), ensure_ascii=False)
        pat = re.compile(r"🔴|🟡|E2[0-9]|/tmp/|\.py|\.json|TODO|L[1-5]\b|MEC-|VEC-|§|知识库|研究档案")
        m = pat.search(blob)
        assert not m, f"口播含内审标记「{m.group(0)}」"
