"""z18 mosaic 经纬度 <-> 像素。Python 3.9 兼容。"""
import json, math, os

Z = 18
N = 2 ** Z
TILE = 256
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = "/Volumes/macstudio/video-projects/yihheyuan_video/research"


def load_cfg():
    with open(os.path.join(SRC, "geo_transform.json"), encoding="utf-8") as f:
        return json.load(f)


def lat2y(lat):
    r = math.radians(lat)
    return (1.0 - math.log(math.tan(r) + 1.0 / math.cos(r)) / math.pi) / 2.0 * N


def lon2x(lon):
    return (lon + 180.0) / 360.0 * N


def mosaic_origin(cfg=None):
    cfg = cfg or load_cfg()
    tx0 = int(math.floor(lon2x(cfg["lon_tl"])))
    ty0 = int(math.floor(lat2y(cfg["lat_tl"])))
    return tx0, ty0


def ll2px(lon, lat, cfg=None):
    cfg = cfg or load_cfg()
    tx0, ty0 = mosaic_origin(cfg)
    fx = (lon2x(lon) - tx0) * TILE
    fy = (lat2y(lat) - ty0) * TILE
    return fx, fy


def px2ll(px, py, cfg=None):
    cfg = cfg or load_cfg()
    tx0, ty0 = mosaic_origin(cfg)
    x = tx0 + px / TILE
    y = ty0 + py / TILE
    lon = x / N * 360.0 - 180.0
    n = math.pi - 2.0 * math.pi * y / N
    lat = math.degrees(math.atan(math.sinh(n)))
    return lon, lat


def m_per_px(lat):
    return 156543.03392 * math.cos(math.radians(lat)) / N


if __name__ == "__main__":
    cfg = load_cfg()
    tx0, ty0 = mosaic_origin(cfg)
    print("tile origin z%d: x=%d y=%d" % (Z, tx0, ty0))
    for nm, lon, lat in [("佛香阁", 116.2755, 39.9985),
                         ("廓如亭?", 116.2815, 39.9996),
                         ("玉带桥", 116.2560, 40.0000)]:
        px, py = ll2px(lon, lat, cfg)
        print("  %-8s (%.4f,%.4f) -> px (%.0f, %.0f)" % (nm, lon, lat, px, py))
    print("m/px @40N: %.3f" % m_per_px(40.0))
    # 往返自检
    px, py = ll2px(116.2755, 39.9985, cfg)
    print("roundtrip:", ["%.7f" % v for v in px2ll(px, py, cfg)])
