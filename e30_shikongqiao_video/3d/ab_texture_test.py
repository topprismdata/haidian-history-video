# -*- coding: utf-8 -*-
"""A/B 渲染: 纯色 marble_material  vs  tex_mat 实测贴图版。

关键: 复用生产 blend(e30_bridge.blend) 与 shot_auto2 的完全相同相机/采样设置,
只替换材质。否则两张图不可比 —— 相机差异会伪装成材质差异。

不改 build_scene2.py / shot_auto2.py(被 freeze_manifest 锁死), 本脚本自包含。

用法: blender -b --factory-startup --python ab_texture_test.py -- hero [res] [samples]
"""
import os
import sys

import bpy
from mathutils import Vector
import math

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
view = a[0] if a else "hero"
res = int(a[1]) if len(a) > 1 and a[1].isdigit() else 1600
smp = int(a[2]) if len(a) > 2 and a[2].isdigit() else 64

bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "e30_bridge.blend"))
sc = bpy.context.scene
cp = bpy.context.preferences.addons['cycles'].preferences
try:
    cp.compute_device_type = 'METAL'
except Exception:
    pass
for d in cp.devices:
    d.use = (d.type == 'METAL')
sc.cycles.device = 'GPU'
sc.cycles.samples = smp
# 确定性: 必须与 shot_auto2 同 seed 且关 animated_seed(否则哈希不可复现)
sc.cycles.seed = 20261004
sc.cycles.use_animated_seed = False
sc.cycles.use_denoising = True
sc.render.resolution_x = res
sc.render.resolution_y = int(res * 9 / 16)
sc.render.image_settings.file_format = 'PNG'

BRIDGE_NAMES = ("bridge_body", "voussoir", "deck_rail", "beasts")
BRIDGE = [bpy.data.objects[n] for n in BRIDGE_NAMES if bpy.data.objects.get(n)]
mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
for o in BRIDGE:
    for c in o.bound_box:
        w = o.matrix_world @ Vector(c)
        for k in range(3):
            mn[k] = min(mn[k], w[k]); mx[k] = max(mx[k], w[k])
ctr = (mn + mx) / 2.0; size = mx - mn
_b = BRIDGE[0]
AX = math.atan2(_b.matrix_world[1][0], _b.matrix_world[0][0])
Bv = Vector((math.cos(AX), math.sin(AX), 0.0))
Nv = Vector((-Bv.y, Bv.x, 0.0))

cd = bpy.data.cameras.new("C"); cd.lens = 50; cd.clip_end = 20000.0
cam = bpy.data.objects.new("C", cd); bpy.context.collection.objects.link(cam)
sc.camera = cam
bpy.ops.object.select_all(action='DESELECT')
for o in BRIDGE:
    o.select_set(True)
bpy.context.view_layer.objects.active = BRIDGE[0]

VIEWS = {
    "hero":  (Nv * 0.90 + Bv * 0.42 + Vector((0, 0, 0.06)), 1.02),
    "side":  (Nv, 1.10),
    "front": (Bv, 1.00),
    "low":   (Nv * 0.86 + Bv * 0.50 + Vector((0, 0, 0.10)), 1.25),
    "arch":  (Nv * 0.50 + Bv * 0.86, 0.55),
}
dirv, dist_k = VIEWS[view]
dirv = dirv.normalized()
radius = size.length / 2.0
pos = ctr - dirv * (radius * dist_k)
if view in ("hero", "low", "arch"):
    pos.z = 3.0 + size.z * 0.06
else:
    pos.z = max(pos.z, mx.z + size.z * 0.15)
cam.location = pos
cam.rotation_euler = (ctr - pos).to_track_quat('-Z', 'Y').to_euler()
for _ in range(14):
    bpy.context.view_layer.update()
    bpy.ops.view3d.camera_to_view_selected()
    bpy.ops.object.select_all(action='DESELECT')
    for o in BRIDGE:
        o.select_set(True)
    bpy.context.view_layer.objects.active = BRIDGE[0]

# ── A: 现状 ──
outA = os.path.join(HERE, "ab_%s_A_plain.png" % view)
sc.render.filepath = outA
bpy.ops.render.render(write_still=True)
print("A ->", outA)

# ── B: 贴图版 ──
import tex_mat as TM
tex = TM.make_tex_stone("marble_tex", tex_dir=os.path.join(HERE, "textures", "ambientcg"))
# 只换"打磨过的近白构件"; bridge_body/voussoir 是粗砌石, 保持不变
swap = []
for name in ("deck_rail", "lions", "beasts", "pier_plinth", "impost"):
    ob = bpy.data.objects.get(name)
    if not ob:
        continue
    ob.data.materials.clear()
    ob.data.materials.append(tex)
    swap.append(name)
print("B swap:", swap)
outB = os.path.join(HERE, "ab_%s_B_tex.png" % view)
sc.render.filepath = outB
bpy.ops.render.render(write_still=True)
print("B ->", outB)
print("DONE")
