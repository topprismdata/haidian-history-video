# -*- coding: utf-8 -*-
"""生成器零字面量锁(终审 I9/I10 重构)。

三道闸门:
1) 尺寸白名单(仅 bridge_geom2.py): 白名单外 float 必红; 白名单只准无量纲容差/贯通系数;
   带单位的尺寸一律进 facts/assumptions 以命名常量出现, 不得再写裸字面量。
2) facts 等值锁(bridge_geom2.py 全量严格 + build_scene2.py 按基线豁免表):
   生成器源码出现"与任一 facts 常量相等"的数字字面量(int/float)必红 ——
   无论它是否在白名单里。终审 I10 实测(修复前): 把 0.50 放回白名单 + 生成器注入
   0.50 字面量, 旧版两测全绿 —— 因为旧判据带 `and f not in ALLOW` 逃逸, 其 fail 集
   只是上一条测试的真子集。逃逸已删。
3) int 覆盖(终审 I9): 旧扫描只收 float —— 注入 `= 3`、`= 17`(== facts.N_SPAN)
   全绿。现按 int+float 全收; int/float 数值同键比较(17 命中 N_SPAN, 7 命中 7.0)。

build_scene2.py 的取舍(终审 I9 注): 该文件属表现层(材质/LOD/机位)且不在本批次
可改范围, 存量 5 个与 facts 数值"巧合"的字面量无法在本批清零 → 逐条豁免并留档
(见 SCENE2_BASELINE); 豁免表之外的 facts 等值字面量照红。bridge_geom2.py 零豁免。

⚠ 撞上这条红时的**正确解法 = 外置命名**, 不是改值、不是加白名单(主控 2026-10-05):
   本锁用"数值同一性"代理"语义同一性", 必有巧合误伤 —— 实例: 券洞挖除体的布尔施工
   余量 0.05(bridge_geom2) 与判据容差 facts.ARCH_RATIO_TOL=0.05 语义无关却数值相等。
   范例解法: 把余量命名为 assumptions.VOID_CUT_MARGIN(依据随注释, 生成器改引用名),
   让两个 0.05 各归各位、可分别审计。
   ⛔ 禁止"改一下值让它不撞"—— 余量/尺寸是生效几何值, 改值=动几何=破坏 M2.5 冻结;
   ⛔ 禁止"把该值加回 ALLOW"—— 那是 I10 刚堵上的逃逸(0.50 藏回白名单即假绿的教训)。
"""
import ast
import os

HERE = os.path.join(os.path.dirname(__file__), "..", "3d")

# 白名单治理: 只准加无量纲容差/循环参量; 任何带单位的尺寸一律进 facts/assumptions。
# 0.5 已被移出白名单(调度者 2026-10-04 修正): 它正是 ARCH_RATIO 的值。
# 0.05 已被移出白名单(终审 I12/I10, 2026-10-05): 它与 facts.ARCH_RATIO_TOL 数值巧合,
#   余量本体已命名为 assumptions.VOID_CUT_MARGIN, 生成器不再出现裸字面量。
ALLOW = {
    0.0, 1.0, 2.0, -1.0, 1e-9,
    # ── 以下为实现参数, 逐条说明为何不是文物尺寸 ──
    0.01,  # _assert_deck_correct 桥面自检的断言容差(1cm); 验证用 epsilon, 不进入几何
    0.001,  # __main__ 自检端点包围盒的浮点余量(1mm); 验证用 epsilon, 不进入几何
    0.8,   # 券洞挖除体向下超出 BODY_BOTTOM 的余量(保证布尔切穿桥体底面); 施工余量, 非桥体尺寸
    # 1.4 已被移出白名单(2026-10-06): M19 新增 facts.SPANDREL_C=1.40 后等值锁必撞;
    #   贯通系数本体已命名为 assumptions.VOID_CUT_WIDTH_K, 生成器不再出现裸字面量
    #   (正规出路=外置命名, 同 0.05/VOID_CUT_MARGIN 先例)。
}

# build_scene2.py 基线豁免表(终审 I9, 2026-10-05 逐条核对行内语境):
SCENE2_BASELINE = {
    0.05: "券洞面/细缝采样与布尔余量(约 10 处, 如 `> a + 0.05`/`SPRINGER + 0.05`), "
          "与 ARCH_RATIO_TOL 数值巧合; 判据余量, 非文物尺寸",
    0.4: "桥头异兽前腿位跨度(`xe+sx*0.40`), 与 RING_T 数值巧合(CROWN_BLUNT_K 已随"
         "拱线族返工删除, 2026-10-08); 异兽体量为表现层工作值",
    0.5: "异兽宽 Wd=0.50 与起拱石高 IMP_H=0.50, 与 ARCH_RATIO/CLOSURE_TOL/SPANDREL_E(M19) 数值巧合; 表现层工作值",
    1.35: "异兽体长上限(工作值 1.15-1.35m), 与 BRIDGE_ABUT 数值巧合; 表现层工作值",
    7: "立方体角点索引 (7,6,5,4) 与卷积/抖动参数(约 25 处), 与 PUBLISHED_BRIDGE_HEIGHT "
       "数值巧合; 拓扑索引, 非尺寸",
    # ── 2026-10-06 M19 后新增碰撞, 逐条核对行内语境登记(正规出路之二: 豁免留档) ──
    0.02: "石板带端部 2cm 内缩(L93-94)/离面杂顶清理 y 余量(L597)/砌缝细缝与采样步距"
          "(L389,576), 与 ARCH_RATIO_TOL 数值巧合(CROWN_BLUNT_CAP 已随拱线族返工删除, "
          "2026-10-08); 实现 epsilon, 非文物尺寸",
    0.15: "水线基脚出挑 0.15m 渐灭带(L542-544)/面块色差方差 block_var(L632 等), "
          "与 SPRINGER_WATER_MIN(M19) 数值巧合; 表现层工作值",
    2.8: "桥台系底面 BED_BOTTOM=-2.8(L491, 扫描器丢弃负号), 与 PIER_MAIN_W 数值巧合; "
         "地形标高表现层工作值(低于岸坡全域最低 -2.4, 实义'稳固插入水底')",
    8.0: "低岸纵向渐灭段长 LOW_FADE=8.0(L504), 与 PUBLISHED_GENERAL_WIDTH/SPAN_DISTINCT[7] "
         "数值巧合; 地形表现层工作值(九轮实测)",
    2.5: "培岸带外缘渐灭距离 2.5m(L814×2), 与 PIER_W 数值巧合; 地形表现层工作值(九轮实测)",
}


def _literals(path):
    """文件内全部数字字面量 → ({float: [行号]}, {int: [行号]})。bool 不是数字。"""
    tree = ast.parse(open(os.path.join(HERE, path), encoding="utf-8").read())
    floats, ints = {}, {}
    for nd in ast.walk(tree):
        if isinstance(nd, ast.Constant):
            v = nd.value
            if isinstance(v, bool):
                continue
            if isinstance(v, float):
                floats.setdefault(v, []).append(nd.lineno)
            elif isinstance(v, int):
                ints.setdefault(v, []).append(nd.lineno)
    return floats, ints


def _fact_values():
    """facts 全部数值常量(标量与序列摊平) → {数值: [常量名]}。
    int/float 数值同键(hash 相等): 字面量 17 命中 N_SPAN=17, 字面量 7 命中 7.0。"""
    import sys
    sys.path.insert(0, HERE)
    import facts as F
    vals = {}
    for n in dir(F):
        if n.startswith("_") or n in ("SOURCES", "RESEARCH_DONE"):
            continue
        v = getattr(F, n)
        for x in (v if isinstance(v, (list, tuple)) else (v,)):
            if isinstance(x, (int, float)) and not isinstance(x, bool):
                vals.setdefault(x, []).append(n)
    return vals


def test_geom_no_dimension_literals():
    """白名单闸门(bridge_geom2.py): 白名单外 float 必红。"""
    floats, _ = _literals("bridge_geom2.py")
    bad = sorted(f for f in floats if f not in ALLOW)
    assert not bad, "bridge_geom2.py 出现白名单外字面数: %s" % bad


def test_no_literal_equal_to_any_fact_value():
    """facts 等值锁(终审 I9/I10): 生成器出现与任一 facts 常量相等的数字字面量必红,
    无论是否在白名单(int 亦覆盖)。负控见模块 docstring 的两条修复前实测。"""
    vals = _fact_values()
    bad = []
    for path, baseline in (("bridge_geom2.py", {}), ("build_scene2.py", SCENE2_BASELINE)):
        floats, ints = _literals(path)
        for v, lns in list(floats.items()) + list(ints.items()):
            names = vals.get(v)
            if names and v not in baseline:
                bad.append((path, v, sorted(set(names)), lns[:3]))
    assert not bad, ("生成器出现与 facts 常量相同的字面量"
                     "(应改为引用 facts/assumptions 命名值): %s" % bad)
