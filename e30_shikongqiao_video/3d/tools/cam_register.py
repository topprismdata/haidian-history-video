# -*- coding: utf-8 -*-
"""黄金基准相机注册协议(六审 §8 工程实现)。

日间实拍(默认 refs/balustrade_count/src/img_0439.jpg, Canon 400D 85mm, EXIF 已验):
  1. 半自动 landmark: 暗拱腔连通域 -> 每拱 3 点(拱冠顶/左水面脚/右水面脚);
  2. 序列对齐: 检出拱宽归一序列 vs 模型 span 序列, 平移匹配定拱号;
  3. 位姿: look-at 参数化(theta,phi,D,tz,roll) 多初值 LM —— 控制点共面,
     常规 PnP 有平面歧义, 故用物理先验(相机在水面上 0.2m+ / |pitch|,|roll| 小)
     的多初值优化取代; 近面(y=±7.3)二次解算取优;
  4. 模型 3D: 场景冻结 yaw=-1.9547687768936157(blend 实测), 本地 X=桥轴;
     facts.SPRINGER=2.5 起拱, 半圆券 rise=span/2, 水面 z=0;
  5. headline: similarity_landmarks = 1 - mean_norm_reproj_err, 预定义 >=0.95 为 PASS;
     逐拱孔心误差分项; clay 同机位比对见 cam_clay_compare.py。
"""
import json
import os
import sys

import numpy as np

try:  # Blender 内置 Python 无 scipy: 几何函数仍可用
    from scipy import ndimage
    from scipy.optimize import least_squares
except ImportError:  # pragma: no cover
    ndimage = None
    least_squares = None

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import facts as F  # noqa: E402

VOID_EXP = [(0.0259, 0.03), (0.072, 0.0327), (0.123, 0.036), (0.1773, 0.0393),
            (0.235, 0.0427), (0.296, 0.046), (0.3603, 0.0493), (0.4283, 0.0533),
            (0.5, 0.0567), (0.5717, 0.0533), (0.6397, 0.0493), (0.704, 0.046),
            (0.765, 0.0427), (0.8227, 0.0393), (0.877, 0.036), (0.928, 0.0327),
            (0.9741, 0.03)]
XC_M = np.array([(c - 0.5) * F.BRIDGE_LEN for c, _ in VOID_EXP])
SPAN_M = np.array([w * F.BRIDGE_LEN for _, w in VOID_EXP])
Z_SPRING = F.SPRINGER
Z_WATER = 0.0

# 场景冻结变换(blend 实测 2026-10-05): bridge_body 世界 yaw, 本地 X=桥轴, 本地 Y=宽±7.3
YAW = -1.9547687768936157
RZ = np.array([[np.cos(YAW), -np.sin(YAW), 0.0],
               [np.sin(YAW), np.cos(YAW), 0.0],
               [0.0, 0.0, 1.0]])
HALF_W = 7.3


def to_world(u, y_face, v):
    return RZ @ np.array([u, y_face, v])


def model_pts(i, y_face=0.0):
    xc, sp = XC_M[i], SPAN_M[i]
    return np.array([
        to_world(xc, y_face, Z_SPRING + sp / 2.0),
        to_world(xc - sp / 2.0, y_face, Z_WATER),
        to_world(xc + sp / 2.0, y_face, Z_WATER)], float)


def look_at(C, target, roll=0.0):
    f = target - C
    f = f / np.linalg.norm(f)
    r = np.cross(f, np.array([0.0, 0.0, 1.0]))
    n = np.linalg.norm(r)
    r = r / n if n > 1e-6 else np.array([1.0, 0.0, 0.0])
    u = np.cross(r, f)
    Rcam = np.stack([r, u, -f], axis=1)
    if roll:
        cr, sr = np.cos(roll), np.sin(roll)
        Rcam = Rcam @ np.array([[cr, -sr, 0.0], [sr, cr, 0.0], [0.0, 0.0, 1.0]])
    M = np.eye(4)
    M[0:3, 0:3] = Rcam
    M[0:3, 3] = C
    return M


def project(pts3, M, K, k1=0.0):
    """针孔 + 可选径向畸变 x' = x(1 + k1 r^2), r 为归一化像半径(M11-A)。"""
    X = (np.linalg.inv(M) @ np.hstack([pts3, np.ones((len(pts3), 1))]).T).T
    d = -X[:, 2]  # Blender 相机 -Z 前视
    xn = X[:, 0] / d
    yn = X[:, 1] / d
    if k1:
        r2 = xn * xn + yn * yn
        w = 1.0 + k1 * r2
        xn = xn * w
        yn = yn * w
    px = xn * K[0, 0] + K[0, 2]
    py = K[1, 2] - yn * K[1, 1]
    return np.stack([px, py], 1), d


def solve_pose(pts3, pts2, K, wmask=None, is_water=None):
    """wmask: (N,2) 残差权重(x,y 分项); 水位降 wl_off 为照片环境 nuisance 参数。

    landmark 平面语义(斜视实拍): 暗腔顶 = 远面拱冠(筒腹silhouette上缘);
    暗腔左右缘 = 近面开口边 -> 水面点只取 x 残差(wmask y=0)。
    """
    tgt0 = np.array([0.0, 0.0, 4.0])
    if is_water is None:
        is_water = np.zeros(len(pts3), bool)
    if wmask is None:
        wmask = np.ones((len(pts3), 2))

    def resid(p):
        th, ph, D, tz, roll, wl_off, cx, cy, fs, k1 = p
        KK = K.copy()
        KK[0, 0:2] *= fs          # focal_scale nuisance(裁切/缩放混杂, 先验±3%)
        KK[1, 1] *= fs
        KK[0, 2] += cx
        KK[1, 2] += cy
        P3 = pts3.copy()
        P3[is_water, 2] -= wl_off
        C = tgt0 + np.array([D * np.cos(th) * np.cos(ph),
                             D * np.sin(th) * np.cos(ph),
                             D * np.sin(ph)])
        C[2] = max(0.2, C[2])
        M = look_at(C, tgt0 + np.array([0.0, 0.0, tz]), roll)
        pr, z = project(P3, M, KK, k1)
        if (z <= 0).any():
            return np.full(pts2.size, 1e4)
        return ((pr - pts2) * wmask).ravel()

    best = None
    for th in np.arange(0, 2 * np.pi, np.pi / 12):
        for ph in (0.01, 0.10, 0.25):
            for D in (160.0, 260.0):
                r = least_squares(resid, [th, ph, D, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0],
                                  bounds=([th - 0.3, -0.35, 60.0, -6.0, -0.2, 0.0, -58.0, -39.0, 0.97, -0.05],
                                          [th + 0.3, 0.35, 900.0, 6.0, 0.2, 4.0, 58.0, 39.0, 1.03, 0.05]))
                if best is None or r.cost < best.cost:
                    best = r
    th, ph, D, tz, roll, wl_off, cx, cy, fs, k1 = best.x
    C = tgt0 + np.array([D * np.cos(th) * np.cos(ph),
                         D * np.sin(th) * np.cos(ph),
                         D * np.sin(ph)])
    C[2] = max(0.2, C[2])
    M = look_at(C, tgt0 + np.array([0.0, 0.0, tz]), roll)
    Kopt = K.copy()
    Kopt[0, 0:2] *= fs
    Kopt[1, 1] *= fs
    Kopt[0, 2] += cx
    Kopt[1, 2] += cy
    return M, float(best.cost), float(wl_off), Kopt, float(k1)


def detect_arches(gray, y0, y1, thr=95):
    band = gray[y0:y1, :]
    dark = ndimage.binary_opening(band < thr, np.ones((5, 5)))
    lab, n = ndimage.label(dark)
    out = []
    H, W = band.shape
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        h = sl[0].stop - sl[0].start
        w = sl[1].stop - sl[1].start
        area = int((lab[sl] == i).sum())
        if h < 0.30 * H or w < 60 or area < 0.45 * w * h:
            continue
        m = (lab[sl] == i)
        rows = np.where(m.any(axis=1))[0]
        crown_y = sl[0].start + rows[0] + y0
        top_slice = m[rows[0]:rows[0] + 6]
        crown_x = sl[1].start + float(np.mean(np.where(top_slice.any(axis=0))[0]))
        bot = sl[0].stop - 1 + y0
        out.append(dict(crown=(crown_x, float(crown_y)),
                        wl=(float(sl[1].start), float(bot)),
                        wr=(float(sl[1].stop - 1), float(bot)),
                        w=w, h=h, area=area))
    out.sort(key=lambda d: d["crown"][0])
    return out


def align_shift(widths_photo, widths_model):
    wp = np.asarray(widths_photo, float)
    wp = wp / wp.sum()
    best, bs = -2.0, 0
    n = len(wp)
    for s in range(0, len(widths_model) - n + 1):
        wm = np.asarray(widths_model[s:s + n], float)
        wm = wm / wm.sum()
        c = float(np.corrcoef(wp, wm)[0, 1])
        if c > best:
            best, bs = c, s
    return bs, best


def main(photo="refs/balustrade_count/src/img_0439.jpg", y0=1500, y1=2350):
    from PIL import Image
    path = os.path.join(ROOT, photo)
    im = Image.open(path)
    W, H = im.size
    gray = np.asarray(im.convert("L"), np.float32)
    ex = im.getexif()
    ifd = ex.get_ifd(0x8769)
    fl_mm = float(ifd.get(0x920A) or ex.get(0x920A))
    native_w = 3888.0
    sensor_w = 22.2
    f_px = fl_mm * native_w / sensor_w
    K = np.array([[f_px, 0.0, W / 2.0], [0.0, f_px, H / 2.0], [0.0, 0.0, 1.0]])

    arches0 = detect_arches(gray, int(y0), int(y1))
    wm = np.median([a["w"] for a in arches0])
    arches = [a for a in arches0 if a["w"] >= 0.5 * wm]  # 剔裁切半拱(冠顶不可观)
    rep = {"photo": photo, "size": [W, H], "focal_mm": fl_mm, "f_px": round(f_px, 1),
           "n_detected": len(arches0), "n_used": len(arches)}
    if len(arches) < 6:
        rep["verdict"] = "DETECTION_FAIL"
        print(json.dumps(rep, ensure_ascii=False))
        return rep
    # 宽峰定 shift: 检出最宽拱 = 模型主孔 idx8
    k_peak = int(np.argmax([a["w"] for a in arches]))
    shift = 8 - k_peak
    corr = float(np.corrcoef(np.asarray([a["w"] for a in arches], float) /
                             np.sum([a["w"] for a in arches]),
                             SPAN_M[shift:shift + len(arches)] /
                             np.sum(SPAN_M[shift:shift + len(arches)]))[0, 1])
    rep["align_shift"] = shift
    rep["align_corr"] = round(corr, 4)
    idx = list(range(shift, shift + len(arches)))
    # 全近面 landmark( silhouette 边 = 近面开口边 ); shift 由 RMSE 扫描选优
    best = None
    for sh in range(3, 11):
        idx_t = list(range(sh, sh + len(arches)))
        if idx_t[-1] > 16:
            continue
        p3, p2 = [], []
        for k, a in enumerate(arches):
            P = model_pts(idx_t[k], -HALF_W)
            p3 += [P[0], P[1], P[2]]
            p2 += [a["crown"], a["wl"], a["wr"]]
        Mt, ct, wt, Kt, k1t = solve_pose(np.array(p3), np.array(p2, float), K.copy(),
                                         np.ones((len(p3), 2)),
                                         np.array([j % 3 != 0 for j in range(len(p3))]))
        prt, _ = project(np.array(p3), Mt, Kt, k1t)
        et = prt - np.array(p2, float)
        rt = float(np.sqrt((et ** 2).sum(1).mean()))
        if best is None or rt < best[0]:
            best = (rt, sh, Mt, wt, idx_t, np.array(p3), np.array(p2, float), Kt, k1t)
    rmse0, shift, M, wl_off, idx, pts3, pts2, Kopt, k1 = best
    corr = float(np.corrcoef(np.asarray([a["w"] for a in arches], float) /
                             np.sum([a["w"] for a in arches]),
                             SPAN_M[shift:shift + len(arches)] /
                             np.sum(SPAN_M[shift:shift + len(arches)]))[0, 1])
    rep["align_shift"] = shift
    rep["align_corr"] = round(corr, 4)
    proj, z = project(pts3, M, Kopt, k1)
    err = proj - pts2
    rmse_px = float(np.sqrt((err ** 2).sum(axis=1).mean()))
    norm_err = np.sqrt((err ** 2).sum(axis=1)) / np.hypot(W, H)
    sim = 1.0 - float(norm_err.mean())
    per = [round(float(np.hypot(*(proj[3 * k] - np.array(arches[k]["crown"]))) / W * 100), 3)
           for k in range(len(arches))]
    rep.update(cam_matrix=M.ravel().tolist(),
               reproj_rmse_px=round(rmse_px, 2),
               mean_norm_err=round(float(norm_err.mean()), 5),
               similarity_landmarks=round(sim, 4),
               crown_err_pctW=per,
               face_sign=-1.0,
               lake_drop_m=round(wl_off, 2),
               k1_radial=round(k1, 5),
               K_opt=Kopt.ravel().tolist(),
               arch_indices=idx,
               caveat="残差结构化(拱形窄高/跨距工作值 vs 实拍): 见 delivery/26 报告; >=95% photo-geometric 不认证")
    rep["verdict"] = "PASS" if sim >= 0.95 else "BELOW_TARGET"
    np.save(os.path.join(HERE, "cam_pose_img0439.npy"),
            np.concatenate([M.ravel(), Kopt.ravel(), [k1]]))
    with open(os.path.join(HERE, "cam_register_last.json"), "w") as fj:
        json.dump(rep, fj, ensure_ascii=False, indent=1)
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    return rep


if __name__ == "__main__":
    main(*sys.argv[1:])
