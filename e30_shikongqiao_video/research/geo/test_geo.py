"""geo 模块回归测试。Python 3.9 兼容, 无外部网络。
每条判据都配负控制, 证明它不是恒真的。
"""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import solar as S
import pierce as P
import ll2px as L


class TestSolar(unittest.TestCase):
    def test_equinox_sun_rises_east_sets_west(self):
        """春分/秋分: 日出正东(90±0.5), 日落正西(270±0.5)。负控制: 若判据恒真则任何日子都该通过。"""
        for (y, m, d) in [(2025, 3, 20), (2025, 9, 23)]:
            _, sr_az = S.sunrise(y, m, d)
            _, ss_az = S.sunset(y, m, d)
            self.assertLess(S.az_diff(sr_az, 90.0), 0.5, "春分/秋分日出应正东")
            self.assertLess(S.az_diff(ss_az, 270.0), 0.5, "春分/秋分日落应正西")

    def test_solstice_extremes(self):
        """冬至日落方位应为全年最小, 夏至最大。这是单调性判据, 恒真的实现给不出此结果。"""
        vals = {}
        for (m, d) in [(12, 21), (1, 15), (3, 20), (6, 21), (9, 23), (11, 10)]:
            vals[(m, d)] = S.sunset(2025, m, d)[1]
        winter = vals[(12, 21)]
        summer = vals[(6, 21)]
        self.assertEqual(min(vals, key=vals.get), (12, 21), "冬至日落方位应最小")
        self.assertEqual(max(vals, key=vals.get), (6, 21), "夏至日落方位应最大")
        self.assertLess(S.az_diff(winter, summer), 360.0)
        self.assertGreater(abs(summer - winter), 50.0, "冬夏日落方位差应大于50度")

    def test_day_length_extremes(self):
        for (m, d, want) in [(12, 21, "min"), (6, 21, "max")]:
            sr, _ = S.sunrise(2025, m, d)
            ss, _ = S.sunset(2025, m, d)
            L_h = ss - sr
            if want == "min":
                self.assertLess(L_h, 9.5, "冬至日长应约9.2小时")
            else:
                self.assertGreater(L_h, 14.5, "夏至日长应约14.8小时")

    def _equator_sunrise_az(self, m, d):
        lo, hi = 2.0, 9.0
        for _ in range(50):
            mid = (lo + hi) / 2
            if S._geom((2025, m, d, mid), 0.0, 0.0, 0.0)[1] < 0:
                lo = mid
            else:
                hi = mid
        az, _ = S._geom((2025, m, d, (lo + hi) / 2), 0.0, 0.0, 0.0)
        return az

    def test_equator_equinox_is_due_east(self):
        """赤道上只有春分/秋分日出正东。"""
        for (m, d) in [(3, 20), (9, 23)]:
            az = self._equator_sunrise_az(m, d)
            self.assertLess(S.az_diff(az, 90.0), 0.5, "赤道春分/秋分日出应正东")

    def test_equator_solstice_swing_equals_obliquity(self):
        """赤道夏至日出应在 90-23.44=66.56 度, 冬至在 90+23.44=113.44 度。
        这条不是恒真的: 若时角或黄赤交角处理错, 摆幅会不对。"""
        az_summer = self._equator_sunrise_az(6, 21)
        az_winter = self._equator_sunrise_az(12, 21)
        self.assertLess(S.az_diff(az_summer, 66.56), 0.5, "赤道夏至日出应偏北 23.44 度")
        self.assertLess(S.az_diff(az_winter, 113.44), 0.5, "赤道冬至日出应偏南 23.44 度")
        self.assertAlmostEqual(az_winter - az_summer, 46.88, delta=0.2,
                               msg="赤道日出方位年摆幅应约 2 倍黄赤交角")

    def test_sunrise_rejects_polar_day(self):
        """负控制: 区间不满足 alt 上升沿不变量时必须抛错, 不得静默外推。"""
        with self.assertRaises(ValueError):
            # 北极圈内夏至 -> 极昼, 全天 alt>0, 区间左端已在地平之上
            S.sunrise(2025, 6, 21, lat=80.0, lon=0.0)

    def test_az_diff_symmetric_and_bounded(self):
        self.assertAlmostEqual(S.az_diff(10.0, 350.0), 20.0, places=6)
        self.assertAlmostEqual(S.az_diff(350.0, 10.0), 20.0, places=6)
        self.assertAlmostEqual(S.az_diff(0.0, 180.0), 180.0, places=6)
        for a in range(0, 360, 7):
            self.assertLessEqual(S.az_diff(float(a), 123.4), 180.0)


class TestPierce(unittest.TestCase):
    def test_tolerance_decreases_with_pier_width(self):
        """单调性负控制: 墩越宽 -> 净跨越小 -> 容差越小。
        若实现与墩宽无关(恒真), 此测试必失败。"""
        prev = None
        for p in [0.5, 1.5, 2.5, 3.5, 4.5]:
            t = P.tolerance_deg(p)
            if prev is not None:
                self.assertLess(t, prev, "容差应随墩宽单调下降")
            prev = t

    def test_tolerance_positive_and_sane(self):
        t = P.tolerance_deg(3.0)
        self.assertGreater(t, 0.0)
        self.assertLess(t, 10.0, "容差应在 0-10 度内, 不应荒谬")

    def test_wrong_direction_gives_zero_lit(self):
        """核心负控制: 太阳方位与桥轴差 90 度时应 0 孔亮。
        恒真实现会对任何方位都给满亮。"""
        sun_az = 238.72
        self.assertEqual(P.count_lit(238.72, sun_az), 17)
        self.assertEqual(P.count_lit(238.72 + 90.0, sun_az), 0)
        self.assertEqual(P.count_lit(238.72 + 45.0, sun_az), 0)
        self.assertEqual(P.count_lit(238.72 + 180.0, sun_az), 0)

    def test_lit_count_monotone_away_from_alignment(self):
        """桥轴偏离日落方位越远, 亮孔数应单调不增。恒真实现对此无感。"""
        sun_az = 238.72
        for d in [1.0, 2.0, 3.0, 5.0]:
            self.assertLessEqual(P.count_lit(sun_az + d, sun_az),
                                 P.count_lit(sun_az + d - 1.0, sun_az),
                                 "偏离越大亮孔应不增")
        self.assertEqual(P.count_lit(sun_az + 0.0, sun_az), 17)
        self.assertLess(P.count_lit(sun_az + 1.5, sun_az), 17)

    def test_arch_derivation(self):
        self.assertAlmostEqual(P.ARCH_M, 150.0 / 17.0, places=9)
        self.assertAlmostEqual(P.span_clear(3.0), 150.0 / 17.0 - 3.0, places=9)


class TestLL2Px(unittest.TestCase):
    def test_roundtrip(self):
        cfg = L.load_cfg()
        for lon, lat in [(116.2689, 39.9975), (116.2733, 39.9940), (116.28, 40.0)]:
            px, py = L.ll2px(lon, lat, cfg)
            lon2, lat2 = L.px2ll(px, py, cfg)
            self.assertAlmostEqual(lon, lon2, places=7)
            self.assertAlmostEqual(lat, lat2, places=7)

    def test_north_is_up(self):
        """负控制: y 像素必须随纬度增大而减小(北在上)。若符号写反, 此测试失败。"""
        cfg = L.load_cfg()
        _, y_north = L.ll2px(116.27, 40.00, cfg)
        _, y_south = L.ll2px(116.27, 39.99, cfg)
        self.assertLess(y_north, y_south, "北纬的 y 应更小")

    def test_east_is_right(self):
        cfg = L.load_cfg()
        x_west, _ = L.ll2px(116.26, 40.0, cfg)
        x_east, _ = L.ll2px(116.28, 40.0, cfg)
        self.assertLess(x_west, x_east, "东经的 x 应更大")

    def test_m_per_px(self):
        self.assertGreater(L.m_per_px(40.0), 0.4)
        self.assertLess(L.m_per_px(40.0), 0.5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
