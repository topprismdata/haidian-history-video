"""
测试 CCVG 本地倒排索引（build_index.py 构建器 + providers.ccvg.CcvgLocalIndex）

用 3 行 fixture CSV 与迷你 KMZ 走完整链路：
解析 → 简繁/拼音/核心名倒排 → 落盘 → 加载 → 查询 → 裁决记录包装。
另附一条对已入库真实索引的冒烟断言（索引文件本身入库，离线可跑）。
"""
import importlib.util
import zipfile
from pathlib import Path

import pytest

from haidian_kg.authority_resolver import (
    LicenseClass,
    MatchMethod,
)
from haidian_kg.providers.ccvg import CcvgLocalIndex

REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_PATH = REPO_ROOT / "haidian_kg" / "data" / "ccvg" / "build_index.py"
DEFAULT_INDEX = REPO_ROOT / "haidian_kg" / "data" / "ccvg" / "ccvg_index.json"

CSV_TEXT = (
    "村志代码 Gazetteer Code,村志书名 Gazetteer Title,"
    "书名 - 汉语拼音 Gazetteer Title - Hanyu Pinyin,"
    "出版年 Year of Publication,出版类型 Publication Type\n"
    "1,太平店村志,Changge Shi Taipingdian Cun zhi,2009,正式出版 Formal\n"
    "29,刘国忠村志,Yulin Shi Liuguozhong Cun zhi,2012,非正式出版物 Informal\n"
    "77,无图村志,No Geo Cun zhi,2015,正式出版 Formal\n"
)

KML_TEXT = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>mini map</name>
    <Folder>
      <name>Northwest China</name>
      <Placemark>
        <name>Liuguozhong Cun</name>
        <ExtendedData>
          <Data name="村志代码 Gazetteer Code"><value>0029</value></Data>
          <Data name="村名 - 汉字 Village Name - Chinese Characters"><value>刘国忠村</value></Data>
          <Data name="省 - 汉字和汉语拼音 Province - Chinese Characters and Hanyu Pinyin"><value>陕西省 Shanxi Sheng</value></Data>
          <Data name="市 - 汉字 City - Chinese Characters"><value>榆林市</value></Data>
          <Data name="县 / 区 - 汉字 County / District - Chinese Characters"><value>神木县</value></Data>
          <Data name="经纬度 – Coordinates"><value>110.533529,38.368453</value></Data>
        </ExtendedData>
      </Placemark>
    </Folder>
    <Folder>
      <name>North China</name>
      <Placemark>
        <name>Taipingdian Cun</name>
        <Point><coordinates>113.99,35.31,0</coordinates></Point>
        <ExtendedData>
          <Data name="村志代码 Gazetteer Code"><value>1</value></Data>
          <Data name="村名 - 汉字 Village Name - Chinese Characters"><value>太平店村</value></Data>
          <Data name="省 - 汉字和汉语拼音 Province - Chinese Characters and Hanyu Pinyin"><value>山西省 Shanxi Sheng</value></Data>
          <Data name="市 - 汉字 City - Chinese Characters"><value>长治市</value></Data>
        </ExtendedData>
      </Placemark>
    </Folder>
  </Document>
</kml>
"""


@pytest.fixture(scope="module")
def build_mod():
    spec = importlib.util.spec_from_file_location("ccvg_build_index_test", BUILD_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def index_file(tmp_path_factory, build_mod):
    """3 行 fixture CSV + 迷你 KMZ → 构建并落盘索引。"""
    root = tmp_path_factory.mktemp("ccvg_fixture")
    csv_path = root / "Gazetteer_Information_村志信息.csv"
    csv_path.write_text(CSV_TEXT, encoding="utf-8")
    kmz_path = root / "ccvg_villages_map.kmz"
    with zipfile.ZipFile(kmz_path, "w") as zf:
        zf.writestr("doc.kml", KML_TEXT.encode("utf-8"))
    index = build_mod.build_index(csv_path, kmz_path)
    out = root / "ccvg_index.json"
    build_mod.write_index(index, out)
    return out


class TestBuildIndex:
    def test_fixture_three_rows_and_join(self, index_file, build_mod):
        import json
        data = json.loads(index_file.read_text(encoding="utf-8"))
        assert data["meta"]["record_count"] == 3
        assert data["meta"]["geo_matched"] == 2  # 村志 77 无地图点
        # 零填充村志代码 '0029' 与 CSV '29' 归并连接
        rec29 = data["records"]["29"]
        assert rec29["village_name_cn"] == "刘国忠村"
        assert rec29["province_cn"] == "陕西省"
        assert rec29["city_cn"] == "榆林市"
        assert rec29["county_cn"] == "神木县"
        assert rec29["coords"] == [110.533529, 38.368453]
        assert rec29["region"] == "Northwest China"
        # 无 ExtendedData 经纬度时退回 Point/coordinates
        rec1 = data["records"]["1"]
        assert rec1["coords"] == [113.99, 35.31]
        # 无地图点的村：省份/坐标字段为 None 而非缺失
        rec77 = data["records"]["77"]
        assert rec77["province_cn"] is None
        assert rec77["coords"] is None

    def test_s2t_conservative_and_reversible(self, build_mod):
        assert build_mod.s2t("刘国忠村") == "劉國忠村"
        assert build_mod.s2t("太平店") == "太平店"
        assert build_mod.t2s("劉國忠村") == "刘国忠村"
        # 歧义字不映射（谷/里/松 原样保留，宁缺毋错）
        assert build_mod.s2t("谷里松村") == "谷里松村"


class TestCcvgLocalIndex:
    def test_query_simplified_title(self, index_file):
        rows = CcvgLocalIndex(index_file).load().query("太平店村志")
        assert len(rows) == 1
        assert rows[0]["gazetteer_code"] == "1"
        assert rows[0]["province_cn"] == "山西省"
        assert rows[0]["coords"] == [113.99, 35.31]

    def test_query_traditional_and_core(self, index_file):
        assert [r["gazetteer_code"] for r in CcvgLocalIndex(index_file).load().query("劉國忠村")] == ["29"]
        # 去通名核心键 + 查询端 t2s 归一：繁体核心名也能命中
        assert [r["gazetteer_code"] for r in CcvgLocalIndex(index_file).load().query("劉國忠")] == ["29"]
        assert [r["gazetteer_code"] for r in CcvgLocalIndex(index_file).load().query("太平店")] == ["1"]

    def test_query_pinyin_case_insensitive(self, index_file):
        rows = CcvgLocalIndex(index_file).load().query("LIUGUOZHONG CUN")
        assert [r["gazetteer_code"] for r in rows] == ["29"]

    def test_query_miss_returns_empty(self, index_file):
        idx = CcvgLocalIndex(index_file).load()
        assert idx.query("不存在的村") == []
        assert idx.query("") == []
        assert idx.query(None) == []

    def test_missing_index_file_returns_empty(self, tmp_path):
        idx = CcvgLocalIndex(tmp_path / "no_such_index.json")
        assert idx.query("刘国忠村") == []  # 懒加载路径
        idx.load()
        assert idx.query("刘国忠村") == []  # 显式加载路径
        assert idx.records == {}

    def test_resolve_wraps_authority_record(self, index_file):
        records = CcvgLocalIndex(index_file).load().resolve("劉國忠村")
        assert len(records) == 1
        rec = records[0]
        assert rec.provider_id == "ccvg"
        assert rec.provider_record_id == "ccvg:29"
        assert rec.matched_name == "刘国忠村"
        assert rec.license_class == LicenseClass.METADATA_UNSPECIFIED
        assert rec.match_method == MatchMethod.LOCAL_MIRROR_INDEX
        assert rec.granularity.value == "MICRO_VILLAGE_SETTLEMENT"
        assert "陕西省" in rec.parent_jurisdiction
        assert rec.raw_payload["coords"] == [110.533529, 38.368453]
        assert CcvgLocalIndex(index_file).load().resolve("查无此村") == []


class TestCommittedIndexSmoke:
    def test_real_index_loads_and_maps_fields(self):
        if not DEFAULT_INDEX.exists():
            pytest.skip("ccvg_index.json 未入库")
        idx = CcvgLocalIndex().load()
        assert idx.meta["record_count"] >= 2600
        assert idx.meta["geo_matched"] >= 2590
        rows = idx.query("刘国忠村")
        assert rows and rows[0]["province_cn"] == "陕西省"
        assert rows[0]["coords"] == [110.533529, 38.368453]
        # 验收要求：索引 meta 的字段映射须含村名/省份/坐标
        fm = idx.meta["field_map"]
        assert "village_name" in fm and "province" in fm and "coordinates" in fm
