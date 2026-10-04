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

# ── 硬锁清单不再手写(I2): 从 manifest 表格反推 —— 凡 manifest 记 SHA256 的文件
# 全部进闸门, 缺一条即 fail。手写清单曾只有 8/15, render_shot.py 漂移无人守。
# 只解析三个"文件 SHA256"节; §6 渲染表是 IDAT **像素**哈希(manifest 自己声明
# "仅存档快照, 非对照判据"), 与磁盘文件哈希不同口径, 明确排除在外。
_HASH_SECTIONS = (
    "1. 事实/假设层快照",
    "2. 生成器与判据",
    "4. 参考资产哈希",
)

# C1 回归的下限: 这些核心文件无论 manifest 怎么改写都必须在记录里
# (防 manifest 悄悄删行让闸门缩水)。
_CORE_RECORDED = (
    "3d/facts.py", "3d/assumptions.py", "3d/bridge_geom2.py",
    "3d/build_scene2.py", "3d/qa_bridge.py", "3d/qa_l2.py",
    "3d/refs/ref_elevation.jpg", "3d/refs/ref_mask.png",
)


def _manifest_text():
    return _MANIFEST.read_text(encoding="utf-8")


def _recorded_hashes(text):
    """解析 manifest 各文件哈希节的全部 (相对路径, sha256) 记录。
    路径以 manifest 写法为键(`3d/xxx.py`, 相对 e30_shikongqiao_video/)。"""
    out = {}
    for sec in _HASH_SECTIONS:
        body = _section(text, sec)
        for line in body.splitlines():
            m = re.match(r"^\|\s*`?([^`|]+?\.(?:py|jpg|png))`?\s*\|\s*`([0-9a-f]{64})`", line)
            if m:
                out[m.group(1).strip()] = m.group(2)
    return out


def _repo_path(rel):
    return _REPO / "e30_shikongqiao_video" / rel


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _git_tracked():
    """仓库当前跟踪的文件集合(git ls-files, 只读)。"""
    import subprocess
    r = subprocess.run(["git", "ls-files", "-z", "e30_shikongqiao_video"],
                       cwd=str(_REPO), capture_output=True, check=True)
    return set(r.stdout.decode("utf-8").split("\0"))


def _section(text, heading_prefix):
    """取 `## <heading_prefix>` 起到下一个 `## ` 的正文。"""
    pat = re.compile(r"^## " + re.escape(heading_prefix), re.M)
    m = pat.search(text)
    assert m, "manifest 缺章节: %s" % heading_prefix
    rest = re.search(r"^## ", text[m.end():], re.M)
    end = m.end() + rest.start() if rest else len(text)
    return text[m.start():end]


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


def test_manifest_records_full_file_hash_table():
    """闸门覆盖面自证: 解析器必须吃进 manifest 全部文件哈希记录(15 条),
    且不吞 §6 的 IDAT 像素哈希(口径不同, manifest 自己声明非判据)。"""
    recorded = _recorded_hashes(_manifest_text())
    missing = [p for p in _CORE_RECORDED if p not in recorded]
    assert not missing, "manifest 核心文件记录缺失(闸门缩水): %s" % missing
    assert len(recorded) >= len(_CORE_RECORDED), \
        "记录数 %d 少于核心清单 %d" % (len(recorded), len(_CORE_RECORDED))
    # §6 渲染表(IDAT 像素哈希)绝不能混进文件哈希口径:
    leaked = [k for k in recorded if k.startswith("ortho_") or k.startswith("shot_")]
    assert not leaked, "IDAT 像素哈希被误当文件哈希比对: %s" % leaked


def test_frozen_file_hashes_match_disk():
    """冻结闸门(I2 全量版): manifest 记录的**每一条**哈希都必须与盘上文件一致,
    文件缺盘也是 fail。改动被锁文件必须走 body_changelog 并更新 manifest。"""
    recorded = _recorded_hashes(_manifest_text())
    problems = []
    for rel, want in sorted(recorded.items()):
        p = _repo_path(rel)
        if not p.is_file():
            problems.append("%s (manifest 记录了哈希但盘上无此文件)" % rel)
        elif _sha256(p) != want:
            problems.append("%s (盘上 %s != 记录 %s)"
                            % (rel, _sha256(p)[:12], want[:12]))
    assert not problems, (
        "冻结文件与 manifest 哈希不一致(改锁死条目必须走 3d/refs/body_changelog.md"
        " 并重跑本体判据, 然后更新 manifest): %s" % problems)


def test_manifest_recorded_files_are_git_tracked():
    """C1 回归闸门(I2): manifest 记哈希的每个文件必须被 git 跟踪 ——
    "记录了哈希但没入库"正是 C1 的形状(干净克隆里文件不存在, 冻结不可复现)。"""
    recorded = _recorded_hashes(_manifest_text())
    tracked = _git_tracked()
    untracked = [rel for rel in sorted(recorded)
                 if ("e30_shikongqiao_video/" + rel) not in tracked]
    assert not untracked, (
        "manifest 记录了哈希但文件未入库(C1 同款缺陷, 干净克隆无法重建): %s" % untracked)


def test_manifest_hashes_detect_tampering():
    """负控制: 把 manifest 里任一被记录文件哈希改一个字符, 全量比对器必须报不一致。
    若此测试红, 说明 test_frozen_file_hashes_match_disk 已退化为恒真。"""
    text = _manifest_text()
    recorded = _recorded_hashes(text)
    target = "3d/facts.py"
    old_hash = recorded[target]
    tampered = ("0" if old_hash[0] != "0" else "1") + old_hash[1:]
    doctored = text.replace("`%s`" % old_hash, "`%s`" % tampered, 1)
    assert doctored != text, "负控构造失败: 未找到可替换的哈希"
    after = _recorded_hashes(doctored)
    assert after[target] != old_hash
    bad = [rel for rel in sorted(after)
           if not _repo_path(rel).is_file()
           or _sha256(_repo_path(rel)) != after[rel]]
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
    """全部 [工作值] 常量必须在 manifest §9 逐条出现(名字级), 漏一条即红。
    (终审 I12 后含 3 条判据阈值参数; 旧 docstring 写死"12 条"会随台账增长失真。)"""
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


# ── spec §9 结构化匹配(终审 I15) ──
# 旧版对每条推导值做裸子串断言("2.5" in sec9): "起拱线 SPRINGER" 靠 §9 标题
# "(M2.5 冻结包…)"里的子串**假通过** —— §9 根本没有起拱线条目, 且改成 9.17 才红,
# 说明该断言只会因"别的文本含此子串"而假绿。改为结构化匹配: 每条 (标签, 行内锚, 推导值),
# 锚(公式名/标签)所在行必须同时含推导值 —— 标题子串不再算数。
# 注: spec §9 不含起拱线条目 —— 起拱线由 L1 券族判据(MET_ARCH_FAMILY/MET_SPRINGER)
# 与 facts.SPRINGER 锚定, 本就不属附属构件接口契约; 旧清单里的 SPRINGER 行是恒真假
# 通过项, 删除(而非补造契约条文)。
# 表格锚(need_row=True)只认 §9.2 契约表的 `|`-行: §9.3 的栏板预置 bullet 同含
# "DECK_UP_W/2"与"3.28"(半宽带边界), 不限表格行会靠数值巧合假配对(与 I15 同病)。
_SPEC9_DERIVED = (
    ("顶面半宽 DECK_UP_W/2", "DECK_UP_W/2", lambda: facts.DECK_UP_W / 2.0, True),
    ("底半宽 DECK_DOWN_W/2", "DECK_DOWN_W", lambda: facts.DECK_DOWN_W / 2.0, True),
    ("端顶标高 DECK_Z_END", "DECK_Z_END", lambda: facts.DECK_Z_END, True),
    ("中央顶标高 DECK_Z_TOP", "DECK_Z_TOP", lambda: facts.DECK_Z_TOP, True),
    ("桥台 BRIDGE_ABUT", "BRIDGE_ABUT", lambda: facts.BRIDGE_ABUT, True),
    ("望柱间距 BRIDGE_LEN/63", "BRIDGE_LEN/63", lambda: facts.BRIDGE_LEN / 63.0, False),
    ("望柱数口径", "柱数", lambda: 128, False),
)


def _spec9_missing_entries(sec9):
    """结构化核对 §9: 返回漂移/缺失描述列表(空 = 全过)。"""
    missing = []
    for label, anchor, get_val, need_row in _SPEC9_DERIVED:
        val = get_val()
        s = str(val) if isinstance(val, int) else ("%.4f" % val).rstrip("0")
        lines = [ln for ln in sec9.splitlines() if anchor in ln]
        if need_row:
            lines = [ln for ln in lines if ln.lstrip().startswith("|")]
        if not lines:
            missing.append("%s(§9 无锚 %r 的契约行)" % (label, anchor))
        elif not any(s in ln for ln in lines):
            missing.append("%s(锚 %r 所在行无推导值 %s)" % (label, anchor, s))
    return missing


def test_interface_contract_values_derived_from_facts():
    """spec §9 的数值必须是冻结 facts 的推导值(结构化匹配, 终审 I15):
    改 facts 本体节而不同步 spec §9 => 红(防止契约与事实漂移)。"""
    missing = _spec9_missing_entries(_section_spec9())
    assert not missing, "spec §9 契约与冻结 facts 漂移: %s" % missing


def test_spec9_matcher_detects_entry_deletion():
    """负控制(终审 I15): 匹配器必须能抓"真存在的契约条目被删/被改值"——
    否则它对旧版 SPRINGER 那种子串假通过毫无免疫(判据自证非恒真)。
    逐条删锚行: 每条都必须单独红; 再抽一条改值: 也必须红。"""
    for label, anchor, _get_val, _need_row in _SPEC9_DERIVED:
        sec9 = _section_spec9()
        doctored = "\n".join(ln for ln in sec9.splitlines() if anchor not in ln)
        assert doctored != sec9, "负控构造失败(%s): §9 无锚行可删" % label
        missing = _spec9_missing_entries(doctored)
        assert any(label in m for m in missing), \
            "匹配器未抓到 %s 条目删除: %s" % (label, missing)
    sec9 = _section_spec9()
    doctored = "\n".join(ln.replace("y=±3.28", "y=±3.88") if "y=±3.28" in ln else ln
                         for ln in sec9.splitlines())
    assert doctored != sec9, "负控构造失败: §9 未找到顶面半宽推导值"
    missing = _spec9_missing_entries(doctored)
    assert any("顶面半宽" in m for m in missing), \
        "匹配器未抓到契约值篡改: %s" % missing


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
