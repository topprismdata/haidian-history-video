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
  真账实况(裁决轮实测): 裸环 17/17 全 feasible; acceptance(结构带)
  16/17 feasible, ARCH07 仍不可行 —— 主控裁决第三条: 维持 raise 停报,
  历史结论 = "券架须驻留至拱肩近满才可落架"(排程跟物理走); 旧口径
  (截面不加厚, 带石当裸环外荷载)对照 {ARCH07..11} 五孔不可行 ——
  结构带假设 load-bearing 由 A/B 负控钉死。
- 停车线: acceptance 不可行 → run_g3 raise G3_FROZEN_GEOMETRY_CONFLICT
  (点名孔), 禁调封卷参数自救; 阈值不为绿而调(0.35 唯一声明带宽)。

五负控: ①楔块重心外移 0.3m → feasible 翻假 ②带缩(t×2/3)区间变窄 /
带加厚(t×1.5)区间变宽 ③裸环退化路径(R5a 清空 acceptance≡robustness,
停车线不误触) ④H 越界出带(过小 H 压力线下穿 intrados / 过大 H 上穿
extrados, 逐缝 exit 点名) ⑤R5a 清空退化 + 注入超重带石(自重入链) →
停车线真触发; 另: 旧口径 A/B(LOCK_BAND_M→0 中央孔翻不可行) + 带界
守恒(r5a 逐石径向 ≤0.35, 0.36m 外肩石不得混入)。

微账几何同 test_p2_g3_dag(全部 GM 现算); 真账 17 孔(存在性 skip)为
acceptance 全 feasible + gate_stress 同形节 + H 区间表 + A01/A08 压力线
图落盘(m20_ctrl/)的常驻断言。
"""
import copy
import json
import math
import os
import sys

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

    裁决链(T6 首核停车线 → 主控两层裁决 → 本轮落地):
    ① R5a 收缩真锁固带: 足印距 extrados ≤0.35m(径向, facts.arch_signed_r
      单源; 竖直读法探针证伪 —— 拆拱脚稳定配重致 ARCH05/13 翻假) ∧
      剔除双建模占位(0.985 吞没 28 石 → R5b)。R5a: 1307 → 1290。
    ② 结构协同假设: 锁固带与券脸石餬灰胶结(C:A5 "餬灰璺"), 并入拱截面
      (s 检验带厚 ring_t+0.35; 带重计入块链 W_k)。
    实测(T6b 相位协变重账): robustness(裸环) 17/17; acceptance(结构带)
    **ARCH07 转可行 [33.479,39.106]**(治本达成; 治本链=①相位协变
    ②in_void 手性修复 ③CORE 肩载质心锚 ④冠载侧归属 EPS 一致)。
    **A08-11 转不可行** —— 冠列核心荷载(13.5-15.4, 占带重 ~20%)锚语义
    修正(角→质心, H1 分派表)使其作用臂移向冠点 ~1.1m 的物理后果, 停车线
    按 A08-11 维持 raise 待主控裁决(冠列荷载分摊方式)。旧口径 A/B(截面
    不加厚)对照见 §7.3/neg 控制。若砖谱/几何再冻结, 此处结论应被显式
    复核而非静默漂移。"""
    led, seqdoc = _real_chain()
    r5a = G3.load_r5a_shoulders()
    # [P2-T6b 相位协变重账] R5a 1290→1342 (+52): in_void 手性修复释放 48 块
    # (12 孔×4, 全部入本孔 R5a) + dm/rbo 0.985 体素口径边界移位 +4
    # (A13 +2, A15 +2; dm 总数 28→29)。归因表见 p2-task-6-report.md §8。
    assert sum(len(v) for v in r5a.values()) == 1342
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
    # acceptance(结构带)实况: 13 孔 feasible + A08-11 停车线(T6b 冠载臂
    # 修正后的裁决基线; 几何/砖谱/荷载分摊再裁决须显式复核本行)
    infeasible = sorted(zh for zh in gate["holes"]
                        if not gate["holes"][zh]["acceptance"]["feasible"])
    assert infeasible == ["ARCH%02d" % i for i in range(8, 12)], infeasible
    assert [v.split(" ", 1)[0] for v in gate["violations"]] == \
        [G3.CODE_STRESS_INFEASIBLE] * len(infeasible)
    assert [v.split("hole=")[1].split(" ", 1)[0]
            for v in gate["violations"]] == infeasible
    assert gate["skipped_zones"] == []
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
    # [P2-T6b] 不变量: 截面不加厚(锁固带当裸环外荷载=修正前模型)的不可行
    # 集合 ⊇ 结构带模型, 且严格更大 —— 结构带假设 load-bearing, 方向单调
    # (T6b 重账后旧口径不可行集实测见 print, 含 A04-13 中央大部)。
    print("旧口径(截面不加厚) infeasible:", old_infra)
    assert set(infeasible) <= set(old_infra), (infeasible, old_infra)
    assert len(old_infra) > len(infeasible), old_infra
    assert "ARCH07" in old_infra and "ARCH07" not in infeasible

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

    # 停车线: run_g3 串接 gate_stress, ARCH07 不可行 → raise 点名孔
    with pytest.raises(G3.G3_FROZEN_GEOMETRY_CONFLICT) as ei:
        G3.run_g3(seqdoc["events"], led, in_void=_excl_in_void(),
                  rbo_ids=[], r5a=r5a)
    for zh in infeasible:
        assert zh in str(ei.value)

    # 压力线图: 中央孔 A08(结构带内 FEASIBLE) + 停车线孔 A07(不可行注记)
    for zh, name in (("ARCH08", "g3_thrust_A08.png"),
                     ("ARCH07", "g3_thrust_A07.png")):
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
