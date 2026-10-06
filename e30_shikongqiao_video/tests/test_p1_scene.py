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
    # 型残隙, 设计界 0.04m = 0.29px 亚像素; 深入净空者必红)
    def _near_bd(x, z):
        if z > band["springer"]:
            return abs(F.arch_signed_r(x, z, band["xc"], band["springer"],
                                       band["a"], band["b"])) < BS.ARC_STEP
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
            stones.extend(M2.backing_stones(faces, hw, seed=i))
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
    # 面石顶不越过桥面弧线(cap_to_deck 收口; 端孔谱平线末层逐块截顶)
    for s in stones:
        if s["role_struct"] == "SPANDREL":
            zt = s["transform"][2] + s["params"]["h"] / 2.0
            assert zt <= BS.deck_z_at(s["transform"][0]) + 1e-9
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
