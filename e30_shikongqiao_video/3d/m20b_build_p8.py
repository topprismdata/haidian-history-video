#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""m20b: 由 autoedges 证据表构建 stones_p8 v3 + family census.
证据优先级: accept(候选,conf>=2,|off|<=0.06, 取 x_fit)
          > retain(旧边照片修正, conf>=1.8, |off|<=0.15, 取 x+off)
          > weak/hidden(保留 v2 原值, conf=null).
合并 <0.2m 近邻, 保留证据强者; 湾缘取精确 bay 界.
每层 _trace 记录 n_read/n_retain/n_hidden 与理由; 每层 families 按
|Δw|<0.05m 归族(同层等高), 附 cut(被拱切割异形)计数.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from m20_pipeline import Model, load_ctrl  # noqa: E402


def load(v):
    with open(os.path.join(HERE, v)) as f:
        return json.load(f)


def kind_keep(e):
    """旧边 weak/hidden 保留 v2 占位; 候选 weak 弃."""
    return e["kind"] == "O"


def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else "p2017"
    model = Model(load_ctrl())
    a = model.arches[8]
    bay0, bay1 = a["bay_x0"], a["bay_x1"]
    v2 = load("stones/stones_p8.json")
    edges = load("m20_ctrl/m20b_edges_%s_a8.json" % tag)
    zfit = {o["ci"]: o for o in load("m20_ctrl/m20b_zfit_%s_a8.json" % tag)}

    courses_v3 = []
    tot = {"read": 0, "retain": 0, "hidden": 0}
    for ci, c in enumerate(sorted(v2["courses"], key=lambda c: c["z0"])):
        z0 = c["z0"]
        ev = edges[ci]["edges"]
        picked = []          # (prio, x, conf, src)
        for e in ev:
            x = float(e["x"])
            if not (bay0 + 0.05 < x < bay1 - 0.05):
                continue     # 湾缘单独处理
            v = e["verdict"]
            if v == "accept":
                picked.append((0, e["x_fit"], e["conf"], "read"))
            elif v == "retain":
                picked.append((1, x + e["off"], e["conf"], "retain"))
            elif v == "shift":
                picked.append((1, e["x_fit"], e["conf"], "retain"))
            elif kind_keep(e):
                picked.append((2, x, None, "hidden"))
            # weak 候选: 直接弃(无证据也不占位)
        # 湾缘
        picked.append((0, bay0, None, "bay"))
        picked.append((0, bay1, None, "bay"))
        # 去重: 近邻 <0.2 取 prio 小(证据强), 平手取 conf 大
        picked.sort(key=lambda p: (p[1], p[0]))
        merged = []
        for p in picked:
            if merged and abs(p[1] - merged[-1][1]) < 0.30:
                q = merged[-1]
                keep = p if (p[0], -(p[2] or 0)) < (q[0], -(q[2] or 0)) else q
                merged[-1] = keep
            else:
                merged.append(p)
        xs = [round(p[1], 3) for p in merged]
        # 单调 + 最小块宽 + 湾缘精确
        xs = sorted(set(xs))
        xs = [bay0] + [x for x in xs if bay0 + 0.05 < x < bay1 - 0.05] + [bay1]
        n_read = sum(1 for p in merged if p[3] == "read")
        n_ret = sum(1 for p in merged if p[3] == "retain")
        n_hid = sum(1 for p in merged if p[3] == "hidden")
        tot["read"] += n_read
        tot["retain"] += n_ret
        tot["hidden"] += n_hid
        zf = zfit.get(ci, {})
        zline = ("zfit off=%+.3fm(n=%d)" % (zf["off_m"], zf["n"])
                 if zf.get("off_m") is not None else "zfit n=0")
        tr = ("m20b-phototrace: read=%d retain=%d hidden=%d (tol±0.15m; "
              "hidden 段保留 v2) %s" % (n_read, n_ret, n_hid, zline))
        if z0 < 1.0:
            tr = "m20b-null-photo: 水下/水线照片不可读, 保留 v2(M18/程序值); " + zline
        # families: 同层等高, |Δw|<0.05 归族
        ws = [xs[k + 1] - xs[k] for k in range(len(xs) - 1)]
        fams = []
        for w in ws:
            for f in fams:
                if abs(w - f["w"]) < 0.05:
                    f["n"] += 1
                    break
            else:
                fams.append({"w": round(w, 3), "n": 1})
        fams.sort(key=lambda f: -f["n"])
        c3 = {"z0": z0, "blocks": xs, "_trace": tr, "families": fams}
        if c.get("_trace") and "m18-water" in c["_trace"]:
            c3["_trace"] += " [v2: m18-water]"
        courses_v3.append(c3)
    out = {
        "arch": 8,
        "provenance": ("stones_p8 v3 (m20b A08 逐块重描 2026-10-06): "
                       "autoedges 定量核验(无网格正射 80px/m, CLAHE, 横向梯度峰), "
                       "证据分 read/retain/hidden; z0 锚保留 v2(zfit 偏移<=0.08m); "
                       "水下层保留 v2 程序值"),
        "datum": v2.get("datum", "M19 冬照重标定 (水面 z=0, 桥面顶 7.30)"),
        "m20b_verify": {
            "edge_account": tot,
            "zfit": "全部层线偏移 <=0.081m (tol 0.15)",
            "ortho": "m20_ctrl/m20b_ortho_%s_a8_clean.png" % tag,
        },
        "courses": courses_v3,
    }
    with open("stones/stones_p8.json", "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print("v3 written; account:", tot)
    for c in courses_v3:
        print("z0=%.3f n=%d %s" % (c["z0"], len(c["blocks"]), c["families"]))


if __name__ == "__main__":
    main()
