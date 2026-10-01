"""L3 渲染存在性、L5 溢出、L6 tag 槽。三层都需渲染帧；L3 额外依赖 OCR。

**为什么不用「区域内有深色像素」**：E11 实测负控制 —— 随手挑的
「空白区」有 583 墨像素被判为通过（落在插画深色木器上）。
该判据对插画底色敏感，板图越暗误判率越高。L3 一律用「该槽该有的文本」。
"""
from pathlib import Path
from typing import List, Optional, Set

import numpy as np
from PIL import Image
from scipy.ndimage import binary_erosion, label

from qa_v2.geometry import Rect

from qa_v2.data import Page, Slot
from qa_v2.frames import OcrResult, text_at
from qa_v2.geometry import plate_to_canvas
from qa_v2.report import Finding

TAG_IDS: Set[str] = {"evidence_tag"}

# 负控制：把槽位平移这么多 px 后必须判为空。
# 300 超过任何板面的标题带高度，不会落回真槽。
NEGATIVE_CONTROL_SHIFT: int = 300

# OCR 置信低于此值报 warn（E11 实测最低 0.350 出现在插画篆书上，
# 槽位内文字实测最低 0.828）
LOW_CONFIDENCE: float = 0.80


def check_l3(page: Page, ocr: OcrResult) -> List[Finding]:
    """槽内必须有 OCR 文本。"""
    out: List[Finding] = []
    for s in page.slots:
        if s.id in TAG_IDS:
            continue  # 深底白字，交给 L6
        rect = plate_to_canvas(page.plate, s.x, s.y, s.w, s.h)
        found = text_at(ocr, rect)
        if not found:
            out.append(Finding(
                "L3", page.number, s.id, "fail", "SLOT_RENDER_EMPTY",
                "槽内无 OCR 文本（该槽没渲出内容）",
                {"canvas_rect": list(rect)}))
            continue
        worst = min(f[2] for f in found)
        if worst < LOW_CONFIDENCE:
            out.append(Finding(
                "L3", page.number, s.id, "warn", "OCR_LOW_CONFIDENCE",
                "OCR 置信偏低 %.2f，可能字被裁切" % worst,
                {"text": found[0][0][:30], "score": round(worst, 3)}))
    return out


def assert_negative_control(
    page: Page, ocr: OcrResult, shift: int = NEGATIVE_CONTROL_SHIFT
) -> int:
    """负控制：平移槽位后应判为空。返回「未命中」的槽位数。

    判据恒真时这个数 > 0 —— 旧 QA 缺的正是这个证明。
    shift=0 会被拒绝：那等于没验证。
    """
    assert shift > 0, "负控制的平移量必须 > 0，否则等于没验证"
    not_caught = 0
    for s in page.slots:
        if s.id in TAG_IDS:
            continue
        moved = Slot(s.id, s.x + shift, s.y, s.w, s.h)
        rect = plate_to_canvas(page.plate, moved.x, moved.y,
                               moved.w, moved.h)
        if text_at(ocr, rect):
            not_caught += 1
    return not_caught


# ── L5 溢出检测 ──────────────────────────────────────────────────────

# 墨迹距槽边小于此值算触边（实测 FitText 的 padding 是 10px 12px）
TOUCH_MARGIN: int = 3
# 面积小于此值的连通域视为噪点
MIN_BLOB: int = 12


def text_bbox_in_slot(a_g: np.ndarray, rect: Rect) -> Optional[Rect]:
    """在槽位矩形内找「文字」的外接框，返回 (x, y, w, h)。

    为什么要先分离底板：槽位有 backing 底板（浅色圆角矩形 + 深色描边
    与阴影），直接量「墨迹包围盒」量到的是底板边缘 —— E11 实测两个
    溢出与否的版本量出**完全相同**的数（恒差 28px），判据失效。

    做法：亮度 <130 视为墨，二值化后腐蚀 1 像素去掉描边与阴影，
    再按连通域面积过滤掉细碎噪点。
    """
    x, y, w, h = rect
    H, W = a_g.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x1 - x0 < 4 or y1 - y0 < 4:
        return None
    sub = a_g[y0:y1, x0:x1]
    if sub.ndim == 3:
        sub = sub.mean(axis=2)
    ink = binary_erosion(sub < 130, iterations=1)
    if not ink.any():
        return None
    lab, n = label(ink)
    if n == 0:
        return None
    sizes = np.bincount(lab.ravel())
    keep_ids = [i for i in range(1, n + 1) if sizes[i] >= MIN_BLOB]
    if not keep_ids:
        return None
    keep = np.isin(lab, keep_ids)
    ys, xs = np.where(keep)
    if len(ys) == 0:
        return None
    return (int(x0 + xs.min()), int(y0 + ys.min()),
            int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1))


def check_l5(page: Page, png: Path) -> List[Finding]:
    """文字外接框触边即溢出。"""
    a = np.array(Image.open(str(png)).convert("L"))
    out: List[Finding] = []
    for s in page.slots:
        if s.id in TAG_IDS:
            continue
        rect = plate_to_canvas(page.plate, s.x, s.y, s.w, s.h)
        r = text_bbox_in_slot(a, rect)
        if r is None:
            continue  # 空槽由 L3 报，这里不重复
        tx, ty, tw, th = r
        rx, ry, rw, rh = rect
        hits = []
        if tx - rx <= TOUCH_MARGIN:
            hits.append("左")
        if ty - ry <= TOUCH_MARGIN:
            hits.append("上")
        if (rx + rw) - (tx + tw) <= TOUCH_MARGIN:
            hits.append("右")
        if (ry + rh) - (ty + th) <= TOUCH_MARGIN:
            hits.append("下")
        if hits:
            out.append(Finding(
                "L5", page.number, s.id, "fail", "TEXT_TOUCHES_SLOT_EDGE",
                "文字贴到槽边（%s），疑似被裁切" % "、".join(hits),
                {"text_rect": [tx, ty, tw, th],
                 "slot_rect": [rx, ry, rw, rh]}))
    return out
