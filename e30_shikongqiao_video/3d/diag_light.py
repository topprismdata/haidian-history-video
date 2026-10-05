"""诊断: 强环境光 + 单侧强光, 分离"几何暗带"与"材质暗带"。"""
import bpy, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "e30_bridge.blend"))
sc = bpy.context.scene
cp = bpy.context.preferences.addons['cycles'].preferences
try: cp.compute_device_type = 'METAL'
except Exception: pass
for d in cp.devices: d.use = (d.type == 'METAL')
sc.cycles.device = 'GPU'; sc.cycles.samples = 40
sc.render.resolution_x, sc.render.resolution_y = 1400, 790
w = sc.world.node_tree.nodes.get('Background')
w.inputs[0].default_value = (1,1,1,1); w.inputs[1].default_value = 2.5
k = bpy.data.objects.get('Key'); k.data.energy = 5.0
# 建相机(正交侧视)
import math
from mathutils import Vector
_b = bpy.data.objects.get("bridge_body")
AX = math.atan2(_b.matrix_world[1][0], _b.matrix_world[0][0])
Nv = Vector((-math.cos(AX), -math.sin(AX), 0.0))
cd = bpy.data.cameras.new("D"); cd.type='ORTHO'; cd.ortho_scale=150.0
cam = bpy.data.objects.new("D", cd); bpy.context.collection.objects.link(cam)
cam.location = Nv*400 + Vector((0,0,4.0))
cam.rotation_euler = Vector((-Nv.x,-Nv.y,0)).to_track_quat('-Z','Y').to_euler()
sc.camera = cam
sc.render.filepath = os.path.join(HERE, "diag_light.png")
bpy.ops.render.render(write_still=True)
print("WROTE diag_light.png")
