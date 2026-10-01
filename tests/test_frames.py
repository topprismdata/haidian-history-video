"""抽帧与 OCR 缓存模块的几何与逻辑测试。

注意：测试绝不加载 PaddleOCR 模型或调用 Remotion 抽帧，
全部使用合成 OcrResult 测试 text_at 的几何与边界容差逻辑，
以及缓存反序列化与断言防呆。
"""
import json
import pytest

from qa_v2.frames import (
    OcrResult,
    text_at,
    _assert_box_format,
    ocr_cached,
)


def _r(x1, y1, x2, y2, t, s=0.99):
    return (t, (x1, y1, x2, y2), s)


def test_text_at_finds_box_inside():
    o = OcrResult(["标题"], [(800, 60, 1100, 100)], [0.99])
    got = text_at(o, (780, 40, 1140, 120))
    assert [g[0] for g in got] == ["标题"]


def test_text_at_converts_box_to_xywh():
    o = OcrResult(["标题"], [(800, 60, 1100, 100)], [0.99])
    got = text_at(o, (780, 40, 1140, 120))
    assert got[0][1] == (800, 60, 300, 40)


def test_text_at_rejects_outside():
    o = OcrResult(["别处"], [(100, 100, 300, 140)], [0.99])
    assert text_at(o, (800, 60, 1140, 120)) == []


def test_text_at_tolerates_small_pad():
    """E11 实测：容差须 >= 25px，槽位与文字框有细微错位。"""
    o = OcrResult(["边缘"], [(790, 50, 1090, 100)], [0.99])
    # 中心点为 (940, 75)。
    # 槽位在 (966, 65, 300, 60) 时，左边界 966 - 25 = 941 > 940，偏离 26px，超容差被排除
    # 槽位在 (963, 62, 300, 60) 时，左边界 963 - 25 = 938 <= 940，偏离 23px，在容差内被保留
    assert text_at(o, (966, 65, 300, 60)) == []      # 差 26px，超容差
    assert len(text_at(o, (963, 62, 300, 60))) == 1  # 差 23px，在容差内


def test_text_at_returns_scores():
    o = OcrResult(["低置信"], [(800, 60, 900, 100)], [0.35])
    assert text_at(o, (780, 40, 1140, 120))[0][2] == 0.35


def test_ocr_result_json_roundtrip():
    o = OcrResult(["标题"], [(800, 60, 1100, 100)], [0.99])
    d = o.to_json()
    o2 = OcrResult.from_json(d)
    assert o2.texts == o.texts
    assert o2.boxes == o.boxes
    assert o2.scores == o.scores


def test_assert_box_format_detects_invalid():
    """首个框不是 [x1,y1,x2,y2] 格式（如误用 [x,y,w,h] 导致 x2 <= x1）时必须抛出异常。"""
    o = OcrResult(["错格式"], [(800, 60, 300, 40)], [0.99])
    with pytest.raises(ValueError, match="rec_boxes 格式异常"):
        _assert_box_format(o)


def test_ocr_cached_reads_cache(tmp_path):
    """验证命中缓存时直接读取反序列化，不执行任何 OCR 调用。"""
    cached = OcrResult(["缓存内容"], [(100, 100, 200, 150)], [0.95])
    cache_file = tmp_path / "e11_p01.json"
    cache_file.write_text(json.dumps(cached.to_json()), encoding="utf-8")

    res = ocr_cached("e11", 1, tmp_path / "non_existent.png", cache_dir=tmp_path)
    assert res.texts == ["缓存内容"]
    assert res.boxes == [(100, 100, 200, 150)]
