#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# e30_shikongqiao_video/3d/film/film_verify.py
"""P3-T3 独立 validator: 与 film_state 双实现对拍(算法刻意不同)。

语义规格唯一来源: p3-task-2-report §2 判定规则全表(=film_state 模块
docstring §1-6)。本模块 **不 import film_state**(import 隔离, 子进程
探针测试钉死): 两实现同错=互相失守, 独立性是 validator 的存在理由;
CLI 对拍路径惰性 import film_state 仅作参照物。

算法差异(对照 film_state 的「事件按 seq 排序 + bisect」):
  1. 帧→stage: 帧前缀展开直接寻址表 frame2stage —— 逐 stage 把其
     frames 份自身下标 append 进表, 查帧 O(1), 无 bisect、不读 start
     字段(用 Σframes==total_frames 前缀和自洽门替代)。
  2. 事件→stage: seq 前缀展开直接寻址表 seq2stage(stage event_range
     逐段扩展), 事件按所属 stage 分桶, 无全局 seq 排序、无 bisect。
  3. 状态推进: **逐 stage 重算的 stage 前缀和表 snapshots[i]** ——
     visible/erected/cleared/wedge_lambda/phase 都在 stage 边界自
     上一 stage 快照增量重算(「整拍语义」: 状态只在 stage 边界变),
     查询 = 表项重组 6 键; film_state 是每次查询按 cursor 全局扫。
  4. validator 结构门(film_state 没有的完整性防线, 负控篡改测钉):
     ① Σstage.frames == total_frames;
     ② stage event_range 无缝恰覆盖 [1..N] 事件, 每桶计数==range 宽
       —— 缺/多/重 seq 事件一律 ValueError 报缺, 不许静默同错;
     ③ stage frames ≥ 1(零宽节拍在 pace 契约外)。

公开接口(计划 Task 3 签名钉死):
    expected_state(frame, pace_path, seq_path) -> dict
        6 键 {stage, event_cursor, visible, centering_up,
        wedge_lambda, phase} 与 film_state.state_at_frame 逐键同构
        (容器类型也同构: frozenset/frozenset/dict/str), 否则对拍无意义。
    main(argv) -> int   # CLI 对拍报告

CLI:
    python3 3d/film/film_verify.py --pace 3d/out/film/pace.json \
        --sequence 3d/out/sequence.json [--stride N] [--json]
    逐帧对拍 film_state.state_at_frame vs expected_state, 输出首违例
    帧+差异键; 退出码 0=全帧一致 / 1=对拍违例 / 2=validator 报缺。

判定规则逐条对齐 p3-task-2-report §2(在此不复抄全表); 两条约定推论
(整拍推进 / erect 取 event_range[1])同样生效。词表单源 import 自
3d/events.py, 本模块不复制词表容器。语义分歧清单见
p3-task-3-report.md §4。

Python 3.9.6; blender-free; 3d/out 只读。
"""
import argparse
import json
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)          # 3d/ — 使 `import events` 与
if _PARENT not in sys.path:               # `python3 3d/film/film_verify.py`
    sys.path.insert(0, _PARENT)           # 直跑两种入口都成立

from events import DECENTERING_TYPES, EVENT_TYPES  # noqa: E402  词表单源

__all__ = ["expected_state", "main"]

# 单事件名与 P2 词表一致性自检(import 即校验, 防拼写漂移)
for _t in ("PLACE_STONE", "CENTERING_CLEAR"):
    if _t not in EVENT_TYPES:
        raise AssertionError("词表漂移: %r 不在 events.EVENT_TYPES" % _t)

_STATE_KEYS = ("stage", "event_cursor", "visible", "centering_up",
               "wedge_lambda", "phase")


# ── 结构门(validator 完整性防线, 与状态语义正交) ──

def _load_json(path, what):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except OSError as exc:
        raise ValueError("无法读 %s %s: %s" % (what, path, exc))
    except json.JSONDecodeError as exc:
        raise ValueError("%s 不是合法 JSON %s: %s" % (what, path, exc))


def _stage_tables(pace):
    """帧前缀展开表 + range 校验; 返回 (frame2stage, stages)。"""
    if not isinstance(pace, dict):
        raise ValueError("pace 须为 dict")
    for k in ("fps", "total_frames", "stages"):
        if k not in pace:
            raise ValueError("pace 缺顶键 %r" % k)
    stages = pace["stages"]
    total = pace["total_frames"]
    if not isinstance(total, int) or isinstance(total, bool) or total < 0:
        raise ValueError("total_frames 非法: %r" % (total,))
    frame2stage = []
    for i, st in enumerate(stages):
        fr = st.get("frames") if isinstance(st, dict) else None
        if not isinstance(fr, int) or isinstance(fr, bool) or fr < 1:
            raise ValueError("stage #%d frames 非法(须正整数): %r" % (i, fr))
        frame2stage.extend([i] * fr)
    if len(frame2stage) != total:
        raise ValueError("Σstage.frames=%d != total_frames=%d(前缀和不自洽)"
                         % (len(frame2stage), total))
    return frame2stage, stages


def _seq_tables(seqdoc, stages):
    """seq 前缀展开表 + 事件分桶 + 恰覆盖计数门; 返回 (buckets, n_ev)。

    缺事件(篡改删事件)在此 ValueError 报缺 —— 这是「双实现必不一致
    或 validator 报缺」负控的实现点: 删事件后 range 仍声称覆盖被删
    seq, 表扩展越界即红; 中段缺则桶计数短缺, 同样红。
    """
    events = seqdoc.get("events") if isinstance(seqdoc, dict) else None
    if not isinstance(events, list):
        raise ValueError("sequence 缺 events 列表")
    n_ev = len(events)
    seq2stage = [None] * (n_ev + 1)          # 按 seq 1..N 直接寻址
    for i, st in enumerate(stages):
        a, b = st.get("first_event"), st.get("last_event")
        if not isinstance(a, int) or not isinstance(b, int) \
                or isinstance(a, bool) or isinstance(b, bool) or a > b:
            raise ValueError("stage #%d event_range 非法: %r..%r" % (i, a, b))
        if a < 1:
            raise ValueError("stage #%d first_event<1: %r" % (i, a))
        if b > n_ev:
            raise ValueError("validator 报缺: stage #%d 声称覆盖至 seq=%d,"
                             " 但事件总数仅 %d(疑缺事件)" % (i, b, n_ev))
        for s in range(a, b + 1):
            if seq2stage[s] is not None:
                raise ValueError("validator 报缺: seq=%d 被多个 stage range"
                                 " 覆盖(重叠)" % s)
            seq2stage[s] = i
    gaps = [s for s in range(1, n_ev + 1) if seq2stage[s] is None]
    if gaps:
        raise ValueError("validator 报缺: seq=%s 不被任何 stage range 覆盖"
                         % gaps[:5])
    buckets = [[] for _ in stages]
    for pos, e in enumerate(events):
        s = e.get("seq") if isinstance(e, dict) else None
        if not isinstance(s, int) or isinstance(s, bool) or not (1 <= s <= n_ev):
            raise ValueError("事件 #%d seq 非法: %r" % (pos, s))
        buckets[seq2stage[s]].append(e)
    for i, st in enumerate(stages):
        want = st["last_event"] - st["first_event"] + 1
        if len(buckets[i]) != want:
            raise ValueError("validator 报缺: stage #%d(%s) 事件桶 %d != "
                             "range 宽 %d(缺/多事件)"
                             % (i, st.get("id"), len(buckets[i]), want))
    return buckets, n_ev


# ── 语义规则(p3-task-2-report §2 逐条; 实现算法与 film_state 无关) ──

def _hole_lambda(evs, cursor):
    """规则 5 单孔: 未出 START→0.0; 已出 CLEAR→1.0; 否则最近 WEDGE 的
    load_lambda; START 后未出楔→0.0。判据按事件类型显式分流, 不靠
    CLEAR 与末档 λ 的数值巧合。evs 须按 seq 升序。"""
    started = False
    cleared = False
    last_wedge = None
    for e in evs:
        if e["seq"] > cursor:
            break
        t = e["etype"]
        if t == "DECENTER_START":
            started = True
        elif t == "CENTERING_CLEAR":
            cleared = True
        elif t == "WEDGE_RELEASE":
            last_wedge = e
    if not started:
        return 0.0
    if cleared:
        return 1.0
    if last_wedge is not None:
        return last_wedge["load_lambda"]
    return 0.0


def _phase(cursor, first_dstart, last_clear):
    """规则 6: 全局三段; 无落架事件恒 BUILD; 有 START 无 CLEAR 恒 DECENTER。"""
    if first_dstart is None or cursor < first_dstart:
        return "BUILD"
    if last_clear is None or cursor < last_clear:
        return "DECENTER"
    return "DONE"


class _Index(object):
    """逐 stage 重算的 stage 前缀和表(一次构建, O(1) 查询)。"""

    __slots__ = ("frame2stage", "stages", "snapshots", "total_frames")


def _build_index(pace, seqdoc):
    frame2stage, stages = _stage_tables(pace)
    buckets, _n_ev = _seq_tables(seqdoc, stages)
    events = seqdoc["events"]

    # 全局相位阈值(规则 6): 全账首 START / 末 CLEAR 的 seq
    dstart = sorted(e["seq"] for e in events if e["etype"] == "DECENTER_START")
    clears = sorted(e["seq"] for e in events if e["etype"] == "CENTERING_CLEAR")
    first_dstart = dstart[0] if dstart else None
    last_clear = clears[-1] if clears else None

    # 单孔落架事件表(规则 5 key universe = 全账有落架事件的孔, 与 cursor
    # 无关 —— 真账 frame0 即 17 孔全 0.0; 非 17 孔假设, 无落架事件则空)
    hole_evs = {}
    for e in events:
        if e["etype"] in DECENTERING_TYPES:
            hole_evs.setdefault(e["hole"], []).append(e)
    for lst in hole_evs.values():
        lst.sort(key=lambda e: e["seq"])

    # 立架 stage 表(规则 4): 名以 .CENTER_ERECT 结尾, 按 event_range[1] 升序
    sq = seqdoc.get("sequence") or []
    erect_list = sorted(
        ((s["event_range"][1], s["centering_id"]) for s in sq
         if isinstance(s, dict)
         and isinstance(s.get("stage"), str)
         and s["stage"].endswith(".CENTER_ERECT")
         and s.get("centering_id") is not None),
        key=lambda p: p[0])

    # 逐 stage 重算: 自上一快照增量推进(整拍语义, 状态只在 stage 边界变)
    idx = _Index()
    idx.frame2stage = frame2stage
    idx.stages = stages
    idx.total_frames = pace["total_frames"]
    vis = frozenset()
    erected = frozenset()
    cleared = set()
    wedge = dict((h, 0.0) for h in hole_evs)   # 全宇宙键开局即 0.0(规则 5)
    ep = 0
    snapshots = []
    for i, st in enumerate(stages):
        cur = st["last_event"]
        b = buckets[i]
        new_vis = frozenset(e["stone_id"] for e in b
                            if e["etype"] == "PLACE_STONE")
        if new_vis:
            vis = vis | new_vis                      # 规则 3: PLACE_STONE 累积
        for e in b:
            if e["etype"] == "CENTERING_CLEAR":
                cleared.add(e["stone_id"])           # 规则 4: 卸架走事件流
        while ep < len(erect_list) and erect_list[ep][0] <= cur:
            erected = erected | frozenset((erect_list[ep][1],))
            ep += 1                                  # 规则 4: erange[1]≤cursor
        touched = set(e["hole"] for e in b
                      if e["etype"] in DECENTERING_TYPES)
        if touched:
            nw = dict(wedge)                         # 写时复制, 快照不可变
            for h in touched:
                nw[h] = _hole_lambda(hole_evs[h], cur)
            wedge = nw
        centering_up = erected - cleared             # frozenset - set → frozenset
        snapshots.append((cur, vis, centering_up, wedge,
                          _phase(cur, first_dstart, last_clear)))
    idx.snapshots = snapshots
    return idx


_CACHE = {}


def _get_index(pace_path, seq_path):
    ap = os.path.abspath(pace_path)
    asp = os.path.abspath(seq_path)
    sp = os.stat(ap)
    ss = os.stat(asp)
    key = (ap, asp, sp.st_mtime_ns, sp.st_size, ss.st_mtime_ns, ss.st_size)
    idx = _CACHE.get(key)
    if idx is None:
        pace = _load_json(ap, "pace")
        seqdoc = _load_json(asp, "sequence")
        idx = _build_index(pace, seqdoc)
        _CACHE[key] = idx
    return idx


def expected_state(frame, pace_path, seq_path):
    """帧号 → 建造状态 dict(独立实现, 与参照实现逐键同构)。

    frame ∉ [0, total_frames) → IndexError(与参照实现边界契约一致)。
    pace/sequence 结构或事件完整性问题 → ValueError(validator 报缺)。
    """
    idx = _get_index(pace_path, seq_path)
    if not isinstance(frame, int) or isinstance(frame, bool) \
            or frame < 0 or frame >= idx.total_frames:
        raise IndexError("frame %r 越界 [0,%d)" % (frame, idx.total_frames))
    i = idx.frame2stage[frame]
    cur, vis, up, wedge, phase = idx.snapshots[i]
    return {"stage": i, "event_cursor": cur, "visible": vis,
            "centering_up": up, "wedge_lambda": wedge, "phase": phase}


# ── CLI 对拍(此处才惰性 import film_state 作参照物) ──

def _diff_states(a, b):
    """逐键差异: {key: (repr_a 截断, repr_b 截断)}; 键序按 _STATE_KEYS。"""
    out = {}
    for k in _STATE_KEYS:
        va, vb = a.get(k), b.get(k)
        if va != vb:
            out[k] = (repr(va)[:220], repr(vb)[:220])
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="P3-T3 独立 validator 双实现对拍(film_state vs film_verify)")
    ap.add_argument("--pace", required=True, help="pace.json 路径")
    ap.add_argument("--sequence", required=True, help="sequence.json 路径")
    ap.add_argument("--stride", type=int, default=1,
                    help="帧抽样步长(默认 1=全帧)")
    ap.add_argument("--json", action="store_true", help="机器可读 JSON 报告")
    args = ap.parse_args(argv)
    if args.stride < 1:
        ap.error("--stride 须 >=1")

    report = {"pace": args.pace, "sequence": args.sequence,
              "stride": args.stride, "compared": 0, "equal": None,
              "first_violation": None, "validator_error": None,
              "elapsed_s": {}}

    def emit():
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            if report["validator_error"]:
                print(str(report["validator_error"]))
            elif report["equal"]:
                print("全帧一致: %d/%d 帧 (stride=%d)"
                      % (report["compared"], report["compared"], args.stride))
            elif report["first_violation"]:
                fv = report["first_violation"]
                print("首违例帧 f=%d 差异键: %s"
                      % (fv["frame"], ",".join(fv["keys"])))
                for k, (ra, rb) in sorted(fv["detail"].items()):
                    print("  %s.film_state = %s" % (k, ra))
                    print("  %s.film_verify = %s" % (k, rb))
            for k, v in sorted(report["elapsed_s"].items()):
                print("耗时 %s: %.3fs" % (k, v))

    try:
        from film_state import load_pace, state_at_frame  # 惰性: 仅对拍路径
    except ImportError as exc:
        report["validator_error"] = "参照实现 film_state 不可用: %s" % exc
        emit()
        return 2
    try:
        pace = load_pace(args.pace)
        seqdoc = _load_json(os.path.abspath(args.sequence), "sequence")
    except ValueError as exc:
        report["validator_error"] = str(exc)
        emit()
        return 2

    total = pace["total_frames"]
    report["total_frames"] = total
    frames = range(0, total, args.stride)
    t0 = time.perf_counter()
    for f in frames:
        try:
            mine = expected_state(f, args.pace, args.sequence)
        except ValueError as exc:
            report["validator_error"] = str(exc)
            emit()
            return 2
        ref = state_at_frame(pace, seqdoc, f)
        report["compared"] += 1
        diff = _diff_states(ref, mine)
        if diff:
            report["equal"] = False
            report["first_violation"] = {
                "frame": f,
                "keys": sorted(diff),
                "detail": dict(diff),
            }
            emit()
            return 1
    report["elapsed_s"]["dual_compare"] = time.perf_counter() - t0
    report["equal"] = True
    emit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
