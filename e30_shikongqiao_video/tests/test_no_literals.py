# -*- coding: utf-8 -*-
import ast, os

HERE = os.path.join(os.path.dirname(__file__), "..", "3d")
# 白名单治理: 只准加无量纲容差/循环参量; 任何带单位的尺寸一律进 facts。
# 0.5 已被移出白名单(调度者 2026-10-04 修正): 它正是 ARCH_RATIO 的值,
# 留在白名单里等于允许"券形判据的核心数字"以字面量形式藏回生成器而不报错。
ALLOW = {
    0.0, 1.0, 2.0, -1.0, 1e-9,
    # ── 以下为实现参数, 逐条说明为何不是文物尺寸 ──
    0.01,  # _assert_deck_correct 桥面自检的断言容差(1cm); 验证用 epsilon, 不进入几何
    0.001,  # __main__ 自检端点包围盒的浮点余量(1mm); 验证用 epsilon, 不进入几何
    0.8,   # 券洞挖除体向下超出 BODY_BOTTOM 的余量(保证布尔切穿桥体底面); 施工余量, 非桥体尺寸
    0.05,  # 券洞挖除体横向半宽余量(放大到 0.80 会把两侧墙整块切穿, "黑横杠"bug 已实测复现);
           #   布尔贯通余量, 非桥体尺寸
    1.4,   # 券洞挖除体 y 向拉伸宽度 = DECK_DOWN_W*1.40(保证切穿整个桥宽); 贯通系数, 无量纲
}

def _floats(path):
    tree = ast.parse(open(os.path.join(HERE, path), encoding="utf-8").read())
    out = set()
    for nd in ast.walk(tree):
        if isinstance(nd, ast.Constant) and isinstance(nd.value, float):
            out.add(nd.value)
    return out

def test_geom_no_dimension_literals():
    bad = sorted(f for f in _floats("bridge_geom2.py") if f not in ALLOW)
    assert not bad, "bridge_geom2.py 出现白名单外字面数: %s" % bad


# ── 负控制: 这条测试本身会不会恒真? ──
# 若把 0.5 重新放进白名单, ARCH_RATIO 就能以字面量形式藏回生成器而测试全绿。
# 用 facts 的实际值反证: 凡是"恰好等于某个 facts 常量"的字面量, 一律不允许, 无论它在不在白名单。
def test_no_literal_equal_to_any_fact_value():
    import sys
    sys.path.insert(0, HERE)
    import facts as F
    fact_vals = {}
    for n in dir(F):
        if n.startswith("_") or n in ("SOURCES", "RESEARCH_DONE"):
            continue
        v = getattr(F, n)
        if isinstance(v, float):
            fact_vals.setdefault(v, []).append(n)
        elif isinstance(v, (list, tuple)):
            for x in v:
                if isinstance(x, float):
                    fact_vals.setdefault(x, []).append(n)
    bad = []
    for f in _floats("bridge_geom2.py"):
        if f in fact_vals and f not in ALLOW:
            bad.append((f, fact_vals[f]))
    assert not bad, "bridge_geom2.py 出现与 facts 常量相同的字面量(应改为引用 facts): %s" % bad
