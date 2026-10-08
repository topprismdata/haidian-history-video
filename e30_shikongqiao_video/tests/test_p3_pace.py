"""P3-T1 pace.json 生成器测试.

计划 Task 1 Step 1 逐字 + Step 4 附加测(scale_exact 三档 / CLOSE_RING 加成).
只读 3d/out/sequence.json, 产物写 /tmp, 不触 blender.
"""
import json
import os
import subprocess
import sys

REPO3D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SEQ = os.path.join(REPO3D, "3d", "out", "sequence.json")


def _build(out_name, target_sec):
    """跑 CLI 生成 pace 并返回 dict(产物落 /tmp/p3test)."""
    os.makedirs("/tmp/p3test", exist_ok=True)
    out = os.path.join("/tmp/p3test", out_name)
    subprocess.run([sys.executable, "3d/film/pace_build.py",
                    "--sequence", "3d/out/sequence.json",
                    "--target-sec", str(target_sec), "--out", out],
                   check=True, cwd=REPO3D)
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
