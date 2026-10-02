# -*- coding: utf-8 -*-
"""T1（2026-10-02）：OCR 参数基线防漂移钉。

背景：E13 反向走查 V3/V4 假警报的精确根因是审计脚本自配 PaddleOCR 参数
（use_textline_orientation=True 且未关 use_doc_orientation_classify），
doc_ori 分类器把水彩板面误判倒置、先旋转整图再检测，rec_polys 全落在
旋转后坐标系。qa_v2/frames.py.OCR_INIT_PARAMS 是唯一事实源，本测试钉死
两个分类器必须关闭，防止未来有人「顺手」改动基线。
"""
from qa_v2.frames import OCR_INIT_PARAMS


def test_orientation_classifiers_must_be_off():
    """E13 疫苗：两个方向分类器必须显式关闭。"""
    assert OCR_INIT_PARAMS["use_doc_orientation_classify"] is False
    assert OCR_INIT_PARAMS["use_textline_orientation"] is False


def test_unwarping_off_and_lang_ch():
    """unwarping 同族风险一并关闭；中文管线 lang=ch。"""
    assert OCR_INIT_PARAMS["use_doc_unwarping"] is False
    assert OCR_INIT_PARAMS["lang"] == "ch"
