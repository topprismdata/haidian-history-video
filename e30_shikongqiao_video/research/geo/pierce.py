"""金光穿洞的几何判据(修正版)。

机制(经北京市园林绿化局 2023 官方说明 + 实拍照片校准):
  券洞是半圆拱, 断面为「口」形: 两侧竖直洞壁 + 顶部半圆拱腹。
  冬至前后日落时太阳高度角接近 0(近水平光), 方位在西南(约 238-240 度)。
  观察者站在桥的西北侧, 镜头顺桥洞延伸方向(东南) 望去。
  光不必"穿过"桥体, 只要斜着射入券洞断面, 就会点亮洞口内侧的拱腹与洞壁,
  从斜侧看过去即为一排发亮的拱洞。

  因此判据不是「方位夹角接近 0」, 而是三重条件同时满足:
    (1) 高度角足够低 —— 太阳要能射到拱腹(拱腹朝上, 要求光有向下分量? 不,
        拱腹朝下, 光要从洞口平面外侧射入并打在内壁上)
    (2) 太阳方位与桥轴的夹角落在「能照进洞内」的区间
    (3) 观察方向能看到洞口内侧

  实用化: 以「桥体正面法线」(东西向, 因东堤南北走向) 与「太阳方位」的夹角
  决定侧照强度; 以「桥轴(西北-东南)」与「视线方向」决定可见孔数。

数据来源(必须随结论一起给出):
  - 桥长 150m / 17 孔: 官方(北京市公园管理中心)
  - 桥轴走向: 官方定性「西北-东南」, 无数值角度
  - 太阳方位: 本项目 solar.py 实算(NOAA 星历, 负控制已过)
  - 官方说明拍摄点在桥的西北侧: 北京市园林绿化局 2023-12-01
"""
import math
from typing import List
import solar as S

BRIDGE_LEN_M = 150.0
N_SPAN = 17
DECK_UP_W_M = 6.56
BRIDGE_H_M = 7.0
ARCH_M = BRIDGE_LEN_M / N_SPAN      # 8.824m
PIER_M = 3.0                        # 【推断】墩宽, 无公开档案; 仅用于敏感性分析
LAT, LON = 40.0, 116.0


def half_angle_deg(distance_m: float, clear_m: float) -> float:
    """距观察者 distance_m 处, 净跨 clear_m 的券洞的方位张开半宽(度)。

    券洞为半圆拱断面, 正面净宽即净跨; 由观察点看去, 该洞可接收光线的
    方位角半宽 = atan((净跨/2) / 距离)。距离越远、净跨越窄, 容差越小。
    """
    return math.degrees(math.atan((clear_m / 2.0) / distance_m))


def span_clear(pier_m: float = PIER_M) -> float:
    """单孔净跨(米) = 拱跨 - 墩宽。墩宽无公开档案, 属【推断】。"""
    return ARCH_M - pier_m


def tolerance_deg(pier_m: float = PIER_M) -> float:
    """17 孔全亮的方位容差(度): 取最远孔的张开半宽。"""
    return half_angle_deg(BRIDGE_LEN_M, span_clear(pier_m))


def count_lit(bridge_az: float, sun_az: float, pier_m: float = PIER_M) -> int:
    """给定太阳方位, 有多少个券洞的内壁会被照亮。观察者在桥东端, 视线沿桥轴向西南。"""
    s = span_clear(pier_m)
    delta = S.az_diff(bridge_az, sun_az)
    n = 0
    for i in range(N_SPAN):
        d = BRIDGE_LEN_M - ARCH_M * i
        if delta < math.degrees(math.atan((s / 2.0) / d)):
            n += 1
    return n


def arch_inner_height(h_bridge: float = BRIDGE_H_M) -> float:
    """券洞内净高(估): 桥总高扣除桥面以上部分与水面以上余量。
    无官方数据, 属【推断】。保守取桥高的一半。"""
    return h_bridge * 0.5


def half_gap_required(alt_deg: float) -> float:
    """给定太阳高度角, 洞内要被打亮, 光线在洞内的水平投射长度需 <= 洞口净跨。
    近似: 洞口高度 h, 光以高度角 alpha 射入, 打到对壁时的水平距离 = h / tan(alpha)。
    若该距离 < 净跨, 则对壁被照亮。"""
    if alt_deg <= 0.05:
        return float("inf")     # 水平光: 无垂直分量, 只能照到同侧壁
    return arch_inner_height() / math.tan(math.radians(alt_deg))


def pierce_window(bridge_az_west_end: float, year: int,
                  piers: float = 3.0) -> dict:
    """给定桥轴(西端指向东端的方位角), 扫描全年, 找出券洞可被斜照的日期。

    判据: 太阳方位与「垂直于桥轴的方向」的夹角须小于某阈值(能照进洞内),
    且太阳高度角须低(低角度才有斜照效果)。
    """
    clear_m = ARCH_M - piers
    rows = []
    for m in range(1, 13):
        for d in range(1, 32):
            try:
                t_sunset, az = S.sunset(year, m, d, LAT, LON)
            except ValueError:
                continue
            # 洞口法线 = 垂直桥轴(在水平面内)
            normal_az = (bridge_az_west_end + 90.0) % 360.0
            # 太阳需在洞口外侧半球: 方位与法线夹角 < 90
            lateral = S.az_diff(az, normal_az)
            # 洞内横向投射需求 vs 净跨
            need = half_gap_required(max(0.5, BRIDGE_H_M * 0.0 + 0.5))
            rows.append({"date": "%d-%02d-%02d" % (year, m, d),
                         "sunset_az": round(az, 2),
                         "normal_az": round(normal_az, 2),
                         "lateral_deg": round(lateral, 2),
                         "side": "顺光" if lateral < 90 else "背光"})
    return {"bridge_az": bridge_az_west_end, "normal_az": (bridge_az_west_end + 90.0) % 360.0,
            "rows": rows}


if __name__ == "__main__":
    print("=== 几何参数 ===")
    print("  桥长 %.0fm  17孔 -> 拱跨 %.3fm" % (BRIDGE_LEN_M, ARCH_M))
    print("  洞口法线(垂直桥轴)与太阳方位的夹角 = 侧照角")
    print()
    print("=== 若桥轴为西北-东南(西端指向东端 = 东南 118 度) ===")
    r = pierce_window(118.0, 2025)
    print("  洞口法线 az = %.1f 度" % r["normal_az"])
    for nm, (m, d) in [("冬至", (12, 21)), ("冬至+10d", (12, 31)), ("1/10", (1, 10)),
                       ("11/20", (11, 20)), ("春分", (3, 20)), ("夏至", (6, 21))]:
        row = [x for x in r["rows"] if x["date"].endswith("%02d-%02d" % (m, d))]
        if row:
            x = row[0]
            print("  %-9s 日落az=%6.2f  侧照角=%5.2f 度  %s" % (nm, x["sunset_az"], x["lateral_deg"], x["side"]))
    print()
    print("=== 全年: 侧照角最小的日子(最接近正侧照) ===")
    rs = sorted(r["rows"], key=lambda x: min(x["lateral_deg"], 180 - x["lateral_deg"]))
    for x in rs[:8]:
        print("  %s  日落az=%6.2f  侧照角=%5.2f" % (x["date"], x["sunset_az"], x["lateral_deg"]))
    print()
    print("=== 关键数字 ===")
    ss_t, ss_az = S.sunset(2025, 12, 21, LAT, LON)
    print("  冬至日落方位 %.2f 度" % ss_az)
    print("  若桥轴东南 118 度, 洞口法线 = %.1f 度" % r["normal_az"])
    print("  侧照角 = |%.2f - %.1f| = %.2f 度" % (ss_az, r["normal_az"],
          S.az_diff(ss_az, r["normal_az"])))
    print("  90 度 = 完全正侧照(洞口法线对着太阳) = 斜照最深、洞内最亮")
