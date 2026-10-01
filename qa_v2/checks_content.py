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
from typing import Dict, List, Optional, Set

from qa_v2.data import Episode, Page
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


# 卷号/版本号类引用：口播通常不念，不参与交叉
_VOLUME_RE = None


def _is_volume_ref(n: int) -> bool:
    """是否为卷号类引用（如《钦定八旗通志》卷116 的 116、99）。

    判据：1 <= n <= 200 且页码/卷号常见量级。E11 实测《八旗通志》卷116、
    《日下旧闻考》卷99/卷73 口播均未念。

    局限性说明：粗启发式，会漏掉小数值的内容数字；只在数字量级明显是卷号时才可靠。
    例如房数（65）、人数等小数字若口播漏念也会被豁免，这是已知假阳性/假阴性来源。
    不改成具体卷号白名单是为了保持跨集泛化性。
    """
    return 1 <= n <= 200


def check_l4c(ep: Episode, ocr_by_page: Dict[int, OcrResult]) -> List[Finding]:
    """字幕交叉：槽里的数字，必须能在该页口播稿里找到。

    **只认 narration/all.json，不认 subtitles.ts**。两个实测理由：
      1) subtitles.ts 的数字 token 大量是数组下标与行号（01…99），
         当文本 grep 会全污染；
      2) 口播有意省略书名简称（文案《钦定日下旧闻考》vs
         口播《日下旧闻考》），直接比对必然假阳性。

    这是三路交叉里最弱的一路：口播与文案本就不要求逐字一致，
    所以只对**数字**交叉，叙述性文字不查。
    """
    from qa_v2.data import narration_text

    out = []
    # Episode 类本身没有 narration 属性；测试中通过 ep.narration = {...} 动态挂载，
    # 真实运行走 narration_text(ep.name) 从 narration/all.json 读。
    narration = getattr(ep, "narration", None)
    if narration is None:
        narration = narration_text(ep.name)
    if not narration:
        out.append(Finding(
            "L4-c", None, None, "skip", "NO_NARRATION",
            "找不到 %s_video/narration/all.json，L4-c 未执行（不算通过）"
            % ep.name))
        return out

    for page in ep.pages:
        spoken = narration.get(page.number)
        if not spoken:
            continue
        spoken_nums = set(extract_numbers(spoken))
        ocr = ocr_by_page.get(page.number)
        for item in page.items:
            if item.is_tag:
                continue
            want = set(extract_numbers(item.text))
            if not want:
                continue
            # 只查「该页叙述里出现过的量级」，避免卷号（116/99）误报
            missing = sorted(
                n for n in want
                if n not in spoken_nums and not _is_volume_ref(n))
            if missing:
                out.append(Finding(
                    "L4-c", page.number, item.slot_id, "fail",
                    "NUMBER_NOT_IN_NARRATION",
                    "数字 %s 在该页口播稿里找不到" % missing,
                    {"text": item.text[:50]}))

    return out
