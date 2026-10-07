# -*- coding: utf-8 -*-
"""P2-T2 修复轮 centering.py 券架生成器测试(blender-free)。

主控裁决落地(2026-10-07):
  D1 工作面基准 = **intrados**: rib 板顶沿拱腹曲线 z=arch_z(x)−0.005(施工隙),
     楞木/柱顶随之下移; 拱脚区/跨中区支撑分叉删除(全线贴 intrados);
     楔副行程 0.06m 语义 = 合龙后压缩沉落(非脱环)。
  D4 id 1 基: "CEN-ARCH%02d"%(arch_idx+1); 返回体加 zone/arch_idx/xc。
  D5 桥面夹持 min() → raise(DECK_CLASH, 附 x 位置与余量); rib 顶纳入夹持。
  D6 footprint = [{poly, y0, y1, kind}] 按榀返回 + 全局 xc 平移字段;
     占位体积取 parts[].bbox 全局系, footprint 仅 rib 带轮廓。
  D7 "端孔柱高"语义 = 柱顶标高(非柱长)。
  变异盲区补测(审查 M06/M07/M08/M11/M12 存活项):
     rib 两榀计数 / 楞木跨两柱头 / 夹持 raise / RIB_T 带界(含 rib 厚的双侧界) /
     footprint≡rib 采样逐点等; 恒真 stations 测试换独立期望值;
     排数断言收敛到一处(防过度耦合)。
"""
import json
import os
import sys
from collections import Counter

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "3d"))

import facts as F
import geom_math as GM
import centering as C

TOL = 1e-9
TOL_Z = 1e-6

# 中央孔: idx 8(1 基第 9 孔), span 8.5(=SPAN_DISTINCT[-1]), springer 1.14(=facts.SPRINGER)
CENTRAL_IDX = 8
CENTRAL_SPAN = F.SPAN_DISTINCT[-1]          # 8.50
CENTRAL_SPRINGER = 1.14                     # 独立锚: facts.SPRINGER 声明值(M19 恒等已验)
# 券石环厚测试参数 = 石账 params.ring_t 真值 0.54(七审P0-2)。D2 停车线裁决:
# facts.RING_T=0.40 已裁 STALE 且 centering 不消费它 —— 此处显式传参, 与 STALE 值分叉。
RING_T = 0.54
A_CENTRAL = CENTRAL_SPAN / 2.0

# 端孔: idx 0(1 基第 1 孔), span 4.5, brief 锚 springer 0.79 → 端冠 2.23
END_IDX = 0
END_SPAN = F.SPAN_DISTINCT[0]               # 4.50
END_SPRINGER = 0.79


def _face(arch_idx, span, springer, x, lift=0.0):
    """D1 工作面真值(测试侧独立公式): rib 板顶 = 拱腹 − 施工隙 − 沉落。"""
    a = span / 2.0
    b = F.rise_ratio(arch_idx) * span
    return F.arch_z(x, 0.0, springer, a, b) - C.RIB_GAP - lift


def _central(lift=0.0):
    return C.build_centering(CENTRAL_IDX, CENTRAL_SPAN, RING_T, lift,
                             CENTRAL_SPRINGER, lambda x: F.DECK_Z_TOP)


def _end(lift=0.0):
    # 端孔跨上桥面 ≈ 端冠 + 端拱肩(冬照口径 crown2.23+spandrel_e0.5=2.73)
    crown = F.arch_z(0.0, 0.0, END_SPRINGER, END_SPAN / 2.0,
                     F.rise_ratio(END_IDX) * END_SPAN)
    deck = crown + F.SPANDREL_E
    res = C.build_centering(END_IDX, END_SPAN, RING_T, lift, END_SPRINGER,
                            lambda x: deck)
    return res, crown


def _parts(res, kind):
    return [p for p in res["parts"] if p["kind"] == kind]


def _x_center(p):
    return (p["bbox"][0] + p["bbox"][1]) / 2.0


def _check_closed_hexahedron(part):
    """闭合六面体: 8 顶点 / 6 quad 面 / 12 边各恰属 2 面 / 每面共面 / bbox 与顶点一致。"""
    vs = part["verts"]
    fs = part["faces"]
    assert len(vs) == 8, "顶点数 != 8"
    assert len(fs) == 6, "面数 != 6"
    edges = []
    for f in fs:
        assert len(f) == 4, "非 quad 面"
        assert all(0 <= i < 8 for i in f)
        # 共面: 三向量混合积 = 0
        p0 = vs[f[0]]
        u = [vs[f[1]][k] - p0[k] for k in range(3)]
        v = [vs[f[2]][k] - p0[k] for k in range(3)]
        w = [vs[f[3]][k] - p0[k] for k in range(3)]
        n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
        assert abs(n[0] * w[0] + n[1] * w[1] + n[2] * w[2]) < 1e-9, "面不共面"
        for k in range(4):
            a, b = f[k], f[(k + 1) % 4]
            assert a != b
            edges.append((min(a, b), max(a, b)))
    assert len(set(edges)) == 12, "边数 != 12(或面间重复边)"
    cnt = Counter(edges)
    assert all(c == 2 for c in cnt.values()), "存在边不属于恰 2 面(非闭合)"
    bb = part["bbox"]
    for k in range(3):
        assert abs(min(v[k] for v in vs) - bb[2 * k]) < 1e-12
        assert abs(max(v[k] for v in vs) - bb[2 * k + 1]) < 1e-12


def _poly_area(pts):
    s = 0.0
    for i in range(len(pts)):
        x1, z1 = pts[i]
        x2, z2 = pts[(i + 1) % len(pts)]
        s += x1 * z2 - x2 * z1
    return abs(s) / 2.0


# ---------------------------------------------------------------- D4 返回体

def test_result_shape_and_id_one_based():
    """D4: id 1 基 "CEN-ARCH%02d"%(idx+1); 返回体含 zone/arch_idx/xc(geom_math 孔心表)。"""
    res = _central()
    assert res["id"] == "CEN-ARCH09"        # idx 8 → 第 9 孔(与石账 zone/事件账 CEN-ARCH09 同形)
    assert res["zone"] == "ARCH09"
    assert res["arch_idx"] == 8
    assert res["xc"] == GM.arch_center_x(8)
    assert set(res.keys()) >= {"id", "zone", "arch_idx", "xc", "parts",
                               "wedge_events", "footprint"}
    assert len(res["parts"]) > 0
    assert {p["kind"] for p in res["parts"]} <= {"post", "waling", "rib", "wedge"}
    for kind in ("post", "waling", "rib", "wedge"):
        assert _parts(res, kind), "缺少 kind=%s 构件" % kind
    # 端孔同样 1 基
    res0 = _end()[0]
    assert res0["id"] == "CEN-ARCH01" and res0["zone"] == "ARCH01"


def test_cen_set_equals_ledger_zone_set():
    """D4 跨源断言: 17 孔 CEN 集合 == 石账 zone 集合(1 基对齐, 0 基漂移即红)。"""
    ledger = os.path.join(os.path.dirname(__file__), "..", "3d", "out",
                          "ledger_full.json")
    if not os.path.exists(ledger):
        raise RuntimeError(
            "out/ledger_full.json 不在盘上 —— CEN↔石账 zone 跨源钉 fail-on-skip:"
            " 先跑 blender -b --python 3d/p1a_slice.py -- --g2; 或显式 --deselect")
    zones = {s["id"].split(".")[0] for s in json.load(open(ledger))["stones"]}
    cen = {C.build_centering_for_arch(i)["id"].split("-", 1)[1]
           for i in range(F.N_SPAN)}
    assert len(cen) == F.N_SPAN
    assert cen == zones, "CEN 集合 != 石账 zone 集合: %r" % (cen ^ zones)


# ---------------------------------------------------------------- 闭合/堆叠

def test_all_parts_are_closed_hexahedra():
    for res in (_central(), _end()[0]):
        for p in res["parts"]:
            _check_closed_hexahedron(p)


def test_wedge_events_equal_post_heads():
    """卸架楔 = 每柱头一对(上下楔各一); wedge_events = 柱头对数 > 0。"""
    res = _central()
    posts = _parts(res, "post")
    wedges = _parts(res, "wedge")
    assert res["wedge_events"] == len(posts) > 0
    assert len(wedges) == 2 * res["wedge_events"]
    # 上下楔各名义高 0.12、斜面 1:8: 两端立边高均值=0.12, 高差=楔长/8
    for p in wedges:
        xlo, xhi = p["bbox"][0], p["bbox"][1]
        h = {}
        for v in p["verts"]:
            side = "lo" if abs(v[0] - xlo) < 1e-12 else "hi"
            h.setdefault(side, []).append(v[2])
        hlo = max(h["lo"]) - min(h["lo"])
        hhi = max(h["hi"]) - min(h["hi"])
        assert abs((hlo + hhi) / 2.0 - C.WEDGE_H) < TOL_Z, "楔名义高非 0.12"
        assert abs(abs(hlo - hhi) - (xhi - xlo) / C.WEDGE_SLOPE) < TOL_Z, "斜面非 1:8"
        assert abs(hlo - hhi) > 1e-6, "楔面无坡度"


def test_waling_sits_on_wedge_pairs():
    """柱顶 → 楔对(0.24) → 楞木(0.12) → rib 带: 堆叠逐层相接(D1 全线贴 intrados)。"""
    res = _central()
    for w in _parts(res, "waling"):
        x = _x_center(w)
        assert abs(w["bbox"][4] - (w["bbox"][5] - C.WALING_H)) < TOL_Z
        below = [p for p in res["parts"] if p["kind"] == "wedge"
                 and abs(_x_center(p) - x) < C.POST_SPACING / 2.0]
        assert below
        for p in below:
            assert p["bbox"][5] <= w["bbox"][4] + TOL_Z
        posts = [p for p in _parts(res, "post")
                 if abs(_x_center(p) - x) < 1e-9]
        assert len(posts) == 2
        for pt in posts:
            assert abs(pt["bbox"][5] + 2 * C.WEDGE_H - w["bbox"][4]) < TOL_Z


def test_two_bents_y_layout():
    """排架沿 y 两榀, 位于 ±(ring_t/2+0.1) 外(brief 补充设计)。"""
    res = _central()
    ys = sorted({(p["bbox"][2] + p["bbox"][3]) / 2.0 for p in _parts(res, "post")})
    y_out = RING_T / 2.0 + C.BENT_Y_CLEAR
    assert len(ys) == 2
    assert abs(ys[0] + y_out) < TOL_Z and abs(ys[1] - y_out) < TOL_Z


# ---------------------------------------------------------------- 排数(收敛一处)

def test_post_station_counts_pinned_to_literals():
    """排数断言唯一属地点(变异盲区整改: 恒真同式复算换独立期望值)。
    中央 8.5m/1.2m 间距 → 8 排(每排两柱, 首末贴拱脚); 端孔 4.5m → 4 排。"""
    central = _central()
    end = _end()[0]
    assert len(_parts(central, "waling")) == 8
    assert len(_parts(central, "post")) == 16
    assert len(_parts(end, "waling")) == 4
    assert len(_parts(end, "post")) == 8
    # 首末排贴拱脚(仅此处做几何位验证, 不再复算排数公式)
    xs = sorted({_x_center(p) for p in _parts(central, "waling")})
    assert abs(xs[0] + A_CENTRAL) < TOL_Z
    assert abs(xs[-1] - A_CENTRAL) < TOL_Z


def test_end_arch_fewer_rows_than_central():
    """端孔排数 < 中央孔(随跨自然减少); 柱底一律 BODY_BOTTOM 基准。"""
    end = _end()[0]
    assert len(_parts(end, "waling")) < len(_parts(_central(), "waling"))
    assert min(p["bbox"][4] for p in _parts(end, "post")) == C.bottom_z()


# ---------------------------------------------------------------- D1 工作面

def test_rib_verts_in_intrados_band_double_sided():
    """M11/D1: rib 板逐顶点双侧带界(含 rib 厚): 工作面 = 拱腹−0.005−lift,
    带界 = [拱腹−0.005−lift−RIB_T, 拱腹−0.005−lift](上缘不许吃进拱腹, 下缘
    不许厚过 RIB_T)。旧 extrados+0.03..0.06 带随 D1 分叉删除而废除。"""
    res = _central()
    ribs = _parts(res, "rib")
    assert ribs
    for p in ribs:
        for v in p["verts"]:
            top = _face(CENTRAL_IDX, CENTRAL_SPAN, CENTRAL_SPRINGER, v[0])
            assert top - C.RIB_T - TOL_Z <= v[2] <= top + TOL_Z, \
                "rib 顶点越出拱腹工作面双侧带: %r" % (v,)


def test_support_line_uniformly_below_intrados():
    """D1: 全线贴 intrados —— 每排楞木顶 = 拱腹−0.005−lift−RIB_T, 无拱脚区/
    跨中区分叉(旧 SPRINGER_ZONE/WORK_CLEAR 双目标已删)。"""
    res = _central()
    for w in _parts(res, "waling"):
        x = _x_center(w)
        expect = _face(CENTRAL_IDX, CENTRAL_SPAN, CENTRAL_SPRINGER, x) - C.RIB_T
        assert abs(w["bbox"][5] - expect) < TOL_Z, "楞木顶高度失配 x=%r" % x
    # 楞木下无明 SPRINGER_ZONE/WORK_CLEAR 常量(分叉删除的源码级证据)
    assert not hasattr(C, "SPRINGER_ZONE")
    assert not hasattr(C, "WORK_CLEAR")


def test_lift_settles_centering_down_with_travel_cap():
    """D1: lift 语义 = 合龙后压缩沉落(非脱环): lift>0 → 券胎面整体下沉 lift;
    行程上限 = 楔副总行程 WEDGE_LEN/WEDGE_SLOPE=0.06, 越界/负值 raise。"""
    lift = 0.02
    res = C.build_centering(CENTRAL_IDX, CENTRAL_SPAN, RING_T, lift,
                            CENTRAL_SPRINGER, lambda x: F.DECK_Z_TOP)
    for p in _parts(res, "rib"):
        for v in p["verts"]:
            top = _face(CENTRAL_IDX, CENTRAL_SPAN, CENTRAL_SPRINGER, v[0], lift)
            assert top - C.RIB_T - TOL_Z <= v[2] <= top + TOL_Z
    # 沉落方向: lift=0.02 的 rib 顶严格低于 lift=0
    z0 = max(p["bbox"][5] for p in _parts(_central(), "rib"))
    z1 = max(p["bbox"][5] for p in _parts(res, "rib"))
    assert z1 < z0 - lift + TOL_Z
    # 行程闸: 超楔副行程(0.06)与负值均 raise(行程是楔副物理属性, 非可调参数)
    with pytest.raises(ValueError):
        C.build_centering(CENTRAL_IDX, CENTRAL_SPAN, RING_T, C.WEDGE_TRAVEL + 0.01,
                          CENTRAL_SPRINGER, lambda x: F.DECK_Z_TOP)
    with pytest.raises(ValueError):
        C.build_centering(CENTRAL_IDX, CENTRAL_SPAN, RING_T, -0.001,
                          CENTRAL_SPRINGER, lambda x: F.DECK_Z_TOP)


def test_wedge_travel_is_six_centimeters():
    """楔副总行程 = 楔长/坡度 = 0.48/8 = 0.06m(合龙后压缩沉落语义的数值锚)。"""
    assert abs(C.WEDGE_TRAVEL - 0.06) < 1e-12
    assert abs(C.WEDGE_LEN / C.WEDGE_SLOPE - 0.06) < 1e-12


def test_family_constants_literal_pinned():
    """M11 真钉(P2-T2 补丁轮): 旧带界/堆叠测试的期望带全部用 C.RIB_T/C.RIB_GAP/
    C.WEDGE_H 复算 —— 翻常量本身带跟着翻, 三变异全存活(假完成盲区)。族常量
    字面值直钉, 不经任何派生: RIB_T=0.03 / RIB_GAP=0.005 / WEDGE_H=0.12。"""
    assert C.RIB_T == 0.03
    assert C.RIB_GAP == 0.005
    assert C.WEDGE_H == 0.12


# ---------------------------------------------------------------- D5 夹持

def test_deck_clash_raises_with_position_and_margin():
    """D5: 桥面夹持从 min() 改 raise —— 压低 deck_z_fn 必红(DECK_CLASH,
    消息含 x 位置与负余量); rib 顶在夹持范围内(贴拱腹工作面即被检)。"""
    a = A_CENTRAL
    intrados_crown = F.arch_z(0.0, 0.0, CENTRAL_SPRINGER, a,
                              F.rise_ratio(CENTRAL_IDX) * CENTRAL_SPAN)
    # 桥面压到工作面冠点之下 1cm → 冠部夹持必触发
    deck = intrados_crown - C.RIB_GAP - 0.01
    with pytest.raises(ValueError) as ei:
        C.build_centering(CENTRAL_IDX, CENTRAL_SPAN, RING_T, 0.0,
                          CENTRAL_SPRINGER, lambda x: deck)
    msg = str(ei.value)
    assert "DECK_CLASH" in msg
    assert "x=" in msg, "DECK_CLASH 必须附 x 位置"
    assert "余量" in msg, "DECK_CLASH 必须附余量"
    # 冠点余量应为 -0.01(压低量), 不许吞成静默夹持
    assert "-0.01" in msg


def test_clamp_reads_pointwise_deck_not_constant():
    """D5/wrapper 桥面主张补牙(补丁轮建议级): 夹持判真桥面(geom_math.deck_z
    抛物线逐点), 不是常数近似 —— 端孔 crown 工作面 2.2206: 传常数桥面 λx→2.20
    (DECK_Z_END 口径)必在 crown 区误判 DECK_CLASH; 传孔心全局平移的真 deck_z
    λx→GM.deck_z(xc+x)(crown 处 2.7256)正常建成。常数近似会双向出错(此处误伤,
    取跨中高值则漏判), 本钉锁"逐点消费"语义。"""
    xc = GM.arch_center_x(END_IDX)
    spr = C.arch_springer_z(END_IDX)
    real = C.build_centering(END_IDX, END_SPAN, RING_T, 0.0, spr,
                             lambda x: GM.deck_z(xc + x))
    assert real["id"] == "CEN-ARCH01"
    with pytest.raises(ValueError) as ei:
        C.build_centering(END_IDX, END_SPAN, RING_T, 0.0, spr,
                          lambda x: GM.DECK_Z_END)
    msg = str(ei.value)
    assert "DECK_CLASH" in msg
    xhit = float(msg.split("x=")[1].split(" ")[0])
    assert abs(xhit) < 0.5, "夹持应在端孔 crown 区触发, 实报 x=%r" % xhit


def test_normal_deck_never_clashes_all_arches():
    """真实工况(端孔 2.66 vs 桥面 2.73 等)夹持零误伤: 17 孔全部可建。"""
    ledger = os.path.join(os.path.dirname(__file__), "..", "3d", "out",
                          "ledger_full.json")
    if not os.path.exists(ledger):
        raise RuntimeError(
            "out/ledger_full.json 不在盘上 —— wrapper ring_t 现算钉 fail-on-skip:"
            " 先跑 blender -b --python 3d/p1a_slice.py -- --g2; 或显式 --deselect")
    for i in range(F.N_SPAN):
        C.build_centering_for_arch(i)


def test_centering_does_not_consume_facts_ring_t():
    """D2 停车线裁决的可执行证: centering 与 facts.RING_T 分叉解耦 ——
    ①源码不出现 facts.RING_T 消费; ②wrapper 缺省环厚 = 石账 params.ring_t
    (0.54), 不是 facts.RING_T(0.40 STALE); ③facts.RING_T 仍是 0.40(回退到位)。"""
    import ast
    import inspect
    tree = ast.parse(inspect.getsource(C))
    consumed = [n for n in ast.walk(tree)
                if isinstance(n, ast.Attribute) and n.attr == "RING_T"
                and isinstance(n.value, ast.Name) and n.value.id in ("_F", "facts")]
    imported = [n for n in ast.walk(tree)
                if isinstance(n, ast.ImportFrom) and n.module == "facts"
                and any(al.name == "RING_T" or al.name == "*" for al in n.names)]
    assert not consumed and not imported, \
        ("centering 代码仍消费 facts.RING_T(STALE) —— 解耦被回退"
         "(Attribute 形态或 import-from/wildcard 形态均算消费; docstring 提及不算)")
    assert F.RING_T == 0.40, "facts.RING_T 应回退 0.40(主控停车线裁决)"
    ledger = os.path.join(os.path.dirname(__file__), "..", "3d", "out",
                          "ledger_full.json")
    if os.path.exists(ledger):
        assert C.stone_ring_t(8) == 0.54, "石账现算 ring_t 应为账目真值 0.54"
        assert C.build_centering_for_arch(8, lift=0.0)["id"] == "CEN-ARCH09"
    # 缺省路径不碰 facts: 石账缺失时必须响亮 raise(fail-on-skip), 不许静默兜底。
    # (清 8 号孔缓存后桩掉 os.path.exists 再调 —— raise 必须来自"账本缺失"分支。)
    import unittest.mock as mock
    C._RING_T_BY_ARCH.pop(8, None)
    try:
        with mock.patch.object(C.os.path, "exists", return_value=False):
            with pytest.raises(RuntimeError):
                C.stone_ring_t(8)
    finally:
        C._RING_T_BY_ARCH.clear()


def test_stone_ledger_missing_arch_valueerror(tmp_path):
    """石账无孔 ValueError 分支(复审点3 次要项): 账本在盘但不含该孔 RING 条目
    → 响亮 ValueError(不许 KeyError 裸奔/静默兜底 facts.RING_T), 消息含 1 基孔号。
    tmp_path 假账本走查, 不碰真账本; finally 还原路径与缓存。"""
    led = {"stones": [{"id": "ARCH01.RING.004", "params": {"ring_t": 0.54}}]}
    p = tmp_path / "ledger_nohole.json"
    p.write_text(json.dumps(led), encoding="utf-8")
    old_path = C._LEDGER_PATH
    C._LEDGER_PATH = str(p)
    try:
        C._RING_T_BY_ARCH.clear()
        assert C.stone_ring_t(0) == 0.54, "账内有孔应正常现算"
        with pytest.raises(ValueError, match="石账无孔6"):
            C.stone_ring_t(5)
    finally:
        C._LEDGER_PATH = old_path
        C._RING_T_BY_ARCH.clear()


# ---------------------------------------------------------------- D6 footprint

def test_footprint_shape_per_bent_with_y_and_kind():
    """D6: footprint = [{poly, y0, y1, kind}] 按榀(两行 rib)返回。"""
    res = _central()
    fp = res["footprint"]
    assert isinstance(fp, list) and len(fp) == 2
    y_out = RING_T / 2.0 + C.BENT_Y_CLEAR
    for row in fp:
        assert set(row.keys()) >= {"poly", "y0", "y1", "kind"}
        assert row["kind"] == "rib"
        assert abs(row["y0"] - (row["y1"] - C.RIB_W)) < TOL_Z
    ys = sorted((row["y0"] + row["y1"]) / 2.0 for row in fp)
    assert abs(ys[0] + y_out) < TOL_Z and abs(ys[1] - y_out) < TOL_Z
    assert _poly_area(fp[0]["poly"]) > 0
    assert not hasattr(res, "footprint_polys") and "footprint_polys" not in res


def test_footprint_equals_rib_sampling_pointwise():
    """M12/D6: footprint 轮廓与 rib 采样逐点相等 —— 底缘 = 工作面−RIB_T,
    顶缘 = 工作面, x 采样 = RIB_SEG_N+1 点全跨均布(测试侧独立重算)。"""
    res = _central()
    seg = C.RIB_SEG_N
    for row in res["footprint"]:
        poly = row["poly"]
        assert len(poly) == 2 * (seg + 1)
        bottom = poly[:seg + 1]
        top = poly[seg + 1:]
        for j in range(seg + 1):
            x = -A_CENTRAL + CENTRAL_SPAN * j / float(seg)
            x = max(-A_CENTRAL, min(A_CENTRAL, x))   # 首末钉在 ±a(与实现同钉)
            face = _face(CENTRAL_IDX, CENTRAL_SPAN, CENTRAL_SPRINGER, x)
            assert abs(bottom[j][0] - x) < TOL_Z
            assert abs(bottom[j][1] - (face - C.RIB_T)) < TOL_Z, \
                "footprint 底缘≠rib 采样: %r" % (bottom[j],)
        for j in range(seg + 1):
            x = -A_CENTRAL + CENTRAL_SPAN * (seg - j) / float(seg)
            x = max(-A_CENTRAL, min(A_CENTRAL, x))
            face = _face(CENTRAL_IDX, CENTRAL_SPAN, CENTRAL_SPRINGER, x)
            assert abs(top[j][0] - x) < TOL_Z
            assert abs(top[j][1] - face) < TOL_Z, \
                "footprint 顶缘≠rib 采样: %r" % (top[j],)
    # xc 全局平移字段(D6): poly 是孔局部系, 平移后轮廓 x 范围 = 孔心 ± 半跨
    xg = res["xc"]
    assert xg == GM.arch_center_x(8)
    for row in res["footprint"]:
        pxs = [pt[0] for pt in row["poly"]]
        assert abs((min(pxs) + xg) - (xg - A_CENTRAL)) < TOL_Z
        assert abs((max(pxs) + xg) - (xg + A_CENTRAL)) < TOL_Z


# ---------------------------------------------------------------- 变异补测

def test_rib_two_rows_count_exact():
    """M06: rib 两榀计数 —— 恰 2 行 × RIB_SEG_N 段, y 位置恰两榀。"""
    res = _central()
    ribs = _parts(res, "rib")
    assert len(ribs) == 2 * C.RIB_SEG_N == 48
    ys = sorted({(p["bbox"][2] + p["bbox"][3]) / 2.0 for p in ribs})
    assert len(ys) == 2
    for p in ribs:
        assert abs((p["bbox"][3] - p["bbox"][2]) - C.RIB_W) < 1e-12


def test_waling_spans_both_post_heads():
    """M07: 每根楞木 y 向跨两柱头 —— 同一排的两柱 y 中心都在楞木 y 范围内。"""
    res = _central()
    posts = _parts(res, "post")
    for w in _parts(res, "waling"):
        x = _x_center(w)
        heads = [p for p in posts if abs(_x_center(p) - x) < 1e-9]
        assert len(heads) == 2, "排 x=%r 柱头数 != 2" % x
        for pt in heads:
            yc = (pt["bbox"][2] + pt["bbox"][3]) / 2.0
            assert w["bbox"][2] < yc < w["bbox"][3], \
                "楞木未跨到柱头 y=%r" % yc


def test_end_arch_post_top_elevation_capped():
    """D7: "端孔柱高"语义 = 柱顶标高(非柱长): 端冠 2.23 锚, 柱顶标高
    ≤ crown+ring_t+0.1; 真实工况(工作面已贴拱腹)自然满足。"""
    res, crown = _end()
    assert abs(crown - 2.23) < 0.01  # brief 锚
    top = max(p["bbox"][5] for p in _parts(res, "post"))
    assert top <= crown + RING_T + 0.1
    # 柱顶标高显著高于"柱长"误读的量级(柱底 -2.2 → 柱长 >4m, 标高 <2.9m, 两者可分)
    assert 0 < top < 3.0
