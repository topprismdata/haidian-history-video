"""九轮第二刀专用: 桥头正侧视剪影探针(对齐 refs side_elev_6794 右端读感)。
低机位长焦从正横向看桥头: 拱桥结束->厚桥台承托->实腹坡体铺向岸上。
用法: blender -b e30_bridge.blend -P _shot_headside.py -- [samples]
"""
import bpy, os, sys, math
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
smp = int(sys.argv[sys.argv.index("--") + 1]) if "--" in sys.argv else 48

sc = bpy.context.scene
cp = bpy.context.preferences.addons['cycles'].preferences
try: cp.compute_device_type = 'METAL'
except Exception: pass
for d in cp.devices: d.use = (d.type == 'METAL')
sc.cycles.device = 'GPU'
sc.cycles.samples = smp
sc.cycles.seed = 20261004
sc.cycles.use_animated_seed = False
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1400, 700
sc.render.image_settings.file_format = 'PNG'

_b = bpy.data.objects["bridge_body"]
AX = math.atan2(_b.matrix_world[1][0], _b.matrix_world[0][0])
Bv = Vector((math.cos(AX), math.sin(AX), 0.0))     # +x 端向
Nv = Vector((-Bv.y, Bv.x, 0.0))

cd = bpy.data.cameras.new("C"); cd.lens = 85       # 长焦: 压透视, 近正侧读剪影
cd.clip_start = 0.1; cd.clip_end = 20000
cam = bpy.data.objects.new("C", cd); bpy.context.collection.objects.link(cam)
sc.camera = cam

# 目标取桥头+前半坡(u 0~25 => 桥心 87.5), 机位正横向低仰角
tgt = (Bv * 87.5) + Vector((0, 0, 2.2))
pos = tgt + Nv * 90.0 + Vector((0, 0, 6.0))
cam.location = pos
cam.rotation_euler = (tgt - pos).to_track_quat('-Z', 'Y').to_euler()
sc.render.filepath = os.path.join(HERE, "_shot_headside.png")
bpy.ops.render.render(write_still=True)
print("WROTE", sc.render.filepath)
