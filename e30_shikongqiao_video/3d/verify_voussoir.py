"""券石几何自检: 券石须贴在侧墙外表面, 不得内嵌、不得伸进洞净空。
每条都带反例, 若实现被改坏必须报错。"""
import bpy, sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bridge_geom2 as G


def body_half_width(z, deck_c):
    f = max(0.0, min(1.0, (z - G.BODY_BOTTOM) / (deck_c - G.BODY_BOTTOM)))
    return (G.DECK_DOWN_W + (G.DECK_UP_W - G.DECK_DOWN_W) * f) / 2.0


def check(filepath=None):
    bpy.ops.wm.open_mainfile(filepath=filepath or os.path.join(HERE, "e30_bridge.blend"))
    o = bpy.data.objects.get("voussoir")
    if o is None:
        return ["voussoir 对象不存在"]
    errs = []
    inside = 0
    deepest_embed = 0.0
    for v in o.data.vertices:
        lx, ly, lz = v.co.x, v.co.y, v.co.z
        for i in range(G.N_SPAN):
            xc = (G.PIER_X[i] + G.PIER_X[i + 1]) / 2.0
            a = G.SPANS[i] / 2.0
            if abs(lx - xc) > a + 0.1:
                continue
            # 洞内检查(半圆券部分)
            if lz >= G.SPRINGER - 0.05 and math.hypot(lx - xc, lz - G.SPRINGER) < a - 0.03:
                inside += 1
            # 内嵌检查: 按【该孔自己的】桥面高算侧墙半宽
            deck_c = G.deck_z(xc)
            hw = body_half_width(lz, deck_c)
            deepest_embed = min(deepest_embed, abs(ly) - hw)
            break
    if inside:
        errs.append("券石有 %d 个顶点伸进券洞净空(应为 0)" % inside)
    if deepest_embed < -0.01:
        errs.append("券石内嵌侧墙 %.3f m(应 >= -0.01)。内嵌会在洞内投出横贯暗带" % (-deepest_embed))
    return errs, inside, deepest_embed


if __name__ == "__main__":
    errs, inside, de = check()
    print("券洞内顶点 %d | 最大内嵌 %.4f m" % (inside, de))
    if errs:
        for e in errs:
            print("  FAIL " + e)
        sys.exit(1)
    print("VOUSSOIR_OK")
