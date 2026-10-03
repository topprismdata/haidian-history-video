# -*- coding: utf-8 -*-
"""E20《勺园·淑春园·未名湖》Task 2: 分层视口漫游组件 — 视口插值数学与边界安全性单测。

本文件是 src/shaoyuan/viewport/*.tsx 中 Remotion 实现的**黄金数学模型 (golden model)**，
两侧必须维持同一契约（两侧口径不对称会产出必假的绿）：

1. 插值进度 progress 一律 clamp 到 [0, 1]，帧越界不得外推 (extrapolate clamp)；
2. durationInFrames <= 0 视为"动画已完成" (progress = 1.0)，严禁除零与非单调 inputRange；
3. 缓动曲线 = 设计规范指定的 CSS ease：cubic-bezier(0.25, 0.1, 0.25, 1.0)，
   端点归一、单调不减、无过冲（推拉不得越过落幅视口）；
4. 图层透明度插值结果必须始终落在 [0, 1]；
5. MapMarker 定位标必须以 SVG 矢量叠加层渲染（含 <text> 矢量标签），
   严禁输出为 QA 可见的 DOM 文字槽。

golden model 中的 round(...) 仅为断言数值稳定性，TS 侧 transform 使用原始浮点。
"""
import math
import pathlib

# 兼容两种工作目录：git 根目录 (/Volumes/macstudio/video-projects) 与 chemistry-video/
_CANDIDATES = [
    pathlib.Path("chemistry-video/src/shaoyuan/viewport"),
    pathlib.Path("src/shaoyuan/viewport"),
]
# 实现落地前目录尚不存在 → 取第一个候选路径，让契约测试以 FileNotFoundError 变红 (TDD red)
VIEWPORT_DIR = next((c for c in _CANDIDATES if c.is_dir()), _CANDIDATES[0])
# 组件的 git 入库正本（.gitignore: chemistry-video/ 为本机工程副本不入库，
# Remotion 源码正本放 remotion-template/，工程副本经符号链接指向这里）
TEMPLATE_DIR = pathlib.Path("remotion-template/src/shaoyuan/viewport")
COMPONENT_FILES = ("PanZoomView.tsx", "CrossFadeViewport.tsx", "MapMarker.tsx", "index.ts")


# ---------------------------------------------------------------------------
# 黄金数学模型 —— 与 TS 实现逐一对应
# ---------------------------------------------------------------------------

def clamp01(v):
    """双侧同源：TS 侧由 Remotion interpolate 的 extrapolate clamp 保证同一语义。"""
    return max(0.0, min(1.0, v))


def frame_to_progress(frame, duration_in_frames):
    """帧 → 归一化进度。duration <= 0 按单帧动画处理（与 TS 侧
    Math.max(1, durationInFrames) 完全同构），防除零与 inputRange 非单调。"""
    return clamp01(frame / max(1, duration_in_frames))


def interpolate_view(start, end, progress):
    """视口平滑插值：progress 先 clamp，起点/终点视口恒等返回，禁止外推。"""
    p = clamp01(progress)
    x = start["x"] + (end["x"] - start["x"]) * p
    y = start["y"] + (end["y"] - start["y"]) * p
    scale = start["scale"] + (end["scale"] - start["scale"]) * p
    return {"x": round(x, 2), "y": round(y, 2), "scale": round(scale, 4)}


def interpolate_opacity(start_op, end_op, progress):
    """图层透明度插值：progress clamp 后线性过渡，结果必须落在 [0, 1]。"""
    p = clamp01(progress)
    return start_op + (end_op - start_op) * p


def cubic_bezier_ease(t, x1=0.25, y1=0.1, x2=0.25, y2=1.0):
    """CSS ease 的黄金参照（与 Remotion Easing.bezier 同为标准三次贝塞尔求值）。
    控制点 x 单调不减 (0 <= x1 <= x2 <= 1)，可用二分法对 x(t) 求参数 u 再回代 y(u)。"""
    def px(u):
        return 3.0 * (1.0 - u) ** 2 * u * x1 + 3.0 * (1.0 - u) * u ** 2 * x2 + u ** 3

    def py(u):
        return 3.0 * (1.0 - u) ** 2 * u * y1 + 3.0 * (1.0 - u) * u ** 2 * y2 + u ** 3

    if t <= 0.0:
        return 0.0
    if t >= 1.0:
        return 1.0
    lo, hi = 0.0, 1.0
    for _ in range(64):
        mid = (lo + hi) / 2.0
        if px(mid) < t:
            lo = mid
        else:
            hi = mid
    return py((lo + hi) / 2.0)


# ---------------------------------------------------------------------------
# 视口插值：边界与安全性
# ---------------------------------------------------------------------------

def test_viewport_interpolation_bounds():
    start = {"x": 0, "y": 0, "scale": 1.0}
    end = {"x": -800, "y": -400, "scale": 2.2}

    assert interpolate_view(start, end, 0.0) == start
    assert interpolate_view(start, end, 1.0) == end
    mid = interpolate_view(start, end, 0.5)
    assert mid["scale"] == 1.6
    assert mid["x"] == -400.0


def test_viewport_interpolation_clamps_out_of_range_progress():
    """帧越过起止边界时必须 clamp：严禁外推出底图可视范围。"""
    start = {"x": 100.0, "y": -50.0, "scale": 1.0}
    end = {"x": -800, "y": -400, "scale": 2.2}

    assert interpolate_view(start, end, -0.5) == start
    assert interpolate_view(start, end, 1.5) == end
    assert interpolate_view(start, end, 12.0) == end
    assert interpolate_view(start, end, -99.0) == start


def test_viewport_interpolation_scale_stays_positive():
    """任何合法输入下缩放不得穿越 0（防止底图翻转/消失）。"""
    start = {"x": 0, "y": 0, "scale": 1.0}
    end = {"x": -300.0, "y": 120.0, "scale": 3.5}
    for i in range(11):
        v = interpolate_view(start, end, i / 10.0)
        assert v["scale"] > 0.0


def test_frame_to_progress_boundary_safety():
    """帧 → 进度映射的除零与越界防护。"""
    assert frame_to_progress(0, 90) == 0.0
    assert frame_to_progress(45, 90) == 0.5
    assert frame_to_progress(90, 90) == 1.0
    # 越界 clamp
    assert frame_to_progress(-7, 90) == 0.0
    assert frame_to_progress(9000, 90) == 1.0
    # duration <= 0：按单帧动画折叠（TS Math.max(1,·) 同构），严禁 ZeroDivisionError
    assert frame_to_progress(0, 0) == 0.0
    assert frame_to_progress(1, 0) == 1.0
    assert frame_to_progress(33, 0) == 1.0
    assert frame_to_progress(33, -5) == 1.0


def test_opacity_interpolation_boundaries_and_clamp():
    """CrossFadeViewport 图层透明度：端点恒等、越界 clamp、结果恒在 [0, 1]。"""
    assert interpolate_opacity(0.0, 1.0, 0.0) == 0.0
    assert interpolate_opacity(0.0, 1.0, 1.0) == 1.0
    assert interpolate_opacity(0.25, 0.9, 0.5) == 0.575
    assert interpolate_opacity(0.8, 0.0, 1.5) == 0.0
    assert interpolate_opacity(0.2, 0.6, -1.0) == 0.2
    for i in range(11):
        p = i / 10.0
        for s, e in ((0.0, 1.0), (1.0, 0.0), (0.35, 0.75), (0.9, 0.1)):
            o = interpolate_opacity(s, e, p)
            assert 0.0 <= o <= 1.0


# ---------------------------------------------------------------------------
# 缓动曲线：cubic-bezier(0.25, 0.1, 0.25, 1.0)（CSS ease）
# ---------------------------------------------------------------------------

def test_ease_curve_endpoints_and_no_overshoot():
    """起幅/落幅必须精确归位，全程不得过冲（推拉不得越过目标视口）。"""
    assert cubic_bezier_ease(0.0) == 0.0
    assert cubic_bezier_ease(1.0) == 1.0
    n = 201
    for i in range(n):
        t = i / (n - 1)
        y = cubic_bezier_ease(t)
        assert 0.0 <= y <= 1.0, "缓动曲线在 t=%r 过冲: %r" % (t, y)


def test_ease_curve_monotonic_and_takeoff_settle():
    """曲线单调不减（漫游不得回跳），起幅平缓、中段连贯、落幅长缓稳定（设计规范要求）。"""
    prev = -1.0
    for i in range(201):
        t = i / 200.0
        y = cubic_bezier_ease(t)
        assert y >= prev, "缓动曲线在 t=%r 出现回跳: %r < %r" % (t, y, prev)
        prev = y
    # 起幅平缓：前段低于对角线爬升 (ease(0.1) ≈ 0.095)
    assert cubic_bezier_ease(0.1) < 0.1
    assert cubic_bezier_ease(0.05) < 0.05
    # 推拉连贯：中前段快速推进 (ease(0.25) ≈ 0.41)
    assert cubic_bezier_ease(0.25) > 0.35
    # 落幅稳定：长缓收尾，尾段近乎贴住终点 (ease(0.75) ≈ 0.96, ease(0.9) ≈ 0.994)
    assert cubic_bezier_ease(0.75) > 0.9
    assert cubic_bezier_ease(0.9) > 0.99
    assert 1.0 - cubic_bezier_ease(0.9) < 0.01


# ---------------------------------------------------------------------------
# 实现契约：TSX 组件必须落地并遵守红线（TDD red → green 的红灯来源）
# ---------------------------------------------------------------------------

def _read_component(name):
    p = VIEWPORT_DIR / name
    assert p.is_file(), "视口组件必须存在: %s" % p
    return p.read_text(encoding="utf-8")


def test_viewport_components_exist():
    for name in COMPONENT_FILES:
        assert (VIEWPORT_DIR / name).is_file(), "视口组件必须存在: %s" % name


def test_working_copy_synced_with_tracked_template():
    """remotion-template 是组件的 git 入库正本，chemistry-video 工程副本（符号链接
    或复制体）必须与正本逐字节一致，防止模板与工程副本静默漂移。"""
    for name in COMPONENT_FILES:
        tp = TEMPLATE_DIR / name
        assert tp.is_file(), "模板正本缺失: %s" % tp
        wp = VIEWPORT_DIR / name
        assert wp.is_file(), "工程副本缺失: %s" % wp
        assert wp.read_bytes() == tp.read_bytes(), "工程副本与模板正本内容漂移: %s" % name


def test_panzoomview_contract():
    src = _read_component("PanZoomView.tsx")
    assert "useCurrentFrame" in src, "必须由 useCurrentFrame 驱动"
    assert "interpolate" in src, "必须使用 Remotion interpolate"
    assert "startView" in src and "endView" in src, "必须声明 startView/endView 视口契约"
    assert "scale" in src, "视口必须包含缩放分量"
    assert "translate3d" in src, "必须使用 GPU 合成的 translate3d"
    assert "overflow" in src and "hidden" in src, "外层必须 overflow: hidden 裁切视口"
    assert "willChange" in src, "必须声明 will-change: transform 启用 GPU 缓存"
    assert "extrapolateLeft" in src and "extrapolateRight" in src, \
        "插值必须双侧 clamp，帧越界不得外推"


def test_panzoomview_easing_matches_golden_curve():
    src = _read_component("PanZoomView.tsx")
    assert "Easing" in src, "必须使用 Remotion Easing"
    has_curve = (
        "Easing.bezier(0.25, 0.1, 0.25, 1.0)" in src
        or "Easing.bezier(0.25,0.1,0.25,1)" in src
        or "Easing.bezier(0.25, 0.1, 0.25, 1)" in src
    )
    assert has_curve, "缓动必须为设计规范指定的 cubic-bezier(0.25, 0.1, 0.25, 1.0)"


def test_crossfadeviewport_contract():
    src = _read_component("CrossFadeViewport.tsx")
    assert "useCurrentFrame" in src, "必须由 useCurrentFrame 驱动"
    assert "opacity" in src, "必须驱动图层 opacity"
    for field in ("src", "startOpacity", "endOpacity"):
        assert field in src, "图层契约缺失字段: %s" % field
    assert "extrapolateLeft" in src and "extrapolateRight" in src, \
        "透明度插值必须双侧 clamp"


def test_mapmarker_is_svg_vector_overlay():
    """MapMarker 红线：必须为 SVG 矢量叠加层，标签为 SVG <text>，
    严禁输出为外部 QA 可见的 DOM 文字槽。"""
    src = _read_component("MapMarker.tsx")
    assert "<svg" in src, "MapMarker 必须以 SVG 叠加层渲染"
    assert "<text" in src, "标签必须为 SVG 矢量文本 (<text>)，不得使用 DOM 文本节点"


def test_viewport_index_exports_all_components():
    src = _read_component("index.ts")
    for sym in ("PanZoomView", "CrossFadeViewport", "MapMarker"):
        assert sym in src, "导出包必须导出: %s" % sym
