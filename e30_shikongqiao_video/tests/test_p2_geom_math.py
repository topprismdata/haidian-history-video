# -*- coding: utf-8 -*-
"""P2-T2 修复轮 D3: geom_math 纯数学单源(blender-free) + 石账跨源钉。

D3(主控裁决 2026-10-07): deck_z / arch_crown_z / arch_springer_z / width_at
公式自 bridge_geom2 **原样搬移**进 3d/geom_math.py(零 bmesh, 常数读
facts/assumptions); bridge_geom2 改一行委托, 几何逐位不变(core_hash 硬门);
centering/sequencer 消费 geom_math。

跨源钉: geom_math vs 石账(out/ledger_full.json) RING **龙门石** transform z
逐孔等(±1e-9, 与 p1a_slice._assert_same_points 同量化口径) —— 账本由
blender 侧 masonry 公式链生成, 本测试用 geom_math + 账本 params 纯 python
重放同一龙门石的包围盒中心 z; 公式漂移或账本漂移任一发生即红。

重放原理(p1a_slice.build_ring_entries 同款): 龙门石 transform = 其烘焙网格
包围盒中心; 顶点 z 集 = 内弧(z − n̂z·BARREL_PROTRUDE) ∪ 外弧
(z + n̂z·(ring_t+lift)), x 采样 = 石两岸(±缝宽)与岸中点; bmesh 顶点为
float32, 故重放逐顶点 f32 量化后再取 min/max —— 实测与账本逐位相等(|d|=0)。
"""
import json
import math
import os
import struct
import subprocess
import sys
import types

_3D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "3d")
_LEDGER = os.path.join(_3D, "out", "ledger_full.json")

sys.path.insert(0, _3D)

# bridge_geom2/masonry 模块头 import bmesh/mathutils(函数体才真正用)。
# pytest 环境无 blender: 注入桩模块使纯数学/常量可导入; 桩永不参与几何计算
# (本文件不调用任何 build_* 函数; blender 内跑测试时真模块已可导入, 不进此分支)。
try:
    import bmesh  # noqa: F401
except ImportError:
    sys.modules["bmesh"] = types.ModuleType("bmesh")
    _mu = types.ModuleType("mathutils")
    _mu.Vector = object
    _mu.Matrix = object
    sys.modules["mathutils"] = _mu

import bridge_geom2 as BG  # noqa: E402
import facts as F  # noqa: E402
import geom_math as GM  # noqa: E402
import masonry as MAS  # noqa: E402  # 只取缝宽/外伸常量(单一来源), 不调用 bmesh 函数


def _f32(v):
    """float64 -> bmesh 顶点存储精度(float32)。"""
    return struct.unpack("f", struct.pack("f", v))[0]


def _keystone_by_arch(led):
    """账本 RING 条目按孔分组, 取每孔中央龙门石(k == n_ring//2, n 恒奇)。"""
    by_arch = {}
    for s in led["stones"]:
        if ".RING." not in s.get("id", ""):
            continue
        ai = int(s["id"].split(".")[0][4:]) - 1
        by_arch.setdefault(ai, []).append(s)
    out = {}
    for ai, ss in by_arch.items():
        n = ss[0]["params"]["n_ring"]
        ks = [s for s in ss if s["params"]["k"] == n // 2]
        assert len(ks) == 1, "孔%d 龙门石不唯一: %d" % (ai + 1, len(ks))
        out[ai] = ks[0]
    return out


def _keystone_center_z(entry):
    """按账本 params 纯 python 重放龙门石包围盒中心 z(几何量全部来自
    geom_math: springer/a/b/deck; 缝宽常量来自 masonry 单一来源)。"""
    p = entry["params"]
    x0, x1 = p["stations"]
    ai = int(entry["id"].split(".")[0][4:]) - 1
    xc = p["xc"]
    a = GM.SPANS[ai] / 2.0
    b = GM.arch_rise(ai)
    spz = GM.arch_springer_z(ai)
    zs = []
    for gap in (MAS.JOINT_GAP_BACK, MAS.JOINT_GAP):   # 内壁环(缝窄)/前脸环(缝宽)
        lo, hi = x0 + gap, x1 - gap
        for t in (lo, (lo + hi) / 2.0, hi):
            z = F.arch_z(t, xc, spz, a, b)
            d = F.arch_dzdx(t, xc, spz, a, b)
            ln = math.hypot(d, 1.0)
            nz = 1.0 / ln                              # masonry._arch_normal 的 z 分量
            zs.append(_f32(z - nz * MAS.BARREL_PROTRUDE))            # 内弧(伸入洞口)
            zs.append(_f32(z + nz * (p["ring_t"] + p["lift"])))      # 外弧(法向 ring_t+lift)
    return (min(zs) + max(zs)) / 2.0


def _load_real_ledger_or_fail():
    """与 test_p1_slice T9 W2 同纪律: 真账本钉 fail-on-skip, 不许静默跳过
    (干净克隆假绿)。数据由 `blender -b --python 3d/p1a_slice.py -- --g2` 产出。"""
    if not os.path.exists(_LEDGER):
        raise RuntimeError(
            "out/ledger_full.json 不在盘上 —— geom_math 石账跨源钉 fail-on-skip:"
            " 先跑 blender -b --python 3d/p1a_slice.py -- --g2 产出账本;"
            " 或显式 --deselect 本钉(不许静默跳过)")


# ── geom_math 单元(独立期望值, 不与实现共用表达式) ──

def test_deck_z_parabola_independent_anchors():
    assert GM.deck_z(0.0) == 7.30
    assert GM.deck_z(75.0) == 2.20
    assert GM.deck_z(-75.0) == 2.20
    # 抛物线中点: 7.30 - (5.10/75^2)*37.5^2 = 6.025(手算独立值)
    assert abs(GM.deck_z(37.5) - 6.025) < 1e-12
    # 端外越界夹持到端标高
    assert GM.deck_z(80.0) == 2.20


def test_pier_x_table_and_centers():
    # 首台中心 = -75 + 1.35/2(手算独立值); 末台中心镜像 = 75 - 1.35/2;
    # 累加闭合(+75)由 geom_math 导入断言(桥长守恒)守护。
    assert GM.PIER_X[0] == -75.0 + 1.35 / 2.0
    assert abs(GM.PIER_X[-1] - (75.0 - 1.35 / 2.0)) < 1e-9
    assert abs(GM.arch_center_x(8)) < 1e-12
    # 轴对称: 17 孔中心表严格镜像
    for i in range(17):
        assert abs(GM.arch_center_x(i) + GM.arch_center_x(16 - i)) < 1e-9


def test_crown_and_springer_profiles():
    # 中央孔: 冠 5.90 / 起拱 1.14(facts.SPRINGER 声明恒等, M19 锚)
    assert abs(GM.arch_crown_z(8) - 5.90) < 1e-12
    assert abs(GM.arch_springer_z(8) - F.SPRINGER) < 1e-9
    assert abs(F.SPRINGER - 1.14) < 1e-12
    # 端孔(独立手算): deck(±71.03) - 0.50 - 0.32*4.50
    xc0 = GM.arch_center_x(0)
    expect = GM.deck_z(xc0) - 0.50 - 0.32 * 4.50
    assert abs(GM.arch_springer_z(0) - expect) < 1e-12
    assert abs(GM.arch_crown_z(0) - (expect + 0.32 * 4.50)) < 1e-12


def test_width_at_linear_taper():
    # 底半宽 7.3 / 顶半宽 3.28 / 半高线性中点 5.29(手算独立值; f=1 处
    # w_bot+(w_top−w_bot)*1 有 ulp 级合成误差, 用 1e-12 容差不做位比较)
    assert GM.width_at(0.0, -2.20) == 14.60 / 2.0
    assert abs(GM.width_at(0.0, 7.30) - 6.56 / 2.0) < 1e-12
    assert abs(GM.width_at(0.0, (-2.20 + 7.30) / 2.0) - (14.60 + 6.56) / 4.0) < 1e-12
    # 越界夹持: 高于桥面 → 顶半宽; 低于底 → 底半宽
    assert abs(GM.width_at(0.0, 99.0) - 6.56 / 2.0) < 1e-12
    assert GM.width_at(0.0, -99.0) == 14.60 / 2.0
    # x 处桥面随 camber 变 → 同一 z 的半宽随 x 变(端孔更低更宽)
    assert GM.width_at(71.03, 2.7256) < GM.width_at(0.0, 2.7256)


def test_geom_math_is_blender_free():
    """零 bmesh 硬承诺: 干净子进程(无桩)直接 import 必须成功。"""
    r = subprocess.run(
        [sys.executable, "-c", "import geom_math; print(geom_math.deck_z(0.0))"],
        cwd=_3D, capture_output=True, text=True)
    assert r.returncode == 0, "geom_math 子进程导入失败: %s" % r.stderr
    assert r.stdout.strip() == "7.3"


def test_bridge_geom2_delegates_bitwise():
    """本体委托逐位不变(D3 硬门的本体侧可执行证): 同输入同位型。"""
    xs = [(-102 + i) * 0.731 for i in range(205)]        # ±74.5 全桥采样
    for x in xs:
        assert BG.deck_z(x) == GM.deck_z(x)
    for i in range(17):
        assert BG.arch_crown_z(i) == GM.arch_crown_z(i)
        assert BG.arch_springer_z(i) == GM.arch_springer_z(i)
        assert BG.arch_rise(i) == GM.arch_rise(i)
        assert BG.PIER_X[i] == GM.PIER_X[i]
        assert BG.SPANS[i] == GM.SPANS[i]
    # 本体 build 链的收分消费即 geom_math.width_at: build_body_bm/build_void_bm
    # 的逐位正确性由 core_hash 逐位不变门(freeze_manifest §7)背书, 此处不重复建网。


def test_masonry_hw_matches_width_at():
    """masonry._hw(贴面石落点半宽)与 geom_math.width_at 同式(历史上各自实现,
    D3 后必须逐位一致 —— 第二套公式就此绝后)。"""
    for x in (-71.03, -30.0, 0.0, 30.0, 71.03):
        for z in (-2.0, 0.5, 2.0, 5.0, 7.0):
            assert MAS._hw(x, z) == GM.width_at(x, z)


# ── 石账跨源钉(D3) ──

def test_keystone_transform_z_matches_geom_math():
    """geom_math vs 账目 RING 龙门石 transform z 逐孔等(±1e-9)。"""
    _load_real_ledger_or_fail()
    led = json.load(open(_LEDGER))
    keys = _keystone_by_arch(led)
    assert sorted(keys) == list(range(17)), "账本 RING 未覆盖 17 孔: %r" % sorted(keys)
    for ai in range(17):
        entry = keys[ai]
        replay = _keystone_center_z(entry)
        want = entry["transform"][2]
        assert abs(replay - want) <= 1e-9, \
            "孔%d 龙门石 transform z 漂移: geom_math 重放 %.12f != 账本 %.12f" \
            % (ai + 1, replay, want)


def test_keystone_pin_is_not_tautological():
    """负控: 钉必须能抓公式漂移 —— 外弧厚错 1cm 时重放必须显著偏离账本。"""
    _load_real_ledger_or_fail()
    led = json.load(open(_LEDGER))
    entry = _keystone_by_arch(led)[8]
    p = entry["params"]
    doctored = {"id": entry["id"],
                "params": dict(p, ring_t=p["ring_t"] + 0.01)}
    assert abs(_keystone_center_z(doctored) - entry["transform"][2]) > 1e-6, \
        "ring_t 扰动 1cm 未被抓: 跨源钉恒真嫌疑"
