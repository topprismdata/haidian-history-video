"""太阳位置(NOAA Solar Equations) + 金光穿洞几何判据。
Python 3.9 兼容, 纯标准库, 无网络依赖。

坐标约定: 输入经纬度必须已折算为 WGS-84(经 crs.to_wgs84)。
方位角 az: 正北 0, 顺时针(东=90, 南=180, 西=270)。
高度角 alt: 地平 0, 天顶 90。
时间: 本地钟点(北京 UTC+8)。
"""
import math
from typing import Optional, Tuple

RAD = math.pi / 180.0
BEIJING_TZ = 8.0


def _julian_day(y: int, m: int, d: float) -> float:
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4
    return (math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1))
            + d + b - 1524.5)


def _geom(p: Tuple[int, int, int, float], lat: float, lon: float,
          tz: float) -> Tuple[float, float]:
    """返回 (方位角, 高度角), 单位度。p=(y,m,d,本地钟点小时)。"""
    y, m, d, local_hour = p
    jd = _julian_day(y, m, d + (local_hour - tz) / 24.0)
    t = (jd - 2451545.0) / 36525.0

    l0 = (280.46646 + t * (36000.76983 + t * 0.0003032)) % 360.0
    m_anom = 357.52911 + t * (35999.05029 - 0.0001537 * t)
    e = 0.016708634 - t * (0.000042037 + 0.0000001267 * t)
    c = (math.sin(RAD * m_anom) * (1.914602 - t * (0.004817 + 0.000014 * t))
         + math.sin(RAD * 2 * m_anom) * (0.019993 - 0.000101 * t)
         + math.sin(RAD * 3 * m_anom) * 0.000289)
    true_long = l0 + c
    app_long = true_long - 0.00569 - 0.00478 * math.sin(RAD * (125.04 - 1934.136 * t))
    mean_obliq = 23.0 + (26.0 + ((21.448 - t * (46.815 + t * (0.00059 - t * 0.001813)))) / 60.0) / 60.0
    obliq = mean_obliq + 0.00256 * math.cos(RAD * (125.04 - 1934.136 * t))
    decl = math.asin(math.sin(RAD * obliq) * math.sin(RAD * app_long))

    vary = math.tan(RAD * obliq / 2.0) ** 2
    eq_time = 4.0 * math.degrees(
        vary * math.sin(2 * RAD * l0)
        - 2 * e * math.sin(RAD * m_anom)
        + 4 * e * vary * math.sin(RAD * m_anom) * math.cos(2 * RAD * l0)
        - 0.5 * vary * vary * math.sin(4 * RAD * l0)
        - 1.25 * e * e * math.sin(2 * RAD * m_anom))

    minutes = local_hour * 60.0
    tst = (minutes + eq_time + 4.0 * lon - 60.0 * tz) % 1440.0
    ha = tst / 4.0
    if ha < 0:
        ha += 180.0
    else:
        ha -= 180.0

    lat_r = math.radians(lat)
    cos_z = (math.sin(lat_r) * math.sin(decl) + math.cos(lat_r) * math.cos(decl) * math.cos(RAD * ha))
    cos_z = max(-1.0, min(1.0, cos_z))
    zen = math.degrees(math.acos(cos_z))
    elev = 90.0 - zen

    sin_z = math.sin(RAD * zen)
    if abs(sin_z) < 1e-9:
        az = 180.0
    else:
        arg = ((math.sin(lat_r) * cos_z - math.sin(decl)) / (math.cos(lat_r) * sin_z))
        arg = max(-1.0, min(1.0, arg))
        if ha > 0:
            az = (math.degrees(math.acos(arg)) + 180.0) % 360.0
        else:
            az = (540.0 - math.degrees(math.acos(arg))) % 360.0
    return az, elev


def solar(y: int, m: int, d: int, local_hour: float,
          lat: float = 40.0, lon: float = 116.0) -> Tuple[float, float]:
    return _geom((y, m, d, local_hour), lat, lon, BEIJING_TZ)


def _find_alt_zero(y: int, m: int, d: int, lat: float, lon: float,
                   lo: float, hi: float) -> float:
    """在 [lo,hi] 内二分求 alt=0 的下降沿(要求 alt(lo)>0>=alt(hi))。"""
    if _geom((y, m, d, lo), lat, lon, BEIJING_TZ)[1] <= 0:
        raise ValueError("sunset 区间左端已在地平线下")
    if _geom((y, m, d, hi), lat, lon, BEIJING_TZ)[1] > 0:
        raise ValueError("sunset 区间右端仍在地平线上(极昼或区间越界)")
    for _ in range(60):
        mid = (lo + hi) / 2.0
        if _geom((y, m, d, mid), lat, lon, BEIJING_TZ)[1] > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def sunset(y: int, m: int, d: int, lat: float = 40.0, lon: float = 116.0) -> Tuple[float, float]:
    """返回 (日落钟点, 日落方位角)。"""
    t = _find_alt_zero(y, m, d, lat, lon, 14.0, 21.0)
    az, _ = _geom((y, m, d, t), lat, lon, BEIJING_TZ)
    return t, az


def sunrise(y: int, m: int, d: int, lat: float = 40.0, lon: float = 116.0) -> Tuple[float, float]:
    """返回 (日出钟点, 日出方位角)。

    二分方向: alt 随钟点单调升, 故 alt<0 的一侧为 lo, 恒有 alt(lo)<0<alt(hi),
    收敛后 (lo+hi)/2 即为 alt=0 之处。若区间不满足该不变量须抛错, 不得静默外推。
    """
    lo, hi = 2.0, 9.0
    if _geom((y, m, d, lo), lat, lon, BEIJING_TZ)[1] >= 0:
        raise ValueError("sunrise 区间 [%g,%g] 左端已在地面之上(极昼或区间越界)" % (lo, hi))
    if _geom((y, m, d, hi), lat, lon, BEIJING_TZ)[1] <= 0:
        raise ValueError("sunrise 区间 [%g,%g] 右端仍在地面之下" % (lo, hi))
    for _ in range(60):
        mid = (lo + hi) / 2.0
        if _geom((y, m, d, mid), lat, lon, BEIJING_TZ)[1] < 0:
            lo = mid
        else:
            hi = mid
    t = (lo + hi) / 2.0
    az, _ = _geom((y, m, d, t), lat, lon, BEIJING_TZ)
    return t, az


def az_diff(a: float, b: float) -> float:
    """两方位角之差的绝对值(0..180)。"""
    return abs((a - b + 540.0) % 360.0 - 180.0)


if __name__ == "__main__":
    print("=== 对已知真值校验(北京 40N 116E, UTC+8) ===")
    for (y, m, d, note) in [
        (2025, 12, 21, "冬至: 日落约16:48 方位约243-244"),
        (2025, 6, 21, "夏至: 日出约4:50 方位约59 / 日落约19:47 方位约300"),
        (2025, 3, 20, "春分: 日出正东约90 / 日落正西约270"),
        (2025, 9, 23, "秋分: 同上"),
    ]:
        sr_t, sr_az = sunrise(y, m, d)
        ss_t, ss_az = sunset(y, m, d)
        print("  %04d-%02d-%02d  日出 %.2f时 az=%.2f | 日落 %.2f时 az=%.2f   %s"
              % (y, m, d, sr_t, sr_az, ss_t, ss_az, note))

    print()
    print("=== 负控制 1: 赤道上太阳永远正东升正西落(用 UTC) ===")
    for (y, m, d) in [(2025, 3, 20), (2025, 6, 21), (2025, 12, 21)]:
        lo, hi = 2.0, 9.0
        for _ in range(60):
            mid = (lo + hi) / 2.0
            if _geom((y, m, d, mid), 0.0, 0.0, 0.0)[1] < 0:
                lo = mid
            else:
                hi = mid
        sr = (lo + hi) / 2.0
        lo2, hi2 = 11.0, 21.0
        for _ in range(60):
            mid = (lo2 + hi2) / 2.0
            if _geom((y, m, d, mid), 0.0, 0.0, 0.0)[1] > 0:
                lo2 = mid
            else:
                hi2 = mid
        ss = (lo2 + hi2) / 2.0
        azr, _ = _geom((y, m, d, sr), 0.0, 0.0, 0.0)
        azs, _ = _geom((y, m, d, ss), 0.0, 0.0, 0.0)
        print("  %04d-%02d-%02d 日出 %.3f时 az=%.2f | 日落 %.3f时 az=%.2f"
              % (y, m, d, sr, azr, ss, azs))

    print()
    print("=== 负控制 2: 冬至日落方位应在全年最南(最小), 夏至最大 ===")
    vals = []
    for (y, m, d) in [(2025, 12, 21), (2025, 1, 15), (2025, 3, 20),
                      (2025, 6, 21), (2025, 9, 23), (2025, 11, 10)]:
        t, az = sunset(y, m, d)
        vals.append((az, "%02d-%02d" % (m, d)))
        print("  %02d-%02d 日落 az=%.2f" % (m, d, az))
    print("  最小=%.2f(%s) 最大=%.2f(%s)  -> %s"
          % (min(vals)[0], min(vals)[1], max(vals)[0], max(vals)[1],
             "冬至最南夏至最北 正确" if min(vals)[1] == "12-21" and max(vals)[1] == "06-21" else "**异常**"))

    print()
    print("=== 负控制 3: 日长 冬至最短 夏至最长 ===")
    for (y, m, d) in [(2025, 12, 21), (2025, 6, 21), (2025, 3, 20)]:
        sr, _ = sunrise(y, m, d)
        ss, _ = sunset(y, m, d)
        print("  %04d-%02d-%02d 日长 %.3f 小时" % (y, m, d, ss - sr))
