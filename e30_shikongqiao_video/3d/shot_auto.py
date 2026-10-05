"""自动构图渲染: 从场景实测包围盒算机位, 不再手算方向(此前多次算错)。"""
import bpy, os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
a = sys.argv[sys.argv.index("--")+1:]
view = a[0] if a else "hero"
res = int(a[1]) if len(a) > 1 and a[1].isdigit() else 1600
smp = int(a[2]) if len(a) > 2 and a[2].isdigit() else 64
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "e30_bridge.blend"))
sc = bpy.context.scene
cp = bpy.context.preferences.addons['cycles'].preferences
try: cp.compute_device_type = 'METAL'
except Exception: pass
for d in cp.devices: d.use = (d.type == 'METAL')
sc.cycles.device = 'GPU'; sc.cycles.samples = smp
sc.render.resolution_x = res
sc.render.resolution_y = int(res * 9 / 16)
sc.render.image_settings.file_format = 'PNG'
sc.render.film_transparent = False

# 实测包围盒(排除水面)
mn = Vector((1e9,)*3); mx = Vector((-1e9,)*3)
for o in bpy.data.objects:
    if o.type != 'MESH' or o.name == 'water':
        continue
    for c in o.bound_box:
        w = o.matrix_world @ Vector(c)
        for k in range(3):
            mn[k] = min(mn[k], w[k]); mx[k] = max(mx[k], w[k])
ctr = (mn + mx) / 2.0
size = mx - mn
print("包围盒 min(%.1f,%.1f,%.1f) max(%.1f,%.1f,%.1f) 尺寸 %.1f x %.1f x %.1f"
      % (mn.x,mn.y,mn.z,mx.x,mx.y,mx.z,size.x,size.y,size.z))

# 桥的世界轴向(几何模块按 BRIDGE_AXIS_AZ 旋转了)
# 桥轴从场景实测: 主体 mesh 绕 Z 旋转, 取其局部 +X 轴的世界方向
_body = bpy.data.objects.get("bridge_body")
if _body:
    AX = math.atan2(_body.matrix_world[1][0], _body.matrix_world[0][0])
else:
    AX = 0.0
B = Vector((math.cos(AX), math.sin(AX), 0.0))   # 桥轴
N = Vector((-B.y, B.x, 0.0))                    # 法向

VIEWS = {
  # (视线方向单位向量, 距离倍数, 高度倍数, 焦距)
  "hero":   (N * 0.94 + B * 0.34 + Vector((0,0,0.16)), 1.05, 0.30, 45),
  "side":   (N, 1.15, 0.12, 50),
  "front":  (B, 0.85, 0.16, 40),
  "low":    (N * 0.90 + B * 0.44 + Vector((0,0,0.06)), 1.0, 0.10, 45),
  "arch":   (N * 0.55 + B * 0.83, 0.42, 0.22, 35),
}
dirv, dist_k, hgt_k, lens = VIEWS[view]
dirv = dirv.normalized()
radius = size.length / 2.0
pos = ctr - dirv * (radius * dist_k) + Vector((0, 0, size.z * hgt_k))
cd = bpy.data.cameras.new("C"); cd.lens = lens
cd.clip_end = 20000.0   # 默认 1000m 会截断雾盒出射面 -> 天空硬边(见 shot_auto2.py 注)
cam = bpy.data.objects.new("C", cd); bpy.context.collection.objects.link(cam)
cam.location = pos
cam.rotation_euler = (ctr - pos).to_track_quat('-Z','Y').to_euler()
sc.camera = cam
out = os.path.join(HERE, "shot_%s.png" % view)
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("SHOT %s pos=(%.0f,%.0f,%.0f) lens=%d" % (view, pos.x, pos.y, pos.z, lens))
print("WROTE", out)
