# -*- coding: utf-8 -*-
"""M23 全幅拱腹线+预测水线 叠加(主控裁定: 模型 z 原点=水面, 位姿即投影)。

对每孔: 模型预测拱腹曲线(冠->起拱线) + 孔侧墩边线(起拱线->水面) 全 Extent 画到照片;
z=0 水面交线全桥横贯。水线偏差数值: 逐墩列在预测线 ±窗内找照片最大竖向梯度 = 真实水线,
有符号偏差(px) 报告; 过曝/不可判列如实标 nd。
用法: python3 compare_pack_waterline.py <pose_json> <stones-free> <photo> <out> [tag]
"""
import json
import math
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from m20_pipeline import Model, load_ctrl, Kmat, project  # noqa: E402


def main():
    pose_path, photo_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    tag = sys.argv[4] if len(sys.argv) > 4 else "tag"
    pose = json.load(open(pose_path))
    model = Model(load_ctrl())
    side = int(pose.get("side", -1))
    K = Kmat(pose["f"], pose["w"], pose["h"])
    rv = np.array(pose["rvec"], np.float64)
    tv = np.array(pose["tvec"], np.float64)
    img = cv2.imread(photo_path)
    H, W = img.shape[:2]
    vis = img.copy()

    def proj(pts):
        return project(np.array(pts), K, rv, tv)

    def draw(pts, color, th=2):
        uv = proj(pts)
        ok = (uv[:, 0] >= 0) & (uv[:, 0] < W) & (uv[:, 1] >= 0) & (uv[:, 1] < H)
        if ok.sum() >= 2:
            cv2.polylines(vis, [np.round(uv[ok]).astype(np.int32)], False, color, th, cv2.LINE_AA)
        return uv

    # 1) 全幅拱腹线 + 孔侧墩边线(到水面)
    for i in range(17):
        a = model.arches[i]
        pts = []
        for t in np.linspace(-1, 1, 60):
            x = a["xc"] + t * a["a"]
            pts.append((x, side * model.hw(x, model.intrados_z(x, i)), model.intrados_z(x, i)))
        draw(pts, (0, 255, 255), 2)  # 黄: 拱腹
        for xb in (a["bay_x0"], a["bay_x1"]):
            zs = np.linspace(model.intrados_z(a["xc"] + (1 if xb > a["xc"] else -1) * a["a"] * 0.999, i), 0.0, 20)
            draw([(xb, side * model.hw(xb, z), z) for z in zs], (255, 0, 255), 2)  # 品红: 墩边线(暖底上可读)
    # 2) 预测水线 z=0
    xs = np.linspace(-75, 75, 300)
    uv_wl = proj([(x, side * model.hw(x, 0.0), 0.0) for x in xs])
    ok = (uv_wl[:, 0] >= 0) & (uv_wl[:, 0] < W) & (uv_wl[:, 1] >= 0) & (uv_wl[:, 1] < H)
    cv2.polylines(vis, [np.round(uv_wl[ok]).astype(np.int32)], False, (255, 255, 0), 2, cv2.LINE_AA)

    # 3) 水线偏差: 墩中心列 ±60px 窗内找 暖石->水 的边(亮度差+蓝通道差联合, 过曝稳妥)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    blue = img[..., 0].astype(np.float32)
    dev_rows = []
    for i in range(1, 17):
        p0 = (model.pier_x[i - 1] + model.pier_x[i]) / 2.0
        uv0 = proj([(p0, side * model.hw(p0, 0.0), 0.0)])[0]
        u, v0 = int(round(uv0[0])), int(round(uv0[1]))
        if u < 30 or u >= W - 30 or v0 < 60 or v0 >= H - 60:
            dev_rows.append(dict(pier=i, verdict="nd_out_of_frame"))
            continue
        colg = gray[:, u]
        colb = blue[:, u]
        lo, hi = max(0, v0 - 60), min(H - 2, v0 + 60)
        gg = np.abs(np.diff(colg[lo:hi])) + 0.6 * np.abs(np.diff(colb[lo:hi]))
        v_meas = int(np.argmax(gg)) + lo
        contrast = float(gg.max())
        if contrast < 26.0:
            dev_rows.append(dict(pier=i, verdict="nd_low_contrast", contrast=round(contrast, 1)))
            continue
        dev_rows.append(dict(pier=i, v_pred=v0, v_meas=v_meas,
                             dev_px=int(v_meas - v0), contrast=round(contrast, 1)))
    devs = [r["dev_px"] for r in dev_rows if "dev_px" in r]
    summary = dict(tag=tag, pier_waterline_dev=dict(
        rows=dev_rows, n_measured=len(devs),
        dev_mean_px=round(float(np.mean(devs)), 1) if devs else None,
        dev_abs_max_px=round(float(np.max(np.abs(devs))), 1) if devs else None,
        note="dev>0=预测线高于实测水线(照片v向下); 模型 z0=水面(M19 冬照基准)"))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    cv2.imwrite(out_path, vis, [cv2.IMWRITE_JPEG_QUALITY, 90])
    json.dump(summary, open(out_path.replace(".jpg", "_summary.json"), "w"), ensure_ascii=False, indent=1)
    print("WATERLINE_DONE", tag, "mean_dev", summary["pier_waterline_dev"]["dev_mean_px"],
          "absmax", summary["pier_waterline_dev"]["dev_abs_max_px"])


if __name__ == "__main__":
    main()
