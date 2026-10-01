"""L4 内容闭环：槽里的字，对不对。

旧 QA 只判「区域里有深色像素」，写错字照样通过。E11 真实发生过：
P8 口播「各占了一处」后又说树村占两处，算术自相矛盾 —— 无机器能发现。

L4 分三子层，任一不过即该槽 fail：
  L4-a 数字严格 —— 「1485」写成「1486」要能抓
  L4-b 专名严格 —— 专名表命中项必须逐个出现
  L4-c 字幕交叉 —— 与口播稿原文对数字（Task 12）

前提：E11 实测 OCR 噪声**只有标点规范化**（·→. 、，→. ），
无错字无漏字。所以不需要 fuzzy matching，数字与专名可以严格比对。
"""
import pathlib
from typing import List, Optional, Set

from qa_v2.data import Page
from qa_v2.frames import OcrResult
from qa_v2.normalize import (
    extract_numbers, normalize_punct, number_unknown_rate,
)
from qa_v2.report import Finding

NAMES = pathlib.Path(__file__).with_name("names.txt")

# 无法解析的数字 token 占比超过此值报 warn
# （防止 to_int 有 bug 却静默通过）
UNKNOWN_RATE_WARN = 0.20


def load_names(path: Optional[pathlib.Path] = None) -> Set[str]:
    """读专名表。空文件返回空 set —— 调用方须据此报 skip 而非 pass。"""
    p = pathlib.Path(path) if path else NAMES
    if not p.exists():
        return set()
    out = set()
    for line in p.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            out.add(s)
    return out


def _ocr_text_for(page: Page, ocr: OcrResult, slot_id: str) -> str:
    """取该槽内的 OCR 读回文本。"""
    from qa_v2.frames import text_at
    from qa_v2.geometry import plate_to_canvas
    slot = page.slot(slot_id)
    if slot is None:
        return ""
    rect = plate_to_canvas(page.plate, slot.x, slot.y, slot.w, slot.h)
    return "".join(t for t, _, _ in text_at(ocr, rect))


def check_l4a(page: Page, ocr: OcrResult) -> List[Finding]:
    """数字严格：原文里的每个数字都必须出现在 OCR 读回里。"""
    out = []
    for item in page.items:
        if item.is_tag:
            continue
        want = set(extract_numbers(item.text))
        if not want:
            continue
        got_raw = _ocr_text_for(page, ocr, item.slot_id)
        got = set(extract_numbers(normalize_punct(got_raw)))

        rate = number_unknown_rate(item.text)
        if rate > UNKNOWN_RATE_WARN:
            out.append(Finding(
                "L4-a", page.number, item.slot_id, "warn",
                "NUMBER_UNKNOWN_RATE",
                "数字归一失败率 %.0f%%，本槽数字比对不可信"
                % (rate * 100), {"text": item.text[:40]}))

        missing = sorted(want - got)
        if missing:
            out.append(Finding(
                "L4-a", page.number, item.slot_id, "fail",
                "NUMBER_MISMATCH",
                "数字对不上：期望 %s，读回 %s"
                % (missing, sorted(got)),
                {"expect": item.text[:50], "ocr": got_raw[:50]}))
    return out


def check_l4b(page: Page, ocr: OcrResult, names: Set[str]) -> List[Finding]:
    """专名严格：原文命中的专名必须逐个出现在 OCR 读回里。"""
    out = []
    if not names:
        out.append(Finding(
            "L4-b", None, None, "skip", "NO_NAMES_TABLE",
            "专名表为空，L4-b 未执行（不算通过）。新集需维护 qa_v2/names.txt"))
        return out
    for item in page.items:
        if item.is_tag:
            continue
        want = [n for n in names if n in item.text]
        if not want:
            continue
        got = normalize_punct(_ocr_text_for(page, ocr, item.slot_id))
        missing = [n for n in want if normalize_punct(n) not in got]
        if missing:
            out.append(Finding(
                "L4-b", page.number, item.slot_id, "fail",
                "PROPER_NAME_MISSING",
                "专名对不上：缺 %s" % "、".join(missing),
                {"expect": item.text[:50]}))
    return out
