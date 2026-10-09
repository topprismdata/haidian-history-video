# -*- coding: utf-8 -*-
"""MET_ARCH_SHAPE 拱形闸门负控制(拱线族返工 2026-10-08)。

纪律: 负控制必须先红后绿 —— 闸门若对被废除的两圆心 ogee 不红, 即恒真不收。
本文件把【返工前 ogee 拱线】逐字钉为 pinned 负控制(与 git 历史 fbe672f
facts.py 逐式一致), 永久证明:
  ① pinned ogee 中央孔(b>a, 两圆心 cusp) 拱腹单圆拟合 rms/r >= CIRCLE_FIT_RTOL
     (返工日实测 0.01443, 见 refs/arch_shape_redgreen.txt);
  ② 现行单心圆弧拱全 17 孔 rms/r < 阈值(check_body 零 MET_ARCH_SHAPE fail);
  ③ 族切换零锚点漂移: 冠/起拱/矢高逐位不变(deck-spandrel / crown-rise);
  ④ ogee 专有符号(arch_e/_arc_pair/blunt_s/CROWN_BLUNT_K/CROWN_BLUNT_CAP)
     已从单一数据源删除, 无残留别名。
"""
import math
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "3d"))
import facts as F  # noqa: E402
import geom_math as GM  # noqa: E402
import qa_bridge as QB  # noqa: E402
from assumptions import CIRCLE_FIT_RTOL  # noqa: E402


# ── pinned 负控制: 返工前(fbe672f) facts.py 的 ogee 拱线, 逐式照抄 ──
_PIN_BLUNT_K = 0.40
_PIN_BLUNT_CAP = 0.020


def _pin_arch_e(a, b):
    return max(0.0, (b * b - a * a) / (2.0 * a)) if a > 1e-6 else 0.0


def _pin_arc_pair(x, xc, a, b):
    if b >= a - 1e-12:
        e = _pin_arch_e(a, b)
        R = a + e
        out = []
        for cc in (xc + e, xc - e):
            dd = R * R - (x - cc) ** 2
            if dd > 1e-9:
                sq = math.sqrt(dd)
                out.append((sq, -(x - cc) / sq))
            else:
                out.append((0.0, 0.0))
        return out
    ep = (a * a - b * b) / (2.0 * b) if b > 1e-6 else 0.0
    R = b + ep
    dd = R * R - (x - xc) ** 2
    if dd > 1e-9:
        sq = math.sqrt(dd)
        return [(sq - ep, -(x - xc) / sq), (sq - ep, -(x - xc) / sq)]
    return [(0.0, 0.0), (0.0, 0.0)]


def _pin_blunt_s(a, b):
    return min(_PIN_BLUNT_K * _pin_arch_e(a, b), _PIN_BLUNT_CAP * a)


def _pin_arch_z(x, xc, springer, a, b):
    (h1, _), (h2, _) = _pin_arc_pair(x, xc, a, b)
    lo, hi = (h1, h2) if h1 <= h2 else (h2, h1)
    s = _pin_blunt_s(a, b)
    if s <= 1e-9:
        return springer + lo
    return springer + lo - s * math.log(1.0 + math.exp((lo - hi) / s))


def _soffit_pts(arch_z_fn, i):
    xc = GM.arch_center_x(i)
    a = GM.SPANS[i] / 2.0
    b = GM.arch_rise(i)
    spz = GM.arch_springer_z(i)
    return [(xc - a + 2.0 * a * k / 40.0,
             arch_z_fn(xc - a + 2.0 * a * k / 40.0, xc, spz, a, b))
            for k in range(41)]


def test_pinned_ogee_center_arch_is_red():
    """负控制(红向): pinned ogee 中央孔拟合残差必须 >= 阈值 —— 闸门抓得住被废族。"""
    rr, _ = QB.circle_fit_rms(_soffit_pts(_pin_arch_z, 8))
    assert rr >= CIRCLE_FIT_RTOL, \
        "pinned ogee 中央孔 rms/r=%.5f 未达红门 %.3f —— MET_ARCH_SHAPE 恒真嫌疑" % (rr, CIRCLE_FIT_RTOL)


def test_pinned_ogee_reported_value_matches_rework_evidence():
    """红证据数值钉: 返工日实测中央孔 rms/r=0.01443(refs/arch_shape_redgreen.txt),
    pinned 重放偏差须在 1e-4 内(公式漂移即本测红)。"""
    rr, _ = QB.circle_fit_rms(_soffit_pts(_pin_arch_z, 8))
    assert abs(rr - 0.01443) < 1e-4, "pinned ogee 残差漂移: %.6f" % rr


def test_round_family_all_arches_green():
    """绿向: 现行单心圆弧全 17 孔拟合残差 < 阈值, 且留一个量级以上余量。"""
    for i in range(17):
        rr, _ = QB.circle_fit_rms(_soffit_pts(F.arch_z, i))
        assert rr < CIRCLE_FIT_RTOL, "孔%d rms/r=%.6f 超阈" % (i + 1, rr)
        assert rr < 1e-6, "孔%d rms/r=%.2e 非解析圆(应 <1e-6)" % (i + 1, rr)


def test_gate_reports_no_shape_fail_on_real_facts():
    """判据级绿: check_body 对现行 facts 零 MET_ARCH_SHAPE fail(闸门确实执行)。"""
    import facts
    levels = {x[1]: x[0] for x in QB.check_body(facts)}
    assert levels.get("MET_ARCH_SHAPE") != "skip", "MET_ARCH_SHAPE 未执行(skip=不算通过)"
    fails = [x for x in QB.check_body(facts)
             if x[0] == "fail" and x[1] in ("MET_ARCH_SHAPE", "MET_ARCH_FAMILY")]
    assert not fails, fails


def test_family_switch_preserves_anchors():
    """锚点零漂移: 冠 z = 桥面-拱肩, 起拱 z = 冠-矢, 矢 = rise_ratio×跨 ——
    族返工只许换曲线, 不许动这三个被 M19/M20 照片钉死的量。"""
    for i in range(17):
        xc = GM.arch_center_x(i)
        a = GM.SPANS[i] / 2.0
        b = GM.arch_rise(i)
        spz = GM.arch_springer_z(i)
        crown = GM.arch_crown_z(i)
        assert abs(GM.arch_rise(i) - F.rise_ratio(i) * GM.SPANS[i]) < 1e-12
        assert abs(spz - (crown - b)) < 1e-9
        assert abs(F.arch_z(xc, xc, spz, a, b) - crown) < 1e-9
        # b>a 孔跨内分支在起拱线上方 2d 处过墩面(horseshoe), 但三锚点恒精确归圆
        assert abs(F.arch_signed_r(xc - a, spz, xc, spz, a, b)) < 1e-9
        assert abs(F.arch_signed_r(xc + a, spz, xc, spz, a, b)) < 1e-9
        assert abs(F.arch_signed_r(xc, crown, xc, spz, a, b)) < 1e-9


def test_ogee_symbols_deleted():
    """干净切换: ogee 专有符号不得残留于单一数据源(删死代码不留别名)。
    bridge_geom2 顶层 import bmesh(Blender 专属), 系统态用 AST 检查源码等价成立。"""
    import ast
    for sym in ("arch_e", "_arc_pair", "blunt_s",
                "CROWN_BLUNT_K", "CROWN_BLUNT_CAP"):
        assert not hasattr(F, sym), "facts.%s 未删" % sym
    src_path = os.path.join(os.path.dirname(__file__), "..", "3d", "bridge_geom2.py")
    tree = ast.parse(open(src_path, encoding="utf-8").read())
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
    for sym in ("arch_e", "_arc_pair", "blunt_s",
                "CROWN_BLUNT_K", "CROWN_BLUNT_CAP"):
        assert sym not in names, "bridge_geom2.py 仍引用 %s" % sym


def test_mesh_level_opening_gate_present():
    """[拱线族返工清债 2026-10-08] 网格级洞形闸门必须存在(qa_l2
    ARCH_MESH_OPENING): 深夜事故——解析层(MET_ARCH_SHAPE)全绿 + 网格层
    洞形破损(bowtie 自交切割折线 → 矩形槽)共存, 目检才抓到。本钉锁
    "解析↔网格闭环"的网格侧闸门不被静默移除; blender-free 用源级 AST 检查。
    变异红证据: 孔9 冠下 0.5m 注入探针顶点 → 闸门抓到(blender 实测,
    /tmp/probe_meshgate.py 输出 MUTATION_PROBE bad=1)。"""
    import ast
    src_path = os.path.join(os.path.dirname(__file__), "..", "3d", "qa_l2.py")
    src = open(src_path, encoding="utf-8").read()
    ast.parse(src)  # 语法自检
    assert "ARCH_MESH_OPENING" in src, \
        "qa_l2 网格级洞形闸门(ARCH_MESH_OPENING)被移除 —— 禁止"
    assert "ARCH_THROUGH_RAY" in src, (
        "qa_l2 透射闸(ARCH_THROUGH_RAY)被移除 —— 禁止"
        "(实心未切墙无顶点在净空圆内, 顶点闸会空转, 射线透射是唯一网格级真闸)")
    assert "arch_signed_r" in src, "qa_l2 径向闭环调用缺失"
    bs_path = os.path.join(os.path.dirname(__file__), "..", "3d", "build_scene2.py")
    bs_src = open(bs_path, encoding="utf-8").read()
    assert "VOID_BOOLEAN_SILENT_FAIL" in bs_src, \
        "build_scene2 缺布尔静默失败结果断言(禁令: 挖洞失败不许静默出厂)"
