import json
import pathlib

from qa_v2.run import parse_args, exit_code, COMPOSITION_OVERRIDES


def test_parse_args_defaults():
    a = parse_args(["shucun"])
    assert a.episodes == ["shucun"]
    assert a.use_ocr is False
    assert a.full is False
    assert a.as_json is False


def test_parse_args_flags():
    a = parse_args(["shucun", "--ocr", "--full", "--json"])
    assert a.use_ocr and a.full and a.as_json


def test_parse_args_multiple_episodes():
    a = parse_args(["shucun", "dazhongsi"])
    assert a.episodes == ["shucun", "dazhongsi"]


def test_exit_code_zero_when_no_fail():
    from qa_v2.report import Finding
    assert exit_code([Finding("L1", 1, "a", "warn", "X", "m")]) == 0
    assert exit_code([Finding("L1", 1, "a", "skip", "X", "m")]) == 0


def test_exit_code_one_on_fail():
    from qa_v2.report import Finding
    assert exit_code([Finding("L1", 1, "a", "fail", "X", "m")]) == 1


def test_composition_overrides_covers_shucun():
    assert COMPOSITION_OVERRIDES["shucun"] == "ShucunCourse"


def test_composition_overrides_covers_all_registered_episodes():
    """集名 → Composition 映射必须完整，且不是 capitalize() 的结果。

    `gaoliangqiao`.capitalize() → `Gaoliangqiao`，但实际注册名是
    `GaoLiangQiaoCourse`；靠拼名字会在旧集上直接报「Composition 不存在」。
    """
    assert set(COMPOSITION_OVERRIDES) >= {
        "yimuyuan", "niangniangfu", "xisanqi", "gaoliangqiao",
        "dazhongsi", "landianchang", "shucun", "suzhoujie", "zhongguancun",
    }
    for ep, comp in COMPOSITION_OVERRIDES.items():
        assert comp.endswith("Course")
        assert comp != "%sCourse" % ep.capitalize() or ep in (
            "shucun", "dazhongsi", "xisanqi", "yimuyuan", "niangniangfu",
            "landianchang", "suzhoujie", "zhongguancun",
            "changchunyuan", "wanshou", "changhe", "fenshi",
        ), "%s 的映射是 capitalize() 拼的，需人工确认" % ep


# ---------- 帧缓存失效（2026-10-02 FullQaRun 实测缺陷回归） ----------

def _fake_ep_tree(tmp_path):
    root = tmp_path / "proj"
    ep_dir = root / "src" / "demo" / "data"
    ep_dir.mkdir(parents=True)
    src = ep_dir / "narration.ts"
    src.write_text("demo", encoding="utf-8")
    return root, src


def test_frame_cache_reused_without_change(monkeypatch, tmp_path):
    """png 存在且数据未变 → 复用，不重渲。"""
    import types
    from qa_v2 import run as run_mod
    root, _src = _fake_ep_tree(tmp_path)
    frame_dir = tmp_path / "frames"
    monkeypatch.setattr(run_mod, "ROOT", root)
    monkeypatch.setattr(run_mod, "FRAME_DIR", frame_dir)
    monkeypatch.setattr(run_mod, "load_episode",
                        lambda name: types.SimpleNamespace(
                            final_frame=lambda n: 30 * n))
    monkeypatch.setattr(run_mod, "COMPOSITION_OVERRIDES",
                        {"demo": "DemoCourse"})
    calls = []

    def fake_render(composition, frame, out):
        calls.append(frame)
        out.write_bytes(b"png")

    monkeypatch.setattr(run_mod, "render_frame", fake_render)
    page = types.SimpleNamespace(number=1)
    png, _ = run_mod._frame_for("demo", page, use_ocr=False)
    assert png.exists() and len(calls) == 1
    run_mod._frame_for("demo", page, use_ocr=False)
    assert len(calls) == 1, "数据未变时不得重渲"


def test_frame_cache_invalidates_on_source_change(monkeypatch, tmp_path):
    """数据 mtime 晚于 png → 重渲；且同步清除该页 OCR 缓存（缓存键不含帧哈希）。"""
    import os
    import time
    import types
    from qa_v2 import run as run_mod
    root, src = _fake_ep_tree(tmp_path)
    frame_dir = tmp_path / "frames"
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    ocr_json = cache_dir / "demo_p01.json"
    ocr_json.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(run_mod, "ROOT", root)
    monkeypatch.setattr(run_mod, "FRAME_DIR", frame_dir)
    monkeypatch.setattr(run_mod, "load_episode",
                        lambda name: types.SimpleNamespace(
                            final_frame=lambda n: 30 * n))
    monkeypatch.setattr(run_mod, "COMPOSITION_OVERRIDES",
                        {"demo": "DemoCourse"})
    monkeypatch.setattr(run_mod, "OCR_CACHE_DIR", cache_dir)
    calls = []

    def fake_render(composition, frame, out):
        calls.append(frame)
        out.write_bytes(b"png")

    monkeypatch.setattr(run_mod, "render_frame", fake_render)
    page = types.SimpleNamespace(number=1)
    png, _ = run_mod._frame_for("demo", page, use_ocr=False)
    assert len(calls) == 1
    # 数据变新 → 帧过期
    future = time.time() + 10
    os.utime(src, (future, future))
    run_mod._frame_for("demo", page, use_ocr=False)
    assert len(calls) == 2, "数据改动后必须重渲"
    assert not ocr_json.exists(), "重渲后必须清该页 OCR 缓存"


def test_source_freshness_missing_episode(monkeypatch, tmp_path):
    """集目录不存在 → 0.0（视为最旧，帧不会被误判过期）。"""
    from qa_v2 import run as run_mod
    monkeypatch.setattr(run_mod, "ROOT", tmp_path)
    assert run_mod._source_freshness("no-such-ep") == 0.0
