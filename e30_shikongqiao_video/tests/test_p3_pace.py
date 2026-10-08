"""P3-T1 pace.json 生成器测试.

计划 Task 1 Step 1 逐字 + Step 4 附加测(scale_exact 三档 / CLOSE_RING 加成).
只读 3d/out/sequence.json, 产物写 /tmp, 不触 blender.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

REPO3D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SEQ = os.path.join(REPO3D, "3d", "out", "sequence.json")


def _build(out_name, target_sec, prologue_sec=None):
    """跑 CLI 生成 pace 并返回 dict(产物落 /tmp/p3test)."""
    os.makedirs("/tmp/p3test", exist_ok=True)
    out = os.path.join("/tmp/p3test", out_name)
    cmd = [sys.executable, "3d/film/pace_build.py",
           "--sequence", "3d/out/sequence.json",
           "--target-sec", str(target_sec), "--out", out]
    if prologue_sec is not None:
        cmd += ["--prologue-sec", str(prologue_sec)]
    subprocess.run(cmd, check=True, cwd=REPO3D)
    return json.load(open(out))


def _has_bonus(name, is_last):
    """普通 stage 判定: 无任何类型加成/倍率/收尾加成(词表对齐真账 stage 名)."""
    return (name.endswith("CLOSE_RING") or ".WEDGE." in name
            or name.endswith("CENTER_ERECT") or ".DSTART." in name
            or ".CLEAR." in name or ".R7." in name or "BRIDGE_DONE" in name
            or name.startswith("ARCH01.") or is_last)


def test_pace_build_schema_and_conservation():
    import json, subprocess, sys, os
    out = "/tmp/p3test/pace.json"; os.makedirs("/tmp/p3test", exist_ok=True)
    subprocess.run([sys.executable, "3d/film/pace_build.py",
                    "--sequence", "3d/out/sequence.json",
                    "--target-sec", "240", "--out", out], check=True, cwd=REPO3D)
    p = json.load(open(out))
    assert p["fps"] == 30
    assert len(p["stages"]) == 408
    # 守恒: start/end 连续无缝, 末帧==total_frames
    assert p["stages"][0]["start"] == 0
    for a, b in zip(p["stages"], p["stages"][1:]):
        assert a["end"] == b["start"]
    assert p["stages"][-1]["end"] == p["total_frames"]
    # 时长在 240s ±2%（缩放后）
    assert abs(p["total_frames"] - 7200) <= 144
    # 单调: frames>=1
    assert all(s["frames"] >= 1 for s in p["stages"])
    # schema 钉死: 逐 stage 五要素 + 溯源字段
    for s in p["stages"]:
        assert set(s) == {"id", "first_event", "last_event", "frames",
                          "pad_frames", "start", "end"}
        assert s["pad_frames"] == 0
        assert s["first_event"] <= s["last_event"]
    assert p["generated_by"] == "pace_build"
    assert p["source_sha"] == "1cefc071"


def test_pace_scale_exact():
    # 最大余数法: 3 档 target-sec 下 Σframes == total_frames 精确相等
    for tgt in (60, 240, 600):
        p = _build("pace_%d.json" % tgt, tgt)
        assert p["total_frames"] == tgt * 30, tgt
        assert sum(s["frames"] for s in p["stages"]) == p["total_frames"], tgt


def test_pace_build_prologue_s000():
    """序幕题卡段(T8): --prologue-sec 5 前置 S000(无事件 (0,0), cursor=0),
    内容段节拍零改动, total 相应增长, generated_by 记变更, validate 绿;
    中段 (0,0) 与首段 (0,b>0) 一律拒绝(无事件段唯一合法编码合同)."""
    _3d = os.path.join(REPO3D, "3d")
    for _p in (_3d, os.path.join(_3d, "film")):
        if _p not in sys.path:
            sys.path.insert(0, _p)
    import pytest
    import film_state as FS
    import film_verify as FV
    import pace_build as PB
    p = _build("pace_pro5.json", 240, prologue_sec=5.0)
    base = _build("pace_nopro.json", 240)
    assert len(p["stages"]) == 409 and len(base["stages"]) == 408
    s0, s1 = p["stages"][0], p["stages"][1]
    assert s0["id"] == "S000"
    assert (s0["first_event"], s0["last_event"]) == (0, 0)
    assert s0["frames"] == 150 and (s0["start"], s0["end"]) == (0, 150)
    assert (s1["id"], s1["first_event"], s1["start"]) == ("S001", 1, 150)
    # 内容段节拍零改动: frames 与事件区间逐段同无序幕版
    assert [(s["frames"], s["first_event"], s["last_event"])
            for s in p["stages"][1:]] == \
        [(s["frames"], s["first_event"], s["last_event"])
            for s in base["stages"]]
    assert p["total_frames"] == 7200 + 150 == base["total_frames"] + 150
    assert p["generated_by"] == "pace_build --prologue-sec 5"
    assert base["generated_by"] == "pace_build"          # 缺省零变
    # 状态机零改动: S000 全段 cursor=0 空场; S001 首帧整拍推进
    pace_p = os.path.join("/tmp/p3test", "pace_pro5.json")
    seq = json.load(open(_SEQ))
    st0 = FS.state_at_frame(p, seq, 0)
    assert st0["event_cursor"] == 0 and st0["visible"] == frozenset()
    assert FS.state_at_frame(p, seq, 149)["event_cursor"] == 0
    st150 = FS.state_at_frame(p, seq, 150)
    assert st150["event_cursor"] == 10 and len(st150["visible"]) == 10
    # 双实现 S000 同读(validator 桶宽 0 放行)
    assert FV.expected_state(0, pace_p, _SEQ) == st0
    # 序幕合同负控: 中段 (0,0) 与首段 (0,3) 均红
    bad_mid = json.loads(json.dumps(p))
    bad_mid["stages"][5]["first_event"] = 0
    bad_mid["stages"][5]["last_event"] = 0
    with pytest.raises(ValueError, match="0 非法"):
        PB.validate_pace(bad_mid)
    bad_open = json.loads(json.dumps(p))
    bad_open["stages"][0]["last_event"] = 3
    with pytest.raises(ValueError, match="0 非法"):
        PB.validate_pace(bad_open)


def test_pace_close_ring_boost():
    # CLOSE_RING stage 的 frames ≥ 同事件数普通 stage 的 2 倍
    seq = json.load(open(_SEQ))["sequence"]
    name = {s["id"]: s["stage"] for s in seq}
    nev = {s["id"]: s["event_range"][1] - s["event_range"][0] + 1
           for s in seq}
    p = _build("pace.json", 240)
    stages = p["stages"]
    last_id = stages[-1]["id"]
    plain = [s for s in stages if not _has_bonus(name[s["id"]],
                                                 s["id"] == last_id)]
    crs = [s for s in stages if name[s["id"]].endswith("CLOSE_RING")]
    assert len(crs) == 17  # 真账每孔恰一次合龙
    for cr in crs:
        k = nev[cr["id"]]
        peers = [s for s in plain if nev[s["id"]] == k]
        assert peers, "同事件数(%d)普通 stage 缺席" % k
        assert cr["frames"] >= 2 * max(s["frames"] for s in peers), \
            (name[cr["id"]], cr["frames"], [s["frames"] for s in peers])


# ═══════════════ P3-T7 pace_writeback(唯一回写通道)+Remotion 接线 ═══════════════
# 语义(计划 Task 7): audio_table={stage_id: audio_sec} →
#   pad_frames = max(0, ceil(audio_sec*fps) - frames)  (音频比画面长才补)
#   start/end 级联重算, total_frames 相应增长; 其余字段逐字节不变;
#   原子写 + 两连跑幂等; 表外 stage pad 不动; 未知 stage id 拒绝(宁红不哑)。
# Remotion(src/e30film)侧: duration/fps/段边界一律 import 真账 pace.json,
#   禁 TS 自算帧号(grep 禁 fps*/常量换算标记), 由 bun 执行 TS 读数对拍。


_WB = "3d/film/pace_writeback.py"
_E30_SRC = os.path.join(os.path.dirname(REPO3D), "src", "e30film")


def _mini_pace(path):
    """3-stage 合成 mini pace: 与真账同 schema, 语义测试不耦合 408 stage."""
    pace = {
        "fps": 30, "total_frames": 60,
        "stages": [
            {"id": "A", "first_event": 1, "last_event": 10, "frames": 20,
             "pad_frames": 0, "start": 0, "end": 20},
            {"id": "B", "first_event": 11, "last_event": 16, "frames": 25,
             "pad_frames": 0, "start": 20, "end": 45},
            {"id": "C", "first_event": 17, "last_event": 18, "frames": 15,
             "pad_frames": 0, "start": 45, "end": 60},
        ],
        "generated_by": "pace_build", "source_sha": "deadbeef",
    }
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(pace, fh, ensure_ascii=False, indent=1)
    return path


def _wb(pace_path, table, out_path, expect_rc=0):
    """跑 pace_writeback CLI; table=dict → 落盘 JSON 再传入."""
    os.makedirs("/tmp/p3test", exist_ok=True)
    tbl = os.path.join("/tmp/p3test", "audio_table.json")
    with open(tbl, "w") as fh:
        json.dump(table, fh, ensure_ascii=False)
    r = subprocess.run([sys.executable, _WB, "--pace", pace_path,
                        "--audio-table", tbl, "--out", out_path],
                       cwd=REPO3D, capture_output=True, text=True)
    assert r.returncode == expect_rc, (r.returncode, r.stdout, r.stderr)
    return r


def test_writeback_only_writer():
    d = "/tmp/p3test"
    pace_p = _mini_pace(os.path.join(d, "wb_in.json"))
    out_p = os.path.join(d, "wb_out.json")
    _wb(pace_p, {"A": 1.5, "C": 0.1}, out_p)      # A: 45-20=25; C: 3<15→0
    p0 = json.load(open(pace_p))
    p1 = json.load(open(out_p))
    st0, st1 = p0["stages"], p1["stages"]
    # pad/边界/total 重算
    assert st1[0]["pad_frames"] == 25, st1[0]
    assert (st1[0]["start"], st1[0]["end"]) == (0, 45)
    assert (st1[1]["start"], st1[1]["end"]) == (45, 70)
    assert st1[1]["pad_frames"] == 0, "表外 stage pad 必须不动"
    assert st1[2]["pad_frames"] == 0, "音频短于画面 pad 钳 0"
    assert (st1[2]["start"], st1[2]["end"]) == (70, 85)
    assert p1["total_frames"] == 85
    # 守恒契约(padded 版): end-start==frames+pad, 连续无缝, 末 end==total
    for a, b in zip(st1, st1[1:]):
        assert a["end"] == b["start"]
    for s in st1:
        assert s["end"] - s["start"] == s["frames"] + s["pad_frames"]
        assert s["pad_frames"] >= 0
    assert st1[-1]["end"] == p1["total_frames"]
    assert sum(s["frames"] + s["pad_frames"] for s in st1) == p1["total_frames"]
    # 其余字段逐字节不变: 段序/五要素/顶层溯源全等
    assert [s["id"] for s in st1] == [s["id"] for s in st0]
    for a, b in zip(st0, st1):
        for k in ("id", "first_event", "last_event", "frames"):
            assert a[k] == b[k], (k, a, b)
        assert sorted(a) == sorted(b)
    for k in ("fps", "generated_by", "source_sha"):
        assert p0[k] == p1[k], k
    # 幂等: 同表对产物再跑一遍 → 逐字节相同; 且无 .tmp 残留(原子写)
    _wb(out_p, {"A": 1.5, "C": 0.1}, out_p)
    out2 = os.path.join(d, "wb_out2.json")
    _wb(out_p, {"A": 1.5, "C": 0.1}, out2)
    h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
    assert h(out_p) == h(out2), "两连跑不幂等"
    assert not [f for f in os.listdir(d) if f.endswith(".tmp")]
    # 浮点 ε: 0.7s*30=21.000000000000004, 须读作 21 而非 22 → pad==1
    _wb(pace_p, {"A": 0.7}, os.path.join(d, "wb_eps.json"))
    assert json.load(open(os.path.join(d, "wb_eps.json")))["stages"][0]["pad_frames"] == 1
    # 未知 stage id → 拒绝(唯一通道不许哑改; rc=3=数据错, 与 argparse 的 2 区分)
    _wb(pace_p, {"ZZZ": 1.0}, os.path.join(d, "wb_bad.json"), expect_rc=3)


def test_writeback_negative_audio_shorter():
    d = "/tmp/p3test"
    pace_p = _mini_pace(os.path.join(d, "wb_neg_in.json"))
    out_p = os.path.join(d, "wb_neg_out.json")
    # C: 15 帧; 0.4999s→ceil(14.997)=15==frames → pad 0; 0.1s→3<15 → pad 0
    _wb(pace_p, {"C": 0.4999}, out_p)
    p1 = json.load(open(out_p))
    c = [s for s in p1["stages"] if s["id"] == "C"][0]
    assert c["pad_frames"] == 0, c
    assert c["end"] - c["start"] == c["frames"] == 15
    assert p1["total_frames"] == 60, "全表短音频时 total 不得变"
    assert all(s["pad_frames"] >= 0 for s in p1["stages"])


def test_remotion_pace_sourced():
    """src/e30film 的 TS 只 import 真账 pace.json; 禁自算帧号; duration 对拍."""
    import glob
    assert os.path.isdir(_E30_SRC), "缺 src/e30film Remotion 工程"
    ts_files = sorted(glob.glob(os.path.join(_E30_SRC, "src", "**", "*.ts*"),
                                recursive=True))
    assert ts_files, "src/e30film/src 下无 TS 文件"
    # 禁自算标记: fps 乘除换算 / 硬编码总帧 / 字面量 duration / 秒→帧 Math.round
    forbidden = [re.compile(p) for p in (
        r"(fps|FPS)\s*[*]", r"[*]\s*(fps|FPS)",
        r"\b7200\b", r"Math\.round\(",
        r"durationInFrames\s*[:=]\s*\{?\s*[0-9]",
    )]
    for f in ts_files:
        src = open(f).read()
        for rx in forbidden:
            m = rx.search(src)
            assert not m, "TS 自算帧号标记 %r @ %s" % (rx.pattern, f)
    # pace.ts 必须 import 仓内真账 pace.json(相对路径解析后同指一文件)
    pace_ts = os.path.join(_E30_SRC, "src", "pace.ts")
    m = re.search(r"import\s+\w+\s+from\s+[\"'](.+?\.json)[\"']", open(pace_ts).read())
    assert m, "pace.ts 未 import pace.json"
    resolved = os.path.realpath(os.path.normpath(
        os.path.join(os.path.dirname(pace_ts), m.group(1))))
    real = os.path.realpath(os.path.join(REPO3D, "3d", "out", "film", "pace.json"))
    assert resolved == real, (resolved, real)
    # bun 执行 TS 读数 → 与 pace.json 对拍(不重新实现, 执行真模块)
    bun = shutil.which("bun")
    assert bun, "测试环境缺 bun(Remotion 接线对拍依赖)"
    script = os.path.join(_E30_SRC, "scripts", "print_pace.ts")
    r = subprocess.run([bun, script], capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, (r.returncode, r.stdout, r.stderr)
    got = json.loads(r.stdout.strip().splitlines()[-1])
    real_pace = json.load(open(real))
    # 序幕 5s 后重钉: 7350 帧, 409 stage(S000 题卡; seg-01 窗自动张开)
    assert got["duration"] == real_pace["total_frames"] == 7350
    assert got["fps"] == real_pace["fps"] == 30
    assert got["stages"] == len(real_pace["stages"]) == 409
    assert got["first"]["from"] == 0 and got["last"]["to"] == got["duration"]
    clips = got["clips"]
    assert len(clips) == 409
    for a, b in zip(clips, clips[1:]):
        assert a["to"] == b["from"], "Remotion 段边界与 pace 不同源"
