# -*- coding: utf-8 -*-
""" beasts2 母模快检: 近景双机位(85mm)快渲, 供造型迭代。一次性工具(仿 _lion_preview.py)。

机位: 正面 1.6m(距吻端约 1m)/3-4 侧 3.2m(含全身, 85mm 视场 23.9° 所需)。
"""
import bpy, sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import beasts2
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
variant = int(sys.argv[sys.argv.index("--") + 1]) if "--" in sys.argv else 0

SIZE = 1.12
bm = beasts2.beast_bm(SIZE, variant, seed=variant)
comps = beasts2.count_components(bm)
me = bpy.data.meshes.new("beast")
bm.to_mesh(me); bm.free()
print("FACES %d COMPS %d" % (len(me.polygons), comps))
ob = bpy.data.objects.new("beast", me)
bpy.context.collection.objects.link(ob)

# 地面 + 材质(汉白玉近似)
m = bpy.data.materials.new("marble"); m.use_nodes = True
b = m.node_tree.nodes.get("Principled BSDF")
b.inputs["Base Color"].default_value = (0.88, 0.87, 0.84, 1.0)
b.inputs["Roughness"].default_value = 0.6
me.materials.append(m)
bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 0))

# 光: 天空 + 侧逆光 + 补光(低曝光保石头灰阶)
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.75, 0.82, 0.95, 1.0)
bg.inputs[1].default_value = 0.45
sun = bpy.data.lights.new("S", 'SUN'); sun.energy = 1.8; sun.angle = math.radians(2)
so = bpy.data.objects.new("S", sun); bpy.context.collection.objects.link(so)
so.rotation_euler = (math.radians(55), 0, math.radians(-55))
fill = bpy.data.lights.new("F", 'AREA'); fill.energy = 25; fill.size = 3
fo = bpy.data.objects.new("F", fill); bpy.context.collection.objects.link(fo)
fo.location = (-2, 3, 2.5)
fo.rotation_euler = (math.radians(50), 0, math.radians(140))

cd = bpy.data.cameras.new("C"); cd.lens = 85
cam = bpy.data.objects.new("C", cd); bpy.context.collection.objects.link(cam)
sc.camera = cam
# 兽体中心 ~ (0, 0, 0.55); 正面机位 +X 前方, 3/4 机位转 40 度(取 +y 侧见卷尾)
target = (0.05, 0.0, 0.60)
# 正面 3.2m(85mm 竖幅 1.02m: 角尖 1.12m 恰全入画) / 3-4 侧 3.4m(含全身卷尾) /
# 正面特写 1.6m(距吻端~0.95m, 演示"距兽 ~1m 可辨识"条款: 口裂/鼻卷/须珠在画)。
for ang_deg, name, dist in ((0.0, "front", 3.20), (40.0, "threeq", 3.40),
                            (0.0, "frontclose", 1.60)):
    a = math.radians(ang_deg)
    cx = target[0] + dist * math.cos(a)
    cy = target[1] + dist * math.sin(a)
    cam.location = (cx, cy, target[2] + 0.10)
    cam.rotation_euler = (Vector(target) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.cycles.samples = 64
    sc.cycles.use_denoising = True
    sc.render.engine = 'CYCLES'
    sc.render.resolution_x = 1600
    sc.render.resolution_y = 900
    sc.render.filepath = os.path.join(HERE, "_beast_preview_%s.png" % name)
    bpy.ops.render.render(write_still=True)
    print("WROTE", sc.render.filepath)
