# e30_shikongqiao_video/3d/printcheck.py
# -*- coding: utf-8 -*-
"""P1-T5 printcheck: 打印性验证器(流形/自交/壁厚@scale/穿透/体积)。

单位约定(顶点与 families/场景一致, 单位=米):
- THIN_WALL 按打印件毫米: 任一 bbox 维(m) * scale * 1000 < min_wall_mm(brief 公式, 严格小于);
- PENETRATION 按模型毫米: AABB 重叠深度(m) * 1000 > tol_mm。语义依据 brief 测试:
  两盒间距 0.999 即重叠 0.001m = 1mm(模型) > tol 0.5mm 必报; scale 仅用于消息中的打印当量换算。

判据:
- 流形 = 每条边恰被 2 个面使用(纯面拓扑计数, 不依赖法向/vn -- T2 审查裁决方向);
- 自交 = 逐面 AABB 粗筛 + 精检(纯 numpy 手写, 无第三方几何库), 分两路:
  * 共面对(整面共面): 按多边形「边界」判 -- 边界横穿或顶点严格包含才算交叉;
    扇形三角化的对角线是伪边不参与, 否则同平面叠置两石(对角线交叉)必误报(有负控制钉死)。
  * 非共面对: 三角扇逐对精检(严格跨越对方平面 + 交线段相交)。扇面恒等于真实面片,
    三角级交叉即真实表面交叉; 单侧贴边(接触)不算。
  共享顶点的相邻面对一律跳过(本就贴合)。面片假定: 凸、平面(族库满足)。
  语义边界: 偏置共面「部分接触」(T 形交界/边界共线)不算交叉 -- 零体积重叠即接触;
  面级判据无法区分「接触」与「轴向齐平的实体互穿」(二者共面对 2D 构型全同),
  后者属分离实体, 由 gap_check 的 AABB 重叠判据负责(见 test_penetration)。
- 规模契约: 逐石调用(数十~数百面), AABB 对矩阵 O(n^2) 足够; 不用于整桥合并网格。
"""
import numpy as np

_EPS = 1e-9     # 3D 长度/平面距离容差(m)
_EPS2 = 1e-12   # 2D 叉积容差(m^2, 面积量级)


# ---------------------------------------------------------------- 流形

def _manifold_issues(faces):
    # type: (list) -> list
    """面拓扑流形: 每条边(无向)恰被 2 个面使用。退化面单独报且不参与计数。"""
    issues = []
    degenerate = [i for i, f in enumerate(faces) if len(f) < 3 or len(set(f)) != len(f)]
    if degenerate:
        issues.append("DEGENERATE_FACE: %d face(s), e.g. #%d" % (len(degenerate), degenerate[0]))
    degen = set(degenerate)
    ec = {}
    for i, f in enumerate(faces):
        if i in degen:
            continue
        n = len(f)
        for k in range(n):
            a, b = f[k], f[(k + 1) % n]
            key = (a, b) if a <= b else (b, a)
            ec[key] = ec.get(key, 0) + 1
    bad = sorted(e for e, c in ec.items() if c != 2)
    if bad:
        issues.append("NON_MANIFOLD: %d edge(s) used by !=2 faces, e.g. %s x%d"
                      % (len(bad), str(bad[0]), ec[bad[0]]))
    return issues


# ---------------------------------------------------------------- 几何基元

def _face_tris(verts, faces):
    # type: (np.ndarray, list) -> list
    """凸面假定: 多边形扇形三角化。返回 [face -> [np.ndarray(3,3), ...]]。"""
    out = []
    for f in faces:
        p0 = verts[f[0]]
        tris = []
        for k in range(1, len(f) - 1):
            tris.append(np.array([p0, verts[f[k]], verts[f[k + 1]]]))
        out.append(tris)
    return out


def _newell_normal(pts):
    # type: (np.ndarray) -> np.ndarray
    """多边形 Newell 法线(平面凸面稳健)。"""
    n = np.zeros(3)
    m = len(pts)
    for k in range(m):
        a = pts[k]
        b = pts[(k + 1) % m]
        n[0] += (a[1] - b[1]) * (a[2] + b[2])
        n[1] += (a[2] - b[2]) * (a[0] + b[0])
        n[2] += (a[0] - b[0]) * (a[1] + b[1])
    return n


def _seg_seg_dist(p1, q1, p2, q2):
    # type: (np.ndarray, np.ndarray, np.ndarray, np.ndarray) -> float
    """两线段最近距离(Ericson clamped closest-point)。"""
    d1 = q1 - p1
    d2 = q2 - p2
    r = p1 - p2
    a = float(d1 @ d1)
    e = float(d2 @ d2)
    f = float(d2 @ r)
    tiny = _EPS * _EPS
    if a <= tiny and e <= tiny:
        return float(np.linalg.norm(r))
    if a <= tiny:
        s = 0.0
        t = min(1.0, max(0.0, f / e))
    else:
        c = float(d1 @ r)
        if e <= tiny:
            t = 0.0
            s = min(1.0, max(0.0, -c / a))
        else:
            b = float(d1 @ d2)
            denom = a * e - b * b
            s = min(1.0, max(0.0, (b * f - c * e) / denom)) if denom > 0.0 else 0.0
            t = (b * s + f) / e
            if t < 0.0:
                t = 0.0
                s = min(1.0, max(0.0, -c / a))
            elif t > 1.0:
                t = 1.0
                s = min(1.0, max(0.0, (b - c) / a))
    return float(np.linalg.norm((p1 + d1 * s) - (p2 + d2 * t)))


def _clip_segment(tri, dist, eps):
    # type: (np.ndarray, list, float) -> tuple
    """三角形与平面的交线段(顶点带平面有符号距离 dist, 须严格跨越)。"""
    pts = []
    for i in range(3):
        j = (i + 1) % 3
        di, dj = dist[i], dist[j]
        if (di > eps and dj < -eps) or (di < -eps and dj > eps):
            t = di / (di - dj)
            pts.append(tri[i] + (tri[j] - tri[i]) * t)
    if len(pts) < 2:
        return None
    return pts[0], pts[1]


def _cross2(o, a, b):
    # type: (tuple, tuple, tuple) -> float
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _proper_cross2(a, b, c, d):
    # type: (tuple, tuple, tuple, tuple) -> bool
    """两 2D 线段横穿(交点在双方内部; 共线/端点触碰不算)。"""
    d1 = _cross2(c, d, a)
    d2 = _cross2(c, d, b)
    d3 = _cross2(a, b, c)
    d4 = _cross2(a, b, d)
    if abs(d1) <= _EPS2 or abs(d2) <= _EPS2 or abs(d3) <= _EPS2 or abs(d4) <= _EPS2:
        return False
    return (d1 > 0) != (d2 > 0) and (d3 > 0) != (d4 > 0)


def _strictly_inside2(pt, poly2d):
    # type: (tuple, list) -> bool
    """点严格位于凸多边形内部(在边上不算)。"""
    sgn = None
    m = len(poly2d)
    for i in range(m):
        c = _cross2(poly2d[i], poly2d[(i + 1) % m], pt)
        if abs(c) <= _EPS2:
            return False
        s = c > 0
        if sgn is None:
            sgn = s
        elif s != sgn:
            return False
    return True


def _project2(pts, normal):
    # type: (np.ndarray, np.ndarray) -> list
    """沿法线主轴投影到 2D(去掉绝对值最大的分量, 保持分量次序)。"""
    ax = int(np.argmax(np.abs(normal)))
    keep = [k for k in range(3) if k != ax]
    return [(float(p[keep[0]]), float(p[keep[1]])) for p in pts]


# ---------------------------------------------------------------- 相交精检

def _coplanar_faces_intersect(pts_i, pts_j, ni):
    # type: (np.ndarray, np.ndarray, np.ndarray) -> bool
    """整面共面: 按「边界」判交叉(横穿或严格包含)。扇形对角线不参与。"""
    P = _project2(pts_i, ni)
    Q = _project2(pts_j, ni)
    mp, mq = len(P), len(Q)
    for a in range(mp):
        for b in range(mq):
            if _proper_cross2(P[a], P[(a + 1) % mp], Q[b], Q[(b + 1) % mq]):
                return True
    return _strictly_inside2(P[0], Q) or _strictly_inside2(Q[0], P)


def _tris_cross_non_coplanar(t1, t2):
    # type: (np.ndarray, np.ndarray) -> bool
    """非共面三角对: 双方严格跨越对方平面 + 交线段相交(单侧贴边=接触, 不算)。"""
    n1 = np.cross(t1[1] - t1[0], t1[2] - t1[0])
    n2 = np.cross(t2[1] - t2[0], t2[2] - t2[0])
    if float(n1 @ n1) <= _EPS * _EPS or float(n2 @ n2) <= _EPS * _EPS:
        return False  # 退化三角
    d1 = [float((v - t1[0]) @ n1) for v in t2]   # t2 各顶点到平面(t1)
    d2 = [float((v - t2[0]) @ n2) for v in t1]   # t1 各顶点到平面(t2)
    if not (min(d2) < -_EPS and max(d2) > _EPS):
        return False
    if not (min(d1) < -_EPS and max(d1) > _EPS):
        return False
    sp = _clip_segment(t1, d2, _EPS)
    sq = _clip_segment(t2, d1, _EPS)
    if sp is None or sq is None:
        return False
    return _seg_seg_dist(sp[0], sp[1], sq[0], sq[1]) <= _EPS


def _face_pair_crosses(pts_i, pts_j, ni, nj, tris_i, tris_j):
    # type: (np.ndarray, np.ndarray, np.ndarray, np.ndarray, list, list) -> bool
    if float(nj @ nj) <= _EPS * _EPS or float(ni @ ni) <= _EPS * _EPS:
        return False  # 退化面(DEGENERATE_FACE 已报)
    d = [float((v - pts_i[0]) @ ni) for v in pts_j]
    if all(abs(x) <= _EPS for x in d):
        return _coplanar_faces_intersect(pts_i, pts_j, ni)
    return any(_tris_cross_non_coplanar(a, b) for a in tris_i for b in tris_j)


def _self_intersect_count(verts, faces):
    # type: (np.ndarray, list) -> int
    """逐面 AABB 粗筛 -> 跳过共享顶点的相邻对 -> 共面/非共面分路精检。返回交叉面对数。"""
    n = len(faces)
    if n < 2:
        return 0
    polys = [verts[list(f)] for f in faces]
    normals = [_newell_normal(p) for p in polys]
    tris = _face_tris(verts, faces)
    vsets = [set(f) for f in faces]
    lo = np.array([p.min(axis=0) for p in polys])
    hi = np.array([p.max(axis=0) for p in polys])
    ov = np.all(lo[:, None, :] <= hi[None, :, :], axis=2) & \
         np.all(hi[:, None, :] >= lo[None, :, :], axis=2)
    hits = 0
    for i, j in zip(*np.nonzero(np.triu(ov, 1))):
        i, j = int(i), int(j)
        if vsets[i] & vsets[j]:
            continue  # 相邻面(共享顶点)本就贴合
        if _face_pair_crosses(polys[i], polys[j], normals[i], normals[j], tris[i], tris[j]):
            hits += 1
    return hits


# ---------------------------------------------------------------- 体积

def volume(verts, faces):
    # type: (list, list) -> float
    """散度定理体积(取绝对值; 族库绕向朝内, 不作绕向判据)。"""
    V = np.asarray(verts, dtype=float)
    total = 0.0
    for f in faces:
        p0 = V[f[0]]
        for k in range(1, len(f) - 1):
            total += float(p0 @ np.cross(V[f[k]], V[f[k + 1]]))
    return abs(total) / 6.0


# ---------------------------------------------------------------- 对外接口

def check_stone(verts, faces, scale=1.0 / 50.0, min_wall_mm=1.2):
    # type: (list, list, float, float) -> dict
    """逐石打印性检查。返回 {"ok": bool, "issues": [str], "volume_m3": float}。"""
    V = np.asarray(verts, dtype=float)
    if V.size == 0 or len(faces) == 0:
        return {"ok": False,
                "issues": ["EMPTY_MESH: %d verts / %d faces" % (len(verts), len(faces))],
                "volume_m3": 0.0}
    issues = []
    issues.extend(_manifold_issues(faces))
    ext = V.max(axis=0) - V.min(axis=0)
    for axis, e in zip(("x", "y", "z"), ext):
        mm = float(e) * scale * 1000.0
        if mm < min_wall_mm:
            issues.append("THIN_WALL: bbox %s=%.3fmm < %.3fmm @scale 1/%d"
                          % (axis, mm, min_wall_mm, int(round(1.0 / scale))))
    hits = _self_intersect_count(V, faces)
    if hits:
        issues.append("SELF_INTERSECT: %d face-pair(s) cross (eps=%g)" % (hits, _EPS))
    return {"ok": not issues, "issues": issues, "volume_m3": volume(verts, faces)}


def gap_check(entry_a, entry_b, tol_mm=0.5, scale=1.0 / 50.0):
    # type: (tuple, tuple, float, float) -> list
    """两石空间关系检查。entry = (位置偏移, (verts, faces))。
    AABB 重叠深度(模型 mm) > tol_mm -> ["PENETRATION: ..."]; 否则 [](贴合/容差内/分离均干净)。"""
    pa, ma = entry_a
    pb, mb = entry_b
    Va = np.asarray(ma[0], dtype=float) + np.asarray(pa, dtype=float)
    Vb = np.asarray(mb[0], dtype=float) + np.asarray(pb, dtype=float)
    a_lo, a_hi = Va.min(axis=0), Va.max(axis=0)
    b_lo, b_hi = Vb.min(axis=0), Vb.max(axis=0)
    overlap = np.minimum(a_hi, b_hi) - np.maximum(a_lo, b_lo)
    if not np.all(overlap > 0.0):
        return []
    depth_mm = float(overlap.min()) * 1000.0   # 模型毫米
    if depth_mm > tol_mm:
        return ["PENETRATION: overlap %.4fmm(model)=%.4fmm(printed) > tol %.3fmm"
                % (depth_mm, depth_mm * scale, tol_mm)]
    return []
