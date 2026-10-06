# Task 3: L1 本体比例判据 + 负控制

> 本文件由计划自动抽取，是该任务的**唯一需求来源**，其中数值必须逐字照用。

### Task 3: L1 本体比例判据 + 负控制

**Files:**
- Create: `e30_shikongqiao_video/3d/qa_bridge.py`
- Create: `e30_shikongqiao_video/tests/test_l1_body.py`

**Interfaces:**
- Consumes: facts（Task 1/2）
- Produces: `qa_bridge.check_body(f: module) -> list[tuple[str, str, str]]`（(级别, 判据名, 说明)，级别∈fail/warn/skip/info）；`qa_bridge.derive(f) -> SimpleNamespace`（含 SPANS, PIER_X, deck_z 封装，供判据与后续几何共用）

- [ ] **Step 1: 写 check_body 与 derive（完整实现）**

```python
# -*- coding: utf-8 -*-
"""E30 本体判据 L1(纯数据)。只有 fail 阻塞; skip=未执行不算通过。"""
try:
    from types import SimpleNamespace
except ImportError:
    raise
import math

def derive(f):
    """由 facts 推导 SPANS/PIER_X。递推规则必须与 bridge_geom2 完全一致:
    墩台宽 = BRIDGE_ABUT_TARGET(Task 4 已把 geom 的 BRIDGE_ABUT 回填机制废除断点)。"""
    spans = list(f.SPAN_DISTINCT) + list(reversed(f.SPAN_DISTINCT[:-1]))
    pier_x, acc = [], -f.BRIDGE_LEN / 2.0
    for i in range(f.N_SPAN + 1):
        w = f.BRIDGE_ABUT if i in (0, f.N_SPAN) else f.PIER_W
        pier_x.append(acc + w / 2.0)
        acc += w
        if i < f.N_SPAN:
            acc += spans[i]
    def deck_z(x):
        half = f.BRIDGE_LEN / 2.0
        ax = min(abs(x), half)
        k = (f.DECK_Z_TOP - f.DECK_Z_END) / (half * half)
        return f.DECK_Z_TOP - k * ax * ax
    return SimpleNamespace(SPANS=spans, PIER_X=pier_x, deck_z=deck_z)

def circle_fit_residual(pts):
    """C2/G2 核心增补: 圆拟合残差(证明'是圆', 而非只测 f/l 标量)。
    pts: [(x,z)] 拱腹采样点。返回 max| |P-C| - R | / R。代数拟合(Kasa)即可。"""
    import numpy as np
    A = np.array([[x, z, 1.0] for x, z in pts])
    b = np.array([x * x + z * z for x, z in pts])
    sol, *_ = np.linalg.lstsq(A, b, rcond=None)
    cx, cz = sol[0] / 2.0, sol[1] / 2.0
    r = math.sqrt(sol[2] + cx * cx + cz * cz)
    err = max(abs(math.hypot(x - cx, z - cz) - r) for x, z in pts)
    return err / r, (cx, cz, r)

def check_body(f):
    """三层: INV(拓扑不变量) / MET(度量, 阈值须有依据) / IMP(实现完整性)。"""
    import assumptions as A
    out = []
    def add(lvl, name, msg):
        out.append((lvl, name, msg))
    d = derive(f)
    # ── INV 拓扑不变量 ──
    if f.N_SPAN != 17:
        add("fail", "INV_N_SPAN", "孔数 %d != 17" % f.N_SPAN)
    if len(d.SPANS) != 17:
        add("fail", "INV_SPANS_LEN", "SPANS 长度 %d" % len(d.SPANS))
    else:
        if any(d.SPANS[i] != d.SPANS[16 - i] for i in range(8)):
            add("fail", "INV_SPANS_SYM", "跨序不对称")
        if any(d.SPANS[i] < d.SPANS[i - 1] - 1e-9 for i in range(1, 9)):
            add("fail", "INV_SPANS_MONO", "左半跨序非单调不减")
        if any(d.SPANS[i] < d.SPANS[i + 1] - 1e-9 for i in range(8, 16)):
            add("fail", "INV_SPANS_MONO", "右半跨序非单调增")
    # ── MET 几何闭合(G2 增补: 抓'对称但整体尺度错') ──
    total = sum(d.SPANS) + (f.N_SPAN - 1) * f.PIER_W + 2 * f.BRIDGE_ABUT
    if abs(total - f.BRIDGE_LEN) > 0.5:
        add("fail", "MET_CLOSURE", "几何闭合差 %.2fm: 跨和+墩+台=%.1f != 桥长%.1f (2026-10-04 T3 复核: 16 墩口径下精确闭合, 本判据应恒绿)" % (total - f.BRIDGE_LEN, total, f.BRIDGE_LEN))
    # ── MET 券族: 圆拟合残差(G2: f/l 只是必要条件) ──
    for i in range(17):
        xc = (d.PIER_X[i] + d.PIER_X[i + 1]) / 2.0
        a = d.SPANS[i] / 2.0
        pts = [(xc - a * math.cos(math.pi * k / 20.0),
                f.SPRINGER + a * math.sin(math.pi * k / 20.0)) for k in range(21)]
        rtol, _ = circle_fit_residual(pts)
        if rtol > A.CIRCLE_FIT_RTOL:
            add("fail", "MET_ARCH_FAMILY", "孔%d 圆拟合残差/R=%.4f 超限(非圆弧?)" % (i + 1, rtol))
        # f/l 只留宽幅 sanity(设计意图半圆)
        if abs(f.ARCH_RATIO - 0.50) > 0.05:
            add("fail", "MET_ARCH_RATIO", "f/l=%.3f 偏离半圆设计意图" % f.ARCH_RATIO)
        # MET 结构自洽(G2 修订): 拱背=拱腹+RING_T 须低于桥面, 替代无据的0.30
        crown_i = f.SPRINGER + a
        if crown_i + f.RING_T > d.deck_z(xc) + 1e-9:
            add("fail", "MET_RING_FIT", "孔%d 拱背%.2f 高于桥面%.2f(券圈穿出桥面)" % (i + 1, crown_i + f.RING_T, d.deck_z(xc)))
        if f.SPRINGER >= d.deck_z(xc):
            add("fail", "MET_SPRINGER", "孔%d 起拱线高于桥面" % (i + 1))
    if not (0 < f.DECK_UP_W < f.DECK_DOWN_W):
        add("fail", "MET_TAPER", "顶宽须小于底宽(收分)")
    if f.DECK_Z_TOP <= f.DECK_Z_END:
        add("fail", "MET_DECK_DIR", "桥面必须中央最高(历史事故回归)")
    if f.PIER_W <= 0.2 or f.BRIDGE_ABUT <= 0:
        add("fail", "IMP_DIM", "墩/台尺寸非法")
    return out

- [ ] **Step 2: 写测试（正例 + 每条判据一个破坏用例）**

`e30_shikongqiao_video/tests/test_l1_body.py`：

```python
# -*- coding: utf-8 -*-
import os, sys, importlib, math, types
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "3d"))
import facts, assumptions, qa_bridge

def _mutate(**kw):
    m = types.SimpleNamespace(**{k: getattr(facts, k) for k in dir(facts) if not k.startswith("_")})
    for k, v in kw.items():
        setattr(m, k, v)
    return m

def _fails_on(name, **kw):
    r = qa_bridge.check_body(_mutate(**kw))
    codes = {x[1] for x in r if x[0] == "fail"}
    assert name in codes, "破坏未被抓(%s): %s" % (name, codes)

def test_baseline_green():
    r = qa_bridge.check_body(facts)
    fails = [x for x in r if x[0] == "fail"]
    assert not fails, "基线不应 fail: %s" % fails

def test_circle_fit_synthetic():
    # 真圆: 残差≈0
    pts = [(math.cos(t), math.sin(t)) for t in [math.pi*k/40 for k in range(41)]]
    rtol, _ = qa_bridge.circle_fit_residual(pts)
    assert rtol < 1e-3
    # 三心拱反例(G2): 同 f/l=0.5 但非圆, 残差必须大。
    # 注意: 椭圆(1-0.5x^2)残差仅 0.0025 < 阈值, 抓不到; 尖顶双心拱残差 0.0626 才对
    def _three_center(n=41, pointiness=0.30):
        pts = []
        for k in range(n):
            t = -1.0 + 2.0 * k / (n - 1)
            z = 0.5 * math.sqrt(max(0.0, 1.0 - t * t)) * (1.0 + pointiness * abs(t))
            pts.append((t, z))
        return pts
    rtol3, _ = qa_bridge.circle_fit_residual(_three_center())
    assert rtol3 > 0.05, "尖顶三心拱残差 %.4f 未超 0.05, 判据抓不住非圆券" % rtol3
    # 椭圆必须被放行(它在圆拟合容差内, 不得误杀)
    rtol_e, _ = qa_bridge.circle_fit_residual(
        [(x, math.sqrt(max(0.0, 1 - x * x * 0.5))) for x in [-1 + 2 * k / 40 for k in range(41)]])
    assert rtol_e < 0.01, "椭圆残差 %.4f 过大, 判据过严" % rtol_e

# ── 边界负控(G2 A类: 符号方向证明) ──
def test_boundary_mono():
    r = qa_bridge.check_body(_mutate(SPAN_DISTINCT=[4.5,4.9,5.4,5.9,6.4,6.9,7.4,7.4,8.0]))
    assert not [x for x in r if x[0] == "fail" and x[1].startswith("INV_SPANS_MONO")], "相等应放行(非严格单调)"
    _fails_on("INV_SPANS_MONO", SPAN_DISTINCT=[4.5,4.9,5.4,5.95,5.9,6.4,6.9,7.4,8.0])

# ── 单点破坏(G2 B类: 一孔坏必须全局红) ──
def test_single_arch_break():
    sd = list(facts.SPAN_DISTINCT); sd[3] = sd[3] + 0.4   # 只改左第4孔
    _fails_on("INV_SPANS_SYM", SPAN_DISTINCT=sd)

# ── 对称但尺度错(G2 C类: 关系判据抓不住, 闭合判据必须抓) ──
def test_symmetric_scale_break():
    sd = [x * 1.05 for x in facts.SPAN_DISTINCT]
    _fails_on("MET_CLOSURE", SPAN_DISTINCT=sd)

# ── 全局Z平移(G2 G类: 相对判据全过, datum判据须抓) ──
# 数值校准: 当前基线 RING_FIT 余量最小为孔1/17 的 +0.17m。
# 平移 0.5m 仍在容差内(抓不住, 已实测), 故破坏量取 1.0m 越过最小余量。
def test_global_z_shift_break():
    _fails_on("MET_RING_FIT",
              DECK_Z_TOP=facts.DECK_Z_TOP - 1.0, DECK_Z_END=facts.DECK_Z_END - 1.0)


# ── 边界: 平移量恰在容差内必须放行(证明判据不是恒真的) ──
def test_global_z_shift_within_tolerance_passes():
    r = qa_bridge.check_body(_mutate(DECK_Z_TOP=facts.DECK_Z_TOP - 0.1,
                                     DECK_Z_END=facts.DECK_Z_END - 0.1))
    assert not [x for x in r if x[0] == "fail" and x[1] == "MET_RING_FIT"], \
        "0.1m 平移(小于最小余量0.17m)不应触发 RING_FIT"

# ── 特异性(G2 J类: 无关破坏不应触发无关判据) ──
def test_specificity():
    r = qa_bridge.check_body(_mutate(PIER_MAIN_W=3.3))   # 改非本体字段
    fails = {x[1] for x in r if x[0] == "fail"}
    assert not fails, "无关字段改动不应触发本体判据: %s" % fails
```

> 注：`MET_CLOSURE` 在当前工作值下**预期基线红**（148.8 vs 150，差1.2m）——这是判据要暴露的真矛盾，M0 研究必须归因（调整桥台长为推导值 2.6m，或修正墩宽/跨序），禁止调宽容差迁就。test_baseline_green **不得**再挂 xfail——闭合差已闭环, 基线必须真绿。

**strict=True 是硬要求**：非 strict 的 xfail 会在 T2b 正常修复后静默变成 XPASS 而不报错——那正是本项目反复踩的"判据恒真却全绿"形态。

- [ ] **Step 3: 跑测试（先确认基线绿、破坏全被抓）**

Run: `cd /Volumes/macstudio/video-projects && python3 -m pytest e30_shikongqiao_video/tests/test_l1_body.py -v`
Expected: 全绿，无 xfail（闭合差已闭环）

- [ ] **Step 4: Commit**

```bash
cd /Volumes/macstudio/video-projects
git add e30_shikongqiao_video/3d/qa_bridge.py e30_shikongqiao_video/tests/test_l1_body.py
git commit -m "feat(e30): L1 本体比例判据+7条负控制破坏用例"
```

---

