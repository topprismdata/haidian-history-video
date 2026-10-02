#!/usr/bin/env python3
"""
CCVG 本地倒排索引构建器（Contemporary Chinese Village Gazetteer Data）
=====================================================================

把匹兹堡大学图书馆《当代中国村庄数据》(CCVG) 的两个离线原始文件
  1. Gazetteer_Information_村志信息.csv   —— 2,601 个行政村的村志主表
     （D-Scholarship 37663，d-scholarship.pitt.edu/downloads/9d3a3109-…）
  2. ccvg_villages_map.kmz                —— 官方交互地图的 KML 导出（2,599 个村点，
     含村名汉字、省/市/县、经纬度，经「村志代码」与主表连接）
合成单一倒排索引 ccvg_index.json：
  键 = 村名简体 / 繁体（保守映射）/ 拼音（小写）/ 去通名核心名 → 村志代码列表
  值 = 行记录（村名、省份、坐标等字段映射见 meta.field_map）

原始大文件不入库（本目录 .gitignore）；入库的只有
ccvg_index.json、metadata.json 与本脚本。

用法（在本目录下）:
    python3 build_index.py
若原始文件缺失，脚本打印人工获取步骤并以退出码 2 中止。
"""

import csv
import datetime
import hashlib
import io
import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

HERE = Path(__file__).resolve().parent

CSV_NAME = "Gazetteer_Information_村志信息.csv"
KMZ_NAME = "ccvg_villages_map.kmz"
INDEX_NAME = "ccvg_index.json"
META_NAME = "metadata.json"

SOURCE_CSV_URL = (
    "https://d-scholarship.pitt.edu/downloads/"
    "9d3a3109-788c-4ee7-a6b3-13f60092e09e?locale=en"
)
SOURCE_KMZ_URL = (
    "https://www.google.com/maps/d/kml"
    "?mid=1lP6spRZf8YR_Kgel5AeGxMQ4zZ5hMK0&force=lite"
)
ITEM_URL = "https://d-scholarship.pitt.edu/37663/"

MANUAL_STEPS = (
    "人工获取步骤：\n"
    "  1. 浏览器打开 https://www.chinesevillagedata.library.pitt.edu/datasets.html\n"
    "  2. 进入 Pitt D-Scholarship 条目 https://d-scholarship.pitt.edu/37663/\n"
    "  3. 下载文件 37663_Gazetteer_Information_村志信息.csv，"
    "重命名为 %s 放入本目录\n"
    "  4. 另存地图 KMZ：%s，重命名为 %s 放入本目录\n"
    "  注：/downloads/ 端点有 Cloudflare 校验，curl 需带浏览器 User-Agent，"
    "偶发 403 时隔几分钟重试。\n" % (CSV_NAME, SOURCE_KMZ_URL, KMZ_NAME)
)

# ---------------------------------------------------------------------------
# 简体 → 繁体（保守单字映射：只收村名常见且繁简一一对应的字；
# 歧义字（谷/里/松/后/冲等）不收，原样保留简体，宁缺毋错。
# 与 expansion.py 的 _TRAD_TO_SIMP 方向互补但独立：本表服务全国村名，
# 不依赖该模块的私有海淀语料子集。
# ---------------------------------------------------------------------------
_S2T = {
    # 方位/数量/政区
    "东": "東", "万": "萬", "两": "兩", "县": "縣", "区": "區", "镇": "鎮",
    "乡": "鄉", "广": "廣", "庆": "慶", "应": "應", "怀": "懷", "总": "總",
    "国": "國", "会": "會", "党": "黨", "军": "軍", "农": "農", "务": "務",
    "卫": "衛", "医": "醫", "汉": "漢", "壮": "壯", "华": "華",
    # 聚落/水陆通名
    "庄": "莊", "营": "營", "铺": "鋪", "驿": "驛", "门": "門", "关": "關",
    "头": "頭", "桥": "橋", "坝": "壩", "沟": "溝", "湾": "灣", "滩": "灘",
    "涧": "澗", "洼": "窪", "泽": "澤", "涝": "澇", "碱": "鹼", "泾": "涇",
    "洁": "潔", "济": "濟", "浑": "渾", "温": "溫", "满": "滿", "滦": "灤",
    "渊": "淵", "岛": "島", "屿": "嶼", "场": "場", "厂": "廠", "墙": "牆",
    "栏": "欄", "栅": "柵", "楼": "樓", "台": "臺", "阁": "閣", "庙": "廟",
    "观": "觀", "坟": "墳", "窑": "窯", "炉": "爐", "园": "園", "厅": "廳",
    # 动植物/物产
    "树": "樹", "枣": "棗", "芦": "蘆", "苇": "葦", "莲": "蓮", "兰": "蘭",
    "麦": "麥", "粮": "糧", "盐": "鹽", "烟": "煙", "铁": "鐵", "铜": "銅",
    "银": "銀", "锡": "錫", "钢": "鋼", "砖": "磚", "猪": "豬", "鹅": "鵝",
    "鸡": "雞", "鸭": "鴨", "鱼": "魚", "虾": "蝦", "鹰": "鷹", "鹤": "鶴",
    "鸦": "鴉", "鹊": "鵲", "蝉": "蟬", "驴": "驢", "骡": "騾", "骆": "駱",
    "驼": "駝", "鹏": "鵬", "鸟": "鳥", "鸠": "鳩", "鸥": "鷗", "莺": "鶯",
    "龙": "龍", "凤": "鳳", "渔": "漁", "猎": "獵",
    # 德祥字
    "义": "義", "礼": "禮", "禄": "祿", "寿": "壽", "宁": "寧", "顺": "順",
    "兴": "興", "贵": "貴", "荣": "榮", "旧": "舊", "乐": "樂", "爱": "愛",
    "双": "雙", "对": "對", "号": "號", "丰": "豐", "临": "臨", "觉": "覺",
    # 常见姓氏
    "刘": "劉", "陈": "陳", "张": "張", "杨": "楊", "黄": "黃", "赵": "趙",
    "钱": "錢", "孙": "孫", "马": "馬", "吴": "吳", "罗": "羅", "郑": "鄭",
    "谢": "謝", "许": "許", "韩": "韓", "冯": "馮", "邓": "鄧", "吕": "呂",
    "苏": "蘇", "卢": "盧", "蒋": "蔣", "贾": "賈", "叶": "葉", "阎": "閻",
    "钟": "鍾", "谭": "譚", "邹": "鄒", "陆": "陸", "顾": "顧", "汤": "湯",
    "乔": "喬", "贺": "賀", "赖": "賴", "龚": "龔", "萧": "蕭", "蓝": "藍",
    "欧": "歐", "韦": "韋", "闵": "閔", "简": "簡", "綦": "綦",
    # 动词/抽象字
    "长": "長", "边": "邊", "达": "達", "运": "運", "进": "進", "远": "遠",
    "连": "連", "迟": "遲", "适": "適", "选": "選", "逊": "遜", "遗": "遺",
    "归": "歸", "当": "當", "层": "層", "无": "無", "为": "為", "与": "與",
    "语": "語", "说": "說", "读": "讀", "书": "書", "学": "學", "试": "試",
    "验": "驗", "报": "報", "训": "訓", "练": "練", "师": "師", "专": "專",
    "术": "術", "艺": "藝", "药": "藥", "护": "護", "产": "產", "业": "業",
    "标": "標", "准": "準", "备": "備", "联": "聯", "队": "隊", "组": "組",
    "众": "眾", "户": "戶", "红": "紅", "绿": "綠", "纪": "紀", "绍": "紹",
    "经": "經", "贸": "貿", "馆": "館", "车": "車", "机": "機", "电": "電",
    "网": "網", "线": "線", "盘": "盤", "盖": "蓋", "环": "環", "灯": "燈",
    "热": "熱", "数": "數", "敌": "敵", "断": "斷", "稳": "穩", "穷": "窮",
    "窦": "竇", "笋": "筍", "盖": "蓋", "廍": "廍", "廪": "廩",
}

_S2T_REVERSE = None  # 惰性构建：{繁: 簡}


def s2t(text: str) -> str:
    """简体→繁体逐字映射；未收录字符原样保留（繁简同形占多数）。"""
    return "".join(_S2T.get(ch, ch) for ch in text)


def t2s(text: str) -> str:
    """繁体→简体（同一张表的逆向）；查询端归一到简体规范键。"""
    global _S2T_REVERSE
    if _S2T_REVERSE is None:
        _S2T_REVERSE = {}
        for simp, trad in _S2T.items():
            _S2T_REVERSE.setdefault(trad, simp)
    return "".join(_S2T_REVERSE.get(ch, ch) for ch in text)


# ---------------------------------------------------------------------------
# CSV 主表解析
# ---------------------------------------------------------------------------

def _csv_field(header: str) -> Optional[str]:
    if header.startswith("村志代码"):
        return "code_raw"
    if header.startswith("村志书名"):
        return "gazetteer_title"
    if header.startswith("书名"):
        return "gazetteer_title_pinyin"
    if header.startswith("出版年"):
        return "pub_year"
    if header.startswith("出版类型"):
        return "pub_type"
    return None


def normalize_code(raw: str) -> str:
    """连接键归一：'0029' 与 '29' 归并为 '29'。"""
    raw = (raw or "").strip()
    return str(int(raw)) if raw.isdigit() else raw


def load_gazetteer_csv(path: Path) -> List[Dict]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        headers = next(reader)
        fields = [_csv_field(h) for h in headers]
        rows = []
        for vals in reader:
            if not any(vals):
                continue
            row = {}
            for field, val in zip(fields, vals):
                if field:
                    row[field] = val.strip()
            row["code"] = normalize_code(row.get("code_raw", ""))
            rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# KMZ（KML）村点解析
# ---------------------------------------------------------------------------

def _classify_extdata(name: str) -> Optional[str]:
    if name.startswith("村志代码"):
        return "code_map"
    if name.startswith("村名"):
        return "village_name_cn"
    if name.startswith("村庄代码"):
        return "village_code"
    if name.startswith("省"):
        return "province_raw"
    if name.startswith("市 - 汉语拼音"):
        return "city_pinyin"
    if name.startswith("市"):
        return "city_cn"
    if name.startswith("县"):
        return "county_pinyin" if "拼音" in name else "county_cn"
    if name.startswith("经纬度"):
        return "coords"
    return None


def _na(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    return None if value.lower() in ("", "n/a", "na") else value


def _folder_region(parents: Dict, placemark) -> Optional[str]:
    node = parents.get(placemark)
    while node is not None:
        if node.tag.endswith("}Folder") and node.findtext("{*}name"):
            return node.findtext("{*}name").strip()
        node = parents.get(node)
    return None


def parse_kml_placemarks(kml_bytes: bytes) -> List[Dict]:
    root = ET.fromstring(kml_bytes)
    parents = {c: p for p in root.iter() for c in p}
    villages = []
    for pm in root.findall(".//{*}Placemark"):
        v: Dict = {}
        for data in pm.findall("{*}ExtendedData/{*}Data"):
            key = _classify_extdata(data.get("name") or "")
            if key:
                v[key] = _na(data.findtext("{*}value"))
        # 坐标优先取 ExtendedData「经纬度」，退回 Point/coordinates
        lonlat = None
        if v.get("coords"):
            lonlat = v.pop("coords")
        else:
            point = pm.findtext("{*}Point/{*}coordinates")
            if point:
                lonlat = point.strip().split()[0]
        if lonlat:
            m = re.match(r"\s*([-\d.]+)\s*,\s*([-\d.]+)", lonlat)
            if m:
                v["coords"] = [float(m.group(1)), float(m.group(2))]
        v["village_name_pinyin"] = _na(pm.findtext("{*}name"))
        v["region"] = _folder_region(parents, pm)
        v["code"] = normalize_code(v.get("code_map", ""))
        villages.append(v)
    return villages


def load_villages_kmz(path: Path) -> List[Dict]:
    with zipfile.ZipFile(path) as zf:
        kml_name = next(n for n in zf.namelist() if n.endswith(".kml"))
        return parse_kml_placemarks(zf.read(kml_name))


# ---------------------------------------------------------------------------
# 索引构建
# ---------------------------------------------------------------------------

def _split_cn_pinyin(raw: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """'陕西省 Shanxi Sheng' → ('陕西省', 'Shanxi Sheng')"""
    if not raw:
        return None, None
    parts = raw.strip().split(None, 1)
    return parts[0], (parts[1].strip() if len(parts) > 1 else None)


def strip_toponym_suffix(name: str) -> str:
    """去通名核心：'太平店村志'→'太平店'，'刘国忠村'→'刘国忠'（保底长度 2）。"""
    core = name.strip()
    if core.endswith("村志"):
        core = core[: -len("村志")]
    if len(core) >= 3 and core.endswith("村"):
        core = core[:-1]
    return core


def _add_key(inverted: Dict[str, List[str]], key: Optional[str], code: str) -> None:
    if not key:
        return
    key = key.strip()
    if not key:
        return
    codes = inverted.setdefault(key, [])
    if code not in codes:
        codes.append(code)


def build_index(csv_path: Path, kmz_path: Path) -> Dict:
    gazetteers = load_gazetteer_csv(csv_path)
    geo = {v["code"]: v for v in load_villages_kmz(kmz_path)}

    records: Dict[str, Dict] = {}
    inverted: Dict[str, List[str]] = {}
    geo_matched = 0

    for row in gazetteers:
        code = row["code"]
        g = geo.get(code)
        if g:
            geo_matched += 1
        province_cn, province_pinyin = _split_cn_pinyin(g.get("province_raw")) if g else (None, None)
        rec = {
            "gazetteer_code": code,
            "gazetteer_title": row.get("gazetteer_title"),
            "gazetteer_title_pinyin": row.get("gazetteer_title_pinyin"),
            "pub_year": row.get("pub_year"),
            "pub_type": row.get("pub_type"),
            "village_name_cn": g.get("village_name_cn") if g else None,
            "village_name_pinyin": g.get("village_name_pinyin") if g else None,
            "village_code": g.get("village_code") if g else None,
            "province_cn": province_cn,
            "province_pinyin": province_pinyin,
            "city_cn": g.get("city_cn") if g else None,
            "city_pinyin": g.get("city_pinyin") if g else None,
            "county_cn": g.get("county_cn") if g else None,
            "county_pinyin": g.get("county_pinyin") if g else None,
            "coords": g.get("coords") if g else None,
            "region": g.get("region") if g else None,
            "catalog_url": g.get("catalog_url") if g else None,
        }
        records[code] = rec

        title = rec["gazetteer_title"]
        title_py = rec["gazetteer_title_pinyin"]
        vname = rec["village_name_cn"]
        vpy = rec["village_name_pinyin"]
        # 简体 + 繁体（保守映射）：题名与其去通名核心、村名与其去通名核心
        cn_keys = [title, strip_toponym_suffix(title)]
        if vname:
            cn_keys += [vname, strip_toponym_suffix(vname)]
        for key in cn_keys:
            _add_key(inverted, key, code)
            _add_key(inverted, s2t(key), code)
        # 拼音（统一小写，便于查询端归一）
        _add_key(inverted, title_py.lower() if title_py else None, code)
        _add_key(inverted, vpy.lower() if vpy else None, code)

    for codes in inverted.values():
        codes.sort(key=lambda c: (len(c), c))

    return {
        "meta": {
            "provider_id": "ccvg",
            "built_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "builder": "build_index.py",
            "record_count": len(records),
            "geo_matched": geo_matched,
            "key_count": len(inverted),
            "field_map": {
                "village_name": "gazetteer_title / village_name_cn",
                "province": "province_cn（+province_pinyin）",
                "coordinates": "coords [lon, lat]（WGS84，来自官方地图 KMZ）",
                "join_key": "gazetteer_code（村志代码）",
            },
            "sources": {
                "gazetteer_csv": CSV_NAME,
                "villages_kmz": KMZ_NAME,
                "item": ITEM_URL,
            },
        },
        "records": records,
        "inverted_index": dict(sorted(inverted.items())),
    }


# ---------------------------------------------------------------------------
# 落盘
# ---------------------------------------------------------------------------

def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_index(index: Dict, out_path: Path) -> None:
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, sort_keys=True,
                  separators=(",", ":"))


def write_metadata(csv_path: Path, kmz_path: Path, index: Dict, out_path: Path) -> None:
    meta = {
        "dataset": "Contemporary Chinese Village Gazetteer Data (CCVG Data)",
        "provider": "University of Pittsburgh Library System, East Asian Library",
        "item_url": ITEM_URL,
        "downloaded_at": datetime.date.today().isoformat(),
        "license_note": (
            "官网声明供学者免费下载；D-Scholarship 权利声明为 "
            "Copyright Not Evaluated —— 本地仅作匹配留证（对应 LicenseClass."
            "METADATA_UNSPECIFIED），索引与元数据入库，原始文件不入库不再分发。"
        ),
        "sources": {
            CSV_NAME: {
                "url": SOURCE_CSV_URL,
                "sha256": sha256_of(csv_path),
                "bytes": csv_path.stat().st_size,
                "rows": index["meta"]["record_count"],
                "columns": ["村志代码", "村志书名", "书名-汉语拼音", "出版年", "出版类型"],
            },
            KMZ_NAME: {
                "url": SOURCE_KMZ_URL,
                "sha256": sha256_of(kmz_path),
                "bytes": kmz_path.stat().st_size,
                "placemarks": index["meta"]["geo_matched"],
                "note": "官方 Coverage Map（Google MyMaps）的 KML 导出，含村名/省市县/经纬度",
            },
        },
        "index": {
            "file": INDEX_NAME,
            "key_domains": ["村名简体", "村名繁体(保守映射)", "拼音(小写)", "去通名核心名"],
            "field_map": index["meta"]["field_map"],
        },
        "manual_acquisition": MANUAL_STEPS,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def main() -> int:
    csv_path = HERE / CSV_NAME
    kmz_path = HERE / KMZ_NAME
    missing = [p.name for p in (csv_path, kmz_path) if not p.exists()]
    if missing:
        print("缺少原始文件: %s" % ", ".join(missing), file=sys.stderr)
        print(MANUAL_STEPS, file=sys.stderr)
        return 2
    index = build_index(csv_path, kmz_path)
    write_index(index, HERE / INDEX_NAME)
    write_metadata(csv_path, kmz_path, index, HERE / META_NAME)
    m = index["meta"]
    print("records=%d geo_matched=%d keys=%d -> %s / %s"
          % (m["record_count"], m["geo_matched"], m["key_count"],
             INDEX_NAME, META_NAME))
    return 0


if __name__ == "__main__":
    sys.exit(main())
