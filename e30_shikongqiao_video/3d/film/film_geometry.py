#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# e30_shikongqiao_video/3d/film/film_geometry.py
"""P3-T4 渲染侧参数单源: 锚点/λ下沉/机位/剪影位(纯函数+常量, blender-free)。

T5 film_render 的唯一几何参数来源 —— 渲染驱动不许内嵌第二套坐标/下沉常数,
净空/布位判据全部在此钉死一次。全部量纲为模型米(世界系: x 沿桥轴,
y 横桥向, z 铅垂; 常水位 z=0, 桥轴 y=0)。

接口(计划 Task 4 签名钉死, T5 消费):
    WEDGE_DROP_M = 0.04                       # 楔石落架全档下沉量(模型米)
    yard_anchor(stone_id)  -> (x, y, z)       # 堆场分组码位
    lift_anchor(stone_id)  -> (x, y, z)       # 吊运过路点(就位位正上方)
    home_position(stone_id) -> (x, y, z)      # 就位世界位(账本 transform 单源)
    SILHOUETTE_SLOTS                         # 剪影站位表(≤6 位, 证据字段)
    CAMERA_TRACKS                            # 段→机位映射(键=film_state.phase)

═══ 布位设计([设计选择], 净空判据为本模块硬合同) ═══

1. yard_anchor —— 堆场分区: 行(zone)×列(family) 的 4 列网格。
   行 x = geom_math.arch_center_x(zone): 堆场沿北岸随 17 孔展开, 石料码放
   在其目标孔旁, 吊运动线最短;
   列 y = YARD_Y0 + col*YARD_COL_PITCH, col = _FAM_COL[family]: 族全域按
   crc32 散列**定序**后依次占列 0..3(散列驱动的双射 —— 纯 mod 4 会出现
   两族同列叠码、另两列恒空, 实测 ring-wedge/impost-step 同 crc32 余数,
   故散列定序消解); 同族聚码, 四族不叠;
   z = deck_z(x) + YARD_Z_ABOVE_DECK(码位平面略高于该 x 处桥面, 与吊运
   平面衔接)。净空: 列起点 9.0m > 桥体半宽极值 7.3m + 0.5m 余量, 恒在
   hw(x,z)+0.5m 之外(test_yield_no_overlap_with_body 以 geom_math.width_at
   反查钉死)。
   散列用 zlib.crc32 —— **禁用内建 hash()**(PYTHONHASHSEED 按进程加盐,
   跨进程不确定); crc32 纯函数, 同 id 两次逐位同(test_anchors_deterministic)。
   family 读账本 stone["family"](族单源), 不从 id 抄第二套映射; 族全域外
   KeyError(网格须随账重排, 拒绝静默并列)。

2. lift_anchor —— 吊运过路点 = 就位位 (x,y) 原地, z = deck_z(就位 x) +
   LIFT_Z_ABOVE_DECK(桥面上方 2m 净高)。在桥体上方的 y 不避让, 净空走
   z 判据: z - deck_z(x) == 2.0m ≥ 2m(test 以 geom_math.deck_z 反查)。

3. home_position —— 就位世界位 = out/ledger_sequenced.json 该石
   transform 前三分量**逐位**(不重算不取整; P2 生成链是唯一写方)。
   账本惰性加载一次; 未知 id KeyError(防静默零位)。

4. SILHOUETTE_SLOTS —— 片头/工序剪影站位(纯轮廓小人, ≤6 位)。pose 词表
   {lever, chisel, crowbar} 对应 C:A4 石作加工链(打荒→錾道→剁斧→扁光)
   的撬/錾/撬棍三形制; 站位与分配为 [设计选择](证据字段如实分层:
   C:A4 只背工具形制, 不背站位坐标)。

5. CAMERA_TRACKS —— 键 = film_state.state_at_frame(...)["phase"] 三段
   词表 {"BUILD","DECENTER","DONE"}(词表单源 film_state, 此处不复制生成
   逻辑只钉消费键面); 值 = 机位 id + 参数:
     BUILD    侧视正射全景(ortho_scale 165 > 桥长 150 留边);
     DECENTER 45° 鸟瞰(loc/target 竖横差各 50m, 恰 45°);
     DONE     侧视缓推(loc_start→loc_end 沿 DONE 帧域线性插值, T5 lerp)。
   机位均在桥体净空外(南侧 y<0 或高空), 与北岸堆场(y>0)互不遮挡。

几何函数(hw=width_at/deck_z/arch_center_x)一律 import geom_math(P2 单源,
facts 常数链), 本模块零几何公式; Python 3.9.6; P2 工件只读。
"""
import json
import os
import sys
import zlib

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)          # 3d/ — 直跑与 pytest 两入口共用
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)

from geom_math import arch_center_x, deck_z  # noqa: E402  P2 几何单源

__all__ = ["WEDGE_DROP_M", "yard_anchor", "lift_anchor", "home_position",
           "SILHOUETTE_SLOTS", "CAMERA_TRACKS"]

# [工程参数·敏感性] 楔石落架全档下沉量(模型米): T5 按 delta_z=-λ*WEDGE_DROP_M
# 逐楔位移(λ∈[0,1] 为 film_state.wedge_lambda 档)。可调范围 0.02-0.08:
# 下限以下落架段落感不足, 上限以上相对缝宽失真(真缝实档见账
# joint_historical_mm)。0.04 为中档缺省。
WEDGE_DROP_M = 0.04

# 堆场网格([设计选择]): 4 列 × (17 zone 行); 列距 2.2m, 首列距桥轴 9.0m。
YARD_Y0_M = 9.0
YARD_COL_PITCH_M = 2.2
YARD_N_COLS = 4
YARD_Z_ABOVE_DECK_M = 1.0                 # 码位平面 = 该 x 处桥面 +1m
LIFT_Z_ABOVE_DECK_M = 2.0                 # 吊运过路点 = 桥面上方 2m 净空

_LEDGER_PATH = os.path.join(_PARENT, "out", "ledger_sequenced.json")
_STONE_INDEX = None                       # 惰性单次加载(id → stone dict)


def _stone(stone_id):
    """id → 账本石记录(未知 id KeyError, 防静默零位)。"""
    global _STONE_INDEX
    if _STONE_INDEX is None:
        with open(_LEDGER_PATH, "r", encoding="utf-8") as fh:
            _STONE_INDEX = {s["id"]: s for s in json.load(fh)["stones"]}
    return _STONE_INDEX[stone_id]


def _zone_index(stone_id):
    """id 首段 ARCHxx → 0-based 孔号; 形制不符 ValueError(账缺陷早爆)。"""
    zone = stone_id.split(".", 1)[0]
    if not (zone.startswith("ARCH") and zone[4:].isdigit()):
        raise ValueError("非 ARCHxx id 形制: %r" % stone_id)
    n = int(zone[4:])
    if not 1 <= n <= 17:
        raise ValueError("孔号越界 [1,17]: %r" % stone_id)
    return n - 1


_YARD_FAMILIES = ("impost-step", "ring-wedge", "slab", "wedge-std")  # 账本族全域
_FAM_COL = {f: i for i, f in enumerate(          # crc32 散列定序 → 双射占列
    sorted(_YARD_FAMILIES, key=lambda s: zlib.crc32(s.encode("utf-8"))))}


def _family_column(family):
    """族 → 码位列 0..3(散列定序双射, 无叠码; 全域外 KeyError 早爆)。"""
    return _FAM_COL[family]


def home_position(stone_id):
    """就位世界位 (x,y,z) = 账本 transform 前三分量, 逐位不重算。"""
    t = _stone(stone_id)["transform"]
    return (t[0], t[1], t[2])


def yard_anchor(stone_id):
    """堆场分组码位: 行 x=arch_center_x(zone), 列 y=族散列, z=deck_z(x)+1。"""
    x = arch_center_x(_zone_index(stone_id))
    col = _family_column(_stone(stone_id)["family"])
    y = YARD_Y0_M + col * YARD_COL_PITCH_M
    z = deck_z(x) + YARD_Z_ABOVE_DECK_M
    return (x, y, z)


def lift_anchor(stone_id):
    """吊运过路点 = 就位位正上方, z = deck_z(就位 x) + 2m 净空。"""
    hx, hy, _ = home_position(stone_id)
    return (hx, hy, deck_z(hx) + LIFT_Z_ABOVE_DECK_M)


# ── 剪影站位表: pose 形制背书 C:A4 石作加工链; 坐标为 [设计选择] ──
_S = SILHOUETTE_SLOTS = [
    {"pos": (-60.0, 2.0, deck_z(-60.0)), "pose": "chisel",
     "evidence": "C:A4|[设计选择] 东段桥面·錾道位"},
    {"pos": (-30.0, -2.0, deck_z(-30.0)), "pose": "crowbar",
     "evidence": "C:A4|[设计选择] 中东段桥面·撬棍拨块位"},
    {"pos": (0.0, 2.0, deck_z(0.0)), "pose": "lever",
     "evidence": "C:A4|[设计选择] 桥顶中央·撬杠就位位"},
    {"pos": (30.0, -2.0, deck_z(30.0)), "pose": "chisel",
     "evidence": "C:A4|[设计选择] 中西段桥面·剁斧收光位"},
    {"pos": (-70.0, 11.0, 0.0), "pose": "lever",
     "evidence": "C:A4|[设计选择] 北岸堆场·撬杠上滚木位"},
    {"pos": (60.0, 11.0, 0.0), "pose": "crowbar",
     "evidence": "C:A4|[设计选择] 北岸堆场东·撬棍翻料位"},
]

# ── 段→机位映射: 键=film_state.phase 词表; 机位参数 T5 直读 ──
CAMERA_TRACKS = {
    "BUILD": {
        "cam_id": "CAM_P3_BUILD_SIDE_ORTHO",
        "projection": "ORTHO",
        "loc": (0.0, -85.0, 7.5),
        "target": (0.0, 0.0, 5.0),
        "ortho_scale": 165.0,
        "evidence": "[设计选择] 侧视正射全景(165>150 留边), 南侧避北岸堆场",
    },
    "DECENTER": {
        "cam_id": "CAM_P3_DECENTER_BIRD45",
        "projection": "PERSP",
        "loc": (0.0, -50.0, 54.0),
        "target": (0.0, 0.0, 4.0),
        "lens_mm": 35.0,
        "evidence": "[设计选择] 45° 鸟瞰(dy=dz=50 恰 45°)看卸架全桥波次",
    },
    "DONE": {
        "cam_id": "CAM_P3_DONE_SIDE_PUSH",
        "projection": "PERSP",
        "loc_start": (0.0, -55.0, 8.0),
        "loc_end": (0.0, -38.0, 7.0),
        "target": (0.0, 0.0, 5.5),
        "lens_mm": 50.0,
        "evidence": "[设计选择] 侧视缓推 17m, T5 按 DONE 帧域线性插值",
    },
}
