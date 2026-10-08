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

P4-T4 扩展(装配图+施工卡, 本文件装配段):
  - bed_layout: 分号位重放(纯)。export_ledger._pack_beds 只落批不落位,
    这里以同源足印(床平移网格 x/y 极距 - 2x clearance, 打印毫米)重放货架
    游标得逐单元床位(batch, slot, x, y, w, d, diag); 重放非权威 —— belt
    与 manifest.batches 逐项对账(批成员有序/fit_diagonal/used_mm 1e-6mm/
    oversize/批数), 装箱约定漂移即响亮(P1A 约定零改动的可执行钉)。
  - assembly_csvs: 每孔分号位表 CSV(确定性, 行=(batch,slot) 放置序,
    行数==该孔单元数; place_seq=sequence 事件号交叉引用)。
  - build_cards + card_lint: 施工卡 = sequence.json 原序过滤的段单元事件
    子序列(stage x event_range, 不重排), 逐行 [工程推断·非史料](装配/
    卸架序无史料锚, P2 关账口径); lint 判域独立(只查装配次序节序行),
    标签文法词表复用 narration_lint(_tag_ok)。卡由自身 lint 零发现才落盘。
  - assembly_main(blender 门): 每孔 assembly_ortho x5(直接复用
    p1a_slice.render_assembly, 同观感同约定) + 段总图(五孔世界位拼合,
    P1A 场景原语的组合 + 墩位缺口/M5(a) 底座端槽示意注记, 图注
    [设计选择]) + 上述 CSV/卡。PNG 落盘前去元数据块(渲染统计每次必变,
    像素零改动) -> 两连跑逐字节幂等。纯 python 路径 --assembly
    --cards-only 只出卡+CSV(不触 bpy)。
"""
import argparse
import copy
import csv
import io
import json
import math
import os
import struct
import sys
import zipfile
import zlib

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

# P4-T4 装配段产物位与口径
ASSEMBLY_DIR = os.path.join(PACK_DIR, "assembly")
CARDS_PATH = os.path.join(PACK_DIR, "construction_cards.md")
SEQ_PATH = os.path.join(OUT_DIR, "sequence.json")
ORDER_TAG = "[工程推断·非史料]"      # 装配/卸架序唯一允许的历史定性(P2 关账)
_CJK_FONT_PATH = "/System/Library/Fonts/Hiragino Sans GB.ttc"


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


# ═════════════════════════════════════════════════════════════════════════
# P4-T4: 分号位表 + 施工卡(sequence 子序列) + 装配图(blender 门)

def bed_layout(manifest, led, statuses):
    # type: (dict, dict, dict) -> dict
    """分号位重放(纯): 逐单元打印床位 {unit_id: {batch, slot, x, y, w, d,
    diag}}(毫米, 槽位左下角; diag=45° 斜置时为外接方)。export_ledger 的
    _pack_beds 只落批不落位, 本函数以【同源足印】重放同一货架游标:
    足印 = 床平移网格 x/y 极距 - 2x clearance(打印毫米, 与 export_ledger
    逐行同式); 游标推进 = EP._pack_beds 原式(90° 归一/45° 外接方/换行/
    换床)。重放非权威 —— belt 逐项对账 manifest.batches: 批成员(有序)/
    fit_diagonal/oversize/used_mm(<=1e-6mm)/批数, 任何漂移响亮 raise
    (P1A 装箱约定零改动纪律的可执行钉)。"""
    scale = float(manifest["meta"]["scale"])
    bed_mm = (float(manifest["meta"]["bed_mm"][0]),
              float(manifest["meta"]["bed_mm"][1]))
    by_id = {s["id"]: s for s in led["stones"]}
    mst = {s["id"]: s for s in manifest["stones"]}
    mesh_fn = PS._to_bed_mesh_fn(statuses)
    items = []       # type: list
    for rec in manifest["stones"]:              # 账序 = export 遍历序(平局序)
        sid = rec["id"]
        verts, _faces = mesh_fn(by_id[sid])
        ext = EP._extents_m(verts)
        cm = float(rec["clearance_model_mm"]) / 1000.0
        items.append((max(0.0, (ext[0] - 2 * cm) * scale * 1000.0),
                      max(0.0, (ext[1] - 2 * cm) * scale * 1000.0),
                      sid))
    # ---- 货架游标重放(EP._pack_beds 逐步同式, 位置只在原地可得)
    diag_lim = math.sqrt(2.0) * bed_mm[0] + 1e-9
    pos = {}         # type: dict
    batches = []     # type: list
    cur = None       # type: Optional[list]
    cx = cy = row_h = ux = uy = 0.0
    for w0, d0, key in sorted(items, key=lambda t: -max(t[0], t[1])):
        w, d = (d0, w0) if d0 > w0 else (w0, d0)   # 90° 旋转归一(长边横向)
        diag = False
        if max(w, d) > bed_mm[0]:                  # 90° 也救不了: 试 45°
            if w + d <= diag_lim:
                w = d = (w0 + d0) / math.sqrt(2.0)  # 45° 外接方
                diag = True
            else:
                batches.append({"batch": len(batches), "stones": [key],
                                "used_mm": [float(w0), float(d0)],
                                "oversize": True})
                pos[key] = {"batch": len(batches) - 1, "slot": 0,
                            "x": 0.0, "y": 0.0, "w": float(w0),
                            "d": float(d0), "diag": False}
                continue
        if cur is None:
            cur = []
            batches.append({"batch": len(batches), "stones": cur,
                            "used_mm": [0.0, 0.0], "oversize": False})
            cx = cy = row_h = ux = uy = 0.0
        if cx + w > bed_mm[0]:              # 换行(同床)
            cx, cy, row_h = 0.0, cy + row_h, 0.0
        if cy + d > bed_mm[1]:              # 床深满 -> 新批
            cur = []
            batches.append({"batch": len(batches), "stones": cur,
                            "used_mm": [0.0, 0.0], "oversize": False})
            cx = cy = row_h = ux = uy = 0.0
        pos[key] = {"batch": batches[-1]["batch"], "slot": len(cur),
                    "x": cx, "y": cy, "w": w, "d": d, "diag": diag}
        cur.append(key)
        if diag:
            batches[-1].setdefault("fit_diagonal", []).append(key)
        cx += w
        row_h = max(row_h, d)
        ux = max(ux, cx)
        uy = max(uy, cy + row_h)
        batches[-1]["used_mm"] = [float(ux), float(uy)]
    # ---- belt: 重放 vs manifest 逐项对账(装箱约定漂移即响亮)
    if len(batches) != len(manifest["batches"]):
        raise ValueError("bed_layout: 重放批数 %d != manifest %d"
                         % (len(batches), len(manifest["batches"])))
    for br, bm in zip(batches, manifest["batches"]):
        if br["stones"] != bm["stones"]:
            raise ValueError("bed_layout: 批 %d 成员/放置序漂移 重放 %r vs %r"
                             % (bm["batch"], br["stones"][:3], bm["stones"][:3]))
        if br.get("fit_diagonal", []) != bm.get("fit_diagonal", []):
            raise ValueError("bed_layout: 批 %d fit_diagonal 漂移" % bm["batch"])
        if br["oversize"] != bm["oversize"]:
            raise ValueError("bed_layout: 批 %d oversize 漂移" % bm["batch"])
        for a, b in zip(br["used_mm"], bm["used_mm"]):
            if abs(a - float(b)) > 1e-6:
                raise ValueError("bed_layout: 批 %d used_mm 漂移 %r vs %r"
                                 % (bm["batch"], br["used_mm"], bm["used_mm"]))
    return pos


_CSV_HEADER = ("unit_id", "batch", "slot", "bed_x_mm", "bed_y_mm",
               "foot_w_mm", "foot_d_mm", "fit_diagonal", "fit", "role",
               "material", "place_seq")


def assembly_csvs(manifest, bed, seq_of, out_dir=ASSEMBLY_DIR):
    # type: (dict, dict, dict, str) -> list
    """每孔分号位表 CSV(确定性): unit id->batch->床位。行序 = (batch, slot)
    放置序; 行数 == 该孔打印单元数; place_seq = sequence.json 中该单元
    PLACE_STONE 事件号(施工卡装配序交叉引用, build_cards 给出)。"""
    os.makedirs(out_dir, exist_ok=True)
    mst = {s["id"]: s for s in manifest["stones"]}
    paths = []
    for zone in manifest["slice"]["zones"]:
        rows = []
        for s in manifest["stones"]:
            if s["id"].split(".")[0] != zone:
                continue
            if s["id"] not in seq_of:
                raise ValueError("assembly_csvs: 单元无 sequence 事件 %s"
                                 % s["id"])
            rows.append((bed[s["id"]]["batch"], bed[s["id"]]["slot"],
                         s["id"]))
        rows.sort(key=lambda r: (r[0], r[1]))
        path = os.path.join(out_dir, zone + ".csv")
        with open(path, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh, lineterminator="\n")
            w.writerow(_CSV_HEADER)
            for _b, _sl, sid in rows:
                p, m = bed[sid], mst[sid]
                w.writerow([sid, p["batch"], p["slot"],
                            "%.2f" % p["x"], "%.2f" % p["y"],
                            "%.2f" % p["w"], "%.2f" % p["d"],
                            int(p["diag"]), m["fit"], m["role"],
                            m["material"], seq_of[sid]])
        paths.append(path)
    return paths


# ---------------------------------------------------------------- 施工卡

def card_order_rows(text):
    # type: (str) -> list
    """施工卡装配序行解析: [(stage_id, seq:int, unit_id, raw_line), ...]
    (文件序)。只认『## 装配次序』节内首格为整数的表数据行 —— 表头/分隔行/
    批次总表行不算序行。lint 与测试共用本解析器; 测试侧以 sequence.json
    独立重算的期望子序列对账(解析器若有漏/重排, 对账必红)。"""
    out = []
    stage = None      # type: Optional[str]
    in_order = False
    for ln in text.splitlines():
        if ln.startswith("### "):
            stage = ln[4:].split()[0]
            continue
        if ln.startswith("## "):
            in_order = "装配次序" in ln
            continue
        if in_order and ln.startswith("| "):
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if cells and cells[0].isdigit():
                out.append((stage, int(cells[0]), cells[1], ln))
    return out


def card_lint(text):
    # type: (str) -> list
    """施工卡小 lint(判域独立): 『装配次序』节每个序断言行必须含字面标注
    [工程推断·非史料](装配/卸架序无史料锚, P2 关账口径), 且行内全部方括
    号标签过 narration 标签文法词表(_tag_ok: 精确表或 '工程推断' 前缀)。
    词表复用 narration_lint, 判域不复用 —— narration 三闸(G0 编号/禁词/
    引语)面向口播稿, 对制造卡是假阳性面(选择理由, 报告同文)。返回发现
    表(字符串), 空=绿; lint 不跑不构绿(qa_l2 I4 同纪律)。"""
    import narration as NR
    bad = []
    for _stage, _seq, _unit, ln in card_order_rows(text):
        if ORDER_TAG not in ln:
            bad.append("ORDER_ROW_UNTAGGED: %s" % ln[:96])
        for t in NR._tags(ln):
            if not NR._tag_ok(t):
                bad.append("TAG_NOT_IN_VOCAB %r: %s" % (t, ln[:96]))
    return bad


def build_cards(manifest, seqdoc, bed, path=CARDS_PATH):
    # type: (dict, dict, dict, str) -> tuple
    """施工卡(确定性 md): 批次总表(今日打印, 每行=一床) + 装配次序(今日
    粘接) = sequence.json【原序过滤】的段单元事件子序列 —— stage 依
    sequence 给定序, 事件依 event_range 原序, stone_id ∈ 段打印单元;
    不重排(tests/test_p4_section.py 独立重算对账钉)。每序行带
    [工程推断·非史料]; 自身 card_lint 零发现才落盘。返回 (path, seq_of)
    —— seq_of: unit_id -> 事件 seq(分号位表 place_seq 交叉引用)。"""
    units = {s["id"] for s in manifest["stones"]}
    evs = seqdoc["events"]
    seq_of = {}      # type: dict
    plan = []        # type: list
    for st in seqdoc["sequence"]:
        lo, hi = st["event_range"]
        hits = [(int(evs[i]["seq"]), evs[i]["stone_id"])
                for i in range(lo - 1, hi)
                if evs[i].get("stone_id") in units]
        for q, sid in hits:
            if sid in seq_of:
                raise ValueError("build_cards: 单元多事件 %s (seq %d/%d)"
                                 % (sid, seq_of[sid], q))
            seq_of[sid] = q
        if hits:
            plan.append((st["id"], st["stage"], lo, hi, hits))
    if len(seq_of) != len(units):
        missing = sorted(units - set(seq_of))[:5]
        raise ValueError("build_cards: 段单元 %d/%d 无 sequence 事件, 首5 %r"
                         % (len(units) - len(seq_of), len(units), missing))
    missing_bed = sorted(sid for sid in seq_of if sid not in bed)
    if missing_bed:
        raise ValueError("build_cards: 床位表缺单元 %d, 首5 %r"
                         % (len(missing_bed), missing_bed[:5]))
    bed_of = bed
    # ---- 批次总表(每行=一床; 单元清单/床位=分号位表 CSV 权威, 不重复列)
    b2z = {}         # type: dict
    b2n = {}         # type: dict
    for s in manifest["stones"]:
        b = s["batch"]
        b2n[b] = b2n.get(b, 0) + 1
        b2z.setdefault(b, set()).add(s["id"].split(".")[0])
    lines = [
        "# 中央五孔段 施工卡 (section5 · construction cards)",
        "",
        "数据源: 3d/out/sequence.json (P2 交付: %d stage/%d 事件) x "
        "3d/out/print/section5/manifest.json (%d 打印单元/%d 批)"
        % (len(seqdoc["sequence"]), len(evs), len(units),
           len(manifest["batches"])),
        "对照账: 3d/out/ledger_full.json",
        "生成命令: blender -b --python 3d/section_pack.py -- --assembly",
        "回放: python3 3d/section_pack.py --assembly --cards-only "
        "(只出本卡+分号位表, 不渲染)",
        "口径: 装配次序 = sequence 原序过滤的段单元事件子序列"
        " (%d/%d 单元全覆盖, 恰一次, 不重排); 批次 = 220x220 打印床分批"
        % (len(seq_of), len(units)),
        "口径: 每孔装配图 = out/print/section5/assembly/ARCHxx.png"
        " (assembly_ortho 模式, P1A 同款); 段总图 = 同目录"
        " section_overview.png (墩位缺口/M5(a) 底座端槽示意, 图注"
        " [设计选择]); 床位权威 = 分号位表 assembly/ARCHxx.csv",
        "",
        "## 批次总表 (今日打印 — 每行=一床)",
        "",
        "| batch | 孔 | 单元数 | 床位占用 mm | 分号位表 |",
        "|---|---|---|---|---|",
    ]
    for b in sorted(b2n):
        um = manifest["batches"][b]["used_mm"]
        lines.append("| %d | %s | %d | %.1fx%.1f | %s |"
                     % (b, "+".join(sorted(b2z[b])), b2n[b], um[0], um[1],
                        "+".join(sorted("assembly/%s.csv" % z
                                        for z in b2z[b]))))
    lines += [
        "",
        "## 装配次序 (今日粘接 — sequence 子序列, %d stage/%d 行; "
        "行序=粘接序)" % (len(plan), len(seq_of)),
        "",
        "序声明: 本节每行均为装配次序断言 [工程推断·非史料](无工序史料锚,"
        " P2 关账口径; sequence 事件原序, 不重排)。",
        "",
    ]
    for sid_, stage, lo, hi, hits in plan:
        lines.append("### %s %s (events %d-%d)" % (sid_, stage, lo, hi))
        lines.append("")
        lines.append("| seq | 单元 | 批 | 床位(x,y) mm | 标注 |")
        lines.append("|---|---|---|---|---|")
        for q, uid in hits:
            p = bed_of[uid]
            lines.append("| %d | %s | %d | %.2f,%.2f | %s |"
                         % (q, uid, p["batch"], p["x"], p["y"], ORDER_TAG))
        lines.append("")
    text = "\n".join(lines)
    findings = card_lint(text)
    if findings:
        raise ValueError("build_cards: card_lint 非零 %r" % findings[:5])
    _write_text(text + "\n", path)
    return path, seq_of


def _write_text(text, path):
    # type: (str, str) -> None
    """确定性原子写文本(utf-8, 与 _write_json 同原子约定)。"""
    d = os.path.dirname(os.path.abspath(path))
    if d:
        os.makedirs(d, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, path)


# ---------------------------------------------------------------- blender

_PNG_KEEP = (b"IHDR", b"PLTE", b"IDAT", b"IEND")


def png_strip_meta(path):
    # type: (str) -> str
    """PNG 去元数据块(tEXt/iTXt/tIME 等 —— blender 渲染统计每次运行必变,
    IDAT 像素流不动): 仅保留 IHDR/PLTE/IDAT/IEND 重写。逐块 CRC 重验
    (坏块响亮)。像素零改动 -> 固定 seed 渲染两连跑逐字节幂等可证。"""
    with open(path, "rb") as fh:
        buf = fh.read()
    if buf[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("png_strip_meta: 非 PNG %s" % path)
    out = [buf[:8]]
    i = 8
    while i + 12 <= len(buf):
        (ln,) = struct.unpack(">I", buf[i:i + 4])
        typ = buf[i + 4:i + 8]
        data = buf[i + 8:i + 8 + ln]
        (crc,) = struct.unpack(">I", buf[i + 8 + ln:i + 12 + ln])
        if zlib.crc32(typ + data) & 0xFFFFFFFF != crc:
            raise ValueError("png_strip_meta: CRC 不符 %s @%d" % (path, i))
        if typ in _PNG_KEEP:
            out.append(buf[i:i + 12 + ln])
        i += 12 + ln
        if typ == b"IEND":
            break
    else:
        raise ValueError("png_strip_meta: 无 IEND %s" % path)
    tmp = path + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(b"".join(out))
    os.replace(tmp, path)
    return path


def _load_cjk_font():
    # type: () -> object
    """中文字体(blender FONT); 失败返 None(调用方降级 ASCII 标注)。"""
    import bpy
    if not os.path.isfile(_CJK_FONT_PATH):
        return None
    try:
        return bpy.data.fonts.load(_CJK_FONT_PATH)
    except Exception:
        return None


def _text(sc, body, loc, size, font=None, rgb=(0.05, 0.05, 0.05)):
    # type: (object, str, tuple, float, object, tuple) -> object
    """文字标注(P1A _add_text 同构 + 可选中文字体; 相机 -Y 同口径)。"""
    import bpy
    cu = bpy.data.curves.new("lbl", type='FONT')
    cu.body = body
    cu.size = size
    cu.align_x = 'CENTER'
    cu.align_y = 'CENTER'
    if font is not None:
        cu.font = font
    ob = bpy.data.objects.new("lbl_" + body, cu)
    ob.location = loc
    ob.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    sc.collection.objects.link(ob)
    ob.data.materials.append(PS._flat_mat("label", rgb))
    return ob


def _quad(sc, name, x0, x1, z0, z1, y, rgb):
    # type: (object, str, float, float, float, float, float, tuple) -> object
    """x-z 前脸薄面注记块(发射材质, P1A _flat_mat 同源)。"""
    import bpy
    me = bpy.data.meshes.new(name)
    me.from_pydata([(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)],
                   [], [(0, 1, 2, 3)])
    me.validate()
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob)
    ob.data.materials.append(PS._flat_mat(name, rgb))
    return ob


def _outline(sc, name, x0, x1, z0, z1, y, rgb, t=0.05):
    # type: (object, str, float, float, float, float, float, tuple, float) -> None
    """矩形描边(4 细条, 注记线框)。"""
    _quad(sc, name + ".b", x0, x1, z0, z0 + t, y, rgb)
    _quad(sc, name + ".t", x0, x1, z1 - t, z1, y, rgb)
    _quad(sc, name + ".l", x0, x0 + t, z0, z1, y, rgb)
    _quad(sc, name + ".r", x1 - t, x1, z0, z1, y, rgb)


def render_section_assembly(led_slice, statuses, out_png, res_x=4800):
    # type: (dict, dict, str, int) -> str
    """段总图(blender): 五孔按世界位拼合的 -Y 正射侧视(P1A render_assembly
    同观感: 同 role 配色/同相机口径/同发射平面) + 段级注记: 墩位缺口(相邻
    孔 x 间隙带 = 段内不打印区, 留续) + M5(a) 底座端槽示意(底座不打印,
    只出 BASE_SPEC 规格) + 图注 [设计选择]。P1A 无段级函数可复用, 本体=
    其场景原语(world_mesh/_flat_mat/_ROLE_RGB)的组合; 标注色彩/字高为
    设计选择。"""
    import bpy
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    stones = led_slice["stones"]
    wv = []      # 全局包围盒
    zext = {}    # zone -> [x0, x1, z_impost_top, z_top, ring_x0, ring_x1]
    for s in stones:
        verts, faces = PS.world_mesh(s, statuses)
        me = bpy.data.meshes.new(s["id"])
        me.from_pydata([tuple(v) for v in verts], [],
                       [tuple(f) for f in faces])
        me.validate()
        ob = bpy.data.objects.new(s["id"], me)
        sc.collection.objects.link(ob)
        role = s["role_struct"]
        ob.data.materials.append(PS._flat_mat(
            role, PS._ROLE_RGB.get(role, (0.5, 0.5, 0.5))))
        wv.extend(verts)
        z = s["id"].split(".")[0]
        e = zext.setdefault(z, [float("inf"), float("-inf"),
                                float("-inf"), float("-inf"),
                                float("inf"), float("-inf")])
        xs = [v[0] for v in verts]
        zs = [v[2] for v in verts]
        e[0] = min(e[0], min(xs))
        e[1] = max(e[1], max(xs))
        e[3] = max(e[3], max(zs))
        if role == "IMPOST":
            e[2] = max(e[2], max(zs))
        if role == "RING":
            e[4] = min(e[4], min(xs))
            e[5] = max(e[5], max(xs))
    xs = [v[0] for v in wv]
    zs = [v[2] for v in wv]
    x0, x1, z0, z1 = min(xs), max(xs), min(zs), max(zs)
    y_f = min(v[1] for v in wv) - 0.08
    xr = x1 - x0
    # ---- 注记: 墩位缺口 + M5(a) 底座端槽示意 + 图注([设计选择])
    font = _load_cjk_font()
    if font is not None:
        caption = ("中央五孔 1:50 段总图 | 墩位缺口=留续不打印 | "
                   "M5(a) 底座不打印·端槽为示意 [设计选择]")
        pier_lbl, slot_lbl = "墩位·留续", "端槽(示意)"
    else:
        caption = ("section 1:50 | pier gaps deferred (not printed) | "
                   "M5(a) base end-slot schematic [DESIGN CHOICE]")
        pier_lbl, slot_lbl = "PIER deferred", "SLOT (schem.)"
    rgb_pier = (0.82, 0.22, 0.18)
    rgb_base = (0.30, 0.45, 0.72)
    b_bot, b_top = z0 - 0.75, z0 - 0.10
    bx0, bx1 = x0 - 1.2, x1 + 1.2
    _outline(sc, "base", bx0, bx1, b_bot, b_top, y_f, rgb_base,
             t=max(0.05, xr * 0.0012))
    slot_w, m = 0.9, 0.35
    for sx0 in (bx0 + m, bx1 - m - slot_w):
        _quad(sc, "slot", sx0, sx0 + slot_w, b_bot + 0.12, b_top - 0.02,
              y_f, rgb_base)
        _text(sc, slot_lbl, (sx0 + slot_w / 2.0, y_f, b_top + 0.32),
              xr * 0.011, font)
    zones = sorted(zext)
    for i in range(len(zones) - 1):
        a, b = zext[zones[i]], zext[zones[i + 1]]
        # 墩位带 = 相邻孔【券环外缘】之间(zone 石 x 范围含拱上背衬, 相邻孔
        # 互叠 ~2.2m, 不能作锚; 券环外缘即立面可见的孔边, 之间是墩体)
        gx0, gx1 = a[5], b[4]
        if gx1 - gx0 <= 0.05:
            raise ValueError(
                "render_section_assembly: 券环外缘间隙异常 %s/%s gap=%.3f"
                % (zones[i], zones[i + 1], gx1 - gx0))
        top = min(a[2] if a[2] > float("-inf") else a[3],
                  b[2] if b[2] > float("-inf") else b[3])
        _outline(sc, "pier", gx0, gx1, b_top, top, y_f, rgb_pier,
                 t=max(0.05, xr * 0.0012))
        _text(sc, pier_lbl, ((gx0 + gx1) / 2.0, y_f, b_top - 0.42),
              xr * 0.011, font, rgb_pier)
    for z in zones:
        e = zext[z]
        _text(sc, z, ((e[0] + e[1]) / 2.0, y_f, e[3] + xr * 0.028),
              xr * 0.018, font)
    _text(sc, caption, ((x0 + x1) / 2.0, y_f, b_bot - xr * 0.020),
          xr * 0.013, font)
    # ---- 相机/渲染(P1A 同口径: -Y 正射, Cycles 1 sample, 透明底)
    ax0, ax1 = bx0 - 0.5, bx1 + 0.5
    az0, az1 = b_bot - xr * 0.055, z1 + xr * 0.055
    cd = bpy.data.cameras.new("Ortho")
    cd.type = 'ORTHO'
    cd.ortho_scale = (ax1 - ax0) * 1.04
    cd.clip_end = 2000.0
    cam = bpy.data.objects.new("Ortho", cd)
    sc.collection.objects.link(cam)
    cam.location = ((ax0 + ax1) / 2.0, -500.0, (az0 + az1) / 2.0)
    cam.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    sc.camera = cam
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 1
    try:
        cp = bpy.context.preferences.addons['cycles'].preferences
        cp.compute_device_type = 'METAL'
        for dv in cp.devices:
            dv.use = (dv.type == 'METAL')
        sc.cycles.device = 'GPU'
    except Exception:
        sc.cycles.device = 'CPU'
    sc.render.resolution_x = res_x
    sc.render.resolution_y = int(res_x * (az1 - az0) / (ax1 - ax0) * 1.06)
    sc.render.film_transparent = True
    sc.render.filepath = out_png
    bpy.ops.render.render(write_still=True)
    print("SECTION_ASSEMBLY_PNG written %s (%dx%d)"
          % (out_png, sc.render.resolution_x, sc.render.resolution_y))
    return out_png


def assembly_main(argv=None):
    # type: (Optional[list]) -> int
    """P4-T4 装配门。blender: blender -b --python 3d/section_pack.py --
    --assembly (每孔 assembly_ortho x5 + 段总图 + 分号位表 x5 + 施工卡);
    纯 python: python3 3d/section_pack.py --assembly --cards-only (只出
    卡+CSV, 不触 bpy)。状态账/网格全纯逻辑(blender 内与 G2 同序重建),
    bpy 只用于场景/渲染。"""
    if argv is None:
        argv = (sys.argv[sys.argv.index("--") + 1:]
                if "--" in sys.argv else sys.argv[1:])
    ap = argparse.ArgumentParser(
        description="P4-T4 装配图(每孔+段总图)+施工卡(sequence 子序列)")
    ap.add_argument("--assembly", action="store_true",
                    help="装配门分派标记(两种入口兼容)")
    ap.add_argument("--cards-only", action="store_true",
                    help="只出分号位表+施工卡(纯 python 可跑)")
    ap.add_argument("--ledger", default=LEDGER_PATH)
    ap.add_argument("--manifest", default=os.path.join(PACK_DIR,
                                                       "manifest.json"))
    ap.add_argument("--sequence", default=SEQ_PATH)
    ap.add_argument("--out-dir", default=ASSEMBLY_DIR)
    ap.add_argument("--cards", default=CARDS_PATH)
    ap.add_argument("--resx", type=int, default=3200)
    ap.add_argument("--overview-resx", type=int, default=4800)
    args = ap.parse_args(argv)
    led = load_full_ledger(args.ledger)
    statuses, scope_ids, _buckets = build_print_view(led)
    with open(args.manifest, encoding="utf-8") as fh:
        manifest = json.load(fh)
    if manifest["slice"]["zones"] != list(SEGMENT):
        raise ValueError("assembly_main: manifest 段孔 %r != %r"
                         % (manifest["slice"]["zones"], list(SEGMENT)))
    if manifest["meta"].get("curve_hash") != led["meta"].get("curve_hash"):
        raise ValueError("assembly_main: manifest curve_hash 与真账不符")
    with open(args.sequence, encoding="utf-8") as fh:
        seqdoc = json.load(fh)
    bed = bed_layout(manifest, led, statuses)
    _cards, seq_of = build_cards(manifest, seqdoc, bed, args.cards)
    csvs = assembly_csvs(manifest, bed, seq_of, args.out_dir)
    print("施工卡: %s" % os.path.abspath(args.cards))
    print("分号位表: %s" % ", ".join(os.path.basename(p) for p in csvs))
    if args.cards_only:
        return 0
    zones = manifest["slice"]["zones"]
    for zone in zones:
        sub = slice_section(led, scope_ids, (zone,))
        png = os.path.join(args.out_dir, zone + ".png")
        PS.render_assembly(sub, statuses, png, res_x=args.resx)
        png_strip_meta(png)
    sub5 = slice_section(led, scope_ids, SEGMENT)
    png5 = os.path.join(args.out_dir, "section_overview.png")
    render_section_assembly(sub5, statuses, png5, res_x=args.overview_resx)
    png_strip_meta(png5)
    return 0


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
    if "--assembly" in sys.argv:
        sys.exit(assembly_main())
    sys.exit(main())
