#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E26《十方普觉寺·五次易名的半部北京佛教史》Task 1: 地理切片与视觉资产预处理.

产出 assets/hist_shifangpujue/ 全套资产并同步 /tmp/chemistry-video/public/shifangpujue/:

  1. sanshanyuan_shuoan_roi_4000.png (MEC-1)
     母版《清 佚名 三山五园图》寿安山段切片 (4000x1400).
  2. beijing_1915_shuoan_roi.png (MEC-2)
     民国四年(1915)《實測京師四郊地圖》寺址带切片 (1920x1080).
  3. yuanshi_folio.png (VEC-1)
     《元史》「昭孝寺」条书影（本集一手正史，元代两次易名与铸佛依据）。
  4. shie_pailue_mingbing_folio.png (VEC-1)
     清代重修寺记碑记拓影（雍正十二年赐名依据）。
  5. shie_yaodian_tuoying.png (VEC-1)
     寺额「十方普觉寺」匾额拓影（御赐名号实物呈现）。
  6. shifangpujue_wofoe_photo.png (VEC-3)
     元代释迦牟尼涅槃铜卧佛全貌。
  7. shifangpujue_wofoe_face.png (VEC-3)
     铜卧佛面部特写（年代错位页专用）。
  8. shifangpujue_garden_view.png (VEC-3)
     卧佛寺与国家植物园共存实景。
  9. mec3_six_names_timeline.png (MEC-3)
     六名纵贯时间轴（唐—元—元—明—明—清），1920x1080。
 10. mec4_composite_eras.png (MEC-4)
     四时代叠合图（唐创寺/元铸佛/明清易名/当代国保），1920x1080。
 11. sources.csv (sha256/MEC/VEC/版权留痕) + 同步 public/shifangpujue/

🔴 E23 事故防线（build_1915_roi 内置断言）:
   拼接窗口宽必须 >= ox + crop_w，否则 PIL 黑色补齐，成片右侧纯黑。
   裁切后量化校验右侧 260px 黑像素占比。

🔴 E24/E25 教训（屏显/牌面纪律，本脚本牌面文字一律用全字形汉字）:
   禁用 U+3007 圆圈数字（宋体下不可见 → OCR 漏读）；公历纪年不用阿拉伯数字。
   寺额与碑记牌面文字必须为全字形，否则 QA v2 L4-a 屏显判据会误报。

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
OUT_DIR = REPO / "assets" / "hist_shifangpujue"
PUBLIC_DIR = pathlib.Path("/tmp/chemistry-video/public/shifangpujue")
CACHE_DIR = pathlib.Path("/tmp/sfpj_cache")
MASTER_MAP = pathlib.Path("/Users/mac/Downloads/清 佚名 三山五园图51x88.tif")

WMTS_TILE_URL = "https://gis.sinica.edu.tw/beijing/file-exists.php?img=Beijing_1915-png-%d-%d-%d"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

# 1915 瓦片窗口（寿安山/香山一带）
T19_TX0, T19_TX1 = 53930, 53942
T19_TY0, T19_TY1 = 24814, 24822
T19_OX, T19_OY = 200, 500
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


# --------------------------------------------- 1. 三山五园图寿安山切片
def build_sanshanyuan_roi(out_path):
    Image.MAX_IMAGE_PIXELS = None
    im = Image.open(MASTER_MAP)
    roi = im.crop((3600, 4200, 7600, 5600))
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
        cf = CACHE_DIR / ("tile_1915_sfpj_%d_%d_%d.png" % (z, tx, ty))
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

    coords = [(tx, ty) for tx in range(T19_TX0, T19_TX1 + 1) for ty in range(T19_TY0, T19_TY1 + 1)]
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


# --------------------------------------------- 3. 元史书影
def build_yuanshi_folio(out_path):
    """《元史·英宗本纪》至治元年冶铜条。

    🔴 E26 判据层审核 C2 订正：原版伪造「長五尺」与「北京現存最大最古銅臥佛」，
       前者与实测 5.3m 差三倍（实为「長丈六」之讹），后者是**现代断语**混进古籍书影。
       现只保留可核的原文四句，并显式标注「依公開文本排印·非原刊掃描」。
    """
    columns = [
        "至治元年十二月",
        "冶銅五十萬斤",
        "作壽安山寺佛像",
        "依公開文本排印",
        "非原刊掃描",
    ]
    center_text = "元\n史\n\n英\n宗\n本\n紀"
    return _draw_folio(out_path, paper=(243, 237, 221), border=(54, 38, 26),
                       columns=columns, center_text=center_text, seal_text="")
# --------------------------------------------- 4. 清代重修寺记碑记拓影
def build_shi_ji_bei(out_path):
    w, h = 1400, 1900
    im = Image.new("RGB", (w, h), (58, 52, 46))
    draw = ImageDraw.Draw(im)

    # 碑面（浅色拓片）
    draw.rectangle([90, 90, w - 90, h - 90], fill=(228, 222, 206))
    draw.rectangle([130, 130, w - 130, h - 130], outline=(120, 110, 96), width=4)

    big = _load_font(86, medium=True)
    small = _load_font(50)
    cy = 230
    for ch in "重修十方普覺寺記":
        draw.text((w // 2 - 46, cy), ch, fill=(38, 32, 26), font=big)
        cy += 104

    cy = 1320
    for line in ["雍正十二年歲次甲寅", "奉敕重修賜額十方普覺"]:
        cx = w // 2 - len(line) * 25
        for ch in line:
            draw.text((cx, cy), ch, fill=(52, 44, 36), font=small)
            cx += 50
        cy += 70

    # 碑额与边框装饰
    draw.rectangle([90, 90, w - 90, 170], fill=(196, 186, 168), outline=(120, 110, 96), width=3)

    im.save(out_path, optimize=True)
    return out_path.stat().st_size


# --------------------------------------------- 5. 寺额「十方普觉寺」拓影
def build_shie_tuoying(out_path):
    w, h = 1920, 1080
    im = Image.new("RGB", (w, h), (196, 190, 178))
    draw = ImageDraw.Draw(im)

    # 殿前木匾底
    for y in range(h):
        t = y / float(h)
        draw.line([0, y, w, y], fill=(int(96 + 40 * (1 - abs(t - 0.5) * 2)),
                                    int(72 + 32 * (1 - abs(t - 0.5) * 2)),
                                    int(54 + 26 * (1 - abs(t - 0.5) * 2))))

    # 匾额框（黑底金字）
    draw.rectangle([340, 300, 1580, 720], fill=(44, 38, 32), outline=(126, 108, 76), width=8)
    draw.rectangle([368, 328, 1552, 692], outline=(146, 126, 88), width=3)

    big = _load_font(150, medium=True)
    cx = 960
    for ch in "十方普覺寺":
        draw.text((cx - 78, 400), ch, fill=(206, 178, 104), font=big)
        cx -= 158

    # 下方说明条
    bar = Image.new("RGB", (w, 140), (247, 240, 223))
    bd = ImageDraw.Draw(bar)
    bd.text((60, 26), "寺额排印示意 · 非实物拓片 · 雍正十二年（一七三四年）",
            fill=(58, 50, 38), font=_load_font(38, medium=True))
    bd.text((60, 82), "此名沿用至今，民间称「卧佛寺」",
            fill=(122, 60, 40), font=_load_font(32))
    im.paste(bar, (0, 940))

    im.save(out_path, optimize=True)
    return out_path.stat().st_size


# --------------------------------------------- 6. 元代铜卧佛全貌
def build_wofoe_photo(out_path):
    w, h = 1920, 1080
    im = Image.new("RGB", (w, h), (74, 64, 56))
    draw = ImageDraw.Draw(im)

    # 殿内幽暗背景
    for y in range(h):
        t = y / float(h)
        draw.line([0, y, w, y], fill=(int(58 + 26 * (1 - t)), int(50 + 22 * (1 - t)), int(44 + 20 * (1 - t))))

    # 佛座台基（居中，纵深两层）
    draw.rectangle([300, 892, 1620, 962], fill=(126, 112, 96))
    draw.rectangle([350, 838, 1570, 892], fill=(150, 136, 116))
    # 佛座须弥座束腰线
    draw.rectangle([340, 856, 1580, 872], fill=(104, 92, 78))

    # 卧佛本体（右胁而卧，长约五米）
    # 躯干（下摆略宽，肩部收窄）
    draw.polygon([(430, 640), (560, 520), (900, 486), (1300, 500), (1520, 570),
                   (1520, 800), (1280, 856), (700, 856), (470, 780)],
                  fill=(180, 146, 86))
    draw.polygon([(470, 660), (580, 548), (900, 514), (1290, 528), (1480, 592),
                   (1480, 782), (1270, 828), (710, 828), (508, 764)],
                  fill=(202, 166, 98))
    # 袈裟褶皱（沿躯干走向的弧线）
    for i in range(6):
        y = 566 + i * 44
        draw.arc([560, y, 1500, y + 150], 195, 345, fill=(154, 122, 68), width=5)
    # 衣缘
    draw.arc([470, 700, 1520, 880], 20, 160, fill=(160, 126, 72), width=6)

    # 头（右胁，枕右臂，面朝观众）
    draw.ellipse([388, 470, 640, 722], fill=(206, 172, 104))
    draw.ellipse([410, 492, 622, 706], fill=(228, 194, 126))
    # 肉髻
    draw.ellipse([462, 442, 566, 538], fill=(196, 162, 96))
    draw.ellipse([476, 456, 552, 526], fill=(214, 178, 112))
    # 面部：闭目（下弧线 = 垂目），微笑唇
    draw.arc([444, 566, 528, 612], 200, 340, fill=(120, 90, 50), width=5)   # 左垂目
    draw.arc([512, 566, 596, 612], 200, 340, fill=(120, 90, 50), width=5)   # 右垂目
    draw.line([(468, 574), (500, 574)], fill=(120, 90, 50), width=5)          # 睫线
    draw.line([(536, 574), (568, 574)], fill=(120, 90, 50), width=5)
    draw.arc([488, 630, 556, 672], 15, 165, fill=(112, 82, 44), width=5)      # 唇
    draw.line([(522, 592), (512, 620), (532, 620)], fill=(140, 106, 58), width=4)  # 鼻
    # 双耳
    draw.ellipse([372, 540, 404, 660], fill=(198, 164, 98))
    draw.ellipse([626, 540, 658, 660], fill=(198, 164, 98))

    # 右臂：自肩下垂于体侧，垫于头下（弧线走在肩线以下，不遮面部）
    draw.arc([470, 640, 860, 900], 200, 350, fill=(196, 162, 96), width=54)
    # 左臂：覆于腹前
    draw.arc([920, 690, 1330, 900], 190, 330, fill=(196, 162, 96), width=52)

    # 双足（右胁末端，叠于台基上）
    draw.ellipse([1398, 726, 1560, 838], fill=(190, 156, 92))
    draw.ellipse([1424, 742, 1544, 822], fill=(208, 174, 104))

    # 供案（置于双足之前的地面层，不压佛身）
    draw.rectangle([1560, 900, 1880, 944], fill=(96, 82, 66))
    draw.rectangle([1580, 944, 1880, 962], fill=(74, 62, 50))
    # 供案上长明灯
    for lx in (1620, 1720, 1820):
        draw.ellipse([lx - 15, 872, lx + 15, 902], fill=(224, 184, 96))
        draw.ellipse([lx - 7, 878, lx + 7, 898], fill=(250, 228, 152))

    im.save(out_path, optimize=True)
    return out_path.stat().st_size


# --------------------------------------------- 7. 铜卧佛面部特写
def build_wofoe_face(out_path):
    w, h = 1920, 1080
    im = Image.new("RGB", (w, h), (66, 58, 50))
    draw = ImageDraw.Draw(im)

    # 背景
    for y in range(h):
        t = y / float(h)
        draw.line([0, y, w, y], fill=(int(52 + 20 * (1 - t)), int(46 + 18 * (1 - t)), int(40 + 16 * (1 - t))))

    # 面部（占画面主体）
    draw.ellipse([420, 120, 1500, 1000], fill=(210, 176, 108))
    draw.ellipse([460, 160, 1460, 960], fill=(232, 198, 128))
    # 肉髻
    draw.ellipse([790, 60, 1130, 300], fill=(202, 168, 100))
    draw.ellipse([820, 88, 1100, 272], fill=(222, 188, 120))

    # 弯眉
    draw.arc([650, 400, 900, 520], 190, 350, fill=(132, 100, 54), width=12)
    draw.arc([1020, 400, 1270, 520], 190, 350, fill=(132, 100, 54), width=12)
    # 垂目（半阖）
    draw.arc([680, 500, 890, 600], 0, 180, fill=(96, 72, 40), width=10)
    draw.arc([1030, 500, 1240, 600], 0, 180, fill=(96, 72, 40), width=10)
    # 白毫与螺发
    for i in range(11):
        draw.ellipse([880 + i * 16, 300 + (i % 3) * 8, 892 + i * 16, 312 + (i % 3) * 8],
                     fill=(178, 146, 86))
    # 鼻
    draw.line([(960, 540), (940, 700), (980, 700)], fill=(140, 106, 58), width=8)
    # 唇（微笑）
    draw.arc([880, 740, 1040, 820], 20, 160, fill=(112, 82, 44), width=10)
    # 双耳
    draw.ellipse([400, 300, 480, 620], fill=(206, 172, 104))
    draw.ellipse([1440, 300, 1520, 620], fill=(206, 172, 104))
    # 螺发（顶部）
    for i in range(16):
        for j in range(6):
            cx = 700 + i * 42
            cy = 200 + j * 30
            draw.ellipse([cx, cy, cx + 20, cy + 20], fill=(180, 148, 88))

    im.save(out_path, optimize=True)
    return out_path.stat().st_size


# --------------------------------------------- 8. 卧佛寺与国家植物园共存实景
def build_garden_view(out_path):
    w, h = 1920, 1080
    im = Image.new("RGB", (w, h), (200, 216, 226))
    draw = ImageDraw.Draw(im)

    # 天空
    for y in range(400):
        t = y / 400.0
        draw.line([0, y, w, y], fill=(int(196 - 34 * t), int(214 - 30 * t), int(230 - 28 * t)))
    # 远山
    draw.polygon([(0, 400), (420, 250), (760, 370), (1180, 230), (1560, 350), (w, 280), (w, 420)],
                 fill=(168, 180, 172))
    # 地面
    draw.rectangle([0, 780, w, h], fill=(176, 178, 156))
    draw.rectangle([0, 860, w, h], fill=(160, 164, 142))

    # 寺殿（中景）
    draw.rectangle([560, 470, 1420, 800], fill=(196, 176, 148), outline=(126, 106, 84), width=4)
    # 殿顶
    draw.polygon([(500, 470), (990, 330), (1480, 470)], fill=(112, 96, 78))
    draw.polygon([(500, 470), (990, 330), (1480, 470)], outline=(78, 66, 54), width=5)
    # 殿门
    draw.rectangle([900, 620, 1080, 800], fill=(88, 74, 58))
    draw.rectangle([912, 632, 1068, 800], fill=(62, 52, 42))
    # 寺额
    draw.rectangle([880, 570, 1100, 618], fill=(48, 42, 36), outline=(140, 118, 78), width=3)

    # 植物园侧景：温室与树木
    for tx, r in [(300, 90), (520, 70), (1620, 84), (1800, 66)]:
        draw.ellipse([tx - r, 620 - r, tx + r, 620 + r], fill=(112, 142, 96))
    # 温室
    draw.polygon([(1420, 800), (1560, 660), (1700, 800)], fill=(206, 220, 214), outline=(140, 152, 146), width=4)
    for gx in range(1440, 1700, 40):
        draw.line([(gx, 790), (gx, 800)], fill=(140, 152, 146), width=2)
    # 步道
    draw.polygon([(700, 1080), (1180, 1080), (1080, 860), (860, 860)], fill=(198, 194, 182))

    # 说明条
    bar = Image.new("RGB", (w, 130), (247, 240, 223))
    bd = ImageDraw.Draw(bar)
    bd.text((60, 24), "卧佛寺与国家植物园 · 制作组绘制示意 · 非实物照片",
            fill=(58, 50, 38), font=_load_font(40, medium=True))
    bd.text((60, 80), "寺在寿安山南麓，今为国家植物园内古建与展陈空间",
            fill=(122, 60, 40), font=_load_font(32))
    im.paste(bar, (0, 950))

    im.save(out_path, optimize=True)
    return out_path.stat().st_size


# --------------------------------------------- 9. MEC-3 六名纵贯时间轴
def build_six_names_timeline(out_path):
    w, h = 1920, 1080
    im = Image.new("RGB", (w, h), (247, 242, 228))
    draw = ImageDraw.Draw(im)

    draw.rectangle([60, 60, w - 60, h - 60], outline=(120, 104, 82), width=5)

    title = _load_font(52, medium=True)
    draw.text((100, 100), "六名纵贯 · 唐至清", fill=(52, 44, 34), font=title)
    draw.text((100, 176), "寺名沿革即断代史（本页为制作组示意 · 非测绘拓扑）",
              fill=(122, 96, 66), font=_load_font(32))

    # 时间轴
    axis_y = 560
    draw.line([(160, axis_y), (w - 160, axis_y)], fill=(96, 84, 66), width=8)

    names = [
        ("唐 · 贞观", "兜率寺", "始建"),
        ("元 · 至治元年", "昭孝寺", "改建"),
        ("元", "洪庆寺", "改称"),
        ("明 · 正统八年", "寿安山寺", "重修改称"),
        ("明 · 成化十八年", "永安寺", "再改"),
        ("清 · 雍正十二年", "十方普觉寺", "御赐"),
    ]

    slot = (w - 320) / len(names)
    f_era = _load_font(28)
    f_name = _load_font(40, medium=True)
    f_note = _load_font(24)

    for i, (era, name, note) in enumerate(names):
        cx = 160 + slot * (i + 0.5)
        # 节点
        draw.ellipse([cx - 16, axis_y - 16, cx + 16, axis_y + 16], fill=(150, 62, 40))
        draw.line([(cx, axis_y - 16), (cx, axis_y - 90)], fill=(120, 104, 82), width=3)
        # 上：年号
        draw.text((cx - len(era) * 14, axis_y - 132), era, fill=(90, 76, 58), font=f_era)
        # 下：名号（交替上下避免拥挤）
        if i % 2 == 0:
            draw.text((cx - len(name) * 21, axis_y + 40), name, fill=(46, 38, 30), font=f_name)
            draw.text((cx - len(note) * 12, axis_y + 100), note, fill=(122, 96, 66), font=f_note)
        else:
            draw.text((cx - len(name) * 21, axis_y - 260), name, fill=(46, 38, 30), font=f_name)
            draw.text((cx - len(note) * 12, axis_y - 216), note, fill=(122, 96, 66), font=f_note)
            draw.line([(cx, axis_y + 16), (cx, axis_y + 40)], fill=(120, 104, 82), width=3)

    # 底部：寺是唐的，佛是元的
    note_f = _load_font(30, medium=True)
    draw.text((100, h - 150), "寺创于唐 · 铜卧佛铸于元 · 相隔六百余载",
              fill=(150, 62, 40), font=note_f)

    im.save(out_path, optimize=True)
    return out_path.stat().st_size


# --------------------------------------------- 10. MEC-4 四时代叠合图
def build_mec4_composite(out_path):
    w, h = 1920, 1080
    im = Image.new("RGB", (w, h), (240, 234, 218))
    draw = ImageDraw.Draw(im)

    draw.rectangle([60, 60, w - 60, h - 60], outline=(120, 104, 82), width=5)
    draw.text((100, 96), "四时代叠合 · 唐创寺 / 元铸佛 / 明清易名 / 当代国保",
              fill=(52, 44, 34), font=_load_font(42, medium=True))
    draw.text((100, 158), "制作组示意 · 非测绘拓扑",
              fill=(122, 96, 66), font=_load_font(26))

    eras = [
        ("唐 · 贞观", "始建兜率寺", "寺的创基", (150, 108, 70)),
        ("元 · 至治", "昭孝寺 / 洪庆寺", "铸释迦牟尼铜卧佛", (140, 70, 60)),
        ("明 · 清", "寿安山寺 / 永安寺 / 十方普觉寺", "三度易名", (96, 104, 84)),
        ("当代", "第五批全国重点文物保护单位", "国家植物园内", (88, 96, 112)),
    ]

    card_w = 400
    gap = 30
    x0 = 100
    y0 = 280
    ch = 420

    for i, (era, title, note, color) in enumerate(eras):
        x = x0 + i * (card_w + gap)
        draw.rectangle([x, y0, x + card_w, y0 + ch], fill=(250, 246, 234), outline=color, width=6)
        draw.rectangle([x, y0, x + card_w, y0 + 96], fill=color)
        draw.text((x + 26, y0 + 28), era, fill=(250, 246, 234), font=_load_font(36, medium=True))

        # 竖排标题
        cy = y0 + 140
        for chx in title:
            draw.text((x + card_w // 2 - 22, cy), chx, fill=(48, 40, 32), font=_load_font(44, medium=True))
            cy += 56

        draw.text((x + 26, y0 + ch - 90), note, fill=(122, 96, 66), font=_load_font(26))
        if i < len(eras) - 1:
            ax = x + card_w + gap // 2
            draw.polygon([(ax - 10, y0 + ch // 2 - 16), (ax + 10, y0 + ch // 2), (ax - 10, y0 + ch // 2 + 16)],
                         fill=(120, 104, 82))

    draw.text((100, h - 130), "寺名换了五次，寺里那尊佛一直是一尊元朝的佛。",
              fill=(150, 62, 40), font=_load_font(34, medium=True))

    im.save(out_path, optimize=True)
    return out_path.stat().st_size


# --------------------------------------------- main
def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    built = [
        ("sanshanyuan_shuoan_roi_4000.png", build_sanshanyuan_roi, "MEC-1", "《清 佚名 三山五园图》寿安山段切片（公有领域）"),
        ("beijing_1915_shuoan_roi.png", build_1915_roi, "MEC-2", "民国四年(1915)《實測京師四郊地圖》寿安山段切片（公有领域）"),
        ("yuanshi_folio.png", build_yuanshi_folio, "VEC-1", "《元史·英宗本纪》至治元年冶铜条·依公开文本排印，非原刊扫描"),
        ("shi_ji_bei_tuoying.png", build_shi_ji_bei, "VEC-1", "清代重修寺记碑记拓影示意（依据公开文本排印，非原石拓片）"),
        ("shie_yaodian_tuoying.png", build_shie_tuoying, "VEC-1", "寺额「十方普觉寺」拓影示意（依据公开图文，非实物扫描）"),
        ("shifangpujue_wofoe_photo.png", build_wofoe_photo, "VEC-3", "元代释迦牟尼涅槃铜卧佛影像示意（制作组绘制，非实物照片）"),
        ("shifangpujue_wofoe_face.png", build_wofoe_face, "VEC-3", "铜卧佛面部特写示意（制作组绘制，非实物照片）"),
        ("shifangpujue_garden_view.png", build_garden_view, "VEC-3", "卧佛寺与国家植物园共存实景示意（制作组绘制，非实物照片）"),
        ("mec3_six_names_timeline.png", build_six_names_timeline, "MEC-3", "六名纵贯时间轴（制作组矢量示意）"),
        ("mec4_composite_eras.png", build_mec4_composite, "MEC-4", "四时代叠合图（制作组矢量示意）"),
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
