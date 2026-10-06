# -*- coding: utf-8 -*-
"""M19 证据渲染批: 同一进程内多机位(桥台 closeup / 坡道落水 / 岸丘吞墙 / 端孔
impost / 冬照机位终渲)。用法:
  blender -b --python _m19_shots.py -- outdir [dz]
dz: 桥体群整体 z 平移(默认 0, 即重标定后几何; 扫描实验用)。"""
import bpy
import sys
import os
import math
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

a = sys.argv[sys.argv.index("--") + 1:]
outdir = a[0]
dz = float(a[1]) if len(a) > 1 else 0.0

import build_scene2 as BS
BS.build()

SKIP = {"water", "shore_bank", "fog_volume"}
if dz:
    for ob in bpy.data.objects:
        if ob.type == 'MESH' and ob.name not in SKIP:
            ob.location.z += dz

AZ = math.radians(-BS.BRIDGE_AXIS_AZ)


def W(x, y, z):
    """桥轴局部 -> 世界(绕 Z 转 -AZ)。"""
    return (x * math.cos(AZ) - y * math.sin(AZ),
            x * math.sin(AZ) + y * math.cos(AZ), z)


sc = bpy.context.scene
cd = bpy.data.cameras.new("C")
cd.sensor_width = 36.0
cd.clip_end = 20000.0
cam = bpy.data.objects.new("C", cd)
sc.collection.objects.link(cam)
sc.camera = cam
sc.render.resolution_x = 1600
sc.render.resolution_y = 1067
sc.cycles.samples = 48

SHOTS = [
    # name, cam_world, target_world, lens
    ("pier_impost_closeup", tuple(Vector(W(-5.8, 6.0, 1.5)) + Vector((9.0, -3.0, 2.2))),
     W(-5.8, 5.9, 1.2), 55),
    ("endspan_impost", tuple(Vector(W(71.4, 5.2, 1.1)) + Vector((14.0, -6.0, 3.0))),
     W(71.4, 5.0, 0.6), 45),
    ("ramp_shore", (-78.0, -135.0, 9.0), W(75 + 40, 0, 1.1), 35),
    ("bank_abutment", (-24.0, -102.0, 12.0), W(78, -6, 1.6), 35),
    ("exifcam_final", (92.0, -34.0, 2.0), (-20.0, 0.0, 3.2), 38),
]
for (name, pos, tgt, lens) in SHOTS:
    cd.lens = lens
    cam.location = pos
    d = Vector(tgt) - Vector(pos)
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(outdir, "m19_%s.png" % name)
    bpy.ops.render.render(write_still=True)
    print("SHOT %s -> %s" % (name, sc.render.filepath))
print("M19_SHOTS_DONE")
