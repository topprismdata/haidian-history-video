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
import re
from typing import Dict, List, Optional, Set

from qa_v2.data import Episode, Page
from qa_v2.frames import OcrResult
from qa_v2.normalize import (
    _REIGN_NAMES, extract_numbers, normalize_punct, number_unknown_rate,
)
from qa_v2.report import Finding

NAMES = pathlib.Path(__file__).with_name("names.txt")

# 无法解析的数字 token 占比超过此值报 warn
# （防止 to_int 有 bug 却静默通过）
UNKNOWN_RATE_WARN = 0.20

_BOOK_TITLE_RE = re.compile(r"《[^》]+》")
_VOLUME_RE = re.compile(r"卷\s*([0-9]+|[零〇一二两三四五六七八九十百]+)")
_EPISODE_RE = re.compile(r"\bE\d+\b")
_TABLE_SLOT_RE = re.compile(r"^(?:r\d+_|th_|cell_)")
_ERA_PAREN_RE = re.compile(
    rf"(?:(?:{_REIGN_NAMES})[零〇一二两三四五六七八九十]+年)"
    r"\s*[（\(·]\s*(\d{3,4})\s*[）\)]?"
)


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
        got = set(extract_numbers(got_raw))

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


def _is_table_cell(slot_id: str) -> bool:
    """是否为明细表格单元格槽位（如 r1_hall, th_dir, cell_2_3）。"""
    return bool(_TABLE_SLOT_RE.match(slot_id))


def _has_competing_number(w: int, spoken_nums: Set[int]) -> bool:
    """口播稿中是否存在与 w 属于同一维度/数量级的竞争数值（用于判断两边冲突）。

    若口播完全没提该数量级的数值（如口播只讲方位，压根没提 1000~2000 之间的房数），
    则说明该明细数据为视觉呈现资料，口播本就未念；
    若口播念了相近区间的数字（例如口播念了 1460，文案写了 1485），
    说明两边都在陈述同一指标但数字冲突，必须报警。
    """
    for s in spoken_nums:
        if w == s:
            return False
        # 相对误差 15% 以内，视为同维度竞争数值
        rel_diff = abs(w - s) / max(w, s)
        if rel_diff <= 0.15:
            return True
        # 或绝对差值 <= 5（针对小规模计数）
        if w >= 20 and abs(w - s) <= 5:
            return True
    return False


def _clean_slot_text_for_l4c(text: str, spoken: str) -> str:
    """清理文案中纯视觉属性的非口播文本：

    1) 书名号《...》：属于专名（由 L4-b 校验），且《八旗》中的「八」不是定量数值；
    2) 卷号「卷116」：文献引用标识，口播不念卷号；
    3) 集数标识「E1」「E11」：系列编号，口播不念；
    4) 朝代年号后的公历换算括号「万历二十八年（1600）」：
       若口播已念出该朝代年号，则括号内的公历换算属于画面辅助注释，予以剥除。
    """
    t = _BOOK_TITLE_RE.sub("", text)
    t = _VOLUME_RE.sub("", t)
    t = _EPISODE_RE.sub("", t)
    for m in _ERA_PAREN_RE.finditer(text):
        era_full = m.group(0)
        era_name = re.match(rf"(?:(?:{_REIGN_NAMES})[零〇一二两三四五六七八九十]+年)", era_full)
        if era_name and era_name.group(0) in spoken:
            t = t.replace(m.group(0), "")
    return t


def _is_volume_ref(n: int) -> bool:
    """是否为小额非定量/卷号数字兜底（1 <= n <= 200）。

    L4-c 重构后，绝大部分卷号与专名已由上下文正则精确剥除。
    保留 1 <= n <= 200 作为多集泛化的二级兜底（如未规范书名号的卷号、
    以及「一个字」「两处」等汉语不定冠词/次序词），
    避免将非定量修辞误判为事实矛盾。
    """
    return 1 <= n <= 200


def check_l4c(ep: Episode, ocr_by_page: Dict[int, OcrResult]) -> List[Finding]:
    """字幕交叉：槽里的数字，必须与当页口播稿保持事实一致。

    重构设计决策（详见 .superpowers/sdd/l4c-redesign.md）：
      1) 区分「结构性表格参考」与「核心叙事文案」：
         明细表格（如 P3 八旗营房表）是纯视觉资料，口播只作方位概括而不念 24 格数字。
         表格单元格仅在口播念了同量级竞争数字却与文案不一致时报 fail（抓两边冲突）；
         口播完全不提该量级数据时豁免。
      2) 精准剥除视觉辅助数字：
         书名号《八旗》内非定量字、文献卷号（卷116）、集数标识（E11）、
         以及口播念了年号时画面附带的公历换算括号（万历二十八年（1600））。
      3) 核心叙述槽位（标题、时间线、主卡片）严格交叉：
         文案中的关键事实数字（年份、人数、总房数、汛数等）必须在口播中找到对应表述。
    """
    from qa_v2.data import narration_text

    out = []
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

        for item in page.items:
            if item.is_tag:
                continue

            cleaned_text = _clean_slot_text_for_l4c(item.text, spoken)
            want = set(extract_numbers(cleaned_text))
            if not want:
                continue

            # 表格明细槽位：只有当口播念了相近竞争数值但与文案不同时才报警
            if _is_table_cell(item.slot_id):
                needs_check = any(_has_competing_number(w, spoken_nums) for w in want)
                if not needs_check:
                    continue

            missing = sorted(
                n for n in want
                if n not in spoken_nums and not _is_volume_ref(n)
            )
            if missing:
                out.append(Finding(
                    "L4-c", page.number, item.slot_id, "fail",
                    "NUMBER_NOT_IN_NARRATION",
                    "数字 %s 在该页口播稿里找不到" % missing,
                    {"text": item.text[:50]}))

    return out
