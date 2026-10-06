#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""M20 逐孔砖谱试点管线(中央 3 孔 A07/A08/A09).

链路: 控制点对应(corr JSON) -> cv2.solvePnP 位姿(焦距扫描) -> (x,z) 正射投影
-> 0.5m 网格叠加 -> Canny+Hough 缝线初稿 -> 人工描摹(网格读数) -> stones_pX.json
-> 缝线叠图 + 逐块边界核对表.

坐标约定: x=桥轴(m, 封版 PIER_X 系), z=水面起算高(m, M19 冬照重标定基准),
y=水平垂直于桥轴(南/北脸 = ±hw(x,z), hw 为 22° 收分墙面半宽)。
相机: 针孔, 主点=图心, 零畸变; 焦距未知 -> 对数扫描取重投影 RMS 最小。

用法:
  python3 m20_pipeline.py pose  m20_ctrl/corr_2017.json
  python3 m20_pipeline.py ortho 2017
  python3 m20_pipeline.py detect 2017
  python3 m20_pipeline.py wire  2017 stones/stones_p8.json
  python3 m20_pipeline.py check 2017 stones/stones_p8.json
"""
import json
import math
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import facts as F  # noqa: E402  封版单一来源(arch_z/arch_dzdx 纯数学)

CTRL = os.path.join(HERE, "m20_ctrl", "model_ctrl.json")
OUT = os.path.join(HERE, "m20_ctrl")


# ── 模型几何(消费 m20_export_ctrl.py 导出的封版值) ──
def load_ctrl():
    with open(CTRL) as f:
        return json.load(f)


class Model:
    def __init__(self, ctrl):
        c = ctrl["constants"]
        self.c = c
        self.L = c["BRIDGE_LEN"]
        self.half = self.L / 2.0
        self.k = (c["DECK_Z_TOP"] - c["DECK_Z_END"]) / (self.half * self.half)
        self.pier_x = ctrl["PIER_X"]
        self.arches = {int(k): v for k, v in ctrl["arches"].items()}
        self.pier_w = {int(k): v for k, v in ctrl["pier_w"].items()}
        self.vtarget = ctrl["VOUSSOIR_TARGET"]

    def deck_z(self, x):
        ax = np.minimum(np.abs(x), self.half)
        return self.c["DECK_Z_TOP"] - self.k * ax * ax

    def hw(self, x, z):
        """墙面半宽(22° 收分): masonry._hw 同式。"""
        xc = np.clip(x, -self.half, self.half)   # np2 兼容(旧 min/max 链对 ndarray 失效)
        deck = self.deck_z(xc)
        f = np.clip((z - self.c["BODY_BOTTOM"]) / (deck - self.c["BODY_BOTTOM"]), 0.0, 1.0)
        return (self.c["DECK_DOWN_W"] + (self.c["DECK_UP_W"] - self.c["DECK_DOWN_W"]) * f) / 2.0

    def arch(self, i):
        a = self.arches[i]
        return a["xc"], a["spz"], a["a"], a["b"]

    def intrados_z(self, x, i):
        xc, spz, a, b = self.arch(i)
        return F.arch_z(x, xc, spz, a, b)

    def extrados_z(self, x, i):
        """intrados 沿外法向偏 RING_T 后的 z(x)(贴拱切割线)。"""
        xc, spz, a, b = self.arch(i)
        d = F.arch_dzdx(x, xc, spz, a, b)
        Ln = math.hypot(d, 1.0)
        return self.intrados_z(x, i) + self.c["RING_T"] / Ln

    def ctrl3d(self, spec, side):
        """控制点语义 -> 3D。spec: {x, z} 或 {arch, t, x_rel}。
        y = side*(hw(x,z) + yoff), yoff 默认 0(券脸 FACE_PROUD=4mm 忽略)。"""
        if "arch" in spec:
            i = spec["arch"]
            xc, spz, a, b = self.arch(i)
            t = spec.get("t", "intrados")
            xr = spec.get("x_rel", 0.0)
            x = xc + xr
            if t == "intrados":
                z = self.intrados_z(x, i)
            elif t == "extrados":
                z = self.extrados_z(x, i)
            elif t == "springer":
                x = xc + (a if xr > 0 else -a)
                z = spz
            elif t == "crown":
                x, z = xc, spz + b
            elif t == "deck":
                z = self.deck_z(x) - 0.10
            else:
                raise ValueError(t)
        else:
            x, z = float(spec["x"]), float(spec["z"])
        return (float(x), side * self.hw(x, z), float(z))


# ── 相机与位姿 ──
def Kmat(f, w, h):
    return np.array([[f, 0, w / 2.0], [0, f, h / 2.0], [0, 0, 1.0]], np.float64)


def project(pts3d, K, rvec, tvec):
    p, _ = cv2.projectPoints(np.asarray(pts3d, np.float64), rvec, tvec, K, None)
    return p.reshape(-1, 2)


def solve_pose(corr, model, verbose=True):
    """焦距对数扫描 + SQPNP; 返回 pose dict。corr.points: [{spec,u,v},...]"""
    img = cv2.imread(corr["image"])
    h, w = img.shape[:2]
    side = int(corr.get("side", 1))
    pts3d = np.array([model.ctrl3d(p["spec"], side) for p in corr["points"]], np.float64)
    pts2d = np.array([[p["u"], p["v"]] for p in corr["points"]], np.float64)

    def rms_for(f):
        K = Kmat(f, w, h)
        ok, rv, tv = cv2.solvePnP(pts3d, pts2d, K, None, flags=cv2.SOLVEPNP_SQPNP)
        if not ok:
            return 1e9, None, None
        pr = project(pts3d, K, rv, tv)
        return float(np.sqrt(np.mean(np.sum((pr - pts2d) ** 2, 1)))), rv, tv

    best = (1e9, None, None, None)
    for f in np.geomspace(0.25 * w, 8.0 * w, 80):
        r = rms_for(float(f))
        if r[0] < best[0]:
            best = (r[0], float(f), r[1], r[2])
    # 细扫描
    f0 = best[1]
    for f in np.linspace(f0 * 0.97, f0 * 1.03, 61):
        r = rms_for(float(f))
        if r[0] < best[0]:
            best = (r[0], float(f), r[1], r[2])
    rms, f, rv, tv = best
    # LM 精化(位姿)
    K = Kmat(f, w, h)
    rv, tv = cv2.solvePnPRefineLM(pts3d, pts2d, K, None, rv, tv)
    pr = project(pts3d, K, rv, tv)
    res = np.sum((pr - pts2d) ** 2, 1) ** 0.5
    rms = float(np.sqrt(np.mean(res ** 2)))
    if verbose:
        print("pose side=%+d f=%.1fpx (%.1fmm eq) RMS=%.2fpx max=%.2fpx n=%d"
              % (side, f, f * 36.0 / w, rms, res.max(), len(pts2d)))
        for p, r, q in zip(corr["points"], res, pr):
            print("  %-14s res=%5.2fpx  proj=(%7.1f,%7.1f) obs=(%7.1f,%7.1f)"
                  % (p.get("id", "?"), r, q[0], q[1], p["u"], p["v"]))
    return {"image": corr["image"], "w": w, "h": h, "side": side, "f": f,
            "rvec": rv.reshape(3).tolist(), "tvec": tv.reshape(3).tolist(),
            "rms": rms, "res": res.tolist(), "n": len(pts2d)}


def load_pose(tag):
    with open(os.path.join(OUT, "pose_%s.json" % tag)) as f:
        p = json.load(f)
    return p


def pose_arr(p):
    return (np.array(p["rvec"], np.float64), np.array(p["tvec"], np.float64),
            Kmat(p["f"], p["w"], p["h"]))


# ── 正射 ──
def ortho_rectify(model, pose, i, ppm=80.0, margin=2.0, ztop=None, tag=None):
    """把帧重采样到第 i 孔 (x,z) 立面。返回 (ortho, grid, qual, extent)。"""
    rv, tv, K = pose_arr(pose)
    img = cv2.imread(pose["image"])
    a = model.arches[i]
    x0, x1 = a["xc"] - a["a"] - margin, a["xc"] + a["a"] + margin
    z1 = ztop if ztop else model.deck_z(a["xc"]) + 0.45
    z0 = 0.0
    W = int(round((x1 - x0) * ppm)); H = int(round((z1 - z0) * ppm))
    xs = x0 + (np.arange(W) + 0.5) / ppm
    zs = z1 - (np.arange(H) + 0.5) / ppm
    side = int(pose["side"])
    # 采样点 3D: 墙面(凸出砧石 8mm 忽略) -> 像素
    P = np.empty((H, W, 3), np.float64)
    P[..., 0] = xs[None, :]
    P[..., 2] = zs[:, None]
    P[..., 1] = side * model.hw(P[..., 0], P[..., 2])
    p = P.reshape(-1, 3)
    uv = project(p, K, rv, tv).reshape(H, W, 2)
    valid = np.ones((H, W), bool)
    # 重采样(双线性, 手写保持 3.9 兼容与越界处理)
    u = uv[..., 0]; v = uv[..., 1]
    valid &= (u >= 0) & (u <= pose["w"] - 2) & (v >= 0) & (v <= pose["h"] - 2)
    u0 = np.floor(u).astype(int); v0 = np.floor(v).astype(int)
    u0c = np.clip(u0, 0, pose["w"] - 2); v0c = np.clip(v0, 0, pose["h"] - 2)
    fu = u - u0c; fv = v - v0c
    out = np.zeros((H, W, 3), np.float32)
    for c in range(3):
        ch = img[..., c].astype(np.float32)
        out[..., c] = (ch[v0c, u0c] * (1 - fu) * (1 - fv) + ch[v0c, u0c + 1] * fu * (1 - fv)
                       + ch[v0c + 1, u0c] * (1 - fu) * fv + ch[v0c + 1, u0c + 1] * fu * fv)
    out[~valid] = 0.25 * out[~valid]  # 越界压暗
    # 每像素地面采样步长(m/源px) -> 质量图(亮=分辨率好)
    eps = 0.05
    p2 = p.copy(); p2[:, 0] += eps
    du = np.linalg.norm(project(p2, K, rv, tv) - project(p, K, rv, tv), axis=1) / eps
    dstep = np.clip((1.0 / np.maximum(du, 1e-6)) / 0.10, 0, 1)  # 0.10 m/px 为 0
    qual = (np.clip(1.0 - dstep, 0, 1) * 255).astype(np.uint8).reshape(H, W)
    qual[~valid.reshape(H, W)] = 0
    ortho = out.astype(np.uint8)
    ext = (x0, x1, z0, z1, ppm)
    if tag:
        cv2.imwrite(os.path.join(OUT, "ortho_%s.png" % tag), ortho)
        cv2.imwrite(os.path.join(OUT, "ortho_%s_q.png" % tag), qual)
        grid = draw_grid(model, ortho, ext, i)
        cv2.imwrite(os.path.join(OUT, "ortho_%s_g.png" % tag), grid)
    return ortho, ext, qual


def xz_to_px(ext, x, z):
    x0, x1, z0, z1, ppm = ext
    return (x - x0) * ppm, (z1 - z) * ppm


def draw_grid(model, img, ext, arch_i=None, step=0.5):
    """0.5m 网格 + 模型特征线(孔 intrados/extrados/墩面/桥面底)。"""
    im = img.copy()
    x0, x1, z0, z1, ppm = ext
    H, W = im.shape[:2]
    g = (70, 70, 70); g1 = (110, 110, 110)
    xx = math.ceil(x0 / step) * step
    while xx <= x1:
        u, _ = xz_to_px(ext, xx, 0)
        c = g1 if abs(xx % 1.0) < 1e-6 else g
        cv2.line(im, (int(u), 0), (int(u), H - 1), c, 1)
        if abs(xx % 1.0) < 1e-6:
            cv2.putText(im, "%.0f" % xx, (int(u) + 2, 14), 0, 0.38, (255, 255, 0), 1)
        xx += step
    zz = math.ceil(z0 / step) * step
    while zz <= z1:
        _, v = xz_to_px(ext, 0, zz)
        c = g1 if abs(zz % 1.0) < 1e-6 else g
        cv2.line(im, (0, int(v)), (W - 1, int(v)), c, 1)
        if abs(zz % 1.0) < 1e-6:
            cv2.putText(im, "%.0f" % zz, (3, int(v) - 3), 0, 0.38, (255, 255, 0), 1)
        zz += step
    if arch_i is not None:
        ys = np.linspace(max(x0, -90), min(x1, 90), 400)
        feat = [(model.intrados_z, (0, 215, 255)), (model.extrados_z, (0, 160, 255))]
        for fn, col in feat:
            pts = []
            for x in ys:
                try:
                    z = fn(float(x), arch_i)
                except Exception:
                    continue
                if z0 - 0.2 <= z <= z1:
                    u, v = xz_to_px(ext, x, z)
                    pts.append((int(u), int(v)))
            if len(pts) > 2:
                cv2.polylines(im, [np.array(pts)], False, col, 1, cv2.LINE_AA)
        for bx in (model.arches[arch_i]["bay_x0"], model.arches[arch_i]["bay_x1"]):
            if x0 <= bx <= x1:
                u, _ = xz_to_px(ext, bx, 0)
                cv2.line(im, (int(u), 0), (int(u), H - 1), (0, 215, 255), 1)
        deck = [(x, model.deck_z(x) - 0.10) for x in ys]
        pts = [tuple(int(t) for t in xz_to_px(ext, x, z)) for x, z in deck
               if z0 <= z <= z1]
        if len(pts) > 2:
            cv2.polylines(im, [np.array(pts)], False, (180, 0, 255), 1, cv2.LINE_AA)
    return im


# ── 缝线检测(初稿) ──
def detect_seams(tag, ppm=None):
    """正射图 Canny+Hough: 水平层缝/竖直块缝候选, 写 detect_<tag>.png。"""
    path = os.path.join(OUT, "ortho_%s.png" % tag)
    img = cv2.imread(path)
    ext = load_ext(tag)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(2.0, (8, 8))
    g = clahe.apply(gray)
    edges = cv2.Canny(g, 28, 90)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=48,
                            minLineLength=int(1.2 * ppm_eff(ext)),
                            maxLineGap=4)
    out = img.copy()
    rows = []
    if lines is not None:
        for l in lines[:, 0]:
            x1, y1, x2, y2 = [int(v) for v in l]
            ang = math.degrees(math.atan2(y2 - y1, x2 - x1)) % 180
            ln = math.hypot(x2 - x1, y2 - y1)
            if ang < 8 or ang > 172:
                rows.append((y1 + y2) / 2.0)
                cv2.line(out, (x1, y1), (x2, y2), (0, 255, 0), 1)
            elif 80 < ang < 100:
                cv2.line(out, (x1, y1), (x2, y2), (0, 128, 255), 1)
    cv2.imwrite(os.path.join(OUT, "detect_%s.png" % tag), out)
    print("detect_%s: %d hough lines" % (tag, 0 if lines is None else len(lines)))
    return out


def ppm_eff(ext):
    return ext[4]


def load_ext(tag):
    """ortho extent 复原(由 pose+ctrl 重算)。"""
    tag0 = tag.split("_")[0]
    pose = load_pose(tag0)
    model = Model(load_ctrl())
    i = int(tag.split("_")[1]) if "_" in tag else None
    if i is None:
        raise SystemExit("tag 须为 <pose>_<arch>")
    a = model.arches[i]
    x0, x1 = a["xc"] - a["a"] - 2.0, a["xc"] + a["a"] + 2.0
    z1 = model.deck_z(a["xc"]) + 0.45
    return (x0, x1, 0.0, z1, 80.0)


# ── 描摹 JSON -> 叠图/核对 ──
def load_stones(path):
    with open(path) as f:
        return json.load(f)


def wire_overlay(model, pose, stones, i, tag, ppm=80.0):
    """照片 + 描摹缝线(青=cyan) + 照片检测缝(红) 叠图。"""
    ortho, ext, _ = ortho_rectify(model, pose, i, ppm=ppm)
    out = ortho.copy()
    x0, x1, z0, z1, _ = ext
    bay0, bay1 = model.arches[i]["bay_x0"], model.arches[i]["bay_x1"]
    deck_top = max(model.deck_z(bay0 + (bay1 - bay0) * k / 15.0) for k in range(16)) - 0.10
    cs = sorted(stones["courses"], key=lambda c: c["z0"])
    for ci, c in enumerate(cs):
        z0c = c["z0"]
        z1c = cs[ci + 1]["z0"] if ci + 1 < len(cs) else deck_top
        for key in ("blocks", "block_centers"):
            if key in c and isinstance(c[key], list):
                bl = c[key]
                if key == "block_centers":
                    st = abs(bl[1] - bl[0])
                    edges = [bl[0] - st / 2] + [(bl[k] + bl[k + 1]) / 2 for k in
                                                range(len(bl) - 1)] + [bl[-1] + st / 2]
                else:
                    edges = bl
                for e in edges:
                    u, v0 = xz_to_px(ext, e, min(z1c, z1))
                    _, v1 = xz_to_px(ext, e, z0c)
                    cv2.line(out, (int(u), int(v0)), (int(u), int(v1)), (255, 255, 0), 1)
        u0, v = xz_to_px(ext, bay0, z0c)
        u1, _ = xz_to_px(ext, bay1, z0c)
        cv2.line(out, (int(u0), int(v)), (int(u1), int(v)), (255, 255, 0), 1)
    # 照片检测缝(红)
    gray = cv2.cvtColor(ortho, cv2.COLOR_BGR2GRAY)
    e = cv2.Canny(cv2.createCLAHE(2.0, (8, 8)).apply(gray), 30, 95)
    red = np.zeros_like(out); red[..., 2] = e
    out = cv2.addWeighted(out, 1.0, red, 0.85, 0)
    cv2.imwrite(os.path.join(OUT, "wire_%s.png" % tag), out)
    print("wire_%s written" % tag)
    return out


def check_boundaries(model, pose, stones, i, tag, tol=0.15, ppm=80.0):
    """逐块边界核对: 每条描摹边界沿法向 ±tol m 采样灰度梯度,
    峰值偏移 <= tol 记 PASS(输出偏移米)。打印表格 + 写 CSV。"""
    ortho, ext, _ = ortho_rectify(model, pose, i, ppm=ppm)
    gray = cv2.cvtColor(ortho, cv2.COLOR_BGR2GRAY).astype(np.float32)
    x0, x1, z0, z1, _ = ext
    bay0, bay1 = model.arches[i]["bay_x0"], model.arches[i]["bay_x1"]
    rows = []
    cs = sorted(stones["courses"], key=lambda c: c["z0"])
    deck_top = max(model.deck_z(bay0 + (bay1 - bay0) * k / 15.0) for k in range(16)) - 0.10

    def sample_grad(x, z, vertical):
        """vertical=True: 竖直边界(沿 x 扫); False: 水平层缝(沿 z 扫)。"""
        r = int(math.ceil(tol * ppm))
        u, v = xz_to_px(ext, x, z)
        u, v = int(round(u)), int(round(v))
        if vertical:
            if u - r < 1 or u + r >= gray.shape[1] - 1:
                return None
            prof = gray[max(v - 2, 0):v + 3, u - r:u + r + 1].mean(axis=0)
        else:
            if v - r < 1 or v + r >= gray.shape[0] - 1:
                return None
            prof = gray[v - r:v + r + 1, max(u - 2, 0):u + 3].mean(axis=1)
        d = np.abs(np.convolve(prof, [-1, 0, 1], "same"))
        d[0] = d[-1] = 0
        k = int(np.argmax(d))
        off = (k - r) / ppm
        conf = float(d[k] / (np.mean(d) + 1e-6))
        return off, conf

    for ci, c in enumerate(cs):
        z0c = c["z0"]
        z1c = cs[ci + 1]["z0"] if ci + 1 < len(cs) else deck_top
        # 层缝(水平线) -> 沿 z 扫
        seg = np.linspace(bay0 + 0.3, bay1 - 0.3, 9)
        offs = []
        for x in seg:
            r = sample_grad(x, z0c, vertical=False)
            if r and r[1] > 1.8:
                offs.append(r[0])
        ok = len(offs) >= 5 and abs(float(np.median(offs))) <= tol
        rows.append(("course_z0", ci, z0c, float(np.median(offs)) if offs else None,
                     len(offs), ok))
        # 竖缝
        if "blocks" in c:
            edges = c["blocks"]
        else:
            bl = c.get("block_centers", [])
            st = abs(bl[1] - bl[0]) if len(bl) > 1 else 1.0
            edges = [bl[0] - st / 2] + [(bl[k] + bl[k + 1]) / 2 for k in range(len(bl) - 1)] \
                + [bl[-1] + st / 2]
        for e in edges:
            if e <= bay0 + 0.1 or e >= bay1 - 0.1:
                continue
            zmid = 0.5 * (min(z1c, z1) + max(z0c, z0))
            r = sample_grad(e, zmid, vertical=True)
            if not r:
                rows.append(("joint_x", e, zmid, None, 0, False))
                continue
            off, conf = r
            rows.append(("joint_x", e, zmid, off, conf, abs(off) <= tol and conf > 1.8))
    npass = sum(1 for r in rows if r[5])
    print("== checklist %s arch %d: %d/%d = %.0f%% (tol ±%.2fm)"
          % (tag, i, npass, len(rows), 100.0 * npass / max(1, len(rows)), tol))
    for r in rows:
        print("  %-9s x=%7.3f z=%6.3f off=%s n/conf=%s %s"
              % (r[0], r[1], r[2], ("None" if r[3] is None else "%+.3f" % r[3]),
                 r[4], "PASS" if r[5] else "FAIL"))
    return rows


# ── 曲线采样自动吸附(半自动控制点) ──
def _project_curve(model, pose, i, n=64, span=0.98):
    """第 i 孔 intrados 上 n 个采样点 -> (pts3d, uv)。"""
    rv, tv, K = pose_arr(pose)
    xc, spz, a, b = model.arch(i)
    side = int(pose["side"])
    pts = []
    for k in range(n):
        xr = -a * span + 2 * a * span * k / (n - 1)
        x = xc + xr
        z = model.intrados_z(x, i)
        pts.append((x, side * model.hw(x, z), z))
    return np.array(pts, np.float64), project(pts, K, rv, tv)


def snap_curve(model, pose, i, n=16, span=(0.25, 0.98), search=14.0):
    """沿 intrados 采 n 个样本并吸附到图像暗边(洞口边界), 亚像素。
    返回 [(x_rel, u, v, conf)]。避开 x_rel<0.25a 的竖直段(斜率大,横向吸附
    不稳)与 impost/座石干扰区。"""
    img = cv2.imread(pose["image"])
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    rv, tv, K = pose_arr(pose)
    P3, uv = _project_curve(model, pose, i, n=96)
    xc, spz, a, b = model.arch(i)
    out = []
    for k in range(96):
        xr = (P3[k, 0] - xc)
        an = abs(xr) / a
        if an < span[0] or an > span[1]:
            continue
        u, v = uv[k]
        # 局部切线: 用相邻投影点
        k0, k1 = max(0, k - 2), min(95, k + 2)
        d = uv[k1] - uv[k0]
        L = np.hypot(*d)
        if L < 1e-6:
            continue
        t = d / L
        nrm = np.array([-t[1], t[0]])
        # 法向指向洞内(暗侧): 探针 = 曲线点沿 -n 偏 1m 处应更暗
        z_in = model.intrados_z(P3[k, 0] - 0.0001, i) - 0.35
        pin = project(np.array([[P3[k, 0], P3[k, 1], z_in]], np.float64),
                      K, rv, tv)[0]
        if np.dot(pin - uv[k], nrm) < 0:
            nrm = -nrm
        r = int(round(search))
        us = np.arange(-r, r + 1)
        base = np.array([u, v])
        samp = np.array([base + s * nrm for s in us])
        # 双线性采样
        x0 = np.clip(np.floor(samp[:, 0]).astype(int), 0, gray.shape[1] - 2)
        y0 = np.clip(np.floor(samp[:, 1]).astype(int), 0, gray.shape[0] - 2)
        fx = samp[:, 0] - x0; fy = samp[:, 1] - y0
        prof = (gray[y0, x0] * (1 - fx) * (1 - fy) + gray[y0, x0 + 1] * fx * (1 - fy)
                + gray[y0 + 1, x0] * (1 - fx) * fy + gray[y0 + 1, x0 + 1] * fx * fy)
        g = np.convolve(prof, [-1, 0, 1], "same")  # 沿 +n 方向变暗
        g[0] = g[-1] = 0
        j = int(np.argmax(g))
        if j <= 1 or j >= len(us) - 2 or g[j] < 6.0:
            continue
        # 亚像素抛物线
        d1, d2, d3 = g[j - 1], g[j], g[j + 1]
        denom = (d1 - 2 * d2 + d3)
        off = 0.5 * (d1 - d3) / denom if abs(denom) > 1e-9 else 0.0
        s = us[j] + off
        out.append((xr, *(base + s * nrm), float(g[j])))
    return out


def cmd_snap(corr_path, out_path, n=16):
    corr = json.load(open(corr_path))
    model = Model(load_ctrl())
    tag = corr.get("tag")
    pose = load_pose(tag)
    pts = []
    seen_arch = set()
    for p in corr["points"]:
        if "arch" in p["spec"]:
            seen_arch.add(p["spec"]["arch"])
    for i in sorted(seen_arch):
        samples = snap_curve(model, pose, i, n=n)
        print("arch %d: %d snapped samples" % (i, len(samples)))
        for xr, u, v, cf in samples:
            pts.append({"id": "snap_a%d_%+.2f" % (i, xr),
                        "spec": {"arch": i, "t": "intrados", "x_rel": float(xr)},
                        "u": float(u), "v": float(v), "snap_conf": cf})
    corr2 = dict(corr)
    corr2["points"] = pts
    json.dump(corr2, open(out_path, "w"), indent=1)
    print("wrote", out_path)


def cmd_icp(corr_path, iters=3, viz=True):
    """ICP 式位姿精化: 模型 intrados 采样 -> 图像暗边吸附 -> 剔外点 -> 重解 PnP。
    初始位姿来自 corr 文件的人工粗标; 搜索半径 40->20->10px 递减。"""
    corr = json.load(open(corr_path))
    tag = corr.get("tag")
    model = Model(load_ctrl())
    pose = load_pose(tag)
    arches = sorted({p["spec"]["arch"] for p in corr["points"] if "arch" in p["spec"]})
    img = cv2.imread(pose["image"])
    radii = [40.0, 20.0, 10.0]
    trim = [30.0, 18.0, 10.0]
    for it in range(iters):
        rv, tv, K = pose_arr(pose)
        P3, pts2 = [], []
        for i in arches:
            for xr, u, v, cf in snap_curve(model, pose, i, n=40,
                                           span=(0.0, 0.86), search=radii[it]):
                x = model.arches[i]["xc"] + xr
                z = model.intrados_z(x, i)
                P3.append((x, int(pose["side"]) * model.hw(x, z), z))
                pts2.append((u, v))
        P3 = np.array(P3, np.float64); pts2 = np.array(pts2, np.float64)
        pr = project(P3, K, rv, tv)
        res = np.linalg.norm(pr - pts2, axis=1)
        keep = res < trim[it]
        P3, pts2 = P3[keep], pts2[keep]
        ok, rv2, tv2 = cv2.solvePnP(P3, pts2, K, None, flags=cv2.SOLVEPNP_SQPNP)
        rv2, tv2 = cv2.solvePnPRefineLM(P3, pts2, K, None, rv2, tv2)
        res2 = np.linalg.norm(project(P3, K, rv2, tv2) - pts2, axis=1)
        best = (float(np.sqrt(np.mean(res2 ** 2))), pose["f"], rv2, tv2)
        for f in np.linspace(best[1] * 0.95, best[1] * 1.05, 21):
            Kf = Kmat(float(f), pose["w"], pose["h"])
            ok, r3, t3 = cv2.solvePnP(P3, pts2, Kf, None, flags=cv2.SOLVEPNP_SQPNP)
            r3, t3 = cv2.solvePnPRefineLM(P3, pts2, Kf, None, r3, t3)
            rr = np.linalg.norm(project(P3, Kf, r3, t3) - pts2, axis=1)
            rms = float(np.sqrt(np.mean(rr ** 2)))
            if rms < best[0]:
                best = (rms, float(f), r3, t3)
        rms, f, rv, tv = best
        K = Kmat(f, pose["w"], pose["h"])
        pose.update(f=f, rvec=rv.reshape(3).tolist(), tvec=tv.reshape(3).tolist(),
                    rms=rms, n=int(len(P3)))
        print("icp it%d: n=%d rms=%.2fpx f=%.0f max=%.2f"
              % (it, len(P3), rms, f, res2.max() if len(res2) else -1))
    json.dump(pose, open(os.path.join(OUT, "pose_%s.json" % tag), "w"), indent=1)
    if viz:
        vis = img.copy()
        for i in arches:
            _, uvc = _project_curve(model, pose, i, n=120)
            cv2.polylines(vis, [uvc.astype(np.int32)], False, (0, 255, 255), 2)
            xc, spz, a, b = model.arch(i)
            E = []
            for k in range(120):
                xr = -a * 1.18 + 2 * a * 1.18 * k / 119.0
                x = xc + xr
                try:
                    z = model.extrados_z(x, i)
                except Exception:
                    continue
                E.append((x, int(pose["side"]) * model.hw(x, z), z))
            ue = project(np.array(E, np.float64), K, rv, tv)
            cv2.polylines(vis, [ue.astype(np.int32)], False, (255, 0, 255), 2)
        cv2.imwrite(os.path.join(OUT, "icp_%s.jpg" % tag), vis,
                    [cv2.IMWRITE_JPEG_QUALITY, 90])
    print("saved pose_%s.json rms=%.2fpx n=%d" % (tag, pose["rms"], pose["n"]))


def main():
    cmd = sys.argv[1]
    model = Model(load_ctrl())
    if cmd == "ctrl":
        for i in sorted(model.arches):
            a = model.arches[i]
            print("arch %2d xc=%8.3f a=%.2f spz=%.3f b=%.3f bay=[%7.3f,%7.3f]"
                  % (i, a["xc"], a["a"], a["spz"], a["b"], a["bay_x0"], a["bay_x1"]))
    elif cmd == "pose":
        corr = json.load(open(sys.argv[2]))
        tag = corr.get("tag") or os.path.splitext(os.path.basename(sys.argv[2]))[0].replace("corr_", "")
        sides = (corr["side"],) if corr.get("side") else (1, -1)
        best = None
        for side in sides:
            corr["side"] = side
            p = solve_pose(corr, model)
            if best is None or p["rms"] < best["rms"]:
                best = p
        best["tag"] = tag
        json.dump(best, open(os.path.join(OUT, "pose_%s.json" % tag), "w"), indent=1)
        print("saved pose_%s.json (side=%+d)" % (tag, best["side"]))
    elif cmd == "ortho":
        tag, i = sys.argv[2], int(sys.argv[3])
        pose = load_pose(tag)
        ortho_rectify(model, pose, i, tag="%s_%d" % (tag, i))
        print("ortho_%s_%d.png written" % (tag, i))
    elif cmd == "snap":
        cmd_snap(sys.argv[2], sys.argv[3], n=int(sys.argv[4]) if len(sys.argv) > 4 else 16)
    elif cmd == "icp":
        cmd_icp(sys.argv[2])
    elif cmd == "detect":
        detect_seams(sys.argv[2])
    elif cmd == "wire":
        tag, i, sp = sys.argv[2], int(sys.argv[3]), sys.argv[4]
        pose = load_pose(tag)
        wire_overlay(model, pose, load_stones(sp), i, "%s_%d" % (tag, i))
    elif cmd == "check":
        tag, i, sp = sys.argv[2], int(sys.argv[3]), sys.argv[4]
        pose = load_pose(tag)
        check_boundaries(model, pose, load_stones(sp), i, "%s_%d" % (tag, i))
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
