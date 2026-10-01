#!/usr/bin/env python3
"""把新配音的实测时长写回 Remotion 工程的时间数据。

配音变短 → 页长必须跟着变，否则画面会在音频结束后留空，
且 SlotPage 的 audioBeats 会按旧音频算槽位入场 anchor，末两项赶不上终态帧
（表现为终态帧上整页槽位空白）。

要改四处（E5–E10 各自不同，且同一集内写法也不统一）：
  * pageMap.ts   的 PAGE_DURATIONS_SEC 与 AUDIO_MEASURED_SEC（E8–E10）
  * pageMap.ts   的 TOTAL_FRAMES（E10 独有）
  * narration.ts 的 PAGE_AUDIO_SEC（E10 的 audioBeats 消费它，纯音频口径）
  * narration.json 的 pages[].pageLenSec 与 beats[].durSec（E5–E7，E8/E9 也有）

[NOTE] subtitles.ts **不在本脚本范围内**：字幕 `from`/`dur` 是按旁白逐句对齐的
     （每页 `from` 累加 = 该页纯音频时长），换配音必须人工按新断句重写，
     不能按字数比例摊 —— 比例摊会把断句位置冲掉。
     2026-10-01 曾试过按字数比例重分配，其正则会吃掉页尾 "],"
     并写出缩进不自洽的内容，六集文件全被写坏（esbuild 直接编译失败）。
"""
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path("/tmp/chemistry-video/src")
AUDIO = pathlib.Path("/Volumes/macstudio/video-projects/audio_new")
GAP = 1.6
EPS = ["yimuyuan", "niangniangfu", "xisanqi", "gaoliangqiao", "dazhongsi", "landianchang"]


def measure(ep):
    """实测 8 段纯音频时长。"""
    out = []
    for i in range(1, 9):
        f = AUDIO / ep / f"p{i:02d}.wav"
        if not f.exists():
            sys.exit(f"{ep}: 缺 {f}")
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(f)], capture_output=True, text=True)
        out.append(round(float(r.stdout.strip()), 2))
    return out


def fix_page_map(ep, aud, pages):
    """改 pageMap.ts 的 PAGE_DURATIONS_SEC / AUDIO_MEASURED_SEC。

    [WARN] PAGE_DURATIONS_SEC 有两种写法，必须都覆盖：
      单行：export const PAGE_DURATIONS_SEC = [21.6, 24.24, ...]
      多行带注释：export const PAGE_DURATIONS_SEC = [
        23.2,  // p01
        27.28, // p02
      ]
    只写单行正则的话，多行那种会静默不改 —— E10 实测踩中。
    （槽位验收会因页长未更新而全页错位。）
    """
    f = ROOT / ep / "data" / "pageMap.ts"
    if not f.exists():
        return False
    s = f.read_text(encoding="utf-8")
    orig = s
    fmt = lambda xs: ", ".join(f"{x:g}" for x in xs)
    # 多行（带 // pNN 注释）优先，保持原有排版风格
    s = re.sub(r"(PAGE_DURATIONS_SEC\s*(?::[^=]+)?=\s*)\[(.*?)\]",
               lambda m: m.group(1) + "[\n"
               + "".join(f"  {x:g},  // p{i+1:02d}\n" for i, x in enumerate(pages))
               + "]", s, flags=re.S)
    s = re.sub(r"(PAGE_DURATIONS_SEC: number\[\] = )\[[^\]]*\]",
               lambda m: m.group(1) + "[" + fmt(pages) + "]", s)
    s = re.sub(r"(AUDIO_MEASURED_SEC(?::[^=]+)?=\s*)\[(.*?)\]",
               lambda m: m.group(1) + "[" + fmt(aud) + "]", s, flags=re.S)
    s = re.sub(r"// 来源：.*",
               "// 来源：新配音实测音频时长 + 1.6s 页尾留白（2026-10-01 换音色后重测）。", s)
    s = re.sub(r"与 audio_qwen/PNN_000\.wav 一一对应", "与 audio_new/PNN.wav 一一对应", s)
    if s == orig:
        return False
    f.write_text(s, encoding="utf-8")
    return True


def fix_narration_ts(ep, aud):
    """E10 用 narration.ts 的 PAGE_AUDIO_SEC（纯音频，帧口径消费）。

    [WARN] 等号**前后都有空格**：`const PAGE_AUDIO_SEC = [21.6, ...]`。
    正则里 `(?::[^=]+)?=\\s*` 漏了等号前的空格，`[^=]+` 也不会匹配空格 ——
    结果整条静默不匹配，页长不更新而 anchor 仍按旧音频算，
    表现为 P3/P5 各少渲 1 个槽位。
    """
    f = ROOT / ep / "data" / "narration.ts"
    if not f.exists():
        return False
    s = f.read_text(encoding="utf-8")
    s2 = re.sub(r"(\bPAGE_AUDIO_SEC\s*(?::[^=]+?)?=\s*)\[[^\]]*\]",
                lambda m: m.group(1) + "[" + ", ".join(f"{x:g}" for x in aud) + "]", s)
    s2 = re.sub(r"(// 由实测 wav 时长生成。)",
                r"\1（2026-10-01 换音色后重测）。", s2)
    if s2 == s:
        return False
    f.write_text(s2, encoding="utf-8")
    return True


def fix_total_frames(ep, pages):
    """E10 pageMap.ts 末尾有 TOTAL_FRAMES，页长变了必须跟着改。"""
    f = ROOT / ep / "data" / "pageMap.ts"
    if not f.exists():
        return False
    s = f.read_text(encoding="utf-8")
    total = sum(round(p * 30) for p in pages)
    s2 = re.sub(r"(export const TOTAL_FRAMES\s*(?::[^=]+?)?=\s*)\d+",
                lambda m: m.group(1) + str(total), s)
    if s2 == s:
        return False
    f.write_text(s2, encoding="utf-8")
    return True


def fix_narration_json(ep, aud, pages):
    """改 narration.json 的 pageLenSec / beats[].durSec。

    [WARN] 这里必须比对**序列化后**的文本再判改动。
    早期版本无条件 json.dump 然后 return True，报告列永远显示「改」，
    掩盖了真实状态 —— 报告列若不可信就等于没有报告。
    """
    f = ROOT / ep / "data" / "narration.json"
    if not f.exists():
        return False
    orig = f.read_text(encoding="utf-8")
    d = json.loads(orig)
    for p in d["pages"]:
        n = p["page"]
        p["pageLenSec"] = pages[n - 1]
        for b in p.get("beats", []):
            b["durSec"] = aud[n - 1]
    s2 = json.dumps(d, ensure_ascii=False, indent=1)
    if s2 == orig:
        return False
    f.write_text(s2, encoding="utf-8")
    return True


for ep in (sys.argv[1:] or EPS):
    aud = measure(ep)
    pages = [round(a + GAP, 2) for a in aud]
    a = fix_page_map(ep, aud, pages)
    b = fix_narration_json(ep, aud, pages)
    d = fix_narration_ts(ep, aud)
    e = fix_total_frames(ep, pages)
    print(f"  {ep:14s} 纯音频 {sum(aud):7.2f}s  页长合计 {sum(pages):7.2f}s  "
          f"pageMap={'改' if a else '-'} narr.json={'改' if b else '-'} "
          f"narr.ts={'改' if d else '-'} 总帧={'改' if e else '-'}")
