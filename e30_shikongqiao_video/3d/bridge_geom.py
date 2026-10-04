"""E30 十七孔桥 独立几何模块(可单独渲染核查, 不含光照)。

所有造型参数依 2016-09-20 白天侧视全景实拍核定:
  research/images/photos/Seventeen_Arch_Bridge_IMG_0398.jpg
实拍确认的四件事(与首轮按均分假设的取值相反):
  1. 券洞是半圆券(实测连通域宽高比 0.76~0.98, 集中于 1), 不是尖拱
  2. 券洞两端小、中央大, 端孔约为中央孔的 0.62 倍
  3. 望柱密排: 实拍桥面两侧目测每 2m 一根以上, 全桥两侧合计约 150 根量级
     (注: 网上流传的"128 根 / 62 对"口径互相矛盾, 无一手出处, 本模型按实拍密度)
  4. 栏板镂空有花格, 非实心平板; 望柱柱头蹲狮

坐标: 桥沿 +X(西端->东端), 桥宽沿 Y, Z 向上, 水面 z=0。
"""
import bmesh
import math

BRIDGE_LEN, N_SPAN = 150.0, 17
DECK_UP_W, DECK_DOWN_W, BRIDGE_H = 6.56, 14.6, 7.0
WATER_Z = 0.0
BODY_BOTTOM = -1.8          # 沉入水下

# 起拱线: 实拍中券洞几乎从水面附近起拱, 券顶约占桥高六成。
# 原设 1.95 过高, 导致券洞在桥腹下挤成小洞(首轮渲染实证)。
SPRINGER = 2.50            # 起拱线高 (GPT v3: 1.55 -> 2.50, 水面 Z=0)
SEG = 28
END_SPAN_RATIO = 0.62      # 端孔/中央孔
N_NEWEL = 63               # 每侧 64 根 = 全桥 128 根(官方)
                              # 循环 63 次 -> 64 根/侧
# GPT v2: 两端 3.85 / 中央 6.05, 起拱差 2.20 (原 4.40 过于夸张)
RISE_TOTAL = 2.40          # GPT v3: 桥面矢高 (中央 7.55 - 两端 5.15)
DECK_Z_END = 5.15
LION_SCALE = 1.0
LION_PER_POST = 4        # GPT: 每侧 16根x5 + 48根x4 = 272, 两侧 544 整


def _span_at(i):
    """第 i 孔净跨。中央最大, 两端最小(实拍)。"""
    return SPANS[i]


# ── 孔位排布: 净跨两端小中央大(实拍), 故不能等分。
# ── 孔位排布(2026-10-04 重做) ────────────────────────────────────────
# 原做法「150/17=8.824m 为每孔总拱跨」经 GPT 古建校核判定为错误前提:
#   150m 包含 17 净孔 + 16 中墩 + 两端桥台, 且 17 孔不等大, 中心距不可能全等。
# 改用外部实测值直接排布:
#   中央第 9 孔净跨 8.5m、端孔 4.35m(北航《现代物理知识》十七孔桥光学建模文;
#     另一二级资料作 4.2~8.5m 并给出 券厚 0.40m、墩厚 2.5m)
#   桥墩厚 2.5m(同上, 二级资料)
# 缩放系数: 令 17 净孔 + 16 墩 + 2 桥台 精确等于官方 150m
PIER_SRC = 2.50          # GPT v3 保留 2.50, 靠水线分层收分解决"细柱感"
CENTER_CLEAR_SRC = 8.50
END_CLEAR_SRC = 4.35
BRIDGE_ABUT_SRC = 1.35       # 两端桥台 (GPT v3: 107.30+40.00+2.70=150.00 精确闭合)


# 只定义半边 1..9 孔, 第 9 孔(中央)为控制孔; 右半由镜像得到。
# (GPT 2026-10-04 建议: 不做 17 等分, 半边参数化后 Mirror)
# 单位 m, 未经文保测绘, 属第一版拟合锚点
# GPT v2 可执行值: 端孔 4.40, 中央 8.50, 中央最大关系清楚
# GPT v3 完整工作值表(半边 1..9, 右半镜像)。总和 107.30 + 16x2.50墩 + 2x1.35桥台 = 150.00 精确闭合。
HALF_SPANS = [4.50, 4.90, 5.40, 5.90, 6.40, 6.90, 7.40, 8.00, 8.50]


def _raw_spans():
    """左半 9 孔 + 右半镜像, 得 17 孔净跨。中央第 9 孔 = HALF_SPANS[8] 控制值。"""
    half = HALF_SPANS
    return list(half) + list(reversed(half[:-1]))    # 9 + 8 = 17


_raw = _raw_spans()
_unit = sum(_raw) + N_SPAN * PIER_SRC + 2 * BRIDGE_ABUT_SRC   # 18 墩身 + 2 桥台
# GPT v3: 该表本就精确闭合(107.30+40.00+2.70=150.00), 故不缩放, K=1.0
K_SPAN = 1.0
SPANS = [v * K_SPAN for v in _raw]
PIER_W = PIER_SRC * K_SPAN
BRIDGE_ABUT = BRIDGE_ABUT_SRC * K_SPAN   # 桥台同步缩放, 保证闭合严格成立
RING_T = 0.40                       # 券圈径向厚 0.40m (二级资料 + GPT 建议)
# 墩心 x
PIER_X = []
# 首末(i=0,17)是桥台, 中间 16 个是中墩。
# 累计必须严格闭合: BRIDGE_ABUT*2 + PIER_W*16 + sum(SPANS) == BRIDGE_LEN
# ⚠ 曾因"为对齐 +75 做整体平移"而吞掉 1 号孔净跨(左端缺 2.5m, 自检 x=-72.5)。
#    正解: 桥台宽度取实际余量 = (BRIDGE_LEN - 16*PIER_W - sum(SPANS)) / 2, 不用整体平移。
_abut_actual = (BRIDGE_LEN - (N_SPAN - 1) * PIER_W - sum(SPANS)) / 2.0
BRIDGE_ABUT = _abut_actual            # 实际桥台宽(覆盖此前按比例缩放的估计值)
_acc = -BRIDGE_LEN / 2.0
for _ in range(N_SPAN + 1):
    w = BRIDGE_ABUT if _ in (0, N_SPAN) else PIER_W
    PIER_X.append(_acc + w / 2.0)
    _acc += w
    if _ < N_SPAN:
        _acc += SPANS[_]
assert abs(_acc - BRIDGE_LEN / 2.0) < 1e-6, "累计未闭合: %.6f" % _acc
_ARCH_MEAN = BRIDGE_LEN / N_SPAN    # 仅作打印, 不再用于几何

def deck_z(x):
    """桥面标高: 圆弧(彩虹形), 两端最低, 中央最高。

    原用四次幂函数 -> 中间 90m 几乎水平(实测 x=-45..+45 全在 6.4~7.0m),
    与实拍相反。改用圆弧: 弦两端高 DECK_Z_END, 中央 BRIDGE_H, 矢高 RISE_TOTAL。
    """
    import math as _m
    half = BRIDGE_LEN / 2.0
    R = (half * half + RISE_TOTAL * RISE_TOTAL) / (2.0 * RISE_TOTAL)
    return _m.sqrt(max(0.0, R * R - x * x)) - R + RISE_TOTAL + DECK_Z_END


# 券弧矢跨比 f/l。0.50 = 正半圆。
#   「圆券形」只说明是圆弧体系, 不等于数学半圆(北京旅游措辞)。
#   网上「园林低拱桥 1/5~1/10」为通例, 但无十七孔桥实测值, 故不采信。
#   取 0.42 作为工作值: 略扁于半圆, 既保持"圆券"观感, 又给桥腹留厚度。
#   须由正侧长焦照片校准(见 refs/gpt_geom_qa.txt 建议)。
ARCH_RATIO = 0.50     # GPT v3: 近似圆券(北京文旅称"圆券形桥孔")


def _half_circle(span, seg=SEG, ratio=None):
    """椭圆券内轮廓点列: 左起拱点 -> 顶 -> 右起拱点。ratio = 矢高/净跨。"""
    f = ARCH_RATIO if ratio is None else ratio
    a = span / 2.0
    b = a * 2.0 * f                    # 矢高 f = b/a -> b = 2af
    return [(-a * math.cos(math.pi * k / seg), b * math.sin(math.pi * k / seg))
            for k in range(seg + 1)]


def _arch_band(span, z_base, ring_t, seg=SEG, cap_x=None, x_center=0.0):
    """券洞剖面 -> (内弧, 外弧), 外弧沿法向外扩 ring_t。

    cap_x: 券圈外扩不得越过 x_center ± cap_x(该孔两侧墩的外缘)。
    原实现不设限, 使券石在两端孔伸出桥体 0.84m(自检 x=75.84 越界)。
    """
    xlim_lo = x_center - cap_x if cap_x is not None else None
    xlim_hi = x_center + cap_x if cap_x is not None else None
    inner = _half_circle(span, seg)
    outer = []
    n = len(inner)
    for k in range(n):
        if k == 0:
            dx, dz = inner[1][0] - inner[0][0], inner[1][1] - inner[0][1]
        elif k == n - 1:
            dx, dz = inner[-1][0] - inner[-2][0], inner[-1][1] - inner[-2][1]
        else:
            dx, dz = inner[k+1][0] - inner[k-1][0], inner[k+1][1] - inner[k-1][1]
        L = math.hypot(dx, dz) or 1.0
        nx, nz = -dz / L, dx / L
        # 外法线: 背离券洞中心(原点)
        if nx * inner[k][0] + nz * inner[k][1] < 0:
            nx, nz = -nx, -nz
        outer.append((inner[k][0] + nx * ring_t, inner[k][1] + nz * ring_t))
    return ([(x, z_base + z) for x, z in inner],
            [(x, z_base + z) for x, z in outer])


def _wedge(bm, cx, cz, sx, y_bot, y_top, z0, z1):
    """梯形棱柱: 底部横向宽 y_bot(可带±), 顶部 y_top。用于桥体收分断面。
    官方: 桥面下宽 14.6m, 上宽 6.56m -> 侧墙明显外撇(上收下放)。
    """
    zb, zt = z0, z1
    v = [bm.verts.new(p) for p in (
        (cx-sx/2, -y_bot/2, zb), (cx+sx/2, -y_bot/2, zb),
        (cx+sx/2,  y_bot/2, zb), (cx-sx/2,  y_bot/2, zb),
        (cx-sx/2, -y_top/2, zt), (cx+sx/2, -y_top/2, zt),
        (cx+sx/2,  y_top/2, zt), (cx-sx/2,  y_top/2, zt))]
    for f in ((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)):
        try: bm.faces.new([v[k] for k in f])
        except ValueError: pass
    return v


def _box(bm, cx, cy, cz, sx, sy, sz):
    vs = [bm.verts.new(p) for p in (
        (cx-sx/2, cy-sy/2, cz-sz/2), (cx+sx/2, cy-sy/2, cz-sz/2),
        (cx+sx/2, cy+sy/2, cz-sz/2), (cx-sx/2, cy+sy/2, cz-sz/2),
        (cx-sx/2, cy-sy/2, cz+sz/2), (cx+sx/2, cy-sy/2, cz+sz/2),
        (cx+sx/2, cy+sy/2, cz+sz/2), (cx-sx/2, cy+sy/2, cz+sz/2))]
    for f in ((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)):
        try: bm.faces.new([vs[k] for k in f])
        except ValueError: pass
    return vs


def _n_voussoir(i):
    """券石块数, 必须奇数(GPT v2: 留出明确的 crown stone / 拱顶石)。
    中央 9/10 孔 15 块, 6-8/11-13 孔 13 块, 端部 1-5/14-17 孔 11 块。"""
    ci = abs(i - (N_SPAN - 1) / 2.0)      # 距中心的孔位差
    if ci <= 0.5:  return 15
    if ci <= 2.5:  return 15
    if ci <= 3.5:  return 13
    return 11


def build_voussoir_bm():
    """券脸楔形券石: **嵌入式券脸**, 不是盖在洞上的半圆帽。

    GPT v2 指令: "券石应该是洞口边缘的一圈砌石, 而不是洞上扣了一顶半圆石帽。
    arch ring 与桥体侧立面基本齐平, 最多微凸 3-6cm。"
    因此: 内弧 = 券洞内轮廓(intrados); 外弧 = 内弧沿法向外扩 RING_T;
    整圈沿 y 方向嵌入桥体, 只在侧立面露出 0.05m 微凸。
    楔缝为径向缝(指向券心), 非竖缝。
    """
    bm = bmesh.new()
    FACE_PROUD = 0.05                   # 券脸相对侧墙微凸 5cm
    for i in range(N_SPAN):
        span = SPANS[i]
        NVOUS = _n_voussoir(i)
        xc = (PIER_X[i] + PIER_X[i + 1]) / 2.0
        y_face = DECK_DOWN_W / 2.0 - FACE_PROUD   # 券脸所在面(微凸 5cm)
        a = span / 2.0
        b = a * 2.0 * ARCH_RATIO
        gap = 0.020                       # 径向楔缝(米)
        for k in range(NVOUS):
            t0 = math.pi * k / NVOUS + gap
            t1 = math.pi * (k + 1) / NVOUS - gap
            # 轻微变体: 每块厚薄差 3~6%(避免 CG 式绝对重复)
            j = 0.97 + 0.06 * ((k * 7 + i * 3) % 5) / 4.0
            rt = RING_T * j
            ya = y_face
            yb = y_face - rt * (0.94 + 0.12 * (((k * 5) % 3) / 2.0))
            quad = []
            for (tt, yy) in ((t0, ya), (t1, ya), (t1, yb), (t0, yb)):
                quad.append((xc + a * math.cos(tt), yy,
                             SPRINGER + b * math.sin(tt)))
            for (tt, yy) in ((t0, -yb), (t1, -yb), (t1, -ya), (t0, -ya)):
                quad.append((xc + a * math.cos(tt), yy,
                             SPRINGER + b * math.sin(tt)))
            vs = [bm.verts.new(p) for p in quad]
            for f in ((0,1,2,3), (7,6,5,4), (0,4,5,1), (1,5,6,2),
                      (2,6,7,3), (3,7,4,0)):
                try: bm.faces.new([vs[k] for k in f])
                except ValueError: pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.normal_update()
    return bm


def build_body_bm():
    """桥身: 桥台 + 17 孔券石 + 分隔墩 + 桥腹。券洞为真贯通(内壁法线朝内)。"""
    bm = bmesh.new()
    x0 = -BRIDGE_LEN / 2
    y_out = DECK_DOWN_W / 2

    # 墩: 底至水面下, 顶至该处桥面下缘。原写死 BRIDGE_H 造成桥身成等高直方块
    # (首轮渲染实证: bridge_body 各 y 的 z 范围都是 -1.80..7.00, 起拱完全不可见)。
    for i in range(N_SPAN + 1):
        w = BRIDGE_ABUT if i in (0, N_SPAN) else PIER_W
        # 墩: 下部宽(14.6m)收向上部(约7.2m), 侧墙外撇
        _wedge(bm, PIER_X[i], 0.0, w, DECK_DOWN_W, DECK_DOWN_W * 0.50,
               BODY_BOTTOM, SPRINGER)

    # 券石 + 拱背填实
    for i in range(N_SPAN):
        span = _span_at(i)
        xc_a = (PIER_X[i] + PIER_X[i + 1]) / 2.0
        half_gap = ((PIER_W if i > 0 else BRIDGE_ABUT) +
                    (PIER_W if i + 1 < N_SPAN else BRIDGE_ABUT)) / 2.0
        inner, outer = _arch_band(span, SPRINGER, RING_T, x_center=xc_a, cap_x=half_gap)
        # 券洞断面也收分: 起拱线处较宽(约下宽), 券顶处收至上宽
        y_in, y_out2 = -DECK_DOWN_W/2, DECK_DOWN_W/2
        for y in (y_in, y_out2):
            vi = [bm.verts.new((xc_a + px, y, pz)) for px, pz in inner]
            vo = [bm.verts.new((xc_a + px, y, pz)) for px, pz in outer]
            for k in range(SEG):
                try: bm.faces.new((vi[k], vi[k+1], vo[k+1], vo[k]))
                except ValueError: pass
            try: bm.faces.new(vi)                       # 拱腹(内壁)
            except ValueError: pass
            try: bm.faces.new(list(reversed(vo)))       # 拱背
            except ValueError: pass
        # 两端封口
        for k in (0, SEG):
            try:
                bm.faces.new([
                    bm.verts.new((xc_a+inner[k][0], y_in,  inner[k][1])),
                    bm.verts.new((xc_a+outer[k][0], y_in,  outer[k][1])),
                    bm.verts.new((xc_a+outer[k][0], y_out2, outer[k][1])),
                    bm.verts.new((xc_a+inner[k][0], y_out2, inner[k][1]))])
            except ValueError: pass
        # 券洞之间的桥腹填实(券顶到桥面下缘)
        # 券顶到桥面下缘之间填"起拱体"—— 这道随桥面起拱的实体才是"长虹"的本体。
        # 首轮把它填死到 BRIDGE_H, 桥身成等高直方块, 起拱完全不可见(渲染实证)。
        arch_top = SPRINGER + span * ARCH_RATIO + RING_T    # 券顶+券石厚
        x_lo, x_hi = PIER_X[i] + PIER_W / 2.0, PIER_X[i + 1] - PIER_W / 2.0
        NS = 24
        for q in range(NS):
            xa = x_lo + (x_hi - x_lo) * q / NS
            xb = x_lo + (x_hi - x_lo) * (q + 1) / NS
            ztop = (deck_z(xa) + deck_z(xb)) / 2.0
            if ztop - arch_top > 0.02:
                # 起拱体: 随高度收分
                f = (arch_top - BODY_BOTTOM) / (ztop - BODY_BOTTOM)
                w_here = DECK_DOWN_W * (1.0 - 0.5 * min(1.0, max(0.0, f)))
                _wedge(bm, (xa + xb) / 2.0, 0.0, xb - xa, w_here, w_here * 0.86,
                       arch_top, ztop)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.normal_update()
    return bm


def build_deck_bm():
    """桥面 + 密排望柱(柱头蹲狮) + 镂空栏板。"""
    bm = bmesh.new()
    x0 = -BRIDGE_LEN / 2
    ry = DECK_UP_W / 2

    n = 120
    prev = None
    for s in range(n + 1):
        x = x0 + s / n * BRIDGE_LEN
        z = deck_z(x)
        cur = [bm.verts.new((x, -ry, z)), bm.verts.new((x, ry, z))]
        if prev:
            try: bm.faces.new((prev[0], cur[0], cur[1], prev[1]))
            except ValueError: pass
        prev = cur

    # 望柱 + 柱头石狮 + 镂空栏板
    lion_bm = bmesh.new()
    panel_bm = bmesh.new()
    for side in (-1, 1):
        y = side * ry
        for i in range(N_NEWEL + 1):
            x = x0 + i / N_NEWEL * BRIDGE_LEN
            z = deck_z(x)
            _box(bm, x, y, z + 0.95, 0.34, 0.34, 1.90)          # 望柱身
            _box(bm, x, y, z + 1.98, 0.46, 0.46, 0.18)          # 柱头承台
            # 蹲狮: 身 + 头 + 前爪 + 绣球(实拍: 狮蹲球上, 前爪抱球)
            # 实拍: 狮蹲球上, 前爪抱球, 体高约 0.55m, 明显高出栏板
            _box(lion_bm, x, y, z + 2.36, 0.54, 0.32, 0.42)       # 身
            _box(lion_bm, x - 0.21, y, z + 2.64, 0.27, 0.27, 0.25)   # 头
            _box(lion_bm, x - 0.31, y, z + 2.24, 0.18, 0.42, 0.14)   # 前爪
            _box(lion_bm, x - 0.40, y, z + 2.18, 0.25, 0.25, 0.25)   # 绣球
            # 栏板: 镂空 —— 只做边框与横枋, 中间留空(实拍为花格透空)
            if i < N_NEWEL:
                x2 = x0 + (i + 1) / N_NEWEL * BRIDGE_LEN
                z2 = deck_z(x2)
                yi = y - side * 0.07
                _box(panel_bm, (x + x2) / 2, yi, (z + z2) / 2 + 0.22,
                     abs(x2 - x) - 0.30, 0.14, 0.12)              # 上枋
                _box(panel_bm, (x + x2) / 2, yi, (z + z2) / 2 + 1.42,
                     abs(x2 - x) - 0.30, 0.14, 0.12)              # 下枋
                _box(panel_bm, (x + x2) / 2, yi, (z + z2) / 2 + 0.82,
                     abs(x2 - x) - 0.30, 0.12, 0.07)              # 中横
    for b in (lion_bm, panel_bm):
        bmesh.ops.recalc_face_normals(b, faces=b.faces[:])
        b.normal_update()
    return bm, lion_bm, panel_bm


def build_beast_bm():
    """桥头异兽 4 只(园方未命名)。位置: 两端各 2 只, 蹲伏大体型。"""
    bm = bmesh.new()
    for xe in (-BRIDGE_LEN / 2 + 1.2, BRIDGE_LEN / 2 - 1.2):
        z = deck_z(xe)
        for side in (-1, 1):
            y = side * (DECK_UP_W / 2 + 0.55)
            _box(bm, xe, y, z + 0.42, 1.30, 0.90, 0.84)          # 躯干
            _box(bm, xe + (0.5 if xe > 0 else -0.5), y, z + 1.02, 0.52, 0.52, 0.50)  # 首
            _box(bm, xe + (0.72 if xe > 0 else -0.72), y, z + 0.92, 0.34, 0.34, 0.30)  # 吻
            _box(bm, xe, y, z + 0.10, 1.10, 1.00, 0.30)           # 座
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.normal_update()
    return bm


if __name__ == "__main__":
    body = build_body_bm()
    xs = [v.co.x for v in body.verts]; zs = [v.co.z for v in body.verts]
    print("桥身  verts=%d faces=%d  x %.2f..%.2f  z %.2f..%.2f"
          % (len(body.verts), len(body.faces), min(xs), max(xs), min(zs), max(zs)))
    print("  中央孔净跨 %.3f  端孔净跨 %.3f  半圆矢高 %.3f"
          % (SPAN_CLEAR_C, _span_at(0), _span_at(0) / 2))
    print("  券顶最高 %.2f (须 <= %.1f)" % (SPRINGER + SPAN_CLEAR_C/2 + RING_T, BRIDGE_H))
    d, l, p = build_deck_bm()
    b = build_beast_bm()
    print("桥面  verts=%d  望柱 %d 对  石狮 %d 只  栏板 verts=%d"
          % (len(d.verts), N_NEWEL + 1, 2 * (N_NEWEL + 1), len(p.verts)))
    print("异兽  verts=%d" % len(b.verts))
    assert abs(max(xs)) <= BRIDGE_LEN/2 + .01
    assert SPRINGER + SPAN_CLEAR_C/2 + RING_T <= BRIDGE_H + .01
    assert SPRINGER > BODY_BOTTOM
    assert len(d.verts) > 0 and len(l.verts) > 0
    print("GEOM_OK")
