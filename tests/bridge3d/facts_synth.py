# -*- coding: utf-8 -*-
"""合成 facts: 5 孔小桥(「汀步桥」)与 23 孔大桥(「长虹桥」), 全部数值为虚构。

用途: 证明 bridge3d 判据不依赖任何具体项目(含 E30)的数值 ——
同一套判据, N_SPAN=5 与 N_SPAN=23 都必须基线全绿。
所有事实均为 [工作值](虚构), [官方]条目用虚构 URL 走通登记格式。
"""
from types import SimpleNamespace

DOC = """合成项目 facts(虚构, 仅用于 bridge3d 框架测试)。
Z 基准: Z=0 = 常水位水面(建模约定)。
禁令: 未标定照片不得产生绝对米制尺寸; 超分(ESRGAN)结果禁止进入计量链; GPT 聊天记录不算来源。
"""


def _relations():
    """纯 lambda(不 import 框架)—— facts 模块必须保持零依赖可独立导入。"""
    return {
        # 中央孔最大、两侧渐小(单峰): 用半侧序列单调不减表达
        "central_span_largest": lambda f: all(
            list(f.SPAN_DISTINCT)[i] <= list(f.SPAN_DISTINCT)[i + 1] + 1e-9
            for i in range(len(f.SPAN_DISTINCT) - 1)),
        "pier_narrower_than_min_span": lambda f: f.PIER_W < min(f.SPAN_DISTINCT),
    }


def _sources(entries):
    return dict(entries)


def make_5():
    """5 孔小桥: 半侧 3 跨 [3,4,5] → 展开 5 跨; 总长 19 + 4×1.2 + 2×1.0 = 25.8 精确闭合。"""
    return SimpleNamespace(**{
        "__doc__": DOC,
        "RESEARCH_DONE": True,
        "BRIDGE_LEN": 25.8,
        "N_SPAN": 5,
        "SPRINGER": 1.2,
        "PIER_W": 1.2,
        "BRIDGE_ABUT": 1.0,
        "SPAN_DISTINCT": [3.0, 4.0, 5.0],
        "ARCH_RATIO": 0.5,
        "RING_T": 0.3,
        "DECK_UP_W": 3.0,
        "DECK_DOWN_W": 6.0,
        "DECK_Z_TOP": 4.2,
        "DECK_Z_END": 3.2,
        "CLOSURE_TOL": 0.01,
        "ARCH_RATIO_TARGET": 0.5,
        "ARCH_RATIO_TOL": 0.05,
        "ASSUMPTION_NAMES": ("MESH_TOL", "NSEG"),
        "PIER_CAP_W": 1.6,   # 未被判据消费的附加项目常量(特异性用)
        "RELATIONS": _relations(),
        "SOURCES": _sources({
            "BRIDGE_LEN": ("官方", "虚构项目志 2024 卷一 http://example.org/synth5/len"),
            "N_SPAN": ("官方", "虚构项目志 2024 卷一 http://example.org/synth5/span"),
            "SPRINGER": ("工作值", "无文献, 沿用合成脚本值"),
            "PIER_W": ("工作值", "无文献, 沿用合成脚本值"),
            "BRIDGE_ABUT": ("工作值", "无文献, 沿用合成脚本值"),
            "SPAN_DISTINCT": ("工作值", "无文献, 合成等差序列"),
            "ARCH_RATIO": ("图像推导", "合成正面图目视; 超分版本已退出计量链"),
            "RING_T": ("工作值", "无文献, 沿用合成脚本值"),
            "DECK_UP_W": ("官方", "虚构文保所 2023 测缩图 http://example.org/synth5/upw"),
            "DECK_DOWN_W": ("官方", "虚构文保所 2023 测缩图 http://example.org/synth5/dww"),
            "DECK_Z_TOP": ("工作值", "无文献, 沿用合成脚本值"),
            "DECK_Z_END": ("工作值", "无文献, 沿用合成脚本值"),
            "CLOSURE_TOL": ("工作值", "无出处, 框架验收约定值"),
            "ARCH_RATIO_TARGET": ("工作值", "无出处, 合成设计意图半圆"),
            "ARCH_RATIO_TOL": ("工作值", "无出处, 框架验收约定值"),
            "PIER_CAP_W": ("工作值", "无文献, 沿用合成脚本值"),
        }),
    })


def make_23():
    """23 孔大桥: 半侧 12 跨 [2.0..7.5] → 展开 23 跨;
    总长 106.5 + 22×1.8 + 2×1.5 = 149.1 精确闭合。"""
    return SimpleNamespace(**{
        "__doc__": DOC,
        "RESEARCH_DONE": True,
        "BRIDGE_LEN": 149.1,
        "N_SPAN": 23,
        "SPRINGER": 2.0,
        "PIER_W": 1.8,
        "BRIDGE_ABUT": 1.5,
        "SPAN_DISTINCT": [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5],
        "ARCH_RATIO": 0.5,
        "RING_T": 0.4,
        "DECK_UP_W": 4.5,
        "DECK_DOWN_W": 9.0,
        "DECK_Z_TOP": 7.0,
        "DECK_Z_END": 5.6,
        "CLOSURE_TOL": 0.01,
        "ARCH_RATIO_TARGET": 0.5,
        "ARCH_RATIO_TOL": 0.05,
        "ASSUMPTION_NAMES": ("MESH_TOL", "NSEG"),
        "PIER_CAP_W": 2.4,
        "RELATIONS": _relations(),
        "SOURCES": _sources({
            "BRIDGE_LEN": ("官方", "虚构长虹桥志 2025 http://example.org/synth23/len"),
            "N_SPAN": ("官方", "虚构长虹桥志 2025 http://example.org/synth23/span"),
            "SPRINGER": ("工作值", "无文献, 沿用合成脚本值"),
            "PIER_W": ("工作值", "无文献, 沿用合成脚本值"),
            "BRIDGE_ABUT": ("工作值", "无文献, 沿用合成脚本值"),
            "SPAN_DISTINCT": ("工作值", "无文献, 合成等差序列"),
            "ARCH_RATIO": ("图像推导", "合成正面图目视; 超分版本已退出计量链"),
            "RING_T": ("工作值", "无文献, 沿用合成脚本值"),
            "DECK_UP_W": ("官方", "虚构市文物局 2022 公告 http://example.org/synth23/upw"),
            "DECK_DOWN_W": ("官方", "虚构市文物局 2022 公告 http://example.org/synth23/dww"),
            "DECK_Z_TOP": ("工作值", "无文献, 沿用合成脚本值"),
            "DECK_Z_END": ("工作值", "无文献, 沿用合成脚本值"),
            "CLOSURE_TOL": ("工作值", "无出处, 框架验收约定值"),
            "ARCH_RATIO_TARGET": ("工作值", "无出处, 合成设计意图半圆"),
            "ARCH_RATIO_TOL": ("工作值", "无出处, 框架验收约定值"),
            "PIER_CAP_W": ("工作值", "无文献, 沿用合成脚本值"),
        }),
    })
