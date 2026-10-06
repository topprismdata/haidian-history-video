# P1-T6: export_print 导出器(inset 吃公差/flip 外翻/STL+3MF/manifest 分批/coupon) 单测。
# 合成数据, 不渲桥。每条判据带负控: FIT 分派边界/打印毫米标尺换算/inset 不外扩/flip 幂等/coupon 三档互分.
import json
import math
import os
import struct
import sys
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "3d"))
import export_print as E
import ledger as L
import printcheck as PC
from families import family_mesh

S50 = 1 / 50.0


# ---------------------------------------------------------------- 合成数据

def _wedge(w=1.0, h=0.4, d=1.0, hw_b=6.0, hw_t=5.9):
    return {"w": w, "h": h, "d": d, "proud": 0.006, "back": 0.3,
            "hw_b": hw_b, "hw_t": hw_t}


def _stone(zone, face, role, course, block, family, params, material="qingshi"):
    return L.new_stone(zone, face, role, course, block, family, params,
                       [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], material)


def _led(stones):
    return {"meta": {"schema": 1, "curve_hash": "t6test", "seed": 0},
            "stones": stones}


def _mesh_fn(stone):
    return family_mesh(stone["family"], stone["params"])


def _extents(verts):
    v = np.asarray(verts, dtype=float)
    return v.max(axis=0) - v.min(axis=0)


# ---------------------------------------------------------------- T1-I1 ledger.allow_clearance

def _clearance_set_ledger():
    led = _led([_stone("ARCH01", "EAST", "RING", 0, 0, "wedge-std", _wedge())])
    led["stones"][0]["clearance_manufacturing_mm"] = 0.3
    return led


def test_neg_clearance_still_rejected_by_default():
    # 负控: 默认闸门不放松 -- 已置 clearance 的账目默认必须红
    errs = L.validate_ledger(_clearance_set_ledger())
    assert any(e.startswith("CLEARANCE_PREMATURE") for e in errs)


def test_allow_clearance_passes_cleared_records():
    assert L.validate_ledger(_clearance_set_ledger(), allow_clearance=True) == []


def test_allow_clearance_keeps_other_checks():
    # 阳性对照: allow_clearance=True 不豁免其他判据(坏 id 照报)
    led = _clearance_set_ledger()
    led["stones"][0]["id"] = "ARCH01.EAST.RING.C00"
    errs = L.validate_ledger(led, allow_clearance=True)
    assert any(e.startswith("ID_COORD") for e in errs)


# ---------------------------------------------------------------- inset

def test_inset_shrinks_exactly_per_axis():
    for params in (_wedge(), {"w": 1.0, "h": 0.4, "d": 0.8}):
        v, f = family_mesh("wedge-std" if "proud" in params else "slab", params)
        c = 0.3
        v2 = E.inset(v, c)
        cm = c / 1000.0
        for ax in range(3):
            lo0, hi0 = min(p[ax] for p in v), max(p[ax] for p in v)
            lo1, hi1 = min(p[ax] for p in v2), max(p[ax] for p in v2)
            assert hi0 - lo0 - (hi1 - lo1) == pytest.approx(2 * cm, abs=1e-9)
            assert lo1 == pytest.approx(lo0 + cm, abs=1e-9)
            assert hi1 == pytest.approx(hi0 - cm, abs=1e-9)


def test_inset_never_expands():
    # 负控: 符号写反会外扩 -- 每个坐标必须落在原 bbox 内
    v, f = family_mesh("wedge-std", _wedge())
    v2 = E.inset(v, 0.5)
    for ax in range(3):
        lo = min(p[ax] for p in v)
        hi = max(p[ax] for p in v)
        for p in v2:
            assert lo - 1e-12 <= p[ax] <= hi + 1e-12


def test_inset_zero_is_identity():
    v, f = family_mesh("slab", {"w": 1.0, "h": 0.4, "d": 0.8})
    v2 = E.inset(v, 0.0)
    assert v2 == [tuple(p) for p in v]


# ---------------------------------------------------------------- FIT 分派

def test_fit_dispatch_boundaries():
    # 边界负控: <0.3 才 TIGHT, <1.0 才 NORMAL, 否则 LOOSE(模型米最小维)
    assert E.fit_for_block((0.2999, 2.0, 2.0), S50)[0] == "TIGHT"
    assert E.fit_for_block((0.3, 2.0, 2.0), S50)[0] == "NORMAL"
    assert E.fit_for_block((0.9999, 2.0, 2.0), S50)[0] == "NORMAL"
    assert E.fit_for_block((1.0, 2.0, 2.0), S50)[0] == "LOOSE"
    assert E.fit_for_block((1.0001, 2.0, 2.0), S50)[0] == "LOOSE"


def test_fit_dispatch_returns_tier_clearance_pairs():
    # W3 口径: FIT_PRINT_MM = 打印件上的真实配合缝(打印毫米);
    # 模型侧 inset = fit_print_mm/scale(模型毫米, scale=1/50 -> NORMAL 吃 15mm)。
    for tier, mm in (("TIGHT", 0.15), ("NORMAL", 0.3), ("LOOSE", 0.5)):
        assert E.FIT_PRINT_MM[tier] == mm
    fit, clr = E.fit_for_block((0.2, 0.2, 0.2), S50)
    assert fit == "TIGHT"
    assert clr == pytest.approx(0.15 / S50, abs=1e-9)      # 7.5 模型毫米
    # scale 耦合负控: 换算若漏乘 scale, S50 与 1:1 会返回同值
    assert E.fit_for_block((0.2, 0.2, 0.2), 1.0)[1] == pytest.approx(0.15, abs=1e-12)


def test_thin_layer_survives_normal_inset():
    # W3 物理标尺负控: 最薄 0.144m 层(coupon back 口径)在 NORMAL 下吃
    # 2x15=30 模型毫米 -> 144-30=114mm 仍正; 打印当量 114/50=2.28mm > 1.2 最小壁。
    import tempfile
    params = {"w": 0.6, "h": 0.144, "d": 0.5}
    v, f = family_mesh("slab", params)
    stone = _stone("ARCH01", "EAST", "PAVING", 0, 0, "slab", params)
    clr_model = E.FIT_PRINT_MM["NORMAL"] / S50
    assert params["h"] * 1000.0 - 2 * clr_model == pytest.approx(114.0, abs=1e-9)
    with tempfile.TemporaryDirectory() as td:
        r = E.export_stone(stone, v, f, td, scale=S50, fit="NORMAL")
        assert r["volume_cm3"] > 0.0                       # 薄层不塌成负体积
        c = clr_model / 1000.0
        assert r["volume_cm3"] == pytest.approx(
            (0.6 - 2 * c) * (0.5 - 2 * c) * (0.144 - 2 * c)
            * S50 ** 3 * 1e6, rel=1e-9)


# ---------------------------------------------------------------- flip_outward

def test_flip_makes_signed_volume_positive():
    v, f = family_mesh("wedge-std", _wedge())
    assert E.signed_volume(v, f) < 0.0          # 族库全体内翻(前置)
    v2, f2 = E.flip_outward(v, f)
    assert E.signed_volume(v2, f2) > 0.0


def test_flip_is_real_flip_and_idempotent():
    v, f = family_mesh("slab", {"w": 1.0, "h": 0.4, "d": 0.8})
    v2, f2 = E.flip_outward(v, f)
    assert f2[0][::-1] == f[0]                  # 确实反序, 不是空转
    v3, f3 = E.flip_outward(v2, f2)
    assert f3 == f2 and E.signed_volume(v3, f3) > 0.0   # 幂等
    # 负控: 输入不被原地改写
    assert f[0][0] == 0 and E.signed_volume(v, f) < 0.0


def test_flip_then_check_stone_ok():
    # S3 时序: inset -> flip -> check(post-inset 几何才准过)
    v, f = family_mesh("wedge-std", _wedge())
    v2 = E.inset(v, 15.0)   # NORMAL@1:50: 0.3 打印毫米 -> 15 模型毫米
    v2, f2 = E.flip_outward(v2, f)
    r = PC.check_stone(v2, f2, scale=S50)
    assert r["ok"], r["issues"]


# ---------------------------------------------------------------- STL/3MF 文件形状

def _stl_counts(path):
    with open(path, "rb") as fh:
        blob = fh.read()
    n = struct.unpack("<I", blob[80:84])[0]
    return blob, n


def test_stl_binary_shape_and_triangle_count():
    import tempfile
    v, f = family_mesh("wedge-std", _wedge())
    stone = _stone("ARCH01", "EAST", "RING", 0, 0, "wedge-std", _wedge())
    with tempfile.TemporaryDirectory() as td:
        r = E.export_stone(stone, v, f, td, scale=S50)
        blob, n = _stl_counts(r["stl"])
        assert len(blob) == 84 + 50 * n
        assert n == 2 * len(f)              # quad 扇形剖分
        assert blob[:5] != b"solid"         # 二进制 STL 头不与 ASCII 撞


def test_stl_volume_matches_print_scale_and_outward():
    import tempfile
    params = _wedge(w=2.0, h=0.5, d=1.0)
    v, f = family_mesh("wedge-std", params)
    stone = _stone("ARCH01", "EAST", "RING", 0, 0, "wedge-std", params)
    with tempfile.TemporaryDirectory() as td:
        r = E.export_stone(stone, v, f, td, scale=S50)
        blob, n = _stl_counts(r["stl"])
        offs = np.frombuffer(blob[84:84 + 50 * n], dtype=np.uint8).reshape(n, 50)
        rows = offs[:, :48].copy().view(np.float32).reshape(n, 4, 3)
        sv = 0.0
        for r in rows:
            a, b, c = (r[i].astype(float) for i in (1, 2, 3))  # [0]=法线
            sv += float(a @ np.cross(b, c)) / 6.0
        # 解析(T9 仿射内缩定律): V1 = |V0| * Π s_ax, s_ax=(ext_ax-2c)/ext_ax
        # —— 单射仿射映射体积恰乘三轴缩放系数(对任意形状成立); 旧"极值顶点
        # 平移"的 (d-c) 闭式随分段映射一并作废(该映射不单射, 真失败件
        # fixture 实证 106 带裁片自交)。c 为 W3 口径模型侧量:
        # NORMAL 0.3 打印毫米 / (1/50) = 15 模型毫米。
        cm = (0.3 / S50) / 1000.0
        ext = [max(p[ax] for p in v) - min(p[ax] for p in v) for ax in range(3)]
        expect_mm3 = (abs(E.signed_volume(v, f))
                      * (ext[0] - 2 * cm) / ext[0]
                      * (ext[1] - 2 * cm) / ext[1]
                      * (ext[2] - 2 * cm) / ext[2]) * S50 ** 3 * 1e9
        assert sv == pytest.approx(expect_mm3, rel=1e-5)
        assert sv > 0                        # 外翻(右手序朝外)


def test_3mf_members_and_counts():
    import tempfile
    v, f = family_mesh("slab", {"w": 1.0, "h": 0.4, "d": 0.8})
    stone = _stone("ARCH01", "EAST", "PAVING", 0, 0, "slab",
                   {"w": 1.0, "h": 0.4, "d": 0.8})
    with tempfile.TemporaryDirectory() as td:
        r = E.export_stone(stone, v, f, td, scale=S50)
        with zipfile.ZipFile(r["stl3mf"]) as z:
            names = set(z.namelist())
            assert {"[Content_Types].xml", "_rels/.rels",
                    "3D/3dmodel.model"} <= names
            root = ET.fromstring(z.read("3D/3dmodel.model"))
        ns = "{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}"
        assert root.get("unit") == "millimeter"
        assert len(root.findall(".//%svertex" % ns)) == len(v)
        assert len(root.findall(".//%striangle" % ns)) == 2 * len(f)


# ---------------------------------------------------------------- export_stone

def test_export_stone_contract_and_volume():
    import tempfile
    params = {"w": 1.0, "h": 0.4, "d": 0.8}
    v, f = family_mesh("slab", params)
    stone = _stone("ARCH01", "EAST", "PIER", 0, 0, "slab", params)
    with tempfile.TemporaryDirectory() as td:
        r = E.export_stone(stone, v, f, td, scale=S50)     # S2: fit 默认 None 自动分档
        assert set(r) == {"stl", "stl3mf", "volume_cm3", "fit",
                          "clearance_print_mm", "clearance_model_mm"}
        assert r["fit"] == "NORMAL"                        # 最小维 0.4m -> NORMAL
        assert r["clearance_print_mm"] == pytest.approx(0.3, abs=1e-12)
        assert r["clearance_model_mm"] == pytest.approx(0.3 / S50, abs=1e-9)
        assert os.path.isfile(r["stl"]) and os.path.isfile(r["stl3mf"])
        c = (0.3 / S50) / 1000.0
        expect_cm3 = (1.0 - 2 * c) * (0.8 - 2 * c) * (0.4 - 2 * c) \
            * S50 ** 3 * 1e6
        assert r["volume_cm3"] == pytest.approx(expect_cm3, rel=1e-9)
        # W3 scale 耦合负控: 1:1 导出时模型毫米 == 打印毫米
        r1 = E.export_stone(stone, v, f, os.path.join(td, "one"), scale=1.0)
        assert r1["clearance_model_mm"] == pytest.approx(0.3, abs=1e-12)
        # 自动分档真实生效: 小块(最小维 0.2m)省略 fit -> TIGHT 7.5 模型毫米
        small_p = {"w": 0.25, "h": 0.2, "d": 0.22}
        small = _stone("ARCH01", "EAST", "PIER", 1, 0, "slab", small_p)
        vs, fs = family_mesh("slab", small_p)
        rs = E.export_stone(small, vs, fs, os.path.join(td, "two"), scale=S50)
        assert rs["fit"] == "TIGHT"
        assert rs["clearance_print_mm"] == pytest.approx(0.15, abs=1e-12)
        assert rs["clearance_model_mm"] == pytest.approx(0.15 / S50, abs=1e-9)


def test_export_stone_rejects_unknown_fit():
    import tempfile
    v, f = family_mesh("slab", {"w": 1.0, "h": 0.4, "d": 0.8})
    stone = _stone("ARCH01", "EAST", "PIER", 0, 0, "slab",
                   {"w": 1.0, "h": 0.4, "d": 0.8})
    with tempfile.TemporaryDirectory() as td:
        with pytest.raises(ValueError):
            E.export_stone(stone, v, f, td, scale=S50, fit="WILD")


# ---------------------------------------------------------------- export_ledger

def _three_stone_ledger():
    return _led([
        _stone("ARCH01", "EAST", "RING", 0, 0, "wedge-std", _wedge()),
        _stone("ARCH01", "EAST", "RING", 0, 1, "wedge-std", _wedge()),
        _stone("ARCH02", "WEST", "SPANDREL", 1, 0, "wedge-std", _wedge(w=0.2, h=0.15, d=0.12)),
    ])


def test_manifest_family_batches(tmp_path):
    led = _led([
        _stone("ARCH01", "EAST", "RING", 0, 0, "wedge-std", _wedge()),
        _stone("ARCH01", "EAST", "RING", 0, 1, "wedge-std", _wedge()),
    ])
    man = E.export_ledger(led, _mesh_fn, str(tmp_path), scale=S50)
    fam = man["families"]["wedge-std"]
    assert fam["count"] == 2
    assert fam["stl"].endswith(".stl")
    # T9 仿射内缩定律: V1 = |V0| * Π (ext_ax-2c)/ext_ax(对任意形状成立;
    # 旧"极值顶点平移"的 d-c 闭式随分段映射一并作废)
    c = (0.3 / S50) / 1000.0   # NORMAL: 打印 0.3mm -> 模型侧 15mm
    wv, wf = family_mesh("wedge-std", _wedge())
    ext = [max(p[ax] for p in wv) - min(p[ax] for p in wv) for ax in range(3)]
    one = (abs(E.signed_volume(wv, wf))
           * (ext[0] - 2 * c) / ext[0]
           * (ext[1] - 2 * c) / ext[1]
           * (ext[2] - 2 * c) / ext[2]) * S50 ** 3 * 1e6
    assert fam["volume_cm3"] == pytest.approx(2 * one, rel=1e-9)
    assert [s["batch"] for s in man["stones"]] == [0, 0]
    assert man == json.loads(json.dumps(man))    # 纯 JSON 可回读
    with open(os.path.join(str(tmp_path), "manifest.json")) as fh:
        assert json.load(fh) == man


def test_manifest_records_fit_and_clearance_timing(tmp_path):
    led = _three_stone_ledger()
    man = E.export_ledger(led, _mesh_fn, str(tmp_path), scale=S50)
    by_id = {s["id"]: s for s in man["stones"]}
    # 分派: 最小维 0.125m -> TIGHT; 0.4 -> NORMAL; manifest 记打印/模型双值(W3 可追溯)
    n = by_id["ARCH01.EAST.RING.C00.B00"]
    t = by_id["ARCH02.WEST.SPANDREL.C01.B00"]
    assert n["fit"] == "NORMAL"
    assert n["clearance_print_mm"] == pytest.approx(0.3, abs=1e-12)
    assert n["clearance_model_mm"] == pytest.approx(15.0, abs=1e-9)
    assert by_id["ARCH01.EAST.RING.C00.B01"]["fit"] == "NORMAL"
    assert t["fit"] == "TIGHT"
    assert t["clearance_print_mm"] == pytest.approx(0.15, abs=1e-12)
    assert t["clearance_model_mm"] == pytest.approx(7.5, abs=1e-9)
    # 时序纪律: 落盘 ledger 带 clearance(allow_clearance 才合法), 原账目不被改写
    assert led["stones"][0]["clearance_manufacturing_mm"] is None
    with open(os.path.join(str(tmp_path), "ledger_print.json")) as fh:
        lp = json.load(fh)
    assert L.validate_ledger(lp) != []            # 默认仍拒(置值必走导出时序)
    assert any(e.startswith("CLEARANCE_PREMATURE") for e in L.validate_ledger(lp))
    assert L.validate_ledger(lp, allow_clearance=True) == []
    # 账目上记的是模型侧 inset(15 模型毫米), 不是打印当量
    assert lp["stones"][0]["clearance_manufacturing_mm"] \
        == pytest.approx(n["clearance_model_mm"], abs=1e-12)
    # W2 双验: 落盘账回读(load_ledger)再过 allow_clearance -- 导出内建同一路径
    rb = L.load_ledger(os.path.join(str(tmp_path), "ledger_print.json"))
    assert L.validate_ledger(rb, allow_clearance=True) == []
    for s in man["stones"]:
        assert os.path.isfile(os.path.join(str(tmp_path), s["stl"]))
        assert os.path.isfile(os.path.join(str(tmp_path), s["stl3mf"]))


def test_roles_whitelist_excludes_carvings(tmp_path):
    led = _led([
        _stone("ARCH01", "EAST", "RING", 0, 0, "wedge-std", _wedge()),
        _stone("ARCH01", "EAST", "CARVE", 0, 0, "slab", {"w": 0.5, "h": 0.3, "d": 0.2}),
        _stone("ARCH01", "EAST", "RAIL", 0, 0, "slab", {"w": 0.5, "h": 0.3, "d": 0.2}),
    ])
    man = E.export_ledger(led, _mesh_fn, str(tmp_path), scale=S50)
    assert [s["id"] for s in man["stones"]] == ["ARCH01.EAST.RING.C00.B00"]
    assert {k["role"] for k in man["skipped"]} == {"CARVE", "RAIL"}
    # 白名单可显式覆盖
    man2 = E.export_ledger(led, _mesh_fn, str(tmp_path / "only_carve"),
                           roles=("CARVE",), scale=S50)
    assert [s["id"] for s in man2["stones"]] == ["ARCH01.EAST.CARVE.C00.B00"]


def test_material_grouping_dirs(tmp_path):
    led = _led([
        _stone("ARCH01", "EAST", "RING", 0, 0, "wedge-std", _wedge(), material="qingshi"),
        _stone("ARCH01", "WEST", "RING", 0, 0, "wedge-std", _wedge(), material="granite"),
    ])
    man = E.export_ledger(led, _mesh_fn, str(tmp_path), scale=S50)
    assert man["materials"] == {"qingshi": 1, "granite": 1}
    for s in man["stones"]:
        assert s["stl"].split(os.sep)[0] == s["material"]


def test_oversized_stone_gets_own_batch(tmp_path):
    led = _led([
        _stone("ARCH01", "EAST", "RING", 0, 0, "wedge-std", _wedge()),
        _stone("ARCH01", "EAST", "PIER", 0, 0, "slab", {"w": 12.0, "h": 1.2, "d": 12.0}),
    ])
    man = E.export_ledger(led, _mesh_fn, str(tmp_path), scale=S50)
    by_id = {s["id"]: s for s in man["stones"]}
    # 12m×1/50×1000 = 240mm > 220 床 -> 独占超批
    assert by_id["ARCH01.EAST.PIER.C00.B00"]["batch"] \
        != by_id["ARCH01.EAST.RING.C00.B00"]["batch"]
    ob = [b for b in man["batches"] if b["oversize"]]
    assert len(ob) == 1 and len(ob[0]["stones"]) == 1
    small = [b for b in man["batches"] if not b["oversize"]]
    assert len(small) >= 1
    assert all(b["used_mm"][0] <= 220.0 and b["used_mm"][1] <= 220.0
               for b in man["batches"] if not b["oversize"])


def test_export_ledger_rejects_invalid_base_ledger(tmp_path):
    led = _three_stone_ledger()
    led["stones"][1]["id"] = led["stones"][0]["id"]     # ID_DUP
    with pytest.raises(ValueError):
        E.export_ledger(led, _mesh_fn, str(tmp_path), scale=S50)


# ---------------------------------------------------------------- coupon

def test_coupon_six_pieces_1to1(tmp_path):
    # S2 裁决: coupon = 打印机配合试片, 1:1 打印 -- 楔块用模型米真尺寸直接出。
    out = E.coupon_set(str(tmp_path))
    assert set(out) == {"TIGHT", "NORMAL", "LOOSE"}
    n_stl = 0
    for tier, rec in out.items():
        assert rec["clearance_print_mm"] == E.FIT_PRINT_MM[tier]
        assert rec["clearance_model_mm"] == pytest.approx(E.FIT_PRINT_MM[tier],
                                                           abs=1e-12)   # 1:1: 模型==打印
        for k in ("a", "b"):
            assert os.path.isfile(rec[k])
            n_stl += 1
    assert n_stl == 6
    # 1:1 负控: STL 真实物理尺寸(NORMAL A 件 x 跨度 = w*1000 - 2x0.3 打印毫米)。
    # 若仍按 S50 缩放会得 ~6mm, 与本判据矛盾。
    blob, cnt = _stl_counts(out["NORMAL"]["a"])
    rows = np.frombuffer(blob[84:84 + 50 * cnt], dtype=np.uint8).reshape(cnt, 50)
    pts = rows[:, :48].copy().view(np.float32).reshape(cnt, 4, 3)
    xspan = float(pts[:, 1:, 0].max() - pts[:, 1:, 0].min())
    assert xspan == pytest.approx(out["NORMAL"]["w_m"] * 1000.0
                                  - 2 * out["NORMAL"]["clearance_print_mm"],
                                  rel=1e-5)


def test_coupon_pair_gap_print_equivalent(tmp_path):
    # 新口径成对缝负控: 打印当量 = 2 x fit_print_mm(0.3/0.6/1.0mm 三档互分)
    out = E.coupon_set(str(tmp_path))
    gaps = {}
    for tier, rec in out.items():
        fp = E.FIT_PRINT_MM[tier]
        assert rec["pair_gap_print_mm"] == pytest.approx(2 * fp, abs=1e-9)
        gaps[tier] = rec["pair_gap_print_mm"]
        # 几何复核(S5 公开口): 以名义 transform 拼装后量 x 向缝隙
        va, fa = E.coupon_mesh(tier, "a")
        vb, fb = E.coupon_mesh(tier, "b")
        w = rec["w_m"]
        tfa = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        tfb = (w, 0.0, 0.0, 0.0, 0.0, 0.0)
        xa = max(np.asarray(va)[:, 0]) + tfa[0]
        xb = min(np.asarray(vb)[:, 0]) + tfb[0]
        assert (xb - xa) * 1000.0 == pytest.approx(2 * fp, abs=1e-9)
        r = PC.gap_check((tfa, (va, fa)), (tfb, (vb, fb)), scale=1.0)
        assert r["ok"], r["issues"]              # 名义拼装不穿透(1:1 口径)
    assert gaps["TIGHT"] < gaps["NORMAL"] < gaps["LOOSE"]   # 三档互相可分


def test_coupon_mesh_public_and_errors():
    # S5: coupon_mesh(tier, side) 公开口径; a/b 同形; 未知档直接拒
    va, fa = E.coupon_mesh("NORMAL", "a")
    vb, fb = E.coupon_mesh("NORMAL", "b")
    assert va == vb and fa == fb
    assert E.signed_volume(va, fa) > 0.0         # 已外翻, 导出即用
    with pytest.raises(ValueError):
        E.coupon_mesh("WILD", "a")


# ── T8b-E8④: 装箱允许旋转(对角斜置非独占批) ──────────────────────────

def test_pack_bed_rotates_diagonal_fit_stone():
    """240x70mm 足印 90° 竖放仍超宽(240>220), 但 (240+70)=310 <= 311.1
    -> 45° 对角斜置入【非独占批】(batch.fit_diagonal), used_mm<=220;
    250x70(=320>311.1) 仍真超床独占(oversize)。负控: 判据不是恒真 ——
    311.2x1 就该被拒(312.2>311.127)。"""
    assign, batches = E._pack_beds([(240.0, 70.0, "A"), (70.0, 240.0, "B"),
                                    (250.0, 70.0, "C")])
    byb = {b["batch"]: b for b in batches}
    for k in ("A", "B"):
        b = byb[assign[k]]
        assert not b.get("oversize"), k
        assert k in b.get("fit_diagonal", [])
        assert b["used_mm"][0] <= 220.0 and b["used_mm"][1] <= 220.0
    ob = byb[assign["C"]]
    assert ob.get("oversize") is True and ob["stones"] == ["C"]
    # 边界负控: 恰好超对角界的一维超长件必被拒(不能总是斜置)
    assign2, batches2 = E._pack_beds([(311.2, 1.0, "D")])
    b2 = [b for b in batches2 if b["stones"] == ["D"]][0]
    assert b2.get("oversize") is True


def test_pack_bed_90_rotation_fits_without_diagonal():
    """210x230 足印: 90° 旋转(230 横放 210 竖)后 210<=220 且 230>220 ——
    长边仍超!归一后 max=230>220 -> 落对角判 (210+230)=440>311 -> oversize。
    而 230x210 与 220x205 这类 90° 可救的件必须正常入批(不标 diagonal)。"""
    assign, batches = E._pack_beds([(210.0, 230.0, "T")])
    b = batches[0]
    assert b.get("oversize") is True
    assign2, batches2 = E._pack_beds([(220.0, 205.0, "N")])
    assert not batches2[0].get("oversize")
    assert not batches2[0].get("fit_diagonal")
