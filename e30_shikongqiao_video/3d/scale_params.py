# e30_shikongqiao_video/3d/scale_params.py
# -*- coding: utf-8 -*-
"""P4-T1 薄特征审计(1:50 打印当量口径)+ CLI 落 thin_features.json。

口径区分(两句话, 互引):
- 本审计 = 块级打印可打印性粗筛: 石块族网格 bbox 最小维 x scale x 1000(打印
  当量毫米) < floor_mm(默认 1.2) 的块列清单 —— 问"整块有没有薄到打不出来";
  另列面浮雕细部(face_sliver, 如出墙面 proud): 块体可印、sub-floor 细部打印
  后损失, 供 M3/外观处置决策。
- printcheck.check_stone 的 THIN_WALL = 模型侧流形壁厚判据(post-inset 网格
  逐轴 bbox + 面片对代理 W1) —— 问"网格上有没有薄壁"。两口径互为粗筛/精检,
  本模块不复算也不替代 printcheck(见 printcheck.py 模块头)。

dims 口径: 与 export_print 同一取法, 不另立第二套 —— 族网格顶点 bbox 轴向
极差(_extents_m), 网格经 families.family_mesh(params) 单源获取(与
export_print.materialize 默认路径同源; 账内 transform 旋转分量全零, 平移不
改极差, 局部极差=世界极差, tests/test_p4_scale.py 有实证)。分档(FIT)仍归
export_print.fit_for_block, 本模块不做。

不回写 ledger: print.min_feature_ok 等字段零触碰, 产物只落
out/print/thin_features.json(spec#4 §3.1 数据/制造分离)。
段=ARCH07-11; 产物/文档口径"十七孔桥·中央五孔 1:50", 不作全桥陈述。
"""
import argparse
import json
import os
import sys

from typing import Any, Dict, List, Optional, Sequence

from export_print import _extents_m
from families import family_mesh

SCHEMA = 1
SCALE_DEFAULT = 1 / 50.0
FLOOR_MM_DEFAULT = 1.2
SEGMENT_DEFAULT = ("ARCH07", "ARCH08", "ARCH09", "ARCH10", "ARCH11")

_M3_BASE = ("M3(雕刻件)裁决: 中央五孔段内无狮/兽雕刻件, v1 自然豁免、M3 顺延续段; "
            "本条为%s, 非雕刻件。")
_M3_BBOX_TAIL = ("P1 排除口径已收(%s, 不单独出件, 打印以登记口径为准); "
                 "处置建议: 与相邻单元合印或并入邻块, 段端剖面块随 M5(a) 底座端槽收边; "
                 "几何封版(G1)禁改。")
_M3_BBOX = (_M3_BASE % "结构薄件(整块最小维低于打印当量)") + \
    "未见 P1 excluded_ids 登记, 需人工裁决: 与相邻单元合印或并入邻块; 几何封版(G1)禁改。"
_M3_SLIVER = (_M3_BASE % "出墙面浮雕细部(proud)低于打印当量") + \
    "块体本身可打印, 浮雕损失属外观项(P1A 实物已证整体可用); 建议按面石分组表面处理补足, 不改几何。"


def stone_dims_m(stone):
    # type: (Dict[str, Any]) -> Sequence[float]
    """块 bbox 三轴极差(米)。与 export_print._extents_m 同式, 网格取族库单源。"""
    verts, _faces = family_mesh(stone["family"], stone["params"])
    return _extents_m(verts)


def _m3_note(where, stone, excluded_bucket):
    # type: (str, Dict[str, Any], Optional[str]) -> str
    if where == "face_sliver":
        return _M3_SLIVER
    if excluded_bucket:
        return (_M3_BASE % "结构薄件(整块最小维低于打印当量)") + \
            (_M3_BBOX_TAIL % ("excluded_ids.%s" % excluded_bucket))
    return _M3_BBOX


def thin_features(ledger, scale=SCALE_DEFAULT, floor_mm=FLOOR_MM_DEFAULT,
                  zones=None, excluded_buckets=None):
    # type: (Dict[str, Any], float, float, Optional[Sequence[str]], Optional[Dict[str, str]]) -> List[Dict[str, Any]]
    """薄特征审计。保守判据=块最小维: min(bbox 极差) x scale x 1000 < floor_mm
    (打印当量, 严格小于, 与 printcheck 同式) -> where=bbox_min_dim;
    否则块体放行, 但 proud 浮雕当量 sub-floor(proud>0 且 proud x scale x 1000
    < floor) -> where=face_sliver。一石一条, bbox_min_dim 优先(整块不可印,
    更严)。条目: {stone, where, min_feature_print_mm, m3_note}, 按 stone 排序。
    zones=None 审全账; excluded_buckets: stone_id -> excluded_ids 桶名(仅用于
    m3_note 注记, 不改判定)。不回写 ledger。"""
    if not 0.0 < float(scale) <= 1.0:
        raise ValueError("scale must be in (0, 1]")
    if not float(floor_mm) > 0.0:
        raise ValueError("floor_mm must be > 0")
    zset = set(zones) if zones else None
    k = float(scale) * 1000.0
    floor = float(floor_mm)
    feats = []  # type: List[Dict[str, Any]]
    for s in ledger["stones"]:
        if zset is not None and s["id"].split(".")[0] not in zset:
            continue
        dims = stone_dims_m(s)
        mm_min = float(min(dims)) * k
        where = None  # type: Optional[str]
        val = 0.0
        if mm_min < floor:
            where, val = "bbox_min_dim", mm_min
        else:
            proud = float(s["params"].get("proud", 0.0))
            pmm = proud * k
            if proud > 0.0 and pmm < floor:
                where, val = "face_sliver", pmm
        if where is None:
            continue
        bucket = None
        if excluded_buckets is not None:
            bucket = excluded_buckets.get(s["id"])
        feats.append({"stone": s["id"],
                      "where": where,
                      "min_feature_print_mm": round(val, 4),
                      "m3_note": _m3_note(where, s, bucket)})
    feats.sort(key=lambda f: f["stone"])
    return feats


def build_document(features, scale, floor_mm, zones, stones_scanned, excluded_ref):
    # type: (List[Dict[str, Any]], float, float, Sequence[str], int, Optional[str]) -> Dict[str, Any]
    """落盘文档。键序固定、无时间字段 -> 两连跑逐字节同。"""
    by_where = {"bbox_min_dim": 0, "face_sliver": 0}
    for f in features:
        by_where[f["where"]] += 1
    return {
        "schema": SCHEMA,
        "what": "thin_features 打印当量薄特征审计(块最小维粗筛口径; "
                "与 printcheck 模型侧流形壁厚口径互为粗筛/精检, 见两模块 docstring)",
        "scale": float(scale),
        "floor_print_mm": float(floor_mm),
        "zones": list(zones),
        "stones_scanned": int(stones_scanned),
        "thin_total": len(features),
        "by_where": by_where,
        "excluded_ref": excluded_ref,
        "features": features,
    }


def _load_excluded_buckets(path):
    # type: (str) -> Dict[str, str]
    """excluded_ids.json -> {stone_id: bucket}。仅 m3_note 注记用。"""
    with open(path, "r", encoding="utf-8") as fh:
        ex = json.load(fh)
    out = {}  # type: Dict[str, str]
    for bucket, ids in ex.get("buckets", {}).items():
        for sid in ids:
            out[sid] = bucket
    return out


def main(argv=None):
    # type: (Optional[List[str]]) -> int
    ap = argparse.ArgumentParser(
        description="P4-T1 薄特征审计(打印当量口径, 不回写账)")
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--zones", default=",".join(SEGMENT_DEFAULT),
                    help="逗号分隔段名, 默认 ARCH07..ARCH11")
    ap.add_argument("--scale", type=float, default=SCALE_DEFAULT)
    ap.add_argument("--floor-mm", type=float, default=FLOOR_MM_DEFAULT)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    zones = [z.strip() for z in args.zones.split(",") if z.strip()]
    with open(args.ledger, "r", encoding="utf-8") as fh:
        ledger = json.load(fh)
    ex_path = os.path.join(os.path.dirname(os.path.abspath(args.ledger)),
                           "print", "excluded_ids.json")
    excluded_buckets = None
    excluded_ref = None
    if os.path.isfile(ex_path):
        excluded_buckets = _load_excluded_buckets(ex_path)
        excluded_ref = os.path.relpath(
            ex_path, os.path.dirname(os.path.abspath(args.out)))
    feats = thin_features(ledger, scale=args.scale, floor_mm=args.floor_mm,
                          zones=zones, excluded_buckets=excluded_buckets)
    scanned = sum(1 for s in ledger["stones"]
                  if s["id"].split(".")[0] in set(zones))
    doc = build_document(feats, args.scale, args.floor_mm, zones, scanned,
                         excluded_ref)
    out_dir = os.path.dirname(os.path.abspath(args.out))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    bw = doc["by_where"]
    print("薄特征审计: 段=%s 扫描 %d 石 -> thin_total=%d "
          "(bbox_min_dim=%d, face_sliver=%d) -> %s"
          % (",".join(zones), scanned, doc["thin_total"],
             bw["bbox_min_dim"], bw["face_sliver"], args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
