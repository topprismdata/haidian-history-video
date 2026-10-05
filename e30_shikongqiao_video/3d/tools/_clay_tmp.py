
import bpy, sys, os
import numpy as np
from mathutils import Matrix, Vector
argv = sys.argv[sys.argv.index("--")+1:]
pose = np.load(argv[0]); out = argv[1]; rw = int(argv[2]); rh = int(argv[3])
blend = argv[4]; Wp = float(argv[5]); sgn = float(argv[6])
M = pose[0:16].reshape(4, 4); K = pose[16:25].reshape(3, 3)
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene
clay = bpy.data.materials.new("clay"); clay.use_nodes = True
b = clay.node_tree.nodes.get("Principled BSDF")
b.inputs["Base Color"].default_value = (0.8, 0.8, 0.8, 1)
b.inputs["Roughness"].default_value = 0.9
KEEP = ("bridge_body", "voussoir", "deck_rail", "deck_cornice", "deck_mortar",
        "impost", "pier_plinth", "beasts", "lion_")
for o in sc.objects:
    if o.type != 'MESH':
        continue
    nm = o.name.lower()
    if not any(nm.startswith(k) or k in nm for k in KEEP):
        o.hide_render = True   # water/fog_volume/环境物件一律隐藏
        continue
    o.data.materials.clear()
    o.data.materials.append(clay)
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.5, 0.5, 0.5, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
cam_d = bpy.data.cameras.new("C"); cam = bpy.data.objects.new("C", cam_d)
sc.collection.objects.link(cam); sc.camera = cam
cam.matrix_world = Matrix(M.tolist())
# M11-A 八审修: 分辨率必须先于任何 world_to_camera_view(K_bl 测量), 否则 aspect 伪各向异性
sc.render.resolution_x = rw; sc.render.resolution_y = rh
sc.render.resolution_percentage = 100
sc.render.pixel_aspect_x = 1.0; sc.render.pixel_aspect_y = 1.0
cam_d.sensor_fit = 'HORIZONTAL'; cam_d.sensor_width = 36.0
cam_d.lens = K[0, 0] * (rw / Wp) * 36.0 / rw
cam_d.shift_x = 0.0; cam_d.shift_y = 0.0
bpy.context.view_layer.update()
# 侧车: 实测 Blender 有效内参 K_bl(同机位 M 下对控制点最小二乘), 供比对侧解析内参 warp
import bpy_extras
sys.path.insert(0, os.path.dirname(out))
import cam_register as CR
ctrl3 = [(-75, 0, 0), (75, 0, 0), (0, 0, 8.9), (0, 7.3, 4.0), (-40, -7.3, 6.0),
         (30, 0, 2.5), (-60, 3.0, 6.0)]
rows = []
Xc = []
for c in ctrl3:
    ndc = bpy_extras.object_utils.world_to_camera_view(sc, cam, Vector(c))
    bx, by = ndc[0] * rw, (1 - ndc[1]) * rh
    X = (np.linalg.inv(M) @ np.array([c[0], c[1], c[2], 1.0]))
    d = -X[2]
    xn, yn = X[0] / d, X[1] / d
    Xc.append([xn, yn, bx, by])
Xc = np.array(Xc)
# bx = fx*xn + cx ; by = cy - fy*yn
fx, cx = np.polyfit(Xc[:, 0], Xc[:, 2], 1)
fy, cyb = np.polyfit(-Xc[:, 1], Xc[:, 3], 1)
K_bl = np.array([[fx, 0, cx], [0, fy, cyb], [0, 0, 1.0]])
tgt, _ = CR.project(np.array(ctrl3, float), M, K)
rows = np.hstack([Xc[:, 2:4], tgt / 2.0])
np.save(out + ".ctrl.npy", np.array(rows))
np.save(out + ".Kbl.npy", K_bl)
sc.cycles.samples = 16; sc.cycles.use_denoising = False
sc.render.film_transparent = True
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGBA'
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("WROTE", out)
