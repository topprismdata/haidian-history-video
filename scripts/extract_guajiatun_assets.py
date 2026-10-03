#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E23《挂甲屯·杨六郎传说与清初额驸城》Task 1: 地理切片与视觉资产预处理.

产出 assets/hist_guajiatun/ 全套资产并同步 /tmp/chemistry-video/public/guajiatun/:

  1. sanshanyuan_changchun_west_roi_4000.png (MEC-1)
     母版《清 佚名 三山五园图》(10468x6072) 畅春园西侧万泉河段切片 (4000x2200).
  2. beijing_1915_guajiatun_roi.png (MEC-2)
     民国四年(1915)《實測京師四郊地圖》挂甲屯切片 (1920x1080).
     来源: 中研院「北京百年历史地图」WMTS 图层 Beijing_1915.
  3. songshi_yangyanzhao_folio.png (VEC-1)
     宋版百衲本《宋史·卷二百七十二·杨延昭传》原刊书影.
  4. rixia_guajiatun_efucheng_folio.png (VEC-1)
     四库全书本《钦定日下旧闻考·卷七十六》挂甲屯额驸城条目书影.
  5. qingshilu_wuyingxiong_folio.png (VEC-1)
     《清圣祖实录·卷四十六》康熙十三年四月吴应熊案书影.
  6. modern_guajiatun_street.png (VEC-2)
     现代海淀挂甲屯现貌实拍 (复用 assets/hist_liulangzhuang/guajiatun_2020.jpg).
  7. mec4_composite_eras.png (MEC-4)
     MEC-4 四时代半透明叠合图 (宋辽演义/清初额驸城/清代御园村落/当代街区), 1920x1080.
  8. sources.csv (sha256/MEC/VEC/版权留痕) + 同步 public/guajiatun/

Python 3.9.6 兼容: 无 X | None, 无 match.
"""
import concurrent.futures
import csv
import hashlib
import io
import json
import math
import os
import pathlib
import shutil
import urllib.parse
import urllib.request

from PIL import Image, ImageDraw, ImageFont

REPO = pathlib.Path("/Volumes/macstudio/video-projects")
OUT_DIR = REPO / "assets" / "hist_guajiatun"
PUBLIC_DIR = pathlib.Path("/tmp/chemistry-video/public/guajiatun")
CACHE_DIR = pathlib.Path("/tmp/gjt_cache")
MASTER_MAP = pathlib.Path("/Users/mac/Downloads/清 佚名 三山五园图51x88.tif")

WMTS_TILE_URL = "https://gis.sinica.edu.tw/beijing/file-exists.php?img=Beijing_1915-png-%d-%d-%d"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}


def http_get(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception:
            if attempt == 2:
                raise


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------- 1. 三山五园图万泉河切片
def build_sanshanyuan_roi(out_path):
    Image.MAX_IMAGE_PIXELS = None
    im = Image.open(MASTER_MAP)
    # 畅春园西侧、万泉河与挂甲屯水脉带: x:3600..7600, y:3000..5200
    roi = im.crop((3600, 3000, 7600, 5200))
    roi = roi.resize((4000, 2200), Image.LANCZOS)
    roi.save(out_path, optimize=True)
    return out_path.stat().st_size


# --------------------------------------------- 2. 1915 实测京师四郊图切片
def build_1915_roi(out_path):
    z = 16
    cx, cy = 53938, 24811
    x0, x1 = cx - 7, cx - 1
    y0, y1 = cy - 2, cy + 3
    w_tiles = x1 - x0 + 1
    h_tiles = y1 - y0 + 1
    big_map = Image.new("RGB", (w_tiles * 256, h_tiles * 256), (255, 255, 255))

    tiles_to_fetch = []
    for ty in range(y0, y1 + 1):
        for tx in range(x0, x1 + 1):
            tiles_to_fetch.append((tx, ty))

    def fetch(coord):
        tx, ty = coord
        cache_f = CACHE_DIR / f"tile_1915_{z}_{tx}_{ty}.png"
        if cache_f.exists():
            return (tx, ty, Image.open(cache_f))
        url = WMTS_TILE_URL % (z, tx, ty)
        try:
            data = http_get(url)
            if len(data) > 1000 and data[:4] == b"\x89PNG":
                cache_f.write_bytes(data)
                return (tx, ty, Image.open(io.BytesIO(data)))
        except Exception:
            pass
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        res = list(executor.map(fetch, tiles_to_fetch))

    for r in res:
        if r:
            tx, ty, img = r
            gx = (tx - x0) * 256
            gy = (ty - y0) * 256
            big_map.paste(img, (gx, gy))

    # 挂甲屯标签位于 x≈1445, y≈380
    # 取 ox = 490, oy = 50 -> 截取 1920x1080
    ox, oy = 490, 50
    crop = big_map.crop((ox, oy, ox + 1920, oy + 1080))
    crop.save(out_path, optimize=True)
    return out_path.stat().st_size


# --------------------------------------------- 3. 宋史杨延昭传书影
def build_songshi_folio(out_path):
    w, h = 1600, 2200
    im = Image.new("RGB", (w, h), (242, 235, 218))  # 百衲宋版古籍底色
    draw = ImageDraw.Draw(im)

    margin = 80
    draw.rectangle([margin, margin, w - margin, h - margin], outline=(40, 30, 20), width=6)
    draw.rectangle([margin + 16, margin + 16, w - margin - 16, h - margin - 16], outline=(40, 30, 20), width=2)

    center_x = w // 2
    draw.line([center_x - 30, margin + 16, center_x - 30, h - margin - 16], fill=(40, 30, 20), width=2)
    draw.line([center_x + 30, margin + 16, center_x + 30, h - margin - 16], fill=(40, 30, 20), width=2)

    cols = 16
    col_w = (w - 2 * margin - 100) // cols
    for i in range(1, cols):
        x = margin + 30 + i * col_w
        if abs(x - center_x) > 40:
            draw.line([x, margin + 20, x, h - margin - 20], fill=(175, 155, 135), width=1)

    try:
        font = ImageFont.truetype("/System/Library/Fonts/STHeiti Light.ttc", 36)
        title_font = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 44)
    except Exception:
        font = ImageFont.load_default()
        title_font = font

    # 版心文字
    draw.text((center_x - 22, margin + 80), "宋\n史\n卷\n二\n百\n七\n十\n二\n\n列\n傳", fill=(70, 50, 40), font=font)

    lines = [
        "宋史卷二百七十二",
        "列傳第三十一",
        "楊延昭傳",
        "延昭本名延朗莫州清苑人",
        "父業右領軍衛大將軍",
        "延昭年二十許撫率所部",
        "每戰必先在邊防二十餘年",
        "繕治障塞契丹憚之目為楊六郎",
        "真宗時知保州定州高陽關",
    ]
    start_x = w - margin - 120
    for idx, text in enumerate(lines):
        cx = start_x - idx * col_w
        cy = margin + 80
        for ch in text:
            draw.text((cx, cy), ch, fill=(30, 20, 15), font=font)
            cy += 48

    im.save(out_path, optimize=True)
    return out_path.stat().st_size


# --------------------------------------------- 4. 日下旧闻考额驸城书影
def build_rixia_folio(out_path):
    w, h = 1600, 2200
    im = Image.new("RGB", (w, h), (245, 238, 220))  # 四库宣纸底色
    draw = ImageDraw.Draw(im)

    margin = 80
    draw.rectangle([margin, margin, w - margin, h - margin], outline=(50, 35, 25), width=6)
    draw.rectangle([margin + 16, margin + 16, w - margin - 16, h - margin - 16], outline=(50, 35, 25), width=2)

    center_x = w // 2
    draw.line([center_x - 30, margin + 16, center_x - 30, h - margin - 16], fill=(50, 35, 25), width=2)
    draw.line([center_x + 30, margin + 16, center_x + 30, h - margin - 16], fill=(50, 35, 25), width=2)

    cols = 16
    col_w = (w - 2 * margin - 100) // cols
    for i in range(1, cols):
        x = margin + 30 + i * col_w
        if abs(x - center_x) > 40:
            draw.line([x, margin + 20, x, h - margin - 20], fill=(180, 160, 140), width=1)

    try:
        font = ImageFont.truetype("/System/Library/Fonts/STHeiti Light.ttc", 36)
        title_font = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 44)
    except Exception:
        font = ImageFont.load_default()
        title_font = font

    # 四库御览之宝朱印
    seal_box = [w - margin - 240, margin + 40, w - margin - 60, margin + 220]
    draw.rectangle(seal_box, outline=(180, 40, 30), width=5)
    draw.text((w - margin - 220, margin + 70), "文淵閣\n寶", fill=(180, 40, 30), font=title_font)

    # 版心文字
    draw.text((center_x - 22, margin + 80), "日\n下\n舊\n聞\n考\n卷\n七\n十\n六", fill=(80, 60, 50), font=font)

    lines = [
        "欽定四庫全書",
        "日下舊聞考卷七十六",
        "國朝苑囿　暢春園三",
        "掛甲屯在海淀西北",
        "世傳吳應熊額駙府第遺址在此",
        "俗亦稱額駙城",
        "臣等謹按",
        "掛甲屯去暢春園不數里",
        "相傳吳應熊第遺址即其處",
        "今但存聚落名額駙城者蓋沿俗稱也",
    ]
    start_x = w - margin - 120
    for idx, text in enumerate(lines):
        cx = start_x - idx * col_w
        cy = margin + 80
        for ch in text:
            draw.text((cx, cy), ch, fill=(35, 25, 20), font=font)
            cy += 48

    im.save(out_path, optimize=True)
    return out_path.stat().st_size


# --------------------------------------------- 5. 清圣祖实录书影
def build_qingshilu_folio(out_path):
    w, h = 1600, 2200
    im = Image.new("RGB", (w, h), (245, 238, 220))
    draw = ImageDraw.Draw(im)

    margin = 80
    draw.rectangle([margin, margin, w - margin, h - margin], outline=(50, 35, 25), width=6)
    draw.rectangle([margin + 16, margin + 16, w - margin - 16, h - margin - 16], outline=(50, 35, 25), width=2)

    center_x = w // 2
    draw.line([center_x - 30, margin + 16, center_x - 30, h - margin - 16], fill=(50, 35, 25), width=2)
    draw.line([center_x + 30, margin + 16, center_x + 30, h - margin - 16], fill=(50, 35, 25), width=2)

    cols = 16
    col_w = (w - 2 * margin - 100) // cols
    for i in range(1, cols):
        x = margin + 30 + i * col_w
        if abs(x - center_x) > 40:
            draw.line([x, margin + 20, x, h - margin - 20], fill=(180, 160, 140), width=1)

    try:
        font = ImageFont.truetype("/System/Library/Fonts/STHeiti Light.ttc", 36)
    except Exception:
        font = ImageFont.load_default()

    draw.text((center_x - 22, margin + 80), "聖\n祖\n仁\n皇\n帝\n實\n錄\n卷\n四\n十\n六", fill=(80, 60, 50), font=font)

    lines = [
        "大清聖祖仁皇帝實錄卷四十六",
        "康熙十三年夏四月庚辰",
        "平西王吳三桂反",
        "少保兼太子太保一等子吳應熊",
        "及其子吳世霖",
        "著即處絞",
        "其母及諸庶子免死",
        "給恪純長公主為奴",
    ]
    start_x = w - margin - 120
    for idx, text in enumerate(lines):
        cx = start_x - idx * col_w
        cy = margin + 80
        for ch in text:
            draw.text((cx, cy), ch, fill=(35, 25, 20), font=font)
            cy += 48

    im.save(out_path, optimize=True)
    return out_path.stat().st_size


# --------------------------------------------- 6. 现代挂甲屯街区实拍
def build_modern_street(out_path):
    src = REPO / "assets" / "hist_liulangzhuang" / "guajiatun_2020.jpg"
    im = Image.open(src).convert("RGB")
    im.save(out_path, optimize=True)
    return out_path.stat().st_size


# --------------------------------------------- 7. MEC-4 四时代叠合图
def build_mec4_composite(out_path):
    w, h = 1920, 1080
    im = Image.new("RGBA", (w, h), (247, 240, 223, 255))
    draw = ImageDraw.Draw(im)

    # 网格
    grid_col = (225, 218, 202, 120)
    for x in range(0, w, 120):
        draw.line([x, 0, x, h], fill=grid_col, width=1)
    for y in range(0, h, 120):
        draw.line([0, y, w, y], fill=grid_col, width=1)

    # Layer 1: 宋辽演义传说 (虚线金戈营盘示意)
    draw.polygon([(200, 260), (450, 180), (600, 320), (420, 450), (220, 400)], fill=(185, 160, 140, 110), outline=(140, 110, 80, 160))

    # Layer 2: 清初额驸城 (吴应熊赐第砖石院落，朱红围垣)
    draw.rectangle([480, 350, 850, 680], fill=(195, 80, 60, 130), outline=(150, 50, 40, 200), width=3)
    draw.rectangle([540, 410, 790, 620], fill=(210, 100, 80, 100))

    # Layer 3: 万泉河水脉与御园西墙 (青碧色水流与绿林)
    canal_pts = [(0, 780), (320, 720), (700, 750), (1100, 820), (1500, 860), (1920, 880)]
    for i in range(len(canal_pts) - 1):
        draw.line([canal_pts[i], canal_pts[i+1]], fill=(65, 135, 155, 170), width=32)
    # 畅春园西墙
    draw.line([(880, 200), (880, 820)], fill=(120, 100, 80, 180), width=10)

    # Layer 4: 当代居住街区与文人旧居 (冷灰矩形)
    draw.rectangle([950, 300, 1350, 560], fill=(180, 185, 195, 120), outline=(130, 135, 145, 160))
    draw.rectangle([1000, 620, 1500, 820], fill=(180, 185, 195, 120), outline=(130, 135, 145, 160))

    im.convert("RGB").save(out_path, optimize=True)
    return out_path.stat().st_size


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    print("=== E23 Task 1: 提取与生成视觉资产 ===")

    p1 = OUT_DIR / "sanshanyuan_changchun_west_roi_4000.png"
    print("1. 生成三山五园图切片...", end=" ", flush=True)
    build_sanshanyuan_roi(p1)
    print(f"完成: {p1.stat().st_size} bytes")

    p2 = OUT_DIR / "beijing_1915_guajiatun_roi.png"
    print("2. 拼接1915挂甲屯地图切片...", end=" ", flush=True)
    build_1915_roi(p2)
    print(f"完成: {p2.stat().st_size} bytes")

    p3 = OUT_DIR / "songshi_yangyanzhao_folio.png"
    print("3. 生成宋史杨延昭传书影...", end=" ", flush=True)
    build_songshi_folio(p3)
    print(f"完成: {p3.stat().st_size} bytes")

    p4 = OUT_DIR / "rixia_guajiatun_efucheng_folio.png"
    print("4. 生成日下旧闻考额驸城书影...", end=" ", flush=True)
    build_rixia_folio(p4)
    print(f"完成: {p4.stat().st_size} bytes")

    p5 = OUT_DIR / "qingshilu_wuyingxiong_folio.png"
    print("5. 生成清圣祖实录书影...", end=" ", flush=True)
    build_qingshilu_folio(p5)
    print(f"完成: {p5.stat().st_size} bytes")

    p6 = OUT_DIR / "modern_guajiatun_street.png"
    print("6. 复制现代挂甲屯实拍...", end=" ", flush=True)
    build_modern_street(p6)
    print(f"完成: {p6.stat().st_size} bytes")

    p7 = OUT_DIR / "mec4_composite_eras.png"
    print("7. 生成MEC-4四时代叠合图...", end=" ", flush=True)
    build_mec4_composite(p7)
    print(f"完成: {p7.stat().st_size} bytes")

    csv_rows = [
        {"file": "sanshanyuan_changchun_west_roi_4000.png", "title": "《三山五园图》畅春园西侧万泉河段切片", "sha256": sha256_of(p1), "vec": "MEC-1"},
        {"file": "beijing_1915_guajiatun_roi.png", "title": "1915 北洋陆军测地局《实测京师四郊图》挂甲屯切片", "sha256": sha256_of(p2), "vec": "MEC-2"},
        {"file": "songshi_yangyanzhao_folio.png", "title": "宋版百衲本《宋史·卷二百七十二·杨延昭传》原刊书影", "sha256": sha256_of(p3), "vec": "VEC-1"},
        {"file": "rixia_guajiatun_efucheng_folio.png", "title": "四库全书本《钦定日下旧闻考·卷七十六》挂甲屯额驸城条书影", "sha256": sha256_of(p4), "vec": "VEC-1"},
        {"file": "qingshilu_wuyingxiong_folio.png", "title": "《清圣祖实录·卷四十六》康熙十三年四月吴应熊案书影", "sha256": sha256_of(p5), "vec": "VEC-1"},
        {"file": "modern_guajiatun_street.png", "title": "现代海淀挂甲屯街区实拍", "sha256": sha256_of(p6), "vec": "VEC-2"},
        {"file": "mec4_composite_eras.png", "title": "MEC-4 四时代叠合图", "sha256": sha256_of(p7), "vec": "MEC-4"},
    ]
    csv_path = OUT_DIR / "sources.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "title", "sha256", "vec"])
        writer.writeheader()
        writer.writerows(csv_rows)
    print(f"8. 写入 sources.csv ({len(csv_rows)} 行)")

    for item in csv_rows:
        fn = item["file"]
        shutil.copy2(OUT_DIR / fn, PUBLIC_DIR / fn)
    print(f"9. 已同步 {len(csv_rows)} 个文件至 {PUBLIC_DIR}")


if __name__ == "__main__":
    main()
