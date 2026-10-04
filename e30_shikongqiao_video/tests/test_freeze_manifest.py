# -*- coding: utf-8 -*-
"""E30 M2.5 冻结包完整性测试(T8)。

冻结 = 可复现构建状态整体。本文件把 freeze_manifest.md 的记录变成可执行闸门:
  - manifest 七类信息齐全
  - 记录的文件哈希与盘上真实文件一致(管线本体 + T3.5 参考资产, 防冻结后静默改动)
  - 冻结状态声明与 facts 实况一致(有工作值 => 必须是 CONDITIONAL)
  - 工作值逐条清单与 facts.SOURCES 完全一致
  - spec §9 附属构件接口契约的数值确由冻结 facts 推导(改 facts 必须同步 spec)
  - 负控制: 哈希比对器对篡改必报(篡改 manifest 一个字符必须被抓)

渲染表现层(materials/ortho/shot_auto2 及渲染 PNG)在 manifest 中记快照但不参与
本硬锁 —— 它们属 M4 渲染契约范围, 冻结批准后随 M4 升级为硬锁。
"""
import importlib
import hashlib
import re
import sys
from pathlib import Path

import pytest

_3D_DIR = Path(__file__).resolve().parents[1] / "3d"
_REPO = Path(__file__).resolve().parents[2]
_MANIFEST = _3D_DIR / "refs" / "freeze_manifest.md"
_SPEC = _REPO / "docs" / "superpowers" / "specs" / "2026-10-04-e30-bridge-facts-design.md"

sys.path.insert(0, str(_3D_DIR))
facts = importlib.import_module("facts")

# 硬锁范围: 冻结本体真相源 + 判据 + T3.5 冻结参考资产
_LOCKED_FILES = [
    _3D_DIR / "facts.py",
    _3D_DIR / "assumptions.py",
    _3D_DIR / "bridge_geom2.py",
    _3D_DIR / "build_scene2.py",
    _3D_DIR / "qa_bridge.py",
    _3D_DIR / "qa_l2.py",
    _3D_DIR / "refs" / "ref_elevation.jpg",
    _3D_DIR / "refs" / "ref_mask.png",
]


def _manifest_text():
    return _MANIFEST.read_text(encoding="utf-8")


def _parse_file_hashes(text):
    """从 manifest 表格里抽 (文件名, sha256)。只认 64 位十六进制哈希单元格。
    键取 basename(manifest 表内写 `3d/xxx.py` 相对路径)。"""
    out = {}
    for line in text.splitlines():
        m = re.match(r"^\|\s*`?([^`|]+?\.(?:py|jpg|png))`?\s*\|\s*`([0-9a-f]{64})`\s*\|", line)
        if m:
            out[Path(m.group(1).strip()).name] = m.group(2)
    return out


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _section(text, heading_prefix):
    """取 `## <heading_prefix>` 起到下一个 `## ` 的正文。"""
    pat = re.compile(r"^## " + re.escape(heading_prefix), re.M)
    m = pat.search(text)
    assert m, "manifest 缺章节: %s" % heading_prefix
    nxt = pat.search(text, m.end())
    rest = re.search(r"^## ", text[m.end():], re.M)
    end = m.end() + rest.start() if rest else len(text)
    return text[m.start():end if not nxt else min(end, nxt.start())]


REQUIRED_SECTIONS = [
    "1. 事实/假设层快照",
    "2. 生成器与判据",
    "3. Blender 版本",
    "4. 参考资产哈希",
    "5. 容差配置",
    "6. 渲染图哈希",
    "7. 冷启动重建验证",
    "8. 已知偏差豁免表",
    "9. 冻结状态声明",
]


def test_manifest_exists_with_required_sections():
    text = _manifest_text()
    for h in REQUIRED_SECTIONS:
        assert ("## " + h) in text, "manifest 缺必备章节: %s" % h


def test_frozen_file_hashes_match_disk():
    """冻结闸门: manifest 记录的哈希必须与盘上文件一致。
    改动被锁文件必须走 body_changelog 并更新 manifest, 否则此处红。"""
    recorded = _parse_file_hashes(_manifest_text())
    locked = {p.name: p for p in _LOCKED_FILES}
    missing = [name for name in locked if name not in recorded]
    assert not missing, "manifest 未记录被锁文件哈希: %s" % missing
    bad = [n for n, p in sorted(locked.items()) if recorded[n] != _sha256(p)]
    assert not bad, (
        "冻结文件与 manifest 哈希不一致(改锁死条目必须走 3d/refs/body_changelog.md"
        " 并重跑本体判据, 然后更新 manifest): %s" % bad)


def test_manifest_hashes_detect_tampering():
    """负控制: 把 manifest 里任一被锁文件哈希改一个字符, 比对器必须报不一致。
    若此测试红, 说明 test_frozen_file_hashes_match_disk 已退化为恒真。"""
    text = _manifest_text()
    recorded = _parse_file_hashes(text)
    target = "facts.py"
    old_hash = recorded[target]
    tampered = ("0" if old_hash[0] != "0" else "1") + old_hash[1:]
    doctored = text.replace("`%s`" % old_hash, "`%s`" % tampered, 1)
    assert doctored != text, "负控构造失败: 未找到可替换的哈希"
    after = _parse_file_hashes(doctored)
    assert after[target] != old_hash
    disk = {p.name: _sha256(p) for p in _LOCKED_FILES}
    bad = [n for n in disk if after.get(n) != disk[n]]
    assert target in bad, "篡改哈希未被比对器抓到"


def test_freeze_state_matches_facts_reality():
    """有工作值 => 必须声明 CONDITIONAL_RECONSTRUCTION_FREEZE;
    全部测绘/档案 => 才允许 FACTUAL_FREEZE。禁止虚标冻结状态。"""
    text = _manifest_text()
    has_wv = any(lv == "工作值" for lv, _ in facts.SOURCES.values())
    has_cond = "CONDITIONAL_RECONSTRUCTION_FREEZE" in text
    has_factual = re.search(r"### `FACTUAL_FREEZE`", text) is not None
    if has_wv:
        assert has_cond, "存在工作值却未声明条件冻结"
        assert has_factual, "条件冻结下必须显式声明 FACTUAL_FREEZE 不适用"
    else:
        assert has_factual and not has_cond, "无工作值却声明条件冻结"


def test_work_values_listed_one_by_one():
    """12 条工作值必须在 manifest §9 逐条出现(名字级), 漏一条即红。"""
    sec9 = _section(_manifest_text(), "9. 冻结状态声明")
    listed = set(re.findall(r"^\|\s*(?:\d+|附)\s*\|\s*([A-Z_]+)\s*\|", sec9, re.M))
    want = {k for k, (lv, _) in facts.SOURCES.items() if lv == "工作值"}
    missing = want - listed
    extra = listed - want - {"ARCH_RATIO"}  # 附行允许图像推导条目
    assert not missing, "manifest 工作值清单缺: %s" % sorted(missing)
    assert not extra, "manifest 工作值清单多列: %s" % sorted(extra)


def test_blender_version_recorded():
    text = _manifest_text()
    assert re.search(r"Blender 5\.2\.\d+ LTS", text), "manifest 未记 Blender 5.2 LTS 精确版本"
    assert re.search(r"build hash: `[0-9a-f]{12}`|build hash: [0-9a-f]{12}", text), \
        "manifest 未记 build hash(精确到 build 号)"


def test_core_hash_candidates_present():
    """§7 冷重建对照表的候选列必须有三个核心对象的 sha_sorted(64 hex)。"""
    sec7 = _section(_manifest_text(), "7. 冷启动重建验证")
    got = re.findall(r"^\|\s*`(bridge_body|voussoir|impost)` sha_sorted\s*\|\s*`([0-9a-f]{64})`", sec7, re.M)
    assert {n for n, _ in got} == {"bridge_body", "voussoir", "impost"}, \
        "核心几何候选哈希不全: %r" % got


def test_hash_tool_exists():
    assert (_3D_DIR / "freeze_hash.py").is_file(), \
        "缺核心几何哈希唯一定义点 3d/freeze_hash.py"


def test_interface_contract_values_derived_from_facts():
    """spec §9 的数值必须是冻结 facts 的推导值:
    改 facts 本体节而不同步 spec §9 => 红(防止契约与事实漂移)。"""
    spec = _SPEC.read_text(encoding="utf-8")
    m9 = re.search(r"^## 9\. 附属构件接口契约", spec, re.M)
    assert m9, "spec 缺 §9 附属构件接口契约"
    sec9 = spec[m9.start():]
    for label, val in (
        ("顶面半宽 DECK_UP_W/2", facts.DECK_UP_W / 2.0),
        ("底半宽 DECK_DOWN_W/2", facts.DECK_DOWN_W / 2.0),
        ("端顶标高 DECK_Z_END", facts.DECK_Z_END),
        ("中央顶标高 DECK_Z_TOP", facts.DECK_Z_TOP),
        ("起拱线 SPRINGER", facts.SPRINGER),
        ("桥台 BRIDGE_ABUT", facts.BRIDGE_ABUT),
        ("望柱间距 BRIDGE_LEN/63", facts.BRIDGE_LEN / 63.0),
    ):
        s = ("%.4f" % val).rstrip("0")
        assert s in sec9, "spec §9 缺事实推导值 %s=%s(改 facts 必须同步契约)" % (label, s)
    # 望柱数口径: L2 判据 128±0 必须出现在契约里
    assert "128" in sec9, "spec §9 缺望柱数 128 口径"


def test_contract_forbids_body_modification():
    """契约必须写明反改禁令与 body_changelog 后果, 否则契约无牙。"""
    sec9 = _section_spec9()
    assert "body_changelog" in sec9, "spec §9 未写本体变更后果(body_changelog)"
    assert "不得反改本体" in sec9, "spec §9 未写反改禁令"


def _section_spec9():
    spec = _SPEC.read_text(encoding="utf-8")
    m = re.search(r"^## 9\. 附属构件接口契约", spec, re.M)
    return spec[m.start():]


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
