# -*- coding: utf-8 -*-
"""坐实核验 v2(用法: blender -b -P tools/lion_seat_check.py): 狮底垫中心到 deck_rail 最近表面距离+法线。
底垫底面位于柱顶面内 2cm(=1.20-1.18) => 距离≈0.02 且法线≈+Z 即为就位。"""
import bpy, sys, re
from mathutils import Vector
import os
bpy.ops.wm.open_mainfile(filepath=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "e30_bridge.blend"))
dg = bpy.context.evaluated_depsgraph_get()
rail = bpy.data.objects["deck_rail"].evaluated_get(dg)
mains = [o for o in bpy.data.objects if re.match(r"lion_\d+_", o.name)]
ok = 0; n = 0; bad = []
for o in mains[::8]:   # 抽 1/8 = 16 只
    n += 1
    base_c = o.matrix_world @ Vector((0.0, 0.0, 0.005))
    hit, loc, nrm, idx = rail.closest_point_on_mesh(base_c)
    d = (base_c - loc).length if hit else 9e9
    if hit and d < 0.03 and nrm.z > 0.9:
        ok += 1
    else:
        bad.append((o.name, round(d, 4), tuple(round(v, 2) for v in nrm)))
print("SEATED %d/%d bad=%s" % (ok, n, bad[:6]))
