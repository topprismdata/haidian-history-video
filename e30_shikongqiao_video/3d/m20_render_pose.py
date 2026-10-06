# -*- coding: utf-8 -*-
"""M20 同机位渲染: 用解算位姿(rvec/tvec/f)在 Blender 里架相机渲染正立面。
用法: blender -b e30_bridge.blend --python m20_render_pose.py -- <pose.json> <out.png> [samples]
"""
import json
import math
import sys

import bpy
import mathutils
import numpy as np


def cv2_Rodrigues(rv):
    th = np.linalg.norm(rv)
    if th < 1e-12:
        return np.eye(3), np.zeros(3)
    k = rv / th
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    R = np.eye(3) + math.sin(th) * K + (1 - math.cos(th)) * (K @ K)
    return R, k


a = sys.argv[sys.argv.index("--") + 1:]
pose_path, out = a[0], a[1]
samples = int(a[2]) if len(a) > 2 else 48
pose = json.load(open(pose_path))
w, h = pose["w"], pose["h"]
if w > 2000:  # 大图限宽, 保持纵横比与视场
    sc_f = 2000.0 / w
    w2, h2 = int(w * sc_f), int(h * sc_f)
else:
    w2, h2 = w, h

rv = np.array(pose["rvec"], np.float64)
tv = np.array(pose["tvec"], np.float64)
R, _ = cv2_Rodrigues(rv)
C = (-R.T @ tv)

sc = bpy.context.scene
cd = bpy.data.cameras.new("M20pose")
cd.lens = pose["f"] * 36.0 / w          # f_px -> mm (sensor 36mm 水平)
cd.sensor_width = 36.0
cd.sensor_fit = "HORIZONTAL"
cam = bpy.data.objects.new("M20pose", cd)
sc.collection.objects.link(cam)
import math as _m
_dist = _m.sqrt(sum(float(C[i]) ** 2 for i in range(3)))
cd.clip_start = max(0.01, _dist * 0.01)
cd.clip_end = max(200.0, _dist * 3.0)
cam.location = mathutils.Vector((float(C[0]), float(C[1]), float(C[2])))
Rbl = mathutils.Matrix(R.tolist()) @ mathutils.Matrix.Diagonal((1, -1, -1, 1)).to_3x3()
cam.rotation_euler = Rbl.to_euler()
sc.camera = cam
sc.render.resolution_x = w2
sc.render.resolution_y = h2
sc.cycles.samples = samples
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("M20_RENDER_OK", out)
