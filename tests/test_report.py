import pytest
from qa_v2.report import Finding, summarize, render_text, render_json


def test_summarize_counts_by_level():
    fs = [
        Finding("L1", 3, "r1_flag", "fail", "SLOT_MISSING_IN_TEXT", "文案没填"),
        Finding("L4", 3, "r1_total", "fail", "NUMBER_MISMATCH", "1485≠1486"),
        Finding("L4", 3, "r2_dir", "warn", "NUMBER_UNKNOWN", "归一失败率高"),
        Finding("L6", 5, "evidence_tag", "skip", "NO_NAMES", "专名表缺"),
    ]
    assert summarize(fs) == {"fail": 2, "warn": 1, "skip": 1, "info": 0}


def test_render_text_mentions_ep_and_counts():
    fs = [Finding("L1", 1, "title", "fail", "X", "坏了")]
    out = render_text(fs, "shucun")
    assert "shucun" in out
    assert "fail" in out
    assert "坏了" in out


def test_render_text_empty_says_pass():
    assert "通过" in render_text([], "shucun")


def test_render_json_roundtrips():
    import json as _json
    fs = [Finding("L1", 1, "title", "fail", "X", "坏了", {"a": 1})]
    got = _json.loads(render_json(fs, "shucun"))
    assert got["episode"] == "shucun"
    assert got["summary"]["fail"] == 1
    assert got["findings"][0]["slot"] == "title"
    assert got["findings"][0]["detail"] == {"a": 1}


def test_finding_defaults():
    f = Finding("L1", 1, "title", "fail", "X", "m")
    assert f.detail is None
    assert f.slot == "title"


def test_finding_invalid_level():
    with pytest.raises(AssertionError):
        Finding("L1", 1, "title", "invalid_level", "X", "m")
