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
