#!/usr/bin/env python3
"""P3-T1 pace.json 生成器: sequence.json(只读) → 单一节奏源 pace.json.

权重规则(计划 Task 1 Step 3, 词表已对齐真账 stage 名):
  w = 事件数(每事件 1) + stage 级类型加成, 乘首孔倍率, 末段另加收尾加成:
    *.CLOSE_RING +40 | *.WEDGE.* +4 | *.CENTER_ERECT +6
    *.DSTART.* / *.CLEAR.* +8 | *.R7.* +3(真账无 R7 stage, 规则按表保留)
    ARCH01.* 全部 ×2(教学段, 作用于 事件数+类型加成)
    末段(或 BRIDGE_DONE stage) +60 —— 真账 408 stage 无 BRIDGE_DONE,
    收尾加成落在末段 ARCH17.FILL(加成不叠乘, 每 stage 至多一次)。
  加成为 stage 级平加、不随 stage 内事件数放大: 否则 17 孔同拍的
  DECENTER 波次(DSTART 17 事件)会淹没 CLOSE_RING +40 的最大单点停顿,
  与计划"合龙=最大加成"的节拍意图相悖(设计选择, 见 P3-T1 报告)。

缩放: 最大余数法(纯整数运算)保证 Σframes == total_frames 精确相等;
每 stage frames 下限 1; pad_frames 初始 0(唯一回写通道 pace_writeback)。

CLI:
  python3 3d/film/pace_build.py --sequence 3d/out/sequence.json \
      --target-sec 240 [--out 3d/out/film/pace.json]
  --out 缺省 = <sequence 所在目录>/film/pace.json; 输出前打印
  total_frames 与 Σframes 的对账行。

Python 3.9.6; blender-free; sequence.json 只读。
"""
import argparse
import hashlib
import json
import os
import sys

FPS = 30

# stage 名 → 类型加成(计划 Task 1 Step 3 全表; R7 规则真账暂空, 保留对表)
_STAGE_BONUS = (
    ("CLOSE_RING", 40),   # 合龙: 全片最大单点节拍
    (".WEDGE.", 4),       # 楔木松档(λ 阶梯)
    ("CENTER_ERECT", 6),  # 立券架
    (".DSTART.", 8),      # 落架开始波次
    (".CLEAR.", 8),       # 券架撤清波次
    (".R7.", 3),          # R7 组(面上收尾: 铺装/栏板/雕刻; 真账暂无)
)
FINALE_BONUS = 60       # 末段/BRIDGE_DONE 收尾加成
FIRST_HOLE_PREFIX = "ARCH01."
FIRST_HOLE_MULT = 2     # 首孔教学段倍率


def stage_weight(name, event_count, is_last):
    """单个 stage 的缩放前权重(纯函数, 供测试与复用)."""
    if event_count < 1:
        raise ValueError("stage %s 事件数 %d < 1" % (name, event_count))
    bonus = 0
    for key, b in _STAGE_BONUS:
        if key in name:
            bonus += b
    finale = FINALE_BONUS if (is_last or "BRIDGE_DONE" in name) else 0
    mult = FIRST_HOLE_MULT if name.startswith(FIRST_HOLE_PREFIX) else 1
    return (event_count + bonus) * mult + finale


def allocate_frames(weights, total):
    """最大余数法精确缩放: 返回 frames 列表, Σ==total, 每项 >=1.

    纯整数运算(无浮点); 余数并列时按权重降序、下标升序定序, 结果确定。
    先给每 stage 保底 1 帧, 余量按 w_i/wsum 比例的最大余数分配——
    兼容 total 较小(w_i*total < wsum, 比例地板为 0)的极端表。
    """
    n = len(weights)
    wsum = sum(weights)
    if n == 0 or wsum <= 0:
        raise ValueError("权重表空或非正: n=%d wsum=%d" % (n, wsum))
    if total < n:
        raise ValueError("total=%d < stage 数 %d, 无法保证每段 >=1 帧"
                         % (total, n))
    rest = total - n
    frames = [1 + (w * rest) // wsum for w in weights]
    rems = [(w * rest) % wsum for w in weights]
    short = total - sum(frames)          # == rest - Σfloor, 恒 >=0
    order = sorted(range(n), key=lambda i: (-rems[i], -weights[i], i))
    for k in range(short):
        frames[order[k]] += 1
    return frames


def validate_pace(pace):
    """schema 校验(失败 raise ValueError): 计划 pace 契约的机检面."""
    for key in ("fps", "total_frames", "stages", "generated_by", "source_sha"):
        if key not in pace:
            raise ValueError("pace 缺顶层键 %s" % key)
    if pace["fps"] != FPS:
        raise ValueError("fps=%r != %d" % (pace["fps"], FPS))
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
        if s["frames"] < 1 or s["end"] - s["start"] != s["frames"]:
            raise ValueError("stage %s frames=%r 与区间长不符"
                             % (s["id"], s["frames"]))
        if s["pad_frames"] < 0 or s["first_event"] > s["last_event"]:
            raise ValueError("stage %s pad/事件区间非法" % s["id"])
    if st[-1]["end"] != pace["total_frames"]:
        raise ValueError("末 stage end=%r != total_frames=%r"
                         % (st[-1]["end"], pace["total_frames"]))
    if sum(s["frames"] for s in st) != pace["total_frames"]:
        raise ValueError("Σframes != total_frames")


def build_pace(seq, target_sec, source_sha=""):
    """sequence dict(含 "sequence" stage 表) → pace dict."""
    stages = seq.get("sequence")
    if not stages:
        raise ValueError("sequence.json 缺 sequence stage 表")
    ids = [s["id"] for s in stages]
    if len(set(ids)) != len(ids):
        raise ValueError("stage id 重复")
    total = int(round(target_sec * FPS))
    n = len(stages)
    weights = [stage_weight(s["stage"],
                            s["event_range"][1] - s["event_range"][0] + 1,
                            i == n - 1)
               for i, s in enumerate(stages)]
    frames = allocate_frames(weights, total)
    out, cursor = [], 0
    for s, f in zip(stages, frames):
        a, b = s["event_range"]
        out.append({"id": s["id"], "first_event": a, "last_event": b,
                    "frames": f, "pad_frames": 0,
                    "start": cursor, "end": cursor + f})
        cursor += f
    return {"fps": FPS, "total_frames": cursor, "stages": out,
            "generated_by": "pace_build", "source_sha": source_sha}


def _sha8(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:8]


def main(argv=None):
    ap = argparse.ArgumentParser(description="pace.json 生成器(P3-T1)")
    ap.add_argument("--sequence", required=True,
                    help="输入 sequence.json(只读)")
    ap.add_argument("--target-sec", type=float, required=True,
                    help="目标成片秒数(缩放基准)")
    ap.add_argument("--out", default=None,
                    help="输出路径, 缺省 <sequence 目录>/film/pace.json")
    args = ap.parse_args(argv)

    seq_path = os.path.abspath(args.sequence)
    out = args.out
    if not out:
        out = os.path.join(os.path.dirname(seq_path), "film", "pace.json")
    with open(seq_path, "r") as fh:
        seq = json.load(fh)
    pace = build_pace(seq, args.target_sec, source_sha=_sha8(seq_path))
    validate_pace(pace)

    out = os.path.abspath(out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    tmp = out + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(pace, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, out)

    s = sum(x["frames"] for x in pace["stages"])
    print("pace.json -> %s" % out)
    print("target=%.3fs fps=%d stages=%d source_sha=%s"
          % (args.target_sec, pace["fps"], len(pace["stages"]),
             pace["source_sha"]))
    print("对账: total_frames=%d  Σframes=%d  %s"
          % (pace["total_frames"], s,
             "一致" if s == pace["total_frames"] else "不一致!!"))
    return 0 if s == pace["total_frames"] else 1


if __name__ == "__main__":
    sys.exit(main())
