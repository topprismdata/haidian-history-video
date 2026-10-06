# e30_shikongqiao_video/3d/masonry2.py
# -*- coding: utf-8 -*-
"""P1 三层生成器: 面石(顺丁)/背衬/core cells -> ledger。

T3 面石层: 消费砖谱 spec(courses/blocks) 产出每石一条 ledger 账目。
- 顺丁相间: (course+block) 偶数位=顺石 STRETCHER_D, 奇数位=丁石 HEADER_D;
  深度差写进 params["d"] 供 T6 材料化(families._wedge_std 以 d 为权威深度)。
- 间隙两量分离: joint_historical_mm=10(历史缝), clearance_manufacturing_mm=None
  (制造间隙未定, T6 挂 allow_clearance 时序再定)。
- zone 编号 1 基(设计 spec: 孔=ARCH01..17 西→东), 砖谱文件/字段 arch 为 0 基。
- 层高由砖谱自身推导: h_i = z0_{i+1} - z0_i, 末层用显式 course_h 兜底(未传则
  DEFAULT_COURSE_H); 真实砖谱层间距不等, 定高建层会纵向插穿(T3 审查修复)。
T4 背衬层 + core cells:
- 背衬 role=BACK evidence=ashlar_truth: 与面石同块位/同层高(_course_heights
  同口径), 外缘退到可及丁石内缘再靠后 BACKING_GAP(2mm 隐缝, 记入
  clearance_manufacturing_mm 制造侧), 深 BACKING_D 伪随机(seed 确定性)。
- core cells role=CORE evidence=core_reconstruction: 孔内 x 分 CORE_COLS 列
  × z 每 CORE_CELL_H 一层 × 前后(东西两墙)合并单 cell, params 记 bbox,
  直盒天然水密(print.watertight, T5 printcheck 复核)。z 界从入参 z_lo/z_hi
  推导不硬编; x 界默认以拱心线处墙面半宽近似孔净半跨(T8 可用 x_lo/x_hi 精化)。
"""
import json
import math
import os
import random
from typing import Any, Callable, Dict, List, Optional, Tuple

import ledger as L

STRETCHER_D = 1.2
HEADER_D = 2.4
PROUD = 0.006
BACK = 0.30
# 末层兜底层高: 砖谱最后一层没有下一条起算线可推导, 才用这个常数
DEFAULT_COURSE_H = 0.55
# T4 背衬: 深度伪随机区间(m) 与丁石内缘隐缝(m)
BACKING_D = (0.8, 1.2)
BACKING_GAP = 0.002
# T4 core cells: 层高上限(m) 与 x 列数
CORE_CELL_H = 0.6
CORE_COLS = 3


def _pairs(blocks):
    # type: (List[Any]) -> List[Dict[str, float]]
    """砖谱块界归一: {x0,x1} 字典直通; 沿 x 的界边表[a,b,c] -> [a-b, b-c] 相邻对。

    边表相邻成块、首尾两边为该列的左右界: n 条界边产出 n-1 块砖,
    故奇数长度的边表不是缺块, 而是这一列有偶数个界位。
    """
    if blocks and isinstance(blocks[0], dict):
        return blocks
    return [{"x0": blocks[i], "x1": blocks[i + 1]}
            for i in range(len(blocks) - 1)]


def _course_heights(courses, course_h):
    # type: (List[Dict[str, Any]], Optional[float]) -> List[float]
    """层高从砖谱自身推导: h_i = z0_{i+1} - z0_i(相邻层起算线之差)。

    砖谱层间距不等(p8 实测 0.144~0.641m), 用定高建层会把矮层砖顶插进
    上层砖体。末层没有下一条起算线可依, 用调用方显式传入的 course_h 兜底;
    未传(None)则回退 DEFAULT_COURSE_H。
    """
    if not courses:
        return []
    zs = [c["z0"] for c in courses]
    top = DEFAULT_COURSE_H if course_h is None else course_h
    return [zs[i + 1] - zs[i] for i in range(len(zs) - 1)] + [top]


def face_stones(spec, arch_idx, side, hw_fn, course_h=None):
    # type: (Dict[str, Any], int, int, Callable[[float, float], float], Optional[float]) -> List[Dict[str, Any]]
    zone = "ARCH%02d" % (arch_idx + 1)
    face = "EAST" if side > 0 else "WEST"
    courses = spec.get("courses", [])
    heights = _course_heights(courses, course_h)
    out = []  # type: List[Dict[str, Any]]
    for ci, (course, h) in enumerate(zip(courses, heights)):
        z0 = course["z0"]
        for bi, blk in enumerate(_pairs(course.get("blocks", []))):
            x0, x1 = blk["x0"], blk["x1"]
            xm = (x0 + x1) / 2.0
            zm = z0 + h / 2.0
            depth = STRETCHER_D if (ci + bi) % 2 == 0 else HEADER_D
            hw_b = hw_fn(xm, z0)
            hw_t = hw_fn(xm, z0 + h)
            y = hw_fn(xm, zm) + PROUD
            st = L.new_stone(zone, face, "SPANDREL", ci, bi, "wedge-std",
                             {"w": x1 - x0, "h": h, "d": depth,
                              "proud": PROUD, "back": BACK,
                              "hw_b": hw_b, "hw_t": hw_t},
                             [xm, y if side > 0 else -y, zm, 0.0, 0.0, 0.0],
                             "qingshi")
            out.append(st)
    return out


def _face_idx(stone):
    # type: (Dict[str, Any]) -> Tuple[int, int]
    """ARCH09.EAST.SPANDREL.C00.B01 -> (0, 1)。"""
    tok = stone["id"].split(".")
    return int(tok[3][1:]), int(tok[4][1:])


def backing_stones(spec, arch_idx, side, hw_fn, course_h=None, seed=0):
    # type: (Dict[str, Any], int, int, Callable[[float, float], float], Optional[float], int) -> List[Dict[str, Any]]
    """背衬层: 与面石同块位/同层高, 外缘退到可及丁石内缘后 2mm 隐缝。

    层高与块位直接取自 face_stones 账目(同口径, 硬契约: 复用 _course_heights)。
    退让线: 对每块背衬, 取 z 向可及(名义层带与两石真实半跨和之较大者内)的
    丁石内缘最小值再退 BACKING_GAP; 可及集为空(全顺层)则退到全部面石内缘
    最小值之后。深度 BACKING_D 区间内 seed 伪随机(同 seed 确定性, 东西同
    seed 即镜像对称)。隐缝 2mm 是制造/装配量, 记 clearance_manufacturing_mm。
    transform[1] = 背衬外缘 y(与面石外缘同语义), 内缘 = |y| - d。
    """
    faces = face_stones(spec, arch_idx, side, hw_fn, course_h=course_h)
    zone = "ARCH%02d" % (arch_idx + 1)
    face = "EAST" if side > 0 else "WEST"
    # 丁石内缘表(取自面石账目, 与面石几何零偏差)
    hdr = [(s["transform"][2], abs(s["transform"][1]) - s["params"]["d"],
            s["params"]["h"])
           for s in faces if s["params"]["d"] == HEADER_D]
    all_in = [abs(s["transform"][1]) - s["params"]["d"] for s in faces]
    rng = random.Random(seed)
    out = []  # type: List[Dict[str, Any]]
    for s in sorted(faces, key=_face_idx):
        ci, bi = _face_idx(s)
        h = s["params"]["h"]
        zm = s["transform"][2]
        # 逐丁石可及带宽: 名义层带(跨薄层相邻) 与 真实半跨和(厚层贴触) 取大
        reach = [y_in for (zm_h, y_in, h_h) in hdr
                 if abs(zm - zm_h) < max(DEFAULT_COURSE_H,
                                         0.5 * (h + h_h)) + 1e-9]
        if not reach:
            reach = all_in
        y_out = min(reach) - BACKING_GAP
        d = BACKING_D[0] + (BACKING_D[1] - BACKING_D[0]) * rng.random()
        xm = s["transform"][0]
        hw_mid = hw_fn(xm, zm)
        st = L.new_stone(zone, face, "BACK", ci, bi, "wedge-std",
                         {"w": s["params"]["w"], "h": h, "d": d,
                          "proud": 0.0, "hw_b": hw_mid, "hw_t": hw_mid,
                          "gap_mm": 2.0},
                         [xm, y_out if side > 0 else -y_out, zm, 0.0, 0.0, 0.0],
                         "maoshi")
        # 2mm 隐缝是制造/装配量: 记 params.gap_mm; clearance_manufacturing_mm
        # 挂 T6 allow_clearance 时序才准置值(ledger I1 纪律, 置早=校验错)
        st["print"]["watertight"] = True
        out.append(st)
    return out


def core_cells(arch_idx, hw_fn, z_lo, z_hi, seed=0, x_lo=None, x_hi=None):
    # type: (int, Callable[[float, float], float], float, float, int, Optional[float], Optional[float]) -> List[Dict[str, Any]]
    """牺牲芯 cells: x 分 CORE_COLS 列 × z 每 CORE_CELL_H 一层 × 前后合并。

    胞是贯穿东西两墙之间的单块直盒(family slab, 前后合并), y 半宽取该列心/
    层中处墙面半宽; params 记 bbox。z 界只从 z_lo/z_hi 推导(末层短胞兜到
    z_hi), 不硬编; x 界缺省以 hw_fn(0, 层中)近似孔净半跨(拱心线处墙面半宽),
    调用方可传 x_lo/x_hi 用真实拱线精化。seed 保留(当前网格无自由度, 与
    背衬共用伪随机接口纪律)。cell 高恒 <= CORE_CELL_H; 直盒天然水密。
    """
    zone = "ARCH%02d" % (arch_idx + 1)
    if z_hi <= z_lo:
        return []
    if x_lo is None or x_hi is None:
        half = hw_fn(0.0, 0.5 * (z_lo + z_hi))
        if x_lo is None:
            x_lo = -half
        if x_hi is None:
            x_hi = half
    out = []  # type: List[Dict[str, Any]]
    n_layers = int(math.ceil((z_hi - z_lo) / CORE_CELL_H - 1e-9))
    for ci in range(n_layers):
        z0 = z_lo + ci * CORE_CELL_H
        # h 用截断量算, 不用 z1-z0 回减: 浮点回减会得 0.6000000000000001
        h = min(CORE_CELL_H, z_hi - z0)
        z1 = z0 + h
        zm = 0.5 * (z0 + z1)
        for bj in range(CORE_COLS):
            x0 = x_lo + (x_hi - x_lo) * bj / CORE_COLS
            x1 = x_lo + (x_hi - x_lo) * (bj + 1) / CORE_COLS
            yh = hw_fn(0.5 * (x0 + x1), zm)
            bb = {"x0": x0, "x1": x1, "y0": -yh, "y1": yh, "z0": z0, "z1": z1}
            cell = L.new_stone(zone, "EAST", "CORE", ci, bj, "slab",
                               {"w": x1 - x0, "h": h, "d": 2.0 * yh,
                                "bbox": bb},
                               [x0, -yh, z0, 0.0, 0.0, 0.0],
                               "maoshi", evidence="core_reconstruction")
            cell["print"]["watertight"] = True
            out.append(cell)
    return out


def build_face_layer(stones_dir, hw_fn, arches, course_h=None):
    # type: (str, Callable[[float, float], float], List[int], Optional[float]) -> List[Dict[str, Any]]
    """逐孔读 stones_p<arch_idx>.json 砖谱, 东西两面合成整层面石账目。

    course_h 仅为末层兜底透传; 其余层高按各孔砖谱自身层间距推导。
    """
    out = []  # type: List[Dict[str, Any]]
    for ai in arches:
        path = os.path.join(stones_dir, "stones_p%d.json" % ai)
        with open(path, "r", encoding="utf-8") as f:
            spec = json.load(f)
        for side in (1, -1):
            out.extend(face_stones(spec, ai, side, hw_fn, course_h=course_h))
    return out
