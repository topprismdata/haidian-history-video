# -*- coding: utf-8 -*-
"""bridge3d —— 中国古建三维管线的通用 L1 验收框架(拓扑不变量与项目常数分离)。

为什么存在:
  首个验证项目(E30 石拱桥)的判据曾把项目常数写进判据源码
  (形如 "孔数必须等于某具体数值"), 导致框架无法承接第二个项目。
  本包把三件事彻底分开:
    项目常数   → 只存在于项目 facts 模块(带 SOURCES 五级来源台账);
    拓扑不变量 → 框架 INV 判据(任何 n 孔桥普适: 展开长度一致 / 支承数=N_SPAN+1);
                对称、单峰等形态约束不是普适律, 由项目自声明(见下);
    项目自声明 → facts.RELATIONS 关系型不变量, 判据只验证"声明的约束"。

语义铁约(所有判据共用):
  fail  阻塞;
  warn  不阻塞, 报告必须列出;
  skip  未执行(前置事实缺失), 不算通过, 也绝不因缺可选事实而 fail;
  每条判据必须配"故意破坏"用例且破坏被抓(negative_control), 否则视为恒真。

第二个项目接入(三步, 详见 docs/bridge3d.md):
  1) 写项目 facts 模块: REQUIRED 常量 + SPAN_DISTINCT + SOURCES(五级登记)
     + RESEARCH_DONE + 三条禁令 docstring + RELATIONS(可选);
  2) 验收 = bridge3d.audit(facts) (含 checks_l1 三层 + facts_schema 事实层);
  3) 为每个 fail 代码写破坏用例: negative_control.assert_criterion_rejects /
     assert_no_always_true (恒真审计)。

本包源码不出现任何项目数值(由 tests/bridge3d/test_no_project_literals.py 锁死)。
"""
from .schema import (REQUIRED, REQUIRED_LISTS, REQUIRED_REGS, OPTIONAL, GRADES,
                     LEVELS, Finding, MissingFactError,
                     is_number, has, get,
                     fail_codes, warn_codes, skip_codes, has_fail, summarize,
                     validate_facts_module)
from . import derive
from . import checks_l1
from . import facts_schema
from . import negative_control
from .checks_l1 import run_l1, default_checks, INV_CHECKS, MET_CHECKS, IMP_CHECKS
from .facts_schema import run_fact_checks, FACT_CHECKS
from .negative_control import (mutate, dropped, snapshot,
                               assert_criterion_rejects, assert_criterion_accepts,
                               assert_skip_not_fail, patched_derive,
                               default_corruptions, killability_report,
                               assert_no_always_true)

__all__ = [
    # 契约
    "REQUIRED", "REQUIRED_LISTS", "REQUIRED_REGS", "OPTIONAL", "GRADES", "LEVELS",
    "Finding", "MissingFactError", "is_number", "has", "get",
    "fail_codes", "warn_codes", "skip_codes", "has_fail", "summarize",
    "validate_facts_module",
    # 推导
    "derive",
    # 判据
    "checks_l1", "run_l1", "default_checks", "INV_CHECKS", "MET_CHECKS", "IMP_CHECKS",
    # 事实层
    "facts_schema", "run_fact_checks", "FACT_CHECKS",
    # 负控制
    "negative_control", "mutate", "dropped", "snapshot",
    "assert_criterion_rejects", "assert_criterion_accepts", "assert_skip_not_fail",
    "patched_derive", "default_corruptions", "killability_report",
    "assert_no_always_true",
]


def audit(f, closure_tol=None):
    """一站式验收: L1 三层判据 + 事实层校验。返回 list[Finding]。
    只有 fail 阻塞; skip=未执行不算通过。"""
    return run_l1(f, closure_tol=closure_tol) + run_fact_checks(f)
