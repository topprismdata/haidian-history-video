# -*- coding: utf-8 -*-
"""P1 面石/背衬/core cells 单测(合成 spec, 不依赖 blender; hw_fn 依赖注入)。"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "3d"))
import masonry2 as M2  # noqa: E402
import facts as F  # noqa: E402  # 纯数据, 无 blender 依赖
from assumptions import BODY_BOTTOM, VOID_CUT_MARGIN  # noqa: E402

SPEC = {"courses": [
    {"z0": 2.0, "blocks": [{"x0": 0.0, "x1": 1.2}, {"x0": 1.2, "x1": 2.0}]},
    {"z0": 2.55, "blocks": [{"x0": 0.0, "x1": 0.8}, {"x0": 0.8, "x1": 2.0}]}]}


def _hw(x, z):
    return 6.0 - 0.02 * (z - 2.0)


def test_face_stones_ids_and_depths():
    stones = M2.face_stones(SPEC, 8, 1, _hw, course_h=0.55)
    assert len(stones) == 4
    ids = [s["id"] for s in stones]
    assert ids[0] == "ARCH09.EAST.SPANDREL.C00.B00"
    assert ids[3] == "ARCH09.EAST.SPANDREL.C01.B01"
    # 顺丁相间: 同层奇偶块深不同(顺1.2/丁2.4 或参数表), 且都>0.5
    d0 = stones[0]["params"]["d"]
    d1 = stones[1]["params"]["d"]
    assert d0 > 0.5 and d1 > 0.5 and abs(d0 - d1) > 0.3
    # 间隙两量分离: 历史缝10mm, 制造间隙未定
    assert all(s["joint_historical_mm"] == 10.0 for s in stones)
    assert all(s["clearance_manufacturing_mm"] is None for s in stones)


def test_face_stones_mirror_id():
    west = M2.face_stones(SPEC, 8, -1, _hw, course_h=0.55)
    assert west[0]["id"] == "ARCH09.WEST.SPANDREL.C00.B00"


def test_face_stones_accepts_edge_list_blocks():
    # 真实砖谱 stones_pX.json 的 blocks 是沿 x 的界边表, 不是 {x0,x1} 字典
    spec = {"courses": [{"z0": 2.0, "blocks": [0.0, 1.2, 2.0]}]}
    stones = M2.face_stones(spec, 0, 1, _hw, course_h=0.55)
    assert [s["id"] for s in stones] == [
        "ARCH01.EAST.SPANDREL.C00.B00", "ARCH01.EAST.SPANDREL.C00.B01"]
    assert stones[0]["params"]["w"] == 1.2
    assert stones[1]["params"]["w"] == 0.8


def test_build_face_layer_aggregates_sides(tmp_path):
    (tmp_path / "stones_p8.json").write_text(json.dumps(SPEC), encoding="utf-8")
    got = M2.build_face_layer(str(tmp_path), _hw, [8])
    assert len(got) == 8
    assert [s["id"] for s in got[:2]] == [
        "ARCH09.EAST.SPANDREL.C00.B00", "ARCH09.EAST.SPANDREL.C00.B01"]
    assert all(s["id"].startswith("ARCH09.WEST.") for s in got[4:])


# ── T3 审查修复: 层高从砖谱自身推导(消层间纵向插穿) ──────────────────
# 真实砖谱层间距不等(p8 的 15 个层间隔 0.144~0.641m); 定高 0.55 会让矮层
# 砖顶插进上层砖体 —— 最差 C0 实高 0.144 却按 0.55 建, 穿 0.406m。
REAL_P8 = os.path.join(os.path.dirname(__file__), "..", "3d",
                       "stones", "stones_p8.json")


def hw_p8(x, z):
    # bridge_geom2 语义的独立线性近似(不 import blender 链): 全宽
    # DECK_DOWN_W -> DECK_UP_W 在 [BODY_BOTTOM, deck_z(0)=DECK_Z_TOP] 线性
    # 收分, 半宽 + VOID_CUT_MARGIN; p8 拱心线 x=0 处 deck_z=DECK_Z_TOP,
    # 斜率 = (6.56-14.6)/2/9.5 = -0.4232/m(审查实测同值)。
    f = (z - BODY_BOTTOM) / (F.DECK_Z_TOP - BODY_BOTTOM)
    return (F.DECK_DOWN_W + (F.DECK_UP_W - F.DECK_DOWN_W) * f) / 2.0 \
        + VOID_CUT_MARGIN

# 不等距合成砖谱: 层间隔 0.144 / 0.56, 末层无上层起算线可依
UNEQUAL_SPEC = {"courses": [
    {"z0": 0.146, "blocks": [0.0, 1.0]},
    {"z0": 0.290, "blocks": [0.0, 1.0]},
    {"z0": 0.850, "blocks": [0.0, 1.0]}]}


def _course_idx(stone):
    # ARCH09.EAST.SPANDREL.C00.B00 -> 0
    return int(stone["id"].split(".")[3][1:])


def test_face_stones_derives_heights_from_spec_gaps():
    # course_h 不传(None) -> h_i = z0_{i+1} - z0_i; 末层回退默认层带高
    stones = M2.face_stones(UNEQUAL_SPEC, 8, 1, _hw)
    hs = [s["params"]["h"] for s in stones]
    assert hs == [0.290 - 0.146, 0.850 - 0.290, M2.DEFAULT_COURSE_H]
    # z 中点与上下沿随本层实高走, 不再按定高外扩
    for course, s in zip(UNEQUAL_SPEC["courses"], stones):
        z0, h = course["z0"], s["params"]["h"]
        assert abs(s["transform"][2] - (z0 + h / 2.0)) < 1e-12
        assert s["params"]["hw_b"] == _hw(0.5, z0)
        assert s["params"]["hw_t"] == _hw(0.5, z0 + h)


def test_face_stones_explicit_course_h_is_last_layer_fallback():
    # 显式传参只兜末层; 其余层仍由砖谱推导(等距砖谱下值不变)
    stones = M2.face_stones(UNEQUAL_SPEC, 8, 1, _hw, course_h=0.55)
    assert [s["params"]["h"] for s in stones] == [
        0.290 - 0.146, 0.850 - 0.290, 0.55]


def test_real_p8_spec_has_no_vertical_penetration():
    # 真实砖谱: 任意相邻两层, 下层砖顶不得越过上层砖底
    with open(REAL_P8, "r", encoding="utf-8") as f:
        spec = json.load(f)
    z0s = [c["z0"] for c in spec["courses"]]
    stones = M2.face_stones(spec, 8, 1, _hw)
    hs = [0.0] * len(z0s)
    for s in stones:
        hs[_course_idx(s)] = s["params"]["h"]
    assert hs[:-1] == [z0s[i + 1] - z0s[i] for i in range(len(z0s) - 1)]
    for i, h in enumerate(hs):
        assert h > 0.0, "C%02d 层高非正: %r" % (i, h)
        if i + 1 < len(z0s):
            assert z0s[i] + h <= z0s[i + 1] + 1e-9, "C%02d 顶插穿 C%02d 底" % (
                i, i + 1)


def test_build_face_layer_derives_heights_by_default(tmp_path):
    (tmp_path / "stones_p8.json").write_text(json.dumps(UNEQUAL_SPEC),
                                             encoding="utf-8")
    got = M2.build_face_layer(str(tmp_path), _hw, [8])
    assert [s["params"]["h"] for s in got[:3]] == [
        0.290 - 0.146, 0.850 - 0.290, M2.DEFAULT_COURSE_H]
    # 末层兜底值可透传
    tail = M2.build_face_layer(str(tmp_path), _hw, [8], course_h=0.40)
    assert [s["params"]["h"] for s in tail[:3]] == [
        0.290 - 0.146, 0.850 - 0.290, 0.40]


# ── T4: 背衬层 + core cells(修复轮: 楔形背衬/强判据/x界必填) ─────────
# 背衬 role=BACK evidence=ashlar_truth, 楔形(proud=0), 外缘面与同带丁石
# 内缘面平行再退 2mm(隐缝记 params.gap_mm); core cells role=CORE
# evidence=core_reconstruction, 每 0.6m 一层 × x 3 列 × 前后合并, bbox 入
# params(y_extent=full_wall, 与面石账目按 evidence 分层不相加)。

def _bands(s):
    # 账目恢复 z 带: transform[2]=层中, params.h=层高
    zm, h = s["transform"][2], s["params"]["h"]
    return zm - h / 2.0, zm + h / 2.0


def _x_band(s):
    xm, w = s["transform"][0], s["params"]["w"]
    return xm - w / 2.0, xm + w / 2.0


def _outer_face_y(b, hw_fn, z):
    # 背衬外缘面(楔形, 与墙面平行): transform[1]=层中处外缘 y, 斜率随 hw_fn
    xm, zm = b["transform"][0], b["transform"][2]
    return abs(b["transform"][1]) + hw_fn(xm, z) - hw_fn(xm, zm)


MIN_CLEARANCE = 0.5 * M2.BACKING_GAP   # 判据边界: 名义缝 2mm 允缩到 1mm


def _hdr_violations(faces, backs, hw_fn):
    # C1 强判据: 对每块背衬, 取 z 带∧x 带**真相交**(正长度重叠, 端点贴合
    # 不算)的丁石, 沿相交带两端比斜面(hw 线性 -> 两端即全域):
    #   y_out(z) <= min_{z∈band}[hw(xm,z)+PROUD-d_h] - BACKING_GAP
    # 旧判据(y_in<=y_h_in-2mm 标量)被背衬自身深度吞掉, 对 0.8m 穿透免疫。
    hdr = [s for s in faces if s["params"]["d"] == M2.HEADER_D]
    bad = []
    for b in backs:
        zb0, zb1 = _bands(b)
        xb0, xb1 = _x_band(b)
        for h in hdr:
            zh0, zh1 = _bands(h)
            xh0, xh1 = _x_band(h)
            zc0, zc1 = max(zb0, zh0), min(zb1, zh1)
            xc0, xc1 = max(xb0, xh0), min(xb1, xh1)
            if zc1 - zc0 <= 1e-9 or xc1 - xc0 <= 1e-9:
                continue
            for z in (zc0, zc1):
                lim = hw_fn(h["transform"][0], z) + M2.PROUD - h["params"]["d"]
                clr = lim - _outer_face_y(b, hw_fn, z)
                if clr < MIN_CLEARANCE - 1e-9:
                    bad.append((b["id"], h["id"], round(z, 6),
                                round(clr, 6)))
    return bad


def test_backing_c1_strong_criterion_synthetic():
    faces = M2.face_stones(SPEC, 8, 1, _hw, course_h=0.55)
    backs = M2.backing_stones(faces, _hw, seed=7)
    assert len(backs) == len(faces)
    assert _hdr_violations(faces, backs, _hw) == []


def test_backing_c1_judgement_boundary_calibration():
    # 负控制打在容差边界(W4): 名义缝 2mm 下, +1mm 退让不足(缝 1mm)必不抓,
    # +3mm(真穿 1mm)必抓 —— 替换旧 0.8m 位移假负控(恰落在旧判据盲区外)。
    faces = M2.face_stones(SPEC, 8, 1, _hw, course_h=0.55)
    backs = M2.backing_stones(faces, _hw, seed=7)

    def shifted(dy):
        return [dict(s, params=dict(s["params"]),
                     transform=list(s["transform"])) for s in backs]

    b1 = shifted(0)
    for s in b1:
        s["transform"][1] += 0.001
    assert _hdr_violations(faces, b1, _hw) == []
    b3 = shifted(0)
    for s in b3:
        s["transform"][1] += 0.003
    assert _hdr_violations(faces, b3, _hw) != []


def test_core_cells_evidence_and_height():
    cells = M2.core_cells(8, _hw, z_lo=1.0, z_hi=6.0, x_lo=-4.0, x_hi=4.0,
                          seed=7)
    assert all(c["evidence"] == "core_reconstruction" for c in cells)
    assert all(c["params"]["h"] <= 0.6 for c in cells)
    assert len(cells) >= 8


def test_backing_evidence_depth_and_clearance():
    faces = M2.face_stones(SPEC, 8, 1, _hw, course_h=0.55)
    backs = M2.backing_stones(faces, _hw, seed=7)
    assert len(backs) == len(faces)
    assert all(s["role_struct"] == "BACK" for s in backs)
    assert all(s["evidence"] == "ashlar_truth" for s in backs)
    assert all(0.8 <= s["params"]["d"] <= 1.2 for s in backs)
    # 2mm 隐缝记 params.gap_mm(几何事实, 绑定常量); clearance_manufacturing_mm
    # 保持 None 挂 T6 时序(ledger I1: 置早被 validate_ledger 抓 CLEARANCE_PREMATURE)
    assert all(s["params"]["gap_mm"] == M2.BACKING_GAP * 1000.0 for s in backs)
    assert all(s["clearance_manufacturing_mm"] is None for s in backs)
    assert all(s["id"].split(".")[2] == "BACK" for s in backs)


def test_backing_depth_is_pseudorandom_deterministic():
    f = M2.face_stones(SPEC, 8, 1, _hw, course_h=0.55)
    a = M2.backing_stones(f, _hw, seed=7)
    b = M2.backing_stones(f, _hw, seed=7)
    c = M2.backing_stones(f, _hw, seed=8)
    fw = M2.face_stones(SPEC, 8, -1, _hw, course_h=0.55)
    same = lambda x, y: [(s["id"], s["transform"], s["params"]) for s in x] == \
        [(s["id"], s["transform"], s["params"]) for s in y]
    assert same(a, b)                      # 同种子逐位一致
    assert not same(a, c)                  # 异种子深度序列确实变了
    assert [s["transform"][1] for s in a] == \
           [-s["transform"][1] for s in M2.backing_stones(fw, _hw, seed=7)]


def test_backing_is_wall_parallel_wedge():
    # C2 方案B: 背衬是楔形非平盒 —— proud=0, hw_b/hw_t 取墙面在 z0/z0+h 的
    # 收分参考; 退让偏移记 params.front_c(外缘面 = hw_fn(xm,z)+front_c)。
    faces = M2.face_stones(UNEQUAL_SPEC, 8, 1, _hw)
    backs = M2.backing_stones(faces, _hw, seed=7)
    for s, b in zip(faces, backs):
        xm, zm = s["transform"][0], s["transform"][2]
        h = s["params"]["h"]
        z0 = zm - h / 2.0
        assert b["params"]["proud"] == 0.0
        assert b["params"]["hw_b"] == _hw(xm, z0)
        assert b["params"]["hw_t"] == _hw(xm, z0 + h)
        assert b["params"]["hw_b"] > b["params"]["hw_t"]   # 收分楔形, 非平盒
        assert abs(abs(b["transform"][1])
                   - (_hw(xm, zm) + b["params"]["front_c"])) < 1e-12


def test_backing_real_p8_no_penetration_and_tight_gap():
    # C2 冒烟: 真实砖谱 + 真实收分(独立线性 hw) -> 0 穿透 ∧ 缝∈[2mm,20mm]。
    # 旧平盒背衬(带中点比标量)实测: 11 块穿透 +24.1mm, 其余空腔 181~403mm。
    with open(REAL_P8, "r", encoding="utf-8") as f:
        spec = json.load(f)
    faces = M2.face_stones(spec, 8, 1, hw_p8)
    backs = M2.backing_stones(faces, hw_p8, seed=7)
    assert len(backs) == len(faces)
    clrs = []
    for b in backs:
        zb0, zb1 = _bands(b)
        xb0, xb1 = _x_band(b)
        for s in faces:
            sz0, sz1 = _bands(s)
            sx0, sx1 = _x_band(s)
            zc0, zc1 = max(zb0, sz0), min(zb1, sz1)
            xc0, xc1 = max(xb0, sx0), min(xb1, sx1)
            if zc1 - zc0 <= 1e-9 or xc1 - xc0 <= 1e-9:
                continue
            for z in (zc0, zc1):
                lim = hw_p8(s["transform"][0], z) + M2.PROUD \
                    - s["params"]["d"]
                clrs.append(lim - _outer_face_y(b, hw_p8, z))
    assert clrs
    assert min(clrs) >= M2.BACKING_GAP - 1e-9, "穿透/缝不足: %r" % min(clrs)
    assert max(clrs) <= 0.020, "空腔回归(旧 0.18~0.40m): %r" % max(clrs)


def test_core_cells_x_bounds_are_required():
    # C3: x 界必填 —— 真实 blocks 用全局 x(arch0 x∈[-72,-69.15]), 旧缺省
    # ±hw_fn(0,·) 恒绕桥中, 15/17 孔越界 0.5~63.5m; 删缺省推导路径。
    try:
        M2.core_cells(8, _hw, z_lo=1.0, z_hi=6.0, seed=7)
    except TypeError:
        pass
    else:
        assert False, "缺 x_lo/x_hi 必须 TypeError"


def test_core_cells_rejects_empty_z_band():
    try:
        M2.core_cells(8, _hw, 6.0, 1.0, -4.0, 4.0, seed=7)
    except ValueError:
        pass
    else:
        assert False, "z_hi<=z_lo 必须 ValueError(不再静默返回空)"


def test_backing_reuses_course_heights_contract():
    # T3 审查硬契约: 背衬层高必须与面石同口径(_course_heights 推导)
    f = M2.face_stones(UNEQUAL_SPEC, 8, 1, _hw)
    b = M2.backing_stones(f, _hw, seed=7)
    assert [s["params"]["h"] for s in b] == [s["params"]["h"] for s in f]
    assert [s["transform"][2] for s in b] == [s["transform"][2] for s in f]


def test_core_cells_bbox_and_coverage():
    cells = M2.core_cells(8, _hw, z_lo=1.0, z_hi=6.0, x_lo=-4.0, x_hi=4.0,
                          seed=7)
    assert all(c["role_struct"] == "CORE" for c in cells)
    assert all(c["id"].split(".")[2] == "CORE" for c in cells)
    # 水密性不再自证标记(print.watertight 留 T5 printcheck 产出, 审查 suggestion 1)
    for c in cells:
        bb = c["params"]["bbox"]
        assert c["params"]["y_extent"] == "full_wall(overlaps ashlar)"
        assert bb["z1"] == bb["z0"] + c["params"]["h"]   # 构造恒等式
        assert bb["x1"] - bb["x0"] == c["params"]["w"]
        assert abs((bb["y1"] - bb["y0"]) - c["params"]["d"]) < 1e-12
        # 前后合并: 宽度 = 2 * hw(列心, 层中)
        yh = _hw((bb["x0"] + bb["x1"]) / 2.0, (bb["z0"] + bb["z1"]) / 2.0)
        assert abs(bb["y1"] - yh) < 1e-9 and abs(bb["y0"] + yh) < 1e-9
    # z 覆盖无缝无叠: 按 (层,列) 排序后层界首尾相接
    zs = sorted(set((c["params"]["bbox"]["z0"], c["params"]["bbox"]["z1"])
                    for c in cells))
    assert zs[0][0] == 1.0 and zs[-1][1] == 6.0
    for (a0, a1), (b0, b1) in zip(zs, zs[1:]):
        assert abs(a1 - b0) < 1e-9


# ---------------------------------------------------------------------------
# [P2-T6b 裁决] 砌筑相位桥轴镜像协变: 东半孔 bi 倒序(顺丁奇偶 + 背衬伪随机序)
# ---------------------------------------------------------------------------

def test_bridge_mirror_phase_helper():
    """相位协变域: 东半孔(arch_idx > 桥心)协变, 西半孔/桥心孔维持原相位。
    17 孔 0-based 桥心=8(ARCH09 自镜像); 镜像对 i ↔ N_SPAN-1-i。"""
    assert not M2.bridge_mirror_phase(0)
    assert not M2.bridge_mirror_phase(6)    # ARCH07 西半孔
    assert not M2.bridge_mirror_phase(8)    # 桥心 ARCH09 自镜像
    assert M2.bridge_mirror_phase(9)        # ARCH10 起东半孔
    assert M2.bridge_mirror_phase(10)       # ARCH11(ARCH07 镜像对)
    assert M2.bridge_mirror_phase(16)


def test_face_phase_bridge_mirror_covariant():
    """东半孔顺丁深度在镜像位(bi ↔ n-1-bi)与西镜像孔一致; 同 bi 反相。
    旧实现两孔同 (ci+bi) 奇偶 = 跨孔反手性(ARCH07 停车线伪影根因,
    实测 145/214 镜像位深度反相) —— 本测在旧实现下必红。"""
    west = M2.face_stones(SPEC, 6, 1, _hw, course_h=0.55)    # ARCH07 西半孔
    east = M2.face_stones(SPEC, 10, 1, _hw, course_h=0.55)   # ARCH11 东半孔
    dw = {}
    for s in west:
        t = s["id"].split(".")
        dw[(int(t[3][1:]), int(t[4][1:]))] = s["params"]["d"]
    n_checked = 0
    for s in east:
        t = s["id"].split(".")
        ci, bi = int(t[3][1:]), int(t[4][1:])
        n = max(b for c, b in dw if c == ci) + 1
        mi = n - 1 - bi
        if (ci, mi) in dw:
            n_checked += 1
            assert s["params"]["d"] == dw[(ci, mi)], \
                ("镜像位深度反相", t, dw[(ci, mi)])
    assert n_checked == len(dw), (n_checked, len(dw))
    # 桥心孔(ARCH09)相位不变: (ci+bi) 奇偶原样
    c00 = M2.face_stones(SPEC, 8, 1, _hw, course_h=0.55)[0]
    assert c00["params"]["d"] == M2.STRETCHER_D   # (0+0)%2==0 → 顺


def test_backing_phase_bridge_mirror_covariant():
    """东半孔背衬伪随机序镜像消费: 镜像孔同种子下, 镜像位深度一致。
    旧实现按孔西缘序消费同种子 → 镜像位取不同抽签(手性), 本测必红。"""
    fw = M2.face_stones(SPEC, 6, 1, _hw, course_h=0.55)
    fe = M2.face_stones(SPEC, 10, 1, _hw, course_h=0.55)
    bw = M2.backing_stones(fw, _hw, seed=6)
    be = M2.backing_stones(fe, _hw, seed=6)   # 种子跨孔镜像锚(同镜像孔种子)
    dw = {}
    for s in bw:
        t = s["id"].split(".")
        dw[(int(t[3][1:]), int(t[4][1:]))] = s["params"]["d"]
    n_checked = 0
    for s in be:
        t = s["id"].split(".")
        ci, bi = int(t[3][1:]), int(t[4][1:])
        n = max(b for c, b in dw if c == ci) + 1
        mi = n - 1 - bi
        if (ci, mi) in dw:
            n_checked += 1
            assert s["params"]["d"] == dw[(ci, mi)], \
                ("镜像位背衬深度反相", t)
    assert n_checked == len(dw), (n_checked, len(dw))
