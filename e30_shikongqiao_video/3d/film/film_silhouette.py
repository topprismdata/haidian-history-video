#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# e30_shikongqiao_video/3d/film/film_silhouette.py
"""P3-T6 工序剪影 SVG 资产(参数化人形轮廓, 纯 path, blender-free)。

产出片头/工序段的剪影小人(film_geometry.SILHOUETTE_SLOTS 全部站位)。
证据纪律(本模块硬合同): 每个 SVG 文件**首行**必须是指示性注释
`<!-- evidence: ... -->`, 内容含 G0 证据号(C:A4 式)或 [设计选择] 标签;
gen_svg 对无出处输入直接 raise —— 不存在无证据头的剪影资产
(test_silhouette_svg_evidence_header 钉死)。

接口:
    gen_svg(pose, out_path, evidence)   # 单 pose → SVG 文件(首行证据头注)
    generate_all(out_dir)               # SILHOUETTE_SLOTS 全部站位落盘

pose 词表 = {lever, chisel, crowbar}, 从 SILHOUETTE_SLOTS 派生(单源):
对应 C:A4 石作加工链(打荒→錾道→剁斧→扁光)的撬/錾/撬棍三形制; 站位坐标
为 [设计选择], 形制背书 C:A4(证据字段如实分层, 与 film_geometry 头注一致)。

几何: 参数化人形 —— 头/躯干/四肢由关节表给出, 手位等次级点从工具线
(杠杆/錾杆/撬棍)参数化求出, 非散点堆砌; 每根肢体一条 <path> 圆帽粗描
线, 头与石块为实心 path。全部矢量 path: 无位图/无外链/无脚本/无文本
(test_svg_render_safe 钉死)。同 pose 两次生成逐字节同(纯字符串格式化,
确定性输出)。
"""
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from film_geometry import SILHOUETTE_SLOTS  # noqa: E402  剪影站位单源(P3-T4)

__all__ = ["POSES", "gen_svg", "generate_all"]

# ── 证据头注校验: G0 证据号或 [设计选择] 标签, 二者有其一 ──
_EVIDENCE_RE = re.compile(r"(?:C:)?[AB]\d+")
_DESIGN_TAG = "[设计选择]"

# ── 画布与比例参数(全部剪影共用同一套模数) ──
_W, _H = 240, 320           # 视窗(px)
_GROUND = 300.0             # 地面 y
_HEAD_R = 18.0              # 头半径(人形模数)
_NECK = 8.0                 # 颈长(肩到头下缘)
_W_LEG, _W_ARM = 13.0, 11.0
_W_TORSO, _W_TOOL, _W_GROUND = 26.0, 7.0, 3.0
_COLOR = "#26221e"          # 剪影墨色(近黑, 对白石桥底)

# pose 词表: 从 SILHOUETTE_SLOTS 派生保序去重(单源; 新 pose 未实现画法
# 时 KeyError fail-closed, 不允许静默出空剪影)
POSES = tuple(dict.fromkeys(s["pose"] for s in SILHOUETTE_SLOTS))


# ---------------------------------------------------------------------------
# path 元素工厂(全部输出都是 <path>)
# ---------------------------------------------------------------------------

def _fmt(v):
    # type: (float) -> str
    return "%.1f" % float(v)


def _pt(p):
    # type: (tuple) -> str
    return "%s,%s" % (_fmt(p[0]), _fmt(p[1]))


def _lerp(a, b, t):
    # type: (tuple, tuple, float) -> tuple
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def _stroke(pts, width, color=_COLOR):
    # type: (list, float, str) -> str
    """折线 → 圆帽描边 path(肢体/工具)。"""
    d = "M " + " L ".join(_pt(p) for p in pts)
    return ('    <path d="%s" fill="none" stroke="%s" stroke-width="%s"'
            ' stroke-linecap="round" stroke-linejoin="round"/>'
            % (d, color, _fmt(width)))


def _disc(c, r, color=_COLOR):
    # type: (tuple, float, str) -> str
    """圆 → 两段圆弧 path(头)。"""
    d = ("M %s a %s,%s 0 1 0 %s,0 a %s,%s 0 1 0 %s,0 Z"
         % (_pt((c[0] - r, c[1])), _fmt(r), _fmt(r), _fmt(2 * r),
            _fmt(r), _fmt(r), _fmt(-2 * r)))
    return '    <path d="%s" fill="%s" stroke="none"/>' % (d, color)


def _block(x0, x1, y_top, y_bot=_GROUND, color=_COLOR):
    # type: (float, float, float, float, str) -> str
    """石块/支点块 → 实心矩形 path。"""
    d = "M %s L %s L %s L %s Z" % (_pt((x0, y_bot)), _pt((x0, y_top)),
                                   _pt((x1, y_top)), _pt((x1, y_bot)))
    return '    <path d="%s" fill="%s" stroke="none"/>' % (d, color)


def _ground_line():
    # type: () -> str
    return _stroke([(_W * 0.06, _GROUND), (_W * 0.94, _GROUND)], _W_GROUND)


def _head(neck):
    # type: (tuple) -> tuple
    """颈点 → 头圆心(颈长 + 头半径, 铅垂上移)。"""
    return (neck[0], neck[1] - _NECK - _HEAD_R)


# ---------------------------------------------------------------------------
# 三 pose 关节表(参数化: 手位取自工具线上的点, 非独立魔数)
# ---------------------------------------------------------------------------

def _pose_lever():
    # type: () -> list
    """撬杠就位位(C:A4 撬形制): 弓身压杠杆尾, 杠过支点块、杠头楔入石底。"""
    bar_e = (52.0, 232.0)                      # 杠尾(手握段)
    bar_f = (128.0, 264.0)                     # 支点接触点
    bar_t = (204.0, 296.0)                     # 杠头(石下, 被石遮)
    h1 = (88.0, bar_e[1] + (bar_t[1] - bar_e[1]) * (88.0 - bar_e[0])
          / (bar_t[0] - bar_e[0]))             # 手位 = 杠上点(参数化)
    h2 = (102.0, bar_e[1] + (bar_t[1] - bar_e[1]) * (102.0 - bar_e[0])
          / (bar_t[0] - bar_e[0]))
    hip, neck = (84.0, 224.0), (98.0, 168.0)
    sh1, sh2 = (98.0, 176.0), (102.0, 178.0)
    return [
        _ground_line(),
        _block(114.0, 142.0, 264.0),           # 支点块(杠先搁其上)
        _stroke([bar_e, bar_t], _W_TOOL),      # 杠(过 bar_f 直线)
        _block(192.0, 228.0, 268.0),           # 被撬石(后画, 遮杠头)
        _stroke([hip, (76.0, 262.0), (70.0, _GROUND)], _W_LEG),
        _stroke([hip, (94.0, 262.0), (100.0, _GROUND)], _W_LEG),
        _stroke([hip, neck], _W_TORSO),
        _stroke([sh1, (96.0, 214.0), h1], _W_ARM),
        _stroke([sh2, (108.0, 216.0), h2], _W_ARM),
        _disc(_head(neck), _HEAD_R),
    ]


def _pose_chisel():
    # type: () -> list
    """錾道位(C:A4 錾形制): 跪姿俯身持錾抵石, 后手举锤。"""
    hip, neck = (108.0, 226.0), (134.0, 154.0)
    sh1, sh2 = (134.0, 162.0), (138.0, 164.0)
    rod_a, rod_b = (166.0, 196.0), (188.0, 246.0)   # 錾杆(尖抵石顶)
    hand1 = (171.0, 208.0)                          # 手位 = 錾杆上点(参数化)
    hand2 = (136.0, 92.0)                           # 举锤手
    return [
        _ground_line(),
        _block(184.0, 224.0, 246.0),               # 正錾的石料
        _stroke([rod_a, rod_b], 5.5),              # 錾
        _stroke([hip, (90.0, _GROUND), (64.0, _GROUND)], _W_LEG),    # 跪腿(膝点地, 胫贴地)
        _stroke([hip, (146.0, 266.0), (158.0, _GROUND)], _W_LEG),     # 前腿
        _stroke([hip, neck], _W_TORSO),
        _stroke([sh1, (158.0, 188.0), hand1], _W_ARM),
        _stroke([sh2, (124.0, 126.0), hand2], _W_ARM),
        _disc(_head(neck), _HEAD_R),
        _stroke([(118.0, 76.0), (152.0, 106.0)], 13.0),   # 锤(举过头顶)
    ]


def _pose_crowbar():
    # type: () -> list
    """撬棍翻料位(C:A4 撬棍形制): 深俯身压撬棍, 棍端楔入石底。"""
    bar_e = (140.0, 178.0)                          # 棍柄端
    bar_t = (206.0, 262.0)                          # 棍端(石下, 被石遮)
    h1 = (176.0, bar_t[1] + (bar_e[1] - bar_t[1]) * (bar_t[0] - 176.0)
          / (bar_t[0] - bar_e[0]))                  # 手位 = 棍上点(参数化)
    h2 = (166.0, bar_t[1] + (bar_e[1] - bar_t[1]) * (bar_t[0] - 166.0)
          / (bar_t[0] - bar_e[0]))
    hip, neck = (92.0, 224.0), (132.0, 194.0)
    sh1, sh2 = (132.0, 202.0), (136.0, 200.0)
    return [
        _ground_line(),
        _stroke([bar_e, bar_t], _W_TOOL),          # 撬棍
        _block(194.0, 232.0, 254.0),               # 被翻石料(后画, 遮棍端)
        _stroke([hip, (84.0, 262.0), (78.0, _GROUND)], _W_LEG),
        _stroke([hip, (102.0, 262.0), (110.0, _GROUND)], _W_LEG),
        _stroke([hip, neck], _W_TORSO),
        _stroke([sh1, (158.0, 220.0), h1], _W_ARM),
        _stroke([sh2, (152.0, 212.0), h2], _W_ARM),
        _disc(_head(neck), _HEAD_R),
    ]


_POSES = {"lever": _pose_lever, "chisel": _pose_chisel, "crowbar": _pose_crowbar}


# ---------------------------------------------------------------------------
# 出口: gen_svg / generate_all
# ---------------------------------------------------------------------------

def _require_evidence(evidence):
    # type: (object) -> None
    """无出处即 raise(计划 Task 6 Step 1: gen_svg 对无 evidence 输入拒绝)。"""
    if not isinstance(evidence, str) or not evidence.strip():
        raise ValueError("evidence 缺失 —— 剪影资产必须带证据头注"
                         "(G0 证据号或 [设计选择])")
    if "--" in evidence:
        raise ValueError("evidence 含 '--' —— SVG 注释非法序列")
    if not (_EVIDENCE_RE.search(evidence) or _DESIGN_TAG in evidence):
        raise ValueError(
            "evidence 无出处: %r —— 须含 G0 证据号(如 C:A4)或 %s 标签"
            % (evidence, _DESIGN_TAG))


def gen_svg(pose, out_path, evidence):
    # type: (str, str, str) -> str
    """单 pose 剪影 → SVG 文件; 返回 out_path。

    首行 = `<!-- evidence: ... -->`(证据头注硬合同); 只接受 SILHOUETTE_SLOTS
    词表内的 pose; evidence 须含 G0 证据号或 [设计选择], 否则 raise。
    """
    if pose not in _POSES:
        raise ValueError("未知 pose: %r —— 词表 = %s(单源 SILHOUETTE_SLOTS)"
                         % (pose, "/".join(POSES)))
    _require_evidence(evidence)
    lines = [
        "<!-- evidence: %s -->" % evidence,
        "<!-- pose: %s | P3-T6 参数化剪影(纯 path, 生成器 film_silhouette.py) -->"
        % pose,
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d"'
        ' viewBox="0 0 %d %d">' % (_W, _H, _W, _H),
    ]
    lines.extend(_POSES[pose]())
    lines.append("</svg>")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return out_path


def generate_all(out_dir):
    # type: (str) -> list
    """SILHOUETTE_SLOTS 全部站位落盘; 返回文件路径表(与站位表同序)。

    每个文件首行 evidence = 该站位自己的证据字段(逐位透传, 不合并改写)。
    """
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for i, slot in enumerate(SILHOUETTE_SLOTS):
        p = os.path.join(out_dir, "silhouette_%02d_%s.svg" % (i, slot["pose"]))
        paths.append(gen_svg(slot["pose"], p, slot["evidence"]))
    return paths


def main():
    # type: () -> int
    out_dir = os.path.normpath(os.path.join(
        _HERE, os.pardir, "out", "film", "silhouettes"))
    for p in generate_all(out_dir):
        with open(p, encoding="utf-8") as f:
            print("%s | %s" % (p, f.readline().strip()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
