# -*- coding: utf-8 -*-
"""P3-T3 独立 validator 双实现对拍测试.

三支钉(计划 Task 3 Step 1)+ import 隔离子进程探针(P2-T5 同款纪律):
  1. 真账 stride-7 全帧逐键等值(film_state vs film_verify 独立算法);
  2. 末帧 visible==入日程集 3931 且与 excluded 幻影 2004 交集空
     (双实现分别断言);
  3. 副本删一条 PLACE_STONE → validator 必报缺(不许静默同错, 真账只读)。
只读 3d/out 真账工件; blender-free; Python 3.9.6。
"""
import inspect
import json
import os
import subprocess
import sys

import pytest

REPO3D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_3D = os.path.join(REPO3D, "3d")
for _p in (_3D, os.path.join(_3D, "film")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from film_state import load_pace, state_at_frame  # noqa: E402
import film_verify  # noqa: E402

_PACE_PATH = os.path.join(_3D, "out", "film", "pace.json")
_SEQ_PATH = os.path.join(_3D, "out", "sequence.json")
_LEDGER_PATH = os.path.join(_3D, "out", "ledger_sequenced.json")

_STATE_KEYS = {"stage", "event_cursor", "visible", "centering_up",
               "wedge_lambda", "phase"}


# ── 1. 真账双实现逐帧对拍(stride-7 = 全 stage 覆盖) ──

def test_dual_impl_frame_by_frame_real():
    pace = load_pace(_PACE_PATH)
    seq = json.load(open(_SEQ_PATH))
    total = pace["total_frames"]
    assert total == 7200 and len(pace["stages"]) == 408   # 真账口径钉
    n = 0
    for f in range(0, total, 7):
        ref = state_at_frame(pace, seq, f)
        mine = film_verify.expected_state(f, _PACE_PATH, _SEQ_PATH)
        assert set(mine) == _STATE_KEYS                   # 键面同构
        assert isinstance(mine["visible"], frozenset)     # 容器同构
        assert isinstance(mine["centering_up"], frozenset)
        assert isinstance(mine["wedge_lambda"], dict)
        assert isinstance(mine["phase"], str)
        assert ref == mine, "帧 %d 双实现不一致" % f
        n += 1
    assert n == 1029                                      # 0..7199 步 7


# ── 2. 幻影 2004 永不可见(双实现分别断言) ──

def test_phantom_never_visible_real():
    pace = load_pace(_PACE_PATH)
    seq = json.load(open(_SEQ_PATH))
    ledger = json.load(open(_LEDGER_PATH))
    universe = set(s["id"] for s in ledger["stones"])
    scheduled = set(e["stone_id"] for e in seq["events"]
                    if e["etype"] == "PLACE_STONE")
    phantom = universe - scheduled
    assert len(universe) == 5935                          # 石账口径钉
    assert len(scheduled) == 3931 and len(phantom) == 2004
    total = pace["total_frames"]
    for label, getter in (
            ("film_state", lambda f: state_at_frame(pace, seq, f)),
            ("film_verify",
             lambda f: film_verify.expected_state(f, _PACE_PATH, _SEQ_PATH))):
        vis = getter(total - 1)["visible"]
        assert len(vis) == 3931, label                    # 末帧恰日程集
        assert vis == scheduled, label                    # 不多不少
        assert vis & phantom == frozenset(), label        # 交集空


# ── 3. 负控篡改: 删一条 PLACE_STONE → validator 报缺(不许静默同错) ──

def test_verify_negative_tamper(tmp_path):
    pace = load_pace(_PACE_PATH)
    seq = json.load(open(_SEQ_PATH))
    f_last = pace["total_frames"] - 1
    # 篡改前基线: 真账末帧双实现一致
    assert state_at_frame(pace, seq, f_last) == \
        film_verify.expected_state(f_last, _PACE_PATH, _SEQ_PATH)
    # 副本删一条中段 PLACE_STONE(真账只读)
    tam = json.load(open(_SEQ_PATH))
    idx = next(i for i, e in enumerate(tam["events"])
               if e["etype"] == "PLACE_STONE" and e["seq"] > 100)
    victim = tam["events"].pop(idx)
    p = tmp_path / "sequence_tampered.json"
    p.write_text(json.dumps(tam, ensure_ascii=False), encoding="utf-8")
    # validator 必报缺(独立结构门, film_state 没有的防线)
    with pytest.raises(ValueError) as ei:
        film_verify.expected_state(0, _PACE_PATH, str(p))
    assert "报缺" in str(ei.value)
    # 证明"单靠双实现等值"会静默同错: 参照实现不报错、只是悄悄少一块石
    ref = state_at_frame(pace, json.load(open(str(p))), f_last)
    assert victim["stone_id"] not in ref["visible"]


# ── 4. import 隔离子进程探针(P2-T5 同款纪律) ──

def test_import_isolation_probe():
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(
        [_3D, os.path.join(_3D, "film")]))
    # 探针: import film_verify 不得连带 import film_state
    prog = ("import sys, film_verify as fv; "
            "assert fv.__file__.endswith('film_verify.py'); "
            "sys.exit(0 if 'film_state' not in sys.modules else 3)")
    r = subprocess.run([sys.executable, "-c", prog], env=env,
                       capture_output=True)
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    # 探针自证有效(阴性对照): 同环境 import film_state 必在 sys.modules
    prog2 = "import sys, film_state; " \
            "sys.exit(0 if 'film_state' in sys.modules else 3)"
    r2 = subprocess.run([sys.executable, "-c", prog2], env=env,
                        capture_output=True)
    assert r2.returncode == 0, r2.stderr.decode("utf-8", "replace")
    # 状态计算路径源码级隔离(expected_state 不引用 film_state)
    assert "film_state" not in inspect.getsource(film_verify.expected_state)
