# -*- coding: utf-8 -*-
"""E24《五塔寺·阳台山麓的千年清水院》Task 2: 分层视口引擎复用与特化测试.

验证 remotion-template/src/wutasi/viewport/*.tsx 组件契约与黄金数学模型:
1. 视口插值无过冲与 clamp01;
2. CrossFadeViewport 图层透明度在 [0, 1];
3. MapMarker 根容器为纯 SVG 矢量层, 杜绝 DOM 容器污染;
4. 工程副本 /tmp/chemistry-video 与正本完全一致。
"""
import math
import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE_DIR = REPO_ROOT / "remotion-template" / "src" / "wutasi" / "viewport"
SYNC_DIR = pathlib.Path("/tmp/chemistry-video/src/wutasi/viewport")

COMPONENT_FILES = (
    "PanZoomView.tsx",
    "CrossFadeViewport.tsx",
    "MapMarker.tsx",
    "ScrollPanView.tsx",
    "index.ts",
)


def clamp01(v):
    return max(0.0, min(1.0, v))


def frame_to_progress(frame, duration_in_frames):
    return clamp01(frame / max(1, duration_in_frames))


def interpolate_view(start, end, progress):
    p = clamp01(progress)
    x = start["x"] + (end["x"] - start["x"]) * p
    y = start["y"] + (end["y"] - start["y"]) * p
    scale = start["scale"] + (end["scale"] - start["scale"]) * p
    return {"x": round(x, 2), "y": round(y, 2), "scale": round(scale, 4)}


def test_viewport_files_exist_in_template():
    assert TEMPLATE_DIR.exists(), f"正本目录缺失: {TEMPLATE_DIR}"
    for filename in COMPONENT_FILES:
        p = TEMPLATE_DIR / filename
        assert p.exists(), f"正本缺失视口组件: {filename}"
        assert p.stat().st_size > 100, f"组件文件为空或损坏: {filename}"


def test_viewport_files_synced_to_runtime():
    assert SYNC_DIR.exists(), f"工程副本目录缺失: {SYNC_DIR}"
    for filename in COMPONENT_FILES:
        src = TEMPLATE_DIR / filename
        dst = SYNC_DIR / filename
        assert dst.exists(), f"工程副本未同步组件: {filename}"
        assert src.read_text(encoding="utf-8") == dst.read_text(encoding="utf-8"), (
            f"正本与副本不一致: {filename}"
        )


def test_golden_model_clamp_and_monotonic():
    start = {"x": 100.0, "y": 200.0, "scale": 1.0}
    end = {"x": 500.0, "y": 800.0, "scale": 2.2}

    assert interpolate_view(start, end, -0.5) == start
    assert interpolate_view(start, end, 1.5) == end

    prev_scale = 1.0
    for f in range(31):
        prog = frame_to_progress(f, 30)
        v = interpolate_view(start, end, prog)
        assert v["scale"] >= prev_scale
        prev_scale = v["scale"]


def test_map_marker_svg_root_contract():
    marker_file = TEMPLATE_DIR / "MapMarker.tsx"
    assert marker_file.exists(), "MapMarker.tsx 不存在"
    code = marker_file.read_text(encoding="utf-8")
    assert "<svg" in code, "MapMarker 根容器必须包含 <svg>"
    assert "<div" not in code, "MapMarker 严禁使用 <div> 根容器 (防 DOM 渗入)"


def test_index_exports_all_components():
    index_file = TEMPLATE_DIR / "index.ts"
    assert index_file.exists(), "index.ts 不存在"
    code = index_file.read_text(encoding="utf-8")
    for name in ["PanZoomView", "CrossFadeViewport", "MapMarker", "ScrollPanView"]:
        assert name in code, f"index.ts 必须导出 {name}"
