# -*- coding: utf-8 -*-
"""M23 逐石层 AOV 渲染: m20 位姿相机, 出 Position/Normal 双 EXR(供逐像素反查 stone_id)。
用法: blender -b e30_bridge.blend --python compare_pack_aov.py -- <pose_json> <tag> [res_x]
产出: out/compare_pack/perstone/<tag>_pos.exr / <tag>_nor.exr / params/rw_cache_<tag>.json
说明: apply_m23_fix 的法线重算必须先跑(黑楔面朝向才正确); 采样 48 即可(位置/法线 pass 确定性)。
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


def apply_m23_fix_geometry():
    """与 compare_pack_render.apply_m23_fix 的几何/材质对齐(法线重算必须一致)。"""
    import bmesh
    for nm in ("voussoir", "coursing"):
        o = bpy.data.objects.get(nm)
        if o:
            bm = bmesh.new()
            bm.from_mesh(o.data)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            bm.to_mesh(o.data)
            bm.free()
    # 青石/汉白玉/雾 与 render 侧同参(遮罩判读与成片观感一致)
    sys.argv = sys.argv  # noqa
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("cpr", os.path.join(HERE, "compare_pack_render.py"))
        # compare_pack_render.main() 会在 import 时执行, 不能整包加载; 手工内联 tint+雾:
    except Exception:
        pass
    COOL = (0.58, 0.66, 0.80)
    MARB = (1.0, 0.97, 0.92)

    def tint(mat, f):
        for n in mat.node_tree.nodes:
            for inp in n.inputs:
                if inp.type == 'RGBA' and not inp.is_linked:
                    c = list(inp.default_value)
                    inp.default_value = [c[i] * f[i] for i in range(3)] + [c[3]]
            if n.bl_idname == 'ShaderNodeValToRGB':
                for e in n.color_ramp.elements:
                    e.color = [e.color[i] * f[i] for i in range(3)] + [e.color[3]]
    for mn, f in (("stone_body", COOL), ("stone_course", COOL), ("stone_ring", COOL),
                  ("marble", MARB), ("deck_marble", MARB)):
        m = bpy.data.materials.get(mn)
        if m:
            tint(m, f)
    fm = bpy.data.materials.get("fog")
    if fm:
        for n in fm.node_tree.nodes:
            for inp in n.inputs:
                if inp.type == 'VALUE' and not inp.is_linked and inp.name == 'Density':
                    inp.default_value *= 0.15


argv = sys.argv[sys.argv.index("--") + 1:]
pose_path, tag = argv[0], argv[1]
res_x = int(argv[2]) if len(argv) > 2 else 1920
apply_m23_fix_geometry()

pose = json.load(open(pose_path))
R = rodrigues(np.array(pose["rvec"], np.float64))
t = np.array(pose["tvec"], np.float64)
C = -R.T @ t
root = bpy.data.objects["bridge_body"]
Mw = root.matrix_world.to_3x3()
axes = [Mw @ mathutils.Vector(v) for v in ((1, 0, 0), (0, 1, 0), (0, 0, 1))]
Rw = mathutils.Matrix([[axes[c][r] / axes[c].length for c in range(3)] for r in range(3)])
Fm = mathutils.Matrix.Diagonal((1, -1, -1, 1)).to_3x3()
Rbl = Rw @ mathutils.Matrix(R.tolist()).transposed() @ Fm
json.dump([[float(Rw[r][c]) for c in range(3)] for r in range(3)],
          open(os.path.join(HERE, "out", "compare_pack", "params", "rw_cache_%s.json" % tag), "w"))

cd = bpy.data.cameras.new("M23aov")
cd.lens = pose["f"] * (res_x / float(pose["w"])) * 36.0 / res_x
cd.sensor_width = 36.0
cd.sensor_fit = 'HORIZONTAL'
cd.clip_start = max(0.01, float(np.linalg.norm(C)) * 0.01)
cd.clip_end = 4000.0
cam = bpy.data.objects.new("M23aov", cd)
sc.collection.objects.link(cam)
sc.camera = cam
cam.location = Rw @ mathutils.Vector(tuple(float(v) for v in C))
cam.rotation_euler = Rbl.to_euler()

sc.render.resolution_x = res_x
sc.render.resolution_y = int(res_x * pose["h"] / pose["w"])
cp = bpy.context.preferences.addons['cycles'].preferences
cp.compute_device_type = 'METAL'
for dv in cp.devices:
    dv.use = (dv.type == 'METAL')
sc.cycles.device = 'GPU'
sc.cycles.samples = 48
sc.cycles.use_denoising = False
sc.cycles.seed = 20261004
sc.cycles.use_animated_seed = False
sc.view_layers[0].use_pass_position = True
sc.view_layers[0].use_pass_normal = True
sc.world.use_nodes = True
if sc.node_tree is None:
    sc.use_nodes = True
nt = sc.node_tree
nt.nodes.clear()
rl = nt.nodes.new('CompositorNodeRLayers')
for name, sock in (("pos", "Position"), ("nor", "Normal")):
    fo = nt.nodes.new('CompositorNodeOutputFile')
    fo.format.file_format = 'OPEN_EXR'
    fo.format.color_depth = '32'
    fo.base_path = os.path.join(HERE, "out", "compare_pack", "perstone")
    fo.file_slots[0].path = "%s_%s_" % (tag, name)
    fo.location = (200, -200 if name == "nor" else 200)
    nt.links.new(rl.outputs[sock], fo.inputs['Image'])
sc.render.image_settings.file_format = 'OPEN_EXR'
sc.render.filepath = os.path.join(HERE, "out", "compare_pack", "perstone", "%s_beauty.exr" % tag)
bpy.ops.render.render(write_still=True)
print("M23_AOV_DONE", tag)
