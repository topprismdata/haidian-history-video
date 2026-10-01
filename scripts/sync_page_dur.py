#!/usr/bin/env python3
"""把新配音的实测时长写回 Remotion 工程的时间数据。

配音变短 → 页长必须跟着变，否则画面会在音频结束后留空。

三处要改（E5–E10 各自不同）：
  * pageMap.ts   的 PAGE_DURATIONS_SEC 与 AUDIO_MEASURED_SEC（E8–E10）
  * narration.json 的 pages[].pageLenSec 与 beats[].durSec（E5–E7，E8/E9 也有）
  * subtitles.ts 的每条 dur/from（按字数比例重分配，页内归一）
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
    s2 = re.sub(r"// 由实测 wav 时长生成。",
                "// 由实测 wav 时长生成（2026-10-01 换音色后重测）。", s2)
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
    f = ROOT / ep / "data" / "narration.json"
    if not f.exists():
        return False
    d = json.load(open(f, encoding="utf-8"))
    for p in d["pages"]:
        n = p["page"]
        p["pageLenSec"] = pages[n - 1]
        for b in p.get("beats", []):
            b["durSec"] = aud[n - 1]
    json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return True


def fix_subtitles(ep, aud):
    """字幕按每页**纯音频**时长重新分配（页尾留白是静默，不上字幕）。"""
    f = ROOT / ep / "data" / "subtitles.ts"
    if not f.exists():
        return 0
    s = f.read_text(encoding="utf-8")
    n_fixed = 0

    def redo(page_body, dur):
        nonlocal n_fixed
        lines = re.findall(r'\{ text: "(.*?)", from: [\d.]+, dur: [\d.]+ \}', page_body)
        if not lines:
            return page_body
        weights = [len(re.sub(r'\\[""]|[""「」]', "", t)) or 1 for t in lines]
        tot = sum(weights)
        t = 0.0
        out = []
        for txt, w in zip(lines, weights):
            d = round(dur * w / tot, 2)
            out.append(f'{{ text: "{txt}", from: {t:.2f}, dur: {d:.2f} }}')
            t = round(t + d, 2)
        n_fixed += len(lines)
        return "[\n    " + ",\n    ".join(out) + ",\n  ]"

    def repl(m):
        page = int(m.group(1))
        return f"  {page}: " + redo(m.group(2), aud[page - 1])

    s2 = re.sub(r"  (\d+): \[(.*?)\n  \],", repl, s, flags=re.S)
    if s2 != s:
        f.write_text(s2, encoding="utf-8")
    return n_fixed


for ep in (sys.argv[1:] or EPS):
    aud = measure(ep)
    pages = [round(a + GAP, 2) for a in aud]
    a = fix_page_map(ep, aud, pages)
    b = fix_narration_json(ep, aud, pages)
    d = fix_narration_ts(ep, aud)
    e = fix_total_frames(ep, pages)
    c = 0  # fix_subtitles 暂禁用：正则会吃掉页尾 '],' 把文件写坏
    print(f"  {ep:14s} 纯音频 {sum(aud):7.2f}s  页长合计 {sum(pages):7.2f}s  "
          f"pageMap={'改' if a else '-'} narr.json={'改' if b else '-'} "
          f"narr.ts={'改' if d else '-'} 总帧={'改' if e else '-'} 字幕{c}条")
