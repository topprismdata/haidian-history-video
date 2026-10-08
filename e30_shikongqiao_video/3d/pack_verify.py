# -*- coding: utf-8 -*-
"""P4-T3 三方守恒 validator —— 独立重算路径(双实现互证的第二实现).

消费 section5 manifest + deferred_holes + excluded_ids + ledger_full, 与两
清单对集合; 不 import export_print 装箱码 / section_pack 任何编排码 ——
重算路径只经 p1a_slice(printcheck 排除口径唯一所有者): classify_full ->
print_scope -> _ring_dedup_dispositions(与 G2 门 run_g2 前奏同序)。

═══ 口径考古(2026-10-08, P4 关账报告关键输入; 判据定义, 两实现同口径)═══

疑点: P1 关账行/计划写 "G2 全桥打印单元=1974", T2 实测段 1123 + 留续 990
= 2113 ≠ 1974。

**"打印单元"定义(现行 G2 门/T8b+ 口径)**: 1 单元 = 1 账面石过
p1a_slice.print_scope 四桶排除(in_void / void_cut_fragment /
ring_band_overlap / thin_merge)后的存活者, 石↔单元 1:1, **无合并** ——
g2_report counts.print_stones == print_units == check_stone.n(T9 的
'#R<i>' run 升格分裂机制现行真总体 475 带裁石全单 run, 未触发)。

**1974 出处** = P1-T8 原始轮(commit 04f2e54 的 g2_report.json): 打印单元
1974 + 排除 3961(in_void 2052 / void_cut_fragment 1520 /
ring_band_overlap 305 / thin_merge 84)== 5935, 守恒成立。该轮
ring_band_overlap 用"足印与 RING 剪影交占比 >50% 一刀切"整桶排除。

**2113 出处** = T8b 体量宇宙处置后口径(c74d54f 起, 至 445fd90 返工): T8b 对
ring_band_overlap 逐石 subsume/带裁仲裁, 123 石回打印域(桶 305→182),
thin_merge 16 石回打印域(84→68), 排除 3961→3822, 打印单元
1974+139 = 2113; P2-T6b(35e37cd) 又把 48 石在 in_void ↔
void_cut_fragment 间重分类(排除桶内搬家, 单元数不变)。P1 收官
(T9, 2026-10-07 09:30)即 2113; T2 段包(1123+990)与之同源。

**2037 出处** = 445fd90 拱线族返工(ogee→单心圆弧 17 孔, 2026-10-08)后
**现行口径**: 拱线换族 → 石坐标变 → ring_band_overlap 仲裁 182→222(+40)、
in_void 2004→2028(+24)、void_cut_fragment 1568→1580(+12), 排除
3822→3898, 打印单元 2113−76 = 2037; T6 段包(1047+990)与之同源。

**候选解释裁决**: (a) stone→unit 合并 —— 否(1:1 无合并, 见上);
(b) deferred "990 units" 是石级估算 —— 否(deferred unit_ids 是与 G2
同 print_scope 口径的逐 id 全表, 非 3188 石的估算); (c) 排除项不同 ——
是, 但是**代际差**(T8 原始轮 vs T8b 体量宇宙之后), 非 G2 判据内部不一致。

**守恒判据(本 validator 实现的口径)**:
  * 稳定不变量 = **石级三方恒等(逐 id 集合)**: section_kept ⊎
    deferred_units ⊎ excluded == ledger 全账 5935, 两两不交;
  * 单元级按同口径分段核对: 1047(段) + 990(留续) == 2037 == 重算
    print_units(1:1 石=单元);
  * **1974 不作守恒判据**(历史口径, 与 2113 差 139 的归因如上), 只作
    考古记录存在于本 docstring 与报告 —— 不许硬凑 1974。
"""
import argparse
import copy
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import p1a_slice as PS  # noqa: E402  (printcheck 排除口径唯一所有者)

_HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(_HERE, "out")
PRINT_DIR = os.path.join(OUT_DIR, "print")
DEFAULT_MANIFEST = os.path.join(PRINT_DIR, "section5", "manifest.json")
DEFAULT_DEFERRED = os.path.join(PRINT_DIR, "deferred_holes.json")
DEFAULT_EXCLUDED = os.path.join(PRINT_DIR, "excluded_ids.json")
DEFAULT_LEDGER = os.path.join(OUT_DIR, "ledger_full.json")


# ────────────────────────────── 独立重算路径 ──────────────────────────

def recompute_view(led):
    # type: (dict) -> dict
    """从真账独立重推 G2 打印视角(blender-free, 与 run_g2 前奏同序):
    classify_full -> print_scope -> ring dedup 处置。返回
    {"scope": set(id), "buckets": {桶: set(id)}, "universe": set(id)}。
    宇宙闭合响亮断言(与 section_pack.build_print_view 各自独立实现,
    双实现互证的同口径第二份)。"""
    statuses = PS.classify_full(led["stones"])
    led_mark = copy.deepcopy(led)       # 处置标不进原账(与 pack 侧纪律同)
    sc = PS.print_scope(led_mark, statuses)
    arch_idx_of = {"ARCH%02d" % (i + 1): i for i in range(PS.G2_N_ARCH)}
    PS._ring_dedup_dispositions(led_mark, statuses, sc["scope"],
                                sc["buckets"], arch_idx_of)
    scope = {s["id"] for s in sc["scope"]}
    buckets = {b: set(ids) for b, ids in sc["buckets"].items()}
    universe = {s["id"] for s in led["stones"]}
    excluded = set().union(*buckets.values()) if buckets else set()
    if scope & excluded:
        raise ValueError("recompute_view: scope 与排除桶相交 %d"
                         % len(scope & excluded))
    if scope | excluded != universe:
        raise ValueError("recompute_view: 宇宙不闭合(差 %d)"
                         % len(universe - (scope | excluded)))
    return {"scope": scope, "buckets": buckets, "universe": universe}


# ────────────────────────────── 三方对账 ──────────────────────────────

def _zone(stone_id):
    # type: (str) -> str
    return stone_id.split(".")[0]


def _v(violations, code, detail):
    # type: (list, str, str) -> None
    violations.append({"code": code, "detail": detail})


def verify_pack(section_manifest, deferred_json, excluded_ids, ledger,
                recomputed=None):
    # type: (dict, dict, dict, dict, ...) -> dict
    """三方守恒裁定(纯函数, 不落盘)。

    口径(见模块 docstring 考古): 稳定不变量 = 石级三方恒等(逐 id 集合);
    单元级 1:1 石=单元, 分段核对 1123+990=2113; 1974 为 T8 原始轮历史
    口径, 不作判据。recomputed 可注入 recompute_view 结果(测试复用重算;
    缺省自算)。返回:
      {"ok": bool, "三方": {"section","deferred","excluded"}, "total": 石,
       "units": {...}, "不变量": 口径声明, "violations": [{code,detail}]}
    结构坏账(缺键/类型错)直接 raise ValueError; 语义违背记 violations。
    """
    if recomputed is None:
        recomputed = recompute_view(ledger)
    try:
        sec_ids = {s["id"] for s in section_manifest["stones"]}
        skipped = section_manifest["skipped"]
        sec_zones = set(section_manifest["slice"]["zones"])
        df_ids = set(deferred_json["unit_ids"])
        df_zones = set(deferred_json["zones"])
        ex_buckets = {b: set(i) for b, i in excluded_ids["buckets"].items()}
        universe = {s["id"] for s in ledger["stones"]}
    except (KeyError, TypeError) as e:
        raise ValueError("verify_pack: 输入结构坏账: %r" % (e,))
    scope = recomputed["scope"]
    r_buckets = recomputed["buckets"]
    ex_ids = set().union(*ex_buckets.values()) if ex_buckets else set()
    bad = []         # type: list

    # 1) 石级三方恒等: 两两不交 + 并集==全账
    for a, b, an, bn in ((sec_ids, df_ids, "section", "deferred"),
                         (sec_ids, ex_ids, "section", "excluded"),
                         (df_ids, ex_ids, "deferred", "excluded")):
        inter = a & b
        if inter:
            _v(bad, "party_overlap", "%s∩%s=%d 首5: %r"
               % (an, bn, len(inter), sorted(inter)[:5]))
    union = sec_ids | df_ids | ex_ids
    missing = universe - union
    unknown = union - universe
    if missing:
        _v(bad, "universe_missing", "全账有而三方皆无 %d 首5: %r"
           % (len(missing), sorted(missing)[:5]))
    if unknown:
        _v(bad, "universe_unknown", "三方有而全账无 %d 首5: %r"
           % (len(unknown), sorted(unknown)[:5]))

    # 2) 双实现互证: 重算视角 vs 盘上三清单
    if scope != sec_ids | df_ids:
        _v(bad, "recompute_scope_mismatch",
           "重算 scope %d != 段∪留续 %d (差 %d)"
           % (len(scope), len(sec_ids | df_ids),
              len(scope ^ (sec_ids | df_ids))))
    for b in sorted(set(r_buckets) | set(ex_buckets)):
        if r_buckets.get(b, set()) != ex_buckets.get(b, set()):
            rb, eb = r_buckets.get(b, set()), ex_buckets.get(b, set())
            _v(bad, "recompute_bucket_mismatch",
               "桶 %s: 重算 %d vs 盘上 %d (差 %d)"
               % (b, len(rb), len(eb), len(rb ^ eb)))
    for z in sorted(sec_zones | df_zones):
        want_sec = {i for i in scope if _zone(i) == z} if z in sec_zones \
            else set()
        want_def = {i for i in scope if _zone(i) == z} if z in df_zones \
            else set()
        got_sec = sec_ids & {i for i in universe if _zone(i) == z}
        got_def = df_ids & {i for i in universe if _zone(i) == z}
        if got_sec != want_sec or got_def != want_def:
            _v(bad, "recompute_party_mismatch",
               "孔 %s 分段与重算不符: 段 %d/%d 留续 %d/%d"
               % (z, len(got_sec), len(want_sec),
                  len(got_def), len(want_def)))

    # 3) 孔划分: 段∩留续空, 并集==账面孔全集
    all_zones = {_zone(i) for i in universe}
    if sec_zones & df_zones:
        _v(bad, "zone_partition_mismatch", "段∩留续孔 %r"
           % sorted(sec_zones & df_zones))
    if sec_zones | df_zones != all_zones:
        _v(bad, "zone_partition_mismatch",
           "孔并集 %d != 账面 %d (差 %r)"
           % (len(sec_zones | df_zones), len(all_zones),
              sorted(all_zones - (sec_zones | df_zones))[:5]))

    # 4) 分段成员资格(偷挪探测)
    for i in sorted(sec_ids):
        if _zone(i) not in sec_zones:
            _v(bad, "section_zone_mismatch",
               "段清单含非段孔石 %s" % i)
    for i in sorted(df_ids):
        if _zone(i) not in df_zones:
            _v(bad, "deferred_zone_mismatch",
               "留续清单含非留续孔石 %s" % i)

    # 5) 原料数守恒(含排除的石级账, 分段核对)
    raw_sec = {i for i in universe if _zone(i) in sec_zones}
    raw_def = universe - raw_sec
    if len(raw_sec) != len(sec_ids) + len(skipped):
        _v(bad, "raw_count_mismatch", "段原料 %d != 出件 %d + skipped %d"
           % (len(raw_sec), len(sec_ids), len(skipped)))
    if {e["id"] for e in skipped} != raw_sec - sec_ids:
        _v(bad, "raw_count_mismatch", "段 skipped 集合 != 段原料-出件")
    if deferred_json.get("stones_total") != len(raw_def):
        _v(bad, "raw_count_mismatch", "留续 stones_total %r != 账面 %d"
           % (deferred_json.get("stones_total"), len(raw_def)))
    for z, rec in sorted(deferred_json.get("per_zone", {}).items()):
        z_ids = {i for i in raw_def if _zone(i) == z}
        if rec.get("stones") != len(z_ids):
            _v(bad, "raw_count_mismatch", "留续 %s stones %r != %d"
               % (z, rec.get("stones"), len(z_ids)))

    # 6) skipped 逐条与排除账同桶(不静默)
    id2b = {i: b for b, ids in ex_buckets.items() for i in ids}
    for e in skipped:
        b = id2b.get(e["id"])
        want = "g2_excluded:" + b if b else None
        if e.get("reason") != want:
            _v(bad, "skipped_reason_mismatch",
               "%s reason %r != 排除账 %r" % (e["id"], e.get("reason"), want))

    # 7) 单元计数 1:1 口径分段核对
    if deferred_json.get("units_total") != len(df_ids):
        _v(bad, "unit_count_mismatch", "units_total %r != unit_ids %d"
           % (deferred_json.get("units_total"), len(df_ids)))
    cons = section_manifest.get("conservation", {})
    if cons.get("exported") not in (None, len(sec_ids)):
        _v(bad, "unit_count_mismatch", "conservation.exported %r != %d"
           % (cons.get("exported"), len(sec_ids)))

    # 8) 账代际防混: curve_hash 三方一致(混代即红)
    hashes = {n: d.get("meta", {}).get("curve_hash")
              for n, d in (("ledger", ledger), ("excluded", excluded_ids),
                           ("manifest", section_manifest))}
    if len({h for h in hashes.values() if h}) > 1:
        _v(bad, "curve_hash_mismatch", "账代际混用: %r" % hashes)

    units_now = len(sec_ids) + len(df_ids)
    inv = ("石级三方恒等(逐id集合): section(%d) ⊎ deferred(%d) ⊎ "
           "excluded(%d) == ledger(%d), 两两不交 —— 稳定不变量; "
           "单元级=现行G2口径(1单元=1账面石, print_scope 存活, 无合并): "
           "section(%d)+deferred(%d)=%d; 1974 为 P1-T8 原始轮历史口径"
           "(排除3961, 已被 T8b 体量宇宙处置更替), 不作守恒判据"
           % (len(sec_ids), len(df_ids), len(ex_ids), len(universe),
              len(sec_ids), len(df_ids), units_now))
    return {
        "ok": not bad,
        "三方": {"section": len(sec_ids), "deferred": len(df_ids),
                 "excluded": len(ex_ids)},
        "total": len(universe),
        "units": {"section": len(sec_ids), "deferred": len(df_ids),
                  "sum": units_now,
                  "recomputed_print_units": len(scope),
                  "caliber": "1单元=1账面石(现行G2/T8b+口径); 1974=T8原始"
                             "轮历史口径(04f2e54), 见模块 docstring 考古"},
        "不变量": inv,
        "violations": bad,
    }


# ────────────────────────────── CLI ──────────────────────────────

def main(argv=None, recomputed=None):
    # type: (list, ...) -> int
    """CLI: --section-manifest/--deferred/--excluded/--ledger/--json。
    退出码 0=守恒, 1=违背(清单可机读)。"""
    ap = argparse.ArgumentParser(
        description="P4-T3 三方守恒 validator(独立重算, 口径见 docstring)")
    ap.add_argument("--section-manifest", default=DEFAULT_MANIFEST)
    ap.add_argument("--deferred", default=DEFAULT_DEFERRED)
    ap.add_argument("--excluded", default=DEFAULT_EXCLUDED)
    ap.add_argument("--ledger", default=DEFAULT_LEDGER)
    ap.add_argument("--json", action="store_true",
                    help="输出机读 JSON(否则人读摘要)")
    args = ap.parse_args(argv)
    with open(args.ledger) as fh:
        led = json.load(fh)
    with open(args.section_manifest) as fh:
        sec = json.load(fh)
    with open(args.deferred) as fh:
        df = json.load(fh)
    with open(args.excluded) as fh:
        ex = json.load(fh)
    rep = verify_pack(sec, df, ex, led, recomputed=recomputed)
    if args.json:
        print(json.dumps(rep, ensure_ascii=False, indent=1, sort_keys=True))
    else:
        tag = "OK" if rep["ok"] else "RED"
        print("PACK_VERIFY %s 石级: section %d + deferred %d + excluded %d"
              " == ledger %d" % (tag, rep["三方"]["section"],
                                 rep["三方"]["deferred"],
                                 rep["三方"]["excluded"], rep["total"]))
        print("单元(现行口径): %d + %d = %d (重算 print_units %d)"
              % (rep["units"]["section"], rep["units"]["deferred"],
                 rep["units"]["sum"], rep["units"]["recomputed_print_units"]))
        for v in rep["violations"][:10]:
            print("VIOLATION [%s] %s" % (v["code"], v["detail"]))
        if len(rep["violations"]) > 10:
            print("... 共 %d 条" % len(rep["violations"]))
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
