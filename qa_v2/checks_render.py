"""L3 渲染存在性、L5 溢出、L6 tag 槽。三层都需渲染帧；L3 额外依赖 OCR。

**为什么不用「区域内有深色像素」**：E11 实测负控制 —— 随手挑的
「空白区」有 583 墨像素被判为通过（落在插画深色木器上）。
该判据对插画底色敏感，板图越暗误判率越高。L3 一律用「该槽该有的文本」。
"""
from typing import List, Set

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
