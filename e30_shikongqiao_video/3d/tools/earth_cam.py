"""从 Google Earth 网页 URL 读出相机中心经纬度与视高, 并换算成 WGS-84。

用法(在 omp 的 JS eval 里):
    const tab = await browser.open({name:"earth", persist:true});
    // 用户在 Earth 上缩放定位后:
    const cam = await tab.run(`return extractCam();`)   // 见下
Earth URL 相机格式:
    /web/@<lat>,<lon>,<alt><a|d>,<heading>d,<pitch><t|y>,<range>h,<fov>h,<roll>r
  alt + 'a' = 以米为单位的绝对视高, 'd' = 以地面为基准
  用 GCJ-02 -> WGS-84 折算(Google 全系用 GCJ-02; Earth 亦然)
负控制: 输入不含 @ 的 URL 必须报错, 不得静默返回 None。
"""
import re
import math
import importlib.util

_CRS = "/Volumes/macstudio/video-projects/yihheyuan_video/research/geo/crs.py"
spec = importlib.util.spec_from_file_location("crs", _CRS)
crs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crs)

PAT = re.compile(r"/web/(?:search/[^/]*?)?@(-?[\d.]+),(-?[\d.]+),(-?[\d.]+)([ad])")


def parse(url):
    m = PAT.search(url)
    if not m:
        raise ValueError("URL 中无 /web/@ 相机段: %s" % url[:120])
    lat = float(m.group(1))
    lon = float(m.group(2))
    alt = float(m.group(3))
    unit = m.group(4)
    wlon, wlat = crs.gcj02_to_wgs84(lon, lat)     # Google 相机是 GCJ-02
    return {"gcj_lon": lon, "gcj_lat": lat,
            "wgs_lon": wlon, "wgs_lat": wlat,
            "altitude_m": alt, "alt_unit": unit,
            "offset_m": math.hypot((wlon - lon) * 111320 * math.cos(math.radians(wlat)),
                                   (wlat - lat) * 111320)}


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        print(parse(sys.argv[1]))
    else:
        print(__doc__)
        for bad in ("https://earth.google.com/web/", "https://example.com"):
            try:
                parse(bad)
                print("负控制失败: %s 未被拒绝" % bad)
            except ValueError as e:
                print("负控制通过:", e)
