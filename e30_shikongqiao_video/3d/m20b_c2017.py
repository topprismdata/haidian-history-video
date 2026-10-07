#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""M20b: closer_2017.jpg (D7000 70mm, fpx≈14614, APS-C) 位姿拟合 + 边缘快照精化.
用法:
  guess CX CY CZ AZ EL F     -> 线叠图 m20_ctrl/c2017_guess.jpg (目视调初值)
  solve                      -> 自动快照+PnP 迭代 -> m20_ctrl/m20b_pose_c2017.json
  fitreport                  -> 残差表
坐标约定与 m20_pipeline 一致: y = side*hw(x,z); AZ: 方位角(rad), 视线 = (cos AZ, sin AZ,·).
"""
import json
import math
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from m20_pipeline import Model, load_ctrl, Kmat, project, OUT  # noqa

IMG = os.path.join(HERE, "refs", "balustrade_count", "src", "closer_2017.jpg")
EXIF_FPX = 14614.0   # 70mm APS-C 23.6mm: 70/23.6*4928

model_ = Model(load_ctrl())


def look_at(C, az, el):
    """OpenCV 相机约定: z 轴=视线(指向场景), x=右, y=下. 视线 d=(cos az cos el, sin az cos el, sin el)."""
    d = np.array([math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)])
    zc = d
    up = np.array([0.0, 0.0, 1.0])
    xc = np.cross(zc, up); xc /= np.linalg.norm(xc)
    yc = np.cross(zc, xc)
    R = np.stack([xc, yc, zc], axis=1)  # 列 = 相机轴在世界系
    return R


def pack(C, az, el, f, w, h):
    R = look_at(np.asarray(C, float), az, el)
    rvec, _ = cv2.Rodrigues(R)
    tvec = -R @ np.asarray(C, float)
    return {"image": IMG, "w": w, "h": h, "side": -1, "f": float(f),
            "rvec": rvec.reshape(3).tolist(), "tvec": tvec.reshape(3).tolist(),
            "rms": None, "n": 0}


def render_wire(pose, outfn, arches=range(0, 9)):
    img = cv2.imread(IMG)
    K = Kmat(pose["f"], pose["w"], pose["h"])
    rv = np.array(pose["rvec"]); tv = np.array(pose["tvec"])
    side = int(pose["side"])
    for i in arches:
        xc, spz, a, b = model_.arch(i)
        xs = np.linspace(xc - a, xc + a, 60)
        pts = [tuple(np.array([x, side * model_.hw(float(x), model_.intrados_z(float(x), i)),
                               model_.intrados_z(float(x), i)])) for x in xs]
        uv = project(np.array(pts), K, rv, tv)
        cv2.polylines(img, [uv.astype(np.int32)], False, (0, 255, 255), 2)
        crown = project(np.array([[xc, side * model_.hw(xc, spz + b), spz + b]]), K, rv, tv)[0]
        cv2.putText(img, str(i), (int(crown[0]) - 6, int(crown[1]) - 10), 0, 1.1, (0, 0, 255), 2)
    # 桥面线
    xs = np.linspace(-75, 75, 300)
    pts = [tuple(np.array([x, side * model_.hw(float(x), model_.deck_z(float(x))),
                           model_.deck_z(float(x))])) for x in xs]
    uv = project(np.array(pts), K, rv, tv)
    cv2.polylines(img, [uv.astype(np.int32)], False, (255, 0, 255), 2)
    cv2.imwrite(outfn, img, [cv2.IMWRITE_JPEG_QUALITY, 90])
    print("wrote", outfn)


HALF_WIN = 0.30


def snap_edges(pose, arches, half_win_m=None):
    if half_win_m is None:
        half_win_m = HALF_WIN
    """沿 intrados 法向 ±half_win 搜最强暗边(洞口: 亮墙->暗洞, 负梯度)亚像素.
    返回 [(spec3d, uv_obs)]."""
    img = cv2.imread(IMG)
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    K = Kmat(pose["f"], pose["w"], pose["h"])
    rv = np.array(pose["rvec"]); tv = np.array(pose["tvec"])
    side = int(pose["side"])
    h, w = g.shape
    obs = []
    import facts as F
    for i in arches:
        xc, spz, a, b = model_.arch(i)
        xs = np.linspace(xc - 0.92 * a, xc + 0.92 * a, 33)
        for x in xs:
            zi = model_.intrados_z(float(x), i)
            d = F.arch_dzdx(float(x), xc, spz, a, b)
            Ln = math.hypot(d, 1.0)
            nx, nz = d / Ln, -1.0 / Ln   # 内法向(指向洞内)
            P0 = np.array([x, side * model_.hw(float(x), zi), zi])
            n3 = np.array([nx, 0.0, nz])
            ss = np.arange(-half_win_m, half_win_m + 1e-9, 0.01)
            pts = P0[None, :] + ss[:, None] * n3[None, :]
            uv = project(pts, K, rv, tv)
            ok = (uv[:, 0] >= 1) & (uv[:, 0] < w - 2) & (uv[:, 1] >= 1) & (uv[:, 1] < h - 2)
            if ok.sum() < len(ss) * 0.6:
                continue
            u = uv[:, 0]; v = uv[:, 1]
            u0 = np.floor(u).astype(int); v0 = np.floor(v).astype(int)
            fu = (u - u0).astype(np.float32); fv = (v - v0).astype(np.float32)
            vv = (g[v0, u0] * (1 - fu) * (1 - fv) + g[v0, u0 + 1] * fu * (1 - fv)
                  + g[v0 + 1, u0] * (1 - fu) * fv + g[v0 + 1, u0 + 1] * fu * fv)
            vv[~ok] = np.nan
            fi = np.where(~np.isnan(vv))[0]
            if len(fi) < 3:
                continue
            sm = np.convolve(np.nan_to_num(vv, nan=np.nanmean(vv)), np.ones(5) / 5, "same")
            gr = -np.gradient(sm)   # 暗边 = 负梯度 -> 取 -grad 最大
            j = int(np.nanargmax(np.where(np.isnan(vv), -np.inf, gr)))
            if gr[j] < 8.0:  # 灰度/m, 太弱弃
                continue
            if 0 < j < len(ss) - 1:
                y0, y1, y2 = gr[j - 1], gr[j], gr[j + 1]
                den = y0 - 2 * y1 + y2
                delta = float(np.clip(0.5 * (y0 - y2) / den, -1, 1)) if abs(den) > 1e-9 else 0
            else:
                delta = 0.0
            s_obs = ss[j] + delta * 0.01
            P_obs = P0 + s_obs * n3
            # 对应关系: 模型点 P0 <-> 图像边缘像素 uv_edge (P_obs 的投影).
            # P3 必须给模型点: 让 PnP 把"模型点-边缘"的偏差用相机运动吸收.
            uv_edge = project(P_obs[None, :], K, rv, tv)[0]
            obs.append((P0, uv_edge, i, float(x - xc)))
    return obs


def refine(pose, arches, iters=4, fix_f=None):
    """快照 <-> PnP 交替. fix_f=None 时焦距自由(有界 EXIF±12%)."""
    K0 = None
    for it in range(iters):
        try:
            obs = snap_edges(pose, arches)
        except Exception as e:
            print("iter%d snap 失败: %s" % (it, e)); obs = []; break
        if len(obs) < 12:
            print("iter%d: obs=%d 不足" % (it, len(obs)))
            obs = []; break
        if not obs:
            break
        P3 = np.array([o[0] for o in obs])
        P2 = np.array([o[1] for o in obs])
        if fix_f:
            K = Kmat(fix_f, pose["w"], pose["h"])
            try:
                ok, rv, tv = cv2.solvePnP(P3, P2, K, None, flags=cv2.SOLVEPNP_SQPNP)
                rv, tv = cv2.solvePnPRefineLM(P3, P2, K, None, rv, tv)
            except cv2.error as e:
                print("iter%d PnP 退化: %s" % (it, e)); break
            f_use = fix_f
        else:
            best = (1e9, None, None, None)
            for f in np.geomspace(pose["w"] * 1.5, pose["w"] * 5.5, 60):
                K = Kmat(float(f), pose["w"], pose["h"])
                ok, rv, tv = cv2.solvePnP(P3, P2, K, None, flags=cv2.SOLVEPNP_SQPNP)
                pr = project(P3, K, rv, tv)
                r = float(np.sqrt(np.mean(np.sum((pr - P2) ** 2, 1))))
                if r < best[0]:
                    best = (r, float(f), rv, tv)
            f_use = best[1]
            K = Kmat(f_use, pose["w"], pose["h"])
            rv, tv = cv2.solvePnPRefineLM(P3, P2, K, None, best[2], best[3])
        pr = project(P3, K, rv, tv)
        res = np.sqrt(np.sum((pr - P2) ** 2, 1))
        keep = res < max(3.0, 2.5 * np.median(res))
        rms = float(np.sqrt(np.mean(res[keep] ** 2)))
        print("iter%d: obs=%d kept=%d f=%.1f rms=%.2fpx med=%.2f max=%.1f"
              % (it, len(obs), keep.sum(), f_use, rms, float(np.median(res)), res.max()))
        pose = dict(pose, f=float(f_use), rvec=rv.reshape(3).tolist(),
                    tvec=tv.reshape(3).tolist(), rms=rms, n=int(keep.sum()))
        # 剔外点后重解一次
        P3k, P2k = P3[keep], P2[keep]
        ok, rv, tv = cv2.solvePnP(P3k, P2k, K, None, flags=cv2.SOLVEPNP_SQPNP,
                                  rvec=np.array(pose["rvec"]), tvec=np.array(pose["tvec"]),
                                  useExtrinsicGuess=True)
        rv, tv = cv2.solvePnPRefineLM(P3k, P2k, K, None, rv, tv)
        pr = project(P3k, K, rv, tv)
        res = np.sqrt(np.sum((pr - P2k) ** 2, 1))
        pose = dict(pose, rvec=rv.reshape(3).tolist(), tvec=tv.reshape(3).tolist(),
                    rms=float(np.sqrt(np.mean(res ** 2))), n=int(len(P3k)))
    return pose, obs


def main():
    cmd = sys.argv[1]
    if cmd == "guess":
        C = [float(t) for t in sys.argv[2:5]]
        az, el, f = [float(t) for t in sys.argv[5:8]]
        img = cv2.imread(IMG)
        render_wire(pack(C, az, el, f, img.shape[1], img.shape[0]),
                    os.path.join(OUT, "c2017_guess.jpg"))
    elif cmd == "solve":
        C = [float(t) for t in sys.argv[2:5]]
        az, el, f = [float(t) for t in sys.argv[5:8]]
        img = cv2.imread(IMG)
        pose = pack(C, az, el, f, img.shape[1], img.shape[0])
        pose, obs = refine(pose, list(range(0, 7)))
        render_wire(pose, os.path.join(OUT, "c2017_fit.jpg"))
        with open(os.path.join(OUT, "m20b_pose_c2017.json"), "w") as fp:
            json.dump(pose, fp, indent=1)
        print("saved m20b_pose_c2017.json")
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
