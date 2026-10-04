# -*- coding: utf-8 -*-
"""E30 本体判据 L2: 开 blend 查顶点。用法:
  blender -b e30_bridge.blend --python qa_l2.py -- out.json          # 正检
  blender -b e30_bridge.blend --python qa_l2.py -- out.json --negative  # 负控自检(必须fail)
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
    fails, warns = [], []
    def fail(n, m): fails.append({"name": n, "msg": m})
    # 1) 对象存在
    for n in ("bridge_body", "voussoir", "impost"):
        o = bpy.data.objects.get(n)
        if o is None:
            fail("OBJ_EXIST", "缺对象 %s" % n)
    if fails:
        return _emit(fails, warns)
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
    for v in vos_me.vertices:
        p = v.co                               # 局部系(框架修订, 见上)
        for i in range(G.N_SPAN):
            xc = (G.PIER_X[i] + G.PIER_X[i + 1]) / 2.0
            a = G.SPANS[i] / 2.0
            if abs(p.x - xc) >= a:
                continue                      # 横向已在孔外, 不是本孔的事
            dz = p.z - G.SPRINGER
            if dz < 0.0 or dz > a:
                continue                      # 纵向不在起拱线以上
            r = math.hypot(p.x - xc, dz)
            if r < a - eps:
                fail("VOUSSOIR_IN_VOID",
                     "券石侵入净空 孔%d 顶点(%.2f,%.2f) 到心距%.4f < 拱腹半径%.4f-eps"
                     % (i + 1, p.x, p.z, r, a))
                break
        else:
            continue
        break
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
        if abs(c.y) >= 7.0 or c.z <= G.SPRINGER + 0.02 or abs(poly.normal.y) >= 0.5:
            return None
        for i in range(G.N_SPAN):
            xc = (G.PIER_X[i] + G.PIER_X[i + 1]) / 2.0
            a = G.SPANS[i] / 2.0
            dz = c.z - G.SPRINGER
            if abs(c.x - xc) >= a - 0.1 or dz >= a - 0.05:
                continue
            r = math.hypot(c.x - xc, dz)
            if abs(r - a) > 0.15:
                continue
            return (xc, r, dz)
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
        xc, r, dz = hit
        tot += 1
        dot = (poly.normal.x * (xc - poly.center.x) + poly.normal.z * (-dz)) / (r or 1.0)
        if dot < math.cos(THETA):
            neg += 1
    if tot == 0:
        warns.append({"name": "L2_SAMPLE", "msg": "未采到拱腹面, 判据未执行(skip 语义)"})
    elif neg > 0:
        fail("WALL_NORMAL", "拱腹法线偏离朝心超容差 %d/%d 面" % (neg, tot))
    body_ev.to_mesh_clear()
    # 4) impost 构件语义(G2 修订: 面数≠几何正确; 查34个锚点附近有顶点)
    #    锚点修订(2026-10-04 实测): 简报逐字版锚点 y=0 取 3D 距离, 但起拱线石按构造
    #    贴在券洞两侧墙 |y|=hw±0.06(hw≈4.7~5.4), y=0 处永无顶点 -> 正检假红 34/34
    #    (实测证据见 task-task-5-report)。锚点语义"起拱线处有石"是 x×z(桥轴纵剖面)
    #    陈述, 距离改取 xz 平面距离, 阈值 0.5 不变。
    imp_obj = bpy.data.objects["impost"]
    vv = [v.co for v in imp_obj.data.vertices]     # 局部系(框架修订, 见上)
    missing = 0
    for i in range(G.N_SPAN):
        xc = (G.PIER_X[i] + G.PIER_X[i + 1]) / 2.0
        for sgn in (-1, 1):
            anchor = Vector((xc + sgn * G.SPANS[i] / 2.0, 0, G.SPRINGER))
            if not any(math.hypot(p.x - anchor.x, p.z - anchor.z) < 0.5 for p in vv):
                missing += 1
    if missing:
        fail("IMPOST_ANCHOR", "起拱线石缺位锚点 %d/34" % missing)
    _emit(fails, warns)

def _emit(fails, warns):
    rep = {"fail": fails, "warn": warns, "ok": not fails}
    with open(out_path, "w", encoding="utf-8") as fp:
        json.dump(rep, fp, ensure_ascii=False, indent=1)
    print("QA_L2_OK" if not fails else "QA_L2_FAIL %d" % len(fails))
    if fails:
        sys.exit(1)

main()
