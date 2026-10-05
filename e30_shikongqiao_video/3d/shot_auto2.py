"""自动构图 v2: 用 Blender 内置 camera_to_view_selected 对准, 不手算方向。"""
import bpy, os, sys, math
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
a = sys.argv[sys.argv.index("--")+1:]
view = a[0] if a else "hero"
res = int(a[1]) if len(a) > 1 and a[1].isdigit() else 1600
smp = int(a[2]) if len(a) > 2 and a[2].isdigit() else 64
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "e30_bridge.blend"))
sc = bpy.context.scene
cp = bpy.context.preferences.addons['cycles'].preferences
try: cp.compute_device_type = 'METAL'
except Exception: pass
for d in cp.devices: d.use = (d.type == 'METAL')
sc.cycles.device = 'GPU'; sc.cycles.samples = smp
# ── 渲染可复现（2026-10-04 主控修, T8 冷重建硬门前置）──
# 原设置无 seed 且用 GPU 采样: 同一 blend 两次渲出的像素不会逐位相同,
# 冷启动重建(T8)的渲染哈希对照必然失败——不是流程不可复现, 是采样不确定。
# 官方依据(Cycles Sampling 页): Seed 控制积分器噪声分布; Use Animated Seed
# 会每帧改 seed, 静帧必须关掉, 否则同机位同帧号也会变。
SEED = 20261004
sc.cycles.seed = SEED
sc.cycles.use_animated_seed = False
# 确定性去噪: OIDN 的 Prefilter/Quality 固定; 关掉 animated seed 后单帧仍应稳定
sc.cycles.use_denoising = True
sc.render.resolution_x = res
sc.render.resolution_y = int(res * 9 / 16)
sc.render.image_settings.file_format = 'PNG'
print("SHOT_SEED %d (animated_seed=%s, device=%s, samples=%d)"
      % (SEED, sc.cycles.use_animated_seed, sc.cycles.device, smp))

BRIDGE = [bpy.data.objects[n] for n in
          ("bridge_body","voussoir","deck_rail","beasts") if bpy.data.objects.get(n)]
mn = Vector((1e9,)*3); mx = Vector((-1e9,)*3)
for o in BRIDGE:
    for c in o.bound_box:
        w = o.matrix_world @ Vector(c)
        for k in range(3):
            mn[k]=min(mn[k],w[k]); mx[k]=max(mx[k],w[k])
ctr = (mn+mx)/2.0; size = mx-mn
# 桥的世界轴向(从 mesh 局部 X 实测)
_b = BRIDGE[0]
AX = math.atan2(_b.matrix_world[1][0], _b.matrix_world[0][0])
Bv = Vector((math.cos(AX), math.sin(AX), 0.0))
Nv = Vector((-Bv.y, Bv.x, 0.0))
print("bbox 尺寸 %.1f x %.1f x %.1f  桥轴向 %.1f 度" % (size.x,size.y,size.z, math.degrees(AX)))

cd = bpy.data.cameras.new("C"); cd.lens = 50
# 2026-10-05 修天空硬边(主控量化: 逐行亮度 y=173 跳变 7.68): 默认 clip_end=1000m
# 会把雾盒(z 上限 123, 侧壁 2600m)的出射面截断 —— 出射距离 >1000m 的天空射线
# 没有体积边界穿越, Cycles 体积栈为空 => 雾效为零, 在仰角 atan(121/1000)≈6.9°
# 处形成"有雾/无雾"硬边。clip_end 拉到雾盒对角之外, 所有射线完整穿出体积。
cd.clip_end = 20000.0
cam = bpy.data.objects.new("C", cd); bpy.context.collection.objects.link(cam)
sc.camera = cam
# 先全部选中再 auto frame
bpy.ops.object.select_all(action='DESELECT')
for o in BRIDGE: o.select_set(True)
bpy.context.view_layer.objects.active = BRIDGE[0]

VIEWS = {   # 方向(单位向量) : 拉远倍数
  "hero":  (Nv*0.90 + Bv*0.42 + Vector((0,0,0.06)), 1.02),
  "side":  (Nv, 1.10),
  "front": (Bv, 1.00),
  "low":   (Nv*0.86 + Bv*0.50 + Vector((0,0,0.10)), 1.25),
  "arch":  (Nv*0.50 + Bv*0.86, 0.55),
  "top":   (Vector((0,0,1)), 1.20),
}
dirv, dist_k = VIEWS[view]
dirv = dirv.normalized()
radius = size.length/2.0
# 从目标点往 dirv 反方向退, 并抬到桥面之上
pos = ctr - dirv*(radius*dist_k)
if view in ("hero","low","arch"):
    pos.z = 3.0 + size.z*0.06              # 近水面低机位(实拍摄影位)
else:
    pos.z = max(pos.z, mx.z + size.z*0.15)
cam.location = pos
cam.rotation_euler = (ctr - pos).to_track_quat('-Z','Y').to_euler()

# M13b: arch 机位重写——原(Nv*0.5+Bv*0.86)退到桥端轴向被岸坡挡死, 且 auto-frame
# 把全桥拉回画面(近景变全景)。改为水面侧斜对第3孔, 以 bridge_body 世界bbox做
# local->world z 映射, 瞄准起拱线以上1.5m, 不 auto-frame。
if view == "arch":
    import bridge_geom2 as G
    bb = [o for o in BRIDGE if o.name == "bridge_body"][0]
    bmn = Vector((1e9,)*3); bmx = Vector((-1e9,)*3)
    for c in bb.bound_box:
        w = bb.matrix_world @ Vector(c)
        for k in range(3):
            bmn[k] = min(bmn[k], w[k]); bmx[k] = max(bmx[k], w[k])
    xc_l = (G.PIER_X[2] + G.PIER_X[3]) / 2.0
    def wz(lz):  # local z -> world z(以桥体自身bbox线性映射)
        return bmn.z + (lz - G.BODY_BOTTOM) / (G.DECK_Z_TOP - G.BODY_BOTTOM) * (bmx.z - bmn.z)
    tgt = ctr + Bv * (xc_l * size.x / G.BRIDGE_LEN)
    tgt.z = wz(G.arch_springer_z(2) + 1.5)
    camdir = (Nv * 0.92 + Bv * 0.30).normalized()
    cam.location = tgt + camdir * 26.0
    cam.location.z = wz(1.6)                      # 近水面机位(实拍摄影位)
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cd.lens = 40
    out = os.path.join(HERE, "shot_%s.png" % view)
    sc.render.filepath = out
    print("SHOT arch pos=(%.0f,%.0f,%.0f) lens=%d" % (cam.location.x, cam.location.y, cam.location.z, cd.lens))
    bpy.ops.render.render(write_still=True)
    print("WROTE", out)
    raise SystemExit

# 自动取景: 反复微调距离直到全桥入画
for _ in range(14):
    bpy.context.view_layer.update()
    bpy.ops.view3d.camera_to_view_selected()
    pos2 = cam.matrix_world.translation.copy()
    bpy.ops.object.select_all(action='DESELECT')
    for o in BRIDGE: o.select_set(True)
    bpy.context.view_layer.objects.active = BRIDGE[0]

out = os.path.join(HERE, "shot_%s.png" % view)
sc.render.filepath = out
print("SHOT %s pos=(%.0f,%.0f,%.0f) lens=%d" % (view, cam.location.x, cam.location.y, cam.location.z, cd.lens))
bpy.ops.render.render(write_still=True)
print("WROTE", out)
