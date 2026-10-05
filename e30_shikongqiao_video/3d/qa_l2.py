# -*- coding: utf-8 -*-
"""E30 本体判据 L2: 开 blend 查顶点。用法:
  blender -b e30_bridge.blend --python qa_l2.py -- out.json          # 正检
  blender -b e30_bridge.blend --python qa_l2.py -- out.json --negative  # 负控自检

退出码语义(2026-10-05 终审 I4/I6; 项目铁律: skip=未执行不算通过):
  正检     0 = ok(判据确实执行且零 fail 零 skip); 1 = 有 fail 或有 skip。
           采样带零命中 → 记入 "skip" 且 ok=false —— 判据没跑绝不能算通过
           (修复前: tot==0 只记 warn, ok=true, 真 blend 实测 QA_L2_OK 假绿)。
  --negative 0 = 负控按预期抓到破坏(护栏健在);
             1 = 负控脱靶(翻转零命中, 扰动没打到被测总体)或翻转后判据仍全绿
             (恒真嫌疑) —— 两者都必须报错退出, 不能静默通过(D4/I6 事故护栏)。
"""
import bpy, sys, json, math, os
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import facts as F
import bridge_geom2 as G
from assumptions import MESH_TOL

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out_path = argv[0] if argv else "qa_l2_report.json"
NEGATIVE = "--negative" in argv

def main():
    fails, warns, skips = [], [], []
    flipped = 0
    def fail(n, m): fails.append({"name": n, "msg": m})
    # 1) 对象存在
    for n in ("bridge_body", "voussoir"):
        o = bpy.data.objects.get(n)
        if o is None:
            fail("OBJ_EXIST", "缺对象 %s" % n)
    if fails:
        return _emit(fails, warns, skips)
    # G3: 必须查 evaluated mesh(依赖图), 否则活修改器下查的是布尔前网格 -> 假绿
    dg = bpy.context.evaluated_depsgraph_get()
    def evaluated(name):
        ob = bpy.data.objects[name].evaluated_get(dg)
        return ob, ob.to_mesh()
    body_ev, me = evaluated("bridge_body")
    # 框架修订(2026-10-04 实测): build_scene2 给所有对象加了 rotation_euler.z=-112°
    # (BRIDGE_AXIS_AZ 轴旋转, 实测 bridge_body rotation_euler.z=-1.9548), 对象 location
    # 全为原点。世界系 x 混入桥轴 y, 简报逐字版用 matrix_world 读世界坐标 -> 券石/法线
    # 判据全假红(实测 VOUSSOIR 假阳 1 例、WALL_NORMAL 520/520 全灭)。facts/bridge_geom2
    # 常量定义在桥轴局部系, to_mesh() 返回局部系网格 —— 判据一律读局部坐标。
    # evaluated mesh 本身保留(G3 语义不变)。
    # 2) 券石不入净空 —— 2026-10-04 修正(主控实测): 原判据缺径向条件, 会误杀整条券石。
    #    券石骑跨在拱圈上, 内缘就是拱腹(半径 a), 其顶点本就落在"孔的矩形范围"内, 那是
    #    正常构造不是缺陷。实测: 半圆券上 15°~90° 的券石顶点全部满足原判据的入净空条件。
    #    正确判据: 顶点落在净空内 **且** 到圆心的距离 **小于** a-MESH_TOL 才算侵入净空
    #    (即券石吃进了拱腹以内), 券石在 r >= a-MESH_TOL 全部合法。
    eps = MESH_TOL
    vos = bpy.data.objects["voussoir"]
    vos_ev = vos.evaluated_get(dg)
    vos_me = vos_ev.to_mesh()
    bad = None
    for v in vos_me.vertices:
        p = v.co
        for i in range(G.N_SPAN):
            a = G.SPANS[i] / 2.0
            xc = (G.PIER_X[i] + G.PIER_X[i + 1]) / 2.0
            if abs(p.x - xc) >= a - eps:
                continue
            spz = G.arch_springer_z(i)
            b = G.arch_rise(i)
            if p.z < spz - 0.05:
                continue
            # 侵入净空: 顶点低于真实尖拱 intrados(拱洞在曲线以下)
            if p.z < G.arch_z(p.x, xc, spz, a, b) - eps:
                bad = (i + 1, p.x, p.z, G.arch_z(p.x, xc, spz, a, b))
                break
        if bad:
            break
    if bad:
        fail("VOUSSOIR_IN_VOID",
             "券石侵入净空 孔%d 顶点(%.2f,%.2f) 低于 intrados %.2f" % bad)
    vos_ev.to_mesh_clear()
    # 3) 券洞内壁法线朝心 —— G2 修订: 全部17孔, 非只第9孔。
    #    判据语义: 拱腹采样面的法线与"指向圆心"夹角 < θ_tol(G2: 面法线不能要求精确0°),
    #    离散弦面与圆心连线的理论夹角 = 半扇形角 = π/NSEG_ARC/2 ≈ 2.25°, 取 6° 容差。
    #    采样修订(2026-10-04 实测): 采样带内混有 26/520 个 carve 在洞缘并出的倾斜
    #    n-gon(|ny|≈0.878, 与朝心夹角 63°~69°, 9~15 边), 那是洞口缘饰刻面不是拱腹面;
    #    拱腹面 |ny|<0.03。判据测的是"拱腹采样面", 加 |ny|<0.5 径向面过滤 —— 否则即使
    #    拱圈法线全部修复, 这 26 个缘饰刻面也永远假红(翻面救不了斜法线), 判据不可收敛。
    #    实测明细见 task-task-5-report; 缘饰刻面本身另记缺陷待办, 不由本判据承担。
    # 负控模式先翻转再测 —— 翻转必须发生在测量之前, 否则负控等于没做(自审R2修复);
    # 且翻转目标必须与测量用同一采样带(R3, 2026-10-04 实测): 原实现翻"前10个任意拱区
    # 面", 实测 10 个全落在采样带外, 修复网格上负控测出 0 坏照常放行 —— 扰动没打到
    # 被测总体, 负控形同虚设。现翻"采样带内前10面", 保证必命中被测属性。
    def band_hit(poly):
        c = poly.center
        if abs(c.y) >= 7.0 or abs(poly.normal.y) >= 0.5:
            return None
        for i in range(G.N_SPAN):
            xc = (G.PIER_X[i] + G.PIER_X[i + 1]) / 2.0
            a = G.SPANS[i] / 2.0
            spz = G.arch_springer_z(i)          # M12: 逐孔起拱线随桥面
            if c.z <= spz + 0.02:
                return None
            b = G.arch_rise(i)
            if abs(c.x - xc) >= a - 0.1:
                continue
            az = G.arch_z(c.x, xc, spz, a, b)   # 真实尖拱 intrados
            if abs(c.z - az) > 0.15 or c.z <= spz + 0.02:
                continue
            return (xc, az, a, b, spz)
        return None
    if NEGATIVE:
        flipped = 0
        for poly in me.polygons:
            if flipped >= 10:
                break
            if band_hit(poly) is not None:
                poly.flip(); flipped += 1
        me.update()
        print("QA_L2_NEG: 翻转 %d 个采样带拱腹面" % flipped)
    THETA = math.radians(6.0)
    neg = 0; tot = 0
    for poly in me.polygons:
        hit = band_hit(poly)
        if hit is None:
            continue
        xc, az, a, b, spz = hit
        tot += 1
        d = G.arch_dzdx(poly.center.x, xc, spz, a, b)               # 尖拱切线斜率
        ix, iz = d / math.hypot(d, 1.0), -1.0 / math.hypot(d, 1.0)  # 指向拱内(下)法线
        dot = poly.normal.x * ix + poly.normal.z * iz
        if dot < math.cos(THETA):
            neg += 1
    if tot == 0:
        # I4(2026-10-05 终审): 判据未执行必须算不通过。skip≠pass —— 记入 skips,
        # _emit 使 ok=false 并以非零码退出(修复前只记 warn 且 ok=true, 假绿)。
        skips.append({"name": "L2_SAMPLE",
                      "msg": "未采到拱腹面, 判据未执行(skip≠通过); 检查采样带参数/网格"})
    elif neg > 0:
        fail("WALL_NORMAL", "拱腹法线偏离朝心超容差 %d/%d 面" % (neg, tot))
    body_ev.to_mesh_clear()
    # (M12: IMPOST_ANCHOR 判据随 impost 立体构件一并移除; 起拱线改材质表达)
    _emit(fails, warns, skips, tot=tot, neg=neg, flipped=flipped)

def _emit(fails, warns, skips, tot=None, neg=None, flipped=0):
    """ok = 零 fail 且零 skip(2026-10-05 终审 I4: 判据未执行不算通过)。
    JSON 显式区分 fail / warn / skip 三级, 与 bridge3d LEVELS 同语义。"""
    rep = {"fail": fails, "warn": warns, "skip": skips,
           "ok": (not fails and not skips)}
    if tot is not None:
        rep["sampled"] = tot           # 判据确实执行的面数(0 = 未执行, 见 skip)
    if NEGATIVE:
        # I6: 负控必须证明"能红"。翻转零命中(脱靶)或翻转后仍全绿(恒真)都报错退出。
        caught = bool(neg) and flipped > 0
        rep["negative"] = {"flipped": flipped, "bad_faces": neg or 0, "caught": caught}
        with open(out_path, "w", encoding="utf-8") as fp:
            json.dump(rep, fp, ensure_ascii=False, indent=1)
        if flipped == 0:
            print("QA_L2_NEG_MISS: 负控零命中(采样带内无可翻转面)——扰动未打到被测总体, 拒绝静默通过")
            sys.exit(1)
        if caught:
            print("QA_L2_NEG_CAUGHT: 翻转 %d 面全部被 WALL_NORMAL 抓到(%d/%d 坏面)——护栏健在"
                  % (flipped, neg, tot))
            sys.exit(0)
        print("QA_L2_NEG_NOT_CAUGHT: 翻转 %d 面后判据仍全绿——恒真嫌疑, 必须介入" % flipped)
        sys.exit(1)
    with open(out_path, "w", encoding="utf-8") as fp:
        json.dump(rep, fp, ensure_ascii=False, indent=1)
    print("QA_L2_OK" if rep["ok"] else
          "QA_L2_FAIL %d fail, %d skip" % (len(fails), len(skips)))
    if not rep["ok"]:
        sys.exit(1)

main()
