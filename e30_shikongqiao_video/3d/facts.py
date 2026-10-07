# -*- coding: utf-8 -*-
"""E30 十七孔桥 尺寸事实清单（单一来源）。

等级: 测绘 > 档案 > 官方 > 图像推导 > 工作值。
"待核"只允许存在于 RESEARCH_DONE=False 期间。
冻结(M2.5)只锁非[工作值]条目; 改锁死条目必须写 3d/refs/body_changelog.md 并重跑本体判据。
禁令: 未标定照片不得产生绝对米制尺寸; 超分(ESRGAN)结果禁止进计量链; GPT 聊天记录不算来源。
Z 基准: Z=0 = 常水位水面(建模约定)。

M0(2026-10-04, Task 2): 完成 web 检索回填, RESEARCH_DONE=True。
逐项命中 URL/原文数字/未查到理由/冲突 C1-C5 见 3d/refs/FACTS.md。
无公开测绘值的条目按约定保留 [工作值] 等级(出处写"无文献, 沿用现脚本值"),
不进 M2.5 冻结范围。检索结论: 官方只公布 桥长/上下宽/高/孔数 四组宏观值;
逐孔净跨/墩厚/纵坡/桥台无公开测绘值, 待 T2b 闭合归因与 T2c 方法论文献。
"""

# --- 研究轮旗标: M0 完成后置 True ---
RESEARCH_DONE = True

# --- 全局 ---
BRIDGE_LEN = 150.0        # [官方散文] 北京青年报(中新网转载2025-12-09): "长150米"; visitbeijing 同值; URL 见 FACTS.md
N_SPAN = 17               # [官方实测] 同篇: "17个拱形桥洞"; visitbeijing: "桥由17个桥洞组成"

# --- 桥面 ---
# [M19 冬照重标定 2026-10-06] 七审 M12 用 side_elev_6794.jpg(枯湖水位, 干湖床当水线)
# 标定 → 全纵剖系统偏高。冬照 winter_20201221160537.jpg(结冰=常水位, D810 38mm,
# fpx=7501, d_center≈112m/d_east≈60-66m, 竖直量不受俯仰透视影响)实测:
# 端部桥面 2.1-2.3m / 中央行走面 7.3m / 中央拱冠(内缘) 5.9m / camber 4.8-5.1m。
# M19 Δz 扫描(0/-1.0/-1.4/-1.8, montage m19_dz_scan.png)证明单参数平移压不住
# (camber 残差 0.80 为 Δ 不变量, 中央桥面最优仍 -0.55) → 按 brief 步骤3 重拟:
# apex 7.2±0.2 取 7.30(冬照中央行走面直读), end 2.2±0.2 取 2.20(冬照东端直读)。
DECK_Z_TOP = 7.30         # [图像推导] M19 冬照重标定: 中央行走面 7.3±0.3(冬照直读); 旧7.75承枯湖基准作废
DECK_Z_END = 2.20         # [图像推导] M19 冬照重标定: 东端桥面 2.1-2.3 取中 2.20; 旧3.60承枯湖基准作废
DECK_UP_W = 6.56          # [官方散文] 北京青年报2025-12-09: "桥面上宽6.56米"(公园管理中心口径; 2019原始专题页未检回, 见FACTS.md)
DECK_DOWN_W = 14.6        # [官方散文] 北京青年报2025-12-09: "桥面下宽14.6米"
PUBLISHED_GENERAL_WIDTH = 8.0   # [官方散文] 公园管理中心2023-12-01: "桥身宽8米"; 与 DECK_UP_W 口径冲突(C2)
PUBLISHED_BRIDGE_HEIGHT = 7.0   # [官方散文] 中新网2025-12-09: "高7米"; 官方侧对7米测点表述互异(桥高 vs 桥洞最高点, C3), 禁止映射 DECK_Z_TOP

# --- 券洞 ---
ARCH_RATIO = 0.50         # [图像推导] 近正面原始照目视近正对孔宽高比≈1.00; ESRGAN 版测量已退出计量链, 待测绘升级
# [M19 冬照重标定] 拱肩厚(冠内缘→桥面)非常数: 冬照中央 1.4±0.3 / 端部 0.4-0.6(取 0.5±0.2)。
# 旧恒定 1.00 承枯湖基准; 端部恒 1.0 曾使端孔拱肩墙高一倍(0.97 vs 真照 0.5)。
SPANDREL_C = 1.40         # [图像推导] M19 冬照重标定: 中央拱肩 7.30-5.90=1.40
SPANDREL_E = 0.50         # [图像推导] M19 冬照重标定: 端孔拱肩 2.20-1.70=0.50(端冠 1.7 冬照直读)
SPRINGER = 1.14           # [工作值] M19 导出值·非独立事实(沿用现脚本兼容锚): = DECK_Z_TOP-SPANDREL_C-rise_ratio(8)*8.50
                          # = 7.30-1.40-0.56*8.50; 冬照中央起拱线 1.4±0.3, 残差 -0.26 在 ±0.35 门内。
                          # 沿用现脚本常量仅为兼容旧诊断工具(report/diag/verify), 生成器一律走 arch_springer_z(i)。
                          # [M19] MET_SPRINGER 新增"声明=导出"恒等校验, 单改本常量即本体自相矛盾。
RING_T = 0.40             # [工作值] 无文献, 沿用现脚本值(M0 无命中)。 # STALE: 与账目 params.ring_t=0.54 分叉, 端孔 extrados 穿桥面 4-11cm 属真缺陷, 债务票 M20b 标定 ring_t(i) 后统一
                          # [2026-10-07 P2-T2 修复轮 D2 停车线主控裁决] 曾尝试对齐 0.54:
                          # 端孔(孔1/17) MET_RING_FIT 即红(拱背 2.77 > 桥面 2.73, 判据等价式
                          # RING_T > spandrel(i), 端 spandrel=0.50) —— 0.40 下的绿灯测的是
                          # 虚构几何, 真缺陷如实挂账 M20b; 本体 build 链不消费本值(几何零变化),
                          # 券石/券架各自走 masonry.RING_T=0.54 / 石账 params.ring_t 现算。
SPAN_DISTINCT = [4.50, 4.90, 5.40, 5.90, 6.40, 6.90, 7.40, 8.00, 8.50]  # [工作值] 9个完整净跨(对称展开17孔), 总水路107.3m+墩台≈150m 自洽; 无公开逐孔测绘值(M0 检索无命中, 官方仅定性"正中一孔最大两侧依次渐小"), 沿用现脚本值

# --- 墩与桥台 ---
PIER_W = 2.50             # [工作值] 无文献, 沿用现脚本值(原脚本[待核]注释 M0 已归一, 见 FACTS.md C5)
PIER_MAIN_W = 2.80        # [工作值] 无文献, 沿用现脚本值(C5 归一)
PIER_FOUND_W = 3.10       # [工作值] 无文献, 沿用现脚本值(C5 归一)
PIER_MAIN_W_C = 2.90      # [工作值] 无文献, 沿用现脚本值(C5 归一)
PIER_FOUND_W_C = 3.20     # [工作值] 无文献, 沿用现脚本值(C5 归一)
BRIDGE_ABUT = 1.35         # [工作值] 现脚本生效值; 无文献; T2b 闭合归因后定稿(候选: 2.00 GPT设计 / 2.60 闭合推导; 原登记[待核]已按实况改[工作值])

# --- 六审四刀#2: 内墩宽度纵剖面(GPT 六审: 大孔间桥墩偏宽厚约10%, 真桥中央修长向两端渐厚实) ---
# 中央内墩(i=8,9)收窄 -9.2% -> 2.27m; 端内墩(i=1,16)渐宽 +9.2% -> 2.73m;
# 逐墩线性内插(mm 取整), 严格轴对称(w[i] == w[17-i])。
# 硬几何约束(桥长守恒): 线性剖面的可证恒等 —— 每个对称对 w[i]+w[17-i] == PIER_W_C+PIER_W_E
# == 2*PIER_W, 故 16 内墩之和恒等于 (N_SPAN-1)*PIER_W = 40.0m, 端台维持 BRIDGE_ABUT=1.35,
# 总桥长严格守恒 BRIDGE_LEN = 150.0(107.3 + 40.0 + 2*1.35), MET_CLOSURE 闭合不动。
# PIER_W 保留为剖面均值/旧引用锚; 生成器消费 PIER_W_INT 表, 不再各自携带公式。
PIER_W_C = 2.17           # [工作值] 七审P0-2: 中央内墩宽(i=8,9) 六审-9.2%后再-4.4%; 无文献
PIER_W_E = 2.83           # [工作值] 七审P0-2: 端内墩宽, 守恒对 C+E=2*PIER_W=5.0(向两头重新变重); 无文献
PIER_W_INT = [2.830, 2.736, 2.641, 2.547, 2.453, 2.359, 2.264, 2.170,  # [工作值] i=1..16 逐墩线性内插(mm 取整), 严格轴对称; 无文献
              2.170, 2.264, 2.359, 2.453, 2.547, 2.641, 2.736, 2.830]  # 半表和=20.0(4对×5.0)精确


# --- 六审四刀#1: 矢跨比剖面 + 两圆心尖拱纯数学(单一数据源) ---
# 0.61 版中央 cusp 角 25°(GPT: 读成哥特), 收到 0.56 后 e/a=0.127、cusp 13°
# —— "圆弧主导+轻微收尖"。soft-min 冠钝化试验已废(e=0 端孔两弧全等时整弧
# 均匀沉 s*ln2, 是缩水不是圆角)。bridge_geom2/qa_bridge/masonry 消费同一函数。
import math as _math
RISE_C = 0.56             # [图像推导] 六审标定: 中央孔矢跨比(与 winter/ovf 侧视对照定)
                          # [M19] 冬照中央冠5.9/起拱1.4 → 隐含 0.53±0.08, 覆盖 0.56(残差0.03)
                          # → 冻结不动; 改之须同步 ARCH_RATIO_TARGET 判据。
RISE_E = 0.32             # [图像推导] M19 冬照重标定: 端孔矢跨比: 端冠1.7 & 起拱近水(≥0.15 硬约束)
                          # → rise ≤ ~1.45/4.50 → 0.32±0.05(旧 0.46 使端起拱线
                          # = 1.70-2.07 = -0.37 没入水面, 违反 springer≥0.15 硬约束)
SPRINGER_WATER_MIN = 0.15  # [工作值] 起拱线水上硬下限(m, 常水位 z=0 基准), 无文献(冬照标定):
                           # M19 RISE_E 重标定所依据的"springer≥0.15 硬约束"升格为判据阈值;
                           # MET_SPRINGER 消费 —— deck 相对判据按构造平移不变, 全局 Z 漂移
                           # (重演 M12 枯湖基准事故)由本条唯一绝对判据抓。
# [七审P1-1] 冠钝化复活, 语义修正: 混合尺度 s 与 cusp 强度 e 成正比(角点局部!)。
# 上轮 soft-min 废除的原因是 s∝b 时 e=0 端孔(两弧全等)整弧均匀沉 s*ln2 ——
# 那是"缩高"不是"圆角"。s=K*e 则 e=0→s=0→精确回到 min, 钝化只发生在两弧
# 真实相交的角域(冠顶最后 ~s 弧长), 矢高/肩点零污染。目标 cusp 13°->~9°。
CROWN_BLUNT_K = 0.40      # [工作值] 七审标定: s=K*e; 0=纯尖角; 无文献
# 带宽封顶: log-sum-exp 过渡带 ~±3s, K*e 在中央孔给到 ±0.15a(15% 弧长, 过宽,
# 会啃肩线)。七审要求"只处理冠顶最后 3-5% 弧长"→ s<=0.02a。
CROWN_BLUNT_CAP = 0.020   # [工作值] 钝化带宽封顶 s<=CAP*a; 七审"只处理冠顶最后 3-5% 弧长"; 无文献


def rise_ratio(i):
    """第 i 孔矢跨比(0-based): 中央 RISE_C 线性过渡到端 RISE_E, 严格对称。"""
    u = abs(2 * i - (N_SPAN - 1)) / (N_SPAN - 1)
    return RISE_C + (RISE_E - RISE_C) * u


def spandrel(i):
    """[M19] 第 i 孔拱肩厚(冠内缘→桥面行走面): 中央 SPANDREL_C 线性过渡到端
    SPANDREL_E, 与 rise_ratio 同一 u 插值, 严格对称。bridge_geom2.arch_crown_z
    与 qa_bridge MET 判据消费同一函数 —— 无第二套公式可失同步。"""
    u = abs(2 * i - (N_SPAN - 1)) / (N_SPAN - 1)
    return SPANDREL_C + (SPANDREL_E - SPANDREL_C) * u


def arch_e(a, b):
    """尖拱(cusp)圆心偏移 e=(b^2-a^2)/(2a), b>=a 才 >0。b<a 是平拱分支(见下)。
    [M15 修] 旧实现把 b<a 截成 e=0 → 渲染成 rise=a 的半圆, '端孔矮'设计意图
    静默丢失(void/券石/L2 全链一致地错)。正确: b<a 为单心平拱(segmental),
    圆心在起拱线下方 e'=(a^2-b^2)/(2b), R=b+e'。"""
    return max(0.0, (b * b - a * a) / (2.0 * a)) if a > 1e-6 else 0.0


def _arc_pair(x, xc, a, b):
    """拱线两弧在 x 处(高度, 斜率)。b>=a: 两圆心尖拱(左圆心 xc+e 右 xc-e,
    起拱线上)。b<a: 单心平拱, 两"弧"退化为同一圆(圆心 xc, springer-e'),
    高度已含 -e' 平移, 肩点/冠点精确归位。"""
    if b >= a - 1e-12:
        e = arch_e(a, b)
        R = a + e
        out = []
        for cc in (xc + e, xc - e):
            dd = R * R - (x - cc) ** 2
            if dd > 1e-9:
                sq = _math.sqrt(dd)
                out.append((sq, -(x - cc) / sq))
            else:
                out.append((0.0, 0.0))
        return out
    ep = (a * a - b * b) / (2.0 * b) if b > 1e-6 else 0.0
    R = b + ep
    dd = R * R - (x - xc) ** 2
    if dd > 1e-9:
        sq = _math.sqrt(dd)
        return [(sq - ep, -(x - xc) / sq), (sq - ep, -(x - xc) / sq)]
    return [(0.0, 0.0), (0.0, 0.0)]


def blunt_s(a, b):
    """冠钝化混合尺度 s = min(K·e, CAP·a)(七审P1-1: 与 cusp 强度 e 成正比, 角点局部;
    公开给 qa_bridge 判据消费 —— 冠高期望须扣 s·ln2, 单一数据源不许第二套公式)。"""
    return min(CROWN_BLUNT_K * arch_e(a, b), CROWN_BLUNT_CAP * a)


def arch_z(x, xc, springer, a, b):
    """两圆心尖拱 intrados 高度 z(x), x∈[xc-a, xc+a] = 两圆下包络 min,
    冠角用 e 比例 soft-min 局部圆化(s=0 时精确 min)。"""
    (h1, _), (h2, _) = _arc_pair(x, xc, a, b)
    lo, hi = (h1, h2) if h1 <= h2 else (h2, h1)
    s = blunt_s(a, b)
    if s <= 1e-9:
        return springer + lo
    return springer + lo - s * _math.log(1.0 + _math.exp((lo - hi) / s))


def arch_dzdx(x, xc, springer, a, b):
    (h1, d1), (h2, d2) = _arc_pair(x, xc, a, b)
    if h1 <= h2:
        lo, hi, dlo, dhi = h1, h2, d1, d2
    else:
        lo, hi, dlo, dhi = h2, h1, d2, d1
    s = blunt_s(a, b)
    if s <= 1e-9:
        return dlo
    w = _math.exp((lo - hi) / s)
    return (dlo + w * dhi) / (1.0 + w)


def arch_signed_r(x, z, xc, springer, a, b):
    """点(x,z)到 intrados 的有符号径向距离(负=吃进洞口)。
    竖直 z 比较在陡肩段(斜率~9)会把 x 向偏移放大成假侵入; 径向与斜率无关。"""
    if b < a - 1e-12:
        ep = (a * a - b * b) / (2.0 * b) if b > 1e-6 else 0.0
        r = _math.hypot(x - xc, z - (springer - ep)) - (b + ep)
        return r
    e = arch_e(a, b)
    R = a + e
    cc = (xc + e) if x <= xc else (xc - e)
    r = _math.hypot(x - cc, z - springer) - R
    s = blunt_s(a, b)
    if s > 1e-9:
        (h1, d1), (h2, d2) = _arc_pair(x, xc, a, b)
        if h1 <= h2:
            lo, hi, d = h1, h2, d1
        else:
            lo, hi, d = h2, h1, d2
        dip = s * _math.log(1.0 + _math.exp((lo - hi) / s))
        # 曲线在圆下方 dip(径向分量 dip*nz): 圆距离换算到曲线距离须**加回**,
        # 减会双重扣 dip(自查: 设计内缩点被误判侵入 2*dip)。
        r += dip / _math.hypot(d, 1.0)
    return r


def pier_w(i):
    """第 i 内墩宽(1-based, i=1..16)。中央收窄/两端渐厚的唯一数据源,
    bridge_geom2 与 qa_bridge.derive 消费同一张表 —— 规则即数据, 无第二套公式可失同步。"""
    return PIER_W_INT[i - 1]


# 剖面自检(导入即验, 破坏立即暴露): 轴对称 / 端点与中央锚定 / 总宽恒等 40.0
assert len(PIER_W_INT) == N_SPAN - 1, "PIER_W_INT 须恰为 N_SPAN-1 个内墩"
assert all(PIER_W_INT[k] == PIER_W_INT[(N_SPAN - 1) - 1 - k] for k in range(N_SPAN - 1)), \
    "PIER_W_INT 非严格轴对称"
assert PIER_W_INT[0] == PIER_W_E and PIER_W_INT[7] == PIER_W_C \
    and PIER_W_INT[8] == PIER_W_C and PIER_W_INT[15] == PIER_W_E, "PIER_W_INT 锚点失配"
assert abs(PIER_W_C + PIER_W_E - 2 * PIER_W) < 1e-9, "W_C+W_E != 2*PIER_W, 均值恒等被破坏"
assert abs(sum(PIER_W_INT) - (N_SPAN - 1) * PIER_W) < 1e-9, \
    "内墩总宽 != %.1fm, 桥长闭合 BRIDGE_LEN 将被破坏" % ((N_SPAN - 1) * PIER_W)

# --- 判据阈值参数(终审 I12: bridge3d.audit 的可选接口字段; 原硬写在 qa_bridge 判据源码,
#     不进 SOURCES → 框架侧 MET_CLOSURE/MET_ARCH_RATIO 双 skip。落进 facts 后判据消费它们,
#     阈值本身也纳入来源台账治理) ---
CLOSURE_TOL = 0.5         # [工作值] MET_CLOSURE 几何闭合容差(m); 现脚本判据值(原硬写 qa_bridge, 阈值承 T2b 计划稿), 无文献
ARCH_RATIO_TARGET = 0.56  # [工作值] 六审标定: 中央孔矢跨比设计意图(0.61 哥特味收 0.56, cusp 13°); 判据比对 facts.rise_ratio 剖面中心; 现脚本判据值
ARCH_RATIO_TOL = 0.02     # [工作值] 六审标定带宽(现脚本判据值, 无文献); GPT 建议 0.55-0.57 区间

# --- 项目自声明的关系型不变量(bridge3d RELATIONS 机制; 框架不预设形态) ---
# 2026-10-05 终审 I1: 对称性从框架 INV 普适律降级为项目自声明 —— 半侧表+镜像
# 展开只对"对称奇数孔"构型成立(卢沟桥等不对称桥、偶数孔桥必须用全长表)。
# 本项目声明对称形态, 由下面两条关系守护(删除任一条, bridge3d.audit 即红):
#   ①半侧严格递增 = 官方定性"正中一孔最大两侧依次渐小"(防同长乱序, INV 层测不到);
#   ②半侧表形态声明: 2n-1 == N_SPAN(选半侧表即声明对称奇数孔拓扑)。
RELATIONS = {
    "half_side_rises_to_center": lambda f: all(
        a < b for a, b in zip(f.SPAN_DISTINCT, f.SPAN_DISTINCT[1:])),
    "half_side_symmetric_form": lambda f: 2 * len(f.SPAN_DISTINCT) - 1 == f.N_SPAN,
}

SOURCES = {
    "BRIDGE_LEN": ("官方散文", "科普口径无测点无基准, 不得直接映射到几何元素; 见 C9(OSM 实测桥体直线仅134.0m, 差16m 口径未定) 北京青年报/中新网2025-12-09 '长150米' https://www.chinanews.com.cn/cul/2025/12-09/10529704.shtml ; visitbeijing 同值 https://s.visitbeijing.com.cn/attraction/120842"),
    "N_SPAN": ("官方实测", "中新网2025-12-09 '17个拱形桥洞' https://www.chinanews.com.cn/cul/2025/12-09/10529704.shtml ; visitbeijing '桥由17个桥洞组成' https://s.visitbeijing.com.cn/attraction/120842 ; 孔数可逐孔实测点数验证(实拍与渲染均可见), 无测点争议"),
    "DECK_Z_TOP": ("图像推导", "冬照 winter_20201221160537 中央行走面 7.3±0.3(竖直量 d/fpx 法, 人高+墩距双标定 d≈112m); 官方'高7米'测点/基准未注明(C3)禁映射; 旧 7.75 承枯湖水位基准(M12 side_elev_6794)作废"),
    "DECK_Z_END": ("图像推导", "冬照东端桥面 2.1-2.3 取中 2.20(d≈60-66m); 旧 3.60 承枯湖基准作废; camber=5.10 落冬照 4.8-5.1 上缘"),
    "DECK_UP_W": ("官方散文", "科普口径无测点(未注明量于何处/是否含栏板), 不得直接映射; 见 C2(与'宽八米'并存) 北京青年报/中新网2025-12-09 '桥面上宽6.56米'; 公园管理中心2019原始页未检回, 以中新网转载为URL锚"),
    "DECK_DOWN_W": ("官方散文", "科普口径无基准面, 不得直接映射到水线处可见几何; 见 C7(若为水线宽则总长247.5m>>150 算术互斥, 疑为水下基础/含燕翅基底宽) 北京青年报/中新网2025-12-09 '桥面下宽14.6米'(与 DECK_UP_W 同篇, 各自独立引用原文)"),
    "PUBLISHED_GENERAL_WIDTH": ("官方散文", "公园管理中心'科普公园'2023-12-01 '桥身宽8米' https://gygl.beijing.gov.cn/xxgk/xxgk_gyxx/202312/t20231201_3336230.html ; 北京日报引颐和园科普讲师 '桥面宽是8米'; 科普概称无测点, 不得直接映射到几何; 与6.56口径冲突(C2)"),
    "PUBLISHED_BRIDGE_HEIGHT": ("官方散文", "中新网2025-12-09 '高7米' https://www.chinanews.com.cn/cul/2025/12-09/10529704.shtml ; 北京日报引颐和园讲师'桥洞最高点有7米'; 科普公园'桥洞最高达7米' 表述互异(C3); 科普口径无测点无基准面, 禁映射DECK_Z_TOP(C3b: 若指主孔洞内净高则误差3.6%, 优于'桥面顶'口径的10.7%)"),
    "ARCH_RATIO": ("图像推导", "近正面原始照比例假设; ESRGAN退出计量链"),
    "RISE_C": ("图像推导", "中央孔矢跨比 0.56: 六审与 winter/ovf 侧视对照标定; M19 冬照冠5.9/起拱1.4 隐含 0.53±0.08 覆盖 0.56(残差0.03) 故冻结不动; 改之须同步 ARCH_RATIO_TARGET 判据"),
    "CROWN_BLUNT_K": ("工作值", "冠钝化强度 s=K·e(七审P1-1 复活并修正语义: 混合尺度与 cusp 强度 e 成正比, e=0 端孔精确回 min), 七审标定值, 无文献"),
    "CROWN_BLUNT_CAP": ("工作值", "钝化带宽封顶 s<=CAP·a=0.020a(七审要求只处理冠顶最后 3-5% 弧长), 七审标定值, 无文献"),
    "SPRINGER_WATER_MIN": ("工作值", "起拱线水上硬下限 0.15m(常水位 z=0 基准), M19 RISE_E 重标定所依据的 springer>=0.15 硬约束升格为判据阈值(冬照标定), 无文献"),
    "SPRINGER": ("工作值", "= DECK_Z_TOP-SPANDREL_C-rise_ratio(8)*SPAN_MAX = 1.14, 非独立事实; 冬照中央起拱线 1.4±0.3 残差 -0.26; 旧 2.50 承枯湖基准作废"),
    "SPANDREL_C": ("图像推导", "中央拱肩(冠内缘→行走面) 1.4±0.3; 旧恒定 1.00 作废"),
    "SPANDREL_E": ("图像推导", "端孔拱肩 0.4-0.6 取 0.50(端冠 1.7 冬照直读 = 2.20-0.50)"),
    "RISE_E": ("图像推导", "端孔矢跨比 0.32±0.05: 端冠 1.7 + 起拱近水(≥0.15 硬约束) → rise≤1.45/4.50; 旧 0.46 端起拱 -0.37 没水作废; RISE_C 冬照隐含 0.53±0.08 覆盖 0.56 故冻结"),
    "RING_T": ("工作值", "无文献, 沿用现脚本值 0.40(M0 无命中); STALE: 与券石账目 params.ring_t=0.54(七审P0-2)分叉, 端孔 extrados 穿桥面属真缺陷, 债务票 M20b 标定 ring_t(i) 后统一(2026-10-07 D2 停车线主控裁决: 对齐尝试实测端孔 MET_RING_FIT 红, 0.40 绿灯测的是虚构几何, 如实挂账)"),
    "SPAN_DISTINCT": ("工作值", "无公开逐孔测绘值(M0 多轮检索无命中), 沿用现脚本GPT冻结表; 中央孔8.50待测绘升级"),
    "PIER_W": ("工作值", "无文献, 沿用现脚本值; 原脚本[待核]注释已归一(C5); 六审后转为内墩剖面均值锚(16墩总宽恒等式)"),
    "PIER_W_C": ("工作值", "六审四刀#2 整改值(GPT 六审图3拱近景: 大孔间桥墩偏宽厚约10%, 真桥中央修长向两端渐厚实), 无文献; 受均值恒等约束 PIER_W_C+PIER_W_E=2*PIER_W 派生"),
    "PIER_W_E": ("工作值", "六审四刀#2 整改值(端内墩渐厚, 与 PIER_W_C 同一轮整改成对取值), 无文献; 同上恒等约束"),
    "PIER_W_INT": ("工作值", "PIER_W_C..PIER_W_E 逐墩线性内插(mm 取整), 严格轴对称; 16 墩之和恒等 (N_SPAN-1)*PIER_W=40.0 为桥长闭合硬约束, facts 导入断言守护"),
    "PIER_MAIN_W": ("工作值", "无文献, 沿用现脚本值(C5 归一)"),
    "PIER_FOUND_W": ("工作值", "无文献, 沿用现脚本值(C5 归一)"),
    "PIER_MAIN_W_C": ("工作值", "无文献, 沿用现脚本值(C5 归一)"),
    "PIER_FOUND_W_C": ("工作值", "无文献, 沿用现脚本值(C5 归一)"),
    "BRIDGE_ABUT": ("工作值", "现生效1.35, 无文献; T2b闭合归因后定稿; 原登记[待核]按实况改[工作值]"),
    "CLOSURE_TOL": ("工作值", "判据容差, 现脚本值(原硬写在 qa_bridge 判据源码, 终审 I12 落地); 阈值承 T2b 计划稿口径, 无文献"),
    "ARCH_RATIO_TARGET": ("工作值", "尖拱矢跨比设计意图 0.56(0.61 哥特味收 0.56, 六审标定), 现脚本值(原硬写在 qa_bridge 判据源码, 终审 I12 落地); 与 RISE_C 同一设计意图, 判据比对 rise_ratio 剖面中心"),
    "ARCH_RATIO_TOL": ("工作值", "f/l 容差带宽, 现脚本值(原硬写在 qa_bridge 判据源码, 终审 I12 落地); 无文献"),
}
