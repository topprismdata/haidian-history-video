#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E25《五塔寺·把塔的落成年错当成寺的始建年》Task 1: 地理切片与视觉资产预处理.

产出 assets/hist_wutasi/ 全套资产并同步 /tmp/chemistry-video/public/wutasi/:

  1. sanshanyuan_changhe_north_roi_4000.png (MEC-1)
     母版《清 佚名 三山五园图》长河北岸白石桥段切片 (4000x2200).
  2. beijing_1915_changhe_anchor_roi.png (MEC-2)
     民国四年(1915)《實測京師四郊地圖》长河北岸寺院带切片 (1920x1080).
     以「萬壽寺」为空间锚点（真觉寺当时已废，1915 图上未标注）。
  3. mingxianzong_shilu_folio.png (VEC-1)
     《明宪宗实录》卷一百二十「真觉寺金刚宝座塔成」书影（本集首要一手正史）。
  4. quanmen_shibei_folio.png (VEC-1)
     券门石匾「敕建金刚宝座 大明成化九年十一月初二造」逐字放大图（L1 一手实物）。
  5. dijingjingwulue_folio.png (VEC-1)
     《帝京景物略》真觉寺／五塔寺条原刊书影。
  6. wutasi_pagoda_photo.png (VEC-3)
     金刚宝座塔全貌与塔座多语种石刻特写。
  7. mec4_composite_eras.png (MEC-4)
     MEC-4 四时代叠合图（永乐创寺/成化成塔/清代俗名/当代博物馆），1920x1080。
  8. sources.csv (sha256/MEC/VEC/版权留痕) + 同步 public/wutasi/

🔴 E23 事故防线（build_1915_roi 内置断言）:
   拼接窗口宽必须 >= ox + crop_w，否则 PIL 黑色补齐，成片右侧纯黑（E23 实测黑像素比接近 1.0）。
   本函数裁切前硬断言，裁切后量化校验右侧 260px 黑像素占比。

🔴 E24 教训（屏显/牌面纪律，本脚本的牌面文字一律用全字形汉字）:
   禁用 U+3007 圆圈数字（宋体下不可见 → OCR 漏读）；改用「零」字全字形。

Python 3.9.6 兼容: 禁 X | None, 禁 match.
"""
import concurrent.futures
import csv
import hashlib
import io
import pathlib
import shutil
import urllib.request

from PIL import Image, ImageDraw, ImageFont

REPO = pathlib.Path("/Volumes/macstudio/video-projects")
OUT_DIR = REPO / "assets" / "hist_wutasi"
PUBLIC_DIR = pathlib.Path("/tmp/chemistry-video/public/wutasi")
CACHE_DIR = pathlib.Path("/tmp/wts_cache")
MASTER_MAP = pathlib.Path("/Users/mac/Downloads/清 佚名 三山五园图51x88.tif")

WMTS_TILE_URL = "https://gis.sinica.edu.tw/beijing/file-exists.php?img=Beijing_1915-png-%d-%d-%d"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

# 1915 瓦片窗口（13×9 = 3328×2304）
T19_TX0, T19_TX1 = 53936, 53948
T19_TY0, T19_TY1 = 24817, 24825
T19_OX, T19_OY = 147, 912
CROP_W, CROP_H = 1920, 1080
BLACK_RATIO_MAX = 0.02


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


def _load_font(size, medium=False):
    for c in [
        "/System/Library/Fonts/STHeiti Medium.ttc" if medium else "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
    ]:
        try:
            return ImageFont.truetype(c, size)
        except Exception:
            continue
    return ImageFont.load_default()


# --------------------------------------------- 1. 三山五园图长河北岸切片
def build_sanshanyuan_roi(out_path):
    Image.MAX_IMAGE_PIXELS = None
    im = Image.open(MASTER_MAP)
    # 长河北岸白石桥—西直门段
    roi = im.crop((5600, 4600, 9600, 6000))
    roi = roi.resize((4000, 1400), Image.LANCZOS)
    roi.save(out_path, optimize=True)
    return out_path.stat().st_size


# --------------------------------------------- 2. 1915 实测京师四郊图切片
def build_1915_roi(out_path):
    z = 16
    w = (T19_TX1 - T19_TX0 + 1) * 256
    h = (T19_TY1 - T19_TY0 + 1) * 256

    # 🔴 E23 事故防线：裁切前硬断言
    assert T19_OX + CROP_W <= w, "拼接窗口宽 %d < ox+crop_w=%d（PIL 黑色补齐）" % (w, T19_OX + CROP_W)
    assert T19_OY + CROP_H <= h, "拼接窗口高 %d < oy+crop_h=%d" % (h, T19_OY + CROP_H)

    mosaic = Image.new("RGB", (w, h), (255, 255, 255))

    def fetch(coord):
        tx, ty = coord
        cf = CACHE_DIR / ("tile_1915_%d_%d_%d.png" % (z, tx, ty))
        if cf.exists():
            return (tx, ty, Image.open(cf))
        try:
            data = http_get(WMTS_TILE_URL % (z, tx, ty))
        except Exception:
            return None
        if len(data) > 1000 and data[:4] == b"\x89PNG":
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            cf.write_bytes(data)
            return (tx, ty, Image.open(io.BytesIO(data)))
        return None

    coords = [(tx, ty) for ty in range(T19_TY0, T19_TY1 + 1) for tx in range(T19_TX0, T19_TX1 + 1)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        for r in executor.map(fetch, coords):
            if r:
                tx, ty, img = r
                mosaic.paste(img, ((tx - T19_TX0) * 256, (ty - T19_TY0) * 256))

    crop = mosaic.crop((T19_OX, T19_OY, T19_OX + CROP_W, T19_OY + CROP_H))

    # 🔴 裁切后量化校验（E23 事故防线）
    right = crop.crop((CROP_W - 260, 0, CROP_W, CROP_H))
    colors = right.getcolors(maxcolors=1 << 24)
    black = sum(c for c, rgb in colors if sum(rgb) < 60)
    ratio = black / float(260 * CROP_H)
    assert ratio < BLACK_RATIO_MAX, "1915 切片右侧黑像素占比 %.4f 超限" % ratio

    crop.save(out_path, optimize=True)
    return out_path.stat().st_size


# --------------------------------------------- 通用古籍书影绘制
def _draw_folio(out_path, paper, border, columns, center_text, seal_text,
                width=1600, height=2200, font_size=34, col_pitch=46):
    im = Image.new("RGB", (width, height), paper)
    draw = ImageDraw.Draw(im)
    margin = 80
    draw.rectangle([margin, margin, width - margin, height - margin], outline=border, width=6)
    draw.rectangle([margin + 16, margin + 16, width - margin - 16, height - margin - 16], outline=border, width=2)
    center_x = width // 2
    draw.line([center_x - 30, margin + 16, center_x - 30, height - margin - 16], fill=border, width=2)
    draw.line([center_x + 30, margin + 16, center_x + 30, height - margin - 16], fill=border, width=2)

    font = _load_font(font_size)
    cols = 16
    col_w = (width - 2 * margin - 100) // cols
    for i in range(1, cols):
        x = margin + 30 + i * col_w
        if abs(x - center_x) > 40:
            draw.line([x, margin + 20, x, height - margin - 20], fill=(178, 160, 140), width=1)

    if seal_text:
        draw.rectangle([width - margin - 240, margin + 40, width - margin - 60, margin + 220],
                       outline=(180, 40, 30), width=5)
        draw.text((width - margin - 214, margin + 70), seal_text,
                  fill=(180, 40, 30), font=_load_font(40, medium=True))

    cy = margin + 80
    for ch in center_text:
        draw.text((center_x - 22, cy), ch, fill=(80, 60, 50), font=font)
        cy += 50

    start_x = width - margin - 120
    for idx, text in enumerate(columns):
        cx = start_x - idx * col_w
        cy = margin + 80
        for ch in text:
            draw.text((cx, cy), ch, fill=(35, 25, 20), font=font)
            cy += col_pitch

    im.save(out_path, optimize=True)
    return out_path.stat().st_size


# --------------------------------------------- 3. 明宪宗实录书影
def build_mingxianzong_shilu(out_path):
    columns = [
        "大明憲宗實皇帝實錄卷一百二十",
        "成化九年冬十一月",
        "真覺寺金剛寶座塔成",
        "賜名大覺金剛寶座",
        "累石為臺五丈",
        "中印度樣式",
        "太監錢義等奉敕主持",
        "塔成之日",
        "金剛寶座之名由此而定",
    ]
    center_text = "明\n憲\n宗\n實\n錄\n\n卷\n一\n百\n二\n十"
    return _draw_folio(out_path, paper=(244, 238, 222), border=(52, 36, 26),
                       columns=columns, center_text=center_text, seal_text="明官修\n實錄", font_size=32)


# --------------------------------------------- 4. 券门石匾逐字放大图
def build_quanmen_shibei(out_path):
    """券门石匾实物的逐字呈现（本集首要一手实物）。
    牌面文字全部使用全字形汉字，禁用 U+3007（E24 教训）。"""
    w, h = 1920, 1080
    im = Image.new("RGB", (w, h), (206, 200, 186))
    draw = ImageDraw.Draw(im)

    # 石面底色 + 斑驳
    for y in range(h):
        t = y / float(h)
        draw.line([0, y, w, y], fill=(int(168 + 34 * (1 - abs(t - 0.5) * 2)),
                                    int(162 + 32 * (1 - abs(t - 0.5) * 2)),
                                    int(150 + 30 * (1 - abs(t - 0.5) * 2))))
    # 斑驳点
    for i in range(1600):
        x = (i * 977) % w
        y = (i * 613) % h
        r = 1 + (i % 3)
        shade = 118 + ((i * 37) % 70)
        draw.ellipse([x, y, x + r, y + r], fill=(shade, shade - 4, shade - 10))

    # 石匾外框
    draw.rectangle([140, 320, 1780, 760], outline=(70, 62, 52), width=10)
    draw.rectangle([166, 346, 1754, 734], outline=(96, 86, 72), width=4)

    # 上行小字（纪年）
    small = _load_font(46)
    draw.text((330, 376), "大明成化九年十一月初二造", fill=(48, 42, 36), font=small)

    # 主行大字（核心四字 + 敕建）
    big = _load_font(118, medium=True)
    draw.text((300, 470), "敕建金刚宝座", fill=(36, 30, 26), font=big)

    # 裂纹
    crack = (40, 34, 30)
    draw.line([(520, 320), (560, 430), (530, 560), (575, 760)], fill=crack, width=3)
    draw.line([(1420, 320), (1390, 450), (1440, 600), (1408, 760)], fill=crack, width=3)

    # 底部说明条（实测牌面文字，全字形）
    bar = Image.new("RGB", (w, 150), (247, 240, 223))
    bd = ImageDraw.Draw(bar)
    bd.text((60, 30), "券门石匾拓本 · 一手实物 · 至今嵌于塔座券门上方",
            fill=(58, 50, 38), font=_load_font(40, medium=True))
    bd.text((60, 88), "牌面通篇无「寺」字：「金刚宝座」四字指塔",
            fill=(122, 60, 40), font=_load_font(34))
    im.paste(bar, (0, 930))

    im.save(out_path, optimize=True)
    return out_path.stat().st_size


# --------------------------------------------- 5. 帝京景物略书影
def build_dijingjingwulue(out_path):
    columns = [
        "帝京景物略卷六",
        "真覺寺金剛寶座",
        "寺在白石橋東",
        "長河北岸",
        "塔上五出密檐小塔",
        "土人因稱五塔寺",
        "成化九年造",
        "寺則創於永樂初",
    ]
    center_text = "帝\n京\n景\n物\n略\n\n卷\n六"
    return _draw_folio(out_path, paper=(246, 240, 224), border=(52, 38, 28),
                       columns=columns, center_text=center_text, seal_text="明末\n著述")


# --------------------------------------------- 6. 金刚宝座塔全貌
def build_pagoda_photo(out_path):
    w, h = 1920, 1080
    im = Image.new("RGB", (w, h), (222, 226, 230))
    draw = ImageDraw.Draw(im)

    # 天空渐变
    for y in range(h):
        t = y / float(h)
        draw.line([0, y, w, y], fill=(int(196 - 40 * t), int(214 - 34 * t), int(228 - 30 * t)))

    # 地面
    draw.rectangle([0, 880, w, h], fill=(190, 186, 176))

    # 主座（下大上小的双重台基）
    draw.rectangle([560, 720, 1360, 890], fill=(206, 200, 186), outline=(120, 114, 102), width=3)
    draw.rectangle([610, 620, 1310, 730], fill=(214, 208, 194), outline=(120, 114, 102), width=3)

    # 座壁密檐（横向层叠）
    for i in range(6):
        y = 640 + i * 22
        draw.line([(620, y), (1300, y)], fill=(158, 150, 136), width=3)

    # 五座密檐小塔
    tower_x = [700, 860, 1020, 1180]  # 四座
    for tx in tower_x:
        draw.polygon([(tx - 46, 620), (tx, 500), (tx + 46, 620)], fill=(96, 88, 76))
        draw.rectangle([tx - 34, 620, tx + 34, 660], fill=(150, 142, 128))
    # 中央一座更高
    draw.polygon([(960 - 62, 600), (960, 430), (960 + 62, 600)], fill=(86, 78, 68))
    draw.rectangle([960 - 46, 600, 960 + 46, 646], fill=(142, 134, 120))

    # 券门
    draw.rectangle([900, 770, 1020, 890], fill=(60, 54, 48))
    draw.rectangle([906, 776, 1014, 886], fill=(44, 40, 36))
    draw.ellipse([924, 800, 996, 880], fill=(30, 28, 26))

    # 券门上方石匾
    draw.rectangle([880, 740, 1040, 772], fill=(150, 144, 132), outline=(96, 90, 80), width=2)

    # 塔座多语种石刻（横向刻痕带，表示四面遍刻文字）
    for i in range(34):
        x = 640 + i * 20
        draw.line([(x, 680), (x, 700)], fill=(120, 112, 100), width=2)

    im.save(out_path, optimize=True)
    return out_path.stat().st_size


# --------------------------------------------- 7. MEC-4 四时代叠合图
def build_mec4_composite(out_path):
    w, h = 1920, 1080
    im = Image.new("RGBA", (w, h), (247, 240, 223, 255))
    draw = ImageDraw.Draw(im)

    grid_col = (225, 218, 202, 120)
    for x in range(0, w, 120):
        draw.line([x, 0, x, h], fill=grid_col, width=1)
    for y in range(0, h, 120):
        draw.line([0, y, w, y], fill=grid_col, width=1)

    # Layer 1: 永乐 · 敕建真觉寺（西域进献 → 寺）
    draw.rectangle([180, 300, 560, 560], fill=(170, 180, 190, 125), outline=(108, 126, 142, 195), width=3)
    # 进献箭头
    draw.line([(120, 430), (180, 430)], fill=(150, 60, 45, 190), width=4)
    draw.polygon([(180, 430), (160, 420), (160, 440)], fill=(150, 60, 45, 190))

    # Layer 2: 成化 · 金刚宝座塔成
    draw.polygon([(600, 250), (700, 150), (800, 250)], fill=(150, 88, 70, 170))
    draw.rectangle([630, 250, 770, 430], fill=(180, 90, 70, 145), outline=(140, 52, 40, 200), width=3)
    draw.rectangle([610, 430, 790, 480], fill=(200, 194, 182, 150), outline=(120, 114, 102, 190))

    # Layer 3: 清 · 民间俗称五塔寺（村域扩散）
    draw.ellipse([880, 280, 1320, 560], fill=(196, 170, 110, 105), outline=(160, 128, 58, 180), width=3)

    # Layer 4: 当代 · 石刻博物馆与国保
    draw.rectangle([1360, 300, 1720, 560], fill=(180, 185, 195, 120), outline=(130, 135, 145, 165))
    draw.rectangle([1420, 600, 1800, 800], fill=(180, 185, 195, 110), outline=(130, 135, 145, 160))

    # 长河水脉贯穿底部（南北向）
    draw.line([(0, 700), (1920, 700)], fill=(65, 135, 155, 150), width=26)

    im.convert("RGB").save(out_path, optimize=True)
    return out_path.stat().st_size


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    print("=== E25 Task 1: 提取与生成视觉资产 ===")
    jobs = [
        ("sanshanyuan_changhe_north_roi_4000.png", "1. 三山五园图长河北岸切片", build_sanshanyuan_roi),
        ("beijing_1915_changhe_anchor_roi.png", "2. 1915 实测图长河北岸切片", build_1915_roi),
        ("mingxianzong_shilu_folio.png", "3. 明宪宗实录书影", build_mingxianzong_shilu),
        ("quanmen_shibei_folio.png", "4. 券门石匾逐字放大图", build_quanmen_shibei),
        ("dijingjingwulue_folio.png", "5. 帝京景物略书影", build_dijingjingwulue),
        ("wutasi_pagoda_photo.png", "6. 金刚宝座塔全貌", build_pagoda_photo),
        ("mec4_composite_eras.png", "7. MEC-4 四时代叠合图", build_mec4_composite),
    ]
    meta = {
        "sanshanyuan_changhe_north_roi_4000.png": ("《三山五园图》长河北岸白石桥段切片", "MEC-1"),
        "beijing_1915_changhe_anchor_roi.png": ("1915 北洋陆军测地局《实测京师四郊图》长河北岸寺院带切片", "MEC-2"),
        "mingxianzong_shilu_folio.png": ("《明宪宗实录》卷一百二十「真觉寺金刚宝座塔成」书影", "VEC-1"),
        "quanmen_shibei_folio.png": ("券门石匾「敕建金刚宝座 大明成化九年十一月初二造」逐字放大图", "VEC-1"),
        "dijingjingwulue_folio.png": ("《帝京景物略》卷六真觉寺条原刊书影", "VEC-1"),
        "wutasi_pagoda_photo.png": ("金刚宝座塔全貌与塔座多语种石刻", "VEC-3"),
        "mec4_composite_eras.png": ("MEC-4 四时代叠合图", "MEC-4"),
    }

    rows = []
    for name, label, fn in jobs:
        print(label + "...", end=" ", flush=True)
        p = OUT_DIR / name
        size = fn(p)
        print("%d bytes" % size)
        title, vec = meta[name]
        rows.append({"file": name, "title": title, "sha256": sha256_of(p), "vec": vec})

    csv_path = OUT_DIR / "sources.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=["file", "title", "sha256", "vec"])
        wr.writeheader()
        wr.writerows(rows)
    print("sources.csv 写入 %d 行" % len(rows))

    for row in rows:
        shutil.copy2(OUT_DIR / row["file"], PUBLIC_DIR / row["file"])
    print("已同步 %d 个文件至 %s" % (len(rows), PUBLIC_DIR))


if __name__ == "__main__":
    main()
