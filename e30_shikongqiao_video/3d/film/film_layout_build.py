#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# e30_shikongqiao_video/3d/film/film_layout_build.py
"""P3-T5b film 点云扩容 builder: ledger_sequenced 5935 石全量 →
out/film/layout_film.blend(20 分区点云 × P1_LAYOUT_INSTANCES 同源 GN 树)。

═══ 裁决背景(主控 2026-10-08 T5b) ═══
P1 几何链(spec/layout 5250)与 P2 账(5935)并存是设计使然; film 需要 5935
全量实例表征 → P3 自有资产重建点云, 零触 P1 工件(P1 layout blend 与
e30_bridge.blend 只读保留作对照基准)。

═══ 网格来源层级(裁决钉死, proxy 网格禁用) ═══
  A(5250 spec 石): families.blend COL_FAMILIES 现成 2824 族对象 —— 随
    GN 树 append 从 P1 layout blend 拖带(link), 名字/序号零重排;
  B(685 RING/IMPOST): ledger_sequenced params.bake 同源还原 —— bake 由
    p1a_slice 逐石重放 masonry 单一真相图元提取(顶点多重集互证), 本
    builder 经 families.family_mesh 确定性还原, 不含第二套砌体公式。

═══ 同源函数(全部 import build_scene2/families, blender-free 段) ═══
  identity/census: family_identity(跨洞裁剪石 uniq, 其余 (family,params))
  点位: placement_point = family_center + masonry2.anchor_offset
  局部网格: centered_verts(family_center 平移到原点; 组合≡materialize, P1 测钉)
  分区: layout_group(CORE 石按块心 x, 其余按孔 SPANxx)

═══ fam_idx 序约定(与 P1 同构) ═══
  A 键: P1 emit 序号(嵌名 fam_NNNN_, 0..2823); B 键: 2824+rank(嵌名续排)。
  sorted(对象名) == fam_idx 序(PickInstance 序双保险, 同 P1)。

═══ 显隐语义(四层一线, 裁决定稿) ═══
  in_void = id ∉ PLACE_STONE 日程(excluded 2004, GN 首支剔除); 排程
  3931 全部获得实例(此前 50 颗"已排程几何内藏"异常随点云重建消解)。
  末帧: 场景可见实例 3931 == 选择记录 == 状态机 == 账面日程。

用法:
  blender -b -P 3d/film/film_layout_build.py --            # 构建
  blender -b -P 3d/film/film_layout_build.py -- --verify-only --json /tmp/x.json
      # 复检已存 blend(独立重开只读), 输出 blend 事实 JSON 供 pytest 对账
Python 3.9 语法兼容。
"""
import argparse
import json
import os
import sys
import time

import bpy

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
for _p in (_PARENT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import build_scene2 as B                      # noqa: E402  同源几何/清点函数
import families as FAM                        # noqa: E402  bake 确定性还原

P1_LAYOUT = os.path.join(_PARENT, "out", "e30_layout.blend")
LEDGER = os.path.join(_PARENT, "out", "ledger_sequenced.json")
SEQ = os.path.join(_PARENT, "out", "sequence.json")
DEFAULT_OUT = os.path.join(_PARENT, "out", "film", "layout_film.blend")

GN_TREE = "P1_LAYOUT_INSTANCES"
COL_FAM = "COL_FAMILIES"
# N_A [拱线族返工 2026-10-08 改派生] 旧硬钉 2824(P1 族对象数)随几何换族失效:
# uniq 跨洞裁剪石族由几何重推导, families.blend 重出后 A 族数 2824→2832,
# 硬钉使 b_rank(N_A+i) 与 A 族尾段重号 → 族名序号断链@2825。
# 现以单源重算 plan 的 len(a_index) 为准(与 A 侧 got_names==a_names 对账互证)。


# ────────────────────── 纯数据侧(单源重算, blender-free) ──────────────────────

def load_inputs(ledger_path, seq_path):
    with open(ledger_path, encoding="utf-8") as fh:
        stones = json.load(fh)["stones"]
    with open(seq_path, encoding="utf-8") as fh:
        seq = json.load(fh)
    sched = {e["stone_id"] for e in (seq.get("events") or ())
             if e.get("etype") == "PLACE_STONE"}
    return stones, sched


def compute_plan(stones, sched):
    """单源重算: 族键/A 序号/B 键/逐石点位分区。返回 plan dict。"""
    spec = B.bridge_ledger()["stones"]
    spec_ids = {s["id"] for s in spec}
    st_spec = B.classify_stones(spec)
    cens_a = B.census(spec, st_spec)
    keys_a = sorted(cens_a)
    a_index = {k: i for i, k in enumerate(keys_a)}

    st_all = B.classify_stones(stones)
    cens_all = B.census(stones, st_all)
    keys_all = sorted(cens_all)
    miss = set(keys_a) - set(keys_all)
    if miss:
        raise RuntimeError("A 键不在全量清点(账退化): %s" % sorted(miss)[:3])
    n_a = len(keys_a)                            # 派生 A 族数(原硬钉 N_A=2824 已废)
    b_keys = [k for k in keys_all if k not in cens_a]
    b_rank = {k: n_a + i for i, k in enumerate(b_keys)}

    by_key = {}
    for k in keys_all:
        by_key[k] = cens_all[k]
    rows = []
    for s in stones:
        key = B.family_identity(s, st_all[s["id"]][0])
        rows.append({
            "sid": s["id"],
            "zone": B.layout_group(s),
            "point": B.placement_point(s),
            "rot": tuple(float(c) for c in s["transform"][3:6]),
            "fam_idx": (a_index[key] if key in a_index else b_rank[key]),
            "in_void": s["id"] not in sched,
            "family": s["family"],
            "key": key,
        })
    return {"rows": rows, "a_index": a_index, "b_rank": b_rank,
            "cens_a": cens_a, "cens_all": cens_all,
            "b_keys": b_keys, "sched": sched, "n_a": n_a}


# ────────────────────── blender 构建 ──────────────────────

def _bytes_attr(me, name, data):
    a = me.attributes.new(name, 'STRING', 'POINT')
    for k, v in enumerate(data):
        a.data[k].value = v.encode("utf-8")     # Blender 5.x STRING 为 bytes
    return a


def _vec_attr(me, name, data):
    a = me.attributes.new(name, 'FLOAT_VECTOR', 'POINT')
    for k, v in enumerate(data):
        a.data[k].vector = tuple(v)
    return a


def build(out_path, plan):
    t0 = time.time()
    N_A = plan["n_a"]          # 派生 A 族数(单源 plan, 原模块硬钉已废)
    rows = plan["rows"]
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # 1) GN 树 append(P1 layout blend; 连带拖入 COL_FAMILIES 2824 link 对象;
    #    collection 本体仍 link 只读 → 另建本地 COL_FAMILIES_FILM 装
    #    A(link 对象)+B(本地网格), 再回接 Collection Info 指针)
    with bpy.data.libraries.load(P1_LAYOUT, link=False, relative=True) as (src, dst):
        dst.node_groups = [GN_TREE]
    ng = bpy.data.node_groups.get(GN_TREE)
    if ng is None:
        raise RuntimeError("GN 树 append 失败: %s" % P1_LAYOUT)
    col_src = bpy.data.collections.get(COL_FAM)
    if col_src is None:
        raise RuntimeError("append 未拖入 %s" % COL_FAM)
    col = bpy.data.collections.new(COL_FAM + "_FILM")
    for ob in list(col_src.objects):
        col.objects.link(ob)

    # 2) A 族对象名与单源重放逐一对账(陈旧 families.blend 在此响亮失败)
    a_names = {B.family_obj_name(k, i) for k, i in plan["a_index"].items()}
    got_names = {o.name for o in col.objects}
    if got_names != a_names:
        raise RuntimeError("families.blend 族名与单源重放不符(陈旧?): "
                           "got=%d want=%d diff=%s"
                           % (len(got_names), len(a_names),
                              sorted(got_names ^ a_names)[:4]))

    # 3) B 族对象(params.bake 同源还原, 本地名续排 N_A+rank)
    for k in plan["b_keys"]:
        rep = plan["cens_all"][k]
        verts, faces = FAM.family_mesh(rep["family"], rep["params"])
        c = B.family_center(rep)
        cv = [(v[0] - c[0], v[1] - c[1], v[2] - c[2]) for v in verts]
        name = B.family_obj_name(k, plan["b_rank"][k])
        me = bpy.data.meshes.new(name)
        me.from_pydata(cv, [], [tuple(f) for f in faces])
        me.validate()
        ob = bpy.data.objects.new(me.name, me)
        col.objects.link(ob)

    # 4) PickInstance 序双保险: sorted(名) == 序号(同 P1 约定)
    names = sorted(o.name for o in col.objects)
    for i, n in enumerate(names):
        if int(n.split("_")[1]) != i:
            raise RuntimeError("族名序号断链 @%d: %s" % (i, n))

    # 4b) 回接 GN Collection Info 指针到本地 collection。
    #     注: 不做 orphans_purge —— 5.2 实证 purge 不认节点指针用户, 会把
    #     仅被 CI 指针引用的本地 collection 连根删掉; 残留的 link 版
    #     COL_FAMILIES 无用户, 随文件保存不参与 view layer, 无害。
    ci = next(n for n in ng.nodes if n.type == 'COLLECTION_INFO')
    ci.inputs['Collection'].default_value = col
    if len(col.objects) != N_A + len(plan["b_keys"]):
        raise RuntimeError("族对象数不符: %d" % len(col.objects))

    # 5) 20 分区点云(schema 同 P1 layout: sid/fam/fam_idx/stage/mat/xyz/rot/in_void)
    zones = {}
    for r in rows:
        zones.setdefault(r["zone"], []).append(r)
    for zname in sorted(zones):
        zrows = sorted(zones[zname], key=lambda r: r["sid"])
        me = bpy.data.meshes.new("pts_" + zname)
        me.from_pydata([r["point"] for r in zrows], [], [])
        me.validate()
        _bytes_attr(me, "sid", [r["sid"] for r in zrows])
        _bytes_attr(me, "fam", [r["family"] for r in zrows])
        a = me.attributes.new("fam_idx", 'INT', 'POINT')
        for k, r in enumerate(zrows):
            a.data[k].value = r["fam_idx"]
        _bytes_attr(me, "stage", [(r["sid"] and "") for r in zrows])
        _bytes_attr(me, "mat", ["" for _ in zrows])
        _vec_attr(me, "xyz", [r["point"] for r in zrows])
        _vec_attr(me, "rot", [r["rot"] for r in zrows])
        a = me.attributes.new("in_void", 'BOOLEAN', 'POINT')
        for k, r in enumerate(zrows):
            a.data[k].value = r["in_void"]
        zc = bpy.data.collections.new(zname)
        bpy.context.scene.collection.children.link(zc)
        ob = bpy.data.objects.new("pts_" + zname, me)
        m = ob.modifiers.new("gn", 'NODES')
        m.node_group = ng
        zc.objects.link(ob)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out_path)
    n_void = sum(1 for r in rows if r["in_void"])
    print("BUILD out=%s points=%d families=%d b_objs=%d in_void=%d "
          "scheduled=%d init_s=%.2f"
          % (out_path, len(rows), len(col.objects), len(plan["b_keys"]),
             n_void, len(plan["sched"]), time.time() - t0), flush=True)
    for z in sorted(zones):
        print("BUILD_ZONE %s %d" % (z, len(zones[z])), flush=True)


# ────────────────────── 独立复检(重开已存文件, 只读) ──────────────────────

def verify(blend_path, ledger_path, seq_path):
    """读 blend 事实 → JSON(stdout): pytest 与单源账对账; 此处不做判。"""
    stones, sched = load_inputs(ledger_path, seq_path)
    plan = compute_plan(stones, sched)
    bpy.ops.wm.open_mainfile(filepath=blend_path)
    ng = bpy.data.node_groups.get(GN_TREE)
    col = bpy.data.collections.get(COL_FAM + "_FILM")
    ci = next((n for n in ng.nodes if n.type == 'COLLECTION_INFO'), None) if ng else None
    ptr = ci.inputs['Collection'].default_value if ci else None
    zones = {}
    sample = []
    nonvoid_ids = set()
    n_void = 0
    total = 0
    all_rows = []
    expect = {r["sid"]: r for r in plan["rows"]}
    for ob in bpy.data.objects:
        if not ob.name.startswith("pts_"):
            continue
        me = ob.data
        a_sid = me.attributes["sid"]
        a_fi = me.attributes["fam_idx"]
        a_iv = me.attributes["in_void"]
        a_xyz = me.attributes["xyz"]
        a_rot = me.attributes["rot"]
        zname = ob.name[4:]
        for k in range(len(me.vertices)):
            sid = a_sid.data[k].value
            if isinstance(sid, bytes):
                sid = sid.decode("utf-8")
            total += 1
            if a_iv.data[k].value:
                n_void += 1
            else:
                nonvoid_ids.add(sid)
            zones[zname] = zones.get(zname, 0) + 1
            all_rows.append({
                "sid": sid, "zone": zname,
                "xyz": [round(c, 9) for c in a_xyz.data[k].vector],
                "rot": [round(c, 9) for c in a_rot.data[k].vector],
                "fam_idx": a_fi.data[k].value})
    # 定步长抽 100 石(排序 sid 全域, 含 void): 对账可复现
    stride = max(1, len(all_rows) // 100)
    sample = sorted(all_rows, key=lambda r: r["sid"])[::stride][:100]
    want_zones = {}
    for r in plan["rows"]:
        want_zones[r["zone"]] = want_zones.get(r["zone"], 0) + 1
    out = {
        "blend": blend_path,
        "total_points": total,
        "in_void": n_void,
        "nonvoid": len(nonvoid_ids),
        "nonvoid_eq_sched": nonvoid_ids == set(plan["sched"]),
        "zones": zones,
        "want_zones": want_zones,
        "families": len(col.objects) if col else 0,
        "gn_tree": ng.name if ng else None,
        "gn_nodes": len(ng.nodes) if ng else 0,
        "ci_ptr": ptr.name if ptr else None,
        "sample": sample,
        "expect_sample": [{"sid": s["sid"], "zone": expect[s["sid"]]["zone"],
                           "xyz": [round(c, 9) for c in expect[s["sid"]]["point"]],
                           "rot": [round(c, 9) for c in expect[s["sid"]]["rot"]],
                           "fam_idx": expect[s["sid"]]["fam_idx"]}
                          for s in sample],
    }
    print("VERIFY_JSON %s" % json.dumps(out, ensure_ascii=False), flush=True)
    return out


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser(description="P3-T5b film layout builder")
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--ledger", default=LEDGER)
    ap.add_argument("--seq", default=SEQ)
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument("--json", default=None, help="verify 输出文件")
    a = ap.parse_args(argv)
    if a.verify_only:
        out = verify(a.out, a.ledger, a.seq)
        if a.json:
            with open(a.json, "w", encoding="utf-8") as fh:
                json.dump(out, fh, ensure_ascii=False, indent=1)
        return
    stones, sched = load_inputs(a.ledger, a.seq)
    plan = compute_plan(stones, sched)
    build(a.out, plan)


if __name__ == "__main__":
    main()
