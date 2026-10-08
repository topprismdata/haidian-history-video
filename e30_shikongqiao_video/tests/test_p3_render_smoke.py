#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# tests/test_p3_render_smoke.py
"""P3-T5 渲染驱动冒烟 + 两负控(blender 门控; CI blender-free 全 skip)。

测什么(计划 Task 5 Step1 + context 红线):
  1. 冒烟: stage 边界 3 帧(首/首个券架在场帧/末)真跑 film_render --
     PNG 存在 + 选择记录==状态机 + work.blend 落盘 + 原料 blend sha 不变。
  2. 楔石位移负控: λ=0 帧与 λ=1 帧的楔石物体 z 差 == WEDGE_DROP_M
     (断言读自驱动回读的场景物体位置 probe.jsonl, 不只看选择记录)。
  3. 券架显隐负控: CEN-ARCHxx 在 centering_up 帧可见、BUILD 首帧与
     CLEAR 末帧全隐藏(同样读场景回读, 非记录)。

原料 blend = 3d/out/film/layout_film.blend(P3-T5b 点云扩容 5935 全量,
film_layout_build.py 产物, 由 session 夹具保证存在且新鲜)。四层一线
(主控 T5b 裁决定稿): 末帧场景可见实例==选择记录==状态机==账面日程 3931。
测试对全部只读输入(P1 layout/families/账/序/bridge blend)断言 sha 不变
(只读打开纪律)。

驱动薄纪律: 在场判定单源 import film_state, 本文件只做对拍裁判。
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_3D = os.path.join(_ROOT, "3d")
for _p in (_3D, os.path.join(_3D, "film")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import film_geometry as FG          # noqa: E402  渲染侧参数单源(相机/下沉量)
import film_state as FS             # noqa: E402  在场判定单源

HAS_BLENDER = shutil.which("blender") is not None
BLENDER = shutil.which("blender") or "blender"
RENDER_PY = os.path.join(_ROOT, "3d", "film", "film_render.py")
PACE = FS.load_pace(os.path.join(_3D, "out", "film", "pace.json"))
SEQ_PATH = os.path.join(_3D, "out", "sequence.json")
with open(SEQ_PATH, encoding="utf-8") as _fh:
    SEQ = json.load(_fh)
FILM_BLEND = os.path.join(_3D, "out", "film", "layout_film.blend")
BRIDGE_BLEND = os.path.join(_ROOT, "3d", "e30_bridge.blend")
WORK_BLEND = os.path.join(_3D, "out", "film", "work.blend")
TOTAL = PACE["total_frames"]


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _mid_frame():
    """首个券架在场帧(stage 起点; 0/末帧之外的第三冒烟帧)。"""
    for s in sorted(PACE["stages"], key=lambda s: s["start"]):
        if FS.state_at_frame(PACE, SEQ, s["start"])["centering_up"]:
            return s["start"]
    raise AssertionError("pace 无券架在场帧, 负控 3 无法选帧")


MID = _mid_frame() if HAS_BLENDER else 71
FRAMES = (0, MID, TOTAL - 1)


def _run_blender(frame, out_dir, timeout=900):
    """单帧驱动调用: blender -b -P film_render.py -- --frames f-f --out d."""
    cmd = [BLENDER, "-b", "-P", RENDER_PY, "--",
           "--frames", "%d-%d" % (frame, frame), "--out", out_dir]
    return subprocess.run(cmd, cwd=_ROOT, capture_output=True, text=True,
                          timeout=timeout)


def _read_jsonl(path):
    rows = {}
    if not os.path.isfile(path):
        return rows
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                r = json.loads(line)
                rows[r["frame"]] = r
    return rows


@pytest.fixture(scope="module")
def smoke(tmp_path_factory, film_layout_blend):
    """3 帧真跑一次, 冒烟+两负控共享产物(避免重复 blender 启动)。"""
    if not HAS_BLENDER:
        pytest.skip("blender-free CI")
    assert film_layout_blend == FILM_BLEND
    out_dir = str(tmp_path_factory.mktemp("film_frames"))
    sha_film = _sha256(FILM_BLEND)
    sha_inputs = {p: _sha256(p) for p in (
        os.path.join(_3D, "out", "e30_layout.blend"),
        os.path.join(_3D, "out", "families.blend"),
        os.path.join(_3D, "out", "ledger_sequenced.json"),
        SEQ_PATH, BRIDGE_BLEND)}
    runs = {f: _run_blender(f, out_dir) for f in FRAMES}
    return {"out_dir": out_dir, "runs": runs,
            "sha_film_before": sha_film, "sha_inputs_before": sha_inputs}


def _fail_tail(proc):
    return "\n".join((proc.stderr or "").splitlines()[-25:])


@pytest.mark.skipif(not HAS_BLENDER, reason="blender-free CI")
def test_render_3frames_smoke(smoke):
    # 1) 三次调用 rc==0
    for f in FRAMES:
        assert smoke["runs"][f].returncode == 0, \
            "frame %d 渲染失败:\n%s" % (f, _fail_tail(smoke["runs"][f]))
    # 2) PNG 存在(f%06d.png)
    for f in FRAMES:
        assert os.path.isfile(os.path.join(smoke["out_dir"],
                                           "f%06d.png" % f)), "缺 f%06d.png" % f
    # 3) 选择记录 == 状态机(计划原文断言, 逐帧)
    recs = _read_jsonl(os.path.join(smoke["out_dir"], "selection.jsonl"))
    for f in FRAMES:
        assert f in recs, "selection.jsonl 缺 frame %d" % f
        st = FS.state_at_frame(PACE, SEQ, f)
        rec = recs[f]
        assert rec["driver"] == "film_render"
        assert set(rec["selected"]) == set(st["visible"]), \
            "frame %d 选择记录 != 状态机" % f
        assert rec["phase"] == st["phase"]
        assert rec["wedge_lambda"] == st["wedge_lambda"]
    # 4) 四层一线(T5b 定稿): 末帧场景实例==记录==状态机==账面日程 3931
    assert len(recs[TOTAL - 1]["selected"]) == 3931
    probe = _read_jsonl(os.path.join(smoke["out_dir"], "probe.jsonl"))
    probeL = probe[TOTAL - 1]
    assert probeL["scene_instances"] == 3931
    assert probeL["vis_idx"] == 3931
    # 5) work.blend 落盘, film blend 与全部只读输入 sha 不变(只读纪律)
    assert os.path.isfile(WORK_BLEND)
    assert _sha256(FILM_BLEND) == smoke["sha_film_before"]
    after = {p: _sha256(p) for p in smoke["sha_inputs_before"]}
    assert after == smoke["sha_inputs_before"]
    # 6) 相机接线: BUILD 帧=侧视正射, DONE 末帧=推到 loc_end 透射
    cam0 = probe[0]["camera"]
    assert cam0["type"] == "ORTHO"
    assert cam0["ortho_scale"] == pytest.approx(
        FG.CAMERA_TRACKS["BUILD"]["ortho_scale"])
    camL = probe[TOTAL - 1]["camera"]
    assert camL["type"] == "PERSP"
    assert camL["loc"] == pytest.approx(
        list(FG.CAMERA_TRACKS["DONE"]["loc_end"]), abs=1e-6)


@pytest.mark.skipif(not HAS_BLENDER, reason="blender-free CI")
def test_wedge_drop_negative_control(smoke):
    """λ=0 帧 vs λ=1 帧: 楔石物体 z 差 == -WEDGE_DROP_M(读场景物体位置)."""
    probe = _read_jsonl(os.path.join(smoke["out_dir"], "probe.jsonl"))
    z0 = probe[0]["wedge_z"]
    z1 = probe[TOTAL - 1]["wedge_z"]
    assert set(z0) == set(z1) and len(z0) == 17, "楔石物体应 17 孔全有"
    for hole in z0:
        # frame0 λ=0, 末帧 λ=1(序幕 5s 后末帧=7349, 以 pace 重生成为准)
        # → 位移 = -1.0 * WEDGE_DROP_M
        assert z1[hole] - z0[hole] == pytest.approx(-FG.WEDGE_DROP_M,
                                                    abs=1e-6), \
            "楔石 %s z 差 != -WEDGE_DROP_M" % hole
        # λ=0 帧停在基准位(位移零点即账面锚位)
        assert z0[hole] == pytest.approx(probe[0]["wedge_base_z"][hole],
                                         abs=1e-9)


@pytest.mark.skipif(not HAS_BLENDER, reason="blender-free CI")
def test_centering_visibility_negative_control(smoke):
    """CEN-ARCHxx: centering_up 帧可见, 首帧与 CLEAR 末帧全隐藏."""
    probe = _read_jsonl(os.path.join(smoke["out_dir"], "probe.jsonl"))
    st_mid = FS.state_at_frame(PACE, SEQ, MID)
    assert st_mid["centering_up"], "中间帧应含券架在场(选帧失效)"
    vis_mid = probe[MID]["centering_visible"]
    assert set(vis_mid) == {("CEN-ARCH%02d" % i) for i in range(1, 18)}
    # 在场判定对拍: 回读可见集合 == 状态机 centering_up(逐孔布尔一致)
    for cid, visible in vis_mid.items():
        assert visible == (cid in st_mid["centering_up"]), \
            "券架 %s 回读可见性 != 状态机" % cid
    for f in (0, TOTAL - 1):
        assert not any(probe[f]["centering_visible"].values()), \
            "frame %d 券架应全隐藏" % f
