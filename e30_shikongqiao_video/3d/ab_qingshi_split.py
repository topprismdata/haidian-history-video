# -*- coding: utf-8 -*-
"""C2 材质分工 A/B 渲染: 桥体现状暖白(stone_body) vs 青石(qingshi_material)。

来源依据(逐字核实): 中新网 2025-12-09 10:53(来源:北京青年报)
《十七孔桥的金光穿洞 你知道它的来龙去脉吗？》
https://www.chinanews.com.cn/cul/2025/12-09/10529704.shtml
  「……以青石筑成桥体, 以汉白玉为栏杆, 因有17个拱券, 故名十七孔桥……」
分工: 桥体(含券圈/伏券/墩肩/燕翅桥台)=青石; 栏杆/望柱/狮/靠山兽=汉白玉(不动)。

关键: 复用生产 blend(e30_bridge.blend) 与 shot_auto2 完全相同的相机/采样设置,
只替换桥体侧材质 —— 相机差异会伪装成材质差异。
不改 build_scene2.py / shot_auto2.py / facts.py / ortho.py(冻结), 本脚本自包含。

用法: blender -b --factory-startup --python ab_qingshi_split.py -- hero [res] [samples]
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
res = int(a[1]) if len(a) > 1 and a[1].isdigit() else 800
smp = int(a[2]) if len(a) > 2 and a[2].isdigit() else 32

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
# 确定性: 与 shot_auto2 同 seed 且关 animated_seed
sc.cycles.seed = 20261004
sc.cycles.use_animated_seed = False
sc.cycles.use_denoising = True
sc.render.resolution_x = res
sc.render.resolution_y = int(res * 9 / 16)
sc.render.image_settings.file_format = 'PNG'
print("AB_SEED %d (animated=%s, device=%s, samples=%d, res=%dx%d)"
      % (sc.cycles.seed, sc.cycles.use_animated_seed, sc.cycles.device, smp,
         sc.render.resolution_x, sc.render.resolution_y))

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
    "top":   (Vector((0, 0, 1)), 1.20),
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

OUTDIR = os.path.join(HERE, "ab_qingshi")
if not os.path.isdir(OUTDIR):
    os.makedirs(OUTDIR)

# ── A: 现状(暖白桥体 stone_body/stone_ring, 栏杆 marble 不动) ──
outA = os.path.join(OUTDIR, "ab_%s_A_warm.png" % view)
sc.render.filepath = outA
bpy.ops.render.render(write_still=True)
print("A ->", outA)

# ── B: 桥体=青石(券圈略亮冷灰保可读), 栏杆侧一律不动 ──
import materials as MAT
qs_body = MAT.qingshi_material("qs_body_ab")                          # 桥体/桥台
qs_ring = MAT.qingshi_material("qs_ring_ab", (0.350, 0.382, 0.418))   # 券圈/伏券/墩肩
BODY_SET = ("bridge_body", "abutment_ground")
RING_SET = ("voussoir", "impost", "pier_plinth")
swap = []
for names, mat in ((BODY_SET, qs_body), (RING_SET, qs_ring)):
    for name in names:
        ob = bpy.data.objects.get(name)
        if not ob:
            continue
        for slot in ob.material_slots:
            slot.material = mat
        swap.append(name)
print("B swap:", swap)
outB = os.path.join(OUTDIR, "ab_%s_B_qingshi.png" % view)
sc.render.filepath = outB
bpy.ops.render.render(write_still=True)
print("B ->", outB)
print("DONE")
