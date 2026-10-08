# -*- coding: utf-8 -*-
"""M23/拱线 洞形透光闸门 v2 —— 射线采样式(极性无关, 不依赖渲染/光照/雾)。

原理: 每孔沿被摄面法线(+Nv 侧 40m 外)向桥体打 z-分层射线栅(24 z 级 × 24 列),
首次命中距离落在 [30,50]m 桥体窗口 = 阻挡; 否则=透光。
指标: ①平均透光率(抓未切/矩形槽: 实心墙透光率≈0)
      ②各 z 级透光宽度剖面 vs 模型圆弧弦宽的 rmse(抓 ogee 错形; 圆弧=单圆 rmse→0)
全 17 孔双指标绿才 PASS。负控标定: ogee RED / 未切 RED / 22:04 圆弧 PASS(两红一绿)。

用法: blender -b <任意blend> --python check_arch_transmittance.py -- [out.json]
输出: stdout ARCHGATE <json>; /tmp/arch_gate.json。
"""
import json
import math
import os
import sys

import bpy
import mathutils
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sc = bpy.context.scene
AXIS = math.radians(112.0)
SEED = 20261004
PROB_TOL = 0.30
ARC_RMSE_MAX = 0.30
SHOOT = 40.0
WIN = (30.0, 50.0)


def B_vec(x, y, z):
    B = mathutils.Vector((math.cos(-AXIS), math.sin(-AXIS), 0.0))
    Nv = mathutils.Vector((-B.y, B.x, 0.0))
    return B * x + Nv * y + mathutils.Vector((0.0, 0.0, z))


def _hw_at(ctrl, x, z):
    c = ctrl["constants"]
    half = c["BRIDGE_LEN"] / 2.0
    k = (c["DECK_Z_TOP"] - c["DECK_Z_END"]) / (half * half)
    deck = c["DECK_Z_TOP"] - k * min(abs(x), half) ** 2
    f = max(0.0, min(1.0, (z - c["BODY_BOTTOM"]) / (deck - c["BODY_BOTTOM"])))
    return (c["DECK_DOWN_W"] + (c["DECK_UP_W"] - c["DECK_DOWN_W"]) * f) / 2.0


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out_json = argv[0] if argv else "/tmp/arch_gate.json"
    dg = bpy.context.evaluated_depsgraph_get()

    ctrl = json.load(open(os.path.join(HERE, "m20_ctrl", "model_ctrl.json")))
    c = ctrl["constants"]
    half = c["BRIDGE_LEN"] / 2.0
    k = (c["DECK_Z_TOP"] - c["DECK_Z_END"]) / (half * half)
    B = mathutils.Vector((math.cos(-AXIS), math.sin(-AXIS), 0.0))
    Nv = mathutils.Vector((-B.y, B.x, 0.0))
    Ez = mathutils.Vector((0.0, 0.0, 1.0))
    dirv = -Nv  # 从 +Nv 侧垂直穿桥

    rows = []
    for i in range(17):
        a = ctrl["arches"][str(i)]
        xc, spz, ah = a["xc"], a["spz"], a["a"]
        crown = spz + ah
        bay_w = (a["bay_x1"] - a["bay_x0"])
        zs = np.linspace(0.25, crown - 0.15, 22)
        xs = np.linspace(a["bay_x0"] + 0.25, a["bay_x1"] - 0.25, 22)
        n_open = 0
        prof = []
        for z in zs:
            op = 0
            # 该 z 级期望圆弧弦宽(模型, 米)
            if z <= spz:
                w_exp = bay_w
            else:
                w_exp = 2.0 * math.sqrt(max(0.0, ah * ah - (z - spz) ** 2))
            for x in xs:
                o = B_vec(float(x), SHOOT, float(z))
                hit, loc, *_ = sc.ray_cast(dg, o, dirv)
                if hit and WIN[0] <= (o - loc).length <= WIN[1]:
                    pass  # 阻挡
                else:
                    op += 1
            frac = op / len(xs)
            prof.append(frac)
            n_open += op
        trans = n_open / (len(zs) * len(xs))
        # 透光宽度剖面 rmse(米)
        w_meas = np.array(prof) * bay_w
        w_mod = np.array([bay_w if z <= spz else 2.0 * math.sqrt(max(0.0, ah * ah - (z - spz) ** 2))
                          for z in zs])
        rmse = float(np.sqrt(np.mean((w_meas - w_mod) ** 2)))
        ok = (trans >= PROB_TOL) and (rmse <= ARC_RMSE_MAX)
        reason = None if ok else ("low_transmittance(未切/矩形槽)" if trans < PROB_TOL else
                                  "shape_not_circle(ogee 类)")
        rows.append(dict(arch=i, verdict="PASS" if ok else "RED", reason=reason,
                         transmittance=round(trans, 3), width_rmse_m=round(rmse, 3)))
    npass = sum(1 for r in rows if r["verdict"] == "PASS")
    gate = "PASS" if npass == 17 else "RED"
    out = dict(gate=gate, pass_n=npass, arches=rows,
               thresholds=dict(trans_min=PROB_TOL, width_rmse_max_m=ARC_RMSE_MAX,
                               ray_grid="22z x 22x per arch, 射线沿被摄面法线, 命中窗[30,50]m"),
               calibration="两红一绿(2026-10-08): ogee RED(width_rmse)/未切RED(transmittance)/圆弧版 PASS")
    print("ARCHGATE " + json.dumps(out, ensure_ascii=False))
    json.dump(out, open(out_json, "w"), ensure_ascii=False, indent=1)


main()
