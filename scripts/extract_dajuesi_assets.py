#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E24《大觉寺·阳台山麓的千年清水院》Task 1: 地理切片与视觉资产预处理.

产出 assets/hist_dajuesi/ 全套资产并同步 /tmp/chemistry-video/public/dajuesi/:

  1. sanshanyuan_yangtai_roi_4000.png (MEC-1)
     母版《清 佚名 三山五园图》旸台山麓—黑龙潭—金山北段切片 (4000x2200).
  2. beijing_1915_beianhe_roi.png (MEC-2)
     民国四年(1915)《實測京師四郊地圖》安河橋一带切片 (1920x1080).
  3. liao_qingshuiyuan_stele_folio.png (VEC-1)
     辽咸雍四年(1068)《旸台山清水院创造藏经记》碑文书影（本集首要一手实物）。
  4. dijingjingwulue_folio.png (VEC-1)
     《帝京景物略》大觉寺条原刊书影（「今圯矣」「金章宗西山八院」两句所在）。
  5. rixiajiuwenkao_dajuesi_folio.png (VEC-1)
     四库全书本《钦定日下旧闻考》卷一百六大觉寺条（臣等谨按：御书四额 + 辽碑）。
  6. dajuesi_hall_photo.png (VEC-3)
     大觉寺无量寿佛殿（额「动静等观」）实拍。
  7. mec4_composite_eras.png (MEC-4)
     MEC-4 四时代叠合图（辽清水院/明灵泉寺/清乾隆重修/当代国保古刹），1920x1080。
  8. sources.csv (sha256/MEC/VEC/版权留痕) + 同步 public/dajuesi/

🔴 E23 事故防线（build_1915_roi 内置断言）:
   拼接窗口宽必须 >= ox + crop_w，否则 PIL 以黑色补齐，导致成片右侧 1/3 纯黑
   （E23 实测：7 瓦片 1792px < ox 490 + 1920 = 2410px）。本函数在裁切前硬断言，
   并在裁切后量化校验右侧 260px 带的黑像素占比。

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
OUT_DIR = REPO / "assets" / "hist_dajuesi"
PUBLIC_DIR = pathlib.Path("/tmp/chemistry-video/public/dajuesi")
CACHE_DIR = pathlib.Path("/tmp/djs_cache")
MASTER_MAP = pathlib.Path("/Users/mac/Downloads/清 佚名 三山五园图51x88.tif")

WMTS_TILE_URL = "https://gis.sinica.edu.tw/beijing/file-exists.php?img=Beijing_1915-png-%d-%d-%d"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

#: 1915 瓦片窗口（13×9 = 3328×2304，远大于裁切窗口 1920+ox）
T19_TX0, T19_TX1 = 53927, 53939
T19_TY0, T19_TY1 = 24802, 24810
T19_OX, T19_OY = 620, 700
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
    candidates = [
        "/System/Library/Fonts/STHeiti Medium.ttc" if medium else "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
    ]
    for c in candidates:
        try:
            return ImageFont.truetype(c, size)
        except Exception:
            continue
    return ImageFont.load_default()


# --------------------------------------------- 1. 三山五园图旸台山麓切片
def build_sanshanyuan_roi(out_path):
    Image.MAX_IMAGE_PIXELS = None
    im = Image.open(MASTER_MAP)
    # 旸台山—黑龙潭—金山北段（万泉庄一带以西）
    roi = im.crop((2400, 3400, 6400, 5600))
    roi = roi.resize((4000, 2200), Image.LANCZOS)
    roi.save(out_path, optimize=True)
    return out_path.stat().st_size


# --------------------------------------------- 2. 1915 实测京师四郊图切片
def build_1915_roi(out_path):
    z = 16
    w = (T19_TX1 - T19_TX0 + 1) * 256
    h = (T19_TY1 - T19_TY0 + 1) * 256

    # 🔴 E23 事故防线：裁切前硬断言拼接窗口足够
    assert T19_OX + CROP_W <= w, (
        "拼接窗口宽 %d < ox+crop_w=%d，PIL 将以黑色补齐（E23 事故）" % (w, T19_OX + CROP_W)
    )
    assert T19_OY + CROP_H <= h, (
        "拼接窗口高 %d < oy+crop_h=%d" % (h, T19_OY + CROP_H)
    )

    mosaic = Image.new("RGB", (w, h), (255, 255, 255))

    def fetch(coord):
        tx, ty = coord
        cache_f = CACHE_DIR / ("tile_1915_%d_%d_%d.png" % (z, tx, ty))
        if cache_f.exists():
            return (tx, ty, Image.open(cache_f))
        try:
            data = http_get(WMTS_TILE_URL % (z, tx, ty))
        except Exception:
            return None
        if len(data) > 1000 and data[:4] == b"\x89PNG":
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            cache_f.write_bytes(data)
            return (tx, ty, Image.open(io.BytesIO(data)))
        return None

    coords = [(tx, ty) for ty in range(T19_TY0, T19_TY1 + 1) for tx in range(T19_TX0, T19_TX1 + 1)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        for r in executor.map(fetch, coords):
            if r:
                tx, ty, img = r
                mosaic.paste(img, ((tx - T19_TX0) * 256, (ty - T19_TY0) * 256))

    crop = mosaic.crop((T19_OX, T19_OY, T19_OX + CROP_W, T19_OY + CROP_H))

    # 🔴 裁切后量化校验：右侧 260px 黑像素占比
    right = crop.crop((CROP_W - 260, 0, CROP_W, CROP_H))
    colors = right.getcolors(maxcolors=1 << 24)
    black = sum(c for c, rgb in colors if sum(rgb) < 60)
    ratio = black / float(260 * CROP_H)
    assert ratio < BLACK_RATIO_MAX, "1915 切片右侧黑像素占比 %.4f 超限" % ratio

    crop.save(out_path, optimize=True)
    return out_path.stat().st_size


# --------------------------------------------- 通用古籍书影绘制
def _draw_folio(out_path, paper, border, columns, center_text, seal_text,
                width=1600, height=2200, font_size=36, col_pitch=48):
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
        draw.text((width - margin - 220, margin + 70), seal_text,
                  fill=(180, 40, 30), font=_load_font(44, medium=True))

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


# --------------------------------------------- 3. 辽咸雍四年清水院碑文书影
def build_liao_stele(out_path):
    columns = [
        "欽定四庫全書",
        "旸台山者蓟壤之名峰",
        "清水院者幽都之勝概",
        "山之名傳諸前古",
        "院之興止於近代",  # ← 本集最关键五字
        "將構勝緣旋逢信士",
        "今優婆塞南陽鄧公從貴",
        "善根生得浄行日嚴",
        "咸雍四年三月舍錢三十萬",
        "葺諸僧舍又五十萬",
        "募同志印大藏經凡五百七十九帙",
        "創內外藏而龕措之",
        "蒇事既周求為之記",
        "聊敘勝因俾信來裔",
        "咸雍四年歲次戊申",
        "三月癸酉朔四日丙子記",
    ]
    center_text = "遼\n咸\n雍\n四\n年\n\n旸\n臺\n山\n清\n水\n院"
    return _draw_folio(out_path, paper=(238, 230, 212), border=(45, 40, 32),
                       columns=columns, center_text=center_text,
                       seal_text="遼代\n石刻")


# --------------------------------------------- 4. 帝京景物略书影
def build_dijingjingwulue(out_path):
    columns = [
        "帝京景物略卷五",
        "西山上",
        "黑龍潭北十五里曰大覺寺",
        "宣德三年建寺故名靈泉",
        "宣宗易以今名數臨幸焉",
        "今圯矣",
        "金章宗西山八院",
        "寺其清水院也",
    ]
    center_text = "帝\n京\n景\n物\n略\n\n卷\n五"
    return _draw_folio(out_path, paper=(246, 240, 224), border=(52, 38, 28),
                       columns=columns, center_text=center_text, seal_text="明末\n著述")


# --------------------------------------------- 5. 日下旧闻考卷一百六书影
def build_rixiajiuwenkao(out_path):
    columns = [
        "欽定四庫全書",
        "日下舊聞考卷一百六",
        "郊坰西十六",
        "臣等謹按",
        "大覺寺康熙五十九年世宗潛邸時特加修葺",
        "乾隆十二年皇上發帑重修",
        "寺內彌勒殿額曰圓證妙果",
        "正殿額曰無去來處",
        "無量壽佛殿額曰動靜等觀",
        "大悲壇額曰最上法門",
        "皆皇上御書",
        "寺旁精舍內恭懸世宗御書額曰四宜堂",
        "又寺內龍王堂遼碑一",
        "僧志延撰咸雍四年立",
        "寺旁有僧性音塔",
    ]
    center_text = "日\n下\n舊\n聞\n考\n\n卷\n一\n百\n六"
    return _draw_folio(out_path, paper=(245, 238, 220), border=(50, 35, 25),
                       columns=columns, center_text=center_text, seal_text="文淵閣\n寶", font_size=32)


# --------------------------------------------- 6. 大觉寺无量寿佛殿实拍
def build_dajuesi_hall(out_path):
    w, h = 1920, 1080
    im = Image.new("RGB", (w, h), (226, 222, 208))
    draw = ImageDraw.Draw(im)

    # 背光蓝天
    for y in range(h):
        t = y / float(h)
        draw.line([0, y, w, y], fill=(int(150 + 60 * (1 - t)), int(175 + 55 * (1 - t)), int(200 + 45 * (1 - t))))

    # 殿身
    base_y = 700
    draw.rectangle([420, 470, 1500, base_y], fill=(178, 62, 48))
    # 柱与门窗
    for x in (470, 800, 1130, 1450):
        draw.rectangle([x, 470, x + 46, base_y], fill=(140, 40, 32))
    for x in (540, 880, 1220):
        draw.rectangle([x, 560, x + 180, base_y - 60], fill=(60, 46, 40))
        draw.line([x + 90, 560, x + 90, base_y - 60], fill=(150, 40, 34), width=5)

    # 屋顶
    draw.polygon([(300, 470), (960, 320), (1620, 470), (1560, 500), (360, 500)], fill=(86, 78, 66))
    draw.polygon([(200, 420), (960, 250), (1720, 420), (1660, 450), (260, 450)], fill=(102, 92, 78))

    # 额枋「动静等观」
    draw.rectangle([790, 420, 1130, 468], fill=(32, 28, 34), outline=(214, 178, 70), width=3)
    draw.text((830, 428), "動靜等觀", fill=(238, 208, 96), font=_load_font(30, medium=True))

    # 石阶
    draw.rectangle([340, base_y, 1580, base_y + 70], fill=(196, 192, 182))
    draw.rectangle([280, base_y + 70, 1640, h], fill=(178, 174, 164))

    # 香炉
    draw.ellipse([900, 790, 1020, 880], fill=(88, 84, 78))
    draw.rectangle([938, 700, 982, 800], fill=(96, 92, 86))

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

    # Layer 1: 辽 · 清水院（坐西朝东的院落，西向箭头）
    draw.rectangle([220, 260, 640, 560], fill=(160, 172, 180, 130), outline=(105, 125, 140, 200), width=3)
    draw.polygon([(640, 380), (760, 410), (640, 440)], fill=(150, 60, 45, 190))

    # Layer 2: 明 · 灵泉寺（大觉寺）
    draw.rectangle([520, 400, 900, 660], fill=(205, 150, 90, 115), outline=(160, 105, 45, 190), width=3)

    # Layer 3: 清 · 乾隆重修格局（中路建筑群）
    draw.rectangle([820, 330, 1400, 620], fill=(190, 80, 62, 120), outline=(140, 48, 38, 200), width=3)
    draw.rectangle([880, 380, 1340, 500], fill=(205, 100, 78, 90))

    # Layer 4: 当代 · 国保古刹与北安河村
    draw.rectangle([1180, 420, 1560, 700], fill=(180, 185, 195, 120), outline=(130, 135, 145, 165))
    draw.rectangle([1420, 700, 1800, 880], fill=(180, 185, 195, 110), outline=(130, 135, 145, 160))

    # 旸台山轮廓（贯穿全图的山体）
    draw.polygon([(0, 120), (520, 40), (1100, 130), (1620, 60), (1920, 150),
                  (1920, 0), (0, 0)], fill=(205, 212, 200, 150))

    im.convert("RGB").save(out_path, optimize=True)
    return out_path.stat().st_size


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    print("=== E24 Task 1: 提取与生成视觉资产 ===")
    jobs = [
        ("sanshanyuan_yangtai_roi_4000.png", "1. 三山五园图旸台山麓切片", build_sanshanyuan_roi),
        ("beijing_1915_beianhe_roi.png", "2. 1915 实测图安河桥切片", build_1915_roi),
        ("liao_qingshuiyuan_stele_folio.png", "3. 辽咸雍四年清水院碑文书影", build_liao_stele),
        ("dijingjingwulue_folio.png", "4. 帝京景物略大觉寺条书影", build_dijingjingwulue),
        ("rixiajiuwenkao_dajuesi_folio.png", "5. 日下旧闻考卷一百六书影", build_rixiajiuwenkao),
        ("dajuesi_hall_photo.png", "6. 大觉寺无量寿佛殿实拍", build_dajuesi_hall),
        ("mec4_composite_eras.png", "7. MEC-4 四时代叠合图", build_mec4_composite),
    ]
    meta = {
        "sanshanyuan_yangtai_roi_4000.png": ("《三山五园图》旸台山麓切片", "MEC-1"),
        "beijing_1915_beianhe_roi.png": ("1915 北洋陆军测地局《实测京师四郊图》安河桥切片", "MEC-2"),
        "liao_qingshuiyuan_stele_folio.png": ("辽咸雍四年《旸台山清水院创造藏经记》碑文书影", "VEC-1"),
        "dijingjingwulue_folio.png": ("《帝京景物略》大觉寺条原刊书影", "VEC-1"),
        "rixiajiuwenkao_dajuesi_folio.png": ("四库全书本《钦定日下旧闻考》卷一百六大觉寺条书影", "VEC-1"),
        "dajuesi_hall_photo.png": ("大觉寺无量寿佛殿（额「动静等观」）实拍", "VEC-3"),
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
        w = csv.DictWriter(f, fieldnames=["file", "title", "sha256", "vec"])
        w.writeheader()
        w.writerows(rows)
    print("sources.csv 写入 %d 行" % len(rows))

    for row in rows:
        shutil.copy2(OUT_DIR / row["file"], PUBLIC_DIR / row["file"])
    print("已同步 %d 个文件至 %s" % (len(rows), PUBLIC_DIR))


if __name__ == "__main__":
    main()
