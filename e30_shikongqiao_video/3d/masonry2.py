# e30_shikongqiao_video/3d/masonry2.py
# -*- coding: utf-8 -*-
"""P1 三层生成器: 面石(顺丁)/背衬/core cells -> ledger。

T3 面石层: 消费砖谱 spec(courses/blocks) 产出每石一条 ledger 账目。
- 顺丁相间: (course+block) 偶数位=顺石 STRETCHER_D, 奇数位=丁石 HEADER_D;
  深度差写进 params["d"] 供 T6 材料化(families._wedge_std 以 d 为权威深度)。
- 间隙两量分离: joint_historical_mm=10(历史缝), clearance_manufacturing_mm=None
  (制造间隙未定, T6 挂 allow_clearance 时序再定)。
- zone 编号 1 基(设计 spec: 孔=ARCH01..17 西→东), 砖谱文件/字段 arch 为 0 基。
"""
import json
import os
from typing import Any, Callable, Dict, List

import ledger as L

STRETCHER_D = 1.2
HEADER_D = 2.4
PROUD = 0.006
BACK = 0.30


def _pairs(blocks):
    # type: (List[Any]) -> List[Dict[str, float]]
    """砖谱块界归一: {x0,x1} 字典直通; 沿 x 的界边表[a,b,c] -> [a-b, b-c] 相邻对。"""
    if blocks and isinstance(blocks[0], dict):
        return blocks
    return [{"x0": blocks[i], "x1": blocks[i + 1]}
            for i in range(len(blocks) - 1)]


def face_stones(spec, arch_idx, side, hw_fn, course_h=0.55):
    # type: (Dict[str, Any], int, int, Callable[[float, float], float], float) -> List[Dict[str, Any]]
    zone = "ARCH%02d" % (arch_idx + 1)
    face = "EAST" if side > 0 else "WEST"
    out = []  # type: List[Dict[str, Any]]
    for ci, course in enumerate(spec.get("courses", [])):
        z0 = course["z0"]
        for bi, blk in enumerate(_pairs(course.get("blocks", []))):
            x0, x1 = blk["x0"], blk["x1"]
            xm = (x0 + x1) / 2.0
            zm = z0 + course_h / 2.0
            depth = STRETCHER_D if (ci + bi) % 2 == 0 else HEADER_D
            hw_b = hw_fn(xm, z0)
            hw_t = hw_fn(xm, z0 + course_h)
            y = hw_fn(xm, zm) + PROUD
            st = L.new_stone(zone, face, "SPANDREL", ci, bi, "wedge-std",
                             {"w": x1 - x0, "h": course_h, "d": depth,
                              "proud": PROUD, "back": BACK,
                              "hw_b": hw_b, "hw_t": hw_t},
                             [xm, y if side > 0 else -y, zm, 0.0, 0.0, 0.0],
                             "qingshi")
            out.append(st)
    return out


def build_face_layer(stones_dir, hw_fn, arches):
    # type: (str, Callable[[float, float], float], List[int]) -> List[Dict[str, Any]]
    """逐孔读 stones_p<arch_idx>.json 砖谱, 东西两面合成整层面石账目。"""
    out = []  # type: List[Dict[str, Any]]
    for ai in arches:
        path = os.path.join(stones_dir, "stones_p%d.json" % ai)
        with open(path, "r", encoding="utf-8") as f:
            spec = json.load(f)
        for side in (1, -1):
            out.extend(face_stones(spec, ai, side, hw_fn))
    return out
