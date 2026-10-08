# -*- coding: utf-8 -*-
"""P3-T5 场景结构探针(只读): 列 collection/物体树/GN 修改器/相机。
输出 JSON 到 stdout, 供报告记录 + 驱动写法设计。不保存 blend。
"""
import json
import sys

import bpy


def obj_summary(o):
    d = {"name": o.name, "type": o.type,
         "hide_viewport": o.hide_viewport,
         "hide_render": o.hide_render,
         "loc": [round(c, 4) for c in o.location]}
    if o.type == "MESH":
        d["verts"] = len(o.data.vertices) if o.data else 0
    for m in o.modifiers:
        d.setdefault("mods", []).append(
            {"name": m.name, "type": m.type,
             "show_viewport": m.show_viewport,
             "show_render": m.show_render})
    return d


def col_tree(col, depth=0):
    node = {"name": col.name, "depth": depth,
            "objects": [o.name for o in col.objects],
            "children": [col_tree(c, depth + 1) for c in col.children],
            "hide_viewport": col.hide_viewport}
    return node


out = {}
sc = bpy.context.scene
out["scene"] = {"name": sc.name,
                "render_engine": sc.render.engine,
                "res": [sc.render.resolution_x, sc.render.resolution_y],
                "fps": sc.render.fps}

# collections 全树
out["collections"] = col_tree(sc.collection)

# 全部物体(含未链接到 master scene collection 的 GN 源)
objs = bpy.data.objects
out["n_objects"] = len(objs)
by_type = {}
for o in objs:
    by_type[o.type] = by_type.get(o.type, 0) + 1
out["objects_by_type"] = by_type

# GN 修改器细节(geometry nodes 实例化入口)
out["gn_mods"] = []
for o in objs:
    for m in o.modifiers:
        if m.type == "NODES":
            g = {"object": o.name, "mod": m.name,
                 "tree": m.node_group.name if m.node_group else None}
            ins = []
            try:
                for item in m.get("Socket_2", []) if False else []:
                    pass
            except Exception:
                pass
            # 输入默认值逐个枚举(接口键名依树而定)
            if m.node_group:
                for it in m.node_group.interface.items_tree:
                    if getattr(it, "in_out", None) == "INPUT" and it.item_type == "SOCKET":
                        try:
                            v = m[it.identifier]
                            if hasattr(v, "to_list"):
                                v = v.to_list()
                            elif hasattr(v, "name"):
                                v = "<%s>" % v.name
                            ins.append({"id": it.identifier, "name": it.name,
                                        "type": it.socket_type, "value": v})
                        except Exception as e:
                            ins.append({"id": it.identifier, "name": it.name,
                                        "err": str(e)})
            g["inputs"] = ins
            out["gn_mods"].append(g)

# 相机
out["cameras"] = [{"name": o.name,
                   "loc": [round(c, 4) for c in o.location],
                   "lens": getattr(o.data, "lens", None),
                   "type": getattr(o.data, "type", None),
                   "ortho_scale": getattr(o.data, "ortho_scale", None)}
                  for o in objs if o.type == "CAMERA"]
sc_cam = sc.camera.name if sc.camera else None
out["scene_camera"] = sc_cam

# GN 节点树内的几何(实例源集合)
out["gn_node_groups"] = []
for ng in bpy.data.node_groups:
    if ng.type == "GEOMETRY":
        srcs = []
        for n in ng.nodes:
            if n.type == "COLLECTION_INFO":
                srcs.append({"node": n.name,
                             "collection": n.inputs["Collection"].default_value.get("name", "?") if n.inputs["Collection"].default_value else None,
                             "instancer": n.instancer_objects.count() if hasattr(n, "instancer_objects") else None})
            if n.type == "DELETE_GEOMETRY":
                srcs.append({"delete_node": n.name, "mode": n.mode})
            if n.type == "INDEX_SWITCH" or "Index" in n.name:
                srcs.append({"indexish": n.name, "type": n.type})
        out["gn_node_groups"].append({"name": ng.name, "nodes_total": len(ng.nodes),
                                      "detail": srcs[:40]})

# 名字特征抽样: 石/CEN/楔
names = sorted(o.name for o in objs)
feat = {}
for pat in ("CEN-", "WEDGE", "ARCH", "CAM_", "KEYSTONE", "keystone"):
    feat[pat] = [n for n in names if pat in n][:40]
out["name_features"] = feat

json.dump(out, sys.stdout, ensure_ascii=False, indent=1, default=str)
