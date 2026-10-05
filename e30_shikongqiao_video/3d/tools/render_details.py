# -*- coding: utf-8 -*-
"""M9 补证机位: 券脸环带近景 / 桥面石板低机位 / 狮与栏板对照(18号构图) / 靠山兽对照(17号构图)。

三审修复指令 1/3/4 要求的"同视角对照"与"细部举证"图。
用法: blender -b e30_bridge.blend --python tools/render_details.py
"""
import bpy, os, sys, math
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import facts as F

sc = bpy.context.scene
col = bpy.context.collection
body = bpy.data.objects["bridge_body"]
mw = body.matrix_world
B = (mw.to_3x3() @ Vector((1, 0, 0))).normalized()   # 桥轴
N = (mw.to_3x3() @ Vector((0, 1, 0))).normalized()   # 北横向
UP = Vector((0, 0, 1))

fog = bpy.data.objects.get("fog_volume")
if fog:
    fog.hide_render = True

cp = bpy.context.preferences.addons['cycles'].preferences
try: cp.compute_device_type = 'METAL'
except Exception: pass
for d in cp.devices: d.use = (d.type == 'METAL')
sc.cycles.device = 'GPU'
sc.cycles.samples = 64
sc.cycles.use_denoising = True


def shot(name, cam_loc, aim, lens, res=(1600, 900)):
    cd = bpy.data.cameras.new("C_" + name)
    cd.lens = lens
    cd.clip_end = 20000.0
    cam = bpy.data.objects.new("C_" + name, cd)
    col.objects.link(cam)
    cam.location = cam_loc
    cam.rotation_euler = (Vector(aim) - Vector(cam_loc)).normalized().to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = res
    out = os.path.join(HERE, "delivery", name + ".png")
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print("WROTE", out)
    col.objects.unlink(cam)
    bpy.data.objects.remove(cam)
    bpy.data.cameras.remove(cd)


def P(station, trans, z):
    """桥轴局部坐标 -> 世界: station 沿 B, trans 沿 N(北+), z 世界竖。"""
    return mw @ Vector((station, trans, z))


# 1) 券脸环带近景: 第 9 孔(中央)右拱脚券石环 + 拱腹纵深砌层
shot("19_detail_arch_ring",
     P(-3.0, -10.5, 4.6), P(3.8, -3.4, 6.0), 40)   # M10.1b: 6-7m 斜掠券脸, 环带+拱腹+天空满幅

# 2) 桥面石板低机位: 三带错缝 + 栏板透空节奏
shot("20_detail_deck_slabs",
     P(-4.0, -1.4, F.DECK_Z_TOP + 0.22), P(2.0, -0.5, F.DECK_Z_TOP + 0.0), 24)  # M10.1c: 贴地 24mm, 4-8m 内板缝满幅

# 3) 狮+栏板对照(18 号历史裁切构图: 斜向两开间, 望柱/透空栏板/柱头狮群)
shot("21_cmp_lion_rail_ref18",
     P(-6.0, -8.5, F.DECK_Z_TOP + 2.2), P(0.0, -3.2, F.DECK_Z_TOP + 1.15), 50)

# 4) 靠山兽对照(17 号历史裁切构图: 桥头斜前方, 兽坐抱鼓石与栏板端衔接)
shot("22_cmp_beast_ref17",
     P(79.5, -7.5, F.DECK_Z_END + 2.0), P(73.8, -3.24, F.DECK_Z_END + 1.35), 50)
