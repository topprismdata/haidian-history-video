# -*- coding: utf-8 -*-
"""框架级字面量闸门: bridge3d 源码不得携带任何项目数值。

验收口径(比 grep 更严): 用 AST 收集全部数值常量,
  1) 白名单之外一律非法(白名单逐条注释"为什么不是文物尺寸");
  2) 项目孔数一类特征数(如某具体孔数)不得以任何形态出现 ——
     连注释都不需要它(第二个项目的孔数写在第二个项目的 facts 里);
  3) 数值常量不得恰好等于合成 facts 的任何值(防止"借"项目数值)。
"""
import ast
import re
import sys
from os.path import dirname, join, splitext

sys.path.insert(0, dirname(__file__))

import bridge3d                            # noqa: E402
from facts_synth import make_5, make_23    # noqa: E402

PKG_DIR = join(dirname(bridge3d.__file__))

# 白名单: 逐条说明为何不是文物尺寸/项目常数
ALLOWED = {
    0,      # 拓扑零点/比较基准
    1,      # 拓扑计数(单孔, N_SPAN>=1, 索引 +1)
    2,      # 拓扑计数(两端桥台, N_SPAN-1, 索引 -1, 回文折半)
    -1,     # 序列切片(去掉中央孔的镜像展开)
    2.0,    # 除以二(中点/半长); 两端桥台的倍数 —— 全是拓扑量
    1e-9,   # 纯浮点等值容差(实现参数, 非计量阈值)
    # ── 仅 negative_control(破坏用例/报告基础设施), 非判据/非几何 ──
    4,      # 破坏用例 scale4 扰动倍率; 恒真审计的崩溃样本展示上限(报告可读性)
    8,      # 破坏用例 scale8 高倍率扰动(高净空桥 SPRINGER 类破坏, I5 逐判据审计)
    1.05,   # 破坏用例单孔缩放幅度(制造超容差闭合差)
}

# 项目孔数一类"特征整数"禁入: 历史教训来自首项目把孔数写进判据。
# 首项目(E30 石拱桥)的孔数同样禁入 —— 第二个项目的孔数写在第二个项目的 facts 里。
# 此处以占位方式点名: 两个合成项目的孔数(5/23)与 E30 的孔数(17)。
FEATURE_NUMBERS = (5, 17, 23)


def _py_files():
    import os
    return sorted(fn for fn in os.listdir(PKG_DIR) if fn.endswith(".py"))


def _numeric_constants(path):
    tree = ast.parse(open(path, encoding="utf-8").read())
    out = set()
    for nd in ast.walk(tree):
        if isinstance(nd, ast.Constant):
            if isinstance(nd.value, bool):
                continue
            if isinstance(nd.value, (int, float)):
                out.add(nd.value)
    return out


def _synthetic_fact_values():
    vals = set()
    for make in (make_5, make_23):
        f = make()
        for k, v in vars(f).items():
            if k.startswith("_") or k in ("RELATIONS", "SOURCES"):
                continue
            if isinstance(v, bool):
                continue
            if isinstance(v, (int, float)):
                vals.add(v)
            elif isinstance(v, (list, tuple)):
                for x in v:
                    if isinstance(x, (int, float)) and not isinstance(x, bool):
                        vals.add(x)
    return vals


def test_no_feature_number_anywhere_in_package():
    """项目孔数一类特征数不得出现在 bridge3d 源码的任何位置(含注释/文档字符串)。"""
    import os
    for fn in _py_files():
        src = open(os.path.join(PKG_DIR, fn), encoding="utf-8").read()
        hits = re.findall(r"(?<![\w.])%d(?![\w.])" % FEATURE_NUMBERS[0], src) + \
               re.findall(r"(?<![\w.])%d(?![\w.])" % FEATURE_NUMBERS[1], src)
        assert not hits, "%s 出现特征数(判据必须随 facts 走): %d 处" % (fn, len(hits))


def test_all_numeric_constants_are_whitelisted():
    import os
    for fn in _py_files():
        bad = sorted(c for c in _numeric_constants(os.path.join(PKG_DIR, fn))
                     if c not in ALLOWED)
        assert not bad, "%s 出现白名单外数值常量: %r" % (fn, bad)


def test_no_literal_equals_any_synthetic_fact_value():
    """数值常量不得恰好等于合成项目的任何事实值(白名单内的拓扑量除外)。"""
    import os
    fact_vals = _synthetic_fact_values()
    for fn in _py_files():
        bad = sorted(c for c in _numeric_constants(os.path.join(PKG_DIR, fn))
                     if c in fact_vals and c not in ALLOWED)
        assert not bad, "%s 出现与合成 facts 相同的字面量(应改为引用 facts): %r" % (fn, bad)


def test_synthetic_bridges_really_differ_in_span_count():
    """本文件所在的测试体系确实覆盖两种孔数(防止占位断言)。"""
    assert make_5().N_SPAN != make_23().N_SPAN
    assert make_5().N_SPAN == FEATURE_NUMBERS[0]
    assert make_23().N_SPAN == FEATURE_NUMBERS[2]
