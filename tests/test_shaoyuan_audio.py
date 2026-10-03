"""E20《勺园·淑春园·未名湖》Task 4 验收——旁白 JSON、TTS 音频与三件套一致性。

红线依据:shaoyuan_video/research.md v1.1 + GPT 闸门(gpt_review.txt E01-E12)。
三件套 = all.json / durations.json / narration.ts + subtitles.ts。
"""
import hashlib
import json
import pathlib
import re
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
NARR_DIR = ROOT / "shaoyuan_video" / "narration"
AUDIO_DIR = pathlib.Path("/tmp/chemistry-video/public/audio/shaoyuan")
REMOTION_DATA = pathlib.Path("/tmp/chemistry-video/src/shaoyuan/data")
TEMPLATE_DATA = ROOT / "remotion-template" / "src" / "shaoyuan" / "data"
PAGES = [f"p{i:02d}" for i in range(1, 9)]

_PUNCT = re.compile(r"[，。！？；：、—…·「」『』《》（）·\s]")


def _narration() -> dict:
    return json.loads((NARR_DIR / "all.json").read_text(encoding="utf-8"))


def _durations() -> dict:
    return json.loads((NARR_DIR / "durations.json").read_text(encoding="utf-8"))


def _ffprobe_duration(path: pathlib.Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out)


def _strip(text: str) -> str:
    return _PUNCT.sub("", text)


# ---------------------------------------------------------------- 旁白 JSON

def test_narration_json_has_8_nonempty_pages():
    data = _narration()
    assert sorted(data) == PAGES, "all.json 必须恰好是 p01–p08 八段"
    for k, v in data.items():
        assert isinstance(v, str) and len(_strip(v)) >= 80, f"{k} 文本过短"
        assert "\t" not in v, f"{k} 含制表符会破坏 TSV"


def test_redline_forbidden_phrases_absent():
    """GPT 闸门红线:己卯(1615=乙卯)/1030/1784/独资/钱穆命名独断。"""
    text = (NARR_DIR / "all.json").read_text(encoding="utf-8")
    for bad in ["己卯", "一千零三十", "一七八四", "1784", "独资",
                "钱穆命名", "钱穆首创"]:
        assert bad not in text, f"红线禁词「{bad}」不得出现"


def test_key_screen_numbers_spoken_l4c():
    """屏显关键数字必须自然念出(L4-c)。"""
    data = _narration()
    assert "一六一五" in data["p02"], "P2 必须念 1615"
    assert "一七九九" in data["p03"] and "一八〇一" in data["p03"], \
        "P3 双链年份必须念 1799/1801"
    assert "一千零三间" in data["p04"], "P4 抄档数字必须念 1003 间"
    assert "四十二" in data["p04"] and "六十四" in data["p04"], \
        "P4 楼台42/亭台64 必须分列念出"
    assert "一九二〇" in data["p06"], "P6 必须念 1920"
    assert "一九二八" in data["p07"] and "一九三一" in data["p07"], \
        "P7 必须念 1928/1931"
    assert "一九八二" in data["p08"] and "二〇〇一" in data["p08"], \
        "P8 必须念 1982/2001"


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
        b = (AUDIO_DIR / f"{k[1:]}.wav").read_bytes()
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


def test_narration_ts_in_sync_with_durations():
    src = (REMOTION_DATA / "narration.ts").read_text(encoding="utf-8")
    m = re.search(r"PAGE_AUDIO_SEC\s*=\s*\[([^\]]*)\]", src)
    assert m, "narration.ts 缺少 PAGE_AUDIO_SEC"
    secs = [float(x) for x in m.group(1).split(",")]
    assert secs == [round(_durations()[k], 2) for k in PAGES], \
        "narration.ts PAGE_AUDIO_SEC 与 durations.json 不一致"
    assert re.search(r"FPS\s*=\s*30", src), "FPS 必须为 30"
    assert "audioBeats" in src, "audioBeats 接口必须保留"


def _subtitles_data() -> dict:
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
        assert caps[-1]["from"] + caps[-1]["dur"] <= audio + 0.06
        for c in caps:
            assert c["dur"] > 0.2 and c["text"], f"P{i} 出现空/过短字幕行"


def test_remotion_template_synced():
    for name in ["narration.ts", "subtitles.ts"]:
        live = (REMOTION_DATA / name).read_bytes()
        mirror = (TEMPLATE_DATA / name).read_bytes()
        assert live == mirror, f"remotion-template/{name} 与 /tmp 副本不一致"
