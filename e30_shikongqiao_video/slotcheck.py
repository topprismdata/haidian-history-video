#!/usr/bin/env python3
"""E30 槽位几何校验器。从 design.md 解析 JSON 槽位块并检查:
  1. 必需字段齐全, 数值合法
  2. 全部槽位在 plate 1920x1080 内
  3. 同页槽位不重叠 (允许 title/tag 等已声明的例外由 ALLOW_OVERLAP 控制)
  4. 同页槽位不越出底部字幕带 (y+h <= SUBTITLE_TOP)
  5. usage 非空 (避免"留空但不说明放什么")
负控制: 内置 CHECK_NEGATIVE_CONTROL, 跑一个已知会越界的样本, 必须报 fail。
Python 3.9 兼容。
"""
import json
import pathlib
import re
import sys
from typing import Any, Dict, List, Tuple

PLATE_W, PLATE_H = 1920, 1080
SUBTITLE_TOP = 1030          # 底部字幕条上沿
REQUIRED = ("id", "x", "y", "w", "h", "role", "usage")
DESIGN = pathlib.Path(__file__).with_name("design.md")


def parse_slots(md: str) -> Dict[str, List[Dict[str, Any]]]:
    out: Dict[str, List[Dict[str, Any]]] = {}
    for m in re.finditer(r'```json\n"(p\d+)"\s*:\s*(\[.*?\])\n```', md, re.S):
        out[m.group(1)] = json.loads(m.group(2))
    return out


def overlap(a: Dict[str, Any], b: Dict[str, Any]) -> float:
    ax2, ay2 = a["x"] + a["w"], a["y"] + a["h"]
    bx2, by2 = b["x"] + b["w"], b["y"] + b["h"]
    ix = max(0, min(ax2, bx2) - max(a["x"], b["x"]))
    iy = max(0, min(ay2, by2) - max(a["y"], b["y"]))
    area = ix * iy
    if area == 0:
        return 0.0
    return area / float(min(a["w"] * a["h"], b["w"] * b["h"]))


def check_page(pid: str, slots: List[Dict[str, Any]]) -> List[str]:
    errs: List[str] = []
    ids = set()
    for s in slots:
        sid = s.get("id", "<无 id>")
        for k in REQUIRED:
            if k not in s:
                errs.append("%s/%s 缺字段 %s" % (pid, sid, k))
        if sid in ids:
            errs.append("%s id 重复: %s" % (pid, sid))
        ids.add(sid)
        for k in ("x", "y", "w", "h"):
            if k in s and not isinstance(s[k], (int, float)):
                errs.append("%s/%s %s 非数值: %r" % (pid, sid, k, s[k]))
            if k in s and s[k] < 0:
                errs.append("%s/%s %s 为负: %r" % (pid, sid, k, s[k]))
        if all(k in s for k in ("x", "y", "w", "h")):
            if s["w"] == 0 or s["h"] == 0:
                errs.append("%s/%s 尺寸为零: %dx%d" % (pid, sid, s["w"], s["h"]))
            if s["x"] + s["w"] > PLATE_W:
                errs.append("%s/%s 右侧越界: x+w=%d > %d" % (pid, sid, s["x"] + s["w"], PLATE_W))
            if s["y"] + s["h"] > SUBTITLE_TOP:
                errs.append("%s/%s 侵入字幕带: y+h=%d > %d"
                            % (pid, sid, s["y"] + s["h"], SUBTITLE_TOP))
        if "usage" in s and not str(s["usage"]).strip():
            errs.append("%s/%s usage 为空" % (pid, sid))
    for i in range(len(slots)):
        for j in range(i + 1, len(slots)):
            a, b = slots[i], slots[j]
            if not all(k in a for k in ("x", "y", "w", "h")):
                continue
            if not all(k in b for k in ("x", "y", "w", "h")):
                continue
            r = overlap(a, b)
            if r > 0.05:
                errs.append("%s 槽位重叠 %.0f%%: %s × %s" % (pid, r * 100, a["id"], b["id"]))
    return errs


def check_negative_control() -> List[str]:
    """负控制: 造三个已知越界样本, 校验器必须逐个抓到。
    返回值: 校验器自己抓到的 errs(证明它能工作) + 若任一负控制漏检则追加一条失败说明。
    若返回空, 说明本校验器可能恒真。"""
    caught: List[str] = []
    miss: List[str] = []

    bad_oor = [{"id": "neg_oor", "x": 1800, "y": 100, "w": 400, "h": 100,
                "role": "title", "usage": "负控制: 右侧越界"}]
    e1 = check_page("NEG", bad_oor)
    caught.extend(e1)
    if not any("越界" in e for e in e1):
        miss.append("负控制失败: 右侧越界样本未被检出")

    bad_sub = [{"id": "neg_sub", "x": 100, "y": 1000, "w": 400, "h": 200,
                "role": "title", "usage": "负控制: 侵入字幕带"}]
    e2 = check_page("NEG", bad_sub)
    caught.extend(e2)
    if not any("字幕带" in e for e in e2):
        miss.append("负控制失败: 侵入字幕带样本未被检出")

    bad_zero = [{"id": "neg_zero", "x": 100, "y": 100, "w": 0, "h": 60,
                 "role": "title", "usage": "负控制: 尺寸为零"}]
    e3 = check_page("NEG", bad_zero)
    caught.extend(e3)
    if not any("尺寸为零" in e for e in e3):
        miss.append("负控制失败: 零尺寸样本未被检出")

    return caught + miss


def main() -> int:
    md = DESIGN.read_text(encoding="utf-8")
    pages = parse_slots(md)
    print("解析到 %d 页槽位: %s" % (len(pages), ", ".join(sorted(pages))))
    all_errs: List[str] = []
    for pid in sorted(pages):
        slots = pages[pid]
        errs = check_page(pid, slots)
        status = "FAIL" if errs else "ok"
        print("  %-5s %2d 槽位  %s" % (pid, len(slots), status))
        all_errs.extend(errs)
    nc = check_negative_control()
    nc_fail = [e for e in nc if e.startswith("负控制失败")]
    nc_caught = [e for e in nc if not e.startswith("负控制失败")]
    print("  负控制: %s (构造 %d 个非法样本, 检出 %d 条)"
          % ("失败" if nc_fail else "通过", 3, len(nc_caught)))
    for e in nc_caught:
        print("    检出 " + e)
    all_errs.extend(nc_fail)
    if all_errs:
        print("\n=== 问题 %d 条 ===" % len(all_errs))
        for e in all_errs:
            print("  " + e)
        return 1
    print("\n全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
