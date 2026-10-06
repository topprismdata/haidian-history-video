# -*- coding: utf-8 -*-
"""M19 假设A Δz 扫描: 建一次场景, 桥体群平移 Δz∈{0,-1.0,-1.4,-1.8}, 冬照机位渲染。
用法: blender -b --python _m19_dzscan.py -- out_prefix [px py pz tx ty tz lens]
水/岸/雾固定不动(场景基准), 其余全部桥体构件整体平移 —— 即"整桥相对水线降 Δ"的
几何等价(桥动水不动 ≡ 水动桥不动, 相对量完全一致)。"""
import bpy
import sys
import os
import time
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

a = sys.argv[sys.argv.index("--") + 1:]
prefix = a[0]
cam_args = [float(v) for v in a[1:8]] if len(a) >= 8 else [92.0, -34.0, 2.0, -20.0, 0.0, 3.2, 38.0]
DZS = [float(v) for v in a[8:]] if len(a) > 8 else [0.0, -1.0, -1.4, -1.8]
SKIP = {"water", "shore_bank", "fog_volume"}   # 场景基准(水线/岸/雾)不动

t0 = time.time()
import build_scene2 as BS
sc = BS.build()
print("BUILD_SEC %.1f" % (time.time() - t0))

mesh_objs = [ob for ob in bpy.data.objects if ob.type == 'MESH' and ob.name not in SKIP]
base_z = dict((ob.name, float(ob.location.z)) for ob in mesh_objs)
print("SHIFT_SET", len(mesh_objs), sorted(base_z)[:12])

cd = bpy.data.cameras.new("EXIF")
cd.lens = cam_args[6]
cd.sensor_width = 36.0
cd.clip_end = 20000.0
cam = bpy.data.objects.new("EXIFcam", cd)
sc.collection.objects.link(cam)
cam.location = cam_args[:3]
d = Vector(cam_args[3:6]) - Vector(cam.location)
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
sc.camera = cam
sc.render.resolution_x = 1600
sc.render.resolution_y = 1067
sc.cycles.samples = 32

for dz in DZS:
    for ob in mesh_objs:
        ob.location.z = base_z[ob.name] + dz
    sc.render.filepath = "%s_dz%+.1f.png" % (prefix, dz)
    t1 = time.time()
    bpy.ops.render.render(write_still=True)
    print("DZ %+.1f RENDER_SEC %.1f -> %s" % (dz, time.time() - t1, sc.render.filepath))
print("DZSCAN_DONE")
