# -*- coding: utf-8 -*-
"""M20 控制几何导出: 在 Blender(bmesh/mathutils 可用)环境里消费封版生成器模块,
把 M19 封版曲线的关键 3D 量导成 JSON, 供纯 python 的 M20 管线(PnP/正射)消费。
只读, 不改场景, 不保存 blend。用法:
  cd /tmp/e30_m20pilot/3d && blender -b --python m20_export_ctrl.py
输出: m20_ctrl/model_ctrl.json
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bridge_geom2 as G  # noqa: E402  (封版: facts 单一来源 + PIER_X 累加)
import masonry as MAS

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "m20_ctrl")
os.makedirs(OUT_DIR, exist_ok=True)

ctrl = {
    "source": "e30_bridge.blend 封版模块 bridge_geom2/masonry (M19 后), 导出脚本 m20_export_ctrl.py",
    "constants": {
        "BRIDGE_LEN": G.BRIDGE_LEN, "N_SPAN": G.N_SPAN,
        "DECK_Z_TOP": G.DECK_Z_TOP, "DECK_Z_END": G.DECK_Z_END,
        "DECK_UP_W": G.DECK_UP_W, "DECK_DOWN_W": G.DECK_DOWN_W,
        "BODY_BOTTOM": 0.0 + __import__("assumptions").BODY_BOTTOM,
        "RING_T": MAS.RING_T, "GAP_W": MAS.GAP_W,
        "STONE_PROUD": MAS.STONE_PROUD, "BARREL_PROTRUDE": MAS.BARREL_PROTRUDE,
        "WATERLINE_Z0": MAS.WATERLINE_Z0, "WATERLINE_Z1": MAS.WATERLINE_Z1,
        "END_ZONE": MAS.END_ZONE,
    },
    "PIER_X": [float(v) for v in G.PIER_X],
    "pier_w": {str(k): float(G.pier_w(k)) for k in range(1, G.N_SPAN)},
    "spans": [float(v) for v in G.SPANS],
    "arches": {},
    "deck_z_samples": [[float(x), float(G.deck_z(x))] for x in range(-78, 79, 2)],
    "rise_ratio": [float(G.arch_rise_ratio(i)) for i in range(G.N_SPAN)],
    "spandrel": [float(G.spandrel(i)) for i in range(G.N_SPAN)],
    "VOUSSOIR_TARGET": list(MAS.VOUSSOIR_TARGET),
}
for i in range(G.N_SPAN):
    xc = (G.PIER_X[i] + G.PIER_X[i + 1]) / 2.0
    a = G.SPANS[i] / 2.0
    spz = G.arch_springer_z(i)
    b = G.arch_rise(i)
    ctrl["arches"][str(i)] = {
        "xc": float(xc), "a": float(a), "spz": float(spz), "b": float(b),
        "crown_z": float(spz + b),
        "bay_x0": float(G.PIER_X[i] + (G.BRIDGE_ABUT if i == 0 else G.pier_w(i)) / 2.0),
        "bay_x1": float(G.PIER_X[i + 1] - (G.BRIDGE_ABUT if i == G.N_SPAN - 1 else G.pier_w(i + 1)) / 2.0),
    }

out = os.path.join(OUT_DIR, "model_ctrl.json")
with open(out, "w") as f:
    json.dump(ctrl, f, ensure_ascii=False, indent=1)
print("M20_CTRL_OK", out)
print("PIER_X[7..10] =", ["%.3f" % G.PIER_X[k] for k in range(7, 11)])
for i in (7, 8, 9):
    a8 = ctrl["arches"][str(i)]
    print("arch %d: xc=%.3f a=%.2f spz=%.3f b=%.3f crown=%.3f bay=[%.3f,%.3f]"
          % (i, a8["xc"], a8["a"], a8["spz"], a8["b"], a8["crown_z"], a8["bay_x0"], a8["bay_x1"]))
