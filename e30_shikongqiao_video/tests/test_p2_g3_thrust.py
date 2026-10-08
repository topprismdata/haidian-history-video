# e30_shikongqiao_video/tests/test_p2_g3_thrust.py
# -*- coding: utf-8 -*-
"""P2-T6 g3_check.py ③压力线: Heyman 刚块链(半环 crown→springer)双 case。

判据(brief 接口节全量):
- pressure_line(ring_stones, extra_loads, band_in_out_fns, H_range) ->
  {feasible, H:[min,max], polyline:[(x,z)...]}: 刚块链法 —— 券石按 params
  角域切块(重量=export_print.signed_volume×密度 体积单源; 质心=烘焙网格
  散度质心, 与单源体积互证), 给定冠推力 H 逐缝递推合力 R_k=R_{k-1}+W_k,
  R_k 与块间缝(放射缝, 同 masonry 端面)交点须落在 [intrados,extrados]
  带内; H 网格 0.1-1.2×qL²/8f 扫描求可行区间(边界二分细化, 上界被触及
  自动外扩防删失 —— 覆盖机制非几何参数)。
- 解析对照: 合成半圆(R=1, 环带 0.27, 块宽 ε→0 无自重) + 均布 q(水平投影
  均布, 经 extra_loads) → funicular 抛物线 H*=qL²/(8f) 必须落在可行区间
  内, 且区间下界与 H* 相差 ≤5%(均布荷载的拱轴重合解; 上界由弹簧截面
  出带约束给出, 高于 H* 属带厚效应, 记录不判假)。
- 双 case(P2-T6 裁决后): acceptance=结构带(RING+胶结锁固带: s 检验截面
  厚 ring_t+0.35, 带石自重仍计入块链 W_k)必须 feasible; robustness=裸环
  (s∈[0,ring_t])只记录不判红。
  真账实况(T6b 相位协变 + T6c/d 冠载字面杠杆分摊后): 裸环与 acceptance
  均 **17/17 全 feasible**(历史停车线解除; "券架须驻留至拱肩近满才可
  落架"结论存档于报告 §7.2 失效边界)。冠楔接触带(跨冠缝环块两缝
  st0/st1)内的肩荷按字面连续杠杆 fr=(x−st0)/(st1−st0) 分派(与跨冠环块
  θ 连续分派同构, 跨带边界连续); 带外整列归所属半环。
- 停车线: acceptance 不可行 → run_g3 raise G3_FROZEN_GEOMETRY_CONFLICT
  (点名孔), 禁调封卷参数自救; 阈值不为绿而调(0.35 唯一声明带宽)。

五负控: ①楔块重心外移 0.3m → feasible 翻假 ②带缩(t×2/3)区间变窄 /
带加厚(t×1.5)区间变宽 ③裸环退化路径(R5a 清空 acceptance≡robustness,
停车线不误触) ④H 越界出带(过小 H 压力线下穿 intrados / 过大 H 上穿
extrados, 逐缝 exit 点名) ⑤R5a 清空退化 + 注入超重带石(自重入链) →
停车线真触发; 另: 纯消融负控(冠楔分摊整体消融, 带界置 0, 位置/权重
不动 → A08-11 恰 4 孔翻红) + 旧口径 A/B(LOCK_BAND_M→0 精确集钉值) +
带界守恒(r5a 逐石径向 ≤0.35, 0.36m 外肩石不得混入) + 冠楔半宽派生
钉值与带界 ±0.1m 不敏感不变量(审查 W2)。

微账几何同 test_p2_g3_dag(全部 GM 现算); 真账 17 孔(存在性 skip)为
acceptance 全 feasible + gate_stress 同形节 + H 区间表 + A01/A08 压力线
图落盘(m20_ctrl/)的常驻断言。
"""
import copy
import hashlib
import json
import math
import os
import sys
from typing import List, Tuple

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "3d"))
os.environ.setdefault("MPLBACKEND", "Agg")

import facts as F
import geom_math as GM
import ledger as L
import g3_check as G3

_HERE = os.path.dirname(os.path.abspath(__file__))
_SEQ = os.path.join(_HERE, "..", "3d", "out", "sequence.json")
_LEDSEQ = os.path.join(_HERE, "..", "3d", "out", "ledger_sequenced.json")
_CTRL = os.path.join(_HERE, "..", "3d", "m20_ctrl")
_NEED = [_SEQ, _LEDSEQ]


# ---------------------------------------------------------------------------
# 合成半环 fixture: 环形扇块(ring-wedge 烘焙, 体积走 families+signed_volume
# 单源) + 同心圆带函数 + 解析缝法向。几何: 圆心(0,0), 内半径 R, 径向环带 t,
# 拱冠 (0,R), 弹簧面 (±R,0), 右半环 θ∈[0,π/2]。
# ---------------------------------------------------------------------------

def _sector_stone(k, th0, th1, R, t, width, n_seg=16):
    """环形扇块 → ring-wedge 石。烘焙网格 = 全局坐标平移到 bbox 中心
    (同 p1a_slice.make_ring_entry 质心锚口径), transform=[bbox 中心]。"""
    r_in, r_out = R, R + t
    pts = []  # (θ 采样) 4 环: 内/外 × 前/背(y=±width/2)
    for i in range(n_seg + 1):
        th = th0 + (th1 - th0) * i / n_seg
        pts.append(th)
    verts = []
    for th in pts:
        for r in (r_in, r_out):
            verts.append((r * math.sin(th), -width / 2.0, r * math.cos(th)))
    for th in pts:
        for r in (r_in, r_out):
            verts.append((r * math.sin(th), width / 2.0, r * math.cos(th)))
    n = n_seg + 1

    def _quad(a, b, c, d):
        return (a, b, c, d)

    faces = []
    for i in range(n_seg):  # 内弧面 / 外弧面
        faces.append(_quad(i, i + 1, i + 1 + n, i + n))            # 内(径向)
        faces.append(_quad(n + i, n + i + 1, 2 * n + i + 1, 2 * n + i))  # 外
    for i in range(n_seg):  # 前脸 / 背面(环带面)
        faces.append(_quad(i, n + i, n + i + 1, i + 1))
        faces.append(_quad(2 * n + i, 3 * n + i, 3 * n + i + 1, 2 * n + i + 1))
    # 两端放射端面(th0 / th1)
    faces.append(_quad(0, n, 3 * n, 2 * n))            # θ0 端面(内前-外前-外背-内背)
    faces.append(_quad(n - 1, 3 * n - 1, 4 * n - 1, 2 * n - 1))  # θ1 端面
    cx = min(v[0] for v in verts) + (max(v[0] for v in verts)
                                     - min(v[0] for v in verts)) / 2.0
    cz = min(v[2] for v in verts) + (max(v[2] for v in verts)
                                     - min(v[2] for v in verts)) / 2.0
    local = [(v[0] - cx, v[1], v[2] - cz) for v in verts]
    th_mid = (th0 + th1) / 2.0
    st0, st1 = R * math.sin(th0), R * math.sin(th1)
    return L.new_stone(
        "SYN", "EAST", "RING", 0, k + 1, "ring-wedge",
        {"angles": [math.degrees(th0), math.degrees(th1)],
         "stations": [st0, st1], "xc": 0.0, "ring_t": t, "lift": 0.0,
         "n_ring": 2 * k + 1, "k": k, "through": "full_depth",
         "bake": {"v": local, "f": faces}},
        [cx, 0.0, cz, 0.0, 0.0, 0.0], "qingshi")


def _sector_ring(t, width, n_half=24):
    """右半环 n_half 块扇石(θ 0→π/2 等分, 拱冠无缝面 x=0 为首缝)。"""
    return [_sector_stone(k, math.pi / 2.0 * k / n_half,
                          math.pi / 2.0 * (k + 1) / n_half,
                          1.0, t, width)
            for k in range(n_half)]


def _sector_bands(t):
    """同心圆带: intrados=√(R²-x²), extrados=√((R+t)²-x²)(径向带真值)。"""

    def z_in(x):
        r2 = 1.0 - x * x
        return math.sqrt(r2) if r2 > 0.0 else 0.0

    def z_out(x):
        r2 = (1.0 + t) ** 2 - x * x
        return math.sqrt(r2) if r2 > 0.0 else 0.0

    return z_in, z_out


def _sector_dzdx():
    def dzdx(x):
        xx = min(max(x, -(1.0 - 1e-9)), 1.0 - 1e-9)
        return -xx / math.sqrt(max(1.0 - xx * xx, 1e-18))

    return dzdx


def _uniform_q_loads(q, n_half=24):
    """均布 q(每水平单位长度)离散到右半环各块水平投影中点。"""
    loads = []
    for k in range(n_half):
        x0 = math.sin(math.pi / 2.0 * k / n_half)
        x1 = math.sin(math.pi / 2.0 * (k + 1) / n_half)
        loads.append({"x": (x0 + x1) / 2.0, "weight": q * (x1 - x0)})
    return loads


def _q_pressure_line(t, q=1.0, extra=None, **kw):
    return G3.pressure_line(
        _sector_ring(t, width=1e-3),      # 块宽 ε→0: 荷载=纯均布 q(解析对照)
        extra if extra is not None else _uniform_q_loads(1.0),
        _sector_bands(t), (0.1 * 0.5 * q, 1.2 * 0.5 * q),
        dzdx_fn=_sector_dzdx(), **kw)


# ---------------------------------------------------------------------------
# 解析对照 + 带厚敏感性(正控)
# ---------------------------------------------------------------------------

def test_analytic_semicircle_uniform_q_h_ref():
    """合成半圆+均布 q → H*=qL²/8f=0.5q 落在可行区间内, 下界偏差 ≤5%。
    网格 0.1-1.2×H* 必须覆盖区间(不删失); 压力线折线全部落带内。"""
    res = _q_pressure_line(t=0.27)
    assert res["feasible"], res
    hmin, hmax = res["H"]
    href = 0.5                                   # qL²/(8f) = 1·4/(8·1)
    assert hmin <= href <= hmax, (hmin, href, hmax)
    assert hmin >= 0.95 * href, \
        "可行区间下界 %r 距解析 funicular %r 超 5%%" % (hmin, href)
    # 区间必须在最终扫描范围内闭合(删失防护自动外扩过 1.2×H_ref 原上限:
    # 弹簧截面出带约束给出 Hmax≈1.47×H_ref, brief 网格原上限不够是物理事实)
    assert res["sweep"][0] <= hmin and hmax < res["sweep"][1] * (1 - 1e-9)
    assert res["censored"], "1.2×H_ref 上限应被触及(否则 fixture 口径变了)"
    # 压力线折线: 冠→弹簧, 每点带内(feasible 的必要条件, 冗余自证)
    z_in, z_out = _sector_bands(0.27)
    poly = res["polyline"]
    assert len(poly) >= 10 and poly[0][0] == pytest.approx(0.0, abs=1e-9)
    for x, z in poly:
        assert z_in(x) - 1e-9 <= z <= z_out(x) + 1e-9, (x, z)


def test_band_thickening_widens_interval():
    """正控+负控②: 环带加厚(t×1.5)→可行区间变宽; 带缩(t×2/3)→变窄。
    (均布 q 半圆在 t/R<≈0.155 全区间不可行 —— 带厚下限, 亦为物理自证)"""
    widths = {}
    for t in (0.18, 0.27, 0.405):
        res = _q_pressure_line(t=t)
        assert res["feasible"], (t, res)
        widths[t] = res["H"][1] - res["H"][0]
    assert widths[0.18] < widths[0.27] < widths[0.405], widths


# ---------------------------------------------------------------------------
# 五负控
# ---------------------------------------------------------------------------

def test_neg1_voussoir_centroid_shift_flips_infeasible():
    """①楔块重心外移 0.3m → feasible 翻假(荷载位置敏感性负控)。

    工况: 均布 q 半圆 t=0.18R(窄区间 [0.554,0.600]×q)+ 一块 0.10q 的肩块
    于 x=0.4R —— base 可行; 把该块重心向冠侧平移 0.3m(失稳向) → 翻假;
    对称验证向弹簧侧外移 0.3m(稳定向)仍可行 —— 双向证明判据对荷载位置
    敏感而非恒真。注: 本模型(经解析 funicular 对照校准)中半圆自重/均布
    工况的外移是稳定向(区间整体下移), brief 原案"外移翻假"在物理上不
    成立, 故负控取真实失稳向并双向自证, 不为凑方向改判据。"""
    t = 0.18
    loads = _uniform_q_loads(1.0) + [{"x": 0.4, "weight": 0.10}]
    base = G3.pressure_line(_sector_ring(t, 1e-3), loads,
                            _sector_bands(t), (0.2, 1.6),
                            dzdx_fn=_sector_dzdx())
    assert base["feasible"], base
    inner = copy.deepcopy(loads)
    inner[-1]["x"] = 0.4 - 0.3                    # 失稳向: 重心向冠侧 0.3m
    res = G3.pressure_line(_sector_ring(t, 1e-3), inner,
                           _sector_bands(t), (0.2, 1.6),
                           dzdx_fn=_sector_dzdx())
    assert not res["feasible"], \
        "重心位移 0.3m 后仍 feasible —— 判据对荷载位置不敏感(恒真嫌疑)"
    outer = copy.deepcopy(loads)
    outer[-1]["x"] = 0.4 + 0.3                    # 稳定向: 向弹簧侧 0.3m
    res2 = G3.pressure_line(_sector_ring(t, 1e-3), outer,
                            _sector_bands(t), (0.2, 1.6),
                            dzdx_fn=_sector_dzdx())
    assert res2["feasible"], res2


def test_neg4_H_out_of_band_exits():
    """④H 越界出带: 过小 H → 某缝交点 s<0(下穿 intrados); 过大 H →
    s>t(上穿 extrados); detail 逐缝点名。"""
    res = _q_pressure_line(t=0.27, H_detail=(0.2, 1.4))
    hmin, hmax = res["H"]
    lo, hi = res["detail"][0.2], res["detail"][1.4]
    assert not lo["feasible"] and not hi["feasible"]
    lo_exits = [j for j in lo["joints"] if j["exit"] == "intrados"]
    hi_exits = [j for j in hi["joints"] if j["exit"] == "extrados"]
    assert lo_exits and all(j["s"] < 0.0 for j in lo_exits), lo_exits[:3]
    assert hi_exits and all(j["s"] > j["s_max"] for j in hi_exits), hi_exits[:3]
    assert hmin > 0.2 and hmax < 1.4


def test_pressure_line_micro_wedge_std_smoke():
    """微账路径冒烟: wedge-std 券石(体积走族网格分支)+ GM 拱带函数 →
    pressure_line 出形(不判可行性, 只验接口/体积分支不炸)。"""
    ai = 7
    xc = GM.arch_center_x(ai)
    springer = GM.arch_springer_z(ai)
    a = GM.SPANS[ai] / 2.0
    b = GM.arch_rise(ai)
    rt = 0.41
    n = 9
    stones = []
    for k in range(n):
        x0 = xc - a + (2 * a) * k / n
        x1 = xc - a + (2 * a) * (k + 1) / n
        stones.append(L.new_stone(
            "ARCH08", "EAST", "RING", 0, k + 1, "wedge-std",
            {"h": 0.5, "w": 0.8, "d": 1.2, "proud": 0.05,
             "hw_b": 0.38, "hw_t": 0.36, "angles": [0.0, 1.0],
             "ring_t": rt, "xc": xc, "stations": [x0, x1],
             "n_ring": n, "k": k, "lift": 0.0, "through": "full_depth"},
            [(x0 + x1) / 2.0, 0.0,
             F.arch_z((x0 + x1) / 2.0 - xc, 0.0, springer, a, b) + rt / 2.0,
             0.0, 0.0, 0.0], "qingshi"))
    z_in = lambda x: F.arch_z(x - xc, 0.0, springer, a, b)          # noqa: E731
    z_out = lambda x: z_in(x) + rt                                  # noqa: E731
    dz = lambda x: F.arch_dzdx(                                    # noqa: E731
        min(max(x - xc, -a + 1e-6), a - 1e-6), 0.0, springer, a, b)
    res = G3.pressure_line(stones, [], (z_in, z_out), (1.0, 60.0),
                           dzdx_fn=dz)
    assert isinstance(res["feasible"], bool)
    # 右半环 = 4 块全右石 + 龙门石右半 → 5 缝间 + 冠/弹簧缝 = 6 点折线
    assert len(res["polyline"]) == 6
    assert len(res["polyline_left"]) == 6
    assert res["H"] is None or res["H"][0] <= res["H"][1]


# ---------------------------------------------------------------------------
# 真账 17 孔(存在性 skip): acceptance 全 feasible + 停车线 + H 区间表 + 图
# ---------------------------------------------------------------------------

def _real_chain():
    with open(_SEQ) as f:
        seqdoc = json.load(f)
    led = L.load_ledger(_LEDSEQ)
    return led, seqdoc


def _excl_in_void():
    with open(os.path.join(os.path.dirname(_SEQ), "print",
                           "excluded_ids.json")) as f:
        return set(json.load(f)["buckets"]["in_void"])


@pytest.mark.skipif(not all(os.path.exists(p) for p in _NEED),
                    reason="out/sequence.json+ledger_sequenced.json 不在盘上")
def test_real_17_holes_acceptance_feasible_and_report():
    """真账 17 孔双 case + 停车线协议(P2-T6 裁决两层落地后)。

    裁决链(T6 首核停车线 → 主控两层裁决 → T6b 相位协变重账 → T6c/d 冠载
    分摊):
    ① R5a 收缩真锁固带: 足印距 extrados ≤0.35m(径向, facts.arch_signed_r
      单源; 竖直读法探针证伪 —— 拆拱脚稳定配重致 ARCH05/13 翻假) ∧
      剔除双建模占位(0.985 吞没 29 石 → R5b)。R5a: 1307 → 1290 → 1342。
    ② 结构协同假设: 锁固带与券脸石餬灰胶结(C:A5 "餬灰璺"), 并入拱截面
      (s 检验带厚 ring_t+0.35; 带重计入块链 W_k)。
    ③④ 相位协变重账 + 冠载**字面连续杠杆**分摊: 冠楔接触带(跨冠缝环块
      两缝 st0/st1=简支两支点)内肩荷 fr=(x−st0)/(st1−st0) 分派, 左=1−fr,
      跨带边界连续(带边 0/1 精确衔接整列归侧, 无阶跃); 带外整列归所属
      半环。镜像协变(镜像孔 fr 自动 1−fr, 构造性)。
    实测(字面杠杆出货口径, 报告 §8.3 同源重打): robustness(裸环) 17/17;
    acceptance **17/17 全 feasible**。镜像对窗口对称至 ~1.6e-3(A07
    [31.256,41.518] vs A11 [31.257,41.519])。run_g3 正常返回(停车线解除)。
    纯消融负控(审查 W3): 冠楔分摊整体消融(带界置 0, 荷载位置/权重/判据
    完全不动)→ A08-11 恰 4 孔翻红 —— 分摊 load-bearing, 且红来自分摊
    而非位置挪动(旧负控挪 x=xc+0.6 混入位置效应+0.5m 伪带宽, 已废)。
    旧口径 A/B(截面不加厚 LOCK_BAND_M=0)对照: 精确集钉值 {07..11}
    (50/50 前身模型下实测为 {06..12} 7 孔; 字面杠杆带更宽, A06/A12 在
    连续分摊下得缓 —— 钉值随出货口径重测, 见报告 §9)。
    若砖谱/几何/分摊模型再冻结, 此处结论应被显式复核而非静默漂移。"""
    led, seqdoc = _real_chain()
    r5a = G3.load_r5a_shoulders()
    # [P2-T6b 相位协变重账] R5a 1290→1342 (+52): in_void 手性修复释放 48 块
    # (12 孔×4, 全部入本孔 R5a) + dm/rbo 0.985 体素口径边界移位 +4
    # (A13 +2, A15 +2; dm 总数 28→29)。归因表见 p2-task-6-report.md §8。
    # [拱线族返工清债 2026-10-08] 1342→1382(+40=ring_band_overlap 182→222,
    # 全在 b>a 三孔; 与 test_p2_sequencer 同源推导)
    assert sum(len(v) for v in r5a.values()) == 1382
    assert sorted(r5a) == ["ARCH%02d" % i for i in range(1, 18)]

    gate = G3.stress_gate(led, r5a=r5a)
    # 同形节: 键与 gate_dag 对齐(报告串接契约)
    for key in ("violations", "violation_counts", "ok", "elapsed_s"):
        assert key in gate
    # robustness(裸环)17/17 全 feasible, 只记录不判红
    for zh in sorted(gate["holes"]):
        h = gate["holes"][zh]
        assert h["robustness"]["feasible"], zh
        assert h["robustness"]["band_t"] == 0.0
        assert h["band_bonded"] and h["n_r5a"] > 0
        assert h["acceptance"]["band_t"] == pytest.approx(G3.LOCK_BAND_M)
    # acceptance(结构带)实况: 17/17 全 feasible(T6d 字面杠杆裁决基线;
    # 几何/砖谱/荷载分摊再变更须显式复核本行)
    infeasible = sorted(zh for zh in gate["holes"]
                        if not gate["holes"][zh]["acceptance"]["feasible"])
    assert infeasible == [], infeasible
    assert gate["violations"] == []
    assert gate["skipped_zones"] == []
    # 镜像对窗口对称(全链协变的直接证据; 推力幅值镜像不变, 对称至 5e-3)
    for a, b in ((7, 11), (8, 10), (1, 17)):
        za, zb = "ARCH%02d" % a, "ARCH%02d" % b
        ha, hb = gate["holes"][za]["acceptance"]["H"], gate["holes"][zb]["acceptance"]["H"]
        assert abs(ha[0] - hb[0]) < 5e-3 and abs(ha[1] - hb[1]) < 5e-3, (za, zb, ha, hb)
    print("acceptance(结构带) H 区间表(供 T7):")
    for zh in sorted(gate["holes"]):
        h = gate["holes"][zh]
        acc = h["acceptance"]
        if acc["feasible"]:
            print("  %s  H=[%.3f, %.3f]  H_ref=%.3f  band=+%.2f  n_r5a=%d"
                  % (zh, acc["H"][0], acc["H"][1], acc["H_ref"],
                     acc["band_t"], h["n_r5a"]))
        else:
            print("  %s  H=无可行区间(sweep=[%.3g, %.3g])  H_ref=%.3f  "
                  "band=+%.2f  n_r5a=%d —— 停车线"
                  % (zh, acc["sweep"][0], acc["sweep"][1], acc["H_ref"],
                     acc["band_t"], h["n_r5a"]))

    # 旧口径 A/B 负控: 截面不加厚(带石当裸环外荷载=修正前模型) → 中央 5 孔
    # 全翻假 —— 结构带假设 load-bearing, 且否证"数据天然过"的恒真风险
    old_gate = None
    _saved = G3.LOCK_BAND_M
    try:
        G3.LOCK_BAND_M = 0.0
        old_gate = G3.stress_gate(led, r5a=r5a)
    finally:
        G3.LOCK_BAND_M = _saved
    old_infra = sorted(zh for zh in old_gate["holes"]
                       if not old_gate["holes"][zh]["acceptance"]["feasible"])
    # [审查 W3] 旧口径 A/B 负控恢复精确集钉值(原为 ⊇ 超集弱断言, 在
    # infeasible=[] 下退化为"old_infra 非空"近恒真)。出货口径(字面杠杆)
    # LOCK_BAND_M=0 下不可行集实测 = {07..11}; 50/50 前身模型下为 {06..12}
    # 7 孔(出口审查实测) —— 差异来自杠杆带变宽, 随口径重测并在此钉死。
    # [拱线族返工清债 2026-10-08] {07..11}→{07,08,10,11}: 新实测——圆弧族
    # 中央孔(ARCH09)旧口径下转可行(跨内分支比两圆心弧高, 杠杆带内容变),
    assert old_infra == ["ARCH07", "ARCH08", "ARCH10", "ARCH11"], old_infra
    # 带界守恒(0.36m 外肩石不得混入): r5a 集合逐石足印径向距 ≤ 0.35
    import sequencer as SQ
    assert G3.LOCK_BAND_M == SQ.LOCK_BAND_M == 0.35
    by_id = {s["id"]: s for s in led["stones"]}
    for zh, ids in r5a.items():
        ai = int(zh[4:]) - 1
        xc = GM.arch_center_x(ai)
        springer = GM.arch_springer_z(ai)
        a2 = GM.SPANS[ai] / 2.0
        b2 = GM.arch_rise(ai)
        rt = gate["holes"][zh]["acceptance"]["ring_t"]
        for sid in ids:
            st = by_id[sid]
            xm, zb, _z = SQ._stone_xz(st)
            r = F.arch_signed_r(xm, zb, xc, springer, a2, b2) - rt
            assert r <= G3.LOCK_BAND_M + 1e-9, (sid, r)

    # 体积单源互证(抽 1 石): 散度质心体积 == export_print.signed_volume
    ring08 = [s for s in led["stones"]
              if G3.stone_role(s["id"]) == "RING"
              and s["id"].startswith("ARCH08.")]
    v_sv = G3._ring_volume(ring08[0])
    v_mc, _cx, _cz = G3._mesh_centroid(*G3._ring_mesh(ring08[0]))
    assert v_mc == pytest.approx(v_sv, rel=1e-9)

    # 停车线解除: ③正常返回口径下 17/17(T6b 成果不回退)。
    # [P2-T7] ④gate_imbalance 起新停车线: 真账卸架序(逐孔串行 [工程推断·
    #  非史料]) 在首轮包络口径下超阈 → run_g3 raise
    #  G3_DECENTER_ORDER_CONFLICT(排程冲突, 报告挂异常, 演进见
    #  p2-task-7-report.md §8/§9); 本测只钉③两门数据
    # 不受④影响(报告三节齐, gate_stress/gate_dag ok 照旧断言)。
    try:
        rep = G3.run_g3(seqdoc["events"], led, in_void=_excl_in_void(),
                        rbo_ids=[], r5a=r5a)
    except G3.G3_DECENTER_ORDER_CONFLICT as exc:
        rep = exc.report
    assert rep["gate_stress"]["ok"] and rep["gate_dag"]["ok"]
    assert "gate_imbalance" in rep

    # 纯消融负控(审查 W3): 带界置 0(_crown_wedge→None, 冠楔分摊整体
    # 消融) —— 荷载位置/权重/截面/判据完全不动, 只摘掉"带内分摊"这一
    # 个语义 → A08-11 恰 4 孔翻红(=审查实测 crown_hw=0 的 E 态, 与
    # 35e37cd commit 记录吻合) —— 分摊 load-bearing, 且红可归因于分摊
    # 而非荷载位置(旧负控 x=xc+0.6 同时挪位置+0.5m 伪带宽, 已废)。
    _saved_wedge = G3._crown_wedge
    try:
        G3._crown_wedge = lambda stones, xc: None
        abl_gate = G3.stress_gate(led, r5a=r5a)
    finally:
        G3._crown_wedge = _saved_wedge
    abl_infra = sorted(zh for zh, h in abl_gate["holes"].items()
                       if not h["acceptance"]["feasible"])
    assert abl_infra == ["ARCH08", "ARCH09", "ARCH10",
                         "ARCH11"], abl_infra

    # 压力线图: 中央孔 A08(结构带内 FEASIBLE) + 端孔 A01(FEASIBLE)
    for zh, name in (("ARCH08", "g3_thrust_A08.png"),
                     ("ARCH01", "g3_thrust_A01.png")):
        path = os.path.join(_CTRL, name)
        G3.plot_hole_pressure(gate["holes"][zh], led, zh, path)
        assert os.path.exists(path) and os.path.getsize(path) > 1000


@pytest.mark.skipif(not all(os.path.exists(p) for p in _NEED),
                    reason="out/sequence.json+ledger_sequenced.json 不在盘上")
def test_neg3_neg5_r5a_degenerate_and_stop_line():
    """③裸环退化路径: R5a 清空 → acceptance≡robustness(无胶结带孔截面
    不加厚, 停车线不误触); ⑤注入超重带石(自重入块链 W_k) → run_g3
    raise G3_FROZEN_GEOMETRY_CONFLICT 且点名注入孔(停车线真触发 ——
    截面自重侧的牙; P2-T6 结构带模型下 r5a 仍承载重量项)。"""
    led, seqdoc = _real_chain()

    # ③ R5a 清空: acceptance 退化为裸环, 与 robustness 全等, 不 raise
    gate = G3.stress_gate(led, r5a={zh: [] for zh in
                                    ("ARCH%02d" % i for i in range(1, 18))})
    for zh in ("ARCH01", "ARCH08"):
        h = gate["holes"][zh]
        assert h["acceptance"]["feasible"] == h["robustness"]["feasible"]
        assert h["acceptance"]["band_t"] == 0.0
        assert h["acceptance"]["H"] == pytest.approx(h["robustness"]["H"],
                                                     abs=1e-12)
    assert gate["ok"], "裸环退化 case 误触停车线"

    # ⑤ 停车线真触发: ARCH01(当前 feasible)注入一块超重带石 → 不可行
    tam = copy.deepcopy(led)
    fake = dict(next(s for s in tam["stones"]
                     if s["id"] == "ARCH01.EAST.BACK.C00.B00"))
    fake["id"] = "ARCH01.EAST.BACK.C99.B99"
    fake["params"] = dict(fake["params"], w=50.0, h=50.0, d=50.0)
    tam["stones"].append(fake)
    r5a = G3.load_r5a_shoulders()
    r5a["ARCH01"] = r5a.get("ARCH01", []) + [fake["id"]]
    with pytest.raises(G3.G3_FROZEN_GEOMETRY_CONFLICT, match="ARCH01"):
        G3.run_g3(seqdoc["events"], tam, in_void=_excl_in_void(),
                  rbo_ids=[], r5a=r5a)


@pytest.mark.skipif(not all(os.path.exists(p) for p in _NEED),
                    reason="out/sequence.json+ledger_sequenced.json 不在盘上")
def test_neg6_thin_ring_stop_line_and_band_widening_helps():
    """⑥停车线的冻结几何牙(合成薄环): 环带薄到裸环即不可行 → run_g3
    raise 点名该孔(不依赖注入, 真"冻结几何冲突"); 同一账把截面加厚到
    结构带(ring_t+0.35) → 转 feasible —— 方向自证非恒红。"""
    led, seqdoc = _real_chain()
    tam = copy.deepcopy(led)
    n = 0
    for s in tam["stones"]:
        if G3.stone_role(s["id"]) == "RING" and s["id"].startswith("ARCH01."):
            s["params"] = dict(s["params"], ring_t=0.02)
            n += 1
    assert n >= 4, "前提失效: ARCH01 环石数异常"
    empty_r5a = {zh: [] for zh in
                 ("ARCH%02d" % i for i in range(1, 18))}
    with pytest.raises(G3.G3_FROZEN_GEOMETRY_CONFLICT, match="ARCH01"):
        G3.run_g3(seqdoc["events"], tam, in_void=_excl_in_void(),
                  rbo_ids=[], r5a=empty_r5a)
    # 方向自证: 同一薄环账, 有胶结锁固带 → 截面按结构带加厚(ring_t+带宽)
    # → 回到可行域 —— 停车线非恒红, 且带宽与可行性的方向正确
    band_id = next(s["id"] for s in tam["stones"]
                   if G3.stone_role(s["id"]) == "BACK"
                   and s["id"].startswith("ARCH01."))
    _saved = G3.LOCK_BAND_M
    try:
        G3.LOCK_BAND_M = 2.0     # 薄环 + 足量结构带 → 截面加厚回可行域
        gate = G3.stress_gate(tam, r5a={"ARCH01": [band_id]})
    finally:
        G3.LOCK_BAND_M = _saved
    acc = gate["holes"]["ARCH01"]["acceptance"]
    assert acc["band_t"] == pytest.approx(2.0) and acc["feasible"], acc


# ---------------------------------------------------------------------------
# 审查修复轮(2026-10-07)钉值: 冠楔半宽派生(W2) + sha sidecar(W5)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not all(os.path.exists(p) for p in _NEED),
                    reason="out/sequence.json+ledger_sequenced.json 不在盘上")
def test_crown_wedge_derivation_pin_and_band_boundary_insensitivity():
    """[审查 W2] 冠楔半宽(带界)派生钉值 + 带界不敏感不变量。

    背景: H 窗口对带界敏感(审查实测 −0.1m 位移 max 2.68 / +0.1m 0.84 /
    ×2 达 6.35≈18%·H_ref), 但派生式此前全仓零测试覆盖 —— 重构可静默
    漂移 §8.3/T7 交接数值而不被拦下。两条钉:
    (1) 逐孔 crown_hw == min(xc−st0, st1−xc)(跨 xc 唯一环块, 全 17 孔,
        abs=1e-12) —— 派生取短半宽=最保守方向, 唯一跨冠块下 max 为空操作;
    (2) 带界 ±0.1m(冠楔两缝外扩/内收, 荷载位置/权重/判据全不动)下
        gate['ok'] is True 不变量 —— 把"结论对带界不敏感"钉成可执行
        事实, 防日后判据漂移式找绿。"""
    led, _seqdoc = _real_chain()
    r5a = G3.load_r5a_shoulders()
    gate = G3.stress_gate(led, r5a=r5a)
    assert gate["ok"], gate["violations"][:3]
    assert sorted(gate["holes"]) == ["ARCH%02d" % i for i in range(1, 18)]
    for zh in sorted(gate["holes"]):
        ring = [s for s in led["stones"]
                if G3.stone_role(s["id"]) == "RING"
                and s["id"].startswith(zh + ".")]
        xc = GM.arch_center_x(int(zh[4:]) - 1)
        straddle = []
        for s in ring:
            st = sorted(float(v) for v in (s["params"]["stations"][:2]))
            if st[0] < xc < st[1]:
                straddle.append((st[0], st[1]))
        # 跨冠缝环块每孔恰 1 块(唯一性本身入钉; 审查实测同)
        assert len(straddle) == 1, (zh, straddle)
        st0, st1 = straddle[0]
        hw = min(xc - st0, st1 - xc)
        acc = gate["holes"][zh]["acceptance"]
        assert acc["crown_wedge"] == [st0, st1], zh
        assert abs(acc["crown_hw"] - hw) <= 1e-12, (zh, acc["crown_hw"], hw)
        assert 0.0 < acc["crown_hw"] < 0.5, (zh, acc["crown_hw"])
    # (2) 带界 ±0.1m: 冠楔两缝外扩/内收 0.1m(内收后跨冠块仍含 xc,
    # crown_hw>0) —— 可行性结论与全门 ok 不变
    orig = G3._crown_wedge
    try:
        for d in (-0.1, 0.1):
            def _perturbed(stones, xc, _d=d):
                w = orig(stones, xc)
                if w is None:
                    return None
                return (w[0] - _d, w[1] + _d,
                        min(xc - (w[0] - _d), (w[1] + _d) - xc))
            G3._crown_wedge = _perturbed
            g2 = G3.stress_gate(led, r5a=r5a)
            assert g2["ok"] is True, (d, g2["violations"][:3])
            assert sorted(zh for zh, h in g2["holes"].items()
                          if not h["acceptance"]["feasible"]) == []
    finally:
        G3._crown_wedge = orig


_SIDE = os.path.join(_HERE, "..", "3d", "refs", "artifact_sha256.txt")

# [P2 终审 BLK-1] sidecar 完备性显式钉: 重锚工件全集合 8 条(新增重锚
# 工件必须 sidecar+本钉同轮扩; 删行/漏登记即红 —— 取代旧 `len>=6` 无牙
# 判据: 实测删两行仍 1 passed)。
_SIDEAR_EXPECTED = frozenset([
    "3d/out/ledger_full.json",
    "3d/out/sequence.json",
    "3d/out/ledger_sequenced.json",
    "3d/core_hash.json",
    "3d/out/print/central_slice/manifest.json",
    "3d/out/print/excluded_ids.json",
    "3d/out/event_ledger.json",
    # [拱线族返工清债 2026-10-08] pace.json 单一节奏源入完备性钉(P3-T8 侧车行
    # 随 sequence 重锚同轮更新; 侧车重建为 9 路径唯一化)
    "3d/out/film/pace.json",
    "3d/out/narration_beats.md",
    # P3-T8(2026-10-08): pace.json 单一节奏源入 sidecar(序幕 5s 重生成,
    # sha 随重生成同轮更新; BLK-1: sidecar+本钉同轮扩)
    "3d/out/film/pace.json",
    # P4-T6(2026-10-08): 段包关账五件入 sidecar —— 薄特征审计/段 manifest/
    # 留续清单/施工卡/进度账 init 模板(现行口径 2113=段 1123+留续 990;
    # BLK-1: sidecar+本钉同轮扩; 生成命令链见 sidecar P4-T6 节)
    "3d/out/print/thin_features.json",
    "3d/out/print/section5/manifest.json",
    "3d/out/print/deferred_holes.json",
    "3d/out/print/section5/construction_cards.md",
    "3d/out/print/print_status.json",
])


def _parse_sidecar(path):
    # type: (str) -> List[Tuple[str, str]]
    entries = []
    with open(path, encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            parts = ln.split(None, 1)
            assert len(parts) == 2, ln
            entries.append((parts[0], parts[1].strip()))
    return entries


def _assert_sidecar_set(entries):
    # type: (List[Tuple[str, str]]) -> None
    """记录集 == 钉集合(纯集合判据, clean clone 亦可跑): 删行/漏登记/
    重复登记一律红 —— sidecar 是"哪些工件入库可核"的契约, 不锁清单则
    P3 新工件漏登记永不红(BLK-1)。"""
    paths = [rel for _sha, rel in entries]
    assert len(paths) == len(set(paths)), "sidecar 重复路径: %r" % paths
    assert set(paths) == _SIDEAR_EXPECTED, \
        "sidecar 路径集 != 完备性钉集合(删行/漏登记即红): 差集 %r" \
        % (set(paths) ^ _SIDEAR_EXPECTED,)


def _assert_sidecar_present_and_matching(entries, base):
    # type: (List[Tuple[str, str]], str) -> None
    """在盘工件逐条 fail-loud(B2b 纪律, tests/test_p1_slice.py:439 同族):
    已录路径盘上缺失 = 半重出树, 红(不许静默 continue); 记录值 ==
    sha256 盘上实算, 任何一条不符红。"""
    missing = [rel for _sha, rel in entries
               if not os.path.exists(os.path.normpath(
                   os.path.join(base, rel)))]
    assert not missing, (
        "sidecar 已录工件盘上缺失(fail-loud, 不许静默跳过; 全缺=clean "
        "clone 由上层 skip): %r" % (missing,))
    for sha, rel in entries:
        h = hashlib.sha256()
        with open(os.path.normpath(os.path.join(base, rel)), "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        assert h.hexdigest() == sha, \
            "%s: sidecar=%s 盘上=%s" % (rel, sha, h.hexdigest())


def test_artifact_sha256_sidecar_matches_disk():
    """[审查 W5→P2 终审 BLK-1] tracked sha sidecar: 完备性 + 逐条一致。

    两段牙(旧判据 len>=6 + 缺失 continue 已废): (1) 记录集合显式钉 8
    路径(删一行/漏登记即红); (2) 已录工件盘上缺失即红 + 记录值==盘上
    实算。全 8 件都不在盘 = clean clone(untracked 大工件不入库) →
    skip, 按各生成命令链重出后可核。变异负控见
    test_sidecar_completeness_mutation_red(tmp 副本, 真账零触碰)。"""
    assert os.path.exists(_SIDE), "sidecar 不在盘上(须随仓库交付)"
    entries = _parse_sidecar(_SIDE)
    _assert_sidecar_set(entries)
    base = os.path.join(_HERE, "..")
    on_disk = [rel for _sha, rel in entries
               if os.path.exists(os.path.normpath(os.path.join(base, rel)))]
    if not on_disk:
        pytest.skip("sidecar 所列工件均不在盘上(clean clone); "
                    "按 sidecar 生成命令链重出后可核")
    _assert_sidecar_present_and_matching(entries, base)


def test_sidecar_completeness_mutation_red(tmp_path):
    """[P2 终审 BLK-1 变异负控] sidecar 副本删一行 → 完备性判据必红
    (判据非恒真自证; tmp 副本验证, tracked sidecar 零触碰)。"""
    assert os.path.exists(_SIDE), "sidecar 不在盘上(须随仓库交付)"
    entries = _parse_sidecar(_SIDE)
    _assert_sidecar_set(entries)          # 完整记录集: 绿
    mutilated = entries[:-1]              # 删末一条(event_ledger/beats 族)
    assert len(mutilated) == len(entries) - 1
    with pytest.raises(AssertionError, match="钉集合|删行|漏登记"):
        _assert_sidecar_set(mutilated)


# ---------------------------------------------------------------------------
# [P2 终审 W-6] IMPOST 恒 0 重静默漏计 → _stone_weight fail-loud 哨兵
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not all(os.path.exists(p) for p in _NEED),
                    reason="out/sequence.json+ledger_sequenced.json 不在盘上")
def test_impost_never_in_load_integral_and_weight_fails_loud():
    """IMPOST(492 块, 无 w/h/d 断面键)不在承重积分集(③环块链/④孔顶
    荷载=RING ∪ R5a 两消费面), 且 _stone_weight 对无断面键石 raise
    (fail-loud 取代静默 0 —— 静默 0 曾使 IMPOST 恒 0 重且两实现同式
    互证不报警; 治本=票3 计重口径)。角色集漂移即红。"""
    led = L.load_ledger(_LEDSEQ)
    impost = next(s for s in led["stones"]
                  if G3.stone_role(s["id"]) == "IMPOST")
    assert "d" not in (impost.get("params") or {}), \
        "前提失效: IMPOST 已补 d 键, 本钉应随票3 同轮退役"
    with pytest.raises(ValueError, match="w/h/d"):
        G3._stone_weight(impost)
    r5a = G3.load_r5a_shoulders()
    roles = {G3.stone_role(sid) for ids in r5a.values() for sid in ids}
    assert "IMPOST" not in roles, \
        "R5a 积分集混入 IMPOST: %r" % sorted(roles)
    # ③另一消费面=ring 构造(stone_role==RING 过滤)与④ _hole_top_loads
    # (RING ∪ r5a)同单源, 由 _stone_weight 的 raise 兜底: 误喂 IMPOST
    # 必响, 不再有静默 0 路径。
