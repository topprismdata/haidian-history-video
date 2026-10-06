#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""m20b: stones_p7 v3 构建.
修复: v2 的 blocks 停在 p8 湾坐标 [±4.25], 加载器对拱7(湾 [−14.42,−6.42])
全 clamp 零块 -> 拱7/9 拱肩墙空. v3 = p8 v3 布局**平移镜像**到拱7湾心
(宽度不缩放), z0 以 A07 实测为准(缺测处镜像 p8).
用法: python3 m20b_build_p7.py [zfit_json]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from m20_pipeline import Model, load_ctrl  # noqa: E402


def main():
    zfit_path = sys.argv[1] if len(sys.argv) > 1 else \
        os.path.join(HERE, "m20_ctrl", "m20b_zfit_a07_a7.json")
    zfit = None
    if os.path.isfile(zfit_path):
        zfit = json.load(open(zfit_path))
    p8 = json.load(open(os.path.join(HERE, "stones", "stones_p8.json")))
    model = Model(load_ctrl())
    a7 = model.arches[7]
    xc7 = a7["xc"]
    # zfit by z0 (拱7 层线实测)
    zm = {}
    if zfit:
        for o in zfit:
            if o.get("off_m") is not None and o["n"] >= 10:
                zm[round(o["z0"], 2)] = o
    courses = []
    n_meas = 0
    for ci, c in enumerate(sorted(p8["courses"], key=lambda c: c["z0"])):
        z0_8 = c["z0"]
        zf = zm.get(round(z0_8, 2))
        if zf and abs(zf["off_m"]) <= 0.25:
            z0 = round(z0_8 + zf["off_m"], 3)
            zsrc = "a07-zfit(%+.3fm n=%d)" % (zf["off_m"], zf["n"])
            n_meas += 1
        else:
            z0 = z0_8
            zsrc = "mirror-p8(无独立实测)"
        # blocks: p8 边绕湾心镜像再平移到拱7湾心, 宽度不缩放
        bl = [round(xc7 - e, 3) for e in sorted(c["blocks"], reverse=True)]
        tr = ("m20b-p7v3: z0=%s; blocks=p8v3 平移镜像到拱7湾心(xc=%.2f, 宽度保留; "
              "CCTV 帧块界不可辨 sx=%.0fpx/m) [v2 修复: v2 blocks 在 p8 湾坐标, "
              "对拱7/9 全 clamp 零块=拱肩墙空]" % (zsrc, xc7, 0))
        courses.append({"z0": z0, "blocks": bl, "_trace": tr,
                        "families": c["families"],
                        "same_family_as": {"arch": 8, "course": ci}})
    out = {
        "arch": 7,
        "provenance": ("stones_p7 v3 (m20b A07 2026-10-06): CCTV f000150 链 "
                       "(pose->ortho) 层界复核 + p8 v3 布局平移镜像; 块界低于帧 "
                       "分辨率(降级=层界+主缝级, 如实标注); 加载器: 拱9=本文件镜像, "
                       "v3 首次把 blocks 放进拱7绝对湾坐标(v2 因此拱7/9 湾零块)"),
        "datum": "M19 冬照重标定 (水面 z=0, 桥面顶 7.30)",
        "courses": courses,
    }
    json.dump(out, open(os.path.join(HERE, "stones", "stones_p7.json"), "w"),
              indent=1, ensure_ascii=False)
    print("p7 v3 written; z0 measured %d/16" % n_meas)


if __name__ == "__main__":
    main()
