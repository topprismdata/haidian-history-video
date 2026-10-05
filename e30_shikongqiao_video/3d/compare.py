"""渲染桥的三个基本视角, 用于与实拍照片逐项对照。不含任何日落/金光设置。"""
import bpy, os, sys, math
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
a = sys.argv[sys.argv.index("--")+1:]
which = a[0] if a else "side"
res = int(a[1]) if len(a)>1 and a[1].isdigit() else 1400
smp = int(a[2]) if len(a)>2 and a[2].isdigit() else 48
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "e30_bridge.blend"))
sc = bpy.context.scene
cp = bpy.context.preferences.addons['cycles'].preferences
try: cp.compute_device_type = 'METAL'
except Exception: pass
for dv in cp.devices: dv.use = (dv.type == 'METAL')
sc.cycles.device = 'GPU'
sc.cycles.samples = smp
sc.render.resolution_x = res
sc.render.resolution_y = int(res*9/16)
out = os.path.join(HERE, "cmp_%s.png" % which)
sc.render.filepath = out
# 桥在场景里绕 Z 转了 -AXIS, 故桥的世界方向 = 局部 +X 经旋转后的方向。
# 真实侧视必须垂直于该方向, 否则起拱会被透视压平(首轮渲染实证)。
AXIS = math.radians(103.15)
B = Vector((math.cos(-AXIS), math.sin(-AXIS), 0))    # 桥的世界轴向(旋转后)
N = Vector((-B.y, B.x, 0))                            # 法向(侧视方向)
CAMS = {
  # 真侧视: 相机在法向上, 正对桥侧面
  "side":  (N * 340 + Vector((0, 0, 12)), -N, 60),
  # 略偏侧的低角度, 更接近实拍(实拍带一点透视)
  "side2": (N * 300 + B * 60 + Vector((0, 0, 8)), -N, 55),
  # 顺桥望(官方拍摄位: 西北侧顺桥洞方向)
  "front": (-B * 150 + N * 45 + Vector((0, 0, 12)), B, 32),
  "top":   (Vector((0, 0, 300)), Vector((0, 0, -1)), 50),
  "arch":  (-B * 45 + N * 30 + Vector((0, 0, 4)), (N * 0.6 - B * 0.3 + Vector((0, 0, -0.15))), 40),
}
pos, look, lens = CAMS[which]
cd = bpy.data.cameras.new("C"); cd.lens = lens
cam = bpy.data.objects.new("C", cd); bpy.context.collection.objects.link(cam)
cam.location = pos
cam.rotation_euler = Vector(look).to_track_quat('-Z','Y').to_euler()
sc.camera = cam
print("RENDER %s  pos=(%.0f,%.0f,%.0f) lens=%dmm samples=%d" % (which,pos.x,pos.y,pos.z,lens,smp))
bpy.ops.render.render(write_still=True)
print("WROTE", out, os.path.getsize(out) if os.path.exists(out) else "MISSING")
