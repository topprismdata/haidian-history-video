# -*- coding: utf-8 -*-
"""M23 水线约束位姿垂直分量修正(主控已批: 检测水线作 z=0 平面约束, 钉死垂直自由度)。

退化机理: m20B 位姿仅拱冠线约束(冠点近共面无垂直基线), 相机沿视线平移+变焦可保持
冠线投影不变——该自由度方向上水线系统性偏 49-56px。
修正: 参数 Δ=(dz, dt, df)(相机世界 z 平移 / 沿视线轴平移 / 焦距缩放), 残差=
[实测水线行 - 预测行(Δ)](强权) + [冠点行(Δ) - 冠点行(0)](锚定, 弱权保持冠线对齐)。
输出: m20_ctrl/m20B_pose_<tag>_wlfit.json + 修正报告。
用法: python3 compare_pack_waterfit.py m20_ctrl/m20B_pose_f175.json f175
"""
import json
import math
import os
import sys

import cv2
import numpy as np
from scipy.optimize import least_squares

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from m20_pipeline import Model, load_ctrl, Kmat, project  # noqa: E402


def rodrigues(rv):
    th = float(np.linalg.norm(rv))
    k = rv / th
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + math.sin(th) * K + (1 - math.cos(th)) * (K @ K)


def measure_waterline(pose, model, img):
    """墩列水线检测(亮度+蓝通道联合梯度, 同 compare_pack_waterline)。返回 [(pier_x, v_meas)]。"""
    K = Kmat(pose["f"], pose["w"], pose["h"])
    rv = np.array(pose["rvec"], np.float64)
    tv = np.array(pose["tvec"], np.float64)
    side = int(pose.get("side", -1))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    blue = img[..., 0].astype(np.float32)
    H, W = img.shape[:2]
    out = []
    for i in range(1, 17):
        p0 = (model.pier_x[i - 1] + model.pier_x[i]) / 2.0
        uv0 = project([(p0, side * model.hw(p0, 0.0), 0.0)], K, rv, tv)[0]
        u, v0 = int(round(uv0[0])), int(round(uv0[1]))
        if u < 30 or u >= W - 30 or v0 < 60 or v0 >= H - 60:
            continue
        lo, hi = max(0, v0 - 60), min(H - 2, v0 + 60)
        gg = np.abs(np.diff(gray[:, u][lo:hi])) + 0.6 * np.abs(np.diff(blue[:, u][lo:hi]))
        if float(gg.max()) < 26.0:
            continue
        out.append((p0, int(np.argmax(gg)) + lo, float(gg.max())))
    return out


def main():
    pose_path, tag = sys.argv[1], sys.argv[2]
    frame = sys.argv[3] if len(sys.argv) > 3 else None
    pose = json.load(open(pose_path))
    model = Model(load_ctrl())
    img = cv2.imread(frame or pose["image"])
    if img is None:
        raise SystemExit("照片读不到: " + str(pose.get("image")))
    measures = measure_waterline(pose, model, img)
    print("WATERLINE measured piers:", [(round(x, 1), v) for x, v, _ in measures])
    if len(measures) < 1:
        raise SystemExit("可测水线不足, 放弃修正")

    side = int(pose.get("side", -1))
    R0 = rodrigues(np.array(pose["rvec"], np.float64))
    t0 = np.array(pose["tvec"], np.float64)
    C0 = -R0.T @ t0
    Rw = np.array(json.load(open(os.path.join(HERE, "out", "compare_pack", "params",
                                               "rw_cache_c_f175_a6.json")))) if os.path.exists(
        os.path.join(HERE, "out", "compare_pack", "params", "rw_cache_c_f175_a6.json")) else None
    if Rw is None:
        root_hint = None  # 模型->世界旋转: 由 bridge_body 已知 -112° 兜底
        th = math.radians(112.0)
        Rw = np.array([[math.cos(-th), -math.sin(-th), 0], [math.sin(-th), math.cos(-th), 0], [0, 0, 1.0]])
    f0 = pose["f"]
    K0 = Kmat(f0, pose["w"], pose["h"])
    axis = (C0 / np.linalg.norm(C0))  # 视线轴近似(沿相机-桥心)

    # 冠点锚(可见拱)
    vis_arch = []
    for i in range(17):
        a = model.arch(i)
        uv = project([(a[0], side * model.hw(a[0], a[2] + a[3]), a[2] + a[3])], K0, rv0, tv0) if False else None
        vis_arch.append(i)

    rv0 = np.array(pose["rvec"], np.float64)
    tv0 = np.array(pose["tvec"], np.float64)
    crowns = []
    for i in range(17):
        a = model.arch(i)
        p3 = [(a[0], side * model.hw(a[0], a[2] + a[3]), a[2] + a[3])]
        uv = project(p3, K0, rv0, tv0)[0]
        if 0 <= uv[0] < pose["w"] and 0 <= uv[1] < pose["h"]:
            crowns.append((i, float(uv[1])))
    print("CROWN anchors:", len(crowns))

    def proj_with(dz, dt, df, pts3d):
        K = Kmat(f0 * df, pose["w"], pose["h"])
        C = C0 + np.array([0.0, 0.0, dz]) - axis * dt
        rv = np.array(R0, np.float64)
        tv = -(R0 @ C)
        return project(pts3d, K, rv, tv)

    def residuals(p):
        dz, dt, df = p
        res = []
        for (x, v_meas, _c) in measures:
            uv = proj_with(dz, dt, df, [(x, side * model.hw(x, 0.0), 0.0)])[0]
            res.append(3.0 * (uv[1] - v_meas))  # 强权
        for (i, v0) in crowns:
            a = model.arch(i)
            uv = proj_with(dz, dt, df, [(a[0], side * model.hw(a[0], a[2] + a[3]), a[2] + a[3])])[0]
            res.append(1.0 * (uv[1] - v0))
        return res

    sol = least_squares(residuals, np.array([0.0, 0.0, 1.0]),
                        bounds=([-6, -25, 0.90], [6, 25, 1.10]))  # df 下界0.90=防过柔(2点3参过拟合), 最小扰动解
    dz, dt, df = sol.x
    res_a = np.array(residuals([0, 0, 1.0]))
    res_b = np.array(residuals(sol.x))
    wl0 = np.abs(res_a[:len(measures)] / 3.0)
    wl1 = np.abs(res_b[:len(measures)] / 3.0)
    print("WLFIT dz=%.3fm dt=%.3fm df=%.4f | waterline |dev| mean %.1f->%.1f px (max %.1f->%.1f)"
          % (dz, dt, df, wl0.mean(), wl1.mean(), wl0.max(), wl1.max()))

    # 应用: 写修正位姿
    K = Kmat(f0 * df, pose["w"], pose["h"])
    C = C0 + np.array([0.0, 0.0, dz]) - axis * dt
    rv = cv2.Rodrigues(np.array(R0, np.float64))[0].reshape(3)
    tv = -(R0 @ C)
    out = dict(pose)
    out["rvec"] = rv.tolist()
    out["tvec"] = tv.reshape(3).tolist()
    out["f"] = float(f0 * df)
    out["rms"] = float(pose.get("rms", 5.2))
    out["wlfit"] = dict(dz=round(float(dz), 3), dt=round(float(dt), 3), df=round(float(df), 5),
                        waterline_mean_px=round(float(wl1.mean()), 1),
                        waterline_mean_before_px=round(float(wl0.mean()), 1),
                        measured_piers=[[round(x, 2), v] for x, v, _ in measures],
                        note="水线 z=0 平面约束钉垂直自由度(主控已批); 冠点行锚定保持")
    dst = pose_path.replace(".json", "_wlfit.json")
    json.dump(out, open(dst, "w"), ensure_ascii=False, indent=1)
    print("WLFIT_SAVED", dst)


if __name__ == "__main__":
    main()
