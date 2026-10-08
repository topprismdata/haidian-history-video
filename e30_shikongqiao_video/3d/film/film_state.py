#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# e30_shikongqiao_video/3d/film/film_state.py
"""P3-T2 帧→状态机: pace.json 帧号 → 建造状态(纯函数, blender-free)。

接口(计划 Task 2 签名钉死, T3/T5 消费):
    load_pace(path) -> dict
    stage_at_frame(pace, f) -> int            # 越界 raise IndexError
    state_at_frame(pace, sequence, f) -> dict # 键面恰为 _STATE_KEYS

═══ 判定规则全表(T3 film_verify 独立实现的唯一接口文档) ═══

1. stage_at_frame(pace, f):
   stage i 拥有帧区间 [start_i, end_i)(T1 保证 start 连续无缝、首 stage
   start=0、末 end=total_frames); 实现 bisect_right(starts, f)-1。
   f ∉ [0, total_frames) → IndexError。

2. event_cursor(f) = stages[stage_at_frame(f)]["last_event"]:
   「stage 首帧即本 stage 事件全部就位」——pace 的帧是 stage 粒度节拍,
   stage 内不再细分事件推进。计划 Task2 Step1 合成测钉死: frame 0 →
   cursor=stage0.last_event=5; 末帧 → cursor=30。落架波同理按 stage 整拍
   推进(WEDGE.1 stage 首帧 17 孔同时到 0.25 档, 不在 stage 内逐孔走)。

3. visible: frozenset[石 id] = {e.stone_id | etype=="PLACE_STONE" 且
   e.seq <= cursor}。事件字段名是 stone_id(计划稿写 `stone` 系偏差, 按真账)。
   CLOSE_RING 真账不引石(stone_id=None), HOLD_EVENT 的 stone_id 是券架 id,
   二者天然不入 visible。幻影 2004 块(5935 石账 − 3931 日程)在 sequence
   无 PLACE_STONE 事件, 结构上永不可见(test_real_phantom_2004 钉)。

4. centering_up: frozenset[券架 id "CEN-ARCHxx"] = erected − cleared
   erected = {s.centering_id | stage 名以 ".CENTER_ERECT" 结尾
              且 s.event_range[1] <= cursor}
       —— CENTER_ERECT 是 stage 名后缀非 etype(真账该 stage 装单个
       HOLD_EVENT, stone_id=券架 id, sequencer.py R2 发射处); 在场判定
       优先走 stage 表 centering_id+event_range。
   cleared = {e.stone_id | etype=="CENTERING_CLEAR" 且 e.seq <= cursor}
       —— 卸架判定走事件流: DECENTER.CLEAR.WAVE 是全局波次 stage
       (centering_id=null, 一 stage 装 17 孔 CLEAR 事件), 只能按事件取。

5. wedge_lambda: dict[孔号 → float]。key universe = {e.hole | etype 在
   DECENTERING_TYPES}(λ 挂事件 hole 字段不挂 stage 名——DECENTER.* 全局
   波次 stage 一档装 17 孔; 非 17 孔假设, 有落架事件的孔才有键)。
   每孔按 seq 升序判:
       未出 DECENTER_START            → 0.0
       已出 CENTERING_CLEAR           → 1.0
       否则最近一次 WEDGE_RELEASE 的 load_lambda(真账四档
       0.25/0.5/0.75/1.0; START 后未出楔为 0.0)
   CLEAR 与末档 λ=1.0 真账数值重合, 但判据按事件类型显式分流, 不靠数值巧合。

6. phase: str, 全局三段[设计选择·计划未钉词表]:
       cursor < 全账首 DECENTER_START seq   → "BUILD"
       cursor < 全账末 CENTERING_CLEAR seq  → "DECENTER"
       否则                                  → "DONE"
   无落架事件的合成小账恒 "BUILD"。

事件词表单源 import 自 3d/events.py(EVENT_TYPES / DECENTERING_TYPES),
本模块不复制词表容器; 单事件名比较("PLACE_STONE"/"CENTERING_CLEAR")
与 events.py 校验代码同风格, 且经 _VOCAB_GUARD 对 EVENT_TYPES 自检。

Python 3.9.6; P2 工件只读; 全量 pytest 分片见 p3-task-2-report §验证。
"""
import bisect
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)          # 3d/ — 使 `import events` 与
if _PARENT not in sys.path:               # `python3 3d/film/film_render.py`
    sys.path.insert(0, _PARENT)           # 直跑两种入口都成立

from events import DECENTERING_TYPES, EVENT_TYPES  # noqa: E402  词表单源

__all__ = ["load_pace", "stage_at_frame", "state_at_frame"]

# 单事件名与 P2 词表一致性自检(import 即校验, 防拼写漂移)
for _t in ("PLACE_STONE", "CENTERING_CLEAR"):
    if _t not in EVENT_TYPES:
        raise AssertionError("词表漂移: %r 不在 events.EVENT_TYPES" % _t)

_STATE_KEYS = ("stage", "event_cursor", "visible", "centering_up",
               "wedge_lambda", "phase")


def load_pace(path):
    """读 pace.json(T1 schema: fps/total_frames/stages) → dict, 只读。

    深校验归 pace_build.validate_pace(T1 所有), 此处只挡缺顶键。
    """
    with open(path, "r", encoding="utf-8") as fh:
        pace = json.load(fh)
    for k in ("fps", "total_frames", "stages"):
        if k not in pace:
            raise ValueError("pace 缺顶键 %r: %s" % (k, path))
    return pace


def stage_at_frame(pace, f):
    """帧号 → stage 下标; stage i 拥有 [start_i, end_i); 越界 IndexError."""
    total = pace["total_frames"]
    if f < 0 or f >= total:
        raise IndexError("frame %r 越界 [0, %s)" % (f, total))
    idx = bisect.bisect_right([s["start"] for s in pace["stages"]], f) - 1
    if idx < 0:
        raise IndexError("frame %r 早于首 stage start(pace 缺陷)" % (f,))
    return idx


def state_at_frame(pace, sequence, f):
    """帧号 → {"stage","event_cursor","visible","centering_up",
    "wedge_lambda","phase"}, 规则见模块 docstring §1-6。纯函数无副作用。"""
    si = stage_at_frame(pace, f)
    cursor = pace["stages"][si]["last_event"]

    events = sequence.get("events") or ()
    # P2 保证 seq 全局严格递增; sorted 对有序输入近 O(n), 防御乱序账
    evs = sorted(events, key=lambda e: e["seq"])

    visible = set()
    cleared_cen = set()      # 已卸券架 id(CENTERING_CLEAR.stone_id)
    started = set()          # 已 START 的孔
    cleared_arch = set()     # 已 CLEAR 的孔
    lam = {}                 # 孔 → 最近 WEDGE_RELEASE 档
    universe = set()         # 有落架事件的孔
    first_ds = None          # 全账首 DECENTER_START seq(phase 用)
    last_clr = None          # 全账末 CENTERING_CLEAR seq(phase 用)

    for e in evs:
        etype = e.get("etype")
        seq = e["seq"]
        if etype in DECENTERING_TYPES:
            hole = e.get("hole")
            if hole is not None:
                universe.add(hole)
            if etype == "DECENTER_START":
                if first_ds is None or seq < first_ds:
                    first_ds = seq
            elif etype == "CENTERING_CLEAR":
                if last_clr is None or seq > last_clr:
                    last_clr = seq
            if seq > cursor:
                continue
            if etype == "DECENTER_START":
                started.add(hole)
            elif etype == "WEDGE_RELEASE":
                lam[hole] = e.get("load_lambda")   # seq 升序 → 后写=最近档
            else:
                cleared_arch.add(hole)
                cid = e.get("stone_id")
                if cid is not None:
                    cleared_cen.add(cid)
            continue
        if seq > cursor:
            continue
        if etype == "PLACE_STONE":
            sid = e.get("stone_id")
            if sid is not None:
                visible.add(sid)

    erected = set()
    for st in sequence.get("sequence") or ():
        cid = st.get("centering_id")
        erange = st.get("event_range")
        if (cid and erange and erange[1] <= cursor
                and st.get("stage", "").endswith(".CENTER_ERECT")):
            erected.add(cid)

    wedge = {}
    for arch in sorted(universe):
        if arch in cleared_arch:
            wedge[arch] = 1.0
        elif arch in started:
            wedge[arch] = lam.get(arch, 0.0)
        else:
            wedge[arch] = 0.0

    if first_ds is None or cursor < first_ds:
        phase = "BUILD"
    elif last_clr is None or cursor < last_clr:
        phase = "DECENTER"
    else:
        phase = "DONE"

    return {"stage": si, "event_cursor": cursor,
            "visible": frozenset(visible),
            "centering_up": frozenset(erected - cleared_cen),
            "wedge_lambda": wedge, "phase": phase}
