# Task 5: L2 Blender 内几何判据 + 破坏用例

> 本文件由计划自动抽取，是该任务的**唯一需求来源**，其中数值必须逐字照用。

### Task 5: L2 Blender 内几何判据 + 破坏用例

**Files:**
- Create: `e30_shikongqiao_video/3d/qa_l2.py`

**Interfaces:**
- Consumes: `e30_bridge.blend`（Task 4 构建产物）、facts、bridge_geom2
- Produces: CLI `blender -b e30_bridge.blend --python qa_l2.py -- [out.json] [--negative]`；输出 JSON `{"fail": [...], "warn": [...], "skip": [...], "ok": bool}`；非零退出码=有 fail

- [ ] **Step 1: 写 qa_l2.py（完整实现：对象存在/命名、券石不入净空、内壁法线朝心、impost 计数=34）**

```python
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
    mw = body_ev.matrix_world
    # 2) 券石不入净空(voussoir 顶点禁入任何洞口矩形区)
    d = G
    vos = bpy.data.objects["voussoir"]
    for v in vos.data.vertices:
        p = mw.inverted() @ (vos.matrix_world @ v.co)  # 局部即同坐标系
        for i in range(G.N_SPAN):
            xc = (G.PIER_X[i] + G.PIER_X[i + 1]) / 2.0
            a = G.SPANS[i] / 2.0
            eps = __import__("assumptions").MESH_TOL
            if abs(p.x - xc) < a - 0.02 + eps and p.z < G.SPRINGER + 0.02 and p.z > G.BODY_BOTTOM:
                fail("VOUSSOIR_IN_VOID", "券石顶点入净空超eps 孔%d (%.2f,%.2f)" % (i + 1, p.x, p.z))
                break
        else:
            continue
        break
    # 3) 券洞内壁法线朝心 —— G2 修订: 全部17孔, 非只第9孔。
    #    判据语义: 拱腹采样面的法线与"指向圆心"夹角 < θ_tol(G2: 面法线不能要求精确0°),
    #    离散弦面与圆心连线的理论夹角 = 半扇形角 = π/NSEG_ARC/2 ≈ 2.25°, 取 6° 容差。
    # 负控模式先翻转再测 —— 翻转必须发生在测量之前, 否则负控等于没做(自审R2修复)
    if NEGATIVE:
        flipped = 0
        for poly in me.polygons:
            c = poly.center
            if abs(c.y) < 7.0 and c.z > G.SPRINGER + 0.02 and c.z < G.SPRINGER + max(G.SPANS) and flipped < 10:
                for i in range(G.N_SPAN):
                    xc = (G.PIER_X[i] + G.PIER_X[i + 1]) / 2.0
                    if abs(c.x - xc) < G.SPANS[i] / 2.0:
                        poly.flip(); flipped += 1; break
        me.update()
    THETA = math.radians(6.0)
    neg = 0; tot = 0
    for poly in me.polygons:
        c = poly.center
        if abs(c.y) >= 7.0 or c.z <= G.SPRINGER + 0.02:
            continue
        for i in range(G.N_SPAN):
            xc = (G.PIER_X[i] + G.PIER_X[i + 1]) / 2.0
            a = G.SPANS[i] / 2.0
            dz = c.z - G.SPRINGER
            if abs(c.x - xc) >= a - 0.1 or dz >= a - 0.05:
                continue
            r = math.hypot(c.x - xc, dz)
            if abs(r - a) > 0.15:
                continue
            tot += 1
            dot = (poly.normal.x * (xc - c.x) + poly.normal.z * (-dz)) / (r or 1.0)
            if dot < math.cos(THETA):
                neg += 1
            break
    if tot == 0:
        warns.append({"name": "L2_SAMPLE", "msg": "未采到拱腹面, 判据未执行(skip 语义)"})
    elif neg > 0:
        fail("WALL_NORMAL", "拱腹法线偏离朝心超容差 %d/%d 面" % (neg, tot))
    body_ev.to_mesh_clear()
    # 4) impost 构件语义(G2 修订: 面数≠几何正确; 查34个锚点附近有顶点)
    imp_obj = bpy.data.objects["impost"]
    imp_mw = imp_obj.matrix_world
    vv = [imp_mw @ v.co for v in imp_obj.data.vertices]
    missing = 0
    for i in range(G.N_SPAN):
        xc = (G.PIER_X[i] + G.PIER_X[i + 1]) / 2.0
        for sgn in (-1, 1):
            anchor = Vector((xc + sgn * G.SPANS[i] / 2.0, 0, G.SPRINGER))
            if not any((p - anchor).length < 0.5 for p in vv):
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
```

- [ ] **Step 2.5: 先重建 blend 再判（顺序前置, 调度者 2026-10-04 修正）**

简报顺序有矛盾：T4 只做"冒烟"不重建 blend，T6 才全链重建。若 T5 直接开 `e30_bridge.blend`，验证的是 **Task 6 之前的陈旧产物**（该 blend 的 mtime 是 2026-10-04 20:01，早于 facts.py 建立），判据结论无意义。

必须先重建再判：
```bash
cd /Volumes/macstudio/video-projects/e30_shikongqiao_video/3d
blender -b --factory-startup --python build_scene2.py 2>&1 | grep -E "SAVED|Error"
```
T4 已把 `bridge_geom2` 接到 facts，所以这次重建产出的是**消费 facts 的新几何**。若重建失败（`bridge_geom2` 尚有 facts 未覆盖的字面量），记录缺哪个名字并在报告里列出，**不要**为了让 T5 跑通而手改 blend。

- [ ] **Step 3: 正检跑通 + 负控必须抓到**

Run: `cd /Volumes/macstudio/video-projects/e30_shikongqiao_video/3d && blender -b e30_bridge.blend --python qa_l2.py --python-exit-code 1 -- /tmp/l2.json && cat /tmp/l2.json`
Expected: `QA_L2_OK`，`ok: true`（若报 VOUSSOIR_IN_VOID/WALL_NORMAL，说明现有几何真有病——记录进 FACTS.md 待办，不许改判据迁就）
Run: `blender -b e30_bridge.blend --python qa_l2.py --python-exit-code 1 -- /tmp/l2neg.json --negative; echo "exit=$?"`
Expected: `QA_L2_FAIL`，`exit=1`（负控未被抓=判据无效，必须修判据）

- [ ] **Step 4: Commit**

```bash
cd /Volumes/macstudio/video-projects
git add e30_shikongqiao_video/3d/qa_l2.py
git commit -m "feat(e30): L2 Blender几何判据(对象/净空/法线/impost)+负控自检"
```

---

