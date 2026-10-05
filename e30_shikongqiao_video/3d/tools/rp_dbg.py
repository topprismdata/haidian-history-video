# -*- coding: utf-8 -*-
"""在中央主孔上方南北两侧生成官方题额石匾并渲染清晰可读的3D刻字特写图。

依据: 《钦定日下旧闻考》卷八十四确证:
南额曰「修蝀凌波」, 北额曰「灵鼍偃月」。
位于中央大拱(第9孔)正上方券脸墙上。
"""
import bpy, bmesh, os, sys, math
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import facts as F
import assumptions as A

bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "e30_bridge.blend"))
sc = bpy.context.scene
col = bpy.context.collection

cp = bpy.context.preferences.addons['cycles'].preferences
try: cp.compute_device_type = 'METAL'
except Exception: pass
for d in cp.devices: d.use = (d.type == 'METAL')
sc.cycles.device = 'GPU'
sc.cycles.samples = 96
sc.cycles.use_denoising = True

# 隐藏全域雾效盒以确保特写清晰可读
fog_ob = bpy.data.objects.get("fog_volume")
if fog_ob:
    fog_ob.hide_render = True

# 获取 bridge_body 的精确变换矩阵
body = bpy.data.objects["bridge_body"]
mw = body.matrix_world

# 载入中文字体
font_paths = [
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc"
]
font_obj = None
for fp in font_paths:
    if os.path.exists(fp):
        try:
            font_obj = bpy.data.fonts.load(fp)
            print("Loaded font:", fp)
            break
        except Exception as e:
            print("Failed to load", fp, e)

def _hw_at(z, x=0.0):
    """桥身收分半宽(与 bridge_geom2._width_at 同公式): DECK_DOWN_W=14.6 为水下基座全宽,
    DECK_UP_W=6.56 为桥顶全宽 —— 二审埋牌根因: 误用 2.70 致牌埋入桥身 0.9m。"""
    t = 1.0 - (2.0 * abs(x) / F.BRIDGE_LEN) ** 2
    zt = F.DECK_Z_END + (F.DECK_Z_TOP - F.DECK_Z_END) * t
    f = max(0.0, min(1.0, (z - A.BODY_BOTTOM) / (zt - A.BODY_BOTTOM)))
    return (F.DECK_DOWN_W + (F.DECK_UP_W - F.DECK_DOWN_W) * f) / 2.0


def create_plaque(text_str, side_sign):
    # side_sign = -1 为南侧 (local -Y), +1 为北侧 (local +Y)
    plaque_z = 7.05                      # 券顶 6.73 与仰天石 7.65 之间券脸正中
    hw = _hw_at(plaque_z)                # 实测收分半宽(~3.56), 牌背贴墙
    
    # 局部坐标定义: 位于中央拱(local x=0)上方, local y = side_sign * (hw + 0.04)
    loc_local = Vector((0.0, side_sign * (hw + 0.04), plaque_z))
    pos_world = mw @ loc_local
    
    W, H, T = 2.10, 0.58, 0.08
    bm = bmesh.new()
    v = [bm.verts.new(p) for p in (
        (-W/2, -T/2, -H/2), (W/2, -T/2, -H/2), (W/2, T/2, -H/2), (-W/2, T/2, -H/2),
        (-W/2, -T/2,  H/2), (W/2, -T/2,  H/2), (W/2, T/2,  H/2), (-W/2, T/2,  H/2)
    )]
    for f in ((0,1,2,3), (4,5,6,7), (0,1,5,4), (1,2,6,5), (2,3,7,6), (3,0,4,7)):
        try: bm.faces.new([v[k] for k in f])
        except ValueError: pass
        
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.normal_update()
    
    me = bpy.data.meshes.new(f"plaque_mesh_{side_sign}")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(f"plaque_{side_sign}", me)
    col.objects.link(ob)
    
    ob.location = pos_world
    ob.rotation_euler = body.rotation_euler
    
    mat_marble = bpy.data.materials.get("marble")
    if mat_marble:
        ob.data.materials.append(mat_marble)

    # 3D 雕刻汉字
    if font_obj:
        cd = bpy.data.curves.new(f"txt_{side_sign}", 'FONT')
        cd.font = font_obj
        cd.body = text_str
        cd.size = 0.38
        cd.extrude = 0.035
        cd.align_x = 'CENTER'
        cd.align_y = 'CENTER'
        t_ob = bpy.data.objects.new(f"txt_ob_{side_sign}", cd)
        col.objects.link(t_ob)
        
        # 旋转对齐(列向量=字体局部基): 南侧读向+X/法向-Y; 北侧读向-X/法向+Y (消除镜像)
        if side_sign == -1:
            R_local = Matrix(((1,0,0),(0,0,1),(0,-1,0))).transposed()
        else:
            R_local = Matrix(((-1,0,0),(0,0,1),(0,1,0))).transposed()
        rot_mat = body.rotation_euler.to_matrix()
        t_ob.rotation_euler = (rot_mat @ R_local).to_euler()
        
        mat_text = bpy.data.materials.new(f"mat_text_{side_sign}")
        mat_text.use_nodes = True
        bsdf = mat_text.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            # 填金深朱砂红
            bsdf.inputs["Base Color"].default_value = (0.28, 0.05, 0.04, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.35
        t_ob.data.materials.append(mat_text)

    return ob

ob_south = create_plaque("修蝀凌波", -1)
ob_north = create_plaque("灵鼍偃月", 1)
def render_plaque_view(target_ob, side_sign, out_name, title_text, rake=False):
    # 法向在世界空间的方向
    norm_world = (mw.to_3x3() @ Vector((0.0, side_sign, 0.0))).normalized()
    b_world = (mw.to_3x3() @ Vector((1.0, 0.0, 0.0))).normalized()
    if rake:
        # 斜侧掠光: 相机沿墙侧移, 光源贴墙掠射强化刻字凹凸阴影
        cam_pos = target_ob.location + norm_world * 1.5 + b_world * 2.2 + Vector((0, 0, 0.15))
        lens = 60.0
    else:
        cam_pos = target_ob.location + norm_world * 2.40 + Vector((0, 0, -0.02))
        lens = 75.0
    cd = bpy.data.cameras.new("CamPlaque")
    cd.lens = lens
    cam = bpy.data.objects.new("CamPlaque", cd)
    col.objects.link(cam)
    cam.location = cam_pos

    direction = (target_ob.location - cam.location).normalized()
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam

    if rake:
        light_data = bpy.data.lights.new("PlaqueLight", 'SUN')
        light_data.energy = 4.0
        light_data.angle = math.radians(2.0)
        light_ob = bpy.data.objects.new("PlaqueLight", light_data)
        col.objects.link(light_ob)
        lpos = target_ob.location + b_world * 3.0 + norm_world * 0.5 + Vector((0, 0, 0.25))
        light_ob.location = lpos
        light_ob.rotation_euler = (target_ob.location - lpos).normalized().to_track_quat('-Z', 'Y').to_euler()
    else:
        light_data = bpy.data.lights.new("PlaqueLight", 'POINT')
        light_data.energy = 350.0
        light_data.shadow_soft_size = 0.2
        light_ob = bpy.data.objects.new("PlaqueLight", light_data)
        col.objects.link(light_ob)
        light_ob.location = cam_pos + Vector((0, 0, 0.3))

    out_file = os.path.join(HERE, "delivery", out_name)
    sc.render.resolution_x = 1200
    sc.render.resolution_y = 675
    sc.render.filepath = out_file
    bpy.ops.render.render(write_still=True)
    print(f"Rendered {title_text} to {out_file}")

    col.objects.unlink(cam)
    col.objects.unlink(light_ob)
    bpy.data.objects.remove(cam)
    bpy.data.objects.remove(light_ob)
    bpy.data.cameras.remove(cd)
    bpy.data.lights.remove(light_data)


# DEBUG: 首渲前射线自检
_dg = bpy.context.evaluated_depsgraph_get()
_t = bpy.data.objects["txt_ob_-1"]
_tb = _t.location
_N = (mw.to_3x3() @ Vector((0.0, -1.0, 0.0))).normalized()
_cp = _tb + _N * 2.4
_d = (_tb - _cp).normalized()
_hit, _loc, _n, _i, _obj, _m = sc.ray_cast(_dg, _cp, _d)
print("DBG ray from cam to text center hits:", _obj.name if _hit else "none", "at transverse", round(_loc.dot(_N),4) if _hit else None)
_ev = _t.evaluated_get(_dg); _m2 = _ev.to_mesh()
print("DBG matrix:", [tuple(round(c,3) for c in row) for row in _t.matrix_world])
print("DBG text eval verts:", len(_m2.vertices), "dims:", tuple(round(d,3) for d in _t.dimensions))
_ev.to_mesh_clear()

render_plaque_view(ob_south, -1, "09_render_plaque_south_front.png", "南额「修蝀凌波」正视")
render_plaque_view(ob_south, -1, "09b_render_plaque_south_raking.png", "南额「修蝀凌波」掠光", rake=True)
render_plaque_view(ob_north, 1, "10_render_plaque_north_front.png", "北额「灵鼍偃月」正视")
render_plaque_view(ob_north, 1, "10b_render_plaque_north_raking.png", "北额「灵鼍偃月」掠光", rake=True)
