#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E21《魏公村·高梁河畔的畏吾村》Task 1: 地理切片与视觉资产预处理.

产出 assets/hist_weigongcun/ 全套资产并同步 /tmp/chemistry-video/public/weigongcun/:

  1. sanshanyuan_gaoliang_roi_4000.png
     母版《清 佚名 三山五园图》(51x88cm 扫描, 10468x6072) 高梁河/长河带切片。
     ROI (x:300..3900, y:3980..5960) 经逐区标签目视核验定界 (2026-10-03):
       - 「萬壽寺」「延慶寺」匾额 ≈(700-1150, 4380-4680), 长河石栏水道紧邻北侧
       - 「大慧寺」匾额 ≈(2500-2700, 5040-5150)
       - 白塔+「極樂寺」≈(1050-1950, 4790-5190), 西直门城楼 ≈(300-780, 5540-5960)
       - 御道南侧庙宇带「廣通寺/壽安寺/慈獻寺/壽福禪林」≈(2600-4000, 5250-5700)
     计划原拟窗口 x:5000..9500, y:3500..5800 实测为昆明湖东南-畅春园-圆明园西南,
     不含高梁河水系与万寿寺带, 故按内容核验西移 (E20 同例); Lanczos 重采样 4000x2200.

  2. beijing_1915_weigongcun_roi.png
     民国四年(1915)《實測京師四郊地圖》魏公村-万寿寺-大慧寺切片。
     来源: 中研院「北京百年历史地图」WMTS 图层 Beijing_1915 (GoogleMapsCompatible),
     z16 瓦片拼接后按 Web 墨卡托中心 (116.3105E, 39.9555N) 裁切 1920x1080.
     瓦片标签竖排右起「魏公村」「萬壽寺」「大慧寺」均已目视核验。

  3. yuanshi_lianxixian_folio.png
     《欽定元史》(文渊阁四库全书本, CADAL/Internet Archive 06056920.cn) 卷一百二十六
     〈廉希憲傳〉卒谥叶(第86叶) 原生分辨率书影: 「大星隕于正寢之旁…是夕希憲卒
     年五十…追封魏國公諡文正…從弟希賢」。
     〔内容核实〕经维基文库《元史》卷125/126/127 全文核验: 卷126 无任何「畏吾」
     字样(卷125 布鲁海牙传仅「畏吾人」)——「《元史·廉希宪传》含畏吾村记载」的
     设计表述不成立, 畏吾村葬地书证须另行溯源; 「廉孟子」「至元十七年十一月卒,
     年五十」在卷126 属实, 为 P2 引语直接书证。

  4-6. 大慧寺殿宇外观实拍 / 中央民族学院 1952 历史照 / 民大东门今貌
     (Wikimedia Commons 原件, 内容逐一目验; 大慧寺照为殿宇外观非诸天彩塑本体)

  7. mec4_composite_eras.png
     MEC-4 四时代半透明叠合图 (元代畏吾村/明代佛刹/清代长河水道/当代高校街区),
     制作组示意·纯图形零文字·非测绘拓扑; 1920x1080.

  8. sources.csv (sha256/MEC/VEC/版权留痕) + 同步 public/weigongcun/

Python 3.9.6 兼容: 无 X | None, 无 match。
"""
import csv
import hashlib
import io
import json
import math
import pathlib
import shutil
import time
import urllib.parse
import urllib.request
import fitz

from PIL import Image, ImageDraw

REPO = pathlib.Path("/Volumes/macstudio/video-projects")
OUT_DIR = REPO / "assets" / "hist_weigongcun"
PUBLIC_DIR = pathlib.Path("/tmp/chemistry-video/public/weigongcun")
CACHE_DIR = pathlib.Path("/tmp/wgc_cache")
MASTER_PATH = pathlib.Path("/Users/mac/Downloads/清 佚名 三山五园图51x88.tif")

UA = {"User-Agent": "weigongcun-asset-task/1.0 (documentary production research)"}
ACCESS_DATE = "2026-10-03"

WMTS_TEMPLATE = ("https://gis.sinica.edu.tw/beijing/file-exists.php"
                 "?img=Beijing_1915-png-%d-%d-%d")
IA_PDF_URL = "https://archive.org/download/06056920.cn/06056920.cn.pdf"
IA_FOLIO_PAGE = 86  # 1-based: 卷126〈廉希憲傳〉卒谥叶
IA_PDF_LOCAL = CACHE_DIR / "yuanshi_juan126_06056920.pdf"

COMMONS_ASSETS = [
    # (落盘名, commons 文件题名, 输出最长边重采样或 None)
    ("dahuisi_twenty_eight_devas.png", "File:Dahui Temple.jpg", None),
    ("minzu_univ_archival_1950s.png", "File:1952-06 中央民族学院 1952年.png", None),
    ("modern_weigongcun_street.png", "File:Minzu University of China (20170330115818).jpg", 2400),
]


# ---------------------------------------------------------------- helpers
def http_get(url, timeout=90):
    req = urllib.request.Request(url, headers=UA)
    last = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as exc:  # noqa: BLE001 - 重试后如实抛出
            last = exc
            time.sleep(0.8 * (attempt + 1))
    raise RuntimeError("download failed %s: %s" % (url, last))


def fetch_cached(url, cache_name):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    p = CACHE_DIR / cache_name
    if not p.exists():
        p.write_bytes(http_get(url))
    return p.read_bytes()


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def lonlat_to_mercator_px(lon, lat, zoom):
    n = 256.0 * (2 ** zoom)
    lat_r = math.radians(lat)
    x = (lon + 180.0) / 360.0 * n
    y = (1.0 - math.log(math.tan(lat_r) + 1.0 / math.cos(lat_r)) / math.pi) / 2.0 * n
    return x, y


def save_rgb_optimized(im, out_path):
    """任务书约束 RGBA/RGB: 全彩 RGB 直接保存(optimize), 不做调色板降档.

    (E20 的 15MB 限额是其内部 OOM 启发式; E21 任务书未设限额,
    Remotion OOM 取决于解码后纹理尺寸, 与文件字节无关.)
    """
    im.convert("RGB").save(out_path, optimize=True)
    return out_path.stat().st_size


# ------------------------------------------------- 1. 三山五园图高梁河切片
ROI_X0, ROI_Y0, ROI_X1, ROI_Y1 = 300, 3980, 3900, 5960
TARGET_SIZE = (4000, 2200)  # 与 ROI 同比 (3600x1980 -> 4000x2200)


def build_sanshanyuan_roi(out_path):
    if not MASTER_PATH.exists():
        raise SystemError("母版缺失: %s" % MASTER_PATH)
    Image.MAX_IMAGE_PIXELS = None
    master = Image.open(MASTER_PATH)
    roi = master.crop((ROI_X0, ROI_Y0, ROI_X1, ROI_Y1))
    roi = roi.resize(TARGET_SIZE, Image.LANCZOS)
    size = save_rgb_optimized(roi, out_path)
    return size, "RGB"


# --------------------------------------------- 2. 1915 实测京师四郊图切片
Z1915 = 16
MERC_CENTER = (116.3105, 39.9555)  # 魏公村/万寿寺带中心
BBOX_1915 = (116.288, 39.9660, 116.333, 39.9450)  # lon0 lat0 lon1 lat1


WMTS_CACHE = pathlib.Path("/tmp/cache_wmts_1915")

def build_1915_roi(out_path):
    lon0, lat0, lon1, lat1 = BBOX_1915
    x0, y0 = lonlat_to_mercator_px(lon0, lat0, Z1915)
    x1, y1 = lonlat_to_mercator_px(lon1, lat1, Z1915)
    c0, r0 = int(x0 // 256), int(y0 // 256)
    c1, r1 = int(x1 // 256), int(y1 // 256)
    WMTS_CACHE.mkdir(parents=True, exist_ok=True)
    mosaic = Image.new("RGB", ((c1 - c0 + 1) * 256, (r1 - r0 + 1) * 256), (255, 0, 255))
    for col in range(c0, c1 + 1):
        for row in range(r0, r1 + 1):
            tile_cache_path = WMTS_CACHE / f"tile_{Z1915}_{col}_{row}.png"
            if tile_cache_path.exists():
                blob = tile_cache_path.read_bytes()
            else:
                blob = http_get(WMTS_TEMPLATE % (Z1915, col, row))
                tile_cache_path.write_bytes(blob)
                time.sleep(0.05)
            tile = Image.open(io.BytesIO(blob)).convert("RGB")
            mosaic.paste(tile, ((col - c0) * 256, (row - r0) * 256))
    cx, cy = lonlat_to_mercator_px(MERC_CENTER[0], MERC_CENTER[1], Z1915)
    ox, oy = int(cx - x0 - 960), int(cy - y0 - 540)
    if ox < 0 or oy < 0 or ox + 1920 > mosaic.width or oy + 1080 > mosaic.height:
        raise SystemError("1915 裁切窗口越界: origin=(%d,%d) mosaic=%s" % (ox, oy, mosaic.size))
    crop = mosaic.crop((ox, oy, ox + 1920, oy + 1080))
    # 洋红底 = 瓦片缺失哨兵; 出现即失败
    colors = crop.getcolors(maxcolors=1 << 24)
    for cnt, rgb in colors:
        if rgb == (255, 0, 255):
            raise SystemError("1915 拼接存在缺失瓦片(洋红哨兵)")
    crop.save(out_path)
    return out_path.stat().st_size


# ---------------------------------------------------- 3. 元史廉希宪传书影
def build_yuanshi_folio(out_path):
    fetch_cached(IA_PDF_URL, IA_PDF_LOCAL.name)
    doc = fitz.open(str(IA_PDF_LOCAL))
    page = doc[IA_FOLIO_PAGE - 1]
    info = doc.extract_image(page.get_images(full=True)[0][0])
    zoom = info["width"] / float(page.rect.width)  # 原生扫描分辨率, 不做超采样
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    im.save(out_path)
    return out_path.stat().st_size, im.size


# ---------------------------------------------------- 4-6. Commons 实拍照
def build_commons_assets():
    sizes = {}
    for out_name, commons_title, max_side in COMMONS_ASSETS:
        info = _commons_imageinfo(commons_title)
        blob = fetch_cached(info["url"], out_name + ".orig")
        im = Image.open(io.BytesIO(blob)).convert("RGB")
        if max_side and max(im.size) > max_side:
            s = max_side / float(max(im.size))
            im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
        out_path = OUT_DIR / out_name
        im.save(out_path)
        sizes[out_name] = (info, im.size, out_path.stat().st_size)
    return sizes


def _commons_imageinfo(title):
    q = ("https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo"
         "&iiprop=url|size|extmetadata&format=json&titles=")
    data = http_get(q + urllib.parse.quote(title))
    pages = json.loads(data)["query"]["pages"]
    for _, page in pages.items():
        ii = page["imageinfo"][0]
        return {
            "url": ii["url"],
            "w": ii["width"],
            "h": ii["height"],
            "license": ii.get("extmetadata", {}).get("LicenseShortName", {}).get("value", ""),
        }
    raise SystemError("Commons imageinfo 未命中: %s" % title)


# ------------------------------------------------- 7. MEC-4 四时代叠合图
W, H = 1920, 1080
PAPER = (239, 230, 208)
GRID = (226, 215, 190)

OCHRE_YUAN = (168, 69, 44)      # 元代畏吾村
INDIGO_MING = (47, 93, 124)     # 明代佛刹
DEEPGREEN_QING = (61, 107, 84)  # 清代长河水道
SLATE_TODAY = (90, 98, 120)     # 当代高校街区

RIVER = (154, 176, 190)
RIVER_LINE = (47, 93, 124)


def _blob(cx, cy, rx, ry, n=48, seed=7, wobble=0.16):
    """确定性有机多边形 (无随机状态, 重跑逐像素一致), E20 同法."""
    pts = []
    for i in range(n):
        a = 2.0 * math.pi * i / n
        k = 1.0 + wobble * math.sin(seed * 3.1 + a * 2.0) * math.cos(seed + a * 5.0)
        pts.append((cx + rx * k * math.cos(a), cy + ry * k * math.sin(a)))
    return [(round(x), round(y)) for x, y in pts]


# 地理空间基线: 上北(y小)下南(y大), 左西(x小)右东(x大)
# 高梁河/南长河位于画面南部(y≈740..850), 畏吾村位于高梁河北岸台地(y≈320..440)
VILLAGE_HUTS = [(740, 360), (820, 330), (880, 370), (780, 420), (860, 430),
                (920, 360), (710, 400), (910, 420)]
# 明代佛刹: 大慧寺位于畏吾村北侧(820, 250), 万寿寺/延庆寺等位于长河北岸水际(420, 680)
MING_TEMPLES = [(820, 250), (420, 680), (1350, 720), (1600, 740)]
# 清代长河码头与沿河御道(位于南部水系旁)
QING_DOCKS = [(400, 715), (800, 740), (1250, 775), (1650, 815)]
# 当代高校园区与街区(位于北部高地)
TODAY_BLOCKS = [(680, 180, 240, 150), (1020, 180, 260, 140), (1340, 220, 220, 160),
                (700, 350, 220, 130), (1020, 340, 250, 140), (1320, 400, 220, 100)]
TODAY_ROADS = [(0, 520), (1920, 520)]


def _draw_layer(spec):
    """spec: callable(draw)->None, 在透明层上绘制后整体 alpha 合成."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(layer)
    spec(dr)
    return layer


def draw_river_base(dr):
    """长河/高梁河水系骨架 (南部带状双线, 左西右东, 自西北流向东南)."""
    pts = [(0, 750), (280, 740), (580, 730), (880, 760), (1200, 790),
           (1550, 830), (1920, 860)]
    dr.line(pts, fill=RIVER, width=46)
    dr.line([(x, y - 20) for x, y in pts], fill=RIVER_LINE, width=3)
    dr.line([(x, y + 20) for x, y in pts], fill=RIVER_LINE, width=3)


def era_yuan(dr):
    """元代: 畏吾村聚落 (北部高梁河北岸台地, 虚线村域圈)."""
    dr.polygon(_blob(820, 380, 200, 120, seed=21), outline=OCHRE_YUAN + (170,), width=4)
    for i, (hx, hy) in enumerate(VILLAGE_HUTS):
        dr.polygon([(hx, hy - 16), (hx + 20, hy), (hx, hy + 14), (hx - 20, hy)],
                   fill=OCHRE_YUAN + (110,), outline=OCHRE_YUAN + (200,))
        if i % 3 == 0:
            dr.rectangle([hx - 2, hy - 26, hx + 2, hy - 14], fill=OCHRE_YUAN + (150,))


def era_ming(dr):
    """明代: 佛刹带 (大慧寺在北, 万寿寺在水际)."""
    for tx, ty in MING_TEMPLES:
        dr.rectangle([tx - 34, ty - 14, tx + 34, ty + 22], fill=INDIGO_MING + (95,),
                     outline=INDIGO_MING + (190,))
        dr.polygon([(tx, ty - 52), (tx + 16, ty - 22), (tx - 16, ty - 22)],
                   fill=INDIGO_MING + (120,), outline=INDIGO_MING + (200,))
        dr.rectangle([tx - 3, ty - 34, tx + 3, ty - 20], fill=INDIGO_MING + (160,))


def era_qing(dr):
    """清代: 皇家水道 (南部水系御道/码头/南岸稻田)."""
    dr.line([(60, 810), (520, 800), (1000, 830), (1500, 870), (1880, 900)],
            fill=DEEPGREEN_QING + (150,), width=8)
    for dx, dy in QING_DOCKS:
        dr.rectangle([dx - 14, dy - 8, dx + 14, dy + 8], fill=DEEPGREEN_QING + (140,),
                     outline=DEEPGREEN_QING + (200,))
    for (fx, fy, fw, fh) in [(200, 880, 160, 90), (700, 890, 180, 80), (1200, 920, 160, 80)]:
        for yy in range(fy, fy + fh, 12):
            dr.line([(fx, yy), (fx + fw - 6, yy)], fill=DEEPGREEN_QING + (70,), width=2)


def era_today(dr):
    """当代: 高校街区 (北部正交路网+院系楼块)."""
    dr.line(TODAY_ROADS, fill=SLATE_TODAY + (160,), width=14)
    dr.line([(960, 0), (960, 720)], fill=SLATE_TODAY + (160,), width=10)
    for (bx, by, bw, bh) in TODAY_BLOCKS:
        dr.rectangle([bx, by, bx + bw, by + bh], fill=SLATE_TODAY + (80,),
                     outline=SLATE_TODAY + (180,))


def build_mec4_composite(out_path):
    im = Image.new("RGBA", (W, H), PAPER + (255,))
    dr = ImageDraw.Draw(im)
    for gy in range(0, H, 120):
        dr.line([(0, gy), (W, gy)], fill=GRID, width=1)
    for gx in range(0, W, 120):
        dr.line([(gx, 0), (gx, H)], fill=GRID, width=1)
    im = Image.alpha_composite(im.convert("RGBA"), _draw_layer(draw_river_base))
    for era in (era_qing, era_ming, era_yuan, era_today):  # 早层在下, 当代在上
        im = Image.alpha_composite(im, _draw_layer(era))
    im.convert("RGB").save(out_path)
    return out_path.stat().st_size


# --------------------------------------------------------- sources.csv
CSV_FIELDS = ["file", "title", "period", "archive", "shelfmark", "url",
              "access_date", "rights", "sha256", "mec", "vec"]


def write_sources_csv(rows):
    path = OUT_DIR / "sources.csv"
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        for row in rows:
            w.writerow(row)
    return path


def main():
    for d in (OUT_DIR, PUBLIC_DIR):
        d.mkdir(parents=True, exist_ok=True)

    # 1. 三山五园图高梁河带切片
    p1 = OUT_DIR / "sanshanyuan_gaoliang_roi_4000.png"
    if not p1.exists():
        size1, mode1 = build_sanshanyuan_roi(p1)
    print("1. %s ready (%d bytes)" % (p1.name, p1.stat().st_size))

    # 2. 1915 实测京师四郊图切片
    p2 = OUT_DIR / "beijing_1915_weigongcun_roi.png"
    if not p2.exists():
        size2 = build_1915_roi(p2)
    print("2. %s ready (%d bytes)" % (p2.name, p2.stat().st_size))

    # 3. 元史卷126 廉希宪传卒谥叶书影
    p3 = OUT_DIR / "yuanshi_lianxixian_folio.png"
    if not p3.exists():
        size3, dims3 = build_yuanshi_folio(p3)
    print("3. %s ready (%d bytes)" % (p3.name, p3.stat().st_size))

    # 4-6. Commons 实拍照三件
    for name, _, _ in COMMONS_ASSETS:
        if not (OUT_DIR / name).exists():
            build_commons_assets()
            break
    print("4-6. Commons assets ready")


    # 7. MEC-4 四时代叠合图
    p7 = OUT_DIR / "mec4_composite_eras.png"
    size7 = build_mec4_composite(p7)
    print("7. %s 1920x1080 %d bytes" % (p7.name, size7))

    # 8. sources.csv
    rows = [
        {
            "file": "sanshanyuan_gaoliang_roi_4000.png",
            "title": ("三山五园图高梁河/长河带切片(西直门-高梁桥-极乐寺白塔-萬壽寺延慶寺-"
                      "大慧寺-廣通寺御道庙宇带;标签目视核验)"),
            "period": "清晚期(绘有颐和园名/不早于1888)",
            "archive": ("清·佚名《三山五园图》51x88cm 绘本扫描母版(10468x6072) "
                        "ROI(300/3980/3900/5960) Lanczos重采样4000x2200/"
                        "切片脚本 scripts/extract_weigongcun_assets.py"),
            "shelfmark": "—",
            "url": "file:///Users/mac/Downloads/清 佚名 三山五园图51x88.tif",
            "access_date": ACCESS_DATE,
            "rights": "母版来源待核/制作研究用",
            "sha256": sha256_of(p1),
            "mec": "MEC-1",
            "vec": "VEC-1",
        },
        {
            "file": "beijing_1915_weigongcun_roi.png",
            "title": ("《實測京師四郊地圖》(1915)魏公村-萬壽寺-大慧寺切片"
                      "(图内竖排右起标签「魏公村」「萬壽寺」「大慧寺」目视核验;"
                      "Web墨卡托z16瓦片拼接, 中心116.3105E/39.9555N, 裁切1920x1080)"),
            "period": "民国四年(1915)",
            "archive": "中研院人文社会科学研究中心「北京百年历史地图」WMTS 图层 Beijing_1915",
            "shelfmark": "—",
            "url": "https://gis.sinica.edu.tw/beijing/wmts",
            "access_date": ACCESS_DATE,
            "rights": "中研院图资/学术研究用",
            "sha256": sha256_of(p2),
            "mec": "MEC-2",
            "vec": "VEC-2",
        },
        {
            "file": "yuanshi_lianxixian_folio.png",
            "title": ("《欽定元史》(文渊阁四库全书本)卷一百二十六〈廉希憲傳〉卒谥叶书影"
                      "(「大星隕于正寢之旁…是夕希憲卒年五十/追封魏國公諡文正/從弟希賢」)"
                      "〔内容核实: 经维基文库元史卷125/126/127全文核验, 卷126无「畏吾」字样——"
                      "原设计「元史含畏吾村记载」不成立, 畏吾村葬地书证待另行溯源;"
                      "「廉孟子」「至元十七年十一月卒年五十」在卷126属实, 为P2引语直接书证〕"),
            "period": "清乾隆四库钞本(史源为明洪武刊元史)",
            "archive": "《欽定元史》四库本 CADAL 扫描(Internet Archive 06056920.cn)第86叶原生分辨率",
            "shelfmark": "四库本",
            "url": "https://archive.org/details/06056920.cn",
            "access_date": ACCESS_DATE,
            "rights": "公共领域(古籍扫描)",
            "sha256": sha256_of(p3),
            "mec": "—",
            "vec": "VEC-1",
        },
        {
            "file": "dahuisi_twenty_eight_devas.png",
            "title": ("大慧寺(北京海淀·国保5-199)大悲宝殿明代殿宇外观实拍"
                      "〔内容核实: 照片为大殿外景, 非二十八诸天彩塑本体; 诸天塑像在殿内, "
                      "塑像本体影像待授权获取〕"),
            "period": "明(寺)/2010s(摄)",
            "archive": "Wikimedia Commons「Dahui Temple.jpg」1600x1155",
            "shelfmark": "—",
            "url": "https://commons.wikimedia.org/wiki/File:Dahui_Temple.jpg",
            "access_date": ACCESS_DATE,
            "rights": "CC BY-SA 3.0",
            "sha256": sha256_of(OUT_DIR / "dahuisi_twenty_eight_devas.png"),
            "mec": "—",
            "vec": "VEC-3",
        },
        {
            "file": "minzu_univ_archival_1950s.png",
            "title": ("中央民族学院建校初期影像(1952, 大礼堂式主楼与1950年代轿车)"
                      "〔内容核实: 黑白历史档案照〕"),
            "period": "1952",
            "archive": "Wikimedia Commons「1952-06 中央民族学院 1952年.png」1104x577",
            "shelfmark": "—",
            "url": "https://commons.wikimedia.org/wiki/File:1952-06_中央民族学院_1952年.png",
            "access_date": ACCESS_DATE,
            "rights": "公共领域",
            "sha256": sha256_of(OUT_DIR / "minzu_univ_archival_1950s.png"),
            "mec": "—",
            "vec": "VEC-2",
        },
        {
            "file": "modern_weigongcun_street.png",
            "title": "中央民族大学东门今貌(2017, 魏公村街区; 重采样2400px)",
            "period": "2017",
            "archive": "Wikimedia Commons「Minzu University of China (20170330115818).jpg」3264x2278",
            "shelfmark": "—",
            "url": "https://commons.wikimedia.org/wiki/File:Minzu_University_of_China_(20170330115818).jpg",
            "access_date": ACCESS_DATE,
            "rights": "CC BY-SA 4.0",
            "sha256": sha256_of(OUT_DIR / "modern_weigongcun_street.png"),
            "mec": "—",
            "vec": "VEC-2",
        },
        {
            "file": "mec4_composite_eras.png",
            "title": ("MEC-4 四时代半透明叠合图(元代畏吾村/明代佛刹/清代长河水道/当代高校街区)"
                      "制作组示意·纯图形零文字·非测绘拓扑"),
            "period": "叠合示意",
            "archive": "制作组生成(scripts/extract_weigongcun_assets.py 内置 builder)",
            "shelfmark": "—",
            "url": "scripts/extract_weigongcun_assets.py",
            "access_date": ACCESS_DATE,
            "rights": "制作组示意/非测绘图",
            "sha256": sha256_of(p7),
            "mec": "MEC-4",
            "vec": "VEC-4",
        },
    ]
    csv_path = write_sources_csv(rows)
    print("8. %s %d rows" % (csv_path, len(rows)))

    # 同步工程 public/
    for f in sorted(OUT_DIR.iterdir()):
        if f.is_file():
            shutil.copy2(f, PUBLIC_DIR / f.name)
    print("synced -> %s (%d files)" % (PUBLIC_DIR, len(list(PUBLIC_DIR.iterdir()))))


if __name__ == "__main__":
    main()
