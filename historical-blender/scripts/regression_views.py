# -*- coding: utf-8 -*-
"""固定机位回归渲染 + 哈希/统计 diff 报告。

设计要点(SKILL.md §5):
- 回归相机必须钉在**世界坐标字面量**。auto-frame(bbox 推导)的相机会随几何变化而移动,
  回归对照将失去基准。故首次运行把机位固化为字面量写进 views JSON, 此后一律用字面量。
- 渲染确定性: seed 固定 / use_animated_seed=False / denoise 固定(见 source_of_truth.md §3)。
- 输出每视图: PNG + sha256 + 均值亮度 + 边缘能量(观感层的量化佐证, 非裁决)。
- --diff <baseline.json>: 逐视图报哈希变化与统计漂移; **未归因的变化 = 回归**(SKILL.md §5)。

用法:
  blender -b --factory-startup --python regression_views.py -- \
      <blend> <out_dir> [--views hero,side] [--res 800] [--samples 24] \
      [--views-json path.json] [--diff baseline.json]

views JSON 不存在时: 从 blend 的桥体 bbox 用 shot_auto2 同款数学推导机位并**落盘固化**;
存在时: 直接用字面量(几何已变也不重推)。
"""
import hashlib
import json
import struct
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))

# 与 shot_auto2.py 同源的方向表(单位向量, 拉远倍数)。仅用于**首次固化**机位。
VIEWS = {
    "hero":  (Vector((0, 0, 0)), 1.02),   # 占位, 实际由 Nv/Bv 组合, 见 _derive
    "side":  (None, 1.10),
    "front": (None, 1.00),
    "low":   (None, 1.25),
    "arch":  (None, 0.55),
    "top":   (Vector((0, 0, 1)), 1.20),
}
BRIDGE_NAMES = ("bridge_body", "voussoir", "deck_rail", "beasts")
SEED = 20261004


def _parse_args():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    opts = {"views": None, "res": 800, "samples": 24,
            "views_json": None, "diff": None}
    pos = []
    i = 0
    while i < len(a):
        if a[i] == "--views":
            opts["views"] = a[i + 1].split(","); i += 2
        elif a[i] == "--res":
            opts["res"] = int(a[i + 1]); i += 2
        elif a[i] == "--samples":
            opts["samples"] = int(a[i + 1]); i += 2
        elif a[i] == "--views-json":
            opts["views_json"] = a[i + 1]; i += 2
        elif a[i] == "--diff":
            opts["diff"] = a[i + 1]; i += 2
        else:
            pos.append(a[i]); i += 1
    if len(pos) < 2:
        raise SystemExit("用法: ... -- <blend> <out_dir> [options]")
    opts["blend"], opts["out"] = pos[0], pos[1]
    return opts


def _derive_cameras():
    """首次运行: 从桥体 bbox 推导机位(shot_auto2 同款数学), 返回字面量表。"""
    objs = [bpy.data.objects[n] for n in BRIDGE_NAMES if bpy.data.objects.get(n)]
    if not objs:
        raise SystemExit("blend 中找不到桥体对象: %s" % (BRIDGE_NAMES,))
    mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
    for o in objs:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            for k in range(3):
                mn[k] = min(mn[k], w[k]); mx[k] = max(mx[k], w[k])
    ctr = (mn + mx) / 2.0
    size = mx - mn
    ax = math.atan2(objs[0].matrix_world[1][0], objs[0].matrix_world[0][0])
    bv = Vector((math.cos(ax), math.sin(ax), 0.0))
    nv = Vector((-bv.y, bv.x, 0.0))
    dirs = {
        "hero":  ((nv * 0.90 + bv * 0.42 + Vector((0, 0, 0.06))).normalized(), 1.02),
        "side":  (nv.normalized(), 1.10),
        "front": (bv.normalized(), 1.00),
        "low":   ((nv * 0.86 + bv * 0.50 + Vector((0, 0, 0.10))).normalized(), 1.25),
        "arch":  ((nv * 0.50 + bv * 0.86).normalized(), 0.55),
        "top":   (Vector((0, 0, 1)), 1.20),
    }
    out = {}
    for name, (dv, k) in dirs.items():
        pos = ctr - dv * (size.length / 2.0 * k)
        if name in ("hero", "low", "arch"):
            pos.z = 3.0 + size.z * 0.06
        else:
            pos.z = max(pos.z, mx.z + size.z * 0.15)
        rot = (ctr - pos).to_track_quat('-Z', 'Y').to_euler()
        out[name] = {"loc": [round(v, 4) for v in pos],
                     "rot": [round(v, 6) for v in rot],
                     "lens": 50}
    return out


def _stats(path):
    """均值亮度 + 边缘能量。用 Blender 原生像素读取, 不依赖 PIL
    (Blender 自带 Python 无 PIL; numpy 随 Blender 附带)。"""
    import numpy as np
    img = bpy.data.images.load(path)
    w, h = img.size
    buf = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(buf)
    bpy.data.images.remove(img)
    rgb = buf.reshape(h, w, 4)[:, :, :3].astype(np.float64)
    lum = rgb @ np.array([0.2126, 0.7152, 0.0722])
    gy = np.abs(np.diff(lum, axis=0)).mean()
    gx = np.abs(np.diff(lum, axis=1)).mean()
    return {"mean_lum": round(float(lum.mean()), 3),
            "edge_energy": round(float(gx + gy), 4)}


def _pixel_sha(path):
    """像素数据哈希 = 所有 IDAT 块拼接后 sha256。

    2026-10-05 实测坑: 同场景同 seed 两次渲染**像素 100% 相同**, 但整文件 sha256 不同——
    差异全在 PNG tEXt 元数据块(渲染耗时/统计), 每次运行都变。
    故回归信号必须哈希像素数据(IDAT 流), 不得哈希整文件字节。"""
    data = open(path, "rb").read()
    i = 8
    h = hashlib.sha256()
    while i < len(data):
        ln = struct.unpack(">I", data[i:i + 4])[0]
        typ = data[i + 4:i + 8]
        if typ == b"IDAT":
            h.update(data[i + 8:i + 8 + ln])
        i += 12 + ln
    return h.hexdigest()

def main():
    o = _parse_args()
    os.makedirs(o["out"], exist_ok=True)
    vj = o["views_json"] or os.path.join(o["out"], "regression_views.json")
    bpy.ops.wm.open_mainfile(filepath=o["blend"])
    if os.path.exists(vj):
        cams = json.load(open(vj, encoding="utf-8"))
        pinned = True
    else:
        cams = _derive_cameras()
        json.dump(cams, open(vj, "w", encoding="utf-8"), indent=1)
        pinned = False
    names = o["views"] or list(cams.keys())

    sc = bpy.context.scene
    cp = bpy.context.preferences.addons['cycles'].preferences
    try:
        cp.compute_device_type = 'METAL'
    except Exception:
        pass
    for d in cp.devices:
        d.use = (d.type == 'METAL')
    sc.cycles.device = 'GPU'
    sc.cycles.samples = o["samples"]
    sc.cycles.seed = SEED
    sc.cycles.use_animated_seed = False
    sc.cycles.use_denoising = True
    sc.render.resolution_x = o["res"]
    sc.render.resolution_y = int(o["res"] * 9 / 16)
    sc.render.image_settings.file_format = 'PNG'

    manifest = {"seed": SEED, "res": o["res"], "samples": o["samples"],
                "views_json": vj, "pinned_at_first_run": pinned, "views": {}}
    for name in names:
        c = cams[name]
        cd = bpy.data.cameras.new("RC"); cd.lens = c["lens"]; cd.clip_end = 20000.0
        cam = bpy.data.objects.new("RC", cd)
        bpy.context.collection.objects.link(cam)
        sc.camera = cam
        cam.location = c["loc"]
        cam.rotation_euler = c["rot"]
        png = os.path.join(o["out"], "reg_%s.png" % name)
        sc.render.filepath = png
        bpy.ops.render.render(write_still=True)
        sha = _pixel_sha(png)   # 像素数据哈希, 非整文件(见 _pixel_sha docstring)
        st = _stats(png)
        manifest["views"][name] = {"png": png, "sha256": sha, **st}
        print("REG %s sha=%s lum=%.2f edge=%.4f" % (name, sha[:12], st["mean_lum"], st["edge_energy"]))
        bpy.data.objects.remove(cam, do_unlink=True)

    mj = os.path.join(o["out"], "regression.json")
    json.dump(manifest, open(mj, "w", encoding="utf-8"), indent=1)
    print("MANIFEST", mj)

    if o["diff"]:
        base = json.load(open(o["diff"], encoding="utf-8"))
        print("\n=== DIFF vs %s ===" % o["diff"])
        for name in names:
            b = base["views"].get(name)
            m = manifest["views"][name]
            if not b:
                print("  %-6s 基线缺此视图" % name)
                continue
            same = "同" if b["sha256"] == m["sha256"] else "变"
            dl = m["mean_lum"] - b["mean_lum"]
            de = m["edge_energy"] - b["edge_energy"]
            print("  %-6s %s  Δlum %+7.3f  Δedge %+8.4f" % (name, same, dl, de))
        print("=== 未归因的变化 = 回归; 预期变化须在 commit/报告写明归因 ===")


main()
