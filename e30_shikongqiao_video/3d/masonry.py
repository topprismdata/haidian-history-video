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
VOUSSOIR_FACE_W = 1.00      # 兜底面宽(仅当目标表缺项时用)
# [masonry_method 照片券缝计数] 每孔券石目标块数, 按|孔位-中央|索引: 中央17, 端7。
# 统一面宽数学上给不出 7/17 两端(弧长比2.19≠块数比2.43)——真桥端孔块更宽, 故按孔给定。
VOUSSOIR_TARGET = [17, 15, 13, 13, 11, 11, 9, 9, 7]
RING_T = 0.54              # [七审P0-2] 券脸径向宽 0.62->0.54(-13%): '轻一点的券环+更大孔占比', 厚重感一半来自环太宽
JOINT = 0.02               # 灰缝 m
FACE_DEPTH = 0.006         # [M17x2] 0.03->0.006: 真照砧石齐口平缝, 3cm 侧壁在掠射光仍投影成块影
# [六审E] 券石改全深筒券: 真桥透洞可见阶梯状环石内壁, 原"前后薄浮雕"读成
# "正立面开孔+光滑内筒"。内弧伸入洞口 BARREL_PROTRUDE, 邻块留放射缝 JOINT_GAP,
# 端面出墙面 FACE_PROUD(保留正面环带阴影)。
BARREL_PROTRUDE = 0.03
JOINT_GAP = 0.0125
JOINT_GAP_BACK = 0.004     # [七审P1-2] 放射缝前后端不等宽: 前脸 0.0125, 内壁
                           #   0.004 → 深度权重 100→~35, 去"洋葱圈隧道"感
FACE_PROUD = 0.004        # [M17c] 0.02->0.004: 券石出挑2cm侧壁在掠射光下投影成暗三角(拱肩棋盘最后残留), 真照券脸近齐平
COURSE_H = 0.40            # 砧石层高 m
COURSE_W = 0.90            # 砧石宽 m


def _arch_normal(x, xc, springer, a, b):
    d = G.arch_dzdx(x, xc, springer, a, b)
    L = math.hypot(d, 1.0)
    return (-d / L, 1.0 / L)   # 指向拱外(上)


def _arc_stations(xc, a, b, springer, N):
    """按内弧等弧长取 N+1 个 x 站点(含两端)。"""
    M = 200
    xs = [xc - a + 2 * a * k / M for k in range(M + 1)]
    zs = [G.arch_z(x, xc, springer, 0.0 + a, b) for x in xs]
    # 用 arch_z 需 springer; 上面 springer=0 占位, 仅取相对弧长
    cum = [0.0]
    for k in range(1, len(xs)):
        cum.append(cum[-1] + math.hypot(xs[k]-xs[k-1], zs[k]-zs[k-1]))
    total = cum[-1]
    st = [xs[0]]
    for j in range(1, N):
        target = total * j / N
        for k in range(1, len(cum)):
            if cum[k] >= target:
                f = (target - cum[k-1]) / max(1e-9, cum[k]-cum[k-1])
                st.append(xs[k-1] + f*(xs[k]-xs[k-1])); break
    st.append(xs[-1])
    return st


def _voussoir(bm, x0, x1, xc, springer, a, b, ring_t, lift=0.0):
    """一块全深放射券石: 内弧伸入洞口 BARREL_PROTRUDE(阶梯筒子券),
    外弧沿法向 ring_t+lift, 端面沿法向(放射缝), y 向贯通全墙并出墙面 FACE_PROUD。"""
    def _ring(x0f, x1f):
        ts = (x0f, (x0f+x1f)/2.0, x1f)
        inner, outer = [], []
        for x in ts:
            z = G.arch_z(x, xc, springer, a, b)
            nx, nz = _arch_normal(x, xc, springer, a, b)
            inner.append((x - nx*BARREL_PROTRUDE, z - nz*BARREL_PROTRUDE))
            outer.append((x + nx*(ring_t+lift), z + nz*(ring_t+lift)))
        return inner + list(reversed(outer))
    rf = _ring(x0 + JOINT_GAP, x1 - JOINT_GAP)          # 前脸环(缝宽)
    rb = _ring(x0 + JOINT_GAP_BACK, x1 - JOINT_GAP_BACK)  # 内壁环(缝窄→衰减)
    zs = [z for _, z in rf]; zmid = sum(zs)/len(zs)
    hw = _hw(xc, zmid)
    y0, y1 = -(hw + FACE_PROUD), hw + FACE_PROUD
    va = [bm.verts.new((x, y0, z)) for x, z in rb]
    vb = [bm.verts.new((x, y1, z)) for x, z in rf]
    m = len(rf)
    for k in range(m):
        k2 = (k+1) % m
        try: bm.faces.new((va[k], va[k2], vb[k2], vb[k]))
        except ValueError: pass
    try:
        bm.faces.new(list(reversed(va))); bm.faces.new(vb)
    except ValueError: pass


def voussoir_count(a, b, i=None):
    """第 i 孔券石块数: 优先照片计数目标表(奇数, 中央留龙门石), 无 i 时退 Ramanujan÷面宽。"""
    if i is not None and 0 <= i < G.N_SPAN:
        return VOUSSOIR_TARGET[abs(i - (G.N_SPAN - 1) // 2)]
    h = ((a - b) ** 2) / ((a + b) ** 2) if (a+b) > 0 else 0
    per_half = 0.5 * math.pi * (a + b) * (1 + 3*h/(10 + math.sqrt(4 - 3*h)))
    n = max(7, int(round(per_half / VOUSSOIR_FACE_W)))
    return n | 1


def build_voussoir(bm, hw_front, half_depth):
    """17 孔尖拱券石环(全深筒券, 每块贯通墙厚)。返回每孔块数。
    hw_front/half_depth 保留签名兼容, 全深模式下不再使用。"""
    counts = []
    for i in range(G.N_SPAN):
        a = G.SPANS[i] / 2.0
        xc = (G.PIER_X[i] + G.PIER_X[i + 1]) / 2.0
        spz = G.arch_springer_z(i)
        b = G.arch_rise(i)
        N = voussoir_count(a, b, i)
        counts.append(N)
        st = _arc_stations(xc, a, b, spz, N)
        for k in range(N):
            _voussoir(bm, st[k], st[k+1], xc, spz, a, b, RING_T,
                      lift=0.07 if k == N//2 else 0.0)
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
            _m = COURSE_H / 2.0 + 0.02  # [M17b] 0.08->0.02: 真照拱肩砧石直接切进券环线, 露体带=一条缝宽
            if in_body and cz < deck_here - 0.05 and not _in_arch(cx, cz, m=_m):
                for side in (1, -1):
                    hw = _hw(cx, cz)
                    yb = side * hw - (half_depth if side > 0 else 0.0)
                    _box(bm, cx, min(yb, yb + half_depth), cz, COURSE_W, half_depth, COURSE_H,
                         uv_face=(cx - COURSE_W / 2.0, cz - COURSE_H / 2.0))
                    n += 1
            x += COURSE_W
        z += COURSE_H
        row += 1
    return n


def _box(bm, xc, yc, zc, dx, dy, dz, uv_face=None):
    """uv_face=(u0,z0): 传入则前脸(+Y)展平到块局部 UV(缝沿块界, 不跨块)。"""
    x0, x1 = xc - dx / 2, xc + dx / 2
    y0, y1 = yc, yc + dy
    z0, z1 = zc - dz / 2, zc + dz / 2
    vs = [bm.verts.new(p) for p in (
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))]
    uv = bm.loops.layers.uv.active or bm.loops.layers.uv.new("UVMap")
    for fi, f in enumerate(((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2),
                            (2, 6, 7, 3), (3, 7, 4, 0))):
        try:
            fc = bm.faces.new([vs[k] for k in f])
        except ValueError:
            continue
        if uv_face is not None and fi in (0, 1):  # 前后脸都展平(桥两侧各有朝外脸)
            u0, z0 = uv_face
            # v[0..3]=(x0,y0,z0),(x1,..),(x1,y1,z0)... 前脸按局部米展平
            for lp in fc.loops:
                vi = lp.vert.index if hasattr(lp.vert, "index") else 0
                lx = lp.vert.co.x - u0
                lz = lp.vert.co.z - z0
                lp[uv].uv = (lx, lz)


def build_masonry(hw_front, half_depth=FACE_DEPTH):
    """返回 (voussoir_bm, coursing_bm, stats)。"""
    vb = bmesh.new()
    vcounts = build_voussoir(vb, hw_front, half_depth)
    cb = bmesh.new()
    ncourse = build_coursing(cb, hw_front, half_depth)
    stats = dict(voussoir_per_arch=vcounts, voussoir_total=sum(vcounts),
                 coursing_total=ncourse,
                 grand_total=sum(vcounts) + ncourse)
    return vb, cb, stats
