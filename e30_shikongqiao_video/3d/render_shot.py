import bpy, os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
out = argv[0] if argv else os.path.join(HERE, "test_winter.jpg")
res = int(argv[1]) if len(argv) > 1 else 960
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "e30_bridge.blend"))
sc = bpy.context.scene
cp = bpy.context.preferences.addons['cycles'].preferences
cp.compute_device_type = 'METAL'
for d in cp.devices:
    d.use = (d.type == 'METAL')
sc.cycles.device = 'GPU'
sc.cycles.samples = 64
sc.cycles.seed = 20261004          # 固定seed: 出图可复现(与ortho.py同一值)
sc.cycles.use_animated_seed = False
sc.render.resolution_x, sc.render.resolution_y = res, int(res*9/16)
sc.render.image_settings.file_format = 'JPEG'
sc.render.filepath = out

# 相机: 站在桥的西北侧, 顺着桥洞延伸方向(东南)望 —— 北京市园林绿化局 2023 官方指引
import mathutils
cam_d = bpy.data.cameras.new("Cam"); cam_d.lens = 35
cam = bpy.data.objects.new("Cam", cam_d); bpy.context.collection.objects.link(cam)
sc.camera = cam
AXIS = math.radians(112.0)   # 桥轴方位: build_scene2.BRIDGE_AXIS_AZ=112.0(北京建筑大学口径); 原103.15为过时值
# 西北侧 = 桥轴反向 + 侧向偏移
tgt = mathutils.Vector((0, 0, 3.0))
dirv = mathutils.Vector((math.sin(AXIS), math.cos(AXIS), 0))      # 指向东南
side = mathutils.Vector((math.cos(AXIS), -math.sin(AXIS), 0))     # 侧向
pos = tgt - dirv * 150 - side * 70 + mathutils.Vector((0, 0, 14))
cam.location = pos
cam.rotation_euler = (tgt - pos).to_track_quat('-Z', 'Y').to_euler()

print("RENDER device=%s samples=%d res=%dx%d" % (sc.cycles.device, sc.cycles.samples,
      sc.render.resolution_x, sc.render.resolution_y))
bpy.ops.render.render(write_still=True)
print("WROTE", out, os.path.getsize(out) if os.path.exists(out) else "MISSING")
