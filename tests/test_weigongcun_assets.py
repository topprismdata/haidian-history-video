# -*- coding: utf-8 -*-
"""E21《魏公村·高梁河畔的畏吾村》Task 1 资产测试.

断言 assets/hist_weigongcun/ 全套地理切片与视觉资产真实存在,
分辨率/色彩通道符合工程约束, sources.csv 的 sha256 完整性与 VEC 分级留痕一致,
且全部资产已同步至 /tmp/chemistry-video/public/weigongcun/。

证据分级依据 docs/superpowers/specs/2026-10-03-e21-weigongcun-design.md:
MEC-1~4 / VEC-1~4。
"""
import csv
import hashlib
import pathlib

from PIL import Image

ASSET_DIR = pathlib.Path("assets/hist_weigongcun")
PUBLIC_DIR = pathlib.Path("/tmp/chemistry-video/public/weigongcun")

# file -> (约束描述, 最小宽, 最小高, 精确宽高或 None, 允许模式)
REQUIRED_ASSETS = {
    "sanshanyuan_gaoliang_roi_4000.png": ("高梁河段高清切片", 3000, 1800, None, {"RGB", "RGBA"}),
    "beijing_1915_weigongcun_roi.png": ("1915 实测京师四郊图魏公村切片", 1920, 1080, (1920, 1080), {"RGB", "RGBA"}),
    "yuanshi_lianxixian_folio.png": ("元史·廉希宪传书影", 1200, 800, None, {"RGB", "L", "LA"}),
    "dahuisi_twenty_eight_devas.png": ("大慧寺诸天造像图档", 1200, 800, None, {"RGB", "L", "LA"}),
    "minzu_univ_archival_1950s.png": ("中央民族学院 1950s 历史实拍", 900, 450, None, {"RGB", "L", "LA"}),
    "modern_weigongcun_street.png": ("现代魏公村/民大实拍", 1200, 800, None, {"RGB", "L", "LA"}),
    "mec4_composite_eras.png": ("MEC-4 四时代叠合图", 1920, 1080, (1920, 1080), {"RGB", "RGBA"}),
}

SOURCE_CSV_HEADER = {"file", "title", "sha256", "vec"}


def _sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def test_asset_dir_exists():
    assert ASSET_DIR.is_dir(), "assets/hist_weigongcun/ 目录必须存在"


def test_required_assets_resolution_and_channels():
    for name, (label, min_w, min_h, exact, modes) in REQUIRED_ASSETS.items():
        p = ASSET_DIR / name
        assert p.exists(), "资产缺失: %s (%s)" % (name, label)
        im = Image.open(p)
        assert im.format == "PNG", "%s 必须是 PNG (实际 %s)" % (name, im.format)
        w, h = im.size
        assert w >= min_w and h >= min_h, "%s 分辨率不足: %sx%s < %sx%s" % (name, w, h, min_w, min_h)
        if exact is not None:
            assert (w, h) == exact, "%s 必须严格为 %sx%s (实际 %sx%s)" % (name, exact[0], exact[1], w, h)
        assert im.mode in modes, "%s 色彩通道不符: %s ∉ %s" % (name, im.mode, sorted(modes))
        assert p.stat().st_size > 10 * 1024, "%s 文件过小, 疑似空文件" % name


def test_sources_csv_sha256_integrity_and_vec():
    csv_file = ASSET_DIR / "sources.csv"
    assert csv_file.exists(), "sources.csv 必须存在"
    with open(csv_file, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    assert rows, "sources.csv 必须包含数据行"
    headers = set(rows[0].keys())
    assert SOURCE_CSV_HEADER <= headers, "sources.csv 表头缺少列: %s" % (SOURCE_CSV_HEADER - headers)

    listed = {}
    for row in rows:
        name = (row.get("file") or "").strip()
        if not name or name.startswith("#"):
            continue
        listed[name] = row
        digest = (row.get("sha256") or "").strip().lower()
        assert len(digest) == 64, "%s 的 sha256 必须是 64 位十六进制" % name
        vec = (row.get("vec") or "").strip()
        assert vec.startswith("VEC-"), "%s 必须标注 VEC 证据分级 (实际 %r)" % (name, vec)
        rights = (row.get("rights") or (row.get("source") or "")).strip()
        assert rights, "%s 必须留痕版权来源" % name
    for name in REQUIRED_ASSETS:
        assert name in listed, "sources.csv 必须登记资产: %s" % name
        p = ASSET_DIR / name
        actual = _sha256_of(p)
        assert listed[name]["sha256"].strip().lower() == actual, (
            "%s sha256 与实际文件不符 (留痕 %s / 实际 %s)"
            % (name, listed[name]["sha256"], actual)
        )


def test_public_weigongcun_synced():
    for name in list(REQUIRED_ASSETS) + ["sources.csv"]:
        p = PUBLIC_DIR / name
        assert p.exists(), "资产未同步到 public/weigongcun: %s" % name
        if name != "sources.csv":
            assert _sha256_of(p) == _sha256_of(ASSET_DIR / name), "%s 同步副本 sha256 不一致" % name
