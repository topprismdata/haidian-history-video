# e30_shikongqiao_video/3d/families.py
# -*- coding: utf-8 -*-
"""P1 族库: 参数化确定性网格。族=共享 mesh; unique=异形块烘焙缓存。"""
import hashlib
import os
from typing import Any, Dict, List, Tuple

def _wedge_std(params):
    # type: (Dict[str, Any]) -> Tuple[List[Tuple[float, float, float]], List[Tuple[int, ...]]]
    """收分楔形砧石(局部坐标: 原点在块左下前角, x=宽, y=深(向墙内为负), z=高)。
    前脸上下沿 y 随 hw_b/hw_t 倾斜(proud 出挑), 背向 -back。"""
    w = params["w"]; h = params["h"]; proud = params["proud"]; back = params["back"]
    hw_b = params["hw_b"]; hw_t = params["hw_t"]
    f0, f1 = proud, proud + (hw_b - hw_t)   # 前脸下/上沿 y(局部, 上沿内收)
    b0, b1 = f0 - back, f1 - back
    v = [(0.0, b0, 0.0), (w, b0, 0.0), (w, f0, 0.0), (0.0, f0, 0.0),
         (0.0, b1, h), (w, b1, h), (w, f1, h), (0.0, f1, h)]
    f = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
         (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    return v, f

def _slab(params):
    # type: (Dict[str, Any]) -> Tuple[List[Tuple[float, float, float]], List[Tuple[int, ...]]]
    """水平铺石/栏板类直盒。"""
    w, d, h = params["w"], params["d"], params["h"]
    v = [(0, 0, 0), (w, 0, 0), (w, d, 0), (0, d, 0),
         (0, 0, h), (w, 0, h), (w, d, h), (0, d, h)]
    f = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
         (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    return v, f

FAMILIES = {"wedge-std": _wedge_std, "slab": _slab}

def family_mesh(family, params):
    # type: (str, Dict[str, Any]) -> Tuple[List[Tuple[float, float, float]], List[Tuple[int, ...]]]
    return FAMILIES[family](params)

def bake_unique(stone_id, verts, faces, cache_dir, curve_hash):
    # type: (str, List[Tuple[float, float, float]], List[Tuple[int, ...]], str, str) -> str
    os.makedirs(cache_dir, exist_ok=True)
    tag = hashlib.sha1(("%s|%s" % (stone_id, curve_hash)).encode()).hexdigest()[:12]
    path = os.path.join(cache_dir, "%s_%s.obj" % (stone_id.replace(".", "_"), tag))
    with open(path, "w", encoding="utf-8") as fh:
        for v in verts:
            fh.write("v %.6f %.6f %.6f\n" % v)
        for fc in faces:
            fh.write("f " + " ".join(str(i + 1) for i in fc) + "\n")
    return path
