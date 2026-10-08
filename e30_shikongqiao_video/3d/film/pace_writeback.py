#!/usr/bin/env python3
"""P3-T7 pace_writeback: 音频秒数 → pad_frames 的唯一回写通道.

pace.json 是渲染器/验收器/Remotion 三方只读的单一节奏源; 本脚本是它唯一
的写入者(T1 的 pace_build 只管初版生成)。语义(计划 Task 7):

    pad_frames = max(0, ceil(audio_sec * fps) - frames)

即音频比画面长才补(短/等长钳 0, 绝不为负); start/end 级联重算
(stage i 拥有 [start_i, end_i), end-start == frames+pad_frames),
total_frames = Σ(frames+pad_frames) 相应增长。同一张表两连跑逐字节
幂等(绝对赋值, 非累加)。表外 stage 的 pad_frames 原样保留; 表内出现
pace 没有的 stage id → 退出码 3 拒绝(唯一通道不许哑改, 宁红不哑)。

用法:
    python3 3d/film/pace_writeback.py --pace 3d/out/film/pace.json \
        --audio-table audio_table.json [--out 3d/out/film/pace.json]
  audio_table.json = {"S001": 12.3, "S009": 8.0, ...}(stage_id → 秒)
  --out 缺省 = 原地写回 --pace 路径(原子替换, 中途崩溃不损原件)。

Python 3.9.6; stdlib only; blender-free; 其余字段(id/事件区间/frames/
fps/generated_by/source_sha)逐字节不变。
"""
import argparse
import json
import math
import os
import sys

_EPS = 1e-9          # 浮点噪声容差: x 距整数 <_EPS 时 ceil 读作该整数
_RC_DATA = 3         # 数据层拒绝(未知 id/非法值); 2 留给 argparse/IO


def padded_pad_frames(audio_sec, frames, fps):
    """单 stage 的 pad 计算(纯函数): max(0, ceil(audio*fps) - frames)."""
    x = audio_sec * fps
    return max(0, int(math.ceil(x - _EPS)) - frames)


def writeback(pace, audio_table):
    """pace dict + {stage_id: audio_sec} → 回写后的新 pace dict(纯函数).

    段序与其余字段原样保留; pad/边界/total 重算。表为空 = 恒等变换。
    """
    fps = pace["fps"]
    ids = [s["id"] for s in pace["stages"]]
    unknown = sorted(set(audio_table) - set(ids))
    if unknown:
        raise ValueError("audio_table 含 pace 没有的 stage id: %s" % unknown)
    for sid, sec in audio_table.items():
        if not isinstance(sec, (int, float)) or isinstance(sec, bool) \
                or not math.isfinite(sec) or sec < 0:
            raise ValueError("audio_table[%s]=%r 非法(须非负有限秒数)"
                             % (sid, sec))
    out, cursor = [], 0
    for s in pace["stages"]:
        st = dict(s)
        if s["id"] in audio_table:
            st["pad_frames"] = padded_pad_frames(audio_table[s["id"]],
                                                 s["frames"], fps)
        st["start"] = cursor
        cursor += st["frames"] + st["pad_frames"]
        st["end"] = cursor
        out.append(st)
    return dict(pace, stages=out, total_frames=cursor)


def validate_pace_padded(pace):
    """padded 契约校验(失败 raise ValueError): writeback 产物的机检面.

    与 pace_build.validate_pace 同族, 但区间长含 pad(端可空), 供回写后
    与后续消费者(读入带 pad 的 pace)复检。生成初版(pad 全 0)同样通过。
    """
    for key in ("fps", "total_frames", "stages", "generated_by", "source_sha"):
        if key not in pace:
            raise ValueError("pace 缺顶层键 %s" % key)
    st = pace["stages"]
    if not st:
        raise ValueError("stages 空")
    if st[0]["start"] != 0:
        raise ValueError("首 stage start=%r != 0" % st[0]["start"])
    for a, b in zip(st, st[1:]):
        if a["end"] != b["start"]:
            raise ValueError("stage %s→%s 不连续: %r != %r"
                             % (a["id"], b["id"], a["end"], b["start"]))
    for s in st:
        if set(s) != {"id", "first_event", "last_event", "frames",
                      "pad_frames", "start", "end"}:
            raise ValueError("stage %s 键面不符: %s" % (s["id"], sorted(s)))
        if s["frames"] < 1 or s["end"] - s["start"] != s["frames"] + s["pad_frames"]:
            raise ValueError("stage %s 区间长 %d != frames %d + pad %d"
                             % (s["id"], s["end"] - s["start"],
                                s["frames"], s["pad_frames"]))
        if s["pad_frames"] < 0 or s["first_event"] > s["last_event"]:
            raise ValueError("stage %s pad/事件区间非法" % s["id"])
    if st[-1]["end"] != pace["total_frames"]:
        raise ValueError("末 stage end=%r != total_frames=%r"
                         % (st[-1]["end"], pace["total_frames"]))
    if sum(s["frames"] + s["pad_frames"] for s in st) != pace["total_frames"]:
        raise ValueError("Σ(frames+pad) != total_frames")


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="音频秒数→pad_frames 唯一回写通道(P3-T7)")
    ap.add_argument("--pace", required=True, help="输入 pace.json(可原地写回)")
    ap.add_argument("--audio-table", required=True,
                    help="音频表 JSON: {stage_id: audio_sec}")
    ap.add_argument("--out", default=None,
                    help="输出路径, 缺省 = 原地写回 --pace(原子替换)")
    args = ap.parse_args(argv)

    with open(args.pace, "r") as fh:
        pace = json.load(fh)
    with open(args.audio_table, "r") as fh:
        audio_table = json.load(fh)
    if not isinstance(audio_table, dict):
        ap.error("audio_table 须为 {stage_id: audio_sec} 对象")

    try:
        out_pace = writeback(pace, audio_table)
        validate_pace_padded(out_pace)
    except ValueError as exc:
        print("pace_writeback 拒绝: %s" % exc, file=sys.stderr)
        return _RC_DATA

    out = os.path.abspath(args.out) if args.out else os.path.abspath(args.pace)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    tmp = out + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(out_pace, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, out)

    n_pad = sum(1 for a, b in zip(pace["stages"], out_pace["stages"])
                if a["pad_frames"] != b["pad_frames"])
    print("pace_writeback -> %s" % out)
    print("表 %d 项: 补帧 stage %d 个, Σpad %d 帧"
          % (len(audio_table), n_pad,
             sum(s["pad_frames"] for s in out_pace["stages"])))
    print("对账: total_frames %d -> %d"
          % (pace["total_frames"], out_pace["total_frames"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
