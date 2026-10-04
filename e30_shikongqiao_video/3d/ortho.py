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
cd.clip_end = 20000.0   # 默认 1000m 会截断雾盒出射面 -> 天空硬边(见 shot_auto2.py 注)
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
# 配准视图保洁净: water 大平面在正交投影只贡献背景, 隐藏以免污染掩膜。
# (abutment_ground 曾未跟随桥轴旋转而横在河道里遮挡立面, 已于 bc485a5 修复为随本体
#  一起转 -112°; 仍留在隐藏名单里, 因为它是引道楔形块、不属于桥体本体轮廓。
#  2026-10-05 M4: 新增岸坡地形与体积雾盒同属环境/表现层, 一并隐藏——
#  正交立面是本体轮廓比对图, L3 掩膜只认本体。)
for _n in ("abutment_ground", "water", "shore_bank", "fog_volume"):
    _o = bpy.data.objects.get(_n)
    if _o:
        _o.hide_render = True
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("WROTE", out, os.path.getsize(out) if os.path.exists(out) else "MISSING")

# ── 输出水线像素行（M3-1 比对口径修正, 2026-10-04）──
# bridge_body 的 mesh 从 BODY_BOTTOM=-2.20 起(水下基座, 建模与布尔运算需要它),
# 但实拍照片里**水线以下根本看不见**。L3 拿整张渲染剪影的 bbox 去比参考掩膜
# (参考只到水线), 模型就"高了" —— 实测长高比 13.61 vs 参考 18.76, 差 27%。
# 这不是几何错也不是 facts 错, 是**比对口径错**: 几何与 facts 都不动,
# 只让比对层知道水线在图像哪一行, 由消费方决定裁不裁。
# 正交相机水平看向桥轴, 世界 z 线性映射到像素 y。
from bpy_extras.object_utils import world_to_camera_view as _w2cv
_camz = 3.5 if which in ("side", "arch") else 4.0
_wl = _w2cv(sc, cam, Vector((0.0, 0.0, 0.0)))
_px_y = (1.0 - _wl.y) * sc.render.resolution_y
import json as _json
_side = out.rsplit(".", 1)[0] + ".waterline.json"
with open(_side, "w", encoding="utf-8") as _fp:
    _json.dump({"image": os.path.basename(out),
                "waterline_px_y": round(_px_y, 2),
                "resolution": [sc.render.resolution_x, sc.render.resolution_y],
                "camera_center_z": _camz,
                "ortho_scale": cd.ortho_scale,
                "note": "水线以下(z<0)为水下基座, 实拍不可见; L3 比对应裁掉此线以下"},
               _fp, ensure_ascii=False, indent=1)
print("WATERLINE_PX_Y %.2f -> %s" % (_px_y, os.path.basename(_side)))
