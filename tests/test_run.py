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
        "dazhongsi", "landianchang", "shucun",
    }
    for ep, comp in COMPOSITION_OVERRIDES.items():
        assert comp.endswith("Course")
        assert comp != "%sCourse" % ep.capitalize() or ep in (
            "shucun", "dazhongsi", "xisanqi", "yimuyuan", "niangniangfu",
            "landianchang",
        ), "%s 的映射是 capitalize() 拼的，需人工确认" % ep
