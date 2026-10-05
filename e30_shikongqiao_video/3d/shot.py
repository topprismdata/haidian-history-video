"""按机位名渲一张。机位与实拍对照, 便于逐项核对几何。"""
import bpy, os, sys, math
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
a = sys.argv[sys.argv.index("--")+1:]
name = a[0] if a else "side"
out = a[1] if len(a) > 1 else os.path.join(HERE, "shot_%s.png" % name)
res = int(a[2]) if len(a) > 2 else 1280
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "e30_bridge.blend"))
sc = bpy.context.scene
cp = bpy.context.preferences.addons['cycles'].preferences
try: cp.compute_device_type = 'METAL'
except Exception: pass
for dv in cp.devices: dv.use = (dv.type == 'METAL')
sc.cycles.device = 'GPU'
sc.cycles.samples = int(a[3]) if len(a) > 3 else 40
sc.render.resolution_x = res
sc.render.resolution_y = int(res * 9 / 16)
sc.render.filepath = out

AXIS = math.radians(103.15)
DIR = Vector((math.sin(AXIS), math.cos(AXIS), 0))   # 指向东南(桥轴)
SIDE = Vector((math.cos(AXIS), -math.sin(AXIS), 0))  # 侧向
CAMS = {
    "side":  (-DIR * 320 + Vector((0, 0, 26)), DIR),        # 正侧视
    "front": (-DIR * 150 - SIDE * 60 + Vector((0, 0, 16)), DIR),  # 西北侧顺桥望(官方拍摄位)
    "top":   (Vector((0, 0, 260)), Vector((0, 0, -1))),
    "arch":  (-DIR * 40 - SIDE * 34 + Vector((0, 0, 5)), SIDE * 0.55 + Vector((0, 0, -0.25))),
}
pos, look = CAMS[name]
cd = bpy.data.cameras.new("C")
cd.clip_end = 20000.0   # 默认 1000m 会截断雾盒出射面 -> 天空硬边(见 shot_auto2.py 注)
cd.lens = {"side": 50, "front": 35, "top": 50, "arch": 40}[name]
cam = bpy.data.objects.new("C", cd); bpy.context.collection.objects.link(cam)
cam.location = pos
cam.rotation_euler = Vector(look).to_track_quat('-Z', 'Y').to_euler()
sc.camera = cam
print("SHOT %s  pos=(%.1f,%.1f,%.1f) samples=%d" % (name, pos.x, pos.y, pos.z, sc.cycles.samples))
bpy.ops.render.render(write_still=True)
print("WROTE", out, os.path.getsize(out) if os.path.exists(out) else "MISSING")
