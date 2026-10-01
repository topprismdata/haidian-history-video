#!/usr/bin/env python3
"""E5–E10 通用逐页槽位验收 —— 判「槽位区域是否有元素」。

用法：
    python3 qa_all.py                # E5–E10 全部
    python3 qa_all.py landianchang   # 只跑某一集

## 判据：为什么不能是绝对色
E9 的 card 判据是「米色底板像素占比」，隐含"板面底色统一"。
E10 板面偏黄绿（b 掉到 185–195），同一判据下所有槽位全判"缺"——8 页全缺，
但帧里明明有字。（E10 实测踩中，一度以为是渲染坏了。）

正确做法：**与底色无关**的「深色墨 + 梯度能量」双判据。
  * 深色墨：字是深色，板面是浅色/中间色 —— 三通道最小值够低
  * 梯度能量：Sobel 边缘均值 —— 文字必然产生大量边缘
两者都不依赖"板面是什么颜色"，跨集通用。

## 必须排除的槽位类型
`kind: "tag"`（evidence_tag）是**深底白字**反白样式，没有深色墨像素，
必须排除，否则每页误报缺 1 项。（E10 实测踩中。）
"""
import json
import os
import pathlib
import re
import subprocess
import sys

import numpy as np
from PIL import Image

ROOT = pathlib.Path("/tmp/chemistry-video")
FPS = 30

EPISODES = {
    "yimuyuan":     ("YimuyuanCourse"),
    "niangniangfu": ("NiangniangfuCourse"),
    "xisanqi":      ("XisanqiCourse"),
    "gaoliangqiao": ("GaoLiangQiaoCourse"),
    "dazhongsi":    ("DazhongsiCourse"),
    "landianchang": ("LandianchangCourse"),
}

# 集 -> 需要排除的槽位 id（tag 型：深底白字）
TAG_IDS = {"evidence_tag"}


def ep_dir(ep):
    return ROOT / "src" / ep


def load_slots(ep):
    return json.load(open(ep_dir(ep) / "data" / "slots.json", encoding="utf-8"))


def _nums(block):
    """只取数值字面量，先剥掉 // 与 /* */ 注释。

    [WARN] 不剥注释会把 `// p01` 里的 1 读成页长值 ——
    PAGE_DURATIONS_SEC = [23.2, // p01, 27.28, // p02, ...]
    会解析成 [23.2, 1.0, 27.28, 2.0, ...]，页数翻倍、页起点全错。
    （qa_all 初版踩中：E10 报成 16 页。）
    """
    block = re.sub(r"/\*.*?\*/", "", block, flags=re.S)
    block = re.sub(r"//[^\n]*", "", block)
    return [float(x) for x in re.findall(r"\d+\.?\d*", block)]


def page_layout(ep):
    """返回每页的 (起点帧, 页长帧)。

    [WARN] 优先级必须是 pageMap > narration.json，**不能反**。
    两者的 pageLenSec 口径不同：
      * pageMap.ts 的 PAGE_DURATIONS_SEC = 纯音频 + 1.6s 页尾留白（**真实页长**）
      * narration.json 的 pageLenSec     = 纯音频（**不含留白**）
    E9 两份都有，累积到 P4 差 144 帧（真实 2047 vs 算出 1903），
    抽帧落到前一页的尾巴 → 误报 3 个槽位"缺失"。
    （qa_all 初版踩中。**页起点要的是渲染用的页长，不是音频长。**）
    """
    # ① pageMap.ts —— 渲染真正用的页长（含页尾留白）
    pm = ep_dir(ep) / "data" / "pageMap.ts"
    if pm.exists():
        s = pm.read_text(encoding="utf-8")
        m = re.search(r"PAGE_DURATIONS_SEC[^=]*=\s*\[([^\]]+)\]", s)
        if m:
            out, cur = [], 0
            for sec in _nums(m.group(1)):
                n = round(sec * FPS)
                out.append((cur, n))
                cur += n
            return out
    # ② narration.json（E5–E7：pageLenSec 已含留白）
    nj = ep_dir(ep) / "data" / "narration.json"
    if nj.exists():
        d = json.load(open(nj, encoding="utf-8"))
        fps = d.get("fps") or FPS
        out, cur = [], 0
        for p in d["pages"]:
            n = round(p["pageLenSec"] * fps)
            out.append((cur, n))
            cur += n
        return out
    # ③ narration.ts 里的手工数组（纯音频 + 1.6s 留白）
    ts = ep_dir(ep) / "data" / "narration.ts"
    if ts.exists():
        s = ts.read_text(encoding="utf-8")
        m = re.search(r"(?:PAGE_AUDIO_SEC|AUDIO_SEC|AUDIO|DUR_SEC)\s*=\s*\[([^\]]+)\]", s)
        if m:
            out, cur = [], 0
            for a in _nums(m.group(1)):
                n = round((a + 1.6) * FPS)
                out.append((cur, n))
                cur += n
            return out
    raise SystemExit(f"{ep}: 找不到页长数据")


def final_frame(layout, page):
    return layout[page - 1][0] + layout[page - 1][1] - 3


def sobel(a):
    """一阶梯度幅值（差分近似），返回 (H-1, W-1)。"""
    g = a.mean(axis=2)
    dx = np.diff(g, axis=1)                      # (H, W-1)
    dy = np.diff(g, axis=0)                      # (H-1, W)
    h = min(dx.shape[0], dy.shape[0])
    w = min(dx.shape[1], dy.shape[1])
    return np.abs(dx[:h, :w]) + np.abs(dy[:h, :w])


def check_frame(img_path, det):
    a = np.array(Image.open(img_path).convert("RGB")).astype(int)
    ink = (a.min(axis=2) < 110)          # 深色墨：三通道最小值够低
    edge = sobel(a)
    miss = []
    n = 0
    for s in det["slots"]:
        sid = s.get("id", "?")
        if sid in TAG_IDS:
            continue
        n += 1
        x0, y0 = max(0, s["x"]), max(0, s["y"])
        x1, y1 = min(1920, s["x"] + s["w"]), min(1080, s["y"] + s["h"])
        if x1 - x0 < 4 or y1 - y0 < 4:
            miss.append(sid)
            continue
        si = ink[y0:y1, x0:x1].sum()
        # edge 比原图小 1 像素，索引相应收缩
        se = edge[max(0, y0 - 1):max(0, y1 - 2), max(0, x0 - 1):max(0, x1 - 2)].mean()
        if not (si > 40 and se > 0.5):
            miss.append((sid, int(si), round(float(se), 2)))
    return n, miss


def run(ep):
    slots = load_slots(ep)
    layout = page_layout(ep)
    comp = EPISODES[ep]
    outdir = ROOT / "qa" / "auto"
    outdir.mkdir(parents=True, exist_ok=True)
    lines, bad = [], 0
    for p in range(1, 9):
        det = slots.get(f"p{p:02d}")
        if not det:
            continue
        f = final_frame(layout, p)
        png = outdir / f"{ep}_p{p}.png"
        r = subprocess.run(
            ["npx", "remotion", "still", "src/index.tsx", comp, str(png),
             f"--frame={f}", "--log=error"],
            cwd=ROOT, capture_output=True, text=True, env=os.environ)
        if r.returncode:
            print(r.stderr[-600:])
            lines.append(f"  P{p} 帧{f}: 渲染失败")
            bad += 1
            continue
        n, miss = check_frame(png, det)
        if miss:
            bad += 1
            lines.append(f"  P{p} 帧{f}: {n-len(miss)}/{n}  缺 {miss}")
        else:
            lines.append(f"  P{p} 帧{f}: {n}/{n}  全通过")
    return len(layout) - bad, len(layout), lines


if __name__ == "__main__":
    eps = sys.argv[1:] or list(EPISODES)
    tot_ok = tot = 0
    for ep in eps:
        if ep not in EPISODES:
            print(f"未知集 {ep}，可选 {list(EPISODES)}")
            continue
        print(f"=== {ep} ===")
        ok, n, lines = run(ep)
        for l in lines:
            print(l)
        print(f"  -> {ok}/{n} 页通过")
        tot_ok += ok
        tot += n
    print(f"\n总计 {tot_ok}/{tot} 页通过")
    sys.exit(0 if tot_ok == tot else 1)
