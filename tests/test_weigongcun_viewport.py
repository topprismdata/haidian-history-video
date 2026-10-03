# -*- coding: utf-8 -*-
"""E21《魏公村·高梁河畔的畏吾村》Task 2: 分层视口引擎复用与特化 — 视口插值数学、
组件契约与双树同步一致性单测。

本文件是 remotion-template/src/weigongcun/viewport/*.tsx 中 Remotion 实现的
**黄金数学模型 (golden model)**，两侧必须维持同一契约（两侧口径不对称会产出必假的绿）：

1. 插值进度 progress 一律 clamp 到 [0, 1]，帧越界不得外推 (extrapolate clamp)；
2. durationInFrames <= 0 视为"动画已完成" (progress = 1.0)，严禁除零与非单调 inputRange；
3. PanZoomView 缓动曲线 = cubic-bezier(0.25, 0.1, 0.25, 1.0)：
   端点归一、单调不减、无过冲（推拉不得越过落幅视口）；
4. CrossFadeViewport 图层透明度插值结果必须始终落在 [0, 1]（四时代 MEC 叠合同样成立）；
5. MapMarker 呼吸光圈由 useCurrentFrame 驱动的正弦函数决定（0.5 Hz，逐帧确定性），
   必须以 SVG 矢量叠加层渲染（含 <text> 矢量标签），严禁输出为 QA 可见的 DOM 文字槽，
   严禁向 slots.json 导出任何文字槽。

golden model 中的 round(...) 仅为断言数值稳定性，TS 侧 transform 使用原始浮点。
"""
import math
import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
# 组件的 git 入库正本（remotion-template/ 为 Remotion 源码正本）
TEMPLATE_DIR = REPO_ROOT / "remotion-template" / "src" / "weigongcun" / "viewport"
# 工程同步副本（/tmp/chemistry-video 是本机工程副本，必须与正本逐字节一致）
SYNC_DIR = pathlib.Path("/tmp/chemistry-video/src/weigongcun/viewport")

COMPONENT_FILES = (
    "PanZoomView.tsx",
    "CrossFadeViewport.tsx",
    "MapMarker.tsx",
    "ScrollPanView.tsx",
    "index.ts",
)


# ---------------------------------------------------------------------------
# 黄金数学模型 —— 与 TS 实现逐一对应
# ---------------------------------------------------------------------------

def clamp01(v):
    """双侧同源：TS 侧由 Remotion interpolate 的 extrapolate clamp + clamp01 兜底保证。"""
    return max(0.0, min(1.0, v))


def frame_to_progress(frame, duration_in_frames):
    """帧 → 归一化进度。duration <= 0 按单帧动画处理（与 TS 侧
    Math.max(1, durationInFrames) 完全同构），防除零与 inputRange 非单调。"""
    return clamp01(frame / max(1, duration_in_frames))


def interpolate_view(start, end, progress):
    """PanZoomView 视口平滑插值：progress 先 clamp，越界不外推。"""
    p = clamp01(progress)
    x = start["x"] + (end["x"] - start["x"]) * p
    y = start["y"] + (end["y"] - start["y"]) * p
    scale = start["scale"] + (end["scale"] - start["scale"]) * p
    return {"x": round(x, 2), "y": round(y, 2), "scale": round(scale, 4)}


def interpolate_opacity(start_op, end_op, progress, eased_progress=None):
    """CrossFadeViewport 图层透明度：progress clamp 后线性（smooth 时传入缓动后的
    progress），结果必须落在 [0, 1]。"""
    p = clamp01(eased_progress if eased_progress is not None else progress)
    return start_op + (end_op - start_op) * p


def cubic_bezier_ease(t, x1=0.25, y1=0.1, x2=0.25, y2=1.0):
    """CSS ease 黄金参照（与 Remotion Easing.bezier 同为标准三次贝塞尔求值）。
    控制点 x 单调不减 (0 <= x1 <= x2 <= 1)，二分法对 x(u) 求参数再回代 y(u)。"""
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


def marker_breath(local_frame, fps, breath_hz=0.5):
    """MapMarker 呼吸光圈黄金模型：0.5 + 0.5·sin(2π·f·t)，逐帧确定性，
    输出恒在 [0, 1]。local_frame = max(0, frame - delay)。"""
    return 0.5 + 0.5 * math.sin((local_frame / fps) * 2.0 * math.pi * breath_hz)


# ---------------------------------------------------------------------------
# 视口插值：边界帧 / 负帧 / 超帧 / 平滑过渡
# ---------------------------------------------------------------------------

def test_viewport_interpolation_bounds():
    start = {"x": 0, "y": 0, "scale": 1.0}
    end = {"x": -900, "y": -420, "scale": 2.4}

    assert interpolate_view(start, end, 0.0) == start
    assert interpolate_view(start, end, 1.0) == end
    mid = interpolate_view(start, end, 0.5)
    assert mid["scale"] == 1.7
    assert mid["x"] == -450.0
    assert mid["y"] == -210.0


def test_viewport_interpolation_clamps_negative_and_over_frames():
    """帧越过起止边界时必须 clamp：严禁外推出底图可视范围。"""
    start = {"x": 120.0, "y": -60.0, "scale": 1.0}
    end = {"x": -900, "y": -420, "scale": 2.4}

    # 负帧 → 起点视口
    assert interpolate_view(start, end, -0.5) == start
    assert interpolate_view(start, end, -1.0) == start
    assert interpolate_view(start, end, -99.0) == start
    # 超帧 → 落点视口
    assert interpolate_view(start, end, 1.5) == end
    assert interpolate_view(start, end, 12.0) == end
    assert interpolate_view(start, end, 9001.0) == end


def test_viewport_interpolation_monotonic_and_scale_positive():
    """逐帧漫游单调不回跳（方向感知：终点在起点左侧则 x 单调不增），缩放全程不得穿越 0。"""
    start = {"x": 0, "y": 0, "scale": 1.0}
    end = {"x": -300.0, "y": 120.0, "scale": 3.5}
    direction = 1.0 if end["x"] >= start["x"] else -1.0
    prev_x = -math.inf * direction
    for i in range(11):
        p = i / 10.0
        v = interpolate_view(start, end, p)
        assert v["scale"] > 0.0
        assert direction * (v["x"] - prev_x) >= 0.0, "漫游在 p=%r 出现回跳" % p
        prev_x = v["x"]


def test_frame_to_progress_boundary_safety():
    """帧 → 进度映射：边界帧、负帧、超帧、除零防护全谱。"""
    # 边界帧
    assert frame_to_progress(0, 90) == 0.0
    assert frame_to_progress(45, 90) == 0.5
    assert frame_to_progress(90, 90) == 1.0
    # 负帧 clamp
    assert frame_to_progress(-1, 90) == 0.0
    assert frame_to_progress(-7, 90) == 0.0
    # 超帧 clamp
    assert frame_to_progress(91, 90) == 1.0
    assert frame_to_progress(9000, 90) == 1.0
    # duration <= 0：按单帧动画折叠（TS Math.max(1,·) 同构），严禁 ZeroDivisionError
    assert frame_to_progress(0, 0) == 0.0
    assert frame_to_progress(1, 0) == 1.0
    assert frame_to_progress(33, 0) == 1.0
    assert frame_to_progress(33, -5) == 1.0


def test_ease_curve_endpoints_and_no_overshoot():
    """起幅/落幅必须精确归位，全程不得过冲（推拉不得越过目标视口）。"""
    assert cubic_bezier_ease(0.0) == 0.0
    assert cubic_bezier_ease(1.0) == 1.0
    for i in range(201):
        t = i / 200.0
        y = cubic_bezier_ease(t)
        assert 0.0 <= y <= 1.0, "缓动曲线在 t=%r 过冲: %r" % (t, y)


def test_ease_curve_monotonic_and_takeoff_settle():
    """曲线单调不减（漫游不得回跳），起幅平缓、中段连贯、落幅长缓稳定。"""
    prev = -1.0
    for i in range(201):
        t = i / 200.0
        y = cubic_bezier_ease(t)
        assert y >= prev, "缓动曲线在 t=%r 出现回跳: %r < %r" % (t, y, prev)
        prev = y
    # 起幅平缓
    assert cubic_bezier_ease(0.1) < 0.1
    assert cubic_bezier_ease(0.05) < 0.05
    # 中段推进连贯
    assert cubic_bezier_ease(0.25) > 0.35
    # 落幅长缓稳定
    assert cubic_bezier_ease(0.75) > 0.9
    assert cubic_bezier_ease(0.9) > 0.99
    assert 1.0 - cubic_bezier_ease(0.9) < 0.01


def test_smooth_transition_of_panzoom_matches_eased_model():
    """PanZoomView 平滑过渡逐帧核验：eased progress 驱动的视口与黄金模型一致，
    且全程位于起止视口包围盒内。"""
    start = {"x": 0.0, "y": 0.0, "scale": 1.0}
    end = {"x": -900.0, "y": -420.0, "scale": 2.4}
    duration = 90
    lo_x, hi_x = min(start["x"], end["x"]), max(start["x"], end["x"])
    lo_s, hi_s = min(start["scale"], end["scale"]), max(start["scale"], end["scale"])
    for f in range(-3, duration + 4):
        p_lin = frame_to_progress(f, duration)
        p_eased = cubic_bezier_ease(p_lin)
        v = interpolate_view(start, end, p_eased)
        assert lo_x <= v["x"] <= hi_x or v["x"] in (lo_x, hi_x)
        assert lo_s <= v["scale"] <= hi_s, "缓动导致缩放过冲: %r" % v
    # 帧边界上 eased 与线性端点重合
    assert cubic_bezier_ease(frame_to_progress(0, duration)) == 0.0
    assert cubic_bezier_ease(frame_to_progress(duration, duration)) == 1.0


def test_crossfade_opacity_boundaries_clamp_and_range():
    """CrossFadeViewport 图层透明度：端点恒等、负帧/超帧 clamp、结果恒在 [0, 1]。"""
    assert interpolate_opacity(0.0, 1.0, 0.0) == 0.0
    assert interpolate_opacity(0.0, 1.0, 1.0) == 1.0
    assert interpolate_opacity(0.25, 0.9, 0.5) == 0.575
    # 超帧 → 终态；负帧 → 初态
    assert interpolate_opacity(0.8, 0.0, 1.5) == 0.0
    assert interpolate_opacity(0.2, 0.6, -1.0) == 0.2
    for i in range(11):
        p = i / 10.0
        for s, e in ((0.0, 1.0), (1.0, 0.0), (0.35, 0.75), (0.9, 0.1)):
            o = interpolate_opacity(s, e, p)
            assert 0.0 <= o <= 1.0


def test_crossfade_four_era_layer_sweep_stays_in_unit_range():
    """E21 MEC 四时代叠合：任一帧、任一图层透明度均须落在 [0, 1]，含 smooth 缓动。"""
    eras = [
        {"start": 1.0, "end": 0.0},   # 元·畏吾村
        {"start": 0.0, "end": 1.0},   # 明· Programmer
        {"start": 0.15, "end": 0.85},  # 1915 实测图
        {"start": 0.9, "end": 0.1},   # 现代遥感
    ]
    for smooth in (False, True):
        for f in range(-5, 96):
            p_lin = frame_to_progress(f, 90)
            p = cubic_bezier_ease(p_lin) if smooth else p_lin
            for era in eras:
                o = interpolate_opacity(era["start"], era["end"], p)
                assert 0.0 <= o <= 1.0, "smooth=%s f=%s opacity=%r 越界" % (smooth, f, o)


def test_mapmarker_breath_is_deterministic_sine_in_unit_range():
    """呼吸光圈黄金模型：正弦确定性、输出恒在 [0, 1]、同帧同值（逐帧可复现）。"""
    fps = 30
    first_pass = [marker_breath(f, fps) for f in range(0, fps * 2)]
    for v in first_pass:
        assert 0.0 <= v <= 1.0
    # 确定性：第二遍逐帧完全一致
    second_pass = [marker_breath(f, fps) for f in range(0, fps * 2)]
    assert first_pass == second_pass
    # 正弦完整呼吸周期：2 秒 @0.5Hz 内必触达上下界附近
    assert max(first_pass) > 0.98
    assert min(first_pass) < 0.02
    # delay 折叠：localFrame = max(0, frame - delay)，delay 前光圈静止在初相
    assert marker_breath(0, fps) == 0.5
    assert marker_breath(max(0, -9), fps) == marker_breath(max(0, -99), fps) == 0.5


# ---------------------------------------------------------------------------
# 实现契约：TSX 组件必须落地并遵守红线（TDD red → green 的红灯来源）
# ---------------------------------------------------------------------------

def _read_component(name):
    p = TEMPLATE_DIR / name
    assert p.is_file(), "视口组件必须存在: %s" % p
    return p.read_text(encoding="utf-8")


def _strip_tsx_strings_and_comments(src, keep_strings=False):
    """极简词法剥离：跳过注释，字符串/模板字面量默认丢弃（返回代码骨架）；
    keep_strings=True 时保留字符串内容（供 slots.json 红线检查——真代码引用
    必然出现在字符串字面量里，文档注释的「严禁写入 slots.json」不算违规）。"""
    out = []
    i, n = 0, len(src)
    mode = None  # None | "'" | '"' | '`' | 'line' | 'block'
    while i < n:
        ch = src[i]
        nxt = src[i + 1] if i + 1 < n else ""
        if mode is None:
            if ch in ("'", '"', "`"):
                mode = ch
                if keep_strings:
                    out.append(" ")
            elif ch == "/" and nxt == "/":
                mode = "line"
                i += 1
            elif ch == "/" and nxt == "*":
                mode = "block"
                i += 1
            else:
                out.append(ch)
        elif mode in ("'", '"', "`"):
            if ch == "\\":
                i += 1
            elif ch == mode:
                mode = None
            elif keep_strings:
                out.append(ch)
            elif mode == "`" and ch == "$" and nxt == "{":
                # 模板插值：内层是表达式，递归为代码骨架
                out.append("(")
                depth = 1
                i += 1
                while i + 1 < n and depth:
                    i += 1
                    if src[i] == "{":
                        depth += 1
                    elif src[i] == "}":
                        depth -= 1
                        if depth == 0:
                            out.append(")")
                            break
                        else:
                            out.append(src[i])
                    else:
                        out.append(src[i])
        elif mode == "line":
            if ch == "\n":
                mode = None
                out.append("\n")
        elif mode == "block":
            if ch == "*" and nxt == "/":
                mode = None
                i += 1
        i += 1
    return "".join(out)


def test_viewport_components_exist():
    assert TEMPLATE_DIR.is_dir(), "weigongcun/viewport/ 目录必须存在"
    for name in COMPONENT_FILES:
        assert (TEMPLATE_DIR / name).is_file(), "视口组件必须存在: %s" % name


def test_components_free_of_syntax_residue():
    """无语法残留：无合并冲突标记、无 TODO/FIXME/占位符残渣，括号引号全部配平。"""
    conflict_markers = ("<<<<<<<", ">>>>>>>", "=======")
    residue_tokens = ["TODO", "FIXME", "XXX", "待补充", "占位", "placeholder"]
    for name in COMPONENT_FILES:
        src = _read_component(name)
        for marker in conflict_markers:
            assert marker not in src, "%s 存在合并冲突标记: %s" % (name, marker)
        upper = src.upper()
        for token in residue_tokens:
            assert token not in upper, "%s 存在残留标记: %s" % (name, token)
        # 括号/引号配平（跳过字符串与注释后统计）
        skeleton = _strip_tsx_strings_and_comments(src)
        for op, cl in (("{", "}"), ("(", ")"), ("[", "]")):
            assert skeleton.count(op) == skeleton.count(cl), \
                "%s 括号不配平: %s %s vs %s%s" % (name, op, skeleton.count(op), cl, skeleton.count(cl))
        assert src.count("`") % 2 == 0, "%s 模板字面量反引号不配平" % name
        # 禁止空文件与禁止以悬空 export 结尾
        assert len(src.strip()) > 100, "%s 内容过短，疑似残缺文件" % name


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
    assert "Easing.bezier(0.25, 0.1, 0.25, 1.0)" in src, \
        "缓动必须为设计规范指定的 cubic-bezier(0.25, 0.1, 0.25, 1.0)"
    assert "Math.max(1" in src, "durationInFrames 必须 Math.max(1, ·) 防除零"
    assert "Img" in src and "staticFile" in src, "底图必须经 staticFile 加载 Remotion Img"


def test_crossfadeviewport_contract():
    src = _read_component("CrossFadeViewport.tsx")
    assert "useCurrentFrame" in src, "必须由 useCurrentFrame 驱动"
    assert "opacity" in src, "必须驱动图层 opacity"
    for field in ("src", "startOpacity", "endOpacity"):
        assert field in src, "图层契约缺失字段: %s" % field
    assert "extrapolateLeft" in src and "extrapolateRight" in src, \
        "透明度插值必须双侧 clamp"
    assert "clamp01" in src, "透明度必须经 clamp01 兜底，结果恒在 [0, 1]"
    assert "smooth" in src, "必须支持 smooth 平滑过渡开关"


def test_mapmarker_is_deterministic_svg_overlay():
    """MapMarker 红线：SVG 矢量叠加层 + <text> 矢量标签 + 正弦呼吸确定性，
    严禁输出为 QA 可见的 DOM 文字槽。"""
    src = _read_component("MapMarker.tsx")
    assert "<svg" in src, "MapMarker 必须以 SVG 叠加层渲染"
    assert "<text" in src, "标签必须为 SVG 矢量文本 (<text>)，不得使用 DOM 文本节点"
    assert "Math.sin" in src, "呼吸光圈必须由正弦函数驱动（逐帧确定性）"
    assert "useCurrentFrame" in src, "呼吸必须由 useCurrentFrame 驱动"
    assert "spring" in src, "入场弹性必须用 Remotion spring，而非 CSS 时间基动画"
    # 红线按代码口径检验：剥离注释后不得出现 slots.json 引用
    # （文档注释书写「严禁写入 slots.json」属红线声明，不算违规）
    assert "slots.json" not in _strip_tsx_strings_and_comments(src, keep_strings=True), \
        "MapMarker 代码严禁引用 slots.json"
    # 标签只允许落在 SVG 内部：组件不得渲染任何 DOM 文本节点
    # （先折叠 JSX 注释与标签间空白，再查找 >非空白非表达式< 形态的裸文本）
    tail = re.sub(r"\{/\*.*?\*/", "{}", src[src.index("<svg"):], flags=re.S)
    tail = re.sub(r">\s+", ">", tail)
    dom_text = re.search(r">[^<>{\s][^<>]*<", tail)
    assert dom_text is None, "SVG 内发现裸 DOM 文本节点: %r" % dom_text.group(0)[:40]


def test_scrollpanview_contract():
    src = _read_component("ScrollPanView.tsx")
    assert "scrollWidth" in src and "viewportWidth" in src, "长卷契约缺失 scrollWidth/viewportWidth"
    assert "translate3d" in src, "平移必须走 GPU 合成 translate3d"
    assert "Math.max(0" in src, "drift 必须 Math.max(0, ·)：内容不足视口宽时静置不平移"
    assert "extrapolateLeft" in src and "extrapolateRight" in src, "插值必须双侧 clamp"


def test_viewport_index_exports_all_components():
    src = _read_component("index.ts")
    for sym in ("PanZoomView", "CrossFadeViewport", "MapMarker", "ScrollPanView"):
        assert sym in src, "导出包必须导出: %s" % sym


def test_viewport_package_exports_no_text_slot_redline():
    """红线：视口包不得向 slots.json 导出文字槽——包目录内严禁出现 slots.json，
    组件源码不得含 slots 导出逻辑。"""
    assert not (TEMPLATE_DIR / "slots.json").exists(), \
        "viewport/ 包目录严禁包含 slots.json（文字槽只允许由 data/slots.json 承载）"
    for name in COMPONENT_FILES:
        src = _read_component(name)
        code_only = _strip_tsx_strings_and_comments(src, keep_strings=True)
        assert not re.search(r"slots\.json", code_only), "%s 代码引用了 slots.json" % name
        assert not re.search(r"export\s+(const|let|var|function)\s+[Ss]lots", src), \
            "%s 存在 slots 导出逻辑" % name


def test_working_copy_synced_with_template():
    """remotion-template 是 git 入库正本，/tmp/chemistry-video 工程副本必须与正本
    逐字节一致（文件集合一致 + 内容一致），防止模板与工程静默漂移。"""
    assert SYNC_DIR.is_dir(), "工程副本目录缺失: %s" % SYNC_DIR
    template_files = sorted(p.name for p in TEMPLATE_DIR.iterdir() if p.is_file())
    sync_files = sorted(p.name for p in SYNC_DIR.iterdir() if p.is_file())
    assert template_files == sync_files, \
        "两侧文件集合不一致: template=%s sync=%s" % (template_files, sync_files)
    for name in COMPONENT_FILES:
        tp = TEMPLATE_DIR / name
        sp = SYNC_DIR / name
        assert sp.is_file(), "工程副本缺失: %s" % sp
        assert sp.read_bytes() == tp.read_bytes(), "工程副本与模板正本内容漂移: %s" % name
