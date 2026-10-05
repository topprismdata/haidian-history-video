# -*- coding: utf-8 -*-
"""M13 逐块砌筑: 真·放射券石环 + 桥墩/拱肩贴面砧石错缝层.

方法论(见 refs/masonry_method.md + 九审/用户): 石拱桥不是光滑面贴石纹, 而是
一块块楔形券石(voussoir)绕拱心放射排布 + 中央龙门石, 桥墩/拱肩为矩形砧石错缝。
本模块生成"贴面石"(facing stones)浮雕层, 覆盖在 bridge_body 前后墙面(y=±hw):
  - voussoir_ring: 每孔 N 块放射楔石(N 奇, 中央=龙门石), 内窄外宽梯形, 留灰缝;
  - coursing: 桥墩/桥台/拱肩墙矩形砧石, running bond 错缝, 按拱洞+券石环+桥面曲线剔除。
纯 bmesh, 无外部网格/贴图。Python 3.9.6。
所有尺寸可由参数覆盖; 默认按十七孔桥实测(见 masonry_method.md)与照片比例。
"""
import math

import bmesh

import bridge_geom2 as G


def _hw(x, z):
    """桥体收分墙面在 (x,z) 的半宽(贴面石落点)。"""
    xc = min(max(x, -G.BRIDGE_LEN / 2), G.BRIDGE_LEN / 2)
    deck = G.deck_z(xc)
    f = max(0.0, min(1.0, (z - G.BODY_BOTTOM) / (deck - G.BODY_BOTTOM)))
    return (G.DECK_DOWN_W + (G.DECK_UP_W - G.DECK_DOWN_W) * f) / 2.0

# ── 砌石参数(masonry_method.md 回填前用照片比例工作值) ──
VOUSSOIR_FACE_W = 1.00      # 券石沿内弧面宽 m(masonry_method 照片券缝检测锚定: 端7/主13)
RING_T = 0.62              # 券石径向厚(=券脸环带宽) m
JOINT = 0.02               # 灰缝 m
FACE_DEPTH = 0.12          # 贴面石出墙面深度 m
COURSE_H = 0.40            # 砧石层高 m
COURSE_W = 0.90            # 砧石宽 m


def _ellipse_pt(xc, spz, a, b, t):
    return (xc + a * math.cos(t), spz + b * math.sin(t))


def voussoir_count(a, b):
    """内弧半周长按 Ramanujan 近似 ÷ 面宽, 取奇数(留中央龙门石)。"""
    h = ((a - b) ** 2) / ((a + b) ** 2)
    per_half = 0.5 * math.pi * (a + b) * (1 + 3 * h / (10 + math.sqrt(4 - 3 * h)))
    n = max(9, int(round(per_half / VOUSSOIR_FACE_W)))
    return n | 1  # 奇数


def _wedge(bm, xc, spz, a, b, t0, t1, side, half_depth, ring_t, lift=0.0):
    """一块放射楔石: 角域[t0,t1], 内椭圆(a,b)->外(a+ring_t,b+ring_t), y[y0,y1]。
    lift: 龙门石径向外凸量。返回 True。"""
    ts = (t0, (t0 + t1) / 2.0, t1)
    inner = [_ellipse_pt(xc, spz, a, b, t) for t in ts]
    outer = [_ellipse_pt(xc, spz, a + ring_t + lift, b + ring_t + lift, t) for t in ts]
    ring = inner + list(reversed(outer))
    # 贴合收分: 每块按其 z 取墙半宽, 贴面石落在墙面外侧 half_depth 带内
    zs = [z for _, z in ring]
    zmid = sum(zs) / len(zs)
    hw = _hw(xc, zmid)
    y0 = side * hw - (half_depth if side > 0 else 0.0)
    y1 = side * hw + (half_depth if side > 0 else 0.0)
    va = [bm.verts.new((x, y0, z)) for x, z in ring]
    vb = [bm.verts.new((x, y1, z)) for x, z in ring]
    m = len(ring)
    for k in range(m):
        k2 = (k + 1) % m
        try:
            bm.faces.new((va[k], va[k2], vb[k2], vb[k]))
        except ValueError:
            pass
    try:
        bm.faces.new(list(reversed(va)))
        bm.faces.new(vb)
    except ValueError:
        pass
    return True


def build_voussoir(bm, hw_front, half_depth):
    """17 孔券石环(前后两面)。返回每孔块数列表。"""
    counts = []
    for i in range(G.N_SPAN):
        a = G.SPANS[i] / 2.0
        xc = (G.PIER_X[i] + G.PIER_X[i + 1]) / 2.0
        spz = G.arch_springer_z(i)
        b = G.arch_rise(i)
        N = voussoir_count(a, b)
        counts.append(N)
        dth = math.pi / N
        jt = JOINT / max(a, 0.5)  # 角向缝宽近似
        for side in (1, -1):
            for k in range(N):
                t0 = k * dth + jt
                t1 = (k + 1) * dth - jt
                is_key = (k == N // 2)
                _wedge(bm, xc, spz, a, b, t0, t1, side, half_depth, RING_T,
                       lift=0.06 if is_key else 0.0)
    return counts


def _in_arch(x, z, tol=0.0, m=0.0):
    """点是否落在某孔拱洞(含券石环带)内。返回 True=在洞/环区(不放砧石)。"""
    for i in range(G.N_SPAN):
        a = G.SPANS[i] / 2.0 + RING_T + 0.05 + m
        xc = (G.PIER_X[i] + G.PIER_X[i + 1]) / 2.0
        spz = G.arch_springer_z(i)
        b = G.arch_rise(i) + RING_T + 0.05 + m
        if abs(x - xc) < a and z > spz - (G.SPRINGER - spz) - 0.1:
            dz = z - spz
            if dz >= 0 and ((x - xc) / a) ** 2 + (dz / b) ** 2 < 1.0:
                return True
            if dz < 0 and abs(x - xc) < a:  # 起拱线以下矩形洞身
                return True
    return False


def build_coursing(bm, hw_front, half_depth):
    """桥墩/桥台/拱肩贴面砧石, running bond。返回块数。"""
    n = 0
    z = 0.15  # 水线以上起砌
    row = 0
    while z < 8.2:
        # 该行 x 起点错缝: 奇数行偏移半块
        xoff = (row % 2) * (COURSE_W / 2.0)
        x = -G.BRIDGE_LEN / 2.0 - 1.0 + xoff
        while x < G.BRIDGE_LEN / 2.0 + 1.0:
            cx = x + COURSE_W / 2.0
            cz = z + COURSE_H / 2.0
            # 桥面曲线: 砧石顶不得超桥面; 且需在桥体收分轮廓内
            deck_here = G.deck_z(min(max(cx, -G.BRIDGE_LEN / 2), G.BRIDGE_LEN / 2))
            in_body = abs(cx) <= G.BRIDGE_LEN / 2 + 1.3
            _m = max(COURSE_W, COURSE_H) / 2.0
            if in_body and cz < deck_here - 0.05 and not _in_arch(cx, cz, m=_m):
                for side in (1, -1):
                    hw = _hw(cx, cz)
                    yb = side * hw - (half_depth if side > 0 else 0.0)
                    _box(bm, cx, min(yb, yb + half_depth), cz, COURSE_W, half_depth, COURSE_H)
                    n += 1
            x += COURSE_W
        z += COURSE_H
        row += 1
    return n


def _box(bm, xc, yc, zc, dx, dy, dz):
    x0, x1 = xc - dx / 2, xc + dx / 2
    y0, y1 = yc, yc + dy
    z0, z1 = zc - dz / 2, zc + dz / 2
    vs = [bm.verts.new(p) for p in (
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))]
    for f in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2),
              (2, 6, 7, 3), (3, 7, 4, 0)):
        try:
            bm.faces.new([vs[k] for k in f])
        except ValueError:
            pass


def build_masonry(hw_front, half_depth=FACE_DEPTH):
    """返回 (voussoir_bm, coursing_bm, stats)。"""
    vb = bmesh.new()
    vcounts = build_voussoir(vb, hw_front, half_depth)
    cb = bmesh.new()
    ncourse = build_coursing(cb, hw_front, half_depth)
    stats = dict(voussoir_per_arch=vcounts, voussoir_total=sum(vcounts) * 2,
                 coursing_total=ncourse,
                 grand_total=sum(vcounts) * 2 + ncourse)
    return vb, cb, stats
