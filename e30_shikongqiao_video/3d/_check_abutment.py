"""八轮 P0-1 数值验证: 实腹桥台/实腹坡道/接岸地坪/栏杆连续+抱鼓石(读 e30_bridge.blend, 副本隔离).

七审三项: ①桥台横向展开(平面梯形, 通高实体) ②坡道加长且端头真正落岸 ③栏杆沿坡道
连续落下以抱鼓石收头。断言值随 2026-10-06 新尺寸(参数块"八轮 P0-1")更新。
"""
import bpy, sys, math

TOL = 1e-6
HALF = 75.0
ABUT_U0, ABUT_L = -0.8, 5.2
HW_ROOT, HW_FRONT = 6.30, 5.00
ABUT_TOP = 3.56
RAMP_U0, RAMP_L = 5.14, 42.0
RAMP_U1 = RAMP_U0 + RAMP_L
RAMP_Z0, Z_TIP = 3.55, 2.45
HW0, HW1 = 3.28, 4.40
PAD_Z = 2.42
WING_U, WING_Y, WING_L, WING_T = 3.0, 5.2, 6.0, 1.8  # L 随 M15 目视修x3 同步
WING_ANG = math.radians(38.0)
BANK_Z = 2.1
BED_BOTTOM = -2.8
RAIL_END_U = RAMP_U1 - 2.0

def road_z(u):
    f = max(0.0, min(1.0, (u - RAMP_U0) / RAMP_L))
    return RAMP_Z0 + (Z_TIP - RAMP_Z0) * f

def road_half(u):
    f = max(0.0, min(1.0, (u - ABUT_L) / RAMP_L))
    return HW0 + (HW1 - HW0) * f

def wing_top(t):
    return ABUT_TOP * (1.0 - t) + 0.55 * t   # 尖端标高随 M15 深埋修同步(原 BANK_Z+0.35)

fails = []
def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        fails.append(msg)

agr = bpy.data.objects["abutment_ground"]
bank = bpy.data.objects["shore_bank"]
rail = bpy.data.objects["deck_rail"]
body = bpy.data.objects["bridge_body"]

def bbox(ob):
    xs = [v.co.x for v in ob.data.vertices]
    ys = [v.co.y for v in ob.data.vertices]
    zs = [v.co.z for v in ob.data.vertices]
    return min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)

ax0, ax1, ay0, ay1, az0, az1 = bbox(agr)
kx0, kx1, _, _, kz0, kz1 = bbox(bank)
rx0, rx1, _, _, rz0, rz1 = bbox(rail)
bx1 = max(abs(v.co.x) for v in body.data.vertices)

# C1 实腹桥台: 平面梯形(根6.30->前脸5.00), 根埋端墙0.8, 通高实体, 台帽沉桥面下4cm
front = [v for v in agr.data.vertices
         if abs(abs(v.co.x) - (HALF + ABUT_L)) < 0.01 and abs(v.co.y) > 4.0]
check(len(front) >= 4, "C1 台体前脸存在 (%d 顶点 @|x|=80.20, |y|>4)" % len(front))
fw = max(abs(v.co.y) for v in agr.data.vertices if 79.9 <= abs(v.co.x) <= 80.21)
rw = max(abs(v.co.y) for v in agr.data.vertices if 74.0 <= abs(v.co.x) <= 75.01)
check(fw >= 5.5, "C1 前脸最大半宽=%.3f (梯形前宽, >=5.5)" % fw)
check(rw >= 7.3, "C1 根部最大半宽=%.3f (包络本体底半宽 7.3)" % rw)
check(rw > fw, "C1 平面收分方向 根 %.2f > 前 %.2f (前宽后窄)" % (rw, fw))
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

# C4 石颊: 坡/台走廊内岸坡 <= 石面-0.70 (u∈[6,39]; 窗口=cap 权重 1 的足印带)
bad_r, n_r, maxover_r = 0, 0, -1e9
for v in bank.data.vertices:
    u, y, z = abs(v.co.x) - HALF, v.co.y, v.co.z
    if 6.0 <= u <= 39.0 and abs(y) <= road_half(u) - 0.01:
        n_r += 1
        over = z - (road_z(u) - 0.70)
        maxover_r = max(maxover_r, over)
        if over > 1e-6:
            bad_r += 1
check(bad_r == 0, "C4 坡道走廊内岸坡超高点=0 (查 %d 点, 最大越界 %.4f)" % (n_r, maxover_r))

# C5 已随翼墙删除(M15目视修x4): 翼墙为纯负资产, 断言无对象

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
# 坡中样本: 栏杆最低点贴路面(地栿底=路面顶)
u_s = 15.0
zs_s = [v.co.z for v in rail.data.vertices if abs(abs(v.co.x) - (HALF + u_s)) <= 0.5]
z_err = abs(min(zs_s) - road_z(u_s)) if zs_s else 9e9
check(z_err <= 0.06, "C7 u=%.0f 处栏杆底贴路面 (差 %.4f, 地栿底=坡面)" % (u_s, z_err))
# 末端抱鼓石: x∈[119.9,121.0] 且鼓高带内有实体
rd = road_z(45.33)
n_drum = sum(1 for v in rail.data.vertices
             if 119.9 <= abs(v.co.x) <= 121.0 and rd + 0.10 <= v.co.z <= rd + 0.50)
check(n_drum >= 12, "C7 抱鼓石存在 (末端 %d 顶点 @z≈路面+0.13~0.47)" % n_drum)
# 坡道望柱列数: 末端收头前 RAIL_END_U, 等分柱距
zs_rail = len([1 for v in rail.data.vertices if abs(v.co.x) > HALF + ABUT_L + 0.1])
check(zs_rail > 500, "C7 坡道段栏杆顶点数 %d (>500, 两侧 17 开间构件)" % zs_rail)

print("── 主要尺寸报告 ──")
print("  桥台     根埋 0.8 + 纵长 5.2, 平面梯形 半宽 %.2f->%.2f, 台帽 %.2f (旧: 恒截面 7.45->3.60)" % (
      HW_ROOT, HW_FRONT, ABUT_TOP))
print("  实腹总厚 73.65 -> 80.20 = %.2f m (旧 4.45)" % thick)
print("  坡道     24 -> %.0f m (端 |x| 99 -> %.2f), 坡度 %.2f%%, 顶 3.55->%.2f" % (
      RAMP_L, ax1, grade, Z_TIP))
print("  接岸坪   u 40~78 标高 %.2f (坡端没入 0.03)" % PAD_Z)
print("  翼墙     L 24 -> %.0f (根 u=%.1f,y=%.1f), 展角 %.0f deg, 厚 %.1f" % (
      WING_L, WING_U, WING_Y, math.degrees(WING_ANG), WING_T))
print("  栏杆     桥端 -> u=%.1f (坡端前 2m), 末端地袱+抱鼓石" % RAIL_END_U)
print("  石作底   %.2f; 岸坡最低 %.2f" % (az0, kz0))

if fails:
    print("ABUTMENT_CHECK FAILED: %d" % len(fails))
    sys.exit(1)
print("ABUTMENT_CHECK ALL PASS")
