#!/usr/bin/env python3
"""E10 槽位几何校验器 —— 三层检查，设计阶段就跑，不渲帧。

教训来源（E9）：E8 因为跳过这一步，白渲染 2 版才修完 6 处缺陷。
E9 因为漏了第三层（字幕带），5 处槽位被压住，白渲 1 版。

用法：
    python3 slotcheck.py                 # 校验 design.md 里的全部槽位
    python3 slotcheck.py --json          # 输出 JSON，供下游生成脚本消费
"""
import json
import re
import sys
import pathlib

DESIGN = pathlib.Path(__file__).with_name("design.md")

# Caption 固定 bottom:8；内边距 14+14；字号 40；lh 1.4  ->  高约 84px
# 1920x1080 下：底边 8 + 84 = 92 ->  顶边 1080-92 = 988
CAPTION_BAND = (0, 988, 1920, 1080)

# 面积重叠超过较小槽位的这个比例即判冲突
OVERLAP_RATIO = 0.12

# 刻意堆叠的槽位对（"匾额+题款""轴标签+年份"这类）
EXEMPT = {
    frozenset(("plaque_text", "plaque_note")),
    frozenset(("inner_note", "outer_note")),
}


def load_slots():
    """从 design.md 的 json 代码块里抽出各页槽位。"""
    text = DESIGN.read_text(encoding="utf-8")
    pages = {}
    for m in re.finditer(r'"(p0[1-8])"\s*:\s*\[(.*?)\n\s*\]', text, re.S):
        page, body = m.group(1), m.group(2)
        slots = []
        # 每个槽位是一个 {...} 块；usage 里可能有转义引号但不含裸花括号
        for sm in re.finditer(r'\{[^{}]*?"id"\s*:\s*"([^"]+)"[^{}]*?\}', body, re.S):
            raw = sm.group(0)
            x = int(re.search(r'"x"\s*:\s*(-?\d+)', raw).group(1))
            y = int(re.search(r'"y"\s*:\s*(-?\d+)', raw).group(1))
            w = int(re.search(r'"w"\s*:\s*(-?\d+)', raw).group(1))
            h = int(re.search(r'"h"\s*:\s*(-?\d+)', raw).group(1))
            usage = re.search(r'"usage"\s*:\s*"((?:[^"\\]|\\.)*)"', raw)
            slots.append({
                "id": sm.group(1), "x": x, "y": y, "w": w, "h": h,
                "usage": json.loads('"' + usage.group(1) + '"') if usage else "",
            })
        pages[page] = slots
    return pages


def inter(a, b):
    ax, ay, aw, ah = a["x"], a["y"], a["w"], a["h"]
    bx, by, bw, bh = b["x"], b["y"], b["w"], b["h"]
    ix = max(0, min(ax + aw, bx + bw) - max(ax, bx))
    iy = max(0, min(ay + ah, by + bh) - max(ay, by))
    return ix * iy


def check(pages):
    issues, warns = [], []
    for page, slots in sorted(pages.items()):
        if not slots:
            issues.append(f"{page}: 没有解析到槽位")
            continue

        # 0. 零尺寸 / 出界
        for s in slots:
            if s["w"] <= 0 or s["h"] <= 0:
                issues.append(f"{page}/{s['id']}: 零尺寸 {s['w']}x{s['h']}")
            if s["x"] < 0 or s["y"] < 0 or s["x"] + s["w"] > 1920 or s["y"] + s["h"] > 1080:
                issues.append(
                    f"{page}/{s['id']}: 出界 "
                    f"({s['x']},{s['y']},{s['x']+s['w']},{s['y']+s['h']})")
            if not s["usage"].strip():
                warns.append(f"{page}/{s['id']}: usage 为空（槽位会渲出空白）")

        # 1. 矩形两两相交
        for i in range(len(slots)):
            for j in range(i + 1, len(slots)):
                a, b = slots[i], slots[j]
                if frozenset((a["id"], b["id"])) in EXEMPT:
                    continue
                ov = inter(a, b)
                if ov == 0:
                    continue
                small = min(a["w"] * a["h"], b["w"] * b["h"])
                if small and ov / small > OVERLAP_RATIO:
                    issues.append(
                        f"{page}: 「{a['id']}」x「{b['id']}」重叠 "
                        f"{ov/small*100:.0f}%")

        # 2. 字幕带冲突（矩形相交检测看不见它）
        cap = {"id": "Caption", "x": CAPTION_BAND[0], "y": CAPTION_BAND[1],
               "w": CAPTION_BAND[2], "h": CAPTION_BAND[3] - CAPTION_BAND[1]}
        for s in slots:
            if s["id"] in ("evidence_tag",):
                continue
            ov = inter(s, cap)
            if ov:
                small = s["w"] * s["h"]
                if small and ov / small > 0.05:
                    issues.append(
                        f"{page}/{s['id']}: 被字幕带压住 "
                        f"（y {s['y']}~{s['y']+s['h']} 深入 y>988）")
    return issues, warns


if __name__ == "__main__":
    pages = load_slots()
    if "--json" in sys.argv:
        print(json.dumps(pages, ensure_ascii=False, indent=2))
        sys.exit(0)

    # ⚠ 硬断言：解析不到槽位必须报错，不能静默"通过"。
    #   design.md 为空、或 JSON 块写法变了，都会落到这里。
    total = sum(len(v) for v in pages.values())
    if not pages or total == 0:
        print("X 未从 design.md 解析到任何槽位。", file=sys.stderr)
        print("  检查 design.md 是否含形如  \"p01\": [ ... ]  的 JSON 块。", file=sys.stderr)
        sys.exit(1)
    if len(pages) < 8:
        print(f"X 只解析到 {len(pages)}/8 页（缺 {8 - len(pages)} 页）", file=sys.stderr)
        sys.exit(1)

    for p in sorted(pages):
        print(f"  {p}: {len(pages[p])} 槽位")
    print(f"合计 {total} 槽位\n")

    issues, warns = check(pages)
    if warns:
        print("提示：")
        for w in warns:
            print(f"  ! {w}")
        print()
    if issues:
        print("冲突：")
        for s in issues:
            print(f"  X {s}")
        sys.exit(1)
    print("零相交、零字幕带冲突、零出界 —— 通过")
