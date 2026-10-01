#!/usr/bin/env python3
"""全量核验：ASR 转写每段配音，与 subtitles.ts 逐页比对。

**为什么必须真的做 ASR**：换音色后最常见的事故是配音念了字幕里没有的内容
（旁白原稿开头的「时长：16s｜约 89 字｜约 5.6 字/秒」这类工作笔记），
而**时长、语速、槽位验收全部正常** —— 念了笔记就等于多念十几字，
正文照样念完，总时长不变，语速也照旧在 4~5 字/秒。
2026-10-01 我就是靠"语速正常"错判成"音频干净"，被 ASR 当场打脸。

判据（两条独立，缺一不可）
  1) 字幕时间轴必须盖住整段音频，否则末句被切断
  2) 音频里不能有字幕之外的**整段**内容（>= 6 字的连续 insert）

**相似度只作参考，不参与判定**：TTS 对数字的念法本就自由
（"四十六点五"↔"46.5"），拿字符相似度当门槛只会制造假阳性。
数字块在 align_ratio 里当成一个原子 token，两种写法都算 1 个。

用法：
    /tmp/.asr-venv/bin/python scripts/verify_subtitles_asr.py [集名...]
"""
import difflib
import pathlib
import re
import sys

from faster_whisper import WhisperModel

ROOT = pathlib.Path("/tmp/chemistry-video")
EPS = ["yimuyuan", "niangniangfu", "xisanqi", "gaoliangqiao",
       "dazhongsi", "landianchang"]
PUNCT = re.compile(r'[\s，。、：；？！""''「」『』（）—…·《》,.;:?!\[\]"\']')
TRAD = {"銅": "铜", "鑄": "铸", "銀": "银", "徑": "径", "園": "园", "裡": "里",
        "樹": "树", "臺": "台", "號": "号", "們": "们", "這": "这", "說": "说",
        "變": "变", "靈": "灵", "馬": "马", "體": "体", "飛": "飞", "後": "后",
        "東": "东", "長": "长", "萬": "万", "與": "与", "為": "为", "會": "会"}


def norm(t: str) -> str:
    """只做标点与简繁归一，**不碰数字**。

    教训：曾试图把「四十六点五」折成 46.5，结果 cn2num 的位值算法有 bug
    （"一百八十五"→124、"三十八"→21），而且中文/阿拉伯数字无法可靠互转 ——
    TTS 本来就可能把数字念成任一形式，两边都归一化只会引入新的错。
    数字差异改由 token 级对齐处理（见 align_ratio）。
    """
    t = PUNCT.sub("", t)
    for trad, simp in TRAD.items():
        t = t.replace(trad, simp)
    return t


# 数字 token：阿拉伯或中文数字（含十百千点），两侧写法不同但语义等价
NUM = re.compile(r'[0-9]+(?:\.[0-9]+)?|[零一二三四五六七八九十百千]+(?:点[零一二三四五六七八九]+)?')


def align_ratio(sub: str, asr: str) -> float:
    """按「数字块 vs 文字」切 token 后求相似度。

    数字块当成一个原子 token —— 无论字幕写"四十六点五"还是 ASR 写 "46.5"，
    都算 1 个 token，不因写法差异拉低分数。
    """
    def split(s):
        out, last = [], 0
        for m in NUM.finditer(s):
            out.extend(c for c in s[last:m.start()] if not c.isspace())
            out.append("<num>")
            last = m.end()
        out.extend(c for c in s[last:] if not c.isspace())
        return out

    return difflib.SequenceMatcher(None, split(sub), split(asr)).ratio()


def extra_text(sub: str, asr: str) -> str:
    """音频里多出来、字幕里没有的连续文字（长度 >= 6 才算实质问题）。

    判据是**多出来的连续片段**而不是整体长度差：
    配音念了字幕没有的内容（元信息）必然是一整段插入；
    而同音错字、数字写法、简繁混用都只是零散替换，不会凑出 6 字以上的整段。
    """
    a, b = sub, asr
    worst = ""
    sm = difflib.SequenceMatcher(None, a, b)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "insert" and (j2 - j1) > len(worst):
            worst = b[j1:j2]
    return worst if len(worst) >= 6 else ""


def audio_path(ep: str, page: int):
    for name in (f"p{page:02d}.wav", f"p{page}.wav",
                 f"p{page:02d}_000.wav", f"p{page}_000.wav"):
        f = ROOT / "public" / "audio" / ep / name
        if f.exists():
            return f
    return None


def subtitles(ep: str):
    s = (ROOT / "src" / ep / "data" / "subtitles.ts").read_text(encoding="utf-8")
    out = {}
    for m in re.finditer(r'\n  (\d+): \[\n(.*?)\n  \],', s, re.S):
        rows = re.findall(r'\{ text: "(.*?)", from: ([\d.]+), dur: ([\d.]+) \}', m.group(2))
        out[int(m.group(1))] = ([r[0] for r in rows],
                                round(float(rows[-1][1]) + float(rows[-1][2]), 2) if rows else 0)
    return out


def main():
    eps = sys.argv[1:] or EPS
    model = WhisperModel("/tmp/fw-small", device="cpu", compute_type="int8")
    bad = 0
    for ep in eps:
        print(f"\n=== {ep} ===")
        subs = subtitles(ep)
        for page in sorted(subs):
            texts, sub_end = subs[page]
            wav = audio_path(ep, page)
            if wav is None:
                print(f"  P{page} ✗ 找不到音频")
                bad += 1
                continue
            segs, info = model.transcribe(str(wav), language="zh",
                                           beam_size=1, vad_filter=True)
            asr = norm("".join(s.text for s in segs))
            sub = norm("".join(texts))
            ratio = align_ratio(sub, asr)
            audio_len = round(info.duration, 2)
            dt = round(sub_end - audio_len, 2)
            extra = extra_text(sub, asr)

            # 两条独立的判据，缺一不可：
            #  1) 字幕时间轴必须盖住整段音频（dt≈0）—— 否则末句被切断
            #  2) 音频里不能有字幕之外的**整段**内容（extra）—— 这是
            #     「配音念了工作笔记」的唯一可靠信号。
            # 相似度只作参考输出，不参与判定：TTS 对数字的念法本就自由
            # （"四十六点五"↔"46.5"），拿它当门槛只会制造假阳性。
            ok = not extra and abs(dt) <= 0.5
            if not ok:
                bad += 1
            flag = "✓" if ok else "✗"
            print(f"  P{page} {flag} 对齐 {ratio:.0%}  "
                  f"字幕{sub_end:6.2f}s / 音频{audio_len:6.2f}s (差{dt:+.2f})"
                  + (f"  ⚠ 多出「{extra}」" if extra else ""))
            if not ok and not extra:
                print(f"      字幕: {sub[:70]}")
                print(f"      音频: {asr[:70]}")
    print(f"\n>>> 不合格页数：{bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
