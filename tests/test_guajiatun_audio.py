# -*- coding: utf-8 -*-
"""E23《挂甲屯·杨六郎传说与清初额驸城》Task 4: 旁白文本与音频流水线测试.

覆盖:
- all.json 8 页文本完整性与学术红线（杨六郎史实辨伪、额驸城档案实录）
- 关键屏显数字与专名在口播中念出 (L4-c / L4-b)
- 16 个音频文件就位 (p01..p08, p1..p8)
- 别名一致性与时长范围
- durations.json / narration.ts / subtitles.ts 镜像同步一致性
"""
import hashlib
import json
import pathlib
import re
import subprocess
import pytest

from qa_v2.normalize import extract_numbers

ROOT = pathlib.Path(__file__).resolve().parents[1]
NARR_DIR = ROOT / "guajiatun_video" / "narration"
AUDIO_DIR = pathlib.Path("/tmp/chemistry-video/public/audio/guajiatun")
REMOTION_DATA = pathlib.Path("/tmp/chemistry-video/src/guajiatun/data")
TEMPLATE_DATA = ROOT / "remotion-template" / "src" / "guajiatun" / "data"


def _narration():
    return json.loads((NARR_DIR / "all.json").read_text(encoding="utf-8"))


def _durations():
    return json.loads((NARR_DIR / "durations.json").read_text(encoding="utf-8"))


def _ffprobe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True).stdout.strip()
    return float(out)


def _strip(text):
    return re.sub(r"[\s,。?!;:、——?「」《》]", "", text)


def test_narration_json_has_8_nonempty_pages():
    data = _narration()
    assert len(data) == 8, f"必须刚好 8 页, 实际 {len(data)}"
    assert sorted(data.keys()) == [f"p{i:02d}" for i in range(1, 9)]
    for k, v in data.items():
        assert len(v.strip()) >= 50, f"{k} 文本过短"


def test_redline_yang_liulang_legend_is_folk_only():
    """杨六郎挂甲只能作民间传说引入, 严禁作史实断言 (V-NC01)."""
    data = _narration()
    p02 = data["p02"]
    assert "白沟河" in p02 or "河北三关" in p02
    assert "纯属后世说书评话" in p02 or "浪漫附会" in p02
    assert "从未曾踏足" in p02 or "未曾踏足" in p02


def test_redline_efucheng_ruins_not_preserved():
    """额驸城地面府第早已废毁, 严禁宣称完整保存 (V-NC03)."""
    data = _narration()
    p04 = data["p04"]
    assert "额驸城" in p04
    assert "荡平" in p04 or "早已" in p04
    assert "完整保存" not in "".join(data.values())


def test_key_screen_numbers_spoken_l4c():
    data = _narration()
    combined = "".join(data.values())
    spoken_nums = set(extract_numbers(combined))
    required = {1653, 1673, 1915, 76, 14, 50000}
    missing = required - spoken_nums
    assert not missing, f"口播缺少关键数字: {missing}"


def test_key_proper_nouns_spoken():
    data = _narration()
    combined = "".join(data.values())
    nouns = ["挂甲屯", "额驸城", "吴应熊", "吴三桂", "杨延昭", "日下旧闻考",
             "清圣祖实录", "宋史", "畅春园", "万泉河", "朱自清"]
    for n in nouns:
        assert n in combined, f"口播缺少专名: {n}"


def test_all_16_audio_files_present():
    assert AUDIO_DIR.exists()
    for i in range(1, 9):
        p_pad = AUDIO_DIR / f"p{i:02d}.wav"
        p_short = AUDIO_DIR / f"p{i}.wav"
        assert p_pad.exists() and p_pad.is_file() and p_pad.stat().st_size > 10000
        assert p_short.exists() and p_short.is_file() and p_short.stat().st_size > 10000


def test_alias_bytes_identical_to_canonical():
    for i in range(1, 9):
        p_pad = AUDIO_DIR / f"p{i:02d}.wav"
        p_short = AUDIO_DIR / f"p{i}.wav"
        h_pad = hashlib.sha256(p_pad.read_bytes()).hexdigest()
        h_short = hashlib.sha256(p_short.read_bytes()).hexdigest()
        assert h_pad == h_short, f"p{i} 与 p{i:02d} 内容不一致"


def test_each_audio_duration_valid():
    durations = _durations()
    for k, d in durations.items():
        assert 25.0 <= d <= 45.0, f"{k} 时长异常: {d}s"


def test_total_audio_duration():
    durations = _durations()
    total = sum(durations.values())
    assert 240.0 <= total <= 320.0, f"总时长超标: {total}s"


def test_durations_json_matches_measured():
    durations = _durations()
    for k, d in durations.items():
        actual = round(_ffprobe_duration(AUDIO_DIR / f"{k}.wav"), 2)
        assert abs(actual - d) <= 0.05, f"{k} durations.json 与实测不符: {d} vs {actual}"


def test_durations_json_mirrored_to_both_data_dirs():
    orig = (NARR_DIR / "durations.json").read_bytes()
    for d in (REMOTION_DATA, TEMPLATE_DATA):
        p = d / "durations.json"
        assert p.exists()
        assert p.read_bytes() == orig


def test_narration_ts_in_sync_with_durations():
    durations = _durations()
    for d in (REMOTION_DATA, TEMPLATE_DATA):
        content = (d / "narration.ts").read_text(encoding="utf-8")
        m = re.search(r"PAGE_AUDIO_SEC\s*=\s*\[([^\]]+)\]", content)
        assert m, f"{d}/narration.ts 缺少 PAGE_AUDIO_SEC"
        ts_values = [float(x.strip()) for x in m.group(1).split(",")]
        expected = [durations[f"p{i:02d}"] for i in range(1, 9)]
        assert ts_values == expected


def test_subtitles_text_matches_narration():
    narr = _narration()
    subs_content = (REMOTION_DATA / "subtitles.ts").read_text(encoding="utf-8")
    m = re.search(r"SUBTITLES:\s*Record<string,\s*CaptionLine\[\]>\s*=\s*(\{.*?\});", subs_content, re.S)
    assert m, "无法解析 SUBTITLES"
    subs_dict = json.loads(m.group(1))

    for i in range(1, 9):
        page_str = str(i)
        assert page_str in subs_dict
        lines = subs_dict[page_str]
        reconstructed = "".join(line["text"] for line in lines)
        assert _strip(reconstructed) == _strip(narr[f"p{i:02d}"])
