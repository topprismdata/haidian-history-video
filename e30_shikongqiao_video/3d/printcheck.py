# e30_shikongqiao_video/3d/printcheck.py
# -*- coding: utf-8 -*-
"""P1-T5 printcheck: 打印性验证器(流形/平面性/多壳/绕向/自交/壁厚@scale/穿透/体积)。

单位约定(顶点与 families/场景一致, 单位=米):
- THIN_WALL 按打印件毫米: bbox 维(m) * scale * 1000 < min_wall_print_mm(brief 公式, 严格小于);
  另有方向无关面片对代理(W1, 见 _thin_wall_proxy_issues)。bbox 代理仅对局部轴对齐坐标有效,
  勿喂旋转后几何 -- 旋转薄壁由代理兜底。
- PENETRATION 按模型毫米: AABB 重叠深度(m) * 1000 > tol_model_mm。scale 仅用于消息中的打印当量。

判据(全部纯 numpy, 零第三方几何依赖):
- 流形 = 每条边(无向)恰被 2 个面使用; 退化面单独报且不参与任何计数;
- NON_PLANAR_FACE (C1) = Newell 法线归一后顶点平面偏差 > max(abs_eps=1e-12, rel=1e-9 x 面片尺度);
  负控: wedge/slab/L 棱柱/U 槽 dev=0~1.39e-17 全不报; 折穿盒 apex z=-0.5/-0.25/1e-7 全报;
- INVALID_COORD (C2) = 顶点含 NaN/Inf, 在一切几何判据之前闸门(旧实现 ok=True 且 volume=nan 下流);
- MULTI_SHELL (C3) = 面级 union-find 连通域 > 1(对齐 lions2.py assert_watertight 的连通域口径,
  本函数此前只查边界边); DOUBLE_MATERIAL (C3) = volume_m3 > bbox 体积 x 1.000001
  (干净 slab 比值 1.00 / wedge 0.91 零假阳; 重合双壳 2.00 / 齐平互穿 1.43 必报);
- NON_ORIENTABLE (C4) = 同一有向边被两处同向使用(一致绕向即放行; 族库全体内翻是 T6 出口统一
  翻三角的事, printcheck 只保证一致, 不强制朝外); 负控: 干净族库全过, 单面反绕必报 4 坏边;
- 自交 = 逐面 AABB 粗筛 + 精检, 分两路:
  * 共面对(整面共面): 按多边形「边界」判 -- 边界横穿, 或任一顶点严格包含于对方(W3: 遍历全部
    顶点, 旧实现只测 index[0] 对 Q3 类共线边界重叠漏报); 扇形三角化对角线是伪边不参与;
  * 非共面对: 三角扇逐对精检(严格跨越对方平面 + 交线段相交), 单侧贴边(接触)不算。
  共享顶点的相邻面对一律跳过(本就贴合)。面片假定: 凸、平面(族库满足)。
  语义边界: 偏置共面「部分接触」(T 形交界/边界共线)不算交叉 -- 零体积重叠即接触;
  面级判据无法区分「接触」与「轴向齐平的实体互穿」(二者共面对 2D 构型全同),
  后者属分离实体, 由 gap_check 的 AABB 重叠判据负责(见 test_penetration)。
- FACE_INDEX_OUT_OF_RANGE (W5 配套) = 面索引越界/负索引, 在一切几何判据前闸门(旧实现直接 IndexError)。

坏输入(W5/W6): EMPTY_MESH / DEGENERATE_FACE(重复索引或 <3 顶点) 均结构化报出, 不崩。

接口契约(S1): check_stone -> {"ok": bool, "issues": [{"code","detail"}], "volume_m3": float};
gap_check -> {"ok": bool, "issues": [{"code","detail"}]}。报告即 JSON, 下游按 code 过滤。

gap_check 旋转契约(W2): entry = (ledger transform 6 元组 [tx,ty,tz,rx,ry,rz], (verts, faces));
先按 transform 旋转+平移顶点再做 AABB -- 券石 RING 必带转角, 纯 AABB 未旋系=假阳+漏判
(test_gap_check_rotated_entry_contract 钉死)。Euler 'XYZ' 约定(R=Rz.Ry.Rx, 先 X 后 Y 后 Z,
与 Blender rotation_euler 默认一致)。

时序契约(S3): check_stone 必须在导出前对最终 post-inset 几何调用; inset 还会再吃
2x clearance, 若在 inset 前跑 = 放行薄件。

规模契约: 逐石调用(数十~数百面), AABB 对矩阵 O(n^2) 足够; 不用于整桥合并网格。
"""
import numpy as np

_EPS = 1e-9            # 3D 长度/平面距离容差(m)
_EPS2 = 1e-12          # 2D 叉积容差(m^2, 面积量级)
_REL_PLANAR = 1e-9     # C1 平面性相对阈( x 面片尺度)
_ABS_PLANAR = 1e-12    # C1 平面性绝对阈(m)
_PARALLEL_EPS = 1e-6   # W1 |ni.nj| > 1-此值 视为近平行
_BBOX_VOL_SLACK = 1e-6  # C3 体积上界不变量容差


def _issue(code, detail):
    # type: (str, str) -> dict
    return {"code": code, "detail": detail}


def _degenerate_indices(faces):
    # type: (list) -> set
    return set(i for i, f in enumerate(faces) if len(f) < 3 or len(set(f)) != len(f))


# ---------------------------------------------------------------- 流形/拓扑

def _manifold_issues(faces, degen):
    # type: (list, set) -> list
    """面拓扑流形: 每条边(无向)恰被 2 个面使用。退化面单独报且不参与计数。"""
    issues = []
    if degen:
        ds = sorted(degen)
        issues.append(_issue("DEGENERATE_FACE", "%d face(s), e.g. #%d"
                             % (len(ds), ds[0])))
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
        issues.append(_issue("NON_MANIFOLD", "%d edge(s) used by !=2 faces, e.g. %s x%d"
                             % (len(bad), str(bad[0]), ec[bad[0]])))
    return issues


def _orient_issues(faces, degen):
    # type: (list, set) -> list
    """C4: 有向边一致性 -- 同一有向边被两处同向使用 => 绕向不一致(NON_ORIENTABLE)。
    一致绕向(朝内或朝外)均放行; 单面反绕 -> 该面每条边与邻面同向, 4 坏边必报。"""
    dc = {}
    for i, f in enumerate(faces):
        if i in degen:
            continue
        n = len(f)
        for k in range(n):
            key = (f[k], f[(k + 1) % n])
            dc[key] = dc.get(key, 0) + 1
    bad = sorted(e for e, c in dc.items() if c > 1)
    if bad:
        return [_issue("NON_ORIENTABLE", "%d directed edge(s) reused same direction, e.g. %s x%d"
                       % (len(bad), str(bad[0]), dc[bad[0]]))]
    return []


def _shell_issues(faces, degen):
    # type: (list, list) -> list
    """C3: 面级 union-find 连通域(共享无向边即连通) > 1 => MULTI_SHELL。
    口径对齐 lions2.py assert_watertight(连通域 + 边界边), 此前本模块只查后者。"""
    valid = [i for i in range(len(faces)) if i not in degen]
    if len(valid) < 2:
        return []
    parent = dict((i, i) for i in valid)

    def find(x):
        r = x
        while parent[r] != r:
            r = parent[r]
        while parent[x] != r:
            parent[x], x = r, parent[x]
        return r

    owner = {}
    for i in valid:
        f = faces[i]
        n = len(f)
        for k in range(n):
            a, b = f[k], f[(k + 1) % n]
            key = (a, b) if a <= b else (b, a)
            j = owner.setdefault(key, i)
            if j != i:
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[ri] = rj
    ncomp = len(set(find(i) for i in valid))
    if ncomp > 1:
        return [_issue("MULTI_SHELL", "%d disjoint shell(s) (face union-find)" % ncomp)]
    return []


def _planarity_issues(V, faces, rel=_REL_PLANAR, abs_eps=_ABS_PLANAR):
    # type: (np.ndarray, list, float, float) -> list
    """C1: 逐面 Newell 法线归一, 顶点到面平面偏差 > max(abs_eps, rel x 面片尺度) => 报。
    零法线(零面积/退化)面跳过(DEGENERATE_FACE 负责)。"""
    bad = []
    for i, f in enumerate(faces):
        if len(f) < 3:
            continue
        pts = V[list(f)]
        n = _newell_normal(pts)
        ln = float(np.linalg.norm(n))
        if ln <= abs_eps:
            continue
        u = n / ln
        dev = float(np.abs((pts - pts[0]) @ u).max())
        size = float(np.max(pts.max(axis=0) - pts.min(axis=0)))
        if dev > max(abs_eps, rel * size):
            bad.append((i, dev, max(abs_eps, rel * size)))
    if bad:
        i, dev, thr = bad[0]
        return [_issue("NON_PLANAR_FACE", "%d face(s), e.g. #%d dev=%.3e > %.3e"
                       % (len(bad), i, dev, thr))]
    return []


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
    """整面共面: 按「边界」判交叉(横穿或严格包含)。扇形对角线不参与。
    W3: 包含检测遍历双方全部顶点 -- 旧实现只测 index[0], 对「边界全共线、
    严格包含顶点不在 0 位」的共面重叠(Q3)漏报。"""
    P = _project2(pts_i, ni)
    Q = _project2(pts_j, ni)
    mp, mq = len(P), len(Q)
    for a in range(mp):
        for b in range(mq):
            if _proper_cross2(P[a], P[(a + 1) % mp], Q[b], Q[(b + 1) % mq]):
                return True
    return any(_strictly_inside2(p, Q) for p in P) or \
        any(_strictly_inside2(q, P) for q in Q)


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


# ---------------------------------------------------------------- 壁厚代理

def _thin_wall_proxy_issues(polys, normals, scale, min_wall_print_mm):
    # type: (list, list, float, float) -> list
    """W1: 方向无关薄壁代理。bbox 判据只看轴向投影, 旋转后几何全漏;
    这里补: 法线近平行(|ni.nj| > 1-1e-6) 且互相朝向(nj 指向 i 一侧, 反之亦然)的面片对,
    以 j 面顶点到 i 面最小平面距离为壁厚(打印件毫米, 严格小于)。
    绕向语义: 族库内翻绕向下「互相朝向」= 两墙之间夹实体(真薄壁);
    槽腔对壁法线背向, 被排除, 不误报。
    注意: bbox 代理仅局部轴对齐坐标有效, 勿喂旋转后几何; 本代理与其互补。"""
    issues = []
    nf = len(polys)
    cents = [p.mean(axis=0) for p in polys]
    uns = []
    for n in normals:
        ln = float(np.linalg.norm(n))
        uns.append(n / ln if ln > _EPS else None)
    for i in range(nf):
        if uns[i] is None:
            continue
        pi0 = polys[i][0]
        for j in range(i + 1, nf):
            if uns[j] is None:
                continue
            if float(uns[i] @ uns[j]) > -(1.0 - _PARALLEL_EPS):
                continue  # 需近平行且反向
            cij = cents[j] - cents[i]
            if float(cij @ uns[i]) <= 0.0 or float(cij @ uns[j]) >= 0.0:
                continue  # 需互相朝向
            t_mm = min(float(abs((p - pi0) @ uns[i])) for p in polys[j]) * scale * 1000.0
            if t_mm < min_wall_print_mm:
                issues.append(_issue(
                    "THIN_WALL", "pair faces #%d/#%d t=%.3fmm < %.3fmm @scale 1/%d (proxy)"
                    % (i, j, t_mm, min_wall_print_mm, int(round(1.0 / scale)))))
    return issues


# ---------------------------------------------------------------- 变换

def _xform(V, tf):
    # type: (np.ndarray, list) -> np.ndarray
    """ledger transform [tx,ty,tz,rx,ry,rz] -> 世界坐标顶点(先旋转后平移)。
    Euler 'XYZ' 约定: R = Rz.Ry.Rx, 即先绕 X, 再绕 Y, 再绕 Z(与 Blender
    rotation_euler 默认顺序一致)。"""
    tx, ty, tz, rx, ry, rz = (float(t) for t in tf)
    if rx or ry or rz:
        cx, sx = np.cos(rx), np.sin(rx)
        cy, sy = np.cos(ry), np.sin(ry)
        cz, sz = np.cos(rz), np.sin(rz)
        R = (np.array([[cz, -sz, 0.0], [sz, cz, 0.0], [0.0, 0.0, 1.0]])
             @ np.array([[cy, 0.0, sy], [0.0, 1.0, 0.0], [-sy, 0.0, cy]])
             @ np.array([[1.0, 0.0, 0.0], [0.0, cx, -sx], [0.0, sx, cx]]))
        V = V @ R.T
    return V + np.array([tx, ty, tz])


# ---------------------------------------------------------------- 体积

def _volume(V, faces):
    # type: (np.ndarray, list) -> float
    total = 0.0
    for f in faces:
        p0 = V[f[0]]
        for k in range(1, len(f) - 1):
            total += float(p0 @ np.cross(V[f[k]], V[f[k + 1]]))
    return abs(total) / 6.0


def volume(verts, faces):
    # type: (list, list) -> float
    """散度定理体积(取绝对值; 族库绕向朝内, 不作绕向判据)。"""
    return _volume(np.asarray(verts, dtype=float), faces)


# ---------------------------------------------------------------- 对外接口

def _check_scale(scale):
    # type: (float) -> float
    s = float(scale)
    if not 0.0 < s <= 1.0:
        raise ValueError("scale 必须是 (0,1] 的模型比例分数(如 1/50), got %r" % (scale,))
    return s


def check_stone(verts, faces, scale=1.0 / 50.0, min_wall_print_mm=1.2):
    # type: (list, list, float, float) -> dict
    """逐石打印性检查。返回 {"ok": bool, "issues": [{"code","detail"}], "volume_m3": float}。

    时序契约(S3): 必须在导出前对最终 post-inset 几何调用 -- inset 还会再吃 2x clearance,
    若在 inset 前跑 = 放行薄件。scale 为模型比例分数, 域 (0,1], 越界 raise ValueError
    (决策1: 旧 min_wall_mm 参数更名 min_wall_print_mm, 打印件毫米口径写进名字)。"""
    s = _check_scale(scale)
    V = np.asarray(verts, dtype=float)
    if V.size == 0 or len(faces) == 0:
        return {"ok": False,
                "issues": [_issue("EMPTY_MESH", "%d verts / %d faces" % (len(verts), len(faces)))],
                "volume_m3": 0.0}
    if not bool(np.isfinite(V).all()):
        n_bad = int((~np.isfinite(V)).sum())
        return {"ok": False,
                "issues": [_issue("INVALID_COORD", "%d non-finite coord(s) (NaN/Inf)" % n_bad)],
                "volume_m3": float("nan")}
    n = len(V)
    oob = sorted(set(int(i) for f in faces for i in f if not (0 <= i < n)))
    if oob:
        return {"ok": False,
                "issues": [_issue("FACE_INDEX_OUT_OF_RANGE",
                                  "%d index out of [0,%d), e.g. %d" % (len(oob), n, oob[0]))],
                "volume_m3": 0.0}
    issues = []
    degen = _degenerate_indices(faces)
    issues.extend(_manifold_issues(faces, degen))
    issues.extend(_planarity_issues(V, faces))
    issues.extend(_orient_issues(faces, degen))
    issues.extend(_shell_issues(faces, degen))
    polys = [V[list(f)] for f in faces]
    normals = [_newell_normal(p) for p in polys]
    ext = V.max(axis=0) - V.min(axis=0)
    for axis, e in zip(("x", "y", "z"), ext):
        mm = float(e) * s * 1000.0
        if mm < min_wall_print_mm:
            issues.append(_issue("THIN_WALL", "bbox %s=%.3fmm < %.3fmm @scale 1/%d"
                                 % (axis, mm, min_wall_print_mm, int(round(1.0 / s)))))
    issues.extend(_thin_wall_proxy_issues(polys, normals, s, min_wall_print_mm))
    hits = _self_intersect_count(V, faces)
    if hits:
        issues.append(_issue("SELF_INTERSECT", "%d face-pair(s) cross (eps=%g)" % (hits, _EPS)))
    vol = _volume(V, faces)
    bbox_vol = float(np.prod(ext))
    if vol > bbox_vol * (1.0 + _BBOX_VOL_SLACK):
        issues.append(_issue("DOUBLE_MATERIAL",
                             "volume %.6f > bbox_vol %.6f (x%.6f) -> 重合/互穿双壳"
                             % (vol, bbox_vol, vol / bbox_vol)))
    return {"ok": not issues, "issues": issues, "volume_m3": vol}


def gap_check(entry_a, entry_b, tol_model_mm=0.5, scale=1.0 / 50.0):
    # type: (tuple, tuple, float, float) -> dict
    """两石空间关系检查。entry = (ledger transform 6 元组 [tx,ty,tz,rx,ry,rz], (verts, faces))。
    旋转契约(W2): 先按 transform 旋转+平移顶点再做 AABB -- 券石 RING 必带转角,
    纯 AABB 未旋系=假阳+漏判(test_gap_check_rotated_entry_contract 钉死)。
    返回 {"ok": bool, "issues": [{"code","detail"}]} (S1, 与 check_stone 同形, T6 只写一套):
    重叠深度(模型 mm) > tol_model_mm -> PENETRATION; 贴合/容差内/分离均 ok=True 且 issues=[]。
    scale 仅用于消息中的打印当量换算。scale 越界 raise ValueError(决策1, 旧 tol_mm 更名
    tol_model_mm, 模型毫米口径写进名字)。"""
    s = _check_scale(scale)
    pa, ma = entry_a
    pb, mb = entry_b
    Va = _xform(np.asarray(ma[0], dtype=float), pa)
    Vb = _xform(np.asarray(mb[0], dtype=float), pb)
    a_lo, a_hi = Va.min(axis=0), Va.max(axis=0)
    b_lo, b_hi = Vb.min(axis=0), Vb.max(axis=0)
    overlap = np.minimum(a_hi, b_hi) - np.maximum(a_lo, b_lo)
    if not np.all(overlap > 0.0):
        return {"ok": True, "issues": []}
    depth_mm = float(overlap.min()) * 1000.0   # 模型毫米
    if depth_mm > tol_model_mm:
        return {"ok": False,
                "issues": [_issue("PENETRATION",
                                  "overlap %.4fmm(model)=%.4fmm(printed) > tol %.3fmm"
                                  % (depth_mm, depth_mm * s, tol_model_mm))]}
    return {"ok": True, "issues": []}
