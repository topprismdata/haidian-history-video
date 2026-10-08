#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# tests/test_p3_film_layout.py
"""P3-T5b 点云扩容负控(blender 门控): builder 产物 ↔ 单源账对账。

五支负控(主控 T5b 裁决 §5): 点数 5935 / 分区守恒 / in_void==2004 /
非 void 集==排程集 / 抽 100 石 sid→transform(fam_idx) 对账。
判定逻辑全部在本文件(裁判), builder 的 --verify-only 只做只读取证
(dump blend 事实 JSON), 期望侧由测试经 build_scene2 单源函数独立重算。
xyz/rot 容差 1e-5: blend 网格/属性为 float32 存储(坐标量级 ~150)。
"""
import json
import os
import subprocess
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_3D = os.path.join(_ROOT, "3d")
for _p in (_3D, os.path.join(_3D, "film")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import build_scene2 as B          # noqa: E402  单源清点/锚点/分区(blender-free)
import conftest                   # noqa: E402  路径/blender 门控常量

BUILDER = conftest.BUILDER
FILM_LAYOUT = conftest.FILM_LAYOUT
LEDGER = os.path.join(_3D, "out", "ledger_sequenced.json")
SEQ = os.path.join(_3D, "out", "sequence.json")
TOL = 1e-5                        # float32 存储精度(坐标量级 ~150)


def _expectation():
    """测试侧独立重算期望(与 builder 同一单源函数, 不同实现路径)。"""
    with open(LEDGER, encoding="utf-8") as fh:
        stones = json.load(fh)["stones"]
    with open(SEQ, encoding="utf-8") as fh:
        seq = json.load(fh)
    sched = {e["stone_id"] for e in (seq.get("events") or ())
             if e.get("etype") == "PLACE_STONE"}
    spec = B.bridge_ledger()["stones"]
    cens_a = B.census(spec, B.classify_stones(spec))
    st_all = B.classify_stones(stones)
    cens_all = B.census(stones, st_all)
    a_index = {k: i for i, k in enumerate(sorted(cens_a))}
    b_keys = [k for k in sorted(cens_all) if k not in cens_a]
    # [拱线族返工 2026-10-08] A 族数改派生 len(a_index)(2824→2832), 与 builder
    # 同源; 旧硬钉随 uniq 跨洞裁剪石族重推导失效(见 film_layout_build.py 头注)。
    b_rank = {k: len(a_index) + i for i, k in enumerate(b_keys)}
    rows = {}
    for s in stones:
        key = B.family_identity(s, st_all[s["id"]][0])
        rows[s["id"]] = {
            "zone": B.layout_group(s),
            "point": B.placement_point(s),
            "rot": tuple(float(c) for c in s["transform"][3:6]),
            "fam_idx": (a_index[key] if key in a_index else b_rank[key]),
            "in_void": s["id"] not in sched,
        }
    return rows, sched


def test_layout_structure(film_layout_blend, tmp_path):
    rows, sched = _expectation()
    jf = str(tmp_path / "verify.json")
    proc = subprocess.run(
        [conftest.BLENDER, "-b", "-P", BUILDER, "--",
         "--verify-only", "--out", film_layout_blend, "--json", jf],
        cwd=_ROOT, capture_output=True, text=True, timeout=600)
    assert proc.returncode == 0, "verify 失败:\n%s" % (
        "\n".join((proc.stderr or "").splitlines()[-20:]))
    with open(jf, encoding="utf-8") as fh:
        d = json.load(fh)
    # 1) 点数 == 5935(账面全量)
    assert d["total_points"] == len(rows) == 5935
    # 2) in_void == excluded 2004; 非 void 集 == 排程集
    # [拱线族返工 2026-10-08] 2004→2028 新实测(+24 全在 b>a 三孔, 推导见 test_p2_sequencer)
    assert d["in_void"] == len(rows) - len(sched) == 2028
    assert d["nonvoid"] == len(sched) == 3907  # [拱线族返工 2026-10-08] 新实测重钉: b>a 三孔(8/9/10)净空边界上移 → in_void 2004→2028 / 日程 3931→3907 / 事件 4118→4094(逐孔分解 ARCH08 +4/ARCH09 +16/ARCH10 +4, 其余 14 孔零差; 推导见 test_p2_sequencer)
    assert d["nonvoid_eq_sched"] is True
    # 3) 分区守恒(逐 zone 计数 == 单源重算)
    want_zones = {}
    for r in rows.values():
        want_zones[r["zone"]] = want_zones.get(r["zone"], 0) + 1
    assert d["zones"] == want_zones
    # 4) 族/GN 结构: 3517 族对象(2832 A + 685 B), GN 树 8 节点指针接本地族
    # [拱线族返工 2026-10-08] 3509→3517 新实测: A 族 2824→2832(uniq 跨洞裁剪
    # 石族随圆弧几何重推导; N_A 改派生, 见 film_layout_build.py 头注)
    assert d["families"] == 3517
    assert d["gn_tree"] == "P1_LAYOUT_INSTANCES" and d["gn_nodes"] == 8
    assert d["ci_ptr"] == "COL_FAMILIES_FILM"
    # 5) 抽 100 石 sid→transform 对账(xyz/rot float32 容差, fam_idx 精确)
    assert len(d["sample"]) == 100
    for got in d["sample"]:
        want = rows[got["sid"]]
        assert got["zone"] == want["zone"]
        assert got["fam_idx"] == want["fam_idx"]
        for a, b in zip(got["xyz"], want["point"]):
            assert a == pytest.approx(b, abs=TOL)
        for a, b in zip(got["rot"], want["rot"]):
            assert a == pytest.approx(b, abs=TOL)
