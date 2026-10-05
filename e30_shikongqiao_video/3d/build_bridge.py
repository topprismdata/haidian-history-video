"""E30《十七孔桥》三维场景: 参数化石桥 + 昆明湖面 + 冬至日光 + Nishita 天空。

参数来源(改���须回写 research.md):
  BRIDGE_LEN/N_SPAN/上宽/下宽/高 -> 北京市公园管理中心 + 官网
  BRIDGE_AXIS_AZ -> 本项目卫星实测 103.15 度(见 research/geo)
  SUNSET_AZ      -> 本项目星历实算 冬至 238.72 度
坐标约定: 1 单位 = 1 米, +Z 向上, +Y 向南, +X 向东(方位角 = atan2(x,y) 自 +Y 顺时针为正)。

Blender 5.2 要点(实测确认, 勿凭旧记忆):
  - action.fcurves 已移除 -> 必须走 layers[0].strips[0].channelbag(slot).fcurves
  - Sky Texture 的 Nishita 已改名 MULTIPLE_SCATTERING
  - Cycles 首选 Metal GPU, 且不要同时勾 CPU(统一内存下会拖慢)
"""
import bpy, bmesh, math, os

HERE = os.path.dirname(os.path.abspath(__file__))

BRIDGE_LEN, N_SPAN = 150.0, 17
PIER_W = 3.0                    # 【推断】墩宽, 无公开档案
DECK_UP_W, DECK_DOWN_W, BRIDGE_H = 6.56, 14.6, 7.0
ARCH_W = BRIDGE_LEN / N_SPAN
SPAN_CLEAR = ARCH_W - PIER_W
BRIDGE_AXIS_AZ = 103.15
SUNSET_AZ = 238.72
LAT, LON = 39.9897, 116.2712
ARCH_RISE_RATIO = 0.62
WATER_Z = 0.0


def az_vec(az_deg, alt_deg=0.0):
    a, e = math.radians(az_deg), math.radians(alt_deg)
    return (math.sin(a)*math.cos(e), math.cos(a)*math.cos(e), math.sin(e))


def new_mat(name, rgb, rough=0.8, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metallic
    return m


def build_bridge(mat_stone, mat_inner):
    objs = []
    rise = SPAN_CLEAR * ARCH_RISE_RATIO
    springer = (BRIDGE_H - rise) * 0.55
    x_start = -BRIDGE_LEN / 2

    # 墩 + 拱圈
    bm = bmesh.new()
    for i in range(N_SPAN + 1):
        xc = x_start + i * ARCH_W
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts[-8:]:
            v.co.x = xc - PIER_W/2 + (v.co.x + 0.5) * PIER_W
            v.co.y = (v.co.y + 0.5) * DECK_DOWN_W - DECK_DOWN_W/2
            v.co.z = (v.co.z + 0.5) * (springer + 1.0) - 1.0
        rr = SPAN_CLEAR / 2
        ring_outer = rr + PIER_W * 0.45
        seg, prev = 20, None
        for k in range(seg + 1):
            t = math.pi * k / seg
            cx = xc + PIER_W/2 + math.cos(t) * rr
            cz = springer + math.sin(t) * rise
            ox = xc + PIER_W/2 + math.cos(t) * ring_outer
            oz = springer + math.sin(t) * ring_outer
            cur = [bm.verts.new(p) for p in
                   ((cx, -DECK_DOWN_W/2, cz), (cx, DECK_DOWN_W/2, cz),
                    (ox, DECK_DOWN_W/2, oz), (ox, -DECK_DOWN_W/2, oz))]
            if prev:
                for a, b in ((0,1),(1,2),(2,3),(3,0)):
                    try: bm.faces.new((prev[a], cur[a], cur[b], prev[b]))
                    except ValueError: pass
            prev = cur
    me = bpy.data.meshes.new("bridge_piers"); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new("bridge_piers", me)
    ob.data.materials.append(mat_stone)
    bpy.context.collection.objects.link(ob); objs.append(ob)

    # 券洞内壁
    bm = bmesh.new()
    for i in range(N_SPAN):
        xc = x_start + PIER_W/2 + i * ARCH_W
        rr, seg = SPAN_CLEAR/2, 20
        ring = []
        for k in range(seg + 1):
            t = math.pi * k / seg
            cx, cz = xc + math.cos(t)*rr, springer + math.sin(t)*rise
            for y in (-DECK_DOWN_W/2, DECK_DOWN_W/2):
                ring.append(bm.verts.new((cx, y, cz)))
        for k in range(seg):
            a, b = ring[2*k:2*k+2], ring[2*k+2:2*k+4]
            bm.faces.new((a[0], b[0], b[1], a[1]))
    me = bpy.data.meshes.new("arch_inner"); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new("arch_inner", me)
    ob.data.materials.append(mat_inner)
    bpy.context.collection.objects.link(ob); objs.append(ob)

    # 桥面 + 望柱
    def deck_z(x):
        # 真实石桥中段高两端低; 抛物线, 中央孔上方最高
        u = (x + BRIDGE_LEN/2) / BRIDGE_LEN
        return BRIDGE_H*0.30 + BRIDGE_H*0.70 * (1 - (2*u - 1)**2)
    bm = bmesh.new()
    nstep = 60
    for s in range(nstep):
        t0 = x_start + s/nstep*BRIDGE_LEN
        t1 = x_start + (s+1)/nstep*BRIDGE_LEN
        z0, z1 = deck_z(t0)+0.55, deck_z(t1)+0.55
        bm.faces.new([bm.verts.new(p) for p in
                      ((t0,-DECK_UP_W/2,z0),(t1,-DECK_UP_W/2,z1),
                       (t1,DECK_UP_W/2,z1),(t0,DECK_UP_W/2,z0))])
        if s % 4 == 0:
            for y in (-DECK_UP_W/2, DECK_UP_W/2):
                bmesh.ops.create_cube(bm, size=1.0)
                for vv in bm.verts[-8:]:
                    vv.co.x = t0 + (vv.co.x+0.5)*0.34 - 0.17
                    vv.co.y = y + (vv.co.y+0.5)*0.34 - 0.17
                    vv.co.z = deck_z(t0)+0.6 + (vv.co.z+0.5)*1.15
        if s % 4 != 3:
            for y in (-DECK_UP_W/2, DECK_UP_W/2):
                bmesh.ops.create_cube(bm, size=1.0)
                for vv in bm.verts[-8:]:
                    vv.co.x = t0 + (vv.co.x+0.5)*(ARCH_W*0.75) - ARCH_W*0.375
                    vv.co.y = y + (vv.co.y+0.5)*0.22 - 0.11
                    vv.co.z = deck_z(t0)+0.55 + (vv.co.z+0.5)*0.62
    me = bpy.data.meshes.new("deck"); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new("deck", me)
    ob.data.materials.append(mat_stone)
    bpy.context.collection.objects.link(ob); objs.append(ob)

    for ob in objs:      # 转到实测方位: 世界方位角 = 绕 Z 转 -az
        ob.rotation_euler = (0.0, 0.0, -math.radians(BRIDGE_AXIS_AZ))
    return objs


def build_water():
    bm = bmesh.new()
    S = 3000.0
    bm.faces.new([bm.verts.new(p) for p in
                  ((-S,-S,WATER_Z),(S,-S,WATER_Z),(S,S,WATER_Z),(-S,S,WATER_Z))])
    me = bpy.data.meshes.new("water"); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new("water", me)
    ob.data.materials.append(new_mat("water", (0.06,0.10,0.13), rough=0.12))
    bpy.context.collection.objects.link(ob)
    return ob


def build_sun_rig(az, alt):
    """Empty 父级 + 太阳灯: 不依赖任何 Python handler, 后台渲染稳定。
    社区已知坑: Sun Position 插件的 frame_change handler 在 -b 批量渲染下会失效。"""
    rig = bpy.data.objects.new("sun_rig", None)
    bpy.context.collection.objects.link(rig)
    d = bpy.data.lights.new("Sun", type='SUN')
    d.energy = 5.0
    d.angle = math.radians(0.526)
    ob = bpy.data.objects.new("Sun", d)
    bpy.context.collection.objects.link(ob)
    ob.parent = rig
    ob.location = (0.0, 0.0, 0.0)
    ob.rotation_euler = (0.0, 0.0, 0.0)
    v = [0.0, 0.0, 0.0]
    vec = az_vec(az, alt)
    # -Z 指向太阳: 灯在原点时 rotation 使 -Z 对准 vec
    ob.rotation_euler = (-math.asin(vec[2]), 0.0, -az)
    return rig, ob


def build_sky(sun_obj):
    """Nishita(5.2 改名 MULTIPLE_SCATTERING): 日落时的真实天空色温。"""
    w = bpy.data.worlds.new("World"); bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        if n.bl_idname != 'ShaderNodeOutputWorld':
            nt.nodes.remove(n)
    out = [n for n in nt.nodes if n.bl_idname == 'ShaderNodeOutputWorld'][0]
    sky = nt.nodes.new('ShaderNodeTexSky')
    sky.sky_type = 'MULTIPLE_SCATTERING'
    sky.sun_elevation = math.radians(1.0)
    sky.sun_rotation = math.radians(SUNSET_AZ)
    # 5.2 实际可写属性(实测): 无 dust_density, 用 aerosol_density
    sky.altitude = 50            # 海拔 m, 北京约 50
    sky.air_density = 1.6        # 冬季干燥空气
    sky.aerosol_density = 2.2    # 5.2 中 dust 的对应项
    sky.ozone_density = 1.0
    sky.ground_albedo = 0.25
    bg = nt.nodes.new('ShaderNodeBackground')
    bg.inputs['Strength'].default_value = 0.35
    nt.links.new(sky.outputs['Color'], bg.inputs['Color'])
    nt.links.new(bg.outputs['Background'], out.inputs['Surface'])
    return sky


def setup_render(samples=256, res=(1920, 1080)):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'GPU'
    cp = bpy.context.preferences.addons['cycles'].preferences
    try:
        cp.compute_device_type = 'METAL'
    except Exception:
        pass
    for d in cp.devices:
        d.use = (d.type == 'METAL')     # 官方建议: 只勾 Metal, 不混 CPU
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.02
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    sc.cycles.max_bounces = 8
    sc.cycles.diffuse_bounces = 3
    sc.cycles.glossy_bounces = 3
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    return sc


if __name__ == "__main__":
    bpy.ops.wm.read_factory_settings(use_empty=True)
    stone = new_mat("stone", (0.62, 0.60, 0.55), rough=0.85)
    inner = new_mat("arch_inner", (0.82, 0.80, 0.74), rough=0.75)
    build_water()
    build_bridge(stone, inner)
    rig, sun = build_sun_rig(SUNSET_AZ, 1.0)
    build_sky(sun)
    sc = setup_render()
    print("PARAM span_clear=%.3f rise=%.2f springer=%.2f" %
          (SPAN_CLEAR, SPAN_CLEAR*ARCH_RISE_RATIO, (BRIDGE_H - SPAN_CLEAR*ARCH_RISE_RATIO)*0.55))
    print("AXIS %.2f  SUN %.2f" % (BRIDGE_AXIS_AZ, SUNSET_AZ))
    print("DEV", [(d.name, d.type, d.use) for d in
                  bpy.context.preferences.addons['cycles'].preferences.devices])
    print("SCENE device:", sc.cycles.device)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "e30_bridge.blend"))
    print("SAVED", os.path.join(HERE, "e30_bridge.blend"))
