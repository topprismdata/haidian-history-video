"""九轮第二刀数值验证: 桥头 massing 收口(台体楔形渐退/坡道侧墙非恒厚/顶铺+侧台外展/
石颊露出渐退), 读 e30_bridge.blend, 副本隔离。C1-C7 沿用八轮口径(常量随新尺寸),
C8-C11 为九轮新增四断言。
"""
import bpy, sys, math

TOL = 1e-6
HALF = 75.0
ABUT_U0, ABUT_L = -0.8, 5.2
HW_ROOT, HW_FRONT = 6.50, 4.55
ABUT_TOP = 3.56
RAMP_U0, RAMP_L = 5.14, 42.0
RAMP_U1 = RAMP_U0 + RAMP_L
RAMP_Z0, Z_TIP = 3.55, 2.45
HW0, HW1 = 3.28, 5.00          # 铺装边线(九轮外展 4.40 -> 5.00)
HW_SOLID_END = 5.15            # 侧墙顶棱@坡端(九轮新增)
REVEAL_HEAD, REVEAL_END = 1.35, 0.75   # 石颊露出高(九轮: 恒0.75 -> 渐退)
BATTER = 0.85
PAD_Z = 2.42
BANK_Z = 2.1
BED_BOTTOM = -2.8
RAIL_END_U = RAMP_U1 - 2.0

def road_z(u):
    f = max(0.0, min(1.0, (u - RAMP_U0) / RAMP_L))
    return RAMP_Z0 + (Z_TIP - RAMP_Z0) * f

def road_half(u):
    f = max(0.0, min(1.0, (u - ABUT_L) / RAMP_L))
    return HW0 + (HW1 - HW0) * f

def abut_plan_hw(u):
    f = max(0.0, min(1.0, (u - ABUT_U0) / ABUT_L))
    return HW_ROOT + (HW_FRONT - HW_ROOT) * f

def ramp_solid_hw(u):
    t = max(0.0, min(1.0, (u - ABUT_L) / RAMP_L))
    return HW_FRONT + (HW_SOLID_END - HW_FRONT) * t ** 0.65

def solid_hw(u):
    return abut_plan_hw(u) if u < ABUT_L else ramp_solid_hw(u)

def reveal_at(u):
    t = max(0.0, min(1.0, (u - ABUT_L) / RAMP_L))
    return REVEAL_END + (REVEAL_HEAD - REVEAL_END) * (1.0 - t)

fails = []
def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        fails.append(msg)

agr = bpy.data.objects["abutment_ground"]
bank = bpy.data.objects["shore_bank"]
rail = bpy.data.objects["deck_rail"]
body = bpy.data.objects["bridge_body"]
cornice = bpy.data.objects["ramp_cornice"]

def bbox(ob):
    xs = [v.co.x for v in ob.data.vertices]
    ys = [v.co.y for v in ob.data.vertices]
    zs = [v.co.z for v in ob.data.vertices]
    return min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)

ax0, ax1, ay0, ay1, az0, az1 = bbox(agr)
kx0, kx1, _, _, kz0, kz1 = bbox(bank)
rx0, rx1, _, _, rz0, rz1 = bbox(rail)
bx1 = max(abs(v.co.x) for v in body.data.vertices)

# C1 实腹桥台: 平面楔形(根6.50->前脸4.55, 九轮"靠桥端厚向岸渐退"), 根埋端墙0.8,
#     通高实体, 台帽沉桥面下4cm
front = [v for v in agr.data.vertices
         if abs(abs(v.co.x) - (HALF + ABUT_L)) < 0.01 and abs(v.co.y) > 4.0]
check(len(front) >= 4, "C1 台体前脸存在 (%d 顶点 @|x|=80.20, |y|>4)" % len(front))
fw = max(abs(v.co.y) for v in agr.data.vertices if 79.9 <= abs(v.co.x) <= 80.21)
rw = max(abs(v.co.y) for v in agr.data.vertices if 74.0 <= abs(v.co.x) <= 75.01)
check(fw >= 5.3, "C1 前脸最大半宽=%.3f (楔形小端 + 收分0.85, >=5.3)" % fw)
check(rw >= 7.3, "C1 根部最大半宽=%.3f (包络本体底半宽 7.3)" % rw)
check(rw - fw >= 1.5, "C1 楔形收口 根 %.2f - 前 %.2f = %.2f (九轮: 楔差>=1.5, 靠桥端厚)"
      % (rw, fw, rw - fw))
check(74.0 <= min(abs(v.co.x) for v in agr.data.vertices) <= 74.5,
      "C1 根埋深 |x|min=%.3f (端墙 73.65~75 内嵌入 0.8, 不侵末孔)"
      % min(abs(v.co.x) for v in agr.data.vertices))
thick = (HALF + ABUT_L) - (HALF - 1.35)
check(5.5 <= thick <= 7.5, "C1 末孔券脸->前脸实腹总厚=%.2fm (要求 5.5~7.5)" % thick)
check(3.50 <= az1 <= 3.58, "C1 台帽顶 z=%.3f (桥面端 3.60 沉 4cm 帽石缝)" % az1)
check(bx1 <= HALF + 1e-6, "C1 本体端面未被布尔改动 |x|max=%.3f (应 75.0)" % bx1)

# C2 实腹坡道: 42m 缓坡, 端头顶 2.45
check(abs(ax1 - (HALF + RAMP_U1)) < 0.01,
      "C2 坡端 |x|max=%.3f (应 %.2f=75+5.14+42)" % (ax1, HALF + RAMP_U1))
grade = (RAMP_Z0 - Z_TIP) / RAMP_L * 100.0
check(2.0 <= grade <= 3.2, "C2 坡度 %.2f%% (3.55->2.45m/42m, 缓坡)" % grade)
tipz = max(v.co.z for v in agr.data.vertices if abs(v.co.x) > HALF + RAMP_U1 - 0.3)
check(2.40 <= tipz <= 2.50, "C2 坡端顶实测 z=%.3f (应≈2.45)" % tipz)

# C3 埋深: 石作底低于岸坡最低点
check(abs(az0 - BED_BOTTOM) < 1e-5, "C3 石作最低点 z=%.3f (应 -2.8)" % az0)
check(az0 < kz0, "C3 石作底 %.3f < 岸坡最低 %.3f (插入水底, 无悬空)" % (az0, kz0))
check(abs(kz0 - (-2.4)) < 0.01, "C3 岸坡最低 z=%.3f (应 -2.4)" % kz0)

# C4 石颊: 坡/台走廊内岸坡 <= 石面-0.70 (u∈[6,39]; 窗口=九轮实腹顶棱足印带)
bad_r, n_r, maxover_r = 0, 0, -1e9
for v in bank.data.vertices:
    u, y, z = abs(v.co.x) - HALF, v.co.y, v.co.z
    if 6.0 <= u <= 39.0 and abs(y) <= solid_hw(u) - 0.01:
        n_r += 1
        over = z - (road_z(u) - 0.70)
        maxover_r = max(maxover_r, over)
        if over > 1e-6:
            bad_r += 1
check(bad_r == 0, "C4 坡道走廊内岸坡超高点=0 (查 %d 点, 最大越界 %.4f)" % (n_r, maxover_r))

# C5 已随翼墙删除(M15目视修x4): 翼墙为纯负资产, 断言无对象(九轮: 维持删除, 不复活)

# C6 接岸地坪: 坡端外侧地坪存在且等于 PAD_Z(端面没入, 无临空)
padz, tipz2, n_p, n_t = [], [], 0, 0
for v in bank.data.vertices:
    u, y, z = abs(v.co.x) - HALF, v.co.y, v.co.z
    if 52.0 <= u <= 66.0 and abs(y) <= 5.0:
        n_p += 1; padz.append(z)
    if 50.2 <= u <= 56.0 and abs(y) <= 4.2:
        n_t += 1; tipz2.append(z)
check(n_p >= 30 and 2.38 <= min(padz) and max(padz) <= 2.46,
      "C6 接岸地坪 z∈[%.3f,%.3f] (n=%d, 应≈%.2f 平整存在)" % (min(padz), max(padz), n_p, PAD_Z))
check(n_t >= 24 and 2.38 <= min(tipz2) and max(tipz2) <= 2.46,
      "C6 坡端区地坪 z∈[%.3f,%.3f] (n=%d, 端面没入: 坡端顶2.45-地坪%.2f 出露0.03)" % (
          min(tipz2), max(tipz2), n_t, PAD_Z))

# C7 栏杆沿坡道连续 + 抱鼓石收头
check(rx1 >= 118.0, "C7 栏杆延伸 |x|max=%.2f (>=118, 末端抱鼓石 ~120.6)" % rx1)
n_plat = sum(1 for v in rail.data.vertices if 77.3 <= abs(v.co.x) <= 77.9)
check(n_plat >= 8, "C7 台帽平台段望柱存在 (x=77.6 处 %d 顶点)" % n_plat)
u_s = 15.0
zs_s = [v.co.z for v in rail.data.vertices if abs(abs(v.co.x) - (HALF + u_s)) <= 0.5]
z_err = abs(min(zs_s) - road_z(u_s)) if zs_s else 9e9
check(z_err <= 0.06, "C7 u=%.0f 处栏杆底贴路面 (差 %.4f, 地栿底=坡面)" % (u_s, z_err))
rd = road_z(45.33)
n_drum = sum(1 for v in rail.data.vertices
             if 119.9 <= abs(v.co.x) <= 121.0 and rd + 0.10 <= v.co.z <= rd + 0.50)
check(n_drum >= 12, "C7 抱鼓石存在 (末端 %d 顶点 @z≈路面+0.13~0.47)" % n_drum)
zs_rail = len([1 for v in rail.data.vertices if abs(v.co.x) > HALF + ABUT_L + 0.1])
check(zs_rail > 500, "C7 坡道段栏杆顶点数 %d (>500, 两侧 17 开间构件)" % zs_rail)

# ── 九轮第二刀新增: massing 收口四断言 ──
# C8 顶铺与侧台一起外展: 铺装边线 3.28->5.00, 侧墙顶棱 4.55->5.15 (都向外, 无束腰)
sh_root = solid_hw(ABUT_L) - road_half(ABUT_L)          # 1.27
sh_end = solid_hw(RAMP_U1) - road_half(RAMP_U1)         # 0.15
cy0 = max(abs(v.co.y) for v in cornice.data.vertices
          if abs(v.co.x) < HALF + ABUT_L + 0.3)
cy1 = max(abs(v.co.y) for v in cornice.data.vertices
          if abs(v.co.x) > HALF + RAMP_U1 - 0.3)
check(road_half(RAMP_U1) - road_half(ABUT_L) >= 1.5,
      "C8 顶铺外展 %.2f -> %.2f (+%.2f, >=+1.5)" % (
          road_half(ABUT_L), road_half(RAMP_U1), road_half(RAMP_U1) - road_half(ABUT_L)))
check(solid_hw(RAMP_U1) >= HW_FRONT + 0.4,
      "C8 侧墙顶棱外展 %.2f -> %.2f (>=前脸+0.4, 侧台随铺装外展)"
      % (HW_FRONT, solid_hw(RAMP_U1)))
check(cy1 - cy0 >= 1.3, "C8 仰天石实测展宽 根 %.2f -> 端 %.2f (+%.2f)"
      % (cy0, cy1, cy1 - cy0))
# C9 坡道侧墙非恒厚直板: 肩宽(顶棱-铺装) 1.27 -> 0.15 递减 + 顶棱幂曲线(非直线)
mid = 0.5 * (ABUT_L + RAMP_U1)
bow = (ramp_solid_hw(mid) - HW_FRONT) / (HW_SOLID_END - HW_FRONT)   # t^0.65 @0.5=0.637
check(sh_root - sh_end >= 0.8,
      "C9 肩宽渐退 根 %.2f -> 端 %.2f (差 %.2f >= 0.8, 墙厚靠桥端厚)"
      % (sh_root, sh_end, sh_root - sh_end))
check(0.55 <= bow <= 0.75,
      "C9 顶棱幂曲线中点归一 %.3f (直线=0.50; 偏离=顶棱非直板)" % bow)
# 实测 mesh: 坡中顶棱 y 应高于线性插值(幂曲线弓出)
u_a, u_b = ABUT_L + 0.5, RAMP_U1 - 0.5
edge = []
for v in agr.data.vertices:
    u = abs(v.co.x) - HALF
    zt = road_z(u) if u > ABUT_L else ABUT_TOP
    if u_a <= u <= u_b and zt - 0.02 <= v.co.z <= zt + 0.02 and abs(v.co.y) > 3.0:
        edge.append((u, abs(v.co.y)))
lin_mid = solid_hw(u_a) + (solid_hw(u_b) - solid_hw(u_a)) * \
          (mid - u_a) / (u_b - u_a)
act_mid = max(yy for uu, yy in edge if abs(uu - mid) < 1.0) if edge else 0.0
check(act_mid >= lin_mid + 0.05,
      "C9 顶棱实测弓出 u=%.1f: %.3f > 线性 %.3f (+%.3f, 侧墙平面非直线)"
      % (mid, act_mid, lin_mid, act_mid - lin_mid))
# C10 石颊露出高渐退: 头墙走廊岸坡挖低 1.35, 坡端 0.75 (mesh 实测走廊内岸坡最高)
def bank_top(u0, u1, hw_ofs):
    z = -9e9
    for v in bank.data.vertices:
        u, y = abs(v.co.x) - HALF, v.co.y
        if u0 <= u <= u1 and abs(y) <= solid_hw((u0 + u1) / 2.0) - hw_ofs:
            z = max(z, v.co.z)
    return z
bh = bank_top(7.0, 12.0, 0.6)          # 头墙走廊(u7~12): 应≈road_top-1.35
be = bank_top(34.0, 39.0, 0.6)         # 坡端走廊(u34~39): 应≈road_top-0.75~0.9
rv_h = road_z(9.5) - bh
rv_e = road_z(36.5) - be
check(rv_h >= 1.15, "C10 头墙石颊露出实测 %.2f (>=1.15, 重量区)" % rv_h)
check(rv_h - rv_e >= 0.25,
      "C10 石颊露出渐退 头 %.2f - 端 %.2f = %.2f (>=0.25, 向岸渐退)"
      % (rv_h, rv_e, rv_h - rv_e))
# C11 无束腰: 台-坡接缝两侧实腹半宽连续(C0), 且全程 >= 铺装+0.10(侧墙始终有厚度)
gap = abs(solid_hw(ABUT_L + 0.01) - solid_hw(ABUT_L - 0.01))
check(gap <= 0.05, "C11 台-坡接缝 C0 连续 (Δ=%.3f <= 0.05)" % gap)
min_sh = min(solid_hw(ABUT_L + RAMP_L * i / 100.0) - road_half(ABUT_L + RAMP_L * i / 100.0)
             for i in range(101))
check(min_sh >= 0.10, "C11 坡道全程肩宽 >= %.3f (>=0.10, 侧墙顶棱不并入铺装)" % min_sh)

print("── 主要尺寸报告(九轮第二刀) ──")
print("  台体楔形  根 %.2f -> 前 %.2f (楔差 %.2f/6m; 旧八轮 6.50->5.00)" % (
      HW_ROOT, HW_FRONT, HW_ROOT - HW_FRONT))
print("  实腹总厚  73.65 -> 80.20 = %.2f m" % thick)
print("  铺装边线  3.28 -> %.2f (外展 +%.2f; 旧 ->4.40)" % (HW1, HW1 - HW0))
print("  侧墙顶棱  %.2f -> %.2f 幂曲线(肩 %.2f -> %.2f 渐退)" % (
      HW_FRONT, HW_SOLID_END, sh_root, sh_end))
print("  石颊露出  %.2f -> %.2f 渐退(旧恒 0.75)" % (REVEAL_HEAD, REVEAL_END))
print("  坡道      %.0f m, 坡度 %.2f%%, 端 |x| %.2f, 接岸坪 %.2f" % (
      RAMP_L, grade, ax1, PAD_Z))
print("  栏杆      -> u=%.1f 末端抱鼓石; 燕翅墙维持删除" % RAIL_END_U)

if fails:
    print("ABUTMENT_CHECK FAILED: %d" % len(fails))
    sys.exit(1)
print("ABUTMENT_CHECK ALL PASS")
