"""验收结论的表示与输出。

level 语义（只有 fail 阻塞退出码，见 spec §10.2）：
  fail —— 违反判据，必须修
  warn —— 可疑但可能是判据过严，不阻塞
  skip —— 该判据因缺前置数据未执行（如专名表未维护），**不算通过**
  info —— 补充信息
"""
import json
from typing import Dict, List, Optional

LEVELS = ("fail", "warn", "skip", "info")


class Finding(object):
    __slots__ = ("layer", "page", "slot", "level", "code", "message", "detail")

    def __init__(
        self,
        layer: str,
        page: Optional[int],
        slot: Optional[str],
        level: str,
        code: str,
        message: str,
        detail: Optional[dict] = None,
    ):
        assert level in LEVELS, "未知 level: %r" % level
        self.layer = layer
        self.page = page
        self.slot = slot
        self.level = level
        self.code = code
        self.message = message
        self.detail = detail

    def to_dict(self) -> dict:
        return {
            "layer": self.layer,
            "page": self.page,
            "slot": self.slot,
            "level": self.level,
            "code": self.code,
            "message": self.message,
            "detail": self.detail,
        }

    def __repr__(self) -> str:
        return "Finding(%s, p%s, %s, %s, %s)" % (
            self.layer,
            self.page,
            self.slot,
            self.level,
            self.code,
        )


def summarize(findings: List[Finding]) -> Dict[str, int]:
    out = dict((lv, 0) for lv in LEVELS)
    for f in findings:
        out[f.level] += 1
    return out


_ICON = {"fail": "✗", "warn": "⚠", "skip": "–", "info": "·"}


def render_text(findings: List[Finding], ep: str) -> str:
    s = summarize(findings)
    lines = ["=== %s ===" % ep]
    if not findings:
        lines.append("  全部通过，无发现")
    else:
        order = {"fail": 0, "warn": 1, "skip": 2, "info": 3}
        for f in sorted(
            findings,
            key=lambda x: (order.get(x.level, 9), x.layer, x.page or 0),
        ):
            where = "P%s" % f.page if f.page else "-"
            slot = f.slot or "-"
            lines.append(
                "  %s [%s] %s/%s  %s"
                % (_ICON.get(f.level, "?"), f.level, where, slot, f.message)
            )
            if f.detail:
                for k, v in sorted(f.detail.items()):
                    lines.append("        %s=%s" % (k, v))
    tail = "  -> fail %d / warn %d / skip %d / info %d" % (
        s["fail"],
        s["warn"],
        s["skip"],
        s["info"],
    )
    lines.append(tail)
    lines.append("  判定：" + ("不通过" if s["fail"] else "通过"))
    return "\n".join(lines)


def render_json(findings: List[Finding], ep: str) -> str:
    return json.dumps(
        {
            "episode": ep,
            "summary": summarize(findings),
            "findings": [f.to_dict() for f in findings],
        },
        ensure_ascii=False,
        indent=1,
    )
