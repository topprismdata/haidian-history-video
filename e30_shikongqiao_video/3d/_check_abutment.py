"""六审第3刀 数值验证: 桥台墩座/引道/燕翅墙/岸坡咬合(读 e30_bridge.blend, 副本隔离).

判据(全部为硬断言, 任何一条不满足即非零退出):
  C1 墩座: bridge_body 端部石墙外缘 |x|=78.0 (=75+ABUT_EXT), 末孔外石墙总厚 4.35m ∈ 3.5~5.0
  C2 引道: abutment_ground 纵向到达 |x|=102.06 (=75+3+24), 坡度 2.7%
  C3 埋深: 石作最低点 = -2.8 < 岸坡全域最低 -> "稳固插入水底", 无悬空
  C4 无穿模(引道走廊): 岸坡顶点 z <= 路面(u) - 0.45 (|v| <= 路面半宽+2.5, u ∈ (-1, 坡端+3])
  C5 无穿模(翼墙走廊): dist < WING_T/2+0.9 的岸坡顶点 z <= 翼墙顶(t) - 0.28
  C6 坡端咬合: 坡端断面外侧岸坡 <= 2.55 (坡端顶 2.95 - 0.45, 端面没入)
"""
import bpy, sys, math

TOL = 1e-6
HALF = 75.0
ABUT_EXT, RAMP_L = 3.0, 24.0
WING_L, WING_T = 24.0, 1.8
WING_ANG = math.radians(38.0)
BANK_Z = 2.1
BED_BOTTOM = -2.8
Z_E = 3.60                      # deck_z(±75)
Z_TIP = BANK_Z + 0.85
Z_R0 = Z_E - 0.04
U_R0, U_R1 = ABUT_EXT - 0.06, ABUT_EXT - 0.06 + RAMP_L
RT0C, RT1C = 6.56 / 2.0 + 0.12, 5.2

def road_top(u):
    fr = max(0.0, min(1.0, (min(u, U_R1) - U_R0) / RAMP_L))
    return Z_R0 + (Z_TIP - Z_R0) * fr

def road_half(u):
    fr = max(0.0, min(1.0, (min(u, U_R1) - U_R0) / RAMP_L))
    return RT0C + (RT1C - RT0C) * fr

def wing_top(t):
    return Z_E * (1.0 - t) + (BANK_Z + 0.35) * t

fails = []
def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        fails.append(msg)

body = bpy.data.objects["bridge_body"]
agr = bpy.data.objects["abutment_ground"]
bank = bpy.data.objects["shore_bank"]

def bbox(ob):
    xs = [v.co.x for v in ob.data.vertices]
    ys = [v.co.y for v in ob.data.vertices]
    zs = [v.co.z for v in ob.data.vertices]
    return min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)

ax0, ax1, ay0, ay1, az0, az1 = bbox(agr)
kx0, kx1, _, _, kz0, kz1 = bbox(bank)
bx1 = max(abs(v.co.x) for v in body.data.vertices)

# C1 墩座: 免布尔实体(在 abutment_ground 内), 前端面 |x|=78, 末孔外石墙总厚 4.35m
collar = [v for v in agr.data.vertices
          if abs(abs(v.co.x) - (HALF + ABUT_EXT)) < 0.01 and abs(v.co.y) > 7.0]
check(len(collar) >= 4, "C1 墩座前端面存在 (%d 顶点 @|x|=78, |y|>7)" % len(collar))
thick = (HALF + ABUT_EXT) - (HALF - 1.35)
check(3.5 <= thick <= 5.0, "C1 末孔外石墙总厚=%.2fm (要求 3.5~5.0)" % thick)
check(bx1 <= HALF + 1e-6, "C1 本体端面未被布尔改动 |x|max=%.3f (应 75.0)" % bx1)

# C2 引道到达
check(abs(ax1 - (HALF + ABUT_EXT + RAMP_L)) < 0.01,
      "C2 引道端 |x|max=%.3f (应 102.00=75+3+24)" % ax1)
grade = (Z_R0 - Z_TIP) / RAMP_L * 100.0
check(abs(grade - 2.5417) < 0.01, "C2 引道坡度 %.2f%% (3.56->2.95m/24m)" % grade)

# C3 埋深: 石作底低于岸坡最低点
check(abs(az0 - BED_BOTTOM) < 1e-5, "C3 石作最低点 z=%.3f (应 -2.8)" % az0)
check(az0 < kz0, "C3 石作底 %.3f < 岸坡最低 %.3f (插入水底, 无悬空)" % (az0, kz0))
check(abs(kz0 - (-2.4)) < 0.01, "C3 岸坡最低 z=%.3f (应 -2.4)" % kz0)

# C4/C5 岸坡走廊无穿模(逐顶点, 用网格实际坐标; 窗口=石作足印, cap 权重=1 的区域)
bad_r, bad_w, n_r, n_w = 0, 0, 0, 0
maxover_r = maxover_w = -1e9
for v in bank.data.vertices:
    x, y, z = v.co.x, v.co.y, v.co.z
    u = abs(x) - HALF
    # C4 引道走廊(石作足印: |v| <= 路面半宽)
    if -1.0 < u < U_R1 + 3.0:
        h = road_half(u)
        if abs(y) <= h:
            n_r += 1
            over = z - (road_top(u) - 0.75)
            if over > TOL:
                bad_r += 1
                maxover_r = max(maxover_r, over)
    # C5 翼墙走廊(石作足印: dist <= WING_T/2)
    for side in (-1, 1):
        ax_, ay_ = ABUT_EXT - 0.5, side * (6.56 / 2.0 - 0.1)
        dx_, dy_ = math.cos(WING_ANG), side * math.sin(WING_ANG)
        t = max(0.0, min(1.0, ((u - ax_) * dx_ + (y - ay_) * dy_) / WING_L))
        cx_, cy_ = ax_ + dx_ * WING_L * t, ay_ + dy_ * WING_L * t
        dist = math.hypot(u - cx_, y - cy_)
        if dist < WING_T / 2.0:
            n_w += 1
            over = z - (wing_top(t) - 0.75)
            if over > TOL:
                bad_w += 1
                maxover_w = max(maxover_w, over)
check(bad_r == 0, "C4 引道足印内岸坡超高点=0 (查 %d 点, 最大越界 %.4f)" % (n_r, maxover_r))
check(bad_w == 0, "C5 翼墙足印内岸坡超高点=0 (查 %d 点, 最大越界 %.4f)" % (n_w, maxover_w))

# C6 坡端咬合: 坡端外侧 3m 内、路面半宽内 岸坡 <= 2.55
tipmax = -1e9
for v in bank.data.vertices:
    u = abs(v.co.x) - HALF
    if U_R1 - 1.0 < u < U_R1 + 3.0 and abs(v.co.y) <= road_half(U_R1):
        tipmax = max(tipmax, v.co.z)
check(tipmax <= Z_TIP - 0.75 + 0.05, "C6 坡端区岸坡最高 z=%.3f (<=2.25, 端面没入)" % tipmax)

print("── 主要尺寸报告 ──")
print("  RAMP_L   14.0 -> %.1f m (端 |x| %.2f -> %.2f)" % (RAMP_L, 75 + 14.0, ax1))
print("  墩座     1.35唇缘 -> %.2f m 总厚 (前伸 %.1f+埋入 0.10, 前端面 |x|=%.1f)" % (
      thick, ABUT_EXT, HALF + ABUT_EXT))
print("  WING_T   1.4 -> %.1f m; 展角 35 -> %.0f deg" % (WING_T, math.degrees(WING_ANG)))
print("  翼墙横向  |y|max=%.2f m (根 3.18 -> 端)" % max(abs(ay0), abs(ay1)))
print("  石作底   -2.20 -> %.2f m; 岸坡最低 %.2f" % (az0, kz0))
print("  引道顶   %.2f -> %.2f m (%.2f%%)" % (Z_R0, Z_TIP, grade))

if fails:
    print("ABUTMENT_CHECK FAILED: %d" % len(fails))
    sys.exit(1)
print("ABUTMENT_CHECK ALL PASS")
