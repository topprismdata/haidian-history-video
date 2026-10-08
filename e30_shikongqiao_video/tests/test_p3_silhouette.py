# -*- coding: utf-8 -*-
"""P3-T6 剪影 SVG 资产测试(计划 Task 6 Step 1 原文两支 + 生成全表一支).

- test_silhouette_svg_evidence_header: 每个生成的 SVG 首行注释含 evidence:
  (G0 证据号或 [设计选择]); gen_svg 对无出处输入必须 raise(fail-closed);
  generate_all 逐站位透传 SILHOUETTE_SLOTS 自带证据字段。
- test_svg_render_safe: 纯 path 验证 —— 无 script/image/外链/文本元素,
  且输出确定(同 pose 两次生成逐字节同)。
净空纪律: 证据校验逻辑与被测模块同源(不另抄第二套正则语义的判定值);
blender-free; Python 3.9.6。
"""
import os
import re
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_3D = os.path.join(REPO, "3d")
for _p in (_3D, os.path.join(_3D, "film")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from film_geometry import SILHOUETTE_SLOTS  # noqa: E402  站位/证据单源(P3-T4)
from film_silhouette import gen_svg, generate_all  # noqa: E402

# 证据判定与 film_silhouette 同一正则语义(守同一合同, 不另立口径)
_EVIDENCE_RE = re.compile(r"(?:C:)?[AB]\d+")


def _read(path):
    # type: (str) -> str
    with open(path, encoding="utf-8") as f:
        return f.read()


def test_silhouette_svg_evidence_header(tmp_path):
    """首行证据头注硬合同: 有出处才出图, 无出处即 raise。"""
    # 1) 合法 evidence(含 G0 号 + [设计选择]) → 首行头注逐位透传
    p1 = os.path.join(str(tmp_path), "lever.svg")
    gen_svg("lever", p1, "C:A4|[设计选择] 测试·撬形制")
    first = _read(p1).splitlines()[0]
    assert first == "<!-- evidence: C:A4|[设计选择] 测试·撬形制 -->"
    assert _EVIDENCE_RE.search(first) and "[设计选择]" in first

    # 2) 仅 [设计选择](无 G0 号)也合法 —— 证据字段分层允许
    p2 = os.path.join(str(tmp_path), "chisel.svg")
    gen_svg("chisel", p2, "[设计选择] 站位坐标无史料出处")
    assert _read(p2).splitlines()[0].startswith("<!-- evidence: [设计选择]")

    # 3) 无出处输入必须 raise: 空/白/无号无标签的话/仅 [现代分析] 标签
    for bad in ("", "   ", "随便一句没有出处的话", "[现代分析] 仅标签不算出处"):
        with pytest.raises(ValueError):
            gen_svg("lever", os.path.join(str(tmp_path), "bad.svg"), bad)
    #    未知 pose 同样拒绝(词表单源 SILHOUETTE_SLOTS)
    with pytest.raises(ValueError):
        gen_svg("hammer", os.path.join(str(tmp_path), "x.svg"), "C:A4")
    #    含 '--' 的 evidence 会破坏 SVG 注释结构, 拒绝
    with pytest.raises(ValueError):
        gen_svg("lever", os.path.join(str(tmp_path), "y.svg"), "C:A4--bad")

    # 4) generate_all: 全站位落盘, 首行 = 站位自带证据字段逐位透传
    out = os.path.join(str(tmp_path), "all")
    paths = generate_all(out)
    assert len(paths) == len(SILHOUETTE_SLOTS)
    for slot, path in zip(SILHOUETTE_SLOTS, paths):
        assert os.path.exists(path)
        assert _read(path).splitlines()[0] == "<!-- evidence: %s -->" \
            % slot["evidence"]


def test_svg_render_safe(tmp_path):
    """纯 path 验证: 无 script/外链/位图/文本元素; 输出确定。"""
    _FORBIDDEN = ("<script", "<image", "<foreignobject", "<use", "<text",
                  "<tspan", "href", "@import", "javascript:", "onload")
    out = os.path.join(str(tmp_path), "safe")
    paths = generate_all(out)
    assert len(paths) == len(SILHOUETTE_SLOTS)
    for path in paths:
        svg = _read(path)
        low = svg.lower()
        for bad in _FORBIDDEN:
            assert bad not in low, "%s 含禁用标记 %r" % (path, bad)
        # 全部元素 = 根 svg + path(注释被标签正则自然跳过)
        tags = set(re.findall(r"<\s*([a-zA-Z][a-zA-Z]*)", svg))
        assert tags == {"svg", "path"}, "%s 元素集 = %s" % (path, tags)
        assert svg.startswith("<!-- evidence:")
        assert 'viewBox="0 0 240 320"' in svg
    # 确定性: 同表重出 → 逐字节同(剪影资产可复现, 无随机源)
    out2 = os.path.join(str(tmp_path), "safe2")
    for a, b in zip(paths, generate_all(out2)):
        assert _read(a) == _read(b)
