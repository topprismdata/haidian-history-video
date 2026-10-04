# -*- coding: utf-8 -*-
"""L3 register_overlay 合成负控测试。

设计说明(简报自相矛盾点的裁决): 简报原 test_shift_lowers_iou 对**纯刚体平移**断言
IoU < 0.95, 但其自身注释又要求"纯 bbox 比例差(实体相同)必须被归一化吸收, 不该拉低
IoU"——在宽高独立归一化(简报 Step 1.5 修订)下, bbox 裁剪使任何刚体平移被完全吸收,
两条要求数学上不可兼得。本套件按设计意图拆成两条:
  - test_rigid_shift_absorbed: 刚体平移必须被吸收(IoU>0.99, 不变性是特性);
  - test_peak_shift40_lowers_iou: 驼峰顶点平移 40px(构图级真错误, FACTS §6.4 口径)
    必须被抓住(IoU<0.95) —— 指标非常数 1 的反恒真负控。
"""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "3d"))
import register_overlay as R  # noqa: E402


def _save(arr, p):
    Image.fromarray(arr).save(str(p))
    return str(p)


def _camelback(w=800, h=200, bottom=150, top0=70, amp=50.0, sig=150.0, cx=400):
    """驼峰立面带: 顶=高斯驼峰, 底=平(水线), 与十七孔桥立面同构。"""
    xs = np.arange(w)
    top = (top0 + amp * np.exp(-((xs - cx) / sig) ** 2)).astype(int)
    m = np.zeros((h, w), np.uint8)
    for x in range(w):
        m[top[x]:bottom, x] = 255
    return m


def _arched_band(w=800, h=220):
    """带 3 个封闭券洞的桥体带(上部环圈 + 下部基础带封口, 与渲染剪影同构)。"""
    m = np.zeros((h, w), np.uint8)
    m[40:170, :] = 255
    for c0, c1 in ((100, 200), (300, 420), (550, 700)):
        m[90:150, c0:c1] = 0
    return m


def test_perfect_overlap(tmp_path):
    m = _camelback()
    a = _save(m, tmp_path / "a.png")
    b = _save(m.copy(), tmp_path / "b.png")
    iou, _ = R.overlay(a, b, str(tmp_path / "v.png"), a_is_ref=True, b_is_ref=True)
    assert iou > 0.99


def test_rigid_shift_absorbed(tmp_path):
    """刚体平移必须被 bbox 归一化吸收(设计特性, 与 test_perfect_overlap 同界)。"""
    m = _camelback()
    big = np.zeros((200, 880), np.uint8)
    big[:, 40:840] = m
    a = _save(m, tmp_path / "a.png")
    b = _save(big, tmp_path / "b.png")
    iou, _ = R.overlay(a, b, str(tmp_path / "v.png"), a_is_ref=True, b_is_ref=True)
    assert iou > 0.99


def test_peak_shift40_lowers_iou(tmp_path):
    """驼峰顶点平移 40px(构图级真错误)必须拉低 IoU —— 反恒真负控。"""
    m = _camelback()
    m2 = _camelback(cx=440)
    a = _save(m, tmp_path / "a.png")
    b = _save(m2, tmp_path / "b.png")
    iou, _ = R.overlay(a, b, str(tmp_path / "v.png"), a_is_ref=True, b_is_ref=True)
    assert iou < 0.95


def test_uniform_scale20_absorbed(tmp_path):
    """整体等比缩放 20%(实体相同)不得拉低 IoU —— 证明宽高独立归一化生效,
    IoU 在测形状而非测对齐/比例。"""
    m = _camelback()
    big = np.asarray(Image.fromarray(m).resize((960, 240), Image.BILINEAR))
    a = _save(m, tmp_path / "a.png")
    b = _save(big, tmp_path / "b.png")
    iou, _ = R.overlay(a, b, str(tmp_path / "v.png"), a_is_ref=True, b_is_ref=True)
    assert iou >= 0.95


def test_enclosed_holes_filled_silhouette(tmp_path):
    """§6.2-2 口径对齐负控: 参考掩膜"拱洞计入白区", 两侧填实 enclosed 孔后比对——
    带孔实体 vs 无孔带必须仍高 IoU(不拿参考不编码的券洞信息扣分)。"""
    a = _save(_arched_band(), tmp_path / "a.png")
    solid = np.zeros((220, 800), np.uint8)
    solid[40:170, :] = 255
    b = _save(solid, tmp_path / "b.png")
    iou, _ = R.overlay(a, b, str(tmp_path / "v.png"), a_is_ref=True, b_is_ref=True)
    assert iou >= 0.95
    # 同一掩膜的券洞表必须机械检出 3 孔(宽度归一化)
    vt = R.void_table(np.asarray(Image.open(a).convert("L")) > 127)
    assert len(vt) == 3
    for (xc, w), ex, ew in zip(vt, (0.1869, 0.4494, 0.7806), (0.125, 0.15, 0.1875)):
        assert abs(xc - ex) < 0.002 and abs(w - ew) < 0.002


def test_void_table_missing_and_shrunk(tmp_path):
    """券洞位置表负控: 挖掉(填实)一个孔 → 该孔检测必须缺失;
    半填一个孔 → 该孔检测宽度必须显著变小。"""
    m = _arched_band()
    vt0 = R.void_table(m > 127)
    assert len(vt0) == 3
    for (xc, w), ex, ew in zip(vt0, (0.1869, 0.4494, 0.7806), (0.125, 0.15, 0.1875)):
        assert abs(xc - ex) < 0.002 and abs(w - ew) < 0.002

    m_fill = m.copy()
    m_fill[90:150, 300:420] = 255          # 填实中孔
    vt1 = R.void_table(m_fill > 127)
    assert len(vt1) == 2
    assert all(abs(x - 0.4494) > 0.05 for x, _ in vt1)   # 该孔检测缺失

    m_half = m.copy()
    m_half[90:150, 550:625] = 255          # 半填第三孔(左半)
    vt2 = R.void_table(m_half > 127)
    assert len(vt2) == 3
    assert vt2[2][1] < 0.6 * vt0[2][1]     # 宽度显著变小(0.094 vs 0.1875)


# ══════════ I3(2026-10-05 终审): 券洞表硬判真实现进 VERDICT ══════════
# 修复前: 文档声称 count+Δxc 硬判, 代码只取 IoU; solidify 填实使缺洞免疫,
# 实测缺 1 孔 IoU=1.0000 仍 PASS, VOID_XC_TOL 全仓 0 处消费。

import facts as F  # noqa: E402  (3d 已在 sys.path; 期望券洞表由 facts 推导)


def _full_render_band(w=2400, h=320):
    """17 孔合成渲染带: 孔位/孔宽取自 facts 推导期望表(与真渲染同构:
    上部环圈 + 下部基础带封口 → enclosed 孔)。"""
    m = np.zeros((h, w), np.uint8)
    m[60:260, :] = 255
    for xc, wn in R.expected_void_table(F):
        x0, x1 = int((xc - wn / 2) * w), int((xc + wn / 2) * w)
        m[110:200, x0 + 2:x1 - 2] = 0
    return m


def test_void_verdict_baseline_pass():
    """合法基线必须绿: 17 孔位与 facts 期望一致 → ok 且零故障。"""
    ok, problems = R.void_verdict(_full_render_band() > 127)
    assert ok, problems
    assert problems == []


def test_void_verdict_missing_hole_fails():
    """挖掉(填实)一个孔 → 孔数 16 != 17 → 必须红(修复前 IoU=1.0000 PASS)。"""
    m = _full_render_band()
    xc, wn = R.expected_void_table(F)[8]           # 中央孔
    x0, x1 = int((xc - wn / 2) * 2400), int((xc + wn / 2) * 2400)
    m[110:200, x0:x1] = 255                        # 填实 = 挖掉一个券洞
    ok, problems = R.void_verdict(m > 127)
    assert not ok, "缺孔未被抓住(判据恒真)"
    assert any("孔数 16" in p for p in problems), problems


def test_void_verdict_xc_axis_on_spaced_bridge():
    """xc 轴必须独立于 count 轴被守: 孔数对但位置错 → xc 分支红。
    E30 真桥孔间距 ~0.017(< 2×VOID_XC_TOL), 大位移会与邻孔粘连塌缩成 count 破坏
    (由 count 分支抓, 见 test_void_verdict_missing_hole_fails); 本用例注入
    大间距三孔 facts(与大孔距桥同构)证明 xc 轴本身有牙。"""
    from types import SimpleNamespace
    f3 = SimpleNamespace(
        BRIDGE_LEN=40.0, N_SPAN=3, PIER_W=2.0, BRIDGE_ABUT=2.0,
        SPAN_DISTINCT=[4.0, 5.0, 4.0])          # 孔间距 0.05 归一(> 2×TOL), 平移不粘连
    W = 2400
    m = np.zeros((320, W), np.uint8)
    m[60:260, :] = 255
    for xc, wn in R.expected_void_table(f3):
        x0, x1 = int((xc - wn / 2) * W), int((xc + wn / 2) * W)
        m[110:200, x0 + 2:x1 - 2] = 0
    ok, problems = R.void_verdict(m > 127, f3)
    assert ok, problems                          # 合法基线先绿

    dx = 0.035                                   # 平移 0.035 > VOID_XC_TOL=0.02, 不触邻孔
    xc, wn = R.expected_void_table(f3)[1]
    x0, x1 = int((xc - wn / 2) * W), int((xc + wn / 2) * W)
    m2 = m.copy()
    m2[110:200, x0:x1] = 255
    n0, n1 = int((xc + dx - wn / 2) * W) + 2, int((xc + dx + wn / 2) * W) - 2
    m2[110:200, n0:n1] = 0
    ok2, problems2 = R.void_verdict(m2 > 127, f3)
    assert not ok2, "xc 轴漂移未被抓住(判据恒真)"
    assert all("孔数" not in p for p in problems2), problems2   # count 3 == 3
    assert any("xc" in p and "孔2" in p for p in problems2), problems2


def test_expected_void_table_matches_facts_topology():
    """期望表口径: 条数 == N_SPAN, xc 升序; 内孔中心 = 左支承内缘 + 净跨/2
    (与 bridge_geom2/qa_l2 挖孔口径同源: 拱心 = 支承中心点中点, 仅端孔受桥台
    宽≠墩宽影响, 两口径在端孔差 (PIER_W-ABUT)/4/BRIDGE_LEN)。"""
    exp = R.expected_void_table(F)
    assert len(exp) == F.N_SPAN
    assert all(exp[i][0] < exp[i + 1][0] for i in range(len(exp) - 1))
    # 内孔(两侧都是墩, 墩宽同): 拱心 = 孔左缘 + span/2, 精确闭式
    # (展开规则与 test_facts.test_span_distinct_shape_and_symmetric_closure 同一口径)
    spans17 = list(F.SPAN_DISTINCT) + list(reversed(F.SPAN_DISTINCT[:-1]))
    assert len(spans17) == F.N_SPAN
    offset = 0.0
    for i in range(1, F.N_SPAN - 1):
        offset += spans17[i - 1] + F.PIER_W
        center = -(F.BRIDGE_LEN / 2) + F.BRIDGE_ABUT + offset + spans17[i] / 2.0
        assert abs(exp[i][0] - (center / F.BRIDGE_LEN + 0.5)) < 1e-9, \
            "孔%d 期望中心与 facts 递推不一致" % (i + 1)
