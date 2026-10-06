#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""m20b: family census (族普查) — 同型砖=复制件(打印一模多铸).
中央孔(p8): 每层宽差<0.05m 归族 -> unique 矩形族数×实例数;
被拱切割的异形块单列(逐块_unique). 全桥族数估计: p7(拱7+9 复用)+p8+其余孔
按同构假设外推, 给范围. stones_deck 同法(列×长度档).
用法: python3 m20b_census.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from m20_pipeline import Model, load_ctrl, OUT  # noqa: E402
from m20b_a08 import hole_zcut  # noqa: E402
import numpy as np  # noqa: E402


def course_cut_blocks(model, i, c, z1):
    """被孔洞切割线穿过的块数(异形, 逐块_unique)."""
    a = model.arches[i]
    xs, zc = hole_zcut(model, i)
    n = 0
    for k in range(len(c["blocks"]) - 1):
        x0, x1 = c["blocks"][k], c["blocks"][k + 1]
        m = (xs >= x0) & (xs <= x1)
        if not m.any():
            continue
        zt = float(np.min(zc[m]))      # 块范围内洞顶最低点
        if z1 > zt:                     # 块顶高于洞顶 -> 被切
            n += 1
    return n


def main():
    model = Model(load_ctrl())
    out = {}
    for name in ("p8", "p7"):
        sp = json.load(open(os.path.join(HERE, "stones", "stones_%s.json" % name)))
        arch = sp["arch"]
        a = model.arches[arch]
        deck_top = max(model.deck_z(a["bay_x0"] + (a["bay_x1"] - a["bay_x0"]) * k / 15.0)
                       for k in range(16)) - 0.10
        cs = sorted(sp["courses"], key=lambda c: c["z0"])
        F = 0           # 矩形族数
        inst = 0        # 矩形块实例
        cut = 0         # 被切异形块
        per_course = []
        for ci, c in enumerate(cs):
            z1 = cs[ci + 1]["z0"] if ci + 1 < len(cs) else deck_top
            f = c.get("families")
            if f is None and c.get("blocks"):
                f = []
                for w in [c["blocks"][k + 1] - c["blocks"][k]
                          for k in range(len(c["blocks"]) - 1)]:
                    for g in f:
                        if abs(w - g["w"]) < 0.05:
                            g["n"] += 1
                            break
                    else:
                        f.append({"w": round(w, 3), "n": 1})
            if f:
                F += len(f)
                inst += sum(g["n"] for g in f)
            cut += course_cut_blocks(model, arch, c, z1)
            per_course.append({"ci": ci, "z0": c["z0"],
                               "families": len(f) if f else 0,
                               "inst": sum(g["n"] for g in f) if f else 0})
        out[name] = {"arch": arch, "families": F, "instances": inst,
                     "cut_blocks": cut, "blocks_total": inst + cut,
                     "per_course": per_course,
                     "reused_by": (["arch 9(加载器镜像)"] if name == "p7" else []),
                     "drives_arches": ([7, 9] if name == "p7" else [8])}
    # 全桥估计: 17 孔 = 镜像对 {0,16},{1,15}...{7,9} 共 8 对 + 中央 8.
    # 已测: p8(中央), p7(一对). 其余 7 对未描摹: 按同构假设每对族数≈p7,
    # 上界=每孔独立. 端孔/桥台端区不计入(P4 范围外).
    f8 = out["p8"]["families"]
    f7 = out["p7"]["families"]
    out["bridge_estimate"] = {
        "specs_total": 9,
        "measured": {"p8": f8, "p7": f7},
        "lower": f7 + f8,
        "upper": f8 + 8 * f7,
        "assumption": "7 个未测镜像对每对族数≈p7; 下界=全对与 p7 同族, "
                      "上界=各对独立",
        "instances_bridge": out["p7"]["instances"] * 2 * 8
        + out["p8"]["instances"],
        "note": "打印模具体积按 unique 族数; 实例数=同模复铸次数",
    }
    with open(os.path.join(OUT, "m20b_census.json"), "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print(json.dumps({k: v for k, v in out.items() if k != "bridge_estimate"}
                     | {"bridge_estimate": out["bridge_estimate"]}, indent=1,
                     ensure_ascii=False)[:1800])


if __name__ == "__main__":
    main()
