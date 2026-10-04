#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E28《温泉·「温泉」之前叫「石窝」》Task: 地理切片与视觉资产预处理.

产出 assets/hist_wenquan/ 全套资产并同步 /tmp/chemistry-video/public/wenquan/:

  1. sanshanyuan_xiangshan_roi.png (MEC-1)
     《清 佚名 三山五园图》香山北坡带切片（碧云寺·过街塔·静宜园北坡一线，4000x1400）。
     🔴 图幅经全幅逐段目视核查：绘本北缘止于香山前山带，温泉村（堂子山）不在画内；
     切片作「图幅北界」呈现，画面内不加温泉标注。
  2. beijing_1915_shiwo_roi.png (MEC-2)
     民国四年(1915)《實測京師四郊地圖》温泉村一带切片 (1920x1080)。
     🔴 清晰可辨：『石窝』小型聚落（图幅西缘县界上）、『白』＋疃/灘族复杂字形
     （白家疃村标注，『家』字未获确认）、『杨家村』『黑龙潭』『福山』『界』。
     本幅未见可确读的『溫泉』注记（E27/E28 双方目视裁决一致）；图幅存在
     非线性畸变，与今坐标仅可作趋势比对。
  3. wanshu_zaji_folio.png (VEC-1)
     明·沈榜《宛署杂记》「温泉堂」条书影（万历官书；村名仍书「石窝村」，
     正德甲戌＝正德九年＝一五一四年谷太监建堂，佥都御史陈天祥记）。
  4. dijing_jingwulue_folio.png (VEC-1)
     明·刘侗 于奕正《帝京景物略》(崇祯八年刊,一六三五)「温泉」条书影
     （「泉如湯未至沸時，甃而為池，以待浴者」；东六十里大汤山/小汤山地理锚点）。
  5. caishi_moyai_shiyi.png (VEC-1)
     显龙山（堂子山）明代采石匠题记摩崖示意：洪武二十七年(1394)/正统十年(1445)
     两条纪年——温泉村可证历史最早一手实物。题记字迹为风化刻痕示意，非释文。
  6. shuiliu_yunzai_moyai.png (VEC-1)
     显龙山「水流云在」摩崖示意：英敛之民国二年(1913)正月手书，每字高约一点六米；
     题注逐字「英敛之偕内子淑仲小儿千里游此，偶取杜句寄意，时宣统退位之次年正月也」。
     字体为排印示意，非手迹摹写。
  7. heilongtan_longwangmiao.png (VEC-3)
     黑龙潭龙王庙示意：山门石额「敕建黑龙王庙」（未书年款）＋黄琉璃筒瓦顶（实物在）；
     明成化二十二年(1486)建庙碑·康熙二十年(1681)重建·乾隆三年(1738)封
     「昭灵沛泽龙王之神」。
  8. luanzhou_jinianta.png (VEC-3)
     辛亥滦州起义纪念园纪念塔示意：八角七级密檐式白石塔，通高十二点二米，
     塔台南「精神不死」北「浩气长存」（冯玉祥手书）；一九三七年四月落成，
     第六批全国重点文物保护单位(二〇〇六)。第六批起有编号体系，此处不引编号。
  9. mec3_diming_timeline.png (MEC-3)
     石窝村→温泉村 地名置换时间轴（一三九四—今）：
     万历官书仍书「石窝村」，明末文献已立「温泉」目，改名具体年代无书证（虚线段）。
 10. mec4_quanming_chain.png (MEC-4)
     「泉→堂→山→村→镇」命名链拓扑 ＋ 京西泉名地名群旁注
     （黑龙潭·大汤山·小汤山·玉泉山，均出《帝京景物略》与机构口径）。
 11. sources.csv (sha256/MEC/VEC/版权留痕) + 同步 public/wenquan/

🔴 E23 事故防线（build_1915_roi 内置断言）:
   拼接窗口宽必须 >= ox + crop_w，否则 PIL 黑色补齐，成片右侧纯黑。
   裁切后量化校验右侧 260px 黑像素占比。

🔴 E24/E25 教训: 牌面文字一律全字形汉字，禁 U+3007 圆圈数字；
   公历纪年牌面一律汉字数字（一五一四），不用阿拉伯数字。

🔴 本集红线（研究档案 V-NC 系列）:
   - 不写「辽金帝王驻跸沐浴」（伪引文层）；
   - 不写香水院在温泉后山（《帝京景物略》断碑在妙高峰法云寺）；
   - 不写温泉眼「至今仍在涌流/早已干涸」（未考得，双禁）；
   - 「暖泉」「白家疃温泉」未考得，地名群仅收温泉/黑龙潭/汤山/玉泉山；
   - 实物类资产一律矢量示意，sources.csv 注明「制作组绘制，非实物照片」。

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
OUT_DIR = REPO / "assets" / "hist_wenquan"
PUBLIC_DIR = pathlib.Path("/tmp/chemistry-video/public/wenquan")
CACHE_DIR = pathlib.Path("/tmp/wenquan_cache")
MASTER_MAP = pathlib.Path("/Users/mac/Downloads/清 佚名 三山五园图51x88.tif")

WMTS_TILE_URL = "https://gis.sinica.edu.tw/beijing/file-exists.php?img=Beijing_1915-png-%d-%d-%d"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

# 1915 瓦片窗口（温泉村一带）。🔴 该幅官方实测图无「溫泉」注记：村名作「石窝」，
# 位于今温泉村一带（位置比定为制作组推断，画面标注存疑）；白家疃／黑龙潭／
# 杨家村（今杨家庄）／福山诸注记同幅经目视辨读锁定。北缘 y<24789 服务端 404（图幅边界）。
T19_Z = 16
T19_TX0, T19_TX1 = 53909, 53922
T19_TY0, T19_TY1 = 24789, 24797
T19_OX, T19_OY = 300, 940
CROP_W, CROP_H = 1920, 1080
BLACK_RATIO_MAX = 0.02

# 三山五园图香山北坡带切片窗（碧云寺·过街塔·静宜园北坡一线，
# 经逐段目视辨读标签后固化：全图绘至香山前山带北缘为止，温泉村不在画内）
MEC1_CROP = (5300, 80, 8000, 1025)
MEC1_OUT_W, MEC1_OUT_H = 4000, 1400


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


def _note_bar(im, draw, lines, bar_h=150):
    """底部米色说明条：lines 为 [(text, font_kind)]，kind: t=标题 b=正文 r=强调"""
    w, h = im.size
    bar = Image.new("RGB", (w, bar_h), (247, 240, 223))
    bd = ImageDraw.Draw(bar)
    y = 18
    for text, kind in lines:
        if kind == "t":
            bd.text((60, y), text, fill=(58, 50, 38), font=_load_font(40, medium=True))
            y += 56
        elif kind == "r":
            bd.text((60, y), text, fill=(150, 62, 40), font=_load_font(32, medium=True))
            y += 46
        else:
            bd.text((60, y), text, fill=(122, 96, 66), font=_load_font(30))
            y += 42
    im.paste(bar, (0, h - bar_h))
    return im


# --------------------------------------------- 1. 三山五园图西山前山带切片
def build_sanshanyuan_roi(out_path):
    Image.MAX_IMAGE_PIXELS = None
    im = Image.open(MASTER_MAP)
    roi = im.crop(MEC1_CROP)
    roi = roi.resize((MEC1_OUT_W, MEC1_OUT_H), Image.LANCZOS)
    roi.save(out_path, optimize=True)
    return out_path.stat().st_size


# --------------------------------------------- 2. 1915 实测京师四郊图切片
def build_1915_roi(out_path):
    z = T19_Z
    w = (T19_TX1 - T19_TX0 + 1) * 256
    h = (T19_TY1 - T19_TY0 + 1) * 256

    # 🔴 E23 事故防线：裁切前硬断言
    assert T19_OX + CROP_W <= w, "拼接窗口宽 %d < ox+crop_w=%d（PIL 黑色补齐）" % (w, T19_OX + CROP_W)
    assert T19_OY + CROP_H <= h, "拼接窗口高 %d < oy+crop_h=%d" % (h, T19_OY + CROP_H)

    mosaic = Image.new("RGB", (w, h), (255, 255, 255))

    def fetch(coord):
        tx, ty = coord
        cf = CACHE_DIR / ("tile_1915_wq_%d_%d_%d.png" % (z, tx, ty))
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
                width=1600, height=2200, font_size=34, col_pitch=50):
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
        sy = margin + 62
        sfont = _load_font(34, medium=True)
        for line in seal_text.split("\n"):
            draw.text((width - margin - 222, sy), line, fill=(180, 40, 30), font=sfont)
            sy += 38

    col_top = margin + (280 if seal_text else 80)
    cy = col_top
    for ch in center_text:
        draw.text((center_x - 22, cy), ch, fill=(80, 60, 50), font=font)
        cy += 54

    start_x = width - margin - 120
    for idx, text in enumerate(columns):
        cx = start_x - idx * col_w
        cy = col_top
        for ch in text:
            draw.text((cx, cy), ch, fill=(35, 25, 20), font=font)
            cy += col_pitch

    im.save(out_path, optimize=True)
    return out_path.stat().st_size


# --------------------------------------------- 3. 宛署杂记书影
def build_wanshu_folio(out_path):
    columns = [
        "溫泉堂在石窩村",
        "離城五十里",
        "本村有山曰堂子山",
        "下有溫泉",
        "正德甲戌谷太監建堂於其上因名",
        "右僉都御史陳天祥記",
    ]
    center_text = "宛\n署\n雜\n記"
    return _draw_folio(out_path, paper=(243, 237, 221), border=(54, 38, 26),
                       columns=columns, center_text=center_text, seal_text="明\n官修\n志書")


# --------------------------------------------- 4. 帝京景物略书影
def build_dijing_folio(out_path):
    columns = [
        "山北十里平疇良苗",
        "溫泉出焉",
        "泉如湯未至沸時",
        "甃而為池以待浴者",
        "泉前數武有碧霞殿",
        "單楹板扉",
        "泉而東六十里大湯山",
        "又一溫泉",
        "再東三里小湯山",
        "又一溫泉",
    ]
    center_text = "帝\n京\n景\n物\n略"
    return _draw_folio(out_path, paper=(240, 233, 215), border=(48, 40, 30),
                       columns=columns, center_text=center_text, seal_text="明\n崇禎\n八年\n刊")


# --------------------------------------------- 5. 显龙山明代采石题记摩崖示意
def build_caishi_moyai(out_path):
    w, h = 1920, 1080
    im = Image.new("RGB", (w, h), (86, 78, 68))
    draw = ImageDraw.Draw(im)
    # 崖壁渐变（石灰岩）
    for y in range(h - 150):
        t = y / float(h - 150)
        draw.line([0, y, w, y], fill=(int(96 + 42 * t), int(88 + 38 * t), int(76 + 30 * t)))

    import math
    rnd = 12345
    def nrand(n):
        nonlocal rnd
        rnd = (rnd * 1103515245 + 12345) % (1 << 31)
        return rnd % n

    # 岩面竖向凿痕纹理
    for i in range(260):
        x = nrand(w)
        y0 = nrand(h - 260)
        ln = 20 + nrand(70)
        shade = 70 + nrand(36)
        draw.line([(x, y0), (x + nrand(7) - 3, y0 + ln)], fill=(shade, shade - 6, shade - 14), width=2)

    # 两方题记刻痕区（石壁左侧与右下，均为抽象刻痕，非释文）
    def scar_area(x0, y0, cw, ch, cols, rows):
        draw.rectangle([x0 - 14, y0 - 14, x0 + cw + 14, y0 + ch + 14],
                       outline=(60, 52, 44), width=3)
        for r in range(rows):
            cy = y0 + 18 + r * ((ch - 24) // max(rows - 1, 1))
            cx = x0
            while cx < x0 + cw - 26:
                seg = 16 + nrand(20)
                draw.line([(cx, cy + nrand(6)), (cx + seg, cy + nrand(6) - 3)],
                          fill=(52, 44, 38), width=3)
                cx += seg + 6 + nrand(10)

    scar_area(180, 240, 560, 380, 6, 7)    # 洪武二十七年题记位
    scar_area(1010, 520, 620, 360, 7, 6)   # 正统十年题记位

    # 纪年标牌（画面事实，非刻文内容）
    def tag(x, y, text):
        tw = len(text) * 26 + 44
        draw.rectangle([x, y, x + tw, y + 58], fill=(247, 240, 223), outline=(120, 100, 80), width=2)
        draw.text((x + 22, y + 12), text, fill=(70, 54, 40), font=_load_font(30, medium=True))

    tag(180, 132, "明洪武二十七年（一三九四）匠人题记位")
    tag(1010, 442, "明正统十年（一四四五）匠人题记位")

    _note_bar(im, draw, [
        ("显龙山（堂子山）摩崖明代采石题记 · 示意", "t"),
        ("温泉村可证历史的最早一手实物：两条纪年相隔五十一年，采石跨明代前中期持续进行", "b"),
        ("刻痕为风化示意，非题记释文 · 制作组绘制，非实物照片", "r"),
    ], bar_h=150)
    im.save(out_path, optimize=True)
    return out_path.stat().st_size


# --------------------------------------------- 6. 「水流云在」摩崖示意
def build_shuiliu_yunzai(out_path):
    w, h = 1920, 1080
    im = Image.new("RGB", (w, h), (82, 76, 66))
    draw = ImageDraw.Draw(im)
    # 崖壁
    for y in range(h - 170):
        t = y / float(h - 170)
        draw.line([0, y, w, y], fill=(int(92 + 46 * t), int(86 + 40 * t), int(74 + 32 * t)))
    import random
    rnd = random.Random(2026)
    for i in range(240):
        x = rnd.randrange(w)
        y0 = rnd.randrange(h - 300)
        ln = 18 + rnd.randrange(60)
        shade = 66 + rnd.randrange(40)
        draw.line([(x, y0), (x + rnd.randrange(7) - 3, y0 + ln)],
                  fill=(shade, shade - 6, shade - 14), width=2)

    # 「水流云在」四字（每字高约一点六米之实景尺度，排印示意）
    big = _load_font(210, medium=True)
    x = 300
    for ch in "水流云在":
        draw.text((x, 210), ch, fill=(232, 224, 208), font=big)
        # 刻边阴影
        draw.text((x + 5, 215), ch, outline=(70, 62, 52), font=big)
        x += 330

    # 题注小字（逐字）
    note_font = _load_font(30)
    note = "英斂之偕內子淑仲小兒千里遊此偶取杜句寄意時宣統退位之次年正月也"
    draw.text((300, 620), note, fill=(206, 196, 178), font=note_font)

    _note_bar(im, draw, [
        ("显龙山「水流云在」摩崖 · 示意", "t"),
        ("英敛之民国二年（一九一三）正月手书，每字高约一点六米；取杜甫《江亭》句意", "b"),
        ("字体为排印示意，非手迹摹写 · 制作组绘制，非实物照片", "r"),
    ], bar_h=170)
    im.save(out_path, optimize=True)
    return out_path.stat().st_size


# --------------------------------------------- 7. 黑龙潭龙王庙示意
def build_heilongtan_miao(out_path):
    w, h = 1920, 1080
    im = Image.new("RGB", (w, h), (196, 208, 216))
    draw = ImageDraw.Draw(im)
    for y in range(420):
        t = y / 420.0
        draw.line([0, y, w, y], fill=(int(190 - 30 * t), int(206 - 26 * t), int(222 - 24 * t)))
    # 远山（画眉山一带）
    draw.polygon([(0, 420), (360, 260), (720, 380), (1150, 240), (1520, 360), (w, 290), (w, 440)],
                 fill=(158, 172, 160))
    # 地面
    draw.rectangle([0, 800, w, h], fill=(172, 176, 152))
    draw.rectangle([0, 880, w, h], fill=(158, 162, 140))

    # 山门（黄琉璃瓦顶——实物在）
    draw.rectangle([620, 520, 1300, 820], fill=(178, 128, 108), outline=(110, 76, 60), width=4)
    # 黄琉璃瓦庑殿顶
    draw.polygon([(560, 520), (760, 430), (1160, 430), (1360, 520)], fill=(226, 178, 62))
    draw.polygon([(560, 520), (760, 430), (1160, 430), (1360, 520)], outline=(158, 118, 40), width=5)
    for gx in range(720, 1140, 46):
        draw.arc([gx, 436, gx + 46, 486], 200, 340, fill=(206, 156, 48), width=3)
    # 门簪与朱门
    for dx in (880, 1040):
        draw.rectangle([dx, 640, dx + 60, 820], fill=(122, 58, 44))
        draw.rectangle([dx + 8, 652, dx + 52, 812], fill=(146, 72, 54), outline=(96, 46, 36), width=2)
    # 石门额「敕建黑龙王庙」（未书年款）
    draw.rectangle([700, 540, 1220, 616], fill=(206, 200, 188), outline=(120, 110, 96), width=4)
    shie_font = _load_font(56, medium=True)
    cx = 960
    for ch in "敕建黑龙王庙":
        draw.text((cx - 210, 552), ch, fill=(58, 48, 40), font=shie_font)
        cx += 70

    # 潭（前景冷泉水面，居左避让山门）
    draw.ellipse([60, 770, 560, 884], fill=(96, 130, 142))
    draw.ellipse([120, 788, 500, 872], fill=(112, 148, 158))

    _note_bar(im, draw, [
        ("黑龙潭龙王庙 · 示意（海淀区温泉镇画眉山一带）", "t"),
        ("山门石额「敕建黑龙王庙」未书年款；殿顶黄琉璃筒瓦（实物在）", "b"),
        ("成化二十二年（一四八六）建庙碑 · 康熙二十年（一六八一）重建 · 乾隆三年（一七三八）封昭灵沛泽龙王之神", "b"),
        ("祈雨属冷泉龙神，与温泉汤池分属两泉两庙 · 制作组绘制，非实物照片", "r"),
    ], bar_h=190)
    im.save(out_path, optimize=True)
    return out_path.stat().st_size


# --------------------------------------------- 8. 滦州起义纪念塔示意
def build_luanzhou_tower(out_path):
    w, h = 1920, 1080
    im = Image.new("RGB", (w, h), (198, 210, 220))
    draw = ImageDraw.Draw(im)
    for y in range(400):
        t = y / 400.0
        draw.line([0, y, w, y], fill=(int(192 - 30 * t), int(208 - 26 * t), int(224 - 24 * t)))
    # 显龙山远影
    draw.polygon([(0, 400), (500, 250), (980, 370), (1500, 240), (w, 330), (w, 430)], fill=(160, 174, 164))
    draw.rectangle([0, 830, w, h], fill=(174, 178, 154))

    # 八角七级密檐式白石塔（通高十二点二米）
    cx = 860
    base_y = 880
    draw.rectangle([cx - 190, base_y - 36, cx + 190, base_y], fill=(188, 184, 172))
    # 塔台两级
    draw.rectangle([cx - 160, base_y - 66, cx + 160, base_y - 36], fill=(206, 202, 190))
    draw.rectangle([cx - 130, base_y - 92, cx + 130, base_y - 66], fill=(216, 212, 200))
    # 塔身与密檐：七级收分
    top_y = base_y - 92
    level_h = 74
    for lv in range(7):
        half = 108 - lv * 11
        body_top = top_y - level_h
        draw.polygon([(cx - half, top_y), (cx - int(half * 0.86), body_top),
                      (cx + int(half * 0.86), body_top), (cx + half, top_y)],
                     fill=(228, 224, 212))
        # 塔身二方连续栏额
        draw.rectangle([cx - int(half * 0.86), body_top + 18, cx + int(half * 0.86), body_top + 30],
                       fill=(198, 192, 178))
        # 密檐（八角出檐，双线）
        eave = half + 26
        draw.polygon([(cx - eave, body_top), (cx, body_top - 26), (cx + eave, body_top)],
                     fill=(214, 208, 194), outline=(150, 142, 126), width=3)
        top_y = body_top - 26
    # 塔刹（鎏金）
    draw.line([(cx, top_y), (cx, top_y - 56)], fill=(196, 156, 60), width=8)
    draw.ellipse([cx - 18, top_y - 92, cx + 18, top_y - 56], fill=(214, 172, 66))
    draw.ellipse([cx - 9, top_y - 74, cx + 9, top_y - 58], fill=(238, 204, 108))

    # 塔台题字（南「精神不死」北「浩气长存」，冯玉祥手书；此处排印示意）
    draw.text((cx - 190, base_y - 62), "精神不死", fill=(90, 66, 52), font=_load_font(34, medium=True))
    draw.text((cx + 40, base_y - 62), "浩气长存", fill=(90, 66, 52), font=_load_font(34, medium=True))

    # 侧注碑位（纪念碑与衣冠冢石幢一字排开）
    draw.rectangle([1430, 780, 1500, 884], fill=(202, 198, 186), outline=(150, 142, 126), width=3)
    draw.polygon([(1420, 780), (1465, 740), (1510, 780)], fill=(212, 206, 192), outline=(150, 142, 126), width=3)
    draw.rectangle([330, 820, 372, 884], fill=(198, 194, 182), outline=(150, 142, 126), width=3)
    draw.polygon([(322, 820), (351, 792), (380, 820)], fill=(208, 202, 188), outline=(150, 142, 126), width=3)

    _note_bar(im, draw, [
        ("辛亥滦州起义纪念园纪念塔 · 示意（显龙山南麓，今北京老年医院内）", "t"),
        ("八角七级密檐式白石塔，通高十二点二米；塔台南「精神不死」北「浩气长存」（冯玉祥手书）", "b"),
        ("一九三七年四月落成；纪念一九一二年滦州起义殉难之王金铭、施从云、白雅雨诸先烈", "b"),
        ("第六批全国重点文物保护单位（二〇〇六年公布）· 制作组绘制，非实物照片", "r"),
    ], bar_h=190)
    im.save(out_path, optimize=True)
    return out_path.stat().st_size


# --------------------------------------------- 9. MEC-3 地名置换时间轴
def build_diming_timeline(out_path):
    w, h = 1920, 1080
    im = Image.new("RGB", (w, h), (247, 242, 228))
    draw = ImageDraw.Draw(im)
    draw.rectangle([60, 60, w - 60, h - 60], outline=(120, 104, 82), width=5)
    draw.text((100, 100), "石窝村 → 温泉村 · 地名置换时间轴", fill=(52, 44, 34), font=_load_font(52, medium=True))
    draw.text((100, 176), "万历官书仍书「石窝村」，明末文献已立「温泉」目；改名具体年代无书证（虚线段）（制作组示意）",
              fill=(122, 96, 66), font=_load_font(30))

    axis_y = 560
    draw.line([(160, axis_y), (w - 160, axis_y)], fill=(96, 84, 66), width=8)

    nodes = [
        ("明洪武二十七年", "采石匠题记", "一三九四 · 一手实物"),
        ("明正统十年", "采石匠题记", "一四四五 · 一手实物"),
        ("明正德九年", "谷太监建温泉堂", "一五一四 · 泉名成堂名"),
        ("明万历年间", "《宛署杂记》", "村名仍书「石窝村」"),
        ("明崇祯八年", "《帝京景物略》", "一六三五 · 已立「温泉」目"),
        ("今", "温泉村 · 温泉镇", "泉名→堂名→村名→镇名"),
    ]
    # 无书证虚线段：介于万历成书与崇祯八年之间
    seg_i = 4  # nodes[4] 之前（即 3→4 段）
    slot = (w - 320) / len(nodes)
    f_era = _load_font(26)
    f_name = _load_font(38, medium=True)
    f_note = _load_font(22)

    for i, (era, name, note) in enumerate(nodes):
        cx = 160 + slot * (i + 0.5)
        is_key = i in (3, 4)
        draw.ellipse([cx - 16, axis_y - 16, cx + 16, axis_y + 16],
                     fill=(150, 62, 40) if is_key else (96, 84, 66))
        draw.line([(cx, axis_y - 16), (cx, axis_y - 90)], fill=(120, 104, 82), width=3)
        draw.text((cx - len(era) * 13, axis_y - 128), era, fill=(90, 76, 58), font=f_era)
        if i % 2 == 0:
            draw.text((cx - len(name) * 20, axis_y + 40), name, fill=(46, 38, 30), font=f_name)
            draw.text((cx - len(note) * 11, axis_y + 96), note, fill=(122, 96, 66), font=f_note)
        else:
            draw.text((cx - len(name) * 20, axis_y - 252), name, fill=(46, 38, 30), font=f_name)
            draw.text((cx - len(note) * 11, axis_y - 210), note, fill=(122, 96, 66), font=f_note)
            draw.line([(cx, axis_y + 16), (cx, axis_y + 40)], fill=(120, 104, 82), width=3)

    # 改名无书证虚线段高亮
    x_a = 160 + slot * 3.5
    x_b = 160 + slot * 4.5
    for dash_x in range(int(x_a), int(x_b), 26):
        draw.line([(dash_x, axis_y - 12), (dash_x + 14, axis_y + 12)], fill=(180, 60, 46), width=6)
    draw.text((x_a + 24, axis_y + 150), "改称「温泉」具体年代：无直接书证",
              fill=(180, 60, 46), font=_load_font(34, medium=True))

    draw.text((100, h - 130), "石窝＝采石场之名 · 温泉＝泉之名 · 一个水的名字，活过了一口水",
              fill=(150, 62, 40), font=_load_font(32, medium=True))

    im.save(out_path, optimize=True)
    return out_path.stat().st_size


# --------------------------------------------- 10. MEC-4 命名链拓扑与泉名地名群
def build_quanming_chain(out_path):
    w, h = 1920, 1080
    im = Image.new("RGB", (w, h), (240, 234, 218))
    draw = ImageDraw.Draw(im)
    draw.rectangle([60, 60, w - 60, h - 60], outline=(120, 104, 82), width=5)
    draw.text((100, 96), "泉 → 堂 → 山 → 村 → 镇 · 一口泉的名字如何层层落户",
              fill=(52, 44, 34), font=_load_font(46, medium=True))
    draw.text((100, 160), "制作组示意 · 非测绘拓扑 · 地名群仅收考得诸名",
              fill=(122, 96, 66), font=_load_font(28))

    chain = [
        ("泉", "温泉", "山下温泉出露（《宛署杂记》「下有温泉」）"),
        ("堂", "温泉堂", "正德九年（一五一四）谷太监建于堂子山上"),
        ("山", "堂子山", "山因堂得名（通行考释，存疑）；今名显龙山"),
        ("村", "温泉村", "明末文献已用；此前官书作「石窝村」"),
        ("镇", "温泉镇", "今海淀区温泉镇，下辖七行政村"),
    ]
    card_w, card_h, gap = 310, 430, 40
    x0, y0 = 110, 270
    for i, (zi, name, note) in enumerate(chain):
        x = x0 + i * (card_w + gap)
        color = (150, 62, 40) if i in (0, 4) else (96, 104, 84)
        draw.rectangle([x, y0, x + card_w, y0 + card_h], fill=(250, 246, 234), outline=color, width=6)
        draw.rectangle([x, y0, x + card_w, y0 + 92], fill=color)
        draw.text((x + card_w // 2 - 26, y0 + 12), zi, fill=(250, 246, 234), font=_load_font(58, medium=True))
        draw.text((x + 30, y0 + 120), name, fill=(46, 38, 30), font=_load_font(44, medium=True))
        # 竖排注
        cy = y0 + 190
        f_s = _load_font(24)
        for line in _wrap(note, 9):
            draw.text((x + 30, cy), line, fill=(110, 92, 70), font=f_s)
            cy += 34
        if i < len(chain) - 1:
            ax = x + card_w + gap // 2
            draw.polygon([(ax - 12, y0 + card_h // 2 - 18), (ax + 12, y0 + card_h // 2),
                          (ax - 12, y0 + card_h // 2 + 18)], fill=(120, 104, 82))

    # 右下：京西泉名地名群
    gy = h - 240
    draw.text((110, gy), "京西泉名地名群（《帝京景物略》与机构口径）：温泉（温）· 黑龙潭（冷泉祈雨）· 大汤山／小汤山（汤）· 玉泉山（玉）",
              fill=(90, 76, 58), font=_load_font(28, medium=True))
    draw.text((110, gy + 46), "「暖泉」「白家疃温泉」未考得，不入图；香水院在妙高峰法云寺，与温泉无涉",
              fill=(150, 62, 40), font=_load_font(26))

    im.save(out_path, optimize=True)
    return out_path.stat().st_size


def _wrap(text, n):
    lines = [text[i:i + n] for i in range(0, len(text), n)]
    out = []
    for ln in lines:
        if out and ln and ln[0] in "，。；：、）」』？！":
            out[-1] += ln[0]
            ln = ln[1:]
        out.append(ln)
    return [l for l in out if l]


# --------------------------------------------- main
def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    built = [
        ("sanshanyuan_xiangshan_roi.png", build_sanshanyuan_roi, "MEC-1",
         "《清 佚名 三山五园图》香山北坡带切片（公有领域）：碧云寺·过街塔·静宜园北坡一线，即该图幅所绘北界；温泉村在图幅之外，画面不加温泉标注"),
        ("beijing_1915_shiwo_roi.png", build_1915_roi, "MEC-2",
         "民国四年(1915)《實測京師四郊地圖》温泉村一带切片（公有领域）。清晰可辨注记：『石窝』（小型聚落，图幅西缘县界上）、『白』＋疃/灘族复杂字形（白家疃村标注，『家』字未获确认）、『杨家村』『黑龙潭』（附庙宇符号）『福山』及昌平『界』。本幅未见可确读的『溫泉』注记；图幅存在非线性畸变，与今坐标仅可作趋势比对，不作点位断言"),
        ("wanshu_zaji_folio.png", build_wanshu_folio, "VEC-1",
         "明·沈榜《宛署杂记》「温泉堂」条书影示意（依据公开文本排印，非原刊扫描）"),
        ("dijing_jingwulue_folio.png", build_dijing_folio, "VEC-1",
         "明·刘侗 于奕正《帝京景物略》「温泉」条书影示意（依据公开文本排印，非原刊扫描）"),
        ("caishi_moyai_shiyi.png", build_caishi_moyai, "VEC-1",
         "显龙山明代采石题记摩崖示意（制作组绘制，非实物照片；刻痕非释文）"),
        ("shuiliu_yunzai_moyai.png", build_shuiliu_yunzai, "VEC-1",
         "「水流云在」摩崖示意（制作组绘制，非实物照片；字体排印非手迹）"),
        ("heilongtan_longwangmiao.png", build_heilongtan_miao, "VEC-3",
         "黑龙潭龙王庙示意（制作组绘制，非实物照片）"),
        ("luanzhou_jinianta.png", build_luanzhou_tower, "VEC-3",
         "辛亥滦州起义纪念园纪念塔示意（制作组绘制，非实物照片）"),
        ("mec3_diming_timeline.png", build_diming_timeline, "MEC-3",
         "石窝村→温泉村地名置换时间轴（制作组矢量示意）"),
        ("mec4_quanming_chain.png", build_quanming_chain, "MEC-4",
         "泉→堂→山→村→镇命名链拓扑（制作组示意 · 非测绘拓扑）"),
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
        wtr = csv.writer(f)
        wtr.writerow(["file", "class", "note", "bytes", "sha256", "status"])
        for r in rows:
            wtr.writerow(r)

    for name, _, _, _, _, st in rows:
        if st == "OK":
            shutil.copy(OUT_DIR / name, PUBLIC_DIR / name)

    ok = sum(1 for r in rows if r[5] == "OK")
    print("\n=== %d/%d 资产成功 ===" % (ok, len(rows)))
    return rows


if __name__ == "__main__":
    main()
