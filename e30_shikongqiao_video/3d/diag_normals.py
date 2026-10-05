"""诊断: 券洞内壁法线方向。负点积 = 法线朝外 = 破面(渲染成黑楔)。"""
import bpy, sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bridge_geom2 as G
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "e30_bridge.blend"))
me = bpy.data.objects["bridge_body"].data
x9 = (G.PIER_X[8] + G.PIER_X[9]) / 2.0
a9 = G.SPANS[8] / 2.0
b9 = a9 * 2.0 * G.ARCH_RATIO
inner = []
for p in me.polygons:
    c = p.center
    if abs(c.x - x9) < a9 - 0.1 and G.SPRINGER - 0.1 < c.z < G.SPRINGER + b9 - 0.05 and abs(c.y) < 7.0:
        # 洞心在该高度上的 x 位置
        dz = c.z - G.SPRINGER
        if dz <= 0: continue
        half = math.sqrt(max(0.0, a9*a9 - dz*dz)) if dz <= b9 else 0.0
        if half <= 0.01: continue
        cxp = x9 + math.copysign(half, c.x - x9)
        nx, nz = c.x - cxp, c.z - (G.SPRINGER + max(0.0, math.sqrt(max(0.0, a9*a9 - (c.x-x9)**2))))
        L = math.hypot(nx, nz) or 1.0
        dot = (p.normal.x * nx + p.normal.z * nz) / L
        inner.append((dot, p.normal.y, round(c.z, 2)))
print("券洞内壁面数 %d" % len(inner))
if inner:
    dots = [d[0] for d in inner]
    neg = sum(1 for d in dots if d < 0)
    print("  法线·(指向洞心): min %.2f max %.2f" % (min(dots), max(dots)))
    print("  朝外(破面)面数 %d / %d" % (neg, len(dots)))
    print("  y 法线分量 %.2f..%.2f" % (min(d[1] for d in inner), max(d[1] for d in inner)))
    print("  VERDICT:", "破面存在, 需翻法线" if neg > 0 else "法线正确")
