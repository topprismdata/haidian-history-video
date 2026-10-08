# -*- coding: utf-8 -*-
"""P3-T6 旁白稿 lint CI(计划 Task 6 Step 1 原文两支).

- test_script_passes_lint: narration_script.md 全文过 narration_lint
  (P2 交付, 判据面只读), 红则测试红; 另钉五段骨架结构——ChatGPT 精修
  替换后段结构仍须保全。
- test_script_carries_four_iron_rules: 四条铁律关键词逐条在文中可指认;
  铁律③条件性表述不得弱化 —— 串行是「临界定」, 不是「不可行」。
blender-free; Python 3.9.6。
"""
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_3D = os.path.join(REPO, "3d")
for _p in (_3D, os.path.join(_3D, "film")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import narration  # noqa: E402  P2 交付(3d/narration.py), 只读其判据

_SCRIPT = os.path.join(_3D, "film", "narration_script.md")

# 五段骨架(计划 Task 6: 开场/首孔教学/合龙/落架高潮/桥成)
_SECTIONS = ("开场", "首孔", "合龙", "落架", "桥成")

# 铁律关键词 → 逐条可指认(计划 Task 6 Step 1 原文词表)
_IRON_KEYWORDS = ("裸环", "自承", "模型族", "工程推断·非史料", "对称同步")


def _script_text():
    # type: () -> str
    with open(_SCRIPT, encoding="utf-8") as f:
        return f.read()


def test_script_passes_lint():
    """全文过 narration_lint; 五段骨架结构在(精修替换后仍须保全)。"""
    text = _script_text()
    findings = narration.narration_lint(text)
    assert narration.narration_ok(findings), \
        "narration_script.md 过不了自己的 lint: %s" % \
        [str(f) for f in findings]
    for sec in _SECTIONS:
        assert sec in text, "五段骨架缺段: %s" % sec


def test_script_carries_four_iron_rules():
    """四铁律关键词逐条可指认; ③的条件性表述不得弱化。"""
    text = _script_text()
    for kw in _IRON_KEYWORDS:
        assert kw in text, "四铁律关键词缺失: %s" % kw
    # 条件性表述在文: 临界定 + 显式否定式「非不可行」
    assert "临界定" in text, "缺「临界定」——铁律③条件性表述被弱化"
    assert "非不可行" in text, "缺「非不可行」否定式——铁律③被弱化"
    # 绝对化反例(精修改稿红线): 串行…不可行 / 串行…不可能 一律不允许
    # (「非不可行」含前缀「非」, 不命中; 窗口 30 字内不许出现绝对化判词)
    weak = re.search(r"串行[^。\n]{0,30}(?<!非)不可行", text)
    assert weak is None, "出现「串行…不可行」绝对化表述(铁律③条件性被弱化)"
    weak2 = re.search(r"串行[^。\n]{0,30}不可能", text)
    assert weak2 is None, "出现「串行…不可能」绝对化表述(铁律③条件性被弱化)"
