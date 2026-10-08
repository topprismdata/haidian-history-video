# -*- coding: utf-8 -*-
"""M18 逐块复刻砌石: 真·放射券石环 + 照片驱动拱肩/桥墩贴面砧石(数据+程序双路).

方法论(见 refs/masonry_method.md + 九审/用户 + M18 照片实测): 石拱桥不是光滑面
贴石纹, 而是一块块楔形券石(voussoir)绕拱心放射排布 + 中央龙门石, 桥墩/拱肩为
大块砧石错缝。本模块生成"贴面石"(facing stones)浮雕层, 覆盖在 bridge_body
前后墙面(y=±hw, 22° 收分):
  - voussoir_ring: 每孔 N 块放射楔石(N 奇, 中央=龙门石), 全深筒券, 放射缝;
  - coursing: [M18 重写] 三区贴面
      * 拱肩区(每孔 extrados 以上到桥面): 大块条石 1.0~1.8m 长块为主短块调剂,
        各层独立错缝; 贴拱一侧块沿 extrados+GAP_W 曲线切成曲边块(咬到券脸);
      * 墩区(两孔之间竖向带): 竖缝上下对直成列(照片实测非错缝), 同列同 x 边界;
      * 端区(|x|>72 桥头): 保留旧均匀错缝逻辑原样(冻结项)。
    块间留真实几何缝 GAP_W=10mm(露本体成暗线), 前脸凸出 STONE_PROUD。
    层高: 水线第一层 0.15~0.85 加高(照片近水线条石更高), 其上 0.50~0.63
    (2017-05-20 特写照实测 0.55±0.05m)。

[M18 数据驱动] 每孔砖谱 stones/stones_pX.json (X=0..8, 9..16 镜像复用):
有谱按谱精确落块, 无谱用上述程序布局兜底。坐标语义: x=桥轴系(与 PIER_X 同
原点同向, m), z=水面起算高(水面 z=0)。谱按键粒度生效: courses/pier/ring 各自
缺省时该项退程序兜底。格式:
  {"courses": [ {"z0": 层底z, "blocks": [x边界...] | "block_centers": [x中心...]} ],
   "pier":    {"cols": [x边界...], "courses": [z边界...]},      # 该孔左侧墩(PIER_X[i])
   "ring":    {"counts": N, "phase": rad}}                       # 券石缝数/冠部相位
纯 bmesh, 无外部网格/贴图。Python 3.9.6。
"""
import math
import os
import random
from bisect import bisect_right
import json

import bmesh

import bridge_geom2 as G

HERE = os.path.dirname(os.path.abspath(__file__))
STONES_DIR = os.environ.get("E30_STONES_DIR") or os.path.join(HERE, "stones")


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
RING_T = 0.54              # [七审P0-2] 券脸径向宽 0.62->0.54(-13%); STALE 分叉侧: facts.RING_T=0.40
                           # 已裁 STALE(2026-10-07 D2 停车线), 本值=券石账目 params.ring_t 真值,
                           # M20b 标定 ring_t(i) 后统一 —— 勿"对齐"到 0.40(券石几何冻结, core_hash 门)
JOINT = 0.02               # 灰缝 m(程序假缝; M18 起砧石真缝由 GAP_W 几何接管)
FACE_DEPTH = 0.006         # [M17x2] 0.03->0.006: 真照砧石齐口平缝
# [六审E] 券石改全深筒券: 内弧伸入洞口 BARREL_PROTRUDE, 邻块留放射缝 JOINT_GAP,
# 端面出墙面 FACE_PROUD(保留正面环带阴影)。
BARREL_PROTRUDE = 0.03
JOINT_GAP = 0.0125
JOINT_GAP_BACK = 0.004     # [七审P1-2] 放射缝前后端不等宽
FACE_PROUD = 0.004        # [M17c] 券石近齐口
COURSE_H = 0.40            # [M18 仅端区旧逻辑用] 旧均匀层高 m
COURSE_W = 0.90            # [M18 仅端区旧逻辑用] 旧均匀块宽 m

# ── [M18] 照片驱动砧石参数(2017-05-20 中央三孔特写实测, 见 .superpowers/sdd/m18-report.md) ──
GAP_W = 0.010              # 真实几何缝宽: 块间空缝露本体成暗线(照片缝 8~12mm)
STONE_PROUD = 0.008        # 砧石前脸凸出墙面(面微凸, 缝内露本体)
STONE_BACK = 0.30          # 背咬墙深(与本体无穿透缝)
BLOCK_W_MIN = 0.55         # 短块调剂下限
BLOCK_W_MAX = 1.80         # 长块上限(照片 1.0~1.8 为主)
COURSE_H_MIN = 0.50        # 主层高带下限(照片 0.55±)
COURSE_H_MAX = 0.63        # 主层高带上限
WATERLINE_Z0, WATERLINE_Z1 = 0.15, 0.85   # 水线加高层(照片近水块 ~0.7m)
PLINTH_TOP = 1.20          # 墩脚基石带顶(与 build_scene2 B1 一致, 砧石自此起砌)
MIN_KEEP_W = 0.30          # 残块宽 < 此值弃
MIN_KEEP_H = 0.22          # 残块高 < 此值弃(冠顶环带薄层除外)
COLLAR_H = 0.20            # 冠顶环带上方薄层高(照片 ~0.20m)
END_ZONE = 72.0            # |x|>72 端区走旧逻辑(桥头 massing 冻结)
ARC_STEP = 0.10            # 贴拱切块沿弧采样步长 m
# ── [M19] 起拱线出挑 impost 线脚(冬照+2017-05-20 特写: 每孔拱脚、墩顶之上阶梯
#    出挑承托层 2-3 阶, 出挑共 ~0.3m, 券环落于其上; M19 brief 拟合目标 高≈0.35) ──
# [十审E2] GPT: 原 3 阶 0.35/0.30 读成"独立承台牛腿"(出挑深/阶厚/间距大,
# 远看横向白带)。改: 4 皮逐级微挑(总高 0.28, 底阶出挑 0.17), 且每皮沿墩列线
# 分块(与墙石同一砌层语法), 不再整幅环带 extrusion。
# [十审E2b] 0.17/4阶仍读"悬浮板"(踏步深>>踢面高, 底影=缝感)。真照判读:
# 浅挑厚线脚, 总出挑<=0.10, 3 阶每阶 ~0.10 高 x ~0.033 挑(踢面主导)。
IMPOST_H = 0.30
IMPOST_PROJ = 0.10
IMPOST_STEPS = 3
IMPOST_BLOCK_W = 1.05      # 皮内分块名义宽(m)
IMPOST_MIN_Z = 0.02        # 没水阶不建(端孔起拱 0.26 近水, 阶没入水下部分省略)


def _arch_of(i):
    """第 i 孔几何参数 (xc, spz, a, b)。"""
    return ((G.PIER_X[i] + G.PIER_X[i + 1]) / 2.0, G.arch_springer_z(i),
            G.SPANS[i] / 2.0, G.arch_rise(i))


def _arch_normal(x, xc, springer, a, b):
    d = G.arch_dzdx(x, xc, springer, a, b)
    L = math.hypot(d, 1.0)
    return (-d / L, 1.0 / L)   # 指向拱外(上)


def _arc_stations(xc, a, b, springer, N):
    """按内弧等弧长取 N+1 个 x 站点(含两端)。"""
    M = 200
    xs = [xc - a + 2 * a * k / M for k in range(M + 1)]
    zs = [G.arch_z(x, xc, springer, 0.0 + a, b) for x in xs]
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


# ══ [M18] 砖谱(stones_pX.json)加载 ══

def _spec_path(i):
    return os.path.join(STONES_DIR, "stones_p%d.json" % i)


def _mirror_spec(spec):
    """镜像砖谱(x -> -x): 9..16 孔复用 8..0 的谱。边界序列取负后反序;
    ring 的 counts/phase 无方向语义, 直接复用。"""
    out = {}
    if "ring" in spec:
        out["ring"] = dict(spec["ring"])
    if "courses" in spec:
        cs = []
        for c in spec["courses"]:
            c2 = dict(c)
            for key in ("blocks", "block_centers"):
                if key in c2 and isinstance(c2[key], list):
                    c2[key] = [-v for v in reversed(c2[key])]
            cs.append(c2)
        out["courses"] = cs
    if "pier" in spec:
        p = dict(spec["pier"])
        if isinstance(p.get("cols"), list):
            p["cols"] = [-v for v in reversed(p["cols"])]
        out["pier"] = p
    return out


def _load_spec(i):
    """第 i 孔砖谱(0..8 直读, 9..16 镜像复用 p(16-i))。
    返回 dict 或 None(无谱/损坏 -> 程序兜底, 打印原因)。"""
    if not (0 <= i < G.N_SPAN):
        return None
    src = i if i <= 8 else 16 - i
    path = _spec_path(src)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r") as f:
            spec = json.load(f)
    except Exception as e:                       # 谱损坏: 兜底并留痕
        print("M18_SPEC_BAD p%d: %s -> 程序兜底" % (src, e))
        return None
    if not isinstance(spec, dict):
        print("M18_SPEC_BAD p%d: 根必须是 dict -> 程序兜底" % src)
        return None
    return _mirror_spec(spec) if i != src else spec


def _spec_blocks(c):
    """谱 course -> 该层块的 (x0,x1) 列表; 格式坏返回 None。
    blocks=边界序列(>=2, 递增); block_centers=中心序列(边界取相邻中心中点,
    端边界取半均距外推)。"""
    if "blocks" in c and isinstance(c["blocks"], list) and len(c["blocks"]) >= 2:
        bs = [float(v) for v in c["blocks"]]
        if any(bs[k + 1] - bs[k] <= 1e-6 for k in range(len(bs) - 1)):
            return None
        return [(bs[k], bs[k + 1]) for k in range(len(bs) - 1)]
    if "block_centers" in c and isinstance(c["block_centers"], list) \
            and len(c["block_centers"]) >= 2:
        cs = [float(v) for v in c["block_centers"]]
        if any(cs[k + 1] - cs[k] <= 1e-6 for k in range(len(cs) - 1)):
            return None
        step = abs(cs[1] - cs[0])
        edges = [cs[0] - step / 2.0]
        for k in range(len(cs) - 1):
            edges.append((cs[k] + cs[k + 1]) / 2.0)
        edges.append(cs[-1] + step / 2.0)
        return [(edges[k], edges[k + 1]) for k in range(len(cs))]
    return None


# ══ [M18] 拱洞+券环带连续判据与贴拱切块 ══

def _hole_cut_polyline(i, x0, x1):
    """第 i 孔『拱洞+券环带』的切割下沿: extrados(=intrados+RING_T)沿外法向
    再偏 GAP_W 的曲线, 采为 (x,z) 折线。拱脚处切线竖直, 偏置曲线以密采样表达
    陡降。返回 None = 该 x 段与孔无交。
    语义: 起拱线以下洞身由 _clip_jamb 竖直裁(xc±(a+GAP_W)); 起拱线处券石端
    承压面(z=spz, x∈[a, a+RING_T])下方的墙块顶面落在 zc(x)≈spz, 恰好托住券脚
    (照片: 贴拱块直接咬到券脸线脚边)。"""
    xc, spz, a, b = _arch_of(i)
    off = RING_T + GAP_W
    xdl, xdr = xc - a - off, xc + a + off
    if x1 <= xdl + 1e-9 or x0 >= xdr - 1e-9:
        return None
    n = max(24, int((2 * a) / ARC_STEP))
    # 等弧长采样: x 等步长在拱脚处一段跨 ~3m 高差, 弦切会慌报 zc(竖直陡降段
    # 被 chord 削平 -> 候选域漏排除)。等弧长步长处处 ~ARC_STEP, 弦差有界。
    xs_t, cum_t = _arc_cum_tables(xc, spz, a, b)
    total = cum_t[-1]
    pts = []
    for k in range(n + 1):
        s = total * k / n
        j = max(1, min(len(cum_t) - 1, bisect_right(cum_t, s)))
        f = (s - cum_t[j - 1]) / max(1e-9, cum_t[j] - cum_t[j - 1])
        x = xs_t[j - 1] + f * (xs_t[j] - xs_t[j - 1])
        if k == 0 or k == n:
            # 参数端点恰落在圆缘(dd=0, arch_dzdx 退化回 0, 法线塌成 0)。
            # 起拱线切线竖直, 外法向 = (∓1, 0): 直接钉住, 保证偏置曲线
            # 从 ±(a+off) 单调出发(_bottom_bound 依赖 x 单调)。
            pts.append((x - off if k == 0 else x + off, spz))
            continue
        z = G.arch_z(x, xc, spz, a, b)
        nx, nz = _arch_normal(x, xc, spz, a, b)
        pts.append((x + nx * off, z + nz * off))
    pts = [(px, pz) for (px, pz) in pts if x0 - 0.35 <= px <= x1 + 0.35]
    if len(pts) < 2:
        return None
    return pts


def _clip_jamb(i, x0, x1):
    """起拱线以下洞身竖直裁: 块 x 区间与 (xc-a-GAP_W, xc+a+GAP_W) 求交的补。
    返回裁后 (x0,x1); None = 整块落在洞身内(弃)。"""
    xc, spz, a, b = _arch_of(i)
    jl, jr = xc - a - GAP_W, xc + a + GAP_W
    if x1 <= jl or x0 >= jr:
        return (x0, x1)
    if x0 >= jl and x1 <= jr:
        return None
    if x0 < jl:
        return (x0, jl)
    return (jr, x1)


def _bottom_bound(x, cuts):
    """x 处块底边界(洞/环带切割下沿) = 各孔贡献的 max(无孔处 None)。
    cuts = [(pts, spz, a, xc)]: 
      - jamb 带(|x-xc|<a+GAP): 洞身到起拱线, 以上沿弧切割 -> 贡献 zc(x);
      - 承压带(a+GAP<=|x-xc|<=a+RING_T+GAP): 起拱线-GAP 以下是墙(座石区),
        切割封顶在 spz-GAP -> 贡献 min(zc(x), spz-GAP)。"""
    z = None
    for (pts, spz, a, xc) in cuts:
        if x < min(pts[0][0], pts[-1][0]) - 1e-9 \
                or x > max(pts[0][0], pts[-1][0]) + 1e-9:
            continue
        zc = None
        for k in range(len(pts) - 1):
            xa, xb = pts[k][0], pts[k + 1][0]
            if not (min(xa, xb) - 1e-9 <= x <= max(xa, xb) + 1e-9):
                continue
            dx = xb - xa
            if abs(dx) < 1e-12:                  # 竖直陡降段: 取高者(不咬环)
                v = max(pts[k][1], pts[k + 1][1])
            else:
                f = (x - xa) / dx
                v = pts[k][1] + f * (pts[k + 1][1] - pts[k][1])
            zc = v if zc is None else max(zc, v)
        if zc is None:
            continue
        if abs(x - xc) >= a + GAP_W:             # 承压带: 座石顶 spz-GAP 封顶
            zc = min(zc, spz - GAP_W)
        z = zc if z is None else max(z, zc)
    return z


# ══ [M18] 通用贴面块: 收分楔形 + 任意上下沿折线 ══

def _stone(bm, x0, x1, z0, z1, side, bottom=None, top=None,
           proud=STONE_PROUD, back=STONE_BACK, uv_x0=None, uv_z0=None):
    """M18 贴面砧石/拱肩块: 前脸逐顶点贴 hw(x,z)+proud(M17f _wedge 同规则的
    曲边推广; 22° 收分跟随), 背向墙内咬 back。bottom/top 为 [(x,z)...] 折线
    (x 递增; top 允许 R->L 传入后内部转环), None=平边。前后脸展平块局部米
    UV(u=x-uv_x0, v=z-uv_z0, 缝沿块界)。side=+1/-1 前后墙面。返回 True=落块。"""
    if x1 - x0 < 1e-4 or z1 - z0 < 1e-4:
        return False
    bot = list(bottom) if bottom else [(x0, z0), (x1, z0)]
    tp = list(top) if top else [(x1, z1), (x0, z1)]
    if bot[0][0] > x0 + 1e-6 or bot[-1][0] < x1 - 1e-6:
        return False
    ring = [(x, z) for (x, z) in bot]
    if abs(ring[-1][0] - tp[0][0]) > 1e-6 or abs(ring[-1][1] - tp[0][1]) > 1e-6:
        ring.append(tp[0])
    ring.extend(tp[1:])
    if abs(ring[-1][0] - ring[0][0]) > 1e-6 or abs(ring[-1][1] - ring[0][1]) > 1e-6:
        ring.append(ring[0])
    clean = [ring[0]]
    for p in ring[1:]:
        if abs(p[0] - clean[-1][0]) > 5e-4 or abs(p[1] - clean[-1][1]) > 5e-4:
            clean.append(p)
    if len(clean) > 2 and abs(clean[0][0] - clean[-1][0]) < 5e-4 \
            and abs(clean[0][1] - clean[-1][1]) < 5e-4:
        clean.pop()
    if len(clean) < 3:
        return False
    ux0 = uv_x0 if uv_x0 is not None else x0
    uz0 = uv_z0 if uv_z0 is not None else z0
    sgn = 1.0 if side > 0 else -1.0
    vf, vbk = [], []
    for (x, z) in clean:
        h = _hw(x, z)
        vf.append(bm.verts.new((x, sgn * (h + proud), z)))
        vbk.append(bm.verts.new((x, sgn * (h + proud - back), z)))
    m = len(clean)
    uv = bm.loops.layers.uv.active or bm.loops.layers.uv.new("UVMap")
    try:
        fc = bm.faces.new(vf)
        for lp in fc.loops:
            lp[uv].uv = (lp.vert.co.x - ux0, lp.vert.co.z - uz0)
    except ValueError:
        return False
    try:
        fc = bm.faces.new(list(reversed(vbk)))
        for lp in fc.loops:
            lp[uv].uv = (lp.vert.co.x - ux0, lp.vert.co.z - uz0)
    except ValueError:
        pass
    for k in range(m):
        k2 = (k + 1) % m
        try:
            bm.faces.new((vbk[k], vbk[k2], vf[k2], vf[k]))
        except ValueError:
            pass
    return True


def _wedge(bm, cx, hw_b, hw_t, cz, dx, dz, side, proud=0.006, back=0.30):
    """收分楔形砧石: 前脸随墙面 hw(z)+proud 倾斜, 背向墙内咬住。
    [M18] 端区(|x|>72)旧逻辑专用, 保持 M17f 原样(桥头贴面冻结)。"""
    x0, x1 = cx - dx / 2.0, cx + dx / 2.0
    z0, z1 = cz - dz / 2.0, cz + dz / 2.0
    if side > 0:
        f0, f1 = hw_b + proud, hw_t + proud
        b0, b1 = f0 - back, f1 - back
    else:
        f0, f1 = -(hw_b + proud), -(hw_t + proud)
        b0, b1 = f0 + back, f1 + back
    vs = [bm.verts.new(v) for v in (
        (x0, b0, z0), (x1, b0, z0), (x1, f0, z0), (x0, f0, z0),
        (x0, b1, z1), (x1, b1, z1), (x1, f1, z1), (x0, f1, z1))]
    uv = bm.loops.layers.uv.active or bm.loops.layers.uv.new("UVMap")
    for fi, f in enumerate(((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2),
                            (2, 6, 7, 3), (3, 7, 4, 0))):
        try:
            fc = bm.faces.new([vs[k] for k in f])
        except ValueError:
            continue
        if fi in (0, 1):  # 前后脸: 块局部米 UV(缝沿块界)
            for lp in fc.loops:
                lp[uv].uv = (lp.vert.co.x - x0, lp.vert.co.z - z0)


# ══ [M18] 三区 coursing ══

def _pier_xrange(k):
    """第 k 墩(k=1..16)面 x 范围。"""
    w = G.pier_w(k)
    return G.PIER_X[k] - w / 2.0, G.PIER_X[k] + w / 2.0


def _bay_xrange(i):
    """第 i 孔贴面区(左墩面到右墩面)。端区 |x|>72 冻结除外。"""
    w0 = G.BRIDGE_ABUT if i == 0 else G.pier_w(i)
    w1 = G.BRIDGE_ABUT if i == G.N_SPAN - 1 else G.pier_w(i + 1)
    x0 = G.PIER_X[i] + w0 / 2.0
    x1 = G.PIER_X[i + 1] - w1 / 2.0
    return max(x0, -END_ZONE), min(x1, END_ZONE)


def _hole_cuts_for(x0, x1):
    """与 x 区间相关的孔切割: [(pts, spz, a, xc)]。"""
    cuts = []
    for i in range(G.N_SPAN):
        xc, spz, a, b = _arch_of(i)
        pl = _hole_cut_polyline(i, x0, x1)
        if pl:
            cuts.append((pl, spz, a, xc))
    return cuts


def _deck_bound(x):
    """桥面下沿切割(仰天石底 deck-0.10, 再留 GAP_W)。"""
    return G.deck_z(min(max(x, -G.BRIDGE_LEN / 2), G.BRIDGE_LEN / 2)) - 0.10 - GAP_W


def _place_stone(bm, x0, x1, z0, z1, cuts,
                 min_h=MIN_KEEP_H, min_w=MIN_KEEP_W):
    """按洞/桥面边界落一块(前后墙各一): 含贴拱曲边底沿与桥面曲线顶沿裁切。
    返回 1/0。"""
    if x1 - x0 < min_w or z1 - z0 < 0.55 * min_h:
        return 0
    for i in range(G.N_SPAN):                    # 起拱线以下洞身竖直裁
        xc, spz, a, b = _arch_of(i)
        if z0 >= spz:
            continue                             # 全在起拱线上: 走底部曲线裁
        r = _clip_jamb(i, x0, x1)                # 跨起拱线的块也要裁(下段贴洞身)
        if r is None:
            return 0
        x0, x1 = r
    if x1 - x0 < min_w:
        return 0
    z_lo = z0
    bot = None
    zc_l = _bottom_bound(x0, cuts)
    zc_r = _bottom_bound(x1, cuts)
    if zc_l is not None or zc_r is not None:
        # 贴拱楔形块: 底沿逐 x 取 max(z0, zc) 且夹进 [z0,z1]; 只要存在一列
        # 剩余高 >= min_h 就落块(块在洞/环带内自然收尖), 全沉才弃。
        n = max(2, int((x1 - x0) / ARC_STEP) + 1)
        h_max = 0.0
        bot = []
        for k in range(n + 1):
            x = x0 + (x1 - x0) * k / n
            zc = _bottom_bound(x, cuts)
            if zc is None or zc >= z1 - 1e-9:
                zb = z0                             # 切割线在块顶以上: 不切
            else:
                zb = min(z1, max(z0, zc))
            h_max = max(h_max, z1 - zb)
            bot.append((x, zb))
        if h_max < min_h:
            return 0
        z_lo = min(b[1] for b in bot)
    top = None
    dk_l, dk_r = _deck_bound(x0), _deck_bound(x1)
    if dk_l < z1 - 1e-4 or dk_r < z1 - 1e-4:
        z_hi = min(z1, dk_l, dk_r)
        if z_hi - z_lo < min_h:
            # [M19] 桥面斜坡(冬照 camber 加陡 4.15->5.10)把坡缘块削成薄片: 整块弃
            # 会在桥面线下留 0.1~0.3m 露体带(_m18_verify 实测 109899 格), 改为
            # >=0.02 的找平薄片照落(贴坡曲线顶, 真桥檐下找平石同款); <0.02 弃。
            if z_hi - z_lo < 0.02:
                return 0
            min_h = z_hi - z_lo
        n = max(2, int((x1 - x0) / 0.15) + 1)
        top = []
        for k in range(n + 1):
            x = x0 + (x1 - x0) * k / n
            top.append((x, min(z1, _deck_bound(x))))
        top.reverse()                            # R->L 环序
        z1 = z_hi
    placed = 0
    for side in (1, -1):
        if _stone(bm, x0, x1, z_lo, z1, side, bottom=bot, top=top,
                  uv_x0=x0, uv_z0=z_lo):
            placed += 1
    # 券脚承压座石: 承压带(a+GAP..a+RING_T+GAP)内, 层跨 spz-GAP 时座石填
    # [z0, spz-GAP](其上为券脚承压面+环带, 由切割让开)。
    for (pts, spz, a, xc) in cuts:
        hl = spz - GAP_W
        if not (z0 < hl - 1e-4 < z1):
            continue
        for sgn in (-1, 1):
            bl = xc + sgn * (a + GAP_W)
            br = xc + sgn * (a + RING_T + GAP_W)
            u0, u1 = max(x0, min(bl, br)), min(x1, max(bl, br))
            if u1 - u0 < MIN_KEEP_W:
                continue
            for s2 in (1, -1):
                if _stone(bm, u0, u1, z0, hl, s2, uv_x0=u0, uv_z0=z0):
                    placed += 1
    return 2 if placed else 0


def _layout_spans(rng, span, short_p=0.18):
    """长块为主(1.0~1.8, 偏大)短块调剂(0.55~0.95)的伪随机宽度序列, 覆盖 span。"""
    spans = []
    x = 0.0
    while x < span - 1e-6:
        if rng.random() >= short_p:
            w = BLOCK_W_MIN + (BLOCK_W_MAX - BLOCK_W_MIN) * (rng.random() ** 0.8)
        else:
            w = 0.55 + 0.40 * rng.random()
        if span - x - w < BLOCK_W_MIN:           # 尾块不足: 并入末块
            w = span - x
        spans.append((x, x + w))
        x += w
    return spans


def _coursing_endzones(bm, hw_front, half_depth):
    """端区 |cx|>72 桥头贴面: M17f 均匀错缝布局原样(层高/错缝量冻结)。
    [M19 缺陷②修复] 落块由 _wedge(块内恒 y 平面脸, 块间 hw 台阶=百叶横纹残留)
    换 _stone(逐顶点贴 hw(x,z)+proud, 22° 收分随桥面曲线连续); 顶沿裁到
    deck-0.05(旧版整块跨过桥面线下, 端区 camber 加陡后露块顶入仰天石底)。"""
    n = 0
    z = 0.15
    row = 0
    while z < 8.2:
        xoff = (row % 2) * (COURSE_W / 2.0)
        x = -G.BRIDGE_LEN / 2.0 - 1.0 + xoff
        while x < G.BRIDGE_LEN / 2.0 + 1.0:
            cx = x + COURSE_W / 2.0
            cz = z + COURSE_H / 2.0
            deck_here = G.deck_z(min(max(cx, -G.BRIDGE_LEN / 2), G.BRIDGE_LEN / 2))
            in_body = abs(cx) <= G.BRIDGE_LEN / 2 + 1.3
            _m = COURSE_H / 2.0 + 0.02
            if in_body and abs(cx) > END_ZONE and cz < deck_here - 0.05 \
                    and not _in_arch(cx, cz, m=_m):
                z1 = min(z + COURSE_H, deck_here - 0.05)
                for side in (1, -1):
                    if _stone(bm, x, x + COURSE_W, z, z1, side,
                              uv_x0=x, uv_z0=z):
                        n += 1
            x += COURSE_W
        z += COURSE_H
        row += 1
    return n


def _in_arch(x, z, tol=0.0, m=0.0):
    """[M18 仅端区旧逻辑用] 点是否落在某孔拱洞(含券石环带)内。"""
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


def _pier_course_zs(rng, px0, px1):
    """墩区程序层高: 水线加高 + 墩脚带顶起 0.50~0.63 随机。
    层顶帽取墩内最大桥面-0.10(逐块桥面裁切吸收曲线差)。"""
    n_s = 8
    deck_top = max(G.deck_z(px0 + (px1 - px0) * k / (n_s - 1))
                   for k in range(n_s)) - 0.10
    zs = [WATERLINE_Z0, WATERLINE_Z1]
    z = PLINTH_TOP
    while z < min(7.6, deck_top - 0.05):
        z2 = z + COURSE_H_MIN + (COURSE_H_MAX - COURSE_H_MIN) * rng.random()
        zs.append(z2)
        z = z2
    if zs[-1] < deck_top - 0.02:                 # 闭合到桥面底(否则留露体带)
        zs.append(deck_top)
    return zs


def _coursing_piers(bm, specs):
    """墩区(16 内墩): 竖缝上下对直成列(照片实测非错缝), 同列同 x 边界。
    程序列: 每墩面内 2 列(三分), 谱 pier 键(cols/courses)可覆盖。
    谱归属: stones_pK.json 的 pier = 第 K 孔左侧墩 = 墩 K。"""
    n = 0
    for k in range(1, G.N_SPAN):
        px0, px1 = _pier_xrange(k)
        if px1 <= -END_ZONE or px0 >= END_ZONE:
            continue
        px0, px1 = max(px0, -END_ZONE), min(px1, END_ZONE)
        rng = random.Random(20261006 * 31 + k)
        cols = [px0 + (px1 - px0) * 0.34, px0 + (px1 - px0) * 0.67]
        zs = _pier_course_zs(rng, px0, px1)
        spec = specs.get(k) if specs else None
        if spec and isinstance(spec.get("pier"), dict):
            p = spec["pier"]
            if isinstance(p.get("cols"), list) and len(p["cols"]) >= 2:
                cand = sorted(float(v) for v in p["cols"])
                cols = [v for v in cand if px0 + 0.15 < v < px1 - 0.15]
            if isinstance(p.get("courses"), list) and len(p["courses"]) >= 2:
                zs = sorted(float(v) for v in p["courses"])
                # 数据路闭合保障: 谱层顶若低于桥面底, 补一道桥面帽(逐块裁切吸收曲线差)
                n_s = 8
                deck_cap = max(G.deck_z(px0 + (px1 - px0) * k2 / (n_s - 1))
                               for k2 in range(n_s)) - 0.10
                if zs[-1] < deck_cap - 0.02:
                    zs = zs + [deck_cap]
        bounds = [px0] + [c for c in sorted(set(cols)) if px0 < c < px1] + [px1]
        cuts = _hole_cuts_for(px0, px1)
        for ci in range(len(bounds) - 1):
            bx0 = bounds[ci] + (GAP_W / 2.0 if ci > 0 else 0.0)
            bx1 = bounds[ci + 1] - (GAP_W / 2.0 if ci + 1 < len(bounds) - 1 else 0.0)
            for zi in range(len(zs) - 1):
                bz0 = zs[zi] + (GAP_W / 2.0 if zi > 0 else 0.0)
                bz1 = zs[zi + 1] - (GAP_W / 2.0 if zi + 1 < len(zs) - 1 else 0.0)
                # 顶 course(贴桥面)残高<=0.02 的部分弃 -> 露体 <=20mm
                n += _place_stone(bm, bx0, bx1, bz0, bz1, cuts,
                                  min_h=(0.02 if zi + 2 == len(zs) else MIN_KEEP_H))
    return n


def _bay_course_zs(rng, bx0, bx1):
    """拱肩区程序层高: 水线加高后连续砌筑(腹孔间墙无墩脚带, 不得跳层) 0.50~0.63
    随机。层顶帽取湾内**最大**桥面-0.10(曲线差由逐块桥面裁切吸收, 若取 min 会在
    湾中段留 ~0.3m 露体带)。"""
    n = 16
    deck_top = max(G.deck_z(bx0 + (bx1 - bx0) * k / (n - 1)) for k in range(n)) - 0.10
    zs = [WATERLINE_Z0, WATERLINE_Z1]
    z = WATERLINE_Z1
    while z < deck_top - 0.05:
        z2 = z + COURSE_H_MIN + (COURSE_H_MAX - COURSE_H_MIN) * rng.random()
        zs.append(min(z2, deck_top))
        z = z2
    zs.append(deck_top)
    return sorted(set(zs))


def _coursing_bays(bm, specs):
    """拱肩区+腹孔间实腹墙: 大块条石各层独立错缝, 贴拱块沿 extrados+GAP_W
    切弧(块直接咬到券脸, 露体带=一条 GAP_W 缝)。谱 courses 键逐层覆盖。"""
    n = 0
    for i in range(G.N_SPAN):
        bx0, bx1 = _bay_xrange(i)
        if bx1 - bx0 < 0.4:
            continue
        n_s = 16
        deck_top = max(G.deck_z(bx0 + (bx1 - bx0) * k / (n_s - 1))
                       for k in range(n_s)) - 0.10
        cuts = _hole_cuts_for(bx0, bx1)
        courses = None
        spec = specs.get(i) if specs else None
        if spec and isinstance(spec.get("courses"), list):
            courses = []
            for c in spec["courses"]:
                if not isinstance(c, dict) or "z0" not in c:
                    continue
                bl = _spec_blocks(c)
                if bl:
                    courses.append((float(c["z0"]), bl))
            courses.sort()
            if not courses:
                courses = None
        if courses:
            for ci, (z0, blocks) in enumerate(courses):
                z1 = courses[ci + 1][0] if ci + 1 < len(courses) else deck_top
                if z1 - z0 < 0.05:
                    continue
                for (u0, u1) in blocks:
                    a0, a1 = max(u0, bx0), min(u1, bx1)
                    if a1 - a0 < 0.05:
                        continue
                    n += _place_stone(bm, a0, a1, z0 + GAP_W / 2.0,
                                      z1 - (GAP_W / 2.0 if ci + 1 < len(courses)
                                            else 0.0),
                                      cuts, min_h=0.02)
        else:
            rng = random.Random(20261006 * 17 + i)
            zbounds = _bay_course_zs(rng, bx0, bx1)
            for zi in range(len(zbounds) - 1):
                za, zb = zbounds[zi], zbounds[zi + 1]
                thin = (zb - za) < 0.35           # 冠顶环带薄层
                last = (zi + 1 == len(zbounds) - 1)
                shift = rng.random() * 1.2        # 各层独立错缝起点
                pending = None
                spans = []
                for (u0, u1) in _layout_spans(rng, (bx1 - bx0) + 1.2):
                    a0 = max(bx0, bx0 - shift + u0)
                    a1 = min(bx1, bx0 - shift + u1)
                    if a1 - a0 < 1e-9:
                        continue
                    # 先做边界缝调整, 用**有效宽**判残块(否则 302mm 块调后
                    # 297mm 会被 _place_stone 弃掉, 在墩面留 300mm 露体带)
                    a0p = a0 + (GAP_W / 2.0 if a0 > bx0 + 1e-9 else 0.0)
                    a1p = a1 - (GAP_W / 2.0 if a1 < bx1 - 1e-9 else 0.0)
                    if a1p - a0p < MIN_KEEP_W:
                        if spans:
                            spans[-1] = (spans[-1][0], a1p)
                        else:
                            pending = a0p
                            continue
                    else:
                        if pending is not None:
                            a0p = pending
                            pending = None
                        spans.append((a0p, a1p))
                for (a0, a1) in spans:
                    if a1 - a0 < MIN_KEEP_W:
                        continue
                    bz0 = za + (GAP_W / 2.0 if zi > 0 else 0.0)
                    bz1 = zb - (GAP_W / 2.0 if zi + 1 < len(zbounds) - 1 else 0.0)
                    # spans 内已是边界缝调整后的有效区间(湾缘齐平, 内缝 GAP)
                    # 顶 course(贴桥面)残高<=0.02 的部分弃 -> 露体 <=20mm
                    n += _place_stone(bm, a0, a1, bz0, bz1, cuts,
                                      min_h=(0.02 if last else
                                             (COLLAR_H if thin else MIN_KEEP_H)))
    return n


def build_impost(bm):
    """[M19] 起拱线出挑 impost 线脚: 每孔两券脚下、墩/桥台前脸之上的阶梯出挑
    承托层(3 阶, 总高 IMPOST_H, 底阶出挑 IMPOST_PROJ 向上递减), 券环落于其上
    (顶面 = spz-GAP 床缝, 与承压座石同一承压面)。逐孔随 arch_springer_z,
    x 覆盖 [券脚内缘-咬合, 墩外面](桥台侧到本体端 |x|=75); 没水阶不建
    (端孔起拱近水)。前脸逐顶点贴 hw(x,z)(22° 收分跟随), 背咬 STONE_BACK。
    返回块数(前后墙合计)。"""
    n = 0
    for i in range(G.N_SPAN):
        xc = (G.PIER_X[i] + G.PIER_X[i + 1]) / 2.0
        a = G.SPANS[i] / 2.0
        hl = G.arch_springer_z(i) - GAP_W
        for sgn in (-1, 1):
            # 开孔侧界 = 券脚内缘 fx(起拱线处 intrados 切线近竖直, 越界即悬进洞口
            # 空气 -> 必须齐平); 墩侧界 = 墩外面(桥台侧 = 本体端 |x|=75)。
            fx = xc + sgn * a
            if sgn > 0:
                k = i + 1
                w_out = G.BRIDGE_ABUT if k == G.N_SPAN else G.pier_w(k)
                px_out = G.PIER_X[k] + w_out / 2.0
            else:
                k = i
                w_out = G.BRIDGE_ABUT if k == 0 else G.pier_w(k)
                px_out = G.PIER_X[k] - w_out / 2.0
            x0, x1 = min(fx, px_out), max(fx, px_out)
            x0 = max(x0, -G.BRIDGE_LEN / 2.0)
            x1 = min(x1, G.BRIDGE_LEN / 2.0)
            if x1 - x0 < 0.10:
                continue
            for st in range(IMPOST_STEPS):
                z1 = hl - IMPOST_H * st / IMPOST_STEPS
                z0 = hl - IMPOST_H * (st + 1) / IMPOST_STEPS
                if z1 <= IMPOST_MIN_Z:
                    break
                proj = IMPOST_PROJ * (st + 1) / IMPOST_STEPS
                zb0 = max(z0, IMPOST_MIN_Z)
                if z1 - zb0 < 0.02:
                    continue
                # [十审E2] 皮内分块: 沿 x 按名义宽切段, 奇偶皮错半块(与墩身
                # 砧石同一错缝语法), 块界=真缝 -> 线脚读成砌层不是环带
                segs = []
                off = (st % 2) * IMPOST_BLOCK_W * 0.5
                xs = x0 + off
                while xs < x1:
                    xe = min(xs + IMPOST_BLOCK_W, x1)
                    if xe - xs >= 0.25:
                        segs.append((xs, xe))
                    xs = xe
                if not segs:
                    segs = [(x0, x1)]
                for (sx0, sx1) in segs:
                    for side in (1, -1):
                        if _stone(bm, sx0, sx1, zb0, z1, side,
                                  proud=STONE_PROUD + proj,
                                  back=STONE_BACK + proj,
                                  uv_x0=sx0, uv_z0=zb0):
                            n += 1
    return n


def build_coursing(bm, hw_front, half_depth):
    """桥墩/桥台/拱肩贴面砧石(M18 三区: 端区冻结旧逻辑 + 墩对直列 + 拱肩大块
    错缝贴拱切块; stones_pX.json 数据路优先, 程序兜底)。返回块数(前后墙合计)。"""
    specs = {}
    for i in range(G.N_SPAN):
        s = _load_spec(i)
        if s:
            specs[i] = s
            print("M18_SPEC p%d <- stones_p%d.json" % (i, i if i <= 8 else 16 - i))
    n_end = _coursing_endzones(bm, hw_front, half_depth)
    n_pier = _coursing_piers(bm, specs)
    n_bay = _coursing_bays(bm, specs)
    n_imp = build_impost(bm)
    build_coursing.region_counts = {"endzone": n_end, "pier": n_pier, "bay": n_bay,
                                    "impost": n_imp}
    print("M18_COURSING endzone=%d pier=%d bay=%d impost=%d" % (n_end, n_pier, n_bay, n_imp))
    return n_end + n_pier + n_bay + n_imp


def _arc_cum_tables(xc, spz, a, b, M=400):
    """内弧累计弧长表(用于相位偏移的 s<->x 互查)。"""
    xs = [xc - a + 2 * a * k / M for k in range(M + 1)]
    cum = [0.0]
    for k in range(1, len(xs)):
        z0 = G.arch_z(xs[k - 1], xc, spz, a, b)
        z1 = G.arch_z(xs[k], xc, spz, a, b)
        cum.append(cum[-1] + math.hypot(xs[k] - xs[k - 1], z1 - z0))
    return xs, cum


def _phase_shift(st, xc, spz, a, b, phase):
    """环缝相位: phase(rad, 名义半张角度量)换算弧长偏移施加于内部缝;
    端点钉在起拱线, 端块保 6% 弧长。"""
    xs, cum = _arc_cum_tables(xc, spz, a, b)
    total = cum[-1]
    theta = math.atan2(a, b)                     # 名义半张角(>0)
    ds = phase * total / (2.0 * theta)
    lo, hi = total * 0.06, total * 0.94

    def s_of(x):
        k = bisect_right(xs, x)
        k = max(1, min(k, len(xs) - 1))
        f = (x - xs[k - 1]) / max(1e-9, xs[k] - xs[k - 1])
        return cum[k - 1] + f * (cum[k] - cum[k - 1])

    def x_of(s):
        k = bisect_right(cum, s)
        k = max(1, min(k, len(cum) - 1))
        f = (s - cum[k - 1]) / max(1e-9, cum[k] - cum[k - 1])
        return xs[k - 1] + f * (xs[k] - xs[k - 1])

    out = [st[0]]
    for x in st[1:-1]:
        out.append(x_of(min(hi, max(lo, s_of(x) + ds))))
    out.append(st[-1])
    return out


def build_voussoir(bm, hw_front, half_depth):
    """17 孔圆弧券石环(全深筒券; 拱线族返工 2026-10-08 前为尖拱)。块数: 谱 ring.counts > VOUSSOIR_TARGET 兜底;
    ring.phase(rad) 转弧长偏移施加于内部缝。返回每孔块数。"""
    counts = []
    for i in range(G.N_SPAN):
        a = G.SPANS[i] / 2.0
        xc = (G.PIER_X[i] + G.PIER_X[i + 1]) / 2.0
        spz = G.arch_springer_z(i)
        b = G.arch_rise(i)
        N = voussoir_count(a, b, i)
        phase = 0.0
        spec = _load_spec(i)
        if spec and isinstance(spec.get("ring"), dict):
            rc = spec["ring"].get("counts")
            if isinstance(rc, int) and rc >= 5:
                N = rc | 1
            ph = spec["ring"].get("phase")
            if isinstance(ph, (int, float)):
                phase = float(ph)
        counts.append(N)
        st = _arc_stations(xc, a, b, spz, N)
        if abs(phase) > 1e-9 and N > 3:
            st = _phase_shift(st, xc, spz, a, b, phase)
        for k in range(N):
            _voussoir(bm, st[k], st[k + 1], xc, spz, a, b, RING_T,
                      lift=0.07 if k == N // 2 else 0.0)
    return counts


def build_masonry(hw_front, half_depth=FACE_DEPTH):
    """返回 (voussoir_bm, coursing_bm, stats)。键与 M17 相同
    (voussoir_per_arch/voussoir_total/coursing_total/grand_total),
    新增 coursing_regions 与 spec_arches。"""
    vb = bmesh.new()
    vcounts = build_voussoir(vb, hw_front, half_depth)
    cb = bmesh.new()
    ncourse = build_coursing(cb, hw_front, half_depth)
    regions = dict(getattr(build_coursing, "region_counts", {}))
    spec_arches = sorted(i for i in range(G.N_SPAN) if _load_spec(i))
    stats = dict(voussoir_per_arch=vcounts, voussoir_total=sum(vcounts),
                 coursing_total=ncourse,
                 grand_total=sum(vcounts) + ncourse,
                 coursing_regions=regions, spec_arches=spec_arches)
    return vb, cb, stats
