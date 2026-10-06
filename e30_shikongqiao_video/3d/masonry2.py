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
  同口径), 楔形(proud=0, hw_b/hw_t=墙面在 z0/z0+h 的收分参考), 外缘面与
  同带丁石内缘面平行、沿 z∧x 真相交带整体退 BACKING_GAP(2mm 隐缝, 记
  params.gap_mm; clearance_manufacturing_mm 保持 None 至 T6), 深 BACKING_D
  伪随机(seed 确定性)。
- core cells role=CORE evidence=core_reconstruction: 孔内 x 分 CORE_COLS 列
  × z 每 CORE_CELL_H 一层 × 前后(东西两墙)合并单 cell, params 记 bbox 与
  y_extent=full_wall(与面石账目重叠; 总体积按 evidence 分层不相加)。
  z 界从入参 z_lo/z_hi 推导不硬编; x 界必填(真实 blocks 用全局 x, 不得以
  拱心线墙面半宽近似——15/17 孔越界的 C3 审查修复)。直盒水密性由 T5
  printcheck 实测产出, 不在账目自证标记。
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


def backing_stones(faces, hw_fn, seed=0):
    # type: (List[Dict[str, Any]], Callable[[float, float], float], int) -> List[Dict[str, Any]]
    """背衬层: 与面石同块位/同层高的楔形背衬, 外缘面与同带丁石内缘面平行
    再退 BACKING_GAP(2mm 隐缝)。

    C2 审查修复(方案B): 面石内缘是斜面(hw_b≠hw_t), 旧平盒背衬(hw_b=hw_t=
    层中半宽)+带中点比标量, 真实 p8 实测 11 块穿透 +24.1mm、其余空腔
    181~403mm。现在背衬做成楔形: proud=0, params.hw_b/hw_t=hw_fn(xm,z0)/
    (z0+h) 的墙面收分参考(只载斜率); 外缘面 = 墙面平行平面 hw_fn(xm,z)+
    front_c, 与同带丁石内缘面(hw_fn(xm_h,z)+PROUD-d_h, 同斜率)平行, 沿
    相交带整体退 BACKING_GAP; front_c 记入 params(外缘面相对墙面的 y 向
    偏移), transform[1] = 层中处外缘 y(与面石外缘同语义), 内缘 = |y|-d。

    退让线(W5: faces 账目单一真相, 不再内部重跑 face_stones): 对每块背衬,
    取 z 带∧x 带**真相交**(正长度重叠, 端点贴合不算)的面石, 沿相交带两端
    比斜面(hw 沿 z 线性 -> 两端即全域):
        hw_fn(xm,z)+c <= min_{z∈band}[hw_fn(xm_s,z)+PROUD-d_s] - BACKING_GAP
    自身块位恒真相交 -> 可及集永不为空(废旧"全顺层回退全局面石最小值"与
    reachability 的 DEFAULT_COURSE_H 项=W3)。深度 BACKING_D 区间内 seed
    伪随机(同 seed 确定性, 东西同 seed 即镜像对称)。
    隐缝 2mm 是制造/装配量: 记 params.gap_mm; clearance_manufacturing_mm
    挂 T6 allow_clearance 时序才准置值(ledger I1 纪律, 置早=校验错)。
    """
    zone = faces[0]["id"].split(".")[0]
    face_name = faces[0]["id"].split(".")[1]
    side = 1 if face_name == "EAST" else -1
    # 账目恢复几何带: z 带 = zm±h/2, x 带 = xm±w/2(单一真相, 不重跑面石)
    geo = [(s, s["transform"][2] - s["params"]["h"] / 2.0,
            s["transform"][2] + s["params"]["h"] / 2.0,
            s["transform"][0] - s["params"]["w"] / 2.0,
            s["transform"][0] + s["params"]["w"] / 2.0)
           for s in faces]
    rng = random.Random(seed)
    out = []  # type: List[Dict[str, Any]]
    for s, zb0, zb1, xb0, xb1 in sorted(geo, key=lambda g: _face_idx(g[0])):
        ci, bi = _face_idx(s)
        h = s["params"]["h"]
        xm = s["transform"][0]
        zm = s["transform"][2]
        c = None  # type: Optional[float]
        for (t, tb0, tb1, tx0, tx1) in geo:
            zc0, zc1 = max(zb0, tb0), min(zb1, tb1)
            xc0, xc1 = max(xb0, tx0), min(xb1, tx1)
            if zc1 - zc0 <= 1e-9 or xc1 - xc0 <= 1e-9:
                continue   # 非真相交(端点贴合不算)
            # 相交带两端比斜面: 丁石内缘面 - 背衬墙面参考, 取紧端再退隐缝
            dz = min(hw_fn(t["transform"][0], zc0) - hw_fn(xm, zc0),
                     hw_fn(t["transform"][0], zc1) - hw_fn(xm, zc1))
            c_h = dz + PROUD - t["params"]["d"] - BACKING_GAP
            if c is None or c_h < c:
                c = c_h
        d = BACKING_D[0] + (BACKING_D[1] - BACKING_D[0]) * rng.random()
        y_out = hw_fn(xm, zm) + c
        st = L.new_stone(zone, face_name, "BACK", ci, bi, "wedge-std",
                         {"w": s["params"]["w"], "h": h, "d": d,
                          "proud": 0.0, "hw_b": hw_fn(xm, zb0),
                          "hw_t": hw_fn(xm, zb1), "front_c": c,
                          "gap_mm": BACKING_GAP * 1000.0},
                         [xm, y_out if side > 0 else -y_out, zm, 0.0, 0.0, 0.0],
                         "maoshi")
        out.append(st)
    return out


def core_cells(arch_idx, hw_fn, z_lo, z_hi, x_lo, x_hi, seed=0):
    # type: (int, Callable[[float, float], float], float, float, float, float, int) -> List[Dict[str, Any]]
    """牺牲芯 cells: x 分 CORE_COLS 列 × z 每 CORE_CELL_H 一层 × 前后合并。

    胞是贯穿东西两墙之间的单块直盒(family slab, 前后合并), y 半宽取该列心/
    层中处墙面半宽; params 记 bbox 与 y_extent="full_wall(overlaps ashlar)"
    —— 胞 y 向贯穿到墙面, 与面石/背衬账目在体积上重叠, **总体积按 evidence
    分层不相加**(牺牲芯会被券洞布尔挖除, 重叠是有意的建模分层)。
    z 界只从 z_lo/z_hi 推导(末层短胞兜到 z_hi), 不硬编; x 界必填(真实
    blocks 用全局 x, 拱心线墙面半宽近似恒绕桥中——15/17 孔越界的 C3 审查
    修复); z_hi <= z_lo 直接 ValueError(无空账静默)。seed 保留(当前网格无
    自由度, 与背衬共用伪随机接口纪律)。cell 高恒 <= CORE_CELL_H; 直盒水密
    性由 T5 printcheck 实测产出, 不在账目自证标记。
    """
    zone = "ARCH%02d" % (arch_idx + 1)
    if z_hi <= z_lo:
        raise ValueError("core_cells: z_hi(%r) <= z_lo(%r)" % (z_hi, z_lo))
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
                                "bbox": bb,
                                "y_extent": "full_wall(overlaps ashlar)"},
                               [x0, -yh, z0, 0.0, 0.0, 0.0],
                               "maoshi", evidence="core_reconstruction")
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
