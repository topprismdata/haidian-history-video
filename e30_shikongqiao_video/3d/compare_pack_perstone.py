# -*- coding: utf-8 -*-
"""M23 逐石像素层: 渲染 Position AOV -> 逐像素反查 stones_pX.json 石 id,
与描摹多边形(照片侧真值)按位姿投影做逐石 IoU + 边界法向偏移。

范围: 有标定位姿+描摹砖谱的孔 —— A05/A06(m20B f150/f175), A07-A09(p2017, 需 pose_p2017.json)。
阈值: IoU>=0.7 或 边界偏移 mean<=3x位姿RMS(px) = PASS; 阈值入档可调。
产出: out/compare_pack/perstone/<tag>_report.csv + <tag>_overlay.png + <tag>_summary.json

用法:
  # 1) AOV 渲染(blender):
  blender -b e30_bridge.blend --python compare_pack_aov.py -- <pose_json> <out.exr> [res_x]
  # 2) 逐石判定(系统 python):
  python3 compare_pack_perstone.py <pose_json> <stones_json> <aov.exr> <tag> [--photo real_券洞X.jpg]
"""
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from m20_pipeline import Model, load_ctrl, Kmat, project  # noqa: E402

IOU_PASS = 0.70
OFF_RMS_MULT = 3.0


def rodrigues(rv):
    th = float(np.linalg.norm(rv))
    k = rv / th
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + math.sin(th) * K + (1 - math.cos(th)) * (K @ K)


def model_to_world():
    import bpy  # 仅 AOV 合成时在 blender 内用; 系统侧用 json 缓存
    root = bpy.data.objects["bridge_body"]
    Mw = root.matrix_world.to_3x3()
    axes = [Mw @ __import__("mathutils").Vector(v) for v in ((1, 0, 0), (0, 1, 0), (0, 0, 1))]
    return np.array([[axes[c][r] / axes[c].length for c in range(3)] for r in range(3)])


def stones_to_rects(path):
    """stones_pX.json -> [{id, x0,x1,z0,z1}] (课程层叠+块区间; 水下层带 _trace 保留仍算)。"""
    d = json.load(open(path))
    out = []
    courses = d["courses"]
    for ci, c in enumerate(courses):
        z0 = c["z0"]
        z1 = courses[ci + 1]["z0"] if ci + 1 < len(courses) else c.get("z1", z0 + 0.45)
        b = c["blocks"]
        for bi in range(len(b) - 1):
            out.append(dict(id="c%02db%02d" % (ci, bi), x0=b[bi], x1=b[bi + 1], z0=z0, z1=z1))
    return out


def lookup_lut(rects, model, side=-1):
    """(x,z)->stone_id 查找表: 按课程分带, 带内按 blocks 二分。"""
    courses = {}
    for r in rects:
        courses.setdefault(round(r["z0"], 3), []).append(r)
    return courses


def stone_at(courses, x, z):
    zq = round(z, 3)
    band = None
    for z0 in sorted(courses):
        if z0 <= zq:
            band = courses[z0]
    if band is None:
        return None
    for r in band:
        if r["x0"] <= x < r["x1"]:
            return r["id"]
    return None


def main_npz(npz_path, pose_path, stones_path, tag):
    """raylabel 标签图 -> 逐石 IoU/偏移表。design=描摹多边形投影, actual=标签图。"""
    from PIL import ImageDraw
    d = np.load(npz_path, allow_pickle=True)
    label = d["label"]
    ids = [str(x) for x in d["ids"]]
    roi = d["roi"]
    step = int(d["step"])
    side = int(d["side"])
    Rw = np.array(d["rw"])
    pose = json.load(open(pose_path))
    rects = stones_to_rects(stones_path)
    model = Model(load_ctrl())
    H, W = label.shape
    sx = pose["w"] / float(pose["w"])  # 标签图即标定画幅 ROI 重采样
    K = Kmat(pose["f"], pose["w"], pose["h"])
    rv = np.array(pose["rvec"], np.float64)
    tv = np.array(pose["tvec"], np.float64)

    rows = []
    overlay = np.full((H, W, 3), 18, np.uint8)
    lid = {sid: k for k, sid in enumerate(ids)}
    for r in rects:
        sid = r["id"]
        corners = [(r["x0"], r["z0"]), (r["x1"], r["z0"]), (r["x1"], r["z1"]), (r["x0"], r["z1"])]
        pts3d = [(x, side * model.hw(x, z), z) for x, z in corners]
        uv = project(np.array(pts3d), K, rv, tv)
        uv[:, 0] = (uv[:, 0] - roi[0]) / step
        uv[:, 1] = (uv[:, 1] - roi[1]) / step
        if uv[:, 0].min() < 0 or uv[:, 0].max() >= W or uv[:, 1].min() < 0 or uv[:, 1].max() >= H:
            continue
        design = np.zeros((H, W), np.uint8)
        cv2.fillPoly(design, [np.round(uv).astype(np.int32)], 1)
        actual = (label == lid[sid]).astype(np.uint8) if sid in lid else np.zeros((H, W), np.uint8)
        if actual.sum() == 0 or design.sum() == 0:
            rows.append(dict(stone_id=sid, iou=None, off_mean_px=None, off_max_px=None,
                             verdict="NOT_VISIBLE"))
            continue
        inter = int(((design == 1) & (actual == 1)).sum())
        union = int(((design == 1) | (actual == 1)).sum())
        iou = inter / union if union else 0.0
        dt_i = cv2.distanceTransform((actual == 1).astype(np.uint8), cv2.DIST_L2, 3)
        dt_o = cv2.distanceTransform((actual == 0).astype(np.uint8), cv2.DIST_L2, 3)
        poly = np.round(uv).astype(np.int32)
        offs = []
        for k in range(4):
            a, b = poly[k], poly[(k + 1) % 4]
            for t in np.linspace(0.15, 0.85, 5):
                p = (a * (1 - t) + b * t).astype(int)
                inside = actual[p[1], p[0]] == 1
                # 内点: 到 actual 外边界的距离为正(dt_i); 外点: 到 actual 的距离为负(dt_o)
                offs.append((dt_i[p[1], p[0]] if inside else -dt_o[p[1], p[0]]))
        offs = np.array(offs)
        rms = float(pose.get("rms", 5.2)) * step
        ok = (iou >= IOU_PASS) or (np.abs(offs).mean() <= OFF_RMS_MULT * rms)
        rows.append(dict(stone_id=sid, iou=round(iou, 4), off_mean_px=round(float(offs.mean()) / step, 2),
                         off_max_px=round(float(np.abs(offs).max()) / step, 2),
                         verdict="PASS" if ok else "FAIL"))
        col = (0, 200, 0) if ok else (220, 40, 40)
        cv2.polylines(overlay, [poly], True, col, 1)
    out_dir = os.path.join(HERE, "out", "compare_pack", "perstone")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "%s_report.csv" % tag), "w") as f:
        f.write("stone_id,iou,off_mean_px,off_max_px,verdict\n")
        for r in rows:
            f.write("%s,%s,%s,%s,%s\n" % (r["stone_id"],
                                          r["iou"] if r["iou"] is not None else "",
                                          r["off_mean_px"] if r["off_mean_px"] is not None else "",
                                          r["off_max_px"] if r["off_max_px"] is not None else "",
                                          r["verdict"]))
    cv2.imwrite(os.path.join(out_dir, "%s_overlay.png" % tag), overlay)
    npass = sum(1 for r in rows if r["verdict"] == "PASS")
    judged = [r for r in rows if r["verdict"] != "NOT_VISIBLE"]
    summary = dict(tag=tag, stones=len(rows), visible=len(ids), pass_n=npass,
                   judged=len(judged), not_visible=len(rows) - len(judged),
                   pass_rate=round(npass / max(1, len(judged)), 4),
                   iou_median=round(float(np.median([r["iou"] for r in judged])), 4) if judged else None,
                   thresholds=dict(iou_pass=IOU_PASS, off_rms_mult=OFF_RMS_MULT, pose_rms_px=pose.get("rms")),
                   note="design=stones_pX 描摹 rect 投影; actual=raylabel 标签图(被摄面带+法线过滤); "
                        "偏移已按 step 折算标定画幅 px; 整体平移=位姿残差单列")
    json.dump(summary, open(os.path.join(out_dir, "%s_summary.json" % tag), "w"), ensure_ascii=False, indent=1)
    print("PERSTONE_DONE", tag, "pass %d/%d" % (npass, len(rows)))


def main():
    if sys.argv[1] == "--npz":
        return main_npz(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
    pose_path, aov_path, tag = sys.argv[1], sys.argv[2], sys.argv[3]
    stones_path = sys.argv[4]
    photo_path = sys.argv[5] if len(sys.argv) > 5 and not sys.argv[5].startswith("--") else None
    pose = json.load(open(pose_path))
    rects = stones_to_rects(stones_path)
    model = Model(load_ctrl())
    side = int(pose.get("side", -1))

    # ── 读 AOV(Position/Normal, 由 compare_pack_aov.py 双 File Output 渲出) ──
    base = aov_path.replace("_pos.exr", "")
    img = cv2.imread(base + "_pos.exr", cv2.IMREAD_UNCHANGED)
    nor = cv2.imread(base + "_nor.exr", cv2.IMREAD_UNCHANGED)
    if img is None:
        raise SystemExit("AOV 读不到: " + base + "_pos.exr")
    H, W = img.shape[:2]
    pos = img[..., :3].astype(np.float64)
    nrm = nor[..., :3].astype(np.float64) if nor is not None else None
    K = Kmat(pose["f"], pose["w"], pose["h"])
    scale_x = W / float(pose["w"])

    # 世界 -> 模型系
    R = rodrigues(np.array(pose["rvec"], np.float64))
    Rw = np.array(json.load(open(os.path.join(HERE, "out", "compare_pack", "params", "rw_cache_%s.json" % tag))))
    Pm = (np.linalg.inv(Rw) @ pos.reshape(-1, 3).T).T.reshape(H, W, 3)

    # 面上判定: |y_model - side*hw| < tol; tol 取局部像素尺度的 1/4(米)
    xs = Pm[..., 0]
    zs = Pm[..., 2]
    hw = model.hw(np.clip(xs, -75, 75), np.clip(zs, 0, 8))
    yface = side * hw
    depth = np.linalg.norm(pos, axis=2)
    px_m = pose["f"] / np.maximum(depth, 1e-6)  # px/m(标定画幅)
    tol = 0.25 * 4.0 / np.maximum(px_m * scale_x, 1e-6)
    onface = np.abs(Pm[..., 1] - yface) < tol
    # 主控边界条件: 东西两面同 (x,z) 会重叠 -> 只收"被拍摄面带"(法线朝相机侧)
    if nrm is not None:
        fw = Rw @ np.array([0.0, float(side), 0.0])  # 被摄面外法线(世界系)
        facing = (nrm @ fw) > 0.5
        onface = onface & facing
        print("FACING px:", int(facing.sum()))
    print("ONFACE px:", int(onface.sum()), "/", H * W)

    # 逐像素 stone id
    courses = {}
    for r in rects:
        courses.setdefault(round(r["z0"], 3), []).append(r)
    zsorted = sorted(courses)
    id_map = {}
    label = np.full((H, W), -1, np.int32)
    ys, xs_ = np.nonzero(onface)
    for yy, xx in zip(ys, xs_):
        z = zs[yy, xx]
        band = None
        for z0 in zsorted:
            if z0 <= z:
                band = courses[z0]
        if band is None:
            continue
        x = xs[yy, xx]
        for r in band:
            if r["x0"] <= x < r["x1"]:
                if r["id"] not in id_map:
                    id_map[r["id"]] = len(id_map)
                label[yy, xx] = id_map[r["id"]]
                break
    print("LABELED stones:", len(id_map))

    # ── 设计多边形投影 + IoU/偏移 ──
    rows = []
    vis = cv2.cvtColor((np.clip(img[..., :3] / (img[..., :3].max() + 1e-9), 0, 1) * 255).astype(np.uint8), cv2.COLOR_BGR2RGB)
    vis = cv2.cvtColor(cv2.cvtColor(vis, cv2.COLOR_RGB2GRAY), cv2.COLOR_GRAY2BGR)
    for r in rects:
        sid = r["id"]
        corners = [(r["x0"], r["z0"]), (r["x1"], r["z0"]), (r["x1"], r["z1"]), (r["x0"], r["z1"])]
        pts3d = [(x, side * model.hw(x, z), z) for x, z in corners]
        uv = project(np.array(pts3d), K, np.array(pose["rvec"], np.float64),
                     np.array(pose["tvec"], np.float64)) * scale_x
        uv[:, 1] = H - uv[:, 1]
        if uv[:, 0].min() < 0 or uv[:, 0].max() >= W or uv[:, 1].min() < 0 or uv[:, 1].max() >= H:
            continue
        design = np.zeros((H, W), np.uint8)
        cv2.fillPoly(design, [np.round(uv).astype(np.int32)], 1)
        actual = (label == id_map[sid]).astype(np.uint8) if sid in id_map else np.zeros((H, W), np.uint8)
        inter = int(((design == 1) & (actual == 1)).sum())
        union = int(((design == 1) | (actual == 1)).sum())
        iou = inter / union if union else 0.0
        # 边界法向偏移: 设计多边形边上采样点到 actual 边界的距离(像素, 有符号=内侧为正)
        dt = cv2.distanceTransform((actual == 0).astype(np.uint8), cv2.DIST_L2, 3)
        dt_in = cv2.distanceTransform((actual == 1).astype(np.uint8), cv2.DIST_L2, 3)
        offs = []
        poly = np.round(uv).astype(np.int32)
        for i in range(4):
            a, b = poly[i], poly[(i + 1) % 4]
            for t in np.linspace(0.1, 0.9, 6):
                p = (a * (1 - t) + b * t).astype(int)
                inside = actual[p[1], p[0]] == 1
                offs.append(dt[p[1], p[0]] if inside else -dt_in[p[1], p[0]])
        offs = np.array(offs)
        rms = float(pose.get("rms", 5.2))
        ok = (iou >= IOU_PASS) or (np.abs(offs).mean() <= OFF_RMS_MULT * rms)
        rows.append(dict(stone_id=sid, iou=round(iou, 4),
                         off_mean_px=round(float(offs.mean()), 2),
                         off_max_px=round(float(np.abs(offs).max()), 2),
                         verdict="PASS" if ok else "FAIL"))
        col = (0, 200, 0) if ok else (0, 0, 220)
        cv2.polylines(vis, [poly], True, col, 1)
    out_dir = os.path.join(HERE, "out", "compare_pack", "perstone")
    os.makedirs(out_dir, exist_ok=True)
    csvp = os.path.join(out_dir, "%s_report.csv" % tag)
    with open(csvp, "w") as f:
        f.write("stone_id,iou,off_mean_px,off_max_px,verdict\n")
        for r in rows:
            f.write("%(stone_id)s,%(iou)s,%(off_mean_px)s,%(off_max_px)s,%(verdict)s\n" % r)
    cv2.imwrite(os.path.join(out_dir, "%s_overlay.png" % tag), vis)
    npass = sum(1 for r in rows if r["verdict"] == "PASS")
    summary = dict(tag=tag, stones=len(rows), visible=len(id_map), pass_n=npass,
                   pass_rate=round(npass / max(1, len(rows)), 4),
                   iou_median=round(float(np.median([r["iou"] for r in rows])), 4),
                   thresholds=dict(iou_pass=IOU_PASS, off_rms_mult=OFF_RMS_MULT, pose_rms_px=pose.get("rms")),
                   note="设计多边形=stones_pX 描摹(rect 简化); actual=Position AOV 反查; "
                        "整体平移若显著=位姿残差, 单独报告不算石错")
    json.dump(summary, open(os.path.join(out_dir, "%s_summary.json" % tag), "w"), ensure_ascii=False, indent=1)
    print("PERSTONE_DONE", tag, "pass %d/%d" % (npass, len(rows)), csvp)


if __name__ == "__main__":
    main()
