"""L1 数据一致性 + L2 几何可行性。纯数据，不渲帧，<0.2s/页。

L1 抓的是「静默失败」——最阴的一类：数据不匹配时代码仍能跑，
只是默默返回一个兜底值，最终表现为「某槽空白」或「文字飞到画外」。
E11 实测踩中：badge→evidence_tag 改名后文案侧漏改，
boxOf 找不到槽位却静默返回 10×10 兜底框。
"""
from typing import List

from qa_v2.data import Episode
from qa_v2.geometry import overlap_ratio, out_of_bounds
from qa_v2.report import Finding

# 交叠面积占较小者的比例达到此值算 fail（边框相邻不算叠）
OVERLAP_FAIL_RATIO = 0.05
# 槽位尺寸下限：低于此值基本装不下任何文字
MIN_SLOT_W = 40
MIN_SLOT_H = 20


def check_l1(ep: Episode) -> List[Finding]:
    """数据一致性。返回 List[Finding]。"""
    out = []
    if len(ep.pages) != len(ep.layout):
        out.append(Finding(
            "L1", None, None, "fail", "PAGE_COUNT_MISMATCH",
            "页数与页长表不符：%d 页 vs %d 项"
            % (len(ep.pages), len(ep.layout))))

    for page in ep.pages:
        have = set(s.id for s in page.slots)
        used = set(i.slot_id for i in page.items)

        for i in page.items:
            if i.slot_id not in have:
                out.append(Finding(
                    "L1", page.number, i.slot_id, "fail",
                    "TEXT_REFERENCES_MISSING_SLOT",
                    "文案引用了不存在的槽位（渲染时会静默走兜底框）",
                    {"text": i.text[:40]}))

        for s in page.slots:
            if s.id not in used:
                out.append(Finding(
                    "L1", page.number, s.id, "fail", "SLOT_WITHOUT_TEXT",
                    "槽位没有被任何文案引用（静默空洞）"))

            if out_of_bounds(s.rect, page.plate):
                out.append(Finding(
                    "L1", page.number, s.id, "fail", "SLOT_OUT_OF_BOUNDS",
                    "槽位越出板面 %dx%d" % page.plate,
                    {"rect": list(s.rect)}))

            if s.w < MIN_SLOT_W or s.h < MIN_SLOT_H:
                out.append(Finding(
                    "L1", page.number, s.id, "warn", "SLOT_TOO_SMALL",
                    "槽位过小，可能是改名后残留的旧坐标",
                    {"w": s.w, "h": s.h}))

        for i in range(len(page.slots)):
            for j in range(i + 1, len(page.slots)):
                a, b = page.slots[i], page.slots[j]
                r = overlap_ratio(a.rect, b.rect)
                if r >= OVERLAP_FAIL_RATIO:
                    out.append(Finding(
                        "L1", page.number, a.id, "fail", "SLOT_OVERLAP",
                        "与 %s 交叠 %.0f%%" % (b.id, r * 100),
                        {"other": b.id, "ratio": round(r, 3)}))
    return out


# ── L2 几何可行性（渲染前预检）────────────────────────────────────────

# 需要高度超过槽高此倍数才报 warn（FitText 内部有自适应缩放，
# 真实溢出点略高于理论值，1.15 是实测留的容差）
OVERFLOW_TOLERANCE = 1.15

# 单个汉字的宽度约等于字号；ASCII 约 0.55 倍
_WIDE = 1.0
_NARROW = 0.55


def _text_units(s: str) -> float:
    """估算文本的"字宽单位"：汉字 1.0，ASCII 0.55。"""
    n = 0.0
    for ch in s:
        n += _NARROW if ord(ch) < 128 else _WIDE
    return n


def estimate_lines(text: str, slot_w: float, size: int) -> int:
    """估算渲染后占几行。与 FitText 的 effW 同口径（宽字符算 1，窄字符 0.45~0.55）。"""
    if not text or size <= 0:
        return 0
    per_line = max(1.0, float(slot_w) / float(size))
    if "\n" in text:
        return sum(
            max(1, int(-(-_text_units(l) // per_line)))
            for l in text.split("\n")
            if l.strip()
        )
    return max(1, int(-(-_text_units(text) // per_line)))


def item_lh(item, default: float = 1.4) -> float:
    """获取文本项的行高倍数。

    说明：TextItem 当前 __slots__ 未包含 lh 字段，故真实 TextItem 对象上
    getattr(item, "lh", None) 会返回 None 并回退到 default (1.4)。
    保留 getattr 是为了防御性兼容未来扩展或带 lh 属性的测试 mock 对象。
    """
    return getattr(item, "lh", None) or default


def check_l2(ep: Episode) -> List[Finding]:
    """渲染前的溢出预检。装不下就 warn，省得渲完再靠眼睛找。"""
    out = []
    for page in ep.pages:
        for item in page.items:
            slot = page.slot(item.slot_id)
            if slot is None or slot.h <= 0 or item.size <= 0:
                continue
            lines = estimate_lines(item.text, slot.w, item.size)
            if lines <= 0:
                continue
            need = lines * item.size * item_lh(item)
            ratio = need / float(slot.h)
            if ratio > OVERFLOW_TOLERANCE:
                out.append(Finding(
                    "L2", page.number, item.slot_id, "warn",
                    "ESTIMATED_OVERFLOW",
                    "预计需 %.0fpx / 槽高 %dpx（%d 行 @%dpx）"
                    % (need, slot.h, lines, item.size),
                    {"ratio": round(ratio, 2), "lines": lines}))
    return out
