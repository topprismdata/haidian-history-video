# -*- coding: utf-8 -*-
"""M23 逐石层 标签图(Blender 内 raycast, 无合成器依赖)。

对位姿相机全帧(或 ROI)逐像素 scene.ray_cast, 命中 masonry 面带且法线朝相机的像素,
反查 stones_pX.json 得 stone_id -> 输出 label map(npz: label/origin/dir 元数据)。
与 Position AOV 等价(5.2 移除 scene.node_tree 的规避方案), 主控批准路线。
用法:
  blender -b e30_bridge.blend --python compare_pack_raylabel.py -- <pose_json> <stones_json> <tag> [roi_x0 roi_y0 roi_x1 roi_y1](1920x1080标定画幅) [step]
输出: out/compare_pack/perstone/<tag>_labels.npz (label int32 HxW, ids 列表, roi, step, K/Rw 缓存)
"""
import json
import math
import os
import sys

import bpy
import mathutils
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sc = bpy.context.scene


def rodrigues(rv):
    th = float(np.linalg.norm(rv))
    k = rv / th
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + math.sin(th) * K + (1 - math.cos(th)) * (K @ K)


def _hw_at(ctrl, x, z):
    c = ctrl["constants"]
    half = c["BRIDGE_LEN"] / 2.0
    k = (c["DECK_Z_TOP"] - c["DECK_Z_END"]) / (half * half)
    deck = c["DECK_Z_TOP"] - k * min(abs(x), half) ** 2
    f = max(0.0, min(1.0, (z - c["BODY_BOTTOM"]) / (deck - c["BODY_BOTTOM"])))
    return (c["DECK_DOWN_W"] + (c["DECK_UP_W"] - c["DECK_DOWN_W"]) * f) / 2.0


def apply_m23_fix_geometry():
    import bmesh
    for nm in ("voussoir", "coursing"):
        o = bpy.data.objects.get(nm)
        if o:
            bm = bmesh.new()
            bm.from_mesh(o.data)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            bm.to_mesh(o.data)
            bm.free()


argv = sys.argv[sys.argv.index("--") + 1:]
pose_path, stones_path, tag = argv[0], argv[1], argv[2]
W, H = 1920, 1080
roi = (0, 0, W, H)
if len(argv) > 3:
    roi = tuple(int(v) for v in argv[3:7])
step = int(argv[7]) if len(argv) > 7 else 2
apply_m23_fix_geometry()

pose = json.load(open(pose_path))
ctrl = json.load(open(os.path.join(HERE, "m20_ctrl", "model_ctrl.json")))
stones = json.load(open(stones_path))
side = int(pose.get("side", -1))

R = rodrigues(np.array(pose["rvec"], np.float64))
t = np.array(pose["tvec"], np.float64)
C = -R.T @ t
root = bpy.data.objects["bridge_body"]
Mw = root.matrix_world.to_3x3()
axes = [Mw @ mathutils.Vector(v) for v in ((1, 0, 0), (0, 1, 0), (0, 0, 1))]
Rw = mathutils.Matrix([[axes[c][r] / axes[c].length for c in range(3)] for r in range(3)])
Rwinv = np.array(Rw.inverted())
Rwinv_t = Rwinv.T.copy()

# 相机参数(标定画幅 K)
f_px = pose["f"]
cx, cy = pose["w"] / 2.0, pose["h"] / 2.0
cam_o = Rw @ mathutils.Vector(tuple(float(v) for v in C))  # 世界系(桥旋转-112°)
Rcw = (Rw @ mathutils.Matrix(R.tolist()).transposed() @ mathutils.Matrix.Diagonal((1, -1, -1, 1)).to_3x3())
fwd = Rcw @ mathutils.Vector((0, 0, -1))
right = Rcw @ mathutils.Vector((1, 0, 0))
up = Rcw @ mathutils.Vector((0, 1, 0))
fw = np.array(fwd)
fw_n = np.array(Rw @ mathutils.Vector((0.0, float(side), 0.0)))  # 被摄面外法线(世界)

# stones -> 查找结构
courses = {}
for ci, c in enumerate(stones["courses"]):
    z0 = c["z0"]
    z1 = stones["courses"][ci + 1]["z0"] if ci + 1 < len(stones["courses"]) else c.get("z1", z0 + 0.45)
    b = c["blocks"]
    for bi in range(len(b) - 1):
        courses.setdefault((round(z0, 3), round(z1, 3)), []).append((b[bi], b[bi + 1], "c%02db%02d" % (ci, bi)))
bands = sorted(courses.keys())
stone_ids = []

dg = bpy.context.evaluated_depsgraph_get()
x0r, y0r, x1r, y1r = roi
nx = (x1r - x0r) // step
ny = (y1r - y0r) // step
label = np.full((ny, nx), -1, np.int32)
ids = []
hit_any = 0
face_any = 0
for j in range(ny):
    v_px = y0r + j * step
    for i2 in range(nx):
        u_px = x0r + i2 * step
        # 像素 -> 世界射线
        u = (u_px - cx) / f_px
        v = (cy - v_px) / f_px
        d = (fw + right * u + up * v)
        dn = mathutils.Vector((float(d[0]), float(d[1]), float(d[2])))
        dn.normalize()
        hit, loc, nrm, _idx, ob, _mw = sc.ray_cast(dg, cam_o, dn)
        if not hit or ob.name not in ("bridge_body", "voussoir", "coursing"):
            continue
        hit_any += 1
        pm = Rwinv @ np.array([loc.x, loc.y, loc.z])
        x, y, z = pm
        hw = _hw_at(ctrl, x, z)
        if abs(y - side * hw) > 0.22:
            continue
        wn = np.array(nrm)
        if float(wn @ fw_n) < 0.5:  # 被摄面带(法线朝相机侧), 背面石不混入
            continue
        band = None
        for (zb0, zb1), lst in courses.items():
            if zb0 <= z < zb1:
                band = lst
        if band is None:
            continue
        sid = None
        for (bx0, bx1, s) in band:
            if bx0 <= x < bx1:
                sid = s
                break
        if sid is None:
            continue
        if sid not in ids:
            ids.append(sid)
        label[j, i2] = ids.index(sid)
        face_any += 1

out_dir = os.path.join(HERE, "out", "compare_pack", "perstone")
os.makedirs(out_dir, exist_ok=True)
np.savez_compressed(os.path.join(out_dir, "%s_labels.npz" % tag),
                    label=label, ids=np.array(ids), roi=np.array(roi), step=step,
                    cal_wh=np.array([pose["w"], pose["h"]]),
                    rw=[[float(Rw[r][c]) for c in range(3)] for r in range(3)],
                    cam_pos=[float(v) for v in C], side=side)
print("RAYLABEL_DONE", tag, "hits", hit_any, "labeled", face_any, "stones", len(ids))
