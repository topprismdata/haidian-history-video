# -*- coding: utf-8 -*-
"""P1-T7 场景三模式纯逻辑单测(blender-free; 不渲桥)。

覆盖:
- masonry2.materialize(U2 全局唯一放置算子): wedge 前脸 y == transform y、
  slab 世界 bbox == params.bbox、旋转绕块中心、纯函数不改写输入;
- build_scene2 纯逻辑段: void 足印分类(内/外/裁剪)、裁剪棱柱水密正体积、
  族清点/身份、全桥账目链结构、GN 实例组合恒等 materialize、layout 分区;
- export_print 默认 mesh_fn(= materialize 回床)与显式 family 路径平移等价。
"""
import copy
import json
import os
import struct
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "3d"))
import build_scene2 as BS  # noqa: E402  # bpy 缺失 -> 守护导入, 纯逻辑可用
import masonry2 as M2  # noqa: E402
import families as FAM  # noqa: E402
import ledger as LED  # noqa: E402
import export_print as EP  # noqa: E402
import facts as F  # noqa: E402
from assumptions import BODY_BOTTOM  # noqa: E402

SPEC = {"courses": [
    {"z0": 2.0, "blocks": [{"x0": 0.0, "x1": 1.2}, {"x0": 1.2, "x1": 2.0}]},
    {"z0": 2.55, "blocks": [{"x0": 0.0, "x1": 0.8}, {"x0": 0.8, "x1": 2.0}]}]}


def _hw(x, z):
    return 6.0 - 0.02 * (z - 2.0)


def _wedge_stone():
    return M2.face_stones(SPEC, 8, 1, _hw, course_h=0.55)[0]


def _core_stone():
    return M2.core_cells(8, lambda x, z: 3.0, z_lo=1.0, z_hi=2.2,
                         x_lo=-1.0, x_hi=1.0)[0]


# ── materialize(U2) ──────────────────────────────────────────────────

def test_materialize_wedge_front_face_y_equals_transform_y():
    st = _wedge_stone()
    verts, _ = M2.materialize(st)
    # U2 语义: transform y = 前脸位置; 前脸是局部 y 最大面 -> 世界 y 最大 == ty
    assert max(v[1] for v in verts) == st["transform"][1]
    p = st["params"]
    t = st["transform"]
    assert min(v[0] for v in verts) == pytest.approx(t[0] - p["w"] / 2.0,
                                                    abs=0.0)
    assert max(v[0] for v in verts) == pytest.approx(t[0] + p["w"] / 2.0,
                                                     abs=0.0)
    assert min(v[2] for v in verts) == pytest.approx(t[2] - p["h"] / 2.0,
                                                     abs=0.0)
    assert max(v[2] for v in verts) == pytest.approx(t[2] + p["h"] / 2.0,
                                                     abs=0.0)


def test_materialize_slab_world_bbox_matches_params_bbox():
    cell = _core_stone()
    verts, _ = M2.materialize(cell)
    bb = cell["params"]["bbox"]
    assert min(v[0] for v in verts) == bb["x0"]
    assert max(v[0] for v in verts) == bb["x1"]
    assert min(v[1] for v in verts) == bb["y0"]
    assert max(v[1] for v in verts) == bb["y1"]
    assert min(v[2] for v in verts) == bb["z0"]
    assert max(v[2] for v in verts) == bb["z1"]


def test_materialize_rotation_spins_about_block_center():
    st = _wedge_stone()
    t = list(st["transform"])
    v0, _ = M2.materialize(st)
    c0 = [sum(v[i] for v in v0) / len(v0) for i in range(3)]
    st2 = dict(st)
    st2["transform"] = [t[0], t[1], t[2], 0.3, 1.1, -0.7]
    v1, _ = M2.materialize(st2)
    c1 = [sum(v[i] for v in v1) / len(v1) for i in range(3)]
    # 8 角点盒的顶点重心 == 块中心: 旋转后不动
    for a, b in zip(c0, c1):
        assert a == pytest.approx(b, abs=1e-12)
    # 旋转确实发生(非恒等)
    assert max(max(abs(a[i] - b[i]) for i in range(3)) for a, b in zip(v0, v1)) > 0.1


def test_materialize_does_not_mutate_inputs():
    st = _wedge_stone()
    snap = copy.deepcopy(st)
    verts, faces = M2.materialize(st)
    vsnap = list(verts)
    fsnap = list(faces)
    M2.materialize(st, verts, faces)
    assert st == snap
    assert verts == vsnap and faces == fsnap


def test_anchor_offset_unknown_family_raises():
    with pytest.raises(ValueError):
        M2.anchor_offset("wedge-l", {"w": 1, "h": 1}, [0, 0, 0, 0, 0, 0])


# ── GN 实例组合恒等 materialize ───────────────────────────────────────

def test_gn_instance_composition_equals_materialize():
    """场景实例化公式 point + R @ centered_verts == materialize(逐点)。"""
    for st in (_wedge_stone(), _core_stone()):
        t = list(st["transform"])
        for rot in ((0.0, 0.0, 0.0), (0.3, 1.1, -0.7)):
            st2 = dict(st)
            st2["transform"] = [t[0], t[1], t[2], rot[0], rot[1], rot[2]]
            world, _ = M2.materialize(st2)
            pt = BS.placement_point(st2)
            centered = BS.centered_verts(st2)
            r = M2._euler_xyz_matrix(*rot)
            comp = []
            for v in centered:
                rv = (r[0][0] * v[0] + r[0][1] * v[1] + r[0][2] * v[2],
                      r[1][0] * v[0] + r[1][1] * v[1] + r[1][2] * v[2],
                      r[2][0] * v[0] + r[2][1] * v[1] + r[2][2] * v[2])
                comp.append((pt[0] + rv[0], pt[1] + rv[1], pt[2] + rv[2]))
            for a, b in zip(comp, world):
                assert a == pytest.approx(b, abs=1e-12)


# ── void 分类与裁剪 ──────────────────────────────────────────────────

def test_point_in_void_triage():
    band = BS.arch_band(8)
    spz, a = band["springer"], band["a"]
    assert BS.point_in_void(band["xc"], spz - 1.0, band)          # 矩形部
    assert BS.point_in_void(band["xc"], spz + band["b"] / 2.0, band)  # 冠下
    assert not BS.point_in_void(band["xc"], spz + band["b"] + 1.0, band)
    assert not BS.point_in_void(band["xc"] + a + 1.0, spz - 1.0, band)
    assert not BS.point_in_void(band["xc"] - a - 1.0, spz + 0.5, band)


def test_clip_footprint_triage_and_mass_balance():
    band = BS.arch_band(8)
    spz, a, xc = band["springer"], band["a"], band["xc"]
    # 全在净空外(墩体远离孔带 -> 面石不会落这, 但分类器必须稳健)
    st, polys = BS.clip_footprint(xc + a + 5.0, xc + a + 6.0, 0.0, 1.0, band, 8)
    assert st == "out" and polys == []
    # 全在矩形部净空内
    st, polys = BS.clip_footprint(xc - 1.0, xc + 1.0, 0.0, 0.5, band, 8)
    assert st == "inside" and polys == []
    # 跨左拱脚: 保留片(墙侧)并 == 足印 - 净空交(细采样交叉核对), 顶点全在洞外
    x0, x1, z0, z1 = xc - a - 0.5, xc - a + 0.9, 0.2, 1.6
    st, polys = BS.clip_footprint(x0, x1, z0, z1, band, 8)
    assert st == "clip" and len(polys) >= 1
    area = sum(BS._poly_area(p) for p in polys)
    n = 40
    hit = 0
    for ii in range(n):
        for jj in range(n):
            x = x0 + (x1 - x0) * (ii + 0.5) / n
            z = z0 + (z1 - z0) * (jj + 0.5) / n
            if BS.point_in_void(x, z, band):
                hit += 1
    void_area = hit / float(n * n) * (x1 - x0) * (z1 - z0)
    assert area == pytest.approx((x1 - x0) * (z1 - z0) - void_area, rel=0.05)
    # 保留片顶点不得落在净空内(折线近似 + z 带直切在边界上留 <=ARC_STEP 斜率
    # 型残隙, 设计界 0.04m = 0.29px 亚像素; 深入净空者必红)。[P2-T6b] 冠钝
    # soft-min 使 cutter 折线在拱肩钝化带内下潜(幅值 = facts.blunt_s 单源),
    # 跨缘竖条保留片顶点允许再让 blunt_s —— 仍深入钝化包络者必红。
    def _near_bd(x, z):
        if z > band["springer"]:
            r = abs(F.arch_signed_r(x, z, band["xc"], band["springer"],
                                    band["a"], band["b"]))
            return r < BS.ARC_STEP + F.blunt_s(band["a"], band["b"])
        return abs(abs(x - band["xc"]) - band["a"]) < BS.ARC_STEP
    for p in polys:
        for (x, z) in p:
            assert not BS.point_in_void(x, z, band) or _near_bd(x, z), (x, z)
    # 负控: 洞心深点必被抓(判据对深入净空者不失效)
    deep_x, deep_z = xc, spz + band["b"] / 2.0
    assert BS.point_in_void(deep_x, deep_z, band)
    assert not _near_bd(deep_x, deep_z)


def test_clipped_stone_mesh_watertight_positive_volume():
    """跨洞真实面石 -> 裁剪棱柱: 每边恰两次且反向(水密), 体积为正(朝外)。"""
    led = BS.bridge_ledger()
    statuses = BS.classify_stones(led["stones"])
    clipped = [s for s in led["stones"]
               if statuses[s["id"]][0] == "clip" and s["role_struct"] == "SPANDREL"]
    assert clipped, "真实砖谱必须有跨洞面石"
    edge_use = {}
    checked = 0
    for st in clipped[:8]:
        verts, faces = BS.stone_local_mesh(st, "clip", statuses[st["id"]][1])
        vol = EP.signed_volume(verts, faces)
        assert vol > 0.0, "%s 裁剪网格体积非正" % st["id"]
        checked += 1
        # 单石水密: 每条有向边恰出现一次, 且反向边各一次
        dirs = {}
        for fc in faces:
            for k in range(len(fc)):
                e = (fc[k], fc[(k + 1) % len(fc)])
                dirs[e] = dirs.get(e, 0) + 1
        for (u, v2), n in dirs.items():
            assert n == 1, "%s 有向边重复" % st["id"]
            assert dirs.get((v2, u), 0) == 1, "%s 非水密" % st["id"]
    assert checked >= 1


def test_inside_void_stones_exist_and_are_hidden_at_layout():
    led = BS.bridge_ledger()
    statuses = BS.classify_stones(led["stones"])
    inside = [s["id"] for s in led["stones"] if statuses[s["id"]][0] == "inside"]
    assert inside, "净空内必须有可剔除石(否则 GN in_void 判据恒假)"


# ── 族清点/身份 ──────────────────────────────────────────────────────

def test_family_identity_dedup_and_unique():
    a = _wedge_stone()
    b = copy.deepcopy(a)
    assert BS.family_identity(a) == BS.family_identity(b)
    b = copy.deepcopy(a)
    b["params"]["d"] = b["params"]["d"] + 0.1
    assert BS.family_identity(a) != BS.family_identity(b)
    c = copy.deepcopy(a)
    assert BS.family_identity(c, "clip") == "uniq:" + c["id"]
    assert BS.family_identity(a) != BS.family_identity(c, "clip")


def test_census_counts_and_object_names_are_ordered():
    led = BS.bridge_ledger()
    statuses = BS.classify_stones(led["stones"])
    fams = BS.census(led["stones"], statuses)
    keys = sorted(fams)
    assert len(fams) >= len(led["stones"]) * 0.5   # 谱驱动参数几乎块块不同
    names = [BS.family_obj_name(k, i) for i, k in enumerate(keys)]
    assert names == sorted(names)                  # 序号前缀 -> 名序==键序
    assert all(len(n.encode()) <= 63 for n in names)
    # 负控: 漏掉 uniq 规则的朴素去重必然少计(跨洞石逐石唯一)
    naive = {BS.family_identity(s) for s in led["stones"]}
    assert len(naive) < len(fams)


# ── 全桥账目链 ───────────────────────────────────────────────────────

def _independent_chain_count():
    """独立实现的同口径全桥链(不调 BS.bridge_ledger): 逐孔谱+镜像、
    hw/deck 由 facts 独立推导 -> 族数。用于与 BS.bridge_ledger 互证。"""
    import math as _m

    def deck_z(x):
        half = F.BRIDGE_LEN / 2.0
        ax = min(abs(x), half)
        k = (F.DECK_Z_TOP - F.DECK_Z_END) / (half * half)
        return F.DECK_Z_TOP - k * ax * ax

    def hw(x, z):
        zt = deck_z(x)
        f = max(0.0, min(1.0, (z - BODY_BOTTOM) / (zt - BODY_BOTTOM)))
        return (F.DECK_DOWN_W + (F.DECK_UP_W - F.DECK_DOWN_W) * f) / 2.0

    spans = list(F.SPAN_DISTINCT) + list(reversed(list(F.SPAN_DISTINCT)[:-1]))
    px = []
    acc = -F.BRIDGE_LEN / 2.0
    for i in range(F.N_SPAN + 1):
        w = F.BRIDGE_ABUT if i in (0, F.N_SPAN) else F.PIER_W_INT[i - 1]
        px.append(acc + w / 2.0)
        acc += w
        if i < F.N_SPAN:
            acc += spans[i]
    sdir = os.path.join(os.path.dirname(__file__), "..", "3d", "stones")
    stones = []
    half = F.N_SPAN // 2
    for i in range(F.N_SPAN):
        src = i if i <= half else (F.N_SPAN - 1 - i)
        with open(os.path.join(sdir, "stones_p%d.json" % src),
                  encoding="utf-8") as f:
            spec = json.load(f)
        if i > half:
            spec = BS.mirror_spec(spec)
        xc = (px[i] + px[i + 1]) / 2.0
        ch = max(0.05, deck_z(xc) - spec["courses"][-1]["z0"])
        for side in (1, -1):
            faces = M2.face_stones(spec, i, side, hw, course_h=ch)
            stones.extend(faces)
            # [P2-T6b] 背衬种子跨孔镜像锚(与 build_scene2 调用点同契约:
            # 东半孔用镜像孔种子, backing_stones 内倒序消费)
            stones.extend(M2.backing_stones(
                faces, hw,
                seed=(F.N_SPAN - 1 - i) if M2.bridge_mirror_phase(i) else i))
        x_lo = -F.BRIDGE_LEN / 2.0 if i == 0 else px[i]
        x_hi = F.BRIDGE_LEN / 2.0 if i == F.N_SPAN - 1 else px[i + 1]
        stones.extend(M2.core_cells(i, hw, BODY_BOTTOM, deck_z(xc),
                                    x_lo, x_hi, seed=i))
    # 场景链收口规则(单一实现 BS.cap_to_deck, 装配链保持独立)
    capped = []
    for i in range(F.N_SPAN):
        zone = "ARCH%02d" % (i + 1)
        capped.extend(BS.cap_to_deck(
            [s for s in stones if s["id"].startswith(zone + ".")]))
    return len(BS.census(capped, BS.classify_stones(capped)))


def _world_top_center_x(s):
    """家族锚语义的世界顶 z 与块心 x(H1): slab=最小角锚(顶=tz+h, 心=bbox
    中点), wedge=中心锚(顶=tz+h/2, 心=transform[0])。与 masonry2
    anchor_offset 的分派表同源, 不另立第二语义。"""
    if s["family"] in M2._ANCHOR_MIN_CORNER:
        bb = s["params"]["bbox"]
        return (float(s["transform"][2]) + float(s["params"]["h"]),
                0.5 * (float(bb["x0"]) + float(bb["x1"])))
    return (float(s["transform"][2]) + float(s["params"]["h"]) / 2.0,
            float(s["transform"][0]))


def test_bridge_ledger_structure_and_family_count_crosscheck():
    led = BS.bridge_ledger()
    errs = LED.validate_ledger(led)
    assert not errs, errs[:5]
    stones = led["stones"]
    zones = {s["id"].split(".")[0] for s in stones}
    assert zones == {"ARCH%02d" % (i + 1) for i in range(F.N_SPAN)}
    roles = {s["role_struct"] for s in stones}
    assert roles == {"SPANDREL", "BACK", "CORE"}
    # 东西同孔共 x 足印(墙面两侧); 跨孔镜像: ARCHzz 与 ARCH(18-zz) 足印互为反号
    byz = {}
    for s in stones:
        if s["role_struct"] == "SPANDREL":
            byz.setdefault(s["id"].split(".")[0], {}).setdefault(
                s["id"].split(".")[1], []).append(s)
    for z, sides in byz.items():
        assert set(sides) == {"EAST", "WEST"}
        assert len(sides["EAST"]) == len(sides["WEST"])
        xs_e = sorted(round(s["transform"][0], 9) for s in sides["EAST"])
        xs_w = sorted(round(s["transform"][0], 9) for s in sides["WEST"])
        assert xs_e == xs_w, "%s 东西足印不一致" % z
    mirror_pairs = 0
    for z, sides in byz.items():
        zt2 = "ARCH%02d" % (F.N_SPAN + 1 - int(z[4:]))
        if zt2 not in byz or int(z[4:]) > F.N_SPAN // 2:
            continue
        xs_a = sorted(round(s["transform"][0], 6) for s in sides["EAST"])
        xs_b = sorted(round(-s["transform"][0], 6) for s in byz[zt2]["EAST"])
        assert xs_a == xs_b, "%s 与 %s 镜像足印不一致" % (z, zt2)
        mirror_pairs += 1
    assert mirror_pairs >= F.N_SPAN // 2
    # 顶不越桥面弧线(cap_to_deck 收口; 端孔谱平线末层逐块截顶)——H1 修复后
    # 断言从"只扫 SPANDREL"扩到全 role: 世界顶 <= 该块【块心 x】处桥面标高
    # (容差 1e-9)。修复前同口径(旧采样 transform[0])全 role 实测 29 块越顶,
    # 全部是 CORE slab(slab 被当块中心锚截顶, 顶穿桥面弧线)。
    for s in stones:
        zt, xc = _world_top_center_x(s)
        assert zt <= BS.deck_z_at(xc) + 1e-9, \
            "%s 世界顶 %r 越过块心(%r)桥面 %r" % (s["id"], zt, xc,
                                                 BS.deck_z_at(xc))
    # 独立链互证族数(FAMILIES_EMIT 的可测替身)
    assert len(BS.census(stones, BS.classify_stones(stones))) \
        == _independent_chain_count()


def test_layout_group_partition():
    led = BS.bridge_ledger()
    groups = {}
    for s in led["stones"]:
        groups.setdefault(BS.layout_group(s), 0)
        groups[BS.layout_group(s)] += 1
    # 分区目标全集由 layout_scene 建满(含 ABUT_E/W 占位: 桥台砌体未入账前
    # 无石可落, 分区合法为空); 当前链的石必须全部落在已知分区名内。
    assert set(groups) <= set(BS.layout_groups())
    assert len(BS.layout_groups()) == F.N_SPAN + 3
    assert "CORE" in groups and "SPAN09" in groups
    # ABUT 只收 CORE 石(规则层; 当前账目桥台条带并入端孔带, 故可为空)
    px, _sp = BS.piers_and_spans()
    for s in led["stones"]:
        g = BS.layout_group(s)
        if g in ("ABUT_E", "ABUT_W"):
            assert s["role_struct"] == "CORE"


# ── export_print 默认 mesh_fn = materialize 回床 ─────────────────────

def _stl_verts(path):
    with open(path, "rb") as fh:
        blob = fh.read()
    n = struct.unpack("<I", blob[80:84])[0]
    vs = []
    for i in range(n):
        off = 84 + 50 * i + 12
        v = struct.unpack("<9f", blob[off:off + 36])
        vs.extend([v[0:3], v[3:6], v[6:9]])
    return vs


def test_export_default_mesh_fn_is_materialize_translation():
    hw = _hw
    stones = M2.face_stones(SPEC, 8, 1, hw, course_h=0.55)
    stones += M2.core_cells(8, lambda x, z: 3.0, z_lo=1.0, z_hi=2.2,
                            x_lo=-1.0, x_hi=1.0)
    led = {"meta": {"curve_hash": "h", "seed": 1, "schema": 1},
           "stones": stones}
    d1 = tempfile.mkdtemp()
    EP.export_ledger(led, out_dir=d1)
    d2 = tempfile.mkdtemp()
    EP.export_ledger(led, mesh_fn=lambda s: FAM.family_mesh(s["family"],
                                                            s["params"]),
                     out_dir=d2)
    for st in stones:
        rel = os.path.join(st["material"], st["id"].replace(".", "_") + ".stl")
        v_def = _stl_verts(os.path.join(d1, rel))
        v_loc = _stl_verts(os.path.join(d2, rel))
        assert len(v_def) == len(v_loc)
        t = [sum((a[i] - b[i]) for a, b in zip(v_def, v_loc)) / len(v_def)
             for i in range(3)]
        dev = max(max(abs((a[i] - b[i]) - t[i]) for i in range(3))
                  for a, b in zip(v_def, v_loc))
        assert dev < 1e-3, "%s 默认路径与显式族路径非平移等价(dev=%r)" % (
            st["id"], dev)
        assert min(v[2] for v in v_def) == pytest.approx(0.0, abs=0.4)
    # 负控: 平移不等价的两份 STL 必被抓(放大偏差注入)
    v_def = _stl_verts(os.path.join(
        d1, stones[0]["material"],
        stones[0]["id"].replace(".", "_") + ".stl"))
    v_bad = [(v[0], v[1], v[2] + 1.0) for v in v_def]
    t = [sum((a[i] - b[i]) for a, b in zip(v_def, v_bad)) / len(v_def)
         for i in range(3)]
    dev = max(max(abs((a[i] - b[i]) - t[i]) for i in range(3))
              for a, b in zip(v_def, v_bad))
    assert dev == 0.0
    v_bad2 = [(v[0], v[1], v[2] + 1.0 if k % 2 else v[2])
              for k, v in enumerate(v_def)]
    t2 = [sum((a[i] - b[i]) for a, b in zip(v_def, v_bad2)) / len(v_def)
          for i in range(3)]
    dev2 = max(max(abs((a[i] - b[i]) - t2[i]) for i in range(3))
               for a, b in zip(v_def, v_bad2))
    assert dev2 > 1e-3, "等价判据对真差异无感"


# ── P1-T7 修复轮(2026-10-07 审查 H1/W1/W4/S1) ────────────────────────

def test_cap_to_deck_slab_min_corner_anchor_negative_control(monkeypatch):
    """H1 slab 负控: 最小角锚石截顶只改 h/bbox.z1, transform[2] 不动;
    不变式 bbox.z0==transform[2] 与"世界 z 跨度==bbox 跨度"维持; 截后顶
    ==块心桥面标高(1e-9); 整块超底的弃且记数。wedge 中心锚同步回归
    (zm 随实高平移, 现状语义不变)。"""
    cells = M2.core_cells(8, lambda x, z: 3.0, z_lo=4.0, z_hi=5.2,
                          x_lo=-1.0, x_hi=1.0)
    assert sorted(c["transform"][2] for c in cells) == [4.0] * 3 + [4.6] * 3
    stats = {}
    monkeypatch.setattr(BS, "deck_z_at", lambda x: 4.5)  # 平桥面
    out = BS.cap_to_deck(cells, stats=stats)
    # z0=4.6 层整块超底: 弃且记数; z0=4.0 层截到 0.5 存活
    assert len(out) == 3 and stats["skipped_below_deck"] == 3
    assert sorted(stats["skipped_ids"]) == sorted(
        c["id"] for c in cells if c["id"] not in {o["id"] for o in out})
    kept = out[0]
    assert kept["transform"][2] == 4.0, "最小角锚 transform[2] 不得动"
    assert kept["params"]["h"] == pytest.approx(0.5)
    bb = kept["params"]["bbox"]
    assert bb["z0"] == kept["transform"][2], "bbox.z0==transform[2] 不变式"
    assert bb["z1"] == pytest.approx(4.5)
    verts, _ = M2.materialize(kept)
    assert max(v[2] for v in verts) == pytest.approx(4.5, abs=1e-9)
    zspan = max(v[2] for v in verts) - min(v[2] for v in verts)
    assert zspan == pytest.approx(bb["z1"] - bb["z0"], abs=1e-12)
    # wedge 回归: 中心锚石截顶后 zm=z0+h2/2(旧语义逐位保持)
    w = M2.face_stones(SPEC, 8, 1, _hw, course_h=0.55)[0]
    w["transform"][2] = 5.0 - w["params"]["h"] / 2.0    # 顶贴 z=5
    out2 = BS.cap_to_deck([w])
    assert len(out2) == 1
    # h2 = 4.5 - (5.0-0.55) = 0.05; zm = z0 + h2/2
    assert out2[0]["transform"][2] == pytest.approx(4.45 + 0.05 / 2.0)


# ── P1-T8b 修复轮(A1: cap_to_deck 截顶同步重算前脸锚) ─────────────────

def _sb_pairs(led):
    """账本里同位 (SPANDREL, BACK) 对列表(同 zone/face/course/block)。"""
    bypos = {}
    for s in led["stones"]:
        t = s["id"].split(".")
        if t[2] in ("SPANDREL", "BACK"):
            bypos.setdefault((t[0], t[1], t[3], t[4]), {})[t[2]] = s
    return [d for k, d in sorted(bypos.items())
            if "SPANDREL" in d and "BACK" in d]


def _pair_pen_mm(sf, sb):
    """审查恒等式的 pen 侧(面石内缘面相对同位背衬外缘面的穿透深度, 模型
    毫米; 负值 = 设计隐缝间隙): pen = |ty_B| - (|ty_F| - d_F)。"""
    pf = sf["params"]
    d_f = pf.get("d", pf.get("back", 0.3) + pf.get("proud", 0.0))
    return (abs(sb["transform"][1]) - (abs(sf["transform"][1]) - d_f)) * 1000.0


def test_cap_to_deck_wedge_cut_recomputes_front_anchor(monkeypatch):
    """A1: wedge-std 截顶(h2<h)时 transform[1] 必须按新层中重算:
    ty = side*(hw(xm, z0+h2/2)+proud)。旧值锚在原层中(zm_orig 高于新层中),
    hw 随 z 递减 -> 截顶石前脸/内缘整体内错, 撞进同位背衬退让线(审查恒等式
    pen+BACKING_GAP == -(|ty|-(hw+proud)), 修复前全链 116 对 pen>0 全为
    截顶石)。截顶层带变薄、hw_t 随实高重算语义不变。"""
    s = _wedge_stone()
    p = s["params"]
    h = float(p["h"])
    z0 = float(s["transform"][2]) - h / 2.0
    # 深截: 桥面压到层底上方 0.1m(桩内自洽: hw_wall 消费同一 patched 线)
    cap = z0 + 0.10
    monkeypatch.setattr(BS, "deck_z_at", lambda x: cap)
    out = BS.cap_to_deck([dict(s, params=dict(s["params"]),
                               transform=list(s["transform"]))])
    o = out[0]
    h2 = float(o["params"]["h"])
    assert h2 == pytest.approx(0.10)
    assert float(o["transform"][2]) == pytest.approx(z0 + h2 / 2.0)
    # A1 断言: 前脸锚随新层中重算
    want = BS.hw_wall(float(o["transform"][0]), z0 + h2 / 2.0) + p["proud"]
    assert abs(o["transform"][1]) == pytest.approx(want, abs=1e-12)
    # 负控: 旧锚(原层中)与 A1 新锚必须可区分 —— 判据不是恒真
    stale = BS.hw_wall(float(o["transform"][0]), z0 + h / 2.0) + p["proud"]
    assert abs(stale - want) > 1e-4, "深截下新旧锚重合, 测试无判别力"
    assert abs(o["transform"][1]) != pytest.approx(stale, abs=1e-4)
    # 未截顶石(h2==h)锚逐位不动
    monkeypatch.setattr(BS, "deck_z_at", lambda x: z0 + 10.0)
    out3 = BS.cap_to_deck([dict(s, params=dict(s["params"]),
                                transform=list(s["transform"]))])
    assert out3[0]["transform"][1] == pytest.approx(s["transform"][1],
                                                    abs=1e-12)


def test_bridge_ledger_spandrel_back_hidden_gap_identity():
    """A1 全链门(T8 审查恒等式): 每对同位 (SPANDREL, BACK)
       pen + BACKING_GAP == -(|ty_F| - (hw(xm, zm)+proud))   (1e-6mm)
    且 pen <= -BACKING_GAP + 1e-9 —— 修复前 116 对截顶石 pen>0(最大
    ~96mm), 修复后必须归 0(全部落回设计 2mm 隐缝)。"""
    led = BS.bridge_ledger()
    gap_mm = M2.BACKING_GAP * 1000.0
    n = 0
    for d in _sb_pairs(led):
        sf = d["SPANDREL"]
        pen = _pair_pen_mm(sf, d["BACK"])
        zm = float(sf["transform"][2])
        hw = BS.hw_wall(float(sf["transform"][0]), zm)
        rhs = -(abs(sf["transform"][1])
                - (hw + float(sf["params"]["proud"]))) * 1000.0
        assert abs(pen + gap_mm - rhs) < 1e-6, \
            "%s 恒等式破坏: pen=%.6f rhs=%.6f" % (sf["id"], pen, rhs)
        assert pen <= -gap_mm + 1e-9, \
            "%s 背衬互穿 pen=%.3fmm (应<= %.3f)" % (sf["id"], pen, -gap_mm)
        n += 1
    assert n > 2000, "全链面石-背衬对数异常: %d" % n


def test_bridge_ledger_records_below_deck_stones():
    """H1: 整块超底石不得静默消失 —— 计数+ids 记入 meta 且与账面一致。
    审查点名的两块超底 CORE slab 必须在记录里(修复前它们要么被静默弃、
    要么带着错误锚位混进账面, 账实不符)。"""
    led = BS.bridge_ledger()
    rec_n = led["meta"]["skipped_below_deck"]
    rec_ids = led["meta"]["skipped_below_deck_ids"]
    assert rec_n >= 1
    assert rec_n == len(rec_ids) == len(set(rec_ids)), "计数与 ids 必须对账"
    named = {"ARCH11.EAST.CORE.C15.B02", "ARCH14.EAST.CORE.C12.B02"}
    assert named <= set(rec_ids), sorted(named - set(rec_ids))
    kept = {s["id"] for s in led["stones"]}
    assert not (named & kept), "被记弃石不得同时出现在账面"


def test_layout_object_gate_is_50():
    """W1: --layout 场景 Object 硬门对齐简报 50(实测 20, 不再用放宽的 60)。"""
    assert BS.LAYOUT_MAX_OBJECTS == 50


def test_clip_stones_marked_and_materialize_demands_baked_mesh():
    """W4: 跨洞裁剪石 params.clipped=True; materialize 无烘焙网格必须
    响亮 raise —— 把"整块族网格静默顶替裁剪片"的前向陷阱变成显式错误。
    未裁剪石不打标、默认路径照常。"""
    led = BS.bridge_ledger()
    statuses = BS.classify_stones(led["stones"])
    clips = [s for s in led["stones"] if statuses[s["id"]][0] == "clip"]
    outs = [s for s in led["stones"] if statuses[s["id"]][0] == "out"]
    assert clips and outs, "真实账目必须同时有跨洞石与洞外石"
    for s in clips:
        assert s["params"].get("clipped") is True, s["id"]
    assert all("clipped" not in s["params"] for s in outs)
    st = clips[0]
    with pytest.raises(ValueError, match="clipped"):
        M2.materialize(st)
    verts, faces = BS.stone_local_mesh(st, "clip", statuses[st["id"]][1])
    wv, wf = M2.materialize(st, verts, faces)
    assert len(wv) == len(verts) and len(wf) == len(faces)
    M2.materialize(_wedge_stone())   # 未裁剪石: 默认族网格路径不受影响


def test_guarded_import_loud_when_bpy_present_but_body_modules_missing():
    """S1: bpy 可用而本体模块(G/MAT/LIONS/BEASTS)缺失 -> 显式 ImportError。
    旧守护 except 一把抓曾把 blender 环境的本体缺文件吞成 bpy=None 静默降级。"""
    import importlib
    import types
    names = ("bpy", "bmesh", "mathutils", "bridge_geom2", "materials",
             "lions2", "beasts2", "build_scene2")
    saved = {k: sys.modules.get(k) for k in names}
    try:
        for k in ("bpy", "bmesh"):
            sys.modules[k] = types.ModuleType(k)
        mu = types.ModuleType("mathutils")
        mu.Vector = mu.Matrix = object
        sys.modules["mathutils"] = mu
        # sys.modules 值置 None -> import 该名即 ImportError(真模块不执行)
        for k in ("bridge_geom2", "materials", "lions2", "beasts2"):
            sys.modules[k] = None
        with pytest.raises(ImportError):
            importlib.reload(BS)
    finally:
        for k, v in saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v
        importlib.reload(BS)


def test_clip_footprint_bridge_mirror_covariant():
    """[P2-T6b] 跨缘石分类桥轴镜像协变 —— 弦线带内上行后上穿块顶的竖条,
    保留片必须沿 z1 折返闭合(旧实现 2 点开环被 len>=3 丢弃 → 整片蒸发,
    石被误判 in_void; station 网格按孔绝对 x 对齐, 镜像孔离散错位使该支
    只在单侧触发 = 手性, 真账 ARCH07.C04.B00 四石误删, in_void 180 vs
    176)。注: 陡肩段(斜率~9) cutter 折线矢高显著, 顶点对解析拱线的
    残隙属 cutter 既有离散精度(两孔同措), 不在本测纪律内。"""
    b6, b10 = BS.arch_band(6), BS.arch_band(10)
    # 真账 ARCH07.EAST.SPANDREL.C04.B00 及其镜像(ARCH11.EAST...C04.B06)
    x0, x1, z0, z1 = -24.084, -23.658, 2.092, 2.693
    st6, polys6 = BS.clip_footprint(x0, x1, z0, z1, b6, 6)
    st10, polys10 = BS.clip_footprint(-x1, -x0, z0, z1, b10, 10)
    assert st6 == "clip" and st10 == "clip", (st6, st10)
    a6 = sum(BS._poly_area(p) for p in polys6)
    a10 = sum(BS._poly_area(p) for p in polys10)
    assert a6 == pytest.approx(a10, rel=1e-6), (a6, a10)
    # 保留片在各自石块矩形内、面积 ≤ 足印(闭合多边形而非开环)
    for polys, rx0, rx1 in ((polys6, x0, x1), (polys10, -x1, -x0)):
        for p in polys:
            xs = [v[0] for v in p]
            zs = [v[1] for v in p]
            assert rx0 - 1e-9 <= min(xs) and max(xs) <= rx1 + 1e-9
            assert z0 - 1e-9 <= min(zs) and max(zs) <= z1 + 1e-9
            assert abs(BS._poly_area(p)) <= (rx1 - rx0) * (z1 - z0) + 1e-12
    # 负控(判据不恒红): 洞心深竖条必是 inside 而非 clip
    xc6 = b6["xc"]
    st_deep, _ = BS.clip_footprint(xc6 - 1.0, xc6 + 1.0, 0.0, 0.5, b6, 6)
    assert st_deep == "inside"
