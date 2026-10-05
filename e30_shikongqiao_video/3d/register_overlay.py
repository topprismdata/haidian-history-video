# -*- coding: utf-8 -*-
"""L3: 渲染正交立面 vs T3.5 人工掩膜 构图级轮廓比对。

参考侧: 直接读 T3.5 冻结的人工掩膜 refs/ref_mask.png —— 禁止对参考照重跑自动阈值。
  依据 FACTS.md §6.1/§6.2: 桥带仅 844x45 px(缩放后 62px 高, 单拱 25-38px), 自动 RGB
  阈值必然混桥身/水面/天空; 且该掩膜按口径"透空拱洞计入白区"(§6.2-2)。
渲染侧: film_transparent 渲染, alpha>127 即几何剪影。本项目实测(2026-10-04):
  简报初版 RGB 阈值(lum 90-235 & sat>0.05)在大理石低饱和材质上失效——
  与 alpha 真值的 IoU 仅 0.15 —— 故渲染侧优先 alpha 阈值, RGB 阈值仅作无 alpha 时的回退。
归一化: 两侧各自 bbox 后宽、高独立缩放到 1200x300 —— 比例失配不由 IoU 承担(Step 1.5)。

指标拆分(Step 1.5, 分别报告, 不合成总分):
  1) 实体轮廓 IoU(overlay): 两侧 enclosed 孔洞填实后比对。不填实则是在用参考掩膜
     不编码的信息(券洞)给渲染扣分——参考侧拱洞按口径计入白区, 填实才与参考口径对齐。
     该判据守驼峰曲线/总体长高比例(FACTS §6.4 构图级口径)。
  2) 券洞位置表硬判(void_verdict, 2026-10-05 终审 I3 真实现——此前只存在于文档,
     solidify 填实使缺洞对 IoU 免疫, 实测缺 1 孔 IoU=1.0000 仍 PASS):
     渲染侧 void_table 必须与 facts 推导的期望表一致 —— 孔数 == N_SPAN
     且逐孔 |Δxc| <= VOID_XC_TOL; 违反任一即 FAIL, 进入 VERDICT。
     参考掩膜无可靠券洞(§6.2-2 "宁缺毋滥"), 期望表来自 facts 而非参考照 ——
     本判据守"模型与 facts 一致"(渲染侧一票), facts 错了会一致地错(§6.2-2 已声明)。

效力边界(FACTS.md §7 完整声明):
  - 正交投影消掉透视尺度-深度可解性: 照片只能约束平面内轮廓, 测不到面外形变;
  - 学界无"渲染 vs 单张照片"定量验证范式, 本判据为自声明效力的空白区方法;
  - 像素层判据只能声明"结构与照片不矛盾", 不能声明准确性。
"""
from PIL import Image
import numpy as np
from scipy import ndimage
import os
import sys

# facts(纯数据)与 bridge3d.derive(纯拓扑, 无 bpy): 期望券洞表由 facts 推导,
# 递推口径与生成器/qa_l2 同源(bridge_geom2 消费同一 facts)。
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(_HERE))
for _p in (_HERE, _REPO_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import facts as _F                      # noqa: E402
from bridge3d import derive as _D       # noqa: E402

# ── 阈值(Step 1.6 扰动标定, 复现: python3 3d/refs/calibrate_iou.py, 种子 20261004) ──
OVERLAY_IOU_MIN = 0.76   # E2 可分: 可接受[0.8046,0.8373] vs 不可接受[0.0030,0.7216] 中点
VOID_XC_TOL = 0.02       # 券洞表 xc 轴: 可接受 max 0.0000 vs 缺孔信号 min 0.0442 中点

# [标定依据] 2026-10-04, 基线 = 冻结候选重渲版 ortho_side.png(IDAT 86fe24ec..., 23:23:44)
#   vs T3.5 人工掩膜; 扰动按物理量在掩膜空间实施(px/m=13.8667=bbox2080px/150m):
#   E2(填实剪影 vs ref) 可接受区间 [0.8046,0.8373](±0.5m 纵向分段扰动 x5 种子 + 墩宽±10%)
#     不可接受区间 [0.0030,0.7216](驼峰削平/纵坡反向——构图级真错误) → 取中点 0.76;
#   基线实测 E2 = 0.8070 ≥ 0.76(PASS, 余量 0.047)。
#   轴判定(详见 FACTS.md §7): ①均匀跨变 ±5% 被宽高独立归一化吸收(E1=0.9969)——
#     L3 对"跨度整体缩放"无判别力, 归 L1 闭合算术+facts; ②闭合补偿跨 ±5% 与墩宽 ±10%
#     的 Δw 区间重叠([0.0019,0.0029] vs [0.0010,0.0020])——Δw 只报告不硬判;
#     ③矢高比 0.45↔0.55 仅 E1 弱可见(0.969~0.970), 表/E2 盲——归 L2 网格判据;
#     ④缺 1 孔: 表孔数 −1 且 missXC 0.044~0.069, 由 count+xc 硬判。
W, H = 1200, 300   # 宽高各自独立归一化(Step 1.5: 比例失配不该由 IoU 承担)

VOID_MIN_WNORM = 0.01   # [工作值] 券洞最小归一化宽度: 主孔 8.5/150≈0.057, 栏板望柱缝 ~0.003


# ── 掩膜载入 ──

def _mask(im):
    """无 alpha 通道时的回退: RGB 亮度+饱和度双阈(简报初版; 本项目渲染图实测失效)。"""
    a = np.asarray(im.convert("RGB"), np.float32)
    lum = a.mean(axis=2)
    mx = a.max(axis=2); mn = a.min(axis=2)
    sat = (mx - mn) / (mx + 1e-6)
    # 天空: 高亮低饱和; 水: 低亮度蓝; 桥体: 中高亮度中等饱和的暖白
    return ((lum > 90) & (lum < 235) & (sat > 0.05))


def _load_render(path):
    """渲染侧: film_transparent 渲染 alpha>127 即几何剪影; 无分辨力时回退 RGB 阈值。"""
    im = Image.open(path)
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        a = np.asarray(im.convert("RGBA"))[..., 3]
        if a.min() < 128 < a.max():   # alpha 有分辨力才用
            return a > 127
    return _mask(im)


def _load_ref(path):
    """参考侧: 直接读人工掩膜(白=桥体), 禁止自动阈值。"""
    return np.asarray(Image.open(path).convert("L"), np.float32) > 127


def _load(path, is_ref):
    if is_ref:
        return _load_ref(path)
    return _load_render(path)


# ── 几何归一 ──

def solidify(mask, seal_bottom=False):
    """填实 enclosed 孔洞。参考侧按口径本就无可靠券洞(§6.2-2), 填实与两侧口径对齐。
    渲染侧 2026-10-05 二审修复后券洞为【开敞湾】(切刀贯通水面, 物理正确), 不再是
    enclosed 孔; seal_bottom=True 先把底行封 1px 使湾成封闭孔再填实, 保持与参考侧
    "拱洞计入白区" 的 IoU 口径不变(否则 17 个湾区域整体扣 IoU)。"""
    m = _crop_bbox(np.asarray(mask, bool)).copy()
    if seal_bottom:
        m[-1, :] = True
    return ndimage.binary_fill_holes(m)


def _crop_bbox(m):
    m = np.asarray(m, bool)
    ys, xs = np.where(m)
    if len(ys) == 0:
        raise ValueError("empty mask: %r" % (m.shape,))
    return m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def _norm(m):
    """按 bbox 归一化到 (W,H): 宽高各自独立缩放, 消除两图比例失配。"""
    im = Image.fromarray(_crop_bbox(m).astype(np.uint8) * 255)
    return np.asarray(im.resize((W, H), Image.BILINEAR)) > 127


def iou_silhouette(m_a, m_b):
    """实体轮廓 IoU(已归一化的两布尔掩膜)。"""
    A = _norm(m_a); B = _norm(m_b)
    return float((A & B).sum()) / max(1, float((A | B).sum()))


def overlay(path_a, path_b, out_png, a_is_ref=False, b_is_ref=True):
    """实体轮廓 IoU 比对 + 可视化。默认 argv 顺序 = (渲染图, 人工掩膜)。

    两侧均填实 enclosed 孔洞后比对(口径对齐, 见模块 docstring)。
    返回 (iou, out_png)。
    """
    ma = _norm(solidify(_load(path_a, a_is_ref), seal_bottom=not a_is_ref))
    mb = _norm(solidify(_load(path_b, b_is_ref), seal_bottom=not b_is_ref))
    inter = (ma & mb).sum(); union = (ma | mb).sum()
    iou = float(inter) / max(1, float(union))
    vis = np.zeros((H, W, 3), np.uint8)
    vis[ma & mb] = (255, 255, 255); vis[ma & ~mb] = (255, 60, 60); vis[~ma & mb] = (60, 120, 255)
    Image.fromarray(vis).save(out_png)
    return iou, out_png


# ── 券洞位置表(尺度无关) ──

def void_table(mask):
    """券洞位置表: [(xc, w), ...] 按 xc 升序。尺度无关(xc/w 均除以 bbox 宽)。

    2026-10-05 二审修复: 切刀贯通后券洞为【开敞湾】(底部开口接背景), 旧 enclosed-hole
    检测恒为 0。改判据: 背景连通域中【触底行但不触顶行】且宽>=VOID_MIN_WNORM、
    高>=15% 掩膜高者 = 一个券洞湾; 另并集保留 enclosed 孔检测(兼容旧几何)。
    负控制: 整块实心矩形掩膜 -> []; 缺一孔的掩膜 -> 16。"""
    m = _crop_bbox(mask)
    Hm, Wm = m.shape
    out = []
    bg = ~m
    lab, nlab = ndimage.label(bg, structure=np.ones((3, 3)))
    if nlab:
        slices = ndimage.find_objects(lab)
        bottom = set(lab[Hm - 1, :].tolist()) - {0}
        top = set(lab[0, :].tolist()) - {0}
        for lbl in bottom - top:
            sl = slices[lbl - 1]
            h = sl[0].stop - sl[0].start
            w = sl[1].stop - sl[1].start
            wn = float(w) / Wm
            if wn < VOID_MIN_WNORM or h < 0.15 * Hm:
                continue
            xc = (sl[1].start + sl[1].stop - 1) / 2.0 / Wm
            out.append((round(xc, 4), round(wn, 4)))
    holes = solidify(m) & ~m
    if holes.any():
        lab2, _ = ndimage.label(holes, structure=np.ones((3, 3)))
        for sl in ndimage.find_objects(lab2):
            w = sl[1].stop - sl[1].start
            wn = float(w) / Wm
            if wn < VOID_MIN_WNORM:
                continue
            xc = (sl[1].start + sl[1].stop - 1) / 2.0 / Wm
            out.append((round(xc, 4), round(wn, 4)))
    out.sort()
    return out


# ── 券洞硬判(2026-10-05 终审 I3: 文档声称的 count+xc 判定真实现进判定路径) ──

def expected_void_table(facts=None):
    """由 facts 推导期望券洞表 [(xc, w), ...], 与 void_table 同口径(尺度无关):
    xc_i = 跨 i 中心 / 桥长(桥轴局部系 -L/2..L/2 → 0..1), w_i = 跨 i 净跨 / 桥长。
    递推用 bridge3d.derive(与 bridge_geom2/qa_l2 消费同一 facts, 无第二套几何)。"""
    f = _F if facts is None else facts
    xs = _D.pier_x(f)
    sp = _D.spans(f)
    L = float(f.BRIDGE_LEN)
    return [((xs[i] + xs[i + 1]) / 2.0 / L + 0.5, w / L) for i, w in enumerate(sp)]


def void_verdict(render_mask, facts=None, tol=None):
    """券洞表硬判: 渲染侧孔数必须 == facts.N_SPAN 且逐孔 |Δxc| <= VOID_XC_TOL。
    w 只报告不硬判(标定 §7: Δw 轴两区间重叠, 无可分性 —— 诚实边界)。
    返回 (ok, problems): problems 为人读故障串列表, ok=False 时至少一条。"""
    f = _F if facts is None else facts
    t = VOID_XC_TOL if tol is None else tol
    got = void_table(render_mask)
    exp = expected_void_table(f)
    problems = []
    if len(got) != len(exp):
        problems.append("孔数 %d != facts.N_SPAN %d (render=%s exp=%s)"
                        % (len(got), len(exp),
                           [(x, w) for x, w in got], [(round(x, 4), round(w, 4)) for x, w in exp]))
        return False, problems
    for i, ((gx, gw), (ex, ew)) in enumerate(zip(got, exp)):
        if abs(gx - ex) > t:
            problems.append("孔%d xc %.4f != 期望 %.4f (|Δxc|=%.4f > %.4f)"
                            % (i + 1, gx, ex, abs(gx - ex), t))
    return (not problems), problems


if __name__ == "__main__":
    import sys
    # 用法: register_overlay.py <渲染正交图> <人工掩膜> <输出png>
    #      (默认 a=渲染侧/非ref, b=人工掩膜/ref)
    iou, out = overlay(sys.argv[1], sys.argv[2], sys.argv[3])
    print("SILHOUETTE_IOU %.4f (min %.2f) -> %s" % (iou, OVERLAY_IOU_MIN, out))
    ren_mask = _load_render(sys.argv[1])
    vt_r = void_table(ren_mask)
    vt_f = void_table(_load_ref(sys.argv[2]))
    print("VOID_TABLE render n=%d: %s" % (len(vt_r), vt_r))
    print("VOID_TABLE ref    n=%d: %s  (§6.2-2: 参考掩膜拱洞未抠空, 表仅记录不判分)" % (len(vt_f), vt_f))
    void_ok, problems = void_verdict(ren_mask)
    exp_t = expected_void_table()
    if void_ok:
        max_dx = max(abs(gx - ex) for (gx, _), (ex, _) in zip(vt_r, exp_t))
        print("VOID_VERDICT PASS (n=%d, max|Δxc|=%.4f <= %.2f)" % (len(vt_r), max_dx, VOID_XC_TOL))
    else:
        print("VOID_VERDICT FAIL: " + "; ".join(problems))
    iou_ok = iou >= OVERLAY_IOU_MIN
    print("VERDICT %s" % ("PASS" if (iou_ok and void_ok) else "FAIL"))
