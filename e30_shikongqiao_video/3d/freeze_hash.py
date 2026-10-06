# -*- coding: utf-8 -*-
"""核心几何冻结哈希(M2.5 冻结包配套工具, T8)。

用法:
  blender -b e30_bridge.blend --python freeze_hash.py -- out.json

对本体重建三个核心对象(bridge_body/voussoir/impost, 对应 spec M2 本体范围)
取 evaluated mesh(G3 语义: 依赖图求值后), 输出:
  - 顶点/面数
  - 包围盒(世界系, 3 位小数)
  - 顶点内容哈希 sha_sorted(排序后, 与顶点顺序无关) 与 sha_order(文件内顺序)
  坐标量化 1e-4 m(0.1mm) 计入哈希; 浮点全同则两者一致。

冷启动重建(G3 硬门)以此工具输出做删除前后对照: sha_sorted 必须一致;
sha_order 不一致而 sha_sorted 一致 => 布尔求解器顶点顺序非确定, 记入豁免表。
"""
import bpy, sys, json, os, hashlib
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out_path = argv[0] if argv else "core_hash.json"

CORE = ("bridge_body", "voussoir", "coursing")
# [2026-10-06 M19 拓扑跟随] 原第三核心对象 `impost`(M2.5 单 mesh 起拱石)已被
# M18 三区贴面/M19 build_impost 线脚(204 块)并入 `coursing` 对象, 场景中不复
# 存在 —— 冻结第三对象随实体迁移改为 coursing; 末次独立 impost 记录
# 5154f49e49d7af1e52ba3b5cb710b9ada7c8a437295b86c99397e850e6aa0c0a(M2.5 候选)。
# 变更走 body_changelog.md 并同步本文件 §2 哈希与 freeze_manifest §7。


def mesh_sha(obj_name, dg):
    ob = bpy.data.objects[obj_name].evaluated_get(dg)
    me = ob.to_mesh()
    mw = ob.matrix_world
    exact, quant = [], []
    xs, ys, zs = [], [], []
    for v in me.vertices:
        w = mw @ v.co
        exact.append((w.x, w.y, w.z))
        quant.append((round(w.x, 4), round(w.y, 4), round(w.z, 4)))
        xs.append(w.x); ys.append(w.y); zs.append(w.z)
    nfaces = len(me.polygons)
    ob.to_mesh_clear()

    def sha(rows):
        h = hashlib.sha256()
        for r in rows:
            h.update(("%.6f,%.6f,%.6f;" % r).encode("utf-8"))
        return h.hexdigest()

    return {
        "nverts": len(quant),
        "nfaces": nfaces,
        "sha_sorted": sha(sorted(quant)),
        "sha_order": sha(quant),
        "bbox_min": [round(min(xs), 3), round(min(ys), 3), round(min(zs), 3)],
        "bbox_max": [round(max(xs), 3), round(max(ys), 3), round(max(zs), 3)],
    }


def main():
    dg = bpy.context.evaluated_depsgraph_get()
    rep = {"core": {}, "objects_present": sorted(o.name for o in bpy.data.objects)}
    missing = [n for n in CORE if bpy.data.objects.get(n) is None]
    if missing:
        rep["missing"] = missing
    else:
        for n in CORE:
            rep["core"][n] = mesh_sha(n, dg)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=1, sort_keys=True)
    print("CORE_HASH_WRITTEN", out_path)


main()
