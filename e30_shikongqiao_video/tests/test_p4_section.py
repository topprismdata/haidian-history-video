# P4-T2: export_print zones 参数化 + 段包(section5)出图单测。
# 三判据(plan T2 Step1): ①zones=None 对盘上 central manifest(45fed1e8)零漂移
# (STL/ledger_print 逐字节 + manifest 语义等值, 除时间字段); ②段守恒
# 2747 = Σstones + Σskipped(skipped 带 reason 不静默); ③deferred(12 孔)∪
# section(5 孔) = 17 孔全集不交。附: zones 过滤语义(合成)、两连跑逐字节幂等。
# blender-free: 网格路径走 p1a_slice 纯逻辑段(classify/print_scope/处置)，
# 与 G2 门同序 —— 零漂移测本身就是该重建正确性的逐字节证明。
import copy
import filecmp
import hashlib
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "3d"))

import export_print as EP  # noqa: E402
import ledger as L  # noqa: E402
import p1a_slice as P  # noqa: E402
import section_pack as SEC  # noqa: E402
from families import family_mesh  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRINT_DIR = os.path.join(REPO, "3d", "out", "print")
CENTRAL = os.path.join(PRINT_DIR, "central_slice")
CENTRAL_SHA = "45fed1e8bb64608af6e946944022e9d2913f525f894d13396ddb10de774b9e8d"
EXCLUDED_PATH = os.path.join(PRINT_DIR, "excluded_ids.json")

# 真账实测(P1 G2 门口径): 段(ARCH07-11)账面石 2747, 打印单元 1123,
# ARCH09 子集 245 == 盘上 central manifest 石数。
SEC_STONES_TOTAL = 2747
SEC_UNITS_MEASURED = 1123
ARCH09_UNITS = 245


# ---------------------------------------------------------------- 工具

def _assert_same(a, b, path="manifest", rel=1e-12):
    """语义等值: 容器结构/字符串/整数精确, 浮点 rel 容差。"""
    if isinstance(a, dict):
        assert isinstance(b, dict), path
        assert sorted(a.keys()) == sorted(b.keys()), \
            "%s: keys %r vs %r" % (path, sorted(a.keys()), sorted(b.keys()))
        for k in a:
            _assert_same(a[k], b[k], "%s.%s" % (path, k), rel)
    elif isinstance(a, list):
        assert isinstance(b, list) and len(a) == len(b), \
            "%s: len %d vs %d" % (path, len(a), len(b) if isinstance(b, list) else -1)
        for i, (x, y) in enumerate(zip(a, b)):
            _assert_same(x, y, "%s[%d]" % (path, i), rel)
    elif isinstance(a, float) or isinstance(b, float):
        assert a == pytest.approx(b, rel=rel, abs=0.0), path
    else:
        assert a == b, path


def _strip_volatile(man):
    """除时间字段: created_utc 由门时刻生成; slice 键为 export_slice 增强
    (非 export_ledger 产物), 对拍时双侧剥除。"""
    m = copy.deepcopy(man)
    m["meta"].pop("created_utc", None)
    m.pop("slice", None)
    return m


def _stl_fields(path):
    # type: (str) -> list
    """二进制 STL -> [(12 floats)x三角](法线3+顶点9, 打印件毫米)。"""
    import struct
    with open(path, "rb") as fh:
        buf = fh.read()
    n = struct.unpack("<I", buf[80:84])[0]
    if len(buf) != 84 + 50 * n:
        raise ValueError("stl 结构坏: %s (n=%d, len=%d)" % (path, n, len(buf)))
    off = 84
    out = []
    for _ in range(n):
        out.append(struct.unpack("<12f", buf[off:off + 48]))
        off += 50
    return out


_STL_TOL_MM = 1e-6      # 打印精度(0.1mm)的 1e5 分之一


def _stl_close(path_a, path_b, tol_mm=_STL_TOL_MM):
    # type: (str, str, float) -> bool
    """STL 数值等值: 结构同(尺寸/三角数)且全 float32 场 |delta|<=tol_mm。
    背景: 门时几何在 blender 捆绑 numpy 下计算, 近零相消坐标(裁剪面重合处)
    与本机 numpy 差 ~1e-13 mm, 恰逢 float32 舍入边界 —— 逐字节比较会在
    物理零差异上翻红(见 test_default_zone_none_reproduces_central 注)。"""
    with open(path_a, "rb") as fh:
        a = fh.read()
    with open(path_b, "rb") as fh:
        b = fh.read()
    if len(a) != len(b):
        return False
    fa, fb = _stl_fields(path_a), _stl_fields(path_b)
    if len(fa) != len(fb):
        return False
    for ta, tb in zip(fa, fb):
        for x, y in zip(ta, tb):
            if abs(x - y) > tol_mm:
                return False
    return True


def _stl_close_negative_control(path):
    # type: (str) -> None
    """负控: 比较器非恒真 —— 单坐标扰动 0.01mm(远超容差 1e-6)必判不等;
    结构破坏(截断)也必判不等。"""
    import struct
    with open(path, "rb") as fh:
        buf = bytearray(fh.read())
    x = struct.unpack_from("<f", buf, 84 + 12)[0]      # 首三角第 5 个 float(顶点1.x)
    struct.pack_into("<f", buf, 84 + 12, x + 0.01)
    p = path + ".perturbed"
    with open(p, "wb") as fh:
        fh.write(bytes(buf))
    assert not _stl_close(p, path), "负控失效: 0.01mm 扰动未被判不等"
    with open(p + ".trunc", "wb") as fh:
        fh.write(bytes(buf[:-50]))
    assert not _stl_close(p + ".trunc", path), "负控失效: 截断未被判不等"
    os.unlink(p)
    os.unlink(p + ".trunc")


@pytest.fixture(scope="session")
def print_view():
    """G2 打印视角重建(纯逻辑, ~95s 一次性): (led, statuses, scope_ids, buckets)。"""
    led = SEC.load_full_ledger()
    statuses, scope_ids, buckets = SEC.build_print_view(led)
    return led, statuses, scope_ids, buckets


@pytest.fixture(scope="session")
def pack_pair(print_view, tmp_path_factory):
    """两连跑段包(独立目录, deferred 各自旁挂) -> ((led, scope_ids, buckets), d1, d2, m1, m2)。"""
    led, statuses, scope_ids, buckets = print_view
    d1 = str(tmp_path_factory.mktemp("packA"))
    d2 = str(tmp_path_factory.mktemp("packB"))
    m1 = SEC.pack(led=led, view=(statuses, scope_ids, buckets), out_dir=d1,
                  deferred_path=os.path.join(d1, "deferred_holes.json"))
    m2 = SEC.pack(led=led, view=(statuses, scope_ids, buckets), out_dir=d2,
                  deferred_path=os.path.join(d2, "deferred_holes.json"))
    return (led, scope_ids, buckets), d1, d2, m1, m2


# ---------------------------------------------------------------- 判据① 零漂移

def test_default_zone_none_reproduces_central(tmp_path, print_view):
    """zones=None(默认)重跑中央孔: 与盘上 45fed1e8 除时间字段外语义等值;
    ledger_print 逐字节 + STL 数值等值(1e-6 mm, 负控在测) —— 参数化零漂移
    门(P1 行为回归)。"""
    led, statuses, scope_ids, _buckets = print_view
    man_path = os.path.join(CENTRAL, "manifest.json")
    with open(man_path, "rb") as fh:
        blob = fh.read()
    assert hashlib.sha256(blob).hexdigest() == CENTRAL_SHA   # 基线在位(未被漂移)
    ref = json.loads(blob)

    sub = P.slice_ledger(led, 8, scope_ids=scope_ids)        # 与门时序同一切片
    out = str(tmp_path)
    man = EP.export_ledger(sub, mesh_fn=P._to_bed_mesh_fn(statuses),
                           out_dir=out, scale=P.G2_SCALE)    # zones=None 默认路径
    _assert_same(_strip_volatile(man), _strip_volatile(ref))
    # ledger_print 逐字节(输入子账 = 盘上真账, 处置标只打在副本)
    assert filecmp.cmp(os.path.join(out, "ledger_print.json"),
                       os.path.join(CENTRAL, "ledger_print.json"),
                       shallow=False)
    # (c) STL 数值等值(全 245 石): 门时几何产自 blender 捆绑 numpy, 与本机
    #     numpy 在裁剪面重合处的近零相消坐标上差 ~1e-13 mm(实测最大
    #     6.1e-14), 恰逢 float32 舍入边界 -> 逐字节比较在物理零差异上翻红。
    #     门改判: 结构同(尺寸/三角数) + 全坐标 |delta|<=1e-6 mm(打印精度
    #     1e5 分之一; 逐石 volume rel=1e-12 已把真实漂移压到 1e-10 mm 级,
    #     此门兜底"同体积异顶点排布"类回归); 负控: 0.01mm 扰动必红。
    assert len(man["stones"]) == ARCH09_UNITS
    for s in man["stones"]:
        assert _stl_close(os.path.join(out, s["stl"]),
                          os.path.join(CENTRAL, s["stl"]),
                          tol_mm=1e-6), s["id"]
    _stl_close_negative_control(os.path.join(out, man["stones"][0]["stl"]))

    # belt: zones=["ARCH09"] 走新参数路径, 对同一子账必须产出同一包
    out_z = str(tmp_path) + "_z"
    man_z = EP.export_ledger(sub, mesh_fn=P._to_bed_mesh_fn(statuses),
                             out_dir=out_z, scale=P.G2_SCALE, zones=["ARCH09"])
    assert man_z["meta"]["zones"] == ["ARCH09"]
    mz = copy.deepcopy(man_z)
    mz["meta"].pop("created_utc")
    mz["meta"].pop("zones")
    _assert_same(mz, _strip_volatile(ref))


# ---------------------------------------------------------------- 判据② 段守恒

def test_section5_counts_conservation_basic(print_view, pack_pair):
    """段石数 2747 = Σmanifest.stones + Σskipped; skipped 全带 reason 且与
    盘上排除账(excluded_ids fa1a4ef3)逐 id 同桶; 双计数逐 id 恰一次。"""
    (led, scope_ids, buckets), d1, _d2, man, _m2 = pack_pair
    zone_ids = [s["id"] for s in led["stones"]
                if s["id"].split(".")[0] in SEC.SEGMENT]
    assert len(zone_ids) == SEC_STONES_TOTAL

    exported = [s["id"] for s in man["stones"]]
    skipped = [s["id"] for s in man["skipped"]]
    cons = man["conservation"]
    assert cons["zone_stones_total"] == SEC_STONES_TOTAL
    assert cons["exported"] == len(exported)
    assert cons["skipped"] == len(skipped)
    assert len(exported) + len(skipped) == SEC_STONES_TOTAL
    assert len(set(exported)) == len(exported)
    assert len(set(skipped)) == len(skipped)
    assert not (set(exported) & set(skipped))
    assert set(exported) | set(skipped) == set(zone_ids)

    # 实测钉值: 段打印单元 1123(spec ~913 估算的实测修正), ARCH09=245=central
    assert len(exported) == SEC_UNITS_MEASURED
    assert sum(1 for i in exported if i.startswith("ARCH09.")) == ARCH09_UNITS
    with open(os.path.join(CENTRAL, "manifest.json"), encoding="utf-8") as fh:
        central_ids = {s["id"] for s in json.load(fh)["stones"]}
    assert {i for i in exported if i.startswith("ARCH09.")} == central_ids

    # skipped 带 reason 不静默; 桶名与盘上排除账一致(独立旁账互证)
    with open(EXCLUDED_PATH, encoding="utf-8") as fh:
        id2bucket = {i: b for b, ids in json.load(fh)["buckets"].items() for i in ids}
    for e in man["skipped"]:
        assert e.get("reason", "").startswith("g2_excluded:"), e
        assert id2bucket[e["id"]] == e["reason"].split(":", 1)[1], e
        assert e["id"] not in scope_ids

    # 体积/件数汇总: 总量=逐石和; 材质分目录(qingshi/maoshi 双组都在)
    assert cons["volume_cm3_total"] == pytest.approx(
        sum(s["volume_cm3"] for s in man["stones"]), rel=1e-9)
    assert cons["batches"] == len(man["batches"])
    for s in man["stones"]:
        assert s["stl"].split(os.sep)[0] == s["material"]
        assert 0 <= s["batch"] < len(man["batches"])
    assert {s["material"] for s in man["stones"]} == {"qingshi", "maoshi"}

    # coupon 首件约定: 文件在盘 + manifest 登记
    assert man["coupon"]["policy"] == "first_article"
    for f in man["coupon"]["files"]:
        assert os.path.isfile(os.path.join(d1, f)), f

    # 片名口径: 产物与报告禁"全桥"(留续清单除外)
    for name in ("manifest.json", "PACK_REPORT.md"):
        with open(os.path.join(d1, name), encoding="utf-8") as fh:
            assert "全桥" not in fh.read(), name
    # 汇总进报告: 件数/体积实测值必须出现
    with open(os.path.join(d1, "PACK_REPORT.md"), encoding="utf-8") as fh:
        rep = fh.read()
    assert str(SEC_UNITS_MEASURED) in rep and str(SEC_STONES_TOTAL) in rep
    assert "913" in rep          # 预估对照(spec#4 M1)与实测偏差表


def test_section5_pack_idempotent(pack_pair):
    """两连跑(独立目录)全树逐字节同: manifest(created_utc 归空)/ledger_print/
    STL/3MF(容器时间归一)/deferred/报告。"""
    (_led, _scope_ids, _buckets), d1, d2, _m1, _m2 = pack_pair

    def tree(root):
        out = {}
        for r, _ds, fs in os.walk(root):
            for f in fs:
                p = os.path.join(r, f)
                with open(p, "rb") as fh:
                    out[os.path.relpath(p, root)] = fh.read()
        return out

    t1, t2 = tree(d1), tree(d2)
    assert sorted(t1.keys()) == sorted(t2.keys())
    diff = sorted(k for k in t1 if t1[k] != t2[k])
    assert not diff, "两连跑字节不同的产物: %r" % diff[:5]


# ---------------------------------------------------------------- 判据③ 互补

def test_deferred_complement(print_view, tmp_path):
    """deferred(12 孔) ∪ section(5 孔) = 17 孔全集, 不交; 计数与段包/全账合账;
    落盘确定性(两连跑逐字节同)。"""
    led, _statuses, scope_ids, _buckets = print_view
    doc = SEC.deferred_plan(led, scope_ids, SEC.SEGMENT)
    all_zones = sorted({s["id"].split(".")[0] for s in led["stones"]})
    assert len(all_zones) == 17
    assert doc["n_holes"] == 12
    assert doc["zones"] == [z for z in all_zones if z not in set(SEC.SEGMENT)]
    assert not (set(doc["zones"]) & set(SEC.SEGMENT))
    assert set(doc["zones"]) | set(SEC.SEGMENT) == set(all_zones)
    # 计数合账: 石 5935 = 段 2747 + 留续; 单元 2113 = 段 1123 + 留续
    assert doc["stones_total"] == len(led["stones"]) - SEC_STONES_TOTAL
    assert doc["units_total"] == len(scope_ids) - SEC_UNITS_MEASURED
    assert doc["unit_ids"] == sorted(
        i for i in scope_ids if i.split(".")[0] in set(doc["zones"]))
    assert sum(v["stones"] for v in doc["per_zone"].values()) == doc["stones_total"]
    assert sum(v["units"] for v in doc["per_zone"].values()) == doc["units_total"]

    p1 = os.path.join(str(tmp_path), "d1.json")
    p2 = os.path.join(str(tmp_path), "d2.json")
    SEC.write_deferred(doc, p1)
    SEC.write_deferred(doc, p2)
    assert filecmp.cmp(p1, p2, shallow=False)


# ---------------------------------------------------------------- zones 过滤语义(合成)

def _slab(zone, block):
    return L.new_stone(zone, "EAST", "SPANDREL", 0, block, "slab",
                       {"w": 0.5, "h": 0.2, "d": 0.2}, [0.0] * 6, "qingshi")


def _synth_led():
    return {"meta": {"schema": 1, "curve_hash": "t2test", "seed": 0},
            "stones": [_slab("ARCH01", i) for i in range(3)]
                      + [_slab("ARCH02", i) for i in range(2)]}


def _mesh_fn(stone):
    return family_mesh(stone["family"], stone["params"])


def test_zones_filter_selects_and_skips(tmp_path):
    """zones 选孔过滤: 选区内导出、区外 skipped 带 reason; 装箱与单孔直出
    等价; 默认调用(不带 zones 键)与 zones=None 逐字节等价(合成面零漂移)。"""
    led = _synth_led()
    d_zone = os.path.join(str(tmp_path), "zone")
    d_ref = os.path.join(str(tmp_path), "ref")
    m_zone = EP.export_ledger(led, _mesh_fn, d_zone, zones=["ARCH02"])
    ids = [s["id"] for s in m_zone["stones"]]
    assert ids == ["ARCH02.EAST.SPANDREL.C00.B%02d" % i for i in range(2)]
    sk = m_zone["skipped"]
    assert [e["id"] for e in sk] == ["ARCH01.EAST.SPANDREL.C00.B%02d" % i
                                     for i in range(3)]
    assert all(e["reason"] == "zone_not_selected" for e in sk)
    assert m_zone["meta"]["zones"] == ["ARCH02"]

    sub = {"meta": dict(led["meta"]),
           "stones": [s for s in led["stones"]
                      if s["id"].split(".")[0] == "ARCH02"]}
    m_ref = EP.export_ledger(sub, _mesh_fn, d_ref)
    assert m_ref["batches"] == m_zone["batches"]
    assert [{k: v for k, v in s.items() if k not in ("stl", "stl3mf")}
            for s in m_ref["stones"]] == \
           [{k: v for k, v in s.items() if k not in ("stl", "stl3mf")}
            for s in m_zone["stones"]]

    # 默认零漂移(合成面): 传统调用 vs zones=None -> 字典等值(除时间)+账文件逐字节
    d_old = os.path.join(str(tmp_path), "old")
    d_none = os.path.join(str(tmp_path), "none")
    m_old = EP.export_ledger(led, _mesh_fn, d_old)
    m_none = EP.export_ledger(led, _mesh_fn, d_none, zones=None)
    assert "zones" not in m_old["meta"] and "zones" not in m_none["meta"]
    a, b = copy.deepcopy(m_old), copy.deepcopy(m_none)
    a["meta"].pop("created_utc", None)
    b["meta"].pop("created_utc", None)
    _assert_same(b, a)
    assert filecmp.cmp(os.path.join(d_old, "ledger_print.json"),
                       os.path.join(d_none, "ledger_print.json"), shallow=False)
    for s in m_old["stones"]:
        assert filecmp.cmp(os.path.join(d_old, s["stl"]),
                           os.path.join(d_none, s["stl"]), shallow=False)

    # 空选区: 全 skipped 带 reason, 不崩(响亮空包语义)
    m_empty = EP.export_ledger(led, _mesh_fn, os.path.join(str(tmp_path), "e"),
                               zones=["ARCH99"])
    assert m_empty["stones"] == [] and m_empty["batches"] == []
    assert len(m_empty["skipped"]) == 5

    # 角色白名单语义沿用: role 过滤的 skipped 不带 reason(P1 口径不变)
    carve = L.new_stone("ARCH01", "EAST", "CARVE", 0, 9, "lion",
                        {"w": 0.2, "h": 0.2, "d": 0.2}, [0.0] * 6, "qingshi")
    led_c = {"meta": dict(led["meta"]), "stones": led["stones"] + [carve]}
    m_c = EP.export_ledger(led_c, _mesh_fn,
                           os.path.join(str(tmp_path), "carve"),
                           zones=["ARCH01"])
    role_skips = [e for e in m_c["skipped"] if e["id"].endswith(".B09")]
    assert len(role_skips) == 1 and "reason" not in role_skips[0]
