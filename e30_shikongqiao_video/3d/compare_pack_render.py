# -*- coding: utf-8 -*-
"""M23 照片对照包 - 渲染驱动(只读 blend, 不保存场景)。

所有渲染: Cycles GPU(METAL) + OpenImageDenoise, seed 固定 20261004(可复现),
灯光/材质/世界全部沿用 e30_bridge.blend 现状(= 最终程序化石材质栈: 青石
stone_body/stone_course/stone_ring + 汉白玉 marble + 灰浆 deck_mortar + 水/岸/雾),
本脚本零场景改动, 只架相机与采样参数。

用法: blender -b e30_bridge.blend --python compare_pack_render.py -- <group> <out.png> [samples]
组别:
  b_f150 / c_f175 / d_f675   m20B 三帧 solvePnP 位姿相机(3840x2160)
  e_winter                   m20C 冬照位姿相机(3552x2368)
  a_front                    正交正视, ppm=5.62 与 ref_elevation.jpg 同尺度配准
  f_side                     正交侧视, ppm=80 与 m20B_ortho_a5/a6/a7 同尺度
输出后打印 M23_PARAMS <json>(单行, 供 params 汇总)。
"""
import json
import math
import os
import sys
import time

import bpy
import bpy_extras
import mathutils
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

AXIS = math.radians(112.0)  # 桥轴方位(build_scene2.BRIDGE_AXIS_AZ=112, ortho.py 口径; 103.15 已废)
SEED = 20261004
sc = None
GROUPS = {
    "b_f150":   dict(kind="pose", pose="m20_ctrl/m20B_pose_f150.json",   res=(3840, 2160), samples=1024),
    "c_f175":   dict(kind="pose", pose="m20_ctrl/m20B_pose_f175.json",   res=(3840, 2160), samples=1024),
    "d_f675":   dict(kind="pose", pose="m20_ctrl/m20B_pose_f675.json",   res=(3840, 2160), samples=1024),
    "e_winter": dict(kind="pose", pose="m20_ctrl/m20C_pose_winter.json", res=(3552, 2368), samples=512),
    "a_front":  dict(kind="ortho_front", res=(1920, 879),  samples=512),
    "f_side":   dict(kind="ortho_side",  res=None,       samples=512),  # res 由窗口宽推出
}


def rodrigues(rv):
    th = float(np.linalg.norm(rv))
    if th < 1e-12:
        return np.eye(3)
    k = rv / th
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + math.sin(th) * K + (1 - math.cos(th)) * (K @ K)


def setup_cycles(sc, samples):
    cp = bpy.context.preferences.addons['cycles'].preferences
    try:
        cp.compute_device_type = 'METAL'
    except Exception:
        pass
    for dv in cp.devices:
        dv.use = (dv.type == 'METAL')
    sc.cycles.device = 'GPU'
    sc.cycles.samples = samples
    sc.cycles.seed = SEED
    sc.cycles.use_animated_seed = False
    sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    except Exception:
        pass
    # clip_end: 大场景+体积雾, 默认 1000 会截断雾盒出射面(天空硬边教训)
    sc.cycles.volume_bounces = 0
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGB'
    sc.render.resolution_percentage = 100


def cam_obj(name, lens=None, ortho_scale=None):
    cd = bpy.data.cameras.new(name)
    if lens:
        cd.lens = lens
        cd.sensor_width = 36.0
        cd.sensor_fit = 'HORIZONTAL'
    if ortho_scale:
        cd.type = 'ORTHO'
        cd.ortho_scale = ortho_scale
    cd.clip_start = 0.01
    cd.clip_end = 20000.0
    cam = bpy.data.objects.new(name, cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    return cam


def register_ortho(cam, target_px, res, world_pt, width_m, height_m, span_pts=None, span_px=None):
    """正交相机配准: world_pt 投到 target_px; span_pts 投影横距收敛到 span_px。
    垂直方向用割线法解相机高度 —— 垂直 m/uv 斜率受 sensor 设置影响与解析式不符
    (实测 blend 内 sensor 36x24 时斜率 0.517 而非 1.0), 不信解析式信测量。"""
    tx, ty = target_px[0] / res[0], 1.0 - target_px[1] / res[1]
    P = mathutils.Vector(world_pt)
    for _ in range(4):
        bpy.context.view_layer.update()  # 不刷新则 world_to_camera_view 读到旧矩阵(踩过)
        uv = bpy_extras.object_utils.world_to_camera_view(sc, cam, P)
        dx = (uv.x - tx) * width_m
        R = cam.matrix_world.to_3x3()
        right = R @ mathutils.Vector((1.0, 0.0, 0.0))
        # 目标点偏右(uv.x>tx) => 相机沿 right 正向平移, 点在画面里左移回中
        cam.location = cam.location + right * dx
        if span_pts is not None:
            a = bpy_extras.object_utils.world_to_camera_view(sc, cam, mathutils.Vector(span_pts[0]))
            b = bpy_extras.object_utils.world_to_camera_view(sc, cam, mathutils.Vector(span_pts[1]))
            got = abs(b.x - a.x) * res[0]
            if abs(got - span_px) > 1.0:
                cam.data.ortho_scale *= got / span_px
                width_m = cam.data.ortho_scale
    bpy.context.view_layer.update()
    uv1 = bpy_extras.object_utils.world_to_camera_view(sc, cam, P)
    z1 = cam.location.z
    cam.location.z = z1 + 10.0
    bpy.context.view_layer.update()
    uv2 = bpy_extras.object_utils.world_to_camera_view(sc, cam, P)
    k = (uv2.y - uv1.y) / 10.0
    if abs(k) > 1e-9:
        cam.location.z = z1 + (ty - uv1.y) / k
    bpy.context.view_layer.update()
    return cam.location.copy()


def _register_square_ppm(cam, res, hppm, anchor_px, span_pts, span_px, z_probe,
                         anchor_frac, anchor_pt=(0.0, 0.0, 0.0)):
    """配准 + 垂直比例自校正。正交相机垂直 ppm 受 sensor 设置影响 ≠ 水平 ppm
    (实测本 blend sensor 36x24: 垂直被拉伸 ~2x, 解析式不可信), 实测 vppm 后改
    res_y 使两轴同 ppm, 再按 anchor_frac(锚点画面占比不变)重配准。
    返回 (res, water_row_px)。"""
    res = list(res)
    for _ in range(3):
        register_ortho(cam, anchor_px, res, anchor_pt, cam.data.ortho_scale, res[1] / hppm,
                       span_pts=span_pts, span_px=span_px)
        bpy.context.view_layer.update()
        p0 = mathutils.Vector(anchor_pt)
        p10 = mathutils.Vector(anchor_pt) + mathutils.Vector((0, 0, z_probe))
        u0 = bpy_extras.object_utils.world_to_camera_view(sc, cam, p0).y
        u10 = bpy_extras.object_utils.world_to_camera_view(sc, cam, p10).y
        vppm = abs(u10 - u0) * res[1] / z_probe
        if abs(vppm - hppm) <= 0.02 * hppm:
            break
        res = [res[0], max(64, int(round(res[1] * hppm / vppm)))]
        anchor_px = (anchor_frac[0] * res[0], anchor_frac[1] * res[1])
    return res, round(anchor_frac[1] * res[1])


def apply_m23_fix():
    """内存材质修复栈(不保存 blend, 每次 render 前应用; 记录于 params.m23_fix)。
    依据: 主控三问初判(分色✗/风化✗/石缝△) + 黑楔探针实证(voussoir 法线翻面,
    probe_fix vs probe_fix_novous vs probe_fix_recalc 三级对照, /tmp 探针留存)。
    1) 青石三区冷灰蓝压暗(对齐 materials.py qingshi 口径, 告别近白);
    2) 汉白玉微暖(与青石拉开分色);
    3) 体积雾密度 x0.15(洗白主因; 特写/全景一致);
    4) voussoir/coursing 法线重算(黑楔根因);
    5) 石面插入中尺度逐石微差噪声(乘法 x0.86..1.06, 与既有块编号噪声叠加)。"""
    fixes = {}
    COOL = (0.58, 0.66, 0.80)
    MARB = (1.0, 0.97, 0.92)

    def tint(mat, f):
        n_changed = 0
        for n in mat.node_tree.nodes:
            for inp in n.inputs:
                if inp.type == 'RGBA' and not inp.is_linked:
                    c = list(inp.default_value)
                    inp.default_value = [c[i] * f[i] for i in range(3)] + [c[3]]
                    n_changed += 1
            if n.bl_idname == 'ShaderNodeValToRGB':
                for e in n.color_ramp.elements:
                    e.color = [e.color[i] * f[i] for i in range(3)] + [e.color[3]]
                    n_changed += 1
        return n_changed

    for mn, f in (("stone_body", COOL), ("stone_course", COOL), ("stone_ring", COOL),
                  ("marble", MARB), ("deck_marble", MARB)):
        m = bpy.data.materials.get(mn)
        if m:
            fixes[mn] = tint(m, f)

    fm = bpy.data.materials.get("fog")
    if fm:
        for n in fm.node_tree.nodes:
            for inp in n.inputs:
                if inp.type == 'VALUE' and not inp.is_linked and inp.name == 'Density':
                    inp.default_value *= 0.15
                    fixes["fog_density"] = round(inp.default_value, 5)

    import bmesh
    for nm in ("voussoir", "coursing"):
        o = bpy.data.objects.get(nm)
        if o:
            bm = bmesh.new()
            bm.from_mesh(o.data)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            bm.to_mesh(o.data)
            bm.free()
            fixes["recalc_" + nm] = True

    # 逐石中尺度微差: Noise(scale 1.1, detail 8) -> Ramp(0.42->1.06, 0.62->0.86) -> Mix multiply
    for mn in ("stone_body", "stone_course", "stone_ring"):
        m = bpy.data.materials.get(mn)
        if not m:
            continue
        nt = m.node_tree
        bsdf = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled')
        inp = bsdf.inputs['Base Color']
        if not inp.is_linked:
            continue
        src = inp.links[0].from_socket
        geo = nt.nodes.new('ShaderNodeNewGeometry')
        noise = nt.nodes.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = 1.1
        noise.inputs['Detail'].default_value = 8.0
        ramp = nt.nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].position = 0.42
        ramp.color_ramp.elements[0].color = (1.06, 1.06, 1.06, 1.0)
        ramp.color_ramp.elements[1].position = 0.62
        ramp.color_ramp.elements[1].color = (0.86, 0.86, 0.86, 1.0)
        mix = nt.nodes.new('ShaderNodeMixRGB')
        mix.blend_type = 'MULTIPLY'
        mix.inputs['Fac'].default_value = 1.0
        nt.links.new(src, mix.inputs['Color1'])
        nt.links.new(geo.outputs['Position'], noise.inputs['Vector'])
        nt.links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
        nt.links.new(ramp.outputs['Color'], mix.inputs['Color2'])
        nt.links.new(mix.outputs['Color'], inp)
        fixes["perstone_noise_" + mn] = True
    return fixes


def apply_golden_light():
    """金光对齐变体(内存, 不保存 blend): 主控指定的 WNW 暖阳光行向 (0.760,-0.307,-0.574)
    (P1 RM-123108 同源/P3Light 定版), 低角度暖色 Key SUN + 天光压低增暖。
    albedo 不动(本征冷灰蓝), 暖调全靠灯光——材质判读版与金光对照版同 albedo。
    拱腹辉光依赖 SUN 穿洞+水面 bounce(Cycles 自然解), 不加塞光。"""
    changes = {}
    sun = next((o for o in bpy.data.objects if o.type == 'LIGHT' and o.data.type == 'SUN'), None)
    d = mathutils.Vector((0.760, -0.307, -0.574)).normalized()
    if sun:
        sun.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()  # -Z 对齐行进方向
        sun.data.energy = 26.0
        sun.data.color = (1.0, 0.50, 0.20)          # 低角深金橙(探针 G4 定版)
        sun.data.angle = math.radians(0.8)          # 低角锐影
        changes["sun"] = dict(dir=[round(v, 3) for v in d], energy=26.0,
                              color=[1.0, 0.50, 0.20], angle_deg=0.8)
    sky = next((n for n in sc.world.node_tree.nodes if n.bl_idname == 'ShaderNodeTexSky'), None)
    if sky:
        sky.sun_elevation = math.radians(4.0)
        sky.sun_rotation = math.radians(292.0)      # 原 WNW 口径
        sky.aerosol_density = 1.2                   # 地平线暖霾
        changes["sky"] = dict(elev_deg=4.0, rot_deg=292.0, aerosol=1.2)
    bgw = next((n for n in sc.world.node_tree.nodes if n.bl_idname == 'ShaderNodeBackground'), None)
    if bgw:
        bgw.inputs['Strength'].default_value = 0.05
        changes["world_strength"] = 0.05
    return changes


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    group, out = argv[0], argv[1]
    golden = len(argv) > 2 and argv[2] == "golden"
    samples_ov = None
    if len(argv) > 2 and argv[2].isdigit():
        samples_ov = int(argv[2])
    if len(argv) > 3 and argv[3].isdigit():
        samples_ov = int(argv[3])
    cfg = GROUPS[group]
    samples = samples_ov or cfg["samples"]
    t0 = time.time()
    global sc
    sc = bpy.context.scene

    params = dict(group=group, out=out, samples=samples, seed=SEED,
                  engine="CYCLES/METAL-GPU", denoise="OPENIMAGEDENOISE")

    if cfg["kind"] == "pose":
        pose = json.load(open(os.path.join(HERE, cfg["pose"])))
        w, h = cfg["res"]
        f_px = pose["f"]                     # 标定画幅下的焦距(px)
        f_scale = w / float(pose["w"])       # 渲染分辨率换算(px/px, 保持视场)
        lens = f_px * f_scale * 36.0 / w     # f_px -> mm(sensor 36mm 水平)
        rv = np.array(pose["rvec"], np.float64)
        tv = np.array(pose["tvec"], np.float64)
        R = rodrigues(rv)
        C = -R.T @ tv
        # ── 模型系 -> 世界系: m20 位姿在模型坐标(x=桥轴,y=法向,z=上),
        # blend 里桥整体绕 Z 旋了 -AXIS(实测 bridge_body rot_z=-1.95rad)。
        # 用 bridge_body 的世界旋转矩阵(无量纲化)把相机位姿变换到世界系。
        root = bpy.data.objects["bridge_body"]
        Mw = root.matrix_world.to_3x3()
        axes = [Mw @ mathutils.Vector(v) for v in ((1, 0, 0), (0, 1, 0), (0, 0, 1))]
        Rw = mathutils.Matrix([[axes[c][r] / axes[c].length for c in range(3)] for r in range(3)])
        C_world = Rw @ mathutils.Vector(tuple(float(v) for v in C))
        # cv 相机系(y下,z前) -> blender 相机系(y上,-z前): 世界->cam = F @ R @ Rw^T,
        # 相机对象需要的 cam->world 旋转 = 其转置 = Rw @ R^T @ F (F=diag(1,-1,-1))。
        Fm = mathutils.Matrix.Diagonal((1, -1, -1, 1)).to_3x3()
        Rbl = Rw @ mathutils.Matrix(R.tolist()).transposed() @ Fm
        cam = cam_obj("M23pose", lens=lens)
        dist = float(np.linalg.norm(C))
        cam.data.clip_start = max(0.01, dist * 0.01)
        cam.data.clip_end = max(1000.0, dist * 4.0)  # 雾盒出射面不裁
        cam.location = C_world
        cam.rotation_euler = Rbl.to_euler()
        params.update(camera=dict(type="perspective_pose", pose_json=cfg["pose"],
                                  pose_tag=pose.get("tag", ""), pose_rms_px=pose.get("rms"),
                                  pose_n=pose.get("n"), lens_mm=round(lens, 3),
                                  f_px_at_cal=round(f_px, 1), cal_wh=[pose["w"], pose["h"]],
                                  frame="模型系->世界系(Rz(-112°), bridge_body 实测旋转)",
                                  cam_pos_model=[round(float(v), 3) for v in C],
                                  cam_pos=[round(float(v), 3) for v in C_world]))
    else:
        B = mathutils.Vector((math.cos(-AXIS), math.sin(-AXIS), 0.0))   # 模型+x(桥轴东端) 的世界方向
        Nv = mathutils.Vector((-B.y, B.x, 0.0))                          # 模型+y 的世界方向
        Ez = mathutils.Vector((0.0, 0.0, 1.0))

        def W(x, y, z):
            "模型系 -> 世界系(与 bridge_body 旋转一致)"
            return B * x + Nv * y + Ez * z

        FACE = -Nv  # 被摄面(模型 -y, m20 照片侧) 外法线
        if cfg["kind"] == "ortho_front":
            res0 = cfg["res"]
            hppm = 1920.0 / 341.6  # =5.6224 px/m, 与 ref_elevation.jpg 桥带同尺度
            cam = cam_obj("M23front", ortho_scale=res0[0] / hppm)
            cam.location = FACE * 500 + mathutils.Vector((0, 0, 80.0))
            cam.rotation_euler = (-FACE).to_track_quat('-Z', 'Y').to_euler()
            res, water_row = _register_square_ppm(
                cam, res0, hppm, (883.5, 459.0),
                span_pts=[W(-75, 0, 0), W(75, 0, 0)], span_px=843.0, z_probe=10.0,
                anchor_frac=(883.5 / 1920.0, 459.0 / 879.0), anchor_pt=(0.0, 0.0, 0.0))
            params.update(camera=dict(type="ortho_front", hppm=round(hppm, 4), vppm=hppm,
                                      ortho_scale_m=round(cam.data.ortho_scale, 2),
                                      res_note="res_y 已按实测垂直比例放大使两轴同 ppm",
                                      water_row_px=water_row,
                                      registered_to="ref_elevation.jpg 桥带(水线中点(883.5,459),150m=843px)",
                                      cam_pos=[round(float(v), 2) for v in cam.location]))
        else:  # ortho_side: 与 m20B_ortho_a5/a6/a7 同 ppm=80, 同被摄面(模型 -y)
            # 窗口公式与 m20_pipeline.ortho_rectify 逐式一致(xc±(a+2), z1=deck_z+0.45),
            # 直接读 m20_ctrl/model_ctrl.json, 避免 blender 内依赖 cv2。
            ctrl = json.load(open(os.path.join(HERE, "m20_ctrl", "model_ctrl.json")))
            c = ctrl["constants"]
            half = c["BRIDGE_LEN"] / 2.0
            k = (c["DECK_Z_TOP"] - c["DECK_Z_END"]) / (half * half)
            ai = [5, 6, 7]
            xs = []
            ztops = []
            for i in ai:
                a = ctrl["arches"][str(i)]
                xs += [a["xc"] - a["a"] - 2.0, a["xc"] + a["a"] + 2.0]
                ztops.append(c["DECK_Z_TOP"] - k * (a["xc"] / half) ** 2 + 0.45)
            x0, x1 = min(xs), max(xs)
            z1 = max(ztops)
            ppm = 80.0
            rw = int(round((x1 - x0) * ppm))
            rh = int(round(z1 * ppm)) + 60
            res0 = [rw, rh]
            cam = cam_obj("M23side", ortho_scale=rw / ppm)
            cam.location = FACE * 500 + mathutils.Vector((0, 0, 80.0))
            cam.rotation_euler = (-FACE).to_track_quat('-Z', 'Y').to_euler()
            cx = 0.5 * (x0 + x1)
            res, water_row = _register_square_ppm(
                cam, res0, ppm, (rw / 2.0, rh - 30),
                span_pts=[W(x0, 0, 0), W(x1, 0, 0)], span_px=float(rw), z_probe=10.0,
                anchor_frac=(0.5, (rh - 30.0) / rh), anchor_pt=(cx, 0.0, 0.0))
            params.update(camera=dict(type="ortho_side", hppm=ppm, vppm=ppm,
                                      window_x=[round(x0, 2), round(x1, 2)], window_z=[0.0, round(z1, 2)],
                                      ortho_scale_m=round(cam.data.ortho_scale, 2),
                                      water_row_px=water_row,
                                      registered_to="m20B_ortho_a5+a6+a7 拼接窗口",
                                      cam_pos=[round(float(v), 2) for v in cam.location]))
        w, h = res

    setup_cycles(sc, samples)
    sc.render.resolution_x = w
    sc.render.resolution_y = h
    params["res"] = [w, h]
    params["m23_fix"] = apply_m23_fix()
    if golden:
        params["lighting_variant"] = "golden"
        params["golden_light"] = apply_golden_light()
    else:
        params["lighting_variant"] = "neutral(材质判读版)"

    # 材质/灯光现状快照(供 GPT 审定位"材质缺失 vs 光照掩盖")
    mats = {}
    for m in bpy.data.materials:
        if m.use_nodes:
            bsdf = next((n for n in m.node_tree.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled'), None)
            base = None
            if bsdf:
                bc = bsdf.inputs['Base Color']
                base = [round(v, 3) for v in bc.default_value[:3]] if not bc.is_linked else "linked"
            mats[m.name] = dict(nodes=len(m.node_tree.nodes), users=m.users, base_rgb=base)
    lights = []
    for o in bpy.data.objects:
        if o.type == 'LIGHT' and o.data:
            lights.append(dict(name=o.name, type=o.data.type, energy=round(o.data.energy, 2)))
    sky = next((n for n in sc.world.node_tree.nodes if n.bl_idname == 'ShaderNodeTexSky'), None)
    params["scene"] = dict(
        materials=mats,
        lights=lights,
        sky=dict(type=sky.sky_type, sun_elev_deg=round(math.degrees(sky.sun_elevation), 1),
                 sun_rot_deg=round(math.degrees(sky.sun_rotation), 1)) if sky else None,
        view_transform=sc.view_settings.view_transform,
        blend="e30_bridge.blend(只读, 材质=最终程序化石栈: 青石 body/course/ring + 汉白玉 marble + 灰浆 mortar)")

    os.makedirs(os.path.dirname(out), exist_ok=True)
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    params["render_sec"] = round(time.time() - t0, 1)
    params["png_bytes"] = os.path.getsize(out) if os.path.exists(out) else None
    print("M23_PARAMS " + json.dumps(params, ensure_ascii=False))
    print("M23_DONE", out)


main()
