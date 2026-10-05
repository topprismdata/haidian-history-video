# -*- coding: utf-8 -*-
"""近景证据机位: 栏外拍柱头狮 正面/3-4侧(35mm 全栈)。渲染纪律与 shot_auto2 一致。用法: blender -b -P tools/lion_closeup.py -- front|threeq 1600 64"""
import bpy, os, sys, math
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 3d/
sys.path.insert(0, HERE)
a = sys.argv[sys.argv.index("--")+1:]
which = a[0] if a else "front"
res = int(a[1]) if len(a) > 1 and a[1].isdigit() else 1600
smp = int(a[2]) if len(a) > 2 and a[2].isdigit() else 64

bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "e30_bridge.blend"))
sc = bpy.context.scene
cp = bpy.context.preferences.addons['cycles'].preferences
try: cp.compute_device_type = 'METAL'
except Exception: pass
for d in cp.devices: d.use = (d.type == 'METAL')
sc.cycles.device = 'GPU'; sc.cycles.samples = smp
sc.cycles.seed = 20261004
sc.cycles.use_animated_seed = False
sc.cycles.use_denoising = True
sc.render.resolution_x = res
sc.render.resolution_y = int(res * 9 / 16)
sc.render.image_settings.file_format = 'PNG'

o = bpy.data.objects["lion_adult_031_+1"]
AZ = -math.radians(112.0)
facing = Vector((math.cos(AZ), math.sin(AZ), 0.0))
head_local = Vector((0.17, 0.0, 0.72))          # v3 母模头部中心(单位高)
head_w = o.matrix_world @ (head_local * o.scale.x)
dist = 2.2                                      # 三审口径: 拉远含透空栏板+邻柱语境, 杜绝"巨狮"误读
if which == "front":
    ang = 0.0
else:
    ang = math.radians(-38.0)                    # 3/4: 绕竖轴转
from mathutils import Matrix
f2 = Matrix.Rotation(ang, 3, 'Z') @ facing
outward = Vector((0.927, -0.375, 0.0))          # side+1 栏外法向 = R_z(-112°)@(0,1,0)
camloc = head_w + f2 * dist + outward * 0.55    # 栏外机位: 望柱+栏板+邻柱入画
aim = Vector((head_w.x, head_w.y, head_w.z + 0.07))  # 狮+柱头承台居中
camloc.z = aim.z + 0.05
cd = bpy.data.cameras.new("C"); cd.lens = 50
cd.clip_end = 20000.0
cam = bpy.data.objects.new("C", cd); bpy.context.collection.objects.link(cam)
cam.location = camloc
cam.rotation_euler = (aim - camloc).to_track_quat('-Z', 'Y').to_euler()
sc.camera = cam
out = os.path.join(HERE, "lion_closeup_%s.png" % which)
sc.render.filepath = out
print("CLOSEUP %s cam=(%.3f,%.3f,%.3f) aim=(%.3f,%.3f,%.3f) dist=%.3f"
      % (which, camloc.x, camloc.y, camloc.z, aim.x, aim.y, aim.z,
         (camloc - aim).length))
bpy.ops.render.render(write_still=True)
print("WROTE", out)
