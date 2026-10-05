"""剖切正侧视: 沿桥中面切一刀, 只留靠镜头一半 -> 消除"看穿洞看到远侧上缘"的白横带干扰。
GPT v4 扣分点 1 的正解。"""
import bpy, os, sys, math
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
a = sys.argv[sys.argv.index("--")+1:]
res = int(a[0]) if a and a[0].isdigit() else 2400
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "e30_bridge.blend"))
sc = bpy.context.scene
cp = bpy.context.preferences.addons['cycles'].preferences
try: cp.compute_device_type = 'METAL'
except Exception: pass
for d in cp.devices: d.use = (d.type == 'METAL')
sc.cycles.device = 'GPU'; sc.cycles.samples = 32
sc.render.resolution_x = res
sc.render.resolution_y = int(res * 0.40)
sc.render.film_transparent = True
# 桥体绕 Z 转了 -112 度, 桥轴世界方向
_b = bpy.data.objects.get("bridge_body")
AX = math.atan2(_b.matrix_world[1][0], _b.matrix_world[0][0])
Bv = Vector((math.cos(AX), math.sin(AX), 0.0))
Nv = Vector((-Bv.y, Bv.x, 0.0))
# 只保留法向为正的一半(用 bisect 切)
bm = bpy.data.objects.get("bridge_body")
import bmesh
cut = bmesh.new()
bmesh.ops.bisect_plane(
    bm_data=bm.data, geom=list(bm.data.vertices) + list(bm.data.edges) + list(bm.data.faces),
    plane_co=(0,0,0), plane_no=(Nv.x, Nv.y, 0.0), clear_inner=True, clear_outer=False)
bpy.ops.object.select_all(action='DESELECT')
for n in ("bridge_body","voussoir","deck_rail","lions","beasts"):
    o = bpy.data.objects.get(n)
    if o:
        bpy.ops.object.select_all(action='DESELECT')
        o.select_set(True); bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_add(type='BOOLEAN')  # 占位, 实际用 bisect 见下
        bpy.ops.object.modifier_remove(modifier=bpy.context.object.modifiers[0].name)
# 逐对象 bisect
for n in ("bridge_body","voussoir","deck_rail","lions","beasts"):
    o = bpy.data.objects.get(n)
    if not o or o.type != 'MESH': continue
    me = o.data
    bmesh.ops.bisect_plane(
        bm_data=me, geom=list(me.vertices) + list(me.edges) + list(me.faces),
        plane_co=(0,0,0), plane_no=(Nv.x, Nv.y, 0.0), clear_inner=True, clear_outer=False)
# 相机: 正交, 垂直桥轴, 高度在起拱线以下(z=2.0)以减少透视干扰
BRIDGE = [bpy.data.objects[n] for n in ("bridge_body","voussoir","deck_rail","lions","beasts")
          if bpy.data.objects.get(n)]
mn = Vector((1e9,)*3); mx = Vector((-1e9,)*3)
for o in BRIDGE:
    for c in o.bound_box:
        w = o.matrix_world @ Vector(c)
        for k in range(3): mn[k]=min(mn[k],w[k]); mx[k]=max(mx[k],w[k])
ctr = (mn+mx)/2.0
cd = bpy.data.cameras.new("O"); cd.type='ORTHO'; cd.ortho_scale = 165.0
cam = bpy.data.objects.new("O", cd); bpy.context.collection.objects.link(cam)
sc.camera = cam
cam.location = Nv*400 + Vector((0,0, 3.0))
cam.rotation_euler = Vector((-Nv.x,-Nv.y,0)).to_track_quat('-Z','Y').to_euler()
out = os.path.join(HERE, "section_side.png")
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("WROTE", out)
