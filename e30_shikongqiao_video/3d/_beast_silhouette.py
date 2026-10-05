# -*- coding: utf-8 -*-
""" beasts2 剪影快检: 正侧+正面纯黑剪影(白底), 供九审轮廓迭代。一次性工具。

用法: blender -b --python _beast_silhouette.py -- <variant> <outdir>
输出: <outdir>/sil_v<variant>_side.png / _front.png
"""
import bpy, sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import beasts2

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
variant = int(argv[0]) if argv else 0
outdir = argv[1] if len(argv) > 1 else HERE

bm = beasts2.beast_bm(1.0, variant, seed=variant)
comps = beasts2.count_components(bm)
me = bpy.data.meshes.new("beast")
bm.to_mesh(me)
bm.free()
print("FACES %d COMPS %d" % (len(me.polygons), comps))
ob = bpy.data.objects.new("beast", me)
bpy.context.collection.objects.link(ob)

# 纯黑自发光兽 + 纯白世界 = 剪影
m = bpy.data.materials.new("sil")
m.use_nodes = True
nt = m.node_tree
nt.nodes.clear()
em = nt.nodes.new("ShaderNodeEmission")
em.inputs[0].default_value = (0.0, 0.0, 0.0, 1.0)
em.inputs[1].default_value = 0.0
out = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(em.outputs[0], out.inputs["Surface"])
me.materials.append(m)

w = bpy.data.worlds.new("W")
sc.world = w
w.use_nodes = True
bg = w.node_tree.nodes["Background"]
bg.inputs[0].default_value = (1.0, 1.0, 1.0, 1.0)
bg.inputs[1].default_value = 1.0

cd = bpy.data.cameras.new("C")
cd.type = 'ORTHO'
cam = bpy.data.objects.new("C", cd)
bpy.context.collection.objects.link(cam)
sc.camera = cam
sc.render.engine = 'CYCLES'
sc.cycles.samples = 4
sc.cycles.use_denoising = False
sc.render.film_transparent = False

# 正侧(+Y 看 -Y, 兽头朝画面左, 与参考照同向) / 正面(+X 看 -X)
for name, loc, rot, resx, resy, ortho in (
        ("side", (0.0, 5.0, 0.53), (math.pi / 2, 0, math.pi), 2000, 1300, 1.95),
        ("front", (5.0, 0.0, 0.53), (math.pi / 2, 0, math.pi / 2), 1000, 1800, 0.80)):
    cam.location = loc
    cam.rotation_euler = rot
    cd.ortho_scale = ortho
    sc.render.resolution_x = resx
    sc.render.resolution_y = resy
    sc.render.filepath = os.path.join(outdir, "sil_v%d_%s.png" % (variant, name))
    bpy.ops.render.render(write_still=True)
    print("WROTE", sc.render.filepath)
