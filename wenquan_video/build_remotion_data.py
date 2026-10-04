#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E28 Task 4 三件套生成: 实测音频时长 → durations.json / narration.ts / subtitles.ts.

产物:
  wenquan_video/narration/durations.json
  /tmp/chemistry-video/src/wenquan/data/narration.ts
  /tmp/chemistry-video/src/wenquan/data/subtitles.ts
  /tmp/chemistry-video/src/wenquan/data/durations.json
  remotion-template/src/wenquan/data/{narration,subtitles,durations}.*  (镜像)
  /tmp/chemistry-video/public/audio/wenquan/p1.wav–p8.wav      (双文件名别名)

字幕规则沿用 E20/E21: 标点切句、字数比例分配; 每页字幕总时长 == 该页纯音频时长。
"""
import json
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
NARR_DIR = ROOT / "wenquan_video" / "narration"
AUDIO_DIR = pathlib.Path("/tmp/chemistry-video/public/audio/wenquan")
REMOTION_DATA = pathlib.Path("/tmp/chemistry-video/src/wenquan/data")
TEMPLATE_DATA = ROOT / "remotion-template" / "src" / "wenquan" / "data"
FPS = 30
SPLIT_RE = re.compile(r"(?<=[,。?!;:、——?])")


def ffprobe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True).stdout.strip()
    return float(out)


def split_captions(text):
    parts = [p for p in SPLIT_RE.split(text) if p.strip()]
    merged = []
    for p in parts:
        if merged and not re.search(r"[\u4e00-\u9fff0-9A-Za-z]", p[:-1] or p):
            merged[-1] += p
        else:
            merged.append(p)
    return merged


def alloc(captions, total):
    """字数比例分配; 累计取整保证 sum(dur) 精确 == total。"""
    weights = [max(len(c), 1) for c in captions]
    wsum = float(sum(weights))
    ends, acc = [], 0.0
    for w in weights[:-1]:
        acc += w / wsum * total
        ends.append(round(acc, 2))
    ends.append(round(total, 2))
    out, start = [], 0.0
    for c, end in zip(captions, ends):
        out.append({"text": c, "from": round(start, 2), "dur": round(end - start, 2)})
        start = end
    return out


def main():
    all_json = json.loads((NARR_DIR / "all.json").read_text(encoding="utf-8"))
    keys = sorted(all_json)
    if keys != [f"p{i:02d}" for i in range(1, 9)]:
        sys.exit(f"all.json 键异常: {keys}")

    # 1) 双文件名别名
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    for k in keys:
        src = AUDIO_DIR / f"{k}.wav"
        if not src.exists() or src.stat().st_size == 0:
            sys.exit(f"缺少 {src}, 先跑 gen_tts.sh")
        shutil.copyfile(src, AUDIO_DIR / f"p{int(k[1:])}.wav")

    # 2) 实测时长
    durations = {k: round(ffprobe_duration(AUDIO_DIR / f"{k}.wav"), 2) for k in keys}
    dur_text = json.dumps(durations, ensure_ascii=False, indent=2) + "\n"

    # 3) narration.ts
    sec_list = ", ".join(f"{durations[k]:.2f}" for k in keys)
    narration_ts = f"""// narration.ts — E28《温泉·「温泉」之前叫「石窝」》配音节拍。实测 2026-10-04。

export interface Beat {{ name: string; from: number; dur: number }}

const FPS = {FPS};

const PAGE_AUDIO_SEC = [{sec_list}];

export const audioBeats = (pageNo: number): Beat[] =>
  PAGE_AUDIO_SEC[pageNo - 1] === undefined
    ? []
    : [{{
        name: `p${{pageNo}}`,
        from: 0,
        dur: Math.round(PAGE_AUDIO_SEC[pageNo - 1] * FPS),
      }}];

export const AUDIO_SEC = PAGE_AUDIO_SEC;
"""

    # 4) subtitles.ts
    subs = {str(i + 1): alloc(split_captions(all_json[k]), durations[k])
            for i, k in enumerate(keys)}
    body = json.dumps(subs, ensure_ascii=False, indent=2)
    subtitles_ts = f"""// subtitles.ts — E28《温泉·「温泉」之前叫「石窝」》字幕(标点切句, 字数比例分配)。

export interface CaptionLine {{ text: string; from: number; dur: number }}

export const SUBTITLES: Record<string, CaptionLine[]> = {body};
"""

    # 5) 落盘 + 双镜像
    (NARR_DIR / "durations.json").write_text(dur_text, encoding="utf-8")
    for d in (REMOTION_DATA, TEMPLATE_DATA):
        d.mkdir(parents=True, exist_ok=True)
        (d / "narration.ts").write_text(narration_ts, encoding="utf-8")
        (d / "subtitles.ts").write_text(subtitles_ts, encoding="utf-8")
        (d / "durations.json").write_text(dur_text, encoding="utf-8")

    total = sum(durations.values())
    print(f"E28 纯音频合计 {total:.2f}s; 含 1.6s/页留白约 "
          f"{total + 8 * 1.6:.1f}s = {round((total + 8 * 1.6) * FPS)} 帧 @30fps")
    for k in keys:
        print(f"  {k}: {durations[k]:6.2f}s  {len(all_json[k])} 字")
    return 0


if __name__ == "__main__":
    sys.exit(main())
