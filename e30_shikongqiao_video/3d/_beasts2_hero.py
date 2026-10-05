# -*- coding: utf-8 -*-
"""beasts2 全场景接线验证(一次性驱动, 不改冻结文件):
build_scene2.build() 内存建场景 -> 删旧 beasts 对象 -> beasts2.place_beasts 同锚点放置
-> 打桥轴旋转(与 build_scene2 旋转名单同 -112°) -> 存 _beasts2_hero.blend 供回归渲染。
打印组装验收数: 对象数=4 / unique mesh<=2 / 每 mesh 连通域=1 / 面数。
"""
import bpy, sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bridge_geom2 as G
import build_scene2
import beasts2

build_scene2.build()

# --keep-old: 不换兽, 存旧兽基线 blend(与新版同管线, 隔离"换兽"单一变量)
KEEP_OLD = "--keep-old" in sys.argv

# ── 删旧 beasts(低模 384 顶点) ──
old = bpy.data.objects["beasts"]
old_me = old.data
if not KEEP_OLD:
    bpy.data.objects.remove(old)
    if old_me.users == 0:
        bpy.data.meshes.remove(old_me)

# ── 与 build_beast_bm 相同的锚点公式(坐标=未旋转桥轴系) ──
spots = []
i = 0
for xe in (-G.BRIDGE_LEN / 2 + 1.5, G.BRIDGE_LEN / 2 - 1.5):
    z = G.deck_z(xe)
    for k, side in enumerate((-1, 1)):
        y = side * (G.DECK_UP_W / 2 - 0.10) + side * k * 0.10
        facing = 1.0 if xe > 0 else -1.0        # 旧实现 sx: 兽头朝桥外
        spots.append((xe, y, z, i, facing))
        i += 1

if not KEEP_OLD:
    m_rail = bpy.data.materials.get("marble")
    assert m_rail is not None, "marble 材质缺失(build_scene2 应已建)"
    obs = beasts2.place_beasts(spots, name="beasts", size=1.12, material=m_rail)

    # ── 桥轴旋转: build_scene2 对全部桥体对象 rotation_euler z = -112°, beasts 名单在内 ──
    for ob in obs:
        ob.rotation_euler = (0.0, 0.0, ob.rotation_euler[2] - math.radians(build_scene2.BRIDGE_AXIS_AZ))

    beasts2.dispose_cache()

    # ── 组装验收(主控口径) ──
    import bmesh
    uniq = {ob.data.name for ob in obs}
    print("ASSEMBLY objects=%d unique_meshes=%d" % (len(obs), len(uniq)))
    for me in sorted({ob.data for ob in obs}, key=lambda m: m.name):
        bm = bmesh.new()
        bm.from_mesh(me)
        print("MESH %s faces=%d comps=%d" % (me.name, len(me.polygons), beasts2.count_components(bm)))
        bm.free()

out_blend = os.path.join(HERE, "_beasts_old_hero.blend" if KEEP_OLD else "_beasts2_hero.blend")
bpy.ops.wm.save_as_mainfile(filepath=out_blend)
print("SAVED", out_blend)
