#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E27《白家疃·疃字里的京西村落》视觉资产脚本（模式照抄 E25/E26）.

产出 assets/hist_baijiatuan/ 全套资产并同步 /tmp/chemistry-video/public/baijiatuan/:

  1. mec1_sanshanyuan_ridge_roi_4000.png (MEC-1)
     母版《清 佚名 三山五园图》香山山脊带切片 (4000x1400)。
     注记：白家疃村经逐区目视核验不在本图幅（母版西北角为空白绢底），
     本切片为村南隔山相望的西山主脉，供「山北村落」叙事使用。
  2. beijing_1915_baijiatuan_roi.png (MEC-2)
     民国四年(1915)《實測京師四郊地圖》白家疃村—楊家村—黑龍潭段切片 (1920x1080)。
     村名标注「白」+疃/灘族复杂字形（「家」字未得确认，勿写死「白家灘」三字）。
     窗口经图面标注目视核验（白家疃/楊家村/黑龍潭/縣界红线均已在切片内）。
     🔴 E23 事故防线保留：拼接窗口硬断言 + 裁切后右侧黑像素量化校验。
  3. shuowen_tuan_folio.png (VEC-1)
     《說文解字·田部》「疃，禽獸所踐處也。從田童聲。」书影示意。
  4. shijing_dongshan_folio.png (VEC-1)
     《詩經·豳風·東山》「町疃鹿場」（毛傳：町疃，鹿跡也）书影示意。
  5. xianwangci_beiji_tuoying.png (VEC-1)
     《敕賜白家疃賢王祠祭田碑記》碑记拓影示意。额题据公开文献著录；
     碑文全文未考得，碑面不排任何正文（防伪红线）。
  6. xianwangci_shanmen_biane.png (VEC-1)
     賢王祠山门拱券门额「賢王祠」拓影示意（据公开著录，非实物扫描）。
  7. xianwangci_gaiju_plan.png (VEC-3)
     怡贤亲王祠建筑格局示意（坐南朝北：戏台—山门—前殿—正殿+东西耳房）。
     制作组绘制，非实物照片，非实测图。
  8. caoxueqin_trail_topology.png (MEC-3)
     曹雪芹小道拓扑：黄叶村—卧佛寺—樱桃沟—三炷香—白家疃。
     民间传说与今人命名路线，制作组示意，非测绘拓扑。
  9. tuan_ziyi_card.png (VEC-4)
     「疃」字释义卡：本义（禽兽所践处）→《诗》证→引申（村庄，北方地名）
     →白家灘→白家疃。制作组示意。
 10. mec4_era_overlay.png (MEC-4)
     五段时代叠合：旧名白家滩（相传）/雍正三年治水设别墅(1725)/
     雍正十年敕建贤王祠(1732)/民国四年实测图作白家滩(1915)/今温泉镇白家疃村。
 11. sources.csv（sha256/MEC/VEC/版权留痕）+ 同步 public/baijiatuan/

🔴 E23 事故防线（build_1915_baijiatuan_roi 内置断言）:
   拼接窗口宽/高必须 >= ox/oy + crop，否则 PIL 黑色补齐。
   裁切后量化校验右侧 260px 黑像素占比。
   另加：瓦片抓取覆盖率必须 100%（防白缝静默通过）。

🔴 E24/E25 教训：牌面文字一律全字形汉字，禁 U+3007 圆圈数字，
   图面公历纪年一律汉字数字；关键大字做落墨(in Ink)断言防字形缺失。

考据依据（全部来自 web_search 实证，未考得处已在图面/notes 标明）:
   - 白家疃今属海淀区温泉镇，东邻杨家庄、西邻温泉村、北邻于家庄、南接西山。
   - 雍正三年(1725)怡亲王允祥奉旨整修京西水利，指挥部与别墅设白家疃；
     雍正八年(1730)允祥逝，雍正十年(1732)别墅改建敕建贤王祠
     （怡贤亲王祠，今白家疃小学院内，海淀区文物保护单位，坐南朝北，
     山门拱券门额书「贤王祠」，正北有大戏台）。
   - 院内曾存《敕赐白家疃贤王祠祭田碑记》（碑文全文未考得）。
   - 曹雪芹小道：黄叶村（正白旗纪念馆）—卧佛寺—樱桃沟—三炷香—白家疃，
     民间传说/今人命名路线。
   - 「疃」：《说文》禽兽所践处；土短切；《诗·豳风·东山》町疃鹿场；
     引申村庄义多用于北方地名（陆游《入蜀记》村疃数家）。
   - 1915 实测图该村标注为「白家灘」，今作「白家疃」。

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
OUT_DIR = REPO / "assets" / "hist_baijiatuan"
PUBLIC_DIR = pathlib.Path("/tmp/chemistry-video/public/baijiatuan")
CACHE_DIR = pathlib.Path("/tmp/bjt_cache")
MASTER_MAP = pathlib.Path("/Users/mac/Downloads/清 佚名 三山五园图51x88.tif")

WMTS_TILE_URL = "https://gis.sinica.edu.tw/beijing/file-exists.php?img=Beijing_1915-png-%d-%d-%d"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

# 1915 瓦片窗口（白家疃—楊家村—黑龍潭带）
# 标准 XYZ 网格换算: 白家疃村 ≈ tile (53919, 24798.7)；经图面标注目视核验。
T19_TX0, T19_TX1 = 53912, 53926
T19_TY0, T19_TY1 = 24792, 24802
T19_OX, T19_OY = 100, 70
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


def _assert_ink(im, box, thresh=120, min_dark=30, tag=""):
    """落墨断言：框内必须有足够深色像素，防字形缺失/空牌（E24 教训）。"""
    region = im.crop(box).convert("L")
    dark = sum(1 for p in region.getdata() if p < thresh)
    assert dark >= min_dark, "落墨断言失败 %s: dark=%d < %d" % (tag, dark, min_dark)


# --------------------------------------------- 1. 三山五园图香山山脊带切片
def build_mec1_ridge_roi(out_path):
    Image.MAX_IMAGE_PIXELS = None
    im = Image.open(MASTER_MAP)
    roi = im.crop((900, 130, 4900, 1530))
    roi = roi.resize((4000, 1400), Image.LANCZOS)
    roi.save(out_path, optimize=True)
    return out_path.stat().st_size


# --------------------------------------------- 2. 1915 实测京师四郊图白家疃切片
def build_1915_baijiatuan_roi(out_path):
    z = 16
    w = (T19_TX1 - T19_TX0 + 1) * 256
    h = (T19_TY1 - T19_TY0 + 1) * 256

    # 🔴 E23 事故防线：裁切前硬断言
    assert T19_OX + CROP_W <= w, "拼接窗口宽 %d < ox+crop_w=%d（PIL 黑色补齐）" % (w, T19_OX + CROP_W)
    assert T19_OY + CROP_H <= h, "拼接窗口高 %d < oy+crop_h=%d" % (h, T19_OY + CROP_H)

    mosaic = Image.new("RGB", (w, h), (255, 255, 255))

    def fetch(coord):
        tx, ty = coord
        cf = CACHE_DIR / ("t_%d_%d.png" % (tx, ty))
        if cf.exists():
            return (tx, ty, Image.open(cf))
        try:
            data = http_get(WMTS_TILE_URL % (z, tx, ty))
            img = Image.open(io.BytesIO(data)).convert("RGB") if data else None
            if img is None:
                return None
            img.save(cf)
        except Exception:
            return None
        return (tx, ty, img)

    coords = [(tx, ty) for ty in range(T19_TY0, T19_TY1 + 1) for tx in range(T19_TX0, T19_TX1 + 1)]
    fetched = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        for r in executor.map(fetch, coords):
            if r:
                tx, ty, img = r
                mosaic.paste(img, ((tx - T19_TX0) * 256, (ty - T19_TY0) * 256))
                fetched.add((tx, ty))

    # 🔴 覆盖率防线：缺瓦片 = 白缝静默通过，必须硬失败
    missing = [c for c in coords if c not in fetched]
    assert not missing, "1915 瓦片缺失 %d 片: %s" % (len(missing), missing[:8])

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


# --------------------------------------------- 3. 说文·田部 疃字书影
def build_shuowen_folio(out_path):
    columns = [
        "說文解字",
        "卷十三",
        "田部",
        "疃",
        "禽獸所踐處也",
        "從田童聲",
        "土短切",
    ]
    center_text = "說\n文\n解\n字"
    _draw_folio(out_path, paper=(243, 237, 221), border=(54, 38, 26),
                columns=columns, center_text=center_text, seal_text="說\n文")
    im = Image.open(out_path)
    _assert_ink(im, (900, 150, 1460, 800), min_dark=150, tag="shuowen 疃")
    return out_path.stat().st_size


# --------------------------------------------- 4. 诗经·东山 町疃鹿场书影
def build_shijing_folio(out_path):
    columns = [
        "詩經",
        "豳風",
        "東山",
        "町疃鹿場",
        "毛傳",
        "町疃鹿跡也",
    ]
    center_text = "詩\n經"
    _draw_folio(out_path, paper=(243, 237, 221), border=(54, 38, 26),
                columns=columns, center_text=center_text, seal_text="毛\n詩")
    im = Image.open(out_path)
    _assert_ink(im, (900, 150, 1460, 800), min_dark=150, tag="shijing")
    return out_path.stat().st_size


# --------------------------------------------- 5. 贤王祠祭田碑 碑记拓影（仅额题）
def build_xianwangci_beiji(out_path):
    w, h = 1400, 1900
    im = Image.new("RGB", (w, h), (58, 52, 46))
    draw = ImageDraw.Draw(im)

    # 碑面（浅色拓片）
    draw.rectangle([90, 90, w - 90, h - 90], fill=(228, 222, 206))
    draw.rectangle([130, 130, w - 130, h - 130], outline=(120, 110, 96), width=4)

    # 碑额带（装饰，不排未考得的文字）
    draw.rectangle([90, 90, w - 90, 190], fill=(196, 186, 168), outline=(120, 110, 96), width=3)
    for dx in (180, 260, 340):
        draw.arc([w // 2 - dx, 110, w // 2 + dx, 190], 200, 340, fill=(150, 138, 120), width=3)

    big = _load_font(82, medium=True)
    title = "敕賜白家疃賢王祠祭田碑記"
    cy = 260
    for ch in title:
        draw.text((w // 2 - 46, cy), ch, fill=(38, 32, 26), font=big)
        cy += 100

    # 碑面下方留白（碑文全文未考得，不排任何正文）
    small = _load_font(34)
    draw.text((150, h - 320), "（碑文全文未考得，此處不錄）",
              fill=(150, 138, 120), font=small)
    draw.text((150, h - 260), "（殘碑四通之一，額題據區保名錄著錄）",
              fill=(150, 138, 120), font=_load_font(28))

    # 底部说明条
    bar = Image.new("RGB", (w, 150), (247, 240, 223))
    bd = ImageDraw.Draw(bar)
    bd.text((60, 22), "《敕赐白家疃贤王祠祭田碑记》拓影示意",
            fill=(58, 50, 38), font=_load_font(40, medium=True))
    bd.text((60, 84), "额题据公开文献著录 · 制作组绘制，非原石拓片",
            fill=(122, 60, 40), font=_load_font(32))
    im.paste(bar, (0, h - 150))

    im.save(out_path, optimize=True)
    _assert_ink(im, (w // 2 - 60, 300, w // 2 + 60, 420), tag="beibi title")
    return out_path.stat().st_size


# --------------------------------------------- 6. 贤王祠山门门额拓影
def build_shanmen_biane(out_path):
    w, h = 1920, 1080
    im = Image.new("RGB", (w, h), (150, 146, 138))
    draw = ImageDraw.Draw(im)

    # 灰砖墙底（横缝）
    for y in range(h):
        t = y / float(h)
        draw.line([0, y, w, y], fill=(int(148 + 14 * (1 - t)), int(144 + 14 * (1 - t)), int(136 + 12 * (1 - t))))
    for by in range(120, 900, 60):
        draw.line([(0, by), (w, by)], fill=(126, 122, 114), width=2)
        for bx in range((by // 60 % 2) * 120, w, 240):
            draw.line([(bx, by), (bx, by + 60)], fill=(126, 122, 114), width=2)

    # 拱券门洞（石券）
    ax0, ay0, ax1, ay1 = 660, 300, 1260, 900
    draw.rectangle([ax0, 520, ax1, ay1], fill=(74, 68, 60))
    draw.pieslice([ax0, 340, ax1, 700], 180, 360, fill=(74, 68, 60))
    draw.arc([ax0, 340, ax1, 700], 180, 360, fill=(96, 88, 76), width=14)
    draw.rectangle([ax0, 520, ax1, ay1], outline=(96, 88, 76), width=14)
    # 券内暗部
    draw.rectangle([ax0 + 30, 540, ax1 - 30, ay1], fill=(40, 36, 32))
    draw.pieslice([ax0 + 30, 360, ax1 - 30, 680], 180, 360, fill=(40, 36, 32))

    # 门额石匾（拱肩处）
    draw.rectangle([810, 380, 1110, 500], fill=(58, 52, 46), outline=(150, 132, 92), width=6)
    big = _load_font(86, medium=True)
    cx = 1080
    for ch in "賢王祠":
        draw.text((cx - 78, 392), ch, fill=(208, 182, 110), font=big)
        cx -= 96

    # 底部说明条
    bar = Image.new("RGB", (w, 150), (247, 240, 223))
    bd = ImageDraw.Draw(bar)
    bd.text((60, 22), "贤王祠山门拱券门额「賢王祠」拓影示意",
            fill=(58, 50, 38), font=_load_font(40, medium=True))
    bd.text((60, 84), "砖石仿木山门 · 单歇山顶 · 坐南朝北 · 据公开著录绘制，非实物照片",
            fill=(122, 60, 40), font=_load_font(32))
    im.paste(bar, (0, h - 150))

    im.save(out_path, optimize=True)
    _assert_ink(im, (820, 385, 1100, 498), thresh=140, min_dark=60, tag="biane chars")
    return out_path.stat().st_size


# --------------------------------------------- 7. 贤王祠建筑格局示意 (VEC-3)
def build_xianwangci_plan(out_path):
    w, h = 1920, 1080
    im = Image.new("RGB", (w, h), (243, 236, 220))
    draw = ImageDraw.Draw(im)
    draw.rectangle([60, 60, w - 60, h - 60], outline=(120, 104, 82), width=5)

    draw.text((100, 96), "怡贤亲王祠（贤王祠）建筑格局示意",
              fill=(52, 44, 34), font=_load_font(48, medium=True))
    draw.text((100, 168), "坐南向北（名录口径） · 位于白家疃村 · 海淀区文物保护单位",
              fill=(122, 96, 66), font=_load_font(30))
    draw.text((w - 560, 100), "制作组绘制示意 · 非实测图",
              fill=(150, 62, 40), font=_load_font(30, medium=True))

    # 指北针
    draw.line([(1770, 220), (1770, 150)], fill=(52, 44, 34), width=5)
    draw.polygon([(1770, 138), (1758, 162), (1782, 162)], fill=(52, 44, 34))
    draw.text((1748, 176), "北", fill=(52, 44, 34), font=_load_font(30, medium=True))

    # 中轴线（虚线，自北向南）
    for yy in range(350, 810, 24):
        draw.line([(960, yy), (960, yy + 12)], fill=(168, 148, 116), width=3)

    def hall(x0, y0, x1, y1, label, note="", roof=False):
        draw.rectangle([x0, y0, x1, y1], fill=(214, 196, 162), outline=(96, 78, 56), width=4)
        if roof:
            draw.line([(x0 - 14, y0 - 14), (x1 + 14, y0 - 14)], fill=(96, 78, 56), width=5)
        lw = _load_font(34, medium=True)
        draw.text(((x0 + x1) // 2 - len(label) * 17, (y0 + y1) // 2 - 22), label,
                  fill=(58, 46, 32), font=lw)
        if note:
            nf = _load_font(24)
            draw.text(((x0 + x1) // 2 - len(note) * 12, (y0 + y1) // 2 + 22), note,
                      fill=(122, 96, 66), font=nf)

    # 戏楼（山门对面，坐北朝南，位于祠之正北）
    draw.polygon([(750, 255), (960, 210), (1170, 255)], fill=(140, 116, 88))
    draw.rectangle([770, 255, 1150, 345], fill=(206, 186, 148), outline=(96, 78, 56), width=4)
    draw.text((900, 283), "戏楼", fill=(58, 46, 32), font=_load_font(32, medium=True))
    draw.text((1190, 261), "坐北朝南，与山门相对", fill=(122, 96, 66), font=_load_font(24))
    draw.text((1190, 297), "（区保名录口径）", fill=(122, 96, 66), font=_load_font(24))

    # 山门（拱券门额书「贤王祠」）
    hall(820, 380, 1100, 470, "山门", "拱券门额书「贤王祠」")

    # 前殿（面阔三间）
    hall(780, 540, 1140, 640, "前殿", "面阔三间·卷棚·旋子彩绘")

    # 后殿（面阔四间）+ 月台
    draw.rectangle([830, 710, 1090, 820], fill=(214, 196, 162), outline=(96, 78, 56), width=4)
    draw.text((886, 746), "后殿", fill=(58, 46, 32), font=_load_font(36, medium=True))
    draw.rectangle([770, 820, 1150, 856], fill=(196, 178, 142), outline=(96, 78, 56), width=3)
    draw.text((894, 824), "月台", fill=(58, 46, 32), font=_load_font(26))

    # 说明
    draw.text((100, h - 150), "呈一字中轴，自北向南：戏楼—山门—前殿—后殿（海淀区文保名录口径）",
              fill=(52, 44, 34), font=_load_font(30, medium=True))
    draw.text((100, h - 100), "「坐南向北」采名录口径，另有著录作坐北朝南；具体尺寸未经测绘",
              fill=(122, 96, 66), font=_load_font(26))

    im.save(out_path, optimize=True)
    return out_path.stat().st_size


# --------------------------------------------- 8. 曹雪芹小道拓扑 (MEC-3)
def build_trail_topology(out_path):
    w, h = 1920, 1080
    im = Image.new("RGB", (w, h), (247, 242, 228))
    draw = ImageDraw.Draw(im)
    draw.rectangle([60, 60, w - 60, h - 60], outline=(120, 104, 82), width=5)

    draw.text((100, 100), "曹雪芹小道 · 香山—白家疃",
              fill=(52, 44, 34), font=_load_font(52, medium=True))
    draw.text((100, 176), "民间传说与今人命名路线 · 制作组示意 · 非测绘拓扑",
              fill=(150, 62, 40), font=_load_font(30, medium=True))

    # 山脊带（上部，避开标题区）
    draw.polygon([(60, 390), (400, 300), (760, 340), (1120, 285), (1500, 345), (1860, 300),
                  (1860, 225), (60, 225)], fill=(226, 216, 194))
    draw.text((1320, 245), "香山山脊（三炷香一带）", fill=(140, 118, 88), font=_load_font(30, medium=True))

    # 小道（蜿蜒南→北）
    pts = [(300, 900), (460, 800), (600, 840), (780, 680), (940, 720), (1090, 540),
           (1250, 460), (1390, 500), (1500, 380)]
    draw.line(pts, fill=(176, 128, 84), width=10, joint="curve")

    nodes = [
        (300, 900, "黄叶村", "正白旗 · 曹雪芹纪念馆", "above"),
        (620, 790, "卧佛寺", "十方普觉寺", "below"),
        (980, 700, "樱桃沟", "", "below"),
        (1360, 480, "三炷香", "翻山越脊", "above"),
        (1600, 310, "白家疃", "贤王祠", "above"),
    ]
    f_node = _load_font(38, medium=True)
    f_sub = _load_font(26)
    for nx, ny, name, sub, side in nodes:
        draw.ellipse([nx - 16, ny - 16, nx + 16, ny + 16], fill=(150, 62, 40))
        draw.ellipse([nx - 7, ny - 7, nx + 7, ny + 7], fill=(247, 242, 228))
        if side == "below":
            draw.text((nx - len(name) * 19, ny + 26), name, fill=(46, 38, 30), font=f_node)
            if sub:
                draw.text((nx - len(sub) * 13, ny + 76), sub, fill=(122, 96, 66), font=f_sub)
        else:
            draw.text((nx - len(name) * 19, ny - 96), name, fill=(46, 38, 30), font=f_node)
            if sub:
                draw.text((nx - len(sub) * 13, ny - 146), sub, fill=(122, 96, 66), font=f_sub)

    draw.text((100, h - 140), "南起黄叶村，北至白家疃贤王祠，翻三炷香山脊——传说中曹雪芹往来西山的小路",
              fill=(52, 44, 34), font=_load_font(30, medium=True))
    draw.text((100, h - 92), "「乾隆二十三年（一七五八）徙居白家疃」据敦敏《瓶湖懋斋记盛》——过录本，真伪存争",
              fill=(122, 96, 66), font=_load_font(26))

    im.save(out_path, optimize=True)
    return out_path.stat().st_size


# --------------------------------------------- 9. 疃字释义卡 (VEC-4)
def build_tuan_card(out_path):
    w, h = 1920, 1080
    im = Image.new("RGB", (w, h), (243, 236, 220))
    draw = ImageDraw.Draw(im)
    draw.rectangle([60, 60, w - 60, h - 60], outline=(120, 104, 82), width=5)

    # 左侧大字卡
    draw.rectangle([110, 150, 610, 760], fill=(250, 246, 234), outline=(96, 78, 56), width=6)
    big = _load_font(360, medium=True)
    draw.text((240, 220), "疃", fill=(46, 38, 30), font=big)
    draw.text((170, 640), "音 tuǎn · 注音 ㄊㄨㄢˇ",
              fill=(122, 96, 66), font=_load_font(34))
    draw.text((170, 690), "《唐韵》土短切",
              fill=(122, 96, 66), font=_load_font(30))

    # 右侧义项三段
    rows = [
        ("本义", "禽獸所踐處也", "——《說文解字·田部》"),
        ("诗证", "町疃鹿場", "——《詩經·豳風·東山》毛傳：町疃，鹿跡也"),
        ("引申", "村莊 · 村落", "多用于北方地名。陆游《入蜀记》：「村疃数家」"),
    ]
    y0 = 170
    for tag, main, src in rows:
        draw.rectangle([680, y0, 820, y0 + 90], fill=(150, 62, 40))
        draw.text((702, y0 + 22), tag, fill=(250, 246, 234), font=_load_font(40, medium=True))
        draw.text((860, y0 + 6), main, fill=(46, 38, 30), font=_load_font(56, medium=True))
        draw.text((860, y0 + 92), src, fill=(122, 96, 66), font=_load_font(30))
        y0 += 200

    # 底部地名链
    draw.rectangle([110, 820, w - 110, 960], fill=(232, 222, 198), outline=(96, 78, 56), width=3)
    draw.text((150, 842), "民国四年《实测京师四郊地图》标注该村作「白」+疃灘族字，今规范作「白家疃」。",
              fill=(58, 50, 38), font=_load_font(34, medium=True))
    draw.text((150, 902), "口中曰滩（tān），纸上曰疃（tuǎn）——两种写法并存已逾二百年。",
              fill=(150, 62, 40), font=_load_font(30, medium=True))
    draw.text((w - 480, 100), "制作组示意 · 非实物照片",
              fill=(150, 62, 40), font=_load_font(28, medium=True))

    im.save(out_path, optimize=True)
    _assert_ink(im, (240, 220, 620, 620), thresh=120, min_dark=300, tag="tuan giant")
    return out_path.stat().st_size


# --------------------------------------------- 10. MEC-4 五段时代叠合
def build_mec4_eras(out_path):
    w, h = 1920, 1080
    im = Image.new("RGB", (w, h), (240, 234, 218))
    draw = ImageDraw.Draw(im)

    draw.rectangle([60, 60, w - 60, h - 60], outline=(120, 104, 82), width=5)
    draw.text((100, 96), "六段叠合 · 白家疃的写法与实在",
              fill=(52, 44, 34), font=_load_font(46, medium=True))
    draw.text((100, 160), "制作组示意 · 非测绘拓扑",
              fill=(122, 96, 66), font=_load_font(26))

    eras = [
        ("旧名", "白家滩", "相传白姓聚居成村（存疑）", (150, 108, 70)),
        ("清 · 雍正初年", "允祥别业", "一说雍正二年造；指挥部设此亦一说", (150, 62, 40)),
        ("清 · 雍正十年", "一七三二", "允祥身后敕建贤王祠（区保名录口径）", (96, 104, 84)),
        ("民国四年", "一九一五", "实测京师四郊地图尚作「白家滩」", (88, 96, 112)),
        ("一九五七", "地震台", "鹫峰台迁此重建，基准台恢复观测", (70, 90, 110)),
        ("今", "白家疃", "村仍存 · 地球观象台在村北运行", (120, 88, 110)),
    ]

    card_w = 270
    gap = 22
    x0 = 92
    y0 = 260
    ch_ = 440

    for i, (era, title, note, color) in enumerate(eras):
        x = x0 + i * (card_w + gap)
        draw.rectangle([x, y0, x + card_w, y0 + ch_], fill=(250, 246, 234), outline=color, width=6)
        draw.rectangle([x, y0, x + card_w, y0 + 92], fill=color)
        draw.text((x + 20, y0 + 26), era, fill=(250, 246, 234), font=_load_font(32, medium=True))

        cy = y0 + 150
        for chx in title:
            draw.text((x + card_w // 2 - 20, cy), chx, fill=(48, 40, 32), font=_load_font(38, medium=True))
            cy += 46

        # 注记折行（每行 9 字，至多两行，避开标题）
        nf = _load_font(24)
        for li in range(0, len(note), 9):
            draw.text((x + 20, y0 + ch_ - 94 + (li // 9) * 36), note[li:li + 9],
                      fill=(122, 96, 66), font=nf)

        if i < len(eras) - 1:
            ax = x + card_w + gap // 2
            draw.polygon([(ax - 9, y0 + ch_ // 2 - 14), (ax + 9, y0 + ch_ // 2), (ax - 9, y0 + ch_ // 2 + 14)],
                         fill=(120, 104, 82))

    draw.text((100, h - 130), "口中滩，纸上疃——两种写法并存已逾二百年。",
              fill=(150, 62, 40), font=_load_font(34, medium=True))

    im.save(out_path, optimize=True)
    return out_path.stat().st_size


# --------------------------------------------- main
def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    built = [
        ("mec1_sanshanyuan_ridge_roi_4000.png", build_mec1_ridge_roi, "MEC-1",
         "《清 佚名 三山五园图》香山山脊带切片（公有领域）；白家疃村经目视核验不在本图幅，此为村南隔山相望的西山主脉"),
        ("beijing_1915_baijiatuan_roi.png", build_1915_baijiatuan_roi, "MEC-2",
         "民国四年(1915)《實測京師四郊地圖》白家疃村—楊家村—黑龍潭段切片（公有领域；村名标注「白」+疃/灘族复杂字形，家字未得确认；窗口经图面标注目视核验）"),
        ("shuowen_tuan_folio.png", build_shuowen_folio, "VEC-1",
         "《說文解字·田部》疃字条书影示意（依据公开文本排印，非原刊扫描）"),
        ("shijing_dongshan_folio.png", build_shijing_folio, "VEC-1",
         "《詩經·豳風·東山》町疃鹿场书影示意（依据公开文本排印，非原刊扫描）"),
        ("xianwangci_beiji_tuoying.png", build_xianwangci_beiji, "VEC-1",
         "《敕賜白家疃賢王祠祭田碑記》碑记拓影示意（残碑四通之一，额题据海淀区文保名录著录；碑文全文未考得，碑面不录正文；非原石拓片）"),
        ("xianwangci_shanmen_biane.png", build_shanmen_biane, "VEC-1",
         "贤王祠山门拱券门额「賢王祠」拓影示意（据公开著录，制作组绘制，非实物扫描）"),
        ("xianwangci_gaiju_plan.png", build_xianwangci_plan, "VEC-3",
         "怡贤亲王祠建筑格局示意（坐南向北·一字中轴，戏楼—山门—前殿—后殿，海淀区文保名录口径；制作组绘制，非实物照片，非实测图）"),
        ("caoxueqin_trail_topology.png", build_trail_topology, "MEC-3",
         "曹雪芹小道拓扑示意（民间传说与今人命名路线；制作组示意，非测绘拓扑）"),
        ("tuan_ziyi_card.png", build_tuan_card, "VEC-4",
         "疃字释义卡（制作组绘制，非实物照片）"),
        ("mec4_era_overlay.png", build_mec4_eras, "MEC-4",
         "六段时代叠合图（旧名滩/雍正初别业/雍正十年敕建贤王祠/1915实测图作白家滩/1957地震台/今；别业年代两说并存；制作组示意，非测绘拓扑）"),
    ]

    rows = []
    for name, fn, cls, note in built:
        out = OUT_DIR / name
        try:
            size = fn(out)
            rows.append((name, cls, note, str(size), sha256_of(out), "OK"))
            print("OK   %-42s %8d" % (name, size))
        except Exception as exc:
            rows.append((name, cls, note, "-", "-", "FAIL: %s" % exc))
            print("FAIL %-42s %s" % (name, exc))

    with open(OUT_DIR / "sources.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["file", "class", "note", "bytes", "sha256", "status"])
        for r in rows:
            w.writerow(r)

    for name, _, _, _, _, st in rows:
        if st == "OK":
            shutil.copy(OUT_DIR / name, PUBLIC_DIR / name)

    ok = sum(1 for r in rows if r[5] == "OK")
    print("\n=== %d/%d 资产成功 ===" % (ok, len(rows)))
    return rows


if __name__ == "__main__":
    main()
