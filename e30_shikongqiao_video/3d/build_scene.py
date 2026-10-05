"""组装 E30 桥体场景。与金光解耦: 本脚本只建桥与中性照明, 不含任何日落设置。"""
import bpy, bmesh, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bridge_geom as G
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
BRIDGE_AXIS_AZ = 103.15     # 本项目实测


def mat(name, rgb, rough=0.85):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    b.inputs["Roughness"].default_value = rough
    return m


def from_bm(bm, name, material):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.data.materials.append(material)
    bpy.context.collection.objects.link(ob)
    return ob


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    # 实拍配色: 桥身暖黄石材 / 券石略浅 / 栏板汉白玉白 / 石狮同白
    m_body = mat("stone_body", (0.66, 0.60, 0.44))
    m_ring = mat("stone_ring", (0.70, 0.665, 0.545))   # 券石略深, 与桥身区分
    m_rail = mat("marble", (0.86, 0.85, 0.81))
    m_lion = mat("marble_lion", (0.88, 0.87, 0.83))
    m_beast = mat("marble_beast", (0.84, 0.83, 0.79))
    m_water = mat("water", (0.09, 0.16, 0.20), rough=0.10)

    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1500.0)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, 0.0))
    from_bm(bm, "water", m_water)

    from_bm(G.build_body_bm(), "bridge_body", m_body)
    from_bm(G.build_voussoir_bm(), "voussoir", m_ring)   # 券脸楔形券石(独立层)
    d, l, p = G.build_deck_bm()
    from_bm(d, "deck_rail", m_rail)
    from_bm(p, "panel", m_rail)
    from_bm(l, "lions", m_lion)
    from_bm(G.build_beast_bm(), "beasts", m_beast)

    # 转到实测方位
    for n in ("bridge_body", "voussoir", "deck_rail", "panel", "lions", "beasts"):
        bpy.data.objects[n].rotation_euler = (0, 0, -math.radians(BRIDGE_AXIS_AZ))

    # 中性白昼照明(与金光无关)
    w = bpy.data.worlds.new("World"); bpy.context.scene.world = w; w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.55, 0.62, 0.72, 1.0)
    bg.inputs[1].default_value = 1.0
    d1 = bpy.data.lights.new("Key", type='SUN'); d1.energy = 3.0; d1.angle = math.radians(2.0)
    o1 = bpy.data.objects.new("Key", d1); bpy.context.collection.objects.link(o1)
    o1.rotation_euler = (math.radians(52), 0, math.radians(38))

    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'GPU'
    cp = bpy.context.preferences.addons['cycles'].preferences
    try: cp.compute_device_type = 'METAL'
    except Exception: pass
    for dv in cp.devices: dv.use = (dv.type == 'METAL')
    sc.cycles.samples = 48
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.03
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 6
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    sc.render.image_settings.file_format = 'PNG'
    return sc


if __name__ == "__main__":
    build()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "e30_bridge.blend"))
    print("SAVED e30_bridge.blend")
