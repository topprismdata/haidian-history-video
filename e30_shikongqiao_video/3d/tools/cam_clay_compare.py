# -*- coding: utf-8 -*-
"""同机位 clay/binary 渲染比对(六审 §8 第 2/3 步)。

读 cam_pose_img0439.npy(M4x4 ravel + K3x3 ravel, Blender 世界矩阵约定) ->
同机位 clay 渲染(禁材质/水/环境, film_transparent: alpha=桥体, 孔=拱洞)。
与实拍派生掩膜分项比对(不平均):
  bridge_body_IoU / void_IoU / contour_Chamfer_px / deck_camber(Pearson+RMSE_px)
实拍掩膜口径: 石作 = L>150 且 y in [deck_top(col), y_water];
deck_top = 逐列亮栏板顶(连续6行亮); y_water = 检出拱底中位数。
shift_y 符号经验校验: 首渲 void IoU < 0.2 则翻转重渲一次。
"""
import json
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import facts as F  # noqa: E402
from cam_register import detect_arches, project, to_world  # noqa: E402

PHOTO = os.path.join(ROOT, "refs/balustrade_count/src/img_0439.jpg")
POSE = os.path.join(HERE, "cam_pose_img0439.npy")
CLAY = os.path.join(HERE, "clay_img0439.png")

BLENDER_SCRIPT = r'''
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
sc.render.resolution_x = rw; sc.render.resolution_y = rh
sc.cycles.samples = 16; sc.cycles.use_denoising = False
sc.render.film_transparent = True
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGBA'
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("WROTE", out)
'''


def deck_top_line(gray, W, y0=1200, y1=1750, thr=170):
    cols = []
    for cx in range(0, W, 4):
        col = gray[y0:y1, cx]
        if col[0:30].min() > 160:      # 天空列: 亮延续到窗顶 -> 不可判
            cols.append(np.nan)
            continue
        hit = np.where(col > thr)[0]
        ok = -1
        for j in range(len(hit) - 6):
            if hit[j + 6] - hit[j] == 6 and hit[j] >= 150:
                ok = hit[j]
                break
        cols.append(ok + y0 if ok >= 0 else np.nan)
    xs = np.arange(0, W, 4)
    cols = np.array(cols, float)
    m = ~np.isnan(cols)
    return np.interp(np.arange(W), xs[m], cols[m]) if m.sum() >= 2 else np.full(W, np.nan)


def opening_masks(M, K, rw, rh, idx, k1=0.0):
    """近面开口半圆+水面线多边形投影 -> void 掩膜(模型预测)。"""
    from cam_register import XC_M, SPAN_M, Z_SPRING, to_world
    polys = []
    for i in idx:
        xc, sp = XC_M[i], SPAN_M[i]
        r = sp / 2.0
        pts = []
        for a in np.linspace(0, np.pi, 40):
            pts.append(to_world(xc - r * np.cos(a), -7.3, Z_SPRING + r * np.sin(a)))
        pts.append(to_world(xc + r, -7.3, 0.0))
        pts.append(to_world(xc - r, -7.3, 0.0))
        P = np.array(pts)
        pr, d = project(P, M, K, k1)
        px = (pr / 2.0).astype(np.int32)
        polys.append(px.reshape(-1, 1, 2))
    m = np.zeros((rh, rw), np.uint8)
    cv2.fillPoly(m, polys, 1)
    return m > 0


def render_clay(sign, W, H):
    script = os.path.join(HERE, "_clay_tmp.py")
    with open(script, "w") as f:
        f.write(BLENDER_SCRIPT)
    rw, rh = W // 2, H // 2
    out = CLAY if sign > 0 else CLAY.replace(".png", "_flip.png")
    subprocess.run(["blender", "-b", "--python", script, "--",
                    POSE, out, str(rw), str(rh),
                    os.path.join(ROOT, "e30_bridge.blend"), str(W), str(sign)],
                   check=True, capture_output=True)
    return out


def main():
    pose = np.load(POSE)
    M = pose[0:16].reshape(4, 4)
    K = pose[16:25].reshape(3, 3)
    k1 = float(pose[25]) if len(pose) > 25 else 0.0
    im = Image.open(PHOTO)
    W, H = im.size
    gray = np.asarray(im.convert("L"), np.float32)
    arches = detect_arches(gray, 1500, 2350)
    y_water = float(np.median([a["wl"][1] for a in arches]))
    dtf = deck_top_line(gray, W)
    yy = np.arange(H)[:, None]
    stone = (gray > 150) & (yy >= dtf[None, :]) & (yy <= y_water + 8)
    band = (yy >= 1500) & (yy <= 2350)
    voids = (gray < 95) & band
    rw, rh = W // 2, H // 2
    stone_h = cv2.resize((stone * 255).astype(np.uint8), (rw, rh), cv2.INTER_AREA) > 127
    voids_h = cv2.resize((voids * 255).astype(np.uint8), (rw, rh), cv2.INTER_AREA) > 127
    sidecar_dev = {}

    def load_alpha(path):
        """M11-A: 解析内参 warp A = K_opt_half @ K_bl_half^-1 (同机位, 仅内参差);
        K_bl 为 Blender 实测有效内参, 与 K_opt 一并公开。"""
        K_bl = np.load(path + ".Kbl.npy")
        Kh_t = np.array([[K[0, 0] / 2, 0, K[0, 2] / 2], [0, K[1, 1] / 2, K[1, 2] / 2], [0, 0, 1.0]])
        Kh_b = K_bl  # 已是渲染分辨率单位
        A = (Kh_t @ np.linalg.inv(Kh_b))[0:2, :]
        dev = float(np.abs(A[0:2, 0:2] - np.eye(2)).max())
        sidecar_dev[path] = dict(K_bl=K_bl.tolist(), K_opt=K.tolist(),
                                 warp_linear=A[0:2, 0:2].tolist(), t=A[0:2, 2].tolist(),
                                 max_dev_from_identity=round(dev, 5))
        a = np.asarray(Image.open(path).convert("RGBA"), np.float32)[..., 3] > 128
        return cv2.warpAffine((a * 255).astype(np.uint8), A, (rw, rh),
                              flags=cv2.INTER_NEAREST) > 127
    out = render_clay(+1, W, H)
    alpha = load_alpha(out)
    idx = list(range(6 - 1, 6 - 1 + 7))  # 占位, 下方由 report 覆盖
    import json as _j
    reg = _j.load(open(os.path.join(HERE, "cam_register_last.json"))) if os.path.exists(
        os.path.join(HERE, "cam_register_last.json")) else None
    idx = reg["arch_indices"] if reg else list(range(5, 12))
    voids_cl = opening_masks(M, K, rw, rh, idx, k1)
    body_cl = alpha & ~voids_cl

    def ious(alpha_):
        bc = alpha_ & ~voids_cl
        ib = float((stone_h & bc).sum()) / max(1, float((stone_h | bc).sum()))
        iv = float((voids_h & voids_cl).sum()) / max(1, float((voids_h | voids_cl).sum()))
        return ib, iv
    iou_body, iou_void = ious(alpha)
    ca = (alpha ^ ndimage.binary_erosion(alpha))
    cb = (stone_h ^ ndimage.binary_erosion(stone_h))
    da = ndimage.distance_transform_edt(~ca)
    db = ndimage.distance_transform_edt(~cb)
    cham = float((da[cb].mean() + db[ca].mean()) / 2.0) if ca.any() and cb.any() else None
    # deck 驼峰: 模型栏板顶曲线投影 vs 实拍顶线
    xm = np.linspace(-F.BRIDGE_LEN / 2, F.BRIDGE_LEN / 2, 200)
    t = 1.0 - (2.0 * np.abs(xm) / F.BRIDGE_LEN) ** 2
    zm = F.DECK_Z_END + (F.DECK_Z_TOP - F.DECK_Z_END) * t + 0.55
    P = np.array([to_world(x, 0.0, z) for x, z in zip(xm, zm)])
    prj, z = project(P, M, K, k1)
    prj = prj / 2.0
    okp = (prj[:, 0] >= 0) & (prj[:, 0] < rw) & (z > 0)
    px_ = prj[okp, 0].astype(int)
    py_ = prj[okp, 1]
    dth = cv2.resize(dtf[None, :].astype(np.float32), (rw, rh), cv2.INTER_LINEAR)[0]
    samp = dth[px_] / 2.0
    good = ~np.isnan(samp)
    pear = float(np.corrcoef(py_[good], samp[good])[0, 1]) if good.sum() > 20 else None
    rmse_deck = float(np.sqrt(((py_[good] - samp[good]) ** 2).mean())) if good.sum() > 20 else None
    rep = dict(sidecar_similarity_dev=sidecar_dev,
               bridge_body_IoU=round(iou_body, 4), void_IoU=round(iou_void, 4),
               contour_Chamfer_px_halfres=round(cham, 2) if cham else None,
               deck_camber_pearson=round(pear, 4) if pear else None,
               deck_camber_rmse_px_halfres=round(rmse_deck, 2) if rmse_deck else None,
               y_water=y_water, n_detected_arches=len(arches),
               n_registered_arches=len(idx), clay=out)
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    with open(os.path.join(ROOT, "delivery", "26_cam_register_report.json"), "w") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)
    body_cl = alpha & ~voids_cl
    vis = np.zeros((rh, rw, 3), np.uint8)
    vis[stone_h & body_cl] = (255, 255, 255)
    vis[stone_h & ~body_cl] = (255, 60, 60)
    vis[~stone_h & body_cl] = (60, 120, 255)
    Image.fromarray(vis).save(os.path.join(ROOT, "delivery", "27_clay_vs_photo_mask.png"))


if __name__ == "__main__":
    main()
