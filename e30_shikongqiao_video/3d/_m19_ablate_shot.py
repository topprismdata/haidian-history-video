# -*- coding: utf-8 -*-
"""M19 平色消融单帧: blend + 全平色 + 固定冬照机位 + 1200 samples。
用法: blender -b --python _m19_ablate_shot.py -- blendpath outpng"""
import bpy
import sys
import os
from mathutils import Vector

a = sys.argv[sys.argv.index("--") + 1:]
blend, out = a[0], a[1]
bpy.ops.wm.open_mainfile(filepath=blend)

m = bpy.data.materials.new("flat")
m.use_nodes = True
b = m.node_tree.nodes.get("Principled BSDF")
b.inputs["Base Color"].default_value = (0.5, 0.5, 0.5, 1.0)
b.inputs["Roughness"].default_value = 0.9
for obj in bpy.data.objects:
    if obj.type == 'MESH' and "water" not in obj.name and "shore" not in obj.name \
            and "fog" not in obj.name:
        obj.data.materials.clear()
        obj.data.materials.append(m)

sc = bpy.context.scene
cp = bpy.context.preferences.addons['cycles'].preferences
try:
    cp.compute_device_type = 'METAL'
except Exception:
    pass
for d in cp.devices:
    d.use = (d.type == 'METAL')
sc.cycles.device = 'GPU'
sc.cycles.samples = 1200
sc.cycles.seed = 20261004
sc.cycles.use_animated_seed = False
sc.cycles.use_denoising = True
sc.render.resolution_x = 1600
sc.render.resolution_y = 1067
cd = bpy.data.cameras.new("AB")
cd.lens = 38.0
cd.sensor_width = 36.0
cd.clip_end = 20000.0
cam = bpy.data.objects.new("AB", cd)
sc.collection.objects.link(cam)
cam.location = (92.0, -34.0, 2.0)
d = Vector((-20.0, 0.0, 3.2)) - Vector(cam.location)
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
sc.camera = cam
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("ABLATE_DONE", out)
