#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E29《郭守敬·一泉入都》资产预处理：地理示意 + 古籍排印书影 + 衰败链主轴.

产出 assets/hist_guoshoujing/ 全套资产并同步 /tmp/chemistry-video/public/guoshoujing/:

  1. jiulongchi_dry_schematic.png (VEC-3)
     昌平龙山九龙池·干涸龙首示意（今日泉眼无自然涌水）。
  2. yuanshi_liushi_folio.png (VEC-1)
     《元史·郭守敬传》中统三年面陈水利六事条（首事即引玉泉水）· 依公开文本排印。
  3. jianyi_schematic.png (VEC-3)
     简仪结构示意（原件不存，明正统年间仿制品今存南京紫金山天文台）。
  4. guansingtai_schematic.png (VEC-3)
     登封观星台示意（元代遗构，二十七所之「河南府陽城」站）。
  5. sihai_27_stations_mec3.png (MEC-3)
     四海测验二十七所按「北极出地」排布示意（依《元史·天文志》全名单，非地图投影）。
  6. yuanshi_suiyu_folio.png (VEC-1)
     《元史》歲餘条「三百六十五日二十四刻二十五分」· 依公开文本排印。
  7. guoshoujing_route_mec3.png (MEC-3)
     白浮泉—瓮山泊—积水潭引水线路示意（纯矢量，严禁编造精确走向）。
  8. yuanshi_baifu_folio.png (VEC-1)
     《元史·郭守敬传》白浮泉引水段「西折而南，經瓮山泊」· 依公开文本排印。
  9. yuanshi_yanyou_folio.png (VEC-1)
     《元史·河渠志》延祐元年「源泉微細，不能通流」· 依公开文本排印。
 10. guoshoujing_decay_chain_mec4.png (MEC-4)
     衰败链时间轴（本集主轴）：大德七年冲决→大德十一年崩三十余里→皇庆元年修
     →延祐元年淤塞→乾隆己巳湮没→今。
 11. sources.csv (sha256/MEC/VEC/版权留痕) + 同步 public/guoshoujing/

🔴 为何不做 1915 瓦片（E23 两防线随瓦片一并省略）：
   《实测京师四郊图》(1915) 与清代《三山五园图》所绘均为渠道湮没**之后**的地表形态，
   对「元代白浮泉引水线路」不构成测绘证据——清代舆图上没有这条渠，画上去即是伪造。
   本集地图类证据一律用 MEC-3 纯矢量示意并显式标注「制作组示意 · 非测绘拓扑」。
   （若后续确需 1915 瓦片，必须照 extract_shifangpujue_assets.py 补回两条防线断言：
   拼接窗口宽 >= ox+crop_w、裁切后右侧 260px 黑像素占比校验。）

🔴 E24/E25/E26 教训（屏显/牌面纪律）：
   全部牌面文字一律全字形汉字纪年；禁 U+3007 圆圈数字；禁阿拉伯数字上牌面。
   示意图一律标「制作组示意 / 绘制示意 · 非实物照片 / 非测绘拓扑」；
   排印书影一律标「依公開文本排印 · 非原刊掃描」。assert_clean_text 内置硬断言。

引文纪律：所有排印书影的文字**逐字**取自 guoshoujing_video/research.md 已直核原文
（《元史》维基文库转录本），不自撰、不转写；引文内繁简异体照录（牐／甕／瓮）。

Python 3.9.6 兼容: 禁 X | None, 禁 match.
"""
import csv
import hashlib
import pathlib
import re
import shutil

from PIL import Image, ImageDraw, ImageFont

REPO = pathlib.Path("/Volumes/macstudio/video-projects")
OUT_DIR = REPO / "assets" / "hist_guoshoujing"
PUBLIC_DIR = pathlib.Path("/tmp/chemistry-video/public/guoshoujing")

PAPER = (243, 237, 221)
INK = (54, 46, 36)
INK_SOFT = (90, 78, 62)
VERMILION = (150, 62, 40)
INDIGO = (47, 93, 124)

# 🔴 牌面文字卫生：全字形汉字纪年，禁 U+3007，禁任何 ASCII 数字（含四位公历）。
_BAD_GLYPH = re.compile(r"[0-9\u3007]")


def assert_clean_text(text):
    m = _BAD_GLYPH.search(text)
    assert not m, "牌面文字违规（禁 ASCII 数字/U+3007）：%r in %r" % (
        m.group(0) if m else "", text[:48])


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


def _draw_note(draw, text, x, y, size=32, medium=True, fill=INK, w=1920):
    """在画布上写说明行，并硬断言整行不越出画布（E23 防线的矢量等价物）。"""
    assert_clean_text(text)
    font = _load_font(size, medium=medium)
    est_w = int(len(text) * size * 1.02) + 8
    assert x >= 0 and y >= 0 and x + est_w <= w, (
        "说明行越界: (%d,%d)+%d > %d : %s" % (x, y, est_w, w, text[:24]))
    draw.text((x, y), text, fill=fill, font=font)


def _caption_bar(im, line1, line2=None, bar_h=130):
    """底部说明条：示意/排印件的红线标注。"""
    w, h = im.size
    _draw_note(ImageDraw.Draw(im), "", 0, 0)  # 占位保持断言路径一致
    bar = Image.new("RGB", (w, bar_h), (247, 240, 223))
    bd = ImageDraw.Draw(bar)
    _draw_note(bd, line1, 60, 24, size=40)
    if line2:
        _draw_note(bd, line2, 60, 82, size=32, medium=False, fill=(122, 60, 40))
    im.paste(bar, (0, h - bar_h))
    return im


# --------------------------------------------- 通用古籍排印书影
def _draw_folio(out_path, columns, center_text, note,
                width=1600, height=2200, font_size=38, col_pitch=54):
    """竖排右起排印书影。columns 为右起各列文字（逐字自 research.md 直核原文）。

    书影本体只含原文与书名，不得混入现代断语（E26 C2 教训）；
    「依公開文本排印」等排印声明放底部说明条，与原文区隔。
    """
    for col in columns:
        assert_clean_text(col)
    for ch in center_text:
        if ch.strip():
            assert_clean_text(ch)
    assert_clean_text(note)

    im = Image.new("RGB", (width, height), PAPER)
    draw = ImageDraw.Draw(im)
    margin = 80
    draw.rectangle([margin, margin, width - margin, height - margin], outline=INK, width=6)
    draw.rectangle([margin + 16, margin + 16, width - margin - 16, height - margin - 16],
                   outline=INK, width=2)
    center_x = width // 2
    draw.line([center_x - 30, margin + 16, center_x - 30, height - margin - 16], fill=INK, width=2)
    draw.line([center_x + 30, margin + 16, center_x + 30, height - margin - 16], fill=INK, width=2)

    font = _load_font(font_size)
    cols = 16
    col_w = (width - 2 * margin - 100) // cols
    for i in range(1, cols):
        x = margin + 30 + i * col_w
        if abs(x - center_x) > 40:
            draw.line([x, margin + 20, x, height - margin - 20],
                      fill=(178, 160, 140), width=1)

    cy = margin + 90
    for ch in center_text:
        if ch.strip():
            draw.text((center_x - 24, cy), ch, fill=(80, 60, 50), font=font)
        cy += 56

    start_x = width - margin - 130
    for idx, text in enumerate(columns):
        cx = start_x - idx * col_w
        cy = margin + 90
        for ch in text:
            draw.text((cx, cy), ch, fill=(35, 25, 20), font=font)
            cy += col_pitch

    im = _caption_bar(im, note)
    im.save(out_path, optimize=True)
    return out_path.stat().st_size


# --------------------------------------------- 1. 九龙池干涸龙首示意 (VEC-3)
def build_jiulongchi_dry(out_path):
    w, h = 1920, 1080
    im = Image.new("RGB", (w, h), (176, 168, 148))
    draw = ImageDraw.Draw(im)
    for y in range(h):
        t = y / float(h)
        draw.line([0, y, w, y], fill=(int(170 - 26 * t), int(162 - 24 * t), int(146 - 20 * t)))

    # 龙山山体
    draw.polygon([(0, 640), (300, 380), (620, 560), (980, 340), (1360, 560), (1700, 430), (w, 560), (w, 760), (0, 760)],
                 fill=(128, 132, 108))
    # 九龙池干池底（龟裂）
    draw.ellipse([460, 700, 1460, 980], fill=(186, 172, 142))
    draw.ellipse([520, 740, 1400, 950], fill=(198, 184, 154))
    for i in range(9):
        x0 = 560 + i * 96
        draw.arc([x0, 730, x0 + 180, 960], 200, 340, fill=(158, 142, 112), width=3)
    # 池壁石沿
    draw.arc([430, 660, 1490, 1020], 180, 360, fill=(120, 108, 88), width=14)

    # 居中石雕龙首（昂首向天，无水）
    draw.polygon([(860, 420), (1060, 420), (1090, 560), (1040, 660), (880, 660), (830, 560)],
                 fill=(154, 142, 118))
    draw.polygon([(884, 448), (1036, 448), (1058, 556), (1022, 632), (898, 632), (862, 556)],
                 fill=(176, 164, 138))
    # 龙角双枝
    draw.arc([900, 300, 980, 430], 180, 350, fill=(140, 126, 102), width=16)
    draw.arc([940, 300, 1020, 430], 190, 360, fill=(140, 126, 102), width=16)
    # 龙目（圆睁对天）
    draw.ellipse([912, 480, 952, 520], outline=(96, 84, 66), width=5)
    draw.ellipse([968, 480, 1008, 520], outline=(96, 84, 66), width=5)
    # 吻部与须
    draw.arc([900, 540, 1020, 610], 20, 160, fill=(110, 96, 76), width=8)
    draw.arc([850, 560, 930, 700], 260, 350, fill=(120, 106, 84), width=5)
    draw.arc([990, 560, 1070, 700], 190, 280, fill=(120, 106, 84), width=5)
    # 张口中空——无水滴、无水纹
    draw.polygon([(930, 590), (990, 590), (960, 646)], fill=(88, 78, 62))

    im = _caption_bar(
        im,
        "昌平龙山九龙池 · 今日泉眼无自然涌水 · 制作组绘制示意 · 非实物照片",
        "《元史》所记白浮泉源，湮塞确切年代未考得——书证止于延祐已淤、乾隆不可详",
    )
    im.save(out_path, optimize=True)
    return out_path.stat().st_size


# --------------------------------------------- 2. 中统三年六事条书影 (VEC-1)
def build_liushi_folio(out_path):
    return _draw_folio(
        out_path,
        columns=[
            "中統三年",
            "文謙薦守敬習水利",
            "巧思絕人",
            "世祖召見面陳水利",
            "六事其一中都舊漕河",
            "東至通州引玉泉水",
            "以通舟歲可省",
            "雇車錢六萬緡",
        ],
        center_text="元\n史\n\n郭\n守\n敬\n傳",
        note="《元史·郭守敬傳》中統三年條 · 依公開文本排印 · 非原刊掃描",
    )


# --------------------------------------------- 3. 简仪示意 (VEC-3)
def build_jianyi_schematic(out_path):
    w, h = 1920, 1080
    im = Image.new("RGB", (w, h), (222, 216, 200))
    draw = ImageDraw.Draw(im)
    for y in range(h):
        t = y / float(h)
        draw.line([0, y, w, y], fill=(int(214 - 20 * t), int(208 - 18 * t), int(192 - 16 * t)))

    cx, cy = 960, 470
    # 基座
    draw.rectangle([560, 700, 1360, 780], fill=(96, 88, 74))
    draw.rectangle([640, 780, 720, 860], fill=(84, 76, 64))
    draw.rectangle([1200, 780, 1280, 860], fill=(84, 76, 64))
    # 赤道环（大圆，斜置示意）
    draw.ellipse([cx - 300, cy - 210, cx + 300, cy + 210], outline=(70, 62, 52), width=14)
    draw.ellipse([cx - 300, cy - 210, cx + 300, cy + 210], outline=(120, 108, 90), width=4)
    # 四游双环（细）
    draw.ellipse([cx - 240, cy - 168, cx + 240, cy + 168], outline=(58, 70, 88), width=9)
    draw.ellipse([cx - 150, cy - 105, cx + 150, cy + 105], outline=(58, 70, 88), width=7)
    # 窥衡（横指杆）
    draw.line([(cx - 240, cy + 40), (cx + 236, cy - 60)], fill=(150, 62, 40), width=12)
    draw.ellipse([cx + 218, cy - 84, cx + 254, cy - 44], outline=(150, 62, 40), width=8)
    # 百刻环（下侧环带刻度示意）
    draw.arc([cx - 300, cy - 60, cx + 300, cy + 320], 20, 160, fill=(110, 96, 72), width=10)
    for i in range(25):
        ang = 3.14159 * (0.08 + i * 0.035)
        x1 = cx + 290 * __import__("math").cos(ang)
        y1 = cy + 60 + 128 * __import__("math").sin(ang)
        x2 = cx + 290 * __import__("math").cos(ang)
        y2 = cy + 60 + 148 * __import__("math").sin(ang)
        draw.line([(x1, y1), (x2, y2)], fill=(110, 96, 72), width=3)
    # 支柱（龙柱简化）
    draw.polygon([(cx - 60, 700), (cx - 20, 560), (cx + 20, 560), (cx + 60, 700)], fill=(104, 92, 76))

    im = _caption_bar(
        im,
        "簡儀結構示意 · 郭守敬原制不存 · 明正統年間仿制品今存南京紫金山天文台",
        "制作组绘制示意 · 非实物照片 · 环圈比例不作仪器实测依据",
    )
    im.save(out_path, optimize=True)
    return out_path.stat().st_size


# --------------------------------------------- 4. 登封观星台示意 (VEC-3)
def build_guansingtai_schematic(out_path):
    w, h = 1080, 1080
    im = Image.new("RGB", (w, h), (214, 208, 192))
    draw = ImageDraw.Draw(im)
    for y in range(h):
        t = y / float(h)
        draw.line([0, y, w, y], fill=(int(206 - 18 * t), int(200 - 16 * t), int(184 - 14 * t)))

    ground = 900
    draw.rectangle([0, ground, w, h], fill=(150, 146, 122))
    # 台体（梯形，北壁直南壁斜，凹槽通道）
    draw.polygon([(240, ground), (280, 260), (800, 260), (840, ground)], fill=(138, 122, 98))
    draw.polygon([(262, ground), (298, 288), (782, 288), (818, ground)], fill=(158, 142, 116))
    # 凹槽（南北向通道）
    draw.polygon([(498, 288), (582, 288), (582, ground), (498, ground)], fill=(96, 84, 68))
    # 横梁（表端）
    draw.rectangle([430, 236, 650, 262], fill=(88, 76, 60))
    # 圭（向北延伸的石圭，量影）
    draw.rectangle([150, ground - 26, 500, ground + 6], fill=(120, 110, 92))
    for i in range(7):
        draw.line([(170 + i * 46, ground - 26), (170 + i * 46, ground + 6)],
                  fill=(84, 76, 62), width=3)
    # 台阶踏道示意
    for i in range(8):
        yy = ground - 40 - i * 78
        if yy > 300:
            draw.line([(818 - i * 6, yy), (842 - i * 6, yy + 18)], fill=(104, 94, 78), width=6)

    im = _caption_bar(
        im,
        "登封觀星台示意 · 元代遺構 · 二十七所之「河南府陽城」站",
        "制作组绘制示意 · 非实物照片 · 一批国保（一九六一年）· 台体比例不作测绘依据",
    )
    im.save(out_path, optimize=True)
    return out_path.stat().st_size


# --------------------------------------------- 5. 四海测验二十七所示意 (MEC-3)
def build_sihai_27(out_path):
    """按《元史·天文志》全名单的「北極出地」值排布——纯数据轴，非地图投影。

    北极出地为天文志原文数据（太強/少/半等修注按整度示意取位），
    横向位置仅作错行排布，不表示经度。
    """
    w, h = 1920, 1080
    im = Image.new("RGB", (w, h), (247, 242, 228))
    draw = ImageDraw.Draw(im)
    draw.rectangle([60, 60, w - 60, h - 250], outline=(120, 104, 82), width=5)
    _draw_note(draw, "四海測驗 · 二十七所按「北極出地」排布", 100, 96, size=46)
    _draw_note(draw, "依《元史·天文志》全名單 · 恰二十七所 · 制作组示意 · 非地圖投影",
               100, 168, size=30, medium=False, fill=(122, 96, 66))

    # 纬度轴（北極出地 一十五度 至 六十五度）
    axis_x = 260
    top, bot = 300, 760
    draw.line([(axis_x, top - 30), (axis_x, bot + 30)], fill=(96, 84, 66), width=6)
    for deg in (15, 25, 35, 45, 55, 65):
        yy = bot - (deg - 15) / 50.0 * (bot - top)
        draw.line([(axis_x - 14, yy), (axis_x + 14, yy)], fill=(96, 84, 66), width=4)
        _draw_note(draw, ["一十五", "二十五", "三十五", "四十五", "五十五", "六十五"][deg == 15 and 0 or (deg - 15) // 10],
                   axis_x - 118, yy - 20, size=26, medium=False, fill=INK_SOFT)
    _draw_note(draw, "北極出地（度）", axis_x - 96, bot + 56, size=28, medium=False, fill=INK_SOFT)

    # 二十七所（名称, 度示意值, 标签开关）
    stations = [
        ("南海", 15, True), ("瓊州", 19, True), ("雷州", 20, False),
        ("衡嶽", 25, True), ("吉州", 26, False), ("鄂州", 31, False),
        ("成都", 31, False), ("興元", 33, False), ("揚州", 33, False),
        ("安西府", 34, False), ("南京", 34, False), ("河南府陽城", 34, True),
        ("嶽臺", 35, False), ("東平", 35, False), ("大名", 36, False),
        ("益都", 37, False), ("登州", 38, False), ("高麗", 38, False),
        ("太原", 38, False), ("西京", 40, False), ("大都", 40, True),
        ("西涼州", 40, True), ("北京", 42, False), ("上都", 43, True),
        ("和林", 45, True), ("鐵勒", 55, True), ("北海", 65, True),
    ]
    assert len(stations) == 27, "名單必須恰二十七所"
    f_name = _load_font(28, medium=True)
    row = 0
    for name, deg, labeled in stations:
        yy = bot - (deg - 15) / 50.0 * (bot - top)
        xx = axis_x + 60 + (row % 5) * 46 + (row % 2) * 18
        color = VERMILION if labeled else (132, 118, 96)
        draw.ellipse([xx - 9, yy - 9, xx + 9, yy + 9], fill=color)
        draw.line([(axis_x + 4, yy), (xx - 9, yy)], fill=(178, 160, 140), width=2)
        if labeled:
            draw.text((xx + 16, yy - 30), name, fill=(46, 38, 30), font=f_name)
            draw.line([(xx + 4, yy + 8), (xx + 4, yy + 34)], fill=color, width=2)
        row += 1

    # 「河南府陽城」站 ＝ 登封观星台遗构
    yy = bot - (34 - 15) / 50.0 * (bot - top)
    xx = axis_x + 60 + 3 * 46
    draw.rectangle([xx - 14, yy - 160, xx + 14, yy - 108], fill=(138, 122, 98))
    draw.rectangle([xx - 6, yy - 168, xx + 34, yy - 152], fill=(88, 76, 60))
    draw.text((xx + 24, yy - 150), "登封觀星台存", fill=VERMILION, font=_load_font(26, medium=True))

    # 名单之外的「空带」：无西藏/无云南/今海淀无站点
    draw.rectangle([w - 420, 300, w - 120, 560], outline=(150, 62, 40), width=4)
    for i in range(14):
        draw.line([(w - 420, 300 + i * 20), (w - 404, 300 + i * 20)], fill=(150, 62, 40), width=2)
    _draw_note(draw, "名單之外", w - 396, 330, size=40, fill=VERMILION)
    _draw_note(draw, "無西藏站點", w - 396, 400, size=32, medium=False, fill=VERMILION)
    _draw_note(draw, "無雲南站點", w - 396, 452, size=32, medium=False, fill=VERMILION)
    _draw_note(draw, "今海淀境內無一站", w - 396, 504, size=32, medium=False, fill=VERMILION)

    im = _caption_bar(
        im,
        "定點測影站 · 測晷影與北極出地 · 非地理測繪",
        "縱軸為天文志原文數據示意取位；橫向錯行不表示經度 · 制作组示意",
    )
    im.save(out_path, optimize=True)
    return out_path.stat().st_size


# --------------------------------------------- 6. 歲餘条书影 (VEC-1)
def build_suiyu_folio(out_path):
    return _draw_folio(
        out_path,
        columns=[
            "二曰歲餘",
            "自宋大明壬寅年",
            "距至今日八百一十年",
            "每歲合得",
            "三百六十五日",
            "二十四刻二十五分",
            "其二十五分為今曆",
            "歲餘合用之數",
        ],
        center_text="元\n史\n\n授\n時\n曆",
        note="《元史·郭守敬傳》歲餘條 · 依公開文本排印 · 非原刊掃描",
    )


# --------------------------------------------- 7. 白浮泉引水线路示意 (MEC-3)
def build_route_mec3(out_path):
    """纯矢量示意。走向只画《元史》原文给出的拓扑关系（西折而南、經瓮山泊、
    自西水門入城、環匯於積水潭、復東折而南出南水門、東至通州），
    不表示任何真实坐标、比例或渠道形状。"""
    w, h = 1920, 1080
    im = Image.new("RGB", (w, h), (245, 240, 226))
    draw = ImageDraw.Draw(im)
    draw.rectangle([60, 60, w - 60, h - 250], outline=(120, 104, 82), width=5)
    _draw_note(draw, "白浮泉引水線路示意", 100, 92, size=48)
    _draw_note(draw, "依《元史》「西折而南，經瓮山泊，自西水門入城，環匯於積水潭」繪製",
               100, 164, size=30, medium=False, fill=(122, 96, 66))

    f_lab = _load_font(30, medium=True)
    f_small = _load_font(26, medium=False)

    def dot(x, y, r, color):
        assert 0 < x < w and 0 < y < h, "节点越界: (%d,%d)" % (x, y)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=color)

    def label(x, y, text, fill=INK, font=None):
        assert_clean_text(text)
        draw.text((x, y), text, fill=fill, font=font or f_lab)

    # 渠道：西折而南 → 瓮山泊 → 东南下 → 西水门 → 积水潭 → 南水门 → 通州
    channel = [
        (1430, 300),  # 白浮泉（昌平龙山）
        (1300, 330), (1150, 360), (1000, 420), (860, 500),   # 西折
        (760, 560),  # 双塔/榆河/一亩/玉泉 诸泉汇入段
        (640, 600),  # 青龙桥入泊
    ]
    line_color = INDIGO
    for i in range(len(channel) - 1):
        draw.line([channel[i], channel[i + 1]], fill=line_color, width=10)
    # 瓮山泊（先在之湖，工程使水「經」之）
    draw.ellipse([440, 570, 700, 690], outline=line_color, width=8)
    draw.ellipse([468, 592, 672, 668], fill=(188, 208, 216))
    # 瓮山泊 → 长河故道 → 西水门
    seg2 = [(560, 690), (620, 760), (720, 800), (860, 810)]
    for i in range(len(seg2) - 1):
        draw.line([seg2[i], seg2[i + 1]], fill=line_color, width=10)
    # 大都城垣（抽象圆角矩形，仅示意城内汇止）
    draw.rounded_rectangle([860, 640, 1500, 980], radius=26, outline=(130, 108, 80), width=8)
    # 西水门（西墙豁口）
    draw.rectangle([842, 790, 878, 830], fill=(245, 240, 226))
    # 积水潭（城内西北隅汇止）
    draw.ellipse([920, 680, 1240, 830], fill=(188, 208, 216), outline=line_color, width=8)
    # 城内环汇后出南水门东南下
    seg3 = [(1240, 830), (1360, 900), (1480, 950)]
    for i in range(len(seg3) - 1):
        draw.line([seg3[i], seg3[i + 1]], fill=line_color, width=10)
    draw.rectangle([1478, 930, 1512, 972], fill=(245, 240, 226))
    # 通州高丽庄（白河）
    draw.ellipse([1540, 940, 1660, 1010], fill=(188, 208, 216), outline=line_color, width=8)

    # 节点与标注
    dot(1430, 300, 14, VERMILION)
    label(1466, 276, "白浮泉（神山泉）", VERMILION)
    label(1466, 316, "昌平縣界 · 今龙山", INK_SOFT, f_small)
    for px, py, nm in [(1000, 420, "雙塔"), (860, 500, "榆河"), (760, 560, "一畝"), (668, 596, "玉泉")]:
        dot(px, py, 8, (132, 118, 96))
        label(px - 34, py - 44, nm + "諸泉", INK_SOFT, f_small)
    label(430, 700, "瓮山泊", INDIGO)
    label(360, 738, "（今昆明湖故址）", INK_SOFT, f_small)
    label(640, 770, "高梁河故道 · 廣源閘（今紫竹院旁）", INK_SOFT, f_small)
    label(806, 836, "西水門", INK)
    label(1030, 740, "積水潭", INDIGO)
    label(968, 700, "舳艫敝水", (150, 62, 40), f_small)
    label(1470, 900, "南水門", INK)
    label(1560, 1006, "通州高麗莊入白河", INDIGO, f_small)

    im = _caption_bar(
        im,
        "制作组示意 · 非測繪拓撲 · 線路走向與匯止關係依《元史》原文",
        "總長一百六十四里一百四步 · 每十里置一牐 · 首事至元二十九年春告成三十年秋",
    )
    im.save(out_path, optimize=True)
    return out_path.stat().st_size


# --------------------------------------------- 8. 白浮泉引水段书影 (VEC-1)
def build_baifu_folio(out_path):
    return _draw_folio(
        out_path,
        columns=[
            "其一大都運糧河",
            "不用一畝泉舊原",
            "別引北山白浮泉水",
            "西折而南經瓮山泊",
            "自西水門入城",
            "環匯於積水潭",
            "復東折而南出南水門",
            "合入舊運糧河",
        ],
        center_text="元\n史\n\n郭\n守\n敬\n傳",
        note="《元史·郭守敬傳》至元二十八年條 · 依公開文本排印 · 非原刊掃描",
    )


# --------------------------------------------- 9. 延祐元年淤塞条书影 (VEC-1)
def build_yanyou_folio(out_path):
    return _draw_folio(
        out_path,
        columns=[
            "自白浮甕山下至廣源牐",
            "隄隁多淤澱淺塞",
            "源泉微細",
            "不能通流",
            "擬疏滌",
        ],
        center_text="元\n史\n\n河\n渠\n志",
        note="《元史·河渠志》延祐元年條 · 郭守敬卒前兩年 · 依公開文本排印 · 非原刊掃描",
    )


# --------------------------------------------- 10. 衰败链时间轴 (MEC-4, 本集主轴)
def build_decay_chain(out_path):
    w, h = 1920, 1080
    im = Image.new("RGB", (w, h), (247, 242, 228))
    draw = ImageDraw.Draw(im)
    draw.rectangle([60, 60, w - 60, h - 250], outline=(120, 104, 82), width=5)
    _draw_note(draw, "一條渠的衰敗鏈 · 泉死得比人早", 100, 92, size=48)
    _draw_note(draw, "依《元史·河渠志》與乾隆御制文繪製 · 制作组示意",
               100, 164, size=30, medium=False, fill=(122, 96, 66))

    nodes = [
        ("至元三十年", "賜名通惠", "帝過積水潭 · 舳艫敝水", (47, 93, 124)),
        ("大德七年", "山水暴漲", "晝夜雨不止 · 衝決水口", (166, 106, 56)),
        ("大德十一年", "河隄崩壞", "白浮甕山河隄崩三十餘里", (166, 86, 56)),
        ("皇慶元年", "徵工修治", "隄多低薄崩陷 · 總修三十七里", (166, 86, 56)),
        ("延祐元年", "源泉微細", "多淤澱淺塞 · 不能通流", (150, 62, 40)),
        ("乾隆己巳", "時皆湮沒", "御制文自承不可詳", (150, 62, 40)),
        ("今日", "無自然涌泉", "九龍池龍首對天 · 遺址公園", (96, 96, 96)),
    ]
    axis_y = 560
    draw.line([(160, axis_y), (w - 160, axis_y)], fill=(96, 84, 66), width=8)
    slot = (w - 320) / len(nodes)
    f_era = _load_font(30, medium=True)
    f_name = _load_font(38, medium=True)
    f_note = _load_font(24, medium=False)
    for i, (era, name, note, color) in enumerate(nodes):
        cx = 160 + slot * (i + 0.5)
        draw.ellipse([cx - 16, axis_y - 16, cx + 16, axis_y + 16], fill=color)
        draw.line([(cx, axis_y - 16), (cx, axis_y - 96)], fill=(120, 104, 82), width=3)
        if i % 2 == 0:
            draw.text((cx - len(era) * 15, axis_y - 140), era, fill=(90, 76, 58), font=f_era)
            draw.text((cx - len(name) * 20, axis_y + 44), name, fill=color, font=f_name)
            draw.text((cx - len(note) * 11, axis_y + 104), note, fill=(122, 96, 66), font=f_note)
        else:
            draw.text((cx - len(era) * 15, axis_y - 140), era, fill=(90, 76, 58), font=f_era)
            draw.text((cx - len(name) * 20, axis_y - 252), name, fill=color, font=f_name)
            draw.text((cx - len(note) * 11, axis_y - 208), note, fill=(122, 96, 66), font=f_note)
            draw.line([(cx, axis_y + 16), (cx, axis_y + 40)], fill=(120, 104, 82), width=3)

    # 衰败量示意（自左向右走低的水位带）
    for i, frac in enumerate([1.0, 0.82, 0.62, 0.45, 0.22, 0.06, 0.0]):
        x0 = int(160 + slot * i + 8)
        x1 = int(160 + slot * (i + 1) - 8)
        top = int(axis_y + 300 - 210 * frac)
        draw.rectangle([x0, top, x1, axis_y + 300], fill=(188, 208, 216) if frac > 0 else (216, 210, 196))

    im = _caption_bar(
        im,
        "郭守敬卒於延祐三年 · 渠淤於延祐元年——泉死得比人早",
        "「澤被六百年」「至今仍在供水」皆無書證 · 上源已隨歲月湮塞",
    )
    im.save(out_path, optimize=True)
    return out_path.stat().st_size


# --------------------------------------------- main
def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    built = [
        ("jiulongchi_dry_schematic.png", build_jiulongchi_dry, "VEC-3",
         "昌平龙山九龙池干涸龙首示意（制作组绘制，非实物照片）"),
        ("yuanshi_liushi_folio.png", build_liushi_folio, "VEC-1",
         "《元史·郭守敬传》中统三年面陈水利六事条·依公开文本排印，非原刊扫描"),
        ("jianyi_schematic.png", build_jianyi_schematic, "VEC-3",
         "简仪结构示意（原件不存，明仿制品今存南京；制作组绘制，非实物照片）"),
        ("guansingtai_schematic.png", build_guansingtai_schematic, "VEC-3",
         "登封观星台示意（元代遗构·阳城站；制作组绘制，非实物照片）"),
        ("sihai_27_stations_mec3.png", build_sihai_27, "MEC-3",
         "四海测验二十七所按北极出地排布示意（依《元史·天文志》名单；制作组矢量示意，非地图投影）"),
        ("yuanshi_suiyu_folio.png", build_suiyu_folio, "VEC-1",
         "《元史》歲餘条三百六十五日二十四刻二十五分·依公开文本排印，非原刊扫描"),
        ("guoshoujing_route_mec3.png", build_route_mec3, "MEC-3",
         "白浮泉—瓮山泊—积水潭引水线路示意（制作组矢量示意，非测绘拓扑）"),
        ("yuanshi_baifu_folio.png", build_baifu_folio, "VEC-1",
         "《元史·郭守敬传》白浮泉引水段·依公开文本排印，非原刊扫描"),
        ("yuanshi_yanyou_folio.png", build_yanyou_folio, "VEC-1",
         "《元史·河渠志》延祐元年源泉微細不能通流条·依公开文本排印，非原刊扫描"),
        ("guoshoujing_decay_chain_mec4.png", build_decay_chain, "MEC-4",
         "衰败链时间轴：大德七年冲决→延祐元年淤塞→乾隆己巳湮没→今（制作组矢量示意）"),
    ]

    rows = []
    for name, fn, cls, note in built:
        out = OUT_DIR / name
        try:
            size = fn(out)
            rows.append((name, cls, note, str(size), sha256_of(out), "OK"))
            print("OK   %-44s %8d" % (name, size))
        except Exception as exc:
            rows.append((name, cls, note, "-", "-", "FAIL: %s" % exc))
            print("FAIL %-44s %s" % (name, exc))

    with open(OUT_DIR / "sources.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["file", "class", "note", "bytes", "sha256", "status"])
        for r in rows:
            w.writerow(r)

    for name, _, _, _, _, st in rows:
        if st == "OK":
            shutil.copy(OUT_DIR / name, PUBLIC_DIR / name)
    shutil.copy(OUT_DIR / "sources.csv", PUBLIC_DIR / "sources.csv")

    ok = sum(1 for r in rows if r[5] == "OK")
    print("\n=== %d/%d 资产成功 ===" % (ok, len(rows)))
    return rows


if __name__ == "__main__":
    main()
