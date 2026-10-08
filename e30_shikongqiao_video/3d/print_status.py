# -*- coding: utf-8 -*-
"""P4-T5 进度账状态机: 中央五孔段打印/装配的断点续跑账 (print_status.json)。

接口(plan T5): CLI 三命令
  init    --manifest M --out S [--force]   从 manifest 初始化全 pending
  advance --status S --unit U --to PH [--batch N]
                                           推进相位; redo→pending 可携 --batch
                                           重打改派; 非法迁移 raise(不落盘)
  query   --status S [--phase PH]          stdout JSON (counts/units, 排序确定)

相位迁移表(表驱动, 唯一事实源; 全迁移经 TRANSITIONS 校验):
  pending --→ printed --→ checked --→ glued   (待打/已打/已检/已装=粘接装配)
                └──→ redo --→ pending         (重打改派: 件报废回待打, 可改批次)
非法迁移/未知相位/未知单元/改派窗口错用 → IllegalTransition/ValueError, 状态文件
字节不动。glued 语义 = 施工卡(construction_cards.md)"今日粘接"行的装配完成;
单元批次号单源 = manifest.stones[].batch(与施工卡批次总表同源)。

幂等落盘纪律: 状态内容零时间戳(排序键+固定缩进+尾换行), 同态两连跑逐字节同;
原子写(同目录临时文件+os.replace)。schema 版本头 {schema:1, kind:"print_status"}
由 validate_status 把门; manifest 路径按原样登记(幂等要求同参数重跑)。

用法:
  python3 3d/print_status.py init  --manifest 3d/out/print/section5/manifest.json \
      --out 3d/out/print/section5/print_status.json
  python3 3d/print_status.py advance --status ... --unit ARCH09.EAST.RING.C00.B00 --to printed
  python3 3d/print_status.py query  --status ... [--phase checked]
"""
import argparse
import json
import os
import sys
import tempfile

SCHEMA_VERSION = 1
KIND = "print_status"

PENDING = "pending"      # 待打
PRINTED = "printed"      # 已打(下床待检)
CHECKED = "checked"      # 已检(首件 coupon/尺寸/printcheck 过)
GLUED = "glued"          # 已装(粘接到装配体, 对账施工卡"今日粘接")
REDO = "redo"            # 重打(报废待重打)

PHASES = (PENDING, PRINTED, CHECKED, GLUED, REDO)

# 全迁移表: 相位 → 允许的目标相位集(表驱动唯一事实源, advance 只认此表)。
TRANSITIONS = {
    PENDING: frozenset((PRINTED,)),
    PRINTED: frozenset((CHECKED, REDO)),
    REDO: frozenset((PENDING,)),
    CHECKED: frozenset((GLUED,)),
    GLUED: frozenset(),
}


class IllegalTransition(ValueError):
    """非法相位迁移(TRANSITIONS 表外)。"""


# ---------------------------------------------------------------- 核心

def validate_status(doc):
    # type: (dict) -> dict
    """schema 版本头把门: 结构/相位词汇合法, 返回原 doc。"""
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA_VERSION:
        raise ValueError("print_status: schema 版本头缺失/不支持: %r"
                         % (doc.get("schema") if isinstance(doc, dict) else doc))
    if doc.get("kind") != KIND:
        raise ValueError("print_status: kind 不符: %r" % (doc.get("kind"),))
    units = doc.get("units")
    if not isinstance(units, dict) or not units:
        raise ValueError("print_status: units 缺失或为空")
    for uid, u in units.items():
        if u.get("phase") not in PHASES:
            raise ValueError("print_status: 单元 %s 相位非法: %r"
                             % (uid, u.get("phase")))
        if not isinstance(u.get("history"), list):
            raise ValueError("print_status: 单元 %s history 缺失" % uid)
    return doc


def load_status(path):
    # type: (str) -> dict
    with open(path, encoding="utf-8") as f:
        return validate_status(json.load(f))


def save_status(doc, path):
    # type: (dict, str) -> str
    """幂等落盘(排序键/固定缩进/零时间戳) + 原子写(同目录 tmp + os.replace)。"""
    text = json.dumps(doc, ensure_ascii=False, sort_keys=True, indent=1) + "\n"
    d = os.path.dirname(os.path.abspath(path))
    if not os.path.isdir(d):
        os.makedirs(d)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".print_status.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    return path


def init_status(manifest, manifest_ref):
    # type: (dict, str) -> dict
    """从 manifest 初始化: 全单元 pending, 批次/材质随 manifest.stones 单源。"""
    stones = manifest.get("stones")
    if not isinstance(stones, list) or not stones:
        raise ValueError("init_status: manifest 无 stones 清单")
    units = {}
    for s in stones:
        uid = s.get("id")
        if not uid:
            raise ValueError("init_status: manifest stone 缺 id: %r" % (s,))
        if uid in units:
            raise ValueError("init_status: manifest 单元重复: %s" % uid)
        if "batch" not in s:
            raise ValueError("init_status: manifest 单元缺 batch: %s" % uid)
        units[uid] = {
            "phase": PENDING,
            "batch": int(s["batch"]),
            "material": s.get("material"),
            "zone": uid.split(".")[0],
            "history": [{"op": "init", "to": PENDING}],
        }
    return {
        "schema": SCHEMA_VERSION,
        "kind": KIND,
        "manifest": manifest_ref,
        "units": units,
    }


def advance_unit(doc, unit_id, to_phase, batch=None):
    # type: (dict, str, str, int | None) -> dict
    """按 TRANSITIONS 表推进单相位; 非法 raise 且不改动任何字段。

    redo→pending 允许携 batch(重打改派批次); 其余迁移携 batch 一律 raise。
    """
    validate_status(doc)
    units = doc["units"]
    u = units.get(unit_id)
    if u is None:
        raise ValueError("advance_unit: 未知单元: %s" % unit_id)
    if to_phase not in TRANSITIONS:
        raise ValueError("advance_unit: 未知相位: %r" % (to_phase,))
    cur = u["phase"]
    if to_phase not in TRANSITIONS[cur]:
        raise IllegalTransition(
            "advance_unit: 非法迁移 %s: %s -> %s (合法: %s)"
            % (unit_id, cur, to_phase,
               "|".join(sorted(TRANSITIONS[cur])) or "无"))
    if batch is not None:
        if not (cur == REDO and to_phase == PENDING):
            raise ValueError(
                "advance_unit: 改派 batch 仅限 redo->pending (现态 %s)" % cur)
        old_batch = u["batch"]
        u["batch"] = int(batch)
        u["history"].append({"op": "reassign", "batch": int(batch),
                             "from_batch": old_batch})
    u["history"].append({"op": "advance", "from": cur, "to": to_phase})
    u["phase"] = to_phase
    return doc


def query(doc, phase=None):
    # type: (dict, str | None) -> dict
    """counts(全相位补零) + units(排序确定); phase 给定时只留该相位单元。"""
    validate_status(doc)
    if phase is not None and phase not in PHASES:
        raise ValueError("query: 未知相位: %r" % (phase,))
    units = doc["units"]
    counts = {p: 0 for p in PHASES}
    for u in units.values():
        counts[u["phase"]] += 1
    ids = sorted(uid for uid, u in units.items()
                 if phase is None or u["phase"] == phase)
    return {"total": len(units), "counts": counts, "units": ids}


# ---------------------------------------------------------------- CLI

def _die(msg):
    # type: (str) -> int
    sys.stderr.write("print_status: error: %s\n" % msg)
    return 1


def main(argv=None):
    # type: (list | None) -> int
    ap = argparse.ArgumentParser(
        prog="print_status.py", description="P4 段包进度账状态机")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="从 manifest 初始化全 pending")
    p_init.add_argument("--manifest", required=True)
    p_init.add_argument("--out", required=True)
    p_init.add_argument("--force", action="store_true",
                        help="覆盖已存在的状态文件(默认拒绝, 防误吞进度)")

    p_adv = sub.add_parser("advance", help="推进单元相位")
    p_adv.add_argument("--status", required=True)
    p_adv.add_argument("--unit", required=True)
    p_adv.add_argument("--to", required=True, choices=list(PHASES))
    p_adv.add_argument("--batch", type=int, default=None,
                       help="重打改派批次(仅 redo->pending)")

    p_q = sub.add_parser("query", help="查询进度(stdout JSON)")
    p_q.add_argument("--status", required=True)
    p_q.add_argument("--phase", default=None, choices=list(PHASES))

    args = ap.parse_args(argv)
    try:
        if args.cmd == "init":
            if os.path.exists(args.out) and not args.force:
                return _die("状态文件已存在(防误吞进度, 覆盖请加 --force): %s"
                            % args.out)
            with open(args.manifest, encoding="utf-8") as f:
                man = json.load(f)
            doc = init_status(man, args.manifest)
            save_status(doc, args.out)
            sys.stdout.write("init: %d units -> %s\n"
                             % (len(doc["units"]), args.out))
            return 0
        if args.cmd == "advance":
            doc = load_status(args.status)
            advance_unit(doc, args.unit, args.to, batch=args.batch)
            save_status(doc, args.status)
            sys.stdout.write("advance: %s -> %s\n" % (args.unit, args.to))
            return 0
        if args.cmd == "query":
            doc = load_status(args.status)
            sys.stdout.write(json.dumps(query(doc, phase=args.phase),
                                        ensure_ascii=False, sort_keys=True,
                                        indent=1) + "\n")
            return 0
        return _die("未知命令: %r" % (args.cmd,))
    except (ValueError, OSError) as e:
        return _die(str(e))


if __name__ == "__main__":
    sys.exit(main())
