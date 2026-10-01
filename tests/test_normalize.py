"""归一化。阈值与规则来自 E11 实测。

E11 用 PaddleOCR 3.7 跑完 8 页，平均置信 0.989，噪声**只有标点**：
  原文「树村·圆明园正北」   → OCR「树村.圆明园正北」
  原文「一个村子，三重身份」 → OCR「一个村子.三重身份」
  原文「楹＝间」           → OCR「楹=间」
无错字、无漏字，所以归一只需处理标点，不需要模糊匹配。
"""
import pytest

from qa_v2.normalize import (
    normalize_punct, normalize_script, to_int, extract_numbers, number_unknown_rate,
)


@pytest.mark.parametrize("raw,expect", [
    ("树村·圆明园正北", "树村圆明园正北"),
    ("一个村子，三重身份", "一个村子三重身份"),
    ("楹＝间", "楹间"),
    ("「著移驻树村」", "著移驻树村"),
    ("E1 肖家河", "E1肖家河"),
    ("1799 → 1800 → 1801", "179918001801"),
])
def test_normalize_punct(raw, expect):
    assert normalize_punct(raw) == expect


def test_normalize_punct_keeps_latin_and_cjk():
    assert normalize_punct("五圣庵·鐡磬一") == "五圣庵鐡磬一"

def test_normalize_script_converts_traditional():
    assert normalize_script("正黃旗") == "正黄旗"
    assert normalize_script("鑲黃旗與正白旗") == "镶黄旗与正白旗"
    assert normalize_script("圓明園") == "圆明园"


def test_normalize_punct_integrates_script_conversion():
    assert normalize_punct("正黃旗 · 圓明園") == "正黄旗圆明园"
    assert normalize_punct("觀音寺·鐵鐘一") == "观音寺铁钟一"


@pytest.mark.parametrize("tok,expect", [
    ("1485", 1485),
    ("1724", 1724),
    ("一七二四", 1724),      # 纯位值写法（口播逐位念年份）
    ("一千二百五十", 1250),
    ("三千", 3000),
    ("三百七十五", 375),
    ("二十三", 23),
    ("二十八", 28),
    ("一百二十", 120),
])
def test_to_int(tok, expect):
    assert to_int(tok) == expect


@pytest.mark.parametrize("tok", ["蜀村", "", "·", "abc", "百", "千", "万"])
def test_to_int_returns_none_for_non_number(tok):
    """单独的单位字（百/千/万）不是定量数字，返回 None。"""
    assert to_int(tok) is None


def test_extract_numbers_mixes_forms():
    txt = "共盖房一万间，分为八处，每处一千二百五十间（1250）"
    assert set(extract_numbers(txt)) == {8, 10000, 1250}


def test_extract_numbers_reads_speech_years():
    """口播里年份是逐位念的：「一七二四年」→ 1724。"""
    assert extract_numbers("雍正二年，也就是一七二四年") == [1724]


def test_extract_numbers_ignores_non_quantitative_units():
    """修辞性用词（逾千年、万寿山、百年老字号）不抽取为定量数字。"""
    assert extract_numbers("若音转成立，地名逾千年") == []
    assert extract_numbers("绕万寿山西麓") == []
    assert extract_numbers("百年老字号") == []


def test_extract_numbers_handles_parallel_reign_years():
    """并列省略年号名时（嘉庆四年 · 五年 · 六年），五年、六年不误判为定量数字。"""
    txt = "嘉庆四年设总兵 · 五年十一月十七日下诏 · 六年移驻"
    assert extract_numbers(txt) == [11, 17]


def test_extract_numbers_preserves_gregorian_years():
    """四位中文公历年份（一七八一年）绝不能被误判成年号剥离。"""
    txt = "一七八一年，乾隆四十六年七月"
    assert extract_numbers(txt) == [1781, 7]


def test_number_unknown_rate_is_zero_for_clean_text():
    assert number_unknown_rate("镶黄旗在村西，65 楹，1485 楹") == 0.0


def test_number_unknown_rate_flags_garbage():
    """归一函数出 bug 时要能被察觉，而不是静默通过。"""
    rate = number_unknown_rate("一七二四 9999 一二三四五六七")
    assert rate > 0.1
