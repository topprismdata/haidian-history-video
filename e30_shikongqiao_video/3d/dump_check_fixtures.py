# -*- coding: utf-8 -*-
"""T9: 真实失败件 fixture 生成器(回归钉, P1 处方: 合成非凸件抓不到该机制)。

从 out/ledger_full.json 重放 G2 前半程(classify_full -> print_scope ->
_ring_dedup_dispositions), 对 scope 逐石复刻 run_g2 的 pre/post-inset
check_stone, 选出失败件按入选项 dump 为 tests/fixtures/check_106/*.json:

  {id, clr_model_mm, fit, verts_pre(世界系, world_mesh 输出=EP.inset 的
   真实输入), faces, post_fail_codes, meta(role/zone/clipped_by)}

fixture 消费方(test_p1_slice)保证: 同一 clr 下 EP.inset(fixture.verts_pre)
后 check_stone 必须无 SELF_INTERSECT(现况红=机制在, 修复后绿)。

用法:
  python3 3d/dump_check_fixtures.py            # 重放+选择+写 fixtures
  python3 3d/dump_check_fixtures.py --list     # 只打印失败清单
前置: blender -b --python 3d/p1a_slice.py -- --g2 (生成 out/ledger_full.json)
"""
import copy
import json
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import export_print as EP
import p1a_slice as P
import printcheck as PC

FIXTURE_DIR = os.path.join(os.path.dirname(_HERE), "tests", "fixtures",
                           "check_106")

# 入选规则(确定性, 变化即测试显式失配): 同带负控 1 件(带裁构造相同且
# post-inset 全绿 —— 防修复把好件改坏) + 真失败件按 x/z 极值带内顶点数
# 降序取 3(跨角色)。历史 anchor ARCH03.EAST.SPANDREL.C07.B00(T8c y 落位
# 反例)在 T8c partner 足印守卫后已不是带裁石(status=out, 不在 475 总体),
# 负控改取同族 ARCH03.EAST.SPANDREL.C07.B01(同孔同课程同带, 若在总体且
# 全绿) —— anchor 缺位时按"最大极值带绿件"兜底, 规则仍确定性。
ANCHOR_ID = "ARCH03.EAST.SPANDREL.C07.B00"
ANCHOR_FALLBACK_ID = "ARCH03.EAST.SPANDREL.C07.B01"
N_FAIL_PICKS = 3       # 真失败件席位


def _band_vertex_count(verts, clr_model_mm):
    """距任一轴极值面 < clr 的顶点数(复审"8-10 顶点落在距极值面一个 clr
    带内"的量化口径)。"""
    V = np.asarray(verts, dtype=float)
    lo, hi = V.min(axis=0), V.max(axis=0)
    c = float(clr_model_mm) / 1000.0
    m = np.zeros(len(V), dtype=bool)
    for ax in range(3):
        if hi[ax] - lo[ax] <= max(1e-12, (hi[ax] - lo[ax]) * 1e-9):
            continue
        m |= (V[:, ax] <= lo[ax] + c) | (V[:, ax] >= hi[ax] - c)
    return int(m.sum())


_CACHE = os.path.join(P.OUT_DIR, "_t9_replay_cache.json")


def _verts_faces_of(item):
    return item["verts_pre"], item["faces"]


def replay(refresh=False):
    """重放 G2 前半程, 返回 (fails, trim_all, scope, statuses, led)。
    fails 元素 = {id, role, verts_pre, faces, fit, clr_model_mm, codes,
    post_ok}。trim_all = 全部带裁石同构条目(含 post_ok=True 的好件)。
    结果缓存 out/_t9_replay_cache.json(untracked, 账本变化后 --refresh)。"""
    if not refresh and os.path.exists(_CACHE):
        cached = json.load(open(_CACHE, encoding="utf-8"))
        return (cached["fails"], cached["trim_all"], None, None, None)
    led = json.load(open(os.path.join(P.OUT_DIR, P.FULL_LEDGER_NAME),
                         encoding="utf-8"))
    led = copy.deepcopy(led)
    statuses = P.classify_full(led["stones"])
    sc = P.print_scope(led, statuses)
    scope = sc["scope"]
    buckets = sc["buckets"]
    arch_idx_of = {"ARCH%02d" % (i + 1): i for i in range(P.G2_N_ARCH)}
    P._ring_dedup_dispositions(led, statuses, scope, buckets, arch_idx_of)
    fails, trim_all = [], []
    for s in scope:
        if statuses[s["id"]][0] != "ring_trim":
            continue
        verts, faces = P.world_mesh(s, statuses)
        fit, clr_model = EP.fit_for_block(EP._extents_m(verts), P.G2_SCALE)
        v2, f2 = EP.flip_outward(EP.inset(verts, clr_model), faces)
        rep = PC.check_stone(v2, f2, scale=P.G2_SCALE,
                             min_wall_print_mm=P.G2_MIN_WALL_PRINT_MM)
        item = {
            "id": s["id"], "role": s["role_struct"],
            "verts_pre": verts, "faces": faces,
            "fit": fit, "clr_model_mm": clr_model,
            "codes": sorted({i["code"] for i in rep["issues"]}),
            "post_ok": bool(rep["ok"]),
        }
        trim_all.append(item)
        if not rep["ok"]:
            fails.append(item)
    try:
        with open(_CACHE, "w", encoding="utf-8") as fh:
            json.dump({"fails": fails, "trim_all": trim_all}, fh)
    except OSError:
        pass
    return fails, trim_all, scope, statuses, led


def main():
    list_only = "--list" in sys.argv
    fails, trim_all, _scope, _statuses, _led = replay(
        refresh="--refresh" in sys.argv)
    print("scope fails: %d / trim total %d" % (len(fails), len(trim_all)))
    if list_only:
        for f in trim_all:
            print("  %-34s %-8s clr=%4.1f nverts=%3d band=%2d %s"
                  % (f["id"], f["role"], f["clr_model_mm"],
                     len(f["verts_pre"]),
                     _band_vertex_count(f["verts_pre"], f["clr_model_mm"]),
                     "OK" if f["post_ok"] else ",".join(f["codes"])))
        return
    # T9b(M3) 防自毁证据: fixtures 是【旧实现失败态】的历史证据(3 件
    # post_ok=False + 失败码)。现实现(仿射 inset)重放必然 fails=0 —— 若
    # 此时照写, 会清空目录只落 1 件绿控, 失败证据被静默覆盖(CI 随后会因
    # 总体钉响亮失败, 但证据已没了)。真要重生成必须人工删旧证据后显式
    # 重跑, 不许脚本顺手自毁。
    if not fails:
        raise RuntimeError(
            "当前实现重放无失败件(fails=0): 现行 fixtures 是 T8c/T9 历史"
            "失败证据(post_ok=False 3 件), 重生成会自毁证据。若几何/判据"
            "确已变更需重钉, 先人工确认并清空 %s 再显式重跑本生成器"
            % FIXTURE_DIR)
    by_id = {f["id"]: f for f in trim_all}
    anchor = by_id.get(ANCHOR_ID)
    if anchor is not None and not anchor["post_ok"]:
        raise RuntimeError("anchor %s 现况非绿, 负控语义失效(几何漂移): %s"
                           % (ANCHOR_ID, anchor["codes"]))
    if anchor is None:
        anchor = by_id.get(ANCHOR_FALLBACK_ID)
        if anchor is not None and not anchor["post_ok"]:
            anchor = None
    if anchor is None:
        # 兜底: 极值带顶点数最大的绿件(确定性, id 决胜)
        oks = [f for f in trim_all if f["post_ok"]]
        oks.sort(key=lambda f: (-_band_vertex_count(f["verts_pre"],
                                                   f["clr_model_mm"]), f["id"]))
        if not oks:
            raise RuntimeError("带裁总体无全绿件, 负控无法入选")
        anchor = oks[0]
    picks = [anchor]
    rest = [f for f in fails if all(f["id"] != p["id"] for p in picks)]
    rest.sort(key=lambda f: (-_band_vertex_count(f["verts_pre"],
                                               f["clr_model_mm"]), f["id"]))
    got_roles = set()
    for f in rest:      # 第一遍: 真失败件角色多样性优先
        if len(picks) >= 1 + N_FAIL_PICKS:
            break
        if f["role"] not in got_roles:
            picks.append(f)
            got_roles.add(f["role"])
    for f in rest:      # 第二遍: 席位未满按极值带顶点数补齐
        if len(picks) >= 1 + N_FAIL_PICKS:
            break
        if all(f["id"] != p["id"] for p in picks):
            picks.append(f)
    os.makedirs(FIXTURE_DIR, exist_ok=True)
    for old in os.listdir(FIXTURE_DIR):
        os.remove(os.path.join(FIXTURE_DIR, old))
    for f in picks:
        out = {
            "schema": 1,
            "id": f["id"], "role": f["role"],
            "fit": f["fit"], "clr_model_mm": f["clr_model_mm"],
            "post_ok": f["post_ok"],
            "post_fail_codes": f["codes"],
            # T9b(M3): 极值带顶点数入册 —— 距任一极值面 < clr 的顶点数是
            # 该机制暴露度的量化口径, 几何漂移重生成时肉眼可见(防静默
            # 换件); 复算公式 = dump_check_fixtures._band_vertex_count。
            "band_verts": _band_vertex_count(f["verts_pre"],
                                             f["clr_model_mm"]),
            "verts_pre": [[round(v[0], 9), round(v[1], 9), round(v[2], 9)]
                          for v in f["verts_pre"]],
            "faces": [list(fc) for fc in f["faces"]],
        }
        path = os.path.join(FIXTURE_DIR, f["id"] + ".json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=1)
        print("wrote %s (nverts=%d nfaces=%d clr=%.1fmm band=%d post_ok=%s)"
              % (os.path.relpath(path, os.path.dirname(_HERE)),
                 len(out["verts_pre"]), len(out["faces"]),
                 out["clr_model_mm"],
                 _band_vertex_count(f["verts_pre"], f["clr_model_mm"]),
                 out["post_ok"]))


if __name__ == "__main__":
    main()
