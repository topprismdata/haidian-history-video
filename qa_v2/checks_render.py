"""L3 渲染存在性、L5 溢出、L6 tag 槽。三层都需渲染帧；L3 额外依赖 OCR。

**为什么不用「区域内有深色像素」**：E11 实测负控制 —— 随手挑的
「空白区」有 583 墨像素被判为通过（落在插画深色木器上）。
该判据对插画底色敏感，板图越暗误判率越高。L3 一律用「该槽该有的文本」。
"""
from pathlib import Path
from typing import List, Optional, Sequence, Set

import numpy as np
from PIL import Image
from scipy.ndimage import binary_erosion, label

from qa_v2.data import Page, Slot
from qa_v2.frames import OcrResult, text_at
from qa_v2.geometry import Rect, plate_to_canvas
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

class NegativeControlResult(int):
    """负控制结果：继承 int（值为 not_caught，兼容 bool 与 == 0 判断）。

    同时记录 untestable（无法在板面上找到不撞任何槽位的空白区而被跳过的槽数）。
    """
    not_caught: int
    untestable: int

    def __new__(cls, not_caught: int, untestable: int = 0):
        obj = super().__new__(cls, not_caught)
        obj.not_caught = not_caught
        obj.untestable = untestable
        return obj

    def __str__(self) -> str:
        return str(self.not_caught)

    def __repr__(self) -> str:
        return (f"NegativeControlResult(not_caught={self.not_caught}, "
                f"untestable={self.untestable})")

    def __iter__(self):
        yield self.not_caught
        yield self.untestable


def _intersects(r1: Rect, r2: Rect) -> bool:
    x1, y1, w1, h1 = r1
    x2, y2, w2, h2 = r2
    return max(x1, x2) < min(x1 + w1, x2 + w2) and max(y1, y2) < min(y1 + h1, y2 + h2)


def _find_negative_control_rect(
    slot: Slot, all_slots: Sequence[Slot], plate: Sequence[int], shift: int
) -> Optional[Rect]:
    """寻找与所有真槽及自身原矩形均不相交且在板面内的负控制平移矩形。"""
    orig: Rect = (int(slot.x), int(slot.y), int(slot.w), int(slot.h))
    all_rects = [(int(s.x), int(s.y), int(s.w), int(s.h)) for s in all_slots]
    pw, ph = plate[0], plate[1]

    candidate_shifts = [
        (shift, 0),
        (-shift, 0),
        (0, shift),
        (0, -shift),
        (int(slot.w + 50), 0),
        (-int(slot.w + 50), 0),
        (0, int(slot.h + 50)),
        (0, -int(slot.h + 50)),
        (shift, shift),
        (-shift, shift),
        (shift, -shift),
        (-shift, -shift),
        (2 * shift, 0),
        (-2 * shift, 0),
        (0, 2 * shift),
        (0, -2 * shift),
        (shift // 2, 0),
        (-shift // 2, 0),
        (0, shift // 2),
        (0, -shift // 2),
    ]

    seen = set()
    for dx, dy in candidate_shifts:
        if (dx, dy) == (0, 0) or (dx, dy) in seen:
            continue
        seen.add((dx, dy))
        cand: Rect = (int(slot.x + dx), int(slot.y + dy), int(slot.w), int(slot.h))
        if cand[0] < 0 or cand[1] < 0 or cand[0] + cand[2] > pw or cand[1] + cand[3] > ph:
            continue
        if _intersects(cand, orig):
            continue
        if any(_intersects(cand, other) for other in all_rects):
            continue
        return cand

    # 回退到网格搜索（步长 100）
    for dy in [0, 100, -100, 200, -200, 300, -300, 400, -400, 500, -500]:
        for dx in [0, 100, -100, 200, -200, 300, -300, 400, -400, 500, -500]:
            if (dx, dy) == (0, 0) or (dx, dy) in seen:
                continue
            seen.add((dx, dy))
            cand = (int(slot.x + dx), int(slot.y + dy), int(slot.w), int(slot.h))
            if cand[0] < 0 or cand[1] < 0 or cand[0] + cand[2] > pw or cand[1] + cand[3] > ph:
                continue
            if _intersects(cand, orig):
                continue
            if any(_intersects(cand, other) for other in all_rects):
                continue
            return cand

    return None


def assert_negative_control(
    page: Page, ocr: OcrResult, shift: int = NEGATIVE_CONTROL_SHIFT
) -> NegativeControlResult:
    """负控制：平移槽位后应判为空。返回 NegativeControlResult(not_caught, untestable)。

    要求：
    1. 平移落点与所有真槽及自身原矩形不相交。若撞了就换方向/加大位移；
    2. 实在无法构造的槽，跳过并计入 untestable（不计入 not_caught）；
    3. 负控制路径上 text_at 的 pad 置 0；
    4. 继承 int，兼容 if missed: 与 == 0 判断；
    5. 负控制判定应与 L3 正向存在性判定标准对称，忽略置信低于 LOW_CONFIDENCE 的背景插画噪点。
    """
    assert shift > 0, "负控制的平移量必须 > 0，否则等于没验证"
    not_caught = 0
    untestable = 0
    for s in page.slots:
        if s.id in TAG_IDS:
            continue
        cand = _find_negative_control_rect(s, page.slots, page.plate, shift)
        if cand is None:
            untestable += 1
            continue
        rect = plate_to_canvas(page.plate, cand[0], cand[1], cand[2], cand[3])
        found = [f for f in text_at(ocr, rect, pad=0) if f[2] >= LOW_CONFIDENCE]
        if found:
            not_caught += 1
    return NegativeControlResult(not_caught=not_caught, untestable=untestable)

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


# ── L6 tag 槽 ────────────────────────────────────────────────────────

# 白字阈值（深底白字反白样式）
WHITE_MIN: int = 200
# 白像素占比上限：超过说明抓到的是浅色底板而非文字块
WHITE_MAX_RATIO: float = 0.40
# 白像素占比下限：低于说明槽里没东西
WHITE_MIN_RATIO: float = 0.01


def check_l6(page: Page, png: Path) -> List[Finding]:
    """tag 型槽（深底白字）的独立判据。

    旧 qa_all.py 用 TAG_IDS 把这类槽直接排除 —— 于是**证据标签
    从不被检查**。E11 实测 8 个 evidence_tag 槽全部有值
    （[文献记载]/[官书记载]/[存疑待考]/[原书记载]/[实录记载]/[系列联动]），
    说明判据可用。
    """
    a = np.array(Image.open(str(png)).convert("RGB"))
    out: List[Finding] = []
    for s in page.slots:
        items = [i for i in page.items if i.slot_id == s.id]
        if not items or not items[0].is_tag:
            continue
        rect = plate_to_canvas(page.plate, s.x, s.y, s.w, s.h)
        rx, ry, rw, rh = rect
        H, W = a.shape[:2]
        x1, y1 = min(W, rx + rw), min(H, ry + rh)
        sub = a[max(0, ry):y1, max(0, rx):x1]
        if sub.size == 0:
            continue
        white = (sub.min(axis=2) > WHITE_MIN).mean()
        if white < WHITE_MIN_RATIO:
            out.append(Finding(
                "L6", page.number, s.id, "fail", "TAG_SLOT_EMPTY",
                "证据标签槽内无白字（tag 是深底白字，此槽未渲染）",
                {"white_ratio": round(float(white), 4)}))
        elif white > WHITE_MAX_RATIO:
            out.append(Finding(
                "L6", page.number, s.id, "warn", "TAG_SLOT_ALL_WHITE",
                "槽内几乎全白，可能抓错区域",
                {"white_ratio": round(float(white), 4)}))
    return out
