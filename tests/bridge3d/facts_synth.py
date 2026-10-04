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


# ══════════ 合法替代构型基线(2026-10-05 终审 I1) ══════════
# 奇数对称不再是契约普适律: 半侧表+镜像展开只是对称奇数孔桥的便利路径。
# 框架的"通用性证明"必须覆盖四类合法但不同构的形态 —— 否则把首项目构型
# 当普适律的判据(原 MET_TAPER / 原 INV_SPANS_SYM / 平桥误判)永远过审。

def _relations_full_length_palindrome():
    """全长表桥的关系: 表自身回文。全长表路径不做镜像展开,
    对称是项目自声明(经 RELATIONS 验证), 不是框架普适律。"""
    return {
        "spans_palindrome": lambda f: all(
            f.SPAN_DISTINCT[i] == f.SPAN_DISTINCT[len(f.SPAN_DISTINCT) - 1 - i]
            for i in range(len(f.SPAN_DISTINCT) // 2)),
        "pier_narrower_than_min_span": lambda f: f.PIER_W < min(f.SPAN_DISTINCT),
    }


def _relations_generic():
    return {"pier_narrower_than_min_span": lambda f: f.PIER_W < min(f.SPAN_DISTINCT)}


def _alt_make(tag, n_span, spans, pier_w, abut, springer, ratio, ring_t,
              up_w, down_w, z_top, z_end, relations):
    """替代构型工厂: BRIDGE_LEN 由闭合精确反推(跨和+(N_SPAN-1)墩+2桥台)。
    全部数值虚构([工作值]), 官方条目用虚构 URL 走通登记格式。"""
    total = sum(spans) + (n_span - 1) * pier_w + 2.0 * abut
    return SimpleNamespace(**{
        "__doc__": DOC,
        "RESEARCH_DONE": True,
        "BRIDGE_LEN": total,
        "N_SPAN": n_span,
        "SPRINGER": springer,
        "PIER_W": pier_w,
        "BRIDGE_ABUT": abut,
        "SPAN_DISTINCT": list(spans),
        "ARCH_RATIO": ratio,
        "RING_T": ring_t,
        "DECK_UP_W": up_w,
        "DECK_DOWN_W": down_w,
        "DECK_Z_TOP": z_top,
        "DECK_Z_END": z_end,
        "CLOSURE_TOL": 0.01,
        "ARCH_RATIO_TARGET": ratio,
        "ARCH_RATIO_TOL": 0.05,
        "ASSUMPTION_NAMES": ("MESH_TOL", "NSEG"),
        "RELATIONS": relations,
        "SOURCES": _sources({
            "BRIDGE_LEN": ("官方", "虚构%s志 2026 http://example.org/%s/len" % (tag, tag)),
            "N_SPAN": ("官方", "虚构%s志 2026 http://example.org/%s/span" % (tag, tag)),
            "SPRINGER": ("工作值", "无文献, 沿用合成脚本值"),
            "PIER_W": ("工作值", "无文献, 沿用合成脚本值"),
            "BRIDGE_ABUT": ("工作值", "无文献, 沿用合成脚本值"),
            "SPAN_DISTINCT": ("工作值", "无文献, 合成%s构型" % tag),
            "ARCH_RATIO": ("图像推导", "合成立面目视; 超分版本已退出计量链"),
            "RING_T": ("工作值", "无文献, 沿用合成脚本值"),
            "DECK_UP_W": ("官方", "虚构文保所 2026 测缩图 http://example.org/%s/upw" % tag),
            "DECK_DOWN_W": ("官方", "虚构文保所 2026 测缩图 http://example.org/%s/dww" % tag),
            "DECK_Z_TOP": ("工作值", "无文献, 沿用合成脚本值"),
            "DECK_Z_END": ("工作值", "无文献, 沿用合成脚本值"),
            "CLOSURE_TOL": ("工作值", "无出处, 框架验收约定值"),
            "ARCH_RATIO_TARGET": ("工作值", "无出处, 合成设计意图"),
            "ARCH_RATIO_TOL": ("工作值", "无出处, 框架验收约定值"),
        }),
    })


def make_asym11():
    """卢沟桥式不对称奇数孔(全长表): 11 跨, 东端跨 11.40 != 西端跨 12.35,
    基准蓝本(十七孔桥官方蓝本)即左右不对称 —— 半侧表形态结构性装不下它。
    总长 133.6 + 10×2.2 + 2×2.6 = 160.8 精确闭合。"""
    return _alt_make(
        "asym11", 11,
        [11.40, 11.20, 12.10, 12.35, 12.55, 13.45, 12.55, 12.35, 12.10, 11.20, 12.35],
        pier_w=2.20, abut=2.60, springer=2.20, ratio=0.50, ring_t=0.50,
        up_w=7.10, down_w=15.80, z_top=12.00, z_end=9.60,
        relations=_relations_generic())


def make_even6():
    """对称偶数孔(全长回文表): 6 跨 [3.0,4.5,5.5,5.5,4.5,3.0]。
    偶数孔没有"中央孔", 半侧表+镜像展开(恒 2n-1)结构性装不下它;
    对称性由 RELATIONS 在全长表上自声明。总长 26.0 + 5×1.5 + 2×1.2 = 35.9。"""
    return _alt_make(
        "even6", 6, [3.00, 4.50, 5.50, 5.50, 4.50, 3.00],
        pier_w=1.50, abut=1.20, springer=1.60, ratio=0.50, ring_t=0.35,
        up_w=4.20, down_w=7.90, z_top=6.40, z_end=5.00,
        relations=_relations_full_length_palindrome())


def make_flat3():
    """平桥(无拱起): 3 等跨, DECK_Z_TOP == DECK_Z_END。
    纵坡方向判据(MET_DECK_DIR)只禁倒拱(端>中), 平桥是合法等号情形 ——
    原"必须中央最高"把拱桥构型当普适律。总长 18.0 + 2×1.4 + 2×1.5 = 23.8。"""
    return _alt_make(
        "flat3", 3, [6.00, 6.00, 6.00],
        pier_w=1.40, abut=1.50, springer=1.00, ratio=0.40, ring_t=0.30,
        up_w=4.00, down_w=5.00, z_top=4.00, z_end=4.00,
        relations=_relations_generic())


def make_equal4():
    """等宽桥(薄墩联拱石桥形态): 4 等跨, DECK_UP_W == DECK_DOWN_W。
    收分判据(MET_TAPER)只禁倒悬(顶>底), 等宽是合法等号情形。
    总长 20.0 + 3×1.6 + 2×1.4 = 27.6 精确闭合。"""
    return _alt_make(
        "equal4", 4, [5.00, 5.00, 5.00, 5.00],
        pier_w=1.60, abut=1.40, springer=1.50, ratio=0.50, ring_t=0.40,
        up_w=4.50, down_w=4.50, z_top=5.50, z_end=4.20,
        relations=_relations_generic())


ALTERNATE_MAKERS = (make_asym11, make_even6, make_flat3, make_equal4)
