#!/usr/bin/env python3
"""剥掉 subtitles.ts 与旁白原稿里的「时长／字数／语速」元信息前缀。

背景
----
旁白原稿 narration/all.json 的每段正文**开头就带着工作笔记**：

    时长：16s｜约 89 字｜约 5.6 字/秒海淀有个地名，叫"一亩园"。……

gen_tts_*.sh 直接把整段丢进 --text，所以这串东西既是
  * 字幕里的噪声（E5/E6 各 8~9 条，E5 还和正文粘在同一条里），也是
  * 一旦重跑那几个 .sh 就会被 TTS 念出声的隐患。

实测本次 audio_new 的语速是 4.0~4.6 字/秒（正常口播），说明新配音用的是
清洗过的文本，音频本身干净 —— 坏的只有字幕。

前缀两种形态
------------
  A) 独立成条：{ text: "时长：", ...} / { text: "”语速说明：", ...}
  B) 与正文同条：{ text: "16s｜约 89 字｜约 5.6 字/秒海淀有个地名，", ...}

B 必须先剥前缀再重新分句，否则剩下的正文仍带着 4.65s 的错误时长。

用法
----
    python3 scripts/strip_meta_prefix.py                 # 原地改 subtitles.ts
    python3 scripts/strip_meta_prefix.py --check         # 只报告不改
"""
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path("/tmp/chemistry-video/src")

# 「时长：16s｜约 89 字｜约 5.6 字/秒」——**锚定到「字/秒」三个字为止**。
#
# [WARN] 早先写的是 `[^一-鿿]{0,60}?` 想"吃掉前缀又不碰汉字"，
#        但懒惰量词在"约 5.6 字/秒"里能一路匹配到下一个汉字之前，
#        结果把正文开头若干字一起吃掉（E5 八页全丢首句，如"海淀有个地名，"）。
#        教训：跨字符类的懒惰匹配无法界定"元信息到哪结束"，
#        必须用**字面锚点**（这里是「字/秒」）定位边界。
META = re.compile(
    r"^\s*(?:时长\s*[：:]\s*)?"          # 可选前缀标签
    r"\d+(?:\.\d+)?\s*s\s*[｜|]"          # 16s｜
    r"约\s*[\d.]+\s*字\s*[｜|]"            # 约 89 字｜
    r"约\s*[\d.]+\s*字\s*/\s*秒"          # 约 5.6 字/秒  ← 锚点，到此为止
    r"\s*(?=[一-鿿])"                     # 后面紧接正文
)
# E6 的形态：正文前面带一个孤立的引号残片
LEAD_JUNK = re.compile(r'^\s*[”"’。、，,:：;；\s]+(?=[一-鿿])')

# E6 的形态不同：统计信息在**结尾**，而且不带「时长：NNs｜」头。
#   ……后人把它叫作："一溜边山七十二府。"语速说明：约 70–78 字，14 秒，约 5.2–5.6 字/秒
# 所以要同时处理尾部：锚定「约 NN 字」「NN 秒」「约 N.N 字/秒」三段。
META_TAIL = re.compile(
    r"\s*(?:语速说明\s*[：:]?\s*)?"      # 可选「语速说明：」
    r"约\s*[\d–\-]+\s*字\s*[，,]?"      # 约 70–78 字，
    r"\s*\d+(?:\.\d+)?\s*秒\s*[，,]?"    # 14 秒，
    r"\s*约\s*[\d.–\-]+\s*字\s*/\s*秒"   # 约 5.2–5.6 字/秒
    r"\s*[。．.]?\s*$"                   # 允许句末句号
)

META_WORDS = ("时长：", "时长:", "语速说明", "字/秒", "字／秒")


def is_meta(text: str) -> bool:
    return any(w in text for w in META_WORDS)


def clean(text: str) -> str:
    """剥掉元信息（开头前缀 + 结尾统计），无则原样返回。"""
    return META_TAIL.sub("", META.sub("", text)).strip()


AUDIO_DIR = pathlib.Path("/tmp/chemistry-video/public/audio")


def wav_sec(ep: str, page: int) -> float:
    """实测该页 wav 时长（秒），取不到返回 0。"""
    f = AUDIO_DIR / ep / f"p{page:02d}.wav"
    if not f.exists():
        f = AUDIO_DIR / ep / f"p{page}.wav"
    if not f.exists():
        return 0.0
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(f)],
        capture_output=True, text=True)
    try:
        return round(float(r.stdout.strip()), 2)
    except ValueError:
        return 0.0


def split_sentences(text: str) -> list:
    """按句读切成字幕块。

    引号/括号要跟着前一句走：`"一溜边山七十二府。"` 必须在 `。` 后的
    闭合引号处才切，否则引号被甩成孤零零的一条字幕。
    """
    parts = re.split(r"(?<=[。！？；?!;])", text)
    out = []
    for p in (x.strip() for x in parts):
        if not p:
            continue
        # 纯标点尾巴（”"」）并入上一条
        if out and re.fullmatch(r'[”"’\'」』）)]+', p):
            out[-1] += p
        else:
            out.append(p)
    return out


def weight(t: str) -> int:
    return len(re.sub(r"[\s，。、：；？！""''「」（）—…·《》]", "", t)) or 1


def process(ep: str, check_only: bool) -> str:
    f = ROOT / ep / "data" / "subtitles.ts"
    if not f.exists():
        return "跳过（无文件）"
    s = f.read_text(encoding="utf-8")
    n_meta = n_fixed = n_block = 0

    def redo(m):
        nonlocal n_meta, n_fixed, n_block
        body = m.group(2)
        lines = re.findall(r'\{ text: "(.*?)", from: [\d.]+, dur: [\d.]+ \}', body)
        if not lines:
            return m.group(0)
        # B 形态：某一条同时含元信息和正文
        had = [l for l in lines if is_meta(l) or META.match(l)]
        if not had:
            return m.group(0)
        n_meta += len(had)

        # 剥除分两步，顺序不能反：
        #  1) 先把本页所有条目拼成**整段文本**再剥尾部统计 —— 统计常被
        #     split_sentences 按句号切成独立块（"约 70–78 字，14 秒，"），
        #     逐条剥时 META_TAIL 的 $ 锚点落空，元信息就漏进正文。
        #  2) 再剥开头的「时长：16s｜…」前缀。
        # 注意本页的 from/dur 里混着元信息条目的时间轴，剥完要整体重分。
        joined = "".join(lines)
        joined = META_TAIL.sub("", joined).strip()
        joined = META.sub("", joined)

        cleaned = []
        for part in split_sentences(joined):
            c = LEAD_JUNK.sub("", part).strip()
            if not c or is_meta(c):
                continue          # A 形态：整条是元信息，丢弃
            cleaned.append(c)
        if not cleaned:
            return m.group(0)

        # 页内总时长取**实测 wav**，不用旧字幕的累加值。
        # 旧值来自换音色前的配音（E5 P01 是 24.56s，新音频只有 16.88s），
        # 沿用它会让字幕整体比音频长 40%，末条压到页尾留白里还退场不了。
        page = int(m.group(1))
        total = wav_sec(ep, page)
        if total <= 0:
            last = re.findall(r"from: ([\d.]+), dur: ([\d.]+) \}", body)
            total = round(float(last[-1][0]) + float(last[-1][1]), 2) if last else 0.0
        if total <= 0:
            return m.group(0)

        ws = [weight(c) for c in cleaned]
        tot = sum(ws)
        t = 0.0
        out = []
        for c, w in zip(cleaned, ws):
            d = round(total * w / tot, 2)
            out.append('{ text: "%s", from: %.2f, dur: %.2f }' % (c, t, d))
            t = round(t + d, 2)
        n_fixed += 1
        n_block += len(out)
        return '  %s: [\n    %s,\n  ],' % (m.group(1), ",\n    ".join(out))

    s2 = re.sub(r"  (\d+): \[\n(.*?)\n  \],", redo, s, flags=re.S)
    tag = f"  {ep:14s} 清掉 {n_meta:2d} 条元信息，重分 {n_fixed} 页共 {n_block} 条"
    if s2 == s:
        return tag + "（无需改）"
    if not check_only:
        f.write_text(s2, encoding="utf-8")
        return tag + " 已写入"
    return tag + " [CHECK 模式未写入]"


def process_source(ep: str, check_only: bool) -> str:
    """清洗旁白原稿 narration/all.json。

    gen_tts_*.sh 把 all.json 的值整个丢进 `--text`，不做任何清洗。
    元信息留在原稿里 = 重跑配音时 TTS 会把"时长，十六秒，约八十九字"
    真的念出来。本函数把原稿本身洗干净，从源头断掉这条路。
    """
    f = pathlib.Path(f"/tmp/{ep}_video/narration/all.json")
    if not f.exists():
        return "跳过（无原稿）"
    d = json.loads(f.read_text(encoding="utf-8"))
    n = 0
    for k, v in d.items():
        if not isinstance(v, str):
            continue
        c = clean(v)
        if c != v:
            d[k] = c
            n += 1
    if n == 0:
        return f"  {ep:14s} 原稿 0 段带元信息（无需改）"
    if not check_only:
        f.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    return f"  {ep:14s} 原稿清掉 {n} 段元信息" + (
        " [CHECK 模式未写入]" if check_only else " 已写入")


if __name__ == "__main__":
    check = "--check" in sys.argv
    eps = [a for a in sys.argv[1:] if not a.startswith("-")] or [
        "yimuyuan", "niangniangfu", "xisanqi", "gaoliangqiao",
        "dazhongsi", "landianchang",
    ]
    print("=== 旁白原稿 ===")
    for ep in eps:
        print(process_source(ep, check))
    print("\n=== 字幕 ===")
    for ep in eps:
        print(process(ep, check))
