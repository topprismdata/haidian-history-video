#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# e30_shikongqiao_video/3d/film/film_render.py
"""P3-T5 Blender 无头渲染驱动: 帧 → 场景状态 → PNG + 选择记录。

用法(blender 内置解释器, 系统 python 不可直跑):
    blender -b -P 3d/film/film_render.py -- --frames 0-0 --out out/film/frames/
    [--blend 3d/out/e30_layout.blend] [--pace ...] [--seq ...]
    [--work out/film/work.blend] [--samples 16]

═══ 驱动纪律(薄执行, 不内嵌判据) ═══
在场判定只 import film_state(单源); 本脚本对每帧仅做机械执行:
  1. GN 阈值显隐: 实例点云写入持久域属性 vis_rank(石按 PLACE_STONE 事件
     全局序的秩, 幻影=哨兵), GN 树加 vis_rank >= vis_idx 删除支(阈值
     vis_idx = len(visible), 一帧一次 socket 写, 逐石零改写)。
  2. 楔石位移: WEDGE-ARCHxx 物体 z = base_z - lambda * WEDGE_DROP_M
     (lambda 直读 film_state.wedge_lambda, 系数单源 film_geometry)。
  3. 券架显隐: CEN-ARCHxx 物体 hide = id 不在 centering_up。
  4. 相机: 相机位姿/投影 = CAMERA_TRACKS[phase](DONE 段内 loc_start→
     loc_end 线性), 参数零重算。
每帧落盘:
  selection.jsonl  {"frame","selected","wedge_lambda","phase","driver"}
                   —— T8 验收与状态机对拍的信任面(计划原文 schema)。
  probe.jsonl      场景回读(楔石物体 z/券架可见布尔/相机实参) ——
                   负控测试断言的取证源(不只看选择记录)。
  timing.json      每帧耗时秒 —— T8 预算表输入。
原料 blend 只读打开, 手术后另存 work.blend, 原件 sha 不变(测试钉)。

═══ 场景结构(T5b 点云扩容, 见 p3-task-5-report §T5b) ═══
本驱动消费 3d/out/film/layout_film.blend(film_layout_build.py 产物, 非本
脚本职责): 5935 石全量点云 × P1_LAYOUT_INSTANCES 同源 GN 树(append 自 P1
layout blend)。A 族(5250 spec 石)=families.blend link 网格; B 族(685
RING/IMPOST)=ledger params.bake 同源还原(p1a_slice 单一真相)。in_void=
excluded 2004; 末帧场景可见实例 3931 == 选择记录 == 状态机 == 账面日程
(四层一线, 主控 T5b 裁决定稿)。该 blend 无相机/无灯/无券架/楔石物体 ——
由本驱动建 work 副本时生成执行脚手架([设计选择], 几何锚取 geom_math
单源; SUN+天光为冒烟可见性脚手架)。
P1 工件(e30_layout.blend / e30_bridge.blend / families.blend)全程只读,
作对照基准, sha 由测试钉。

Python 3.9 语法兼容(本文件只在 blender 内置解释器执行); P2/P3 工件只读。
"""
import argparse
import json
import math
import os
import sys
import time

import bpy
import mathutils

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)              # 3d/ — film_state 直跑入口
for _p in (_PARENT, _HERE):                   # 3d/ + 3d/film/ 双入口
    if _p not in sys.path:
        sys.path.insert(0, _p)

import film_geometry as FG                    # noqa: E402  渲染侧参数单源
import film_state as FS                       # noqa: E402  在场判定单源
from geom_math import arch_center_x, arch_springer_z  # noqa: E402  几何锚单源

__all__ = ["main"]

DEFAULT_BLEND = os.path.join(_PARENT, "out", "film", "layout_film.blend")
DEFAULT_PACE = os.path.join(_PARENT, "out", "film", "pace.json")
DEFAULT_SEQ = os.path.join(_PARENT, "out", "sequence.json")
DEFAULT_WORK = os.path.join(_PARENT, "out", "film", "work.blend")

GN_TREE = "P1_LAYOUT_INSTANCES"               # build_scene2 --layout 产物
VIS_ATTR = "vis_rank"                         # 点云持久域属性(int)
VIS_SOCKET = "vis_idx"                        # GN 树输入 socket(int)
THR_DEL = "Delete Threshold"                  # 新增删除节点名(幂等锚)
THR_CMP = "vis_rank ge vis_idx"
COL_CEN = "COL_CENTERING"
COL_WEDGE = "COL_WEDGES"
PHANTOM_RANK = 2 ** 31 - 1                    # in_void 哨兵(先被 in_void 剔除)
N_HOLES = 17                                  # facts.N_SPAN, 免 import 副本
RES_W, RES_H = 1920, 1080                     # 1080p(spec 冒烟口径)
EEVEE_ENGINES = ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT")


# ────────────────────────── 一次性手术(work 副本) ──────────────────────────

def _hole_of(i):
    """0-based 孔号 → 事件 hole 词表 "ARCH01"。"""
    return "ARCH%02d" % (i + 1)


def placement_ranks(sequence):
    """PLACE_STONE 事件按 seq 全局序 → {stone_id: rank}。

    账面结构早爆: stone_id 缺失 / 重复(同石两事件)在此 raise, 防静默错序。
    """
    evs = sorted((e for e in (sequence.get("events") or ())
                  if e.get("etype") == "PLACE_STONE"), key=lambda e: e["seq"])
    ranks = {}
    for rank, e in enumerate(evs):
        sid = e.get("stone_id")
        if not sid:
            raise RuntimeError("PLACE_STONE seq=%s 缺 stone_id" % e.get("seq"))
        if sid in ranks:
            raise RuntimeError("stone_id 重复出现于 PLACE_STONE: %s" % sid)
        ranks[sid] = rank
    return ranks


def install_vis_threshold():
    """GN 树加 vis_idx 输入 + vis_rank>=vis_idx 删除支; 返回 socket id。

    幂等: 按节点名/socket 名锚定, 重复调用不重复加。默认值 0 = 全删
    (fail-closed: 驱动忘写 socket 时画面为空而非全量)。
    """
    ng = bpy.data.node_groups.get(GN_TREE)
    if ng is None:
        raise RuntimeError("缺 GN 树 %s(原料应为 --layout 产物)" % GN_TREE)
    ident = None
    for it in ng.interface.items_tree:
        if (it.item_type == 'SOCKET' and it.in_out == 'INPUT'
                and it.name == VIS_SOCKET):
            ident = it.identifier
    if ident is None:
        s = ng.interface.new_socket(VIS_SOCKET, in_out='INPUT',
                                    socket_type='NodeSocketInt')
        s.default_value = 0
        ident = s.identifier
    if ng.nodes.get(THR_DEL) is not None:
        return ident
    lk = ng.links.new
    n_del_void = next(n for n in ng.nodes if n.type == 'DELETE_GEOMETRY')
    n_iop = next(n for n in ng.nodes
                 if n.bl_idname == 'GeometryNodeInstanceOnPoints')
    n_in = next(n for n in ng.nodes if n.type == 'GROUP_INPUT')

    n_thr = ng.nodes.new('GeometryNodeDeleteGeometry')
    n_thr.name = THR_DEL
    n_thr.domain = 'POINT'
    n_thr.mode = 'ALL'
    n_rank = ng.nodes.new('GeometryNodeInputNamedAttribute')
    n_rank.name = "vis_rank attr"
    n_rank.data_type = 'INT'
    n_rank.inputs['Name'].default_value = VIS_ATTR
    n_cmp = ng.nodes.new('FunctionNodeCompare')
    n_cmp.name = THR_CMP
    n_cmp.data_type = 'INT'
    n_cmp.operation = 'GREATER_EQUAL'

    lk(n_del_void.outputs['Geometry'], n_thr.inputs['Geometry'])
    lk(n_rank.outputs[0], n_cmp.inputs[0])
    lk(n_in.outputs[ident], n_cmp.inputs[1])
    lk(n_cmp.outputs['Result'], n_thr.inputs['Selection'])
    lk(n_thr.outputs['Geometry'], n_iop.inputs['Points'])
    return ident


def write_vis_ranks(ranks):
    """逐点写 vis_rank; 结构硬断言(四层一线的 scene 层证据):
    非 void 点集 == 已排程集双射(无缺失/无重复/无账外), void = excluded。
    任何失配 raise —— 陈旧/劣质点云在此响亮失败, 不静默。
    """
    seen = {}
    n_void = 0
    unsched_nv = set()
    total = 0
    for ob in bpy.data.objects:
        if not any(m.type == 'NODES' for m in ob.modifiers):
            continue
        me = ob.data
        a_sid = me.attributes.get("sid")
        a_iv = me.attributes.get("in_void")
        if a_sid is None or a_iv is None:
            raise RuntimeError("%s 缺 sid/in_void 域属性" % ob.name)
        a_vr = me.attributes.get(VIS_ATTR)
        if a_vr is None:
            a_vr = me.attributes.new(VIS_ATTR, 'INT', 'POINT')
        for k in range(len(me.vertices)):
            sid = a_sid.data[k].value
            if isinstance(sid, bytes):            # Blender 5.x STRING 为 bytes
                sid = sid.decode("utf-8")
            if sid in ranks and not a_iv.data[k].value:
                a_vr.data[k].value = ranks[sid]
                seen[sid] = seen.get(sid, 0) + 1
            else:
                if a_iv.data[k].value:
                    n_void += 1
                else:
                    unsched_nv.add(sid)           # 账外非 void 变体: 永隐
                a_vr.data[k].value = PHANTOM_RANK
            total += 1
    dup = {s: c for s, c in seen.items() if c > 1}
    if dup:
        raise RuntimeError("石多实例: %s" % sorted(dup)[:5])
    missing = sorted(set(ranks) - set(seen))
    if missing:
        raise RuntimeError("已排程石无实例点: %d 如 %s"
                           % (len(missing), missing[:5]))
    if unsched_nv:
        raise RuntimeError("账外非 void 点: %s" % sorted(unsched_nv)[:5])
    print("VIS_RANK points=%d void=%d scene_instances=%d sched=%d"
          % (total, n_void, len(seen), len(ranks)), flush=True)
    return total, len(seen)


def _box(name, size, center):
    """from_pydata 轴对齐盒(免 ops 上下文依赖)。"""
    me = bpy.data.meshes.new(name)
    hx, hy, hz = (s * 0.5 for s in size)
    cx, cy, cz = center
    me.from_pydata(
        [(cx - hx, cy - hy, cz - hz), (cx + hx, cy - hy, cz - hz),
         (cx + hx, cy + hy, cz - hz), (cx - hx, cy + hy, cz - hz),
         (cx - hx, cy - hy, cz + hz), (cx + hx, cy - hy, cz + hz),
         (cx + hx, cy + hy, cz + hz), (cx - hx, cy + hy, cz + hz)],
        [], [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
             (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)])
    me.validate()
    return bpy.data.objects.new(name, me)


def _link_new(scene, col_name, ob):
    col = bpy.data.collections.get(col_name)
    if col is None:
        col = bpy.data.collections.new(col_name)
        scene.collection.children.link(col)
    if ob.name not in col.objects:
        col.objects.link(ob)


def ensure_stage_geometry(scene):
    """生成券架/楔石执行脚手架([设计选择], 尺寸锚取 geom_math 单源)。

    返回 ({hole: (obj, base_z)}, {cen_id: obj}); 幂等(按名取旧)。
    """
    pitch = abs(arch_center_x(1) - arch_center_x(0))    # 邻孔中心距
    wedges, cens = {}, {}
    for i in range(N_HOLES):
        cx = arch_center_x(i)
        sz = arch_springer_z(i)
        hole = _hole_of(i)
        wz = sz - 0.25                                   # 楔块面贴起拱线下
        wname = "WEDGE-" + hole
        wob = bpy.data.objects.get(wname)
        if wob is None:
            wob = _box(wname, (1.2, 1.0, 0.3), (cx, 0.0, wz))
        wob["base_z"] = wz
        _link_new(scene, COL_WEDGE, wob)
        wedges[hole] = (wob, float(wz))
        cname = "CEN-" + hole
        cobj = bpy.data.objects.get(cname)
        if cobj is None:
            ch = max(0.1, sz - 0.55)                     # 顶面让位楔块
            cobj = _box(cname, (pitch * 0.76, 1.0, ch),
                        (cx, 0.0, 0.05 + ch * 0.5))
        _link_new(scene, COL_CEN, cobj)
        cens[cname] = cobj
    return wedges, cens


def ensure_camera(scene):
    cam = bpy.data.objects.get("CAM_P3_FILM")
    if cam is None:
        cd = bpy.data.cameras.new("CAM_P3_FILM")
        cam = bpy.data.objects.new("CAM_P3_FILM", cd)
        scene.collection.objects.link(cam)
    cam.data.clip_start = 0.1
    cam.data.clip_end = 20000.0      # 大场景: 默认远裁剪面会切体积/远景
    scene.camera = cam
    return cam


def ensure_light_world(scene):
    """冒烟可见性脚手架: P1 layout blend 无灯无 world(渲染全黑)。"""
    if not any(o.type == 'LIGHT' for o in bpy.data.objects):
        ld = bpy.data.lights.new("SUN_P3", 'SUN')
        ld.energy = 3.0
        lo = bpy.data.objects.new("SUN_P3", ld)
        lo.rotation_euler = (math.radians(55), 0.0, math.radians(35))
        scene.collection.objects.link(lo)
    w = scene.world
    if w is None:
        w = bpy.data.worlds.new("World_P3")
        scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    if bg is not None:
        bg.inputs[0].default_value = (0.75, 0.82, 0.92, 1.0)
        bg.inputs[1].default_value = 1.0


def setup_render(scene, out_dir, samples, fps):
    eng = scene.render.engine
    if eng not in EEVEE_ENGINES:
        scene.render.engine = 'BLENDER_EEVEE'        # spec: EEVEE
    scene.render.resolution_x = RES_W
    scene.render.resolution_y = RES_H
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.eevee.taa_render_samples = samples         # 冒烟低采样
    scene.render.fps = fps                           # pace 单源节奏
    scene.render.filepath = out_dir
    return scene.render.engine


def done_domain(pace, sequence):
    """DONE phase 帧域 [done_lo, total); 无落架账返回 None。"""
    starts = sorted({s["start"] for s in pace["stages"]})
    for f in starts:
        if FS.state_at_frame(pace, sequence, f)["phase"] == "DONE":
            return f
    return None


# ────────────────────────── 每帧执行 ──────────────────────────

def apply_camera(cam, phase, f, done_lo, total):
    """相机 = CAMERA_TRACKS[phase]; DONE 段内 loc_start→loc_end 线性。"""
    tr = FG.CAMERA_TRACKS[phase]
    if phase == "DONE" and "loc_start" in tr:
        hi = max(done_lo, total - 1)
        t = 0.0 if hi <= done_lo else (f - done_lo) / float(hi - done_lo)
        t = min(1.0, max(0.0, t))
        a, b = tr["loc_start"], tr["loc_end"]
        loc = tuple(a[k] + (b[k] - a[k]) * t for k in range(3))
    else:
        loc = tuple(tr["loc"])
    cam.location = loc
    d = mathutils.Vector(tr["target"]) - mathutils.Vector(loc)
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    if tr.get("projection") == "ORTHO":
        cam.data.type = 'ORTHO'
        cam.data.ortho_scale = float(tr["ortho_scale"])
    else:
        cam.data.type = 'PERSP'
        cam.data.lens = float(tr.get("lens_mm", 50.0))
    return {"loc": [round(c, 6) for c in loc],
            "type": cam.data.type,
            "ortho_scale": round(cam.data.ortho_scale, 6),
            "lens": round(cam.data.lens, 6),
            "track": FG.CAMERA_TRACKS[phase].get("cam_id", phase)}


def apply_frame(scene, f, st, gn_ident, wedges, cens, cam, done_lo, total,
                n_scene):
    """状态 → 场景态(纯执行), 返回场景回读 probe(负控取证源)。"""
    vis_idx = len(st["visible"])
    for ob in bpy.data.objects:
        for m in ob.modifiers:
            if m.type == 'NODES':
                ins = m.properties.inputs     # Blender 5.2: 输入值走
                if gn_ident not in ins.keys():  # properties.inputs(无 idprops)
                    raise RuntimeError("%s 缺 GN 输入 %s" % (ob.name, gn_ident))
                ins[gn_ident]["value"] = vis_idx   # 一帧一次 socket 写
    for hole, lam in st["wedge_lambda"].items():
        pair = wedges.get(hole)
        if pair is None:
            raise RuntimeError("wedge_lambda 孔 %s 无楔石物体" % hole)
        pair[0].location.z = pair[1] - lam * FG.WEDGE_DROP_M
    for cid, cobj in cens.items():
        up = cid in st["centering_up"]
        cobj.hide_viewport = up is False
        cobj.hide_render = up is False
    cam_probe = apply_camera(cam, st["phase"], f, done_lo, total)
    scene.frame_set(f)
    return {"frame": f, "vis_idx": vis_idx,
            "scene_instances": n_scene,
            "wedge_z": {h: round(p[0].location.z, 6)
                        for h, p in wedges.items()},
            "wedge_base_z": {h: round(p[1], 6) for h, p in wedges.items()},
            "centering_visible": {cid: (not cobj.hide_render)
                                  for cid, cobj in cens.items()},
            "camera": cam_probe,
            "engine": scene.render.engine}


# ────────────────────────── 入口 ──────────────────────────

def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser(description="P3-T5 film render driver")
    ap.add_argument("--frames", required=True, help="a-b 闭区间或单帧 a")
    ap.add_argument("--out", required=True)
    ap.add_argument("--blend", default=DEFAULT_BLEND)
    ap.add_argument("--pace", default=DEFAULT_PACE)
    ap.add_argument("--seq", default=DEFAULT_SEQ)
    ap.add_argument("--work", default=DEFAULT_WORK)
    ap.add_argument("--samples", type=int, default=16)
    a = ap.parse_args(argv)
    if "-" in a.frames:
        lo, hi = a.frames.split("-", 1)
        a.f0, a.f1 = int(lo), int(hi)
    else:
        a.f0 = a.f1 = int(a.frames)
    if a.f0 < 0 or a.f1 < a.f0:
        raise ValueError("--frames 非法: %r" % a.frames)
    return a


def main():
    a = parse_args()
    pace = FS.load_pace(a.pace)
    with open(a.seq, encoding="utf-8") as fh:
        sequence = json.load(fh)
    ranks = placement_ranks(sequence)

    bpy.ops.wm.open_mainfile(filepath=a.blend)       # 原料只读打开
    scene = bpy.context.scene
    os.makedirs(os.path.dirname(a.work), exist_ok=True)
    os.makedirs(a.out, exist_ok=True)

    t0 = time.time()
    gn_ident = install_vis_threshold()
    n_pts, n_scene = write_vis_ranks(ranks)
    wedges, cens = ensure_stage_geometry(scene)
    cam = ensure_camera(scene)
    ensure_light_world(scene)
    engine = setup_render(scene, a.out, a.samples, pace["fps"])
    bpy.ops.wm.save_as_mainfile(filepath=a.work)     # 另存 work, 原件不动
    done_lo = done_domain(pace, sequence)
    init_s = time.time() - t0
    print("INIT gn=%s points=%d wedges=%d cen=%d engine=%s init_s=%.2f"
          % (gn_ident, n_pts, len(wedges), len(cens), engine, init_s),
          flush=True)

    sel_path = os.path.join(a.out, "selection.jsonl")
    prb_path = os.path.join(a.out, "probe.jsonl")
    timings = {}
    total0 = time.time()
    for f in range(a.f0, a.f1 + 1):
        t_f = time.time()
        st = FS.state_at_frame(pace, sequence, f)     # 在场判定单源
        probe = apply_frame(scene, f, st, gn_ident, wedges, cens,
                            cam, done_lo, pace["total_frames"], n_scene)
        scene.render.filepath = os.path.join(a.out, "f%06d.png" % f)
        bpy.ops.render.render(write_still=True)
        dt = time.time() - t_f
        timings[f] = round(dt, 3)
        rec = {"frame": f, "selected": sorted(st["visible"]),
               "wedge_lambda": st["wedge_lambda"], "phase": st["phase"],
               "driver": "film_render"}
        with open(sel_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        with open(prb_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(probe, ensure_ascii=False) + "\n")
        print("TIMING frame=%d sec=%.3f vis_idx=%d"
              % (f, dt, probe["vis_idx"]), flush=True)
    with open(os.path.join(a.out, "timing.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"frames": timings,
                   "total_s": round(time.time() - total0, 3),
                   "init_s": round(init_s, 3),
                   "engine": engine, "samples": a.samples}, fh,
                  ensure_ascii=False, indent=1)
    print("RENDER_DONE frames=%d..%d n=%d wall_s=%.1f"
          % (a.f0, a.f1, a.f1 - a.f0 + 1, time.time() - total0), flush=True)


if __name__ == "__main__":
    main()
