# -*- coding: utf-8 -*-
"""E21《魏公村·高梁河畔的畏吾村》Task 4 验收——旁白 JSON、TTS 音频与三件套一致性。

红线依据:weigongcun_video/research.md + haidian_kg/calibration/weigongcun.py(Task1 直核):
  - 《元史》卷125/126/127 全文核验 **无「畏吾」字样**,葬地书证挂
    元明善《廉希宪神道碑》「葬于宛平之西原」(L3 转引) + 查礼《畏吾村考》守冢廉姓(L3);
    严禁口播断言《元史》直接写有「畏吾村」。
  - 「魏公村」得名必须并存「畏吾音转」与「魏国公爵号」双轨(V-NC02)。
  - 屏显核心数字 1280/1513/1915/1951/5-199 必须自然存在于口播(L4-c)。
三件套 = all.json / durations.json / narration.ts + subtitles.ts。
"""
import hashlib
import json
import pathlib
import re
import subprocess

import pytest

from qa_v2.normalize import extract_numbers

ROOT = pathlib.Path(__file__).resolve().parents[1]
NARR_DIR = ROOT / "weigongcun_video" / "narration"
AUDIO_DIR = pathlib.Path("/tmp/chemistry-video/public/audio/weigongcun")
REMOTION_DATA = pathlib.Path("/tmp/chemistry-video/src/weigongcun/data")
TEMPLATE_DATA = ROOT / "remotion-template" / "src" / "weigongcun" / "data"
PAGES = [f"p{i:02d}" for i in range(1, 9)]

_PUNCT = re.compile(r"[，。！？；：、—…·「」『』《》（）·\s]")


def _narration():
    return json.loads((NARR_DIR / "all.json").read_text(encoding="utf-8"))


def _durations():
    return json.loads((NARR_DIR / "durations.json").read_text(encoding="utf-8"))


def _ffprobe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out)


def _strip(text):
    return _PUNCT.sub("", text)


# ---------------------------------------------------------------- 旁白 JSON

def test_narration_json_has_8_nonempty_pages():
    data = _narration()
    assert sorted(data) == PAGES, "all.json 必须恰好是 p01–p08 八段"
    for k, v in data.items():
        assert isinstance(v, str) and len(_strip(v)) >= 80, f"{k} 文本过短"
        assert "\t" not in v, f"{k} 含制表符会破坏 TSV"


def test_redline_no_yuanshi_weiwucun_attribution():
    """Task1 直核铁案:《元史》卷126 无「畏吾」——伪引文一字不得入稿。"""
    data = _narration()
    text = "".join(data.values())
    # 伪引文「卒，葬大都宛平之西高梁河畔，子孙家焉，号畏吾村」是 DISPROVEN 节点
    for bad in ["号畏吾村", "子孙家焉", "葬大都宛平之西高梁河畔", "魏家村", "卫伍"]:
        assert bad not in text, f"红线禁词「{bad}」不得出现(《元史》无「畏吾」字样)"
    for k, v in data.items():
        if "元史" in v:
            assert "畏吾村" not in v, \
                f"{k} 同页并现「元史」与「畏吾村」= 伪归属断言"
    assert "元史" not in data["p03"], "P3 讲葬地书证,严禁再挂《元史》"


def test_burial_quote_uses_attested_stele_wording():
    """P3 葬地/村名书证必须用已溯源的一手字句(神道碑 L3 + 查礼《畏吾村考》 L3)。"""
    p03 = _narration()["p03"]
    assert "葬于宛平之西原" in p03, "P3 必须引用神道碑「葬于宛平之西原」"
    assert "守冢者亦廉姓" in p03, "P3 必须引用查礼「守冢者亦廉姓」"
    assert "高梁河" in p03, "P3 必须锚定高梁河畔"


def test_dual_track_naming_both_tracks_present():
    """V-NC02:「魏公」得名必须音转与爵位并存,严禁单一化。"""
    p05 = _narration()["p05"]
    assert "既合音转" in p05 and "又暗合魏国公" in p05, \
        "P5 必须使用「既合音转、又暗合魏国公爵号」并存句式"
    assert "畏兀村" in p05, "P5 异写必须用有书证的「畏兀村」(乔松年)"


def test_ming_page_quotes_dahuisi_and_lidongyang():
    """P4 明代书证:正德八年 1513 大慧寺 + 李东阳《怀麓堂集》祖茔字句。"""
    p04 = _narration()["p04"]
    assert "一五一三" in p04 or "正德八年" in p04
    assert "大慧寺" in p04 and "李东阳" in p04
    assert "葬曾祖考妣于畏吾村" in p04, "P4 必须引《怀麓堂集》「葬曾祖考妣于畏吾村」"
    assert "魏忠贤" in p04, "P4 必须存在对魏忠贤附会的反向驳斥"


def test_key_screen_numbers_spoken_l4c():
    """屏显核心数字必须自然念出(L4-c);口径与 qa_v2.normalize 完全一致。"""
    data = _narration()
    for page, want in [("p02", {1280}), ("p04", {1513, 5, 199}),
                       ("p06", {1915}), ("p07", {1951})]:
        got = set(extract_numbers(data[page]))
        assert want <= got, f"{page} 口播数字 {sorted(got)} 缺 {sorted(want)}"
    assert "至元十七年" in data["p02"], "P2 必须念至元十七年(=1280)"
    assert "五万分之一" in data["p06"], "P6 必须念五万分之一实测图比例尺"


def test_key_proper_nouns_spoken():
    data = _narration()
    assert "畏吾村" in data["p01"] and "魏公村" in data["p01"]
    assert "廉希宪" in data["p02"] and "魏国公" in data["p02"]
    assert "查礼" in data["p03"] and "畏吾村考" in data["p03"]
    assert "中央民族学院" in data["p07"] and "五十六个民族" in data["p07"]


# ---------------------------------------------------------------- 音频文件

def test_all_16_audio_files_present():
    for k in PAGES:
        canon = AUDIO_DIR / f"{k}.wav"
        alias = AUDIO_DIR / f"p{int(k[1:])}.wav"
        assert canon.exists() and canon.stat().st_size > 44100, \
            f"{canon} 缺失或过小"
        assert alias.exists() and alias.stat().st_size > 44100, \
            f"双文件名别名 {alias} 缺失(E19 经验:防 Remotion 404)"


def test_alias_bytes_identical_to_canonical():
    for k in PAGES:
        a = (AUDIO_DIR / f"{k}.wav").read_bytes()
        b = (AUDIO_DIR / f"p{int(k[1:])}.wav").read_bytes()
        assert hashlib.md5(a).hexdigest() == hashlib.md5(b).hexdigest(), \
            f"别名 {k[1:]}.wav 与 {k}.wav 内容不一致"


def test_each_audio_duration_gt_10s():
    for k in PAGES:
        d = _ffprobe_duration(AUDIO_DIR / f"{k}.wav")
        assert d > 10.0, f"{k} 时长 {d:.2f}s ≤ 10s"


def test_total_audio_between_180_and_250s():
    total = sum(_ffprobe_duration(AUDIO_DIR / f"{k}.wav") for k in PAGES)
    assert 180.0 <= total <= 250.0, f"总时长 {total:.1f}s 超出 180–250s"


# ---------------------------------------------------------------- 三件套一致

def test_durations_json_matches_measured():
    dur = _durations()
    assert sorted(dur) == PAGES
    for k in PAGES:
        measured = round(_ffprobe_duration(AUDIO_DIR / f"{k}.wav"), 2)
        assert abs(dur[k] - measured) <= 0.05, \
            f"{k}: durations.json={dur[k]} 实测={measured}"


def test_durations_json_mirrored_to_both_data_dirs():
    base = (NARR_DIR / "durations.json").read_bytes()
    for d in (REMOTION_DATA, TEMPLATE_DATA):
        assert (d / "durations.json").read_bytes() == base, \
            f"{d}/durations.json 与 narration/durations.json 不一致"


def test_narration_ts_in_sync_with_durations():
    src = (REMOTION_DATA / "narration.ts").read_text(encoding="utf-8")
    m = re.search(r"PAGE_AUDIO_SEC\s*=\s*\[([^\]]*)\]", src)
    assert m, "narration.ts 缺少 PAGE_AUDIO_SEC"
    secs = [float(x) for x in m.group(1).split(",")]
    assert secs == [round(_durations()[k], 2) for k in PAGES], \
        "narration.ts PAGE_AUDIO_SEC 与 durations.json 不一致"
    assert re.search(r"FPS\s*=\s*30", src), "FPS 必须为 30"
    assert "audioBeats" in src, "audioBeats 接口必须保留"


def _subtitles_data():
    src = (REMOTION_DATA / "subtitles.ts").read_text(encoding="utf-8")
    m = re.search(r"SUBTITLES[^=]*=\s*(\{.*\});\s*$", src, re.S)
    assert m, "subtitles.ts 缺少 SUBTITLES 数据块"
    return json.loads(m.group(1))


def test_subtitles_text_matches_narration():
    subs = _subtitles_data()
    assert sorted(subs) == [str(i) for i in range(1, 9)]
    narr = _narration()
    for i, k in enumerate(PAGES):
        joined = "".join(c["text"] for c in subs[str(i + 1)])
        assert _strip(joined) == _strip(narr[k]), \
            f"P{i + 1} 字幕连读与旁白文本不一致"


def test_subtitle_timing_fits_page_audio():
    subs = _subtitles_data()
    for i in range(1, 9):
        caps = subs[str(i)]
        assert caps, f"P{i} 字幕为空"
        audio = _durations()[f"p{i:02d}"]
        assert caps[0]["from"] == pytest.approx(0.0, abs=0.01)
        assert sum(c["dur"] for c in caps) == pytest.approx(audio, abs=0.06), \
            f"P{i} 字幕总时长应等于该页纯音频时长"
        assert caps[-1]["from"] + caps[-1]["dur"] <= audio + 0.06, \
            f"P{i} 字幕溢出页音频时长"
        for c in caps:
            assert c["dur"] > 0.2 and c["text"], f"P{i} 出现空/过短字幕行"


def test_remotion_template_synced():
    for name in ["narration.ts", "subtitles.ts", "durations.json"]:
        live = (REMOTION_DATA / name).read_bytes()
        mirror = (TEMPLATE_DATA / name).read_bytes()
        assert live == mirror, f"remotion-template/{name} 与 /tmp 副本不一致"
