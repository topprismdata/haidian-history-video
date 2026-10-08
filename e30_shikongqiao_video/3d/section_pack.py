# e30_shikongqiao_video/3d/section_pack.py
# -*- coding: utf-8 -*-
"""P4-T2 段包出图: 代表段(中央五孔 ARCH07-11, spec#4 M1c) -> 可执行打印
制造包 out/print/section5/(manifest/STL+3MF 按 maoshi|qingshi 分目录/ledger_print/
coupon 首件/PACK_REPORT 汇总)+ 留续清单 deferred_holes.json(段外 12 孔)。

编排(全部 blender-free, 纯逻辑): G2 打印视角重建(build_print_view, 与
p1a_slice.run_g2 前奏同序: classify_full -> print_scope -> ring_dedup 处置)
-> slice_section(段孔 x scope 选石) -> export_print.export_ledger(zones=段孔,
过滤点在账遍历处, 分档/装箱/FIT 约定零动) -> manifest 增强:
  - skipped 补全: 段内未出件石逐条带 reason="g2_excluded:<桶>"(不静默),
    与 export 的 role 过滤语义(P1 原样)合并;
  - slice 扩型: {"zones":[...], "zone":首孔(向后兼容键), "arch_idx":[...],
    stones/roles/note};
  - coupon 首件约定登记(1:1 配合试片随包);
  - conservation: 段守恒账 + 全段体积/件数汇总 + spec ~913 估算的实测偏差。
幂等: created_utc 归空(出包时刻不落盘, 溯源归 git), 3MF zip 容器时间归一
(内层 model 零改动) -> 两连跑全树逐字节同(tests/test_p4_section.py 钉)。
零漂移门: zones=None 对盘上 central manifest(45fed1e8)的 STL/ledger_print
逐字节复现 —— 同时证明 build_print_view 重建与 G2 门时序逐位同源。
"""
import argparse
import copy
import io
import json
import os
import sys
import zipfile

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import export_print as EP  # noqa: E402
import ledger as L  # noqa: E402
import p1a_slice as PS  # noqa: E402
import scale_params as SCALE  # noqa: E402

SCHEMA = 1
SEGMENT = tuple(SCALE.SEGMENT_DEFAULT)      # ("ARCH07".."ARCH11"), 单一来源
OUT_DIR = os.path.join(_HERE, "out")
LEDGER_PATH = os.path.join(OUT_DIR, "ledger_full.json")
PRINT_DIR = os.path.join(OUT_DIR, "print")
PACK_DIR = os.path.join(PRINT_DIR, "section5")
DEFERRED_PATH = os.path.join(PRINT_DIR, "deferred_holes.json")
SPEC_ESTIMATE_UNITS = 913       # spec#4 M1: 2747 x 0.332(全桥单元率) ~ 913
ZIP_FIXED_DATE = (1981, 1, 1, 0, 0, 0)      # 3MF 容器去时间(内层零改动)


# ---------------------------------------------------------------- 账与视角

def load_full_ledger(path=LEDGER_PATH):
    # type: (str) -> dict
    """真账加载(只读)。缺失即响亮 —— 不代跑 blender 门。"""
    if not os.path.isfile(path):
        raise FileNotFoundError(
            "ledger_full.json 不存在: %s (真账由 G2 门产出: "
            "blender -b --python 3d/p1a_slice.py -- --g2)" % path)
    return L.load_ledger(path)


def build_print_view(led):
    # type: (dict) -> tuple
    """G2 打印视角重建(纯逻辑, 无 bpy): statuses/scope/处置与 run_g2 前奏
    同序 —— classify_full -> print_scope -> _ring_dedup_dispositions(处置标
    打在深拷贝副本上, 与 run_g2 的 deepcopy 纪律一致; 原账目不落标, 导出侧
    world_mesh 只按 statuses 取裁片折线)。返回 (statuses, scope_ids,
    buckets{桶: [id]}), 并断言宇宙闭合: scope ∪ 排除桶 == 全账 且不交。
    正确性由 tests/test_p4_section.py 的 central 零漂移测逐字节钉死。"""
    statuses = PS.classify_full(led["stones"])
    led_mark = copy.deepcopy(led)               # 处置标(params.clipped_by)不进原账
    sc = PS.print_scope(led_mark, statuses)
    arch_idx_of = {"ARCH%02d" % (i + 1): i for i in range(PS.G2_N_ARCH)}
    PS._ring_dedup_dispositions(led_mark, statuses, sc["scope"],
                                sc["buckets"], arch_idx_of)
    scope_ids = {s["id"] for s in sc["scope"]}
    buckets = {b: list(ids) for b, ids in sorted(sc["buckets"].items())}
    excluded_ids = {i for ids in buckets.values() for i in ids}
    all_ids = {s["id"] for s in led["stones"]}
    if scope_ids & excluded_ids:
        raise ValueError("build_print_view: scope 与排除桶相交 %d id"
                         % len(scope_ids & excluded_ids))
    if scope_ids | excluded_ids != all_ids:
        raise ValueError("build_print_view: 宇宙不闭合(scope+排除 != 全账, "
                         "差 %d)" % len(all_ids - (scope_ids | excluded_ids)))
    return statuses, scope_ids, buckets


def slice_section(led, scope_ids, zones=SEGMENT):
    # type: (dict, set, ...) -> dict
    """段切片(纯): zones ∩ G2 scope 的账目子集(保持原账序), meta 带 slice_zones。
    p1a_slice.slice_ledger 的多孔段推广(单孔=段特例); 不在 scope 的石不进包,
    由 pack 在 manifest.skipped 带原因补记。"""
    zs = set(zones)
    stones = [s for s in led["stones"]
              if s["id"].split(".")[0] in zs and s["id"] in scope_ids]
    if not stones:
        raise ValueError("slice_section: 空段 %r (zones x scope 无交集)"
                         % (tuple(zones),))
    meta = dict(led.get("meta", {}))
    meta["slice_zones"] = list(zones)
    return {"meta": meta, "stones": stones}


# ---------------------------------------------------------------- 留续清单

def deferred_plan(led, scope_ids, zones=SEGMENT):
    # type: (dict, set, ...) -> dict
    """留续清单(纯): 段外孔 = 账面孔全集 - 段孔(=12 孔, spec#4 M1c)。逐孔
    stones=账面石数, units=G2 打印单元数; unit_ids 全表(守恒 validator 的
    留续侧对账输入)。孔数非 12 或账面存在非 ARCH 孔即 raise(封版口径漂移响亮)。"""
    all_zones = sorted({s["id"].split(".")[0] for s in led["stones"]})
    if len(all_zones) != PS.G2_N_ARCH:
        raise ValueError("deferred_plan: 账面孔数 %d != %d (封版口径漂移?)"
                         % (len(all_zones), PS.G2_N_ARCH))
    zs = set(zones)
    if not zs <= set(all_zones):
        raise ValueError("deferred_plan: 段孔不在账面: %r" % sorted(zs - set(all_zones)))
    if not zs:
        raise ValueError("deferred_plan: 空段")
    dzones = [z for z in all_zones if z not in zs]
    per_zone = {}    # type: dict
    unit_ids = []    # type: list
    stones_total = 0
    for z in dzones:
        n_st = sum(1 for s in led["stones"] if s["id"].split(".")[0] == z)
        un = sorted(i for i in scope_ids if i.split(".")[0] == z)
        per_zone[z] = {"stones": n_st, "units": len(un)}
        stones_total += n_st
        unit_ids.extend(un)
    return {
        "meta": {"schema": SCHEMA, "section_zones": list(zones),
                 "note": "留续清单(spec#4 M1c): 段外 %d 孔只出清单不出包; "
                         "stones=账面石数, units=G2 打印单元数; 与 "
                         "section5 manifest.conservation 三方合账(validator "
                         "独立重算, 本清单是对账输入之一)" % len(dzones)},
        "n_holes": len(dzones),
        "zones": dzones,
        "per_zone": per_zone,
        "stones_total": stones_total,
        "units_total": len(unit_ids),
        "unit_ids": unit_ids,
    }


def write_deferred(doc, path=DEFERRED_PATH):
    # type: (dict, str) -> str
    """留续清单落盘(确定性 JSON, 两连跑逐字节同)。"""
    _write_json(doc, path)
    return path


# ---------------------------------------------------------------- 段包编排

def pack(led=None, view=None, out_dir=PACK_DIR, zones=SEGMENT,
         deferred_path=DEFERRED_PATH, scale=None):
    # type: (dict, tuple, str, ...) -> dict
    """段包出图(幂等): 切片 -> export_ledger(zones 二次过滤 belt) -> manifest
    增强(skipped 补全/slice 扩型/coupon 首件/conservation 汇总) -> 全树 3MF
    容器去时间 -> deferred_holes.json + PACK_REPORT.md。view=(statuses,
    scope_ids, buckets) 可传入已重建视角(测试/复算复用); 缺省自建。返回
    manifest dict。"""
    zones = tuple(zones)
    if led is None:
        led = load_full_ledger()
    if view is None:
        view = build_print_view(led)
    statuses, scope_ids, buckets = view
    sub = slice_section(led, scope_ids, zones)
    manifest = EP.export_ledger(sub, mesh_fn=PS._to_bed_mesh_fn(statuses),
                                out_dir=out_dir,
                                scale=PS.G2_SCALE if scale is None else scale,
                                zones=list(zones))
    # belt: 子账已按段切片, zones 二次过滤必须零 skip —— 有即切片/过滤漂移
    belt = [e for e in manifest["skipped"]
            if e.get("reason") == "zone_not_selected"]
    if belt:
        raise ValueError("pack: zones belt 拦到区外石 %d (切片与过滤不一致) 首3: %r"
                         % (len(belt), [e["id"] for e in belt[:3]]))

    # ---- skipped 补全: 段内未出件石逐条带 reason(不静默); role 过滤语义沿用 P1
    exported_ids = {s["id"] for s in manifest["stones"]}
    id2bucket = {i: b for b, ids in buckets.items() for i in ids}
    extra = []
    zs = set(zones)
    for s in led["stones"]:
        sid = s["id"]
        if sid.split(".")[0] not in zs or sid in exported_ids:
            continue
        if sid not in id2bucket:
            raise ValueError("pack: 段内石不在 scope 也不在排除账: %s" % sid)
        extra.append({"id": sid, "role": s.get("role_struct"),
                      "reason": "g2_excluded:" + id2bucket[sid]})
    manifest["skipped"] = sorted(manifest["skipped"] + extra,
                                 key=lambda e: e["id"])

    # ---- slice 扩型(向后兼容: 保留 zone 键=首孔语义并入 zones)
    roles = {}       # type: dict
    for s in sub["stones"]:
        roles[s["role_struct"]] = roles.get(s["role_struct"], 0) + 1
    manifest["slice"] = {
        "zones": list(zones),
        "zone": zones[0],
        "arch_idx": [int(z[4:]) - 1 for z in zones],
        "stones": len(manifest["stones"]),
        "roles": dict(sorted(roles.items())),
        "note": "代表段=中央五孔 1:50(spec#4 M1c); 其余 12 孔留续见 "
                "deferred_holes.json; RING=全深筒券楔(贯通东西), IMPOST=起拱"
                "线出挑(东西墙各一套), SPANDREL/BACK/CORE=链条石/背衬/牺牲芯",
    }

    # ---- coupon 首件约定(1:1 配合试片随包)
    coupons = EP.coupon_set(out_dir, scale=1.0)
    cdir = os.path.join(out_dir, "coupon")
    cfiles = sorted(os.path.join("coupon", f) for f in os.listdir(cdir))
    manifest["coupon"] = {
        "policy": "first_article",
        "scale": 1.0,
        "note": "每批首件打印前先以同档 coupon 成对试配(1:1 真尺寸, 非 1:50;"
                "缝=2x fit_print_mm 可直接实测); 档按该批首石 manifest.stones"
                "[].fit 取。",
        "tiers": {t: {"clearance_print_mm": coupons[t]["clearance_print_mm"],
                      "pair_gap_print_mm": coupons[t]["pair_gap_print_mm"]}
                  for t in sorted(coupons)},
        "files": cfiles,
    }

    # ---- conservation + 全段汇总(供关账把 ~913 估算修成实测)
    zone_stones = [s for s in led["stones"] if s["id"].split(".")[0] in zs]
    per_zone = {}
    for z in zones:
        zset = {s["id"] for s in zone_stones if s["id"].split(".")[0] == z}
        n_exp = sum(1 for s in manifest["stones"]
                    if s["id"].split(".")[0] == z)
        per_zone[z] = {"stones": len(zset), "exported": n_exp,
                       "skipped": len(zset) - n_exp}
    total_cm3 = sum(s["volume_cm3"] for s in manifest["stones"])
    mat_vol = {}     # type: dict
    mat_cnt = {}     # type: dict
    fit_cnt = {}     # type: dict
    for s in manifest["stones"]:
        mat_vol[s["material"]] = mat_vol.get(s["material"], 0.0) + s["volume_cm3"]
        mat_cnt[s["material"]] = mat_cnt.get(s["material"], 0) + 1
        fit_cnt[s["fit"]] = fit_cnt.get(s["fit"], 0) + 1
    overs = [b for b in manifest["batches"] if b.get("oversize")]
    manifest["conservation"] = {
        "identity": "zone_stones_total == exported + skipped (skipped 全带 "
                    "reason: role 过滤沿用 P1 无 reason; 其余 g2_excluded:<桶>)",
        "zone_stones_total": len(zone_stones),
        "exported": len(manifest["stones"]),
        "skipped": len(manifest["skipped"]),
        "per_zone": per_zone,
        "batches": len(manifest["batches"]),
        "volume_cm3_total": total_cm3,
        "volume_cm3_by_material": {k: mat_vol[k] for k in sorted(mat_vol)},
        "stones_by_material": {k: mat_cnt[k] for k in sorted(mat_cnt)},
        "fit_tiers": {k: fit_cnt[k] for k in sorted(fit_cnt)},
        "fit_diagonal_stones": sum(len(b.get("fit_diagonal", []))
                                   for b in manifest["batches"]),
        "oversize_stones": [i for b in overs for i in b["stones"]],
        "units_vs_estimate": {
            "estimate_spec": SPEC_ESTIMATE_UNITS,
            "note": "spec#4 M1 估 ~913 = 2747 x 0.332(单元率外推); 实测以 "
                    "exported 为准, 关账以本字段修正",
            "measured": len(manifest["stones"]),
            "delta": len(manifest["stones"]) - SPEC_ESTIMATE_UNITS,
        },
    }

    # ---- 幂等: created_utc 归空(时刻不落盘, 溯源归 git), 再确定性重写 manifest
    manifest["meta"]["created_utc"] = ""
    _write_json(manifest, os.path.join(out_dir, "manifest.json"))

    # ---- 3MF zip 容器去时间(内层 3D/3dmodel.model 零改动) -> 全树逐字节幂等
    for root, _dirs, files in os.walk(out_dir):
        for f in files:
            if f.endswith(".3mf"):
                _rezip_3mf(os.path.join(root, f))

    if deferred_path:
        write_deferred(deferred_plan(led, scope_ids, zones), deferred_path)
    report = _pack_report(manifest, zones)
    with open(os.path.join(out_dir, "PACK_REPORT.md"), "w",
              encoding="utf-8") as fh:
        fh.write(report)
    return manifest


# ---------------------------------------------------------------- 确定性工具

def _write_json(doc, path):
    # type: (dict, str) -> None
    """确定性原子写: sort_keys + indent=1(与 save_ledger 同约定)。"""
    d = os.path.dirname(os.path.abspath(path))
    if d:
        os.makedirs(d, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(tmp, path)


def _rezip_3mf(path):
    # type: (str) -> None
    """3MF zip 容器时间归一: ZipInfo 缺省带当前时刻, 两连跑容器字节必不同;
    按固定 date_time 重打包(成员顺序/内容/压缩约定不动)。"""
    with zipfile.ZipFile(path, "r") as zin:
        members = [(zi.filename, zin.read(zi.filename))
                   for zi in zin.infolist()]
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, data in members:
            zi = zipfile.ZipInfo(name, date_time=ZIP_FIXED_DATE)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            zout.writestr(zi, data)
    tmp = path + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(buf.getvalue())
    os.replace(tmp, path)


# ---------------------------------------------------------------- 报告

def _pack_report(manifest, zones):
    # type: (dict, ...) -> str
    """PACK_REPORT.md(确定性): 全段体积/件数汇总 + 分孔表 + spec 估算偏差表
    + 口径声明(供关账修正 ~913 为实测)。数字全部取自 manifest(单源)。"""
    cons = manifest["conservation"]
    est = cons["units_vs_estimate"]
    skipped_reasons = {}     # type: dict
    for e in manifest["skipped"]:
        r = e.get("reason", "role_filtered(P1 口径)")
        skipped_reasons[r] = skipped_reasons.get(r, 0) + 1
    rate_meas = cons["exported"] / float(cons["zone_stones_total"])
    delta_pct = 100.0 * est["delta"] / float(est["estimate_spec"])
    lines = [
        "# 十七孔桥·中央五孔 1:50 段包报告 (section5)",
        "",
        "段=ARCH07-11(spec#4 M1c 代表段); 其余 %d 孔留续见 deferred_holes.json"
        % (17 - len(zones)),
        "(留续清单语义即段外清单, 不出包)。片名口径: 十七孔桥·中央五孔 1:50。",
        "",
        "## 全段汇总(实测)",
        "",
        "| 项 | 值 |",
        "|---|---|",
        "| 段账面石 | %d |" % cons["zone_stones_total"],
        "| 打印单元(exported) | %d |" % cons["exported"],
        "| skipped(带 reason) | %d |" % cons["skipped"],
        "| 守恒 | %d = %d + %d |" % (cons["zone_stones_total"],
                                    cons["exported"], cons["skipped"]),
        "| 批数(220x220 床) | %d |" % cons["batches"],
        "| 总体积(打印件) | %.1f cm3 |" % cons["volume_cm3_total"],
    ]
    for m in sorted(cons["volume_cm3_by_material"]):
        lines.append("| %s 体积/件数 | %.1f cm3 / %d |"
                     % (m, cons["volume_cm3_by_material"][m],
                        cons["stones_by_material"][m]))
    lines += [
        "| fit 档分布 | %s |" % ", ".join(
            "%s %d" % (k, cons["fit_tiers"][k]) for k in sorted(cons["fit_tiers"])),
        "| fit_diagonal 斜置 | %d 件 |" % cons["fit_diagonal_stones"],
        "| oversize 独占批 | %d 件 |" % len(cons["oversize_stones"]),
        "",
        "## 预估偏差(spec#4 M1 估 ~913)",
        "",
        "| 口径 | 打印单元 | 段石率 |",
        "|---|---|---|",
        "| spec 估算(2747 x 0.332) | %d | 0.332 |" % est["estimate_spec"],
        "| 实测(本包) | %d | %.3f |" % (est["measured"], rate_meas),
        "| 偏差 | %+d | %+.1f%% |" % (est["delta"], delta_pct),
        "",
        "## 分孔",
        "",
        "| zone | 账面石 | 打印单元 | 排除 |",
        "|---|---|---|---|",
    ]
    for z in zones:
        pz = cons["per_zone"][z]
        lines.append("| %s | %d | %d | %d |"
                     % (z, pz["stones"], pz["exported"], pz["skipped"]))
    lines += [
        "",
        "## skipped 原因分布",
        "",
        "| reason | 件数 |",
        "|---|---|",
    ]
    for r in sorted(skipped_reasons):
        lines.append("| %s | %d |" % (r, skipped_reasons[r]))
    lines += [
        "",
        "## 口径",
        "",
        "- 1:50(scale=0.02); 打印件毫米 = 模型米 x 20; 床 220x220。",
        "- 装箱: 贪心货架 + 90° 归一 + 45° 对角斜置(P1A 约定, manifest.batches,",
        "  fit_diagonal 非独占批); 真放不下才 oversize 独占。",
        "- FIT 自动分档(块最小维): <0.3m TIGHT / <1.0m NORMAL / 否则 LOOSE;",
        "  clearance 双值见 manifest.stones(打印/模型)。",
        "- 体积=散度定理(耳切对角约定口径, 实心体上界); CORE 与面石有意重叠",
        "  (牺牲芯建模语义), 各族体积不可加和成净打印料。",
        "- 打印单元=G2 scope 口径(p1a_slice 纯逻辑重建, 与 G2 门时序同序;",
        "  零漂移由 tests/test_p4_section.py 对 central manifest 45fed1e8",
        "  manifest 语义/ledger_print 逐字节/STL 数值(1e-6mm, 负控在测)钉)。",
        "- coupon 首件约定: 每批首件打印前以同档 coupon 成对试配(1:1 真尺寸,",
        "  缝=2x fit_print_mm 可实测), 12 件见 coupon/。",
        "- 幂等: created_utc 归空(出包时刻不落盘, 溯源归 git); 3MF 容器时间",
        "  归一(内层 model 零改动) -> 两连跑全树逐字节同。",
        "",
        "## 复现",
        "",
        "```",
        "python3 3d/section_pack.py",
        "```",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------- 入口

def main(argv=None):
    # type: (Optional[list]) -> int
    ap = argparse.ArgumentParser(
        description="P4-T2 段包出图: 中央五孔(ARCH07-11)制造包 + 留续清单")
    ap.add_argument("--ledger", default=LEDGER_PATH, help="真账路径")
    ap.add_argument("--out", default=PACK_DIR, help="段包输出目录")
    ap.add_argument("--zones", default=",".join(SEGMENT),
                    help="段孔 CSV (默认 ARCH07..ARCH11)")
    ap.add_argument("--deferred-path", default=DEFERRED_PATH,
                    help="留续清单落盘路径")
    ap.add_argument("--no-deferred", action="store_true",
                    help="不写留续清单")
    args = ap.parse_args(argv)
    zones = tuple(z for z in args.zones.split(",") if z)
    led = load_full_ledger(args.ledger)
    view = build_print_view(led)
    manifest = pack(led=led, view=view, out_dir=args.out, zones=zones,
                    deferred_path=None if args.no_deferred
                    else args.deferred_path)
    cons = manifest["conservation"]
    est = cons["units_vs_estimate"]
    print("段包 section5: zones=%s" % ",".join(zones))
    print("  守恒: 段石 %d = 出件 %d + skipped %d (skipped 全带 reason)"
          % (cons["zone_stones_total"], cons["exported"], cons["skipped"]))
    print("  批数 %d | 总体积 %.1f cm3 (%s)"
          % (cons["batches"], cons["volume_cm3_total"],
             " / ".join("%s %.1f cm3 x%d" % (m, cons["volume_cm3_by_material"][m],
                                             cons["stones_by_material"][m])
                        for m in sorted(cons["volume_cm3_by_material"]))))
    print("  单元 vs spec 估 %d: %+d (实测率 %.3f)"
          % (est["estimate_spec"], est["delta"],
             cons["exported"] / float(cons["zone_stones_total"])))
    print("  -> %s" % os.path.abspath(args.out))
    if not args.no_deferred:
        doc = deferred_plan(led, view[1], zones)
        print("deferred: %d 孔 %d 石 %d 单元 -> %s"
              % (doc["n_holes"], doc["stones_total"], doc["units_total"],
                 os.path.abspath(args.deferred_path)))
    print("报告: %s" % os.path.abspath(os.path.join(args.out, "PACK_REPORT.md")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
