"""端部体量冒烟渲染(六审第3刀验证): 桥台墩座+引道+燕翅墙两端视角.

用法: blender -b e30_bridge.blend --python _shot_end.py [samples]
输出: _shot_end_flank.png(侧前 3/4), _shot_end_low.png(近水面), _shot_end_axial.png(沿引道轴)
clip_end=20000(本机教训: 大场景+体积雾必须放宽远裁剪面, 否则雾在硬边处消失)。
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
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.render.image_settings.file_format = 'PNG'

agr = bpy.data.objects["abutment_ground"]
mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
for v in agr.data.vertices:
    w = agr.matrix_world @ v.co
    for k in range(3):
        mn[k] = min(mn[k], w[k]); mx[k] = max(mx[k], w[k])
# 只取 +x 端(旋转后世界侧未知 -> 取两端中离原点更远的一束)
ctr_all = (mn + mx) / 2.0
end_ctr = None
for sgn in (1, -1):
    c = Vector((sgn * 89.0, 0, 1.5))
    w = agr.matrix_world @ c
    if end_ctr is None or w.length > end_ctr[1].length:
        end_ctr = (sgn, w)
sgn, tgt = end_ctr
_b = bpy.data.objects["bridge_body"]
AX = math.atan2(_b.matrix_world[1][0], _b.matrix_world[0][0])
Bv = Vector((math.cos(AX), math.sin(AX), 0.0)) * sgn   # 指向该端
Nv = Vector((-Bv.y, Bv.x, 0.0))

cd = bpy.data.cameras.new("C"); cd.lens = 40
cd.clip_start = 0.1; cd.clip_end = 20000
cam = bpy.data.objects.new("C", cd); bpy.context.collection.objects.link(cam)
sc.camera = cam

VIEWS = {
    "flank": (Nv * 0.72 - Bv * 0.52 + Vector((0, 0, 0.30)), 46.0),   # 侧前 3/4 看端部全貌
    "low":   (Nv * 0.96 + Bv * 0.18 + Vector((0, 0, 0.10)), 34.0),   # 近水面看墩座/颊墙
    "axial": (-Bv * 0.92 + Nv * 0.30 + Vector((0, 0, 0.18)), 40.0),  # 从引道外段回望桥端
}
for name, (dirv, dist) in VIEWS.items():
    dirv = dirv.normalized()
    pos = tgt + dirv * dist
    pos.z = max(pos.z, 2.6)
    cam.location = pos
    cam.rotation_euler = (tgt - pos).to_track_quat('-Z', 'Y').to_euler()
    out = os.path.join(HERE, "_shot_end_%s.png" % name)
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print("WROTE", out)
