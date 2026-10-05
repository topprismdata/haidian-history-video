# -*- coding: utf-8 -*-
"""WaterFix 水面/岸坡材质 A/B 渲染: blend 内旧材质 vs 盘上 materials.py 新版。

用法: blender -b e30_bridge.blend --python ab_water_split.py -- [res] [samples]

A = 打开 e30_bridge.blend 后以"旧版 materials.py"重建 water/earth 材质渲 hero
    (argv[2]=旧模块路径; 不传则 A=blend 内置材质原样 —— 但 blend 会被并行
    rebuild 重写, 建议总传旧模块, 见 ab_water/measure_ab.py 报告注记);
B = 用盘上 materials.py 新建 water_material()/earth_material() 重赋给
    water / shore_bank 对象后, 同相机再渲。
单进程内完成 A、B, 相机只建一次 —— A/B 差异只来自水/岸材质, 与在途
build_scene2 及盘上 blend 重建完全隔离。渲染前有 A≠B 探针(bump/节点数)。
量化: ab_water/measure_ab.py。png 不入库, 本脚本入库。
"""
import bpy, os, sys, math
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
res = int(a[0]) if a and a[0].isdigit() else 800
smp = int(a[1]) if len(a) > 1 and a[1].isdigit() else 32

bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "e30_bridge.blend"))
sc = bpy.context.scene
cp = bpy.context.preferences.addons['cycles'].preferences
try:
    cp.compute_device_type = 'METAL'
except Exception:
    pass
for d in cp.devices:
    d.use = (d.type == 'METAL')
sc.cycles.device = 'GPU'
sc.cycles.samples = smp
# 确定性: 与 shot_auto2 同 seed 且关 animated_seed(像素序列层)
sc.cycles.seed = 20261004
sc.cycles.use_animated_seed = False
sc.cycles.use_denoising = True
sc.render.resolution_x = res
sc.render.resolution_y = int(res * 9 / 16)
sc.render.image_settings.file_format = 'PNG'
print("AB_WATER_SEED %d (animated=%s, device=%s, samples=%d, res=%dx%d)"
      % (sc.cycles.seed, sc.cycles.use_animated_seed, sc.cycles.device, smp,
         sc.render.resolution_x, sc.render.resolution_y))

BRIDGE = [bpy.data.objects[n] for n in
          ("bridge_body", "voussoir", "deck_rail", "beasts") if bpy.data.objects.get(n)]
mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
for o in BRIDGE:
    for c in o.bound_box:
        w = o.matrix_world @ Vector(c)
        for k in range(3):
            mn[k] = min(mn[k], w[k]); mx[k] = max(mx[k], w[k])
ctr = (mn + mx) / 2.0; size = mx - mn
_b = BRIDGE[0]
AX = math.atan2(_b.matrix_world[1][0], _b.matrix_world[0][0])
Bv = Vector((math.cos(AX), math.sin(AX), 0.0))
Nv = Vector((-Bv.y, Bv.x, 0.0))
print("bbox %.1f x %.1f x %.1f  axis %.1f deg" % (size.x, size.y, size.z, math.degrees(AX)))

# hero 机位 = shot_auto2 逐条复刻: Nv*0.90+Bv*0.42+(0,0,0.06), dist 1.02,
# z=3+size.z*0.06, 50mm, clip_end 20000(M4b 修的雾盒出射面截断)
cd = bpy.data.cameras.new("C"); cd.lens = 50; cd.clip_end = 20000.0
cam = bpy.data.objects.new("C", cd); bpy.context.collection.objects.link(cam)
sc.camera = cam
bpy.ops.object.select_all(action='DESELECT')
for o in BRIDGE:
    o.select_set(True)
bpy.context.view_layer.objects.active = BRIDGE[0]
dirv = (Nv * 0.90 + Bv * 0.42 + Vector((0, 0, 0.06))).normalized()
pos = ctr - dirv * (size.length / 2.0 * 1.02)
pos.z = 3.0 + size.z * 0.06
cam.location = pos
cam.rotation_euler = (ctr - pos).to_track_quat('-Z', 'Y').to_euler()
for _ in range(14):
    bpy.context.view_layer.update()
    bpy.ops.view3d.camera_to_view_selected()
    bpy.ops.object.select_all(action='DESELECT')
    for o in BRIDGE:
        o.select_set(True)
    bpy.context.view_layer.objects.active = BRIDGE[0]

OUTDIR = os.path.join(HERE, "ab_water")
if not os.path.isdir(OUTDIR):
    os.makedirs(OUTDIR)

# 任务要求: 先打印 blend 对象名单确认名字, 再按名字定位换材质
names = sorted(o.name for o in bpy.data.objects)
print("BLEND_OBJECTS: %s" % ",".join(names))


def _assign(ob, mat):
    if ob.data.materials:
        ob.data.materials[0] = mat
    else:
        ob.data.materials.append(mat)


def _bump_strength(mat):
    for nd in mat.node_tree.nodes:
        if nd.type == 'BUMP':
            return nd.inputs["Strength"].default_value
    return None


# ── A: 旧材质基线 ──
# 无第 3 参: blend 内置材质原样渲。⚠ blend 会被并行 rebuild 重写(2026-10-05 实测
# 中途 rebuild 把中间态材质烧了进去, A 侧失去"旧材质"语义)——传 argv[2]=旧版
# materials.py 路径(如 git show HEAD:... 的落盘副本)则由其重建 water/earth 作 A,
# 与 blend 内容解耦。
old_py = a[2] if len(a) > 2 else None
if old_py:
    import importlib.util
    spec = importlib.util.spec_from_file_location("materials_old", old_py)
    MATOLD = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(MATOLD)
    _assign(bpy.data.objects["water"], MATOLD.water_material("water_old"))
    _assign(bpy.data.objects["shore_bank"], MATOLD.earth_material("shore_earth_old"))
    print("A baseline rebuilt from %s" % old_py)
else:
    print("A baseline = blend 内置材质")

# 探针基线必须在 B 侧换材质"之前"采样(首版在 swap 后读槽位, 读到的是新材质,
# 探针自己被打假 —— A/B 两侧引用在渲染前先抓快照)
m_water_old = bpy.data.objects["water"].data.materials[0]
m_earth_old = bpy.data.objects["shore_bank"].data.materials[0]
bs_old = _bump_strength(m_water_old)
nn_old = len(m_earth_old.node_tree.nodes)

outA = os.path.join(OUTDIR, "ab_hero_A_old.png")
sc.render.filepath = outA
bpy.ops.render.render(write_still=True)
print("A ->", outA)

# ── B: 盘上 materials.py 新建 water/earth 重赋 ──
import materials as MAT
m_water = MAT.water_material("water_ab")
m_earth = MAT.earth_material("shore_earth_ab")
targets = ["water"] + [o.name for o in bpy.data.objects
                       if o.name.startswith("shore_bank")]
swap = []
for name in targets:
    ob = bpy.data.objects.get(name)
    if ob is None:
        continue
    _assign(ob, m_water if name == "water" else m_earth)
    swap.append((name, ob.data.materials[0].name, len(ob.data.materials)))
print("B swap: %s" % swap)
# 换材质必须自证: water 与 shore_bank 都要真的换上, 否则 A/B 无效
got = {n for n, _, _ in swap}
if "water" not in got or not any(n.startswith("shore_bank") for n in got):
    print("AB_WATER_ERROR: water/shore_bank 未全部换上新材料")
    sys.exit(1)
# A/B 差异自证: A 侧水材质 bump Strength(旧 0.20) vs B 侧(新 0.32) 必须不同,
# A 侧岸材质节点数(旧 7, 无湿带) vs B 侧(新 12, 有水线湿带)必须不同
bs_new = _bump_strength(m_water)
nn_new = len(m_earth.node_tree.nodes)
print("PROBE water bump old=%s new=%s | earth nodes old=%d new=%d"
      % (bs_old, bs_new, nn_old, nn_new))
if not (bs_old is not None and bs_new is not None
        and abs(bs_old - bs_new) > 1e-6 and nn_old != nn_new):
    print("AB_WATER_ERROR: A/B 材质探针相同, A/B 无效")
    sys.exit(1)
outB = os.path.join(OUTDIR, "ab_hero_B_waterfix.png")
sc.render.filepath = outB
bpy.ops.render.render(write_still=True)
print("B ->", outB)
print("DONE")
