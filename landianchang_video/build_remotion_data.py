#!/usr/bin/env python3
"""从 design.md 生成 Remotion 用的 slots.json + pages.config.ts。

不手抄槽位——手抄必错（E9 教训）。直接读 design.md 里已校验过的那份。

用法：python3 build_remotion_data.py
"""
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
DESIGN = HERE / "design.md"
OUT = pathlib.Path("/tmp/chemistry-video/src/landianchang/data")

INK = "#3a3226"

# role → 默认字号 / 是否带底板
ROLE_STYLE = {
    "title":      (26, True),
    "subtitle":   (20, True),
    "note":       (20, True),
    "databar":    (18, True),
    "tag":        (20, False),   # tag 型无底板
    "span":       (24, True),
    "layertext":  (20, True),
    "celltext":   (18, True),
    "celltitle":  (22, True),
    "layertitle": (22, True),
    "year":       (20, True),
    "bignum":     (40, True),
    "quote":      (20, True),
    "band":       (22, True),
    "fest":       (26, True),
    "baseline":   (22, True),
    "closing":    (26, True),
}


def load_slots():
    text = DESIGN.read_text(encoding="utf-8")
    pages = {}
    for m in re.finditer(r'"(p0[1-8])"\s*:\s*\[(.*?)\n\]', text, re.S):
        page, body = m.group(1), m.group(2)
        slots = []
        for sm in re.finditer(r'\{[^{}]*?"id"\s*:\s*"([^"]+)"[^{}]*?\}', body, re.S):
            raw = sm.group(0)
            def num(key):
                mm = re.search(rf'"{key}"\s*:\s*(-?\d+)', raw)
                return int(mm.group(1)) if mm else 0
            um = re.search(r'"usage"\s*:\s*"((?:[^"\\]|\\.)*)"', raw)
            usage = json.loads('"' + um.group(1) + '"') if um else ""
            rm = re.search(r'"role"\s*:\s*"([^"]+)"', raw)
            vm = re.search(r'"vertical"\s*:\s*(\w+)', raw)
            slots.append({
                "id": sm.group(1), "x": num("x"), "y": num("y"),
                "w": num("w"), "h": num("h"),
                "role": rm.group(1) if rm else "note",
                "usage": usage,
                "vertical": (vm.group(1) == "true") if vm else False,
            })
        pages[page] = slots
    return pages


def main():
    pages = load_slots()
    total = sum(len(v) for v in pages.values())
    print(f"读到 {len(pages)} 页 / {total} 槽位")

    # ── slots.json（几何，只给 SlotPage 用）──
    # ⚠ **必须带 id 字段**：SlotPage 的 boxOf() 靠 find(x => x.id === ref) 定位槽位，
    #   缺 id 就永远找不到，会静默返回 10×10 的兜底框 ——
    #   FitText 在 10px 宽的框里把字压到装不下，终态帧上表现为「整页槽位空白」。
    #   （E10 实测踩中：8 页全缺，一度以为是 anchor 算错。）
    geo = {
        p: {"plate": [1920, 1080],
            "slots": [{k: s[k] for k in ("id", "x", "y", "w", "h")} for s in slots]}
        for p, slots in pages.items()
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "slots.json").write_text(
        json.dumps(geo, ensure_ascii=False, indent=1), encoding="utf-8")

    # ── pages.config.ts（文案 + 样式）──
    lines = [
        "// pages.config.ts — E10《蓝靛厂》逐页槽位文案与样式。",
        "// 由 build_remotion_data.py 从 design.md 生成，请勿手改。",
        f"// 源：{DESIGN.name}  |  {total} 槽位",
        "//",
        "// 两条纪律已内建：",
        "//  1) 页边界用 PAGE_DURATIONS_SEC（含 1.6s 留白）累加，不用 _meta.json 的 bounds。",
        "//  2) 除 tag 型外，所有压在插画上的文字一律 backing: true。",
        "",
        f'const INK = "{INK}";',
        "",
        "export const PAGE_CONFIG: Record<number, any> = {",
    ]

    for i in range(1, 9):
        key = f"p{i:02d}"
        slots = pages.get(key, [])
        lines.append(f"  // ── p{i:02d} " + "─" * 44)
        lines.append(f"  {i}: {{")
        lines.append(f"    design: {i},")
        lines.append('    bounds: [0, 0, 9999, 9999],')
        lines.append("    items: [")
        for s in slots:
            role = s["role"]
            size, backing = ROLE_STYLE.get(role, (20, True))
            if role == "tag":
                parts = [f'slotId: "{s["id"]}"', 'kind: "tag"',
                         f'text: {json.dumps(s["usage"].strip("[]"), ensure_ascii=False)}']
            else:
                parts = [f'slotId: "{s["id"]}"',
                         f'text: {json.dumps(s["usage"], ensure_ascii=False)}',
                         f"size: {size}", f'color: "{INK}"', "weight: 800", "lh: 1.4"]
                if backing:
                    parts.append("backing: true")
            if s["vertical"]:
                parts.append("vertical: true")
            lines.append("      { " + ", ".join(parts) + " },")
        lines.append("    ],")
        lines.append("  },")
    lines.append("};")
    lines.append("")
    (OUT / "pages.config.ts").write_text("\n".join(lines), encoding="utf-8")

    print(f"已生成：\n  {OUT / 'slots.json'}\n  {OUT / 'pages.config.ts'}")


if __name__ == "__main__":
    main()
