"""GPT 诊断法: 纯黑剪影 + 隐藏栏杆。只看轮廓, 判断结构是否到位。"""
import bpy, os, sys, math
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
mode = sys.argv[sys.argv.index("--")+1:]
mode = mode[0] if mode else "sil"
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "e30_bridge.blend"))
sc = bpy.context.scene
cp = bpy.context.preferences.addons['cycles'].preferences
try: cp.compute_device_type = 'METAL'
except Exception: pass
for d in cp.devices: d.use = (d.type == 'METAL')
sc.cycles.device = 'GPU'
sc.cycles.samples = 16
sc.render.resolution_x = 2000
sc.render.resolution_y = 900
sc.render.film_transparent = True
AXIS = math.radians(103.15)
B = Vector((math.cos(-AXIS), math.sin(-AXIS), 0))
N = Vector((-B.y, B.x, 0))
cd = bpy.data.cameras.new("O"); cd.type='ORTHO'; cd.ortho_scale=165.0
cam = bpy.data.objects.new("O", cd); bpy.context.collection.objects.link(cam)
sc.camera = cam
cam.location = N*500 + Vector((0,0,3.5))
cam.rotation_euler = Vector((-N.x,-N.y,0)).to_track_quat('-Z','Y').to_euler()
# 全部染黑
m = bpy.data.materials.new("BLK"); m.use_nodes=True
b = m.node_tree.nodes.get("Principled BSDF")
b.inputs["Base Color"].default_value=(0,0,0,1); b.inputs["Roughness"].default_value=1.0
for o in [x for x in bpy.data.objects if x.type=="MESH"]:
    if not o.data.materials:
        o.data.materials.append(m)
    else:
        o.data.materials.clear(); o.data.materials.append(m)
    if True:
        o.visible_camera = True
# 隐藏栏杆
if mode == "nobody":
    # 隐藏全部栏杆系, 只留桥面薄板 —— 桥面与望柱在同一 mesh, 故用临时副本裁剪
    for n in ("panel","lions","beasts"):
        o=bpy.data.objects.get(n)
        if o: o.hide_render = True
    d=bpy.data.objects.get("deck_rail")
    if d:
        # deck_rail 含桥面板+望柱。删掉高于桥面 0.35m 的顶点, 只留桥面板
        import bmesh as _bm
        me = d.data
        for v in me.vertices:
            if v.co.z > 0.35:
                v.co.z = min(v.co.z, 0.35)
    # 券石层在剪影里也应隐藏(它不是"实体", 是砌缝表现)
    v_=bpy.data.objects.get("voussoir")
    if v_: v_.hide_render = True
out = os.path.join(HERE, "sil_%s.png" % ("body" if mode=="nobody" else "all"))
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("WROTE", out)
