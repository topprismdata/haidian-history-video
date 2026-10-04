"""正交正侧视: 与古建测绘图同源视角, 比例一目了然, 用于与长焦照片逐项校准。
不受透视压缩影响 —— 前几轮机位错误正是被透视骗了。"""
import bpy, os, sys, math
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
a = sys.argv[sys.argv.index("--")+1:]
which = a[0] if a else "side"
res = int(a[1]) if len(a) > 1 and a[1].isdigit() else 2200
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "e30_bridge.blend"))
sc = bpy.context.scene
cp = bpy.context.preferences.addons['cycles'].preferences
try: cp.compute_device_type = 'METAL'
except Exception: pass
for dv in cp.devices: dv.use = (dv.type == 'METAL')
sc.cycles.device = 'GPU'
sc.cycles.samples = 40
sc.cycles.seed = 20261004          # 固定seed: 出图可复现, 值记录于交付报告
sc.cycles.use_animated_seed = False
sc.render.resolution_x = res
sc.render.resolution_y = int(res * 0.42)
sc.render.film_transparent = True
AXIS = math.radians(112.0)   # 桥轴方位: build_scene2.BRIDGE_AXIS_AZ=112.0(北京建筑大学口径), 实测mesh沿-112°±75.00/半宽7.30; 原103.15为过时值(差8.85°致立面压缩/正面分水尖扇形散开)
B = Vector((math.cos(-AXIS), math.sin(-AXIS), 0))
N = Vector((-B.y, B.x, 0))
cd = bpy.data.cameras.new("Ortho")
cd.type = 'ORTHO'
# 视域宽度按需: 桥 150m + 余量
cd.ortho_scale = {"side": 165.0, "front": 90.0, "top": 165.0, "arch": 24.0}[which]
cam = bpy.data.objects.new("Ortho", cd); bpy.context.collection.objects.link(cam)
sc.camera = cam
if which in ("side", "arch"):   # arch=主孔(净跨8.5m)特写, 同侧视方向
    cam.location = N * 500 + Vector((0, 0, 3.5))
    cam.rotation_euler = Vector((-N.x, -N.y, 0)).to_track_quat('-Z','Y').to_euler()
elif which == "front":
    cam.location = -B * 500 + Vector((0, 0, 4.0))
    cam.rotation_euler = Vector((B.x, B.y, 0)).to_track_quat('-Z','Y').to_euler()
else:
    # 顶视: 绕Z转轴角使桥轴(世界-103.15°)横置于画面, 否则150m桥在0.42高宽比下两端被裁
    cam.location = Vector((0,0,500)); cam.rotation_euler = (0, 0, -AXIS)
out = os.path.join(HERE, "ortho_%s.png" % which)
# 配准视图保洁净: abutment_ground(引道楔形块)未跟随桥轴旋转(rot=0 vs 本体-1.9548rad),
# 横在河道里会以假轮廓遮挡立面/透入券洞; water 大平面在正交投影只贡献背景。
# 仅本进程 hide_render, 不保存blend不动几何(T7掩膜IoU主输入必须只有桥体轮廓)。
for _n in ("abutment_ground", "water"):
    _o = bpy.data.objects.get(_n)
    if _o:
        _o.hide_render = True
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("WROTE", out, os.path.getsize(out) if os.path.exists(out) else "MISSING")
